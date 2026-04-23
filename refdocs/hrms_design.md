# HRMS & Payroll Module - Detailed Design Document

## Executive Summary

This document outlines the complete design for the Human Resource Management System (HRMS) and Payroll module. The module covers the entire employee lifecycle from recruitment to separation, including leave management, attendance, payroll processing, and statutory compliance.

---

## Module Overview

### Scope

| Area | Coverage |
|------|----------|
| Employee Management | Master data, documents, lifecycle events |
| Organization Structure | Reporting hierarchy, cost centers |
| Leave Management | Types, quotas, applications, encashment |
| Attendance | Shifts, punch-in/out, regularization |
| Payroll | Salary structure, processing, payslips |
| Statutory Compliance | PF, ESI, PT, TDS, LWF |
| Self-Service | Employee portal, requests, approvals |

### Integration Points

- **Finance Module**: Salary posting to GL, cost center allocation
- **Workflow Engine**: Approvals for leave, attendance, expense claims
- **TDS Module**: Salary TDS computation, Form 16 generation
- **Bank Integration**: Salary disbursement via NEFT/RTGS

---

## Database Design

### Entity Relationship Overview

```
Organization (existing)
    └── Department (existing)
        └── Designation (existing)
            └── Employee
                ├── EmployeeDocument
                ├── EmployeeFamily
                ├── EmployeeBankAccount
                ├── EmployeeEducation
                ├── EmployeeExperience
                ├── EmployeeStatutory (PF, ESI, PT)
                ├── EmployeeSalaryStructure
                │   └── EmployeeSalaryComponent
                ├── LeaveBalance
                ├── LeaveApplication
                ├── Attendance
                └── EmployeeLifecycleEvent
```

---

## Table Definitions

### 1. Employee Master (`hris_employee`)

Core employee information.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| organization_id | UUID | FK to organization |
| employee_code | VARCHAR(20) | Unique per org (e.g., EMP001) |
| salutation | ENUM | Mr, Ms, Mrs, Dr |
| first_name | VARCHAR(100) | |
| middle_name | VARCHAR(100) | |
| last_name | VARCHAR(100) | |
| display_name | VARCHAR(200) | Computed or override |
| gender | ENUM | MALE, FEMALE, OTHER |
| date_of_birth | DATE | |
| blood_group | VARCHAR(5) | |
| marital_status | ENUM | SINGLE, MARRIED, DIVORCED, WIDOWED |
| nationality | VARCHAR(50) | |
| personal_email | VARCHAR(255) | |
| personal_mobile | VARCHAR(20) | |
| official_email | VARCHAR(255) | |
| official_mobile | VARCHAR(20) | |
| emergency_contact_name | VARCHAR(200) | |
| emergency_contact_phone | VARCHAR(20) | |
| emergency_contact_relation | VARCHAR(50) | |
| current_address | JSONB | {line1, line2, city, state, pincode, country} |
| permanent_address | JSONB | |
| is_address_same | BOOLEAN | |
| photo_url | VARCHAR(500) | |
| department_id | UUID | FK to department |
| designation_id | UUID | FK to designation |
| reporting_manager_id | UUID | FK to self |
| unit_id | UUID | FK to unit (location) |
| cost_center_id | UUID | FK to cost_center |
| date_of_joining | DATE | |
| confirmation_date | DATE | |
| probation_end_date | DATE | |
| date_of_leaving | DATE | Nullable |
| employment_type | ENUM | PERMANENT, CONTRACT, TRAINEE, INTERN, CONSULTANT |
| employment_status | ENUM | ACTIVE, PROBATION, NOTICE_PERIOD, RELIEVED, ABSCONDING, TERMINATED |
| notice_period_days | INTEGER | Default 30/60/90 |
| shift_id | UUID | FK to shift_master |
| weekly_off | VARCHAR(20) | e.g., "SAT,SUN" |
| is_payroll_active | BOOLEAN | Include in payroll run |
| payment_mode | ENUM | BANK_TRANSFER, CHEQUE, CASH |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |
| created_by | UUID | |
| updated_by | UUID | |
| is_active | BOOLEAN | Soft delete |

**Indexes:**
- UNIQUE(organization_id, employee_code)
- INDEX(department_id)
- INDEX(designation_id)
- INDEX(reporting_manager_id)
- INDEX(employment_status)

---

### 2. Employee Documents (`hris_employee_document`)

KYC and other documents.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| employee_id | UUID | FK to employee |
| document_type | ENUM | AADHAAR, PAN, PASSPORT, VOTER_ID, DRIVING_LICENSE, PHOTO, OFFER_LETTER, APPOINTMENT_LETTER, RELIEVING_LETTER, EXPERIENCE_CERTIFICATE, EDUCATION_CERTIFICATE, OTHER |
| document_number | VARCHAR(50) | |
| issue_date | DATE | |
| expiry_date | DATE | |
| issuing_authority | VARCHAR(200) | |
| file_url | VARCHAR(500) | S3/storage path |
| file_name | VARCHAR(255) | |
| file_size | INTEGER | In bytes |
| is_verified | BOOLEAN | HR verified |
| verified_by | UUID | |
| verified_at | TIMESTAMP | |
| remarks | TEXT | |
| is_active | BOOLEAN | |

**Indexes:**
- INDEX(employee_id)
- INDEX(document_type)
- UNIQUE(employee_id, document_type, document_number)

---

### 3. Employee Family (`hris_employee_family`)

Family and dependent details.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| employee_id | UUID | FK to employee |
| relation | ENUM | FATHER, MOTHER, SPOUSE, SON, DAUGHTER, BROTHER, SISTER, OTHER |
| name | VARCHAR(200) | |
| date_of_birth | DATE | |
| gender | ENUM | |
| occupation | VARCHAR(100) | |
| phone | VARCHAR(20) | |
| is_dependent | BOOLEAN | For tax/insurance |
| is_nominee | BOOLEAN | For PF/gratuity |
| nominee_percentage | DECIMAL(5,2) | If nominee |
| is_emergency_contact | BOOLEAN | |
| aadhaar_number | VARCHAR(12) | |
| is_active | BOOLEAN | |

---

### 4. Employee Bank Account (`hris_employee_bank_account`)

Salary disbursement accounts.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| employee_id | UUID | FK to employee |
| account_holder_name | VARCHAR(200) | |
| bank_name | VARCHAR(200) | |
| branch_name | VARCHAR(200) | |
| account_number | VARCHAR(30) | |
| ifsc_code | VARCHAR(11) | |
| account_type | ENUM | SAVINGS, CURRENT |
| is_primary | BOOLEAN | Default salary account |
| is_verified | BOOLEAN | |
| verified_by | UUID | |
| verified_at | TIMESTAMP | |
| is_active | BOOLEAN | |

---

### 5. Employee Education (`hris_employee_education`)

Educational qualifications.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| employee_id | UUID | FK |
| education_level | ENUM | SSC, HSC, DIPLOMA, GRADUATE, POST_GRADUATE, DOCTORATE, PROFESSIONAL |
| degree | VARCHAR(100) | e.g., B.Tech, MBA |
| specialization | VARCHAR(100) | e.g., Computer Science |
| institution | VARCHAR(200) | |
| university | VARCHAR(200) | |
| year_of_passing | INTEGER | |
| percentage_cgpa | DECIMAL(5,2) | |
| grade | VARCHAR(10) | |
| is_highest | BOOLEAN | |
| certificate_url | VARCHAR(500) | |
| is_active | BOOLEAN | |

---

### 6. Employee Experience (`hris_employee_experience`)

Previous employment history.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| employee_id | UUID | FK |
| company_name | VARCHAR(200) | |
| designation | VARCHAR(100) | |
| department | VARCHAR(100) | |
| from_date | DATE | |
| to_date | DATE | |
| last_ctc | DECIMAL(15,2) | |
| leaving_reason | TEXT | |
| reference_name | VARCHAR(200) | |
| reference_phone | VARCHAR(20) | |
| reference_email | VARCHAR(255) | |
| is_verified | BOOLEAN | BGV done |
| relieving_letter_url | VARCHAR(500) | |
| experience_letter_url | VARCHAR(500) | |
| is_active | BOOLEAN | |

---

### 7. Employee Statutory (`hris_employee_statutory`)

PF, ESI, PT registration details.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| employee_id | UUID | FK |
| pan_number | VARCHAR(10) | |
| aadhaar_number | VARCHAR(12) | |
| uan_number | VARCHAR(12) | Universal Account Number (PF) |
| pf_number | VARCHAR(22) | Regional PF number |
| esi_number | VARCHAR(17) | |
| pt_state | VARCHAR(50) | Professional Tax state |
| pt_number | VARCHAR(30) | |
| lwf_number | VARCHAR(30) | Labour Welfare Fund |
| gratuity_nominee | JSONB | {name, relation, percentage} |
| is_pf_applicable | BOOLEAN | |
| is_esi_applicable | BOOLEAN | Based on salary limit |
| is_pt_applicable | BOOLEAN | |
| is_lwf_applicable | BOOLEAN | |
| pf_contribution_type | ENUM | STANDARD, VOLUNTARY |
| voluntary_pf_percentage | DECIMAL(5,2) | If VPF opted |
| is_active | BOOLEAN | |

---

### 8. Shift Master (`hris_shift_master`)

Work shift definitions.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| organization_id | UUID | FK |
| shift_code | VARCHAR(20) | |
| shift_name | VARCHAR(100) | e.g., General, Night |
| start_time | TIME | e.g., 09:00 |
| end_time | TIME | e.g., 18:00 |
| break_duration_minutes | INTEGER | |
| working_hours | DECIMAL(4,2) | Computed |
| is_night_shift | BOOLEAN | |
| grace_period_minutes | INTEGER | Late arrival tolerance |
| half_day_hours | DECIMAL(4,2) | |
| overtime_applicable | BOOLEAN | |
| overtime_rate_multiplier | DECIMAL(3,2) | e.g., 1.5, 2.0 |
| is_active | BOOLEAN | |

---

### 9. Holiday Calendar (`hris_holiday_calendar`)

Organization holidays.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| organization_id | UUID | FK |
| calendar_year | INTEGER | e.g., 2026 |
| holiday_date | DATE | |
| holiday_name | VARCHAR(100) | |
| holiday_type | ENUM | NATIONAL, STATE, RESTRICTED, OPTIONAL |
| applicable_states | JSONB | If state-specific |
| is_optional | BOOLEAN | Can be exchanged |
| is_active | BOOLEAN | |

**Indexes:**
- UNIQUE(organization_id, calendar_year, holiday_date)

---

### 10. Leave Type Master (`hris_leave_type`)

Leave category definitions.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| organization_id | UUID | FK |
| leave_code | VARCHAR(10) | e.g., CL, EL, SL |
| leave_name | VARCHAR(100) | Casual Leave, Earned Leave |
| description | TEXT | |
| leave_category | ENUM | PAID, UNPAID, COMPENSATORY, RESTRICTED |
| annual_quota | DECIMAL(5,2) | Per year entitlement |
| accrual_frequency | ENUM | MONTHLY, QUARTERLY, YEARLY, UPFRONT |
| accrual_day | INTEGER | Day of month/quarter for accrual |
| carry_forward_allowed | BOOLEAN | |
| max_carry_forward | DECIMAL(5,2) | Limit |
| carry_forward_expiry_months | INTEGER | |
| encashment_allowed | BOOLEAN | |
| min_encashment_balance | DECIMAL(5,2) | Must retain |
| max_encashment_days | DECIMAL(5,2) | Per year |
| min_days_per_application | DECIMAL(3,1) | e.g., 0.5 |
| max_days_per_application | DECIMAL(5,2) | |
| max_consecutive_days | INTEGER | |
| advance_days_required | INTEGER | Apply X days before |
| can_be_clubbed | BOOLEAN | With other leave types |
| clubbing_restricted_with | JSONB | Leave type IDs |
| requires_document | BOOLEAN | e.g., Medical certificate |
| document_required_after_days | INTEGER | |
| applicable_gender | ENUM | ALL, MALE, FEMALE |
| applicable_marital_status | ENUM | ALL, MARRIED |
| applicable_employment_types | JSONB | ["PERMANENT", "CONTRACT"] |
| waiting_period_days | INTEGER | After joining |
| negative_balance_allowed | BOOLEAN | |
| max_negative_balance | DECIMAL(5,2) | |
| is_active | BOOLEAN | |

---

### 11. Leave Balance (`hris_leave_balance`)

Employee leave balances by type and year.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| employee_id | UUID | FK |
| leave_type_id | UUID | FK |
| calendar_year | INTEGER | |
| opening_balance | DECIMAL(5,2) | At year start |
| accrued | DECIMAL(5,2) | YTD accrued |
| availed | DECIMAL(5,2) | YTD taken |
| lapsed | DECIMAL(5,2) | Expired carry forward |
| encashed | DECIMAL(5,2) | |
| adjustment | DECIMAL(5,2) | Manual adjustments |
| closing_balance | DECIMAL(5,2) | Computed: opening + accrued - availed - lapsed - encashed + adjustment |
| carry_forward_expiry_date | DATE | |
| last_accrual_date | DATE | |
| is_active | BOOLEAN | |

**Indexes:**
- UNIQUE(employee_id, leave_type_id, calendar_year)

---

### 12. Leave Application (`hris_leave_application`)

Leave requests.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| organization_id | UUID | FK |
| employee_id | UUID | FK |
| leave_type_id | UUID | FK |
| application_date | DATE | |
| from_date | DATE | |
| to_date | DATE | |
| from_session | ENUM | FULL_DAY, FIRST_HALF, SECOND_HALF |
| to_session | ENUM | |
| total_days | DECIMAL(5,2) | Computed |
| reason | TEXT | |
| contact_during_leave | VARCHAR(20) | |
| handover_to_id | UUID | FK to employee |
| handover_notes | TEXT | |
| document_url | VARCHAR(500) | Medical cert etc |
| status | ENUM | DRAFT, PENDING, APPROVED, REJECTED, CANCELLED, WITHDRAWN |
| approved_by | UUID | |
| approved_at | TIMESTAMP | |
| rejection_reason | TEXT | |
| cancelled_reason | TEXT | |
| workflow_instance_id | UUID | FK to workflow |
| is_active | BOOLEAN | |

**Business Rules:**
- Validate against leave balance
- Check for overlapping leaves
- Apply advance days rule
- Validate consecutive days limit
- Check clubbing restrictions

---

### 13. Leave Encashment (`hris_leave_encashment`)

Leave encashment requests.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| employee_id | UUID | FK |
| leave_type_id | UUID | FK |
| calendar_year | INTEGER | |
| request_date | DATE | |
| days_requested | DECIMAL(5,2) | |
| days_approved | DECIMAL(5,2) | |
| per_day_amount | DECIMAL(12,2) | Basic / 30 or 26 |
| total_amount | DECIMAL(15,2) | |
| status | ENUM | PENDING, APPROVED, REJECTED, PAID |
| approved_by | UUID | |
| approved_at | TIMESTAMP | |
| payment_date | DATE | |
| payroll_id | UUID | FK if paid via payroll |
| voucher_id | UUID | FK if paid separately |
| remarks | TEXT | |
| is_active | BOOLEAN | |

---

### 14. Attendance (`hris_attendance`)

Daily attendance records.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| employee_id | UUID | FK |
| attendance_date | DATE | |
| shift_id | UUID | FK |
| scheduled_in | TIME | From shift |
| scheduled_out | TIME | |
| actual_in | TIME | Punch in |
| actual_out | TIME | Punch out |
| punch_in_source | ENUM | BIOMETRIC, WEB, MOBILE, MANUAL |
| punch_out_source | ENUM | |
| punch_in_location | JSONB | {lat, lng} for mobile |
| punch_out_location | JSONB | |
| total_hours | DECIMAL(5,2) | |
| overtime_hours | DECIMAL(5,2) | |
| late_by_minutes | INTEGER | |
| early_leaving_minutes | INTEGER | |
| status | ENUM | PRESENT, ABSENT, HALF_DAY, ON_LEAVE, HOLIDAY, WEEKLY_OFF, ON_DUTY, WORK_FROM_HOME |
| leave_application_id | UUID | If on leave |
| on_duty_request_id | UUID | If OD |
| regularization_status | ENUM | NONE, PENDING, APPROVED, REJECTED |
| regularization_reason | TEXT | |
| regularized_by | UUID | |
| regularized_at | TIMESTAMP | |
| remarks | TEXT | |
| is_active | BOOLEAN | |

**Indexes:**
- UNIQUE(employee_id, attendance_date)
- INDEX(attendance_date)
- INDEX(status)

---

### 15. Attendance Regularization (`hris_attendance_regularization`)

Requests to correct attendance.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| attendance_id | UUID | FK |
| employee_id | UUID | FK |
| request_date | DATE | |
| original_in | TIME | |
| original_out | TIME | |
| requested_in | TIME | |
| requested_out | TIME | |
| original_status | ENUM | |
| requested_status | ENUM | |
| reason | TEXT | |
| document_url | VARCHAR(500) | |
| status | ENUM | PENDING, APPROVED, REJECTED |
| approved_by | UUID | |
| approved_at | TIMESTAMP | |
| rejection_reason | TEXT | |
| workflow_instance_id | UUID | |
| is_active | BOOLEAN | |

---

### 16. On Duty Request (`hris_on_duty_request`)

Outdoor duty / work from home requests.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| employee_id | UUID | FK |
| request_type | ENUM | ON_DUTY, WORK_FROM_HOME |
| from_date | DATE | |
| to_date | DATE | |
| from_session | ENUM | |
| to_session | ENUM | |
| total_days | DECIMAL(5,2) | |
| purpose | TEXT | |
| location | VARCHAR(200) | For OD |
| status | ENUM | PENDING, APPROVED, REJECTED, CANCELLED |
| approved_by | UUID | |
| approved_at | TIMESTAMP | |
| rejection_reason | TEXT | |
| workflow_instance_id | UUID | |
| is_active | BOOLEAN | |

---

### 17. Salary Component Master (`hris_salary_component`)

Payroll components (earnings/deductions).

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| organization_id | UUID | FK |
| component_code | VARCHAR(20) | e.g., BASIC, HRA, PF |
| component_name | VARCHAR(100) | |
| component_type | ENUM | EARNING, DEDUCTION, REIMBURSEMENT, STATUTORY_DEDUCTION |
| calculation_type | ENUM | FIXED, PERCENTAGE, FORMULA |
| percentage_of | UUID | FK to another component |
| percentage_value | DECIMAL(5,2) | |
| formula | TEXT | Custom formula if any |
| is_taxable | BOOLEAN | |
| tax_exemption_limit | DECIMAL(15,2) | Annual limit |
| tax_exemption_section | VARCHAR(20) | e.g., 10(13A) |
| is_part_of_ctc | BOOLEAN | |
| is_part_of_gross | BOOLEAN | |
| is_part_of_net | BOOLEAN | |
| is_pro_rata | BOOLEAN | Calculate based on days |
| is_arrear_applicable | BOOLEAN | |
| show_in_payslip | BOOLEAN | |
| payslip_display_order | INTEGER | |
| gl_account_id | UUID | FK to account |
| is_employer_contribution | BOOLEAN | Like employer PF |
| is_active | BOOLEAN | |

**Standard Components:**
- BASIC - Basic Salary
- HRA - House Rent Allowance
- CONV - Conveyance Allowance
- MED - Medical Allowance
- SPL - Special Allowance
- LTA - Leave Travel Allowance
- BONUS - Performance Bonus
- PF_EE - PF Employee Contribution
- PF_ER - PF Employer Contribution
- ESI_EE - ESI Employee Contribution
- ESI_ER - ESI Employer Contribution
- PT - Professional Tax
- TDS - Tax Deducted at Source
- LWF_EE - LWF Employee
- LWF_ER - LWF Employer

---

### 18. Salary Structure (`hris_salary_structure`)

Employee salary configuration.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| employee_id | UUID | FK |
| effective_from | DATE | |
| effective_to | DATE | Null if current |
| ctc_annual | DECIMAL(15,2) | Cost to Company |
| ctc_monthly | DECIMAL(15,2) | |
| gross_annual | DECIMAL(15,2) | |
| gross_monthly | DECIMAL(15,2) | |
| net_monthly | DECIMAL(15,2) | Take home |
| revision_type | ENUM | JOINING, APPRAISAL, PROMOTION, CORRECTION |
| revision_reason | TEXT | |
| revision_percentage | DECIMAL(5,2) | |
| approved_by | UUID | |
| approved_at | TIMESTAMP | |
| is_current | BOOLEAN | |
| is_active | BOOLEAN | |

---

### 19. Salary Structure Component (`hris_salary_structure_component`)

Component values in structure.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| salary_structure_id | UUID | FK |
| component_id | UUID | FK to salary_component |
| monthly_amount | DECIMAL(15,2) | |
| annual_amount | DECIMAL(15,2) | |
| is_active | BOOLEAN | |

---

### 20. Payroll Period (`hris_payroll_period`)

Monthly payroll periods.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| organization_id | UUID | FK |
| period_name | VARCHAR(20) | e.g., Jan-2026 |
| period_month | INTEGER | 1-12 |
| period_year | INTEGER | |
| start_date | DATE | |
| end_date | DATE | |
| attendance_lock_date | DATE | |
| payroll_process_date | DATE | |
| payment_date | DATE | |
| status | ENUM | OPEN, ATTENDANCE_LOCKED, PROCESSING, PROCESSED, PAID, CLOSED |
| processed_by | UUID | |
| processed_at | TIMESTAMP | |
| total_employees | INTEGER | |
| total_gross | DECIMAL(18,2) | |
| total_deductions | DECIMAL(18,2) | |
| total_net | DECIMAL(18,2) | |
| voucher_id | UUID | FK to GL voucher |
| is_active | BOOLEAN | |

**Indexes:**
- UNIQUE(organization_id, period_year, period_month)

---

### 21. Payroll (`hris_payroll`)

Employee payroll for a period.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| payroll_period_id | UUID | FK |
| employee_id | UUID | FK |
| salary_structure_id | UUID | FK |
| total_days | INTEGER | Working days in month |
| present_days | DECIMAL(5,2) | |
| absent_days | DECIMAL(5,2) | |
| leave_days | DECIMAL(5,2) | Paid leaves |
| lwp_days | DECIMAL(5,2) | Loss of pay |
| holiday_days | INTEGER | |
| weekly_off_days | INTEGER | |
| overtime_hours | DECIMAL(6,2) | |
| gross_earnings | DECIMAL(15,2) | |
| total_deductions | DECIMAL(15,2) | |
| net_payable | DECIMAL(15,2) | |
| arrears_amount | DECIMAL(15,2) | |
| reimbursements | DECIMAL(15,2) | |
| employer_contributions | DECIMAL(15,2) | PF/ESI employer |
| tds_amount | DECIMAL(15,2) | |
| status | ENUM | DRAFT, PROCESSED, APPROVED, PAID, CANCELLED |
| payment_mode | ENUM | BANK_TRANSFER, CHEQUE, CASH |
| payment_date | DATE | |
| bank_reference | VARCHAR(50) | |
| remarks | TEXT | |
| is_active | BOOLEAN | |

---

### 22. Payroll Detail (`hris_payroll_detail`)

Line items of payroll.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| payroll_id | UUID | FK |
| component_id | UUID | FK |
| component_type | ENUM | EARNING, DEDUCTION, REIMBURSEMENT |
| calculated_amount | DECIMAL(15,2) | Before adjustments |
| adjusted_amount | DECIMAL(15,2) | After arrears/LOP |
| final_amount | DECIMAL(15,2) | |
| arrear_amount | DECIMAL(15,2) | |
| remarks | TEXT | |
| is_active | BOOLEAN | |

---

### 23. Employee Lifecycle Event (`hris_employee_lifecycle`)

Career events (joining, promotion, transfer, separation).

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| employee_id | UUID | FK |
| event_type | ENUM | JOINING, CONFIRMATION, PROMOTION, TRANSFER, DEMOTION, SALARY_REVISION, RESIGNATION, TERMINATION, RETIREMENT, ABSCONDING, REHIRE |
| event_date | DATE | |
| effective_date | DATE | |
| previous_department_id | UUID | |
| new_department_id | UUID | |
| previous_designation_id | UUID | |
| new_designation_id | UUID | |
| previous_unit_id | UUID | |
| new_unit_id | UUID | |
| previous_reporting_manager_id | UUID | |
| new_reporting_manager_id | UUID | |
| previous_salary_structure_id | UUID | |
| new_salary_structure_id | UUID | |
| reason | TEXT | |
| remarks | TEXT | |
| letter_url | VARCHAR(500) | Offer/promotion letter |
| approved_by | UUID | |
| approved_at | TIMESTAMP | |
| workflow_instance_id | UUID | |
| is_active | BOOLEAN | |

---

### 24. Separation (`hris_separation`)

Employee exit process.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| employee_id | UUID | FK |
| separation_type | ENUM | RESIGNATION, TERMINATION, RETIREMENT, ABSCONDING, DEATH |
| resignation_date | DATE | |
| requested_last_working_date | DATE | |
| approved_last_working_date | DATE | |
| actual_last_working_date | DATE | |
| notice_period_days | INTEGER | |
| notice_period_served | INTEGER | |
| notice_period_shortfall | INTEGER | |
| shortfall_recovery_amount | DECIMAL(15,2) | |
| reason_category | ENUM | BETTER_OPPORTUNITY, PERSONAL, HEALTH, RELOCATION, HIGHER_STUDIES, OTHER |
| reason_detail | TEXT | |
| exit_interview_done | BOOLEAN | |
| exit_interview_date | DATE | |
| exit_interview_notes | TEXT | |
| clearance_status | ENUM | PENDING, IN_PROGRESS, COMPLETED |
| fnf_status | ENUM | PENDING, CALCULATED, APPROVED, PAID |
| fnf_amount | DECIMAL(15,2) | |
| fnf_payment_date | DATE | |
| relieving_letter_issued | BOOLEAN | |
| experience_letter_issued | BOOLEAN | |
| status | ENUM | INITIATED, NOTICE_PERIOD, CLEARANCE, FNF_PENDING, COMPLETED, WITHDRAWN |
| approved_by | UUID | |
| workflow_instance_id | UUID | |
| is_active | BOOLEAN | |

---

### 25. Clearance Checklist (`hris_clearance_checklist`)

Exit clearance items.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| organization_id | UUID | FK |
| checklist_item | VARCHAR(200) | e.g., "ID Card Returned" |
| department_id | UUID | Responsible dept |
| display_order | INTEGER | |
| is_mandatory | BOOLEAN | |
| is_active | BOOLEAN | |

---

### 26. Separation Clearance (`hris_separation_clearance`)

Clearance status per item.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| separation_id | UUID | FK |
| checklist_id | UUID | FK |
| status | ENUM | PENDING, CLEARED, NOT_APPLICABLE |
| cleared_by | UUID | |
| cleared_at | TIMESTAMP | |
| recovery_amount | DECIMAL(15,2) | If any |
| remarks | TEXT | |
| is_active | BOOLEAN | |

---

### 27. Full & Final Settlement (`hris_fnf_settlement`)

FnF calculation.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| separation_id | UUID | FK |
| employee_id | UUID | FK |
| settlement_date | DATE | |
| last_working_date | DATE | |
| pending_salary | DECIMAL(15,2) | |
| leave_encashment | DECIMAL(15,2) | |
| gratuity_amount | DECIMAL(15,2) | |
| bonus_amount | DECIMAL(15,2) | |
| reimbursements | DECIMAL(15,2) | |
| other_earnings | DECIMAL(15,2) | |
| total_earnings | DECIMAL(15,2) | |
| notice_recovery | DECIMAL(15,2) | |
| advance_recovery | DECIMAL(15,2) | |
| loan_recovery | DECIMAL(15,2) | |
| asset_recovery | DECIMAL(15,2) | |
| other_deductions | DECIMAL(15,2) | |
| tds_amount | DECIMAL(15,2) | |
| total_deductions | DECIMAL(15,2) | |
| net_payable | DECIMAL(15,2) | |
| status | ENUM | DRAFT, CALCULATED, APPROVED, PAID |
| approved_by | UUID | |
| approved_at | TIMESTAMP | |
| payment_date | DATE | |
| payment_mode | ENUM | |
| payment_reference | VARCHAR(50) | |
| voucher_id | UUID | FK |
| remarks | TEXT | |
| is_active | BOOLEAN | |

---

## Process Flows

### 1. Employee Onboarding Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EMPLOYEE ONBOARDING FLOW                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. CREATE EMPLOYEE                                                 │
│     ├── Basic details (name, DOB, contact)                          │
│     ├── Department & Designation assignment                         │
│     ├── Reporting manager assignment                                │
│     └── Generate employee code                                      │
│              │                                                      │
│              ▼                                                      │
│  2. DOCUMENT COLLECTION                                             │
│     ├── Upload Aadhaar, PAN                                         │
│     ├── Upload education certificates                               │
│     ├── Upload experience letters                                   │
│     └── Photo upload                                                │
│              │                                                      │
│              ▼                                                      │
│  3. STATUTORY REGISTRATION                                          │
│     ├── Capture PAN, Aadhaar                                        │
│     ├── Register for PF (UAN generation)                            │
│     ├── Register for ESI (if applicable)                            │
│     └── PT registration                                             │
│              │                                                      │
│              ▼                                                      │
│  4. SALARY STRUCTURE CREATION                                       │
│     ├── Define CTC                                                  │
│     ├── Break down into components                                  │
│     │   ├── Basic (40-50% of CTC)                                   │
│     │   ├── HRA (40-50% of Basic)                                   │
│     │   ├── Other allowances                                        │
│     │   └── Statutory (PF, ESI)                                     │
│     └── Approval by HR/Finance                                      │
│              │                                                      │
│              ▼                                                      │
│  5. LEAVE SETUP                                                     │
│     ├── Initialize leave balances                                   │
│     ├── Apply joining-month proration                               │
│     └── Set waiting period if any                                   │
│              │                                                      │
│              ▼                                                      │
│  6. ATTENDANCE SETUP                                                │
│     ├── Assign shift                                                │
│     ├── Configure weekly off                                        │
│     └── Biometric enrollment                                        │
│              │                                                      │
│              ▼                                                      │
│  7. CONFIRMATION TRACKING                                           │
│     ├── Set probation end date                                      │
│     ├── Schedule confirmation review                                │
│     └── On confirmation: Update status, revise salary if any        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 2. Leave Application Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LEAVE APPLICATION FLOW                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. EMPLOYEE SUBMITS LEAVE REQUEST                                  │
│     ├── Select leave type                                           │
│     ├── Enter from/to dates with sessions                           │
│     ├── Provide reason                                              │
│     └── Upload documents (if required)                              │
│              │                                                      │
│              ▼                                                      │
│  2. SYSTEM VALIDATIONS                                              │
│     ├── Check leave balance                                         │
│     ├── Validate advance notice period                              │
│     ├── Check for overlapping leaves                                │
│     ├── Validate consecutive days limit                             │
│     ├── Check clubbing restrictions                                 │
│     └── Validate document requirement                               │
│              │                                                      │
│              ▼                                                      │
│  3. WORKFLOW INITIATION                                             │
│     ├── Create workflow instance                                    │
│     ├── Assign to reporting manager                                 │
│     └── Send notification                                           │
│              │                                                      │
│              ▼                                                      │
│  4. MANAGER APPROVAL                                                │
│     ├── Review request                                              │
│     ├── Approve / Reject                                            │
│     │   ├── If Approved → Continue                                  │
│     │   └── If Rejected → Notify employee, END                      │
│     └── Comments (mandatory for rejection)                          │
│              │                                                      │
│              ▼                                                      │
│  5. POST-APPROVAL ACTIONS                                           │
│     ├── Deduct from leave balance                                   │
│     ├── Mark attendance as ON_LEAVE                                 │
│     ├── Notify employee                                             │
│     └── Update calendar                                             │
│              │                                                      │
│              ▼                                                      │
│  6. CANCELLATION (If requested before leave starts)                 │
│     ├── Employee requests cancellation                              │
│     ├── Manager approves cancellation                               │
│     ├── Restore leave balance                                       │
│     └── Update attendance to normal                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 3. Monthly Attendance Processing Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                 MONTHLY ATTENDANCE PROCESSING                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. DAILY ATTENDANCE CAPTURE                                        │
│     ├── Biometric punch-in/out                                      │
│     ├── Mobile GPS punch                                            │
│     ├── Web check-in                                                │
│     └── Manual entry (with approval)                                │
│              │                                                      │
│              ▼                                                      │
│  2. NIGHTLY ATTENDANCE PROCESSING JOB                               │
│     ├── For each employee:                                          │
│     │   ├── Check if punch exists                                   │
│     │   ├── Calculate late/early                                    │
│     │   ├── Calculate overtime                                      │
│     │   ├── Check against leave/holiday/weekly-off                  │
│     │   └── Determine final status                                  │
│     └── Generate attendance summary                                 │
│              │                                                      │
│              ▼                                                      │
│  3. REGULARIZATION WINDOW (Until lock date)                         │
│     ├── Employee views attendance                                   │
│     ├── Raises regularization for:                                  │
│     │   ├── Missing punch                                           │
│     │   ├── Wrong punch                                             │
│     │   └── Status correction                                       │
│     ├── Manager approval                                            │
│     └── Apply corrections                                           │
│              │                                                      │
│              ▼                                                      │
│  4. ATTENDANCE LOCK                                                 │
│     ├── HR locks attendance for month                               │
│     ├── No more regularizations allowed                             │
│     └── Generate final summary                                      │
│              │                                                      │
│              ▼                                                      │
│  5. GENERATE ATTENDANCE REPORT                                      │
│     ├── Present/Absent/Leave days                                   │
│     ├── Late/Early instances                                        │
│     ├── Overtime hours                                              │
│     └── LOP days calculation                                        │
│              │                                                      │
│              ▼                                                      │
│  6. PASS TO PAYROLL                                                 │
│     └── Attendance data ready for payroll processing                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 4. Payroll Processing Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PAYROLL PROCESSING FLOW                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. INITIATE PAYROLL PERIOD                                         │
│     ├── Create period (e.g., Jan 2026)                              │
│     ├── Set attendance cutoff date                                  │
│     ├── Set payment date                                            │
│     └── Status: OPEN                                                │
│              │                                                      │
│              ▼                                                      │
│  2. LOCK ATTENDANCE                                                 │
│     ├── Freeze attendance for period                                │
│     ├── Generate attendance summary                                 │
│     └── Status: ATTENDANCE_LOCKED                                   │
│              │                                                      │
│              ▼                                                      │
│  3. RUN PAYROLL CALCULATION                                         │
│     ├── For each active employee:                                   │
│     │   ├── Get salary structure                                    │
│     │   ├── Get attendance summary                                  │
│     │   ├── Calculate earnings:                                     │
│     │   │   ├── Basic (pro-rated for LOP)                           │
│     │   │   ├── HRA (pro-rated)                                     │
│     │   │   ├── Other allowances                                    │
│     │   │   ├── Overtime pay                                        │
│     │   │   └── Arrears (if any)                                    │
│     │   ├── Calculate deductions:                                   │
│     │   │   ├── PF Employee (12% of Basic+DA)                       │
│     │   │   ├── ESI Employee (0.75% if applicable)                  │
│     │   │   ├── Professional Tax (state-wise)                       │
│     │   │   ├── TDS (based on tax projection)                       │
│     │   │   ├── Loan EMIs                                           │
│     │   │   └── Other deductions                                    │
│     │   ├── Calculate employer contributions:                       │
│     │   │   ├── PF Employer (12% + admin)                           │
│     │   │   └── ESI Employer (3.25%)                                │
│     │   └── Net = Gross - Deductions                                │
│     └── Status: PROCESSING                                          │
│              │                                                      │
│              ▼                                                      │
│  4. PAYROLL REVIEW                                                  │
│     ├── HR reviews payroll summary                                  │
│     ├── Check for anomalies                                         │
│     ├── Verify totals                                               │
│     └── Make adjustments if needed                                  │
│              │                                                      │
│              ▼                                                      │
│  5. PAYROLL APPROVAL                                                │
│     ├── Finance Head approval                                       │
│     ├── Director approval (if needed)                               │
│     └── Status: APPROVED                                            │
│              │                                                      │
│              ▼                                                      │
│  6. GENERATE OUTPUTS                                                │
│     ├── Payslips (PDF)                                              │
│     ├── Bank file (salary credit)                                   │
│     ├── PF return file                                              │
│     ├── ESI return file                                             │
│     ├── PT challans                                                 │
│     └── GL voucher entries                                          │
│              │                                                      │
│              ▼                                                      │
│  7. SALARY DISBURSEMENT                                             │
│     ├── Upload bank file                                            │
│     ├── Track credit confirmations                                  │
│     ├── Handle failures                                             │
│     └── Status: PAID                                                │
│              │                                                      │
│              ▼                                                      │
│  8. STATUTORY REMITTANCE                                            │
│     ├── PF remittance (by 15th)                                     │
│     ├── ESI remittance (by 15th)                                    │
│     ├── PT remittance (state-wise)                                  │
│     └── TDS deposit (by 7th)                                        │
│              │                                                      │
│              ▼                                                      │
│  9. CLOSE PAYROLL                                                   │
│     ├── Post GL entries                                             │
│     ├── Finalize all records                                        │
│     └── Status: CLOSED                                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 5. Separation & FnF Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                   SEPARATION & FNF FLOW                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. RESIGNATION INITIATION                                          │
│     ├── Employee submits resignation                                │
│     ├── Enter last working date (per notice period)                 │
│     ├── Reason for leaving                                          │
│     └── Status: INITIATED                                           │
│              │                                                      │
│              ▼                                                      │
│  2. MANAGER ACCEPTANCE                                              │
│     ├── Manager reviews resignation                                 │
│     ├── Accept / Negotiate / Reject                                 │
│     ├── Confirm or modify LWD                                       │
│     └── Status: NOTICE_PERIOD                                       │
│              │                                                      │
│              ▼                                                      │
│  3. NOTICE PERIOD SERVING                                           │
│     ├── Employee continues work                                     │
│     ├── Knowledge transfer                                          │
│     ├── Handover documentation                                      │
│     └── (Option: Notice buyout)                                     │
│              │                                                      │
│              ▼                                                      │
│  4. EXIT INTERVIEW                                                  │
│     ├── HR schedules interview                                      │
│     ├── Capture feedback                                            │
│     └── Document findings                                           │
│              │                                                      │
│              ▼                                                      │
│  5. CLEARANCE PROCESS                                               │
│     ├── IT: Laptop, access revocation                               │
│     ├── Admin: ID card, keys                                        │
│     ├── Finance: Advances, loans                                    │
│     ├── HR: Documents return                                        │
│     ├── Department: Handover sign-off                               │
│     └── Status: CLEARANCE                                           │
│              │                                                      │
│              ▼                                                      │
│  6. FNF CALCULATION                                                 │
│     ├── EARNINGS:                                                   │
│     │   ├── Pending salary (current month)                          │
│     │   ├── Leave encashment                                        │
│     │   ├── Gratuity (if 5+ years)                                  │
│     │   ├── Bonus pro-rata                                          │
│     │   └── Reimbursements pending                                  │
│     ├── DEDUCTIONS:                                                 │
│     │   ├── Notice shortfall recovery                               │
│     │   ├── Advance recovery                                        │
│     │   ├── Loan balance                                            │
│     │   ├── Asset recovery                                          │
│     │   └── TDS on FnF                                              │
│     └── NET PAYABLE = Earnings - Deductions                         │
│              │                                                      │
│              ▼                                                      │
│  7. FNF APPROVAL                                                    │
│     ├── HR verification                                             │
│     ├── Finance approval                                            │
│     └── Status: FNF_APPROVED                                        │
│              │                                                      │
│              ▼                                                      │
│  8. FNF PAYMENT                                                     │
│     ├── Process payment                                             │
│     ├── Generate FnF statement                                      │
│     └── Status: FNF_PAID                                            │
│              │                                                      │
│              ▼                                                      │
│  9. DOCUMENTATION                                                   │
│     ├── Issue relieving letter                                      │
│     ├── Issue experience letter                                     │
│     ├── Provide Form 16                                             │
│     ├── PF withdrawal/transfer docs                                 │
│     └── Status: COMPLETED                                           │
│              │                                                      │
│              ▼                                                      │
│ 10. EMPLOYEE DEACTIVATION                                           │
│     ├── Mark employee as RELIEVED                                   │
│     ├── Revoke all system access                                    │
│     └── Archive employee data                                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Statutory Calculations

### 1. Provident Fund (PF)

**Applicability**: All employees with Basic + DA ≤ ₹15,000/month (mandatory), optional above

| Component | Rate | Ceiling |
|-----------|------|---------|
| Employee Contribution | 12% of Basic + DA | Basic ≤ ₹15,000 |
| Employer Contribution (PF) | 3.67% | |
| Employer Contribution (EPS) | 8.33% | ₹15,000 cap |
| EDLI (Employer) | 0.50% | ₹15,000 cap |
| Admin Charges (Employer) | 0.50% | |

**Calculation Example:**
- Basic: ₹20,000
- PF Wage (capped): ₹15,000
- Employee PF: ₹15,000 × 12% = ₹1,800
- Employer PF: ₹15,000 × 3.67% = ₹550
- Employer EPS: ₹15,000 × 8.33% = ₹1,250
- Employer Total: ₹1,800 + Admin

### 2. Employee State Insurance (ESI)

**Applicability**: Gross salary ≤ ₹21,000/month

| Component | Rate |
|-----------|------|
| Employee Contribution | 0.75% of Gross |
| Employer Contribution | 3.25% of Gross |

### 3. Professional Tax (State-wise)

**Karnataka:**
| Salary Range | Monthly Tax |
|--------------|-------------|
| ≤ ₹15,000 | Nil |
| > ₹15,000 | ₹200 |

**Maharashtra:**
| Salary Range | Monthly Tax |
|--------------|-------------|
| ≤ ₹7,500 | Nil |
| ₹7,501 - ₹10,000 | ₹175 |
| > ₹10,000 | ₹200 (₹300 in Feb) |

### 4. Gratuity

**Eligibility**: 5+ years of continuous service

**Formula:**
```
Gratuity = (Last drawn salary × 15 × Years of service) / 26

Where:
- Last drawn salary = Basic + DA
- Maximum limit: ₹20,00,000
```

---

## API Endpoints Summary

### Employee Management
```
POST   /api/v1/hris/employees                    - Create employee
GET    /api/v1/hris/employees                    - List employees
GET    /api/v1/hris/employees/{id}               - Get employee details
PUT    /api/v1/hris/employees/{id}               - Update employee
DELETE /api/v1/hris/employees/{id}               - Deactivate employee
GET    /api/v1/hris/employees/{id}/documents     - Get documents
POST   /api/v1/hris/employees/{id}/documents     - Upload document
GET    /api/v1/hris/employees/{id}/family        - Get family members
POST   /api/v1/hris/employees/{id}/family        - Add family member
GET    /api/v1/hris/employees/{id}/lifecycle     - Get lifecycle events
```

### Leave Management
```
GET    /api/v1/hris/leave-types                  - List leave types
POST   /api/v1/hris/leave-types                  - Create leave type
GET    /api/v1/hris/leave/balances/{employee_id} - Get leave balances
POST   /api/v1/hris/leave/applications           - Apply leave
GET    /api/v1/hris/leave/applications           - List applications
PUT    /api/v1/hris/leave/applications/{id}      - Update application
POST   /api/v1/hris/leave/applications/{id}/approve  - Approve leave
POST   /api/v1/hris/leave/applications/{id}/reject   - Reject leave
POST   /api/v1/hris/leave/applications/{id}/cancel   - Cancel leave
POST   /api/v1/hris/leave/encashment             - Request encashment
GET    /api/v1/hris/leave/calendar               - Team calendar view
```

### Attendance Management
```
POST   /api/v1/hris/attendance/punch             - Record punch
GET    /api/v1/hris/attendance/my                - My attendance
GET    /api/v1/hris/attendance/team              - Team attendance
POST   /api/v1/hris/attendance/regularization    - Request regularization
PUT    /api/v1/hris/attendance/regularization/{id}/approve
POST   /api/v1/hris/attendance/on-duty           - Request on-duty
GET    /api/v1/hris/attendance/summary           - Monthly summary
POST   /api/v1/hris/attendance/process-daily     - Nightly job
```

### Shift & Holiday
```
GET    /api/v1/hris/shifts                       - List shifts
POST   /api/v1/hris/shifts                       - Create shift
GET    /api/v1/hris/holidays                     - List holidays
POST   /api/v1/hris/holidays                     - Create holiday
POST   /api/v1/hris/holidays/import              - Bulk import
```

### Salary & Payroll
```
GET    /api/v1/hris/salary-components            - List components
POST   /api/v1/hris/salary-components            - Create component
GET    /api/v1/hris/salary-structures/{employee_id} - Get structure
POST   /api/v1/hris/salary-structures            - Create structure
PUT    /api/v1/hris/salary-structures/{id}       - Update structure

POST   /api/v1/hris/payroll/periods              - Create period
GET    /api/v1/hris/payroll/periods              - List periods
POST   /api/v1/hris/payroll/periods/{id}/lock    - Lock attendance
POST   /api/v1/hris/payroll/periods/{id}/process - Run payroll
GET    /api/v1/hris/payroll/periods/{id}/summary - Get summary
POST   /api/v1/hris/payroll/periods/{id}/approve - Approve payroll
POST   /api/v1/hris/payroll/periods/{id}/pay     - Mark as paid
POST   /api/v1/hris/payroll/periods/{id}/close   - Close period
GET    /api/v1/hris/payroll/{employee_id}/payslip/{period_id}
```

### Separation & FnF
```
POST   /api/v1/hris/separation/initiate          - Initiate separation
GET    /api/v1/hris/separation/{id}              - Get separation
PUT    /api/v1/hris/separation/{id}/accept       - Accept resignation
GET    /api/v1/hris/separation/{id}/clearance    - Get clearance status
PUT    /api/v1/hris/separation/{id}/clearance/{item_id} - Update clearance
POST   /api/v1/hris/separation/{id}/fnf/calculate - Calculate FnF
POST   /api/v1/hris/separation/{id}/fnf/approve  - Approve FnF
POST   /api/v1/hris/separation/{id}/fnf/pay      - Pay FnF
POST   /api/v1/hris/separation/{id}/complete     - Complete separation
```

### Reports
```
GET    /api/v1/hris/reports/headcount            - Headcount report
GET    /api/v1/hris/reports/attendance-summary   - Attendance summary
GET    /api/v1/hris/reports/leave-summary        - Leave summary
GET    /api/v1/hris/reports/payroll-register     - Payroll register
GET    /api/v1/hris/reports/pf-return            - PF ECR file
GET    /api/v1/hris/reports/esi-return           - ESI return file
GET    /api/v1/hris/reports/pt-return            - PT challans
GET    /api/v1/hris/reports/salary-register      - Salary register
GET    /api/v1/hris/reports/form-16              - Form 16
```

---

## Frontend Pages

### Employee Self-Service
```
/hris/dashboard                    - Employee dashboard
/hris/profile                      - My profile
/hris/profile/documents            - My documents
/hris/attendance                   - My attendance
/hris/attendance/regularization    - Apply regularization
/hris/leave                        - My leave balance
/hris/leave/apply                  - Apply leave
/hris/leave/history                - Leave history
/hris/payslips                     - My payslips
/hris/tax-declaration              - IT declaration
```

### Manager Self-Service
```
/hris/team                         - My team
/hris/team/attendance              - Team attendance
/hris/team/leaves                  - Team leave requests
/hris/approvals                    - Pending approvals
```

### HR Administration
```
/hris/admin/employees              - Employee list
/hris/admin/employees/new          - Add employee
/hris/admin/employees/{id}         - Employee detail
/hris/admin/employees/{id}/edit    - Edit employee
/hris/admin/employees/{id}/lifecycle - Lifecycle events

/hris/admin/shifts                 - Shift master
/hris/admin/holidays               - Holiday calendar
/hris/admin/leave-types            - Leave type master

/hris/admin/attendance             - Attendance dashboard
/hris/admin/attendance/process     - Process attendance
/hris/admin/attendance/corrections - Pending corrections

/hris/admin/salary-components      - Salary components
/hris/admin/salary-structures      - Salary structures

/hris/admin/payroll                - Payroll dashboard
/hris/admin/payroll/run            - Run payroll
/hris/admin/payroll/review         - Review & approve
/hris/admin/payroll/history        - Payroll history

/hris/admin/separations            - Separation list
/hris/admin/separations/{id}       - Separation detail
/hris/admin/separations/{id}/fnf   - FnF processing

/hris/admin/reports                - Reports dashboard
```

---

## Files to Create

### Backend (~45 files)

```
# Models
backend/app/models/hris/__init__.py
backend/app/models/hris/employee.py
backend/app/models/hris/employee_document.py
backend/app/models/hris/employee_family.py
backend/app/models/hris/employee_bank_account.py
backend/app/models/hris/employee_education.py
backend/app/models/hris/employee_experience.py
backend/app/models/hris/employee_statutory.py
backend/app/models/hris/shift.py
backend/app/models/hris/holiday.py
backend/app/models/hris/leave_type.py
backend/app/models/hris/leave_balance.py
backend/app/models/hris/leave_application.py
backend/app/models/hris/attendance.py
backend/app/models/hris/attendance_regularization.py
backend/app/models/hris/on_duty_request.py
backend/app/models/hris/employee_lifecycle.py
backend/app/models/hris/salary_component.py
backend/app/models/hris/salary_structure.py
backend/app/models/hris/payroll_period.py
backend/app/models/hris/payroll.py
backend/app/models/hris/separation.py
backend/app/models/hris/clearance.py
backend/app/models/hris/fnf_settlement.py

# Schemas
backend/app/schemas/hris/__init__.py
backend/app/schemas/hris/employee.py
backend/app/schemas/hris/leave.py
backend/app/schemas/hris/attendance.py
backend/app/schemas/hris/salary.py
backend/app/schemas/hris/payroll.py
backend/app/schemas/hris/separation.py

# Services
backend/app/services/hris/__init__.py
backend/app/services/hris/employee_service.py
backend/app/services/hris/leave_service.py
backend/app/services/hris/attendance_service.py
backend/app/services/hris/salary_service.py
backend/app/services/hris/payroll_service.py
backend/app/services/hris/statutory_service.py
backend/app/services/hris/separation_service.py

# APIs
backend/app/api/v1/hris/__init__.py
backend/app/api/v1/hris/employees.py
backend/app/api/v1/hris/leaves.py
backend/app/api/v1/hris/attendance.py
backend/app/api/v1/hris/payroll.py
backend/app/api/v1/hris/separations.py
backend/app/api/v1/hris/reports.py

# Migration
backend/alembic/versions/z13_add_hris.py
```

### Frontend (~25 files)

```
src/pages/hris/
├── HRISDashboard.tsx
├── employees/
│   ├── EmployeeList.tsx
│   ├── EmployeeForm.tsx
│   └── EmployeeView.tsx
├── leave/
│   ├── LeaveTypeList.tsx
│   ├── LeaveApplication.tsx
│   ├── LeaveApprovals.tsx
│   └── LeaveCalendar.tsx
├── attendance/
│   ├── AttendanceList.tsx
│   ├── AttendanceProcess.tsx
│   └── RegularizationList.tsx
├── payroll/
│   ├── SalaryComponentList.tsx
│   ├── SalaryStructureForm.tsx
│   ├── PayrollRun.tsx
│   ├── PayrollReview.tsx
│   └── PayslipView.tsx
├── separation/
│   ├── SeparationList.tsx
│   ├── SeparationForm.tsx
│   └── FnFCalculation.tsx
└── reports/
    └── HRISReports.tsx

src/services/hrisApi.ts
```

---

## Implementation Phases

### Phase 1: Foundation (Core Masters)
- Employee master with documents, family, bank accounts
- Shift master
- Holiday calendar
- Organization structure integration

### Phase 2: Leave Management
- Leave type master
- Leave balance initialization
- Leave application workflow
- Leave encashment

### Phase 3: Attendance Management
- Daily attendance capture
- Attendance processing job
- Regularization workflow
- On-duty/WFH requests

### Phase 4: Payroll Setup
- Salary components
- Salary structure
- Tax computation setup

### Phase 5: Payroll Processing
- Payroll period management
- Payroll calculation engine
- Statutory deductions (PF, ESI, PT)
- Payslip generation

### Phase 6: Separation & FnF
- Separation initiation
- Clearance workflow
- FnF calculation
- Document generation

### Phase 7: Reports & Compliance
- Statutory returns (PF ECR, ESI)
- Form 16 generation
- MIS reports

---

## Verification Checklist

### Employee Management
- [ ] Employee creation with auto-code generation
- [ ] Document upload and verification
- [ ] Family/nominee details
- [ ] Bank account management
- [ ] Reporting hierarchy
- [ ] Lifecycle event tracking

### Leave Management
- [ ] Leave type configuration with all rules
- [ ] Leave balance accrual (monthly/yearly)
- [ ] Leave application with validations
- [ ] Approval workflow
- [ ] Leave cancellation
- [ ] Leave encashment
- [ ] Carry forward processing

### Attendance
- [ ] Punch-in/out (biometric, web, mobile)
- [ ] Late/early calculation
- [ ] Overtime calculation
- [ ] Status determination
- [ ] Regularization workflow
- [ ] Monthly processing
- [ ] Attendance lock

### Payroll
- [ ] Salary component configuration
- [ ] Salary structure setup
- [ ] LOP calculation
- [ ] Overtime pay
- [ ] Arrears processing
- [ ] PF calculation (correct rates)
- [ ] ESI calculation (if applicable)
- [ ] PT calculation (state-wise)
- [ ] TDS integration
- [ ] Net pay calculation
- [ ] Payslip generation
- [ ] Bank file generation
- [ ] GL posting

### Separation
- [ ] Resignation initiation
- [ ] Notice period tracking
- [ ] Clearance workflow
- [ ] FnF calculation (all components)
- [ ] Gratuity calculation
- [ ] Document generation
- [ ] Employee deactivation

---

*Document Version: 1.0*
*Last Updated: January 2026*
