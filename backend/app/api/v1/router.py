"""Main API v1 router."""

from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.ap_ar.aging_reports import router as aging_reports_router
from app.api.v1.ap_ar.bank_reconciliation import router as bank_reconciliation_router
from app.api.v1.ap_ar.customers import router as customers_router
from app.api.v1.ap_ar.payment_files import router as payment_files_router
from app.api.v1.ap_ar.payment_terms import router as payment_terms_router
from app.api.v1.ap_ar.payments import router as payments_router
from app.api.v1.ap_ar.purchase_bills import router as purchase_bills_router
from app.api.v1.ap_ar.sales_invoices import router as sales_invoices_router
from app.api.v1.ap_ar.vendors import router as vendors_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.auth.auth import router as auth_router
from app.api.v1.auth.roles import router as roles_router
from app.api.v1.auth.users import router as users_router
from app.api.v1.bi import router as bi_router
from app.api.v1.common.audit_logs import router as audit_logs_router
from app.api.v1.compliance import router as compliance_router
from app.api.v1.core.integrations import router as integrations_router
from app.api.v1.dashboard.dashboard import router as dashboard_router
from app.api.v1.dms import router as dms_router
from app.api.v1.ess import router as ess_router
from app.api.v1.finance.account_groups import router as account_groups_router
from app.api.v1.finance.accounts import router as accounts_router
from app.api.v1.finance.cost_centers import router as cost_centers_router
from app.api.v1.finance.financial_years import router as financial_years_router
from app.api.v1.finance.gl_entries import router as gl_entries_router
from app.api.v1.finance.recurring_vouchers import router as recurring_vouchers_router
from app.api.v1.finance.voucher_templates import router as voucher_templates_router
from app.api.v1.finance.voucher_types import router as voucher_types_router
from app.api.v1.finance.vouchers import router as vouchers_router
from app.api.v1.finance.year_end import router as year_end_router
from app.api.v1.fixed_assets import router as fixed_assets_router
from app.api.v1.fixed_deposits import router as fixed_deposits_router
from app.api.v1.gst.gst_rates import router as gst_rates_router
from app.api.v1.gst.gst_registrations import router as gst_registrations_router
from app.api.v1.gst.gstn import router as gstn_router
from app.api.v1.gst.hsn_sac import router as hsn_sac_router
from app.api.v1.hris import router as hris_router
from app.api.v1.inventory import router as inventory_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.legal import router as legal_router
from app.api.v1.lending import router as lending_router
from app.api.v1.masters.departments import router as departments_router
from app.api.v1.masters.designations import router as designations_router
from app.api.v1.masters.organization_addresses import router as org_addresses_router
from app.api.v1.masters.organization_bank_accounts import router as org_bank_accounts_router
from app.api.v1.masters.organizations import router as organizations_router
from app.api.v1.masters.units import router as units_router
from app.api.v1.notification import router as notification_router
from app.api.v1.payroll import router as payroll_router
from app.api.v1.portal import router as portal_router
from app.api.v1.reports import router as reports_router
from app.api.v1.tds.form16a import router as form16a_router
from app.api.v1.tds.tds_challans import router as tds_challans_router
from app.api.v1.tds.tds_entries import router as tds_entries_router
from app.api.v1.tds.tds_returns import router as tds_returns_router
from app.api.v1.tds.tds_sections import router as tds_sections_router
from app.api.v1.vendor_portal import router as vendor_portal_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.workflow import router as workflow_router

api_router = APIRouter()

# Auth routes
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(roles_router, prefix="/roles", tags=["Roles & Permissions"])

# Master routes
api_router.include_router(organizations_router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(
    org_bank_accounts_router, prefix="/organizations", tags=["Organization Bank Accounts"]
)
api_router.include_router(
    org_addresses_router, prefix="/organizations", tags=["Organization Addresses"]
)
api_router.include_router(units_router, prefix="/units", tags=["Units"])
api_router.include_router(departments_router, prefix="/departments", tags=["Departments"])
api_router.include_router(designations_router, prefix="/designations", tags=["Designations"])

# Finance routes
api_router.include_router(
    financial_years_router, prefix="/financial-years", tags=["Financial Years"]
)
api_router.include_router(account_groups_router, prefix="/account-groups", tags=["Account Groups"])
api_router.include_router(accounts_router, prefix="/accounts", tags=["Accounts"])
api_router.include_router(voucher_types_router, prefix="/voucher-types", tags=["Voucher Types"])
api_router.include_router(vouchers_router, prefix="/vouchers", tags=["Vouchers"])
api_router.include_router(year_end_router, prefix="/year-end", tags=["Year-End Closing"])
api_router.include_router(
    recurring_vouchers_router, prefix="/recurring-vouchers", tags=["Recurring Vouchers"]
)
api_router.include_router(
    voucher_templates_router, prefix="/voucher-templates", tags=["Voucher Templates"]
)
api_router.include_router(gl_entries_router, prefix="/gl-entries", tags=["GL Entries"])
api_router.include_router(cost_centers_router, prefix="/cost-centers", tags=["Cost Centers"])

# Fixed Assets routes
api_router.include_router(fixed_assets_router, prefix="/fixed-assets", tags=["Fixed Assets"])

# GST routes
api_router.include_router(gst_rates_router, prefix="/gst/rates", tags=["GST Rates"])
api_router.include_router(hsn_sac_router, prefix="/gst/hsn-sac", tags=["HSN/SAC"])
api_router.include_router(
    gst_registrations_router, prefix="/gst/registrations", tags=["GST Registrations"]
)
api_router.include_router(gstn_router, prefix="/gst/gstn", tags=["GSTN Portal"])

# TDS routes
api_router.include_router(tds_sections_router, prefix="/tds/sections", tags=["TDS Sections"])
api_router.include_router(tds_entries_router, prefix="/tds/entries", tags=["TDS Entries"])
api_router.include_router(tds_challans_router, prefix="/tds/challans", tags=["TDS Challans"])
api_router.include_router(tds_returns_router, prefix="/tds/returns", tags=["TDS Returns"])
api_router.include_router(form16a_router, prefix="/tds/form16a", tags=["Form 16A Certificates"])

# Reports (Financial + Regulatory + MIS)
api_router.include_router(reports_router, prefix="/reports")

# AP/AR routes
api_router.include_router(payment_terms_router, prefix="/payment-terms", tags=["Payment Terms"])
api_router.include_router(vendors_router, prefix="/vendors", tags=["Vendors"])
api_router.include_router(customers_router, prefix="/customers", tags=["Customers"])
api_router.include_router(purchase_bills_router, prefix="/purchase-bills", tags=["Purchase Bills"])
api_router.include_router(sales_invoices_router, prefix="/sales-invoices", tags=["Sales Invoices"])
api_router.include_router(payments_router, prefix="/payments", tags=["Payments"])
api_router.include_router(bank_reconciliation_router)
api_router.include_router(aging_reports_router)
api_router.include_router(payment_files_router, prefix="/payment-files", tags=["Payment Files"])

# Dashboard routes
api_router.include_router(dashboard_router)

# Common/System routes
api_router.include_router(audit_logs_router, prefix="/audit-logs", tags=["Audit Logs"])

# Workflow routes
api_router.include_router(workflow_router, prefix="/workflows", tags=["Workflows"])

# Approval (Maker-Checker) routes
api_router.include_router(approvals_router, prefix="/approvals", tags=["Approvals"])

# Lending/LOS routes
api_router.include_router(lending_router, prefix="/lending", tags=["Lending"])

# Core/System routes
api_router.include_router(integrations_router)

# HRIS routes
api_router.include_router(hris_router, prefix="/hris", tags=["HRIS"])

# Payroll routes
api_router.include_router(payroll_router, prefix="/payroll", tags=["Payroll"])

# Compliance routes
api_router.include_router(compliance_router, prefix="/compliance", tags=["Compliance"])

# Fixed Deposits routes
api_router.include_router(fixed_deposits_router, prefix="/fixed-deposits", tags=["Fixed Deposits"])

# Webhooks (external callbacks)
api_router.include_router(webhooks_router, prefix="/webhooks", tags=["Webhooks"])

# Background Jobs
api_router.include_router(jobs_router, prefix="/jobs", tags=["Background Jobs"])

# Legal Module routes
api_router.include_router(legal_router, tags=["Legal"])

# Customer Portal routes
api_router.include_router(portal_router, tags=["Customer Portal"])

# ESS (Employee Self-Service) Portal routes
api_router.include_router(ess_router, tags=["ESS Portal"])

# Vendor Portal routes
api_router.include_router(vendor_portal_router, tags=["Vendor Portal"])

# Notification System routes
api_router.include_router(notification_router, tags=["Notifications"])

# DMS (Document Management System) routes
api_router.include_router(dms_router, tags=["DMS"])

# Inventory Module routes
api_router.include_router(inventory_router, prefix="/inventory", tags=["Inventory"])

# BI/Analytics routes
api_router.include_router(bi_router, prefix="/bi", tags=["BI/Analytics"])

# Cross-module admin routes (mounted under /api/v1/admin/...)
api_router.include_router(admin_router)
