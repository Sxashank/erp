"""Lending workflow dispatch tests (STAGE-4-PENDING-010 closure).

Pins the contract between the three lending services (application / sanction /
rating) and ``WorkflowEngine.start_workflow``:

  * Happy path: dispatch succeeds → ``workflow_instance_id`` is stamped on the
    entity; the correct ``WorkflowEntityType`` is passed.
  * Missing-definition path: ``NotFoundException`` from the engine is swallowed
    → submission proceeds, ``workflow_instance_id`` stays None, no exception
    bubbles. This is how fresh deployments survive before seeds land.

The tests are pure AsyncMock — no DB — so they run fast and pin the dispatch
behaviour without the overhead of spinning up Postgres + seed data.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundException
from app.models.workflow.enums import WorkflowEntityType

# ---------------------------------------------------------------------------
# Enum extension — regression if someone drops a lending value.
# ---------------------------------------------------------------------------


def test_workflow_entity_type_contains_lending_values() -> None:
    """Three lending workflows need their own entity types. Regression guard."""
    assert WorkflowEntityType.LOAN_APPLICATION.value == "LOAN_APPLICATION"
    assert WorkflowEntityType.LOAN_SANCTION.value == "LOAN_SANCTION"
    assert WorkflowEntityType.LOAN_RATING.value == "LOAN_RATING"


def test_workflow_entity_type_preserves_finance_values() -> None:
    """Existing finance values must survive the enum extension."""
    for v in ("VOUCHER", "PURCHASE_BILL", "SALES_INVOICE", "PAYMENT", "JOURNAL_ENTRY"):
        assert v in WorkflowEntityType.__members__


# ---------------------------------------------------------------------------
# ApplicationService.submit_application — happy + graceful-skip.
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_application() -> SimpleNamespace:
    """Minimal LoanApplication stand-in."""
    return SimpleNamespace(
        id=uuid4(),
        organization_id=uuid4(),
        application_number="APP/2025/00001",
        requested_amount=Decimal("5000000"),
        status=None,  # will be set by submit
        stage=None,
        submitted_at=None,
        updated_by=None,
        workflow_instance_id=None,
    )


@pytest.mark.asyncio
async def test_application_submit_dispatches_loan_application_workflow(
    fake_application,
) -> None:
    from app.models.lending.enums import ApplicationStatus
    from app.services.lending.application_service import ApplicationService

    service = ApplicationService(session=AsyncMock())
    fake_application.status = ApplicationStatus.DRAFT
    service.app_repo = MagicMock(get=AsyncMock(return_value=fake_application))
    service.session.commit = AsyncMock()
    service.session.refresh = AsyncMock()

    wf_instance = SimpleNamespace(id=uuid4())
    with patch(
        "app.services.workflow.workflow_engine.WorkflowEngine.start_workflow",
        new=AsyncMock(return_value=wf_instance),
    ) as mock_start:
        await service.submit_application(fake_application.id, submitted_by=uuid4())

    assert mock_start.called
    assert mock_start.call_args.kwargs["entity_type"] is WorkflowEntityType.LOAN_APPLICATION
    assert fake_application.workflow_instance_id == wf_instance.id


@pytest.mark.asyncio
async def test_application_submit_survives_missing_workflow_definition(
    fake_application,
) -> None:
    """No seeded definition → NotFoundException is swallowed; submit still succeeds."""
    from app.models.lending.enums import ApplicationStatus
    from app.services.lending.application_service import ApplicationService

    service = ApplicationService(session=AsyncMock())
    fake_application.status = ApplicationStatus.DRAFT
    service.app_repo = MagicMock(get=AsyncMock(return_value=fake_application))
    service.session.commit = AsyncMock()
    service.session.refresh = AsyncMock()

    with patch(
        "app.services.workflow.workflow_engine.WorkflowEngine.start_workflow",
        new=AsyncMock(side_effect=NotFoundException("no def")),
    ):
        result = await service.submit_application(fake_application.id, submitted_by=uuid4())

    assert result.status == ApplicationStatus.SUBMITTED
    assert result.workflow_instance_id is None


# ---------------------------------------------------------------------------
# SanctionService.submit_sanction — happy + graceful-skip.
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_sanction() -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        organization_id=uuid4(),
        sanction_number="SAN/2025/00001",
        sanctioned_amount=Decimal("2500000"),
        status=None,
        updated_by=None,
        workflow_instance_id=None,
    )


@pytest.mark.asyncio
async def test_sanction_submit_dispatches_loan_sanction_workflow(fake_sanction) -> None:
    from app.models.lending.enums import SanctionStatus
    from app.services.lending.sanction_service import SanctionService

    service = SanctionService(session=AsyncMock())
    fake_sanction.status = SanctionStatus.DRAFT
    service.sanction_repo = MagicMock(get=AsyncMock(return_value=fake_sanction))
    service.session.commit = AsyncMock()
    service.session.refresh = AsyncMock()

    wf_instance = SimpleNamespace(id=uuid4())
    with patch(
        "app.services.workflow.workflow_engine.WorkflowEngine.start_workflow",
        new=AsyncMock(return_value=wf_instance),
    ) as mock_start:
        await service.submit_for_approval(fake_sanction.id, submitted_by=uuid4())

    assert mock_start.called
    assert mock_start.call_args.kwargs["entity_type"] is WorkflowEntityType.LOAN_SANCTION
    assert fake_sanction.workflow_instance_id == wf_instance.id


@pytest.mark.asyncio
async def test_sanction_submit_survives_missing_workflow_definition(fake_sanction) -> None:
    from app.models.lending.enums import SanctionStatus
    from app.services.lending.sanction_service import SanctionService

    service = SanctionService(session=AsyncMock())
    fake_sanction.status = SanctionStatus.DRAFT
    service.sanction_repo = MagicMock(get=AsyncMock(return_value=fake_sanction))
    service.session.commit = AsyncMock()
    service.session.refresh = AsyncMock()

    with patch(
        "app.services.workflow.workflow_engine.WorkflowEngine.start_workflow",
        new=AsyncMock(side_effect=NotFoundException("no def")),
    ):
        result = await service.submit_for_approval(fake_sanction.id, submitted_by=uuid4())

    assert result.status == SanctionStatus.PENDING_APPROVAL
    assert result.workflow_instance_id is None


# ---------------------------------------------------------------------------
# RatingService.submit_rating — happy + graceful-skip.
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_rating() -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        organization_id=uuid4(),
        proposed_grade="A+",
        status=None,
        updated_by=None,
        workflow_instance_id=None,
    )


@pytest.mark.asyncio
async def test_rating_submit_dispatches_loan_rating_workflow(fake_rating) -> None:
    from app.models.lending.enums import RatingStatus
    from app.services.lending.rating_service import RatingService

    service = RatingService(session=AsyncMock())
    fake_rating.status = RatingStatus.DRAFT
    service.rating_repo = MagicMock(get=AsyncMock(return_value=fake_rating))
    service.session.commit = AsyncMock()
    service.session.refresh = AsyncMock()

    wf_instance = SimpleNamespace(id=uuid4())
    with patch(
        "app.services.workflow.workflow_engine.WorkflowEngine.start_workflow",
        new=AsyncMock(return_value=wf_instance),
    ) as mock_start:
        await service.submit_rating_for_approval(fake_rating.id, submitted_by=uuid4())

    assert mock_start.called
    assert mock_start.call_args.kwargs["entity_type"] is WorkflowEntityType.LOAN_RATING
    assert fake_rating.workflow_instance_id == wf_instance.id


@pytest.mark.asyncio
async def test_rating_submit_survives_missing_workflow_definition(fake_rating) -> None:
    from app.models.lending.enums import RatingStatus
    from app.services.lending.rating_service import RatingService

    service = RatingService(session=AsyncMock())
    fake_rating.status = RatingStatus.DRAFT
    service.rating_repo = MagicMock(get=AsyncMock(return_value=fake_rating))
    service.session.commit = AsyncMock()
    service.session.refresh = AsyncMock()

    with patch(
        "app.services.workflow.workflow_engine.WorkflowEngine.start_workflow",
        new=AsyncMock(side_effect=NotFoundException("no def")),
    ):
        result = await service.submit_rating_for_approval(fake_rating.id, submitted_by=uuid4())

    assert result.status == RatingStatus.PENDING_APPROVAL
    assert result.workflow_instance_id is None
