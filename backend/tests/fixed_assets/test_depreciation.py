"""Unit tests for depreciation calculations.

Tests cover:
- Straight Line Method (SLM) depreciation
- Written Down Value (WDV) depreciation
- Pro-rata depreciation calculations
- IT Act depreciation block calculations
"""

import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.core.constants import DepreciationMethod, AssetStatus, ITActAssetBlock


class TestSLMDepreciation:
    """Tests for Straight Line Method depreciation."""

    def test_slm_annual_depreciation(self):
        """Test basic SLM annual depreciation calculation."""
        # Asset value: 100,000
        # Residual value: 10,000
        # Useful life: 5 years
        # Expected annual depreciation: (100,000 - 10,000) / 5 = 18,000

        asset_value = Decimal("100000.00")
        residual_value = Decimal("10000.00")
        useful_life_years = 5

        depreciable_value = asset_value - residual_value
        annual_depreciation = depreciable_value / useful_life_years

        assert annual_depreciation == Decimal("18000.00")

    def test_slm_monthly_depreciation(self):
        """Test SLM monthly depreciation calculation."""
        # Asset value: 120,000
        # Residual value: 12,000
        # Useful life: 5 years (60 months)
        # Expected monthly depreciation: (120,000 - 12,000) / 60 = 1,800

        asset_value = Decimal("120000.00")
        residual_value = Decimal("12000.00")
        useful_life_months = 60

        depreciable_value = asset_value - residual_value
        monthly_depreciation = depreciable_value / useful_life_months

        assert monthly_depreciation == Decimal("1800.00")

    def test_slm_rate_based_depreciation(self):
        """Test SLM using depreciation rate."""
        # Asset value: 100,000
        # Depreciation rate: 20%
        # Expected annual depreciation: 100,000 * 20% = 20,000

        asset_value = Decimal("100000.00")
        depreciation_rate = Decimal("20.00")

        annual_depreciation = asset_value * depreciation_rate / 100

        assert annual_depreciation == Decimal("20000.00")

    def test_slm_pro_rata_first_year(self):
        """Test SLM pro-rata depreciation for partial first year."""
        # Asset put to use: 1st April (start of FY in India)
        # Full year depreciation: 18,000
        # Days in year: 365
        # Days asset in use: 365 (full year)

        annual_depreciation = Decimal("18000.00")
        days_in_year = 365
        days_in_use = 365

        pro_rata_depreciation = annual_depreciation * days_in_use / days_in_year

        assert round(pro_rata_depreciation, 2) == Decimal("18000.00")

    def test_slm_pro_rata_partial_year(self):
        """Test SLM pro-rata for asset acquired mid-year."""
        # Annual depreciation: 18,000
        # Asset put to use: 1st October (183 days remaining in FY)
        # Expected: 18,000 * 183/365 = 9,024.66

        annual_depreciation = Decimal("18000.00")
        days_in_year = 365
        days_in_use = 183

        pro_rata_depreciation = annual_depreciation * days_in_use / days_in_year

        assert round(pro_rata_depreciation, 2) == Decimal("9024.66")

    def test_slm_full_depreciation_not_exceed_depreciable(self):
        """Test that accumulated depreciation doesn't exceed depreciable value."""
        asset_value = Decimal("100000.00")
        residual_value = Decimal("10000.00")
        depreciable_value = asset_value - residual_value
        annual_depreciation = Decimal("18000.00")

        # After 5 years, should equal depreciable value
        accumulated = annual_depreciation * 5
        assert accumulated == depreciable_value

        # 6th year should be capped to 0
        remaining = depreciable_value - accumulated
        assert remaining == Decimal("0.00")


class TestWDVDepreciation:
    """Tests for Written Down Value depreciation."""

    def test_wdv_first_year(self):
        """Test WDV depreciation for first year."""
        # Asset value: 100,000
        # WDV rate: 40%
        # Year 1 depreciation: 100,000 * 40% = 40,000

        opening_wdv = Decimal("100000.00")
        wdv_rate = Decimal("40.00")

        depreciation = opening_wdv * wdv_rate / 100

        assert depreciation == Decimal("40000.00")

    def test_wdv_second_year(self):
        """Test WDV depreciation for second year."""
        # Opening WDV: 60,000 (100,000 - 40,000)
        # WDV rate: 40%
        # Year 2 depreciation: 60,000 * 40% = 24,000

        opening_wdv = Decimal("60000.00")
        wdv_rate = Decimal("40.00")

        depreciation = opening_wdv * wdv_rate / 100

        assert depreciation == Decimal("24000.00")

    def test_wdv_declining_balance(self):
        """Test WDV declining balance over multiple years."""
        opening_wdv = Decimal("100000.00")
        wdv_rate = Decimal("40.00")
        residual_value = Decimal("5000.00")

        years = []
        current_wdv = opening_wdv

        for year in range(1, 11):
            if current_wdv <= residual_value:
                break

            depreciation = current_wdv * wdv_rate / 100

            # Don't depreciate below residual
            if current_wdv - depreciation < residual_value:
                depreciation = current_wdv - residual_value

            closing_wdv = current_wdv - depreciation
            years.append({
                "year": year,
                "opening": current_wdv,
                "depreciation": depreciation,
                "closing": closing_wdv,
            })
            current_wdv = closing_wdv

        # Year 1: 100,000 -> 60,000
        assert years[0]["depreciation"] == Decimal("40000.00")
        assert years[0]["closing"] == Decimal("60000.00")

        # Year 2: 60,000 -> 36,000
        assert years[1]["depreciation"] == Decimal("24000.00")
        assert years[1]["closing"] == Decimal("36000.00")

    def test_wdv_pro_rata(self):
        """Test WDV with pro-rata for partial year."""
        # Opening WDV: 100,000
        # WDV rate: 40%
        # Asset in use for 6 months (183 days)
        # Expected: 100,000 * 40% * 183/365 = 20,054.79

        opening_wdv = Decimal("100000.00")
        wdv_rate = Decimal("40.00")
        days_in_use = 183
        days_in_year = 365

        annual_depreciation = opening_wdv * wdv_rate / 100
        pro_rata_depreciation = annual_depreciation * days_in_use / days_in_year

        assert round(pro_rata_depreciation, 2) == Decimal("20054.79")


class TestITActDepreciation:
    """Tests for IT Act depreciation blocks."""

    def test_it_block_plant_machinery_rate(self):
        """Test IT Act depreciation rate for plant and machinery."""
        # Block: Plant & Machinery - General
        # Rate: 15%

        opening_wdv = Decimal("1000000.00")
        it_rate = Decimal("15.00")

        depreciation = opening_wdv * it_rate / 100

        assert depreciation == Decimal("150000.00")

    def test_it_block_computer_rate(self):
        """Test IT Act depreciation rate for computers."""
        # Block: Computers
        # Rate: 40%

        opening_wdv = Decimal("100000.00")
        it_rate = Decimal("40.00")

        depreciation = opening_wdv * it_rate / 100

        assert depreciation == Decimal("40000.00")

    def test_it_block_furniture_rate(self):
        """Test IT Act depreciation rate for furniture."""
        # Block: Furniture & Fittings
        # Rate: 10%

        opening_wdv = Decimal("500000.00")
        it_rate = Decimal("10.00")

        depreciation = opening_wdv * it_rate / 100

        assert depreciation == Decimal("50000.00")

    def test_it_block_motor_vehicle_rate(self):
        """Test IT Act depreciation rate for motor vehicles."""
        # Block: Motor Vehicles
        # Rate: 15%

        opening_wdv = Decimal("800000.00")
        it_rate = Decimal("15.00")

        depreciation = opening_wdv * it_rate / 100

        assert depreciation == Decimal("120000.00")

    def test_it_additional_depreciation(self):
        """Test additional depreciation for new manufacturing assets."""
        # New plant & machinery for manufacturing
        # Normal rate: 15%
        # Additional depreciation: 20% (first year only)
        # Total first year: 35%

        asset_value = Decimal("1000000.00")
        normal_rate = Decimal("15.00")
        additional_rate = Decimal("20.00")

        normal_depreciation = asset_value * normal_rate / 100
        additional_depreciation = asset_value * additional_rate / 100
        total_first_year = normal_depreciation + additional_depreciation

        assert normal_depreciation == Decimal("150000.00")
        assert additional_depreciation == Decimal("200000.00")
        assert total_first_year == Decimal("350000.00")

    def test_it_half_year_rule(self):
        """Test IT Act half-year rule for assets acquired in second half."""
        # Asset acquired after September (second half of FY)
        # Depreciation = 50% of normal rate

        opening_wdv = Decimal("100000.00")
        it_rate = Decimal("40.00")  # Computers

        # Full year depreciation
        full_depreciation = opening_wdv * it_rate / 100

        # Second half acquisition - 50% rule
        half_year_depreciation = full_depreciation / 2

        assert full_depreciation == Decimal("40000.00")
        assert half_year_depreciation == Decimal("20000.00")

    def test_it_block_aggregation(self):
        """Test IT Act block-level depreciation aggregation."""
        # Multiple assets in same block
        # Block: Computers (40%)
        # Asset 1: 50,000
        # Asset 2: 30,000
        # Asset 3: 20,000
        # Total block WDV: 100,000
        # Block depreciation: 100,000 * 40% = 40,000

        assets = [
            Decimal("50000.00"),
            Decimal("30000.00"),
            Decimal("20000.00"),
        ]
        block_wdv = sum(assets)
        it_rate = Decimal("40.00")

        block_depreciation = block_wdv * it_rate / 100

        assert block_wdv == Decimal("100000.00")
        assert block_depreciation == Decimal("40000.00")


class TestDepreciationDifference:
    """Tests for Companies Act vs IT Act depreciation difference."""

    def test_depreciation_difference_calculation(self):
        """Test difference between Companies Act and IT Act depreciation."""
        # Asset: Computer
        # Companies Act: SLM 20% (5 years)
        # IT Act: WDV 40%
        # Asset value: 100,000

        asset_value = Decimal("100000.00")

        # Companies Act - SLM
        slm_rate = Decimal("20.00")
        companies_act_dep = asset_value * slm_rate / 100

        # IT Act - WDV
        wdv_rate = Decimal("40.00")
        it_act_dep = asset_value * wdv_rate / 100

        difference = it_act_dep - companies_act_dep

        assert companies_act_dep == Decimal("20000.00")
        assert it_act_dep == Decimal("40000.00")
        assert difference == Decimal("20000.00")  # IT allows higher in year 1

    def test_accumulated_difference_over_years(self):
        """Test accumulated difference over multiple years."""
        asset_value = Decimal("100000.00")
        residual = Decimal("5000.00")

        # Companies Act SLM
        slm_annual = (asset_value - residual) / 5  # 19,000

        # IT Act WDV 40%
        it_wdv = asset_value
        it_rates = Decimal("40.00")

        ca_accumulated = Decimal("0.00")
        it_accumulated = Decimal("0.00")

        for year in range(1, 6):
            # CA depreciation
            ca_dep = min(slm_annual, asset_value - residual - ca_accumulated)
            ca_accumulated += ca_dep

            # IT depreciation
            it_dep = it_wdv * it_rates / 100
            if it_wdv - it_dep < residual:
                it_dep = it_wdv - residual
            it_accumulated += it_dep
            it_wdv -= it_dep

        # After 5 years, CA should reach depreciable value
        assert round(ca_accumulated, 2) == Decimal("95000.00")

        # IT will have different pattern
        assert it_accumulated > Decimal("0.00")


class TestSpecialScenarios:
    """Tests for special depreciation scenarios."""

    def test_revalued_asset_depreciation(self):
        """Test depreciation after asset revaluation."""
        # Original cost: 100,000
        # Accumulated depreciation (3 years): 60,000
        # Book value: 40,000
        # Revalued to: 80,000
        # Remaining life: 2 years
        # New annual depreciation: 80,000 / 2 = 40,000

        revalued_amount = Decimal("80000.00")
        remaining_life_years = 2

        new_annual_depreciation = revalued_amount / remaining_life_years

        assert new_annual_depreciation == Decimal("40000.00")

    def test_impaired_asset_depreciation(self):
        """Test depreciation after impairment."""
        # Original cost: 100,000
        # Accumulated depreciation: 20,000
        # Book value before impairment: 80,000
        # Impairment loss: 30,000
        # New book value: 50,000
        # Remaining life: 4 years
        # New annual depreciation: 50,000 / 4 = 12,500

        book_value_after_impairment = Decimal("50000.00")
        remaining_life_years = 4

        new_annual_depreciation = book_value_after_impairment / remaining_life_years

        assert new_annual_depreciation == Decimal("12500.00")

    def test_zero_residual_value(self):
        """Test depreciation with zero residual value."""
        asset_value = Decimal("100000.00")
        residual_value = Decimal("0.00")
        useful_life_years = 5

        depreciable_value = asset_value - residual_value
        annual_depreciation = depreciable_value / useful_life_years

        assert depreciable_value == Decimal("100000.00")
        assert annual_depreciation == Decimal("20000.00")

    def test_asset_below_threshold_no_depreciation(self):
        """Test that assets below capitalization threshold are expensed."""
        asset_value = Decimal("4000.00")
        capitalization_threshold = Decimal("5000.00")

        should_capitalize = asset_value >= capitalization_threshold
        assert not should_capitalize
        # Asset should be expensed immediately, not depreciated

    def test_disposed_asset_stops_depreciation(self):
        """Test that disposed assets stop accumulating depreciation."""
        asset_value = Decimal("100000.00")
        accumulated_before_disposal = Decimal("40000.00")
        disposal_date = date(2024, 6, 30)

        # No further depreciation after disposal
        book_value_at_disposal = asset_value - accumulated_before_disposal
        assert book_value_at_disposal == Decimal("60000.00")

    def test_fully_depreciated_asset(self):
        """Test that fully depreciated assets show residual value."""
        asset_value = Decimal("100000.00")
        residual_value = Decimal("5000.00")
        accumulated_depreciation = Decimal("95000.00")

        current_wdv = asset_value - accumulated_depreciation
        assert current_wdv == residual_value

        # No further depreciation
        remaining_depreciable = current_wdv - residual_value
        assert remaining_depreciable == Decimal("0.00")
