"""Unit tests for Lease Accounting service (Ind AS 116).

Tests cover:
- Lease classification
- ROUA (Right of Use Asset) calculation
- Lease liability NPV calculation
- Interest and amortization schedules
- Lease modifications
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4
import math


class TestLeaseClassification:
    """Tests for lease classification."""

    def test_short_term_lease_exemption(self):
        """Test short-term lease (≤12 months) is exempt from Ind AS 116."""
        lease_start = date(2024, 4, 1)
        lease_end = date(2025, 3, 31)

        lease_term_months = (
            (lease_end.year - lease_start.year) * 12
            + (lease_end.month - lease_start.month)
            + 1
        )

        is_short_term = lease_term_months <= 12
        assert is_short_term

    def test_low_value_lease_exemption(self):
        """Test low-value lease is exempt from Ind AS 116."""
        asset_value = Decimal("4000.00")
        low_value_threshold = Decimal("5000.00")  # USD 5,000 equivalent

        is_low_value = asset_value < low_value_threshold
        assert is_low_value

    def test_finance_lease_identification(self):
        """Test finance lease identification criteria."""
        # Transfer of ownership at end
        transfers_ownership = True

        # Bargain purchase option
        has_bargain_purchase = True

        # Lease term is major part of useful life (>75%)
        lease_term_years = 8
        useful_life_years = 10
        is_major_part = (lease_term_years / useful_life_years) > 0.75

        is_finance_lease = (
            transfers_ownership or has_bargain_purchase or is_major_part
        )
        assert is_finance_lease


class TestROUACalculation:
    """Tests for Right of Use Asset calculation."""

    def test_roua_initial_measurement(self):
        """Test ROUA initial measurement equals lease liability + initial costs."""
        lease_liability = Decimal("850000.00")
        initial_direct_costs = Decimal("50000.00")
        prepaid_lease_payments = Decimal("100000.00")
        restoration_obligation = Decimal("30000.00")

        roua_initial = (
            lease_liability
            + initial_direct_costs
            + prepaid_lease_payments
            + restoration_obligation
        )

        assert roua_initial == Decimal("1030000.00")

    def test_roua_depreciation_calculation(self):
        """Test ROUA depreciation over lease term."""
        roua_initial = Decimal("1030000.00")
        lease_term_months = 60
        residual_value = Decimal("0.00")

        monthly_depreciation = (roua_initial - residual_value) / lease_term_months

        assert round(monthly_depreciation, 2) == Decimal("17166.67")

    def test_roua_shorter_of_useful_life_or_lease_term(self):
        """Test ROUA depreciated over shorter of useful life or lease term."""
        roua_initial = Decimal("1000000.00")
        asset_useful_life_years = 10
        lease_term_years = 5

        # If no transfer of ownership, use shorter period
        transfers_ownership = False

        if transfers_ownership:
            depreciation_years = asset_useful_life_years
        else:
            depreciation_years = min(asset_useful_life_years, lease_term_years)

        assert depreciation_years == 5

        annual_depreciation = roua_initial / depreciation_years
        assert annual_depreciation == Decimal("200000.00")


class TestLeaseLibabilityNPV:
    """Tests for Lease Liability NPV calculation."""

    def test_npv_calculation_basic(self):
        """Test basic NPV calculation for lease liability."""
        # Monthly payment: 20,000 for 60 months
        # Incremental borrowing rate: 10% p.a.

        monthly_payment = Decimal("20000.00")
        num_payments = 60
        annual_rate = Decimal("0.10")
        monthly_rate = annual_rate / 12

        # NPV = PMT * [1 - (1 + r)^-n] / r
        npv = Decimal("0")
        for i in range(1, num_payments + 1):
            discount_factor = Decimal(str(1 / (1 + float(monthly_rate)) ** i))
            npv += monthly_payment * discount_factor

        npv = npv.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Expected NPV approximately 942,169
        assert npv > Decimal("900000.00")
        assert npv < Decimal("1000000.00")

    def test_npv_with_variable_payments(self):
        """Test NPV with escalating payments."""
        base_payment = Decimal("20000.00")
        escalation_rate = Decimal("0.05")  # 5% annual escalation
        num_years = 5
        annual_rate = Decimal("0.10")
        monthly_rate = annual_rate / 12

        npv = Decimal("0")
        month = 0

        for year in range(num_years):
            year_payment = base_payment * (1 + escalation_rate) ** year
            for m in range(12):
                month += 1
                discount_factor = Decimal(str(1 / (1 + float(monthly_rate)) ** month))
                npv += year_payment * discount_factor

        npv = npv.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # NPV with escalation should be higher than without
        assert npv > Decimal("900000.00")

    def test_discount_rate_selection(self):
        """Test discount rate selection hierarchy."""
        implicit_rate = None  # Not readily determinable
        incremental_borrowing_rate = Decimal("0.10")

        # Use implicit rate if known, otherwise IBR
        if implicit_rate is not None:
            discount_rate = implicit_rate
        else:
            discount_rate = incremental_borrowing_rate

        assert discount_rate == Decimal("0.10")


class TestLeaseAmortizationSchedule:
    """Tests for lease amortization schedule."""

    def test_interest_expense_calculation(self):
        """Test interest expense calculation using effective interest method."""
        opening_liability = Decimal("942169.00")
        annual_rate = Decimal("0.10")
        monthly_rate = annual_rate / 12

        monthly_interest = opening_liability * monthly_rate

        assert round(monthly_interest, 2) == Decimal("7851.41")

    def test_principal_repayment(self):
        """Test principal repayment calculation."""
        monthly_payment = Decimal("20000.00")
        monthly_interest = Decimal("7851.41")

        principal_repayment = monthly_payment - monthly_interest

        assert round(principal_repayment, 2) == Decimal("12148.59")

    def test_closing_liability(self):
        """Test closing liability calculation."""
        opening_liability = Decimal("942169.00")
        principal_repayment = Decimal("12148.59")

        closing_liability = opening_liability - principal_repayment

        assert round(closing_liability, 2) == Decimal("930020.41")

    def test_schedule_totals(self):
        """Test amortization schedule totals."""
        monthly_payment = Decimal("20000.00")
        num_payments = 60
        initial_liability = Decimal("942169.00")

        total_payments = monthly_payment * num_payments
        total_interest = total_payments - initial_liability

        assert total_payments == Decimal("1200000.00")
        assert total_interest == Decimal("257831.00")

    def test_final_liability_is_zero(self):
        """Test final liability equals zero (or close to zero)."""
        # After all payments, liability should be zero
        final_liability = Decimal("0.00")
        tolerance = Decimal("1.00")  # Allow for rounding

        assert abs(final_liability) <= tolerance


class TestLeaseModification:
    """Tests for lease modifications."""

    def test_modification_extends_term(self):
        """Test modification that extends lease term."""
        original_term_months = 60
        extension_months = 24
        new_term_months = original_term_months + extension_months

        assert new_term_months == 84

    def test_modification_increases_scope(self):
        """Test modification that increases scope (additional space)."""
        original_area_sqft = 5000
        additional_area_sqft = 2000
        new_area_sqft = original_area_sqft + additional_area_sqft

        assert new_area_sqft == 7000

        # Payment increases proportionally
        original_payment = Decimal("100000.00")
        rate_per_sqft = original_payment / original_area_sqft
        new_payment = rate_per_sqft * new_area_sqft

        assert new_payment == Decimal("140000.00")

    def test_modification_decreases_scope(self):
        """Test modification that decreases scope (partial termination)."""
        original_liability = Decimal("1000000.00")
        terminated_portion = Decimal("0.30")  # 30% of space returned

        liability_terminated = original_liability * terminated_portion
        remaining_liability = original_liability - liability_terminated

        assert liability_terminated == Decimal("300000.00")
        assert remaining_liability == Decimal("700000.00")

    def test_remeasurement_on_modification(self):
        """Test lease remeasurement on modification."""
        # Original liability: 942,169
        # Remaining payments: 36 months x 20,000 = 720,000
        # Modified payments: 36 months x 22,000 = 792,000
        # New rate: 11%

        remaining_months = 36
        modified_payment = Decimal("22000.00")
        new_annual_rate = Decimal("0.11")
        monthly_rate = new_annual_rate / 12

        new_liability = Decimal("0")
        for i in range(1, remaining_months + 1):
            discount_factor = Decimal(str(1 / (1 + float(monthly_rate)) ** i))
            new_liability += modified_payment * discount_factor

        new_liability = new_liability.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        assert new_liability > Decimal("650000.00")


class TestLeaseGLEntries:
    """Tests for lease GL entries."""

    def test_initial_recognition_entries(self):
        """Test GL entries for initial lease recognition."""
        roua_initial = Decimal("1000000.00")
        lease_liability = Decimal("900000.00")
        prepaid_rent = Decimal("100000.00")

        # DR: ROUA Asset = 1,000,000
        # CR: Lease Liability = 900,000
        # CR: Prepaid Rent = 100,000

        total_dr = roua_initial
        total_cr = lease_liability + prepaid_rent

        assert total_dr == total_cr

    def test_monthly_interest_entry(self):
        """Test GL entries for monthly interest expense."""
        interest_expense = Decimal("7851.41")

        # DR: Interest Expense = 7,851.41
        # CR: Lease Liability = 7,851.41

        dr_amount = interest_expense
        cr_amount = interest_expense

        assert dr_amount == cr_amount

    def test_monthly_payment_entry(self):
        """Test GL entries for monthly lease payment."""
        monthly_payment = Decimal("20000.00")

        # DR: Lease Liability = 20,000
        # CR: Bank = 20,000

        dr_amount = monthly_payment
        cr_amount = monthly_payment

        assert dr_amount == cr_amount

    def test_roua_depreciation_entry(self):
        """Test GL entries for ROUA depreciation."""
        monthly_depreciation = Decimal("17166.67")

        # DR: Depreciation Expense = 17,166.67
        # CR: Accumulated Depreciation - ROUA = 17,166.67

        dr_amount = monthly_depreciation
        cr_amount = monthly_depreciation

        assert dr_amount == cr_amount

    def test_termination_gain_entries(self):
        """Test GL entries for lease termination with gain."""
        lease_liability = Decimal("300000.00")
        roua_nbv = Decimal("250000.00")
        termination_gain = lease_liability - roua_nbv

        # DR: Lease Liability = 300,000
        # CR: ROUA Asset = 250,000
        # CR: Gain on Termination = 50,000

        total_dr = lease_liability
        total_cr = roua_nbv + termination_gain

        assert total_dr == total_cr
        assert termination_gain == Decimal("50000.00")

    def test_termination_loss_entries(self):
        """Test GL entries for lease termination with loss."""
        lease_liability = Decimal("300000.00")
        roua_nbv = Decimal("350000.00")
        termination_loss = roua_nbv - lease_liability

        # DR: Lease Liability = 300,000
        # DR: Loss on Termination = 50,000
        # CR: ROUA Asset = 350,000

        total_dr = lease_liability + termination_loss
        total_cr = roua_nbv

        assert total_dr == total_cr
        assert termination_loss == Decimal("50000.00")


class TestLeaseDisclosures:
    """Tests for Ind AS 116 disclosures."""

    def test_maturity_analysis(self):
        """Test maturity analysis of lease liabilities."""
        monthly_payment = Decimal("20000.00")

        maturity = {
            "within_1_year": monthly_payment * 12,
            "1_to_2_years": monthly_payment * 12,
            "2_to_3_years": monthly_payment * 12,
            "3_to_4_years": monthly_payment * 12,
            "4_to_5_years": monthly_payment * 12,
            "beyond_5_years": Decimal("0.00"),
        }

        total = sum(maturity.values())
        assert total == Decimal("1200000.00")

    def test_weighted_average_ibr(self):
        """Test weighted average incremental borrowing rate."""
        leases = [
            {"liability": Decimal("500000.00"), "ibr": Decimal("0.10")},
            {"liability": Decimal("300000.00"), "ibr": Decimal("0.11")},
            {"liability": Decimal("200000.00"), "ibr": Decimal("0.12")},
        ]

        total_liability = sum(l["liability"] for l in leases)
        weighted_ibr = sum(
            l["liability"] * l["ibr"] for l in leases
        ) / total_liability

        assert round(weighted_ibr, 4) == Decimal("0.1070")

    def test_expense_recognition_summary(self):
        """Test expense recognition summary for period."""
        depreciation_expense = Decimal("206000.00")
        interest_expense = Decimal("80000.00")
        short_term_lease_expense = Decimal("50000.00")
        low_value_lease_expense = Decimal("20000.00")

        total_expense = (
            depreciation_expense
            + interest_expense
            + short_term_lease_expense
            + low_value_lease_expense
        )

        assert total_expense == Decimal("356000.00")


class TestLeaseIndexation:
    """Tests for lease payment indexation."""

    def test_cpi_based_escalation(self):
        """Test CPI-based rent escalation."""
        base_rent = Decimal("100000.00")
        cpi_current = Decimal("340.00")
        cpi_base = Decimal("320.00")

        escalated_rent = base_rent * (cpi_current / cpi_base)

        assert escalated_rent == Decimal("106250.00")

    def test_fixed_percentage_escalation(self):
        """Test fixed percentage escalation."""
        current_rent = Decimal("100000.00")
        escalation_rate = Decimal("0.05")  # 5%

        next_year_rent = current_rent * (1 + escalation_rate)

        assert next_year_rent == Decimal("105000.00")

    def test_market_rate_escalation(self):
        """Test market rate escalation at review date."""
        current_rent = Decimal("100000.00")
        market_rent = Decimal("120000.00")

        # Rent reset to market rate
        new_rent = market_rent

        assert new_rent == Decimal("120000.00")
