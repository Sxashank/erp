import { Download, RefreshCw } from 'lucide-react';
import { useMemo, useState } from 'react';

import { DataTable, DateDisplay, ErrorState, FilterBar, PageHeader, StatusPill } from '@/components/common';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useCreateReportRun, useReportRuns } from '@/hooks/reports/useMisReports';
import type { ReportRun } from '@/services/reports/misApi';

export default function ReportHistory() {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const runsQuery = useReportRuns(100);
  const createRun = useCreateReportRun();

  const filteredRuns = useMemo(() => {
    return (runsQuery.data ?? []).filter((run) => {
      const matchesSearch =
        run.reportName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        run.reportCode.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCategory = categoryFilter === 'ALL' || run.category === categoryFilter;
      const matchesStatus = statusFilter === 'ALL' || run.status === statusFilter;
      return matchesSearch && matchesCategory && matchesStatus;
    });
  }, [categoryFilter, runsQuery.data, searchTerm, statusFilter]);

  const categories = Array.from(new Set((runsQuery.data ?? []).map((run) => run.category))).sort();

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Report History"
        subtitle="Auditable history of manually generated and scheduled MIS reports"
        breadcrumbs={[
          { label: 'Reports', to: '/admin/reports' },
          { label: 'History' },
        ]}
        actions={
          <Button variant="outline" onClick={() => void runsQuery.refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        }
      />

      {runsQuery.error && <ErrorState error={runsQuery.error} onRetry={() => void runsQuery.refetch()} />}

      <FilterBar
        search={searchTerm}
        onSearchChange={setSearchTerm}
        searchPlaceholder="Search report history"
        onClear={() => {
          setSearchTerm('');
          setCategoryFilter('ALL');
          setStatusFilter('ALL');
        }}
      >
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All categories</SelectItem>
            {categories.map((category) => (
              <SelectItem key={category} value={category}>
                {category}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All statuses</SelectItem>
            <SelectItem value="COMPLETED">Completed</SelectItem>
            <SelectItem value="FAILED">Failed</SelectItem>
          </SelectContent>
        </Select>
      </FilterBar>

      <DataTable<ReportRun>
        data={filteredRuns}
        isLoading={runsQuery.isLoading}
        error={runsQuery.error}
        onRetry={() => void runsQuery.refetch()}
        getRowId={(row) => row.id}
        emptyTitle="No report runs"
        emptySubtitle="Generate a report from MIS to create history."
        columns={[
          { key: 'reportName', header: 'Report', sortable: true },
          { key: 'category', header: 'Category', sortable: true },
          {
            key: 'generatedAt',
            header: 'Generated at',
            sortable: true,
            render: (row) => <DateDisplay date={row.generatedAt} />,
          },
          {
            key: 'status',
            header: 'Status',
            render: (row) => <StatusPill type="application" status={row.status} />,
          },
          {
            key: 'rowCount',
            header: 'Rows',
            align: 'right',
            render: (row) => row.rowCount.toLocaleString('en-IN'),
          },
          { key: 'exportFormat', header: 'Format' },
          {
            key: 'durationMs',
            header: 'Duration',
            align: 'right',
            render: (row) => (row.durationMs == null ? '-' : `${row.durationMs} ms`),
          },
          {
            key: 'actions',
            header: 'Actions',
            render: (row) => (
              <Button
                variant="ghost"
                size="sm"
                disabled={createRun.isPending}
                onClick={() =>
                  createRun.mutate({
                    reportCode: row.reportCode,
                    exportFormat: row.exportFormat,
                    parameters: row.parameters,
                  })
                }
              >
                <Download className="mr-2 h-4 w-4" />
                Re-run
              </Button>
            ),
          },
        ]}
      />
    </div>
  );
}
