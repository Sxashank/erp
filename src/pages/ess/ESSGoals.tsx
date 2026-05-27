import { DataTable, type Column } from '@/components/common/DataTable';
import { DateDisplay } from '@/components/common/DateDisplay';
import { EmptyState } from '@/components/common/EmptyState';
import { PageHeader } from '@/components/common/PageHeader';
import { StatusPill } from '@/components/common/StatusPill';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useEssPerformancePacket } from '@/hooks/ess/useEssOperations';
import type { ESSPerformanceGoal } from '@/services/essApi';

function GoalMetric({
  title,
  value,
  subtitle,
}: {
  title: string;
  value: string | number;
  subtitle: string;
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <p className="text-sm text-muted-foreground">{title}</p>
        <p className="mt-2 text-3xl font-semibold">{value}</p>
        <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>
      </CardContent>
    </Card>
  );
}

export default function ESSGoals() {
  const performanceQuery = useEssPerformancePacket();
  const appraisal = performanceQuery.data?.appraisal ?? null;
  const goals = appraisal?.goals ?? [];

  const columns: Column<ESSPerformanceGoal>[] = [
    {
      key: 'title',
      header: 'Goal',
      render: (row) => (
        <div>
          <div className="font-medium">{row.title}</div>
          <div className="text-xs text-muted-foreground">{row.category || 'General'}</div>
        </div>
      ),
    },
    {
      key: 'weightage',
      header: 'Weight',
      align: 'right',
      render: (row) => `${row.weightage}%`,
      sortable: true,
      sortValue: (row) => row.weightage,
    },
    {
      key: 'dueDate',
      header: 'Due Date',
      render: (row) => (row.dueDate ? <DateDisplay date={row.dueDate} /> : '—'),
      sortable: true,
      sortValue: (row) => row.dueDate ?? '',
    },
    {
      key: 'progressPercent',
      header: 'Progress',
      align: 'right',
      render: (row) => `${row.progressPercent}%`,
      sortable: true,
      sortValue: (row) => row.progressPercent,
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => <StatusPill type="application" status={row.status} />,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Goals"
        subtitle="View appraisal goals, weightage, progress, and the current cycle stage."
      />

      {!appraisal && !performanceQuery.isLoading ? (
        <EmptyState
          title="No active goals"
          subtitle="An appraisal cycle will appear here once HR starts the cycle and assigns your goals."
        />
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-4">
            <GoalMetric
              title="Cycle"
              value={appraisal?.cycle.name ?? '—'}
              subtitle={appraisal?.cycle.cycleType ?? 'No active cycle'}
            />
            <GoalMetric
              title="Total Goals"
              value={goals.length}
              subtitle={`${appraisal?.employee.submittedGoals ?? 0} submitted`}
            />
            <GoalMetric
              title="Completed Goals"
              value={appraisal?.employee.completedGoals ?? 0}
              subtitle={`${appraisal?.employee.goalCount ?? 0} total goals in cycle`}
            />
            <GoalMetric
              title="Current Stage"
              value={appraisal?.appraisal.status ?? '—'}
              subtitle={
                appraisal?.cycle.selfAppraisalEnd
                  ? `Self appraisal due ${appraisal.cycle.selfAppraisalEnd}`
                  : 'No active self-appraisal deadline'
              }
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Current Goal Packet</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                data={goals}
                columns={columns}
                getRowId={(row) => row.id}
                isLoading={performanceQuery.isLoading}
                error={performanceQuery.error}
                onRetry={() => void performanceQuery.refetch()}
                emptyTitle="No goals available"
                emptySubtitle="Goals will appear here once the appraisal cycle is opened."
              />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
