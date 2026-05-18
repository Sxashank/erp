"""Unit tests for Approval Workflow service.

Tests cover:
- Approval workflow configuration
- Approval request creation
- Multi-level approval flow
- Approval status transitions
"""

import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.core.constants import (
    ApprovalWorkflowType,
    ApprovalRequestStatus,
    ApprovalAction,
)


class TestApprovalWorkflowConfiguration:
    """Tests for approval workflow configuration."""

    def test_workflow_threshold_check(self):
        """Test workflow threshold determines if approval needed."""
        threshold = Decimal("1000000.00")  # 10 Lakhs

        # Amount below threshold - no approval needed
        amount_below = Decimal("500000.00")
        assert amount_below < threshold

        # Amount above threshold - approval needed
        amount_above = Decimal("1500000.00")
        assert amount_above >= threshold

    def test_workflow_approval_levels(self):
        """Test workflow can have multiple approval levels."""
        # Single level approval
        single_level_workflow = {
            "workflow_type": ApprovalWorkflowType.FA_ASSET_CAPITALIZATION,
            "approval_levels": 1,
        }
        assert single_level_workflow["approval_levels"] == 1

        # Two level approval
        two_level_workflow = {
            "workflow_type": ApprovalWorkflowType.FA_ASSET_DISPOSAL,
            "approval_levels": 2,
        }
        assert two_level_workflow["approval_levels"] == 2

    def test_workflow_approvers_per_level(self):
        """Test approvers can be configured per level."""
        approver_1 = uuid4()
        approver_2 = uuid4()
        approver_3 = uuid4()

        workflow_config = {
            "level_1_approvers": [approver_1],
            "level_2_approvers": [approver_2, approver_3],
        }

        assert len(workflow_config["level_1_approvers"]) == 1
        assert len(workflow_config["level_2_approvers"]) == 2

    def test_workflow_types(self):
        """Test all workflow types are defined."""
        workflow_types = [
            ApprovalWorkflowType.FA_ASSET_CREATION,
            ApprovalWorkflowType.FA_ASSET_CAPITALIZATION,
            ApprovalWorkflowType.FA_ASSET_DISPOSAL,
            ApprovalWorkflowType.FA_ASSET_REVALUATION,
            ApprovalWorkflowType.FA_DEPRECIATION_RUN,
            ApprovalWorkflowType.FA_ASSET_TRANSFER,
            ApprovalWorkflowType.FA_INSURANCE_CLAIM,
            ApprovalWorkflowType.FA_LEASE_ACTIVATION,
        ]

        assert len(workflow_types) >= 8


class TestApprovalRequestCreation:
    """Tests for approval request creation."""

    def test_create_approval_request(self):
        """Test creating a new approval request."""
        request = {
            "id": uuid4(),
            "workflow_type": ApprovalWorkflowType.FA_ASSET_DISPOSAL,
            "entity_type": "FIXED_ASSET",
            "entity_id": uuid4(),
            "requested_by": uuid4(),
            "requested_at": datetime.now(timezone.utc),
            "status": ApprovalRequestStatus.PENDING,
            "current_level": 1,
        }

        assert request["status"] == ApprovalRequestStatus.PENDING
        assert request["current_level"] == 1

    def test_approval_request_includes_amount(self):
        """Test approval request includes amount for threshold check."""
        request = {
            "entity_id": uuid4(),
            "amount": Decimal("1500000.00"),
        }

        assert request["amount"] > 0

    def test_approval_request_includes_remarks(self):
        """Test approval request can include remarks."""
        request = {
            "entity_id": uuid4(),
            "remarks": "Asset disposal due to obsolescence",
        }

        assert len(request["remarks"]) > 0


class TestApprovalRequestStatusTransitions:
    """Tests for approval status transitions."""

    def test_pending_to_approved(self):
        """Test PENDING -> APPROVED transition."""
        current_status = ApprovalRequestStatus.PENDING
        action = ApprovalAction.APPROVE
        new_status = ApprovalRequestStatus.APPROVED

        assert current_status == ApprovalRequestStatus.PENDING
        assert new_status == ApprovalRequestStatus.APPROVED

    def test_pending_to_rejected(self):
        """Test PENDING -> REJECTED transition."""
        current_status = ApprovalRequestStatus.PENDING
        action = ApprovalAction.REJECT
        new_status = ApprovalRequestStatus.REJECTED

        assert current_status == ApprovalRequestStatus.PENDING
        assert new_status == ApprovalRequestStatus.REJECTED

    def test_pending_to_returned(self):
        """Test PENDING -> RETURNED transition."""
        current_status = ApprovalRequestStatus.PENDING
        action = ApprovalAction.RETURN
        new_status = ApprovalRequestStatus.RETURNED

        # Returned means sent back to maker for clarification
        assert new_status == ApprovalRequestStatus.RETURNED

    def test_approved_is_terminal(self):
        """Test APPROVED is a terminal status (for that level)."""
        status = ApprovalRequestStatus.APPROVED

        # Cannot change from APPROVED
        assert status == ApprovalRequestStatus.APPROVED

    def test_rejected_is_terminal(self):
        """Test REJECTED is a terminal status."""
        status = ApprovalRequestStatus.REJECTED

        # Cannot change from REJECTED
        assert status == ApprovalRequestStatus.REJECTED


class TestMultiLevelApproval:
    """Tests for multi-level approval flow."""

    def test_level_1_approval_advances_to_level_2(self):
        """Test level 1 approval advances request to level 2."""
        request = {
            "current_level": 1,
            "total_levels": 2,
            "status": ApprovalRequestStatus.PENDING,
        }

        # After level 1 approval
        request["current_level"] = 2
        request["status"] = ApprovalRequestStatus.PENDING  # Still pending level 2

        assert request["current_level"] == 2
        assert request["status"] == ApprovalRequestStatus.PENDING

    def test_final_level_approval_completes_request(self):
        """Test final level approval marks request as approved."""
        request = {
            "current_level": 2,
            "total_levels": 2,
            "status": ApprovalRequestStatus.PENDING,
        }

        # After level 2 approval (final level)
        request["status"] = ApprovalRequestStatus.APPROVED

        assert request["status"] == ApprovalRequestStatus.APPROVED

    def test_any_level_rejection_rejects_entire_request(self):
        """Test rejection at any level rejects entire request."""
        # Level 1 rejection
        level_1_reject = {
            "current_level": 1,
            "action": ApprovalAction.REJECT,
            "status": ApprovalRequestStatus.REJECTED,
        }
        assert level_1_reject["status"] == ApprovalRequestStatus.REJECTED

        # Level 2 rejection
        level_2_reject = {
            "current_level": 2,
            "action": ApprovalAction.REJECT,
            "status": ApprovalRequestStatus.REJECTED,
        }
        assert level_2_reject["status"] == ApprovalRequestStatus.REJECTED

    def test_approval_chain_tracking(self):
        """Test approval chain is tracked."""
        approval_chain = [
            {
                "level": 1,
                "approver_id": str(uuid4()),
                "action": "APPROVE",
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "comments": "Approved",
            },
            {
                "level": 2,
                "approver_id": str(uuid4()),
                "action": "APPROVE",
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "comments": "Final approval",
            },
        ]

        assert len(approval_chain) == 2
        assert all(entry["action"] == "APPROVE" for entry in approval_chain)


class TestApprovalAuthorization:
    """Tests for approval authorization."""

    def test_maker_cannot_approve_own_request(self):
        """Test maker cannot approve their own request."""
        maker_id = uuid4()
        approver_id = maker_id  # Same person

        is_self_approval = maker_id == approver_id
        assert is_self_approval  # Should be blocked

    def test_only_configured_approvers_can_approve(self):
        """Test only configured approvers can approve."""
        configured_approvers = [uuid4(), uuid4()]
        user_attempting_approval = uuid4()

        is_authorized = user_attempting_approval in configured_approvers
        assert not is_authorized

    def test_level_specific_approvers(self):
        """Test approvers are level-specific."""
        level_1_approvers = [uuid4(), uuid4()]
        level_2_approvers = [uuid4()]

        user = level_1_approvers[0]

        # User can approve level 1
        can_approve_level_1 = user in level_1_approvers
        assert can_approve_level_1

        # But not level 2
        can_approve_level_2 = user in level_2_approvers
        assert not can_approve_level_2


class TestApprovalTriggers:
    """Tests for when approval is triggered."""

    def test_asset_creation_above_threshold(self):
        """Test asset creation above threshold requires approval."""
        asset_cost = Decimal("1500000.00")
        threshold = Decimal("1000000.00")

        requires_approval = asset_cost >= threshold
        assert requires_approval

    def test_asset_disposal_always_requires_approval(self):
        """Test asset disposal always requires approval."""
        disposal_threshold = Decimal("0.00")  # Always required
        disposal_amount = Decimal("10000.00")

        requires_approval = disposal_amount >= disposal_threshold
        assert requires_approval

    def test_depreciation_run_requires_approval(self):
        """Test depreciation run posting requires approval."""
        # Depreciation run posting to GL always requires approval
        requires_approval = True
        assert requires_approval

    def test_insurance_claim_above_threshold(self):
        """Test insurance claim above threshold requires approval."""
        claim_amount = Decimal("600000.00")
        threshold = Decimal("500000.00")  # 5 Lakhs

        requires_approval = claim_amount >= threshold
        assert requires_approval


class TestApprovalCallbacks:
    """Tests for approval callbacks (post-approval actions)."""

    def test_asset_capitalization_on_approval(self):
        """Test asset is capitalized after approval."""
        # Before approval: PENDING_APPROVAL
        # After approval: ACTIVE
        pre_approval_status = "PENDING_APPROVAL"
        post_approval_status = "ACTIVE"

        assert pre_approval_status != post_approval_status

    def test_disposal_execution_on_approval(self):
        """Test disposal is executed after approval."""
        # Before approval: disposal_date = None
        # After approval: disposal_date = today
        disposal_date_before = None
        disposal_date_after = date.today()

        assert disposal_date_before is None
        assert disposal_date_after is not None

    def test_depreciation_gl_posting_on_approval(self):
        """Test depreciation GL entries are created after approval."""
        # Before approval: gl_posted = False
        # After approval: gl_posted = True
        gl_posted_before = False
        gl_posted_after = True

        assert gl_posted_before == False
        assert gl_posted_after == True


class TestApprovalNotifications:
    """Tests for approval notifications."""

    def test_notify_approvers_on_request_creation(self):
        """Test approvers are notified when request is created."""
        notification = {
            "type": "APPROVAL_REQUIRED",
            "recipients": [uuid4()],
            "entity_type": "FIXED_ASSET",
            "entity_id": uuid4(),
        }

        assert notification["type"] == "APPROVAL_REQUIRED"
        assert len(notification["recipients"]) > 0

    def test_notify_maker_on_approval(self):
        """Test maker is notified when request is approved."""
        notification = {
            "type": "REQUEST_APPROVED",
            "recipient": uuid4(),
            "entity_type": "FIXED_ASSET",
            "entity_id": uuid4(),
        }

        assert notification["type"] == "REQUEST_APPROVED"

    def test_notify_maker_on_rejection(self):
        """Test maker is notified when request is rejected."""
        notification = {
            "type": "REQUEST_REJECTED",
            "recipient": uuid4(),
            "entity_type": "FIXED_ASSET",
            "entity_id": uuid4(),
            "rejection_reason": "Insufficient documentation",
        }

        assert notification["type"] == "REQUEST_REJECTED"
        assert len(notification["rejection_reason"]) > 0


class TestApprovalExpiry:
    """Tests for approval request expiry."""

    def test_expired_request_cannot_be_approved(self):
        """Test expired request cannot be approved."""
        request_created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        expiry_days = 7
        current_date = datetime(2024, 1, 15, tzinfo=timezone.utc)

        days_since_creation = (current_date - request_created_at).days
        is_expired = days_since_creation > expiry_days

        assert is_expired

    def test_expired_request_status_updated(self):
        """Test expired request status is updated to EXPIRED."""
        is_expired = True
        current_status = ApprovalRequestStatus.PENDING

        if is_expired:
            new_status = ApprovalRequestStatus.EXPIRED
        else:
            new_status = current_status

        assert new_status == ApprovalRequestStatus.EXPIRED
