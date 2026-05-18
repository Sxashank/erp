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
    // Allowlist of `(table, code-column)` pairs the suite writes to. Add new
    // entries here when new specs create new entities. The DELETE is RLS-
    // scoped by organization_id (see `dbConnect`), so dev rows are not at risk.
    const targets: Array<[string, string]> = [
      ['mst_unit', 'code'],
      ['mst_department', 'code'],
      ['mst_designation', 'code'],
      // Tier-2 / tier-3 entries added as their specs land.
    ];

    let totalDeleted = 0;
    for (const [table, column] of targets) {
      const n = await db.cleanupByPrefix(table, 'E2E-', column);
      totalDeleted += n;
    }
    // We don't fail the test if zero rows were deleted — a fresh DB has none
    // by definition. The assertion is just "the query plan ran".
    expect(totalDeleted).toBeGreaterThanOrEqual(0);
  });
});
