import {
  AlertTriangle,
  TrendingUp,
  BarChart3,
  RefreshCw,
  Download,
  ArrowRight,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { useNPAAccounts } from '@/hooks/lending/useNPAAccounts';
import { useNPASummary } from '@/hooks/lending/useNPASummary';

interface BreakdownRow {
  name: string;
  count: number;
  amount: number;
  color: string;
}

export default function NPADashboard() {
  const navigate = useNavigate();
  const { data, isLoading, isError, error, refetch, isFetching } = useNPASummary();
  const { data: npaAccounts } = useNPAAccounts({ pageSize: 5 });

  const totalAmount = Number(data?.totalNpaAmount ?? 0);
  const totalProvision = Number(data?.totalProvisionHeld ?? 0);
  const grossNpaRatio = Number(data?.grossNpaRatio ?? 0);
  const netNpaRatio = Number(data?.netNpaRatio ?? 0);
  const provisionCoverage = Number(data?.provisionCoverageRatio ?? 0);

  // Build breakdown rows from the summary; only include classes with rows.
  const breakdown: BreakdownRow[] = data
    ? [
        {
          name: 'Standard',
          count: data.standardCount,
          amount: Number(data.standardAmount),
          color: '#22c55e',
        },
        { name: 'SMA-0', count: data.sma0Count, amount: Number(data.sma0Amount), color: '#84cc16' },
        { name: 'SMA-1', count: data.sma1Count, amount: Number(data.sma1Amount), color: '#eab308' },
        { name: 'SMA-2', count: data.sma2Count, amount: Number(data.sma2Amount), color: '#f97316' },
        {
          name: 'Substandard',
          count: data.substandardCount,
          amount: Number(data.substandardAmount),
          color: '#ef4444',
        },
        {
          name: 'Doubtful-1',
          count: data.doubtful1Count,
          amount: Number(data.doubtful1Amount),
          color: '#dc2626',
        },
        {
          name: 'Doubtful-2',
          count: data.doubtful2Count,
          amount: Number(data.doubtful2Amount),
          color: '#b91c1c',
        },
        {
          name: 'Doubtful-3',
          count: data.doubtful3Count,
          amount: Number(data.doubtful3Amount),
          color: '#991b1b',
        },
        { name: 'Loss', count: data.lossCount, amount: Number(data.lossAmount), color: '#7f1d1d' },
      ].filter((r) => r.count > 0)
    : [];

  const breakdownTotal = breakdown.reduce((s, r) => s + r.amount, 0) || 1;

  return (
    <div className="space-y-6">
      <PageHeader
        title="NPA Dashboard"
        subtitle="Non-Performing Asset monitoring and classification"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => refetch()} disabled={isFetching}>
              <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button variant="outline" onClick={() => navigate('/admin/lending/collections/npa')}>
              <Download className="mr-2 h-4 w-4" />
              View Full List
            </Button>
          </div>
        }
      />

      {isError && (
        <ErrorState title="Could not load NPA summary" error={error} onRetry={() => refetch()} />
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Gross NPA Ratio
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <>
                <span className="text-3xl font-bold">
                  <PercentageDisplay value={data?.grossNpaRatio ?? '0'} />
                </span>
                <p className="mt-1 text-xs text-muted-foreground">RBI definition</p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Net NPA Ratio
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <>
                <span className="text-3xl font-bold">
                  <PercentageDisplay value={data?.netNpaRatio ?? '0'} />
                </span>
                <p className="mt-1 text-xs text-muted-foreground">After provisions</p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Provision Coverage
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-3xl font-bold">
                    <PercentageDisplay value={data?.provisionCoverageRatio ?? '0'} />
                  </span>
                </div>
                <Progress value={provisionCoverage} className="mt-2" />
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">NPA Count</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <>
                <div className="flex items-baseline justify-between">
                  <span className="text-3xl font-bold">{data?.totalNpaAccounts ?? 0}</span>
                  <span className="text-sm text-muted-foreground">accounts</span>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Amount: <AmountDisplay amount={totalAmount} abbreviated />
                </p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Asset Classification</CardTitle>
            <CardDescription>Portfolio distribution by classification</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-80 w-full" />
            ) : breakdown.length === 0 ? (
              <EmptyState
                title="No active loans yet"
                subtitle="Classification breakdown will populate once loans are disbursed."
              />
            ) : (
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={breakdown as unknown as Record<string, unknown>[]}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={2}
                      dataKey="amount"
                      label={({ name, percent }) =>
                        `${name}: ${((percent ?? 0) * 100).toFixed(1)}%`
                      }
                    >
                      {breakdown.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value: number | undefined) => [`₹ ${value ?? 0}`, 'Amount']}
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent NPA Accounts</CardTitle>
            <CardDescription>5 most-recent NPA-classified loans</CardDescription>
          </CardHeader>
          <CardContent>
            {!npaAccounts?.items?.length ? (
              <EmptyState
                title="No NPA accounts"
                subtitle="Accounts will appear here as classifications change."
              />
            ) : (
              <div className="space-y-3">
                {npaAccounts.items.slice(0, 5).map((account) => (
                  <div
                    key={account.id}
                    className="flex cursor-pointer items-center justify-between rounded-lg border p-3 hover:bg-muted/50"
                    onClick={() => navigate(`/admin/lending/accounts/${account.loanAccountId}`)}
                  >
                    <div>
                      <div className="font-mono text-sm font-medium">
                        {account.loanAccountNumber}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {account.entityName ?? '—'}
                      </div>
                    </div>
                    <div className="text-right">
                      <AmountDisplay
                        amount={account.totalOutstanding}
                        abbreviated
                        className="font-medium"
                      />
                      <div className="mt-1 flex items-center justify-end gap-1 text-xs">
                        <Badge variant="destructive">{account.classification}</Badge>
                      </div>
                    </div>
                  </div>
                ))}
                <Button
                  variant="ghost"
                  className="w-full"
                  onClick={() => navigate('/admin/lending/collections/npa')}
                >
                  View all NPA accounts
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Classification Breakdown bar */}
      <Card>
        <CardHeader>
          <CardTitle>Classification Breakdown</CardTitle>
          <CardDescription>Asset bucket sizes</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-40 w-full" />
          ) : breakdown.length === 0 ? (
            <EmptyState
              title="No active loans yet"
              subtitle="Buckets populate once loan accounts are live."
            />
          ) : (
            <div className="space-y-3">
              {breakdown.map((item) => {
                const pct = breakdownTotal > 0 ? (item.amount / breakdownTotal) * 100 : 0;
                return (
                  <div key={item.name} className="flex items-center gap-4">
                    <div className="w-28 text-sm font-medium">{item.name}</div>
                    <div className="flex-1">
                      <Progress value={pct} className="h-4" />
                    </div>
                    <div className="w-20 text-right text-sm">
                      <PercentageDisplay value={pct} />
                    </div>
                    <div className="w-20 text-right text-sm text-muted-foreground">
                      {item.count} loans
                    </div>
                    <div className="w-32 text-right text-sm text-muted-foreground">
                      <AmountDisplay amount={item.amount} abbreviated />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Button
          variant="outline"
          className="flex h-auto flex-col items-center gap-2 py-4"
          onClick={() => navigate('/admin/lending/collections/npa')}
        >
          <BarChart3 className="h-6 w-6" />
          <span>NPA Classification</span>
        </Button>
        <Button
          variant="outline"
          className="flex h-auto flex-col items-center gap-2 py-4"
          onClick={() => navigate('/admin/lending/collections/ots')}
        >
          <AlertTriangle className="h-6 w-6" />
          <span>OTS Proposals</span>
        </Button>
        <Button
          variant="outline"
          className="flex h-auto flex-col items-center gap-2 py-4"
          onClick={() => navigate('/admin/lending/collections/restructure')}
        >
          <TrendingUp className="h-6 w-6" />
          <span>Restructure</span>
        </Button>
        <Button
          variant="outline"
          className="flex h-auto flex-col items-center gap-2 py-4"
          onClick={() => navigate('/admin/lending/collections/legal')}
        >
          <AlertTriangle className="h-6 w-6" />
          <span>Legal Cases</span>
        </Button>
      </div>

      {/* netNpa available for future ratio visualisation; suppress unused-var */}
      {}
      {(() => {
        void netNpaRatio;
        void totalProvision;
        void grossNpaRatio;
        return null;
      })()}
    </div>
  );
}
