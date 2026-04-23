**SMFC Ltd**

Integrated ERP Solution

**TECHNICAL SPECIFICATION**

Phase 3: Loan Accounting & Management

Part 1: Loan Account, Disbursement & Schedules

*Developer Reference Document*

**Table of Contents**

1\. Module Overview

2\. Loan Account Master (TXN_LOAN_ACCOUNT)

3\. Tranche Management (TXN_LOAN_TRANCHE)

4\. Disbursement Module

4.1 Disbursement Request (TXN_DISBURSEMENT_REQUEST)

4.2 Disbursement Record (TXN_DISBURSEMENT)

5\. Repayment Schedules

5.1 Principal Schedule (TXN_PRINCIPAL_SCHEDULE)

5.2 Interest Schedule (TXN_INTEREST_SCHEDULE)

5.3 Schedule Generation Logic

6\. Interest Rate Management

6.1 Rate Reset (TXN_RATE_RESET)

6.2 Interest Computation

7\. Demand Generation

8\. Business Flows

9\. Business Rules

**1. Module Overview**

The Loan Accounting & Management System (LAMS) is the core module for managing the complete lifecycle of loan assets from disbursement through repayment to closure.

**1.1 Scope**

- Loan Account Creation: Create loan accounts from sanctioned applications

- Tranche Management: Handle multi-tranche disbursements

- Disbursement Processing: Financial concurrence and fund release

- Schedule Generation: Principal and interest repayment schedules

- Interest Management: Rate resets, accruals, and computation

- Demand Generation: Periodic demand notices to borrowers

- Receipt Processing: Record and apportion repayments

- Penal Interest: Compute and track delayed payment charges

**1.2 Data Model Overview**

TXN_LOAN_ACCOUNT (Master loan record)

\|\-- TXN_LOAN_TRANCHE (Multiple tranches)

\| \|\-- TXN_DISBURSEMENT_REQUEST

\| \|\-- TXN_DISBURSEMENT

\| \|\-- TXN_PRINCIPAL_SCHEDULE

\| \|\-- TXN_INTEREST_SCHEDULE

\|

\|\-- TXN_RATE_RESET (Interest rate changes)

\|\-- TXN_DEMAND (Demand notices)

\|\-- TXN_RECEIPT (Repayments)

\|\-- TXN_RECEIPT_ALLOCATION (Receipt apportionment)

\|\-- TXN_INTEREST_ACCRUAL (Period-end accruals)

\|\-- TXN_PENAL_INTEREST (Overdue charges)

\|\-- TXN_LOAN_BALANCE (Daily/periodic balances)

**2. Loan Account Master (TXN_LOAN_ACCOUNT)**

The primary loan record created from a sanctioned loan application.

**2.1 Table Definition**

  --------------------------- --------------- ---------- ------------- -------------------------------------------------------------
  **Column**                  **Type**        **Null**   **Default**   **Description**

  loan_account_id             BIGSERIAL       NO         Auto          Primary Key

  org_id                      BIGINT          NO         \-            FK to MST_ORGANIZATION

  loan_account_number         VARCHAR(30)     NO         \-            Unique loan account number

  sanction_id                 BIGINT          NO         \-            FK to TXN_LOAN_SANCTION

  application_id              BIGINT          NO         \-            FK to TXN_LOAN_APPLICATION

  entity_id                   BIGINT          NO         \-            FK to MST_ENTITY (Borrower)

  product_id                  BIGINT          NO         \-            FK to MST_LOAN_PRODUCT

  branch_id                   BIGINT          NO         \-            FK to MST_UNIT (Servicing branch)

  account_open_date           DATE            NO         \-            Account creation date

  sanctioned_amount           NUMERIC(18,2)   NO         \-            Total sanctioned amount

  disbursed_amount            NUMERIC(18,2)   NO         0             Total disbursed till date

  undisbursed_amount          NUMERIC(18,2)   NO         \-            Sanctioned - Disbursed

  principal_outstanding       NUMERIC(18,2)   NO         0             Principal O/S

  interest_outstanding        NUMERIC(18,2)   NO         0             Interest O/S

  penal_outstanding           NUMERIC(18,2)   NO         0             Penal interest O/S

  other_charges_outstanding   NUMERIC(18,2)   NO         0             Other charges O/S

  total_outstanding           NUMERIC(18,2)   NO         0             Total amount outstanding

  interest_type               VARCHAR(20)     NO         \-            FIXED, FLOATING

  base_rate_id                BIGINT          YES        \-            FK to MST_INTEREST_RATE

  current_base_rate           NUMERIC(5,2)    YES        \-            Current base rate value

  spread_bps                  INTEGER         NO         \-            Spread in basis points

  effective_rate              NUMERIC(5,2)    NO         \-            Current effective interest rate

  rate_reset_frequency        VARCHAR(20)     YES        \-            MONTHLY, QUARTERLY, HALF_YEARLY, YEARLY

  last_rate_reset_date        DATE            YES        \-            Last rate reset date

  next_rate_reset_date        DATE            YES        \-            Next rate reset date

  tenure_months               INTEGER         NO         \-            Total tenure in months

  moratorium_months           INTEGER         NO         0             Moratorium period

  moratorium_end_date         DATE            YES        \-            Moratorium end date

  repayment_start_date        DATE            YES        \-            First repayment due date

  maturity_date               DATE            NO         \-            Loan maturity date

  repayment_frequency         VARCHAR(20)     NO         \-            MONTHLY, QUARTERLY, HALF_YEARLY, YEARLY

  repayment_mode              VARCHAR(30)     NO         \-            EMI, STRUCTURED, BALLOON, BULLET

  day_count_convention        VARCHAR(20)     NO         ACT_365       ACT_360, ACT_365, 30_360

  interest_calc_method        VARCHAR(20)     NO         SIMPLE        SIMPLE, COMPOUND

  first_disbursement_date     DATE            YES        \-            First disbursement date

  last_disbursement_date      DATE            YES        \-            Last disbursement date

  last_repayment_date         DATE            YES        \-            Last repayment received date

  last_demand_date            DATE            YES        \-            Last demand generation date

  next_demand_date            DATE            YES        \-            Next demand due date

  dpd                         INTEGER         NO         0             Days Past Due

  max_dpd                     INTEGER         NO         0             Maximum DPD in last 12 months

  overdue_amount              NUMERIC(18,2)   NO         0             Total overdue amount

  overdue_since_date          DATE            YES        \-            Overdue start date

  asset_classification        VARCHAR(20)     NO         STANDARD      STANDARD, SMA_0, SMA_1, SMA_2, SUB_STANDARD, DOUBTFUL, LOSS

  classification_date         DATE            YES        \-            Classification date

  npa_date                    DATE            YES        \-            NPA recognition date

  provision_rate              NUMERIC(5,2)    NO         0             Provisioning rate %

  provision_amount            NUMERIC(18,2)   NO         0             Provision held

  prepayment_allowed          BOOLEAN         NO         TRUE          Prepayment permitted

  prepayment_penalty_pct      NUMERIC(5,2)    YES        \-            Prepayment penalty

  restructured                BOOLEAN         NO         FALSE         Ever restructured

  restructure_count           INTEGER         NO         0             Number of restructures

  last_restructure_date       DATE            YES        \-            Last restructure date

  written_off                 BOOLEAN         NO         FALSE         Written off flag

  write_off_date              DATE            YES        \-            Write-off date

  write_off_amount            NUMERIC(18,2)   YES        \-            Written off amount

  recovered_post_writeoff     NUMERIC(18,2)   NO         0             Recovery post write-off

  closure_date                DATE            YES        \-            Account closure date

  closure_type                VARCHAR(30)     YES        \-            NORMAL, PREPAID, SETTLED, WRITTEN_OFF

  noc_issued                  BOOLEAN         NO         FALSE         NOC issued

  noc_date                    DATE            YES        \-            NOC issue date

  relationship_manager_id     BIGINT          YES        \-            FK to MST_USER

  status                      VARCHAR(20)     NO         ACTIVE        ACTIVE, CLOSED, NPA, WRITTEN_OFF

  \+ Audit Columns                                                     Standard audit columns
  --------------------------- --------------- ---------- ------------- -------------------------------------------------------------

**2.2 Loan Account Number Format**

Format: SMFC/{PRODUCT}/{BRANCH}/{FY}/{SEQUENCE}

Example: SMFC/PTL/DEL/2025-26/L00001

Components:

SMFC - Organization prefix

PTL - Product code

DEL - Branch code

2025-26 - Financial year of account creation

L00001 - Sequence (L prefix for loan)

**2.3 Asset Classification**

  -------------------- ----------------- ----------------- -----------------------------
  **Classification**   **DPD Range**     **Provision %**   **Description**

  STANDARD             0 days            0.40%             Regular performing asset

  SMA_0                1-30 days         0.40%             Special Mention Account - 0

  SMA_1                31-60 days        0.40%             Special Mention Account - 1

  SMA_2                61-90 days        0.40%             Special Mention Account - 2

  SUB_STANDARD         91-365 days       15.00%            NPA - Sub-standard

  DOUBTFUL_1           366-730 days      25.00%            NPA - Doubtful 1 year

  DOUBTFUL_2           731-1095 days     40.00%            NPA - Doubtful 2 years

  DOUBTFUL_3           \> 1095 days      100.00%           NPA - Doubtful 3+ years

  LOSS                 Identified loss   100.00%           Loss asset
  -------------------- ----------------- ----------------- -----------------------------

**2.4 Indexes**

PRIMARY KEY (loan_account_id)

UNIQUE INDEX idx_loan_acc_number ON txn_loan_account(loan_account_number)

INDEX idx_loan_entity ON txn_loan_account(entity_id)

INDEX idx_loan_sanction ON txn_loan_account(sanction_id)

INDEX idx_loan_product ON txn_loan_account(product_id)

INDEX idx_loan_branch ON txn_loan_account(branch_id)

INDEX idx_loan_status ON txn_loan_account(status)

INDEX idx_loan_classification ON txn_loan_account(asset_classification)

INDEX idx_loan_maturity ON txn_loan_account(maturity_date)

INDEX idx_loan_dpd ON txn_loan_account(dpd) WHERE dpd \> 0

**3. Tranche Management (TXN_LOAN_TRANCHE)**

Supports multiple tranches/drawdowns under a single loan account with different rates and schedules.

**3.1 Table Definition**

  ------------------------- --------------- ---------- ------------- --------------------------------------------
  **Column**                **Type**        **Null**   **Default**   **Description**

  tranche_id                BIGSERIAL       NO         Auto          Primary Key

  loan_account_id           BIGINT          NO         \-            FK to TXN_LOAN_ACCOUNT

  tranche_number            INTEGER         NO         \-            Tranche sequence (1, 2, 3\...)

  tranche_reference         VARCHAR(30)     NO         \-            Tranche reference number

  sanctioned_amount         NUMERIC(18,2)   NO         \-            Tranche sanctioned amount

  disbursed_amount          NUMERIC(18,2)   NO         0             Amount disbursed

  undisbursed_amount        NUMERIC(18,2)   NO         \-            Pending disbursement

  principal_outstanding     NUMERIC(18,2)   NO         0             Principal O/S

  interest_outstanding      NUMERIC(18,2)   NO         0             Interest O/S

  effective_rate            NUMERIC(5,2)    NO         \-            Interest rate for tranche

  spread_bps                INTEGER         YES        \-            Tranche-specific spread

  disbursement_deadline     DATE            YES        \-            Last date to disburse

  first_disbursement_date   DATE            YES        \-            First disbursement

  last_disbursement_date    DATE            YES        \-            Last disbursement

  repayment_start_date      DATE            YES        \-            Repayment start

  maturity_date             DATE            YES        \-            Tranche maturity

  tenure_months             INTEGER         YES        \-            Tranche tenure

  moratorium_months         INTEGER         NO         0             Moratorium

  currency_id               BIGINT          NO         \-            FK to MST_CURRENCY

  purpose                   VARCHAR(500)    YES        \-            Tranche purpose

  linked_milestone_id       BIGINT          YES        \-            FK to TXN_PROJECT_MILESTONE

  status                    VARCHAR(20)     NO         ACTIVE        ACTIVE, FULLY_DISBURSED, CLOSED, CANCELLED

  \+ Audit Columns                                                   Standard audit columns
  ------------------------- --------------- ---------- ------------- --------------------------------------------

**3.2 Tranche Reference Format**

Format: {LOAN_ACCOUNT_NUMBER}/T{SEQUENCE}

Example: SMFC/PTL/DEL/2025-26/L00001/T1

SMFC/PTL/DEL/2025-26/L00001/T2

**4. Disbursement Module**

Handles disbursement requests, approvals, and fund release.

**4.1 Disbursement Request (TXN_DISBURSEMENT_REQUEST)**

Request initiated for releasing funds against sanctioned amount.

**4.1.1 Table Definition**

  -------------------------- --------------- ---------- ------------- ----------------------------------------------------------------------------
  **Column**                 **Type**        **Null**   **Default**   **Description**

  request_id                 BIGSERIAL       NO         Auto          Primary Key

  loan_account_id            BIGINT          NO         \-            FK to TXN_LOAN_ACCOUNT

  tranche_id                 BIGINT          NO         \-            FK to TXN_LOAN_TRANCHE

  request_number             VARCHAR(30)     NO         \-            Unique request number

  request_date               DATE            NO         \-            Request date

  requested_amount           NUMERIC(18,2)   NO         \-            Amount requested

  purpose                    TEXT            YES        \-            Purpose of disbursement

  beneficiary_type           VARCHAR(20)     NO         \-            BORROWER, VENDOR, ESCROW

  beneficiary_name           VARCHAR(200)    NO         \-            Payment beneficiary

  beneficiary_bank_id        BIGINT          YES        \-            FK to MST_ENTITY_BANK

  beneficiary_account        VARCHAR(30)     YES        \-            Account number

  beneficiary_ifsc           VARCHAR(11)     YES        \-            IFSC code

  payment_mode               VARCHAR(20)     NO         \-            RTGS, NEFT, DD

  milestone_id               BIGINT          YES        \-            FK to TXN_PROJECT_MILESTONE

  milestone_verified         BOOLEAN         NO         FALSE         Milestone completion verified

  conditions_verified        BOOLEAN         NO         FALSE         Pre-disb conditions cleared

  documents_verified         BOOLEAN         NO         FALSE         Required docs submitted

  equity_infusion_verified   BOOLEAN         NO         FALSE         Promoter equity verified

  requested_by               BIGINT          NO         \-            FK to MST_USER

  status                     VARCHAR(20)     NO         PENDING       PENDING, FC_PENDING, FC_APPROVED, APPROVED, DISBURSED, REJECTED, CANCELLED

  fc_user_id                 BIGINT          YES        \-            Financial concurrence by

  fc_date                    DATE            YES        \-            FC date

  fc_remarks                 VARCHAR(500)    YES        \-            FC remarks

  approved_amount            NUMERIC(18,2)   YES        \-            Approved amount

  approved_by                BIGINT          YES        \-            Final approver

  approved_date              DATE            YES        \-            Approval date

  rejection_reason           TEXT            YES        \-            If rejected

  disbursement_id            BIGINT          YES        \-            FK to TXN_DISBURSEMENT

  \+ Audit Columns                                                    Standard audit columns
  -------------------------- --------------- ---------- ------------- ----------------------------------------------------------------------------

**4.2 Disbursement Record (TXN_DISBURSEMENT)**

Actual disbursement transaction recording fund release.

**4.2.1 Table Definition**

  ---------------------- --------------- ---------- ------------- ------------------------------------------------------
  **Column**             **Type**        **Null**   **Default**   **Description**

  disbursement_id        BIGSERIAL       NO         Auto          Primary Key

  loan_account_id        BIGINT          NO         \-            FK to TXN_LOAN_ACCOUNT

  tranche_id             BIGINT          NO         \-            FK to TXN_LOAN_TRANCHE

  request_id             BIGINT          NO         \-            FK to TXN_DISBURSEMENT_REQUEST

  disbursement_number    VARCHAR(30)     NO         \-            Unique disbursement ref

  disbursement_date      DATE            NO         \-            Date of disbursement

  value_date             DATE            NO         \-            Value date for interest calc

  disbursement_amount    NUMERIC(18,2)   NO         \-            Amount disbursed

  currency_id            BIGINT          NO         \-            FK to MST_CURRENCY

  exchange_rate          NUMERIC(12,6)   NO         1             If foreign currency

  base_amount            NUMERIC(18,2)   NO         \-            Amount in base currency

  beneficiary_name       VARCHAR(200)    NO         \-            Payment beneficiary

  beneficiary_account    VARCHAR(30)     NO         \-            Account number

  beneficiary_ifsc       VARCHAR(11)     NO         \-            IFSC code

  beneficiary_bank       VARCHAR(200)    YES        \-            Bank name

  payment_mode           VARCHAR(20)     NO         \-            RTGS, NEFT, DD, INTERNAL

  payment_reference      VARCHAR(50)     YES        \-            UTR/Reference number

  payment_date           DATE            YES        \-            Actual payment date

  smfc_bank_account_id   BIGINT          NO         \-            FK to MST_BANK_ACCOUNT

  effective_rate         NUMERIC(5,2)    NO         \-            Interest rate at disbursement

  first_interest_date    DATE            YES        \-            First interest due date

  first_principal_date   DATE            YES        \-            First principal due date

  remarks                VARCHAR(500)    YES        \-            Disbursement remarks

  voucher_id             BIGINT          YES        \-            FK to TXN_VOUCHER

  status                 VARCHAR(20)     NO         INITIATED     INITIATED, PAYMENT_SENT, CONFIRMED, FAILED, REVERSED

  \+ Audit Columns                                                Standard audit columns
  ---------------------- --------------- ---------- ------------- ------------------------------------------------------

**4.2.2 Disbursement Accounting Entries**

  -------------------------- -------------- -------------- ------------------------
  **Account**                **Debit**      **Credit**     **Description**

  Loan Asset (Principal)     ₹ XX,XX,XXX    \-             Increase in loan asset

  Bank Account               \-             ₹ XX,XX,XXX    Fund outflow

  If Upfront Fee Deducted:                                 

  Fee Income                 \-             ₹ X,XXX        Fee recognition

  Loan Asset (adjusted)      ₹ (Fee)        \-             Net disbursement
  -------------------------- -------------- -------------- ------------------------

**5. Repayment Schedules**

System-generated principal and interest repayment schedules.

**5.1 Principal Schedule (TXN_PRINCIPAL_SCHEDULE)**

Principal repayment schedule with due dates and amounts.

**5.1.1 Table Definition**

  ----------------------- --------------- ---------- ------------- ---------------------------------------------------------------
  **Column**              **Type**        **Null**   **Default**   **Description**

  principal_schedule_id   BIGSERIAL       NO         Auto          Primary Key

  loan_account_id         BIGINT          NO         \-            FK to TXN_LOAN_ACCOUNT

  tranche_id              BIGINT          YES        \-            FK to TXN_LOAN_TRANCHE

  installment_number      INTEGER         NO         \-            Installment sequence

  due_date                DATE            NO         \-            Principal due date

  principal_amount        NUMERIC(18,2)   NO         \-            Principal due

  principal_paid          NUMERIC(18,2)   NO         0             Principal paid

  principal_waived        NUMERIC(18,2)   NO         0             Principal waived

  principal_outstanding   NUMERIC(18,2)   NO         \-            Principal pending

  opening_balance         NUMERIC(18,2)   NO         \-            O/S before this installment

  closing_balance         NUMERIC(18,2)   NO         \-            O/S after this installment

  payment_date            DATE            YES        \-            Actual payment date

  dpd                     INTEGER         NO         0             Days past due

  status                  VARCHAR(20)     NO         SCHEDULED     SCHEDULED, PARTIALLY_PAID, PAID, OVERDUE, WAIVED, RESCHEDULED

  demand_id               BIGINT          YES        \-            FK to TXN_DEMAND

  original_due_date       DATE            YES        \-            Original date if rescheduled

  reschedule_reason       VARCHAR(200)    YES        \-            Reason for reschedule

  \+ Audit Columns                                                 Standard audit columns
  ----------------------- --------------- ---------- ------------- ---------------------------------------------------------------

**5.2 Interest Schedule (TXN_INTEREST_SCHEDULE)**

Interest repayment schedule calculated based on outstanding principal.

**5.2.1 Table Definition**

  ------------------------- --------------- ---------- ------------- --------------------------------------------------
  **Column**                **Type**        **Null**   **Default**   **Description**

  interest_schedule_id      BIGSERIAL       NO         Auto          Primary Key

  loan_account_id           BIGINT          NO         \-            FK to TXN_LOAN_ACCOUNT

  tranche_id                BIGINT          YES        \-            FK to TXN_LOAN_TRANCHE

  installment_number        INTEGER         NO         \-            Installment sequence

  period_from               DATE            NO         \-            Interest period start

  period_to                 DATE            NO         \-            Interest period end

  due_date                  DATE            NO         \-            Interest due date

  days_in_period            INTEGER         NO         \-            Number of days

  principal_balance         NUMERIC(18,2)   NO         \-            Principal for calculation

  interest_rate             NUMERIC(5,2)    NO         \-            Rate applied

  interest_amount           NUMERIC(18,2)   NO         \-            Interest due

  interest_paid             NUMERIC(18,2)   NO         0             Interest paid

  interest_waived           NUMERIC(18,2)   NO         0             Interest waived

  interest_outstanding      NUMERIC(18,2)   NO         \-            Interest pending

  tds_deducted              NUMERIC(18,2)   NO         0             TDS on interest

  net_interest_receivable   NUMERIC(18,2)   NO         \-            Net of TDS

  payment_date              DATE            YES        \-            Actual payment date

  dpd                       INTEGER         NO         0             Days past due

  status                    VARCHAR(20)     NO         SCHEDULED     SCHEDULED, PARTIALLY_PAID, PAID, OVERDUE, WAIVED

  demand_id                 BIGINT          YES        \-            FK to TXN_DEMAND

  \+ Audit Columns                                                   Standard audit columns
  ------------------------- --------------- ---------- ------------- --------------------------------------------------

**5.3 Schedule Generation Logic**

Logic for generating principal and interest schedules based on repayment mode.

**5.3.1 Repayment Modes**

  ---------------- ---------------------- ------------------- ---------------------
  **Mode**         **Principal**          **Interest**        **Use Case**

  EMI              Increasing             Decreasing          Standard term loans

  STRUCTURED       As per structure       On outstanding      Project finance

  BALLOON          Small + Lump sum       On outstanding      Cash flow mismatch

  BULLET           100% at maturity       Periodic            Short-term loans

  MORATORIUM_EMI   EMI after moratorium   During moratorium   Infra projects
  ---------------- ---------------------- ------------------- ---------------------

**5.3.2 EMI Calculation**

EMI Formula:

EMI = P × r × (1 + r)\^n / ((1 + r)\^n - 1)

Where:

P = Principal amount

r = Monthly interest rate (Annual rate / 12 / 100)

n = Number of monthly installments

Example:

Principal = ₹10,00,00,000

Annual Rate = 12%

Tenure = 120 months

r = 12/12/100 = 0.01

EMI = 10,00,00,000 × 0.01 × (1.01)\^120 / ((1.01)\^120 - 1)

EMI = ₹14,34,709 per month

**5.3.3 Schedule Generation Algorithm**

FUNCTION generate_schedule(loan_account_id, disbursement_id):

\-- Get loan parameters

loan = GET_LOAN(loan_account_id)

principal = disbursement.amount

rate = loan.effective_rate

tenure = loan.tenure_months

moratorium = loan.moratorium_months

frequency = loan.repayment_frequency

mode = loan.repayment_mode

\-- Calculate dates

first_interest_date = add_months(disbursement.value_date, frequency_months)

first_principal_date = add_months(disbursement.value_date, moratorium + frequency_months)

\-- Generate interest schedule (from disbursement)

current_date = disbursement.value_date

FOR i = 1 TO total_interest_installments:

period_from = current_date

period_to = add_months(current_date, frequency_months) - 1

due_date = add_months(current_date, frequency_months)

days = date_diff(period_to, period_from) + 1

interest = principal_balance × rate / 100 × days / 365

INSERT INTO txn_interest_schedule(\...)

current_date = due_date

\-- Generate principal schedule (after moratorium)

IF mode = \'EMI\':

emi = calculate_emi(principal, rate, repayment_installments)

FOR each principal_due_date:

interest_component = balance × rate × days / 365

principal_component = emi - interest_component

INSERT INTO txn_principal_schedule(\...)

balance = balance - principal_component

**6. Interest Rate Management**

Management of floating rate resets and interest computation.

**6.1 Rate Reset (TXN_RATE_RESET)**

Records interest rate changes for floating rate loans.

**6.1.1 Table Definition**

  ---------------------- -------------- ---------- ------------- -------------------------------------
  **Column**             **Type**       **Null**   **Default**   **Description**

  reset_id               BIGSERIAL      NO         Auto          Primary Key

  loan_account_id        BIGINT         NO         \-            FK to TXN_LOAN_ACCOUNT

  reset_date             DATE           NO         \-            Rate reset date

  effective_from         DATE           NO         \-            New rate effective from

  old_base_rate          NUMERIC(5,2)   YES        \-            Previous base rate

  new_base_rate          NUMERIC(5,2)   NO         \-            New base rate

  spread_bps             INTEGER        NO         \-            Spread (unchanged)

  old_effective_rate     NUMERIC(5,2)   NO         \-            Previous effective rate

  new_effective_rate     NUMERIC(5,2)   NO         \-            New effective rate

  reset_type             VARCHAR(20)    NO         \-            AUTO, MANUAL, REPRICING

  trigger                VARCHAR(50)    YES        \-            BASE_RATE_CHANGE, SCHEDULE, REQUEST

  base_rate_ref_id       BIGINT         YES        \-            FK to MST_INTEREST_RATE

  schedule_regenerated   BOOLEAN        NO         FALSE         Schedules updated

  approved_by            BIGINT         YES        \-            FK to MST_USER

  remarks                VARCHAR(500)   YES        \-            Reset remarks

  \+ Audit Columns                                               Standard audit columns
  ---------------------- -------------- ---------- ------------- -------------------------------------

**6.1.2 Rate Reset Flow**

**Step 1: Trigger Detection** - System detects rate reset trigger

- Auto: Base rate changed in MST_INTEREST_RATE

- Schedule: next_rate_reset_date reached

- Manual: User-initiated repricing

**Step 2: Calculate New Rate** - Compute new effective rate

new_effective_rate = new_base_rate + (spread_bps / 100)

**Step 3: Record Reset** - Insert rate reset record

INSERT INTO txn_rate_reset (\...)

UPDATE txn_loan_account SET

current_base_rate = :new_base,

effective_rate = :new_effective,

last_rate_reset_date = :reset_date,

next_rate_reset_date = add_months(:reset_date, frequency)

**Step 4: Regenerate Schedules** - Update future interest schedules

- Recalculate interest for future periods

- Do NOT change past/current period schedules

**6.2 Interest Computation**

**6.2.1 Day Count Conventions**

  ---------------- ------------------ ------------------- ----------------------------------------------
  **Convention**   **Days in Year**   **Days in Month**   **Formula**

  ACT/365          365                Actual              Interest = P × R × Actual Days / 365

  ACT/360          360                Actual              Interest = P × R × Actual Days / 360

  30/360           360                30                  Interest = P × R × 30 / 360

  ACT/ACT          Actual             Actual              Interest = P × R × Actual Days / Actual Year
  ---------------- ------------------ ------------------- ----------------------------------------------

**6.2.2 Interest Accrual (TXN_INTEREST_ACCRUAL)**

Period-end interest accrual for accounting purposes.

  -------------------- --------------- ---------- ------------- ------------------------------
  **Column**           **Type**        **Null**   **Default**   **Description**

  accrual_id           BIGSERIAL       NO         Auto          Primary Key

  loan_account_id      BIGINT          NO         \-            FK to TXN_LOAN_ACCOUNT

  accrual_date         DATE            NO         \-            Accrual date (month-end)

  period_from          DATE            NO         \-            Accrual period start

  period_to            DATE            NO         \-            Accrual period end

  principal_balance    NUMERIC(18,2)   NO         \-            Principal for accrual

  interest_rate        NUMERIC(5,2)    NO         \-            Rate applied

  days                 INTEGER         NO         \-            Days in period

  accrued_interest     NUMERIC(18,2)   NO         \-            Interest accrued

  cumulative_accrual   NUMERIC(18,2)   NO         \-            Cumulative since last demand

  voucher_id           BIGINT          YES        \-            FK to TXN_VOUCHER

  reversed             BOOLEAN         NO         FALSE         Reversed on receipt/demand

  \+ Audit Columns                                              Standard audit columns
  -------------------- --------------- ---------- ------------- ------------------------------

**7. Demand Generation**

Periodic demand notices sent to borrowers for principal and interest.

**7.1 Demand Record (TXN_DEMAND)**

  -------------------- --------------- ---------- ------------- ------------------------------------------------
  **Column**           **Type**        **Null**   **Default**   **Description**

  demand_id            BIGSERIAL       NO         Auto          Primary Key

  loan_account_id      BIGINT          NO         \-            FK to TXN_LOAN_ACCOUNT

  demand_number        VARCHAR(30)     NO         \-            Unique demand number

  demand_date          DATE            NO         \-            Demand generation date

  demand_type          VARCHAR(20)     NO         \-            REGULAR, REMINDER, FINAL

  period_from          DATE            NO         \-            Demand period start

  period_to            DATE            NO         \-            Demand period end

  due_date             DATE            NO         \-            Payment due date

  principal_due        NUMERIC(18,2)   NO         0             Principal demand

  interest_due         NUMERIC(18,2)   NO         0             Interest demand

  penal_interest_due   NUMERIC(18,2)   NO         0             Penal interest

  other_charges        NUMERIC(18,2)   NO         0             Other charges

  total_demand         NUMERIC(18,2)   NO         \-            Total demand amount

  previous_overdue     NUMERIC(18,2)   NO         0             Brought forward overdue

  grand_total          NUMERIC(18,2)   NO         \-            Total payable

  principal_paid       NUMERIC(18,2)   NO         0             Principal received

  interest_paid        NUMERIC(18,2)   NO         0             Interest received

  penal_paid           NUMERIC(18,2)   NO         0             Penal paid

  total_paid           NUMERIC(18,2)   NO         0             Total paid

  balance_due          NUMERIC(18,2)   NO         \-            Balance outstanding

  sent_date            DATE            YES        \-            Demand sent date

  sent_via             VARCHAR(30)     YES        \-            EMAIL, POST, BOTH

  email_sent           BOOLEAN         NO         FALSE         Email sent flag

  letter_generated     BOOLEAN         NO         FALSE         Letter generated

  status               VARCHAR(20)     NO         GENERATED     GENERATED, SENT, PARTIALLY_PAID, PAID, OVERDUE

  \+ Audit Columns                                              Standard audit columns
  -------------------- --------------- ---------- ------------- ------------------------------------------------

**7.2 Demand Generation Flow**

**Step 1: Identify Due Accounts** - Query accounts with upcoming demands

SELECT \* FROM txn_loan_account

WHERE next_demand_date \<= CURRENT_DATE

AND status = \'ACTIVE\'

**Step 2: Calculate Demand Components** - Compute amounts due

- Principal: From txn_principal_schedule for due date

- Interest: From txn_interest_schedule for due date

- Penal: Calculate on overdue amounts

- Other charges: Any applicable fees

**Step 3: Generate Demand Notice** - Create demand record

INSERT INTO txn_demand (\...)

UPDATE txn_loan_account SET last_demand_date = :date, next_demand_date = :next

**Step 4: Send to Borrower** - Dispatch demand notice

- Generate PDF demand letter

- Send via email and/or post

- Log communication

**8. Business Flows**

**8.1 Loan Account Creation Flow**

**TRIGGER: Sanction accepted by borrower**

**Step 1: Validate Sanction** - Verify sanction is valid and accepted

- VALIDATE: sanction.status = \'ACCEPTED\'

- VALIDATE: sanction.validity_expiry_date \>= CURRENT_DATE

- VALIDATE: No existing loan account for this sanction

**Step 2: Create Loan Account** - Initialize loan account record

INSERT INTO txn_loan_account (

sanction_id, entity_id, product_id, branch_id,

sanctioned_amount, interest_type, effective_rate,

tenure_months, moratorium_months, repayment_frequency,

status = \'ACTIVE\'

)

- Generate loan_account_number

- Set maturity_date = account_open_date + tenure

- Set moratorium_end_date if applicable

**Step 3: Create Tranches** - Setup disbursement tranches

- If single tranche: Create one tranche = full amount

- If multiple: Create tranches per sanction structure

INSERT INTO txn_loan_tranche FOR EACH tranche

**Step 4: Link Securities** - Associate collateral from sanction

- Copy security details from sanction to loan

- Update security status to \'ACTIVE\'

**Step 5: Notify Stakeholders** - Send notifications

- Email borrower with loan account details

- Notify relationship manager

- Update portal access for borrower

**8.2 Disbursement Flow**

**TRIGGER: Disbursement request initiated**

**Step 1: Create Request** - Initiate disbursement request

- Select loan account and tranche

- Enter amount and beneficiary details

- Attach supporting documents

INSERT INTO txn_disbursement_request (status = \'PENDING\')

**Step 2: Verify Conditions** - Check pre-disbursement conditions

- Query pending conditions from TXN_SANCTION_CONDITION

- Verify each mandatory condition is COMPLIED or WAIVED

- Check milestone completion if linked

- Verify equity infusion proportionate to disbursement

IF any mandatory condition pending → Block disbursement

**Step 3: Financial Concurrence** - FC team review

- Route to FC officer

- Verify fund availability

- Check exposure limits

- Approve/Return/Reject

UPDATE txn_disbursement_request SET status = \'FC_APPROVED\', fc_date = :date

**Step 4: Final Approval** - Authority approval

- Route to sanctioning authority if amount \> threshold

- Verify all checks passed

- Approve disbursement

UPDATE txn_disbursement_request SET status = \'APPROVED\', approved_amount = :amt

**Step 5: Process Payment** - Execute fund transfer

INSERT INTO txn_disbursement (status = \'INITIATED\')

- Create payment instruction

- Push to banking platform (RTGS/NEFT)

- Await confirmation

UPDATE txn_disbursement SET status = \'PAYMENT_SENT\', payment_reference = :utr

**Step 6: Post-Disbursement Processing** - Update records

BEGIN TRANSACTION

\-- Update loan account

UPDATE txn_loan_account SET

disbursed_amount += :amount,

undisbursed_amount -= :amount,

principal_outstanding += :amount,

total_outstanding += :amount

\-- Update tranche

UPDATE txn_loan_tranche SET disbursed_amount += :amount

\-- Generate schedules

CALL generate_schedule(loan_account_id, disbursement_id)

\-- Create accounting entry

CALL create_disbursement_voucher(disbursement_id)

COMMIT

**9. Business Rules**

**9.1 Loan Account Rules**

  ------------- --------------------------- ----------------------------------- --------------- ------------------------
  **Rule ID**   **Rule**                    **Condition**                       **Action**      **Error Code**

  LA-001        One account per sanction    Sanction already has loan account   Block           ERR_DUPLICATE_ACCOUNT

  LA-002        Valid sanction              Sanction not accepted or expired    Block           ERR_INVALID_SANCTION

  LA-003        Entity active               Entity status = BLACKLISTED         Block           ERR_ENTITY_BLACKLISTED

  LA-004        Product active              Product status != ACTIVE            Block           ERR_PRODUCT_INACTIVE

  LA-005        Cannot close with balance   total_outstanding \> 0              Block closure   ERR_BALANCE_PENDING
  ------------- --------------------------- ----------------------------------- --------------- ------------------------

**9.2 Disbursement Rules**

  ------------- ------------------------- ------------------------------------------ ------------ ------------------------
  **Rule ID**   **Rule**                  **Condition**                              **Action**   **Error Code**

  DISB-001      Within sanctioned limit   disbursed + requested \> sanctioned        Block        ERR_EXCEEDS_SANCTION

  DISB-002      Conditions cleared        Pending mandatory pre-disb conditions      Block        ERR_CONDITIONS_PENDING

  DISB-003      Equity proportionate      equity_infused \< required for %disb       Block        ERR_EQUITY_SHORT

  DISB-004      Sanction valid            sanction expired                           Block        ERR_SANCTION_EXPIRED

  DISB-005      Account active            loan_account.status != ACTIVE              Block        ERR_ACCOUNT_INACTIVE

  DISB-006      No overdue                loan has overdue \> 90 days                Warn         WARN_OVERDUE_EXISTS

  DISB-007      Milestone verified        linked milestone not complete              Block        ERR_MILESTONE_PENDING

  DISB-008      Bank verified             beneficiary bank not penny-drop verified   Block        ERR_BANK_UNVERIFIED

  DISB-009      Duplicate check           Same request pending approval              Block        ERR_DUPLICATE_REQUEST
  ------------- ------------------------- ------------------------------------------ ------------ ------------------------

**9.3 Schedule Rules**

  ------------- ---------------------- -------------------------------------- ------------ -----------------------
  **Rule ID**   **Rule**               **Condition**                          **Action**   **Error Code**

  SCH-001       Sum equals disbursed   SUM(principal_schedule) != disbursed   Block        ERR_SCHEDULE_MISMATCH

  SCH-002       Dates in sequence      Installment dates not sequential       Block        ERR_DATE_SEQUENCE

  SCH-003       Within tenure          Last installment \> maturity_date      Block        ERR_EXCEEDS_TENURE

  SCH-004       Rate consistency       Schedule rate != loan effective rate   Warn         WARN_RATE_MISMATCH

  SCH-005       No past schedules      Cannot add schedule for past date      Block        ERR_PAST_DATE
  ------------- ---------------------- -------------------------------------- ------------ -----------------------

*\-\-- End of Phase 3 Part 1 \-\--*

Part 2 covers: Receipts, Repayment Processing, NPA Management, Legal Module
