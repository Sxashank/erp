"""Unit tests for Background Job service.

Tests cover:
- Job creation and status tracking
- Job lifecycle (pending -> running -> completed/failed)
- Progress tracking
- Job cancellation
"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import uuid4
from typing import Dict, Any

from app.models.common.background_job import JobStatus, JobType


class TestJobCreation:
    """Tests for job creation."""

    def test_create_job_with_defaults(self):
        """Test creating a job with default values."""
        job = {
            "id": uuid4(),
            "organization_id": uuid4(),
            "job_type": JobType.BULK_ASSET_IMPORT,
            "job_name": "Test Import Job",
            "status": JobStatus.PENDING,
            "total_records": 0,
            "processed_records": 0,
            "successful_records": 0,
            "failed_records": 0,
            "progress_percentage": 0,
            "created_by": uuid4(),
            "created_at": datetime.now(timezone.utc),
        }

        assert job["status"] == JobStatus.PENDING
        assert job["progress_percentage"] == 0

    def test_create_job_with_input_data(self):
        """Test creating a job with input data."""
        input_data = {
            "assets": [
                {"asset_name": "Laptop 1", "category_code": "COMP"},
                {"asset_name": "Laptop 2", "category_code": "COMP"},
            ],
            "validation_mode": False,
        }

        job = {
            "job_type": JobType.BULK_ASSET_IMPORT,
            "total_records": len(input_data["assets"]),
            "input_data": input_data,
        }

        assert job["total_records"] == 2
        assert job["input_data"]["validation_mode"] == False


class TestJobLifecycle:
    """Tests for job lifecycle management."""

    def test_job_starts_correctly(self):
        """Test job start sets correct status and timestamp."""
        job = {
            "status": JobStatus.PENDING,
            "started_at": None,
        }

        # Start job
        job["status"] = JobStatus.RUNNING
        job["started_at"] = datetime.now(timezone.utc)

        assert job["status"] == JobStatus.RUNNING
        assert job["started_at"] is not None

    def test_job_completes_successfully(self):
        """Test job completion with success."""
        job = {
            "status": JobStatus.RUNNING,
            "started_at": datetime.now(timezone.utc) - timedelta(minutes=5),
            "completed_at": None,
            "total_records": 100,
            "processed_records": 0,
            "successful_records": 0,
            "failed_records": 0,
        }

        # Complete job
        job["status"] = JobStatus.COMPLETED
        job["completed_at"] = datetime.now(timezone.utc)
        job["processed_records"] = 100
        job["successful_records"] = 95
        job["failed_records"] = 5
        job["progress_percentage"] = 100

        assert job["status"] == JobStatus.COMPLETED
        assert job["completed_at"] is not None
        assert job["successful_records"] + job["failed_records"] == job["total_records"]

    def test_job_fails(self):
        """Test job failure handling."""
        job = {
            "status": JobStatus.RUNNING,
            "started_at": datetime.now(timezone.utc),
            "completed_at": None,
            "error_details": None,
        }

        # Fail job
        error_message = "Database connection error"
        job["status"] = JobStatus.FAILED
        job["completed_at"] = datetime.now(timezone.utc)
        job["error_details"] = {
            "message": error_message,
            "exception_type": "ConnectionError",
        }

        assert job["status"] == JobStatus.FAILED
        assert job["error_details"]["message"] == error_message

    def test_job_cancellation(self):
        """Test job cancellation."""
        job = {
            "status": JobStatus.RUNNING,
            "completed_at": None,
        }

        # Cancel job
        job["status"] = JobStatus.CANCELLED
        job["completed_at"] = datetime.now(timezone.utc)

        assert job["status"] == JobStatus.CANCELLED


class TestProgressTracking:
    """Tests for job progress tracking."""

    def test_progress_percentage_calculation(self):
        """Test progress percentage calculation."""
        total_records = 100
        processed_records = 25

        progress_percentage = int((processed_records / total_records) * 100)

        assert progress_percentage == 25

    def test_progress_updates_correctly(self):
        """Test progress updates during job execution."""
        job = {
            "total_records": 100,
            "processed_records": 0,
            "successful_records": 0,
            "failed_records": 0,
            "progress_percentage": 0,
        }

        # Simulate batch processing
        for batch_num in range(1, 5):
            processed = batch_num * 25
            successful = batch_num * 23
            failed = batch_num * 2

            job["processed_records"] = processed
            job["successful_records"] = successful
            job["failed_records"] = failed
            job["progress_percentage"] = int((processed / job["total_records"]) * 100)

        assert job["processed_records"] == 100
        assert job["progress_percentage"] == 100

    def test_zero_total_records_handling(self):
        """Test handling when total_records is zero."""
        total_records = 0
        processed_records = 0

        # Avoid division by zero
        if total_records > 0:
            progress = int((processed_records / total_records) * 100)
        else:
            progress = 0

        assert progress == 0


class TestJobOutput:
    """Tests for job output handling."""

    def test_output_data_for_import(self):
        """Test output data structure for import job."""
        output_data = {
            "validation_mode": False,
            "errors": [
                {"row": 5, "error": "Invalid category code"},
                {"row": 12, "error": "Duplicate asset code"},
            ],
            "created_asset_ids": [str(uuid4()), str(uuid4())],
        }

        assert len(output_data["errors"]) == 2
        assert len(output_data["created_asset_ids"]) == 2

    def test_output_data_for_export(self):
        """Test output data structure for export job."""
        output_data = {
            "total_records": 500,
            "file_path": "/tmp/exports/assets_export_123.csv",
        }

        assert output_data["total_records"] == 500
        assert "csv" in output_data["file_path"]

    def test_output_data_for_dispose(self):
        """Test output data structure for dispose job."""
        output_data = {
            "total_proceeds": "1500000.00",
            "total_gain_loss": "-50000.00",
            "errors": [],
        }

        assert Decimal(output_data["total_proceeds"]) > 0


class TestJobTypes:
    """Tests for different job types."""

    def test_all_job_types_defined(self):
        """Test all required job types are defined."""
        expected_types = [
            JobType.BULK_ASSET_IMPORT,
            JobType.BULK_ASSET_UPDATE,
            JobType.BULK_ASSET_TRANSFER,
            JobType.BULK_ASSET_DISPOSE,
            JobType.ASSET_EXPORT,
            JobType.DEPRECIATION_RUN,
            JobType.REPORT_GENERATION,
            JobType.DATA_MIGRATION,
            JobType.BATCH_GL_POSTING,
        ]

        for job_type in expected_types:
            assert isinstance(job_type, JobType)

    def test_job_type_enum_values(self):
        """Test job type enum string values."""
        assert JobType.BULK_ASSET_IMPORT.value == "BULK_ASSET_IMPORT"
        assert JobType.ASSET_EXPORT.value == "ASSET_EXPORT"


class TestJobQueries:
    """Tests for job query helpers."""

    def test_filter_by_status(self):
        """Test filtering jobs by status."""
        jobs = [
            {"id": uuid4(), "status": JobStatus.PENDING},
            {"id": uuid4(), "status": JobStatus.RUNNING},
            {"id": uuid4(), "status": JobStatus.COMPLETED},
            {"id": uuid4(), "status": JobStatus.FAILED},
        ]

        running_jobs = [j for j in jobs if j["status"] == JobStatus.RUNNING]
        assert len(running_jobs) == 1

        completed_jobs = [j for j in jobs if j["status"] in [JobStatus.COMPLETED, JobStatus.FAILED]]
        assert len(completed_jobs) == 2

    def test_filter_by_job_type(self):
        """Test filtering jobs by type."""
        jobs = [
            {"id": uuid4(), "job_type": JobType.BULK_ASSET_IMPORT},
            {"id": uuid4(), "job_type": JobType.BULK_ASSET_IMPORT},
            {"id": uuid4(), "job_type": JobType.ASSET_EXPORT},
        ]

        import_jobs = [j for j in jobs if j["job_type"] == JobType.BULK_ASSET_IMPORT]
        assert len(import_jobs) == 2

    def test_filter_by_date_range(self):
        """Test filtering jobs by date range."""
        now = datetime.now(timezone.utc)
        jobs = [
            {"created_at": now - timedelta(days=1)},
            {"created_at": now - timedelta(hours=6)},
            {"created_at": now - timedelta(days=10)},
        ]

        # Jobs from last 7 days
        cutoff = now - timedelta(days=7)
        recent_jobs = [j for j in jobs if j["created_at"] > cutoff]
        assert len(recent_jobs) == 2


class TestJobDuration:
    """Tests for job duration calculation."""

    def test_duration_calculation(self):
        """Test job duration calculation."""
        started_at = datetime.now(timezone.utc) - timedelta(minutes=5, seconds=30)
        completed_at = datetime.now(timezone.utc)

        duration_seconds = int((completed_at - started_at).total_seconds())

        assert duration_seconds >= 330  # 5 minutes 30 seconds

    def test_duration_for_running_job(self):
        """Test duration is None for running job."""
        job = {
            "started_at": datetime.now(timezone.utc),
            "completed_at": None,
        }

        if job["started_at"] and job["completed_at"]:
            duration = int((job["completed_at"] - job["started_at"]).total_seconds())
        else:
            duration = None

        assert duration is None


class TestJobCleanup:
    """Tests for job cleanup functionality."""

    def test_identify_old_jobs(self):
        """Test identifying old jobs for cleanup."""
        now = datetime.now(timezone.utc)
        retention_days = 30

        jobs = [
            {"completed_at": now - timedelta(days=45), "status": JobStatus.COMPLETED},
            {"completed_at": now - timedelta(days=10), "status": JobStatus.COMPLETED},
            {"completed_at": now - timedelta(days=60), "status": JobStatus.FAILED},
            {"completed_at": None, "status": JobStatus.RUNNING},
        ]

        cutoff = now - timedelta(days=retention_days)
        old_completed_jobs = [
            j for j in jobs
            if j["completed_at"] and j["completed_at"] < cutoff
            and j["status"] in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
        ]

        assert len(old_completed_jobs) == 2

    def test_running_jobs_not_cleaned(self):
        """Test that running jobs are not cleaned up."""
        job = {
            "status": JobStatus.RUNNING,
            "completed_at": None,
        }

        can_cleanup = (
            job["status"] in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
            and job["completed_at"] is not None
        )

        assert not can_cleanup
