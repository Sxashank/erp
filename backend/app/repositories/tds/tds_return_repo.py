"""TDS Return repository."""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tds.tds_return import TDSReturn, ReturnType, ReturnStatus, Quarter
from app.models.tds.tds_challan import TDSChallan, ChallanStatus
from app.models.tds.tds_entry import TDSEntry
from app.repositories.base import BaseRepository


class TDSReturnRepository(BaseRepository[TDSReturn]):
    """Repository for TDS Return operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(TDSReturn, session)

    async def get_with_details(self, id: UUID) -> Optional[TDSReturn]:
        """Get TDS return with all relationships loaded."""
        query = (
            select(TDSReturn)
            .options(
                selectinload(TDSReturn.organization),
                selectinload(TDSReturn.fy),
                selectinload(TDSReturn.original_return),
            )
            .where(TDSReturn.id == id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_organization(
        self,
        organization_id: UUID,
        return_type: Optional[ReturnType] = None,
        financial_year_id: Optional[UUID] = None,
        quarter: Optional[Quarter] = None,
        status: Optional[ReturnStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[TDSReturn], int]:
        """Get TDS returns for an organization with filters."""
        conditions = [
            TDSReturn.organization_id == organization_id,
            TDSReturn.is_active == True,
        ]

        if return_type:
            conditions.append(TDSReturn.return_type == return_type)
        if financial_year_id:
            conditions.append(TDSReturn.financial_year_id == financial_year_id)
        if quarter:
            conditions.append(TDSReturn.quarter == quarter)
        if status:
            conditions.append(TDSReturn.status == status)

        base_query = (
            select(TDSReturn)
            .options(selectinload(TDSReturn.fy))
            .where(and_(*conditions))
        )

        # Count total
        count_query = select(func.count()).select_from(
            select(TDSReturn).where(and_(*conditions)).subquery()
        )
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = base_query.order_by(
            TDSReturn.financial_year.desc(),
            TDSReturn.quarter.desc(),
        ).offset(skip).limit(limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_by_period(
        self,
        organization_id: UUID,
        return_type: ReturnType,
        financial_year: str,
        quarter: Quarter,
    ) -> Optional[TDSReturn]:
        """Get return for a specific period."""
        query = (
            select(TDSReturn)
            .options(selectinload(TDSReturn.fy))
            .where(
                and_(
                    TDSReturn.organization_id == organization_id,
                    TDSReturn.return_type == return_type,
                    TDSReturn.financial_year == financial_year,
                    TDSReturn.quarter == quarter,
                    TDSReturn.is_original == True,
                    TDSReturn.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_latest_revision(
        self,
        organization_id: UUID,
        return_type: ReturnType,
        financial_year: str,
        quarter: Quarter,
    ) -> Optional[TDSReturn]:
        """Get latest revision of a return."""
        query = (
            select(TDSReturn)
            .where(
                and_(
                    TDSReturn.organization_id == organization_id,
                    TDSReturn.return_type == return_type,
                    TDSReturn.financial_year == financial_year,
                    TDSReturn.quarter == quarter,
                    TDSReturn.is_active == True,
                )
            )
            .order_by(TDSReturn.revision_number.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_revisions(self, original_return_id: UUID) -> List[TDSReturn]:
        """Get all revisions of a return."""
        query = (
            select(TDSReturn)
            .where(
                and_(
                    TDSReturn.original_return_id == original_return_id,
                    TDSReturn.is_active == True,
                )
            )
            .order_by(TDSReturn.revision_number)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_returns(
        self,
        organization_id: UUID,
    ) -> List[TDSReturn]:
        """Get returns pending filing."""
        query = (
            select(TDSReturn)
            .options(selectinload(TDSReturn.fy))
            .where(
                and_(
                    TDSReturn.organization_id == organization_id,
                    TDSReturn.is_active == True,
                    TDSReturn.status.in_([
                        ReturnStatus.DRAFT,
                        ReturnStatus.VALIDATED,
                        ReturnStatus.GENERATED,
                    ]),
                )
            )
            .order_by(TDSReturn.due_date)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_due_returns(
        self,
        organization_id: UUID,
        as_of_date: Optional[date] = None,
    ) -> List[TDSReturn]:
        """Get returns due for filing."""
        if as_of_date is None:
            as_of_date = date.today()

        query = (
            select(TDSReturn)
            .options(selectinload(TDSReturn.fy))
            .where(
                and_(
                    TDSReturn.organization_id == organization_id,
                    TDSReturn.is_active == True,
                    TDSReturn.due_date <= as_of_date,
                    TDSReturn.status.in_([
                        ReturnStatus.DRAFT,
                        ReturnStatus.VALIDATED,
                        ReturnStatus.GENERATED,
                    ]),
                )
            )
            .order_by(TDSReturn.due_date)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_challans_for_return(
        self,
        organization_id: UUID,
        quarter: Quarter,
        financial_year_id: UUID,
        return_type: ReturnType,
    ) -> List[TDSChallan]:
        """Get challans eligible for a return."""
        # Determine quarter date range
        # This will be calculated based on the quarter
        query = (
            select(TDSChallan)
            .options(
                selectinload(TDSChallan.tds_section),
                selectinload(TDSChallan.entries),
            )
            .where(
                and_(
                    TDSChallan.organization_id == organization_id,
                    TDSChallan.financial_year_id == financial_year_id,
                    TDSChallan.return_quarter == quarter.value,
                    TDSChallan.is_active == True,
                    TDSChallan.status.in_([ChallanStatus.PAID, ChallanStatus.VERIFIED]),
                )
            )
            .order_by(TDSChallan.payment_date)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_entries_for_return(
        self,
        organization_id: UUID,
        period_from: date,
        period_to: date,
        return_type: ReturnType,
    ) -> List[TDSEntry]:
        """Get TDS entries for a return period."""
        query = (
            select(TDSEntry)
            .options(
                selectinload(TDSEntry.tds_section),
                selectinload(TDSEntry.vendor),
            )
            .where(
                and_(
                    TDSEntry.organization_id == organization_id,
                    TDSEntry.deduction_date >= period_from,
                    TDSEntry.deduction_date <= period_to,
                    TDSEntry.is_active == True,
                )
            )
            .order_by(TDSEntry.deduction_date)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_deductee_summary(
        self,
        organization_id: UUID,
        period_from: date,
        period_to: date,
    ) -> List[dict]:
        """Get deductee-wise TDS summary for return."""
        query = (
            select(
                TDSEntry.deductee_pan,
                TDSEntry.deductee_name,
                TDSEntry.tds_section_id,
                func.sum(TDSEntry.base_amount).label("total_amount_paid"),
                func.sum(TDSEntry.total_tds).label("total_tds_deducted"),
                func.count(TDSEntry.id).label("transaction_count"),
            )
            .where(
                and_(
                    TDSEntry.organization_id == organization_id,
                    TDSEntry.deduction_date >= period_from,
                    TDSEntry.deduction_date <= period_to,
                    TDSEntry.is_active == True,
                )
            )
            .group_by(
                TDSEntry.deductee_pan,
                TDSEntry.deductee_name,
                TDSEntry.tds_section_id,
            )
        )
        result = await self.session.execute(query)
        return [
            {
                "deductee_pan": row.deductee_pan,
                "deductee_name": row.deductee_name,
                "tds_section_id": row.tds_section_id,
                "total_amount_paid": row.total_amount_paid,
                "total_tds_deducted": row.total_tds_deducted,
                "transaction_count": row.transaction_count,
            }
            for row in result.all()
        ]

    async def update_challan_return_status(
        self,
        challan_ids: List[UUID],
        return_id: UUID,
        quarter: str,
    ) -> int:
        """Mark challans as included in return."""
        stmt = (
            update(TDSChallan)
            .where(TDSChallan.id.in_(challan_ids))
            .values(
                is_included_in_return=True,
                return_id=return_id,
                return_quarter=quarter,
            )
        )
        result = await self.session.execute(stmt)
        return result.rowcount

    async def get_return_summary(
        self,
        organization_id: UUID,
        financial_year_id: Optional[UUID] = None,
    ) -> dict:
        """Get return filing summary."""
        conditions = [
            TDSReturn.organization_id == organization_id,
            TDSReturn.is_active == True,
        ]
        if financial_year_id:
            conditions.append(TDSReturn.financial_year_id == financial_year_id)

        query = (
            select(
                TDSReturn.status,
                func.count(TDSReturn.id).label("count"),
            )
            .where(and_(*conditions))
            .group_by(TDSReturn.status)
        )
        result = await self.session.execute(query)
        rows = result.all()

        summary = {
            "total_returns": 0,
            "draft_count": 0,
            "validated_count": 0,
            "generated_count": 0,
            "uploaded_count": 0,
            "accepted_count": 0,
            "filed_count": 0,
            "rejected_count": 0,
        }

        for row in rows:
            summary["total_returns"] += row.count
            if row.status == ReturnStatus.DRAFT:
                summary["draft_count"] = row.count
            elif row.status == ReturnStatus.VALIDATED:
                summary["validated_count"] = row.count
            elif row.status == ReturnStatus.GENERATED:
                summary["generated_count"] = row.count
            elif row.status == ReturnStatus.UPLOADED:
                summary["uploaded_count"] = row.count
            elif row.status == ReturnStatus.ACCEPTED:
                summary["accepted_count"] = row.count
            elif row.status == ReturnStatus.FILED:
                summary["filed_count"] = row.count
            elif row.status == ReturnStatus.REJECTED:
                summary["rejected_count"] = row.count

        return summary
