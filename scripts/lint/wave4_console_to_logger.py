#!/usr/bin/env python3
"""Wave 4 codemod: `console.log/info/warn/error/debug` → `logger.<level>`.

CLAUDE.md §5.12: frontend code must use `src/lib/logger.ts`, not raw
console. ESLint `no-console` was flipped to `error` in Wave 0 so this
codemod brings the tree into compliance before the rule actually starts
blocking CI.

Mapping
-------
  console.log   → logger.debug
  console.debug → logger.debug
  console.info  → logger.info
  console.warn  → logger.warn
  console.error → logger.error

Rules
-----
- Only `*.ts`/`*.tsx` under `src/` (NOT tests, NOT `src/lib/logger.ts`).
- If the file isn't already importing `logger`, add
  `import { logger } from "@/lib/logger";` near the other imports.
- Lines that are commented out are skipped.
- Lines that already use `logger.` are skipped.

Use `--dry-run` to preview.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"

CONSOLE_MAP = {
    "log": "debug",
    "debug": "debug",
    "info": "info",
    "warn": "warn",
    "error": "error",
}

CALL_RE = re.compile(r"\bconsole\.(log|debug|info|warn|error)\b")
IMPORT_LOGGER_RE = re.compile(r"""\bimport\s+\{[^}]*\blogger\b[^}]*\}\s+from\s+["']@/lib/logger["']""")
LAST_IMPORT_RE = re.compile(r"^(import .+from\s+['\"][^'\"]+['\"];?\s*)$", re.MULTILINE)

SKIP_NAMES = {"logger.ts"}
SKIP_DIR_PARTS = {"__tests__", "test", "tests"}


def _should_skip(path: Path) -> bool:
    if path.name in SKIP_NAMES:
        return True
    if any(p in SKIP_DIR_PARTS for p in path.parts):
        return True
    name = path.name
    if name.endswith(".test.ts") or name.endswith(".test.tsx"):
        return True
    if name.endswith(".spec.ts") or name.endswith(".spec.tsx"):
        return True
    return False


def transform(text: str) -> tuple[str, int]:
    """Return (new_text, replacement_count)."""
    lines = text.split("\n")
    out: list[str] = []
    count = 0
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("*"):
            out.append(line)
            continue

        def repl(m: re.Match[str]) -> str:
            nonlocal count
            count += 1
            return f"logger.{CONSOLE_MAP[m.group(1)]}"

        new_line = CALL_RE.sub(repl, line)
        out.append(new_line)

    new_text = "\n".join(out)
    if text.endswith("\n") and not new_text.endswith("\n"):
        new_text += "\n"

    if count > 0 and not IMPORT_LOGGER_RE.search(new_text):
        new_text = _inject_logger_import(new_text)

    return new_text, count


def _inject_logger_import(text: str) -> str:
    """Insert `import { logger } from "@/lib/logger";` after the last import."""
    matches = list(LAST_IMPORT_RE.finditer(text))
    if not matches:
        return 'import { logger } from "@/lib/logger";\n' + text
    last = matches[-1]
    insert_at = last.end()
    return text[:insert_at] + '\nimport { logger } from "@/lib/logger";' + text[insert_at:]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    total = 0
    files = 0
    for path in sorted(list(SRC.rglob("*.ts")) + list(SRC.rglob("*.tsx"))):
        if _should_skip(path):
            continue
        text = path.read_text()
        if "console." not in text:
            continue
        new_text, n = transform(text)
        if n == 0:
            continue
        files += 1
        total += n
        if args.dry_run:
            print(f"DRY {path.relative_to(ROOT)}: {n} replacement(s)")
        else:
            path.write_text(new_text)
            print(f"OK  {path.relative_to(ROOT)}: {n} replacement(s)")

    print(f"\n{'(dry-run) ' if args.dry_run else ''}{total} replacement(s) across {files} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
