/**
 * LendingPipelineDashboard — TAT-by-stage + drop-off + NPA + AUM ribbons.
 *
 * One-page snapshot using the new /reports/lending/* endpoints landed in
 * Phase E.3.
 */

import { useQuery } from '@tanstack/react-query';
import { AlertCircle, BarChart3, Clock, Layers, TrendingDown, Wallet } from 'lucide-react';
import { useMemo } from 'react';

import { AmountDisplay, ErrorState, PageHeader, SkeletonTable } from '@/components/common';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import api from '@/services/api';

function isoDaysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}

function isoToday(): string {
  return new Date().toISOString().slice(0, 10);
}

async function fetchOne<T>(path: string): Promise<T> {
  const { data } = await api.get<T>(path);
  return data;
}

interface AumResponse {
  asOfDate: string;
  activeLoanCount: number;
  totalPrincipalOutstanding: number;
  totalSanctioned: number;
}
interface NpaMovement {
  asOfDate: string;
  byBucket: { assetClassification: string; count: number; principalOutstanding: number }[];
  totalCount: number;
  totalOutstanding: number;
}
interface ProvSummary {
  asOfDate: string;
  totalProvision: number;
  byClassification: { classification: string; outstanding: number; provision: number }[];
}
interface TatReport {
  averagesDays: Record<string, number | null>;
  sampleSize: Record<string, number>;
}
interface DocReleaseWatch {
  totalCount: number;
  totalCompensationPayable: number;
  items: {
    trackerId: string;
    loanAccountId: string;
    closureDate: string;
    targetReleaseDate: string;
    status: string;
    breachDays: number;
    compensationPayable: number;
  }[];
}

export default function LendingPipelineDashboard(): JSX.Element {
  const from30 = useMemo(() => isoDaysAgo(30), []);
  const today = useMemo(() => isoToday(), []);

  const aumQ = useQuery<AumResponse>({
    queryKey: ['report', 'aum'],
    queryFn: () => fetchOne('/lending/reports/lending/aum'),
    staleTime: 60_000,
  });
  const npaQ = useQuery<NpaMovement>({
    queryKey: ['report', 'npa-movement'],
    queryFn: () => fetchOne(`/lending/reports/lending/npa-movement?as_of_date=${today}`),
    staleTime: 60_000,
  });
  const provQ = useQuery<ProvSummary>({
    queryKey: ['report', 'provisioning'],
    queryFn: () => fetchOne('/lending/reports/lending/provisioning-summary'),
    staleTime: 60_000,
  });
  const tatQ = useQuery<TatReport>({
    queryKey: ['report', 'tat'],
    queryFn: () =>
      fetchOne(`/lending/reports/lending/tat-by-stage?period_from=${from30}&period_to=${today}`),
    staleTime: 60_000,
  });
  const docWatchQ = useQuery<DocReleaseWatch>({
    queryKey: ['report', 'doc-release-watch'],
    queryFn: () => fetchOne('/lending/reports/lending/doc-release-breach-watch'),
    staleTime: 60_000,
  });

  const anyLoading =
    aumQ.isLoading || npaQ.isLoading || provQ.isLoading || tatQ.isLoading || docWatchQ.isLoading;

  if (anyLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Lending dashboard"
          subtitle="Live snapshot from the lifecycle event log"
          breadcrumbs={[{ label: 'Lending', to: '/admin/lending' }, { label: 'Dashboard' }]}
        />
        <SkeletonTable rows={4} columns={2} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Lending dashboard"
        subtitle="Live snapshot from the lifecycle event log"
        breadcrumbs={[{ label: 'Lending', to: '/admin/lending' }, { label: 'Dashboard' }]}
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Wallet className="h-4 w-4" />
              AUM (active)
            </div>
            <div className="mt-2 text-2xl font-semibold">
              <AmountDisplay amount={aumQ.data?.totalPrincipalOutstanding ?? 0} />
            </div>
            <div className="text-xs text-muted-foreground">
              {aumQ.data?.activeLoanCount ?? 0} active loans
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <AlertCircle className="h-4 w-4" />
              NPA outstanding
            </div>
            <div className="mt-2 text-2xl font-semibold">
              <AmountDisplay
                amount={
                  npaQ.data?.byBucket
                    ?.filter((b) =>
                      ['SUBSTANDARD', 'DOUBTFUL_1', 'DOUBTFUL_2', 'DOUBTFUL_3', 'LOSS'].includes(
                        b.assetClassification.toUpperCase(),
                      ),
                    )
                    .reduce((s, b) => s + b.principalOutstanding, 0) ?? 0
                }
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Layers className="h-4 w-4" />
              Total provisioning
            </div>
            <div className="mt-2 text-2xl font-semibold">
              <AmountDisplay amount={provQ.data?.totalProvision ?? 0} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <TrendingDown className="h-4 w-4" />
              Doc-release at risk
            </div>
            <div className="mt-2 text-2xl font-semibold">{docWatchQ.data?.totalCount ?? 0}</div>
            <div className="text-xs text-amber-700">
              Compensation: <AmountDisplay amount={docWatchQ.data?.totalCompensationPayable ?? 0} />
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            NPA by bucket
          </CardTitle>
        </CardHeader>
        <CardContent>
          {npaQ.data?.byBucket?.length ? (
            <table className="w-full text-sm">
              <thead className="text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="py-2 text-left">Classification</th>
                  <th className="py-2 text-right">Count</th>
                  <th className="py-2 text-right">Principal outstanding</th>
                </tr>
              </thead>
              <tbody>
                {npaQ.data.byBucket.map((b) => (
                  <tr key={b.assetClassification} className="border-t">
                    <td className="py-2">{b.assetClassification}</td>
                    <td className="py-2 text-right">{b.count}</td>
                    <td className="py-2 text-right">
                      <AmountDisplay amount={b.principalOutstanding} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-sm text-muted-foreground">No loans to classify yet.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            TAT by stage (last 30 days)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <thead className="text-xs uppercase text-muted-foreground">
              <tr>
                <th className="py-2 text-left">Stage transition</th>
                <th className="py-2 text-right">Avg (days)</th>
                <th className="py-2 text-right">Sample size</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(tatQ.data?.averagesDays ?? {}).map(([key, value]) => (
                <tr key={key} className="border-t">
                  <td className="py-2 font-mono text-xs">{key}</td>
                  <td className="py-2 text-right">
                    {value !== null && value !== undefined ? value.toFixed(1) : '—'}
                  </td>
                  <td className="py-2 text-right">{tatQ.data?.sampleSize?.[key] ?? 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {docWatchQ.data?.items?.length ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-amber-700">
              <AlertCircle className="h-4 w-4" />
              Doc-release breach watch
            </CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-sm">
              <thead className="text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="py-2 text-left">Loan</th>
                  <th className="py-2 text-left">Closed on</th>
                  <th className="py-2 text-left">Release due</th>
                  <th className="py-2 text-right">Breach days</th>
                  <th className="py-2 text-right">Compensation</th>
                  <th className="py-2 text-left">Status</th>
                </tr>
              </thead>
              <tbody>
                {docWatchQ.data.items.slice(0, 20).map((r) => (
                  <tr key={r.trackerId} className="border-t">
                    <td className="py-2 font-mono text-xs">{r.loanAccountId.slice(0, 8)}</td>
                    <td className="py-2">{r.closureDate}</td>
                    <td className="py-2">{r.targetReleaseDate}</td>
                    <td
                      className={`py-2 text-right ${r.breachDays > 0 ? 'font-semibold text-red-600' : ''}`}
                    >
                      {r.breachDays}
                    </td>
                    <td className="py-2 text-right">
                      <AmountDisplay amount={r.compensationPayable} />
                    </td>
                    <td className="py-2">{r.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
