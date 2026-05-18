/**
 * Form-fill helpers for real-user E2E specs.
 *
 * Built on Playwright's role-based / label-based selectors so the suite is
 * stable across UI refactors and does not require new `data-testid`
 * attributes (which the codebase only adds incrementally for ambiguous
 * affordances — see `E2E_BOOTSTRAP_FIXES.md` § "Selector strategy decision").
 *
 *   fillForm(page, { 'Unit Name': 'E2E Unit', Code: 'E2E-...' })
 *
 * Recognized control types (in order):
 *   - native text/number/date inputs        → page.getByLabel().fill()
 *   - shadcn <Select>                       → combobox open + option click
 *   - native <select>                       → page.getByLabel().selectOption()
 *   - checkbox                              → page.getByLabel().setChecked()
 *
 * Successful saves are asserted via `expectSuccessToast`; validation errors
 * via `expectFieldError`. Both are tolerant of the toaster library variance
 * (react-hot-toast vs shadcn `<Sonner>` vs a custom <Toast>).
 */

import { expect, type Locator, type Page } from '@playwright/test';

export type FieldValue = string | number | boolean | null | undefined;
export type FormValues = Record<string, FieldValue>;

export async function fillForm(page: Page, values: FormValues): Promise<void> {
  for (const [label, value] of Object.entries(values)) {
    if (value === undefined) continue;
    await fillField(page, label, value);
  }
}

/** Single-field filler — exported so specs can drive a wizard step-by-step. */
export async function fillField(page: Page, label: string, value: FieldValue): Promise<void> {
  const control = page.getByLabel(label, { exact: false }).first();

  // Detect control kind via DOM role / tagName.
  const handle = await control.elementHandle();
  if (!handle) {
    throw new Error(`fillField: control with label ${JSON.stringify(label)} not found`);
  }
  const role = (await handle.getAttribute('role')) ?? '';
  const tagName = (await handle.evaluate((el) => (el as Element).tagName.toLowerCase())) ?? '';
  const type = ((await handle.getAttribute('type')) ?? '').toLowerCase();

  // Boolean inputs.
  if (type === 'checkbox' || role === 'checkbox') {
    await control.setChecked(Boolean(value));
    return;
  }

  // shadcn `<Select>` — `<button role="combobox">` with `aria-haspopup="listbox"`.
  if (role === 'combobox') {
    await control.click();
    const option = page
      .getByRole('option', { name: new RegExp(`^${escapeRegex(String(value))}$`, 'i') })
      .first();
    await option.click();
    return;
  }

  // Native <select>.
  if (tagName === 'select') {
    await control.selectOption(String(value));
    return;
  }

  // Native text/number/date/email/etc. Clear + type.
  await control.fill('');
  await control.fill(String(value));
}

/**
 * Submit the form on the current page. Looks for `<button type="submit">` —
 * shadcn `<Button type="submit">` matches.
 */
export async function submitForm(page: Page): Promise<void> {
  await page.locator('button[type="submit"]').first().click();
}

/**
 * Assert a success toast appeared. The codebase uses both `react-hot-toast`
 * and `<Sonner>`-style toasts; both render with `role="status"` containing
 * the message. Treat 5 seconds as the worst-case server round-trip.
 */
export async function expectSuccessToast(page: Page, message: RegExp | string): Promise<void> {
  const re = message instanceof RegExp ? message : new RegExp(escapeRegex(message), 'i');
  await expect(
    page.getByRole('status').filter({ hasText: re }).first(),
  ).toBeVisible({ timeout: 5_000 });
}

/**
 * Assert a per-field validation error appeared. Looks for the canonical
 * shadcn `<FormMessage>` adjacent to the labelled control.
 */
export async function expectFieldError(
  page: Page,
  label: string,
  message: RegExp | string,
): Promise<void> {
  const re = message instanceof RegExp ? message : new RegExp(escapeRegex(message), 'i');
  // shadcn wires `aria-describedby` from the control to the FormMessage; the
  // simplest stable lookup is the visible-text proximity in the same
  // FormItem container. We use `:near()` semantics via Playwright's locator
  // chaining: find the label, then the nearest text node matching `re`.
  const labelLocator = page.getByText(new RegExp(`^${escapeRegex(label)}\\b`, 'i')).first();
  const formItem = labelLocator.locator('xpath=ancestor::*[contains(@class,"form-item") or .//label][1]');
  await expect(formItem.locator(`text=${re}`).first()).toBeVisible({ timeout: 3_000 });
}

/** Convenience: open the row's Edit affordance in a DataTable. */
export async function openRowEdit(page: Page, code: string): Promise<void> {
  const row = page.getByRole('row', { name: new RegExp(escapeRegex(code)) }).first();
  await expect(row).toBeVisible();
  // Most list pages render an inline `<Link>Edit</Link>` per row; some use a
  // row-actions dropdown. Try inline first, fall back to the menu.
  const inline = row.getByRole('link', { name: /^edit$/i });
  if (await inline.count()) {
    await inline.first().click();
    return;
  }
  await row.getByRole('button', { name: /actions|more/i }).first().click();
  await page.getByRole('menuitem', { name: /^edit$/i }).first().click();
}

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export type FormLocator = Locator;
