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
    const code = uniqueCode('UNIT');
    const name = `E2E Unit ${code}`;

    // ---------------------------------------------------------------- CREATE
    await loginAsAdmin(page);
    await page.goto('/admin/units/new');

    // Wait for the form to render (the /organizations call resolves and the
    // RHF state hydrates) before driving fields.
    await expect(page.getByRole('textbox', { name: /Unit Code/i })).toBeVisible({
      timeout: 10_000,
    });

    await fillForm(page, {
      'Unit Code': code,
      'Unit Name': name,
    });
    // Pick the seeded E2E org from the combobox.
    await fillField(page, 'Organization', 'SMFC E2E Sandbox');
    await fillField(page, 'Unit Type', 'Branch');

    await submitForm(page);
    await expectSuccessToast(page, /(unit (created|saved)|created successfully)/i);

    // Redirected back to /admin/units after save.
    await page.waitForURL(/\/admin\/units(\/|$|\?)/, { timeout: 8_000 });

    // -------------------------------------------------------------- LIST UI
    // The code appears in both the Code column and (substring) inside the
    // Name column — match the row whose accessible name contains the code
    // and check that the Code cell within it exactly matches.
    const listRow = page.getByRole('row').filter({ hasText: code }).first();
    await expect(listRow).toBeVisible();
    await expect(listRow.getByRole('cell', { name: code, exact: true })).toBeVisible();
    await expect(listRow.getByRole('cell', { name, exact: true })).toBeVisible();

    // ---------------------------------------------------------- DB ASSERTION
    const row = await db.assertRowExists<{ id: string; name: string; code: string; unit_type: string }>(
      'mst_unit',
      { code },
      { name, unit_type: 'BRANCH' },
    );

    // ------------------------------------------------------------------ EDIT
    // Open the row's actions menu and click Edit.
    const rowEl = page.getByRole('row').filter({ hasText: code }).first();
    await expect(rowEl).toBeVisible();
    await rowEl.getByRole('button').last().click();
    await page.getByRole('menuitem', { name: /^edit$/i }).first().click();

    await page.waitForURL(/\/admin\/units\/[\w-]+\/edit/, { timeout: 8_000 });

    // Existing value pre-populated — wait for both the value AND the
    // background `/units/{id}` + `/organizations` + `/units?organization_id=…`
    // requests to settle. Without this, React Strict-Mode's double-mount can
    // fire `fetchUnit().then(reset)` a second time *after* our fillField,
    // wiping out the typed change.
    await expect(page.getByLabel(/^Unit Name/i)).toHaveValue(name);
    await page.waitForLoadState('networkidle');

    const newName = `${name} (renamed)`;
    await fillField(page, 'Unit Name', newName);
    await submitForm(page);
    await expectSuccessToast(page, /(unit (updated|saved)|updated successfully)/i);

    // DB row updated. Re-read with a retry to allow the FE-driven PUT to
    // round-trip and commit before the assertion fires; the toast/redirect
    // can land before the BE transaction is visible from a separate
    // connection in the suite's worker.
    await expect(async () => {
      const fresh = await db.query<{ id: string; name: string }>(
        'SELECT id::text, name FROM mst_unit WHERE id = $1',
        [row.id],
      );
      expect(fresh[0]?.name).toBe(newName);
    }).toPass({ timeout: 10_000, intervals: [200, 500, 1000] });

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
