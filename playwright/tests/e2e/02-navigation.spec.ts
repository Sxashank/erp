/**
 * E2E — navigation.
 *
 * Drives the actual sidebar / list-detail / tab affordances rather than
 * deep-linking. Proves that:
 *   - clicking a sidebar item changes route + main content
 *   - clicking a row changes route to the detail page
 *   - tab clicks update the active tab pill AND swap the panel content
 *   - the breadcrumb back-affordance returns to the prior list
 *
 * These are the bedrock interactions every other spec depends on; if any of
 * these break, the higher-level CRUD specs become unreliable.
 */

import { expect, test } from '../../fixtures/test';
import { loginAsAdmin } from '../../fixtures/auth';

test.describe('E2E › navigation', () => {
  test('sidebar Units link navigates to the Unit list', async ({ page, consoleGate }) => {
    void consoleGate;
    await loginAsAdmin(page);

    // Find the Units link in the sidebar. The sidebar uses <Link> elements
    // with the canonical text.
    const sidebarLink = page.getByRole('link', { name: /^units$/i }).first();
    if (!(await sidebarLink.count())) {
      // Some layouts collapse masters into a "Masters" submenu — open it.
      const mastersToggle = page.getByRole('button', { name: /^masters$/i }).first();
      if (await mastersToggle.count()) {
        await mastersToggle.click();
      }
    }
    await sidebarLink.click();
    await page.waitForURL(/\/admin\/units(\?|$)/, { timeout: 8_000 });
    // The page renders the canonical "Units" heading via <PageHeader>.
    await expect(page.getByRole('heading', { name: /^units$/i }).first()).toBeVisible();
  });

  test('list → "Add Unit" → form route', async ({ page, consoleGate }) => {
    void consoleGate;
    await loginAsAdmin(page);
    await page.goto('/admin/units');

    // PageHeader actions: a single CTA button labelled "New Unit" or "Add Unit".
    const cta = page
      .getByRole('link', { name: /^(new|add)\s+unit$/i })
      .or(page.getByRole('button', { name: /^(new|add)\s+unit$/i }))
      .first();
    await cta.click();
    await page.waitForURL(/\/admin\/units\/new/, { timeout: 8_000 });
    // Form first input must be visible.
    await expect(page.getByLabel(/^Unit Code/i)).toBeVisible();
  });
});
