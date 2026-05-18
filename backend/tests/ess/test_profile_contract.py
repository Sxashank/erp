"""ESS payroll profile contract tests."""

from types import SimpleNamespace

from app.services.ess.profile_service import ESSProfileService


def test_payslip_period_uses_payroll_batch_month():
    payslip = SimpleNamespace(
        batch=SimpleNamespace(payroll_year=2026, payroll_month=4),
    )

    assert ESSProfileService.payslip_period(payslip) == "2026-04"
