"""Add HR enhancement tables for training and performance management.

Revision ID: z28_hr_enhancement
Revises: z27_inventory
Create Date: 2026-01-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'z28_hr_enhancement'
down_revision: Union[str, None] = 'z27_inventory'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create training_status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE training_status AS ENUM (
                'planned', 'scheduled', 'in_progress', 'completed', 'cancelled'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create nomination_status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE nomination_status AS ENUM (
                'nominated', 'approved', 'rejected', 'attended', 'completed', 'no_show'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create appraisal_status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE appraisal_status AS ENUM (
                'not_started', 'goal_setting', 'self_appraisal', 'manager_review',
                'calibration', 'completed', 'cancelled'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create goal_status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE goal_status AS ENUM (
                'draft', 'submitted', 'approved', 'in_progress', 'completed', 'deferred'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create mst_training_program table
    op.create_table(
        'mst_training_program',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('training_type', sa.String(50), nullable=False),
        sa.Column('mode', sa.String(50), nullable=False, server_default='offline'),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('duration_hours', sa.Numeric(6, 2), nullable=True),
        sa.Column('duration_days', sa.Integer, nullable=True),
        sa.Column('max_participants', sa.Integer, nullable=True),
        sa.Column('min_participants', sa.Integer, nullable=True),
        sa.Column('trainer_name', sa.String(255), nullable=True),
        sa.Column('trainer_organization', sa.String(255), nullable=True),
        sa.Column('venue', sa.String(500), nullable=True),
        sa.Column('start_date', sa.Date, nullable=True),
        sa.Column('end_date', sa.Date, nullable=True),
        sa.Column('start_time', sa.Time, nullable=True),
        sa.Column('end_time', sa.Time, nullable=True),
        sa.Column('cost_per_participant', sa.Numeric(12, 2), nullable=True),
        sa.Column('total_budget', sa.Numeric(15, 2), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='planned'),
        sa.Column('prerequisites', sa.Text, nullable=True),
        sa.Column('objectives', sa.Text, nullable=True),
        sa.Column('syllabus', sa.Text, nullable=True),
        sa.Column('certification_required', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('certification_validity_months', sa.Integer, nullable=True),
        sa.Column('is_mandatory', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('target_departments', postgresql.ARRAY(postgresql.UUID), nullable=True),
        sa.Column('target_designations', postgresql.ARRAY(postgresql.UUID), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mst_training_program_org', 'mst_training_program', ['organization_id'])
    op.create_index('ix_mst_training_program_code', 'mst_training_program', ['organization_id', 'code'], unique=True)
    op.create_index('ix_mst_training_program_status', 'mst_training_program', ['status'])
    op.create_index('ix_mst_training_program_dates', 'mst_training_program', ['start_date', 'end_date'])

    # Create txn_training_nomination table
    op.create_table(
        'txn_training_nomination',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('training_program_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nominated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('nomination_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('nomination_reason', sa.String(1000), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='nominated'),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.String(500), nullable=True),
        sa.Column('attendance_date', sa.Date, nullable=True),
        sa.Column('attendance_hours', sa.Numeric(6, 2), nullable=True),
        sa.Column('completion_date', sa.Date, nullable=True),
        sa.Column('certification_obtained', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('certification_date', sa.Date, nullable=True),
        sa.Column('certification_expiry', sa.Date, nullable=True),
        sa.Column('score', sa.Numeric(5, 2), nullable=True),
        sa.Column('grade', sa.String(10), nullable=True),
        sa.Column('remarks', sa.String(1000), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['training_program_id'], ['mst_training_program.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['employee_id'], ['hris_employee.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['nominated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approved_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_training_nomination_program', 'txn_training_nomination', ['training_program_id'])
    op.create_index('ix_txn_training_nomination_employee', 'txn_training_nomination', ['employee_id'])
    op.create_index('ix_txn_training_nomination_status', 'txn_training_nomination', ['status'])
    op.create_index('ix_txn_training_nomination_unique', 'txn_training_nomination', ['training_program_id', 'employee_id'], unique=True)

    # Create txn_training_feedback table
    op.create_table(
        'txn_training_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('nomination_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feedback_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('overall_rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('content_rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('trainer_rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('facility_rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('relevance_rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('effectiveness_rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('feedback_text', sa.Text, nullable=True),
        sa.Column('suggestions', sa.Text, nullable=True),
        sa.Column('would_recommend', sa.Boolean, nullable=True),
        sa.Column('key_learnings', sa.Text, nullable=True),
        sa.Column('application_plan', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['nomination_id'], ['txn_training_nomination.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_training_feedback_nomination', 'txn_training_feedback', ['nomination_id'], unique=True)

    # Create mst_appraisal_cycle table
    op.create_table(
        'mst_appraisal_cycle',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('financial_year_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cycle_type', sa.String(50), nullable=False, server_default='annual'),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=False),
        sa.Column('goal_setting_start', sa.Date, nullable=True),
        sa.Column('goal_setting_end', sa.Date, nullable=True),
        sa.Column('mid_review_start', sa.Date, nullable=True),
        sa.Column('mid_review_end', sa.Date, nullable=True),
        sa.Column('self_appraisal_start', sa.Date, nullable=True),
        sa.Column('self_appraisal_end', sa.Date, nullable=True),
        sa.Column('manager_review_start', sa.Date, nullable=True),
        sa.Column('manager_review_end', sa.Date, nullable=True),
        sa.Column('calibration_start', sa.Date, nullable=True),
        sa.Column('calibration_end', sa.Date, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='not_started'),
        sa.Column('rating_scale', sa.Integer, nullable=False, server_default='5'),
        sa.Column('weightage_goals', sa.Numeric(5, 2), nullable=True, server_default='70'),
        sa.Column('weightage_competencies', sa.Numeric(5, 2), nullable=True, server_default='30'),
        sa.Column('allow_self_rating', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('allow_peer_feedback', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['organization_id'], ['mst_organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['financial_year_id'], ['mst_financial_year.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mst_appraisal_cycle_org', 'mst_appraisal_cycle', ['organization_id'])
    op.create_index('ix_mst_appraisal_cycle_code', 'mst_appraisal_cycle', ['organization_id', 'code'], unique=True)
    op.create_index('ix_mst_appraisal_cycle_status', 'mst_appraisal_cycle', ['status'])

    # Create txn_goal table
    op.create_table(
        'txn_goal',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('appraisal_cycle_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('goal_number', sa.Integer, nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('weightage', sa.Numeric(5, 2), nullable=False),
        sa.Column('target_value', sa.String(255), nullable=True),
        sa.Column('measurement_criteria', sa.Text, nullable=True),
        sa.Column('start_date', sa.Date, nullable=True),
        sa.Column('due_date', sa.Date, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('progress_percent', sa.Numeric(5, 2), nullable=True, server_default='0'),
        sa.Column('achievement_value', sa.String(255), nullable=True),
        sa.Column('self_rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('self_comments', sa.Text, nullable=True),
        sa.Column('manager_rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('manager_comments', sa.Text, nullable=True),
        sa.Column('final_rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['appraisal_cycle_id'], ['mst_appraisal_cycle.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['employee_id'], ['hris_employee.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_goal_cycle', 'txn_goal', ['appraisal_cycle_id'])
    op.create_index('ix_txn_goal_employee', 'txn_goal', ['employee_id'])
    op.create_index('ix_txn_goal_status', 'txn_goal', ['status'])

    # Create txn_appraisal table
    op.create_table(
        'txn_appraisal',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('appraisal_cycle_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='not_started'),
        sa.Column('goal_rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('competency_rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('overall_rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('final_grade', sa.String(10), nullable=True),
        sa.Column('self_appraisal_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('self_summary', sa.Text, nullable=True),
        sa.Column('self_achievements', sa.Text, nullable=True),
        sa.Column('self_challenges', sa.Text, nullable=True),
        sa.Column('self_development_areas', sa.Text, nullable=True),
        sa.Column('manager_review_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('manager_summary', sa.Text, nullable=True),
        sa.Column('manager_achievements', sa.Text, nullable=True),
        sa.Column('manager_improvements', sa.Text, nullable=True),
        sa.Column('manager_recommendations', sa.Text, nullable=True),
        sa.Column('calibration_notes', sa.Text, nullable=True),
        sa.Column('calibrated_rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('calibrated_grade', sa.String(10), nullable=True),
        sa.Column('calibrated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('calibrated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('employee_acknowledgment', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('acknowledgment_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('employee_comments', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['appraisal_cycle_id'], ['mst_appraisal_cycle.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['employee_id'], ['hris_employee.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewer_id'], ['mst_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['calibrated_by'], ['mst_user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_txn_appraisal_cycle', 'txn_appraisal', ['appraisal_cycle_id'])
    op.create_index('ix_txn_appraisal_employee', 'txn_appraisal', ['employee_id'])
    op.create_index('ix_txn_appraisal_status', 'txn_appraisal', ['status'])
    op.create_index('ix_txn_appraisal_unique', 'txn_appraisal', ['appraisal_cycle_id', 'employee_id'], unique=True)


def downgrade() -> None:
    # Drop tables
    op.drop_table('txn_appraisal')
    op.drop_table('txn_goal')
    op.drop_table('mst_appraisal_cycle')
    op.drop_table('txn_training_feedback')
    op.drop_table('txn_training_nomination')
    op.drop_table('mst_training_program')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS goal_status")
    op.execute("DROP TYPE IF EXISTS appraisal_status")
    op.execute("DROP TYPE IF EXISTS nomination_status")
    op.execute("DROP TYPE IF EXISTS training_status")
