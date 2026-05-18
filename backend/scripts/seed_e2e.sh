#!/usr/bin/env bash
#
# seed_e2e.sh — bootstrap the dedicated E2E database for Playwright real-user tests.
#
# What it does (idempotent):
#   1. Targets a separate DB (default: smfc_erp_e2e) so dev data is never touched.
#   2. Runs alembic upgrade head against it.
#   3. Runs the canonical seed_data.py with overridden org code / name so the tenant
#      is "SMFC-E2E" (vs dev's "SMFC").
#
# Requires: `psql` not strictly needed; uses python+asyncpg + alembic via the
# existing .venv. Run from repo root or anywhere — paths are absolute.
#
# Usage:
#   bash backend/scripts/seed_e2e.sh
#
# Environment (with sane defaults — override only if needed):
#   E2E_DB_NAME      — Postgres database name (default: smfc_erp_e2e)
#   E2E_ORG_CODE     — tenant short code (default: SMFC-E2E)
#   E2E_ORG_NAME     — tenant display name (default: "SMFC E2E Sandbox")
#   SEED_ADMIN_*     — admin user overrides (passed through unchanged)
#

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${REPO_ROOT}/backend"

: "${E2E_DB_NAME:=smfc_erp_e2e}"
: "${E2E_ORG_CODE:=SMFC-E2E}"
: "${E2E_ORG_NAME:=SMFC E2E Sandbox}"
export E2E_ORG_CODE E2E_ORG_NAME E2E_DB_NAME

# Activate venv
if [[ -f .venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
else
  echo "ERROR: backend/.venv not found. Run pip install -r requirements.txt first." >&2
  exit 1
fi

# Override DB URL for the seed run only — keep dev .env untouched.
ALEMBIC_URL="postgresql+asyncpg://smfc:smfc_secret@localhost:5432/${E2E_DB_NAME}"
export DATABASE_URL="${ALEMBIC_URL}"
export SEED_ORG_CODE="${E2E_ORG_CODE}"
export SEED_ORG_NAME="${E2E_ORG_NAME}"
export SEED_ORG_LEGAL_NAME="${E2E_ORG_NAME}"

echo "==> [seed_e2e] DB:       ${E2E_DB_NAME}"
echo "==> [seed_e2e] org code: ${E2E_ORG_CODE}"
echo "==> [seed_e2e] org name: ${E2E_ORG_NAME}"

echo "==> [seed_e2e] creating enum types + tables via the canonical fresh-DB bootstrap"
python - <<'PY'
import asyncio

from app.database import engine, Base
import app.models  # noqa: F401  — registers all ORM tables
import app.models.lending  # noqa: F401
from app.db.bootstrap_enums import bootstrap_enums

async def main():
    async with engine.begin() as conn:
        # 1) Materialise every Postgres enum type referenced by the ORM,
        #    idempotently (no-op on a DB that already has them).
        count = await bootstrap_enums(conn, Base.metadata)
        print(f"  - ensured {count} enum type(s)")
        # 2) Now `create_all` is safe: every column's underlying enum type
        #    exists. `create_all` itself is idempotent — it skips tables that
        #    are already present.
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

asyncio.run(main())
PY

echo "==> [seed_e2e] alembic stamp head (matches schema state to migration head)"
# Pre-create alembic_version at the widened width so stamp (which doesn't
# run migrations, only inserts the version row) doesn't fail on long
# revision IDs. The widening is harmless on existing DBs. Same width as
# `alembic/env.py::do_run_migrations`.
python - <<'PY'
import asyncio
from app.database import engine
from sqlalchemy import text

async def main():
    async with engine.begin() as conn:
        await conn.execute(text(
            "CREATE TABLE IF NOT EXISTS alembic_version ("
            "version_num VARCHAR(128) NOT NULL, "
            "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"
        ))
    await engine.dispose()

asyncio.run(main())
PY
alembic stamp head

echo "==> [seed_e2e] python scripts/seed_data.py"
python scripts/seed_data.py

# Resolve the org UUID so callers (Playwright globalSetup) can pin tenant context.
ORG_ID="$(
  python - <<PY
import asyncio, os
import asyncpg

async def main():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"].replace("postgresql+asyncpg", "postgresql"))
    try:
        row = await conn.fetchrow("SELECT id FROM mst_organization WHERE code = \$1", os.environ["E2E_ORG_CODE"])
        if not row:
            raise SystemExit(f"E2E org {os.environ['E2E_ORG_CODE']!r} not found after seed")
        print(str(row["id"]))
    finally:
        await conn.close()

asyncio.run(main())
PY
)"

echo "==> [seed_e2e] E2E org id: ${ORG_ID}"
echo "${ORG_ID}" > "${REPO_ROOT}/playwright/.e2e-org-id"
echo "==> [seed_e2e] wrote ${REPO_ROOT}/playwright/.e2e-org-id"
echo "==> [seed_e2e] done"
