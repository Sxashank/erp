"""Stress Test API — parametric v1.

Endpoints:
  - GET  /lending/stress-test/scenarios  — list scenario metadata (4 items)
  - POST /lending/stress-test/run        — run one scenario (Idempotency-Key required)
  - POST /lending/stress-test/run-all    — run all 4 scenarios (Idempotency-Key required)

Routes are tenant-scoped via ``get_db_with_tenant`` (CLAUDE.md §3.4) and
gated by ``treasury.stress.run`` / ``treasury.stress.read`` per CLAUDE.md §8.2.

The mutating endpoints carry ``Idempotency-Key`` even though the math is
pure — the API contract stays consistent and the reads are expensive
(CLAUDE.md §6.3).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.core.exceptions import BadRequestException
from app.models.auth.user import User
from app.schemas.lending.stress_test import (
    ScenarioMetadata,
    StressTestRunAllRequest,
    StressTestRunRequest,
    StressTestRunResponse,
)
from app.services.lending.stress_test_service import StressTestService

router = APIRouter()


@router.get(
    "/scenarios",
    response_model=list[ScenarioMetadata],
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def list_stress_scenarios(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> list[ScenarioMetadata]:
    """Return metadata for the four supported stress scenarios."""
    if current_user.organization_id is None:
        raise BadRequestException(
            "Current user has no organization context",
            error_code="MISSING_ORG_CONTEXT",
        )
    service = StressTestService(db)
    return await service.list_scenarios(current_user.organization_id)


@router.post(
    "/run",
    response_model=StressTestRunResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def run_stress_scenario(
    data: StressTestRunRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> StressTestRunResponse:
    """Run a single stress scenario and return its result.

    Requires `Idempotency-Key` (CLAUDE.md §6.3). Pure computation — no DB
    writes — so the call is safely retryable.
    """
    if not idempotency_key:
        raise BadRequestException(
            "Idempotency-Key header is required for this operation",
            error_code="IDEMPOTENCY_KEY_REQUIRED",
        )
    if current_user.organization_id is None:
        raise BadRequestException(
            "Current user has no organization context",
            error_code="MISSING_ORG_CONTEXT",
        )

    service = StressTestService(db)
    result = await service.run_stress(
        current_user.organization_id,
        data.scenario_id,
        data.as_of_date,
    )
    return StressTestRunResponse(
        as_of_date=result.inputs.as_of_date,
        results=[result],
        summary={
            "scenarios_run": 1,
            "status": result.status,
        },
    )


@router.post(
    "/run-all",
    response_model=StressTestRunResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def run_all_stress_scenarios(
    data: StressTestRunAllRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> StressTestRunResponse:
    """Run all four scenarios against a single snapshot.

    Requires `Idempotency-Key` (CLAUDE.md §6.3). Pure computation.
    """
    if not idempotency_key:
        raise BadRequestException(
            "Idempotency-Key header is required for this operation",
            error_code="IDEMPOTENCY_KEY_REQUIRED",
        )
    if current_user.organization_id is None:
        raise BadRequestException(
            "Current user has no organization context",
            error_code="MISSING_ORG_CONTEXT",
        )

    service = StressTestService(db)
    results = await service.run_all_scenarios(
        current_user.organization_id,
        data.as_of_date,
    )

    # Summary — overall status is the worst across all 4
    rank = {"PASS": 0, "WARN": 1, "FAIL": 2}
    overall = "PASS"
    for r in results:
        if rank[r.status] > rank[overall]:
            overall = r.status

    return StressTestRunResponse(
        as_of_date=results[0].inputs.as_of_date if results else data.as_of_date,  # type: ignore[arg-type]
        results=results,
        summary={
            "scenarios_run": len(results),
            "overall_status": overall,
            "fail_count": sum(1 for r in results if r.status == "FAIL"),
            "warn_count": sum(1 for r in results if r.status == "WARN"),
            "pass_count": sum(1 for r in results if r.status == "PASS"),
        },
    )
