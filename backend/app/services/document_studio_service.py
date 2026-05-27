"""Enterprise Document Studio service."""

from __future__ import annotations

import hashlib
import html
import re
from datetime import UTC, datetime
from datetime import date as date_type
from io import BytesIO
from typing import Any
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.document_studio import (
    DocumentModule,
    DocumentPackage,
    DocumentPackageItem,
    DocumentPackageStatus,
    DocumentStudioTemplate,
    DocumentStudioTemplateVersion,
    DocumentTemplateStatus,
    GeneratedDocument,
)
from app.services.dms.filing_service import DocumentFilingService

_MERGE_RE = re.compile(r"{{\s*([a-zA-Z0-9_.-]+)(?:\s*\|\s*([a-zA-Z0-9_]+))?\s*}}")


def _variable(
    key: str,
    label: str,
    description: str,
    formatter: str | None = None,
) -> dict[str, Any]:
    value = {"key": key, "label": label, "description": description}
    if formatter:
        value["formatter"] = formatter
    return value


COMMON_VARIABLES: dict[str, list[dict[str, Any]]] = {
    "ORGANIZATION": [
        _variable("organization.name", "Organization Name", "Tenant legal name"),
        _variable(
            "organization.registeredAddress",
            "Registered Address",
            "Tenant registered address",
        ),
    ],
    "ENTITY": [
        _variable("entity.entityCode", "Entity Code", "Borrower or party business code"),
        _variable("entity.legalName", "Legal Name", "Borrower or party legal name"),
        _variable("entity.pan", "PAN", "Masked PAN where required", "maskPan"),
    ],
    "LENDING": [
        _variable(
            "application.applicationNumber",
            "Application Number",
            "Loan application number",
        ),
        _variable("sanction.sanctionNumber", "Sanction Number", "Sanction reference"),
        _variable(
            "sanction.sanctionedAmount",
            "Sanction Amount",
            "Approved amount",
            "amount",
        ),
        _variable("loanAccount.accountNumber", "Loan Account", "Loan account number"),
        _variable(
            "loanAccount.interestRate",
            "Interest Rate",
            "Applicable rate",
            "percent",
        ),
    ],
    "IIF_CLAIM": [
        _variable("scheme.schemeCode", "Scheme Code", "Interest subvention scheme code"),
        _variable("scheme.schemeName", "Scheme Name", "Interest subvention scheme name"),
        _variable("claim.claimReference", "Claim Reference", "Subvention claim reference"),
        _variable("claim.periodStart", "Claim Period Start", "Claim period start date", "date"),
        _variable("claim.periodEnd", "Claim Period End", "Claim period end date", "date"),
        _variable(
            "claim.interestPaidInPeriod",
            "Interest Paid",
            "Interest paid by borrower during the claim period",
            "amount",
        ),
        _variable(
            "claim.applicableSubventionAmount",
            "Subvention Amount",
            "Applicable interest subvention amount",
            "amount",
        ),
        _variable("claim.status", "Claim Status", "Current claim workflow status"),
        _variable(
            "claim.repaymentRecordText",
            "Paid EMI/EPI Details",
            "Installment-wise paid EMI/EPI details for the claim period",
        ),
        _variable(
            "account.lastEmiStatus",
            "Last EMI/EPI Status",
            "Latest installment status as of the claim period end",
        ),
    ],
    "TREASURY": [
        _variable("lender.lenderCode", "Lender Code", "Treasury lender code"),
        _variable("lender.name", "Lender Name", "Funding source name"),
        _variable("facility.facilityNumber", "Facility Number", "Borrowing facility reference"),
        _variable(
            "facility.sanctionAmount", "Facility Amount", "Sanctioned facility amount", "amount"
        ),
        _variable("drawdown.drawdownNumber", "Drawdown Number", "Drawdown reference"),
    ],
    "HRIS": [
        _variable("employee.employeeCode", "Employee Code", "Employee number"),
        _variable("employee.fullName", "Employee Name", "Employee full name"),
        _variable("employee.designation", "Designation", "Employee designation"),
        _variable("employee.department", "Department", "Employee department"),
        _variable("employee.dateOfJoining", "Date of Joining", "Employee joining date", "date"),
    ],
    "PAYROLL": [
        _variable("payroll.period", "Payroll Period", "Payroll month or period"),
        _variable("payroll.netPay", "Net Pay", "Net payable salary", "amount"),
        _variable("payroll.grossPay", "Gross Pay", "Gross salary", "amount"),
        _variable("payroll.totalDeductions", "Total Deductions", "Total deductions", "amount"),
        _variable("payroll.payslipNumber", "Payslip Number", "Payslip reference"),
    ],
    "LEGAL": [
        _variable("legal.caseNumber", "Case Number", "Legal case number"),
        _variable("legal.noticeDate", "Notice Date", "Date of legal notice", "date"),
        _variable("legal.borrowerName", "Borrower Name", "Borrower or respondent name"),
        _variable("legal.outstandingAmount", "Outstanding Amount", "Outstanding amount", "amount"),
    ],
    "FINANCE": [
        _variable("finance.financialYear", "Financial Year", "Financial year"),
        _variable("finance.period", "Period", "Accounting period"),
        _variable("finance.balance", "Balance", "Confirmation balance", "amount"),
    ],
    "AP_AR": [
        _variable("vendor.vendorCode", "Vendor Code", "Vendor code"),
        _variable("vendor.name", "Vendor Name", "Vendor legal name"),
        _variable("customer.customerCode", "Customer Code", "Customer code"),
        _variable("customer.name", "Customer Name", "Customer legal name"),
        _variable("payment.reference", "Payment Reference", "Payment reference"),
        _variable("payment.amount", "Payment Amount", "Payment amount", "amount"),
    ],
    "ESS": [
        _variable("request.requestNumber", "Request Number", "ESS request number"),
        _variable("request.status", "Request Status", "ESS request status"),
    ],
    "BORROWER_PORTAL": [
        _variable("portal.requestNumber", "Request Number", "Borrower service request number"),
        _variable("portal.requestType", "Request Type", "Borrower service request type"),
    ],
    "VENDOR_PORTAL": [
        _variable(
            "vendor.registrationNumber", "Registration Number", "Vendor registration reference"
        ),
        _variable("vendor.complianceStatus", "Compliance Status", "Vendor compliance status"),
    ],
}

DEFAULT_DOCUMENT_TEMPLATES: list[dict[str, Any]] = [
    {
        "module": DocumentModule.LENDING,
        "document_type": "SANCTION_LETTER",
        "code": "SANCTION_LETTER_DEFAULT",
        "name": "Default Sanction Letter",
        "entity_type": "sanction",
        "body": (
            "<h2>Sanction Letter</h2>"
            "Dear {{ entity.legalName }},<br/><br/>"
            "We are pleased to sanction loan reference {{ sanction.sanctionNumber }} "
            "for {{ sanction.sanctionedAmount | amount }} at "
            "{{ loanAccount.interestRate | percent }} p.a.<br/><br/>"
            "This sanction is valid until {{ sanction.validityDate }}."
        ),
        "required_variables": ["entity.legalName", "sanction.sanctionNumber"],
    },
    {
        "module": DocumentModule.LENDING,
        "document_type": "APPROVAL_LETTER",
        "code": "LOAN_APPROVAL_LETTER_DEFAULT",
        "name": "Default Loan Approval Letter",
        "entity_type": "application",
        "body": (
            "<h2>Loan Approval Letter</h2>"
            "<p>Dear {{ entity.legalName }},</p>"
            "<p>Your application {{ application.applicationNumber }} has been approved "
            "for further sanction processing.</p>"
        ),
        "required_variables": ["entity.legalName", "application.applicationNumber"],
    },
    {
        "module": DocumentModule.LENDING,
        "document_type": "KFS",
        "code": "KFS_DEFAULT",
        "name": "Default Key Facts Statement",
        "entity_type": "application",
        "body": (
            "<h2>Key Facts Statement</h2>"
            "<p>Borrower: {{ entity.legalName }}</p>"
            "<p>Application: {{ application.applicationNumber }}</p>"
            "<p>Sanctioned amount: {{ sanction.sanctionedAmount | amount }}</p>"
            "<p>Annualized rate: {{ loanAccount.interestRate | percent }}</p>"
        ),
        "required_variables": ["entity.legalName", "application.applicationNumber"],
    },
    {
        "module": DocumentModule.LENDING,
        "document_type": "DISBURSEMENT_ADVICE",
        "code": "DISBURSEMENT_ADVICE_DEFAULT",
        "name": "Default Disbursement Advice",
        "entity_type": "loan_account",
        "body": (
            "<h2>Disbursement Advice</h2>"
            "<p>Loan account {{ loanAccount.accountNumber }} has been processed "
            "for disbursement as per approved terms.</p>"
        ),
        "required_variables": ["loanAccount.accountNumber"],
    },
    {
        "module": DocumentModule.LENDING,
        "document_type": "NDC",
        "code": "NDC_DEFAULT",
        "name": "Default No Dues Certificate",
        "entity_type": "loan_account",
        "body": (
            "<h2>No Dues Certificate</h2>"
            "This is to certify that dues for loan account "
            "{{ loanAccount.accountNumber }} of {{ entity.legalName }} are closed."
        ),
        "required_variables": ["entity.legalName", "loanAccount.accountNumber"],
    },
    {
        "module": DocumentModule.LENDING,
        "document_type": "FORECLOSURE_LETTER",
        "code": "FORECLOSURE_LETTER_DEFAULT",
        "name": "Default Foreclosure Letter",
        "entity_type": "loan_account",
        "body": (
            "<h2>Foreclosure Letter</h2>"
            "<p>Foreclosure quote for loan {{ loanAccount.accountNumber }} is enclosed. "
            "Please make payment within the validity period.</p>"
        ),
        "required_variables": ["loanAccount.accountNumber"],
    },
    {
        "module": DocumentModule.LENDING,
        "document_type": "IIF_CLAIM_CERTIFICATE",
        "code": "IIF_CLAIM_CERTIFICATE_DEFAULT",
        "name": "Default IIF Claim Certificate",
        "entity_type": "subvention_claim",
        "body": (
            "This is to certify that interest subvention claim "
            "{{ claim.claimReference }} under {{ scheme.schemeName }} "
            "has been reviewed for {{ entity.legalName }} against SFC loan account "
            "{{ loanAccount.accountNumber }} for the period "
            "{{ claim.periodStart | date }} to {{ claim.periodEnd | date }}.<br/><br/>"
            "Interest paid during the period: {{ claim.interestPaidInPeriod | amount }}.<br/>"
            "Applicable subvention amount: {{ claim.applicableSubventionAmount | amount }}.<br/>"
            "Claim status: {{ claim.status }}.<br/>"
            "Latest EMI/EPI status: {{ account.lastEmiStatus }}.<br/><br/>"
            "Paid EMI/EPI details: {{ claim.repaymentRecordText }}."
        ),
        "required_variables": [
            "entity.legalName",
            "loanAccount.accountNumber",
            "claim.claimReference",
            "claim.periodStart",
            "claim.periodEnd",
            "claim.applicableSubventionAmount",
        ],
    },
    {
        "module": DocumentModule.LENDING,
        "document_type": "PRE_CLOSURE_QUOTE",
        "code": "PRE_CLOSURE_QUOTE_DEFAULT",
        "name": "Default Pre-Closure Quote",
        "entity_type": "loan_account",
        "body": "<h2>Pre-Closure Quote</h2><p>Quote for {{ loanAccount.accountNumber }}.</p>",
        "required_variables": ["loanAccount.accountNumber"],
    },
    {
        "module": DocumentModule.LENDING,
        "document_type": "DEMAND_NOTICE",
        "code": "DEMAND_NOTICE_DEFAULT",
        "name": "Default Demand Notice",
        "entity_type": "loan_account",
        "body": (
            "<h2>Demand Notice</h2>"
            "<p>Dear {{ entity.legalName }}, overdue dues are payable on "
            "loan account {{ loanAccount.accountNumber }}.</p>"
        ),
        "required_variables": ["entity.legalName", "loanAccount.accountNumber"],
    },
    {
        "module": DocumentModule.LENDING,
        "document_type": "OTS_LETTER",
        "code": "OTS_LETTER_DEFAULT",
        "name": "Default OTS Approval Letter",
        "entity_type": "loan_account",
        "body": "<h2>OTS Approval Letter</h2><p>OTS terms for {{ loanAccount.accountNumber }}.</p>",
        "required_variables": ["loanAccount.accountNumber"],
    },
    {
        "module": DocumentModule.LENDING,
        "document_type": "RESTRUCTURE_ADDENDUM",
        "code": "RESTRUCTURE_ADDENDUM_DEFAULT",
        "name": "Default Restructure Addendum",
        "entity_type": "loan_account",
        "body": (
            "<h2>Restructure Addendum</h2><p>Revised terms for {{ loanAccount.accountNumber }}.</p>"
        ),
        "required_variables": ["loanAccount.accountNumber"],
    },
    {
        "module": DocumentModule.LENDING,
        "document_type": "RATE_REVISION_INTIMATION",
        "code": "RATE_REVISION_INTIMATION_DEFAULT",
        "name": "Default Rate Revision Intimation",
        "entity_type": "loan_account",
        "body": (
            "<h2>Rate Revision Intimation</h2>"
            "<p>Applicable rate for {{ loanAccount.accountNumber }} is revised to "
            "{{ loanAccount.interestRate | percent }}.</p>"
        ),
        "required_variables": ["loanAccount.accountNumber", "loanAccount.interestRate"],
    },
    {
        "module": DocumentModule.LENDING,
        "document_type": "INTEREST_CERT",
        "code": "INTEREST_CERT_DEFAULT",
        "name": "Default Interest Certificate",
        "entity_type": "loan_account",
        "body": (
            "<h2>Interest Certificate</h2><p>Certificate for {{ loanAccount.accountNumber }}.</p>"
        ),
        "required_variables": ["loanAccount.accountNumber"],
    },
    {
        "module": DocumentModule.LENDING,
        "document_type": "STATEMENT_OF_ACCOUNT",
        "code": "STATEMENT_OF_ACCOUNT_DEFAULT",
        "name": "Default Statement of Account",
        "entity_type": "loan_account",
        "body": (
            "<h2>Statement of Account</h2><p>Statement for {{ loanAccount.accountNumber }}.</p>"
        ),
        "required_variables": ["loanAccount.accountNumber"],
    },
    {
        "module": DocumentModule.LENDING,
        "document_type": "CHARGE_RELEASE_LETTER",
        "code": "CHARGE_RELEASE_LETTER_DEFAULT",
        "name": "Default Charge Release Letter",
        "entity_type": "loan_account",
        "body": "<h2>Charge Release Letter</h2><p>Release for {{ loanAccount.accountNumber }}.</p>",
        "required_variables": ["loanAccount.accountNumber"],
    },
    {
        "module": DocumentModule.TREASURY,
        "document_type": "LENDER_FACILITY_LETTER",
        "code": "LENDER_FACILITY_LETTER_DEFAULT",
        "name": "Default Lender Facility Letter",
        "entity_type": "lender",
        "body": (
            "<h2>Lender Facility Letter</h2><p>Facility communication for {{ lender.name }}.</p>"
        ),
        "required_variables": ["lender.name"],
    },
    {
        "module": DocumentModule.TREASURY,
        "document_type": "DRAWDOWN_REQUEST",
        "code": "DRAWDOWN_REQUEST_DEFAULT",
        "name": "Default Drawdown Request",
        "entity_type": "lender",
        "body": (
            "<h2>Drawdown Request</h2>"
            "<p>Request to {{ lender.name }} for {{ drawdown.drawdownNumber }}.</p>"
        ),
        "required_variables": ["lender.name"],
    },
    {
        "module": DocumentModule.TREASURY,
        "document_type": "REPAYMENT_ADVICE",
        "code": "LENDER_REPAYMENT_ADVICE_DEFAULT",
        "name": "Default Lender Repayment Advice",
        "entity_type": "lender",
        "body": "<h2>Repayment Advice</h2><p>Repayment advice for {{ lender.name }}.</p>",
        "required_variables": ["lender.name"],
    },
    {
        "module": DocumentModule.TREASURY,
        "document_type": "COVENANT_COMPLIANCE_CERTIFICATE",
        "code": "COVENANT_COMPLIANCE_CERTIFICATE_DEFAULT",
        "name": "Default Covenant Compliance Certificate",
        "entity_type": "lender",
        "body": "<h2>Covenant Compliance Certificate</h2><p>Issued to {{ lender.name }}.</p>",
        "required_variables": ["lender.name"],
    },
    {
        "module": DocumentModule.HRIS,
        "document_type": "OFFER_LETTER",
        "code": "OFFER_LETTER_DEFAULT",
        "name": "Default Offer Letter",
        "entity_type": "employee",
        "body": (
            "<h2>Offer Letter</h2>"
            "<p>Dear {{ employee.fullName }}, we are pleased to offer you employment.</p>"
        ),
        "required_variables": ["employee.fullName"],
    },
    {
        "module": DocumentModule.HRIS,
        "document_type": "APPOINTMENT_LETTER",
        "code": "APPOINTMENT_LETTER_DEFAULT",
        "name": "Default Appointment Letter",
        "entity_type": "employee",
        "body": (
            "<h2>Appointment Letter</h2>"
            "<p>Dear {{ employee.fullName }}, welcome to the organization.</p>"
        ),
        "required_variables": ["employee.fullName"],
    },
    {
        "module": DocumentModule.HRIS,
        "document_type": "EMPLOYEE_LETTER",
        "code": "EMPLOYEE_LETTER_DEFAULT",
        "name": "Default Employee Letter",
        "entity_type": "employee",
        "body": "Dear {{ employee.fullName }},",
        "required_variables": ["employee.fullName"],
    },
    {
        "module": DocumentModule.HRIS,
        "document_type": "EXPERIENCE_LETTER",
        "code": "EXPERIENCE_LETTER_DEFAULT",
        "name": "Default Experience Letter",
        "entity_type": "employee",
        "body": (
            "<h2>Experience Letter</h2>"
            "<p>This certifies the employment of {{ employee.fullName }}.</p>"
        ),
        "required_variables": ["employee.fullName"],
    },
    {
        "module": DocumentModule.HRIS,
        "document_type": "RELIEVING_LETTER",
        "code": "RELIEVING_LETTER_DEFAULT",
        "name": "Default Relieving Letter",
        "entity_type": "employee",
        "body": "<h2>Relieving Letter</h2><p>{{ employee.fullName }} is relieved from duties.</p>",
        "required_variables": ["employee.fullName"],
    },
    {
        "module": DocumentModule.HRIS,
        "document_type": "TRAINING_CERTIFICATE",
        "code": "TRAINING_CERTIFICATE_DEFAULT",
        "name": "Default Training Certificate",
        "entity_type": "employee",
        "body": "<h2>Training Certificate</h2><p>Awarded to {{ employee.fullName }}.</p>",
        "required_variables": ["employee.fullName"],
    },
    {
        "module": DocumentModule.PAYROLL,
        "document_type": "PAYSLIP",
        "code": "PAYSLIP_DEFAULT",
        "name": "Default Payslip",
        "entity_type": "employee",
        "body": "Payslip for {{ payroll.period }}. Net pay {{ payroll.netPay | amount }}.",
        "required_variables": ["payroll.period", "payroll.netPay"],
    },
    {
        "module": DocumentModule.PAYROLL,
        "document_type": "SALARY_REVISION_LETTER",
        "code": "SALARY_REVISION_LETTER_DEFAULT",
        "name": "Default Salary Revision Letter",
        "entity_type": "employee",
        "body": (
            "<h2>Salary Revision Letter</h2>"
            "<p>Dear {{ employee.fullName }}, revised gross pay is "
            "{{ payroll.grossPay | amount }}.</p>"
        ),
        "required_variables": ["employee.fullName", "payroll.grossPay"],
    },
    {
        "module": DocumentModule.PAYROLL,
        "document_type": "BONUS_LETTER",
        "code": "BONUS_LETTER_DEFAULT",
        "name": "Default Bonus Letter",
        "entity_type": "employee",
        "body": (
            "<h2>Bonus Letter</h2><p>Dear {{ employee.fullName }}, bonus payment is approved.</p>"
        ),
        "required_variables": ["employee.fullName"],
    },
    {
        "module": DocumentModule.PAYROLL,
        "document_type": "FNF_STATEMENT",
        "code": "FNF_STATEMENT_DEFAULT",
        "name": "Default Full and Final Statement",
        "entity_type": "employee",
        "body": "<h2>Full and Final Statement</h2><p>Settlement for {{ employee.fullName }}.</p>",
        "required_variables": ["employee.fullName"],
    },
    {
        "module": DocumentModule.LEGAL,
        "document_type": "LEGAL_NOTICE",
        "code": "LEGAL_NOTICE_DEFAULT",
        "name": "Default Legal Notice",
        "entity_type": "legal_case",
        "body": (
            "<h2>Legal Notice</h2><p>Case {{ legal.caseNumber }} for {{ legal.borrowerName }}.</p>"
        ),
        "required_variables": ["legal.caseNumber"],
    },
    {
        "module": DocumentModule.LEGAL,
        "document_type": "SARFAESI_13_2_NOTICE",
        "code": "SARFAESI_13_2_NOTICE_DEFAULT",
        "name": "Default SARFAESI 13(2) Notice",
        "entity_type": "legal_case",
        "body": (
            "<h2>SARFAESI 13(2) Notice</h2>"
            "<p>Outstanding amount {{ legal.outstandingAmount | amount }}.</p>"
        ),
        "required_variables": ["legal.outstandingAmount"],
    },
    {
        "module": DocumentModule.LEGAL,
        "document_type": "ARBITRATION_NOTICE",
        "code": "ARBITRATION_NOTICE_DEFAULT",
        "name": "Default Arbitration Notice",
        "entity_type": "legal_case",
        "body": "<h2>Arbitration Notice</h2><p>Case {{ legal.caseNumber }}.</p>",
        "required_variables": ["legal.caseNumber"],
    },
    {
        "module": DocumentModule.FINANCE,
        "document_type": "BALANCE_CONFIRMATION",
        "code": "BALANCE_CONFIRMATION_DEFAULT",
        "name": "Default Balance Confirmation",
        "entity_type": "financial_year",
        "body": (
            "<h2>Balance Confirmation</h2>"
            "<p>Balance for {{ finance.financialYear }} is "
            "{{ finance.balance | amount }}.</p>"
        ),
        "required_variables": ["finance.financialYear"],
    },
    {
        "module": DocumentModule.FINANCE,
        "document_type": "AUDIT_CONFIRMATION",
        "code": "AUDIT_CONFIRMATION_DEFAULT",
        "name": "Default Audit Confirmation",
        "entity_type": "financial_year",
        "body": "<h2>Audit Confirmation</h2><p>Confirmation for {{ finance.financialYear }}.</p>",
        "required_variables": ["finance.financialYear"],
    },
    {
        "module": DocumentModule.AP_AR,
        "document_type": "VENDOR_CERTIFICATE",
        "code": "VENDOR_CERTIFICATE_DEFAULT",
        "name": "Default Vendor Certificate",
        "entity_type": "vendor",
        "body": "<h2>Vendor Certificate</h2><p>Issued for {{ vendor.name }}.</p>",
        "required_variables": ["vendor.name"],
    },
    {
        "module": DocumentModule.AP_AR,
        "document_type": "PAYMENT_ADVICE",
        "code": "PAYMENT_ADVICE_DEFAULT",
        "name": "Default Payment Advice",
        "entity_type": "vendor",
        "body": (
            "<h2>Payment Advice</h2>"
            "<p>Payment {{ payment.reference }} of {{ payment.amount | amount }}.</p>"
        ),
        "required_variables": ["payment.reference"],
    },
    {
        "module": DocumentModule.VENDOR_PORTAL,
        "document_type": "VENDOR_REGISTRATION_APPROVAL",
        "code": "VENDOR_REGISTRATION_APPROVAL_DEFAULT",
        "name": "Default Vendor Registration Approval",
        "entity_type": "vendor",
        "body": (
            "<h2>Vendor Registration Approval</h2>"
            "<p>Registration {{ vendor.registrationNumber }} is approved.</p>"
        ),
        "required_variables": ["vendor.registrationNumber"],
    },
    {
        "module": DocumentModule.BORROWER_PORTAL,
        "document_type": "SERVICE_REQUEST_ACK",
        "code": "BORROWER_SERVICE_REQUEST_ACK_DEFAULT",
        "name": "Default Borrower Service Request Acknowledgement",
        "entity_type": "portal_request",
        "body": (
            "<h2>Service Request Acknowledgement</h2>"
            "<p>Request {{ portal.requestNumber }} has been received.</p>"
        ),
        "required_variables": ["portal.requestNumber"],
    },
    {
        "module": DocumentModule.ESS,
        "document_type": "LEAVE_APPROVAL",
        "code": "ESS_LEAVE_APPROVAL_DEFAULT",
        "name": "Default ESS Leave Approval",
        "entity_type": "employee",
        "body": (
            "<h2>Leave Approval</h2>"
            "<p>Dear {{ employee.fullName }}, your leave request is approved.</p>"
        ),
        "required_variables": ["employee.fullName"],
    },
    {
        "module": DocumentModule.ESS,
        "document_type": "REIMBURSEMENT_APPROVAL",
        "code": "ESS_REIMBURSEMENT_APPROVAL_DEFAULT",
        "name": "Default ESS Reimbursement Approval",
        "entity_type": "employee",
        "body": (
            "<h2>Reimbursement Approval</h2><p>Request {{ request.requestNumber }} is approved.</p>"
        ),
        "required_variables": ["request.requestNumber"],
    },
]


def _lookup(context: dict[str, Any], key: str) -> Any:
    value: Any = context
    for part in key.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            value = getattr(value, part, None)
        if value is None:
            return None
    return value


def _format(value: Any, formatter: str | None) -> str:
    if value is None:
        return ""
    if formatter == "amount":
        try:
            return f"₹ {float(value):,.2f}"
        except (TypeError, ValueError):
            return str(value)
    if formatter == "percent":
        try:
            return f"{float(value):.2f}%"
        except (TypeError, ValueError):
            return str(value)
    if formatter == "date":
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date_type):
            return value.isoformat()
        return str(value)
    if formatter == "uppercase":
        return str(value).upper()
    if formatter == "titleCase":
        return str(value).title()
    if formatter == "maskPan":
        raw = str(value)
        return f"XXXXX{raw[-5:]}" if len(raw) >= 5 else "XXXXX"
    return str(value)


def render_template_text(template: str, context: dict[str, Any]) -> tuple[str, list[str]]:
    missing: list[str] = []

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        formatter = match.group(2)
        value = _lookup(context, key)
        if value is None:
            missing.append(key)
            return ""
        return html.escape(_format(value, formatter))

    return _MERGE_RE.sub(replace, template or ""), sorted(set(missing))


def _html_to_pdf_bytes(*, title: str, rendered_html: str) -> bytes:
    """Small ReportLab renderer for v1 generated letter PDFs."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=title,
    )
    styles = getSampleStyleSheet()
    story = []
    for block in rendered_html.split("\n"):
        text = block.strip()
        if not text:
            story.append(Spacer(1, 4 * mm))
            continue
        story.append(Paragraph(text, styles["Normal"]))
        story.append(Spacer(1, 2 * mm))
    doc.build(story)
    return buffer.getvalue()


class DocumentStudioService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.filing = DocumentFilingService(db)

    async def list_templates(
        self,
        *,
        organization_id: UUID,
        module: DocumentModule | None = None,
        document_type: str | None = None,
    ) -> list[DocumentStudioTemplate]:
        await self.ensure_default_templates(organization_id=organization_id)
        stmt = (
            select(DocumentStudioTemplate)
            .options(selectinload(DocumentStudioTemplate.versions))
            .where(
                DocumentStudioTemplate.organization_id == organization_id,
                DocumentStudioTemplate.is_active.is_(True),
            )
        )
        if module:
            stmt = stmt.where(DocumentStudioTemplate.module == module)
        if document_type:
            stmt = stmt.where(DocumentStudioTemplate.document_type == document_type)
        result = await self.db.execute(
            stmt.order_by(
                DocumentStudioTemplate.module,
                DocumentStudioTemplate.document_type,
                DocumentStudioTemplate.priority,
            )
        )
        return list(result.scalars().unique().all())

    async def get_template(
        self,
        *,
        organization_id: UUID,
        template_id: UUID,
    ) -> DocumentStudioTemplate:
        template = (
            await self.db.execute(
                select(DocumentStudioTemplate)
                .options(selectinload(DocumentStudioTemplate.versions))
                .where(
                    DocumentStudioTemplate.id == template_id,
                    DocumentStudioTemplate.organization_id == organization_id,
                    DocumentStudioTemplate.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        if not template:
            raise NotFoundException(
                "Document template not found",
                "DOCUMENT_TEMPLATE_NOT_FOUND",
            )
        return template

    async def ensure_default_templates(
        self,
        *,
        organization_id: UUID,
        created_by: UUID | None = None,
    ) -> None:
        for template_data in DEFAULT_DOCUMENT_TEMPLATES:
            existing = (
                await self.db.execute(
                    select(DocumentStudioTemplate).where(
                        DocumentStudioTemplate.organization_id == organization_id,
                        DocumentStudioTemplate.code == template_data["code"],
                    )
                )
            ).scalar_one_or_none()
            if existing:
                continue

            template = DocumentStudioTemplate(
                organization_id=organization_id,
                module=template_data["module"],
                document_type=template_data["document_type"],
                code=template_data["code"],
                name=template_data["name"],
                entity_type=template_data["entity_type"],
                locale="en",
                channel="PDF",
                priority=1000,
                selection_rules={},
                is_system=True,
                created_by=created_by,
            )
            self.db.add(template)
            await self.db.flush()
            self.db.add(
                DocumentStudioTemplateVersion(
                    organization_id=organization_id,
                    template_id=template.id,
                    version_number=1,
                    status=DocumentTemplateStatus.PUBLISHED,
                    format="HTML",
                    header="<b>{{ organization.name }}</b>",
                    body=template_data["body"],
                    footer="Authorised Signatory",
                    style_config={},
                    variable_schema={},
                    required_variables=template_data["required_variables"],
                    locked_blocks=[],
                    published_at=datetime.now(UTC),
                    created_by=created_by,
                )
            )
        await self.db.flush()

    async def create_template(
        self,
        *,
        organization_id: UUID,
        data: dict[str, Any],
        created_by: UUID | None,
    ) -> DocumentStudioTemplate:
        row = DocumentStudioTemplate(
            organization_id=organization_id,
            module=data["module"],
            document_type=data["document_type"],
            code=data["code"],
            name=data["name"],
            description=data.get("description"),
            product_code=data.get("product_code"),
            entity_type=data.get("entity_type"),
            locale=data.get("locale") or "en",
            channel=data.get("channel") or "PDF",
            priority=data.get("priority", 100),
            selection_rules=data.get("selection_rules") or {},
            created_by=created_by,
        )
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def create_version(
        self,
        *,
        organization_id: UUID,
        template_id: UUID,
        data: dict[str, Any],
        created_by: UUID | None,
    ) -> DocumentStudioTemplateVersion:
        await self.get_template(organization_id=organization_id, template_id=template_id)
        existing_count = (
            await self.db.execute(
                select(func.count(DocumentStudioTemplateVersion.id)).where(
                    DocumentStudioTemplateVersion.template_id == template_id
                )
            )
        ).scalar_one()
        row = DocumentStudioTemplateVersion(
            organization_id=organization_id,
            template_id=template_id,
            version_number=int(existing_count) + 1,
            status=DocumentTemplateStatus.DRAFT,
            format=data.get("format") or "HTML",
            body=data["body"],
            header=data.get("header"),
            footer=data.get("footer"),
            style_config=data.get("style_config") or {},
            variable_schema=data.get("variable_schema") or {},
            required_variables=data.get("required_variables") or [],
            locked_blocks=data.get("locked_blocks") or [],
            source_document_id=data.get("source_document_id"),
            change_notes=data.get("change_notes"),
            created_by=created_by,
        )
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def transition_version(
        self,
        *,
        organization_id: UUID,
        version_id: UUID,
        action: str,
        user_id: UUID | None,
    ) -> DocumentStudioTemplateVersion:
        version = await self.db.get(DocumentStudioTemplateVersion, version_id)
        if version is None or version.organization_id != organization_id:
            raise NotFoundException(
                "Document template version not found",
                "DOCUMENT_TEMPLATE_VERSION_NOT_FOUND",
            )
        now = datetime.now(UTC)
        if action == "submit-review":
            if version.status != DocumentTemplateStatus.DRAFT:
                raise BadRequestException(
                    "Only draft versions can be submitted",
                    "DOCUMENT_TEMPLATE_INVALID_STATUS",
                )
            version.status = DocumentTemplateStatus.IN_REVIEW
        elif action == "approve":
            if version.status not in {
                DocumentTemplateStatus.IN_REVIEW,
                DocumentTemplateStatus.DRAFT,
            }:
                raise BadRequestException(
                    "Only draft or review versions can be approved",
                    "DOCUMENT_TEMPLATE_INVALID_STATUS",
                )
            version.status = DocumentTemplateStatus.APPROVED
            version.approved_by_id = user_id
            version.approved_at = now
        elif action == "publish":
            if version.status != DocumentTemplateStatus.APPROVED:
                raise BadRequestException(
                    "Only approved versions can be published",
                    "DOCUMENT_TEMPLATE_INVALID_STATUS",
                )
            await self._retire_published_versions(version)
            version.status = DocumentTemplateStatus.PUBLISHED
            version.published_at = now
        else:
            raise BadRequestException(
                "Unsupported document template action",
                "DOCUMENT_TEMPLATE_UNSUPPORTED_ACTION",
            )
        version.updated_by = user_id
        await self.db.flush()
        await self.db.refresh(version)
        return version

    async def _retire_published_versions(self, version: DocumentStudioTemplateVersion) -> None:
        rows = list(
            (
                await self.db.execute(
                    select(DocumentStudioTemplateVersion).where(
                        DocumentStudioTemplateVersion.template_id == version.template_id,
                        DocumentStudioTemplateVersion.id != version.id,
                        DocumentStudioTemplateVersion.status == DocumentTemplateStatus.PUBLISHED,
                    )
                )
            )
            .scalars()
            .all()
        )
        now = datetime.now(UTC)
        for row in rows:
            row.status = DocumentTemplateStatus.RETIRED
            row.retired_at = now

    async def variables(
        self,
        *,
        module: DocumentModule,
        document_type: str | None,
    ) -> list[dict[str, Any]]:
        values = [*COMMON_VARIABLES["ORGANIZATION"]]
        if module in {DocumentModule.LENDING, DocumentModule.BORROWER_PORTAL}:
            values.extend(COMMON_VARIABLES["ENTITY"])
            values.extend(COMMON_VARIABLES["LENDING"])
            if document_type == "IIF_CLAIM_CERTIFICATE":
                values.extend(COMMON_VARIABLES["IIF_CLAIM"])
        values.extend(COMMON_VARIABLES.get(module.value, []))
        if document_type == "SANCTION_LETTER":
            values.append(
                {
                    "key": "sanction.validityDate",
                    "label": "Sanction Validity Date",
                    "description": "Last date for sanction acceptance",
                    "formatter": "date",
                }
            )
        return values

    async def preview(
        self,
        *,
        organization_id: UUID,
        template_version_id: UUID | None,
        body: str | None,
        header: str | None,
        footer: str | None,
        context: dict[str, Any],
    ) -> tuple[str, list[str]]:
        if template_version_id:
            version = await self.db.get(DocumentStudioTemplateVersion, template_version_id)
            if version is None or version.organization_id != organization_id:
                raise NotFoundException(
                    "Document template version not found",
                    "DOCUMENT_TEMPLATE_VERSION_NOT_FOUND",
                )
            body = version.body
            header = version.header
            footer = version.footer
        rendered_header, missing_header = render_template_text(header or "", context)
        rendered_body, missing_body = render_template_text(body or "", context)
        rendered_footer, missing_footer = render_template_text(footer or "", context)
        rendered_html = "\n".join(
            part for part in [rendered_header, rendered_body, rendered_footer] if part
        )
        return rendered_html, sorted(set(missing_header + missing_body + missing_footer))

    async def generate(
        self,
        *,
        organization_id: UUID,
        data: dict[str, Any],
        user_id: UUID | None,
    ) -> GeneratedDocument:
        await self.ensure_default_templates(
            organization_id=organization_id,
            created_by=user_id,
        )
        template, version = await self._resolve_generation_template(
            organization_id=organization_id,
            template_id=data.get("template_id"),
            template_version_id=data.get("template_version_id"),
            module=data["module"],
            document_type=data["document_type"],
        )
        rendered_html, missing = await self.preview(
            organization_id=organization_id,
            template_version_id=version.id,
            body=None,
            header=None,
            footer=None,
            context=data.get("context") or {},
        )
        required_missing = sorted(set(version.required_variables or []) & set(missing))
        if required_missing:
            raise BadRequestException(
                detail=f"Missing required document variables: {', '.join(required_missing)}",
                error_code="DOCUMENT_REQUIRED_VARIABLES_MISSING",
            )
        pdf = _html_to_pdf_bytes(title=template.name, rendered_html=rendered_html)
        checksum = hashlib.sha256(pdf).hexdigest()
        file_name = data.get("file_name") or f"{template.code}_v{version.version_number}.pdf"
        dms_doc, folder, filing_rule = await self.filing.file_bytes(
            organization_id=organization_id,
            content=pdf,
            file_name=file_name,
            mime_type="application/pdf",
            module=template.module.value,
            document_type=data["document_type"],
            document_subtype=data.get("document_subtype"),
            entity_type=data["entity_type"],
            entity_id=data["entity_id"],
            context=data.get("context") or {},
            name=f"{template.name} v{version.version_number}",
            description=f"Generated from {template.code} v{version.version_number}",
            created_by=user_id,
        )
        generated = GeneratedDocument(
            organization_id=organization_id,
            module=template.module,
            document_type=data["document_type"],
            document_subtype=data.get("document_subtype"),
            template_id=template.id,
            template_version_id=version.id,
            template_code=template.code,
            template_version=version.version_number,
            dms_document_id=dms_doc.id,
            folder_id=folder.id,
            entity_type=data["entity_type"],
            entity_id=data["entity_id"],
            generated_from=data.get("generated_from"),
            business_number=data.get("business_number"),
            render_snapshot={
                "context": jsonable_encoder(data.get("context") or {}),
                "renderedHtml": rendered_html,
                "missingVariables": missing,
                "fileName": file_name,
            },
            checksum=checksum,
            portal_visible=(
                bool(data["portal_visible"])
                if data.get("portal_visible") is not None
                else bool(filing_rule.portal_visible if filing_rule else False)
            ),
            finalized_at=datetime.now(UTC),
            finalized_by_id=user_id,
            created_by=user_id,
        )
        self.db.add(generated)
        await self.db.flush()
        dms_doc.extracted_metadata = {
            **(dms_doc.extracted_metadata or {}),
            "templateCode": template.code,
            "templateVersion": version.version_number,
            "generatedDocumentId": str(generated.id),
            "businessNumber": data.get("business_number"),
            "portalVisible": generated.portal_visible,
        }
        await self.db.flush()
        await self.db.refresh(generated)
        return generated

    async def _resolve_generation_template(
        self,
        *,
        organization_id: UUID,
        template_id: UUID | None,
        template_version_id: UUID | None,
        module: DocumentModule,
        document_type: str,
    ) -> tuple[DocumentStudioTemplate, DocumentStudioTemplateVersion]:
        if template_version_id:
            version = await self.db.get(DocumentStudioTemplateVersion, template_version_id)
            if version is None or version.organization_id != organization_id:
                raise NotFoundException(
                    "Document template version not found",
                    "DOCUMENT_TEMPLATE_VERSION_NOT_FOUND",
                )
            template = await self.get_template(
                organization_id=organization_id,
                template_id=version.template_id,
            )
        else:
            stmt = (
                select(DocumentStudioTemplate)
                .where(
                    DocumentStudioTemplate.organization_id == organization_id,
                    DocumentStudioTemplate.module == module,
                    DocumentStudioTemplate.document_type == document_type,
                    DocumentStudioTemplate.is_active.is_(True),
                )
                .order_by(DocumentStudioTemplate.priority)
                .limit(1)
            )
            if template_id:
                stmt = stmt.where(DocumentStudioTemplate.id == template_id)
            template = (await self.db.execute(stmt)).scalar_one_or_none()
            if not template:
                raise NotFoundException(
                    "Published document template not found",
                    "DOCUMENT_TEMPLATE_NOT_FOUND",
                )
            version = (
                await self.db.execute(
                    select(DocumentStudioTemplateVersion)
                    .where(
                        DocumentStudioTemplateVersion.template_id == template.id,
                        DocumentStudioTemplateVersion.status == DocumentTemplateStatus.PUBLISHED,
                    )
                    .order_by(DocumentStudioTemplateVersion.version_number.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
        if version.status != DocumentTemplateStatus.PUBLISHED:
            raise BadRequestException(
                detail="Only published document templates can generate finalized documents",
                error_code="DOCUMENT_TEMPLATE_NOT_PUBLISHED",
            )
        return template, version

    async def get_package(
        self,
        *,
        organization_id: UUID,
        package_id: UUID,
    ) -> tuple[DocumentPackage, list[DocumentPackageItem]]:
        row = await self.db.get(DocumentPackage, package_id)
        if row is None or row.organization_id != organization_id:
            raise NotFoundException(
                "Document package not found",
                "DOCUMENT_PACKAGE_NOT_FOUND",
            )
        items = await self.list_package_items(
            organization_id=organization_id,
            package_id=package_id,
        )
        return row, items

    async def list_packages(
        self,
        *,
        organization_id: UUID,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
    ) -> list[DocumentPackage]:
        stmt = select(DocumentPackage).where(
            DocumentPackage.organization_id == organization_id,
            DocumentPackage.is_active.is_(True),
        )
        if entity_type:
            stmt = stmt.where(DocumentPackage.entity_type == entity_type)
        if entity_id:
            stmt = stmt.where(DocumentPackage.entity_id == entity_id)
        result = await self.db.execute(stmt.order_by(DocumentPackage.created_at.desc()))
        return list(result.scalars().all())

    async def create_package(
        self,
        *,
        organization_id: UUID,
        data: dict[str, Any],
        created_by: UUID | None,
    ) -> DocumentPackage:
        package_number = await self._next_package_number(
            organization_id=organization_id,
            package_type=data["package_type"],
        )
        row = DocumentPackage(
            organization_id=organization_id,
            package_number=package_number,
            package_type=data["package_type"],
            name=data["name"],
            entity_type=data["entity_type"],
            entity_id=data["entity_id"],
            manifest=data.get("manifest") or {},
            status=DocumentPackageStatus.DRAFT,
            created_by=created_by,
        )
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def add_package_item(
        self,
        *,
        organization_id: UUID,
        package_id: UUID,
        data: dict[str, Any],
        created_by: UUID | None,
    ) -> DocumentPackageItem:
        from app.models.dms import DMSDocument

        package = await self.db.get(DocumentPackage, package_id)
        if package is None or package.organization_id != organization_id:
            raise NotFoundException(
                "Document package not found",
                "DOCUMENT_PACKAGE_NOT_FOUND",
            )
        if package.status != DocumentPackageStatus.DRAFT:
            raise BadRequestException(
                "Only draft document packages can be changed",
                "DOCUMENT_PACKAGE_LOCKED",
            )

        dms_document = await self.db.get(DMSDocument, data["dms_document_id"])
        if dms_document is None or dms_document.organization_id != organization_id:
            raise NotFoundException(
                "DMS document not found",
                "DMS_DOCUMENT_NOT_FOUND",
            )

        generated_document_id = data.get("generated_document_id")
        if generated_document_id:
            generated = await self.db.get(GeneratedDocument, generated_document_id)
            if generated is None or generated.organization_id != organization_id:
                raise NotFoundException(
                    "Generated document not found",
                    "GENERATED_DOCUMENT_NOT_FOUND",
                )

        row = DocumentPackageItem(
            organization_id=organization_id,
            package_id=package_id,
            dms_document_id=data["dms_document_id"],
            generated_document_id=generated_document_id,
            role=data.get("role") or "SUPPORTING",
            sort_order=data.get("sort_order", 0),
            created_by=created_by,
        )
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def list_package_items(
        self,
        *,
        organization_id: UUID,
        package_id: UUID,
    ) -> list[DocumentPackageItem]:
        result = await self.db.execute(
            select(DocumentPackageItem)
            .where(
                DocumentPackageItem.organization_id == organization_id,
                DocumentPackageItem.package_id == package_id,
                DocumentPackageItem.is_active.is_(True),
            )
            .order_by(DocumentPackageItem.sort_order, DocumentPackageItem.created_at)
        )
        return list(result.scalars().all())

    async def finalize_package(
        self,
        *,
        organization_id: UUID,
        package_id: UUID,
        manifest: dict[str, Any] | None,
        user_id: UUID | None,
    ) -> tuple[DocumentPackage, list[DocumentPackageItem]]:
        row = await self.db.get(DocumentPackage, package_id)
        if row is None or row.organization_id != organization_id:
            raise NotFoundException(
                "Document package not found",
                "DOCUMENT_PACKAGE_NOT_FOUND",
            )
        if row.status != DocumentPackageStatus.DRAFT:
            raise BadRequestException(
                "Only draft document packages can be finalized",
                "DOCUMENT_PACKAGE_INVALID_STATUS",
            )

        items = await self.list_package_items(
            organization_id=organization_id,
            package_id=package_id,
        )
        if not items:
            raise BadRequestException(
                "Document package must contain at least one document",
                "DOCUMENT_PACKAGE_EMPTY",
            )

        row.status = DocumentPackageStatus.FINALIZED
        row.manifest = {
            **(row.manifest or {}),
            **(manifest or {}),
            "documentCount": len(items),
            "dmsDocumentIds": [str(item.dms_document_id) for item in items],
        }
        row.finalized_at = datetime.now(UTC)
        row.finalized_by_id = user_id
        row.updated_by = user_id
        await self.db.flush()
        await self.db.refresh(row)
        return row, items

    async def _next_package_number(self, *, organization_id: UUID, package_type: str) -> str:
        today = datetime.now(UTC).strftime("%Y%m%d")
        prefix = re.sub(r"[^A-Z0-9]+", "-", package_type.upper()).strip("-") or "PACKAGE"
        count = (
            await self.db.execute(
                select(func.count(DocumentPackage.id)).where(
                    DocumentPackage.organization_id == organization_id,
                    DocumentPackage.package_type == package_type,
                )
            )
        ).scalar_one()
        return f"PKG/{prefix}/{today}/{int(count) + 1:04d}"
