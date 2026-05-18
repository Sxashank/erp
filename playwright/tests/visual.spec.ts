/**
 * Visual regression — baseline screenshots for 10 critical screens.
 *
 * Tracked as STAGE-7-PENDING-visual-baselines. This spec is GATED behind
 * `PLAYWRIGHT_VISUAL=1` so CI runs visuals only when the baseline images
 * are committed. To capture baselines locally:
 *
 *     pnpm dev            # in one shell
 *     PLAYWRIGHT_VISUAL=1 pnpm test:e2e --update-snapshots visual.spec.ts
 *     git add playwright/tests/__screenshots__
 *
 * After that, `PLAYWRIGHT_VISUAL=1 pnpm test:e2e visual.spec.ts` diffs
 * against the baseline and fails on any unintended change. CLAUDE.md §9.
 *
 * 10 critical flows covered per CLAUDE.md §10.5 / .stubs-approved.md:
 *   1. login / auth
 *   2. dashboard (post-login overview)
 *   3. loan-application list
 *   4. loan-application detail
 *   5. GL posting create (dense finance screen)
 *   6. payroll batch list
 *   7. customer list (AP/AR)
 *   8. fixed-asset list
 *   9. compliance dashboard
 *  10. audit-log list
 *
 * Each flow captures both desktop (1440×900) and tablet (768×1024) viewports.
 */

import { expect, test } from '../fixtures/test';

declare const process: { env: Record<string, string | undefined> };

const VISUAL_ENABLED = process.env.PLAYWRIGHT_VISUAL === '1';

interface Flow {
  /** Friendly name used in the baseline filename — lowercase, hyphen-separated. */
  slug: string;
  /** Route to visit. Relative to baseURL. */
  path: string;
  /** If true, use the seeded-auth fixture (authedPage) so we land past login. */
  needsAuth: boolean;
  /** If set, wait for this selector to be visible before snapshotting. */
  waitFor?: string;
}

const FLOWS: Flow[] = [
  { slug: 'login', path: '/login', needsAuth: false },
  { slug: 'dashboard', path: '/admin/dashboard', needsAuth: true },
  { slug: 'loan-application-list', path: '/admin/lending/applications', needsAuth: true },
  {
    slug: 'loan-application-detail',
    path: '/admin/lending/applications/demo-app-1',
    needsAuth: true,
  },
  { slug: 'gl-posting-create', path: '/admin/accounting/gl-postings/new', needsAuth: true },
  { slug: 'payroll-batch-list', path: '/payroll/batches', needsAuth: true },
  { slug: 'customer-list', path: '/admin/ap-ar/customers', needsAuth: true },
  { slug: 'fixed-asset-list', path: '/admin/fixed-assets/assets', needsAuth: true },
  { slug: 'compliance-dashboard', path: '/admin/compliance', needsAuth: true },
  { slug: 'audit-log-list', path: '/admin/audit-logs', needsAuth: true },
];

const VIEWPORTS = [
  { label: 'desktop', width: 1440, height: 900 },
  { label: 'tablet', width: 768, height: 1024 },
] as const;

test.describe('visual regression — 10 critical flows', () => {
  test.skip(!VISUAL_ENABLED, 'Set PLAYWRIGHT_VISUAL=1 to run visual baselines.');

  for (const flow of FLOWS) {
    for (const vp of VIEWPORTS) {
      test(`${flow.slug} — ${vp.label} ${vp.width}x${vp.height}`, async ({
        page,
        authedPage,
        consoleGate,
      }) => {
        const target = flow.needsAuth ? authedPage : page;
        // The authed-page fixture injects localStorage tokens; the dev server
        // may still return 4xx on routes that depend on a real backend
        // response. Those are allowed so the visual spec focuses on layout,
        // not backend wiring.
        consoleGate.allowStatus(401);
        consoleGate.allowStatus(403);
        consoleGate.allowStatus(404);

        await target.setViewportSize({ width: vp.width, height: vp.height });
        await target.goto(flow.path);
        await target.evaluate(() => document.fonts.ready);

        if (flow.waitFor) {
          await target.waitForSelector(flow.waitFor, { state: 'visible' });
        }

        await expect(target).toHaveScreenshot(`${flow.slug}-${vp.label}.png`, {
          fullPage: false,
          // The page-level skeleton can flicker before first paint even after
          // fonts.ready; give animations a frame to settle.
          animations: 'disabled',
        });
      });
    }
  }
});
