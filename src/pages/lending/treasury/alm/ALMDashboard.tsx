/**
 * ALM Dashboard
 *
 * Data source: GET /lending/treasury/summary (camelCase via Pydantic CamelSchema).
 * Returns ALMSummary with gap_analysis if a snapshot has been generated.
 */

import { Download, RefreshCw, TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts';

import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { Badge } from '@/components/ui/badge';
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
import { useTreasurySummary } from '@/hooks/lending/useTreasurySummary';

export default function ALMDashboard() {
  const navigate = useNavigate();
  const { data, isLoading, isError, error, refetch, isFetching } = useTreasurySummary();
  const alm = data?.almSummary;

  // Coerce string Decimal → number for charts and math (display only).
  const buckets = (alm?.gapAnalysis ?? []).map((b) => ({
    bucket: b.bucket,
    assets: Number(b.assets),
    liabilities: Number(b.liabilities),
    gap: Number(b.gap),
    cumulativeGap: Number(b.cumulativeGap),
    gapPercent: Number(b.gapPercent),
  }));

  const totalAssets = Number(alm?.totalAssets ?? 0);
  const totalLiabilities = Number(alm?.totalLiabilities ?? 0);
  const netGap = Number(alm?.netPosition ?? 0);
  const shortTermGap = buckets.slice(0, 4).reduce((sum, b) => sum + b.gap, 0);

  const gapChartData = buckets.map((b) => ({
    name: b.bucket,
    assets: b.assets / 1e7, // → Cr
    liabilities: b.liabilities / 1e7,
    gap: b.gap / 1e7,
  }));
  const cumulativeChartData = buckets.map((b) => ({
    name: b.bucket,
    cumulativeGap: b.cumulativeGap / 1e7,
  }));

  return (
    <div className="space-y-6">
      <PageHeader
        title="ALM Dashboard"
        subtitle="Asset Liability Management – Structural Liquidity & Interest Rate Sensitivity"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => refetch()} disabled={isFetching}>
              <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export ALM-1
            </Button>
          </div>
        }
      />

      {isError && (
        <ErrorState title="Could not load ALM summary" error={error} onRetry={() => refetch()} />
      )}

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Assets</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <>
                <AmountDisplay
                  amount={alm?.totalAssets ?? 0}
                  abbreviated
                  className="text-2xl font-bold"
                />
                <p className="text-xs text-muted-foreground">Loans & advances</p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Liabilities</CardTitle>
            <TrendingDown className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <>
                <AmountDisplay
                  amount={alm?.totalLiabilities ?? 0}
                  abbreviated
                  className="text-2xl font-bold"
                />
                <p className="text-xs text-muted-foreground">Borrowings & NCDs</p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Short-term Gap</CardTitle>
            {!isLoading &&
              (shortTermGap >= 0 ? (
                <Badge variant="default" className="bg-green-100 text-green-700">
                  Surplus
                </Badge>
              ) : (
                <Badge variant="destructive">Deficit</Badge>
              ))}
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <>
                <AmountDisplay
                  amount={Math.abs(shortTermGap)}
                  abbreviated
                  className={`text-2xl font-bold ${
                    shortTermGap >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                />
                <p className="text-xs text-muted-foreground">First 4 buckets</p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Net Position</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <>
                <AmountDisplay
                  amount={Math.abs(netGap)}
                  abbreviated
                  className={`text-2xl font-bold ${
                    netGap >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                />
                <p className="text-xs text-muted-foreground">
                  Assets − Liabilities
                  {alm?.positionDate && (
                    <>
                      {' '}
                      · As of <DateDisplay date={alm.positionDate} format="short" />
                    </>
                  )}
                </p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Empty state when no snapshot exists */}
      {!isLoading && !alm && (
        <Card>
          <CardContent className="py-12">
            <EmptyState
              title="No ALM snapshot generated"
              subtitle="Generate an ALM snapshot to see structural liquidity gap analysis across RBI time buckets."
              icon={AlertTriangle}
              action={
                <Button variant="outline" onClick={() => navigate('/admin/treasury/alm/gap')}>
                  Open Gap Analysis
                </Button>
              }
            />
          </CardContent>
        </Card>
      )}

      {alm && buckets.length > 0 && (
        <>
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Assets vs Liabilities by Bucket</CardTitle>
                <CardDescription>RBI time-bucket structural liquidity (in ₹ Cr)</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={gapChartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="assets" name="Assets" fill="#22c55e" />
                      <Bar dataKey="liabilities" name="Liabilities" fill="#f59e0b" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Cumulative Gap</CardTitle>
                <CardDescription>Running gap across buckets (in ₹ Cr)</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={cumulativeChartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                      <YAxis />
                      <Tooltip />
                      <Line
                        type="monotone"
                        dataKey="cumulativeGap"
                        name="Cumulative Gap"
                        stroke="#3b82f6"
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Time-Bucket Detail</CardTitle>
              <CardDescription>RBI structural liquidity statement (ALM-1 buckets)</CardDescription>
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
                    <TableHead className="text-right">Gap %</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {buckets.map((b) => (
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
                      <TableCell className="text-right">{b.gapPercent.toFixed(2)}%</TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="border-t-2 font-semibold">
                    <TableCell>Total</TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={totalAssets} abbreviated />
                    </TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={totalLiabilities} abbreviated />
                    </TableCell>
                    <TableCell
                      className={`text-right ${netGap >= 0 ? 'text-green-600' : 'text-red-600'}`}
                    >
                      <AmountDisplay amount={Math.abs(netGap)} abbreviated />
                    </TableCell>
                    <TableCell />
                    <TableCell />
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
