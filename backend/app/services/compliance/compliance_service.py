"""
Compliance Service

Business logic for compliance management.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.compliance.compliance import (
    ComplianceItem,
    ComplianceInstance,
    ComplianceDocument,
    ComplianceStatus,
)
from app.schemas.compliance.compliance import (
    ComplianceItemCreate,
    ComplianceItemUpdate,
    ComplianceInstanceCreate,
    ComplianceInstanceUpdate,
    ComplianceDocumentCreate,
    ComplianceSummary,
    ComplianceCalendarItem,
    UpcomingCompliance,
)


class ComplianceItemService:
    """Service for compliance item (master) operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ComplianceItemCreate, created_by: UUID) -> ComplianceItem:
        """Create a new compliance item"""
        item = ComplianceItem(
            **data.model_dump(),
            created_by=created_by
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def get(self, id: UUID) -> Optional[ComplianceItem]:
        """Get compliance item by ID"""
        result = await self.db.execute(
            select(ComplianceItem).where(ComplianceItem.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, organization_id: UUID, code: str) -> Optional[ComplianceItem]:
        """Get compliance item by organization and code"""
        result = await self.db.execute(
            select(ComplianceItem).where(
                and_(
                    ComplianceItem.organization_id == organization_id,
                    ComplianceItem.item_code == code
                )
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        organization_id: UUID,
        regulatory_body: Optional[str] = None,
        frequency: Optional[str] = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[ComplianceItem], int]:
        """List compliance items with filters"""
        query = select(ComplianceItem).where(
            ComplianceItem.organization_id == organization_id
        )

        if regulatory_body:
            query = query.where(ComplianceItem.regulatory_body == regulatory_body)
        if frequency:
            query = query.where(ComplianceItem.frequency == frequency)
        if active_only:
            query = query.where(ComplianceItem.is_active == True)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total_count = total.scalar() or 0

        # Results
        query = query.order_by(ComplianceItem.regulatory_body, ComplianceItem.item_name)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return items, total_count

    async def update(
        self,
        id: UUID,
        data: ComplianceItemUpdate,
        updated_by: UUID
    ) -> Optional[ComplianceItem]:
        """Update a compliance item"""
        item = await self.get(id)
        if not item:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)
        item.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def delete(self, id: UUID) -> bool:
        """Soft delete a compliance item"""
        item = await self.get(id)
        if not item:
            return False

        item.is_active = False
        await self.db.commit()
        return True


class ComplianceInstanceService:
    """Service for compliance instance operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ComplianceInstanceCreate, created_by: UUID) -> ComplianceInstance:
        """Create a new compliance instance"""
        instance_data = data.model_dump()
        # Set actual_due_date
        instance_data['actual_due_date'] = (
            data.extended_due_date if data.extended_due_date else data.original_due_date
        )

        instance = ComplianceInstance(
            **instance_data,
            created_by=created_by
        )
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return await self.get(instance.id)

    async def get(self, id: UUID) -> Optional[ComplianceInstance]:
        """Get compliance instance by ID with related item"""
        result = await self.db.execute(
            select(ComplianceInstance)
            .options(selectinload(ComplianceInstance.compliance_item))
            .where(ComplianceInstance.id == id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        organization_id: Optional[UUID] = None,
        compliance_item_id: Optional[UUID] = None,
        regulatory_body: Optional[str] = None,
        status: Optional[str] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[ComplianceInstance], int]:
        """List compliance instances with filters"""
        query = select(ComplianceInstance).options(
            selectinload(ComplianceInstance.compliance_item)
        )

        # Join with compliance_item for organization and body filtering
        if organization_id or regulatory_body:
            query = query.join(ComplianceItem)

        if organization_id:
            query = query.where(ComplianceItem.organization_id == organization_id)
        if compliance_item_id:
            query = query.where(ComplianceInstance.compliance_item_id == compliance_item_id)
        if regulatory_body:
            query = query.where(ComplianceItem.regulatory_body == regulatory_body)
        if status:
            query = query.where(ComplianceInstance.status == status)
        if year:
            query = query.where(ComplianceInstance.period_year == year)
        if month:
            query = query.where(ComplianceInstance.period_month == month)
        if from_date:
            query = query.where(ComplianceInstance.actual_due_date >= from_date)
        if to_date:
            query = query.where(ComplianceInstance.actual_due_date <= to_date)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total_count = total.scalar() or 0

        # Results
        query = query.order_by(ComplianceInstance.actual_due_date)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return items, total_count

    async def update(
        self,
        id: UUID,
        data: ComplianceInstanceUpdate,
        updated_by: UUID
    ) -> Optional[ComplianceInstance]:
        """Update a compliance instance"""
        instance = await self.get(id)
        if not instance:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Handle status transitions
        if 'status' in update_data:
            new_status = update_data['status']
            now = datetime.utcnow()

            if new_status == ComplianceStatus.PREPARED.value:
                update_data['prepared_by'] = updated_by
                update_data['prepared_at'] = now
            elif new_status == ComplianceStatus.UNDER_REVIEW.value:
                pass
            elif new_status == ComplianceStatus.FILED.value:
                update_data['filed_by'] = updated_by
                if not update_data.get('filed_date'):
                    update_data['filed_date'] = date.today()
                # Check if delayed
                if update_data['filed_date'] > instance.actual_due_date:
                    update_data['is_delayed'] = True
                    update_data['delay_days'] = (update_data['filed_date'] - instance.actual_due_date).days

        # Update extended due date if provided
        if 'extended_due_date' in update_data:
            update_data['actual_due_date'] = update_data['extended_due_date']

        for field, value in update_data.items():
            setattr(instance, field, value)
        instance.updated_by = updated_by

        await self.db.commit()
        return await self.get(id)

    async def get_summary(self, organization_id: UUID, year: Optional[int] = None) -> ComplianceSummary:
        """Get compliance summary for dashboard"""
        query = (
            select(ComplianceInstance.status, func.count(ComplianceInstance.id))
            .join(ComplianceItem)
            .where(ComplianceItem.organization_id == organization_id)
        )

        if year:
            query = query.where(ComplianceInstance.period_year == year)

        query = query.group_by(ComplianceInstance.status)
        result = await self.db.execute(query)
        status_counts = dict(result.all())

        # Count delayed
        delayed_query = (
            select(func.count(ComplianceInstance.id))
            .join(ComplianceItem)
            .where(
                and_(
                    ComplianceItem.organization_id == organization_id,
                    ComplianceInstance.is_delayed == True
                )
            )
        )
        if year:
            delayed_query = delayed_query.where(ComplianceInstance.period_year == year)
        delayed_result = await self.db.execute(delayed_query)
        delayed_count = delayed_result.scalar() or 0

        return ComplianceSummary(
            total=sum(status_counts.values()),
            pending=status_counts.get(ComplianceStatus.PENDING, 0),
            in_progress=status_counts.get(ComplianceStatus.IN_PROGRESS, 0),
            prepared=status_counts.get(ComplianceStatus.PREPARED, 0),
            filed=status_counts.get(ComplianceStatus.FILED, 0) + status_counts.get(ComplianceStatus.ACKNOWLEDGED, 0),
            delayed=delayed_count,
            not_applicable=status_counts.get(ComplianceStatus.NOT_APPLICABLE, 0)
        )

    async def get_upcoming(self, organization_id: UUID) -> UpcomingCompliance:
        """Get upcoming compliance items"""
        today = date.today()
        week_end = today + timedelta(days=7)
        month_end = today + timedelta(days=30)

        # Base query
        base_query = (
            select(ComplianceInstance)
            .options(selectinload(ComplianceInstance.compliance_item))
            .join(ComplianceItem)
            .where(ComplianceItem.organization_id == organization_id)
        )

        # Overdue
        overdue_query = base_query.where(
            and_(
                ComplianceInstance.actual_due_date < today,
                ComplianceInstance.status.in_([
                    ComplianceStatus.PENDING,
                    ComplianceStatus.IN_PROGRESS,
                    ComplianceStatus.PREPARED
                ])
            )
        ).order_by(ComplianceInstance.actual_due_date)
        overdue_result = await self.db.execute(overdue_query)
        overdue = [self._to_calendar_item(i) for i in overdue_result.scalars().all()]

        # Due this week
        week_query = base_query.where(
            and_(
                ComplianceInstance.actual_due_date >= today,
                ComplianceInstance.actual_due_date <= week_end,
                ComplianceInstance.status.in_([
                    ComplianceStatus.PENDING,
                    ComplianceStatus.IN_PROGRESS,
                    ComplianceStatus.PREPARED
                ])
            )
        ).order_by(ComplianceInstance.actual_due_date)
        week_result = await self.db.execute(week_query)
        due_this_week = [self._to_calendar_item(i) for i in week_result.scalars().all()]

        # Due this month (excluding this week)
        month_query = base_query.where(
            and_(
                ComplianceInstance.actual_due_date > week_end,
                ComplianceInstance.actual_due_date <= month_end,
                ComplianceInstance.status.in_([
                    ComplianceStatus.PENDING,
                    ComplianceStatus.IN_PROGRESS,
                    ComplianceStatus.PREPARED
                ])
            )
        ).order_by(ComplianceInstance.actual_due_date)
        month_result = await self.db.execute(month_query)
        due_this_month = [self._to_calendar_item(i) for i in month_result.scalars().all()]

        return UpcomingCompliance(
            overdue=overdue,
            due_this_week=due_this_week,
            due_this_month=due_this_month
        )

    def _to_calendar_item(self, instance: ComplianceInstance) -> ComplianceCalendarItem:
        """Convert instance to calendar item"""
        return ComplianceCalendarItem(
            id=instance.id,
            item_code=instance.compliance_item.item_code,
            item_name=instance.compliance_item.item_name,
            regulatory_body=instance.compliance_item.regulatory_body,
            due_date=instance.actual_due_date,
            status=instance.status,
            is_delayed=instance.is_delayed
        )

    async def generate_instances_for_period(
        self,
        organization_id: UUID,
        year: int,
        month: Optional[int] = None,
        created_by: UUID = None
    ) -> List[ComplianceInstance]:
        """Generate compliance instances for a period based on active items"""
        # Get all active compliance items
        items_result = await self.db.execute(
            select(ComplianceItem).where(
                and_(
                    ComplianceItem.organization_id == organization_id,
                    ComplianceItem.is_active == True
                )
            )
        )
        items = items_result.scalars().all()

        created_instances = []
        for item in items:
            # Calculate due date based on frequency and due_day
            due_date = self._calculate_due_date(item, year, month)
            if not due_date:
                continue

            # Check if instance already exists
            existing = await self.db.execute(
                select(ComplianceInstance).where(
                    and_(
                        ComplianceInstance.compliance_item_id == item.id,
                        ComplianceInstance.period_year == year,
                        ComplianceInstance.period_month == month
                    )
                )
            )
            if existing.scalar_one_or_none():
                continue

            # Create instance
            instance = ComplianceInstance(
                compliance_item_id=item.id,
                period_year=year,
                period_month=month,
                original_due_date=due_date,
                actual_due_date=due_date,
                status=ComplianceStatus.PENDING,
                created_by=created_by
            )
            self.db.add(instance)
            created_instances.append(instance)

        if created_instances:
            await self.db.commit()
            for inst in created_instances:
                await self.db.refresh(inst)

        return created_instances

    def _calculate_due_date(
        self,
        item: ComplianceItem,
        year: int,
        month: Optional[int]
    ) -> Optional[date]:
        """Calculate due date for a compliance item"""
        if item.frequency == "MONTHLY" and month:
            due_day = item.due_day or 15
            # Handle next month due dates
            if due_day > 28:
                due_day = min(due_day, 28)
            return date(year, month, due_day) + timedelta(days=item.grace_days)

        if item.frequency == "QUARTERLY" and month:
            # Quarterly filings are typically due after quarter end
            quarter = (month - 1) // 3 + 1
            # Due month is typically the month after quarter end
            quarter_end_month = quarter * 3
            due_month = quarter_end_month + 1 if quarter_end_month < 12 else 1
            due_year = year if due_month > 1 else year + 1
            due_day = item.due_day or 15
            return date(due_year, due_month, due_day) + timedelta(days=item.grace_days)

        if item.frequency == "ANNUALLY":
            due_month = item.due_month or 3
            due_day = item.due_day or 31
            return date(year, due_month, due_day) + timedelta(days=item.grace_days)

        return None


class ComplianceDocumentService:
    """Service for compliance document operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ComplianceDocumentCreate, uploaded_by: UUID) -> ComplianceDocument:
        """Create a new compliance document"""
        doc = ComplianceDocument(
            **data.model_dump(),
            uploaded_at=datetime.utcnow(),
            uploaded_by=uploaded_by
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def list_by_instance(self, instance_id: UUID) -> List[ComplianceDocument]:
        """List documents for an instance"""
        result = await self.db.execute(
            select(ComplianceDocument)
            .where(
                and_(
                    ComplianceDocument.instance_id == instance_id,
                    ComplianceDocument.is_active == True
                )
            )
            .order_by(ComplianceDocument.uploaded_at.desc())
        )
        return result.scalars().all()

    async def delete(self, id: UUID) -> bool:
        """Soft delete a document"""
        result = await self.db.execute(
            select(ComplianceDocument).where(ComplianceDocument.id == id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            return False

        doc.is_active = False
        await self.db.commit()
        return True
