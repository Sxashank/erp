"""MIS report schemas using camelCase API aliases."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelSchema


class ReportPeriod(CamelSchema):
    from_date: date
    to_date: date


class MISMetric(CamelSchema):
    code: str
    label: str
    value: Decimal | int | float | str
    value_type: str = "NUMBER"
    unit: str | None = None
    status: str = "OK"
    description: str | None = None


class ReportFilterDefinition(CamelSchema):
    code: str
    label: str
    type: str
    required: bool = False


class ReportCatalogItem(CamelSchema):
    report_code: str
    report_name: str
    category: str
    module: str
    description: str
    route: str
    supported_filters: list[ReportFilterDefinition] = Field(default_factory=list)
    export_formats: list[str] = Field(default_factory=lambda: ["PDF", "XLSX", "CSV"])
    schedule_eligible: bool = True
    permission: str = "FIN_REPORT_VIEW"
    manual_first_note: str | None = None


class ReportCatalogGroup(CamelSchema):
    category: str
    title: str
    description: str
    reports: list[ReportCatalogItem]


class ReportCatalogResponse(CamelSchema):
    generated_at: datetime
    groups: list[ReportCatalogGroup]


class DashboardSummary(CamelSchema):
    as_of_date: date
    generated_at: datetime
    executive_metrics: list[MISMetric]
    module_metrics: list[MISMetric]
    exception_metrics: list[MISMetric]
    recent_runs: list["ReportRunResponse"] = Field(default_factory=list)
    active_schedules: list["ReportScheduleResponse"] = Field(default_factory=list)


class PortfolioSummary(CamelSchema):
    total_accounts: int = 0
    active_accounts: int = 0
    closed_accounts: int = 0
    written_off_accounts: int = 0
    total_sanctioned: Decimal = Decimal("0")
    total_disbursed: Decimal = Decimal("0")
    principal_outstanding: Decimal = Decimal("0")
    interest_outstanding: Decimal = Decimal("0")
    total_outstanding: Decimal = Decimal("0")
    principal_overdue: Decimal = Decimal("0")
    interest_overdue: Decimal = Decimal("0")
    total_overdue: Decimal = Decimal("0")
    average_ticket_size: Decimal = Decimal("0")
    weighted_average_yield: Decimal = Decimal("0")


class PortfolioBreakdownItem(CamelSchema):
    name: str
    count: int
    amount: Decimal
    share_percent: Decimal
    average_yield: Decimal | None = None


class PortfolioSummaryResponse(CamelSchema):
    report_type: str = "PORTFOLIO_SUMMARY"
    as_of_date: date
    generated_at: datetime
    summary: PortfolioSummary
    product_breakdown: list[PortfolioBreakdownItem] = Field(default_factory=list)
    asset_quality_breakdown: list[PortfolioBreakdownItem] = Field(default_factory=list)
    top_exposures: list[dict[str, Any]] = Field(default_factory=list)


class PeriodSummary(CamelSchema):
    total_count: int = 0
    total_amount: Decimal = Decimal("0")
    average_ticket_size: Decimal = Decimal("0")


class DisbursementBreakdownItem(CamelSchema):
    name: str
    count: int
    amount: Decimal
    average_ticket_size: Decimal
    share_percent: Decimal


class DailyTrendItem(CamelSchema):
    date: date
    count: int
    amount: Decimal


class DisbursementReportResponse(CamelSchema):
    report_type: str = "DISBURSEMENT"
    period: ReportPeriod
    generated_at: datetime
    summary: PeriodSummary
    breakdown: list[DisbursementBreakdownItem] = Field(default_factory=list)
    daily_trend: list[DailyTrendItem] = Field(default_factory=list)


class CollectionSummary(CamelSchema):
    total_demand: Decimal = Decimal("0")
    total_collected: Decimal = Decimal("0")
    collection_efficiency: Decimal = Decimal("0")
    principal_collected: Decimal = Decimal("0")
    interest_collected: Decimal = Decimal("0")
    penal_collected: Decimal = Decimal("0")
    charges_collected: Decimal = Decimal("0")
    shortfall: Decimal = Decimal("0")


class CollectionModeItem(CamelSchema):
    mode: str
    amount: Decimal
    share_percent: Decimal


class CollectionBucketItem(CamelSchema):
    bucket: str
    demand: Decimal
    collected: Decimal
    shortfall: Decimal
    efficiency: Decimal


class CollectionReportResponse(CamelSchema):
    report_type: str = "COLLECTION"
    period: ReportPeriod
    generated_at: datetime
    summary: CollectionSummary
    mode_wise: list[CollectionModeItem] = Field(default_factory=list)
    bucket_wise: list[CollectionBucketItem] = Field(default_factory=list)


class DelinquencySummary(CamelSchema):
    total_outstanding: Decimal = Decimal("0")
    total_delinquent: Decimal = Decimal("0")
    delinquency_rate: Decimal = Decimal("0")
    overdue_accounts: int = 0


class DelinquencyBucketItem(CamelSchema):
    bucket: str
    accounts: int
    amount: Decimal
    share_percent: Decimal
    classification: str


class TopDelinquentAccount(CamelSchema):
    loan_account_number: str
    borrower_name: str
    product_name: str
    outstanding_amount: Decimal
    days_past_due: int
    classification: str


class DelinquencyReportResponse(CamelSchema):
    report_type: str = "DELINQUENCY"
    as_of_date: date
    generated_at: datetime
    summary: DelinquencySummary
    buckets: list[DelinquencyBucketItem] = Field(default_factory=list)
    top_delinquent_accounts: list[TopDelinquentAccount] = Field(default_factory=list)


class ProfitabilitySummary(CamelSchema):
    interest_income: Decimal = Decimal("0")
    fee_income: Decimal = Decimal("0")
    total_income: Decimal = Decimal("0")
    interest_expense: Decimal = Decimal("0")
    provision_expense: Decimal = Decimal("0")
    operating_expense: Decimal = Decimal("0")
    total_expense: Decimal = Decimal("0")
    profit_before_tax: Decimal = Decimal("0")
    net_interest_margin: Decimal = Decimal("0")
    net_margin: Decimal = Decimal("0")
    loan_yield: Decimal = Decimal("0")
    cost_of_funds: Decimal = Decimal("0")
    spread: Decimal = Decimal("0")


class ProfitabilityBreakdownItem(CamelSchema):
    name: str
    income: Decimal
    expense: Decimal
    profit: Decimal
    margin: Decimal


class ProfitabilityReportResponse(CamelSchema):
    report_type: str = "PROFITABILITY"
    period: ReportPeriod
    generated_at: datetime
    summary: ProfitabilitySummary
    product_wise: list[ProfitabilityBreakdownItem] = Field(default_factory=list)


class BranchPerformanceItem(CamelSchema):
    branch_id: UUID | None = None
    branch_name: str
    aum: Decimal
    disbursement: Decimal
    collection: Decimal
    collection_efficiency: Decimal
    npa_percentage: Decimal
    applications: int
    sanctioned_amount: Decimal


class BranchPerformanceResponse(CamelSchema):
    report_type: str = "BRANCH_PERFORMANCE"
    period: ReportPeriod
    generated_at: datetime
    branches: list[BranchPerformanceItem] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


class ModuleReportRow(CamelSchema):
    label: str
    values: dict[str, Any] = Field(default_factory=dict)
    status: str = "OK"
    route: str | None = None


class ModuleReportSection(CamelSchema):
    module_code: str
    module_name: str
    category: str
    route: str
    metrics: list[MISMetric] = Field(default_factory=list)
    rows: list[ModuleReportRow] = Field(default_factory=list)
    exceptions: list[MISMetric] = Field(default_factory=list)


class AllModulesReportResponse(CamelSchema):
    report_type: str = "ALL_MODULES_MIS"
    period: ReportPeriod
    as_of_date: date
    generated_at: datetime
    modules: list[ModuleReportSection] = Field(default_factory=list)


class ReportRunCreate(CamelSchema):
    report_code: str
    export_format: str = "XLSX"
    parameters: dict[str, Any] = Field(default_factory=dict)


class ReportRunResponse(CamelSchema):
    id: UUID
    report_code: str
    report_name: str
    category: str
    parameters: dict[str, Any]
    generated_by: UUID | None = None
    generated_at: datetime
    status: str
    row_count: int
    export_format: str
    file_reference: str | None = None
    error_message: str | None = None
    duration_ms: int | None = None


class ReportScheduleCreate(CamelSchema):
    report_code: str
    frequency: str
    schedule_time: str
    output_format: str = "XLSX"
    parameters: dict[str, Any] = Field(default_factory=dict)
    recipients: list[str] = Field(default_factory=list)
    is_active: bool = True
    description: str | None = None


class ReportScheduleResponse(CamelSchema):
    id: UUID
    report_code: str
    report_name: str
    category: str
    frequency: str
    schedule_time: str
    output_format: str
    parameters: dict[str, Any]
    recipients: list[str]
    is_active: bool
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    last_status: str | None = None
    delivery_mode: str
    owner_user_id: UUID | None = None
    description: str | None = None


DashboardSummary.model_rebuild()
