"""Bureau Report Parser.

Utility for parsing and analyzing credit bureau reports.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any

from app.integrations.bureau.base import BureauReport, CreditAccount

logger = logging.getLogger(__name__)


class BureauReportParser:
    """Parser and analyzer for credit bureau reports."""

    # Score bands
    SCORE_BANDS = {
        (750, 900): "EXCELLENT",
        (700, 749): "GOOD",
        (650, 699): "FAIR",
        (550, 649): "POOR",
        (300, 549): "VERY_POOR",
    }

    # DPD thresholds
    DPD_THRESHOLDS = {
        "STANDARD": 0,
        "SMA_0": 30,
        "SMA_1": 60,
        "SMA_2": 90,
        "NPA": 90,
    }

    @classmethod
    def get_score_band(cls, score: Optional[int]) -> str:
        """Get score band classification.

        Args:
            score: Credit score

        Returns:
            Score band (EXCELLENT, GOOD, FAIR, POOR, VERY_POOR, NA)
        """
        if score is None:
            return "NA"

        for (low, high), band in cls.SCORE_BANDS.items():
            if low <= score <= high:
                return band
        return "NA"

    @classmethod
    def get_score_percentile(cls, score: Optional[int]) -> Optional[int]:
        """Estimate score percentile.

        Args:
            score: Credit score

        Returns:
            Estimated percentile (0-100)
        """
        if score is None:
            return None

        # Rough estimation based on typical score distribution
        if score >= 800:
            return 95
        elif score >= 750:
            return 80
        elif score >= 700:
            return 60
        elif score >= 650:
            return 40
        elif score >= 600:
            return 25
        elif score >= 550:
            return 15
        else:
            return 5

    @classmethod
    def analyze_accounts(
        cls, accounts: List[CreditAccount]
    ) -> Dict[str, Any]:
        """Analyze credit accounts.

        Args:
            accounts: List of credit accounts

        Returns:
            Account analysis summary
        """
        if not accounts:
            return {
                "total_accounts": 0,
                "by_type": {},
                "by_status": {},
                "financial_summary": {},
            }

        # Count by type
        by_type: Dict[str, Dict] = {}
        for acc in accounts:
            acc_type = acc.account_type
            if acc_type not in by_type:
                by_type[acc_type] = {
                    "count": 0,
                    "sanctioned": Decimal("0"),
                    "outstanding": Decimal("0"),
                    "overdue": Decimal("0"),
                    "active": 0,
                    "closed": 0,
                }
            by_type[acc_type]["count"] += 1
            by_type[acc_type]["sanctioned"] += acc.sanctioned_amount or Decimal("0")
            by_type[acc_type]["outstanding"] += acc.current_balance or Decimal("0")
            by_type[acc_type]["overdue"] += acc.overdue_amount or Decimal("0")
            if acc.account_status == "ACTIVE":
                by_type[acc_type]["active"] += 1
            elif acc.account_status == "CLOSED":
                by_type[acc_type]["closed"] += 1

        # Count by status
        by_status: Dict[str, int] = {}
        for acc in accounts:
            status = acc.account_status
            by_status[status] = by_status.get(status, 0) + 1

        # Financial summary
        financial = {
            "total_sanctioned": sum(a.sanctioned_amount or Decimal("0") for a in accounts),
            "total_outstanding": sum(a.current_balance or Decimal("0") for a in accounts),
            "total_overdue": sum(a.overdue_amount or Decimal("0") for a in accounts),
            "total_emi": sum(a.emi_amount or Decimal("0") for a in accounts if a.account_status == "ACTIVE"),
            "total_credit_limit": sum(a.credit_limit or Decimal("0") for a in accounts if a.credit_limit),
        }

        # Calculate utilization for credit cards
        credit_card_limit = sum(
            a.credit_limit or Decimal("0")
            for a in accounts
            if a.account_type == "CREDIT_CARD" and a.credit_limit
        )
        credit_card_outstanding = sum(
            a.current_balance or Decimal("0")
            for a in accounts
            if a.account_type == "CREDIT_CARD"
        )
        if credit_card_limit > 0:
            financial["credit_card_utilization"] = round(
                (credit_card_outstanding / credit_card_limit) * 100, 2
            )

        return {
            "total_accounts": len(accounts),
            "active_accounts": sum(1 for a in accounts if a.account_status == "ACTIVE"),
            "closed_accounts": sum(1 for a in accounts if a.account_status == "CLOSED"),
            "by_type": by_type,
            "by_status": by_status,
            "financial_summary": financial,
        }

    @classmethod
    def analyze_dpd(
        cls, accounts: List[CreditAccount], months: int = 24
    ) -> Dict[str, Any]:
        """Analyze DPD (Days Past Due) history.

        Args:
            accounts: List of credit accounts
            months: Number of months to analyze

        Returns:
            DPD analysis summary
        """
        all_dpd_values: List[int] = []
        monthly_dpd: Dict[str, int] = {}

        for acc in accounts:
            if acc.dpd_history:
                for month_key, dpd in acc.dpd_history.items():
                    all_dpd_values.append(dpd)
                    # Keep max DPD for each month across all accounts
                    if month_key not in monthly_dpd or dpd > monthly_dpd[month_key]:
                        monthly_dpd[month_key] = dpd

        if not all_dpd_values:
            return {
                "max_dpd_ever": 0,
                "max_dpd_6m": 0,
                "max_dpd_12m": 0,
                "max_dpd_24m": 0,
                "months_with_dpd": 0,
                "current_dpd": 0,
                "dpd_trend": "STABLE",
            }

        # Get current month key
        today = date.today()
        current_month_key = today.strftime("%Y%m")

        # Calculate metrics
        sorted_months = sorted(monthly_dpd.keys(), reverse=True)
        recent_6m = sorted_months[:6]
        recent_12m = sorted_months[:12]

        max_dpd_6m = max((monthly_dpd.get(m, 0) for m in recent_6m), default=0)
        max_dpd_12m = max((monthly_dpd.get(m, 0) for m in recent_12m), default=0)
        max_dpd_ever = max(all_dpd_values) if all_dpd_values else 0

        # Count months with DPD > 0
        months_with_dpd = sum(1 for dpd in monthly_dpd.values() if dpd > 0)

        # Current DPD
        current_dpd = monthly_dpd.get(current_month_key, 0)

        # Determine trend
        if len(recent_6m) >= 3:
            recent_avg = sum(monthly_dpd.get(m, 0) for m in recent_6m[:3]) / 3
            older_avg = sum(monthly_dpd.get(m, 0) for m in recent_6m[3:6]) / max(len(recent_6m[3:6]), 1)
            if recent_avg < older_avg - 10:
                trend = "IMPROVING"
            elif recent_avg > older_avg + 10:
                trend = "WORSENING"
            else:
                trend = "STABLE"
        else:
            trend = "INSUFFICIENT_DATA"

        return {
            "max_dpd_ever": max_dpd_ever,
            "max_dpd_6m": max_dpd_6m,
            "max_dpd_12m": max_dpd_12m,
            "max_dpd_24m": max(all_dpd_values[-24:]) if len(all_dpd_values) >= 24 else max_dpd_ever,
            "months_with_dpd": months_with_dpd,
            "current_dpd": current_dpd,
            "dpd_trend": trend,
            "monthly_dpd": monthly_dpd,
        }

    @classmethod
    def analyze_enquiries(
        cls, enquiries: List[Any], months: int = 12
    ) -> Dict[str, Any]:
        """Analyze credit enquiries.

        Args:
            enquiries: List of credit enquiries
            months: Number of months to analyze

        Returns:
            Enquiry analysis summary
        """
        if not enquiries:
            return {
                "total": 0,
                "last_30d": 0,
                "last_90d": 0,
                "last_6m": 0,
                "last_12m": 0,
                "by_purpose": {},
                "high_volume": False,
            }

        today = date.today()
        by_purpose: Dict[str, int] = {}

        last_30d = 0
        last_90d = 0
        last_6m = 0
        last_12m = 0

        for enq in enquiries:
            enq_date = enq.enquiry_date
            purpose = enq.enquiry_purpose or "OTHER"

            by_purpose[purpose] = by_purpose.get(purpose, 0) + 1

            if enq_date:
                days_ago = (today - enq_date).days
                if days_ago <= 30:
                    last_30d += 1
                if days_ago <= 90:
                    last_90d += 1
                if days_ago <= 180:
                    last_6m += 1
                if days_ago <= 365:
                    last_12m += 1

        # High enquiry volume threshold
        high_volume = last_90d >= 5 or last_6m >= 8

        return {
            "total": len(enquiries),
            "last_30d": last_30d,
            "last_90d": last_90d,
            "last_6m": last_6m,
            "last_12m": last_12m,
            "by_purpose": by_purpose,
            "high_volume": high_volume,
        }

    @classmethod
    def identify_risk_factors(cls, report: BureauReport) -> List[Dict[str, Any]]:
        """Identify risk factors from bureau report.

        Args:
            report: Bureau report

        Returns:
            List of risk factors with severity
        """
        risk_factors = []

        # Low credit score
        if report.credit_score:
            if report.credit_score < 550:
                risk_factors.append({
                    "factor": "VERY_LOW_SCORE",
                    "severity": "HIGH",
                    "description": f"Credit score ({report.credit_score}) is very low",
                    "value": report.credit_score,
                })
            elif report.credit_score < 650:
                risk_factors.append({
                    "factor": "LOW_SCORE",
                    "severity": "MEDIUM",
                    "description": f"Credit score ({report.credit_score}) is below average",
                    "value": report.credit_score,
                })

        # High DPD
        if report.max_dpd_last_12m > 90:
            risk_factors.append({
                "factor": "HIGH_DPD",
                "severity": "HIGH",
                "description": f"Maximum DPD in last 12 months is {report.max_dpd_last_12m} days",
                "value": report.max_dpd_last_12m,
            })
        elif report.max_dpd_last_12m > 30:
            risk_factors.append({
                "factor": "MODERATE_DPD",
                "severity": "MEDIUM",
                "description": f"DPD of {report.max_dpd_last_12m} days in last 12 months",
                "value": report.max_dpd_last_12m,
            })

        # High enquiry volume
        if report.enquiries_last_30d >= 3:
            risk_factors.append({
                "factor": "HIGH_RECENT_ENQUIRIES",
                "severity": "MEDIUM",
                "description": f"{report.enquiries_last_30d} enquiries in last 30 days",
                "value": report.enquiries_last_30d,
            })

        # Check for written-off or suit-filed accounts
        for acc in report.accounts:
            if acc.account_status == "WRITTEN_OFF":
                risk_factors.append({
                    "factor": "WRITTEN_OFF_ACCOUNT",
                    "severity": "HIGH",
                    "description": f"Written-off account with {acc.institution_name}",
                    "value": str(acc.write_off_amount or 0),
                })
                break

            if acc.account_status == "SUIT_FILED":
                risk_factors.append({
                    "factor": "SUIT_FILED",
                    "severity": "HIGH",
                    "description": f"Suit filed by {acc.institution_name}",
                    "value": acc.institution_name,
                })
                break

            if acc.account_status == "WILLFUL_DEFAULT":
                risk_factors.append({
                    "factor": "WILLFUL_DEFAULT",
                    "severity": "CRITICAL",
                    "description": "Marked as willful defaulter",
                    "value": acc.institution_name,
                })
                break

        # High overdue amount
        if report.total_overdue and report.total_overdue > Decimal("100000"):
            risk_factors.append({
                "factor": "HIGH_OVERDUE",
                "severity": "HIGH" if report.total_overdue > Decimal("500000") else "MEDIUM",
                "description": f"Total overdue amount is Rs. {report.total_overdue:,.2f}",
                "value": str(report.total_overdue),
            })

        return risk_factors

    @classmethod
    def calculate_debt_to_income(
        cls,
        report: BureauReport,
        monthly_income: Decimal,
    ) -> Optional[Decimal]:
        """Calculate debt-to-income ratio.

        Args:
            report: Bureau report
            monthly_income: Monthly income

        Returns:
            Debt-to-income ratio as percentage
        """
        if not monthly_income or monthly_income <= 0:
            return None

        total_emi = sum(
            acc.emi_amount or Decimal("0")
            for acc in report.accounts
            if acc.account_status == "ACTIVE" and acc.emi_amount
        )

        return round((total_emi / monthly_income) * 100, 2)

    @classmethod
    def generate_summary(cls, report: BureauReport) -> Dict[str, Any]:
        """Generate comprehensive summary from bureau report.

        Args:
            report: Bureau report

        Returns:
            Comprehensive summary dictionary
        """
        account_analysis = cls.analyze_accounts(report.accounts)
        dpd_analysis = cls.analyze_dpd(report.accounts)
        enquiry_analysis = cls.analyze_enquiries(report.enquiries)
        risk_factors = cls.identify_risk_factors(report)

        return {
            "bureau": report.bureau,
            "report_date": report.score_date,
            "credit_score": report.credit_score,
            "score_band": cls.get_score_band(report.credit_score),
            "score_percentile": cls.get_score_percentile(report.credit_score),
            "accounts": account_analysis,
            "dpd": dpd_analysis,
            "enquiries": enquiry_analysis,
            "risk_factors": risk_factors,
            "risk_level": cls._calculate_overall_risk(risk_factors),
        }

    @classmethod
    def _calculate_overall_risk(cls, risk_factors: List[Dict[str, Any]]) -> str:
        """Calculate overall risk level from risk factors."""
        if any(rf["severity"] == "CRITICAL" for rf in risk_factors):
            return "CRITICAL"
        if sum(1 for rf in risk_factors if rf["severity"] == "HIGH") >= 2:
            return "HIGH"
        if any(rf["severity"] == "HIGH" for rf in risk_factors):
            return "MEDIUM_HIGH"
        if any(rf["severity"] == "MEDIUM" for rf in risk_factors):
            return "MEDIUM"
        return "LOW"
