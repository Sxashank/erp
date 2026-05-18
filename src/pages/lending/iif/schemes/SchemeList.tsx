/**
 * IIF Subvention Schemes — list page.
 *
 * Read-only-by-default master. Admins can create/edit/deactivate schemes.
 * See CLAUDE.md §9.2 / §9.3.
 */

import { Edit, Eye, Plus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { DataTable, type Column } from '@/components/common/DataTable';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useSubventionSchemes } from '@/hooks/lending/useIif';
import type { SubventionScheme } from '@/services/lending/iifApi';

export default function SchemeList(): JSX.Element {
  const navigate = useNavigate();
  const { data, isLoading, error, refetch } = useSubventionSchemes();
  const items = data?.items ?? [];

  const columns: Column<SubventionScheme>[] = [
    {
      key: 'schemeCode',
      header: 'Code',
      sortable: true,
      render: (row) => <span className="font-mono text-sm">{row.schemeCode}</span>,
    },
    {
      key: 'schemeName',
      header: 'Scheme Name',
      sortable: true,
    },
    {
      key: 'subventionRatePercent',
      header: 'Rate',
      align: 'right',
      render: (row) => `${row.subventionRatePercent}%`,
    },
    {
      key: 'claimFrequency',
      header: 'Frequency',
      render: (row) => <span className="text-sm">{row.claimFrequency}</span>,
    },
    {
      key: 'administeringMinistry',
      header: 'Ministry',
      render: (row) => row.administeringMinistry ?? '—',
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
              navigate(`/admin/lending/iif/schemes/${row.id}`);
            }}
            aria-label="View scheme"
          >
            <Eye className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/admin/lending/iif/schemes/${row.id}`);
            }}
            aria-label="Edit scheme"
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
        title="Subvention Schemes"
        subtitle="Government interest-subvention programmes available to enrolled loans (e.g. Interest Incentivization Fund)."
        breadcrumbs={[
          { label: 'Lending', to: '/admin/lending' },
          { label: 'Interest Subvention' },
          { label: 'Schemes' },
        ]}
        actions={
          <Button onClick={() => navigate('/admin/lending/iif/schemes/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Scheme
          </Button>
        }
      />

      <DataTable<SubventionScheme>
        data={items}
        columns={columns}
        getRowId={(r) => r.id}
        isLoading={isLoading}
        error={error}
        onRetry={refetch}
        emptyTitle="No schemes configured"
        emptySubtitle="Add a subvention scheme to start enrolling loans."
        emptyAction={
          <Button onClick={() => navigate('/admin/lending/iif/schemes/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Scheme
          </Button>
        }
      />
    </div>
  );
}
