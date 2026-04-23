**SMFC Ltd**

Integrated ERP Solution

**TECHNICAL SPECIFICATION**

Phase 3: Loan Accounting & Management

Part 2: Receipts, NPA & Legal Module

**1. Receipt Management**

Processing and allocation of repayments received from borrowers.

**1.1 Receipt Record (TXN_RECEIPT)**

  --------------------- --------------- ---------- ------------- ---------------------------------------------------------
  **Column**            **Type**        **Null**   **Default**   **Description**

  receipt_id            BIGSERIAL       NO         Auto          Primary Key

  org_id                BIGINT          NO         \-            FK to MST_ORGANIZATION

  loan_account_id       BIGINT          NO         \-            FK to TXN_LOAN_ACCOUNT

  receipt_number        VARCHAR(30)     NO         \-            Unique receipt number

  receipt_date          DATE            NO         \-            Receipt date

  value_date            DATE            NO         \-            Value date for interest

  receipt_amount        NUMERIC(18,2)   NO         \-            Total amount received

  receipt_type          VARCHAR(30)     NO         \-            REGULAR, PREPAYMENT, PART_PREPAY, FORECLOSURE, RECOVERY

  payment_mode          VARCHAR(20)     NO         \-            RTGS, NEFT, CHEQUE, CASH, DD, AUTO_DEBIT

  instrument_number     VARCHAR(30)     YES        \-            Cheque/DD number

  instrument_date       DATE            YES        \-            Cheque/DD date

  drawee_bank           VARCHAR(200)    YES        \-            Bank name

  utr_reference         VARCHAR(50)     YES        \-            UTR for electronic

  deposited_bank_id     BIGINT          NO         \-            FK to MST_BANK_ACCOUNT

  entity_bank_id        BIGINT          YES        \-            FK to MST_ENTITY_BANK

  tds_deducted          NUMERIC(18,2)   NO         0             TDS deducted by borrower

  tds_certificate_no    VARCHAR(50)     YES        \-            TDS certificate ref

  net_amount            NUMERIC(18,2)   NO         \-            Net after TDS

  allocated_amount      NUMERIC(18,2)   NO         0             Amount allocated

  unallocated_amount    NUMERIC(18,2)   NO         \-            Pending allocation

  principal_allocated   NUMERIC(18,2)   NO         0             Allocated to principal

  interest_allocated    NUMERIC(18,2)   NO         0             Allocated to interest

  penal_allocated       NUMERIC(18,2)   NO         0             Allocated to penal

  charges_allocated     NUMERIC(18,2)   NO         0             Allocated to charges

  prepayment_penalty    NUMERIC(18,2)   NO         0             Prepayment charge

  allocation_status     VARCHAR(20)     NO         PENDING       PENDING, PARTIAL, FULLY_ALLOCATED

  cheque_status         VARCHAR(20)     YES        \-            DEPOSITED, CLEARED, BOUNCED

  bounce_date           DATE            YES        \-            Cheque bounce date

  bounce_reason         VARCHAR(200)    YES        \-            Bounce reason

  bounce_charges        NUMERIC(18,2)   YES        \-            Bounce charges levied

  reversal_id           BIGINT          YES        \-            FK to reversal receipt

  remarks               TEXT            YES        \-            Receipt remarks

  voucher_id            BIGINT          YES        \-            FK to TXN_VOUCHER

  status                VARCHAR(20)     NO         ACTIVE        ACTIVE, REVERSED, BOUNCED

  \+ Audit Columns                                               Standard audit columns
  --------------------- --------------- ---------- ------------- ---------------------------------------------------------

**1.2 Receipt Allocation (TXN_RECEIPT_ALLOCATION)**

Detailed allocation of receipt amount to outstanding dues.

  ------------------ --------------- ---------- ------------- -------------------------------------------------
  **Column**         **Type**        **Null**   **Default**   **Description**

  allocation_id      BIGSERIAL       NO         Auto          Primary Key

  receipt_id         BIGINT          NO         \-            FK to TXN_RECEIPT

  loan_account_id    BIGINT          NO         \-            FK to TXN_LOAN_ACCOUNT

  allocation_type    VARCHAR(20)     NO         \-            PRINCIPAL, INTEREST, PENAL, CHARGES, ON_ACCOUNT

  schedule_id        BIGINT          YES        \-            FK to schedule (principal/interest)

  demand_id          BIGINT          YES        \-            FK to TXN_DEMAND

  due_date           DATE            YES        \-            Original due date

  due_amount         NUMERIC(18,2)   YES        \-            Original due amount

  allocated_amount   NUMERIC(18,2)   NO         \-            Amount allocated

  dpd_at_payment     INTEGER         YES        \-            DPD when paid

  allocation_date    DATE            NO         \-            Allocation date

  \+ Audit Columns                                            Standard audit columns
  ------------------ --------------- ---------- ------------- -------------------------------------------------

**1.3 Allocation Priority**

Standard allocation sequence (configurable per product):

  -------------- --------------------------- --------------------------------------
  **Priority**   **Component**               **Rationale**

  1              Penal Interest              Penalty charges first

  2              Other Charges               Bounce charges, legal fees, etc.

  3              Overdue Interest            Oldest interest dues

  4              Current Interest            Current period interest

  5              Overdue Principal           Oldest principal dues

  6              Current Principal           Current period principal

  7              Future Principal (Prepay)   If prepayment

  8              On Account                  Unallocated surplus
  -------------- --------------------------- --------------------------------------

**1.4 Receipt Accounting Entries**

  ------------------------- -------------- -------------- ---------------------
  **Account**               **Debit**      **Credit**     **Description**

  Bank Account              ₹ XX,XX,XXX    \-             Amount received

  Loan Asset (Principal)    \-             ₹ XX,XXX       Principal reduction

  Interest Receivable       \-             ₹ X,XXX        Interest received

  Penal Interest Income     \-             ₹ XXX          Penal interest

  If TDS deducted:                                        

  TDS Receivable            ₹ X,XXX        \-             TDS to claim
  ------------------------- -------------- -------------- ---------------------

**2. Penal Interest Management**

Computation and tracking of delayed payment charges.

**2.1 Penal Interest Record (TXN_PENAL_INTEREST)**

  ----------------------- --------------- ---------- ------------- ------------------------------
  **Column**              **Type**        **Null**   **Default**   **Description**

  penal_id                BIGSERIAL       NO         Auto          Primary Key

  loan_account_id         BIGINT          NO         \-            FK to TXN_LOAN_ACCOUNT

  schedule_id             BIGINT          YES        \-            FK to overdue schedule

  demand_id               BIGINT          YES        \-            FK to TXN_DEMAND

  overdue_type            VARCHAR(20)     NO         \-            PRINCIPAL, INTEREST

  overdue_amount          NUMERIC(18,2)   NO         \-            Amount overdue

  original_due_date       DATE            NO         \-            Original due date

  calc_from_date          DATE            NO         \-            Penal calc start

  calc_to_date            DATE            NO         \-            Penal calc end

  days_overdue            INTEGER         NO         \-            Days delayed

  penal_rate              NUMERIC(5,2)    NO         \-            Penal rate % p.a.

  penal_amount            NUMERIC(18,2)   NO         \-            Penal interest charged

  penal_paid              NUMERIC(18,2)   NO         0             Penal paid

  penal_waived            NUMERIC(18,2)   NO         0             Penal waived

  penal_outstanding       NUMERIC(18,2)   NO         \-            Penal pending

  included_in_demand_id   BIGINT          YES        \-            Demand where included

  status                  VARCHAR(20)     NO         ACTIVE        ACTIVE, PAID, WAIVED

  \+ Audit Columns                                                 Standard audit columns
  ----------------------- --------------- ---------- ------------- ------------------------------

**2.2 Penal Interest Calculation**

Penal Interest = Overdue Amount × Penal Rate × Days Overdue / 365

Example:

Overdue Principal: ₹50,00,000

Days Overdue: 45 days

Penal Rate: 2% p.a. (additional to normal rate)

Penal = 50,00,000 × 0.02 × 45 / 365 = ₹12,329

**2.3 Penal Waiver (TXN_PENAL_WAIVER)**

  ------------------- --------------- ---------- ------------- ------------------------------
  **Column**          **Type**        **Null**   **Default**   **Description**

  waiver_id           BIGSERIAL       NO         Auto          Primary Key

  loan_account_id     BIGINT          NO         \-            FK to TXN_LOAN_ACCOUNT

  waiver_date         DATE            NO         \-            Waiver date

  penal_outstanding   NUMERIC(18,2)   NO         \-            Penal before waiver

  waiver_amount       NUMERIC(18,2)   NO         \-            Amount waived

  waiver_pct          NUMERIC(5,2)    YES        \-            Waiver percentage

  reason              TEXT            NO         \-            Justification

  approved_by         BIGINT          NO         \-            Approving authority

  approval_date       DATE            NO         \-            Approval date

  committee_ref       VARCHAR(100)    YES        \-            Committee reference

  voucher_id          BIGINT          YES        \-            FK to TXN_VOUCHER

  \+ Audit Columns                                             Standard audit columns
  ------------------- --------------- ---------- ------------- ------------------------------

**3. NPA Management**

Non-Performing Asset identification, classification, and provisioning.

**3.1 NPA Record (TXN_NPA)**

  ------------------------ --------------- ---------- ------------- ------------------------------------------
  **Column**               **Type**        **Null**   **Default**   **Description**

  npa_id                   BIGSERIAL       NO         Auto          Primary Key

  loan_account_id          BIGINT          NO         \-            FK to TXN_LOAN_ACCOUNT

  npa_date                 DATE            NO         \-            NPA recognition date

  dpd_at_npa               INTEGER         NO         \-            DPD when classified NPA

  overdue_amount_at_npa    NUMERIC(18,2)   NO         \-            Overdue at NPA

  principal_os_at_npa      NUMERIC(18,2)   NO         \-            Principal O/S at NPA

  total_os_at_npa          NUMERIC(18,2)   NO         \-            Total O/S at NPA

  initial_classification   VARCHAR(20)     NO         \-            SUB_STANDARD, DOUBTFUL, LOSS

  current_classification   VARCHAR(20)     NO         \-            Current classification

  classification_date      DATE            NO         \-            Current classification date

  provision_rate           NUMERIC(5,2)    NO         \-            Current provision %

  provision_amount         NUMERIC(18,2)   NO         \-            Provision held

  secured_portion          NUMERIC(18,2)   YES        \-            Secured by collateral

  unsecured_portion        NUMERIC(18,2)   YES        \-            Unsecured exposure

  irac_compliant           BOOLEAN         NO         TRUE          RBI IRAC compliance

  ots_initiated            BOOLEAN         NO         FALSE         OTS started

  legal_initiated          BOOLEAN         NO         FALSE         Legal action started

  recovery_rating          VARCHAR(20)     YES        \-            Expected recovery rating

  expected_recovery        NUMERIC(18,2)   YES        \-            Expected recovery amount

  upgraded_date            DATE            YES        \-            If upgraded to standard

  write_off_date           DATE            YES        \-            Write-off date

  status                   VARCHAR(20)     NO         ACTIVE        ACTIVE, UPGRADED, WRITTEN_OFF, RECOVERED

  \+ Audit Columns                                                  Standard audit columns
  ------------------------ --------------- ---------- ------------- ------------------------------------------

**3.2 NPA Classification Rules**

  -------------------- ------------ ------------------------- --------------------------- -------------------------
  **Classification**   **DPD**      **Provision - Secured**   **Provision - Unsecured**   **IRAC Category**

  STANDARD             0-89         0.40%                     0.40%                       Standard

  SMA_1                31-60        0.40%                     0.40%                       Standard (SMA)

  SMA_2                61-90        0.40%                     0.40%                       Standard (SMA)

  SUB_STANDARD         91-365       15%                       25%                         NPA - Sub-standard

  DOUBTFUL_1           366-730      25%                       100%                        NPA - Doubtful \< 1 yr

  DOUBTFUL_2           731-1095     40%                       100%                        NPA - Doubtful 1-3 yrs

  DOUBTFUL_3           \> 1095      100%                      100%                        NPA - Doubtful \> 3 yrs

  LOSS                 Identified   100%                      100%                        Loss Asset
  -------------------- ------------ ------------------------- --------------------------- -------------------------

**3.3 NPA Classification History (TXN_NPA_HISTORY)**

  --------------------- --------------- ---------- ------------- ------------------------------
  **Column**            **Type**        **Null**   **Default**   **Description**

  history_id            BIGSERIAL       NO         Auto          Primary Key

  npa_id                BIGINT          NO         \-            FK to TXN_NPA

  change_date           DATE            NO         \-            Classification change date

  from_classification   VARCHAR(20)     NO         \-            Previous classification

  to_classification     VARCHAR(20)     NO         \-            New classification

  from_provision_rate   NUMERIC(5,2)    NO         \-            Previous provision %

  to_provision_rate     NUMERIC(5,2)    NO         \-            New provision %

  provision_impact      NUMERIC(18,2)   NO         \-            Provision increase/decrease

  trigger               VARCHAR(30)     NO         \-            AUTO, MANUAL, REVIEW

  remarks               VARCHAR(500)    YES        \-            Change remarks

  \+ Audit Columns                                               Standard audit columns
  --------------------- --------------- ---------- ------------- ------------------------------

**3.4 Provisioning Entries**

  ---------------------------- -------------- -------------- ---------------------
  **Account**                  **Debit**      **Credit**     **Description**

  Provision Creation:                                        

  Provision Expense (P&L)      ₹ XX,XXX       \-             Provision charge

  Provision for NPAs (B/S)     \-             ₹ XX,XXX       Provision liability

  Provision Release:                                         

  Provision for NPAs           ₹ XX,XXX       \-             Release provision

  Provision Write-back (P&L)   \-             ₹ XX,XXX       Write-back income
  ---------------------------- -------------- -------------- ---------------------

**3.5 NPA Identification Flow**

**Step 1: Daily DPD Check** - Identify accounts crossing thresholds

SELECT \* FROM txn_loan_account

WHERE dpd \>= 90 AND asset_classification = \'STANDARD\'

**Step 2: Mark as NPA** - Create NPA record

INSERT INTO txn_npa (loan_account_id, npa_date, initial_classification=\'SUB_STANDARD\')

UPDATE txn_loan_account SET asset_classification=\'SUB_STANDARD\', npa_date=CURRENT_DATE

**Step 3: Calculate Provision** - Determine provision requirement

provision_amount = principal_outstanding × provision_rate

\-- Adjust for security coverage

**Step 4: Create Provision Entry** - Accounting entries

- Debit: Provision Expense

- Credit: Provision for Bad Debts

**Step 5: Notify Stakeholders** - Alerts and escalations

- Alert relationship manager

- Notify recovery team

- Escalate to management

**4. OTS (One-Time Settlement)**

Negotiated settlement with borrowers for NPA accounts.

**4.1 OTS Record (TXN_OTS)**

  ------------------------ --------------- ---------- ------------- --------------------------------------------------------------
  **Column**               **Type**        **Null**   **Default**   **Description**

  ots_id                   BIGSERIAL       NO         Auto          Primary Key

  loan_account_id          BIGINT          NO         \-            FK to TXN_LOAN_ACCOUNT

  npa_id                   BIGINT          NO         \-            FK to TXN_NPA

  ots_reference            VARCHAR(30)     NO         \-            OTS reference number

  ots_date                 DATE            NO         \-            OTS initiation date

  principal_outstanding    NUMERIC(18,2)   NO         \-            Principal O/S

  interest_outstanding     NUMERIC(18,2)   NO         \-            Interest O/S

  penal_outstanding        NUMERIC(18,2)   NO         \-            Penal O/S

  total_outstanding        NUMERIC(18,2)   NO         \-            Total O/S

  proposed_settlement      NUMERIC(18,2)   NO         \-            Proposed OTS amount

  haircut_amount           NUMERIC(18,2)   NO         \-            Write-off amount

  haircut_pct              NUMERIC(5,2)    NO         \-            Haircut percentage

  approved_settlement      NUMERIC(18,2)   YES        \-            Approved OTS amount

  payment_schedule         JSONB           YES        \-            Payment installments

  payment_deadline         DATE            YES        \-            Final payment date

  security_release_terms   TEXT            YES        \-            Security release conditions

  proposed_by              BIGINT          NO         \-            Proposer

  approved_by              BIGINT          YES        \-            Approving authority

  approval_date            DATE            YES        \-            Approval date

  committee_ref            VARCHAR(100)    YES        \-            Committee reference

  amount_received          NUMERIC(18,2)   NO         0             Amount received

  balance_pending          NUMERIC(18,2)   NO         \-            Balance to receive

  status                   VARCHAR(20)     NO         PROPOSED      PROPOSED, APPROVED, IN_PROGRESS, COMPLETED, FAILED, REJECTED

  completion_date          DATE            YES        \-            Settlement completion

  failure_reason           TEXT            YES        \-            If failed

  \+ Audit Columns                                                  Standard audit columns
  ------------------------ --------------- ---------- ------------- --------------------------------------------------------------

**4.2 OTS Approval Matrix**

  ------------------ ---------------------- ---------------------------
  **Haircut %**      **Write-off Amount**   **Approving Authority**

  Up to 10%          Up to ₹25 Lakhs        GM (Recovery)

  10-25%             ₹25 Lakhs - ₹1 Cr      ED

  25-40%             ₹1 Cr - ₹5 Cr          CMD

  40-50%             ₹5 Cr - ₹25 Cr         Board Committee

  \> 50%             \> ₹25 Cr              Full Board
  ------------------ ---------------------- ---------------------------

**5. Legal Module**

Legal documentation, verification, and recovery proceedings.

**5.1 Loan Documentation (TXN_LOAN_DOCUMENT)**

  ----------------------- --------------- ---------- ------------- ------------------------------------------------
  **Column**              **Type**        **Null**   **Default**   **Description**

  document_id             BIGSERIAL       NO         Auto          Primary Key

  loan_account_id         BIGINT          NO         \-            FK to TXN_LOAN_ACCOUNT

  document_type           VARCHAR(50)     NO         \-            LOAN_AGREEMENT, MORTGAGE_DEED, GUARANTEE, etc.

  document_number         VARCHAR(50)     YES        \-            Document reference

  document_date           DATE            NO         \-            Execution date

  description             VARCHAR(500)    YES        \-            Document description

  parties                 JSONB           YES        \-            Parties to document

  executed_by             JSONB           YES        \-            Signatories

  witnessed_by            JSONB           YES        \-            Witnesses

  stamp_duty              NUMERIC(18,2)   YES        \-            Stamp duty paid

  registration_required   BOOLEAN         NO         FALSE         Registration needed

  registration_number     VARCHAR(50)     YES        \-            Registration number

  registration_date       DATE            YES        \-            Registration date

  registrar_office        VARCHAR(200)    YES        \-            Registering office

  original_location       VARCHAR(200)    YES        \-            Where original stored

  file_path               VARCHAR(500)    YES        \-            Scanned copy path

  verified                BOOLEAN         NO         FALSE         Legally verified

  verified_by             BIGINT          YES        \-            Verifying lawyer

  verified_date           DATE            YES        \-            Verification date

  expiry_date             DATE            YES        \-            Document expiry

  status                  VARCHAR(20)     NO         ACTIVE        DRAFT, EXECUTED, REGISTERED, RELEASED

  \+ Audit Columns                                                 Standard audit columns
  ----------------------- --------------- ---------- ------------- ------------------------------------------------

**5.2 Standard Loan Documents**

  ------------------------------ ------------------------ ------------------------------ ----------------------
  **Document**                   **Registration**         **Parties**                    **Validity**

  Loan Agreement                 No                       Borrower, SMFC                 Loan tenure

  Deed of Hypothecation          CERSAI                   Borrower, SMFC                 Until release

  Mortgage Deed                  Sub-Registrar + CERSAI   Property owner, SMFC           Until release

  Personal Guarantee             No                       Guarantor, SMFC                Loan tenure + 3 yrs

  Corporate Guarantee            ROC (Form CHG-1)         Guarantor Co., SMFC            Loan tenure + 3 yrs

  Pledge Agreement               No                       Pledgor, SMFC                  Until release

  Escrow Agreement               No                       Borrower, SMFC, Escrow Agent   Project completion

  Power of Attorney              Sub-Registrar            Borrower, SMFC                 Until revoked

  Undertaking to Create Charge   No                       Borrower                       Until charge created
  ------------------------------ ------------------------ ------------------------------ ----------------------

**5.3 Legal Proceedings (TXN_LEGAL_CASE)**

Track legal actions for recovery.

  -------------------- --------------- ---------- ------------- ---------------------------------------------
  **Column**           **Type**        **Null**   **Default**   **Description**

  case_id              BIGSERIAL       NO         Auto          Primary Key

  loan_account_id      BIGINT          NO         \-            FK to TXN_LOAN_ACCOUNT

  case_reference       VARCHAR(50)     NO         \-            Case reference number

  case_type            VARCHAR(30)     NO         \-            SARFAESI, DRT, NCLT, CIVIL, ARBITRATION

  filing_date          DATE            NO         \-            Case filing date

  court_name           VARCHAR(200)    NO         \-            Court/Tribunal name

  jurisdiction         VARCHAR(100)    YES        \-            Jurisdiction

  case_number          VARCHAR(50)     YES        \-            Court case number

  claim_amount         NUMERIC(18,2)   NO         \-            Amount claimed

  lawyer_name          VARCHAR(200)    YES        \-            Advocate name

  lawyer_contact       VARCHAR(100)    YES        \-            Advocate contact

  opposing_party       VARCHAR(300)    YES        \-            Defendant/Respondent

  opposing_counsel     VARCHAR(200)    YES        \-            Opposing lawyer

  current_stage        VARCHAR(50)     YES        \-            Current stage

  next_hearing_date    DATE            YES        \-            Next hearing date

  last_order_date      DATE            YES        \-            Last order date

  last_order_summary   TEXT            YES        \-            Order summary

  possession_taken     BOOLEAN         NO         FALSE         Asset possession taken

  possession_date      DATE            YES        \-            Possession date

  auction_conducted    BOOLEAN         NO         FALSE         Auction done

  auction_date         DATE            YES        \-            Auction date

  sale_amount          NUMERIC(18,2)   YES        \-            Sale realization

  decree_amount        NUMERIC(18,2)   YES        \-            Decreed amount

  recovered_amount     NUMERIC(18,2)   NO         0             Amount recovered

  legal_expenses       NUMERIC(18,2)   NO         0             Legal costs

  status               VARCHAR(20)     NO         ACTIVE        ACTIVE, DECREED, CLOSED, SETTLED, WITHDRAWN

  closure_date         DATE            YES        \-            Case closure date

  closure_reason       VARCHAR(200)    YES        \-            Closure reason

  \+ Audit Columns                                              Standard audit columns
  -------------------- --------------- ---------- ------------- ---------------------------------------------

**5.4 Legal Case Types**

  -------------- ------------------------ ----------------------- ----------------------
  **Type**       **Act/Forum**            **Threshold**           **Timeline**

  SARFAESI       SARFAESI Act, 2002       \> ₹1 Lakh              60-90 days notice

  DRT            Debt Recovery Tribunal   \> ₹20 Lakhs            120-180 days

  NCLT           IBC, 2016                \> ₹1 Crore (default)   180-330 days CIRP

  CIVIL          Civil Court              Any amount              2-5 years

  ARBITRATION    As per agreement         Any amount              6-12 months

  CRIMINAL       NI Act (Sec 138)         Cheque bounce           Criminal proceedings
  -------------- ------------------------ ----------------------- ----------------------

**5.5 Case Hearing Log (TXN_CASE_HEARING)**

  ---------------------- --------------- ---------- ------------- ---------------------------------------
  **Column**             **Type**        **Null**   **Default**   **Description**

  hearing_id             BIGSERIAL       NO         Auto          Primary Key

  case_id                BIGINT          NO         \-            FK to TXN_LEGAL_CASE

  hearing_date           DATE            NO         \-            Hearing date

  hearing_type           VARCHAR(30)     YES        \-            ADMISSION, ARGUMENTS, EVIDENCE, ORDER

  proceedings            TEXT            YES        \-            Proceedings summary

  order_passed           TEXT            YES        \-            Order if any

  next_hearing_date      DATE            YES        \-            Next date fixed

  next_hearing_purpose   VARCHAR(200)    YES        \-            Purpose of next hearing

  attended_by            VARCHAR(200)    YES        \-            Who attended

  documents_filed        TEXT            YES        \-            Documents submitted

  expenses               NUMERIC(18,2)   YES        \-            Hearing expenses

  \+ Audit Columns                                                Standard audit columns
  ---------------------- --------------- ---------- ------------- ---------------------------------------

**6. Loan Restructuring**

Modification of loan terms for stressed accounts.

**6.1 Restructure Record (TXN_RESTRUCTURE)**

  ----------------------- --------------- ---------- ------------- ---------------------------------------------------
  **Column**              **Type**        **Null**   **Default**   **Description**

  restructure_id          BIGSERIAL       NO         Auto          Primary Key

  loan_account_id         BIGINT          NO         \-            FK to TXN_LOAN_ACCOUNT

  restructure_number      INTEGER         NO         \-            Restructure count (1, 2\...)

  restructure_date        DATE            NO         \-            Restructure effective date

  restructure_type        VARCHAR(30)     NO         \-            RESCHEDULEMENT, REDUCTION, CONVERSION, RBI_SCHEME

  reason                  TEXT            NO         \-            Restructure reason

  pre_outstanding         NUMERIC(18,2)   NO         \-            O/S before restructure

  post_outstanding        NUMERIC(18,2)   NO         \-            O/S after restructure

  old_tenure_months       INTEGER         NO         \-            Previous tenure

  new_tenure_months       INTEGER         NO         \-            New tenure

  old_rate                NUMERIC(5,2)    NO         \-            Previous rate

  new_rate                NUMERIC(5,2)    NO         \-            New rate

  old_emi                 NUMERIC(18,2)   YES        \-            Previous EMI

  new_emi                 NUMERIC(18,2)   YES        \-            New EMI

  moratorium_granted      INTEGER         YES        \-            Additional moratorium

  interest_capitalized    NUMERIC(18,2)   YES        \-            Interest added to principal

  waivers                 JSONB           YES        \-            Any waivers granted

  dpd_reset               BOOLEAN         NO         FALSE         DPD reset to 0

  classification_impact   VARCHAR(50)     YES        \-            Impact on classification

  rbi_scheme_ref          VARCHAR(100)    YES        \-            RBI scheme reference

  approved_by             BIGINT          NO         \-            Approving authority

  committee_ref           VARCHAR(100)    YES        \-            Committee reference

  status                  VARCHAR(20)     NO         APPROVED      PROPOSED, APPROVED, IMPLEMENTED, REJECTED

  \+ Audit Columns                                                 Standard audit columns
  ----------------------- --------------- ---------- ------------- ---------------------------------------------------

**6.2 Restructuring Types**

  ---------------- --------------------------- --------------------- -----------------------
  **Type**         **Description**             **Impact**            **Approval Level**

  RESCHEDULEMENT   Extend tenure, reduce EMI   No write-off          GM/ED based on amount

  REDUCTION        Reduce interest rate        Interest sacrifice    ED/CMD

  MORATORIUM       Payment holiday             Interest may accrue   GM/ED

  CONVERSION       Convert to equity/OCD       Debt reduction        Board

  HAIRCUT          Principal reduction         Write-off             Board

  RBI_SCHEME       As per regulatory scheme    Scheme-specific       As per scheme
  ---------------- --------------------------- --------------------- -----------------------

**7. Business Rules**

**7.1 Receipt Rules**

  ------------- ------------------------- --------------------------------------------- -------------------------
  **Rule ID**   **Rule**                  **Condition**                                 **Action**

  REC-001       Receipt \<= Outstanding   receipt_amount \> total_outstanding           Warn (excess)

  REC-002       Valid loan account        loan_account not found or closed              Block

  REC-003       Cheque clearance          Cheque receipts need clearance confirmation   Hold allocation

  REC-004       TDS certificate           If TDS claimed, certificate required          Warn

  REC-005       Bounce handling           Cheque bounced                                Reverse, charge penalty

  REC-006       Prepayment check          If prepayment, calculate penalty              Apply penalty
  ------------- ------------------------- --------------------------------------------- -------------------------

**7.2 NPA Rules**

  ------------- -------------------------- ----------------------------------------------- ----------------------------------
  **Rule ID**   **Rule**                   **Condition**                                   **Action**

  NPA-001       Auto NPA at 90 DPD         dpd \>= 90 AND classification = STANDARD        Mark NPA

  NPA-002       Upgrade eligibility        All overdues cleared AND current for 3 months   Allow upgrade

  NPA-003       Classification migration   DPD crosses threshold                           Auto-downgrade

  NPA-004       Provision calculation      Classification changes                          Recalculate provision

  NPA-005       Interest recognition       Account is NPA                                  Stop interest income recognition

  NPA-006       Write-off approval         Write-off proposal                              Route per delegation
  ------------- -------------------------- ----------------------------------------------- ----------------------------------

**7.3 Legal Rules**

  ------------- ----------------------- -------------------------------- ------------------------
  **Rule ID**   **Rule**                **Condition**                    **Action**

  LEG-001       SARFAESI threshold      Outstanding \> ₹1 Lakh secured   Enable SARFAESI

  LEG-002       DRT threshold           Outstanding \> ₹20 Lakhs         Enable DRT filing

  LEG-003       NCLT threshold          Default \> ₹1 Crore              Enable IBC proceedings

  LEG-004       Document verification   Loan document not verified       Block legal action

  LEG-005       Hearing tracking        Hearing date approaching         Alert legal team

  LEG-006       Expense tracking        Legal expenses incurred          Add to recovery amount
  ------------- ----------------------- -------------------------------- ------------------------

*\-\-- End of Phase 3 \-\--*

Phase 4 covers: Treasury (Payable Loans, ALM), Credit Risk
