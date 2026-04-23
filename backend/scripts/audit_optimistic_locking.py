"""Audit optimistic-locking coverage across all SQLAlchemy models.

Walks the application's SQLAlchemy registry and reports every model that
is expected to be mutable (inherits BaseModel) but does NOT expose a
`version` column from VersionedMixin.

Usage:
    python scripts/audit_optimistic_locking.py

Exits non-zero if any non-compliant model is found. Intended for CI once
all pending remediations land.

See CLAUDE.md §6.3 ("Optimistic locking").
"""

from __future__ import annotations

import sys

# Importing app.main forces every model module to load so the SQLAlchemy
# registry is complete before we walk it.
import app.main  # noqa: F401
from app.database import Base
from app.models.base import BaseModel

# Tables we INTENTIONALLY exempt from optimistic locking. System-owned or
# append-only tables don't need versioning; document each exemption here.
EXEMPT_TABLES = {
    "idempotency_key",       # append-only; uniqueness + expiry handle replay
    "audit_log",             # append-only
    "audit_logs",
    "txn_audit_log",
    "alembic_version",
    "communication_log",
    "notification_log",
    "integration_log",
    "sys_integration_log",   # append-only log
    "gl_entry",              # append-only ledger; reversals are new rows
    "txn_gl_entry",
    "tenant_context",
    "audit_day_anchor",      # append-only daily SHA-256 anchor (hash chain)
    "txn_line_item_history", # append-only history
    "map_role_permission",   # pure link table, replaced wholesale
    "map_user_role",         # pure link table, replaced wholesale
    # AA (Account Aggregator) captured data — read-only snapshots from the
    # AA protocol. Modified only by re-fetch, never in-place.
    "lms_aa_bank_account",
    "lms_aa_bank_transaction",
    "lms_aa_consent",
    "lms_aa_consent_log",
    "lms_aa_fetch_session",
    # Credit bureau pull data — immutable once fetched.
    "lending_credit_pull",
    "lending_credit_enquiry",
}


def main() -> int:
    all_tables = list(Base.metadata.tables.keys())

    # Find every ORM class that inherits BaseModel (versioned + audited).
    versioned_mapped: dict[str, bool] = {}
    for cls in Base.registry.mappers:
        pyclass = cls.class_
        try:
            inherits_base = issubclass(pyclass, BaseModel)
        except TypeError:
            inherits_base = False
        table_name = pyclass.__tablename__ if hasattr(pyclass, "__tablename__") else None
        if not table_name:
            continue
        has_version = "version" in pyclass.__table__.c
        versioned_mapped[table_name] = has_version

    missing: list[str] = []
    present: list[str] = []
    exempt: list[str] = []

    for t, has_version in sorted(versioned_mapped.items()):
        if t in EXEMPT_TABLES:
            exempt.append(t)
        elif has_version:
            present.append(t)
        else:
            missing.append(t)

    print(f"[optimistic-lock audit] total tables in registry: {len(all_tables)}")
    print(f"[optimistic-lock audit] with `version` column:    {len(present)}")
    print(f"[optimistic-lock audit] exempt (by policy):       {len(exempt)}")
    print(f"[optimistic-lock audit] MISSING `version`:        {len(missing)}")

    if missing:
        print()
        print("MISSING optimistic-locking column on the following tables:")
        for t in missing:
            print(f"  - {t}")
        print()
        print("Add `version` via VersionedMixin (already on BaseModel) OR mark")
        print("the table exempt in EXEMPT_TABLES with a documented reason.")
        print("See CLAUDE.md §6.3 and .stubs-approved.md.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
