# SMFC ERP Accounting Full-Sweep Review Report

Prepared for Sagarmala Finance Corporation / SMFCL ERP  
Review date: 2026-05-17  
Basis: Company/NBFC accounting under Indian requirements, manual-first operations, optional future automation

---

## 1. Executive Summary

This review covers the full accounting and finance stack, not only core GL:

- Chart of accounts, account groups, cash/bank/control accounts, cost centers.
- Financial years, periods, period lock/close/reopen, opening balances, year-end close.
- Voucher types, voucher entry, voucher templates, recurring vouchers, approval, posting, reversal/cancellation.
- GL entries, ledgers, trial balance, P&L, balance sheet, cash flow, day book.
- AP/AR, vendors, customers, purchase bills, sales invoices, payments, receipts, advances, allocation, aging.
- Bank reconciliation and manual bank statement workflows.
- GST, TDS/TCS, e-invoice/e-way bill references, filing status, challans, Form 16A.
- Accounting hooks from lending, treasury, fixed assets, fixed deposits, payroll, legal, compliance, and portals.
- ACL, tenant isolation, API contracts, audit trail, and UAT readiness.

The implementation already has a strong foundation: visible frontend screens, backend models, services, repositories, schemas, and tests exist for most accounting areas. However, it is not yet UAT-ready for accounting certification because a few correctness blockers sit in the core posting path, and several manual-first statutory/accounting flows are only partially complete.

The highest-priority issue is the GL posting architecture. `VoucherService.post()` calls `GLPostingService.post_entries()`, but no such method exists in `backend/app/services/finance/gl_posting_service.py`. Separately, `post_from_source()` writes non-voucher source IDs into `txn_gl_entry.voucher_id`, even though `GLEntry.voucher_id` is a required FK to `txn_voucher`. These two issues must be fixed before accounting UAT.

---

## 2. Benchmark Used

The benchmark for this module is Indian company/NBFC accounting, not government fund accounting.

Key reference expectations:

- Companies Act books should support accrual basis and double-entry accounting. See [Companies Act, 2013 - MCA PDF](https://www.mca.gov.in/content/dam/mca/pdf/CompaniesAct2013.pdf).
- Accounting standards should align to current ICAI/MCA framework. See [ICAI Accounting Standards](https://www.icai.org/post/accounting-standards-as).
- Modern Indian accounting products generally provide GST, e-invoicing, e-way bill, banking/reconciliation, multi-user permissions, audit-ready reports, AP/AR, inventory, payroll, and automation. See [Zoho Books India](https://www.zoho.com/in/books/), [TallyPrime release features](https://help.tallysolutions.com/tallyprime-features-release-wise/), and [TallyPrime product page](https://tallysolutions.com/tally-prime/).
- GST operational expectations include GSTR-1 outward supplies, GSTR-3B summary liability/payment, GSTR-2B ITC statement and reconciliation, e-invoice IRN, and e-way bill references. See [GST GSTR-1 guide](https://tutorial.gst.gov.in/userguide/returns/GSTR_1.htm), [GST GSTR-2B guide](https://tutorial.gst.gov.in/userguide/returns/Manual_gstr2b.htm), [GST GSTR-3B guide](https://tutorial.gst.gov.in/userguide/returns/GSTR3B.htm), and [GST e-invoice mandate](https://einvoice6.gst.gov.in/content/einvoice-mandate/).

For this release, all workflows must remain manual-first. Bank feeds, GSTN, IRP, e-way bill, payment gateway, TRACES/NSDL, and other external integrations are future automation only.

---

## 3. Current Capability Inventory

| Area | Current capability observed | Status |
| --- | --- | --- |
| Chart of accounts | Account groups, accounts, account nature, account type, bank/cash/control flags, GSTIN, PAN, TDS applicability, opening/current balances. | Partially present |
| Cost centers | Backend cost-center model/service exists; GL entries support `cost_center_id`; frontend exposure needs verification across reports and vouchers. | Partially present |
| Financial year and periods | Financial year creation, period creation, close, lock, unlock, reopen, GST filing date, year-end close service. | Present but needs hardening |
| Voucher types | Voucher class, prefix, auto-numbering, starting/current number, approval configuration. | Present |
| Voucher entry | Create/update/list/view/submit/approve/post/cancel/delete flows; frontend pages exist. | Present but posting is blocked |
| Voucher templates and recurring vouchers | Frontend pages and backend models/services exist. | Present but needs UAT sweep |
| GL entries | GL entry model supports immutable posting records, party, cost center, source type, source reference, reversal metadata, period, unit, and organization. | Present but source architecture needs fix |
| Manual posting approval | Accounting pages exist for GL posting approval, approval matrix, and pending approvals. | Present but needs end-to-end verification |
| Financial reports | Trial Balance, P&L, Balance Sheet, Cash Flow, Account Ledger, Day Book pages and backend endpoints exist. | Present but needs statutory/report correctness review |
| AP/AR masters | Vendors, customers, payment terms, GSTIN/PAN/TDS fields, bank details, default accounts. | Present |
| Purchase bills | Bill entry, line taxes, TDS, status, payment status, GL hooks. | Partially present |
| Sales invoices | Invoice entry, line taxes, TCS, GST fields, e-invoice/e-way bill references, status, receipt status. | Partially present |
| Payments/receipts | Payment/receipt records, payment modes, bank/cash account references, TDS, allocations, cheque details, statuses. | Partially present |
| Bank reconciliation | Bank statement import/list/reconciliation/report pages; backend matching logic and tests for references, amount/date, stale cheques, unbooked credits/debits. | Present but manual workflow needs UAT |
| GST | GST rates, HSN/SAC, registrations, GSTN-facing pages, GSTR-1/3B, ITC reconciliation, e-invoice/e-way bill services. | Partially present; manual local computation incomplete |
| TDS/TCS | Sections, thresholds, rates, challans, returns, Form 16A, LDC/rate tests, no-PAN rate tests. | Partially present |
| Audit | Common audit logging used in voucher/AP/AR services; AGENTS.md requires non-disableable audit trail. | Partially present |
| ACL | Backend permission checks exist across many endpoints; frontend module access was moved to ACL-based visibility. | Partially present; inconsistent permission patterns remain |

---

## 4. Gap Matrix

### Critical

| Gap | Evidence | Impact | Required action |
| --- | --- | --- | --- |
| Voucher posting calls missing GL method | `VoucherService._create_gl_entries()` calls `self.gl_posting_service.post_entries(...)`; `GLPostingService` has `post_voucher()` and `post_from_source()`, but no `post_entries()`. | Approved vouchers cannot reliably post to ledger; accounting UAT cannot pass. | Replace with a single canonical posting method or add `post_entries()` with tests. Ensure one service owns balance updates. |
| Source-document GL posting has invalid voucher FK design | `GLEntry.voucher_id` is non-null FK to `txn_voucher`; `post_from_source()` sets `voucher_id = source_id` as a pseudo-voucher reference. | AP/AR/lending/payroll/fixed-asset source postings can fail FK constraints or corrupt audit meaning. | Require every source posting to create/link an accounting voucher, or make GL source fields first-class and nullable voucher optional through a migration. Prefer voucher-backed posting for auditability. |
| Double balance-update risk | `VoucherService.post()` manually updates `Account.current_balance`; `GLPostingService` posting methods also update account running balance. | If posting method is fixed naively, balances can double-post. | Centralize account balance updates inside GL posting only, with idempotent posted-state checks. |
| Zero-value GL/source lines are not rejected in service | `backend/tests/finance/test_gl_balance.py` documents that zero debit and zero credit currently proceeds to account lookup. | Meaningless accounting entries can pass validation and pollute reports. | Reject lines where both debit and credit are zero; require at least two non-zero lines and balanced totals. |
| Tenant-safe DB dependency is inconsistent | Many finance/AP/AR/GST/TDS/report endpoints use `get_db` rather than `get_db_with_tenant`. | RLS and tenant isolation can be bypassed or depend on caller-supplied organization IDs. | Migrate accounting/tax/report routes to tenant-safe dependencies and remove trust in request `organization_id` where JWT/RLS should decide. |

### High

| Gap | Evidence | Impact | Required action |
| --- | --- | --- | --- |
| API contracts are legacy snake_case in accounting schemas | Finance/AP/AR/GST/TDS schemas commonly inherit `BaseSchema`; AGENTS.md requires frontend-facing `CamelSchema`. | Frontend mappers/fallbacks reappear; contract inconsistency causes UI defects. | Migrate touched accounting schemas/endpoints to `CamelSchema` and `response_model_by_alias=True`; frontend DTOs must be camelCase only. |
| Permission naming is inconsistent | TDS endpoints use finance permissions like `FIN_VOUCHER_VIEW`; GSTN endpoints use strings such as `gstn.return.read`; constants define `TDS_*` and `GST_*`. | ACL becomes hard to certify; users may see or miss screens incorrectly. | Normalize accounting permission mapping and seed roles for Finance, Tax, AP/AR, Treasury, Auditor, Admin. |
| Voucher numbering lacks concurrency hardening | `VoucherType.get_next_number()` increments model state without visible row lock/sequence service. | Duplicate voucher numbers are possible under concurrent posting/creation. | Add transactional voucher numbering service with row-level lock or DB sequence per org/unit/FY/voucher type. |
| Account deletion/update guards are incomplete | `account_service.py` has TODO to check transactions; voucher type service has TODO to check existing vouchers. | Master records used in books may be altered/deleted incorrectly. | Block delete/incompatible changes once transactions exist; allow only inactive/archive with audit trail. |
| Manual GST computation is incomplete | `gstn_service.py` has TODOs for invoice fetching, GSTR-1/3B calculation, purchase bill query, matched/variance ITC. | GST screens may not reflect real local books; tax UAT will fail even without GSTN integration. | Build manual GST return summaries from local sales invoices, purchase bills, credit/debit notes, and ITC records. |
| AP/AR reversal/cancellation GL hooks incomplete | `payment_service.py` has TODO for reversal GL voucher; purchase/sales services need cancellation/posting verification. | Cancelled payments/bills/invoices can leave balances and ledgers wrong. | Implement voucher-backed reversal entries for AP/AR and verify outstanding balances recalculate. |
| Organization settings for accounting defaults are not complete | AP/AR service has TODO to move default accounts to organization settings. | Hardcoded/default account assumptions break tenant-specific accounting. | Add tenant-scoped accounting configuration for default sales, purchase, tax, TDS/TCS, bank charge, round-off, discount, write-off, and suspense accounts. |

### Medium

| Gap | Evidence | Impact | Required action |
| --- | --- | --- | --- |
| Schedule III / NBFC financial statement formats are not explicit | Reports exist but are generic Trial Balance/P&L/Balance Sheet/Cash Flow. | Client/auditor may need statutory format and NBFC schedules. | Add statutory presentation views and export formats mapped from account groups. |
| MCA audit trail certification not explicit | Audit service exists, but accounting software edit-log requirements need a dedicated evidence report. | Auditor may not certify if edit trail, retention, and tamper resistance are unclear. | Add audit-trail report for create/update/delete/post/reverse/master changes with before/after, user, timestamp, reason, IP/correlation ID. |
| Cost center/reporting dimensions need end-to-end validation | GL supports cost center but reports/UI may not fully expose it. | Department/project/unit profitability may be incomplete. | Add cost-center ledgers, filters, allocation report, and validations. |
| Multi-currency exists in GL fields but is not productized | GL entry has currency/exchange rate fields; reports mostly assume INR. | Foreign currency transactions can be misleading. | Either hide multi-currency or complete exchange-rate posting, realized/unrealized gain/loss, and reports. |
| Report scheduler/history likely needs hardening | Pages exist for scheduler/history; workflow and export persistence need UAT. | Scheduled statutory/MIS report workflows may be unreliable. | Verify report generation storage, permissions, email/manual download, and audit trail. |
| MIS service uses sample data | `mis_report_service.py` contains sample-data comments. | Management reports may show non-booked values. | Replace with book/sub-ledger-derived data or mark as demo-only and hide from production. |

### Low

| Gap | Evidence | Impact | Required action |
| --- | --- | --- | --- |
| Some UI forms still use page-local form patterns | Several finance/AP/AR forms should be checked against AGENTS.md component/RHF/zod rules. | Design consistency and validation quality vary. | Refactor opportunistically while touching pages. |
| Placeholder/integration wording can confuse users | GSTN/e-invoice/e-way bill pages exist while integrations are future-state. | Users may assume live integrations are available. | Label these as manual/future automation unless feature flag enables live integration. |
| Report export consistency needs review | Reports exist; export component usage may be inconsistent. | Client UAT may flag missing Excel/PDF/CSV. | Standardize all accounting reports through `ExportMenu`. |

---

## 5. Recommended Roadmap

### Sprint A: Core Correctness Blockers

Goal: make accounting postings safe enough for UAT.

- Replace the current voucher/source posting split with one canonical GL posting architecture.
- Ensure every AP/AR/lending/payroll/fixed-asset/FD accounting event produces a voucher-backed audit trail or a correctly modeled source-backed GL entry.
- Remove double account-balance updates; only the canonical posting service updates balances.
- Reject zero-value lines, unbalanced postings, non-leaf posting accounts, closed/locked periods, and deleted/inactive accounts.
- Add idempotency and posted-state guards for all financial mutations.
- Migrate accounting/tax/report routes to tenant-safe dependencies.
- Normalize frontend-facing accounting schemas to camelCase.

Acceptance for Sprint A:

- Draft voucher -> submit -> approve -> post creates exactly one balanced set of GL entries.
- Posted voucher cannot be reposted.
- Reversal creates contra entries, not edits.
- Source document posting creates valid accounting records and passes FK constraints.
- Account balances match GL entries after posting and reversal.
- Unauthorized user cannot view/post/approve/reverse.

### Sprint B: Manual-First GST, TDS, AP/AR, BRS Completion

Goal: make Indian finance operations complete without external integrations.

- Build GST manual summaries from local books:
  - GSTR-1 outward supply summary.
  - GSTR-3B liability and ITC summary.
  - GSTR-2B/manual ITC reconciliation workbench.
  - HSN/SAC summary, RCM, advances, credit/debit notes, nil/exempt/non-GST.
  - Manual status fields for prepared/submitted/filed/ARN.
- Complete TDS/TCS:
  - Section/rate/threshold application from tables.
  - PAN/no-PAN and LDC logic.
  - TDS entry creation from AP payments and vendor bills.
  - Challan generation/verification status and Form 16A status.
  - Return summary by quarter/form.
- Complete AP/AR:
  - Bill/invoice approval and posting.
  - Payments/receipts with allocations, advances, refunds, discounts, write-offs, TDS/TCS, round-off.
  - Cancellation/reversal vouchers.
  - Vendor/customer ledgers and aging.
- Complete manual BRS:
  - Statement import/user entry.
  - UTR/reference/amount/date matching.
  - Stale cheques, unbooked credits/debits, bank charges, suspense, manual match/unmatch.

Acceptance for Sprint B:

- Vendor bill with GST + TDS posts to AP, tax, TDS payable, and expense accounts.
- Vendor payment allocates to bill, creates payment voucher, and updates TDS/challan status.
- Customer invoice with GST posts to AR, revenue, and GST output accounts.
- Customer receipt allocates to invoice and updates AR aging.
- Bank statement item can be manually matched or marked as unbooked with follow-up action.

### Sprint C: Statutory, Audit, and Management Reporting

Goal: make the module client/auditor-friendly.

- Add statutory-style accounting packs:
  - Trial Balance.
  - Ledger.
  - Day Book.
  - Cash/Bank Book.
  - P&L.
  - Balance Sheet.
  - Cash Flow.
  - AP/AR aging.
  - GST/TDS registers.
  - Audit trail/export pack.
- Add NBFC-oriented schedules:
  - Interest income accrual.
  - Borrowing interest expense.
  - NPA income reversal.
  - Provisioning movement.
  - Loan disbursement/receipt voucher trace.
  - Treasury borrowing repayment voucher trace.
- Add report export consistency: Excel, PDF, CSV, filters, generated-by, generated-at, org, FY, period, and audit trail.

Acceptance for Sprint C:

- Trial balance balances after all golden scenarios.
- Balance sheet balances.
- P&L agrees with GL income/expense accounts.
- GST/TDS registers tie back to source documents and vouchers.
- Auditor can trace any report value to voucher and source document.

### Sprint D: Optional Future Automation

Goal: add automation later without breaking manual operations.

- Bank feeds and automated BRS matching.
- GSTN return upload/download, GSTR-2B fetch, filing status sync.
- IRP e-invoice and e-way bill API integration.
- Payment gateway, NEFT/RTGS/NACH file generation/status sync.
- TRACES/NSDL integration for TDS returns/certificates.

Release rule:

- Every automated flow must be feature-flagged per tenant, auditable, and fallback-safe.
- Manual entry/import must remain available even after automation is released.

---

## 6. UAT Acceptance Checklist

### Core GL

- Create account group and account.
- Set opening balances.
- Create financial year and monthly periods.
- Lock period and confirm posting is blocked.
- Reopen period with reason and audit entry.
- Create voucher type with numbering.
- Create balanced draft voucher.
- Confirm unbalanced and zero-value voucher lines are rejected.
- Submit voucher for approval.
- Approve voucher with maker-checker separation.
- Post voucher.
- View GL entries, ledger, day book, and trial balance.
- Reverse/cancel posted voucher through contra entries only.
- Confirm audit trail shows create/update/submit/approve/post/reverse.

### AP/AR

- Create vendor with PAN, GSTIN, TDS section, bank details.
- Create purchase bill with GST, TDS, due date, cost center.
- Approve and post purchase bill.
- Create vendor payment with UTR/cheque/reference.
- Allocate payment to bill and verify outstanding/aging.
- Cancel/reverse payment and verify GL/outstanding.
- Create customer with GSTIN and receivable account.
- Create sales invoice with CGST/SGST or IGST.
- Record customer receipt and allocate.
- Verify AR aging and customer ledger.

### GST

- Maintain GST rates and HSN/SAC.
- Generate manual GSTR-1 summary from invoices.
- Generate manual GSTR-3B summary from output tax, ITC, RCM, and payments.
- Import/enter GSTR-2B data and reconcile with purchase bills.
- Track ITC matched, mismatched, ineligible, deferred, reversed.
- Record manual filed status, ARN, filing date, and notes.
- Track e-invoice IRN/e-way bill number manually without live integration.

### TDS/TCS

- Maintain TDS sections with effective-date rates and thresholds.
- Validate threshold crossing and no-PAN 20% handling.
- Apply LDC where available.
- Deduct TDS on eligible bill/payment.
- Generate challan record.
- Mark challan paid/verified manually.
- Generate quarterly return summary and Form 16A status.

### BRS

- Enter/import bank statement.
- Match by UTR/reference.
- Match by amount/date fallback.
- Mark bank charges, stale cheques, unbooked credits, unbooked debits.
- Generate BRS report with unmatched aging.
- Confirm bank book and statement reconciliation tie out.

### ACL and Audit

- Finance maker can create but not approve own voucher.
- Finance checker can approve but not create under restricted role.
- Tax user can access GST/TDS but not payroll or lending.
- Auditor can view reports/audit logs but cannot mutate transactions.
- Unit/branch user sees only permitted organization/unit data.
- All financial mutations produce audit rows with user, timestamp, action, old/new state, reason, and source reference.

---

## 7. Test Plan

### Backend Unit/Integration Tests

- Balanced voucher posts successfully.
- Unbalanced voucher is rejected.
- Zero-value line is rejected.
- Closed period and locked period reject posting.
- Posting to non-leaf/control account is rejected unless explicitly allowed.
- Source document posting creates valid voucher/GL entries.
- Voucher reversal creates opposite entries and marks original as reversed.
- Account current balance equals sum of non-reversed GL entries.
- Voucher number uniqueness under concurrent creation.
- Purchase bill GST/TDS calculation and GL posting.
- Sales invoice GST/TCS calculation and GL posting.
- Payment allocation, partial payment, write-off, discount, TDS.
- Payment cancellation/reversal.
- GST GSTR-1/GSTR-3B summaries from local invoices/bills.
- GSTR-2B reconciliation statuses.
- TDS threshold/rate/no-PAN/LDC/challan/return/Form 16A.
- BRS matching and manual exceptions.
- Report totals for trial balance, P&L, balance sheet, cash flow, ledgers.
- Permission-denied tests for create/approve/post/reverse/report export.
- Tenant isolation tests using RLS dependency.

### Frontend / Playwright UAT

- Navigate every accounting route.
- Verify no 404, API failure, console error, or broken tab.
- Create/edit/view flows for finance, AP/AR, GST, TDS, BRS, reports.
- Verify all action buttons enable/disable based on record state and ACL.
- Verify exports for reports and registers.
- Verify large INR values use shared amount display.
- Verify empty, loading, and error states.
- Verify audit/report drilldowns.

---

## 8. Final Readiness Position

The accounting module is architecturally broad and close enough to justify a full hardening sprint, but it should not be certified as UAT-ready until Sprint A is complete. The posting architecture must be fixed first because all downstream accounting reports, GST/TDS registers, AP/AR aging, BRS, and NBFC accounting hooks depend on reliable GL entries and account balances.

Recommended sequence:

1. Fix GL posting correctness and tenant/API contracts.
2. Complete manual GST/TDS/AP/AR/BRS flows.
3. Certify financial/statutory reports.
4. Run accounting UAT with seeded manual scenarios.
5. Defer all live external integrations until the manual process is signed off.
