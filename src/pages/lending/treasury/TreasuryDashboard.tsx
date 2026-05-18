import {
  Building2,
  Wallet,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  BarChart3,
  RefreshCw,
  ArrowRight,
  CreditCard,
  Receipt,
  PieChart,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { useTreasurySummary, type TopExposure } from '@/hooks/lending/useTreasurySummary';

const formatCurrencyAxis = (value: number) => {
  if (Math.abs(value) >= 1e7) return `${(value / 1e7).toFixed(1)}Cr`;
  if (Math.abs(value) >= 1e5) return `${(value / 1e5).toFixed(1)}L`;
  return value.toFixed(0);
};

function exposureLabel(e: TopExposure): string {
  return e.lenderName ?? e.key ?? e.type ?? 'Unknown';
}

// Wire percent fields may arrive as `string` (Decimal) or `number` (free-form
// dict from BE); coerce uniformly.
function exposurePercent(e: TopExposure): number {
  return Number(e.exposurePercent ?? 0);
}

function exposureLimitPercent(e: TopExposure): number {
  return Number(e.limitPercent ?? 100);
}

export default function TreasuryDashboard() {
  const navigate = useNavigate();
  const { data, isLoading, isError, error, refetch, isFetching } = useTreasurySummary();

  const borrowing = data?.borrowingSummary;
  const alm = data?.almSummary;
  const exposure = data?.exposureSummary;

  // Wire amounts are strings (Decimal precision); coerce once for display math.
  const sanctioned = borrowing ? Number(borrowing.totalSanctioned) : 0;
  const outstanding = borrowing ? Number(borrowing.totalOutstanding) : 0;
  const utilizationPercent = sanctioned > 0 ? (outstanding / sanctioned) * 100 : 0;
  const netPositionNum = alm ? Number(alm.netPosition) : 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Treasury Dashboard"
        subtitle="Borrowings, ALM & Liquidity Management"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => refetch()} disabled={isFetching}>
              <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button onClick={() => navigate('/admin/treasury/borrowings/new')}>
              <Wallet className="mr-2 h-4 w-4" />
              New Borrowing
            </Button>
          </div>
        }
      />

      {isError && (
        <ErrorState
          title="Could not load treasury summary"
          error={error}
          onRetry={() => refetch()}
        />
      )}

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sanctioned</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <>
                <AmountDisplay
                  amount={borrowing?.totalSanctioned ?? 0}
                  abbreviated
                  className="text-2xl font-bold"
                />
                <p className="text-xs text-muted-foreground">
                  {borrowing?.activeBorrowings ?? 0} active facilities
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Outstanding</CardTitle>
            <TrendingDown className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <>
                <AmountDisplay
                  amount={borrowing?.totalOutstanding ?? 0}
                  abbreviated
                  className="text-2xl font-bold text-amber-600"
                />
                <div className="mt-1 flex items-center gap-2">
                  <Progress value={utilizationPercent} className="h-2" />
                  <span className="text-xs text-muted-foreground">
                    <PercentageDisplay value={utilizationPercent} />
                  </span>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Weighted Avg Rate</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <>
                <div className="text-2xl font-bold">
                  {borrowing?.weightedAvgRate != null ? (
                    <>
                      <PercentageDisplay value={borrowing.weightedAvgRate} /> p.a.
                    </>
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">Cost of borrowing</p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Available Limit</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <>
                <AmountDisplay
                  amount={borrowing?.totalAvailable ?? 0}
                  abbreviated
                  className="text-2xl font-bold text-green-600"
                />
                <p className="text-xs text-muted-foreground">Undrawn facilities</p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ALM Position */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>ALM Position</CardTitle>
            <CardDescription>
              {alm ? (
                <>
                  As of <DateDisplay date={alm.positionDate} />
                </>
              ) : (
                'No ALM snapshot yet'
              )}
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={() => navigate('/admin/treasury/alm')}>
            View Details <ArrowRight className="ml-1 h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-[300px] w-full" />
          ) : alm ? (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="rounded-lg border p-3">
                  <p className="text-xs text-muted-foreground">Total Assets</p>
                  <AmountDisplay
                    amount={alm.totalAssets}
                    abbreviated
                    className="text-lg font-bold"
                  />
                </div>
                <div className="rounded-lg border p-3">
                  <p className="text-xs text-muted-foreground">Total Liabilities</p>
                  <AmountDisplay
                    amount={alm.totalLiabilities}
                    abbreviated
                    className="text-lg font-bold"
                  />
                </div>
                <div className="rounded-lg border p-3">
                  <p className="text-xs text-muted-foreground">Net Position</p>
                  <AmountDisplay
                    amount={alm.netPosition}
                    abbreviated
                    className={`text-lg font-bold ${
                      netPositionNum >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}
                  />
                </div>
              </div>
              {alm.gapAnalysis.length > 0 && (
                <div className="h-[260px]">
                  <ResponsiveContainer width="100%" height="100%">
                    {/* Coerce string gap/assets/liabilities to numbers for Recharts. */}
                    <BarChart
                      data={alm.gapAnalysis.map((g) => ({
                        bucket: g.bucket,
                        gap: Number(g.gap),
                        assets: Number(g.assets),
                        liabilities: Number(g.liabilities),
                        cumulativeGap: Number(g.cumulativeGap),
                        gapPercent: Number(g.gapPercent),
                      }))}
                      layout="vertical"
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        type="number"
                        tick={{ fontSize: 10 }}
                        tickFormatter={formatCurrencyAxis}
                      />
                      <YAxis dataKey="bucket" type="category" tick={{ fontSize: 10 }} width={100} />
                      <Tooltip
                        formatter={(value: number | undefined) =>
                          `₹ ${formatCurrencyAxis(value ?? 0)}`
                        }
                      />
                      <Bar dataKey="gap" name="Gap" fill="#3b82f6" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          ) : (
            <EmptyState
              title="No ALM position generated"
              subtitle="Generate an ALM snapshot to see asset / liability gap analysis."
              icon={PieChart}
              action={
                <Button variant="outline" size="sm" onClick={() => navigate('/admin/treasury/alm')}>
                  Open ALM module
                </Button>
              }
            />
          )}
        </CardContent>
      </Card>

      {/* Exposure Concentration */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Exposure Concentration</CardTitle>
            <CardDescription>Lender / counterparty limit utilisation</CardDescription>
          </div>
          {exposure && exposure.breachCount > 0 && (
            <Badge variant="destructive">
              <AlertTriangle className="mr-1 h-3 w-3" />
              {exposure.breachCount} Breach
              {exposure.breachCount > 1 ? 'es' : ''}
            </Badge>
          )}
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-[200px] w-full" />
          ) : exposure && exposure.topExposures.length > 0 ? (
            <div className="space-y-4">
              {exposure.topExposures.slice(0, 5).map((e, index) => (
                <div key={index} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="max-w-[300px] truncate font-medium">{exposureLabel(e)}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground">
                        <PercentageDisplay value={exposurePercent(e)} /> / {exposureLimitPercent(e)}
                        %
                      </span>
                      {e.status && (
                        <Badge
                          variant="outline"
                          className={
                            e.status === 'WITHIN_LIMIT'
                              ? 'bg-green-50 text-green-700'
                              : e.status === 'NEAR_LIMIT'
                                ? 'bg-amber-50 text-amber-700'
                                : 'bg-red-50 text-red-700'
                          }
                        >
                          {e.status.replace('_', ' ')}
                        </Badge>
                      )}
                    </div>
                  </div>
                  <Progress
                    value={
                      exposureLimitPercent(e) > 0
                        ? (exposurePercent(e) / exposureLimitPercent(e)) * 100
                        : 0
                    }
                    className={`h-2 ${
                      e.status === 'BREACHED' || e.status === 'BREACH' ? '[&>div]:bg-red-500' : ''
                    }`}
                  />
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No exposure limits configured"
              subtitle="Configure single-borrower / group limits to see concentration risk."
            />
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <Button
              variant="outline"
              className="h-auto flex-col py-4"
              onClick={() => navigate('/admin/treasury/lenders')}
            >
              <Building2 className="mb-2 h-6 w-6" />
              <span>Manage Lenders</span>
              <span className="text-xs text-muted-foreground">
                {borrowing?.lenderCount ?? 0} active
              </span>
            </Button>
            <Button
              variant="outline"
              className="h-auto flex-col py-4"
              onClick={() => navigate('/admin/treasury/borrowings')}
            >
              <Wallet className="mb-2 h-6 w-6" />
              <span>All Borrowings</span>
              <span className="text-xs text-muted-foreground">
                {borrowing?.activeBorrowings ?? 0} facilities
              </span>
            </Button>
            <Button
              variant="outline"
              className="h-auto flex-col py-4"
              onClick={() => navigate('/admin/treasury/alm')}
            >
              <BarChart3 className="mb-2 h-6 w-6" />
              <span>ALM Reports</span>
              <span className="text-xs text-muted-foreground">Gap Analysis</span>
            </Button>
            <Button
              variant="outline"
              className="h-auto flex-col py-4"
              onClick={() => navigate('/admin/regulatory/crar')}
            >
              <Receipt className="mb-2 h-6 w-6" />
              <span>Regulatory</span>
              <span className="text-xs text-muted-foreground">CRAR & Returns</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
