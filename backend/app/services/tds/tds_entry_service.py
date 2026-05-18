"""TDS Entry service."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import TDSChallanStatus, TDSDeducteeType
from app.core.exceptions import NotFoundException, ValidationException
from app.core.tds_ldc import LDCContext, RateSelection, select_tds_rate
from app.models.ap_ar.vendor import Vendor
from app.models.tds.tds_entry import TDSEntry
from app.models.tds.tds_section import TDSSection
from app.repositories.ap_ar.vendor_repo import VendorRepository
from app.repositories.tds.tds_entry_repo import TDSEntryRepository
from app.repositories.tds.tds_section_repo import TDSSectionRepository
from app.schemas.tds.tds_entry import TDSEntryCreate, TDSEntryUpdate


@dataclass
class ThresholdValidationResult:
    """Result of TDS threshold validation."""

    tds_applicable: bool
    reason: str  # SINGLE_THRESHOLD, AGGREGATE_THRESHOLD, BELOW_THRESHOLD, MANUAL
    single_threshold: Decimal
    annual_threshold: Decimal
    current_aggregate: Decimal
    new_aggregate: Decimal
    tds_rate: Decimal
    estimated_tds: Decimal
    estimated_surcharge: Decimal
    estimated_cess: Decimal
    estimated_total_tds: Decimal


def _ldc_from_vendor(vendor: Vendor | None) -> LDCContext | None:
    """Project the vendor's LDC columns into an immutable `LDCContext`.

    Returns ``None`` when the vendor itself is missing. When the vendor is present
    but has no LDC on file, returns a context with ``certificate_no=None`` — the
    rate selector treats that as NO_CERTIFICATE.
    """
    if vendor is None:
        return None
    return LDCContext(
        certificate_no=getattr(vendor, "ldc_certificate_no", None),
        rate=getattr(vendor, "ldc_rate", None),
        limit=getattr(vendor, "ldc_limit", None),
        valid_from=getattr(vendor, "ldc_valid_from", None),
        valid_until=getattr(vendor, "ldc_valid_until", None),
        utilized=getattr(vendor, "ldc_utilized", None) or Decimal("0.00"),
    )


class TDSEntryService:
    """Service for TDS Entry operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TDSEntryRepository(session)
        self.section_repo = TDSSectionRepository(session)
        self.vendor_repo = VendorRepository(session)

    def _get_tds_rate(
        self,
        section: TDSSection,
        deductee_type: TDSDeducteeType,
        has_pan: bool,
    ) -> Decimal:
        """Determine TDS rate based on deductee type and PAN availability.

        This is the LDC-unaware path, preserved for callers that don't carry a
        vendor/date/amount context (threshold estimation, existing tests). New
        deduction paths should use :py:meth:`resolve_rate_with_ldc` instead so
        the Lower Deduction Certificate is honoured.
        """
        if not has_pan:
            return section.rate_no_pan
        if deductee_type == TDSDeducteeType.COMPANY:
            return section.rate_company
        return section.rate_individual

    def resolve_rate_with_ldc(
        self,
        *,
        section: TDSSection,
        deductee_type: TDSDeducteeType,
        has_pan: bool,
        deduction_date: date,
        base_amount: Decimal,
        vendor: Vendor | None = None,
    ) -> RateSelection:
        """Select the TDS rate honouring §206AA and any LDC on file.

        §206AA (no PAN → 20%) always wins; an LDC overrides only the standard
        rate when the certificate is valid on ``deduction_date`` and the
        remaining limit covers ``base_amount``.
        """
        return select_tds_rate(
            rate_no_pan=section.rate_no_pan,
            rate_individual=section.rate_individual,
            rate_company=section.rate_company,
            deductee_type=deductee_type,
            has_pan=has_pan,
            deduction_date=deduction_date,
            base_amount=base_amount,
            ldc=_ldc_from_vendor(vendor),
        )

    def _calculate_surcharge(
        self,
        tds_amount: Decimal,
        base_amount: Decimal,
        section: TDSSection,
        deductee_type: TDSDeducteeType,
    ) -> Decimal:
        """Calculate surcharge based on slabs and deductee type.

        Surcharge slabs format:
        [{"min": 0, "max": 10000000, "rates": {"INDIVIDUAL": 0, "COMPANY": 0}},
         {"min": 10000000, "max": 100000000, "rates": {"INDIVIDUAL": 0.10, "COMPANY": 0.02}}]
        """
        if not section.surcharge_applicable:
            return Decimal("0.00")

        # If surcharge_slabs is configured, use it
        if section.surcharge_slabs:
            for slab in section.surcharge_slabs:
                min_amount = Decimal(str(slab.get("min", 0)))
                max_amount = Decimal(str(slab.get("max", float("inf"))))

                if min_amount <= base_amount < max_amount:
                    rates = slab.get("rates", {})
                    rate = Decimal(str(rates.get(deductee_type.value, slab.get("rate", 0))))
                    return (tds_amount * rate).quantize(Decimal("0.01"))
            return Decimal("0.00")

        # Fallback: Simple 10% surcharge above 1 crore
        if base_amount > Decimal("10000000"):
            return (tds_amount * Decimal("0.10")).quantize(Decimal("0.01"))

        return Decimal("0.00")

    async def validate_threshold(
        self,
        organization_id: UUID,
        vendor_id: UUID | None,
        tds_section_id: UUID,
        base_amount: Decimal,
        deduction_date: date,
        deductee_type: TDSDeducteeType,
        has_pan: bool,
    ) -> ThresholdValidationResult:
        """Validate TDS thresholds and return applicability status.

        Implements Section 194C style thresholds:
        - Single transaction threshold
        - Annual aggregate threshold per vendor
        """
        section = await self.section_repo.get(tds_section_id)
        if not section:
            raise NotFoundException("TDS section not found")

        single_threshold = section.threshold_single
        annual_threshold = section.threshold_annual
        current_aggregate = Decimal("0")
        financial_year_id = None

        # Get aggregate if vendor is specified
        if vendor_id:
            fy = await self.repo.get_financial_year_for_date(organization_id, deduction_date)
            if fy:
                financial_year_id = fy.id
                current_aggregate = await self.repo.get_vendor_aggregate(
                    organization_id, vendor_id, tds_section_id, fy.id
                )

        new_aggregate = current_aggregate + base_amount
        rate = self._get_tds_rate(section, deductee_type, has_pan)

        # Calculate estimated TDS
        tds_amount = base_amount * rate / Decimal("100")
        surcharge = self._calculate_surcharge(tds_amount, base_amount, section, deductee_type)
        cess = (tds_amount + surcharge) * section.cess_rate / Decimal("100")
        total_tds = tds_amount + surcharge + cess

        # Determine if TDS is applicable
        tds_applicable = False
        reason = "BELOW_THRESHOLD"

        # Check single transaction threshold
        if single_threshold > 0 and base_amount >= single_threshold:
            tds_applicable = True
            reason = "SINGLE_THRESHOLD"
        # Check annual aggregate threshold
        elif annual_threshold > 0 and new_aggregate >= annual_threshold:
            tds_applicable = True
            reason = "AGGREGATE_THRESHOLD"
        # Both thresholds are 0 = TDS always applicable
        elif single_threshold == 0 and annual_threshold == 0:
            tds_applicable = True
            reason = "NO_THRESHOLD"

        return ThresholdValidationResult(
            tds_applicable=tds_applicable,
            reason=reason,
            single_threshold=single_threshold,
            annual_threshold=annual_threshold,
            current_aggregate=current_aggregate,
            new_aggregate=new_aggregate,
            tds_rate=rate,
            estimated_tds=tds_amount.quantize(Decimal("0.01")),
            estimated_surcharge=surcharge.quantize(Decimal("0.01")),
            estimated_cess=cess.quantize(Decimal("0.01")),
            estimated_total_tds=total_tds.quantize(Decimal("0.01")),
        )

    async def create(
        self,
        data: TDSEntryCreate,
        created_by: UUID,
        skip_threshold_check: bool = False,
    ) -> TDSEntry:
        """Create a new TDS entry with threshold validation.

        Args:
            data: TDS entry creation data
            created_by: User ID creating the entry
            skip_threshold_check: If True, skip threshold validation (for manual entries)
        """
        # Validate TDS section exists
        section = await self.section_repo.get(data.tds_section_id)
        if not section:
            raise NotFoundException("TDS section not found")

        entry_data = data.model_dump(
            exclude={"tds_rate", "tds_amount", "surcharge", "cess", "total_tds"}
        )
        has_pan = bool(data.deductee_pan)

        # Get financial year for the deduction date
        fy = await self.repo.get_financial_year_for_date(data.organization_id, data.deduction_date)
        financial_year_id = fy.id if fy else None

        # Get current aggregate if vendor is specified
        current_aggregate = Decimal("0")
        vendor_id = entry_data.get("vendor_id")

        if vendor_id and financial_year_id:
            current_aggregate = await self.repo.get_vendor_aggregate(
                data.organization_id, vendor_id, data.tds_section_id, financial_year_id
            )

        new_aggregate = current_aggregate + data.base_amount

        # Validate threshold unless skipped
        threshold_reason = "MANUAL"
        is_threshold_crossed = True

        if not skip_threshold_check:
            validation = await self.validate_threshold(
                organization_id=data.organization_id,
                vendor_id=vendor_id,
                tds_section_id=data.tds_section_id,
                base_amount=data.base_amount,
                deduction_date=data.deduction_date,
                deductee_type=data.deductee_type,
                has_pan=has_pan,
            )

            if not validation.tds_applicable:
                raise ValidationException(
                    f"TDS not applicable. Amount below threshold. "
                    f"Single: ₹{validation.single_threshold}, "
                    f"Annual aggregate: ₹{validation.current_aggregate}/₹{validation.annual_threshold}"
                )

            threshold_reason = validation.reason
            is_threshold_crossed = True

        # Determine rate: §206AA / LDC / standard — cascade handled by resolve_rate_with_ldc.
        vendor: Vendor | None = None
        if vendor_id:
            vendor = await self.vendor_repo.get(vendor_id)

        selection = self.resolve_rate_with_ldc(
            section=section,
            deductee_type=data.deductee_type,
            has_pan=has_pan,
            deduction_date=data.deduction_date,
            base_amount=data.base_amount,
            vendor=vendor,
        )
        rate = selection.rate

        # If LDC applied and the entry didn't carry its own cert_no, stamp the one from the vendor.
        if selection.ldc_applied and not entry_data.get("lower_deduction_cert_no"):
            entry_data["lower_deduction_cert_no"] = selection.ldc_certificate_no

        # Calculate TDS components
        tds_amount = data.base_amount * rate / Decimal("100")
        surcharge = self._calculate_surcharge(
            tds_amount, data.base_amount, section, data.deductee_type
        )
        cess = (tds_amount + surcharge) * section.cess_rate / Decimal("100")
        total_tds = tds_amount + surcharge + cess

        entry = TDSEntry(
            **entry_data,
            financial_year_id=financial_year_id,
            tds_rate=rate,
            tds_amount=tds_amount.quantize(Decimal("0.01")),
            surcharge=surcharge.quantize(Decimal("0.01")),
            cess=cess.quantize(Decimal("0.01")),
            total_tds=total_tds.quantize(Decimal("0.01")),
            is_threshold_crossed=is_threshold_crossed,
            aggregate_amount_ytd=new_aggregate.quantize(Decimal("0.01")),
            threshold_reason=threshold_reason,
            created_by=created_by,
        )
        self.session.add(entry)

        # Accrue vendor LDC utilisation so the next computation sees the updated remaining limit.
        # Done before commit so the update participates in the same transaction.
        if selection.ldc_applied and vendor is not None:
            vendor.ldc_utilized = (vendor.ldc_utilized or Decimal("0.00")) + data.base_amount

        await self.session.flush()
        detailed_entry = await self.repo.get_with_details(entry.id)
        if detailed_entry is None:
            raise NotFoundException("TDS entry not found after creation")
        return detailed_entry

    async def update(
        self,
        id: UUID,
        data: TDSEntryUpdate,
        updated_by: UUID,
    ) -> TDSEntry:
        """Update a TDS entry."""
        entry = await self.repo.get_with_details(id)
        if not entry:
            raise NotFoundException("TDS entry not found")

        # Don't allow updates if return is filed
        if entry.return_filed and not data.return_filed:
            raise ValidationException("Cannot modify TDS entry after return is filed")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(entry, field, value)
        entry.updated_by = updated_by

        await self.session.flush()
        detailed_entry = await self.repo.get_with_details(entry.id)
        if detailed_entry is None:
            raise NotFoundException("TDS entry not found after update")
        return detailed_entry

    async def get(self, id: UUID) -> TDSEntry:
        """Get TDS entry by ID."""
        entry = await self.repo.get_with_details(id)
        if not entry:
            raise NotFoundException("TDS entry not found")
        return entry

    async def get_by_organization(
        self,
        organization_id: UUID,
        from_date: date | None = None,
        to_date: date | None = None,
        challan_status: TDSChallanStatus | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[TDSEntry], int]:
        """Get TDS entries for an organization."""
        return await self.repo.get_by_organization(
            organization_id, from_date, to_date, challan_status, skip, limit
        )

    async def get_pending_challans(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[TDSEntry], int]:
        """Get TDS entries with pending challan payments."""
        return await self.repo.get_pending_challans(organization_id, skip, limit)

    async def get_by_quarter(
        self,
        organization_id: UUID,
        financial_year: str,
        quarter: str,
    ) -> list[TDSEntry]:
        """Get TDS entries for a quarter."""
        return await self.repo.get_by_quarter(organization_id, financial_year, quarter)

    async def get_summary(
        self,
        organization_id: UUID,
        from_date: date,
        to_date: date,
    ) -> list[dict]:
        """Get TDS summary by section."""
        return await self.repo.get_summary_by_section(organization_id, from_date, to_date)

    async def update_challan(
        self,
        id: UUID,
        challan_number: str,
        challan_date: date,
        bank_name: str,
        bsr_code: str,
        updated_by: UUID,
    ) -> TDSEntry:
        """Update challan details for a TDS entry."""
        entry = await self.repo.get(id)
        if not entry:
            raise NotFoundException("TDS entry not found")

        entry.challan_number = challan_number
        entry.challan_date = challan_date
        entry.bank_name = bank_name
        entry.bsr_code = bsr_code
        entry.challan_status = TDSChallanStatus.PAID
        entry.updated_by = updated_by

        await self.session.flush()
        detailed_entry = await self.repo.get_with_details(entry.id)
        if detailed_entry is None:
            raise NotFoundException("TDS entry not found after challan update")
        return detailed_entry

    async def delete(self, id: UUID, deleted_by: UUID) -> None:
        """Soft delete a TDS entry."""
        entry = await self.repo.get(id)
        if not entry:
            raise NotFoundException("TDS entry not found")
        if entry.return_filed:
            raise ValidationException("Cannot delete TDS entry after return is filed")
        entry.soft_delete(deleted_by)
        await self.session.flush()
