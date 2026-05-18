/**
 * Unique-data helper for E2E specs.
 *
 * Every test run produces collision-free codes so reruns of the suite never
 * trip the unique constraints on `(organization_id, code)` etc. Codes are
 * short enough to fit varchar(30/50) columns and descriptive enough to be
 * grep-able in DB rows ("which run created this row?").
 *
 * Shape: `<PREFIX>-<timestamp36>-<6hex>` — 16-20 chars total.
 *   E2E-UNIT-lwz8wq-3f2a91
 *
 * The prefix is the caller's responsibility (typically the entity short name
 * — `UNIT`, `DEPT`, `VND`, `CUST`).
 */

import { randomBytes } from 'node:crypto';

export function uniqueCode(prefix: string): string {
  const ts = Date.now().toString(36);
  const rand = randomBytes(3).toString('hex');
  return `${prefix}-${ts}-${rand}`;
}

/** Stable per-run suffix, useful for free-text fields like names. */
export function runSuffix(): string {
  return `${Date.now().toString(36)}-${randomBytes(2).toString('hex')}`;
}
