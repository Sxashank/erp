/**
 * Stress Testing page — parametric v1.
 *
 * Lets a treasury user run the four standard stress scenarios:
 *   1. Rate shock +200 bps  (NII impact, IRS Gap math)
 *   2. Rate shock -200 bps
 *   3. NPA shock +5%        (5% migrate Standard → Substandard)
 *   4. Combined macro       (1 + 3)
 *
 * Math is parametric — no Monte Carlo, no portfolio revaluation engine.
 * Honest scope for v1 (CLAUDE.md §1 quality bar: do not fabricate).
 *
 * Routed at /admin/treasury/stress-test in src/App.tsx.
 *
 * UI contract:
 *   - <PageHeader> with breadcrumbs + a "Run Stress Test" action.
 *   - On click, all 4 scenarios run via `useRunAllStressScenarios`.
 *   - First render (no results) shows an <EmptyState> CTA prompting "Run".
 *   - While running, shows a <SkeletonTable>.
 *   - On failure, shows an <ErrorState> with the canonical envelope.
 *   - On success, renders 4 status cards + a detail Table.
 */

import { ArrowLeft, Loader2, AlertTriangle, Play } from 'lucide-react';
import { useMemo } from 'react';
import { Link } from 'react-router-dom';

import { AmountDisplay } from '@/components/common/AmountDisplay';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { SkeletonTable } from '@/components/common/SkeletonTable';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useRunAllStressScenarios } from '@/hooks/lending/useStressTest';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import { cn } from '@/lib/utils';
import type { ScenarioResult, ScenarioStatus } from '@/services/lending/stressTestApi';

/** Map a stress status to a StatusPill-compatible value + variant hint. */
const STATUS_LABEL: Record<ScenarioStatus, string> = {
  PASS: 'Pass',
  WARN: 'Warn',
  FAIL: 'Fail',
};

/** Decimal-string → number for display only (never for math). */
function toNumber(value: string | null | undefined): number {
  if (value === null || value === undefined || value === '') return 0;
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

/** Format a percentage decimal-string (e.g. "12.34") as "12.34%". */
function formatPct(value: string | null | undefined, digits = 2): string {
  const n = toNumber(value);
  return `${n.toFixed(digits)}%`;
}

function formatBps(bps: number): string {
  const sign = bps > 0 ? '+' : '';
  return `${sign}${bps} bps`;
}

function statusToneClass(status: ScenarioStatus): string {
  switch (status) {
    case 'PASS':
      return 'border-green-200 bg-green-50';
    case 'WARN':
      return 'border-amber-200 bg-amber-50';
    case 'FAIL':
      return 'border-red-200 bg-red-50';
  }
}

/** Local PASS/WARN/FAIL pill — the canonical StatusBadge enum doesn't
 *  include stress-test statuses yet. See CLAUDE.md §5.8 — when a domain
 *  status is reused across pages, promote this to a `StressStatusBadge`
 *  under `src/components/lending/common/`.
 */
function StressStatusPill({ status }: { status: ScenarioStatus }): JSX.Element {
  const toneClass: Record<ScenarioStatus, string> = {
    PASS: 'bg-green-100 text-green-800 border-green-300',
    WARN: 'bg-amber-100 text-amber-800 border-amber-300',
    FAIL: 'bg-red-100 text-red-800 border-red-300',
  };
  return (
    <Badge
      variant="outline"
      className={cn('border px-2.5 py-0.5 text-xs font-medium', toneClass[status])}
    >
      {STATUS_LABEL[status]}
    </Badge>
  );
}

interface ResultCardProps {
  result: ScenarioResult;
}

function ResultCard({ result }: ResultCardProps): JSX.Element {
  const o = result.outputs;
  return (
    <Card className={statusToneClass(result.status)}>
      <CardHeader className="flex flex-row items-start justify-between gap-2 space-y-0 pb-2">
        <div className="min-w-0">
          <CardTitle className="text-base font-semibold">{result.name}</CardTitle>
          <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{result.description}</p>
        </div>
        <StressStatusPill status={result.status} />
      </CardHeader>
      <CardContent className="space-y-2 pt-2 text-sm">
        <div className="flex items-baseline justify-between">
          <span className="text-muted-foreground">Post-stress CRAR</span>
          <span className="font-semibold tabular-nums">{formatPct(o.postStressCrar)}</span>
        </div>
        <div className="flex items-baseline justify-between">
          <span className="text-muted-foreground">CRAR change</span>
          <span className="font-medium tabular-nums">{formatBps(o.crarDeltaBps)}</span>
        </div>
        <div className="flex items-baseline justify-between">
          <span className="text-muted-foreground">NII impact</span>
          <AmountDisplay amount={toNumber(o.niiImpact)} compact />
        </div>
        <div className="flex items-baseline justify-between">
          <span className="text-muted-foreground">Provision impact</span>
          <AmountDisplay amount={toNumber(o.provisionImpact)} compact />
        </div>
        {o.breachMinimumCrar && (
          <p className="mt-2 flex items-start gap-1 text-xs text-red-700">
            <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
            Below RBI minimum CRAR ({formatPct(o.minimumCrarRequired, 0)}).
          </p>
        )}
      </CardContent>
    </Card>
  );
}

export default function StressTest(): JSX.Element {
  const { toast } = useToast();
  const runAll = useRunAllStressScenarios();

  const results: ScenarioResult[] = useMemo(() => runAll.data?.results ?? [], [runAll.data]);

  const handleRun = (): void => {
    runAll.mutate(
      {},
      {
        onError: (err) => showErrorToast(err, toast),
      },
    );
  };

  // ----- Three required UI states (CLAUDE.md §5.7) ------------------------
  // - Loading:  SkeletonTable while the mutation is pending on first run.
  // - Empty:    EmptyState with CTA when no run has happened yet.
  // - Error:    ErrorState if the run fails.

  return (
    <div className="space-y-6">
      <PageHeader
        title="Stress Testing"
        subtitle="Parametric impact of rate / credit / combined shocks on CRAR, NII, and provisioning"
        breadcrumbs={[{ label: 'Treasury', to: '/admin/treasury' }, { label: 'Stress Testing' }]}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="ghost" asChild>
              <Link to="/admin/treasury">
                <ArrowLeft className="mr-2 h-4 w-4" /> Back to Treasury
              </Link>
            </Button>
            <Button onClick={handleRun} disabled={runAll.isPending}>
              {runAll.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden />
              ) : (
                <Play className="mr-2 h-4 w-4" aria-hidden />
              )}
              {runAll.isPending ? 'Running…' : 'Run Stress Test'}
            </Button>
          </div>
        }
      />

      {/* Loading — first run, no data yet */}
      {runAll.isPending && !runAll.data && (
        <Card>
          <CardContent className="py-6">
            <SkeletonTable rows={4} columns={6} />
          </CardContent>
        </Card>
      )}

      {/* Error */}
      {runAll.isError && !runAll.isPending && (
        <ErrorState title="Stress test failed" error={runAll.error} onRetry={handleRun} />
      )}

      {/* Empty — never run */}
      {!runAll.isPending && !runAll.isError && results.length === 0 && (
        <Card>
          <CardContent className="py-12">
            <EmptyState
              icon={AlertTriangle}
              title="No stress test results yet"
              subtitle="Run the four standard scenarios (±200 bps rate shock, +5% NPA migration, and a combined macro shock) to see the impact on CRAR, NII, and provisioning."
              action={
                <Button onClick={handleRun} disabled={runAll.isPending}>
                  {runAll.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden />
                  ) : (
                    <Play className="mr-2 h-4 w-4" aria-hidden />
                  )}
                  Run Stress Test
                </Button>
              }
            />
          </CardContent>
        </Card>
      )}

      {/* Success — results */}
      {results.length > 0 && !runAll.isPending && (
        <>
          {/* Per-scenario status cards */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            {results.map((r) => (
              <ResultCard key={r.scenarioId} result={r} />
            ))}
          </div>

          {/* Detail comparison table */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-semibold">Scenario detail</CardTitle>
              <p className="mt-1 text-xs text-muted-foreground">
                As of {runAll.data?.asOfDate ?? 'today'} · provisioning rates from{' '}
                <code className="rounded bg-muted px-1 py-0.5 text-xs">
                  {results[0]?.inputs.provisioningRateSource ?? '—'}
                </code>
              </p>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Scenario</TableHead>
                    <TableHead className="text-right">Pre-CRAR</TableHead>
                    <TableHead className="text-right">Post-CRAR</TableHead>
                    <TableHead className="text-right">Δ CRAR</TableHead>
                    <TableHead className="text-right">NII Impact</TableHead>
                    <TableHead className="text-right">Provision Impact</TableHead>
                    <TableHead className="text-right">Pre-NPA</TableHead>
                    <TableHead className="text-right">Post-NPA</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {results.map((r) => (
                    <TableRow key={r.scenarioId}>
                      <TableCell className="font-medium">{r.name}</TableCell>
                      <TableCell className="text-right tabular-nums">
                        {formatPct(r.outputs.preStressCrar)}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {formatPct(r.outputs.postStressCrar)}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {formatBps(r.outputs.crarDeltaBps)}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        <AmountDisplay amount={toNumber(r.outputs.niiImpact)} compact />
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        <AmountDisplay amount={toNumber(r.outputs.provisionImpact)} compact />
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {formatPct(r.outputs.preStressNpaRatio)}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {formatPct(r.outputs.postStressNpaRatio)}
                      </TableCell>
                      <TableCell>
                        <StressStatusPill status={r.status} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
