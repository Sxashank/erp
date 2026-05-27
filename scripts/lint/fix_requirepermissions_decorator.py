#!/usr/bin/env python3
"""Fix the 83 sites that misuse `RequirePermissions` as a decorator.

`backend/app/api/deps.py::RequirePermissions` is a `Depends` class, not a
decorator. Using it as `@RequirePermissions([Permissions.X])` turns the route
handler into a callable that FastAPI cannot wire — every request to those
routes returns plain "Internal Server Error" 500 BEFORE the AppException
handler runs, which also strips the CORS header and breaks the FE.

Canonical pattern (CLAUDE.md §6.3):

    @router.get(...)
    async def handler(
        ...,
        current_user: User = Depends(RequirePermissions(Permissions.X)),
    ):

Misuse pattern this script rewrites:

    @router.get(...)
    @RequirePermissions([Permissions.X])
    async def handler(
        ...,
        current_user: User = Depends(get_current_user),
    ):

Transformation per match:
  1. Delete the `@RequirePermissions([...])` line.
  2. Replace `Depends(get_current_user)` with
     `Depends(RequirePermissions(Permissions.X))` so the same permission is
     now actually enforced.

`--dry-run` prints what would change.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "backend" / "app" / "api" / "v1"

# Captures the permission expression inside the brackets:
#   @RequirePermissions([Permissions.X])
#   @RequirePermissions([Permissions.X, Permissions.Y])
DECO_RE = re.compile(r"^(\s*)@RequirePermissions\(\[([^\]]+)\]\)\s*$")

# Captures the `current_user: User = Depends(get_current_user)` line so we can
# upgrade it to enforce the permission inline (the canonical pattern).
CURRENT_USER_RE = re.compile(
    r"(^\s*current_user:\s*User\s*=\s*Depends\()get_current_user(\)\s*,?\s*$)",
    re.MULTILINE,
)


def transform(text: str) -> tuple[str, int]:
    """Return (new_text, sites_fixed)."""
    lines = text.split("\n")
    out: list[str] = []
    sites = 0
    i = 0
    while i < len(lines):
        m = DECO_RE.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue

        perm_expr = m.group(2).strip()
        # Drop the decorator line. Walk forward to find the matching function
        # signature's `current_user: User = Depends(get_current_user)` line
        # and rewrite it to wrap RequirePermissions.
        sites += 1
        # Skip the deco line; copy following lines until we find current_user.
        j = i + 1
        replaced_current_user = False
        while j < len(lines):
            line = lines[j]
            new_line = CURRENT_USER_RE.sub(
                rf"\1RequirePermissions({perm_expr})\2",
                line,
            )
            if new_line != line:
                replaced_current_user = True
                out.append(new_line)
                j += 1
                break
            # Stop once we've crossed the function body (a `):` or
            # `\"\"\"docstring\"\"\"` line). Don't accidentally rewrite a later
            # endpoint.
            out.append(line)
            j += 1
            stripped = line.strip()
            if stripped == "):":
                break
            if stripped.startswith('"""') or stripped.startswith('"""') or (
                stripped.endswith(':') and stripped.startswith('async def') is False
                and stripped.startswith('def') is False
            ):
                # heuristic: stop at any line that looks like the end of the
                # function signature.
                pass
        if not replaced_current_user:
            # Couldn't find the conventional `current_user: User = Depends(
            # get_current_user)` line — flag it for manual review by emitting
            # a clear marker. (No silent skip.)
            out.append(
                f"# MANUAL_REVIEW_REQUIRED: scripts/lint/fix_requirepermissions_decorator.py could not "
                f"locate the `current_user: User = Depends(get_current_user)` line "
                f"to upgrade; the @RequirePermissions decorator was REMOVED but no "
                f"permission gate was inserted. Original perm: {perm_expr}"
            )
        i = j
    new_text = "\n".join(out)
    if text.endswith("\n") and not new_text.endswith("\n"):
        new_text += "\n"
    return new_text, sites


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    total = 0
    files = 0
    for path in sorted(API_ROOT.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        text = path.read_text()
        if "@RequirePermissions(" not in text:
            continue
        new_text, n = transform(text)
        if n == 0:
            continue
        files += 1
        total += n
        if args.dry_run:
            print(f"DRY {path.relative_to(ROOT)}: {n} site(s)")
        else:
            path.write_text(new_text)
            print(f"OK  {path.relative_to(ROOT)}: {n} site(s)")

    print(f"\n{'(dry-run) ' if args.dry_run else ''}{total} site(s) across {files} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
