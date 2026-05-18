"""Accounting bridge tests for LMS money movements."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.constants import GLEntrySourceType
from app.services.lending.disbursement_service import DisbursementService
from app.services.lending.receipt_service import ReceiptService


def _service_with_gl(service_cls):
    service = service_cls.__new__(service_cls)
    service.fy_repo = SimpleNamespace(
        get_by_date=AsyncMock(return_value=SimpleNamespace(id=uuid4()))
    )
    service.period_repo = SimpleNamespace(
        get_by_date=AsyncMock(return_value=SimpleNamespace(id=uuid4()))
    )
    service.gl_posting_service = SimpleNamespace(post_entries=AsyncMock())
    service.gl_posting_service.post_entries.return_value = [
        SimpleNamespace(voucher_id=uuid4())
    ]
    return service


@pytest.mark.asyncio
async def test_lms_disbursement_posts_balanced_gl_entries() -> None:
    service = _service_with_gl(DisbursementService)
    org_id = uuid4()
    source_account_id = uuid4()
    loan_asset_account_id = uuid4()
    charges_income_account_id = uuid4()
    user_id = uuid4()
    disbursement = SimpleNamespace(
        id=uuid4(),
        voucher_id=None,
        disbursement_reference="LN-001/D001",
        disbursement_date=date(2026, 5, 18),
        disbursed_amount=Decimal("100000.00"),
        net_disbursement=Decimal("99000.00"),
        disbursement_charges=Decimal("1000.00"),
    )
    loan = SimpleNamespace(
        organization_id=org_id,
        loan_account_number="LN-001",
        loan_asset_account_id=loan_asset_account_id,
        charges_income_account_id=charges_income_account_id,
    )

    await service._post_disbursement_to_gl(
        disbursement=disbursement,
        loan=loan,
        source_account_id=source_account_id,
        posted_by=user_id,
    )

    kwargs = service.gl_posting_service.post_entries.await_args.kwargs
    assert kwargs["source_type"] == GLEntrySourceType.LOAN_DISBURSEMENT
    assert kwargs["source_id"] == disbursement.id
    assert kwargs["organization_id"] == org_id
    assert sum(line["debit_amount"] for line in kwargs["lines"]) == Decimal("100000.00")
    assert sum(line["credit_amount"] for line in kwargs["lines"]) == Decimal("100000.00")
    assert kwargs["lines"][0]["account_id"] == loan_asset_account_id
    assert kwargs["lines"][1]["account_id"] == source_account_id
    assert kwargs["lines"][2]["account_id"] == charges_income_account_id


@pytest.mark.asyncio
async def test_lms_receipt_creation_posts_cash_to_suspense() -> None:
    service = _service_with_gl(ReceiptService)
    org_id = uuid4()
    receipt_account_id = uuid4()
    suspense_account_id = uuid4()
    receipt = SimpleNamespace(
        id=uuid4(),
        voucher_id=None,
        receipt_number="RCP-001",
        value_date=date(2026, 5, 18),
        receipt_amount=Decimal("25000.00"),
        receipt_account_id=receipt_account_id,
        receipt_suspense_account_id=suspense_account_id,
    )
    loan = SimpleNamespace(organization_id=org_id, loan_account_number="LN-001")

    await service._post_receipt_cash_to_gl(
        receipt=receipt,
        loan=loan,
        posted_by=uuid4(),
    )

    kwargs = service.gl_posting_service.post_entries.await_args.kwargs
    assert kwargs["source_type"] == GLEntrySourceType.LOAN_RECEIPT
    assert kwargs["source_reference"] == "RCP-001/CASH"
    assert sum(line["debit_amount"] for line in kwargs["lines"]) == Decimal("25000.00")
    assert sum(line["credit_amount"] for line in kwargs["lines"]) == Decimal("25000.00")
    assert kwargs["lines"][0]["account_id"] == receipt_account_id
    assert kwargs["lines"][1]["account_id"] == suspense_account_id


@pytest.mark.asyncio
async def test_lms_receipt_allocation_posts_component_deltas() -> None:
    service = _service_with_gl(ReceiptService)
    org_id = uuid4()
    suspense_account_id = uuid4()
    loan_asset_account_id = uuid4()
    interest_receivable_account_id = uuid4()
    penal_income_account_id = uuid4()
    charges_income_account_id = uuid4()
    receipt = SimpleNamespace(
        id=uuid4(),
        receipt_number="RCP-002",
        value_date=date(2026, 5, 18),
        receipt_suspense_account_id=suspense_account_id,
        allocated_amount=Decimal("15000.00"),
        principal_allocated=Decimal("10000.00"),
        interest_allocated=Decimal("4000.00"),
        penal_interest_allocated=Decimal("750.00"),
        charges_allocated=Decimal("250.00"),
        gl_allocated_amount=Decimal("0.00"),
        gl_principal_allocated=Decimal("0.00"),
        gl_interest_allocated=Decimal("0.00"),
        gl_penal_interest_allocated=Decimal("0.00"),
        gl_charges_allocated=Decimal("0.00"),
        allocation_voucher_id=None,
    )
    loan = SimpleNamespace(
        organization_id=org_id,
        loan_account_number="LN-002",
        loan_asset_account_id=loan_asset_account_id,
        interest_receivable_account_id=interest_receivable_account_id,
        penal_interest_income_account_id=penal_income_account_id,
        charges_income_account_id=charges_income_account_id,
    )

    await service._post_receipt_allocation_to_gl(
        receipt=receipt,
        loan=loan,
        posted_by=uuid4(),
    )

    kwargs = service.gl_posting_service.post_entries.await_args.kwargs
    assert kwargs["source_reference"] == "RCP-002/ALLOC"
    assert sum(line["debit_amount"] for line in kwargs["lines"]) == Decimal("15000.00")
    assert sum(line["credit_amount"] for line in kwargs["lines"]) == Decimal("15000.00")
    assert receipt.gl_allocated_amount == Decimal("15000.00")
    assert receipt.gl_principal_allocated == Decimal("10000.00")
    assert receipt.gl_interest_allocated == Decimal("4000.00")
    assert receipt.gl_penal_interest_allocated == Decimal("750.00")
    assert receipt.gl_charges_allocated == Decimal("250.00")
