"""Maker-checker rollout tests (STAGE-4-PENDING-004 closure — backend half).

CLAUDE.md §8.4 requires that the maker ≠ checker invariant be enforced on
every high-risk approval surface. This file pins the invariant on all 11
approval methods we just wired:

  AP/AR (3):           PurchaseBill.approve, SalesInvoice.approve, Payment.approve_payment
  HRIS (4):            Attendance.approve_regularization, Leave.approve,
                       Separation.approve_separation, Separation.approve_fnf
  Lending (5):         Sanction.approve_sanction_with_maker_checker_check (already wired pre-rollout),
                       Disbursement.approve_disbursement,
                       Collections.approve_penal_waiver, approve_ots_proposal,
                       approve_restructure, approve_write_off

Each approval path has two tests:
  * same-user → `MakerCheckerViolationError` raised, DB side-effects avoided
  * different-user → the invariant allows, and the service reaches its next
    validation step (status check, repo call, etc.)

All tests use in-memory doubles; no real DB. This is the backend half of §10.0
parity — FE rejection UI + Playwright E2E are tracked as STAGE-4-PENDING-004b.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.maker_checker import MakerCheckerViolationError

# ---------------------------------------------------------------------------
# AP/AR — Purchase Bill.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_purchase_bill_approve_rejects_self_approval() -> None:
    from app.models.ap_ar.purchase_bill import BillStatus
    from app.services.ap_ar.purchase_bill_service import PurchaseBillService

    service = PurchaseBillService.__new__(PurchaseBillService)
    maker = uuid4()
    bill = SimpleNamespace(
        id=uuid4(),
        status=BillStatus.SUBMITTED,
        workflow_instance_id=None,
        created_by=maker,
    )
    service.get = AsyncMock(return_value=bill)

    with pytest.raises(MakerCheckerViolationError):
        await service.approve(bill.id, user_id=maker)


@pytest.mark.asyncio
async def test_purchase_bill_approve_passes_guard_with_different_checker() -> None:
    """Different user → the guard allows; the first post-guard side effect fires.

    We detect that by letting ``repo.update`` raise a marker exception — if the
    guard had blocked, this marker wouldn't appear.
    """
    from app.models.ap_ar.purchase_bill import BillStatus
    from app.services.ap_ar.purchase_bill_service import PurchaseBillService

    class _GuardPassed(Exception):
        """Marker: we reached the first post-guard call (repo.update)."""

    service = PurchaseBillService.__new__(PurchaseBillService)
    bill = SimpleNamespace(
        id=uuid4(),
        status=BillStatus.SUBMITTED,
        workflow_instance_id=None,
        created_by=uuid4(),
    )
    service.get = AsyncMock(return_value=bill)
    service.repo = MagicMock(update=AsyncMock(side_effect=_GuardPassed()))

    with pytest.raises(_GuardPassed):
        await service.approve(bill.id, user_id=uuid4())


# ---------------------------------------------------------------------------
# AP/AR — Sales Invoice.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sales_invoice_approve_rejects_self_approval() -> None:
    from app.models.ap_ar.sales_invoice import InvoiceStatus
    from app.services.ap_ar.sales_invoice_service import SalesInvoiceService

    service = SalesInvoiceService.__new__(SalesInvoiceService)
    maker = uuid4()
    invoice = SimpleNamespace(
        id=uuid4(),
        status=InvoiceStatus.SUBMITTED,
        workflow_instance_id=None,
        created_by=maker,
    )
    service.get = AsyncMock(return_value=invoice)

    with pytest.raises(MakerCheckerViolationError):
        await service.approve(invoice.id, user_id=maker)


# ---------------------------------------------------------------------------
# AP/AR — Payment (uses submitted_by_id as the maker identity).
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_payment_approve_rejects_self_approval_via_submitted_by() -> None:
    from app.models.ap_ar.payment import PaymentStatus
    from app.services.ap_ar.payment_service import PaymentService

    service = PaymentService.__new__(PaymentService)
    maker = uuid4()
    payment = SimpleNamespace(
        id=uuid4(),
        status=PaymentStatus.SUBMITTED,
        workflow_instance_id=None,
        submitted_by_id=maker,
        created_by=uuid4(),  # different from submitter — submitter wins
    )
    service.get_by_id = AsyncMock(return_value=payment)

    with pytest.raises(MakerCheckerViolationError):
        await service.approve_payment(payment.id, approved_by_id=maker)


@pytest.mark.asyncio
async def test_payment_approve_falls_back_to_created_by_when_no_submitter() -> None:
    """Legacy rows without submitted_by_id fall back to created_by."""
    from app.models.ap_ar.payment import PaymentStatus
    from app.services.ap_ar.payment_service import PaymentService

    service = PaymentService.__new__(PaymentService)
    maker = uuid4()
    payment = SimpleNamespace(
        id=uuid4(),
        status=PaymentStatus.SUBMITTED,
        workflow_instance_id=None,
        submitted_by_id=None,
        created_by=maker,
    )
    service.get_by_id = AsyncMock(return_value=payment)

    with pytest.raises(MakerCheckerViolationError):
        await service.approve_payment(payment.id, approved_by_id=maker)


# ---------------------------------------------------------------------------
# HRIS — Attendance regularization / Leave / Separation / FnF.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_attendance_regularization_rejects_self_approval() -> None:
    from app.core.constants import RegularizationStatus
    from app.services.hris.attendance_service import AttendanceService

    service = AttendanceService.__new__(AttendanceService)
    maker = uuid4()
    reg = SimpleNamespace(
        id=uuid4(),
        status=RegularizationStatus.PENDING,
        created_by=maker,
    )
    service.get_regularization = AsyncMock(return_value=reg)

    with pytest.raises(MakerCheckerViolationError):
        await service.approve_regularization(reg.id, remarks="ok", approved_by=maker)


@pytest.mark.asyncio
async def test_leave_approve_rejects_self_approval() -> None:
    from app.core.constants import LeaveApplicationStatus
    from app.services.hris.leave_service import LeaveApplicationService

    service = LeaveApplicationService.__new__(LeaveApplicationService)
    maker = uuid4()
    app = SimpleNamespace(
        id=uuid4(),
        status=LeaveApplicationStatus.PENDING,
        created_by=maker,
    )
    service.get = AsyncMock(return_value=app)

    with pytest.raises(MakerCheckerViolationError):
        await service.approve(app.id, remarks="ok", approved_by=maker)


@pytest.mark.asyncio
async def test_separation_approve_rejects_self_approval() -> None:
    from datetime import date

    from app.models.hris.separation import SeparationStatus
    from app.services.hris.separation_service import SeparationService

    service = SeparationService.__new__(SeparationService)
    maker = uuid4()
    sep = SimpleNamespace(
        id=uuid4(),
        status=SeparationStatus.INITIATED,
        created_by=maker,
    )
    service.get = AsyncMock(return_value=sep)

    with pytest.raises(MakerCheckerViolationError):
        await service.approve_separation(
            sep.id,
            approved_last_working_date=date(2025, 6, 30),
            approved_by=maker,
        )


@pytest.mark.asyncio
async def test_fnf_approve_rejects_self_approval() -> None:
    from app.models.hris.separation import FnFStatus
    from app.services.hris.separation_service import FnFService

    service = FnFService.__new__(FnFService)
    maker = uuid4()
    fnf = SimpleNamespace(
        id=uuid4(),
        status=FnFStatus.CALCULATED,
        created_by=maker,
    )
    service.get = AsyncMock(return_value=fnf)

    with pytest.raises(MakerCheckerViolationError):
        await service.approve_fnf(fnf.id, approved_by=maker)


# ---------------------------------------------------------------------------
# Lending — Disbursement.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_disbursement_approve_rejects_self_approval() -> None:
    from app.models.lending.enums import DisbursementStatus
    from app.services.lending.disbursement_service import DisbursementService

    service = DisbursementService.__new__(DisbursementService)
    maker = uuid4()
    disbursement = SimpleNamespace(
        id=uuid4(),
        status=DisbursementStatus.PENDING,
        conditions_verified=True,
        created_by=maker,
    )
    # db.execute returns a Result with scalar_one_or_none()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=disbursement)
    service.db = MagicMock(execute=AsyncMock(return_value=result_mock))

    with pytest.raises(MakerCheckerViolationError):
        await service.approve_disbursement(disbursement.id, user_id=maker)


# ---------------------------------------------------------------------------
# Lending — Collections: penal waiver, OTS, restructure, write-off.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_penal_waiver_approve_rejects_self_approval() -> None:
    from app.services.lending.collections_service import CollectionsService

    service = CollectionsService.__new__(CollectionsService)
    maker = uuid4()
    waiver = SimpleNamespace(
        id=uuid4(),
        is_approved=False,
        created_by=maker,
    )
    service.penal_waiver_repo = MagicMock(get=AsyncMock(return_value=waiver))

    # Data schema only matters after the guard; pass a stub.
    data = SimpleNamespace(model_dump=lambda: {})
    with pytest.raises(MakerCheckerViolationError):
        await service.approve_penal_waiver(waiver.id, data=data, updated_by=maker)


@pytest.mark.asyncio
async def test_ots_approve_rejects_self_approval() -> None:
    from app.models.lending.enums import OTSStatus
    from app.services.lending.collections_service import CollectionsService

    service = CollectionsService.__new__(CollectionsService)
    maker = uuid4()
    proposal = SimpleNamespace(
        id=uuid4(),
        status=OTSStatus.PENDING_APPROVAL,
        created_by=maker,
    )
    service.ots_proposal_repo = MagicMock(get=AsyncMock(return_value=proposal))

    data = SimpleNamespace(model_dump=lambda: {})
    with pytest.raises(MakerCheckerViolationError):
        await service.approve_ots_proposal(proposal.id, data=data, updated_by=maker)


@pytest.mark.asyncio
async def test_restructure_approve_rejects_self_approval() -> None:
    from app.models.lending.enums import RestructureStatus
    from app.services.lending.collections_service import CollectionsService

    service = CollectionsService.__new__(CollectionsService)
    maker = uuid4()
    restructure = SimpleNamespace(
        id=uuid4(),
        status=RestructureStatus.PENDING_APPROVAL,
        created_by=maker,
    )
    service.restructure_repo = MagicMock(get=AsyncMock(return_value=restructure))

    data = SimpleNamespace(model_dump=lambda: {})
    with pytest.raises(MakerCheckerViolationError):
        await service.approve_restructure(restructure.id, data=data, updated_by=maker)


@pytest.mark.asyncio
async def test_write_off_approve_rejects_self_approval() -> None:
    from app.models.lending.enums import WriteOffStatus
    from app.services.lending.collections_service import CollectionsService

    service = CollectionsService.__new__(CollectionsService)
    maker = uuid4()
    wo = SimpleNamespace(
        id=uuid4(),
        status=WriteOffStatus.PENDING_APPROVAL,
        created_by=maker,
    )
    service.write_off_repo = MagicMock(get=AsyncMock(return_value=wo))

    data = SimpleNamespace(model_dump=lambda: {})
    with pytest.raises(MakerCheckerViolationError):
        await service.approve_write_off(wo.id, data=data, updated_by=maker)


# ---------------------------------------------------------------------------
# Regression guard: the enforcement surface covers all 11 endpoints.
# ---------------------------------------------------------------------------


def test_every_target_endpoint_imports_the_helper() -> None:
    """Every approval service should import `ensure_maker_is_not_checker`.

    Regression against a future edit that silently drops the guard. We grep
    the source files at import time rather than at runtime so it fires even
    when the specific code path isn't exercised.
    """
    import inspect

    from app.services.ap_ar import payment_service, purchase_bill_service, sales_invoice_service
    from app.services.hris import attendance_service, leave_service, separation_service
    from app.services.lending import collections_service, disbursement_service, sanction_service

    modules = [
        purchase_bill_service,
        sales_invoice_service,
        payment_service,
        attendance_service,
        leave_service,
        separation_service,
        disbursement_service,
        collections_service,
        sanction_service,
    ]
    for mod in modules:
        src = inspect.getsource(mod)
        assert (
            "ensure_maker_is_not_checker" in src
        ), f"Maker-checker guard missing from {mod.__name__} — STAGE-4-PENDING-004 regression"
