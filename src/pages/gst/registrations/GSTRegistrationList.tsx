import { Edit, Eye, Plus, Trash2 } from 'lucide-react';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { DataTable } from '@/components/common/DataTable';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  useDeleteGSTRegistration,
  useGSTRegistrations,
  type GSTRegistration,
} from '@/hooks/tax/useTaxation';
import { useActiveOrganizationId } from '@/stores/organizationStore';

export function GSTRegistrationList() {
  const navigate = useNavigate();
  const activeOrganizationId = useActiveOrganizationId();
  const registrationsQuery = useGSTRegistrations({
    organizationId: activeOrganizationId ?? undefined,
    pageSize: 100,
    includeInactive: true,
  });
  const deleteRegistration = useDeleteGSTRegistration();

  const columns = useMemo(
    () => [
      {
        key: 'gstin',
        header: 'GSTIN',
        render: (registration: GSTRegistration) => (
          <span className="font-mono text-sm">{registration.gstin}</span>
        ),
      },
      { key: 'legalName', header: 'Legal Name', sortable: true },
      { key: 'tradeName', header: 'Trade Name' },
      { key: 'registrationType', header: 'Type', sortable: true },
      {
        key: 'state',
        header: 'State',
        render: (registration: GSTRegistration) => `${registration.stateCode} · ${registration.stateName}`,
      },
      {
        key: 'flags',
        header: 'Features',
        render: (registration: GSTRegistration) => (
          <div className="flex flex-wrap gap-2">
            {registration.isEInvoiceEnabled && <Badge variant="outline">E-Invoice</Badge>}
            {registration.isEWayBillEnabled && <Badge variant="outline">E-Way Bill</Badge>}
          </div>
        ),
      },
      {
        key: 'status',
        header: 'Status',
        render: (registration: GSTRegistration) => (
          <Badge variant={registration.isActive ? 'default' : 'secondary'}>
            {registration.isActive ? 'Active' : 'Inactive'}
          </Badge>
        ),
      },
      {
        key: 'actions',
        header: 'Actions',
        align: 'right' as const,
        render: (registration: GSTRegistration) => (
          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={(event) => {
                event.stopPropagation();
                navigate(`/admin/gst/registrations/${registration.id}`);
              }}
              aria-label={`View ${registration.gstin}`}
            >
              <Eye className="h-4 w-4" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={(event) => {
                event.stopPropagation();
                navigate(`/admin/gst/registrations/${registration.id}/edit`);
              }}
              aria-label={`Edit ${registration.gstin}`}
            >
              <Edit className="h-4 w-4" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              disabled={deleteRegistration.isPending}
              onClick={(event) => {
                event.stopPropagation();
                deleteRegistration.mutate(registration.id);
              }}
              aria-label={`Delete ${registration.gstin}`}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        ),
      },
    ],
    [deleteRegistration, navigate],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="GST Registrations"
        subtitle="Maintain GSTIN registrations used for invoicing, filing, and reconciliation"
        actions={
          <Button onClick={() => navigate('/admin/gst/registrations/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add GST Registration
          </Button>
        }
      />

      <DataTable
        data={registrationsQuery.data?.items ?? []}
        columns={columns}
        getRowId={(registration) => registration.id}
        isLoading={registrationsQuery.isLoading}
        error={registrationsQuery.error}
        onRetry={() => registrationsQuery.refetch()}
        emptyTitle="No GST registrations"
        emptySubtitle="Add at least one GST registration before working on GSTN flows."
        onRowClick={(registration) => navigate(`/admin/gst/registrations/${registration.id}`)}
      />
    </div>
  );
}
