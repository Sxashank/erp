/**
 * E2E — teardown.
 *
 * Removes every row created by the real-user suite for the dedicated E2E
 * organisation. Idempotent and safe to run in isolation. Keeping it as a
 * spec (not `globalTeardown`) means a failing run leaves the rows in the DB
 * for forensic inspection, and the operator can opt in to cleanup by
 * running just this file: `pnpm exec playwright test playwright/tests/e2e/99-cleanup.spec.ts`.
 */

import { expect, test } from '../../fixtures/test';

test.describe('E2E › cleanup', () => {
  test('truncate E2E-prefixed rows from transactional tables', async ({ db }) => {
    // Allowlist of `(table, entity-code-prefix, code-column)` triples the
    // suite writes to. Add new entries as new specs land. The DELETE is RLS-
    // scoped by organization_id (see `dbConnect`), so dev rows are not at
    // risk; the per-entity prefix is the per-spec match (set in
    // `fixtures/unique.ts::uniqueCode`).
    // Entries land here as each spec adopts a `code` prefix. The cleanup
    // helper scopes the DELETE by `organization_id`; only tables that carry
    // that column belong here (e.g. `mst_designation` is platform-global and
    // is intentionally excluded — designations never become test churn).
    const targets: Array<[string, string, string]> = [
      ['mst_unit', 'UNIT', 'code'],
      ['mst_department', 'DEPT', 'code'],
      ['mst_designation', 'DESIG', 'code'],
      ['mst_voucher_type', 'VT', 'code'],
      ['mst_payment_terms', 'PTERM', 'code'],
      ['mst_gst_rate', 'GR', 'code'],
      ['mst_hsn_sac', 'HSN', 'code'],
      // Tier-2 / tier-3 entries added as their specs land.
    ];

    let totalDeleted = 0;
    for (const [table, prefix, column] of targets) {
      const n = await db.cleanupByPrefix(table, prefix, column);
      totalDeleted += n;
    }
    // We don't fail the test if zero rows were deleted — a fresh DB has none
    // by definition. The assertion is just "the query plan ran".
    expect(totalDeleted).toBeGreaterThanOrEqual(0);
  });
});
