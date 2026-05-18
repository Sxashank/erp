# SFC ERP Implementation Roadmap

Prepared for Sagarmala Finance Corporation (Indian NBFC)

Companion documents:
- `refdocs/SFC_NBFC_Corporate_Loan_Lifecycle_Gap_Report.md`
- `refdocs/SFC_ERP_Capabilities_Integrations_Report.md`
- `refdocs/SFC_ERP_Module_Report_List.md`
- `refdocs/SFC_ERP_Client_Deck_Outline.md`

## 1. Roadmap Objective

This roadmap converts the corporate/project loan lifecycle review into an implementation sequence for the ERP. The goal is to build an enterprise-grade NBFC platform that lets management monitor:

- Money raised from banks/FIs/bonds and its cost of funds.
- Corporate/project loans sanctioned, disbursed, serviced, collected, and closed.
- Interest income vs interest expense, spread, NII, and NIM.
- Borrower inflows vs lender outflows and ALM/liquidity gaps.
- Manual collections, manual borrower receipt posting, and manual source-lender payment recording today.
- Overdue, SMA, NPA, provisioning, OTS, legal, compliance, and regulatory reporting.

The roadmap uses corporate/project lending vocabulary. "EMI" should be used only when a product is truly equated monthly repayment; otherwise use "instalment", "EPI", "interest demand", or "repayment schedule".

## 2. Implementation Principles

- Build around loan-level and borrowing-level auditability, not only portfolio totals.
- Keep manual receipt posting, manual lender-payment posting, and manual reconciliation as the current operating baseline.
- Treat dashboards as operational controls, not cosmetic MIS screens.
- Design lending and borrowing together so spread, liquidity, and ALM are visible.
- Separate accounting recognition from borrower liability, especially for NPA/income controls.
- Keep regulatory assumptions configurable until Sagarmala's exact NBFC layer/category is confirmed.
- Continue building accounting, tax, GST, AP/AR, portal, and integration entities/services where they support ERP data integrity, but keep their UI hidden behind release visibility gates until each module is formally released.

## 3. Phase 0: Product and Regulatory Baseline

Objective: Lock scope, terminology, product catalogue, and compliance assumptions before implementation expands.

Key features:
- Define Sagarmala product catalogue: port term loan, maritime term loan, working capital loan, bridge loan, vessel finance, project finance, MSME/startup lending.
- Confirm repayment modes per product: structured, bullet, balloon, moratorium-based, quarterly interest, equated instalment.
- Confirm source-of-funds attribution policy: exact loan-level mapping, portfolio/pool mapping, or hybrid.
- Confirm current collection channels for manual recording: RTGS/NEFT, cheque, escrow transfer, cash if applicable, and manually captured UTR/reference.
- Treat payment gateway, virtual account, bank statement import, NACH/mandate, and bank API integration as future automation only.
- Confirm applicable RBI layer/category, CRILC applicability, ALM returns, large exposure framework, KFS/MSME applicability, and reporting calendar.

Deliverables:
- Approved product and repayment catalogue.
- Regulatory applicability checklist.
- Final terminology glossary.
- Prioritised implementation backlog.

Acceptance criteria:
- Product teams, treasury, finance, risk, and compliance sign off on terminology and scope.
- Each product has lending rate structure, repayment structure, fees, security requirement, and workflow route defined.

## 4. Phase 1: Foundation, Masters, Security, and GL Controls

Objective: Establish the common backbone required by every lending, treasury, finance, and reporting workflow.

Key features:
- Organisation, unit, department, user, role, permission, financial year, currency, and bank account masters.
- Chart of accounts, cost centers, voucher types, approval matrix, and period controls.
- Maker-checker workflow for master changes, vouchers, sanctions, disbursements, receipts, write-offs, and configuration changes.
- Audit trail for create/update/delete/view/approve/reject/login/report/API events.
- Document management with versioning, metadata, access levels, expiry, and entity linkage.
- Notification templates for approvals, demands, due dates, compliance, and exceptions.

Reports and metrics:
- Maker-checker pending list and TAT.
- Voucher status and GL posting exception report.
- Master data change audit report.
- Document expiry and missing document report.

Current manual scope:
- Manual notification, document upload, and document reference tracking.
- External storage, email/SMS gateways, and other integrations are future automation only.

Acceptance criteria:
- All critical transactions can be routed through role-based approval.
- Every posted transaction has source module, source document, voucher, user, and audit trace.
- Reports can be generated and access is logged.

## 5. Phase 2: Corporate Borrower Onboarding, KYC, and Credit Appraisal

Objective: Build the borrower and appraisal foundation for organisation-level lending.

Key features:
- Entity master for companies, port authorities, shipping firms, MSMEs, startups, maritime institutions, promoters, directors, and group entities.
- Borrower contacts, addresses, bank accounts, GST/PAN/TAN, related-party and group exposure mapping.
- KYC document collection, verification, CKYC support, and document checklist.
- Credit rating model, risk parameters, policy exceptions, and rating workflow.
- Corporate/project appraisal: DPR/TEV/CMA, ratios, DSCR, security cover, promoter contribution, project cost, source-of-repayment, escrow status, concession/project milestone risk.
- Exposure checks by borrower, group, sector, product, geography, and internal limits.

Reports and metrics:
- KYC pending/verified/rejected dashboard.
- Credit rating distribution and migration.
- Policy exception report.
- Exposure concentration report.
- Project appraisal summary with DSCR/security cover/promoter contribution.

Current manual scope:
- Manual KYC document tracking and internal verification.
- Manual capture of PAN/GST/TAN/CIN and external credit documents.
- CKYC, credit bureau, MCA, and GSTIN integrations are future automation only.

Acceptance criteria:
- A corporate borrower can be onboarded with related parties and group exposure.
- A credit appraisal can be submitted only after mandatory documents and risk checks are complete.
- Exposure limit breach blocks or escalates as configured.

## 6. Phase 3: Loan Origination, Sanction, and Disbursement Readiness

Objective: Implement the full pre-disbursement lifecycle from application to accepted sanction.

Key features:
- Loan application intake with product, borrower, project, amount, tenure, rate, purpose, and branch/RM details.
- Technical appraisal, financial appraisal, approval recommendation, and exception escalation.
- Sanction workflow with terms, conditions, security, covenants, fees, rate reset terms, moratorium, and repayment structure.
- Conditions precedent/subsequent mapped to sanction, tranche, or project milestone.
- Sanction acceptance and loan account creation trigger.
- Disbursement readiness dashboard: sanctioned, accepted, condition pending, ready for disbursement, expired, cancelled.

Reports and metrics:
- Application pipeline by stage, amount, product, and aging.
- Sanction vs rejection analysis.
- Sanctioned-not-disbursed (SND) report.
- Pre-disbursement condition compliance report.
- Appraisal and approval TAT.

Current manual scope:
- Document management for manually uploaded sanction letters, agreements, board resolutions, and security documents.
- Manual notification/task follow-up for sanction approval, acceptance, and pending conditions.

Acceptance criteria:
- A sanctioned corporate loan cannot move to disbursement if mandatory conditions are pending.
- Management can see sanctioned-not-disbursed exposure by borrower, project, product, and tranche.

## 7. Phase 4: Resource Mobilisation and Borrowing Management

Objective: Implement the liability side of the NBFC model and make borrowing cost visible.

Key features:
- Annual borrowing limit approval by board/committee.
- Lender master and borrowing instrument setup for term loan, CC/OD, bond, NCD, CP, GOI loan, ECB, or multilateral borrowing.
- Borrowing account with sanction amount, drawn amount, undrawn amount, principal outstanding, rate type, base rate, spread, effective rate, maturity, covenants, security, and repayment terms.
- Borrowing drawdowns/tranches and repayment schedule generation.
- Borrowing interest accrual, principal/interest payment, prepayment, closure, and covenant alerts.
- Cost of funds by lender, instrument, tranche, maturity, and portfolio.

Reports and metrics:
- Borrowing position: sanctioned, drawn, undrawn, outstanding.
- Cost of funds dashboard.
- Upcoming borrowing repayment calendar.
- Covenant compliance report.
- Borrowing maturity profile.

Current manual scope:
- Manual borrowing drawdown recording with bank/reference details entered by treasury users.
- Manual source-lender principal and interest repayment recording.
- CBS/bank payment instruction and bank statement import are future automation only.

Acceptance criteria:
- Treasury can record a borrowing facility, drawdown funds, generate schedules, accrue interest, and process repayment.
- Management can see borrowing utilisation and cost of funds at any time.

## 8. Phase 5: Loan Account, Tranche Disbursement, and Schedules

Objective: Convert accepted sanctions into live loan assets with structured repayment schedules.

Key features:
- Loan account creation from accepted sanction.
- Tranche setup by sanction structure, project milestone, borrower request, or disbursement plan.
- Disbursement request workflow with condition check, exposure check, funds availability, bank verification, and approval.
- Payment instruction, UTR/reference capture, and disbursement accounting voucher.
- Principal schedule and interest schedule generation.
- Repayment structures: structured, bullet, balloon, moratorium-based, quarterly interest servicing, equated instalment, sculpted repayment.
- Rate reset workflow for floating-rate loans.

Reports and metrics:
- Disbursement register.
- Tranche-wise utilisation report.
- Payment sent/UTR pending/disbursed report.
- Repayment schedule performance vs actual.
- Rate reset impact report.

Current manual scope:
- Manual disbursement record, payment mode, and UTR/reference capture.
- Manual borrower bank verification based on documents/approval records.
- CBS/payment channel, penny-drop, and borrower portal visibility are future automation only.

Acceptance criteria:
- A multi-tranche corporate loan can be disbursed only after conditions are cleared.
- Schedules are generated without exceeding sanctioned amount, disbursed amount, or maturity date.
- Disbursement voucher and loan outstanding are updated in the same controlled flow.

## 9. Phase 6: Interest Accrual, Demand Generation, and Accounting Recognition

Objective: Implement income/expense accrual and borrower demand workflows.

Key features:
- Borrower interest accrual by loan, tranche, outstanding principal, day-count convention, rate type, and reset terms.
- Borrowing interest expense accrual by borrowing account/tranche/schedule.
- Demand generation for principal, interest, overdue, penal charges, other charges, and previous overdue.
- Manual demand notice/reference tracking, with PDF/export support where available.
- Accounting vouchers for interest income accrual, interest received, interest expense accrual, borrowing payment, reversals, and adjustments.
- NPA income control: suspend/reverse unrealised income as per applicable policy while retaining borrower liability.
- Penal charges handling as charges, not as additional penal interest, where applicable.

Reports and metrics:
- Interest income accrual report.
- Interest expense accrual report.
- Demand due calendar.
- Demand generated/sent/paid/overdue report.
- NII and spread summary.
- Income recognition exception report.

Current manual scope:
- Manual demand communication tracking.
- Manual or workflow-driven GL/voucher posting.
- Email/SMS gateway and borrower portal delivery are future automation only.

Acceptance criteria:
- Borrower interest income and borrowing interest expense can be computed independently and reconciled.
- Demand generation creates due records, updates next demand date, and supports manual notice/reference tracking.
- NPA accounts do not continue recognising income in violation of configured policy.

## 10. Phase 7: Manual Collections, Receipt Allocation, and BRS

Objective: Stabilise current manual collection operations and reconcile bank records.

Key features:
- Manual receipt entry with loan account, demand, receipt date, value date, payment mode, UTR, deposited bank, borrower bank, TDS, and remarks.
- Receipt allocation waterfall by product: penal/charges, overdue interest, current interest, overdue principal, current principal, or configured sequence.
- Partial receipt, excess receipt, TDS-deducted receipt, reversal, bounce, and unallocated receipt handling.
- Manual BRS observation and reconciliation status tracking.
- Bank statement import through CSV/Excel and future API-ready design is deferred until automation is approved.
- Collection exception queue for unapplied/unallocated receipts.

Reports and metrics:
- Daily collection summary.
- Manual receipt posting register.
- Demand vs receipt vs allocation reconciliation.
- Unallocated receipts aging.
- BRS unmatched item aging.
- Collection efficiency.
- DPD movement due to payment/non-payment.

Current manual scope:
- Manual receipt entry and manual allocation.
- Manual UTR/reference capture.
- Manual TDS deduction capture where borrower deducts TDS.
- Manual GL/voucher posting or workflow-driven internal posting.
- Bank statement file import and bank API integration are future automation only.

Acceptance criteria:
- A receipt can be posted manually, allocated to due components, and reflected in loan outstanding.
- Partial payments update allocation and overdue status correctly.
- Manual receipt records can be reconciled against ERP vouchers and manually maintained bank/BRS observations.

## 11. Phase 8: Future Automated Bank Credit Matching and Collection Automation

Objective: Optional future phase to move from manual receipt identification to controlled automatic loan-level matching. This is not part of the current manual implementation scope.

Key features:
- Bank statement import batch with normalised UTR, narration, value date, amount, bank reference, and account identifier.
- Matching rules using UTR/reference, virtual account, borrower bank account, amount, value date, due date window, loan account number, borrower name, demand number, and tolerance.
- Matching confidence score and decision log.
- Auto-create draft receipt or auto-post receipt based on policy threshold.
- Exception queue for no match, multiple match, amount mismatch, partial payment, excess payment, duplicate UTR, TDS, reversal, and delayed payment.
- User override with audit trail.
- Optional future NACH/mandate/payment gateway reconciliation if Sagarmala adopts those channels.

Reports and metrics:
- Auto-match success rate.
- Exception aging by reason.
- Manual override report.
- Duplicate/failed/reversed payment report.
- Collection automation productivity report.

Future integrations only:
- Bank statement APIs or secure file transfer.
- Virtual account/payment gateway/NACH if selected later.

Acceptance criteria:
- Imported bank credit can be matched to the correct borrower loan and demand using deterministic rules.
- Exceptions are not auto-posted without policy approval.
- Every automated or overridden match has an audit trail.

## 12. Phase 9: Treasury, ALM, Spread, and Profitability Cockpits

Objective: Give management the core NBFC margin and liquidity view.

Key features:
- Source-of-funds mapping: exact loan-level, pool-level, or hybrid attribution.
- Cost of funds calculation by borrowing pool/instrument.
- Lending yield calculation by loan/product/project.
- Spread, NII, NIM, and margin bridge.
- Asset inflow and liability outflow calendar.
- ALM maturity ladder and structural liquidity gap.
- Interest rate sensitivity analysis for floating-rate assets and liabilities.
- Liquidity buffer and mismatch alerts.

Reports and metrics:
- Executive lifecycle cockpit.
- Treasury funding cockpit.
- ALM cockpit.
- Spread/NII/NIM report.
- Upcoming borrower inflows vs borrowing repayments.
- Cost of funds vs yield trend.
- Rate reset calendar.

Current manual scope:
- Borrowing schedules.
- Loan schedules and demands.
- GL actuals entered/posted in ERP.
- Manually maintained bank balance and BRS observations.

Acceptance criteria:
- Management can see whether expected borrower collections cover upcoming lender obligations.
- Spread/NII/NIM can be viewed by product, project, borrower, lender, and portfolio.
- ALM buckets include both loan inflows and borrowing outflows.

## 13. Phase 10: Risk, SMA/NPA, Provisioning, OTS, and Legal

Objective: Complete the stressed asset and recovery lifecycle.

Key features:
- DPD calculation from contractual due date.
- SMA and NPA classification rules.
- NPA history, upgrade eligibility, provisioning, and write-off tracking.
- Stop/reversal controls for income recognition on NPA accounts.
- OTS proposal, approval workflow, haircut calculation, payment tracking, and settlement closure.
- Legal case management for SARFAESI, DRT, NCLT, arbitration, civil cases, notices, hearings, expenses, and recovery status.
- CRILC/large exposure readiness inputs.

Reports and metrics:
- DPD aging.
- SMA monitoring.
- NPA movement.
- Provisioning report.
- OTS pipeline and recovery effectiveness.
- Legal case status and expense report.
- CRILC/large exposure readiness report.

Current manual scope:
- Manual task/notification follow-up to RM, credit head, recovery, legal, and borrower.
- Document management for manually uploaded legal/security documents.
- Manual compliance/regulatory report preparation and file export.

Acceptance criteria:
- Overdue accounts move through configured SMA/NPA stages.
- Provisioning and income recognition controls are triggered by classification.
- OTS/legal status is visible in management dashboards.

## 14. Phase 11: Compliance, Regulatory Reporting, and Governance

Objective: Align operations with RBI/NBFC, MCA, GST, IT, and internal governance needs.

Key features:
- Compliance calendar with RBI, MCA, GST, IT, statutory auditor certificate, ALM, CRILC, and board/committee items.
- Compliance instance workflow: prepare, review, approve, file, acknowledge, archive.
- Regulatory return checklist linked to Sagarmala's confirmed NBFC layer/category.
- Audit trail retention policies.
- Sensitive data access logging.
- Board/committee pack generation.

Reports and metrics:
- Compliance tracker.
- Filing delay and penalty report.
- Regulatory return status.
- Audit trail and sensitive access report.
- Board approval pending report.

Current manual scope:
- RBI/CIMS/COSMOS manual upload support or file-generation support as applicable.
- Manual MCA/GST filing status and acknowledgement tracking.
- MCA/GST portal integrations are future automation only.

Acceptance criteria:
- Compliance team can track every filing from due date to acknowledgement.
- Management can see upcoming, delayed, and completed compliance obligations.

## 15. Phase 12: Future Portals, Self-Service, and External Stakeholder Experience

Objective: Optional future phase to reduce internal support load and improve stakeholder transparency. This is not part of the current manual implementation scope.

Key features:
- Borrower portal: loan summary, schedules, demands, statements, receipts, documents, requests, NOC/closure requests, and payment status.
- Vendor portal: PO, invoice, payment status, TDS certificates, compliance uploads.
- Employee ESS: leave, attendance, payslips, claims, documents, helpdesk.
- Portal MFA, lockouts, role/entity mapping, and audit logs.

Reports and metrics:
- Portal adoption.
- Service request aging and SLA.
- Document download/upload activity.
- Borrower request category trends.

Future integrations only:
- Payment gateway if online collections are enabled.
- Email/SMS/OTP gateway.
- Document management linkage for external users.

Acceptance criteria:
- Borrowers can view accurate loan demands, schedules, receipts, and documents.
- Portal actions are audited and visible to operations teams.

## 16. Phase 13: BI, Dashboards, and Board-Level Analytics

Objective: Convert operational data into decision-grade management analytics.

Key dashboards:
- Executive lifecycle cockpit.
- Loan pipeline cockpit.
- Disbursement readiness cockpit.
- Collections and reconciliation cockpit.
- Closure and security release cockpit.
- Treasury funding cockpit.
- ALM and liquidity cockpit.
- Spread/NII/NIM profitability cockpit.
- Risk, SMA/NPA, and provisioning cockpit.
- Compliance cockpit.
- HR and operational productivity cockpit.

Core KPIs:
- AUM, sanctioned amount, disbursed amount, SND.
- Collection efficiency, overdue amount, DPD, SMA, gross NPA, net NPA.
- Cost of funds, lending yield, spread, NII, NIM.
- Borrowing outstanding, borrowing utilisation, upcoming repayments.
- ALM gap, cumulative mismatch, liquidity buffer.
- CRAR, exposure concentration, provisioning coverage.
- Application TAT, sanction TAT, disbursement TAT.
- Future auto-match rate, reconciliation exceptions, unallocated receipts.

Acceptance criteria:
- Dashboards are role-based and drill down from portfolio to borrower/loan/tranche.
- Data definitions for each KPI are documented and consistent across reports.

## 17. Suggested Delivery Sequence

| Wave | Focus | Recommended Phases | Outcome |
| --- | --- | --- | --- |
| Wave 1 | Foundation and control | Phases 0-1 | Common masters, GL, audit, workflow, DMS |
| Wave 2 | Lending setup | Phases 2-3 | Corporate onboarding, appraisal, sanction, readiness |
| Wave 3 | Core assets/liabilities | Phases 4-6 | Borrowings, loan accounts, disbursements, schedules, demands |
| Wave 4 | Current collections | Phase 7 | Manual receipt posting, allocation, BRS |
| Wave 5 | Management visibility | Phases 9 and 13 | Spread, ALM, dashboards, board MIS |
| Wave 6 | Risk and compliance | Phases 10-11 | SMA/NPA, provisioning, legal, compliance |
| Wave 7 | Future automation and portals | Phases 8 and 12 | Optional bank matching, borrower/vendor/employee self-service |

## 18. Sprint Completion Status

The current sprint set is implemented as a manual-first operating model. It gives management visibility across the corporate loan lifecycle without activating bank, portal, bureau, GSTN, MCA, payment gateway, or NACH integrations.

| Sprint | Status | Implemented outcome |
| --- | --- | --- |
| Executive lending dashboard | Complete | Role-level view of pipeline, sanctioned/disbursed AUM, collections, risk, treasury, and lifecycle exceptions. |
| Manual disbursement readiness cockpit | Complete | Sanctioned-not-disbursed exposure, ready sanctions, condition blockers, expired sanctions, and pending manual disbursement requests. |
| Manual receipt and allocation cockpit | Complete | Borrower demand, manual receipt posting, allocation efficiency, overdue ageing, and unallocated receipt exceptions. |
| Closure and release cockpit | Complete | Zero-outstanding closure candidates, closed-pending-release loans, unreleased security/document controls, and recent manual closure receipts. |
| Approval checklist module | Complete | Loan checklist templates and application-level checklist controls remain visible in the loan release scope. |
| Interest subvention module | Complete | IIF schemes, categories, enrollments, and claims remain visible as lending-domain operations. |
| Source-of-funds workbench | Complete | Manual mapping between borrowing drawdowns and lending deployment for cost-of-funds and spread visibility. |
| Profitability analytics | Complete | Lending yield, borrowing cost, spread, NII, and margin visibility based on ERP-recorded schedules and actuals. |
| Treasury and ALM visibility | Complete | Borrowing utilisation, upcoming lender obligations, maturity buckets, and liquidity gap inputs. |
| Credit risk cockpit | Complete | Exposure concentration, DPD/SMA/NPA movement, provisioning visibility, and risk exceptions. |
| Manual-first documentation reset | Complete | Client-facing materials now state that current operations are manual and integrations are future automation only. |
| Release visibility gates | Complete | Accounting, tax, GST, AP/AR, portal admin, and future automation screens stay hidden in manual-first release mode while backend/entities remain available for controlled data flows. |
| Future automation design | Deferred | Bank statement import, automated repayment matching, portals, payment gateways, GSTN/MCA/CKYC/bureau integrations, and NACH remain roadmap items only. |

## 19. Master Acceptance Checklist

- Management can track funds raised, funds deployed, and funds available.
- Management can see loan pipeline, sanctioned-not-disbursed exposure, and disbursement readiness.
- System supports corporate/project repayment structures beyond simple EMI.
- Borrower interest income and borrowing interest expense are accrued and reconciled.
- Manual receipts are posted and allocated correctly.
- Manual receipt recording, manual allocation, and manual lender-payment recording are available.
- Future automated matching is designed with audit and exception controls but not enabled in the current scope.
- ALM shows loan inflows and borrowing outflows by bucket.
- Spread, NII, NIM, yield, cost of funds, and liquidity are visible.
- SMA/NPA/provisioning/legal lifecycle is connected to collections and dashboards.
- Compliance calendar and regulatory reporting dependencies are tracked.
- Dashboards and reports use documented KPI definitions.

## 20. Key Decisions Still Needed

- Confirm exact RBI NBFC layer/category and applicable reporting obligations.
- Confirm source-of-funds attribution level: loan-level, pool-level, or hybrid.
- Confirm whether and when any collection automation channel should be added: bank statement file import, bank API, virtual account, payment gateway, or NACH.
- Confirm which dashboards are needed for go-live vs board pack phase.
- Confirm whether portfolio profitability should be calculated on booked accruals, cash basis, or both.
