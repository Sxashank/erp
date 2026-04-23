/**
 * Playwright custom test fixtures. See CLAUDE.md §10.5.
 *
 * Exposes:
 *   - `consoleGate`: fails the test on any uncaught `console.error` or on
 *     any non-asserted 4xx/5xx response during the test. The test can opt
 *     out per-request with `consoleGate.allow404(url)` or suppress a
 *     specific console error with `consoleGate.allowError(pattern)`.
 *   - `authedPage`: a Page that is already logged in as the seeded admin.
 *
 * Every E2E test imports from this module instead of `@playwright/test`
 * directly so the console gate is always on.
 */

import { expect, test as base, type ConsoleMessage, type Page, type Response } from '@playwright/test';

interface ConsoleGate {
  allowError: (pattern: RegExp | string) => void;
  allowStatus: (status: number, urlSubstring?: string) => void;
  getErrors: () => string[];
  getFailedResponses: () => Array<{ status: number; url: string }>;
}

interface AuthFixtures {
  consoleGate: ConsoleGate;
  authedPage: Page;
}

export const test = base.extend<AuthFixtures>({
  // eslint-disable-next-line no-empty-pattern
  consoleGate: async ({ page }, use, testInfo) => {
    const errorAllowlist: Array<RegExp | string> = [];
    const statusAllowlist: Array<{ status: number; urlSubstring?: string }> = [];
    const errors: string[] = [];
    const failedResponses: Array<{ status: number; url: string }> = [];

    const onConsole = (msg: ConsoleMessage) => {
      if (msg.type() !== 'error') return;
      const text = msg.text();
      if (errorAllowlist.some((p) => (p instanceof RegExp ? p.test(text) : text.includes(p)))) return;
      errors.push(text);
    };

    const onResponse = (res: Response) => {
      const status = res.status();
      if (status < 400) return;
      const url = res.url();
      // Don't gate on static asset 404s (favicons etc.).
      if (/\.(ico|png|jpg|jpeg|gif|svg|map)(\?.*)?$/.test(url)) return;
      if (
        statusAllowlist.some(
          (a) =>
            a.status === status &&
            (!a.urlSubstring || url.includes(a.urlSubstring)),
        )
      ) {
        return;
      }
      failedResponses.push({ status, url });
    };

    const onPageError = (err: Error) => {
      if (errorAllowlist.some((p) => (p instanceof RegExp ? p.test(err.message) : err.message.includes(p))))
        return;
      errors.push(`uncaught: ${err.message}`);
    };

    page.on('console', onConsole);
    page.on('response', onResponse);
    page.on('pageerror', onPageError);

    const gate: ConsoleGate = {
      allowError: (pattern) => errorAllowlist.push(pattern),
      allowStatus: (status, urlSubstring) => statusAllowlist.push({ status, urlSubstring }),
      getErrors: () => [...errors],
      getFailedResponses: () => [...failedResponses],
    };

    await use(gate);

    page.off('console', onConsole);
    page.off('response', onResponse);
    page.off('pageerror', onPageError);

    if (testInfo.status !== 'skipped') {
      expect(errors, 'no uncaught console.error expected').toEqual([]);
      expect(
        failedResponses,
        'no non-asserted 4xx/5xx responses expected',
      ).toEqual([]);
    }
  },

  authedPage: async ({ page, context }, use) => {
    // Seed tokens + user + org into localStorage so `<AuthProvider>` skips
    // the server round-trip. This matches the shape persisted by Zustand.
    await context.addInitScript(() => {
      const seededAuth = {
        state: {
          accessToken: 'playwright-access-token',
          refreshToken: 'playwright-refresh-token',
        },
        version: 0,
      };
      const seededOrg = {
        state: {
          activeOrganizationId: '11111111-1111-1111-1111-111111111111',
        },
        version: 0,
      };
      window.localStorage.setItem('smfc-auth', JSON.stringify(seededAuth));
      window.localStorage.setItem('smfc-organization', JSON.stringify(seededOrg));
    });
    await use(page);
  },
});

export { expect };
