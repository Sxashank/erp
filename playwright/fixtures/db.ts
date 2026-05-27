/**
 * Direct-Postgres helper for E2E specs.
 *
 * Per the plan's "UI → API → DB → reload" loop, every spec needs to assert
 * what the server actually persisted, not just what the UI shows. This module
 * opens a real `pg.Client` against the dedicated E2E database
 * (`DATABASE_URL_E2E` env, default `postgres://smfc:smfc_secret@localhost:5432/smfc_erp_e2e`),
 * sets the tenant-context GUC so RLS (CLAUDE.md §3.4 / §6.2) returns rows for
 * the E2E org, and exposes a small assertion surface:
 *
 *   - `dbConnect(orgId)`     → returns a `DbHelper` already in tenant context
 *   - `assertRowExists(...)` → fail with a clear diff if missing / mismatch
 *   - `assertRowMatches(...)` → subset match by primary key
 *   - `cleanupByPrefix(...)` → optional teardown for rerunnable suites
 *
 * The helper is per-test (open + close) rather than worker-scoped so a failed
 * connection in one spec does not poison the others. Connection cost is
 * negligible against localhost.
 */

import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { Client, type QueryResultRow } from 'pg';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '..', '..');
const LIVE_BACKEND_ENABLED = process.env.PLAYWRIGHT_LIVE_BACKEND === '1';
const LIVE_ADMIN_USERNAME = process.env.UAT_ADMIN_USERNAME ?? 'krishna';
const LIVE_ORG_CODE = process.env.PLAYWRIGHT_LIVE_ORG_CODE ?? 'SMFC_UAT';

export const E2E_DATABASE_URL =
  process.env.DATABASE_URL_E2E ?? 'postgres://smfc:smfc_secret@localhost:5432/smfc_erp_e2e';
export const LIVE_DATABASE_URL =
  process.env.DATABASE_URL_LIVE ?? 'postgres://smfc:smfc_secret@localhost:5432/smfc_erp';
export const PLAYWRIGHT_DATABASE_URL = LIVE_BACKEND_ENABLED ? LIVE_DATABASE_URL : E2E_DATABASE_URL;

/**
 * Resolve the E2E organization UUID written by `backend/scripts/seed_e2e.sh`
 * to `playwright/.e2e-org-id`. Falls back to `E2E_ORG_ID` env if the file is
 * missing (CI checkout, fresh worktree, etc.).
 */
export function readE2EOrgId(): string {
  if (process.env.E2E_ORG_ID) return process.env.E2E_ORG_ID;
  try {
    const path = resolve(ROOT, 'playwright', '.e2e-org-id');
    return readFileSync(path, 'utf8').trim();
  } catch (err) {
    throw new Error(
      'E2E org UUID not found. Either set E2E_ORG_ID or run `backend/scripts/seed_e2e.sh` first.',
    );
  }
}

async function resolveDefaultOrgId(client: Client): Promise<string> {
  if (!LIVE_BACKEND_ENABLED) {
    return readE2EOrgId();
  }

  if (process.env.PLAYWRIGHT_ORG_ID) {
    return process.env.PLAYWRIGHT_ORG_ID;
  }

  const byUser = await client.query<{ organization_id: string }>(
    `SELECT organization_id::text AS organization_id
     FROM mst_user
     WHERE username = $1
       AND organization_id IS NOT NULL
     ORDER BY created_at DESC
     LIMIT 1`,
    [LIVE_ADMIN_USERNAME],
  );
  if (byUser.rowCount && byUser.rows[0]?.organization_id) {
    return byUser.rows[0].organization_id;
  }

  const byCode = await client.query<{ id: string }>(
    `SELECT id::text AS id
     FROM mst_organization
     WHERE code = $1
     LIMIT 1`,
    [LIVE_ORG_CODE],
  );
  if (byCode.rowCount && byCode.rows[0]?.id) {
    return byCode.rows[0].id;
  }

  throw new Error(
    `Could not resolve Playwright org context for live backend mode. ` +
      `Checked PLAYWRIGHT_ORG_ID, admin user ${JSON.stringify(LIVE_ADMIN_USERNAME)}, ` +
      `and org code ${JSON.stringify(LIVE_ORG_CODE)} in ${PLAYWRIGHT_DATABASE_URL}.`,
  );
}

export interface DbHelper {
  client: Client;
  orgId: string;
  /** Execute an ad-hoc query with positional params. */
  query<T extends QueryResultRow = QueryResultRow>(sql: string, params?: unknown[]): Promise<T[]>;
  /** Assert a row exists; optionally check a subset of columns. */
  assertRowExists<T extends QueryResultRow = QueryResultRow>(
    table: string,
    where: Record<string, unknown>,
    expectedColumns?: Record<string, unknown>,
  ): Promise<T>;
  /** Assert a row matches expected columns (sub-set). Pass PK in `where`. */
  assertRowMatches<T extends QueryResultRow = QueryResultRow>(
    table: string,
    where: Record<string, unknown>,
    expectedColumns: Record<string, unknown>,
  ): Promise<T>;
  /** Delete every row in `table` whose `code` (or supplied column) begins with
   *  the test prefix, scoped to the E2E org. Safe to call from teardown. */
  cleanupByPrefix(table: string, prefix: string, column?: string): Promise<number>;
  end(): Promise<void>;
}

function buildWhere(where: Record<string, unknown>, startParam: number) {
  const keys = Object.keys(where);
  if (keys.length === 0) throw new Error('assertRowExists: where clause is empty');
  const clauses: string[] = [];
  const params: unknown[] = [];
  keys.forEach((k, i) => {
    clauses.push(`${quoteIdent(k)} = $${startParam + i}`);
    params.push(where[k]);
  });
  return { sql: clauses.join(' AND '), params };
}

/**
 * Quote a SQL identifier (table or column name). Allows only alphanumerics
 * and underscores — keeps callers honest, no string-interpolation surprises.
 */
function quoteIdent(ident: string): string {
  if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(ident)) {
    throw new Error(`unsafe SQL identifier: ${JSON.stringify(ident)}`);
  }
  return `"${ident}"`;
}

export async function dbConnect(orgId?: string): Promise<DbHelper> {
  const client = new Client({ connectionString: PLAYWRIGHT_DATABASE_URL });
  await client.connect();
  const resolvedOrg = orgId ?? (await resolveDefaultOrgId(client));
  // RLS GUC — CLAUDE.md §3.4. Without this, every SELECT against an
  // org-scoped table returns zero rows even when the data is there.
  await client.query("SELECT set_config('app.current_org_id', $1, false)", [resolvedOrg]);

  const helper: DbHelper = {
    client,
    orgId: resolvedOrg,
    async query(sql, params) {
      const res = await client.query(sql, params);
      return res.rows as never;
    },
    async assertRowExists(table, where, expectedColumns) {
      const w = buildWhere(where, 1);
      const sql = `SELECT * FROM ${quoteIdent(table)} WHERE ${w.sql} LIMIT 1`;
      const res = await client.query(sql, w.params);
      if (res.rows.length === 0) {
        throw new Error(
          `DB row not found in ${table} where ${JSON.stringify(where)}. ` +
            `Did the UI save succeed? Did RLS allow the read for org ${resolvedOrg}?`,
        );
      }
      const row = res.rows[0];
      if (expectedColumns) {
        for (const [col, want] of Object.entries(expectedColumns)) {
          const got = row[col];
          if (!sameValue(got, want)) {
            throw new Error(
              `DB column ${table}.${col} mismatch: expected ${JSON.stringify(want)}, got ${JSON.stringify(got)} (row ${JSON.stringify(where)})`,
            );
          }
        }
      }
      return row as never;
    },
    async assertRowMatches(table, where, expectedColumns) {
      const w = buildWhere(where, 1);
      const sql = `SELECT * FROM ${quoteIdent(table)} WHERE ${w.sql} LIMIT 1`;
      const res = await client.query(sql, w.params);
      if (res.rows.length === 0) {
        throw new Error(
          `assertRowMatches: row not found in ${table} where ${JSON.stringify(where)}`,
        );
      }
      const row = res.rows[0];
      const drift: string[] = [];
      for (const [col, want] of Object.entries(expectedColumns)) {
        const got = row[col];
        if (!sameValue(got, want)) {
          drift.push(`  ${col}: expected ${JSON.stringify(want)}, got ${JSON.stringify(got)}`);
        }
      }
      if (drift.length > 0) {
        throw new Error(
          `DB row drift in ${table} (${JSON.stringify(where)}):\n${drift.join('\n')}`,
        );
      }
      return row as never;
    },
    async cleanupByPrefix(table, prefix, column = 'code') {
      // Probe whether the table is org-scoped — global masters like
      // mst_designation have no `organization_id` column.
      const cols = await client.query<{ column_name: string }>(
        "SELECT column_name FROM information_schema.columns WHERE table_name = $1 AND column_name = 'organization_id'",
        [table],
      );
      if (cols.rows.length === 0) {
        const sql = `DELETE FROM ${quoteIdent(table)} WHERE ${quoteIdent(column)} LIKE $1`;
        const res = await client.query(sql, [`${prefix}%`]);
        return res.rowCount ?? 0;
      }
      const sql = `DELETE FROM ${quoteIdent(table)} WHERE ${quoteIdent(column)} LIKE $1 AND organization_id = $2`;
      const res = await client.query(sql, [`${prefix}%`, resolvedOrg]);
      return res.rowCount ?? 0;
    },
    async end() {
      await client.end();
    },
  };
  return helper;
}

function sameValue(got: unknown, want: unknown): boolean {
  if (got instanceof Date && want instanceof Date) return got.getTime() === want.getTime();
  if (typeof got === 'object' && typeof want === 'object' && got && want) {
    return JSON.stringify(got) === JSON.stringify(want);
  }
  // Normalize numeric strings vs numbers (pg returns NUMERIC as string).
  if (typeof got === 'string' && typeof want === 'number') return Number(got) === want;
  if (typeof got === 'number' && typeof want === 'string') return got === Number(want);
  return got === want;
}
