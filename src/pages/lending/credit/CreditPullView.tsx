/**
 * Credit Bureau Pull Detail View
 *
 * Surfaces the headline credit pull record via /lending/credit/pulls/{id}.
 * Detailed report sections (account-wise + enquiry-wise + DPD history)
 * require the bureau-provided report blob to be parsed and displayed;
 * those tabs show EmptyState until the renderer is built.
 */

import { useQuery } from '@tanstack/react-query';
import { Download, RefreshCw, ArrowLeft } from 'lucide-react';
import { useParams, useNavigate } from 'react-router-dom';

import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import api from '@/services/api';

interface CreditPullDetail {
  id: string;
  bureau: string;
  pullType: string;
  status: string;
  customerName: string;
  panNumber?: string | null;
  creditScore?: number | null;
  scoreBand?: string | null;
  pulledAt?: string | null;
  expiresAt?: string | null;
  isValid?: boolean;
  createdAt: string;
}

export default function CreditPullView() {
  const { id } = useParams();
  const navigate = useNavigate();

  const {
    data: pull,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<CreditPullDetail>({
    queryKey: ['lending', 'credit', 'pulls', id] as const,
    queryFn: async () => {
      const { data } = await api.get<CreditPullDetail>(`/lending/credit/pulls/${id}`);
      return data;
    },
    enabled: !!id,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Credit Report" subtitle="Loading..." />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (isError || !pull) {
    return (
      <div className="space-y-6">
        <PageHeader title="Credit Report" />
        <ErrorState title="Could not load credit pull" error={error} onRetry={() => refetch()} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={`${pull.bureau} Credit Report`}
        subtitle={`${pull.customerName}${pull.panNumber ? ` · PAN ${pull.panNumber}` : ''}`}
        breadcrumbs={[
          { label: 'Lending', to: '/admin/lending' },
          { label: 'Credit', to: '/admin/lending/credit' },
          { label: 'Pulls', to: '/admin/lending/credit' },
          { label: pull.bureau },
        ]}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigate('/admin/lending/credit')}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Download PDF
            </Button>
            {pull.status === 'IN_PROGRESS' || pull.status === 'PENDING' ? (
              <Button variant="outline" onClick={() => refetch()}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh Status
              </Button>
            ) : null}
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Bureau</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant="outline" className="font-medium">
              {pull.bureau}
            </Badge>
            <p className="mt-1 text-xs text-muted-foreground">{pull.pullType}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant="outline">{pull.status.replace('_', ' ')}</Badge>
            {pull.isValid && <p className="mt-1 text-xs text-green-600">Valid</p>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Credit Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{pull.creditScore ?? '—'}</div>
            {pull.scoreBand && (
              <p className="mt-1 text-xs text-muted-foreground">{pull.scoreBand}</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Pulled</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm">
              {pull.pulledAt ? <DateDisplay date={pull.pulledAt} /> : '—'}
            </div>
            {pull.expiresAt && (
              <p className="mt-1 text-xs text-muted-foreground">
                Expires <DateDisplay date={pull.expiresAt} />
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="accounts">Accounts</TabsTrigger>
          <TabsTrigger value="enquiries">Enquiries</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Report Details</CardTitle>
              <CardDescription>{pull.bureau} bureau report metadata</CardDescription>
            </CardHeader>
            <CardContent>
              <EmptyState
                title="Full report rendering not yet wired"
                subtitle="The bureau report blob (account-wise tradelines, DPD history, enquiry log) is stored on the credit pull but needs a dedicated renderer."
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="accounts" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Tradelines</CardTitle>
              <CardDescription>Account-wise credit history</CardDescription>
            </CardHeader>
            <CardContent>
              <EmptyState
                title="Account list not yet wired"
                subtitle="Requires parsing the bureau response payload (CIBIL/Experian/etc-specific format)."
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="enquiries" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Enquiries</CardTitle>
            </CardHeader>
            <CardContent>
              <EmptyState
                title="Enquiry list not yet wired"
                subtitle="Requires parsing the bureau response payload."
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
