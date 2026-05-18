import { Edit, Plus, Trash2 } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import {
  AmountDisplay,
  DataTable,
  FilterBar,
  PageHeader,
  type Column,
} from '@/components/common';
import { Button } from '@/components/ui/button';
import { useAssetCategories, useDeleteAssetCategory } from '@/hooks/fixed-assets/useAssetCategories';
import { useToast } from '@/hooks/use-toast';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import { showErrorToast } from '@/lib/errorToast';
import type { AssetCategory } from '@/types/fixed-assets';

export function AssetCategoryList(): JSX.Element {
  const organizationId = useRequiredActiveOrganizationId();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [search, setSearch] = useState('');

  const categoriesQuery = useAssetCategories(organizationId);
  const deleteMutation = useDeleteAssetCategory(organizationId);

  const categories = categoriesQuery.data?.items ?? [];
  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return categories;
    return categories.filter((category) =>
      [category.categoryCode, category.categoryName, category.parentCategoryName]
        .filter(Boolean)
        .some((value) => value!.toLowerCase().includes(query)),
    );
  }, [categories, search]);

  const columns: Column<AssetCategory>[] = useMemo(
    () => [
      {
        key: 'categoryCode',
        header: 'Category',
        render: (row) => (
          <div>
            <div className="font-medium">{row.categoryName}</div>
            <div className="text-xs text-muted-foreground">{row.categoryCode}</div>
          </div>
        ),
        sortable: true,
        sortValue: (row) => row.categoryCode,
      },
      {
        key: 'parentCategoryName',
        header: 'Parent',
        render: (row) => row.parentCategoryName ?? 'Root category',
      },
      {
        key: 'assetType',
        header: 'Asset type',
        render: (row) => row.assetType.replace(/_/g, ' '),
        sortable: true,
        sortValue: (row) => row.assetType,
      },
      {
        key: 'depreciationMethod',
        header: 'Depreciation',
        render: (row) => (
          <div>
            <div className="font-medium">{row.depreciationMethod.replace(/_/g, ' ')}</div>
            <div className="text-xs text-muted-foreground">
              Life {row.usefulLifeYears} years
            </div>
          </div>
        ),
      },
      {
        key: 'capitalizationThreshold',
        header: 'Threshold',
        align: 'right',
        render: (row) => <AmountDisplay amount={row.capitalizationThreshold} compact />,
        sortable: true,
        sortValue: (row) => Number(row.capitalizationThreshold),
      },
      {
        key: 'assetCount',
        header: 'Assets',
        align: 'right',
        render: (row) => row.assetCount.toLocaleString('en-IN'),
        sortable: true,
        sortValue: (row) => row.assetCount,
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
              onClick={() => navigate(`/admin/fixed-assets/categories/${row.id}/edit`)}
            >
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="text-red-600 hover:text-red-700"
              onClick={async () => {
                if (!window.confirm(`Delete category ${row.categoryCode}?`)) return;
                try {
                  await deleteMutation.mutateAsync(row.id);
                  toast({ title: 'Asset category deleted' });
                } catch (error) {
                  showErrorToast(error, toast);
                }
              }}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </Button>
          </div>
        ),
      },
    ],
    [deleteMutation, navigate, toast],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Asset Categories"
        subtitle="Define capitalization thresholds, depreciation defaults, and GL mapping for fixed assets."
        breadcrumbs={[{ label: 'Fixed Assets' }, { label: 'Asset Categories' }]}
        actions={
          <Button onClick={() => navigate('/admin/fixed-assets/categories/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New category
          </Button>
        }
      />

      <FilterBar
        search={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search by category code, name, or parent"
        onClear={() => setSearch('')}
      />

      <DataTable
        data={filtered}
        columns={columns}
        getRowId={(row) => row.id}
        isLoading={categoriesQuery.isLoading}
        error={categoriesQuery.error}
        onRetry={() => categoriesQuery.refetch()}
        emptyTitle="No asset categories found"
        emptySubtitle="Create a category to start classifying and capitalizing fixed assets."
      />
    </div>
  );
}
