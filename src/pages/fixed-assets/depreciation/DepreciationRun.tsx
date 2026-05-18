import { Eye, Play } from 'lucide-react';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import {
  AmountDisplay,
  DataTable,
  DateDisplay,
  PageHeader,
  type Column,
} from '@/components/common';
import { DepreciationRunStatusPill } from '@/components/fixed-assets/DepreciationRunStatusPill';
import { Button } from '@/components/ui/button';
import { useDepreciationRuns, useSubmitDepreciationPosting } from '@/hooks/fixed-assets/useDepreciation';
import { useToast } from '@/hooks/use-toast';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import { showErrorToast } from '@/lib/errorToast';
import type { DepreciationRun } from '@/types/fixed-assets';

export function DepreciationRunPage(): JSX.Element {
  const organizationId = useRequiredActiveOrganizationId();
  const navigate = useNavigate();
  const { toast } = useToast();
  const runsQuery = useDepreciationRuns(organizationId, 0, 100);
  const runs = runsQuery.data?.items ?? [];

  const columns: Column<DepreciationRun>[] = useMemo(
    () => [
      {
        key: 'depreciationPeriod',
        header: 'Period',
        render: (row) => row.depreciationPeriod,
        sortable: true,
        sortValue: (row) => row.depreciationPeriod,
      },
      {
        key: 'totalAssets',
        header: 'Assets',
        align: 'right',
        render: (row) => row.totalAssets.toLocaleString('en-IN'),
        sortable: true,
        sortValue: (row) => row.totalAssets,
      },
      {
        key: 'processedAssets',
        header: 'Processed',
        align: 'right',
        render: (row) => row.processedAssets.toLocaleString('en-IN'),
        sortable: true,
        sortValue: (row) => row.processedAssets,
      },
      {
        key: 'totalDepreciation',
        header: 'Depreciation',
        align: 'right',
        render: (row) => <AmountDisplay amount={row.totalDepreciation} compact />,
        sortable: true,
        sortValue: (row) => Number(row.totalDepreciation),
      },
      {
        key: 'status',
        header: 'Status',
        render: (row) => <DepreciationRunStatusPill status={row.status} />,
      },
      {
        key: 'postedAt',
        header: 'Posted at',
        render: (row) => <DateDisplay date={row.postedAt ?? row.runCompletedAt ?? row.runStartedAt} />,
        sortable: true,
        sortValue: (row) => row.postedAt ?? row.runCompletedAt ?? row.runStartedAt ?? '',
      },
      {
        key: 'actions',
        header: '',
        align: 'right',
        render: (row) => <RunActions organizationId={organizationId} row={row} onView={() => navigate(`/admin/fixed-assets/depreciation/runs/${row.id}`)} onToast={toast} />,
      },
    ],
    [navigate, organizationId, toast],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Depreciation Runs"
        subtitle="Run, submit, and monitor monthly depreciation postings for the active organization."
        breadcrumbs={[{ label: 'Fixed Assets' }, { label: 'Depreciation Runs' }]}
        actions={
          <Button onClick={() => navigate('/admin/fixed-assets/depreciation/run')}>
            <Play className="mr-2 h-4 w-4" />
            Run depreciation
          </Button>
        }
      />

      <DataTable
        data={runs}
        columns={columns}
        getRowId={(row) => row.id}
        isLoading={runsQuery.isLoading}
        error={runsQuery.error}
        onRetry={() => runsQuery.refetch()}
        emptyTitle="No depreciation runs found"
        emptySubtitle="Run the first monthly depreciation cycle after capitalizing assets."
      />
    </div>
  );
}

function RunActions({
  organizationId,
  row,
  onView,
  onToast,
}: {
  organizationId: string;
  row: DepreciationRun;
  onView: () => void;
  onToast: ReturnType<typeof useToast>['toast'];
}): JSX.Element {
  const submitMutation = useSubmitDepreciationPosting(organizationId, row.id);

  return (
    <div className="flex items-center justify-end gap-2">
      <Button type="button" size="sm" variant="outline" onClick={onView}>
        <Eye className="mr-2 h-4 w-4" />
        View
      </Button>
      {row.status === 'COMPLETED' && (
        <Button
          type="button"
          size="sm"
          onClick={async () => {
            try {
              const result = await submitMutation.mutateAsync();
              onToast({
                title:
                  result.mode === 'posted'
                    ? 'Depreciation posted to GL'
                    : `Depreciation submitted for approval (${result.approvalRequestNumber})`,
              });
            } catch (error) {
              showErrorToast(error, onToast);
            }
          }}
        >
          Post / Submit
        </Button>
      )}
    </div>
  );
}
