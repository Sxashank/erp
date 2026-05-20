"""Align inventory enum column types with SQLAlchemy models.

Revision ID: zzc43_align_inventory_enum_types
Revises: zzc42_relax_legacy_inventory_columns
Create Date: 2026-05-18
"""

from alembic import op


revision = "zzc43_align_inventory_enum_types"
down_revision = "zzc42_relax_legacy_inventory_columns"
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
    _create_enum("itemtype", ("STOCK", "SERVICE", "CONSUMABLE", "FIXED_ASSET"))
    _create_enum(
        "unitofmeasure",
        (
            "EACH",
            "BOX",
            "CARTON",
            "PACK",
            "KG",
            "GRAM",
            "LITER",
            "ML",
            "METER",
            "CM",
            "PIECE",
            "SET",
            "PAIR",
            "DOZEN",
            "REAM",
        ),
    )
    _create_enum("warehousetype", ("MAIN", "BRANCH", "TRANSIT", "VIRTUAL"))

    op.execute("ALTER TABLE mst_item_master ALTER COLUMN item_type DROP DEFAULT")
    op.execute("ALTER TABLE mst_item_master ALTER COLUMN uom DROP DEFAULT")
    op.execute("ALTER TABLE mst_warehouse ALTER COLUMN warehouse_type DROP DEFAULT")

    op.execute(
        "ALTER TABLE mst_item_master ALTER COLUMN item_type TYPE itemtype "
        "USING COALESCE(item_type, 'STOCK')::itemtype"
    )
    op.execute(
        "ALTER TABLE mst_item_master ALTER COLUMN uom TYPE unitofmeasure "
        "USING COALESCE(uom, primary_uom, 'EACH')::unitofmeasure"
    )
    op.execute(
        "ALTER TABLE mst_warehouse ALTER COLUMN warehouse_type TYPE warehousetype "
        "USING COALESCE(warehouse_type, 'MAIN')::warehousetype"
    )
    op.execute("ALTER TABLE mst_item_master ALTER COLUMN item_type SET DEFAULT 'STOCK'::itemtype")
    op.execute("ALTER TABLE mst_item_master ALTER COLUMN uom SET DEFAULT 'EACH'::unitofmeasure")
    op.execute("ALTER TABLE mst_warehouse ALTER COLUMN warehouse_type SET DEFAULT 'MAIN'::warehousetype")


def downgrade() -> None:
    op.execute("ALTER TABLE mst_warehouse ALTER COLUMN warehouse_type DROP DEFAULT")
    op.execute("ALTER TABLE mst_item_master ALTER COLUMN uom DROP DEFAULT")
    op.execute("ALTER TABLE mst_item_master ALTER COLUMN item_type DROP DEFAULT")
    op.execute("ALTER TABLE mst_warehouse ALTER COLUMN warehouse_type TYPE VARCHAR USING warehouse_type::text")
    op.execute("ALTER TABLE mst_item_master ALTER COLUMN uom TYPE VARCHAR USING uom::text")
    op.execute("ALTER TABLE mst_item_master ALTER COLUMN item_type TYPE VARCHAR USING item_type::text")
