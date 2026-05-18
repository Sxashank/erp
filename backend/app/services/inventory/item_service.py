"""Item Master service."""

from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.inventory.item_master import ItemMaster
from app.models.inventory.item_category import ItemCategory
from app.models.inventory.stock import StockBalance
from app.schemas.inventory.item_master import (
    ItemMasterCreate,
    ItemMasterUpdate,
)


class ItemMasterService:
    """Service for Item Master operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        data: ItemMasterCreate,
        created_by: Optional[UUID] = None,
    ) -> ItemMaster:
        """Create a new item."""
        # Check for duplicate code
        existing = await self._get_by_code(data.item_code, data.organization_id)
        if existing:
            raise ValueError(f"Item code '{data.item_code}' already exists")

        # Validate category
        category = await self._get_category(data.category_id)
        if not category:
            raise ValueError("Category not found")
        if category.organization_id != data.organization_id:
            raise ValueError("Category belongs to different organization")

        # Create item
        item_data = data.model_dump()
        if created_by:
            item_data["created_by"] = created_by

        item = ItemMaster(**item_data)
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def get(self, id: UUID) -> Optional[ItemMaster]:
        """Get item by ID."""
        result = await self.session.execute(
            select(ItemMaster)
            .options(selectinload(ItemMaster.category))
            .where(ItemMaster.id == id, ItemMaster.is_active == True)
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        id: UUID,
        data: ItemMasterUpdate,
        updated_by: Optional[UUID] = None,
    ) -> Optional[ItemMaster]:
        """Update an item."""
        item = await self.get(id)
        if not item:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Check code uniqueness if changing code
        if "item_code" in update_data and update_data["item_code"] != item.item_code:
            existing = await self._get_by_code(
                update_data["item_code"],
                item.organization_id,
                exclude_id=id,
            )
            if existing:
                raise ValueError(f"Item code '{update_data['item_code']}' already exists")

        # Validate category if changing
        if "category_id" in update_data:
            category = await self._get_category(update_data["category_id"])
            if not category:
                raise ValueError("Category not found")
            if category.organization_id != item.organization_id:
                raise ValueError("Category belongs to different organization")

        # Update fields
        for key, value in update_data.items():
            setattr(item, key, value)
        if updated_by:
            item.updated_by = updated_by

        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def delete(
        self,
        id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> bool:
        """Soft delete an item."""
        item = await self.get(id)
        if not item:
            return False

        # Check if item has stock
        has_stock = await self._has_stock(id)
        if has_stock:
            raise ValueError("Cannot delete item with existing stock")

        item.soft_delete(deleted_by)
        await self.session.flush()
        return True

    async def list_by_organization(
        self,
        organization_id: UUID,
        category_id: Optional[UUID] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ItemMaster]:
        """List items for an organization."""
        query = (
            select(ItemMaster)
            .options(selectinload(ItemMaster.category))
            .where(
                ItemMaster.organization_id == organization_id,
                ItemMaster.is_active == True,
            )
        )

        if category_id:
            query = query.where(ItemMaster.category_id == category_id)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    ItemMaster.item_code.ilike(search_pattern),
                    ItemMaster.item_name.ilike(search_pattern),
                    ItemMaster.description.ilike(search_pattern),
                    ItemMaster.sku.ilike(search_pattern),
                    ItemMaster.barcode.ilike(search_pattern),
                )
            )

        result = await self.session.execute(
            query.order_by(ItemMaster.item_code).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_organization(
        self,
        organization_id: UUID,
        category_id: Optional[UUID] = None,
        search: Optional[str] = None,
    ) -> int:
        """Count items for an organization."""
        query = select(func.count(ItemMaster.id)).where(
            ItemMaster.organization_id == organization_id,
            ItemMaster.is_active == True,
        )

        if category_id:
            query = query.where(ItemMaster.category_id == category_id)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    ItemMaster.item_code.ilike(search_pattern),
                    ItemMaster.item_name.ilike(search_pattern),
                )
            )

        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_stock_summary(self, item_id: UUID) -> dict:
        """Get stock summary for an item across all warehouses."""
        result = await self.session.execute(
            select(
                func.sum(StockBalance.quantity_on_hand).label("total_on_hand"),
                func.sum(StockBalance.quantity_reserved).label("total_reserved"),
                func.sum(StockBalance.total_value).label("total_value"),
            )
            .where(
                StockBalance.item_id == item_id,
                StockBalance.is_active == True,
            )
        )
        row = result.one()
        return {
            "total_on_hand": row.total_on_hand or Decimal("0"),
            "total_reserved": row.total_reserved or Decimal("0"),
            "total_value": row.total_value or Decimal("0"),
            "available_quantity": (row.total_on_hand or Decimal("0")) - (row.total_reserved or Decimal("0")),
        }

    async def get_low_stock_items(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> List[dict]:
        """Get items with stock below minimum level."""
        # Get total stock per item
        subquery = (
            select(
                StockBalance.item_id,
                func.sum(StockBalance.quantity_on_hand).label("total_stock"),
            )
            .where(StockBalance.is_active == True)
            .group_by(StockBalance.item_id)
            .subquery()
        )

        result = await self.session.execute(
            select(ItemMaster, subquery.c.total_stock)
            .outerjoin(subquery, ItemMaster.id == subquery.c.item_id)
            .where(
                ItemMaster.organization_id == organization_id,
                ItemMaster.is_active == True,
                ItemMaster.is_stockable == True,
                ItemMaster.minimum_stock_level > 0,
                or_(
                    subquery.c.total_stock == None,
                    subquery.c.total_stock < ItemMaster.minimum_stock_level,
                ),
            )
            .order_by(ItemMaster.item_code)
            .offset(skip)
            .limit(limit)
        )

        items = []
        for item, total_stock in result:
            items.append({
                "item": item,
                "current_stock": total_stock or Decimal("0"),
                "minimum_level": item.minimum_stock_level,
                "shortfall": item.minimum_stock_level - (total_stock or Decimal("0")),
            })
        return items

    async def _get_by_code(
        self,
        code: str,
        organization_id: UUID,
        exclude_id: Optional[UUID] = None,
    ) -> Optional[ItemMaster]:
        """Get item by code."""
        query = select(ItemMaster).where(
            ItemMaster.item_code == code,
            ItemMaster.organization_id == organization_id,
            ItemMaster.is_active == True,
        )
        if exclude_id:
            query = query.where(ItemMaster.id != exclude_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_category(self, category_id: UUID) -> Optional[ItemCategory]:
        """Get category by ID."""
        result = await self.session.execute(
            select(ItemCategory).where(
                ItemCategory.id == category_id,
                ItemCategory.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def _has_stock(self, item_id: UUID) -> bool:
        """Check if item has any stock."""
        result = await self.session.execute(
            select(func.count(StockBalance.id)).where(
                StockBalance.item_id == item_id,
                StockBalance.quantity_on_hand > 0,
                StockBalance.is_active == True,
            )
        )
        return result.scalar_one() > 0
