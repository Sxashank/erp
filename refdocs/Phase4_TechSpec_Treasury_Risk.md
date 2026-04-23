**SMFC Ltd**

Integrated ERP Solution

**TECHNICAL SPECIFICATION**

Phase 4: Treasury & Risk Management

Payable Loans, ALM, Credit Risk

**Table of Contents**

1\. Payable Loan Control System (Borrowings)

2\. Asset-Liability Management (ALM)

3\. Credit Risk Management

4\. Business Flows

5\. Business Rules

**1. Payable Loan Control System (Borrowings)**

Management of SMFC\'s own borrowings from banks, financial institutions, and bond issuances.

**1.1 Borrowing Master (MST_LENDER)**

Master data for lending institutions/agencies.

  -------------------- -------------- ---------- ------------- -----------------------------------------
  **Column**           **Type**       **Null**   **Default**   **Description**

  lender_id            BIGSERIAL      NO         Auto          Primary Key

  org_id               BIGINT         NO         \-            FK to MST_ORGANIZATION

  lender_code          VARCHAR(20)    NO         \-            Unique lender code

  lender_name          VARCHAR(200)   NO         \-            Lender name

  lender_type          VARCHAR(30)    NO         \-            BANK, DFI, BOND, ECB, GOI, MULTILATERAL

  short_name           VARCHAR(50)    YES        \-            Short name

  pan                  VARCHAR(10)    YES        \-            PAN

  tan                  VARCHAR(10)    YES        \-            TAN

  gstin                VARCHAR(15)    YES        \-            GSTIN

  address              TEXT           YES        \-            Address

  contact_person       VARCHAR(200)   YES        \-            Primary contact

  contact_email        VARCHAR(255)   YES        \-            Contact email

  contact_phone        VARCHAR(20)    YES        \-            Contact phone

  relationship_since   DATE           YES        \-            Relationship start

  status               VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                             Standard audit columns
  -------------------- -------------- ---------- ------------- -----------------------------------------

**1.2 Borrowing Account (TXN_BORROWING)**

SMFC\'s borrowing/liability accounts.

  ------------------------ --------------- ---------- ------------- -------------------------------------------------
  **Column**               **Type**        **Null**   **Default**   **Description**

  borrowing_id             BIGSERIAL       NO         Auto          Primary Key

  org_id                   BIGINT          NO         \-            FK to MST_ORGANIZATION

  borrowing_number         VARCHAR(30)     NO         \-            Unique borrowing reference

  lender_id                BIGINT          NO         \-            FK to MST_LENDER

  borrowing_type           VARCHAR(30)     NO         \-            TERM_LOAN, CC, OD, BOND, NCD, CP, ECB, GOI_LOAN

  sanction_date            DATE            NO         \-            Sanction/Issue date

  sanction_amount          NUMERIC(18,2)   NO         \-            Sanctioned amount

  drawn_amount             NUMERIC(18,2)   NO         0             Amount drawn/utilized

  undrawn_amount           NUMERIC(18,2)   NO         \-            Available limit

  principal_outstanding    NUMERIC(18,2)   NO         0             Principal O/S

  interest_accrued         NUMERIC(18,2)   NO         0             Interest accrued

  total_outstanding        NUMERIC(18,2)   NO         0             Total liability

  currency_id              BIGINT          NO         \-            FK to MST_CURRENCY

  interest_type            VARCHAR(20)     NO         \-            FIXED, FLOATING

  base_rate_type           VARCHAR(30)     YES        \-            MCLR, REPO, TBILL, FIXED

  base_rate_value          NUMERIC(5,2)    YES        \-            Base rate value

  spread_bps               INTEGER         YES        \-            Spread in bps

  effective_rate           NUMERIC(5,2)    NO         \-            Effective interest rate

  coupon_rate              NUMERIC(5,2)    YES        \-            For bonds/NCDs

  rate_reset_frequency     VARCHAR(20)     YES        \-            Rate reset frequency

  last_reset_date          DATE            YES        \-            Last rate reset

  next_reset_date          DATE            YES        \-            Next rate reset

  tenure_months            INTEGER         NO         \-            Total tenure

  moratorium_months        INTEGER         NO         0             Moratorium period

  first_drawdown_date      DATE            YES        \-            First utilization

  last_drawdown_date       DATE            YES        \-            Last utilization

  maturity_date            DATE            NO         \-            Maturity date

  repayment_frequency      VARCHAR(20)     NO         \-            MONTHLY, QUARTERLY, etc.

  repayment_mode           VARCHAR(30)     NO         \-            EMI, BULLET, STRUCTURED

  next_payment_date        DATE            YES        \-            Next payment due

  last_payment_date        DATE            YES        \-            Last payment made

  prepayment_allowed       BOOLEAN         NO         TRUE          Prepayment permitted

  prepayment_penalty_pct   NUMERIC(5,2)    YES        \-            Prepayment penalty

  security_details         TEXT            YES        \-            Security provided

  covenant_details         JSONB           YES        \-            Financial covenants

  gl_account_id            BIGINT          YES        \-            FK to MST_COA

  status                   VARCHAR(20)     NO         ACTIVE        ACTIVE, CLOSED, PREPAID

  closure_date             DATE            YES        \-            Closure date

  \+ Audit Columns                                                  Standard audit columns
  ------------------------ --------------- ---------- ------------- -------------------------------------------------

**1.3 Borrowing Tranches (TXN_BORROWING_TRANCHE)**

  ------------------ --------------- ---------- ------------- -----------------------------
  **Column**         **Type**        **Null**   **Default**   **Description**

  tranche_id         BIGSERIAL       NO         Auto          Primary Key

  borrowing_id       BIGINT          NO         \-            FK to TXN_BORROWING

  tranche_number     INTEGER         NO         \-            Tranche sequence

  tranche_amount     NUMERIC(18,2)   NO         \-            Tranche amount

  drawn_amount       NUMERIC(18,2)   NO         0             Amount drawn

  drawdown_date      DATE            YES        \-            Drawdown date

  maturity_date      DATE            YES        \-            Tranche maturity

  effective_rate     NUMERIC(5,2)    NO         \-            Interest rate

  status             VARCHAR(20)     NO         ACTIVE        ACTIVE, MATURED, PREPAID

  \+ Audit Columns                                            Standard audit columns
  ------------------ --------------- ---------- ------------- -----------------------------

**1.4 Borrowing Schedule (TXN_BORROWING_SCHEDULE)**

Principal and interest payment schedules for borrowings.

  -------------------- --------------- ---------- ------------- ------------------------------
  **Column**           **Type**        **Null**   **Default**   **Description**

  schedule_id          BIGSERIAL       NO         Auto          Primary Key

  borrowing_id         BIGINT          NO         \-            FK to TXN_BORROWING

  tranche_id           BIGINT          YES        \-            FK to TXN_BORROWING_TRANCHE

  installment_number   INTEGER         NO         \-            Installment sequence

  due_date             DATE            NO         \-            Payment due date

  component_type       VARCHAR(20)     NO         \-            PRINCIPAL, INTEREST

  due_amount           NUMERIC(18,2)   NO         \-            Amount due

  paid_amount          NUMERIC(18,2)   NO         0             Amount paid

  outstanding_amount   NUMERIC(18,2)   NO         \-            Amount pending

  payment_date         DATE            YES        \-            Actual payment date

  payment_reference    VARCHAR(50)     YES        \-            Payment reference

  voucher_id           BIGINT          YES        \-            FK to TXN_VOUCHER

  status               VARCHAR(20)     NO         SCHEDULED     SCHEDULED, PAID, OVERDUE

  \+ Audit Columns                                              Standard audit columns
  -------------------- --------------- ---------- ------------- ------------------------------

**1.5 Borrowing Types**

  ----------- ------------ -------------------- -------------------- ------------------------------------
  **Type**    **Source**   **Tenure**           **Rate Type**        **Characteristics**

  TERM_LOAN   Banks/FIs    3-10 years           MCLR+Spread          EMI/Structured repayment

  CC          Banks        1 year (renewable)   MCLR+Spread          Revolving, interest on utilization

  OD          Banks        1 year (renewable)   MCLR+Spread          Against FD/Securities

  NCD         Market       3-10 years           Fixed Coupon         Listed, debenture trustees

  BOND        Market       5-15 years           Fixed Coupon         Infrastructure bonds

  CP          Market       \< 1 year            Discount             Short-term working capital

  ECB         Foreign      3-7 years            SOFR+Spread          Foreign currency, hedging required

  GOI_LOAN    Government   10-25 years          Fixed/Concessional   Budget allocation
  ----------- ------------ -------------------- -------------------- ------------------------------------

**2. Asset-Liability Management (ALM)**

Management of maturity mismatches, liquidity risk, and interest rate risk.

**2.1 ALM Position (TXN_ALM_POSITION)**

Periodic ALM position capturing assets and liabilities by maturity bucket.

  ------------------- --------------- ---------- ------------- ------------------------------
  **Column**          **Type**        **Null**   **Default**   **Description**

  position_id         BIGSERIAL       NO         Auto          Primary Key

  org_id              BIGINT          NO         \-            FK to MST_ORGANIZATION

  position_date       DATE            NO         \-            Position as of date

  bucket_code         VARCHAR(20)     NO         \-            Time bucket code

  bucket_name         VARCHAR(50)     NO         \-            Bucket description

  bucket_days_from    INTEGER         NO         \-            Days from (lower bound)

  bucket_days_to      INTEGER         YES        \-            Days to (upper bound)

  total_assets        NUMERIC(18,2)   NO         0             Total assets in bucket

  total_liabilities   NUMERIC(18,2)   NO         0             Total liabilities in bucket

  gap                 NUMERIC(18,2)   NO         0             Assets - Liabilities

  cumulative_gap      NUMERIC(18,2)   NO         0             Cumulative gap

  gap_to_assets_pct   NUMERIC(5,2)    YES        \-            Gap as % of assets

  asset_details       JSONB           YES        \-            Breakdown of assets

  liability_details   JSONB           YES        \-            Breakdown of liabilities

  status              VARCHAR(20)     NO         DRAFT         DRAFT, FINAL

  \+ Audit Columns                                             Standard audit columns
  ------------------- --------------- ---------- ------------- ------------------------------

**2.2 Standard ALM Buckets (RBI Guidelines)**

  -------------- --------------- ------------- -------------------------------
  **Bucket**     **Days From**   **Days To**   **Description**

  DAY_1          1               1             Day 1 (Call money)

  2_7_DAYS       2               7             2-7 days

  8_14_DAYS      8               14            8-14 days

  15_28_DAYS     15              28            15 days to 1 month

  1_2_MONTHS     29              60            Over 1 month to 2 months

  2_3_MONTHS     61              90            Over 2 months to 3 months

  3_6_MONTHS     91              180           Over 3 months to 6 months

  6_12_MONTHS    181             365           Over 6 months to 1 year

  1_3_YEARS      366             1095          Over 1 year to 3 years

  3_5_YEARS      1096            1825          Over 3 years to 5 years

  OVER_5_YEARS   1826            NULL          Over 5 years
  -------------- --------------- ------------- -------------------------------

**2.3 ALM Asset Mapping (TXN_ALM_ASSET)**

  ------------------ --------------- ---------- ------------- -----------------------------------
  **Column**         **Type**        **Null**   **Default**   **Description**

  asset_map_id       BIGSERIAL       NO         Auto          Primary Key

  position_id        BIGINT          NO         \-            FK to TXN_ALM_POSITION

  asset_type         VARCHAR(30)     NO         \-            LOAN, INVESTMENT, FD, CASH, OTHER

  asset_subtype      VARCHAR(50)     YES        \-            Further classification

  reference_id       BIGINT          YES        \-            FK to source table

  reference_type     VARCHAR(50)     YES        \-            Source table name

  bucket_code        VARCHAR(20)     NO         \-            Time bucket

  principal_amount   NUMERIC(18,2)   NO         \-            Principal maturing

  interest_amount    NUMERIC(18,2)   NO         0             Interest receivable

  total_amount       NUMERIC(18,2)   NO         \-            Total inflow

  rate_sensitive     BOOLEAN         NO         TRUE          Rate sensitive asset

  floating_rate      BOOLEAN         NO         FALSE         Floating rate asset

  \+ Audit Columns                                            Standard audit columns
  ------------------ --------------- ---------- ------------- -----------------------------------

**2.4 ALM Liability Mapping (TXN_ALM_LIABILITY)**

  ------------------- --------------- ---------- ------------- ---------------------------------
  **Column**          **Type**        **Null**   **Default**   **Description**

  liability_map_id    BIGSERIAL       NO         Auto          Primary Key

  position_id         BIGINT          NO         \-            FK to TXN_ALM_POSITION

  liability_type      VARCHAR(30)     NO         \-            BORROWING, BOND, DEPOSIT, OTHER

  liability_subtype   VARCHAR(50)     YES        \-            Further classification

  reference_id        BIGINT          YES        \-            FK to source table

  reference_type      VARCHAR(50)     YES        \-            Source table name

  bucket_code         VARCHAR(20)     NO         \-            Time bucket

  principal_amount    NUMERIC(18,2)   NO         \-            Principal maturing

  interest_amount     NUMERIC(18,2)   NO         0             Interest payable

  total_amount        NUMERIC(18,2)   NO         \-            Total outflow

  rate_sensitive      BOOLEAN         NO         TRUE          Rate sensitive liability

  floating_rate       BOOLEAN         NO         FALSE         Floating rate liability

  \+ Audit Columns                                             Standard audit columns
  ------------------- --------------- ---------- ------------- ---------------------------------

**2.5 Interest Rate Sensitivity (TXN_IRS_ANALYSIS)**

Interest Rate Sensitivity analysis for rate risk management.

  ------------------ --------------- ---------- ------------- ------------------------------
  **Column**         **Type**        **Null**   **Default**   **Description**

  irs_id             BIGSERIAL       NO         Auto          Primary Key

  org_id             BIGINT          NO         \-            FK to MST_ORGANIZATION

  analysis_date      DATE            NO         \-            Analysis date

  bucket_code        VARCHAR(20)     NO         \-            Time bucket

  rsa_amount         NUMERIC(18,2)   NO         0             Rate Sensitive Assets

  rsl_amount         NUMERIC(18,2)   NO         0             Rate Sensitive Liabilities

  gap                NUMERIC(18,2)   NO         0             RSA - RSL

  cumulative_gap     NUMERIC(18,2)   NO         0             Cumulative gap

  rate_change_bps    INTEGER         YES        100           Rate shock (bps)

  nii_impact         NUMERIC(18,2)   YES        \-            NII impact for rate shock

  \+ Audit Columns                                            Standard audit columns
  ------------------ --------------- ---------- ------------- ------------------------------

**2.6 ALM Generation Flow**

**Step 1: Extract Loan Assets** - Get all loan accounts with schedules

FOR each loan_account WHERE status = \'ACTIVE\':

FOR each future schedule (principal + interest):

bucket = determine_bucket(schedule.due_date - position_date)

INSERT INTO txn_alm_asset (asset_type=\'LOAN\', bucket, amount)

**Step 2: Extract Borrowing Liabilities** - Get all borrowings with schedules

FOR each borrowing WHERE status = \'ACTIVE\':

FOR each future schedule:

bucket = determine_bucket(schedule.due_date - position_date)

INSERT INTO txn_alm_liability (liability_type=\'BORROWING\', bucket, amount)

**Step 3: Add Other Assets/Liabilities** - Include investments, FDs, etc.

- Fixed Deposits (both placed and received)

- Investments with maturity

- Bonds payable

**Step 4: Compute Gap** - Calculate liquidity gaps

FOR each bucket:

gap = SUM(assets) - SUM(liabilities)

cumulative_gap = previous_cumulative + gap

INSERT INTO txn_alm_position (bucket, assets, liabilities, gap, cumulative_gap)

**3. Credit Risk Management**

Portfolio-level credit risk monitoring and reporting.

**3.1 Exposure Limits (MST_EXPOSURE_LIMIT)**

  ----------------------- --------------- ---------- ------------- ---------------------------------------------------
  **Column**              **Type**        **Null**   **Default**   **Description**

  limit_id                BIGSERIAL       NO         Auto          Primary Key

  org_id                  BIGINT          NO         \-            FK to MST_ORGANIZATION

  limit_type              VARCHAR(30)     NO         \-            SINGLE_BORROWER, GROUP, SECTOR, RATING, GEOGRAPHY

  limit_code              VARCHAR(50)     NO         \-            Limit identifier

  limit_name              VARCHAR(200)    NO         \-            Limit description

  limit_value             NUMERIC(18,2)   YES        \-            Absolute limit amount

  limit_pct               NUMERIC(5,2)    YES        \-            \% of capital/assets

  base_for_pct            VARCHAR(30)     YES        \-            TIER1, NET_WORTH, TOTAL_ASSETS

  warning_threshold_pct   NUMERIC(5,2)    YES        80            Warning level %

  regulatory_limit        BOOLEAN         NO         FALSE         RBI mandated

  regulation_ref          VARCHAR(100)    YES        \-            Regulation reference

  effective_from          DATE            NO         \-            Limit effective date

  effective_to            DATE            YES        \-            Limit expiry

  status                  VARCHAR(20)     NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                                 Standard audit columns
  ----------------------- --------------- ---------- ------------- ---------------------------------------------------

**3.2 Standard Exposure Limits**

  ------------------------- ------------------- ------------------ ------------------------
  **Limit Type**            **RBI Limit**       **SMFC Limit**     **Regulation**

  Single Borrower           15% of Tier-1       12% of Tier-1      Scale Based Regulation

  Single Borrower (Infra)   20% of Tier-1       18% of Tier-1      SBR with carve-out

  Group Exposure            25% of Tier-1       22% of Tier-1      SBR

  Group (Infra)             35% of Tier-1       30% of Tier-1      SBR with carve-out

  Sector Concentration      No specific limit   25% of portfolio   Internal policy

  Rating Concentration      No specific limit   See matrix         Internal policy

  Geography                 No specific limit   30% per state      Internal policy
  ------------------------- ------------------- ------------------ ------------------------

**3.3 Exposure Tracking (TXN_EXPOSURE)**

  ----------------------- --------------- ---------- ------------- ---------------------------------
  **Column**              **Type**        **Null**   **Default**   **Description**

  exposure_id             BIGSERIAL       NO         Auto          Primary Key

  org_id                  BIGINT          NO         \-            FK to MST_ORGANIZATION

  as_of_date              DATE            NO         \-            Position date

  entity_id               BIGINT          YES        \-            FK to MST_ENTITY (for borrower)

  group_id                BIGINT          YES        \-            Group identifier

  sector                  VARCHAR(100)    YES        \-            Industry sector

  rating_grade            VARCHAR(10)     YES        \-            Internal rating

  geography               VARCHAR(100)    YES        \-            State/Region

  sanctioned_exposure     NUMERIC(18,2)   NO         0             Total sanctioned

  disbursed_exposure      NUMERIC(18,2)   NO         0             Total disbursed

  outstanding_exposure    NUMERIC(18,2)   NO         0             Current O/S

  undrawn_exposure        NUMERIC(18,2)   NO         0             Committed undrawn

  total_exposure          NUMERIC(18,2)   NO         0             O/S + Undrawn

  exposure_pct_tier1      NUMERIC(5,2)    YES        \-            \% of Tier-1 capital

  exposure_pct_networth   NUMERIC(5,2)    YES        \-            \% of Net Worth

  limit_id                BIGINT          YES        \-            FK to applicable limit

  limit_utilized_pct      NUMERIC(5,2)    YES        \-            \% of limit used

  breach_flag             BOOLEAN         NO         FALSE         Limit breached

  warning_flag            BOOLEAN         NO         FALSE         Approaching limit

  \+ Audit Columns                                                 Standard audit columns
  ----------------------- --------------- ---------- ------------- ---------------------------------

**3.4 Portfolio Risk Summary (TXN_PORTFOLIO_RISK)**

  ------------------------ --------------- ---------- ------------- ------------------------------
  **Column**               **Type**        **Null**   **Default**   **Description**

  risk_id                  BIGSERIAL       NO         Auto          Primary Key

  org_id                   BIGINT          NO         \-            FK to MST_ORGANIZATION

  as_of_date               DATE            NO         \-            Position date

  total_portfolio          NUMERIC(18,2)   NO         \-            Total loan portfolio

  standard_assets          NUMERIC(18,2)   NO         \-            Standard assets

  sma_assets               NUMERIC(18,2)   NO         \-            SMA assets

  npa_assets               NUMERIC(18,2)   NO         \-            NPA assets

  gross_npa_pct            NUMERIC(5,2)    NO         \-            Gross NPA %

  net_npa_pct              NUMERIC(5,2)    NO         \-            Net NPA %

  total_provisions         NUMERIC(18,2)   NO         \-            Total provisions

  provision_coverage       NUMERIC(5,2)    NO         \-            Provision coverage ratio

  weighted_avg_rating      NUMERIC(5,2)    YES        \-            Weighted avg rating score

  rating_distribution      JSONB           YES        \-            Rating-wise breakdown

  sector_distribution      JSONB           YES        \-            Sector-wise breakdown

  geography_distribution   JSONB           YES        \-            State-wise breakdown

  vintage_distribution     JSONB           YES        \-            Age-wise breakdown

  expected_loss            NUMERIC(18,2)   YES        \-            ECL (Ind-AS)

  \+ Audit Columns                                                  Standard audit columns
  ------------------------ --------------- ---------- ------------- ------------------------------

**3.5 Risk Dashboard Metrics**

  ------------------------------- ---------------------------------------------------- --------------- ---------------
  **Metric**                      **Formula**                                          **Threshold**   **Frequency**

  Gross NPA Ratio                 NPA / Total Advances × 100                           \< 5%           Daily

  Net NPA Ratio                   (NPA - Provisions) / (Advances - Provisions) × 100   \< 2%           Daily

  Provision Coverage              Provisions / NPA × 100                               \> 70%          Monthly

  Single Borrower Concentration   Max Exposure / Tier-1 × 100                          \< 15%          Daily

  Top 10 Borrower Concentration   Top 10 Exposure / Portfolio × 100                    \< 40%          Weekly

  Sector Concentration            Max Sector / Portfolio × 100                         \< 25%          Monthly

  SMA-2 Ratio                     SMA-2 / Standard × 100                               \< 5%           Daily

  Credit Cost Ratio               Provisions / Avg Advances × 100                      \< 2%           Quarterly

  CRAR                            (Tier-1 + Tier-2) / Risk Weighted Assets             \> 15%          Quarterly
  ------------------------------- ---------------------------------------------------- --------------- ---------------

**4. Business Flows**

**4.1 Borrowing Lifecycle Flow**

**Step 1: Borrowing Approval** - Board/Committee approves borrowing program

- Define borrowing limit for the year

- Approve instruments (Term Loan, NCD, etc.)

- Set treasury parameters

**Step 2: Create Borrowing Account** - Record new borrowing

INSERT INTO txn_borrowing (lender_id, amount, rate, tenure, \...)

- Link to lender master

- Define repayment schedule

**Step 3: Drawdown** - Utilize sanctioned amount

- Record each tranche/drawdown

- Generate schedule for tranche

- Credit bank account

UPDATE txn_borrowing SET drawn_amount += :amount

**Step 4: Interest/Principal Payment** - Process scheduled payments

FOR each due payment:

Create payment voucher (Dr: Borrowing, Cr: Bank)

UPDATE txn_borrowing_schedule SET paid_amount = due_amount, status = \'PAID\'

UPDATE txn_borrowing SET principal_outstanding -= principal_paid

**Step 5: Closure/Prepayment** - Close borrowing account

- Calculate prepayment penalty if applicable

- Final payment

- Close account

UPDATE txn_borrowing SET status = \'CLOSED\', closure_date = CURRENT_DATE

**4.2 ALM Report Generation Flow**

**Step 1: Initiate ALM Run** - Start monthly/quarterly ALM

position_date = CURRENT_DATE or month_end

INSERT INTO txn_alm_position (position_date, status=\'DRAFT\')

**Step 2: Map Assets to Buckets** - Classify all assets

- Loan schedules → by due date

- Investments → by maturity

- Cash/Bank → Day 1 bucket

**Step 3: Map Liabilities to Buckets** - Classify all liabilities

- Borrowing schedules → by due date

- Bonds/NCDs → by maturity

- Other payables → by expected outflow

**Step 4: Calculate Gaps** - Compute structural gaps

FOR each bucket:

gap = total_assets - total_liabilities

cumulative_gap = running_sum(gap)

**Step 5: Rate Sensitivity Analysis** - IRS computation

- Identify floating rate assets and liabilities

- Calculate impact of 100bps rate change

- Compute NII impact

**Step 6: Finalize and Report** - Generate ALM statements

- Generate Structural Liquidity Statement

- Generate Interest Rate Sensitivity Statement

- Submit to ALCO/Board

UPDATE txn_alm_position SET status = \'FINAL\'

**5. Business Rules**

**5.1 Borrowing Rules**

  ------------- ----------------------- ---------------------------------------------- -----------------------------------
  **Rule ID**   **Rule**                **Condition**                                  **Action**

  BOR-001       Within approved limit   Total borrowing \> approved limit              Block

  BOR-002       Maturity mismatch       Avg liability maturity \< avg asset maturity   Warn

  BOR-003       Currency mismatch       FCY borrowing without hedge                    Block/Warn

  BOR-004       Covenant compliance     Financial covenant breached                    Alert

  BOR-005       Payment on due date     Schedule due today                             Auto-trigger payment

  BOR-006       Rate reset              Reset date reached                             Update rate, recalculate schedule
  ------------- ----------------------- ---------------------------------------------- -----------------------------------

**5.2 ALM Rules**

  ------------- --------------------- ----------------------------------------------- --------------------
  **Rule ID**   **Rule**              **Condition**                                   **Action**

  ALM-001       Negative gap limit    Cumulative gap \< -15% of assets (short term)   Escalate to ALCO

  ALM-002       Structural mismatch   Long-term assets \> long-term liabilities       Warn

  ALM-003       Liquidity buffer      Day 1 + 2-7 day assets \< 10% of liabilities    Alert

  ALM-004       Rate sensitivity      NII impact \> 5% for 100bps shock               Escalate

  ALM-005       Data completeness     Missing schedules for any account               Block finalization
  ------------- --------------------- ----------------------------------------------- --------------------

**5.3 Exposure Rules**

  ------------- ----------------------- ------------------------------------ ----------------------------
  **Rule ID**   **Rule**                **Condition**                        **Action**

  EXP-001       Single borrower limit   Exposure \> 15% of Tier-1            Block new sanction

  EXP-002       Group limit             Group exposure \> 25% of Tier-1      Block new sanction

  EXP-003       Warning threshold       Exposure \> 80% of limit             Alert RM and Risk

  EXP-004       Sector concentration    Sector \> internal limit             Escalate to Risk Committee

  EXP-005       Rating migration        Significant downgrade in portfolio   Trigger review

  EXP-006       Connected lending       Exposure to related party            Board approval required
  ------------- ----------------------- ------------------------------------ ----------------------------

*\-\-- End of Phase 4 \-\--*

Phase 5 covers: HRIS & Payroll Modules
