"""Audit Log repository for MCA-compliant audit trail.

This repository only supports CREATE and READ operations.
UPDATE and DELETE are not allowed per MCA compliance requirements.
"""

from datetime import date, datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.common.audit_log import AuditLog
from app.models.common.line_item_history import LineItemHistory
from app.models.auth.user import User


class AuditLogRepository:
    """Repository for audit log operations.

    IMPORTANT: This repository intentionally does NOT support
    update or delete operations to maintain MCA compliance.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: Dict[str, Any]) -> AuditLog:
        """Create a new audit log entry."""
        audit_log = AuditLog(**data)
        self.session.add(audit_log)
        await self.session.flush()
        await self.session.refresh(audit_log)
        return audit_log

    async def create_line_item_history(self, data: Dict[str, Any]) -> LineItemHistory:
        """Create a new line item history entry."""
        history = LineItemHistory(**data)
        self.session.add(history)
        await self.session.flush()
        await self.session.refresh(history)
        return history

    async def create_bulk_line_item_history(
        self,
        entries: List[Dict[str, Any]]
    ) -> List[LineItemHistory]:
        """Create multiple line item history entries."""
        history_items = [LineItemHistory(**data) for data in entries]
        self.session.add_all(history_items)
        await self.session.flush()
        for item in history_items:
            await self.session.refresh(item)
        return history_items

    async def get(self, id: UUID) -> Optional[AuditLog]:
        """Get an audit log entry by ID."""
        query = (
            select(AuditLog)
            .options(selectinload(AuditLog.line_item_changes))
            .where(AuditLog.id == id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[AuditLog], int]:
        """Get all audit logs for a specific entity."""
        base_query = select(AuditLog).where(
            and_(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
            )
        )

        # Count query
        count_query = select(func.count(AuditLog.id)).where(
            and_(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
            )
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Data query with line item changes
        query = (
            base_query
            .options(selectinload(AuditLog.line_item_changes))
            .order_by(AuditLog.changed_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        changed_by: Optional[UUID] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[AuditLog], int]:
        """Get audit logs for an organization with filters."""
        conditions = [AuditLog.organization_id == organization_id]

        if entity_type:
            conditions.append(AuditLog.entity_type == entity_type)
        if action:
            conditions.append(AuditLog.action == action)
        if changed_by:
            conditions.append(AuditLog.changed_by == changed_by)
        if date_from:
            conditions.append(
                AuditLog.changed_at >= datetime.combine(
                    date_from, datetime.min.time()
                ).replace(tzinfo=timezone.utc)
            )
        if date_to:
            conditions.append(
                AuditLog.changed_at <= datetime.combine(
                    date_to, datetime.max.time()
                ).replace(tzinfo=timezone.utc)
            )
        if search:
            conditions.append(
                or_(
                    AuditLog.entity_reference.ilike(f"%{search}%"),
                    AuditLog.change_reason.ilike(f"%{search}%"),
                )
            )

        base_query = select(AuditLog).where(and_(*conditions))

        # Count query
        count_query = select(func.count(AuditLog.id)).where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Data query
        query = (
            base_query
            .options(selectinload(AuditLog.line_item_changes))
            .order_by(AuditLog.changed_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_entity_history_summary(
        self,
        entity_type: str,
        entity_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """Get summary of changes for an entity."""
        # Get first and last change
        first_query = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.entity_type == entity_type,
                    AuditLog.entity_id == entity_id,
                )
            )
            .order_by(AuditLog.changed_at.asc())
            .limit(1)
        )
        first_result = await self.session.execute(first_query)
        first = first_result.scalar_one_or_none()

        if not first:
            return None

        last_query = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.entity_type == entity_type,
                    AuditLog.entity_id == entity_id,
                )
            )
            .order_by(AuditLog.changed_at.desc())
            .limit(1)
        )
        last_result = await self.session.execute(last_query)
        last = last_result.scalar_one_or_none()

        # Get total count
        count_query = select(func.count(AuditLog.id)).where(
            and_(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
            )
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "entity_reference": first.entity_reference,
            "total_changes": total,
            "first_created": first.changed_at,
            "last_modified": last.changed_at if last else first.changed_at,
        }

    async def get_line_item_history(
        self,
        parent_audit_id: UUID,
    ) -> List[LineItemHistory]:
        """Get all line item changes for a parent audit entry."""
        query = (
            select(LineItemHistory)
            .where(LineItemHistory.parent_audit_id == parent_audit_id)
            .order_by(LineItemHistory.line_number)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_user_activity(
        self,
        user_id: UUID,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Tuple[List[AuditLog], int]:
        """Get audit logs for a specific user."""
        conditions = [
            AuditLog.changed_by == user_id,
            AuditLog.organization_id == organization_id,
        ]

        if date_from:
            conditions.append(
                AuditLog.changed_at >= datetime.combine(
                    date_from, datetime.min.time()
                ).replace(tzinfo=timezone.utc)
            )
        if date_to:
            conditions.append(
                AuditLog.changed_at <= datetime.combine(
                    date_to, datetime.max.time()
                ).replace(tzinfo=timezone.utc)
            )

        base_query = select(AuditLog).where(and_(*conditions))

        # Count query
        count_query = select(func.count(AuditLog.id)).where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Data query
        query = (
            base_query
            .options(selectinload(AuditLog.line_item_changes))
            .order_by(AuditLog.changed_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_recent_changes(
        self,
        organization_id: UUID,
        limit: int = 50,
    ) -> List[AuditLog]:
        """Get most recent changes across all entities."""
        query = (
            select(AuditLog)
            .where(AuditLog.organization_id == organization_id)
            .options(selectinload(AuditLog.line_item_changes))
            .order_by(AuditLog.changed_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
