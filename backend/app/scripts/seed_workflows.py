"""Seed default workflow definitions and notification templates."""

import asyncio
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.workflow import (
    ApprovalMode,
    ApprovalRule,
    ApproverType,
    EscalationRule,
    EscalationType,
    NotificationTemplate,
    WorkflowDefinition,
    WorkflowEntityType,
    WorkflowStep,
    WorkflowStepType,
)


async def seed_workflow_definitions(
    db: AsyncSession,
    organization_id: UUID,
) -> None:
    """Seed default workflow definitions for an organization."""

    # Check if workflows already exist for this organization
    result = await db.execute(
        select(WorkflowDefinition)
        .where(WorkflowDefinition.organization_id == organization_id)
        .limit(1)
    )
    if result.scalar_one_or_none():
        print(f"Workflows already exist for organization {organization_id}, skipping...")
        return

    # 1. Purchase Bill Approval Workflow
    pb_workflow = WorkflowDefinition(
        organization_id=organization_id,
        name="Purchase Bill Approval",
        code="PB_APPROVAL",
        entity_type=WorkflowEntityType.PURCHASE_BILL,
        description="Multi-level approval workflow for purchase bills based on amount",
        is_default=True,
        priority=10,
        activation_conditions=None,  # Apply to all purchase bills
        allow_parallel_branches=False,
        require_comments_on_reject=True,
        notify_initiator_on_complete=True,
    )
    db.add(pb_workflow)
    await db.flush()

    # Step 1: Manager Approval (for all bills)
    pb_step1 = WorkflowStep(
        workflow_definition_id=pb_workflow.id,
        step_number=1,
        name="Manager Approval",
        step_type=WorkflowStepType.APPROVAL,
        approval_mode=ApprovalMode.SEQUENTIAL,
        entry_conditions=None,
        on_approve_action="NEXT",
        on_reject_action="REJECT",
        allow_delegation=True,
        sla_hours=24,
    )
    db.add(pb_step1)
    await db.flush()

    # Manager approval rule - Reporting Manager
    pb_rule1 = ApprovalRule(
        workflow_step_id=pb_step1.id,
        sequence=1,
        approver_type=ApproverType.REPORTING_MANAGER,
        is_mandatory=True,
        can_self_approve=False,
    )
    db.add(pb_rule1)

    # Escalation rule for step 1
    pb_esc1 = EscalationRule(
        workflow_step_id=pb_step1.id,
        level=1,
        timeout_hours=24,
        escalation_type=EscalationType.NOTIFY,
        notify_current_approver=True,
        notify_initiator=False,
    )
    db.add(pb_esc1)

    pb_esc2 = EscalationRule(
        workflow_step_id=pb_step1.id,
        level=2,
        timeout_hours=48,
        escalation_type=EscalationType.REASSIGN,
        escalate_to_type=ApproverType.DESIGNATION,
        escalate_to_designation="Finance Manager",
        notify_current_approver=True,
        notify_initiator=True,
    )
    db.add(pb_esc2)

    # Step 2: Finance Approval (for bills >= 50,000)
    pb_step2 = WorkflowStep(
        workflow_definition_id=pb_workflow.id,
        step_number=2,
        name="Finance Approval",
        step_type=WorkflowStepType.APPROVAL,
        approval_mode=ApprovalMode.PARALLEL_ANY,
        entry_conditions={"amount_gte": 50000},
        on_approve_action="NEXT",
        on_reject_action="REJECT",
        allow_delegation=True,
        sla_hours=24,
    )
    db.add(pb_step2)
    await db.flush()

    pb_rule2 = ApprovalRule(
        workflow_step_id=pb_step2.id,
        sequence=1,
        approver_type=ApproverType.DESIGNATION,
        designation="Finance Manager",
        is_mandatory=True,
        can_self_approve=False,
    )
    db.add(pb_rule2)

    # Step 3: CFO Approval (for bills >= 500,000)
    pb_step3 = WorkflowStep(
        workflow_definition_id=pb_workflow.id,
        step_number=3,
        name="CFO Approval",
        step_type=WorkflowStepType.APPROVAL,
        approval_mode=ApprovalMode.SEQUENTIAL,
        entry_conditions={"amount_gte": 500000},
        on_approve_action="COMPLETE",
        on_reject_action="REJECT",
        allow_delegation=False,
        sla_hours=48,
    )
    db.add(pb_step3)
    await db.flush()

    pb_rule3 = ApprovalRule(
        workflow_step_id=pb_step3.id,
        sequence=1,
        approver_type=ApproverType.DESIGNATION,
        designation="CFO",
        is_mandatory=True,
        can_self_approve=False,
    )
    db.add(pb_rule3)

    # 2. Sales Invoice Approval Workflow
    si_workflow = WorkflowDefinition(
        organization_id=organization_id,
        name="Sales Invoice Approval",
        code="SI_APPROVAL",
        entity_type=WorkflowEntityType.SALES_INVOICE,
        description="Approval workflow for sales invoices",
        is_default=True,
        priority=10,
        activation_conditions=None,
        allow_parallel_branches=False,
        require_comments_on_reject=True,
        notify_initiator_on_complete=True,
    )
    db.add(si_workflow)
    await db.flush()

    si_step1 = WorkflowStep(
        workflow_definition_id=si_workflow.id,
        step_number=1,
        name="Sales Manager Approval",
        step_type=WorkflowStepType.APPROVAL,
        approval_mode=ApprovalMode.SEQUENTIAL,
        entry_conditions=None,
        on_approve_action="COMPLETE",
        on_reject_action="REJECT",
        allow_delegation=True,
        sla_hours=8,
    )
    db.add(si_step1)
    await db.flush()

    si_rule1 = ApprovalRule(
        workflow_step_id=si_step1.id,
        sequence=1,
        approver_type=ApproverType.DESIGNATION,
        designation="Sales Manager",
        is_mandatory=True,
        can_self_approve=False,
    )
    db.add(si_rule1)

    # 3. Payment Approval Workflow
    pay_workflow = WorkflowDefinition(
        organization_id=organization_id,
        name="Payment Approval",
        code="PAY_APPROVAL",
        entity_type=WorkflowEntityType.PAYMENT,
        description="Multi-level approval workflow for payments based on amount",
        is_default=True,
        priority=10,
        activation_conditions=None,
        allow_parallel_branches=False,
        require_comments_on_reject=True,
        notify_initiator_on_complete=True,
    )
    db.add(pay_workflow)
    await db.flush()

    # Step 1: Finance Officer (for all payments)
    pay_step1 = WorkflowStep(
        workflow_definition_id=pay_workflow.id,
        step_number=1,
        name="Finance Officer Approval",
        step_type=WorkflowStepType.APPROVAL,
        approval_mode=ApprovalMode.SEQUENTIAL,
        entry_conditions=None,
        on_approve_action="NEXT",
        on_reject_action="REJECT",
        allow_delegation=True,
        sla_hours=4,
    )
    db.add(pay_step1)
    await db.flush()

    pay_rule1 = ApprovalRule(
        workflow_step_id=pay_step1.id,
        sequence=1,
        approver_type=ApproverType.DESIGNATION,
        designation="Finance Officer",
        is_mandatory=True,
        can_self_approve=False,
    )
    db.add(pay_rule1)

    # Step 2: Finance Manager (for payments >= 100,000)
    pay_step2 = WorkflowStep(
        workflow_definition_id=pay_workflow.id,
        step_number=2,
        name="Finance Manager Approval",
        step_type=WorkflowStepType.APPROVAL,
        approval_mode=ApprovalMode.SEQUENTIAL,
        entry_conditions={"amount_gte": 100000},
        on_approve_action="NEXT",
        on_reject_action="REJECT",
        allow_delegation=True,
        sla_hours=8,
    )
    db.add(pay_step2)
    await db.flush()

    pay_rule2 = ApprovalRule(
        workflow_step_id=pay_step2.id,
        sequence=1,
        approver_type=ApproverType.DESIGNATION,
        designation="Finance Manager",
        is_mandatory=True,
        can_self_approve=False,
    )
    db.add(pay_rule2)

    # Step 3: CFO (for payments >= 1,000,000)
    pay_step3 = WorkflowStep(
        workflow_definition_id=pay_workflow.id,
        step_number=3,
        name="CFO Approval",
        step_type=WorkflowStepType.APPROVAL,
        approval_mode=ApprovalMode.SEQUENTIAL,
        entry_conditions={"amount_gte": 1000000},
        on_approve_action="COMPLETE",
        on_reject_action="REJECT",
        allow_delegation=False,
        sla_hours=24,
    )
    db.add(pay_step3)
    await db.flush()

    pay_rule3 = ApprovalRule(
        workflow_step_id=pay_step3.id,
        sequence=1,
        approver_type=ApproverType.DESIGNATION,
        designation="CFO",
        is_mandatory=True,
        can_self_approve=False,
    )
    db.add(pay_rule3)

    # 4. Voucher Approval Workflow
    vcr_workflow = WorkflowDefinition(
        organization_id=organization_id,
        name="Voucher Approval",
        code="VCR_APPROVAL",
        entity_type=WorkflowEntityType.VOUCHER,
        description="Approval workflow for journal vouchers and general ledger entries",
        is_default=True,
        priority=10,
        activation_conditions=None,
        allow_parallel_branches=False,
        require_comments_on_reject=True,
        notify_initiator_on_complete=True,
    )
    db.add(vcr_workflow)
    await db.flush()

    vcr_step1 = WorkflowStep(
        workflow_definition_id=vcr_workflow.id,
        step_number=1,
        name="Accountant Approval",
        step_type=WorkflowStepType.APPROVAL,
        approval_mode=ApprovalMode.SEQUENTIAL,
        entry_conditions=None,
        on_approve_action="NEXT",
        on_reject_action="REJECT",
        allow_delegation=True,
        sla_hours=8,
    )
    db.add(vcr_step1)
    await db.flush()

    vcr_rule1 = ApprovalRule(
        workflow_step_id=vcr_step1.id,
        sequence=1,
        approver_type=ApproverType.DESIGNATION,
        designation="Senior Accountant",
        is_mandatory=True,
        can_self_approve=False,
    )
    db.add(vcr_rule1)

    # Step 2: Finance Manager (for vouchers >= 100,000)
    vcr_step2 = WorkflowStep(
        workflow_definition_id=vcr_workflow.id,
        step_number=2,
        name="Finance Manager Approval",
        step_type=WorkflowStepType.APPROVAL,
        approval_mode=ApprovalMode.SEQUENTIAL,
        entry_conditions={"amount_gte": 100000},
        on_approve_action="COMPLETE",
        on_reject_action="REJECT",
        allow_delegation=True,
        sla_hours=24,
    )
    db.add(vcr_step2)
    await db.flush()

    vcr_rule2 = ApprovalRule(
        workflow_step_id=vcr_step2.id,
        sequence=1,
        approver_type=ApproverType.DESIGNATION,
        designation="Finance Manager",
        is_mandatory=True,
        can_self_approve=False,
    )
    db.add(vcr_rule2)

    # -------------------------------------------------------------------------
    # 5. Loan Application Review — Credit Officer → Credit Manager (≥ ₹25L).
    #    Mirrors the §8.4 delegation band; the amount_gte gate is conservative
    #    and aligns with the existing Officer → GM handoff.
    # -------------------------------------------------------------------------
    la_workflow = WorkflowDefinition(
        organization_id=organization_id,
        name="Loan Application Review",
        code="LOAN_APPLICATION_REVIEW",
        entity_type=WorkflowEntityType.LOAN_APPLICATION,
        description="Credit underwriting review for loan applications",
        is_default=True,
        priority=10,
        activation_conditions=None,
        allow_parallel_branches=False,
        require_comments_on_reject=True,
        notify_initiator_on_complete=True,
    )
    db.add(la_workflow)
    await db.flush()

    la_step1 = WorkflowStep(
        workflow_definition_id=la_workflow.id,
        step_number=1,
        name="Credit Officer Review",
        step_type=WorkflowStepType.APPROVAL,
        approval_mode=ApprovalMode.SEQUENTIAL,
        entry_conditions=None,
        on_approve_action="NEXT",
        on_reject_action="REJECT",
        allow_delegation=True,
        sla_hours=24,
    )
    db.add(la_step1)
    await db.flush()
    db.add(
        ApprovalRule(
            workflow_step_id=la_step1.id,
            sequence=1,
            approver_type=ApproverType.DESIGNATION,
            designation="Credit Officer",
            is_mandatory=True,
            can_self_approve=False,
        )
    )

    la_step2 = WorkflowStep(
        workflow_definition_id=la_workflow.id,
        step_number=2,
        name="Credit Manager Review",
        step_type=WorkflowStepType.APPROVAL,
        approval_mode=ApprovalMode.SEQUENTIAL,
        entry_conditions={"amount_gte": 2500000},
        on_approve_action="COMPLETE",
        on_reject_action="REJECT",
        allow_delegation=False,
        sla_hours=48,
    )
    db.add(la_step2)
    await db.flush()
    db.add(
        ApprovalRule(
            workflow_step_id=la_step2.id,
            sequence=1,
            approver_type=ApproverType.DESIGNATION,
            designation="Credit Manager",
            is_mandatory=True,
            can_self_approve=False,
        )
    )

    # -------------------------------------------------------------------------
    # 6. Loan Sanction Approval — Officer → GM → ED → CMD → Board ladder per
    #    the delegation matrix in app/core/maker_checker.py. Thresholds are
    #    placeholders; production deploys override via the workflow UI.
    # -------------------------------------------------------------------------
    ls_workflow = WorkflowDefinition(
        organization_id=organization_id,
        name="Loan Sanction Approval",
        code="LOAN_SANCTION_APPROVAL",
        entity_type=WorkflowEntityType.LOAN_SANCTION,
        description="Delegation-banded approval for loan sanctions",
        is_default=True,
        priority=10,
        activation_conditions=None,
        allow_parallel_branches=False,
        require_comments_on_reject=True,
        notify_initiator_on_complete=True,
    )
    db.add(ls_workflow)
    await db.flush()

    ls_step1 = WorkflowStep(
        workflow_definition_id=ls_workflow.id,
        step_number=1,
        name="Credit Officer Approval",
        step_type=WorkflowStepType.APPROVAL,
        approval_mode=ApprovalMode.SEQUENTIAL,
        entry_conditions=None,
        on_approve_action="NEXT",
        on_reject_action="REJECT",
        allow_delegation=True,
        sla_hours=24,
    )
    db.add(ls_step1)
    await db.flush()
    db.add(
        ApprovalRule(
            workflow_step_id=ls_step1.id,
            sequence=1,
            approver_type=ApproverType.DESIGNATION,
            designation="Credit Officer",
            is_mandatory=True,
            can_self_approve=False,
        )
    )

    ls_step2 = WorkflowStep(
        workflow_definition_id=ls_workflow.id,
        step_number=2,
        name="GM Approval",
        step_type=WorkflowStepType.APPROVAL,
        approval_mode=ApprovalMode.SEQUENTIAL,
        entry_conditions={"amount_gte": 5000000},  # ≥ ₹50L
        on_approve_action="NEXT",
        on_reject_action="REJECT",
        allow_delegation=True,
        sla_hours=48,
    )
    db.add(ls_step2)
    await db.flush()
    db.add(
        ApprovalRule(
            workflow_step_id=ls_step2.id,
            sequence=1,
            approver_type=ApproverType.DESIGNATION,
            designation="GM",
            is_mandatory=True,
            can_self_approve=False,
        )
    )

    ls_step3 = WorkflowStep(
        workflow_definition_id=ls_workflow.id,
        step_number=3,
        name="ED Approval",
        step_type=WorkflowStepType.APPROVAL,
        approval_mode=ApprovalMode.SEQUENTIAL,
        entry_conditions={"amount_gte": 25000000},  # ≥ ₹2.5Cr
        on_approve_action="NEXT",
        on_reject_action="REJECT",
        allow_delegation=False,
        sla_hours=72,
    )
    db.add(ls_step3)
    await db.flush()
    db.add(
        ApprovalRule(
            workflow_step_id=ls_step3.id,
            sequence=1,
            approver_type=ApproverType.DESIGNATION,
            designation="ED",
            is_mandatory=True,
            can_self_approve=False,
        )
    )

    ls_step4 = WorkflowStep(
        workflow_definition_id=ls_workflow.id,
        step_number=4,
        name="CMD / Board Approval",
        step_type=WorkflowStepType.APPROVAL,
        approval_mode=ApprovalMode.SEQUENTIAL,
        entry_conditions={"amount_gte": 100000000},  # ≥ ₹10Cr
        on_approve_action="COMPLETE",
        on_reject_action="REJECT",
        allow_delegation=False,
        sla_hours=168,
    )
    db.add(ls_step4)
    await db.flush()
    db.add(
        ApprovalRule(
            workflow_step_id=ls_step4.id,
            sequence=1,
            approver_type=ApproverType.DESIGNATION,
            designation="CMD",
            is_mandatory=True,
            can_self_approve=False,
        )
    )

    # -------------------------------------------------------------------------
    # 7. Entity Rating Approval — Credit Committee (no amount band).
    # -------------------------------------------------------------------------
    lr_workflow = WorkflowDefinition(
        organization_id=organization_id,
        name="Entity Rating Approval",
        code="ENTITY_RATING_APPROVAL",
        entity_type=WorkflowEntityType.LOAN_RATING,
        description="Credit committee review of internal entity ratings",
        is_default=True,
        priority=10,
        activation_conditions=None,
        allow_parallel_branches=False,
        require_comments_on_reject=True,
        notify_initiator_on_complete=True,
    )
    db.add(lr_workflow)
    await db.flush()

    lr_step1 = WorkflowStep(
        workflow_definition_id=lr_workflow.id,
        step_number=1,
        name="Credit Committee Approval",
        step_type=WorkflowStepType.APPROVAL,
        approval_mode=ApprovalMode.PARALLEL_ALL,
        entry_conditions=None,
        on_approve_action="COMPLETE",
        on_reject_action="REJECT",
        allow_delegation=False,
        sla_hours=72,
    )
    db.add(lr_step1)
    await db.flush()
    # Credit Committee is modelled as a designation for seeding since ROLE
    # requires a concrete role_id (UUID) we don't know at seed time. Admins can
    # switch to ROLE in the workflow UI post-deployment if the org prefers it.
    db.add(
        ApprovalRule(
            workflow_step_id=lr_step1.id,
            sequence=1,
            approver_type=ApproverType.DESIGNATION,
            designation="Credit Committee",
            is_mandatory=True,
            can_self_approve=False,
        )
    )

    await db.commit()
    print(f"Created default workflow definitions for organization {organization_id}")


async def seed_notification_templates(
    db: AsyncSession,
    organization_id: UUID,
) -> None:
    """Seed default notification templates for an organization."""

    # Check if templates already exist
    result = await db.execute(
        select(NotificationTemplate)
        .where(NotificationTemplate.organization_id == organization_id)
        .limit(1)
    )
    if result.scalar_one_or_none():
        print(
            f"Notification templates already exist for organization {organization_id}, skipping..."
        )
        return

    templates = [
        NotificationTemplate(
            organization_id=organization_id,
            code="APPROVAL_PENDING",
            name="Approval Request",
            entity_type=None,  # Generic template for all entity types
            email_subject="[{app_name}] Approval Required: {entity_type} - {entity_reference}",
            email_body="""
<p>Hello {approver_name},</p>
<p>A new {entity_type} requires your approval.</p>
<p><strong>Reference:</strong> {entity_reference}<br>
<strong>Amount:</strong> {amount}<br>
<strong>Submitted By:</strong> {initiator_name}</p>
<p>Please review and take appropriate action.</p>
""",
            available_variables=[
                "app_name",
                "entity_type",
                "entity_reference",
                "amount",
                "approver_name",
                "initiator_name",
                "step_name",
                "due_date",
            ],
        ),
        NotificationTemplate(
            organization_id=organization_id,
            code="APPROVAL_APPROVED",
            name="Approval Completed - Approved",
            entity_type=None,
            email_subject="[{app_name}] Approved: {entity_type} - {entity_reference}",
            email_body="""
<p>Hello {initiator_name},</p>
<p>Your {entity_type} has been <strong>approved</strong>.</p>
<p><strong>Reference:</strong> {entity_reference}<br>
<strong>Amount:</strong> {amount}<br>
<strong>Approved By:</strong> {approver_name}</p>
""",
            available_variables=[
                "app_name",
                "entity_type",
                "entity_reference",
                "amount",
                "approver_name",
                "initiator_name",
                "comments",
            ],
        ),
        NotificationTemplate(
            organization_id=organization_id,
            code="APPROVAL_REJECTED",
            name="Approval Completed - Rejected",
            entity_type=None,
            email_subject="[{app_name}] Rejected: {entity_type} - {entity_reference}",
            email_body="""
<p>Hello {initiator_name},</p>
<p>Your {entity_type} has been <strong>rejected</strong>.</p>
<p><strong>Reference:</strong> {entity_reference}<br>
<strong>Amount:</strong> {amount}<br>
<strong>Rejected By:</strong> {approver_name}<br>
<strong>Reason:</strong> {comments}</p>
<p>Please review the comments and make necessary corrections.</p>
""",
            available_variables=[
                "app_name",
                "entity_type",
                "entity_reference",
                "amount",
                "approver_name",
                "initiator_name",
                "comments",
            ],
        ),
        NotificationTemplate(
            organization_id=organization_id,
            code="ESCALATION_NOTICE",
            name="Escalation Notice",
            entity_type=None,
            email_subject="[{app_name}] ESCALATION: {entity_type} - {entity_reference}",
            email_body="""
<p>Hello {escalate_to_name},</p>
<p>A {entity_type} approval has been escalated to you due to timeout.</p>
<p><strong>Reference:</strong> {entity_reference}<br>
<strong>Amount:</strong> {amount}<br>
<strong>Original Approver:</strong> {original_approver}<br>
<strong>Escalation Level:</strong> {escalation_level}</p>
<p>Please review and take action immediately.</p>
""",
            available_variables=[
                "app_name",
                "entity_type",
                "entity_reference",
                "amount",
                "escalate_to_name",
                "original_approver",
                "escalation_level",
                "pending_since",
            ],
        ),
    ]

    for template in templates:
        db.add(template)

    await db.commit()
    print(f"Created default notification templates for organization {organization_id}")


async def seed_all_for_organization(organization_id: UUID) -> None:
    """Seed all default workflow data for an organization."""
    async with async_session_factory() as db:
        await seed_workflow_definitions(db, organization_id)
        await seed_notification_templates(db, organization_id)


async def main():
    """Main entry point for seeding workflow data."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m app.scripts.seed_workflows <organization_id>")
        print("Example: python -m app.scripts.seed_workflows 550e8400-e29b-41d4-a716-446655440000")
        sys.exit(1)

    organization_id = UUID(sys.argv[1])
    await seed_all_for_organization(organization_id)
    print("Workflow seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
