"""Align LMS receipt status enum name with ORM model.

Revision ID: zzc49_align_lms_receipt_status_enum
Revises: zzc48_iif_guideline_configuration
Create Date: 2026-05-20
"""

from alembic import op


revision = "zzc49_align_lms_receipt_status_enum"
down_revision = "zzc48_iif_guideline_configuration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'lms_receipt_status'
            ) THEN
                CREATE TYPE lms_receipt_status AS ENUM (
                    'PENDING',
                    'ALLOCATED',
                    'REVERSED',
                    'BOUNCED'
                );
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        ALTER TABLE lms_loan_receipt
        ALTER COLUMN status TYPE lms_receipt_status
        USING status::text::lms_receipt_status
        """
    )
    op.execute(
        """
        ALTER TABLE lms_loan_receipt
        ALTER COLUMN status SET DEFAULT 'PENDING'::lms_receipt_status
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE lms_loan_receipt ALTER COLUMN status DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE lms_loan_receipt
        ALTER COLUMN status TYPE varchar(20)
        USING status::text
        """
    )
    op.execute("DROP TYPE IF EXISTS lms_receipt_status")
