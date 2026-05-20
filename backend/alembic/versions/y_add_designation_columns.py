"""Add missing designation columns.

Revision ID: y_add_designation_columns
Revises: x_add_org_bank_address
Create Date: 2026-01-13

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'y_add_designation_columns'
down_revision: Union[str, None] = 'v1w2x3y4z5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS mst_organization_address (
            id UUID NOT NULL,
            organization_id UUID NOT NULL,
            address_type VARCHAR(30) NOT NULL,
            address_label VARCHAR(100),
            address_line1 VARCHAR(255) NOT NULL,
            address_line2 VARCHAR(255),
            address_line3 VARCHAR(255),
            landmark VARCHAR(200),
            city VARCHAR(100) NOT NULL,
            district VARCHAR(100),
            state_code VARCHAR(2) NOT NULL,
            state_name VARCHAR(100),
            pincode VARCHAR(10) NOT NULL,
            country VARCHAR(50) NOT NULL DEFAULT 'India',
            contact_person VARCHAR(200),
            phone VARCHAR(20),
            email VARCHAR(255),
            latitude NUMERIC(10, 8),
            longitude NUMERIC(11, 8),
            is_primary BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_by UUID,
            updated_at TIMESTAMPTZ,
            updated_by UUID,
            deleted_at TIMESTAMPTZ,
            deleted_by UUID,
            is_active BOOLEAN NOT NULL DEFAULT true,
            PRIMARY KEY (id),
            FOREIGN KEY (organization_id) REFERENCES mst_organization(id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES mst_user(id) ON DELETE SET NULL,
            FOREIGN KEY (updated_by) REFERENCES mst_user(id) ON DELETE SET NULL,
            FOREIGN KEY (deleted_by) REFERENCES mst_user(id) ON DELETE SET NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_mst_organization_address_organization_id ON mst_organization_address (organization_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_mst_organization_address_address_type ON mst_organization_address (address_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_org_address_org_type ON mst_organization_address (organization_id, address_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_org_address_org_active ON mst_organization_address (organization_id, is_active)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS mst_organization_bank_account (
            id UUID NOT NULL,
            organization_id UUID NOT NULL,
            account_name VARCHAR(200) NOT NULL,
            account_number VARCHAR(30) NOT NULL,
            ifsc_code VARCHAR(11) NOT NULL,
            bank_name VARCHAR(200) NOT NULL,
            branch_name VARCHAR(200),
            branch_address TEXT,
            micr_code VARCHAR(9),
            swift_code VARCHAR(11),
            account_type VARCHAR(20) NOT NULL DEFAULT 'CURRENT',
            ledger_account_id UUID,
            sanctioned_limit NUMERIC(18, 2),
            drawing_power NUMERIC(18, 2),
            is_primary BOOLEAN NOT NULL DEFAULT false,
            allow_payments BOOLEAN NOT NULL DEFAULT true,
            allow_receipts BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_by UUID,
            updated_at TIMESTAMPTZ,
            updated_by UUID,
            deleted_at TIMESTAMPTZ,
            deleted_by UUID,
            is_active BOOLEAN NOT NULL DEFAULT true,
            PRIMARY KEY (id),
            CONSTRAINT uq_org_bank_account_number UNIQUE (organization_id, account_number),
            FOREIGN KEY (organization_id) REFERENCES mst_organization(id) ON DELETE CASCADE,
            FOREIGN KEY (ledger_account_id) REFERENCES mst_account(id) ON DELETE SET NULL,
            FOREIGN KEY (created_by) REFERENCES mst_user(id) ON DELETE SET NULL,
            FOREIGN KEY (updated_by) REFERENCES mst_user(id) ON DELETE SET NULL,
            FOREIGN KEY (deleted_by) REFERENCES mst_user(id) ON DELETE SET NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_mst_organization_bank_account_organization_id ON mst_organization_bank_account (organization_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_org_bank_account_org_active ON mst_organization_bank_account (organization_id, is_active)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS mst_department (
            id UUID NOT NULL,
            code VARCHAR(20) NOT NULL,
            name VARCHAR(200) NOT NULL,
            short_name VARCHAR(50),
            description TEXT,
            organization_id UUID NOT NULL,
            parent_dept_id UUID,
            level INTEGER NOT NULL DEFAULT 1,
            path VARCHAR(500),
            cost_center_code VARCHAR(50),
            head_user_id UUID,
            head_name VARCHAR(200),
            email VARCHAR(255),
            phone VARCHAR(20),
            status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_by UUID,
            updated_at TIMESTAMPTZ,
            updated_by UUID,
            deleted_at TIMESTAMPTZ,
            deleted_by UUID,
            is_active BOOLEAN NOT NULL DEFAULT true,
            PRIMARY KEY (id),
            UNIQUE (code),
            FOREIGN KEY (organization_id) REFERENCES mst_organization(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_dept_id) REFERENCES mst_department(id) ON DELETE SET NULL,
            FOREIGN KEY (head_user_id) REFERENCES mst_user(id) ON DELETE SET NULL,
            FOREIGN KEY (created_by) REFERENCES mst_user(id) ON DELETE SET NULL,
            FOREIGN KEY (updated_by) REFERENCES mst_user(id) ON DELETE SET NULL,
            FOREIGN KEY (deleted_by) REFERENCES mst_user(id) ON DELETE SET NULL
        )
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_mst_department_code ON mst_department (code)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_mst_department_organization_id ON mst_department (organization_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_mst_department_parent_dept_id ON mst_department (parent_dept_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_mst_department_head_user_id ON mst_department (head_user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_mst_department_path ON mst_department (path)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_mst_department_status ON mst_department (status)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS mst_designation (
            id UUID NOT NULL,
            code VARCHAR(20) NOT NULL,
            name VARCHAR(200) NOT NULL,
            short_name VARCHAR(50),
            description TEXT,
            department_id UUID,
            level INTEGER NOT NULL DEFAULT 1,
            reporting_to_id UUID,
            approval_limit NUMERIC(18, 2),
            min_experience_years INTEGER NOT NULL DEFAULT 0,
            min_qualification VARCHAR(200),
            job_description TEXT,
            responsibilities TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_by UUID,
            updated_at TIMESTAMPTZ,
            updated_by UUID,
            deleted_at TIMESTAMPTZ,
            deleted_by UUID,
            is_active BOOLEAN NOT NULL DEFAULT true,
            PRIMARY KEY (id),
            UNIQUE (code),
            FOREIGN KEY (department_id) REFERENCES mst_department(id) ON DELETE SET NULL,
            FOREIGN KEY (reporting_to_id) REFERENCES mst_designation(id) ON DELETE SET NULL,
            FOREIGN KEY (created_by) REFERENCES mst_user(id) ON DELETE SET NULL,
            FOREIGN KEY (updated_by) REFERENCES mst_user(id) ON DELETE SET NULL,
            FOREIGN KEY (deleted_by) REFERENCES mst_user(id) ON DELETE SET NULL
        )
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_mst_designation_code ON mst_designation (code)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_mst_designation_department_id ON mst_designation (department_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_mst_designation_status ON mst_designation (status)")

    op.execute("ALTER TABLE mst_designation ADD COLUMN IF NOT EXISTS approval_limit NUMERIC(18, 2)")


def downgrade() -> None:
    op.drop_column('mst_designation', 'approval_limit')
