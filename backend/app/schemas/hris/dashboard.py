"""Schemas for HRIS dashboard responses."""

from __future__ import annotations

from datetime import date
from typing import Literal, Optional
from uuid import UUID

from app.schemas.base import CamelSchema


class HRDashboardStatsResponse(CamelSchema):
    """Top-level KPI cards for HR dashboard."""

    total_employees: int
    active_employees: int
    new_joinees_this_month: int
    separations_this_month: int
    pending_leave_approvals: int
    pending_regularizations: int
    today_present: int
    today_absent: int
    today_on_leave: int
    attendance_percentage: float
    upcoming_trainings: int
    active_cycles: int
    pending_goals: int
    pending_appraisals: int
    payroll_ready_batches: int
    payroll_pending_batches: int


class HRDashboardPendingActionResponse(CamelSchema):
    """Pending approval or review task."""

    id: UUID
    type: Literal["LEAVE", "REGULARIZATION", "SEPARATION", "APPRAISAL", "TRAINING"]
    title: str
    employee: str
    request_date: date
    status: str


class HRDashboardUpcomingEventResponse(CamelSchema):
    """Upcoming dashboard event."""

    id: str
    type: Literal["HOLIDAY", "ANNIVERSARY", "TRAINING", "APPRAISAL_DUE"]
    title: str
    date: date
    count: Optional[int] = None


class HRDistributionItemResponse(CamelSchema):
    """Simple dimension-count report row."""

    label: str
    count: int


class HRDashboardPayrollStatusResponse(CamelSchema):
    """Payroll-readiness status for current organization."""

    latest_batch_id: Optional[UUID] = None
    latest_batch_number: Optional[str] = None
    latest_batch_status: Optional[str] = None
    processed_batches_this_year: int
    approved_batches_this_year: int
    paid_batches_this_year: int


class HRDashboardResponse(CamelSchema):
    """Dashboard response."""

    stats: HRDashboardStatsResponse
    pending_actions: list[HRDashboardPendingActionResponse]
    upcoming_events: list[HRDashboardUpcomingEventResponse]
    department_distribution: list[HRDistributionItemResponse]
    unit_distribution: list[HRDistributionItemResponse]
    training_completion: list[HRDistributionItemResponse]
    separation_pipeline: list[HRDistributionItemResponse]
    payroll: HRDashboardPayrollStatusResponse
