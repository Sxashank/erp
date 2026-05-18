"""Enterprise MIS report service backed by live ERP data."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from time import perf_counter
from typing import Any
from uuid import UUID

from sqlalchemy import case, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ap_ar.bank_reconciliation import BankStatement
from app.models.ap_ar.customer import Customer
from app.models.ap_ar.purchase_bill import PurchaseBill
from app.models.ap_ar.sales_invoice import SalesInvoice
from app.models.ap_ar.vendor import Vendor
from app.models.common.audit_log import AuditLog
from app.models.common.background_job import BackgroundJob
from app.models.compliance.compliance import ComplianceInstance, ComplianceItem
from app.models.dms.document import DMSDocument
from app.models.finance.account import Account
from app.models.finance.gl_entry import GLEntry
from app.models.finance.voucher import Voucher
from app.models.fixed_assets.depreciation import DepreciationRun
from app.models.fixed_assets.fixed_asset import FixedAsset
from app.models.fixed_deposits.fixed_deposit import FixedDeposit
from app.models.gst.gstn_models import GSTReturnFiling
from app.models.hris.attendance import Attendance, MonthlyAttendanceSummary
from app.models.hris.employee import Employee
from app.models.hris.leave import LeaveApplication
from app.models.inventory.item_master import ItemMaster
from app.models.inventory.stock import StockBalance, StockTransaction
from app.models.lending.application import LoanApplication
from app.models.lending.entity import Entity
from app.models.lending.enums import (
    AssetClassification,
    DisbursementStatus,
    LoanAccountStatus,
    ReceiptStatus,
)
from app.models.lending.loan_account import (
    Disbursement,
    LoanAccount,
    LoanReceipt,
    RepaymentSchedule,
    ScheduleInstallment,
)
from app.models.lending.product import LoanProduct
from app.models.lending.sanction import LoanSanction
from app.models.lending.treasury import (
    ALMPosition,
    Borrowing,
    BorrowingPayment,
)
from app.models.masters.unit import Unit
from app.models.payroll.payroll import PayrollBatch, Payslip
from app.models.portal.document import PortalDocument, PortalDocumentRequest
from app.models.portal.portal_user import PortalSession, PortalUser
from app.models.portal.service_request import PortalServiceRequest
from app.models.reports import ReportRun, ReportSchedule
from app.models.tds.tds_challan import TDSChallan
from app.models.tds.tds_entry import TDSEntry
from app.models.tds.tds_return import TDSReturn
from app.models.vendor_portal.asn import AdvancedShippingNotice
from app.models.vendor_portal.invoice import VendorInvoice
from app.models.vendor_portal.portal_vendor_user import PortalVendorSession, PortalVendorUser
from app.models.vendor_portal.registration import VendorRegistration
from app.models.workflow.workflow_instance import WorkflowInstance
from app.models.workflow.workflow_task import WorkflowTask
from app.schemas.reports.mis import (
    AllModulesReportResponse,
    BranchPerformanceItem,
    BranchPerformanceResponse,
    CollectionBucketItem,
    CollectionModeItem,
    CollectionReportResponse,
    CollectionSummary,
    DailyTrendItem,
    DashboardSummary,
    DelinquencyBucketItem,
    DelinquencyReportResponse,
    DelinquencySummary,
    DisbursementBreakdownItem,
    DisbursementReportResponse,
    MISMetric,
    ModuleReportRow,
    ModuleReportSection,
    PeriodSummary,
    PortfolioBreakdownItem,
    PortfolioSummary,
    PortfolioSummaryResponse,
    ProfitabilityBreakdownItem,
    ProfitabilityReportResponse,
    ProfitabilitySummary,
    ReportCatalogGroup,
    ReportCatalogItem,
    ReportCatalogResponse,
    ReportFilterDefinition,
    ReportPeriod,
    ReportRunResponse,
    ReportScheduleCreate,
    ReportScheduleResponse,
    TopDelinquentAccount,
)

ZERO = Decimal("0")
NPA_CLASSIFICATIONS = {
    AssetClassification.NPA,
    AssetClassification.SUBSTANDARD,
    AssetClassification.DOUBTFUL_1,
    AssetClassification.DOUBTFUL_2,
    AssetClassification.DOUBTFUL_3,
    AssetClassification.LOSS,
}


def _now() -> datetime:
    return datetime.now(UTC)


def _decimal(value: Any) -> Decimal:
    if value is None:
        return ZERO
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _pct(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return (numerator / denominator * Decimal("100")).quantize(Decimal("0.01"))


def _enum_value(value: Any) -> str:
    return getattr(value, "value", str(value)) if value is not None else ""


def _safe_row_count(payload: Any) -> int:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        return len(payload)
    return 1


FILTERS = {
    "asOfDate": ReportFilterDefinition(code="asOfDate", label="As of date", type="DATE"),
    "fromDate": ReportFilterDefinition(code="fromDate", label="From date", type="DATE"),
    "toDate": ReportFilterDefinition(code="toDate", label="To date", type="DATE"),
    "unitId": ReportFilterDefinition(code="unitId", label="Unit / branch", type="UNIT"),
    "productId": ReportFilterDefinition(code="productId", label="Loan product", type="PRODUCT"),
    "entityId": ReportFilterDefinition(code="entityId", label="Borrower / entity", type="ENTITY"),
    "lenderId": ReportFilterDefinition(code="lenderId", label="Funding source", type="LENDER"),
    "status": ReportFilterDefinition(code="status", label="Status", type="STATUS"),
    "gstin": ReportFilterDefinition(code="gstin", label="GSTIN", type="TEXT"),
}


CATALOG_GROUPS = [
    ReportCatalogGroup(
        category="EXECUTIVE",
        title="Executive / Board MIS",
        description="Board pack, daily flash, and enterprise KPI exception reporting.",
        reports=[
            ReportCatalogItem(
                report_code="CEO_CFO_DASHBOARD",
                report_name="CEO/CFO Dashboard",
                category="EXECUTIVE",
                module="Board",
                description="AUM, GNPA, NIM, spread, collection and liquidity indicators.",
                route="/admin/reports/mis",
                supported_filters=[FILTERS["asOfDate"]],
            ),
            ReportCatalogItem(
                report_code="BOARD_PACK",
                report_name="Board Pack",
                category="EXECUTIVE",
                module="Board",
                description=(
                    "Monthly management pack across lending, finance, treasury, "
                    "asset quality and compliance."
                ),
                route="/admin/reports/mis",
                supported_filters=[FILTERS["asOfDate"]],
            ),
            ReportCatalogItem(
                report_code="DAILY_FLASH",
                report_name="Daily Flash",
                category="EXECUTIVE",
                module="Board",
                description=(
                    "Daily movement in applications, disbursements, collections, "
                    "overdue and cash obligations."
                ),
                route="/admin/reports/mis",
                supported_filters=[FILTERS["asOfDate"]],
            ),
        ],
    ),
    ReportCatalogGroup(
        category="LENDING",
        title="Lending / Portfolio",
        description="Corporate lending lifecycle, portfolio, sanction and disbursement reports.",
        reports=[
            ReportCatalogItem(
                report_code="PORTFOLIO_SUMMARY",
                report_name="Portfolio Summary",
                category="LENDING",
                module="LMS",
                description="Loan book, outstanding, product mix, asset quality and top exposures.",
                route="/admin/reports/mis/portfolio",
                supported_filters=[FILTERS["asOfDate"], FILTERS["unitId"], FILTERS["productId"]],
            ),
            ReportCatalogItem(
                report_code="APPLICATION_PIPELINE",
                report_name="Application Pipeline",
                category="LENDING",
                module="LOS",
                description=(
                    "Applications by stage, status, product, relationship manager " "and branch."
                ),
                route="/admin/lending/los/applications",
                supported_filters=[FILTERS["fromDate"], FILTERS["toDate"], FILTERS["status"]],
            ),
            ReportCatalogItem(
                report_code="SANCTION_PIPELINE",
                report_name="Sanction Pipeline",
                category="LENDING",
                module="LOS",
                description=(
                    "Sanctions approved, pending acceptance, expired and "
                    "sanctioned-not-disbursed."
                ),
                route="/admin/lending/los/sanctions",
                supported_filters=[FILTERS["fromDate"], FILTERS["toDate"], FILTERS["status"]],
            ),
            ReportCatalogItem(
                report_code="DISBURSEMENT",
                report_name="Disbursement Report",
                category="LENDING",
                module="LMS",
                description="Processed disbursements by product, branch, mode and daily trend.",
                route="/admin/reports/mis/disbursement",
                supported_filters=[FILTERS["fromDate"], FILTERS["toDate"], FILTERS["unitId"]],
            ),
        ],
    ),
    ReportCatalogGroup(
        category="COLLECTIONS",
        title="Collections / Asset Quality",
        description="Demand, receipt, DPD, SMA/NPA, provisioning and recovery views.",
        reports=[
            ReportCatalogItem(
                report_code="COLLECTION",
                report_name="Collection Report",
                category="COLLECTIONS",
                module="Collections",
                description=(
                    "Demand vs collection, receipt mode, component allocation and " "DPD buckets."
                ),
                route="/admin/reports/mis/collection",
                supported_filters=[FILTERS["fromDate"], FILTERS["toDate"]],
            ),
            ReportCatalogItem(
                report_code="DELINQUENCY",
                report_name="Delinquency Report",
                category="COLLECTIONS",
                module="Collections",
                description="Current, SMA, NPA and top delinquent corporate borrowers.",
                route="/admin/reports/mis/delinquency",
                supported_filters=[FILTERS["asOfDate"], FILTERS["productId"]],
            ),
            ReportCatalogItem(
                report_code="NPA_MOVEMENT",
                report_name="NPA Movement",
                category="COLLECTIONS",
                module="Risk",
                description="Movement across standard, SMA and NPA classifications.",
                route="/admin/lending/reports/npa",
                supported_filters=[FILTERS["fromDate"], FILTERS["toDate"]],
            ),
            ReportCatalogItem(
                report_code="PROVISIONING",
                report_name="Provisioning Report",
                category="COLLECTIONS",
                module="Risk",
                description="Provision held by classification and exposure.",
                route="/admin/reports/regulatory/npa",
                supported_filters=[FILTERS["asOfDate"]],
            ),
        ],
    ),
    ReportCatalogGroup(
        category="TREASURY",
        title="Treasury / ALM / Funding",
        description="Borrowing, source-of-funds, cost of funds, spread and ALM reports.",
        reports=[
            ReportCatalogItem(
                report_code="BORROWING_POSITION",
                report_name="Borrowing Position",
                category="TREASURY",
                module="Treasury",
                description="Borrowing limits, drawdowns, outstanding and lender obligations.",
                route="/admin/lending/treasury/borrowings",
                supported_filters=[FILTERS["asOfDate"], FILTERS["lenderId"]],
            ),
            ReportCatalogItem(
                report_code="SOURCE_OF_FUNDS",
                report_name="Source-of-Funds Utilisation",
                category="TREASURY",
                module="Treasury",
                description=(
                    "Borrowing deployment into loans with cost rate, lending rate " "and spread."
                ),
                route="/admin/lending/treasury/source-of-funds",
                supported_filters=[FILTERS["fromDate"], FILTERS["toDate"], FILTERS["lenderId"]],
            ),
            ReportCatalogItem(
                report_code="ALM_GAP",
                report_name="ALM Gap Statement",
                category="TREASURY",
                module="ALM",
                description="Future loan inflows and borrowing outflows by maturity bucket.",
                route="/admin/reports/regulatory/alm",
                supported_filters=[FILTERS["asOfDate"]],
            ),
            ReportCatalogItem(
                report_code="PROFITABILITY",
                report_name="Profitability Report",
                category="TREASURY",
                module="Finance",
                description=(
                    "Interest income, borrowing cost, NII, NIM, spread and "
                    "product profitability."
                ),
                route="/admin/reports/mis/profitability",
                supported_filters=[FILTERS["fromDate"], FILTERS["toDate"]],
            ),
        ],
    ),
    ReportCatalogGroup(
        category="FINANCE",
        title="Finance / Accounting",
        description="Financial statements, ledgers, close controls and reconciliation reports.",
        reports=[
            ReportCatalogItem(
                report_code="TRIAL_BALANCE",
                report_name="Trial Balance",
                category="FINANCE",
                module="GL",
                description="Account-wise debit, credit and closing balances.",
                route="/admin/reports/trial-balance",
                supported_filters=[FILTERS["asOfDate"]],
            ),
            ReportCatalogItem(
                report_code="PROFIT_LOSS",
                report_name="Profit & Loss",
                category="FINANCE",
                module="GL",
                description="Income and expense statement for selected period.",
                route="/admin/reports/profit-loss",
                supported_filters=[FILTERS["fromDate"], FILTERS["toDate"]],
            ),
            ReportCatalogItem(
                report_code="BALANCE_SHEET",
                report_name="Balance Sheet",
                category="FINANCE",
                module="GL",
                description="Assets, liabilities and equity as of date.",
                route="/admin/reports/balance-sheet",
                supported_filters=[FILTERS["asOfDate"]],
            ),
            ReportCatalogItem(
                report_code="VOUCHER_REGISTER",
                report_name="Voucher Register",
                category="FINANCE",
                module="GL",
                description="Voucher status, approvals, posting and reversal audit.",
                route="/admin/finance/vouchers",
                supported_filters=[FILTERS["fromDate"], FILTERS["toDate"], FILTERS["status"]],
            ),
        ],
    ),
    ReportCatalogGroup(
        category="TAX_COMPLIANCE",
        title="GST / TDS / Compliance",
        description="Manual-first statutory working reports and filing trackers.",
        reports=[
            ReportCatalogItem(
                report_code="GST_LIABILITY",
                report_name="GST Liability Summary",
                category="TAX_COMPLIANCE",
                module="GST",
                description="Output GST, ITC, RCM and return working status from ERP vouchers.",
                route="/admin/gst/gstn/gstr3b",
                supported_filters=[FILTERS["fromDate"], FILTERS["toDate"], FILTERS["gstin"]],
            ),
            ReportCatalogItem(
                report_code="EWAY_EINVOICE_REGISTER",
                report_name="E-way / E-invoice Reference Register",
                category="TAX_COMPLIANCE",
                module="GST",
                description=(
                    "Manual and future integration reference register; no live " "GSTN dependency."
                ),
                route="/admin/gst/gstn",
                supported_filters=[FILTERS["fromDate"], FILTERS["toDate"], FILTERS["status"]],
                manual_first_note="External GSTN/IRP/e-way bill filing remains release-gated.",
            ),
            ReportCatalogItem(
                report_code="TDS_SUMMARY",
                report_name="TDS Deduction Summary",
                category="TAX_COMPLIANCE",
                module="TDS",
                description="Section-wise deduction, challan, return and Form 16A working report.",
                route="/admin/tds/entries",
                supported_filters=[FILTERS["fromDate"], FILTERS["toDate"]],
            ),
            ReportCatalogItem(
                report_code="COMPLIANCE_TRACKER",
                report_name="Compliance Tracker",
                category="TAX_COMPLIANCE",
                module="Compliance",
                description="Upcoming, filed, overdue and escalated statutory filings.",
                route="/admin/compliance",
                supported_filters=[FILTERS["fromDate"], FILTERS["toDate"], FILTERS["status"]],
            ),
        ],
    ),
    ReportCatalogGroup(
        category="OPERATIONS",
        title="Assets / Inventory / HRIS / Portals / Audit",
        description="Operational reports across remaining ERP modules.",
        reports=[
            ReportCatalogItem(
                report_code="FIXED_ASSET_REGISTER",
                report_name="Asset Register",
                category="OPERATIONS",
                module="Fixed Assets",
                description="Asset cost, depreciation, disposal and verification status.",
                route="/admin/fixed-assets/reports",
                supported_filters=[FILTERS["asOfDate"], FILTERS["status"]],
            ),
            ReportCatalogItem(
                report_code="STOCK_VALUATION",
                report_name="Stock Valuation",
                category="OPERATIONS",
                module="Inventory",
                description="Stock balance, movement and reorder reporting.",
                route="/admin/inventory/valuation",
                supported_filters=[FILTERS["asOfDate"]],
            ),
            ReportCatalogItem(
                report_code="HR_PAYROLL_SUMMARY",
                report_name="HR & Payroll Summary",
                category="OPERATIONS",
                module="HRIS/Payroll",
                description="Headcount, attendance, payroll batches and statutory payroll totals.",
                route="/admin/payroll/batches",
                supported_filters=[FILTERS["fromDate"], FILTERS["toDate"]],
            ),
            ReportCatalogItem(
                report_code="PORTAL_ACTIVITY",
                report_name="Portal Activity",
                category="OPERATIONS",
                module="Portals",
                description=(
                    "Borrower, ESS and vendor portal activity and document/report " "downloads."
                ),
                route="/admin/reports/history",
                supported_filters=[FILTERS["fromDate"], FILTERS["toDate"]],
            ),
            ReportCatalogItem(
                report_code="AUDIT_ACCESS",
                report_name="Audit & Access Report",
                category="OPERATIONS",
                module="Audit",
                description="User access, report exports, failed jobs and exception dashboard.",
                route="/admin/audit-logs",
                supported_filters=[FILTERS["fromDate"], FILTERS["toDate"], FILTERS["status"]],
            ),
        ],
    ),
]


class MISReportService:
    """Service for generating enterprise MIS reports."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_report_catalog(self) -> ReportCatalogResponse:
        return ReportCatalogResponse(generated_at=_now(), groups=CATALOG_GROUPS)

    def _find_catalog_item(self, report_code: str) -> ReportCatalogItem:
        for group in CATALOG_GROUPS:
            for report in group.reports:
                if report.report_code == report_code:
                    return report
        raise ValueError(f"Unknown report code: {report_code}")

    async def get_dashboard_metrics(self, org_id: UUID, as_of_date: date) -> DashboardSummary:
        portfolio = await self.generate_portfolio_summary(org_id, as_of_date)
        month_start = as_of_date.replace(day=1)
        disbursement = await self.generate_disbursement_report(org_id, month_start, as_of_date)
        collection = await self.generate_collection_report(org_id, month_start, as_of_date)
        profitability = await self.generate_profitability_report(org_id, month_start, as_of_date)

        latest_alm = await self.db.scalar(
            select(ALMPosition.net_position)
            .where(ALMPosition.organization_id == org_id, ALMPosition.position_date <= as_of_date)
            .order_by(desc(ALMPosition.position_date))
            .limit(1)
        )
        pending_vouchers = await self.db.scalar(
            select(func.count(Voucher.id)).where(
                Voucher.organization_id == org_id,
                Voucher.status.in_(["DRAFT", "PENDING_APPROVAL", "APPROVED"]),
            )
        )
        overdue_compliance = await self.db.scalar(
            select(func.count(ComplianceInstance.id))
            .join(ComplianceItem, ComplianceItem.id == ComplianceInstance.compliance_item_id)
            .where(
                ComplianceItem.organization_id == org_id,
                ComplianceInstance.actual_due_date < as_of_date,
                ComplianceInstance.status.notin_(["FILED", "COMPLETED"]),
            )
        )
        failed_jobs = await self.db.scalar(
            select(func.count(BackgroundJob.id)).where(
                BackgroundJob.organization_id == org_id,
                BackgroundJob.status == "FAILED",
            )
        )
        active_schedules = await self.list_schedules(org_id, active_only=True, limit=5)
        recent_runs = await self.list_runs(org_id, limit=5)

        summary = portfolio.summary
        gnpa = _pct(
            sum(
                (
                    item.amount
                    for item in portfolio.asset_quality_breakdown
                    if item.name in {c.value for c in NPA_CLASSIFICATIONS}
                ),
                ZERO,
            ),
            summary.total_outstanding,
        )

        return DashboardSummary(
            as_of_date=as_of_date,
            generated_at=_now(),
            executive_metrics=[
                MISMetric(
                    code="AUM", label="AUM", value=summary.total_outstanding, value_type="AMOUNT"
                ),
                MISMetric(
                    code="GNPA", label="Gross NPA", value=gnpa, value_type="PERCENTAGE", unit="%"
                ),
                MISMetric(
                    code="COLLECTION_EFFICIENCY",
                    label="Collection efficiency",
                    value=collection.summary.collection_efficiency,
                    value_type="PERCENTAGE",
                    unit="%",
                ),
                MISMetric(
                    code="DISBURSEMENT_MTD",
                    label="Disbursement MTD",
                    value=disbursement.summary.total_amount,
                    value_type="AMOUNT",
                ),
                MISMetric(
                    code="NIM",
                    label="Net interest margin",
                    value=profitability.summary.net_interest_margin,
                    value_type="PERCENTAGE",
                    unit="%",
                ),
                MISMetric(
                    code="ALM_GAP",
                    label="Latest ALM net gap",
                    value=_decimal(latest_alm),
                    value_type="AMOUNT",
                ),
            ],
            module_metrics=[
                MISMetric(
                    code="ACTIVE_ACCOUNTS",
                    label="Active loan accounts",
                    value=summary.active_accounts,
                ),
                MISMetric(
                    code="BORROWING_COST",
                    label="Cost of funds",
                    value=profitability.summary.cost_of_funds,
                    value_type="PERCENTAGE",
                    unit="%",
                ),
                MISMetric(
                    code="LOAN_YIELD",
                    label="Loan yield",
                    value=profitability.summary.loan_yield,
                    value_type="PERCENTAGE",
                    unit="%",
                ),
                MISMetric(
                    code="SPREAD",
                    label="Yield spread",
                    value=profitability.summary.spread,
                    value_type="PERCENTAGE",
                    unit="%",
                ),
            ],
            exception_metrics=[
                MISMetric(
                    code="TOTAL_OVERDUE",
                    label="Total overdue",
                    value=summary.total_overdue,
                    value_type="AMOUNT",
                    status="WARN" if summary.total_overdue > ZERO else "OK",
                ),
                MISMetric(
                    code="PENDING_VOUCHERS",
                    label="Vouchers pending posting/approval",
                    value=int(pending_vouchers or 0),
                    status="WARN" if pending_vouchers else "OK",
                ),
                MISMetric(
                    code="OVERDUE_COMPLIANCE",
                    label="Overdue compliance items",
                    value=int(overdue_compliance or 0),
                    status="WARN" if overdue_compliance else "OK",
                ),
                MISMetric(
                    code="FAILED_JOBS",
                    label="Failed background jobs",
                    value=int(failed_jobs or 0),
                    status="WARN" if failed_jobs else "OK",
                ),
            ],
            recent_runs=recent_runs,
            active_schedules=active_schedules,
        )

    async def generate_portfolio_summary(
        self, org_id: UUID, as_of_date: date, unit_id: UUID | None = None
    ) -> PortfolioSummaryResponse:
        filters = [
            LoanAccount.organization_id == org_id,
            LoanAccount.account_open_date <= as_of_date,
        ]
        if unit_id:
            filters.append(LoanApplication.branch_id == unit_id)
            base_from = LoanAccount.__table__.join(
                LoanSanction, LoanSanction.id == LoanAccount.sanction_id
            ).join(LoanApplication, LoanApplication.id == LoanSanction.application_id)
        else:
            base_from = LoanAccount.__table__

        row = (
            await self.db.execute(
                select(
                    func.count(LoanAccount.id),
                    func.count(case((LoanAccount.status == LoanAccountStatus.ACTIVE, 1))),
                    func.count(case((LoanAccount.status == LoanAccountStatus.CLOSED, 1))),
                    func.count(case((LoanAccount.status == LoanAccountStatus.WRITTEN_OFF, 1))),
                    func.coalesce(func.sum(LoanAccount.sanctioned_amount), 0),
                    func.coalesce(func.sum(LoanAccount.total_disbursed_amount), 0),
                    func.coalesce(func.sum(LoanAccount.principal_outstanding), 0),
                    func.coalesce(func.sum(LoanAccount.interest_outstanding), 0),
                    func.coalesce(func.sum(LoanAccount.total_outstanding), 0),
                    func.coalesce(func.sum(LoanAccount.principal_overdue), 0),
                    func.coalesce(func.sum(LoanAccount.interest_overdue), 0),
                    func.coalesce(
                        func.sum(
                            LoanAccount.principal_overdue
                            + LoanAccount.interest_overdue
                            + LoanAccount.penal_interest_outstanding
                            + LoanAccount.charges_outstanding
                        ),
                        0,
                    ),
                    func.coalesce(func.avg(LoanAccount.current_interest_rate), 0),
                )
                .select_from(base_from)
                .where(*filters)
            )
        ).one()
        total_outstanding = _decimal(row[8])
        active_accounts = int(row[1] or 0)
        summary = PortfolioSummary(
            total_accounts=int(row[0] or 0),
            active_accounts=active_accounts,
            closed_accounts=int(row[2] or 0),
            written_off_accounts=int(row[3] or 0),
            total_sanctioned=_decimal(row[4]),
            total_disbursed=_decimal(row[5]),
            principal_outstanding=_decimal(row[6]),
            interest_outstanding=_decimal(row[7]),
            total_outstanding=total_outstanding,
            principal_overdue=_decimal(row[9]),
            interest_overdue=_decimal(row[10]),
            total_overdue=_decimal(row[11]),
            average_ticket_size=(
                (_decimal(row[4]) / active_accounts).quantize(Decimal("0.01"))
                if active_accounts
                else ZERO
            ),
            weighted_average_yield=_decimal(row[12]).quantize(Decimal("0.01")),
        )

        product_rows = (
            await self.db.execute(
                select(
                    LoanProduct.name,
                    func.count(LoanAccount.id),
                    func.coalesce(func.sum(LoanAccount.total_outstanding), 0),
                    func.coalesce(func.avg(LoanAccount.current_interest_rate), 0),
                )
                .join(LoanProduct, LoanProduct.id == LoanAccount.product_id)
                .where(
                    LoanAccount.organization_id == org_id,
                    LoanAccount.account_open_date <= as_of_date,
                )
                .group_by(LoanProduct.name)
                .order_by(desc(func.coalesce(func.sum(LoanAccount.total_outstanding), 0)))
            )
        ).all()
        product_breakdown = [
            PortfolioBreakdownItem(
                name=name or "Unmapped",
                count=int(count or 0),
                amount=_decimal(amount),
                share_percent=_pct(_decimal(amount), total_outstanding),
                average_yield=_decimal(avg_yield).quantize(Decimal("0.01")),
            )
            for name, count, amount, avg_yield in product_rows
        ]

        asset_rows = (
            await self.db.execute(
                select(
                    LoanAccount.asset_classification,
                    func.count(LoanAccount.id),
                    func.coalesce(func.sum(LoanAccount.total_outstanding), 0),
                )
                .where(
                    LoanAccount.organization_id == org_id,
                    LoanAccount.account_open_date <= as_of_date,
                )
                .group_by(LoanAccount.asset_classification)
            )
        ).all()
        asset_quality = [
            PortfolioBreakdownItem(
                name=_enum_value(name),
                count=int(count or 0),
                amount=_decimal(amount),
                share_percent=_pct(_decimal(amount), total_outstanding),
            )
            for name, count, amount in asset_rows
        ]

        top_rows = (
            await self.db.execute(
                select(
                    LoanAccount.loan_account_number,
                    Entity.legal_name,
                    LoanProduct.name,
                    LoanAccount.total_outstanding,
                    LoanAccount.current_interest_rate,
                    LoanAccount.asset_classification,
                )
                .join(Entity, Entity.id == LoanAccount.entity_id)
                .join(LoanProduct, LoanProduct.id == LoanAccount.product_id)
                .where(LoanAccount.organization_id == org_id, LoanAccount.total_outstanding > 0)
                .order_by(desc(LoanAccount.total_outstanding))
                .limit(10)
            )
        ).all()
        top_exposures = [
            {
                "loanAccountNumber": account_number,
                "borrowerName": borrower,
                "productName": product,
                "outstandingAmount": _decimal(amount),
                "interestRate": _decimal(rate),
                "classification": _enum_value(classification),
            }
            for account_number, borrower, product, amount, rate, classification in top_rows
        ]
        return PortfolioSummaryResponse(
            as_of_date=as_of_date,
            generated_at=_now(),
            summary=summary,
            product_breakdown=product_breakdown,
            asset_quality_breakdown=asset_quality,
            top_exposures=top_exposures,
        )

    async def generate_disbursement_report(
        self, org_id: UUID, from_date: date, to_date: date, group_by: str = "PRODUCT"
    ) -> DisbursementReportResponse:
        filters = [
            LoanAccount.organization_id == org_id,
            Disbursement.status == DisbursementStatus.PROCESSED,
            Disbursement.disbursement_date >= from_date,
            Disbursement.disbursement_date <= to_date,
        ]
        total_row = (
            await self.db.execute(
                select(
                    func.count(Disbursement.id),
                    func.coalesce(func.sum(Disbursement.disbursed_amount), 0),
                )
                .join(LoanAccount, LoanAccount.id == Disbursement.loan_account_id)
                .where(*filters)
            )
        ).one()
        total_count = int(total_row[0] or 0)
        total_amount = _decimal(total_row[1])
        summary = PeriodSummary(
            total_count=total_count,
            total_amount=total_amount,
            average_ticket_size=(
                (total_amount / total_count).quantize(Decimal("0.01")) if total_count else ZERO
            ),
        )

        if group_by == "BRANCH":
            label_col = func.coalesce(Unit.name, "Unmapped")
            query = (
                select(
                    label_col,
                    func.count(Disbursement.id),
                    func.coalesce(func.sum(Disbursement.disbursed_amount), 0),
                )
                .join(LoanAccount, LoanAccount.id == Disbursement.loan_account_id)
                .join(LoanSanction, LoanSanction.id == LoanAccount.sanction_id)
                .join(LoanApplication, LoanApplication.id == LoanSanction.application_id)
                .outerjoin(Unit, Unit.id == LoanApplication.branch_id)
                .where(*filters)
                .group_by(label_col)
            )
        elif group_by == "CHANNEL":
            label_col = Disbursement.disbursement_mode
            query = (
                select(
                    label_col,
                    func.count(Disbursement.id),
                    func.coalesce(func.sum(Disbursement.disbursed_amount), 0),
                )
                .join(LoanAccount, LoanAccount.id == Disbursement.loan_account_id)
                .where(*filters)
                .group_by(label_col)
            )
        else:
            label_col = LoanProduct.name
            query = (
                select(
                    label_col,
                    func.count(Disbursement.id),
                    func.coalesce(func.sum(Disbursement.disbursed_amount), 0),
                )
                .join(LoanAccount, LoanAccount.id == Disbursement.loan_account_id)
                .join(LoanProduct, LoanProduct.id == LoanAccount.product_id)
                .where(*filters)
                .group_by(label_col)
            )
        rows = (
            await self.db.execute(
                query.order_by(desc(func.coalesce(func.sum(Disbursement.disbursed_amount), 0)))
            )
        ).all()
        breakdown = [
            DisbursementBreakdownItem(
                name=_enum_value(name) or "Unmapped",
                count=int(count or 0),
                amount=_decimal(amount),
                average_ticket_size=(
                    (_decimal(amount) / int(count)).quantize(Decimal("0.01")) if count else ZERO
                ),
                share_percent=_pct(_decimal(amount), total_amount),
            )
            for name, count, amount in rows
        ]
        daily_rows = (
            await self.db.execute(
                select(
                    Disbursement.disbursement_date,
                    func.count(Disbursement.id),
                    func.coalesce(func.sum(Disbursement.disbursed_amount), 0),
                )
                .join(LoanAccount, LoanAccount.id == Disbursement.loan_account_id)
                .where(*filters)
                .group_by(Disbursement.disbursement_date)
                .order_by(Disbursement.disbursement_date)
            )
        ).all()
        return DisbursementReportResponse(
            period=ReportPeriod(from_date=from_date, to_date=to_date),
            generated_at=_now(),
            summary=summary,
            breakdown=breakdown,
            daily_trend=[
                DailyTrendItem(date=row_date, count=int(count or 0), amount=_decimal(amount))
                for row_date, count, amount in daily_rows
            ],
        )

    async def generate_collection_report(
        self, org_id: UUID, from_date: date, to_date: date
    ) -> CollectionReportResponse:
        demand = await self.db.scalar(
            select(func.coalesce(func.sum(ScheduleInstallment.emi_amount), 0))
            .join(RepaymentSchedule, RepaymentSchedule.id == ScheduleInstallment.schedule_id)
            .join(LoanAccount, LoanAccount.id == RepaymentSchedule.loan_account_id)
            .where(
                LoanAccount.organization_id == org_id,
                RepaymentSchedule.is_current.is_(True),
                ScheduleInstallment.due_date >= from_date,
                ScheduleInstallment.due_date <= to_date,
            )
        )
        receipt_row = (
            await self.db.execute(
                select(
                    func.coalesce(func.sum(LoanReceipt.receipt_amount), 0),
                    func.coalesce(func.sum(LoanReceipt.principal_allocated), 0),
                    func.coalesce(func.sum(LoanReceipt.interest_allocated), 0),
                    func.coalesce(func.sum(LoanReceipt.penal_interest_allocated), 0),
                    func.coalesce(func.sum(LoanReceipt.charges_allocated), 0),
                ).where(
                    LoanReceipt.organization_id == org_id,
                    LoanReceipt.receipt_date >= from_date,
                    LoanReceipt.receipt_date <= to_date,
                    LoanReceipt.status != ReceiptStatus.REVERSED,
                )
            )
        ).one()
        total_demand = _decimal(demand)
        total_collected = _decimal(receipt_row[0])
        summary = CollectionSummary(
            total_demand=total_demand,
            total_collected=total_collected,
            collection_efficiency=_pct(total_collected, total_demand),
            principal_collected=_decimal(receipt_row[1]),
            interest_collected=_decimal(receipt_row[2]),
            penal_collected=_decimal(receipt_row[3]),
            charges_collected=_decimal(receipt_row[4]),
            shortfall=max(total_demand - total_collected, ZERO),
        )
        mode_rows = (
            await self.db.execute(
                select(
                    LoanReceipt.receipt_mode, func.coalesce(func.sum(LoanReceipt.receipt_amount), 0)
                )
                .where(
                    LoanReceipt.organization_id == org_id,
                    LoanReceipt.receipt_date >= from_date,
                    LoanReceipt.receipt_date <= to_date,
                    LoanReceipt.status != ReceiptStatus.REVERSED,
                )
                .group_by(LoanReceipt.receipt_mode)
                .order_by(desc(func.coalesce(func.sum(LoanReceipt.receipt_amount), 0)))
            )
        ).all()
        mode_wise = [
            CollectionModeItem(
                mode=_enum_value(mode),
                amount=_decimal(amount),
                share_percent=_pct(_decimal(amount), total_collected),
            )
            for mode, amount in mode_rows
        ]
        bucket_wise = await self._collection_bucket_wise(org_id)
        return CollectionReportResponse(
            period=ReportPeriod(from_date=from_date, to_date=to_date),
            generated_at=_now(),
            summary=summary,
            mode_wise=mode_wise,
            bucket_wise=bucket_wise,
        )

    async def _collection_bucket_wise(self, org_id: UUID) -> list[CollectionBucketItem]:
        rows = (
            await self.db.execute(
                select(
                    case(
                        (LoanAccount.days_past_due <= 0, "Current"),
                        (LoanAccount.days_past_due <= 30, "1-30 DPD"),
                        (LoanAccount.days_past_due <= 60, "31-60 DPD"),
                        (LoanAccount.days_past_due <= 90, "61-90 DPD"),
                        else_=">90 DPD",
                    ).label("bucket"),
                    func.coalesce(
                        func.sum(LoanAccount.principal_overdue + LoanAccount.interest_overdue), 0
                    ),
                    func.coalesce(
                        func.sum(
                            LoanAccount.total_principal_received
                            + LoanAccount.total_interest_received
                        ),
                        0,
                    ),
                )
                .where(LoanAccount.organization_id == org_id)
                .group_by("bucket")
            )
        ).all()
        items: list[CollectionBucketItem] = []
        for bucket, demand, collected in rows:
            demand_amount = _decimal(demand)
            collected_amount = _decimal(collected)
            items.append(
                CollectionBucketItem(
                    bucket=bucket,
                    demand=demand_amount,
                    collected=collected_amount,
                    shortfall=max(demand_amount - collected_amount, ZERO),
                    efficiency=_pct(collected_amount, demand_amount),
                )
            )
        return items

    async def generate_delinquency_report(
        self, org_id: UUID, as_of_date: date
    ) -> DelinquencyReportResponse:
        rows = (
            await self.db.execute(
                select(
                    case(
                        (LoanAccount.days_past_due <= 0, "Current"),
                        (LoanAccount.days_past_due <= 30, "1-30 DPD"),
                        (LoanAccount.days_past_due <= 60, "31-60 DPD"),
                        (LoanAccount.days_past_due <= 90, "61-90 DPD"),
                        (LoanAccount.days_past_due <= 180, "91-180 DPD"),
                        else_=">180 DPD",
                    ).label("bucket"),
                    LoanAccount.asset_classification,
                    func.count(LoanAccount.id),
                    func.coalesce(func.sum(LoanAccount.total_outstanding), 0),
                )
                .where(
                    LoanAccount.organization_id == org_id,
                    LoanAccount.account_open_date <= as_of_date,
                )
                .group_by("bucket", LoanAccount.asset_classification)
            )
        ).all()
        total_outstanding = sum((_decimal(amount) for _, _, _, amount in rows), ZERO)
        total_delinquent = sum(
            (_decimal(amount) for bucket, _, _, amount in rows if bucket != "Current"), ZERO
        )
        buckets = [
            DelinquencyBucketItem(
                bucket=bucket,
                accounts=int(count or 0),
                amount=_decimal(amount),
                share_percent=_pct(_decimal(amount), total_outstanding),
                classification=_enum_value(classification),
            )
            for bucket, classification, count, amount in rows
        ]
        top_rows = (
            await self.db.execute(
                select(
                    LoanAccount.loan_account_number,
                    Entity.legal_name,
                    LoanProduct.name,
                    LoanAccount.total_outstanding,
                    LoanAccount.days_past_due,
                    LoanAccount.asset_classification,
                )
                .join(Entity, Entity.id == LoanAccount.entity_id)
                .join(LoanProduct, LoanProduct.id == LoanAccount.product_id)
                .where(LoanAccount.organization_id == org_id, LoanAccount.days_past_due > 0)
                .order_by(desc(LoanAccount.days_past_due), desc(LoanAccount.total_outstanding))
                .limit(10)
            )
        ).all()
        return DelinquencyReportResponse(
            as_of_date=as_of_date,
            generated_at=_now(),
            summary=DelinquencySummary(
                total_outstanding=total_outstanding,
                total_delinquent=total_delinquent,
                delinquency_rate=_pct(total_delinquent, total_outstanding),
                overdue_accounts=sum(item.accounts for item in buckets if item.bucket != "Current"),
            ),
            buckets=buckets,
            top_delinquent_accounts=[
                TopDelinquentAccount(
                    loan_account_number=loan_number,
                    borrower_name=borrower,
                    product_name=product,
                    outstanding_amount=_decimal(amount),
                    days_past_due=int(dpd or 0),
                    classification=_enum_value(classification),
                )
                for loan_number, borrower, product, amount, dpd, classification in top_rows
            ],
        )

    async def generate_profitability_report(
        self, org_id: UUID, from_date: date, to_date: date
    ) -> ProfitabilityReportResponse:
        interest_income = await self.db.scalar(
            select(
                func.coalesce(
                    func.sum(
                        LoanReceipt.interest_allocated
                        + LoanReceipt.penal_interest_allocated
                        + LoanReceipt.charges_allocated
                    ),
                    0,
                )
            ).where(
                LoanReceipt.organization_id == org_id,
                LoanReceipt.receipt_date >= from_date,
                LoanReceipt.receipt_date <= to_date,
                LoanReceipt.status != ReceiptStatus.REVERSED,
            )
        )
        interest_expense = await self.db.scalar(
            select(
                func.coalesce(
                    func.sum(BorrowingPayment.interest_amount + BorrowingPayment.fee_amount), 0
                )
            )
            .join(Borrowing, Borrowing.borrowing_id == BorrowingPayment.borrowing_id)
            .where(
                Borrowing.organization_id == org_id,
                BorrowingPayment.payment_date >= from_date,
                BorrowingPayment.payment_date <= to_date,
            )
        )
        provision_expense = await self.db.scalar(
            select(func.coalesce(func.sum(LoanAccount.provision_amount), 0)).where(
                LoanAccount.organization_id == org_id
            )
        )
        operating_expense = await self.db.scalar(
            select(
                func.coalesce(func.sum(GLEntry.base_debit_amount - GLEntry.base_credit_amount), 0)
            )
            .join(Account, Account.id == GLEntry.account_id)
            .where(
                GLEntry.organization_id == org_id,
                GLEntry.voucher_date >= from_date,
                GLEntry.voucher_date <= to_date,
                or_(Account.name.ilike("%expense%"), Account.name.ilike("%cost%")),
                ~Account.name.ilike("%interest%"),
                ~Account.name.ilike("%provision%"),
            )
        )
        loan_rate_row = (
            await self.db.execute(
                select(
                    func.coalesce(
                        func.sum(LoanAccount.total_outstanding * LoanAccount.current_interest_rate),
                        0,
                    ),
                    func.coalesce(func.sum(LoanAccount.total_outstanding), 0),
                ).where(LoanAccount.organization_id == org_id)
            )
        ).one()
        borrowing_rate_row = (
            await self.db.execute(
                select(
                    func.coalesce(
                        func.sum(Borrowing.principal_outstanding * Borrowing.effective_rate), 0
                    ),
                    func.coalesce(func.sum(Borrowing.principal_outstanding), 0),
                ).where(Borrowing.organization_id == org_id)
            )
        ).one()
        loan_yield = (
            (_decimal(loan_rate_row[0]) / _decimal(loan_rate_row[1])).quantize(Decimal("0.01"))
            if _decimal(loan_rate_row[1])
            else ZERO
        )
        cost_of_funds = (
            (_decimal(borrowing_rate_row[0]) / _decimal(borrowing_rate_row[1])).quantize(
                Decimal("0.01")
            )
            if _decimal(borrowing_rate_row[1])
            else ZERO
        )
        income = _decimal(interest_income)
        expense_interest = _decimal(interest_expense)
        expense_operating = max(_decimal(operating_expense), ZERO)
        expense_provision = _decimal(provision_expense)
        total_expense = expense_interest + expense_operating + expense_provision
        pbt = income - total_expense
        product_rows = (
            await self.db.execute(
                select(
                    LoanProduct.name,
                    func.coalesce(
                        func.sum(
                            LoanReceipt.interest_allocated
                            + LoanReceipt.penal_interest_allocated
                            + LoanReceipt.charges_allocated
                        ),
                        0,
                    ),
                )
                .join(LoanAccount, LoanAccount.id == LoanReceipt.loan_account_id)
                .join(LoanProduct, LoanProduct.id == LoanAccount.product_id)
                .where(
                    LoanReceipt.organization_id == org_id,
                    LoanReceipt.receipt_date >= from_date,
                    LoanReceipt.receipt_date <= to_date,
                    LoanReceipt.status != ReceiptStatus.REVERSED,
                )
                .group_by(LoanProduct.name)
                .order_by(desc(func.coalesce(func.sum(LoanReceipt.interest_allocated), 0)))
            )
        ).all()
        return ProfitabilityReportResponse(
            period=ReportPeriod(from_date=from_date, to_date=to_date),
            generated_at=_now(),
            summary=ProfitabilitySummary(
                interest_income=income,
                fee_income=ZERO,
                total_income=income,
                interest_expense=expense_interest,
                provision_expense=expense_provision,
                operating_expense=expense_operating,
                total_expense=total_expense,
                profit_before_tax=pbt,
                net_interest_margin=_pct(income - expense_interest, income),
                net_margin=_pct(pbt, income),
                loan_yield=loan_yield,
                cost_of_funds=cost_of_funds,
                spread=loan_yield - cost_of_funds,
            ),
            product_wise=[
                ProfitabilityBreakdownItem(
                    name=name or "Unmapped",
                    income=_decimal(income_amount),
                    expense=ZERO,
                    profit=_decimal(income_amount),
                    margin=Decimal("100.00") if _decimal(income_amount) else ZERO,
                )
                for name, income_amount in product_rows
            ],
        )

    async def generate_branch_performance_report(
        self, org_id: UUID, from_date: date, to_date: date
    ) -> BranchPerformanceResponse:
        rows = (
            await self.db.execute(
                select(
                    Unit.id,
                    func.coalesce(Unit.name, "Unmapped"),
                    func.count(func.distinct(LoanApplication.id)),
                    func.coalesce(func.sum(LoanSanction.sanctioned_amount), 0),
                    func.coalesce(func.sum(LoanAccount.total_outstanding), 0),
                    func.coalesce(func.sum(Disbursement.disbursed_amount), 0),
                    func.coalesce(func.sum(LoanReceipt.receipt_amount), 0),
                    func.coalesce(
                        func.sum(
                            case(
                                (
                                    LoanAccount.asset_classification.in_(NPA_CLASSIFICATIONS),
                                    LoanAccount.total_outstanding,
                                ),
                                else_=0,
                            )
                        ),
                        0,
                    ),
                )
                .select_from(LoanApplication)
                .outerjoin(Unit, Unit.id == LoanApplication.branch_id)
                .outerjoin(LoanSanction, LoanSanction.application_id == LoanApplication.id)
                .outerjoin(LoanAccount, LoanAccount.sanction_id == LoanSanction.id)
                .outerjoin(Disbursement, Disbursement.loan_account_id == LoanAccount.id)
                .outerjoin(LoanReceipt, LoanReceipt.loan_account_id == LoanAccount.id)
                .where(
                    LoanApplication.organization_id == org_id,
                    LoanApplication.application_date >= from_date,
                    LoanApplication.application_date <= to_date,
                )
                .group_by(Unit.id, Unit.name)
            )
        ).all()
        branches = []
        for (
            branch_id,
            branch_name,
            apps,
            sanction_amount,
            aum,
            disbursement,
            collection,
            npa_amount,
        ) in rows:
            aum_dec = _decimal(aum)
            demand_proxy = aum_dec if aum_dec > ZERO else _decimal(disbursement)
            branches.append(
                BranchPerformanceItem(
                    branch_id=branch_id,
                    branch_name=branch_name or "Unmapped",
                    aum=aum_dec,
                    disbursement=_decimal(disbursement),
                    collection=_decimal(collection),
                    collection_efficiency=_pct(_decimal(collection), demand_proxy),
                    npa_percentage=_pct(_decimal(npa_amount), aum_dec),
                    applications=int(apps or 0),
                    sanctioned_amount=_decimal(sanction_amount),
                )
            )
        return BranchPerformanceResponse(
            period=ReportPeriod(from_date=from_date, to_date=to_date),
            generated_at=_now(),
            branches=branches,
            summary={
                "totalBranches": len(branches),
                "totalAum": sum((b.aum for b in branches), ZERO),
                "totalDisbursement": sum((b.disbursement for b in branches), ZERO),
                "totalCollection": sum((b.collection for b in branches), ZERO),
            },
        )

    async def generate_employee_productivity_report(
        self, org_id: UUID, from_date: date, to_date: date
    ) -> dict[str, Any]:
        application_count = await self.db.scalar(
            select(func.count(LoanApplication.id)).where(
                LoanApplication.organization_id == org_id,
                LoanApplication.application_date >= from_date,
                LoanApplication.application_date <= to_date,
            )
        )
        employee_count = await self.db.scalar(
            select(func.count(Employee.id)).where(Employee.organization_id == org_id)
        )
        attendance_count = await self.db.scalar(
            select(func.count(MonthlyAttendanceSummary.id))
            .join(Employee, Employee.id == MonthlyAttendanceSummary.employee_id)
            .where(Employee.organization_id == org_id)
        )
        return {
            "reportType": "EMPLOYEE_PRODUCTIVITY",
            "period": {"fromDate": from_date, "toDate": to_date},
            "generatedAt": _now(),
            "summary": {
                "applicationsHandled": int(application_count or 0),
                "activeEmployees": int(employee_count or 0),
                "attendanceSummaries": int(attendance_count or 0),
            },
            "teamRows": [],
        }

    async def generate_all_modules_report(
        self,
        org_id: UUID,
        from_date: date,
        to_date: date,
        as_of_date: date,
    ) -> AllModulesReportResponse:
        """Generate live module-level MIS across the full ERP surface."""
        modules = [
            await self._finance_module(org_id, from_date, to_date),
            await self._tax_module(org_id, from_date, to_date, as_of_date),
            await self._compliance_module(org_id, from_date, to_date, as_of_date),
            await self._fixed_assets_module(org_id, as_of_date),
            await self._fixed_deposits_module(org_id, as_of_date),
            await self._inventory_module(org_id, from_date, to_date),
            await self._hris_module(org_id, from_date, to_date),
            await self._payroll_module(org_id, from_date, to_date),
            await self._portal_module(org_id, from_date, to_date),
            await self._vendor_module(org_id, from_date, to_date),
            await self._dms_module(org_id, as_of_date),
            await self._workflow_module(org_id, as_of_date),
            await self._audit_system_module(org_id, from_date, to_date),
        ]
        return AllModulesReportResponse(
            period=ReportPeriod(from_date=from_date, to_date=to_date),
            as_of_date=as_of_date,
            generated_at=_now(),
            modules=modules,
        )

    def _metric(
        self,
        code: str,
        label: str,
        value: Decimal | int | float | str,
        value_type: str = "NUMBER",
        status: str = "OK",
        description: str | None = None,
    ) -> MISMetric:
        return MISMetric(
            code=code,
            label=label,
            value=value,
            value_type=value_type,
            status=status,
            description=description,
        )

    async def _finance_module(
        self, org_id: UUID, from_date: date, to_date: date
    ) -> ModuleReportSection:
        voucher_row = (
            await self.db.execute(
                select(
                    func.count(Voucher.id),
                    func.count(case((Voucher.is_posted.is_(True), 1))),
                    func.count(case((Voucher.is_posted.is_(False), 1))),
                ).where(
                    Voucher.organization_id == org_id,
                    Voucher.voucher_date >= from_date,
                    Voucher.voucher_date <= to_date,
                )
            )
        ).one()
        gl_row = (
            await self.db.execute(
                select(
                    func.count(GLEntry.id),
                    func.coalesce(func.sum(GLEntry.base_debit_amount), 0),
                    func.coalesce(func.sum(GLEntry.base_credit_amount), 0),
                ).where(
                    GLEntry.organization_id == org_id,
                    GLEntry.voucher_date >= from_date,
                    GLEntry.voucher_date <= to_date,
                )
            )
        ).one()
        ap_row = (
            await self.db.execute(
                select(
                    func.count(PurchaseBill.id),
                    func.coalesce(func.sum(PurchaseBill.total_amount), 0),
                    func.coalesce(func.sum(PurchaseBill.balance_amount), 0),
                    func.count(case((PurchaseBill.is_posted.is_(False), 1))),
                ).where(
                    PurchaseBill.organization_id == org_id,
                    PurchaseBill.bill_date >= from_date,
                    PurchaseBill.bill_date <= to_date,
                )
            )
        ).one()
        ar_row = (
            await self.db.execute(
                select(
                    func.count(SalesInvoice.id),
                    func.coalesce(func.sum(SalesInvoice.total_amount), 0),
                    func.coalesce(func.sum(SalesInvoice.balance_amount), 0),
                    func.count(case((SalesInvoice.is_posted.is_(False), 1))),
                ).where(
                    SalesInvoice.organization_id == org_id,
                    SalesInvoice.invoice_date >= from_date,
                    SalesInvoice.invoice_date <= to_date,
                )
            )
        ).one()
        brs_unmatched = await self.db.scalar(
            select(func.count(BankStatement.id)).where(
                BankStatement.organization_id == org_id,
                BankStatement.reconciliation_status != "RECONCILED",
            )
        )
        pending_postings = int(ap_row[3] or 0) + int(ar_row[3] or 0) + int(voucher_row[2] or 0)
        return ModuleReportSection(
            module_code="FINANCE",
            module_name="Finance / Accounting / AP / AR / BRS",
            category="FINANCE",
            route="/admin/reports",
            metrics=[
                self._metric("VOUCHERS", "Vouchers", int(voucher_row[0] or 0)),
                self._metric("GL_DEBIT", "GL debit", _decimal(gl_row[1]), "AMOUNT"),
                self._metric("GL_CREDIT", "GL credit", _decimal(gl_row[2]), "AMOUNT"),
                self._metric("AP_OUTSTANDING", "AP outstanding", _decimal(ap_row[2]), "AMOUNT"),
                self._metric("AR_OUTSTANDING", "AR outstanding", _decimal(ar_row[2]), "AMOUNT"),
            ],
            rows=[
                ModuleReportRow(
                    label="Voucher register",
                    route="/admin/finance/vouchers",
                    values={
                        "count": int(voucher_row[0] or 0),
                        "posted": int(voucher_row[1] or 0),
                        "pending": int(voucher_row[2] or 0),
                    },
                    status="WARN" if voucher_row[2] else "OK",
                ),
                ModuleReportRow(
                    label="Purchase bills / AP",
                    route="/admin/ap-ar/purchase-bills",
                    values={
                        "count": int(ap_row[0] or 0),
                        "total": _decimal(ap_row[1]),
                        "outstanding": _decimal(ap_row[2]),
                        "unposted": int(ap_row[3] or 0),
                    },
                    status="WARN" if ap_row[3] else "OK",
                ),
                ModuleReportRow(
                    label="Sales invoices / AR",
                    route="/admin/ap-ar/sales-invoices",
                    values={
                        "count": int(ar_row[0] or 0),
                        "total": _decimal(ar_row[1]),
                        "outstanding": _decimal(ar_row[2]),
                        "unposted": int(ar_row[3] or 0),
                    },
                    status="WARN" if ar_row[3] else "OK",
                ),
                ModuleReportRow(
                    label="Bank reconciliation",
                    route="/admin/ap-ar/bank-reconciliation",
                    values={"unmatchedStatements": int(brs_unmatched or 0)},
                    status="WARN" if brs_unmatched else "OK",
                ),
            ],
            exceptions=[
                self._metric(
                    "PENDING_POSTINGS",
                    "Pending postings",
                    pending_postings,
                    status="WARN" if pending_postings else "OK",
                )
            ],
        )

    async def _tax_module(
        self, org_id: UUID, from_date: date, to_date: date, as_of_date: date
    ) -> ModuleReportSection:
        output_gst_row = (
            await self.db.execute(
                select(
                    func.coalesce(
                        func.sum(
                            SalesInvoice.cgst_amount
                            + SalesInvoice.sgst_amount
                            + SalesInvoice.igst_amount
                            + SalesInvoice.cess_amount
                        ),
                        0,
                    ),
                    func.coalesce(
                        func.sum(
                            PurchaseBill.cgst_amount
                            + PurchaseBill.sgst_amount
                            + PurchaseBill.igst_amount
                            + PurchaseBill.cess_amount
                        ),
                        0,
                    ),
                    func.count(case((SalesInvoice.e_invoice_required.is_(True), 1))),
                    func.count(case((SalesInvoice.eway_bill_number.isnot(None), 1))),
                ).where(
                    SalesInvoice.organization_id == org_id,
                    SalesInvoice.invoice_date >= from_date,
                    SalesInvoice.invoice_date <= to_date,
                )
            )
        ).one()
        input_gst = await self.db.scalar(
            select(
                func.coalesce(
                    func.sum(
                        PurchaseBill.cgst_amount
                        + PurchaseBill.sgst_amount
                        + PurchaseBill.igst_amount
                        + PurchaseBill.cess_amount
                    ),
                    0,
                )
            ).where(
                PurchaseBill.organization_id == org_id,
                PurchaseBill.bill_date >= from_date,
                PurchaseBill.bill_date <= to_date,
            )
        )
        gst_return_row = (
            await self.db.execute(
                select(
                    func.count(GSTReturnFiling.id),
                    func.count(case((GSTReturnFiling.status == "FILED", 1))),
                    func.count(case((GSTReturnFiling.status != "FILED", 1))),
                    func.coalesce(func.sum(GSTReturnFiling.total_tax_liability), 0),
                    func.coalesce(func.sum(GSTReturnFiling.total_itc_claimed), 0),
                ).where(GSTReturnFiling.organization_id == org_id)
            )
        ).one()
        tds_row = (
            await self.db.execute(
                select(
                    func.count(TDSEntry.id),
                    func.coalesce(func.sum(TDSEntry.total_tds), 0),
                    func.count(case((TDSEntry.challan_status == "PENDING", 1))),
                    func.count(case((TDSEntry.return_filed.is_(False), 1))),
                ).where(
                    TDSEntry.organization_id == org_id,
                    TDSEntry.deduction_date >= from_date,
                    TDSEntry.deduction_date <= to_date,
                )
            )
        ).one()
        challan_row = (
            await self.db.execute(
                select(
                    func.count(TDSChallan.id),
                    func.count(case((TDSChallan.status.in_(["PAID", "VERIFIED"]), 1))),
                    func.coalesce(func.sum(TDSChallan.total_amount), 0),
                ).where(TDSChallan.organization_id == org_id)
            )
        ).one()
        return_row = (
            await self.db.execute(
                select(
                    func.count(TDSReturn.id),
                    func.count(case((TDSReturn.status == "FILED", 1))),
                ).where(TDSReturn.organization_id == org_id)
            )
        ).one()
        output_gst = _decimal(output_gst_row[0]) + _decimal(gst_return_row[3])
        total_input_gst = _decimal(input_gst) + _decimal(gst_return_row[4])
        gst_payable = max(output_gst - total_input_gst, ZERO)
        exceptions = int(gst_return_row[2] or 0) + int(tds_row[2] or 0) + int(tds_row[3] or 0)
        return ModuleReportSection(
            module_code="TAX",
            module_name="GST / TDS / Indian Tax",
            category="TAX_COMPLIANCE",
            route="/admin/gst",
            metrics=[
                self._metric("OUTPUT_GST", "Output GST", output_gst, "AMOUNT"),
                self._metric("ITC", "ITC / input GST", total_input_gst, "AMOUNT"),
                self._metric("GST_PAYABLE", "Net GST payable", gst_payable, "AMOUNT"),
                self._metric("TDS_DEDUCTED", "TDS deducted", _decimal(tds_row[1]), "AMOUNT"),
            ],
            rows=[
                ModuleReportRow(
                    label="GST return working",
                    route="/admin/gst/gstn/gstr3b",
                    values={
                        "returns": int(gst_return_row[0] or 0),
                        "filed": int(gst_return_row[1] or 0),
                        "open": int(gst_return_row[2] or 0),
                        "manualStatus": "Manual working; no live GSTN filing",
                    },
                    status="WARN" if gst_return_row[2] else "OK",
                ),
                ModuleReportRow(
                    label="E-invoice / e-way reference register",
                    route="/admin/gst/gstn",
                    values={
                        "einvoiceRequired": int(output_gst_row[1] or 0),
                        "ewayReferences": int(output_gst_row[2] or 0),
                        "asOfDate": as_of_date.isoformat(),
                    },
                ),
                ModuleReportRow(
                    label="TDS entries and challans",
                    route="/admin/tds/entries",
                    values={
                        "entries": int(tds_row[0] or 0),
                        "challans": int(challan_row[0] or 0),
                        "paidChallans": int(challan_row[1] or 0),
                        "challanAmount": _decimal(challan_row[2]),
                    },
                    status="WARN" if tds_row[2] else "OK",
                ),
                ModuleReportRow(
                    label="TDS returns / Form 16A working",
                    route="/admin/tds/returns",
                    values={
                        "returns": int(return_row[0] or 0),
                        "filed": int(return_row[1] or 0),
                        "entriesPendingReturn": int(tds_row[3] or 0),
                    },
                    status="WARN" if tds_row[3] else "OK",
                ),
            ],
            exceptions=[
                self._metric(
                    "TAX_OPEN_ITEMS",
                    "Open tax items",
                    exceptions,
                    status="WARN" if exceptions else "OK",
                )
            ],
        )

    async def _compliance_module(
        self, org_id: UUID, from_date: date, to_date: date, as_of_date: date
    ) -> ModuleReportSection:
        row = (
            await self.db.execute(
                select(
                    func.count(ComplianceInstance.id),
                    func.count(case((ComplianceInstance.status.in_(["FILED", "COMPLETED"]), 1))),
                    func.count(
                        case(
                            (
                                ComplianceInstance.actual_due_date < as_of_date,
                                1,
                            )
                        )
                    ),
                    func.count(
                        case(
                            (
                                ComplianceInstance.actual_due_date.between(from_date, to_date),
                                1,
                            )
                        )
                    ),
                )
                .join(ComplianceItem, ComplianceItem.id == ComplianceInstance.compliance_item_id)
                .where(ComplianceItem.organization_id == org_id)
            )
        ).one()
        overdue = int(row[2] or 0)
        return ModuleReportSection(
            module_code="COMPLIANCE",
            module_name="Compliance Calendar",
            category="TAX_COMPLIANCE",
            route="/admin/compliance",
            metrics=[
                self._metric("TOTAL_FILINGS", "Compliance instances", int(row[0] or 0)),
                self._metric("FILED", "Filed / completed", int(row[1] or 0)),
                self._metric("DUE_IN_PERIOD", "Due in period", int(row[3] or 0)),
                self._metric("OVERDUE", "Overdue", overdue, status="WARN" if overdue else "OK"),
            ],
            rows=[
                ModuleReportRow(
                    label="Statutory filing tracker",
                    route="/admin/compliance",
                    values={
                        "total": int(row[0] or 0),
                        "filed": int(row[1] or 0),
                        "overdue": overdue,
                    },
                    status="WARN" if overdue else "OK",
                )
            ],
            exceptions=[
                self._metric(
                    "OVERDUE_COMPLIANCE",
                    "Overdue compliance",
                    overdue,
                    status="WARN" if overdue else "OK",
                )
            ],
        )

    async def _fixed_assets_module(self, org_id: UUID, as_of_date: date) -> ModuleReportSection:
        asset_row = (
            await self.db.execute(
                select(
                    func.count(FixedAsset.id),
                    func.coalesce(func.sum(FixedAsset.total_cost), 0),
                    func.coalesce(func.sum(FixedAsset.accumulated_depreciation), 0),
                    func.coalesce(func.sum(FixedAsset.wdv_value), 0),
                    func.count(case((FixedAsset.status == "DISPOSED", 1))),
                ).where(FixedAsset.organization_id == org_id)
            )
        ).one()
        dep_row = (
            await self.db.execute(
                select(
                    func.count(DepreciationRun.id),
                    func.count(case((DepreciationRun.status.notin_(["POSTED", "COMPLETED"]), 1))),
                    func.coalesce(func.sum(DepreciationRun.total_depreciation), 0),
                ).where(DepreciationRun.organization_id == org_id)
            )
        ).one()
        pending_runs = int(dep_row[1] or 0)
        return ModuleReportSection(
            module_code="FIXED_ASSETS",
            module_name="Fixed Assets",
            category="OPERATIONS",
            route="/admin/fixed-assets/reports",
            metrics=[
                self._metric("ASSETS", "Assets", int(asset_row[0] or 0)),
                self._metric("GROSS_BLOCK", "Gross block", _decimal(asset_row[1]), "AMOUNT"),
                self._metric(
                    "ACCUMULATED_DEPRECIATION",
                    "Accumulated depreciation",
                    _decimal(asset_row[2]),
                    "AMOUNT",
                ),
                self._metric("WDV", "Net block / WDV", _decimal(asset_row[3]), "AMOUNT"),
            ],
            rows=[
                ModuleReportRow(
                    label="Asset register",
                    route="/admin/fixed-assets/assets",
                    values={
                        "assets": int(asset_row[0] or 0),
                        "disposed": int(asset_row[4] or 0),
                        "asOfDate": as_of_date.isoformat(),
                    },
                ),
                ModuleReportRow(
                    label="Depreciation schedule",
                    route="/admin/fixed-assets/depreciation",
                    values={
                        "runs": int(dep_row[0] or 0),
                        "pendingRuns": pending_runs,
                        "depreciation": _decimal(dep_row[2]),
                    },
                    status="WARN" if pending_runs else "OK",
                ),
            ],
            exceptions=[
                self._metric(
                    "PENDING_DEPRECIATION",
                    "Pending depreciation runs",
                    pending_runs,
                    status="WARN" if pending_runs else "OK",
                )
            ],
        )

    async def _fixed_deposits_module(self, org_id: UUID, as_of_date: date) -> ModuleReportSection:
        row = (
            await self.db.execute(
                select(
                    func.count(FixedDeposit.id),
                    func.count(case((FixedDeposit.status == "ACTIVE", 1))),
                    func.coalesce(func.sum(FixedDeposit.deposit_amount), 0),
                    func.coalesce(func.sum(FixedDeposit.accrued_interest), 0),
                    func.coalesce(func.sum(FixedDeposit.tds_deducted), 0),
                    func.count(
                        case((FixedDeposit.maturity_date <= as_of_date + timedelta(days=30), 1))
                    ),
                ).where(FixedDeposit.organization_id == org_id)
            )
        ).one()
        upcoming = int(row[5] or 0)
        return ModuleReportSection(
            module_code="FIXED_DEPOSITS",
            module_name="Fixed Deposits",
            category="TREASURY",
            route="/admin/fixed-deposits",
            metrics=[
                self._metric("FD_COUNT", "FD accounts", int(row[0] or 0)),
                self._metric("ACTIVE_FD", "Active FDs", int(row[1] or 0)),
                self._metric("DEPOSIT_AMOUNT", "Deposit amount", _decimal(row[2]), "AMOUNT"),
                self._metric("ACCRUED_INTEREST", "Accrued interest", _decimal(row[3]), "AMOUNT"),
            ],
            rows=[
                ModuleReportRow(
                    label="FD maturity and interest",
                    route="/admin/fixed-deposits/deposits",
                    values={
                        "tdsDeducted": _decimal(row[4]),
                        "maturingIn30Days": upcoming,
                    },
                    status="WARN" if upcoming else "OK",
                )
            ],
            exceptions=[
                self._metric(
                    "FD_MATURING_30D",
                    "Maturing in 30 days",
                    upcoming,
                    status="WARN" if upcoming else "OK",
                )
            ],
        )

    async def _inventory_module(
        self, org_id: UUID, from_date: date, to_date: date
    ) -> ModuleReportSection:
        item_count = await self.db.scalar(
            select(func.count(ItemMaster.id)).where(ItemMaster.organization_id == org_id)
        )
        stock_row = (
            await self.db.execute(
                select(
                    func.count(StockBalance.id),
                    func.coalesce(func.sum(StockBalance.total_value), 0),
                    func.coalesce(func.sum(StockBalance.quantity_on_hand), 0),
                ).where(StockBalance.organization_id == org_id)
            )
        ).one()
        low_stock = await self.db.scalar(
            select(func.count(StockBalance.id))
            .join(ItemMaster, ItemMaster.id == StockBalance.item_id)
            .where(
                StockBalance.organization_id == org_id,
                StockBalance.quantity_on_hand < ItemMaster.minimum_stock_level,
            )
        )
        txn_row = (
            await self.db.execute(
                select(
                    func.count(StockTransaction.id),
                    func.coalesce(func.sum(StockTransaction.total_cost), 0),
                    func.count(case((StockTransaction.status != "APPROVED", 1))),
                ).where(
                    StockTransaction.organization_id == org_id,
                    StockTransaction.transaction_date >= from_date,
                    StockTransaction.transaction_date <= to_date,
                )
            )
        ).one()
        return ModuleReportSection(
            module_code="INVENTORY",
            module_name="Inventory / Stock",
            category="OPERATIONS",
            route="/admin/inventory",
            metrics=[
                self._metric("ITEMS", "Items", int(item_count or 0)),
                self._metric("STOCK_VALUE", "Stock value", _decimal(stock_row[1]), "AMOUNT"),
                self._metric("STOCK_QTY", "Quantity on hand", _decimal(stock_row[2])),
                self._metric(
                    "LOW_STOCK",
                    "Low stock items",
                    int(low_stock or 0),
                    status="WARN" if low_stock else "OK",
                ),
            ],
            rows=[
                ModuleReportRow(
                    label="Stock movement",
                    route="/admin/inventory/stock-report",
                    values={
                        "transactions": int(txn_row[0] or 0),
                        "movementValue": _decimal(txn_row[1]),
                        "pendingApprovals": int(txn_row[2] or 0),
                    },
                    status="WARN" if txn_row[2] else "OK",
                ),
                ModuleReportRow(
                    label="Reorder report",
                    route="/admin/inventory/reorder",
                    values={"lowStockItems": int(low_stock or 0)},
                    status="WARN" if low_stock else "OK",
                ),
            ],
            exceptions=[
                self._metric(
                    "LOW_STOCK_ITEMS",
                    "Low stock items",
                    int(low_stock or 0),
                    status="WARN" if low_stock else "OK",
                )
            ],
        )

    async def _hris_module(
        self, org_id: UUID, from_date: date, to_date: date
    ) -> ModuleReportSection:
        employee_row = (
            await self.db.execute(
                select(
                    func.count(Employee.id),
                    func.count(case((Employee.employment_status == "ACTIVE", 1))),
                    func.count(case((Employee.date_of_joining.between(from_date, to_date), 1))),
                    func.count(case((Employee.date_of_leaving.between(from_date, to_date), 1))),
                ).where(Employee.organization_id == org_id)
            )
        ).one()
        attendance_row = (
            await self.db.execute(
                select(
                    func.count(Attendance.id),
                    func.count(case((Attendance.status == "ABSENT", 1))),
                    func.count(case((Attendance.is_locked.is_(True), 1))),
                )
                .join(Employee, Employee.id == Attendance.employee_id)
                .where(
                    Employee.organization_id == org_id,
                    Attendance.attendance_date >= from_date,
                    Attendance.attendance_date <= to_date,
                )
            )
        ).one()
        leave_row = (
            await self.db.execute(
                select(
                    func.count(LeaveApplication.id),
                    func.count(case((LeaveApplication.status == "PENDING", 1))),
                    func.coalesce(func.sum(LeaveApplication.total_days), 0),
                )
                .join(Employee, Employee.id == LeaveApplication.employee_id)
                .where(
                    Employee.organization_id == org_id,
                    LeaveApplication.from_date >= from_date,
                    LeaveApplication.from_date <= to_date,
                )
            )
        ).one()
        pending_leave = int(leave_row[1] or 0)
        return ModuleReportSection(
            module_code="HRIS",
            module_name="HRIS / Attendance / Leave",
            category="OPERATIONS",
            route="/admin/hris",
            metrics=[
                self._metric("HEADCOUNT", "Headcount", int(employee_row[0] or 0)),
                self._metric("ACTIVE_EMPLOYEES", "Active employees", int(employee_row[1] or 0)),
                self._metric("NEW_JOINERS", "New joiners", int(employee_row[2] or 0)),
                self._metric("EXITS", "Exits", int(employee_row[3] or 0)),
            ],
            rows=[
                ModuleReportRow(
                    label="Attendance summary",
                    route="/admin/hris/attendance",
                    values={
                        "records": int(attendance_row[0] or 0),
                        "absent": int(attendance_row[1] or 0),
                        "locked": int(attendance_row[2] or 0),
                    },
                    status="WARN" if attendance_row[1] else "OK",
                ),
                ModuleReportRow(
                    label="Leave summary",
                    route="/admin/hris/leave-applications",
                    values={
                        "applications": int(leave_row[0] or 0),
                        "pending": pending_leave,
                        "days": _decimal(leave_row[2]),
                    },
                    status="WARN" if pending_leave else "OK",
                ),
            ],
            exceptions=[
                self._metric(
                    "PENDING_LEAVE",
                    "Pending leave approvals",
                    pending_leave,
                    status="WARN" if pending_leave else "OK",
                )
            ],
        )

    async def _payroll_module(
        self, org_id: UUID, from_date: date, to_date: date
    ) -> ModuleReportSection:
        batch_row = (
            await self.db.execute(
                select(
                    func.count(PayrollBatch.id),
                    func.count(
                        case((PayrollBatch.status.in_(["PROCESSED", "APPROVED", "PAID"]), 1))
                    ),
                    func.coalesce(func.sum(PayrollBatch.total_gross), 0),
                    func.coalesce(func.sum(PayrollBatch.total_net), 0),
                    func.coalesce(func.sum(PayrollBatch.total_tds), 0),
                    func.coalesce(
                        func.sum(
                            PayrollBatch.total_pf_employee
                            + PayrollBatch.total_pf_employer
                            + PayrollBatch.total_esi_employee
                            + PayrollBatch.total_esi_employer
                            + PayrollBatch.total_pt
                        ),
                        0,
                    ),
                ).where(
                    PayrollBatch.organization_id == org_id,
                    PayrollBatch.pay_period_from <= to_date,
                    PayrollBatch.pay_period_to >= from_date,
                )
            )
        ).one()
        payslip_row = (
            await self.db.execute(
                select(
                    func.count(Payslip.id),
                    func.count(case((Payslip.status != "PAID", 1))),
                    func.coalesce(func.sum(Payslip.net_salary), 0),
                )
                .join(PayrollBatch, PayrollBatch.id == Payslip.batch_id)
                .where(PayrollBatch.organization_id == org_id)
            )
        ).one()
        unpaid = int(payslip_row[1] or 0)
        return ModuleReportSection(
            module_code="PAYROLL",
            module_name="Payroll / Statutory Payroll",
            category="OPERATIONS",
            route="/admin/payroll",
            metrics=[
                self._metric("BATCHES", "Payroll batches", int(batch_row[0] or 0)),
                self._metric("GROSS_PAYROLL", "Gross payroll", _decimal(batch_row[2]), "AMOUNT"),
                self._metric("NET_PAYROLL", "Net payroll", _decimal(batch_row[3]), "AMOUNT"),
                self._metric("STATUTORY", "Statutory deductions", _decimal(batch_row[5]), "AMOUNT"),
            ],
            rows=[
                ModuleReportRow(
                    label="Payroll batch status",
                    route="/admin/payroll/batches",
                    values={
                        "batches": int(batch_row[0] or 0),
                        "processedOrPaid": int(batch_row[1] or 0),
                        "tds": _decimal(batch_row[4]),
                    },
                ),
                ModuleReportRow(
                    label="Payslip payout",
                    route="/admin/payroll/payslips",
                    values={
                        "payslips": int(payslip_row[0] or 0),
                        "unpaid": unpaid,
                        "netSalary": _decimal(payslip_row[2]),
                    },
                    status="WARN" if unpaid else "OK",
                ),
            ],
            exceptions=[
                self._metric(
                    "UNPAID_PAYSLIPS",
                    "Unpaid payslips",
                    unpaid,
                    status="WARN" if unpaid else "OK",
                )
            ],
        )

    async def _portal_module(
        self, org_id: UUID, from_date: date, to_date: date
    ) -> ModuleReportSection:
        user_row = (
            await self.db.execute(
                select(
                    func.count(PortalUser.id),
                    func.count(case((PortalUser.status == "ACTIVE", 1))),
                    func.count(case((PortalUser.registration_status == "PENDING_APPROVAL", 1))),
                ).where(PortalUser.organization_id == org_id)
            )
        ).one()
        session_count = await self.db.scalar(
            select(func.count(PortalSession.id))
            .join(PortalUser, PortalUser.id == PortalSession.user_id)
            .where(
                PortalUser.organization_id == org_id,
                PortalSession.login_at >= datetime.combine(from_date, time.min),
                PortalSession.login_at <= datetime.combine(to_date, time.max),
            )
        )
        sr_row = (
            await self.db.execute(
                select(
                    func.count(PortalServiceRequest.id),
                    func.count(
                        case((PortalServiceRequest.status.notin_(["COMPLETED", "CANCELLED"]), 1))
                    ),
                    func.count(case((PortalServiceRequest.is_sla_breached.is_(True), 1))),
                ).where(
                    PortalServiceRequest.organization_id == org_id,
                    PortalServiceRequest.created_at
                    >= datetime.combine(from_date, time.min, tzinfo=UTC),
                    PortalServiceRequest.created_at
                    <= datetime.combine(to_date, time.max, tzinfo=UTC),
                )
            )
        ).one()
        doc_row = (
            await self.db.execute(
                select(
                    func.count(PortalDocument.id),
                    func.coalesce(func.sum(PortalDocument.file_size), 0),
                ).where(PortalDocument.organization_id == org_id)
            )
        ).one()
        doc_req_open = await self.db.scalar(
            select(func.count(PortalDocumentRequest.id)).where(
                PortalDocumentRequest.organization_id == org_id,
                PortalDocumentRequest.status.notin_(["COMPLETED", "CANCELLED"]),
            )
        )
        portal_exceptions = int(user_row[2] or 0) + int(sr_row[1] or 0) + int(sr_row[2] or 0)
        return ModuleReportSection(
            module_code="PORTALS",
            module_name="Borrower / ESS / Vendor Portal Activity",
            category="OPERATIONS",
            route="/admin/reports/history",
            metrics=[
                self._metric("PORTAL_USERS", "Borrower portal users", int(user_row[0] or 0)),
                self._metric("SESSIONS", "Portal sessions", int(session_count or 0)),
                self._metric("SERVICE_REQUESTS", "Service requests", int(sr_row[0] or 0)),
                self._metric("PORTAL_DOCUMENTS", "Portal documents", int(doc_row[0] or 0)),
            ],
            rows=[
                ModuleReportRow(
                    label="Borrower portal access",
                    route="/admin/portal-users",
                    values={
                        "activeUsers": int(user_row[1] or 0),
                        "pendingRegistrations": int(user_row[2] or 0),
                    },
                    status="WARN" if user_row[2] else "OK",
                ),
                ModuleReportRow(
                    label="Service requests",
                    route="/admin/portal/service-requests",
                    values={
                        "open": int(sr_row[1] or 0),
                        "slaBreached": int(sr_row[2] or 0),
                    },
                    status="WARN" if sr_row[1] or sr_row[2] else "OK",
                ),
                ModuleReportRow(
                    label="Document exchange",
                    route="/admin/dms/documents",
                    values={
                        "documents": int(doc_row[0] or 0),
                        "sizeBytes": int(doc_row[1] or 0),
                        "openDocumentRequests": int(doc_req_open or 0),
                    },
                    status="WARN" if doc_req_open else "OK",
                ),
            ],
            exceptions=[
                self._metric(
                    "PORTAL_EXCEPTIONS",
                    "Portal exceptions",
                    portal_exceptions,
                    status="WARN" if portal_exceptions else "OK",
                )
            ],
        )

    async def _vendor_module(
        self, org_id: UUID, from_date: date, to_date: date
    ) -> ModuleReportSection:
        vendor_count = await self.db.scalar(
            select(func.count(Vendor.id)).where(Vendor.organization_id == org_id)
        )
        customer_count = await self.db.scalar(
            select(func.count(Customer.id)).where(Customer.organization_id == org_id)
        )
        vendor_portal_row = (
            await self.db.execute(
                select(
                    func.count(PortalVendorUser.id),
                    func.count(case((PortalVendorUser.status == "ACTIVE", 1))),
                    func.count(case((PortalVendorUser.failed_login_attempts > 0, 1))),
                ).where(PortalVendorUser.organization_id == org_id)
            )
        ).one()
        vendor_session_count = await self.db.scalar(
            select(func.count(PortalVendorSession.id))
            .join(PortalVendorUser, PortalVendorUser.id == PortalVendorSession.user_id)
            .where(
                PortalVendorUser.organization_id == org_id,
                PortalVendorSession.login_at >= datetime.combine(from_date, time.min, tzinfo=UTC),
                PortalVendorSession.login_at <= datetime.combine(to_date, time.max, tzinfo=UTC),
            )
        )
        vendor_docs_pending = await self.db.scalar(
            select(func.count(VendorRegistration.id)).where(
                VendorRegistration.organization_id == org_id,
                VendorRegistration.status.notin_(["APPROVED", "REJECTED", "CANCELLED"]),
            )
        )
        invoice_row = (
            await self.db.execute(
                select(
                    func.count(VendorInvoice.id),
                    func.coalesce(func.sum(VendorInvoice.total_amount), 0),
                    func.count(
                        case((VendorInvoice.status.notin_(["APPROVED", "PAID", "REJECTED"]), 1))
                    ),
                ).where(
                    VendorInvoice.organization_id == org_id,
                    VendorInvoice.invoice_date >= from_date,
                    VendorInvoice.invoice_date <= to_date,
                )
            )
        ).one()
        asn_open = await self.db.scalar(
            select(func.count(AdvancedShippingNotice.id)).where(
                AdvancedShippingNotice.organization_id == org_id,
                AdvancedShippingNotice.status.notin_(["DELIVERED", "CANCELLED"]),
            )
        )
        pending = int(vendor_docs_pending or 0) + int(invoice_row[2] or 0) + int(asn_open or 0)
        return ModuleReportSection(
            module_code="VENDORS",
            module_name="Vendors / Procurement / Vendor Portal",
            category="OPERATIONS",
            route="/admin/vendor-portal",
            metrics=[
                self._metric("VENDORS", "Vendors", int(vendor_count or 0)),
                self._metric("CUSTOMERS", "Customers", int(customer_count or 0)),
                self._metric("VENDOR_USERS", "Vendor portal users", int(vendor_portal_row[0] or 0)),
                self._metric(
                    "VENDOR_INVOICES", "Vendor invoice value", _decimal(invoice_row[1]), "AMOUNT"
                ),
            ],
            rows=[
                ModuleReportRow(
                    label="Vendor portal users",
                    route="/admin/vendor-portal/users",
                    values={
                        "activeUsers": int(vendor_portal_row[1] or 0),
                        "sessions": int(vendor_session_count or 0),
                        "failedLoginUsers": int(vendor_portal_row[2] or 0),
                    },
                    status="WARN" if vendor_portal_row[2] else "OK",
                ),
                ModuleReportRow(
                    label="Vendor invoices",
                    route="/admin/vendor-portal/invoices",
                    values={
                        "count": int(invoice_row[0] or 0),
                        "value": _decimal(invoice_row[1]),
                        "pending": int(invoice_row[2] or 0),
                    },
                    status="WARN" if invoice_row[2] else "OK",
                ),
                ModuleReportRow(
                    label="Vendor registration / ASN",
                    route="/admin/vendor-portal/registration",
                    values={
                        "pendingRegistrations": int(vendor_docs_pending or 0),
                        "openAsn": int(asn_open or 0),
                    },
                    status="WARN" if vendor_docs_pending or asn_open else "OK",
                ),
            ],
            exceptions=[
                self._metric(
                    "VENDOR_PENDING_ITEMS",
                    "Vendor pending items",
                    pending,
                    status="WARN" if pending else "OK",
                )
            ],
        )

    async def _dms_module(self, org_id: UUID, as_of_date: date) -> ModuleReportSection:
        row = (
            await self.db.execute(
                select(
                    func.count(DMSDocument.id),
                    func.coalesce(func.sum(DMSDocument.file_size), 0),
                    func.count(case((DMSDocument.is_expired.is_(True), 1))),
                    func.count(
                        case(
                            (
                                DMSDocument.expiry_date
                                <= datetime.combine(as_of_date, time.max, tzinfo=UTC),
                                1,
                            )
                        )
                    ),
                    func.coalesce(func.sum(DMSDocument.download_count), 0),
                    func.coalesce(func.sum(DMSDocument.view_count), 0),
                ).where(DMSDocument.organization_id == org_id)
            )
        ).one()
        expired = int(row[2] or 0)
        return ModuleReportSection(
            module_code="DMS",
            module_name="Document Management",
            category="OPERATIONS",
            route="/admin/dms/documents",
            metrics=[
                self._metric("DOCUMENTS", "Documents", int(row[0] or 0)),
                self._metric("STORAGE_BYTES", "Storage bytes", int(row[1] or 0)),
                self._metric("DOWNLOADS", "Downloads", int(row[4] or 0)),
                self._metric("VIEWS", "Views", int(row[5] or 0)),
            ],
            rows=[
                ModuleReportRow(
                    label="Document register",
                    route="/admin/dms/documents",
                    values={
                        "documents": int(row[0] or 0),
                        "expired": expired,
                        "expiringAsOf": int(row[3] or 0),
                    },
                    status="WARN" if expired else "OK",
                )
            ],
            exceptions=[
                self._metric(
                    "EXPIRED_DOCUMENTS",
                    "Expired documents",
                    expired,
                    status="WARN" if expired else "OK",
                )
            ],
        )

    async def _workflow_module(self, org_id: UUID, as_of_date: date) -> ModuleReportSection:
        instance_row = (
            await self.db.execute(
                select(
                    func.count(WorkflowInstance.id),
                    func.count(case((WorkflowInstance.status == "PENDING", 1))),
                    func.count(case((WorkflowInstance.status == "COMPLETED", 1))),
                ).where(WorkflowInstance.organization_id == org_id)
            )
        ).one()
        task_row = (
            await self.db.execute(
                select(
                    func.count(WorkflowTask.id),
                    func.count(case((WorkflowTask.status == "PENDING", 1))),
                    func.count(case((WorkflowTask.is_overdue.is_(True), 1))),
                    func.count(
                        case(
                            (
                                WorkflowTask.due_at
                                < datetime.combine(as_of_date, time.max, tzinfo=UTC),
                                1,
                            )
                        )
                    ),
                )
                .join(WorkflowInstance, WorkflowInstance.id == WorkflowTask.workflow_instance_id)
                .where(WorkflowInstance.organization_id == org_id)
            )
        ).one()
        overdue = int(task_row[2] or 0) + int(task_row[3] or 0)
        return ModuleReportSection(
            module_code="WORKFLOW",
            module_name="Workflow / Approvals / Maker-Checker",
            category="SYSTEM",
            route="/admin/workflow/tasks",
            metrics=[
                self._metric("WORKFLOWS", "Workflow instances", int(instance_row[0] or 0)),
                self._metric("PENDING_WORKFLOWS", "Pending workflows", int(instance_row[1] or 0)),
                self._metric("TASKS", "Approval tasks", int(task_row[0] or 0)),
                self._metric("PENDING_TASKS", "Pending tasks", int(task_row[1] or 0)),
            ],
            rows=[
                ModuleReportRow(
                    label="Approval queue",
                    route="/admin/workflow/tasks",
                    values={
                        "pendingTasks": int(task_row[1] or 0),
                        "overdueTasks": overdue,
                        "completedWorkflows": int(instance_row[2] or 0),
                    },
                    status="WARN" if overdue else "OK",
                )
            ],
            exceptions=[
                self._metric(
                    "OVERDUE_APPROVALS",
                    "Overdue approvals",
                    overdue,
                    status="WARN" if overdue else "OK",
                )
            ],
        )

    async def _audit_system_module(
        self, org_id: UUID, from_date: date, to_date: date
    ) -> ModuleReportSection:
        audit_count = await self.db.scalar(
            select(func.count(AuditLog.id)).where(
                AuditLog.organization_id == org_id,
                AuditLog.changed_at >= datetime.combine(from_date, time.min, tzinfo=UTC),
                AuditLog.changed_at <= datetime.combine(to_date, time.max, tzinfo=UTC),
            )
        )
        job_row = (
            await self.db.execute(
                select(
                    func.count(BackgroundJob.id),
                    func.count(case((BackgroundJob.status == "FAILED", 1))),
                    func.count(case((BackgroundJob.status.in_(["PENDING", "RUNNING"]), 1))),
                ).where(BackgroundJob.organization_id == org_id)
            )
        ).one()
        run_count = await self.db.scalar(
            select(func.count(ReportRun.id)).where(
                ReportRun.organization_id == org_id,
                ReportRun.generated_at >= datetime.combine(from_date, time.min, tzinfo=UTC),
                ReportRun.generated_at <= datetime.combine(to_date, time.max, tzinfo=UTC),
            )
        )
        failed_jobs = int(job_row[1] or 0)
        return ModuleReportSection(
            module_code="AUDIT_SYSTEM",
            module_name="Audit / Jobs / Report Export History",
            category="SYSTEM",
            route="/admin/audit-logs",
            metrics=[
                self._metric("AUDIT_EVENTS", "Audit events", int(audit_count or 0)),
                self._metric("REPORT_RUNS", "Report runs", int(run_count or 0)),
                self._metric("JOBS", "Background jobs", int(job_row[0] or 0)),
                self._metric(
                    "FAILED_JOBS",
                    "Failed jobs",
                    failed_jobs,
                    status="WARN" if failed_jobs else "OK",
                ),
            ],
            rows=[
                ModuleReportRow(
                    label="System jobs",
                    route="/admin/jobs",
                    values={
                        "failed": failed_jobs,
                        "pendingOrRunning": int(job_row[2] or 0),
                    },
                    status="WARN" if failed_jobs else "OK",
                ),
                ModuleReportRow(
                    label="Report export history",
                    route="/admin/reports/history",
                    values={"reportRuns": int(run_count or 0)},
                ),
            ],
            exceptions=[
                self._metric(
                    "FAILED_JOBS",
                    "Failed jobs",
                    failed_jobs,
                    status="WARN" if failed_jobs else "OK",
                )
            ],
        )

    async def list_runs(self, org_id: UUID, limit: int = 50) -> list[ReportRunResponse]:
        rows = (
            (
                await self.db.execute(
                    select(ReportRun)
                    .where(ReportRun.organization_id == org_id, ReportRun.is_active.is_(True))
                    .order_by(desc(ReportRun.generated_at))
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )
        return [ReportRunResponse.model_validate(row) for row in rows]

    async def create_run(
        self,
        org_id: UUID,
        user_id: UUID,
        report_code: str,
        export_format: str,
        parameters: dict[str, Any],
    ) -> ReportRunResponse:
        catalog_item = self._find_catalog_item(report_code)
        started = perf_counter()
        status = "COMPLETED"
        error_message = None
        row_count = 0
        try:
            row_count = _safe_row_count(
                await self._generate_for_run(org_id, report_code, parameters)
            )
        except Exception as exc:  # report history must capture failures
            status = "FAILED"
            error_message = str(exc)
        run = ReportRun(
            organization_id=org_id,
            report_code=report_code,
            report_name=catalog_item.report_name,
            category=catalog_item.category,
            parameters=parameters,
            generated_by=user_id,
            generated_at=_now(),
            status=status,
            row_count=row_count,
            export_format=export_format.upper(),
            file_reference=None,
            error_message=error_message,
            duration_ms=int((perf_counter() - started) * 1000),
            created_by=user_id,
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return ReportRunResponse.model_validate(run)

    async def _generate_for_run(
        self, org_id: UUID, report_code: str, parameters: dict[str, Any]
    ) -> Any:
        today = date.today()
        as_of = date.fromisoformat(parameters.get("asOfDate", today.isoformat()))
        from_date = date.fromisoformat(parameters.get("fromDate", as_of.replace(day=1).isoformat()))
        to_date = date.fromisoformat(parameters.get("toDate", as_of.isoformat()))
        if report_code == "PORTFOLIO_SUMMARY":
            return await self.generate_portfolio_summary(org_id, as_of)
        if report_code == "DISBURSEMENT":
            return await self.generate_disbursement_report(
                org_id, from_date, to_date, parameters.get("groupBy", "PRODUCT")
            )
        if report_code == "COLLECTION":
            return await self.generate_collection_report(org_id, from_date, to_date)
        if report_code == "DELINQUENCY":
            return await self.generate_delinquency_report(org_id, as_of)
        if report_code == "PROFITABILITY":
            return await self.generate_profitability_report(org_id, from_date, to_date)
        if report_code == "BRANCH_PERFORMANCE":
            return await self.generate_branch_performance_report(org_id, from_date, to_date)
        if report_code in {
            "CEO_CFO_DASHBOARD",
            "BOARD_PACK",
            "DAILY_FLASH",
            "TRIAL_BALANCE",
            "PROFIT_LOSS",
            "BALANCE_SHEET",
            "VOUCHER_REGISTER",
            "GST_LIABILITY",
            "EWAY_EINVOICE_REGISTER",
            "TDS_SUMMARY",
            "COMPLIANCE_TRACKER",
            "FIXED_ASSET_REGISTER",
            "STOCK_VALUATION",
            "HR_PAYROLL_SUMMARY",
            "PORTAL_ACTIVITY",
            "AUDIT_ACCESS",
            "BORROWING_POSITION",
            "SOURCE_OF_FUNDS",
            "ALM_GAP",
            "NPA_MOVEMENT",
            "PROVISIONING",
            "APPLICATION_PIPELINE",
            "SANCTION_PIPELINE",
        }:
            return await self.generate_all_modules_report(org_id, from_date, to_date, as_of)
        return {"reportCode": report_code, "status": "CATALOG_ONLY"}

    async def list_schedules(
        self, org_id: UUID, active_only: bool = False, limit: int = 100
    ) -> list[ReportScheduleResponse]:
        filters = [ReportSchedule.organization_id == org_id]
        if active_only:
            filters.append(ReportSchedule.is_active.is_(True))
        rows = (
            (
                await self.db.execute(
                    select(ReportSchedule)
                    .where(*filters)
                    .order_by(desc(ReportSchedule.created_at))
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )
        return [ReportScheduleResponse.model_validate(row) for row in rows]

    async def create_schedule(
        self, org_id: UUID, user_id: UUID, payload: ReportScheduleCreate
    ) -> ReportScheduleResponse:
        catalog_item = self._find_catalog_item(payload.report_code)
        schedule = ReportSchedule(
            organization_id=org_id,
            report_code=payload.report_code,
            report_name=catalog_item.report_name,
            category=catalog_item.category,
            frequency=payload.frequency.upper(),
            schedule_time=payload.schedule_time,
            output_format=payload.output_format.upper(),
            parameters=payload.parameters,
            recipients=payload.recipients,
            is_active=payload.is_active,
            next_run_at=self._next_run_at(payload.frequency, payload.schedule_time),
            delivery_mode="MANUAL_DOWNLOAD",
            owner_user_id=user_id,
            description=payload.description,
            created_by=user_id,
        )
        self.db.add(schedule)
        await self.db.commit()
        await self.db.refresh(schedule)
        return ReportScheduleResponse.model_validate(schedule)

    async def run_schedule_now(
        self, org_id: UUID, user_id: UUID, schedule_id: UUID
    ) -> ReportRunResponse:
        schedule = await self.db.get(ReportSchedule, schedule_id)
        if not schedule or schedule.organization_id != org_id:
            raise ValueError("Report schedule not found")
        run = await self.create_run(
            org_id, user_id, schedule.report_code, schedule.output_format, schedule.parameters
        )
        schedule.last_run_at = run.generated_at
        schedule.last_status = run.status
        schedule.next_run_at = self._next_run_at(schedule.frequency, schedule.schedule_time)
        schedule.updated_by = user_id
        await self.db.commit()
        return run

    def _next_run_at(self, frequency: str, schedule_time: str) -> datetime:
        hour, minute = (int(part) for part in schedule_time.split(":", 1))
        candidate = datetime.combine(date.today(), time(hour=hour, minute=minute), tzinfo=UTC)
        if candidate <= _now():
            frequency_upper = frequency.upper()
            if frequency_upper == "WEEKLY":
                candidate += timedelta(days=7)
            elif frequency_upper == "MONTHLY":
                candidate += timedelta(days=31)
            else:
                candidate += timedelta(days=1)
        return candidate
