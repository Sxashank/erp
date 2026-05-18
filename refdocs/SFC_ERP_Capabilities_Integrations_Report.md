# SFC ERP Capabilities, Manual Operations, and Analytics Overview

Prepared for SFC (NBFC)

Companion detailed review: `refdocs/SFC_NBFC_Corporate_Loan_Lifecycle_Gap_Report.md`

Implementation roadmap: `refdocs/SFC_ERP_Implementation_Roadmap.md`

## Executive Summary
SFC ERP is an end-to-end operational platform that covers the full NBFC operating cycle: borrower onboarding and loan origination, loan servicing and collections, treasury and risk, finance and compliance, HR and payroll, and reporting. The current implementation should be positioned as a manual-first ERP: users record transactions, receipts, instalments, lender payments, approvals, and accounting events manually, while the system provides workflow control, auditability, dashboards, and reports.

For Sagarmala Finance Corporation, the lending lifecycle should be positioned as corporate/project finance rather than individual loan disbursement. The ERP should therefore track both sides of the NBFC business model: funds raised from banks/FIs/bonds at a cost of funds, and loans deployed to organisations/projects at a lending yield. Management should be able to monitor sanctioned pipeline, tranche disbursements, borrower instalments, borrowing repayments, spread, liquidity gaps, overdue/NPA, and regulatory status in one system.

## How This Improves Productivity
- Streamlines the lending lifecycle from onboarding to closure, reducing manual handoffs.
- Tracks compliance tasks, reminders, and escalations to reduce regulatory risk.
- Centralizes documents, approvals, and audit logs for faster reviews and fewer data gaps.
- Delivers real-time dashboards and scheduled MIS reports for faster management action.
- Reduces spreadsheet dependency by giving teams structured manual entry, maker-checker, and audit trail.
- Gives treasury, lending, finance, and management a common view of expected borrower inflows vs borrowing outflows.

## Current Scope vs Future Automation

### Current Manual Scope
- Borrower onboarding, application, appraisal, sanction, disbursement, receipt, and lender-payment records are entered by users.
- EMI/instalment receipts from borrowers are recorded manually against loan accounts and allocated to due components.
- Borrowing interest and principal payments to source lenders are recorded manually by treasury/finance users.
- GST, TDS, e-way bill references, vouchers, BRS observations, and statutory filing status are maintained manually.
- Dashboards and MIS are generated from recorded ERP data, not from live bank or portal integrations.

### Future Automation Only
- Bank statement import, UTR-based repayment matching, auto-created receipts, NACH/payment gateway flows, live GSTN/MCA/CKYC/CERSAI integrations, and borrower/vendor/employee portals should be presented as optional future roadmap items, not current capabilities.

## Module-by-Module Capabilities

### Enterprise Masters and General Ledger
- Feature: Organization, unit, department, user, role, financial year, currency, and bank masters.
- Feature: Chart of accounts, cost centers, voucher types, and approval matrix configuration.
- Feature: Voucher entry with maker-checker workflow, attachments, reversals, and posting status.
- Feature: Period management controls and audit-ready GL postings.
- Feature: Accounting flows for borrowing drawdown, loan disbursement, interest income accrual, interest expense accrual, borrower receipts, borrowing repayments, and NPA income controls.
- Output: Source module references for postings from lending, treasury, HR, and other modules.

### Lending Masters, KYC, and Credit Rating
- Feature: Borrower/entity master with contacts, addresses, bank accounts, and related parties.
- Feature: KYC document types, collection, verification, and CKYC support.
- Feature: Risk categories, parameters, rating matrix, and rating workflow history.
- Feature: Loan product masters, interest rates, fees, document checklists, and collateral masters.
- Current Output: Manual KYC/credit document tracking and internal verification status.
- Future Automation: Credit bureau, CKYC, MCA, GSTIN, and external verification integrations if approved later.

### Loan Origination System (LOS)
- Feature: Loan application capture with documents, fees, and application workflow.
- Feature: Technical appraisal, project details, and appraisal checklist tracking.
- Feature: Financial appraisal with CMA structures and ratio analysis.
- Feature: Sanction records with terms, conditions, and security details.
- Feature: Corporate/project finance controls such as DSCR, escrow/source-of-repayment, security cover, promoter contribution, milestone checks, and conditions precedent/subsequent.
- Output: Feeds sanctioned data to loan accounting and document management.

### Loan Accounting and Servicing (LAMS)
- Feature: Loan account creation, tranche management, and disbursement processing.
- Feature: Principal and interest schedule generation with rate reset handling.
- Feature: Interest accruals, demand generation, and penal interest tracking.
- Feature: Daily/periodic balances and repayment performance tracking.
- Feature: Enterprise repayment structures including structured repayment, bullet, balloon, moratorium-based instalments, quarterly interest servicing, and tranche-wise schedules.
- Output: Manual loan schedules, statements, dues, and servicing records for internal teams.

### Receipts, Collections, NPA, and Legal
- Feature: Receipt capture with payment modes, TDS handling, and bounce tracking.
- Feature: Receipt allocation with configurable priority across principal, interest, penal, and charges.
- Feature: NPA classification rules, history, provisioning, upgrades, and write-offs.
- Feature: OTS tracking with approval thresholds and settlement completion.
- Feature: Legal case management for SARFAESI, DRT, NCLT, arbitration, and civil routes.
- Feature: Manual instalment/EPI/interest receipt posting against borrower loan accounts.
- Feature: Manual recording of payment mode, UTR/reference, value date, TDS deduction, bounce/reversal, and allocation remarks.
- Output: Overdue, SMA, NPA, provisioning, OTS, and legal dashboards for internal teams.

### Treasury, ALM, and Risk
- Feature: Borrowing master and borrowing accounts with rate resets and repayment schedules.
- Feature: ALM position generation, asset/liability mapping, RBI maturity buckets, and gap analysis.
- Feature: Exposure limits, concentration monitoring, and portfolio risk summaries including ECL.
- Feature: Risk dashboard metrics such as CRAR and rating migration monitoring.
- Feature: Source-of-funds and borrowing utilisation view to compare cost of funds, lending yield, spread, NII, and NIM.
- Output: ALM and risk MIS statements for governance and committees.

### Finance Ancillary Modules
- Feature: Fixed asset register with categories, depreciation methods, transfers, and disposals.
- Feature: TDS sections, transactions, challans, return tracking, and due-date alerts.
- Feature: GST registrations, transaction register with HSN/SAC, ITC eligibility, RCM handling, and returns.
- Feature: Manual GST transaction register with HSN/SAC, ITC eligibility, RCM handling, return status, and e-way bill reference tracking where applicable.
- Feature: Manual BRS observations and reconciliation status tracking based on user-entered/uploaded data when adopted.
- Future Automation: Bank statement import, GST portal filing integration, e-invoice/e-way bill API, and loan-level receipt matching from imported bank credits.
- Feature: Fixed deposit tracking with maturity and interest monitoring.
- Output: Statutory filing readiness reports and manual GST/TDS tracking.

### HRIS and Payroll
- Feature: Employee master with organizational structure, documents, and bank details.
- Feature: Attendance, shift management, and regularization through manual records.
- Feature: Leave management with balances, approvals, and policies.
- Feature: Payroll configuration, processing, arrears, and statutory compliance (PF, ESI, PT, TDS, LWF).
- Future Automation: ESS portal for payslips, tax declarations, reimbursements, and helpdesk.

### Compliance and Governance
- Feature: Compliance calendar covering RBI, MCA, GST, IT, and other regulators.
- Feature: Compliance instances with preparation, review, approval, and filing status tracking.
- Feature: Automated reminders, escalation rules, and penalty tracking.
- Output: Compliance tracker MIS and audit-ready documentation.

### Portals and Self-Service
- Future Automation: Borrower portal for loan summaries, schedules, statements, documents, and requests.
- Future Automation: Online payment support through payment gateway, virtual account, or NACH if approved later.
- Future Automation: Vendor portal for PO visibility, invoice submission, payment status, and TDS certificates.
- Future Automation: Employee portal for profile updates, attendance, leave, payroll, and claims.

### Inventory, Notifications, and Document Management
- Feature: Inventory item master with reorder levels and transaction tracking (receipt, issue, transfer).
- Feature: Notification templates and logs for Email, SMS, push, in-app, and WhatsApp channels.
- Feature: Event-driven alerts for disbursements, dues, compliance, approvals, and payroll.
- Feature: Document management with versioning, access controls, expiry tracking, and metadata.
- Output: Document storage, notification logs, and manual communication tracking.

### Audit Trail and Logging
- Feature: Comprehensive audit log with before/after values and user/session context.
- Feature: Retention policies for regulatory, report, and portal activity logs.
- Future Automation: Integration API logs with request/response traceability and retry status when external integrations are enabled.

## Reports and Analytics

### Executive Dashboard KPIs
- Total AUM, Gross NPA percent, Net NPA percent, CRAR.
- Cost of funds, NIM, ROA, ROE.
- Disbursement MTD, Collection efficiency, SMA book.
- Employee productivity (AUM per employee).
- Role-based dashboards (executive, operational, analytical) with drill-down widgets.
- Sanctioned-not-disbursed pipeline, upcoming borrower inflows, upcoming borrowing repayments, spread/NII, and ALM mismatch.

### Standard MIS Reports
- Portfolio position (AUM, disbursements, collections, O/S by product).
- NPA movement (opening, additions, upgrades, write-offs, closing).
- ALM statement and interest rate sensitivity.
- Borrowing position and income statement flash.
- Provisioning report and exposure report.
- Source-of-funds utilisation, net spread, borrower inflow vs lender outflow, and disbursement readiness reports.
- GST returns summary and ITC reconciliation (GSTR-1/3B/9, GSTR-2B matching).
- Rating migration and SMA monitoring.
- Compliance tracker and HR dashboard.

### Report Delivery
- Configurable MIS templates with parameterized queries.
- Scheduled runs with PDF/Excel/CSV outputs.
- Manual export and stakeholder circulation in the current scope.
- Future Automation: Scheduled email distribution if messaging integration is enabled.

## Future Automation Landscape

The following are not part of the current manual operating scope. They should be discussed only as future roadmap options:
- Bank statement feeds/files or APIs for collection account credits, UTR matching, BRS, and loan-level repayment automation.
- Payment gateway, virtual account, or NACH for borrower collections.
- CKYC, CERSAI, credit bureau, MCA, GSTN, e-invoice, and e-way bill API integrations.
- Email/SMS/WhatsApp gateways and biometric attendance systems.
- Borrower, vendor, and employee self-service portals.

## Security and Controls
- Role-based access and maker-checker workflows across modules.
- Future portal access can use MFA and account lockouts if portals are enabled.
- Document access levels and versioning for governance.
- Full audit trail to meet regulatory expectations.

## Next Steps (Optional)
- Confirm branding (SFC vs SMFC) and preferred tone for the client document.
- Validate client-specific manual workflows and report variants.
- Keep integrations explicitly marked as future roadmap items until approved.
- Share any preferred formatting or slide template if a presentation deck is required.
