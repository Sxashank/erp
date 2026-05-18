/**
 * Collection Efficiency Report
 *
 * Surfaces live data from /lending/collections/summary/collection +
 * /summary/recovery. Detailed monthly/branch/product breakdowns require
 * a dedicated reports aggregator endpoint (not yet built) — those panels
 * show EmptyState until the BE endpoint lands.
 */

import { Download, RefreshCw, TrendingUp, AlertTriangle } from 'lucide-react';

import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useCollectionSummary, useRecoverySummary } from '@/hooks/lending/useCollectionSummary';

export default function CollectionEfficiency() {
  const collection = useCollectionSummary();
  const recovery = useRecoverySummary();
  const isLoading = collection.isLoading || recovery.isLoading;
  const isError = collection.isError || recovery.isError;
  const isFetching = collection.isFetching || recovery.isFetching;
  const refetch = () => {
    collection.refetch();
    recovery.refetch();
  };

  const c = collection.data;
  const r = recovery.data;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Collection Efficiency"
        subtitle="Collection performance, overdue ageing, and recovery snapshot"
        breadcrumbs={[
          { label: 'Reports', to: '/admin/lending/reports' },
          { label: 'Collections' },
          { label: 'Efficiency' },
        ]}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={refetch} disabled={isFetching}>
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
        <ErrorState
          title="Could not load collection summary"
          error={collection.error ?? recovery.error}
          onRetry={refetch}
        />
      )}

      {/* Headline metrics */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Collections Today
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <AmountDisplay
                amount={c?.collectionsToday ?? 0}
                abbreviated
                className="text-2xl font-bold text-green-600"
              />
            )}
            <p className="mt-1 text-xs text-muted-foreground">Receipts booked today</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              MTD Collections
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <AmountDisplay
                amount={c?.collectionsMtd ?? 0}
                abbreviated
                className="text-2xl font-bold"
              />
            )}
            <p className="mt-1 text-xs text-muted-foreground">Month-to-date</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Overdue Outstanding
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <>
                <AmountDisplay
                  amount={c?.totalOverdueAmount ?? 0}
                  abbreviated
                  className="text-2xl font-bold text-amber-600"
                />
                <p className="mt-1 text-xs text-muted-foreground">
                  {c?.totalOverdueAccounts ?? 0} accounts
                </p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Pending Follow-ups
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-12" />
            ) : (
              <div className="text-2xl font-bold">{c?.pendingFollowUps ?? 0}</div>
            )}
            <p className="mt-1 text-xs text-muted-foreground">
              {c?.completedFollowUpsToday ?? 0} completed today
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recovery breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Recovery Pipeline</CardTitle>
          <CardDescription>OTS, restructure, legal — current state</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-40 w-full" />
          ) : !r ? (
            <EmptyState
              title="No recovery data"
              subtitle="Recovery breakdown shows once OTS / restructure / legal cases are created."
              icon={TrendingUp}
            />
          ) : (
            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-lg border p-4">
                <p className="text-xs text-muted-foreground">OTS Proposals</p>
                <div className="text-2xl font-bold">{r.totalOtsProposals}</div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Approved: {r.approvedOts} · Completed: {r.completedOts}
                </p>
                <AmountDisplay
                  amount={r.otsSettlementAmount}
                  abbreviated
                  className="mt-2 text-sm font-medium"
                />
              </div>
              <div className="rounded-lg border p-4">
                <p className="text-xs text-muted-foreground">Restructures</p>
                <div className="text-2xl font-bold">{r.totalRestructures}</div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Approved: {r.approvedRestructures} · Implemented: {r.implementedRestructures}
                </p>
              </div>
              <div className="rounded-lg border p-4">
                <p className="text-xs text-muted-foreground">Legal Cases</p>
                <div className="text-2xl font-bold">{r.totalLegalCases}</div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Pending: {r.pendingCases} · Decree: {r.decreeObtained}
                </p>
                <AmountDisplay
                  amount={r.recoveryThroughLegal}
                  abbreviated
                  className="mt-2 text-sm font-medium"
                />
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Detailed breakdowns — pending BE work */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Reports</CardTitle>
          <CardDescription>
            Monthly trend, branch- and product-wise efficiency, ageing buckets
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState
            title="Detailed breakdowns not yet wired"
            subtitle="Monthly trends, branch- and product-wise efficiency, and ageing buckets require a dedicated reports aggregator endpoint that joins receipts to demands and groups by period/branch/product. Coming soon."
            icon={AlertTriangle}
          />
        </CardContent>
      </Card>
    </div>
  );
}
