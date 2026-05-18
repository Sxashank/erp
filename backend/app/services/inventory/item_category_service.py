"""Item Category service."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.inventory.item_category import ItemCategory
from app.models.inventory.item_master import ItemMaster
from app.schemas.inventory.item_category import (
    ItemCategoryCreate,
    ItemCategoryUpdate,
    ItemCategoryTreeResponse,
)


class ItemCategoryService:
    """Service for Item Category operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        data: ItemCategoryCreate,
        created_by: Optional[UUID] = None,
    ) -> ItemCategory:
        """Create a new item category."""
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

        category = ItemCategory(**category_data)
        self.session.add(category)
        await self.session.flush()
        await self.session.refresh(category)
        return category

    async def get(self, id: UUID) -> Optional[ItemCategory]:
        """Get item category by ID."""
        result = await self.session.execute(
            select(ItemCategory)
            .options(selectinload(ItemCategory.parent_category))
            .where(ItemCategory.id == id, ItemCategory.is_active == True)
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        id: UUID,
        data: ItemCategoryUpdate,
        updated_by: Optional[UUID] = None,
    ) -> Optional[ItemCategory]:
        """Update an item category."""
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
        """Soft delete an item category."""
        category = await self.get(id)
        if not category:
            return False

        # Check if category has items
        item_count = await self._get_item_count(id)
        if item_count > 0:
            raise ValueError(f"Cannot delete category with {item_count} items")

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
    ) -> List[ItemCategory]:
        """List all categories for an organization."""
        result = await self.session.execute(
            select(ItemCategory)
            .options(selectinload(ItemCategory.parent_category))
            .where(
                ItemCategory.organization_id == organization_id,
                ItemCategory.is_active == True,
            )
            .order_by(ItemCategory.category_code)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_parent(
        self,
        parent_id: Optional[UUID],
        organization_id: Optional[UUID] = None,
    ) -> List[ItemCategory]:
        """List categories by parent."""
        query = select(ItemCategory).where(
            ItemCategory.is_active == True,
            ItemCategory.parent_category_id == parent_id,
        )
        if organization_id:
            query = query.where(ItemCategory.organization_id == organization_id)

        result = await self.session.execute(query.order_by(ItemCategory.category_code))
        return list(result.scalars().all())

    async def get_tree(
        self,
        organization_id: UUID,
    ) -> List[ItemCategoryTreeResponse]:
        """Get hierarchical tree of categories."""
        # Get all categories
        categories = await self.list_by_organization(organization_id, limit=1000)

        # Get item counts
        item_counts = await self._get_item_counts_by_category(organization_id)

        # Build tree
        tree_nodes = {}
        for category in categories:
            tree_nodes[category.id] = ItemCategoryTreeResponse(
                id=category.id,
                category_code=category.category_code,
                category_name=category.category_name,
                is_stockable=category.is_stockable,
                item_count=item_counts.get(category.id, 0),
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
            select(func.count(ItemCategory.id)).where(
                ItemCategory.organization_id == organization_id,
                ItemCategory.is_active == True,
            )
        )
        return result.scalar_one()

    async def _get_by_code(
        self,
        code: str,
        organization_id: UUID,
        exclude_id: Optional[UUID] = None,
    ) -> Optional[ItemCategory]:
        """Get category by code."""
        query = select(ItemCategory).where(
            ItemCategory.category_code == code,
            ItemCategory.organization_id == organization_id,
            ItemCategory.is_active == True,
        )
        if exclude_id:
            query = query.where(ItemCategory.id != exclude_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_item_count(self, category_id: UUID) -> int:
        """Get count of items in a category."""
        result = await self.session.execute(
            select(func.count(ItemMaster.id)).where(
                ItemMaster.category_id == category_id,
                ItemMaster.is_active == True,
            )
        )
        return result.scalar_one()

    async def _get_item_counts_by_category(
        self,
        organization_id: UUID,
    ) -> dict[UUID, int]:
        """Get item counts grouped by category."""
        result = await self.session.execute(
            select(
                ItemMaster.category_id,
                func.count(ItemMaster.id).label("count"),
            )
            .where(
                ItemMaster.organization_id == organization_id,
                ItemMaster.is_active == True,
            )
            .group_by(ItemMaster.category_id)
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
