import { Edit, Eye, Plus, Trash2 } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AmountDisplay } from '@/components/common/AmountDisplay';
import { DataTable } from '@/components/common/DataTable';
import { DateDisplay } from '@/components/common/DateDisplay';
import { FilterBar } from '@/components/common/FilterBar';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  useDeleteTDSEntry,
  useTDSEntries,
  type TDSEntry,
} from '@/hooks/tax/useTaxation';
import { useActiveOrganizationId } from '@/stores/organizationStore';

export function TDSEntryList() {
  const navigate = useNavigate();
  const activeOrganizationId = useActiveOrganizationId();
  const [challanStatus, setChallanStatus] = useState('all');
  const tdsEntriesQuery = useTDSEntries({
    organizationId: activeOrganizationId ?? undefined,
    challanStatus: challanStatus === 'all' ? undefined : challanStatus,
    pageSize: 100,
  });
  const deleteEntry = useDeleteTDSEntry();

  const columns = useMemo(
    () => [
      { key: 'deducteeName', header: 'Deductee', sortable: true },
      {
        key: 'deducteePan',
        header: 'PAN',
        render: (entry: TDSEntry) =>
          entry.deducteePan ? <span className="font-mono text-sm">{entry.deducteePan}</span> : '—',
      },
      { key: 'tdsSectionCode', header: 'Section' },
      {
        key: 'deductionDate',
        header: 'Deduction Date',
        render: (entry: TDSEntry) => <DateDisplay date={entry.deductionDate} />,
      },
      {
        key: 'baseAmount',
        header: 'Base Amount',
        align: 'right' as const,
        render: (entry: TDSEntry) => <AmountDisplay amount={entry.baseAmount} />,
      },
      {
        key: 'totalTds',
        header: 'Total TDS',
        align: 'right' as const,
        render: (entry: TDSEntry) => <AmountDisplay amount={entry.totalTds} />,
      },
      {
        key: 'challanStatus',
        header: 'Challan Status',
        render: (entry: TDSEntry) => <Badge variant="outline">{entry.challanStatus}</Badge>,
      },
      {
        key: 'returnFiled',
        header: 'Return',
        render: (entry: TDSEntry) => (
          <Badge variant={entry.returnFiled ? 'default' : 'secondary'}>
            {entry.returnFiled ? entry.returnQuarter || 'Filed' : 'Pending'}
          </Badge>
        ),
      },
      {
        key: 'actions',
        header: 'Actions',
        align: 'right' as const,
        render: (entry: TDSEntry) => (
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" size="icon" onClick={(event) => { event.stopPropagation(); navigate(`/admin/tds/entries/${entry.id}`); }}>
              <Eye className="h-4 w-4" />
            </Button>
            <Button type="button" variant="ghost" size="icon" onClick={(event) => { event.stopPropagation(); navigate(`/admin/tds/entries/${entry.id}/edit`); }}>
              <Edit className="h-4 w-4" />
            </Button>
            <Button type="button" variant="ghost" size="icon" disabled={deleteEntry.isPending} onClick={(event) => { event.stopPropagation(); deleteEntry.mutate(entry.id); }}>
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        ),
      },
    ],
    [deleteEntry, navigate],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="TDS Entries"
        subtitle="Capture deductee-level TDS and TCS deductions"
        actions={
          <Button onClick={() => navigate('/admin/tds/entries/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add TDS Entry
          </Button>
        }
      />

      <FilterBar onClear={() => setChallanStatus('all')}>
        <Select value={challanStatus} onValueChange={setChallanStatus}>
          <SelectTrigger className="w-[220px]">
            <SelectValue placeholder="Challan status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All challan statuses</SelectItem>
            <SelectItem value="PENDING">Pending</SelectItem>
            <SelectItem value="PAID">Paid</SelectItem>
            <SelectItem value="VERIFIED">Verified</SelectItem>
            <SelectItem value="NOT_APPLICABLE">Not applicable</SelectItem>
          </SelectContent>
        </Select>
      </FilterBar>

      <DataTable
        data={tdsEntriesQuery.data?.items ?? []}
        columns={columns}
        getRowId={(entry) => entry.id}
        isLoading={tdsEntriesQuery.isLoading}
        error={tdsEntriesQuery.error}
        onRetry={() => tdsEntriesQuery.refetch()}
        emptyTitle="No TDS entries"
        emptySubtitle="Add deductions before challan aggregation and return filing."
        onRowClick={(entry) => navigate(`/admin/tds/entries/${entry.id}`)}
      />
    </div>
  );
}
