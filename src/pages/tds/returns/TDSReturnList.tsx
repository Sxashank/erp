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
import { useFinancialYears, useTDSReturns, type TDSReturn } from '@/hooks/tax/useTaxation';
import { useActiveOrganizationId } from '@/stores/organizationStore';

export default function TDSReturnList() {
  const navigate = useNavigate();
  const activeOrganizationId = useActiveOrganizationId();
  const [status, setStatus] = useState('all');
  const [quarter, setQuarter] = useState('all');
  const [financialYearId, setFinancialYearId] = useState('all');
  const financialYearsQuery = useFinancialYears(activeOrganizationId ?? undefined);
  const returnsQuery = useTDSReturns({
    organizationId: activeOrganizationId ?? undefined,
    status: status === 'all' ? undefined : status,
    quarter: quarter === 'all' ? undefined : quarter,
    financialYearId: financialYearId === 'all' ? undefined : financialYearId,
    pageSize: 100,
  });

  const columns = useMemo(
    () => [
      { key: 'returnType', header: 'Return Type', sortable: true },
      { key: 'financialYear', header: 'Financial Year', sortable: true },
      { key: 'quarter', header: 'Quarter' },
      { key: 'deductorTan', header: 'TAN' },
      {
        key: 'dueDate',
        header: 'Due Date',
        render: (item: TDSReturn) => <DateDisplay date={item.dueDate} />,
      },
      {
        key: 'totalTdsDeposited',
        header: 'TDS Deposited',
        align: 'right' as const,
        render: (item: TDSReturn) => <AmountDisplay amount={item.totalTdsDeposited} />,
      },
      {
        key: 'status',
        header: 'Status',
        render: (item: TDSReturn) => <Badge variant="outline">{item.status}</Badge>,
      },
      {
        key: 'actions',
        header: 'Actions',
        align: 'right' as const,
        render: (item: TDSReturn) => (
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" size="icon" onClick={(event) => { event.stopPropagation(); navigate(`/admin/tds/returns/${item.id}`); }}>
              <Eye className="h-4 w-4" />
            </Button>
            <Button type="button" variant="ghost" size="icon" onClick={(event) => { event.stopPropagation(); navigate(`/admin/tds/returns/${item.id}/edit`); }}>
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
        title="TDS Returns"
        subtitle="Prepare, validate, and evidence quarterly TDS/TCS filings"
        actions={<Button onClick={() => navigate('/admin/tds/returns/create')}><Plus className="mr-2 h-4 w-4" />Create Return</Button>}
      />

      <FilterBar onClear={() => { setStatus('all'); setQuarter('all'); setFinancialYearId('all'); }}>
        <Select value={financialYearId} onValueChange={setFinancialYearId}>
          <SelectTrigger className="w-[200px]"><SelectValue placeholder="Financial year" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All financial years</SelectItem>
            {(financialYearsQuery.data?.items ?? []).map((year) => <SelectItem key={year.id} value={year.id}>{year.name}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={quarter} onValueChange={setQuarter}>
          <SelectTrigger className="w-[140px]"><SelectValue placeholder="Quarter" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All quarters</SelectItem>
            <SelectItem value="Q1">Q1</SelectItem>
            <SelectItem value="Q2">Q2</SelectItem>
            <SelectItem value="Q3">Q3</SelectItem>
            <SelectItem value="Q4">Q4</SelectItem>
          </SelectContent>
        </Select>
        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger className="w-[180px]"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="DRAFT">Draft</SelectItem>
            <SelectItem value="VALIDATED">Validated</SelectItem>
            <SelectItem value="GENERATED">Generated</SelectItem>
            <SelectItem value="UPLOADED">Uploaded</SelectItem>
            <SelectItem value="FILED">Filed</SelectItem>
            <SelectItem value="ACCEPTED">Accepted</SelectItem>
          </SelectContent>
        </Select>
      </FilterBar>

      <DataTable
        data={returnsQuery.data?.items ?? []}
        columns={columns}
        getRowId={(item) => item.id}
        isLoading={returnsQuery.isLoading}
        error={returnsQuery.error}
        onRetry={() => returnsQuery.refetch()}
        emptyTitle="No TDS returns"
        emptySubtitle="Create a quarterly return workspace to start validations and filing evidence capture."
        onRowClick={(item) => navigate(`/admin/tds/returns/${item.id}`)}
      />
    </div>
  );
}
