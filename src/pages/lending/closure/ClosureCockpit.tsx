import { FileCheck2, LockKeyhole, ReceiptText, RefreshCw } from 'lucide-react';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { DataTable, type Column } from '@/components/common/DataTable';
import { PageHeader } from '@/components/common/PageHeader';
import { StatusPill } from '@/components/common/StatusPill';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useClosureCockpit } from '@/hooks/lending/useClosureCockpit';
import type {
  ClosureCandidateItem,
  RecentClosureReceiptItem,
  SecurityReleaseItem,
} from '@/services/lending/closureCockpitApi';

export default function ClosureCockpit() {
  const navigate = useNavigate();
  const query = useClosureCockpit({ limit: 10, recentDays: 30 });
  const summary = query.data?.summary;

  const candidateColumns = useMemo<Column<ClosureCandidateItem>[]>(
    () => [
      {
        key: 'loanAccountNumber',
        header: 'Loan Account',
        sortable: true,
        render: (row) => (
          <div className="space-y-1">
            <p className="font-mono text-sm">{row.loanAccountNumber}</p>
            <p className="text-xs text-muted-foreground">{row.borrowerName}</p>
          </div>
        ),
      },
      {
        key: 'closureStatus',
        header: 'Closure Status',
        sortable: true,
        render: (row) => <StatusPill type="loan" status={row.closureStatus} />,
      },
      {
        key: 'maturityDate',
        header: 'Maturity',
        sortable: true,
        render: (row) => <DateDisplay date={row.maturityDate} />,
      },
      {
        key: 'totalOutstanding',
        header: 'Outstanding',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.totalOutstanding),
        render: (row) => <AmountDisplay amount={row.totalOutstanding} abbreviated />,
      },
      {
        key: 'unreleasedSecurityCount',
        header: 'Securities',
        align: 'right',
        sortable: true,
        render: (row) => (
          <span className="font-mono">
            {row.unreleasedSecurityCount} / {row.originalDocumentsHeld} docs
          </span>
        ),
      },
      {
        key: 'unreleasedSecurityValue',
        header: 'Security Value',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.unreleasedSecurityValue),
        render: (row) => <AmountDisplay amount={row.unreleasedSecurityValue} abbreviated />,
      },
    ],
    [],
  );

  const securityColumns = useMemo<Column<SecurityReleaseItem>[]>(
    () => [
      {
        key: 'loanAccountNumber',
        header: 'Loan Account',
        sortable: true,
        render: (row) => (
          <div className="space-y-1">
            <p className="font-mono text-sm">{row.loanAccountNumber}</p>
            <p className="text-xs text-muted-foreground">{row.borrowerName}</p>
          </div>
        ),
      },
      {
        key: 'securityType',
        header: 'Security',
        sortable: true,
        render: (row) => (
          <div className="space-y-1">
            <p className="text-sm">{row.securityType.replace(/_/g, ' ')}</p>
            <p className="line-clamp-1 text-xs text-muted-foreground">{row.description}</p>
          </div>
        ),
      },
      {
        key: 'status',
        header: 'Status',
        sortable: true,
        render: (row) => <StatusPill type="sanction" status={row.status} />,
      },
      {
        key: 'originalDocumentsReceived',
        header: 'Original Docs',
        sortable: true,
        render: (row) => (row.originalDocumentsReceived ? 'Held' : 'Not held'),
      },
      {
        key: 'documentLocation',
        header: 'Location',
        sortable: true,
        render: (row) => row.documentLocation || '-',
      },
      {
        key: 'netValue',
        header: 'Net Value',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.netValue),
        render: (row) => <AmountDisplay amount={row.netValue} abbreviated />,
      },
    ],
    [],
  );

  const receiptColumns = useMemo<Column<RecentClosureReceiptItem>[]>(
    () => [
      {
        key: 'receiptNumber',
        header: 'Receipt',
        sortable: true,
        render: (row) => (
          <div className="space-y-1">
            <p className="font-mono text-sm">{row.receiptNumber}</p>
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
        key: 'receiptType',
        header: 'Type',
        sortable: true,
        render: (row) => <StatusPill type="receipt" status={row.receiptType} />,
      },
      {
        key: 'receiptDate',
        header: 'Receipt Date',
        sortable: true,
        render: (row) => <DateDisplay date={row.receiptDate} />,
      },
      {
        key: 'receiptAmount',
        header: 'Amount',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.receiptAmount),
        render: (row) => <AmountDisplay amount={row.receiptAmount} abbreviated />,
      },
      {
        key: 'unallocatedAmount',
        header: 'Unallocated',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.unallocatedAmount),
        render: (row) => <AmountDisplay amount={row.unallocatedAmount} abbreviated />,
      },
    ],
    [],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Closure & Release Cockpit"
        subtitle="Manual loan closure, NOC, security release and document release control view"
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
            <CardTitle className="text-sm font-medium">Ready for Closure</CardTitle>
            <FileCheck2 className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{summary?.closureReadyCount ?? 0}</p>
            <p className="text-sm text-muted-foreground">Zero-outstanding accounts to close</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Closed Pending Release</CardTitle>
            <LockKeyhole className="h-4 w-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{summary?.closedPendingReleaseCount ?? 0}</p>
            <p className="text-sm text-muted-foreground">NOC/security release still open</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Unreleased Security</CardTitle>
            <LockKeyhole className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={summary?.unreleasedSecurityValue ?? '0'}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-sm text-muted-foreground">
              {summary?.unreleasedSecurityCount ?? 0} security records
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Closure Receipts</CardTitle>
            <ReceiptText className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={summary?.recentClosureReceiptAmount ?? '0'}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-sm text-muted-foreground">
              {summary?.recentClosureReceiptCount ?? 0} in last 30 days
            </p>
          </CardContent>
        </Card>
      </div>

      <DataTable
        data={query.data?.closureCandidates ?? []}
        columns={candidateColumns}
        getRowId={(row) => row.loanAccountId}
        isLoading={query.isLoading}
        error={query.isError ? query.error : undefined}
        onRetry={() => query.refetch()}
        onRowClick={(row) => navigate(`/admin/lending/accounts/${row.loanAccountId}`)}
        emptyTitle="No loan accounts ready for closure"
        emptySubtitle="Zero-outstanding or closed-pending-release loan accounts appear here."
      />

      <DataTable
        data={query.data?.pendingSecurityReleases ?? []}
        columns={securityColumns}
        getRowId={(row) => row.securityId}
        isLoading={query.isLoading}
        error={query.isError ? query.error : undefined}
        onRetry={() => query.refetch()}
        onRowClick={(row) => navigate(`/admin/lending/accounts/${row.loanAccountId}`)}
        emptyTitle="No pending security releases"
        emptySubtitle="Security and original-document release items appear after closure readiness."
      />

      <DataTable
        data={query.data?.recentClosureReceipts ?? []}
        columns={receiptColumns}
        getRowId={(row) => row.receiptId}
        isLoading={query.isLoading}
        error={query.isError ? query.error : undefined}
        onRetry={() => query.refetch()}
        onRowClick={(row) => navigate(`/admin/lending/accounts/${row.loanAccountId}`)}
        emptyTitle="No recent closure receipts"
        emptySubtitle="Manual prepayment, foreclosure, OTS and legal recovery receipts appear here."
      />
    </div>
  );
}
