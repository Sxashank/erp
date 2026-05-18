#!/usr/bin/env python3
"""Wave 1 codemod: swap `Depends(get_db)` → `Depends(get_db_with_tenant)`.

Scope: every authenticated route under `backend/app/api/v1/**` except:
  - LOS namespace (entities / products / applications / sanctions).
  - `auth/auth.py` (login routes run before identity is known).
  - `health.py`.

What it does (per file):
  1. Detect occurrences of `Depends(get_db)` outside import statements + comments.
  2. Replace with `Depends(get_db_with_tenant)`.
  3. Ensure `get_db_with_tenant` is imported from `app.api.deps`. If the file
     uses the `get_db_with_tenant as get_db` alias trick, rewrite that import to
     a plain `from app.api.deps import get_db_with_tenant` (the body's
     `Depends(get_db)` was rewritten in step 2, so the alias is no longer needed).
  4. Leave the file's other imports + structure untouched.

Run with `--dry-run` to preview; without to apply.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "backend" / "app" / "api" / "v1"

SKIP_FILES = {
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

CALL_PATTERN = re.compile(r"\bDepends\(\s*get_db\s*\)")

# Aliased imports like `get_db_with_tenant as get_db` need to become a plain
# import of `get_db_with_tenant` once the file's body stops using the alias.
ALIAS_IMPORT_PATTERN = re.compile(
    r"from\s+app\.api\.deps\s+import\s+([^\n]+?)\bget_db_with_tenant\s+as\s+get_db([^\n]*)"
)

# Plain import containing `get_db` (not aliased) — we need to ensure it also
# imports `get_db_with_tenant`.
PLAIN_IMPORT_PATTERN = re.compile(
    r"^from\s+app\.(?:api\.deps|database)\s+import\s+(.+)$",
    re.MULTILINE,
)


def _is_skipped(rel: Path) -> bool:
    rel_str = str(rel.relative_to(API_ROOT))
    return rel_str in SKIP_FILES


def _is_imported(text: str, symbol: str) -> bool:
    """Return True if `symbol` is in the import block of this file.

    We only inspect lines starting with `from ` or `import ` so that body-
    references (e.g. `Depends(get_db_with_tenant)` from a freshly-rewritten
    call site) don't fool us.
    """
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("from ") or stripped.startswith("import "):
            if re.search(rf"\b{re.escape(symbol)}\b", stripped):
                return True
    return False


def _ensure_import(text: str) -> str:
    """Make sure `get_db_with_tenant` is imported.

    Handles both single-line and multi-line (parenthesised) import blocks.
    """
    if _is_imported(text, "get_db_with_tenant"):
        return text

    lines = text.split("\n")

    # Pass 1: look for a `from app.api.deps import ...` block (single or multi line).
    for i, line in enumerate(lines):
        m = re.match(r"^(\s*from\s+app\.api\.deps\s+import\s+)(.*)$", line)
        if not m:
            continue
        rest = m.group(2)
        if rest.lstrip().startswith("("):
            # Multi-line. Find the closing `)`.
            for j in range(i, len(lines)):
                if ")" in lines[j]:
                    # Insert before the closing paren on its own line.
                    closing_line = lines[j]
                    close_idx = closing_line.index(")")
                    indent_match = re.match(r"^(\s*)", closing_line)
                    indent = indent_match.group(1) if indent_match else "    "
                    # If the line above already ends with a comma, just inject
                    # a new entry on its own line.
                    new_entry = f"{indent}get_db_with_tenant,"
                    # Decide insertion point: before the `)` whether it shares
                    # the line with content or is alone.
                    if closing_line[:close_idx].strip() == "":
                        # `)` is alone — insert as the previous line.
                        lines.insert(j, new_entry)
                    else:
                        # `)` on a line with content — split.
                        before = closing_line[:close_idx].rstrip()
                        if not before.endswith(","):
                            before = before + ","
                        after = closing_line[close_idx:]
                        lines[j] = before
                        lines.insert(j + 1, new_entry)
                        lines.insert(j + 2, indent[:-4] + after if len(indent) >= 4 else after)
                    return "\n".join(lines)
            # No closing paren found — fall through to append.
            break
        else:
            # Single-line `from app.api.deps import a, b, c`.
            current = rest.rstrip()
            if current.endswith(","):
                new_rest = current + " get_db_with_tenant"
            else:
                new_rest = current + ", get_db_with_tenant"
            lines[i] = m.group(1) + new_rest
            return "\n".join(lines)

    # No deps import found — splice a fresh import AFTER the import block,
    # i.e. on the first line that is not an import / not inside an import
    # parenthesis / not a comment / not blank. Track paren depth so we never
    # land inside a multi-line `from X import ( ... )`.
    paren_depth = 0
    insertion_idx = -1
    in_imports = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not in_imports:
            if stripped.startswith("from ") or stripped.startswith("import "):
                in_imports = True
                paren_depth += line.count("(") - line.count(")")
            continue
        # Already in the import block.
        if paren_depth > 0:
            paren_depth += line.count("(") - line.count(")")
            continue
        if stripped.startswith("from ") or stripped.startswith("import "):
            paren_depth += line.count("(") - line.count(")")
            continue
        if stripped == "" or stripped.startswith("#"):
            continue
        # First non-import line after the block.
        insertion_idx = i
        break
    if insertion_idx >= 0:
        lines.insert(insertion_idx, "from app.api.deps import get_db_with_tenant")
        if insertion_idx > 0 and lines[insertion_idx - 1].strip() != "":
            lines.insert(insertion_idx, "")
    else:
        # File is all imports; tack it onto the end.
        lines.append("from app.api.deps import get_db_with_tenant")
    return "\n".join(lines)


def _rewrite_alias(text: str) -> str:
    """Replace `get_db_with_tenant as get_db` import with the plain form."""

    def repl(m: re.Match[str]) -> str:
        before = m.group(1).rstrip()
        after = m.group(2).strip()
        # Normalize the import list: drop the alias, keep other symbols.
        rest = (before + " " + after).strip().strip(",").strip()
        rest = re.sub(r"\bget_db\b", "", rest).strip(",").strip()
        rest_cleaned = ", ".join(p.strip() for p in rest.split(",") if p.strip())
        if rest_cleaned:
            return f"from app.api.deps import {rest_cleaned}, get_db_with_tenant"
        return "from app.api.deps import get_db_with_tenant"

    return ALIAS_IMPORT_PATTERN.sub(repl, text)


def transform(text: str) -> tuple[str, int]:
    """Return (new_text, replacements)."""
    new_lines: list[str] = []
    count = 0
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped.startswith("from ") or stripped.startswith("import "):
            new_lines.append(line)
            continue
        new_line, n = CALL_PATTERN.subn("Depends(get_db_with_tenant)", line)
        new_lines.append(new_line)
        count += n
    new_text = "\n".join(new_lines)
    if not text.endswith("\n"):
        new_text = new_text  # preserve trailing-newline absence
    else:
        new_text = new_text + "\n"
    if count:
        new_text = _rewrite_alias(new_text)
        new_text = _ensure_import(new_text)
    return new_text, count


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    total_replacements = 0
    files_touched = 0
    for path in sorted(API_ROOT.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        if _is_skipped(path):
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
