"""Fixed Assets background worker for bulk operations."""

import asyncio
import csv
import io
import os
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, List, Optional
from uuid import UUID
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.common.background_job import BackgroundJob, JobType, JobStatus
from app.models.fixed_assets.fixed_asset import FixedAsset
from app.models.fixed_assets.asset_category import AssetCategory
from app.core.constants import (
    AssetStatus,
    AssetAcquisitionType,
    DepreciationMethod,
)
from app.services.common.job_service import BackgroundJobRunner

logger = logging.getLogger(__name__)

# Batch size for processing
BATCH_SIZE = 50


async def process_bulk_asset_import(
    job: BackgroundJob,
    runner: BackgroundJobRunner,
) -> Dict[str, Any]:
    """Process bulk asset import job.

    Expected input_data format:
    {
        "assets": [
            {
                "asset_name": str,
                "category_code": str,
                "acquisition_date": str (YYYY-MM-DD),
                "acquisition_cost": str,
                ...
            }
        ],
        "validation_mode": bool
    }
    """
    from app.database import async_session_maker

    input_data = job.input_data or {}
    assets_data = input_data.get("assets", [])
    validation_mode = input_data.get("validation_mode", False)

    successful = 0
    failed = 0
    errors: List[Dict] = []
    created_ids: List[str] = []

    async with async_session_maker() as session:
        # Get category mapping
        categories = await _get_category_mapping(session, job.organization_id)

        # Process in batches
        for i in range(0, len(assets_data), BATCH_SIZE):
            batch = assets_data[i : i + BATCH_SIZE]

            for idx, asset_row in enumerate(batch):
                row_num = i + idx + 1

                try:
                    # Validate row
                    validated = _validate_asset_row(asset_row, categories, row_num)

                    if not validation_mode:
                        # Create asset
                        asset = FixedAsset(
                            organization_id=job.organization_id,
                            category_id=validated["category_id"],
                            asset_name=validated["asset_name"],
                            asset_code=f"FA/IMP/{datetime.now().year}/{row_num:05d}",
                            acquisition_date=validated["acquisition_date"],
                            acquisition_type=validated.get(
                                "acquisition_type", AssetAcquisitionType.PURCHASE
                            ),
                            acquisition_cost=validated["acquisition_cost"],
                            installation_cost=validated.get(
                                "installation_cost", Decimal("0.00")
                            ),
                            other_costs=validated.get("other_costs", Decimal("0.00")),
                            total_cost=validated["total_cost"],
                            residual_value=validated["residual_value"],
                            depreciable_value=validated["depreciable_value"],
                            useful_life_months=validated["useful_life_months"],
                            depreciation_method=validated["depreciation_method"],
                            depreciation_rate=validated["depreciation_rate"],
                            accumulated_depreciation=Decimal("0.00"),
                            wdv_value=validated["total_cost"],
                            status=AssetStatus.DRAFT,
                            quantity=validated.get("quantity", 1),
                            location=validated.get("location"),
                            serial_number=validated.get("serial_number"),
                            is_active=True,
                            created_by=job.created_by,
                        )
                        session.add(asset)
                        await session.flush()
                        created_ids.append(str(asset.id))

                    successful += 1

                except Exception as e:
                    failed += 1
                    errors.append({
                        "row": row_num,
                        "error": str(e),
                        "data": asset_row,
                    })

            # Update progress
            processed = i + len(batch)
            await runner.update_progress(job.id, processed, successful, failed)

            # Commit batch if not validation mode
            if not validation_mode:
                await session.commit()

            # Small delay to prevent overwhelming the database
            await asyncio.sleep(0.1)

    return {
        "successful": successful,
        "failed": failed,
        "output_data": {
            "validation_mode": validation_mode,
            "errors": errors[:100],  # Limit errors in output
            "created_asset_ids": created_ids if not validation_mode else [],
        },
    }


async def process_bulk_asset_transfer(
    job: BackgroundJob,
    runner: BackgroundJobRunner,
) -> Dict[str, Any]:
    """Process bulk asset transfer job.

    Expected input_data format:
    {
        "transfers": [
            {
                "asset_id": str (UUID),
                "to_location": str,
                "to_department_id": str (UUID, optional),
                "to_custodian_id": str (UUID, optional),
                "transfer_date": str (YYYY-MM-DD),
                "remarks": str (optional)
            }
        ]
    }
    """
    from app.database import async_session_maker

    input_data = job.input_data or {}
    transfers = input_data.get("transfers", [])

    successful = 0
    failed = 0
    errors: List[Dict] = []

    async with async_session_maker() as session:
        for idx, transfer in enumerate(transfers):
            row_num = idx + 1

            try:
                asset_id = UUID(transfer["asset_id"])

                # Get asset
                result = await session.execute(
                    select(FixedAsset).where(
                        FixedAsset.id == asset_id,
                        FixedAsset.organization_id == job.organization_id,
                    )
                )
                asset = result.scalar_one_or_none()

                if not asset:
                    raise ValueError(f"Asset not found: {transfer['asset_id']}")

                if asset.status not in [AssetStatus.ACTIVE, AssetStatus.UNDER_MAINTENANCE]:
                    raise ValueError(f"Asset cannot be transferred in status: {asset.status}")

                # Update asset
                asset.location = transfer.get("to_location", asset.location)
                if transfer.get("to_department_id"):
                    asset.department_id = UUID(transfer["to_department_id"])
                if transfer.get("to_custodian_id"):
                    asset.custodian_id = UUID(transfer["to_custodian_id"])

                asset.updated_by = job.created_by
                asset.updated_at = datetime.now(timezone.utc)

                successful += 1

            except Exception as e:
                failed += 1
                errors.append({
                    "row": row_num,
                    "asset_id": transfer.get("asset_id"),
                    "error": str(e),
                })

            # Update progress periodically
            if (idx + 1) % 10 == 0:
                await runner.update_progress(job.id, idx + 1, successful, failed)

        # Commit all changes
        await session.commit()

    return {
        "successful": successful,
        "failed": failed,
        "output_data": {
            "errors": errors[:100],
        },
    }


async def process_bulk_asset_dispose(
    job: BackgroundJob,
    runner: BackgroundJobRunner,
) -> Dict[str, Any]:
    """Process bulk asset disposal job.

    Expected input_data format:
    {
        "disposals": [
            {
                "asset_id": str (UUID),
                "disposal_type": str,
                "disposal_date": str (YYYY-MM-DD),
                "sale_proceeds": str (optional),
                "remarks": str (optional)
            }
        ]
    }
    """
    from app.database import async_session_maker
    from app.core.constants import DisposalType

    input_data = job.input_data or {}
    disposals = input_data.get("disposals", [])

    successful = 0
    failed = 0
    errors: List[Dict] = []
    total_proceeds = Decimal("0.00")
    total_gain_loss = Decimal("0.00")

    async with async_session_maker() as session:
        for idx, disposal in enumerate(disposals):
            row_num = idx + 1

            try:
                asset_id = UUID(disposal["asset_id"])

                # Get asset
                result = await session.execute(
                    select(FixedAsset).where(
                        FixedAsset.id == asset_id,
                        FixedAsset.organization_id == job.organization_id,
                    )
                )
                asset = result.scalar_one_or_none()

                if not asset:
                    raise ValueError(f"Asset not found: {disposal['asset_id']}")

                if asset.status != AssetStatus.ACTIVE:
                    raise ValueError(f"Asset cannot be disposed in status: {asset.status}")

                # Parse disposal data
                disposal_date = datetime.strptime(
                    disposal["disposal_date"], "%Y-%m-%d"
                ).date()
                disposal_type = DisposalType(disposal["disposal_type"])
                sale_proceeds = Decimal(disposal.get("sale_proceeds", "0.00"))

                # Calculate gain/loss
                book_value = asset.total_cost - asset.accumulated_depreciation
                gain_loss = sale_proceeds - book_value

                # Update asset
                asset.status = AssetStatus.DISPOSED
                asset.disposal_date = disposal_date
                asset.disposal_type = disposal_type
                asset.disposal_proceeds = sale_proceeds
                asset.disposal_remarks = disposal.get("remarks")
                asset.updated_by = job.created_by
                asset.updated_at = datetime.now(timezone.utc)

                total_proceeds += sale_proceeds
                total_gain_loss += gain_loss
                successful += 1

            except Exception as e:
                failed += 1
                errors.append({
                    "row": row_num,
                    "asset_id": disposal.get("asset_id"),
                    "error": str(e),
                })

            # Update progress periodically
            if (idx + 1) % 10 == 0:
                await runner.update_progress(job.id, idx + 1, successful, failed)

        # Commit all changes
        await session.commit()

    return {
        "successful": successful,
        "failed": failed,
        "output_data": {
            "total_proceeds": str(total_proceeds),
            "total_gain_loss": str(total_gain_loss),
            "errors": errors[:100],
        },
    }


async def process_asset_export(
    job: BackgroundJob,
    runner: BackgroundJobRunner,
) -> Dict[str, Any]:
    """Process asset export job.

    Expected input_data format:
    {
        "filters": {
            "status": str (optional),
            "category_id": str (optional),
            "location": str (optional)
        },
        "columns": [str] (optional)
    }
    """
    from app.database import async_session_maker

    input_data = job.input_data or {}
    filters = input_data.get("filters", {})

    # Default columns
    columns = input_data.get("columns", [
        "asset_code",
        "asset_name",
        "category_code",
        "acquisition_date",
        "total_cost",
        "accumulated_depreciation",
        "wdv_value",
        "status",
        "location",
    ])

    async with async_session_maker() as session:
        # Build query
        query = select(FixedAsset).where(
            FixedAsset.organization_id == job.organization_id,
            FixedAsset.is_active == True,
        )

        if filters.get("status"):
            query = query.where(FixedAsset.status == AssetStatus(filters["status"]))
        if filters.get("category_id"):
            query = query.where(FixedAsset.category_id == UUID(filters["category_id"]))
        if filters.get("location"):
            query = query.where(FixedAsset.location == filters["location"])

        result = await session.execute(query)
        assets = result.scalars().all()

        # Generate CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()

        for idx, asset in enumerate(assets):
            row = {}
            for col in columns:
                value = getattr(asset, col, None)
                if isinstance(value, Decimal):
                    value = str(value)
                elif isinstance(value, date):
                    value = value.isoformat()
                elif hasattr(value, "value"):
                    value = value.value
                row[col] = value
            writer.writerow(row)

            # Update progress periodically
            if (idx + 1) % 100 == 0:
                await runner.update_progress(job.id, idx + 1, idx + 1, 0)

        # Save to file
        export_dir = os.environ.get("EXPORT_DIR", "/tmp/exports")
        os.makedirs(export_dir, exist_ok=True)

        filename = f"assets_export_{job.id}.csv"
        filepath = os.path.join(export_dir, filename)

        with open(filepath, "w", newline="") as f:
            f.write(output.getvalue())

    return {
        "successful": len(assets),
        "failed": 0,
        "result_file": filepath,
        "output_data": {
            "total_records": len(assets),
            "file_path": filepath,
        },
    }


async def _get_category_mapping(
    session: AsyncSession,
    organization_id: UUID,
) -> Dict[str, AssetCategory]:
    """Get category mapping by code."""
    result = await session.execute(
        select(AssetCategory).where(
            AssetCategory.organization_id == organization_id,
            AssetCategory.is_active == True,
        )
    )
    categories = result.scalars().all()
    return {cat.category_code: cat for cat in categories}


def _validate_asset_row(
    row: Dict[str, Any],
    categories: Dict[str, AssetCategory],
    row_num: int,
) -> Dict[str, Any]:
    """Validate and transform asset row data."""
    errors = []

    # Required fields
    if not row.get("asset_name"):
        errors.append("asset_name is required")

    if not row.get("category_code"):
        errors.append("category_code is required")
    elif row["category_code"] not in categories:
        errors.append(f"Invalid category_code: {row['category_code']}")

    if not row.get("acquisition_date"):
        errors.append("acquisition_date is required")

    if not row.get("acquisition_cost"):
        errors.append("acquisition_cost is required")

    if errors:
        raise ValueError(f"Row {row_num}: {'; '.join(errors)}")

    # Get category
    category = categories[row["category_code"]]

    # Parse values
    try:
        acquisition_date = datetime.strptime(
            row["acquisition_date"], "%Y-%m-%d"
        ).date()
    except ValueError:
        raise ValueError(f"Row {row_num}: Invalid date format for acquisition_date")

    try:
        acquisition_cost = Decimal(str(row["acquisition_cost"]))
        installation_cost = Decimal(str(row.get("installation_cost", "0")))
        other_costs = Decimal(str(row.get("other_costs", "0")))
    except InvalidOperation:
        raise ValueError(f"Row {row_num}: Invalid numeric value")

    total_cost = acquisition_cost + installation_cost + other_costs

    # Calculate derived values from category
    residual_pct = category.residual_value_pct or Decimal("0.00")
    residual_value = total_cost * residual_pct / 100
    depreciable_value = total_cost - residual_value

    return {
        "asset_name": row["asset_name"],
        "category_id": category.id,
        "acquisition_date": acquisition_date,
        "acquisition_cost": acquisition_cost,
        "installation_cost": installation_cost,
        "other_costs": other_costs,
        "total_cost": total_cost,
        "residual_value": residual_value,
        "depreciable_value": depreciable_value,
        "useful_life_months": category.useful_life_years * 12,
        "depreciation_method": category.depreciation_method,
        "depreciation_rate": (
            category.depreciation_rate_slm
            if category.depreciation_method == DepreciationMethod.SLM
            else category.depreciation_rate_wdv
        ),
        "location": row.get("location"),
        "serial_number": row.get("serial_number"),
        "quantity": int(row.get("quantity", 1)),
    }


# Job type to handler mapping
JOB_HANDLERS = {
    JobType.BULK_ASSET_IMPORT: process_bulk_asset_import,
    JobType.BULK_ASSET_TRANSFER: process_bulk_asset_transfer,
    JobType.BULK_ASSET_DISPOSE: process_bulk_asset_dispose,
    JobType.ASSET_EXPORT: process_asset_export,
}


async def dispatch_job(
    job_id: UUID,
    session: AsyncSession,
) -> None:
    """Dispatch job to appropriate handler."""
    from app.services.common.job_service import JobService, BackgroundJobRunner

    job_service = JobService(session)
    runner = BackgroundJobRunner(session, job_service)

    job = await job_service.get_job(job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")

    handler = JOB_HANDLERS.get(job.job_type)
    if not handler:
        raise ValueError(f"No handler for job type {job.job_type}")

    await runner.run_job(job_id, handler)
