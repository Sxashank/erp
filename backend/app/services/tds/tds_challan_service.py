"""TDS Challan service."""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tds.tds_challan import TDSChallan, ChallanStatus
from app.models.tds.tds_entry import TDSEntry
from app.schemas.tds.tds_challan import (
    TDSChallanCreate,
    TDSChallanUpdate,
    TDSChallanPaymentUpdate,
    TDSChallanOLTASUpdate,
    ChallanAggregationRequest,
    ChallanSummary,
)
from app.repositories.tds.tds_challan_repo import TDSChallanRepository
from app.repositories.tds.tds_section_repo import TDSSectionRepository
from app.repositories.tds.tds_entry_repo import TDSEntryRepository
from app.core.constants import TDSChallanStatus
from app.core.exceptions import NotFoundException, ValidationException


class TDSChallanService:
    """Service for TDS Challan operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TDSChallanRepository(session)
        self.section_repo = TDSSectionRepository(session)
        self.entry_repo = TDSEntryRepository(session)

    def _calculate_due_date(self, period_to: date) -> date:
        """Calculate challan due date (7th of next month)."""
        if period_to.month == 12:
            return date(period_to.year + 1, 1, 7)
        else:
            return date(period_to.year, period_to.month + 1, 7)

    def _calculate_interest(
        self,
        total_tds: Decimal,
        due_date: date,
        payment_date: Optional[date] = None,
    ) -> Decimal:
        """Calculate interest for late payment.

        Interest is 1.5% per month or part thereof for delay in payment.
        """
        if payment_date is None:
            payment_date = date.today()

        if payment_date <= due_date:
            return Decimal("0")

        # Calculate months of delay
        months_delay = (payment_date.year - due_date.year) * 12 + (payment_date.month - due_date.month)
        if payment_date.day > due_date.day:
            months_delay += 1

        # Interest rate is 1.5% per month
        interest = total_tds * Decimal("0.015") * months_delay
        return interest.quantize(Decimal("0.01"))

    def _determine_quarter(self, period_from: date, period_to: date) -> str:
        """Determine the return quarter for a period."""
        # Indian FY quarters
        month = period_from.month
        if 4 <= month <= 6:
            return "Q1"
        elif 7 <= month <= 9:
            return "Q2"
        elif 10 <= month <= 12:
            return "Q3"
        else:  # Jan-Mar
            return "Q4"

    def _get_assessment_year(self, period_to: date) -> str:
        """Get assessment year for a period (AY is FY + 1)."""
        if period_to.month <= 3:
            # Jan-Mar belongs to previous FY
            return f"{period_to.year}-{str(period_to.year + 1)[-2:]}"
        else:
            return f"{period_to.year + 1}-{str(period_to.year + 2)[-2:]}"

    async def create(
        self,
        data: TDSChallanCreate,
        created_by: UUID,
    ) -> TDSChallan:
        """Create a new TDS challan."""
        # Validate section exists
        section = await self.section_repo.get(data.tds_section_id)
        if not section:
            raise NotFoundException("TDS section not found")

        # Check for existing challan for same period/section
        existing = await self.repo.get_for_period_section(
            data.organization_id,
            data.tds_section_id,
            data.period_from,
            data.period_to,
        )
        if existing:
            raise ValidationException(
                f"Challan already exists for this period and section (ID: {existing.id})"
            )

        # Determine quarter if not provided
        quarter = data.return_quarter or self._determine_quarter(data.period_from, data.period_to)

        # Create challan
        challan_data = data.model_dump(exclude={"entry_ids"})
        challan_data["return_quarter"] = quarter
        challan_data["created_by"] = created_by

        challan = TDSChallan(**challan_data)
        self.session.add(challan)
        await self.session.flush()

        # Link entries if provided
        if data.entry_ids:
            await self._add_entries_to_challan(challan, data.entry_ids)

        await self.session.commit()
        await self.session.refresh(challan)
        return challan

    async def _add_entries_to_challan(
        self,
        challan: TDSChallan,
        entry_ids: List[UUID],
    ) -> None:
        """Add entries to challan and recalculate totals."""
        # Validate entries
        for entry_id in entry_ids:
            entry = await self.entry_repo.get(entry_id)
            if not entry:
                raise NotFoundException(f"TDS entry {entry_id} not found")
            if entry.challan_id and entry.challan_id != challan.id:
                raise ValidationException(
                    f"Entry {entry_id} is already linked to another challan"
                )
            if entry.tds_section_id != challan.tds_section_id:
                raise ValidationException(
                    f"Entry {entry_id} belongs to a different TDS section"
                )
            if entry.organization_id != challan.organization_id:
                raise ValidationException(
                    f"Entry {entry_id} belongs to a different organization"
                )

        # Link entries
        await self.repo.link_entries_to_challan(challan.id, entry_ids)

        # Recalculate totals
        await self._recalculate_challan_totals(challan)

    async def _recalculate_challan_totals(self, challan: TDSChallan) -> None:
        """Recalculate challan totals from linked entries."""
        entries = await self.repo.get_entries_for_challan(challan.id)

        total_base = Decimal("0")
        total_tds = Decimal("0")
        total_surcharge = Decimal("0")
        total_cess = Decimal("0")

        for entry in entries:
            total_base += entry.base_amount
            total_tds += entry.tds_amount
            total_surcharge += entry.surcharge
            total_cess += entry.cess

        challan.total_base_amount = total_base
        challan.total_tds_amount = total_tds
        challan.total_surcharge = total_surcharge
        challan.total_cess = total_cess
        challan.entry_count = len(entries)

        # Total includes interest and penalty
        challan.total_amount = (
            total_tds
            + total_surcharge
            + total_cess
            + challan.interest_amount
            + challan.penalty_amount
            + challan.other_amount
        )

    async def update(
        self,
        id: UUID,
        data: TDSChallanUpdate,
        updated_by: UUID,
    ) -> TDSChallan:
        """Update a TDS challan."""
        challan = await self.repo.get_with_details(id)
        if not challan:
            raise NotFoundException("TDS challan not found")

        # Don't allow updates if challan is paid/verified
        if challan.status in [ChallanStatus.PAID, ChallanStatus.VERIFIED]:
            raise ValidationException(
                "Cannot modify challan after payment. Use payment update endpoint."
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(challan, field, value)
        challan.updated_by = updated_by

        # Recalculate total if amounts changed
        if any(k in update_data for k in ["interest_amount", "penalty_amount", "other_amount"]):
            await self._recalculate_challan_totals(challan)

        await self.session.commit()
        await self.session.refresh(challan)
        return challan

    async def add_entries(
        self,
        challan_id: UUID,
        entry_ids: List[UUID],
        updated_by: UUID,
    ) -> TDSChallan:
        """Add entries to an existing challan."""
        challan = await self.repo.get_with_details(challan_id)
        if not challan:
            raise NotFoundException("TDS challan not found")

        if challan.status != ChallanStatus.DRAFT:
            raise ValidationException("Can only add entries to DRAFT challans")

        await self._add_entries_to_challan(challan, entry_ids)
        challan.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(challan)
        return challan

    async def remove_entries(
        self,
        challan_id: UUID,
        entry_ids: List[UUID],
        updated_by: UUID,
    ) -> TDSChallan:
        """Remove entries from a challan."""
        challan = await self.repo.get_with_details(challan_id)
        if not challan:
            raise NotFoundException("TDS challan not found")

        if challan.status != ChallanStatus.DRAFT:
            raise ValidationException("Can only remove entries from DRAFT challans")

        # Unlink entries
        await self.repo.unlink_entries_from_challan(entry_ids)

        # Recalculate totals
        await self._recalculate_challan_totals(challan)
        challan.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(challan)
        return challan

    async def finalize(
        self,
        id: UUID,
        updated_by: UUID,
    ) -> TDSChallan:
        """Finalize a challan (move from DRAFT to PENDING)."""
        challan = await self.repo.get_with_details(id)
        if not challan:
            raise NotFoundException("TDS challan not found")

        if challan.status != ChallanStatus.DRAFT:
            raise ValidationException("Only DRAFT challans can be finalized")

        if challan.entry_count == 0:
            raise ValidationException("Cannot finalize challan with no entries")

        # Calculate interest if due date has passed
        due_date = self._calculate_due_date(challan.period_to)
        if date.today() > due_date:
            tds_total = challan.total_tds_amount + challan.total_surcharge + challan.total_cess
            challan.interest_amount = self._calculate_interest(tds_total, due_date)
            await self._recalculate_challan_totals(challan)

        challan.status = ChallanStatus.PENDING
        challan.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(challan)
        return challan

    async def record_payment(
        self,
        id: UUID,
        data: TDSChallanPaymentUpdate,
        updated_by: UUID,
    ) -> TDSChallan:
        """Record payment details for a challan."""
        challan = await self.repo.get_with_details(id)
        if not challan:
            raise NotFoundException("TDS challan not found")

        if challan.status not in [ChallanStatus.DRAFT, ChallanStatus.PENDING]:
            raise ValidationException("Challan is already paid or cancelled")

        # Update payment details
        challan.challan_number = data.challan_number
        challan.bsr_code = data.bsr_code
        challan.serial_number = data.serial_number
        challan.payment_date = data.payment_date
        challan.payment_mode = data.payment_mode
        challan.bank_name = data.bank_name
        challan.bank_branch = data.bank_branch
        challan.bank_account_number = data.bank_account_number
        challan.cheque_dd_number = data.cheque_dd_number
        challan.cheque_dd_date = data.cheque_dd_date
        challan.status = ChallanStatus.PAID
        challan.updated_by = updated_by

        # Update linked entries with challan details
        entries = await self.repo.get_entries_for_challan(challan.id)
        for entry in entries:
            entry.challan_number = data.challan_number
            entry.challan_date = data.payment_date
            entry.bank_name = data.bank_name
            entry.bsr_code = data.bsr_code
            entry.challan_status = TDSChallanStatus.PAID

        await self.session.commit()
        await self.session.refresh(challan)
        return challan

    async def verify_oltas(
        self,
        id: UUID,
        data: TDSChallanOLTASUpdate,
        updated_by: UUID,
    ) -> TDSChallan:
        """Update OLTAS verification status."""
        challan = await self.repo.get_with_details(id)
        if not challan:
            raise NotFoundException("TDS challan not found")

        if challan.status != ChallanStatus.PAID:
            raise ValidationException("Only PAID challans can be verified")

        challan.oltas_acknowledgment = data.oltas_acknowledgment
        challan.oltas_status = data.oltas_status
        challan.oltas_verified_at = data.oltas_verified_at
        challan.status = ChallanStatus.VERIFIED
        challan.updated_by = updated_by

        # Update linked entries
        entries = await self.repo.get_entries_for_challan(challan.id)
        for entry in entries:
            entry.challan_status = TDSChallanStatus.VERIFIED

        await self.session.commit()
        await self.session.refresh(challan)
        return challan

    async def cancel(
        self,
        id: UUID,
        reason: str,
        updated_by: UUID,
    ) -> TDSChallan:
        """Cancel a challan."""
        challan = await self.repo.get_with_details(id)
        if not challan:
            raise NotFoundException("TDS challan not found")

        if challan.status in [ChallanStatus.PAID, ChallanStatus.VERIFIED]:
            raise ValidationException("Cannot cancel paid/verified challans")

        if challan.is_included_in_return:
            raise ValidationException("Cannot cancel challan included in return")

        # Unlink all entries
        entries = await self.repo.get_entries_for_challan(challan.id)
        entry_ids = [e.id for e in entries]
        if entry_ids:
            await self.repo.unlink_entries_from_challan(entry_ids)

        challan.status = ChallanStatus.CANCELLED
        challan.remarks = f"Cancelled: {reason}"
        challan.entry_count = 0
        challan.total_base_amount = Decimal("0")
        challan.total_tds_amount = Decimal("0")
        challan.total_surcharge = Decimal("0")
        challan.total_cess = Decimal("0")
        challan.total_amount = Decimal("0")
        challan.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(challan)
        return challan

    async def get(self, id: UUID) -> TDSChallan:
        """Get challan by ID."""
        challan = await self.repo.get_with_details(id)
        if not challan:
            raise NotFoundException("TDS challan not found")
        return challan

    async def get_with_entries(self, id: UUID) -> TDSChallan:
        """Get challan with all entries."""
        challan = await self.repo.get_with_entries(id)
        if not challan:
            raise NotFoundException("TDS challan not found")
        return challan

    async def get_by_organization(
        self,
        organization_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        status: Optional[ChallanStatus] = None,
        tds_section_id: Optional[UUID] = None,
        financial_year_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[TDSChallan], int]:
        """Get challans for an organization."""
        return await self.repo.get_by_organization(
            organization_id,
            from_date,
            to_date,
            status,
            tds_section_id,
            financial_year_id,
            skip,
            limit,
        )

    async def get_summary(
        self,
        organization_id: UUID,
        financial_year_id: Optional[UUID] = None,
    ) -> ChallanSummary:
        """Get challan summary statistics."""
        summary_dict = await self.repo.get_summary(organization_id, financial_year_id)
        return ChallanSummary(**summary_dict)

    async def get_due_for_payment(
        self,
        organization_id: UUID,
    ) -> List[TDSChallan]:
        """Get challans due for payment."""
        return await self.repo.get_due_for_payment(organization_id)

    async def generate_challans(
        self,
        data: ChallanAggregationRequest,
        created_by: UUID,
    ) -> List[TDSChallan]:
        """Auto-generate challans for a period.

        Groups unlinked TDS entries by section (if group_by_section=True)
        and creates challans for each group.
        """
        created_challans = []

        if data.tds_section_id:
            # Generate for specific section
            sections = [await self.section_repo.get(data.tds_section_id)]
            if not sections[0]:
                raise NotFoundException("TDS section not found")
        else:
            # Get all sections with unlinked entries
            sections = await self.section_repo.get_all()

        for section in sections:
            if not section:
                continue

            # Get unlinked entries for this section in the period
            entries = await self.repo.get_unlinked_entries(
                data.organization_id,
                section.id,
                data.period_from,
                data.period_to,
            )

            if not entries:
                continue

            # Check for existing challan
            existing = await self.repo.get_for_period_section(
                data.organization_id,
                section.id,
                data.period_from,
                data.period_to,
            )

            if existing:
                # Add entries to existing challan
                entry_ids = [e.id for e in entries]
                await self._add_entries_to_challan(existing, entry_ids)
                created_challans.append(existing)
            else:
                # Get organization details for deductor info
                first_entry = entries[0]
                org = first_entry.organization

                # Create new challan
                challan = TDSChallan(
                    organization_id=data.organization_id,
                    tds_section_id=section.id,
                    financial_year_id=data.financial_year_id,
                    assessment_year=self._get_assessment_year(data.period_to),
                    period_from=data.period_from,
                    period_to=data.period_to,
                    return_quarter=self._determine_quarter(data.period_from, data.period_to),
                    deductor_tan=org.tan_number if org.tan_number else "",
                    deductor_name=org.name,
                    deductor_address=org.address if hasattr(org, 'address') else None,
                    created_by=created_by,
                )
                self.session.add(challan)
                await self.session.flush()

                # Link entries
                entry_ids = [e.id for e in entries]
                await self._add_entries_to_challan(challan, entry_ids)
                created_challans.append(challan)

        await self.session.commit()

        # Refresh all created challans
        for challan in created_challans:
            await self.session.refresh(challan)

        return created_challans

    async def delete(self, id: UUID, deleted_by: UUID) -> None:
        """Soft delete a TDS challan."""
        challan = await self.repo.get(id)
        if not challan:
            raise NotFoundException("TDS challan not found")

        if challan.status in [ChallanStatus.PAID, ChallanStatus.VERIFIED]:
            raise ValidationException("Cannot delete paid/verified challans")

        if challan.is_included_in_return:
            raise ValidationException("Cannot delete challan included in return")

        # Unlink entries first
        entries = await self.repo.get_entries_for_challan(challan.id)
        entry_ids = [e.id for e in entries]
        if entry_ids:
            await self.repo.unlink_entries_from_challan(entry_ids)

        challan.soft_delete(deleted_by)
        await self.session.commit()
