/**
 * PortalLoanTimeline — borrower-facing full lifecycle view for one loan.
 *
 * Reads `/portal/loans/{id}/lifecycle` (borrower_visible filter applied
 * server-side) and renders the unified timeline component. Shows
 * application + sanction + disbursement + servicing + closure events on
 * one ribbon.
 */

import { useQuery } from '@tanstack/react-query';
import { ArrowLeft } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';

import { ErrorState, PageHeader, SkeletonTable } from '@/components/common';
import { LifecycleTimeline, type LifecycleEvent } from '@/components/lending/LifecycleTimeline';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import api from '@/services/api';

interface TimelineResponse {
  items: LifecycleEvent[];
  total: number;
}

async function fetchTimeline(loanId: string): Promise<TimelineResponse> {
  const { data } = await api.get<TimelineResponse>(`/portal/loans/${loanId}/lifecycle`);
  return data;
}

export default function PortalLoanTimeline(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  const query = useQuery<TimelineResponse>({
    queryKey: ['portal', 'loan', id, 'lifecycle'],
    queryFn: () => fetchTimeline(id as string),
    enabled: Boolean(id),
    staleTime: 30_000,
  });

  if (query.isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Loan timeline"
          breadcrumbs={[{ label: 'My loans', to: '/portal/loans' }, { label: 'Timeline' }]}
        />
        <SkeletonTable rows={5} columns={1} />
      </div>
    );
  }

  if (query.isError || !query.data) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Loan timeline"
          breadcrumbs={[{ label: 'My loans', to: '/portal/loans' }, { label: 'Timeline' }]}
        />
        <ErrorState
          error={query.error ?? new Error('Could not load timeline')}
          onRetry={() => query.refetch()}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Loan timeline"
        subtitle={`${query.data.total} events`}
        breadcrumbs={[{ label: 'My loans', to: '/portal/loans' }, { label: 'Timeline' }]}
        actions={
          <Button variant="outline" asChild>
            <Link to={`/portal/loans/${id}`}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to loan
            </Link>
          </Button>
        }
      />
      <Card>
        <CardHeader>
          <CardTitle>Complete history</CardTitle>
        </CardHeader>
        <CardContent>
          <LifecycleTimeline
            events={query.data.items}
            emptyText="No events recorded on this loan yet."
          />
        </CardContent>
      </Card>
    </div>
  );
}
