"""Payment File repository."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ap_ar.payment_file import PaymentFile, PaymentFileTransaction
from app.repositories.base import BaseRepository


class PaymentFileRepository(BaseRepository[PaymentFile]):
    """Repository for Payment File operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(PaymentFile, session)

    async def get_with_details(self, id: UUID) -> Optional[PaymentFile]:
        """Get payment file with bank account and transactions."""
        query = (
            select(PaymentFile)
            .options(
                selectinload(PaymentFile.organization),
                selectinload(PaymentFile.bank_account),
                selectinload(PaymentFile.transactions),
            )
            .where(
                and_(
                    PaymentFile.id == id,
                    PaymentFile.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_reference(self, file_reference: str) -> Optional[PaymentFile]:
        """Get payment file by reference number."""
        query = (
            select(PaymentFile)
            .options(selectinload(PaymentFile.transactions))
            .where(
                and_(
                    PaymentFile.file_reference == file_reference,
                    PaymentFile.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_organization(
        self,
        organization_id: UUID,
        status: Optional[str] = None,
        file_format: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[PaymentFile], int]:
        """Get payment files for an organization with filters."""
        conditions = [
            PaymentFile.organization_id == organization_id,
            PaymentFile.is_active == True,
        ]

        if status:
            conditions.append(PaymentFile.status == status)
        if file_format:
            conditions.append(PaymentFile.file_format == file_format)
        if from_date:
            conditions.append(PaymentFile.payment_date >= from_date)
        if to_date:
            conditions.append(PaymentFile.payment_date <= to_date)

        # Count total
        count_query = select(func.count()).select_from(
            select(PaymentFile).where(and_(*conditions)).subquery()
        )
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = (
            select(PaymentFile)
            .options(selectinload(PaymentFile.bank_account))
            .where(and_(*conditions))
            .order_by(PaymentFile.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_pending_files(
        self,
        organization_id: UUID,
    ) -> List[PaymentFile]:
        """Get files pending processing."""
        query = (
            select(PaymentFile)
            .where(
                and_(
                    PaymentFile.organization_id == organization_id,
                    PaymentFile.status.in_(["GENERATED", "DOWNLOADED", "UPLOADED"]),
                    PaymentFile.is_active == True,
                )
            )
            .order_by(PaymentFile.created_at)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_next_reference(
        self,
        organization_id: UUID,
        prefix: str,
    ) -> str:
        """Generate next file reference number."""
        today = date.today()
        date_prefix = today.strftime("%Y%m%d")
        full_prefix = f"{prefix}{date_prefix}"

        query = (
            select(func.count())
            .select_from(PaymentFile)
            .where(
                and_(
                    PaymentFile.organization_id == organization_id,
                    PaymentFile.file_reference.like(f"{full_prefix}%"),
                )
            )
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0

        return f"{full_prefix}{count + 1:04d}"

    async def is_payment_in_file(
        self,
        payment_id: UUID,
        exclude_status: Optional[List[str]] = None,
    ) -> bool:
        """Check if payment is already in a file."""
        conditions = [
            PaymentFileTransaction.payment_id == payment_id,
            PaymentFile.is_active == True,
        ]

        if exclude_status:
            conditions.append(~PaymentFile.status.in_(exclude_status))

        query = (
            select(func.count())
            .select_from(PaymentFileTransaction)
            .join(PaymentFile)
            .where(and_(*conditions))
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0
        return count > 0

    async def get_payments_in_files(
        self,
        payment_ids: List[UUID],
        exclude_status: Optional[List[str]] = None,
    ) -> List[UUID]:
        """Get list of payment IDs that are already in files."""
        conditions = [
            PaymentFileTransaction.payment_id.in_(payment_ids),
            PaymentFile.is_active == True,
        ]

        if exclude_status:
            conditions.append(~PaymentFile.status.in_(exclude_status))

        query = (
            select(PaymentFileTransaction.payment_id)
            .join(PaymentFile)
            .where(and_(*conditions))
            .distinct()
        )
        result = await self.session.execute(query)
        return [row[0] for row in result.all()]

    async def update_file_status(
        self,
        id: UUID,
        status: str,
        timestamp_field: Optional[str] = None,
    ) -> Optional[PaymentFile]:
        """Update file status with timestamp."""
        update_data = {"status": status}

        if timestamp_field:
            update_data[timestamp_field] = datetime.utcnow()

        return await self.update(id, update_data)

    async def update_aggregates(self, id: UUID) -> Optional[PaymentFile]:
        """Recalculate and update file aggregates."""
        # Get transaction stats
        query = (
            select(
                func.count(PaymentFileTransaction.id).label("total"),
                func.coalesce(func.sum(PaymentFileTransaction.amount), 0).label("amount"),
                func.count().filter(PaymentFileTransaction.status == "SUCCESS").label("success"),
                func.count().filter(PaymentFileTransaction.status == "FAILED").label("failed"),
            )
            .where(PaymentFileTransaction.payment_file_id == id)
        )
        result = await self.session.execute(query)
        row = result.one()

        update_data = {
            "total_transactions": row.total,
            "total_amount": row.amount,
            "successful_count": row.success or 0,
            "failed_count": row.failed or 0,
        }

        return await self.update(id, update_data)


class PaymentFileTransactionRepository(BaseRepository[PaymentFileTransaction]):
    """Repository for Payment File Transaction operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(PaymentFileTransaction, session)

    async def get_by_payment_file(
        self,
        payment_file_id: UUID,
    ) -> List[PaymentFileTransaction]:
        """Get all transactions for a payment file."""
        query = (
            select(PaymentFileTransaction)
            .where(
                and_(
                    PaymentFileTransaction.payment_file_id == payment_file_id,
                    PaymentFileTransaction.is_active == True,
                )
            )
            .order_by(PaymentFileTransaction.sequence_number)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_payment(
        self,
        payment_id: UUID,
    ) -> List[PaymentFileTransaction]:
        """Get file transactions for a payment."""
        query = (
            select(PaymentFileTransaction)
            .options(selectinload(PaymentFileTransaction.payment_file))
            .where(
                and_(
                    PaymentFileTransaction.payment_id == payment_id,
                    PaymentFileTransaction.is_active == True,
                )
            )
            .order_by(PaymentFileTransaction.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_status(
        self,
        id: UUID,
        status: str,
        bank_reference: Optional[str] = None,
        failure_reason: Optional[str] = None,
    ) -> Optional[PaymentFileTransaction]:
        """Update transaction status."""
        update_data = {
            "status": status,
            "processed_at": datetime.utcnow(),
        }
        if bank_reference:
            update_data["bank_reference"] = bank_reference
        if failure_reason:
            update_data["failure_reason"] = failure_reason

        return await self.update(id, update_data)

    async def bulk_update_status(
        self,
        payment_file_id: UUID,
        status: str,
    ) -> int:
        """Update status for all transactions in a file."""
        transactions = await self.get_by_payment_file(payment_file_id)
        count = 0
        for txn in transactions:
            await self.update_status(txn.id, status)
            count += 1
        return count
