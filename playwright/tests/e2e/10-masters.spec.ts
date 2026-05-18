/**
 * E2E — masters CRUD (Tier 1 in the test plan).
 *
 * Walks the canonical real-user loop for the cheapest, dependency-free
 * master: Unit. The same shape (create → list-row visible → DB row exists →
 * edit → DB updated → reload → values still shown) is templated for the
 * other Tier-1 entities; this file proves the harness end-to-end.
 *
 *   UI → API → DB → page reload
 */

import { expect, test } from '../../fixtures/test';
import { loginAsAdmin } from '../../fixtures/auth';
import {
  fillField,
  fillForm,
  submitForm,
  expectSuccessToast,
} from '../../fixtures/form';
import { uniqueCode } from '../../fixtures/unique';

test.describe('Masters › Unit', () => {
  test('create → list shows row → DB row exists → edit → DB updated → reload', async ({
    page,
    consoleGate,
    db,
  }) => {
    consoleGate.allowStatus(404, '/api/v1');
    const code = uniqueCode('E2E-UNIT');
    const name = `E2E Unit ${code}`;

    // ---------------------------------------------------------------- CREATE
    await loginAsAdmin(page);
    await page.goto('/admin/units/new');

    await fillForm(page, {
      'Unit Code': code,
      'Unit Name': name,
    });
    // Pick the seeded E2E org from the combobox.
    await fillField(page, 'Organization', 'SMFC E2E Sandbox');
    await fillField(page, 'Unit Type', 'Branch Office');

    await submitForm(page);
    await expectSuccessToast(page, /(unit (created|saved)|created successfully)/i);

    // Redirected back to /admin/units after save.
    await page.waitForURL(/\/admin\/units(\/|$|\?)/, { timeout: 8_000 });

    // -------------------------------------------------------------- LIST UI
    await expect(page.getByRole('cell', { name: code })).toBeVisible();
    await expect(page.getByRole('cell', { name })).toBeVisible();

    // ---------------------------------------------------------- DB ASSERTION
    const row = await db.assertRowExists<{ id: string; name: string; code: string; unit_type: string }>(
      'mst_unit',
      { code },
      { name, unit_type: 'BRANCH_OFFICE' },
    );

    // ------------------------------------------------------------------ EDIT
    // Open the row's actions menu and click Edit.
    const rowEl = page.getByRole('row').filter({ hasText: code }).first();
    await expect(rowEl).toBeVisible();
    await rowEl.getByRole('button').last().click();
    await page.getByRole('menuitem', { name: /^edit$/i }).first().click();

    await page.waitForURL(/\/admin\/units\/[\w-]+\/edit/, { timeout: 8_000 });

    // Existing value pre-populated.
    await expect(page.getByLabel(/^Unit Name/i)).toHaveValue(name);

    const newName = `${name} (renamed)`;
    await fillField(page, 'Unit Name', newName);
    await submitForm(page);
    await expectSuccessToast(page, /(unit (updated|saved)|updated successfully)/i);

    // DB row updated.
    await db.assertRowMatches('mst_unit', { id: row.id }, { name: newName });

    // ---------------------------------------------------- RELOAD CONFIRMS UI
    await page.goto(`/admin/units/${row.id}/edit`);
    await expect(page.getByLabel(/^Unit Name/i)).toHaveValue(newName);

    // Teardown: leave the row in the DB so a follow-up debugging session can
    // inspect it. `99-cleanup.spec.ts` removes everything by prefix.
  });

  test('validation: empty Code and Name block submit', async ({ page, consoleGate }) => {
    void consoleGate;
    await loginAsAdmin(page);
    await page.goto('/admin/units/new');

    await submitForm(page);
    await expect(page.getByText(/code is required/i)).toBeVisible();
    await expect(page.getByText(/name is required/i)).toBeVisible();
    // Still on /new — no navigation occurred.
    await expect(page).toHaveURL(/\/admin\/units\/new/);

    // Fill Code; the Code error clears as soon as the field becomes valid.
    await page.getByLabel(/^Unit Code/i).fill('E2E-VALIDATE');
    await expect(page.getByText(/code is required/i)).toBeHidden();
  });
});
