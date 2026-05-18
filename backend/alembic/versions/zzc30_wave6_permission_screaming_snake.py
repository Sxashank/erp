"""Wave 6 — rename permission codes to SCREAMING_SNAKE_CASE.

Revision ID: zzc30_wave6_permission_screaming_snake
Revises: zzc29_add_report_runtime_tables
Create Date: 2026-05-18

Closes the Wave 6 Convention Sweep (CLAUDE.md §8.2 / Appendix C) on the
data plane. Backend lint, code rewrite, and seed data are kept in lockstep
so SUPER_ADMIN keeps its grants and FE permission strings line up with the
backend `RequirePermissions(...)` literals.

Strategy:
  1. For every permission whose code is in the old lowercase-dot/colon
     form, UPDATE `mst_permission.code` to the SCREAMING_SNAKE form.
     `mst_role_permission` references by FK (permission_id), so the
     mapping rows survive untouched and SUPER_ADMIN keeps its grants.
  2. For every new permission that did not previously exist in this
     deployment (AA_*, EINVOICE_*, EWAYBILL_*, GSTN_*, LEGAL_DELETE,
     LEGAL_APPROVE), INSERT the row and grant it to SUPER_ADMIN.
  3. Idempotent: every UPDATE/INSERT is guarded by a `WHERE NOT EXISTS`
     / `WHERE code = old`. Re-runs are a no-op.

This migration is tenant-agnostic — `mst_permission` and `mst_role` are
global master tables (no `organization_id`), so every tenant inherits
the new codes simultaneously.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "zzc30_wave6_permission_screaming_snake"
down_revision = "zzc29_add_report_runtime_tables"
branch_labels = None
depends_on = None


# --------------------------------------------------------------------------- #
# Mapping: old (lowercase-dot/colon) -> new (SCREAMING_SNAKE)
# --------------------------------------------------------------------------- #
RENAMES: list[tuple[str, str]] = [
    # COLLECTIONS
    ("collections:read", "COLLECTIONS_READ"),
    ("collections:create", "COLLECTIONS_CREATE"),
    ("collections:update", "COLLECTIONS_UPDATE"),
    ("collections:approve", "COLLECTIONS_APPROVE"),
    # NPA
    ("npa:read", "NPA_READ"),
    ("npa:create", "NPA_CREATE"),
    ("npa:update", "NPA_UPDATE"),
    # OTS
    ("ots:create", "OTS_CREATE"),
    ("ots:update", "OTS_UPDATE"),
    ("ots:approve", "OTS_APPROVE"),
    # Restructure
    ("restructure:create", "RESTRUCTURE_CREATE"),
    ("restructure:update", "RESTRUCTURE_UPDATE"),
    ("restructure:approve", "RESTRUCTURE_APPROVE"),
    # Write-off
    ("writeoff:create", "WRITEOFF_CREATE"),
    ("writeoff:approve", "WRITEOFF_APPROVE"),
    # Legal
    ("legal:read", "LEGAL_READ"),
    ("legal:create", "LEGAL_CREATE"),
    ("legal:update", "LEGAL_UPDATE"),
    # Treasury
    ("treasury:read", "TREASURY_READ"),
    ("treasury:write", "TREASURY_WRITE"),
    ("treasury:approve", "TREASURY_APPROVE"),
    # AA — older seed rows that pre-date the lint sweep; canonicalize for
    # symmetry with `AA_CONSENT_*` codes the API uses.
    ("aa.consent.read", "AA_CONSENT_READ"),
    ("aa.consent.write", "AA_CONSENT_WRITE"),
    # Stale row from an early seed; align with COLLECTIONS_* family.
    ("collections:write", "COLLECTIONS_WRITE"),
]


# Permissions referenced by `RequirePermissions(...)` in the API that did NOT
# previously have a constant declaration. Insert these fresh and grant them
# to SUPER_ADMIN so krishna (and any other SUPER_ADMIN holder) can hit the
# routes that consume them.
#
# (code, name, module, resource, action, description)
NEW_PERMISSIONS: list[tuple[str, str, str, str, str, str]] = [
    # Legal — variants beyond what existed
    ("LEGAL_DELETE", "Legal: Delete", "LENDING", "legal", "delete", "Delete legal cases / proceedings"),
    ("LEGAL_APPROVE", "Legal: Approve", "LENDING", "legal", "approve", "Approve legal actions"),
    # Account Aggregator (AA)
    ("AA_CONSENT_CREATE", "AA Consent: Create", "LENDING", "aa_consent", "create", "Create Account Aggregator consent requests"),
    ("AA_CONSENT_READ", "AA Consent: Read", "LENDING", "aa_consent", "read", "Read Account Aggregator consent records"),
    ("AA_CONSENT_WRITE", "AA Consent: Write", "LENDING", "aa_consent", "write", "Modify Account Aggregator consent records"),
    ("AA_CONSENT_REVOKE", "AA Consent: Revoke", "LENDING", "aa_consent", "revoke", "Revoke Account Aggregator consents"),
    ("AA_DATA_FETCH", "AA Data: Fetch", "LENDING", "aa_data", "fetch", "Fetch financial data via Account Aggregator"),
    ("AA_DATA_READ", "AA Data: Read", "LENDING", "aa_data", "read", "Read fetched Account Aggregator data"),
    ("AA_STATISTICS_READ", "AA Statistics: Read", "LENDING", "aa_statistics", "read", "Read Account Aggregator usage statistics"),
    # GST — e-Invoice / e-Way Bill
    ("EINVOICE_CREATE", "e-Invoice: Create", "GST", "einvoice", "create", "Generate e-Invoices via IRP"),
    ("EINVOICE_CANCEL", "e-Invoice: Cancel", "GST", "einvoice", "cancel", "Cancel previously generated e-Invoices"),
    ("EINVOICE_READ", "e-Invoice: Read", "GST", "einvoice", "read", "Read e-Invoice records and IRN/QR data"),
    ("EWAYBILL_CREATE", "e-Way Bill: Create", "GST", "ewaybill", "create", "Generate e-Way Bills"),
    ("EWAYBILL_CANCEL", "e-Way Bill: Cancel", "GST", "ewaybill", "cancel", "Cancel e-Way Bills"),
    ("EWAYBILL_READ", "e-Way Bill: Read", "GST", "ewaybill", "read", "Read e-Way Bill records"),
    ("EWAYBILL_UPDATE", "e-Way Bill: Update", "GST", "ewaybill", "update", "Update e-Way Bill vehicle / transporter details"),
    # GSTN portal
    ("GSTN_SESSION_CREATE", "GSTN Session: Create", "GST", "gstn_session", "create", "Create authenticated GSTN portal session"),
    ("GSTN_SESSION_READ", "GSTN Session: Read", "GST", "gstn_session", "read", "Read GSTN portal session state"),
    ("GSTN_RETURN_CREATE", "GSTN Return: Create", "GST", "gstn_return", "create", "Prepare GSTR returns for filing"),
    ("GSTN_RETURN_READ", "GSTN Return: Read", "GST", "gstn_return", "read", "Read GSTR return drafts and filings"),
    ("GSTN_RETURN_SUBMIT", "GSTN Return: Submit", "GST", "gstn_return", "submit", "Submit GSTR returns to GSTN"),
    ("GSTN_RETURN_FILE", "GSTN Return: File", "GST", "gstn_return", "file", "File GSTR returns (with DSC/EVC)"),
    ("GSTN_GSTR2B_FETCH", "GSTR-2B: Fetch", "GST", "gstn_gstr2b", "fetch", "Fetch GSTR-2B from GSTN"),
    ("GSTN_GSTR2B_READ", "GSTR-2B: Read", "GST", "gstn_gstr2b", "read", "Read GSTR-2B records"),
    ("GSTN_ITC_READ", "GSTN ITC: Read", "GST", "gstn_itc", "read", "Read ITC reconciliation state"),
    ("GSTN_ITC_RECONCILE", "GSTN ITC: Reconcile", "GST", "gstn_itc", "reconcile", "Run ITC reconciliation"),
    ("GSTN_ITC_RESOLVE", "GSTN ITC: Resolve", "GST", "gstn_itc", "resolve", "Resolve ITC mismatches"),
    ("GSTN_STATISTICS_READ", "GSTN Statistics: Read", "GST", "gstn_statistics", "read", "Read GSTN filing statistics"),
]


def _has_table(conn, name: str) -> bool:
    return conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = current_schema() AND table_name = :n"
        ),
        {"n": name},
    ).scalar() is not None


def upgrade() -> None:
    conn = op.get_bind()
    if not _has_table(conn, "mst_permission") or not _has_table(conn, "mst_role"):
        # Fresh DB before base tables — nothing to do; init seed will use the
        # new SCREAMING_SNAKE values directly.
        return

    # 1) Rename in place. References from map_role_permission survive
    #    because they FK on `permission_id`, not on `code`.
    for old, new in RENAMES:
        conn.execute(
            sa.text(
                """
                UPDATE mst_permission
                SET code = :new
                WHERE code = :old
                  AND NOT EXISTS (
                    SELECT 1 FROM mst_permission WHERE code = :new
                  )
                """
            ),
            {"old": old, "new": new},
        )
        # Edge case: both old + new rows exist (e.g. partial replay or a
        # seed that emitted both forms). Two sub-steps:
        #   (a) Drop role-mappings on the OLD row when the same role
        #       already holds the NEW row — otherwise the re-point UPDATE
        #       hits `uq_role_permission`.
        #   (b) Re-point remaining mappings on the OLD row to the NEW row.
        #   (c) Delete the orphaned OLD row.
        conn.execute(
            sa.text(
                """
                DELETE FROM map_role_permission rp_old
                USING mst_permission p_old, mst_permission p_new
                WHERE rp_old.permission_id = p_old.id
                  AND p_old.code = :old
                  AND p_new.code = :new
                  AND EXISTS (
                    SELECT 1 FROM map_role_permission rp_new
                    WHERE rp_new.role_id = rp_old.role_id
                      AND rp_new.permission_id = p_new.id
                  )
                """
            ),
            {"old": old, "new": new},
        )
        conn.execute(
            sa.text(
                """
                UPDATE map_role_permission rp
                SET permission_id = (SELECT id FROM mst_permission WHERE code = :new)
                WHERE permission_id IN (SELECT id FROM mst_permission WHERE code = :old)
                  AND EXISTS (SELECT 1 FROM mst_permission WHERE code = :new)
                """
            ),
            {"old": old, "new": new},
        )
        conn.execute(
            sa.text(
                """
                DELETE FROM mst_permission
                WHERE code = :old
                  AND EXISTS (SELECT 1 FROM mst_permission WHERE code = :new)
                """
            ),
            {"old": old, "new": new},
        )

    # 2) Insert net-new permissions (idempotent). Cast every parameter
    #    explicitly — asyncpg refuses to deduce types when the same
    #    placeholder is reused across SELECT-list and WHERE clause with
    #    different target column types (e.g. VARCHAR(100) vs TEXT).
    for code, name, module, resource, action, desc in NEW_PERMISSIONS:
        conn.execute(
            sa.text(
                """
                INSERT INTO mst_permission
                    (id, code, name, description, module, resource, action,
                     is_active, created_at, updated_at, created_by, updated_by)
                SELECT gen_random_uuid(),
                       CAST(:code AS VARCHAR),
                       CAST(:name AS VARCHAR),
                       CAST(:desc AS TEXT),
                       CAST(:module AS VARCHAR),
                       CAST(:resource AS VARCHAR),
                       CAST(:action AS VARCHAR),
                       TRUE, NOW(), NOW(), NULL, NULL
                WHERE NOT EXISTS (
                    SELECT 1 FROM mst_permission WHERE code = CAST(:code AS VARCHAR)
                )
                """
            ),
            {
                "code": code,
                "name": name,
                "desc": desc,
                "module": module,
                "resource": resource,
                "action": action,
            },
        )

    # 3) Grant every renamed + new permission to SUPER_ADMIN so krishna's
    #    role keeps full coverage.
    super_admin_id = conn.execute(
        sa.text("SELECT id FROM mst_role WHERE code = 'SUPER_ADMIN'")
    ).scalar()
    if super_admin_id is None:
        # No SUPER_ADMIN role yet — the role seed will create it later and
        # pick up these codes via `assign_all`.
        return

    all_new_codes = [new for _, new in RENAMES] + [c for c, *_ in NEW_PERMISSIONS]
    for code in all_new_codes:
        conn.execute(
            sa.text(
                """
                INSERT INTO map_role_permission
                    (role_id, permission_id, created_at, updated_at, created_by, updated_by)
                SELECT :role_id, p.id, NOW(), NOW(), NULL, NULL
                FROM mst_permission p
                WHERE p.code = :code
                  AND NOT EXISTS (
                    SELECT 1 FROM map_role_permission
                    WHERE role_id = :role_id AND permission_id = p.id
                  )
                """
            ),
            {"role_id": super_admin_id, "code": code},
        )


def downgrade() -> None:
    """Reverse the rename so an emergency rollback restores the old codes.

    The newly INSERTED rows (AA_*, EINVOICE_*, EWAYBILL_*, GSTN_*,
    LEGAL_DELETE, LEGAL_APPROVE) are NOT deleted on downgrade — the API
    layer is the system of record for what permissions exist, and dropping
    them here would orphan any role mapping created later.
    """
    conn = op.get_bind()
    if not _has_table(conn, "mst_permission"):
        return
    for old, new in RENAMES:
        conn.execute(
            sa.text(
                """
                UPDATE mst_permission
                SET code = :old
                WHERE code = :new
                  AND NOT EXISTS (
                    SELECT 1 FROM mst_permission WHERE code = :old
                  )
                """
            ),
            {"old": old, "new": new},
        )
