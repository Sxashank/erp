"""Training models for the HRIS module."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.auth.user import User
    from app.models.hris.employee import Employee
    from app.models.masters.organization import Organization


class TrainingProgram(BaseModel):
    """Training program master."""

    __tablename__ = "hris_training_program"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "program_code",
            name="uq_hris_training_program_org_code",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    program_code: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    mode: Mapped[str] = mapped_column(String(30), nullable=False)
    trainer_type: Mapped[str] = mapped_column(String(20), nullable=False)
    trainer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    trainer_contact: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    duration_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    max_participants: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    cost_per_participant: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=Decimal("0")
    )
    pre_requisites: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    learning_objectives: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    certificate_provided: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    organization: Mapped["Organization"] = relationship()
    nominations: Mapped[List["TrainingNomination"]] = relationship(
        back_populates="program",
        cascade="all, delete-orphan",
    )
    feedback_entries: Mapped[List["TrainingFeedback"]] = relationship(
        back_populates="program",
        cascade="all, delete-orphan",
    )


class TrainingNomination(BaseModel):
    """Employee nomination for a training program."""

    __tablename__ = "hris_training_nomination"
    __table_args__ = (
        UniqueConstraint(
            "program_id",
            "employee_id",
            name="uq_hris_training_nomination_program_employee",
        ),
    )

    program_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_training_program.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="NOMINATED")
    attendance_marked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    program: Mapped["TrainingProgram"] = relationship(back_populates="nominations")
    employee: Mapped["Employee"] = relationship()
    nominated_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys="TrainingNomination.created_by",
        uselist=False,
    )


class TrainingFeedback(BaseModel):
    """Training feedback captured against a nominated employee."""

    __tablename__ = "hris_training_feedback"
    __table_args__ = (
        UniqueConstraint(
            "program_id",
            "employee_id",
            name="uq_hris_training_feedback_program_employee",
        ),
    )

    program_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_training_program.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nomination_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_training_nomination.id", ondelete="SET NULL"),
        nullable=True,
    )
    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    overall_rating: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    content_rating: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    trainer_rating: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    facilities_rating: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    relevance_rating: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    would_recommend: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    strengths: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    improvements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_on: Mapped[date] = mapped_column(Date, nullable=False)

    program: Mapped["TrainingProgram"] = relationship(back_populates="feedback_entries")
    nomination: Mapped[Optional["TrainingNomination"]] = relationship()
    employee: Mapped["Employee"] = relationship()
    submitted_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys="TrainingFeedback.created_by",
        uselist=False,
    )
