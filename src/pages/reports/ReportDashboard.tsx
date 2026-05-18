import { BarChart3, Calendar, Download, FileText, Shield } from 'lucide-react';
import { Link } from 'react-router-dom';

import {
  AmountDisplay,
  DataTable,
  ErrorState,
  PageHeader,
  PercentageDisplay,
  StatusPill,
} from '@/components/common';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useMisCatalog, useMisDashboard } from '@/hooks/reports/useMisReports';
import type { MISMetric, ReportCatalogItem } from '@/services/reports/misApi';

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function MetricCard({ metric }: { metric: MISMetric }) {
  return (
    <Card className={metric.status !== 'OK' ? 'border-amber-300 bg-amber-50/50' : undefined}>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-sm text-muted-foreground">{metric.label}</div>
            {metric.valueType === 'AMOUNT' ? (
              <AmountDisplay amount={metric.value} abbreviated className="mt-1 block text-2xl font-semibold" />
            ) : metric.valueType === 'PERCENTAGE' ? (
              <PercentageDisplay value={metric.value} className="mt-1 block text-2xl font-semibold" />
            ) : (
              <div className="mt-1 text-2xl font-semibold tabular-nums">{String(metric.value)}</div>
            )}
          </div>
          <BarChart3 className="h-5 w-5 text-muted-foreground" />
        </div>
      </CardContent>
    </Card>
  );
}

export default function ReportDashboard() {
  const dashboardQuery = useMisDashboard({ asOfDate: todayIso() });
  const catalogQuery = useMisCatalog();
  const groups = catalogQuery.data?.groups ?? [];

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Reports & Analytics"
        subtitle="Financial, regulatory, MIS and operational reporting from live ERP data"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" asChild>
              <Link to="/admin/reports/history">
                <Download className="mr-2 h-4 w-4" />
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

      {(dashboardQuery.error || catalogQuery.error) && (
        <ErrorState
          error={dashboardQuery.error ?? catalogQuery.error}
          onRetry={() => {
            void dashboardQuery.refetch();
            void catalogQuery.refetch();
          }}
        />
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3 xl:grid-cols-6">
        {(dashboardQuery.data?.executiveMetrics ?? []).map((metric) => (
          <MetricCard key={metric.code} metric={metric} />
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        {groups.map((group) => (
          <Card key={group.category}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {group.category === 'TAX_COMPLIANCE' || group.category === 'TREASURY' ? (
                  <Shield className="h-5 w-5" />
                ) : (
                  <FileText className="h-5 w-5" />
                )}
                {group.title}
              </CardTitle>
              <CardDescription>{group.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable<ReportCatalogItem>
                data={group.reports}
                isLoading={catalogQuery.isLoading}
                getRowId={(row) => row.reportCode}
                emptyTitle="No reports configured"
                columns={[
                  {
                    key: 'reportName',
                    header: 'Report',
                    render: (row) => (
                      <Link to={row.route} className="font-medium hover:underline">
                        {row.reportName}
                      </Link>
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

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Report Runs</CardTitle>
          </CardHeader>
          <CardContent>
            <DataTable
              data={dashboardQuery.data?.recentRuns ?? []}
              isLoading={dashboardQuery.isLoading}
              getRowId={(row) => row.id}
              emptyTitle="No generated reports"
              columns={[
                { key: 'reportName', header: 'Report' },
                { key: 'category', header: 'Category' },
                { key: 'status', header: 'Status', render: (row) => <StatusPill type="application" status={row.status} /> },
                { key: 'exportFormat', header: 'Format' },
              ]}
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Active Report Schedules</CardTitle>
            <CardDescription>Manual-download schedules; automated email delivery is not active.</CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={dashboardQuery.data?.activeSchedules ?? []}
              isLoading={dashboardQuery.isLoading}
              getRowId={(row) => row.id}
              emptyTitle="No active schedules"
              columns={[
                { key: 'reportName', header: 'Report' },
                { key: 'frequency', header: 'Frequency' },
                { key: 'scheduleTime', header: 'Time' },
                { key: 'deliveryMode', header: 'Delivery' },
              ]}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

