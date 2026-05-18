"""Maintenance and AMC Service.

This service handles:
- AMC contract management
- Maintenance request lifecycle
- Preventive maintenance scheduling
- Warranty tracking
- Maintenance analytics and alerts
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.fixed_assets.maintenance import (
    AMCContract,
    MaintenanceRequest,
    MaintenanceSchedule,
    AssetWarranty,
    AMCStatus,
    AMCType,
    MaintenanceStatus,
    MaintenanceType,
    MaintenancePriority,
)
from app.models.fixed_assets.fixed_asset import FixedAsset
from app.schemas.fixed_assets.maintenance import (
    AMCContractCreate,
    AMCContractUpdate,
    AMCContractRenew,
    MaintenanceRequestCreate,
    MaintenanceRequestUpdate,
    MaintenanceRequestComplete,
    MaintenanceScheduleCreate,
    MaintenanceScheduleUpdate,
    AssetWarrantyCreate,
    AssetWarrantyUpdate,
    MaintenanceSummaryResponse,
    AssetMaintenanceHistoryResponse,
)
from app.core.exceptions import ConcurrentModificationError
from app.core.optimistic_lock import increment_version


class MaintenanceService:
    """Service for maintenance and AMC operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # =========================================
    # AMC Contract Operations
    # =========================================

    async def create_amc_contract(
        self,
        data: AMCContractCreate,
        created_by: UUID,
    ) -> AMCContract:
        """Create a new AMC contract."""
        # Calculate GST
        gst_amount = data.contract_value * data.gst_rate / 100
        total_value = data.contract_value + gst_amount

        contract = AMCContract(
            organization_id=data.organization_id,
            contract_number=data.contract_number,
            contract_name=data.contract_name,
            amc_type=data.amc_type,
            status=AMCStatus.DRAFT,
            vendor_id=data.vendor_id,
            vendor_contact_person=data.vendor_contact_person,
            vendor_contact_phone=data.vendor_contact_phone,
            vendor_contact_email=data.vendor_contact_email,
            start_date=data.start_date,
            end_date=data.end_date,
            contract_value=data.contract_value,
            gst_rate=data.gst_rate,
            gst_amount=gst_amount,
            total_value=total_value,
            payment_frequency=data.payment_frequency,
            coverage_details=data.coverage_details,
            exclusions=data.exclusions,
            response_time_hours=data.response_time_hours,
            resolution_time_hours=data.resolution_time_hours,
            preventive_maintenance_frequency=data.preventive_maintenance_frequency,
            visits_per_year=data.visits_per_year,
            asset_ids=data.asset_ids,
            is_renewable=data.is_renewable,
            renewal_reminder_days=data.renewal_reminder_days,
            auto_renewal=data.auto_renewal,
            terms_conditions=data.terms_conditions,
            notes=data.notes,
            created_by=created_by,
            updated_by=created_by,
        )

        self.session.add(contract)
        await self.session.flush()
        await self.session.refresh(contract)

        return contract

    async def get_amc_contract(self, contract_id: UUID) -> Optional[AMCContract]:
        """Get AMC contract by ID."""
        result = await self.session.execute(
            select(AMCContract)
            .options(selectinload(AMCContract.vendor))
            .where(AMCContract.id == contract_id)
        )
        return result.scalar_one_or_none()

    async def list_amc_contracts(
        self,
        organization_id: UUID,
        status: Optional[AMCStatus] = None,
        vendor_id: Optional[UUID] = None,
        expiring_within_days: Optional[int] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[AMCContract], int]:
        """List AMC contracts with filters."""
        query = (
            select(AMCContract)
            .options(selectinload(AMCContract.vendor))
            .where(AMCContract.organization_id == organization_id)
        )

        if status:
            query = query.where(AMCContract.status == status)

        if vendor_id:
            query = query.where(AMCContract.vendor_id == vendor_id)

        if expiring_within_days:
            cutoff = date.today() + timedelta(days=expiring_within_days)
            query = query.where(
                AMCContract.end_date <= cutoff,
                AMCContract.status == AMCStatus.ACTIVE,
            )

        # Count
        count_query = select(func.count(AMCContract.id)).where(
            AMCContract.organization_id == organization_id
        )
        if status:
            count_query = count_query.where(AMCContract.status == status)

        total = await self.session.scalar(count_query)

        result = await self.session.execute(
            query.order_by(AMCContract.end_date).offset(skip).limit(limit)
        )
        contracts = list(result.scalars().all())

        return contracts, total or 0

    async def update_amc_contract(
        self,
        contract_id: UUID,
        data: AMCContractUpdate,
        updated_by: UUID,
        expected_version: Optional[int] = None,
    ) -> Optional[AMCContract]:
        """Update AMC contract.

        Args:
            contract_id: Contract UUID
            data: Update data
            updated_by: User performing the update
            expected_version: If provided, enables optimistic locking.
        """
        contract = await self.get_amc_contract(contract_id)
        if not contract:
            return None

        # Optimistic locking check
        if expected_version is not None and contract.version != expected_version:
            raise ConcurrentModificationError(
                f"AMC contract {contract.contract_number} was modified by another user. "
                "Please refresh and try again."
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contract, field, value)

        contract.updated_by = updated_by
        increment_version(contract)

        await self.session.flush()
        await self.session.refresh(contract)

        return contract

    async def activate_amc_contract(
        self,
        contract_id: UUID,
        activated_by: UUID,
    ) -> AMCContract:
        """Activate an AMC contract."""
        contract = await self.get_amc_contract(contract_id)
        if not contract:
            raise ValueError("Contract not found")

        if contract.status != AMCStatus.DRAFT:
            raise ValueError("Only draft contracts can be activated")

        contract.status = AMCStatus.ACTIVE
        contract.updated_by = activated_by

        # Set next payment date based on frequency
        contract.next_payment_date = contract.start_date

        await self.session.flush()
        await self.session.refresh(contract)

        return contract

    async def renew_amc_contract(
        self,
        contract_id: UUID,
        data: AMCContractRenew,
        renewed_by: UUID,
    ) -> AMCContract:
        """Renew an expiring/expired AMC contract."""
        old_contract = await self.get_amc_contract(contract_id)
        if not old_contract:
            raise ValueError("Contract not found")

        # Mark old as renewed
        old_contract.status = AMCStatus.RENEWED
        old_contract.updated_by = renewed_by

        # Calculate GST for new contract
        gst_amount = data.new_contract_value * old_contract.gst_rate / 100
        total_value = data.new_contract_value + gst_amount

        # Create new contract
        new_number = f"{old_contract.contract_number}-R{date.today().year}"
        new_contract = AMCContract(
            organization_id=old_contract.organization_id,
            contract_number=new_number,
            contract_name=old_contract.contract_name,
            amc_type=old_contract.amc_type,
            status=AMCStatus.ACTIVE,
            vendor_id=old_contract.vendor_id,
            vendor_contact_person=old_contract.vendor_contact_person,
            vendor_contact_phone=old_contract.vendor_contact_phone,
            vendor_contact_email=old_contract.vendor_contact_email,
            start_date=data.new_start_date,
            end_date=data.new_end_date,
            contract_value=data.new_contract_value,
            gst_rate=old_contract.gst_rate,
            gst_amount=gst_amount,
            total_value=total_value,
            payment_frequency=old_contract.payment_frequency,
            coverage_details=old_contract.coverage_details,
            exclusions=old_contract.exclusions,
            response_time_hours=old_contract.response_time_hours,
            resolution_time_hours=old_contract.resolution_time_hours,
            preventive_maintenance_frequency=old_contract.preventive_maintenance_frequency,
            visits_per_year=old_contract.visits_per_year,
            asset_ids=old_contract.asset_ids,
            is_renewable=old_contract.is_renewable,
            renewal_reminder_days=old_contract.renewal_reminder_days,
            auto_renewal=old_contract.auto_renewal,
            terms_conditions=data.new_terms_conditions or old_contract.terms_conditions,
            previous_contract_id=old_contract.id,
            created_by=renewed_by,
            updated_by=renewed_by,
        )

        self.session.add(new_contract)
        await self.session.flush()
        await self.session.refresh(new_contract)

        return new_contract

    # =========================================
    # Maintenance Request Operations
    # =========================================

    async def create_maintenance_request(
        self,
        data: MaintenanceRequestCreate,
        created_by: UUID,
    ) -> MaintenanceRequest:
        """Create a new maintenance request."""
        # Generate request number
        request_number = await self._generate_request_number(data.organization_id)

        request = MaintenanceRequest(
            organization_id=data.organization_id,
            request_number=request_number,
            asset_id=data.asset_id,
            amc_contract_id=data.amc_contract_id,
            maintenance_type=data.maintenance_type,
            status=MaintenanceStatus.SCHEDULED,
            priority=data.priority,
            title=data.title,
            description=data.description,
            reported_by=data.reported_by or created_by,
            reported_date=data.reported_date,
            scheduled_date=data.scheduled_date,
            scheduled_time=data.scheduled_time,
            assigned_to_vendor_id=data.assigned_to_vendor_id,
            assigned_technician=data.assigned_technician,
            created_by=created_by,
            updated_by=created_by,
        )

        # Check if covered under AMC
        if data.amc_contract_id:
            request.is_covered_under_amc = True

        self.session.add(request)
        await self.session.flush()
        await self.session.refresh(request)

        return request

    async def get_maintenance_request(self, request_id: UUID) -> Optional[MaintenanceRequest]:
        """Get maintenance request by ID."""
        result = await self.session.execute(
            select(MaintenanceRequest)
            .options(
                selectinload(MaintenanceRequest.asset),
                selectinload(MaintenanceRequest.amc_contract),
                selectinload(MaintenanceRequest.assigned_vendor),
            )
            .where(MaintenanceRequest.id == request_id)
        )
        return result.scalar_one_or_none()

    async def list_maintenance_requests(
        self,
        organization_id: UUID,
        asset_id: Optional[UUID] = None,
        status: Optional[MaintenanceStatus] = None,
        maintenance_type: Optional[MaintenanceType] = None,
        priority: Optional[MaintenancePriority] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[MaintenanceRequest], int]:
        """List maintenance requests with filters."""
        query = (
            select(MaintenanceRequest)
            .options(
                selectinload(MaintenanceRequest.asset),
                selectinload(MaintenanceRequest.assigned_vendor),
            )
            .where(MaintenanceRequest.organization_id == organization_id)
        )

        if asset_id:
            query = query.where(MaintenanceRequest.asset_id == asset_id)
        if status:
            query = query.where(MaintenanceRequest.status == status)
        if maintenance_type:
            query = query.where(MaintenanceRequest.maintenance_type == maintenance_type)
        if priority:
            query = query.where(MaintenanceRequest.priority == priority)
        if from_date:
            query = query.where(MaintenanceRequest.reported_date >= from_date)
        if to_date:
            query = query.where(MaintenanceRequest.reported_date <= to_date)

        # Count
        count_query = select(func.count(MaintenanceRequest.id)).where(
            MaintenanceRequest.organization_id == organization_id
        )
        total = await self.session.scalar(count_query)

        result = await self.session.execute(
            query.order_by(MaintenanceRequest.reported_date.desc())
            .offset(skip).limit(limit)
        )
        requests = list(result.scalars().all())

        return requests, total or 0

    async def update_maintenance_request(
        self,
        request_id: UUID,
        data: MaintenanceRequestUpdate,
        updated_by: UUID,
        expected_version: Optional[int] = None,
    ) -> Optional[MaintenanceRequest]:
        """Update maintenance request.

        Args:
            request_id: Request UUID
            data: Update data
            updated_by: User performing the update
            expected_version: If provided, enables optimistic locking.
        """
        request = await self.get_maintenance_request(request_id)
        if not request:
            return None

        # Optimistic locking check
        if expected_version is not None and request.version != expected_version:
            raise ConcurrentModificationError(
                f"Maintenance request {request.request_number} was modified by another user. "
                "Please refresh and try again."
            )

        update_data = data.model_dump(exclude_unset=True)

        # Calculate total cost if any cost field is updated
        labor = update_data.get("labor_cost", request.labor_cost)
        parts = update_data.get("parts_cost", request.parts_cost)
        other = update_data.get("other_cost", request.other_cost)

        for field, value in update_data.items():
            setattr(request, field, value)

        request.total_cost = labor + parts + other
        request.updated_by = updated_by
        increment_version(request)

        await self.session.flush()
        await self.session.refresh(request)

        return request

    async def complete_maintenance_request(
        self,
        request_id: UUID,
        data: MaintenanceRequestComplete,
        completed_by: UUID,
    ) -> MaintenanceRequest:
        """Complete a maintenance request."""
        request = await self.get_maintenance_request(request_id)
        if not request:
            raise ValueError("Request not found")

        if request.status == MaintenanceStatus.COMPLETED:
            raise ValueError("Request already completed")

        request.status = MaintenanceStatus.COMPLETED
        request.actual_completion_date = data.actual_completion_date
        request.work_performed = data.work_performed
        request.parts_replaced = data.parts_replaced
        request.findings = data.findings
        request.recommendations = data.recommendations
        request.labor_cost = data.labor_cost
        request.parts_cost = data.parts_cost
        request.other_cost = data.other_cost
        request.total_cost = data.labor_cost + data.parts_cost + data.other_cost
        request.is_covered_under_amc = data.is_covered_under_amc
        request.next_maintenance_date = data.next_maintenance_date
        request.customer_signoff_by = completed_by
        request.customer_signoff_date = data.actual_completion_date
        request.updated_by = completed_by

        # Update AMC visits count if applicable
        if request.amc_contract_id and request.is_covered_under_amc:
            amc = await self.get_amc_contract(request.amc_contract_id)
            if amc:
                amc.visits_completed += 1

        await self.session.flush()
        await self.session.refresh(request)

        return request

    async def start_maintenance_request(
        self,
        request_id: UUID,
        started_by: UUID,
    ) -> MaintenanceRequest:
        """Start a maintenance request."""
        request = await self.get_maintenance_request(request_id)
        if not request:
            raise ValueError("Request not found")

        request.status = MaintenanceStatus.IN_PROGRESS
        request.actual_start_date = date.today()
        request.updated_by = started_by

        await self.session.flush()
        await self.session.refresh(request)

        return request

    # =========================================
    # Maintenance Schedule Operations
    # =========================================

    async def create_maintenance_schedule(
        self,
        data: MaintenanceScheduleCreate,
        created_by: UUID,
    ) -> MaintenanceSchedule:
        """Create a preventive maintenance schedule."""
        schedule = MaintenanceSchedule(
            organization_id=data.organization_id,
            schedule_name=data.schedule_name,
            asset_id=data.asset_id,
            category_id=data.category_id,
            maintenance_type=data.maintenance_type,
            description=data.description,
            checklist=data.checklist,
            frequency=data.frequency,
            frequency_value=data.frequency_value,
            preferred_day_of_week=data.preferred_day_of_week,
            preferred_day_of_month=data.preferred_day_of_month,
            estimated_duration_hours=data.estimated_duration_hours,
            estimated_cost=data.estimated_cost,
            default_vendor_id=data.default_vendor_id,
            is_active=True,
            created_by=created_by,
            updated_by=created_by,
        )

        # Calculate next due date
        schedule.next_due_date = self._calculate_next_due_date(
            date.today(), data.frequency, data.frequency_value
        )

        self.session.add(schedule)
        await self.session.flush()
        await self.session.refresh(schedule)

        return schedule

    async def list_maintenance_schedules(
        self,
        organization_id: UUID,
        asset_id: Optional[UUID] = None,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[MaintenanceSchedule], int]:
        """List maintenance schedules."""
        query = (
            select(MaintenanceSchedule)
            .options(selectinload(MaintenanceSchedule.asset))
            .where(
                MaintenanceSchedule.organization_id == organization_id,
                MaintenanceSchedule.is_active == is_active,
            )
        )

        if asset_id:
            query = query.where(MaintenanceSchedule.asset_id == asset_id)

        count_query = select(func.count(MaintenanceSchedule.id)).where(
            MaintenanceSchedule.organization_id == organization_id,
            MaintenanceSchedule.is_active == is_active,
        )
        total = await self.session.scalar(count_query)

        result = await self.session.execute(
            query.order_by(MaintenanceSchedule.next_due_date).offset(skip).limit(limit)
        )
        schedules = list(result.scalars().all())

        return schedules, total or 0

    async def execute_scheduled_maintenance(
        self,
        organization_id: UUID,
        executed_by: UUID,
    ) -> List[MaintenanceRequest]:
        """Create maintenance requests for due schedules."""
        today = date.today()

        # Get due schedules
        result = await self.session.execute(
            select(MaintenanceSchedule)
            .options(selectinload(MaintenanceSchedule.asset))
            .where(
                MaintenanceSchedule.organization_id == organization_id,
                MaintenanceSchedule.is_active == True,
                MaintenanceSchedule.next_due_date <= today,
            )
        )
        schedules = list(result.scalars().all())

        created_requests = []

        for schedule in schedules:
            # Create maintenance request
            if schedule.asset_id:
                request_data = MaintenanceRequestCreate(
                    organization_id=organization_id,
                    asset_id=schedule.asset_id,
                    maintenance_type=schedule.maintenance_type,
                    priority=MaintenancePriority.MEDIUM,
                    title=f"Scheduled: {schedule.schedule_name}",
                    description=schedule.description,
                    scheduled_date=today,
                    assigned_to_vendor_id=schedule.default_vendor_id,
                )
                request = await self.create_maintenance_request(request_data, executed_by)
                created_requests.append(request)

            # Update schedule
            schedule.last_executed_date = today
            schedule.next_due_date = self._calculate_next_due_date(
                today, schedule.frequency, schedule.frequency_value
            )

        await self.session.flush()

        return created_requests

    # =========================================
    # Warranty Operations
    # =========================================

    async def create_warranty(
        self,
        data: AssetWarrantyCreate,
        created_by: UUID,
    ) -> AssetWarranty:
        """Create asset warranty record."""
        warranty = AssetWarranty(
            organization_id=data.organization_id,
            asset_id=data.asset_id,
            warranty_type=data.warranty_type,
            warranty_provider=data.warranty_provider,
            warranty_number=data.warranty_number,
            start_date=data.start_date,
            end_date=data.end_date,
            coverage_details=data.coverage_details,
            exclusions=data.exclusions,
            contact_phone=data.contact_phone,
            contact_email=data.contact_email,
            is_active=True,
            created_by=created_by,
            updated_by=created_by,
        )

        self.session.add(warranty)
        await self.session.flush()
        await self.session.refresh(warranty)

        return warranty

    async def list_warranties(
        self,
        organization_id: UUID,
        asset_id: Optional[UUID] = None,
        expiring_within_days: Optional[int] = None,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[AssetWarranty], int]:
        """List warranties."""
        query = (
            select(AssetWarranty)
            .options(selectinload(AssetWarranty.asset))
            .where(
                AssetWarranty.organization_id == organization_id,
                AssetWarranty.is_active == is_active,
            )
        )

        if asset_id:
            query = query.where(AssetWarranty.asset_id == asset_id)

        if expiring_within_days:
            cutoff = date.today() + timedelta(days=expiring_within_days)
            query = query.where(
                AssetWarranty.end_date <= cutoff,
                AssetWarranty.end_date >= date.today(),
            )

        count_query = select(func.count(AssetWarranty.id)).where(
            AssetWarranty.organization_id == organization_id,
            AssetWarranty.is_active == is_active,
        )
        total = await self.session.scalar(count_query)

        result = await self.session.execute(
            query.order_by(AssetWarranty.end_date).offset(skip).limit(limit)
        )
        warranties = list(result.scalars().all())

        return warranties, total or 0

    # =========================================
    # Analytics and Summaries
    # =========================================

    async def get_maintenance_summary(
        self,
        organization_id: UUID,
        as_on_date: Optional[date] = None,
    ) -> MaintenanceSummaryResponse:
        """Get comprehensive maintenance summary."""
        if not as_on_date:
            as_on_date = date.today()

        # Determine FY start
        if as_on_date.month >= 4:
            fy_start = date(as_on_date.year, 4, 1)
        else:
            fy_start = date(as_on_date.year - 1, 4, 1)

        # AMC counts
        amc_result = await self.session.execute(
            select(
                func.count(AMCContract.id).label("total"),
                func.count(AMCContract.id).filter(AMCContract.status == AMCStatus.ACTIVE).label("active"),
                func.count(AMCContract.id).filter(
                    and_(
                        AMCContract.status == AMCStatus.ACTIVE,
                        AMCContract.end_date <= as_on_date + timedelta(days=30),
                        AMCContract.end_date >= as_on_date,
                    )
                ).label("expiring_30"),
                func.count(AMCContract.id).filter(AMCContract.status == AMCStatus.EXPIRED).label("expired"),
                func.sum(AMCContract.total_value).filter(AMCContract.status == AMCStatus.ACTIVE).label("total_value"),
            )
            .where(AMCContract.organization_id == organization_id)
        )
        amc_stats = amc_result.one()

        # Warranty counts
        warranty_result = await self.session.execute(
            select(
                func.count(AssetWarranty.id).label("total"),
                func.count(AssetWarranty.id).filter(
                    and_(AssetWarranty.is_active == True, AssetWarranty.end_date >= as_on_date)
                ).label("active"),
                func.count(AssetWarranty.id).filter(
                    and_(
                        AssetWarranty.is_active == True,
                        AssetWarranty.end_date <= as_on_date + timedelta(days=30),
                        AssetWarranty.end_date >= as_on_date,
                    )
                ).label("expiring_30"),
            )
            .where(AssetWarranty.organization_id == organization_id)
        )
        warranty_stats = warranty_result.one()

        # Maintenance request counts
        maint_result = await self.session.execute(
            select(
                func.count(MaintenanceRequest.id).filter(
                    MaintenanceRequest.reported_date >= fy_start
                ).label("ytd_total"),
                func.count(MaintenanceRequest.id).filter(
                    MaintenanceRequest.status.in_([
                        MaintenanceStatus.SCHEDULED,
                        MaintenanceStatus.IN_PROGRESS,
                        MaintenanceStatus.ON_HOLD,
                    ])
                ).label("open"),
                func.count(MaintenanceRequest.id).filter(
                    and_(
                        MaintenanceRequest.status != MaintenanceStatus.COMPLETED,
                        MaintenanceRequest.scheduled_date < as_on_date,
                    )
                ).label("overdue"),
                func.count(MaintenanceRequest.id).filter(
                    and_(
                        MaintenanceRequest.status == MaintenanceStatus.COMPLETED,
                        MaintenanceRequest.actual_completion_date >= as_on_date.replace(day=1),
                    )
                ).label("completed_month"),
            )
            .where(MaintenanceRequest.organization_id == organization_id)
        )
        maint_stats = maint_result.one()

        # Cost analysis
        cost_result = await self.session.execute(
            select(
                func.sum(MaintenanceRequest.total_cost).filter(
                    MaintenanceRequest.reported_date >= fy_start
                ).label("total_cost"),
                func.sum(MaintenanceRequest.total_cost).filter(
                    and_(
                        MaintenanceRequest.reported_date >= fy_start,
                        MaintenanceRequest.is_covered_under_amc == True,
                    )
                ).label("amc_covered"),
            )
            .where(MaintenanceRequest.organization_id == organization_id)
        )
        cost_stats = cost_result.one()

        total_cost = cost_stats.total_cost or Decimal("0.00")
        amc_covered = cost_stats.amc_covered or Decimal("0.00")

        # By maintenance type
        type_result = await self.session.execute(
            select(
                MaintenanceRequest.maintenance_type,
                func.count(MaintenanceRequest.id).label("count"),
                func.sum(MaintenanceRequest.total_cost).label("cost"),
            )
            .where(
                MaintenanceRequest.organization_id == organization_id,
                MaintenanceRequest.reported_date >= fy_start,
            )
            .group_by(MaintenanceRequest.maintenance_type)
        )
        by_type = [
            {
                "type": row.maintenance_type.value,
                "count": row.count,
                "cost": float(row.cost or 0),
            }
            for row in type_result
        ]

        # Upcoming scheduled
        upcoming_result = await self.session.execute(
            select(func.count(MaintenanceSchedule.id))
            .where(
                MaintenanceSchedule.organization_id == organization_id,
                MaintenanceSchedule.is_active == True,
                MaintenanceSchedule.next_due_date <= as_on_date + timedelta(days=30),
            )
        )
        upcoming_count = upcoming_result.scalar_one() or 0

        return MaintenanceSummaryResponse(
            organization_id=organization_id,
            as_on_date=as_on_date,
            total_amc_contracts=amc_stats.total or 0,
            active_amc_contracts=amc_stats.active or 0,
            expiring_within_30_days=amc_stats.expiring_30 or 0,
            expired_contracts=amc_stats.expired or 0,
            total_amc_value=amc_stats.total_value or Decimal("0.00"),
            total_warranties=warranty_stats.total or 0,
            active_warranties=warranty_stats.active or 0,
            expiring_within_30_days_warranty=warranty_stats.expiring_30 or 0,
            total_requests_ytd=maint_stats.ytd_total or 0,
            open_requests=maint_stats.open or 0,
            overdue_requests=maint_stats.overdue or 0,
            completed_this_month=maint_stats.completed_month or 0,
            total_maintenance_cost_ytd=total_cost,
            cost_covered_by_amc=amc_covered,
            cost_not_covered=total_cost - amc_covered,
            by_maintenance_type=by_type,
            upcoming_scheduled_count=upcoming_count,
        )

    async def get_asset_maintenance_history(
        self,
        asset_id: UUID,
    ) -> AssetMaintenanceHistoryResponse:
        """Get complete maintenance history for an asset."""
        # Get asset
        asset_result = await self.session.execute(
            select(FixedAsset)
            .where(FixedAsset.id == asset_id)
        )
        asset = asset_result.scalar_one_or_none()
        if not asset:
            raise ValueError("Asset not found")

        # Get warranties
        warranties, _ = await self.list_warranties(
            asset.organization_id, asset_id=asset_id, is_active=True
        )

        # Check AMC coverage
        amc_result = await self.session.execute(
            select(AMCContract)
            .options(selectinload(AMCContract.vendor))
            .where(
                AMCContract.organization_id == asset.organization_id,
                AMCContract.status == AMCStatus.ACTIVE,
                AMCContract.asset_ids.contains([str(asset_id)]),
            )
        )
        amc = amc_result.scalar_one_or_none()

        # Maintenance history
        history_result = await self.session.execute(
            select(MaintenanceRequest)
            .where(MaintenanceRequest.asset_id == asset_id)
            .order_by(MaintenanceRequest.reported_date.desc())
            .limit(20)
        )
        recent_maintenance = list(history_result.scalars().all())

        # Totals
        totals_result = await self.session.execute(
            select(
                func.count(MaintenanceRequest.id).label("count"),
                func.sum(MaintenanceRequest.total_cost).label("cost"),
                func.sum(MaintenanceRequest.downtime_hours).label("downtime"),
            )
            .where(MaintenanceRequest.asset_id == asset_id)
        )
        totals = totals_result.one()

        # Schedules
        schedules, _ = await self.list_maintenance_schedules(
            asset.organization_id, asset_id=asset_id
        )

        # Next scheduled
        next_scheduled = None
        if schedules:
            next_scheduled = min(s.next_due_date for s in schedules if s.next_due_date)

        return AssetMaintenanceHistoryResponse(
            asset_id=asset_id,
            asset_code=asset.asset_code,
            asset_name=asset.asset_name,
            active_warranties=[],  # Would need to convert to response
            covered_under_amc=amc is not None,
            amc_contract=None,  # Would need to convert to response
            total_maintenance_count=totals.count or 0,
            total_maintenance_cost=totals.cost or Decimal("0.00"),
            total_downtime_hours=totals.downtime or Decimal("0.00"),
            recent_maintenance=[],  # Would need to convert to response
            next_scheduled_maintenance=next_scheduled,
            maintenance_schedules=[],  # Would need to convert to response
        )

    async def get_expiring_amc_alerts(
        self,
        organization_id: UUID,
        days: int = 30,
    ) -> List[AMCContract]:
        """Get AMC contracts expiring within specified days."""
        contracts, _ = await self.list_amc_contracts(
            organization_id,
            expiring_within_days=days,
        )
        return contracts

    async def get_expiring_warranty_alerts(
        self,
        organization_id: UUID,
        days: int = 30,
    ) -> List[AssetWarranty]:
        """Get warranties expiring within specified days."""
        warranties, _ = await self.list_warranties(
            organization_id,
            expiring_within_days=days,
        )
        return warranties

    # =========================================
    # Helper Methods
    # =========================================

    async def _generate_request_number(self, organization_id: UUID) -> str:
        """Generate next maintenance request number."""
        result = await self.session.execute(
            select(func.count(MaintenanceRequest.id))
            .where(MaintenanceRequest.organization_id == organization_id)
        )
        count = result.scalar_one() or 0
        return f"MR-{date.today().year}-{count + 1:05d}"

    def _calculate_next_due_date(
        self,
        from_date: date,
        frequency: str,
        frequency_value: int,
    ) -> date:
        """Calculate next due date based on frequency."""
        if frequency == "DAILY":
            return from_date + timedelta(days=frequency_value)
        elif frequency == "WEEKLY":
            return from_date + timedelta(weeks=frequency_value)
        elif frequency == "MONTHLY":
            month = from_date.month + frequency_value
            year = from_date.year
            while month > 12:
                month -= 12
                year += 1
            return from_date.replace(year=year, month=month)
        elif frequency == "QUARTERLY":
            month = from_date.month + (3 * frequency_value)
            year = from_date.year
            while month > 12:
                month -= 12
                year += 1
            return from_date.replace(year=year, month=month)
        elif frequency == "HALF_YEARLY":
            month = from_date.month + (6 * frequency_value)
            year = from_date.year
            while month > 12:
                month -= 12
                year += 1
            return from_date.replace(year=year, month=month)
        elif frequency == "YEARLY":
            return from_date.replace(year=from_date.year + frequency_value)
        else:
            return from_date + timedelta(days=30)
