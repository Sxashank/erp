#!/usr/bin/env python3
"""Seed initial master data for a fresh SMFC ERP tenant."""

import asyncio
import os
import re
import sys
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

import app.models.lending  # noqa: F401 - register lending ORM tables
from app.config import settings
from app.core.constants import (
    ALL_PERMISSIONS,
    AccountNature,
    AccountType,
    AssetType,
    BalanceType,
    DepreciationMethod,
    GSTRegistrationType,
    HolidayType,
    HSNSACType,
    LeaveCategory,
    Permissions,
    ShiftType,
    UserStatus,
    VoucherClass,
    VoucherStatus,
)
from app.core.security import get_password_hash
from app.database import async_session_factory
from app.models.ap_ar.payment_terms import PaymentTerms
from app.models.auth.role import Permission, Role, RolePermission, UserRole
from app.models.auth.user import User
from app.models.bi.chart import ChartDefinition
from app.models.bi.datasource import DataSource
from app.models.bi.enums import APIMethod, BIModule, ChartType, DataSourceType
from app.models.compliance.compliance import (
    ComplianceFrequency,
    ComplianceItem,
    CompliancePriority,
    RegulatoryBody,
)
from app.models.dms.document import DocumentAccessLevel
from app.models.dms.folder import DMSFolder
from app.models.dms.tag import DMSTag
from app.models.ess.enums import ClaimType, TicketCategory
from app.models.ess.helpdesk import TicketCategoryMaster
from app.models.ess.it_declaration import ITDeclarationMaster
from app.models.ess.reimbursement import ReimbursementCategory
from app.models.finance.account import Account
from app.models.finance.account_group import AccountGroup
from app.models.finance.financial_year import FinancialPeriod, FinancialYear
from app.models.finance.voucher import Voucher, VoucherLine
from app.models.finance.voucher_type import VoucherType
from app.models.fixed_assets.asset_category import AssetCategory
from app.models.fixed_assets.fa_config import FAConfiguration
from app.models.fixed_deposits.fd_product import (
    FDCompoundingFrequency,
    FDCustomerCategory,
    FDInterestPayoutFrequency,
    FDInterestSlab,
    FDProduct,
)
from app.models.gst.gst_rate import GSTRate
from app.models.gst.gst_registration import GSTRegistration
from app.models.gst.hsn_sac import HSNSAC
from app.models.hris.leave import LeaveType
from app.models.hris.shift import Holiday, HolidayCalendar, Shift
from app.models.inventory.item_category import ItemCategory
from app.models.inventory.item_master import ItemMaster, ItemType, UnitOfMeasure
from app.models.inventory.warehouse import Warehouse, WarehouseType
from app.models.legal.court import Court, CourtFeeSlab
from app.models.legal.enums import CourtType, ExpenseCategoryType
from app.models.legal.expense import ExpenseCategory
from app.models.legal.statutory_period import StatutoryPeriod
from app.models.lending import (
    ApprovalChecklistTemplate,
    ApprovalChecklistTemplateItem,
    ChecklistAppliesTo,
    ChecklistItemCategory,
    DayCountConvention,
    DocumentCategory,
    DocumentChecklist,
    DocumentStage,
    FeeCalculationType,
    FeeCollectionStage,
    FeeMaster,
    FeeType,
    FundUtilizationCategory,
    IIFLoanType,
    InterestRate,
    InterestType,
    LoanProduct,
    ProductCategory,
    ProductFee,
    RateResetFrequency,
    RepaymentFrequency,
    RepaymentMode,
    SubventionScheme,
)
from app.models.lending.enums import ClaimFrequency, LenderStatus, LenderType
from app.models.lending.treasury import Lender
from app.models.masters.department import Department
from app.models.masters.designation import Designation
from app.models.masters.organization import Organization
from app.models.masters.organization_bank_account import OrganizationBankAccount
from app.models.masters.unit import Unit
from app.models.notification.notification import NotificationCategory
from app.models.notification.template import NotificationTemplate, NotificationTemplateType
from app.models.payroll.payroll import StatutorySetup
from app.models.payroll.salary_component import (
    CalculationType,
    ComponentCategory,
    ComponentType,
    SalaryComponent,
    SalaryStructure,
    SalaryStructureComponent,
)
from app.models.tds.tds_section import TDSSection

# Permission definitions
PERMISSIONS = [
    # Masters - Organization
    {
        "code": "MASTER_ORG_VIEW",
        "name": "View Organizations",
        "module": "MASTERS",
        "resource": "organization",
        "action": "READ",
    },
    {
        "code": "MASTER_ORG_CREATE",
        "name": "Create Organization",
        "module": "MASTERS",
        "resource": "organization",
        "action": "CREATE",
    },
    {
        "code": "MASTER_ORG_UPDATE",
        "name": "Update Organization",
        "module": "MASTERS",
        "resource": "organization",
        "action": "UPDATE",
    },
    {
        "code": "MASTER_ORG_DELETE",
        "name": "Delete Organization",
        "module": "MASTERS",
        "resource": "organization",
        "action": "DELETE",
    },
    # Masters - Unit
    {
        "code": "MASTER_UNIT_VIEW",
        "name": "View Units",
        "module": "MASTERS",
        "resource": "unit",
        "action": "READ",
    },
    {
        "code": "MASTER_UNIT_CREATE",
        "name": "Create Unit",
        "module": "MASTERS",
        "resource": "unit",
        "action": "CREATE",
    },
    {
        "code": "MASTER_UNIT_UPDATE",
        "name": "Update Unit",
        "module": "MASTERS",
        "resource": "unit",
        "action": "UPDATE",
    },
    {
        "code": "MASTER_UNIT_DELETE",
        "name": "Delete Unit",
        "module": "MASTERS",
        "resource": "unit",
        "action": "DELETE",
    },
    # Masters - Department
    {
        "code": "MASTER_DEPT_VIEW",
        "name": "View Departments",
        "module": "MASTERS",
        "resource": "department",
        "action": "READ",
    },
    {
        "code": "MASTER_DEPT_CREATE",
        "name": "Create Department",
        "module": "MASTERS",
        "resource": "department",
        "action": "CREATE",
    },
    {
        "code": "MASTER_DEPT_UPDATE",
        "name": "Update Department",
        "module": "MASTERS",
        "resource": "department",
        "action": "UPDATE",
    },
    {
        "code": "MASTER_DEPT_DELETE",
        "name": "Delete Department",
        "module": "MASTERS",
        "resource": "department",
        "action": "DELETE",
    },
    # Masters - Designation
    {
        "code": "MASTER_DESIG_VIEW",
        "name": "View Designations",
        "module": "MASTERS",
        "resource": "designation",
        "action": "READ",
    },
    {
        "code": "MASTER_DESIG_CREATE",
        "name": "Create Designation",
        "module": "MASTERS",
        "resource": "designation",
        "action": "CREATE",
    },
    {
        "code": "MASTER_DESIG_UPDATE",
        "name": "Update Designation",
        "module": "MASTERS",
        "resource": "designation",
        "action": "UPDATE",
    },
    {
        "code": "MASTER_DESIG_DELETE",
        "name": "Delete Designation",
        "module": "MASTERS",
        "resource": "designation",
        "action": "DELETE",
    },
    # User Management
    {
        "code": "USER_VIEW",
        "name": "View Users",
        "module": "USER_MGMT",
        "resource": "user",
        "action": "READ",
    },
    {
        "code": "USER_CREATE",
        "name": "Create User",
        "module": "USER_MGMT",
        "resource": "user",
        "action": "CREATE",
    },
    {
        "code": "USER_UPDATE",
        "name": "Update User",
        "module": "USER_MGMT",
        "resource": "user",
        "action": "UPDATE",
    },
    {
        "code": "USER_DELETE",
        "name": "Delete User",
        "module": "USER_MGMT",
        "resource": "user",
        "action": "DELETE",
    },
    {
        "code": "USER_ROLE_ASSIGN",
        "name": "Assign Roles to User",
        "module": "USER_MGMT",
        "resource": "user",
        "action": "UPDATE",
    },
    {
        "code": "USER_UNLOCK",
        "name": "Unlock User Account",
        "module": "USER_MGMT",
        "resource": "user",
        "action": "UPDATE",
    },
    {
        "code": "USER_RESET_PASSWORD",
        "name": "Reset User Password",
        "module": "USER_MGMT",
        "resource": "user",
        "action": "UPDATE",
    },
    # Role Management
    {
        "code": "ROLE_VIEW",
        "name": "View Roles",
        "module": "USER_MGMT",
        "resource": "role",
        "action": "READ",
    },
    {
        "code": "ROLE_CREATE",
        "name": "Create Role",
        "module": "USER_MGMT",
        "resource": "role",
        "action": "CREATE",
    },
    {
        "code": "ROLE_UPDATE",
        "name": "Update Role",
        "module": "USER_MGMT",
        "resource": "role",
        "action": "UPDATE",
    },
    {
        "code": "ROLE_DELETE",
        "name": "Delete Role",
        "module": "USER_MGMT",
        "resource": "role",
        "action": "DELETE",
    },
    {
        "code": "ROLE_PERMISSION_ASSIGN",
        "name": "Assign Permissions to Role",
        "module": "USER_MGMT",
        "resource": "role",
        "action": "UPDATE",
    },
    # Finance - Financial Year
    {
        "code": "FIN_FY_VIEW",
        "name": "View Financial Years",
        "module": "FINANCE",
        "resource": "financial_year",
        "action": "READ",
    },
    {
        "code": "FIN_FY_CREATE",
        "name": "Create Financial Year",
        "module": "FINANCE",
        "resource": "financial_year",
        "action": "CREATE",
    },
    {
        "code": "FIN_FY_UPDATE",
        "name": "Update Financial Year",
        "module": "FINANCE",
        "resource": "financial_year",
        "action": "UPDATE",
    },
    {
        "code": "FIN_FY_DELETE",
        "name": "Delete Financial Year",
        "module": "FINANCE",
        "resource": "financial_year",
        "action": "DELETE",
    },
    {
        "code": "FIN_FY_CLOSE",
        "name": "Close Financial Year/Period",
        "module": "FINANCE",
        "resource": "financial_year",
        "action": "APPROVE",
    },
    # Finance - Chart of Accounts
    {
        "code": "FIN_COA_VIEW",
        "name": "View Chart of Accounts",
        "module": "FINANCE",
        "resource": "account",
        "action": "READ",
    },
    {
        "code": "FIN_COA_CREATE",
        "name": "Create Account/Group",
        "module": "FINANCE",
        "resource": "account",
        "action": "CREATE",
    },
    {
        "code": "FIN_COA_UPDATE",
        "name": "Update Account/Group",
        "module": "FINANCE",
        "resource": "account",
        "action": "UPDATE",
    },
    {
        "code": "FIN_COA_DELETE",
        "name": "Delete Account/Group",
        "module": "FINANCE",
        "resource": "account",
        "action": "DELETE",
    },
    # Finance - Voucher Types
    {
        "code": "FIN_VTYPE_VIEW",
        "name": "View Voucher Types",
        "module": "FINANCE",
        "resource": "voucher_type",
        "action": "READ",
    },
    {
        "code": "FIN_VTYPE_CREATE",
        "name": "Create Voucher Type",
        "module": "FINANCE",
        "resource": "voucher_type",
        "action": "CREATE",
    },
    {
        "code": "FIN_VTYPE_UPDATE",
        "name": "Update Voucher Type",
        "module": "FINANCE",
        "resource": "voucher_type",
        "action": "UPDATE",
    },
    {
        "code": "FIN_VTYPE_DELETE",
        "name": "Delete Voucher Type",
        "module": "FINANCE",
        "resource": "voucher_type",
        "action": "DELETE",
    },
    # Finance - Vouchers
    {
        "code": "FIN_VOUCHER_VIEW",
        "name": "View Vouchers",
        "module": "FINANCE",
        "resource": "voucher",
        "action": "READ",
    },
    {
        "code": "FIN_VOUCHER_CREATE",
        "name": "Create Voucher",
        "module": "FINANCE",
        "resource": "voucher",
        "action": "CREATE",
    },
    {
        "code": "FIN_VOUCHER_UPDATE",
        "name": "Update Voucher",
        "module": "FINANCE",
        "resource": "voucher",
        "action": "UPDATE",
    },
    {
        "code": "FIN_VOUCHER_DELETE",
        "name": "Delete Voucher",
        "module": "FINANCE",
        "resource": "voucher",
        "action": "DELETE",
    },
    {
        "code": "FIN_VOUCHER_APPROVE",
        "name": "Approve Voucher",
        "module": "FINANCE",
        "resource": "voucher",
        "action": "APPROVE",
    },
    {
        "code": "FIN_VOUCHER_POST",
        "name": "Post Voucher to Ledger",
        "module": "FINANCE",
        "resource": "voucher",
        "action": "APPROVE",
    },
    {
        "code": "FIN_VOUCHER_CANCEL",
        "name": "Cancel Voucher",
        "module": "FINANCE",
        "resource": "voucher",
        "action": "DELETE",
    },
    # Finance - Reports
    {
        "code": "FIN_REPORT_VIEW",
        "name": "View Financial Reports",
        "module": "FINANCE",
        "resource": "report",
        "action": "READ",
    },
    {
        "code": "FIN_REPORT_EXPORT",
        "name": "Export Financial Reports",
        "module": "FINANCE",
        "resource": "report",
        "action": "EXPORT",
    },
    # AP/AR - Payment Terms
    {
        "code": "APAR_TERMS_VIEW",
        "name": "View Payment Terms",
        "module": "AP_AR",
        "resource": "payment_terms",
        "action": "READ",
    },
    {
        "code": "APAR_TERMS_CREATE",
        "name": "Create Payment Terms",
        "module": "AP_AR",
        "resource": "payment_terms",
        "action": "CREATE",
    },
    {
        "code": "APAR_TERMS_UPDATE",
        "name": "Update Payment Terms",
        "module": "AP_AR",
        "resource": "payment_terms",
        "action": "UPDATE",
    },
    {
        "code": "APAR_TERMS_DELETE",
        "name": "Delete Payment Terms",
        "module": "AP_AR",
        "resource": "payment_terms",
        "action": "DELETE",
    },
    # AP/AR - Vendors
    {
        "code": "APAR_VENDOR_VIEW",
        "name": "View Vendors",
        "module": "AP_AR",
        "resource": "vendor",
        "action": "READ",
    },
    {
        "code": "APAR_VENDOR_CREATE",
        "name": "Create Vendor",
        "module": "AP_AR",
        "resource": "vendor",
        "action": "CREATE",
    },
    {
        "code": "APAR_VENDOR_UPDATE",
        "name": "Update Vendor",
        "module": "AP_AR",
        "resource": "vendor",
        "action": "UPDATE",
    },
    {
        "code": "APAR_VENDOR_DELETE",
        "name": "Delete Vendor",
        "module": "AP_AR",
        "resource": "vendor",
        "action": "DELETE",
    },
    # AP/AR - Customers
    {
        "code": "APAR_CUSTOMER_VIEW",
        "name": "View Customers",
        "module": "AP_AR",
        "resource": "customer",
        "action": "READ",
    },
    {
        "code": "APAR_CUSTOMER_CREATE",
        "name": "Create Customer",
        "module": "AP_AR",
        "resource": "customer",
        "action": "CREATE",
    },
    {
        "code": "APAR_CUSTOMER_UPDATE",
        "name": "Update Customer",
        "module": "AP_AR",
        "resource": "customer",
        "action": "UPDATE",
    },
    {
        "code": "APAR_CUSTOMER_DELETE",
        "name": "Delete Customer",
        "module": "AP_AR",
        "resource": "customer",
        "action": "DELETE",
    },
    # AP/AR - Purchase Bills
    {
        "code": "APAR_BILL_VIEW",
        "name": "View Purchase Bills",
        "module": "AP_AR",
        "resource": "purchase_bill",
        "action": "READ",
    },
    {
        "code": "APAR_BILL_CREATE",
        "name": "Create Purchase Bill",
        "module": "AP_AR",
        "resource": "purchase_bill",
        "action": "CREATE",
    },
    {
        "code": "APAR_BILL_UPDATE",
        "name": "Update Purchase Bill",
        "module": "AP_AR",
        "resource": "purchase_bill",
        "action": "UPDATE",
    },
    {
        "code": "APAR_BILL_DELETE",
        "name": "Delete Purchase Bill",
        "module": "AP_AR",
        "resource": "purchase_bill",
        "action": "DELETE",
    },
    {
        "code": "APAR_BILL_APPROVE",
        "name": "Approve Purchase Bill",
        "module": "AP_AR",
        "resource": "purchase_bill",
        "action": "APPROVE",
    },
    # AP/AR - Sales Invoices
    {
        "code": "APAR_INVOICE_VIEW",
        "name": "View Sales Invoices",
        "module": "AP_AR",
        "resource": "sales_invoice",
        "action": "READ",
    },
    {
        "code": "APAR_INVOICE_CREATE",
        "name": "Create Sales Invoice",
        "module": "AP_AR",
        "resource": "sales_invoice",
        "action": "CREATE",
    },
    {
        "code": "APAR_INVOICE_UPDATE",
        "name": "Update Sales Invoice",
        "module": "AP_AR",
        "resource": "sales_invoice",
        "action": "UPDATE",
    },
    {
        "code": "APAR_INVOICE_DELETE",
        "name": "Delete Sales Invoice",
        "module": "AP_AR",
        "resource": "sales_invoice",
        "action": "DELETE",
    },
    {
        "code": "APAR_INVOICE_APPROVE",
        "name": "Approve Sales Invoice",
        "module": "AP_AR",
        "resource": "sales_invoice",
        "action": "APPROVE",
    },
    # AP/AR - Payments
    {
        "code": "APAR_PAYMENT_VIEW",
        "name": "View Payments",
        "module": "AP_AR",
        "resource": "payment",
        "action": "READ",
    },
    {
        "code": "APAR_PAYMENT_CREATE",
        "name": "Create Payment",
        "module": "AP_AR",
        "resource": "payment",
        "action": "CREATE",
    },
    {
        "code": "APAR_PAYMENT_UPDATE",
        "name": "Update Payment",
        "module": "AP_AR",
        "resource": "payment",
        "action": "UPDATE",
    },
    {
        "code": "APAR_PAYMENT_DELETE",
        "name": "Delete Payment",
        "module": "AP_AR",
        "resource": "payment",
        "action": "DELETE",
    },
    {
        "code": "APAR_PAYMENT_APPROVE",
        "name": "Approve Payment",
        "module": "AP_AR",
        "resource": "payment",
        "action": "APPROVE",
    },
    # AP/AR - Bank Reconciliation
    {
        "code": "APAR_BRS_VIEW",
        "name": "View Bank Reconciliation",
        "module": "AP_AR",
        "resource": "bank_reconciliation",
        "action": "READ",
    },
    {
        "code": "APAR_BRS_CREATE",
        "name": "Perform Bank Reconciliation",
        "module": "AP_AR",
        "resource": "bank_reconciliation",
        "action": "CREATE",
    },
    {
        "code": "APAR_BRS_APPROVE",
        "name": "Approve Bank Reconciliation",
        "module": "AP_AR",
        "resource": "bank_reconciliation",
        "action": "APPROVE",
    },
    # AP/AR - Reports
    {
        "code": "APAR_REPORT_VIEW",
        "name": "View AP/AR Reports",
        "module": "AP_AR",
        "resource": "report",
        "action": "READ",
    },
    {
        "code": "APAR_REPORT_EXPORT",
        "name": "Export AP/AR Reports",
        "module": "AP_AR",
        "resource": "report",
        "action": "EXPORT",
    },
]

# Role definitions
ROLES = [
    {
        "code": "SUPER_ADMIN",
        "name": "Super Administrator",
        "description": "Full system access with all permissions",
        "is_system_role": True,
        "is_default": False,
        "permissions": "*",  # All permissions
    },
    {
        "code": "ORG_ADMIN",
        "name": "Organization Administrator",
        "description": "Organization-level administration",
        "is_system_role": True,
        "is_default": False,
        "permissions": [
            "MASTER_ORG_VIEW",
            "MASTER_ORG_UPDATE",
            "MASTER_UNIT_VIEW",
            "MASTER_UNIT_CREATE",
            "MASTER_UNIT_UPDATE",
            "MASTER_UNIT_DELETE",
            "MASTER_DEPT_VIEW",
            "MASTER_DEPT_CREATE",
            "MASTER_DEPT_UPDATE",
            "MASTER_DEPT_DELETE",
            "MASTER_DESIG_VIEW",
            "MASTER_DESIG_CREATE",
            "MASTER_DESIG_UPDATE",
            "MASTER_DESIG_DELETE",
            "USER_VIEW",
            "USER_CREATE",
            "USER_UPDATE",
            "USER_DELETE",
            "USER_ROLE_ASSIGN",
            "USER_UNLOCK",
            "USER_RESET_PASSWORD",
            "ROLE_VIEW",
        ],
    },
    {
        "code": "BRANCH_MANAGER",
        "name": "Branch Manager",
        "description": "Branch-level management",
        "is_system_role": True,
        "is_default": False,
        "permissions": [
            "MASTER_ORG_VIEW",
            "MASTER_UNIT_VIEW",
            "MASTER_DEPT_VIEW",
            "MASTER_DESIG_VIEW",
            "USER_VIEW",
            "ROLE_VIEW",
        ],
    },
    {
        "code": "OPERATOR",
        "name": "Operator",
        "description": "Data entry operator with create access",
        "is_system_role": True,
        "is_default": False,
        "permissions": [
            "MASTER_ORG_VIEW",
            "MASTER_UNIT_VIEW",
            "MASTER_UNIT_CREATE",
            "MASTER_DEPT_VIEW",
            "MASTER_DEPT_CREATE",
            "MASTER_DESIG_VIEW",
            "MASTER_DESIG_CREATE",
            "USER_VIEW",
            "ROLE_VIEW",
        ],
    },
    {
        "code": "VIEWER",
        "name": "Viewer",
        "description": "Read-only access",
        "is_system_role": True,
        "is_default": True,
        "permissions": [
            "MASTER_ORG_VIEW",
            "MASTER_UNIT_VIEW",
            "MASTER_DEPT_VIEW",
            "MASTER_DESIG_VIEW",
            "USER_VIEW",
            "ROLE_VIEW",
        ],
    },
    {
        "code": "FINANCE_MANAGER",
        "name": "Finance Manager",
        "description": "Finance department manager with full finance access",
        "is_system_role": False,
        "is_default": False,
        "permissions": [
            "MASTER_ORG_VIEW",
            "MASTER_UNIT_VIEW",
            "MASTER_DEPT_VIEW",
            "MASTER_DESIG_VIEW",
            "USER_VIEW",
            "ROLE_VIEW",
            # Finance permissions
            "FIN_FY_VIEW",
            "FIN_FY_CREATE",
            "FIN_FY_UPDATE",
            "FIN_FY_CLOSE",
            "FIN_COA_VIEW",
            "FIN_COA_CREATE",
            "FIN_COA_UPDATE",
            "FIN_COA_DELETE",
            "FIN_VTYPE_VIEW",
            "FIN_VTYPE_CREATE",
            "FIN_VTYPE_UPDATE",
            "FIN_VOUCHER_VIEW",
            "FIN_VOUCHER_CREATE",
            "FIN_VOUCHER_UPDATE",
            "FIN_VOUCHER_APPROVE",
            "FIN_VOUCHER_POST",
            "FIN_VOUCHER_CANCEL",
            "FIN_REPORT_VIEW",
            "FIN_REPORT_EXPORT",
        ],
    },
    {
        "code": "ACCOUNTANT",
        "name": "Accountant",
        "description": "Accounts and bookkeeping",
        "is_system_role": False,
        "is_default": False,
        "permissions": [
            "MASTER_ORG_VIEW",
            "MASTER_UNIT_VIEW",
            "MASTER_DEPT_VIEW",
            "MASTER_DESIG_VIEW",
            "USER_VIEW",
            "ROLE_VIEW",
            # Finance permissions (limited)
            "FIN_FY_VIEW",
            "FIN_COA_VIEW",
            "FIN_VTYPE_VIEW",
            "FIN_VOUCHER_VIEW",
            "FIN_VOUCHER_CREATE",
            "FIN_VOUCHER_UPDATE",
            "FIN_REPORT_VIEW",
        ],
    },
    {
        "code": "HR_MANAGER",
        "name": "HR Manager",
        "description": "Human resources manager",
        "is_system_role": False,
        "is_default": False,
        "permissions": [
            "MASTER_ORG_VIEW",
            "MASTER_UNIT_VIEW",
            "MASTER_DEPT_VIEW",
            "MASTER_DEPT_CREATE",
            "MASTER_DEPT_UPDATE",
            "MASTER_DESIG_VIEW",
            "MASTER_DESIG_CREATE",
            "MASTER_DESIG_UPDATE",
            "USER_VIEW",
            "USER_CREATE",
            "USER_UPDATE",
            "ROLE_VIEW",
        ],
    },
]

# Sample data
DEPARTMENTS = [
    {"code": "ADMIN", "name": "Administration", "short_name": "Admin", "cost_center_code": "CC001"},
    {
        "code": "FIN",
        "name": "Finance & Accounts",
        "short_name": "Finance",
        "cost_center_code": "CC002",
    },
    {"code": "HR", "name": "Human Resources", "short_name": "HR", "cost_center_code": "CC003"},
    {
        "code": "IT",
        "name": "Information Technology",
        "short_name": "IT",
        "cost_center_code": "CC004",
    },
    {"code": "OPS", "name": "Operations", "short_name": "Ops", "cost_center_code": "CC005"},
    {
        "code": "SALES",
        "name": "Sales & Marketing",
        "short_name": "Sales",
        "cost_center_code": "CC006",
    },
]

UNITS = [
    {
        "code": "HO",
        "name": "Head Office",
        "unit_type": "HEAD_OFFICE",
        "city": "Mumbai",
        "state_code": "27",
        "is_head_office": True,
    },
    {
        "code": "MUM01",
        "name": "Mumbai Branch",
        "unit_type": "BRANCH",
        "city": "Mumbai",
        "state_code": "27",
    },
    {
        "code": "DEL01",
        "name": "Delhi Branch",
        "unit_type": "BRANCH",
        "city": "New Delhi",
        "state_code": "07",
    },
    {
        "code": "BLR01",
        "name": "Bangalore Branch",
        "unit_type": "BRANCH",
        "city": "Bangalore",
        "state_code": "29",
    },
    {
        "code": "CHN01",
        "name": "Chennai Branch",
        "unit_type": "BRANCH",
        "city": "Chennai",
        "state_code": "33",
    },
]

DESIGNATIONS = [
    {"code": "CEO", "name": "Chief Executive Officer", "level": 1, "min_experience_years": 15},
    {"code": "CFO", "name": "Chief Financial Officer", "level": 2, "min_experience_years": 12},
    {"code": "CTO", "name": "Chief Technology Officer", "level": 2, "min_experience_years": 12},
    {"code": "VP", "name": "Vice President", "level": 3, "min_experience_years": 10},
    {"code": "GM", "name": "General Manager", "level": 4, "min_experience_years": 8},
    {"code": "MGR", "name": "Manager", "level": 5, "min_experience_years": 5},
    {"code": "SR_EXEC", "name": "Senior Executive", "level": 6, "min_experience_years": 3},
    {"code": "EXEC", "name": "Executive", "level": 7, "min_experience_years": 1},
    {"code": "TRAINEE", "name": "Trainee", "level": 8, "min_experience_years": 0},
]

# Admin user and sample users
ADMIN_USER = {
    "username": os.getenv("SEED_ADMIN_USERNAME", "krishna"),
    "email": os.getenv("SEED_ADMIN_EMAIL", "krishna@supersight.com"),
    "full_name": os.getenv("SEED_ADMIN_FULL_NAME", "Krishna Administrator"),
    "password": os.getenv("SEED_ADMIN_PASSWORD", "ChangeMe123!"),
    "employee_code": "EMP001",
    "role": "SUPER_ADMIN",
}

SAMPLE_USERS = [
    {
        "username": "rajesh.kumar",
        "email": "rajesh.kumar@smfc.com",
        "full_name": "Rajesh Kumar",
        "employee_code": "EMP002",
        "role": "ORG_ADMIN",
    },
    {
        "username": "priya.sharma",
        "email": "priya.sharma@smfc.com",
        "full_name": "Priya Sharma",
        "employee_code": "EMP003",
        "role": "HR_MANAGER",
    },
    {
        "username": "amit.patel",
        "email": "amit.patel@smfc.com",
        "full_name": "Amit Patel",
        "employee_code": "EMP004",
        "role": "FINANCE_MANAGER",
    },
    {
        "username": "sneha.reddy",
        "email": "sneha.reddy@smfc.com",
        "full_name": "Sneha Reddy",
        "employee_code": "EMP005",
        "role": "BRANCH_MANAGER",
    },
    {
        "username": "vikram.singh",
        "email": "vikram.singh@smfc.com",
        "full_name": "Vikram Singh",
        "employee_code": "EMP006",
        "role": "OPERATOR",
    },
    {
        "username": "ananya.gupta",
        "email": "ananya.gupta@smfc.com",
        "full_name": "Ananya Gupta",
        "employee_code": "EMP007",
        "role": "VIEWER",
    },
    {
        "username": "rahul.verma",
        "email": "rahul.verma@smfc.com",
        "full_name": "Rahul Verma",
        "employee_code": "EMP008",
        "role": "OPERATOR",
    },
    {
        "username": "meera.nair",
        "email": "meera.nair@smfc.com",
        "full_name": "Meera Nair",
        "employee_code": "EMP009",
        "role": "VIEWER",
    },
]

# =====================================================
# FINANCE SEED DATA - Indian Standards (Schedule III)
# =====================================================

# Account Groups - Following Indian Schedule III of Companies Act 2013
ACCOUNT_GROUPS = [
    # Level 0 - Primary Groups (Nature-based)
    {
        "code": "ASSETS",
        "name": "Assets",
        "nature": "ASSETS",
        "level": 0,
        "sequence": 1,
        "is_system": True,
    },
    {
        "code": "LIABILITIES",
        "name": "Liabilities",
        "nature": "LIABILITIES",
        "level": 0,
        "sequence": 2,
        "is_system": True,
    },
    {
        "code": "EQUITY",
        "name": "Equity / Shareholders' Funds",
        "nature": "EQUITY",
        "level": 0,
        "sequence": 3,
        "is_system": True,
    },
    {
        "code": "INCOME",
        "name": "Income",
        "nature": "INCOME",
        "level": 0,
        "sequence": 4,
        "is_system": True,
    },
    {
        "code": "EXPENSES",
        "name": "Expenses",
        "nature": "EXPENSES",
        "level": 0,
        "sequence": 5,
        "is_system": True,
    },
    # Level 1 - ASSETS Sub-Groups (Schedule III Format)
    {
        "code": "NONCURR_ASSETS",
        "name": "Non-Current Assets",
        "nature": "ASSETS",
        "parent": "ASSETS",
        "level": 1,
        "sequence": 1,
        "is_system": True,
    },
    {
        "code": "CURR_ASSETS",
        "name": "Current Assets",
        "nature": "ASSETS",
        "parent": "ASSETS",
        "level": 1,
        "sequence": 2,
        "is_system": True,
    },
    # Level 2 - Non-Current Assets
    {
        "code": "PPE",
        "name": "Property, Plant and Equipment",
        "nature": "ASSETS",
        "parent": "NONCURR_ASSETS",
        "level": 2,
        "sequence": 1,
        "is_system": True,
    },
    {
        "code": "INTANGIBLE",
        "name": "Intangible Assets",
        "nature": "ASSETS",
        "parent": "NONCURR_ASSETS",
        "level": 2,
        "sequence": 2,
        "is_system": True,
    },
    {
        "code": "CAPITAL_WIP",
        "name": "Capital Work-in-Progress",
        "nature": "ASSETS",
        "parent": "NONCURR_ASSETS",
        "level": 2,
        "sequence": 3,
        "is_system": True,
    },
    {
        "code": "FIN_ASSETS_NC",
        "name": "Financial Assets (Non-Current)",
        "nature": "ASSETS",
        "parent": "NONCURR_ASSETS",
        "level": 2,
        "sequence": 4,
        "is_system": True,
    },
    {
        "code": "DEFERRED_TAX_ASSET",
        "name": "Deferred Tax Assets (Net)",
        "nature": "ASSETS",
        "parent": "NONCURR_ASSETS",
        "level": 2,
        "sequence": 5,
        "is_system": True,
    },
    {
        "code": "OTHER_NC_ASSETS",
        "name": "Other Non-Current Assets",
        "nature": "ASSETS",
        "parent": "NONCURR_ASSETS",
        "level": 2,
        "sequence": 6,
        "is_system": True,
    },
    # Level 2 - Current Assets
    {
        "code": "INVENTORIES",
        "name": "Inventories",
        "nature": "ASSETS",
        "parent": "CURR_ASSETS",
        "level": 2,
        "sequence": 1,
        "is_system": True,
    },
    {
        "code": "FIN_ASSETS_C",
        "name": "Financial Assets (Current)",
        "nature": "ASSETS",
        "parent": "CURR_ASSETS",
        "level": 2,
        "sequence": 2,
        "is_system": True,
    },
    {
        "code": "CURR_TAX_ASSETS",
        "name": "Current Tax Assets (Net)",
        "nature": "ASSETS",
        "parent": "CURR_ASSETS",
        "level": 2,
        "sequence": 3,
        "is_system": True,
    },
    {
        "code": "OTHER_CURR_ASSETS",
        "name": "Other Current Assets",
        "nature": "ASSETS",
        "parent": "CURR_ASSETS",
        "level": 2,
        "sequence": 4,
        "is_system": True,
    },
    # Level 3 - Financial Assets (Current) - detailed
    {
        "code": "TRADE_RECEIVABLES",
        "name": "Trade Receivables",
        "nature": "ASSETS",
        "parent": "FIN_ASSETS_C",
        "level": 3,
        "sequence": 1,
        "is_system": True,
    },
    {
        "code": "CASH_EQUIVALENTS",
        "name": "Cash and Cash Equivalents",
        "nature": "ASSETS",
        "parent": "FIN_ASSETS_C",
        "level": 3,
        "sequence": 2,
        "is_system": True,
    },
    {
        "code": "BANK_BALANCES",
        "name": "Bank Balances",
        "nature": "ASSETS",
        "parent": "FIN_ASSETS_C",
        "level": 3,
        "sequence": 3,
        "is_system": True,
    },
    {
        "code": "LOANS_ADVANCES",
        "name": "Loans and Advances",
        "nature": "ASSETS",
        "parent": "FIN_ASSETS_C",
        "level": 3,
        "sequence": 4,
        "is_system": True,
    },
    {
        "code": "OTHER_FIN_ASSETS",
        "name": "Other Financial Assets",
        "nature": "ASSETS",
        "parent": "FIN_ASSETS_C",
        "level": 3,
        "sequence": 5,
        "is_system": True,
    },
    # Level 1 - LIABILITIES Sub-Groups
    {
        "code": "NONCURR_LIAB",
        "name": "Non-Current Liabilities",
        "nature": "LIABILITIES",
        "parent": "LIABILITIES",
        "level": 1,
        "sequence": 1,
        "is_system": True,
    },
    {
        "code": "CURR_LIAB",
        "name": "Current Liabilities",
        "nature": "LIABILITIES",
        "parent": "LIABILITIES",
        "level": 1,
        "sequence": 2,
        "is_system": True,
    },
    # Level 2 - Non-Current Liabilities
    {
        "code": "FIN_LIAB_NC",
        "name": "Financial Liabilities (Non-Current)",
        "nature": "LIABILITIES",
        "parent": "NONCURR_LIAB",
        "level": 2,
        "sequence": 1,
        "is_system": True,
    },
    {
        "code": "PROVISIONS_NC",
        "name": "Provisions (Non-Current)",
        "nature": "LIABILITIES",
        "parent": "NONCURR_LIAB",
        "level": 2,
        "sequence": 2,
        "is_system": True,
    },
    {
        "code": "DEFERRED_TAX_LIAB",
        "name": "Deferred Tax Liabilities (Net)",
        "nature": "LIABILITIES",
        "parent": "NONCURR_LIAB",
        "level": 2,
        "sequence": 3,
        "is_system": True,
    },
    {
        "code": "OTHER_NC_LIAB",
        "name": "Other Non-Current Liabilities",
        "nature": "LIABILITIES",
        "parent": "NONCURR_LIAB",
        "level": 2,
        "sequence": 4,
        "is_system": True,
    },
    # Level 2 - Current Liabilities
    {
        "code": "FIN_LIAB_C",
        "name": "Financial Liabilities (Current)",
        "nature": "LIABILITIES",
        "parent": "CURR_LIAB",
        "level": 2,
        "sequence": 1,
        "is_system": True,
    },
    {
        "code": "OTHER_CURR_LIAB",
        "name": "Other Current Liabilities",
        "nature": "LIABILITIES",
        "parent": "CURR_LIAB",
        "level": 2,
        "sequence": 2,
        "is_system": True,
    },
    {
        "code": "PROVISIONS_C",
        "name": "Provisions (Current)",
        "nature": "LIABILITIES",
        "parent": "CURR_LIAB",
        "level": 2,
        "sequence": 3,
        "is_system": True,
    },
    {
        "code": "CURR_TAX_LIAB",
        "name": "Current Tax Liabilities (Net)",
        "nature": "LIABILITIES",
        "parent": "CURR_LIAB",
        "level": 2,
        "sequence": 4,
        "is_system": True,
    },
    # Level 3 - Financial Liabilities (Current) - detailed
    {
        "code": "TRADE_PAYABLES",
        "name": "Trade Payables",
        "nature": "LIABILITIES",
        "parent": "FIN_LIAB_C",
        "level": 3,
        "sequence": 1,
        "is_system": True,
    },
    {
        "code": "BORROWINGS_C",
        "name": "Borrowings (Current)",
        "nature": "LIABILITIES",
        "parent": "FIN_LIAB_C",
        "level": 3,
        "sequence": 2,
        "is_system": True,
    },
    {
        "code": "OTHER_FIN_LIAB",
        "name": "Other Financial Liabilities",
        "nature": "LIABILITIES",
        "parent": "FIN_LIAB_C",
        "level": 3,
        "sequence": 3,
        "is_system": True,
    },
    # Level 3 - Other Current Liabilities - detailed
    {
        "code": "STATUTORY_DUES",
        "name": "Statutory Dues Payable",
        "nature": "LIABILITIES",
        "parent": "OTHER_CURR_LIAB",
        "level": 3,
        "sequence": 1,
        "is_system": True,
    },
    {
        "code": "DUTIES_TAXES",
        "name": "Duties and Taxes",
        "nature": "LIABILITIES",
        "parent": "OTHER_CURR_LIAB",
        "level": 3,
        "sequence": 2,
        "is_system": True,
    },
    # Level 1 - EQUITY Sub-Groups
    {
        "code": "SHARE_CAPITAL",
        "name": "Share Capital",
        "nature": "EQUITY",
        "parent": "EQUITY",
        "level": 1,
        "sequence": 1,
        "is_system": True,
    },
    {
        "code": "RESERVES_SURPLUS",
        "name": "Reserves and Surplus",
        "nature": "EQUITY",
        "parent": "EQUITY",
        "level": 1,
        "sequence": 2,
        "is_system": True,
    },
    {
        "code": "OTHER_EQUITY",
        "name": "Other Equity",
        "nature": "EQUITY",
        "parent": "EQUITY",
        "level": 1,
        "sequence": 3,
        "is_system": True,
    },
    # Level 2 - Reserves and Surplus
    {
        "code": "CAPITAL_RESERVE",
        "name": "Capital Reserve",
        "nature": "EQUITY",
        "parent": "RESERVES_SURPLUS",
        "level": 2,
        "sequence": 1,
        "is_system": True,
    },
    {
        "code": "SECURITIES_PREMIUM",
        "name": "Securities Premium",
        "nature": "EQUITY",
        "parent": "RESERVES_SURPLUS",
        "level": 2,
        "sequence": 2,
        "is_system": True,
    },
    {
        "code": "GENERAL_RESERVE",
        "name": "General Reserve",
        "nature": "EQUITY",
        "parent": "RESERVES_SURPLUS",
        "level": 2,
        "sequence": 3,
        "is_system": True,
    },
    {
        "code": "RETAINED_EARNINGS",
        "name": "Retained Earnings",
        "nature": "EQUITY",
        "parent": "RESERVES_SURPLUS",
        "level": 2,
        "sequence": 4,
        "is_system": True,
    },
    # Level 1 - INCOME Sub-Groups
    {
        "code": "REVENUE_OPS",
        "name": "Revenue from Operations",
        "nature": "INCOME",
        "parent": "INCOME",
        "level": 1,
        "sequence": 1,
        "is_system": True,
    },
    {
        "code": "OTHER_INCOME",
        "name": "Other Income",
        "nature": "INCOME",
        "parent": "INCOME",
        "level": 1,
        "sequence": 2,
        "is_system": True,
    },
    # Level 2 - Revenue from Operations (NBFC specific)
    {
        "code": "INTEREST_INCOME",
        "name": "Interest Income",
        "nature": "INCOME",
        "parent": "REVENUE_OPS",
        "level": 2,
        "sequence": 1,
        "is_system": True,
    },
    {
        "code": "FEE_COMMISSION",
        "name": "Fee and Commission Income",
        "nature": "INCOME",
        "parent": "REVENUE_OPS",
        "level": 2,
        "sequence": 2,
        "is_system": True,
    },
    {
        "code": "NET_GAIN_FV",
        "name": "Net Gain on Fair Value Changes",
        "nature": "INCOME",
        "parent": "REVENUE_OPS",
        "level": 2,
        "sequence": 3,
        "is_system": True,
    },
    # Level 2 - Other Income
    {
        "code": "DIVIDEND_INCOME",
        "name": "Dividend Income",
        "nature": "INCOME",
        "parent": "OTHER_INCOME",
        "level": 2,
        "sequence": 1,
        "is_system": True,
    },
    {
        "code": "RENTAL_INCOME",
        "name": "Rental Income",
        "nature": "INCOME",
        "parent": "OTHER_INCOME",
        "level": 2,
        "sequence": 2,
        "is_system": True,
    },
    {
        "code": "MISC_INCOME",
        "name": "Miscellaneous Income",
        "nature": "INCOME",
        "parent": "OTHER_INCOME",
        "level": 2,
        "sequence": 3,
        "is_system": True,
    },
    # Level 1 - EXPENSES Sub-Groups
    {
        "code": "FINANCE_COSTS",
        "name": "Finance Costs",
        "nature": "EXPENSES",
        "parent": "EXPENSES",
        "level": 1,
        "sequence": 1,
        "is_system": True,
    },
    {
        "code": "IMPAIRMENT",
        "name": "Impairment on Financial Instruments",
        "nature": "EXPENSES",
        "parent": "EXPENSES",
        "level": 1,
        "sequence": 2,
        "is_system": True,
    },
    {
        "code": "EMPLOYEE_BENEFITS",
        "name": "Employee Benefits Expense",
        "nature": "EXPENSES",
        "parent": "EXPENSES",
        "level": 1,
        "sequence": 3,
        "is_system": True,
    },
    {
        "code": "DEPRECIATION",
        "name": "Depreciation and Amortisation",
        "nature": "EXPENSES",
        "parent": "EXPENSES",
        "level": 1,
        "sequence": 4,
        "is_system": True,
    },
    {
        "code": "OTHER_EXPENSES",
        "name": "Other Expenses",
        "nature": "EXPENSES",
        "parent": "EXPENSES",
        "level": 1,
        "sequence": 5,
        "is_system": True,
    },
    # Level 2 - Finance Costs
    {
        "code": "INTEREST_EXP",
        "name": "Interest Expense",
        "nature": "EXPENSES",
        "parent": "FINANCE_COSTS",
        "level": 2,
        "sequence": 1,
        "is_system": True,
    },
    {
        "code": "OTHER_BORROWING_COSTS",
        "name": "Other Borrowing Costs",
        "nature": "EXPENSES",
        "parent": "FINANCE_COSTS",
        "level": 2,
        "sequence": 2,
        "is_system": True,
    },
    # Level 2 - Employee Benefits
    {
        "code": "SALARIES_WAGES",
        "name": "Salaries and Wages",
        "nature": "EXPENSES",
        "parent": "EMPLOYEE_BENEFITS",
        "level": 2,
        "sequence": 1,
        "is_system": True,
    },
    {
        "code": "CONTRIBUTION_PF",
        "name": "Contribution to PF/ESI",
        "nature": "EXPENSES",
        "parent": "EMPLOYEE_BENEFITS",
        "level": 2,
        "sequence": 2,
        "is_system": True,
    },
    {
        "code": "STAFF_WELFARE",
        "name": "Staff Welfare Expenses",
        "nature": "EXPENSES",
        "parent": "EMPLOYEE_BENEFITS",
        "level": 2,
        "sequence": 3,
        "is_system": True,
    },
    {
        "code": "GRATUITY_EXP",
        "name": "Gratuity Expense",
        "nature": "EXPENSES",
        "parent": "EMPLOYEE_BENEFITS",
        "level": 2,
        "sequence": 4,
        "is_system": True,
    },
    # Level 2 - Other Expenses
    {
        "code": "RENT_EXP",
        "name": "Rent Expense",
        "nature": "EXPENSES",
        "parent": "OTHER_EXPENSES",
        "level": 2,
        "sequence": 1,
        "is_system": True,
    },
    {
        "code": "REPAIRS_MAINT",
        "name": "Repairs and Maintenance",
        "nature": "EXPENSES",
        "parent": "OTHER_EXPENSES",
        "level": 2,
        "sequence": 2,
        "is_system": True,
    },
    {
        "code": "INSURANCE_EXP",
        "name": "Insurance Expense",
        "nature": "EXPENSES",
        "parent": "OTHER_EXPENSES",
        "level": 2,
        "sequence": 3,
        "is_system": True,
    },
    {
        "code": "LEGAL_PROF",
        "name": "Legal and Professional Fees",
        "nature": "EXPENSES",
        "parent": "OTHER_EXPENSES",
        "level": 2,
        "sequence": 4,
        "is_system": True,
    },
    {
        "code": "TRAVEL_CONV",
        "name": "Travel and Conveyance",
        "nature": "EXPENSES",
        "parent": "OTHER_EXPENSES",
        "level": 2,
        "sequence": 5,
        "is_system": True,
    },
    {
        "code": "COMM_EXP",
        "name": "Communication Expenses",
        "nature": "EXPENSES",
        "parent": "OTHER_EXPENSES",
        "level": 2,
        "sequence": 6,
        "is_system": True,
    },
    {
        "code": "PRINTING_STAT",
        "name": "Printing and Stationery",
        "nature": "EXPENSES",
        "parent": "OTHER_EXPENSES",
        "level": 2,
        "sequence": 7,
        "is_system": True,
    },
    {
        "code": "AUDIT_FEES",
        "name": "Audit Fees",
        "nature": "EXPENSES",
        "parent": "OTHER_EXPENSES",
        "level": 2,
        "sequence": 8,
        "is_system": True,
    },
    {
        "code": "BANK_CHARGES",
        "name": "Bank Charges",
        "nature": "EXPENSES",
        "parent": "OTHER_EXPENSES",
        "level": 2,
        "sequence": 9,
        "is_system": True,
    },
    {
        "code": "GST_EXP",
        "name": "GST Expense (Non-ITC)",
        "nature": "EXPENSES",
        "parent": "OTHER_EXPENSES",
        "level": 2,
        "sequence": 10,
        "is_system": True,
    },
    {
        "code": "MISC_EXP",
        "name": "Miscellaneous Expenses",
        "nature": "EXPENSES",
        "parent": "OTHER_EXPENSES",
        "level": 2,
        "sequence": 11,
        "is_system": True,
    },
]

# Sample Accounts (Ledgers)
ACCOUNTS = [
    # Cash & Bank Accounts
    {
        "code": "1001",
        "name": "Cash in Hand",
        "group": "CASH_EQUIVALENTS",
        "type": "CASH",
        "opening": 50000,
        "balance_type": "DEBIT",
    },
    {
        "code": "1002",
        "name": "Petty Cash",
        "group": "CASH_EQUIVALENTS",
        "type": "CASH",
        "opening": 10000,
        "balance_type": "DEBIT",
    },
    {
        "code": "1101",
        "name": "SBI Current Account",
        "group": "BANK_BALANCES",
        "type": "BANK",
        "opening": 500000,
        "balance_type": "DEBIT",
        "bank_name": "State Bank of India",
        "bank_branch": "BKC Branch",
        "bank_account": "39876543210",
        "bank_ifsc": "SBIN0001234",
    },
    {
        "code": "1102",
        "name": "HDFC Current Account",
        "group": "BANK_BALANCES",
        "type": "BANK",
        "opening": 300000,
        "balance_type": "DEBIT",
        "bank_name": "HDFC Bank",
        "bank_branch": "Andheri Branch",
        "bank_account": "50100123456789",
        "bank_ifsc": "HDFC0001234",
    },
    {
        "code": "1103",
        "name": "ICICI Savings Account",
        "group": "BANK_BALANCES",
        "type": "BANK",
        "opening": 100000,
        "balance_type": "DEBIT",
        "bank_name": "ICICI Bank",
        "bank_branch": "Fort Branch",
        "bank_account": "123456789012",
        "bank_ifsc": "ICIC0001234",
    },
    # Trade Receivables
    {
        "code": "1201",
        "name": "Trade Receivables - Secured",
        "group": "TRADE_RECEIVABLES",
        "type": "CONTROL",
        "control_type": "CUSTOMER",
    },
    {
        "code": "1202",
        "name": "Trade Receivables - Unsecured",
        "group": "TRADE_RECEIVABLES",
        "type": "CONTROL",
        "control_type": "CUSTOMER",
    },
    # Loans & Advances (NBFC specific)
    {
        "code": "1301",
        "name": "Loans to Customers",
        "group": "LOANS_ADVANCES",
        "type": "CONTROL",
        "control_type": "CUSTOMER",
    },
    {
        "code": "1302",
        "name": "Staff Loans and Advances",
        "group": "LOANS_ADVANCES",
        "type": "LEDGER",
    },
    {"code": "1303", "name": "Security Deposits", "group": "LOANS_ADVANCES", "type": "LEDGER"},
    {"code": "1304", "name": "Advances to Suppliers", "group": "LOANS_ADVANCES", "type": "LEDGER"},
    # Other Current Assets
    {"code": "1401", "name": "Prepaid Expenses", "group": "OTHER_CURR_ASSETS", "type": "LEDGER"},
    {
        "code": "1402",
        "name": "Input GST Receivable",
        "group": "OTHER_CURR_ASSETS",
        "type": "LEDGER",
    },
    {"code": "1403", "name": "TDS Receivable", "group": "OTHER_CURR_ASSETS", "type": "LEDGER"},
    {
        "code": "1404",
        "name": "Interest Accrued but Not Due",
        "group": "OTHER_CURR_ASSETS",
        "type": "LEDGER",
    },
    # Fixed Assets
    {"code": "1501", "name": "Land", "group": "PPE", "type": "LEDGER"},
    {"code": "1502", "name": "Buildings", "group": "PPE", "type": "LEDGER"},
    {"code": "1503", "name": "Furniture and Fixtures", "group": "PPE", "type": "LEDGER"},
    {"code": "1504", "name": "Office Equipment", "group": "PPE", "type": "LEDGER"},
    {"code": "1505", "name": "Computers and Laptops", "group": "PPE", "type": "LEDGER"},
    {"code": "1506", "name": "Vehicles", "group": "PPE", "type": "LEDGER"},
    {
        "code": "1507",
        "name": "Accumulated Depreciation",
        "group": "PPE",
        "type": "LEDGER",
        "opening": 0,
        "balance_type": "CREDIT",
    },
    # Intangible Assets
    {"code": "1601", "name": "Software Licenses", "group": "INTANGIBLE", "type": "LEDGER"},
    {"code": "1602", "name": "Goodwill", "group": "INTANGIBLE", "type": "LEDGER"},
    # Trade Payables
    {
        "code": "2001",
        "name": "Trade Payables - MSME",
        "group": "TRADE_PAYABLES",
        "type": "CONTROL",
        "control_type": "VENDOR",
    },
    {
        "code": "2002",
        "name": "Trade Payables - Others",
        "group": "TRADE_PAYABLES",
        "type": "CONTROL",
        "control_type": "VENDOR",
    },
    # Other Financial Liabilities
    {"code": "2101", "name": "Salaries Payable", "group": "OTHER_FIN_LIAB", "type": "LEDGER"},
    {"code": "2102", "name": "Expenses Payable", "group": "OTHER_FIN_LIAB", "type": "LEDGER"},
    {
        "code": "2103",
        "name": "Security Deposits Received",
        "group": "OTHER_FIN_LIAB",
        "type": "LEDGER",
    },
    {
        "code": "2104",
        "name": "Borrower Receipt Suspense",
        "group": "OTHER_FIN_LIAB",
        "type": "LEDGER",
    },
    # Statutory Dues
    {"code": "2201", "name": "TDS Payable", "group": "STATUTORY_DUES", "type": "LEDGER"},
    {"code": "2202", "name": "GST Payable", "group": "STATUTORY_DUES", "type": "LEDGER"},
    {
        "code": "2203",
        "name": "Professional Tax Payable",
        "group": "STATUTORY_DUES",
        "type": "LEDGER",
    },
    {"code": "2204", "name": "PF Payable", "group": "STATUTORY_DUES", "type": "LEDGER"},
    {"code": "2205", "name": "ESI Payable", "group": "STATUTORY_DUES", "type": "LEDGER"},
    # Duties and Taxes
    {"code": "2301", "name": "CGST Payable", "group": "DUTIES_TAXES", "type": "LEDGER"},
    {"code": "2302", "name": "SGST Payable", "group": "DUTIES_TAXES", "type": "LEDGER"},
    {"code": "2303", "name": "IGST Payable", "group": "DUTIES_TAXES", "type": "LEDGER"},
    {"code": "2304", "name": "Income Tax Payable", "group": "DUTIES_TAXES", "type": "LEDGER"},
    # Borrowings
    {"code": "2401", "name": "Bank Overdraft", "group": "BORROWINGS_C", "type": "LEDGER"},
    {"code": "2402", "name": "Short Term Loans", "group": "BORROWINGS_C", "type": "LEDGER"},
    # Provisions
    {"code": "2501", "name": "Provision for Gratuity", "group": "PROVISIONS_C", "type": "LEDGER"},
    {
        "code": "2502",
        "name": "Provision for Leave Encashment",
        "group": "PROVISIONS_C",
        "type": "LEDGER",
    },
    {"code": "2503", "name": "Provision for Bad Debts", "group": "PROVISIONS_C", "type": "LEDGER"},
    # Share Capital
    {
        "code": "3001",
        "name": "Equity Share Capital",
        "group": "SHARE_CAPITAL",
        "type": "LEDGER",
        "opening": 10000000,
        "balance_type": "CREDIT",
    },
    {
        "code": "3002",
        "name": "Preference Share Capital",
        "group": "SHARE_CAPITAL",
        "type": "LEDGER",
    },
    # Reserves
    {
        "code": "3101",
        "name": "Securities Premium Account",
        "group": "SECURITIES_PREMIUM",
        "type": "LEDGER",
    },
    {"code": "3102", "name": "General Reserve", "group": "GENERAL_RESERVE", "type": "LEDGER"},
    {
        "code": "3103",
        "name": "Profit and Loss Account",
        "group": "RETAINED_EARNINGS",
        "type": "LEDGER",
        "opening": 2500000,
        "balance_type": "CREDIT",
    },
    {
        "code": "3104",
        "name": "Statutory Reserve (RBI)",
        "group": "RETAINED_EARNINGS",
        "type": "LEDGER",
    },
    # Income Accounts
    {"code": "4001", "name": "Interest on Loans", "group": "INTEREST_INCOME", "type": "LEDGER"},
    {"code": "4002", "name": "Interest on FD", "group": "INTEREST_INCOME", "type": "LEDGER"},
    {
        "code": "4003",
        "name": "Interest on Savings Account",
        "group": "INTEREST_INCOME",
        "type": "LEDGER",
    },
    {"code": "4101", "name": "Processing Fee Income", "group": "FEE_COMMISSION", "type": "LEDGER"},
    {"code": "4102", "name": "Documentation Charges", "group": "FEE_COMMISSION", "type": "LEDGER"},
    {"code": "4103", "name": "Late Payment Charges", "group": "FEE_COMMISSION", "type": "LEDGER"},
    {"code": "4104", "name": "Foreclosure Charges", "group": "FEE_COMMISSION", "type": "LEDGER"},
    {"code": "4201", "name": "Dividend Received", "group": "DIVIDEND_INCOME", "type": "LEDGER"},
    {"code": "4202", "name": "Rent Received", "group": "RENTAL_INCOME", "type": "LEDGER"},
    {"code": "4203", "name": "Other Income", "group": "MISC_INCOME", "type": "LEDGER"},
    # Expense Accounts
    {"code": "5001", "name": "Interest on Borrowings", "group": "INTEREST_EXP", "type": "LEDGER"},
    {"code": "5002", "name": "Bank Interest Expense", "group": "INTEREST_EXP", "type": "LEDGER"},
    {
        "code": "5003",
        "name": "Processing Fee Expense",
        "group": "OTHER_BORROWING_COSTS",
        "type": "LEDGER",
    },
    {"code": "5101", "name": "Provision for NPA", "group": "IMPAIRMENT", "type": "LEDGER"},
    {"code": "5102", "name": "Bad Debts Written Off", "group": "IMPAIRMENT", "type": "LEDGER"},
    {"code": "5201", "name": "Salaries and Wages", "group": "SALARIES_WAGES", "type": "LEDGER"},
    {
        "code": "5202",
        "name": "Directors' Remuneration",
        "group": "SALARIES_WAGES",
        "type": "LEDGER",
    },
    {"code": "5203", "name": "Bonus", "group": "SALARIES_WAGES", "type": "LEDGER"},
    {"code": "5204", "name": "PF Contribution", "group": "CONTRIBUTION_PF", "type": "LEDGER"},
    {"code": "5205", "name": "ESI Contribution", "group": "CONTRIBUTION_PF", "type": "LEDGER"},
    {"code": "5206", "name": "Staff Welfare", "group": "STAFF_WELFARE", "type": "LEDGER"},
    {"code": "5207", "name": "Gratuity Expense", "group": "GRATUITY_EXP", "type": "LEDGER"},
    {"code": "5301", "name": "Depreciation - Buildings", "group": "DEPRECIATION", "type": "LEDGER"},
    {"code": "5302", "name": "Depreciation - Furniture", "group": "DEPRECIATION", "type": "LEDGER"},
    {"code": "5303", "name": "Depreciation - Equipment", "group": "DEPRECIATION", "type": "LEDGER"},
    {"code": "5304", "name": "Depreciation - Vehicles", "group": "DEPRECIATION", "type": "LEDGER"},
    {"code": "5305", "name": "Amortisation - Software", "group": "DEPRECIATION", "type": "LEDGER"},
    {"code": "5401", "name": "Office Rent", "group": "RENT_EXP", "type": "LEDGER"},
    {"code": "5402", "name": "Repairs - Building", "group": "REPAIRS_MAINT", "type": "LEDGER"},
    {"code": "5403", "name": "Repairs - Machinery", "group": "REPAIRS_MAINT", "type": "LEDGER"},
    {"code": "5404", "name": "Insurance Premium", "group": "INSURANCE_EXP", "type": "LEDGER"},
    {"code": "5405", "name": "Legal Fees", "group": "LEGAL_PROF", "type": "LEDGER"},
    {"code": "5406", "name": "Professional Fees", "group": "LEGAL_PROF", "type": "LEDGER"},
    {"code": "5407", "name": "Consultancy Charges", "group": "LEGAL_PROF", "type": "LEDGER"},
    {"code": "5408", "name": "Travelling Expenses", "group": "TRAVEL_CONV", "type": "LEDGER"},
    {"code": "5409", "name": "Conveyance Expenses", "group": "TRAVEL_CONV", "type": "LEDGER"},
    {"code": "5410", "name": "Telephone Expenses", "group": "COMM_EXP", "type": "LEDGER"},
    {"code": "5411", "name": "Internet Charges", "group": "COMM_EXP", "type": "LEDGER"},
    {"code": "5412", "name": "Postage and Courier", "group": "COMM_EXP", "type": "LEDGER"},
    {"code": "5413", "name": "Printing and Stationery", "group": "PRINTING_STAT", "type": "LEDGER"},
    {"code": "5414", "name": "Audit Fees", "group": "AUDIT_FEES", "type": "LEDGER"},
    {"code": "5415", "name": "Tax Audit Fees", "group": "AUDIT_FEES", "type": "LEDGER"},
    {"code": "5416", "name": "Bank Charges", "group": "BANK_CHARGES", "type": "LEDGER"},
    {"code": "5417", "name": "GST Expense", "group": "GST_EXP", "type": "LEDGER"},
    {"code": "5418", "name": "Miscellaneous Expenses", "group": "MISC_EXP", "type": "LEDGER"},
    {"code": "5419", "name": "ROC Filing Fees", "group": "LEGAL_PROF", "type": "LEDGER"},
    {"code": "5420", "name": "Advertisement Expenses", "group": "MISC_EXP", "type": "LEDGER"},
    {"code": "5421", "name": "Business Promotion", "group": "MISC_EXP", "type": "LEDGER"},
]

# Voucher Types (Standard Indian Accounting)
VOUCHER_TYPES = [
    {
        "code": "JV",
        "name": "Journal Voucher",
        "class": "JOURNAL",
        "prefix": "JV/",
        "auto": True,
        "approval": True,
        "levels": 1,
    },
    {
        "code": "PV",
        "name": "Payment Voucher",
        "class": "PAYMENT",
        "prefix": "PV/",
        "auto": True,
        "approval": True,
        "levels": 1,
    },
    {
        "code": "RV",
        "name": "Receipt Voucher",
        "class": "RECEIPT",
        "prefix": "RV/",
        "auto": True,
        "approval": True,
        "levels": 1,
    },
    {
        "code": "CV",
        "name": "Contra Voucher",
        "class": "CONTRA",
        "prefix": "CV/",
        "auto": True,
        "approval": False,
        "levels": 0,
    },
    {
        "code": "SV",
        "name": "Sales Voucher",
        "class": "SALES",
        "prefix": "SV/",
        "auto": True,
        "approval": True,
        "levels": 1,
    },
    {
        "code": "PU",
        "name": "Purchase Voucher",
        "class": "PURCHASE",
        "prefix": "PU/",
        "auto": True,
        "approval": True,
        "levels": 1,
    },
    {
        "code": "DN",
        "name": "Debit Note",
        "class": "DEBIT_NOTE",
        "prefix": "DN/",
        "auto": True,
        "approval": True,
        "levels": 1,
    },
    {
        "code": "CN",
        "name": "Credit Note",
        "class": "CREDIT_NOTE",
        "prefix": "CN/",
        "auto": True,
        "approval": True,
        "levels": 1,
    },
]

# =====================================================
# GST SEED DATA - Indian GST Rates
# =====================================================

GST_RATES = [
    {
        "code": "GST0",
        "name": "Exempt / NIL Rated",
        "rate": 0,
        "cgst": 0,
        "sgst": 0,
        "igst": 0,
        "cess": 0,
        "description": "Exempt or NIL rated goods and services",
    },
    {
        "code": "GST5",
        "name": "GST 5%",
        "rate": 5,
        "cgst": 2.5,
        "sgst": 2.5,
        "igst": 5,
        "cess": 0,
        "description": "Essential items, basic services",
    },
    {
        "code": "GST12",
        "name": "GST 12%",
        "rate": 12,
        "cgst": 6,
        "sgst": 6,
        "igst": 12,
        "cess": 0,
        "description": "Standard goods and services",
    },
    {
        "code": "GST18",
        "name": "GST 18%",
        "rate": 18,
        "cgst": 9,
        "sgst": 9,
        "igst": 18,
        "cess": 0,
        "description": "Most goods and services (default)",
    },
    {
        "code": "GST28",
        "name": "GST 28%",
        "rate": 28,
        "cgst": 14,
        "sgst": 14,
        "igst": 28,
        "cess": 0,
        "description": "Luxury goods, sin goods",
    },
    {
        "code": "GST28C1",
        "name": "GST 28% + 1% Cess",
        "rate": 28,
        "cgst": 14,
        "sgst": 14,
        "igst": 28,
        "cess": 1,
        "description": "Small cars, SUVs cess",
    },
    {
        "code": "GST28C3",
        "name": "GST 28% + 3% Cess",
        "rate": 28,
        "cgst": 14,
        "sgst": 14,
        "igst": 28,
        "cess": 3,
        "description": "Mid-size cars cess",
    },
    {
        "code": "GST28C15",
        "name": "GST 28% + 15% Cess",
        "rate": 28,
        "cgst": 14,
        "sgst": 14,
        "igst": 28,
        "cess": 15,
        "description": "Large cars cess",
    },
    {
        "code": "GST28C22",
        "name": "GST 28% + 22% Cess",
        "rate": 28,
        "cgst": 14,
        "sgst": 14,
        "igst": 28,
        "cess": 22,
        "description": "Luxury SUVs cess",
    },
]

# Sample HSN/SAC Codes
HSN_SAC_CODES = [
    # Financial Services (SAC)
    {
        "code": "997119",
        "description": "Other financial services except insurance and pension funding services",
        "type": "SAC",
        "gst_rate": "GST18",
    },
    {
        "code": "997112",
        "description": "Credit granting services",
        "type": "SAC",
        "gst_rate": "GST18",
    },
    {
        "code": "997113",
        "description": "Financial leasing services",
        "type": "SAC",
        "gst_rate": "GST18",
    },
    {
        "code": "997152",
        "description": "Loan brokerage services",
        "type": "SAC",
        "gst_rate": "GST18",
    },
    {
        "code": "997159",
        "description": "Other services auxiliary to financial services",
        "type": "SAC",
        "gst_rate": "GST18",
    },
    {
        "code": "997161",
        "description": "Services of holding financial assets",
        "type": "SAC",
        "gst_rate": "GST18",
    },
    # Professional Services (SAC)
    {
        "code": "998211",
        "description": "Legal advisory and representation services",
        "type": "SAC",
        "gst_rate": "GST18",
    },
    {
        "code": "998212",
        "description": "Legal documentation and certification services",
        "type": "SAC",
        "gst_rate": "GST18",
    },
    {
        "code": "998221",
        "description": "Financial auditing services",
        "type": "SAC",
        "gst_rate": "GST18",
    },
    {
        "code": "998222",
        "description": "Accounting and book keeping services",
        "type": "SAC",
        "gst_rate": "GST18",
    },
    {
        "code": "998231",
        "description": "Corporate tax consulting and preparation services",
        "type": "SAC",
        "gst_rate": "GST18",
    },
    {
        "code": "998311",
        "description": "Management consulting and management services",
        "type": "SAC",
        "gst_rate": "GST18",
    },
    {
        "code": "998312",
        "description": "Business consulting services",
        "type": "SAC",
        "gst_rate": "GST18",
    },
    # IT Services (SAC)
    {
        "code": "998313",
        "description": "Information technology consulting and support services",
        "type": "SAC",
        "gst_rate": "GST18",
    },
    {
        "code": "998314",
        "description": "Information technology design and development services",
        "type": "SAC",
        "gst_rate": "GST18",
    },
    {
        "code": "998315",
        "description": "Hosting and information technology infrastructure provisioning services",
        "type": "SAC",
        "gst_rate": "GST18",
    },
    {
        "code": "998316",
        "description": "IT infrastructure and network management services",
        "type": "SAC",
        "gst_rate": "GST18",
    },
    # Rental Services (SAC)
    {
        "code": "997212",
        "description": (
            "Rental or leasing services involving own or leased non-residential property"
        ),
        "type": "SAC",
        "gst_rate": "GST18",
    },
    # Common Goods (HSN)
    {
        "code": "8471",
        "description": "Computers and Computer Parts",
        "type": "HSN",
        "gst_rate": "GST18",
    },
    {
        "code": "8443",
        "description": "Printing machinery, printers, copiers",
        "type": "HSN",
        "gst_rate": "GST18",
    },
    {"code": "9403", "description": "Office Furniture", "type": "HSN", "gst_rate": "GST18"},
    {
        "code": "8517",
        "description": "Telephones including smartphones",
        "type": "HSN",
        "gst_rate": "GST18",
    },
    {"code": "4820", "description": "Paper and Stationery", "type": "HSN", "gst_rate": "GST12"},
    {"code": "4901", "description": "Printed books, newspapers", "type": "HSN", "gst_rate": "GST0"},
]

# =====================================================
# TDS SEED DATA - Indian TDS Sections
# =====================================================

TDS_SECTIONS = [
    # Salary & Payments to Employees
    {
        "code": "192",
        "name": "Salaries",
        "description": "TDS on salary payments",
        "rate_ind": 0,
        "rate_comp": 0,
        "rate_no_pan": 20,
        "threshold_single": 0,
        "threshold_annual": 0,
        "return_form": "24Q",
        "nature_code": "1",
    },
    # Contractors
    {
        "code": "194C",
        "name": "Contractors (Single)",
        "description": "Payment to contractors - single transaction",
        "rate_ind": 1,
        "rate_comp": 2,
        "rate_no_pan": 20,
        "threshold_single": 30000,
        "threshold_annual": 100000,
        "return_form": "26Q",
        "nature_code": "C",
    },
    {
        "code": "194C-A",
        "name": "Contractors (Aggregate)",
        "description": "Payment to contractors - aggregate in year",
        "rate_ind": 1,
        "rate_comp": 2,
        "rate_no_pan": 20,
        "threshold_single": 0,
        "threshold_annual": 100000,
        "return_form": "26Q",
        "nature_code": "C",
    },
    # Professional & Technical
    {
        "code": "194J",
        "name": "Professional/Technical Services",
        "description": "Fees for professional or technical services",
        "rate_ind": 10,
        "rate_comp": 10,
        "rate_no_pan": 20,
        "threshold_single": 30000,
        "threshold_annual": 30000,
        "return_form": "26Q",
        "nature_code": "J",
    },
    {
        "code": "194J-B",
        "name": "Technical Services (Reduced)",
        "description": "Technical services with reduced rate",
        "rate_ind": 2,
        "rate_comp": 2,
        "rate_no_pan": 20,
        "threshold_single": 30000,
        "threshold_annual": 30000,
        "return_form": "26Q",
        "nature_code": "JB",
    },
    # Rent
    {
        "code": "194I-A",
        "name": "Rent - Plant & Machinery",
        "description": "Rent on plant and machinery",
        "rate_ind": 2,
        "rate_comp": 2,
        "rate_no_pan": 20,
        "threshold_single": 0,
        "threshold_annual": 240000,
        "return_form": "26Q",
        "nature_code": "IA",
    },
    {
        "code": "194I-B",
        "name": "Rent - Land/Building/Furniture",
        "description": "Rent on land, building, furniture",
        "rate_ind": 10,
        "rate_comp": 10,
        "rate_no_pan": 20,
        "threshold_single": 0,
        "threshold_annual": 240000,
        "return_form": "26Q",
        "nature_code": "IB",
    },
    # Commission & Brokerage
    {
        "code": "194H",
        "name": "Commission/Brokerage",
        "description": "Commission or brokerage payments",
        "rate_ind": 5,
        "rate_comp": 5,
        "rate_no_pan": 20,
        "threshold_single": 0,
        "threshold_annual": 15000,
        "return_form": "26Q",
        "nature_code": "H",
    },
    # Interest
    {
        "code": "194A",
        "name": "Interest (Other than Securities)",
        "description": "Interest other than interest on securities",
        "rate_ind": 10,
        "rate_comp": 10,
        "rate_no_pan": 20,
        "threshold_single": 0,
        "threshold_annual": 40000,
        "return_form": "26Q",
        "nature_code": "A",
    },
    {
        "code": "194A-S",
        "name": "Interest (Senior Citizen)",
        "description": "Interest to senior citizens",
        "rate_ind": 10,
        "rate_comp": 10,
        "rate_no_pan": 20,
        "threshold_single": 0,
        "threshold_annual": 50000,
        "return_form": "26Q",
        "nature_code": "AS",
    },
    # Dividend
    {
        "code": "194",
        "name": "Dividend",
        "description": "Dividend payments",
        "rate_ind": 10,
        "rate_comp": 10,
        "rate_no_pan": 20,
        "threshold_single": 0,
        "threshold_annual": 5000,
        "return_form": "26Q",
        "nature_code": "D",
    },
    # Payments to NRIs (Form 27Q)
    {
        "code": "195",
        "name": "Payments to NRI",
        "description": "Any payment to non-resident",
        "rate_ind": 0,
        "rate_comp": 0,
        "rate_no_pan": 20,
        "threshold_single": 0,
        "threshold_annual": 0,
        "return_form": "27Q",
        "nature_code": "NR",
    },
    # E-Commerce
    {
        "code": "194O",
        "name": "E-Commerce Operator",
        "description": "Payment by e-commerce operator",
        "rate_ind": 1,
        "rate_comp": 1,
        "rate_no_pan": 20,
        "threshold_single": 0,
        "threshold_annual": 500000,
        "return_form": "26Q",
        "nature_code": "O",
    },
    # TCS Sections
    {
        "code": "206C-1H",
        "name": "TCS - Sale of Goods",
        "description": "TCS on sale of goods exceeding 50L",
        "rate_ind": 0.1,
        "rate_comp": 0.1,
        "rate_no_pan": 1,
        "threshold_single": 0,
        "threshold_annual": 5000000,
        "return_form": "27EQ",
        "nature_code": "TCS1H",
        "is_tcs": True,
    },
    {
        "code": "206C-1G",
        "name": "TCS - Foreign Remittance",
        "description": "TCS on foreign remittance under LRS",
        "rate_ind": 5,
        "rate_comp": 5,
        "rate_no_pan": 10,
        "threshold_single": 0,
        "threshold_annual": 700000,
        "return_form": "27EQ",
        "nature_code": "TCS1G",
        "is_tcs": True,
    },
]

# =====================================================
# PAYMENT TERMS SEED DATA
# =====================================================

PAYMENT_TERMS = [
    {
        "code": "IMMEDIATE",
        "name": "Immediate / Cash",
        "description": "Payment due immediately on invoice",
        "days": 0,
        "discount_days": 0,
        "discount_percent": 0,
    },
    {
        "code": "COD",
        "name": "Cash on Delivery",
        "description": "Payment on delivery of goods",
        "days": 0,
        "discount_days": 0,
        "discount_percent": 0,
    },
    {
        "code": "NET7",
        "name": "Net 7 Days",
        "description": "Payment due within 7 days",
        "days": 7,
        "discount_days": 0,
        "discount_percent": 0,
    },
    {
        "code": "NET15",
        "name": "Net 15 Days",
        "description": "Payment due within 15 days",
        "days": 15,
        "discount_days": 0,
        "discount_percent": 0,
    },
    {
        "code": "NET30",
        "name": "Net 30 Days",
        "description": "Payment due within 30 days",
        "days": 30,
        "discount_days": 0,
        "discount_percent": 0,
    },
    {
        "code": "NET45",
        "name": "Net 45 Days",
        "description": "Payment due within 45 days",
        "days": 45,
        "discount_days": 0,
        "discount_percent": 0,
    },
    {
        "code": "NET60",
        "name": "Net 60 Days",
        "description": "Payment due within 60 days",
        "days": 60,
        "discount_days": 0,
        "discount_percent": 0,
    },
    {
        "code": "NET90",
        "name": "Net 90 Days",
        "description": "Payment due within 90 days",
        "days": 90,
        "discount_days": 0,
        "discount_percent": 0,
    },
    {
        "code": "2/10NET30",
        "name": "2% 10 Net 30",
        "description": "2% discount if paid within 10 days, net due in 30 days",
        "days": 30,
        "discount_days": 10,
        "discount_percent": 2,
    },
    {
        "code": "1/10NET30",
        "name": "1% 10 Net 30",
        "description": "1% discount if paid within 10 days, net due in 30 days",
        "days": 30,
        "discount_days": 10,
        "discount_percent": 1,
    },
    {
        "code": "EOM",
        "name": "End of Month",
        "description": "Payment due at end of month",
        "days": 30,
        "discount_days": 0,
        "discount_percent": 0,
    },
    {
        "code": "MFI",
        "name": "Month Following Invoice",
        "description": "Payment due on 15th of month following invoice",
        "days": 45,
        "discount_days": 0,
        "discount_percent": 0,
    },
]

# =====================================================
# LENDING MASTER SEED DATA - CORPORATE NBFC DEFAULTS
# =====================================================

INTEREST_RATES = [
    {
        "code": "SMFCL_BR",
        "name": "SMFCL Base Rate",
        "description": "Default internal base rate for floating corporate/project loans",
        "rate_type": "BASE_RATE",
        "benchmark_name": "SMFCL Board Approved Base Rate",
        "current_rate": 8.25,
        "reset_frequency": RateResetFrequency.QUARTERLY,
    },
    {
        "code": "REPO_LINKED",
        "name": "Repo Linked Lending Rate",
        "description": "External benchmark rate used for selected infrastructure loans",
        "rate_type": "EXTERNAL_BENCHMARK",
        "benchmark_name": "RBI Repo Rate",
        "current_rate": 6.50,
        "reset_frequency": RateResetFrequency.QUARTERLY,
    },
]

LOAN_PRODUCTS = [
    {
        "code": "CORP_PROJECT_FIN",
        "name": "Corporate Project Finance",
        "description": "Multi-tranche project finance for institutional borrowers",
        "category": ProductCategory.PROJECT_FINANCE,
        "min_amount": 50000000,
        "max_amount": 5000000000,
        "default_amount": 250000000,
        "min_tenure_months": 24,
        "max_tenure_months": 180,
        "default_tenure_months": 84,
        "max_moratorium_months": 24,
        "default_spread_bps": 275,
        "default_repayment_frequency": RepaymentFrequency.QUARTERLY,
        "default_repayment_mode": RepaymentMode.STRUCTURED,
        "disbursement_type": "TRANCHE_BASED",
        "max_tranches": 6,
        "min_collateral_coverage": 125,
        "min_dscr": 1.20,
    },
    {
        "code": "CORP_TERM_LOAN",
        "name": "Corporate Term Loan",
        "description": "Standard secured corporate term loan with monthly or quarterly repayment",
        "category": ProductCategory.TERM_LOAN,
        "min_amount": 10000000,
        "max_amount": 1000000000,
        "default_amount": 100000000,
        "min_tenure_months": 12,
        "max_tenure_months": 120,
        "default_tenure_months": 60,
        "max_moratorium_months": 12,
        "default_spread_bps": 250,
        "default_repayment_frequency": RepaymentFrequency.MONTHLY,
        "default_repayment_mode": RepaymentMode.EMI,
        "disbursement_type": "MULTIPLE",
        "max_tranches": 3,
        "min_collateral_coverage": 110,
        "min_dscr": 1.10,
    },
    {
        "code": "INFRA_BRIDGE_LOAN",
        "name": "Infrastructure Bridge Loan",
        "description": "Short-tenor demand/bridge facility against approved project receivables",
        "category": ProductCategory.DEMAND_LOAN,
        "min_amount": 10000000,
        "max_amount": 750000000,
        "default_amount": 75000000,
        "min_tenure_months": 3,
        "max_tenure_months": 36,
        "default_tenure_months": 18,
        "max_moratorium_months": 6,
        "default_spread_bps": 325,
        "default_repayment_frequency": RepaymentFrequency.QUARTERLY,
        "default_repayment_mode": RepaymentMode.BULLET,
        "disbursement_type": "SINGLE",
        "max_tranches": 1,
        "min_collateral_coverage": 100,
        "min_dscr": 1.00,
    },
]

FEE_MASTERS = [
    {
        "code": "PROCESSING_FEE",
        "name": "Processing Fee",
        "fee_type": FeeType.PROCESSING,
        "calculation_type": FeeCalculationType.PERCENTAGE,
        "default_rate": 0.50,
        "min_amount": 50000,
        "max_amount": 2500000,
        "collection_stage": FeeCollectionStage.SANCTION,
        "is_taxable": True,
    },
    {
        "code": "DOCUMENTATION_FEE",
        "name": "Documentation Fee",
        "fee_type": FeeType.DOCUMENTATION,
        "calculation_type": FeeCalculationType.FLAT,
        "default_amount": 100000,
        "collection_stage": FeeCollectionStage.DISBURSEMENT,
        "is_taxable": True,
    },
    {
        "code": "PREPAYMENT_FEE",
        "name": "Prepayment Fee",
        "fee_type": FeeType.PREPAYMENT,
        "calculation_type": FeeCalculationType.PERCENTAGE,
        "default_rate": 1.00,
        "collection_stage": FeeCollectionStage.PREPAYMENT,
        "is_taxable": True,
    },
]

DOCUMENT_CHECKLIST = [
    (
        "KYC_PAN",
        "PAN and constitutional documents",
        DocumentCategory.KYC,
        DocumentStage.APPLICATION,
        True,
    ),
    (
        "BOARD_RESOLUTION",
        "Board resolution / borrowing authority",
        DocumentCategory.LEGAL,
        DocumentStage.SANCTION,
        True,
    ),
    (
        "AUDITED_FINANCIALS",
        "Audited financial statements - 3 years",
        DocumentCategory.FINANCIAL,
        DocumentStage.APPRAISAL,
        True,
    ),
    (
        "PROJECT_DPR",
        "Detailed project report and cost estimates",
        DocumentCategory.PROJECT,
        DocumentStage.APPRAISAL,
        True,
    ),
    (
        "SECURITY_TITLE",
        "Security title and valuation documents",
        DocumentCategory.SECURITY,
        DocumentStage.PRE_DISBURSEMENT,
        True,
    ),
    (
        "INSURANCE_POLICY",
        "Insurance policy for charged assets",
        DocumentCategory.INSURANCE,
        DocumentStage.POST_DISBURSEMENT,
        False,
    ),
]

APPROVAL_CHECKLIST_ITEMS = [
    (
        "KYC_COMPLETE",
        "Borrower KYC and beneficial ownership verified",
        ChecklistItemCategory.KYC,
        True,
        True,
    ),
    (
        "FINANCIAL_APPRAISAL",
        "Financial appraisal and DSCR assessment completed",
        ChecklistItemCategory.OTHER,
        True,
        True,
    ),
    (
        "TECHNICAL_APPRAISAL",
        "Technical/project appraisal completed",
        ChecklistItemCategory.OTHER,
        True,
        True,
    ),
    (
        "SECURITY_PERFECTED",
        "Security creation and charge registration validated",
        ChecklistItemCategory.LEGAL,
        True,
        True,
    ),
    (
        "LEGAL_VETTING",
        "Legal vetting and documentation clearance obtained",
        ChecklistItemCategory.LEGAL,
        True,
        True,
    ),
    (
        "BOARD_APPROVAL",
        "Delegated authority / board approval captured",
        ChecklistItemCategory.COMPLIANCE,
        True,
        True,
    ),
]

SOURCE_LENDERS = [
    {
        "lender_code": "SBI_TERM",
        "lender_name": "State Bank of India",
        "lender_type": LenderType.BANK.value,
        "status": LenderStatus.ACTIVE.value,
        "contact_person": "Relationship Manager",
        "contact_email": "treasury.rm@sbi.example",
        "contact_phone": "02240001000",
        "external_rating": "AAA",
        "rating_agency": "CRISIL",
        "total_sanction_limit": 1500000000,
        "available_limit": 1500000000,
    },
    {
        "lender_code": "NABARD_LINE",
        "lender_name": "NABARD Refinance Line",
        "lender_type": LenderType.DFI.value,
        "status": LenderStatus.ACTIVE.value,
        "contact_person": "Institutional Finance Desk",
        "contact_email": "refinance@nabard.example",
        "contact_phone": "02240002000",
        "external_rating": "AAA",
        "rating_agency": "India Ratings",
        "total_sanction_limit": 1000000000,
        "available_limit": 1000000000,
    },
]

LEAVE_TYPES = [
    ("EL", "Earned Leave", LeaveCategory.EARNED, 18, True, 45, True, 15, False, None, 0),
    ("CL", "Casual Leave", LeaveCategory.CASUAL, 8, False, None, False, None, False, None, 1),
    ("SL", "Sick Leave", LeaveCategory.SICK, 10, False, None, False, None, True, 2, 2),
    (
        "CO",
        "Compensatory Off",
        LeaveCategory.COMPENSATORY,
        0,
        False,
        None,
        False,
        None,
        False,
        None,
        3,
    ),
    ("LOP", "Loss of Pay", LeaveCategory.LOP, 0, False, None, False, None, False, None, 4),
    ("ML", "Maternity Leave", LeaveCategory.MATERNITY, 182, False, None, False, None, True, 1, 5),
    (
        "PL",
        "Paternity Leave",
        LeaveCategory.PATERNITY,
        15,
        False,
        None,
        False,
        None,
        False,
        None,
        6,
    ),
]

SHIFT_MASTERS = [
    (
        "GEN",
        "General Shift",
        ShiftType.GENERAL,
        time(9, 30),
        time(18, 30),
        time(13, 30),
        time(14, 30),
        60,
    ),
    (
        "FLEX",
        "Flexible Shift",
        ShiftType.FLEXIBLE,
        time(10, 0),
        time(19, 0),
        time(14, 0),
        time(15, 0),
        60,
    ),
    (
        "MORN",
        "Morning Operations Shift",
        ShiftType.MORNING,
        time(7, 0),
        time(15, 30),
        time(11, 0),
        time(11, 30),
        30,
    ),
]

HOLIDAYS_2026 = [
    (date(2026, 1, 26), "Republic Day", HolidayType.NATIONAL),
    (date(2026, 5, 1), "Maharashtra Day", HolidayType.STATE),
    (date(2026, 8, 15), "Independence Day", HolidayType.NATIONAL),
    (date(2026, 10, 2), "Gandhi Jayanti", HolidayType.NATIONAL),
    (date(2026, 12, 25), "Christmas", HolidayType.COMPANY),
]

SALARY_COMPONENTS = [
    (
        "BASIC",
        "Basic Salary",
        ComponentType.EARNING,
        ComponentCategory.BASIC,
        CalculationType.PERCENTAGE_OF_CTC,
        40,
        True,
        True,
        True,
        True,
    ),
    (
        "HRA",
        "House Rent Allowance",
        ComponentType.EARNING,
        ComponentCategory.ALLOWANCE,
        CalculationType.PERCENTAGE_OF_BASIC,
        50,
        True,
        False,
        False,
        False,
    ),
    (
        "CONV",
        "Conveyance Allowance",
        ComponentType.EARNING,
        ComponentCategory.ALLOWANCE,
        CalculationType.FIXED,
        1600,
        True,
        False,
        False,
        False,
    ),
    (
        "SPL",
        "Special Allowance",
        ComponentType.EARNING,
        ComponentCategory.ALLOWANCE,
        CalculationType.FORMULA,
        None,
        True,
        False,
        False,
        False,
    ),
    (
        "PF_EMP",
        "Provident Fund - Employee",
        ComponentType.DEDUCTION,
        ComponentCategory.STATUTORY,
        CalculationType.PERCENTAGE_OF_BASIC,
        12,
        False,
        False,
        False,
        False,
    ),
    (
        "ESI_EMP",
        "ESI - Employee",
        ComponentType.DEDUCTION,
        ComponentCategory.STATUTORY,
        CalculationType.PERCENTAGE_OF_GROSS,
        Decimal("0.75"),
        False,
        False,
        False,
        False,
    ),
    (
        "PT",
        "Professional Tax",
        ComponentType.DEDUCTION,
        ComponentCategory.STATUTORY,
        CalculationType.FIXED,
        200,
        False,
        False,
        False,
        False,
    ),
    (
        "TDS_SAL",
        "Salary TDS",
        ComponentType.DEDUCTION,
        ComponentCategory.STATUTORY,
        CalculationType.FIXED,
        0,
        False,
        False,
        False,
        False,
    ),
]

FIXED_ASSET_CATEGORIES = [
    (
        "LAND",
        "Land",
        AssetType.TANGIBLE,
        DepreciationMethod.NO_DEPRECIATION,
        99,
        0,
        0,
        0,
        False,
        False,
    ),
    (
        "BLDG",
        "Office Buildings",
        AssetType.TANGIBLE,
        DepreciationMethod.SLM,
        30,
        5,
        Decimal("3.17"),
        10,
        True,
        True,
    ),
    (
        "COMP",
        "Computers and IT Equipment",
        AssetType.TANGIBLE,
        DepreciationMethod.WDV,
        3,
        5,
        Decimal("31.67"),
        40,
        True,
        True,
    ),
    (
        "FURN",
        "Furniture and Fixtures",
        AssetType.TANGIBLE,
        DepreciationMethod.SLM,
        10,
        5,
        Decimal("9.50"),
        10,
        False,
        False,
    ),
    (
        "VEH",
        "Vehicles",
        AssetType.TANGIBLE,
        DepreciationMethod.WDV,
        8,
        5,
        Decimal("11.88"),
        15,
        True,
        True,
    ),
    (
        "SOFT",
        "Software Licences",
        AssetType.INTANGIBLE,
        DepreciationMethod.SLM,
        3,
        0,
        Decimal("33.33"),
        25,
        False,
        True,
    ),
]

FD_PRODUCTS = [
    (
        "FD_STD",
        "Standard Fixed Deposit",
        7,
        3650,
        10000,
        FDInterestPayoutFrequency.QUARTERLY,
        FDCompoundingFrequency.QUARTERLY,
    ),
    (
        "FD_CORP",
        "Corporate Treasury Fixed Deposit",
        30,
        3650,
        1000000,
        FDInterestPayoutFrequency.ON_MATURITY,
        FDCompoundingFrequency.QUARTERLY,
    ),
]

FD_INTEREST_SLABS = [
    (7, 45, Decimal("4.00")),
    (46, 180, Decimal("5.25")),
    (181, 365, Decimal("6.50")),
    (366, 1095, Decimal("7.00")),
    (1096, 3650, Decimal("7.25")),
]

INVENTORY_CATEGORIES = [
    ("STATIONERY", "Stationery and Office Supplies", True, False, False),
    ("IT_CONS", "IT Consumables", True, False, False),
    ("SECURITY", "Security and Access Cards", True, True, False),
    ("SERVICE", "Services", False, False, False),
]

INVENTORY_ITEMS = [
    (
        "PAPER_A4",
        "A4 Copier Paper",
        "STATIONERY",
        ItemType.CONSUMABLE,
        UnitOfMeasure.REAM,
        250,
        10,
        50,
        20,
        "4820",
        12,
    ),
    (
        "TONER_STD",
        "Standard Printer Toner",
        "IT_CONS",
        ItemType.CONSUMABLE,
        UnitOfMeasure.EACH,
        3500,
        5,
        20,
        5,
        "8443",
        18,
    ),
    (
        "ID_CARD",
        "Employee ID Card",
        "SECURITY",
        ItemType.STOCK,
        UnitOfMeasure.EACH,
        120,
        25,
        200,
        50,
        "3926",
        18,
    ),
    (
        "AMC_SERVICE",
        "Annual Maintenance Service",
        "SERVICE",
        ItemType.SERVICE,
        UnitOfMeasure.EACH,
        0,
        0,
        0,
        0,
        "9987",
        18,
    ),
]

COMPLIANCE_ITEMS = [
    (
        "GST_GSTR1",
        "GSTR-1 outward supply return",
        RegulatoryBody.GST,
        ComplianceFrequency.MONTHLY,
        11,
        CompliancePriority.HIGH,
        "GSTR-1",
        "GST",
    ),
    (
        "GST_GSTR3B",
        "GSTR-3B monthly summary return",
        RegulatoryBody.GST,
        ComplianceFrequency.MONTHLY,
        20,
        CompliancePriority.CRITICAL,
        "GSTR-3B",
        "GST",
    ),
    (
        "TDS_26Q",
        "TDS Form 26Q non-salary return",
        RegulatoryBody.INCOME_TAX,
        ComplianceFrequency.QUARTERLY,
        31,
        CompliancePriority.HIGH,
        "26Q",
        "Finance",
    ),
    (
        "RBI_ALM",
        "RBI ALM statement",
        RegulatoryBody.RBI,
        ComplianceFrequency.MONTHLY,
        15,
        CompliancePriority.CRITICAL,
        "ALM",
        "Treasury",
    ),
    (
        "RBI_CRILC",
        "RBI CRILC return",
        RegulatoryBody.RBI,
        ComplianceFrequency.MONTHLY,
        21,
        CompliancePriority.CRITICAL,
        "CRILC",
        "Risk",
    ),
    (
        "MCA_AOC4",
        "MCA AOC-4 financial statement filing",
        RegulatoryBody.MCA,
        ComplianceFrequency.ANNUALLY,
        30,
        CompliancePriority.HIGH,
        "AOC-4",
        "Finance",
    ),
]

DMS_FOLDERS = [
    (
        "Finance",
        "finance",
        "Financial statements, vouchers and audit documents",
        "#2563eb",
        "wallet",
    ),
    (
        "Lending",
        "lending",
        "Loan applications, sanctions, security and disbursement documents",
        "#16a34a",
        "landmark",
    ),
    ("Treasury", "treasury", "Borrowing, ALM and investment records", "#0f766e", "banknote"),
    ("Tax", "tax", "GST, TDS and statutory tax working files", "#dc2626", "receipt"),
    ("HRIS", "hris", "Employee, attendance, leave and payroll documents", "#7c3aed", "users"),
    (
        "Vendor",
        "vendor",
        "Vendor onboarding, invoices and compliance documents",
        "#ea580c",
        "briefcase",
    ),
    ("Legal", "legal", "Notices, cases and recovery documents", "#374151", "scale"),
    ("Board", "board", "Board packs, approvals and committee notes", "#9333ea", "file-check"),
]

DMS_TAGS = [
    ("Approved", "approved", "Workflow", "#16a34a"),
    ("Pending Review", "pending-review", "Workflow", "#f59e0b"),
    ("Confidential", "confidential", "Security", "#dc2626"),
    ("Statutory", "statutory", "Compliance", "#2563eb"),
    ("Borrower", "borrower", "Lending", "#0f766e"),
    ("Audit", "audit", "Finance", "#6b7280"),
]

IT_DECLARATION_SECTIONS = [
    ("80C", "Section 80C Investments", "DEDUCTION", 150000, ["LIC", "PPF", "ELSS", "TUITION_FEE"]),
    ("80D", "Medical Insurance Premium", "DEDUCTION", 25000, ["INSURANCE_RECEIPT"]),
    ("80CCD_1B", "Additional NPS Contribution", "DEDUCTION", 50000, ["NPS_RECEIPT"]),
    ("24B", "Home Loan Interest", "DEDUCTION", 200000, ["INTEREST_CERTIFICATE"]),
    ("HRA", "House Rent Allowance", "EXEMPTION", 9999999, ["RENT_RECEIPT", "LANDLORD_PAN"]),
    ("LTA", "Leave Travel Allowance", "EXEMPTION", 9999999, ["TRAVEL_BILLS"]),
]

REIMBURSEMENT_CATEGORIES = [
    ("TRAVEL_LOCAL", "Local Travel", ClaimType.LOCAL_TRAVEL, 5000, 25000),
    ("MOBILE", "Mobile Reimbursement", ClaimType.MOBILE, 2000, 24000),
    ("INTERNET", "Internet Reimbursement", ClaimType.INTERNET, 1500, 18000),
    ("MEDICAL", "Medical Reimbursement", ClaimType.MEDICAL, 5000, 30000),
    ("CERT", "Professional Certification", ClaimType.CERTIFICATION, 25000, 50000),
]

HELPDESK_CATEGORIES = [
    ("HR_LEAVE", "Leave and Attendance", TicketCategory.LEAVE_ISSUE, "HR", 4, 48),
    ("HR_PAYROLL", "Salary and Payroll", TicketCategory.SALARY_QUERY, "HR", 4, 72),
    ("HR_DOC", "Employee Document Request", TicketCategory.DOCUMENT_REQUEST, "HR", 8, 96),
    ("IT_ACCESS", "Application Access Request", TicketCategory.ACCESS_REQUEST, "IT", 2, 24),
    ("IT_SOFTWARE", "Software Issue", TicketCategory.SOFTWARE_ISSUE, "IT", 4, 48),
]

LEGAL_EXPENSE_CATEGORIES = [
    ("COURT_FEE", "Court Fee", ExpenseCategoryType.COURT_FEE, False, None, False, 0),
    ("FILING_FEE", "Filing Fee", ExpenseCategoryType.FILING_FEE, False, None, False, 1),
    ("ADV_RET", "Advocate Retainer", ExpenseCategoryType.ADVOCATE_RETAINER, True, "194J", True, 2),
    (
        "ADV_APP",
        "Advocate Appearance Fee",
        ExpenseCategoryType.ADVOCATE_APPEARANCE,
        True,
        "194J",
        True,
        3,
    ),
    (
        "PUBLICATION",
        "Publication Charges",
        ExpenseCategoryType.PUBLICATION_CHARGES,
        True,
        "194C",
        True,
        4,
    ),
    ("COURIER", "Courier and Postage", ExpenseCategoryType.COURIER_POSTAGE, False, None, True, 5),
]

STATUTORY_PERIODS = [
    (
        "SARFAESI_13_2",
        "SARFAESI 13(2) Demand Notice",
        "SARFAESI Act, 2002",
        "Section 13(2)",
        60,
        "60 days",
        "Demand notice served",
        "Proceed under Section 13(4) after expiry",
    ),
    (
        "SARFAESI_13_4",
        "SARFAESI Possession Action",
        "SARFAESI Act, 2002",
        "Section 13(4)",
        15,
        "15 days",
        "Possession notice issued",
        "Possession publication/next recovery action",
    ),
    (
        "NI_138",
        "Cheque Bounce Notice",
        "Negotiable Instruments Act, 1881",
        "Section 138",
        30,
        "30 days",
        "Cheque return memo received",
        "Issue statutory demand notice",
    ),
    (
        "DRT_OA",
        "DRT Original Application Limitation",
        "Recovery of Debts and Bankruptcy Act, 1993",
        "Section 19",
        1095,
        "3 years",
        "Cause of action/default",
        "Claim may become time barred",
    ),
]

COURT_MASTERS = [
    (
        "DRT_MUM",
        "Debt Recovery Tribunal Mumbai",
        CourtType.DRT,
        "Mumbai and Maharashtra",
        "Maharashtra",
        "27",
    ),
    (
        "DRAT_MUM",
        "Debt Recovery Appellate Tribunal Mumbai",
        CourtType.DRAT,
        "Western Zone",
        "Maharashtra",
        "27",
    ),
    (
        "NCLT_MUM",
        "National Company Law Tribunal Mumbai Bench",
        CourtType.NCLT,
        "Mumbai",
        "Maharashtra",
        "27",
    ),
    (
        "HC_BOM",
        "Bombay High Court",
        CourtType.HIGH_COURT,
        "Maharashtra and Goa",
        "Maharashtra",
        "27",
    ),
]

NOTIFICATION_TEMPLATES = [
    (
        "WORKFLOW_PENDING",
        "Workflow approval pending",
        NotificationCategory.WORKFLOW,
        "Approval pending: {{item_name}}",
        "A workflow item is pending for your action.",
    ),
    (
        "LOAN_STATUS",
        "Loan application status update",
        NotificationCategory.LOAN,
        "Loan status updated",
        "Your loan application status has been updated.",
    ),
    (
        "PAYMENT_DUE",
        "Payment due reminder",
        NotificationCategory.PAYMENT,
        "Payment due reminder",
        "A payment/demand is due for action.",
    ),
    (
        "COMPLIANCE_DUE",
        "Compliance due reminder",
        NotificationCategory.REMINDER,
        "Compliance due: {{form_name}}",
        "A compliance activity is approaching its due date.",
    ),
    (
        "REPORT_READY",
        "Report generation complete",
        NotificationCategory.SYSTEM,
        "Report ready",
        "Your report is ready for download.",
    ),
]

BI_DATA_SOURCES = [
    ("MIS_DASHBOARD", "MIS Dashboard API", "/api/v1/reports/mis/dashboard", BIModule.FINANCE),
    ("MIS_ALL_MODULES", "All Modules MIS API", "/api/v1/reports/mis/all-modules", BIModule.FINANCE),
    (
        "LENDING_PORTFOLIO",
        "Lending Portfolio Summary",
        "/api/v1/reports/mis/portfolio-summary",
        BIModule.LENDING,
    ),
    (
        "COLLECTION_DPD",
        "Collections and DPD",
        "/api/v1/reports/mis/delinquency",
        BIModule.COLLECTIONS,
    ),
]


def money(value) -> Decimal:
    """Return Decimal money with 2 decimal places."""
    return Decimal(str(value)).quantize(Decimal("0.01"))


def discover_backend_permission_codes() -> set[str]:
    """Discover permission codes used by API dependencies.

    This keeps the master seed aligned as modules are added so a fresh UAT
    environment does not start with missing-role empty screens or 403s.
    """
    codes = {perm["code"] for perm in PERMISSIONS}
    for permission_group in ALL_PERMISSIONS.values():
        codes.update(str(code) for code in permission_group)

    api_root = Path(__file__).parent.parent / "app" / "api"
    dependency_pattern = re.compile(
        r"(?:RequirePermissions|PermissionChecker)\((.*?)\)",
        re.DOTALL,
    )
    for path in api_root.rglob("*.py"):
        text = path.read_text()
        for match in dependency_pattern.finditer(text):
            codes.update(re.findall(r"[\"']([A-Z0-9_]+)[\"']", match.group(1)))
            for permission_name in re.findall(r"Permissions\.([A-Z0-9_]+)", match.group(1)):
                permission_code = getattr(Permissions, permission_name, None)
                if permission_code:
                    codes.add(str(permission_code))
    return codes


def permission_data_from_code(code: str) -> dict:
    parts = code.split("_")
    module = parts[0] if parts else "SYSTEM"
    action = (
        "READ" if code.endswith("_VIEW") else "EXPORT" if code.endswith("_EXPORT") else "MANAGE"
    )
    return {
        "code": code,
        "name": code.replace("_", " ").title(),
        "module": module,
        "resource": code.lower(),
        "action": action,
    }


async def seed_permissions(session) -> dict:
    """Seed permissions and return permission map."""
    print("Seeding permissions...")
    permission_map = {}

    permission_seed_data = [
        permission_data_from_code(code) for code in sorted(discover_backend_permission_codes())
    ]

    for perm_data in permission_seed_data:
        result = await session.execute(
            select(Permission).where(Permission.code == perm_data["code"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            permission_map[perm_data["code"]] = existing
            print(f"  - Permission '{perm_data['code']}' already exists")
        else:
            permission = Permission(**perm_data)
            session.add(permission)
            await session.flush()
            permission_map[perm_data["code"]] = permission
            print(f"  + Created permission '{perm_data['code']}'")

    await session.commit()
    print(f"Total permissions: {len(permission_map)}")
    return permission_map


async def seed_roles(session, permission_map: dict) -> dict:
    """Seed roles with permissions."""
    print("\nSeeding roles...")
    role_map = {}

    for role_data in ROLES:
        result = await session.execute(select(Role).where(Role.code == role_data["code"]))
        existing = result.scalar_one_or_none()

        if existing:
            role_map[role_data["code"]] = existing

            # For SUPER_ADMIN, ensure all permissions are assigned
            if role_data["code"] == "SUPER_ADMIN":
                # Get existing role permissions
                existing_perm_ids = set()
                for rp in existing.role_permissions:
                    existing_perm_ids.add(rp.permission_id)

                # Add any missing permissions
                added_count = 0
                for perm_code, perm in permission_map.items():
                    if perm.id not in existing_perm_ids:
                        role_perm = RolePermission(
                            role_id=existing.id,
                            permission_id=perm.id,
                        )
                        session.add(role_perm)
                        added_count += 1

                if added_count > 0:
                    await session.commit()
                    print(
                        f"  - Role '{role_data['code']}' already exists, "
                        f"added {added_count} new permissions"
                    )
                else:
                    print(
                        f"  - Role '{role_data['code']}' already exists (all permissions present)"
                    )
            else:
                print(f"  - Role '{role_data['code']}' already exists")
            continue

        # Create role
        role = Role(
            code=role_data["code"],
            name=role_data["name"],
            description=role_data["description"],
            is_system_role=role_data["is_system_role"],
            is_default=role_data["is_default"],
        )
        session.add(role)
        await session.flush()

        # Assign permissions
        perm_codes = role_data["permissions"]
        if perm_codes == "*":
            perm_codes = list(permission_map.keys())

        for perm_code in perm_codes:
            if perm_code in permission_map:
                role_perm = RolePermission(
                    role_id=role.id,
                    permission_id=permission_map[perm_code].id,
                )
                session.add(role_perm)

        role_map[role_data["code"]] = role
        print(f"  + Created role '{role_data['code']}' with {len(perm_codes)} permissions")

    await session.commit()
    print(f"Total roles: {len(role_map)}")
    return role_map


async def seed_organization(session):
    """Seed SMFC organization (overridable via SEED_ORG_* env vars for E2E)."""
    print("\nSeeding organization...")

    org_code = os.getenv("SEED_ORG_CODE", "SMFC")
    org_name = os.getenv("SEED_ORG_NAME", "SMFC Ltd")
    org_legal_name = os.getenv("SEED_ORG_LEGAL_NAME", "SMFC Financial Corporation Limited")

    result = await session.execute(select(Organization).where(Organization.code == org_code))
    existing = result.scalar_one_or_none()

    if existing:
        print(f"  - Organization '{org_code}' already exists")
        return existing

    org = Organization(
        code=org_code,
        name=org_name,
        legal_name=org_legal_name,
        short_name=org_code[:20],
        description="State Micro Finance Corporation - Enterprise NBFC Management System",
        pan="AABCS1234A",
        cin="U65100MH2020PTC123456",
        gstin="27AABCS1234A1Z5",
        reg_address_line1="123 Finance Tower",
        reg_address_line2="Bandra Kurla Complex",
        reg_city="Mumbai",
        reg_district="Mumbai Suburban",
        reg_state_code="27",
        reg_pincode="400051",
        reg_country="IN",
        phone="+91 22 12345678",
        email="info@smfc.com",
        website="https://www.smfc.com",
        base_currency="INR",
        financial_year_start_month=4,
        is_primary=True,
        status="ACTIVE",
    )
    session.add(org)
    await session.commit()
    print("  + Created organization 'SMFC'")
    return org


async def seed_units(session, org):
    """Seed units."""
    print("\nSeeding units...")
    unit_map = {}
    head_office = None

    for unit_data in UNITS:
        result = await session.execute(select(Unit).where(Unit.code == unit_data["code"]))
        existing = result.scalar_one_or_none()

        if existing:
            unit_map[unit_data["code"]] = existing
            if existing.is_head_office:
                head_office = existing
            print(f"  - Unit '{unit_data['code']}' already exists")
            continue

        unit = Unit(
            code=unit_data["code"],
            name=unit_data["name"],
            unit_type=unit_data["unit_type"],
            organization_id=org.id,
            city=unit_data.get("city"),
            state_code=unit_data.get("state_code"),
            country="IN",
            is_head_office=unit_data.get("is_head_office", False),
            status="ACTIVE",
        )
        session.add(unit)
        await session.flush()
        unit_map[unit_data["code"]] = unit
        if unit.is_head_office:
            head_office = unit
        print(f"  + Created unit '{unit_data['code']}'")

    # Set parent unit for branches (Head Office is parent)
    if head_office:
        for code, unit in unit_map.items():
            if not unit.is_head_office and not unit.parent_unit_id:
                unit.parent_unit_id = head_office.id

    await session.commit()
    print(f"Total units: {len(unit_map)}")
    return unit_map


async def seed_departments(session, org):
    """Seed departments."""
    print("\nSeeding departments...")
    dept_map = {}

    for dept_data in DEPARTMENTS:
        result = await session.execute(
            select(Department).where(Department.code == dept_data["code"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            dept_map[dept_data["code"]] = existing
            print(f"  - Department '{dept_data['code']}' already exists")
            continue

        dept = Department(
            code=dept_data["code"],
            name=dept_data["name"],
            short_name=dept_data.get("short_name"),
            cost_center_code=dept_data.get("cost_center_code"),
            organization_id=org.id,
            status="ACTIVE",
        )
        session.add(dept)
        await session.flush()
        dept_map[dept_data["code"]] = dept
        print(f"  + Created department '{dept_data['code']}'")

    await session.commit()
    print(f"Total departments: {len(dept_map)}")
    return dept_map


async def seed_designations(session, dept_map):
    """Seed designations."""
    print("\nSeeding designations...")
    desig_map = {}

    for desig_data in DESIGNATIONS:
        result = await session.execute(
            select(Designation).where(Designation.code == desig_data["code"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            desig_map[desig_data["code"]] = existing
            print(f"  - Designation '{desig_data['code']}' already exists")
            continue

        desig = Designation(
            code=desig_data["code"],
            name=desig_data["name"],
            level=desig_data["level"],
            min_experience_years=desig_data["min_experience_years"],
            status="ACTIVE",
        )
        session.add(desig)
        await session.flush()
        desig_map[desig_data["code"]] = desig
        print(f"  + Created designation '{desig_data['code']}'")

    await session.commit()
    print(f"Total designations: {len(desig_map)}")
    return desig_map


async def seed_users(session, org, role_map, unit_map):
    """Seed admin and sample users."""
    print("\nSeeding users...")
    user_count = 0
    head_office = unit_map.get("HO")

    # Create admin user
    result = await session.execute(select(User).where(User.username == ADMIN_USER["username"]))
    admin = result.scalar_one_or_none()

    if admin:
        updated = False
        if admin.organization_id != org.id:
            admin.organization_id = org.id
            updated = True
        if head_office and admin.default_unit_id != head_office.id:
            admin.default_unit_id = head_office.id
            updated = True
        if updated:
            print(
                f"  ~ Admin user '{ADMIN_USER['username']}' already exists; "
                "aligned organization and default unit"
            )
        else:
            print(f"  - Admin user '{ADMIN_USER['username']}' already exists")
    else:
        password_hash = get_password_hash(ADMIN_USER["password"])
        password_expires_at = datetime.now(UTC) + timedelta(days=settings.PASSWORD_EXPIRY_DAYS)

        admin = User(
            username=ADMIN_USER["username"],
            email=ADMIN_USER["email"],
            full_name=ADMIN_USER["full_name"],
            employee_code=ADMIN_USER["employee_code"],
            password_hash=password_hash,
            password_changed_at=datetime.now(UTC),
            password_expires_at=password_expires_at,
            status=UserStatus.ACTIVE.value,
            organization_id=org.id,
            default_unit_id=head_office.id if head_office else None,
        )
        session.add(admin)
        await session.flush()

        # Assign admin role
        admin_role = role_map.get(ADMIN_USER["role"])
        if admin_role:
            user_role = UserRole(
                user_id=admin.id,
                role_id=admin_role.id,
                effective_from=datetime.now(UTC),
            )
            session.add(user_role)

        print(f"  + Created admin user '{ADMIN_USER['username']}'")
        user_count += 1

    # Create sample users
    for user_data in SAMPLE_USERS:
        result = await session.execute(select(User).where(User.username == user_data["username"]))
        existing = result.scalar_one_or_none()

        if existing:
            updated = False
            if existing.organization_id != org.id:
                existing.organization_id = org.id
                updated = True
            if head_office and existing.default_unit_id != head_office.id:
                existing.default_unit_id = head_office.id
                updated = True
            if updated:
                print(
                    f"  ~ User '{user_data['username']}' already exists; "
                    "aligned organization and default unit"
                )
            else:
                print(f"  - User '{user_data['username']}' already exists")
            continue

        password_hash = get_password_hash("Password123!")
        password_expires_at = datetime.now(UTC) + timedelta(days=settings.PASSWORD_EXPIRY_DAYS)

        user = User(
            username=user_data["username"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            employee_code=user_data["employee_code"],
            password_hash=password_hash,
            password_changed_at=datetime.now(UTC),
            password_expires_at=password_expires_at,
            status=UserStatus.ACTIVE.value,
            organization_id=org.id,
            default_unit_id=head_office.id if head_office else None,
        )
        session.add(user)
        await session.flush()

        # Assign role
        role = role_map.get(user_data["role"])
        if role:
            user_role = UserRole(
                user_id=user.id,
                role_id=role.id,
                effective_from=datetime.now(UTC),
            )
            session.add(user_role)

        print(f"  + Created user '{user_data['username']}' with role '{user_data['role']}'")
        user_count += 1

    await session.commit()
    print(f"Total users created: {user_count}")


async def seed_financial_year(session, org):
    """Seed Financial Year FY2024-25 with monthly periods."""
    print("\nSeeding financial year...")

    result = await session.execute(select(FinancialYear).where(FinancialYear.code == "FY2024-25"))
    existing = result.scalar_one_or_none()

    if existing:
        print("  - Financial Year 'FY2024-25' already exists")
        return existing

    from datetime import date

    fy = FinancialYear(
        code="FY2024-25",
        name="April 2024 - March 2025",
        start_date=date(2024, 4, 1),
        end_date=date(2025, 3, 31),
        is_active=True,
        is_current=True,
        is_closed=False,
        organization_id=org.id,
    )
    session.add(fy)
    await session.flush()

    # Create monthly periods
    month_names = [
        "April 2024",
        "May 2024",
        "June 2024",
        "July 2024",
        "August 2024",
        "September 2024",
        "October 2024",
        "November 2024",
        "December 2024",
        "January 2025",
        "February 2025",
        "March 2025",
    ]

    current_date = date(2024, 4, 1)
    for i, month_name in enumerate(month_names):
        # Calculate end date (last day of month)
        if current_date.month == 12:
            next_month = date(current_date.year + 1, 1, 1)
        else:
            next_month = date(current_date.year, current_date.month + 1, 1)
        end_date = next_month - timedelta(days=1)

        period = FinancialPeriod(
            financial_year_id=fy.id,
            period_number=i + 1,
            name=month_name,
            start_date=current_date,
            end_date=end_date,
            is_closed=False,
        )
        session.add(period)

        # Move to next month
        current_date = next_month

    await session.commit()
    print("  + Created financial year 'FY2024-25' with 12 monthly periods")
    return fy


async def seed_account_groups(session, org):
    """Seed Account Groups following Indian Schedule III."""
    print("\nSeeding account groups...")
    group_map = {}
    created_count = 0

    # First pass: create all groups without parent references
    for group_data in ACCOUNT_GROUPS:
        result = await session.execute(
            select(AccountGroup).where(AccountGroup.code == group_data["code"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            group_map[group_data["code"]] = existing
            continue

        group = AccountGroup(
            code=group_data["code"],
            name=group_data["name"],
            nature=AccountNature[group_data["nature"]],
            level=group_data["level"],
            sequence=group_data["sequence"],
            is_system=group_data.get("is_system", False),
            is_active=True,
            organization_id=org.id,
        )
        session.add(group)
        await session.flush()
        group_map[group_data["code"]] = group
        created_count += 1

    await session.commit()

    # Second pass: set parent references
    for group_data in ACCOUNT_GROUPS:
        if "parent" in group_data:
            group = group_map[group_data["code"]]
            parent = group_map.get(group_data["parent"])
            if parent and group.parent_group_id != parent.id:
                group.parent_group_id = parent.id

    await session.commit()

    if created_count > 0:
        print(f"  + Created {created_count} account groups")
    else:
        print("  - All account groups already exist")

    print(f"Total account groups: {len(group_map)}")
    return group_map


async def seed_accounts(session, org, group_map):
    """Seed sample accounts (ledgers)."""
    print("\nSeeding accounts...")
    created_count = 0

    for acc_data in ACCOUNTS:
        result = await session.execute(select(Account).where(Account.code == acc_data["code"]))
        existing = result.scalar_one_or_none()

        if existing:
            acc_type = AccountType[acc_data.get("type", "LEDGER")]
            existing.is_bank_account = acc_type == AccountType.BANK
            existing.is_cash_account = acc_type == AccountType.CASH
            existing.bank_name = acc_data.get("bank_name")
            existing.bank_branch = acc_data.get("bank_branch")
            existing.bank_account_number = acc_data.get("bank_account")
            existing.bank_ifsc_code = acc_data.get("bank_ifsc")
            continue

        group = group_map.get(acc_data["group"])
        if not group:
            print(
                f"  ! Warning: Group '{acc_data['group']}' not found for account "
                f"'{acc_data['code']}'"
            )
            continue

        # Map account type
        acc_type = AccountType[acc_data.get("type", "LEDGER")]

        # Map balance type
        balance_type = None
        if "balance_type" in acc_data:
            balance_type = BalanceType[acc_data["balance_type"]]

        account = Account(
            code=acc_data["code"],
            name=acc_data["name"],
            account_group_id=group.id,
            account_type=acc_type,
            is_control_account=acc_data.get("type") == "CONTROL",
            control_type=acc_data.get("control_type"),
            currency_code="INR",
            opening_balance=acc_data.get("opening", 0),
            opening_balance_type=balance_type,
            bank_name=acc_data.get("bank_name"),
            bank_branch=acc_data.get("bank_branch"),
            bank_account_number=acc_data.get("bank_account"),
            bank_ifsc_code=acc_data.get("bank_ifsc"),
            is_bank_account=acc_type == AccountType.BANK,
            is_cash_account=acc_type == AccountType.CASH,
            is_active=True,
            organization_id=org.id,
        )
        session.add(account)
        created_count += 1

    await session.commit()

    if created_count > 0:
        print(f"  + Created {created_count} accounts")
    else:
        print("  - All accounts already exist")


async def seed_organization_bank_accounts(session, org):
    """Seed organization bank accounts linked to bank GL ledgers."""
    print("\nSeeding organization bank accounts...")
    created_count = 0

    for code in ["1101", "1102", "1103"]:
        account = (
            await session.execute(
                select(Account).where(
                    Account.organization_id == org.id,
                    Account.code == code,
                )
            )
        ).scalar_one_or_none()
        if not account or not account.bank_account_number:
            continue

        existing = (
            await session.execute(
                select(OrganizationBankAccount).where(
                    OrganizationBankAccount.organization_id == org.id,
                    OrganizationBankAccount.account_number == account.bank_account_number,
                )
            )
        ).scalar_one_or_none()
        if existing:
            existing.ledger_account_id = account.id
            existing.is_primary = code == "1101"
            existing.allow_payments = True
            existing.allow_receipts = True
            continue

        session.add(
            OrganizationBankAccount(
                organization_id=org.id,
                account_name=account.name,
                account_number=account.bank_account_number,
                ifsc_code=account.bank_ifsc_code or "SBIN0001234",
                bank_name=account.bank_name or account.name,
                branch_name=account.bank_branch,
                account_type="CURRENT",
                ledger_account_id=account.id,
                is_primary=code == "1101",
                allow_payments=True,
                allow_receipts=True,
            )
        )
        created_count += 1

    await session.commit()
    if created_count > 0:
        print(f"  + Created {created_count} organization bank accounts")
    else:
        print("  - Organization bank accounts already exist")


async def seed_voucher_types(session, org):
    """Seed standard voucher types."""
    print("\nSeeding voucher types...")
    created_count = 0

    for vt_data in VOUCHER_TYPES:
        result = await session.execute(
            select(VoucherType).where(VoucherType.code == vt_data["code"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            continue

        voucher_type = VoucherType(
            code=vt_data["code"],
            name=vt_data["name"],
            voucher_class=VoucherClass[vt_data["class"]],
            auto_numbering=vt_data["auto"],
            prefix=vt_data["prefix"],
            requires_approval=vt_data["approval"],
            approval_levels=vt_data["levels"],
            is_active=True,
            organization_id=org.id,
        )
        session.add(voucher_type)
        created_count += 1

    await session.commit()

    if created_count > 0:
        print(f"  + Created {created_count} voucher types")
    else:
        print("  - All voucher types already exist")


async def seed_gst_rates(session):
    """Seed GST rates."""
    print("\nSeeding GST rates...")
    created_count = 0
    gst_rate_map = {}
    from datetime import date

    for rate_data in GST_RATES:
        result = await session.execute(select(GSTRate).where(GSTRate.code == rate_data["code"]))
        existing = result.scalar_one_or_none()

        if existing:
            gst_rate_map[rate_data["code"]] = existing
            continue

        gst_rate = GSTRate(
            code=rate_data["code"],
            name=rate_data["name"],
            rate=rate_data["rate"],
            cgst_rate=rate_data["cgst"],
            sgst_rate=rate_data["sgst"],
            igst_rate=rate_data["igst"],
            cess_rate=rate_data["cess"],
            description=rate_data.get("description"),
            effective_from=date(2017, 7, 1),  # GST implemented from July 2017
            is_active=True,
        )
        session.add(gst_rate)
        await session.flush()
        gst_rate_map[rate_data["code"]] = gst_rate
        created_count += 1

    await session.commit()

    if created_count > 0:
        print(f"  + Created {created_count} GST rates")
    else:
        print("  - All GST rates already exist")

    return gst_rate_map


async def seed_hsn_sac_codes(session, gst_rate_map):
    """Seed HSN/SAC codes."""
    print("\nSeeding HSN/SAC codes...")
    created_count = 0

    for hsn_data in HSN_SAC_CODES:
        result = await session.execute(select(HSNSAC).where(HSNSAC.code == hsn_data["code"]))
        existing = result.scalar_one_or_none()

        if existing:
            continue

        gst_rate = gst_rate_map.get(hsn_data["gst_rate"])

        hsn_sac = HSNSAC(
            code=hsn_data["code"],
            description=hsn_data["description"],
            hsn_sac_type=HSNSACType[hsn_data["type"]],
            gst_rate_id=gst_rate.id if gst_rate else None,
            is_active=True,
        )
        session.add(hsn_sac)
        created_count += 1

    await session.commit()

    if created_count > 0:
        print(f"  + Created {created_count} HSN/SAC codes")
    else:
        print("  - All HSN/SAC codes already exist")


async def seed_gst_registration(session, org):
    """Seed sample GST registration."""
    print("\nSeeding GST registration...")
    seeded_gstin = "27AABCS1234A1Z5"

    result = await session.execute(
        select(GSTRegistration)
        .where(GSTRegistration.organization_id == org.id)
        .order_by(GSTRegistration.created_at.asc(), GSTRegistration.id.asc())
    )
    existing_registrations = result.scalars().all()

    if existing_registrations:
        existing = next(
            (
                registration
                for registration in existing_registrations
                if registration.gstin == seeded_gstin
            ),
            existing_registrations[0],
        )
        if len(existing_registrations) > 1:
            print(
                f"  - Found {len(existing_registrations)} GST registrations for organization; "
                f"reusing {existing.gstin}"
            )
        else:
            print("  - GST registration already exists")
        return existing

    registration = GSTRegistration(
        gstin=seeded_gstin,
        legal_name="SMFC Financial Corporation Limited",
        trade_name="SMFC Ltd",
        registration_type=GSTRegistrationType.REGULAR,
        state_code="27",
        state_name="Maharashtra",
        organization_id=org.id,
        address="123 Finance Tower, Bandra Kurla Complex, Mumbai",
        pincode="400051",
        is_e_invoice_enabled=True,
        is_e_way_bill_enabled=True,
        is_active=True,
    )
    session.add(registration)
    await session.commit()
    print(f"  + Created GST registration for GSTIN: {registration.gstin}")
    return registration


async def seed_tds_sections(session):
    """Seed TDS sections."""
    print("\nSeeding TDS sections...")
    created_count = 0
    from datetime import date

    for tds_data in TDS_SECTIONS:
        result = await session.execute(
            select(TDSSection).where(TDSSection.section_code == tds_data["code"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            continue

        tds_section = TDSSection(
            section_code=tds_data["code"],
            section_name=tds_data["name"],
            description=tds_data.get("description"),
            rate_individual=tds_data["rate_ind"],
            rate_company=tds_data["rate_comp"],
            rate_no_pan=tds_data["rate_no_pan"],
            threshold_single=tds_data.get("threshold_single", 0),
            threshold_annual=tds_data.get("threshold_annual", 0),
            is_tcs=tds_data.get("is_tcs", False),
            surcharge_applicable=False,
            cess_rate=4,  # Health & Education Cess @ 4%
            effective_from=date(2024, 4, 1),  # FY 2024-25
            return_form=tds_data.get("return_form", "26Q"),
            nature_of_payment_code=tds_data.get("nature_code"),
            is_active=True,
        )
        session.add(tds_section)
        created_count += 1

    await session.commit()

    if created_count > 0:
        print(f"  + Created {created_count} TDS sections")
    else:
        print("  - All TDS sections already exist")


async def seed_payment_terms(session, org_id):
    """Seed default payment terms for organization."""
    print("\nSeeding payment terms...")
    created_count = 0

    for terms_data in PAYMENT_TERMS:
        result = await session.execute(
            select(PaymentTerms).where(
                PaymentTerms.code == terms_data["code"], PaymentTerms.organization_id == org_id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            continue

        payment_terms = PaymentTerms(
            code=terms_data["code"],
            name=terms_data["name"],
            description=terms_data.get("description"),
            days=terms_data["days"],
            discount_days=terms_data.get("discount_days", 0),
            discount_percent=terms_data.get("discount_percent", 0),
            organization_id=org_id,
            is_active=True,
        )
        session.add(payment_terms)
        created_count += 1

    await session.commit()

    if created_count > 0:
        print(f"  + Created {created_count} payment terms")
    else:
        print("  - All payment terms already exist")


async def seed_lending_masters(session, org):
    """Seed corporate lending masters so a fresh tenant has usable defaults."""
    print("\nSeeding lending masters...")

    # Base/reference rates
    rate_map = {}
    created_rates = 0
    for data in INTEREST_RATES:
        result = await session.execute(
            select(InterestRate).where(
                InterestRate.organization_id == org.id,
                InterestRate.code == data["code"],
            )
        )
        rate = result.scalar_one_or_none()
        if not rate:
            rate = InterestRate(
                organization_id=org.id,
                code=data["code"],
                name=data["name"],
                description=data["description"],
                rate_type=data["rate_type"],
                benchmark_name=data["benchmark_name"],
                current_rate=money(data["current_rate"]),
                effective_from=datetime.now(UTC).date().replace(month=4, day=1),
                reset_frequency=data["reset_frequency"],
                next_review_date=datetime.now(UTC).date() + timedelta(days=90),
            )
            session.add(rate)
            await session.flush()
            created_rates += 1
        rate_map[data["code"]] = rate

    # Fees
    fee_map = {}
    created_fees = 0
    for data in FEE_MASTERS:
        result = await session.execute(
            select(FeeMaster).where(
                FeeMaster.organization_id == org.id,
                FeeMaster.code == data["code"],
            )
        )
        fee = result.scalar_one_or_none()
        if not fee:
            fee = FeeMaster(
                organization_id=org.id,
                code=data["code"],
                name=data["name"],
                description=f"{data['name']} for corporate lending",
                fee_type=data["fee_type"],
                calculation_type=data["calculation_type"],
                default_rate=(
                    money(data["default_rate"]) if data.get("default_rate") is not None else None
                ),
                default_amount=(
                    money(data["default_amount"])
                    if data.get("default_amount") is not None
                    else None
                ),
                min_amount=(
                    money(data["min_amount"]) if data.get("min_amount") is not None else None
                ),
                max_amount=(
                    money(data["max_amount"]) if data.get("max_amount") is not None else None
                ),
                collection_stage=data["collection_stage"],
                is_refundable=False,
                deduct_from_disbursement=True,
                is_taxable=data["is_taxable"],
                gst_rate=money("18.00"),
                hsn_sac_code="9971",
                income_gl_account="4101",
                receivable_gl_account="1404",
            )
            session.add(fee)
            await session.flush()
            created_fees += 1
        fee_map[data["code"]] = fee

    # Loan products + document checklists + product fee links
    created_products = 0
    created_docs = 0
    created_product_fees = 0
    base_rate = rate_map.get("SMFCL_BR")
    for data in LOAN_PRODUCTS:
        result = await session.execute(
            select(LoanProduct).where(
                LoanProduct.organization_id == org.id,
                LoanProduct.code == data["code"],
            )
        )
        product = result.scalar_one_or_none()
        if not product:
            product = LoanProduct(
                organization_id=org.id,
                code=data["code"],
                name=data["name"],
                description=data["description"],
                category=data["category"],
                min_amount=money(data["min_amount"]),
                max_amount=money(data["max_amount"]),
                default_amount=money(data["default_amount"]),
                min_tenure_months=data["min_tenure_months"],
                max_tenure_months=data["max_tenure_months"],
                default_tenure_months=data["default_tenure_months"],
                allows_moratorium=True,
                max_moratorium_months=data["max_moratorium_months"],
                moratorium_type="INTEREST_ONLY",
                interest_type=InterestType.FLOATING,
                base_rate_id=base_rate.id if base_rate else None,
                min_spread_bps=100,
                max_spread_bps=650,
                default_spread_bps=data["default_spread_bps"],
                min_effective_rate=money("8.00"),
                max_effective_rate=money("18.00"),
                rate_reset_frequency=RateResetFrequency.QUARTERLY,
                day_count_convention=DayCountConvention.ACT_365,
                interest_calculation_method="REDUCING_BALANCE",
                interest_compounding="MONTHLY",
                allowed_repayment_frequencies=["MONTHLY", "QUARTERLY", "HALF_YEARLY", "BULLET"],
                default_repayment_frequency=data["default_repayment_frequency"],
                allowed_repayment_modes=["EMI", "STRUCTURED", "BULLET", "BALLOON"],
                default_repayment_mode=data["default_repayment_mode"],
                allows_prepayment=True,
                prepayment_lock_in_months=12,
                allows_foreclosure=True,
                foreclosure_lock_in_months=12,
                requires_collateral=True,
                min_collateral_coverage=money(data["min_collateral_coverage"]),
                allowed_security_types=[
                    "IMMOVABLE_PROPERTY",
                    "PLANT_MACHINERY",
                    "RECEIVABLES",
                    "FIXED_DEPOSIT",
                    "CORPORATE_GUARANTEE",
                ],
                requires_guarantee=False,
                eligible_entity_types=["CORPORATE", "LLP", "PARTNERSHIP"],
                min_vintage_months=24,
                min_turnover=money("50000000"),
                min_rating_grade="BBB",
                max_debt_equity_ratio=money("3.00"),
                min_current_ratio=money("1.10"),
                min_dscr=money(data["min_dscr"]),
                disbursement_type=data["disbursement_type"],
                max_tranches=data["max_tranches"],
                allows_partial_disbursement=True,
                disbursement_validity_days=365,
                is_active_for_new_loans=True,
                effective_from=datetime.now(UTC).date().replace(month=4, day=1),
            )
            session.add(product)
            await session.flush()
            created_products += 1

        for idx, fee in enumerate(fee_map.values(), start=1):
            existing_link = await session.execute(
                select(ProductFee).where(
                    ProductFee.product_id == product.id,
                    ProductFee.fee_master_id == fee.id,
                )
            )
            if not existing_link.scalar_one_or_none():
                session.add(
                    ProductFee(
                        product_id=product.id,
                        fee_master_id=fee.id,
                        is_mandatory=fee.code != "PREPAYMENT_FEE",
                        is_waivable=True,
                        max_waiver_percentage=money("100"),
                        display_order=idx,
                    )
                )
                created_product_fees += 1

        for idx, (code, name, category, stage, mandatory) in enumerate(DOCUMENT_CHECKLIST, start=1):
            existing_doc = await session.execute(
                select(DocumentChecklist).where(
                    DocumentChecklist.product_id == product.id,
                    DocumentChecklist.code == code,
                )
            )
            if existing_doc.scalar_one_or_none():
                continue
            session.add(
                DocumentChecklist(
                    product_id=product.id,
                    code=code,
                    name=name,
                    description=f"{name} required for {product.name}",
                    category=category,
                    required_at_stage=stage,
                    is_mandatory=mandatory,
                    is_mandatory_for_disbursement=stage == DocumentStage.PRE_DISBURSEMENT,
                    applicable_entity_types=["CORPORATE", "LLP"],
                    allowed_file_types=["pdf", "jpg", "jpeg", "png"],
                    max_file_size_mb=25,
                    min_file_count=1,
                    max_file_count=10,
                    requires_verification=True,
                    verification_instructions="Verify manually before approval/disbursement.",
                    display_order=idx,
                    help_text=(
                        "Upload clear scanned copies. External portal upload is not "
                        "enabled in this release."
                    ),
                )
            )
            created_docs += 1

    # Approval checklist template
    template = (
        await session.execute(
            select(ApprovalChecklistTemplate).where(
                ApprovalChecklistTemplate.organization_id == org.id,
                ApprovalChecklistTemplate.code == "CORP_LOAN_APPROVAL",
            )
        )
    ).scalar_one_or_none()
    created_template_items = 0
    if not template:
        template = ApprovalChecklistTemplate(
            organization_id=org.id,
            code="CORP_LOAN_APPROVAL",
            name="Corporate Loan Approval Checklist",
            description="Default approval checklist for institutional lending",
            applies_to=ChecklistAppliesTo.LOAN_APPLICATION.value,
            is_default=True,
        )
        session.add(template)
        await session.flush()

    for idx, (code, label, category, mandatory, evidence) in enumerate(
        APPROVAL_CHECKLIST_ITEMS, start=1
    ):
        existing_item = await session.execute(
            select(ApprovalChecklistTemplateItem).where(
                ApprovalChecklistTemplateItem.template_id == template.id,
                ApprovalChecklistTemplateItem.code == code,
            )
        )
        if existing_item.scalar_one_or_none():
            continue
        session.add(
            ApprovalChecklistTemplateItem(
                template_id=template.id,
                code=code,
                label=label,
                description=label,
                category=category.value,
                is_mandatory=mandatory,
                sort_order=idx,
                default_due_offset_days=7,
                requires_evidence=evidence,
            )
        )
        created_template_items += 1

    # Interest Incentivization Fund basics
    scheme = (
        await session.execute(
            select(SubventionScheme).where(
                SubventionScheme.organization_id == org.id,
                SubventionScheme.scheme_code == "IIF_DEFAULT",
            )
        )
    ).scalar_one_or_none()
    if not scheme:
        scheme = SubventionScheme(
            organization_id=org.id,
            scheme_code="IIF_DEFAULT",
            scheme_name="Interest Incentivization Fund",
            administering_ministry="Ministry of Ports, Shipping and Waterways",
            implementing_agency="Sagarmala Finance Corporation Limited",
            subvention_rate_percent=money("3.00"),
            max_subvention_per_beneficiary=money("10000000000"),
            scheme_corpus=money("50000000000"),
            eligible_loan_types=[
                IIFLoanType.TERM_LOAN_CAPEX.value,
                IIFLoanType.WORKING_CAPITAL.value,
            ],
            max_tenure_term_loan_months=180,
            max_tenure_working_capital_months=60,
            scheme_start_date=date(2025, 9, 24),
            scheme_end_date=date(2036, 3, 31),
            eligibility_window_months=36,
            claim_frequency=ClaimFrequency.QUARTERLY.value,
            npa_disqualification_dpd_days=30,
            description="Default IIF scheme master. Tenants may customise or disable it later.",
        )
        session.add(scheme)
        await session.flush()

    fuc = (
        await session.execute(
            select(FundUtilizationCategory).where(
                FundUtilizationCategory.organization_id == org.id,
                FundUtilizationCategory.scheme_id == scheme.id,
                FundUtilizationCategory.code == "PORT_INFRA",
            )
        )
    ).scalar_one_or_none()
    if not fuc:
        session.add(
            FundUtilizationCategory(
                organization_id=org.id,
                scheme_id=scheme.id,
                code="PORT_INFRA",
                label="Port and maritime infrastructure",
                description=(
                    "Eligible port, terminal, shipyard, logistics and related maritime assets"
                ),
                sort_order=1,
            )
        )

    # Source lenders / funding master
    created_lenders = 0
    for data in SOURCE_LENDERS:
        existing_lender = await session.execute(
            select(Lender).where(
                Lender.organization_id == org.id,
                Lender.lender_code == data["lender_code"],
            )
        )
        if existing_lender.scalar_one_or_none():
            continue
        session.add(
            Lender(
                organization_id=org.id,
                lender_code=data["lender_code"],
                lender_name=data["lender_name"],
                lender_type=data["lender_type"],
                status=data["status"],
                contact_person=data["contact_person"],
                contact_email=data["contact_email"],
                contact_phone=data["contact_phone"],
                external_rating=data["external_rating"],
                rating_agency=data["rating_agency"],
                rating_date=datetime.now(UTC).date(),
                total_sanction_limit=money(data["total_sanction_limit"]),
                available_limit=money(data["available_limit"]),
                remarks="Seeded default source lender. No integration is configured.",
                updated_at=datetime.now(UTC),
            )
        )
        created_lenders += 1

    await session.commit()
    print(
        "  + Lending masters ready "
        f"(rates:{created_rates}, fees:{created_fees}, products:{created_products}, "
        f"product-fees:{created_product_fees}, documents:{created_docs}, "
        f"checklist-items:{created_template_items}, lenders:{created_lenders})"
    )


async def seed_hris_masters(session, org):
    """Seed HRIS leave, shift and holiday masters."""
    print("\nSeeding HRIS masters...")
    created_leave = created_shift = created_holidays = 0

    for (
        code,
        name,
        category,
        quota,
        carry,
        max_carry,
        encash,
        max_encash,
        doc,
        doc_after,
        order,
    ) in LEAVE_TYPES:
        existing = (
            await session.execute(
                select(LeaveType).where(
                    LeaveType.organization_id == org.id,
                    LeaveType.leave_code == code,
                )
            )
        ).scalar_one_or_none()
        if existing:
            continue
        session.add(
            LeaveType(
                organization_id=org.id,
                leave_code=code,
                leave_name=name,
                category=category,
                description=f"Default {name} policy. HR may customise quota and approval rules.",
                annual_quota=money(quota),
                max_accumulation=money(max_carry) if max_carry is not None else None,
                accrual_type="YEARLY" if quota else "NONE",
                carry_forward_allowed=carry,
                max_carry_forward=money(max_carry) if max_carry is not None else None,
                encashment_allowed=encash,
                max_encashment_days=money(max_encash) if max_encash is not None else None,
                encashment_on_separation=encash,
                document_required=doc,
                document_required_after_days=doc_after,
                is_paid=category != LeaveCategory.LOP,
                display_order=order,
            )
        )
        created_leave += 1

    for code, name, shift_type, start, end, break_start, break_end, break_mins in SHIFT_MASTERS:
        existing = (
            await session.execute(
                select(Shift).where(
                    Shift.organization_id == org.id,
                    Shift.shift_code == code,
                )
            )
        ).scalar_one_or_none()
        if existing:
            continue
        session.add(
            Shift(
                organization_id=org.id,
                shift_code=code,
                shift_name=name,
                shift_type=shift_type,
                start_time=start,
                end_time=end,
                break_start_time=break_start,
                break_end_time=break_end,
                break_duration_minutes=break_mins,
                working_hours=480,
                half_day_hours=240,
                week_off_days=["SATURDAY", "SUNDAY"],
                description="Default shift master seeded for manual attendance workflows.",
            )
        )
        created_shift += 1

    calendar = (
        await session.execute(
            select(HolidayCalendar).where(
                HolidayCalendar.organization_id == org.id,
                HolidayCalendar.year == 2026,
                HolidayCalendar.calendar_name == "Default Holiday Calendar",
            )
        )
    ).scalar_one_or_none()
    if not calendar:
        calendar = HolidayCalendar(
            organization_id=org.id,
            year=2026,
            calendar_name="Default Holiday Calendar",
            description="Default Indian holiday calendar for initial HRIS setup.",
        )
        session.add(calendar)
        await session.flush()

    for holiday_date, name, holiday_type in HOLIDAYS_2026:
        existing = (
            await session.execute(
                select(Holiday).where(
                    Holiday.calendar_id == calendar.id,
                    Holiday.holiday_date == holiday_date,
                )
            )
        ).scalar_one_or_none()
        if existing:
            continue
        session.add(
            Holiday(
                calendar_id=calendar.id,
                holiday_date=holiday_date,
                holiday_name=name,
                holiday_type=holiday_type,
                description="Seeded holiday; HR may adjust based on annual policy.",
            )
        )
        created_holidays += 1

    await session.commit()
    print(
        f"  + HRIS masters ready (leave:{created_leave}, shifts:{created_shift}, "
        f"holidays:{created_holidays})"
    )


async def seed_payroll_masters(session, org):
    """Seed payroll salary components, structure and statutory setup."""
    print("\nSeeding payroll masters...")
    created_components = created_structure_lines = created_statutory = 0
    component_map = {}

    for (
        code,
        name,
        comp_type,
        category,
        calc_type,
        value,
        taxable,
        affects_pf,
        affects_esi,
        gratuity,
    ) in SALARY_COMPONENTS:
        component = (
            await session.execute(
                select(SalaryComponent).where(
                    SalaryComponent.organization_id == org.id,
                    SalaryComponent.component_code == code,
                )
            )
        ).scalar_one_or_none()
        if not component:
            component = SalaryComponent(
                organization_id=org.id,
                component_code=code,
                component_name=name,
                description=f"Default payroll component for {name}.",
                component_type=comp_type,
                category=category,
                calculation_type=calc_type,
                default_value=money(value) if value is not None else None,
                formula="GROSS - BASIC - HRA - CONV" if code == "SPL" else None,
                is_taxable=taxable,
                is_part_of_basic=code == "BASIC",
                is_part_of_gross=comp_type == ComponentType.EARNING,
                is_part_of_ctc=True,
                affects_pf=affects_pf,
                affects_esi=affects_esi,
                affects_pt=comp_type == ComponentType.EARNING,
                affects_gratuity=gratuity,
                display_order=len(component_map) + 1,
            )
            session.add(component)
            await session.flush()
            created_components += 1
        component_map[code] = component

    structure = (
        await session.execute(
            select(SalaryStructure).where(
                SalaryStructure.organization_id == org.id,
                SalaryStructure.structure_code == "STD_PAY",
            )
        )
    ).scalar_one_or_none()
    if not structure:
        structure = SalaryStructure(
            organization_id=org.id,
            structure_code="STD_PAY",
            structure_name="Standard Monthly Payroll Structure",
            description="Default salary structure for monthly payroll.",
            effective_from=date(2026, 4, 1),
            payment_mode="BANK",
            pay_frequency="MONTHLY",
        )
        session.add(structure)
        await session.flush()

    for code, component in component_map.items():
        existing_link = (
            await session.execute(
                select(SalaryStructureComponent).where(
                    SalaryStructureComponent.structure_id == structure.id,
                    SalaryStructureComponent.component_id == component.id,
                )
            )
        ).scalar_one_or_none()
        if existing_link:
            continue
        session.add(
            SalaryStructureComponent(
                structure_id=structure.id,
                component_id=component.id,
                calculation_type=component.calculation_type,
                value=component.default_value,
                formula=component.formula,
                is_mandatory=code in {"BASIC", "HRA", "SPL"},
            )
        )
        created_structure_lines += 1

    statutory_setups = [
        (
            "PF",
            dict(
                pf_employer_rate=money("3.67"),
                eps_employer_rate=money("8.33"),
                pf_employee_rate=money("12.00"),
                pf_admin_charge_rate=money("0.50"),
                pf_edli_rate=money("0.50"),
                pf_wage_ceiling=money("15000"),
                eps_wage_ceiling=money("15000"),
            ),
        ),
        (
            "ESI",
            dict(
                esi_employer_rate=money("3.25"),
                esi_employee_rate=money("0.75"),
                esi_wage_ceiling=money("21000"),
            ),
        ),
        (
            "PT",
            dict(
                pt_state="Maharashtra",
                pt_slabs={
                    "monthly": [
                        {"from": 0, "to": 7500, "amount": 0},
                        {"from": 7501, "to": 10000, "amount": 175},
                        {"from": 10001, "to": None, "amount": 200},
                    ]
                },
            ),
        ),
    ]
    for statutory_type, values in statutory_setups:
        existing = (
            await session.execute(
                select(StatutorySetup).where(
                    StatutorySetup.organization_id == org.id,
                    StatutorySetup.statutory_type == statutory_type,
                )
            )
        ).scalar_one_or_none()
        if existing:
            continue
        session.add(
            StatutorySetup(
                organization_id=org.id,
                statutory_type=statutory_type,
                effective_from=date(2026, 4, 1),
                **values,
            )
        )
        created_statutory += 1

    await session.commit()
    print(
        "  + Payroll masters ready "
        f"(components:{created_components}, structure-lines:{created_structure_lines}, "
        f"statutory:{created_statutory})"
    )


async def seed_fixed_assets_masters(session, org):
    """Seed fixed-asset configuration and categories."""
    print("\nSeeding fixed assets masters...")
    created_categories = 0

    config = (
        await session.execute(
            select(FAConfiguration).where(FAConfiguration.organization_id == org.id)
        )
    ).scalar_one_or_none()
    if not config:
        session.add(
            FAConfiguration(
                organization_id=org.id,
                asset_code_prefix="FA",
                creation_approval_threshold=money("1000000"),
                min_asset_value_for_depreciation=money("5000"),
            )
        )

    accounts = {
        account.code: account
        for account in (
            await session.execute(select(Account).where(Account.organization_id == org.id))
        ).scalars()
    }

    for (
        code,
        name,
        asset_type,
        method,
        life,
        residual,
        slm_rate,
        it_rate,
        insurance,
        amc,
    ) in FIXED_ASSET_CATEGORIES:
        existing = (
            await session.execute(
                select(AssetCategory).where(
                    AssetCategory.organization_id == org.id,
                    AssetCategory.category_code == code,
                )
            )
        ).scalar_one_or_none()
        if existing:
            continue
        session.add(
            AssetCategory(
                organization_id=org.id,
                category_code=code,
                category_name=name,
                description=f"Default fixed asset category for {name}.",
                asset_type=asset_type,
                depreciation_method=method,
                useful_life_years=life,
                residual_value_pct=money(residual),
                depreciation_rate_slm=money(slm_rate),
                depreciation_rate_wdv=money(it_rate),
                it_act_rate=money(it_rate),
                capitalization_threshold=money("5000"),
                gl_asset_account_id=accounts.get("1501").id if accounts.get("1501") else None,
                gl_accum_dep_account_id=accounts.get("1507").id if accounts.get("1507") else None,
                gl_dep_expense_account_id=accounts.get("5302").id if accounts.get("5302") else None,
                requires_insurance=insurance,
                requires_amc=amc,
            )
        )
        created_categories += 1

    await session.commit()
    print(f"  + Fixed assets masters ready (categories:{created_categories})")


async def seed_fixed_deposit_masters(session, org):
    """Seed fixed deposit products and rate slabs."""
    print("\nSeeding fixed deposit masters...")
    created_products = created_slabs = 0
    accounts = {
        account.code: account
        for account in (
            await session.execute(select(Account).where(Account.organization_id == org.id))
        ).scalars()
    }

    for code, name, min_days, max_days, min_amount, payout, compounding in FD_PRODUCTS:
        product = (
            await session.execute(
                select(FDProduct).where(
                    FDProduct.organization_id == org.id,
                    FDProduct.product_code == code,
                )
            )
        ).scalar_one_or_none()
        if not product:
            product = FDProduct(
                organization_id=org.id,
                product_code=code,
                product_name=name,
                description="Default FD product for treasury placement/monitoring.",
                min_tenure_days=min_days,
                max_tenure_days=max_days,
                min_amount=money(min_amount),
                max_amount=None,
                interest_payout_frequency=payout,
                compounding_frequency=compounding,
                tds_threshold=money("40000"),
                fd_liability_account_id=accounts.get("2104").id if accounts.get("2104") else None,
                interest_expense_account_id=accounts.get("5001").id
                if accounts.get("5001")
                else None,
                tds_payable_account_id=accounts.get("2201").id if accounts.get("2201") else None,
                effective_from=date(2026, 4, 1),
            )
            session.add(product)
            await session.flush()
            created_products += 1

        for min_tenure, max_tenure, rate in FD_INTEREST_SLABS:
            existing_slab = (
                await session.execute(
                    select(FDInterestSlab).where(
                        FDInterestSlab.product_id == product.id,
                        FDInterestSlab.customer_category == FDCustomerCategory.CORPORATE,
                        FDInterestSlab.min_tenure_days == min_tenure,
                        FDInterestSlab.max_tenure_days == max_tenure,
                    )
                )
            ).scalar_one_or_none()
            if existing_slab:
                continue
            session.add(
                FDInterestSlab(
                    product_id=product.id,
                    customer_category=FDCustomerCategory.CORPORATE,
                    min_tenure_days=min_tenure,
                    max_tenure_days=max_tenure,
                    min_amount=money(min_amount),
                    interest_rate=rate,
                    effective_from=date(2026, 4, 1),
                )
            )
            created_slabs += 1

    await session.commit()
    print(f"  + Fixed deposit masters ready (products:{created_products}, slabs:{created_slabs})")


async def seed_inventory_masters(session, org, unit_map):
    """Seed inventory categories, warehouses and basic items."""
    print("\nSeeding inventory masters...")
    created_categories = created_warehouses = created_items = 0
    category_map = {}

    for code, name, stockable, serial, batch in INVENTORY_CATEGORIES:
        category = (
            await session.execute(
                select(ItemCategory).where(
                    ItemCategory.organization_id == org.id,
                    ItemCategory.category_code == code,
                )
            )
        ).scalar_one_or_none()
        if not category:
            category = ItemCategory(
                organization_id=org.id,
                category_code=code,
                category_name=name,
                description=f"Default inventory category for {name}.",
                is_stockable=stockable,
                requires_serial_number=serial,
                requires_batch_number=batch,
            )
            session.add(category)
            await session.flush()
            created_categories += 1
        category_map[code] = category

    for code, name, warehouse_type, unit_code, is_default in [
        ("MAIN", "Main Store", WarehouseType.MAIN, "HO", True),
        ("BRANCH", "Branch Store", WarehouseType.BRANCH, "BR-MUM", False),
        ("TRANSIT", "Transit Stock Location", WarehouseType.TRANSIT, None, False),
    ]:
        existing = (
            await session.execute(
                select(Warehouse).where(
                    Warehouse.organization_id == org.id,
                    Warehouse.warehouse_code == code,
                )
            )
        ).scalar_one_or_none()
        if existing:
            continue
        session.add(
            Warehouse(
                organization_id=org.id,
                unit_id=unit_map.get(unit_code).id
                if unit_code and unit_map.get(unit_code)
                else None,
                warehouse_code=code,
                warehouse_name=name,
                description="Default warehouse seeded for manual stock workflows.",
                warehouse_type=warehouse_type,
                city="Mumbai",
                state="Maharashtra",
                pincode="400051",
                is_default=is_default,
            )
        )
        created_warehouses += 1

    for (
        code,
        name,
        category_code,
        item_type,
        uom,
        cost,
        minimum,
        maximum,
        reorder,
        hsn,
        gst,
    ) in INVENTORY_ITEMS:
        existing = (
            await session.execute(
                select(ItemMaster).where(
                    ItemMaster.organization_id == org.id,
                    ItemMaster.item_code == code,
                )
            )
        ).scalar_one_or_none()
        if existing or category_code not in category_map:
            continue
        session.add(
            ItemMaster(
                organization_id=org.id,
                category_id=category_map[category_code].id,
                item_code=code,
                item_name=name,
                description=f"Default inventory item for {name}.",
                item_type=item_type,
                uom=uom,
                is_stockable=item_type != ItemType.SERVICE,
                minimum_stock_level=Decimal(str(minimum)),
                maximum_stock_level=Decimal(str(maximum)),
                reorder_quantity=Decimal(str(reorder)),
                standard_cost=Decimal(str(cost)),
                hsn_code=hsn,
                gst_rate=money(gst),
            )
        )
        created_items += 1

    await session.commit()
    print(
        "  + Inventory masters ready "
        f"(categories:{created_categories}, warehouses:{created_warehouses}, items:{created_items})"
    )


async def seed_compliance_masters(session, org, admin_user):
    """Seed compliance calendar masters."""
    print("\nSeeding compliance masters...")
    created_count = 0
    for code, name, body, frequency, due_day, priority, form_name, department in COMPLIANCE_ITEMS:
        existing = (
            await session.execute(
                select(ComplianceItem).where(
                    ComplianceItem.organization_id == org.id,
                    ComplianceItem.item_code == code,
                )
            )
        ).scalar_one_or_none()
        if existing:
            continue
        session.add(
            ComplianceItem(
                organization_id=org.id,
                item_code=code,
                item_name=name,
                description=f"Manual-first compliance tracker for {name}.",
                regulatory_body=body,
                frequency=frequency,
                due_day=due_day,
                grace_days=0,
                priority=priority,
                responsible_designation="Department Head",
                department=department,
                form_name=form_name,
                required_documents=["working_file", "approval", "acknowledgement"],
                filing_portal=None,
                effective_from=date(2026, 4, 1),
                created_by=admin_user.id if admin_user else None,
            )
        )
        created_count += 1

    await session.commit()
    print(f"  + Compliance masters ready (items:{created_count})")


async def seed_dms_masters(session, org):
    """Seed DMS root folders and standard tags."""
    print("\nSeeding DMS masters...")
    created_folders = created_tags = 0

    for idx, (name, slug, description, color, icon) in enumerate(DMS_FOLDERS, start=1):
        path = f"/{slug}"
        existing = (
            await session.execute(
                select(DMSFolder).where(
                    DMSFolder.organization_id == org.id,
                    DMSFolder.path == path,
                )
            )
        ).scalar_one_or_none()
        if existing:
            continue
        session.add(
            DMSFolder(
                organization_id=org.id,
                name=name,
                description=description,
                path=path,
                level=0,
                folder_type="system",
                access_level=DocumentAccessLevel.ORGANIZATION.value,
                color=color,
                icon=icon,
                sort_order=idx,
                folder_metadata={"seeded": True, "manualFirst": True},
            )
        )
        created_folders += 1

    for name, slug, category, color in DMS_TAGS:
        existing = (
            await session.execute(
                select(DMSTag).where(DMSTag.organization_id == org.id, DMSTag.slug == slug)
            )
        ).scalar_one_or_none()
        if existing:
            continue
        session.add(
            DMSTag(
                organization_id=org.id,
                name=name,
                slug=slug,
                description=f"Default DMS tag: {name}.",
                color=color,
                category=category,
            )
        )
        created_tags += 1

    await session.commit()
    print(f"  + DMS masters ready (folders:{created_folders}, tags:{created_tags})")


async def seed_ess_masters(session, org):
    """Seed ESS IT declaration, reimbursement and helpdesk masters."""
    print("\nSeeding ESS masters...")
    created_it = created_reimbursements = created_helpdesk = 0

    for idx, (code, name, category, limit, proof_types) in enumerate(
        IT_DECLARATION_SECTIONS, start=1
    ):
        existing = (
            await session.execute(
                select(ITDeclarationMaster).where(
                    ITDeclarationMaster.organization_id == org.id,
                    ITDeclarationMaster.section_code == code,
                )
            )
        ).scalar_one_or_none()
        if existing:
            continue
        session.add(
            ITDeclarationMaster(
                organization_id=org.id,
                section_code=code,
                section_name=name,
                description=f"Default Indian income-tax declaration section {code}.",
                category=category,
                max_limit=money(limit),
                applicable_from_fy="2026-27",
                requires_proof=True,
                proof_types=proof_types,
                display_order=idx,
                help_text=(
                    "Employee enters declaration manually; payroll validates before processing."
                ),
                applicable_in_old_regime=True,
                applicable_in_new_regime=code in {"80CCD_2"},
            )
        )
        created_it += 1

    for code, name, claim_type, per_claim, per_year in REIMBURSEMENT_CATEGORIES:
        existing = (
            await session.execute(
                select(ReimbursementCategory).where(
                    ReimbursementCategory.organization_id == org.id,
                    ReimbursementCategory.code == code,
                )
            )
        ).scalar_one_or_none()
        if existing:
            continue
        session.add(
            ReimbursementCategory(
                organization_id=org.id,
                code=code,
                name=name,
                description=f"Default reimbursement category for {name}.",
                claim_type=claim_type,
                max_amount_per_claim=money(per_claim),
                max_amount_per_year=money(per_year),
                requires_approval=True,
                requires_bills=True,
            )
        )
        created_reimbursements += 1

    for code, name, category, department, response_sla, resolution_sla in HELPDESK_CATEGORIES:
        existing = (
            await session.execute(
                select(TicketCategoryMaster).where(
                    TicketCategoryMaster.organization_id == org.id,
                    TicketCategoryMaster.code == code,
                )
            )
        ).scalar_one_or_none()
        if existing:
            continue
        session.add(
            TicketCategoryMaster(
                organization_id=org.id,
                code=code,
                name=name,
                description=f"Default ESS helpdesk category for {name}.",
                category_type=category,
                department=department,
                response_sla_hours=response_sla,
                resolution_sla_hours=resolution_sla,
                enable_escalation=True,
                escalation_after_hours=resolution_sla,
            )
        )
        created_helpdesk += 1

    await session.commit()
    print(
        "  + ESS masters ready "
        f"(it-sections:{created_it}, reimbursements:{created_reimbursements}, "
        f"helpdesk:{created_helpdesk})"
    )


async def seed_legal_masters(session, org):
    """Seed legal recovery master data."""
    print("\nSeeding legal masters...")
    created_expense = created_periods = created_courts = created_fee_slabs = 0

    for code, name, category_type, tds, tds_section, gst, order in LEGAL_EXPENSE_CATEGORIES:
        existing = (
            await session.execute(
                select(ExpenseCategory).where(
                    ExpenseCategory.organization_id == org.id,
                    ExpenseCategory.category_code == code,
                )
            )
        ).scalar_one_or_none()
        if existing:
            continue
        session.add(
            ExpenseCategory(
                organization_id=org.id,
                category_code=code,
                category_name=name,
                category_type=category_type,
                tds_applicable=tds,
                tds_section=tds_section,
                tds_rate=money("10.00") if tds else None,
                gst_applicable=gst,
                gst_rate=money("18.00") if gst else None,
                hsn_sac_code="9982" if gst else None,
                recoverable_from_borrower=True,
                recovery_priority=order,
                display_order=order,
                description=f"Default legal expense category for {name}.",
            )
        )
        created_expense += 1

    for code, name, act, section, days, description, start_event, consequence in STATUTORY_PERIODS:
        existing = (
            await session.execute(
                select(StatutoryPeriod).where(
                    StatutoryPeriod.organization_id == org.id,
                    StatutoryPeriod.provision_code == code,
                )
            )
        ).scalar_one_or_none()
        if existing:
            continue
        session.add(
            StatutoryPeriod(
                organization_id=org.id,
                provision_code=code,
                provision_name=name,
                act_name=act,
                section_reference=section,
                period_days=days,
                period_description=description,
                start_event=start_event,
                includes_holidays=True,
                extension_allowed=False,
                consequence=consequence,
                alert_before_days=[30, 15, 7, 1],
                description=f"Default statutory period for {name}.",
            )
        )
        created_periods += 1

    for code, name, court_type, jurisdiction, state, state_code in COURT_MASTERS:
        court = (
            await session.execute(
                select(Court).where(
                    Court.organization_id == org.id,
                    Court.court_code == code,
                )
            )
        ).scalar_one_or_none()
        if not court:
            court = Court(
                organization_id=org.id,
                court_code=code,
                court_name=name,
                court_type=court_type,
                short_name=code,
                jurisdiction=jurisdiction,
                address_line1="Manual court master - update exact address",
                city="Mumbai",
                district=state,
                state_code=state_code,
                country="IN",
                pincode="400001",
                working_days=["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"],
                working_hours="10:30-16:30",
                filing_time="10:30-15:00",
                e_filing_enabled=False,
                is_operational=True,
            )
            session.add(court)
            await session.flush()
            created_courts += 1

        existing_slab = (
            await session.execute(
                select(CourtFeeSlab).where(
                    CourtFeeSlab.court_id == court.id,
                    CourtFeeSlab.fee_type == "FILING",
                    CourtFeeSlab.min_claim_amount == money("0"),
                )
            )
        ).scalar_one_or_none()
        if not existing_slab:
            session.add(
                CourtFeeSlab(
                    court_id=court.id,
                    organization_id=org.id,
                    court_type=court_type,
                    fee_type="FILING",
                    min_claim_amount=money("0"),
                    max_claim_amount=None,
                    calculation_type="FIXED",
                    fixed_fee=money("1000"),
                    min_fee=money("1000"),
                    effective_from=date(2026, 4, 1),
                )
            )
            created_fee_slabs += 1

    await session.commit()
    print(
        "  + Legal masters ready "
        f"(expense-categories:{created_expense}, periods:{created_periods}, "
        f"courts:{created_courts}, fee-slabs:{created_fee_slabs})"
    )


async def seed_notification_masters(session, org):
    """Seed notification templates for manual-first workflows."""
    print("\nSeeding notification masters...")
    created_count = 0
    for code, name, category, subject, message in NOTIFICATION_TEMPLATES:
        existing = (
            await session.execute(
                select(NotificationTemplate).where(
                    NotificationTemplate.organization_id == org.id,
                    NotificationTemplate.code == code,
                )
            )
        ).scalar_one_or_none()
        if existing:
            continue
        session.add(
            NotificationTemplate(
                organization_id=org.id,
                code=code,
                name=name,
                description=f"Default notification template for {name}.",
                template_type=NotificationTemplateType.TRANSACTIONAL,
                category=category,
                channels=["email", "in_app"],
                email_subject=subject,
                email_body_text=message,
                in_app_title=subject,
                in_app_message=message,
                variables=["item_name", "form_name", "due_date"],
                default_values={"item_name": "Item", "form_name": "Form", "due_date": "Due date"},
                is_active=True,
            )
        )
        created_count += 1

    await session.commit()
    print(f"  + Notification masters ready (templates:{created_count})")


async def seed_bi_masters(session):
    """Seed BI data sources and chart definitions."""
    print("\nSeeding BI masters...")
    created_sources = created_charts = 0
    source_map = {}
    for code, name, endpoint, module in BI_DATA_SOURCES:
        source = (
            await session.execute(select(DataSource).where(DataSource.code == code))
        ).scalar_one_or_none()
        if not source:
            source = DataSource(
                code=code,
                name=name,
                description=f"Default BI data source for {name}.",
                source_type=DataSourceType.API_ENDPOINT,
                api_endpoint=endpoint,
                api_method=APIMethod.GET,
                parameters_schema={"type": "object"},
                cache_ttl_seconds=300,
            )
            session.add(source)
            await session.flush()
            created_sources += 1
        source_map[code] = source

        chart_code = f"CHART_{code}"
        chart = (
            await session.execute(select(ChartDefinition).where(ChartDefinition.code == chart_code))
        ).scalar_one_or_none()
        if chart:
            continue
        session.add(
            ChartDefinition(
                code=chart_code,
                name=name,
                description=f"Default chart for {name}.",
                module=module,
                chart_type=ChartType.KPI if code == "MIS_DASHBOARD" else ChartType.TABLE,
                default_data_source_id=source.id,
                config={"seeded": True},
                data_mapping={"source": code},
                is_system=True,
            )
        )
        created_charts += 1

    await session.commit()
    print(f"  + BI masters ready (data-sources:{created_sources}, charts:{created_charts})")


# Sample Vouchers with different statuses
SAMPLE_VOUCHERS = [
    # DRAFT Vouchers - Not yet submitted
    {
        "type": "JV",
        "date": "2024-12-01",
        "narration": "Opening entry adjustment for prepaid insurance",
        "status": "DRAFT",
        "lines": [
            {
                "account": "1401",
                "debit": 25000,
                "credit": 0,
                "narration": "Prepaid Insurance - Dec portion",
            },
            {
                "account": "5404",
                "debit": 0,
                "credit": 25000,
                "narration": "Insurance Premium expense reversal",
            },
        ],
    },
    {
        "type": "PV",
        "date": "2024-12-02",
        "narration": "Professional fees payment to M/s Legal Associates",
        "status": "DRAFT",
        "lines": [
            {
                "account": "5405",
                "debit": 50000,
                "credit": 0,
                "narration": "Legal fees for loan documentation",
            },
            {"account": "1101", "debit": 0, "credit": 45000, "narration": "Payment via SBI"},
            {"account": "2201", "debit": 0, "credit": 5000, "narration": "TDS @ 10% u/s 194J"},
        ],
    },
    # PENDING_APPROVAL Vouchers - Submitted for approval
    {
        "type": "JV",
        "date": "2024-12-03",
        "narration": "Monthly salary provision for December 2024",
        "status": "PENDING_APPROVAL",
        "lines": [
            {"account": "5201", "debit": 450000, "credit": 0, "narration": "Salaries for Dec 2024"},
            {
                "account": "5204",
                "debit": 54000,
                "credit": 0,
                "narration": "PF Contribution - Employer",
            },
            {
                "account": "5205",
                "debit": 16875,
                "credit": 0,
                "narration": "ESI Contribution - Employer",
            },
            {"account": "2101", "debit": 0, "credit": 385000, "narration": "Net Salaries Payable"},
            {
                "account": "2204",
                "debit": 0,
                "credit": 108000,
                "narration": "PF Payable (Employee + Employer)",
            },
            {
                "account": "2205",
                "debit": 0,
                "credit": 27875,
                "narration": "ESI Payable (Employee + Employer)",
            },
        ],
    },
    {
        "type": "PV",
        "date": "2024-12-04",
        "narration": "Office rent payment for December 2024",
        "status": "PENDING_APPROVAL",
        "lines": [
            {
                "account": "5401",
                "debit": 150000,
                "credit": 0,
                "narration": "Office Rent - Dec 2024",
            },
            {"account": "1402", "debit": 27000, "credit": 0, "narration": "GST Input Credit @ 18%"},
            {"account": "1101", "debit": 0, "credit": 162000, "narration": "Payment via SBI"},
            {"account": "2201", "debit": 0, "credit": 15000, "narration": "TDS @ 10% u/s 194I"},
        ],
    },
    {
        "type": "RV",
        "date": "2024-12-05",
        "narration": "Processing fee received from loan customer ABC Corp",
        "status": "PENDING_APPROVAL",
        "lines": [
            {"account": "1102", "debit": 118000, "credit": 0, "narration": "Received in HDFC Bank"},
            {"account": "4101", "debit": 0, "credit": 100000, "narration": "Processing Fee Income"},
            {"account": "2202", "debit": 0, "credit": 18000, "narration": "GST Collected @ 18%"},
        ],
    },
    # APPROVED Vouchers - Approved but not posted
    {
        "type": "JV",
        "date": "2024-12-06",
        "narration": "Depreciation provision for November 2024",
        "status": "APPROVED",
        "lines": [
            {
                "account": "5302",
                "debit": 12500,
                "credit": 0,
                "narration": "Depreciation - Furniture",
            },
            {
                "account": "5303",
                "debit": 8500,
                "credit": 0,
                "narration": "Depreciation - Equipment",
            },
            {
                "account": "5304",
                "debit": 25000,
                "credit": 0,
                "narration": "Depreciation - Vehicles",
            },
            {
                "account": "1507",
                "debit": 0,
                "credit": 46000,
                "narration": "Accumulated Depreciation",
            },
        ],
    },
    {
        "type": "CV",
        "date": "2024-12-07",
        "narration": "Transfer from HDFC to SBI for salary payment",
        "status": "APPROVED",
        "lines": [
            {"account": "1101", "debit": 500000, "credit": 0, "narration": "Transfer to SBI"},
            {"account": "1102", "debit": 0, "credit": 500000, "narration": "Transfer from HDFC"},
        ],
    },
    # POSTED Vouchers - Fully processed
    {
        "type": "JV",
        "date": "2024-11-30",
        "narration": "Interest income accrual for November 2024",
        "status": "POSTED",
        "lines": [
            {
                "account": "1404",
                "debit": 285000,
                "credit": 0,
                "narration": "Interest accrued on loans",
            },
            {
                "account": "4001",
                "debit": 0,
                "credit": 285000,
                "narration": "Interest Income - Nov 2024",
            },
        ],
    },
    {
        "type": "PV",
        "date": "2024-11-28",
        "narration": "Electricity bill payment for November 2024",
        "status": "POSTED",
        "lines": [
            {"account": "5418", "debit": 45000, "credit": 0, "narration": "Electricity Charges"},
            {"account": "1402", "debit": 8100, "credit": 0, "narration": "GST Input Credit"},
            {"account": "1101", "debit": 0, "credit": 53100, "narration": "Paid via SBI"},
        ],
    },
    {
        "type": "RV",
        "date": "2024-11-25",
        "narration": "Interest received from FD maturity",
        "status": "POSTED",
        "lines": [
            {
                "account": "1103",
                "debit": 125000,
                "credit": 0,
                "narration": "Credited to ICICI Savings",
            },
            {
                "account": "4002",
                "debit": 0,
                "credit": 125000,
                "narration": "Interest on Fixed Deposit",
            },
        ],
    },
    {
        "type": "JV",
        "date": "2024-11-20",
        "narration": "NPA provision for Q2 FY24-25",
        "status": "POSTED",
        "lines": [
            {"account": "5101", "debit": 175000, "credit": 0, "narration": "Provision for NPA"},
            {
                "account": "2503",
                "debit": 0,
                "credit": 175000,
                "narration": "Provision for Bad Debts",
            },
        ],
    },
    # REJECTED Voucher
    {
        "type": "PV",
        "date": "2024-12-08",
        "narration": "Entertainment expenses - Board meeting",
        "status": "REJECTED",
        "rejection_reason": (
            "Entertainment expenses need prior approval from CFO. Please get approval and resubmit."
        ),
        "lines": [
            {"account": "5418", "debit": 35000, "credit": 0, "narration": "Entertainment expenses"},
            {"account": "1001", "debit": 0, "credit": 35000, "narration": "Paid from petty cash"},
        ],
    },
]


async def seed_vouchers(session, org, fy, admin_user):
    """Seed sample vouchers with different statuses."""
    print("\nSeeding sample vouchers...")

    # Check if vouchers already exist
    result = await session.execute(
        select(Voucher).where(Voucher.organization_id == org.id).limit(1)
    )
    if result.scalar_one_or_none():
        print("  - Sample vouchers already exist")
        return

    # Get voucher types
    result = await session.execute(select(VoucherType).where(VoucherType.organization_id == org.id))
    voucher_types = {vt.code: vt for vt in result.scalars().all()}

    # Get accounts
    result = await session.execute(select(Account).where(Account.organization_id == org.id))
    accounts = {acc.code: acc for acc in result.scalars().all()}

    # Get financial periods
    result = await session.execute(
        select(FinancialPeriod).where(FinancialPeriod.financial_year_id == fy.id)
    )
    periods = {p.period_number: p for p in result.scalars().all()}

    # Get head office unit
    result = await session.execute(
        select(Unit).where(Unit.organization_id == org.id, Unit.is_head_office.is_(True))
    )
    head_office = result.scalar_one_or_none()

    created_count = 0
    voucher_counters = {}  # Track voucher numbers per type

    for v_data in SAMPLE_VOUCHERS:
        vtype = voucher_types.get(v_data["type"])
        if not vtype:
            print(f"  ! Voucher type '{v_data['type']}' not found")
            continue

        # Parse date and find period
        from datetime import date

        v_date = date.fromisoformat(v_data["date"])
        period_num = v_date.month - 3 if v_date.month >= 4 else v_date.month + 9
        period = periods.get(period_num)
        if not period:
            print(f"  ! Period not found for date {v_date}")
            continue

        # Generate voucher number
        if vtype.code not in voucher_counters:
            voucher_counters[vtype.code] = 1
        else:
            voucher_counters[vtype.code] += 1

        voucher_number = f"{vtype.prefix}{fy.code[-5:]}-{voucher_counters[vtype.code]:04d}"

        # Calculate totals
        total_debit = sum(line["debit"] for line in v_data["lines"])
        total_credit = sum(line["credit"] for line in v_data["lines"])

        # Determine status
        status = VoucherStatus[v_data["status"]]

        voucher = Voucher(
            voucher_type_id=vtype.id,
            voucher_number=voucher_number,
            voucher_date=v_date,
            financial_year_id=fy.id,
            period_id=period.id,
            narration=v_data["narration"],
            total_debit=total_debit,
            total_credit=total_credit,
            status=status,
            organization_id=org.id,
            unit_id=head_office.id if head_office else None,
            created_by=admin_user.id,
        )

        # Set status-specific fields
        if status in [
            VoucherStatus.PENDING_APPROVAL,
            VoucherStatus.APPROVED,
            VoucherStatus.POSTED,
            VoucherStatus.REJECTED,
        ]:
            voucher.submitted_at = datetime.now(UTC) - timedelta(days=2)
            voucher.submitted_by = admin_user.id

        if status in [VoucherStatus.APPROVED, VoucherStatus.POSTED]:
            voucher.approved_at = datetime.now(UTC) - timedelta(days=1)
            voucher.approved_by = admin_user.id
            voucher.current_approval_level = vtype.approval_levels
            voucher.approval_status = [
                {
                    "level": 1,
                    "approved_by": str(admin_user.id),
                    "approved_at": str(voucher.approved_at),
                }
            ]

        if status == VoucherStatus.POSTED:
            voucher.posted_at = datetime.now(UTC)
            voucher.posted_by = admin_user.id

        if status == VoucherStatus.REJECTED:
            voucher.rejection_reason = v_data.get("rejection_reason", "Rejected by approver")
            voucher.current_approval_level = 0

        session.add(voucher)
        await session.flush()

        # Create voucher lines
        for idx, line_data in enumerate(v_data["lines"]):
            account = accounts.get(line_data["account"])
            if not account:
                print(f"  ! Account '{line_data['account']}' not found")
                continue

            line = VoucherLine(
                voucher_id=voucher.id,
                line_number=idx + 1,
                account_id=account.id,
                debit_amount=line_data["debit"],
                credit_amount=line_data["credit"],
                narration=line_data.get("narration"),
                created_by=admin_user.id,
            )
            session.add(line)

        created_count += 1

    await session.commit()
    print(f"  + Created {created_count} sample vouchers with various statuses")
    print("    - DRAFT: 2 vouchers")
    print("    - PENDING_APPROVAL: 3 vouchers")
    print("    - APPROVED: 2 vouchers")
    print("    - POSTED: 4 vouchers")
    print("    - REJECTED: 1 voucher")


async def main():
    """Run seed data."""
    print("=" * 60)
    print("SMFC ERP - Seed Data")
    print("=" * 60)

    # Tables are migration-managed. Run `alembic upgrade head` before this
    # script; do not call `Base.metadata.create_all()` here because some legacy
    # ORM defaults are not valid DDL on PostgreSQL.
    print("\nUsing migration-managed schema. Ensure alembic is at head.")

    async with async_session_factory() as session:
        # Seed data - Foundation
        permission_map = await seed_permissions(session)
        role_map = await seed_roles(session, permission_map)
        org = await seed_organization(session)
        unit_map = await seed_units(session, org)
        dept_map = await seed_departments(session, org)
        await seed_designations(session, dept_map)
        await seed_users(session, org, role_map, unit_map)

        # Seed data - Finance (Indian Standards)
        fy = await seed_financial_year(session, org)
        group_map = await seed_account_groups(session, org)
        await seed_accounts(session, org, group_map)
        await seed_organization_bank_accounts(session, org)
        await seed_voucher_types(session, org)

        # Seed data - GST Module
        gst_rate_map = await seed_gst_rates(session)
        await seed_hsn_sac_codes(session, gst_rate_map)
        await seed_gst_registration(session, org)

        # Seed data - TDS Module
        await seed_tds_sections(session)

        # Seed data - AP/AR Module
        await seed_payment_terms(session, org.id)

        # Seed data - Lending/Treasury Master Defaults
        await seed_lending_masters(session, org)

        # Get admin user for voucher creation
        result = await session.execute(select(User).where(User.username == ADMIN_USER["username"]))
        admin_user = result.scalar_one_or_none()

        # Seed data - remaining ERP module masters
        await seed_hris_masters(session, org)
        await seed_payroll_masters(session, org)
        await seed_fixed_assets_masters(session, org)
        await seed_fixed_deposit_masters(session, org)
        await seed_inventory_masters(session, org, unit_map)
        await seed_compliance_masters(session, org, admin_user)
        await seed_dms_masters(session, org)
        await seed_ess_masters(session, org)
        await seed_legal_masters(session, org)
        await seed_notification_masters(session, org)
        await seed_bi_masters(session)

        # Seed sample vouchers with different statuses
        if admin_user and fy:
            await seed_vouchers(session, org, fy, admin_user)

    print("\n" + "=" * 60)
    print("Seed data completed successfully!")
    print("=" * 60)
    print("\nAdmin Credentials:")
    print(f"  Username: {ADMIN_USER['username']}")
    print(f"  Email: {ADMIN_USER['email']}")
    print(f"  Password: {ADMIN_USER['password']}")
    print("\nSample User Password: Password123!")
    print("\nFinance Data Seeded:")
    print("  - Financial Year: FY2024-25 (April 2024 - March 2025)")
    print("  - Account Groups: Indian Schedule III structure")
    print("  - Accounts: 90+ sample ledgers (NBFC-focused)")
    print("  - Voucher Types: JV, PV, RV, CV, SV, PU, DN, CN")
    print("  - Sample Vouchers: 12 vouchers with various statuses")
    print("    * DRAFT: 2, PENDING_APPROVAL: 3, APPROVED: 2")
    print("    * POSTED: 4, REJECTED: 1")
    print("\nGST Data Seeded:")
    print("  - GST Rates: 0%, 5%, 12%, 18%, 28% (with cess variants)")
    print("  - HSN/SAC Codes: 24+ codes for financial/IT/professional services")
    print("  - GST Registration: Sample GSTIN with E-Invoice enabled")
    print("\nTDS Data Seeded:")
    print("  - TDS Sections: 15+ sections (192, 194C, 194J, 194I, 194H, 194A, etc.)")
    print("  - TCS Sections: 206C-1H (Sale of Goods), 206C-1G (Foreign Remittance)")
    print("  - Return Forms: 24Q (Salary), 26Q (Non-Salary), 27Q (NRI), 27EQ (TCS)")
    print("\nAP/AR Data Seeded:")
    print("  - Payment Terms: 12 standard terms (Immediate, Net 7/15/30/45/60/90, etc.)")
    print("  - Early Payment Discounts: 2/10 Net 30, 1/10 Net 30")
    print("\nLending Master Data Seeded:")
    print("  - Corporate loan products: Project Finance, Term Loan, Bridge Loan")
    print("  - Interest rates, fee masters, product fees and document checklists")
    print("  - Approval checklist template, IIF scheme/utilization category, source lenders")
    print("\nAll Module Master Data Seeded:")
    print("  - HRIS: leave types, shifts and default holiday calendar")
    print("  - Payroll: salary components, salary structure and PF/ESI/PT setup")
    print("  - Fixed Assets: configuration and asset categories")
    print("  - Fixed Deposits: FD products and corporate interest slabs")
    print("  - Inventory: categories, warehouses and starter item masters")
    print("  - Compliance: RBI/GST/TDS/MCA compliance calendar items")
    print("  - DMS: module folders and document tags")
    print("  - ESS: IT declarations, reimbursement categories and helpdesk categories")
    print("  - Legal: courts, limitation periods and legal expense categories")
    print("  - Notifications/BI: templates, data sources and chart definitions")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
