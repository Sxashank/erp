/**
 * Interest Rate Risk Page
 *
 * Data source: GET /lending/treasury/irs/preview (CamelSchema, Decimal-as-string).
 * Computes RSA / RSL / Gap and projects NII impact under a default set of
 * rate-shock buckets (±50 / ±100 / ±200 bps). Non-persisting — for the
 * dashboard view only; the `generate_irs_analysis` POST persists results.
 */

import { ArrowLeft, Calculator, RefreshCw, TrendingDown, TrendingUp } from 'lucide-react';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useIrsPreview } from '@/hooks/lending/useIrsPreview';

function formatShockLabel(bps: number): string {
  const sign = bps > 0 ? '+' : '';
  return `${sign}${bps} bps`;
}

export default function InterestRateRisk() {
  const navigate = useNavigate();
  const { data, isLoading, isError, error, refetch, isFetching } = useIrsPreview();

  // Coerce string-Decimals to Number only at the chart / arithmetic boundary.
  const rsa = Number(data?.summary.rsa ?? 0);
  const rsl = Number(data?.summary.rsl ?? 0);
  const gap = Number(data?.summary.gap ?? 0);
  const gapToTotalAssetsPct = Number(data?.summary.gapToTotalAssetsPercent ?? 0);

  const shocks = useMemo(
    () =>
      (data?.shocks ?? []).map((s) => ({
        shockBps: s.shockBps,
        label: formatShockLabel(s.shockBps),
        niiImpact: Number(s.niiImpact),
        niiImpactPercent: Number(s.niiImpactPercent),
      })),
    [data],
  );

  const hasData = Boolean(data) && shocks.length > 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Interest Rate Risk"
        subtitle="NII sensitivity to rate shocks and re-pricing gap analysis"
        breadcrumbs={[
          { label: 'Treasury', to: '/admin/treasury' },
          { label: 'ALM', to: '/admin/treasury/alm' },
          { label: 'Interest Rate Risk' },
        ]}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigate('/admin/treasury/alm')}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to ALM
            </Button>
            <Button variant="outline" onClick={() => refetch()} disabled={isFetching}>
              <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        }
      />

      {isError && (
        <ErrorState title="Could not load IRS preview" error={error} onRetry={() => refetch()} />
      )}

      {isLoading ? (
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <Skeleton className="h-28 w-full" />
            <Skeleton className="h-28 w-full" />
            <Skeleton className="h-28 w-full" />
          </div>
          <Skeleton className="h-80 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      ) : !hasData ? (
        !isError && (
          <Card>
            <CardContent className="py-12">
              <EmptyState
                title="No rate-sensitive exposure to analyse"
                subtitle="No active floating-rate loans or borrowings were found. IRS analysis becomes meaningful once floating-rate positions exist on the books."
                icon={Calculator}
                action={
                  <Button variant="outline" onClick={() => navigate('/admin/treasury/alm/gap')}>
                    Open Gap Analysis
                  </Button>
                }
              />
            </CardContent>
          </Card>
        )
      ) : (
        <>
          {/* Summary cards */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Rate-Sensitive Assets
                </CardTitle>
              </CardHeader>
              <CardContent>
                <AmountDisplay amount={rsa} abbreviated className="text-2xl font-bold" />
                <p className="mt-1 text-xs text-muted-foreground">Active floating-rate loans</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Rate-Sensitive Liabilities
                </CardTitle>
              </CardHeader>
              <CardContent>
                <AmountDisplay amount={rsl} abbreviated className="text-2xl font-bold" />
                <p className="mt-1 text-xs text-muted-foreground">
                  Floating / MCLR / repo-linked borrowings
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Rate Sensitivity Gap
                </CardTitle>
              </CardHeader>
              <CardContent>
                <AmountDisplay
                  amount={Math.abs(gap)}
                  abbreviated
                  className={`text-2xl font-bold ${gap >= 0 ? 'text-green-600' : 'text-red-600'}`}
                />
                <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                  {gap >= 0 ? (
                    <TrendingUp className="h-3 w-3 text-green-600" />
                  ) : (
                    <TrendingDown className="h-3 w-3 text-red-600" />
                  )}
                  {gap >= 0 ? 'Asset-sensitive' : 'Liability-sensitive'} (
                  {gapToTotalAssetsPct.toFixed(2)}% of total assets)
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Chart */}
          <Card>
            <CardHeader>
              <CardTitle>NII Impact Across Rate Shocks</CardTitle>
              <CardDescription>
                Projected change in Net Interest Income per shock bucket as of{' '}
                <DateDisplay date={data!.asOfDate} format="short" />. Positive bars indicate NII
                expansion; negative bars indicate NII compression.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={shocks}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                    <YAxis
                      tick={{ fontSize: 12 }}
                      tickFormatter={(v: number) =>
                        new Intl.NumberFormat('en-IN', {
                          notation: 'compact',
                          maximumFractionDigits: 1,
                        }).format(v)
                      }
                    />
                    <Tooltip
                      formatter={(value: number | string | (number | string)[] | undefined) => {
                        const numeric = Array.isArray(value)
                          ? Number(value[0])
                          : Number(value ?? 0);
                        return formatIndianCompactCurrency(numeric);
                      }}
                    />
                    <Bar dataKey="niiImpact" name="NII Impact">
                      {shocks.map((s) => (
                        <Cell key={s.shockBps} fill={s.niiImpact >= 0 ? '#22c55e' : '#ef4444'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Table */}
          <Card>
            <CardHeader>
              <CardTitle>Shock Bucket Detail</CardTitle>
              <CardDescription>
                Per-bucket projected NII impact in ₹ and as % of RSL.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Rate Shock</TableHead>
                    <TableHead className="text-right">NII Impact (₹)</TableHead>
                    <TableHead className="text-right">NII Impact (%)</TableHead>
                    <TableHead>Direction</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {shocks.map((s) => {
                    const isPositive = s.niiImpact >= 0;
                    return (
                      <TableRow key={s.shockBps}>
                        <TableCell className="font-medium">{s.label}</TableCell>
                        <TableCell
                          className={`text-right font-medium ${
                            isPositive ? 'text-green-600' : 'text-red-600'
                          }`}
                        >
                          <AmountDisplay amount={Math.abs(s.niiImpact)} abbreviated />
                          {!isPositive ? ' (–)' : ''}
                        </TableCell>
                        <TableCell
                          className={`text-right font-medium ${
                            isPositive ? 'text-green-600' : 'text-red-600'
                          }`}
                        >
                          {s.niiImpactPercent.toFixed(2)}%
                        </TableCell>
                        <TableCell>
                          <span
                            className={`inline-flex items-center gap-1 text-sm ${
                              isPositive ? 'text-green-700' : 'text-red-700'
                            }`}
                          >
                            {isPositive ? (
                              <TrendingUp className="h-4 w-4" />
                            ) : (
                              <TrendingDown className="h-4 w-4" />
                            )}
                            {isPositive ? 'NII expansion' : 'NII compression'}
                          </span>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
