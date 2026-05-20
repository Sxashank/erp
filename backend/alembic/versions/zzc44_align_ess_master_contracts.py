"""Align ESS master tables with BaseModel and enum contracts.

Revision ID: zzc44_align_ess_master_contracts
Revises: zzc43_align_inventory_enum_types
Create Date: 2026-05-18
"""

from alembic import op


revision = "zzc44_align_ess_master_contracts"
down_revision = "zzc43_align_inventory_enum_types"
branch_labels = None
depends_on = None


ESS_MASTER_TABLES = (
    "mst_it_declaration_section",
    "mst_reimbursement_category",
    "mst_helpdesk_category",
)


def _add_base_columns(table_name: str) -> None:
    op.execute(
        f"ALTER TABLE IF EXISTS {table_name} "
        "ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
    )
    op.execute(f"ALTER TABLE IF EXISTS {table_name} ADD COLUMN IF NOT EXISTS created_by UUID")
    op.execute(f"ALTER TABLE IF EXISTS {table_name} ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ")
    op.execute(f"ALTER TABLE IF EXISTS {table_name} ADD COLUMN IF NOT EXISTS updated_by UUID")
    op.execute(f"ALTER TABLE IF EXISTS {table_name} ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ")
    op.execute(f"ALTER TABLE IF EXISTS {table_name} ADD COLUMN IF NOT EXISTS deleted_by UUID")
    op.execute(
        f"ALTER TABLE IF EXISTS {table_name} "
        "ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE"
    )
    op.execute(
        f"ALTER TABLE IF EXISTS {table_name} "
        "ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1"
    )


def _create_enum(name: str, values: tuple[str, ...]) -> None:
    values_sql = ", ".join(f"'{value}'" for value in values)
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{name}') THEN
                CREATE TYPE {name} AS ENUM ({values_sql});
            END IF;
        END $$;
        """
    )


def upgrade() -> None:
    for table_name in ESS_MASTER_TABLES:
        _add_base_columns(table_name)

    _create_enum(
        "claim_type_enum",
        (
            "TRAVEL",
            "MEDICAL",
            "CONVEYANCE",
            "MOBILE",
            "INTERNET",
            "FOOD",
            "LOCAL_TRAVEL",
            "OUTSTATION_TRAVEL",
            "RELOCATION",
            "TRAINING",
            "CERTIFICATION",
            "OTHER",
        ),
    )
    _create_enum(
        "ticket_category_enum",
        (
            "HR_QUERY",
            "LEAVE_ISSUE",
            "SALARY_QUERY",
            "ATTENDANCE_ISSUE",
            "POLICY_CLARIFICATION",
            "DOCUMENT_REQUEST",
            "IT_SUPPORT",
            "HARDWARE_ISSUE",
            "SOFTWARE_ISSUE",
            "ACCESS_REQUEST",
            "NETWORK_ISSUE",
            "OTHER",
        ),
    )

    op.execute(
        """
        UPDATE mst_reimbursement_category
        SET claim_type = CASE claim_type
            WHEN 'TRV' THEN 'TRAVEL'
            WHEN 'CONV' THEN 'CONVEYANCE'
            WHEN 'COMM' THEN 'MOBILE'
            WHEN 'MED' THEN 'MEDICAL'
            WHEN 'RELOC' THEN 'RELOCATION'
            WHEN 'TRAIN' THEN 'TRAINING'
            WHEN 'BOOKS' THEN 'CERTIFICATION'
            WHEN 'CLIENT' THEN 'OUTSTATION_TRAVEL'
            WHEN 'WFH' THEN 'INTERNET'
            WHEN 'MISC' THEN 'OTHER'
            ELSE claim_type
        END
        WHERE claim_type IN ('TRV', 'CONV', 'COMM', 'MED', 'RELOC', 'TRAIN', 'BOOKS', 'CLIENT', 'WFH', 'MISC')
        """
    )
    op.execute(
        """
        UPDATE mst_helpdesk_category
        SET category_type = CASE category_type
            WHEN 'HR' THEN 'HR_QUERY'
            WHEN 'IT' THEN 'IT_SUPPORT'
            WHEN 'ADMIN' THEN 'OTHER'
            WHEN 'FINANCE' THEN 'SALARY_QUERY'
            ELSE category_type
        END
        WHERE category_type IN ('HR', 'IT', 'ADMIN', 'FINANCE')
        """
    )

    op.execute("ALTER TABLE mst_reimbursement_category ALTER COLUMN claim_type DROP DEFAULT")
    op.execute(
        "ALTER TABLE mst_reimbursement_category ALTER COLUMN claim_type TYPE claim_type_enum "
        "USING claim_type::claim_type_enum"
    )

    op.execute("ALTER TABLE mst_helpdesk_category ALTER COLUMN category_type DROP DEFAULT")
    op.execute(
        "ALTER TABLE mst_helpdesk_category ALTER COLUMN category_type TYPE ticket_category_enum "
        "USING category_type::ticket_category_enum"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE IF EXISTS mst_helpdesk_category ALTER COLUMN category_type TYPE VARCHAR "
        "USING category_type::text"
    )
    op.execute(
        "ALTER TABLE IF EXISTS mst_reimbursement_category ALTER COLUMN claim_type TYPE VARCHAR "
        "USING claim_type::text"
    )
