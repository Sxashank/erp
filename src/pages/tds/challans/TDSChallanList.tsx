import { Edit, Eye, Plus } from 'lucide-react';
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
import { useFinancialYears, useTDSChallans, type TDSChallan } from '@/hooks/tax/useTaxation';
import { useActiveOrganizationId } from '@/stores/organizationStore';

export default function TDSChallanList() {
  const navigate = useNavigate();
  const activeOrganizationId = useActiveOrganizationId();
  const [status, setStatus] = useState('all');
  const [financialYearId, setFinancialYearId] = useState('all');
  const financialYearsQuery = useFinancialYears(activeOrganizationId ?? undefined);
  const challansQuery = useTDSChallans({
    organizationId: activeOrganizationId ?? undefined,
    status: status === 'all' ? undefined : status,
    financialYearId: financialYearId === 'all' ? undefined : financialYearId,
    pageSize: 100,
  });

  const columns = useMemo(
    () => [
      { key: 'tdsSectionCode', header: 'Section', sortable: true },
      { key: 'assessmentYear', header: 'Assessment Year', sortable: true },
      {
        key: 'periodFrom',
        header: 'Period',
        render: (item: TDSChallan) => (
          <span>
            <DateDisplay date={item.periodFrom} /> - <DateDisplay date={item.periodTo} />
          </span>
        ),
      },
      {
        key: 'totalAmount',
        header: 'Total Amount',
        align: 'right' as const,
        render: (item: TDSChallan) => <AmountDisplay amount={item.totalAmount} />,
      },
      { key: 'entryCount', header: 'Entries', align: 'right' as const },
      { key: 'challanNumber', header: 'Challan No.' },
      {
        key: 'status',
        header: 'Status',
        render: (item: TDSChallan) => <Badge variant="outline">{item.status}</Badge>,
      },
      {
        key: 'actions',
        header: 'Actions',
        align: 'right' as const,
        render: (item: TDSChallan) => (
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" size="icon" onClick={(event) => { event.stopPropagation(); navigate(`/admin/tds/challans/${item.id}`); }}>
              <Eye className="h-4 w-4" />
            </Button>
            <Button type="button" variant="ghost" size="icon" onClick={(event) => { event.stopPropagation(); navigate(`/admin/tds/challans/${item.id}/edit`); }}>
              <Edit className="h-4 w-4" />
            </Button>
          </div>
        ),
      },
    ],
    [navigate],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="TDS Challans"
        subtitle="Aggregate deductions into payment challans and capture OLTAS verification"
        actions={<Button onClick={() => navigate('/admin/tds/challans/create')}><Plus className="mr-2 h-4 w-4" />Create Challan</Button>}
      />

      <FilterBar onClear={() => { setStatus('all'); setFinancialYearId('all'); }}>
        <Select value={financialYearId} onValueChange={setFinancialYearId}>
          <SelectTrigger className="w-[200px]"><SelectValue placeholder="Financial year" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All financial years</SelectItem>
            {(financialYearsQuery.data?.items ?? []).map((year) => <SelectItem key={year.id} value={year.id}>{year.name}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger className="w-[180px]"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="DRAFT">Draft</SelectItem>
            <SelectItem value="PENDING">Pending</SelectItem>
            <SelectItem value="PAID">Paid</SelectItem>
            <SelectItem value="VERIFIED">Verified</SelectItem>
            <SelectItem value="CANCELLED">Cancelled</SelectItem>
          </SelectContent>
        </Select>
      </FilterBar>

      <DataTable
        data={challansQuery.data?.items ?? []}
        columns={columns}
        getRowId={(item) => item.id}
        isLoading={challansQuery.isLoading}
        error={challansQuery.error}
        onRetry={() => challansQuery.refetch()}
        emptyTitle="No TDS challans"
        emptySubtitle="Create a challan workspace once you have eligible deduction entries."
        onRowClick={(item) => navigate(`/admin/tds/challans/${item.id}`)}
      />
    </div>
  );
}
