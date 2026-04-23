**SMFC Ltd**

Integrated ERP Solution

**TECHNICAL SPECIFICATION**

Phase 2: Lending Pipeline

Part 2: Loan Application, Appraisal & Sanction

*Developer Reference Document*

Version 1.0

**Table of Contents**

1\. Loan Application Module

1.1 Application Header (TXN_LOAN_APPLICATION)

1.2 Application Documents (TXN_APPLICATION_DOC)

1.3 Application Fees (TXN_APPLICATION_FEE)

1.4 Application Workflow

2\. Technical Appraisal Module

2.1 Appraisal Header (TXN_TECHNICAL_APPRAISAL)

2.2 Project Details

2.3 Appraisal Checklist

3\. Financial Appraisal

3.1 Financial Analysis (TXN_FINANCIAL_ANALYSIS)

3.2 CMA Data Structure

3.3 Ratio Analysis

4\. Sanction Module

4.1 Sanction Record (TXN_LOAN_SANCTION)

4.2 Sanction Terms (TXN_SANCTION_TERMS)

4.3 Sanction Conditions

4.4 Security/Collateral Details

5\. Business Flows

6\. Business Rules & Validations

7\. State Machines

8\. API Contracts

**1. Loan Application Module**

The Loan Origination System (LOS) captures loan applications from intake through to sanction decision.

**1.1 Application Header (TXN_LOAN_APPLICATION)**

Main loan application record capturing request details and lifecycle.

**1.1.1 Table Definition**

  --------------------------- --------------- ---------- ------------- ---------------------------------
  **Column**                  **Type**        **Null**   **Default**   **Description**

  application_id              BIGSERIAL       NO         Auto          Primary Key

  org_id                      BIGINT          NO         \-            FK to MST_ORGANIZATION

  application_number          VARCHAR(30)     NO         \-            Unique application number

  application_date            DATE            NO         \-            Application submission date

  entity_id                   BIGINT          NO         \-            FK to MST_ENTITY (Borrower)

  product_id                  BIGINT          NO         \-            FK to MST_LOAN_PRODUCT

  requested_amount            NUMERIC(18,2)   NO         \-            Loan amount requested

  requested_tenure_months     INTEGER         NO         \-            Tenure requested

  purpose                     TEXT            NO         \-            Purpose of loan

  project_name                VARCHAR(300)    YES        \-            Project name if project finance

  project_location            VARCHAR(200)    YES        \-            Project location/state

  project_cost                NUMERIC(18,2)   YES        \-            Total project cost

  promoter_contribution       NUMERIC(18,2)   YES        \-            Promoter\'s equity contribution

  promoter_contribution_pct   NUMERIC(5,2)    YES        \-            Equity as % of project cost

  existing_exposure           NUMERIC(18,2)   YES        0             Existing loans with SMFC

  proposed_total_exposure     NUMERIC(18,2)   YES        \-            Total exposure post this loan

  source_of_application       VARCHAR(30)     YES        \-            DIRECT, REFERRAL, PORTAL, CAMP

  referral_source             VARCHAR(200)    YES        \-            Referral details if any

  relationship_manager_id     BIGINT          YES        \-            FK to MST_USER

  branch_id                   BIGINT          YES        \-            FK to MST_UNIT

  priority                    VARCHAR(20)     NO         NORMAL        LOW, NORMAL, HIGH, URGENT

  entity_rating_id            BIGINT          YES        \-            FK to TXN_ENTITY_RATING

  internal_rating             VARCHAR(10)     YES        \-            Rating at application time

  status                      VARCHAR(30)     NO         DRAFT         See status list below

  stage                       VARCHAR(30)     NO         APPLICATION   Current processing stage

  rejection_reason            TEXT            YES        \-            If rejected

  rejection_date              DATE            YES        \-            Rejection date

  withdrawal_reason           TEXT            YES        \-            If withdrawn

  withdrawal_date             DATE            YES        \-            Withdrawal date

  sanction_id                 BIGINT          YES        \-            FK to TXN_LOAN_SANCTION

  remarks                     TEXT            YES        \-            General remarks

  \+ Audit Columns                                                     Standard audit columns
  --------------------------- --------------- ---------- ------------- ---------------------------------

**1.1.2 Application Number Format**

Format: SMFC/{BRANCH}/{PRODUCT}/{FY}/{SEQUENCE}

Example: SMFC/DEL/PTL/2025-26/00001

Components:

SMFC - Organization prefix

DEL - Branch code (3 chars)

PTL - Product code (3 chars)

2025-26 - Financial year

00001 - Sequential number (reset yearly)

**1.1.3 Application Status Values**

  --------------------- --------------- ------------------------------- -------------------------
  **Status**            **Stage**       **Description**                 **Next Actions**

  DRAFT                 APPLICATION     Application being prepared      SUBMIT, DELETE

  SUBMITTED             APPLICATION     Submitted for processing        ACCEPT, RETURN, REJECT

  UNDER_REVIEW          APPLICATION     Initial review in progress      PROCEED, RETURN, REJECT

  DOCS_PENDING          APPLICATION     Waiting for documents           SUBMIT_DOCS, WITHDRAW

  TECHNICAL_APPRAISAL   APPRAISAL       Technical evaluation            COMPLETE_TECH, REJECT

  FINANCIAL_APPRAISAL   APPRAISAL       Financial evaluation            COMPLETE_FIN, REJECT

  APPRAISAL_COMPLETE    APPRAISAL       Both appraisals done            RECOMMEND, REJECT

  PENDING_SANCTION      SANCTION        Awaiting sanction decision      SANCTION, REJECT

  SANCTIONED            SANCTION        Loan sanctioned                 ACCEPT_SANCTION

  SANCTION_ACCEPTED     POST_SANCTION   Borrower accepted terms         PROCEED_DISB

  REJECTED              CLOSED          Application rejected            \-

  WITHDRAWN             CLOSED          Withdrawn by applicant          \-

  LAPSED                CLOSED          Auto-closed due to inactivity   \-
  --------------------- --------------- ------------------------------- -------------------------

**1.1.4 Indexes**

PRIMARY KEY (application_id)

UNIQUE INDEX idx_app_number ON txn_loan_application(application_number)

INDEX idx_app_entity ON txn_loan_application(entity_id)

INDEX idx_app_product ON txn_loan_application(product_id)

INDEX idx_app_status ON txn_loan_application(status)

INDEX idx_app_stage ON txn_loan_application(stage)

INDEX idx_app_rm ON txn_loan_application(relationship_manager_id)

INDEX idx_app_date ON txn_loan_application(application_date)

**1.2 Application Documents (TXN_APPLICATION_DOC)**

Documents submitted against loan application, linked to checklist.

**1.2.1 Table Definition**

  ---------------------- -------------- ---------- ------------- ------------------------------
  **Column**             **Type**       **Null**   **Default**   **Description**

  app_doc_id             BIGSERIAL      NO         Auto          Primary Key

  application_id         BIGINT         NO         \-            FK to TXN_LOAN_APPLICATION

  checklist_id           BIGINT         NO         \-            FK to MST_DOC_CHECKLIST

  doc_name               VARCHAR(200)   NO         \-            Document name

  file_name              VARCHAR(255)   NO         \-            Uploaded file name

  file_path              VARCHAR(500)   NO         \-            Storage path

  file_size              INTEGER        NO         \-            Size in bytes

  file_type              VARCHAR(50)    NO         \-            MIME type

  document_date          DATE           YES        \-            Document date

  document_ref           VARCHAR(100)   YES        \-            Document reference number

  valid_from             DATE           YES        \-            Validity start

  valid_to               DATE           YES        \-            Validity end

  verification_status    VARCHAR(20)    NO         PENDING       PENDING, VERIFIED, REJECTED

  verified_by            BIGINT         YES        \-            FK to MST_USER

  verified_at            TIMESTAMPTZ    YES        \-            Verification timestamp

  verification_remarks   VARCHAR(500)   YES        \-            Verification notes

  rejection_reason       VARCHAR(500)   YES        \-            If rejected

  version                INTEGER        NO         1             Document version

  is_latest              BOOLEAN        NO         TRUE          Latest version flag

  \+ Audit Columns                                               Standard audit columns
  ---------------------- -------------- ---------- ------------- ------------------------------

**1.3 Application Fees (TXN_APPLICATION_FEE)**

Fees charged at application/processing stage.

**1.3.1 Table Definition**

  -------------------- --------------- ---------- ------------- ---------------------------------
  **Column**           **Type**        **Null**   **Default**   **Description**

  app_fee_id           BIGSERIAL       NO         Auto          Primary Key

  application_id       BIGINT          NO         \-            FK to TXN_LOAN_APPLICATION

  fee_id               BIGINT          NO         \-            FK to MST_FEE

  fee_name             VARCHAR(100)    NO         \-            Fee description

  base_amount          NUMERIC(18,2)   NO         \-            Fee amount before tax

  gst_rate             NUMERIC(5,2)    YES        \-            GST rate %

  gst_amount           NUMERIC(18,2)   YES        \-            GST amount

  total_amount         NUMERIC(18,2)   NO         \-            Total including GST

  due_date             DATE            YES        \-            Payment due date

  payment_status       VARCHAR(20)     NO         PENDING       PENDING, PAID, WAIVED, REFUNDED

  waiver_pct           NUMERIC(5,2)    YES        \-            Waiver percentage

  waiver_amount        NUMERIC(18,2)   YES        \-            Waived amount

  waiver_approved_by   BIGINT          YES        \-            FK to MST_USER

  waiver_reason        VARCHAR(500)    YES        \-            Waiver justification

  receipt_number       VARCHAR(50)     YES        \-            Payment receipt number

  receipt_date         DATE            YES        \-            Payment date

  payment_mode         VARCHAR(30)     YES        \-            RTGS, NEFT, CHEQUE, CASH

  voucher_id           BIGINT          YES        \-            FK to TXN_VOUCHER

  \+ Audit Columns                                              Standard audit columns
  -------------------- --------------- ---------- ------------- ---------------------------------

**1.4 Application Workflow (TXN_APPLICATION_WORKFLOW)**

Tracks application processing history and approvals.

**1.4.1 Table Definition**

  ------------------ ------------- ---------- ------------- --------------------------------------
  **Column**         **Type**      **Null**   **Default**   **Description**

  workflow_id        BIGSERIAL     NO         Auto          Primary Key

  application_id     BIGINT        NO         \-            FK to TXN_LOAN_APPLICATION

  from_status        VARCHAR(30)   NO         \-            Previous status

  to_status          VARCHAR(30)   NO         \-            New status

  from_stage         VARCHAR(30)   NO         \-            Previous stage

  to_stage           VARCHAR(30)   NO         \-            New stage

  action             VARCHAR(30)   NO         \-            Action taken (SUBMIT, APPROVE, etc.)

  action_by          BIGINT        NO         \-            FK to MST_USER

  action_date        TIMESTAMPTZ   NO         \-            Action timestamp

  assigned_to        BIGINT        YES        \-            FK to MST_USER (next handler)

  assigned_role      VARCHAR(50)   YES        \-            Role for next action

  sla_due_at         TIMESTAMPTZ   YES        \-            SLA deadline

  comments           TEXT          YES        \-            Action comments

  \+ Audit Columns                                          Standard audit columns
  ------------------ ------------- ---------- ------------- --------------------------------------

**2. Technical Appraisal Module**

Technical due diligence for project finance and term loans.

**2.1 Technical Appraisal (TXN_TECHNICAL_APPRAISAL)**

Technical assessment record capturing project viability analysis.

**2.1.1 Table Definition**

  ------------------------------ --------------- ---------- ------------- ------------------------------------------
  **Column**                     **Type**        **Null**   **Default**   **Description**

  tech_appraisal_id              BIGSERIAL       NO         Auto          Primary Key

  application_id                 BIGINT          NO         \-            FK to TXN_LOAN_APPLICATION

  appraisal_date                 DATE            NO         \-            Appraisal start date

  appraiser_id                   BIGINT          NO         \-            FK to MST_USER

  project_type                   VARCHAR(50)     NO         \-            PORT, SHIPPING, LOGISTICS, INFRA, OTHER

  project_description            TEXT            YES        \-            Project description

  project_capacity               VARCHAR(200)    YES        \-            Project capacity/size

  technology_type                VARCHAR(100)    YES        \-            Technology being used

  technology_provider            VARCHAR(200)    YES        \-            Technology partner/vendor

  implementation_period_months   INTEGER         YES        \-            Expected implementation time

  cod_date                       DATE            YES        \-            Commercial Operation Date

  land_area_acres                NUMERIC(10,2)   YES        \-            Land requirement

  land_status                    VARCHAR(50)     YES        \-            OWNED, LEASED, TO_BE_ACQUIRED

  environmental_clearance        VARCHAR(30)     YES        \-            OBTAINED, APPLIED, NOT_REQUIRED

  ec_date                        DATE            YES        \-            EC date

  other_clearances               JSONB           YES        \-            List of other clearances

  project_cost_estimate          NUMERIC(18,2)   YES        \-            Appraised project cost

  cost_variance_pct              NUMERIC(5,2)    YES        \-            Variance from application

  cost_variance_reason           TEXT            YES        \-            Reason for variance

  technical_feasibility          VARCHAR(20)     YES        \-            FEASIBLE, CONDITIONAL, NOT_FEASIBLE

  feasibility_remarks            TEXT            YES        \-            Feasibility assessment

  implementation_risk            VARCHAR(20)     YES        \-            LOW, MEDIUM, HIGH

  technology_risk                VARCHAR(20)     YES        \-            LOW, MEDIUM, HIGH

  regulatory_risk                VARCHAR(20)     YES        \-            LOW, MEDIUM, HIGH

  overall_risk                   VARCHAR(20)     YES        \-            LOW, MEDIUM, HIGH

  site_visit_date                DATE            YES        \-            Site visit date

  site_visit_report              TEXT            YES        \-            Site visit observations

  recommendation                 VARCHAR(30)     YES        \-            PROCEED, PROCEED_WITH_CONDITIONS, REJECT

  conditions                     TEXT            YES        \-            Conditions if any

  status                         VARCHAR(20)     NO         DRAFT         DRAFT, SUBMITTED, APPROVED, REJECTED

  approved_by                    BIGINT          YES        \-            FK to MST_USER

  approved_at                    TIMESTAMPTZ     YES        \-            Approval timestamp

  \+ Audit Columns                                                        Standard audit columns
  ------------------------------ --------------- ---------- ------------- ------------------------------------------

**2.2 Project Milestones (TXN_PROJECT_MILESTONE)**

Implementation milestones for disbursement linkage.

**2.2.1 Table Definition**

  --------------------- --------------- ---------- ------------- ------------------------------------------
  **Column**            **Type**        **Null**   **Default**   **Description**

  milestone_id          BIGSERIAL       NO         Auto          Primary Key

  tech_appraisal_id     BIGINT          NO         \-            FK to TXN_TECHNICAL_APPRAISAL

  milestone_number      INTEGER         NO         \-            Sequence number

  milestone_name        VARCHAR(200)    NO         \-            Milestone description

  expected_date         DATE            NO         \-            Target completion date

  completion_criteria   TEXT            YES        \-            Criteria for completion

  disbursement_linked   BOOLEAN         NO         FALSE         Linked to disbursement

  disbursement_pct      NUMERIC(5,2)    YES        \-            \% of loan to disburse

  disbursement_amount   NUMERIC(18,2)   YES        \-            Amount to disburse

  status                VARCHAR(20)     NO         PENDING       PENDING, IN_PROGRESS, COMPLETED, DELAYED

  actual_date           DATE            YES        \-            Actual completion date

  remarks               VARCHAR(500)    YES        \-            Completion remarks

  \+ Audit Columns                                               Standard audit columns
  --------------------- --------------- ---------- ------------- ------------------------------------------

**2.2.2 Sample Milestones**

  -------- ---------------------------------- -------------------- ------------------
  **\#**   **Milestone**                      **Disbursement %**   **Cumulative %**

  1        Land acquisition complete          10%                  10%

  2        All statutory approvals obtained   10%                  20%

  3        Civil works 50% complete           20%                  40%

  4        Equipment ordered/delivered        25%                  65%

  5        Civil works 100% complete          15%                  80%

  6        Equipment installation complete    10%                  90%

  7        COD achieved                       10%                  100%
  -------- ---------------------------------- -------------------- ------------------

**3. Financial Appraisal**

Financial analysis of the borrower and project viability.

**3.1 Financial Analysis (TXN_FINANCIAL_ANALYSIS)**

Summary financial appraisal capturing key metrics and assessment.

**3.1.1 Table Definition**

  ---------------------------- -------------- ---------- ------------- ------------------------------------------
  **Column**                   **Type**       **Null**   **Default**   **Description**

  fin_analysis_id              BIGSERIAL      NO         Auto          Primary Key

  application_id               BIGINT         NO         \-            FK to TXN_LOAN_APPLICATION

  analyst_id                   BIGINT         NO         \-            FK to MST_USER

  analysis_date                DATE           NO         \-            Analysis date

  historical_years             INTEGER        NO         3             Years of historical data analyzed

  projection_years             INTEGER        NO         \-            Years of projections

  revenue_cagr_historical      NUMERIC(5,2)   YES        \-            Historical revenue CAGR

  revenue_cagr_projected       NUMERIC(5,2)   YES        \-            Projected revenue CAGR

  ebitda_margin_avg            NUMERIC(5,2)   YES        \-            Average EBITDA margin

  pat_margin_avg               NUMERIC(5,2)   YES        \-            Average PAT margin

  current_ratio                NUMERIC(5,2)   YES        \-            Current ratio

  debt_equity_ratio            NUMERIC(5,2)   YES        \-            Debt to Equity ratio

  interest_coverage            NUMERIC(5,2)   YES        \-            Interest coverage ratio

  dscr_min                     NUMERIC(5,2)   YES        \-            Minimum DSCR during tenure

  dscr_avg                     NUMERIC(5,2)   YES        \-            Average DSCR

  project_irr                  NUMERIC(5,2)   YES        \-            Project IRR %

  equity_irr                   NUMERIC(5,2)   YES        \-            Equity IRR %

  payback_years                NUMERIC(5,2)   YES        \-            Payback period in years

  break_even_capacity_pct      NUMERIC(5,2)   YES        \-            Break-even capacity utilization

  sensitivity_analysis         JSONB          YES        \-            Sensitivity scenarios

  working_capital_assessment   JSONB          YES        \-            WC requirement analysis

  fund_flow_analysis           JSONB          YES        \-            Sources and uses of funds

  cash_flow_adequacy           VARCHAR(30)    YES        \-            ADEQUATE, MARGINAL, INADEQUATE

  overall_assessment           VARCHAR(30)    YES        \-            STRONG, SATISFACTORY, WEAK

  recommendation               VARCHAR(30)    YES        \-            PROCEED, PROCEED_WITH_CONDITIONS, REJECT

  conditions                   TEXT           YES        \-            Conditions if any

  analyst_remarks              TEXT           YES        \-            Detailed remarks

  status                       VARCHAR(20)    NO         DRAFT         DRAFT, SUBMITTED, APPROVED, REJECTED

  \+ Audit Columns                                                     Standard audit columns
  ---------------------------- -------------- ---------- ------------- ------------------------------------------

**3.2 Financial Statements (TXN_FINANCIAL_STATEMENT)**

Historical and projected financial statements captured during appraisal.

**3.2.1 Table Definition**

  ------------------ -------------- ---------- ------------- -------------------------------
  **Column**         **Type**       **Null**   **Default**   **Description**

  statement_id       BIGSERIAL      NO         Auto          Primary Key

  fin_analysis_id    BIGINT         NO         \-            FK to TXN_FINANCIAL_ANALYSIS

  statement_type     VARCHAR(30)    NO         \-            BALANCE_SHEET, PNL, CASH_FLOW

  period_type        VARCHAR(20)    NO         \-            HISTORICAL, PROJECTED

  financial_year     VARCHAR(10)    NO         \-            FY (e.g., 2024-25)

  period_end_date    DATE           NO         \-            Period end date

  is_audited         BOOLEAN        NO         FALSE         Audited figures

  statement_data     JSONB          NO         \-            Full statement in JSON

  key_metrics        JSONB          YES        \-            Extracted key metrics

  remarks            VARCHAR(500)   YES        \-            Period-specific remarks

  \+ Audit Columns                                           Standard audit columns
  ------------------ -------------- ---------- ------------- -------------------------------

**3.2.2 Statement Data JSON Structure (Balance Sheet)**

{

\"assets\": {

\"non_current\": {

\"fixed_assets\": 50000000,

\"intangible_assets\": 1000000,

\"investments\": 5000000

},

\"current\": {

\"inventory\": 8000000,

\"receivables\": 12000000,

\"cash\": 3000000

}

},

\"liabilities\": {

\"equity\": { \"share_capital\": 20000000, \"reserves\": 15000000 },

\"non_current\": { \"term_loans\": 25000000 },

\"current\": { \"creditors\": 10000000, \"short_term_debt\": 5000000 }

}

}

**4. Sanction Module**

Loan sanction decision, terms, and conditions.

**4.1 Sanction Record (TXN_LOAN_SANCTION)**

Master sanction record capturing approved loan terms.

**4.1.1 Table Definition**

  -------------------------- --------------- ---------- ------------- ----------------------------------------
  **Column**                 **Type**        **Null**   **Default**   **Description**

  sanction_id                BIGSERIAL       NO         Auto          Primary Key

  application_id             BIGINT          NO         \-            FK to TXN_LOAN_APPLICATION

  sanction_number            VARCHAR(30)     NO         \-            Unique sanction reference

  sanction_date              DATE            NO         \-            Sanction date

  sanctioned_amount          NUMERIC(18,2)   NO         \-            Approved loan amount

  sanctioned_tenure_months   INTEGER         NO         \-            Approved tenure

  moratorium_months          INTEGER         NO         0             Moratorium period

  interest_type              VARCHAR(20)     NO         \-            FIXED, FLOATING

  base_rate_id               BIGINT          YES        \-            FK to MST_INTEREST_RATE

  base_rate_value            NUMERIC(5,2)    YES        \-            Base rate at sanction

  spread_bps                 INTEGER         NO         \-            Spread in basis points

  effective_rate             NUMERIC(5,2)    NO         \-            Total interest rate

  fixed_rate                 NUMERIC(5,2)    YES        \-            If interest_type=FIXED

  repayment_frequency        VARCHAR(20)     NO         \-            MONTHLY, QUARTERLY, etc.

  repayment_mode             VARCHAR(30)     NO         \-            EMI, STRUCTURED, BALLOON, BULLET

  first_repayment_date       DATE            YES        \-            Expected first repayment

  maturity_date              DATE            YES        \-            Loan maturity date

  prepayment_allowed         BOOLEAN         NO         TRUE          Prepayment permitted

  prepayment_penalty_pct     NUMERIC(5,2)    YES        \-            Prepayment penalty

  prepayment_lockin_months   INTEGER         YES        \-            Lock-in period

  validity_days              INTEGER         NO         90            Sanction validity

  validity_expiry_date       DATE            NO         \-            Sanction expires on

  sanctioning_authority      VARCHAR(100)    YES        \-            Approving authority

  sanctioned_by              BIGINT          NO         \-            FK to MST_USER

  committee_meeting_date     DATE            YES        \-            If committee approval

  committee_minutes_ref      VARCHAR(100)    YES        \-            Minutes reference

  status                     VARCHAR(20)     NO         ACTIVE        ACTIVE, ACCEPTED, EXPIRED, CANCELLED

  acceptance_date            DATE            YES        \-            Borrower acceptance date

  acceptance_letter_path     VARCHAR(500)    YES        \-            Signed acceptance letter

  loan_account_id            BIGINT          YES        \-            FK to TXN_LOAN_ACCOUNT (post-creation)

  \+ Audit Columns                                                    Standard audit columns
  -------------------------- --------------- ---------- ------------- ----------------------------------------

**4.2 Sanction Conditions (TXN_SANCTION_CONDITION)**

Pre-disbursement and post-disbursement conditions.

**4.2.1 Table Definition**

  ------------------------ -------------- ---------- ------------- ----------------------------------------------
  **Column**               **Type**       **Null**   **Default**   **Description**

  condition_id             BIGSERIAL      NO         Auto          Primary Key

  sanction_id              BIGINT         NO         \-            FK to TXN_LOAN_SANCTION

  condition_type           VARCHAR(30)    NO         \-            PRE_DISBURSEMENT, POST_DISBURSEMENT, ONGOING

  condition_category       VARCHAR(30)    YES        \-            LEGAL, FINANCIAL, SECURITY, OTHER

  condition_number         INTEGER        NO         \-            Sequence number

  condition_text           TEXT           NO         \-            Condition description

  compliance_deadline      DATE           YES        \-            Deadline for compliance

  is_mandatory             BOOLEAN        NO         TRUE          Mandatory condition

  can_waive                BOOLEAN        NO         FALSE         Can be waived

  linked_to_disbursement   INTEGER        YES        \-            Disbursement tranche number

  compliance_status        VARCHAR(20)    NO         PENDING       PENDING, COMPLIED, WAIVED, DEFERRED

  complied_date            DATE           YES        \-            Compliance date

  compliance_remarks       VARCHAR(500)   YES        \-            Compliance notes

  verified_by              BIGINT         YES        \-            FK to MST_USER

  waiver_reason            TEXT           YES        \-            If waived

  waiver_approved_by       BIGINT         YES        \-            Waiver approver

  deferral_date            DATE           YES        \-            Deferred to date

  deferral_reason          TEXT           YES        \-            Reason for deferral

  \+ Audit Columns                                                 Standard audit columns
  ------------------------ -------------- ---------- ------------- ----------------------------------------------

**4.2.2 Sample Pre-Disbursement Conditions**

  -------- -------------- ---------------------------------------------- ---------------
  **\#**   **Category**   **Condition**                                  **Mandatory**

  1        LEGAL          Execution of Loan Agreement                    Yes

  2        LEGAL          Creation of charge on assets with CERSAI/ROC   Yes

  3        SECURITY       Mortgage of project land in favor of SMFC      Yes

  4        SECURITY       Hypothecation of movable assets                Yes

  5        SECURITY       Corporate Guarantee from promoter company      Yes

  6        FINANCIAL      Infusion of 25% promoter equity                Yes

  7        FINANCIAL      Tie-up of balance debt from other lenders      No

  8        OTHER          Environmental Clearance                        Yes

  9        OTHER          All statutory approvals                        Yes

  10       OTHER          Project Insurance policy assignment            Yes
  -------- -------------- ---------------------------------------------- ---------------

**4.3 Security/Collateral (TXN_LOAN_SECURITY)**

Collateral and security details linked to sanction.

**4.3.1 Table Definition**

  ----------------------- --------------- ---------- ------------- ---------------------------------
  **Column**              **Type**        **Null**   **Default**   **Description**

  loan_security_id        BIGSERIAL       NO         Auto          Primary Key

  sanction_id             BIGINT          NO         \-            FK to TXN_LOAN_SANCTION

  security_type_id        BIGINT          NO         \-            FK to MST_SECURITY_TYPE

  security_category       VARCHAR(30)     NO         \-            PRIMARY, COLLATERAL, GUARANTEE

  description             TEXT            NO         \-            Security description

  asset_description       TEXT            YES        \-            Detailed asset description

  asset_location          VARCHAR(300)    YES        \-            Asset location

  ownership_type          VARCHAR(30)     YES        \-            BORROWER, PROMOTER, THIRD_PARTY

  owner_name              VARCHAR(200)    YES        \-            Owner name if not borrower

  owner_entity_id         BIGINT          YES        \-            FK to MST_ENTITY if in system

  original_value          NUMERIC(18,2)   YES        \-            Original/purchase value

  valuation_amount        NUMERIC(18,2)   YES        \-            Latest valuation amount

  valuation_date          DATE            YES        \-            Valuation date

  valuer_name             VARCHAR(200)    YES        \-            Valuer/agency name

  valuation_report_path   VARCHAR(500)    YES        \-            Valuation report

  margin_pct              NUMERIC(5,2)    YES        \-            Margin/haircut applied

  net_security_value      NUMERIC(18,2)   YES        \-            Value after margin

  charge_type             VARCHAR(30)     YES        \-            FIRST, SECOND, PARI_PASSU

  charge_holder           VARCHAR(200)    YES        \-            Existing charge holder

  charge_created          BOOLEAN         NO         FALSE         Charge created

  charge_creation_date    DATE            YES        \-            Charge creation date

  cersai_ref              VARCHAR(50)     YES        \-            CERSAI registration number

  roc_ref                 VARCHAR(50)     YES        \-            ROC charge ID

  insurance_required      BOOLEAN         NO         FALSE         Insurance needed

  insurance_policy_no     VARCHAR(50)     YES        \-            Insurance policy number

  insurance_amount        NUMERIC(18,2)   YES        \-            Sum insured

  insurance_expiry        DATE            YES        \-            Policy expiry date

  release_status          VARCHAR(20)     NO         HELD          HELD, PARTIAL_RELEASE, RELEASED

  release_date            DATE            YES        \-            Release date

  release_reason          VARCHAR(500)    YES        \-            Release justification

  status                  VARCHAR(20)     NO         PROPOSED      PROPOSED, CREATED, RELEASED

  \+ Audit Columns                                                 Standard audit columns
  ----------------------- --------------- ---------- ------------- ---------------------------------

**5. Business Flows**

Complete end-to-end flows for loan origination.

**5.1 Loan Application Flow**

**TRIGGER: Borrower initiates new loan application**

**Step 1: Validate Entity Eligibility** - Check borrower readiness

- VALIDATE: Entity KYC is complete

- VALIDATE: Entity has valid internal rating

- VALIDATE: Entity not blacklisted

- VALIDATE: No overdue with SMFC

IF any validation fails → Block application, show error

**Step 2: Create Application** - Initialize loan application

INSERT INTO txn_loan_application (

entity_id, product_id, requested_amount, requested_tenure,

purpose, status=\'DRAFT\', stage=\'APPLICATION\'

)

- Generate application_number

- Load document checklist for product

- Calculate applicable fees

**Step 3: Capture Application Details** - Enter loan specifics

- Project details (name, location, cost)

- Funding plan (equity, debt, internal accruals)

- Promoter contribution calculation

- Purpose and end-use of funds

**Step 4: Document Upload** - Collect required documents

- Display checklist with mandatory flags

- Upload documents against each item

- Track upload status and pending items

INSERT INTO txn_application_doc FOR EACH document

**Step 5: Fee Payment** - Collect processing fee

- Calculate fee based on product and amount

- Generate fee invoice

- Record payment receipt

UPDATE txn_application_fee SET payment_status=\'PAID\'

**Step 6: Submit Application** - Submit for processing

- VALIDATE: All mandatory documents uploaded

- VALIDATE: Processing fee paid (or waiver approved)

UPDATE txn_loan_application SET status=\'SUBMITTED\'

INSERT INTO txn_application_workflow (action=\'SUBMIT\')

- Assign to processing officer

- Send acknowledgment to borrower

**5.2 Appraisal Flow**

**TRIGGER: Application moves to appraisal stage**

**Step 1: Technical Appraisal** - Evaluate project viability

- Assign to technical appraiser

- Review DPR and project documents

- Conduct site visit

- Assess technical feasibility, risks

- Define implementation milestones

INSERT INTO txn_technical_appraisal (\...)

INSERT INTO txn_project_milestone FOR EACH milestone

**Step 2: Financial Appraisal** - Analyze financials

- Assign to financial analyst

- Review historical financials (3 years)

- Validate projections

- Calculate key ratios (DSCR, ICR, etc.)

- Assess cash flow adequacy

- Perform sensitivity analysis

INSERT INTO txn_financial_analysis (\...)

INSERT INTO txn_financial_statement FOR EACH period

**Step 3: Collate Appraisals** - Combine assessments

- Both appraisals must be complete

- Review technical and financial recommendations

- Prepare consolidated appraisal note

UPDATE txn_loan_application SET stage=\'APPRAISAL_COMPLETE\'

**Step 4: Recommend Sanction** - Prepare sanction proposal

- If both recommend PROCEED → Prepare sanction terms

- Determine sanctioning authority based on amount

- Route to appropriate approver/committee

UPDATE txn_loan_application SET status=\'PENDING_SANCTION\'

**5.3 Sanction Flow**

**TRIGGER: Application submitted for sanction decision**

**Step 1: Sanction Review** - Authority reviews proposal

- Review appraisal note and recommendations

- Assess risk and pricing

- Determine terms and conditions

**Step 2: Sanction Decision** - Approve/Reject

**Decision: APPROVE / REJECT / DEFER**

**If APPROVE:**

INSERT INTO txn_loan_sanction (

application_id, sanctioned_amount, tenure, rate, \...

)

INSERT INTO txn_sanction_condition FOR EACH condition

INSERT INTO txn_loan_security FOR EACH security

UPDATE txn_loan_application SET status=\'SANCTIONED\', sanction_id=:id

**If REJECT:**

UPDATE txn_loan_application SET status=\'REJECTED\', rejection_reason=:reason

- Notify borrower of rejection

**Step 3: Generate Sanction Letter** - Create formal sanction

- Generate sanction letter with all terms

- Include all conditions (pre/post disbursement)

- Include security requirements

- Set validity period (typically 90 days)

**Step 4: Borrower Acceptance** - Obtain borrower consent

- Send sanction letter to borrower

- Borrower reviews terms and conditions

- Borrower signs and returns acceptance

UPDATE txn_loan_sanction SET status=\'ACCEPTED\', acceptance_date=:date

UPDATE txn_loan_application SET status=\'SANCTION_ACCEPTED\'

**Step 5: Proceed to Documentation** - Initiate legal process

- Create loan account (covered in Phase 3)

- Initiate legal documentation

- Track pre-disbursement condition compliance

**6. Business Rules & Validations**

**6.1 Application Rules**

  ------------- ----------------------- ----------------------------------------------- -------------- -----------------------
  **Rule ID**   **Rule**                **Condition**                                   **Action**     **Error Code**

  APP-001       Entity KYC complete     entity.kyc_status != \'COMPLETE\'               Block          ERR_KYC_INCOMPLETE

  APP-002       Valid internal rating   entity.internal_rating IS NULL OR expired       Block          ERR_NO_RATING

  APP-003       Minimum rating          entity.rating \< product.min_rating             Block          ERR_RATING_BELOW_MIN

  APP-004       Amount within limits    amount \< product.min OR \> product.max         Block          ERR_AMOUNT_LIMIT

  APP-005       Tenure within limits    tenure \< product.min OR \> product.max         Block          ERR_TENURE_LIMIT

  APP-006       No overdue              entity has overdue with SMFC                    Block          ERR_OVERDUE_EXISTS

  APP-007       Not blacklisted         entity.status = \'BLACKLISTED\'                 Block          ERR_BLACKLISTED

  APP-008       Sector eligibility      entity.sector NOT IN product.eligible_sectors   Block          ERR_SECTOR_INELIGIBLE

  APP-009       Mandatory docs          mandatory docs not uploaded                     Block Submit   ERR_DOCS_PENDING

  APP-010       Fee payment             processing fee not paid/waived                  Block Submit   ERR_FEE_PENDING
  ------------- ----------------------- ----------------------------------------------- -------------- -----------------------

**6.2 Appraisal Rules**

  ------------- --------------------------- ------------------------------------------ -------------------- -----------------------
  **Rule ID**   **Rule**                    **Condition**                              **Action**           **Error Code**

  APR-001       Site visit required         project_finance AND no site_visit_date     Warn                 WARN_NO_SITE_VISIT

  APR-002       Min DSCR check              dscr_min \< 1.20                           Flag for committee   ALERT_LOW_DSCR

  APR-003       High D/E ratio              debt_equity_ratio \> 3.0                   Flag for review      ALERT_HIGH_LEVERAGE

  APR-004       Negative IRR                project_irr \<= 0                          Block approval       ERR_NEGATIVE_IRR

  APR-005       Tech feasibility            technical_feasibility = \'NOT_FEASIBLE\'   Block sanction       ERR_NOT_FEASIBLE

  APR-006       Both appraisals done        tech OR fin appraisal incomplete           Block sanction       ERR_APPRAISAL_PENDING

  APR-007       Consistent recommendation   tech != fin recommendation                 Escalate             ALERT_MISMATCH
  ------------- --------------------------- ------------------------------------------ -------------------- -----------------------

**6.3 Sanction Rules**

  ------------- --------------------- ------------------------------------- ---------------------- -----------------------
  **Rule ID**   **Rule**              **Condition**                         **Action**             **Error Code**

  SAN-001       Authority check       amount \> user.sanction_limit         Route to higher auth   ERR_EXCEEDS_AUTH

  SAN-002       Amount variance       sanctioned \> requested               Block                  ERR_SANCTION_EXCEEDS

  SAN-003       Tenure variance       sanctioned_tenure \> product.max      Block                  ERR_TENURE_EXCEEDS

  SAN-004       Rate floor            effective_rate \< minimum_rate        Warn                   WARN_RATE_BELOW_FLOOR

  SAN-005       Security coverage     security_value \< 1.0x loan           Warn                   WARN_LOW_COVERAGE

  SAN-006       Validity check        sanction expired (\> validity_days)   Block disbursement     ERR_SANCTION_EXPIRED

  SAN-007       Acceptance required   disbursement without acceptance       Block                  ERR_NOT_ACCEPTED
  ------------- --------------------- ------------------------------------- ---------------------- -----------------------

**7. State Machines**

**7.1 Application Status State Machine**

  --------------------- ----------------- --------------------- ------------------ ----------------------
  **From Status**       **Event**         **To Status**         **Stage Change**   **Conditions**

  (new)                 CREATE            DRAFT                 APPLICATION        Entity eligible

  DRAFT                 SUBMIT            SUBMITTED             \-                 All validations pass

  DRAFT                 DELETE            (deleted)             \-                 No fee paid

  SUBMITTED             ACCEPT            UNDER_REVIEW          \-                 Initial check OK

  SUBMITTED             RETURN            DOCS_PENDING          \-                 Docs insufficient

  SUBMITTED             REJECT            REJECTED              CLOSED             Ineligible

  DOCS_PENDING          SUBMIT_DOCS       SUBMITTED             \-                 Docs uploaded

  UNDER_REVIEW          PROCEED           TECHNICAL_APPRAISAL   APPRAISAL          Review complete

  TECHNICAL_APPRAISAL   COMPLETE_TECH     FINANCIAL_APPRAISAL   \-                 Tech done

  FINANCIAL_APPRAISAL   COMPLETE_FIN      APPRAISAL_COMPLETE    \-                 Fin done

  APPRAISAL_COMPLETE    RECOMMEND         PENDING_SANCTION      SANCTION           Both recommend

  PENDING_SANCTION      SANCTION          SANCTIONED            \-                 Approved

  PENDING_SANCTION      REJECT            REJECTED              CLOSED             Not approved

  SANCTIONED            ACCEPT_SANCTION   SANCTION_ACCEPTED     POST_SANCTION      Borrower accepts

  \*                    WITHDRAW          WITHDRAWN             CLOSED             Borrower request

  \*                    LAPSE             LAPSED                CLOSED             Inactivity timeout
  --------------------- ----------------- --------------------- ------------------ ----------------------

**7.2 Sanction Status State Machine**

  ------------------ ---------------- --------------- --------------------------------------
  **From Status**    **Event**        **To Status**   **Conditions**

  (new)              SANCTION         ACTIVE          Authority approves

  ACTIVE             ACCEPT           ACCEPTED        Borrower signs acceptance

  ACTIVE             EXPIRE           EXPIRED         Current date \> validity_expiry_date

  ACTIVE             CANCEL           CANCELLED       Authority cancels

  ACCEPTED           CREATE_ACCOUNT   ACCEPTED        Loan account created
  ------------------ ---------------- --------------- --------------------------------------

**8. API Contracts**

**8.1 Application APIs**

**POST /api/v1/applications - Create Application**

Request Body:

{

\"entity_id\": 1001,

\"product_id\": 5,

\"requested_amount\": 500000000,

\"requested_tenure_months\": 120,

\"purpose\": \"Expansion of port terminal capacity\",

\"project_name\": \"Terminal 3 Expansion\",

\"project_location\": \"Gujarat\",

\"project_cost\": 750000000,

\"promoter_contribution\": 250000000

}

Response (201 Created):

{

\"application_id\": 5001,

\"application_number\": \"SMFC/DEL/PTL/2025-26/00042\",

\"status\": \"DRAFT\",

\"checklist\": \[\...\],

\"fees\": \[\...\]

}

**POST /api/v1/applications/{id}/submit**

Response (200 OK):

{

\"application_id\": 5001,

\"status\": \"SUBMITTED\",

\"assigned_to\": \"Credit Officer\",

\"sla_due_at\": \"2026-01-20T18:00:00Z\"

}

**POST /api/v1/applications/{id}/sanction**

Request Body:

{

\"sanctioned_amount\": 450000000,

\"sanctioned_tenure_months\": 120,

\"interest_type\": \"FLOATING\",

\"base_rate_id\": 1,

\"spread_bps\": 200,

\"moratorium_months\": 24,

\"repayment_frequency\": \"QUARTERLY\",

\"conditions\": \[\...\],

\"securities\": \[\...\]

}

*\-\-- End of Phase 2 \-\--*

Phase 3 will cover: Loan Accounting & Management, Disbursement, Repayment
