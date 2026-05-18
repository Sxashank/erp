# SFC ERP Module-Specific Reports and Analytics

Prepared for SFC (NBFC)

Implementation roadmap: `refdocs/SFC_ERP_Implementation_Roadmap.md`

## How to Use This List
This is a structured catalog of reports by module. It combines standard MIS from the specs with module-level analytics typically required by NBFC operations. Items can be enabled or tailored to SFC's governance and statutory calendar.

For Sagarmala Finance Corporation, report names should use corporate/project lending vocabulary. Use "repayment instalment", "interest demand", "structured repayment", and "tranche" as the default terminology; use "EMI" only where the product is truly equated monthly repayment.

## Enterprise Masters and General Ledger
- Trial balance (daily/monthly) with drill-down by unit and cost center.
- P&L and balance sheet snapshots with variance vs budget/previous period.
- GL account ledger and voucher audit trail reports.
- Cash/bank book and day book.
- Maker-checker approval pending and turnaround time (TAT) reports.
- Interest income vs interest expense reconciliation.
- Borrowing drawdown, loan disbursement, receipt, and borrowing repayment voucher audit reports.

## Lending Masters, KYC, and Credit Rating
- KYC status dashboard by borrower segment and branch.
- CKYC verification summary and exception reports.
- Credit rating distribution and migration analysis.
- Policy exceptions and overrides report.

## Loan Origination System (LOS)
- Application pipeline: stage-wise volume, value, and aging.
- Sanction vs rejection analysis with reason codes.
- Appraisal TAT and sanction authority utilization.
- Pre-disbursement condition compliance report.
- Sanctioned-not-disbursed (SND) report by borrower, project, product, and tranche.
- Project finance appraisal summary including DSCR, security cover, promoter contribution, and escrow/source-of-repayment status.

## Loan Accounting and Servicing (LAMS)
- Disbursement register and tranche-wise utilization.
- Repayment schedule performance vs actuals.
- Interest accrual summary and income recognition.
- Rate reset impact analysis and upcoming reset list.
- Tranche-wise demand calendar for principal, interest, charges, and overdue amounts.
- Structured repayment and moratorium monitoring report.
- Loan closure, prepayment, and NOC/document release report.
- Closure and release cockpit showing closure-ready loans, closed-pending-release loans, unreleased securities, original-document custody, and recent foreclosure/prepayment/OTS receipts.

## Receipts, Collections, NPA, and Legal
- Daily collection summary and allocation status.
- Overdue aging (DPD buckets) with branch/product splits.
- NPA movement report (opening, additions, upgrades, write-offs, closing).
- SMA monitoring (SMA-0/1/2) with trend charts.
- OTS pipeline and recovery effectiveness.
- Legal case status and expense tracking.
- Manual receipt posting register with UTR/payment mode/TDS details.
- Manual receipt exception report (unallocated, partial, duplicate reference, unidentified receipt, amount mismatch).
- Future bank credit matching exception report if bank statement import is enabled later.
- Demand vs receipt vs allocation reconciliation by loan account.

## Treasury, ALM, and Risk
- ALM structural liquidity statement by RBI buckets.
- ALM gap analysis and limit breach alerts.
- Borrowing position (outstanding, unutilized, cost of funds).
- Interest rate sensitivity (RSA/RSL) and NII impact.
- Exposure concentration (single borrower, group, sector).
- Portfolio risk summary and CRAR trend.
- Source-of-funds utilisation report linking borrowing pools to lending deployment.
- Upcoming borrower inflows vs borrowing repayments by date bucket.
- Spread/NII/NIM report by product, project, borrower, lender, and portfolio.
- Covenant compliance and borrowing repayment due report.

## Compliance and Governance
- Compliance tracker (due, completed, delayed) by regulator.
- Regulatory return status with penalties and extensions.
- Board/committee approval pending list.
- Audit trail access logs and sensitive data access reports.
- CRILC/large exposure reporting readiness report.
- RBI/NBFC layer-specific reporting checklist, once Sagarmala's applicable layer is confirmed.

## Finance Ancillary Modules
- Fixed asset register with depreciation schedules and disposals.
- TDS deduction summary by section with challan and return status.
- GST transaction register and ITC eligibility report.
- GSTR-1/3B/9 manual summaries and manually tracked GSTR-2B matching exceptions.
- Bank reconciliation (BRS) summary with unmatched items aging.
- Fixed deposit maturity and interest accrual report.

## HRIS and Payroll
- Headcount and attrition dashboard by unit and role.
- Attendance and late coming trends with regularization stats.
- Leave balance and utilization report.
- Payroll register with statutory deductions (PF/ESI/PT/TDS).
- Reimbursement claims pending and TAT report.

## Future Portals and Self-Service
- Future borrower portal usage and service request aging, if portal is enabled later.
- Future vendor invoice status, pending approvals, and payment advice, if portal is enabled later.
- Future employee ESS adoption metrics and ticket resolution TAT, if portal is enabled later.

## Inventory and Assets (Operational)
- Stock on hand, reorder alerts, and consumption trends.
- Issue/receipt register by department.

## Notifications and Communication
- Notification delivery summary (sent, failed, read).
- SLA compliance on reminders and escalations.

## Notes for Tailoring
- Align report frequencies to statutory and board schedules.
- Map report ownership to compliance, finance, treasury, and risk teams.
- Add client-specific KPIs (e.g., segment-level AUM, branch productivity).
