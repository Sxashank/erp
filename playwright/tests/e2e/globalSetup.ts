/**
 * Pre-flight for the real-user E2E suite.
 *
 * Verifies the dedicated `smfc_erp_e2e` database has been seeded (the
 * `SMFC-E2E` organization row exists). Fails loud before any spec runs so the
 * suite never thrashes against a half-bootstrapped DB.
 *
 * Bootstrap is **not** done here automatically — that's a one-time operator
 * step: `bash backend/scripts/seed_e2e.sh`. Running it here would slow every
 * CI run by ~60 s; instead we point the operator at the README on failure.
 */

import { Client } from 'pg';

import { E2E_DATABASE_URL, readE2EOrgId } from '../../fixtures/db';

export default async function globalSetup(): Promise<void> {
  let orgId: string;
  try {
    orgId = readE2EOrgId();
  } catch (err) {
    throw new Error(
      'E2E suite cannot start: the org-id file is missing. Run:\n' +
        '  bash backend/scripts/seed_e2e.sh\n' +
        'See playwright/tests/e2e/README.md.',
    );
  }

  const client = new Client({ connectionString: E2E_DATABASE_URL });
  await client.connect();
  try {
    const res = await client.query(
      "SELECT 1 FROM mst_organization WHERE id = $1 AND code = 'SMFC-E2E'",
      [orgId],
    );
    if (res.rowCount === 0) {
      throw new Error(
        `E2E org ${orgId} (code=SMFC-E2E) not found in ${E2E_DATABASE_URL}. ` +
          'Re-run `bash backend/scripts/seed_e2e.sh`.',
      );
    }
    const userRes = await client.query(
      "SELECT 1 FROM mst_user WHERE username = $1",
      [process.env.UAT_ADMIN_USERNAME ?? 'krishna'],
    );
    if (userRes.rowCount === 0) {
      throw new Error('E2E admin user not seeded. Re-run seed_e2e.sh.');
    }
  } finally {
    await client.end();
  }

  // eslint-disable-next-line no-console
  console.log(`[e2e:globalSetup] E2E org ${orgId} ready, admin user seeded.`);
}
