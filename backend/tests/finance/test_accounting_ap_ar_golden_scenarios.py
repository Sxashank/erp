"""Golden AP/AR accounting scenarios for Indian finance workflows.

These tests intentionally avoid live integrations. They pin manual-first
business behavior around GST/TDS/TCS, payable/receivable balances, and GL
posting shapes so accounting changes cannot drift silently.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.models.ap_ar.payment import DocumentType
from app.models.ap_ar.purchase_bill import BillStatus
from app.models.ap_ar.purchase_bill import PaymentStatus as BillPaymentStatus
from app.models.ap_ar.sales_invoice import InvoiceStatus, ReceiptStatus
from app.services.ap_ar.payment_service import PaymentService
from app.services.ap_ar.purchase_bill_service import PurchaseBillService
from app.services.ap_ar.sales_invoice_service import SalesInvoiceService


def money(value: str) -> Decimal:
    return Decimal(value)


def account(account_id):
    return SimpleNamespace(id=account_id)


def assert_balanced(lines: list[dict]) -> None:
    debit_total = sum(line["debit_amount"] for line in lines)
    credit_total = sum(line["credit_amount"] for line in lines)
    assert debit_total == credit_total


@pytest.mark.asyncio
async def test_purchase_bill_with_gst_and_tds_posts_balanced_gl_lines() -> None:
    organization_id = uuid4()
    vendor_id = uuid4()
    fy_id = uuid4()
    period_id = uuid4()
    expense_account_id = uuid4()
    ap_account_id = uuid4()
    cgst_input_id = uuid4()
    sgst_input_id = uuid4()
    tds_payable_id = uuid4()

    bill = SimpleNamespace(
        id=uuid4(),
        bill_number="PB-2026-0001",
        vendor_invoice_number="VEN-001",
        bill_date=date(2026, 4, 10),
        organization_id=organization_id,
        unit_id=None,
        vendor_id=vendor_id,
        subtotal=money("100000.00"),
        taxable_amount=money("100000.00"),
        cgst_amount=money("9000.00"),
        sgst_amount=money("9000.00"),
        igst_amount=money("0.00"),
        cess_amount=money("0.00"),
        tds_amount=money("10000.00"),
        total_amount=money("108000.00"),
        is_posted=False,
        lines=[
            SimpleNamespace(
                line_number=1,
                description="Professional services",
                taxable_amount=money("100000.00"),
                expense_account_id=expense_account_id,
            )
        ],
    )

    service = PurchaseBillService.__new__(PurchaseBillService)
    service.fy_repo = SimpleNamespace(get_by_date=AsyncMock(return_value=SimpleNamespace(id=fy_id)))
    service.period_repo = SimpleNamespace(
        get_by_date=AsyncMock(return_value=SimpleNamespace(id=period_id))
    )
    service.vendor_repo = SimpleNamespace(
        get=AsyncMock(
            return_value=SimpleNamespace(
                id=vendor_id,
                name="UAT Vendor",
                control_account_id=ap_account_id,
                expense_account_id=None,
            )
        )
    )

    account_by_code = {
        "CGST-INPUT": account(cgst_input_id),
        "SGST-INPUT": account(sgst_input_id),
        "TDS-PAYABLE": account(tds_payable_id),
    }
    service.account_repo = SimpleNamespace(
        get_by_code=AsyncMock(side_effect=lambda _org_id, code: account_by_code.get(code))
    )
    service.gl_posting_service = SimpleNamespace(post_from_source=AsyncMock())

    await service._post_to_gl(bill, posted_by=uuid4())

    kwargs = service.gl_posting_service.post_from_source.await_args.kwargs
    lines = kwargs["lines"]

    assert bill.is_posted is True
    assert kwargs["source_reference"] == "PB-2026-0001"
    assert len(lines) == 5
    assert_balanced(lines)
    assert {line["account_id"] for line in lines} == {
        expense_account_id,
        cgst_input_id,
        sgst_input_id,
        tds_payable_id,
        ap_account_id,
    }
    assert sum(line["debit_amount"] for line in lines) == money("118000.00")
    assert sum(line["credit_amount"] for line in lines) == money("118000.00")


@pytest.mark.asyncio
async def test_sales_invoice_with_igst_and_tcs_posts_balanced_gl_lines() -> None:
    organization_id = uuid4()
    customer_id = uuid4()
    fy_id = uuid4()
    period_id = uuid4()
    revenue_account_id = uuid4()
    ar_account_id = uuid4()
    igst_output_id = uuid4()
    tcs_payable_id = uuid4()

    invoice = SimpleNamespace(
        id=uuid4(),
        invoice_number="SI-2026-0001",
        invoice_date=date(2026, 4, 12),
        organization_id=organization_id,
        customer_id=customer_id,
        total_amount=money("296000.00"),
        taxable_amount=money("250000.00"),
        cgst_amount=money("0.00"),
        sgst_amount=money("0.00"),
        igst_amount=money("45000.00"),
        cess_amount=money("0.00"),
        tcs_amount=money("1000.00"),
        is_posted=False,
        lines=[
            SimpleNamespace(
                line_number=1,
                description="Consulting revenue",
                taxable_amount=money("250000.00"),
                revenue_account_id=revenue_account_id,
            )
        ],
    )

    service = SalesInvoiceService.__new__(SalesInvoiceService)
    service.fy_repo = SimpleNamespace(get_by_date=AsyncMock(return_value=SimpleNamespace(id=fy_id)))
    service.period_repo = SimpleNamespace(
        get_by_date=AsyncMock(return_value=SimpleNamespace(id=period_id))
    )
    service.customer_repo = SimpleNamespace(
        get=AsyncMock(
            return_value=SimpleNamespace(
                id=customer_id,
                name="UAT Customer",
                control_account_id=ar_account_id,
                revenue_account_id=None,
            )
        )
    )

    account_by_code = {
        "IGST-OUT": account(igst_output_id),
        "TCS-PAY": account(tcs_payable_id),
    }
    service.account_repo = SimpleNamespace(
        get_by_code=AsyncMock(side_effect=lambda _org_id, code: account_by_code.get(code))
    )
    service.gl_posting_service = SimpleNamespace(post_entries=AsyncMock())

    await service._post_to_gl(invoice, posted_by=uuid4())

    kwargs = service.gl_posting_service.post_entries.await_args.kwargs
    lines = kwargs["lines"]

    assert invoice.is_posted is True
    assert kwargs["source_reference"] == "SI-2026-0001"
    assert len(lines) == 4
    assert_balanced(lines)
    assert {line["account_id"] for line in lines} == {
        ar_account_id,
        revenue_account_id,
        igst_output_id,
        tcs_payable_id,
    }
    assert sum(line["debit_amount"] for line in lines) == money("296000.00")
    assert sum(line["credit_amount"] for line in lines) == money("296000.00")


@pytest.mark.asyncio
async def test_manual_vendor_payment_allocation_updates_and_reverses_bill_balance() -> None:
    bill = SimpleNamespace(
        id=uuid4(),
        bill_number="PB-2026-0002",
        total_amount=money("108000.00"),
        balance_amount=money("108000.00"),
        payment_status=BillPaymentStatus.UNPAID,
        status=BillStatus.APPROVED,
    )
    allocation = SimpleNamespace(
        document_type=DocumentType.PURCHASE_BILL,
        document_id=bill.id,
        allocated_amount=money("60000.00"),
    )
    payment = SimpleNamespace(allocations=[allocation])

    execute_result = SimpleNamespace(scalar_one=lambda: bill)
    service = PaymentService.__new__(PaymentService)
    service.session = SimpleNamespace(execute=AsyncMock(return_value=execute_result))

    await service._update_document_balances(payment)

    assert bill.balance_amount == money("48000.00")
    assert bill.payment_status == BillPaymentStatus.PARTIALLY_PAID
    assert bill.status == BillStatus.PARTIALLY_PAID

    await service._reverse_document_balances(payment)

    assert bill.balance_amount == money("108000.00")
    assert bill.payment_status == BillPaymentStatus.UNPAID
    assert bill.status == BillStatus.APPROVED


@pytest.mark.asyncio
async def test_manual_customer_receipt_allocation_updates_and_reverses_invoice_balance() -> None:
    invoice = SimpleNamespace(
        id=uuid4(),
        invoice_number="SI-2026-0002",
        total_amount=money("296000.00"),
        balance_amount=money("296000.00"),
        receipt_status=ReceiptStatus.UNRECEIVED,
        status=InvoiceStatus.APPROVED,
    )
    allocation = SimpleNamespace(
        document_type=DocumentType.SALES_INVOICE,
        document_id=invoice.id,
        allocated_amount=money("296000.00"),
    )
    receipt = SimpleNamespace(allocations=[allocation])

    execute_result = SimpleNamespace(scalar_one=lambda: invoice)
    service = PaymentService.__new__(PaymentService)
    service.session = SimpleNamespace(execute=AsyncMock(return_value=execute_result))

    await service._update_document_balances(receipt)

    assert invoice.balance_amount == money("0.00")
    assert invoice.receipt_status == ReceiptStatus.RECEIVED
    assert invoice.status == InvoiceStatus.RECEIVED

    await service._reverse_document_balances(receipt)

    assert invoice.balance_amount == money("296000.00")
    assert invoice.receipt_status == ReceiptStatus.UNRECEIVED
    assert invoice.status == InvoiceStatus.APPROVED
