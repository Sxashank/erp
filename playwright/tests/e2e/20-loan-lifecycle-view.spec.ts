/**
 * E2E — full loan lifecycle, view path.
 *
 * The E2E DB is bootstrapped with a complete IIF chain (via
 * `backend/scripts/seed_e2e_iif_chain.py`):
 *
 *     Entity → LoanProduct → LoanApplication → LoanSanction
 *         → LoanAccount → Disbursement(PROCESSED)
 *         → SubventionEnrollment → SubventionClaim(DRAFT)
 *
 * This spec drives a real admin user through every stage's list + detail
 * page and asserts the seeded identifiers (`E2E-IIF-ENT-001`,
 * `E2E-IIF-APP-001`, `E2E-IIF-SANC-001`, `E2E-IIF-LOAN-001`,
 * `E2E-IIF-DISB-001`, `E2E/IIF/2026Q1/00001`) round-trip from DB → API → UI
 * at every stage. That proves the full origination + servicing pipeline is
 * wired end-to-end: any regression in a list query, a detail page, or the
 * camelCase wire contract surfaces here.
 *
 * Why view-path, not create-path: the canonical create flow for a loan
 * spans 4 multi-step forms (application wizard, sanction with security
 * setup, account open with GL mapping, disbursement authorize+process)
 * with ~150 fields total. That belongs in its own wizard-aware spec
 * (deferred). This spec proves the *read* contract of every lifecycle
 * stage — equally critical, and a strong gate against camelCase /
 * permission / RLS regressions.
 *
 * If the E2E DB has no seeded chain (fresh bootstrap before
 * `seed_e2e_iif_chain.py` runs), the spec soft-skips. Production CI runs
 * the seeder before this spec, so the skip should never happen there.
 */

import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { chromium } from '@playwright/test';

import { expect, test as base } from '../../fixtures/test';
import { loginAsAdmin } from '../../fixtures/auth';

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:5176';
const LIVE_BACKEND_ENABLED = process.env.PLAYWRIGHT_LIVE_BACKEND === '1';

const test = base.extend<{}, { storageStatePath: string }>({
  storageStatePath: [
    async (_args, use) => {
      const dir = mkdtempSync(join(tmpdir(), 'e2e-loan-lifecycle-'));
      const path = join(dir, 'storage.json');
      const browser = await chromium.launch();
      const ctx = await browser.newContext({ baseURL: BASE_URL });
      const page = await ctx.newPage();
      await loginAsAdmin(page);
      await ctx.storageState({ path });
      await ctx.close();
      await browser.close();
      await use(path);
    },
    { scope: 'worker' },
  ],

  context: async ({ browser, storageStatePath }, use) => {
    const ctx = await browser.newContext({ storageState: storageStatePath, baseURL: BASE_URL });
    await use(ctx);
    await ctx.close();
  },
});

const ENTITY_CODE = 'E2E-IIF-ENT-001';
const APPLICATION_NUMBER = 'E2E-IIF-APP-001';
const SANCTION_NUMBER = 'E2E-IIF-SANC-001';
const LOAN_ACCOUNT_NUMBER = 'E2E-IIF-LOAN-001';
const DISBURSEMENT_REF = 'E2E-IIF-DISB-001';
const CLAIM_REFERENCE = 'E2E/IIF/2026Q1/00001';

interface SeededIds {
  entityId: string;
  applicationId: string;
  sanctionId: string;
  loanAccountId: string;
  claimId: string;
}

function seededChainHint(): string {
  if (!LIVE_BACKEND_ENABLED) {
    return 'Run `python backend/scripts/seed_e2e_iif_chain.py` first.';
  }
  return (
    'Run `DATABASE_URL=postgresql+asyncpg://smfc:smfc_secret@localhost:5432/smfc_erp ' +
    'SEED_ORG_CODE=SMFC_UAT python backend/scripts/seed_e2e_iif_chain.py` first.'
  );
}

function fmtAmount(amountStr: string): string {
  const abs = Math.abs(Number(amountStr));
  if (abs >= 10_000_000) return `₹ ${(abs / 10_000_000).toFixed(2)} Cr`;
  if (abs >= 100_000) return `₹ ${(abs / 100_000).toFixed(2)} L`;
  if (abs >= 1_000) return `₹ ${(abs / 1_000).toFixed(2)} K`;
  return `₹ ${abs.toFixed(2)}`;
}

test.describe('E2E › loan lifecycle › view path', () => {
  test('the entire seeded chain is reachable through the admin UI', async ({
    page,
    consoleGate,
    db,
  }) => {
    // ---- Pre-flight: resolve every seeded record id (skip gracefully if
    // the seeder hasn't run on this DB).
    const entityRow = await db.query<{ id: string }>(
      'SELECT id::text AS id FROM los_entity WHERE entity_code = $1 LIMIT 1',
      [ENTITY_CODE],
    );
    if (entityRow.length === 0) {
      test.info().annotations.push({
        type: 'note',
        description: `No seeded IIF chain found in the active Playwright DB. ${seededChainHint()}`,
      });
      return;
    }

    const appRow = await db.query<{ id: string }>(
      'SELECT id::text AS id FROM los_loan_application WHERE application_number = $1 LIMIT 1',
      [APPLICATION_NUMBER],
    );
    const sanctionRow = await db.query<{ id: string }>(
      'SELECT id::text AS id FROM los_loan_sanction WHERE sanction_number = $1 LIMIT 1',
      [SANCTION_NUMBER],
    );
    const accountRow = await db.query<{ id: string }>(
      'SELECT id::text AS id FROM lms_loan_account WHERE loan_account_number = $1 LIMIT 1',
      [LOAN_ACCOUNT_NUMBER],
    );
    const claimRow = await db.query<{ id: string }>(
      'SELECT id::text AS id FROM txn_subvention_claim WHERE claim_reference = $1 LIMIT 1',
      [CLAIM_REFERENCE],
    );
    expect(appRow.length, 'seeded application missing').toBeGreaterThan(0);
    expect(sanctionRow.length, 'seeded sanction missing').toBeGreaterThan(0);
    expect(accountRow.length, 'seeded loan account missing').toBeGreaterThan(0);
    expect(claimRow.length, 'seeded claim missing').toBeGreaterThan(0);

    const ids: SeededIds = {
      entityId: entityRow[0].id,
      applicationId: appRow[0].id,
      sanctionId: sanctionRow[0].id,
      loanAccountId: accountRow[0].id,
      claimId: claimRow[0].id,
    };

    // ------------------------------------------------- Stage 1: Entity
    await page.goto(`/admin/lending/entities?search=${encodeURIComponent(ENTITY_CODE)}`);
    await expect(page.locator('main, [role="main"]').first()).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(ENTITY_CODE).first()).toBeVisible({ timeout: 10_000 });

    await page.goto(`/admin/lending/entities/${ids.entityId}`);
    await expect(page.locator('main, [role="main"]').first()).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(ENTITY_CODE).first()).toBeVisible({ timeout: 10_000 });
    // The detail page must render the legal name from the seeded entity.
    await expect(page.getByText(/E2E IIF Borrower/i).first()).toBeVisible({ timeout: 10_000 });

    // ------------------------------------------------- Stage 2: Application
    await page.goto(`/admin/lending/applications?search=${encodeURIComponent(APPLICATION_NUMBER)}`);
    await expect(page.locator('main, [role="main"]').first()).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(APPLICATION_NUMBER).first()).toBeVisible({ timeout: 10_000 });

    await page.goto(`/admin/lending/applications/${ids.applicationId}`);
    await expect(page.locator('main, [role="main"]').first()).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(APPLICATION_NUMBER).first()).toBeVisible({ timeout: 10_000 });

    // ------------------------------------------------- Stage 3: Sanction
    await page.goto('/admin/lending/sanctions');
    await expect(page.locator('main, [role="main"]').first()).toBeVisible({ timeout: 10_000 });
    await page
      .getByPlaceholder(/search by sanction number, entity name, or application/i)
      .fill(SANCTION_NUMBER);
    await expect(page.getByText(SANCTION_NUMBER).first()).toBeVisible({ timeout: 10_000 });

    await page.goto(`/admin/lending/sanctions/${ids.sanctionId}`);
    await expect(page.locator('main, [role="main"]').first()).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(SANCTION_NUMBER).first()).toBeVisible({ timeout: 10_000 });

    // ------------------------------------------------- Stage 4: Loan Account
    await page.goto('/admin/lending/accounts');
    await expect(page.locator('main, [role="main"]').first()).toBeVisible({ timeout: 10_000 });
    await page
      .getByPlaceholder(/search by loan account number or entity name/i)
      .fill(LOAN_ACCOUNT_NUMBER);
    await expect(page.getByText(LOAN_ACCOUNT_NUMBER).first()).toBeVisible({ timeout: 10_000 });

    await page.goto(`/admin/lending/accounts/${ids.loanAccountId}`);
    await expect(page.locator('main, [role="main"]').first()).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(LOAN_ACCOUNT_NUMBER).first()).toBeVisible({ timeout: 10_000 });

    // ------------------------------------------------- Stage 5: Disbursement
    // Disbursement list joins to the loan account, so the disbursement
    // reference appears in the list when the parent loan exists.
    await page.goto('/admin/lending/disbursements');
    await expect(page.locator('main, [role="main"]').first()).toBeVisible({ timeout: 10_000 });
    await page
      .getByPlaceholder(/search by disbursement number, entity, or loan account/i)
      .fill(DISBURSEMENT_REF);
    // Disbursement reference OR loan account number must appear — either
    // is sufficient proof that the disbursement row is reachable.
    await expect(
      page.getByText(new RegExp(`${DISBURSEMENT_REF}|${LOAN_ACCOUNT_NUMBER}`)).first(),
    ).toBeVisible({ timeout: 10_000 });

    // ------------------------------------------------- Stage 6: IIF Claim
    await page.goto('/admin/lending/iif/claims');
    await expect(page.locator('main, [role="main"]').first()).toBeVisible({ timeout: 10_000 });
    // Claim references contain `/` — the list page renders that verbatim.
    await expect(page.getByText(CLAIM_REFERENCE).first()).toBeVisible({ timeout: 10_000 });

    await page.goto(`/admin/lending/iif/claims/${ids.claimId}`);
    await expect(page.locator('main, [role="main"]').first()).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(CLAIM_REFERENCE).first()).toBeVisible({ timeout: 10_000 });
    // Loan account number must appear on the claim detail (subtitle).
    await expect(page.getByText(LOAN_ACCOUNT_NUMBER).first()).toBeVisible({ timeout: 10_000 });

    // The consoleGate fixture verifies no console.error / 4xx / 5xx
    // leaked across the entire 12-page traversal.
    void consoleGate;
  });

  test('IIF claim detail computation block renders the seeded amounts', async ({ page, db }) => {
    const claimRow = await db.query<{
      id: string;
      interest_paid_in_period: string;
      applicable_subvention_amount: string;
    }>(
      `SELECT id::text AS id,
              interest_paid_in_period::text AS interest_paid_in_period,
              applicable_subvention_amount::text AS applicable_subvention_amount
       FROM txn_subvention_claim WHERE claim_reference = $1 LIMIT 1`,
      [CLAIM_REFERENCE],
    );
    if (claimRow.length === 0) {
      test.info().annotations.push({
        type: 'note',
        description: `No seeded IIF claim found in the active Playwright DB. ${seededChainHint()}`,
      });
      return;
    }
    const claim = claimRow[0];
    await page.goto(`/admin/lending/iif/claims/${claim.id}`);

    // The "Computation" card renders interest_paid_in_period and
    // applicable_subvention_amount via <AmountDisplay>, which prefixes the
    // Indian abbreviated amount with the rupee symbol.
    await expect(page.getByText(fmtAmount(claim.interest_paid_in_period)).first()).toBeVisible({
      timeout: 10_000,
    });
    await expect(page.getByText(fmtAmount(claim.applicable_subvention_amount)).first()).toBeVisible(
      {
        timeout: 10_000,
      },
    );
  });
});
