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
  // Strategy ladder for resolving the control associated with a visible
  // label string. Tries the most-specific match first; each strategy is
  // an O(1) DOM read with no implicit wait, so a miss falls through fast.
  const labelRe = new RegExp(escapeRegex(label), 'i');
  let control = page.getByLabel(label, { exact: false }).first();
  let handle = (await control.count()) > 0 ? await control.elementHandle() : null;

  if (!handle) {
    // Textbox / spinbutton / combobox with the accessible name. The shadcn
    // form primitives expose the label as the accessible name on the input
    // even when the underlying `<Label>` doesn't reach the input via htmlFor.
    for (const role of ['textbox', 'spinbutton', 'combobox', 'checkbox'] as const) {
      const byRole = page.getByRole(role, { name: labelRe }).first();
      if ((await byRole.count()) > 0) {
        control = byRole;
        handle = await byRole.elementHandle();
        if (handle) break;
      }
    }
  }

  if (!handle) {
    // Last resort: locate the visible label text, then the nearest form
    // control inside its container (`.space-y-2` is the codebase convention).
    const labelEl = page
      .getByText(new RegExp(`^${escapeRegex(label)}\\s*\\*?\\s*$`, 'i'))
      .first();
    if (!(await labelEl.count())) {
      throw new Error(`fillField: control with label ${JSON.stringify(label)} not found`);
    }
    const container = labelEl.locator(
      'xpath=ancestor::*[contains(@class,"space-y-2")][1] | ancestor::*[1]',
    );
    control = container
      .locator('[role="combobox"], input, select, textarea, [role="checkbox"]')
      .first();
    if (!(await control.count())) {
      throw new Error(`fillField: no input adjacent to label ${JSON.stringify(label)}`);
    }
    handle = await control.elementHandle();
    if (!handle) {
      throw new Error(`fillField: no input adjacent to label ${JSON.stringify(label)}`);
    }
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
    const valueRe = new RegExp(`^${escapeRegex(String(value))}$`, 'i');
    const looseRe = new RegExp(escapeRegex(String(value)), 'i');
    const exact = page.getByRole('option', { name: valueRe }).first();
    if (await exact.count()) {
      await exact.click();
    } else {
      await page.getByRole('option', { name: looseRe }).first().click();
    }
    return;
  }

  // Native <select>.
  if (tagName === 'select') {
    await control.selectOption(String(value));
    return;
  }

  // Native text/number/date/email/etc.
  //
  // We can't just call `Locator.fill(value)` here: on edit pages RHF has
  // pre-populated the input via `form.reset(...)` and Playwright's `fill`
  // doesn't always trigger the change-event flow that updates RHF's
  // internal state — the input's *visible* value updates but the form's
  // serialised value lags.
  //
  // Three-phase fix:
  //   1. `Locator.clear()` empties the input. This dispatches `input` so
  //      RHF zeroes its state — important when the field already had a
  //      pre-filled value (edit page).
  //   2. `pressSequentially` types the new value one keystroke at a time
  //      so RHF's `register(...).onChange` fires for every character.
  //   3. `toHaveValue` waits for the DOM to settle.
  const stringValue = String(value);
  // We've been around the houses with `fill` (doesn't always commit RHF),
  // `pressSequentially` after `clear()` (races React's controlled rebind),
  // and the native-setter idiom (breaks for some inputs). The one
  // combination that *consistently* works is the native-setter idiom for
  // text/textarea, AND for number we use `fill`.
  //
  // The native-setter idiom is the well-known "drive a controlled React
  // input from outside React" pattern: get the value setter from the DOM
  // prototype, call it with the new value (so React's `_valueTracker`
  // sees the change), then fire `input` so RHF/React's synthetic
  // `onChange` fires. Crucially, we ALSO call `Locator.fill` first so
  // any input that doesn't use React's tracker (uncontrolled / shadcn
  // custom) still updates.
  if (type === 'number') {
    await control.fill(stringValue);
  } else {
    // Drive the value via the React-native setter so React's
    // `_valueTracker` sees the change and the synthetic onChange fires
    // (Playwright's `fill` alone does not always commit RHF state on
    // controlled inputs that were prefilled via `form.reset`). The
    // sequence is: native setter to clear, fire input, native setter to
    // the new value, fire input + change. Each event is fired AFTER the
    // corresponding value-set so React sees consistent transitions.
    await control.evaluate((el, next) => {
      const target = el as HTMLInputElement | HTMLTextAreaElement;
      const proto = target instanceof HTMLTextAreaElement
        ? HTMLTextAreaElement.prototype
        : HTMLInputElement.prototype;
      const desc = Object.getOwnPropertyDescriptor(proto, 'value');
      const setNativeValue = (v: string) => desc?.set?.call(target, v);
      // Clear first (so React's tracker sees an empty-then-new transition,
      // which prevents same-value-no-op suppression).
      setNativeValue('');
      target.dispatchEvent(new Event('input', { bubbles: true }));
      setNativeValue(next);
      target.dispatchEvent(new Event('input', { bubbles: true }));
      target.dispatchEvent(new Event('change', { bubbles: true }));
    }, stringValue);
  }
  await expect(control).toHaveValue(stringValue, { timeout: 8_000 });
  // React batches state updates; the DOM `value` may reflect the new value
  // while RHF's internal store is still in the middle of committing.
  // A short tick gives React's microtask queue a chance to flush before
  // the caller invokes submit.
  await page.waitForTimeout(50);
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
