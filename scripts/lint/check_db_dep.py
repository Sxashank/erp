#!/usr/bin/env python3
"""Pre-commit + CI gate that bans `Depends(get_db)` on authenticated routes.

Per CLAUDE.md §3.4 + Appendix C: every authenticated route must use
`get_db_with_tenant` (or its alias) so the PostgreSQL RLS GUC is set before
the handler runs. Plain `Depends(get_db)` on an authenticated route is a
multi-tenant data-leakage path.

Scope (in scope: every module except LOS):
  - Walks `backend/app/api/v1/**`.
  - Skips the LOS namespace (entities / products / applications / sanctions /
    appraisals) — those routes are frozen until the LOS module is re-enabled.
  - Skips `backend/app/api/v1/auth/auth.py` (login endpoints execute before
    a user identity exists; plain `get_db` is correct there).
  - Skips `backend/app/api/v1/health.py`.

Exits 1 with a list of offending file:line locations if any violation is
found. Exit 0 otherwise.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "backend" / "app" / "api" / "v1"

# Files that LEGITIMATELY use plain `get_db` because no user identity exists
# yet (login, registration, public webhooks) or because the module is frozen
# until re-enabled (LOS namespace).
SKIP_PATHS = {
    # LOS namespace — frozen until module is re-enabled.
    "lending/entities.py",
    "lending/products.py",
    "lending/applications.py",
    "lending/sanctions.py",
    # Pre-auth routes — no current_user yet.
    "auth/auth.py",
    "health.py",
    "portal/auth.py",
    "portal/registration.py",
    "vendor_portal/auth.py",
    "vendor_portal/registration.py",
    "ess/auth.py",
    # Webhooks — external callers, no auth token.
    "webhooks/aa.py",
    "webhooks/bureau.py",
    "webhooks/nach.py",
    "webhooks/payment.py",
}

# Match `Depends(get_db)` (no qualifier — `get_db_with_tenant` is fine).
PATTERN = re.compile(r"\bDepends\(\s*get_db\s*\)")


def _is_in_scope(rel: Path) -> bool:
    rel_str = str(rel)
    return not any(rel_str.endswith(p) for p in SKIP_PATHS)


def main() -> int:
    violations: list[str] = []
    for path in sorted(API_ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT)
        if not _is_in_scope(rel):
            continue
        if path.name == "__init__.py":
            continue
        for lineno, line in enumerate(path.read_text().splitlines(), start=1):
            if PATTERN.search(line):
                # Ignore lines that are just imports or comments.
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                if stripped.startswith("from ") or stripped.startswith("import "):
                    continue
                violations.append(f"{rel}:{lineno}: {line.strip()}")

    if violations:
        print(
            "Banned `Depends(get_db)` on authenticated routes (CLAUDE.md §3.4):",
            file=sys.stderr,
        )
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        print(
            f"\n{len(violations)} offending line(s). Switch to `Depends(get_db_with_tenant)`.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
