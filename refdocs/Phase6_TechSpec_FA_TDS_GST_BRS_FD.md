**SMFC Ltd**

Integrated ERP Solution

**TECHNICAL SPECIFICATION**

Phase 6: Ancillary Finance Modules

Fixed Assets, TDS, GST, Bank Reconciliation, FD Tracker

**Table of Contents**

1\. Fixed Asset Management

2\. TDS Management

3\. GST Management

4\. Bank Reconciliation Statement (BRS)

5\. Fixed Deposit Tracker

6\. Business Flows

7\. Business Rules

**1. Fixed Asset Management**

Complete lifecycle management of fixed assets including acquisition, depreciation, transfer, and disposal.

**1.1 Asset Category Master (MST_ASSET_CATEGORY)**

  -------------------------- --------------- ---------- ------------- ---------------------------------
  **Column**                 **Type**        **Null**   **Default**   **Description**

  category_id                BIGSERIAL       NO         Auto          Primary Key

  org_id                     BIGINT          NO         \-            FK to MST_ORGANIZATION

  category_code              VARCHAR(20)     NO         \-            Unique category code

  category_name              VARCHAR(100)    NO         \-            Category name

  parent_category_id         BIGINT          YES        \-            Parent category (hierarchy)

  asset_type                 VARCHAR(30)     NO         \-            TANGIBLE, INTANGIBLE, ROU

  depreciation_method        VARCHAR(20)     NO         \-            SLM, WDV

  useful_life_years          INTEGER         NO         \-            Useful life in years

  residual_value_pct         NUMERIC(5,2)    NO         5             Residual value %

  depreciation_rate_slm      NUMERIC(5,2)    YES        \-            SLM rate %

  depreciation_rate_wdv      NUMERIC(5,2)    YES        \-            WDV rate %

  it_act_rate                NUMERIC(5,2)    YES        \-            IT Act depreciation rate

  it_act_block               VARCHAR(20)     YES        \-            IT Act block

  capitalization_threshold   NUMERIC(12,2)   NO         5000          Min value for capitalization

  gl_asset_account           BIGINT          NO         \-            FK to MST_COA (Asset)

  gl_accum_dep_account       BIGINT          NO         \-            FK to MST_COA (Accum Dep)

  gl_dep_expense_account     BIGINT          NO         \-            FK to MST_COA (Dep Expense)

  gl_disposal_account        BIGINT          YES        \-            FK to MST_COA (P&L on disposal)

  requires_insurance         BOOLEAN         NO         FALSE         Insurance tracking

  requires_amc               BOOLEAN         NO         FALSE         AMC tracking

  status                     VARCHAR(20)     NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                                    Standard audit columns
  -------------------------- --------------- ---------- ------------- ---------------------------------

**1.2 Standard Asset Categories**

  ------------------------ ------------ ------------ ----------------- -------------- ---------------
  **Category**             **Type**     **Method**   **Useful Life**   **SLM Rate**   **WDV Rate**

  Land                     TANGIBLE     N/A          Unlimited         0%             0%

  Building                 TANGIBLE     SLM          60 years          1.67%          5%

  Plant & Machinery        TANGIBLE     WDV          15 years          6.67%          15%

  Furniture & Fixtures     TANGIBLE     SLM          10 years          10%            10%

  Office Equipment         TANGIBLE     SLM          5 years           20%            15%

  Computers & IT           TANGIBLE     SLM          3 years           33.33%         40%

  Vehicles                 TANGIBLE     WDV          8 years           12.5%          15%

  Software                 INTANGIBLE   SLM          5 years           20%            \-

  Leasehold Improvements   TANGIBLE     SLM          Lease term        Lease based    \-

  Right of Use Assets      ROU          SLM          Lease term        Lease based    \-
  ------------------------ ------------ ------------ ----------------- -------------- ---------------

**1.3 Fixed Asset Register (MST_FIXED_ASSET)**

  -------------------------- --------------- ---------- ------------- --------------------------------------------------
  **Column**                 **Type**        **Null**   **Default**   **Description**

  asset_id                   BIGSERIAL       NO         Auto          Primary Key

  org_id                     BIGINT          NO         \-            FK to MST_ORGANIZATION

  asset_code                 VARCHAR(30)     NO         \-            Unique asset code

  asset_name                 VARCHAR(200)    NO         \-            Asset description

  category_id                BIGINT          NO         \-            FK to MST_ASSET_CATEGORY

  sub_category               VARCHAR(100)    YES        \-            Sub-category

  location_id                BIGINT          NO         \-            FK to MST_UNIT

  department_id              BIGINT          YES        \-            FK to MST_DEPARTMENT

  custodian_id               BIGINT          YES        \-            FK to MST_EMPLOYEE

  acquisition_date           DATE            NO         \-            Purchase/Acquisition date

  put_to_use_date            DATE            NO         \-            Date put to use

  acquisition_type           VARCHAR(20)     NO         \-            PURCHASE, TRANSFER, DONATION, LEASE

  vendor_id                  BIGINT          YES        \-            FK to MST_VENDOR

  invoice_number             VARCHAR(50)     YES        \-            Purchase invoice

  invoice_date               DATE            YES        \-            Invoice date

  po_number                  VARCHAR(50)     YES        \-            Purchase order

  acquisition_cost           NUMERIC(14,2)   NO         \-            Original cost

  installation_cost          NUMERIC(14,2)   NO         0             Installation charges

  other_costs                NUMERIC(14,2)   NO         0             Other capitalizable costs

  total_cost                 NUMERIC(14,2)   NO         \-            Total capitalized value

  residual_value             NUMERIC(14,2)   NO         \-            Estimated residual

  depreciable_value          NUMERIC(14,2)   NO         \-            Total - Residual

  useful_life_months         INTEGER         NO         \-            Useful life in months

  depreciation_method        VARCHAR(20)     NO         \-            SLM, WDV

  depreciation_rate          NUMERIC(5,2)    NO         \-            Annual rate

  accumulated_depreciation   NUMERIC(14,2)   NO         0             Depreciation till date

  wdv_value                  NUMERIC(14,2)   NO         \-            Written Down Value

  last_depreciation_date     DATE            YES        \-            Last dep run date

  revaluation_amount         NUMERIC(14,2)   NO         0             Revaluation adjustments

  impairment_amount          NUMERIC(14,2)   NO         0             Impairment loss

  make                       VARCHAR(100)    YES        \-            Manufacturer/Brand

  model                      VARCHAR(100)    YES        \-            Model number

  serial_number              VARCHAR(100)    YES        \-            Serial/Asset tag

  warranty_expiry            DATE            YES        \-            Warranty end date

  insurance_policy           VARCHAR(50)     YES        \-            Insurance policy no

  insurance_expiry           DATE            YES        \-            Insurance expiry

  amc_vendor_id              BIGINT          YES        \-            AMC vendor

  amc_expiry                 DATE            YES        \-            AMC expiry date

  disposal_date              DATE            YES        \-            Disposal date

  disposal_type              VARCHAR(20)     YES        \-            SALE, SCRAP, WRITE_OFF, TRANSFER

  disposal_value             NUMERIC(14,2)   YES        \-            Sale/Scrap value

  disposal_gain_loss         NUMERIC(14,2)   YES        \-            Gain/Loss on disposal

  parent_asset_id            BIGINT          YES        \-            Parent asset (for components)

  is_component               BOOLEAN         NO         FALSE         Is sub-component

  status                     VARCHAR(20)     NO         ACTIVE        ACTIVE, DISPOSED, TRANSFERRED, UNDER_MAINTENANCE

  \+ Audit Columns                                                    Standard audit columns
  -------------------------- --------------- ---------- ------------- --------------------------------------------------

**1.4 Asset Code Format**

Format: {CATEGORY}/{LOCATION}/{YEAR}/{SEQUENCE}

Example: FA-COM/DEL/2025/0001 (Computer at Delhi)

FA-VEH/MUM/2025/0005 (Vehicle at Mumbai)

Category Codes:

FA-LND: Land

FA-BLD: Building

FA-P&M: Plant & Machinery

FA-FUR: Furniture

FA-OFF: Office Equipment

FA-COM: Computers

FA-VEH: Vehicles

FA-SFT: Software

**1.5 Depreciation Transaction (TXN_DEPRECIATION)**

  -------------------------- --------------- ---------- ------------- -------------------------------
  **Column**                 **Type**        **Null**   **Default**   **Description**

  depreciation_id            BIGSERIAL       NO         Auto          Primary Key

  asset_id                   BIGINT          NO         \-            FK to MST_FIXED_ASSET

  depreciation_period        VARCHAR(10)     NO         \-            YYYY-MM

  period_from                DATE            NO         \-            Period start

  period_to                  DATE            NO         \-            Period end

  days_in_period             INTEGER         NO         \-            Days for calculation

  opening_wdv                NUMERIC(14,2)   NO         \-            WDV at period start

  depreciation_rate          NUMERIC(5,2)    NO         \-            Rate applied

  depreciation_amount        NUMERIC(14,2)   NO         \-            Depreciation charged

  accumulated_depreciation   NUMERIC(14,2)   NO         \-            Total accumulated

  closing_wdv                NUMERIC(14,2)   NO         \-            WDV at period end

  depreciation_type          VARCHAR(20)     NO         REGULAR       REGULAR, ADDITIONAL, REVERSAL

  voucher_id                 BIGINT          YES        \-            FK to TXN_VOUCHER

  run_id                     BIGINT          YES        \-            Depreciation run reference

  \+ Audit Columns                                                    Standard audit columns
  -------------------------- --------------- ---------- ------------- -------------------------------

**1.6 Asset Transfer (TXN_ASSET_TRANSFER)**

  -------------------- -------------- ---------- ------------- ----------------------------------------
  **Column**           **Type**       **Null**   **Default**   **Description**

  transfer_id          BIGSERIAL      NO         Auto          Primary Key

  asset_id             BIGINT         NO         \-            FK to MST_FIXED_ASSET

  transfer_date        DATE           NO         \-            Transfer date

  from_location_id     BIGINT         NO         \-            From location

  to_location_id       BIGINT         NO         \-            To location

  from_department_id   BIGINT         YES        \-            From department

  to_department_id     BIGINT         YES        \-            To department

  from_custodian_id    BIGINT         YES        \-            From custodian

  to_custodian_id      BIGINT         YES        \-            To custodian

  reason               VARCHAR(500)   YES        \-            Transfer reason

  approved_by          BIGINT         YES        \-            Approver

  status               VARCHAR(20)    NO         COMPLETED     PENDING, APPROVED, COMPLETED, REJECTED

  \+ Audit Columns                                             Standard audit columns
  -------------------- -------------- ---------- ------------- ----------------------------------------

**1.7 Depreciation Calculation**

**1.7.1 Straight Line Method (SLM)**

Annual Depreciation = (Cost - Residual Value) / Useful Life

Monthly Depreciation = Annual Depreciation / 12

Example:

Cost: ₹10,00,000

Residual: ₹50,000 (5%)

Useful Life: 5 years

Annual Dep = (10,00,000 - 50,000) / 5 = ₹1,90,000

Monthly Dep = ₹15,833

**1.7.2 Written Down Value (WDV)**

Annual Depreciation = Opening WDV × Rate

Example:

Cost: ₹10,00,000

Rate: 15%

Year 1: 10,00,000 × 15% = ₹1,50,000 → WDV: ₹8,50,000

Year 2: 8,50,000 × 15% = ₹1,27,500 → WDV: ₹7,22,500

Year 3: 7,22,500 × 15% = ₹1,08,375 → WDV: ₹6,14,125

**2. TDS Management**

Tax Deducted at Source - tracking, deduction, and return filing.

**2.1 TDS Section Master (MST_TDS_SECTION)**

  ---------------------- --------------- ---------- ------------- ---------------------------------
  **Column**             **Type**        **Null**   **Default**   **Description**

  section_id             BIGSERIAL       NO         Auto          Primary Key

  section_code           VARCHAR(10)     NO         \-            Section code (194A, 194C, etc.)

  section_name           VARCHAR(200)    NO         \-            Section description

  payment_nature         VARCHAR(100)    NO         \-            Nature of payment

  threshold_limit        NUMERIC(12,2)   NO         0             Threshold for deduction

  rate_individual        NUMERIC(5,2)    NO         \-            Rate for individuals

  rate_company           NUMERIC(5,2)    NO         \-            Rate for companies

  rate_no_pan            NUMERIC(5,2)    NO         20            Rate if no PAN

  surcharge_applicable   BOOLEAN         NO         FALSE         Surcharge applies

  cess_rate              NUMERIC(5,2)    NO         4             H&E cess rate

  tds_payable_by         INTEGER         NO         7             Due date (day of month)

  return_form            VARCHAR(10)     NO         \-            24Q, 26Q, 27Q, 27EQ

  effective_from         DATE            NO         \-            Effective from date

  effective_to           DATE            YES        \-            Effective to date

  status                 VARCHAR(20)     NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                                Standard audit columns
  ---------------------- --------------- ---------- ------------- ---------------------------------

**2.2 Common TDS Sections**

  ------------- ---------------------------------- ----------------- ---------------- ------------- -----------
  **Section**   **Nature of Payment**              **Threshold**     **Individual**   **Company**   **Form**

  192           Salary                             Basic exemption   Slab rates       \-            24Q

  194A          Interest (other than securities)   ₹40,000           10%              10%           26Q

  194C          Contractor payments                ₹30,000/₹1L       1%               2%            26Q

  194H          Commission/Brokerage               ₹15,000           5%               5%            26Q

  194I(a)       Rent - Plant/Machinery             ₹2,40,000         2%               2%            26Q

  194I(b)       Rent - Land/Building               ₹2,40,000         10%              10%           26Q

  194J          Professional/Technical fees        ₹30,000           10%              10%           26Q

  194Q          Purchase of goods                  ₹50L              0.1%             0.1%          26Q

  195           Payment to NR                      Any               Varies           Varies        27Q

  194N          Cash withdrawal                    ₹1 Cr             2%               2%            26Q
  ------------- ---------------------------------- ----------------- ---------------- ------------- -----------

**2.3 TDS Transaction (TXN_TDS)**

  ---------------------- --------------- ---------- ------------- -----------------------------------
  **Column**             **Type**        **Null**   **Default**   **Description**

  tds_id                 BIGSERIAL       NO         Auto          Primary Key

  org_id                 BIGINT          NO         \-            FK to MST_ORGANIZATION

  tan                    VARCHAR(10)     NO         \-            Deductor TAN

  section_id             BIGINT          NO         \-            FK to MST_TDS_SECTION

  deductee_type          VARCHAR(20)     NO         \-            VENDOR, EMPLOYEE, BORROWER, OTHER

  deductee_id            BIGINT          YES        \-            FK to relevant master

  deductee_name          VARCHAR(200)    NO         \-            Deductee name

  deductee_pan           VARCHAR(10)     YES        \-            Deductee PAN

  transaction_date       DATE            NO         \-            Transaction date

  payment_date           DATE            YES        \-            Actual payment date

  gross_amount           NUMERIC(14,2)   NO         \-            Gross payment

  tds_rate               NUMERIC(5,2)    NO         \-            TDS rate applied

  tds_amount             NUMERIC(12,2)   NO         \-            TDS deducted

  surcharge              NUMERIC(12,2)   NO         0             Surcharge amount

  cess                   NUMERIC(12,2)   NO         \-            H&E cess

  total_tds              NUMERIC(12,2)   NO         \-            Total TDS

  net_amount             NUMERIC(14,2)   NO         \-            Net paid to deductee

  lower_deduction_cert   VARCHAR(50)     YES        \-            Lower TDS certificate no

  lower_rate             NUMERIC(5,2)    YES        \-            Rate as per certificate

  reference_voucher_id   BIGINT          YES        \-            Source voucher

  reference_type         VARCHAR(50)     YES        \-            VENDOR_PAYMENT, INTEREST, SALARY

  challan_id             BIGINT          YES        \-            FK to TXN_TDS_CHALLAN

  quarter                VARCHAR(10)     NO         \-            Q1, Q2, Q3, Q4

  financial_year         VARCHAR(10)     NO         \-            2025-26

  return_filed           BOOLEAN         NO         FALSE         Included in return

  return_id              BIGINT          YES        \-            FK to TXN_TDS_RETURN

  status                 VARCHAR(20)     NO         DEDUCTED      DEDUCTED, DEPOSITED, RETURNED

  \+ Audit Columns                                                Standard audit columns
  ---------------------- --------------- ---------- ------------- -----------------------------------

**2.4 TDS Challan (TXN_TDS_CHALLAN)**

  ------------------ --------------- ---------- ------------- -------------------------------
  **Column**         **Type**        **Null**   **Default**   **Description**

  challan_id         BIGSERIAL       NO         Auto          Primary Key

  org_id             BIGINT          NO         \-            FK to MST_ORGANIZATION

  tan                VARCHAR(10)     NO         \-            TAN

  challan_type       VARCHAR(10)     NO         \-            281 (TDS), 280 (IT)

  assessment_year    VARCHAR(10)     NO         \-            AY (2026-27)

  period_from        DATE            NO         \-            Period start

  period_to          DATE            NO         \-            Period end

  section_code       VARCHAR(10)     YES        \-            If single section

  tds_amount         NUMERIC(14,2)   NO         \-            Total TDS

  surcharge          NUMERIC(12,2)   NO         0             Surcharge

  cess               NUMERIC(12,2)   NO         \-            Cess

  interest           NUMERIC(12,2)   NO         0             Interest if late

  penalty            NUMERIC(12,2)   NO         0             Penalty if any

  total_amount       NUMERIC(14,2)   NO         \-            Total deposited

  payment_date       DATE            NO         \-            Payment date

  payment_mode       VARCHAR(20)     NO         \-            ONLINE, BANK

  bsr_code           VARCHAR(10)     YES        \-            Bank BSR code

  challan_serial     VARCHAR(10)     YES        \-            Challan serial no

  cin                VARCHAR(30)     YES        \-            Challan Identification No

  bank_name          VARCHAR(100)    YES        \-            Depositing bank

  voucher_id         BIGINT          YES        \-            FK to TXN_VOUCHER

  status             VARCHAR(20)     NO         PAID          DRAFT, PAID, VERIFIED

  \+ Audit Columns                                            Standard audit columns
  ------------------ --------------- ---------- ------------- -------------------------------

**3. GST Management**

Goods and Services Tax - input credit, output liability, and return filing.

**3.1 GST Registration (MST_GST_REGISTRATION)**

  ---------------------- -------------- ---------- ------------- --------------------------------
  **Column**             **Type**       **Null**   **Default**   **Description**

  registration_id        BIGSERIAL      NO         Auto          Primary Key

  org_id                 BIGINT         NO         \-            FK to MST_ORGANIZATION

  gstin                  VARCHAR(15)    NO         \-            GSTIN

  legal_name             VARCHAR(200)   NO         \-            Legal name

  trade_name             VARCHAR(200)   YES        \-            Trade name

  state_code             VARCHAR(2)     NO         \-            State code

  state_name             VARCHAR(100)   NO         \-            State name

  registration_type      VARCHAR(30)    NO         \-            REGULAR, COMPOSITION, SEZ, ISD

  registration_date      DATE           NO         \-            GST registration date

  principal_place        TEXT           NO         \-            Principal place of business

  additional_places      JSONB          YES        \-            Additional places

  authorized_signatory   VARCHAR(200)   YES        \-            Authorized signatory

  filing_frequency       VARCHAR(20)    NO         MONTHLY       MONTHLY, QUARTERLY

  status                 VARCHAR(20)    NO         ACTIVE        ACTIVE, SUSPENDED, CANCELLED

  \+ Audit Columns                                               Standard audit columns
  ---------------------- -------------- ---------- ------------- --------------------------------

**3.2 GST Transaction (TXN_GST)**

  ----------------------- --------------- ---------- ------------- ----------------------------------
  **Column**              **Type**        **Null**   **Default**   **Description**

  gst_id                  BIGSERIAL       NO         Auto          Primary Key

  org_id                  BIGINT          NO         \-            FK to MST_ORGANIZATION

  gstin                   VARCHAR(15)     NO         \-            Own GSTIN

  transaction_type        VARCHAR(20)     NO         \-            INPUT, OUTPUT, RCM

  supply_type             VARCHAR(20)     NO         \-            B2B, B2C, EXPORT, IMPORT, SEZ

  document_type           VARCHAR(20)     NO         \-            INVOICE, CREDIT_NOTE, DEBIT_NOTE

  document_number         VARCHAR(50)     NO         \-            Invoice/Document number

  document_date           DATE            NO         \-            Document date

  party_gstin             VARCHAR(15)     YES        \-            Counter-party GSTIN

  party_name              VARCHAR(200)    NO         \-            Party name

  party_state_code        VARCHAR(2)      YES        \-            Party state code

  place_of_supply         VARCHAR(2)      NO         \-            POS state code

  is_igst                 BOOLEAN         NO         \-            Inter-state (IGST)

  hsn_code                VARCHAR(10)     YES        \-            HSN/SAC code

  description             VARCHAR(500)    YES        \-            Item description

  taxable_value           NUMERIC(14,2)   NO         \-            Taxable value

  cgst_rate               NUMERIC(5,2)    NO         0             CGST rate

  cgst_amount             NUMERIC(12,2)   NO         0             CGST amount

  sgst_rate               NUMERIC(5,2)    NO         0             SGST rate

  sgst_amount             NUMERIC(12,2)   NO         0             SGST amount

  igst_rate               NUMERIC(5,2)    NO         0             IGST rate

  igst_amount             NUMERIC(12,2)   NO         0             IGST amount

  cess_rate               NUMERIC(5,2)    NO         0             Cess rate

  cess_amount             NUMERIC(12,2)   NO         0             Cess amount

  total_gst               NUMERIC(14,2)   NO         \-            Total GST

  total_amount            NUMERIC(14,2)   NO         \-            Total invoice value

  itc_eligible            BOOLEAN         NO         TRUE          ITC eligible

  itc_ineligible_reason   VARCHAR(100)    YES        \-            Reason if not eligible

  reversal_required       BOOLEAN         NO         FALSE         ITC reversal needed

  reversed_amount         NUMERIC(12,2)   NO         0             Reversed amount

  reference_voucher_id    BIGINT          YES        \-            Source voucher

  return_period           VARCHAR(10)     YES        \-            MMYYYY

  return_filed            BOOLEAN         NO         FALSE         Included in return

  gstr1_status            VARCHAR(20)     YES        \-            UPLOADED, FILED

  gstr2b_matched          BOOLEAN         NO         FALSE         Matched in 2B

  status                  VARCHAR(20)     NO         ACTIVE        ACTIVE, AMENDED, CANCELLED

  \+ Audit Columns                                                 Standard audit columns
  ----------------------- --------------- ---------- ------------- ----------------------------------

**3.3 GST Return Summary (TXN_GST_RETURN)**

  ------------------ --------------- ---------- ------------- -------------------------------
  **Column**         **Type**        **Null**   **Default**   **Description**

  return_id          BIGSERIAL       NO         Auto          Primary Key

  org_id             BIGINT          NO         \-            FK to MST_ORGANIZATION

  gstin              VARCHAR(15)     NO         \-            GSTIN

  return_type        VARCHAR(10)     NO         \-            GSTR1, GSTR3B, GSTR9

  return_period      VARCHAR(10)     NO         \-            MMYYYY

  financial_year     VARCHAR(10)     NO         \-            FY

  due_date           DATE            NO         \-            Filing due date

  output_igst        NUMERIC(14,2)   NO         0             Output IGST

  output_cgst        NUMERIC(14,2)   NO         0             Output CGST

  output_sgst        NUMERIC(14,2)   NO         0             Output SGST

  output_cess        NUMERIC(12,2)   NO         0             Output Cess

  total_output       NUMERIC(14,2)   NO         0             Total output tax

  input_igst         NUMERIC(14,2)   NO         0             Input IGST

  input_cgst         NUMERIC(14,2)   NO         0             Input CGST

  input_sgst         NUMERIC(14,2)   NO         0             Input SGST

  input_cess         NUMERIC(12,2)   NO         0             Input Cess

  total_input        NUMERIC(14,2)   NO         0             Total input credit

  net_liability      NUMERIC(14,2)   NO         0             Net tax payable

  cash_paid          NUMERIC(14,2)   NO         0             Paid via cash ledger

  credit_utilized    NUMERIC(14,2)   NO         0             ITC utilized

  interest           NUMERIC(12,2)   NO         0             Interest if late

  late_fee           NUMERIC(10,2)   NO         0             Late filing fee

  filing_date        DATE            YES        \-            Actual filing date

  arn                VARCHAR(30)     YES        \-            Acknowledgement number

  status             VARCHAR(20)     NO         DRAFT         DRAFT, FILED, REVISED

  \+ Audit Columns                                            Standard audit columns
  ------------------ --------------- ---------- ------------- -------------------------------

**3.4 GST Rates (Service Companies)**

  ------------------------------- ------------- -------------- ------------------------
  **Service/Item**                **HSN/SAC**   **GST Rate**   **Type**

  Financial services (interest)   997113        18%            Exempt for lending

  Processing fees                 997119        18%            Taxable

  Insurance services              997132        18%            Taxable

  Legal services                  998211        18%            Taxable (RCM)

  Audit services                  998221        18%            Taxable

  IT services                     998314        18%            Taxable

  Rent - Commercial               997212        18%            Taxable

  Office supplies                 Various       5-18%          Varies
  ------------------------------- ------------- -------------- ------------------------

**4. Bank Reconciliation Statement (BRS)**

Automated reconciliation between book balance and bank statement.

**4.1 Bank Statement Import (TXN_BANK_STATEMENT)**

  -------------------- --------------- ---------- ------------- --------------------------------------
  **Column**           **Type**        **Null**   **Default**   **Description**

  statement_id         BIGSERIAL       NO         Auto          Primary Key

  org_id               BIGINT          NO         \-            FK to MST_ORGANIZATION

  bank_account_id      BIGINT          NO         \-            FK to MST_BANK_ACCOUNT

  statement_date       DATE            NO         \-            Transaction date

  value_date           DATE            YES        \-            Value date

  transaction_ref      VARCHAR(50)     YES        \-            Bank reference

  description          VARCHAR(500)    NO         \-            Transaction narration

  cheque_number        VARCHAR(20)     YES        \-            Cheque number if any

  debit_amount         NUMERIC(14,2)   NO         0             Debit (withdrawal)

  credit_amount        NUMERIC(14,2)   NO         0             Credit (deposit)

  running_balance      NUMERIC(14,2)   YES        \-            Balance per statement

  import_batch_id      BIGINT          YES        \-            Import batch reference

  import_date          DATE            NO         \-            Statement import date

  reconciled           BOOLEAN         NO         FALSE         Reconciliation status

  reconciled_date      DATE            YES        \-            Reconciliation date

  matched_voucher_id   BIGINT          YES        \-            FK to TXN_VOUCHER

  match_type           VARCHAR(20)     YES        \-            AUTO, MANUAL, PARTIAL

  reconciliation_id    BIGINT          YES        \-            FK to TXN_BRS

  remarks              VARCHAR(500)    YES        \-            Reconciliation remarks

  status               VARCHAR(20)     NO         PENDING       PENDING, MATCHED, UNMATCHED, IGNORED

  \+ Audit Columns                                              Standard audit columns
  -------------------- --------------- ---------- ------------- --------------------------------------

**4.2 BRS Record (TXN_BRS)**

  ------------------------------- --------------- ---------- ------------- ------------------------------
  **Column**                      **Type**        **Null**   **Default**   **Description**

  brs_id                          BIGSERIAL       NO         Auto          Primary Key

  org_id                          BIGINT          NO         \-            FK to MST_ORGANIZATION

  bank_account_id                 BIGINT          NO         \-            FK to MST_BANK_ACCOUNT

  reconciliation_date             DATE            NO         \-            Reconciliation as of date

  period_from                     DATE            NO         \-            Period start

  period_to                       DATE            NO         \-            Period end

  book_balance                    NUMERIC(14,2)   NO         \-            Balance as per books

  bank_balance                    NUMERIC(14,2)   NO         \-            Balance as per bank

  cheques_issued_not_presented    NUMERIC(14,2)   NO         0             Cheques in transit (-)

  cheques_deposited_not_cleared   NUMERIC(14,2)   NO         0             Deposits in transit (+)

  bank_charges_not_booked         NUMERIC(14,2)   NO         0             Unbooked charges (-)

  interest_credited_not_booked    NUMERIC(14,2)   NO         0             Unbooked interest (+)

  direct_debits_not_booked        NUMERIC(14,2)   NO         0             Unbooked debits (-)

  direct_credits_not_booked       NUMERIC(14,2)   NO         0             Unbooked credits (+)

  other_adjustments               NUMERIC(14,2)   NO         0             Other adjustments

  reconciled_balance              NUMERIC(14,2)   NO         \-            Reconciled balance

  difference                      NUMERIC(14,2)   NO         0             Unexplained difference

  total_items_matched             INTEGER         NO         0             Items matched

  total_items_unmatched           INTEGER         NO         0             Items pending

  prepared_by                     BIGINT          NO         \-            Prepared by user

  reviewed_by                     BIGINT          YES        \-            Reviewed by user

  approved_by                     BIGINT          YES        \-            Approved by user

  status                          VARCHAR(20)     NO         DRAFT         DRAFT, COMPLETED, APPROVED

  \+ Audit Columns                                                         Standard audit columns
  ------------------------------- --------------- ---------- ------------- ------------------------------

**4.3 BRS Reconciliation Items (TXN_BRS_ITEM)**

  ------------------ --------------- ---------- ------------- -------------------------------
  **Column**         **Type**        **Null**   **Default**   **Description**

  item_id            BIGSERIAL       NO         Auto          Primary Key

  brs_id             BIGINT          NO         \-            FK to TXN_BRS

  item_type          VARCHAR(30)     NO         \-            See item types below

  item_date          DATE            NO         \-            Transaction date

  reference          VARCHAR(100)    YES        \-            Cheque/Ref number

  description        VARCHAR(500)    YES        \-            Description

  book_amount        NUMERIC(14,2)   YES        \-            Amount in books

  bank_amount        NUMERIC(14,2)   YES        \-            Amount in bank

  difference         NUMERIC(14,2)   YES        \-            Difference

  source             VARCHAR(20)     NO         \-            BOOK, BANK

  voucher_id         BIGINT          YES        \-            FK to TXN_VOUCHER

  statement_id       BIGINT          YES        \-            FK to TXN_BANK_STATEMENT

  aging_days         INTEGER         YES        \-            Days outstanding

  action_required    VARCHAR(100)    YES        \-            Follow-up action

  resolved           BOOLEAN         NO         FALSE         Item resolved

  resolution_date    DATE            YES        \-            Resolution date

  \+ Audit Columns                                            Standard audit columns
  ------------------ --------------- ---------- ------------- -------------------------------

**4.4 BRS Item Types**

  ------------------------------ ------------ -------------------- ----------------------
  **Item Type**                  **Source**   **Impact**           **Action**

  CHEQUE_ISSUED_NOT_PRESENTED    Book         Subtract from bank   Track cheque status

  CHEQUE_DEPOSITED_NOT_CLEARED   Book         Add to bank          Follow up with bank

  BANK_CHARGES_NOT_BOOKED        Bank         Debit in books       Pass entry

  INTEREST_CREDIT_NOT_BOOKED     Bank         Credit in books      Pass entry

  DIRECT_DEBIT_NOT_BOOKED        Bank         Debit in books       Identify and book

  DIRECT_CREDIT_NOT_BOOKED       Bank         Credit in books      Identify and book

  STALE_CHEQUE                   Book         Reverse entry        Cancel cheque

  AMOUNT_MISMATCH                Both         Investigate          Correct entry

  DUPLICATE_ENTRY                Book/Bank    Reverse duplicate    Correct entry
  ------------------------------ ------------ -------------------- ----------------------

**5. Fixed Deposit Tracker**

Track FDs placed by SMFC and FDs received from borrowers as collateral.

**5.1 FD Placed (TXN_FD_PLACED)**

Fixed deposits placed by SMFC with banks/institutions.

  ------------------------ --------------- ---------- ------------- ------------------------------------
  **Column**               **Type**        **Null**   **Default**   **Description**

  fd_placed_id             BIGSERIAL       NO         Auto          Primary Key

  org_id                   BIGINT          NO         \-            FK to MST_ORGANIZATION

  fd_number                VARCHAR(50)     NO         \-            FD receipt number

  fd_reference             VARCHAR(30)     NO         \-            Internal reference

  bank_id                  BIGINT          NO         \-            FK to MST_BANK (where placed)

  branch_name              VARCHAR(200)    YES        \-            Bank branch

  fd_type                  VARCHAR(30)     NO         \-            TERM, CUMULATIVE, TAX_SAVER, FLEXI

  deposit_date             DATE            NO         \-            Deposit date

  maturity_date            DATE            NO         \-            Maturity date

  tenure_days              INTEGER         NO         \-            Tenure in days

  principal_amount         NUMERIC(14,2)   NO         \-            Principal deposited

  interest_rate            NUMERIC(5,2)    NO         \-            Interest rate p.a.

  interest_type            VARCHAR(20)     NO         \-            SIMPLE, COMPOUND

  payout_frequency         VARCHAR(20)     NO         \-            MONTHLY, QUARTERLY, MATURITY

  maturity_value           NUMERIC(14,2)   NO         \-            Maturity amount

  interest_earned_ytd      NUMERIC(12,2)   NO         0             Interest earned YTD

  tds_deducted_ytd         NUMERIC(12,2)   NO         0             TDS deducted YTD

  last_interest_date       DATE            YES        \-            Last interest credit

  auto_renewal             BOOLEAN         NO         FALSE         Auto-renew on maturity

  renewal_tenure_days      INTEGER         YES        \-            Renewal tenure

  lien_marked              BOOLEAN         NO         FALSE         Lien exists

  lien_details             VARCHAR(500)    YES        \-            Lien purpose/holder

  nominee_name             VARCHAR(200)    YES        \-            Nominee

  encashment_date          DATE            YES        \-            Premature/Maturity encash

  encashment_amount        NUMERIC(14,2)   YES        \-            Encashment value

  encashment_type          VARCHAR(20)     YES        \-            MATURITY, PREMATURE

  penalty_amount           NUMERIC(12,2)   YES        \-            Premature penalty

  source_bank_account_id   BIGINT          YES        \-            Funded from account

  gl_account_id            BIGINT          YES        \-            FK to MST_COA

  status                   VARCHAR(20)     NO         ACTIVE        ACTIVE, MATURED, ENCASHED, RENEWED

  \+ Audit Columns                                                  Standard audit columns
  ------------------------ --------------- ---------- ------------- ------------------------------------

**5.2 FD Received as Collateral (TXN_FD_COLLATERAL)**

Fixed deposits received from borrowers as security.

  ------------------- --------------- ---------- ------------- ------------------------------------
  **Column**          **Type**        **Null**   **Default**   **Description**

  fd_collateral_id    BIGSERIAL       NO         Auto          Primary Key

  org_id              BIGINT          NO         \-            FK to MST_ORGANIZATION

  loan_account_id     BIGINT          NO         \-            FK to TXN_LOAN_ACCOUNT

  entity_id           BIGINT          NO         \-            FK to MST_ENTITY (owner)

  fd_number           VARCHAR(50)     NO         \-            FD receipt number

  issuing_bank        VARCHAR(200)    NO         \-            FD issuing bank

  branch_name         VARCHAR(200)    YES        \-            Branch

  deposit_date        DATE            NO         \-            Original deposit date

  maturity_date       DATE            NO         \-            Maturity date

  principal_amount    NUMERIC(14,2)   NO         \-            FD principal

  interest_rate       NUMERIC(5,2)    NO         \-            Interest rate

  maturity_value      NUMERIC(14,2)   NO         \-            Maturity value

  margin_pct          NUMERIC(5,2)    NO         25            Margin held %

  drawable_value      NUMERIC(14,2)   NO         \-            Value after margin

  lien_marked         BOOLEAN         NO         FALSE         Lien marked with bank

  lien_date           DATE            YES        \-            Lien marking date

  lien_reference      VARCHAR(100)    YES        \-            Lien reference

  original_held       BOOLEAN         NO         TRUE          Original FDR with SMFC

  physical_location   VARCHAR(200)    YES        \-            FDR storage location

  verified            BOOLEAN         NO         FALSE         FDR verified with bank

  verified_date       DATE            YES        \-            Verification date

  renewal_due         BOOLEAN         NO         FALSE         Renewal reminder

  release_date        DATE            YES        \-            FDR release date

  release_reason      VARCHAR(200)    YES        \-            Release reason

  released_to         VARCHAR(200)    YES        \-            Released to person

  status              VARCHAR(20)     NO         ACTIVE        ACTIVE, RELEASED, INVOKED, EXPIRED

  \+ Audit Columns                                             Standard audit columns
  ------------------- --------------- ---------- ------------- ------------------------------------

**5.3 FD Interest Accrual (TXN_FD_INTEREST)**

  --------------------- --------------- ---------- ------------- -------------------------------
  **Column**            **Type**        **Null**   **Default**   **Description**

  interest_id           BIGSERIAL       NO         Auto          Primary Key

  fd_placed_id          BIGINT          NO         \-            FK to TXN_FD_PLACED

  accrual_date          DATE            NO         \-            Accrual date

  period_from           DATE            NO         \-            Period start

  period_to             DATE            NO         \-            Period end

  days                  INTEGER         NO         \-            Days in period

  principal_balance     NUMERIC(14,2)   NO         \-            Principal

  interest_rate         NUMERIC(5,2)    NO         \-            Rate

  interest_accrued      NUMERIC(12,2)   NO         \-            Interest for period

  cumulative_interest   NUMERIC(12,2)   NO         \-            Total interest

  tds_rate              NUMERIC(5,2)    NO         10            TDS rate

  tds_amount            NUMERIC(12,2)   NO         \-            TDS on interest

  net_interest          NUMERIC(12,2)   NO         \-            Net interest

  credited              BOOLEAN         NO         FALSE         Interest credited

  credit_date           DATE            YES        \-            Credit date

  voucher_id            BIGINT          YES        \-            FK to TXN_VOUCHER

  \+ Audit Columns                                               Standard audit columns
  --------------------- --------------- ---------- ------------- -------------------------------

**6. Business Flows**

**6.1 Fixed Asset Acquisition Flow**

**Step 1: Purchase Requisition** - Initiate asset purchase request

**Step 2: PO & Invoice** - Create PO, receive invoice from vendor

**Step 3: Capitalize Asset** - Create asset record with all costs

INSERT INTO mst_fixed_asset (acquisition_cost, installation_cost, \...)

total_cost = acquisition_cost + installation_cost + other_costs

depreciable_value = total_cost - residual_value

**Step 4: Accounting Entry** - Post capitalization entry

Dr: Fixed Asset Account

Cr: Bank / Vendor Payable

**Step 5: Monthly Depreciation** - Run depreciation at month-end

FOR each active asset:

dep = calculate_depreciation(asset, period)

INSERT INTO txn_depreciation (\...)

Dr: Depreciation Expense

Cr: Accumulated Depreciation

**6.2 TDS Processing Flow**

**Step 1: Payment with TDS** - Vendor payment or interest payment

**Step 2: Calculate TDS** - Apply section rate

gross_amount = invoice_amount

tds_rate = get_rate(section, pan_available, deductee_type)

tds_amount = gross_amount × tds_rate

net_payment = gross_amount - tds_amount

**Step 3: Record TDS** - Create TDS transaction

INSERT INTO txn_tds (section, gross_amount, tds_amount, quarter, \...)

**Step 4: Deposit TDS** - Pay to government by due date

INSERT INTO txn_tds_challan (\...)

UPDATE txn_tds SET challan_id, status=\'DEPOSITED\'

**Step 5: File Return** - Prepare and file quarterly return

Generate 26Q/24Q data

Upload to TRACES

UPDATE txn_tds SET return_filed=TRUE

**6.3 BRS Flow**

**Step 1: Import Bank Statement** - Upload/Auto-fetch statement

LOAD DATA INTO txn_bank_statement FROM bank_file

**Step 2: Auto-Match** - Match by reference/amount/date

FOR each statement_line:

voucher = FIND voucher WHERE cheque_no = statement.cheque_no

IF match THEN UPDATE statement SET reconciled=TRUE, voucher_id

**Step 3: Manual Match** - Match remaining items manually

**Step 4: Identify Differences** - Categorize unmatched items

INSERT INTO txn_brs_item (type, source, amount, \...)

**Step 5: Generate BRS** - Calculate reconciliation

reconciled_balance = bank_balance

\+ cheques_deposited_not_cleared

\- cheques_issued_not_presented

\+ unbooked_credits

\- unbooked_debits

difference = book_balance - reconciled_balance

**Step 6: Review & Approve** - Get BRS approved

**7. Business Rules**

**7.1 Fixed Asset Rules**

  ------------- -------------------------- -------------------------- ------------------------------
  **Rule ID**   **Rule**                   **Condition**              **Action**

  FA-001        Capitalization threshold   Cost \< threshold          Expense, don\'t capitalize

  FA-002        Depreciation start         Put to use date required   Start dep from put to use

  FA-003        Full month convention      Asset added mid-month      Full month dep if \> 15 days

  FA-004        Disposal validation        Asset has pending dep      Run dep before disposal

  FA-005        Transfer approval          Inter-location transfer    Require approval

  FA-006        Insurance tracking         Expires within 30 days     Generate alert
  ------------- -------------------------- -------------------------- ------------------------------

**7.2 TDS Rules**

  ------------- ---------------------- -------------------------------- ---------------------------------
  **Rule ID**   **Rule**               **Condition**                    **Action**

  TDS-001       PAN validation         PAN not available                Apply 20% rate

  TDS-002       Threshold check        Amount \< section threshold      No TDS deduction

  TDS-003       Lower cert validity    Certificate expired              Apply normal rate

  TDS-004       Deposit deadline       7th of next month                Alert before due date

  TDS-005       Return filing          Quarterly due date approaching   Generate reminder

  TDS-006       Interest calculation   Late deposit                     Calculate interest @ 1.5%/month
  ------------- ---------------------- -------------------------------- ---------------------------------

**7.3 GST Rules**

  ------------- ------------------- ---------------------------------- ----------------------
  **Rule ID**   **Rule**            **Condition**                      **Action**

  GST-001       GSTIN validation    Invalid GSTIN format               Block transaction

  GST-002       ITC eligibility     Blocked credit categories          Mark ITC ineligible

  GST-003       RCM applicability   Unregistered vendor \> ₹5000/day   Apply RCM

  GST-004       GSTR-2B matching    Invoice not in 2B                  Flag for review

  GST-005       ITC reversal        Non-payment within 180 days        Reverse ITC

  GST-006       Place of supply     Service to different state         Apply IGST
  ------------- ------------------- ---------------------------------- ----------------------

**7.4 BRS Rules**

  ------------- ---------------------- --------------------------------- ---------------------------
  **Rule ID**   **Rule**               **Condition**                     **Action**

  BRS-001       Stale cheque           Cheque issued \> 90 days ago      Mark stale, reverse entry

  BRS-002       Auto-matching          Exact amount + date + ref match   Auto-reconcile

  BRS-003       Tolerance matching     Amount within ₹1 tolerance        Suggest match

  BRS-004       Aging analysis         Item pending \> 30 days           Escalate for action

  BRS-005       Difference threshold   Unexplained difference \> ₹1000   Require investigation

  BRS-006       Month-end completion   BRS not approved by 10th          Alert management
  ------------- ---------------------- --------------------------------- ---------------------------

*\-\-- End of Phase 6 \-\--*

Phase 7 covers: Compliance, Dashboard, Portals, Inventory
