"""Align BI enum type names with SQLAlchemy defaults.

Revision ID: zzc47_align_bi_enum_contracts
Revises: zzc46_add_missing_court_contact_columns
Create Date: 2026-05-18
"""

from alembic import op


revision = "zzc47_align_bi_enum_contracts"
down_revision = "zzc46_add_missing_court_contact_columns"
branch_labels = None
depends_on = None


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
    _create_enum(
        "widgettype",
        (
            "KPI_CARD",
            "LINE_CHART",
            "BAR_CHART",
            "PIE_CHART",
            "DONUT_CHART",
            "AREA_CHART",
            "DATA_TABLE",
            "TEXT_MARKDOWN",
            "GAUGE_PROGRESS",
        ),
    )
    _create_enum("charttype", ("LINE", "BAR", "PIE", "DONUT", "AREA", "GAUGE", "KPI", "TABLE"))
    _create_enum(
        "bimodule",
        (
            "FINANCE",
            "LENDING",
            "HR",
            "TREASURY",
            "PROCUREMENT",
            "INVENTORY",
            "TAX",
            "COLLECTIONS",
            "LEGAL",
            "PORTAL",
        ),
    )
    _create_enum("datasourcetype", ("API_ENDPOINT", "SQL_QUERY", "STATIC"))
    _create_enum("apimethod", ("GET", "POST"))

    op.execute("ALTER TABLE bi_data_source ALTER COLUMN source_type DROP DEFAULT")
    op.execute(
        "ALTER TABLE bi_data_source ALTER COLUMN source_type TYPE datasourcetype "
        "USING source_type::datasourcetype"
    )
    op.execute("ALTER TABLE bi_data_source ALTER COLUMN api_method DROP DEFAULT")
    op.execute(
        "ALTER TABLE bi_data_source ALTER COLUMN api_method TYPE apimethod "
        "USING api_method::apimethod"
    )
    op.execute("ALTER TABLE bi_data_source ALTER COLUMN api_method SET DEFAULT 'GET'::apimethod")

    op.execute("ALTER TABLE bi_chart_definition ALTER COLUMN module DROP DEFAULT")
    op.execute(
        "ALTER TABLE bi_chart_definition ALTER COLUMN module TYPE bimodule "
        "USING module::bimodule"
    )
    op.execute("ALTER TABLE bi_chart_definition ALTER COLUMN chart_type DROP DEFAULT")
    op.execute(
        "ALTER TABLE bi_chart_definition ALTER COLUMN chart_type TYPE charttype "
        "USING chart_type::charttype"
    )

    op.execute("ALTER TABLE bi_dashboard_widget ALTER COLUMN widget_type DROP DEFAULT")
    op.execute(
        "ALTER TABLE bi_dashboard_widget ALTER COLUMN widget_type TYPE widgettype "
        "USING widget_type::widgettype"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE IF EXISTS bi_dashboard_widget ALTER COLUMN widget_type TYPE VARCHAR USING widget_type::text")
    op.execute("ALTER TABLE IF EXISTS bi_chart_definition ALTER COLUMN chart_type TYPE VARCHAR USING chart_type::text")
    op.execute("ALTER TABLE IF EXISTS bi_chart_definition ALTER COLUMN module TYPE VARCHAR USING module::text")
    op.execute("ALTER TABLE IF EXISTS bi_data_source ALTER COLUMN api_method TYPE VARCHAR USING api_method::text")
    op.execute("ALTER TABLE IF EXISTS bi_data_source ALTER COLUMN source_type TYPE VARCHAR USING source_type::text")
