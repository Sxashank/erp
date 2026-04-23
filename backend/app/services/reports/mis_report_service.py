"""
MIS Report Service
Management Information System reports for business analytics
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class MISReportService:
    """Service for generating MIS reports"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_portfolio_summary(
        self,
        org_id: UUID,
        as_of_date: date,
        unit_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Generate Portfolio Summary Report
        Overview of entire loan portfolio
        """
        # Portfolio metrics
        portfolio = {
            "total_accounts": 15420,
            "active_accounts": 14850,
            "closed_accounts": 520,
            "written_off_accounts": 50,
            "total_sanctioned": 2850000000,
            "total_disbursed": 2650000000,
            "principal_outstanding": 2150000000,
            "interest_outstanding": 85000000,
            "total_outstanding": 2235000000,
            "principal_overdue": 125000000,
            "interest_overdue": 18500000,
            "total_overdue": 143500000,
        }

        # Product-wise breakdown
        product_breakdown = [
            {"product": "Business Loan", "accounts": 5200, "outstanding": 850000000, "percentage": 38.0},
            {"product": "Personal Loan", "accounts": 4500, "outstanding": 520000000, "percentage": 23.3},
            {"product": "Vehicle Loan", "accounts": 3200, "outstanding": 480000000, "percentage": 21.5},
            {"product": "Gold Loan", "accounts": 2520, "outstanding": 385000000, "percentage": 17.2},
        ]

        # Geographic breakdown
        geography_breakdown = [
            {"region": "North", "accounts": 4200, "outstanding": 620000000, "percentage": 27.7},
            {"region": "South", "accounts": 3800, "outstanding": 550000000, "percentage": 24.6},
            {"region": "West", "accounts": 4100, "outstanding": 580000000, "percentage": 26.0},
            {"region": "East", "accounts": 2750, "outstanding": 485000000, "percentage": 21.7},
        ]

        return {
            "report_type": "PORTFOLIO_SUMMARY",
            "as_of_date": as_of_date.isoformat(),
            "generated_at": datetime.now().isoformat(),
            "portfolio": portfolio,
            "product_breakdown": product_breakdown,
            "geography_breakdown": geography_breakdown,
        }

    async def generate_disbursement_report(
        self,
        org_id: UUID,
        from_date: date,
        to_date: date,
        group_by: str = "PRODUCT"
    ) -> Dict[str, Any]:
        """
        Generate Disbursement Report
        Shows disbursements over a period
        """
        # Daily disbursements (sample data for last 30 days)
        daily_data = []
        current_date = from_date
        while current_date <= to_date:
            daily_data.append({
                "date": current_date.isoformat(),
                "count": 45 + (current_date.day % 20),
                "amount": 15000000 + (current_date.day * 500000),
            })
            current_date += timedelta(days=1)

        # Product-wise disbursements
        product_wise = [
            {"product": "Business Loan", "count": 320, "amount": 185000000},
            {"product": "Personal Loan", "count": 480, "amount": 96000000},
            {"product": "Vehicle Loan", "count": 280, "amount": 112000000},
            {"product": "Gold Loan", "count": 520, "amount": 78000000},
        ]

        # Channel-wise disbursements
        channel_wise = [
            {"channel": "Branch", "count": 850, "amount": 320000000},
            {"channel": "DSA", "count": 450, "amount": 98000000},
            {"channel": "Digital", "count": 300, "amount": 53000000},
        ]

        total_count = sum(p["count"] for p in product_wise)
        total_amount = sum(p["amount"] for p in product_wise)

        return {
            "report_type": "DISBURSEMENT",
            "period": {"from": from_date.isoformat(), "to": to_date.isoformat()},
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_count": total_count,
                "total_amount": total_amount,
                "average_ticket_size": total_amount / total_count if total_count > 0 else 0,
            },
            "daily_trend": daily_data,
            "product_wise": product_wise,
            "channel_wise": channel_wise,
        }

    async def generate_collection_report(
        self,
        org_id: UUID,
        from_date: date,
        to_date: date
    ) -> Dict[str, Any]:
        """
        Generate Collection Report
        Shows collection performance
        """
        # Collection summary
        summary = {
            "total_demand": 285000000,
            "total_collected": 252000000,
            "collection_efficiency": 88.4,
            "advance_collection": 12000000,
            "on_time_collection": 198000000,
            "overdue_collection": 42000000,
        }

        # Mode-wise collection
        mode_wise = [
            {"mode": "NACH/ECS", "amount": 165000000, "percentage": 65.5},
            {"mode": "Online", "amount": 42000000, "percentage": 16.7},
            {"mode": "Cash", "amount": 28000000, "percentage": 11.1},
            {"mode": "Cheque", "amount": 17000000, "percentage": 6.7},
        ]

        # Bucket-wise collection
        bucket_wise = [
            {"bucket": "Current", "demand": 220000000, "collected": 210000000, "efficiency": 95.5},
            {"bucket": "1-30 DPD", "demand": 35000000, "collected": 28000000, "efficiency": 80.0},
            {"bucket": "31-60 DPD", "demand": 18000000, "collected": 10000000, "efficiency": 55.6},
            {"bucket": "61-90 DPD", "demand": 8000000, "collected": 3200000, "efficiency": 40.0},
            {"bucket": ">90 DPD", "demand": 4000000, "collected": 800000, "efficiency": 20.0},
        ]

        return {
            "report_type": "COLLECTION",
            "period": {"from": from_date.isoformat(), "to": to_date.isoformat()},
            "generated_at": datetime.now().isoformat(),
            "summary": summary,
            "mode_wise": mode_wise,
            "bucket_wise": bucket_wise,
        }

    async def generate_delinquency_report(
        self,
        org_id: UUID,
        as_of_date: date
    ) -> Dict[str, Any]:
        """
        Generate Delinquency Report
        Shows overdue position and trends
        """
        # Bucket-wise delinquency
        buckets = [
            {"bucket": "Current", "accounts": 13250, "amount": 1980000000, "percentage": 88.6},
            {"bucket": "1-30 DPD", "accounts": 850, "amount": 125000000, "percentage": 5.6},
            {"bucket": "31-60 DPD", "accounts": 380, "amount": 52000000, "percentage": 2.3},
            {"bucket": "61-90 DPD", "accounts": 220, "amount": 38000000, "percentage": 1.7},
            {"bucket": "91-180 DPD", "accounts": 110, "amount": 28000000, "percentage": 1.3},
            {"bucket": ">180 DPD", "accounts": 40, "amount": 12000000, "percentage": 0.5},
        ]

        # Roll forward analysis
        roll_forward = {
            "current_to_1_30": 2.5,
            "1_30_to_31_60": 15.2,
            "31_60_to_61_90": 22.8,
            "61_90_to_91_plus": 35.5,
        }

        # Vintage analysis
        vintage = [
            {"vintage": "Q1 2024", "accounts": 2500, "delinquency_rate": 4.2},
            {"vintage": "Q2 2024", "accounts": 2800, "delinquency_rate": 3.8},
            {"vintage": "Q3 2024", "accounts": 3200, "delinquency_rate": 3.2},
            {"vintage": "Q4 2024", "accounts": 3500, "delinquency_rate": 2.5},
        ]

        total_delinquent = sum(b["amount"] for b in buckets if b["bucket"] != "Current")
        total_outstanding = sum(b["amount"] for b in buckets)

        return {
            "report_type": "DELINQUENCY",
            "as_of_date": as_of_date.isoformat(),
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_outstanding": total_outstanding,
                "total_delinquent": total_delinquent,
                "delinquency_rate": total_delinquent / total_outstanding * 100 if total_outstanding > 0 else 0,
            },
            "buckets": buckets,
            "roll_forward": roll_forward,
            "vintage_analysis": vintage,
        }

    async def generate_profitability_report(
        self,
        org_id: UUID,
        from_date: date,
        to_date: date
    ) -> Dict[str, Any]:
        """
        Generate Profitability Report
        Shows income, expenses and margins
        """
        # Income breakdown
        income = {
            "interest_income": 285000000,
            "processing_fees": 18500000,
            "penal_interest": 8500000,
            "other_charges": 4200000,
            "total_income": 316200000,
        }

        # Cost breakdown
        costs = {
            "interest_expense": 125000000,
            "provision_expense": 28000000,
            "operating_expense": 65000000,
            "total_costs": 218000000,
        }

        # Margins
        nim = (income["interest_income"] - costs["interest_expense"]) / income["interest_income"] * 100
        operating_margin = (income["total_income"] - costs["operating_expense"]) / income["total_income"] * 100
        net_margin = (income["total_income"] - costs["total_costs"]) / income["total_income"] * 100

        # Product-wise profitability
        product_wise = [
            {"product": "Business Loan", "income": 125000000, "cost": 85000000, "profit": 40000000, "margin": 32.0},
            {"product": "Personal Loan", "income": 85000000, "cost": 58000000, "profit": 27000000, "margin": 31.8},
            {"product": "Vehicle Loan", "income": 62000000, "cost": 45000000, "profit": 17000000, "margin": 27.4},
            {"product": "Gold Loan", "income": 44200000, "cost": 30000000, "profit": 14200000, "margin": 32.1},
        ]

        return {
            "report_type": "PROFITABILITY",
            "period": {"from": from_date.isoformat(), "to": to_date.isoformat()},
            "generated_at": datetime.now().isoformat(),
            "income": income,
            "costs": costs,
            "margins": {
                "net_interest_margin": nim,
                "operating_margin": operating_margin,
                "net_margin": net_margin,
            },
            "product_wise": product_wise,
            "profit_before_tax": income["total_income"] - costs["total_costs"],
        }

    async def generate_branch_performance_report(
        self,
        org_id: UUID,
        from_date: date,
        to_date: date
    ) -> Dict[str, Any]:
        """
        Generate Branch Performance Report
        Compares performance across branches
        """
        branches = [
            {
                "branch_code": "BR001",
                "branch_name": "Mumbai Main",
                "aum": 520000000,
                "disbursement": 85000000,
                "collection_efficiency": 92.5,
                "npa_percentage": 2.1,
                "profit": 12500000,
            },
            {
                "branch_code": "BR002",
                "branch_name": "Delhi Central",
                "aum": 480000000,
                "disbursement": 78000000,
                "collection_efficiency": 89.2,
                "npa_percentage": 2.8,
                "profit": 10800000,
            },
            {
                "branch_code": "BR003",
                "branch_name": "Bangalore South",
                "aum": 420000000,
                "disbursement": 72000000,
                "collection_efficiency": 91.8,
                "npa_percentage": 1.9,
                "profit": 11200000,
            },
            {
                "branch_code": "BR004",
                "branch_name": "Chennai North",
                "aum": 380000000,
                "disbursement": 65000000,
                "collection_efficiency": 88.5,
                "npa_percentage": 3.2,
                "profit": 9500000,
            },
            {
                "branch_code": "BR005",
                "branch_name": "Kolkata East",
                "aum": 350000000,
                "disbursement": 58000000,
                "collection_efficiency": 85.2,
                "npa_percentage": 4.1,
                "profit": 7800000,
            },
        ]

        # Calculate rankings
        branches_sorted = sorted(branches, key=lambda x: x["aum"], reverse=True)
        for i, branch in enumerate(branches_sorted):
            branch["aum_rank"] = i + 1

        return {
            "report_type": "BRANCH_PERFORMANCE",
            "period": {"from": from_date.isoformat(), "to": to_date.isoformat()},
            "generated_at": datetime.now().isoformat(),
            "branches": branches_sorted,
            "summary": {
                "total_branches": len(branches),
                "total_aum": sum(b["aum"] for b in branches),
                "total_disbursement": sum(b["disbursement"] for b in branches),
                "avg_collection_efficiency": sum(b["collection_efficiency"] for b in branches) / len(branches),
                "avg_npa": sum(b["npa_percentage"] for b in branches) / len(branches),
            }
        }

    async def generate_employee_productivity_report(
        self,
        org_id: UUID,
        from_date: date,
        to_date: date
    ) -> Dict[str, Any]:
        """
        Generate Employee Productivity Report
        Shows sales and collection staff performance
        """
        # Sales team performance
        sales_team = [
            {"employee": "Amit Kumar", "role": "Sales Manager", "logins": 45, "disbursement": 28000000, "target": 25000000, "achievement": 112.0},
            {"employee": "Priya Singh", "role": "Sales Executive", "logins": 38, "disbursement": 18500000, "target": 20000000, "achievement": 92.5},
            {"employee": "Rahul Sharma", "role": "Sales Executive", "logins": 42, "disbursement": 22000000, "target": 20000000, "achievement": 110.0},
        ]

        # Collection team performance
        collection_team = [
            {"employee": "Vijay Patil", "role": "Collection Manager", "cases_handled": 250, "amount_collected": 45000000, "target": 50000000, "efficiency": 90.0},
            {"employee": "Neha Gupta", "role": "Collection Executive", "cases_handled": 180, "amount_collected": 28000000, "target": 30000000, "efficiency": 93.3},
        ]

        return {
            "report_type": "EMPLOYEE_PRODUCTIVITY",
            "period": {"from": from_date.isoformat(), "to": to_date.isoformat()},
            "generated_at": datetime.now().isoformat(),
            "sales_team": sales_team,
            "collection_team": collection_team,
            "summary": {
                "total_logins": sum(s["logins"] for s in sales_team),
                "total_disbursement": sum(s["disbursement"] for s in sales_team),
                "avg_sales_achievement": sum(s["achievement"] for s in sales_team) / len(sales_team),
                "avg_collection_efficiency": sum(c["efficiency"] for c in collection_team) / len(collection_team),
            }
        }

    async def get_dashboard_metrics(
        self,
        org_id: UUID,
        as_of_date: date
    ) -> Dict[str, Any]:
        """
        Get key metrics for dashboard display
        """
        return {
            "portfolio": {
                "aum": 2235000000,
                "aum_growth_mom": 3.5,
                "active_accounts": 14850,
            },
            "disbursement": {
                "mtd": 471000000,
                "ytd": 2650000000,
                "target_achievement": 94.2,
            },
            "collection": {
                "efficiency_mtd": 88.4,
                "overdue_amount": 143500000,
                "recovery_rate": 42.5,
            },
            "asset_quality": {
                "gnpa": 3.8,
                "nnpa": 2.1,
                "provision_coverage": 68.5,
            },
            "profitability": {
                "nim": 8.2,
                "roa": 2.8,
                "roe": 15.4,
            }
        }
