import { Eye } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import {
  AmountDisplay,
  DataTable,
  DateDisplay,
  FilterBar,
  PageHeader,
  type Column,
} from '@/components/common';
import { DisposalStatusPill } from '@/components/fixed-assets/DisposalStatusPill';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useDisposals, useTakeDisposalApprovalAction } from '@/hooks/fixed-assets/useDisposals';
import { useToast } from '@/hooks/use-toast';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import { showErrorToast } from '@/lib/errorToast';
import type { DisposalRegisterItem, DisposalRegisterStatus } from '@/types/fixed-assets';

const statusOptions: { value: DisposalRegisterStatus | 'ALL'; label: string }[] = [
  { value: 'ALL', label: 'All statuses' },
  { value: 'PENDING_APPROVAL', label: 'Pending approval' },
  { value: 'COMPLETED', label: 'Completed' },
  { value: 'RETURNED', label: 'Returned' },
  { value: 'REJECTED', label: 'Rejected' },
  { value: 'CANCELLED', label: 'Cancelled' },
];

export function DisposalList(): JSX.Element {
  const organizationId = useRequiredActiveOrganizationId();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState<DisposalRegisterStatus | 'ALL'>('ALL');

  const disposalsQuery = useDisposals(organizationId, {
    search: search.trim() || undefined,
    status: status === 'ALL' ? undefined : status,
    limit: 100,
  });
  const approvalMutation = useTakeDisposalApprovalAction(organizationId);

  const columns: Column<DisposalRegisterItem>[] = useMemo(
    () => [
      {
        key: 'assetCode',
        header: 'Asset',
        render: (row) => (
          <div>
            <div className="font-medium">{row.assetName}</div>
            <div className="text-xs text-muted-foreground">{row.assetCode}</div>
          </div>
        ),
      },
      {
        key: 'requestDate',
        header: 'Raised on',
        render: (row) => <DateDisplay date={row.requestDate ?? row.disposalDate} />,
      },
      {
        key: 'bookValue',
        header: 'Book value',
        align: 'right',
        render: (row) => <AmountDisplay amount={row.bookValue} compact />,
      },
      {
        key: 'disposalValue',
        header: 'Disposal value',
        align: 'right',
        render: (row) => <AmountDisplay amount={row.disposalValue} compact />,
      },
      {
        key: 'status',
        header: 'Status',
        render: (row) => <DisposalStatusPill status={row.status} />,
      },
      {
        key: 'actions',
        header: '',
        align: 'right',
        render: (row) => (
          <div className="flex items-center justify-end gap-2">
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => navigate(`/admin/fixed-assets/assets/${row.assetId}`)}
            >
              <Eye className="mr-2 h-4 w-4" />
              Asset
            </Button>
            {row.approvalRequestId && row.status === 'PENDING_APPROVAL' && (
              <>
                <Button
                  type="button"
                  size="sm"
                  onClick={async () => {
                    try {
                      await approvalMutation.mutateAsync({
                        requestId: row.approvalRequestId!,
                        payload: { action: 'APPROVE' },
                      });
                      toast({ title: 'Disposal approved' });
                    } catch (error) {
                      showErrorToast(error, toast);
                    }
                  }}
                >
                  Approve
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="text-red-600 hover:text-red-700"
                  onClick={async () => {
                    try {
                      await approvalMutation.mutateAsync({
                        requestId: row.approvalRequestId!,
                        payload: { action: 'REJECT', comments: 'Rejected from disposal register' },
                      });
                      toast({ title: 'Disposal rejected' });
                    } catch (error) {
                      showErrorToast(error, toast);
                    }
                  }}
                >
                  Reject
                </Button>
              </>
            )}
          </div>
        ),
      },
    ],
    [approvalMutation, navigate, toast],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Disposal & Write-off"
        subtitle="Monitor manual disposals, routed approvals, and completed write-offs from one register."
        breadcrumbs={[{ label: 'Fixed Assets' }, { label: 'Disposal & Write-off' }]}
      />

      <FilterBar
        search={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search by asset code, name, or request number"
        onClear={() => {
          setSearch('');
          setStatus('ALL');
        }}
      >
        <Select value={status} onValueChange={(value) => setStatus(value as DisposalRegisterStatus | 'ALL')}>
          <SelectTrigger className="w-[220px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {statusOptions.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </FilterBar>

      <DataTable
        data={disposalsQuery.data?.items ?? []}
        columns={columns}
        getRowId={(row) => `${row.assetId}-${row.status}-${row.requestDate ?? row.disposalDate ?? 'none'}`}
        isLoading={disposalsQuery.isLoading}
        error={disposalsQuery.error}
        onRetry={() => disposalsQuery.refetch()}
        emptyTitle="No disposal activity found"
        emptySubtitle="Start a disposal from an asset detail page to populate this register."
      />
    </div>
  );
}
