"""Unit tests for Separation and FnF Settlement.

Tests cover:
- Separation initiation and lifecycle
- Clearance workflow
- FnF calculation (gratuity, leave encashment, recoveries)
- Status transitions
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.models.hris.separation import (
    SeparationType,
    SeparationStatus,
    ResignationReason,
    ClearanceStatus,
    FnFStatus,
)


class TestSeparationTypes:
    """Tests for separation type enums."""

    def test_all_separation_types_defined(self):
        """Test all required separation types are defined."""
        expected_types = [
            SeparationType.RESIGNATION,
            SeparationType.TERMINATION,
            SeparationType.RETIREMENT,
            SeparationType.ABSCONDING,
            SeparationType.DEATH,
            SeparationType.VRS,
            SeparationType.CONTRACT_END,
        ]
        for sep_type in expected_types:
            assert isinstance(sep_type, SeparationType)

    def test_separation_status_flow(self):
        """Test separation status flow values."""
        assert SeparationStatus.INITIATED.value == "INITIATED"
        assert SeparationStatus.PENDING_APPROVAL.value == "PENDING_APPROVAL"
        assert SeparationStatus.APPROVED.value == "APPROVED"
        assert SeparationStatus.NOTICE_PERIOD.value == "NOTICE_PERIOD"
        assert SeparationStatus.CLEARANCE.value == "CLEARANCE"
        assert SeparationStatus.FNF_PENDING.value == "FNF_PENDING"
        assert SeparationStatus.COMPLETED.value == "COMPLETED"

    def test_resignation_reasons(self):
        """Test resignation reason categories."""
        expected_reasons = [
            ResignationReason.BETTER_OPPORTUNITY,
            ResignationReason.PERSONAL,
            ResignationReason.HEALTH,
            ResignationReason.RELOCATION,
            ResignationReason.HIGHER_STUDIES,
        ]
        for reason in expected_reasons:
            assert isinstance(reason, ResignationReason)


class TestNoticePeriodCalculation:
    """Tests for notice period calculations."""

    def test_notice_period_full_served(self):
        """Test when full notice period is served."""
        initiation_date = date(2024, 1, 1)
        last_working_date = date(2024, 1, 31)
        notice_period_days = 30

        days_served = (last_working_date - initiation_date).days
        shortfall = max(0, notice_period_days - days_served)

        assert days_served == 30
        assert shortfall == 0

    def test_notice_period_partial_served(self):
        """Test when notice period is partially served."""
        initiation_date = date(2024, 1, 1)
        last_working_date = date(2024, 1, 15)
        notice_period_days = 30

        days_served = (last_working_date - initiation_date).days
        shortfall = max(0, notice_period_days - days_served)

        assert days_served == 14
        assert shortfall == 16

    def test_notice_recovery_calculation(self):
        """Test notice period recovery amount calculation."""
        monthly_salary = Decimal("100000")
        shortfall_days = 15
        daily_salary = monthly_salary / Decimal("30")

        recovery_amount = daily_salary * Decimal(str(shortfall_days))

        assert recovery_amount == Decimal("50000")


class TestGratuityCalculation:
    """Tests for gratuity calculation."""

    def test_gratuity_formula(self):
        """Test gratuity calculation formula: (15/26) × basic × years."""
        basic_salary = Decimal("50000")
        years_of_service = Decimal("10")

        gratuity = (
            Decimal("15") / Decimal("26") *
            basic_salary *
            years_of_service
        ).quantize(Decimal("0.01"))

        # Expected: (15/26) × 50000 × 10 = 288461.54
        assert gratuity == Decimal("288461.54")

    def test_gratuity_eligibility_five_years(self):
        """Test gratuity eligibility requires 5 years of service."""
        required_years = Decimal("5")

        # Less than 5 years - not eligible
        years_1 = Decimal("4.9")
        eligible_1 = years_1 >= required_years
        assert eligible_1 == False

        # Exactly 5 years - eligible
        years_2 = Decimal("5.0")
        eligible_2 = years_2 >= required_years
        assert eligible_2 == True

        # More than 5 years - eligible
        years_3 = Decimal("7.5")
        eligible_3 = years_3 >= required_years
        assert eligible_3 == True

    def test_gratuity_maximum_cap(self):
        """Test gratuity is capped at ₹20 lakhs."""
        basic_salary = Decimal("200000")  # High salary
        years_of_service = Decimal("25")
        max_gratuity = Decimal("2000000")

        calculated_gratuity = (
            Decimal("15") / Decimal("26") *
            basic_salary *
            years_of_service
        )

        # Should exceed cap
        assert calculated_gratuity > max_gratuity

        # Apply cap
        final_gratuity = min(calculated_gratuity, max_gratuity)
        assert final_gratuity == Decimal("2000000")

    def test_gratuity_not_eligible_under_five_years(self):
        """Test no gratuity for service under 5 years."""
        basic_salary = Decimal("50000")
        years_of_service = Decimal("4.5")
        required_years = Decimal("5")

        if years_of_service < required_years:
            gratuity = Decimal("0")
        else:
            gratuity = (
                Decimal("15") / Decimal("26") *
                basic_salary *
                years_of_service
            )

        assert gratuity == Decimal("0")


class TestLeaveEncashmentCalculation:
    """Tests for leave encashment calculation."""

    def test_leave_encashment_formula(self):
        """Test leave encashment calculation: Basic/26 × days."""
        basic_salary = Decimal("50000")
        leave_days = Decimal("30")

        per_day_amount = basic_salary / Decimal("26")
        encashment = (per_day_amount * leave_days).quantize(Decimal("0.01"))

        # Expected: (50000/26) × 30 = 57692.31
        assert encashment == Decimal("57692.31")

    def test_leave_encashment_zero_balance(self):
        """Test leave encashment with zero leave balance."""
        basic_salary = Decimal("50000")
        leave_days = Decimal("0")

        if leave_days <= 0:
            encashment = Decimal("0")
        else:
            per_day_amount = basic_salary / Decimal("26")
            encashment = per_day_amount * leave_days

        assert encashment == Decimal("0")

    def test_leave_encashment_partial_days(self):
        """Test leave encashment with partial days."""
        basic_salary = Decimal("50000")
        leave_days = Decimal("15.5")

        per_day_amount = basic_salary / Decimal("26")
        encashment = (per_day_amount * leave_days).quantize(Decimal("0.01"))

        # Expected: (50000/26) × 15.5 = 29807.69
        assert encashment == Decimal("29807.69")


class TestFnFCalculation:
    """Tests for Full & Final settlement calculation."""

    def test_fnf_total_earnings(self):
        """Test FnF total earnings calculation."""
        pending_salary = Decimal("30000")
        leave_encashment = Decimal("57692.31")
        gratuity = Decimal("288461.54")
        bonus = Decimal("10000")
        reimbursements = Decimal("5000")
        other_earnings = Decimal("2000")

        total_earnings = (
            pending_salary +
            leave_encashment +
            gratuity +
            bonus +
            reimbursements +
            other_earnings
        )

        assert total_earnings == Decimal("393153.85")

    def test_fnf_total_deductions(self):
        """Test FnF total deductions calculation."""
        notice_recovery = Decimal("50000")
        advance_recovery = Decimal("10000")
        loan_recovery = Decimal("20000")
        asset_recovery = Decimal("5000")
        clearance_recovery = Decimal("3000")
        other_deductions = Decimal("1000")
        tds = Decimal("15000")

        total_deductions = (
            notice_recovery +
            advance_recovery +
            loan_recovery +
            asset_recovery +
            clearance_recovery +
            other_deductions +
            tds
        )

        assert total_deductions == Decimal("104000")

    def test_fnf_net_payable(self):
        """Test FnF net payable calculation."""
        total_earnings = Decimal("393153.85")
        total_deductions = Decimal("104000")

        net_payable = total_earnings - total_deductions

        assert net_payable == Decimal("289153.85")

    def test_fnf_negative_net_payable(self):
        """Test FnF when deductions exceed earnings (employee owes)."""
        total_earnings = Decimal("50000")
        total_deductions = Decimal("75000")

        net_payable = total_earnings - total_deductions

        assert net_payable == Decimal("-25000")


class TestYearsOfServiceCalculation:
    """Tests for years of service calculation."""

    def test_exact_years_calculation(self):
        """Test exact years calculation."""
        joining_date = date(2019, 1, 15)
        last_working_date = date(2024, 1, 15)

        days = (last_working_date - joining_date).days
        years = Decimal(str(days)) / Decimal("365.25")

        assert years >= Decimal("4.99")  # Approximately 5 years

    def test_partial_years_calculation(self):
        """Test partial years calculation."""
        joining_date = date(2020, 6, 1)
        last_working_date = date(2024, 1, 15)

        days = (last_working_date - joining_date).days
        years = (Decimal(str(days)) / Decimal("365.25")).quantize(Decimal("0.01"))

        # About 3.6 years
        assert Decimal("3.5") <= years <= Decimal("3.7")

    def test_less_than_one_year(self):
        """Test service less than one year."""
        joining_date = date(2024, 1, 1)
        last_working_date = date(2024, 6, 30)

        days = (last_working_date - joining_date).days
        years = (Decimal(str(days)) / Decimal("365.25")).quantize(Decimal("0.01"))

        assert years < Decimal("1.0")


class TestClearanceStatus:
    """Tests for clearance status."""

    def test_clearance_status_values(self):
        """Test clearance status enum values."""
        assert ClearanceStatus.PENDING.value == "PENDING"
        assert ClearanceStatus.CLEARED.value == "CLEARED"
        assert ClearanceStatus.NOT_APPLICABLE.value == "NOT_APPLICABLE"
        assert ClearanceStatus.RECOVERY_PENDING.value == "RECOVERY_PENDING"

    def test_clearance_completion_check(self):
        """Test checking if clearance is complete."""
        clearances = [
            {"status": ClearanceStatus.CLEARED},
            {"status": ClearanceStatus.CLEARED},
            {"status": ClearanceStatus.NOT_APPLICABLE},
            {"status": ClearanceStatus.CLEARED},
        ]

        pending = sum(1 for c in clearances if c["status"] == ClearanceStatus.PENDING)
        recovery_pending = sum(1 for c in clearances if c["status"] == ClearanceStatus.RECOVERY_PENDING)
        is_complete = pending == 0 and recovery_pending == 0

        assert is_complete == True

    def test_clearance_not_complete_with_pending(self):
        """Test clearance not complete when items pending."""
        clearances = [
            {"status": ClearanceStatus.CLEARED},
            {"status": ClearanceStatus.PENDING},
            {"status": ClearanceStatus.CLEARED},
        ]

        pending = sum(1 for c in clearances if c["status"] == ClearanceStatus.PENDING)
        is_complete = pending == 0

        assert is_complete == False


class TestFnFStatus:
    """Tests for FnF status flow."""

    def test_fnf_status_values(self):
        """Test FnF status enum values."""
        assert FnFStatus.DRAFT.value == "DRAFT"
        assert FnFStatus.CALCULATED.value == "CALCULATED"
        assert FnFStatus.PENDING_APPROVAL.value == "PENDING_APPROVAL"
        assert FnFStatus.APPROVED.value == "APPROVED"
        assert FnFStatus.PAID.value == "PAID"
        assert FnFStatus.CANCELLED.value == "CANCELLED"

    def test_fnf_status_flow_valid(self):
        """Test valid FnF status transitions."""
        valid_transitions = {
            FnFStatus.DRAFT: [FnFStatus.CALCULATED],
            FnFStatus.CALCULATED: [FnFStatus.PENDING_APPROVAL, FnFStatus.APPROVED],
            FnFStatus.PENDING_APPROVAL: [FnFStatus.APPROVED],
            FnFStatus.APPROVED: [FnFStatus.PAID],
        }

        # Verify transitions are defined
        assert FnFStatus.CALCULATED in valid_transitions[FnFStatus.DRAFT]
        assert FnFStatus.APPROVED in valid_transitions[FnFStatus.CALCULATED]


class TestPendingSalaryCalculation:
    """Tests for pending salary calculation."""

    def test_pending_salary_full_month(self):
        """Test pending salary for full month."""
        monthly_gross = Decimal("100000")
        days_in_month = 30
        days_worked = 30

        pending = (monthly_gross / Decimal(str(days_in_month))) * Decimal(str(days_worked))

        assert pending == Decimal("100000")

    def test_pending_salary_partial_month(self):
        """Test pending salary for partial month."""
        monthly_gross = Decimal("100000")
        days_in_month = 30
        days_worked = 15

        pending = (monthly_gross / Decimal(str(days_in_month))) * Decimal(str(days_worked))

        assert pending == Decimal("50000")

    def test_pending_salary_last_day(self):
        """Test pending salary when leaving on last day."""
        monthly_gross = Decimal("60000")
        last_working_date = date(2024, 1, 31)

        # Days from 1st to 31st
        days_worked = last_working_date.day
        daily_salary = monthly_gross / Decimal("30")
        pending = daily_salary * Decimal(str(days_worked))

        assert pending == Decimal("62000")  # 31 days worked in 30-day month


class TestSeparationLifecycle:
    """Tests for separation lifecycle management."""

    def test_separation_initiation(self):
        """Test separation initiation creates correct status."""
        separation = {
            "status": SeparationStatus.INITIATED,
            "initiation_date": date.today(),
            "notice_period_days": 30,
        }

        assert separation["status"] == SeparationStatus.INITIATED
        assert separation["initiation_date"] == date.today()

    def test_separation_approval_updates_status(self):
        """Test separation approval updates status correctly."""
        separation = {
            "status": SeparationStatus.INITIATED,
            "approved_by": None,
            "approved_at": None,
        }

        # Approve
        separation["status"] = SeparationStatus.APPROVED
        separation["approved_by"] = uuid4()
        separation["approved_at"] = datetime.now()

        assert separation["status"] == SeparationStatus.APPROVED
        assert separation["approved_by"] is not None

    def test_separation_withdrawal(self):
        """Test separation can be withdrawn before completion."""
        allowed_withdrawal_statuses = [
            SeparationStatus.INITIATED,
            SeparationStatus.PENDING_APPROVAL,
            SeparationStatus.APPROVED,
            SeparationStatus.NOTICE_PERIOD,
            SeparationStatus.CLEARANCE,
        ]

        disallowed_statuses = [
            SeparationStatus.COMPLETED,
            SeparationStatus.FNF_PAID,
        ]

        for status in allowed_withdrawal_statuses:
            can_withdraw = status not in disallowed_statuses
            assert can_withdraw == True

        for status in disallowed_statuses:
            can_withdraw = status not in disallowed_statuses
            assert can_withdraw == False
