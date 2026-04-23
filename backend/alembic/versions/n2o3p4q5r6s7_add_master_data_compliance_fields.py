"""add_master_data_compliance_fields

Revision ID: n2o3p4q5r6s7
Revises: m1n2o3p4q5r6
Create Date: 2026-01-12 15:00:00.000000

Add MSME type, LDC fields to Vendor and MSME/E-Invoice fields to Customer.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'n2o3p4q5r6s7'
down_revision: Union[str, None] = 'm1n2o3p4q5r6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create MSMEType enum
    msme_type_enum = postgresql.ENUM(
        'MICRO', 'SMALL', 'MEDIUM', 'NOT_APPLICABLE',
        name='msmetype',
        create_type=False
    )
    msme_type_enum.create(op.get_bind(), checkfirst=True)

    # === VENDOR TABLE UPDATES ===

    # Add msme_type column
    op.add_column(
        'mst_vendor',
        sa.Column(
            'msme_type',
            sa.Enum('MICRO', 'SMALL', 'MEDIUM', 'NOT_APPLICABLE', name='msmetype'),
            nullable=False,
            server_default='NOT_APPLICABLE',
            comment='MSME classification: MICRO, SMALL, MEDIUM'
        )
    )

    # Add msme_valid_until
    op.add_column(
        'mst_vendor',
        sa.Column(
            'msme_valid_until',
            sa.Date,
            nullable=True,
            comment='MSME certificate validity date'
        )
    )

    # Add LDC fields to vendor
    op.add_column(
        'mst_vendor',
        sa.Column(
            'ldc_certificate_no',
            sa.String(50),
            nullable=True,
            comment='Lower Deduction Certificate number'
        )
    )

    op.add_column(
        'mst_vendor',
        sa.Column(
            'ldc_rate',
            sa.Numeric(5, 2),
            nullable=True,
            comment='Lower TDS rate as per certificate (e.g., 0.5%)'
        )
    )

    op.add_column(
        'mst_vendor',
        sa.Column(
            'ldc_limit',
            sa.Numeric(18, 2),
            nullable=True,
            comment='Maximum amount covered under LDC'
        )
    )

    op.add_column(
        'mst_vendor',
        sa.Column(
            'ldc_valid_from',
            sa.Date,
            nullable=True,
            comment='LDC validity start date'
        )
    )

    op.add_column(
        'mst_vendor',
        sa.Column(
            'ldc_valid_until',
            sa.Date,
            nullable=True,
            comment='LDC validity end date'
        )
    )

    op.add_column(
        'mst_vendor',
        sa.Column(
            'ldc_utilized',
            sa.Numeric(18, 2),
            nullable=False,
            server_default='0',
            comment='Amount utilized against LDC limit'
        )
    )

    # === CUSTOMER TABLE UPDATES ===

    # Add MSME fields to customer
    op.add_column(
        'mst_customer',
        sa.Column(
            'msme_registered',
            sa.Boolean,
            nullable=False,
            server_default='false',
            comment='Is MSME registered'
        )
    )

    op.add_column(
        'mst_customer',
        sa.Column(
            'msme_number',
            sa.String(20),
            nullable=True,
            comment='MSME registration number (UAM/Udyam)'
        )
    )

    op.add_column(
        'mst_customer',
        sa.Column(
            'msme_type',
            sa.Enum('MICRO', 'SMALL', 'MEDIUM', 'NOT_APPLICABLE', name='msmetype'),
            nullable=False,
            server_default='NOT_APPLICABLE',
            comment='MSME classification: MICRO, SMALL, MEDIUM'
        )
    )

    op.add_column(
        'mst_customer',
        sa.Column(
            'msme_valid_until',
            sa.Date,
            nullable=True,
            comment='MSME certificate validity date'
        )
    )

    # Add E-Invoice fields to customer
    op.add_column(
        'mst_customer',
        sa.Column(
            'e_invoice_applicable',
            sa.Boolean,
            nullable=False,
            server_default='true',
            comment='Is E-Invoice applicable for this customer'
        )
    )

    op.add_column(
        'mst_customer',
        sa.Column(
            'e_invoice_exemption_reason',
            sa.Text,
            nullable=True,
            comment='Reason for E-Invoice exemption if not applicable'
        )
    )


def downgrade() -> None:
    # Remove customer fields
    op.drop_column('mst_customer', 'e_invoice_exemption_reason')
    op.drop_column('mst_customer', 'e_invoice_applicable')
    op.drop_column('mst_customer', 'msme_valid_until')
    op.drop_column('mst_customer', 'msme_type')
    op.drop_column('mst_customer', 'msme_number')
    op.drop_column('mst_customer', 'msme_registered')

    # Remove vendor fields
    op.drop_column('mst_vendor', 'ldc_utilized')
    op.drop_column('mst_vendor', 'ldc_valid_until')
    op.drop_column('mst_vendor', 'ldc_valid_from')
    op.drop_column('mst_vendor', 'ldc_limit')
    op.drop_column('mst_vendor', 'ldc_rate')
    op.drop_column('mst_vendor', 'ldc_certificate_no')
    op.drop_column('mst_vendor', 'msme_valid_until')
    op.drop_column('mst_vendor', 'msme_type')

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS msmetype")
