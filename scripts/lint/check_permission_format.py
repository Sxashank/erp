#!/usr/bin/env python3
"""Pre-commit + CI gate that enforces the canonical permission format.

Per CLAUDE.md §8.2 + Appendix C: permission strings are
`SCREAMING_SNAKE_CASE` (e.g. `FIN_VOUCHER_POST`). Lowercase-dot
(`foo.bar`) and colon (`foo:bar`) styles are legacy outliers being
migrated; new occurrences are rejected at commit time.

Walks `backend/app/api/v1/**`; reports any
`RequirePermissions("<non-screaming-snake>")` it finds.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "backend" / "app" / "api" / "v1"

# Matches a string arg to RequirePermissions that contains a `.` or `:`.
# Example offenders: "treasury:read", "aa.consent.read", "legal.law_firm.read".
OFFENDER = re.compile(r'RequirePermissions\(\s*"([^"]*[\.:][^"]*)"')


def main() -> int:
    violations: list[str] = []
    for path in sorted(API_ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT)
        if path.name == "__init__.py":
            continue
        for lineno, line in enumerate(path.read_text().splitlines(), start=1):
            m = OFFENDER.search(line)
            if not m:
                continue
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            violations.append(f"{rel}:{lineno}: RequirePermissions({m.group(1)!r})")

    if violations:
        print(
            "Banned non-SCREAMING_SNAKE permission strings (CLAUDE.md §8.2):",
            file=sys.stderr,
        )
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        print(
            f"\n{len(violations)} offending line(s). Use SCREAMING_SNAKE_CASE; "
            "register the constant in backend/app/core/constants.py::Permissions.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
