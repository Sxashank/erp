"""create_lending_los_tables

Revision ID: q5r6s7t8u9v0
Revises: p4q5r6s7t8u9
Create Date: 2026-01-12 19:00:00.000000

Create Loan Origination System (LOS) tables for NBFC lending platform.
Phase 1: Entity, KYC, Rating, Product, Application, Sanction models.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'q5r6s7t8u9v0'
down_revision: Union[str, None] = 'p4q5r6s7t8u9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types using raw SQL with DO blocks to avoid async issues
    # Entity/Borrower enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE entitytype AS ENUM ('CORPORATE', 'INDIVIDUAL', 'LLP', 'PARTNERSHIP', 'TRUST', 'HUF', 'SOCIETY', 'PROPRIETORSHIP');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE entitystatus AS ENUM ('PROSPECT', 'ACTIVE', 'INACTIVE', 'BLACKLISTED', 'SUSPENDED');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE contacttype AS ENUM ('DIRECTOR', 'PROMOTER', 'AUTHORIZED_SIGNATORY', 'KEY_MANAGERIAL_PERSON', 'CFO', 'CEO', 'COMPANY_SECRETARY', 'PARTNER', 'PROPRIETOR', 'TRUSTEE', 'GUARANTOR');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE addresstype AS ENUM ('REGISTERED', 'CORRESPONDENCE', 'PLANT', 'WAREHOUSE', 'BRANCH', 'PROJECT_SITE');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE relationtype AS ENUM ('PARENT', 'SUBSIDIARY', 'ASSOCIATE', 'GROUP_COMPANY', 'HOLDING', 'JOINT_VENTURE', 'PROMOTER', 'GUARANTOR');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE riskcategory AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE industrysector AS ENUM ('MANUFACTURING', 'SERVICES', 'INFRASTRUCTURE', 'REAL_ESTATE', 'TRADING', 'AGRICULTURE', 'HEALTHCARE', 'EDUCATION', 'IT_ITES', 'FINANCIAL_SERVICES', 'RETAIL', 'HOSPITALITY', 'TRANSPORT', 'POWER', 'TELECOM', 'OTHERS');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    # KYC enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE kycdoccategory AS ENUM ('IDENTITY', 'ADDRESS', 'FINANCIAL', 'LEGAL', 'BUSINESS', 'TAX', 'BANK');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE kycverificationstatus AS ENUM ('PENDING', 'VERIFIED', 'REJECTED', 'EXPIRED', 'RESUBMISSION_REQUIRED');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE kycverificationmethod AS ENUM ('MANUAL', 'API', 'PHYSICAL', 'VIDEO_KYC', 'AADHAAR_OTP', 'CKYC');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE ckyctransactiontype AS ENUM ('SEARCH', 'DOWNLOAD', 'UPLOAD', 'UPDATE');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE bureautype AS ENUM ('CIBIL', 'EXPERIAN', 'EQUIFAX', 'CRIF_HIGH_MARK');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE bureaupullstatus AS ENUM ('INITIATED', 'SUCCESS', 'FAILED', 'PARTIAL', 'NO_HIT');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    # Rating enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE ratinggrade AS ENUM ('AAA', 'AA_PLUS', 'AA', 'AA_MINUS', 'A_PLUS', 'A', 'A_MINUS', 'BBB_PLUS', 'BBB', 'BBB_MINUS', 'BB_PLUS', 'BB', 'BB_MINUS', 'B_PLUS', 'B', 'B_MINUS', 'C', 'D');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE ratingtype AS ENUM ('INITIAL', 'REVIEW', 'ANNUAL', 'EVENT_BASED');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE ratingstatus AS ENUM ('DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE riskcategorytype AS ENUM ('SPONSOR', 'PROJECT', 'FINANCIAL', 'INDUSTRY', 'SECURITY', 'MANAGEMENT', 'CONDUCT');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    # Product enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE productcategory AS ENUM ('TERM_LOAN', 'PROJECT_FINANCE', 'WORKING_CAPITAL', 'DEMAND_LOAN', 'OVERDRAFT', 'CASH_CREDIT', 'LETTER_OF_CREDIT', 'BANK_GUARANTEE', 'BILL_DISCOUNTING');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE interesttype AS ENUM ('FIXED', 'FLOATING');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE rateresetfrequency AS ENUM ('MONTHLY', 'QUARTERLY', 'HALF_YEARLY', 'YEARLY');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE repaymentfrequency AS ENUM ('MONTHLY', 'QUARTERLY', 'HALF_YEARLY', 'YEARLY', 'BULLET');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE repaymentmode AS ENUM ('EMI', 'STRUCTURED', 'BULLET', 'BALLOON', 'STEP_UP', 'STEP_DOWN');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE daycountconvention AS ENUM ('ACT_365', 'ACT_360', 'THIRTY_360');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE feetype AS ENUM ('PROCESSING', 'UPFRONT', 'COMMITMENT', 'PREPAYMENT', 'FORECLOSURE', 'DOCUMENTATION', 'VALUATION', 'LEGAL', 'TECHNICAL', 'INSURANCE', 'STAMP_DUTY', 'ROC_CHARGES', 'CERSAI_CHARGES');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE feecalculationtype AS ENUM ('PERCENTAGE', 'FLAT', 'SLAB');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE feecollectionstage AS ENUM ('APPLICATION', 'SANCTION', 'DISBURSEMENT', 'PREPAYMENT', 'CLOSURE');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE documentcategory AS ENUM ('KYC', 'FINANCIAL', 'LEGAL', 'PROJECT', 'SECURITY', 'INSURANCE', 'REGULATORY');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE documentstage AS ENUM ('APPLICATION', 'APPRAISAL', 'SANCTION', 'PRE_DISBURSEMENT', 'POST_DISBURSEMENT', 'ONGOING');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    # Application enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE applicationstage AS ENUM ('LEAD', 'APPLICATION', 'APPRAISAL', 'SANCTION', 'POST_SANCTION', 'DISBURSED', 'CLOSED');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE applicationstatus AS ENUM ('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'ADDITIONAL_INFO_REQUIRED', 'SANCTIONED', 'REJECTED', 'WITHDRAWN', 'CANCELLED', 'EXPIRED');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE appraisaltype AS ENUM ('TECHNICAL', 'FINANCIAL', 'LEGAL', 'MARKET');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE technicalfeasibility AS ENUM ('FEASIBLE', 'CONDITIONAL', 'NOT_FEASIBLE');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE appraisalrecommendation AS ENUM ('PROCEED', 'PROCEED_WITH_CONDITIONS', 'REJECT', 'HOLD');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE milestonestatus AS ENUM ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'DELAYED', 'WAIVED');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    # Sanction enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE sanctionstatus AS ENUM ('DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'ACTIVE', 'ACCEPTED', 'EXPIRED', 'CANCELLED', 'SUPERSEDED');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE conditiontype AS ENUM ('PRE_DISBURSEMENT', 'POST_DISBURSEMENT', 'ONGOING', 'EVENT_BASED');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE conditioncategory AS ENUM ('LEGAL', 'FINANCIAL', 'SECURITY', 'REGULATORY', 'OPERATIONAL', 'PROJECT');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE conditioncompliancestatus AS ENUM ('PENDING', 'COMPLIED', 'WAIVED', 'DEFERRED', 'NOT_APPLICABLE');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE securitycategory AS ENUM ('PRIMARY', 'COLLATERAL', 'GUARANTEE');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE securitytype AS ENUM ('IMMOVABLE_PROPERTY', 'MOVABLE_PROPERTY', 'PLANT_MACHINERY', 'INVENTORY', 'RECEIVABLES', 'FIXED_DEPOSIT', 'SHARES', 'DEBENTURES', 'GOVERNMENT_SECURITIES', 'VEHICLE', 'GOLD', 'PERSONAL_GUARANTEE', 'CORPORATE_GUARANTEE', 'BANK_GUARANTEE');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE chargetype AS ENUM ('FIRST', 'SECOND', 'PARI_PASSU', 'SUBSERVIENT');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE securitystatus AS ENUM ('PROPOSED', 'CREATED', 'REGISTERED', 'RELEASED', 'SUBSTITUTED');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # ============================================================================
    # ENTITY/BORROWER TABLES
    # ============================================================================

    # los_entity - Borrower master
    op.create_table(
        'los_entity',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_code', sa.String(50), nullable=False),
        sa.Column('entity_type', postgresql.ENUM(name='entitytype', create_type=False), nullable=False),
        sa.Column('legal_name', sa.String(500), nullable=False),
        sa.Column('trade_name', sa.String(500), nullable=True),
        sa.Column('pan', sa.String(10), nullable=False),
        sa.Column('cin', sa.String(21), nullable=True),
        sa.Column('llpin', sa.String(20), nullable=True),
        sa.Column('gstin', sa.String(15), nullable=True),
        sa.Column('udyam_number', sa.String(25), nullable=True),
        sa.Column('tan', sa.String(10), nullable=True),
        sa.Column('ckyc_number', sa.String(14), nullable=True),
        sa.Column('kyc_verified', sa.Boolean, default=False, nullable=False),
        sa.Column('kyc_verified_date', sa.Date, nullable=True),
        sa.Column('date_of_incorporation', sa.Date, nullable=True),
        sa.Column('date_of_birth', sa.Date, nullable=True),
        sa.Column('place_of_incorporation', sa.String(200), nullable=True),
        sa.Column('country_of_incorporation', sa.String(3), default='IND', nullable=False),
        sa.Column('industry_sector', postgresql.ENUM(name='industrysector', create_type=False), nullable=True),
        sa.Column('industry_sub_sector', sa.String(200), nullable=True),
        sa.Column('nic_code', sa.String(10), nullable=True),
        sa.Column('risk_category', postgresql.ENUM(name='riskcategory', create_type=False), default='MEDIUM', nullable=False),
        sa.Column('internal_rating', sa.String(10), nullable=True),
        sa.Column('external_rating', sa.String(50), nullable=True),
        sa.Column('external_rating_agency', sa.String(50), nullable=True),
        sa.Column('authorized_capital', sa.Numeric(20, 2), nullable=True),
        sa.Column('paid_up_capital', sa.Numeric(20, 2), nullable=True),
        sa.Column('net_worth', sa.Numeric(20, 2), nullable=True),
        sa.Column('turnover', sa.Numeric(20, 2), nullable=True),
        sa.Column('employee_count', sa.Integer, nullable=True),
        sa.Column('primary_email', sa.String(255), nullable=True),
        sa.Column('primary_phone', sa.String(20), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),
        sa.Column('relationship_manager_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('status', postgresql.ENUM(name='entitystatus', create_type=False), default='PROSPECT', nullable=False),
        sa.Column('onboarding_date', sa.Date, nullable=True),
        sa.Column('blacklist_reason', sa.Text, nullable=True),
        sa.Column('remarks', sa.Text, nullable=True),
        sa.Column('extra_data', postgresql.JSONB, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('organization_id', 'entity_code', name='uq_entity_org_code'),
        sa.UniqueConstraint('organization_id', 'pan', name='uq_entity_org_pan'),
        sa.CheckConstraint('LENGTH(pan) = 10', name='ck_entity_pan_length'),
    )
    op.create_index('ix_los_entity_org', 'los_entity', ['organization_id'])
    op.create_index('ix_los_entity_code', 'los_entity', ['entity_code'])
    op.create_index('ix_los_entity_type', 'los_entity', ['entity_type'])
    op.create_index('ix_los_entity_pan', 'los_entity', ['pan'])
    op.create_index('ix_los_entity_ckyc', 'los_entity', ['ckyc_number'])
    op.create_index('ix_los_entity_status', 'los_entity', ['status'])
    op.create_index('ix_los_entity_org_status', 'los_entity', ['organization_id', 'status'])
    op.create_index('ix_los_entity_org_type', 'los_entity', ['organization_id', 'entity_type'])
    op.create_index('ix_los_entity_rm', 'los_entity', ['relationship_manager_id'])

    # los_entity_contact - Key contacts
    op.create_table(
        'los_entity_contact',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contact_type', postgresql.ENUM(name='contacttype', create_type=False), nullable=False),
        sa.Column('designation', sa.String(200), nullable=True),
        sa.Column('is_primary', sa.Boolean, default=False, nullable=False),
        sa.Column('is_authorized_signatory', sa.Boolean, default=False, nullable=False),
        sa.Column('salutation', sa.String(10), nullable=True),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('middle_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('date_of_birth', sa.Date, nullable=True),
        sa.Column('gender', sa.String(10), nullable=True),
        sa.Column('nationality', sa.String(50), default='Indian', nullable=False),
        sa.Column('pan', sa.String(10), nullable=True),
        sa.Column('aadhaar_masked', sa.String(12), nullable=True),
        sa.Column('din', sa.String(8), nullable=True),
        sa.Column('dpin', sa.String(8), nullable=True),
        sa.Column('passport_number', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('mobile', sa.String(20), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('address_line1', sa.String(500), nullable=True),
        sa.Column('address_line2', sa.String(500), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('pincode', sa.String(10), nullable=True),
        sa.Column('country', sa.String(50), default='India', nullable=False),
        sa.Column('shareholding_percentage', sa.Numeric(5, 2), nullable=True),
        sa.Column('shareholding_value', sa.Numeric(20, 2), nullable=True),
        sa.Column('appointment_date', sa.Date, nullable=True),
        sa.Column('cessation_date', sa.Date, nullable=True),
        sa.Column('kyc_verified', sa.Boolean, default=False, nullable=False),
        sa.Column('ckyc_number', sa.String(14), nullable=True),
        sa.Column('remarks', sa.Text, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
    )
    op.create_index('ix_los_entity_contact_entity', 'los_entity_contact', ['entity_id'])
    op.create_index('ix_los_entity_contact_entity_type', 'los_entity_contact', ['entity_id', 'contact_type'])
    op.create_index('ix_los_entity_contact_pan', 'los_entity_contact', ['pan'])

    # los_entity_address - Addresses
    op.create_table(
        'los_entity_address',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity.id', ondelete='CASCADE'), nullable=False),
        sa.Column('address_type', postgresql.ENUM(name='addresstype', create_type=False), nullable=False),
        sa.Column('is_primary', sa.Boolean, default=False, nullable=False),
        sa.Column('address_line1', sa.String(500), nullable=False),
        sa.Column('address_line2', sa.String(500), nullable=True),
        sa.Column('address_line3', sa.String(500), nullable=True),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('district', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=False),
        sa.Column('state_code', sa.String(2), nullable=True),
        sa.Column('pincode', sa.String(10), nullable=False),
        sa.Column('country', sa.String(50), default='India', nullable=False),
        sa.Column('country_code', sa.String(3), default='IND', nullable=False),
        sa.Column('latitude', sa.Numeric(10, 7), nullable=True),
        sa.Column('longitude', sa.Numeric(10, 7), nullable=True),
        sa.Column('contact_person', sa.String(200), nullable=True),
        sa.Column('contact_phone', sa.String(20), nullable=True),
        sa.Column('is_verified', sa.Boolean, default=False, nullable=False),
        sa.Column('verified_date', sa.Date, nullable=True),
        sa.Column('verified_by', sa.String(200), nullable=True),
        sa.Column('ownership_type', sa.String(50), nullable=True),
        sa.Column('occupied_since', sa.Date, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
    )
    op.create_index('ix_los_entity_address_entity', 'los_entity_address', ['entity_id'])
    op.create_index('ix_los_entity_address_entity_type', 'los_entity_address', ['entity_id', 'address_type'])

    # los_entity_bank_account - Bank accounts
    op.create_table(
        'los_entity_bank_account',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity.id', ondelete='CASCADE'), nullable=False),
        sa.Column('bank_name', sa.String(200), nullable=False),
        sa.Column('branch_name', sa.String(200), nullable=False),
        sa.Column('branch_address', sa.String(500), nullable=True),
        sa.Column('ifsc_code', sa.String(11), nullable=False),
        sa.Column('micr_code', sa.String(9), nullable=True),
        sa.Column('account_number', sa.String(30), nullable=False),
        sa.Column('account_type', sa.String(50), nullable=False),
        sa.Column('account_holder_name', sa.String(200), nullable=False),
        sa.Column('is_primary', sa.Boolean, default=False, nullable=False),
        sa.Column('is_disbursement_account', sa.Boolean, default=False, nullable=False),
        sa.Column('is_collection_account', sa.Boolean, default=False, nullable=False),
        sa.Column('is_escrow_account', sa.Boolean, default=False, nullable=False),
        sa.Column('is_verified', sa.Boolean, default=False, nullable=False),
        sa.Column('verified_date', sa.Date, nullable=True),
        sa.Column('verification_method', sa.String(50), nullable=True),
        sa.Column('penny_drop_reference', sa.String(100), nullable=True),
        sa.Column('nach_registered', sa.Boolean, default=False, nullable=False),
        sa.Column('nach_umrn', sa.String(50), nullable=True),
        sa.Column('nach_max_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('nach_start_date', sa.Date, nullable=True),
        sa.Column('nach_end_date', sa.Date, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('entity_id', 'account_number', 'ifsc_code', name='uq_entity_bank_account'),
        sa.CheckConstraint('LENGTH(ifsc_code) = 11', name='ck_bank_ifsc_length'),
    )
    op.create_index('ix_los_entity_bank_entity', 'los_entity_bank_account', ['entity_id'])
    op.create_index('ix_los_entity_bank_ifsc', 'los_entity_bank_account', ['ifsc_code'])

    # los_entity_relation - Entity relationships
    op.create_table(
        'los_entity_relation',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity.id', ondelete='CASCADE'), nullable=False),
        sa.Column('related_entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity.id', ondelete='SET NULL'), nullable=True),
        sa.Column('relation_type', postgresql.ENUM(name='relationtype', create_type=False), nullable=False),
        sa.Column('related_entity_name', sa.String(500), nullable=True),
        sa.Column('related_entity_pan', sa.String(10), nullable=True),
        sa.Column('related_entity_cin', sa.String(21), nullable=True),
        sa.Column('shareholding_percentage', sa.Numeric(5, 2), nullable=True),
        sa.Column('voting_percentage', sa.Numeric(5, 2), nullable=True),
        sa.Column('guarantee_amount', sa.Numeric(20, 2), nullable=True),
        sa.Column('guarantee_type', sa.String(50), nullable=True),
        sa.Column('effective_from', sa.Date, nullable=True),
        sa.Column('effective_to', sa.Date, nullable=True),
        sa.Column('remarks', sa.Text, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
    )
    op.create_index('ix_los_entity_relation_entity', 'los_entity_relation', ['entity_id'])
    op.create_index('ix_los_entity_relation_type', 'los_entity_relation', ['entity_id', 'relation_type'])

    # los_entity_financial - Annual financials
    op.create_table(
        'los_entity_financial',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity.id', ondelete='CASCADE'), nullable=False),
        sa.Column('financial_year', sa.String(10), nullable=False),
        sa.Column('is_audited', sa.Boolean, default=False, nullable=False),
        sa.Column('audit_date', sa.Date, nullable=True),
        sa.Column('auditor_name', sa.String(200), nullable=True),
        # Income statement
        sa.Column('revenue', sa.Numeric(20, 2), nullable=True),
        sa.Column('other_income', sa.Numeric(20, 2), nullable=True),
        sa.Column('total_income', sa.Numeric(20, 2), nullable=True),
        sa.Column('cost_of_goods_sold', sa.Numeric(20, 2), nullable=True),
        sa.Column('gross_profit', sa.Numeric(20, 2), nullable=True),
        sa.Column('operating_expenses', sa.Numeric(20, 2), nullable=True),
        sa.Column('ebitda', sa.Numeric(20, 2), nullable=True),
        sa.Column('depreciation', sa.Numeric(20, 2), nullable=True),
        sa.Column('interest_expense', sa.Numeric(20, 2), nullable=True),
        sa.Column('profit_before_tax', sa.Numeric(20, 2), nullable=True),
        sa.Column('tax_expense', sa.Numeric(20, 2), nullable=True),
        sa.Column('net_profit', sa.Numeric(20, 2), nullable=True),
        # Balance sheet - Assets
        sa.Column('total_assets', sa.Numeric(20, 2), nullable=True),
        sa.Column('fixed_assets', sa.Numeric(20, 2), nullable=True),
        sa.Column('current_assets', sa.Numeric(20, 2), nullable=True),
        sa.Column('inventory', sa.Numeric(20, 2), nullable=True),
        sa.Column('receivables', sa.Numeric(20, 2), nullable=True),
        sa.Column('cash_and_equivalents', sa.Numeric(20, 2), nullable=True),
        # Balance sheet - Liabilities
        sa.Column('total_liabilities', sa.Numeric(20, 2), nullable=True),
        sa.Column('share_capital', sa.Numeric(20, 2), nullable=True),
        sa.Column('reserves_surplus', sa.Numeric(20, 2), nullable=True),
        sa.Column('net_worth', sa.Numeric(20, 2), nullable=True),
        sa.Column('long_term_debt', sa.Numeric(20, 2), nullable=True),
        sa.Column('short_term_debt', sa.Numeric(20, 2), nullable=True),
        sa.Column('total_debt', sa.Numeric(20, 2), nullable=True),
        sa.Column('current_liabilities', sa.Numeric(20, 2), nullable=True),
        sa.Column('payables', sa.Numeric(20, 2), nullable=True),
        # Cash flow
        sa.Column('operating_cash_flow', sa.Numeric(20, 2), nullable=True),
        sa.Column('investing_cash_flow', sa.Numeric(20, 2), nullable=True),
        sa.Column('financing_cash_flow', sa.Numeric(20, 2), nullable=True),
        sa.Column('net_cash_flow', sa.Numeric(20, 2), nullable=True),
        # Key ratios
        sa.Column('current_ratio', sa.Numeric(10, 2), nullable=True),
        sa.Column('debt_equity_ratio', sa.Numeric(10, 2), nullable=True),
        sa.Column('interest_coverage_ratio', sa.Numeric(10, 2), nullable=True),
        sa.Column('dscr', sa.Numeric(10, 2), nullable=True),
        sa.Column('net_profit_margin', sa.Numeric(10, 2), nullable=True),
        sa.Column('return_on_equity', sa.Numeric(10, 2), nullable=True),
        sa.Column('return_on_assets', sa.Numeric(10, 2), nullable=True),
        sa.Column('remarks', sa.Text, nullable=True),
        sa.Column('raw_data', postgresql.JSONB, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('entity_id', 'financial_year', name='uq_entity_financial_year'),
    )
    op.create_index('ix_los_entity_financial_entity', 'los_entity_financial', ['entity_id'])
    op.create_index('ix_los_entity_financial_year', 'los_entity_financial', ['entity_id', 'financial_year'])

    # Print progress message
    print("Created entity/borrower tables")

    # ============================================================================
    # KYC TABLES
    # ============================================================================

    # los_kyc_document_type - KYC document types master
    op.create_table(
        'los_kyc_document_type',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', postgresql.ENUM(name='kycdoccategory', create_type=False), nullable=False),
        sa.Column('applicable_for_individual', sa.Boolean, default=True, nullable=False),
        sa.Column('applicable_for_corporate', sa.Boolean, default=True, nullable=False),
        sa.Column('applicable_for_contact', sa.Boolean, default=False, nullable=False),
        sa.Column('supports_api_verification', sa.Boolean, default=False, nullable=False),
        sa.Column('verification_api_code', sa.String(50), nullable=True),
        sa.Column('supports_ocr', sa.Boolean, default=False, nullable=False),
        sa.Column('has_expiry', sa.Boolean, default=False, nullable=False),
        sa.Column('default_validity_days', sa.Integer, nullable=True),
        sa.Column('is_mandatory', sa.Boolean, default=False, nullable=False),
        sa.Column('mandatory_for_categories', postgresql.JSONB, nullable=True),
        sa.Column('allowed_file_types', postgresql.JSONB, default=['pdf', 'jpg', 'jpeg', 'png'], nullable=False),
        sa.Column('max_file_size_mb', sa.Integer, default=5, nullable=False),
        sa.Column('display_order', sa.Integer, default=0, nullable=False),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('organization_id', 'code', name='uq_kyc_doc_type_org_code'),
    )
    op.create_index('ix_los_kyc_doc_type_org', 'los_kyc_document_type', ['organization_id'])
    op.create_index('ix_los_kyc_doc_type_code', 'los_kyc_document_type', ['code'])
    op.create_index('ix_los_kyc_doc_type_org_cat', 'los_kyc_document_type', ['organization_id', 'category'])

    # los_entity_kyc_document - Entity KYC documents
    op.create_table(
        'los_entity_kyc_document',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_type_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_kyc_document_type.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity_contact.id', ondelete='CASCADE'), nullable=True),
        sa.Column('document_number', sa.String(100), nullable=True),
        sa.Column('document_name', sa.String(200), nullable=True),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size_bytes', sa.Integer, nullable=True),
        sa.Column('file_mime_type', sa.String(100), nullable=True),
        sa.Column('file_hash', sa.String(64), nullable=True),
        sa.Column('issue_date', sa.Date, nullable=True),
        sa.Column('expiry_date', sa.Date, nullable=True),
        sa.Column('verification_status', postgresql.ENUM(name='kycverificationstatus', create_type=False), default='PENDING', nullable=False),
        sa.Column('verification_method', postgresql.ENUM(name='kycverificationmethod', create_type=False), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),
        sa.Column('resubmission_count', sa.Integer, default=0, nullable=False),
        sa.Column('api_verification_response', postgresql.JSONB, nullable=True),
        sa.Column('api_verification_reference', sa.String(100), nullable=True),
        sa.Column('ocr_extracted_data', postgresql.JSONB, nullable=True),
        sa.Column('ocr_confidence_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('remarks', sa.Text, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
    )
    op.create_index('ix_los_entity_kyc_doc_entity', 'los_entity_kyc_document', ['entity_id'])
    op.create_index('ix_los_entity_kyc_doc_type', 'los_entity_kyc_document', ['document_type_id'])
    op.create_index('ix_los_entity_kyc_doc_entity_type', 'los_entity_kyc_document', ['entity_id', 'document_type_id'])
    op.create_index('ix_los_entity_kyc_doc_status', 'los_entity_kyc_document', ['entity_id', 'verification_status'])
    op.create_index('ix_los_entity_kyc_doc_expiry', 'los_entity_kyc_document', ['expiry_date'])
    op.create_index('ix_los_entity_kyc_doc_number', 'los_entity_kyc_document', ['document_number'])

    # los_ckyc_transaction - CKYC transaction log
    op.create_table(
        'los_ckyc_transaction',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity.id', ondelete='SET NULL'), nullable=True),
        sa.Column('transaction_type', postgresql.ENUM(name='ckyctransactiontype', create_type=False), nullable=False),
        sa.Column('search_pan', sa.String(10), nullable=True),
        sa.Column('search_name', sa.String(200), nullable=True),
        sa.Column('search_dob', sa.Date, nullable=True),
        sa.Column('ckyc_number', sa.String(14), nullable=True),
        sa.Column('ckyc_status', sa.String(50), nullable=True),
        sa.Column('transaction_id', sa.String(100), nullable=True),
        sa.Column('request_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('response_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_success', sa.Boolean, default=False, nullable=False),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('request_data', postgresql.JSONB, nullable=True),
        sa.Column('response_data', postgresql.JSONB, nullable=True),
        sa.Column('downloaded_file_path', sa.String(500), nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
    )
    op.create_index('ix_los_ckyc_txn_org', 'los_ckyc_transaction', ['organization_id'])
    op.create_index('ix_los_ckyc_txn_org_type', 'los_ckyc_transaction', ['organization_id', 'transaction_type'])
    op.create_index('ix_los_ckyc_txn_pan', 'los_ckyc_transaction', ['search_pan'])
    op.create_index('ix_los_ckyc_txn_ckyc', 'los_ckyc_transaction', ['ckyc_number'])

    # los_bureau_pull - Bureau pull history
    op.create_table(
        'los_bureau_pull',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity_contact.id', ondelete='CASCADE'), nullable=True),
        sa.Column('bureau_type', postgresql.ENUM(name='bureautype', create_type=False), nullable=False),
        sa.Column('report_type', sa.String(50), default='CONSUMER', nullable=False),
        sa.Column('request_reference', sa.String(100), nullable=False),
        sa.Column('request_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('input_pan', sa.String(10), nullable=True),
        sa.Column('input_name', sa.String(200), nullable=True),
        sa.Column('input_dob', sa.Date, nullable=True),
        sa.Column('input_mobile', sa.String(15), nullable=True),
        sa.Column('input_address', sa.Text, nullable=True),
        sa.Column('status', postgresql.ENUM(name='bureaupullstatus', create_type=False), default='INITIATED', nullable=False),
        sa.Column('response_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('bureau_reference', sa.String(100), nullable=True),
        sa.Column('bureau_report_id', sa.String(100), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('consent_reference', sa.String(100), nullable=True),
        sa.Column('consent_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('purpose', sa.String(100), default='LOAN_APPLICATION', nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
    )
    op.create_index('ix_los_bureau_pull_org', 'los_bureau_pull', ['organization_id'])
    op.create_index('ix_los_bureau_pull_entity', 'los_bureau_pull', ['entity_id'])
    op.create_index('ix_los_bureau_pull_entity_bureau', 'los_bureau_pull', ['entity_id', 'bureau_type'])
    op.create_index('ix_los_bureau_pull_org_status', 'los_bureau_pull', ['organization_id', 'status'])
    op.create_index('ix_los_bureau_pull_ref', 'los_bureau_pull', ['request_reference'])

    # los_bureau_report - Bureau report data
    op.create_table(
        'los_bureau_report',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('bureau_pull_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_bureau_pull.id', ondelete='CASCADE'), nullable=False),
        sa.Column('report_file_path', sa.String(500), nullable=True),
        sa.Column('report_format', sa.String(10), default='JSON', nullable=False),
        sa.Column('credit_score', sa.Integer, nullable=True),
        sa.Column('score_version', sa.String(50), nullable=True),
        sa.Column('score_date', sa.Date, nullable=True),
        sa.Column('score_factors', postgresql.JSONB, nullable=True),
        sa.Column('total_accounts', sa.Integer, nullable=True),
        sa.Column('active_accounts', sa.Integer, nullable=True),
        sa.Column('closed_accounts', sa.Integer, nullable=True),
        sa.Column('overdue_accounts', sa.Integer, nullable=True),
        sa.Column('default_accounts', sa.Integer, nullable=True),
        sa.Column('written_off_accounts', sa.Integer, nullable=True),
        sa.Column('total_sanctioned_amount', sa.Numeric(20, 2), nullable=True),
        sa.Column('total_outstanding', sa.Numeric(20, 2), nullable=True),
        sa.Column('total_overdue', sa.Numeric(20, 2), nullable=True),
        sa.Column('total_written_off', sa.Numeric(20, 2), nullable=True),
        sa.Column('highest_dpd_last_12m', sa.Integer, nullable=True),
        sa.Column('highest_dpd_last_24m', sa.Integer, nullable=True),
        sa.Column('total_enquiries', sa.Integer, nullable=True),
        sa.Column('enquiries_last_30d', sa.Integer, nullable=True),
        sa.Column('enquiries_last_90d', sa.Integer, nullable=True),
        sa.Column('enquiries_last_6m', sa.Integer, nullable=True),
        sa.Column('enquiries_last_12m', sa.Integer, nullable=True),
        sa.Column('payment_history_months', sa.Integer, nullable=True),
        sa.Column('on_time_payments_pct', sa.Numeric(5, 2), nullable=True),
        sa.Column('account_details', postgresql.JSONB, nullable=True),
        sa.Column('enquiry_details', postgresql.JSONB, nullable=True),
        sa.Column('dpd_history', postgresql.JSONB, nullable=True),
        sa.Column('raw_report_data', postgresql.JSONB, nullable=True),
        sa.Column('has_fraud_indicator', sa.Boolean, default=False, nullable=False),
        sa.Column('has_suit_filed', sa.Boolean, default=False, nullable=False),
        sa.Column('has_wilful_default', sa.Boolean, default=False, nullable=False),
        sa.Column('is_cibil_defaulter', sa.Boolean, default=False, nullable=False),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
    )
    op.create_index('ix_los_bureau_report_pull', 'los_bureau_report', ['bureau_pull_id'])
    op.create_index('ix_los_bureau_report_score', 'los_bureau_report', ['credit_score'])

    print("Created KYC tables")


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('los_bureau_report')
    op.drop_table('los_bureau_pull')
    op.drop_table('los_ckyc_transaction')
    op.drop_table('los_entity_kyc_document')
    op.drop_table('los_kyc_document_type')
    op.drop_table('los_entity_financial')
    op.drop_table('los_entity_relation')
    op.drop_table('los_entity_bank_account')
    op.drop_table('los_entity_address')
    op.drop_table('los_entity_contact')
    op.drop_table('los_entity')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS securitystatus")
    op.execute("DROP TYPE IF EXISTS chargetype")
    op.execute("DROP TYPE IF EXISTS securitytype")
    op.execute("DROP TYPE IF EXISTS securitycategory")
    op.execute("DROP TYPE IF EXISTS conditioncompliancestatus")
    op.execute("DROP TYPE IF EXISTS conditioncategory")
    op.execute("DROP TYPE IF EXISTS conditiontype")
    op.execute("DROP TYPE IF EXISTS sanctionstatus")
    op.execute("DROP TYPE IF EXISTS milestonestatus")
    op.execute("DROP TYPE IF EXISTS appraisalrecommendation")
    op.execute("DROP TYPE IF EXISTS technicalfeasibility")
    op.execute("DROP TYPE IF EXISTS appraisaltype")
    op.execute("DROP TYPE IF EXISTS applicationstatus")
    op.execute("DROP TYPE IF EXISTS applicationstage")
    op.execute("DROP TYPE IF EXISTS documentstage")
    op.execute("DROP TYPE IF EXISTS documentcategory")
    op.execute("DROP TYPE IF EXISTS feecollectionstage")
    op.execute("DROP TYPE IF EXISTS feecalculationtype")
    op.execute("DROP TYPE IF EXISTS feetype")
    op.execute("DROP TYPE IF EXISTS daycountconvention")
    op.execute("DROP TYPE IF EXISTS repaymentmode")
    op.execute("DROP TYPE IF EXISTS repaymentfrequency")
    op.execute("DROP TYPE IF EXISTS rateresetfrequency")
    op.execute("DROP TYPE IF EXISTS interesttype")
    op.execute("DROP TYPE IF EXISTS productcategory")
    op.execute("DROP TYPE IF EXISTS riskcategorytype")
    op.execute("DROP TYPE IF EXISTS ratingstatus")
    op.execute("DROP TYPE IF EXISTS ratingtype")
    op.execute("DROP TYPE IF EXISTS ratinggrade")
    op.execute("DROP TYPE IF EXISTS bureaupullstatus")
    op.execute("DROP TYPE IF EXISTS bureautype")
    op.execute("DROP TYPE IF EXISTS ckyctransactiontype")
    op.execute("DROP TYPE IF EXISTS kycverificationmethod")
    op.execute("DROP TYPE IF EXISTS kycverificationstatus")
    op.execute("DROP TYPE IF EXISTS kycdoccategory")
    op.execute("DROP TYPE IF EXISTS industrysector")
    op.execute("DROP TYPE IF EXISTS riskcategory")
    op.execute("DROP TYPE IF EXISTS relationtype")
    op.execute("DROP TYPE IF EXISTS addresstype")
    op.execute("DROP TYPE IF EXISTS contacttype")
    op.execute("DROP TYPE IF EXISTS entitystatus")
    op.execute("DROP TYPE IF EXISTS entitytype")
