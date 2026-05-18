import { CheckCircle2, Clock, RefreshCw, ShieldAlert } from 'lucide-react';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { DataTable, type Column } from '@/components/common/DataTable';
import { PageHeader } from '@/components/common/PageHeader';
import { StatusPill } from '@/components/common/StatusPill';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useDisbursementReadiness } from '@/hooks/lending/useDisbursementReadiness';
import type {
  PendingDisbursementItem,
  ReadinessBlockerItem,
  ReadinessBucketMetric,
} from '@/services/lending/disbursementReadinessApi';

export default function DisbursementReadinessCockpit() {
  const navigate = useNavigate();
  const query = useDisbursementReadiness({ limit: 10 });
  const summary = query.data?.summary;

  const bucketColumns = useMemo<Column<ReadinessBucketMetric>[]>(
    () => [
      {
        key: 'label',
        header: 'Readiness Bucket',
        sortable: true,
      },
      {
        key: 'count',
        header: 'Sanctions',
        align: 'right',
        sortable: true,
      },
      {
        key: 'amount',
        header: 'Undisbursed Exposure',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.amount),
        render: (row) => <AmountDisplay amount={row.amount} abbreviated />,
      },
    ],
    [],
  );

  const blockerColumns = useMemo<Column<ReadinessBlockerItem>[]>(
    () => [
      {
        key: 'sanctionNumber',
        header: 'Sanction',
        sortable: true,
        render: (row) => (
          <div className="space-y-1">
            <p className="font-mono text-sm">{row.sanctionNumber}</p>
            <p className="text-xs text-muted-foreground">{row.borrowerName}</p>
          </div>
        ),
      },
      {
        key: 'projectName',
        header: 'Project',
        sortable: true,
        render: (row) => row.projectName || '-',
      },
      {
        key: 'readinessStatus',
        header: 'Readiness',
        sortable: true,
        render: (row) => (
          <StatusPill type="application" status={row.readinessStatus.toUpperCase()} />
        ),
      },
      {
        key: 'mandatoryPending',
        header: 'Pending Conditions',
        align: 'right',
        sortable: true,
        render: (row) => (
          <span className="font-mono">
            {row.mandatoryPending} / {row.mandatoryOverdue} overdue
          </span>
        ),
      },
      {
        key: 'firstDisbursementDeadline',
        header: 'First Disb. Deadline',
        sortable: true,
        render: (row) => <DateDisplay date={row.firstDisbursementDeadline} />,
      },
      {
        key: 'undisbursedAmount',
        header: 'Undisbursed',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.undisbursedAmount),
        render: (row) => <AmountDisplay amount={row.undisbursedAmount} abbreviated />,
      },
    ],
    [],
  );

  const disbursementColumns = useMemo<Column<PendingDisbursementItem>[]>(
    () => [
      {
        key: 'reference',
        header: 'Request',
        sortable: true,
        render: (row) => (
          <div className="space-y-1">
            <p className="font-mono text-sm">{row.reference}</p>
            <p className="text-xs text-muted-foreground">{row.loanAccountNumber}</p>
          </div>
        ),
      },
      {
        key: 'borrowerName',
        header: 'Borrower',
        sortable: true,
      },
      {
        key: 'status',
        header: 'Status',
        sortable: true,
        render: (row) => <StatusPill type="disbursement" status={row.status} />,
      },
      {
        key: 'conditionsVerified',
        header: 'Conditions',
        sortable: true,
        render: (row) => (row.conditionsVerified ? 'Verified' : 'Pending'),
      },
      {
        key: 'scheduledDate',
        header: 'Scheduled',
        sortable: true,
        render: (row) => <DateDisplay date={row.scheduledDate} />,
      },
      {
        key: 'requestedAmount',
        header: 'Requested',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.requestedAmount),
        render: (row) => <AmountDisplay amount={row.requestedAmount} abbreviated />,
      },
      {
        key: 'approvedAmount',
        header: 'Approved',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.approvedAmount ?? 0),
        render: (row) => <AmountDisplay amount={row.approvedAmount} abbreviated />,
      },
    ],
    [],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Disbursement Readiness"
        subtitle="Manual control cockpit for sanctioned-not-disbursed exposure, conditions and tranche processing"
        actions={
          <Button variant="outline" onClick={() => query.refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sanctioned Not Disbursed</CardTitle>
            <Clock className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={summary?.sanctionedNotDisbursedAmount ?? '0'}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-sm text-muted-foreground">
              {summary?.sanctionedNotDisbursedCount ?? 0} open sanctions
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Ready for Manual Disbursement</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={summary?.readyAmount ?? '0'}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-sm text-muted-foreground">
              {summary?.readyCount ?? 0} sanctions without mandatory blockers
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Condition Blocked</CardTitle>
            <ShieldAlert className="h-4 w-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={summary?.conditionBlockedAmount ?? '0'}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-sm text-muted-foreground">
              {summary?.conditionBlockedCount ?? 0} sanctions need manual condition closure
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Requests</CardTitle>
            <Clock className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={summary?.pendingDisbursementAmount ?? '0'}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-sm text-muted-foreground">
              {summary?.pendingDisbursementCount ?? 0} pending,{' '}
              {summary?.approvedPendingProcessingCount ?? 0} approved
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle>Readiness Buckets</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            data={query.data?.readinessBuckets ?? []}
            columns={bucketColumns}
            getRowId={(row) => row.bucket}
            isLoading={query.isLoading}
            error={query.isError ? query.error : undefined}
            onRetry={() => query.refetch()}
            dense
            emptyTitle="No sanctioned-not-disbursed exposure"
            emptySubtitle="Readiness buckets appear when approved sanctions still have undisbursed limits."
          />
        </CardContent>
      </Card>

      <DataTable
        data={query.data?.blockers ?? []}
        columns={blockerColumns}
        getRowId={(row) => row.sanctionId}
        isLoading={query.isLoading}
        error={query.isError ? query.error : undefined}
        onRetry={() => query.refetch()}
        onRowClick={(row) => navigate(`/admin/lending/sanctions/${row.sanctionId}`)}
        emptyTitle="No sanction readiness blockers"
        emptySubtitle="All open sanctions are either fully disbursed or do not have manual condition blockers."
      />

      <DataTable
        data={query.data?.pendingDisbursements ?? []}
        columns={disbursementColumns}
        getRowId={(row) => row.disbursementId}
        isLoading={query.isLoading}
        error={query.isError ? query.error : undefined}
        onRetry={() => query.refetch()}
        onRowClick={(row) => navigate(`/admin/lending/accounts/${row.loanAccountId}`)}
        emptyTitle="No manual disbursement requests pending"
        emptySubtitle="Pending and approved disbursement requests appear here until they are processed manually."
      />
    </div>
  );
}
