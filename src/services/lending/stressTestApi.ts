/**
 * Stress Test API service.
 *
 * Thin axios wrapper for `/lending/stress-test/*`. Wire format is camelCase
 * (Pydantic `CamelSchema` on the BE). Money / rate fields are JSON strings
 * on the wire — Pydantic v2 serialises `Decimal` as `string` so we never
 * lose precision (CLAUDE.md §6.2).
 *
 * Mutating endpoints inject a fresh `Idempotency-Key` per call
 * (CLAUDE.md §6.3). The math is pure computation but the API contract is
 * consistent across financial endpoints — same header policy, same error
 * envelope, same retry semantics.
 */

import api from '../api';

const BASE_URL = '/lending/stress-test';

// --------------------------------------------------------------------------
// Wire types
// --------------------------------------------------------------------------

export type ScenarioId =
  | 'RATE_SHOCK_PLUS_200'
  | 'RATE_SHOCK_MINUS_200'
  | 'NPA_SHOCK_PLUS_5'
  | 'COMBINED_MACRO';

export type ScenarioStatus = 'PASS' | 'WARN' | 'FAIL';

export type ScenarioCategory = 'RATE' | 'CREDIT' | 'COMBINED';

export interface ScenarioMetadata {
  scenarioId: ScenarioId;
  name: string;
  description: string;
  category: ScenarioCategory;
  shockBps: number | null;
  npaMigrationPct: string | null;
}

export interface ScenarioInputs {
  asOfDate: string; // yyyy-MM-dd
  shockBps: number | null;
  npaMigrationPct: string | null;

  totalPrincipalOutstanding: string;
  securedPrincipal: string;
  unsecuredPrincipal: string;
  rateSensitiveLiabilities: string;
  rateSensitiveAssets: string;

  tier1Capital: string;
  tier2Capital: string;
  totalCapital: string;
  totalRwa: string;

  standardSecuredRate: string;
  substandardSecuredRate: string;
  standardUnsecuredRate: string;
  substandardUnsecuredRate: string;
  provisioningRateSource: 'mst_provisioning_rate' | 'rbi_default';
}

export interface ScenarioOutputs {
  niiImpact: string;
  niiImpactPercent: string;
  provisionImpact: string;
  preStressCrar: string;
  postStressCrar: string;
  crarDeltaBps: number;
  preStressNpaRatio: string;
  postStressNpaRatio: string;
  minimumCrarRequired: string;
  breachMinimumCrar: boolean;
}

export interface ScenarioResult {
  scenarioId: ScenarioId;
  name: string;
  description: string;
  inputs: ScenarioInputs;
  outputs: ScenarioOutputs;
  status: ScenarioStatus;
  warnings: string[];
}

export interface StressTestSummary {
  scenariosRun: number;
  overallStatus?: ScenarioStatus;
  status?: ScenarioStatus;
  failCount?: number;
  warnCount?: number;
  passCount?: number;
}

export interface StressTestRunResponse {
  asOfDate: string;
  results: ScenarioResult[];
  summary: StressTestSummary;
}

// --------------------------------------------------------------------------
// Request shapes
// --------------------------------------------------------------------------

export interface RunScenarioRequest {
  scenarioId: ScenarioId;
  asOfDate?: string;
}

export interface RunAllScenariosRequest {
  asOfDate?: string;
}

// --------------------------------------------------------------------------
// Calls
// --------------------------------------------------------------------------

/**
 * GET /lending/stress-test/scenarios — static metadata for the 4 scenarios.
 */
export async function listScenarios(): Promise<ScenarioMetadata[]> {
  const { data } = await api.get<ScenarioMetadata[]>(`${BASE_URL}/scenarios`);
  return data;
}

/**
 * POST /lending/stress-test/run — runs one scenario.
 *
 * Generates a fresh `Idempotency-Key` per call (CLAUDE.md §6.3) so retries
 * dedupe even though the computation is read-only.
 */
export async function runScenario(
  scenarioId: ScenarioId,
  asOfDate?: string,
): Promise<StressTestRunResponse> {
  const { data } = await api.post<StressTestRunResponse>(
    `${BASE_URL}/run`,
    { scenarioId, asOfDate },
    { headers: { 'Idempotency-Key': crypto.randomUUID() } },
  );
  return data;
}

/**
 * POST /lending/stress-test/run-all — runs all 4 scenarios against a single
 * snapshot. This is the primary entry point for the page.
 */
export async function runAllScenarios(asOfDate?: string): Promise<StressTestRunResponse> {
  const { data } = await api.post<StressTestRunResponse>(
    `${BASE_URL}/run-all`,
    { asOfDate },
    { headers: { 'Idempotency-Key': crypto.randomUUID() } },
  );
  return data;
}

export const stressTestApi = {
  listScenarios,
  runScenario,
  runAllScenarios,
};

export default stressTestApi;
