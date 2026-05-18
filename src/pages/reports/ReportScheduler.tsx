import { zodResolver } from '@hookform/resolvers/zod';
import { Play, Plus, RefreshCw } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { DataTable, DateDisplay, ErrorState, FormSection, FormShell, PageHeader, StatusPill } from '@/components/common';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  useCreateReportSchedule,
  useMisCatalog,
  useReportSchedules,
  useRunScheduleNow,
} from '@/hooks/reports/useMisReports';
import type { ReportSchedule } from '@/services/reports/misApi';

const scheduleSchema = z.object({
  reportCode: z.string().min(1, 'Report is required'),
  frequency: z.enum(['DAILY', 'WEEKLY', 'MONTHLY']),
  scheduleTime: z.string().regex(/^\d{2}:\d{2}$/, 'Use HH:mm format'),
  outputFormat: z.enum(['XLSX', 'PDF', 'CSV']),
  recipients: z.string().optional(),
  description: z.string().optional(),
});

type ScheduleFormData = z.infer<typeof scheduleSchema>;

export default function ReportScheduler() {
  const [showForm, setShowForm] = useState(false);
  const catalogQuery = useMisCatalog();
  const schedulesQuery = useReportSchedules(false);
  const createSchedule = useCreateReportSchedule();
  const runNow = useRunScheduleNow();

  const reportOptions = useMemo(
    () => (catalogQuery.data?.groups ?? []).flatMap((group) => group.reports),
    [catalogQuery.data],
  );

  const form = useForm<ScheduleFormData>({
    resolver: zodResolver(scheduleSchema),
    defaultValues: {
      reportCode: '',
      frequency: 'DAILY',
      scheduleTime: '06:00',
      outputFormat: 'XLSX',
      recipients: '',
      description: '',
    },
  });

  function onSubmit(data: ScheduleFormData) {
    createSchedule.mutate(
      {
        reportCode: data.reportCode,
        frequency: data.frequency,
        scheduleTime: data.scheduleTime,
        outputFormat: data.outputFormat,
        recipients: data.recipients
          ?.split(',')
          .map((recipient) => recipient.trim())
          .filter(Boolean),
        description: data.description,
        isActive: true,
      },
      {
        onSuccess: () => {
          setShowForm(false);
          form.reset();
        },
      },
    );
  }

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Report Scheduler"
        subtitle="Persisted manual-download report generation schedules"
        breadcrumbs={[
          { label: 'Reports', to: '/admin/reports' },
          { label: 'Scheduler' },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => void schedulesQuery.refetch()}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
            <Button onClick={() => setShowForm((value) => !value)}>
              <Plus className="mr-2 h-4 w-4" />
              New Schedule
            </Button>
          </div>
        }
      />

      <div className="rounded-lg border bg-muted/30 p-3 text-sm text-muted-foreground">
        Schedules generate report history for manual download. Automated email delivery is not
        enabled in this phase.
      </div>

      {(catalogQuery.error || schedulesQuery.error || createSchedule.error || runNow.error) && (
        <ErrorState
          error={catalogQuery.error ?? schedulesQuery.error ?? createSchedule.error ?? runNow.error}
          onRetry={() => {
            void catalogQuery.refetch();
            void schedulesQuery.refetch();
          }}
        />
      )}

      {showForm && (
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <FormShell
              footer={
                <>
                  <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={createSchedule.isPending}>
                    Save schedule
                  </Button>
                </>
              }
            >
            <FormSection title="Schedule details">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <FormField
                  control={form.control}
                  name="reportCode"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Report</FormLabel>
                      <Select value={field.value} onValueChange={field.onChange}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select report" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {reportOptions.map((report) => (
                            <SelectItem key={report.reportCode} value={report.reportCode}>
                              {report.reportName}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="frequency"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Frequency</FormLabel>
                      <Select value={field.value} onValueChange={field.onChange}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="DAILY">Daily</SelectItem>
                          <SelectItem value="WEEKLY">Weekly</SelectItem>
                          <SelectItem value="MONTHLY">Monthly</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="scheduleTime"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Time</FormLabel>
                      <FormControl>
                        <Input type="time" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="outputFormat"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Output format</FormLabel>
                      <Select value={field.value} onValueChange={field.onChange}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="XLSX">Excel</SelectItem>
                          <SelectItem value="PDF">PDF</SelectItem>
                          <SelectItem value="CSV">CSV</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="recipients"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Recipient metadata</FormLabel>
                      <FormControl>
                        <Input placeholder="name@company.com, finance@company.com" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Description</FormLabel>
                      <FormControl>
                        <Input placeholder="Monthly board pack" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </FormSection>
            </FormShell>
          </form>
        </Form>
      )}

      <DataTable<ReportSchedule>
        data={schedulesQuery.data ?? []}
        isLoading={schedulesQuery.isLoading}
        error={schedulesQuery.error}
        onRetry={() => void schedulesQuery.refetch()}
        getRowId={(row) => row.id}
        emptyTitle="No report schedules"
        emptySubtitle="Create schedules for recurring manual-download MIS generation."
        columns={[
          { key: 'reportName', header: 'Report', sortable: true },
          { key: 'category', header: 'Category', sortable: true },
          { key: 'frequency', header: 'Frequency' },
          { key: 'scheduleTime', header: 'Time' },
          { key: 'outputFormat', header: 'Format' },
          {
            key: 'isActive',
            header: 'Status',
            render: (row) => (
              <StatusPill type="application" status={row.isActive ? 'ACTIVE' : 'INACTIVE'} />
            ),
          },
          {
            key: 'nextRunAt',
            header: 'Next run',
            render: (row) => (row.nextRunAt ? <DateDisplay date={row.nextRunAt} /> : '-'),
          },
          {
            key: 'actions',
            header: 'Actions',
            render: (row) => (
              <Button
                variant="ghost"
                size="sm"
                disabled={runNow.isPending}
                onClick={() => runNow.mutate(row.id)}
              >
                <Play className="mr-2 h-4 w-4" />
                Run now
              </Button>
            ),
          },
        ]}
      />
    </div>
  );
}
