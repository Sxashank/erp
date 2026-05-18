"""Background Job Service for managing async tasks."""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Callable, Awaitable
from uuid import UUID
import logging

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.common.background_job import BackgroundJob, JobStatus, JobType

logger = logging.getLogger(__name__)


class JobService:
    """Service for managing background jobs."""

    def __init__(self, session: AsyncSession):
        """Initialize job service."""
        self.session = session

    async def create_job(
        self,
        organization_id: UUID,
        job_type: JobType,
        job_name: str,
        created_by: UUID,
        total_records: int = 0,
        input_data: Optional[Dict[str, Any]] = None,
        job_description: Optional[str] = None,
    ) -> BackgroundJob:
        """Create a new background job record."""
        job = BackgroundJob(
            organization_id=organization_id,
            job_type=job_type,
            job_name=job_name,
            job_description=job_description,
            status=JobStatus.PENDING,
            total_records=total_records,
            input_data=input_data,
            created_by=created_by,
        )

        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job)

        logger.info(f"Created background job {job.id} of type {job_type}")
        return job

    async def get_job(self, job_id: UUID) -> Optional[BackgroundJob]:
        """Get job by ID."""
        result = await self.session.execute(
            select(BackgroundJob).where(BackgroundJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_job_status(self, job_id: UUID) -> Optional[Dict[str, Any]]:
        """Get job status summary."""
        job = await self.get_job(job_id)
        if not job:
            return None

        return {
            "id": str(job.id),
            "job_type": job.job_type.value,
            "job_name": job.job_name,
            "status": job.status.value,
            "total_records": job.total_records,
            "processed_records": job.processed_records,
            "successful_records": job.successful_records,
            "failed_records": job.failed_records,
            "progress_percentage": job.progress_percentage,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "duration_seconds": job.duration_seconds,
            "error_details": job.error_details,
            "result_file_path": job.result_file_path,
        }

    async def list_jobs(
        self,
        organization_id: UUID,
        job_type: Optional[JobType] = None,
        status: Optional[JobStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[BackgroundJob]:
        """List jobs with filters."""
        query = select(BackgroundJob).where(
            BackgroundJob.organization_id == organization_id
        )

        if job_type:
            query = query.where(BackgroundJob.job_type == job_type)
        if status:
            query = query.where(BackgroundJob.status == status)

        query = query.order_by(BackgroundJob.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def start_job(self, job_id: UUID) -> BackgroundJob:
        """Mark job as started."""
        job = await self.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.start()
        await self.session.flush()
        await self.session.refresh(job)

        logger.info(f"Started job {job_id}")
        return job

    async def update_job_progress(
        self,
        job_id: UUID,
        processed: int,
        successful: int,
        failed: int,
    ) -> None:
        """Update job progress."""
        await self.session.execute(
            update(BackgroundJob)
            .where(BackgroundJob.id == job_id)
            .values(
                processed_records=processed,
                successful_records=successful,
                failed_records=failed,
                progress_percentage=(
                    processed * 100 // BackgroundJob.total_records
                    if BackgroundJob.total_records > 0
                    else 0
                ),
            )
        )
        await self.session.flush()

    async def complete_job(
        self,
        job_id: UUID,
        successful: int,
        failed: int,
        output_data: Optional[Dict] = None,
        result_file: Optional[str] = None,
    ) -> BackgroundJob:
        """Mark job as completed."""
        job = await self.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.complete(
            successful=successful,
            failed=failed,
            output_data=output_data,
            result_file=result_file,
        )
        await self.session.flush()
        await self.session.refresh(job)

        logger.info(
            f"Completed job {job_id}: {successful} successful, {failed} failed"
        )
        return job

    async def fail_job(
        self,
        job_id: UUID,
        error_message: str,
        error_details: Optional[Dict] = None,
    ) -> BackgroundJob:
        """Mark job as failed."""
        job = await self.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.fail(error_message, error_details)
        await self.session.flush()
        await self.session.refresh(job)

        logger.error(f"Failed job {job_id}: {error_message}")
        return job

    async def cancel_job(self, job_id: UUID) -> BackgroundJob:
        """Cancel a pending or running job."""
        job = await self.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
            raise ValueError(f"Cannot cancel job in status {job.status}")

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(job)

        logger.info(f"Cancelled job {job_id}")
        return job

    async def cleanup_old_jobs(
        self,
        organization_id: UUID,
        days_to_keep: int = 30,
    ) -> int:
        """Delete completed jobs older than specified days."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

        from sqlalchemy import delete

        result = await self.session.execute(
            delete(BackgroundJob).where(
                and_(
                    BackgroundJob.organization_id == organization_id,
                    BackgroundJob.status.in_([
                        JobStatus.COMPLETED,
                        JobStatus.FAILED,
                        JobStatus.CANCELLED,
                    ]),
                    BackgroundJob.completed_at < cutoff_date,
                )
            )
        )
        await self.session.flush()

        deleted_count = result.rowcount
        logger.info(f"Cleaned up {deleted_count} old jobs for org {organization_id}")
        return deleted_count


class BackgroundJobRunner:
    """Runner for executing background jobs with progress tracking."""

    def __init__(self, session: AsyncSession, job_service: JobService):
        """Initialize job runner."""
        self.session = session
        self.job_service = job_service
        self._running_jobs: Dict[UUID, asyncio.Task] = {}

    async def run_job(
        self,
        job_id: UUID,
        task_fn: Callable[[BackgroundJob, "BackgroundJobRunner"], Awaitable[Dict[str, Any]]],
    ) -> None:
        """Run a job asynchronously."""
        job = await self.job_service.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Create task
        task = asyncio.create_task(self._execute_job(job, task_fn))
        self._running_jobs[job_id] = task

    async def _execute_job(
        self,
        job: BackgroundJob,
        task_fn: Callable[[BackgroundJob, "BackgroundJobRunner"], Awaitable[Dict[str, Any]]],
    ) -> None:
        """Execute the job function."""
        try:
            # Start job
            await self.job_service.start_job(job.id)

            # Execute
            result = await task_fn(job, self)

            # Complete
            await self.job_service.complete_job(
                job_id=job.id,
                successful=result.get("successful", 0),
                failed=result.get("failed", 0),
                output_data=result.get("output_data"),
                result_file=result.get("result_file"),
            )

        except Exception as e:
            logger.exception(f"Job {job.id} failed with error")
            await self.job_service.fail_job(
                job_id=job.id,
                error_message=str(e),
                error_details={"exception_type": type(e).__name__},
            )

        finally:
            # Remove from running jobs
            self._running_jobs.pop(job.id, None)

    async def update_progress(
        self,
        job_id: UUID,
        processed: int,
        successful: int,
        failed: int,
    ) -> None:
        """Update job progress (called from task function)."""
        await self.job_service.update_job_progress(
            job_id=job_id,
            processed=processed,
            successful=successful,
            failed=failed,
        )

    def is_running(self, job_id: UUID) -> bool:
        """Check if job is currently running."""
        return job_id in self._running_jobs

    async def cancel(self, job_id: UUID) -> bool:
        """Cancel a running job."""
        if job_id not in self._running_jobs:
            return False

        task = self._running_jobs[job_id]
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        await self.job_service.cancel_job(job_id)
        return True
