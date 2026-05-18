/**
 * useStressTest — react-query hooks for `/lending/stress-test/*`.
 *
 * Pages never call axios directly (CLAUDE.md §5.4). Mutations don't need to
 * invalidate other queries — stress test runs are read-only computations
 * and don't mutate any cached server state. Callers surface the
 * `{error_code, message, correlation_id}` envelope via `showErrorToast`.
 */

import { useMutation, useQuery } from '@tanstack/react-query';

import {
  type ScenarioId,
  type ScenarioMetadata,
  type StressTestRunResponse,
  listScenarios,
  runAllScenarios,
  runScenario,
} from '@/services/lending/stressTestApi';

// --------------------------------------------------------------------------
// Query keys
// --------------------------------------------------------------------------

export const stressTestBaseKey = ['lending', 'stress-test'] as const;

export const stressScenariosQueryKey = () => [...stressTestBaseKey, 'scenarios'] as const;

// --------------------------------------------------------------------------
// Queries
// --------------------------------------------------------------------------

/**
 * Static scenario metadata. Cached for 1h — the list is constant on the BE
 * (see `SCENARIO_METADATA` in `stress_test_service.py`).
 */
export function useStressScenarios() {
  return useQuery<ScenarioMetadata[]>({
    queryKey: stressScenariosQueryKey(),
    queryFn: () => listScenarios(),
    staleTime: 60 * 60 * 1000, // 1 hour
    refetchOnWindowFocus: false,
  });
}

// --------------------------------------------------------------------------
// Mutations
// --------------------------------------------------------------------------

interface RunScenarioVariables {
  scenarioId: ScenarioId;
  asOfDate?: string;
}

/**
 * Run a single scenario.
 *
 * The service layer (`runScenario`) injects an `Idempotency-Key` per call
 * (CLAUDE.md §6.3). Returns the canonical envelope so the page can render
 * uniformly whether one or four scenarios are run.
 */
export function useRunStressScenario() {
  return useMutation<StressTestRunResponse, unknown, RunScenarioVariables>({
    mutationFn: ({ scenarioId, asOfDate }) => runScenario(scenarioId, asOfDate),
  });
}

interface RunAllScenariosVariables {
  asOfDate?: string;
}

/**
 * Run all 4 scenarios against a single snapshot — primary entry point for
 * the page's "Run Stress Test" button.
 */
export function useRunAllStressScenarios() {
  return useMutation<StressTestRunResponse, unknown, RunAllScenariosVariables>({
    mutationFn: ({ asOfDate } = {}) => runAllScenarios(asOfDate),
  });
}
