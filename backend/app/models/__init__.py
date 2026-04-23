"""SQLAlchemy models."""

from app.models.base import BaseModel, AuditMixin, SoftDeleteMixin

# Core system models
from app.models.core.integration_config import (
    IntegrationConfig,
    IntegrationLog,
    IntegrationType,
    IntegrationProvider,
    HealthStatus,
)

# Common models (audit trail)
from app.models.common.audit_log import AuditLog, AuditAction, EntityType
from app.models.common.line_item_history import LineItemHistory, LineItemAction, LineItemEntityType

# Notification models
from app.models.notification import (
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    NotificationCategory,
    NotificationTemplateType,
    Notification,
    NotificationPreference,
    NotificationLog,
    SysNotificationTemplate,
    NotificationTemplateVariable,
)

# Auth models
from app.models.auth.user import User
from app.models.auth.role import Role, Permission, UserRole, RolePermission
from app.models.auth.session import UserSession

# Master models
from app.models.masters.organization import Organization
from app.models.masters.unit import Unit
from app.models.masters.department import Department
from app.models.masters.designation import Designation

# Finance models
from app.models.finance.financial_year import FinancialYear, FinancialPeriod
from app.models.finance.account_group import AccountGroup
from app.models.finance.account import Account
from app.models.finance.voucher_type import VoucherType
from app.models.finance.voucher import Voucher, VoucherLine

# GST models
from app.models.gst.gst_rate import GSTRate
from app.models.gst.hsn_sac import HSNSAC
from app.models.gst.gst_registration import GSTRegistration

# TDS models
from app.models.tds.tds_section import TDSSection
from app.models.tds.tds_entry import TDSEntry

# AP/AR models
from app.models.ap_ar.payment_terms import PaymentTerms
from app.models.ap_ar.vendor import Vendor, VendorType, GSTRegistrationType, PaymentModePreference, BalanceType
from app.models.ap_ar.customer import Customer, CustomerType
from app.models.ap_ar.purchase_bill import PurchaseBill, PurchaseBillLine, BillStatus, PaymentStatus, SupplyType
from app.models.ap_ar.sales_invoice import (
    SalesInvoice,
    SalesInvoiceLine,
    InvoiceStatus,
    ReceiptStatus,
    InvoiceSupplyType,
    EInvoiceStatus,
)
from app.models.ap_ar.payment import (
    Payment,
    PaymentAllocation,
    PaymentType,
    PartyType,
    PaymentMode,
    PaymentStatus as PmtStatus,
    ChequeStatus,
    DocumentType,
)
from app.models.ap_ar.bank_reconciliation import (
    BankStatement,
    BankStatementMatch,
    BankReconciliation,
    StatementTransactionType,
    ReconciliationStatus,
    BankReconciliationStatus,
)

# Fixed Assets models
from app.models.fixed_assets.asset_category import AssetCategory
from app.models.fixed_assets.fixed_asset import FixedAsset
from app.models.fixed_assets.depreciation import Depreciation, DepreciationRun
from app.models.fixed_assets.asset_transfer import AssetTransfer
from app.models.fixed_assets.asset_revaluation import AssetRevaluation

# HRIS models
from app.models.hris.employee import (
    Employee,
    EmployeeDocument,
    EmployeeFamily,
    EmployeeBankAccount,
    EmployeeEducation,
    EmployeeExperience,
    EmployeeStatutory,
    EmployeeLifecycleEvent,
)
from app.models.hris.shift import Shift, HolidayCalendar, Holiday
from app.models.hris.leave import LeaveType, LeaveBalance, LeaveApplication, LeaveEncashment
from app.models.hris.attendance import (
    AttendancePunch,
    Attendance,
    AttendanceRegularization,
    MonthlyAttendanceSummary,
)

# Payroll models
from app.models.payroll.salary_component import (
    SalaryComponent,
    SalaryStructure,
    SalaryStructureComponent,
    EmployeeSalary,
    EmployeeSalaryComponent,
)
from app.models.payroll.payroll import (
    StatutorySetup,
    PayrollBatch,
    Payslip,
    PayslipComponent,
    PayrollStatutory,
)

# Workflow models
from app.models.workflow import (
    WorkflowEntityType,
    WorkflowStepType,
    ApprovalMode,
    ApproverType,
    EscalationType,
    WorkflowInstanceStatus,
    TaskStatus,
    StepAction,
    WorkflowAction,
    WorkflowDefinition,
    WorkflowStep,
    ApprovalRule,
    EscalationRule,
    NotificationTemplate,
    WorkflowInstance,
    WorkflowTask,
    WorkflowHistory,
)

# Legal models
from app.models.legal import (
    # Enums
    NoticeType,
    NoticeStatus,
    DeliveryMode,
    DeliveryStatus,
    DocumentCategory as LegalDocumentCategory,
    ExpenseCategoryType,
    ExpenseStatus,
    RecoveryType,
    FeeStructureType,
    AdvocateRole,
    SpecializationType,
    CourtType,
    AlertPriority,
    # Models
    LawFirm,
    Advocate,
    AdvocateSpecialization,
    AdvocateAssignment,
    AdvocatePerformance,
    NoticeTemplate,
    LegalNotice,
    NoticeDelivery,
    NoticeResponse,
    LegalDocumentType,
    LegalDocument,
    DocumentVersion,
    DocumentChecklist,
    ExpenseCategory as LegalExpenseCategory,
    LegalExpense,
    ExpenseRecovery,
    AdvocateFee,
    StatutoryPeriod,
    PeriodTracking,
    LimitationAlert,
    Court,
    CourtBench,
    CourtFeeSlab,
)

# DMS models
from app.models.dms import (
    # Enums
    DocumentStatus,
    DocumentAccessLevel,
    # Models
    DMSDocument,
    DMSDocumentVersion,
    DMSDocumentAccess,
    DMSDocumentHistory,
    DMSFolder,
    DMSFolderAccess,
    DMSTag,
    DMSDocumentTag,
)

# BI/Analytics models
from app.models.bi import (
    # Enums
    WidgetType,
    ChartType,
    BIModule,
    DataSourceType,
    APIMethod,
    # Models
    DataSource,
    ChartDefinition,
    ChartRoleAccess,
    Dashboard,
    DashboardWidget,
    DashboardRoleAccess,
)

# Portal models
from app.models.portal import (
    # Enums
    PortalUserStatus,
    DeviceType,
    OTPPurpose,
    ConsentType,
    NotificationChannel,
    NotificationPriority,
    TicketStatus,
    TicketPriority,
    TicketCategory,
    PaymentMode as PortalPaymentMode,
    PaymentStatus as PortalPaymentStatus,
    MandateStatus,
    MandateFrequency,
    PortalDocumentType,
    DocumentRequestStatus,
    KYCType,
    KYCStatus,
    ServiceRequestType,
    ServiceRequestStatus,
    # Models
    PortalUser,
    PortalSession,
    PortalDevice,
    PortalOTP,
    PortalConsent,
    PortalNotification,
    PortalMessage,
    PortalTicket,
    PortalAnnouncement,
    PortalPaymentRequest,
    PortalPaymentTransaction,
    PortalSavedPaymentMethod,
    PortalAutoDebitMandate,
    PortalDocument,
    PortalDocumentRequest,
    PortalKYCVerification,
    PortalServiceRequest,
    PortalServiceRequestDocument,
    PortalServiceRequestHistory,
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
