import { useEffect, useState } from 'react';

import { DataTable, type Column } from '@/components/common/DataTable';
import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { StatusPill } from '@/components/common/StatusPill';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useEssTrainingDetail, useEssTrainingList } from '@/hooks/ess/useEssOperations';
import type { ESSTrainingProgram } from '@/services/essApi';

function TrainingMetric({
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

export default function ESSTrainingList() {
  const trainingListQuery = useEssTrainingList();
  const [selectedProgramId, setSelectedProgramId] = useState<string>();
  const detailQuery = useEssTrainingDetail(selectedProgramId);
  const items = trainingListQuery.data?.items ?? [];

  useEffect(() => {
    if (!selectedProgramId && items.length > 0) {
      setSelectedProgramId(items[0].programId);
    }
  }, [items, selectedProgramId]);

  const columns: Column<ESSTrainingProgram>[] = [
    { key: 'title', header: 'Program' },
    { key: 'category', header: 'Category' },
    { key: 'trainerName', header: 'Trainer' },
    {
      key: 'schedule',
      header: 'Schedule',
      render: (row) => (
        <div className="space-y-1">
          <DateDisplay date={row.startDate} />
          <div className="text-xs text-muted-foreground">{row.durationHours} hours</div>
        </div>
      ),
      sortable: true,
      sortValue: (row) => row.startDate,
    },
    {
      key: 'nominationStatus',
      header: 'Nomination',
      render: (row) => <StatusPill type="application" status={row.nominationStatus} />,
    },
    {
      key: 'feedbackSubmitted',
      header: 'Feedback',
      render: (row) => (
        <StatusPill type="application" status={row.feedbackSubmitted ? 'SUBMITTED' : 'PENDING'} />
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Training & Learning"
        subtitle="Track nominations, attendance, completion history, and submitted feedback."
      />

      <div className="grid gap-4 md:grid-cols-4">
        <TrainingMetric
          title="Completed Programs"
          value={trainingListQuery.data?.summary.completedPrograms ?? 0}
          subtitle="Programs attended and closed"
        />
        <TrainingMetric
          title="Upcoming Programs"
          value={trainingListQuery.data?.summary.upcomingPrograms ?? 0}
          subtitle="Confirmed or nominated"
        />
        <TrainingMetric
          title="Feedback Pending"
          value={trainingListQuery.data?.summary.feedbackPending ?? 0}
          subtitle="Attended programs awaiting feedback"
        />
        <TrainingMetric
          title="Hours Completed"
          value={trainingListQuery.data?.summary.totalHoursCompleted ?? 0}
          subtitle="Training hours completed"
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <DataTable
          data={items}
          columns={columns}
          getRowId={(row) => row.programId}
          isLoading={trainingListQuery.isLoading}
          error={trainingListQuery.error}
          onRetry={() => void trainingListQuery.refetch()}
          emptyTitle="No nominated programs"
          emptySubtitle="Training nominations from HR will appear here."
          onRowClick={(row) => setSelectedProgramId(row.programId)}
          rowClassName={(row) => (row.programId === selectedProgramId ? 'bg-muted/40' : undefined)}
        />

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Program Detail</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {!selectedProgramId ? (
              <p className="text-sm text-muted-foreground">
                Select a nominated program to view the schedule, feedback, and completion record.
              </p>
            ) : detailQuery.isLoading ? (
              <p className="text-sm text-muted-foreground">Loading program detail…</p>
            ) : detailQuery.isError ? (
              <p className="text-sm text-destructive">Unable to load training detail.</p>
            ) : detailQuery.data ? (
              <>
                <div>
                  <h3 className="font-semibold">{detailQuery.data.title}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {detailQuery.data.description}
                  </p>
                </div>
                <div className="grid gap-3 text-sm md:grid-cols-2 xl:grid-cols-1">
                  <div>
                    <p className="text-muted-foreground">Program Code</p>
                    <p className="font-medium">{detailQuery.data.programCode}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Mode</p>
                    <p className="font-medium">{detailQuery.data.mode}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Trainer</p>
                    <p className="font-medium">{detailQuery.data.trainerName}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Schedule</p>
                    <p className="font-medium">
                      <DateDisplay date={detailQuery.data.startDate} /> to{' '}
                      <DateDisplay date={detailQuery.data.endDate} />
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Location</p>
                    <p className="font-medium">{detailQuery.data.location}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Nomination Status</p>
                    <div className="mt-1">
                      <StatusPill type="application" status={detailQuery.data.nominationStatus} />
                    </div>
                  </div>
                </div>
                {detailQuery.data.feedback ? (
                  <Card className="bg-muted/30">
                    <CardContent className="space-y-2 pt-4 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Feedback Rating</span>
                        <span className="font-medium">
                          {detailQuery.data.feedback.overallRating}/5
                        </span>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Strengths</p>
                        <p>{detailQuery.data.feedback.strengths || '—'}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Improvements</p>
                        <p>{detailQuery.data.feedback.improvements || '—'}</p>
                      </div>
                    </CardContent>
                  </Card>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Feedback has not been submitted for this program yet.
                  </p>
                )}
              </>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
