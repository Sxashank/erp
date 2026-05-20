"""Align legal master tables with current ORM contracts.

Revision ID: zzc45_align_legal_master_contracts
Revises: zzc44_align_ess_master_contracts
Create Date: 2026-05-18
"""

from alembic import op


revision = "zzc45_align_legal_master_contracts"
down_revision = "zzc44_align_ess_master_contracts"
branch_labels = None
depends_on = None


LEGAL_MASTER_TABLES = (
    "mst_expense_category",
    "mst_statutory_period",
    "mst_court",
    "mst_court_bench",
    "mst_court_fee_slab",
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


def upgrade() -> None:
    for table_name in LEGAL_MASTER_TABLES:
        _add_base_columns(table_name)

    op.execute("ALTER TABLE IF EXISTS mst_expense_category ADD COLUMN IF NOT EXISTS category_code VARCHAR(50)")
    op.execute("ALTER TABLE IF EXISTS mst_expense_category ADD COLUMN IF NOT EXISTS category_name VARCHAR(200)")
    op.execute("ALTER TABLE IF EXISTS mst_expense_category ADD COLUMN IF NOT EXISTS tds_applicable BOOLEAN NOT NULL DEFAULT FALSE")
    op.execute("ALTER TABLE IF EXISTS mst_expense_category ADD COLUMN IF NOT EXISTS tds_section VARCHAR(20)")
    op.execute("ALTER TABLE IF EXISTS mst_expense_category ADD COLUMN IF NOT EXISTS tds_rate NUMERIC(5, 2)")
    op.execute("ALTER TABLE IF EXISTS mst_expense_category ADD COLUMN IF NOT EXISTS gst_applicable BOOLEAN NOT NULL DEFAULT FALSE")
    op.execute("ALTER TABLE IF EXISTS mst_expense_category ADD COLUMN IF NOT EXISTS gst_rate NUMERIC(5, 2)")
    op.execute("ALTER TABLE IF EXISTS mst_expense_category ADD COLUMN IF NOT EXISTS hsn_sac_code VARCHAR(20)")
    op.execute("ALTER TABLE IF EXISTS mst_expense_category ADD COLUMN IF NOT EXISTS recoverable_from_borrower BOOLEAN NOT NULL DEFAULT TRUE")
    op.execute("ALTER TABLE IF EXISTS mst_expense_category ADD COLUMN IF NOT EXISTS recovery_priority INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE IF EXISTS mst_expense_category ADD COLUMN IF NOT EXISTS display_order INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE IF EXISTS mst_expense_category ADD COLUMN IF NOT EXISTS description TEXT")
    op.execute("UPDATE mst_expense_category SET category_code = COALESCE(category_code, code)")
    op.execute("UPDATE mst_expense_category SET category_name = COALESCE(category_name, name)")
    op.execute("ALTER TABLE IF EXISTS mst_expense_category ALTER COLUMN code DROP NOT NULL")
    op.execute("ALTER TABLE IF EXISTS mst_expense_category ALTER COLUMN name DROP NOT NULL")

    op.execute("ALTER TABLE IF EXISTS mst_statutory_period ADD COLUMN IF NOT EXISTS provision_code VARCHAR(50)")
    op.execute("ALTER TABLE IF EXISTS mst_statutory_period ADD COLUMN IF NOT EXISTS provision_name VARCHAR(200)")
    op.execute("ALTER TABLE IF EXISTS mst_statutory_period ADD COLUMN IF NOT EXISTS section_reference VARCHAR(100)")
    op.execute("ALTER TABLE IF EXISTS mst_statutory_period ADD COLUMN IF NOT EXISTS period_months INTEGER")
    op.execute("ALTER TABLE IF EXISTS mst_statutory_period ADD COLUMN IF NOT EXISTS period_years INTEGER")
    op.execute("ALTER TABLE IF EXISTS mst_statutory_period ADD COLUMN IF NOT EXISTS period_description VARCHAR(100)")
    op.execute("ALTER TABLE IF EXISTS mst_statutory_period ADD COLUMN IF NOT EXISTS start_event VARCHAR(200)")
    op.execute("ALTER TABLE IF EXISTS mst_statutory_period ADD COLUMN IF NOT EXISTS includes_holidays BOOLEAN NOT NULL DEFAULT TRUE")
    op.execute("ALTER TABLE IF EXISTS mst_statutory_period ADD COLUMN IF NOT EXISTS extension_allowed BOOLEAN NOT NULL DEFAULT FALSE")
    op.execute("ALTER TABLE IF EXISTS mst_statutory_period ADD COLUMN IF NOT EXISTS extension_grounds TEXT")
    op.execute("ALTER TABLE IF EXISTS mst_statutory_period ADD COLUMN IF NOT EXISTS applicable_forums JSONB")
    op.execute("ALTER TABLE IF EXISTS mst_statutory_period ADD COLUMN IF NOT EXISTS applicable_case_types JSONB")
    op.execute("ALTER TABLE IF EXISTS mst_statutory_period ADD COLUMN IF NOT EXISTS alert_before_days JSONB")
    op.execute("ALTER TABLE IF EXISTS mst_statutory_period ADD COLUMN IF NOT EXISTS legal_reference TEXT")
    op.execute("ALTER TABLE IF EXISTS mst_statutory_period ADD COLUMN IF NOT EXISTS description TEXT")
    op.execute("UPDATE mst_statutory_period SET provision_code = COALESCE(provision_code, code)")
    op.execute("UPDATE mst_statutory_period SET provision_name = COALESCE(provision_name, name)")
    op.execute("UPDATE mst_statutory_period SET section_reference = COALESCE(section_reference, section)")
    op.execute("UPDATE mst_statutory_period SET start_event = COALESCE(start_event, trigger_event)")
    op.execute("ALTER TABLE IF EXISTS mst_statutory_period ALTER COLUMN code DROP NOT NULL")
    op.execute("ALTER TABLE IF EXISTS mst_statutory_period ALTER COLUMN name DROP NOT NULL")

    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS court_code VARCHAR(50)")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS court_name VARCHAR(300)")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS short_name VARCHAR(50)")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS jurisdiction_area TEXT")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS bench_number VARCHAR(20)")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS circuit_bench BOOLEAN NOT NULL DEFAULT FALSE")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS circuit_location VARCHAR(200)")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS establishment_date DATE")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS working_days JSONB")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS working_hours VARCHAR(50)")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS filing_time VARCHAR(50)")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS e_filing_enabled BOOLEAN NOT NULL DEFAULT FALSE")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS e_filing_portal VARCHAR(255)")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS e_filing_instructions TEXT")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS parent_court_id UUID")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS appellate_court_id UUID")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS min_claim_amount NUMERIC(18, 2)")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS max_claim_amount NUMERIC(18, 2)")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS presiding_officer VARCHAR(200)")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS presiding_officer_designation VARCHAR(100)")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS registrar VARCHAR(200)")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS is_operational BOOLEAN NOT NULL DEFAULT TRUE")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS remarks TEXT")
    op.execute("ALTER TABLE IF EXISTS mst_court ADD COLUMN IF NOT EXISTS district VARCHAR(100)")
    op.execute("UPDATE mst_court SET court_code = COALESCE(court_code, code)")
    op.execute("UPDATE mst_court SET court_name = COALESCE(court_name, name)")
    op.execute("UPDATE mst_court SET min_claim_amount = COALESCE(min_claim_amount, pecuniary_limit_min)")
    op.execute("UPDATE mst_court SET max_claim_amount = COALESCE(max_claim_amount, pecuniary_limit_max)")
    op.execute("ALTER TABLE IF EXISTS mst_court ALTER COLUMN code DROP NOT NULL")
    op.execute("ALTER TABLE IF EXISTS mst_court ALTER COLUMN name DROP NOT NULL")

    op.execute("ALTER TABLE IF EXISTS mst_court_fee_slab ADD COLUMN IF NOT EXISTS organization_id UUID")
    op.execute("ALTER TABLE IF EXISTS mst_court_fee_slab ADD COLUMN IF NOT EXISTS court_type VARCHAR(50)")
    op.execute("ALTER TABLE IF EXISTS mst_court_fee_slab ADD COLUMN IF NOT EXISTS min_claim_amount NUMERIC(18, 2)")
    op.execute("ALTER TABLE IF EXISTS mst_court_fee_slab ADD COLUMN IF NOT EXISTS max_claim_amount NUMERIC(18, 2)")
    op.execute("ALTER TABLE IF EXISTS mst_court_fee_slab ADD COLUMN IF NOT EXISTS calculation_type VARCHAR(20)")
    op.execute("ALTER TABLE IF EXISTS mst_court_fee_slab ADD COLUMN IF NOT EXISTS fixed_fee NUMERIC(12, 2)")
    op.execute("ALTER TABLE IF EXISTS mst_court_fee_slab ADD COLUMN IF NOT EXISTS percentage_rate NUMERIC(8, 4)")
    op.execute("ALTER TABLE IF EXISTS mst_court_fee_slab ADD COLUMN IF NOT EXISTS min_fee NUMERIC(12, 2)")
    op.execute("ALTER TABLE IF EXISTS mst_court_fee_slab ADD COLUMN IF NOT EXISTS max_fee NUMERIC(12, 2)")
    op.execute("ALTER TABLE IF EXISTS mst_court_fee_slab ADD COLUMN IF NOT EXISTS process_fee NUMERIC(12, 2)")
    op.execute("ALTER TABLE IF EXISTS mst_court_fee_slab ADD COLUMN IF NOT EXISTS service_fee NUMERIC(12, 2)")
    op.execute("ALTER TABLE IF EXISTS mst_court_fee_slab ADD COLUMN IF NOT EXISTS exemption_available BOOLEAN NOT NULL DEFAULT FALSE")
    op.execute("ALTER TABLE IF EXISTS mst_court_fee_slab ADD COLUMN IF NOT EXISTS exemption_conditions TEXT")
    op.execute("ALTER TABLE IF EXISTS mst_court_fee_slab ADD COLUMN IF NOT EXISTS notification_reference VARCHAR(200)")
    op.execute("ALTER TABLE IF EXISTS mst_court_fee_slab ADD COLUMN IF NOT EXISTS remarks TEXT")
    op.execute("UPDATE mst_court_fee_slab SET min_claim_amount = COALESCE(min_claim_amount, claim_min)")
    op.execute("UPDATE mst_court_fee_slab SET max_claim_amount = COALESCE(max_claim_amount, claim_max)")
    op.execute("UPDATE mst_court_fee_slab SET fixed_fee = COALESCE(fixed_fee, fee_value)")
    op.execute("UPDATE mst_court_fee_slab SET calculation_type = COALESCE(calculation_type, 'FIXED')")
    op.execute("ALTER TABLE IF EXISTS mst_court_fee_slab ALTER COLUMN claim_min DROP NOT NULL")
    op.execute("ALTER TABLE IF EXISTS mst_court_fee_slab ALTER COLUMN fee_value DROP NOT NULL")


def downgrade() -> None:
    pass
