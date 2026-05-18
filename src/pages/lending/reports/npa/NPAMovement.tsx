/**
 * NPA Movement Report
 *
 * Surfaces live NPA distribution + provision via the NPA summary endpoint.
 * Monthly opening→closing movement requires a time-series aggregator
 * (not yet built); that section shows an EmptyState.
 */

import { Download, RefreshCw, TrendingUp, AlertTriangle } from 'lucide-react';

import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useNPASummary } from '@/hooks/lending/useNPASummary';

interface Row {
  label: string;
  count: number;
  amount: string;
  color: string;
}

export default function NPAMovement() {
  const { data, isLoading, isError, error, refetch, isFetching } = useNPASummary();

  const buckets: Row[] = data
    ? [
        { label: 'SMA-0', count: data.sma0Count, amount: data.sma0Amount, color: 'text-amber-600' },
        {
          label: 'SMA-1',
          count: data.sma1Count,
          amount: data.sma1Amount,
          color: 'text-orange-600',
        },
        {
          label: 'SMA-2',
          count: data.sma2Count,
          amount: data.sma2Amount,
          color: 'text-orange-700',
        },
        {
          label: 'Substandard',
          count: data.substandardCount,
          amount: data.substandardAmount,
          color: 'text-red-600',
        },
        {
          label: 'Doubtful-1',
          count: data.doubtful1Count,
          amount: data.doubtful1Amount,
          color: 'text-red-700',
        },
        {
          label: 'Doubtful-2',
          count: data.doubtful2Count,
          amount: data.doubtful2Amount,
          color: 'text-red-800',
        },
        {
          label: 'Doubtful-3',
          count: data.doubtful3Count,
          amount: data.doubtful3Amount,
          color: 'text-red-900',
        },
        { label: 'Loss', count: data.lossCount, amount: data.lossAmount, color: 'text-red-950' },
      ]
    : [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="NPA Movement"
        subtitle="Asset classification distribution and provisioning snapshot"
        breadcrumbs={[
          { label: 'Reports', to: '/admin/lending/reports' },
          { label: 'NPA' },
          { label: 'Movement' },
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
        <ErrorState title="Could not load NPA movement" error={error} onRetry={() => refetch()} />
      )}

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total NPA</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <div className="text-2xl font-bold">{data?.totalNpaAccounts ?? 0}</div>
            )}
            <p className="mt-1 text-xs text-muted-foreground">Non-performing accounts</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">NPA Amount</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <AmountDisplay
                amount={data?.totalNpaAmount ?? 0}
                abbreviated
                className="text-2xl font-bold text-red-600"
              />
            )}
            <p className="mt-1 text-xs text-muted-foreground">Outstanding</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Provision Held
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <AmountDisplay
                amount={data?.totalProvisionHeld ?? 0}
                abbreviated
                className="text-2xl font-bold"
              />
            )}
            <p className="mt-1 text-xs text-muted-foreground">As per IRAC</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Coverage Ratio
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold">
                <PercentageDisplay value={data?.provisionCoverageRatio ?? '0'} />
              </div>
            )}
            <p className="mt-1 text-xs text-muted-foreground">PCR</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Distribution by Classification</CardTitle>
          <CardDescription>SMA + NPA buckets with current outstanding</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6">
              <Skeleton className="h-40 w-full" />
            </div>
          ) : buckets.every((b) => b.count === 0) ? (
            <div className="p-6">
              <EmptyState
                title="No NPA / SMA accounts"
                subtitle="Distribution populates as classifications change."
                icon={TrendingUp}
              />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Bucket</TableHead>
                  <TableHead className="text-right">Accounts</TableHead>
                  <TableHead className="text-right">Outstanding</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {buckets.map((row) => (
                  <TableRow key={row.label}>
                    <TableCell className={`font-medium ${row.color}`}>{row.label}</TableCell>
                    <TableCell className="text-right">{row.count}</TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={row.amount} abbreviated />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Monthly Movement</CardTitle>
          <CardDescription>Opening → Additions → Recoveries → Closing</CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState
            title="Time-series movement not yet wired"
            subtitle="Monthly opening/addition/recovery/closing requires a separate aggregator endpoint that groups NPA events by period. Coming soon."
            icon={AlertTriangle}
          />
        </CardContent>
      </Card>
    </div>
  );
}
