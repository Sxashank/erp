import {
  AlertTriangle,
  BadgeCheck,
  CalendarClock,
  Clock3,
  GraduationCap,
  TimerReset,
  TrendingUp,
  UserMinus,
  Users,
} from 'lucide-react';

import { DataTable, type Column } from '@/components/common/DataTable';
import { DateDisplay } from '@/components/common/DateDisplay';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { StatusPill } from '@/components/common/StatusPill';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useHRDashboard } from '@/hooks/hris/useDashboard';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import type {
  HRDashboardPendingAction,
  HRDashboardUpcomingEvent,
} from '@/services/hris/dashboardApi';

function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
}: {
  title: string;
  value: string | number;
  subtitle: string;
  icon: typeof Users;
}) {
  return (
    <Card>
      <CardContent className="flex items-start justify-between pt-6">
        <div>
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="mt-2 text-3xl font-semibold">{value}</p>
          <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>
        </div>
        <div className="rounded-full bg-muted p-3">
          <Icon className="h-5 w-5 text-muted-foreground" />
        </div>
      </CardContent>
    </Card>
  );
}

function DistributionList({
  title,
  items,
}: {
  title: string;
  items: { label: string; count: number }[];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">No activity recorded yet.</p>
        ) : (
          items.map((item) => (
            <div key={item.label} className="flex items-center justify-between gap-4">
              <span className="text-sm">{item.label}</span>
              <span className="text-sm font-medium">{item.count}</span>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

export function HRISDashboard() {
  useRequiredActiveOrganizationId();
  const dashboardQuery = useHRDashboard();

  if (dashboardQuery.isError) {
    return (
      <ErrorState error={dashboardQuery.error} onRetry={() => void dashboardQuery.refetch()} />
    );
  }

  const dashboard = dashboardQuery.data;

  const pendingColumns: Column<HRDashboardPendingAction>[] = [
    { key: 'title', header: 'Queue Item' },
    { key: 'employee', header: 'Employee' },
    {
      key: 'requestDate',
      header: 'Requested',
      render: (row) => <DateDisplay date={row.requestDate} />,
      sortable: true,
      sortValue: (row) => row.requestDate,
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => <StatusPill type="application" status={row.status} />,
    },
  ];

  const eventColumns: Column<HRDashboardUpcomingEvent>[] = [
    { key: 'title', header: 'Event' },
    {
      key: 'date',
      header: 'Date',
      render: (row) => <DateDisplay date={row.date} />,
      sortable: true,
      sortValue: (row) => row.date,
    },
    {
      key: 'count',
      header: 'Count',
      align: 'right',
      render: (row) => row.count ?? '—',
    },
    {
      key: 'type',
      header: 'Type',
      render: (row) => <StatusPill type="application" status={row.type} />,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="HR Dashboard"
        subtitle="Live headcount, attendance, payroll readiness, training, and appraisal operations."
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Active Workforce"
          value={dashboard?.stats.activeEmployees ?? 0}
          subtitle={`${dashboard?.stats.totalEmployees ?? 0} total employees`}
          icon={Users}
        />
        <MetricCard
          title="Today's Attendance"
          value={`${dashboard?.stats.attendancePercentage ?? 0}%`}
          subtitle={`${dashboard?.stats.todayPresent ?? 0} present · ${dashboard?.stats.todayAbsent ?? 0} absent`}
          icon={BadgeCheck}
        />
        <MetricCard
          title="Pending Approvals"
          value={
            (dashboard?.stats.pendingLeaveApprovals ?? 0) +
            (dashboard?.stats.pendingRegularizations ?? 0)
          }
          subtitle={`${dashboard?.stats.pendingLeaveApprovals ?? 0} leave · ${dashboard?.stats.pendingRegularizations ?? 0} regularization`}
          icon={Clock3}
        />
        <MetricCard
          title="Payroll Readiness"
          value={dashboard?.stats.payrollReadyBatches ?? 0}
          subtitle={`${dashboard?.stats.payrollPendingBatches ?? 0} processed batches awaiting next step`}
          icon={TrendingUp}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="New Joiners"
          value={dashboard?.stats.newJoineesThisMonth ?? 0}
          subtitle="Joined this month"
          icon={Users}
        />
        <MetricCard
          title="Separations"
          value={dashboard?.stats.separationsThisMonth ?? 0}
          subtitle="Exited this month"
          icon={UserMinus}
        />
        <MetricCard
          title="Training Pipeline"
          value={dashboard?.stats.upcomingTrainings ?? 0}
          subtitle="Programs in the next 30 days"
          icon={GraduationCap}
        />
        <MetricCard
          title="Appraisal Load"
          value={dashboard?.stats.pendingAppraisals ?? 0}
          subtitle={`${dashboard?.stats.activeCycles ?? 0} active cycles · ${dashboard?.stats.pendingGoals ?? 0} goal packets pending`}
          icon={TimerReset}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <AlertTriangle className="h-4 w-4" />
              Pending HR Workbench
            </CardTitle>
          </CardHeader>
          <CardContent>
            <DataTable
              data={dashboard?.pendingActions ?? []}
              columns={pendingColumns}
              getRowId={(row) => row.id}
              isLoading={dashboardQuery.isLoading}
              emptyTitle="No pending actions"
              emptySubtitle="Leave approvals, attendance regularizations, separations, training, and appraisal queues are currently clear."
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <CalendarClock className="h-4 w-4" />
              Upcoming Events
            </CardTitle>
          </CardHeader>
          <CardContent>
            <DataTable
              data={dashboard?.upcomingEvents ?? []}
              columns={eventColumns}
              getRowId={(row) => row.id}
              isLoading={dashboardQuery.isLoading}
              emptyTitle="No upcoming events"
              emptySubtitle="Holidays, trainings, anniversaries, and appraisal deadlines will appear here."
            />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2 xl:grid-cols-4">
        <DistributionList
          title="Department Distribution"
          items={dashboard?.departmentDistribution ?? []}
        />
        <DistributionList title="Unit Distribution" items={dashboard?.unitDistribution ?? []} />
        <DistributionList title="Training Completion" items={dashboard?.trainingCompletion ?? []} />
        <DistributionList title="Separation Pipeline" items={dashboard?.separationPipeline ?? []} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Payroll Status</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-4">
          <div>
            <p className="text-sm text-muted-foreground">Latest Batch</p>
            <p className="mt-1 font-medium">{dashboard?.payroll.latestBatchNumber ?? '—'}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Latest Status</p>
            {dashboard?.payroll.latestBatchStatus ? (
              <div className="mt-1">
                <StatusPill type="application" status={dashboard.payroll.latestBatchStatus} />
              </div>
            ) : (
              <p className="mt-1 font-medium">—</p>
            )}
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Approved This Year</p>
            <p className="mt-1 font-medium">{dashboard?.payroll.approvedBatchesThisYear ?? 0}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Paid This Year</p>
            <p className="mt-1 font-medium">{dashboard?.payroll.paidBatchesThisYear ?? 0}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default HRISDashboard;
