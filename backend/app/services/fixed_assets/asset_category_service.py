"""Asset Category service."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.fixed_assets.asset_category import AssetCategory
from app.models.fixed_assets.fixed_asset import FixedAsset
from app.schemas.fixed_assets.asset_category import (
    AssetCategoryCreate,
    AssetCategoryUpdate,
    AssetCategoryTreeResponse,
)


class AssetCategoryService:
    """Service for Asset Category operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        data: AssetCategoryCreate,
        created_by: Optional[UUID] = None,
    ) -> AssetCategory:
        """Create a new asset category."""
        self._validate_gl_mapping(
            depreciation_method=data.depreciation_method,
            gl_asset_account_id=data.gl_asset_account_id,
            gl_accum_dep_account_id=data.gl_accum_dep_account_id,
            gl_dep_expense_account_id=data.gl_dep_expense_account_id,
        )

        # Check for duplicate code
        existing = await self._get_by_code(data.category_code, data.organization_id)
        if existing:
            raise ValueError(f"Category code '{data.category_code}' already exists")

        # Validate parent if provided
        if data.parent_category_id:
            parent = await self.get(data.parent_category_id)
            if not parent:
                raise ValueError("Parent category not found")
            if parent.organization_id != data.organization_id:
                raise ValueError("Parent category belongs to different organization")

        # Create category
        category_data = data.model_dump()
        if created_by:
            category_data["created_by"] = created_by

        category = AssetCategory(**category_data)
        self.session.add(category)
        await self.session.flush()
        await self.session.refresh(category)
        return category

    async def get(self, id: UUID) -> Optional[AssetCategory]:
        """Get asset category by ID."""
        result = await self.session.execute(
            select(AssetCategory)
            .options(
                selectinload(AssetCategory.parent_category),
                selectinload(AssetCategory.gl_asset_account),
                selectinload(AssetCategory.gl_accum_dep_account),
                selectinload(AssetCategory.gl_dep_expense_account),
            )
            .where(AssetCategory.id == id, AssetCategory.is_active == True)
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        id: UUID,
        data: AssetCategoryUpdate,
        updated_by: Optional[UUID] = None,
    ) -> Optional[AssetCategory]:
        """Update an asset category."""
        category = await self.get(id)
        if not category:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Check code uniqueness if changing code
        if "category_code" in update_data and update_data["category_code"] != category.category_code:
            existing = await self._get_by_code(
                update_data["category_code"],
                category.organization_id,
                exclude_id=id,
            )
            if existing:
                raise ValueError(f"Category code '{update_data['category_code']}' already exists")

        # Validate parent if changing
        if "parent_category_id" in update_data:
            new_parent_id = update_data["parent_category_id"]
            if new_parent_id:
                if new_parent_id == id:
                    raise ValueError("Category cannot be its own parent")
                parent = await self.get(new_parent_id)
                if not parent:
                    raise ValueError("Parent category not found")
                if parent.organization_id != category.organization_id:
                    raise ValueError("Parent category belongs to different organization")
                # Check for circular reference
                if await self._would_create_cycle(id, new_parent_id):
                    raise ValueError("Cannot set parent: would create circular reference")

        self._validate_gl_mapping(
            depreciation_method=update_data.get(
                "depreciation_method", category.depreciation_method
            ),
            gl_asset_account_id=update_data.get(
                "gl_asset_account_id", category.gl_asset_account_id
            ),
            gl_accum_dep_account_id=update_data.get(
                "gl_accum_dep_account_id", category.gl_accum_dep_account_id
            ),
            gl_dep_expense_account_id=update_data.get(
                "gl_dep_expense_account_id", category.gl_dep_expense_account_id
            ),
        )

        # Update fields
        for key, value in update_data.items():
            setattr(category, key, value)
        if updated_by:
            category.updated_by = updated_by

        await self.session.flush()
        await self.session.refresh(category)
        return category

    async def delete(
        self,
        id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> bool:
        """Soft delete an asset category."""
        category = await self.get(id)
        if not category:
            return False

        # Check if category has assets
        asset_count = await self._get_asset_count(id)
        if asset_count > 0:
            raise ValueError(f"Cannot delete category with {asset_count} assets")

        # Check if category has children
        children = await self.list_by_parent(id)
        if children:
            raise ValueError("Cannot delete category with sub-categories")

        category.soft_delete(deleted_by)
        await self.session.flush()
        return True

    async def list_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AssetCategory]:
        """List all categories for an organization."""
        result = await self.session.execute(
            select(AssetCategory)
            .options(
                selectinload(AssetCategory.parent_category),
                selectinload(AssetCategory.gl_asset_account),
                selectinload(AssetCategory.gl_accum_dep_account),
            )
            .where(
                AssetCategory.organization_id == organization_id,
                AssetCategory.is_active == True,
            )
            .order_by(AssetCategory.category_code)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_parent(
        self,
        parent_id: Optional[UUID],
        organization_id: Optional[UUID] = None,
    ) -> List[AssetCategory]:
        """List categories by parent."""
        query = select(AssetCategory).where(
            AssetCategory.is_active == True,
            AssetCategory.parent_category_id == parent_id,
        )
        if organization_id:
            query = query.where(AssetCategory.organization_id == organization_id)

        result = await self.session.execute(query.order_by(AssetCategory.category_code))
        return list(result.scalars().all())

    async def get_tree(
        self,
        organization_id: UUID,
    ) -> List[AssetCategoryTreeResponse]:
        """Get hierarchical tree of categories."""
        # Get all categories
        categories = await self.list_by_organization(organization_id, limit=1000)

        # Get asset counts
        asset_counts = await self._get_asset_counts_by_category(organization_id)

        # Build tree
        category_map = {cat.id: cat for cat in categories}
        root_categories = []

        for category in categories:
            tree_node = AssetCategoryTreeResponse(
                id=category.id,
                category_code=category.category_code,
                category_name=category.category_name,
                asset_type=category.asset_type,
                depreciation_method=category.depreciation_method,
                useful_life_years=category.useful_life_years,
                asset_count=asset_counts.get(category.id, 0),
                children=[],
            )

            if category.parent_category_id is None:
                root_categories.append(tree_node)
            else:
                # Find parent and add as child
                parent = category_map.get(category.parent_category_id)
                if parent:
                    # This is handled in a second pass
                    pass

        # Second pass to build tree structure
        tree_nodes = {}
        for category in categories:
            tree_nodes[category.id] = AssetCategoryTreeResponse(
                id=category.id,
                category_code=category.category_code,
                category_name=category.category_name,
                asset_type=category.asset_type,
                depreciation_method=category.depreciation_method,
                useful_life_years=category.useful_life_years,
                asset_count=asset_counts.get(category.id, 0),
                children=[],
            )

        root_nodes = []
        for category in categories:
            node = tree_nodes[category.id]
            if category.parent_category_id and category.parent_category_id in tree_nodes:
                tree_nodes[category.parent_category_id].children.append(node)
            else:
                root_nodes.append(node)

        return root_nodes

    async def count_by_organization(self, organization_id: UUID) -> int:
        """Count categories for an organization."""
        result = await self.session.execute(
            select(func.count(AssetCategory.id)).where(
                AssetCategory.organization_id == organization_id,
                AssetCategory.is_active == True,
            )
        )
        return result.scalar_one()

    async def _get_by_code(
        self,
        code: str,
        organization_id: UUID,
        exclude_id: Optional[UUID] = None,
    ) -> Optional[AssetCategory]:
        """Get category by code."""
        query = select(AssetCategory).where(
            AssetCategory.category_code == code,
            AssetCategory.organization_id == organization_id,
            AssetCategory.is_active == True,
        )
        if exclude_id:
            query = query.where(AssetCategory.id != exclude_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_asset_count(self, category_id: UUID) -> int:
        """Get count of assets in a category."""
        result = await self.session.execute(
            select(func.count(FixedAsset.id)).where(
                FixedAsset.category_id == category_id,
                FixedAsset.is_active == True,
            )
        )
        return result.scalar_one()

    async def _get_asset_counts_by_category(
        self,
        organization_id: UUID,
    ) -> dict[UUID, int]:
        """Get asset counts grouped by category."""
        result = await self.session.execute(
            select(
                FixedAsset.category_id,
                func.count(FixedAsset.id).label("count"),
            )
            .where(
                FixedAsset.organization_id == organization_id,
                FixedAsset.is_active == True,
            )
            .group_by(FixedAsset.category_id)
        )
        return {row.category_id: row.count for row in result}

    async def _would_create_cycle(
        self,
        category_id: UUID,
        new_parent_id: UUID,
    ) -> bool:
        """Check if setting new_parent_id would create a circular reference."""
        current_id = new_parent_id
        visited = {category_id}

        while current_id:
            if current_id in visited:
                return True
            visited.add(current_id)

            parent = await self.get(current_id)
            if not parent:
                break
            current_id = parent.parent_category_id

        return False

    @staticmethod
    def _validate_gl_mapping(
        *,
        depreciation_method,
        gl_asset_account_id: Optional[UUID],
        gl_accum_dep_account_id: Optional[UUID],
        gl_dep_expense_account_id: Optional[UUID],
    ) -> None:
        """Ensure the operational-core category stays postable."""
        if not gl_asset_account_id:
            raise ValueError("Asset account is required for fixed asset categories")

        if str(depreciation_method) == "DepreciationMethod.NO_DEPRECIATION":
            return
        if str(depreciation_method) == "NO_DEPRECIATION":
            return

        if not gl_accum_dep_account_id:
            raise ValueError(
                "Accumulated depreciation account is required for depreciable categories"
            )
        if not gl_dep_expense_account_id:
            raise ValueError(
                "Depreciation expense account is required for depreciable categories"
            )
