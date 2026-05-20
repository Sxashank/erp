# SMFC ERP - Loan Lifecycle, Portal Users, and Interest Subvention User Guide

**Audience:** SMFCL operations, credit, treasury, finance, scheme administrators, borrower portal users, lender users, SMFCL reviewers, SMFCL approvers, and ministry viewers.

**Scope:** Corporate / institutional lending only. This guide does not cover individual retail loans. All steps assume the current manual-first rollout: users record applications, sanctions, drawdowns, disbursements, receipts, releases, and references manually. External bank, GSTN, payment, and government portal integrations are not required for this workflow.

---

## 1. Quick Navigation Map

### Admin Console

Use the admin console for master setup, loan processing, treasury borrowing, loan servicing, interest subvention administration, and portal user creation.

- Login: `/login`
- Dashboard: `/admin`
- Borrower entities: `Lending -> Entities/Borrowers`
- Loan applications: `Lending -> Applications`
- Loan sanctions: `Lending -> Sanctions`
- Loan accounts: `Lending -> Loan Accounts`
- Disbursement readiness: `Lending -> Disbursement Readiness`
- Disbursements: `Lending -> Disbursements`
- Receipts: `Lending -> Receipts`
- Funding sources: `Treasury & Borrowings -> Funding Sources / Lenders`
- Borrowings / loans taken by SMFCL: `Treasury & Borrowings -> Borrowing Facilities / Loans Taken`
- Borrowing-to-loan spread mapping: `Treasury & Borrowings -> Borrowing-to-Loan Mapping`
- Interest subvention enrollments: `Interest Subvention -> Enrollments`
- Interest subvention claims: `Interest Subvention -> Claims`
- Portal users: `Portals & Notifications -> Portal Users`
- Portal registrations: `Portals & Notifications -> Portal Registrations`
- Reports: `MIS & Reports`

### Scheme Portal

Use the scheme portal for borrower self-service, lender review, SMFCL review/approval queues, claim submission, and scheme-level reporting.

- Portal login: `/portal/login`
- Workbench: `/portal/workbench`
- Applications: `/portal/applications`
- Loans: `/portal/loans`
- Loan detail: `/portal/loans/:loanId`
- Claims: `/portal/claims`
- Reports: `/portal/reports`
- Documents: `/portal/documents`

### Grounding Status

This guide is grounded in the current platform implementation as follows:

- Admin portal user creation, update, entity linking, and invite generation are active.
- Portal login, workbench, applications, loans, loan detail, documents, claims, and reports are active.
- Admin lending entities, products, applications, sanctions, loan accounts, disbursements, receipts, treasury lenders, borrowings, source-of-funds mapping, and IIF claims/enrollments are active route areas.
- Claim CSV, XLSX, and PDF exports are active from admin and portal claim screens.
- Portal report CSV export is active.
- Portal document PDF generation and loan schedule CSV downloads are active.

---

## 2. Roles and Responsibilities

### Admin Console Users

- **System / tenant admin:** creates users, roles, masters, portal users, products, schemes, and access configuration.
- **Treasury user:** records funding sources, borrowing facilities, drawdowns, borrowing repayments, and source-of-funds mapping.
- **Credit / operations user:** creates borrower entities, loan applications, appraisals, sanctions, loan accounts, disbursements, and receipts.
- **Finance user:** validates accounting impact, vouchers, receipts, disbursements, and reports.
- **Scheme admin:** manages IIF / interest subvention schemes, categories, enrollments, claims, and release lifecycle.

### Scheme Portal Users

- **Borrower:** creates and tracks applications, uploads documents, creates subsidy claims, uploads claim documents, submits claims, downloads claim CSV / XLSX / PDF reports, and views reports.
- **Lender:** reviews/validates scheme applications where lender validation is part of the scheme workflow.
- **SMFCL reviewer:** reviews submitted applications and verifies submitted claims.
- **SMFCL approver:** approves scheme applications and initiates / marks subsidy release.
- **Ministry viewer:** monitors scheme-level application and claim reports.
- **Scheme admin:** can oversee all scheme queues and perform administration actions.

---

## 3. Minimum Master Data Required Before Starting

Before processing an end-to-end loan, confirm that these masters exist.

### Organization and Accounting

1. Go to `Settings -> Organization Setup`.
2. Confirm the SMFCL organization record is active.
3. Go to `Settings -> Financial Years`.
4. Confirm the active financial year exists.
5. Go to `Settings -> Chart of Accounts`, `Accounts`, and `Voucher Types`.
6. Confirm accounting masters are seeded and active.

### Loan Products

1. Go to `Settings -> Loan Products`.
2. Confirm the applicable product exists, for example:
   - Corporate Project Finance
   - Corporate Term Loan
   - Bridge Loan
3. Open the product and confirm:
   - Product name and code
   - Interest settings
   - Tenure limits
   - Repayment type
   - Fees and charges
   - Document checklist

### Interest Subvention Masters

1. Go to `Settings -> IIF Schemes`.
2. Confirm an active scheme exists.
3. Open the scheme and confirm:
   - Scheme code
   - Scheme name
   - Subvention rate
   - Claim frequency
   - Effective dates
   - Maximum subvention limits, if applicable
4. Go to `Settings -> IIF Categories`.
5. Confirm utilization categories are available for application fund-utilization split.

### Treasury Masters

1. Go to `Treasury & Borrowings -> Funding Sources / Lenders`.
2. Confirm the lender / funding institution exists.
3. Go to `Treasury & Borrowings -> Borrowing Facilities / Loans Taken`.
4. Create borrowing facilities before linking them to lending deployments if SMFCL funds the loan from external borrowing.

---

## 4. Create a Portal User End to End

Portal users are created from the admin console. Borrower users can log in with OTP after being linked to an institutional borrower entity. Internal users, such as lender, reviewer, approver, ministry, and scheme admin users, should be invited and activated with email/password.

### 4.1 Create or Confirm the Borrower Entity

1. Go to `Lending -> Entities/Borrowers`.
2. Click `New Entity`.
3. Enter the institutional borrower details:
   - Legal name
   - Entity type
   - Registration details
   - PAN / GSTIN, if available
   - Address
   - Contact details
   - Bank accounts
   - KYC documents
4. Save the entity.
5. Open the entity and verify that the contact, KYC, address, and bank-account tabs are complete.

### 4.2 Create a Borrower Portal User

1. Go to `Portals & Notifications -> Portal Users`.
2. Click `New portal user`.
3. In `Identity and access`, enter:
   - Display name
   - Mobile number
   - Email address, if available
   - Actor role: `Borrower`
   - Portal status: `Active`
   - Preferred language
4. In `Entity links`, select the borrower entity created in section 4.1.
5. Click `Create portal user`.

Expected result:

- The user appears in `Scheme Portal Users`.
- The `Linked entities` column shows at least one linked entity.
- The borrower can use the linked mobile number on `/portal/login`.

### 4.3 Borrower Login With OTP

1. Open `/portal/login`.
2. Select `Borrower OTP`.
3. Enter the authorised 10-digit mobile number.
4. Click `Send OTP`.
5. Enter the 6-digit OTP.
6. After successful login, the borrower lands on `/portal/workbench`.

### 4.4 Create an Internal Portal User

Use this for lender, SMFCL reviewer, SMFCL approver, ministry viewer, or scheme admin users.

1. Go to `Portals & Notifications -> Portal Users`.
2. Click `New portal user`.
3. Enter:
   - Display name
   - Mobile number
   - Email address
   - Actor role:
     - `Lender`
     - `SMFCL Reviewer`
     - `SMFCL Approver`
     - `Ministry Viewer`
     - `Scheme Admin`
   - Portal status: `Active`
4. Link borrower entities only if the user must be scoped to specific borrower records. Otherwise, leave entity links blank for tenant-wide queue access.
5. Click `Create portal user`.
6. Reopen the created user by clicking `Edit`.
7. In `Activation link`, click `Generate invite`.
8. Copy the activation URL and share it securely with the internal user.

### 4.5 Activate an Internal User Invite

1. Open the activation URL.
2. Set the password as instructed on the activation page.
3. Return to `/portal/login`.
4. Select `Internal user`.
5. Enter email and password.
6. If MFA is required, enter the OTP.
7. The user lands on `/portal/workbench`.

---

## 5. End-to-End Loan Process

The full process has two financial sides:

- **SMFCL borrowing side:** SMFCL takes funds from another bank / FI / lender at cost rate X.
- **SMFCL lending side:** SMFCL lends to an institutional borrower at X + margin.

The spread is visible when borrowing facilities are linked to loan deployments through source-of-funds mapping.

### 5.1 Record Funding Source / Lender

1. Go to `Treasury & Borrowings -> Funding Sources / Lenders`.
2. Click `New Lender`.
3. Enter:
   - Lender name
   - Lender type
   - Contact / branch details
   - Sanction limit, if applicable
   - Security / covenant details, if applicable
4. Save.

### 5.2 Record Borrowing Facility / Loan Taken by SMFCL

1. Go to `Treasury & Borrowings -> Borrowing Facilities / Loans Taken`.
2. Click `New Borrowing`.
3. Select the funding source / lender.
4. Enter:
   - Borrowing type
   - Sanction reference
   - Sanction date
   - Sanctioned amount
   - Interest rate / cost of funds
   - Rate type
   - Interest payment frequency
   - Principal payment frequency
   - Tenure and maturity details
   - Security / covenant notes
5. Save the borrowing facility.
6. Open the borrowing record and use the detail screen to record:
   - Drawdowns / tranches
   - Repayment schedule
   - Manual lender repayments

Expected result:

- Treasury can see sanctioned, drawn, outstanding, weighted cost of funds, maturity, and repayment status.

### 5.3 Create Borrower Loan Application

There are two supported routes.

#### Option A - Admin Console

1. Go to `Lending -> Applications`.
2. Click `New Application`.
3. Complete the application wizard:
   - Entity and product
   - Loan details
   - Project details
   - Security details
   - Documents
   - Fund utilization, if IIF / subvention scheme applies
   - Review
4. Submit / save the application.

#### Option B - Scheme Portal

1. Borrower logs in at `/portal/login`.
2. Go to `Applications`.
3. Click `New application`.
4. Select the linked borrower entity and product.
5. Enter project and funding details.
6. Complete `Funding & lenders`:
   - Project funding composition, such as equity share capital, promoter contribution, bank / FI term loan, NBFC term loan, government support, internal accruals, and other sources.
   - Tagged lender loan rows for each sanctioned facility, including lender name, facility type, loan amount, sanction reference/date, interest rate, EMI / repayment periodicity, loan account number, IFSC, security type, and disbursement call type.
   - Funding-source total should match project cost where project cost is provided.
   - Tagged lender loan total should match the requested loan amount.
7. Upload required documents.
8. Submit the application.

Expected result:

- The application appears in the admin console under `Lending -> Applications`.
- Portal users can track application status under `Portal -> Applications`.

### 5.4 Review Application and Issue Sanction

1. Go to `Lending -> Applications`.
2. Open the application.
3. Review borrower, product, project, security, documents, and fund utilization.
4. If required, complete appraisal and internal checks.
5. Go to `Lending -> Sanctions`.
6. Click `New Sanction` or open the application-linked sanction flow.
7. Enter:
   - Sanctioned amount
   - Interest rate / yield
   - Tenure
   - Repayment structure
   - Security / conditions
   - Pre-disbursement conditions
8. Save / approve the sanction.
9. Use `Sanction Letter` to download the sanction letter PDF where available.

Expected result:

- The borrower has a sanctioned facility.
- The system can proceed toward loan account creation and disbursement.

### 5.5 Create / Confirm Loan Account

1. Go to `Lending -> Loan Accounts`.
2. Confirm that a loan account exists for the sanctioned facility.
3. Open the account and verify:
   - Loan account number
   - Borrower
   - Product
   - Sanction reference
   - Principal amount
   - Interest rate
   - Repayment schedule
   - Outstanding amount
   - DPD / risk status

### 5.6 Link Borrowing Facility to Loan Deployment

This is the key step for showing SMFCL’s spread.

1. Go to `Treasury & Borrowings -> Borrowing-to-Loan Mapping`.
2. Select the borrowing source / drawdown.
3. Select the loan account or disbursement funded from that source.
4. Enter the mapped amount.
5. Add basis / notes, such as sanction committee reference or deployment basis.
6. Save.

Expected result:

- Management can see:
  - Cost of funds from the borrowing side
  - Lending yield from the loan side
  - Spread / NII / profitability by loan or portfolio
  - Unmapped drawdowns, if any

### 5.7 Process Disbursement Manually

1. Go to `Lending -> Disbursement Readiness`.
2. Review pre-disbursement conditions.
3. Go to `Lending -> Disbursements`.
4. Click `New Disbursement`.
5. Select loan account.
6. Enter:
   - Requested amount
   - Beneficiary details
   - Disbursement mode
   - Manual bank / reference details
   - Charges, if any
7. Submit for approval, if approval is required.
8. Open the disbursement and process it manually once funds are released.

Expected result:

- Loan outstanding is updated.
- Manual disbursement details are recorded.
- Accounting impact can be posted through the finance flow where configured.

### 5.8 Record Borrower Repayments / EMI / EPI Manually

1. Go to `Lending -> Receipts`.
2. Click `New Receipt`.
3. Select the loan account.
4. Enter:
   - Receipt date
   - Receipt amount
   - Payment mode
   - UTR / cheque / bank reference
   - Narration
5. Save the receipt.
6. Open the receipt allocation screen if allocation review is needed.
7. Allocate against:
   - Penal charges
   - Other charges
   - Overdue interest
   - Current interest
   - Overdue principal
   - Current principal

Expected result:

- The repayment is reflected in the loan account.
- DPD / overdue position is reduced as per allocation.
- Collections dashboard and reports update from recorded data.

### 5.9 Record SMFCL Repayment to Source Lender

1. Go to `Treasury & Borrowings -> Borrowing Facilities / Loans Taken`.
2. Open the borrowing facility.
3. Go to the repayment / payments section.
4. Record manual repayment to lender:
   - Payment date
   - Interest component
   - Principal component
   - Charges, if any
   - Bank reference / UTR
   - Notes
5. Save.

Expected result:

- Borrowing outstanding reduces.
- Lender obligations and ALM views reflect the updated payment.
- Management can compare borrower inflows against lender outflows.

---

## 6. Interest Subvention / IIF Process

Interest subvention starts after the loan account is active and eligible under an active scheme.

### 6.1 Confirm Scheme and Categories

1. Go to `Settings -> IIF Schemes`.
2. Confirm the scheme is active.
3. Confirm rate, claim frequency, effective dates, eligibility rules, required documents, workflow SLA rules, and fund rules.
4. Go to `Settings -> IIF Categories`.
5. Confirm utilization categories are active.

Default IIF configuration is aligned to the Ministry guideline:

- 3% per annum incentive.
- Term / CAPEX loan maximum tenure: 15 years.
- Working capital maximum tenure: 5 years.
- Scheme approval / start date: 24 September 2025.
- Scheme end date: 31 March 2036.
- Initial sanction eligibility window: 36 months.
- Claim frequency: quarterly, with half-yearly / yearly configurable if notified later.
- Stage-1 / NPA disqualification threshold: 30 DPD.
- Per-beneficiary cap: ₹1,000 crore.
- Scheme corpus: ₹5,000 crore.

The scheme remains configurable so future Ministry notifications can change rate, tenure, claim frequency, required documents, SLA days, eligibility evidence, and fund rules without changing the operational flow.

### 6.2 Capture Fund Utilization During Application

During application creation, use the `Fund Utilization` step to split the requested amount across scheme categories.

1. Complete the `Funding & lenders` step first so the application records the project funding composition and the lender loan facilities being tagged for IIF review.
2. Use `Fund Utilization` to split the requested loan amount across scheme categories.
3. Enter amount for each category.
4. Ensure total utilization equals the applicable requested amount.
5. Save and continue.

### 6.3 Enroll Loan Into Scheme

1. Go to `Interest Subvention -> Enrollments`.
2. Click `Enroll Loan`.
3. Select loan account.
4. Select scheme.
5. Click `Check eligibility`.
6. Review pass/fail checks.
7. Enter notes, if required.
8. Submit enrollment.
9. Approver reviews the enrollment and clicks approve.

Expected result:

- Enrollment status becomes `Enrolled`.
- The borrower can see eligible claim periods in the portal once periods are available.

### 6.4 Create Claim From Admin Console

1. Go to `Interest Subvention -> Claims`.
2. Click `New Claim`.
3. Select enrollment.
4. Enter claim period start and end.
5. Click `Compute`.
6. Review:
   - Period
   - Subvention rate
   - Interest paid in period
   - Calculation method
   - Eligible principal-day base
   - Applicable subvention amount
7. Enter notes, if any.
8. Click `Create draft claim`.
9. Open the claim.
10. Click `Submit for verification`.
11. Reviewer clicks `Mark verified`.
12. Approver clicks `Initiate release`.
13. Enter release instruction reference and notes.
14. After payment is released, click `Mark released`.
15. Enter release reference and released date.

### 6.5 Create Claim From Scheme Portal

1. Borrower or lender logs in at `/portal/login`.
2. Go to `Claims`.
3. Click `New claim`.
4. Select enrolled loan.
5. Select eligible period.
6. Click `Save draft`.
7. In the claim list, click `Edit draft`.
8. Upload the configured claim documents:
   - Interest calculation sheet
   - Borrower repayment record
   - Certificate of regular account status
   - Undertaking on non-duplication of claims
   - Audited interest certificate
   - Claim summary
9. Click `Submit`.

The claim then moves to reviewer and approver queues based on actor role.

### 6.6 Official IIF Guideline Coverage

The platform covers the official IIF operational requirements through configurable scheme rules:

| Guideline requirement | Platform coverage |
| --- | --- |
| Implementing agency is SMFCL | Captured in the IIF scheme master. |
| Shipyard located in India | Checked during enrollment through borrower / application evidence. |
| Eligible lender is Indian-regulated bank / FI / NBFC | Checked through lender evidence on the application. |
| Term / CAPEX and working capital loans | Configured as eligible loan types. |
| 15-year term loan cap and 5-year working capital cap | Configured and checked during enrollment. |
| Sanction after 24 September 2025 and within initial 3-year window | Configured and checked during enrollment. |
| Fresh / incremental / multiple eligible loans | Supported through separate enrollments per loan account. |
| Refinance, takeover, restructure, overdue or NPA exclusion | Checked at enrollment and re-checked at claim / release stages. |
| Incentive ceases beyond Stage-1 / 30 DPD or NPA | Enforced at claim creation, submission, verification, release initiation, and final release. |
| Quarterly release after EMI / interest realization | Claim periods are generated by configured frequency and interest paid is taken from recorded receipts. |
| 3% per annum incentive | Default calculation uses rate differential on principal-days, capped by actual interest paid. |
| Tranche-wise computation | Claim report computes tranche-wise eligible incentive from actual disbursement dates and amounts. |
| Lender documents and audited certificates | Submission is blocked until configured mandatory documents are uploaded. |
| Release to borrower loan account | Release workflow captures instruction and UTR / release reference. |
| Dedicated IIF fund account | Fund rules are configurable and each release records a scheme fund-ledger movement. |
| IA decision and release SLAs | 30-day decision and 7-day release SLA are scheme configuration fields. |
| MIS and monitoring | Portal reports show application, claim, borrower, lender, and release summaries. |

### 6.7 Verify and Release Claim From Portal

For SMFCL reviewer:

1. Login as `SMFCL Reviewer`.
2. Go to `Claims`.
3. Review submitted claims.
4. Click `Verify` or `Reject`.
5. If rejecting, enter reason.

For SMFCL approver:

1. Login as `SMFCL Approver`.
2. Go to `Claims`.
3. For verified claims, click `Initiate release`.
4. Enter release instruction reference and notes.
5. For release-in-progress claims, click `Mark released`.
6. Enter bank / release reference.

Expected result:

- Borrower sees the claim status.
- Portal reports and admin claim dashboard reflect the lifecycle.

---

## 7. Downloads and Exports

### 7.1 Interest Subvention Claim CSV, Excel, and PDF

Admin console:

1. Go to `Interest Subvention -> Claims`.
2. Open a claim.
3. Click `CSV report`, `XLSX report`, or `PDF report`.
4. The file downloads as `<claim-reference>.csv`, `<claim-reference>.xlsx`, or `<claim-reference>.pdf`.

Scheme portal:

1. Login to `/portal/login`.
2. Go to `Claims`.
3. Find the claim.
4. Click `CSV`, `XLSX`, or `PDF`.
5. The file downloads as `<claim-reference>.csv`, `<claim-reference>.xlsx`, or `<claim-reference>.pdf`.

Use CSV for interchange, XLSX for Excel-ready review, and PDF for print-ready / client-facing claim packs.

### 7.2 Scheme Portal Summary CSV

1. Login to `/portal/login`.
2. Go to `Reports`.
3. Click `Download CSV`.
4. The file downloads as `scheme-portal-report.csv`.

This report includes application funnel, claim funnel, borrower breakdown, lender breakdown, and recent releases based on the signed-in actor role.

### 7.3 Loan Schedule CSV

1. Login to `/portal/login`.
2. Go to `Loans`.
3. Open the required loan account.
4. Open the `EMI Schedule` tab.
5. Click `Download Schedule (CSV)`.
6. The file downloads as `loan_schedule_<loan-id>.csv`.

### 7.4 Portal Document and Certificate PDF Downloads

1. Login to `/portal/login`.
2. Go to `Documents`.
3. Use the document list to download available documents.
4. To generate PDFs:
   - Use statement generation for account statement PDF.
   - Use interest certificate generation for interest certificate PDF.
   - Use TDS certificate generation for TDS certificate PDF.

---

## 8. End-to-End UAT Script

Use this script to certify one complete workflow.

### Step 1 - Admin Setup

1. Login to `/login`.
2. Confirm financial year, loan product, IIF scheme, IIF categories, and accounting masters.
3. Create funding source under `Treasury & Borrowings -> Funding Sources / Lenders`.
4. Create borrowing facility under `Treasury & Borrowings -> Borrowing Facilities / Loans Taken`.

Pass criteria:

- Funding source exists.
- Borrowing facility has sanction amount and cost rate.

### Step 2 - Borrower and Portal User

1. Create borrower entity under `Lending -> Entities/Borrowers`.
2. Create borrower portal user under `Portals & Notifications -> Portal Users`.
3. Link portal user to borrower entity.

Pass criteria:

- Portal user shows the linked entity.
- Borrower can login with OTP.

### Step 3 - Application

1. Borrower logs into `/portal/login`.
2. Borrower creates a new application.
3. Borrower enters project funding composition and tagged lender loan details.
4. Borrower uploads required documents.
5. Borrower submits application.

Pass criteria:

- Application appears in admin `Lending -> Applications`.
- Portal application status is visible.
- Application detail shows `Project funding composition`, `Tagged lender loans`, and `Fund utilisation`.

### Step 4 - Sanction and Loan Account

1. Admin reviews application.
2. Admin creates sanction.
3. Admin confirms loan account.

Pass criteria:

- Loan account exists.
- Loan account shows sanctioned amount, rate, and schedule.

### Step 5 - Funding Link

1. Go to `Treasury & Borrowings -> Borrowing-to-Loan Mapping`.
2. Map borrowing drawdown to loan account / disbursement.

Pass criteria:

- Loan-level spread can be derived from borrowing cost and lending yield.
- Unmapped borrowing amount reduces.

### Step 6 - Disbursement

1. Go to `Lending -> Disbursement Readiness`.
2. Confirm conditions.
3. Create and process disbursement manually.

Pass criteria:

- Disbursement status is processed.
- Loan account outstanding updates.

### Step 7 - Receipt / EMI

1. Go to `Lending -> Receipts`.
2. Record manual borrower repayment.
3. Allocate receipt.

Pass criteria:

- Receipt is linked to loan.
- Loan outstanding / overdue reflects the payment.

### Step 8 - Lender Repayment

1. Open the borrowing facility.
2. Record manual repayment to lender.

Pass criteria:

- Borrowing outstanding updates.
- Treasury / ALM views reflect lender payment.

### Step 9 - Subvention Enrollment

1. Go to `Interest Subvention -> Enrollments`.
2. Enroll loan into active scheme.
3. Run eligibility check.
4. Approve enrollment.

Pass criteria:

- Enrollment status is `Enrolled`.
- Eligible periods appear when claim period conditions are met.

### Step 10 - Subvention Claim and Downloads

1. Borrower logs into `/portal/login`.
2. Borrower goes to `Claims`.
3. Borrower creates claim for eligible period.
4. Borrower uploads supporting documents.
5. Borrower submits claim.
6. Reviewer verifies claim.
7. Approver initiates release.
8. Approver marks claim released.
9. Borrower or admin downloads claim CSV, XLSX, and PDF.
10. Borrower downloads reports CSV from `Reports`.
11. Borrower downloads available statement / interest certificate PDFs from `Documents`.

Pass criteria:

- Claim lifecycle reaches `Released`.
- Claim CSV, XLSX, and PDF downloads.
- Portal reports CSV downloads.
- Available document PDFs download.

---

## 9. Common Issues and Checks

### Portal User Cannot Login

Check:

- Portal user status is `Active`.
- Mobile number is correct for borrower OTP login.
- Email is present for internal-user password login.
- Internal user has activated the invite URL.
- Borrower user is linked to at least one institutional entity.

### Borrower Cannot Create Claim

Check:

- Loan account is active.
- Loan is enrolled in an active subvention scheme.
- Enrollment status is `Enrolled`.
- A claimable period exists and has not already been claimed.
- Required claim documents are uploaded before submit.

### New Claim Button Is Disabled

Usually this means no eligible unclaimed period exists. Confirm:

- The enrolled loan has an eligible period.
- The period is closed.
- A claim for that period has not already been created.
- Interest paid in the period is recorded.

### Claim Submit Button Is Disabled

Check:

- Claim status is `Draft`.
- At least one supporting document is uploaded.

### CSV Opens Incorrectly in Excel

Use Excel import:

1. Open Excel.
2. Choose `Data -> From Text/CSV`.
3. Select downloaded CSV.
4. Confirm delimiter as comma.
5. Load.

## 10. Recommended Client Demo Flow

Use this sequence in demos because it explains the NBFC model clearly.

1. Show `Treasury & Borrowings -> Borrowing Facilities / Loans Taken`.
2. Explain SMFCL borrows funds at cost rate X.
3. Show `Lending -> Loan Accounts`.
4. Explain SMFCL lends to institutional borrowers at X + margin.
5. Show `Borrowing-to-Loan Mapping`.
6. Explain spread / NII visibility.
7. Show `Lending -> Receipts`.
8. Explain borrower repayment is recorded manually today.
9. Show borrowing repayment under treasury.
10. Explain lender repayment is recorded manually today.
11. Show `Interest Subvention -> Enrollments`.
12. Show `Interest Subvention -> Claims`.
13. Login to portal as borrower.
14. Show `Applications`, `Loans`, `Claims`, `Reports`, and `Documents`.
15. Download claim CSV, XLSX, PDF, and portal report CSV.
16. Show `Documents` and download available PDF statement / interest certificate.

This gives the client the full picture: funding, lending, repayment, subvention, portal self-service, and MIS/reporting.
