"""Reporting runtime models for generated MIS output."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ReportRun(BaseModel):
    """A generated report run and its export metadata."""

    __tablename__ = "rpt_report_run"
    __table_args__ = (
        Index("ix_rpt_run_org_generated", "organization_id", "generated_at"),
        Index("ix_rpt_run_org_report", "organization_id", "report_code"),
        Index("ix_rpt_run_org_status", "organization_id", "status"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    report_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    report_name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    generated_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="COMPLETED")
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    export_format: Mapped[str] = mapped_column(String(20), nullable=False, default="XLSX")
    file_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)


class ReportSchedule(BaseModel):
    """Manual-first persisted report schedule configuration."""

    __tablename__ = "rpt_report_schedule"
    __table_args__ = (
        Index("ix_rpt_schedule_org_report", "organization_id", "report_code"),
        Index("ix_rpt_schedule_org_active", "organization_id", "is_active"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    report_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    report_name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    frequency: Mapped[str] = mapped_column(String(30), nullable=False)
    schedule_time: Mapped[str] = mapped_column(String(10), nullable=False)
    output_format: Mapped[str] = mapped_column(String(20), nullable=False, default="XLSX")
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    recipients: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    delivery_mode: Mapped[str] = mapped_column(
        String(30), nullable=False, default="MANUAL_DOWNLOAD"
    )
    owner_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
