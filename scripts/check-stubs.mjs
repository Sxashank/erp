#!/usr/bin/env node
/**
 * Stub lint. Enforces AGENTS.md §12.2 / §12 rule 3.
 *
 * Scans code/config files for TODO / FIXME / XXX / HACK / "not implemented"
 * markers and cross-checks each one against `.stubs-approved.md`.
 *
 * Exits non-zero if:
 *  - an unapproved marker exists, or
 *  - an approved entry has passed its expiry date.
 *
 * Usage: node scripts/check-stubs.mjs
 */

import { execSync } from 'node:child_process';
import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const REPO = process.cwd();
const APPROVED_FILE = join(REPO, '.stubs-approved.md');

/** Markers that indicate a stub. */
const COMMENT_MARKER_RE = /\b(TODO|FIXME|HACK)\b/i;
const NOT_IMPLEMENTED_RE = /\bnot implemented\b/i;
const XXX_COMMENT_RE = /(?:^|\s)(?:#|\/\/|\/\*|\*)\s*XXX\b/;

/** Paths we never scan. */
const IGNORE_DIRS = new Set([
  'node_modules',
  'dist',
  'build',
  'coverage',
  'playwright-report',
  'test-results',
  '.git',
  '.venv',
  '__pycache__',
  '.pytest_cache',
  '.mypy_cache',
  '.ruff_cache',
  'refdocs',
]);

/** Files we never scan. */
const IGNORE_FILES = new Set([
  'CLAUDE.md',
  'AGENTS.md',
  'CLAUDE_REVIEW_PROMPT.md',
  '.stubs-approved.md',
  'pnpm-lock.yaml',
  'package-lock.json',
  'check-stubs.mjs',
]);

/** Extensions we scan. */
const SCAN_EXT = new Set([
  '.ts',
  '.tsx',
  '.js',
  '.cjs',
  '.mjs',
  '.py',
  '.sh',
  '.yml',
  '.yaml',
  '.json',
  '.html',
  '.css',
  '.toml',
]);

function listTrackedFiles() {
  try {
    const out = execSync('git ls-files', { encoding: 'utf8', cwd: REPO });
    return out.split('\n').filter(Boolean);
  } catch {
    // Not a git repo (first-time bootstrap). Fall back to a find-based walk.
    const out = execSync(
      "find . -type f -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.venv/*'",
      { encoding: 'utf8', cwd: REPO },
    );
    return out
      .split('\n')
      .filter(Boolean)
      .map((p) => p.replace(/^\.\//, ''));
  }
}

function parseApproved(content) {
  /** Set of normalized approved entry keys. */
  const exact = new Set();
  const pathCounts = new Map();
  const globs = [];
  const expiries = new Map(); // key -> expiry date
  const rowRe =
    /^\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*[^|]+\|\s*[^|]+\|\s*(\d{4}-\d{2}-\d{2})\s*\|/gm;
  let m;
  while ((m = rowRe.exec(content))) {
    const raw = m[1].trim();
    const expiry = m[4];
    if (raw.includes('*') || raw.includes('?')) {
      globs.push({ raw, expiry });
    } else {
      exact.add(raw);
      expiries.set(raw, expiry);
      const path = raw.replace(/:\d+$/, '');
      pathCounts.set(path, (pathCounts.get(path) ?? 0) + 1);
    }
  }

  let tableHasExpiry = false;
  for (const line of content.split('\n')) {
    if (!line.startsWith('|')) {
      tableHasExpiry = false;
      continue;
    }
    if (/\|\s*Expiry\s*\|/.test(line)) {
      tableHasExpiry = true;
      continue;
    }
    if (line.startsWith('|---')) continue;
    if (!tableHasExpiry) continue;

    if (!line.startsWith('|') || line.startsWith('|---')) continue;
    const cells = line
      .split('|')
      .slice(1, -1)
      .map((cell) => cell.trim());
    if (cells.length < 5) continue;

    const expiry = cells.find((cell) => /^\d{4}-\d{2}-\d{2}$/.test(cell));
    if (!expiry) continue;

    for (const cell of cells) {
      const codeSpans = [...cell.matchAll(/`([^`]+)`/g)].map((match) => match[1].trim());
      for (const raw of codeSpans) {
        if (!looksLikeRepoPath(raw)) continue;
        if (raw.includes('*') || raw.includes('?')) {
          if (!globs.some((g) => g.raw === raw)) {
            globs.push({ raw, expiry });
          }
        } else {
          exact.add(raw);
          expiries.set(raw, expiry);
          const path = raw.replace(/:\d+$/, '');
          pathCounts.set(path, (pathCounts.get(path) ?? 0) + 1);
        }
      }
    }
  }

  return { exact, pathCounts, globs, expiries };
}

function looksLikeRepoPath(value) {
  return (
    value.includes('/') &&
    !value.includes(' ') &&
    !value.startsWith('http://') &&
    !value.startsWith('https://')
  );
}

function globToRegex(g) {
  const escaped = g
    .replace(/[.+^${}()|[\]\\]/g, '\\$&')
    .replace(/\*\*/g, '§§DOUBLE§§')
    .replace(/\*/g, '[^/]*')
    .replace(/§§DOUBLE§§/g, '.*')
    .replace(/\?/g, '[^/]');
  return new RegExp('^' + escaped + '$');
}

function hasStubMarker(line) {
  if (COMMENT_MARKER_RE.test(line)) return true;
  if (NOT_IMPLEMENTED_RE.test(line)) return true;
  return XXX_COMMENT_RE.test(line);
}

function matchApproved(key, approved, usedPathCounts) {
  if (approved.exact.has(key)) {
    return { matched: true, expiry: approved.expiries.get(key) };
  }
  // Approved entries can be "path:line" or "path" (whole file).
  const [path] = key.split(':');
  if (approved.exact.has(path)) {
    return { matched: true, expiry: approved.expiries.get(path) };
  }
  const allowedForPath = approved.pathCounts.get(path) ?? 0;
  const usedForPath = usedPathCounts.get(path) ?? 0;
  if (usedForPath < allowedForPath) {
    usedPathCounts.set(path, usedForPath + 1);
    return { matched: true, expiry: undefined };
  }
  for (const g of approved.globs) {
    if (globToRegex(g.raw).test(path)) {
      return { matched: true, expiry: g.expiry };
    }
  }
  return { matched: false };
}

function main() {
  if (!existsSync(APPROVED_FILE)) {
    console.error(
      'FAIL: .stubs-approved.md not found. Every repo that uses this script must maintain one.',
    );
    process.exit(2);
  }

  const approved = parseApproved(readFileSync(APPROVED_FILE, 'utf8'));
  const today = new Date().toISOString().slice(0, 10);

  // 1) Expired-approved check.
  const expired = [];
  for (const [key, expiry] of approved.expiries.entries()) {
    if (expiry < today) expired.push({ key, expiry });
  }

  // 2) Unapproved-marker check.
  const files = listTrackedFiles();
  const unapproved = [];
  const usedPathCounts = new Map();
  for (const rel of files) {
    const parts = rel.split('/');
    if (parts.some((p) => IGNORE_DIRS.has(p))) continue;
    if (IGNORE_FILES.has(parts[parts.length - 1])) continue;
    const dot = rel.lastIndexOf('.');
    const ext = dot >= 0 ? rel.slice(dot) : '';
    if (!SCAN_EXT.has(ext)) continue;

    let content;
    try {
      content = readFileSync(join(REPO, rel), 'utf8');
    } catch {
      continue;
    }

    const lines = content.split('\n');
    lines.forEach((line, i) => {
      if (!hasStubMarker(line)) return;
      // Skip obvious false positives: the lint script itself.
      if (rel === 'scripts/check-stubs.mjs') return;

      const key = `${rel}:${i + 1}`;
      const { matched } = matchApproved(key, approved, usedPathCounts);
      if (!matched) {
        unapproved.push({ file: rel, line: i + 1, text: line.trim().slice(0, 140) });
      }
    });
  }

  let failed = false;

  if (unapproved.length > 0) {
    failed = true;
    console.error(
      `\n✖ ${unapproved.length} unapproved stub marker(s) found. Every TODO/FIXME/XXX/HACK must be recorded in .stubs-approved.md (see AGENTS.md §12.2).\n`,
    );
    for (const u of unapproved) {
      console.error(`  ${u.file}:${u.line}  ${u.text}`);
    }
  }

  if (expired.length > 0) {
    failed = true;
    console.error(
      `\n✖ ${expired.length} approved stub(s) have passed their expiry date. Promote them to P1 defects or re-approve with a new date.\n`,
    );
    for (const e of expired) {
      console.error(`  ${e.key}  expired ${e.expiry}`);
    }
  }

  if (failed) {
    console.error('\nSee AGENTS.md §12 and .stubs-approved.md.');
    process.exit(1);
  }

  console.log(
    `✓ stub-lint clean — ${approved.exact.size} approved marker(s), ${approved.globs.length} glob(s). 0 unapproved.`,
  );
}

main();
