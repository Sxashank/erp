"""Stock service for inventory operations."""

from datetime import datetime, date, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.inventory.item_master import ItemMaster
from app.models.inventory.warehouse import Warehouse
from app.models.inventory.stock import (
    StockBalance,
    StockTransaction,
    TransactionType,
    TransactionStatus,
)
from app.schemas.inventory.stock import (
    StockInCreate,
    StockOutCreate,
    StockTransferCreate,
    StockAdjustmentCreate,
    StockTransactionUpdate,
)


class StockService:
    """Service for Stock operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ==========================================
    # Stock Balance Operations
    # ==========================================

    async def get_balance(
        self,
        item_id: UUID,
        warehouse_id: UUID,
    ) -> Optional[StockBalance]:
        """Get stock balance for item in warehouse."""
        result = await self.session.execute(
            select(StockBalance)
            .options(
                selectinload(StockBalance.item),
                selectinload(StockBalance.warehouse),
            )
            .where(
                StockBalance.item_id == item_id,
                StockBalance.warehouse_id == warehouse_id,
                StockBalance.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create_balance(
        self,
        organization_id: UUID,
        item_id: UUID,
        warehouse_id: UUID,
        created_by: Optional[UUID] = None,
    ) -> StockBalance:
        """Get or create stock balance for item in warehouse."""
        balance = await self.get_balance(item_id, warehouse_id)
        if not balance:
            balance = StockBalance(
                organization_id=organization_id,
                item_id=item_id,
                warehouse_id=warehouse_id,
                created_by=created_by,
            )
            self.session.add(balance)
            await self.session.flush()
        return balance

    async def list_balances(
        self,
        organization_id: UUID,
        warehouse_id: Optional[UUID] = None,
        item_id: Optional[UUID] = None,
        low_stock_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> List[StockBalance]:
        """List stock balances."""
        query = (
            select(StockBalance)
            .options(
                selectinload(StockBalance.item),
                selectinload(StockBalance.warehouse),
            )
            .where(
                StockBalance.organization_id == organization_id,
                StockBalance.is_active == True,
            )
        )

        if warehouse_id:
            query = query.where(StockBalance.warehouse_id == warehouse_id)

        if item_id:
            query = query.where(StockBalance.item_id == item_id)

        if low_stock_only:
            query = query.join(ItemMaster).where(
                StockBalance.quantity_on_hand < ItemMaster.minimum_stock_level
            )

        result = await self.session.execute(
            query.order_by(StockBalance.item_id).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count_balances(
        self,
        organization_id: UUID,
        warehouse_id: Optional[UUID] = None,
        item_id: Optional[UUID] = None,
    ) -> int:
        """Count stock balances."""
        query = select(func.count(StockBalance.id)).where(
            StockBalance.organization_id == organization_id,
            StockBalance.is_active == True,
            StockBalance.quantity_on_hand > 0,
        )

        if warehouse_id:
            query = query.where(StockBalance.warehouse_id == warehouse_id)

        if item_id:
            query = query.where(StockBalance.item_id == item_id)

        result = await self.session.execute(query)
        return result.scalar_one()

    # ==========================================
    # Stock Transaction Operations
    # ==========================================

    async def create_stock_in(
        self,
        data: StockInCreate,
        created_by: Optional[UUID] = None,
    ) -> StockTransaction:
        """Create stock in transaction."""
        return await self._create_transaction(
            transaction_type=TransactionType.STOCK_IN,
            data=data,
            created_by=created_by,
        )

    async def create_stock_out(
        self,
        data: StockOutCreate,
        created_by: Optional[UUID] = None,
    ) -> StockTransaction:
        """Create stock out transaction."""
        # Check available quantity
        balance = await self.get_balance(data.item_id, data.warehouse_id)
        available = (balance.quantity_on_hand - balance.quantity_reserved) if balance else Decimal("0")

        warehouse = await self._get_warehouse(data.warehouse_id)
        if not warehouse:
            raise ValueError("Warehouse not found")

        if available < data.quantity and not warehouse.allow_negative_stock:
            raise ValueError(
                f"Insufficient stock. Available: {available}, Requested: {data.quantity}"
            )

        return await self._create_transaction(
            transaction_type=TransactionType.STOCK_OUT,
            data=data,
            created_by=created_by,
        )

    async def create_stock_transfer(
        self,
        data: StockTransferCreate,
        created_by: Optional[UUID] = None,
    ) -> Tuple[StockTransaction, StockTransaction]:
        """Create stock transfer between warehouses."""
        if data.from_warehouse_id == data.to_warehouse_id:
            raise ValueError("Source and destination warehouse cannot be the same")

        # Check available quantity at source
        balance = await self.get_balance(data.item_id, data.from_warehouse_id)
        available = (balance.quantity_on_hand - balance.quantity_reserved) if balance else Decimal("0")

        warehouse = await self._get_warehouse(data.from_warehouse_id)
        if available < data.quantity and not (warehouse and warehouse.allow_negative_stock):
            raise ValueError(
                f"Insufficient stock at source. Available: {available}, Requested: {data.quantity}"
            )

        # Get item for unit cost
        item = await self._get_item(data.item_id)
        unit_cost = balance.average_cost if balance and balance.average_cost > 0 else item.standard_cost

        # Create transfer out transaction
        transfer_out = await self._create_transaction(
            transaction_type=TransactionType.TRANSFER_OUT,
            data=StockInCreate(
                item_id=data.item_id,
                warehouse_id=data.from_warehouse_id,
                quantity=data.quantity,
                unit_cost=unit_cost,
                transaction_date=data.transaction_date,
                batch_number=data.batch_number,
                serial_number=data.serial_number,
                remarks=data.remarks,
                organization_id=data.organization_id,
            ),
            created_by=created_by,
            to_warehouse_id=data.to_warehouse_id,
        )

        # Create transfer in transaction
        transfer_in = await self._create_transaction(
            transaction_type=TransactionType.TRANSFER_IN,
            data=StockInCreate(
                item_id=data.item_id,
                warehouse_id=data.to_warehouse_id,
                quantity=data.quantity,
                unit_cost=unit_cost,
                transaction_date=data.transaction_date,
                batch_number=data.batch_number,
                serial_number=data.serial_number,
                remarks=data.remarks,
                organization_id=data.organization_id,
                reference_type="TRANSFER",
                reference_id=transfer_out.id,
                reference_number=transfer_out.transaction_number,
            ),
            created_by=created_by,
        )

        return transfer_out, transfer_in

    async def create_stock_adjustment(
        self,
        data: StockAdjustmentCreate,
        created_by: Optional[UUID] = None,
    ) -> StockTransaction:
        """Create stock adjustment transaction."""
        transaction_type = (
            TransactionType.ADJUSTMENT_PLUS
            if data.adjustment_quantity > 0
            else TransactionType.ADJUSTMENT_MINUS
        )

        # Get item for unit cost
        item = await self._get_item(data.item_id)
        balance = await self.get_balance(data.item_id, data.warehouse_id)
        unit_cost = balance.average_cost if balance and balance.average_cost > 0 else item.standard_cost

        return await self._create_transaction(
            transaction_type=transaction_type,
            data=StockInCreate(
                item_id=data.item_id,
                warehouse_id=data.warehouse_id,
                quantity=abs(data.adjustment_quantity),
                unit_cost=unit_cost,
                transaction_date=data.transaction_date,
                batch_number=data.batch_number,
                serial_number=data.serial_number,
                remarks=data.adjustment_reason,
                organization_id=data.organization_id,
            ),
            created_by=created_by,
        )

    async def get_transaction(self, id: UUID) -> Optional[StockTransaction]:
        """Get transaction by ID."""
        result = await self.session.execute(
            select(StockTransaction)
            .options(
                selectinload(StockTransaction.item),
                selectinload(StockTransaction.warehouse),
                selectinload(StockTransaction.to_warehouse),
            )
            .where(StockTransaction.id == id, StockTransaction.is_active == True)
        )
        return result.scalar_one_or_none()

    async def list_transactions(
        self,
        organization_id: UUID,
        warehouse_id: Optional[UUID] = None,
        item_id: Optional[UUID] = None,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[StockTransaction]:
        """List transactions with filters."""
        query = (
            select(StockTransaction)
            .options(
                selectinload(StockTransaction.item),
                selectinload(StockTransaction.warehouse),
                selectinload(StockTransaction.to_warehouse),
            )
            .where(
                StockTransaction.organization_id == organization_id,
                StockTransaction.is_active == True,
            )
        )

        if warehouse_id:
            query = query.where(StockTransaction.warehouse_id == warehouse_id)

        if item_id:
            query = query.where(StockTransaction.item_id == item_id)

        if transaction_type:
            query = query.where(StockTransaction.transaction_type == transaction_type)

        if status:
            query = query.where(StockTransaction.status == status)

        if from_date:
            query = query.where(StockTransaction.transaction_date >= from_date)

        if to_date:
            query = query.where(StockTransaction.transaction_date <= to_date)

        result = await self.session.execute(
            query.order_by(StockTransaction.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count_transactions(
        self,
        organization_id: UUID,
        warehouse_id: Optional[UUID] = None,
        item_id: Optional[UUID] = None,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
    ) -> int:
        """Count transactions with filters."""
        query = select(func.count(StockTransaction.id)).where(
            StockTransaction.organization_id == organization_id,
            StockTransaction.is_active == True,
        )

        if warehouse_id:
            query = query.where(StockTransaction.warehouse_id == warehouse_id)

        if item_id:
            query = query.where(StockTransaction.item_id == item_id)

        if transaction_type:
            query = query.where(StockTransaction.transaction_type == transaction_type)

        if status:
            query = query.where(StockTransaction.status == status)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def approve_transaction(
        self,
        id: UUID,
        approved_by: UUID,
    ) -> StockTransaction:
        """Approve a pending transaction and update stock."""
        transaction = await self.get_transaction(id)
        if not transaction:
            raise ValueError("Transaction not found")

        if transaction.status != TransactionStatus.PENDING_APPROVAL:
            raise ValueError(f"Cannot approve transaction with status: {transaction.status}")

        # Update stock balance
        await self._apply_transaction_to_balance(transaction)

        # Update transaction status
        transaction.status = TransactionStatus.APPROVED
        transaction.approved_by = approved_by
        transaction.approved_at = datetime.now(timezone.utc)

        await self.session.flush()
        await self.session.refresh(transaction)
        return transaction

    async def reject_transaction(
        self,
        id: UUID,
        rejected_by: UUID,
        rejection_reason: str,
    ) -> StockTransaction:
        """Reject a pending transaction."""
        transaction = await self.get_transaction(id)
        if not transaction:
            raise ValueError("Transaction not found")

        if transaction.status != TransactionStatus.PENDING_APPROVAL:
            raise ValueError(f"Cannot reject transaction with status: {transaction.status}")

        transaction.status = TransactionStatus.REJECTED
        transaction.approved_by = rejected_by
        transaction.approved_at = datetime.now(timezone.utc)
        transaction.rejection_reason = rejection_reason

        await self.session.flush()
        await self.session.refresh(transaction)
        return transaction

    # ==========================================
    # Helper Methods
    # ==========================================

    async def _create_transaction(
        self,
        transaction_type: TransactionType,
        data: StockInCreate,
        created_by: Optional[UUID] = None,
        to_warehouse_id: Optional[UUID] = None,
    ) -> StockTransaction:
        """Create a stock transaction."""
        # Validate item
        item = await self._get_item(data.item_id)
        if not item:
            raise ValueError("Item not found")
        if item.organization_id != data.organization_id:
            raise ValueError("Item belongs to different organization")

        # Validate warehouse
        warehouse = await self._get_warehouse(data.warehouse_id)
        if not warehouse:
            raise ValueError("Warehouse not found")
        if warehouse.organization_id != data.organization_id:
            raise ValueError("Warehouse belongs to different organization")

        # Get current balance
        balance = await self.get_or_create_balance(
            data.organization_id, data.item_id, data.warehouse_id, created_by
        )
        balance_before = balance.quantity_on_hand

        # Calculate balance after based on transaction type
        if transaction_type in [
            TransactionType.STOCK_IN,
            TransactionType.TRANSFER_IN,
            TransactionType.ADJUSTMENT_PLUS,
            TransactionType.OPENING_BALANCE,
            TransactionType.RETURN_IN,
        ]:
            balance_after = balance_before + data.quantity
        else:
            balance_after = balance_before - data.quantity

        # Generate transaction number
        transaction_number = await self._generate_transaction_number(data.organization_id)

        # Create transaction
        total_cost = data.quantity * data.unit_cost

        transaction = StockTransaction(
            organization_id=data.organization_id,
            transaction_number=transaction_number,
            transaction_type=transaction_type,
            transaction_date=data.transaction_date,
            status=TransactionStatus.APPROVED,  # Auto-approve for now
            item_id=data.item_id,
            warehouse_id=data.warehouse_id,
            to_warehouse_id=to_warehouse_id,
            quantity=data.quantity,
            unit_cost=data.unit_cost,
            total_cost=total_cost,
            balance_before=balance_before,
            balance_after=balance_after,
            batch_number=data.batch_number,
            serial_number=data.serial_number,
            expiry_date=data.expiry_date,
            reference_type=data.reference_type,
            reference_id=data.reference_id,
            reference_number=data.reference_number,
            remarks=data.remarks,
            created_by=created_by,
            approved_by=created_by,
            approved_at=datetime.now(timezone.utc),
        )

        self.session.add(transaction)

        # Update balance immediately (since auto-approved)
        await self._apply_transaction_to_balance(transaction, balance)

        await self.session.flush()
        await self.session.refresh(transaction)
        return transaction

    async def _apply_transaction_to_balance(
        self,
        transaction: StockTransaction,
        balance: Optional[StockBalance] = None,
    ) -> None:
        """Apply transaction to stock balance."""
        if not balance:
            balance = await self.get_or_create_balance(
                transaction.organization_id,
                transaction.item_id,
                transaction.warehouse_id,
            )

        # Update quantity based on transaction type
        if transaction.transaction_type in [
            TransactionType.STOCK_IN,
            TransactionType.TRANSFER_IN,
            TransactionType.ADJUSTMENT_PLUS,
            TransactionType.OPENING_BALANCE,
            TransactionType.RETURN_IN,
        ]:
            # Calculate new average cost
            total_value = balance.total_value + transaction.total_cost
            total_quantity = balance.quantity_on_hand + transaction.quantity
            if total_quantity > 0:
                balance.average_cost = total_value / total_quantity
            balance.quantity_on_hand = total_quantity
            balance.total_value = total_value
        else:
            balance.quantity_on_hand -= transaction.quantity
            balance.total_value = balance.quantity_on_hand * balance.average_cost

        balance.last_transaction_date = datetime.now(timezone.utc)

    async def _generate_transaction_number(self, organization_id: UUID) -> str:
        """Generate unique transaction number."""
        today = date.today()
        prefix = f"STK{today.strftime('%y%m%d')}"

        result = await self.session.execute(
            select(func.count(StockTransaction.id)).where(
                StockTransaction.organization_id == organization_id,
                StockTransaction.transaction_number.like(f"{prefix}%"),
            )
        )
        count = result.scalar_one() + 1
        return f"{prefix}{count:04d}"

    async def _get_item(self, item_id: UUID) -> Optional[ItemMaster]:
        """Get item by ID."""
        result = await self.session.execute(
            select(ItemMaster).where(
                ItemMaster.id == item_id,
                ItemMaster.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def _get_warehouse(self, warehouse_id: UUID) -> Optional[Warehouse]:
        """Get warehouse by ID."""
        result = await self.session.execute(
            select(Warehouse).where(
                Warehouse.id == warehouse_id,
                Warehouse.is_active == True,
            )
        )
        return result.scalar_one_or_none()
