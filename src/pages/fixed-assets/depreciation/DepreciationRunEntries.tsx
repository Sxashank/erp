import { useNavigate, useParams } from 'react-router-dom';

import {
  AmountDisplay,
  DataTable,
  DateDisplay,
  DetailGrid,
  EmptyState,
  ErrorState,
  PageHeader,
} from '@/components/common';
import { DepreciationRunStatusPill } from '@/components/fixed-assets/DepreciationRunStatusPill';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useDepreciationRun, useDepreciationRunEntries, useSubmitDepreciationPosting } from '@/hooks/fixed-assets/useDepreciation';
import { useToast } from '@/hooks/use-toast';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import { showErrorToast } from '@/lib/errorToast';

export function DepreciationRunEntries(): JSX.Element {
  const organizationId = useRequiredActiveOrganizationId();
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const runQuery = useDepreciationRun(runId);
  const entriesQuery = useDepreciationRunEntries(runId);
  const submitMutation = useSubmitDepreciationPosting(organizationId, runId ?? '');

  if (runQuery.isLoading) {
    return <Card><CardContent className="py-12 text-sm text-muted-foreground">Loading depreciation run…</CardContent></Card>;
  }

  if (runQuery.error) {
    return <ErrorState error={runQuery.error} onRetry={() => runQuery.refetch()} />;
  }

  if (!runQuery.data) {
    return (
      <EmptyState
        title="Depreciation run not found"
        subtitle="The requested depreciation run is not available in the current organization."
        action={
          <Button type="button" onClick={() => navigate('/admin/fixed-assets/depreciation')}>
            Back to runs
          </Button>
        }
      />
    );
  }

  const run = runQuery.data;

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Depreciation Run ${run.depreciationPeriod}`}
        subtitle="Review the asset-level postings generated in this monthly run."
        breadcrumbs={[
          { label: 'Fixed Assets' },
          { label: 'Depreciation Runs', to: '/admin/fixed-assets/depreciation' },
          { label: run.depreciationPeriod },
        ]}
        actions={
          run.status === 'COMPLETED' ? (
            <Button
              onClick={async () => {
                try {
                  const result = await submitMutation.mutateAsync();
                  toast({
                    title:
                      result.mode === 'posted'
                        ? 'Depreciation posted to GL'
                        : `Depreciation submitted for approval (${result.approvalRequestNumber})`,
                  });
                  await runQuery.refetch();
                  await entriesQuery.refetch();
                } catch (error) {
                  showErrorToast(error, toast);
                }
              }}
            >
              Post / Submit
            </Button>
          ) : undefined
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>Run Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <DetailGrid
            columns={3}
            fields={[
              { label: 'Status', value: <DepreciationRunStatusPill status={run.status} /> },
              { label: 'Book', value: run.depreciationBook.replace(/_/g, ' ') },
              { label: 'Period', value: run.depreciationPeriod },
              { label: 'Assets', value: run.totalAssets.toLocaleString('en-IN') },
              { label: 'Processed assets', value: run.processedAssets.toLocaleString('en-IN') },
              { label: 'Skipped assets', value: run.skippedAssets.toLocaleString('en-IN') },
              { label: 'Total depreciation', value: <AmountDisplay amount={run.totalDepreciation} /> },
              { label: 'Run started', value: <DateDisplay date={run.runStartedAt} /> },
              { label: 'Posted at', value: <DateDisplay date={run.postedAt} /> },
            ]}
          />
        </CardContent>
      </Card>

      <DataTable
        data={entriesQuery.data?.items ?? []}
        columns={[
          { key: 'assetCode', header: 'Asset code' },
          { key: 'assetName', header: 'Asset name' },
          {
            key: 'openingWdv',
            header: 'Opening WDV',
            align: 'right',
            render: (row) => <AmountDisplay amount={row.openingWdv} compact />,
          },
          {
            key: 'depreciationRate',
            header: 'Rate',
            align: 'right',
            render: (row) => `${Number(row.depreciationRate).toLocaleString('en-IN')}%`,
          },
          {
            key: 'depreciationAmount',
            header: 'Depreciation',
            align: 'right',
            render: (row) => <AmountDisplay amount={row.depreciationAmount} compact />,
          },
          {
            key: 'closingWdv',
            header: 'Closing WDV',
            align: 'right',
            render: (row) => <AmountDisplay amount={row.closingWdv} compact />,
          },
        ]}
        getRowId={(row) => row.id}
        isLoading={entriesQuery.isLoading}
        error={entriesQuery.error}
        onRetry={() => entriesQuery.refetch()}
        emptyTitle="No depreciation entries found"
        emptySubtitle="The run completed without any eligible assets to depreciate."
      />
    </div>
  );
}
