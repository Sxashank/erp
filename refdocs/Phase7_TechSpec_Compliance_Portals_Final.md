**SMFC Ltd**

Integrated ERP Solution

**TECHNICAL SPECIFICATION**

Phase 7: Supporting Modules (Final)

Compliance, Dashboard, Portals, Inventory, Notifications

**Table of Contents**

1\. Regulatory Compliance Module

2\. Management Dashboard & MIS

3\. Borrower Portal

4\. Employee Self-Service Portal

5\. Vendor Portal

6\. Inventory Management

7\. Notification & Alert System

8\. Document Management System

9\. Audit Trail & Logging

10\. Integration Framework

**1. Regulatory Compliance Module**

Track and manage regulatory returns, filings, and compliance requirements for NBFC operations.

**1.1 Compliance Calendar (MST_COMPLIANCE_ITEM)**

  ------------------------- -------------- ---------- ------------- ------------------------------------------------------
  **Column**                **Type**       **Null**   **Default**   **Description**

  compliance_id             BIGSERIAL      NO         Auto          Primary Key

  org_id                    BIGINT         NO         \-            FK to MST_ORGANIZATION

  compliance_code           VARCHAR(30)    NO         \-            Unique code

  compliance_name           VARCHAR(200)   NO         \-            Compliance item name

  regulator                 VARCHAR(50)    NO         \-            RBI, MCA, SEBI, GST, IT, OTHER

  category                  VARCHAR(50)    NO         \-            RETURN, REPORT, CERTIFICATE, FILING, AUDIT

  form_number               VARCHAR(50)    YES        \-            Form/Return number

  description               TEXT           YES        \-            Detailed description

  frequency                 VARCHAR(20)    NO         \-            MONTHLY, QUARTERLY, HALF_YEARLY, YEARLY, EVENT_BASED

  due_day                   INTEGER        YES        \-            Day of month/quarter due

  due_offset_days           INTEGER        YES        \-            Days after period end

  applicable_from           DATE           NO         \-            Applicable from date

  applicable_to             DATE           YES        \-            Applicable to date

  penalty_provision         TEXT           YES        \-            Penalty for non-compliance

  reference_regulation      VARCHAR(200)   YES        \-            Act/Circular reference

  responsible_role          VARCHAR(100)   YES        \-            Responsible designation

  reviewer_role             VARCHAR(100)   YES        \-            Reviewer designation

  requires_board_approval   BOOLEAN        NO         FALSE         Board approval needed

  requires_audit_cert       BOOLEAN        NO         FALSE         Auditor certificate needed

  auto_reminder_days        INTEGER        NO         7             Reminder before due

  escalation_days           INTEGER        NO         3             Escalate if not done

  status                    VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE, SUPERSEDED

  \+ Audit Columns                                                  Standard audit columns
  ------------------------- -------------- ---------- ------------- ------------------------------------------------------

**1.2 Key RBI Compliance Items (NBFC)**

  ----------------------------- ---------- ------------------- ------------------ ---------------
  **Return/Filing**             **Form**   **Frequency**       **Due Date**       **Category**

  NBS-1: Balance Sheet          NBS-1      Yearly              30 days from AGM   Return

  NBS-2: P&L Statement          NBS-2      Yearly              30 days from AGM   Return

  NBS-3: Auditors Certificate   NBS-3      Yearly              30 days from AGM   Certificate

  NBS-4: Statutory Auditor      NBS-4      Yearly              30 days from AGM   Return

  NBS-7: Prudential Norms       NBS-7      Quarterly           15 days            Return

  ALM Returns                   ALM 1-3    Monthly/Quarterly   10/20 days         Return

  CRILC Reporting               CRILC      Monthly             Last Friday        Return

  Fraud Reporting               FMR        Event-based         21 days            Report

  Branch Opening/Closure        \-         Event-based         Prior approval     Filing

  Change in Directors           \-         Event-based         30 days            Filing

  FPC Certificate               FPC        Yearly              Before July 31     Certificate

  IT Audit Report               \-         Yearly              Sept 30            Report
  ----------------------------- ---------- ------------------- ------------------ ---------------

**1.3 Compliance Instance (TXN_COMPLIANCE)**

  ---------------------- --------------- ---------- ------------- --------------------------------------------------------------------
  **Column**             **Type**        **Null**   **Default**   **Description**

  instance_id            BIGSERIAL       NO         Auto          Primary Key

  compliance_id          BIGINT          NO         \-            FK to MST_COMPLIANCE_ITEM

  org_id                 BIGINT          NO         \-            FK to MST_ORGANIZATION

  period_type            VARCHAR(20)     NO         \-            MONTH, QUARTER, HALF_YEAR, YEAR

  period_value           VARCHAR(20)     NO         \-            2025-01, Q1-2025, H1-2025, 2025-26

  period_from            DATE            NO         \-            Period start

  period_to              DATE            NO         \-            Period end

  due_date               DATE            NO         \-            Filing due date

  extended_due_date      DATE            YES        \-            If extension granted

  extension_reason       VARCHAR(500)    YES        \-            Extension reason

  prepared_by            BIGINT          YES        \-            Preparer user ID

  prepared_date          DATE            YES        \-            Preparation date

  reviewed_by            BIGINT          YES        \-            Reviewer user ID

  reviewed_date          DATE            YES        \-            Review date

  approved_by            BIGINT          YES        \-            Approver user ID

  approved_date          DATE            YES        \-            Approval date

  filed_date             DATE            YES        \-            Actual filing date

  filing_reference       VARCHAR(100)    YES        \-            Filing/ARN number

  filing_mode            VARCHAR(20)     YES        \-            ONLINE, PHYSICAL, EMAIL

  document_path          VARCHAR(500)    YES        \-            Filed document path

  acknowledgement_path   VARCHAR(500)    YES        \-            Acknowledgement path

  remarks                TEXT            YES        \-            Filing remarks

  delay_days             INTEGER         NO         0             Days delayed

  penalty_paid           NUMERIC(12,2)   NO         0             Penalty if any

  status                 VARCHAR(20)     NO         PENDING       PENDING, IN_PROGRESS, PREPARED, REVIEWED, APPROVED, FILED, DELAYED

  \+ Audit Columns                                                Standard audit columns
  ---------------------- --------------- ---------- ------------- --------------------------------------------------------------------

**1.4 MCA Filings**

  ----------- ----------------------------- --------------------- --------------------
  **Form**    **Description**               **Due Date**          **Penalty**

  AOC-4       Annual financial statements   30 days from AGM      ₹100/day

  MGT-7       Annual Return                 60 days from AGM      ₹100/day

  ADT-1       Auditor Appointment           15 days from AGM      ₹10,000 + ₹100/day

  DIR-3 KYC   Director KYC                  September 30          ₹5,000

  DIR-12      Change in Directors           30 days of change     ₹50,000

  CHG-1       Charge Registration           30 days of creation   ₹1,000/day

  CHG-4       Charge Satisfaction           30 days               ₹1,000/day

  INC-20A     Commencement Certificate      180 days of incorp    ₹50,000

  MSME-1      Outstanding MSME Payments     Half-yearly           No penalty

  DPT-3       Return of Deposits            June 30               ₹5,000 + ₹500/day
  ----------- ----------------------------- --------------------- --------------------

**2. Management Dashboard & MIS**

Real-time dashboards and MIS reports for management decision-making.

**2.1 Dashboard Configuration (MST_DASHBOARD)**

  ---------------------- -------------- ---------- ------------- ------------------------------------
  **Column**             **Type**       **Null**   **Default**   **Description**

  dashboard_id           BIGSERIAL      NO         Auto          Primary Key

  org_id                 BIGINT         NO         \-            FK to MST_ORGANIZATION

  dashboard_code         VARCHAR(30)    NO         \-            Unique code

  dashboard_name         VARCHAR(100)   NO         \-            Dashboard name

  dashboard_type         VARCHAR(30)    NO         \-            EXECUTIVE, OPERATIONAL, ANALYTICAL

  description            VARCHAR(500)   YES        \-            Description

  default_for_roles      JSONB          YES        \-            Default roles

  refresh_interval_sec   INTEGER        NO         300           Auto-refresh interval

  layout_config          JSONB          YES        \-            Widget layout JSON

  is_public              BOOLEAN        NO         FALSE         Available to all users

  status                 VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                               Standard audit columns
  ---------------------- -------------- ---------- ------------- ------------------------------------

**2.2 Dashboard Widgets (MST_DASHBOARD_WIDGET)**

  ------------------- -------------- ---------- ------------- -------------------------------------
  **Column**          **Type**       **Null**   **Default**   **Description**

  widget_id           BIGSERIAL      NO         Auto          Primary Key

  dashboard_id        BIGINT         NO         \-            FK to MST_DASHBOARD

  widget_code         VARCHAR(30)    NO         \-            Widget code

  widget_name         VARCHAR(100)   NO         \-            Widget title

  widget_type         VARCHAR(30)    NO         \-            KPI, CHART, TABLE, MAP, GAUGE, LIST

  chart_type          VARCHAR(20)    YES        \-            LINE, BAR, PIE, DONUT, AREA

  data_source         VARCHAR(100)   NO         \-            Data source/API

  query_config        JSONB          YES        \-            Query parameters

  display_config      JSONB          YES        \-            Display settings

  position_x          INTEGER        NO         0             Grid X position

  position_y          INTEGER        NO         0             Grid Y position

  width               INTEGER        NO         4             Widget width (cols)

  height              INTEGER        NO         3             Widget height (rows)

  drill_down_config   JSONB          YES        \-            Drill-down settings

  status              VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                            Standard audit columns
  ------------------- -------------- ---------- ------------- -------------------------------------

**2.3 Executive Dashboard KPIs**

  ----------------------- ----------------------------------------- ---------------------------- ---------------------
  **KPI**                 **Formula/Source**                        **Drill-Down**               **Alert Threshold**

  Total AUM               SUM(principal_outstanding)                By product, branch, rating   Growth \< 5%

  Gross NPA %             NPA / Total Advances × 100                By borrower, age, sector     \> 5%

  Net NPA %               (NPA - Provisions) / Net Advances         By category                  \> 2%

  CRAR                    Capital / Risk Weighted Assets            Tier 1, Tier 2 split         \< 15%

  Cost of Funds           Interest Expense / Avg Borrowings         By source                    \> 9%

  NIM                     (Int Income - Int Expense) / Avg Assets   Trend                        \< 3%

  ROA                     PAT / Avg Total Assets                    Quarterly trend              \< 1%

  ROE                     PAT / Avg Equity                          Quarterly trend              \< 10%

  Disbursement MTD        SUM(disbursements)                        By product, branch           vs Target

  Collection Efficiency   Collections / Demand × 100                By branch, product           \< 95%

  SMA Book                SMA-0 + SMA-1 + SMA-2                     By category, aging           \> 10%

  Employee Productivity   AUM / Employee Count                      By branch                    Below benchmark
  ----------------------- ----------------------------------------- ---------------------------- ---------------------

**2.4 MIS Report Configuration (MST_MIS_REPORT)**

  ------------------ -------------- ---------- ------------- --------------------------------------------
  **Column**         **Type**       **Null**   **Default**   **Description**

  report_id          BIGSERIAL      NO         Auto          Primary Key

  org_id             BIGINT         NO         \-            FK to MST_ORGANIZATION

  report_code        VARCHAR(30)    NO         \-            Report code

  report_name        VARCHAR(200)   NO         \-            Report name

  report_category    VARCHAR(50)    NO         \-            FINANCE, LENDING, TREASURY, HR, COMPLIANCE

  report_type        VARCHAR(30)    NO         \-            STANDARD, CUSTOM, REGULATORY

  frequency          VARCHAR(20)    NO         \-            DAILY, WEEKLY, MONTHLY, ON_DEMAND

  query_template     TEXT           YES        \-            SQL/Query template

  parameters         JSONB          YES        \-            Report parameters

  output_format      VARCHAR(20)    NO         PDF           PDF, EXCEL, CSV, HTML

  email_recipients   JSONB          YES        \-            Auto-email list

  schedule_time      TIME           YES        \-            Scheduled run time

  last_run_date      TIMESTAMPTZ    YES        \-            Last execution

  status             VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                           Standard audit columns
  ------------------ -------------- ---------- ------------- --------------------------------------------

**2.5 Standard MIS Reports**

  --------------------------- -------------- --------------- ---------------------------------------------------
  **Report**                  **Category**   **Frequency**   **Key Contents**

  Portfolio Position          Lending        Daily           AUM, disbursements, collections, O/S by product

  NPA Movement                Lending        Monthly         Opening, additions, upgrades, write-offs, closing

  ALM Statement               Treasury       Monthly         Liquidity gaps by bucket

  Interest Rate Sensitivity   Treasury       Monthly         RSA, RSL, gap analysis

  Borrowing Position          Treasury       Daily           Outstanding, unutilized, cost

  Income Statement Flash      Finance        Daily           Interest income, expense, NII, provisions

  Provisioning Report         Finance        Monthly         Standard, NPA provisions, movement

  Exposure Report             Risk           Weekly          Single borrower, group, sector concentration

  Rating Migration            Risk           Quarterly       Rating changes, downgrades

  SMA Monitoring              Collections    Daily           SMA-0, 1, 2 by value and count

  Compliance Tracker          Compliance     Weekly          Pending filings, delays

  HR Dashboard                HR             Monthly         Headcount, attrition, cost per employee
  --------------------------- -------------- --------------- ---------------------------------------------------

**3. Borrower Portal**

Self-service portal for borrowers to view loan status, make payments, and submit requests.

**3.1 Portal User (MST_PORTAL_USER)**

  ---------------------- -------------- ---------- ------------- -------------------------------------
  **Column**             **Type**       **Null**   **Default**   **Description**

  portal_user_id         BIGSERIAL      NO         Auto          Primary Key

  org_id                 BIGINT         NO         \-            FK to MST_ORGANIZATION

  portal_type            VARCHAR(20)    NO         \-            BORROWER, EMPLOYEE, VENDOR

  entity_id              BIGINT         YES        \-            FK to MST_ENTITY (for borrower)

  employee_id            BIGINT         YES        \-            FK to MST_EMPLOYEE (for employee)

  vendor_id              BIGINT         YES        \-            FK to MST_VENDOR (for vendor)

  username               VARCHAR(100)   NO         \-            Login username

  email                  VARCHAR(255)   NO         \-            Email address

  mobile                 VARCHAR(15)    NO         \-            Mobile number

  password_hash          VARCHAR(255)   NO         \-            Hashed password

  mfa_enabled            BOOLEAN        NO         TRUE          2FA enabled

  mfa_secret             VARCHAR(100)   YES        \-            TOTP secret

  last_login             TIMESTAMPTZ    YES        \-            Last login time

  login_attempts         INTEGER        NO         0             Failed attempts

  locked_until           TIMESTAMPTZ    YES        \-            Account lock expiry

  password_changed_at    TIMESTAMPTZ    YES        \-            Last password change

  must_change_password   BOOLEAN        NO         FALSE         Force password change

  session_token          VARCHAR(255)   YES        \-            Current session

  status                 VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE, LOCKED, SUSPENDED

  \+ Audit Columns                                               Standard audit columns
  ---------------------- -------------- ---------- ------------- -------------------------------------

**3.2 Borrower Portal Features**

  ---------------------- ----------------------------------------------- ------------------
  **Feature**            **Description**                                 **Access Level**

  Dashboard              Overview of all loans, outstanding, next due    All borrowers

  Loan Summary           Loan-wise details, disbursements, schedules     All borrowers

  Repayment Schedule     View/download principal and interest schedule   All borrowers

  Statement of Account   Transaction history, receipts, demands          All borrowers

  Make Payment           Online payment via payment gateway              All borrowers

  Download Documents     Sanction letter, demand letters, NOC            All borrowers

  Upload Documents       Submit requested documents                      All borrowers

  Raise Request          Prepayment, rescheduling, NOC requests          All borrowers

  View Correspondence    Letters, notices, communications                All borrowers

  Interest Certificate   Download interest certificate for IT            All borrowers

  TDS Certificate        View TDS deducted, download Form 16A            All borrowers

  Contact Support        Raise tickets, chat with RM                     All borrowers
  ---------------------- ----------------------------------------------- ------------------

**3.3 Portal Service Request (TXN_PORTAL_REQUEST)**

  ------------------ -------------- ---------- ------------- ---------------------------------------------------------
  **Column**         **Type**       **Null**   **Default**   **Description**

  request_id         BIGSERIAL      NO         Auto          Primary Key

  portal_user_id     BIGINT         NO         \-            FK to MST_PORTAL_USER

  request_type       VARCHAR(50)    NO         \-            PREPAYMENT, RESCHEDULE, NOC, DOCUMENT, QUERY, COMPLAINT

  reference_type     VARCHAR(50)    YES        \-            LOAN_ACCOUNT, APPLICATION

  reference_id       BIGINT         YES        \-            Reference ID

  subject            VARCHAR(200)   NO         \-            Request subject

  description        TEXT           NO         \-            Request details

  attachments        JSONB          YES        \-            Uploaded files

  priority           VARCHAR(20)    NO         NORMAL        LOW, NORMAL, HIGH, URGENT

  assigned_to        BIGINT         YES        \-            FK to MST_USER

  assigned_date      TIMESTAMPTZ    YES        \-            Assignment date

  response           TEXT           YES        \-            Response text

  response_date      TIMESTAMPTZ    YES        \-            Response date

  resolution_date    TIMESTAMPTZ    YES        \-            Resolution date

  sla_hours          INTEGER        NO         48            SLA in hours

  sla_breached       BOOLEAN        NO         FALSE         SLA breached

  rating             INTEGER        YES        \-            User rating (1-5)

  feedback           TEXT           YES        \-            User feedback

  status             VARCHAR(20)    NO         OPEN          OPEN, IN_PROGRESS, RESOLVED, CLOSED, CANCELLED

  \+ Audit Columns                                           Standard audit columns
  ------------------ -------------- ---------- ------------- ---------------------------------------------------------

**4. Employee Self-Service Portal**

ESS portal for employees to manage their HR-related activities.

**4.1 Employee Portal Features**

  ------------- -------------------------------------------------- ----------------------------
  **Module**    **Features**                                       **Actions**

  Profile       View/update personal info, address, bank, family   View, Request Update

  Attendance    View attendance, punch records, regularization     View, Apply Regularization

  Leave         Leave balance, history, apply, cancel              Apply, Withdraw, View

  Payroll       Payslips, YTD earnings, Form 16, tax declaration   View, Download

  Claims        Reimbursement claims, travel, medical              Apply, Track, View

  Training      Training calendar, enrollment, feedback            Enroll, Complete, Feedback

  Performance   Goals, self-appraisal, review history              Update Goals, Self-Rate

  Documents     Policies, forms, circulars                         View, Download

  Directory     Employee directory, org chart                      Search, View

  Helpdesk      HR queries, IT tickets                             Raise, Track
  ------------- -------------------------------------------------- ----------------------------

**4.2 Reimbursement Claims (TXN_REIMBURSEMENT)**

  ------------------- --------------- ---------- ------------- --------------------------------------------
  **Column**          **Type**        **Null**   **Default**   **Description**

  claim_id            BIGSERIAL       NO         Auto          Primary Key

  employee_id         BIGINT          NO         \-            FK to MST_EMPLOYEE

  claim_number        VARCHAR(30)     NO         \-            Unique claim number

  claim_type          VARCHAR(30)     NO         \-            TRAVEL, MEDICAL, CONVEYANCE, MOBILE, OTHER

  claim_date          DATE            NO         \-            Claim submission date

  expense_from        DATE            NO         \-            Expense period from

  expense_to          DATE            NO         \-            Expense period to

  claimed_amount      NUMERIC(12,2)   NO         \-            Amount claimed

  approved_amount     NUMERIC(12,2)   YES        \-            Amount approved

  description         TEXT            YES        \-            Claim description

  bills_attached      INTEGER         NO         0             Number of bills

  attachments         JSONB           YES        \-            Bill images/PDFs

  approved_by         BIGINT          YES        \-            Approver

  approved_date       DATE            YES        \-            Approval date

  rejection_reason    VARCHAR(500)    YES        \-            If rejected

  payment_date        DATE            YES        \-            Payment date

  payment_reference   VARCHAR(50)     YES        \-            Payment ref

  status              VARCHAR(20)     NO         SUBMITTED     DRAFT, SUBMITTED, APPROVED, REJECTED, PAID

  \+ Audit Columns                                             Standard audit columns
  ------------------- --------------- ---------- ------------- --------------------------------------------

**5. Vendor Portal**

Portal for vendors to submit invoices, track payments, and manage compliance.

**5.1 Vendor Portal Features**

  -------------------- ---------------------------------------------- ---------------------------
  **Feature**          **Description**                                **Actions**

  Dashboard            PO summary, pending invoices, payment status   View

  Purchase Orders      View POs issued, accept/reject                 View, Accept, Acknowledge

  Invoice Submission   Submit invoices against POs                    Upload, Submit

  Invoice Status       Track invoice processing status                View, Query

  Payment Status       View payments made, download advice            View, Download

  TDS Certificates     Download Form 16A for TDS                      View, Download

  Compliance Upload    Upload GST returns, PAN, bank details          Upload, Update

  Communication        Messages, notices from SMFC                    View, Respond

  Rate Contract        View rate contracts, validity                  View
  -------------------- ---------------------------------------------- ---------------------------

**5.2 Vendor Master (MST_VENDOR)**

  -------------------- --------------- ---------- ------------- ----------------------------------------------------
  **Column**           **Type**        **Null**   **Default**   **Description**

  vendor_id            BIGSERIAL       NO         Auto          Primary Key

  org_id               BIGINT          NO         \-            FK to MST_ORGANIZATION

  vendor_code          VARCHAR(20)     NO         \-            Unique vendor code

  vendor_name          VARCHAR(200)    NO         \-            Vendor name

  vendor_type          VARCHAR(30)     NO         \-            SUPPLIER, CONTRACTOR, SERVICE_PROVIDER, CONSULTANT

  pan                  VARCHAR(10)     YES        \-            PAN

  gstin                VARCHAR(15)     YES        \-            GSTIN

  tan                  VARCHAR(10)     YES        \-            TAN

  msme_registered      BOOLEAN         NO         FALSE         MSME registered

  msme_number          VARCHAR(30)     YES        \-            MSME/Udyam number

  msme_category        VARCHAR(20)     YES        \-            MICRO, SMALL, MEDIUM

  address              TEXT            YES        \-            Address

  city                 VARCHAR(100)    YES        \-            City

  state                VARCHAR(100)    YES        \-            State

  pincode              VARCHAR(6)      YES        \-            PIN code

  contact_person       VARCHAR(200)    YES        \-            Contact person

  contact_email        VARCHAR(255)    YES        \-            Email

  contact_phone        VARCHAR(20)     YES        \-            Phone

  bank_name            VARCHAR(200)    YES        \-            Bank name

  bank_account         VARCHAR(30)     YES        \-            Account number

  bank_ifsc            VARCHAR(11)     YES        \-            IFSC code

  payment_terms_days   INTEGER         NO         30            Payment terms

  tds_section_id       BIGINT          YES        \-            Default TDS section

  lower_tds_cert       VARCHAR(50)     YES        \-            Lower TDS cert

  lower_tds_rate       NUMERIC(5,2)    YES        \-            Lower TDS rate

  lower_tds_validity   DATE            YES        \-            Cert validity

  credit_limit         NUMERIC(14,2)   YES        \-            Credit limit

  gl_account_id        BIGINT          YES        \-            FK to MST_COA

  blacklisted          BOOLEAN         NO         FALSE         Blacklisted vendor

  blacklist_reason     VARCHAR(500)    YES        \-            Blacklist reason

  status               VARCHAR(20)     NO         ACTIVE        ACTIVE, INACTIVE, BLACKLISTED

  \+ Audit Columns                                              Standard audit columns
  -------------------- --------------- ---------- ------------- ----------------------------------------------------

**6. Inventory Management**

Basic inventory management for office supplies, stationery, and consumables.

**6.1 Item Master (MST_INVENTORY_ITEM)**

  --------------------- --------------- ---------- ------------- -------------------------------------------
  **Column**            **Type**        **Null**   **Default**   **Description**

  item_id               BIGSERIAL       NO         Auto          Primary Key

  org_id                BIGINT          NO         \-            FK to MST_ORGANIZATION

  item_code             VARCHAR(30)     NO         \-            Item code

  item_name             VARCHAR(200)    NO         \-            Item name

  item_category         VARCHAR(50)     NO         \-            STATIONERY, IT, ELECTRICAL, PANTRY, OTHER

  uom                   VARCHAR(20)     NO         \-            Unit of measure

  hsn_code              VARCHAR(10)     YES        \-            HSN code

  gst_rate              NUMERIC(5,2)    NO         18            GST rate

  reorder_level         INTEGER         NO         10            Reorder point

  reorder_qty           INTEGER         NO         50            Reorder quantity

  max_stock             INTEGER         YES        \-            Maximum stock

  current_stock         INTEGER         NO         0             Current quantity

  avg_cost              NUMERIC(12,2)   NO         0             Weighted avg cost

  last_purchase_price   NUMERIC(12,2)   YES        \-            Last purchase price

  last_purchase_date    DATE            YES        \-            Last purchase date

  preferred_vendor_id   BIGINT          YES        \-            FK to MST_VENDOR

  is_consumable         BOOLEAN         NO         TRUE          Consumable item

  is_serialized         BOOLEAN         NO         FALSE         Track serials

  shelf_life_days       INTEGER         YES        \-            Shelf life

  status                VARCHAR(20)     NO         ACTIVE        ACTIVE, INACTIVE, DISCONTINUED

  \+ Audit Columns                                               Standard audit columns
  --------------------- --------------- ---------- ------------- -------------------------------------------

**6.2 Inventory Transaction (TXN_INVENTORY)**

  ---------------------- --------------- ---------- ------------- ----------------------------------------------
  **Column**             **Type**        **Null**   **Default**   **Description**

  transaction_id         BIGSERIAL       NO         Auto          Primary Key

  item_id                BIGINT          NO         \-            FK to MST_INVENTORY_ITEM

  location_id            BIGINT          NO         \-            FK to MST_UNIT (store)

  transaction_date       DATE            NO         \-            Transaction date

  transaction_type       VARCHAR(20)     NO         \-            RECEIPT, ISSUE, RETURN, TRANSFER, ADJUSTMENT

  reference_type         VARCHAR(30)     YES        \-            PO, INDENT, TRANSFER_NOTE

  reference_number       VARCHAR(50)     YES        \-            Reference document

  quantity               INTEGER         NO         \-            Quantity (+/-)

  unit_cost              NUMERIC(12,2)   YES        \-            Unit cost

  total_cost             NUMERIC(14,2)   YES        \-            Total cost

  issued_to_employee     BIGINT          YES        \-            FK to MST_EMPLOYEE

  issued_to_department   BIGINT          YES        \-            FK to MST_DEPARTMENT

  received_from_vendor   BIGINT          YES        \-            FK to MST_VENDOR

  batch_number           VARCHAR(50)     YES        \-            Batch/Lot number

  expiry_date            DATE            YES        \-            Expiry date

  balance_after          INTEGER         NO         \-            Stock after transaction

  remarks                VARCHAR(500)    YES        \-            Remarks

  \+ Audit Columns                                                Standard audit columns
  ---------------------- --------------- ---------- ------------- ----------------------------------------------

**7. Notification & Alert System**

Centralized notification system for alerts, reminders, and communications.

**7.1 Notification Template (MST_NOTIFICATION_TEMPLATE)**

  ------------------ -------------- ---------- ------------- ------------------------------------
  **Column**         **Type**       **Null**   **Default**   **Description**

  template_id        BIGSERIAL      NO         Auto          Primary Key

  org_id             BIGINT         NO         \-            FK to MST_ORGANIZATION

  template_code      VARCHAR(50)    NO         \-            Unique code

  template_name      VARCHAR(200)   NO         \-            Template name

  event_type         VARCHAR(50)    NO         \-            Trigger event

  channel            VARCHAR(20)    NO         \-            EMAIL, SMS, PUSH, IN_APP, WHATSAPP

  subject_template   VARCHAR(500)   YES        \-            Subject with placeholders

  body_template      TEXT           NO         \-            Body with placeholders

  html_template      TEXT           YES        \-            HTML version

  placeholders       JSONB          YES        \-            Available placeholders

  priority           VARCHAR(20)    NO         NORMAL        LOW, NORMAL, HIGH, URGENT

  status             VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                           Standard audit columns
  ------------------ -------------- ---------- ------------- ------------------------------------

**7.2 Notification Log (TXN_NOTIFICATION)**

  ------------------- -------------- ---------- ------------- ----------------------------------------
  **Column**          **Type**       **Null**   **Default**   **Description**

  notification_id     BIGSERIAL      NO         Auto          Primary Key

  template_id         BIGINT         YES        \-            FK to template

  channel             VARCHAR(20)    NO         \-            EMAIL, SMS, PUSH, IN_APP

  recipient_type      VARCHAR(30)    NO         \-            USER, EMPLOYEE, BORROWER, VENDOR

  recipient_id        BIGINT         YES        \-            Recipient ID

  recipient_address   VARCHAR(255)   NO         \-            Email/Phone

  subject             VARCHAR(500)   YES        \-            Subject

  body                TEXT           NO         \-            Message body

  reference_type      VARCHAR(50)    YES        \-            Related entity type

  reference_id        BIGINT         YES        \-            Related entity ID

  scheduled_at        TIMESTAMPTZ    YES        \-            Scheduled time

  sent_at             TIMESTAMPTZ    YES        \-            Actual sent time

  delivered_at        TIMESTAMPTZ    YES        \-            Delivery confirmation

  read_at             TIMESTAMPTZ    YES        \-            Read time (for in-app)

  retry_count         INTEGER        NO         0             Retry attempts

  error_message       TEXT           YES        \-            If failed

  external_ref        VARCHAR(100)   YES        \-            Gateway reference

  status              VARCHAR(20)    NO         PENDING       PENDING, SENT, DELIVERED, READ, FAILED

  \+ Audit Columns                                            Standard audit columns
  ------------------- -------------- ---------- ------------- ----------------------------------------

**7.3 Standard Notification Events**

  -------------------- ------------------ ------------------ ---------------------
  **Event**            **Channel**        **Recipients**     **Trigger**

  Loan Disbursement    Email, SMS         Borrower           On disbursement

  Demand Notice        Email, SMS, Post   Borrower           7 days before due

  Payment Reminder     SMS                Borrower           On due date

  Overdue Alert        Email, SMS         Borrower, RM       1 day after due

  NPA Classification   Email              RM, Credit Head    On NPA mark

  Sanction Approved    Email              Borrower, Branch   On sanction

  Leave Approved       Email, Push        Employee           On approval

  Salary Credited      SMS, Email         Employee           On credit

  Compliance Due       Email              Compliance team    7 days before

  Password Expiry      Email              User               7 days before

  Invoice Approved     Email              Vendor             On approval

  Payment Processed    Email              Vendor             On payment
  -------------------- ------------------ ------------------ ---------------------

**8. Document Management System**

Centralized document storage, versioning, and retrieval.

**8.1 Document Store (TXN_DOCUMENT)**

  --------------------- -------------- ---------- ------------- --------------------------------
  **Column**            **Type**       **Null**   **Default**   **Description**

  document_id           BIGSERIAL      NO         Auto          Primary Key

  org_id                BIGINT         NO         \-            FK to MST_ORGANIZATION

  document_code         VARCHAR(50)    NO         \-            Unique document code

  document_name         VARCHAR(200)   NO         \-            Document name

  document_type         VARCHAR(50)    NO         \-            Category/Type

  entity_type           VARCHAR(50)    NO         \-            Related entity type

  entity_id             BIGINT         NO         \-            Related entity ID

  file_name             VARCHAR(255)   NO         \-            Original filename

  file_extension        VARCHAR(10)    NO         \-            File extension

  file_size_bytes       BIGINT         NO         \-            File size

  mime_type             VARCHAR(100)   NO         \-            MIME type

  storage_path          VARCHAR(500)   NO         \-            Storage location

  storage_type          VARCHAR(20)    NO         LOCAL         LOCAL, S3, AZURE, GCS

  checksum              VARCHAR(64)    NO         \-            SHA-256 hash

  version               INTEGER        NO         1             Version number

  is_latest             BOOLEAN        NO         TRUE          Latest version flag

  previous_version_id   BIGINT         YES        \-            Previous version

  uploaded_by           BIGINT         NO         \-            Uploader user ID

  upload_date           TIMESTAMPTZ    NO         \-            Upload timestamp

  expiry_date           DATE           YES        \-            Document expiry

  is_confidential       BOOLEAN        NO         FALSE         Confidential flag

  access_level          VARCHAR(20)    NO         PRIVATE       PUBLIC, PRIVATE, RESTRICTED

  ocr_text              TEXT           YES        \-            Extracted text

  metadata              JSONB          YES        \-            Additional metadata

  status                VARCHAR(20)    NO         ACTIVE        ACTIVE, ARCHIVED, DELETED

  \+ Audit Columns                                              Standard audit columns
  --------------------- -------------- ---------- ------------- --------------------------------

**9. Audit Trail & Logging**

Comprehensive audit logging for compliance and security.

**9.1 Audit Log (TXN_AUDIT_LOG)**

  -------------------- -------------- ---------- ------------- --------------------------------------------------------------
  **Column**           **Type**       **Null**   **Default**   **Description**

  audit_id             BIGSERIAL      NO         Auto          Primary Key

  org_id               BIGINT         NO         \-            FK to MST_ORGANIZATION

  event_timestamp      TIMESTAMPTZ    NO         NOW()         Event time

  event_type           VARCHAR(30)    NO         \-            CREATE, UPDATE, DELETE, VIEW, LOGIN, LOGOUT, APPROVE, REJECT

  entity_type          VARCHAR(100)   NO         \-            Table/Entity name

  entity_id            BIGINT         YES        \-            Record ID

  entity_code          VARCHAR(100)   YES        \-            Business code

  user_id              BIGINT         YES        \-            User who performed action

  username             VARCHAR(100)   YES        \-            Username

  user_ip              VARCHAR(45)    YES        \-            IP address

  user_agent           VARCHAR(500)   YES        \-            Browser/Client

  session_id           VARCHAR(100)   YES        \-            Session identifier

  old_values           JSONB          YES        \-            Previous values

  new_values           JSONB          YES        \-            New values

  changed_fields       JSONB          YES        \-            List of changed fields

  action_description   VARCHAR(500)   YES        \-            Human-readable description

  module               VARCHAR(50)    YES        \-            Application module

  sub_module           VARCHAR(50)    YES        \-            Sub-module

  api_endpoint         VARCHAR(200)   YES        \-            API endpoint called

  request_id           VARCHAR(100)   YES        \-            Correlation ID

  execution_time_ms    INTEGER        YES        \-            Execution time

  status               VARCHAR(20)    NO         SUCCESS       SUCCESS, FAILURE, ERROR

  error_message        TEXT           YES        \-            Error details
  -------------------- -------------- ---------- ------------- --------------------------------------------------------------

**9.2 Audit Trail Requirements**

  ----------------------- ------------------------------------------------- -----------------
  **Requirement**         **Implementation**                                **Retention**

  All data changes        Trigger-based capture of INSERT, UPDATE, DELETE   7 years

  User logins             Log every login attempt (success/failure)         2 years

  Sensitive data access   Log access to PII, financial data                 7 years

  Approval actions        Log all workflow approvals/rejections             7 years

  Report generation       Log MIS/regulatory report access                  3 years

  Configuration changes   Log master data changes                           7 years

  API access              Log external API calls                            1 year

  Portal access           Log borrower/vendor portal activity               3 years
  ----------------------- ------------------------------------------------- -----------------

**10. Integration Framework**

APIs and integration points with external systems.

**10.1 External Integrations**

  -------------------- ------------------------------------ ---------------------- -----------------
  **System**           **Purpose**                          **Protocol**           **Frequency**

  Core Banking (CBS)   Fund transfers, account validation   REST API / ISO 20022   Real-time

  Payment Gateway      Online collections                   REST API               Real-time

  CKYC Registry        KYC verification                     REST API               On-demand

  CERSAI               Charge registration                  Web service            On-demand

  CRILC                Credit information                   File upload            Monthly

  Credit Bureaus       Credit reports                       REST API               On-demand

  GST Portal           GSTIN validation, returns            REST API               On-demand

  MCA Portal           Company master, filings              REST API               On-demand

  Email Gateway        Transactional emails                 SMTP/API               Real-time

  SMS Gateway          OTP, alerts                          REST API               Real-time

  Biometric System     Attendance                           REST API               Real-time

  HRMS (if external)   Employee data sync                   REST API               Daily
  -------------------- ------------------------------------ ---------------------- -----------------

**10.2 API Gateway Configuration (MST_API_CONFIG)**

  -------------------- -------------- ---------- ------------- -----------------------------------
  **Column**           **Type**       **Null**   **Default**   **Description**

  config_id            BIGSERIAL      NO         Auto          Primary Key

  api_code             VARCHAR(50)    NO         \-            API identifier

  api_name             VARCHAR(200)   NO         \-            API name

  api_type             VARCHAR(20)    NO         \-            INBOUND, OUTBOUND

  protocol             VARCHAR(20)    NO         \-            REST, SOAP, SFTP, MQ

  base_url             VARCHAR(500)   YES        \-            Base URL

  endpoint             VARCHAR(200)   YES        \-            Endpoint path

  http_method          VARCHAR(10)    YES        \-            GET, POST, PUT, DELETE

  auth_type            VARCHAR(30)    YES        \-            NONE, BASIC, BEARER, OAUTH2, CERT

  auth_credentials     JSONB          YES        \-            Encrypted credentials

  headers              JSONB          YES        \-            Default headers

  timeout_seconds      INTEGER        NO         30            Timeout

  retry_count          INTEGER        NO         3             Max retries

  retry_interval_sec   INTEGER        NO         5             Retry interval

  rate_limit_per_min   INTEGER        YES        \-            Rate limit

  is_active            BOOLEAN        NO         TRUE          Active flag

  \+ Audit Columns                                             Standard audit columns
  -------------------- -------------- ---------- ------------- -----------------------------------

**10.3 Integration Log (TXN_API_LOG)**

  -------------------- -------------- ---------- ------------- ----------------------------------
  **Column**           **Type**       **Null**   **Default**   **Description**

  log_id               BIGSERIAL      NO         Auto          Primary Key

  config_id            BIGINT         YES        \-            FK to MST_API_CONFIG

  api_code             VARCHAR(50)    NO         \-            API code

  direction            VARCHAR(10)    NO         \-            INBOUND, OUTBOUND

  request_timestamp    TIMESTAMPTZ    NO         \-            Request time

  response_timestamp   TIMESTAMPTZ    YES        \-            Response time

  request_id           VARCHAR(100)   YES        \-            Correlation ID

  endpoint             VARCHAR(500)   YES        \-            Full endpoint

  http_method          VARCHAR(10)    YES        \-            Method used

  request_headers      JSONB          YES        \-            Request headers

  request_body         TEXT           YES        \-            Request payload

  response_status      INTEGER        YES        \-            HTTP status code

  response_headers     JSONB          YES        \-            Response headers

  response_body        TEXT           YES        \-            Response payload

  execution_time_ms    INTEGER        YES        \-            Time taken

  retry_attempt        INTEGER        NO         0             Retry number

  error_code           VARCHAR(50)    YES        \-            Error code

  error_message        TEXT           YES        \-            Error details

  status               VARCHAR(20)    NO         \-            SUCCESS, FAILURE, TIMEOUT, ERROR
  -------------------- -------------- ---------- ------------- ----------------------------------

**Technical Specification Summary**

Complete summary of all modules covered across all phases.

**Module Coverage Summary**

  ----------- -------------------------------- --------------------------------------------------- -----------------
  **Phase**   **Modules**                      **Key Tables**                                      **Est. Tables**

  Phase 1     Masters, GL, Accounting          MST_ORG, MST_UNIT, MST_USER, MST_COA, TXN_VOUCHER   \~15

  Phase 2     Lending Masters, LOS, Sanction   MST_ENTITY, TXN_APPLICATION, TXN_SANCTION           \~25

  Phase 3     Loan Accounting, NPA, Legal      TXN_LOAN_ACCOUNT, TXN_DISBURSEMENT, TXN_NPA         \~20

  Phase 4     Treasury, ALM, Risk              TXN_BORROWING, TXN_ALM_POSITION, TXN_EXPOSURE       \~15

  Phase 5     HRIS, Payroll                    MST_EMPLOYEE, TXN_PAYROLL, TXN_LEAVE                \~20

  Phase 6     FA, TDS, GST, BRS, FD            MST_FIXED_ASSET, TXN_TDS, TXN_GST, TXN_BRS          \~20

  Phase 7     Compliance, Portal, Inventory    MST_COMPLIANCE, MST_PORTAL_USER, TXN_DOCUMENT       \~15

  TOTAL       All Modules                      \-                                                  \~130 Tables
  ----------- -------------------------------- --------------------------------------------------- -----------------

**Technology Stack Recommendation**

  --------------- ------------------------ -----------------------------------------
  **Layer**       **Technology**           **Rationale**

  Database        PostgreSQL 15+           JSONB support, performance, open-source

  Backend         .NET Core 8 / Node.js    Enterprise-grade, scalable

  Frontend        React / Angular          Modern SPA, responsive

  Mobile          React Native / Flutter   Cross-platform

  API Gateway     Kong / AWS API Gateway   Rate limiting, security

  Caching         Redis                    Session, performance

  Message Queue   RabbitMQ / Kafka         Async processing

  Search          Elasticsearch            Full-text search, analytics

  Storage         S3 / Azure Blob          Document storage

  Reporting       JasperReports / SSRS     PDF generation

  BI              Metabase / Power BI      Dashboards
  --------------- ------------------------ -----------------------------------------

═══════════════════════════════════════════════════

**END OF TECHNICAL SPECIFICATION**

SMFC Ltd - Integrated ERP Solution

*All 7 Phases Complete \| \~130 Database Tables \| Full Enterprise Coverage*

═══════════════════════════════════════════════════
