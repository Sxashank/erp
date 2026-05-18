/**
 * IIF Fund Utilization Categories — list page.
 *
 * Master data filtered by scheme. CLAUDE.md §9.2 / §9.3.
 */

import { Edit, Eye, Plus } from 'lucide-react';
import { useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { DataTable, type Column } from '@/components/common/DataTable';
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
import { useSubventionSchemes, useUtilizationCategories } from '@/hooks/lending/useIif';
import type { FundUtilizationCategory } from '@/services/lending/iifApi';

const ALL_SCHEMES = 'ALL';

export default function CategoryList(): JSX.Element {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const schemeId = searchParams.get('schemeId') ?? ALL_SCHEMES;

  const { data: schemesData } = useSubventionSchemes();
  const schemes = schemesData?.items ?? [];

  const filterParams = useMemo(
    () => (schemeId === ALL_SCHEMES ? undefined : { schemeId }),
    [schemeId],
  );

  const { data, isLoading, error, refetch } = useUtilizationCategories(filterParams);
  const items = data?.items ?? [];

  const handleSchemeChange = (value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value === ALL_SCHEMES) {
      next.delete('schemeId');
    } else {
      next.set('schemeId', value);
    }
    setSearchParams(next);
  };

  const columns: Column<FundUtilizationCategory>[] = [
    {
      key: 'sortOrder',
      header: '#',
      align: 'right',
      width: '60px',
      sortable: true,
    },
    {
      key: 'code',
      header: 'Code',
      sortable: true,
      render: (row) => <span className="font-mono text-sm">{row.code}</span>,
    },
    {
      key: 'label',
      header: 'Label',
      sortable: true,
    },
    {
      key: 'description',
      header: 'Description',
      render: (row) => row.description ?? '—',
    },
    {
      key: 'isActive',
      header: 'Status',
      render: (row) => (
        <Badge variant={row.isActive ? 'default' : 'secondary'}>
          {row.isActive ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: '',
      align: 'right',
      render: (row) => (
        <div className="flex justify-end gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/admin/lending/iif/categories/${row.id}`);
            }}
            aria-label="View category"
          >
            <Eye className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/admin/lending/iif/categories/${row.id}`);
            }}
            aria-label="Edit category"
          >
            <Edit className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Fund Utilization Categories"
        subtitle="Buckets that loan applicants split their requested amount across (e.g. Land acquisition, Civil works)."
        breadcrumbs={[
          { label: 'Lending', to: '/admin/lending' },
          { label: 'Interest Subvention' },
          { label: 'Categories' },
        ]}
        actions={
          <Button onClick={() => navigate('/admin/lending/iif/categories/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Category
          </Button>
        }
      />

      <FilterBar>
        <div className="w-full max-w-xs">
          <Select value={schemeId} onValueChange={handleSchemeChange}>
            <SelectTrigger>
              <SelectValue placeholder="Filter by scheme" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL_SCHEMES}>All schemes</SelectItem>
              {schemes.map((s) => (
                <SelectItem key={s.id} value={s.id}>
                  {s.schemeCode} — {s.schemeName}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </FilterBar>

      <DataTable<FundUtilizationCategory>
        data={items}
        columns={columns}
        getRowId={(r) => r.id}
        isLoading={isLoading}
        error={error}
        onRetry={refetch}
        emptyTitle="No categories"
        emptySubtitle="Add a category to let applicants split their loan amount."
        emptyAction={
          <Button onClick={() => navigate('/admin/lending/iif/categories/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Category
          </Button>
        }
      />
    </div>
  );
}
