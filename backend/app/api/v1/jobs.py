"""Background Jobs API endpoints."""

from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, BackgroundTasks, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.common.background_job import JobStatus, JobType
from app.services.common.job_service import JobService
from app.workers.fa_worker import dispatch_job

from app.api.deps import get_db_with_tenant
from app.core.exceptions import BadRequestException, NotFoundException
router = APIRouter(prefix="/jobs", tags=["Background Jobs"])


# Schemas
class JobCreateRequest(BaseModel):
    """Request to create a background job."""

    job_type: JobType
    job_name: str = Field(..., max_length=200)
    job_description: Optional[str] = None
    total_records: int = 0
    input_data: Optional[dict] = None


class JobStatusResponse(BaseModel):
    """Job status response."""

    id: str
    job_type: str
    job_name: str
    status: str
    total_records: int
    processed_records: int
    successful_records: int
    failed_records: int
    progress_percentage: int
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[int] = None
    error_details: Optional[dict] = None
    result_file_path: Optional[str] = None


class JobListResponse(BaseModel):
    """Job list response."""

    jobs: List[JobStatusResponse]
    total: int


# Dependencies
def get_job_service(
    session: Annotated[AsyncSession, Depends(get_db_with_tenant)],
) -> JobService:
    return JobService(session)


# Endpoints
@router.post(
    "",
    response_model=JobStatusResponse, response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Create and start a background job",
)
async def create_job(
    request: JobCreateRequest,
    organization_id: UUID,
    user_id: UUID,
    background_tasks: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(get_db_with_tenant)],
    job_service: Annotated[JobService, Depends(get_job_service)],
):
    """Create a new background job and start processing."""
    # Create job record
    job = await job_service.create_job(
        organization_id=organization_id,
        job_type=request.job_type,
        job_name=request.job_name,
        job_description=request.job_description,
        total_records=request.total_records,
        input_data=request.input_data,
        created_by=user_id,
    )

    # Schedule job execution in background
    background_tasks.add_task(dispatch_job, job.id, session)

    # Return job status
    status_data = await job_service.get_job_status(job.id)
    return JobStatusResponse(**status_data)


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse, response_model_by_alias=True,
    summary="Get job status",
)
async def get_job_status(
    job_id: UUID,
    job_service: Annotated[JobService, Depends(get_job_service)],
):
    """Get current status of a background job."""
    status_data = await job_service.get_job_status(job_id)
    if not status_data:
        raise NotFoundException(detail=f"Job {job_id} not found", error_code="JOB_NOT_FOUND")
    return JobStatusResponse(**status_data)


@router.get(
    "",
    response_model=JobListResponse, response_model_by_alias=True,
    summary="List background jobs",
)
async def list_jobs(
    organization_id: UUID,
    job_service: Annotated[JobService, Depends(get_job_service)],
    job_type: Optional[JobType] = None,
    status_filter: Optional[JobStatus] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List background jobs with optional filters."""
    jobs = await job_service.list_jobs(
        organization_id=organization_id,
        job_type=job_type,
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    job_statuses = []
    for job in jobs:
        status_data = await job_service.get_job_status(job.id)
        if status_data:
            job_statuses.append(JobStatusResponse(**status_data))

    return JobListResponse(jobs=job_statuses, total=len(job_statuses))


@router.post(
    "/{job_id}/cancel",
    response_model=JobStatusResponse, response_model_by_alias=True,
    summary="Cancel a running job",
)
async def cancel_job(
    job_id: UUID,
    job_service: Annotated[JobService, Depends(get_job_service)],
):
    """Cancel a pending or running job."""
    try:
        job = await job_service.cancel_job(job_id)
        status_data = await job_service.get_job_status(job.id)
        return JobStatusResponse(**status_data)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.delete(
    "/cleanup",
    status_code=status.HTTP_200_OK,
    summary="Clean up old completed jobs",
)
async def cleanup_jobs(
    organization_id: UUID,
    job_service: Annotated[JobService, Depends(get_job_service)],
    days_to_keep: int = 30,
):
    """Delete completed jobs older than specified days."""
    deleted_count = await job_service.cleanup_old_jobs(
        organization_id=organization_id,
        days_to_keep=days_to_keep,
    )
    return {"deleted_count": deleted_count}
