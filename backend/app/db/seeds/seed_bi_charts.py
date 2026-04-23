"""
Seed data for BI/Analytics module - 195 pre-designed charts across 10 modules

This script seeds:
1. All 195 chart definitions
2. Chart role access assignments
3. Sample dashboards

Run with: python -m app.db.seeds.seed_bi_charts
"""

import asyncio
import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings


# Chart definitions by module
FINANCE_CHARTS = [
    {"code": "FIN_REV_MTD", "name": "Revenue MTD", "type": "KPI", "desc": "Month-to-date revenue"},
    {"code": "FIN_EXP_MTD", "name": "Expenses MTD", "type": "KPI", "desc": "Month-to-date expenses"},
    {"code": "FIN_PROFIT_MTD", "name": "Net Profit MTD", "type": "KPI", "desc": "Month-to-date net profit"},
    {"code": "FIN_PROFIT_MARGIN", "name": "Profit Margin", "type": "GAUGE", "desc": "Profit margin percentage"},
    {"code": "FIN_REV_TREND", "name": "Revenue Trend", "type": "LINE", "desc": "12-month revenue trend"},
    {"code": "FIN_EXP_TREND", "name": "Expense Trend", "type": "LINE", "desc": "12-month expense trend"},
    {"code": "FIN_REV_VS_EXP", "name": "Revenue vs Expenses", "type": "BAR", "desc": "Monthly comparison"},
    {"code": "FIN_GL_BALANCE", "name": "GL Account Balances", "type": "TABLE", "desc": "Top GL accounts by balance"},
    {"code": "FIN_CASH_BALANCE", "name": "Cash & Bank Balance", "type": "KPI", "desc": "Total cash position"},
    {"code": "FIN_CASHFLOW_TREND", "name": "Cash Flow Trend", "type": "AREA", "desc": "Monthly cash flow"},
    {"code": "FIN_AP_OUTSTANDING", "name": "AP Outstanding", "type": "KPI", "desc": "Total payables"},
    {"code": "FIN_AR_OUTSTANDING", "name": "AR Outstanding", "type": "KPI", "desc": "Total receivables"},
    {"code": "FIN_AP_AGING", "name": "AP Aging", "type": "PIE", "desc": "Payables by aging bucket"},
    {"code": "FIN_AR_AGING", "name": "AR Aging", "type": "PIE", "desc": "Receivables by aging bucket"},
    {"code": "FIN_TOP_VENDORS", "name": "Top Vendors by Payable", "type": "BAR", "desc": "Top 10 vendors"},
    {"code": "FIN_TOP_CUSTOMERS", "name": "Top Customers by Receivable", "type": "BAR", "desc": "Top 10 customers"},
    {"code": "FIN_JOURNAL_COUNT", "name": "Journal Entries", "type": "KPI", "desc": "Journals this month"},
    {"code": "FIN_PENDING_APPROVALS", "name": "Pending Approvals", "type": "KPI", "desc": "Finance approvals pending"},
    {"code": "FIN_BUDGET_VS_ACTUAL", "name": "Budget vs Actual", "type": "BAR", "desc": "Monthly budget comparison"},
    {"code": "FIN_EXPENSE_BY_DEPT", "name": "Expenses by Department", "type": "PIE", "desc": "Department-wise expenses"},
    {"code": "FIN_EXPENSE_BY_HEAD", "name": "Expenses by Head", "type": "DONUT", "desc": "Expense head distribution"},
    {"code": "FIN_REVENUE_BY_SOURCE", "name": "Revenue by Source", "type": "PIE", "desc": "Revenue source breakdown"},
    {"code": "FIN_WORKING_CAPITAL", "name": "Working Capital", "type": "KPI", "desc": "Current assets - liabilities"},
    {"code": "FIN_CURRENT_RATIO", "name": "Current Ratio", "type": "GAUGE", "desc": "Liquidity ratio"},
    {"code": "FIN_DEBT_EQUITY", "name": "Debt to Equity", "type": "GAUGE", "desc": "Leverage ratio"},
]

LENDING_CHARTS = [
    {"code": "LEN_AUM", "name": "Assets Under Management", "type": "KPI", "desc": "Total loan portfolio"},
    {"code": "LEN_DISBURSED_MTD", "name": "Disbursements MTD", "type": "KPI", "desc": "Month disbursements"},
    {"code": "LEN_DISBURSED_TREND", "name": "Disbursement Trend", "type": "LINE", "desc": "Monthly disbursement trend"},
    {"code": "LEN_COLLECTION_MTD", "name": "Collections MTD", "type": "KPI", "desc": "Month collections"},
    {"code": "LEN_COLLECTION_TREND", "name": "Collection Trend", "type": "LINE", "desc": "Monthly collection trend"},
    {"code": "LEN_COLLECTION_EFF", "name": "Collection Efficiency", "type": "GAUGE", "desc": "Collection vs demand %"},
    {"code": "LEN_ACTIVE_LOANS", "name": "Active Loans", "type": "KPI", "desc": "Count of active loans"},
    {"code": "LEN_NEW_LOANS_MTD", "name": "New Loans MTD", "type": "KPI", "desc": "New loans this month"},
    {"code": "LEN_LOAN_BY_PRODUCT", "name": "Loans by Product", "type": "PIE", "desc": "Product-wise distribution"},
    {"code": "LEN_LOAN_BY_BRANCH", "name": "Loans by Branch", "type": "BAR", "desc": "Branch-wise distribution"},
    {"code": "LEN_LOAN_BY_STATE", "name": "Loans by State", "type": "BAR", "desc": "State-wise distribution"},
    {"code": "LEN_AVG_TICKET_SIZE", "name": "Avg Ticket Size", "type": "KPI", "desc": "Average loan amount"},
    {"code": "LEN_AVG_TENURE", "name": "Avg Loan Tenure", "type": "KPI", "desc": "Average tenure months"},
    {"code": "LEN_AVG_ROI", "name": "Average ROI", "type": "KPI", "desc": "Average interest rate"},
    {"code": "LEN_INTEREST_INCOME", "name": "Interest Income MTD", "type": "KPI", "desc": "Interest earned"},
    {"code": "LEN_INTEREST_TREND", "name": "Interest Income Trend", "type": "LINE", "desc": "Monthly interest trend"},
    {"code": "LEN_EMI_DUE_TODAY", "name": "EMI Due Today", "type": "KPI", "desc": "Today's EMI demand"},
    {"code": "LEN_EMI_DUE_WEEK", "name": "EMI Due This Week", "type": "KPI", "desc": "Week's EMI demand"},
    {"code": "LEN_OVERDUE_AMOUNT", "name": "Overdue Amount", "type": "KPI", "desc": "Total overdue"},
    {"code": "LEN_OVERDUE_TREND", "name": "Overdue Trend", "type": "LINE", "desc": "Monthly overdue trend"},
    {"code": "LEN_DPD_0_30", "name": "DPD 0-30", "type": "KPI", "desc": "Loans in 0-30 DPD"},
    {"code": "LEN_DPD_31_60", "name": "DPD 31-60", "type": "KPI", "desc": "Loans in 31-60 DPD"},
    {"code": "LEN_DPD_61_90", "name": "DPD 61-90", "type": "KPI", "desc": "Loans in 61-90 DPD"},
    {"code": "LEN_DPD_90_PLUS", "name": "DPD 90+", "type": "KPI", "desc": "Loans in 90+ DPD"},
    {"code": "LEN_DPD_DISTRIBUTION", "name": "DPD Distribution", "type": "PIE", "desc": "DPD bucket distribution"},
    {"code": "LEN_NPA_RATIO", "name": "NPA Ratio", "type": "GAUGE", "desc": "Gross NPA percentage"},
    {"code": "LEN_NPA_AMOUNT", "name": "NPA Amount", "type": "KPI", "desc": "Gross NPA amount"},
    {"code": "LEN_PROVISION_AMOUNT", "name": "Provision Amount", "type": "KPI", "desc": "Total provisions"},
    {"code": "LEN_PROVISION_COVERAGE", "name": "Provision Coverage", "type": "GAUGE", "desc": "PCR percentage"},
    {"code": "LEN_TOP_DEFAULTERS", "name": "Top Defaulters", "type": "TABLE", "desc": "Highest overdue accounts"},
]

HR_CHARTS = [
    {"code": "HR_TOTAL_EMP", "name": "Total Employees", "type": "KPI", "desc": "Active employee count"},
    {"code": "HR_NEW_JOINS_MTD", "name": "New Joins MTD", "type": "KPI", "desc": "Joinings this month"},
    {"code": "HR_ATTRITION_MTD", "name": "Attrition MTD", "type": "KPI", "desc": "Exits this month"},
    {"code": "HR_ATTRITION_RATE", "name": "Attrition Rate", "type": "GAUGE", "desc": "Annual attrition %"},
    {"code": "HR_HEADCOUNT_TREND", "name": "Headcount Trend", "type": "LINE", "desc": "12-month headcount"},
    {"code": "HR_EMP_BY_DEPT", "name": "Employees by Department", "type": "PIE", "desc": "Department distribution"},
    {"code": "HR_EMP_BY_LOCATION", "name": "Employees by Location", "type": "BAR", "desc": "Location-wise count"},
    {"code": "HR_EMP_BY_GRADE", "name": "Employees by Grade", "type": "BAR", "desc": "Grade-wise distribution"},
    {"code": "HR_EMP_BY_GENDER", "name": "Gender Distribution", "type": "PIE", "desc": "Male/Female ratio"},
    {"code": "HR_EMP_BY_AGE", "name": "Age Distribution", "type": "BAR", "desc": "Age group distribution"},
    {"code": "HR_EMP_BY_TENURE", "name": "Tenure Distribution", "type": "BAR", "desc": "Service years distribution"},
    {"code": "HR_AVG_AGE", "name": "Average Age", "type": "KPI", "desc": "Average employee age"},
    {"code": "HR_AVG_TENURE", "name": "Average Tenure", "type": "KPI", "desc": "Average service years"},
    {"code": "HR_PAYROLL_MTD", "name": "Payroll MTD", "type": "KPI", "desc": "Payroll expense"},
    {"code": "HR_PAYROLL_TREND", "name": "Payroll Trend", "type": "LINE", "desc": "Monthly payroll trend"},
    {"code": "HR_LEAVE_BALANCE", "name": "Leave Balance", "type": "TABLE", "desc": "Department leave summary"},
    {"code": "HR_ATTENDANCE_TODAY", "name": "Attendance Today", "type": "KPI", "desc": "Present today"},
    {"code": "HR_ABSENT_TODAY", "name": "Absent Today", "type": "KPI", "desc": "Absent today"},
    {"code": "HR_ATTENDANCE_RATE", "name": "Attendance Rate", "type": "GAUGE", "desc": "Monthly attendance %"},
    {"code": "HR_PENDING_LEAVES", "name": "Pending Leave Requests", "type": "KPI", "desc": "Leaves awaiting approval"},
    {"code": "HR_OPEN_POSITIONS", "name": "Open Positions", "type": "KPI", "desc": "Unfilled vacancies"},
    {"code": "HR_TIME_TO_HIRE", "name": "Time to Hire", "type": "KPI", "desc": "Avg days to fill position"},
    {"code": "HR_TRAINING_HOURS", "name": "Training Hours MTD", "type": "KPI", "desc": "Training hours delivered"},
    {"code": "HR_APPRAISAL_STATUS", "name": "Appraisal Status", "type": "PIE", "desc": "Completed vs pending"},
    {"code": "HR_SALARY_BY_DEPT", "name": "Salary by Department", "type": "BAR", "desc": "Department salary cost"},
]

TREASURY_CHARTS = [
    {"code": "TRE_TOTAL_INVESTMENT", "name": "Total Investments", "type": "KPI", "desc": "Investment portfolio"},
    {"code": "TRE_INVESTMENT_BY_TYPE", "name": "Investments by Type", "type": "PIE", "desc": "FD/Bonds/MF distribution"},
    {"code": "TRE_INVESTMENT_TREND", "name": "Investment Trend", "type": "LINE", "desc": "Monthly investment trend"},
    {"code": "TRE_MATURITY_SCHEDULE", "name": "Maturity Schedule", "type": "BAR", "desc": "Upcoming maturities"},
    {"code": "TRE_INTEREST_EARNED", "name": "Interest Earned MTD", "type": "KPI", "desc": "Interest income"},
    {"code": "TRE_INTEREST_TREND", "name": "Interest Earned Trend", "type": "LINE", "desc": "Monthly interest trend"},
    {"code": "TRE_BORROWINGS", "name": "Total Borrowings", "type": "KPI", "desc": "Outstanding borrowings"},
    {"code": "TRE_BORROWING_BY_TYPE", "name": "Borrowings by Type", "type": "PIE", "desc": "Bank/NCD/CP distribution"},
    {"code": "TRE_INTEREST_PAID", "name": "Interest Paid MTD", "type": "KPI", "desc": "Interest expense"},
    {"code": "TRE_NIM", "name": "Net Interest Margin", "type": "GAUGE", "desc": "NIM percentage"},
    {"code": "TRE_ALM_GAP", "name": "ALM Gap", "type": "BAR", "desc": "Asset-liability gap by bucket"},
    {"code": "TRE_LIQUIDITY_RATIO", "name": "Liquidity Ratio", "type": "GAUGE", "desc": "Liquid assets ratio"},
    {"code": "TRE_COST_OF_FUNDS", "name": "Cost of Funds", "type": "KPI", "desc": "Average borrowing rate"},
    {"code": "TRE_YIELD_ON_ASSETS", "name": "Yield on Assets", "type": "KPI", "desc": "Average lending rate"},
    {"code": "TRE_SPREAD", "name": "Interest Spread", "type": "KPI", "desc": "Yield - Cost of funds"},
    {"code": "TRE_UNUTILIZED_LIMITS", "name": "Unutilized Limits", "type": "KPI", "desc": "Available credit lines"},
    {"code": "TRE_FD_MATURING_WEEK", "name": "FDs Maturing This Week", "type": "TABLE", "desc": "Upcoming FD maturities"},
    {"code": "TRE_CONCENTRATION_RISK", "name": "Concentration Risk", "type": "PIE", "desc": "Borrower concentration"},
    {"code": "TRE_VAR", "name": "Value at Risk", "type": "KPI", "desc": "Portfolio VaR"},
    {"code": "TRE_STRESS_TEST", "name": "Stress Test Impact", "type": "BAR", "desc": "Stress scenario impacts"},
]

PROCUREMENT_CHARTS = [
    {"code": "PRO_PO_MTD", "name": "Purchase Orders MTD", "type": "KPI", "desc": "POs this month"},
    {"code": "PRO_PO_VALUE_MTD", "name": "PO Value MTD", "type": "KPI", "desc": "PO amount this month"},
    {"code": "PRO_PO_TREND", "name": "PO Trend", "type": "LINE", "desc": "Monthly PO trend"},
    {"code": "PRO_PENDING_PO", "name": "Pending POs", "type": "KPI", "desc": "POs awaiting delivery"},
    {"code": "PRO_OVERDUE_PO", "name": "Overdue POs", "type": "KPI", "desc": "Delayed deliveries"},
    {"code": "PRO_VENDOR_COUNT", "name": "Active Vendors", "type": "KPI", "desc": "Approved vendor count"},
    {"code": "PRO_TOP_VENDORS", "name": "Top Vendors by Spend", "type": "BAR", "desc": "Highest spend vendors"},
    {"code": "PRO_SPEND_BY_CATEGORY", "name": "Spend by Category", "type": "PIE", "desc": "Category-wise spend"},
    {"code": "PRO_SPEND_TREND", "name": "Procurement Spend Trend", "type": "LINE", "desc": "Monthly spend trend"},
    {"code": "PRO_AVG_LEAD_TIME", "name": "Average Lead Time", "type": "KPI", "desc": "Avg delivery days"},
    {"code": "PRO_QUALITY_SCORE", "name": "Vendor Quality Score", "type": "GAUGE", "desc": "Average quality rating"},
    {"code": "PRO_ON_TIME_DELIVERY", "name": "On-Time Delivery", "type": "GAUGE", "desc": "Delivery performance %"},
    {"code": "PRO_GRN_MTD", "name": "GRNs MTD", "type": "KPI", "desc": "Goods received this month"},
    {"code": "PRO_PENDING_GRN", "name": "Pending GRNs", "type": "KPI", "desc": "POs awaiting GRN"},
    {"code": "PRO_PENDING_INVOICES", "name": "Pending Vendor Invoices", "type": "KPI", "desc": "Invoices to process"},
    {"code": "PRO_PRICE_VARIANCE", "name": "Price Variance", "type": "BAR", "desc": "Budget vs actual prices"},
    {"code": "PRO_RFQ_OPEN", "name": "Open RFQs", "type": "KPI", "desc": "Active quotation requests"},
    {"code": "PRO_SAVINGS_MTD", "name": "Savings MTD", "type": "KPI", "desc": "Negotiated savings"},
    {"code": "PRO_APPROVAL_PENDING", "name": "Pending Approvals", "type": "KPI", "desc": "POs awaiting approval"},
    {"code": "PRO_VENDOR_PERFORMANCE", "name": "Vendor Performance", "type": "TABLE", "desc": "Vendor scorecards"},
]

COLLECTIONS_CHARTS = [
    {"code": "COL_TARGET_MTD", "name": "Collection Target MTD", "type": "KPI", "desc": "Month target amount"},
    {"code": "COL_ACHIEVED_MTD", "name": "Collection Achieved MTD", "type": "KPI", "desc": "Month actual collection"},
    {"code": "COL_ACHIEVEMENT", "name": "Collection Achievement", "type": "GAUGE", "desc": "Target achievement %"},
    {"code": "COL_TREND", "name": "Collection Trend", "type": "LINE", "desc": "Monthly collection trend"},
    {"code": "COL_BY_CHANNEL", "name": "Collections by Channel", "type": "PIE", "desc": "Cash/Cheque/NACH/UPI"},
    {"code": "COL_BY_BUCKET", "name": "Collections by Bucket", "type": "BAR", "desc": "DPD bucket wise"},
    {"code": "COL_BY_AGENT", "name": "Collections by Agent", "type": "BAR", "desc": "Agent-wise collection"},
    {"code": "COL_EFFICIENCY", "name": "Collection Efficiency", "type": "GAUGE", "desc": "Collected vs assigned %"},
    {"code": "COL_CALLS_TODAY", "name": "Calls Made Today", "type": "KPI", "desc": "Collection calls count"},
    {"code": "COL_PTP_TODAY", "name": "PTP Received Today", "type": "KPI", "desc": "Promise to pay count"},
    {"code": "COL_VISITS_TODAY", "name": "Field Visits Today", "type": "KPI", "desc": "Physical visits count"},
    {"code": "COL_BOUNCE_RATE", "name": "NACH Bounce Rate", "type": "GAUGE", "desc": "NACH failure %"},
    {"code": "COL_BOUNCE_TREND", "name": "Bounce Trend", "type": "LINE", "desc": "Monthly bounce trend"},
    {"code": "COL_RECOVERY_RATE", "name": "Recovery Rate", "type": "GAUGE", "desc": "Recovery vs overdue %"},
    {"code": "COL_LEGAL_CASES", "name": "Active Legal Cases", "type": "KPI", "desc": "Cases in legal"},
    {"code": "COL_RESTRUCTURED", "name": "Restructured Accounts", "type": "KPI", "desc": "Restructure count"},
    {"code": "COL_WRITTEN_OFF", "name": "Written Off MTD", "type": "KPI", "desc": "Write-offs this month"},
    {"code": "COL_RECOVERED_WO", "name": "Recovered from W/O", "type": "KPI", "desc": "Recovery from write-offs"},
    {"code": "COL_AGENT_PERFORMANCE", "name": "Agent Performance", "type": "TABLE", "desc": "Agent scorecards"},
    {"code": "COL_ALLOCATION_STATUS", "name": "Allocation Status", "type": "PIE", "desc": "Allocated vs unallocated"},
]

TAX_CHARTS = [
    {"code": "TAX_TDS_DEDUCTED", "name": "TDS Deducted MTD", "type": "KPI", "desc": "TDS this month"},
    {"code": "TAX_TDS_DEPOSITED", "name": "TDS Deposited MTD", "type": "KPI", "desc": "TDS paid to govt"},
    {"code": "TAX_TDS_PENDING", "name": "TDS Pending Deposit", "type": "KPI", "desc": "TDS due for payment"},
    {"code": "TAX_TDS_TREND", "name": "TDS Trend", "type": "LINE", "desc": "Monthly TDS trend"},
    {"code": "TAX_GST_OUTPUT", "name": "GST Output MTD", "type": "KPI", "desc": "GST collected"},
    {"code": "TAX_GST_INPUT", "name": "GST Input MTD", "type": "KPI", "desc": "GST paid on purchases"},
    {"code": "TAX_GST_PAYABLE", "name": "GST Payable", "type": "KPI", "desc": "Net GST liability"},
    {"code": "TAX_GST_TREND", "name": "GST Trend", "type": "LINE", "desc": "Monthly GST trend"},
    {"code": "TAX_TCS_COLLECTED", "name": "TCS Collected MTD", "type": "KPI", "desc": "TCS this month"},
    {"code": "TAX_RETURN_STATUS", "name": "Return Filing Status", "type": "TABLE", "desc": "Due dates and status"},
    {"code": "TAX_ADVANCE_TAX", "name": "Advance Tax Due", "type": "KPI", "desc": "Next installment due"},
    {"code": "TAX_BY_SECTION", "name": "TDS by Section", "type": "PIE", "desc": "Section-wise TDS"},
    {"code": "TAX_VENDOR_TDS", "name": "Top TDS Vendors", "type": "TABLE", "desc": "Highest TDS deductions"},
    {"code": "TAX_COMPLIANCE_SCORE", "name": "Compliance Score", "type": "GAUGE", "desc": "Filing timeliness %"},
    {"code": "TAX_NOTICES", "name": "Open Tax Notices", "type": "KPI", "desc": "Pending notices"},
]

INVENTORY_CHARTS = [
    {"code": "INV_TOTAL_VALUE", "name": "Total Inventory Value", "type": "KPI", "desc": "Stock value"},
    {"code": "INV_BY_CATEGORY", "name": "Inventory by Category", "type": "PIE", "desc": "Category distribution"},
    {"code": "INV_BY_WAREHOUSE", "name": "Inventory by Warehouse", "type": "BAR", "desc": "Warehouse-wise stock"},
    {"code": "INV_TREND", "name": "Inventory Trend", "type": "LINE", "desc": "Monthly inventory value"},
    {"code": "INV_TURNOVER", "name": "Inventory Turnover", "type": "GAUGE", "desc": "Turnover ratio"},
    {"code": "INV_DAYS_ON_HAND", "name": "Days on Hand", "type": "KPI", "desc": "Average DOH"},
    {"code": "INV_LOW_STOCK", "name": "Low Stock Items", "type": "KPI", "desc": "Below reorder level"},
    {"code": "INV_OUT_OF_STOCK", "name": "Out of Stock Items", "type": "KPI", "desc": "Zero stock items"},
    {"code": "INV_SLOW_MOVING", "name": "Slow Moving Items", "type": "TABLE", "desc": "No movement 90+ days"},
    {"code": "INV_FAST_MOVING", "name": "Fast Moving Items", "type": "TABLE", "desc": "High turnover items"},
    {"code": "INV_RECEIPTS_MTD", "name": "Stock Receipts MTD", "type": "KPI", "desc": "Goods received"},
    {"code": "INV_ISSUES_MTD", "name": "Stock Issues MTD", "type": "KPI", "desc": "Goods issued"},
    {"code": "INV_ADJUSTMENTS", "name": "Stock Adjustments", "type": "KPI", "desc": "Adjustments this month"},
    {"code": "INV_AGEING", "name": "Inventory Ageing", "type": "PIE", "desc": "Age-wise distribution"},
    {"code": "INV_VALUATION_TREND", "name": "Valuation Trend", "type": "LINE", "desc": "Monthly stock value"},
]

LEGAL_CHARTS = [
    {"code": "LEG_ACTIVE_CASES", "name": "Active Cases", "type": "KPI", "desc": "Ongoing legal cases"},
    {"code": "LEG_CASES_BY_TYPE", "name": "Cases by Type", "type": "PIE", "desc": "Civil/Criminal/SARFAESI"},
    {"code": "LEG_CASES_BY_STAGE", "name": "Cases by Stage", "type": "BAR", "desc": "Stage-wise distribution"},
    {"code": "LEG_NEW_CASES_MTD", "name": "New Cases MTD", "type": "KPI", "desc": "Cases filed this month"},
    {"code": "LEG_CLOSED_CASES_MTD", "name": "Closed Cases MTD", "type": "KPI", "desc": "Cases resolved"},
    {"code": "LEG_CASE_TREND", "name": "Case Trend", "type": "LINE", "desc": "Monthly case volume"},
    {"code": "LEG_RECOVERY_MTD", "name": "Legal Recovery MTD", "type": "KPI", "desc": "Amount recovered"},
    {"code": "LEG_RECOVERY_TREND", "name": "Recovery Trend", "type": "LINE", "desc": "Monthly recovery trend"},
    {"code": "LEG_EXPENSES_MTD", "name": "Legal Expenses MTD", "type": "KPI", "desc": "Legal costs"},
    {"code": "LEG_EXPENSES_BY_TYPE", "name": "Expenses by Type", "type": "PIE", "desc": "Fees/Court/Other"},
    {"code": "LEG_HEARINGS_WEEK", "name": "Hearings This Week", "type": "KPI", "desc": "Upcoming hearings"},
    {"code": "LEG_NOTICES_SENT", "name": "Notices Sent MTD", "type": "KPI", "desc": "Legal notices issued"},
    {"code": "LEG_NOTICES_BY_TYPE", "name": "Notices by Type", "type": "PIE", "desc": "DRT/SARFAESI/Recall"},
    {"code": "LEG_ADVOCATE_PERFORMANCE", "name": "Advocate Performance", "type": "TABLE", "desc": "Advocate scorecards"},
    {"code": "LEG_LIMITATION_ALERTS", "name": "Limitation Alerts", "type": "KPI", "desc": "Approaching deadlines"},
]

PORTAL_CHARTS = [
    {"code": "POR_ACTIVE_USERS", "name": "Active Portal Users", "type": "KPI", "desc": "Registered users"},
    {"code": "POR_LOGINS_TODAY", "name": "Logins Today", "type": "KPI", "desc": "Today's logins"},
    {"code": "POR_LOGIN_TREND", "name": "Login Trend", "type": "LINE", "desc": "Daily login trend"},
    {"code": "POR_PAYMENTS_MTD", "name": "Portal Payments MTD", "type": "KPI", "desc": "Online payments"},
    {"code": "POR_PAYMENT_TREND", "name": "Payment Trend", "type": "LINE", "desc": "Monthly payment trend"},
    {"code": "POR_TICKETS_OPEN", "name": "Open Tickets", "type": "KPI", "desc": "Support tickets open"},
    {"code": "POR_TICKET_TREND", "name": "Ticket Trend", "type": "LINE", "desc": "Monthly tickets"},
    {"code": "POR_DOCUMENT_DOWNLOADS", "name": "Document Downloads", "type": "KPI", "desc": "Downloads this month"},
    {"code": "POR_SERVICE_REQUESTS", "name": "Service Requests", "type": "KPI", "desc": "Active requests"},
    {"code": "POR_NPS_SCORE", "name": "NPS Score", "type": "GAUGE", "desc": "Customer satisfaction"},
]

# Module to role mapping
MODULE_ROLES = {
    "FINANCE": ["SUPER_ADMIN", "FINANCE_MANAGER", "ACCOUNTANT"],
    "LENDING": ["SUPER_ADMIN", "LENDING_MANAGER", "LENDING_OFFICER", "CREDIT_MANAGER"],
    "HR": ["SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER"],
    "TREASURY": ["SUPER_ADMIN", "TREASURY_MANAGER", "FINANCE_MANAGER"],
    "PROCUREMENT": ["SUPER_ADMIN", "PROCUREMENT_MANAGER", "PURCHASE_OFFICER"],
    "COLLECTIONS": ["SUPER_ADMIN", "COLLECTIONS_MANAGER", "COLLECTIONS_AGENT"],
    "TAX": ["SUPER_ADMIN", "TAX_MANAGER", "FINANCE_MANAGER"],
    "INVENTORY": ["SUPER_ADMIN", "INVENTORY_MANAGER", "WAREHOUSE_OFFICER"],
    "LEGAL": ["SUPER_ADMIN", "LEGAL_MANAGER", "LEGAL_OFFICER"],
    "PORTAL": ["SUPER_ADMIN", "PORTAL_MANAGER"],
}


def get_chart_config(chart_type: str) -> dict:
    """Get default config for chart type"""
    configs = {
        "KPI": {
            "valueField": "value",
            "subtitleField": "subtitle",
            "changeField": "change",
            "valueFormat": "number",
        },
        "LINE": {
            "xAxisField": "date",
            "series": ["value"],
            "showLegend": True,
            "showGrid": True,
        },
        "BAR": {
            "xAxisField": "category",
            "series": ["value"],
            "showLegend": True,
            "stacked": False,
        },
        "PIE": {
            "valueField": "value",
            "labelField": "name",
            "showLegend": True,
        },
        "DONUT": {
            "valueField": "value",
            "labelField": "name",
            "showLegend": True,
            "innerRadius": 60,
            "outerRadius": 80,
        },
        "AREA": {
            "xAxisField": "date",
            "series": ["value"],
            "showLegend": True,
            "stacked": False,
        },
        "GAUGE": {
            "valueField": "value",
            "minValue": 0,
            "maxValue": 100,
            "thresholds": [
                {"value": 30, "color": "#ef4444"},
                {"value": 70, "color": "#eab308"},
                {"value": 100, "color": "#22c55e"},
            ],
        },
        "TABLE": {
            "columns": [
                {"key": "name", "label": "Name"},
                {"key": "value", "label": "Value", "format": "number"},
            ],
            "pageSize": 10,
            "sortable": True,
        },
    }
    return configs.get(chart_type, {})


async def create_db_session():
    """Create database session without loading all ORM models"""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return async_session()


async def seed_charts(db: AsyncSession) -> dict:
    """Seed all chart definitions using raw SQL"""
    now = datetime.now(timezone.utc)

    # Get all charts by module
    all_charts = [
        (FINANCE_CHARTS, "FINANCE"),
        (LENDING_CHARTS, "LENDING"),
        (HR_CHARTS, "HR"),
        (TREASURY_CHARTS, "TREASURY"),
        (PROCUREMENT_CHARTS, "PROCUREMENT"),
        (COLLECTIONS_CHARTS, "COLLECTIONS"),
        (TAX_CHARTS, "TAX"),
        (INVENTORY_CHARTS, "INVENTORY"),
        (LEGAL_CHARTS, "LEGAL"),
        (PORTAL_CHARTS, "PORTAL"),
    ]

    chart_ids = {}  # code -> (id, module) mapping
    total_created = 0
    total_updated = 0

    for charts, module in all_charts:
        print(f"Seeding {len(charts)} charts for {module} module...")

        for chart in charts:
            chart_id = str(uuid4())
            config = get_chart_config(chart["type"])

            # Check if chart exists
            result = await db.execute(
                text("SELECT id FROM bi_chart_definition WHERE code = :code"),
                {"code": chart["code"]}
            )
            existing = result.fetchone()

            if existing:
                # Update existing
                await db.execute(
                    text("""
                        UPDATE bi_chart_definition
                        SET name = :name, description = :description,
                            module = :module, chart_type = :chart_type,
                            config = :config, updated_at = :updated_at
                        WHERE code = :code
                    """),
                    {
                        "code": chart["code"],
                        "name": chart["name"],
                        "description": chart["desc"],
                        "module": module,
                        "chart_type": chart["type"],
                        "config": json.dumps(config),
                        "updated_at": now,
                    }
                )
                chart_ids[chart["code"]] = (str(existing[0]), module)
                total_updated += 1
            else:
                # Insert new
                await db.execute(
                    text("""
                        INSERT INTO bi_chart_definition (
                            id, code, name, description, module, chart_type,
                            config, data_mapping, is_system, is_active,
                            created_at, updated_at
                        ) VALUES (
                            :id, :code, :name, :description, :module, :chart_type,
                            :config, :data_mapping, :is_system, :is_active,
                            :created_at, :updated_at
                        )
                    """),
                    {
                        "id": chart_id,
                        "code": chart["code"],
                        "name": chart["name"],
                        "description": chart["desc"],
                        "module": module,
                        "chart_type": chart["type"],
                        "config": json.dumps(config),
                        "data_mapping": "{}",
                        "is_system": True,
                        "is_active": True,
                        "created_at": now,
                        "updated_at": now,
                    }
                )
                chart_ids[chart["code"]] = (chart_id, module)
                total_created += 1

    await db.commit()
    print(f"Charts: {total_created} created, {total_updated} updated (Total: {len(chart_ids)})")
    return chart_ids


async def seed_role_access(db: AsyncSession, chart_ids: dict):
    """Seed chart role access based on module"""
    now = datetime.now(timezone.utc)

    # Get all roles from database
    result = await db.execute(text("SELECT id, code FROM mst_role WHERE is_active = true"))
    roles = {row[1]: str(row[0]) for row in result.fetchall()}

    if not roles:
        print("No roles found in database, skipping role access seeding")
        return

    print(f"Found {len(roles)} roles: {list(roles.keys())}")

    access_created = 0
    access_skipped = 0

    for chart_code, (chart_id, module) in chart_ids.items():
        module_roles = MODULE_ROLES.get(module, ["SUPER_ADMIN"])

        for role_code in module_roles:
            role_id = roles.get(role_code)
            if not role_id:
                continue

            # Check if access already exists
            result = await db.execute(
                text("""
                    SELECT id FROM bi_chart_role_access
                    WHERE chart_definition_id = :chart_id AND role_id = :role_id
                """),
                {"chart_id": chart_id, "role_id": role_id}
            )
            if result.fetchone():
                access_skipped += 1
                continue

            # Create new access
            access_id = str(uuid4())
            await db.execute(
                text("""
                    INSERT INTO bi_chart_role_access (
                        id, chart_definition_id, role_id, is_active,
                        created_at, updated_at
                    ) VALUES (
                        :id, :chart_definition_id, :role_id, :is_active,
                        :created_at, :updated_at
                    )
                """),
                {
                    "id": access_id,
                    "chart_definition_id": chart_id,
                    "role_id": role_id,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                }
            )
            access_created += 1

    await db.commit()
    print(f"Chart role access: {access_created} created, {access_skipped} already existed")


async def seed_sample_dashboards(db: AsyncSession):
    """Create sample dashboards for demonstration"""
    now = datetime.now(timezone.utc)

    # Get first organization
    result = await db.execute(
        text("SELECT id, name FROM mst_organization WHERE is_active = true LIMIT 1")
    )
    org = result.fetchone()

    if not org:
        print("No organization found, skipping dashboard seeding")
        return

    org_id, org_name = str(org[0]), org[1]
    print(f"Using organization: {org_name}")

    # Get SUPER_ADMIN role for dashboard access
    result = await db.execute(text("SELECT id FROM mst_role WHERE code = 'SUPER_ADMIN'"))
    super_admin_row = result.fetchone()
    super_admin_role_id = str(super_admin_row[0]) if super_admin_row else None

    dashboards = [
        {
            "code": "FINANCE_OVERVIEW",
            "name": "Finance Overview",
            "description": "Key financial metrics and trends",
            "is_default": True,
            "is_public": True,
        },
        {
            "code": "LENDING_DASHBOARD",
            "name": "Lending Dashboard",
            "description": "Loan portfolio and collection metrics",
            "is_default": False,
            "is_public": False,
        },
        {
            "code": "HR_ANALYTICS",
            "name": "HR Analytics",
            "description": "Employee metrics and workforce analytics",
            "is_default": False,
            "is_public": False,
        },
    ]

    created = 0
    updated = 0

    for dashboard_data in dashboards:
        # Check if dashboard already exists
        result = await db.execute(
            text("""
                SELECT id FROM bi_dashboard
                WHERE organization_id = :org_id AND code = :code
            """),
            {"org_id": org_id, "code": dashboard_data["code"]}
        )
        existing = result.fetchone()

        if existing:
            await db.execute(
                text("""
                    UPDATE bi_dashboard
                    SET name = :name, description = :description, updated_at = :updated_at
                    WHERE id = :id
                """),
                {
                    "id": str(existing[0]),
                    "name": dashboard_data["name"],
                    "description": dashboard_data["description"],
                    "updated_at": now,
                }
            )
            updated += 1
        else:
            dashboard_id = str(uuid4())
            await db.execute(
                text("""
                    INSERT INTO bi_dashboard (
                        id, code, name, description, organization_id,
                        is_default, is_public, auto_refresh, refresh_interval_seconds,
                        display_order, is_active, created_at, updated_at
                    ) VALUES (
                        :id, :code, :name, :description, :org_id,
                        :is_default, :is_public, :auto_refresh, :refresh_interval,
                        :display_order, :is_active, :created_at, :updated_at
                    )
                """),
                {
                    "id": dashboard_id,
                    "code": dashboard_data["code"],
                    "name": dashboard_data["name"],
                    "description": dashboard_data["description"],
                    "org_id": org_id,
                    "is_default": dashboard_data["is_default"],
                    "is_public": dashboard_data["is_public"],
                    "auto_refresh": True,
                    "refresh_interval": 300,
                    "display_order": 0,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                }
            )
            created += 1

            # Add role access for SUPER_ADMIN
            if super_admin_role_id:
                access_id = str(uuid4())
                await db.execute(
                    text("""
                        INSERT INTO bi_dashboard_role_access (
                            id, dashboard_id, role_id, can_view, can_edit,
                            show_on_landing, landing_order, is_active,
                            created_at, updated_at
                        ) VALUES (
                            :id, :dashboard_id, :role_id, :can_view, :can_edit,
                            :show_on_landing, :landing_order, :is_active,
                            :created_at, :updated_at
                        )
                    """),
                    {
                        "id": access_id,
                        "dashboard_id": dashboard_id,
                        "role_id": super_admin_role_id,
                        "can_view": True,
                        "can_edit": True,
                        "show_on_landing": True,
                        "landing_order": 0,
                        "is_active": True,
                        "created_at": now,
                        "updated_at": now,
                    }
                )

    await db.commit()
    print(f"Dashboards: {created} created, {updated} updated")


async def main():
    """Main seeding function"""
    print("=" * 60)
    print("BI/Analytics Module - Seeding 195 Pre-designed Charts")
    print("=" * 60)

    db = await create_db_session()
    try:
        # Seed chart definitions
        chart_ids = await seed_charts(db)

        # Seed role access
        await seed_role_access(db, chart_ids)

        # Seed sample dashboards
        await seed_sample_dashboards(db)

        print("=" * 60)
        print("Seeding completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"Error during seeding: {e}")
        await db.rollback()
        raise
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
