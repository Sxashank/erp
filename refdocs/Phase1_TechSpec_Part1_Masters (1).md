**SMFC Ltd**

Integrated ERP Solution

**TECHNICAL SPECIFICATION**

Phase 1: Masters & Accounting/General Ledger

*Developer Reference Document*

Version 1.0

  --------------------- ----------------------------
  Document Type         Technical Specification

  Module                Masters + Accounting/GL

  Version               1.0

  Status                Draft

  Last Updated          January 2026
  --------------------- ----------------------------

**Table of Contents**

1\. Document Overview

2\. Database Conventions

3\. Global Masters

3.1 Organization (MST_ORGANIZATION)

3.2 Units/Locations (MST_UNIT)

3.3 Departments (MST_DEPARTMENT)

3.4 Users (MST_USER)

3.5 Roles & Permissions (MST_ROLE, MAP_ROLE_PERMISSION)

3.6 Financial Year (MST_FINANCIAL_YEAR)

3.7 Currency (MST_CURRENCY)

3.8 Bank Accounts (MST_BANK_ACCOUNT)

4\. Accounting Masters

4.1 Chart of Accounts (MST_COA)

4.2 Cost Centers (MST_COST_CENTER)

4.3 Balance Sheet Groups (MST_BS_GROUP)

4.4 Voucher Types (MST_VOUCHER_TYPE)

4.5 Approval Matrix (MST_APPROVAL_MATRIX)

5\. General Ledger Module

5.1 Voucher Header (TXN_VOUCHER)

5.2 Voucher Lines (TXN_VOUCHER_LINE)

5.3 Voucher Workflow (TXN_VOUCHER_WORKFLOW)

5.4 Period Management (MST_PERIOD)

5.5 GL Postings (TXN_GL_POSTING)

6\. Business Flows

7\. Business Rules & Validations

8\. State Machines

9\. API Contracts

10\. Audit Requirements

**1. Document Overview**

This document serves as the definitive technical reference for developers implementing the Masters and Accounting/General Ledger modules of the SMFC ERP system. It contains complete specifications for database schema, business rules, validation logic, and integration requirements.

**1.1 Purpose**

- Provide complete database schema with all tables, columns, and relationships

- Define all business rules and validation logic with specific conditions

- Document state transitions and workflow requirements

- Specify integration points with other modules

- Establish audit and logging requirements

**1.2 Scope**

This phase covers:

- Global Masters: Organization, Units, Departments, Users, Roles, Financial Years, Currency, Bank Accounts

- Accounting Masters: Chart of Accounts, Cost Centers, BS Groups, Voucher Types, Approval Matrix

- General Ledger: Voucher Entry, Approval Workflow, Posting, Period Management

**1.3 Technology Stack Reference**

  ------------------ ------------------------------ ------------------------------------
  **Component**      **Technology**                 **Notes**

  Database           PostgreSQL 15+                 Primary data store

  Backend            .NET Core / Node.js            RESTful API services

  ORM                Entity Framework / Sequelize   Database abstraction

  Caching            Redis                          Session & frequently accessed data

  Message Queue      RabbitMQ                       Async processing

  Search             Elasticsearch                  Full-text search for vouchers
  ------------------ ------------------------------ ------------------------------------

**2. Database Conventions**

**2.1 Naming Conventions**

  --------------------- ------------------------------- -----------------------------
  **Element**           **Convention**                  **Example**

  Master Tables         MST\_\<entity_name\>            MST_USER, MST_COA

  Transaction Tables    TXN\_\<entity_name\>            TXN_VOUCHER, TXN_GL_POSTING

  Mapping Tables        MAP\_\<entity1\>\_\<entity2\>   MAP_ROLE_PERMISSION

  History Tables        HIS\_\<entity_name\>            HIS_VOUCHER

  Audit Tables          AUD\_\<entity_name\>            AUD_USER_ACTION

  Primary Key           \<table\>\_id                   voucher_id, user_id

  Foreign Key           \<ref_table\>\_id               created_by_user_id

  Status Column         status                          ENUM values

  Timestamps            created_at, updated_at          TIMESTAMPTZ

  Soft Delete           is_deleted, deleted_at          BOOLEAN, TIMESTAMPTZ
  --------------------- ------------------------------- -----------------------------

**2.2 Standard Audit Columns**

Every table MUST include the following audit columns:

created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP

created_by BIGINT NOT NULL REFERENCES mst_user(user_id)

updated_at TIMESTAMPTZ NULL

updated_by BIGINT NULL REFERENCES mst_user(user_id)

is_deleted BOOLEAN NOT NULL DEFAULT FALSE

deleted_at TIMESTAMPTZ NULL

deleted_by BIGINT NULL REFERENCES mst_user(user_id)

version INTEGER NOT NULL DEFAULT 1 \-- For optimistic locking

**2.3 Data Types Reference**

  --------------------- ----------------------- ---------------------------
  **Use Case**          **PostgreSQL Type**     **Size/Precision**

  Primary Key           BIGSERIAL               Auto-increment

  Amounts/Money         NUMERIC(18,2)           Max 16 digits + 2 decimal

  Percentages           NUMERIC(5,2)            Max 100.00

  Quantities            NUMERIC(18,4)           4 decimal places

  Exchange Rates        NUMERIC(12,6)           6 decimal places

  Short Codes           VARCHAR(20)             Account codes, etc.

  Names                 VARCHAR(200)            Entity names

  Descriptions          VARCHAR(500)            Short descriptions

  Long Text             TEXT                    Unlimited

  Email                 VARCHAR(255)            Standard email length

  Phone                 VARCHAR(20)             With country code

  Status/Enum           VARCHAR(30)             Status values

  Boolean Flags         BOOLEAN                 TRUE/FALSE

  Dates                 DATE                    Date only

  Timestamps            TIMESTAMPTZ             With timezone

  JSON Data             JSONB                   Flexible structured data
  --------------------- ----------------------- ---------------------------

**3. Global Masters**

Global masters form the foundation of the ERP system. All other modules depend on these master tables.

**3.1 Organization (MST_ORGANIZATION)**

Stores the top-level organization/company information. In most cases, this will have a single record for SMFC Ltd.

**3.1.1 Table Definition**

  -------------------- -------------- ---------- ------------- ------------------------------
  **Column**           **Type**       **Null**   **Default**   **Description**

  org_id               BIGSERIAL      NO         Auto          Primary Key

  org_code             VARCHAR(20)    NO         \-            Unique org code (e.g., SMFC)

  org_name             VARCHAR(200)   NO         \-            Full legal name

  short_name           VARCHAR(50)    YES        \-            Short display name

  cin                  VARCHAR(25)    YES        \-            Corporate Identity Number

  pan                  VARCHAR(10)    YES        \-            PAN of organization

  tan                  VARCHAR(10)    YES        \-            TAN for TDS

  gstin                VARCHAR(15)    YES        \-            GST Registration Number

  registered_address   TEXT           NO         \-            Registered office address

  city                 VARCHAR(100)   YES        \-            City

  state_code           VARCHAR(2)     YES        \-            State code for GST

  pincode              VARCHAR(6)     YES        \-            PIN code

  country              VARCHAR(50)    NO         India         Country

  phone                VARCHAR(20)    YES        \-            Primary phone

  email                VARCHAR(255)   YES        \-            Primary email

  website              VARCHAR(255)   YES        \-            Website URL

  logo_path            VARCHAR(500)   YES        \-            Path to logo file

  incorporation_date   DATE           YES        \-            Date of incorporation

  base_currency_id     BIGINT         NO         \-            FK to MST_CURRENCY

  status               VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                             Standard audit columns
  -------------------- -------------- ---------- ------------- ------------------------------

**3.1.2 Indexes**

PRIMARY KEY (org_id)

UNIQUE INDEX idx_org_code ON mst_organization(org_code)

UNIQUE INDEX idx_org_pan ON mst_organization(pan) WHERE pan IS NOT NULL

**3.1.3 Business Rules**

  ------------- ------------------------ ---------------------------------------------------------------------------- ----------------------------------
  **Rule ID**   **Rule**                 **Validation**                                                               **Error Message**

  ORG-001       Unique org_code          No duplicate org_code allowed                                                Organization code already exists

  ORG-002       Valid PAN format         REGEX: \[A-Z\]{5}\[0-9\]{4}\[A-Z\]{1}                                        Invalid PAN format

  ORG-003       Valid GSTIN format       REGEX: \[0-9\]{2}\[A-Z\]{5}\[0-9\]{4}\[A-Z\]{1}\[1-9A-Z\]{1}Z\[0-9A-Z\]{1}   Invalid GSTIN format

  ORG-004       PAN-GSTIN match          GSTIN\[2:12\] must match PAN                                                 GSTIN does not match PAN

  ORG-005       Base currency required   base_currency_id must exist                                                  Base currency is mandatory
  ------------- ------------------------ ---------------------------------------------------------------------------- ----------------------------------

**3.2 Units/Locations (MST_UNIT)**

Represents organizational units or locations. The system supports multi-location accounting with separate books per unit.

**3.2.1 Table Definition**

  -------------------- -------------- ---------- ------------- -------------------------------------
  **Column**           **Type**       **Null**   **Default**   **Description**

  unit_id              BIGSERIAL      NO         Auto          Primary Key

  org_id               BIGINT         NO         \-            FK to MST_ORGANIZATION

  unit_code            VARCHAR(20)    NO         \-            Unique unit code

  unit_name            VARCHAR(200)   NO         \-            Unit name

  unit_type            VARCHAR(30)    NO         \-            HEAD_OFFICE, BRANCH, PROJECT_OFFICE

  parent_unit_id       BIGINT         YES        \-            FK to MST_UNIT (for hierarchy)

  gstin                VARCHAR(15)    YES        \-            Unit-specific GSTIN

  address              TEXT           YES        \-            Unit address

  city                 VARCHAR(100)   YES        \-            City

  state_code           VARCHAR(2)     YES        \-            State code

  pincode              VARCHAR(6)     YES        \-            PIN code

  is_accounting_unit   BOOLEAN        NO         TRUE          Whether separate books maintained

  effective_from       DATE           NO         \-            Unit active from date

  effective_to         DATE           YES        \-            Unit deactivation date

  status               VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE, CLOSED

  \+ Audit Columns                                             Standard audit columns
  -------------------- -------------- ---------- ------------- -------------------------------------

**3.2.2 Indexes**

PRIMARY KEY (unit_id)

UNIQUE INDEX idx_unit_code ON mst_unit(org_id, unit_code)

INDEX idx_unit_parent ON mst_unit(parent_unit_id)

INDEX idx_unit_type ON mst_unit(unit_type)

**3.2.3 Business Rules**

  ------------- -------------------------- ---------------------------------------- -----------------------------
  **Rule ID**   **Rule**                   **Validation**                           **Error Message**

  UNIT-001      Unique unit code per org   org_id + unit_code must be unique        Unit code already exists

  UNIT-002      Valid parent hierarchy     Parent unit must belong to same org      Invalid parent unit

  UNIT-003      No circular hierarchy      Unit cannot be its own ancestor          Circular hierarchy detected

  UNIT-004      Head office required       At least one HEAD_OFFICE must exist      Head office is mandatory

  UNIT-005      GSTIN state match          GSTIN\[0:2\] must match state_code       GSTIN state code mismatch

  UNIT-006      Effective date range       effective_to must be \> effective_from   Invalid date range
  ------------- -------------------------- ---------------------------------------- -----------------------------

**3.3 Departments (MST_DEPARTMENT)**

Organizational departments used for cost allocation and access control.

**3.3.1 Table Definition**

  ------------------- -------------- ---------- ------------- ---------------------------
  **Column**          **Type**       **Null**   **Default**   **Description**

  dept_id             BIGSERIAL      NO         Auto          Primary Key

  org_id              BIGINT         NO         \-            FK to MST_ORGANIZATION

  dept_code           VARCHAR(20)    NO         \-            Unique department code

  dept_name           VARCHAR(200)   NO         \-            Department name

  parent_dept_id      BIGINT         YES        \-            FK to MST_DEPARTMENT

  dept_head_user_id   BIGINT         YES        \-            FK to MST_USER

  cost_center_id      BIGINT         YES        \-            FK to MST_COST_CENTER

  status              VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                            Standard audit columns
  ------------------- -------------- ---------- ------------- ---------------------------

**3.3.2 Business Rules**

  ------------- -------------------------- ----------------------------------- -----------------------------
  **Rule ID**   **Rule**                   **Validation**                      **Error Message**

  DEPT-001      Unique dept code per org   org_id + dept_code must be unique   Department code exists

  DEPT-002      Valid parent hierarchy     Parent must belong to same org      Invalid parent department

  DEPT-003      No circular hierarchy      Dept cannot be its own ancestor     Circular hierarchy detected

  DEPT-004      Cannot delete with users   No active users should be mapped    Department has active users
  ------------- -------------------------- ----------------------------------- -----------------------------

**3.4 Users (MST_USER)**

System users with authentication and authorization details.

**3.4.1 Table Definition**

  ---------------------- -------------- ---------- ------------- -------------------------------------
  **Column**             **Type**       **Null**   **Default**   **Description**

  user_id                BIGSERIAL      NO         Auto          Primary Key

  org_id                 BIGINT         NO         \-            FK to MST_ORGANIZATION

  employee_id            BIGINT         YES        \-            FK to HRIS employee (if applicable)

  username               VARCHAR(50)    NO         \-            Unique login username

  email                  VARCHAR(255)   NO         \-            Email address

  password_hash          VARCHAR(255)   NO         \-            Bcrypt hashed password

  first_name             VARCHAR(100)   NO         \-            First name

  last_name              VARCHAR(100)   YES        \-            Last name

  display_name           VARCHAR(200)   NO         \-            Full display name

  mobile                 VARCHAR(20)    YES        \-            Mobile number

  dept_id                BIGINT         YES        \-            FK to MST_DEPARTMENT

  primary_unit_id        BIGINT         NO         \-            FK to MST_UNIT

  designation            VARCHAR(100)   YES        \-            Job designation

  auth_type              VARCHAR(20)    NO         LOCAL         LOCAL, LDAP, SSO

  ldap_dn                VARCHAR(500)   YES        \-            LDAP DN for AD integration

  is_locked              BOOLEAN        NO         FALSE         Account locked status

  locked_at              TIMESTAMPTZ    YES        \-            Lock timestamp

  lock_reason            VARCHAR(200)   YES        \-            Reason for lock

  failed_attempts        INTEGER        NO         0             Failed login count

  last_login_at          TIMESTAMPTZ    YES        \-            Last successful login

  password_changed_at    TIMESTAMPTZ    YES        \-            Last password change

  must_change_password   BOOLEAN        NO         TRUE          Force password change

  two_factor_enabled     BOOLEAN        NO         FALSE         2FA enabled

  two_factor_secret      VARCHAR(100)   YES        \-            2FA secret key

  status                 VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE, SUSPENDED

  \+ Audit Columns                                               Standard audit columns
  ---------------------- -------------- ---------- ------------- -------------------------------------

**3.4.2 Indexes**

PRIMARY KEY (user_id)

UNIQUE INDEX idx_user_username ON mst_user(username) WHERE is_deleted = FALSE

UNIQUE INDEX idx_user_email ON mst_user(email) WHERE is_deleted = FALSE

INDEX idx_user_dept ON mst_user(dept_id)

INDEX idx_user_unit ON mst_user(primary_unit_id)

INDEX idx_user_status ON mst_user(status)

**3.4.3 Business Rules**

  ------------- ----------------------- ---------------------------------------------------- ---------------------------------------
  **Rule ID**   **Rule**                **Validation**                                       **Error Message**

  USER-001      Unique username         username must be unique (non-deleted)                Username already exists

  USER-002      Unique email            email must be unique (non-deleted)                   Email already registered

  USER-003      Valid email format      REGEX: standard email pattern                        Invalid email format

  USER-004      Password strength       Min 8 chars, 1 upper, 1 lower, 1 number, 1 special   Password does not meet requirements

  USER-005      Lock after 5 failures   Lock account if failed_attempts \>= 5                Account locked due to failed attempts

  USER-006      Password expiry         Force change if password_changed_at \> 90 days       Password expired

  USER-007      Primary unit required   primary_unit_id must be valid                        Primary unit is mandatory
  ------------- ----------------------- ---------------------------------------------------- ---------------------------------------

**3.5 Roles & Permissions**

Role-based access control with granular permissions.

**3.5.1 MST_ROLE Table**

  ------------------ -------------- ---------- ------------- ---------------------------
  **Column**         **Type**       **Null**   **Default**   **Description**

  role_id            BIGSERIAL      NO         Auto          Primary Key

  org_id             BIGINT         NO         \-            FK to MST_ORGANIZATION

  role_code          VARCHAR(50)    NO         \-            Unique role code

  role_name          VARCHAR(200)   NO         \-            Role display name

  role_type          VARCHAR(30)    NO         \-            SYSTEM, CUSTOM

  description        VARCHAR(500)   YES        \-            Role description

  is_admin           BOOLEAN        NO         FALSE         Super admin role

  status             VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                           Standard audit columns
  ------------------ -------------- ---------- ------------- ---------------------------

**3.5.2 MST_PERMISSION Table**

  ----------------- -------------- ---------- ------------- ---------------------------------------------
  **Column**        **Type**       **Null**   **Default**   **Description**

  permission_id     BIGSERIAL      NO         Auto          Primary Key

  module_code       VARCHAR(50)    NO         \-            Module identifier (GL, AR, AP, etc.)

  permission_code   VARCHAR(100)   NO         \-            Unique permission code

  permission_name   VARCHAR(200)   NO         \-            Permission display name

  permission_type   VARCHAR(30)    NO         \-            VIEW, CREATE, EDIT, DELETE, APPROVE, EXPORT

  description       VARCHAR(500)   YES        \-            Permission description
  ----------------- -------------- ---------- ------------- ---------------------------------------------

**3.5.3 MAP_ROLE_PERMISSION Table**

  -------------------- ------------- ---------- ------------- -------------------------
  **Column**           **Type**      **Null**   **Default**   **Description**

  role_permission_id   BIGSERIAL     NO         Auto          Primary Key

  role_id              BIGINT        NO         \-            FK to MST_ROLE

  permission_id        BIGINT        NO         \-            FK to MST_PERMISSION

  \+ Audit Columns                                            Standard audit columns
  -------------------- ------------- ---------- ------------- -------------------------

**3.5.4 MAP_USER_ROLE Table**

  ------------------ ------------- ---------- ------------- -------------------------------------
  **Column**         **Type**      **Null**   **Default**   **Description**

  user_role_id       BIGSERIAL     NO         Auto          Primary Key

  user_id            BIGINT        NO         \-            FK to MST_USER

  role_id            BIGINT        NO         \-            FK to MST_ROLE

  unit_id            BIGINT        YES        \-            FK to MST_UNIT (unit-specific role)

  effective_from     DATE          NO         \-            Role assignment start

  effective_to       DATE          YES        \-            Role assignment end

  \+ Audit Columns                                          Standard audit columns
  ------------------ ------------- ---------- ------------- -------------------------------------

**3.5.5 Sample Permissions (GL Module)**

  ----------------------- ---------------------------- ---------------
  **Permission Code**     **Name**                     **Type**

  GL_VOUCHER_VIEW         View Vouchers                VIEW

  GL_VOUCHER_CREATE       Create Vouchers              CREATE

  GL_VOUCHER_EDIT         Edit Draft Vouchers          EDIT

  GL_VOUCHER_DELETE       Delete Draft Vouchers        DELETE

  GL_VOUCHER_APPROVE_L1   Approve Vouchers Level 1     APPROVE

  GL_VOUCHER_APPROVE_L2   Approve Vouchers Level 2     APPROVE

  GL_VOUCHER_POST         Post Approved Vouchers       APPROVE

  GL_VOUCHER_REVERSE      Reverse Posted Vouchers      EDIT

  GL_PERIOD_MANAGE        Open/Close Periods           EDIT

  GL_REPORT_VIEW          View GL Reports              VIEW

  GL_REPORT_EXPORT        Export GL Reports            EXPORT
  ----------------------- ---------------------------- ---------------

**3.6 Financial Year (MST_FINANCIAL_YEAR)**

Defines financial years with their periods. SMFC follows April-March financial year.

**3.6.1 Table Definition**

  ------------------ ------------- ---------- ------------- ---------------------------
  **Column**         **Type**      **Null**   **Default**   **Description**

  fy_id              BIGSERIAL     NO         Auto          Primary Key

  org_id             BIGINT        NO         \-            FK to MST_ORGANIZATION

  fy_code            VARCHAR(10)   NO         \-            FY code (e.g., 2025-26)

  fy_name            VARCHAR(50)   NO         \-            Display name

  start_date         DATE          NO         \-            FY start date (April 1)

  end_date           DATE          NO         \-            FY end date (March 31)

  is_current         BOOLEAN       NO         FALSE         Current active FY

  status             VARCHAR(20)   NO         OPEN          OPEN, CLOSED, ARCHIVED

  \+ Audit Columns                                          Standard audit columns
  ------------------ ------------- ---------- ------------- ---------------------------

**3.6.2 Business Rules**

  ------------- ------------------------- ------------------------------------ ------------------------------------
  **Rule ID**   **Rule**                  **Validation**                       **Error Message**

  FY-001        No overlapping FYs        Date ranges must not overlap         Financial year dates overlap

  FY-002        Only one current FY       Only one is_current = TRUE allowed   Multiple current FY not allowed

  FY-003        Cannot delete with txns   No transactions should exist         FY has transactions

  FY-004        Sequential dates          end_date must be \> start_date       Invalid date range

  FY-005        Standard duration         Duration should be \~365 days        Non-standard FY duration (warning)
  ------------- ------------------------- ------------------------------------ ------------------------------------

**3.7 Currency (MST_CURRENCY)**

Currency master with exchange rate management.

**3.7.1 MST_CURRENCY Table**

  ------------------ -------------- ---------- ------------- -------------------------------
  **Column**         **Type**       **Null**   **Default**   **Description**

  currency_id        BIGSERIAL      NO         Auto          Primary Key

  currency_code      VARCHAR(3)     NO         \-            ISO 4217 code (INR, USD, EUR)

  currency_name      VARCHAR(100)   NO         \-            Currency name

  currency_symbol    VARCHAR(5)     YES        \-            Symbol (₹, \$, €)

  decimal_places     INTEGER        NO         2             Decimal precision

  is_base_currency   BOOLEAN        NO         FALSE         Base currency flag (INR)

  status             VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                           Standard audit columns
  ------------------ -------------- ---------- ------------- -------------------------------

**3.7.2 MST_EXCHANGE_RATE Table**

  ------------------ --------------- ---------- ------------- ---------------------------
  **Column**         **Type**        **Null**   **Default**   **Description**

  rate_id            BIGSERIAL       NO         Auto          Primary Key

  from_currency_id   BIGINT          NO         \-            FK to MST_CURRENCY

  to_currency_id     BIGINT          NO         \-            FK to MST_CURRENCY

  rate_date          DATE            NO         \-            Rate effective date

  exchange_rate      NUMERIC(12,6)   NO         \-            Conversion rate

  rate_type          VARCHAR(20)     NO         STANDARD      STANDARD, BUYING, SELLING

  source             VARCHAR(50)     YES        \-            Rate source (RBI, Manual)

  \+ Audit Columns                                            Standard audit columns
  ------------------ --------------- ---------- ------------- ---------------------------

**3.7.3 Business Rules**

  ------------- ------------------------ ---------------------------------- --------------------------------------
  **Rule ID**   **Rule**                 **Validation**                     **Error Message**

  CUR-001       Only one base currency   Only one is_base_currency = TRUE   Multiple base currencies not allowed

  CUR-002       Unique currency code     currency_code must be unique       Currency code already exists

  CUR-003       Valid ISO code           Must be valid ISO 4217 code        Invalid currency code

  CUR-004       Rate \> 0                exchange_rate must be positive     Exchange rate must be positive

  CUR-005       No duplicate rate        Unique: from, to, date, type       Rate already exists for date
  ------------- ------------------------ ---------------------------------- --------------------------------------

**3.8 Bank Accounts (MST_BANK_ACCOUNT)**

Organization bank accounts for payment and receipt processing.

**3.8.1 Table Definition**

  ----------------------- --------------- ---------- ------------- -----------------------------------
  **Column**              **Type**        **Null**   **Default**   **Description**

  bank_account_id         BIGSERIAL       NO         Auto          Primary Key

  org_id                  BIGINT          NO         \-            FK to MST_ORGANIZATION

  unit_id                 BIGINT          YES        \-            FK to MST_UNIT

  account_code            VARCHAR(20)     NO         \-            Internal account code

  account_name            VARCHAR(200)    NO         \-            Account name

  bank_name               VARCHAR(200)    NO         \-            Bank name

  branch_name             VARCHAR(200)    YES        \-            Branch name

  account_number          VARCHAR(30)     NO         \-            Bank account number

  ifsc_code               VARCHAR(11)     NO         \-            IFSC code

  swift_code              VARCHAR(11)     YES        \-            SWIFT/BIC code

  account_type            VARCHAR(30)     NO         \-            CURRENT, SAVINGS, OD, CC, FD

  currency_id             BIGINT          NO         \-            FK to MST_CURRENCY

  gl_account_id           BIGINT          NO         \-            FK to MST_COA (linked GL account)

  od_limit                NUMERIC(18,2)   YES        \-            OD/CC limit if applicable

  is_primary              BOOLEAN         NO         FALSE         Primary account flag

  is_payment_enabled      BOOLEAN         NO         TRUE          Can make payments

  is_collection_enabled   BOOLEAN         NO         TRUE          Can receive funds

  contact_person          VARCHAR(200)    YES        \-            Bank contact person

  contact_phone           VARCHAR(20)     YES        \-            Contact phone

  contact_email           VARCHAR(255)    YES        \-            Contact email

  status                  VARCHAR(20)     NO         ACTIVE        ACTIVE, INACTIVE, CLOSED

  \+ Audit Columns                                                 Standard audit columns
  ----------------------- --------------- ---------- ------------- -----------------------------------

**3.8.2 Indexes**

PRIMARY KEY (bank_account_id)

UNIQUE INDEX idx_bank_acc_code ON mst_bank_account(org_id, account_code)

UNIQUE INDEX idx_bank_acc_number ON mst_bank_account(account_number, ifsc_code)

INDEX idx_bank_acc_unit ON mst_bank_account(unit_id)

INDEX idx_bank_acc_gl ON mst_bank_account(gl_account_id)

**3.8.3 Business Rules**

  ------------- ------------------------------ ------------------------------------- ----------------------------------
  **Rule ID**   **Rule**                       **Validation**                        **Error Message**

  BANK-001      Unique account number + IFSC   account_number + ifsc_code unique     Bank account already exists

  BANK-002      Valid IFSC format              REGEX: \[A-Z\]{4}0\[A-Z0-9\]{6}       Invalid IFSC code

  BANK-003      GL account required            gl_account_id must be valid bank GL   GL account mapping required

  BANK-004      One primary per unit           Only one is_primary per unit_id       Unit already has primary account

  BANK-005      Cannot close with balance      GL balance must be zero to close      Account has pending balance
  ------------- ------------------------------ ------------------------------------- ----------------------------------

**4. Accounting Masters**

Accounting-specific master data required for the General Ledger module.

**4.1 Chart of Accounts (MST_COA)**

The Chart of Accounts defines all general ledger accounts organized in a hierarchical structure. This is the most critical master for the accounting module.

**4.1.1 Table Definition**

  ------------------------ --------------- ---------- ------------- -------------------------------------------
  **Column**               **Type**        **Null**   **Default**   **Description**

  account_id               BIGSERIAL       NO         Auto          Primary Key

  org_id                   BIGINT          NO         \-            FK to MST_ORGANIZATION

  account_code             VARCHAR(20)     NO         \-            Unique account code

  account_name             VARCHAR(200)    NO         \-            Account name

  account_name_local       VARCHAR(200)    YES        \-            Name in local language

  parent_account_id        BIGINT          YES        \-            FK to MST_COA (parent)

  account_level            INTEGER         NO         \-            Hierarchy level (1=top)

  account_type             VARCHAR(30)     NO         \-            ASSET, LIABILITY, EQUITY, INCOME, EXPENSE

  account_nature           VARCHAR(10)     NO         \-            DR (Debit), CR (Credit)

  account_category         VARCHAR(50)     NO         \-            Sub-category for grouping

  is_group                 BOOLEAN         NO         FALSE         TRUE = Group, FALSE = Ledger

  is_bank_account          BOOLEAN         NO         FALSE         Bank account flag

  is_cash_account          BOOLEAN         NO         FALSE         Cash account flag

  is_party_account         BOOLEAN         NO         FALSE         Requires party/subledger

  is_cost_center_reqd      BOOLEAN         NO         FALSE         Cost center mandatory

  is_interunit_account     BOOLEAN         NO         FALSE         Inter-unit transaction account

  is_control_account       BOOLEAN         NO         FALSE         Control/summary account

  subledger_type           VARCHAR(30)     YES        \-            CUSTOMER, VENDOR, EMPLOYEE, NONE

  bs_group_id              BIGINT          YES        \-            FK to MST_BS_GROUP

  pnl_group_id             BIGINT          YES        \-            FK to MST_PNL_GROUP

  currency_id              BIGINT          YES        \-            FK to MST_CURRENCY (if FCY)

  is_reconciliation_reqd   BOOLEAN         NO         FALSE         BRS required

  opening_balance          NUMERIC(18,2)   NO         0             Opening balance

  opening_balance_type     VARCHAR(2)      YES        \-            DR or CR

  opening_balance_date     DATE            YES        \-            Opening balance as of date

  status                   VARCHAR(20)     NO         ACTIVE        ACTIVE, INACTIVE, FROZEN

  \+ Audit Columns                                                  Standard audit columns
  ------------------------ --------------- ---------- ------------- -------------------------------------------

**4.1.2 Indexes**

PRIMARY KEY (account_id)

UNIQUE INDEX idx_coa_code ON mst_coa(org_id, account_code)

INDEX idx_coa_parent ON mst_coa(parent_account_id)

INDEX idx_coa_type ON mst_coa(account_type)

INDEX idx_coa_bs_group ON mst_coa(bs_group_id)

INDEX idx_coa_subledger ON mst_coa(subledger_type) WHERE subledger_type IS NOT NULL

**4.1.3 Account Types & Nature**

  ------------------ -------------------- -------------- -------------- -----------------
  **Account Type**   **Normal Balance**   **Increase**   **Decrease**   **BS/PnL**

  ASSET              DR                   Debit          Credit         Balance Sheet

  LIABILITY          CR                   Credit         Debit          Balance Sheet

  EQUITY             CR                   Credit         Debit          Balance Sheet

  INCOME             CR                   Credit         Debit          Profit & Loss

  EXPENSE            DR                   Debit          Credit         Profit & Loss
  ------------------ -------------------- -------------- -------------- -----------------

**4.1.4 Business Rules**

  ------------- ---------------------------- --------------------------------------------------- -----------------------------------
  **Rule ID**   **Rule**                     **Validation**                                      **Error Message**

  COA-001       Unique account code          org_id + account_code must be unique                Account code already exists

  COA-002       Valid parent                 Parent must be group account                        Parent must be a group account

  COA-003       No circular hierarchy        Account cannot be own ancestor                      Circular hierarchy detected

  COA-004       Type matches parent          Account type must match parent type                 Account type mismatch with parent

  COA-005       Cannot post to group         is_group = TRUE cannot have postings                Cannot post to group account

  COA-006       Party type consistency       If is_party_account, subledger_type required        Subledger type required

  COA-007       Bank account mapping         If is_bank_account, must link to MST_BANK_ACCOUNT   Bank account mapping required

  COA-008       BS group required            ASSET/LIABILITY/EQUITY needs bs_group_id            BS group mapping required

  COA-009       Cannot delete with balance   Account balance must be zero                        Account has balance

  COA-010       Cannot delete with txns      No transactions in current FY                       Account has transactions
  ------------- ---------------------------- --------------------------------------------------- -----------------------------------

**4.2 Cost Centers (MST_COST_CENTER)**

Cost centers for departmental expense tracking and allocation.

**4.2.1 Table Definition**

  ------------------ --------------- ---------- ------------- -------------------------------
  **Column**         **Type**        **Null**   **Default**   **Description**

  cost_center_id     BIGSERIAL       NO         Auto          Primary Key

  org_id             BIGINT          NO         \-            FK to MST_ORGANIZATION

  cc_code            VARCHAR(20)     NO         \-            Unique cost center code

  cc_name            VARCHAR(200)    NO         \-            Cost center name

  parent_cc_id       BIGINT          YES        \-            FK to MST_COST_CENTER

  cc_type            VARCHAR(30)     NO         \-            OVERHEAD, PROJECT, DEPARTMENT

  dept_id            BIGINT          YES        \-            FK to MST_DEPARTMENT

  budget_amount      NUMERIC(18,2)   YES        \-            Annual budget

  effective_from     DATE            NO         \-            Active from date

  effective_to       DATE            YES        \-            Deactivation date

  status             VARCHAR(20)     NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                            Standard audit columns
  ------------------ --------------- ---------- ------------- -------------------------------

**4.2.2 Business Rules**

  ------------- ------------------------- --------------------------------- ---------------------------------
  **Rule ID**   **Rule**                  **Validation**                    **Error Message**

  CC-001        Unique CC code            org_id + cc_code must be unique   Cost center code already exists

  CC-002        Valid parent              Parent must be in same org        Invalid parent cost center

  CC-003        Date range valid          effective_to \> effective_from    Invalid date range

  CC-004        Cannot delete with txns   No GL postings against CC         Cost center has transactions
  ------------- ------------------------- --------------------------------- ---------------------------------

**4.3 Balance Sheet Groups (MST_BS_GROUP)**

Balance sheet grouping for financial statement presentation as per Ind-AS / Schedule III.

**4.3.1 Table Definition**

  ------------------ -------------- ---------- ------------- ------------------------------------
  **Column**         **Type**       **Null**   **Default**   **Description**

  bs_group_id        BIGSERIAL      NO         Auto          Primary Key

  org_id             BIGINT         NO         \-            FK to MST_ORGANIZATION

  group_code         VARCHAR(20)    NO         \-            Unique group code

  group_name         VARCHAR(200)   NO         \-            Group name

  parent_group_id    BIGINT         YES        \-            FK to MST_BS_GROUP

  group_type         VARCHAR(30)    NO         \-            ASSET, LIABILITY, EQUITY

  is_current         BOOLEAN        NO         \-            Current vs Non-current

  display_order      INTEGER        NO         \-            Order in BS presentation

  schedule_ref       VARCHAR(50)    YES        \-            Schedule reference (Note 1, 2\...)

  status             VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                           Standard audit columns
  ------------------ -------------- ---------- ------------- ------------------------------------

**4.3.2 Standard BS Groups (Ind-AS)**

  ---------------- ------------------------------- ------------- --------------
  **Group Code**   **Group Name**                  **Type**      **Current**

  A-NCA-PPE        Property, Plant and Equipment   ASSET         Non-Current

  A-NCA-INTANG     Intangible Assets               ASSET         Non-Current

  A-NCA-FINAST     Non-Current Financial Assets    ASSET         Non-Current

  A-CA-INV         Inventories                     ASSET         Current

  A-CA-FINAST      Current Financial Assets        ASSET         Current

  A-CA-CASH        Cash and Cash Equivalents       ASSET         Current

  L-NCL-BORROW     Non-Current Borrowings          LIABILITY     Non-Current

  L-NCL-PROV       Non-Current Provisions          LIABILITY     Non-Current

  L-CL-BORROW      Current Borrowings              LIABILITY     Current

  L-CL-TRADE       Trade Payables                  LIABILITY     Current

  E-SHARE          Share Capital                   EQUITY        \-

  E-RESERVE        Reserves and Surplus            EQUITY        \-
  ---------------- ------------------------------- ------------- --------------

**4.4 Voucher Types (MST_VOUCHER_TYPE)**

Defines different types of accounting vouchers with their behavior and numbering rules.

**4.4.1 Table Definition**

  ----------------------- -------------- ---------- ------------- -----------------------------------
  **Column**              **Type**       **Null**   **Default**   **Description**

  voucher_type_id         BIGSERIAL      NO         Auto          Primary Key

  org_id                  BIGINT         NO         \-            FK to MST_ORGANIZATION

  type_code               VARCHAR(10)    NO         \-            Short code (JV, BPV, BRV, etc.)

  type_name               VARCHAR(100)   NO         \-            Full name

  type_category           VARCHAR(30)    NO         \-            JOURNAL, PAYMENT, RECEIPT, CONTRA

  default_dr_account_id   BIGINT         YES        \-            Default debit account

  default_cr_account_id   BIGINT         YES        \-            Default credit account

  is_bank_voucher         BOOLEAN        NO         FALSE         Involves bank account

  is_cash_voucher         BOOLEAN        NO         FALSE         Involves cash account

  requires_party          BOOLEAN        NO         FALSE         Party/subledger mandatory

  requires_cheque         BOOLEAN        NO         FALSE         Cheque details required

  requires_narration      BOOLEAN        NO         TRUE          Narration mandatory

  auto_numbering          BOOLEAN        NO         TRUE          System generates number

  number_prefix           VARCHAR(10)    YES        \-            Voucher number prefix

  number_format           VARCHAR(50)    YES        \-            Format pattern

  reset_frequency         VARCHAR(20)    NO         YEARLY        YEARLY, MONTHLY, NEVER

  status                  VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                                Standard audit columns
  ----------------------- -------------- ---------- ------------- -----------------------------------

**4.4.2 Standard Voucher Types**

  ---------- ---------------------- -------------- ---------- ---------- -------------------------
  **Code**   **Name**               **Category**   **Bank**   **Cash**   **Description**

  JV         Journal Voucher        JOURNAL        No         No         General journal entries

  BPV        Bank Payment Voucher   PAYMENT        Yes        No         Payments via bank

  CPV        Cash Payment Voucher   PAYMENT        No         Yes        Cash payments

  BRV        Bank Receipt Voucher   RECEIPT        Yes        No         Receipts via bank

  CRV        Cash Receipt Voucher   RECEIPT        No         Yes        Cash receipts

  CONTRA     Contra Voucher         CONTRA         Yes        Yes        Bank to cash transfer

  ADJ        Adjustment Voucher     JOURNAL        No         No         Year-end adjustments

  REV        Reversal Voucher       JOURNAL        No         No         Reversal entries
  ---------- ---------------------- -------------- ---------- ---------- -------------------------

**4.4.3 MST_VOUCHER_NUMBERING Table**

Tracks current voucher numbers per type, unit, and period.

  ------------------ ------------- ---------- ------------- ---------------------------
  **Column**         **Type**      **Null**   **Default**   **Description**

  numbering_id       BIGSERIAL     NO         Auto          Primary Key

  voucher_type_id    BIGINT        NO         \-            FK to MST_VOUCHER_TYPE

  unit_id            BIGINT        NO         \-            FK to MST_UNIT

  fy_id              BIGINT        NO         \-            FK to MST_FINANCIAL_YEAR

  period_month       INTEGER       YES        \-            Month (if monthly reset)

  last_number        INTEGER       NO         0             Last used number

  \+ Audit Columns                                          Standard audit columns
  ------------------ ------------- ---------- ------------- ---------------------------

**4.5 Approval Matrix (MST_APPROVAL_MATRIX)**

Defines financial limits and approval workflow for vouchers based on amount and voucher type.

**4.5.1 Table Definition**

  ---------------------- --------------- ---------- ------------- -----------------------------------
  **Column**             **Type**        **Null**   **Default**   **Description**

  matrix_id              BIGSERIAL       NO         Auto          Primary Key

  org_id                 BIGINT          NO         \-            FK to MST_ORGANIZATION

  voucher_type_id        BIGINT          YES        \-            FK to MST_VOUCHER_TYPE (NULL=all)

  unit_id                BIGINT          YES        \-            FK to MST_UNIT (NULL=all units)

  min_amount             NUMERIC(18,2)   NO         0             Minimum amount (inclusive)

  max_amount             NUMERIC(18,2)   YES        \-            Maximum amount (NULL=unlimited)

  approval_level         INTEGER         NO         \-            Level sequence (1, 2, 3\...)

  approver_role_id       BIGINT          YES        \-            FK to MST_ROLE

  approver_user_id       BIGINT          YES        \-            FK to MST_USER (specific user)

  approver_designation   VARCHAR(100)    YES        \-            Designation-based approval

  is_mandatory           BOOLEAN         NO         TRUE          Cannot skip this level

  can_self_approve       BOOLEAN         NO         FALSE         Creator can approve own voucher

  sla_hours              INTEGER         YES        \-            SLA for approval (hours)

  escalation_user_id     BIGINT          YES        \-            Escalate to if SLA breached

  status                 VARCHAR(20)     NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                                Standard audit columns
  ---------------------- --------------- ---------- ------------- -----------------------------------

**4.5.2 Sample Approval Matrix**

  ------------------ ---------------------- ----------- --------------------- -----------
  **Voucher Type**   **Amount Range**       **Level**   **Approver**          **SLA**

  All                0 - 50,000             1           Finance Officer       4 hrs

  All                50,001 - 2,00,000      1           Finance Officer       4 hrs

  All                50,001 - 2,00,000      2           Sr. Finance Manager   8 hrs

  All                2,00,001 - 10,00,000   1           Finance Officer       4 hrs

  All                2,00,001 - 10,00,000   2           Sr. Finance Manager   8 hrs

  All                2,00,001 - 10,00,000   3           CFO                   24 hrs

  All                \> 10,00,000           1-3         As above              \-

  All                \> 10,00,000           4           MD/Board              48 hrs
  ------------------ ---------------------- ----------- --------------------- -----------

**4.5.3 Business Rules**

  ------------- -------------------------- ------------------------------------------------- ---------------------------------
  **Rule ID**   **Rule**                   **Validation**                                    **Error Message**

  APPR-001      No overlapping amounts     Amount ranges cannot overlap for same type/unit   Overlapping approval ranges

  APPR-002      Sequential levels          Levels must be sequential (1, 2, 3\...)           Invalid approval level sequence

  APPR-003      At least one approver      Either role_id or user_id required                Approver not specified

  APPR-004      Self-approve restriction   If can_self_approve=FALSE, validate               Cannot approve own voucher

  APPR-005      Complete coverage          All amount ranges must be covered                 Gap in approval amount coverage
  ------------- -------------------------- ------------------------------------------------- ---------------------------------

**\-\-- Continued in Part 2 \-\--**

Part 2 of this document covers:

- Section 5: General Ledger Module (Transaction Tables)

- Section 6: Business Flows with Flowcharts

- Section 7: Complete Business Rules & Validations

- Section 8: State Machines

- Section 9: API Contracts

- Section 10: Audit Requirements
