#!/usr/bin/env python3
"""Wave 2 codemod: service-level `commit()` → `flush()`.

Why: `get_db()` (in `backend/app/database.py`) already commits at the
end of each request and rolls back on exception. Explicit
`await self.session.commit()` inside service helpers therefore:
  - moves the transaction boundary INSIDE the service (CLAUDE.md §6.4
    violation),
  - makes partial state durable before the request completes (audit
    integrity risk: a later raise leaves the DB in a partial state),
  - prevents the request-level rollback from being effective.

`flush()` keeps the existing INSERT/UPDATE semantics (e.g. DB-generated
PKs become available for `refresh()` and FK use) without committing.

Scope: every `backend/app/services/**/*.py`. LOS services are NOT a
separate file; they live alongside other lending services, so we
process the whole tree.

Patterns rewritten:
  - `await self.session.commit()` → `await self.session.flush()`
  - `await self.db.commit()`       → `await self.db.flush()`
  - `await session.commit()`       → `await session.flush()`
  - `await db.commit()`            → `await db.flush()`

Skipped:
  - Files under `backend/app/scripts/` (seed / one-off scripts that
    legitimately open a session outside the FastAPI lifecycle).
  - Files under `backend/app/services/audit/` if any audit-chain
    finalisation requires explicit commit (none today, but reserved).
  - Lines that are commented out.
  - Test files (`tests/`).

Use `--dry-run` to preview.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVICES_ROOT = ROOT / "backend" / "app" / "services"

PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bawait\s+self\.session\.commit\(\)"), "await self.session.flush()"),
    (re.compile(r"\bawait\s+self\.db\.commit\(\)"), "await self.db.flush()"),
    (re.compile(r"\bawait\s+session\.commit\(\)"), "await session.flush()"),
    (re.compile(r"\bawait\s+db\.commit\(\)"), "await db.flush()"),
]

SKIP_DIR_PARTS = {"scripts", "tests"}


def _should_skip(path: Path) -> bool:
    parts = path.parts
    if any(p in SKIP_DIR_PARTS for p in parts):
        return True
    return False


def transform(text: str) -> tuple[str, int]:
    count = 0
    new_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            new_lines.append(line)
            continue
        new_line = line
        for pat, repl in PATTERNS:
            new_line, n = pat.subn(repl, new_line)
            count += n
        new_lines.append(new_line)
    new_text = "\n".join(new_lines)
    if text.endswith("\n"):
        new_text = new_text + "\n"
    return new_text, count


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    total_replacements = 0
    files_touched = 0
    for path in sorted(SERVICES_ROOT.rglob("*.py")):
        if _should_skip(path):
            continue
        text = path.read_text()
        new_text, count = transform(text)
        if count == 0:
            continue
        files_touched += 1
        total_replacements += count
        if args.dry_run:
            print(f"DRY {path.relative_to(ROOT)}: {count} replacement(s)")
        else:
            path.write_text(new_text)
            print(f"OK  {path.relative_to(ROOT)}: {count} replacement(s)")

    print(
        f"\n{'(dry-run) ' if args.dry_run else ''}"
        f"{total_replacements} replacement(s) across {files_touched} file(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
