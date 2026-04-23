**SMFC Ltd**

Integrated ERP Solution

**TECHNICAL SPECIFICATION**

Phase 5: HRIS & Payroll

Employee Management, Attendance, Leave, Payroll Processing

**Table of Contents**

1\. Module Overview

2\. Employee Master (MST_EMPLOYEE)

3\. Organization Structure

4\. Leave Management

5\. Attendance Management

6\. Payroll Configuration

7\. Salary Processing

8\. Statutory Compliance

9\. Business Flows

10\. Business Rules

**1. Module Overview**

Comprehensive Human Resource Information System (HRIS) with integrated payroll for managing employee lifecycle, attendance, leave, and compensation.

**1.1 Scope**

- Employee Master: Complete employee information management

- Organization Structure: Designations, grades, pay scales, reporting hierarchy

- Leave Management: Leave types, balances, applications, approvals

- Attendance: Biometric integration, regularization, shift management

- Payroll: Salary structure, processing, arrears, full & final

- Statutory: PF, ESI, PT, TDS (Form 16), LWF compliance

- Self-Service: Employee portal for leave, attendance, payslips

**1.2 Data Model Overview**

MST_EMPLOYEE (Core employee record)

\|\-- MST_EMPLOYEE_PERSONAL (Personal details)

\|\-- MST_EMPLOYEE_QUALIFICATION (Education)

\|\-- MST_EMPLOYEE_EXPERIENCE (Work history)

\|\-- MST_EMPLOYEE_FAMILY (Dependents)

\|\-- MST_EMPLOYEE_BANK (Bank accounts)

\|\-- MST_EMPLOYEE_DOCUMENT (Documents)

\|\-- TXN_EMPLOYEE_SALARY (Salary structure)

\|\-- TXN_LEAVE_BALANCE (Leave balances)

\|\-- TXN_LEAVE_APPLICATION (Leave requests)

\|\-- TXN_ATTENDANCE (Daily attendance)

\|\-- TXN_PAYROLL (Monthly payroll)

**2. Employee Master (MST_EMPLOYEE)**

Core employee record with employment details.

**2.1 Table Definition**

  ---------------------------- -------------- ---------- ------------- -----------------------------------------------------
  **Column**                   **Type**       **Null**   **Default**   **Description**

  employee_id                  BIGSERIAL      NO         Auto          Primary Key

  org_id                       BIGINT         NO         \-            FK to MST_ORGANIZATION

  employee_code                VARCHAR(20)    NO         \-            Unique employee code

  salutation                   VARCHAR(10)    YES        \-            Mr, Ms, Dr, etc.

  first_name                   VARCHAR(100)   NO         \-            First name

  middle_name                  VARCHAR(100)   YES        \-            Middle name

  last_name                    VARCHAR(100)   YES        \-            Last name

  full_name                    VARCHAR(300)   NO         \-            Computed full name

  gender                       VARCHAR(10)    NO         \-            MALE, FEMALE, OTHER

  date_of_birth                DATE           NO         \-            Date of birth

  blood_group                  VARCHAR(5)     YES        \-            Blood group

  marital_status               VARCHAR(20)    YES        \-            SINGLE, MARRIED, DIVORCED, WIDOWED

  nationality                  VARCHAR(50)    NO         Indian        Nationality

  religion                     VARCHAR(50)    YES        \-            Religion

  caste_category               VARCHAR(20)    YES        \-            GENERAL, OBC, SC, ST, EWS

  personal_email               VARCHAR(255)   YES        \-            Personal email

  official_email               VARCHAR(255)   YES        \-            Official email

  mobile                       VARCHAR(15)    NO         \-            Mobile number

  alternate_mobile             VARCHAR(15)    YES        \-            Alternate contact

  emergency_contact            VARCHAR(200)   YES        \-            Emergency contact details

  pan                          VARCHAR(10)    NO         \-            PAN number

  aadhaar_masked               VARCHAR(16)    YES        \-            Masked Aadhaar

  passport_number              VARCHAR(20)    YES        \-            Passport number

  passport_expiry              DATE           YES        \-            Passport expiry date

  driving_license              VARCHAR(20)    YES        \-            DL number

  voter_id                     VARCHAR(20)    YES        \-            Voter ID

  unit_id                      BIGINT         NO         \-            FK to MST_UNIT (posting location)

  department_id                BIGINT         NO         \-            FK to MST_DEPARTMENT

  designation_id               BIGINT         NO         \-            FK to MST_DESIGNATION

  grade_id                     BIGINT         YES        \-            FK to MST_GRADE

  reporting_to                 BIGINT         YES        \-            FK to MST_EMPLOYEE (manager)

  employment_type              VARCHAR(20)    NO         \-            PERMANENT, CONTRACT, PROBATION, TRAINEE, CONSULTANT

  date_of_joining              DATE           NO         \-            Joining date

  confirmation_date            DATE           YES        \-            Confirmation date

  probation_end_date           DATE           YES        \-            Probation end date

  contract_end_date            DATE           YES        \-            For contract employees

  previous_experience_months   INTEGER        NO         0             Prior experience

  retirement_date              DATE           YES        \-            Computed retirement date

  date_of_leaving              DATE           YES        \-            If separated

  separation_type              VARCHAR(30)    YES        \-            RESIGNATION, TERMINATION, RETIREMENT, VRS, DEATH

  separation_reason            TEXT           YES        \-            Separation details

  notice_period_days           INTEGER        YES        \-            Notice period

  pf_applicable                BOOLEAN        NO         TRUE          PF applicable

  pf_number                    VARCHAR(30)    YES        \-            PF account number

  uan                          VARCHAR(15)    YES        \-            Universal Account Number

  esi_applicable               BOOLEAN        NO         FALSE         ESI applicable

  esi_number                   VARCHAR(20)    YES        \-            ESI number

  pt_applicable                BOOLEAN        NO         TRUE          Prof Tax applicable

  pt_state                     VARCHAR(50)    YES        \-            PT deduction state

  lwf_applicable               BOOLEAN        NO         FALSE         Labour Welfare Fund

  gratuity_applicable          BOOLEAN        NO         TRUE          Gratuity eligible

  photo_path                   VARCHAR(500)   YES        \-            Employee photo

  signature_path               VARCHAR(500)   YES        \-            Signature specimen

  user_id                      BIGINT         YES        \-            FK to MST_USER (ERP login)

  status                       VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE, SEPARATED, ON_NOTICE

  \+ Audit Columns                                                     Standard audit columns
  ---------------------------- -------------- ---------- ------------- -----------------------------------------------------

**2.2 Employee Code Format**

Format: SMFC/{LOCATION}/{TYPE}/{SEQUENCE}

Example: SMFC/DEL/P/0001 (Permanent employee)

SMFC/MUM/C/0025 (Contract employee)

Type Codes:

P - Permanent

C - Contract

T - Trainee

N - Consultant

**2.3 Employee Personal Details (MST_EMPLOYEE_PERSONAL)**

  ----------------------- -------------- ---------- ------------- -------------------------------
  **Column**              **Type**       **Null**   **Default**   **Description**

  personal_id             BIGSERIAL      NO         Auto          Primary Key

  employee_id             BIGINT         NO         \-            FK to MST_EMPLOYEE

  current_address         TEXT           NO         \-            Current residential address

  current_city            VARCHAR(100)   NO         \-            City

  current_state           VARCHAR(100)   NO         \-            State

  current_pincode         VARCHAR(6)     NO         \-            PIN code

  permanent_address       TEXT           YES        \-            Permanent address

  permanent_city          VARCHAR(100)   YES        \-            City

  permanent_state         VARCHAR(100)   YES        \-            State

  permanent_pincode       VARCHAR(6)     YES        \-            PIN code

  is_address_same         BOOLEAN        NO         FALSE         Current = Permanent

  father_name             VARCHAR(200)   YES        \-            Father\'s name

  mother_name             VARCHAR(200)   YES        \-            Mother\'s name

  spouse_name             VARCHAR(200)   YES        \-            Spouse name

  spouse_dob              DATE           YES        \-            Spouse DOB

  spouse_occupation       VARCHAR(100)   YES        \-            Spouse occupation

  marriage_date           DATE           YES        \-            Marriage date

  children_count          INTEGER        NO         0             Number of children

  physically_challenged   BOOLEAN        NO         FALSE         PwD status

  disability_type         VARCHAR(100)   YES        \-            Type of disability

  disability_pct          NUMERIC(5,2)   YES        \-            Disability percentage

  \+ Audit Columns                                                Standard audit columns
  ----------------------- -------------- ---------- ------------- -------------------------------

**2.4 Employee Bank Account (MST_EMPLOYEE_BANK)**

  -------------------------- -------------- ---------- ------------- ------------------------------
  **Column**                 **Type**       **Null**   **Default**   **Description**

  emp_bank_id                BIGSERIAL      NO         Auto          Primary Key

  employee_id                BIGINT         NO         \-            FK to MST_EMPLOYEE

  account_holder_name        VARCHAR(200)   NO         \-            Name as per bank

  bank_name                  VARCHAR(200)   NO         \-            Bank name

  branch_name                VARCHAR(200)   YES        \-            Branch

  account_number             VARCHAR(30)    NO         \-            Account number

  ifsc_code                  VARCHAR(11)    NO         \-            IFSC code

  account_type               VARCHAR(20)    NO         \-            SAVINGS, CURRENT

  is_salary_account          BOOLEAN        NO         TRUE          For salary credit

  is_reimbursement_account   BOOLEAN        NO         FALSE         For reimbursements

  verified                   BOOLEAN        NO         FALSE         Bank verified

  verified_date              DATE           YES        \-            Verification date

  status                     VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                                   Standard audit columns
  -------------------------- -------------- ---------- ------------- ------------------------------

**2.5 Employee Family (MST_EMPLOYEE_FAMILY)**

  ------------------ -------------- ---------- ------------- ----------------------------------------
  **Column**         **Type**       **Null**   **Default**   **Description**

  family_id          BIGSERIAL      NO         Auto          Primary Key

  employee_id        BIGINT         NO         \-            FK to MST_EMPLOYEE

  relation           VARCHAR(30)    NO         \-            FATHER, MOTHER, SPOUSE, CHILD, SIBLING

  name               VARCHAR(200)   NO         \-            Family member name

  date_of_birth      DATE           YES        \-            DOB

  gender             VARCHAR(10)    YES        \-            Gender

  occupation         VARCHAR(100)   YES        \-            Occupation

  is_dependent       BOOLEAN        NO         FALSE         Is dependent

  is_nominee         BOOLEAN        NO         FALSE         Nominee for benefits

  nominee_pct        NUMERIC(5,2)   YES        \-            Nominee percentage

  aadhaar_masked     VARCHAR(16)    YES        \-            Aadhaar if available

  for_insurance      BOOLEAN        NO         FALSE         Covered in insurance

  status             VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                           Standard audit columns
  ------------------ -------------- ---------- ------------- ----------------------------------------

**3. Organization Structure**

Hierarchical organization setup for reporting and payroll.

**3.1 Designation Master (MST_DESIGNATION)**

  ------------------------ -------------- ---------- ------------- ------------------------------
  **Column**               **Type**       **Null**   **Default**   **Description**

  designation_id           BIGSERIAL      NO         Auto          Primary Key

  org_id                   BIGINT         NO         \-            FK to MST_ORGANIZATION

  designation_code         VARCHAR(20)    NO         \-            Unique code

  designation_name         VARCHAR(100)   NO         \-            Designation title

  short_name               VARCHAR(50)    YES        \-            Short form

  designation_level        INTEGER        NO         \-            Hierarchy level (1=top)

  job_description          TEXT           YES        \-            JD summary

  min_experience_years     INTEGER        YES        \-            Min experience needed

  max_headcount            INTEGER        YES        \-            Sanctioned positions

  reports_to_designation   BIGINT         YES        \-            Reporting designation

  status                   VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                                 Standard audit columns
  ------------------------ -------------- ---------- ------------- ------------------------------

**3.2 Grade/Pay Band (MST_GRADE)**

  ---------------------- --------------- ---------- ------------- ------------------------------
  **Column**             **Type**        **Null**   **Default**   **Description**

  grade_id               BIGSERIAL       NO         Auto          Primary Key

  org_id                 BIGINT          NO         \-            FK to MST_ORGANIZATION

  grade_code             VARCHAR(20)     NO         \-            Grade code

  grade_name             VARCHAR(100)    NO         \-            Grade description

  grade_level            INTEGER         NO         \-            Grade level

  min_basic              NUMERIC(12,2)   NO         \-            Minimum basic salary

  max_basic              NUMERIC(12,2)   NO         \-            Maximum basic salary

  annual_increment_pct   NUMERIC(5,2)    YES        \-            Standard increment %

  probation_months       INTEGER         NO         6             Probation period

  notice_period_days     INTEGER         NO         30            Notice period

  leave_eligibility      JSONB           YES        \-            Leave quotas by type

  perks_eligibility      JSONB           YES        \-            Perks/allowances eligibility

  status                 VARCHAR(20)     NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                                Standard audit columns
  ---------------------- --------------- ---------- ------------- ------------------------------

**3.3 Sample Grade Structure**

  ----------- ----------- ----------------------- ---------------------------- -------------------
  **Grade**   **Level**   **Basic Range**         **Designations**             **Notice Period**

  E1          10          ₹30,000 - ₹50,000       Jr. Officer, Executive       30 days

  E2          9           ₹50,000 - ₹75,000       Sr. Officer, Sr. Executive   30 days

  E3          8           ₹75,000 - ₹1,00,000     Asst. Manager                60 days

  E4          7           ₹1,00,000 - ₹1,50,000   Manager                      60 days

  E5          6           ₹1,50,000 - ₹2,00,000   Sr. Manager                  90 days

  E6          5           ₹2,00,000 - ₹2,75,000   AGM, DGM                     90 days

  E7          4           ₹2,75,000 - ₹3,50,000   GM                           90 days

  E8          3           ₹3,50,000 - ₹5,00,000   CGM, VP                      90 days

  E9          2           ₹5,00,000 - ₹7,50,000   ED, SVP                      90 days

  E10         1           ₹7,50,000+              MD, CEO                      180 days
  ----------- ----------- ----------------------- ---------------------------- -------------------

**4. Leave Management**

Complete leave lifecycle from configuration to encashment.

**4.1 Leave Type Master (MST_LEAVE_TYPE)**

  ---------------------------- -------------- ---------- ------------- -----------------------------------------------------------
  **Column**                   **Type**       **Null**   **Default**   **Description**

  leave_type_id                BIGSERIAL      NO         Auto          Primary Key

  org_id                       BIGINT         NO         \-            FK to MST_ORGANIZATION

  leave_code                   VARCHAR(10)    NO         \-            Leave type code

  leave_name                   VARCHAR(100)   NO         \-            Leave name

  leave_category               VARCHAR(30)    NO         \-            EARNED, CASUAL, SICK, MATERNITY, PATERNITY, COMP_OFF, LOP

  annual_quota                 NUMERIC(5,2)   NO         \-            Annual entitlement

  credit_frequency             VARCHAR(20)    NO         \-            YEARLY, HALF_YEARLY, QUARTERLY, MONTHLY

  credit_month                 INTEGER        YES        \-            Month for yearly credit (1-12)

  prorate_on_joining           BOOLEAN        NO         TRUE          Prorate for new joiners

  carry_forward                BOOLEAN        NO         FALSE         Allow carry forward

  max_carry_forward            NUMERIC(5,2)   YES        \-            Max CF days

  cf_expiry_months             INTEGER        YES        \-            CF expiry in months

  encashment_allowed           BOOLEAN        NO         FALSE         Leave encashment

  max_encashment               NUMERIC(5,2)   YES        \-            Max encashable days

  encashment_frequency         VARCHAR(20)    YES        \-            YEARLY, ON_SEPARATION

  accumulation_limit           NUMERIC(5,2)   YES        \-            Max accumulation

  min_days_per_application     NUMERIC(3,1)   NO         0.5           Min leave days

  max_days_per_application     NUMERIC(5,2)   YES        \-            Max per application

  advance_days_required        INTEGER        NO         0             Advance notice days

  document_required            BOOLEAN        NO         FALSE         Supporting doc needed

  document_for_days            INTEGER        YES        \-            Doc required if \> days

  half_day_allowed             BOOLEAN        NO         TRUE          Half-day leave allowed

  clubbing_allowed             BOOLEAN        NO         TRUE          Club with other leave

  holiday_between_counts       BOOLEAN        NO         FALSE         Count holidays between

  negative_balance_allowed     BOOLEAN        NO         FALSE         Allow negative balance

  max_negative                 NUMERIC(5,2)   YES        \-            Max negative days

  applicable_gender            VARCHAR(10)    YES        ALL           MALE, FEMALE, ALL

  applicable_employment_type   JSONB          YES        \-            Applicable to which types

  waiting_period_months        INTEGER        NO         0             Wait after joining

  status                       VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                                     Standard audit columns
  ---------------------------- -------------- ---------- ------------- -----------------------------------------------------------

**4.2 Standard Leave Types**

  ---------- -------------------- -------------- -------------------- --------------------
  **Code**   **Leave Type**       **Quota**      **Carry Forward**    **Encashment**

  EL         Earned Leave         30 days/year   Yes, max 60 days     Yes, on separation

  CL         Casual Leave         12 days/year   No                   No

  SL         Sick Leave           12 days/year   Yes, max 24 days     No

  ML         Maternity Leave      26 weeks       No                   No

  PL         Paternity Leave      15 days        No                   No

  CO         Compensatory Off     As earned      Expires in 30 days   No

  LOP        Loss of Pay          Unlimited      No                   No

  RH         Restricted Holiday   2 days/year    No                   No

  SPL        Special Leave        As approved    No                   No
  ---------- -------------------- -------------- -------------------- --------------------

**4.3 Leave Balance (TXN_LEAVE_BALANCE)**

  ------------------- -------------- ---------- ------------- -------------------------------
  **Column**          **Type**       **Null**   **Default**   **Description**

  balance_id          BIGSERIAL      NO         Auto          Primary Key

  employee_id         BIGINT         NO         \-            FK to MST_EMPLOYEE

  leave_type_id       BIGINT         NO         \-            FK to MST_LEAVE_TYPE

  financial_year      VARCHAR(10)    NO         \-            Financial year

  opening_balance     NUMERIC(5,2)   NO         0             Balance at year start

  credited            NUMERIC(5,2)   NO         0             Credited during year

  availed             NUMERIC(5,2)   NO         0             Leave taken

  lapsed              NUMERIC(5,2)   NO         0             Lapsed leaves

  encashed            NUMERIC(5,2)   NO         0             Encashed leaves

  adjusted            NUMERIC(5,2)   NO         0             Manual adjustments

  closing_balance     NUMERIC(5,2)   NO         0             Current balance

  carry_forward_due   NUMERIC(5,2)   NO         0             To CF to next year

  last_updated        TIMESTAMPTZ    NO         \-            Last calculation date

  \+ Audit Columns                                            Standard audit columns
  ------------------- -------------- ---------- ------------- -------------------------------

**4.4 Leave Application (TXN_LEAVE_APPLICATION)**

  ---------------------- -------------- ---------- ------------- ---------------------------------------------------
  **Column**             **Type**       **Null**   **Default**   **Description**

  application_id         BIGSERIAL      NO         Auto          Primary Key

  employee_id            BIGINT         NO         \-            FK to MST_EMPLOYEE

  leave_type_id          BIGINT         NO         \-            FK to MST_LEAVE_TYPE

  application_date       DATE           NO         \-            Application submission date

  from_date              DATE           NO         \-            Leave start date

  to_date                DATE           NO         \-            Leave end date

  from_half              VARCHAR(10)    YES        \-            FIRST_HALF, SECOND_HALF

  to_half                VARCHAR(10)    YES        \-            FIRST_HALF, SECOND_HALF

  total_days             NUMERIC(5,2)   NO         \-            Total leave days

  reason                 TEXT           NO         \-            Leave reason

  contact_during_leave   VARCHAR(100)   YES        \-            Emergency contact

  address_during_leave   TEXT           YES        \-            Address during leave

  document_path          VARCHAR(500)   YES        \-            Supporting document

  reporting_manager_id   BIGINT         NO         \-            FK to MST_EMPLOYEE

  balance_before         NUMERIC(5,2)   NO         \-            Balance before application

  balance_after          NUMERIC(5,2)   NO         \-            Balance after approval

  status                 VARCHAR(20)    NO         PENDING       PENDING, APPROVED, REJECTED, CANCELLED, WITHDRAWN

  approved_by            BIGINT         YES        \-            Approver employee ID

  approved_date          DATE           YES        \-            Approval date

  rejection_reason       VARCHAR(500)   YES        \-            If rejected

  cancellation_reason    VARCHAR(500)   YES        \-            If cancelled

  is_emergency           BOOLEAN        NO         FALSE         Emergency leave

  comp_off_date          DATE           YES        \-            If comp-off, worked date

  \+ Audit Columns                                               Standard audit columns
  ---------------------- -------------- ---------- ------------- ---------------------------------------------------

**5. Attendance Management**

Daily attendance tracking with biometric integration.

**5.1 Shift Master (MST_SHIFT)**

  -------------------------- --------------- ---------- ------------- ------------------------------
  **Column**                 **Type**        **Null**   **Default**   **Description**

  shift_id                   BIGSERIAL       NO         Auto          Primary Key

  org_id                     BIGINT          NO         \-            FK to MST_ORGANIZATION

  shift_code                 VARCHAR(10)     NO         \-            Shift code

  shift_name                 VARCHAR(100)    NO         \-            Shift name

  start_time                 TIME            NO         \-            Shift start time

  end_time                   TIME            NO         \-            Shift end time

  break_minutes              INTEGER         NO         60            Break duration

  working_hours              NUMERIC(4,2)    NO         \-            Working hours

  grace_minutes_in           INTEGER         NO         15            Grace for late coming

  grace_minutes_out          INTEGER         NO         15            Grace for early going

  half_day_hours             NUMERIC(4,2)    YES        \-            Min hours for half day

  full_day_hours             NUMERIC(4,2)    YES        \-            Min hours for full day

  overtime_threshold_hours   NUMERIC(4,2)    YES        \-            OT calculation threshold

  is_night_shift             BOOLEAN         NO         FALSE         Night shift flag

  night_shift_allowance      NUMERIC(10,2)   YES        \-            Night shift allowance

  status                     VARCHAR(20)     NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                                    Standard audit columns
  -------------------------- --------------- ---------- ------------- ------------------------------

**5.2 Daily Attendance (TXN_ATTENDANCE)**

  ----------------------- -------------- ---------- ------------- -----------------------------------------------------
  **Column**              **Type**       **Null**   **Default**   **Description**

  attendance_id           BIGSERIAL      NO         Auto          Primary Key

  employee_id             BIGINT         NO         \-            FK to MST_EMPLOYEE

  attendance_date         DATE           NO         \-            Attendance date

  shift_id                BIGINT         YES        \-            FK to MST_SHIFT

  first_in                TIMESTAMPTZ    YES        \-            First punch-in time

  last_out                TIMESTAMPTZ    YES        \-            Last punch-out time

  total_hours             NUMERIC(5,2)   YES        \-            Total working hours

  overtime_hours          NUMERIC(5,2)   NO         0             Overtime hours

  late_minutes            INTEGER        NO         0             Late by minutes

  early_out_minutes       INTEGER        NO         0             Early out by minutes

  attendance_status       VARCHAR(20)    NO         \-            PRESENT, ABSENT, HALF_DAY, LEAVE, HOLIDAY, WEEK_OFF

  leave_type_id           BIGINT         YES        \-            FK if on leave

  leave_application_id    BIGINT         YES        \-            FK to leave application

  punch_records           JSONB          YES        \-            All punch records

  is_regularized          BOOLEAN        NO         FALSE         Attendance regularized

  regularization_reason   VARCHAR(500)   YES        \-            Regularization reason

  regularized_by          BIGINT         YES        \-            FK to MST_USER

  is_on_duty              BOOLEAN        NO         FALSE         On official duty

  od_reason               VARCHAR(500)   YES        \-            OD reason

  wfh                     BOOLEAN        NO         FALSE         Work from home

  remarks                 VARCHAR(500)   YES        \-            Any remarks

  processed_for_payroll   BOOLEAN        NO         FALSE         Included in payroll

  payroll_month           VARCHAR(10)    YES        \-            Payroll period

  \+ Audit Columns                                                Standard audit columns
  ----------------------- -------------- ---------- ------------- -----------------------------------------------------

**5.3 Attendance Status Derivation**

FUNCTION derive_attendance_status(employee_id, date):

\-- Check if holiday

IF is_holiday(date) THEN RETURN \'HOLIDAY\'

\-- Check if week off

IF is_week_off(employee_id, date) THEN RETURN \'WEEK_OFF\'

\-- Check if on approved leave

leave = get_approved_leave(employee_id, date)

IF leave EXISTS THEN RETURN \'LEAVE\'

\-- Check punch records

IF no_punch_record THEN RETURN \'ABSENT\'

\-- Calculate working hours

hours = last_out - first_in - break_minutes

IF hours \>= shift.full_day_hours THEN RETURN \'PRESENT\'

ELSE IF hours \>= shift.half_day_hours THEN RETURN \'HALF_DAY\'

ELSE RETURN \'ABSENT\'

**6. Payroll Configuration**

Salary components, structures, and calculation rules.

**6.1 Salary Component Master (MST_SALARY_COMPONENT)**

  --------------------- --------------- ---------- ------------- -------------------------------------------
  **Column**            **Type**        **Null**   **Default**   **Description**

  component_id          BIGSERIAL       NO         Auto          Primary Key

  org_id                BIGINT          NO         \-            FK to MST_ORGANIZATION

  component_code        VARCHAR(20)     NO         \-            Component code

  component_name        VARCHAR(100)    NO         \-            Component name

  component_type        VARCHAR(20)     NO         \-            EARNING, DEDUCTION, EMPLOYER_CONTRIB

  component_category    VARCHAR(30)     NO         \-            FIXED, VARIABLE, STATUTORY, REIMBURSEMENT

  calculation_type      VARCHAR(20)     NO         \-            FIXED, PERCENTAGE, FORMULA, SLAB

  base_component_id     BIGINT          YES        \-            Base for percentage calc

  percentage_value      NUMERIC(5,2)    YES        \-            If percentage type

  formula               TEXT            YES        \-            Custom formula

  slab_config           JSONB           YES        \-            Slab-based calculation

  taxable               BOOLEAN         NO         TRUE          Taxable component

  tax_exemption_limit   NUMERIC(12,2)   YES        \-            Annual exemption limit

  tax_section           VARCHAR(20)     YES        \-            80C, 80D, 10, etc.

  pf_applicable         BOOLEAN         NO         FALSE         Include in PF calculation

  esi_applicable        BOOLEAN         NO         FALSE         Include in ESI calculation

  gratuity_applicable   BOOLEAN         NO         FALSE         Include in gratuity

  lwf_applicable        BOOLEAN         NO         FALSE         Include in LWF

  show_in_payslip       BOOLEAN         NO         TRUE          Display in payslip

  payslip_order         INTEGER         NO         \-            Display sequence

  prorate_on_lop        BOOLEAN         NO         TRUE          Reduce for LOP days

  arrears_applicable    BOOLEAN         NO         TRUE          Calculate arrears

  effective_from        DATE            NO         \-            Component effective from

  effective_to          DATE            YES        \-            Component effective to

  status                VARCHAR(20)     NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                               Standard audit columns
  --------------------- --------------- ---------- ------------- -------------------------------------------

**6.2 Standard Salary Components**

  ----------- ------------------------ ----------- --------------------- ----------------
  **Code**    **Component**            **Type**    **Calculation**       **PF/ESI**

  BASIC       Basic Salary             EARNING     FIXED                 Yes

  HRA         House Rent Allowance     EARNING     40-50% of Basic       No

  DA          Dearness Allowance       EARNING     \% of Basic           Yes

  CONV        Conveyance Allowance     EARNING     FIXED (₹1,600)        No

  SPECIAL     Special Allowance        EARNING     Balancing figure      No

  LTA         Leave Travel Allowance   EARNING     FIXED                 No

  MEDICAL     Medical Allowance        EARNING     FIXED                 No

  PF_EE       PF Employee              DEDUCTION   12% of (Basic+DA)     \-

  PF_ER       PF Employer              EMPLOYER    12% of (Basic+DA)     \-

  ESI_EE      ESI Employee             DEDUCTION   0.75% of Gross        \-

  ESI_ER      ESI Employer             EMPLOYER    3.25% of Gross        \-

  PT          Professional Tax         DEDUCTION   SLAB                  \-

  TDS         TDS                      DEDUCTION   Income Tax slab       \-

  BONUS       Bonus                    EARNING     \% or Fixed           Yes

  INCENTIVE   Performance Incentive    EARNING     Variable              No

  OT          Overtime                 EARNING     Hourly rate × hours   Yes
  ----------- ------------------------ ----------- --------------------- ----------------

**6.3 Employee Salary Structure (TXN_EMPLOYEE_SALARY)**

  -------------------- --------------- ---------- ------------- -----------------------------------------
  **Column**           **Type**        **Null**   **Default**   **Description**

  salary_id            BIGSERIAL       NO         Auto          Primary Key

  employee_id          BIGINT          NO         \-            FK to MST_EMPLOYEE

  effective_from       DATE            NO         \-            Structure effective from

  effective_to         DATE            YES        \-            Structure effective to

  ctc_annual           NUMERIC(14,2)   NO         \-            Annual CTC

  ctc_monthly          NUMERIC(12,2)   NO         \-            Monthly CTC

  gross_monthly        NUMERIC(12,2)   NO         \-            Monthly gross salary

  net_monthly          NUMERIC(12,2)   NO         \-            Approx net salary

  components           JSONB           NO         \-            Component-wise breakup

  revision_type        VARCHAR(30)     YES        \-            JOINING, INCREMENT, PROMOTION, REVISION

  revision_pct         NUMERIC(5,2)    YES        \-            \% increment

  previous_salary_id   BIGINT          YES        \-            Previous structure ref

  approved_by          BIGINT          YES        \-            Approver

  remarks              VARCHAR(500)    YES        \-            Revision remarks

  status               VARCHAR(20)     NO         ACTIVE        ACTIVE, INACTIVE, SUPERSEDED

  \+ Audit Columns                                              Standard audit columns
  -------------------- --------------- ---------- ------------- -----------------------------------------

**7. Salary Processing**

Monthly payroll processing, arrears, and full & final settlement.

**7.1 Payroll Run (TXN_PAYROLL_RUN)**

  --------------------- --------------- ---------- ------------- -------------------------------------------------------
  **Column**            **Type**        **Null**   **Default**   **Description**

  run_id                BIGSERIAL       NO         Auto          Primary Key

  org_id                BIGINT          NO         \-            FK to MST_ORGANIZATION

  payroll_month         VARCHAR(10)     NO         \-            YYYY-MM format

  run_date              DATE            NO         \-            Processing date

  run_type              VARCHAR(20)     NO         \-            REGULAR, SUPPLEMENTARY, ARREARS, FNF

  from_date             DATE            NO         \-            Period start

  to_date               DATE            NO         \-            Period end

  total_employees       INTEGER         NO         \-            Employees processed

  total_gross           NUMERIC(16,2)   NO         \-            Total gross

  total_deductions      NUMERIC(16,2)   NO         \-            Total deductions

  total_net             NUMERIC(16,2)   NO         \-            Total net payable

  total_employer_cost   NUMERIC(16,2)   NO         \-            Total employer cost

  status                VARCHAR(20)     NO         DRAFT         DRAFT, PROCESSED, REVIEWED, APPROVED, PAID, CANCELLED

  processed_by          BIGINT          NO         \-            Processed by user

  reviewed_by           BIGINT          YES        \-            Reviewed by user

  approved_by           BIGINT          YES        \-            Approved by user

  approved_date         DATE            YES        \-            Approval date

  bank_file_generated   BOOLEAN         NO         FALSE         Bank file created

  bank_file_path        VARCHAR(500)    YES        \-            Bank file location

  payment_date          DATE            YES        \-            Salary credit date

  \+ Audit Columns                                               Standard audit columns
  --------------------- --------------- ---------- ------------- -------------------------------------------------------

**7.2 Employee Payroll (TXN_PAYROLL)**

  ------------------------ --------------- ---------- ------------- --------------------------------
  **Column**               **Type**        **Null**   **Default**   **Description**

  payroll_id               BIGSERIAL       NO         Auto          Primary Key

  run_id                   BIGINT          NO         \-            FK to TXN_PAYROLL_RUN

  employee_id              BIGINT          NO         \-            FK to MST_EMPLOYEE

  salary_id                BIGINT          NO         \-            FK to TXN_EMPLOYEE_SALARY

  payroll_month            VARCHAR(10)     NO         \-            YYYY-MM

  working_days             INTEGER         NO         \-            Working days in month

  days_worked              NUMERIC(5,2)    NO         \-            Days worked

  lop_days                 NUMERIC(5,2)    NO         0             LOP days

  leave_days               NUMERIC(5,2)    NO         0             Paid leave days

  overtime_hours           NUMERIC(6,2)    NO         0             OT hours

  gross_salary             NUMERIC(12,2)   NO         \-            Gross earnings

  total_earnings           NUMERIC(12,2)   NO         \-            All earnings

  total_deductions         NUMERIC(12,2)   NO         \-            All deductions

  net_salary               NUMERIC(12,2)   NO         \-            Net payable

  employer_contributions   NUMERIC(12,2)   NO         \-            Employer costs

  total_ctc                NUMERIC(12,2)   NO         \-            Total cost to company

  earnings_breakup         JSONB           NO         \-            Component-wise earnings

  deductions_breakup       JSONB           NO         \-            Component-wise deductions

  employer_breakup         JSONB           NO         \-            Employer contributions

  arrears_amount           NUMERIC(12,2)   NO         0             Arrears if any

  arrears_details          JSONB           YES        \-            Arrears breakup

  bank_account_id          BIGINT          YES        \-            FK to MST_EMPLOYEE_BANK

  payment_mode             VARCHAR(20)     NO         BANK          BANK, CHEQUE, CASH

  payment_status           VARCHAR(20)     NO         PENDING       PENDING, PAID, HOLD, FAILED

  payment_reference        VARCHAR(50)     YES        \-            UTR/Ref number

  payslip_generated        BOOLEAN         NO         FALSE         Payslip created

  payslip_path             VARCHAR(500)    YES        \-            Payslip PDF path

  voucher_id               BIGINT          YES        \-            FK to TXN_VOUCHER

  status                   VARCHAR(20)     NO         PROCESSED     PROCESSED, APPROVED, CANCELLED

  \+ Audit Columns                                                  Standard audit columns
  ------------------------ --------------- ---------- ------------- --------------------------------

**7.3 Payroll Calculation Flow**

**Step 1: Initialize Payroll Run** - Create payroll run record

INSERT INTO txn_payroll_run (payroll_month, run_type=\'REGULAR\', status=\'DRAFT\')

**Step 2: Get Active Employees** - Fetch employees to process

SELECT \* FROM mst_employee WHERE status=\'ACTIVE\' AND date_of_joining \<= :period_end

**Step 3: Get Attendance Summary** - Calculate working days

FOR each employee:

present_days = COUNT(attendance_status IN (\'PRESENT\', \'LEAVE\'))

lop_days = COUNT(attendance_status = \'ABSENT\') - available_leave

overtime_hours = SUM(overtime_hours)

**Step 4: Calculate Earnings** - Process each earning component

FOR each earning_component:

IF type = \'FIXED\':

amount = component.value × (days_worked / working_days)

ELSE IF type = \'PERCENTAGE\':

amount = base_amount × percentage / 100

ELSE IF type = \'FORMULA\':

amount = evaluate_formula(component.formula, context)

**Step 5: Calculate Deductions** - Process statutory and other deductions

\-- PF Calculation

pf_base = basic + da (capped at ₹15,000)

pf_employee = pf_base × 0.12

pf_employer = pf_base × 0.12

\-- ESI Calculation (if gross \<= ₹21,000)

esi_employee = gross × 0.0075

esi_employer = gross × 0.0325

\-- PT (state-specific slabs)

\-- TDS (based on tax computation)

**Step 6: Calculate Net Salary** - Finalize amounts

gross_salary = SUM(all_earnings)

total_deductions = pf + esi + pt + tds + other_deductions

net_salary = gross_salary - total_deductions

**Step 7: Generate Payslips** - Create PDF payslips

- Generate individual payslip PDFs

- Email payslips to employees

**8. Statutory Compliance**

PF, ESI, PT, TDS compliance and return filing.

**8.1 PF Challan (TXN_PF_CHALLAN)**

  ------------------------- --------------- ---------- ------------- ------------------------------
  **Column**                **Type**        **Null**   **Default**   **Description**

  challan_id                BIGSERIAL       NO         Auto          Primary Key

  org_id                    BIGINT          NO         \-            FK to MST_ORGANIZATION

  pf_establishment_id       VARCHAR(30)     NO         \-            PF establishment code

  month                     VARCHAR(10)     NO         \-            YYYY-MM

  due_date                  DATE            NO         \-            Payment due date

  total_employees           INTEGER         NO         \-            Covered employees

  total_wages               NUMERIC(14,2)   NO         \-            Total PF wages

  ee_contribution           NUMERIC(12,2)   NO         \-            Employee share

  er_pf_contribution        NUMERIC(12,2)   NO         \-            Employer PF share

  er_pension_contribution   NUMERIC(12,2)   NO         \-            EPS contribution

  admin_charges             NUMERIC(10,2)   NO         \-            Admin charges (0.5%)

  edli_charges              NUMERIC(10,2)   NO         \-            EDLI charges

  total_amount              NUMERIC(14,2)   NO         \-            Total payable

  payment_date              DATE            YES        \-            Actual payment date

  trrn                      VARCHAR(30)     YES        \-            TRRN number

  challan_number            VARCHAR(30)     YES        \-            Challan reference

  ecr_file_path             VARCHAR(500)    YES        \-            ECR file path

  status                    VARCHAR(20)     NO         PENDING       PENDING, PAID, VERIFIED

  voucher_id                BIGINT          YES        \-            FK to TXN_VOUCHER

  \+ Audit Columns                                                   Standard audit columns
  ------------------------- --------------- ---------- ------------- ------------------------------

**8.2 ESI Challan (TXN_ESI_CHALLAN)**

  ------------------ --------------- ---------- ------------- -------------------------------
  **Column**         **Type**        **Null**   **Default**   **Description**

  challan_id         BIGSERIAL       NO         Auto          Primary Key

  org_id             BIGINT          NO         \-            FK to MST_ORGANIZATION

  esi_code           VARCHAR(20)     NO         \-            ESI employer code

  month              VARCHAR(10)     NO         \-            YYYY-MM

  total_employees    INTEGER         NO         \-            Covered employees

  total_wages        NUMERIC(14,2)   NO         \-            Total ESI wages

  ee_contribution    NUMERIC(12,2)   NO         \-            Employee share (0.75%)

  er_contribution    NUMERIC(12,2)   NO         \-            Employer share (3.25%)

  total_amount       NUMERIC(12,2)   NO         \-            Total payable

  payment_date       DATE            YES        \-            Payment date

  challan_number     VARCHAR(30)     YES        \-            Challan reference

  status             VARCHAR(20)     NO         PENDING       PENDING, PAID

  voucher_id         BIGINT          YES        \-            FK to TXN_VOUCHER

  \+ Audit Columns                                            Standard audit columns
  ------------------ --------------- ---------- ------------- -------------------------------

**8.3 Professional Tax Slabs (Maharashtra Example)**

  ------------------------- --------------------- --------------------
  **Monthly Salary**        **PT Amount**         **Frequency**

  Up to ₹7,500              Nil                   Monthly

  ₹7,501 - ₹10,000          ₹175                  Monthly

  Above ₹10,000             ₹200 (₹300 in Feb)    Monthly
  ------------------------- --------------------- --------------------

**8.4 TDS Computation (TXN_TDS_COMPUTATION)**

  --------------------- --------------- ---------- ------------- ------------------------------
  **Column**            **Type**        **Null**   **Default**   **Description**

  tds_id                BIGSERIAL       NO         Auto          Primary Key

  employee_id           BIGINT          NO         \-            FK to MST_EMPLOYEE

  financial_year        VARCHAR(10)     NO         \-            FY (2025-26)

  computation_month     VARCHAR(10)     NO         \-            As of month

  gross_salary_ytd      NUMERIC(14,2)   NO         \-            YTD gross salary

  projected_salary      NUMERIC(14,2)   NO         \-            Projected annual

  standard_deduction    NUMERIC(10,2)   NO         75000         Std deduction

  sec_80c_declared      NUMERIC(10,2)   NO         0             80C investments

  sec_80d_declared      NUMERIC(10,2)   NO         0             80D (medical)

  hra_exemption         NUMERIC(10,2)   NO         0             HRA exemption

  lta_exemption         NUMERIC(10,2)   NO         0             LTA exemption

  other_exemptions      NUMERIC(10,2)   NO         0             Other exemptions

  taxable_income        NUMERIC(14,2)   NO         \-            Taxable income

  tax_old_regime        NUMERIC(12,2)   YES        \-            Tax under old regime

  tax_new_regime        NUMERIC(12,2)   YES        \-            Tax under new regime

  regime_opted          VARCHAR(10)     NO         NEW           OLD, NEW

  annual_tax            NUMERIC(12,2)   NO         \-            Annual tax liability

  cess                  NUMERIC(10,2)   NO         \-            Health & education cess

  total_tax             NUMERIC(12,2)   NO         \-            Total tax payable

  tax_deducted_ytd      NUMERIC(12,2)   NO         \-            TDS deducted YTD

  monthly_tds           NUMERIC(10,2)   NO         \-            Monthly TDS to deduct

  computation_details   JSONB           YES        \-            Detailed calculation

  \+ Audit Columns                                               Standard audit columns
  --------------------- --------------- ---------- ------------- ------------------------------

**9. Business Flows**

**9.1 Employee Onboarding Flow**

**Step 1: Create Employee** - HR creates employee record

- Enter basic details, department, designation

- Generate employee code

- Set up reporting hierarchy

**Step 2: Capture Details** - Complete employee profile

- Personal information

- Family details & nominees

- Bank account (verify via penny drop)

- Upload documents (photo, education, experience)

**Step 3: Assign Salary Structure** - Configure compensation

INSERT INTO txn_employee_salary (employee_id, ctc, components)

- Define component-wise breakup

**Step 4: Initialize Leave Balance** - Credit leave entitlements

FOR each leave_type:

prorated_quota = annual_quota × remaining_months / 12

INSERT INTO txn_leave_balance (\...)

**Step 5: Create User Account** - Setup ERP login

- Create MST_USER record

- Assign Employee role

- Enable self-service portal

**9.2 Monthly Payroll Flow**

**Step 1: Freeze Attendance** - Lock attendance for the month

**Step 2: Process Leave** - Update leave balances

**Step 3: Generate Payroll** - Run salary calculations

**Step 4: Review & Approve** - HR/Finance review

**Step 5: Generate Bank File** - Create payment file

**Step 6: Process Payment** - Credit salaries

**Step 7: Generate Payslips** - Create and email payslips

**Step 8: Post to GL** - Create accounting entries

**10. Business Rules**

**10.1 Leave Rules**

  ------------- ----------------------- ---------------------------------------------- ---------------------------------
  **Rule ID**   **Rule**                **Condition**                                  **Action**

  LV-001        Balance check           Applied days \> available balance              Block (unless negative allowed)

  LV-002        Advance notice          Application date \< from_date - advance_days   Warn/Block

  LV-003        Max per application     Total days \> max_days_per_application         Block

  LV-004        Document required       Leave days \> document_for_days                Require attachment

  LV-005        Holiday between         Holidays fall between leave dates              Include/Exclude per config

  LV-006        Clubbing restriction    Leave clubbed with restricted type             Block if not allowed

  LV-007        Probation restriction   Employee on probation                          Limit leave types
  ------------- ----------------------- ---------------------------------------------- ---------------------------------

**10.2 Payroll Rules**

  ------------- ------------------------- ---------------------------- ---------------------------------
  **Rule ID**   **Rule**                  **Condition**                **Action**

  PAY-001       Active salary structure   No active salary structure   Exclude from payroll

  PAY-002       Bank account required     No verified bank account     Hold payment

  PAY-003       Attendance freeze         Attendance not frozen        Block payroll processing

  PAY-004       PF wage ceiling           PF wages \> ₹15,000          Cap at ₹15,000

  PAY-005       ESI eligibility           Gross \> ₹21,000             ESI not applicable

  PAY-006       Minimum net               Net salary \< 0              Show error, review deductions

  PAY-007       TDS minimum               Monthly TDS \< 0             Set to 0 (no refund in monthly)
  ------------- ------------------------- ---------------------------- ---------------------------------

**10.3 Attendance Rules**

  ------------- ------------------ -------------------------------- -----------------------------
  **Rule ID**   **Rule**           **Condition**                    **Action**

  ATT-001       Minimum hours      Hours \< half_day_hours          Mark ABSENT

  ATT-002       Late coming        In time \> shift start + grace   Record late minutes

  ATT-003       Early leaving      Out time \< shift end - grace    Record early minutes

  ATT-004       Multiple punches   Multiple in/out                  Consider first in, last out

  ATT-005       Missing punch      Only in or only out              Flag for regularization

  ATT-006       OD/WFH approval    OD/WFH without approval          Mark pending regularization
  ------------- ------------------ -------------------------------- -----------------------------

*\-\-- End of Phase 5 \-\--*

Phase 6 covers: Fixed Assets, TDS, GST, BRS, FD Tracker
