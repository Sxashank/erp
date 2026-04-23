"""TDS Return service."""

from datetime import date, datetime
from decimal import Decimal
import hashlib
import os
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tds.tds_return import TDSReturn, ReturnType, ReturnStatus, Quarter
from app.models.tds.tds_challan import TDSChallan
from app.schemas.tds.tds_return import (
    TDSReturnCreate,
    TDSReturnUpdate,
    FilingDetailsUpdate,
    ReturnValidationResult,
    ValidationError,
)
from app.repositories.tds.tds_return_repo import TDSReturnRepository
from app.repositories.tds.tds_challan_repo import TDSChallanRepository
from app.repositories.tds.tds_entry_repo import TDSEntryRepository
from app.core.exceptions import NotFoundException, ValidationException


class TDSReturnService:
    """Service for TDS Return operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TDSReturnRepository(session)
        self.challan_repo = TDSChallanRepository(session)
        self.entry_repo = TDSEntryRepository(session)

    def _get_quarter_dates(self, financial_year: str, quarter: Quarter) -> Tuple[date, date]:
        """Get start and end dates for a quarter."""
        year_start = int(financial_year.split("-")[0])

        quarter_dates = {
            Quarter.Q1: (date(year_start, 4, 1), date(year_start, 6, 30)),
            Quarter.Q2: (date(year_start, 7, 1), date(year_start, 9, 30)),
            Quarter.Q3: (date(year_start, 10, 1), date(year_start, 12, 31)),
            Quarter.Q4: (date(year_start + 1, 1, 1), date(year_start + 1, 3, 31)),
        }
        return quarter_dates[quarter]

    def _get_assessment_year(self, financial_year: str) -> str:
        """Get assessment year from financial year (AY = FY + 1)."""
        year_start = int(financial_year.split("-")[0])
        return f"{year_start + 1}-{str(year_start + 2)[-2:]}"

    def _get_due_date(self, quarter: Quarter, financial_year: str) -> date:
        """Get return filing due date for a quarter.

        Due dates:
        - Q1 (Apr-Jun): 31st July
        - Q2 (Jul-Sep): 31st October
        - Q3 (Oct-Dec): 31st January
        - Q4 (Jan-Mar): 31st May
        """
        year_start = int(financial_year.split("-")[0])

        due_dates = {
            Quarter.Q1: date(year_start, 7, 31),
            Quarter.Q2: date(year_start, 10, 31),
            Quarter.Q3: date(year_start + 1, 1, 31),
            Quarter.Q4: date(year_start + 1, 5, 31),
        }
        return due_dates[quarter]

    async def create(
        self,
        data: TDSReturnCreate,
        created_by: UUID,
    ) -> TDSReturn:
        """Create a new TDS return."""
        # Check for existing return
        existing = await self.repo.get_by_period(
            data.organization_id,
            data.return_type,
            data.financial_year,
            data.quarter,
        )
        if existing:
            raise ValidationException(
                f"Return already exists for {data.return_type.value} "
                f"{data.financial_year} {data.quarter.value}"
            )

        # Calculate period dates
        period_from, period_to = self._get_quarter_dates(data.financial_year, data.quarter)
        assessment_year = self._get_assessment_year(data.financial_year)
        due_date = self._get_due_date(data.quarter, data.financial_year)

        # Check if late
        today = date.today()
        is_late = today > due_date
        days_late = (today - due_date).days if is_late else 0

        return_data = data.model_dump()
        return_data.update({
            "period_from": period_from,
            "period_to": period_to,
            "assessment_year": assessment_year,
            "due_date": due_date,
            "is_late": is_late,
            "days_late": days_late,
            "created_by": created_by,
        })

        tds_return = TDSReturn(**return_data)
        self.session.add(tds_return)

        # Calculate totals from challans/entries
        await self._calculate_return_totals(tds_return)

        await self.session.commit()
        await self.session.refresh(tds_return)
        return tds_return

    async def _calculate_return_totals(self, tds_return: TDSReturn) -> None:
        """Calculate return totals from challans and entries."""
        # Get challans for this quarter
        challans = await self.repo.get_challans_for_return(
            tds_return.organization_id,
            tds_return.quarter,
            tds_return.financial_year_id,
            tds_return.return_type,
        )

        # Get entries for this period
        entries = await self.repo.get_entries_for_return(
            tds_return.organization_id,
            tds_return.period_from,
            tds_return.period_to,
            tds_return.return_type,
        )

        # Calculate totals
        total_challans = len(challans)
        total_deposited = Decimal("0")
        total_interest = Decimal("0")

        for challan in challans:
            total_deposited += challan.total_amount
            total_interest += challan.interest_amount

        # Unique deductees (by PAN or name if no PAN)
        deductee_set = set()
        total_amount_paid = Decimal("0")
        total_deducted = Decimal("0")

        for entry in entries:
            key = entry.deductee_pan or entry.deductee_name
            deductee_set.add(key)
            total_amount_paid += entry.base_amount
            total_deducted += entry.total_tds

        tds_return.total_challans = total_challans
        tds_return.total_deductees = len(deductee_set)
        tds_return.total_amount_paid = total_amount_paid
        tds_return.total_tds_deducted = total_deducted
        tds_return.total_tds_deposited = total_deposited
        tds_return.total_interest = total_interest
        tds_return.total_late_fee = tds_return.calculate_late_fee()

    async def update(
        self,
        id: UUID,
        data: TDSReturnUpdate,
        updated_by: UUID,
    ) -> TDSReturn:
        """Update a TDS return."""
        tds_return = await self.repo.get_with_details(id)
        if not tds_return:
            raise NotFoundException("TDS return not found")

        if tds_return.status in [ReturnStatus.FILED, ReturnStatus.ACCEPTED]:
            raise ValidationException(
                "Cannot modify filed/accepted return. Create a revision instead."
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tds_return, field, value)
        tds_return.updated_by = updated_by

        # Reset status if significant changes
        if update_data:
            tds_return.status = ReturnStatus.DRAFT
            tds_return.validation_errors = None
            tds_return.validation_warnings = None

        await self.session.commit()
        await self.session.refresh(tds_return)
        return tds_return

    async def validate(
        self,
        id: UUID,
        updated_by: UUID,
    ) -> ReturnValidationResult:
        """Validate a TDS return."""
        tds_return = await self.repo.get_with_details(id)
        if not tds_return:
            raise NotFoundException("TDS return not found")

        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []

        # Refresh totals
        await self._calculate_return_totals(tds_return)

        # Validation rules
        # 1. Check if TAN is valid format
        if not self._validate_tan(tds_return.deductor_tan):
            errors.append(ValidationError(
                code="INVALID_TAN",
                message="Invalid TAN format",
                field="deductor_tan",
            ))

        # 2. Check if there are challans
        if tds_return.total_challans == 0:
            warnings.append(ValidationError(
                code="NO_CHALLANS",
                message="No challans found for this period. This will be a NIL return.",
            ))

        # 3. Check TDS deposited vs deducted
        if tds_return.total_tds_deposited < tds_return.total_tds_deducted:
            diff = tds_return.total_tds_deducted - tds_return.total_tds_deposited
            errors.append(ValidationError(
                code="TDS_SHORTFALL",
                message=f"TDS deposited ({tds_return.total_tds_deposited}) is less than "
                        f"TDS deducted ({tds_return.total_tds_deducted}). Shortfall: {diff}",
            ))

        # 4. Check PAN for all deductees
        entries = await self.repo.get_entries_for_return(
            tds_return.organization_id,
            tds_return.period_from,
            tds_return.period_to,
            tds_return.return_type,
        )

        for idx, entry in enumerate(entries):
            if not entry.deductee_pan:
                warnings.append(ValidationError(
                    code="MISSING_PAN",
                    message=f"PAN missing for deductee: {entry.deductee_name}",
                    row=idx + 1,
                ))
            elif not self._validate_pan(entry.deductee_pan):
                errors.append(ValidationError(
                    code="INVALID_PAN",
                    message=f"Invalid PAN format for: {entry.deductee_name}",
                    field="deductee_pan",
                    row=idx + 1,
                ))

        # 5. Check late filing
        if tds_return.is_late:
            warnings.append(ValidationError(
                code="LATE_FILING",
                message=f"Return is {tds_return.days_late} days late. "
                        f"Late fee of Rs. {tds_return.calculate_late_fee()} will apply.",
            ))

        # Store validation results
        tds_return.validation_errors = [e.model_dump() for e in errors]
        tds_return.validation_warnings = [w.model_dump() for w in warnings]
        tds_return.last_validated_at = datetime.utcnow()

        # Update status
        if not errors:
            tds_return.status = ReturnStatus.VALIDATED
        tds_return.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(tds_return)

        return ReturnValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            total_challans=tds_return.total_challans,
            total_deductees=tds_return.total_deductees,
            total_tds_deducted=tds_return.total_tds_deducted,
            total_tds_deposited=tds_return.total_tds_deposited,
        )

    def _validate_tan(self, tan: str) -> bool:
        """Validate TAN format (4 letters + 5 digits + 1 letter)."""
        if not tan or len(tan) != 10:
            return False
        return (
            tan[:4].isalpha() and
            tan[4:9].isdigit() and
            tan[9].isalpha()
        )

    def _validate_pan(self, pan: str) -> bool:
        """Validate PAN format (5 letters + 4 digits + 1 letter)."""
        if not pan or len(pan) != 10:
            return False
        return (
            pan[:5].isalpha() and
            pan[5:9].isdigit() and
            pan[9].isalpha()
        )

    async def generate_file(
        self,
        id: UUID,
        updated_by: UUID,
        include_nil: bool = False,
    ) -> Tuple[str, str]:
        """Generate return file in NSDL format.

        Returns tuple of (file_name, file_path).
        """
        tds_return = await self.repo.get_with_details(id)
        if not tds_return:
            raise NotFoundException("TDS return not found")

        if tds_return.status not in [ReturnStatus.VALIDATED, ReturnStatus.GENERATED]:
            raise ValidationException(
                "Return must be validated before file generation"
            )

        if tds_return.total_challans == 0 and not include_nil:
            raise ValidationException(
                "No challans found. Set include_nil=true for NIL return."
            )

        # Get data for file generation
        challans = await self.repo.get_challans_for_return(
            tds_return.organization_id,
            tds_return.quarter,
            tds_return.financial_year_id,
            tds_return.return_type,
        )

        entries = await self.repo.get_entries_for_return(
            tds_return.organization_id,
            tds_return.period_from,
            tds_return.period_to,
            tds_return.return_type,
        )

        # Generate file content
        file_content = self._generate_nsdl_file(tds_return, challans, entries)

        # Generate file name
        file_name = (
            f"{tds_return.return_type.value}_"
            f"{tds_return.financial_year.replace('-', '')}_"
            f"{tds_return.quarter.value}_"
            f"{tds_return.deductor_tan}_"
            f"{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
        )

        # Calculate hash
        file_hash = hashlib.sha256(file_content.encode()).hexdigest()

        # Save file (in real implementation, would save to storage)
        # For now, we'll just store the metadata
        tds_return.file_name = file_name
        tds_return.file_path = f"/tds-returns/{file_name}"
        tds_return.file_hash = file_hash
        tds_return.file_generated_at = datetime.utcnow()
        tds_return.status = ReturnStatus.GENERATED
        tds_return.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(tds_return)

        return file_name, file_content

    def _generate_nsdl_file(
        self,
        tds_return: TDSReturn,
        challans: List[TDSChallan],
        entries: list,
    ) -> str:
        """Generate NSDL format return file.

        This is a simplified version. Real implementation would follow
        exact NSDL RPU file format specifications.
        """
        lines = []

        # Header record (simplified)
        lines.append(f"^FH^{tds_return.return_type.value}^{tds_return.financial_year}^{tds_return.quarter.value}^")

        # Batch header
        lines.append(
            f"^BH^{tds_return.deductor_tan}^{tds_return.deductor_name}^"
            f"{tds_return.deductor_address or ''}^{tds_return.deductor_city or ''}^"
            f"{tds_return.deductor_state or ''}^{tds_return.deductor_pincode or ''}^"
        )

        # Challan details
        for challan in challans:
            lines.append(
                f"^CD^{challan.bsr_code or ''}^{challan.challan_number or ''}^"
                f"{challan.payment_date}^{challan.total_amount}^{challan.total_tds_amount}^"
                f"{challan.total_surcharge}^{challan.total_cess}^{challan.interest_amount}^"
            )

        # Deductee details
        for entry in entries:
            lines.append(
                f"^DD^{entry.deductee_pan or 'PANAPPLIED'}^{entry.deductee_name}^"
                f"{entry.base_amount}^{entry.tds_amount}^{entry.surcharge}^"
                f"{entry.cess}^{entry.total_tds}^{entry.deduction_date}^"
            )

        # Trailer
        lines.append(f"^FT^{len(challans)}^{len(entries)}^{tds_return.total_tds_deposited}^")

        return "\n".join(lines)

    async def update_filing_details(
        self,
        id: UUID,
        data: FilingDetailsUpdate,
        updated_by: UUID,
    ) -> TDSReturn:
        """Update filing details after submission."""
        tds_return = await self.repo.get_with_details(id)
        if not tds_return:
            raise NotFoundException("TDS return not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tds_return, field, value)

        # Update status based on filed data
        if data.acknowledgment_number:
            tds_return.status = ReturnStatus.FILED
            tds_return.accepted_at = datetime.utcnow()
        elif data.provisional_receipt_number:
            tds_return.status = ReturnStatus.UPLOADED

        tds_return.updated_by = updated_by

        # Mark challans as included in return
        challans = await self.repo.get_challans_for_return(
            tds_return.organization_id,
            tds_return.quarter,
            tds_return.financial_year_id,
            tds_return.return_type,
        )
        challan_ids = [c.id for c in challans]
        if challan_ids:
            await self.repo.update_challan_return_status(
                challan_ids,
                tds_return.id,
                tds_return.quarter.value,
            )

        await self.session.commit()
        await self.session.refresh(tds_return)
        return tds_return

    async def create_revision(
        self,
        original_return_id: UUID,
        reason: str,
        created_by: UUID,
    ) -> TDSReturn:
        """Create a revision of a filed return."""
        original = await self.repo.get_with_details(original_return_id)
        if not original:
            raise NotFoundException("Original return not found")

        if original.status not in [ReturnStatus.FILED, ReturnStatus.ACCEPTED]:
            raise ValidationException(
                "Can only revise filed/accepted returns"
            )

        # Get latest revision number
        latest = await self.repo.get_latest_revision(
            original.organization_id,
            original.return_type,
            original.financial_year,
            original.quarter,
        )
        next_revision = (latest.revision_number if latest else 0) + 1

        # Create revision
        revision = TDSReturn(
            organization_id=original.organization_id,
            return_type=original.return_type,
            financial_year_id=original.financial_year_id,
            financial_year=original.financial_year,
            assessment_year=original.assessment_year,
            quarter=original.quarter,
            period_from=original.period_from,
            period_to=original.period_to,
            status=ReturnStatus.DRAFT,
            is_original=False,
            revision_number=next_revision,
            original_return_id=original.id if original.is_original else original.original_return_id,
            deductor_tan=original.deductor_tan,
            deductor_name=original.deductor_name,
            deductor_pan=original.deductor_pan,
            deductor_type=original.deductor_type,
            deductor_category=original.deductor_category,
            deductor_address=original.deductor_address,
            deductor_city=original.deductor_city,
            deductor_state=original.deductor_state,
            deductor_pincode=original.deductor_pincode,
            deductor_email=original.deductor_email,
            deductor_phone=original.deductor_phone,
            responsible_person_name=original.responsible_person_name,
            responsible_person_designation=original.responsible_person_designation,
            responsible_person_address=original.responsible_person_address,
            responsible_person_pan=original.responsible_person_pan,
            due_date=original.due_date,
            is_late=True,  # Revisions are always after due date
            days_late=max(0, (date.today() - original.due_date).days),
            remarks=f"Revision {next_revision}: {reason}",
            created_by=created_by,
        )

        self.session.add(revision)

        # Calculate totals
        await self._calculate_return_totals(revision)

        # Mark original as revised
        original.status = ReturnStatus.REVISED

        await self.session.commit()
        await self.session.refresh(revision)
        return revision

    async def get(self, id: UUID) -> TDSReturn:
        """Get return by ID."""
        tds_return = await self.repo.get_with_details(id)
        if not tds_return:
            raise NotFoundException("TDS return not found")
        return tds_return

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
        """Get returns for an organization."""
        return await self.repo.get_by_organization(
            organization_id,
            return_type,
            financial_year_id,
            quarter,
            status,
            skip,
            limit,
        )

    async def get_pending(self, organization_id: UUID) -> List[TDSReturn]:
        """Get pending returns."""
        return await self.repo.get_pending_returns(organization_id)

    async def get_due(self, organization_id: UUID) -> List[TDSReturn]:
        """Get returns due for filing."""
        return await self.repo.get_due_returns(organization_id)

    async def delete(self, id: UUID, deleted_by: UUID) -> None:
        """Soft delete a TDS return."""
        tds_return = await self.repo.get(id)
        if not tds_return:
            raise NotFoundException("TDS return not found")

        if tds_return.status in [ReturnStatus.FILED, ReturnStatus.ACCEPTED]:
            raise ValidationException("Cannot delete filed/accepted returns")

        tds_return.soft_delete(deleted_by)
        await self.session.commit()
