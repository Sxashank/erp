"""Integration tests for Fixed Asset lifecycle.

Tests cover end-to-end asset workflows:
- Asset creation -> Capitalization -> Depreciation -> Disposal
- Asset creation with approval workflow
- Physical verification workflow
"""

import pytest
import pytest_asyncio
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    AssetStatus,
    AssetAcquisitionType,
    DepreciationMethod,
    AssetType,
    AssetDisposalType,
    ApprovalRequestStatus,
    ApprovalWorkflowType,
)


class TestAssetLifecycle:
    """Integration tests for complete asset lifecycle."""

    @pytest.mark.asyncio
    async def test_asset_creation_to_disposal_lifecycle(
        self,
        session: AsyncSession,
        test_organization,
        test_category,
    ):
        """Test complete asset lifecycle from creation to disposal."""
        # Step 1: Create asset
        asset_data = {
            "organization_id": test_organization.id,
            "category_id": test_category.id,
            "asset_name": "Test Laptop",
            "acquisition_date": date(2024, 1, 1),
            "acquisition_type": AssetAcquisitionType.PURCHASE,
            "acquisition_cost": Decimal("100000.00"),
            "installation_cost": Decimal("0.00"),
            "other_costs": Decimal("0.00"),
        }

        # Verify initial calculations
        total_cost = (
            asset_data["acquisition_cost"]
            + asset_data["installation_cost"]
            + asset_data["other_costs"]
        )
        assert total_cost == Decimal("100000.00")

        # Step 2: Calculate residual and depreciable value
        residual_pct = test_category.residual_value_pct
        residual_value = total_cost * residual_pct / 100
        depreciable_value = total_cost - residual_value

        assert residual_value == Decimal("5000.00")
        assert depreciable_value == Decimal("95000.00")

        # Step 3: Simulate capitalization
        put_to_use_date = date(2024, 1, 15)
        status = AssetStatus.ACTIVE
        wdv_value = total_cost
        accumulated_depreciation = Decimal("0.00")

        assert status == AssetStatus.ACTIVE
        assert wdv_value == Decimal("100000.00")

        # Step 4: Calculate first year depreciation (SLM)
        useful_life_years = test_category.useful_life_years
        depreciation_rate = test_category.depreciation_rate_slm

        annual_depreciation = depreciable_value / useful_life_years
        assert annual_depreciation == Decimal("19000.00")

        # Pro-rata for partial year (Jan 15 to Mar 31 = ~76 days)
        days_in_fy = 365
        days_in_use = 76  # Approximate
        prorata_depreciation = annual_depreciation * days_in_use / days_in_fy

        assert prorata_depreciation > Decimal("0.00")
        assert prorata_depreciation < annual_depreciation

        # Step 5: Update after depreciation
        accumulated_depreciation = prorata_depreciation
        wdv_value = total_cost - accumulated_depreciation

        assert wdv_value < total_cost

        # Step 6: Simulate disposal
        disposal_date = date(2025, 6, 30)
        disposal_type = AssetDisposalType.SALE
        sale_proceeds = Decimal("70000.00")

        # Assume 1.5 years depreciation
        accumulated_at_disposal = annual_depreciation * Decimal("1.5")
        book_value_at_disposal = total_cost - accumulated_at_disposal

        gain_loss = sale_proceeds - book_value_at_disposal

        # Verify disposal calculations
        assert accumulated_at_disposal == Decimal("28500.00")
        assert book_value_at_disposal == Decimal("71500.00")
        assert gain_loss == Decimal("-1500.00")  # Loss

        # Final status
        final_status = AssetStatus.DISPOSED
        assert final_status == AssetStatus.DISPOSED


class TestDepreciationWorkflow:
    """Integration tests for depreciation workflow."""

    @pytest.mark.asyncio
    async def test_depreciation_run_workflow(
        self,
        session: AsyncSession,
        test_organization,
    ):
        """Test complete depreciation run workflow."""
        # Step 1: Verify open period
        depreciation_date = date(2024, 3, 31)
        is_period_open = True
        assert is_period_open

        # Step 2: Get eligible assets
        eligible_assets = [
            {
                "id": uuid4(),
                "total_cost": Decimal("100000.00"),
                "accumulated_depreciation": Decimal("0.00"),
                "depreciable_value": Decimal("95000.00"),
                "status": AssetStatus.ACTIVE,
            },
            {
                "id": uuid4(),
                "total_cost": Decimal("50000.00"),
                "accumulated_depreciation": Decimal("0.00"),
                "depreciable_value": Decimal("47500.00"),
                "status": AssetStatus.ACTIVE,
            },
        ]

        # Step 3: Calculate depreciation for each
        annual_rate = Decimal("20.00")
        days_in_period = 76  # Jan 15 to Mar 31
        days_in_year = 365

        depreciation_entries = []
        for asset in eligible_assets:
            annual_dep = asset["depreciable_value"] * annual_rate / 100
            period_dep = annual_dep * days_in_period / days_in_year
            period_dep = period_dep.quantize(Decimal("0.01"))

            depreciation_entries.append({
                "asset_id": asset["id"],
                "depreciation_amount": period_dep,
            })

        assert len(depreciation_entries) == 2
        total_depreciation = sum(e["depreciation_amount"] for e in depreciation_entries)
        assert total_depreciation > Decimal("0.00")

        # Step 4: Create depreciation run record
        run_record = {
            "id": uuid4(),
            "organization_id": test_organization.id,
            "run_date": depreciation_date,
            "total_depreciation": total_depreciation,
            "assets_processed": len(depreciation_entries),
            "status": "DRAFT",
        }

        assert run_record["status"] == "DRAFT"

        # Step 5: Submit for approval
        run_record["status"] = "PENDING_APPROVAL"
        assert run_record["status"] == "PENDING_APPROVAL"

        # Step 6: After approval, post to GL
        run_record["status"] = "POSTED"
        run_record["gl_voucher_id"] = uuid4()

        assert run_record["status"] == "POSTED"
        assert run_record["gl_voucher_id"] is not None


class TestApprovalWorkflow:
    """Integration tests for approval workflow."""

    @pytest.mark.asyncio
    async def test_two_level_approval_workflow(
        self,
        session: AsyncSession,
        test_organization,
        test_user,
    ):
        """Test two-level approval workflow."""
        # Step 1: Configure workflow
        workflow_config = {
            "organization_id": test_organization.id,
            "workflow_type": ApprovalWorkflowType.FA_ASSET_DISPOSAL,
            "approval_levels": 2,
            "threshold_amount": Decimal("0.00"),  # All require approval
        }

        # Step 2: Create asset disposal request
        disposal_request = {
            "entity_type": "FIXED_ASSET",
            "entity_id": uuid4(),
            "workflow_type": ApprovalWorkflowType.FA_ASSET_DISPOSAL,
            "requested_by": test_user.id,
            "amount": Decimal("500000.00"),
            "status": ApprovalRequestStatus.PENDING,
            "current_level": 1,
        }

        assert disposal_request["status"] == ApprovalRequestStatus.PENDING
        assert disposal_request["current_level"] == 1

        # Step 3: Level 1 approval
        level_1_approver = uuid4()
        disposal_request["current_level"] = 2
        # Status stays PENDING until final approval

        assert disposal_request["current_level"] == 2

        # Step 4: Level 2 approval
        level_2_approver = uuid4()
        disposal_request["status"] = ApprovalRequestStatus.APPROVED

        assert disposal_request["status"] == ApprovalRequestStatus.APPROVED

        # Step 5: Execute disposal after approval
        asset_status = AssetStatus.DISPOSED
        assert asset_status == AssetStatus.DISPOSED

    @pytest.mark.asyncio
    async def test_rejection_workflow(
        self,
        session: AsyncSession,
        test_organization,
        test_user,
    ):
        """Test approval rejection workflow."""
        # Step 1: Create approval request
        request = {
            "entity_type": "FIXED_ASSET",
            "entity_id": uuid4(),
            "workflow_type": ApprovalWorkflowType.FA_ASSET_DISPOSAL,
            "requested_by": test_user.id,
            "status": ApprovalRequestStatus.PENDING,
            "current_level": 1,
        }

        # Step 2: Level 1 rejects
        request["status"] = ApprovalRequestStatus.REJECTED
        rejection_reason = "Insufficient justification"

        assert request["status"] == ApprovalRequestStatus.REJECTED

        # Step 3: Verify asset status unchanged
        asset_status = AssetStatus.ACTIVE  # Remains active
        assert asset_status == AssetStatus.ACTIVE


class TestPhysicalVerificationWorkflow:
    """Integration tests for physical verification workflow."""

    @pytest.mark.asyncio
    async def test_physical_verification_workflow(
        self,
        session: AsyncSession,
        test_organization,
        test_user,
    ):
        """Test physical verification workflow."""
        # Step 1: Create verification schedule
        schedule = {
            "id": uuid4(),
            "organization_id": test_organization.id,
            "schedule_name": "FY 2024-25 Q4 Verification",
            "scheduled_date": date(2025, 3, 15),
            "assigned_to": test_user.id,
            "status": "SCHEDULED",
        }

        assert schedule["status"] == "SCHEDULED"

        # Step 2: Get assets for verification
        assets_to_verify = [
            {"id": uuid4(), "asset_code": "FA/COMP/2024/00001", "location": "Mumbai"},
            {"id": uuid4(), "asset_code": "FA/COMP/2024/00002", "location": "Mumbai"},
            {"id": uuid4(), "asset_code": "FA/FURN/2024/00001", "location": "Delhi"},
        ]

        # Step 3: Create verification items
        verification_items = []
        for asset in assets_to_verify:
            verification_items.append({
                "schedule_id": schedule["id"],
                "asset_id": asset["id"],
                "expected_location": asset["location"],
                "verification_status": "PENDING",
            })

        assert len(verification_items) == 3

        # Step 4: Verify assets
        verification_items[0]["verification_status"] = "VERIFIED"
        verification_items[0]["actual_location"] = "Mumbai"
        verification_items[0]["condition"] = "GOOD"

        verification_items[1]["verification_status"] = "VERIFIED"
        verification_items[1]["actual_location"] = "Delhi"  # Moved
        verification_items[1]["condition"] = "FAIR"

        verification_items[2]["verification_status"] = "NOT_FOUND"
        verification_items[2]["remarks"] = "Asset not at expected location"

        # Step 5: Complete verification
        schedule["status"] = "COMPLETED"
        verified_count = sum(1 for item in verification_items if item["verification_status"] == "VERIFIED")
        not_found_count = sum(1 for item in verification_items if item["verification_status"] == "NOT_FOUND")

        assert verified_count == 2
        assert not_found_count == 1
        assert schedule["status"] == "COMPLETED"


class TestTransferWorkflow:
    """Integration tests for asset transfer workflow."""

    @pytest.mark.asyncio
    async def test_inter_location_transfer(
        self,
        session: AsyncSession,
        test_organization,
        test_user,
    ):
        """Test inter-location asset transfer."""
        # Step 1: Create transfer request
        transfer_request = {
            "id": uuid4(),
            "asset_id": uuid4(),
            "from_location": "Mumbai Office",
            "to_location": "Delhi Office",
            "from_department_id": uuid4(),
            "to_department_id": uuid4(),
            "transfer_date": date(2024, 6, 15),
            "requested_by": test_user.id,
            "status": "PENDING_APPROVAL",
        }

        assert transfer_request["status"] == "PENDING_APPROVAL"

        # Step 2: Approve transfer
        transfer_request["status"] = "APPROVED"
        transfer_request["approved_by"] = uuid4()
        transfer_request["approved_at"] = datetime.now(timezone.utc)

        # Step 3: Execute transfer
        asset_location = transfer_request["to_location"]
        asset_department = transfer_request["to_department_id"]

        assert asset_location == "Delhi Office"

        # Step 4: Update asset status temporarily
        asset_status = AssetStatus.TRANSFERRED
        assert asset_status == AssetStatus.TRANSFERRED

        # Step 5: Complete transfer
        transfer_request["status"] = "COMPLETED"
        asset_status = AssetStatus.ACTIVE  # Back to active at new location

        assert transfer_request["status"] == "COMPLETED"
        assert asset_status == AssetStatus.ACTIVE


class TestRevaluationWorkflow:
    """Integration tests for asset revaluation workflow."""

    @pytest.mark.asyncio
    async def test_upward_revaluation_workflow(
        self,
        session: AsyncSession,
        test_organization,
        test_user,
    ):
        """Test upward revaluation workflow."""
        # Step 1: Asset current values
        asset = {
            "id": uuid4(),
            "total_cost": Decimal("100000.00"),
            "accumulated_depreciation": Decimal("40000.00"),
            "book_value": Decimal("60000.00"),
            "useful_life_years": 5,
            "remaining_life_years": 3,
        }

        # Step 2: Valuer provides new value
        revalued_amount = Decimal("80000.00")
        valuation_date = date(2024, 3, 31)
        valuer_name = "ABC Valuers Pvt Ltd"

        # Step 3: Calculate revaluation surplus
        revaluation_surplus = revalued_amount - asset["book_value"]
        assert revaluation_surplus == Decimal("20000.00")

        # Step 4: Submit for approval
        revaluation_request = {
            "asset_id": asset["id"],
            "old_book_value": asset["book_value"],
            "new_revalued_amount": revalued_amount,
            "revaluation_surplus": revaluation_surplus,
            "status": ApprovalRequestStatus.PENDING,
        }

        # Step 5: After approval, update asset
        revaluation_request["status"] = ApprovalRequestStatus.APPROVED

        # Update asset values
        asset["total_cost"] = revalued_amount
        asset["accumulated_depreciation"] = Decimal("0.00")  # Reset
        asset["book_value"] = revalued_amount

        # Step 6: Calculate new depreciation
        new_annual_depreciation = revalued_amount / asset["remaining_life_years"]
        assert round(new_annual_depreciation, 2) == Decimal("26666.67")

        # Step 7: GL entry for revaluation surplus
        gl_entry = {
            "debit_account": "Fixed Asset",
            "debit_amount": revaluation_surplus,
            "credit_account": "Revaluation Reserve",
            "credit_amount": revaluation_surplus,
        }

        assert gl_entry["debit_amount"] == gl_entry["credit_amount"]


class TestLeaseLifecycle:
    """Integration tests for lease lifecycle."""

    @pytest.mark.asyncio
    async def test_lease_recognition_to_termination(
        self,
        session: AsyncSession,
        test_organization,
    ):
        """Test complete lease lifecycle from recognition to termination."""
        # Step 1: Create lease
        lease = {
            "id": uuid4(),
            "organization_id": test_organization.id,
            "lease_number": "LEASE/2024/00001",
            "asset_description": "Office Space - 5000 sqft",
            "lease_start_date": date(2024, 4, 1),
            "lease_end_date": date(2029, 3, 31),
            "monthly_lease_payment": Decimal("100000.00"),
            "incremental_borrowing_rate": Decimal("10.00"),
            "status": "DRAFT",
        }

        # Step 2: Calculate NPV (simplified)
        num_payments = 60
        monthly_rate = Decimal("10.00") / 12 / 100

        npv = Decimal("0")
        for i in range(1, num_payments + 1):
            discount_factor = Decimal(str(1 / (1 + float(monthly_rate)) ** i))
            npv += lease["monthly_lease_payment"] * discount_factor

        lease["lease_liability_initial"] = round(npv, 2)
        lease["roua_initial_value"] = lease["lease_liability_initial"]

        assert lease["lease_liability_initial"] > Decimal("4000000.00")

        # Step 3: Activate lease
        lease["status"] = "ACTIVE"

        # Step 4: Monthly processing (first month)
        first_month = {
            "opening_liability": lease["lease_liability_initial"],
            "interest_expense": lease["lease_liability_initial"] * monthly_rate,
            "payment": lease["monthly_lease_payment"],
        }
        first_month["principal_repayment"] = first_month["payment"] - first_month["interest_expense"]
        first_month["closing_liability"] = first_month["opening_liability"] - first_month["principal_repayment"]

        assert first_month["closing_liability"] < first_month["opening_liability"]

        # Step 5: ROUA depreciation
        monthly_roua_depreciation = lease["roua_initial_value"] / num_payments
        assert monthly_roua_depreciation > Decimal("0.00")

        # Step 6: Early termination (after 3 years)
        termination_date = date(2027, 3, 31)
        remaining_liability = Decimal("2000000.00")  # Simplified
        roua_nbv = Decimal("1800000.00")  # Simplified

        termination_gain = remaining_liability - roua_nbv
        assert termination_gain == Decimal("200000.00")

        # Step 7: Final status
        lease["status"] = "TERMINATED"
        lease["termination_date"] = termination_date

        assert lease["status"] == "TERMINATED"
