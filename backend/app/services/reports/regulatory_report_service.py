"""
Regulatory Report Service
Generates various regulatory reports required by RBI and other regulators for NBFCs
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending.loan_account import LoanAccount
from app.models.lending.npa import NPAClassification
from app.models.lending.receipt import LoanReceipt


class RegulatoryReportService:
    """Service for generating regulatory reports"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_alm_report(
        self,
        org_id: UUID,
        as_of_date: date,
        report_type: str = "STRUCTURAL"
    ) -> Dict[str, Any]:
        """
        Generate Asset Liability Management (ALM) Report
        Shows maturity profile of assets and liabilities
        """
        # Define time buckets as per RBI guidelines
        buckets = [
            {"name": "1-7 days", "days_from": 1, "days_to": 7},
            {"name": "8-14 days", "days_from": 8, "days_to": 14},
            {"name": "15-30 days", "days_from": 15, "days_to": 30},
            {"name": "31-60 days", "days_from": 31, "days_to": 60},
            {"name": "61-90 days", "days_from": 61, "days_to": 90},
            {"name": "91-180 days", "days_from": 91, "days_to": 180},
            {"name": "181-365 days", "days_from": 181, "days_to": 365},
            {"name": "1-3 years", "days_from": 366, "days_to": 1095},
            {"name": "3-5 years", "days_from": 1096, "days_to": 1825},
            {"name": "Over 5 years", "days_from": 1826, "days_to": 99999},
        ]

        alm_data = []
        for bucket in buckets:
            bucket_start = as_of_date + timedelta(days=bucket["days_from"])
            bucket_end = as_of_date + timedelta(days=bucket["days_to"])

            # Calculate assets maturing in this bucket (loan principal + interest due)
            assets = await self._calculate_assets_in_bucket(
                org_id, bucket_start, bucket_end
            )

            # Calculate liabilities maturing in this bucket (borrowings, FDs)
            liabilities = await self._calculate_liabilities_in_bucket(
                org_id, bucket_start, bucket_end
            )

            gap = assets - liabilities
            cumulative_gap = gap  # Would need running total in real implementation

            alm_data.append({
                "bucket": bucket["name"],
                "assets": float(assets),
                "liabilities": float(liabilities),
                "gap": float(gap),
                "cumulative_gap": float(cumulative_gap),
                "gap_percentage": float(gap / assets * 100) if assets > 0 else 0,
            })

        return {
            "report_type": "ALM_STRUCTURAL",
            "as_of_date": as_of_date.isoformat(),
            "generated_at": datetime.now().isoformat(),
            "buckets": alm_data,
            "summary": {
                "total_assets": sum(b["assets"] for b in alm_data),
                "total_liabilities": sum(b["liabilities"] for b in alm_data),
                "net_gap": sum(b["gap"] for b in alm_data),
            }
        }

    async def generate_npa_report(
        self,
        org_id: UUID,
        as_of_date: date,
        detailed: bool = False
    ) -> Dict[str, Any]:
        """
        Generate NPA Report as per RBI IRAC norms
        Shows classification of assets and provisioning
        """
        # NPA categories as per RBI
        categories = [
            {"code": "STD", "name": "Standard Assets", "provision_rate": 0.40},
            {"code": "SMA0", "name": "SMA-0 (1-30 days)", "provision_rate": 0.40},
            {"code": "SMA1", "name": "SMA-1 (31-60 days)", "provision_rate": 0.40},
            {"code": "SMA2", "name": "SMA-2 (61-90 days)", "provision_rate": 0.40},
            {"code": "SUB", "name": "Sub-Standard (91-365 days)", "provision_rate": 15.0},
            {"code": "DBT", "name": "Doubtful 1 (1-2 years)", "provision_rate": 25.0},
            {"code": "DBT2", "name": "Doubtful 2 (2-3 years)", "provision_rate": 40.0},
            {"code": "DBT3", "name": "Doubtful 3 (>3 years)", "provision_rate": 100.0},
            {"code": "LOSS", "name": "Loss Assets", "provision_rate": 100.0},
        ]

        npa_data = []
        total_advances = Decimal("0")
        total_npa = Decimal("0")
        total_provision = Decimal("0")

        for category in categories:
            # Get accounts in this category
            count, outstanding, provision = await self._get_npa_category_data(
                org_id, category["code"], as_of_date
            )

            total_advances += outstanding
            if category["code"] not in ["STD", "SMA0", "SMA1", "SMA2"]:
                total_npa += outstanding

            total_provision += provision

            npa_data.append({
                "category_code": category["code"],
                "category_name": category["name"],
                "account_count": count,
                "outstanding_amount": float(outstanding),
                "provision_rate": category["provision_rate"],
                "provision_amount": float(provision),
            })

        gross_npa_ratio = (total_npa / total_advances * 100) if total_advances > 0 else 0
        net_npa = total_npa - total_provision
        net_npa_ratio = (net_npa / (total_advances - total_provision) * 100) if (total_advances - total_provision) > 0 else 0

        return {
            "report_type": "NPA_CLASSIFICATION",
            "as_of_date": as_of_date.isoformat(),
            "generated_at": datetime.now().isoformat(),
            "categories": npa_data,
            "summary": {
                "total_advances": float(total_advances),
                "gross_npa": float(total_npa),
                "gross_npa_ratio": float(gross_npa_ratio),
                "total_provision": float(total_provision),
                "net_npa": float(net_npa),
                "net_npa_ratio": float(net_npa_ratio),
            }
        }

    async def generate_crar_report(
        self,
        org_id: UUID,
        as_of_date: date
    ) -> Dict[str, Any]:
        """
        Generate Capital to Risk Assets Ratio (CRAR) Report
        Also known as Capital Adequacy Ratio (CAR)
        """
        # Get capital components (simplified - would need proper GL integration)
        tier1_capital = await self._get_tier1_capital(org_id, as_of_date)
        tier2_capital = await self._get_tier2_capital(org_id, as_of_date)
        total_capital = tier1_capital + tier2_capital

        # Get risk weighted assets
        rwa = await self._calculate_risk_weighted_assets(org_id, as_of_date)

        crar = (total_capital / rwa * 100) if rwa > 0 else 0
        tier1_ratio = (tier1_capital / rwa * 100) if rwa > 0 else 0

        return {
            "report_type": "CRAR",
            "as_of_date": as_of_date.isoformat(),
            "generated_at": datetime.now().isoformat(),
            "capital": {
                "tier1_capital": float(tier1_capital),
                "tier2_capital": float(tier2_capital),
                "total_capital": float(total_capital),
            },
            "risk_weighted_assets": {
                "credit_risk_rwa": float(rwa * Decimal("0.85")),
                "market_risk_rwa": float(rwa * Decimal("0.10")),
                "operational_risk_rwa": float(rwa * Decimal("0.05")),
                "total_rwa": float(rwa),
            },
            "ratios": {
                "crar": float(crar),
                "tier1_ratio": float(tier1_ratio),
                "minimum_crar_required": 15.0,  # As per RBI for NBFCs
                "surplus_deficit": float(crar - 15.0),
            }
        }

    async def generate_liquidity_report(
        self,
        org_id: UUID,
        as_of_date: date
    ) -> Dict[str, Any]:
        """
        Generate Liquidity Coverage Ratio (LCR) Report
        """
        # High Quality Liquid Assets (HQLA)
        hqla = await self._calculate_hqla(org_id, as_of_date)

        # Net Cash Outflows over 30 days
        cash_outflows = await self._calculate_cash_outflows(org_id, as_of_date)
        cash_inflows = await self._calculate_cash_inflows(org_id, as_of_date)
        net_outflows = cash_outflows - min(cash_inflows, cash_outflows * Decimal("0.75"))

        lcr = (hqla / net_outflows * 100) if net_outflows > 0 else 0

        return {
            "report_type": "LIQUIDITY_COVERAGE",
            "as_of_date": as_of_date.isoformat(),
            "generated_at": datetime.now().isoformat(),
            "hqla": {
                "level1_assets": float(hqla * Decimal("0.7")),
                "level2a_assets": float(hqla * Decimal("0.2")),
                "level2b_assets": float(hqla * Decimal("0.1")),
                "total_hqla": float(hqla),
            },
            "cash_flows": {
                "total_outflows": float(cash_outflows),
                "total_inflows": float(cash_inflows),
                "net_outflows": float(net_outflows),
            },
            "ratios": {
                "lcr": float(lcr),
                "minimum_lcr_required": 100.0,
                "surplus_deficit": float(lcr - 100.0),
            }
        }

    async def generate_large_exposure_report(
        self,
        org_id: UUID,
        as_of_date: date,
        threshold_percentage: float = 10.0
    ) -> Dict[str, Any]:
        """
        Generate Large Exposure Report
        Shows borrowers with exposure exceeding threshold % of capital
        """
        tier1_capital = await self._get_tier1_capital(org_id, as_of_date)
        threshold_amount = tier1_capital * Decimal(str(threshold_percentage / 100))

        # Get large exposures
        large_exposures = await self._get_large_exposures(
            org_id, as_of_date, threshold_amount
        )

        return {
            "report_type": "LARGE_EXPOSURE",
            "as_of_date": as_of_date.isoformat(),
            "generated_at": datetime.now().isoformat(),
            "tier1_capital": float(tier1_capital),
            "threshold_percentage": threshold_percentage,
            "threshold_amount": float(threshold_amount),
            "exposures": large_exposures,
            "summary": {
                "count": len(large_exposures),
                "total_exposure": sum(e["exposure_amount"] for e in large_exposures),
            }
        }

    async def generate_sector_exposure_report(
        self,
        org_id: UUID,
        as_of_date: date
    ) -> Dict[str, Any]:
        """
        Generate Sector-wise Exposure Report
        Shows concentration of advances across sectors
        """
        sectors = [
            "Agriculture",
            "Manufacturing",
            "Trade",
            "Services",
            "Personal Loans",
            "Real Estate",
            "MSME",
            "Others",
        ]

        sector_data = []
        total_advances = Decimal("0")

        for sector in sectors:
            amount = await self._get_sector_exposure(org_id, sector, as_of_date)
            total_advances += amount
            sector_data.append({
                "sector": sector,
                "exposure_amount": float(amount),
            })

        # Calculate percentages
        for item in sector_data:
            item["percentage"] = (
                item["exposure_amount"] / float(total_advances) * 100
                if total_advances > 0 else 0
            )

        return {
            "report_type": "SECTOR_EXPOSURE",
            "as_of_date": as_of_date.isoformat(),
            "generated_at": datetime.now().isoformat(),
            "sectors": sector_data,
            "total_advances": float(total_advances),
        }

    # Helper methods (simplified implementations)
    async def _calculate_assets_in_bucket(
        self, org_id: UUID, start_date: date, end_date: date
    ) -> Decimal:
        """Calculate assets maturing in given date range"""
        # Simplified - would query loan schedules
        return Decimal("10000000")

    async def _calculate_liabilities_in_bucket(
        self, org_id: UUID, start_date: date, end_date: date
    ) -> Decimal:
        """Calculate liabilities maturing in given date range"""
        return Decimal("8000000")

    async def _get_npa_category_data(
        self, org_id: UUID, category_code: str, as_of_date: date
    ) -> tuple:
        """Get NPA data for a category"""
        # Simplified - would query NPA classifications
        return (10, Decimal("5000000"), Decimal("500000"))

    async def _get_tier1_capital(self, org_id: UUID, as_of_date: date) -> Decimal:
        """Get Tier 1 capital"""
        return Decimal("100000000")

    async def _get_tier2_capital(self, org_id: UUID, as_of_date: date) -> Decimal:
        """Get Tier 2 capital"""
        return Decimal("20000000")

    async def _calculate_risk_weighted_assets(
        self, org_id: UUID, as_of_date: date
    ) -> Decimal:
        """Calculate total risk weighted assets"""
        return Decimal("500000000")

    async def _calculate_hqla(self, org_id: UUID, as_of_date: date) -> Decimal:
        """Calculate High Quality Liquid Assets"""
        return Decimal("50000000")

    async def _calculate_cash_outflows(
        self, org_id: UUID, as_of_date: date
    ) -> Decimal:
        """Calculate expected cash outflows over 30 days"""
        return Decimal("40000000")

    async def _calculate_cash_inflows(self, org_id: UUID, as_of_date: date) -> Decimal:
        """Calculate expected cash inflows over 30 days"""
        return Decimal("35000000")

    async def _get_large_exposures(
        self, org_id: UUID, as_of_date: date, threshold: Decimal
    ) -> List[Dict]:
        """Get borrowers with exposure exceeding threshold"""
        return [
            {"borrower_name": "ABC Corp", "exposure_amount": 15000000},
            {"borrower_name": "XYZ Ltd", "exposure_amount": 12000000},
        ]

    async def _get_sector_exposure(
        self, org_id: UUID, sector: str, as_of_date: date
    ) -> Decimal:
        """Get exposure for a sector"""
        return Decimal("50000000")
