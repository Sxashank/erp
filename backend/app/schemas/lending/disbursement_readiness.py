"""Disbursement readiness cockpit response schemas."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from app.schemas.base import CamelSchema


class DisbursementReadinessSummary(CamelSchema):
    """Portfolio-level readiness KPIs for sanctioned corporate loans."""

    sanctioned_not_disbursed_count: int
    sanctioned_not_disbursed_amount: Decimal
    ready_count: int
    ready_amount: Decimal
    condition_blocked_count: int
    condition_blocked_amount: Decimal
    expired_count: int
    expired_amount: Decimal
    pending_disbursement_count: int
    pending_disbursement_amount: Decimal
    approved_pending_processing_count: int
    approved_pending_processing_amount: Decimal
    processed_this_month_amount: Decimal


class ReadinessBucketMetric(CamelSchema):
    """Readiness bucket for sanctioned-not-disbursed exposure."""

    bucket: str
    label: str
    count: int
    amount: Decimal


class ReadinessBlockerItem(CamelSchema):
    """Sanction awaiting manual disbursement or condition closure."""

    sanction_id: UUID
    sanction_number: str
    application_id: UUID
    application_number: str
    borrower_name: str
    project_name: str | None = None
    sanctioned_amount: Decimal
    undisbursed_amount: Decimal
    validity_date: str | None = None
    first_disbursement_deadline: str | None = None
    status: str
    readiness_status: str
    mandatory_pending: int
    mandatory_overdue: int
    pending_disbursement_amount: Decimal


class PendingDisbursementItem(CamelSchema):
    """Manual disbursement request pending approval or processing."""

    disbursement_id: UUID
    loan_account_id: UUID
    loan_account_number: str
    borrower_name: str
    reference: str
    requested_amount: Decimal
    approved_amount: Decimal | None = None
    scheduled_date: str | None = None
    request_date: str
    status: str
    conditions_verified: bool
    utr_number: str | None = None


class DisbursementReadinessResponse(CamelSchema):
    """Aggregate envelope returned by /api/v1/lending/disbursement-readiness."""

    summary: DisbursementReadinessSummary
    readiness_buckets: list[ReadinessBucketMetric]
    blockers: list[ReadinessBlockerItem]
    pending_disbursements: list[PendingDisbursementItem]
