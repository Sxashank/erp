"""Add HRIS tables.

Revision ID: z13_hris_tables
Revises: z12_fixed_assets
Create Date: 2024-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'z13_hris_tables'
down_revision = 'z12_fixed_assets'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ====================================
    # Create ENUMS
    # ====================================

    # Gender enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE gender_enum AS ENUM ('MALE', 'FEMALE', 'OTHER');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Salutation enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE salutation_enum AS ENUM ('MR', 'MS', 'MRS', 'DR', 'PROF');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Marital status enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE marital_status_enum AS ENUM ('SINGLE', 'MARRIED', 'DIVORCED', 'WIDOWED', 'SEPARATED');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Employment type enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE employment_type_enum AS ENUM ('PERMANENT', 'CONTRACT', 'PROBATION', 'INTERN', 'TRAINEE', 'CONSULTANT', 'TEMPORARY');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Employment status enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE employment_status_enum AS ENUM ('ACTIVE', 'PROBATION', 'NOTICE_PERIOD', 'RELIEVED', 'ABSCONDED', 'SUSPENDED', 'TERMINATED', 'RETIRED', 'DECEASED');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Document type enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE document_type_enum AS ENUM ('PHOTO', 'AADHAAR', 'PAN', 'PASSPORT', 'VOTER_ID', 'DRIVING_LICENSE', 'EDUCATIONAL', 'EXPERIENCE_LETTER', 'RELIEVING_LETTER', 'SALARY_SLIP', 'OFFER_LETTER', 'APPOINTMENT_LETTER', 'OTHER');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Family relation enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE family_relation_enum AS ENUM ('FATHER', 'MOTHER', 'SPOUSE', 'SON', 'DAUGHTER', 'BROTHER', 'SISTER', 'GRANDFATHER', 'GRANDMOTHER', 'FATHER_IN_LAW', 'MOTHER_IN_LAW', 'OTHER');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Education level enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE education_level_enum AS ENUM ('BELOW_10', 'SSC_10', 'HSC_12', 'DIPLOMA', 'GRADUATE', 'POST_GRADUATE', 'DOCTORATE', 'PROFESSIONAL', 'OTHER');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Lifecycle event type enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE lifecycle_event_type_enum AS ENUM ('JOINING', 'CONFIRMATION', 'PROMOTION', 'TRANSFER', 'DEPARTMENT_CHANGE', 'DESIGNATION_CHANGE', 'SALARY_REVISION', 'PROBATION_EXTENSION', 'SUSPENSION', 'REINSTATEMENT', 'RESIGNATION', 'TERMINATION', 'RETIREMENT', 'SEPARATION', 'ABSCONDING');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Shift type enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE shift_type_enum AS ENUM ('GENERAL', 'MORNING', 'AFTERNOON', 'NIGHT', 'ROTATIONAL', 'FLEXIBLE');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Holiday type enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE holiday_type_enum AS ENUM ('NATIONAL', 'STATE', 'COMPANY', 'RESTRICTED', 'OPTIONAL');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Leave category enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE leave_category_enum AS ENUM ('EARNED', 'CASUAL', 'SICK', 'MATERNITY', 'PATERNITY', 'MARRIAGE', 'BEREAVEMENT', 'COMP_OFF', 'UNPAID', 'SPECIAL', 'SABBATICAL', 'OTHER');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Leave application status enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE leave_application_status_enum AS ENUM ('DRAFT', 'PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', 'WITHDRAWN');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Attendance status enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE attendance_status_enum AS ENUM ('PRESENT', 'ABSENT', 'HALF_DAY', 'LATE', 'ON_LEAVE', 'HOLIDAY', 'WEEK_OFF', 'ON_DUTY', 'WFH', 'COMP_OFF');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Attendance source enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE attendance_source_enum AS ENUM ('BIOMETRIC', 'WEB', 'MOBILE', 'MANUAL', 'IMPORT', 'RFID', 'FACE_RECOGNITION');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # Regularization status enum
    op.execute("""

        DO $$ BEGIN

            CREATE TYPE regularization_status_enum AS ENUM ('PENDING', 'APPROVED', 'REJECTED');

        EXCEPTION WHEN duplicate_object THEN null; END $$;

    """)

    # ====================================
    # Create HRIS Shift Table
    # ====================================
    op.create_table(
        'hris_shift',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shift_code', sa.String(20), nullable=False),
        sa.Column('shift_name', sa.String(100), nullable=False),
        sa.Column('shift_type', postgresql.ENUM('GENERAL', 'MORNING', 'AFTERNOON', 'NIGHT', 'ROTATIONAL', 'FLEXIBLE', name='shift_type_enum', create_type=False), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('is_overnight', sa.Boolean(), default=False),
        sa.Column('break_start_time', sa.Time(), nullable=True),
        sa.Column('break_end_time', sa.Time(), nullable=True),
        sa.Column('break_duration_minutes', sa.Integer(), default=0),
        sa.Column('working_hours', sa.Integer(), nullable=False, default=480),
        sa.Column('half_day_hours', sa.Integer(), default=240),
        sa.Column('grace_period_late_minutes', sa.Integer(), default=15),
        sa.Column('grace_period_early_minutes', sa.Integer(), default=15),
        sa.Column('late_deduction_rules', postgresql.JSONB(), nullable=True),
        sa.Column('overtime_applicable', sa.Boolean(), default=False),
        sa.Column('overtime_threshold_minutes', sa.Integer(), default=30),
        sa.Column('overtime_rate_multiplier', sa.Integer(), default=1),
        sa.Column('week_off_days', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'shift_code', name='uq_shift_org_code'),
    )
    op.create_index('ix_hris_shift_organization_id', 'hris_shift', ['organization_id'])

    # ====================================
    # Create HRIS Employee Table
    # ====================================
    op.create_table(
        'hris_employee',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_code', sa.String(20), nullable=False),
        # Personal Info
        sa.Column('salutation', postgresql.ENUM('MR', 'MS', 'MRS', 'DR', 'PROF', name='salutation_enum', create_type=False), nullable=True),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('middle_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(200), nullable=True),
        sa.Column('gender', postgresql.ENUM('MALE', 'FEMALE', 'OTHER', name='gender_enum', create_type=False), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=False),
        sa.Column('blood_group', sa.String(5), nullable=True),
        sa.Column('marital_status', postgresql.ENUM('SINGLE', 'MARRIED', 'DIVORCED', 'WIDOWED', 'SEPARATED', name='marital_status_enum', create_type=False), nullable=True),
        sa.Column('nationality', sa.String(50), nullable=True, default='Indian'),
        # Contact Info
        sa.Column('personal_email', sa.String(255), nullable=True),
        sa.Column('personal_mobile', sa.String(20), nullable=False),
        sa.Column('official_email', sa.String(255), nullable=True),
        sa.Column('official_mobile', sa.String(20), nullable=True),
        # Emergency Contact
        sa.Column('emergency_contact_name', sa.String(200), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(20), nullable=True),
        sa.Column('emergency_contact_relation', sa.String(50), nullable=True),
        # Address
        sa.Column('current_address', postgresql.JSONB(), nullable=True),
        sa.Column('permanent_address', postgresql.JSONB(), nullable=True),
        sa.Column('is_address_same', sa.Boolean(), default=False),
        # Photo
        sa.Column('photo_url', sa.String(500), nullable=True),
        # Organization Structure
        sa.Column('department_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('designation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reporting_manager_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('unit_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cost_center_id', postgresql.UUID(as_uuid=True), nullable=True),
        # Employment Dates
        sa.Column('date_of_joining', sa.Date(), nullable=False),
        sa.Column('confirmation_date', sa.Date(), nullable=True),
        sa.Column('probation_end_date', sa.Date(), nullable=True),
        sa.Column('date_of_leaving', sa.Date(), nullable=True),
        # Employment Type/Status
        sa.Column('employment_type', postgresql.ENUM('PERMANENT', 'CONTRACT', 'PROBATION', 'INTERN', 'TRAINEE', 'CONSULTANT', 'TEMPORARY', name='employment_type_enum', create_type=False), nullable=False),
        sa.Column('employment_status', postgresql.ENUM('ACTIVE', 'PROBATION', 'NOTICE_PERIOD', 'RELIEVED', 'ABSCONDED', 'SUSPENDED', 'TERMINATED', 'RETIRED', 'DECEASED', name='employment_status_enum', create_type=False), nullable=False),
        sa.Column('notice_period_days', sa.Integer(), default=30),
        # Shift
        sa.Column('shift_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('week_off_days', postgresql.JSONB(), nullable=True),
        # Linked User Account
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        # Identity Numbers
        sa.Column('pan_number', sa.String(10), nullable=True),
        sa.Column('aadhaar_number', sa.String(12), nullable=True),
        sa.Column('uan_number', sa.String(12), nullable=True),
        sa.Column('esic_number', sa.String(17), nullable=True),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['department_id'], ['mst_department.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['designation_id'], ['mst_designation.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reporting_manager_id'], ['hris_employee.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['unit_id'], ['mst_unit.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['cost_center_id'], ['mst_cost_center.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['shift_id'], ['hris_shift.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'employee_code', name='uq_employee_org_code'),
    )
    op.create_index('ix_hris_employee_organization_id', 'hris_employee', ['organization_id'])
    op.create_index('ix_hris_employee_department_id', 'hris_employee', ['department_id'])
    op.create_index('ix_hris_employee_designation_id', 'hris_employee', ['designation_id'])
    op.create_index('ix_hris_employee_employment_status', 'hris_employee', ['employment_status'])

    # ====================================
    # Create Employee Document Table
    # ====================================
    op.create_table(
        'hris_employee_document',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_type', postgresql.ENUM('PHOTO', 'AADHAAR', 'PAN', 'PASSPORT', 'VOTER_ID', 'DRIVING_LICENSE', 'EDUCATIONAL', 'EXPERIENCE_LETTER', 'RELIEVING_LETTER', 'SALARY_SLIP', 'OFFER_LETTER', 'APPOINTMENT_LETTER', 'OTHER', name='document_type_enum', create_type=False), nullable=False),
        sa.Column('document_number', sa.String(100), nullable=True),
        sa.Column('document_name', sa.String(200), nullable=False),
        sa.Column('file_url', sa.String(500), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('issue_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('verified_at', sa.Date(), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['employee_id'], ['hris_employee.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['verified_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_hris_employee_document_employee_id', 'hris_employee_document', ['employee_id'])

    # ====================================
    # Create Employee Family Table
    # ====================================
    op.create_table(
        'hris_employee_family',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relation', postgresql.ENUM('FATHER', 'MOTHER', 'SPOUSE', 'SON', 'DAUGHTER', 'BROTHER', 'SISTER', 'GRANDFATHER', 'GRANDMOTHER', 'FATHER_IN_LAW', 'MOTHER_IN_LAW', 'OTHER', name='family_relation_enum', create_type=False), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('gender', postgresql.ENUM('MALE', 'FEMALE', 'OTHER', name='gender_enum', create_type=False), nullable=True),
        sa.Column('occupation', sa.String(100), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('is_dependent', sa.Boolean(), default=False),
        sa.Column('is_nominee', sa.Boolean(), default=False),
        sa.Column('nominee_percentage', sa.Numeric(5, 2), nullable=True),
        sa.Column('is_emergency_contact', sa.Boolean(), default=False),
        sa.Column('aadhaar_number', sa.String(12), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['employee_id'], ['hris_employee.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_hris_employee_family_employee_id', 'hris_employee_family', ['employee_id'])

    # ====================================
    # Create Employee Bank Account Table
    # ====================================
    op.create_table(
        'hris_employee_bank_account',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bank_name', sa.String(200), nullable=False),
        sa.Column('branch_name', sa.String(200), nullable=True),
        sa.Column('account_number', sa.String(30), nullable=False),
        sa.Column('ifsc_code', sa.String(11), nullable=False),
        sa.Column('account_holder_name', sa.String(200), nullable=False),
        sa.Column('account_type', sa.String(20), nullable=True, default='SAVINGS'),
        sa.Column('is_primary', sa.Boolean(), default=False),
        sa.Column('is_salary_account', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('verified_at', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['employee_id'], ['hris_employee.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('employee_id', 'account_number', name='uq_emp_bank_account'),
    )
    op.create_index('ix_hris_employee_bank_account_employee_id', 'hris_employee_bank_account', ['employee_id'])

    # ====================================
    # Create Employee Education Table
    # ====================================
    op.create_table(
        'hris_employee_education',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('level', postgresql.ENUM('BELOW_10', 'SSC_10', 'HSC_12', 'DIPLOMA', 'GRADUATE', 'POST_GRADUATE', 'DOCTORATE', 'PROFESSIONAL', 'OTHER', name='education_level_enum', create_type=False), nullable=False),
        sa.Column('degree_name', sa.String(200), nullable=False),
        sa.Column('specialization', sa.String(200), nullable=True),
        sa.Column('institution_name', sa.String(300), nullable=False),
        sa.Column('university_board', sa.String(200), nullable=True),
        sa.Column('start_year', sa.Integer(), nullable=True),
        sa.Column('end_year', sa.Integer(), nullable=True),
        sa.Column('percentage_cgpa', sa.Numeric(5, 2), nullable=True),
        sa.Column('grade', sa.String(20), nullable=True),
        sa.Column('is_highest_qualification', sa.Boolean(), default=False),
        sa.Column('document_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['employee_id'], ['hris_employee.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_hris_employee_education_employee_id', 'hris_employee_education', ['employee_id'])

    # ====================================
    # Create Employee Experience Table
    # ====================================
    op.create_table(
        'hris_employee_experience',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_name', sa.String(300), nullable=False),
        sa.Column('designation', sa.String(200), nullable=False),
        sa.Column('department', sa.String(200), nullable=True),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('is_current', sa.Boolean(), default=False),
        sa.Column('last_ctc', sa.Numeric(15, 2), nullable=True),
        sa.Column('reason_for_leaving', sa.Text(), nullable=True),
        sa.Column('reference_name', sa.String(200), nullable=True),
        sa.Column('reference_phone', sa.String(20), nullable=True),
        sa.Column('reference_email', sa.String(255), nullable=True),
        sa.Column('experience_letter_url', sa.String(500), nullable=True),
        sa.Column('relieving_letter_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['employee_id'], ['hris_employee.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_hris_employee_experience_employee_id', 'hris_employee_experience', ['employee_id'])

    # ====================================
    # Create Employee Statutory Table
    # ====================================
    op.create_table(
        'hris_employee_statutory',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        # PF Details
        sa.Column('pf_applicable', sa.Boolean(), default=True),
        sa.Column('pf_account_number', sa.String(30), nullable=True),
        sa.Column('pf_join_date', sa.Date(), nullable=True),
        sa.Column('pf_exit_date', sa.Date(), nullable=True),
        sa.Column('is_pf_capped', sa.Boolean(), default=True),
        sa.Column('voluntary_pf_rate', sa.Numeric(5, 2), nullable=True),
        # ESI Details
        sa.Column('esi_applicable', sa.Boolean(), default=False),
        sa.Column('esi_number', sa.String(17), nullable=True),
        sa.Column('esi_dispensary', sa.String(200), nullable=True),
        # Professional Tax
        sa.Column('pt_applicable', sa.Boolean(), default=True),
        sa.Column('pt_state', sa.String(50), nullable=True),
        sa.Column('pt_location', sa.String(100), nullable=True),
        # Labour Welfare Fund
        sa.Column('lwf_applicable', sa.Boolean(), default=False),
        # TDS / Income Tax
        sa.Column('tax_regime', sa.String(10), nullable=True, default='NEW'),
        sa.Column('it_section_declarations', postgresql.JSONB(), nullable=True),
        # Gratuity
        sa.Column('gratuity_applicable', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['employee_id'], ['hris_employee.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_hris_employee_statutory_employee_id', 'hris_employee_statutory', ['employee_id'])

    # ====================================
    # Create Employee Lifecycle Event Table
    # ====================================
    op.create_table(
        'hris_employee_lifecycle_event',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', postgresql.ENUM('JOINING', 'CONFIRMATION', 'PROMOTION', 'TRANSFER', 'DEPARTMENT_CHANGE', 'DESIGNATION_CHANGE', 'SALARY_REVISION', 'PROBATION_EXTENSION', 'SUSPENSION', 'REINSTATEMENT', 'RESIGNATION', 'TERMINATION', 'RETIREMENT', 'SEPARATION', 'ABSCONDING', name='lifecycle_event_type_enum', create_type=False), nullable=False),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('old_values', postgresql.JSONB(), nullable=True),
        sa.Column('new_values', postgresql.JSONB(), nullable=True),
        sa.Column('from_department_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('to_department_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('from_designation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('to_designation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('from_unit_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('to_unit_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.Date(), nullable=True),
        sa.Column('document_reference', sa.String(100), nullable=True),
        sa.Column('document_url', sa.String(500), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['employee_id'], ['hris_employee.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_hris_employee_lifecycle_event_employee_id', 'hris_employee_lifecycle_event', ['employee_id'])
    op.create_index('ix_hris_employee_lifecycle_event_event_date', 'hris_employee_lifecycle_event', ['event_date'])

    # ====================================
    # Create Holiday Calendar Table
    # ====================================
    op.create_table(
        'hris_holiday_calendar',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('calendar_name', sa.String(100), nullable=False, default='DEFAULT'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('applicable_unit_ids', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'year', 'calendar_name', name='uq_holiday_calendar_org_year'),
    )
    op.create_index('ix_hris_holiday_calendar_organization_id', 'hris_holiday_calendar', ['organization_id'])

    # ====================================
    # Create Holiday Table
    # ====================================
    op.create_table(
        'hris_holiday',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('calendar_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('holiday_date', sa.Date(), nullable=False),
        sa.Column('holiday_name', sa.String(200), nullable=False),
        sa.Column('holiday_type', postgresql.ENUM('NATIONAL', 'STATE', 'COMPANY', 'RESTRICTED', 'OPTIONAL', name='holiday_type_enum', create_type=False), nullable=False),
        sa.Column('is_optional', sa.Boolean(), default=False),
        sa.Column('max_optional_per_year', sa.Integer(), nullable=True),
        sa.Column('applicable_unit_ids', postgresql.JSONB(), nullable=True),
        sa.Column('applicable_department_ids', postgresql.JSONB(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['calendar_id'], ['hris_holiday_calendar.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('calendar_id', 'holiday_date', name='uq_holiday_calendar_date'),
    )
    op.create_index('ix_hris_holiday_calendar_id', 'hris_holiday', ['calendar_id'])
    op.create_index('ix_hris_holiday_holiday_date', 'hris_holiday', ['holiday_date'])

    # ====================================
    # Create Leave Type Table
    # ====================================
    op.create_table(
        'hris_leave_type',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('leave_code', sa.String(20), nullable=False),
        sa.Column('leave_name', sa.String(100), nullable=False),
        sa.Column('category', postgresql.ENUM('EARNED', 'CASUAL', 'SICK', 'MATERNITY', 'PATERNITY', 'MARRIAGE', 'BEREAVEMENT', 'COMP_OFF', 'UNPAID', 'SPECIAL', 'SABBATICAL', 'OTHER', name='leave_category_enum', create_type=False), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        # Annual Quota
        sa.Column('annual_quota', sa.Numeric(5, 2), nullable=False, default=0),
        sa.Column('max_accumulation', sa.Numeric(5, 2), nullable=True),
        # Accrual Settings
        sa.Column('accrual_type', sa.String(20), default='YEARLY'),
        sa.Column('accrual_on_joining', sa.Boolean(), default=True),
        sa.Column('prorate_on_joining', sa.Boolean(), default=True),
        # Carry Forward
        sa.Column('carry_forward_allowed', sa.Boolean(), default=False),
        sa.Column('max_carry_forward', sa.Numeric(5, 2), nullable=True),
        sa.Column('carry_forward_expiry_months', sa.Integer(), nullable=True),
        # Encashment
        sa.Column('encashment_allowed', sa.Boolean(), default=False),
        sa.Column('max_encashment_days', sa.Numeric(5, 2), nullable=True),
        sa.Column('encashment_on_separation', sa.Boolean(), default=False),
        # Application Rules
        sa.Column('min_days_per_application', sa.Numeric(3, 1), default=0.5),
        sa.Column('max_days_per_application', sa.Numeric(5, 2), nullable=True),
        sa.Column('max_consecutive_days', sa.Integer(), nullable=True),
        # Advance Notice
        sa.Column('min_advance_days', sa.Integer(), default=0),
        sa.Column('max_advance_days', sa.Integer(), nullable=True),
        # Club with Other Leaves
        sa.Column('can_club_with_holidays', sa.Boolean(), default=True),
        sa.Column('can_club_with_weekoff', sa.Boolean(), default=True),
        sa.Column('excluded_holidays_counted', sa.Boolean(), default=False),
        # Negative Balance
        sa.Column('negative_balance_allowed', sa.Boolean(), default=False),
        sa.Column('max_negative_balance', sa.Numeric(5, 2), nullable=True),
        # Document Required
        sa.Column('document_required', sa.Boolean(), default=False),
        sa.Column('document_required_after_days', sa.Integer(), nullable=True),
        # Gender Specific
        sa.Column('gender_specific', postgresql.ENUM('MALE', 'FEMALE', 'OTHER', name='gender_enum', create_type=False), nullable=True),
        # Employment Type Specific
        sa.Column('applicable_employment_types', postgresql.JSONB(), nullable=True),
        # Probation
        sa.Column('applicable_in_probation', sa.Boolean(), default=True),
        sa.Column('probation_quota', sa.Numeric(5, 2), nullable=True),
        # Notice Period
        sa.Column('applicable_in_notice', sa.Boolean(), default=False),
        # Compensatory Off Settings
        sa.Column('comp_off_validity_days', sa.Integer(), nullable=True),
        # Half Day Settings
        sa.Column('half_day_allowed', sa.Boolean(), default=True),
        # Paid/Unpaid
        sa.Column('is_paid', sa.Boolean(), default=True),
        # Status
        sa.Column('is_active', sa.Boolean(), default=True),
        # Display Order
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'leave_code', name='uq_leave_type_org_code'),
    )
    op.create_index('ix_hris_leave_type_organization_id', 'hris_leave_type', ['organization_id'])

    # ====================================
    # Create Leave Balance Table
    # ====================================
    op.create_table(
        'hris_leave_balance',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('leave_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('opening_balance', sa.Numeric(6, 2), default=0),
        sa.Column('accrued', sa.Numeric(6, 2), default=0),
        sa.Column('carry_forward', sa.Numeric(6, 2), default=0),
        sa.Column('adjustment', sa.Numeric(6, 2), default=0),
        sa.Column('used', sa.Numeric(6, 2), default=0),
        sa.Column('encashed', sa.Numeric(6, 2), default=0),
        sa.Column('lapsed', sa.Numeric(6, 2), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['employee_id'], ['hris_employee.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['leave_type_id'], ['hris_leave_type.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('employee_id', 'leave_type_id', 'year', name='uq_leave_balance_emp_type_year'),
    )
    op.create_index('ix_hris_leave_balance_employee_id', 'hris_leave_balance', ['employee_id'])
    op.create_index('ix_hris_leave_balance_leave_type_id', 'hris_leave_balance', ['leave_type_id'])

    # ====================================
    # Create Leave Application Table
    # ====================================
    op.create_table(
        'hris_leave_application',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('leave_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('application_number', sa.String(30), nullable=False, unique=True),
        sa.Column('from_date', sa.Date(), nullable=False),
        sa.Column('to_date', sa.Date(), nullable=False),
        sa.Column('is_half_day', sa.Boolean(), default=False),
        sa.Column('half_day_type', sa.String(10), nullable=True),
        sa.Column('total_days', sa.Numeric(5, 2), nullable=False),
        sa.Column('working_days', sa.Numeric(5, 2), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('contact_number', sa.String(20), nullable=True),
        sa.Column('contact_address', sa.Text(), nullable=True),
        sa.Column('attachments', postgresql.JSONB(), nullable=True),
        sa.Column('status', postgresql.ENUM('DRAFT', 'PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', 'WITHDRAWN', name='leave_application_status_enum', create_type=False), nullable=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.Date(), nullable=True),
        sa.Column('approver_remarks', sa.Text(), nullable=True),
        sa.Column('rejected_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rejected_at', sa.Date(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('cancelled_at', sa.Date(), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('comp_off_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['employee_id'], ['hris_employee.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['leave_type_id'], ['hris_leave_type.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['rejected_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_hris_leave_application_employee_id', 'hris_leave_application', ['employee_id'])
    op.create_index('ix_hris_leave_application_leave_type_id', 'hris_leave_application', ['leave_type_id'])
    op.create_index('ix_hris_leave_application_from_date', 'hris_leave_application', ['from_date'])
    op.create_index('ix_hris_leave_application_status', 'hris_leave_application', ['status'])

    # ====================================
    # Create Leave Encashment Table
    # ====================================
    op.create_table(
        'hris_leave_encashment',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('leave_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('encashment_date', sa.Date(), nullable=False),
        sa.Column('days_encashed', sa.Numeric(5, 2), nullable=False),
        sa.Column('per_day_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('gross_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('tds_amount', sa.Numeric(12, 2), default=0),
        sa.Column('net_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('encashment_type', sa.String(20), default='ANNUAL'),
        sa.Column('payroll_run_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('voucher_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.Date(), nullable=True),
        sa.Column('status', sa.String(20), default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['employee_id'], ['hris_employee.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['leave_type_id'], ['hris_leave_type.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_hris_leave_encashment_employee_id', 'hris_leave_encashment', ['employee_id'])

    # ====================================
    # Create Attendance Regularization Table (before Attendance)
    # ====================================
    op.create_table(
        'hris_attendance_regularization',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attendance_date', sa.Date(), nullable=False),
        sa.Column('request_type', sa.String(20), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('original_first_in', sa.Time(), nullable=True),
        sa.Column('original_last_out', sa.Time(), nullable=True),
        sa.Column('original_status', sa.String(20), nullable=True),
        sa.Column('requested_first_in', sa.Time(), nullable=True),
        sa.Column('requested_last_out', sa.Time(), nullable=True),
        sa.Column('requested_status', sa.String(20), nullable=True),
        sa.Column('attachments', postgresql.JSONB(), nullable=True),
        sa.Column('status', postgresql.ENUM('PENDING', 'APPROVED', 'REJECTED', name='regularization_status_enum', create_type=False), nullable=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.Date(), nullable=True),
        sa.Column('approver_remarks', sa.Text(), nullable=True),
        sa.Column('rejected_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rejected_at', sa.Date(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['employee_id'], ['hris_employee.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['rejected_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_hris_attendance_regularization_employee_id', 'hris_attendance_regularization', ['employee_id'])

    # ====================================
    # Create Attendance Punch Table
    # ====================================
    op.create_table(
        'hris_attendance_punch',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('punch_datetime', sa.DateTime(), nullable=False),
        sa.Column('punch_type', sa.String(10), nullable=False),
        sa.Column('source', postgresql.ENUM('BIOMETRIC', 'WEB', 'MOBILE', 'MANUAL', 'IMPORT', 'RFID', 'FACE_RECOGNITION', name='attendance_source_enum', create_type=False), nullable=False),
        sa.Column('device_id', sa.String(50), nullable=True),
        sa.Column('device_name', sa.String(100), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('latitude', sa.Numeric(10, 7), nullable=True),
        sa.Column('longitude', sa.Numeric(10, 7), nullable=True),
        sa.Column('is_processed', sa.Boolean(), default=False),
        sa.Column('is_valid', sa.Boolean(), default=True),
        sa.Column('invalid_reason', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['employee_id'], ['hris_employee.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_hris_attendance_punch_employee_id', 'hris_attendance_punch', ['employee_id'])
    op.create_index('ix_hris_attendance_punch_punch_datetime', 'hris_attendance_punch', ['punch_datetime'])

    # ====================================
    # Create Attendance Table
    # ====================================
    op.create_table(
        'hris_attendance',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attendance_date', sa.Date(), nullable=False),
        sa.Column('shift_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('scheduled_in', sa.Time(), nullable=True),
        sa.Column('scheduled_out', sa.Time(), nullable=True),
        sa.Column('first_in', sa.Time(), nullable=True),
        sa.Column('last_out', sa.Time(), nullable=True),
        sa.Column('all_punches', postgresql.JSONB(), nullable=True),
        sa.Column('status', postgresql.ENUM('PRESENT', 'ABSENT', 'HALF_DAY', 'LATE', 'ON_LEAVE', 'HOLIDAY', 'WEEK_OFF', 'ON_DUTY', 'WFH', 'COMP_OFF', name='attendance_status_enum', create_type=False), nullable=False),
        sa.Column('total_work_minutes', sa.Integer(), default=0),
        sa.Column('break_minutes', sa.Integer(), default=0),
        sa.Column('effective_work_minutes', sa.Integer(), default=0),
        sa.Column('late_minutes', sa.Integer(), default=0),
        sa.Column('early_leave_minutes', sa.Integer(), default=0),
        sa.Column('overtime_minutes', sa.Integer(), default=0),
        sa.Column('overtime_approved', sa.Boolean(), default=False),
        sa.Column('leave_application_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('leave_type_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_holiday', sa.Boolean(), default=False),
        sa.Column('holiday_name', sa.String(200), nullable=True),
        sa.Column('is_week_off', sa.Boolean(), default=False),
        sa.Column('is_regularized', sa.Boolean(), default=False),
        sa.Column('regularization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_on_duty', sa.Boolean(), default=False),
        sa.Column('on_duty_reference', sa.String(100), nullable=True),
        sa.Column('is_work_from_home', sa.Boolean(), default=False),
        sa.Column('is_processed', sa.Boolean(), default=False),
        sa.Column('is_locked', sa.Boolean(), default=False),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['employee_id'], ['hris_employee.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shift_id'], ['hris_shift.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['leave_application_id'], ['hris_leave_application.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['leave_type_id'], ['hris_leave_type.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['regularization_id'], ['hris_attendance_regularization.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('employee_id', 'attendance_date', name='uq_attendance_emp_date'),
    )
    op.create_index('ix_hris_attendance_employee_id', 'hris_attendance', ['employee_id'])
    op.create_index('ix_hris_attendance_attendance_date', 'hris_attendance', ['attendance_date'])
    op.create_index('ix_hris_attendance_status', 'hris_attendance', ['status'])

    # ====================================
    # Create Monthly Attendance Summary Table
    # ====================================
    op.create_table(
        'hris_monthly_attendance_summary',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('total_days', sa.Integer(), nullable=False),
        sa.Column('working_days', sa.Integer(), nullable=False),
        sa.Column('holidays', sa.Integer(), default=0),
        sa.Column('week_offs', sa.Integer(), default=0),
        sa.Column('present_days', sa.Numeric(5, 2), default=0),
        sa.Column('absent_days', sa.Numeric(5, 2), default=0),
        sa.Column('half_days', sa.Numeric(5, 2), default=0),
        sa.Column('late_days', sa.Integer(), default=0),
        sa.Column('early_leave_days', sa.Integer(), default=0),
        sa.Column('paid_leave_days', sa.Numeric(5, 2), default=0),
        sa.Column('unpaid_leave_days', sa.Numeric(5, 2), default=0),
        sa.Column('leave_breakdown', postgresql.JSONB(), nullable=True),
        sa.Column('on_duty_days', sa.Numeric(5, 2), default=0),
        sa.Column('wfh_days', sa.Numeric(5, 2), default=0),
        sa.Column('comp_off_availed', sa.Numeric(5, 2), default=0),
        sa.Column('total_overtime_hours', sa.Numeric(6, 2), default=0),
        sa.Column('approved_overtime_hours', sa.Numeric(6, 2), default=0),
        sa.Column('total_late_minutes', sa.Integer(), default=0),
        sa.Column('late_deduction_lop', sa.Numeric(5, 2), default=0),
        sa.Column('payable_days', sa.Numeric(5, 2), nullable=False),
        sa.Column('lop_days', sa.Numeric(5, 2), default=0),
        sa.Column('is_processed', sa.Boolean(), default=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('is_locked', sa.Boolean(), default=False),
        sa.Column('locked_at', sa.DateTime(), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['employee_id'], ['hris_employee.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('employee_id', 'year', 'month', name='uq_monthly_attendance_emp_year_month'),
    )
    op.create_index('ix_hris_monthly_attendance_summary_employee_id', 'hris_monthly_attendance_summary', ['employee_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('hris_monthly_attendance_summary')
    op.drop_table('hris_attendance')
    op.drop_table('hris_attendance_punch')
    op.drop_table('hris_attendance_regularization')
    op.drop_table('hris_leave_encashment')
    op.drop_table('hris_leave_application')
    op.drop_table('hris_leave_balance')
    op.drop_table('hris_leave_type')
    op.drop_table('hris_holiday')
    op.drop_table('hris_holiday_calendar')
    op.drop_table('hris_employee_lifecycle_event')
    op.drop_table('hris_employee_statutory')
    op.drop_table('hris_employee_experience')
    op.drop_table('hris_employee_education')
    op.drop_table('hris_employee_bank_account')
    op.drop_table('hris_employee_family')
    op.drop_table('hris_employee_document')
    op.drop_table('hris_employee')
    op.drop_table('hris_shift')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS regularization_status_enum')
    op.execute('DROP TYPE IF EXISTS attendance_source_enum')
    op.execute('DROP TYPE IF EXISTS attendance_status_enum')
    op.execute('DROP TYPE IF EXISTS leave_application_status_enum')
    op.execute('DROP TYPE IF EXISTS leave_category_enum')
    op.execute('DROP TYPE IF EXISTS holiday_type_enum')
    op.execute('DROP TYPE IF EXISTS shift_type_enum')
    op.execute('DROP TYPE IF EXISTS lifecycle_event_type_enum')
    op.execute('DROP TYPE IF EXISTS education_level_enum')
    op.execute('DROP TYPE IF EXISTS family_relation_enum')
    op.execute('DROP TYPE IF EXISTS document_type_enum')
    op.execute('DROP TYPE IF EXISTS employment_status_enum')
    op.execute('DROP TYPE IF EXISTS employment_type_enum')
    op.execute('DROP TYPE IF EXISTS marital_status_enum')
    op.execute('DROP TYPE IF EXISTS salutation_enum')
    op.execute('DROP TYPE IF EXISTS gender_enum')
