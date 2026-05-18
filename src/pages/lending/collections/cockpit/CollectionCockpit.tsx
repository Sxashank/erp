import { CircleDollarSign, Receipt, RefreshCw } from 'lucide-react';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { DataTable, type Column } from '@/components/common/DataTable';
import { PageHeader } from '@/components/common/PageHeader';
import { StatusPill } from '@/components/common/StatusPill';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCollectionCockpit } from '@/hooks/lending/useCollectionCockpit';
import type {
  CollectionBucketMetric,
  UpcomingCollectionItem,
} from '@/services/lending/collectionCockpitApi';

export default function CollectionCockpit() {
  const navigate = useNavigate();
  const query = useCollectionCockpit({ limit: 10 });
  const summary = query.data?.summary;

  const ageingColumns = useMemo<Column<CollectionBucketMetric>[]>(
    () => [
      {
        key: 'label',
        header: 'Ageing Bucket',
        sortable: true,
      },
      {
        key: 'installmentCount',
        header: 'Instalments',
        align: 'right',
        sortable: true,
      },
      {
        key: 'amountDue',
        header: 'Amount Due',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.amountDue),
        render: (row) => <AmountDisplay amount={row.amountDue} abbreviated />,
      },
      {
        key: 'portfolioPercent',
        header: 'Share',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.portfolioPercent),
        render: (row) => <PercentageDisplay value={row.portfolioPercent} />,
      },
    ],
    [],
  );

  const dueColumns = useMemo<Column<UpcomingCollectionItem>[]>(
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
        key: 'dueDate',
        header: 'Due Date',
        sortable: true,
        render: (row) => <DateDisplay date={row.dueDate} />,
      },
      {
        key: 'status',
        header: 'Status',
        sortable: true,
        render: (row) => <StatusPill type="receipt" status={row.status} />,
      },
      {
        key: 'daysPastDue',
        header: 'DPD',
        align: 'right',
        sortable: true,
        render: (row) => <span className="font-mono">{row.daysPastDue}</span>,
      },
      {
        key: 'amountDue',
        header: 'Amount Due',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.amountDue),
        render: (row) => <AmountDisplay amount={row.amountDue} abbreviated />,
      },
    ],
    [],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Collection Cockpit"
        subtitle="Manual borrower demands, manual receipts, due ageing and allocation exceptions"
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
            <CardTitle className="text-sm font-medium">Period Demand</CardTitle>
            <Receipt className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={summary?.demandAmount ?? '0'}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-sm text-muted-foreground">
              {summary?.periodFrom ? <DateDisplay date={summary.periodFrom} /> : '-'} to{' '}
              {summary?.periodTo ? <DateDisplay date={summary.periodTo} /> : '-'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Collection Efficiency</CardTitle>
            <CircleDollarSign className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <PercentageDisplay
              value={summary?.collectionEfficiencyPercent ?? '0'}
              className="text-2xl font-bold"
            />
            <p className="text-sm text-muted-foreground">
              Allocated <AmountDisplay amount={summary?.allocatedAmount ?? '0'} abbreviated />
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Overdue Amount</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={summary?.overdueAmount ?? '0'}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-sm text-muted-foreground">
              {summary?.overdueAccounts ?? 0} borrower accounts
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Unallocated Receipts</CardTitle>
            <Receipt className="h-4 w-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={summary?.unallocatedReceipts ?? '0'}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-sm text-muted-foreground">
              Manual receipts pending allocation review
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle>Due Ageing</CardTitle>
          </CardHeader>
          <CardContent>
            <DataTable
              data={query.data?.ageingBuckets ?? []}
              columns={ageingColumns}
              getRowId={(row) => row.bucket}
              isLoading={query.isLoading}
              error={query.isError ? query.error : undefined}
              onRetry={() => query.refetch()}
              dense
              emptyTitle="No due ageing rows"
              emptySubtitle="Instalment ageing appears once repayment schedules are generated."
            />
          </CardContent>
        </Card>
      </div>

      <DataTable
        data={query.data?.upcomingCollections ?? []}
        columns={dueColumns}
        getRowId={(row) => `${row.loanAccountId}-${row.installmentNumber}-${row.dueDate}`}
        isLoading={query.isLoading}
        error={query.isError ? query.error : undefined}
        onRetry={() => query.refetch()}
        onRowClick={(row) => navigate(`/admin/lending/accounts/${row.loanAccountId}`)}
        emptyTitle="No pending borrower dues"
        emptySubtitle="There are no unpaid instalments in the selected collection window."
      />
    </div>
  );
}
