# Sagarmala Finance Corporation ERP

## Corporate / Project Loan Lifecycle Gap Report and Roadmap

Prepared for Sagarmala Finance Corporation (Indian NBFC)

Implementation roadmap: `refdocs/SFC_ERP_Implementation_Roadmap.md`

## 1. Purpose and Scope

This document reviews the end-to-end corporate/project loan lifecycle for Sagarmala Finance Corporation, with a specific focus on an enterprise NBFC model:

- The NBFC raises money from banks, financial institutions, bonds, NCDs, CPs, or government/multilateral sources at a defined cost of funds.
- The NBFC lends to organisations, projects, port authorities, shipping companies, maritime infrastructure entities, MSMEs, startups, and allied maritime sector institutions at a lending rate higher than the borrowing cost.
- The spread between lending yield and borrowing cost contributes to net interest income, subject to credit risk, liquidity risk, operating cost, provisioning, and compliance requirements.
- The ERP must give management a live view of both sides of the balance sheet: money borrowed, money lent, upcoming inflows, upcoming outflows, overdue accounts, profitability, and regulatory position.

This is not a retail/personal loan lifecycle. The correct vocabulary for this ERP should be "corporate loan", "project finance", "term loan", "structured repayment", "tranche", "interest demand", "repayment instalment", or "EPI/instalment" rather than only "EMI".

## 2. Research and Regulatory Anchors

- Sagarmala Finance Corporation Limited is described by the Sagarmala portal as India's first maritime sector-specific NBFC, registered with RBI on June 19, 2025, and focused on financing ports, shipping, shipbuilding, cruise tourism, renewable energy, maritime education, MSMEs, startups, and maritime institutions.
- RBI's NBFC Scale Based Regulation Directions, 2023 are the base regulatory framework for NBFC governance, prudential norms, and scale-based classification.
- RBI NBFC reporting references include NBS returns, ALM returns, CRILC reporting for eligible NBFCs, statutory auditor certificates, and prudential return requirements.
- RBI's KFS circular applies to retail and MSME term loans and defines EPI/EMI as fixed periodic repayment amounts. For SFC, KFS/MSME applicability should be checked product-wise.
- RBI large exposure rules and CRILC requirements matter for enterprise borrowers because exposure concentration and group borrower reporting are central risks.
- RBI ALM reporting references require maturity/bucket-based monitoring of asset-liability mismatches and interest rate sensitivity.

Reference links:
- https://sagarmala.gov.in/about-sagarmala/sagarmala-finance-corporation-limited-sfcl
- https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12550
- https://www.rbi.org.in/ScriptS/BS_ViewMasDirections.aspx?id=10620
- https://www.rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx?Id=12663
- https://www.rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx?Id=12298
- https://rbi.org.in/Scripts/BS_Listofreturns.aspx

## 3. Target End-to-End Lifecycle

### Stage 1: Resource Mobilisation / Borrowing

What happens:
- Board or authorised committee approves annual borrowing limits and eligible instruments.
- Treasury raises funds through term loans, working capital lines, bonds, NCDs, CPs, GOI loans, multilateral borrowings, or bank/FI facilities.
- Each borrowing has lender, sanction amount, drawdown schedule, repayment schedule, rate type, reset terms, covenants, security, maturity, and repayment mode.
- Drawdown credits SFC's bank account and creates a liability with principal outstanding and interest payable.

ERP should support:
- Borrowing program approval and utilisation tracking.
- Lender master, borrowing account, drawdown/tranche records, and repayment schedules.
- Borrowing interest accrual and payment vouchers.
- Covenant tracking and due-date alerts.
- Cost of funds by instrument, lender, maturity, and tranche.

Current coverage:
- Phase 4 covers lender master, borrowing account, borrowing tranches, borrowing schedules, borrowing lifecycle, covenant details, ALM mapping, and borrowing rules.

Key gap:
- Borrowings and lending assets are tracked separately, but the specs do not clearly define source-of-funds deployment or how cost of funds flows into project/portfolio profitability.

### Stage 2: Borrower Onboarding and Appraisal

What happens:
- Organisation borrower is onboarded with legal, KYC, group, promoter, GST/PAN, bank, project, and related-party data.
- Credit appraisal checks sector, project viability, financials, cash flow, repayment capacity, security, approvals, and exposure concentration.
- For corporate/project finance, repayment capacity is based on projected project cash flows, DSCR, escrow/receivable structure, contracts, concessions, and sponsor support.

ERP should support:
- Entity master for organisations, promoters, directors, group companies, related parties, and bank accounts.
- KYC/CKYC and document verification.
- Credit rating model and appraisal workflow.
- DPR/TEV/CMA/ratio analysis and policy exception capture.
- Exposure checks at borrower, group, sector, product, and geography level.

Current coverage:
- Phase 2 covers entity master, KYC, credit rating, loan products, application, technical appraisal, financial appraisal, sanction, and conditions.

Key gap:
- Corporate project finance should explicitly include DSCR, escrow arrangement, security cover, concession/project milestone risk, source-of-repayment, and sponsor support visibility.

### Stage 3: Sanction and Pre-Disbursement

What happens:
- Sanction terms define amount, tenure, rate, spread, reset terms, repayment frequency, moratorium, security, covenants, fees, and conditions precedent/subsequent.
- Borrower accepts sanction and executes documents.
- Pre-disbursement checks confirm legal documentation, security creation, CERSAI charge registration where applicable, equity infusion, insurance, permissions, board resolutions, and milestone readiness.

ERP should support:
- Sanction approval workflow and authority matrix.
- Conditions checklist linked to tranche or disbursement milestone.
- Document management with versioning and expiry.
- Security/collateral and legal verification status.
- Readiness dashboard: sanctioned not accepted, accepted but conditions pending, conditions cleared, ready for disbursement.

Current coverage:
- Phase 2 and Phase 3 cover sanction, terms, conditions, security, loan account creation, and disbursement rules.

Key gap:
- The client-facing docs should show "disbursement readiness" as a major management control point, not just a technical workflow.

### Stage 4: Loan Account Creation and Tranche Disbursement

What happens:
- Accepted sanction becomes a loan account.
- Tranches are set up as per sanction, milestone, project progress, or borrower drawdown request.
- Each disbursement checks conditions, exposure, funds availability, bank verification, and approvals.
- Payment is executed through bank/CBS/payment instruction and confirmed through UTR/reference.
- Schedules are generated or updated for principal and interest.

ERP should support:
- Loan account generation from accepted sanction.
- Multi-tranche drawdowns and milestone-linked disbursement.
- Payment instruction and UTR capture.
- Accounting voucher generation.
- Schedule generation for structured repayment, bullet, balloon, moratorium, quarterly interest, and project cash-flow based repayment.

Current coverage:
- Phase 3 supports loan account, tranches, disbursement request, disbursement record, payment reference, and schedule generation.

Key gap:
- The schedule model should explicitly support enterprise/project repayment patterns such as quarterly interest servicing, principal moratorium, sculpted repayment, balloon repayment, and DSCR-linked structured schedules.

### Stage 5: Interest Accrual, Demand, and Income Recognition

What happens:
- Borrower interest accrues based on outstanding principal, rate type, day-count convention, reset terms, and compounding rules.
- Borrowing interest expense accrues independently on SFC's liability side.
- Demand notices are generated before due date for interest, principal, overdue, penal charges, and other charges.
- Income recognition must be controlled when an account becomes overdue/NPA.

ERP should support:
- Borrower interest accrual and lender interest expense accrual.
- Rate reset calendars for floating-rate assets and liabilities.
- Demand generation and communication logs.
- GL entries for accrued income, interest received, interest expense, borrowing payment, and reversals.
- NPA income suspension/reversal controls.

Current coverage:
- Phase 3 covers interest schedules, interest accrual, rate reset, and demand generation.
- Phase 4 covers borrowing schedules and interest payable.
- Phase 1 covers GL/voucher workflow.

Key gap:
- There is no consolidated "interest margin engine" view showing borrower interest receivable vs borrowing interest payable, net interest income, spread, NIM, and liquidity timing mismatch.

### Stage 6: Collections and Receipt Allocation

What happens now:
- EMI/instalment receipts are manually recorded.
- Finance/operations posts receipt details, including payment mode, UTR, amount, value date, TDS, and bank account.
- Receipt is allocated to dues according to a waterfall: penal charges, other charges, overdue interest, current interest, overdue principal, current principal, or product-specific rules.

What should happen later:
- Bank statements are imported.
- Incoming credits are automatically matched to the correct borrower/loan/demand using UTR, virtual account, borrower bank account, amount, value date, narration, and expected schedule.
- Exceptions go to a matching queue.
- Partial, excess, unidentified, or duplicate receipts are handled through suspense/unallocated receipt workflows.

ERP should support:
- Manual receipt entry as current state.
- Manual BRS observation/reconciliation status tracking as current state.
- Future bank statement import and BRS automation only if approved later.
- Future auto matching rules with confidence score and exception queue.
- Partial payment handling and DPD impact.
- Receipt allocation history and reversal controls.
- Collection efficiency dashboards.

Current coverage:
- Phase 3 covers receipt record and allocation.
- Phase 6 covers BRS concepts; current SFC scope should use manual reconciliation tracking.

Key gap:
- Current documentation must separate manual receipt recording from future bank statement automation. BRS matches bank vs books, while future loan repayment automation would need bank credit -> borrower -> loan account -> demand/schedule -> allocation.

### Stage 7: Borrowing Repayment and Liquidity Management

What happens:
- SFC uses collections, cash balances, new drawdowns, investments, or other funding to meet scheduled interest/principal payments to banks/FIs/bondholders.
- Treasury monitors whether upcoming borrower inflows are sufficient to cover lender outflows.
- ALM buckets classify future loan inflows and borrowing outflows by timing.

ERP should support:
- Upcoming lender obligation calendar.
- Upcoming borrower inflow calendar.
- Daily liquidity position.
- ALM structural liquidity statement.
- Mismatch alerts and escalation to ALCO/management.
- Borrowing repayment vouchers and bank payment confirmation.

Current coverage:
- Phase 4 covers borrowing payment, ALM generation, asset/liability bucket mapping, and ALM rules.

Key gap:
- Management dashboards should clearly show "expected borrower collections vs borrowing repayments" by date bucket and project/portfolio, not just aggregate ALM reports.

### Stage 8: Monitoring, Overdue, SMA, NPA, OTS, and Legal

What happens:
- DPD starts from the contractual due date when an amount remains unpaid.
- SMA and NPA categories are tracked based on overdue status.
- NPA accounts require income recognition controls, provisioning, recovery tracking, and possible legal action.
- Corporate loans may move to restructuring, OTS, SARFAESI, DRT, NCLT, arbitration, or civil recovery depending on terms and security.

ERP should support:
- DPD, SMA, NPA, and provisioning automation.
- Overdue alerts to RM, credit, recovery, and borrower.
- NPA classification history and upgrade conditions.
- OTS proposal, approval, payment tracking, and haircut/write-off.
- Legal case and expense tracking.
- CRILC/large exposure and regulatory reporting inputs.

Current coverage:
- Phase 3 Part 2 covers receipts, NPA, OTS, and legal.
- Phase 4 covers exposure and portfolio risk.
- Phase 7 covers compliance and dashboards.

Key gap:
- Client documents should clarify the risk lifecycle from overdue -> SMA -> NPA -> provisioning -> recovery/legal and connect it to dashboards.

### Stage 9: Closure, Prepayment, and Release

What happens:
- Borrower may repay as scheduled, prepay, part-prepay, foreclose, settle under OTS, or close after maturity.
- System calculates outstanding principal, interest, charges, TDS adjustment, prepayment penalty if applicable, and final settlement.
- Security/collateral release and NOC/document release are processed.

ERP should support:
- Foreclosure/prepayment quote.
- Final outstanding and closure workflow.
- NOC/document release.
- Security release checklist.
- Final GL settlement and closure status.

Current coverage:
- Phase 3 supports prepayment/foreclosure receipt types and closure controls.
- Phase 7 borrower portal supports NOC requests and document download.

Key gap:
- Closure should be shown as a governed lifecycle stage with document release and collateral release controls.

## 4. Gap Matrix

| Area | Current Coverage | Gap | Recommendation | Priority |
| --- | --- | --- | --- | --- |
| Borrowing to lending linkage | Borrowing and loan schedules exist separately | No explicit source-of-funds deployment or spread attribution | Add source-of-funds mapping and profitability views | High |
| Corporate repayment vocabulary | EMI, structured, balloon, bullet, moratorium EMI | Client docs overuse EMI language | Use instalment/EPI/repayment schedule and define EMI as one variant | High |
| Project finance schedules | Structured repayment exists | DSCR-linked/sculpted repayment not explicit | Add repayment structure examples and validation rules | High |
| Interest margin visibility | Interest income and expense exist separately | No combined NII/NIM cockpit | Add spread/NII lifecycle and dashboard | High |
| Bank statement to loan matching | Bank statement import and BRS exist | No loan-level auto matching workflow | Add future-state receipt matching design | High |
| Manual collections current state | Receipt entry exists | Current vs future automation not clearly explained | Document manual receipt now, automation later | High |
| Liquidity view | ALM exists | No plain management view of inflows vs outflows | Add cash flow and ALM cockpit | High |
| Disbursement readiness | Conditions and disbursement rules exist | Not surfaced as management dashboard | Add sanctioned-not-disbursed and readiness dashboard | Medium |
| NPA/risk lifecycle | NPA/OTS/legal exists | Not connected end-to-end in client docs | Add overdue -> SMA -> NPA -> recovery narrative | Medium |
| Regulatory dependencies | Compliance module exists | Sagarmala exact NBFC layer not confirmed | Add regulatory dependency note and validation checklist | Medium |
| Closure controls | Closure, NOC, security/document release, and recent closure receipts are surfaced in a closure cockpit | Keep future borrower portal NOC requests deferred until portal release | Monitor manually | Medium |

## 5. Recommended Management Cockpits

### 5.1 Executive Lifecycle Cockpit

- Applications in pipeline by stage, value, and aging.
- Sanctioned amount, accepted amount, sanctioned-not-disbursed amount.
- Disbursed AUM, principal outstanding, interest outstanding.
- Collections due today/week/month vs received.
- Borrowing outstanding and upcoming lender payments.
- Gross spread, NII, NIM, cost of funds, yield on advances.
- Overdue, SMA, NPA, provisioning, and recovery status.

### 5.2 Loan Origination and Disbursement Cockpit

- Applications awaiting appraisal, credit review, sanction, acceptance.
- Conditions precedent pending by loan/tranche.
- Tranche-wise drawdown requests and approval status.
- Funds availability and exposure check status.
- Payment sent, UTR pending, disbursement completed.

### 5.3 Collections and Reconciliation Cockpit

- Demand generated, demand sent, due today, overdue.
- Manual receipts posted and pending allocation.
- Bank statement credits imported and unmatched.
- Matching exceptions by reason: no UTR match, amount mismatch, duplicate, partial payment, unidentified borrower.
- Collection efficiency and DPD movement.

### 5.4 Treasury and ALM Cockpit

- Borrowing limit approved, utilised, and available.
- Borrowing by lender/instrument/rate/maturity.
- Upcoming borrower inflows vs lender outflows by bucket.
- Structural liquidity gaps and cumulative gaps.
- Rate reset calendar for assets and liabilities.
- Covenant breach alerts and liquidity buffer.

### 5.5 Risk and Compliance Cockpit

- Exposure by borrower, group, sector, product, and geography.
- SMA/NPA movement and provisioning.
- CRILC/large exposure reporting readiness.
- RBI/MCA/GST/IT compliance tracker.
- Audit exceptions and sensitive data access.

## 6. Future Bank Statement and Instalment Matching Design

### Current State

- User manually records borrower payment as a receipt.
- User selects loan account/demand and allocates receipt manually.
- BRS observations and reconciliation status are maintained manually against vouchers.

### Future State

1. Import bank statement file/API feed into a bank statement import batch.
2. Standardise narration, UTR, value date, amount, account number, and bank reference.
3. Match credit transaction to expected borrower receipt using:
   - UTR/reference captured in demand notice or borrower portal.
   - Virtual account or collection account identifier.
   - Borrower bank account from entity master.
   - Exact or tolerance-based amount match against due demand.
   - Due date/value date window.
   - Loan account number, borrower name, or invoice/demand number in narration.
4. Create matched receipt in draft or auto-posted status depending on confidence and policy.
5. Allocate receipt using product waterfall.
6. Route exceptions to a reconciliation queue.
7. Produce audit trail of match decision, user override, and allocation result.

### Exception Types

- No borrower match.
- Multiple possible borrower matches.
- Amount mismatch.
- Partial payment.
- Excess payment.
- Duplicate UTR/reference.
- TDS deducted by borrower.
- Payment received after due date.
- Reversal/bounce/chargeback.

## 7. Accounting View

### Borrowing Drawdown

- Debit: Bank
- Credit: Borrowing liability

### Borrower Loan Disbursement

- Debit: Loan asset / principal outstanding
- Credit: Bank

### Borrower Interest Accrual

- Debit: Interest receivable / accrued income
- Credit: Interest income

### Borrowing Interest Accrual

- Debit: Interest expense
- Credit: Interest payable

### Borrower Receipt

- Debit: Bank
- Credit: Interest receivable, principal outstanding, charges, penal charges, or suspense based on allocation

### Borrowing Repayment

- Debit: Borrowing liability / interest payable
- Credit: Bank

### NPA Income Control

- Stop or reverse unrealised income recognition as per applicable IRAC policy.
- Keep borrower liability visible even if income recognition is suspended.
- Track provisioning separately from legal/recovery outstanding.

## 8. Terminology Glossary

| Term | Meaning in SFC ERP |
| --- | --- |
| Borrowing | Money raised by SFC from banks, FIs, bonds, NCDs, CPs, GOI, or multilateral sources. |
| Drawdown | Actual utilisation of a sanctioned borrowing line or lending tranche. |
| Lending asset | Loan given by SFC to an organisation/project and recorded as an asset. |
| Tranche | Part disbursement under a sanctioned loan or borrowing facility. |
| Moratorium | Period where principal repayment may be deferred while interest may still accrue or be serviced. |
| Structured repayment | Repayment schedule customised to project cash flows instead of equal monthly payments. |
| EPI/EMI | Equated Periodic Instalment; EMI is monthly EPI. For corporate loans, use "instalment" unless repayment is truly monthly/equated. |
| Demand | Notice/record of amount due from borrower for a period. |
| Receipt allocation | Splitting received money across penal charges, fees, interest, principal, and other dues. |
| Spread | Difference between lending yield and cost of funds. |
| Cost of funds | Weighted cost SFC pays on borrowings. |
| NII | Net Interest Income: interest income minus interest expense. |
| NIM | Net Interest Margin: NII over average earning assets. |
| DPD | Days Past Due from contractual due date. |
| SMA | Special Mention Account, an early stress classification before NPA. |
| NPA | Non-performing asset based on overdue/classification norms. |
| Provisioning | Accounting provision for expected/non-performing credit losses. |
| ALM | Asset Liability Management, matching expected asset inflows and liability outflows. |
| CRILC | Central Repository of Information on Large Credits reporting framework. |

## 9. Execution Roadmap

### Phase A: Documentation and Lifecycle Spec Cleanup

- Update all client-facing docs to use corporate/project lending vocabulary.
- Add lifecycle diagrams and current-state/future-state collection flow.
- Add regulatory dependency note for exact NBFC layer/category.
- Clarify which products are term loans, bridge loans, working capital loans, and project finance.

### Phase B: Data Model and Workflow Additions

- Add source-of-funds / borrowing deployment mapping concept.
- Add collection matching concepts: import batch, match rule, confidence score, exception queue, suspense receipt.
- Add project finance repayment metadata: moratorium, sculpted schedule, DSCR target, repayment source, escrow, milestone.
- Add interest margin analytics data views.

### Phase C: Reporting and Dashboard Additions

- Build executive lifecycle cockpit.
- Build disbursement readiness cockpit.
- Build treasury and ALM cockpit.
- Build collection and reconciliation cockpit.
- Build risk and compliance cockpit.

### Phase D: Future Automation of Bank Statement Import and Repayment Matching

- This phase is not part of the current manual operating scope.
- Start with CSV/Excel bank statement upload only if SFC approves collection automation later.
- Add deterministic matching by UTR, amount, borrower bank account, and demand number.
- Add exception workflow and user override audit trail.
- Later integrate bank APIs, virtual accounts, payment gateway, or NACH/mandate flows if required.

## 10. Acceptance Scenarios

- A corporate project loan is sanctioned for multiple tranches and appears as sanctioned-not-disbursed until conditions are cleared.
- A borrowing drawdown is recorded and management can see available borrowing limit, cost of funds, and upcoming lender repayments.
- A tranche is disbursed after mandatory pre-disbursement conditions are met and schedules are generated.
- Borrower interest demand is generated and appears in upcoming inflows.
- Manual receipt is entered, allocated to dues, and reflected in outstanding balances.
- Future scenario: imported bank credit is matched to a borrower loan using UTR/reference/amount/date rules if bank statement import is enabled later.
- Partial payment remains partly allocated and partly overdue, with DPD updated from contractual due date.
- Upcoming borrower inflows and lender outflows are visible in ALM buckets.
- Overdue account moves through SMA/NPA lifecycle and appears in risk dashboard.
- Management dashboard shows applications in process, sanctioned not disbursed, disbursed AUM, collections due/received, borrowing obligations, margin, and risk status.

## 11. Open Validation Items

- Confirm Sagarmala Finance Corporation's RBI layer/category and applicable regulatory returns.
- Confirm exact product list: port term loan, maritime term loan, working capital loan, bridge loan, vessel finance, project finance, MSME/startup lending.
- Confirm manual borrower repayment recording fields: payment mode, UTR/reference, value date, borrower bank, deposited bank, TDS, and remarks.
- Separately confirm whether future automation channels such as payment gateway, NACH, virtual account, or bank import are required later.
- Confirm whether source-of-funds attribution is needed at exact loan level or portfolio/pool level.
- Confirm desired dashboard refresh frequency and management hierarchy.
