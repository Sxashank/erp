import { Edit, Eye, Plus, Trash2 } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { DataTable } from '@/components/common/DataTable';
import { FilterBar } from '@/components/common/FilterBar';
import { PageHeader } from '@/components/common/PageHeader';
import { PercentageDisplay } from '@/components/common/PercentageDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useDeleteHSNSAC, useHSNSAC, type HSNSAC } from '@/hooks/tax/useTaxation';

export function HSNSACList() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [hsnSacType, setHsnSacType] = useState<string>('all');
  const hsnSacQuery = useHSNSAC({
    search,
    hsnSacType: hsnSacType === 'all' ? undefined : hsnSacType,
    pageSize: 100,
  });
  const deleteHsnSac = useDeleteHSNSAC();

  const columns = useMemo(
    () => [
      { key: 'code', header: 'Code', sortable: true },
      { key: 'description', header: 'Description', sortable: true },
      {
        key: 'type',
        header: 'Type',
        render: (item: HSNSAC) => <Badge variant="outline">{item.hsnSacType}</Badge>,
      },
      { key: 'chapter', header: 'Chapter' },
      { key: 'section', header: 'Section' },
      {
        key: 'gstRateValue',
        header: 'GST Rate',
        align: 'right' as const,
        render: (item: HSNSAC) =>
          item.gstRateValue != null ? <PercentageDisplay value={item.gstRateValue} decimals={2} /> : '—',
      },
      { key: 'unitOfMeasurement', header: 'UOM' },
      {
        key: 'status',
        header: 'Status',
        render: (item: HSNSAC) => (
          <Badge variant={item.isActive ? 'default' : 'secondary'}>{item.isActive ? 'Active' : 'Inactive'}</Badge>
        ),
      },
      {
        key: 'actions',
        header: 'Actions',
        align: 'right' as const,
        render: (item: HSNSAC) => (
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" size="icon" onClick={(event) => { event.stopPropagation(); navigate(`/admin/gst/hsn-sac/${item.id}`); }}>
              <Eye className="h-4 w-4" />
            </Button>
            <Button type="button" variant="ghost" size="icon" onClick={(event) => { event.stopPropagation(); navigate(`/admin/gst/hsn-sac/${item.id}/edit`); }}>
              <Edit className="h-4 w-4" />
            </Button>
            <Button type="button" variant="ghost" size="icon" disabled={deleteHsnSac.isPending} onClick={(event) => { event.stopPropagation(); deleteHsnSac.mutate(item.id); }}>
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        ),
      },
    ],
    [deleteHsnSac, navigate],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="HSN / SAC"
        subtitle="Manage tax classification codes mapped to GST rates"
        actions={
          <Button onClick={() => navigate('/admin/gst/hsn-sac/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add HSN / SAC
          </Button>
        }
      />

      <FilterBar search={search} onSearchChange={setSearch} searchPlaceholder="Search code or description" onClear={() => { setSearch(''); setHsnSacType('all'); }}>
        <Select value={hsnSacType} onValueChange={setHsnSacType}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All types</SelectItem>
            <SelectItem value="HSN">HSN</SelectItem>
            <SelectItem value="SAC">SAC</SelectItem>
          </SelectContent>
        </Select>
      </FilterBar>

      <DataTable
        data={hsnSacQuery.data?.items ?? []}
        columns={columns}
        getRowId={(item) => item.id}
        isLoading={hsnSacQuery.isLoading}
        error={hsnSacQuery.error}
        onRetry={() => hsnSacQuery.refetch()}
        emptyTitle="No HSN/SAC codes"
        emptySubtitle="Create classification codes before invoice-level tax automation."
        onRowClick={(item) => navigate(`/admin/gst/hsn-sac/${item.id}`)}
      />
    </div>
  );
}
