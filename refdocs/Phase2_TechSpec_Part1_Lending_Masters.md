**SMFC Ltd**

Integrated ERP Solution

**TECHNICAL SPECIFICATION**

Phase 2: Lending Pipeline

Part 1: Lending Masters, KYC & Credit Rating

*Developer Reference Document*

Version 1.0

**Table of Contents**

1\. Module Overview & Data Model

2\. Borrower/Customer Masters

2.1 Entity Master (MST_ENTITY)

2.2 Entity Contacts (MST_ENTITY_CONTACT)

2.3 Entity Addresses (MST_ENTITY_ADDRESS)

2.4 Entity Bank Accounts (MST_ENTITY_BANK)

2.5 Related Parties (MAP_ENTITY_RELATION)

3\. KYC Module

3.1 KYC Document Types (MST_KYC_DOC_TYPE)

3.2 Entity KYC (TXN_ENTITY_KYC)

3.3 CKYC Integration

4\. Credit Rating Module

4.1 Risk Categories (MST_RISK_CATEGORY)

4.2 Risk Parameters (MST_RISK_PARAMETER)

4.3 Rating Matrix (MST_RATING_MATRIX)

4.4 Entity Rating (TXN_ENTITY_RATING)

4.5 Rating Workflow

5\. Loan Product Masters

5.1 Loan Products/Schemes (MST_LOAN_PRODUCT)

5.2 Interest Rate Master (MST_INTEREST_RATE)

5.3 Fee Master (MST_FEE)

5.4 Document Checklist (MST_DOC_CHECKLIST)

6\. Security/Collateral Masters

7\. Business Rules & Validations

8\. KYC & Rating Flows

**1. Module Overview & Data Model**

Phase 2 covers the lending pipeline from borrower onboarding through loan origination. This part focuses on the foundational masters and pre-sanction processes.

**1.1 Scope**

- Borrower/Entity Master: Complete customer database with contacts, addresses, bank accounts

- KYC Module: Document collection, verification, CKYC integration

- Credit Rating: Risk assessment framework with scoring model

- Loan Products: Scheme definitions, interest rates, fees, document requirements

- Security Masters: Collateral types and valuation framework

**1.2 Entity Relationship Overview**

The lending module centers around the ENTITY (borrower) which connects to:

MST_ENTITY (Borrower)

\|\-- MST_ENTITY_CONTACT (Directors, Key Persons)

\|\-- MST_ENTITY_ADDRESS (Registered, Correspondence)

\|\-- MST_ENTITY_BANK (Bank Accounts)

\|\-- MAP_ENTITY_RELATION (Group Companies, Promoters)

\|\-- TXN_ENTITY_KYC (KYC Documents)

\|\-- TXN_ENTITY_RATING (Credit Rating History)

\|\-- TXN_LOAN_APPLICATION (Loan Applications)

**1.3 Key Design Principles**

- Entity-centric: All data linked to a central entity record

- Temporal: Historical tracking of KYC, ratings, and key data

- Configurable: Risk parameters, rating models, product features are configuration-driven

- Audit Complete: Full history of all changes with maker-checker

- Integration Ready: CKYC, Credit Bureaus, external rating agencies

**2. Borrower/Customer Masters**

Comprehensive borrower information management supporting both corporate and individual entities.

**2.1 Entity Master (MST_ENTITY)**

Central borrower/customer record. Supports corporates, SPVs, government bodies, and individuals.

**2.1.1 Table Definition**

  ------------------------- --------------- ---------- ------------- ---------------------------------------------------------
  **Column**                **Type**        **Null**   **Default**   **Description**

  entity_id                 BIGSERIAL       NO         Auto          Primary Key

  org_id                    BIGINT          NO         \-            FK to MST_ORGANIZATION

  entity_code               VARCHAR(20)     NO         \-            Unique entity code (auto-generated)

  entity_type               VARCHAR(30)     NO         \-            CORPORATE, SPV, GOVT_BODY, INDIVIDUAL, PARTNERSHIP, LLP

  legal_name                VARCHAR(300)    NO         \-            Full legal name

  short_name                VARCHAR(100)    YES        \-            Common/short name

  trade_name                VARCHAR(200)    YES        \-            Trading name if different

  incorporation_date        DATE            YES        \-            Date of incorporation

  incorporation_place       VARCHAR(100)    YES        \-            Place of incorporation

  cin                       VARCHAR(25)     YES        \-            Corporate Identity Number

  llpin                     VARCHAR(20)     YES        \-            LLP Identification Number

  pan                       VARCHAR(10)     NO         \-            PAN (mandatory for all)

  tan                       VARCHAR(10)     YES        \-            TAN if applicable

  gstin                     VARCHAR(15)     YES        \-            Primary GSTIN

  lei                       VARCHAR(20)     YES        \-            Legal Entity Identifier

  din_main_promoter         VARCHAR(10)     YES        \-            DIN of main promoter

  industry_sector           VARCHAR(100)    YES        \-            Industry sector

  industry_subsector        VARCHAR(100)    YES        \-            Sub-sector

  nic_code                  VARCHAR(10)     YES        \-            NIC classification code

  constitution              VARCHAR(50)     YES        \-            PUBLIC_LTD, PRIVATE_LTD, PSU, GOVT, etc.

  ownership_type            VARCHAR(30)     YES        \-            CENTRAL_GOVT, STATE_GOVT, PRIVATE, LISTED

  listed_exchange           VARCHAR(50)     YES        \-            BSE, NSE, etc. if listed

  stock_code                VARCHAR(20)     YES        \-            Stock symbol

  website                   VARCHAR(255)    YES        \-            Company website

  email                     VARCHAR(255)    YES        \-            Primary email

  phone                     VARCHAR(20)     YES        \-            Primary phone

  authorized_capital        NUMERIC(18,2)   YES        \-            Authorized share capital

  paid_up_capital           NUMERIC(18,2)   YES        \-            Paid-up capital

  net_worth                 NUMERIC(18,2)   YES        \-            Latest net worth

  net_worth_date            DATE            YES        \-            As of date for net worth

  annual_turnover           NUMERIC(18,2)   YES        \-            Latest annual turnover

  turnover_year             VARCHAR(10)     YES        \-            FY for turnover

  employee_count            INTEGER         YES        \-            Number of employees

  ckyc_number               VARCHAR(20)     YES        \-            CKYC registration number

  ckyc_date                 DATE            YES        \-            CKYC registration date

  external_rating           VARCHAR(20)     YES        \-            External credit rating

  rating_agency             VARCHAR(50)     YES        \-            CRISIL, ICRA, CARE, etc.

  rating_date               DATE            YES        \-            Rating date

  internal_rating           VARCHAR(10)     YES        \-            Internal credit rating

  internal_rating_date      DATE            YES        \-            Internal rating date

  risk_category             VARCHAR(20)     YES        \-            LOW, MEDIUM, HIGH

  relationship_manager_id   BIGINT          YES        \-            FK to MST_USER

  source_of_lead            VARCHAR(50)     YES        \-            How entity was acquired

  remarks                   TEXT            YES        \-            General remarks

  status                    VARCHAR(20)     NO         ACTIVE        ACTIVE, INACTIVE, BLACKLISTED, PROSPECT

  blacklist_reason          VARCHAR(500)    YES        \-            If blacklisted

  blacklist_date            DATE            YES        \-            Blacklist date

  \+ Audit Columns                                                   Standard audit columns
  ------------------------- --------------- ---------- ------------- ---------------------------------------------------------

**2.1.2 Indexes**

PRIMARY KEY (entity_id)

UNIQUE INDEX idx_entity_code ON mst_entity(org_id, entity_code)

UNIQUE INDEX idx_entity_pan ON mst_entity(pan) WHERE is_deleted = FALSE

UNIQUE INDEX idx_entity_cin ON mst_entity(cin) WHERE cin IS NOT NULL AND is_deleted = FALSE

INDEX idx_entity_type ON mst_entity(entity_type)

INDEX idx_entity_status ON mst_entity(status)

INDEX idx_entity_rm ON mst_entity(relationship_manager_id)

INDEX idx_entity_sector ON mst_entity(industry_sector)

INDEX idx_entity_name ON mst_entity USING gin(legal_name gin_trgm_ops) \-- Full text search

**2.1.3 Entity Types**

  ------------- ------------------------------- ------------------------- ---------------------
  **Type**      **Description**                 **Required Fields**       **Example**

  CORPORATE     Registered company              CIN, PAN                  Tata Steel Ltd

  SPV           Special Purpose Vehicle         CIN, PAN, Parent Entity   ABC Infra SPV Ltd

  GOVT_BODY     Government entity               PAN                       Port Authority

  PSU           Public Sector Undertaking       CIN, PAN                  NTPC Ltd

  PARTNERSHIP   Partnership firm                PAN                       M/s XYZ Associates

  LLP           Limited Liability Partnership   LLPIN, PAN                ABC Consultants LLP

  INDIVIDUAL    Individual borrower             PAN, Aadhaar              John Doe
  ------------- ------------------------------- ------------------------- ---------------------

**2.1.4 Business Rules**

  ------------- ----------------------------- --------------------------------------------------------------------- ------------------------
  **Rule ID**   **Rule**                      **Validation**                                                        **Error Code**

  ENT-001       Unique PAN                    PAN must be unique across active entities                             ERR_DUPLICATE_PAN

  ENT-002       Valid PAN format              REGEX: \[A-Z\]{5}\[0-9\]{4}\[A-Z\]{1}                                 ERR_INVALID_PAN

  ENT-003       CIN required for corporates   If type=CORPORATE, CIN mandatory                                      ERR_CIN_REQUIRED

  ENT-004       Valid CIN format              REGEX: \[A-Z\]{1}\[0-9\]{5}\[A-Z\]{2}\[0-9\]{4}\[A-Z\]{3}\[0-9\]{6}   ERR_INVALID_CIN

  ENT-005       LLPIN for LLP                 If type=LLP, LLPIN mandatory                                          ERR_LLPIN_REQUIRED

  ENT-006       Valid GSTIN                   GSTIN\[2:12\] must match PAN                                          ERR_GSTIN_PAN_MISMATCH

  ENT-007       Blacklist reason              If status=BLACKLISTED, reason required                                ERR_BLACKLIST_REASON

  ENT-008       Cannot delete with loans      Entity with active loans cannot be deleted                            ERR_ACTIVE_LOANS

  ENT-009       KYC before loan               Complete KYC required before loan application                         ERR_KYC_INCOMPLETE
  ------------- ----------------------------- --------------------------------------------------------------------- ------------------------

**2.2 Entity Contacts (MST_ENTITY_CONTACT)**

Key contact persons including directors, promoters, authorized signatories.

**2.2.1 Table Definition**

  ------------------------- --------------- ---------- ------------- ---------------------------------------------------
  **Column**                **Type**        **Null**   **Default**   **Description**

  contact_id                BIGSERIAL       NO         Auto          Primary Key

  entity_id                 BIGINT          NO         \-            FK to MST_ENTITY

  contact_type              VARCHAR(30)     NO         \-            DIRECTOR, PROMOTER, AUTH_SIGNATORY, CFO, CEO, KMP

  salutation                VARCHAR(10)     YES        \-            Mr, Ms, Dr, etc.

  first_name                VARCHAR(100)    NO         \-            First name

  middle_name               VARCHAR(100)    YES        \-            Middle name

  last_name                 VARCHAR(100)    YES        \-            Last name

  full_name                 VARCHAR(300)    NO         \-            Computed full name

  designation               VARCHAR(100)    YES        \-            Current designation

  din                       VARCHAR(10)     YES        \-            Director Identification Number

  pan                       VARCHAR(10)     YES        \-            PAN of individual

  aadhaar_masked            VARCHAR(16)     YES        \-            Masked Aadhaar (XXXX-XXXX-1234)

  dob                       DATE            YES        \-            Date of birth

  gender                    VARCHAR(10)     YES        \-            MALE, FEMALE, OTHER

  nationality               VARCHAR(50)     YES        Indian        Nationality

  email                     VARCHAR(255)    YES        \-            Email address

  mobile                    VARCHAR(20)     YES        \-            Mobile number

  alternate_phone           VARCHAR(20)     YES        \-            Alternate phone

  address                   TEXT            YES        \-            Current address

  appointment_date          DATE            YES        \-            Date of appointment

  cessation_date            DATE            YES        \-            Date of cessation

  shareholding_pct          NUMERIC(5,2)    YES        \-            Shareholding percentage

  is_authorized_signatory   BOOLEAN         NO         FALSE         Can sign documents

  signing_limit             NUMERIC(18,2)   YES        \-            Signing authority limit

  is_primary_contact        BOOLEAN         NO         FALSE         Primary contact person

  kyc_verified              BOOLEAN         NO         FALSE         KYC completed

  photo_path                VARCHAR(500)    YES        \-            Photo file path

  signature_path            VARCHAR(500)    YES        \-            Signature specimen path

  status                    VARCHAR(20)     NO         ACTIVE        ACTIVE, INACTIVE, CEASED

  \+ Audit Columns                                                   Standard audit columns
  ------------------------- --------------- ---------- ------------- ---------------------------------------------------

**2.2.2 Business Rules**

  ------------- -------------------------- ---------------------------------------------------- --------------------
  **Rule ID**   **Rule**                   **Validation**                                       **Error Code**

  CON-001       At least one contact       Entity must have at least one contact                ERR_NO_CONTACT

  CON-002       Primary contact required   One contact must be marked primary                   ERR_NO_PRIMARY

  CON-003       DIN for directors          If contact_type=DIRECTOR, DIN required               ERR_DIN_REQUIRED

  CON-004       Valid DIN format           REGEX: \[0-9\]{8}                                    ERR_INVALID_DIN

  CON-005       Auth signatory limit       If is_authorized_signatory, signing_limit required   ERR_LIMIT_REQUIRED

  CON-006       Unique DIN per entity      DIN cannot repeat within same entity                 ERR_DUPLICATE_DIN
  ------------- -------------------------- ---------------------------------------------------- --------------------

**2.3 Entity Addresses (MST_ENTITY_ADDRESS)**

Multiple addresses for registered office, correspondence, project sites, etc.

**2.3.1 Table Definition**

  ------------------ --------------- ---------- ------------- ----------------------------------------------------
  **Column**         **Type**        **Null**   **Default**   **Description**

  address_id         BIGSERIAL       NO         Auto          Primary Key

  entity_id          BIGINT          NO         \-            FK to MST_ENTITY

  address_type       VARCHAR(30)     NO         \-            REGISTERED, CORRESPONDENCE, PLANT, PROJECT, BRANCH

  address_line1      VARCHAR(200)    NO         \-            Address line 1

  address_line2      VARCHAR(200)    YES        \-            Address line 2

  address_line3      VARCHAR(200)    YES        \-            Address line 3

  landmark           VARCHAR(200)    YES        \-            Nearby landmark

  city               VARCHAR(100)    NO         \-            City/Town

  district           VARCHAR(100)    YES        \-            District

  state_code         VARCHAR(2)      NO         \-            State code (01-37)

  state_name         VARCHAR(100)    NO         \-            State name

  pincode            VARCHAR(6)      NO         \-            PIN code

  country            VARCHAR(50)     NO         India         Country

  phone              VARCHAR(20)     YES        \-            Landline number

  fax                VARCHAR(20)     YES        \-            Fax number

  gstin              VARCHAR(15)     YES        \-            State-specific GSTIN

  latitude           NUMERIC(10,8)   YES        \-            GPS latitude

  longitude          NUMERIC(11,8)   YES        \-            GPS longitude

  is_primary         BOOLEAN         NO         FALSE         Primary address

  verified           BOOLEAN         NO         FALSE         Address verified

  verified_date      DATE            YES        \-            Verification date

  verified_by        BIGINT          YES        \-            Verified by user

  status             VARCHAR(20)     NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                            Standard audit columns
  ------------------ --------------- ---------- ------------- ----------------------------------------------------

**2.3.2 Business Rules**

  ------------- ----------------------------- ------------------------------------------ -------------------
  **Rule ID**   **Rule**                      **Validation**                             **Error Code**

  ADDR-001      Registered address required   CORPORATE must have REGISTERED address     ERR_REG_ADDR_REQD

  ADDR-002      One primary address           Exactly one address marked is_primary      ERR_PRIMARY_ADDR

  ADDR-003      Valid PIN format              REGEX: \[1-9\]\[0-9\]{5}                   ERR_INVALID_PIN

  ADDR-004      State-PIN match               First 2 digits of PIN should match state   WARN_PIN_STATE

  ADDR-005      GSTIN state match             If GSTIN provided, state code must match   ERR_GSTIN_STATE
  ------------- ----------------------------- ------------------------------------------ -------------------

**2.4 Entity Bank Accounts (MST_ENTITY_BANK)**

Borrower bank accounts for disbursement and collection.

**2.4.1 Table Definition**

  ------------------------- -------------- ---------- ------------- ------------------------------
  **Column**                **Type**       **Null**   **Default**   **Description**

  entity_bank_id            BIGSERIAL      NO         Auto          Primary Key

  entity_id                 BIGINT         NO         \-            FK to MST_ENTITY

  account_holder_name       VARCHAR(200)   NO         \-            Name as per bank records

  bank_name                 VARCHAR(200)   NO         \-            Bank name

  branch_name               VARCHAR(200)   YES        \-            Branch name

  account_number            VARCHAR(30)    NO         \-            Bank account number

  ifsc_code                 VARCHAR(11)    NO         \-            IFSC code

  micr_code                 VARCHAR(10)    YES        \-            MICR code

  account_type              VARCHAR(30)    NO         \-            CURRENT, SAVINGS, CC, OD

  currency                  VARCHAR(3)     NO         INR           Account currency

  swift_code                VARCHAR(11)    YES        \-            SWIFT/BIC code

  is_escrow                 BOOLEAN        NO         FALSE         Escrow account

  is_disbursement_account   BOOLEAN        NO         TRUE          Use for disbursement

  is_collection_account     BOOLEAN        NO         FALSE         Use for collections

  is_primary                BOOLEAN        NO         FALSE         Primary account

  penny_drop_verified       BOOLEAN        NO         FALSE         Penny drop verification done

  penny_drop_date           DATE           YES        \-            Verification date

  penny_drop_ref            VARCHAR(50)    YES        \-            Verification reference

  cancelled_cheque_path     VARCHAR(500)   YES        \-            Cancelled cheque image

  status                    VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE, CLOSED

  \+ Audit Columns                                                  Standard audit columns
  ------------------------- -------------- ---------- ------------- ------------------------------

**2.4.2 Business Rules**

  ------------- ----------------------------- ------------------------------------------------- ---------------------
  **Rule ID**   **Rule**                      **Validation**                                    **Error Code**

  BANK-001      At least one account          Entity must have at least one bank account        ERR_NO_BANK_ACCT

  BANK-002      Valid IFSC                    REGEX: \[A-Z\]{4}0\[A-Z0-9\]{6}                   ERR_INVALID_IFSC

  BANK-003      Unique account                account_number + ifsc_code unique per entity      ERR_DUPLICATE_ACCT

  BANK-004      Penny drop for disbursement   If is_disbursement_account, penny drop required   ERR_VERIFY_ACCOUNT

  BANK-005      Primary account required      At least one primary account for disbursement     ERR_NO_PRIMARY_BANK

  BANK-006      Name match                    account_holder_name should match entity name      WARN_NAME_MISMATCH
  ------------- ----------------------------- ------------------------------------------------- ---------------------

**2.5 Related Parties (MAP_ENTITY_RELATION)**

Tracks relationships between entities - group companies, promoters, subsidiaries.

**2.5.1 Table Definition**

  --------------------- -------------- ---------- ------------- -------------------------------------------------------
  **Column**            **Type**       **Null**   **Default**   **Description**

  relation_id           BIGSERIAL      NO         Auto          Primary Key

  entity_id             BIGINT         NO         \-            FK to MST_ENTITY (primary)

  related_entity_id     BIGINT         YES        \-            FK to MST_ENTITY (if in system)

  related_entity_name   VARCHAR(300)   NO         \-            Related party name

  related_entity_pan    VARCHAR(10)    YES        \-            PAN of related party

  relation_type         VARCHAR(30)    NO         \-            PARENT, SUBSIDIARY, ASSOCIATE, GROUP_CO, PROMOTER, JV

  ownership_pct         NUMERIC(5,2)   YES        \-            Ownership percentage

  effective_from        DATE           NO         \-            Relationship start date

  effective_to          DATE           YES        \-            Relationship end date

  is_guarantor          BOOLEAN        NO         FALSE         Acts as guarantor

  remarks               VARCHAR(500)   YES        \-            Additional notes

  status                VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                              Standard audit columns
  --------------------- -------------- ---------- ------------- -------------------------------------------------------

**2.5.2 Relation Types**

  ------------- ------------------------ ------------------------ -------------------------
  **Type**      **Description**          **Ownership Required**   **Use Case**

  PARENT        Parent/Holding company   Yes (\>50%)              Corporate structure

  SUBSIDIARY    Subsidiary company       Yes (\>50%)              Corporate structure

  ASSOCIATE     Associate company        Yes (20-50%)             Corporate structure

  GROUP_CO      Group company            No                       Business group

  PROMOTER      Promoter entity          Yes                      Promoter details

  JV            Joint venture partner    Yes                      JV relationships

  GUARANTOR     Corporate guarantor      No                       Guarantee relationships
  ------------- ------------------------ ------------------------ -------------------------

**3. KYC Module**

Know Your Customer module for regulatory compliance and borrower verification.

**3.1 KYC Document Types (MST_KYC_DOC_TYPE)**

Master list of KYC document types with validation rules.

**3.1.1 Table Definition**

  ----------------------- -------------- ---------- ------------- --------------------------------------------
  **Column**              **Type**       **Null**   **Default**   **Description**

  doc_type_id             BIGSERIAL      NO         Auto          Primary Key

  org_id                  BIGINT         NO         \-            FK to MST_ORGANIZATION

  doc_code                VARCHAR(20)    NO         \-            Unique document code

  doc_name                VARCHAR(200)   NO         \-            Document name

  doc_category            VARCHAR(30)    NO         \-            IDENTITY, ADDRESS, FINANCIAL, LEGAL, OTHER

  applicable_to           VARCHAR(30)    NO         ALL           CORPORATE, INDIVIDUAL, ALL

  is_mandatory            BOOLEAN        NO         FALSE         Mandatory for KYC completion

  has_expiry              BOOLEAN        NO         FALSE         Document has expiry date

  default_validity_days   INTEGER        YES        \-            Default validity period

  verification_required   BOOLEAN        NO         TRUE          Requires verification

  verification_method     VARCHAR(30)    YES        \-            MANUAL, API, PHYSICAL

  api_provider            VARCHAR(50)    YES        \-            External API for verification

  max_file_size_mb        INTEGER        NO         5             Max upload size in MB

  allowed_formats         VARCHAR(100)   NO         PDF,JPG,PNG   Allowed file formats

  display_order           INTEGER        NO         0             Display sequence

  status                  VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                                Standard audit columns
  ----------------------- -------------- ---------- ------------- --------------------------------------------

**3.1.2 Standard KYC Document Types**

  ---------------- ---------------------------------- -------------- --------------- -------------------
  **Code**         **Document**                       **Category**   **Mandatory**   **Applicable To**

  PAN_CARD         PAN Card                           IDENTITY       Yes             ALL

  COI              Certificate of Incorporation       LEGAL          Yes             CORPORATE

  MOA              Memorandum of Association          LEGAL          Yes             CORPORATE

  AOA              Articles of Association            LEGAL          Yes             CORPORATE

  BR_AUTH          Board Resolution - Authorization   LEGAL          Yes             CORPORATE

  GST_REG          GST Registration Certificate       IDENTITY       No              ALL

  AADHAAR          Aadhaar Card                       IDENTITY       Yes             INDIVIDUAL

  ADDR_PROOF       Address Proof                      ADDRESS        Yes             ALL

  FIN_STMT_3Y      Financial Statements (3 years)     FINANCIAL      Yes             CORPORATE

  ITR_3Y           Income Tax Returns (3 years)       FINANCIAL      Yes             ALL

  BANK_STMT_6M     Bank Statements (6 months)         FINANCIAL      No              ALL

  NET_WORTH_CERT   Net Worth Certificate              FINANCIAL      No              INDIVIDUAL

  FORM_32          Form 32 - Director Details         LEGAL          No              CORPORATE

  CKYC_ACK         CKYC Acknowledgement               IDENTITY       No              ALL
  ---------------- ---------------------------------- -------------- --------------- -------------------

**3.2 Entity KYC (TXN_ENTITY_KYC)**

Stores actual KYC documents submitted by entities with verification status.

**3.2.1 Table Definition**

  ---------------------- -------------- ---------- ------------- --------------------------------------
  **Column**             **Type**       **Null**   **Default**   **Description**

  kyc_id                 BIGSERIAL      NO         Auto          Primary Key

  entity_id              BIGINT         NO         \-            FK to MST_ENTITY

  doc_type_id            BIGINT         NO         \-            FK to MST_KYC_DOC_TYPE

  document_number        VARCHAR(50)    YES        \-            Document reference number

  document_date          DATE           YES        \-            Document issue date

  expiry_date            DATE           YES        \-            Document expiry date

  issuing_authority      VARCHAR(200)   YES        \-            Issuing authority

  file_name              VARCHAR(255)   NO         \-            Uploaded file name

  file_path              VARCHAR(500)   NO         \-            Storage path

  file_size              INTEGER        NO         \-            Size in bytes

  file_hash              VARCHAR(64)    YES        \-            SHA-256 hash for integrity

  ocr_extracted_data     JSONB          YES        \-            OCR extracted data

  verification_status    VARCHAR(20)    NO         PENDING       PENDING, VERIFIED, REJECTED, EXPIRED

  verification_method    VARCHAR(30)    YES        \-            MANUAL, API, OCR

  verified_by            BIGINT         YES        \-            FK to MST_USER

  verified_at            TIMESTAMPTZ    YES        \-            Verification timestamp

  verification_remarks   VARCHAR(500)   YES        \-            Verification notes

  rejection_reason       VARCHAR(500)   YES        \-            If rejected

  api_response           JSONB          YES        \-            External API response

  is_latest              BOOLEAN        NO         TRUE          Latest version of this doc type

  version_number         INTEGER        NO         1             Document version

  previous_kyc_id        BIGINT         YES        \-            Previous version reference

  \+ Audit Columns                                               Standard audit columns
  ---------------------- -------------- ---------- ------------- --------------------------------------

**3.2.2 KYC Status Transitions**

  ----------------- -------------- --------------- -----------------------------
  **From Status**   **Action**     **To Status**   **Conditions**

  (new)             UPLOAD         PENDING         Document uploaded

  PENDING           VERIFY         VERIFIED        Verification successful

  PENDING           REJECT         REJECTED        Verification failed

  VERIFIED          EXPIRE         EXPIRED         Current date \> expiry_date

  REJECTED          RE-UPLOAD      PENDING         New document uploaded

  EXPIRED           RE-UPLOAD      PENDING         New document uploaded
  ----------------- -------------- --------------- -----------------------------

**3.2.3 Business Rules**

  ------------- ------------------------- --------------------------------------------- --------------------
  **Rule ID**   **Rule**                  **Validation**                                **Error Code**

  KYC-001       Mandatory docs complete   All mandatory docs must be VERIFIED           ERR_KYC_INCOMPLETE

  KYC-002       No expired docs           Cannot proceed if mandatory docs expired      ERR_KYC_EXPIRED

  KYC-003       File size limit           file_size \<= doc_type.max_file_size          ERR_FILE_TOO_LARGE

  KYC-004       Valid format              File extension in allowed_formats             ERR_INVALID_FORMAT

  KYC-005       Reject reason required    If REJECTED, rejection_reason mandatory       ERR_REJECT_REASON

  KYC-006       Expiry check              Warn if expiry within 30 days                 WARN_EXPIRING_SOON

  KYC-007       Duplicate check           Same doc_type cannot have 2 PENDING records   ERR_DUPLICATE_DOC
  ------------- ------------------------- --------------------------------------------- --------------------

**3.3 CKYC Integration**

Integration with Central KYC Registry for regulatory compliance.

**3.3.1 CKYC Transaction Table (TXN_CKYC)**

  -------------------- -------------- ---------- ------------- ----------------------------------
  **Column**           **Type**       **Null**   **Default**   **Description**

  ckyc_txn_id          BIGSERIAL      NO         Auto          Primary Key

  entity_id            BIGINT         NO         \-            FK to MST_ENTITY

  transaction_type     VARCHAR(20)    NO         \-            SEARCH, DOWNLOAD, UPLOAD, UPDATE

  ckyc_number          VARCHAR(20)    YES        \-            CKYC identifier

  request_timestamp    TIMESTAMPTZ    NO         \-            API request time

  response_timestamp   TIMESTAMPTZ    YES        \-            API response time

  request_payload      JSONB          YES        \-            Request sent to CKYC

  response_payload     JSONB          YES        \-            Response from CKYC

  status               VARCHAR(20)    NO         \-            SUCCESS, FAILED, PENDING

  error_code           VARCHAR(20)    YES        \-            Error code if failed

  error_message        VARCHAR(500)   YES        \-            Error description

  \+ Audit Columns                                             Standard audit columns
  -------------------- -------------- ---------- ------------- ----------------------------------

**3.3.2 CKYC Integration Flow**

**Step 1: Search CKYC** - Check if entity already exists in CKYC

POST /ckyc/search { pan: \'XXXXX1234X\' }

**Step 2: If Found - Download** - Download existing KYC data

GET /ckyc/download/{ckyc_number}

- Map downloaded data to entity KYC records

- Mark verification_method = \'CKYC\'

**Step 3: If Not Found - Upload** - Register entity in CKYC

POST /ckyc/upload { entity_data, documents\[\] }

- Store returned ckyc_number in entity master

**Step 4: Periodic Update** - Update CKYC when entity data changes

PUT /ckyc/update/{ckyc_number} { updated_fields }

**4. Credit Rating Module**

Internal credit rating system with configurable risk parameters and scoring model.

**4.1 Risk Categories (MST_RISK_CATEGORY)**

High-level risk categories for credit assessment.

**4.1.1 Table Definition**

  ------------------ -------------- ---------- ------------- ----------------------------------
  **Column**         **Type**       **Null**   **Default**   **Description**

  category_id        BIGSERIAL      NO         Auto          Primary Key

  org_id             BIGINT         NO         \-            FK to MST_ORGANIZATION

  category_code      VARCHAR(20)    NO         \-            Unique code

  category_name      VARCHAR(100)   NO         \-            Category name

  description        VARCHAR(500)   YES        \-            Description

  weightage          NUMERIC(5,2)   NO         \-            Category weight in overall score

  display_order      INTEGER        NO         \-            Display sequence

  status             VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                           Standard audit columns
  ------------------ -------------- ---------- ------------- ----------------------------------

**4.1.2 Standard Risk Categories**

  ----------- --------------------- ----------------------------------------------------- -------------
  **Code**    **Category**          **Description**                                       **Weight**

  SPONSOR     Sponsor Risk          Promoter background, track record, integrity          25%

  PROJECT     Project Risk          Technical feasibility, implementation capability      30%

  FINANCIAL   Financial Risk        Financials, profitability, leverage, liquidity        30%

  INDUSTRY    Industry Risk         Sector outlook, competition, regulatory environment   10%

  SECURITY    Security/Collateral   Collateral coverage, quality, enforceability          5%
  ----------- --------------------- ----------------------------------------------------- -------------

**4.2 Risk Parameters (MST_RISK_PARAMETER)**

Individual risk parameters within each category with scoring criteria.

**4.2.1 Table Definition**

  ------------------ --------------- ---------- ------------- --------------------------------
  **Column**         **Type**        **Null**   **Default**   **Description**

  param_id           BIGSERIAL       NO         Auto          Primary Key

  category_id        BIGINT          NO         \-            FK to MST_RISK_CATEGORY

  param_code         VARCHAR(30)     NO         \-            Unique parameter code

  param_name         VARCHAR(200)    NO         \-            Parameter name

  description        VARCHAR(500)    YES        \-            Detailed description

  data_type          VARCHAR(20)     NO         \-            NUMERIC, TEXT, BOOLEAN, SELECT

  input_type         VARCHAR(20)     NO         \-            MANUAL, COMPUTED, EXTERNAL

  unit_of_measure    VARCHAR(20)     YES        \-            %, Years, Ratio, etc.

  min_value          NUMERIC(18,4)   YES        \-            Minimum allowed value

  max_value          NUMERIC(18,4)   YES        \-            Maximum allowed value

  weightage          NUMERIC(5,2)    NO         \-            Weight within category

  scoring_logic      JSONB           YES        \-            Scoring rules (see below)

  is_mandatory       BOOLEAN         NO         TRUE          Required for rating

  help_text          TEXT            YES        \-            User guidance

  display_order      INTEGER         NO         \-            Display sequence

  status             VARCHAR(20)     NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                            Standard audit columns
  ------------------ --------------- ---------- ------------- --------------------------------

**4.2.2 Scoring Logic Structure (JSON)**

{

\"type\": \"range\", // range, threshold, lookup

\"rules\": \[

{ \"min\": null, \"max\": 1.0, \"score\": 1, \"label\": \"Poor\" },

{ \"min\": 1.0, \"max\": 1.5, \"score\": 2, \"label\": \"Below Average\" },

{ \"min\": 1.5, \"max\": 2.0, \"score\": 3, \"label\": \"Average\" },

{ \"min\": 2.0, \"max\": 2.5, \"score\": 4, \"label\": \"Good\" },

{ \"min\": 2.5, \"max\": null, \"score\": 5, \"label\": \"Excellent\" }

\],

\"max_score\": 5

}

**4.2.3 Sample Risk Parameters**

  -------------- ----------------------------- --------------- ------------ ---------------
  **Category**   **Parameter**                 **Data Type**   **Weight**   **Max Score**

  SPONSOR        Promoter Experience (Years)   NUMERIC         30%          5

  SPONSOR        Track Record with SMFC        SELECT          25%          5

  SPONSOR        Group Net Worth               NUMERIC         25%          5

  SPONSOR        Regulatory/Legal Issues       BOOLEAN         20%          5

  FINANCIAL      Debt Equity Ratio             NUMERIC         25%          5

  FINANCIAL      Interest Coverage Ratio       NUMERIC         25%          5

  FINANCIAL      Current Ratio                 NUMERIC         20%          5

  FINANCIAL      PAT Margin %                  NUMERIC         15%          5

  FINANCIAL      Revenue CAGR (3Y)             NUMERIC         15%          5

  PROJECT        Project IRR %                 NUMERIC         30%          5

  PROJECT        Statutory Approvals           SELECT          25%          5

  PROJECT        Technology Risk               SELECT          20%          5

  PROJECT        Implementation Timeline       SELECT          25%          5
  -------------- ----------------------------- --------------- ------------ ---------------

**4.3 Rating Matrix (MST_RATING_MATRIX)**

Maps aggregate scores to rating grades.

**4.3.1 Table Definition**

  -------------------- -------------- ---------- ------------- --------------------------------------
  **Column**           **Type**       **Null**   **Default**   **Description**

  matrix_id            BIGSERIAL      NO         Auto          Primary Key

  org_id               BIGINT         NO         \-            FK to MST_ORGANIZATION

  rating_grade         VARCHAR(10)    NO         \-            Rating grade (AAA, AA, A, BBB, etc.)

  rating_name          VARCHAR(50)    NO         \-            Grade description

  min_score            NUMERIC(5,2)   NO         \-            Minimum score for this grade

  max_score            NUMERIC(5,2)   NO         \-            Maximum score for this grade

  risk_level           VARCHAR(20)    NO         \-            LOW, MEDIUM, HIGH, VERY_HIGH

  color_code           VARCHAR(7)     YES        \-            Display color (#00FF00)

  pricing_spread_bps   INTEGER        YES        \-            Suggested spread over base rate

  provisioning_pct     NUMERIC(5,2)   YES        \-            Standard provisioning %

  approval_authority   VARCHAR(100)   YES        \-            Required approval level

  status               VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                             Standard audit columns
  -------------------- -------------- ---------- ------------- --------------------------------------

**4.3.2 Standard Rating Matrix**

  ------------ ----------------- ---------------- ------------------ ------------------
  **Grade**    **Score Range**   **Risk Level**   **Spread (bps)**   **Approval**

  AAA          4.50 - 5.00       LOW              50                 Manager

  AA+          4.25 - 4.49       LOW              75                 Manager

  AA           4.00 - 4.24       LOW              100                Sr. Manager

  AA-          3.75 - 3.99       MEDIUM           125                Sr. Manager

  A+           3.50 - 3.74       MEDIUM           150                AGM

  A            3.25 - 3.49       MEDIUM           175                AGM

  A-           3.00 - 3.24       MEDIUM           200                GM

  BBB+         2.75 - 2.99       HIGH             250                GM

  BBB          2.50 - 2.74       HIGH             300                ED

  BBB-         2.25 - 2.49       HIGH             350                CMD

  Below BBB-   \< 2.25           VERY_HIGH        \-                 Not Eligible
  ------------ ----------------- ---------------- ------------------ ------------------

**4.4 Entity Rating (TXN_ENTITY_RATING)**

Stores credit rating assessments for entities with full history.

**4.4.1 Table Definition**

  ---------------------- -------------- ---------- ------------- ---------------------------------------------
  **Column**             **Type**       **Null**   **Default**   **Description**

  rating_id              BIGSERIAL      NO         Auto          Primary Key

  entity_id              BIGINT         NO         \-            FK to MST_ENTITY

  rating_type            VARCHAR(20)    NO         \-            INITIAL, REVIEW, REVISION, ANNUAL

  rating_date            DATE           NO         \-            Assessment date

  valid_from             DATE           NO         \-            Rating effective from

  valid_to               DATE           YES        \-            Rating valid until

  assessed_by            BIGINT         NO         \-            FK to MST_USER

  category_scores        JSONB          NO         \-            Category-wise scores

  parameter_scores       JSONB          NO         \-            Parameter-wise scores & inputs

  total_score            NUMERIC(5,2)   NO         \-            Weighted average score

  rating_grade           VARCHAR(10)    NO         \-            Final rating grade

  risk_level             VARCHAR(20)    NO         \-            LOW, MEDIUM, HIGH, VERY_HIGH

  rating_remarks         TEXT           YES        \-            Assessment remarks

  strengths              TEXT           YES        \-            Key strengths identified

  weaknesses             TEXT           YES        \-            Key weaknesses/concerns

  recommendation         TEXT           YES        \-            Analyst recommendation

  external_rating        VARCHAR(20)    YES        \-            External rating if available

  external_agency        VARCHAR(50)    YES        \-            Rating agency

  external_rating_date   DATE           YES        \-            External rating date

  status                 VARCHAR(20)    NO         DRAFT         DRAFT, PENDING_APPROVAL, APPROVED, REJECTED

  approved_by            BIGINT         YES        \-            FK to MST_USER

  approved_at            TIMESTAMPTZ    YES        \-            Approval timestamp

  rejection_reason       VARCHAR(500)   YES        \-            If rejected

  is_current             BOOLEAN        NO         FALSE         Current active rating

  superseded_by          BIGINT         YES        \-            FK to newer rating

  \+ Audit Columns                                               Standard audit columns
  ---------------------- -------------- ---------- ------------- ---------------------------------------------

**4.4.2 Category Scores JSON Structure**

{

\"SPONSOR\": { \"weight\": 0.25, \"raw_score\": 3.8, \"weighted_score\": 0.95 },

\"PROJECT\": { \"weight\": 0.30, \"raw_score\": 4.2, \"weighted_score\": 1.26 },

\"FINANCIAL\": { \"weight\": 0.30, \"raw_score\": 3.5, \"weighted_score\": 1.05 },

\"INDUSTRY\": { \"weight\": 0.10, \"raw_score\": 4.0, \"weighted_score\": 0.40 },

\"SECURITY\": { \"weight\": 0.05, \"raw_score\": 4.5, \"weighted_score\": 0.225 }

}

// Total = 0.95 + 1.26 + 1.05 + 0.40 + 0.225 = 3.885 → Rating: A-

**4.4.3 Parameter Scores JSON Structure**

{

\"SPONSOR_EXP\": {

\"input_value\": 12,

\"input_label\": \"12 Years\",

\"score\": 4,

\"score_label\": \"Good\",

\"weight\": 0.30,

\"weighted_score\": 1.2

},

\"DEBT_EQUITY\": {

\"input_value\": 1.8,

\"input_label\": \"1.8:1\",

\"score\": 3,

\"score_label\": \"Average\",

\"weight\": 0.25,

\"weighted_score\": 0.75

}

// \... more parameters

}

**4.5 Rating Workflow (TXN_RATING_WORKFLOW)**

Approval workflow for credit ratings.

**4.5.1 Table Definition**

  ------------------ -------------- ---------- ------------- -----------------------------------------
  **Column**         **Type**       **Null**   **Default**   **Description**

  workflow_id        BIGSERIAL      NO         Auto          Primary Key

  rating_id          BIGINT         NO         \-            FK to TXN_ENTITY_RATING

  approval_level     INTEGER        NO         \-            Workflow level (1, 2, 3)

  approver_user_id   BIGINT         NO         \-            FK to MST_USER

  action             VARCHAR(20)    NO         \-            SUBMITTED, APPROVED, REJECTED, RETURNED

  action_date        TIMESTAMPTZ    NO         \-            Action timestamp

  comments           VARCHAR(500)   YES        \-            Approver comments

  from_status        VARCHAR(20)    NO         \-            Status before action

  to_status          VARCHAR(20)    NO         \-            Status after action

  \+ Audit Columns                                           Standard audit columns
  ------------------ -------------- ---------- ------------- -----------------------------------------

**4.5.2 Rating Approval Matrix**

  --------------------- -------------------------- ---------------- ------------------
  **Risk Level**        **Level 1**                **Level 2**      **Level 3**

  LOW (AAA to AA)       Credit Analyst             Credit Manager   \-

  MEDIUM (AA- to A-)    Credit Analyst             Credit Manager   HOD Credit

  HIGH (BBB+ to BBB-)   Credit Analyst             Credit Manager   Credit Committee

  VERY_HIGH             Not Eligible for Lending   \-               \-
  --------------------- -------------------------- ---------------- ------------------

**5. Loan Product Masters**

Configuration of loan products, interest rates, fees, and documentation requirements.

**5.1 Loan Products/Schemes (MST_LOAN_PRODUCT)**

Defines loan products offered by SMFC with terms and conditions.

**5.1.1 Table Definition**

  -------------------------- --------------- ---------- ------------- ----------------------------------------------------------
  **Column**                 **Type**        **Null**   **Default**   **Description**

  product_id                 BIGSERIAL       NO         Auto          Primary Key

  org_id                     BIGINT          NO         \-            FK to MST_ORGANIZATION

  product_code               VARCHAR(20)     NO         \-            Unique product code

  product_name               VARCHAR(200)    NO         \-            Product name

  product_category           VARCHAR(50)     NO         \-            TERM_LOAN, PROJECT_FINANCE, WORKING_CAPITAL, BRIDGE_LOAN

  description                TEXT            YES        \-            Detailed description

  min_amount                 NUMERIC(18,2)   NO         \-            Minimum loan amount

  max_amount                 NUMERIC(18,2)   YES        \-            Maximum loan amount

  min_tenure_months          INTEGER         NO         \-            Minimum tenure in months

  max_tenure_months          INTEGER         NO         \-            Maximum tenure in months

  interest_type              VARCHAR(20)     NO         \-            FIXED, FLOATING

  base_rate_id               BIGINT          YES        \-            FK to base rate (if floating)

  default_spread_bps         INTEGER         YES        \-            Default spread over base rate

  min_spread_bps             INTEGER         YES        \-            Minimum spread

  max_spread_bps             INTEGER         YES        \-            Maximum spread

  fixed_rate                 NUMERIC(5,2)    YES        \-            If interest_type=FIXED

  repayment_frequency        VARCHAR(20)     NO         \-            MONTHLY, QUARTERLY, HALF_YEARLY, YEARLY, BULLET

  moratorium_months          INTEGER         NO         0             Default moratorium period

  max_moratorium_months      INTEGER         YES        \-            Maximum allowed moratorium

  prepayment_allowed         BOOLEAN         NO         TRUE          Allow prepayment

  prepayment_penalty_pct     NUMERIC(5,2)    YES        \-            Prepayment penalty %

  prepayment_lockin_months   INTEGER         YES        \-            Lock-in before prepayment

  collateral_required        BOOLEAN         NO         TRUE          Collateral mandatory

  min_collateral_coverage    NUMERIC(5,2)    YES        \-            Minimum collateral coverage

  eligible_sectors           JSONB           YES        \-            Allowed industry sectors

  eligible_entity_types      JSONB           YES        \-            Allowed entity types

  min_rating_grade           VARCHAR(10)     YES        \-            Minimum required rating

  gl_account_principal       BIGINT          YES        \-            FK to MST_COA (loan asset)

  gl_account_interest        BIGINT          YES        \-            FK to MST_COA (interest income)

  gl_account_fee             BIGINT          YES        \-            FK to MST_COA (fee income)

  effective_from             DATE            NO         \-            Product active from

  effective_to               DATE            YES        \-            Product deactivation date

  status                     VARCHAR(20)     NO         ACTIVE        ACTIVE, INACTIVE, DISCONTINUED

  \+ Audit Columns                                                    Standard audit columns
  -------------------------- --------------- ---------- ------------- ----------------------------------------------------------

**5.1.2 Sample Loan Products**

  ---------- -------------------------------- ----------------- ---------------------- -------------
  **Code**   **Product**                      **Category**      **Amount Range**       **Tenure**

  PTL        Port Term Loan                   TERM_LOAN         ₹100 Cr - ₹5,000 Cr    5-20 years

  MTL        Maritime Term Loan               TERM_LOAN         ₹50 Cr - ₹2,000 Cr     5-15 years

  IPF        Infrastructure Project Finance   PROJECT_FINANCE   ₹500 Cr - ₹10,000 Cr   10-25 years

  WCL        Working Capital Loan             WORKING_CAPITAL   ₹10 Cr - ₹500 Cr       1-3 years

  BL         Bridge Loan                      BRIDGE_LOAN       ₹25 Cr - ₹1,000 Cr     6-24 months
  ---------- -------------------------------- ----------------- ---------------------- -------------

**5.2 Interest Rate Master (MST_INTEREST_RATE)**

Base rates and their history for floating rate loans.

**5.2.1 Table Definition**

  ------------------ -------------- ---------- ------------- ---------------------------------------
  **Column**         **Type**       **Null**   **Default**   **Description**

  rate_id            BIGSERIAL      NO         Auto          Primary Key

  org_id             BIGINT         NO         \-            FK to MST_ORGANIZATION

  rate_code          VARCHAR(20)    NO         \-            Rate identifier (SMFC_BR, MCLR, REPO)

  rate_name          VARCHAR(100)   NO         \-            Rate name

  rate_type          VARCHAR(30)    NO         \-            BASE_RATE, BENCHMARK, SPREAD

  effective_date     DATE           NO         \-            Rate effective from

  rate_value         NUMERIC(5,2)   NO         \-            Rate value (%)

  previous_rate      NUMERIC(5,2)   YES        \-            Previous rate for tracking

  change_reason      VARCHAR(200)   YES        \-            Reason for rate change

  approved_by        BIGINT         YES        \-            FK to MST_USER

  is_current         BOOLEAN        NO         FALSE         Current active rate

  \+ Audit Columns                                           Standard audit columns
  ------------------ -------------- ---------- ------------- ---------------------------------------

**5.2.2 Rate Calculation Example**

Loan Interest Rate = Base Rate + Spread

Base Rate (SMFC_BR): 9.50%

Risk-based Spread (A- rating): +2.00%

Product Spread: +0.50%

\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--

Final Rate: 12.00%

**5.3 Fee Master (MST_FEE)**

Loan-related fees and charges configuration.

**5.3.1 Table Definition**

  ------------------ --------------- ---------- ------------- --------------------------------------------------
  **Column**         **Type**        **Null**   **Default**   **Description**

  fee_id             BIGSERIAL       NO         Auto          Primary Key

  org_id             BIGINT          NO         \-            FK to MST_ORGANIZATION

  fee_code           VARCHAR(20)     NO         \-            Unique fee code

  fee_name           VARCHAR(100)    NO         \-            Fee name

  fee_type           VARCHAR(30)     NO         \-            PROCESSING, COMMITMENT, PREPAYMENT, LEGAL, OTHER

  calculation_type   VARCHAR(20)     NO         \-            PERCENTAGE, FLAT, SLAB

  percentage_value   NUMERIC(5,2)    YES        \-            If percentage-based

  flat_amount        NUMERIC(18,2)   YES        \-            If flat amount

  slab_config        JSONB           YES        \-            Slab-based configuration

  min_amount         NUMERIC(18,2)   YES        \-            Minimum fee amount

  max_amount         NUMERIC(18,2)   YES        \-            Maximum fee amount

  gst_applicable     BOOLEAN         NO         TRUE          GST applicable

  gst_rate           NUMERIC(5,2)    YES        18.00         GST rate %

  collection_stage   VARCHAR(30)     NO         \-            APPLICATION, SANCTION, DISBURSEMENT

  refundable         BOOLEAN         NO         FALSE         Is refundable

  gl_account_id      BIGINT          YES        \-            FK to MST_COA

  status             VARCHAR(20)     NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                            Standard audit columns
  ------------------ --------------- ---------- ------------- --------------------------------------------------

**5.3.2 Standard Fee Types**

  ------------- ----------------------- ------------ --------------------- ---------------
  **Code**      **Fee Name**            **Type**     **Rate/Amount**       **Stage**

  PROC_FEE      Processing Fee          PERCENTAGE   0.10% - 0.50%         APPLICATION

  UPFRONT_FEE   Upfront Fee             PERCENTAGE   0.25% - 1.00%         SANCTION

  COMMIT_FEE    Commitment Fee          PERCENTAGE   0.25% on undrawn      DISBURSEMENT

  PREPAY_CHG    Prepayment Charge       PERCENTAGE   1.00% - 2.00%         PREPAYMENT

  DOC_CHG       Documentation Charges   FLAT         ₹25,000 - ₹1,00,000   SANCTION

  LEGAL_FEE     Legal Fee               ACTUAL       As per actuals        SANCTION

  VALUATION     Valuation Fee           ACTUAL       As per actuals        SANCTION
  ------------- ----------------------- ------------ --------------------- ---------------

**5.4 Document Checklist (MST_DOC_CHECKLIST)**

Product-wise document requirements for loan processing.

**5.4.1 Table Definition**

  ---------------------- -------------- ---------- ------------- -------------------------------------------------------
  **Column**             **Type**       **Null**   **Default**   **Description**

  checklist_id           BIGSERIAL      NO         Auto          Primary Key

  product_id             BIGINT         NO         \-            FK to MST_LOAN_PRODUCT

  doc_code               VARCHAR(30)    NO         \-            Document code

  doc_name               VARCHAR(200)   NO         \-            Document name

  doc_category           VARCHAR(30)    NO         \-            FINANCIAL, LEGAL, PROJECT, SECURITY, OTHER

  stage                  VARCHAR(30)    NO         \-            APPLICATION, APPRAISAL, SANCTION, PRE_DISB, POST_DISB

  is_mandatory           BOOLEAN        NO         TRUE          Mandatory document

  mandatory_for_stages   JSONB          YES        \-            Stage-specific mandatory

  description            VARCHAR(500)   YES        \-            Document description

  sample_format_path     VARCHAR(500)   YES        \-            Sample/template path

  display_order          INTEGER        NO         \-            Display sequence

  status                 VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                               Standard audit columns
  ---------------------- -------------- ---------- ------------- -------------------------------------------------------

**5.4.2 Sample Document Checklist**

  -------------- ------------------------------------ ------------- ----------------
  **Category**   **Document**                         **Stage**     **Mandatory**

  FINANCIAL      Audited Financials (3 years)         APPLICATION   Yes

  FINANCIAL      Projected Financials (Loan tenure)   APPRAISAL     Yes

  FINANCIAL      CMA Data                             APPRAISAL     Yes

  PROJECT        Detailed Project Report (DPR)        APPLICATION   Yes

  PROJECT        Techno-Economic Viability Report     APPRAISAL     Yes

  PROJECT        Environmental Clearance              APPRAISAL     Yes

  LEGAL          Board Resolution for Borrowing       SANCTION      Yes

  LEGAL          Shareholder Agreement                SANCTION      Conditional

  SECURITY       Title Documents                      PRE_DISB      Yes

  SECURITY       Valuation Report                     PRE_DISB      Yes

  SECURITY       Insurance Policy                     PRE_DISB      Yes
  -------------- ------------------------------------ ------------- ----------------

**6. Security/Collateral Masters**

Configuration for collateral types and valuation.

**6.1 Security Types (MST_SECURITY_TYPE)**

  ----------------------- -------------- ---------- ------------- ---------------------------------
  **Column**              **Type**       **Null**   **Default**   **Description**

  security_type_id        BIGSERIAL      NO         Auto          Primary Key

  org_id                  BIGINT         NO         \-            FK to MST_ORGANIZATION

  type_code               VARCHAR(20)    NO         \-            Unique code

  type_name               VARCHAR(100)   NO         \-            Security type name

  category                VARCHAR(30)    NO         \-            PRIMARY, COLLATERAL, GUARANTEE

  nature                  VARCHAR(30)    NO         \-            TANGIBLE, INTANGIBLE, FINANCIAL

  description             TEXT           YES        \-            Description

  default_margin_pct      NUMERIC(5,2)   YES        \-            Default haircut/margin

  valuation_frequency     VARCHAR(20)    YES        \-            ANNUAL, HALF_YEARLY, QUARTERLY

  registration_required   BOOLEAN        NO         FALSE         Charge registration needed

  registration_type       VARCHAR(30)    YES        \-            ROC, CERSAI, BOTH

  insurance_required      BOOLEAN        NO         FALSE         Insurance mandatory

  status                  VARCHAR(20)    NO         ACTIVE        ACTIVE, INACTIVE

  \+ Audit Columns                                                Standard audit columns
  ----------------------- -------------- ---------- ------------- ---------------------------------

**6.1.1 Standard Security Types**

  ------------ --------------------------------- -------------- ------------ ------------------
  **Code**     **Type**                          **Category**   **Margin**   **Registration**

  HYP_FA       Hypothecation of Fixed Assets     PRIMARY        25%          CERSAI

  HYP_CA       Hypothecation of Current Assets   PRIMARY        25%          CERSAI

  MORT_LAND    Mortgage of Land                  COLLATERAL     30%          BOTH

  MORT_BLDG    Mortgage of Building              COLLATERAL     30%          BOTH

  PLEDGE_FD    Pledge of Fixed Deposits          COLLATERAL     10%          No

  PLEDGE_SEC   Pledge of Securities              COLLATERAL     50%          No

  CORP_GUAR    Corporate Guarantee               GUARANTEE      N/A          No

  PERS_GUAR    Personal Guarantee                GUARANTEE      N/A          No

  BG           Bank Guarantee                    GUARANTEE      0%           No

  ESCROW       Escrow of Receivables             PRIMARY        10%          No
  ------------ --------------------------------- -------------- ------------ ------------------

**7. Business Rules & Validations**

Complete business rules for lending masters and KYC/Rating modules.

**7.1 Entity Onboarding Rules**

  ------------- --------------------------- ----------------------------- --------------------- ------------------------
  **Rule ID**   **Rule**                    **Condition**                 **Action**            **Error Code**

  EONT-001      Complete entity profile     All mandatory fields filled   Block if incomplete   ERR_PROFILE_INCOMPLETE

  EONT-002      At least one contact        contact_count \>= 1           Block creation        ERR_NO_CONTACT

  EONT-003      At least one address        address_count \>= 1           Block creation        ERR_NO_ADDRESS

  EONT-004      At least one bank account   bank_account_count \>= 1      Block creation        ERR_NO_BANK

  EONT-005      PAN verification            PAN validated via API         Block if invalid      ERR_PAN_INVALID

  EONT-006      CIN verification            CIN validated via MCA         Block if invalid      ERR_CIN_INVALID

  EONT-007      Director KYC                All directors have KYC        Warn if incomplete    WARN_DIR_KYC
  ------------- --------------------------- ----------------------------- --------------------- ------------------------

**7.2 KYC Completion Rules**

  ------------- ---------------------- ---------------------------------- -------------------- ---------------------
  **Rule ID**   **Rule**               **Condition**                      **Action**           **Error Code**

  KYC-101       All mandatory docs     All mandatory KYC docs VERIFIED    Block loan app       ERR_KYC_MANDATORY

  KYC-102       No expired docs        All docs within validity           Block loan app       ERR_KYC_EXPIRED

  KYC-103       CKYC registration      Entity registered in CKYC          Warn if not done     WARN_CKYC_PENDING

  KYC-104       Address verification   At least one address verified      Block loan app       ERR_ADDR_UNVERIFIED

  KYC-105       Bank verification      Primary bank penny-drop verified   Block disbursement   ERR_BANK_UNVERIFIED

  KYC-106       Expiry notification    Doc expires in \< 30 days          Send alert           NOTIFY_EXPIRING
  ------------- ---------------------- ---------------------------------- -------------------- ---------------------

**7.3 Credit Rating Rules**

  ------------- ------------------------- --------------------------------------- ----------------------- ----------------------
  **Rule ID**   **Rule**                  **Condition**                           **Action**              **Error Code**

  RAT-001       All parameters scored     All mandatory params have score         Block submission        ERR_PARAM_MISSING

  RAT-002       Score in valid range      0 \<= score \<= max_score               Block save              ERR_INVALID_SCORE

  RAT-003       Remarks for low score     If param_score \< 2, remarks required   Block save              ERR_REMARKS_REQD

  RAT-004       Rating validity           Rating valid for max 1 year             Auto-mark for review    NOTIFY_REVIEW_DUE

  RAT-005       Minimum rating for loan   rating_grade \>= product.min_rating     Block application       ERR_RATING_BELOW_MIN

  RAT-006       Annual review             Rating \> 1 year old for active loan    Trigger review          NOTIFY_ANNUAL_REVIEW

  RAT-007       Downgrade trigger         New rating \< current by 2+ notches     Escalate to committee   ALERT_DOWNGRADE
  ------------- ------------------------- --------------------------------------- ----------------------- ----------------------

**8. KYC & Rating Flows**

Key business flows for KYC verification and credit rating.

**8.1 Entity Onboarding Flow**

**TRIGGER: New borrower registration initiated**

**Step 1: Create Entity** - Capture basic entity information

- Collect: Legal name, PAN, entity type, incorporation details

- Generate unique entity_code

- Validate PAN format and uniqueness

**Step 2: Add Contacts** - Add key contact persons

- At least one contact required

- Mark one as primary contact

- For directors: capture DIN, validate via MCA

**Step 3: Add Addresses** - Capture entity addresses

- Registered address mandatory for corporates

- Validate PIN code

- Optional: Geo-tag for verification

**Step 4: Add Bank Accounts** - Capture banking details

- At least one account required

- Validate IFSC via RBI database

- Initiate penny-drop verification

**Step 5: KYC Document Upload** - Collect KYC documents

- Display checklist based on entity type

- Upload and verify mandatory documents

- OCR extraction where applicable

**Step 6: CKYC Integration** - Register/download from CKYC

- Search existing CKYC record

- If found: download and map data

- If not found: upload entity to CKYC

**Step 7: Mark KYC Complete** - Finalize KYC status

UPDATE mst_entity SET kyc_status = \'COMPLETE\' WHERE entity_id = :id

- Enable entity for loan applications

**8.2 Credit Rating Flow**

**TRIGGER: New rating initiated for entity**

**Step 1: Initiate Rating** - Create rating assessment record

INSERT INTO txn_entity_rating (entity_id, rating_type, status=\'DRAFT\')

- Load applicable risk parameters based on entity type

**Step 2: Input Parameter Values** - Capture risk parameter inputs

- For NUMERIC: Enter value, system calculates score

- For SELECT: Choose from options, system maps to score

- For COMPUTED: System fetches from financials/external data

**Step 3: Calculate Scores** - Compute weighted scores

FOR each parameter:

raw_score = apply_scoring_logic(input_value, scoring_rules)

weighted_score = raw_score \* param_weight

FOR each category:

category_score = SUM(param_weighted_scores) / SUM(param_weights)

category_weighted = category_score \* category_weight

total_score = SUM(category_weighted_scores)

**Step 4: Determine Grade** - Map score to rating grade

SELECT rating_grade, risk_level FROM mst_rating_matrix

WHERE :total_score BETWEEN min_score AND max_score

**Step 5: Add Qualitative Assessment** - Analyst inputs

- Document strengths and weaknesses

- Add recommendation remarks

- Flag any override requests

**Step 6: Submit for Approval** - Route to workflow

- Determine approval matrix based on risk_level

- Submit to Level 1 approver

- Send notification with SLA

**Step 7: Approval Process** - Multi-level approval

- Each level: APPROVE / REJECT / RETURN

- If approved by all levels: Mark rating APPROVED

- Set is_current = TRUE, supersede previous rating

**Step 8: Update Entity** - Reflect approved rating

UPDATE mst_entity SET

internal_rating = :grade,

internal_rating_date = CURRENT_DATE,

risk_category = :risk_level

WHERE entity_id = :id

*\-\-- End of Phase 2 Part 1 \-\--*

Part 2 covers: Loan Application, Appraisal, Sanction, and Pre-Disbursement
