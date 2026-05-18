#!/usr/bin/env python3
"""Wave 3 codemod: add `response_model_by_alias=True` to every route
returning a `CamelSchema`-derived response.

Without the flag, FastAPI ignores the `alias_generator=to_camel` config
and emits snake_case on the wire — silently breaking the camelCase wire
contract (CLAUDE.md §6 / Appendix C).

Approach (pragmatic, low-risk):
  - Walk every `backend/app/api/v1/**/*.py`.
  - For each `@router.<verb>(...)` decorator whose argument list contains
    `response_model=` but NOT `response_model_by_alias=`, insert
    `response_model_by_alias=True` right after `response_model=...`.
  - We DO NOT try to verify that the response model is actually a
    CamelSchema — adding the flag to a non-CamelSchema response is a no-op
    (FastAPI uses by-name serialisation when no alias generator is set).

Run with `--dry-run` to preview.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "backend" / "app" / "api" / "v1"


def transform(text: str) -> tuple[str, int]:
    """Return (new_text, replacements).

    Strategy: split into decorator blocks, modify per-block.

    A decorator block here is a contiguous sequence of lines whose first
    line matches ``@router.<verb>(`` and which continues until the
    matching ``)`` at brace-depth 0.
    """
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)
    replacements = 0
    deco_re = re.compile(r"^\s*@router\.\w+\(")
    while i < n:
        line = lines[i]
        if not deco_re.match(line):
            out.append(line)
            i += 1
            continue
        # Found the start of a router decorator. Walk forward, tracking paren depth.
        start = i
        depth = 0
        end = start
        while end < n:
            depth += lines[end].count("(") - lines[end].count(")")
            if depth <= 0:
                break
            end += 1
        # Block is lines[start..end] inclusive.
        block_lines = lines[start : end + 1]
        block = "\n".join(block_lines)
        # Does the block already have response_model_by_alias? Skip.
        if "response_model_by_alias" in block:
            out.extend(block_lines)
            i = end + 1
            continue
        # Does the block have response_model=? If not, skip.
        if "response_model=" not in block:
            out.extend(block_lines)
            i = end + 1
            continue
        # Insert `response_model_by_alias=True,` right after the
        # `response_model=...` argument.
        # Find the line containing `response_model=`.
        for j, bl in enumerate(block_lines):
            m = re.search(r"response_model\s*=\s*([^,)\n]+)", bl)
            if not m:
                continue
            # Determine indent from this line.
            indent_m = re.match(r"^(\s*)", bl)
            indent = indent_m.group(1) if indent_m else "    "
            # Strip trailing whitespace + trailing comma to splice cleanly.
            tail_after = bl[m.end() :]
            head = bl[: m.end()]
            # If the line ends here (no comma yet), add one.
            if tail_after.strip() == "":
                head_with_comma = head.rstrip() + ","
                new_block_lines = (
                    block_lines[: j + 1]
                    + [indent + "response_model_by_alias=True,"]
                    + block_lines[j + 1 :]
                )
                # Replace original line with head_with_comma + tail_after's rest (newline).
                new_block_lines[j] = head_with_comma
            else:
                # The argument continues on the same line — e.g.
                # `response_model=SomeType, status_code=...`
                # Split at the comma after the type.
                comma_idx = tail_after.find(",")
                if comma_idx >= 0:
                    new_line = head + tail_after[: comma_idx + 1] + " response_model_by_alias=True," + tail_after[comma_idx + 1 :]
                    new_block_lines = list(block_lines)
                    new_block_lines[j] = new_line
                else:
                    # The argument ends with `)` on the same line — unusual.
                    new_line = head + tail_after.rstrip()
                    # Insert before the closing paren.
                    if new_line.endswith(")"):
                        new_line = new_line[:-1].rstrip().rstrip(",") + ", response_model_by_alias=True)"
                    new_block_lines = list(block_lines)
                    new_block_lines[j] = new_line
            out.extend(new_block_lines)
            replacements += 1
            break
        else:
            out.extend(block_lines)
        i = end + 1
    new_text = "\n".join(out)
    if text.endswith("\n") and not new_text.endswith("\n"):
        new_text += "\n"
    return new_text, replacements


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    total = 0
    files_touched = 0
    for path in sorted(API_ROOT.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        text = path.read_text()
        new_text, count = transform(text)
        if count == 0:
            continue
        files_touched += 1
        total += count
        if args.dry_run:
            print(f"DRY {path.relative_to(ROOT)}: {count} insertion(s)")
        else:
            path.write_text(new_text)
            print(f"OK  {path.relative_to(ROOT)}: {count} insertion(s)")
    print(
        f"\n{'(dry-run) ' if args.dry_run else ''}"
        f"{total} insertion(s) across {files_touched} file(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
