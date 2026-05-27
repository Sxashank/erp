/**
 * Borrower Portal - Loan Applications list.
 *
 * Shows the borrower's applications scoped to their accessible entities.
 * Uses the canonical `<PageHeader>` + `<DataTable>` shell; status pill via
 * `<StatusPill>`; money via `<AmountDisplay>`; dates via `<DateDisplay>`.
 * Filter bar is rendered inline above the card per §9.3.
 */

import { FileText, Plus } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import {
  AmountDisplay,
  DataTable,
  DateDisplay,
  PageHeader,
  StatusPill,
  type Column,
} from '@/components/common';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useActiveEntity } from '@/hooks/portal/useActiveEntity';
import { usePortalApplications } from '@/hooks/portal/useApplications';
import { usePortalSession } from '@/hooks/portal/usePortalSession';
import type {
  PortalApplication,
  PortalApplicationStatus,
  PortalSchemeApplicationStatus,
} from '@/services/portalApi';

const STATUS_OPTIONS: {
  value: PortalApplicationStatus | PortalSchemeApplicationStatus | 'ALL';
  label: string;
}[] = [
  { value: 'ALL', label: 'All statuses' },
  { value: 'DRAFT', label: 'Draft' },
  { value: 'LENDER_REVIEW', label: 'Pending SFC review' },
  { value: 'LENDER_VALIDATED', label: 'SFC validated' },
  { value: 'SMFCL_PRELIM_REVIEW', label: 'Pending SFC review' },
  { value: 'QUERY_PENDING', label: 'Query pending' },
  { value: 'SMFCL_APPRAISAL', label: 'In appraisal' },
  { value: 'APPROVED', label: 'Approved' },
  { value: 'SANCTION_ISSUED', label: 'Sanction issued' },
  { value: 'REJECTED', label: 'Rejected' },
  { value: 'CLOSED', label: 'Closed' },
];

export default function PortalApplications(): JSX.Element {
  const navigate = useNavigate();
  const { actorRole } = usePortalSession();
  const { entities, activeEntityId } = useActiveEntity();
  const isBorrower = actorRole === 'scheme_borrower';
  const showEntityFilter = isBorrower && entities.length > 1;
  const [entityFilter, setEntityFilter] = useState<string | 'ALL'>('ALL');
  const [statusFilter, setStatusFilter] = useState<
    PortalApplicationStatus | PortalSchemeApplicationStatus | 'ALL'
  >('ALL');

  const effectiveEntityId =
    entityFilter !== 'ALL'
      ? entityFilter
      : showEntityFilter
        ? undefined
        : (activeEntityId ?? undefined);

  const query = usePortalApplications({
    status: statusFilter === 'ALL' ? undefined : statusFilter,
    entityId: effectiveEntityId,
    page: 1,
    pageSize: 50,
  });

  const columns = useMemo<Column<PortalApplication>[]>(() => {
    const cols: Column<PortalApplication>[] = [
      {
        key: 'applicationNumber',
        header: 'Application #',
        render: (row) => <span className="font-medium">{row.applicationNumber}</span>,
        sortable: true,
        sortValue: (r) => r.applicationNumber,
      },
    ];
    if (showEntityFilter) {
      cols.push({
        key: 'entity',
        header: 'Entity',
        render: (r) => r.entityLegalName,
        sortable: true,
        sortValue: (r) => r.entityLegalName,
      });
    }
    cols.push(
      {
        key: 'productName',
        header: 'Product',
        render: (r) => r.productName,
        sortable: true,
        sortValue: (r) => r.productName,
      },
      {
        key: 'requestedAmount',
        header: 'Amount',
        align: 'right',
        render: (r) => <AmountDisplay amount={Number(r.requestedAmount)} />,
        sortable: true,
        sortValue: (r) => Number(r.requestedAmount),
      },
      {
        key: 'schemeStatus',
        header: 'Status',
        render: (r) => <StatusPill type="application" status={r.schemeStatus} />,
        sortable: true,
        sortValue: (r) => r.schemeStatus,
      },
      {
        key: 'submittedAt',
        header: 'Submitted',
        render: (r) => <DateDisplay date={r.submittedAt} />,
        sortable: true,
        sortValue: (r) => r.submittedAt ?? '',
      },
    );
    return cols;
  }, [showEntityFilter]);

  const pageTitle = isBorrower ? 'Loan Applications' : 'Application Review Queue';
  const pageSubtitle = isBorrower
    ? 'Track institutional maritime and shipyard applications across borrower entities.'
    : 'Review submitted applications, SFC validations, appraisal cases, and borrower query responses.';

  return (
    <div className="space-y-6">
      <PageHeader
        title={pageTitle}
        subtitle={pageSubtitle}
        breadcrumbs={[
          { label: 'Borrower Portal', to: '/portal/workbench' },
          { label: 'Applications' },
        ]}
        actions={
          isBorrower ? (
            <Button
              onClick={() => navigate('/portal/applications/new')}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              <Plus className="mr-2 h-4 w-4" />
              New application
            </Button>
          ) : undefined
        }
      />

      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {showEntityFilter && (
              <div className="space-y-2">
                <Label>Entity</Label>
                <Select value={entityFilter} onValueChange={(v) => setEntityFilter(v)}>
                  <SelectTrigger>
                    <SelectValue placeholder="All entities" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">All entities</SelectItem>
                    {entities.map((e) => (
                      <SelectItem key={e.id} value={e.id}>
                        {e.legalName}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            <div className="space-y-2">
              <Label>Status</Label>
              <Select
                value={statusFilter}
                onValueChange={(v) =>
                  setStatusFilter(
                    v as PortalApplicationStatus | PortalSchemeApplicationStatus | 'ALL',
                  )
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  {STATUS_OPTIONS.map((o) => (
                    <SelectItem key={o.value} value={o.value}>
                      {o.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <DataTable<PortalApplication>
        data={query.data?.items ?? []}
        columns={columns}
        getRowId={(row) => row.id}
        isLoading={query.isLoading}
        error={query.isError ? query.error : undefined}
        onRetry={() => query.refetch()}
        onRowClick={(row) => navigate(`/portal/applications/${row.id}`)}
        emptyTitle="No applications yet"
        emptySubtitle={
          isBorrower
            ? 'Start a new institutional application to fund your next maritime or shipyard project.'
            : 'No applications match the current review filters.'
        }
        emptyAction={
          isBorrower ? (
            <Button
              onClick={() => navigate('/portal/applications/new')}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              <FileText className="mr-2 h-4 w-4" />
              New application
            </Button>
          ) : undefined
        }
      />
    </div>
  );
}
