"""Add Aadhaar and PAN integration enum values.

Revision ID: zzc69_add_identity_integration_types
Revises: zzc68_portal_registration_loan_verification
Create Date: 2026-06-12
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "zzc69_add_identity_integration_types"
down_revision: Union[str, None] = "zzc68_portal_registration_loan_verification"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_enum_value(enum_name: str, value: str) -> None:
    op.execute(f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{value}'")


def upgrade() -> None:
    _add_enum_value("integrationtype", "AADHAAR_KYC")
    _add_enum_value("integrationtype", "PAN_VERIFICATION")

    _add_enum_value("integrationprovider", "UIDAI")
    _add_enum_value("integrationprovider", "DIGILOCKER")
    _add_enum_value("integrationprovider", "KARZA")
    _add_enum_value("integrationprovider", "IDFY")
    _add_enum_value("integrationprovider", "NSDL_PAN")
    _add_enum_value("integrationprovider", "PROTEAN")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values safely. Leaving values in
    # place is intentional; unused enum values are harmless and preserve data.
    pass
