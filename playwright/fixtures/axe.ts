/**
 * axe-core Playwright fixture.
 *
 * Every smoke + flow spec should call `runAxe(page)` on each meaningful
 * navigation. The fixture fails the test on `critical` or `serious`
 * violations; `moderate` and `minor` are reported (and surfaced in the
 * HTML report) but do not block the pipeline.
 *
 * See CLAUDE.md §5.11 (accessibility) and §10.5 (E2E).
 *
 * Usage:
 *
 *   import { test } from '../fixtures/test';
 *   import { runAxe } from '../fixtures/axe';
 *
 *   test('login page is accessible', async ({ page }) => {
 *     await page.goto('/login');
 *     await runAxe(page);  // throws on critical/serious violations
 *   });
 *
 * To bypass a known false-positive, pass `ignoreRules: [...]` or
 * `ignoreSelectors: [...]`. Every suppression must be recorded in
 * `.stubs-approved.md` so it can't accumulate silently.
 */

import { expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

export interface AxeRunOptions {
  /** Run only against a specific DOM tree. Defaults to whole page. */
  include?: string;
  /** Rule IDs to disable (e.g. `['landmark-one-main']`). */
  ignoreRules?: string[];
  /** CSS selectors to exclude from analysis. */
  ignoreSelectors?: string[];
  /** Which axe tags to include. Default: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']. */
  tags?: string[];
  /**
   * Severities that MUST NOT appear. Anything in this list fails the test.
   * Default is ['critical', 'serious']; tests that need to be stricter can
   * pass ['critical', 'serious', 'moderate'].
   */
  failOnImpact?: Array<'critical' | 'serious' | 'moderate' | 'minor'>;
}

const DEFAULT_FAIL_IMPACT: NonNullable<AxeRunOptions['failOnImpact']> = [
  'critical',
  'serious',
];

const DEFAULT_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'];

/** Run axe-core against `page` and fail the test on critical/serious violations. */
export async function runAxe(page: Page, options: AxeRunOptions = {}): Promise<void> {
  const builder = new AxeBuilder({ page }).withTags(options.tags ?? DEFAULT_TAGS);

  if (options.include) builder.include(options.include);
  for (const rule of options.ignoreRules ?? []) builder.disableRules(rule);
  for (const selector of options.ignoreSelectors ?? []) builder.exclude(selector);

  const results = await builder.analyze();
  const failImpact = new Set(options.failOnImpact ?? DEFAULT_FAIL_IMPACT);

  const blocking = results.violations.filter((v) =>
    v.impact ? failImpact.has(v.impact as 'critical' | 'serious' | 'moderate' | 'minor') : false,
  );

  if (blocking.length === 0) return;

  const summary = blocking
    .map((v) => {
      const nodes = v.nodes
        .slice(0, 3)
        .map((n) => `    - ${n.target.join(' ')}`)
        .join('\n');
      return `  ${v.impact?.toUpperCase()} ${v.id}: ${v.help}\n    ${v.helpUrl}\n${nodes}`;
    })
    .join('\n\n');

  expect(
    blocking,
    `\nAxe-core found ${blocking.length} blocking violation(s):\n\n${summary}\n`,
  ).toEqual([]);
}
