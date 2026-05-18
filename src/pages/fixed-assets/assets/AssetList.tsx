import { Edit, Eye, Plus, Trash2 } from 'lucide-react';
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
import { FixedAssetStatusPill } from '@/components/fixed-assets/FixedAssetStatusPill';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useAssetCategories } from '@/hooks/fixed-assets/useAssetCategories';
import { useDeleteFixedAsset, useFixedAssets } from '@/hooks/fixed-assets/useFixedAssets';
import { useToast } from '@/hooks/use-toast';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import { showErrorToast } from '@/lib/errorToast';
import type { AssetStatus, FixedAsset } from '@/types/fixed-assets';

const statusOptions: { value: AssetStatus | 'ALL'; label: string }[] = [
  { value: 'ALL', label: 'All statuses' },
  { value: 'DRAFT', label: 'Draft' },
  { value: 'ACTIVE', label: 'Active' },
  { value: 'FULLY_DEPRECIATED', label: 'Fully depreciated' },
  { value: 'TRANSFERRED', label: 'Transferred' },
  { value: 'DISPOSED', label: 'Disposed' },
];

export function AssetList(): JSX.Element {
  const organizationId = useRequiredActiveOrganizationId();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [search, setSearch] = useState('');
  const [categoryId, setCategoryId] = useState<string>('ALL');
  const [status, setStatus] = useState<AssetStatus | 'ALL'>('ALL');

  const assetsQuery = useFixedAssets({
    organizationId,
    categoryId: categoryId === 'ALL' ? undefined : categoryId,
    status: status === 'ALL' ? undefined : status,
    search: search.trim() || undefined,
    limit: 100,
  });
  const categoriesQuery = useAssetCategories(organizationId);
  const deleteMutation = useDeleteFixedAsset(organizationId);

  const assets = assetsQuery.data?.items ?? [];
  const totals = useMemo(
    () => ({
      totalCost: assets.reduce((sum, asset) => sum + Number(asset.totalCost), 0),
      totalWdv: assets.reduce((sum, asset) => sum + Number(asset.wdvValue), 0),
      active: assets.filter((asset) => asset.status === 'ACTIVE').length,
      draft: assets.filter((asset) => asset.status === 'DRAFT').length,
    }),
    [assets],
  );

  const columns: Column<FixedAsset>[] = useMemo(
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
        sortable: true,
        sortValue: (row) => row.assetCode,
      },
      {
        key: 'categoryName',
        header: 'Category',
        render: (row) => row.categoryName ?? 'Unmapped',
      },
      {
        key: 'locationName',
        header: 'Location',
        render: (row) => row.locationName ?? 'Not assigned',
      },
      {
        key: 'acquisitionDate',
        header: 'Acquired',
        render: (row) => <DateDisplay date={row.acquisitionDate} />,
        sortable: true,
        sortValue: (row) => row.acquisitionDate,
      },
      {
        key: 'totalCost',
        header: 'Total cost',
        align: 'right',
        render: (row) => <AmountDisplay amount={row.totalCost} compact />,
        sortable: true,
        sortValue: (row) => Number(row.totalCost),
      },
      {
        key: 'wdvValue',
        header: 'WDV',
        align: 'right',
        render: (row) => <AmountDisplay amount={row.wdvValue} compact />,
        sortable: true,
        sortValue: (row) => Number(row.wdvValue),
      },
      {
        key: 'status',
        header: 'Status',
        render: (row) => <FixedAssetStatusPill status={row.status} />,
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
              onClick={() => navigate(`/admin/fixed-assets/assets/${row.id}`)}
            >
              <Eye className="mr-2 h-4 w-4" />
              View
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() =>
                navigate(
                  row.status === 'DRAFT'
                    ? `/admin/fixed-assets/assets/${row.id}/edit`
                    : `/admin/fixed-assets/assets/${row.id}/transfer`,
                )
              }
            >
              <Edit className="mr-2 h-4 w-4" />
              {row.status === 'DRAFT' ? 'Edit' : 'Action'}
            </Button>
            {row.status === 'DRAFT' && (
              <Button
                type="button"
                size="sm"
                variant="outline"
                className="text-red-600 hover:text-red-700"
                onClick={async () => {
                  if (!window.confirm(`Delete asset ${row.assetCode}?`)) return;
                  try {
                    await deleteMutation.mutateAsync(row.id);
                    toast({ title: 'Asset deleted' });
                  } catch (error) {
                    showErrorToast(error, toast);
                  }
                }}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </Button>
            )}
          </div>
        ),
      },
    ],
    [deleteMutation, navigate, toast],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Asset Register"
        subtitle="Track capitalization, depreciation, transfer, impairment, and disposal across the fixed-assets estate."
        breadcrumbs={[{ label: 'Fixed Assets' }, { label: 'Asset Register' }]}
        actions={
          <Button onClick={() => navigate('/admin/fixed-assets/assets/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New asset
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-lg border bg-background p-4">
          <div className="text-xs text-muted-foreground">Assets on screen</div>
          <div className="mt-1 text-2xl font-semibold">{assets.length}</div>
        </div>
        <div className="rounded-lg border bg-background p-4">
          <div className="text-xs text-muted-foreground">Draft assets</div>
          <div className="mt-1 text-2xl font-semibold">{totals.draft}</div>
        </div>
        <div className="rounded-lg border bg-background p-4">
          <div className="text-xs text-muted-foreground">Active assets</div>
          <div className="mt-1 text-2xl font-semibold">{totals.active}</div>
        </div>
        <div className="rounded-lg border bg-background p-4">
          <div className="text-xs text-muted-foreground">Aggregate WDV</div>
          <div className="mt-1 text-2xl font-semibold">
            <AmountDisplay amount={totals.totalWdv} abbreviated />
          </div>
        </div>
      </div>

      <FilterBar
        search={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search by asset code, name, vendor, or invoice"
        onClear={() => {
          setSearch('');
          setCategoryId('ALL');
          setStatus('ALL');
        }}
      >
        <Select value={categoryId} onValueChange={setCategoryId}>
          <SelectTrigger className="w-[220px]">
            <SelectValue placeholder="All categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All categories</SelectItem>
            {(categoriesQuery.data?.items ?? []).map((category) => (
              <SelectItem key={category.id} value={category.id}>
                {category.categoryCode} · {category.categoryName}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={status} onValueChange={(value) => setStatus(value as AssetStatus | 'ALL')}>
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
        data={assets}
        columns={columns}
        getRowId={(row) => row.id}
        isLoading={assetsQuery.isLoading}
        error={assetsQuery.error}
        onRetry={() => assetsQuery.refetch()}
        emptyTitle="No fixed assets found"
        emptySubtitle="Create a draft asset and capitalize it to start running depreciation."
        onRowClick={(row) => navigate(`/admin/fixed-assets/assets/${row.id}`)}
      />
    </div>
  );
}
