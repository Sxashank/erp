/**
 * E2E — masters CRUD (batch).
 *
 * Data-driven loop that exercises the same UI → API → DB → reload journey
 * across every Tier-1 master after Unit (which is the hand-written canonical
 * example in `10-masters.spec.ts`). Each entry below adds one full CRUD spec
 * for a master without duplicating the assertion plumbing.
 *
 * Each entity declares:
 *   - `routeList`        — `/admin/…` list URL
 *   - `routeNew`         — `/admin/…/new` URL
 *   - `routeEditTpl(id)` — function returning the edit URL for an id
 *   - `firstFieldLabel`  — the label we wait for before driving the form
 *   - `prefix`           — short code prefix (≤ 8 chars to fit varchar(20))
 *   - `formFields`       — fields filled in order (combo / text)
 *   - `editableLabel`    — which field is modified on the edit pass
 *   - `dbTable`          — `mst_*` table that backs the entity
 *   - `dbExpected`       — extra columns to assert beyond `name`
 *   - `successToastRe`   — regex matching the page's success toast
 *
 * Stays in lockstep with `99-cleanup.spec.ts::targets`: every new entry
 * here must also be added there so its rows are removed by teardown.
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

interface MasterSpec {
  module: string;
  entity: string;
  prefix: string;
  routeList: string;
  routeNew: string;
  routeEditTpl: (id: string) => string;
  firstFieldLabel: RegExp;
  /** Fields filled before submit, in the order they should be driven.
   *  Each entry is `[label, value, kind]` — `text` uses fillForm,
   *  `combo` uses fillField (handles shadcn `<Select>`). */
  formFields: Array<['text' | 'combo', string, string]>;
  editableLabel: string;
  /** Column the BE uses to store the editable field. Defaults to `name`. */
  dbNameColumn?: string;
  dbTable: string;
  /** Columns to assert exist with these values immediately after create. */
  dbExpected: Record<string, unknown>;
  /** Toast pattern; some forms only redirect on success without a toast.
   *  When null the spec relies on the URL redirect alone. */
  successToastRe: RegExp | null;
  /** When false, the entity has no `organization_id` column (global master
   *  like designations) — the cleanup spec adapts automatically. */
  dbHasOrgScope?: boolean;
}

const ORG_NAME = 'SMFC E2E Sandbox';

const ENTITIES: MasterSpec[] = [
  // ---------------------------------------------------------------- Department
  {
    module: 'masters',
    entity: 'Department',
    prefix: 'DEPT',
    routeList: '/admin/departments',
    routeNew: '/admin/departments/new',
    routeEditTpl: (id) => `/admin/departments/${id}/edit`,
    firstFieldLabel: /Department Code/i,
    formFields: [
      ['text', 'Department Code', '__CODE__'],
      ['text', 'Department Name', '__NAME__'],
      ['combo', 'Organization', ORG_NAME],
    ],
    editableLabel: 'Department Name',
    dbTable: 'mst_department',
    dbExpected: {},
    successToastRe: /(department (created|saved|updated)|saved successfully|created successfully|updated successfully)/i,
    dbHasOrgScope: true,
  },

  // ---------------------------------------------------------- Voucher Type
  {
    module: 'finance',
    entity: 'Voucher Type',
    prefix: 'VT',
    routeList: '/admin/finance/voucher-types',
    routeNew: '/admin/finance/voucher-types/new',
    routeEditTpl: (id) => `/admin/finance/voucher-types/${id}/edit`,
    firstFieldLabel: /Voucher Type Code/i,
    formFields: [
      ['combo', 'Organization', ORG_NAME],
      ['combo', 'Voucher Class', 'Journal Voucher'],
      ['text', 'Voucher Type Code', '__CODE__'],
      ['text', 'Voucher Type Name', '__NAME__'],
      ['text', 'Prefix', 'VTPRE-'],
    ],
    editableLabel: 'Voucher Type Name',
    dbTable: 'mst_voucher_type',
    dbExpected: { voucher_class: 'JOURNAL' },
    successToastRe: /(voucher (type )?(created|saved|updated)|created successfully|updated successfully)/i,
    dbHasOrgScope: true,
  },

  // ---------------------------------------------------------- Designation
  // Note: `mst_designation` is a global table (no `organization_id`), so the
  // 99-cleanup spec doesn't org-scope its delete.
  {
    module: 'masters',
    entity: 'Designation',
    prefix: 'DESIG',
    routeList: '/admin/designations',
    routeNew: '/admin/designations/new',
    routeEditTpl: (id) => `/admin/designations/${id}/edit`,
    firstFieldLabel: /Designation Code/i,
    formFields: [
      ['text', 'Designation Code', '__CODE__'],
      ['text', 'Designation Name', '__NAME__'],
    ],
    editableLabel: 'Designation Name',
    dbTable: 'mst_designation',
    dbExpected: {},
    successToastRe: /(designation (created|saved|updated)|created successfully|updated successfully)/i,
    dbHasOrgScope: false,
  },

  // ---------------------------------------------------------- GST Rate
  // FormShell-based; no toast on success — relies on the post-save redirect
  // back to the list page. The DB column for the natural-key uniqueness is
  // `code`. Effective dates come from a default `new Date().toISOString()`
  // initialiser in the form, so the spec only fills the user-required
  // (`code`, `name`, `rate`) fields.
  {
    module: 'gst',
    entity: 'GST Rate',
    prefix: 'GR',
    routeList: '/admin/gst/rates',
    routeNew: '/admin/gst/rates/new',
    routeEditTpl: (id) => `/admin/gst/rates/${id}/edit`,
    firstFieldLabel: /^Code/i,
    formFields: [
      ['text', 'Code', '__CODE__'],
      ['text', 'Name', '__NAME__'],
      // zod schema enforces `rate == cgst+sgst` AND `rate == igst`.
      ['text', 'rate', '18'],
      ['text', 'cgst Rate', '9'],
      ['text', 'sgst Rate', '9'],
      ['text', 'igst Rate', '18'],
    ],
    editableLabel: 'Name',
    dbTable: 'mst_gst_rate',
    dbExpected: {},
    successToastRe: null,
    dbHasOrgScope: true,
  },

  // ---------------------------------------------------------- HSN/SAC
  {
    module: 'gst',
    entity: 'HSN/SAC',
    prefix: 'HSN',
    routeList: '/admin/gst/hsn-sac',
    routeNew: '/admin/gst/hsn-sac/new',
    routeEditTpl: (id) => `/admin/gst/hsn-sac/${id}/edit`,
    firstFieldLabel: /^Code/i,
    formFields: [
      ['text', 'Code', '__CODE__'],
      ['combo', 'Type', 'HSN'],
      ['text', 'Description', '__NAME__'],
    ],
    editableLabel: 'Description',
    dbNameColumn: 'description',
    dbTable: 'mst_hsn_sac',
    dbExpected: { hsn_sac_type: 'HSN' },
    successToastRe: null,
    dbHasOrgScope: true,
  },

  // ---------------------------------------------------------- Payment Terms
  {
    module: 'ap_ar',
    entity: 'Payment Terms',
    prefix: 'PTERM',
    routeList: '/admin/ap-ar/payment-terms',
    routeNew: '/admin/ap-ar/payment-terms/new',
    routeEditTpl: (id) => `/admin/ap-ar/payment-terms/${id}/edit`,
    firstFieldLabel: /^Code/i,
    formFields: [
      ['combo', 'Organization', ORG_NAME],
      ['text', 'Code', '__CODE__'],
      ['text', 'Name', '__NAME__'],
      ['text', 'Due Days', '30'],
    ],
    editableLabel: 'Name',
    dbTable: 'mst_payment_terms',
    dbExpected: { days: 30 },
    successToastRe: /(payment terms? (created|saved|updated)|created successfully|updated successfully|saved successfully)/i,
    dbHasOrgScope: true,
  },
];

for (const spec of ENTITIES) {
  test.describe(`Masters › ${spec.entity}`, () => {
    test('create → list shows row → DB row exists → edit → DB updated → reload', async ({
      page,
      consoleGate,
      db,
    }) => {
      consoleGate.allowStatus(404, '/api/v1');
      const code = uniqueCode(spec.prefix);
      const name = `E2E ${spec.entity} ${code}`;

      // ------------------------------------------------------------- CREATE
      await loginAsAdmin(page);
      await page.goto(spec.routeNew);

      // Wait for the form to render before driving any field.
      await expect(
        page.getByRole('textbox', { name: spec.firstFieldLabel }).first(),
      ).toBeVisible({ timeout: 10_000 });

      const textFields: Record<string, string> = {};
      for (const [kind, label, rawValue] of spec.formFields) {
        const value = rawValue.replace('__CODE__', code).replace('__NAME__', name);
        if (kind === 'text') {
          textFields[label] = value;
        }
      }
      if (Object.keys(textFields).length > 0) {
        await fillForm(page, textFields);
      }
      for (const [kind, label, rawValue] of spec.formFields) {
        if (kind === 'combo') {
          const value = rawValue.replace('__CODE__', code).replace('__NAME__', name);
          await fillField(page, label, value);
        }
      }

      await submitForm(page);
      if (spec.successToastRe) {
        await expectSuccessToast(page, spec.successToastRe);
      }

      // Redirect back to the list page.
      await page.waitForURL(new RegExp(spec.routeList.replace(/\//g, '\\/')), {
        timeout: 10_000,
      });

      // ----------------------------------------------------------- LIST UI
      const listRow = page.getByRole('row').filter({ hasText: code }).first();
      await expect(listRow).toBeVisible({ timeout: 10_000 });

      // ----------------------------------------------------- DB ASSERTION
      const nameCol = spec.dbNameColumn ?? 'name';
      const row = await db.assertRowExists<{ id: string; name: string; code: string }>(
        spec.dbTable,
        { code },
        { [nameCol]: name, ...spec.dbExpected },
      );

      // --------------------------------------------------------------- EDIT
      await page.goto(spec.routeEditTpl(row.id));
      await expect(page.getByLabel(new RegExp(`^${spec.editableLabel}`, 'i'))).toHaveValue(name, {
        timeout: 10_000,
      });
      // Wait for *all* pending requests so React Strict-Mode's double-
      // mount can't fire `reset()` again and clobber the typed value.
      await page.waitForLoadState('networkidle');

      const newName = `${name} (renamed)`;
      await fillField(page, spec.editableLabel, newName);
      await submitForm(page);
      if (spec.successToastRe) {
        await expectSuccessToast(page, spec.successToastRe);
      }

      // DB updated.
      await expect(async () => {
        const fresh = await db.query<Record<string, unknown>>(
          `SELECT id::text, "${nameCol}" AS name_value FROM ${spec.dbTable} WHERE id = $1`,
          [row.id],
        );
        expect(fresh[0]?.name_value).toBe(newName);
      }).toPass({ timeout: 10_000, intervals: [200, 500, 1000] });

      // ---------------------------------------------- RELOAD CONFIRMS UI
      await page.goto(spec.routeEditTpl(row.id));
      await expect(page.getByLabel(new RegExp(`^${spec.editableLabel}`, 'i'))).toHaveValue(
        newName,
        { timeout: 10_000 },
      );
    });
  });
}
