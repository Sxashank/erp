# SFC ERP Client Deck Outline

Prepared for SFC (NBFC)

Implementation roadmap: `refdocs/SFC_ERP_Implementation_Roadmap.md`

## Slide 1: Title
- SFC ERP: Integrated NBFC Platform
- Subtitle: Manual Operations, Capabilities, and Analytics
- Date and presenter

## Slide 2: Executive Summary
- End-to-end coverage from onboarding to collections and compliance.
- Single source of truth with audit-grade controls.
- Manual-first ERP controls to improve service and productivity without relying on live integrations.
- Corporate/project lending focus for maritime infrastructure, not retail individual loan disbursement.

## Slide 3: Business Outcomes
- Faster lending cycle with reduced manual handoffs.
- Stronger compliance with structured tracking, reminders, and audit trail.
- Improved management visibility via dashboards and MIS.

## Slide 4: End-to-End Process Map
- Resource mobilisation -> borrower onboarding -> appraisal -> sanction -> tranche disbursement -> demand -> receipt allocation -> borrowing repayment -> ALM/risk -> closure.
- Parallel management tracks: source of funds, profitability/spread, compliance, risk, and treasury liquidity.

## Slide 5: Module Coverage (At a Glance)
- Masters + GL
- Lending + LOS
- LAMS + Collections/NPA/Legal
- Treasury + ALM + Risk
- Finance ancillary (FA, TDS, GST, BRS, FD)
- HRIS + Payroll
- Compliance, DMS, Notifications
- Portals (Borrower, Vendor, Employee)

## Slide 6: Lending and Credit (Deep Dive)
- Entity master, KYC/CKYC, credit rating.
- Application, appraisal, sanction workflows.
- Sanction terms and condition tracking.
- Project finance controls: DSCR, escrow/source-of-repayment, security cover, milestone readiness, and promoter contribution.

## Slide 7: Loan Servicing and Collections
- Tranche disbursements, structured schedules, rate resets, and moratorium tracking.
- Interest demand generation, manual receipt posting, allocation waterfall, and outstanding balance updates.
- Current workflow: manual receipt entry, UTR/reference capture, partial payment handling, and allocation review.
- Future automation: bank statement import, UTR/reference matching, and exception queue.

## Slide 8: Treasury, ALM, and Risk
- Borrowings management and cost of funds.
- ALM buckets, gaps, and early warnings.
- Exposure monitoring and CRAR trends.
- Source-of-funds utilisation, spread/NII/NIM, and borrower inflows vs lender outflows.

## Slide 9: Finance, Accounting, and Reconciliation
- Accounting for borrowing drawdown, loan disbursement, interest income, interest expense, receipt allocation, and borrowing repayment.
- Manual BRS observations and future bank statement import/loan-level receipt matching.
- Fixed assets, TDS, GST, FD tracking, GST returns, and ITC reconciliation.

## Slide 10: Compliance and Governance
- RBI/MCA/GST/IT compliance calendar.
- Maker-checker approvals and audit trail.
- Document versioning and secure access.

## Slide 11: Portals and Self-Service
- Future borrower portal: schedules, statements, payments, requests.
- Future vendor portal: invoices, payment status, TDS certificates.
- Future employee portal: attendance, leave, payroll, claims.

## Slide 12: Analytics and MIS
- Executive KPIs (AUM, NPA, CRAR, NIM).
- Standard MIS: ALM, NPA movement, compliance tracker.
- Scheduled reports with PDF/Excel delivery.
- Lifecycle cockpits: loan pipeline, disbursement readiness, collections, treasury funding, ALM, profitability, and risk.

## Slide 13: Future Automation Landscape
- No live bank, GST, MCA, credit bureau, payment gateway, NACH, or portal integrations in current scope.
- Current scope is manual entry, maker-checker, audit trail, dashboards, and reports.
- Future roadmap can add integrations after business process stabilization.

## Slide 14: Security and Controls
- Role-based access and maker-checker controls.
- Future portal access can use MFA if portals are enabled.
- Audit logs for all critical actions.
- Future API logging and monitoring when integrations are enabled.

## Slide 15: Implementation Approach
- Phased rollout by module or business function.
- Data migration and parallel run approach.
- Training and change management.

## Slide 16: Next Steps
- Confirm scope and priorities.
- Validate manual workflows and report requirements.
- Keep integrations as future roadmap items until approved.
- Finalize timeline and resourcing.
