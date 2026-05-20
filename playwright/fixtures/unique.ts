/**
 * Unique-data helper for E2E specs.
 *
 * Every test run produces collision-free codes so reruns of the suite never
 * trip the unique constraints on `(organization_id, code)` etc.
 *
 * **Size budget**: master `code` columns cap at 20 chars in the strictest
 * schemas (see `UnitBase.code: max_length=20`). The default shape fits well
 * under that:
 *   `<PREFIX>` (≤ 8) + `<ts:6>` + `<hex:4>` = ≤ 18 chars.
 *
 *   uniqueCode('UNIT') → 'UNITxxxxxxYYYY' (14 chars)
 *
 * Every E2E-created row starts with the caller-supplied entity prefix so
 * the cleanup pass (`99-cleanup.spec.ts`) can find them with a simple
 * `LIKE 'UNIT%'` predicate, scoped to the E2E org.
 */

import { randomBytes } from 'node:crypto';

const E2E_TAG = 'E2E';

function shortTs(): string {
  // Last 6 chars of base36 timestamp (millisecond resolution; rolls over
  // every ~7 weeks — well past the suite's "reruns within an hour" needs).
  return Date.now().toString(36).slice(-6).toUpperCase();
}

export function uniqueCode(prefix: string): string {
  if (prefix.length > 8) {
    throw new Error(`uniqueCode prefix ${JSON.stringify(prefix)} is too long (max 8 chars)`);
  }
  const rand = randomBytes(2).toString('hex').toUpperCase(); // 4 chars
  return `${prefix}${shortTs()}${rand}`;
}

/** Stable per-run suffix, useful for free-text fields (no length pressure). */
export function runSuffix(): string {
  return `${shortTs()}-${randomBytes(2).toString('hex').toUpperCase()}`;
}

/** Common test prefix any spec can apply when it doesn't want a per-entity tag. */
export const E2E_PREFIX = E2E_TAG;
