"""add hris training tables

Revision ID: zzc65_add_hris_training_tables
Revises: zzc64_realign_payroll_employee_salary_table
Create Date: 2026-05-26 18:40:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "zzc65_add_hris_training_tables"
down_revision: Union[str, None] = "zzc64_realign_payroll_employee_salary_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "hris_training_program",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("program_code", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("mode", sa.String(length=30), nullable=False),
        sa.Column("trainer_type", sa.String(length=20), nullable=False),
        sa.Column("trainer_name", sa.String(length=200), nullable=False),
        sa.Column("trainer_contact", sa.String(length=200), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("duration_hours", sa.Numeric(10, 2), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("max_participants", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("cost_per_participant", sa.Numeric(14, 2), nullable=False),
        sa.Column("pre_requisites", sa.Text(), nullable=True),
        sa.Column("learning_objectives", sa.Text(), nullable=True),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "certificate_provided",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["created_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["deleted_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["mst_organization.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id", "program_code", name="uq_hris_training_program_org_code"
        ),
    )
    op.create_index(
        op.f("ix_hris_training_program_organization_id"),
        "hris_training_program",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_hris_training_program_status"), "hris_training_program", ["status"], unique=False
    )

    op.create_table(
        "hris_training_nomination",
        sa.Column("program_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="NOMINATED"),
        sa.Column(
            "attendance_marked", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["created_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["deleted_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["employee_id"], ["hris_employee.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["program_id"], ["hris_training_program.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "program_id", "employee_id", name="uq_hris_training_nomination_program_employee"
        ),
    )
    op.create_index(
        op.f("ix_hris_training_nomination_employee_id"),
        "hris_training_nomination",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_hris_training_nomination_program_id"),
        "hris_training_nomination",
        ["program_id"],
        unique=False,
    )

    op.create_table(
        "hris_training_feedback",
        sa.Column("program_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nomination_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("overall_rating", sa.Numeric(4, 2), nullable=False),
        sa.Column("content_rating", sa.Numeric(4, 2), nullable=False),
        sa.Column("trainer_rating", sa.Numeric(4, 2), nullable=False),
        sa.Column("facilities_rating", sa.Numeric(4, 2), nullable=False),
        sa.Column("relevance_rating", sa.Numeric(4, 2), nullable=False),
        sa.Column("would_recommend", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("strengths", sa.Text(), nullable=True),
        sa.Column("improvements", sa.Text(), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("submitted_on", sa.Date(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["created_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["deleted_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["employee_id"], ["hris_employee.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["nomination_id"], ["hris_training_nomination.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["program_id"], ["hris_training_program.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by"], ["mst_user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "program_id", "employee_id", name="uq_hris_training_feedback_program_employee"
        ),
    )
    op.create_index(
        op.f("ix_hris_training_feedback_employee_id"),
        "hris_training_feedback",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_hris_training_feedback_program_id"),
        "hris_training_feedback",
        ["program_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_hris_training_feedback_program_id"), table_name="hris_training_feedback")
    op.drop_index(
        op.f("ix_hris_training_feedback_employee_id"), table_name="hris_training_feedback"
    )
    op.drop_table("hris_training_feedback")
    op.drop_index(
        op.f("ix_hris_training_nomination_program_id"), table_name="hris_training_nomination"
    )
    op.drop_index(
        op.f("ix_hris_training_nomination_employee_id"), table_name="hris_training_nomination"
    )
    op.drop_table("hris_training_nomination")
    op.drop_index(op.f("ix_hris_training_program_status"), table_name="hris_training_program")
    op.drop_index(
        op.f("ix_hris_training_program_organization_id"), table_name="hris_training_program"
    )
    op.drop_table("hris_training_program")
