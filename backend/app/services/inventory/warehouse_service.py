"""Warehouse service."""

from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.inventory.warehouse import Warehouse
from app.models.inventory.stock import StockBalance
from app.schemas.inventory.warehouse import (
    WarehouseCreate,
    WarehouseUpdate,
)


class WarehouseService:
    """Service for Warehouse operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        data: WarehouseCreate,
        created_by: Optional[UUID] = None,
    ) -> Warehouse:
        """Create a new warehouse."""
        # Check for duplicate code
        existing = await self._get_by_code(data.warehouse_code, data.organization_id)
        if existing:
            raise ValueError(f"Warehouse code '{data.warehouse_code}' already exists")

        # If setting as default, unset other defaults
        if data.is_default:
            await self._unset_default(data.organization_id)

        # Create warehouse
        warehouse_data = data.model_dump()
        if created_by:
            warehouse_data["created_by"] = created_by

        warehouse = Warehouse(**warehouse_data)
        self.session.add(warehouse)
        await self.session.flush()
        await self.session.refresh(warehouse)
        return warehouse

    async def get(self, id: UUID) -> Optional[Warehouse]:
        """Get warehouse by ID."""
        result = await self.session.execute(
            select(Warehouse)
            .options(selectinload(Warehouse.unit))
            .where(Warehouse.id == id, Warehouse.is_active == True)
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        id: UUID,
        data: WarehouseUpdate,
        updated_by: Optional[UUID] = None,
    ) -> Optional[Warehouse]:
        """Update a warehouse."""
        warehouse = await self.get(id)
        if not warehouse:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Check code uniqueness if changing code
        if "warehouse_code" in update_data and update_data["warehouse_code"] != warehouse.warehouse_code:
            existing = await self._get_by_code(
                update_data["warehouse_code"],
                warehouse.organization_id,
                exclude_id=id,
            )
            if existing:
                raise ValueError(f"Warehouse code '{update_data['warehouse_code']}' already exists")

        # If setting as default, unset other defaults
        if update_data.get("is_default") and not warehouse.is_default:
            await self._unset_default(warehouse.organization_id)

        # Update fields
        for key, value in update_data.items():
            setattr(warehouse, key, value)
        if updated_by:
            warehouse.updated_by = updated_by

        await self.session.flush()
        await self.session.refresh(warehouse)
        return warehouse

    async def delete(
        self,
        id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> bool:
        """Soft delete a warehouse."""
        warehouse = await self.get(id)
        if not warehouse:
            return False

        # Check if warehouse has stock
        has_stock = await self._has_stock(id)
        if has_stock:
            raise ValueError("Cannot delete warehouse with existing stock")

        warehouse.soft_delete(deleted_by)
        await self.session.flush()
        return True

    async def list_by_organization(
        self,
        organization_id: UUID,
        unit_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Warehouse]:
        """List warehouses for an organization."""
        query = (
            select(Warehouse)
            .options(selectinload(Warehouse.unit))
            .where(
                Warehouse.organization_id == organization_id,
                Warehouse.is_active == True,
            )
        )

        if unit_id:
            query = query.where(Warehouse.unit_id == unit_id)

        result = await self.session.execute(
            query.order_by(Warehouse.warehouse_code).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_organization(
        self,
        organization_id: UUID,
        unit_id: Optional[UUID] = None,
    ) -> int:
        """Count warehouses for an organization."""
        query = select(func.count(Warehouse.id)).where(
            Warehouse.organization_id == organization_id,
            Warehouse.is_active == True,
        )

        if unit_id:
            query = query.where(Warehouse.unit_id == unit_id)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_default(self, organization_id: UUID) -> Optional[Warehouse]:
        """Get the default warehouse for an organization."""
        result = await self.session.execute(
            select(Warehouse).where(
                Warehouse.organization_id == organization_id,
                Warehouse.is_default == True,
                Warehouse.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def get_stock_summary(self, warehouse_id: UUID) -> dict:
        """Get stock summary for a warehouse."""
        result = await self.session.execute(
            select(
                func.count(StockBalance.id).label("total_items"),
                func.sum(StockBalance.total_value).label("total_value"),
            )
            .where(
                StockBalance.warehouse_id == warehouse_id,
                StockBalance.quantity_on_hand > 0,
                StockBalance.is_active == True,
            )
        )
        row = result.one()
        return {
            "total_items": row.total_items or 0,
            "total_value": row.total_value or Decimal("0"),
        }

    async def _get_by_code(
        self,
        code: str,
        organization_id: UUID,
        exclude_id: Optional[UUID] = None,
    ) -> Optional[Warehouse]:
        """Get warehouse by code."""
        query = select(Warehouse).where(
            Warehouse.warehouse_code == code,
            Warehouse.organization_id == organization_id,
            Warehouse.is_active == True,
        )
        if exclude_id:
            query = query.where(Warehouse.id != exclude_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _unset_default(self, organization_id: UUID) -> None:
        """Unset default flag for all warehouses in organization."""
        result = await self.session.execute(
            select(Warehouse).where(
                Warehouse.organization_id == organization_id,
                Warehouse.is_default == True,
                Warehouse.is_active == True,
            )
        )
        for warehouse in result.scalars().all():
            warehouse.is_default = False

    async def _has_stock(self, warehouse_id: UUID) -> bool:
        """Check if warehouse has any stock."""
        result = await self.session.execute(
            select(func.count(StockBalance.id)).where(
                StockBalance.warehouse_id == warehouse_id,
                StockBalance.quantity_on_hand > 0,
                StockBalance.is_active == True,
            )
        )
        return result.scalar_one() > 0
