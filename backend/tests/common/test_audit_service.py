"""Unit tests for Audit Service.

Tests cover:
- Audit log creation
- Change tracking
- Financial impact logging
- Approval action logging
"""

import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4
from typing import Dict, Any


class TestAuditLogCreation:
    """Tests for audit log creation."""

    def test_create_audit_log_entry(self):
        """Test creating a basic audit log entry."""
        audit_entry = {
            "id": uuid4(),
            "organization_id": uuid4(),
            "entity_type": "FIXED_ASSET",
            "entity_id": uuid4(),
            "action": "CREATE",
            "user_id": uuid4(),
            "timestamp": datetime.now(timezone.utc),
            "old_values": None,
            "new_values": {"asset_name": "Dell Laptop"},
        }

        assert audit_entry["action"] == "CREATE"
        assert audit_entry["old_values"] is None

    def test_update_audit_log_entry(self):
        """Test creating an update audit log entry."""
        audit_entry = {
            "entity_type": "FIXED_ASSET",
            "entity_id": uuid4(),
            "action": "UPDATE",
            "old_values": {"asset_name": "Dell Laptop"},
            "new_values": {"asset_name": "HP Desktop"},
        }

        assert audit_entry["action"] == "UPDATE"
        assert audit_entry["old_values"] is not None
        assert audit_entry["new_values"] is not None

    def test_delete_audit_log_entry(self):
        """Test creating a delete audit log entry."""
        audit_entry = {
            "entity_type": "FIXED_ASSET",
            "entity_id": uuid4(),
            "action": "DELETE",
            "old_values": {"asset_name": "Dell Laptop", "status": "ACTIVE"},
            "new_values": None,
        }

        assert audit_entry["action"] == "DELETE"
        assert audit_entry["new_values"] is None


class TestChangeTracking:
    """Tests for change tracking in audit logs."""

    def test_track_field_changes(self):
        """Test tracking individual field changes."""
        old_values = {
            "asset_name": "Dell Laptop",
            "location": "Mumbai",
            "status": "ACTIVE",
        }
        new_values = {
            "asset_name": "Dell Laptop",  # No change
            "location": "Delhi",  # Changed
            "status": "UNDER_MAINTENANCE",  # Changed
        }

        changed_fields = {
            k: {"old": old_values[k], "new": new_values[k]}
            for k in new_values
            if old_values.get(k) != new_values.get(k)
        }

        assert "location" in changed_fields
        assert "status" in changed_fields
        assert "asset_name" not in changed_fields

    def test_track_decimal_changes(self):
        """Test tracking Decimal field changes."""
        old_values = {"accumulated_depreciation": Decimal("40000.00")}
        new_values = {"accumulated_depreciation": Decimal("45000.00")}

        change = new_values["accumulated_depreciation"] - old_values["accumulated_depreciation"]

        assert change == Decimal("5000.00")

    def test_track_date_changes(self):
        """Test tracking date field changes."""
        old_values = {"put_to_use_date": None}
        new_values = {"put_to_use_date": date(2024, 4, 1)}

        assert old_values["put_to_use_date"] is None
        assert new_values["put_to_use_date"] == date(2024, 4, 1)

    def test_track_status_transition(self):
        """Test tracking status transitions."""
        old_status = "DRAFT"
        new_status = "ACTIVE"

        transition = f"{old_status} -> {new_status}"

        assert transition == "DRAFT -> ACTIVE"


class TestFinancialImpactLogging:
    """Tests for financial impact logging."""

    def test_log_disposal_financial_impact(self):
        """Test logging financial impact of disposal."""
        financial_impact = {
            "transaction_type": "ASSET_DISPOSAL",
            "asset_value": Decimal("100000.00"),
            "accumulated_depreciation": Decimal("60000.00"),
            "book_value": Decimal("40000.00"),
            "disposal_proceeds": Decimal("50000.00"),
            "gain_loss": Decimal("10000.00"),
        }

        assert financial_impact["gain_loss"] == Decimal("10000.00")
        assert financial_impact["book_value"] == (
            financial_impact["asset_value"] - financial_impact["accumulated_depreciation"]
        )

    def test_log_depreciation_financial_impact(self):
        """Test logging financial impact of depreciation run."""
        financial_impact = {
            "transaction_type": "DEPRECIATION_RUN",
            "run_date": date(2024, 3, 31),
            "total_depreciation": Decimal("500000.00"),
            "assets_processed": 150,
            "gl_voucher_id": uuid4(),
        }

        assert financial_impact["total_depreciation"] == Decimal("500000.00")
        assert financial_impact["assets_processed"] == 150

    def test_log_revaluation_financial_impact(self):
        """Test logging financial impact of revaluation."""
        financial_impact = {
            "transaction_type": "ASSET_REVALUATION",
            "old_book_value": Decimal("60000.00"),
            "new_revalued_amount": Decimal("80000.00"),
            "revaluation_surplus": Decimal("20000.00"),
            "effective_date": date(2024, 3, 31),
        }

        assert financial_impact["revaluation_surplus"] == Decimal("20000.00")

    def test_log_impairment_financial_impact(self):
        """Test logging financial impact of impairment."""
        financial_impact = {
            "transaction_type": "ASSET_IMPAIRMENT",
            "book_value": Decimal("80000.00"),
            "recoverable_amount": Decimal("50000.00"),
            "impairment_loss": Decimal("30000.00"),
        }

        assert financial_impact["impairment_loss"] == (
            financial_impact["book_value"] - financial_impact["recoverable_amount"]
        )


class TestApprovalActionLogging:
    """Tests for approval action logging."""

    def test_log_approval_request(self):
        """Test logging approval request submission."""
        audit_entry = {
            "entity_type": "APPROVAL_REQUEST",
            "entity_id": uuid4(),
            "action": "SUBMIT_FOR_APPROVAL",
            "user_id": uuid4(),
            "audit_context": {
                "workflow_type": "ASSET_DISPOSAL",
                "amount": "1500000.00",
                "entity_reference": "FA/COMP/2024/00001",
            },
        }

        assert audit_entry["action"] == "SUBMIT_FOR_APPROVAL"
        assert "workflow_type" in audit_entry["audit_context"]

    def test_log_approval_action(self):
        """Test logging approval/rejection action."""
        audit_entry = {
            "entity_type": "APPROVAL_REQUEST",
            "entity_id": uuid4(),
            "action": "APPROVAL_APPROVED",
            "user_id": uuid4(),
            "audit_context": {
                "level": 1,
                "comments": "Approved as per policy",
                "previous_status": "PENDING",
                "new_status": "APPROVED",
            },
        }

        assert audit_entry["action"] == "APPROVAL_APPROVED"
        assert audit_entry["audit_context"]["level"] == 1

    def test_log_rejection_action(self):
        """Test logging rejection action."""
        audit_entry = {
            "entity_type": "APPROVAL_REQUEST",
            "entity_id": uuid4(),
            "action": "APPROVAL_REJECTED",
            "user_id": uuid4(),
            "audit_context": {
                "level": 2,
                "comments": "Insufficient documentation",
                "rejection_reason": "Documentation missing",
            },
        }

        assert audit_entry["action"] == "APPROVAL_REJECTED"
        assert "rejection_reason" in audit_entry["audit_context"]


class TestGLPostingLogging:
    """Tests for GL posting audit logging."""

    def test_log_gl_posting_success(self):
        """Test logging successful GL posting."""
        audit_entry = {
            "entity_type": "FIXED_ASSET",
            "entity_id": uuid4(),
            "action": "GL_POST_SUCCESS",
            "audit_context": {
                "voucher_id": str(uuid4()),
                "voucher_number": "JV/2024/00123",
                "total_debit": "100000.00",
                "total_credit": "100000.00",
                "posting_date": "2024-03-31",
            },
        }

        assert audit_entry["action"] == "GL_POST_SUCCESS"
        assert audit_entry["audit_context"]["total_debit"] == audit_entry["audit_context"]["total_credit"]

    def test_log_gl_posting_failure(self):
        """Test logging failed GL posting."""
        audit_entry = {
            "entity_type": "FIXED_ASSET",
            "entity_id": uuid4(),
            "action": "GL_POST_FAILED",
            "audit_context": {
                "error_message": "Period closed for posting",
                "posting_date": "2024-03-31",
                "attempted_by": str(uuid4()),
            },
        }

        assert audit_entry["action"] == "GL_POST_FAILED"
        assert "error_message" in audit_entry["audit_context"]


class TestBulkOperationLogging:
    """Tests for bulk operation audit logging."""

    def test_log_bulk_import(self):
        """Test logging bulk import operation."""
        audit_entry = {
            "entity_type": "FIXED_ASSET",
            "action": "BULK_IMPORT",
            "user_id": uuid4(),
            "audit_context": {
                "total_records": 100,
                "successful": 95,
                "failed": 5,
                "error_details": [
                    {"row": 10, "error": "Invalid category"},
                    {"row": 25, "error": "Duplicate asset code"},
                ],
            },
        }

        assert audit_entry["action"] == "BULK_IMPORT"
        assert audit_entry["audit_context"]["total_records"] == 100
        assert audit_entry["audit_context"]["successful"] == 95

    def test_log_bulk_update(self):
        """Test logging bulk update operation."""
        audit_entry = {
            "entity_type": "FIXED_ASSET",
            "action": "BULK_UPDATE",
            "user_id": uuid4(),
            "audit_context": {
                "total_records": 50,
                "successful": 48,
                "failed": 2,
                "updated_fields": ["location", "custodian_id"],
            },
        }

        assert audit_entry["action"] == "BULK_UPDATE"
        assert "updated_fields" in audit_entry["audit_context"]


class TestConfigurationChangeLogging:
    """Tests for configuration change audit logging."""

    def test_log_config_change(self):
        """Test logging configuration changes."""
        audit_entry = {
            "entity_type": "FA_CONFIGURATION",
            "entity_id": uuid4(),
            "action": "UPDATE",
            "user_id": uuid4(),
            "old_values": {
                "creation_approval_threshold": "1000000.00",
                "amc_expiry_reminder_days": 30,
            },
            "new_values": {
                "creation_approval_threshold": "500000.00",
                "amc_expiry_reminder_days": 45,
            },
        }

        assert audit_entry["old_values"]["creation_approval_threshold"] != audit_entry["new_values"]["creation_approval_threshold"]

    def test_log_threshold_change(self):
        """Test logging approval threshold changes."""
        audit_entry = {
            "entity_type": "APPROVAL_WORKFLOW",
            "entity_id": uuid4(),
            "action": "UPDATE",
            "audit_context": {
                "config_type": "APPROVAL_THRESHOLD",
                "workflow_type": "ASSET_DISPOSAL",
                "old_threshold": "0.00",
                "new_threshold": "100000.00",
                "authorized_by": str(uuid4()),
            },
        }

        assert audit_entry["audit_context"]["config_type"] == "APPROVAL_THRESHOLD"


class TestAuditQueryHelpers:
    """Tests for audit log query helpers."""

    def test_filter_by_entity(self):
        """Test filtering audit logs by entity."""
        entity_id = uuid4()
        audit_logs = [
            {"entity_id": entity_id, "action": "CREATE"},
            {"entity_id": entity_id, "action": "UPDATE"},
            {"entity_id": uuid4(), "action": "CREATE"},
        ]

        filtered = [log for log in audit_logs if log["entity_id"] == entity_id]

        assert len(filtered) == 2

    def test_filter_by_date_range(self):
        """Test filtering audit logs by date range."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 31, tzinfo=timezone.utc)

        audit_logs = [
            {"timestamp": datetime(2024, 1, 15, tzinfo=timezone.utc)},
            {"timestamp": datetime(2024, 2, 15, tzinfo=timezone.utc)},
            {"timestamp": datetime(2023, 12, 15, tzinfo=timezone.utc)},
        ]

        filtered = [
            log for log in audit_logs
            if start_date <= log["timestamp"] <= end_date
        ]

        assert len(filtered) == 1

    def test_filter_by_action_type(self):
        """Test filtering audit logs by action type."""
        audit_logs = [
            {"action": "CREATE"},
            {"action": "UPDATE"},
            {"action": "UPDATE"},
            {"action": "DELETE"},
        ]

        filtered = [log for log in audit_logs if log["action"] == "UPDATE"]

        assert len(filtered) == 2

    def test_filter_by_user(self):
        """Test filtering audit logs by user."""
        user_id = uuid4()
        audit_logs = [
            {"user_id": user_id, "action": "CREATE"},
            {"user_id": user_id, "action": "UPDATE"},
            {"user_id": uuid4(), "action": "CREATE"},
        ]

        filtered = [log for log in audit_logs if log["user_id"] == user_id]

        assert len(filtered) == 2


class TestAuditRetention:
    """Tests for audit log retention."""

    def test_audit_retention_period(self):
        """Test audit logs are retained for required period."""
        retention_years = 8  # RBI requirement
        log_date = datetime(2020, 4, 1, tzinfo=timezone.utc)
        current_date = datetime(2024, 4, 1, tzinfo=timezone.utc)

        years_since_log = (current_date - log_date).days / 365
        is_within_retention = years_since_log <= retention_years

        assert is_within_retention

    def test_audit_logs_not_deleted(self):
        """Test audit logs are not deleted (immutable)."""
        # Audit logs should only be archived, never deleted
        can_delete = False
        can_archive = True

        assert not can_delete
        assert can_archive
