/**
 * ALM Gap Analysis Page
 *
 * Data source: GET /lending/treasury/summary (CamelSchema, Decimal-as-string).
 */

import {
  Download,
  RefreshCw,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Loader2,
} from 'lucide-react';
import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useTreasurySummary } from '@/hooks/lending/useTreasurySummary';

export default function GapAnalysis() {
  const navigate = useNavigate();
  const [view, setView] = useState<'absolute' | 'cumulative'>('absolute');
  const { data, isLoading, isError, error, refetch, isFetching } = useTreasurySummary();
  const alm = data?.almSummary;

  const buckets = useMemo(
    () =>
      (alm?.gapAnalysis ?? []).map((b) => ({
        bucket: b.bucket,
        assets: Number(b.assets),
        liabilities: Number(b.liabilities),
        gap: Number(b.gap),
        cumulativeGap: Number(b.cumulativeGap),
        gapPercent: Number(b.gapPercent),
      })),
    [alm],
  );

  const totalAssets = Number(alm?.totalAssets ?? 0);
  const totalLiabilities = Number(alm?.totalLiabilities ?? 0);
  const netPosition = Number(alm?.netPosition ?? 0);
  const cumulative1Year = Number(alm?.cumulativeGap1Year ?? 0);
  const cumulativeGapPercent = Number(alm?.cumulativeGapPercent ?? 0);

  // RBI threshold: short-term cumulative gap > 20% of liabilities is a breach.
  const shortTermBuckets = buckets.slice(0, 4);
  const shortTermAssets = shortTermBuckets.reduce((s, b) => s + b.assets, 0);
  const shortTermLiabilities = shortTermBuckets.reduce((s, b) => s + b.liabilities, 0);
  const shortTermGapPct =
    shortTermLiabilities > 0
      ? ((shortTermAssets - shortTermLiabilities) / shortTermLiabilities) * 100
      : 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="ALM Gap Analysis"
        subtitle="Structural liquidity gap across RBI time-buckets"
        breadcrumbs={[
          { label: 'Treasury', to: '/admin/treasury' },
          { label: 'ALM', to: '/admin/treasury/alm' },
          { label: 'Gap Analysis' },
        ]}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => refetch()} disabled={isFetching}>
              <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
          </div>
        }
      />

      {isError && (
        <ErrorState title="Could not load gap analysis" error={error} onRetry={() => refetch()} />
      )}

      {isLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : !alm ? (
        <Card>
          <CardContent className="py-12">
            <EmptyState
              title="No ALM snapshot generated"
              subtitle="Generate an ALM snapshot to view structural liquidity gap by bucket."
              icon={BarChart3}
              action={
                <Button variant="outline" onClick={() => navigate('/admin/treasury/alm')}>
                  Open ALM Dashboard
                </Button>
              }
            />
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Breach alert */}
          {Math.abs(shortTermGapPct) > 20 && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Short-term liquidity gap exceeds RBI threshold</AlertTitle>
              <AlertDescription>
                Cumulative gap in the first 4 buckets is {shortTermGapPct.toFixed(2)}% of
                liabilities — RBI guidance flags &gt;20% as material.
              </AlertDescription>
            </Alert>
          )}

          {/* Summary */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Total Assets
                </CardTitle>
              </CardHeader>
              <CardContent>
                <AmountDisplay amount={totalAssets} abbreviated className="text-2xl font-bold" />
                <TrendingUp className="mt-1 h-4 w-4 text-green-500" />
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Total Liabilities
                </CardTitle>
              </CardHeader>
              <CardContent>
                <AmountDisplay
                  amount={totalLiabilities}
                  abbreviated
                  className="text-2xl font-bold"
                />
                <TrendingDown className="mt-1 h-4 w-4 text-amber-500" />
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Net Position
                </CardTitle>
              </CardHeader>
              <CardContent>
                <AmountDisplay
                  amount={Math.abs(netPosition)}
                  abbreviated
                  className={`text-2xl font-bold ${
                    netPosition >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                />
                <p className="mt-1 text-xs text-muted-foreground">
                  As of <DateDisplay date={alm.positionDate} format="short" />
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  1-Year Cumulative Gap
                </CardTitle>
              </CardHeader>
              <CardContent>
                <AmountDisplay
                  amount={Math.abs(cumulative1Year)}
                  abbreviated
                  className={`text-2xl font-bold ${
                    cumulative1Year >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                />
                <p className="mt-1 text-xs text-muted-foreground">
                  {cumulativeGapPercent.toFixed(2)}% of liabilities
                </p>
              </CardContent>
            </Card>
          </div>

          {/* View toggle + table */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Bucket-wise Gap</CardTitle>
                <CardDescription>
                  {view === 'absolute' ? 'Per-bucket' : 'Cumulative'} gap
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Button
                  variant={view === 'absolute' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setView('absolute')}
                >
                  Per-bucket
                </Button>
                <Button
                  variant={view === 'cumulative' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setView('cumulative')}
                >
                  Cumulative
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Bucket</TableHead>
                    <TableHead className="text-right">Assets</TableHead>
                    <TableHead className="text-right">Liabilities</TableHead>
                    <TableHead className="text-right">Gap</TableHead>
                    <TableHead className="text-right">Cumulative Gap</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Gap %</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {buckets.map((b) => {
                    const gap = view === 'absolute' ? b.gap : b.cumulativeGap;
                    const isSurplus = gap >= 0;
                    return (
                      <TableRow key={b.bucket}>
                        <TableCell className="font-medium">{b.bucket}</TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={b.assets} abbreviated />
                        </TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={b.liabilities} abbreviated />
                        </TableCell>
                        <TableCell
                          className={`text-right font-medium ${
                            b.gap >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}
                        >
                          <AmountDisplay amount={Math.abs(b.gap)} abbreviated />
                          {b.gap < 0 ? ' (D)' : ''}
                        </TableCell>
                        <TableCell
                          className={`text-right font-medium ${
                            b.cumulativeGap >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}
                        >
                          <AmountDisplay amount={Math.abs(b.cumulativeGap)} abbreviated />
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={
                              isSurplus ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                            }
                          >
                            {isSurplus ? 'Surplus' : 'Deficit'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">{b.gapPercent.toFixed(2)}%</TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Bucket utilisation visualization */}
          <Card>
            <CardHeader>
              <CardTitle>Bucket Utilisation</CardTitle>
              <CardDescription>Asset coverage of liabilities by bucket</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {buckets.map((b) => {
                  const coverage = b.liabilities > 0 ? (b.assets / b.liabilities) * 100 : 100;
                  return (
                    <div key={b.bucket} className="flex items-center gap-4">
                      <div className="w-24 text-sm font-medium">{b.bucket}</div>
                      <div className="flex-1">
                        <Progress value={Math.min(coverage, 200)} className="h-3" />
                      </div>
                      <div className="w-20 text-right text-sm">{coverage.toFixed(0)}%</div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Suppress unused */}
      {isLoading ? <Loader2 className="hidden" /> : null}
    </div>
  );
}
