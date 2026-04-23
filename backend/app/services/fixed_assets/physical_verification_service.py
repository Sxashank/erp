"""Physical Verification service for Fixed Assets module."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.fixed_assets.fixed_asset import FixedAsset
from app.models.fixed_assets.physical_verification import (
    PhysicalVerificationSchedule,
    PhysicalVerificationEntry,
    PhysicalVerificationDiscrepancy,
    VerificationStatus,
    VerificationResult,
    DiscrepancyStatus,
)
from app.core.constants import AssetStatus
from app.schemas.fixed_assets.physical_verification import (
    VerificationScheduleCreate,
    VerificationScheduleUpdate,
    VerificationEntryCreate,
    VerificationEntryUpdate,
    DiscrepancyCreate,
    DiscrepancyUpdate,
    BulkVerificationEntry,
    VerificationSummaryResponse,
)


class PhysicalVerificationService:
    """Service for physical verification operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ============================================
    # Schedule Operations
    # ============================================

    async def create_schedule(
        self,
        data: VerificationScheduleCreate,
        created_by: Optional[UUID] = None,
    ) -> PhysicalVerificationSchedule:
        """Create a new physical verification schedule."""
        # Generate reference number
        reference = await self._generate_schedule_reference(
            data.organization_id, data.financial_year
        )

        # Get assets to verify
        assets = await self._get_assets_for_verification(
            data.organization_id,
            data.location_id,
            data.category_ids,
        )

        # Create schedule
        schedule = PhysicalVerificationSchedule(
            organization_id=data.organization_id,
            schedule_reference=reference,
            schedule_name=data.schedule_name,
            financial_year=data.financial_year,
            location_id=data.location_id,
            category_ids=data.category_ids,
            scheduled_start_date=data.scheduled_start_date,
            scheduled_end_date=data.scheduled_end_date,
            assigned_to=data.assigned_to,
            team_members=data.team_members,
            total_assets=len(assets),
            status=VerificationStatus.SCHEDULED,
            remarks=data.remarks,
        )
        if created_by:
            schedule.created_by = created_by

        self.session.add(schedule)
        await self.session.flush()

        # Create entries for each asset
        for asset in assets:
            entry = PhysicalVerificationEntry(
                schedule_id=schedule.id,
                asset_id=asset.id,
                expected_location_id=asset.location_id,
                expected_department_id=asset.department_id,
                book_value=asset.wdv_value,
            )
            if created_by:
                entry.created_by = created_by
            self.session.add(entry)

        await self.session.commit()
        await self.session.refresh(schedule)
        return schedule

    async def get_schedule(self, schedule_id: UUID) -> Optional[PhysicalVerificationSchedule]:
        """Get schedule by ID."""
        result = await self.session.execute(
            select(PhysicalVerificationSchedule)
            .options(selectinload(PhysicalVerificationSchedule.entries))
            .where(PhysicalVerificationSchedule.id == schedule_id)
        )
        return result.scalar_one_or_none()

    async def list_schedules(
        self,
        organization_id: UUID,
        financial_year: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[PhysicalVerificationSchedule], int]:
        """List verification schedules."""
        query = select(PhysicalVerificationSchedule).where(
            PhysicalVerificationSchedule.organization_id == organization_id
        )

        if financial_year:
            query = query.where(PhysicalVerificationSchedule.financial_year == financial_year)
        if status:
            query = query.where(PhysicalVerificationSchedule.status == status)

        # Count
        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        # Fetch
        result = await self.session.execute(
            query.order_by(PhysicalVerificationSchedule.scheduled_start_date.desc())
            .offset(skip)
            .limit(limit)
        )
        schedules = list(result.scalars().all())

        return schedules, total

    async def update_schedule(
        self,
        schedule_id: UUID,
        data: VerificationScheduleUpdate,
        updated_by: Optional[UUID] = None,
    ) -> Optional[PhysicalVerificationSchedule]:
        """Update a verification schedule."""
        schedule = await self.get_schedule(schedule_id)
        if not schedule:
            return None

        if schedule.status not in [VerificationStatus.SCHEDULED]:
            raise ValueError("Can only update scheduled verifications")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(schedule, field, value)

        if updated_by:
            schedule.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(schedule)
        return schedule

    async def start_verification(
        self,
        schedule_id: UUID,
        started_by: Optional[UUID] = None,
    ) -> PhysicalVerificationSchedule:
        """Start a verification schedule."""
        schedule = await self.get_schedule(schedule_id)
        if not schedule:
            raise ValueError("Schedule not found")

        if schedule.status != VerificationStatus.SCHEDULED:
            raise ValueError("Can only start scheduled verifications")

        schedule.status = VerificationStatus.IN_PROGRESS
        schedule.actual_start_date = date.today()
        if started_by:
            schedule.updated_by = started_by

        await self.session.commit()
        await self.session.refresh(schedule)
        return schedule

    async def complete_verification(
        self,
        schedule_id: UUID,
        completed_by: Optional[UUID] = None,
    ) -> PhysicalVerificationSchedule:
        """Complete a verification schedule."""
        schedule = await self.get_schedule(schedule_id)
        if not schedule:
            raise ValueError("Schedule not found")

        if schedule.status != VerificationStatus.IN_PROGRESS:
            raise ValueError("Can only complete in-progress verifications")

        # Update summary counts
        await self._update_schedule_summary(schedule)

        schedule.status = VerificationStatus.COMPLETED
        schedule.actual_end_date = date.today()
        if completed_by:
            schedule.updated_by = completed_by

        await self.session.commit()
        await self.session.refresh(schedule)
        return schedule

    async def approve_verification(
        self,
        schedule_id: UUID,
        approved_by: UUID,
    ) -> PhysicalVerificationSchedule:
        """Approve a completed verification."""
        schedule = await self.get_schedule(schedule_id)
        if not schedule:
            raise ValueError("Schedule not found")

        if schedule.status != VerificationStatus.COMPLETED:
            raise ValueError("Can only approve completed verifications")

        schedule.approved_by = approved_by
        schedule.approved_at = datetime.now(timezone.utc)

        await self.session.commit()
        await self.session.refresh(schedule)
        return schedule

    # ============================================
    # Entry Operations
    # ============================================

    async def get_entry(self, entry_id: UUID) -> Optional[PhysicalVerificationEntry]:
        """Get entry by ID."""
        result = await self.session.execute(
            select(PhysicalVerificationEntry)
            .options(selectinload(PhysicalVerificationEntry.asset))
            .where(PhysicalVerificationEntry.id == entry_id)
        )
        return result.scalar_one_or_none()

    async def list_entries(
        self,
        schedule_id: UUID,
        verification_result: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[PhysicalVerificationEntry], int]:
        """List verification entries for a schedule."""
        query = select(PhysicalVerificationEntry).where(
            PhysicalVerificationEntry.schedule_id == schedule_id
        )

        if verification_result:
            query = query.where(
                PhysicalVerificationEntry.verification_result == verification_result
            )

        # Count
        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        # Fetch
        result = await self.session.execute(
            query.options(selectinload(PhysicalVerificationEntry.asset))
            .offset(skip)
            .limit(limit)
        )
        entries = list(result.scalars().all())

        return entries, total

    async def verify_entry(
        self,
        entry_id: UUID,
        data: VerificationEntryCreate,
        verified_by: Optional[UUID] = None,
    ) -> PhysicalVerificationEntry:
        """Record verification result for an entry."""
        entry = await self.get_entry(entry_id)
        if not entry:
            raise ValueError("Entry not found")

        # Check schedule status
        schedule = await self.get_schedule(entry.schedule_id)
        if schedule.status != VerificationStatus.IN_PROGRESS:
            raise ValueError("Verification is not in progress")

        # Update entry
        entry.verification_date = data.verification_date
        entry.verified_by = verified_by
        entry.verification_result = data.verification_result
        entry.asset_condition = data.asset_condition
        entry.actual_location_id = data.actual_location_id
        entry.actual_department_id = data.actual_department_id
        entry.photo_urls = data.photo_urls
        entry.barcode_scan = data.barcode_scan
        entry.condition_notes = data.condition_notes
        entry.remarks = data.remarks

        if verified_by:
            entry.updated_by = verified_by

        # Create discrepancy if needed
        await self._create_discrepancy_if_needed(entry, verified_by)

        # Update schedule summary
        await self._update_schedule_summary(schedule)

        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def bulk_verify(
        self,
        schedule_id: UUID,
        verification_date: date,
        entries: List[BulkVerificationEntry],
        verified_by: Optional[UUID] = None,
    ) -> int:
        """Bulk update verification entries."""
        schedule = await self.get_schedule(schedule_id)
        if not schedule:
            raise ValueError("Schedule not found")

        if schedule.status != VerificationStatus.IN_PROGRESS:
            raise ValueError("Verification is not in progress")

        updated_count = 0
        for entry_data in entries:
            # Find entry
            result = await self.session.execute(
                select(PhysicalVerificationEntry).where(
                    PhysicalVerificationEntry.schedule_id == schedule_id,
                    PhysicalVerificationEntry.asset_id == entry_data.asset_id,
                )
            )
            entry = result.scalar_one_or_none()
            if not entry:
                continue

            entry.verification_date = verification_date
            entry.verified_by = verified_by
            entry.verification_result = entry_data.verification_result
            entry.asset_condition = entry_data.asset_condition
            entry.actual_location_id = entry_data.actual_location_id
            entry.condition_notes = entry_data.condition_notes
            entry.barcode_scan = entry_data.barcode_scan

            if verified_by:
                entry.updated_by = verified_by

            # Create discrepancy if needed
            await self._create_discrepancy_if_needed(entry, verified_by)
            updated_count += 1

        # Update schedule summary
        await self._update_schedule_summary(schedule)

        await self.session.commit()
        return updated_count

    # ============================================
    # Discrepancy Operations
    # ============================================

    async def get_discrepancy(self, discrepancy_id: UUID) -> Optional[PhysicalVerificationDiscrepancy]:
        """Get discrepancy by ID."""
        result = await self.session.execute(
            select(PhysicalVerificationDiscrepancy)
            .options(selectinload(PhysicalVerificationDiscrepancy.entry))
            .where(PhysicalVerificationDiscrepancy.id == discrepancy_id)
        )
        return result.scalar_one_or_none()

    async def list_discrepancies(
        self,
        organization_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[PhysicalVerificationDiscrepancy], int]:
        """List discrepancies."""
        # Build query with join to get org filter
        query = (
            select(PhysicalVerificationDiscrepancy)
            .join(PhysicalVerificationEntry)
            .join(PhysicalVerificationSchedule)
            .where(PhysicalVerificationSchedule.organization_id == organization_id)
        )

        if status:
            query = query.where(PhysicalVerificationDiscrepancy.status == status)

        # Count
        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        # Fetch
        result = await self.session.execute(
            query.options(selectinload(PhysicalVerificationDiscrepancy.entry))
            .order_by(PhysicalVerificationDiscrepancy.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        discrepancies = list(result.scalars().all())

        return discrepancies, total

    async def update_discrepancy(
        self,
        discrepancy_id: UUID,
        data: DiscrepancyUpdate,
        updated_by: Optional[UUID] = None,
    ) -> Optional[PhysicalVerificationDiscrepancy]:
        """Update a discrepancy."""
        discrepancy = await self.get_discrepancy(discrepancy_id)
        if not discrepancy:
            return None

        update_data = data.model_dump(exclude_unset=True)

        if "status" in update_data:
            new_status = update_data["status"]
            if new_status == DiscrepancyStatus.INVESTIGATING:
                discrepancy.investigated_by = updated_by
            elif new_status in [DiscrepancyStatus.RESOLVED, DiscrepancyStatus.WRITTEN_OFF]:
                discrepancy.resolved_by = updated_by
                discrepancy.resolved_at = datetime.now(timezone.utc)

        for field, value in update_data.items():
            setattr(discrepancy, field, value)

        if updated_by:
            discrepancy.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(discrepancy)
        return discrepancy

    # ============================================
    # Reports
    # ============================================

    async def get_verification_summary(
        self,
        organization_id: UUID,
        financial_year: str,
    ) -> VerificationSummaryResponse:
        """Get verification summary for a financial year."""
        # Get all schedules for the FY
        result = await self.session.execute(
            select(PhysicalVerificationSchedule).where(
                PhysicalVerificationSchedule.organization_id == organization_id,
                PhysicalVerificationSchedule.financial_year == financial_year,
            )
        )
        schedules = list(result.scalars().all())

        total_schedules = len(schedules)
        completed_schedules = sum(1 for s in schedules if s.status == VerificationStatus.COMPLETED)
        total_assets = sum(s.total_assets for s in schedules)
        total_verified = sum(s.verified_count for s in schedules)
        total_found = sum(s.found_count for s in schedules)
        total_missing = sum(s.missing_count for s in schedules)
        total_discrepancies = sum(s.discrepancy_count for s in schedules)
        total_value_verified = sum(s.total_value_verified for s in schedules)
        total_value_missing = sum(s.total_value_missing for s in schedules)

        # Count open discrepancies
        open_count_result = await self.session.execute(
            select(func.count())
            .select_from(PhysicalVerificationDiscrepancy)
            .join(PhysicalVerificationEntry)
            .join(PhysicalVerificationSchedule)
            .where(
                PhysicalVerificationSchedule.organization_id == organization_id,
                PhysicalVerificationSchedule.financial_year == financial_year,
                PhysicalVerificationDiscrepancy.status.in_([
                    DiscrepancyStatus.OPEN,
                    DiscrepancyStatus.INVESTIGATING,
                ]),
            )
        )
        open_discrepancies = open_count_result.scalar_one()

        verification_pct = (
            Decimal(total_verified * 100) / Decimal(total_assets)
            if total_assets > 0 else Decimal("0.00")
        )

        return VerificationSummaryResponse(
            organization_id=organization_id,
            financial_year=financial_year,
            total_schedules=total_schedules,
            completed_schedules=completed_schedules,
            total_assets_to_verify=total_assets,
            total_assets_verified=total_verified,
            total_found=total_found,
            total_missing=total_missing,
            total_discrepancies=total_discrepancies,
            open_discrepancies=open_discrepancies,
            total_value_verified=total_value_verified,
            total_value_missing=total_value_missing,
            verification_percentage=verification_pct.quantize(Decimal("0.01")),
        )

    # ============================================
    # Private Methods
    # ============================================

    async def _generate_schedule_reference(
        self,
        organization_id: UUID,
        financial_year: str,
    ) -> str:
        """Generate unique schedule reference."""
        result = await self.session.execute(
            select(func.count()).where(
                PhysicalVerificationSchedule.organization_id == organization_id,
                PhysicalVerificationSchedule.financial_year == financial_year,
            )
        )
        count = result.scalar_one()
        return f"PV/{financial_year}/{count + 1:03d}"

    async def _get_assets_for_verification(
        self,
        organization_id: UUID,
        location_id: Optional[UUID] = None,
        category_ids: Optional[List[UUID]] = None,
    ) -> List[FixedAsset]:
        """Get assets eligible for verification."""
        query = select(FixedAsset).where(
            FixedAsset.organization_id == organization_id,
            FixedAsset.status.in_([AssetStatus.ACTIVE, AssetStatus.FULLY_DEPRECIATED]),
        )

        if location_id:
            query = query.where(FixedAsset.location_id == location_id)
        if category_ids:
            query = query.where(FixedAsset.category_id.in_(category_ids))

        result = await self.session.execute(
            query.order_by(FixedAsset.asset_code)
        )
        return list(result.scalars().all())

    async def _update_schedule_summary(self, schedule: PhysicalVerificationSchedule):
        """Update schedule summary counts."""
        # Count verified
        result = await self.session.execute(
            select(func.count()).where(
                PhysicalVerificationEntry.schedule_id == schedule.id,
                PhysicalVerificationEntry.verification_result.isnot(None),
            )
        )
        schedule.verified_count = result.scalar_one()

        # Count found
        result = await self.session.execute(
            select(func.count()).where(
                PhysicalVerificationEntry.schedule_id == schedule.id,
                PhysicalVerificationEntry.verification_result == VerificationResult.FOUND,
            )
        )
        schedule.found_count = result.scalar_one()

        # Count missing
        result = await self.session.execute(
            select(func.count()).where(
                PhysicalVerificationEntry.schedule_id == schedule.id,
                PhysicalVerificationEntry.verification_result == VerificationResult.MISSING,
            )
        )
        schedule.missing_count = result.scalar_one()

        # Sum value verified
        result = await self.session.execute(
            select(func.coalesce(func.sum(PhysicalVerificationEntry.book_value), 0)).where(
                PhysicalVerificationEntry.schedule_id == schedule.id,
                PhysicalVerificationEntry.verification_result == VerificationResult.FOUND,
            )
        )
        schedule.total_value_verified = result.scalar_one()

        # Sum value missing
        result = await self.session.execute(
            select(func.coalesce(func.sum(PhysicalVerificationEntry.book_value), 0)).where(
                PhysicalVerificationEntry.schedule_id == schedule.id,
                PhysicalVerificationEntry.verification_result == VerificationResult.MISSING,
            )
        )
        schedule.total_value_missing = result.scalar_one()

        # Count discrepancies
        result = await self.session.execute(
            select(func.count())
            .select_from(PhysicalVerificationDiscrepancy)
            .join(PhysicalVerificationEntry)
            .where(PhysicalVerificationEntry.schedule_id == schedule.id)
        )
        schedule.discrepancy_count = result.scalar_one()

    async def _create_discrepancy_if_needed(
        self,
        entry: PhysicalVerificationEntry,
        created_by: Optional[UUID] = None,
    ):
        """Create discrepancy record if verification found issues."""
        if entry.verification_result == VerificationResult.MISSING:
            discrepancy = PhysicalVerificationDiscrepancy(
                entry_id=entry.id,
                discrepancy_type="MISSING",
                description=f"Asset not found during verification",
                value_impact=entry.book_value,
                status=DiscrepancyStatus.OPEN,
            )
            if created_by:
                discrepancy.created_by = created_by
            self.session.add(discrepancy)

        elif entry.verification_result == VerificationResult.MISPLACED:
            if entry.actual_location_id != entry.expected_location_id:
                discrepancy = PhysicalVerificationDiscrepancy(
                    entry_id=entry.id,
                    discrepancy_type="LOCATION_MISMATCH",
                    description=f"Asset found at different location than register",
                    value_impact=Decimal("0.00"),
                    status=DiscrepancyStatus.OPEN,
                )
                if created_by:
                    discrepancy.created_by = created_by
                self.session.add(discrepancy)

        elif entry.asset_condition in ["DAMAGED", "NOT_WORKING"]:
            discrepancy = PhysicalVerificationDiscrepancy(
                entry_id=entry.id,
                discrepancy_type="CONDITION_ISSUE",
                description=f"Asset condition: {entry.asset_condition}. {entry.condition_notes or ''}",
                value_impact=Decimal("0.00"),
                status=DiscrepancyStatus.OPEN,
            )
            if created_by:
                discrepancy.created_by = created_by
            self.session.add(discrepancy)
