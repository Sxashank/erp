"""Audit Service for MCA-compliant transaction logging.

This service provides methods to log changes to transactions and entities
in compliance with MCA April 2023 notification requirements.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.common.audit_log import AuditLog, AuditAction, EntityType
from app.models.common.line_item_history import LineItemHistory, LineItemAction
from app.repositories.common.audit_log_repo import AuditLogRepository
from app.schemas.common.audit_log import (
    AuditLogResponse,
    AuditLogListResponse,
    EntityHistoryResponse,
    LineItemHistoryResponse,
)
from app.schemas.base import PaginatedResponse


class AuditService:
    """Service for MCA-compliant audit trail management.

    This service handles:
    - Logging create/update/delete actions on transactions
    - Calculating field-level changes (old vs new values)
    - Tracking line item changes separately
    - Querying audit history
    """

    # Fields to exclude from audit comparison (internal/computed fields)
    EXCLUDED_FIELDS = {
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "deleted_at",
        "deleted_by",
        "is_active",
        "_sa_instance_state",
    }

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AuditLogRepository(session)

    async def log_create(
        self,
        organization_id: UUID,
        entity_type: str,
        entity_id: UUID,
        entity_reference: Optional[str],
        new_values: Dict[str, Any],
        user_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        change_reason: Optional[str] = None,
    ) -> AuditLog:
        """Log creation of a new entity."""
        # Clean new values for storage
        clean_values = self._clean_values(new_values)

        audit_data = {
            "organization_id": organization_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "entity_reference": entity_reference,
            "action": AuditAction.CREATE.value,
            "changed_by": user_id,
            "changed_at": datetime.now(timezone.utc),
            "old_values": None,
            "new_values": clean_values,
            "changed_fields": list(clean_values.keys()),
            "change_reason": change_reason,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

        return await self.repo.create(audit_data)

    async def log_update(
        self,
        organization_id: UUID,
        entity_type: str,
        entity_id: UUID,
        entity_reference: Optional[str],
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        user_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        change_reason: Optional[str] = None,
    ) -> AuditLog:
        """Log update to an existing entity."""
        # Calculate changed fields
        clean_old = self._clean_values(old_values)
        clean_new = self._clean_values(new_values)
        changed_fields = self._get_changed_fields(clean_old, clean_new)

        # Only store values that actually changed
        old_changed = {k: clean_old.get(k) for k in changed_fields}
        new_changed = {k: clean_new.get(k) for k in changed_fields}

        audit_data = {
            "organization_id": organization_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "entity_reference": entity_reference,
            "action": AuditAction.UPDATE.value,
            "changed_by": user_id,
            "changed_at": datetime.now(timezone.utc),
            "old_values": old_changed,
            "new_values": new_changed,
            "changed_fields": changed_fields,
            "change_reason": change_reason,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

        return await self.repo.create(audit_data)

    async def log_delete(
        self,
        organization_id: UUID,
        entity_type: str,
        entity_id: UUID,
        entity_reference: Optional[str],
        old_values: Dict[str, Any],
        user_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        change_reason: Optional[str] = None,
    ) -> AuditLog:
        """Log deletion of an entity."""
        clean_old = self._clean_values(old_values)

        audit_data = {
            "organization_id": organization_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "entity_reference": entity_reference,
            "action": AuditAction.DELETE.value,
            "changed_by": user_id,
            "changed_at": datetime.now(timezone.utc),
            "old_values": clean_old,
            "new_values": None,
            "changed_fields": list(clean_old.keys()),
            "change_reason": change_reason,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

        return await self.repo.create(audit_data)

    async def log_action(
        self,
        organization_id: UUID,
        entity_type: str,
        entity_id: UUID,
        entity_reference: Optional[str],
        action: str,
        user_id: UUID,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        change_reason: Optional[str] = None,
        audit_context: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Log a custom action (APPROVE, CANCEL, POST, REVERSE, VOID).

        Args:
            audit_context: Additional context like financial impact, GL entries, approval chain
        """
        clean_old = self._clean_values(old_values) if old_values else None
        clean_new = self._clean_values(new_values) if new_values else None
        changed_fields = []

        if clean_old and clean_new:
            changed_fields = self._get_changed_fields(clean_old, clean_new)

        audit_data = {
            "organization_id": organization_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "entity_reference": entity_reference,
            "action": action,
            "changed_by": user_id,
            "changed_at": datetime.now(timezone.utc),
            "old_values": clean_old,
            "new_values": clean_new,
            "changed_fields": changed_fields if changed_fields else None,
            "change_reason": change_reason,
            "audit_context": audit_context,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

        return await self.repo.create(audit_data)

    async def log_approval_action(
        self,
        organization_id: UUID,
        entity_type: str,
        entity_id: UUID,
        entity_reference: Optional[str],
        action: str,
        user_id: UUID,
        request_id: UUID,
        approval_level: int,
        comments: Optional[str] = None,
        approval_chain: Optional[List[Dict[str, Any]]] = None,
    ) -> AuditLog:
        """Log an approval workflow action.

        Args:
            request_id: The approval request ID
            approval_level: The approval level being acted upon
            comments: Approver comments
            approval_chain: Full approval chain details
        """
        audit_context = {
            "transaction_type": "APPROVAL_ACTION",
            "request_id": str(request_id),
            "approval_level": approval_level,
            "approval_chain": approval_chain,
        }

        return await self.log_action(
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_reference=entity_reference,
            action=action,
            user_id=user_id,
            change_reason=comments,
            audit_context=audit_context,
        )

    async def log_gl_posting(
        self,
        organization_id: UUID,
        entity_type: str,
        entity_id: UUID,
        entity_reference: Optional[str],
        success: bool,
        user_id: UUID,
        voucher_id: Optional[UUID] = None,
        gl_entries: Optional[List[Dict[str, Any]]] = None,
        error_message: Optional[str] = None,
    ) -> AuditLog:
        """Log GL posting attempt (success or failure).

        Args:
            success: Whether GL posting succeeded
            voucher_id: The created voucher ID (if successful)
            gl_entries: Details of GL entries created
            error_message: Error details (if failed)
        """
        action = AuditAction.GL_POST_SUCCESS.value if success else AuditAction.GL_POST_FAILED.value

        audit_context = {
            "transaction_type": "GL_POSTING",
            "success": success,
            "voucher_id": str(voucher_id) if voucher_id else None,
            "gl_entries": gl_entries,
            "error_message": error_message,
        }

        return await self.log_action(
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_reference=entity_reference,
            action=action,
            user_id=user_id,
            change_reason=error_message if not success else "GL entries posted successfully",
            audit_context=audit_context,
        )

    async def log_financial_transaction(
        self,
        organization_id: UUID,
        entity_type: str,
        entity_id: UUID,
        entity_reference: Optional[str],
        action: str,
        user_id: UUID,
        financial_impact: Dict[str, Any],
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        change_reason: Optional[str] = None,
    ) -> AuditLog:
        """Log a transaction with financial impact details.

        Args:
            financial_impact: Dict with keys like:
                - asset_value: Original asset value
                - accumulated_depreciation: Accumulated depreciation
                - disposal_proceeds: Proceeds from disposal
                - gain_loss: Gain or loss amount
                - gl_entries_created: List of GL voucher IDs
        """
        audit_context = {
            "transaction_type": action,
            "financial_impact": financial_impact,
        }

        return await self.log_action(
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_reference=entity_reference,
            action=action,
            user_id=user_id,
            old_values=old_values,
            new_values=new_values,
            change_reason=change_reason,
            audit_context=audit_context,
        )

    async def log_bulk_operation(
        self,
        organization_id: UUID,
        action: str,
        user_id: UUID,
        total_records: int,
        successful: int,
        failed: int,
        affected_entity_ids: List[UUID],
        errors: Optional[List[Dict[str, Any]]] = None,
    ) -> AuditLog:
        """Log a bulk operation.

        Args:
            total_records: Total records in the bulk operation
            successful: Number of successful operations
            failed: Number of failed operations
            affected_entity_ids: List of affected entity IDs
            errors: Error details for failed records
        """
        from uuid import uuid4

        audit_context = {
            "transaction_type": "BULK_OPERATION",
            "total_records": total_records,
            "successful": successful,
            "failed": failed,
            "affected_entity_ids": [str(eid) for eid in affected_entity_ids],
            "errors": errors,
        }

        # Use a generated ID since bulk operations don't have a single entity
        bulk_operation_id = uuid4()

        return await self.log_action(
            organization_id=organization_id,
            entity_type="BULK_OPERATION",
            entity_id=bulk_operation_id,
            entity_reference=f"BULK-{action}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            action=action,
            user_id=user_id,
            change_reason=f"Bulk operation: {successful}/{total_records} successful, {failed} failed",
            audit_context=audit_context,
        )

    async def log_config_change(
        self,
        organization_id: UUID,
        entity_type: str,
        entity_id: UUID,
        entity_reference: Optional[str],
        user_id: UUID,
        old_config: Optional[Dict[str, Any]],
        new_config: Dict[str, Any],
        change_reason: Optional[str] = None,
    ) -> AuditLog:
        """Log a configuration change.

        Configuration changes are always logged with full old/new values
        for compliance and troubleshooting purposes.
        """
        audit_context = {
            "transaction_type": "CONFIGURATION_CHANGE",
            "config_entity": entity_type,
        }

        return await self.log_action(
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_reference=entity_reference,
            action=AuditAction.CONFIG_UPDATE.value,
            user_id=user_id,
            old_values=old_config,
            new_values=new_config,
            change_reason=change_reason or "Configuration updated",
            audit_context=audit_context,
        )

    async def log_line_changes(
        self,
        parent_audit_id: UUID,
        entity_type: str,
        old_lines: List[Dict[str, Any]],
        new_lines: List[Dict[str, Any]],
    ) -> List[LineItemHistory]:
        """Log changes to line items.

        Compares old and new line lists to detect:
        - Deleted lines (in old but not in new)
        - Added lines (in new but not in old)
        - Updated lines (in both with different values)
        """
        entries = []

        # Index lines by ID for comparison
        old_by_id = {
            line.get("id"): line
            for line in old_lines
            if line.get("id")
        }
        new_by_id = {
            line.get("id"): line
            for line in new_lines
            if line.get("id")
        }

        # Detect deleted lines
        for line_id, old_line in old_by_id.items():
            if line_id not in new_by_id:
                entries.append({
                    "parent_audit_id": parent_audit_id,
                    "entity_type": entity_type,
                    "line_id": line_id,
                    "line_number": old_line.get("line_number", 0),
                    "action": LineItemAction.DELETE.value,
                    "old_values": self._clean_values(old_line),
                    "new_values": None,
                })

        # Process new lines
        for idx, new_line in enumerate(new_lines):
            line_id = new_line.get("id")
            line_number = new_line.get("line_number", idx + 1)

            if line_id and line_id in old_by_id:
                # Update - check if values changed
                old_line = old_by_id[line_id]
                clean_old = self._clean_values(old_line)
                clean_new = self._clean_values(new_line)
                changed = self._get_changed_fields(clean_old, clean_new)

                if changed:
                    entries.append({
                        "parent_audit_id": parent_audit_id,
                        "entity_type": entity_type,
                        "line_id": line_id,
                        "line_number": line_number,
                        "action": LineItemAction.UPDATE.value,
                        "old_values": {k: clean_old.get(k) for k in changed},
                        "new_values": {k: clean_new.get(k) for k in changed},
                    })
            else:
                # New line
                entries.append({
                    "parent_audit_id": parent_audit_id,
                    "entity_type": entity_type,
                    "line_id": line_id or new_line.get("id"),
                    "line_number": line_number,
                    "action": LineItemAction.CREATE.value,
                    "old_values": None,
                    "new_values": self._clean_values(new_line),
                })

        if entries:
            return await self.repo.create_bulk_line_item_history(entries)
        return []

    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> EntityHistoryResponse:
        """Get complete audit history for an entity."""
        skip = (page - 1) * page_size
        logs, total = await self.repo.get_by_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            skip=skip,
            limit=page_size,
        )

        summary = await self.repo.get_entity_history_summary(
            entity_type=entity_type,
            entity_id=entity_id,
        )

        history = [self._to_response(log) for log in logs]

        return EntityHistoryResponse(
            entity_type=entity_type,
            entity_id=entity_id,
            entity_reference=summary.get("entity_reference") if summary else None,
            total_changes=summary.get("total_changes", 0) if summary else 0,
            first_created=summary.get("first_created") if summary else datetime.now(timezone.utc),
            last_modified=summary.get("last_modified") if summary else datetime.now(timezone.utc),
            history=history,
        )

    async def get_audit_logs(
        self,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        changed_by: Optional[UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search: Optional[str] = None,
    ) -> AuditLogListResponse:
        """Get paginated audit logs with filters."""
        skip = (page - 1) * page_size
        logs, total = await self.repo.get_by_organization(
            organization_id=organization_id,
            skip=skip,
            limit=page_size,
            entity_type=entity_type,
            action=action,
            changed_by=changed_by,
            date_from=date_from.date() if date_from else None,
            date_to=date_to.date() if date_to else None,
            search=search,
        )

        items = [self._to_response(log) for log in logs]
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return AuditLogListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_recent_changes(
        self,
        organization_id: UUID,
        limit: int = 50,
    ) -> List[AuditLogResponse]:
        """Get most recent changes for dashboard/activity feed."""
        logs = await self.repo.get_recent_changes(
            organization_id=organization_id,
            limit=limit,
        )
        return [self._to_response(log) for log in logs]

    def _clean_values(self, values: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Clean values for storage by removing excluded fields and serializing."""
        if not values:
            return {}

        result = {}
        for key, value in values.items():
            if key in self.EXCLUDED_FIELDS:
                continue
            if key.startswith("_"):
                continue

            # Serialize special types
            if isinstance(value, UUID):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, date):
                result[key] = value.isoformat()
            elif isinstance(value, Decimal):
                result[key] = str(value)
            elif hasattr(value, "__dict__") and not isinstance(value, dict):
                # Skip SQLAlchemy relationship objects
                continue
            elif isinstance(value, list):
                # Skip lists (usually relationships)
                continue
            else:
                result[key] = value

        return result

    def _get_changed_fields(
        self,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
    ) -> List[str]:
        """Identify fields that changed between old and new values."""
        changed = []
        all_keys = set(old_values.keys()) | set(new_values.keys())

        for key in all_keys:
            old_val = old_values.get(key)
            new_val = new_values.get(key)

            if old_val != new_val:
                changed.append(key)

        return changed

    def _to_response(self, audit_log: AuditLog) -> AuditLogResponse:
        """Convert AuditLog model to response schema."""
        line_changes = None
        if audit_log.line_item_changes:
            line_changes = [
                LineItemHistoryResponse(
                    id=line.id,
                    parent_audit_id=line.parent_audit_id,
                    entity_type=line.entity_type,
                    line_id=line.line_id,
                    line_number=line.line_number,
                    action=line.action,
                    old_values=line.old_values,
                    new_values=line.new_values,
                    created_at=line.created_at,
                )
                for line in audit_log.line_item_changes
            ]

        return AuditLogResponse(
            id=audit_log.id,
            organization_id=audit_log.organization_id,
            entity_type=audit_log.entity_type,
            entity_id=audit_log.entity_id,
            entity_reference=audit_log.entity_reference,
            action=audit_log.action,
            changed_by=audit_log.changed_by,
            changed_at=audit_log.changed_at,
            old_values=audit_log.old_values,
            new_values=audit_log.new_values,
            changed_fields=audit_log.changed_fields,
            change_reason=audit_log.change_reason,
            ip_address=audit_log.ip_address,
            user_agent=audit_log.user_agent,
            line_item_changes=line_changes,
        )


def model_to_dict(model: Any) -> Dict[str, Any]:
    """Convert SQLAlchemy model to dictionary for audit logging."""
    if hasattr(model, "__dict__"):
        return {
            key: value
            for key, value in model.__dict__.items()
            if not key.startswith("_")
        }
    return {}
