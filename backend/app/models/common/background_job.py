"""Background Job model for async task processing."""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy import (
    String,
    Text,
    Integer,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class JobStatus(str, Enum):
    """Background job status."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobType(str, Enum):
    """Background job types."""

    # Fixed Assets
    BULK_ASSET_IMPORT = "BULK_ASSET_IMPORT"
    BULK_ASSET_UPDATE = "BULK_ASSET_UPDATE"
    BULK_ASSET_TRANSFER = "BULK_ASSET_TRANSFER"
    BULK_ASSET_DISPOSE = "BULK_ASSET_DISPOSE"
    ASSET_EXPORT = "ASSET_EXPORT"
    DEPRECIATION_RUN = "DEPRECIATION_RUN"

    # Reports
    REPORT_GENERATION = "REPORT_GENERATION"

    # General
    DATA_MIGRATION = "DATA_MIGRATION"
    BATCH_GL_POSTING = "BATCH_GL_POSTING"


class BackgroundJob(BaseModel):
    """Model for tracking background jobs."""

    __tablename__ = "txn_background_job"

    # Organization reference
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Job identification
    job_type: Mapped[JobType] = mapped_column(
        SQLEnum(JobType, name="job_type_enum"),
        nullable=False,
        index=True,
    )
    job_name: Mapped[str] = mapped_column(String(200), nullable=False)
    job_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status tracking
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus, name="job_status_enum"),
        default=JobStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Progress tracking
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    processed_records: Mapped[int] = mapped_column(Integer, default=0)
    successful_records: Mapped[int] = mapped_column(Integer, default=0)
    failed_records: Mapped[int] = mapped_column(Integer, default=0)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0)

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Input/Output data
    input_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )
    error_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )

    # Result file (for exports)
    result_file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # User tracking
    created_by: Mapped[UUID] = mapped_column(
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=False,
    )

    # Indexes
    __table_args__ = (
        Index("ix_background_job_org_status", "organization_id", "status"),
        Index("ix_background_job_org_type", "organization_id", "job_type"),
        Index("ix_background_job_created", "created_at"),
    )

    def start(self) -> None:
        """Mark job as started."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)

    def complete(
        self,
        successful: int,
        failed: int,
        output_data: Optional[Dict] = None,
        result_file: Optional[str] = None,
    ) -> None:
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.successful_records = successful
        self.failed_records = failed
        self.processed_records = successful + failed
        self.progress_percentage = 100
        if output_data:
            self.output_data = output_data
        if result_file:
            self.result_file_path = result_file

    def fail(self, error_message: str, error_details: Optional[Dict] = None) -> None:
        """Mark job as failed."""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.error_details = {
            "message": error_message,
            "details": error_details or {},
        }

    def update_progress(self, processed: int, successful: int, failed: int) -> None:
        """Update job progress."""
        self.processed_records = processed
        self.successful_records = successful
        self.failed_records = failed
        if self.total_records > 0:
            self.progress_percentage = int((processed / self.total_records) * 100)

    @property
    def is_running(self) -> bool:
        """Check if job is currently running."""
        return self.status == JobStatus.RUNNING

    @property
    def is_completed(self) -> bool:
        """Check if job has completed (success or failure)."""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]

    @property
    def duration_seconds(self) -> Optional[int]:
        """Get job duration in seconds."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None
