"""Bulk Operations API endpoints for Fixed Assets."""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, BackgroundTasks, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.fixed_assets.bulk_operations import (
    BulkAssetImportRequest,
    BulkAssetImportResponse,
    BulkAssetUpdateRequest,
    BulkAssetUpdateResponse,
    BulkTransferRequest,
    BulkTransferResponse,
    BulkDisposeRequest,
    BulkDisposeResponse,
    ExportFilters,
)
from app.services.fixed_assets.bulk_operations_service import BulkOperationsService
from app.services.common.job_service import JobService
from app.models.common.background_job import JobType
from app.workers.fa_worker import dispatch_job

import csv
import io
from datetime import date

router = APIRouter(prefix="/bulk", tags=["FA Bulk Operations"])

# Threshold for background processing
BACKGROUND_THRESHOLD = 100


class BackgroundJobResponse(BaseModel):
    """Response for background job submission."""

    job_id: str
    message: str = "Job submitted for background processing"
    status_url: str


def get_bulk_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> BulkOperationsService:
    """Get bulk operations service instance."""
    return BulkOperationsService(session)


def get_job_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> JobService:
    """Get job service instance."""
    return JobService(session)


@router.post(
    "/import",
    response_model=BulkAssetImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk import assets",
)
async def bulk_import_assets(
    data: BulkAssetImportRequest,
    service: Annotated[BulkOperationsService, Depends(get_bulk_service)],
    # current_user: Annotated[User, Depends(get_current_user)],
) -> BulkAssetImportResponse:
    """
    Import multiple assets in bulk.

    - Maximum 500 assets per request
    - Set `validation_only=true` to validate without creating
    - Returns detailed error report for failed rows
    - For >100 records, use /import/async endpoint for background processing
    """
    # Replace with current_user.id when auth is integrated
    created_by = UUID("00000000-0000-0000-0000-000000000000")

    return await service.bulk_import(data, created_by)


@router.post(
    "/import/async",
    response_model=BackgroundJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Bulk import assets (background)",
)
async def bulk_import_assets_async(
    data: BulkAssetImportRequest,
    background_tasks: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(get_db)],
    job_service: Annotated[JobService, Depends(get_job_service)],
    # current_user: Annotated[User, Depends(get_current_user)],
) -> BackgroundJobResponse:
    """
    Import multiple assets in background.

    - For large imports (>100 records)
    - Returns job ID for status polling
    - Use GET /api/v1/jobs/{job_id} to check status
    """
    created_by = UUID("00000000-0000-0000-0000-000000000000")

    # Create background job
    job = await job_service.create_job(
        organization_id=data.organization_id,
        job_type=JobType.BULK_ASSET_IMPORT,
        job_name=f"Bulk Import - {len(data.assets)} assets",
        total_records=len(data.assets),
        input_data={
            "assets": [asset.model_dump(mode="json") for asset in data.assets],
            "validation_mode": data.validation_only,
        },
        created_by=created_by,
    )

    # Schedule background processing
    background_tasks.add_task(dispatch_job, job.id, session)

    return BackgroundJobResponse(
        job_id=str(job.id),
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.put(
    "/update",
    response_model=BulkAssetUpdateResponse,
    summary="Bulk update assets",
)
async def bulk_update_assets(
    data: BulkAssetUpdateRequest,
    service: Annotated[BulkOperationsService, Depends(get_bulk_service)],
    # current_user: Annotated[User, Depends(get_current_user)],
) -> BulkAssetUpdateResponse:
    """
    Update multiple assets in bulk.

    - Maximum 200 assets per request
    - Each row must include current `version` for optimistic locking
    - Only non-financial fields can be updated
    """
    updated_by = UUID("00000000-0000-0000-0000-000000000000")

    return await service.bulk_update(data, updated_by)


@router.post(
    "/transfer",
    response_model=BulkTransferResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk transfer assets",
)
async def bulk_transfer_assets(
    data: BulkTransferRequest,
    service: Annotated[BulkOperationsService, Depends(get_bulk_service)],
    # current_user: Annotated[User, Depends(get_current_user)],
) -> BulkTransferResponse:
    """
    Initiate bulk asset transfers.

    - Creates pending transfer requests for all assets
    - Transfers still require approval based on workflow settings
    - Maximum 200 assets per request
    - For >100 records, use /transfer/async endpoint for background processing
    """
    transferred_by = UUID("00000000-0000-0000-0000-000000000000")

    return await service.bulk_transfer(data, transferred_by)


@router.post(
    "/transfer/async",
    response_model=BackgroundJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Bulk transfer assets (background)",
)
async def bulk_transfer_assets_async(
    data: BulkTransferRequest,
    background_tasks: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(get_db)],
    job_service: Annotated[JobService, Depends(get_job_service)],
    # current_user: Annotated[User, Depends(get_current_user)],
) -> BackgroundJobResponse:
    """
    Bulk transfer assets in background.

    - For large transfers (>100 records)
    - Returns job ID for status polling
    """
    created_by = UUID("00000000-0000-0000-0000-000000000000")

    # Create background job
    job = await job_service.create_job(
        organization_id=data.organization_id,
        job_type=JobType.BULK_ASSET_TRANSFER,
        job_name=f"Bulk Transfer - {len(data.transfers)} assets",
        total_records=len(data.transfers),
        input_data={
            "transfers": [t.model_dump(mode="json") for t in data.transfers],
        },
        created_by=created_by,
    )

    # Schedule background processing
    background_tasks.add_task(dispatch_job, job.id, session)

    return BackgroundJobResponse(
        job_id=str(job.id),
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post(
    "/dispose",
    response_model=BulkDisposeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk dispose assets",
)
async def bulk_dispose_assets(
    data: BulkDisposeRequest,
    service: Annotated[BulkOperationsService, Depends(get_bulk_service)],
    # current_user: Annotated[User, Depends(get_current_user)],
) -> BulkDisposeResponse:
    """
    Dispose multiple assets in bulk.

    - Calculates gain/loss for each asset
    - Creates GL entries for disposals
    - Maximum 200 assets per request
    - For >100 records, use /dispose/async endpoint for background processing
    """
    disposed_by = UUID("00000000-0000-0000-0000-000000000000")

    return await service.bulk_dispose(data, disposed_by)


@router.post(
    "/dispose/async",
    response_model=BackgroundJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Bulk dispose assets (background)",
)
async def bulk_dispose_assets_async(
    data: BulkDisposeRequest,
    background_tasks: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(get_db)],
    job_service: Annotated[JobService, Depends(get_job_service)],
    # current_user: Annotated[User, Depends(get_current_user)],
) -> BackgroundJobResponse:
    """
    Bulk dispose assets in background.

    - For large disposals (>100 records)
    - Returns job ID for status polling
    """
    created_by = UUID("00000000-0000-0000-0000-000000000000")

    # Create background job
    job = await job_service.create_job(
        organization_id=data.organization_id,
        job_type=JobType.BULK_ASSET_DISPOSE,
        job_name=f"Bulk Dispose - {len(data.disposals)} assets",
        total_records=len(data.disposals),
        input_data={
            "disposals": [d.model_dump(mode="json") for d in data.disposals],
        },
        created_by=created_by,
    )

    # Schedule background processing
    background_tasks.add_task(dispatch_job, job.id, session)

    return BackgroundJobResponse(
        job_id=str(job.id),
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.get(
    "/export",
    summary="Export assets to CSV",
)
async def export_assets(
    organization_id: UUID,
    service: Annotated[BulkOperationsService, Depends(get_bulk_service)],
    category_id: UUID = Query(None, description="Filter by category"),
    location_id: UUID = Query(None, description="Filter by location"),
    department_id: UUID = Query(None, description="Filter by department"),
    status: str = Query(None, description="Filter by status"),
    acquisition_date_from: date = Query(None, description="Filter by acquisition date from"),
    acquisition_date_to: date = Query(None, description="Filter by acquisition date to"),
    include_disposed: bool = Query(False, description="Include disposed assets"),
) -> StreamingResponse:
    """
    Export assets to CSV format.

    Returns a downloadable CSV file with all matching assets.
    """
    filters = ExportFilters(
        organization_id=organization_id,
        category_id=category_id,
        location_id=location_id,
        department_id=department_id,
        status=status,
        acquisition_date_from=acquisition_date_from,
        acquisition_date_to=acquisition_date_to,
        include_disposed=include_disposed,
    )

    export_data, total = await service.export_assets(filters)

    # Generate CSV
    output = io.StringIO()
    if export_data:
        writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
        writer.writeheader()
        writer.writerows(export_data)

    output.seek(0)

    # Generate filename with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"fixed_assets_export_{timestamp}.csv"

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Total-Records": str(total),
        },
    )


@router.post(
    "/export/async",
    response_model=BackgroundJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Export assets (background)",
)
async def export_assets_async(
    organization_id: UUID,
    background_tasks: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(get_db)],
    job_service: Annotated[JobService, Depends(get_job_service)],
    category_id: UUID = Query(None, description="Filter by category"),
    status_filter: str = Query(None, description="Filter by status"),
    location: str = Query(None, description="Filter by location"),
    # current_user: Annotated[User, Depends(get_current_user)],
) -> BackgroundJobResponse:
    """
    Export assets to CSV in background.

    - For large exports
    - Returns job ID for status polling
    - Download file from result_file_path after completion
    """
    created_by = UUID("00000000-0000-0000-0000-000000000000")

    # Create background job
    job = await job_service.create_job(
        organization_id=organization_id,
        job_type=JobType.ASSET_EXPORT,
        job_name="Asset Export",
        total_records=0,  # Will be determined during processing
        input_data={
            "filters": {
                "category_id": str(category_id) if category_id else None,
                "status": status_filter,
                "location": location,
            },
        },
        created_by=created_by,
    )

    # Schedule background processing
    background_tasks.add_task(dispatch_job, job.id, session)

    return BackgroundJobResponse(
        job_id=str(job.id),
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post(
    "/validate-import",
    response_model=BulkAssetImportResponse,
    summary="Validate bulk import data",
)
async def validate_bulk_import(
    data: BulkAssetImportRequest,
    service: Annotated[BulkOperationsService, Depends(get_bulk_service)],
) -> BulkAssetImportResponse:
    """
    Validate bulk import data without creating assets.

    Useful for pre-checking data before actual import.
    """
    # Force validation_only mode
    data.validation_only = True

    created_by = UUID("00000000-0000-0000-0000-000000000000")
    return await service.bulk_import(data, created_by)
