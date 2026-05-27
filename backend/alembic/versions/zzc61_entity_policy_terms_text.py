"""Make borrower entity policy fields master-driven text codes.

Revision ID: zzc61_entity_policy_terms_text
Revises: zzc60_lending_policy_terms_text
Create Date: 2026-05-26
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "zzc61_entity_policy_terms_text"
down_revision: str | None = "zzc60_lending_policy_terms_text"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _to_text(table: str, column: str, enum_name: str, nullable: bool = False) -> None:
    op.alter_column(
        table,
        column,
        existing_nullable=nullable,
        type_=sa.String(length=80),
        existing_type=sa.Enum(name=enum_name),
        postgresql_using=f"{column}::text",
    )


def _to_enum(table: str, column: str, enum_name: str, nullable: bool = False) -> None:
    op.alter_column(
        table,
        column,
        existing_nullable=nullable,
        type_=sa.Enum(name=enum_name),
        existing_type=sa.String(length=80),
        postgresql_using=f"{column}::{enum_name}",
    )


def upgrade() -> None:
    _to_text("los_entity", "entity_type", "entitytype")
    _to_text("los_entity", "industry_sector", "industrysector", nullable=True)
    _to_text("los_entity", "risk_category", "riskcategory")
    _to_text("los_entity_contact", "contact_type", "contacttype")
    _to_text("los_entity_address", "address_type", "addresstype")


def downgrade() -> None:
    _to_enum("los_entity_address", "address_type", "addresstype")
    _to_enum("los_entity_contact", "contact_type", "contacttype")
    _to_enum("los_entity", "risk_category", "riskcategory")
    _to_enum("los_entity", "industry_sector", "industrysector", nullable=True)
    _to_enum("los_entity", "entity_type", "entitytype")
