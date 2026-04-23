"""create_lending_lms_tables

Revision ID: t8u9v0w1x2y3
Revises: s7t8u9v0w1x2
Create Date: 2026-01-13 10:00:00.000000

Create Loan Management System (LMS) tables - Phase 2.
Loan Accounting, Disbursements, Schedules, Receipts, NPA tracking.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 't8u9v0w1x2y3'
down_revision: Union[str, None] = 's7t8u9v0w1x2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================================================
    # CREATE ENUMS FOR PHASE 2
    # ============================================================================

    # Loan Account Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE loanaccountstatus AS ENUM ('CREATED', 'ACTIVE', 'DORMANT', 'FROZEN', 'CLOSED', 'WRITTEN_OFF', 'RECALLED');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # Disbursement Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE disbursementstatus AS ENUM ('PENDING', 'APPROVED', 'PROCESSED', 'REJECTED', 'CANCELLED', 'FAILED', 'REVERSED');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # Disbursement Mode
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE disbursementmode AS ENUM ('RTGS', 'NEFT', 'IMPS', 'CHEQUE', 'DD', 'DIRECT_CREDIT', 'ESCROW');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # Schedule Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE scheduletype AS ENUM ('ORIGINAL', 'RESCHEDULED', 'RESTRUCTURED', 'REVISED');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # Installment Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE installmenttype AS ENUM ('PRINCIPAL', 'INTEREST', 'EMI', 'MORATORIUM_INTEREST', 'PENAL_INTEREST');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # Installment Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE installmentstatus AS ENUM ('NOT_DUE', 'DUE', 'PARTIALLY_PAID', 'PAID', 'OVERDUE', 'WAIVED', 'WRITTEN_OFF');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # Accrual Category
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE accrualcategory AS ENUM ('INTEREST', 'PENAL_INTEREST', 'FEE', 'COMMITMENT_FEE');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # Accrual Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE accrualstatus AS ENUM ('ACCRUED', 'REVERSED', 'SUSPENDED', 'WRITTEN_OFF');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # Asset Classification
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE assetclassification AS ENUM ('STANDARD', 'SMA_0', 'SMA_1', 'SMA_2', 'NPA', 'SUBSTANDARD',
            'DOUBTFUL_1', 'DOUBTFUL_2', 'DOUBTFUL_3', 'LOSS');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # Receipt Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE receipttype AS ENUM ('REGULAR', 'PREPAYMENT', 'FORECLOSURE', 'SUBVENTION',
            'INSURANCE_CLAIM', 'LEGAL_RECOVERY', 'OTS_SETTLEMENT', 'WRITE_BACK');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # Receipt Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE receiptstatus AS ENUM ('PENDING', 'ALLOCATED', 'REVERSED', 'BOUNCED');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # Receipt Mode
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE receiptmode AS ENUM ('CASH', 'CHEQUE', 'DD', 'RTGS', 'NEFT', 'IMPS', 'UPI', 'NACH', 'AUTO_DEBIT', 'ADJUSTMENT');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # Allocation Priority
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE allocationpriority AS ENUM ('FIFO', 'LIFO', 'PROPORTIONATE', 'CUSTOM');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # Allocation Component
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE allocationcomponent AS ENUM ('CHARGES', 'PENAL_INTEREST', 'INTEREST', 'PRINCIPAL', 'EMI');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # Adjustment Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE adjustmenttype AS ENUM ('RATE_CHANGE', 'TENURE_CHANGE', 'EMI_CHANGE', 'MORATORIUM',
            'RESCHEDULE', 'RESTRUCTURE', 'WRITE_OFF', 'WAIVER');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # Waiver Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE waivertype AS ENUM ('INTEREST', 'PENAL_INTEREST', 'CHARGES', 'PRINCIPAL', 'FULL');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # Provisioning Category
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE provisioningcategory AS ENUM ('STANDARD', 'SUBSTANDARD_SECURED', 'SUBSTANDARD_UNSECURED',
            'DOUBTFUL_1', 'DOUBTFUL_2', 'DOUBTFUL_3', 'LOSS');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # Mandate Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE mandatestatus AS ENUM ('INITIATED', 'REGISTERED', 'ACTIVE', 'SUSPENDED', 'CANCELLED', 'REJECTED', 'EXPIRED');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # GL Entry Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE glentrytype AS ENUM ('DISBURSEMENT', 'ACCRUAL', 'RECEIPT', 'REVERSAL',
            'PROVISIONING', 'WRITE_OFF', 'WRITE_BACK', 'ADJUSTMENT');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # ============================================================================
    # LOAN ACCOUNT TABLE
    # ============================================================================
    op.create_table(
        'lms_loan_account',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sanction_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_loan_sanction.id', ondelete='RESTRICT'), nullable=False, unique=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_loan_product.id', ondelete='RESTRICT'), nullable=False),
        # Account identification
        sa.Column('loan_account_number', sa.String(50), nullable=False, unique=True),
        sa.Column('loan_reference_number', sa.String(50), nullable=True),
        # Dates
        sa.Column('account_open_date', sa.Date, nullable=False),
        sa.Column('first_disbursement_date', sa.Date, nullable=True),
        sa.Column('last_disbursement_date', sa.Date, nullable=True),
        sa.Column('repayment_start_date', sa.Date, nullable=True),
        sa.Column('maturity_date', sa.Date, nullable=True),
        sa.Column('closure_date', sa.Date, nullable=True),
        # Sanctioned terms
        sa.Column('sanctioned_amount', sa.Numeric(20, 2), nullable=False),
        sa.Column('tenure_months', sa.Integer, nullable=False),
        sa.Column('moratorium_months', sa.Integer, default=0, nullable=False),
        sa.Column('moratorium_end_date', sa.Date, nullable=True),
        # Interest terms
        sa.Column('interest_type', postgresql.ENUM(name='interesttype', create_type=False), nullable=False),
        sa.Column('base_rate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_interest_rate.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('current_base_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('spread_bps', sa.Integer, default=0, nullable=False),
        sa.Column('current_interest_rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('rate_reset_frequency', postgresql.ENUM(name='rateresetfrequency', create_type=False), nullable=True),
        sa.Column('next_rate_reset_date', sa.Date, nullable=True),
        sa.Column('last_rate_reset_date', sa.Date, nullable=True),
        sa.Column('penal_interest_rate', sa.Numeric(5, 2), default=2.00, nullable=False),
        # Repayment terms
        sa.Column('repayment_frequency', postgresql.ENUM(name='repaymentfrequency', create_type=False), nullable=False),
        sa.Column('repayment_mode', postgresql.ENUM(name='repaymentmode', create_type=False), nullable=False),
        sa.Column('day_count_convention', postgresql.ENUM(name='daycountconvention', create_type=False), default='ACT_365', nullable=False),
        sa.Column('installment_day', sa.Integer, default=1, nullable=False),
        sa.Column('current_emi_amount', sa.Numeric(20, 2), nullable=True),
        # Outstanding balances
        sa.Column('total_disbursed_amount', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('undisbursed_amount', sa.Numeric(20, 2), nullable=False),
        sa.Column('principal_outstanding', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('interest_outstanding', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('interest_overdue', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('principal_overdue', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('penal_interest_outstanding', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('charges_outstanding', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('total_outstanding', sa.Numeric(20, 2), default=0, nullable=False),
        # Cumulative totals
        sa.Column('total_principal_received', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('total_interest_received', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('total_penal_interest_received', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('total_charges_received', sa.Numeric(20, 2), default=0, nullable=False),
        # Accrual tracking
        sa.Column('interest_accrued_not_due', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('last_accrual_date', sa.Date, nullable=True),
        sa.Column('accrual_suspended', sa.Boolean, default=False, nullable=False),
        sa.Column('accrual_suspension_date', sa.Date, nullable=True),
        sa.Column('suspended_interest', sa.Numeric(20, 2), default=0, nullable=False),
        # DPD and NPA tracking
        sa.Column('days_past_due', sa.Integer, default=0, nullable=False),
        sa.Column('oldest_due_date', sa.Date, nullable=True),
        sa.Column('asset_classification', postgresql.ENUM('STANDARD', 'SMA_0', 'SMA_1', 'SMA_2', 'NPA', 'SUBSTANDARD', 'DOUBTFUL_1', 'DOUBTFUL_2', 'DOUBTFUL_3', 'LOSS', name='assetclassification', create_type=False), default='STANDARD', nullable=False),
        sa.Column('npa_date', sa.Date, nullable=True),
        sa.Column('npa_amount', sa.Numeric(20, 2), default=0, nullable=False),
        # Provisioning
        sa.Column('provision_percentage', sa.Numeric(5, 2), default=0.40, nullable=False),
        sa.Column('provision_amount', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('provision_held', sa.Numeric(20, 2), default=0, nullable=False),
        # Write-off tracking
        sa.Column('principal_written_off', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('interest_written_off', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('write_off_date', sa.Date, nullable=True),
        # Prepayment/Foreclosure
        sa.Column('prepayment_penalty_rate', sa.Numeric(5, 2), default=0, nullable=False),
        sa.Column('foreclosure_penalty_rate', sa.Numeric(5, 2), default=0, nullable=False),
        sa.Column('lock_in_end_date', sa.Date, nullable=True),
        # Receipt allocation
        sa.Column('allocation_priority', postgresql.ENUM('FIFO', 'LIFO', 'PROPORTIONATE', 'CUSTOM', name='allocationpriority', create_type=False), default='FIFO', nullable=False),
        sa.Column('allocation_order', postgresql.JSONB, nullable=False),
        # Status
        sa.Column('status', postgresql.ENUM('CREATED', 'ACTIVE', 'DORMANT', 'FROZEN', 'CLOSED', 'WRITTEN_OFF', 'RECALLED', name='loanaccountstatus', create_type=False), default='CREATED', nullable=False),
        # GL Account mapping
        sa.Column('loan_asset_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_account.id', ondelete='SET NULL'), nullable=True),
        sa.Column('interest_receivable_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_account.id', ondelete='SET NULL'), nullable=True),
        sa.Column('interest_income_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_account.id', ondelete='SET NULL'), nullable=True),
        sa.Column('interest_suspense_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_account.id', ondelete='SET NULL'), nullable=True),
        sa.Column('provision_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_account.id', ondelete='SET NULL'), nullable=True),
        # Remarks
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
    op.create_index('ix_lms_loan_account_org_status', 'lms_loan_account', ['organization_id', 'status'])
    op.create_index('ix_lms_loan_account_entity', 'lms_loan_account', ['entity_id'])
    op.create_index('ix_lms_loan_account_asset_class', 'lms_loan_account', ['asset_classification'])
    op.create_index('ix_lms_loan_account_dpd', 'lms_loan_account', ['days_past_due'])
    op.create_index('ix_lms_loan_account_number', 'lms_loan_account', ['loan_account_number'])

    # ============================================================================
    # DISBURSEMENT TABLE
    # ============================================================================
    op.create_table(
        'lms_disbursement',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('loan_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lms_loan_account.id', ondelete='CASCADE'), nullable=False),
        sa.Column('disbursement_number', sa.Integer, nullable=False),
        sa.Column('disbursement_reference', sa.String(50), nullable=False, unique=True),
        # Amount
        sa.Column('requested_amount', sa.Numeric(20, 2), nullable=False),
        sa.Column('approved_amount', sa.Numeric(20, 2), nullable=True),
        sa.Column('disbursed_amount', sa.Numeric(20, 2), nullable=True),
        sa.Column('disbursement_charges', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('net_disbursement', sa.Numeric(20, 2), nullable=True),
        # Dates
        sa.Column('request_date', sa.Date, nullable=False),
        sa.Column('approval_date', sa.Date, nullable=True),
        sa.Column('scheduled_date', sa.Date, nullable=True),
        sa.Column('disbursement_date', sa.Date, nullable=True),
        sa.Column('value_date', sa.Date, nullable=True),
        # Mode
        sa.Column('disbursement_mode', postgresql.ENUM('RTGS', 'NEFT', 'IMPS', 'CHEQUE', 'DD', 'DIRECT_CREDIT', 'ESCROW', name='disbursementmode', create_type=False), default='RTGS', nullable=False),
        # Beneficiary
        sa.Column('beneficiary_name', sa.String(200), nullable=False),
        sa.Column('beneficiary_account_number', sa.String(50), nullable=False),
        sa.Column('beneficiary_ifsc', sa.String(11), nullable=False),
        sa.Column('beneficiary_bank', sa.String(200), nullable=True),
        sa.Column('bank_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity_bank_account.id', ondelete='SET NULL'), nullable=True),
        # Payment reference
        sa.Column('utr_number', sa.String(50), nullable=True),
        sa.Column('cheque_number', sa.String(20), nullable=True),
        # Purpose
        sa.Column('purpose', sa.Text, nullable=True),
        sa.Column('milestone_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_project_milestone.id', ondelete='SET NULL'), nullable=True),
        # Conditions
        sa.Column('conditions_verified', sa.Boolean, default=False, nullable=False),
        sa.Column('conditions_verified_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('conditions_verified_at', sa.DateTime(timezone=True), nullable=True),
        # Status
        sa.Column('status', postgresql.ENUM('PENDING', 'APPROVED', 'PROCESSED', 'REJECTED', 'CANCELLED', 'FAILED', 'REVERSED', name='disbursementstatus', create_type=False), default='PENDING', nullable=False),
        # Approval
        sa.Column('approved_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        # Processing
        sa.Column('processed_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        # Rejection
        sa.Column('rejection_reason', sa.Text, nullable=True),
        # GL
        sa.Column('voucher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('txn_voucher.id', ondelete='SET NULL'), nullable=True),
        sa.Column('remarks', sa.Text, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('loan_account_id', 'disbursement_number', name='uq_disbursement_num'),
    )
    op.create_index('ix_lms_disbursement_status', 'lms_disbursement', ['loan_account_id', 'status'])
    op.create_index('ix_lms_disbursement_date', 'lms_disbursement', ['disbursement_date'])
    op.create_index('ix_lms_disbursement_utr', 'lms_disbursement', ['utr_number'])

    # ============================================================================
    # REPAYMENT SCHEDULE TABLE
    # ============================================================================
    op.create_table(
        'lms_repayment_schedule',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('loan_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lms_loan_account.id', ondelete='CASCADE'), nullable=False),
        sa.Column('schedule_number', sa.Integer, nullable=False),
        sa.Column('schedule_type', postgresql.ENUM('ORIGINAL', 'RESCHEDULED', 'RESTRUCTURED', 'REVISED', name='scheduletype', create_type=False), default='ORIGINAL', nullable=False),
        # Schedule basis
        sa.Column('principal_amount', sa.Numeric(20, 2), nullable=False),
        sa.Column('interest_rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('tenure_months', sa.Integer, nullable=False),
        sa.Column('emi_amount', sa.Numeric(20, 2), nullable=True),
        # Dates
        sa.Column('effective_date', sa.Date, nullable=False),
        sa.Column('first_installment_date', sa.Date, nullable=False),
        sa.Column('last_installment_date', sa.Date, nullable=False),
        # Totals
        sa.Column('total_installments', sa.Integer, nullable=False),
        sa.Column('total_principal', sa.Numeric(20, 2), nullable=False),
        sa.Column('total_interest', sa.Numeric(20, 2), nullable=False),
        # Status
        sa.Column('is_current', sa.Boolean, default=True, nullable=False),
        sa.Column('superseded_date', sa.Date, nullable=True),
        sa.Column('superseded_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lms_repayment_schedule.id', ondelete='SET NULL'), nullable=True),
        sa.Column('change_reason', sa.Text, nullable=True),
        sa.Column('remarks', sa.Text, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('loan_account_id', 'schedule_number', name='uq_schedule_num'),
    )
    op.create_index('ix_lms_schedule_current', 'lms_repayment_schedule', ['loan_account_id', 'is_current'])

    # ============================================================================
    # SCHEDULE INSTALLMENT TABLE
    # ============================================================================
    op.create_table(
        'lms_schedule_installment',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('schedule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lms_repayment_schedule.id', ondelete='CASCADE'), nullable=False),
        sa.Column('installment_number', sa.Integer, nullable=False),
        sa.Column('due_date', sa.Date, nullable=False),
        # Scheduled amounts
        sa.Column('principal_amount', sa.Numeric(20, 2), nullable=False),
        sa.Column('interest_amount', sa.Numeric(20, 2), nullable=False),
        sa.Column('emi_amount', sa.Numeric(20, 2), nullable=False),
        # Balances
        sa.Column('opening_balance', sa.Numeric(20, 2), nullable=False),
        sa.Column('closing_balance', sa.Numeric(20, 2), nullable=False),
        # Paid amounts
        sa.Column('principal_paid', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('interest_paid', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('penal_interest_paid', sa.Numeric(20, 2), default=0, nullable=False),
        # Overdue tracking
        sa.Column('principal_overdue', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('interest_overdue', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('penal_interest_due', sa.Numeric(20, 2), default=0, nullable=False),
        # Status
        sa.Column('status', postgresql.ENUM('NOT_DUE', 'DUE', 'PARTIALLY_PAID', 'PAID', 'OVERDUE', 'WAIVED', 'WRITTEN_OFF', name='installmentstatus', create_type=False), default='NOT_DUE', nullable=False),
        sa.Column('paid_date', sa.Date, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('schedule_id', 'installment_number', name='uq_installment_num'),
    )
    op.create_index('ix_lms_installment_due', 'lms_schedule_installment', ['due_date', 'status'])
    op.create_index('ix_lms_installment_status', 'lms_schedule_installment', ['schedule_id', 'status'])

    # ============================================================================
    # LOAN ACCRUAL TABLE
    # ============================================================================
    op.create_table(
        'lms_loan_accrual',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('loan_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lms_loan_account.id', ondelete='CASCADE'), nullable=False),
        sa.Column('accrual_date', sa.Date, nullable=False),
        sa.Column('accrual_category', postgresql.ENUM('INTEREST', 'PENAL_INTEREST', 'FEE', 'COMMITMENT_FEE', name='accrualcategory', create_type=False), nullable=False),
        # Calculation basis
        sa.Column('principal_balance', sa.Numeric(20, 2), nullable=False),
        sa.Column('interest_rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('day_count_basis', sa.Integer, default=365, nullable=False),
        # Accrued amount
        sa.Column('accrued_amount', sa.Numeric(20, 4), nullable=False),
        sa.Column('cumulative_accrued', sa.Numeric(20, 2), nullable=False),
        # Status
        sa.Column('status', postgresql.ENUM('ACCRUED', 'REVERSED', 'SUSPENDED', 'WRITTEN_OFF', name='accrualstatus', create_type=False), default='ACCRUED', nullable=False),
        sa.Column('moved_to_suspense', sa.Boolean, default=False, nullable=False),
        sa.Column('suspense_date', sa.Date, nullable=True),
        # GL
        sa.Column('voucher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('txn_voucher.id', ondelete='SET NULL'), nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('loan_account_id', 'accrual_date', 'accrual_category', name='uq_accrual_date_cat'),
    )
    op.create_index('ix_lms_accrual_date', 'lms_loan_accrual', ['accrual_date'])
    op.create_index('ix_lms_accrual_status', 'lms_loan_accrual', ['loan_account_id', 'status'])

    # ============================================================================
    # LOAN MANDATE TABLE
    # ============================================================================
    op.create_table(
        'lms_loan_mandate',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('loan_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lms_loan_account.id', ondelete='CASCADE'), nullable=False),
        sa.Column('mandate_reference', sa.String(50), nullable=False, unique=True),
        sa.Column('umrn', sa.String(50), nullable=True),
        sa.Column('mandate_type', sa.String(20), default='NACH', nullable=False),
        # Bank account
        sa.Column('bank_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('los_entity_bank_account.id', ondelete='SET NULL'), nullable=True),
        sa.Column('account_number', sa.String(50), nullable=False),
        sa.Column('ifsc_code', sa.String(11), nullable=False),
        sa.Column('bank_name', sa.String(200), nullable=True),
        sa.Column('account_holder_name', sa.String(200), nullable=False),
        # Amount
        sa.Column('mandate_amount', sa.Numeric(20, 2), nullable=False),
        sa.Column('amount_type', sa.String(20), default='FIXED', nullable=False),
        # Frequency
        sa.Column('frequency', sa.String(20), default='MONTHLY', nullable=False),
        sa.Column('debit_day', sa.Integer, default=1, nullable=False),
        # Validity
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=False),
        sa.Column('registration_date', sa.Date, nullable=True),
        # Status
        sa.Column('status', postgresql.ENUM('INITIATED', 'REGISTERED', 'ACTIVE', 'SUSPENDED', 'CANCELLED', 'REJECTED', 'EXPIRED', name='mandatestatus', create_type=False), default='INITIATED', nullable=False),
        sa.Column('rejection_reason', sa.String(200), nullable=True),
        # Cancellation
        sa.Column('cancellation_date', sa.Date, nullable=True),
        sa.Column('cancellation_reason', sa.Text, nullable=True),
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
    op.create_index('ix_lms_mandate_loan', 'lms_loan_mandate', ['loan_account_id', 'status'])
    op.create_index('ix_lms_mandate_umrn', 'lms_loan_mandate', ['umrn'])

    # ============================================================================
    # LOAN RECEIPT TABLE
    # ============================================================================
    op.create_table(
        'lms_loan_receipt',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('loan_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lms_loan_account.id', ondelete='CASCADE'), nullable=False),
        sa.Column('receipt_number', sa.String(50), nullable=False, unique=True),
        # Receipt details
        sa.Column('receipt_date', sa.Date, nullable=False),
        sa.Column('value_date', sa.Date, nullable=False),
        sa.Column('receipt_amount', sa.Numeric(20, 2), nullable=False),
        # Type and mode
        sa.Column('receipt_type', postgresql.ENUM('REGULAR', 'PREPAYMENT', 'FORECLOSURE', 'SUBVENTION', 'INSURANCE_CLAIM', 'LEGAL_RECOVERY', 'OTS_SETTLEMENT', 'WRITE_BACK', name='receipttype', create_type=False), default='REGULAR', nullable=False),
        sa.Column('receipt_mode', postgresql.ENUM('CASH', 'CHEQUE', 'DD', 'RTGS', 'NEFT', 'IMPS', 'UPI', 'NACH', 'AUTO_DEBIT', 'ADJUSTMENT', name='receiptmode', create_type=False), nullable=False),
        # Instrument
        sa.Column('instrument_number', sa.String(50), nullable=True),
        sa.Column('instrument_date', sa.Date, nullable=True),
        sa.Column('instrument_bank', sa.String(200), nullable=True),
        # Mandate
        sa.Column('mandate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lms_loan_mandate.id', ondelete='SET NULL'), nullable=True),
        # Allocation
        sa.Column('allocated_amount', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('unallocated_amount', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('principal_allocated', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('interest_allocated', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('penal_interest_allocated', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('charges_allocated', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('prepayment_charges', sa.Numeric(20, 2), default=0, nullable=False),
        # Status
        sa.Column('status', postgresql.ENUM('PENDING', 'ALLOCATED', 'REVERSED', 'BOUNCED', name='receiptstatus', create_type=False), default='PENDING', nullable=False),
        # Bounce
        sa.Column('bounced', sa.Boolean, default=False, nullable=False),
        sa.Column('bounce_date', sa.Date, nullable=True),
        sa.Column('bounce_reason', sa.String(200), nullable=True),
        sa.Column('bounce_charges', sa.Numeric(20, 2), default=0, nullable=False),
        # GL
        sa.Column('voucher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('txn_voucher.id', ondelete='SET NULL'), nullable=True),
        # Processing
        sa.Column('processed_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
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
    op.create_index('ix_lms_receipt_org_date', 'lms_loan_receipt', ['organization_id', 'receipt_date'])
    op.create_index('ix_lms_receipt_loan_date', 'lms_loan_receipt', ['loan_account_id', 'receipt_date'])
    op.create_index('ix_lms_receipt_status', 'lms_loan_receipt', ['loan_account_id', 'status'])
    op.create_index('ix_lms_receipt_number', 'lms_loan_receipt', ['receipt_number'])

    # ============================================================================
    # RECEIPT ALLOCATION TABLE
    # ============================================================================
    op.create_table(
        'lms_receipt_allocation',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('receipt_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lms_loan_receipt.id', ondelete='CASCADE'), nullable=False),
        sa.Column('installment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lms_schedule_installment.id', ondelete='SET NULL'), nullable=True),
        sa.Column('allocation_component', postgresql.ENUM('CHARGES', 'PENAL_INTEREST', 'INTEREST', 'PRINCIPAL', 'EMI', name='allocationcomponent', create_type=False), nullable=False),
        sa.Column('allocated_amount', sa.Numeric(20, 2), nullable=False),
        sa.Column('allocation_sequence', sa.Integer, nullable=False),
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
    op.create_index('ix_lms_allocation_receipt', 'lms_receipt_allocation', ['receipt_id'])
    op.create_index('ix_lms_allocation_installment', 'lms_receipt_allocation', ['installment_id'])

    # ============================================================================
    # ASSET CLASSIFICATION HISTORY TABLE
    # ============================================================================
    op.create_table(
        'lms_asset_classification_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('loan_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lms_loan_account.id', ondelete='CASCADE'), nullable=False),
        sa.Column('effective_date', sa.Date, nullable=False),
        sa.Column('previous_classification', postgresql.ENUM('STANDARD', 'SMA_0', 'SMA_1', 'SMA_2', 'NPA', 'SUBSTANDARD', 'DOUBTFUL_1', 'DOUBTFUL_2', 'DOUBTFUL_3', 'LOSS', name='assetclassification', create_type=False), nullable=True),
        sa.Column('new_classification', postgresql.ENUM('STANDARD', 'SMA_0', 'SMA_1', 'SMA_2', 'NPA', 'SUBSTANDARD', 'DOUBTFUL_1', 'DOUBTFUL_2', 'DOUBTFUL_3', 'LOSS', name='assetclassification', create_type=False), nullable=False),
        sa.Column('days_past_due', sa.Integer, nullable=False),
        sa.Column('principal_outstanding', sa.Numeric(20, 2), nullable=False),
        sa.Column('total_outstanding', sa.Numeric(20, 2), nullable=False),
        sa.Column('change_reason', sa.String(50), nullable=False),
        sa.Column('change_remarks', sa.Text, nullable=True),
        sa.Column('approved_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
    )
    op.create_index('ix_lms_asset_class_hist_loan', 'lms_asset_classification_history', ['loan_account_id', 'effective_date'])

    # ============================================================================
    # LOAN PROVISION TABLE
    # ============================================================================
    op.create_table(
        'lms_loan_provision',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('loan_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lms_loan_account.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provision_date', sa.Date, nullable=False),
        # Classification
        sa.Column('asset_classification', postgresql.ENUM('STANDARD', 'SMA_0', 'SMA_1', 'SMA_2', 'NPA', 'SUBSTANDARD', 'DOUBTFUL_1', 'DOUBTFUL_2', 'DOUBTFUL_3', 'LOSS', name='assetclassification', create_type=False), nullable=False),
        sa.Column('provisioning_category', postgresql.ENUM('STANDARD', 'SUBSTANDARD_SECURED', 'SUBSTANDARD_UNSECURED', 'DOUBTFUL_1', 'DOUBTFUL_2', 'DOUBTFUL_3', 'LOSS', name='provisioningcategory', create_type=False), nullable=False),
        # Outstanding
        sa.Column('principal_outstanding', sa.Numeric(20, 2), nullable=False),
        sa.Column('total_outstanding', sa.Numeric(20, 2), nullable=False),
        sa.Column('security_value', sa.Numeric(20, 2), default=0, nullable=False),
        sa.Column('unsecured_portion', sa.Numeric(20, 2), default=0, nullable=False),
        # Provision calculation
        sa.Column('provision_percentage', sa.Numeric(5, 2), nullable=False),
        sa.Column('provision_required', sa.Numeric(20, 2), nullable=False),
        sa.Column('provision_held', sa.Numeric(20, 2), nullable=False),
        sa.Column('provision_movement', sa.Numeric(20, 2), nullable=False),
        # GL
        sa.Column('voucher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('txn_voucher.id', ondelete='SET NULL'), nullable=True),
        sa.Column('remarks', sa.Text, nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.UniqueConstraint('loan_account_id', 'provision_date', name='uq_provision_loan_date'),
    )
    op.create_index('ix_lms_provision_org_date', 'lms_loan_provision', ['organization_id', 'provision_date'])

    # ============================================================================
    # LOAN ADJUSTMENT TABLE
    # ============================================================================
    op.create_table(
        'lms_loan_adjustment',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('loan_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lms_loan_account.id', ondelete='CASCADE'), nullable=False),
        sa.Column('adjustment_reference', sa.String(50), nullable=False, unique=True),
        sa.Column('adjustment_type', postgresql.ENUM('RATE_CHANGE', 'TENURE_CHANGE', 'EMI_CHANGE', 'MORATORIUM', 'RESCHEDULE', 'RESTRUCTURE', 'WRITE_OFF', 'WAIVER', name='adjustmenttype', create_type=False), nullable=False),
        sa.Column('effective_date', sa.Date, nullable=False),
        # Before values
        sa.Column('previous_interest_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('previous_emi', sa.Numeric(20, 2), nullable=True),
        sa.Column('previous_tenure', sa.Integer, nullable=True),
        sa.Column('previous_maturity_date', sa.Date, nullable=True),
        # After values
        sa.Column('new_interest_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('new_emi', sa.Numeric(20, 2), nullable=True),
        sa.Column('new_tenure', sa.Integer, nullable=True),
        sa.Column('new_maturity_date', sa.Date, nullable=True),
        # Waiver
        sa.Column('waiver_type', postgresql.ENUM('INTEREST', 'PENAL_INTEREST', 'CHARGES', 'PRINCIPAL', 'FULL', name='waivertype', create_type=False), nullable=True),
        sa.Column('waiver_amount', sa.Numeric(20, 2), default=0, nullable=False),
        # Write-off
        sa.Column('write_off_amount', sa.Numeric(20, 2), default=0, nullable=False),
        # Moratorium
        sa.Column('moratorium_months', sa.Integer, nullable=True),
        sa.Column('moratorium_end_date', sa.Date, nullable=True),
        # New schedule
        sa.Column('new_schedule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lms_repayment_schedule.id', ondelete='SET NULL'), nullable=True),
        # Approval
        sa.Column('adjustment_reason', sa.Text, nullable=False),
        sa.Column('approved_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        # GL
        sa.Column('voucher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('txn_voucher.id', ondelete='SET NULL'), nullable=True),
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
    op.create_index('ix_lms_adjustment_loan', 'lms_loan_adjustment', ['loan_account_id', 'effective_date'])
    op.create_index('ix_lms_adjustment_type', 'lms_loan_adjustment', ['adjustment_type'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('lms_loan_adjustment')
    op.drop_table('lms_loan_provision')
    op.drop_table('lms_asset_classification_history')
    op.drop_table('lms_receipt_allocation')
    op.drop_table('lms_loan_receipt')
    op.drop_table('lms_loan_mandate')
    op.drop_table('lms_loan_accrual')
    op.drop_table('lms_schedule_installment')
    op.drop_table('lms_repayment_schedule')
    op.drop_table('lms_disbursement')
    op.drop_table('lms_loan_account')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS glentrytype")
    op.execute("DROP TYPE IF EXISTS mandatestatus")
    op.execute("DROP TYPE IF EXISTS provisioningcategory")
    op.execute("DROP TYPE IF EXISTS waivertype")
    op.execute("DROP TYPE IF EXISTS adjustmenttype")
    op.execute("DROP TYPE IF EXISTS allocationcomponent")
    op.execute("DROP TYPE IF EXISTS allocationpriority")
    op.execute("DROP TYPE IF EXISTS receiptmode")
    op.execute("DROP TYPE IF EXISTS receiptstatus")
    op.execute("DROP TYPE IF EXISTS receipttype")
    op.execute("DROP TYPE IF EXISTS assetclassification")
    op.execute("DROP TYPE IF EXISTS accrualstatus")
    op.execute("DROP TYPE IF EXISTS accrualcategory")
    op.execute("DROP TYPE IF EXISTS installmentstatus")
    op.execute("DROP TYPE IF EXISTS installmenttype")
    op.execute("DROP TYPE IF EXISTS scheduletype")
    op.execute("DROP TYPE IF EXISTS disbursementmode")
    op.execute("DROP TYPE IF EXISTS disbursementstatus")
    op.execute("DROP TYPE IF EXISTS loanaccountstatus")
