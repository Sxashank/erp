"""SQLAlchemy models."""

from app.models.ap_ar.bank_reconciliation import (
    BankReconciliation,
    BankReconciliationStatus,
    BankStatement,
    BankStatementMatch,
    ReconciliationStatus,
    StatementTransactionType,
)
from app.models.ap_ar.customer import Customer, CustomerType
from app.models.ap_ar.payment import (
    ChequeStatus,
    DocumentType,
    PartyType,
    Payment,
    PaymentAllocation,
    PaymentMode,
    PaymentType,
)
from app.models.ap_ar.payment import (
    PaymentStatus as PmtStatus,
)

# AP/AR models
from app.models.ap_ar.payment_terms import PaymentTerms
from app.models.ap_ar.purchase_bill import (
    BillStatus,
    PaymentStatus,
    PurchaseBill,
    PurchaseBillLine,
    SupplyType,
)
from app.models.ap_ar.sales_invoice import (
    EInvoiceStatus,
    InvoiceStatus,
    InvoiceSupplyType,
    ReceiptStatus,
    SalesInvoice,
    SalesInvoiceLine,
)
from app.models.ap_ar.vendor import (
    BalanceType,
    GSTRegistrationType,
    PaymentModePreference,
    Vendor,
    VendorType,
)
from app.models.auth.role import Permission, Role, RolePermission, UserRole
from app.models.auth.session import UserSession

# Auth models
from app.models.auth.user import User
from app.models.base import AuditMixin, BaseModel, SoftDeleteMixin

# BI/Analytics models
from app.models.bi import (
    APIMethod,
    BIModule,
    ChartDefinition,
    ChartRoleAccess,
    ChartType,
    Dashboard,
    DashboardRoleAccess,
    DashboardWidget,
    # Models
    DataSource,
    DataSourceType,
    # Enums
    WidgetType,
)

# Common models (audit trail)
from app.models.common.audit_log import AuditAction, AuditLog, EntityType
from app.models.common.line_item_history import LineItemAction, LineItemEntityType, LineItemHistory

# Core system models
from app.models.core.integration_config import (
    HealthStatus,
    IntegrationConfig,
    IntegrationLog,
    IntegrationProvider,
    IntegrationType,
)

# DMS models
from app.models.dms import (
    # Models
    DMSDocument,
    DMSDocumentAccess,
    DMSDocumentHistory,
    DMSDocumentTag,
    DMSDocumentVersion,
    DMSFolder,
    DMSFolderAccess,
    DMSTag,
    DocumentAccessLevel,
    # Enums
    DocumentStatus,
)
from app.models.finance.account import Account
from app.models.finance.account_group import AccountGroup

# Finance models
from app.models.finance.financial_year import FinancialPeriod, FinancialYear
from app.models.finance.voucher import Voucher, VoucherLine
from app.models.finance.voucher_type import VoucherType

# Fixed Assets models
from app.models.fixed_assets.asset_category import AssetCategory
from app.models.fixed_assets.asset_revaluation import AssetRevaluation
from app.models.fixed_assets.asset_transfer import AssetTransfer
from app.models.fixed_assets.depreciation import Depreciation, DepreciationRun
from app.models.fixed_assets.fixed_asset import FixedAsset

# GST models
from app.models.gst.gst_rate import GSTRate
from app.models.gst.gst_registration import GSTRegistration
from app.models.gst.hsn_sac import HSNSAC
from app.models.hris.attendance import (
    Attendance,
    AttendancePunch,
    AttendanceRegularization,
    MonthlyAttendanceSummary,
)

# HRIS models
from app.models.hris.employee import (
    Employee,
    EmployeeBankAccount,
    EmployeeDocument,
    EmployeeEducation,
    EmployeeExperience,
    EmployeeFamily,
    EmployeeLifecycleEvent,
    EmployeeStatutory,
)
from app.models.hris.leave import LeaveApplication, LeaveBalance, LeaveEncashment, LeaveType
from app.models.hris.shift import Holiday, HolidayCalendar, Shift

# Legal models
from app.models.legal import (
    Advocate,
    AdvocateAssignment,
    AdvocateFee,
    AdvocatePerformance,
    AdvocateRole,
    AdvocateSpecialization,
    AlertPriority,
    Court,
    CourtBench,
    CourtFeeSlab,
    CourtType,
    DeliveryMode,
    DeliveryStatus,
    DocumentChecklist,
    DocumentVersion,
    ExpenseCategoryType,
    ExpenseRecovery,
    ExpenseStatus,
    FeeStructureType,
    # Models
    LawFirm,
    LegalDocument,
    LegalDocumentType,
    LegalExpense,
    LegalNotice,
    LimitationAlert,
    NoticeDelivery,
    NoticeResponse,
    NoticeStatus,
    NoticeTemplate,
    # Enums
    NoticeType,
    PeriodTracking,
    RecoveryType,
    SpecializationType,
    StatutoryPeriod,
)
from app.models.legal import (
    DocumentCategory as LegalDocumentCategory,
)
from app.models.legal import (
    ExpenseCategory as LegalExpenseCategory,
)

# Lending models referenced by cross-module Legal relationships. Importing
# these before the Legal package keeps SQLAlchemy's class registry complete
# even when a non-lending route, such as DMS document detail, is the first
# endpoint to configure mappers in a fresh worker.
from app.models.lending.collections import LegalCase
from app.models.masters.department import Department
from app.models.masters.designation import Designation

# Master models
from app.models.masters.organization import Organization
from app.models.masters.unit import Unit

# Notification models
from app.models.notification import (
    Notification,
    NotificationCategory,
    NotificationChannel,
    NotificationLog,
    NotificationPreference,
    NotificationPriority,
    NotificationStatus,
    NotificationTemplateType,
    NotificationTemplateVariable,
    SysNotificationTemplate,
)
from app.models.reports import ReportRun, ReportSchedule
from app.models.payroll.payroll import (
    PayrollBatch,
    PayrollStatutory,
    Payslip,
    PayslipComponent,
    StatutorySetup,
)

# Payroll models
from app.models.payroll.salary_component import (
    EmployeeSalary,
    EmployeeSalaryComponent,
    SalaryComponent,
    SalaryStructure,
    SalaryStructureComponent,
)

# Portal models
from app.models.portal import (
    ConsentType,
    DeviceType,
    DocumentRequestStatus,
    KYCStatus,
    KYCType,
    MandateFrequency,
    MandateStatus,
    NotificationChannel,
    NotificationPriority,
    OTPPurpose,
    PortalActorRole,
    PortalAnnouncement,
    PortalAutoDebitMandate,
    PortalConsent,
    PortalDevice,
    PortalDocument,
    PortalDocumentRequest,
    PortalDocumentType,
    PortalKYCVerification,
    PortalMessage,
    PortalNotification,
    PortalOTP,
    PortalPaymentRequest,
    PortalPaymentTransaction,
    PortalRegistrationStatus,
    PortalSavedPaymentMethod,
    PortalServiceRequest,
    PortalServiceRequestDocument,
    PortalServiceRequestHistory,
    PortalSession,
    PortalTicket,
    # Models
    PortalUser,
    PortalUserEntity,
    # Enums
    PortalUserStatus,
    ServiceRequestStatus,
    ServiceRequestType,
    TicketCategory,
    TicketPriority,
    TicketStatus,
)
from app.models.portal import (
    PaymentMode as PortalPaymentMode,
)
from app.models.portal import (
    PaymentStatus as PortalPaymentStatus,
)
from app.models.tds.tds_entry import TDSEntry

# TDS models
from app.models.tds.tds_section import TDSSection

# Workflow models
from app.models.workflow import (
    ApprovalMode,
    ApprovalRule,
    ApproverType,
    EscalationRule,
    EscalationType,
    NotificationTemplate,
    StepAction,
    TaskStatus,
    WorkflowAction,
    WorkflowDefinition,
    WorkflowEntityType,
    WorkflowHistory,
    WorkflowInstance,
    WorkflowInstanceStatus,
    WorkflowStep,
    WorkflowStepType,
    WorkflowTask,
)

__all__ = [
    # Base
    "BaseModel",
    "AuditMixin",
    "SoftDeleteMixin",
    # Core
    "IntegrationConfig",
    "IntegrationLog",
    "IntegrationType",
    "IntegrationProvider",
    "HealthStatus",
    # Common (Audit Trail)
    "AuditLog",
    "AuditAction",
    "EntityType",
    "LineItemHistory",
    "LineItemAction",
    "LineItemEntityType",
    # Auth
    "User",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "UserSession",
    # Masters
    "Organization",
    "Unit",
    "Department",
    "Designation",
    # Finance
    "FinancialYear",
    "FinancialPeriod",
    "AccountGroup",
    "Account",
    "VoucherType",
    "Voucher",
    "VoucherLine",
    # GST
    "GSTRate",
    "HSNSAC",
    "GSTRegistration",
    # TDS
    "TDSSection",
    "TDSEntry",
    # AP/AR
    "PaymentTerms",
    "Vendor",
    "VendorType",
    "GSTRegistrationType",
    "PaymentModePreference",
    "BalanceType",
    "Customer",
    "CustomerType",
    "PurchaseBill",
    "PurchaseBillLine",
    "BillStatus",
    "PaymentStatus",
    "SupplyType",
    "SalesInvoice",
    "SalesInvoiceLine",
    "InvoiceStatus",
    "ReceiptStatus",
    "InvoiceSupplyType",
    "EInvoiceStatus",
    "Payment",
    "PaymentAllocation",
    "PaymentType",
    "PartyType",
    "PaymentMode",
    "PmtStatus",
    "ChequeStatus",
    "DocumentType",
    # Bank Reconciliation
    "BankStatement",
    "BankStatementMatch",
    "BankReconciliation",
    "StatementTransactionType",
    "ReconciliationStatus",
    "BankReconciliationStatus",
    # Fixed Assets
    "AssetCategory",
    "FixedAsset",
    "Depreciation",
    "DepreciationRun",
    "AssetTransfer",
    "AssetRevaluation",
    # HRIS
    "Employee",
    "EmployeeDocument",
    "EmployeeFamily",
    "EmployeeBankAccount",
    "EmployeeEducation",
    "EmployeeExperience",
    "EmployeeStatutory",
    "EmployeeLifecycleEvent",
    "Shift",
    "HolidayCalendar",
    "Holiday",
    "LeaveType",
    "LeaveBalance",
    "LeaveApplication",
    "LeaveEncashment",
    "AttendancePunch",
    "Attendance",
    "AttendanceRegularization",
    "MonthlyAttendanceSummary",
    # Payroll
    "SalaryComponent",
    "SalaryStructure",
    "SalaryStructureComponent",
    "EmployeeSalary",
    "EmployeeSalaryComponent",
    "StatutorySetup",
    "PayrollBatch",
    "Payslip",
    "PayslipComponent",
    "PayrollStatutory",
    # Workflow
    "WorkflowEntityType",
    "WorkflowStepType",
    "ApprovalMode",
    "ApproverType",
    "EscalationType",
    "WorkflowInstanceStatus",
    "TaskStatus",
    "StepAction",
    "WorkflowAction",
    "WorkflowDefinition",
    "WorkflowStep",
    "ApprovalRule",
    "EscalationRule",
    "NotificationTemplate",
    "WorkflowInstance",
    "WorkflowTask",
    "WorkflowHistory",
    # Cross-module lending models
    "LegalCase",
    # Legal Enums
    "NoticeType",
    "NoticeStatus",
    "DeliveryMode",
    "DeliveryStatus",
    "LegalDocumentCategory",
    "ExpenseCategoryType",
    "ExpenseStatus",
    "RecoveryType",
    "FeeStructureType",
    "AdvocateRole",
    "SpecializationType",
    "CourtType",
    "AlertPriority",
    # Legal Models
    "LawFirm",
    "Advocate",
    "AdvocateSpecialization",
    "AdvocateAssignment",
    "AdvocatePerformance",
    "NoticeTemplate",
    "LegalNotice",
    "NoticeDelivery",
    "NoticeResponse",
    "LegalDocumentType",
    "LegalDocument",
    "DocumentVersion",
    "DocumentChecklist",
    "LegalExpenseCategory",
    "LegalExpense",
    "ExpenseRecovery",
    "AdvocateFee",
    "StatutoryPeriod",
    "PeriodTracking",
    "LimitationAlert",
    "Court",
    "CourtBench",
    "CourtFeeSlab",
    # Portal Enums
    "PortalUserStatus",
    "PortalRegistrationStatus",
    "PortalActorRole",
    "DeviceType",
    "OTPPurpose",
    "ConsentType",
    "NotificationChannel",
    "NotificationPriority",
    "TicketStatus",
    "TicketPriority",
    "TicketCategory",
    "PortalPaymentMode",
    "PortalPaymentStatus",
    "MandateStatus",
    "MandateFrequency",
    "PortalDocumentType",
    "DocumentRequestStatus",
    "KYCType",
    "KYCStatus",
    "ServiceRequestType",
    "ServiceRequestStatus",
    # Portal Models
    "PortalUser",
    "PortalSession",
    "PortalDevice",
    "PortalOTP",
    "PortalConsent",
    "PortalUserEntity",
    "PortalNotification",
    "PortalMessage",
    "PortalTicket",
    "PortalAnnouncement",
    "PortalPaymentRequest",
    "PortalPaymentTransaction",
    "PortalSavedPaymentMethod",
    "PortalAutoDebitMandate",
    "PortalDocument",
    "PortalDocumentRequest",
    "PortalKYCVerification",
    "PortalServiceRequest",
    "PortalServiceRequestDocument",
    "PortalServiceRequestHistory",
    # Notification System Enums
    "NotificationChannel",
    "NotificationPriority",
    "NotificationStatus",
    "NotificationCategory",
    "NotificationTemplateType",
    # Notification System Models
    "Notification",
    "NotificationPreference",
    "NotificationLog",
    "SysNotificationTemplate",
    "NotificationTemplateVariable",
    # DMS Enums
    "DocumentStatus",
    "DocumentAccessLevel",
    # DMS Models
    "DMSDocument",
    "DMSDocumentVersion",
    "DMSDocumentAccess",
    "DMSDocumentHistory",
    "DMSFolder",
    "DMSFolderAccess",
    "DMSTag",
    "DMSDocumentTag",
    # BI/Analytics Enums
    "WidgetType",
    "ChartType",
    "BIModule",
    "DataSourceType",
    "APIMethod",
    # BI/Analytics Models
    "DataSource",
    "ChartDefinition",
    "ChartRoleAccess",
    "Dashboard",
    "DashboardWidget",
    "DashboardRoleAccess",
]
