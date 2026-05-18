import { Edit, Plus, Trash2 } from 'lucide-react';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { DataTable } from '@/components/common/DataTable';
import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { PercentageDisplay } from '@/components/common/PercentageDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useDeleteGSTRate, useGSTRates, type GSTRate } from '@/hooks/tax/useTaxation';

export function GSTRateList() {
  const navigate = useNavigate();
  const ratesQuery = useGSTRates({ pageSize: 100, includeInactive: true });
  const deleteRate = useDeleteGSTRate();

  const columns = useMemo(
    () => [
      { key: 'code', header: 'Code', sortable: true },
      { key: 'name', header: 'Name', sortable: true },
      {
        key: 'rate',
        header: 'Total',
        align: 'right' as const,
        render: (rate: GSTRate) => <PercentageDisplay value={rate.rate} decimals={2} />,
      },
      {
        key: 'cgstRate',
        header: 'CGST',
        align: 'right' as const,
        render: (rate: GSTRate) => <PercentageDisplay value={rate.cgstRate} decimals={2} />,
      },
      {
        key: 'sgstRate',
        header: 'SGST',
        align: 'right' as const,
        render: (rate: GSTRate) => <PercentageDisplay value={rate.sgstRate} decimals={2} />,
      },
      {
        key: 'igstRate',
        header: 'IGST',
        align: 'right' as const,
        render: (rate: GSTRate) => <PercentageDisplay value={rate.igstRate} decimals={2} />,
      },
      {
        key: 'cessRate',
        header: 'Cess',
        align: 'right' as const,
        render: (rate: GSTRate) => <PercentageDisplay value={rate.cessRate} decimals={2} />,
      },
      {
        key: 'effectiveFrom',
        header: 'Effective From',
        render: (rate: GSTRate) => <DateDisplay date={rate.effectiveFrom} />,
      },
      {
        key: 'isActive',
        header: 'Status',
        render: (rate: GSTRate) => (
          <Badge variant={rate.isActive ? 'default' : 'secondary'}>
            {rate.isActive ? 'Active' : 'Inactive'}
          </Badge>
        ),
      },
      {
        key: 'actions',
        header: 'Actions',
        align: 'right' as const,
        render: (rate: GSTRate) => (
          <div className="flex justify-end gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={(event) => {
                event.stopPropagation();
                navigate(`/admin/gst/rates/${rate.id}/edit`);
              }}
              aria-label={`Edit ${rate.code}`}
            >
              <Edit className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              disabled={deleteRate.isPending}
              onClick={(event) => {
                event.stopPropagation();
                deleteRate.mutate(rate.id);
              }}
              aria-label={`Delete ${rate.code}`}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        ),
      },
    ],
    [deleteRate, navigate],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="GST Rates"
        subtitle="Manage GST rate configurations by effective date"
        actions={
          <Button onClick={() => navigate('/admin/gst/rates/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add GST Rate
          </Button>
        }
      />

      <DataTable
        data={ratesQuery.data?.items ?? []}
        columns={columns}
        getRowId={(rate) => rate.id}
        isLoading={ratesQuery.isLoading}
        error={ratesQuery.error}
        onRetry={() => ratesQuery.refetch()}
        emptyTitle="No GST rates"
        emptySubtitle="Create a GST rate before assigning HSN/SAC codes or invoices."
      />
    </div>
  );
}
