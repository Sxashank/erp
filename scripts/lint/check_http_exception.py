#!/usr/bin/env python3
"""Ban `raise HTTPException(...)` in `backend/app/api/v1/**`.

CLAUDE.md §7 requires every error response to use the canonical envelope
`{error_code, message, correlation_id, details?}`. The only way to emit that
envelope is to raise a typed `AppException` subclass from
`app.core.exceptions` — FastAPI's `HTTPException` returns the default
`{detail: ...}` body that breaks the frontend `showErrorToast` contract.

This script is wired into pre-commit at the end of Wave 3.

Exit codes:
  0 — no violations
  1 — at least one new `raise HTTPException` site found
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "backend" / "app" / "api" / "v1"

# Frozen LOS namespace — out of scope for this sweep.
LOS_FILES = {
    API_ROOT / "lending" / "entities.py",
    API_ROOT / "lending" / "products.py",
    API_ROOT / "lending" / "applications.py",
    API_ROOT / "lending" / "sanctions.py",
}

RAISE_RE = re.compile(r"^\s*raise\s+HTTPException\b")


def main() -> int:
    violations: list[tuple[Path, int, str]] = []
    for path in sorted(API_ROOT.rglob("*.py")):
        if path in LOS_FILES:
            continue
        for i, line in enumerate(path.read_text().splitlines(), start=1):
            if RAISE_RE.match(line):
                violations.append((path.relative_to(ROOT), i, line.strip()))

    if not violations:
        return 0

    print("error: `raise HTTPException(...)` found in backend/app/api/v1/**.", file=sys.stderr)
    print("       Use a typed `AppException` subclass from `app.core.exceptions`", file=sys.stderr)
    print("       so the error envelope (error_code/message/correlation_id) is preserved.", file=sys.stderr)
    print("       (CLAUDE.md §7 + Appendix C, Convention Sweep Wave 3.)", file=sys.stderr)
    print("", file=sys.stderr)
    for path, line_no, src in violations:
        print(f"  {path}:{line_no}: {src}", file=sys.stderr)
    print("", file=sys.stderr)
    print(f"  Total: {len(violations)} site(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
