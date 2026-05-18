"""Payroll processing guard tests."""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.payroll.payroll import PayrollBatchStatus
from app.schemas.payroll.payroll import PayrollBatchCreate
from app.services.payroll.payroll_service import PayrollBatchService, PayrollProcessingService


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _Session:
    def __init__(self, value):
        self.value = value

    async def execute(self, _query):
        return _ScalarResult(self.value)


def _batch_create(**overrides):
    data = {
        "organization_id": uuid4(),
        "payroll_month": 4,
        "payroll_year": 2026,
        "pay_period_from": date(2026, 4, 1),
        "pay_period_to": date(2026, 4, 30),
    }
    data.update(overrides)
    return PayrollBatchCreate(**data)


def test_payroll_batch_create_validates_period_order():
    service = PayrollBatchService(None)

    with pytest.raises(ValueError, match="start cannot be after"):
        service._validate_payroll_period(
            _batch_create(
                pay_period_from=date(2026, 4, 30),
                pay_period_to=date(2026, 4, 1),
            )
        )


def test_payroll_batch_create_validates_period_month():
    service = PayrollBatchService(None)

    with pytest.raises(ValueError, match="payroll month"):
        service._validate_payroll_period(
            _batch_create(
                pay_period_from=date(2026, 3, 31),
                pay_period_to=date(2026, 4, 30),
            )
        )


@pytest.mark.asyncio
async def test_payroll_batch_create_rejects_duplicate_active_period():
    service = PayrollBatchService(_Session(uuid4()))

    with pytest.raises(ValueError, match="already exists"):
        await service._ensure_unique_period(uuid4(), 2026, 4)


@pytest.mark.asyncio
async def test_monthly_attendance_must_be_processed_and_locked_for_payroll():
    service = PayrollProcessingService(_Session(SimpleNamespace(is_processed=False, is_locked=False)))

    with pytest.raises(ValueError, match="not processed"):
        await service._get_attendance_summary(uuid4(), 2026, 4)

    service = PayrollProcessingService(_Session(SimpleNamespace(is_processed=True, is_locked=False)))

    with pytest.raises(ValueError, match="locked"):
        await service._get_attendance_summary(uuid4(), 2026, 4)


@pytest.mark.asyncio
async def test_locked_attendance_summary_maps_to_payroll_days():
    service = PayrollProcessingService(
        _Session(
            SimpleNamespace(
                is_processed=True,
                is_locked=True,
                working_days=26,
                present_days=20,
                half_days=2,
                absent_days=1,
                paid_leave_days=3,
                lop_days=1,
            )
        )
    )

    summary = await service._get_attendance_summary(uuid4(), 2026, 4)

    assert summary == {
        "working_days": Decimal("26"),
        "days_present": Decimal("21.0"),
        "days_absent": Decimal("1"),
        "leave_days": Decimal("3"),
        "lop_days": Decimal("1"),
    }


@pytest.mark.asyncio
async def test_bank_file_requires_approved_or_paid_batch(monkeypatch):
    service = PayrollBatchService(None)
    async def get_batch(_id):
        return SimpleNamespace(status=PayrollBatchStatus.PROCESSED)

    monkeypatch.setattr(
        service,
        "get",
        get_batch,
    )

    with pytest.raises(ValueError, match="only after approval"):
        await service.export_bank_file(uuid4())


@pytest.mark.asyncio
async def test_bank_file_validates_salary_bank_details(monkeypatch):
    service = PayrollBatchService(None)
    async def get_batch(_id):
        return SimpleNamespace(
            status=PayrollBatchStatus.APPROVED,
            payslips=[
                SimpleNamespace(
                    employee_code="E001",
                    employee_name="Asha Rao",
                    net_salary=Decimal("1000.00"),
                    bank_account_number=None,
                    bank_ifsc="HDFC0001234",
                )
            ],
        )

    monkeypatch.setattr(
        service,
        "get",
        get_batch,
    )

    with pytest.raises(ValueError, match="Missing salary bank details"):
        await service.export_bank_file(uuid4())


@pytest.mark.asyncio
async def test_bank_file_exports_manual_upload_csv(monkeypatch):
    service = PayrollBatchService(None)
    async def get_batch(_id):
        return SimpleNamespace(
            status=PayrollBatchStatus.APPROVED,
            batch_number="PAY/2026/04/001",
            payroll_year=2026,
            payroll_month=4,
            payslips=[
                SimpleNamespace(
                    employee_code="E001",
                    employee_name="Asha Rao",
                    net_salary=Decimal("1000.00"),
                    bank_account_number="1234567890",
                    bank_ifsc="HDFC0001234",
                    payment_reference=None,
                )
            ],
        )

    monkeypatch.setattr(
        service,
        "get",
        get_batch,
    )

    bank_file = await service.export_bank_file(uuid4())

    assert bank_file.file_name == "salary_payout_PAY_2026_04_001.csv"
    assert bank_file.record_count == 1
    assert bank_file.total_amount == Decimal("1000.00")
    assert "E001,Asha Rao,1234567890,HDFC0001234,1000.00" in bank_file.file_content


@pytest.mark.asyncio
async def test_mark_paid_requires_payment_reference(monkeypatch):
    service = PayrollBatchService(None)

    async def get_batch(_id, _organization_id=None):
        return SimpleNamespace(status=PayrollBatchStatus.APPROVED)

    monkeypatch.setattr(service, "get", get_batch)

    with pytest.raises(ValueError, match="Payment reference is required"):
        await service.mark_paid(uuid4(), uuid4(), payment_reference=" ")


@pytest.mark.asyncio
async def test_mark_paid_requires_salary_bank_details(monkeypatch):
    service = PayrollBatchService(None)

    async def get_batch(_id, _organization_id=None):
        return SimpleNamespace(
            status=PayrollBatchStatus.APPROVED,
            payslips=[
                SimpleNamespace(
                    employee_code="E001",
                    employee_name="Asha Rao",
                    net_salary=Decimal("1000.00"),
                    bank_account_number=None,
                    bank_ifsc="HDFC0001234",
                )
            ],
        )

    monkeypatch.setattr(service, "get", get_batch)

    with pytest.raises(ValueError, match="Missing salary bank details"):
        await service.mark_paid(uuid4(), uuid4(), payment_reference="NEFT-001")
