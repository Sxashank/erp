/**
 * NACH Batch Detail Page
 *
 * Fetches batch metadata via /lending/nach/batches/{id}. Per-transaction
 * tabs (success/failure/retry breakdown) require a dedicated transactions
 * endpoint and renderer — those tabs show EmptyState until built.
 */

import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Download, RefreshCw } from 'lucide-react';
import { useParams, useNavigate } from 'react-router-dom';

import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import api from '@/services/api';

interface NachBatchDetailData {
  id: string;
  batchReference: string;
  batchDate: string;
  debitDate: string;
  status: string;
  totalTransactions: number;
  totalAmount: string | number;
  successCount: number;
  failureCount: number;
  pendingCount: number;
  fileName?: string | null;
  fileGeneratedAt?: string | null;
  submittedAt?: string | null;
  responseReceivedAt?: string | null;
  errorMessage?: string | null;
  createdAt: string;
}

export default function NachBatchDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const {
    data: batch,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<NachBatchDetailData>({
    queryKey: ['lending', 'nach', 'batches', id] as const,
    queryFn: async () => {
      const { data } = await api.get<NachBatchDetailData>(`/lending/nach/batches/${id}`);
      return data;
    },
    enabled: !!id,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title="NACH Batch" subtitle="Loading..." />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (isError || !batch) {
    return (
      <div className="space-y-6">
        <PageHeader title="NACH Batch" />
        <ErrorState title="Could not load batch" error={error} onRetry={() => refetch()} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={batch.batchReference}
        subtitle={`Debit date: ${new Date(batch.debitDate).toLocaleDateString('en-IN')} · ${batch.status}`}
        breadcrumbs={[
          { label: 'Lending', to: '/admin/lending' },
          { label: 'NACH', to: '/admin/lending/nach/batches' },
          { label: batch.batchReference },
        ]}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigate('/admin/lending/nach/batches')}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            <Button variant="outline" onClick={() => refetch()}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
            {batch.fileName && (
              <Button variant="outline">
                <Download className="mr-2 h-4 w-4" />
                Download File
              </Button>
            )}
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant="outline">{batch.status.replace('_', ' ')}</Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Transactions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{batch.totalTransactions}</div>
            <p className="mt-1 text-xs text-muted-foreground">
              <AmountDisplay amount={batch.totalAmount} abbreviated />
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Successful</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{batch.successCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Failed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{batch.failureCount}</div>
            {batch.pendingCount > 0 && (
              <p className="mt-1 text-xs text-muted-foreground">{batch.pendingCount} pending</p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Batch Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-4 text-sm md:grid-cols-3">
            <div>
              <dt className="text-muted-foreground">Created</dt>
              <dd className="font-medium">
                <DateDisplay date={batch.createdAt} />
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">File Generated</dt>
              <dd className="font-medium">
                {batch.fileGeneratedAt ? <DateDisplay date={batch.fileGeneratedAt} /> : '—'}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Submitted</dt>
              <dd className="font-medium">
                {batch.submittedAt ? <DateDisplay date={batch.submittedAt} /> : '—'}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Response Received</dt>
              <dd className="font-medium">
                {batch.responseReceivedAt ? <DateDisplay date={batch.responseReceivedAt} /> : '—'}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">File Name</dt>
              <dd className="font-mono text-xs">{batch.fileName ?? '—'}</dd>
            </div>
          </dl>
          {batch.errorMessage && (
            <div className="mt-4 border-t pt-4">
              <p className="text-sm text-red-600">Error: {batch.errorMessage}</p>
            </div>
          )}
        </CardContent>
      </Card>

      <Tabs defaultValue="transactions">
        <TabsList>
          <TabsTrigger value="transactions">Transactions</TabsTrigger>
          <TabsTrigger value="failures">Failures</TabsTrigger>
          <TabsTrigger value="retries">Retries</TabsTrigger>
        </TabsList>
        <TabsContent value="transactions" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Batch Transactions</CardTitle>
              <CardDescription>Per-transaction listing</CardDescription>
            </CardHeader>
            <CardContent>
              <EmptyState
                title="Transaction listing not embedded yet"
                subtitle="Available at /lending/nach/batches/{id}/transactions; embedded view to follow."
              />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="failures" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Failed Transactions</CardTitle>
              <CardDescription>Bounce reasons and return codes</CardDescription>
            </CardHeader>
            <CardContent>
              <EmptyState
                title="Failure breakdown coming"
                subtitle="Use the Retry Queue page for failed transactions awaiting retry."
                action={
                  <Button variant="outline" onClick={() => navigate('/admin/lending/nach/retry')}>
                    Open Retry Queue
                  </Button>
                }
              />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="retries" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Retry Batches</CardTitle>
              <CardDescription>Subsequent retry attempts for this batch</CardDescription>
            </CardHeader>
            <CardContent>
              <EmptyState
                title="Retry history not embedded yet"
                subtitle="The retry queue tracks per-transaction retry attempts."
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
