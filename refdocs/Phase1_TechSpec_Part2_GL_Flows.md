**5. General Ledger Module - Transaction Tables**

This section defines all transaction tables for the General Ledger module including voucher entry, workflow, and GL postings.

**5.1 Voucher Header (TXN_VOUCHER)**

Main voucher header table storing voucher-level information.

**5.1.1 Table Definition**

  ------------------------ --------------- ---------- ------------- ---------------------------------------------------------------
  **Column**               **Type**        **Null**   **Default**   **Description**

  voucher_id               BIGSERIAL       NO         Auto          Primary Key

  org_id                   BIGINT          NO         \-            FK to MST_ORGANIZATION

  unit_id                  BIGINT          NO         \-            FK to MST_UNIT

  fy_id                    BIGINT          NO         \-            FK to MST_FINANCIAL_YEAR

  period_id                BIGINT          NO         \-            FK to MST_PERIOD

  voucher_type_id          BIGINT          NO         \-            FK to MST_VOUCHER_TYPE

  voucher_number           VARCHAR(30)     YES        \-            System/manual voucher number

  voucher_date             DATE            NO         \-            Transaction date

  posting_date             DATE            YES        \-            GL posting date

  reference_number         VARCHAR(50)     YES        \-            External reference

  reference_date           DATE            YES        \-            External reference date

  narration                TEXT            YES        \-            Voucher narration/description

  total_debit              NUMERIC(18,2)   NO         0             Sum of debit amounts

  total_credit             NUMERIC(18,2)   NO         0             Sum of credit amounts

  currency_id              BIGINT          NO         \-            FK to MST_CURRENCY

  exchange_rate            NUMERIC(12,6)   NO         1             Rate to base currency

  base_total_debit         NUMERIC(18,2)   NO         0             Debit in base currency

  base_total_credit        NUMERIC(18,2)   NO         0             Credit in base currency

  bank_account_id          BIGINT          YES        \-            FK to MST_BANK_ACCOUNT

  cheque_number            VARCHAR(20)     YES        \-            Cheque/DD number

  cheque_date              DATE            YES        \-            Cheque date

  payment_mode             VARCHAR(20)     YES        \-            CHEQUE, RTGS, NEFT, CASH, DD

  source_module            VARCHAR(30)     YES        \-            Originating module (LOS, HR, etc.)

  source_document_id       BIGINT          YES        \-            Source document reference

  source_document_type     VARCHAR(50)     YES        \-            Source document type

  is_auto_generated        BOOLEAN         NO         FALSE         System generated voucher

  is_reversal              BOOLEAN         NO         FALSE         Reversal voucher flag

  reversed_voucher_id      BIGINT          YES        \-            Original voucher if reversal

  reversal_voucher_id      BIGINT          YES        \-            Reversal voucher if reversed

  reversal_reason          VARCHAR(500)    YES        \-            Reason for reversal

  status                   VARCHAR(20)     NO         DRAFT         DRAFT, PENDING_APPROVAL, APPROVED, POSTED, REVERSED, REJECTED

  current_approval_level   INTEGER         YES        \-            Current workflow level

  rejection_reason         VARCHAR(500)    YES        \-            Reason if rejected

  attachment_count         INTEGER         NO         0             Number of attachments

  \+ Audit Columns                                                  Standard audit columns
  ------------------------ --------------- ---------- ------------- ---------------------------------------------------------------

**5.1.2 Indexes**

PRIMARY KEY (voucher_id)

UNIQUE INDEX idx_voucher_number ON txn_voucher(org_id, unit_id, fy_id, voucher_type_id, voucher_number) WHERE voucher_number IS NOT NULL

INDEX idx_voucher_date ON txn_voucher(voucher_date)

INDEX idx_voucher_status ON txn_voucher(status)

INDEX idx_voucher_unit ON txn_voucher(unit_id)

INDEX idx_voucher_period ON txn_voucher(period_id)

INDEX idx_voucher_type ON txn_voucher(voucher_type_id)

INDEX idx_voucher_source ON txn_voucher(source_module, source_document_id)

**5.2 Voucher Lines (TXN_VOUCHER_LINE)**

Individual debit/credit line items for each voucher.

**5.2.1 Table Definition**

  ---------------------- --------------- ---------- ------------- --------------------------------
  **Column**             **Type**        **Null**   **Default**   **Description**

  line_id                BIGSERIAL       NO         Auto          Primary Key

  voucher_id             BIGINT          NO         \-            FK to TXN_VOUCHER

  line_number            INTEGER         NO         \-            Line sequence (1, 2, 3\...)

  account_id             BIGINT          NO         \-            FK to MST_COA

  debit_amount           NUMERIC(18,2)   NO         0             Debit amount (0 if credit)

  credit_amount          NUMERIC(18,2)   NO         0             Credit amount (0 if debit)

  base_debit_amount      NUMERIC(18,2)   NO         0             Debit in base currency

  base_credit_amount     NUMERIC(18,2)   NO         0             Credit in base currency

  cost_center_id         BIGINT          YES        \-            FK to MST_COST_CENTER

  party_type             VARCHAR(30)     YES        \-            CUSTOMER, VENDOR, EMPLOYEE

  party_id               BIGINT          YES        \-            FK to respective party master

  party_name             VARCHAR(200)    YES        \-            Denormalized party name

  narration              VARCHAR(500)    YES        \-            Line-level narration

  due_date               DATE            YES        \-            Expected settlement date

  disposal_date          DATE            YES        \-            For current/non-current

  allocation_type        VARCHAR(30)     YES        \-            NEW, AGAINST_REF, ON_ACCOUNT

  reference_voucher_id   BIGINT          YES        \-            FK to TXN_VOUCHER (allocation)

  reference_line_id      BIGINT          YES        \-            FK to TXN_VOUCHER_LINE

  tds_section_id         BIGINT          YES        \-            FK to MST_TDS_SECTION

  tds_rate               NUMERIC(5,2)    YES        \-            TDS rate applied

  tds_amount             NUMERIC(18,2)   YES        \-            TDS deducted

  gst_rate               NUMERIC(5,2)    YES        \-            GST rate

  gst_amount             NUMERIC(18,2)   YES        \-            GST amount

  is_interunit           BOOLEAN         NO         FALSE         Inter-unit transaction

  counterpart_unit_id    BIGINT          YES        \-            Other unit in interunit txn

  advice_number          VARCHAR(30)     YES        \-            Interunit advice number

  employee_id            BIGINT          YES        \-            FK to employee (for emp loans)

  asset_id               BIGINT          YES        \-            FK to fixed asset

  additional_data        JSONB           YES        \-            Module-specific extra data

  \+ Audit Columns                                                Standard audit columns
  ---------------------- --------------- ---------- ------------- --------------------------------

**5.2.2 Indexes**

PRIMARY KEY (line_id)

INDEX idx_vline_voucher ON txn_voucher_line(voucher_id)

INDEX idx_vline_account ON txn_voucher_line(account_id)

INDEX idx_vline_party ON txn_voucher_line(party_type, party_id) WHERE party_id IS NOT NULL

INDEX idx_vline_cc ON txn_voucher_line(cost_center_id) WHERE cost_center_id IS NOT NULL

INDEX idx_vline_reference ON txn_voucher_line(reference_voucher_id) WHERE reference_voucher_id IS NOT NULL

**5.3 Voucher Workflow (TXN_VOUCHER_WORKFLOW)**

Tracks approval workflow history for each voucher.

**5.3.1 Table Definition**

  ------------------ -------------- ---------- ------------- ----------------------------------------------------
  **Column**         **Type**       **Null**   **Default**   **Description**

  workflow_id        BIGSERIAL      NO         Auto          Primary Key

  voucher_id         BIGINT         NO         \-            FK to TXN_VOUCHER

  approval_level     INTEGER        NO         \-            Workflow level (1, 2, 3\...)

  approver_user_id   BIGINT         NO         \-            FK to MST_USER

  action             VARCHAR(20)    NO         \-            SUBMITTED, APPROVED, REJECTED, RETURNED, ESCALATED

  action_date        TIMESTAMPTZ    NO         NOW()         When action was taken

  comments           VARCHAR(500)   YES        \-            Approver comments

  from_status        VARCHAR(20)    NO         \-            Status before action

  to_status          VARCHAR(20)    NO         \-            Status after action

  sla_due_at         TIMESTAMPTZ    YES        \-            SLA deadline

  is_sla_breached    BOOLEAN        NO         FALSE         SLA breached flag

  \+ Audit Columns                                           Standard audit columns
  ------------------ -------------- ---------- ------------- ----------------------------------------------------

**5.3.2 Sample Workflow Trail**

  ----------- ----------------- ------------ ------------------ ------------------ -----------------------------
  **Level**   **User**          **Action**   **From Status**    **To Status**      **Comments**

  1           Clerk (Creator)   SUBMITTED    DRAFT              PENDING_APPROVAL   Submitted for approval

  1           Finance Officer   APPROVED     PENDING_APPROVAL   PENDING_APPROVAL   L1 Approved

  2           Sr. Manager       RETURNED     PENDING_APPROVAL   DRAFT              Please attach invoice

  1           Clerk             SUBMITTED    DRAFT              PENDING_APPROVAL   Resubmitted with attachment

  1           Finance Officer   APPROVED     PENDING_APPROVAL   PENDING_APPROVAL   L1 Re-approved

  2           Sr. Manager       APPROVED     PENDING_APPROVAL   APPROVED           Final approval
  ----------- ----------------- ------------ ------------------ ------------------ -----------------------------

**5.4 Period Management (MST_PERIOD)**

Accounting periods within financial year for period-based transaction control.

**5.4.1 Table Definition**

  ---------------------- -------------- ---------- ------------- --------------------------------
  **Column**             **Type**       **Null**   **Default**   **Description**

  period_id              BIGSERIAL      NO         Auto          Primary Key

  org_id                 BIGINT         NO         \-            FK to MST_ORGANIZATION

  fy_id                  BIGINT         NO         \-            FK to MST_FINANCIAL_YEAR

  period_number          INTEGER        NO         \-            Period sequence (1-12 or 1-13)

  period_name            VARCHAR(50)    NO         \-            Display name (Apr-2025)

  start_date             DATE           NO         \-            Period start date

  end_date               DATE           NO         \-            Period end date

  is_adjustment_period   BOOLEAN        NO         FALSE         Year-end adjustment period

  status                 VARCHAR(20)    NO         OPEN          OPEN, SOFT_CLOSED, HARD_CLOSED

  closed_at              TIMESTAMPTZ    YES        \-            When period was closed

  closed_by              BIGINT         YES        \-            User who closed period

  reopened_at            TIMESTAMPTZ    YES        \-            Last reopen timestamp

  reopened_by            BIGINT         YES        \-            User who reopened

  reopen_reason          VARCHAR(500)   YES        \-            Reason for reopening

  \+ Audit Columns                                               Standard audit columns
  ---------------------- -------------- ---------- ------------- --------------------------------

**5.4.2 Period Status Definitions**

  ------------- ---------------- -------------- ---------------- -------------- -----------------------------
  **Status**    **Can Create**   **Can Edit**   **Can Delete**   **Can Post**   **Use Case**

  OPEN          Yes              Yes            Yes              Yes            Normal operations

  SOFT_CLOSED   No               Yes\*          No               Yes\*          Month-end, adjustments only

  HARD_CLOSED   No               No             No               No             Finalized, audit-ready
  ------------- ---------------- -------------- ---------------- -------------- -----------------------------

\* With special permission only

**5.4.3 Business Rules**

  ------------- -------------------------- -------------------------------------- --------------------------------
  **Rule ID**   **Rule**                   **Validation**                         **Error Message**

  PER-001       Sequential periods         Periods must be sequential within FY   Invalid period sequence

  PER-002       No gaps                    No date gaps between periods           Gap between periods

  PER-003       No overlaps                Period dates cannot overlap            Overlapping periods

  PER-004       Close in sequence          Cannot close if previous period open   Close previous period first

  PER-005       Reopen requires approval   Special permission to reopen closed    Insufficient permission

  PER-006       Adjustment period last     Period 13 (if exists) must be last     Adjustment period must be last
  ------------- -------------------------- -------------------------------------- --------------------------------

**5.5 GL Postings (TXN_GL_POSTING)**

Actual general ledger postings created when voucher is posted. This is the final book of record.

**5.5.1 Table Definition**

  --------------------- --------------- ---------- ------------- --------------------------------
  **Column**            **Type**        **Null**   **Default**   **Description**

  posting_id            BIGSERIAL       NO         Auto          Primary Key

  org_id                BIGINT          NO         \-            FK to MST_ORGANIZATION

  unit_id               BIGINT          NO         \-            FK to MST_UNIT

  fy_id                 BIGINT          NO         \-            FK to MST_FINANCIAL_YEAR

  period_id             BIGINT          NO         \-            FK to MST_PERIOD

  posting_date          DATE            NO         \-            GL posting date

  voucher_id            BIGINT          NO         \-            FK to TXN_VOUCHER

  voucher_line_id       BIGINT          NO         \-            FK to TXN_VOUCHER_LINE

  account_id            BIGINT          NO         \-            FK to MST_COA

  debit_amount          NUMERIC(18,2)   NO         0             Debit in transaction currency

  credit_amount         NUMERIC(18,2)   NO         0             Credit in transaction currency

  currency_id           BIGINT          NO         \-            FK to MST_CURRENCY

  exchange_rate         NUMERIC(12,6)   NO         1             Exchange rate

  base_debit_amount     NUMERIC(18,2)   NO         0             Debit in base currency

  base_credit_amount    NUMERIC(18,2)   NO         0             Credit in base currency

  cost_center_id        BIGINT          YES        \-            FK to MST_COST_CENTER

  party_type            VARCHAR(30)     YES        \-            CUSTOMER, VENDOR, EMPLOYEE

  party_id              BIGINT          YES        \-            Party reference

  running_balance       NUMERIC(18,2)   YES        \-            Running balance (computed)

  is_reversed           BOOLEAN         NO         FALSE         If posting was reversed

  reversal_posting_id   BIGINT          YES        \-            FK to reversal posting

  \+ Audit Columns                                               Standard audit columns
  --------------------- --------------- ---------- ------------- --------------------------------

**5.5.2 Indexes**

PRIMARY KEY (posting_id)

INDEX idx_glpost_account ON txn_gl_posting(account_id, posting_date)

INDEX idx_glpost_voucher ON txn_gl_posting(voucher_id)

INDEX idx_glpost_period ON txn_gl_posting(period_id)

INDEX idx_glpost_party ON txn_gl_posting(party_type, party_id) WHERE party_id IS NOT NULL

INDEX idx_glpost_date ON txn_gl_posting(posting_date)

INDEX idx_glpost_cc ON txn_gl_posting(cost_center_id) WHERE cost_center_id IS NOT NULL

**5.5.3 Constraints**

CHECK (debit_amount \>= 0 AND credit_amount \>= 0)

CHECK (NOT (debit_amount \> 0 AND credit_amount \> 0)) \-- Cannot have both

CHECK (debit_amount \> 0 OR credit_amount \> 0) \-- Must have one

**5.6 Voucher Attachments (TXN_VOUCHER_ATTACHMENT)**

Stores document attachments for vouchers (scanned bills, invoices, etc.).

**5.6.1 Table Definition**

  ------------------ -------------- ---------- ------------- -----------------------------
  **Column**         **Type**       **Null**   **Default**   **Description**

  attachment_id      BIGSERIAL      NO         Auto          Primary Key

  voucher_id         BIGINT         NO         \-            FK to TXN_VOUCHER

  file_name          VARCHAR(255)   NO         \-            Original file name

  file_type          VARCHAR(50)    NO         \-            MIME type

  file_size          INTEGER        NO         \-            Size in bytes

  file_path          VARCHAR(500)   NO         \-            Storage path

  description        VARCHAR(200)   YES        \-            Attachment description

  is_primary         BOOLEAN        NO         FALSE         Primary supporting document

  \+ Audit Columns                                           Standard audit columns
  ------------------ -------------- ---------- ------------- -----------------------------

**6. Business Flows**

Detailed step-by-step flows for all major processes in the GL module.

**6.1 Voucher Creation Flow**

Complete flow from voucher initiation to draft save.

**TRIGGER: User clicks \'New Voucher\' or system initiates auto-voucher**

**Step 1: Initialize Voucher** - Create voucher header with default values

- Set org_id, unit_id from user context

- Set fy_id from current active FY

- Set voucher_date to current date

- Set status = \'DRAFT\'

- Set currency_id to base currency (INR)

**Step 2: Select Voucher Type** - User selects voucher type (JV, BPV, BRV, etc.)

- VALIDATE: Voucher type must be ACTIVE

- VALIDATE: User must have permission for this voucher type

- Load default accounts if configured

**Step 3: Select Period** - Determine accounting period

- Auto-select period based on voucher_date

- VALIDATE: Period must be OPEN

- VALIDATE: If SOFT_CLOSED, user needs special permission

- ERROR: \'Cannot create voucher in closed period\'

**Step 4: Enter Header Details** - Capture voucher header information

- Enter reference_number (optional)

- Enter narration (validate if required by voucher type)

- Select currency (if multi-currency enabled)

- If foreign currency, fetch/enter exchange_rate

**Step 5: Add Line Items** - Enter debit/credit lines

- For each line: Select account from COA

- VALIDATE: Account must not be GROUP account

- VALIDATE: Account must be ACTIVE

- Enter debit_amount OR credit_amount (not both)

- If account.is_party_account = TRUE, select party

- If account.is_cost_center_reqd = TRUE, select cost center

- Capture additional fields based on account type (TDS, GST, etc.)

**Step 6: Validate Totals** - Ensure voucher is balanced

- Calculate total_debit = SUM(debit_amount)

- Calculate total_credit = SUM(credit_amount)

- VALIDATE: total_debit MUST EQUAL total_credit

- ERROR: \'Voucher is not balanced. Difference: {amount}\'

**Step 7: Save Draft** - Persist voucher to database

BEGIN TRANSACTION

INSERT INTO txn_voucher (header fields\...)

FOR EACH line:

INSERT INTO txn_voucher_line (line fields\...)

UPDATE attachment_count if attachments added

COMMIT

**Step 8: Output** - Return result to user

- Display voucher in DRAFT status

- Show options: Edit, Submit for Approval, Delete

**6.2 Voucher Approval Flow**

Multi-level approval workflow for vouchers.

**TRIGGER: User clicks \'Submit for Approval\' on DRAFT voucher**

**Step 1: Validate Submission** - Pre-submission checks

- VALIDATE: Voucher status must be DRAFT

- VALIDATE: Voucher must be balanced

- VALIDATE: All mandatory fields populated

- VALIDATE: Period is still OPEN

**Step 2: Determine Approval Matrix** - Find applicable approval levels

SELECT \* FROM mst_approval_matrix

WHERE (voucher_type_id = :vtype OR voucher_type_id IS NULL)

AND (unit_id = :unit OR unit_id IS NULL)

AND :amount BETWEEN min_amount AND COALESCE(max_amount, 999999999)

AND status = \'ACTIVE\'

ORDER BY approval_level

**Step 3: Submit to Level 1** - Initiate workflow

BEGIN TRANSACTION

UPDATE txn_voucher SET

status = \'PENDING_APPROVAL\',

current_approval_level = 1

INSERT INTO txn_voucher_workflow (

voucher_id, approval_level, approver_user_id,

action = \'SUBMITTED\', from_status = \'DRAFT\',

to_status = \'PENDING_APPROVAL\', sla_due_at)

COMMIT

**Step 4: Notify Approver** - Send notifications

- Email notification to Level 1 approver(s)

- In-app notification with link to voucher

- SMS notification if enabled

**Step 5: Approver Action** - Process approver decision

**Decision Point: APPROVE / REJECT / RETURN**

**If APPROVE:**

- Check if more levels pending

- If yes: Move to next level, repeat from Step 4

- If no: Set status = \'APPROVED\'

**If REJECT:**

UPDATE txn_voucher SET status = \'REJECTED\', rejection_reason = :reason

INSERT INTO txn_voucher_workflow (action = \'REJECTED\', comments = :reason)

- Notify creator about rejection

**If RETURN:**

UPDATE txn_voucher SET status = \'DRAFT\', current_approval_level = NULL

INSERT INTO txn_voucher_workflow (action = \'RETURNED\', comments = :reason)

- Notify creator to make corrections and resubmit

**6.3 Voucher Posting Flow**

Post approved voucher to General Ledger.

**TRIGGER: User clicks \'Post\' on APPROVED voucher OR Batch posting job**

**Step 1: Pre-posting Validation** - Final checks before posting

- VALIDATE: Status must be APPROVED

- VALIDATE: User has GL_VOUCHER_POST permission

- VALIDATE: Period is OPEN or SOFT_CLOSED

- VALIDATE: Voucher not already posted

**Step 2: Generate Voucher Number** - If auto-numbering enabled

SELECT last_number FROM mst_voucher_numbering

WHERE voucher_type_id = :type AND unit_id = :unit AND fy_id = :fy

FOR UPDATE \-- Lock row

new_number = last_number + 1

voucher_number = format(prefix + new_number, format_pattern)

\-- Example: JV/DEL/2025-26/00001

UPDATE mst_voucher_numbering SET last_number = new_number

**Step 3: Create GL Postings** - Insert into GL posting table

BEGIN TRANSACTION

\-- Update voucher header

UPDATE txn_voucher SET

status = \'POSTED\',

voucher_number = :generated_number,

posting_date = CURRENT_DATE

\-- Create GL postings for each line

FOR EACH voucher_line:

INSERT INTO txn_gl_posting (

org_id, unit_id, fy_id, period_id, posting_date,

voucher_id, voucher_line_id, account_id,

debit_amount, credit_amount, currency_id, exchange_rate,

base_debit_amount, base_credit_amount,

cost_center_id, party_type, party_id)

COMMIT

**Step 4: Update Account Balances** - Refresh materialized views/caches

- Update account running balances if maintained

- Invalidate trial balance cache for period

- Queue balance recalculation job

**Step 5: Post-posting Actions** - Downstream processing

- If bank voucher: Create BRS entry

- If TDS deducted: Update TDS register

- If inter-unit: Generate advice number

- Send posting confirmation notification

**6.4 Voucher Reversal Flow**

Reverse a posted voucher (creates contra entry).

**TRIGGER: User requests reversal of POSTED voucher**

**Step 1: Validate Reversal** - Check if reversal is allowed

- VALIDATE: Original voucher status = POSTED

- VALIDATE: Voucher not already reversed

- VALIDATE: User has GL_VOUCHER_REVERSE permission

- VALIDATE: Reversal period is OPEN

- VALIDATE: Reason provided

**Step 2: Create Reversal Voucher** - Generate new voucher with opposite entries

BEGIN TRANSACTION

\-- Create reversal voucher header

INSERT INTO txn_voucher (

\...copy from original\...,

voucher_type_id = (SELECT type for \'REV\'),

is_reversal = TRUE,

reversed_voucher_id = :original_voucher_id,

reversal_reason = :reason,

status = \'APPROVED\' \-- Skip workflow for reversals

)

\-- Create reversal lines (swap debit/credit)

FOR EACH original_line:

INSERT INTO txn_voucher_line (

debit_amount = original.credit_amount,

credit_amount = original.debit_amount,

\...rest same as original\...

)

\-- Mark original as reversed

UPDATE txn_voucher SET

reversal_voucher_id = :new_reversal_id

WHERE voucher_id = :original_voucher_id

\-- Mark GL postings as reversed

UPDATE txn_gl_posting SET is_reversed = TRUE

WHERE voucher_id = :original_voucher_id

COMMIT

**Step 3: Post Reversal** - Create reversal GL postings

- Follow standard posting flow (Section 6.3)

- Link reversal_posting_id in original postings

**Step 4: Notify** - Inform stakeholders

- Notify original voucher creator

- Notify approvers

- Log audit entry

**7. Complete Business Rules & Validations**

Comprehensive list of all business rules with validation logic and error handling.

**7.1 Voucher Entry Rules**

  ------------- ----------------------- --------------------------------------------------- -------------------- ---------------------
  **Rule ID**   **Rule Name**           **Condition**                                       **Action**           **Error Code**

  VCH-001       Balanced Voucher        total_debit != total_credit                         Block Save           ERR_VCH_UNBALANCED

  VCH-002       Period Open             period.status NOT IN (\'OPEN\', \'SOFT_CLOSED\')    Block Save           ERR_PERIOD_CLOSED

  VCH-003       Valid Date Range        voucher_date NOT IN fy.date_range                   Block Save           ERR_DATE_OUTSIDE_FY

  VCH-004       No Future Date          voucher_date \> CURRENT_DATE                        Warning              WARN_FUTURE_DATE

  VCH-005       Back Date Auth          voucher_date \< CURRENT_DATE - 7                    Require Admin Auth   ERR_BACKDATE_AUTH

  VCH-006       Minimum Lines           line_count \< 2                                     Block Save           ERR_MIN_LINES

  VCH-007       Narration Required      vtype.requires_narration AND narration IS NULL      Block Save           ERR_NARRATION_REQD

  VCH-008       Bank Account Required   vtype.is_bank_voucher AND bank_account_id IS NULL   Block Save           ERR_BANK_REQD

  VCH-009       Cheque Required         vtype.requires_cheque AND cheque_number IS NULL     Block Save           ERR_CHEQUE_REQD

  VCH-010       Valid Exchange Rate     currency != base AND exchange_rate \<= 0            Block Save           ERR_INVALID_RATE
  ------------- ----------------------- --------------------------------------------------- -------------------- ---------------------

**7.2 Voucher Line Rules**

  ------------- ------------------- --------------------------------------------------------------------- ------------ -------------------------
  **Rule ID**   **Rule Name**       **Condition**                                                         **Action**   **Error Code**

  LIN-001       Valid Account       account.is_deleted = TRUE OR status != \'ACTIVE\'                     Block        ERR_INVALID_ACCOUNT

  LIN-002       Not Group Account   account.is_group = TRUE                                               Block        ERR_GROUP_ACCOUNT

  LIN-003       One Side Only       debit_amount \> 0 AND credit_amount \> 0                              Block        ERR_BOTH_DR_CR

  LIN-004       Positive Amount     debit_amount \< 0 OR credit_amount \< 0                               Block        ERR_NEGATIVE_AMOUNT

  LIN-005       Party Required      account.is_party_account AND party_id IS NULL                         Block        ERR_PARTY_REQD

  LIN-006       Cost Center Reqd    account.is_cost_center_reqd AND cost_center_id IS NULL                Block        ERR_CC_REQD

  LIN-007       Valid Party Type    account.subledger_type != party_type                                  Block        ERR_PARTY_TYPE_MISMATCH

  LIN-008       Disposal Date       account.type IN (\'ASSET\',\'LIABILITY\') AND disposal_date IS NULL   Warning      WARN_DISPOSAL_DATE

  LIN-009       TDS Validation      tds_section_id IS NOT NULL AND tds_rate IS NULL                       Block        ERR_TDS_RATE_REQD

  LIN-010       Interunit Advice    is_interunit = TRUE AND advice_number IS NULL                         Block        ERR_ADVICE_REQD
  ------------- ------------------- --------------------------------------------------------------------- ------------ -------------------------

**7.3 Approval Rules**

  ------------- -------------------- ------------------------------------------------ --------------- ----------------------
  **Rule ID**   **Rule Name**        **Condition**                                    **Action**      **Error Code**

  APR-001       Self Approve Check   approver_id = creator_id AND !can_self_approve   Block           ERR_SELF_APPROVE

  APR-002       Permission Check     User lacks APPROVE permission                    Block           ERR_NO_APPROVE_PERM

  APR-003       Sequence Check       Trying to approve without prior levels done      Block           ERR_LEVEL_SEQUENCE

  APR-004       Amount Authority     amount \> user.max_approval_limit                Block           ERR_EXCEEDS_LIMIT

  APR-005       SLA Breach           CURRENT_TIME \> sla_due_at                       Auto-Escalate   WARN_SLA_BREACH

  APR-006       Already Actioned     Level already has action                         Block           ERR_ALREADY_ACTIONED

  APR-007       Reject Reason        action = REJECT AND comments IS NULL             Block           ERR_REJECT_REASON
  ------------- -------------------- ------------------------------------------------ --------------- ----------------------

**7.4 Posting Rules**

  ------------- ----------------- ---------------------------------- ------------ --------------------
  **Rule ID**   **Rule Name**     **Condition**                      **Action**   **Error Code**

  PST-001       Approved Only     status != \'APPROVED\'             Block        ERR_NOT_APPROVED

  PST-002       Period Check      period.status = \'HARD_CLOSED\'    Block        ERR_PERIOD_CLOSED

  PST-003       Duplicate Check   voucher.status = \'POSTED\'        Block        ERR_ALREADY_POSTED

  PST-004       Number Lock       Could not acquire numbering lock   Retry        ERR_NUMBER_LOCK

  PST-005       FY Check          fy.status = \'CLOSED\'             Block        ERR_FY_CLOSED
  ------------- ----------------- ---------------------------------- ------------ --------------------

**7.5 Reversal Rules**

  ------------- ------------------- ------------------------------------------ ------------ ------------------------
  **Rule ID**   **Rule Name**       **Condition**                              **Action**   **Error Code**

  REV-001       Posted Only         original.status != \'POSTED\'              Block        ERR_NOT_POSTED

  REV-002       Not Reversed        original.reversal_voucher_id IS NOT NULL   Block        ERR_ALREADY_REVERSED

  REV-003       Reason Required     reversal_reason IS NULL                    Block        ERR_REASON_REQD

  REV-004       Open Period         target_period.status = \'HARD_CLOSED\'     Block        ERR_REVERSAL_PERIOD

  REV-005       Permission Check    User lacks REVERSE permission              Block        ERR_NO_REVERSE_PERM

  REV-006       Same FY Preferred   reversal.fy_id != original.fy_id           Warning      WARN_CROSS_FY_REVERSAL
  ------------- ------------------- ------------------------------------------ ------------ ------------------------

**8. State Machines**

State transition diagrams for key entities.

**8.1 Voucher Status State Machine**

  ------------------ --------------------- ------------------ ------------------------------- ----------------------------------------
  **From State**     **Event/Action**      **To State**       **Conditions**                  **Side Effects**

  (new)              CREATE                DRAFT              User has CREATE permission      Voucher record created

  DRAFT              SUBMIT                PENDING_APPROVAL   Voucher balanced, period open   Workflow initiated, notifications sent

  DRAFT              DELETE                (deleted)          No postings exist               Soft delete, audit log

  PENDING_APPROVAL   APPROVE (final)       APPROVED           All levels approved             Ready for posting

  PENDING_APPROVAL   APPROVE (not final)   PENDING_APPROVAL   More levels pending             Move to next level

  PENDING_APPROVAL   REJECT                REJECTED           Rejection reason provided       Notify creator

  PENDING_APPROVAL   RETURN                DRAFT              Return comments provided        Reset workflow

  APPROVED           POST                  POSTED             User has POST permission        GL entries created, number assigned

  POSTED             REVERSE               POSTED\*           Reversal voucher created        Original marked reversed

  REJECTED           REOPEN                DRAFT              Admin permission                Can edit and resubmit
  ------------------ --------------------- ------------------ ------------------------------- ----------------------------------------

**8.1.1 Status Transition Diagram (Text)**

+\--\[DELETE\]\-\--\> (DELETED)

\|

(NEW) \--\[CREATE\]\--\> DRAFT \--\[SUBMIT\]\--\> PENDING_APPROVAL

\^ \| \| \|

\| \| \| +\--\[APPROVE\]\--\> APPROVED \--\[POST\]\--\> POSTED

\| \| \| \|

+\-\-\--\[RETURN\]\-\-\-\-\-\-\-\--+ \| \|

\| \[REVERSE\]\-\-\-\-\--+

\|

+\--\[REJECT\]\--\> REJECTED \--\[REOPEN\]\--\> DRAFT

**8.2 Period Status State Machine**

  ---------------- ------------------ -------------- -------------------------- -----------------------------------
  **From State**   **Event/Action**   **To State**   **Conditions**             **Side Effects**

  (new)            CREATE             OPEN           FY is OPEN                 Period available for transactions

  OPEN             SOFT_CLOSE         SOFT_CLOSED    All vouchers processed     Only adjustments allowed

  SOFT_CLOSED      REOPEN             OPEN           Admin approval             Audit log entry

  SOFT_CLOSED      HARD_CLOSE         HARD_CLOSED    All reconciliations done   No more transactions

  HARD_CLOSED      REOPEN             SOFT_CLOSED    Auditor override only      Requires special auth
  ---------------- ------------------ -------------- -------------------------- -----------------------------------

**9. API Contracts**

RESTful API specifications for key operations.

**9.1 Voucher APIs**

**POST /api/v1/vouchers - Create Voucher**

Request Body:

{

\"unit_id\": 1,

\"voucher_type_id\": 1,

\"voucher_date\": \"2026-01-15\",

\"reference_number\": \"INV-2026-001\",

\"narration\": \"Payment for services\",

\"currency_id\": 1,

\"exchange_rate\": 1.0,

\"bank_account_id\": null,

\"lines\": \[

{

\"account_id\": 1001,

\"debit_amount\": 10000.00,

\"credit_amount\": 0,

\"cost_center_id\": 5,

\"party_type\": \"VENDOR\",

\"party_id\": 101,

\"narration\": \"Consulting fees\"

},

{

\"account_id\": 2001,

\"debit_amount\": 0,

\"credit_amount\": 10000.00,

\"party_type\": null,

\"party_id\": null

}

\]

}

Response (201 Created):

{

\"voucher_id\": 12345,

\"status\": \"DRAFT\",

\"message\": \"Voucher created successfully\"

}

**POST /api/v1/vouchers/{id}/submit - Submit for Approval**

Request: No body required

Response (200 OK):

{

\"voucher_id\": 12345,

\"status\": \"PENDING_APPROVAL\",

\"current_level\": 1,

\"pending_with\": \"Finance Officer\",

\"sla_due_at\": \"2026-01-16T14:00:00Z\"

}

**POST /api/v1/vouchers/{id}/approve - Approve Voucher**

Request Body:

{

\"action\": \"APPROVE\", // APPROVE, REJECT, RETURN

\"comments\": \"Approved after verification\"

}

**POST /api/v1/vouchers/{id}/post - Post Voucher**

Request: No body required

Response (200 OK):

{

\"voucher_id\": 12345,

\"voucher_number\": \"JV/HO/2025-26/00042\",

\"status\": \"POSTED\",

\"posting_date\": \"2026-01-15\",

\"gl_postings_count\": 2

}

**10. Audit Requirements**

Comprehensive audit logging specifications.

**10.1 Audit Log Table (AUD_ACTION_LOG)**

  -------------- -------------- ----------------------------------------
  **Column**     **Type**       **Description**

  log_id         BIGSERIAL      Primary Key

  timestamp      TIMESTAMPTZ    When action occurred

  user_id        BIGINT         Who performed action

  user_ip        VARCHAR(50)    IP address

  session_id     VARCHAR(100)   Session identifier

  module         VARCHAR(50)    Module code (GL, AR, AP)

  entity_type    VARCHAR(50)    Table/entity name

  entity_id      BIGINT         Record ID

  action         VARCHAR(30)    CREATE, UPDATE, DELETE, VIEW, EXPORT

  old_values     JSONB          Previous values (for UPDATE)

  new_values     JSONB          New values

  description    TEXT           Human-readable description
  -------------- -------------- ----------------------------------------

**10.2 Mandatory Audit Events**

  --------------------------- ------------ ------------------------------------- ---------------
  **Event**                   **Module**   **Data to Capture**                   **Retention**

  Voucher Created             GL           Full voucher with lines               7 years

  Voucher Submitted           GL           Voucher ID, submitter, timestamp      7 years

  Voucher Approved/Rejected   GL           Approver, action, comments            7 years

  Voucher Posted              GL           Voucher number, posting date          7 years

  Voucher Reversed            GL           Original + reversal details, reason   7 years

  Period Opened/Closed        GL           Period, user, reason                  7 years

  COA Created/Modified        GL           Full account record                   Permanent

  User Login/Logout           AUTH         User, IP, timestamp, success/fail     2 years

  Permission Changed          ADMIN        User, old/new permissions             7 years

  Report Exported             ALL          Report name, parameters, user         2 years
  --------------------------- ------------ ------------------------------------- ---------------

**10.3 Data Retention Policy**

- Transaction Data: Minimum 8 financial years (as per Companies Act)

- Audit Logs: Minimum 7 years from transaction date

- Login/Session Logs: Minimum 2 years

- Master Data Changes: Permanent retention

- Archived data must be retrievable within 48 hours

**10.4 Security Audit Points**

- All failed login attempts must be logged with IP address

- All permission changes require dual approval and logging

- Export of financial data must be logged with full parameters

- Direct database access must be logged separately

- All API calls must be logged with request/response (excluding sensitive data)

- PII data access must be logged for DPDP Act compliance

*\-\-- End of Phase 1 Technical Specification \-\--*

Phase 2 will cover: Loan Origination + Entity Appraisal + Technical Appraisal
