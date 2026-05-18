import {
  AlertTriangle,
  BarChart3,
  Calendar,
  Download,
  FileText,
  RefreshCw,
  Shield,
  TrendingUp,
} from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import {
  AmountDisplay,
  DataTable,
  EmptyState,
  ErrorState,
  PageHeader,
  PercentageDisplay,
  StatusPill,
} from '@/components/common';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  useAllModulesReport,
  useBranchPerformanceReport,
  useCollectionReport,
  useCreateReportRun,
  useDelinquencyReport,
  useDisbursementReport,
  useMisCatalog,
  useMisDashboard,
  usePortfolioSummary,
  useProfitabilityReport,
} from '@/hooks/reports/useMisReports';
import type {
  CollectionBucketItem,
  CollectionModeItem,
  DelinquencyBucketItem,
  DisbursementBreakdownItem,
  MISMetric,
  ModuleReportSection,
  NumericValue,
  PortfolioBreakdownItem,
  ReportCatalogItem,
} from '@/services/reports/misApi';

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function priorMonthIso(): string {
  return new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
}

function asNumber(value: NumericValue | null | undefined): number {
  if (value === null || value === undefined) return 0;
  return typeof value === 'string' ? Number(value) : value;
}

function isAmountKey(key: string): boolean {
  return /amount|value|outstanding|payable|cost|salary|gross|net|tds|gst|debit|credit|block|wdv|depreciation|payroll/i.test(
    key,
  );
}

function renderModuleValue(key: string, value: unknown) {
  if (value === null || value === undefined || value === '') return '-';
  if (typeof value === 'number' || typeof value === 'string') {
    const numericValue = typeof value === 'string' ? Number(value) : value;
    if (Number.isFinite(numericValue) && isAmountKey(key)) {
      return <AmountDisplay amount={numericValue} abbreviated />;
    }
  }
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  return String(value);
}

function MetricValue({ metric }: { metric: MISMetric }) {
  if (metric.valueType === 'AMOUNT') {
    return <AmountDisplay amount={metric.value} abbreviated className="text-2xl font-semibold" />;
  }
  if (metric.valueType === 'PERCENTAGE') {
    return <PercentageDisplay value={metric.value} className="text-2xl font-semibold" />;
  }
  return <span className="text-2xl font-semibold tabular-nums">{String(metric.value)}</span>;
}

function ModuleMetricTile({ metric }: { metric: MISMetric }) {
  return (
    <div
      className={
        metric.status !== 'OK'
          ? 'rounded-lg border border-amber-300 bg-amber-50/50 p-3'
          : 'rounded-lg border bg-background p-3'
      }
    >
      <div className="text-xs text-muted-foreground">{metric.label}</div>
      <div className="mt-1">
        <MetricValue metric={metric} />
      </div>
    </div>
  );
}

function ModuleSectionCard({ section }: { section: ModuleReportSection }) {
  const rows = section.rows.flatMap((row) =>
    Object.entries(row.values).map(([key, value]) => ({
      rowKey: `${row.label}-${key}`,
      label: row.label,
      metric: key,
      value,
      status: row.status,
      route: row.route,
    })),
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle>{section.moduleName}</CardTitle>
            <CardDescription>{section.category}</CardDescription>
          </div>
          <Button variant="outline" size="sm" asChild>
            <Link to={section.route}>Open module</Link>
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
          {section.metrics.map((metric) => (
            <ModuleMetricTile key={metric.code} metric={metric} />
          ))}
        </div>
        <DataTable
          data={rows}
          getRowId={(row) => row.rowKey}
          emptyTitle="No module report rows"
          columns={[
            {
              key: 'label',
              header: 'Report area',
              render: (row) =>
                row.route ? (
                  <Link to={row.route} className="font-medium hover:underline">
                    {row.label}
                  </Link>
                ) : (
                  row.label
                ),
            },
            { key: 'metric', header: 'Metric' },
            {
              key: 'value',
              header: 'Value',
              align: 'right',
              render: (row) => renderModuleValue(row.metric, row.value),
            },
            {
              key: 'status',
              header: 'Status',
              render: (row) => <StatusPill type="application" status={row.status} />,
            },
          ]}
        />
      </CardContent>
    </Card>
  );
}

function MetricCard({ metric }: { metric: MISMetric }) {
  const isWarning = metric.status !== 'OK';
  return (
    <Card className={isWarning ? 'border-amber-300 bg-amber-50/50' : undefined}>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 space-y-1">
            <div className="text-sm text-muted-foreground">{metric.label}</div>
            <MetricValue metric={metric} />
          </div>
          {isWarning ? (
            <AlertTriangle className="h-5 w-5 shrink-0 text-amber-600" />
          ) : (
            <TrendingUp className="h-5 w-5 shrink-0 text-muted-foreground" />
          )}
        </div>
        {metric.description && (
          <p className="mt-2 text-xs text-muted-foreground">{metric.description}</p>
        )}
      </CardContent>
    </Card>
  );
}

function ReportToolbar({
  children,
  onRefresh,
  reportCode,
  parameters,
}: {
  children: React.ReactNode;
  onRefresh: () => void;
  reportCode: string;
  parameters: Record<string, unknown>;
}) {
  const createRun = useCreateReportRun();

  return (
    <div className="flex flex-wrap items-end justify-between gap-3 rounded-lg border bg-background p-3">
      <div className="flex flex-wrap items-end gap-3">{children}</div>
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={onRefresh}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Generate
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={createRun.isPending}
          onClick={() =>
            createRun.mutate({
              reportCode,
              exportFormat: 'XLSX',
              parameters,
            })
          }
        >
          <Download className="mr-2 h-4 w-4" />
          Record Export
        </Button>
      </div>
    </div>
  );
}

function DateField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-1">
      <Label>{label}</Label>
      <Input type="date" value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

function PortfolioSummaryReport({ asOfDate, setAsOfDate }: { asOfDate: string; setAsOfDate: (value: string) => void }) {
  const query = usePortfolioSummary({ asOfDate });
  const report = query.data;

  return (
    <div className="space-y-6">
      <ReportToolbar
        onRefresh={() => void query.refetch()}
        reportCode="PORTFOLIO_SUMMARY"
        parameters={{ asOfDate }}
      >
        <DateField label="As of date" value={asOfDate} onChange={setAsOfDate} />
      </ReportToolbar>

      {query.error && <ErrorState error={query.error} onRetry={() => void query.refetch()} />}

      {report && (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <Card>
              <CardContent className="pt-6">
                <div className="text-sm text-muted-foreground">AUM</div>
                <AmountDisplay
                  amount={report.summary.totalOutstanding}
                  abbreviated
                  className="mt-1 block text-2xl font-semibold"
                />
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-sm text-muted-foreground">Active accounts</div>
                <div className="mt-1 text-2xl font-semibold tabular-nums">
                  {report.summary.activeAccounts.toLocaleString('en-IN')}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-sm text-muted-foreground">Total overdue</div>
                <AmountDisplay
                  amount={report.summary.totalOverdue}
                  abbreviated
                  className="mt-1 block text-2xl font-semibold"
                />
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-sm text-muted-foreground">Weighted yield</div>
                <PercentageDisplay
                  value={report.summary.weightedAverageYield}
                  className="mt-1 block text-2xl font-semibold"
                />
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Product Mix</CardTitle>
              <CardDescription>Live loan outstanding by corporate loan product.</CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable<PortfolioBreakdownItem>
                data={report.productBreakdown}
                isLoading={query.isLoading}
                getRowId={(row) => row.name}
                emptyTitle="No portfolio data"
                emptySubtitle="Loan accounts created in LMS will appear here."
                columns={[
                  { key: 'name', header: 'Product', sortable: true },
                  {
                    key: 'count',
                    header: 'Accounts',
                    align: 'right',
                    render: (row) => row.count.toLocaleString('en-IN'),
                  },
                  {
                    key: 'amount',
                    header: 'Outstanding',
                    align: 'right',
                    render: (row) => <AmountDisplay amount={row.amount} abbreviated />,
                  },
                  {
                    key: 'sharePercent',
                    header: 'Share',
                    align: 'right',
                    render: (row) => <PercentageDisplay value={row.sharePercent} />,
                  },
                  {
                    key: 'averageYield',
                    header: 'Yield',
                    align: 'right',
                    render: (row) => <PercentageDisplay value={row.averageYield} />,
                  },
                ]}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Asset Quality</CardTitle>
              <CardDescription>Outstanding by RBI asset classification.</CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable<PortfolioBreakdownItem>
                data={report.assetQualityBreakdown}
                getRowId={(row) => row.name}
                emptyTitle="No asset quality buckets"
                columns={[
                  {
                    key: 'name',
                    header: 'Classification',
                    render: (row) => <StatusPill type="classification" status={row.name} />,
                  },
                  {
                    key: 'count',
                    header: 'Accounts',
                    align: 'right',
                    render: (row) => row.count.toLocaleString('en-IN'),
                  },
                  {
                    key: 'amount',
                    header: 'Outstanding',
                    align: 'right',
                    render: (row) => <AmountDisplay amount={row.amount} abbreviated />,
                  },
                  {
                    key: 'sharePercent',
                    header: 'Share',
                    align: 'right',
                    render: (row) => <PercentageDisplay value={row.sharePercent} />,
                  },
                ]}
              />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function DisbursementReport({ fromDate, toDate, setFromDate, setToDate }: {
  fromDate: string;
  toDate: string;
  setFromDate: (value: string) => void;
  setToDate: (value: string) => void;
}) {
  const [groupBy, setGroupBy] = useState<'PRODUCT' | 'BRANCH' | 'CHANNEL'>('PRODUCT');
  const query = useDisbursementReport({ fromDate, toDate, groupBy });
  const report = query.data;

  return (
    <div className="space-y-6">
      <ReportToolbar
        onRefresh={() => void query.refetch()}
        reportCode="DISBURSEMENT"
        parameters={{ fromDate, toDate, groupBy }}
      >
        <DateField label="From" value={fromDate} onChange={setFromDate} />
        <DateField label="To" value={toDate} onChange={setToDate} />
        <div className="space-y-1">
          <Label>Group by</Label>
          <Select value={groupBy} onValueChange={(value) => setGroupBy(value as typeof groupBy)}>
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="PRODUCT">Product</SelectItem>
              <SelectItem value="BRANCH">Branch</SelectItem>
              <SelectItem value="CHANNEL">Disbursement mode</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </ReportToolbar>

      {report && (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <MetricCard
              metric={{
                code: 'DISB_AMOUNT',
                label: 'Total disbursed',
                value: report.summary.totalAmount,
                valueType: 'AMOUNT',
                status: 'OK',
              }}
            />
            <MetricCard
              metric={{
                code: 'DISB_COUNT',
                label: 'Disbursement count',
                value: report.summary.totalCount,
                valueType: 'NUMBER',
                status: 'OK',
              }}
            />
            <MetricCard
              metric={{
                code: 'AVG_TICKET',
                label: 'Average ticket size',
                value: report.summary.averageTicketSize,
                valueType: 'AMOUNT',
                status: 'OK',
              }}
            />
          </div>
          <Card>
            <CardHeader>
              <CardTitle>Disbursement Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable<DisbursementBreakdownItem>
                data={report.breakdown}
                isLoading={query.isLoading}
                error={query.error}
                onRetry={() => void query.refetch()}
                getRowId={(row) => row.name}
                emptyTitle="No disbursements"
                columns={[
                  { key: 'name', header: groupBy === 'CHANNEL' ? 'Mode' : groupBy === 'BRANCH' ? 'Branch' : 'Product' },
                  { key: 'count', header: 'Loans', align: 'right', render: (row) => row.count.toLocaleString('en-IN') },
                  { key: 'amount', header: 'Amount', align: 'right', render: (row) => <AmountDisplay amount={row.amount} abbreviated /> },
                  { key: 'averageTicketSize', header: 'Avg ticket', align: 'right', render: (row) => <AmountDisplay amount={row.averageTicketSize} abbreviated /> },
                  { key: 'sharePercent', header: 'Share', align: 'right', render: (row) => <PercentageDisplay value={row.sharePercent} /> },
                ]}
              />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function CollectionReport({ fromDate, toDate, setFromDate, setToDate }: {
  fromDate: string;
  toDate: string;
  setFromDate: (value: string) => void;
  setToDate: (value: string) => void;
}) {
  const query = useCollectionReport({ fromDate, toDate });
  const report = query.data;

  return (
    <div className="space-y-6">
      <ReportToolbar
        onRefresh={() => void query.refetch()}
        reportCode="COLLECTION"
        parameters={{ fromDate, toDate }}
      >
        <DateField label="From" value={fromDate} onChange={setFromDate} />
        <DateField label="To" value={toDate} onChange={setToDate} />
      </ReportToolbar>

      {report && (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <MetricCard metric={{ code: 'DEMAND', label: 'Demand', value: report.summary.totalDemand, valueType: 'AMOUNT', status: 'OK' }} />
            <MetricCard metric={{ code: 'COLLECTED', label: 'Collected', value: report.summary.totalCollected, valueType: 'AMOUNT', status: 'OK' }} />
            <MetricCard metric={{ code: 'EFFICIENCY', label: 'Collection efficiency', value: report.summary.collectionEfficiency, valueType: 'PERCENTAGE', status: asNumber(report.summary.collectionEfficiency) < 90 ? 'WARN' : 'OK' }} />
            <MetricCard metric={{ code: 'SHORTFALL', label: 'Shortfall', value: report.summary.shortfall, valueType: 'AMOUNT', status: asNumber(report.summary.shortfall) > 0 ? 'WARN' : 'OK' }} />
          </div>
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Receipt Mode</CardTitle>
              </CardHeader>
              <CardContent>
                <DataTable<CollectionModeItem>
                  data={report.modeWise}
                  isLoading={query.isLoading}
                  error={query.error}
                  onRetry={() => void query.refetch()}
                  getRowId={(row) => row.mode}
                  emptyTitle="No receipts"
                  columns={[
                    { key: 'mode', header: 'Mode', render: (row) => <StatusPill type="receipt" status={row.mode} /> },
                    { key: 'amount', header: 'Amount', align: 'right', render: (row) => <AmountDisplay amount={row.amount} abbreviated /> },
                    { key: 'sharePercent', header: 'Share', align: 'right', render: (row) => <PercentageDisplay value={row.sharePercent} /> },
                  ]}
                />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>DPD Buckets</CardTitle>
              </CardHeader>
              <CardContent>
                <DataTable<CollectionBucketItem>
                  data={report.bucketWise}
                  getRowId={(row) => row.bucket}
                  emptyTitle="No bucket data"
                  columns={[
                    { key: 'bucket', header: 'Bucket' },
                    { key: 'demand', header: 'Demand', align: 'right', render: (row) => <AmountDisplay amount={row.demand} abbreviated /> },
                    { key: 'collected', header: 'Collected', align: 'right', render: (row) => <AmountDisplay amount={row.collected} abbreviated /> },
                    { key: 'efficiency', header: 'Efficiency', align: 'right', render: (row) => <PercentageDisplay value={row.efficiency} /> },
                  ]}
                />
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

function DelinquencyReport({ asOfDate, setAsOfDate }: { asOfDate: string; setAsOfDate: (value: string) => void }) {
  const query = useDelinquencyReport({ asOfDate });
  const report = query.data;

  return (
    <div className="space-y-6">
      <ReportToolbar onRefresh={() => void query.refetch()} reportCode="DELINQUENCY" parameters={{ asOfDate }}>
        <DateField label="As of date" value={asOfDate} onChange={setAsOfDate} />
      </ReportToolbar>
      {report && (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <MetricCard metric={{ code: 'TOTAL_OUTSTANDING', label: 'Outstanding', value: report.summary.totalOutstanding, valueType: 'AMOUNT', status: 'OK' }} />
            <MetricCard metric={{ code: 'DELINQUENT', label: 'Delinquent', value: report.summary.totalDelinquent, valueType: 'AMOUNT', status: asNumber(report.summary.totalDelinquent) > 0 ? 'WARN' : 'OK' }} />
            <MetricCard metric={{ code: 'DELINQUENCY_RATE', label: 'Delinquency rate', value: report.summary.delinquencyRate, valueType: 'PERCENTAGE', status: asNumber(report.summary.delinquencyRate) > 0 ? 'WARN' : 'OK' }} />
            <MetricCard metric={{ code: 'OVERDUE_ACCOUNTS', label: 'Overdue accounts', value: report.summary.overdueAccounts, valueType: 'NUMBER', status: report.summary.overdueAccounts > 0 ? 'WARN' : 'OK' }} />
          </div>
          <Card>
            <CardHeader>
              <CardTitle>DPD Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable<DelinquencyBucketItem>
                data={report.buckets}
                isLoading={query.isLoading}
                error={query.error}
                onRetry={() => void query.refetch()}
                getRowId={(row, index) => `${row.bucket}-${row.classification}-${index}`}
                emptyTitle="No delinquency data"
                columns={[
                  { key: 'bucket', header: 'Bucket' },
                  { key: 'classification', header: 'Classification', render: (row) => <StatusPill type="classification" status={row.classification} /> },
                  { key: 'accounts', header: 'Accounts', align: 'right', render: (row) => row.accounts.toLocaleString('en-IN') },
                  { key: 'amount', header: 'Outstanding', align: 'right', render: (row) => <AmountDisplay amount={row.amount} abbreviated /> },
                  { key: 'sharePercent', header: 'Share', align: 'right', render: (row) => <PercentageDisplay value={row.sharePercent} /> },
                ]}
              />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Top Delinquent Accounts</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                data={report.topDelinquentAccounts}
                getRowId={(row) => row.loanAccountNumber}
                emptyTitle="No overdue accounts"
                columns={[
                  { key: 'loanAccountNumber', header: 'Loan account' },
                  { key: 'borrowerName', header: 'Borrower' },
                  { key: 'productName', header: 'Product' },
                  { key: 'outstandingAmount', header: 'Outstanding', align: 'right', render: (row) => <AmountDisplay amount={row.outstandingAmount} abbreviated /> },
                  { key: 'daysPastDue', header: 'DPD', align: 'right', render: (row) => row.daysPastDue.toLocaleString('en-IN') },
                  { key: 'classification', header: 'Classification', render: (row) => <StatusPill type="classification" status={row.classification} /> },
                ]}
              />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function ProfitabilityReport({ fromDate, toDate, setFromDate, setToDate }: {
  fromDate: string;
  toDate: string;
  setFromDate: (value: string) => void;
  setToDate: (value: string) => void;
}) {
  const query = useProfitabilityReport({ fromDate, toDate });
  const report = query.data;

  return (
    <div className="space-y-6">
      <ReportToolbar onRefresh={() => void query.refetch()} reportCode="PROFITABILITY" parameters={{ fromDate, toDate }}>
        <DateField label="From" value={fromDate} onChange={setFromDate} />
        <DateField label="To" value={toDate} onChange={setToDate} />
      </ReportToolbar>
      {report && (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <MetricCard metric={{ code: 'PBT', label: 'Profit before tax', value: report.summary.profitBeforeTax, valueType: 'AMOUNT', status: asNumber(report.summary.profitBeforeTax) < 0 ? 'WARN' : 'OK' }} />
            <MetricCard metric={{ code: 'NIM', label: 'NIM', value: report.summary.netInterestMargin, valueType: 'PERCENTAGE', status: 'OK' }} />
            <MetricCard metric={{ code: 'COST_OF_FUNDS', label: 'Cost of funds', value: report.summary.costOfFunds, valueType: 'PERCENTAGE', status: 'OK' }} />
            <MetricCard metric={{ code: 'SPREAD', label: 'Spread', value: report.summary.spread, valueType: 'PERCENTAGE', status: asNumber(report.summary.spread) < 0 ? 'WARN' : 'OK' }} />
          </div>
          <Card>
            <CardHeader>
              <CardTitle>Product Profitability</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                data={report.productWise}
                isLoading={query.isLoading}
                error={query.error}
                onRetry={() => void query.refetch()}
                getRowId={(row) => row.name}
                emptyTitle="No profitability data"
                columns={[
                  { key: 'name', header: 'Product' },
                  { key: 'income', header: 'Income', align: 'right', render: (row) => <AmountDisplay amount={row.income} abbreviated /> },
                  { key: 'expense', header: 'Expense', align: 'right', render: (row) => <AmountDisplay amount={row.expense} abbreviated /> },
                  { key: 'profit', header: 'Profit', align: 'right', render: (row) => <AmountDisplay amount={row.profit} abbreviated /> },
                  { key: 'margin', header: 'Margin', align: 'right', render: (row) => <PercentageDisplay value={row.margin} /> },
                ]}
              />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function BranchPerformanceReport({ fromDate, toDate, setFromDate, setToDate }: {
  fromDate: string;
  toDate: string;
  setFromDate: (value: string) => void;
  setToDate: (value: string) => void;
}) {
  const query = useBranchPerformanceReport({ fromDate, toDate });
  const report = query.data;

  return (
    <div className="space-y-6">
      <ReportToolbar onRefresh={() => void query.refetch()} reportCode="BRANCH_PERFORMANCE" parameters={{ fromDate, toDate }}>
        <DateField label="From" value={fromDate} onChange={setFromDate} />
        <DateField label="To" value={toDate} onChange={setToDate} />
      </ReportToolbar>
      <Card>
        <CardHeader>
          <CardTitle>Branch Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            data={report?.branches ?? []}
            isLoading={query.isLoading}
            error={query.error}
            onRetry={() => void query.refetch()}
            getRowId={(row, index) => row.branchId ?? `${row.branchName}-${index}`}
            emptyTitle="No branch performance data"
            columns={[
              { key: 'branchName', header: 'Branch' },
              { key: 'applications', header: 'Applications', align: 'right', render: (row) => row.applications.toLocaleString('en-IN') },
              { key: 'sanctionedAmount', header: 'Sanctioned', align: 'right', render: (row) => <AmountDisplay amount={row.sanctionedAmount} abbreviated /> },
              { key: 'aum', header: 'AUM', align: 'right', render: (row) => <AmountDisplay amount={row.aum} abbreviated /> },
              { key: 'disbursement', header: 'Disbursement', align: 'right', render: (row) => <AmountDisplay amount={row.disbursement} abbreviated /> },
              { key: 'collection', header: 'Collection', align: 'right', render: (row) => <AmountDisplay amount={row.collection} abbreviated /> },
              { key: 'collectionEfficiency', header: 'Efficiency', align: 'right', render: (row) => <PercentageDisplay value={row.collectionEfficiency} /> },
              { key: 'npaPercentage', header: 'NPA', align: 'right', render: (row) => <PercentageDisplay value={row.npaPercentage} /> },
            ]}
          />
        </CardContent>
      </Card>
    </div>
  );
}

function AllModulesReport({
  asOfDate,
  fromDate,
  toDate,
  setAsOfDate,
  setFromDate,
  setToDate,
}: {
  asOfDate: string;
  fromDate: string;
  toDate: string;
  setAsOfDate: (value: string) => void;
  setFromDate: (value: string) => void;
  setToDate: (value: string) => void;
}) {
  const query = useAllModulesReport({ asOfDate, fromDate, toDate });
  const report = query.data;

  return (
    <div className="space-y-6">
      <ReportToolbar
        onRefresh={() => void query.refetch()}
        reportCode="BOARD_PACK"
        parameters={{ asOfDate, fromDate, toDate }}
      >
        <DateField label="As of date" value={asOfDate} onChange={setAsOfDate} />
        <DateField label="From" value={fromDate} onChange={setFromDate} />
        <DateField label="To" value={toDate} onChange={setToDate} />
      </ReportToolbar>

      {query.error && <ErrorState error={query.error} onRetry={() => void query.refetch()} />}

      {!query.isLoading && !report?.modules.length && (
        <EmptyState
          title="No module report data"
          subtitle="As modules are used, their live MIS metrics will appear here."
        />
      )}

      <div className="grid grid-cols-1 gap-6">
        {(report?.modules ?? []).map((section) => (
          <ModuleSectionCard key={section.moduleCode} section={section} />
        ))}
      </div>
    </div>
  );
}

function ReportCatalog() {
  const catalogQuery = useMisCatalog();
  const groups = catalogQuery.data?.groups ?? [];

  if (catalogQuery.error) {
    return <ErrorState error={catalogQuery.error} onRetry={() => void catalogQuery.refetch()} />;
  }

  if (!catalogQuery.isLoading && groups.length === 0) {
    return <EmptyState title="No MIS reports configured" />;
  }

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      {groups.map((group) => (
        <Card key={group.category}>
          <CardHeader>
            <CardTitle>{group.title}</CardTitle>
            <CardDescription>{group.description}</CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable<ReportCatalogItem>
              data={group.reports}
              isLoading={catalogQuery.isLoading}
              getRowId={(row) => row.reportCode}
              emptyTitle="No reports in this group"
              columns={[
                {
                  key: 'reportName',
                  header: 'Report',
                  render: (row) => (
                    <div className="space-y-1">
                      <Link to={row.route} className="font-medium hover:underline">
                        {row.reportName}
                      </Link>
                      <div className="text-xs text-muted-foreground">{row.description}</div>
                    </div>
                  ),
                },
                { key: 'module', header: 'Module' },
                {
                  key: 'exportFormats',
                  header: 'Formats',
                  render: (row) => (
                    <div className="flex flex-wrap gap-1">
                      {row.exportFormats.map((format) => (
                        <Badge key={format} variant="outline">
                          {format}
                        </Badge>
                      ))}
                    </div>
                  ),
                },
              ]}
            />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default function MISReports() {
  const [activeTab, setActiveTab] = useState('command');
  const [asOfDate, setAsOfDate] = useState(todayIso());
  const [fromDate, setFromDate] = useState(priorMonthIso());
  const [toDate, setToDate] = useState(todayIso());
  const dashboardQuery = useMisDashboard({ asOfDate });
  const dashboard = dashboardQuery.data;

  const allDashboardMetrics = useMemo(
    () => [
      ...(dashboard?.executiveMetrics ?? []),
      ...(dashboard?.exceptionMetrics ?? []),
    ],
    [dashboard],
  );

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="MIS Command Center"
        subtitle="Enterprise reporting across board, lending, treasury, finance, tax, operations and portals"
        breadcrumbs={[{ label: 'Reports', to: '/admin/reports' }, { label: 'MIS Reports' }]}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" asChild>
              <Link to="/admin/reports/history">
                <FileText className="mr-2 h-4 w-4" />
                History
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link to="/admin/reports/scheduler">
                <Calendar className="mr-2 h-4 w-4" />
                Scheduler
              </Link>
            </Button>
          </div>
        }
      />

      <div className="rounded-lg border bg-muted/30 p-3 text-sm text-muted-foreground">
        Reports are generated from manually recorded ERP transactions. External bank, GSTN, RBI,
        email and payment integrations remain future release-gated.
      </div>

      {dashboardQuery.error && (
        <ErrorState error={dashboardQuery.error} onRetry={() => void dashboardQuery.refetch()} />
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3 xl:grid-cols-6">
        {allDashboardMetrics.map((metric) => (
          <MetricCard key={metric.code} metric={metric} />
        ))}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="flex h-auto flex-wrap justify-start">
          <TabsTrigger value="command">
            <BarChart3 className="mr-2 h-4 w-4" />
            Command
          </TabsTrigger>
          <TabsTrigger value="all-modules">All Modules</TabsTrigger>
          <TabsTrigger value="portfolio">Portfolio</TabsTrigger>
          <TabsTrigger value="disbursement">Disbursement</TabsTrigger>
          <TabsTrigger value="collection">Collection</TabsTrigger>
          <TabsTrigger value="delinquency">Delinquency</TabsTrigger>
          <TabsTrigger value="profitability">Profitability</TabsTrigger>
          <TabsTrigger value="branch">Branch</TabsTrigger>
          <TabsTrigger value="catalog">
            <Shield className="mr-2 h-4 w-4" />
            Catalog
          </TabsTrigger>
        </TabsList>

        <TabsContent value="command" className="mt-6">
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Recent Report Runs</CardTitle>
                <CardDescription>Persisted manual/scheduled report generation history.</CardDescription>
              </CardHeader>
              <CardContent>
                <DataTable
                  data={dashboard?.recentRuns ?? []}
                  isLoading={dashboardQuery.isLoading}
                  getRowId={(row) => row.id}
                  emptyTitle="No report runs yet"
                  emptySubtitle="Use Record Export on any report to create an auditable report run."
                  columns={[
                    { key: 'reportName', header: 'Report' },
                    { key: 'category', header: 'Category' },
                    { key: 'status', header: 'Status', render: (row) => <StatusPill type="application" status={row.status} /> },
                    { key: 'rowCount', header: 'Rows', align: 'right', render: (row) => row.rowCount.toLocaleString('en-IN') },
                    { key: 'exportFormat', header: 'Format' },
                  ]}
                />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Active Schedules</CardTitle>
                <CardDescription>Schedules generate history for manual download; email delivery is future-gated.</CardDescription>
              </CardHeader>
              <CardContent>
                <DataTable
                  data={dashboard?.activeSchedules ?? []}
                  isLoading={dashboardQuery.isLoading}
                  getRowId={(row) => row.id}
                  emptyTitle="No active schedules"
                  columns={[
                    { key: 'reportName', header: 'Report' },
                    { key: 'frequency', header: 'Frequency' },
                    { key: 'scheduleTime', header: 'Time' },
                    { key: 'outputFormat', header: 'Format' },
                    { key: 'deliveryMode', header: 'Delivery' },
                  ]}
                />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="all-modules" className="mt-6">
          <AllModulesReport
            asOfDate={asOfDate}
            fromDate={fromDate}
            toDate={toDate}
            setAsOfDate={setAsOfDate}
            setFromDate={setFromDate}
            setToDate={setToDate}
          />
        </TabsContent>
        <TabsContent value="portfolio" className="mt-6">
          <PortfolioSummaryReport asOfDate={asOfDate} setAsOfDate={setAsOfDate} />
        </TabsContent>
        <TabsContent value="disbursement" className="mt-6">
          <DisbursementReport
            fromDate={fromDate}
            toDate={toDate}
            setFromDate={setFromDate}
            setToDate={setToDate}
          />
        </TabsContent>
        <TabsContent value="collection" className="mt-6">
          <CollectionReport
            fromDate={fromDate}
            toDate={toDate}
            setFromDate={setFromDate}
            setToDate={setToDate}
          />
        </TabsContent>
        <TabsContent value="delinquency" className="mt-6">
          <DelinquencyReport asOfDate={asOfDate} setAsOfDate={setAsOfDate} />
        </TabsContent>
        <TabsContent value="profitability" className="mt-6">
          <ProfitabilityReport
            fromDate={fromDate}
            toDate={toDate}
            setFromDate={setFromDate}
            setToDate={setToDate}
          />
        </TabsContent>
        <TabsContent value="branch" className="mt-6">
          <BranchPerformanceReport
            fromDate={fromDate}
            toDate={toDate}
            setFromDate={setFromDate}
            setToDate={setToDate}
          />
        </TabsContent>
        <TabsContent value="catalog" className="mt-6">
          <ReportCatalog />
        </TabsContent>
      </Tabs>
    </div>
  );
}
