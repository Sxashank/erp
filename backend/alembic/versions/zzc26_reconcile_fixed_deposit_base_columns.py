"""Reconcile fixed deposit BaseModel columns.

Revision ID: zzc26_reconcile_fixed_deposit_base_columns
Revises: zzc25_reconcile_notification_runtime_schema
Create Date: 2026-05-18
"""

from typing import Sequence, Union

from alembic import op


revision: str = "zzc26_reconcile_fixed_deposit_base_columns"
down_revision: Union[str, None] = "zzc25_reconcile_notification_runtime_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


FD_TABLES = (
    "fd_product",
    "fd_interest_slab",
    "fd_fixed_deposit",
    "fd_interest_accrual",
    "fd_transaction",
    "fd_nominee",
)


def upgrade() -> None:
    for table_name in FD_TABLES:
        op.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT FROM pg_tables
                    WHERE schemaname = 'public' AND tablename = '{table_name}'
                ) THEN
                    IF NOT EXISTS (
                        SELECT FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = '{table_name}'
                          AND column_name = 'deleted_at'
                    ) THEN
                        ALTER TABLE {table_name}
                        ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE NULL;
                    END IF;

                    IF NOT EXISTS (
                        SELECT FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = '{table_name}'
                          AND column_name = 'deleted_by'
                    ) THEN
                        ALTER TABLE {table_name}
                        ADD COLUMN deleted_by UUID NULL;
                    END IF;

                    IF NOT EXISTS (
                        SELECT FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = '{table_name}'
                          AND column_name = 'is_active'
                    ) THEN
                        ALTER TABLE {table_name}
                        ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;
                    END IF;

                    IF NOT EXISTS (
                        SELECT FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = '{table_name}'
                          AND column_name = 'version'
                    ) THEN
                        ALTER TABLE {table_name}
                        ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
                    END IF;
                END IF;
            END $$;
            """
        )


def downgrade() -> None:
    for table_name in reversed(FD_TABLES):
        op.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT FROM pg_tables
                    WHERE schemaname = 'public' AND tablename = '{table_name}'
                ) THEN
                    IF EXISTS (
                        SELECT FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = '{table_name}'
                          AND column_name = 'deleted_at'
                    ) THEN
                        ALTER TABLE {table_name} DROP COLUMN deleted_at;
                    END IF;

                    IF EXISTS (
                        SELECT FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = '{table_name}'
                          AND column_name = 'deleted_by'
                    ) THEN
                        ALTER TABLE {table_name} DROP COLUMN deleted_by;
                    END IF;
                END IF;
            END $$;
            """
        )
