import { AlertTriangle, RefreshCw, ShieldAlert, TrendingDown } from 'lucide-react';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { DataTable, type Column } from '@/components/common/DataTable';
import { PageHeader } from '@/components/common/PageHeader';
import { AssetClassificationBadge } from '@/components/common/StatusPill';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useRiskCockpit } from '@/hooks/lending/useRiskCockpit';
import type {
  OverdueBandMetric,
  RiskBucketMetric,
  TopRiskExposure,
} from '@/services/lending/riskCockpitApi';

export default function RiskCockpit() {
  const navigate = useNavigate();
  const query = useRiskCockpit(10);
  const summary = query.data?.summary;

  const classificationColumns = useMemo<Column<RiskBucketMetric>[]>(
    () => [
      {
        key: 'classification',
        header: 'Asset Class',
        sortable: true,
        render: (row) => <AssetClassificationBadge status={row.classification} />,
      },
      {
        key: 'accountCount',
        header: 'Accounts',
        align: 'right',
        sortable: true,
      },
      {
        key: 'outstanding',
        header: 'Outstanding',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.outstanding),
        render: (row) => <AmountDisplay amount={row.outstanding} abbreviated />,
      },
      {
        key: 'portfolioPercent',
        header: 'Portfolio',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.portfolioPercent),
        render: (row) => <PercentageDisplay value={row.portfolioPercent} />,
      },
      {
        key: 'provisionGap',
        header: 'Provision Gap',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.provisionGap),
        render: (row) => <AmountDisplay amount={row.provisionGap} abbreviated />,
      },
      {
        key: 'provisionCoveragePercent',
        header: 'PCR',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.provisionCoveragePercent),
        render: (row) => <PercentageDisplay value={row.provisionCoveragePercent} />,
      },
    ],
    [],
  );

  const overdueColumns = useMemo<Column<OverdueBandMetric>[]>(
    () => [
      {
        key: 'label',
        header: 'DPD Band',
        sortable: true,
      },
      {
        key: 'accountCount',
        header: 'Accounts',
        align: 'right',
        sortable: true,
      },
      {
        key: 'outstanding',
        header: 'Outstanding',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.outstanding),
        render: (row) => <AmountDisplay amount={row.outstanding} abbreviated />,
      },
      {
        key: 'portfolioPercent',
        header: 'Portfolio',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.portfolioPercent),
        render: (row) => <PercentageDisplay value={row.portfolioPercent} />,
      },
    ],
    [],
  );

  const exposureColumns = useMemo<Column<TopRiskExposure>[]>(
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
        key: 'assetClassification',
        header: 'Class',
        sortable: true,
        render: (row) => <AssetClassificationBadge status={row.assetClassification} />,
      },
      {
        key: 'daysPastDue',
        header: 'DPD',
        align: 'right',
        sortable: true,
        render: (row) => <span className="font-mono">{row.daysPastDue}</span>,
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
        key: 'overdueAmount',
        header: 'Overdue',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.overdueAmount),
        render: (row) => <AmountDisplay amount={row.overdueAmount} abbreviated />,
      },
      {
        key: 'oldestDueDate',
        header: 'Oldest Due',
        sortable: true,
        render: (row) => (row.oldestDueDate ? <DateDisplay date={row.oldestDueDate} /> : '-'),
      },
      {
        key: 'provisionCoveragePercent',
        header: 'PCR',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.provisionCoveragePercent),
        render: (row) => <PercentageDisplay value={row.provisionCoveragePercent} />,
      },
    ],
    [],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Credit Risk Cockpit"
        subtitle="SMA, NPA, DPD, provisioning and top borrower exposure view for corporate loans"
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
            <CardTitle className="text-sm font-medium">Gross NPA</CardTitle>
            <ShieldAlert className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <PercentageDisplay
              value={summary?.grossNpaPercent ?? '0'}
              className="text-2xl font-bold"
            />
            <p className="text-sm text-muted-foreground">
              <AmountDisplay amount={summary?.npaAmount ?? '0'} abbreviated /> across{' '}
              {summary?.npaAccounts ?? 0} accounts
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">SMA Watchlist</CardTitle>
            <AlertTriangle className="h-4 w-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={summary?.smaAmount ?? '0'}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-sm text-muted-foreground">
              {summary?.smaAccounts ?? 0} early-warning accounts
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overdue Exposure</CardTitle>
            <TrendingDown className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={summary?.overdueAmount ?? '0'}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-sm text-muted-foreground">
              {summary?.overdueAccounts ?? 0} accounts with DPD or unpaid dues
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Provision Coverage</CardTitle>
          </CardHeader>
          <CardContent>
            <PercentageDisplay
              value={summary?.provisionCoveragePercent ?? '0'}
              className="text-2xl font-bold"
            />
            <p className="text-sm text-muted-foreground">
              Gap <AmountDisplay amount={summary?.provisionGap ?? '0'} abbreviated />
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle>Asset Classification</CardTitle>
          </CardHeader>
          <CardContent>
            <DataTable
              data={query.data?.assetClassification ?? []}
              columns={classificationColumns}
              getRowId={(row) => row.classification}
              isLoading={query.isLoading}
              error={query.isError ? query.error : undefined}
              onRetry={() => query.refetch()}
              dense
              emptyTitle="No asset-classification rows"
              emptySubtitle="Risk buckets appear after loan accounts are active."
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle>DPD Ageing</CardTitle>
          </CardHeader>
          <CardContent>
            <DataTable
              data={query.data?.overdueBands ?? []}
              columns={overdueColumns}
              getRowId={(row) => row.band}
              isLoading={query.isLoading}
              error={query.isError ? query.error : undefined}
              onRetry={() => query.refetch()}
              dense
              emptyTitle="No DPD rows"
              emptySubtitle="DPD ageing appears after active loan data is available."
            />
          </CardContent>
        </Card>
      </div>

      <DataTable
        data={query.data?.topExposures ?? []}
        columns={exposureColumns}
        getRowId={(row) => row.loanAccountId}
        isLoading={query.isLoading}
        error={query.isError ? query.error : undefined}
        onRetry={() => query.refetch()}
        onRowClick={(row) => navigate(`/admin/lending/accounts/${row.loanAccountId}`)}
        emptyTitle="No risk exposures"
        emptySubtitle="There are no overdue, SMA or NPA corporate loan exposures in this view."
      />
    </div>
  );
}
