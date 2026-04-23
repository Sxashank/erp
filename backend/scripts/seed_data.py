#!/usr/bin/env python3
"""Seed initial data - permissions, roles, organization, units, departments, designations, and users."""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.database import async_session_factory, engine, Base
from app.core.security import get_password_hash
from app.core.constants import UserStatus, UnitType
from app.models.auth.role import Role, Permission, RolePermission
from app.models.auth.user import User
from app.models.auth.role import UserRole
from app.models.masters.organization import Organization
from app.models.masters.unit import Unit
from app.models.masters.department import Department
from app.models.masters.designation import Designation
from app.models.finance.financial_year import FinancialYear, FinancialPeriod
from app.models.finance.account_group import AccountGroup
from app.models.finance.account import Account
from app.models.finance.voucher_type import VoucherType
from app.models.finance.voucher import Voucher, VoucherLine
from app.models.gst.gst_rate import GSTRate
from app.models.gst.hsn_sac import HSNSAC
from app.models.gst.gst_registration import GSTRegistration
from app.models.tds.tds_section import TDSSection
from app.models.ap_ar.payment_terms import PaymentTerms
from app.core.constants import (
    AccountNature, AccountType, BalanceType, VoucherClass, VoucherStatus,
    HSNSACType, GSTRegistrationType
)
from app.config import settings
from dateutil.relativedelta import relativedelta


# Permission definitions
PERMISSIONS = [
    # Masters - Organization
    {"code": "MASTER_ORG_VIEW", "name": "View Organizations", "module": "MASTERS", "resource": "organization", "action": "READ"},
    {"code": "MASTER_ORG_CREATE", "name": "Create Organization", "module": "MASTERS", "resource": "organization", "action": "CREATE"},
    {"code": "MASTER_ORG_UPDATE", "name": "Update Organization", "module": "MASTERS", "resource": "organization", "action": "UPDATE"},
    {"code": "MASTER_ORG_DELETE", "name": "Delete Organization", "module": "MASTERS", "resource": "organization", "action": "DELETE"},

    # Masters - Unit
    {"code": "MASTER_UNIT_VIEW", "name": "View Units", "module": "MASTERS", "resource": "unit", "action": "READ"},
    {"code": "MASTER_UNIT_CREATE", "name": "Create Unit", "module": "MASTERS", "resource": "unit", "action": "CREATE"},
    {"code": "MASTER_UNIT_UPDATE", "name": "Update Unit", "module": "MASTERS", "resource": "unit", "action": "UPDATE"},
    {"code": "MASTER_UNIT_DELETE", "name": "Delete Unit", "module": "MASTERS", "resource": "unit", "action": "DELETE"},

    # Masters - Department
    {"code": "MASTER_DEPT_VIEW", "name": "View Departments", "module": "MASTERS", "resource": "department", "action": "READ"},
    {"code": "MASTER_DEPT_CREATE", "name": "Create Department", "module": "MASTERS", "resource": "department", "action": "CREATE"},
    {"code": "MASTER_DEPT_UPDATE", "name": "Update Department", "module": "MASTERS", "resource": "department", "action": "UPDATE"},
    {"code": "MASTER_DEPT_DELETE", "name": "Delete Department", "module": "MASTERS", "resource": "department", "action": "DELETE"},

    # Masters - Designation
    {"code": "MASTER_DESIG_VIEW", "name": "View Designations", "module": "MASTERS", "resource": "designation", "action": "READ"},
    {"code": "MASTER_DESIG_CREATE", "name": "Create Designation", "module": "MASTERS", "resource": "designation", "action": "CREATE"},
    {"code": "MASTER_DESIG_UPDATE", "name": "Update Designation", "module": "MASTERS", "resource": "designation", "action": "UPDATE"},
    {"code": "MASTER_DESIG_DELETE", "name": "Delete Designation", "module": "MASTERS", "resource": "designation", "action": "DELETE"},

    # User Management
    {"code": "USER_VIEW", "name": "View Users", "module": "USER_MGMT", "resource": "user", "action": "READ"},
    {"code": "USER_CREATE", "name": "Create User", "module": "USER_MGMT", "resource": "user", "action": "CREATE"},
    {"code": "USER_UPDATE", "name": "Update User", "module": "USER_MGMT", "resource": "user", "action": "UPDATE"},
    {"code": "USER_DELETE", "name": "Delete User", "module": "USER_MGMT", "resource": "user", "action": "DELETE"},
    {"code": "USER_ROLE_ASSIGN", "name": "Assign Roles to User", "module": "USER_MGMT", "resource": "user", "action": "UPDATE"},
    {"code": "USER_UNLOCK", "name": "Unlock User Account", "module": "USER_MGMT", "resource": "user", "action": "UPDATE"},
    {"code": "USER_RESET_PASSWORD", "name": "Reset User Password", "module": "USER_MGMT", "resource": "user", "action": "UPDATE"},

    # Role Management
    {"code": "ROLE_VIEW", "name": "View Roles", "module": "USER_MGMT", "resource": "role", "action": "READ"},
    {"code": "ROLE_CREATE", "name": "Create Role", "module": "USER_MGMT", "resource": "role", "action": "CREATE"},
    {"code": "ROLE_UPDATE", "name": "Update Role", "module": "USER_MGMT", "resource": "role", "action": "UPDATE"},
    {"code": "ROLE_DELETE", "name": "Delete Role", "module": "USER_MGMT", "resource": "role", "action": "DELETE"},
    {"code": "ROLE_PERMISSION_ASSIGN", "name": "Assign Permissions to Role", "module": "USER_MGMT", "resource": "role", "action": "UPDATE"},

    # Finance - Financial Year
    {"code": "FIN_FY_VIEW", "name": "View Financial Years", "module": "FINANCE", "resource": "financial_year", "action": "READ"},
    {"code": "FIN_FY_CREATE", "name": "Create Financial Year", "module": "FINANCE", "resource": "financial_year", "action": "CREATE"},
    {"code": "FIN_FY_UPDATE", "name": "Update Financial Year", "module": "FINANCE", "resource": "financial_year", "action": "UPDATE"},
    {"code": "FIN_FY_DELETE", "name": "Delete Financial Year", "module": "FINANCE", "resource": "financial_year", "action": "DELETE"},
    {"code": "FIN_FY_CLOSE", "name": "Close Financial Year/Period", "module": "FINANCE", "resource": "financial_year", "action": "APPROVE"},

    # Finance - Chart of Accounts
    {"code": "FIN_COA_VIEW", "name": "View Chart of Accounts", "module": "FINANCE", "resource": "account", "action": "READ"},
    {"code": "FIN_COA_CREATE", "name": "Create Account/Group", "module": "FINANCE", "resource": "account", "action": "CREATE"},
    {"code": "FIN_COA_UPDATE", "name": "Update Account/Group", "module": "FINANCE", "resource": "account", "action": "UPDATE"},
    {"code": "FIN_COA_DELETE", "name": "Delete Account/Group", "module": "FINANCE", "resource": "account", "action": "DELETE"},

    # Finance - Voucher Types
    {"code": "FIN_VTYPE_VIEW", "name": "View Voucher Types", "module": "FINANCE", "resource": "voucher_type", "action": "READ"},
    {"code": "FIN_VTYPE_CREATE", "name": "Create Voucher Type", "module": "FINANCE", "resource": "voucher_type", "action": "CREATE"},
    {"code": "FIN_VTYPE_UPDATE", "name": "Update Voucher Type", "module": "FINANCE", "resource": "voucher_type", "action": "UPDATE"},
    {"code": "FIN_VTYPE_DELETE", "name": "Delete Voucher Type", "module": "FINANCE", "resource": "voucher_type", "action": "DELETE"},

    # Finance - Vouchers
    {"code": "FIN_VOUCHER_VIEW", "name": "View Vouchers", "module": "FINANCE", "resource": "voucher", "action": "READ"},
    {"code": "FIN_VOUCHER_CREATE", "name": "Create Voucher", "module": "FINANCE", "resource": "voucher", "action": "CREATE"},
    {"code": "FIN_VOUCHER_UPDATE", "name": "Update Voucher", "module": "FINANCE", "resource": "voucher", "action": "UPDATE"},
    {"code": "FIN_VOUCHER_DELETE", "name": "Delete Voucher", "module": "FINANCE", "resource": "voucher", "action": "DELETE"},
    {"code": "FIN_VOUCHER_APPROVE", "name": "Approve Voucher", "module": "FINANCE", "resource": "voucher", "action": "APPROVE"},
    {"code": "FIN_VOUCHER_POST", "name": "Post Voucher to Ledger", "module": "FINANCE", "resource": "voucher", "action": "APPROVE"},
    {"code": "FIN_VOUCHER_CANCEL", "name": "Cancel Voucher", "module": "FINANCE", "resource": "voucher", "action": "DELETE"},

    # Finance - Reports
    {"code": "FIN_REPORT_VIEW", "name": "View Financial Reports", "module": "FINANCE", "resource": "report", "action": "READ"},
    {"code": "FIN_REPORT_EXPORT", "name": "Export Financial Reports", "module": "FINANCE", "resource": "report", "action": "EXPORT"},

    # AP/AR - Payment Terms
    {"code": "APAR_TERMS_VIEW", "name": "View Payment Terms", "module": "AP_AR", "resource": "payment_terms", "action": "READ"},
    {"code": "APAR_TERMS_CREATE", "name": "Create Payment Terms", "module": "AP_AR", "resource": "payment_terms", "action": "CREATE"},
    {"code": "APAR_TERMS_UPDATE", "name": "Update Payment Terms", "module": "AP_AR", "resource": "payment_terms", "action": "UPDATE"},
    {"code": "APAR_TERMS_DELETE", "name": "Delete Payment Terms", "module": "AP_AR", "resource": "payment_terms", "action": "DELETE"},

    # AP/AR - Vendors
    {"code": "APAR_VENDOR_VIEW", "name": "View Vendors", "module": "AP_AR", "resource": "vendor", "action": "READ"},
    {"code": "APAR_VENDOR_CREATE", "name": "Create Vendor", "module": "AP_AR", "resource": "vendor", "action": "CREATE"},
    {"code": "APAR_VENDOR_UPDATE", "name": "Update Vendor", "module": "AP_AR", "resource": "vendor", "action": "UPDATE"},
    {"code": "APAR_VENDOR_DELETE", "name": "Delete Vendor", "module": "AP_AR", "resource": "vendor", "action": "DELETE"},

    # AP/AR - Customers
    {"code": "APAR_CUSTOMER_VIEW", "name": "View Customers", "module": "AP_AR", "resource": "customer", "action": "READ"},
    {"code": "APAR_CUSTOMER_CREATE", "name": "Create Customer", "module": "AP_AR", "resource": "customer", "action": "CREATE"},
    {"code": "APAR_CUSTOMER_UPDATE", "name": "Update Customer", "module": "AP_AR", "resource": "customer", "action": "UPDATE"},
    {"code": "APAR_CUSTOMER_DELETE", "name": "Delete Customer", "module": "AP_AR", "resource": "customer", "action": "DELETE"},

    # AP/AR - Purchase Bills
    {"code": "APAR_BILL_VIEW", "name": "View Purchase Bills", "module": "AP_AR", "resource": "purchase_bill", "action": "READ"},
    {"code": "APAR_BILL_CREATE", "name": "Create Purchase Bill", "module": "AP_AR", "resource": "purchase_bill", "action": "CREATE"},
    {"code": "APAR_BILL_UPDATE", "name": "Update Purchase Bill", "module": "AP_AR", "resource": "purchase_bill", "action": "UPDATE"},
    {"code": "APAR_BILL_DELETE", "name": "Delete Purchase Bill", "module": "AP_AR", "resource": "purchase_bill", "action": "DELETE"},
    {"code": "APAR_BILL_APPROVE", "name": "Approve Purchase Bill", "module": "AP_AR", "resource": "purchase_bill", "action": "APPROVE"},

    # AP/AR - Sales Invoices
    {"code": "APAR_INVOICE_VIEW", "name": "View Sales Invoices", "module": "AP_AR", "resource": "sales_invoice", "action": "READ"},
    {"code": "APAR_INVOICE_CREATE", "name": "Create Sales Invoice", "module": "AP_AR", "resource": "sales_invoice", "action": "CREATE"},
    {"code": "APAR_INVOICE_UPDATE", "name": "Update Sales Invoice", "module": "AP_AR", "resource": "sales_invoice", "action": "UPDATE"},
    {"code": "APAR_INVOICE_DELETE", "name": "Delete Sales Invoice", "module": "AP_AR", "resource": "sales_invoice", "action": "DELETE"},
    {"code": "APAR_INVOICE_APPROVE", "name": "Approve Sales Invoice", "module": "AP_AR", "resource": "sales_invoice", "action": "APPROVE"},

    # AP/AR - Payments
    {"code": "APAR_PAYMENT_VIEW", "name": "View Payments", "module": "AP_AR", "resource": "payment", "action": "READ"},
    {"code": "APAR_PAYMENT_CREATE", "name": "Create Payment", "module": "AP_AR", "resource": "payment", "action": "CREATE"},
    {"code": "APAR_PAYMENT_UPDATE", "name": "Update Payment", "module": "AP_AR", "resource": "payment", "action": "UPDATE"},
    {"code": "APAR_PAYMENT_DELETE", "name": "Delete Payment", "module": "AP_AR", "resource": "payment", "action": "DELETE"},
    {"code": "APAR_PAYMENT_APPROVE", "name": "Approve Payment", "module": "AP_AR", "resource": "payment", "action": "APPROVE"},

    # AP/AR - Bank Reconciliation
    {"code": "APAR_BRS_VIEW", "name": "View Bank Reconciliation", "module": "AP_AR", "resource": "bank_reconciliation", "action": "READ"},
    {"code": "APAR_BRS_CREATE", "name": "Perform Bank Reconciliation", "module": "AP_AR", "resource": "bank_reconciliation", "action": "CREATE"},
    {"code": "APAR_BRS_APPROVE", "name": "Approve Bank Reconciliation", "module": "AP_AR", "resource": "bank_reconciliation", "action": "APPROVE"},

    # AP/AR - Reports
    {"code": "APAR_REPORT_VIEW", "name": "View AP/AR Reports", "module": "AP_AR", "resource": "report", "action": "READ"},
    {"code": "APAR_REPORT_EXPORT", "name": "Export AP/AR Reports", "module": "AP_AR", "resource": "report", "action": "EXPORT"},
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
            "MASTER_ORG_VIEW", "MASTER_ORG_UPDATE",
            "MASTER_UNIT_VIEW", "MASTER_UNIT_CREATE", "MASTER_UNIT_UPDATE", "MASTER_UNIT_DELETE",
            "MASTER_DEPT_VIEW", "MASTER_DEPT_CREATE", "MASTER_DEPT_UPDATE", "MASTER_DEPT_DELETE",
            "MASTER_DESIG_VIEW", "MASTER_DESIG_CREATE", "MASTER_DESIG_UPDATE", "MASTER_DESIG_DELETE",
            "USER_VIEW", "USER_CREATE", "USER_UPDATE", "USER_DELETE",
            "USER_ROLE_ASSIGN", "USER_UNLOCK", "USER_RESET_PASSWORD",
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
            "MASTER_UNIT_VIEW", "MASTER_UNIT_CREATE",
            "MASTER_DEPT_VIEW", "MASTER_DEPT_CREATE",
            "MASTER_DESIG_VIEW", "MASTER_DESIG_CREATE",
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
            "FIN_FY_VIEW", "FIN_FY_CREATE", "FIN_FY_UPDATE", "FIN_FY_CLOSE",
            "FIN_COA_VIEW", "FIN_COA_CREATE", "FIN_COA_UPDATE", "FIN_COA_DELETE",
            "FIN_VTYPE_VIEW", "FIN_VTYPE_CREATE", "FIN_VTYPE_UPDATE",
            "FIN_VOUCHER_VIEW", "FIN_VOUCHER_CREATE", "FIN_VOUCHER_UPDATE",
            "FIN_VOUCHER_APPROVE", "FIN_VOUCHER_POST", "FIN_VOUCHER_CANCEL",
            "FIN_REPORT_VIEW", "FIN_REPORT_EXPORT",
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
            "FIN_VOUCHER_VIEW", "FIN_VOUCHER_CREATE", "FIN_VOUCHER_UPDATE",
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
            "MASTER_DEPT_VIEW", "MASTER_DEPT_CREATE", "MASTER_DEPT_UPDATE",
            "MASTER_DESIG_VIEW", "MASTER_DESIG_CREATE", "MASTER_DESIG_UPDATE",
            "USER_VIEW", "USER_CREATE", "USER_UPDATE",
            "ROLE_VIEW",
        ],
    },
]

# Sample data
DEPARTMENTS = [
    {"code": "ADMIN", "name": "Administration", "short_name": "Admin", "cost_center_code": "CC001"},
    {"code": "FIN", "name": "Finance & Accounts", "short_name": "Finance", "cost_center_code": "CC002"},
    {"code": "HR", "name": "Human Resources", "short_name": "HR", "cost_center_code": "CC003"},
    {"code": "IT", "name": "Information Technology", "short_name": "IT", "cost_center_code": "CC004"},
    {"code": "OPS", "name": "Operations", "short_name": "Ops", "cost_center_code": "CC005"},
    {"code": "SALES", "name": "Sales & Marketing", "short_name": "Sales", "cost_center_code": "CC006"},
]

UNITS = [
    {"code": "HO", "name": "Head Office", "unit_type": "HEAD_OFFICE", "city": "Mumbai", "state_code": "27", "is_head_office": True},
    {"code": "MUM01", "name": "Mumbai Branch", "unit_type": "BRANCH", "city": "Mumbai", "state_code": "27"},
    {"code": "DEL01", "name": "Delhi Branch", "unit_type": "BRANCH", "city": "New Delhi", "state_code": "07"},
    {"code": "BLR01", "name": "Bangalore Branch", "unit_type": "BRANCH", "city": "Bangalore", "state_code": "29"},
    {"code": "CHN01", "name": "Chennai Branch", "unit_type": "BRANCH", "city": "Chennai", "state_code": "33"},
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
    "username": "krishna",
    "email": "krishna@supersight.com",
    "full_name": "Krishna Administrator",
    "password": "ChangeMe123!",
    "employee_code": "EMP001",
    "role": "SUPER_ADMIN",
}

SAMPLE_USERS = [
    {"username": "rajesh.kumar", "email": "rajesh.kumar@smfc.com", "full_name": "Rajesh Kumar", "employee_code": "EMP002", "role": "ORG_ADMIN"},
    {"username": "priya.sharma", "email": "priya.sharma@smfc.com", "full_name": "Priya Sharma", "employee_code": "EMP003", "role": "HR_MANAGER"},
    {"username": "amit.patel", "email": "amit.patel@smfc.com", "full_name": "Amit Patel", "employee_code": "EMP004", "role": "FINANCE_MANAGER"},
    {"username": "sneha.reddy", "email": "sneha.reddy@smfc.com", "full_name": "Sneha Reddy", "employee_code": "EMP005", "role": "BRANCH_MANAGER"},
    {"username": "vikram.singh", "email": "vikram.singh@smfc.com", "full_name": "Vikram Singh", "employee_code": "EMP006", "role": "OPERATOR"},
    {"username": "ananya.gupta", "email": "ananya.gupta@smfc.com", "full_name": "Ananya Gupta", "employee_code": "EMP007", "role": "VIEWER"},
    {"username": "rahul.verma", "email": "rahul.verma@smfc.com", "full_name": "Rahul Verma", "employee_code": "EMP008", "role": "OPERATOR"},
    {"username": "meera.nair", "email": "meera.nair@smfc.com", "full_name": "Meera Nair", "employee_code": "EMP009", "role": "VIEWER"},
]

# =====================================================
# FINANCE SEED DATA - Indian Standards (Schedule III)
# =====================================================

# Account Groups - Following Indian Schedule III of Companies Act 2013
ACCOUNT_GROUPS = [
    # Level 0 - Primary Groups (Nature-based)
    {"code": "ASSETS", "name": "Assets", "nature": "ASSETS", "level": 0, "sequence": 1, "is_system": True},
    {"code": "LIABILITIES", "name": "Liabilities", "nature": "LIABILITIES", "level": 0, "sequence": 2, "is_system": True},
    {"code": "EQUITY", "name": "Equity / Shareholders' Funds", "nature": "EQUITY", "level": 0, "sequence": 3, "is_system": True},
    {"code": "INCOME", "name": "Income", "nature": "INCOME", "level": 0, "sequence": 4, "is_system": True},
    {"code": "EXPENSES", "name": "Expenses", "nature": "EXPENSES", "level": 0, "sequence": 5, "is_system": True},

    # Level 1 - ASSETS Sub-Groups (Schedule III Format)
    {"code": "NONCURR_ASSETS", "name": "Non-Current Assets", "nature": "ASSETS", "parent": "ASSETS", "level": 1, "sequence": 1, "is_system": True},
    {"code": "CURR_ASSETS", "name": "Current Assets", "nature": "ASSETS", "parent": "ASSETS", "level": 1, "sequence": 2, "is_system": True},

    # Level 2 - Non-Current Assets
    {"code": "PPE", "name": "Property, Plant and Equipment", "nature": "ASSETS", "parent": "NONCURR_ASSETS", "level": 2, "sequence": 1, "is_system": True},
    {"code": "INTANGIBLE", "name": "Intangible Assets", "nature": "ASSETS", "parent": "NONCURR_ASSETS", "level": 2, "sequence": 2, "is_system": True},
    {"code": "CAPITAL_WIP", "name": "Capital Work-in-Progress", "nature": "ASSETS", "parent": "NONCURR_ASSETS", "level": 2, "sequence": 3, "is_system": True},
    {"code": "FIN_ASSETS_NC", "name": "Financial Assets (Non-Current)", "nature": "ASSETS", "parent": "NONCURR_ASSETS", "level": 2, "sequence": 4, "is_system": True},
    {"code": "DEFERRED_TAX_ASSET", "name": "Deferred Tax Assets (Net)", "nature": "ASSETS", "parent": "NONCURR_ASSETS", "level": 2, "sequence": 5, "is_system": True},
    {"code": "OTHER_NC_ASSETS", "name": "Other Non-Current Assets", "nature": "ASSETS", "parent": "NONCURR_ASSETS", "level": 2, "sequence": 6, "is_system": True},

    # Level 2 - Current Assets
    {"code": "INVENTORIES", "name": "Inventories", "nature": "ASSETS", "parent": "CURR_ASSETS", "level": 2, "sequence": 1, "is_system": True},
    {"code": "FIN_ASSETS_C", "name": "Financial Assets (Current)", "nature": "ASSETS", "parent": "CURR_ASSETS", "level": 2, "sequence": 2, "is_system": True},
    {"code": "CURR_TAX_ASSETS", "name": "Current Tax Assets (Net)", "nature": "ASSETS", "parent": "CURR_ASSETS", "level": 2, "sequence": 3, "is_system": True},
    {"code": "OTHER_CURR_ASSETS", "name": "Other Current Assets", "nature": "ASSETS", "parent": "CURR_ASSETS", "level": 2, "sequence": 4, "is_system": True},

    # Level 3 - Financial Assets (Current) - detailed
    {"code": "TRADE_RECEIVABLES", "name": "Trade Receivables", "nature": "ASSETS", "parent": "FIN_ASSETS_C", "level": 3, "sequence": 1, "is_system": True},
    {"code": "CASH_EQUIVALENTS", "name": "Cash and Cash Equivalents", "nature": "ASSETS", "parent": "FIN_ASSETS_C", "level": 3, "sequence": 2, "is_system": True},
    {"code": "BANK_BALANCES", "name": "Bank Balances", "nature": "ASSETS", "parent": "FIN_ASSETS_C", "level": 3, "sequence": 3, "is_system": True},
    {"code": "LOANS_ADVANCES", "name": "Loans and Advances", "nature": "ASSETS", "parent": "FIN_ASSETS_C", "level": 3, "sequence": 4, "is_system": True},
    {"code": "OTHER_FIN_ASSETS", "name": "Other Financial Assets", "nature": "ASSETS", "parent": "FIN_ASSETS_C", "level": 3, "sequence": 5, "is_system": True},

    # Level 1 - LIABILITIES Sub-Groups
    {"code": "NONCURR_LIAB", "name": "Non-Current Liabilities", "nature": "LIABILITIES", "parent": "LIABILITIES", "level": 1, "sequence": 1, "is_system": True},
    {"code": "CURR_LIAB", "name": "Current Liabilities", "nature": "LIABILITIES", "parent": "LIABILITIES", "level": 1, "sequence": 2, "is_system": True},

    # Level 2 - Non-Current Liabilities
    {"code": "FIN_LIAB_NC", "name": "Financial Liabilities (Non-Current)", "nature": "LIABILITIES", "parent": "NONCURR_LIAB", "level": 2, "sequence": 1, "is_system": True},
    {"code": "PROVISIONS_NC", "name": "Provisions (Non-Current)", "nature": "LIABILITIES", "parent": "NONCURR_LIAB", "level": 2, "sequence": 2, "is_system": True},
    {"code": "DEFERRED_TAX_LIAB", "name": "Deferred Tax Liabilities (Net)", "nature": "LIABILITIES", "parent": "NONCURR_LIAB", "level": 2, "sequence": 3, "is_system": True},
    {"code": "OTHER_NC_LIAB", "name": "Other Non-Current Liabilities", "nature": "LIABILITIES", "parent": "NONCURR_LIAB", "level": 2, "sequence": 4, "is_system": True},

    # Level 2 - Current Liabilities
    {"code": "FIN_LIAB_C", "name": "Financial Liabilities (Current)", "nature": "LIABILITIES", "parent": "CURR_LIAB", "level": 2, "sequence": 1, "is_system": True},
    {"code": "OTHER_CURR_LIAB", "name": "Other Current Liabilities", "nature": "LIABILITIES", "parent": "CURR_LIAB", "level": 2, "sequence": 2, "is_system": True},
    {"code": "PROVISIONS_C", "name": "Provisions (Current)", "nature": "LIABILITIES", "parent": "CURR_LIAB", "level": 2, "sequence": 3, "is_system": True},
    {"code": "CURR_TAX_LIAB", "name": "Current Tax Liabilities (Net)", "nature": "LIABILITIES", "parent": "CURR_LIAB", "level": 2, "sequence": 4, "is_system": True},

    # Level 3 - Financial Liabilities (Current) - detailed
    {"code": "TRADE_PAYABLES", "name": "Trade Payables", "nature": "LIABILITIES", "parent": "FIN_LIAB_C", "level": 3, "sequence": 1, "is_system": True},
    {"code": "BORROWINGS_C", "name": "Borrowings (Current)", "nature": "LIABILITIES", "parent": "FIN_LIAB_C", "level": 3, "sequence": 2, "is_system": True},
    {"code": "OTHER_FIN_LIAB", "name": "Other Financial Liabilities", "nature": "LIABILITIES", "parent": "FIN_LIAB_C", "level": 3, "sequence": 3, "is_system": True},

    # Level 3 - Other Current Liabilities - detailed
    {"code": "STATUTORY_DUES", "name": "Statutory Dues Payable", "nature": "LIABILITIES", "parent": "OTHER_CURR_LIAB", "level": 3, "sequence": 1, "is_system": True},
    {"code": "DUTIES_TAXES", "name": "Duties and Taxes", "nature": "LIABILITIES", "parent": "OTHER_CURR_LIAB", "level": 3, "sequence": 2, "is_system": True},

    # Level 1 - EQUITY Sub-Groups
    {"code": "SHARE_CAPITAL", "name": "Share Capital", "nature": "EQUITY", "parent": "EQUITY", "level": 1, "sequence": 1, "is_system": True},
    {"code": "RESERVES_SURPLUS", "name": "Reserves and Surplus", "nature": "EQUITY", "parent": "EQUITY", "level": 1, "sequence": 2, "is_system": True},
    {"code": "OTHER_EQUITY", "name": "Other Equity", "nature": "EQUITY", "parent": "EQUITY", "level": 1, "sequence": 3, "is_system": True},

    # Level 2 - Reserves and Surplus
    {"code": "CAPITAL_RESERVE", "name": "Capital Reserve", "nature": "EQUITY", "parent": "RESERVES_SURPLUS", "level": 2, "sequence": 1, "is_system": True},
    {"code": "SECURITIES_PREMIUM", "name": "Securities Premium", "nature": "EQUITY", "parent": "RESERVES_SURPLUS", "level": 2, "sequence": 2, "is_system": True},
    {"code": "GENERAL_RESERVE", "name": "General Reserve", "nature": "EQUITY", "parent": "RESERVES_SURPLUS", "level": 2, "sequence": 3, "is_system": True},
    {"code": "RETAINED_EARNINGS", "name": "Retained Earnings", "nature": "EQUITY", "parent": "RESERVES_SURPLUS", "level": 2, "sequence": 4, "is_system": True},

    # Level 1 - INCOME Sub-Groups
    {"code": "REVENUE_OPS", "name": "Revenue from Operations", "nature": "INCOME", "parent": "INCOME", "level": 1, "sequence": 1, "is_system": True},
    {"code": "OTHER_INCOME", "name": "Other Income", "nature": "INCOME", "parent": "INCOME", "level": 1, "sequence": 2, "is_system": True},

    # Level 2 - Revenue from Operations (NBFC specific)
    {"code": "INTEREST_INCOME", "name": "Interest Income", "nature": "INCOME", "parent": "REVENUE_OPS", "level": 2, "sequence": 1, "is_system": True},
    {"code": "FEE_COMMISSION", "name": "Fee and Commission Income", "nature": "INCOME", "parent": "REVENUE_OPS", "level": 2, "sequence": 2, "is_system": True},
    {"code": "NET_GAIN_FV", "name": "Net Gain on Fair Value Changes", "nature": "INCOME", "parent": "REVENUE_OPS", "level": 2, "sequence": 3, "is_system": True},

    # Level 2 - Other Income
    {"code": "DIVIDEND_INCOME", "name": "Dividend Income", "nature": "INCOME", "parent": "OTHER_INCOME", "level": 2, "sequence": 1, "is_system": True},
    {"code": "RENTAL_INCOME", "name": "Rental Income", "nature": "INCOME", "parent": "OTHER_INCOME", "level": 2, "sequence": 2, "is_system": True},
    {"code": "MISC_INCOME", "name": "Miscellaneous Income", "nature": "INCOME", "parent": "OTHER_INCOME", "level": 2, "sequence": 3, "is_system": True},

    # Level 1 - EXPENSES Sub-Groups
    {"code": "FINANCE_COSTS", "name": "Finance Costs", "nature": "EXPENSES", "parent": "EXPENSES", "level": 1, "sequence": 1, "is_system": True},
    {"code": "IMPAIRMENT", "name": "Impairment on Financial Instruments", "nature": "EXPENSES", "parent": "EXPENSES", "level": 1, "sequence": 2, "is_system": True},
    {"code": "EMPLOYEE_BENEFITS", "name": "Employee Benefits Expense", "nature": "EXPENSES", "parent": "EXPENSES", "level": 1, "sequence": 3, "is_system": True},
    {"code": "DEPRECIATION", "name": "Depreciation and Amortisation", "nature": "EXPENSES", "parent": "EXPENSES", "level": 1, "sequence": 4, "is_system": True},
    {"code": "OTHER_EXPENSES", "name": "Other Expenses", "nature": "EXPENSES", "parent": "EXPENSES", "level": 1, "sequence": 5, "is_system": True},

    # Level 2 - Finance Costs
    {"code": "INTEREST_EXP", "name": "Interest Expense", "nature": "EXPENSES", "parent": "FINANCE_COSTS", "level": 2, "sequence": 1, "is_system": True},
    {"code": "OTHER_BORROWING_COSTS", "name": "Other Borrowing Costs", "nature": "EXPENSES", "parent": "FINANCE_COSTS", "level": 2, "sequence": 2, "is_system": True},

    # Level 2 - Employee Benefits
    {"code": "SALARIES_WAGES", "name": "Salaries and Wages", "nature": "EXPENSES", "parent": "EMPLOYEE_BENEFITS", "level": 2, "sequence": 1, "is_system": True},
    {"code": "CONTRIBUTION_PF", "name": "Contribution to PF/ESI", "nature": "EXPENSES", "parent": "EMPLOYEE_BENEFITS", "level": 2, "sequence": 2, "is_system": True},
    {"code": "STAFF_WELFARE", "name": "Staff Welfare Expenses", "nature": "EXPENSES", "parent": "EMPLOYEE_BENEFITS", "level": 2, "sequence": 3, "is_system": True},
    {"code": "GRATUITY_EXP", "name": "Gratuity Expense", "nature": "EXPENSES", "parent": "EMPLOYEE_BENEFITS", "level": 2, "sequence": 4, "is_system": True},

    # Level 2 - Other Expenses
    {"code": "RENT_EXP", "name": "Rent Expense", "nature": "EXPENSES", "parent": "OTHER_EXPENSES", "level": 2, "sequence": 1, "is_system": True},
    {"code": "REPAIRS_MAINT", "name": "Repairs and Maintenance", "nature": "EXPENSES", "parent": "OTHER_EXPENSES", "level": 2, "sequence": 2, "is_system": True},
    {"code": "INSURANCE_EXP", "name": "Insurance Expense", "nature": "EXPENSES", "parent": "OTHER_EXPENSES", "level": 2, "sequence": 3, "is_system": True},
    {"code": "LEGAL_PROF", "name": "Legal and Professional Fees", "nature": "EXPENSES", "parent": "OTHER_EXPENSES", "level": 2, "sequence": 4, "is_system": True},
    {"code": "TRAVEL_CONV", "name": "Travel and Conveyance", "nature": "EXPENSES", "parent": "OTHER_EXPENSES", "level": 2, "sequence": 5, "is_system": True},
    {"code": "COMM_EXP", "name": "Communication Expenses", "nature": "EXPENSES", "parent": "OTHER_EXPENSES", "level": 2, "sequence": 6, "is_system": True},
    {"code": "PRINTING_STAT", "name": "Printing and Stationery", "nature": "EXPENSES", "parent": "OTHER_EXPENSES", "level": 2, "sequence": 7, "is_system": True},
    {"code": "AUDIT_FEES", "name": "Audit Fees", "nature": "EXPENSES", "parent": "OTHER_EXPENSES", "level": 2, "sequence": 8, "is_system": True},
    {"code": "BANK_CHARGES", "name": "Bank Charges", "nature": "EXPENSES", "parent": "OTHER_EXPENSES", "level": 2, "sequence": 9, "is_system": True},
    {"code": "GST_EXP", "name": "GST Expense (Non-ITC)", "nature": "EXPENSES", "parent": "OTHER_EXPENSES", "level": 2, "sequence": 10, "is_system": True},
    {"code": "MISC_EXP", "name": "Miscellaneous Expenses", "nature": "EXPENSES", "parent": "OTHER_EXPENSES", "level": 2, "sequence": 11, "is_system": True},
]

# Sample Accounts (Ledgers)
ACCOUNTS = [
    # Cash & Bank Accounts
    {"code": "1001", "name": "Cash in Hand", "group": "CASH_EQUIVALENTS", "type": "CASH", "opening": 50000, "balance_type": "DEBIT"},
    {"code": "1002", "name": "Petty Cash", "group": "CASH_EQUIVALENTS", "type": "CASH", "opening": 10000, "balance_type": "DEBIT"},
    {"code": "1101", "name": "SBI Current Account", "group": "BANK_BALANCES", "type": "BANK", "opening": 500000, "balance_type": "DEBIT",
     "bank_name": "State Bank of India", "bank_branch": "BKC Branch", "bank_account": "39876543210", "bank_ifsc": "SBIN0001234"},
    {"code": "1102", "name": "HDFC Current Account", "group": "BANK_BALANCES", "type": "BANK", "opening": 300000, "balance_type": "DEBIT",
     "bank_name": "HDFC Bank", "bank_branch": "Andheri Branch", "bank_account": "50100123456789", "bank_ifsc": "HDFC0001234"},
    {"code": "1103", "name": "ICICI Savings Account", "group": "BANK_BALANCES", "type": "BANK", "opening": 100000, "balance_type": "DEBIT",
     "bank_name": "ICICI Bank", "bank_branch": "Fort Branch", "bank_account": "123456789012", "bank_ifsc": "ICIC0001234"},

    # Trade Receivables
    {"code": "1201", "name": "Trade Receivables - Secured", "group": "TRADE_RECEIVABLES", "type": "CONTROL", "control_type": "CUSTOMER"},
    {"code": "1202", "name": "Trade Receivables - Unsecured", "group": "TRADE_RECEIVABLES", "type": "CONTROL", "control_type": "CUSTOMER"},

    # Loans & Advances (NBFC specific)
    {"code": "1301", "name": "Loans to Customers", "group": "LOANS_ADVANCES", "type": "CONTROL", "control_type": "CUSTOMER"},
    {"code": "1302", "name": "Staff Loans and Advances", "group": "LOANS_ADVANCES", "type": "LEDGER"},
    {"code": "1303", "name": "Security Deposits", "group": "LOANS_ADVANCES", "type": "LEDGER"},
    {"code": "1304", "name": "Advances to Suppliers", "group": "LOANS_ADVANCES", "type": "LEDGER"},

    # Other Current Assets
    {"code": "1401", "name": "Prepaid Expenses", "group": "OTHER_CURR_ASSETS", "type": "LEDGER"},
    {"code": "1402", "name": "Input GST Receivable", "group": "OTHER_CURR_ASSETS", "type": "LEDGER"},
    {"code": "1403", "name": "TDS Receivable", "group": "OTHER_CURR_ASSETS", "type": "LEDGER"},
    {"code": "1404", "name": "Interest Accrued but Not Due", "group": "OTHER_CURR_ASSETS", "type": "LEDGER"},

    # Fixed Assets
    {"code": "1501", "name": "Land", "group": "PPE", "type": "LEDGER"},
    {"code": "1502", "name": "Buildings", "group": "PPE", "type": "LEDGER"},
    {"code": "1503", "name": "Furniture and Fixtures", "group": "PPE", "type": "LEDGER"},
    {"code": "1504", "name": "Office Equipment", "group": "PPE", "type": "LEDGER"},
    {"code": "1505", "name": "Computers and Laptops", "group": "PPE", "type": "LEDGER"},
    {"code": "1506", "name": "Vehicles", "group": "PPE", "type": "LEDGER"},
    {"code": "1507", "name": "Accumulated Depreciation", "group": "PPE", "type": "LEDGER", "opening": 0, "balance_type": "CREDIT"},

    # Intangible Assets
    {"code": "1601", "name": "Software Licenses", "group": "INTANGIBLE", "type": "LEDGER"},
    {"code": "1602", "name": "Goodwill", "group": "INTANGIBLE", "type": "LEDGER"},

    # Trade Payables
    {"code": "2001", "name": "Trade Payables - MSME", "group": "TRADE_PAYABLES", "type": "CONTROL", "control_type": "VENDOR"},
    {"code": "2002", "name": "Trade Payables - Others", "group": "TRADE_PAYABLES", "type": "CONTROL", "control_type": "VENDOR"},

    # Other Financial Liabilities
    {"code": "2101", "name": "Salaries Payable", "group": "OTHER_FIN_LIAB", "type": "LEDGER"},
    {"code": "2102", "name": "Expenses Payable", "group": "OTHER_FIN_LIAB", "type": "LEDGER"},
    {"code": "2103", "name": "Security Deposits Received", "group": "OTHER_FIN_LIAB", "type": "LEDGER"},

    # Statutory Dues
    {"code": "2201", "name": "TDS Payable", "group": "STATUTORY_DUES", "type": "LEDGER"},
    {"code": "2202", "name": "GST Payable", "group": "STATUTORY_DUES", "type": "LEDGER"},
    {"code": "2203", "name": "Professional Tax Payable", "group": "STATUTORY_DUES", "type": "LEDGER"},
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
    {"code": "2502", "name": "Provision for Leave Encashment", "group": "PROVISIONS_C", "type": "LEDGER"},
    {"code": "2503", "name": "Provision for Bad Debts", "group": "PROVISIONS_C", "type": "LEDGER"},

    # Share Capital
    {"code": "3001", "name": "Equity Share Capital", "group": "SHARE_CAPITAL", "type": "LEDGER", "opening": 10000000, "balance_type": "CREDIT"},
    {"code": "3002", "name": "Preference Share Capital", "group": "SHARE_CAPITAL", "type": "LEDGER"},

    # Reserves
    {"code": "3101", "name": "Securities Premium Account", "group": "SECURITIES_PREMIUM", "type": "LEDGER"},
    {"code": "3102", "name": "General Reserve", "group": "GENERAL_RESERVE", "type": "LEDGER"},
    {"code": "3103", "name": "Profit and Loss Account", "group": "RETAINED_EARNINGS", "type": "LEDGER", "opening": 2500000, "balance_type": "CREDIT"},
    {"code": "3104", "name": "Statutory Reserve (RBI)", "group": "RETAINED_EARNINGS", "type": "LEDGER"},

    # Income Accounts
    {"code": "4001", "name": "Interest on Loans", "group": "INTEREST_INCOME", "type": "LEDGER"},
    {"code": "4002", "name": "Interest on FD", "group": "INTEREST_INCOME", "type": "LEDGER"},
    {"code": "4003", "name": "Interest on Savings Account", "group": "INTEREST_INCOME", "type": "LEDGER"},
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
    {"code": "5003", "name": "Processing Fee Expense", "group": "OTHER_BORROWING_COSTS", "type": "LEDGER"},
    {"code": "5101", "name": "Provision for NPA", "group": "IMPAIRMENT", "type": "LEDGER"},
    {"code": "5102", "name": "Bad Debts Written Off", "group": "IMPAIRMENT", "type": "LEDGER"},
    {"code": "5201", "name": "Salaries and Wages", "group": "SALARIES_WAGES", "type": "LEDGER"},
    {"code": "5202", "name": "Directors' Remuneration", "group": "SALARIES_WAGES", "type": "LEDGER"},
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
    {"code": "JV", "name": "Journal Voucher", "class": "JOURNAL", "prefix": "JV/", "auto": True, "approval": True, "levels": 1},
    {"code": "PV", "name": "Payment Voucher", "class": "PAYMENT", "prefix": "PV/", "auto": True, "approval": True, "levels": 1},
    {"code": "RV", "name": "Receipt Voucher", "class": "RECEIPT", "prefix": "RV/", "auto": True, "approval": True, "levels": 1},
    {"code": "CV", "name": "Contra Voucher", "class": "CONTRA", "prefix": "CV/", "auto": True, "approval": False, "levels": 0},
    {"code": "SV", "name": "Sales Voucher", "class": "SALES", "prefix": "SV/", "auto": True, "approval": True, "levels": 1},
    {"code": "PU", "name": "Purchase Voucher", "class": "PURCHASE", "prefix": "PU/", "auto": True, "approval": True, "levels": 1},
    {"code": "DN", "name": "Debit Note", "class": "DEBIT_NOTE", "prefix": "DN/", "auto": True, "approval": True, "levels": 1},
    {"code": "CN", "name": "Credit Note", "class": "CREDIT_NOTE", "prefix": "CN/", "auto": True, "approval": True, "levels": 1},
]

# =====================================================
# GST SEED DATA - Indian GST Rates
# =====================================================

GST_RATES = [
    {"code": "GST0", "name": "Exempt / NIL Rated", "rate": 0, "cgst": 0, "sgst": 0, "igst": 0, "cess": 0, "description": "Exempt or NIL rated goods and services"},
    {"code": "GST5", "name": "GST 5%", "rate": 5, "cgst": 2.5, "sgst": 2.5, "igst": 5, "cess": 0, "description": "Essential items, basic services"},
    {"code": "GST12", "name": "GST 12%", "rate": 12, "cgst": 6, "sgst": 6, "igst": 12, "cess": 0, "description": "Standard goods and services"},
    {"code": "GST18", "name": "GST 18%", "rate": 18, "cgst": 9, "sgst": 9, "igst": 18, "cess": 0, "description": "Most goods and services (default)"},
    {"code": "GST28", "name": "GST 28%", "rate": 28, "cgst": 14, "sgst": 14, "igst": 28, "cess": 0, "description": "Luxury goods, sin goods"},
    {"code": "GST28C1", "name": "GST 28% + 1% Cess", "rate": 28, "cgst": 14, "sgst": 14, "igst": 28, "cess": 1, "description": "Small cars, SUVs cess"},
    {"code": "GST28C3", "name": "GST 28% + 3% Cess", "rate": 28, "cgst": 14, "sgst": 14, "igst": 28, "cess": 3, "description": "Mid-size cars cess"},
    {"code": "GST28C15", "name": "GST 28% + 15% Cess", "rate": 28, "cgst": 14, "sgst": 14, "igst": 28, "cess": 15, "description": "Large cars cess"},
    {"code": "GST28C22", "name": "GST 28% + 22% Cess", "rate": 28, "cgst": 14, "sgst": 14, "igst": 28, "cess": 22, "description": "Luxury SUVs cess"},
]

# Sample HSN/SAC Codes
HSN_SAC_CODES = [
    # Financial Services (SAC)
    {"code": "997119", "description": "Other financial services except insurance and pension funding services", "type": "SAC", "gst_rate": "GST18"},
    {"code": "997112", "description": "Credit granting services", "type": "SAC", "gst_rate": "GST18"},
    {"code": "997113", "description": "Financial leasing services", "type": "SAC", "gst_rate": "GST18"},
    {"code": "997152", "description": "Loan brokerage services", "type": "SAC", "gst_rate": "GST18"},
    {"code": "997159", "description": "Other services auxiliary to financial services", "type": "SAC", "gst_rate": "GST18"},
    {"code": "997161", "description": "Services of holding financial assets", "type": "SAC", "gst_rate": "GST18"},
    # Professional Services (SAC)
    {"code": "998211", "description": "Legal advisory and representation services", "type": "SAC", "gst_rate": "GST18"},
    {"code": "998212", "description": "Legal documentation and certification services", "type": "SAC", "gst_rate": "GST18"},
    {"code": "998221", "description": "Financial auditing services", "type": "SAC", "gst_rate": "GST18"},
    {"code": "998222", "description": "Accounting and book keeping services", "type": "SAC", "gst_rate": "GST18"},
    {"code": "998231", "description": "Corporate tax consulting and preparation services", "type": "SAC", "gst_rate": "GST18"},
    {"code": "998311", "description": "Management consulting and management services", "type": "SAC", "gst_rate": "GST18"},
    {"code": "998312", "description": "Business consulting services", "type": "SAC", "gst_rate": "GST18"},
    # IT Services (SAC)
    {"code": "998313", "description": "Information technology consulting and support services", "type": "SAC", "gst_rate": "GST18"},
    {"code": "998314", "description": "Information technology design and development services", "type": "SAC", "gst_rate": "GST18"},
    {"code": "998315", "description": "Hosting and information technology infrastructure provisioning services", "type": "SAC", "gst_rate": "GST18"},
    {"code": "998316", "description": "IT infrastructure and network management services", "type": "SAC", "gst_rate": "GST18"},
    # Rental Services (SAC)
    {"code": "997212", "description": "Rental or leasing services involving own or leased non-residential property", "type": "SAC", "gst_rate": "GST18"},
    # Common Goods (HSN)
    {"code": "8471", "description": "Computers and Computer Parts", "type": "HSN", "gst_rate": "GST18"},
    {"code": "8443", "description": "Printing machinery, printers, copiers", "type": "HSN", "gst_rate": "GST18"},
    {"code": "9403", "description": "Office Furniture", "type": "HSN", "gst_rate": "GST18"},
    {"code": "8517", "description": "Telephones including smartphones", "type": "HSN", "gst_rate": "GST18"},
    {"code": "4820", "description": "Paper and Stationery", "type": "HSN", "gst_rate": "GST12"},
    {"code": "4901", "description": "Printed books, newspapers", "type": "HSN", "gst_rate": "GST0"},
]

# =====================================================
# TDS SEED DATA - Indian TDS Sections
# =====================================================

TDS_SECTIONS = [
    # Salary & Payments to Employees
    {"code": "192", "name": "Salaries", "description": "TDS on salary payments", "rate_ind": 0, "rate_comp": 0, "rate_no_pan": 20,
     "threshold_single": 0, "threshold_annual": 0, "return_form": "24Q", "nature_code": "1"},
    # Contractors
    {"code": "194C", "name": "Contractors (Single)", "description": "Payment to contractors - single transaction", "rate_ind": 1, "rate_comp": 2, "rate_no_pan": 20,
     "threshold_single": 30000, "threshold_annual": 100000, "return_form": "26Q", "nature_code": "C"},
    {"code": "194C-A", "name": "Contractors (Aggregate)", "description": "Payment to contractors - aggregate in year", "rate_ind": 1, "rate_comp": 2, "rate_no_pan": 20,
     "threshold_single": 0, "threshold_annual": 100000, "return_form": "26Q", "nature_code": "C"},
    # Professional & Technical
    {"code": "194J", "name": "Professional/Technical Services", "description": "Fees for professional or technical services", "rate_ind": 10, "rate_comp": 10, "rate_no_pan": 20,
     "threshold_single": 30000, "threshold_annual": 30000, "return_form": "26Q", "nature_code": "J"},
    {"code": "194J-B", "name": "Technical Services (Reduced)", "description": "Technical services with reduced rate", "rate_ind": 2, "rate_comp": 2, "rate_no_pan": 20,
     "threshold_single": 30000, "threshold_annual": 30000, "return_form": "26Q", "nature_code": "JB"},
    # Rent
    {"code": "194I-A", "name": "Rent - Plant & Machinery", "description": "Rent on plant and machinery", "rate_ind": 2, "rate_comp": 2, "rate_no_pan": 20,
     "threshold_single": 0, "threshold_annual": 240000, "return_form": "26Q", "nature_code": "IA"},
    {"code": "194I-B", "name": "Rent - Land/Building/Furniture", "description": "Rent on land, building, furniture", "rate_ind": 10, "rate_comp": 10, "rate_no_pan": 20,
     "threshold_single": 0, "threshold_annual": 240000, "return_form": "26Q", "nature_code": "IB"},
    # Commission & Brokerage
    {"code": "194H", "name": "Commission/Brokerage", "description": "Commission or brokerage payments", "rate_ind": 5, "rate_comp": 5, "rate_no_pan": 20,
     "threshold_single": 0, "threshold_annual": 15000, "return_form": "26Q", "nature_code": "H"},
    # Interest
    {"code": "194A", "name": "Interest (Other than Securities)", "description": "Interest other than interest on securities", "rate_ind": 10, "rate_comp": 10, "rate_no_pan": 20,
     "threshold_single": 0, "threshold_annual": 40000, "return_form": "26Q", "nature_code": "A"},
    {"code": "194A-S", "name": "Interest (Senior Citizen)", "description": "Interest to senior citizens", "rate_ind": 10, "rate_comp": 10, "rate_no_pan": 20,
     "threshold_single": 0, "threshold_annual": 50000, "return_form": "26Q", "nature_code": "AS"},
    # Dividend
    {"code": "194", "name": "Dividend", "description": "Dividend payments", "rate_ind": 10, "rate_comp": 10, "rate_no_pan": 20,
     "threshold_single": 0, "threshold_annual": 5000, "return_form": "26Q", "nature_code": "D"},
    # Payments to NRIs (Form 27Q)
    {"code": "195", "name": "Payments to NRI", "description": "Any payment to non-resident", "rate_ind": 0, "rate_comp": 0, "rate_no_pan": 20,
     "threshold_single": 0, "threshold_annual": 0, "return_form": "27Q", "nature_code": "NR"},
    # E-Commerce
    {"code": "194O", "name": "E-Commerce Operator", "description": "Payment by e-commerce operator", "rate_ind": 1, "rate_comp": 1, "rate_no_pan": 20,
     "threshold_single": 0, "threshold_annual": 500000, "return_form": "26Q", "nature_code": "O"},
    # TCS Sections
    {"code": "206C-1H", "name": "TCS - Sale of Goods", "description": "TCS on sale of goods exceeding 50L", "rate_ind": 0.1, "rate_comp": 0.1, "rate_no_pan": 1,
     "threshold_single": 0, "threshold_annual": 5000000, "return_form": "27EQ", "nature_code": "TCS1H", "is_tcs": True},
    {"code": "206C-1G", "name": "TCS - Foreign Remittance", "description": "TCS on foreign remittance under LRS", "rate_ind": 5, "rate_comp": 5, "rate_no_pan": 10,
     "threshold_single": 0, "threshold_annual": 700000, "return_form": "27EQ", "nature_code": "TCS1G", "is_tcs": True},
]

# =====================================================
# PAYMENT TERMS SEED DATA
# =====================================================

PAYMENT_TERMS = [
    {"code": "IMMEDIATE", "name": "Immediate / Cash", "description": "Payment due immediately on invoice", "days": 0, "discount_days": 0, "discount_percent": 0},
    {"code": "COD", "name": "Cash on Delivery", "description": "Payment on delivery of goods", "days": 0, "discount_days": 0, "discount_percent": 0},
    {"code": "NET7", "name": "Net 7 Days", "description": "Payment due within 7 days", "days": 7, "discount_days": 0, "discount_percent": 0},
    {"code": "NET15", "name": "Net 15 Days", "description": "Payment due within 15 days", "days": 15, "discount_days": 0, "discount_percent": 0},
    {"code": "NET30", "name": "Net 30 Days", "description": "Payment due within 30 days", "days": 30, "discount_days": 0, "discount_percent": 0},
    {"code": "NET45", "name": "Net 45 Days", "description": "Payment due within 45 days", "days": 45, "discount_days": 0, "discount_percent": 0},
    {"code": "NET60", "name": "Net 60 Days", "description": "Payment due within 60 days", "days": 60, "discount_days": 0, "discount_percent": 0},
    {"code": "NET90", "name": "Net 90 Days", "description": "Payment due within 90 days", "days": 90, "discount_days": 0, "discount_percent": 0},
    {"code": "2/10NET30", "name": "2% 10 Net 30", "description": "2% discount if paid within 10 days, net due in 30 days", "days": 30, "discount_days": 10, "discount_percent": 2},
    {"code": "1/10NET30", "name": "1% 10 Net 30", "description": "1% discount if paid within 10 days, net due in 30 days", "days": 30, "discount_days": 10, "discount_percent": 1},
    {"code": "EOM", "name": "End of Month", "description": "Payment due at end of month", "days": 30, "discount_days": 0, "discount_percent": 0},
    {"code": "MFI", "name": "Month Following Invoice", "description": "Payment due on 15th of month following invoice", "days": 45, "discount_days": 0, "discount_percent": 0},
]


async def seed_permissions(session) -> dict:
    """Seed permissions and return permission map."""
    print("Seeding permissions...")
    permission_map = {}

    for perm_data in PERMISSIONS:
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
        result = await session.execute(
            select(Role).where(Role.code == role_data["code"])
        )
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
                    print(f"  - Role '{role_data['code']}' already exists, added {added_count} new permissions")
                else:
                    print(f"  - Role '{role_data['code']}' already exists (all permissions present)")
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
    """Seed SMFC organization."""
    print("\nSeeding organization...")

    result = await session.execute(
        select(Organization).where(Organization.code == "SMFC")
    )
    existing = result.scalar_one_or_none()

    if existing:
        print("  - Organization 'SMFC' already exists")
        return existing

    org = Organization(
        code="SMFC",
        name="SMFC Ltd",
        legal_name="SMFC Financial Corporation Limited",
        short_name="SMFC",
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
    print(f"  + Created organization 'SMFC'")
    return org


async def seed_units(session, org):
    """Seed units."""
    print("\nSeeding units...")
    unit_map = {}
    head_office = None

    for unit_data in UNITS:
        result = await session.execute(
            select(Unit).where(Unit.code == unit_data["code"])
        )
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
    result = await session.execute(
        select(User).where(User.username == ADMIN_USER["username"])
    )
    admin = result.scalar_one_or_none()

    if admin:
        print(f"  - Admin user '{ADMIN_USER['username']}' already exists")
    else:
        password_hash = get_password_hash(ADMIN_USER["password"])
        password_expires_at = datetime.now(timezone.utc) + timedelta(days=settings.PASSWORD_EXPIRY_DAYS)

        admin = User(
            username=ADMIN_USER["username"],
            email=ADMIN_USER["email"],
            full_name=ADMIN_USER["full_name"],
            employee_code=ADMIN_USER["employee_code"],
            password_hash=password_hash,
            password_changed_at=datetime.now(timezone.utc),
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
                effective_from=datetime.now(timezone.utc),
            )
            session.add(user_role)

        print(f"  + Created admin user '{ADMIN_USER['username']}'")
        user_count += 1

    # Create sample users
    for user_data in SAMPLE_USERS:
        result = await session.execute(
            select(User).where(User.username == user_data["username"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  - User '{user_data['username']}' already exists")
            continue

        password_hash = get_password_hash("Password123!")
        password_expires_at = datetime.now(timezone.utc) + timedelta(days=settings.PASSWORD_EXPIRY_DAYS)

        user = User(
            username=user_data["username"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            employee_code=user_data["employee_code"],
            password_hash=password_hash,
            password_changed_at=datetime.now(timezone.utc),
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
                effective_from=datetime.now(timezone.utc),
            )
            session.add(user_role)

        print(f"  + Created user '{user_data['username']}' with role '{user_data['role']}'")
        user_count += 1

    await session.commit()
    print(f"Total users created: {user_count}")


async def seed_financial_year(session, org):
    """Seed Financial Year FY2024-25 with monthly periods."""
    print("\nSeeding financial year...")

    result = await session.execute(
        select(FinancialYear).where(FinancialYear.code == "FY2024-25")
    )
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
        "April 2024", "May 2024", "June 2024", "July 2024",
        "August 2024", "September 2024", "October 2024", "November 2024",
        "December 2024", "January 2025", "February 2025", "March 2025"
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
    print(f"  + Created financial year 'FY2024-25' with 12 monthly periods")
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
        result = await session.execute(
            select(Account).where(Account.code == acc_data["code"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            continue

        group = group_map.get(acc_data["group"])
        if not group:
            print(f"  ! Warning: Group '{acc_data['group']}' not found for account '{acc_data['code']}'")
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
        result = await session.execute(
            select(GSTRate).where(GSTRate.code == rate_data["code"])
        )
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
        result = await session.execute(
            select(HSNSAC).where(HSNSAC.code == hsn_data["code"])
        )
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

    result = await session.execute(
        select(GSTRegistration).where(GSTRegistration.organization_id == org.id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        print("  - GST registration already exists")
        return existing

    registration = GSTRegistration(
        gstin="27AABCS1234A1Z5",
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
                PaymentTerms.code == terms_data["code"],
                PaymentTerms.organization_id == org_id
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


# Sample Vouchers with different statuses
SAMPLE_VOUCHERS = [
    # DRAFT Vouchers - Not yet submitted
    {
        "type": "JV",
        "date": "2024-12-01",
        "narration": "Opening entry adjustment for prepaid insurance",
        "status": "DRAFT",
        "lines": [
            {"account": "1401", "debit": 25000, "credit": 0, "narration": "Prepaid Insurance - Dec portion"},
            {"account": "5404", "debit": 0, "credit": 25000, "narration": "Insurance Premium expense reversal"},
        ]
    },
    {
        "type": "PV",
        "date": "2024-12-02",
        "narration": "Professional fees payment to M/s Legal Associates",
        "status": "DRAFT",
        "lines": [
            {"account": "5405", "debit": 50000, "credit": 0, "narration": "Legal fees for loan documentation"},
            {"account": "1101", "debit": 0, "credit": 45000, "narration": "Payment via SBI"},
            {"account": "2201", "debit": 0, "credit": 5000, "narration": "TDS @ 10% u/s 194J"},
        ]
    },
    # PENDING_APPROVAL Vouchers - Submitted for approval
    {
        "type": "JV",
        "date": "2024-12-03",
        "narration": "Monthly salary provision for December 2024",
        "status": "PENDING_APPROVAL",
        "lines": [
            {"account": "5201", "debit": 450000, "credit": 0, "narration": "Salaries for Dec 2024"},
            {"account": "5204", "debit": 54000, "credit": 0, "narration": "PF Contribution - Employer"},
            {"account": "5205", "debit": 16875, "credit": 0, "narration": "ESI Contribution - Employer"},
            {"account": "2101", "debit": 0, "credit": 385000, "narration": "Net Salaries Payable"},
            {"account": "2204", "debit": 0, "credit": 108000, "narration": "PF Payable (Employee + Employer)"},
            {"account": "2205", "debit": 0, "credit": 27875, "narration": "ESI Payable (Employee + Employer)"},
        ]
    },
    {
        "type": "PV",
        "date": "2024-12-04",
        "narration": "Office rent payment for December 2024",
        "status": "PENDING_APPROVAL",
        "lines": [
            {"account": "5401", "debit": 150000, "credit": 0, "narration": "Office Rent - Dec 2024"},
            {"account": "1402", "debit": 27000, "credit": 0, "narration": "GST Input Credit @ 18%"},
            {"account": "1101", "debit": 0, "credit": 162000, "narration": "Payment via SBI"},
            {"account": "2201", "debit": 0, "credit": 15000, "narration": "TDS @ 10% u/s 194I"},
        ]
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
        ]
    },
    # APPROVED Vouchers - Approved but not posted
    {
        "type": "JV",
        "date": "2024-12-06",
        "narration": "Depreciation provision for November 2024",
        "status": "APPROVED",
        "lines": [
            {"account": "5302", "debit": 12500, "credit": 0, "narration": "Depreciation - Furniture"},
            {"account": "5303", "debit": 8500, "credit": 0, "narration": "Depreciation - Equipment"},
            {"account": "5304", "debit": 25000, "credit": 0, "narration": "Depreciation - Vehicles"},
            {"account": "1507", "debit": 0, "credit": 46000, "narration": "Accumulated Depreciation"},
        ]
    },
    {
        "type": "CV",
        "date": "2024-12-07",
        "narration": "Transfer from HDFC to SBI for salary payment",
        "status": "APPROVED",
        "lines": [
            {"account": "1101", "debit": 500000, "credit": 0, "narration": "Transfer to SBI"},
            {"account": "1102", "debit": 0, "credit": 500000, "narration": "Transfer from HDFC"},
        ]
    },
    # POSTED Vouchers - Fully processed
    {
        "type": "JV",
        "date": "2024-11-30",
        "narration": "Interest income accrual for November 2024",
        "status": "POSTED",
        "lines": [
            {"account": "1404", "debit": 285000, "credit": 0, "narration": "Interest accrued on loans"},
            {"account": "4001", "debit": 0, "credit": 285000, "narration": "Interest Income - Nov 2024"},
        ]
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
        ]
    },
    {
        "type": "RV",
        "date": "2024-11-25",
        "narration": "Interest received from FD maturity",
        "status": "POSTED",
        "lines": [
            {"account": "1103", "debit": 125000, "credit": 0, "narration": "Credited to ICICI Savings"},
            {"account": "4002", "debit": 0, "credit": 125000, "narration": "Interest on Fixed Deposit"},
        ]
    },
    {
        "type": "JV",
        "date": "2024-11-20",
        "narration": "NPA provision for Q2 FY24-25",
        "status": "POSTED",
        "lines": [
            {"account": "5101", "debit": 175000, "credit": 0, "narration": "Provision for NPA"},
            {"account": "2503", "debit": 0, "credit": 175000, "narration": "Provision for Bad Debts"},
        ]
    },
    # REJECTED Voucher
    {
        "type": "PV",
        "date": "2024-12-08",
        "narration": "Entertainment expenses - Board meeting",
        "status": "REJECTED",
        "rejection_reason": "Entertainment expenses need prior approval from CFO. Please get approval and resubmit.",
        "lines": [
            {"account": "5418", "debit": 35000, "credit": 0, "narration": "Entertainment expenses"},
            {"account": "1001", "debit": 0, "credit": 35000, "narration": "Paid from petty cash"},
        ]
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
    result = await session.execute(
        select(VoucherType).where(VoucherType.organization_id == org.id)
    )
    voucher_types = {vt.code: vt for vt in result.scalars().all()}

    # Get accounts
    result = await session.execute(
        select(Account).where(Account.organization_id == org.id)
    )
    accounts = {acc.code: acc for acc in result.scalars().all()}

    # Get financial periods
    result = await session.execute(
        select(FinancialPeriod).where(FinancialPeriod.financial_year_id == fy.id)
    )
    periods = {p.period_number: p for p in result.scalars().all()}

    # Get head office unit
    result = await session.execute(
        select(Unit).where(Unit.organization_id == org.id, Unit.is_head_office == True)
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
        if status in [VoucherStatus.PENDING_APPROVAL, VoucherStatus.APPROVED, VoucherStatus.POSTED, VoucherStatus.REJECTED]:
            voucher.submitted_at = datetime.now(timezone.utc) - timedelta(days=2)
            voucher.submitted_by = admin_user.id

        if status in [VoucherStatus.APPROVED, VoucherStatus.POSTED]:
            voucher.approved_at = datetime.now(timezone.utc) - timedelta(days=1)
            voucher.approved_by = admin_user.id
            voucher.current_approval_level = vtype.approval_levels
            voucher.approval_status = [{"level": 1, "approved_by": str(admin_user.id), "approved_at": str(voucher.approved_at)}]

        if status == VoucherStatus.POSTED:
            voucher.posted_at = datetime.now(timezone.utc)
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

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("\nDatabase tables created/verified.")

    async with async_session_factory() as session:
        # Seed data - Foundation
        permission_map = await seed_permissions(session)
        role_map = await seed_roles(session, permission_map)
        org = await seed_organization(session)
        unit_map = await seed_units(session, org)
        dept_map = await seed_departments(session, org)
        desig_map = await seed_designations(session, dept_map)
        await seed_users(session, org, role_map, unit_map)

        # Seed data - Finance (Indian Standards)
        fy = await seed_financial_year(session, org)
        group_map = await seed_account_groups(session, org)
        await seed_accounts(session, org, group_map)
        await seed_voucher_types(session, org)

        # Seed data - GST Module
        gst_rate_map = await seed_gst_rates(session)
        await seed_hsn_sac_codes(session, gst_rate_map)
        await seed_gst_registration(session, org)

        # Seed data - TDS Module
        await seed_tds_sections(session)

        # Seed data - AP/AR Module
        await seed_payment_terms(session, org.id)

        # Get admin user for voucher creation
        result = await session.execute(
            select(User).where(User.username == ADMIN_USER["username"])
        )
        admin_user = result.scalar_one_or_none()

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
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
