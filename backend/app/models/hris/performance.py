"""Performance management models for HRIS."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.auth.user import User
    from app.models.finance.financial_year import FinancialYear
    from app.models.hris.employee import Employee
    from app.models.masters.organization import Organization


class AppraisalCycle(BaseModel):
    """Appraisal cycle master."""

    __tablename__ = "mst_appraisal_cycle"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="ix_mst_appraisal_cycle_code"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    financial_year_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_financial_year.id", ondelete="SET NULL"),
        nullable=True,
    )
    cycle_type: Mapped[str] = mapped_column(String(50), nullable=False, default="ANNUAL")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    goal_setting_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    goal_setting_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    mid_review_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    mid_review_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    self_appraisal_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    self_appraisal_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    manager_review_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    manager_review_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    calibration_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    calibration_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT")
    rating_scale: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    weightage_goals: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("70.00"),
    )
    weightage_competencies: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("30.00"),
    )
    allow_self_rating: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allow_peer_feedback: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    organization: Mapped["Organization"] = relationship()
    financial_year: Mapped[Optional["FinancialYear"]] = relationship()
    goals: Mapped[List["PerformanceGoal"]] = relationship(
        back_populates="appraisal_cycle",
        cascade="all, delete-orphan",
    )
    appraisals: Mapped[List["EmployeeAppraisal"]] = relationship(
        back_populates="appraisal_cycle",
        cascade="all, delete-orphan",
    )


class PerformanceGoal(BaseModel):
    """Employee goal for an appraisal cycle."""

    __tablename__ = "txn_goal"

    appraisal_cycle_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_appraisal_cycle.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    goal_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    weightage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    target_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    measurement_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT")
    progress_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.00")
    )
    achievement_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    self_rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    self_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manager_rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    manager_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    final_rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    approved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    appraisal_cycle: Mapped["AppraisalCycle"] = relationship(back_populates="goals")
    employee: Mapped["Employee"] = relationship()
    approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by])


class EmployeeAppraisal(BaseModel):
    """Employee appraisal summary for a cycle."""

    __tablename__ = "txn_appraisal"
    __table_args__ = (
        UniqueConstraint(
            "appraisal_cycle_id",
            "employee_id",
            name="ix_txn_appraisal_unique",
        ),
    )

    appraisal_cycle_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_appraisal_cycle.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="NOT_STARTED")
    goal_rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    competency_rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    overall_rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    final_grade: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    self_appraisal_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    self_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    self_achievements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    self_challenges: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    self_development_areas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manager_review_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    manager_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manager_achievements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manager_improvements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manager_recommendations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    calibration_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    calibrated_rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    calibrated_grade: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    calibrated_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    calibrated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    employee_acknowledgment: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    acknowledgment_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    employee_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    appraisal_cycle: Mapped["AppraisalCycle"] = relationship(back_populates="appraisals")
    employee: Mapped["Employee"] = relationship()
    reviewer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewer_id])
    calibrator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[calibrated_by])
