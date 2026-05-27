import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { StatusPill } from '@/components/common/StatusPill';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import {
  useCalibrateAppraisal,
  useCycleEmployees,
  useEmployeePerformanceDetail,
  usePerformanceCycles,
  useSubmitManagerReview,
} from '@/hooks/hris/usePerformance';
import { useToast } from '@/hooks/use-toast';
import type {
  AppraisalCycleListItem,
  PerformanceEmployeeSummary,
  PerformanceGoal,
  PerformanceManagerReviewPayload,
} from '@/services/hris/performanceApi';

interface GoalReviewState {
  goalId: string;
  managerRating: number;
  managerComments: string;
  finalRating: number;
}

function SummaryCard({
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

function ReviewGoalCard({
  goal,
  state,
  readOnly,
  onChange,
}: {
  goal: PerformanceGoal;
  state: GoalReviewState | undefined;
  readOnly: boolean;
  onChange: (goalId: string, patch: Partial<GoalReviewState>) => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{goal.title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 md:grid-cols-4">
          <div>
            <Label className="text-muted-foreground">Weightage</Label>
            <p className="mt-1 font-medium">{goal.weightage}%</p>
          </div>
          <div>
            <Label className="text-muted-foreground">Due Date</Label>
            <p className="mt-1 font-medium">
              <DateDisplay date={goal.dueDate ?? null} />
            </p>
          </div>
          <div>
            <Label className="text-muted-foreground">Self Rating</Label>
            <p className="mt-1 font-medium">{goal.selfRating ?? '—'}</p>
          </div>
          <div>
            <Label className="text-muted-foreground">Progress</Label>
            <p className="mt-1 font-medium">{goal.progressPercent}%</p>
          </div>
        </div>

        <div className="space-y-2">
          <Label className="text-muted-foreground">Self Comments</Label>
          <p className="text-sm">{goal.selfComments || '—'}</p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <div className="space-y-2">
            <Label>Manager Rating</Label>
            <Select
              value={String(state?.managerRating ?? goal.managerRating ?? 0)}
              onValueChange={(value) =>
                onChange(goal.id, { managerRating: Number(value), finalRating: Number(value) })
              }
              disabled={readOnly}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select rating" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">1</SelectItem>
                <SelectItem value="2">2</SelectItem>
                <SelectItem value="3">3</SelectItem>
                <SelectItem value="4">4</SelectItem>
                <SelectItem value="5">5</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Final Goal Rating</Label>
            <Select
              value={String(state?.finalRating ?? goal.finalRating ?? goal.managerRating ?? 0)}
              onValueChange={(value) => onChange(goal.id, { finalRating: Number(value) })}
              disabled={readOnly}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select final rating" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">1</SelectItem>
                <SelectItem value="2">2</SelectItem>
                <SelectItem value="3">3</SelectItem>
                <SelectItem value="4">4</SelectItem>
                <SelectItem value="5">5</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2 md:col-span-2 xl:col-span-1">
            <Label>Status</Label>
            <div className="pt-2">
              <StatusPill type="application" status={goal.status} />
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <Label>Manager Comments</Label>
          <Textarea
            rows={4}
            value={state?.managerComments ?? goal.managerComments ?? ''}
            onChange={(event) => onChange(goal.id, { managerComments: event.target.value })}
            disabled={readOnly}
          />
        </div>
      </CardContent>
    </Card>
  );
}

export default function ManagerReview() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { cycleId, employeeId } = useParams();
  const [cycleSelectionId, setCycleSelectionId] = useState(cycleId ?? '');

  const cyclesQuery = usePerformanceCycles({ skip: 0, limit: 100 });
  const employeesQuery = useCycleEmployees(cycleId);
  const employeeSelectionQuery = useCycleEmployees(cycleSelectionId || undefined);
  const detailQuery = useEmployeePerformanceDetail(cycleId, employeeId);
  const submitReviewMutation = useSubmitManagerReview(cycleId ?? '', employeeId ?? '');
  const calibrateMutation = useCalibrateAppraisal(cycleId ?? '', employeeId ?? '');

  const [goalReviews, setGoalReviews] = useState<Record<string, GoalReviewState>>({});
  const [competencyRating, setCompetencyRating] = useState('3');
  const [managerSummary, setManagerSummary] = useState('');
  const [managerAchievements, setManagerAchievements] = useState('');
  const [managerImprovements, setManagerImprovements] = useState('');
  const [managerRecommendations, setManagerRecommendations] = useState('');
  const [calibratedRating, setCalibratedRating] = useState('3');
  const [calibrationNotes, setCalibrationNotes] = useState('');
  const [finalGrade, setFinalGrade] = useState('');

  useEffect(() => {
    const detail = detailQuery.data;
    if (!detail) return;
    setGoalReviews(
      Object.fromEntries(
        detail.goals.map((goal) => [
          goal.id,
          {
            goalId: goal.id,
            managerRating: goal.managerRating ?? goal.selfRating ?? 0,
            managerComments: goal.managerComments ?? '',
            finalRating: goal.finalRating ?? goal.managerRating ?? goal.selfRating ?? 0,
          },
        ]),
      ),
    );
    setCompetencyRating(String(detail.appraisal.competencyRating ?? 3));
    setManagerSummary(detail.appraisal.managerSummary ?? '');
    setManagerAchievements(detail.appraisal.managerAchievements ?? '');
    setManagerImprovements(detail.appraisal.managerImprovements ?? '');
    setManagerRecommendations(detail.appraisal.managerRecommendations ?? '');
    setCalibratedRating(
      String(detail.appraisal.calibratedRating ?? detail.appraisal.overallRating ?? 3),
    );
    setCalibrationNotes(detail.appraisal.calibrationNotes ?? '');
    setFinalGrade(detail.appraisal.calibratedGrade ?? detail.appraisal.finalGrade ?? '');
  }, [detailQuery.data]);

  const selectedCycle = useMemo(
    () => cyclesQuery.data?.items.find((item) => item.id === cycleId),
    [cycleId, cyclesQuery.data],
  );
  const employeeOptions = useMemo(
    () => (employeesQuery.data ?? []) as PerformanceEmployeeSummary[],
    [employeesQuery.data],
  );
  const detail = detailQuery.data;
  const isCalibrationStage = detail?.appraisal.status === 'CALIBRATION';
  const reviewReadOnly = detail?.appraisal.status !== 'MANAGER_REVIEW';

  const handleGoalChange = (goalId: string, patch: Partial<GoalReviewState>) => {
    setGoalReviews((current) => ({
      ...current,
      [goalId]: {
        ...(current[goalId] ?? {
          goalId,
          managerRating: 0,
          managerComments: '',
          finalRating: 0,
        }),
        ...patch,
      },
    }));
  };

  const handleSubmitReview = async () => {
    if (!detail) return;
    const payload: PerformanceManagerReviewPayload = {
      goals: detail.goals.map((goal) => ({
        goalId: goal.id,
        managerRating: goalReviews[goal.id]?.managerRating ?? 0,
        managerComments: goalReviews[goal.id]?.managerComments ?? '',
        finalRating: goalReviews[goal.id]?.finalRating || undefined,
      })),
      competencyRating: Number(competencyRating),
      managerSummary,
      managerAchievements: managerAchievements || undefined,
      managerImprovements,
      managerRecommendations: managerRecommendations || undefined,
    };
    await submitReviewMutation.mutateAsync(payload);
    toast({ title: 'Manager review submitted' });
  };

  const handleSubmitCalibration = async () => {
    if (!detail) return;
    await calibrateMutation.mutateAsync({
      calibratedRating: Number(calibratedRating),
      calibrationNotes: calibrationNotes || undefined,
      finalGrade: finalGrade || undefined,
    });
    toast({ title: 'Calibration completed' });
  };

  if (!cycleId || !employeeId) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Manager Review"
          subtitle="Select an appraisal cycle and employee packet to continue."
          breadcrumbs={[
            { label: 'Performance Cycles', to: '/admin/hris/performance/cycles' },
            { label: 'Manager Review' },
          ]}
        />
        <Card>
          <CardContent className="grid gap-4 pt-6 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Select cycle</Label>
              <Select value={cycleSelectionId} onValueChange={setCycleSelectionId}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a cycle" />
                </SelectTrigger>
                <SelectContent>
                  {(cyclesQuery.data?.items ?? []).map((cycle: AppraisalCycleListItem) => (
                    <SelectItem key={cycle.id} value={cycle.id}>
                      {cycle.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Select employee</Label>
              <Select
                value=""
                onValueChange={(value) =>
                  navigate(`/admin/hris/performance/manager-review/${cycleSelectionId}/${value}`)
                }
                disabled={!cycleSelectionId}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Choose an employee packet" />
                </SelectTrigger>
                <SelectContent>
                  {(employeeSelectionQuery.data ?? []).map((employee) => (
                    <SelectItem key={employee.employeeId} value={employee.employeeId}>
                      {employee.employeeName} ({employee.employeeCode})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (detailQuery.isError) {
    return <ErrorState error={detailQuery.error} onRetry={() => void detailQuery.refetch()} />;
  }

  if (!detail) {
    return (
      <EmptyState
        title="No manager review packet"
        subtitle="This employee does not currently have a manager review packet for the selected cycle."
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Manager Review"
        subtitle={selectedCycle?.name ?? detail.cycle.name}
        breadcrumbs={[
          { label: 'Performance Cycles', to: '/admin/hris/performance/cycles' },
          { label: 'Manager Review' },
        ]}
        actions={
          <div className="flex gap-2">
            <Select
              value={cycleId}
              onValueChange={(value) =>
                navigate(`/admin/hris/performance/manager-review/${value}/${employeeId}`)
              }
            >
              <SelectTrigger className="w-[260px]">
                <SelectValue placeholder="Select cycle" />
              </SelectTrigger>
              <SelectContent>
                {(cyclesQuery.data?.items ?? []).map((cycle: AppraisalCycleListItem) => (
                  <SelectItem key={cycle.id} value={cycle.id}>
                    {cycle.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={employeeId}
              onValueChange={(value) =>
                navigate(`/admin/hris/performance/manager-review/${cycleId}/${value}`)
              }
            >
              <SelectTrigger className="w-[320px]">
                <SelectValue placeholder="Select employee" />
              </SelectTrigger>
              <SelectContent>
                {employeeOptions.map((employee) => (
                  <SelectItem key={employee.employeeId} value={employee.employeeId}>
                    {employee.employeeName} ({employee.employeeCode})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {isCalibrationStage ? (
              <Button
                onClick={() => void handleSubmitCalibration()}
                disabled={calibrateMutation.isPending}
              >
                {calibrateMutation.isPending ? 'Calibrating…' : 'Complete Calibration'}
              </Button>
            ) : (
              <Button
                onClick={() => void handleSubmitReview()}
                disabled={reviewReadOnly || submitReviewMutation.isPending}
              >
                {submitReviewMutation.isPending ? 'Submitting…' : 'Submit Review'}
              </Button>
            )}
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <SummaryCard
          title="Employee"
          value={detail.employee.employeeName}
          subtitle={detail.employee.employeeCode}
        />
        <SummaryCard
          title="Current Status"
          value={detail.appraisal.status}
          subtitle={detail.employee.reviewerName ?? 'Reviewer not assigned'}
        />
        <SummaryCard
          title="Self Appraisal Date"
          value={detail.appraisal.selfAppraisalDate ?? '—'}
          subtitle="Employee submission timestamp"
        />
        <SummaryCard
          title="Manager Review Deadline"
          value={detail.cycle.managerReviewEnd ?? '—'}
          subtitle="Cycle manager-review deadline"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Employee Self Appraisal Summary</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div>
            <Label className="text-muted-foreground">Self Summary</Label>
            <p className="mt-1 text-sm">{detail.appraisal.selfSummary || '—'}</p>
          </div>
          <div>
            <Label className="text-muted-foreground">Key Achievements</Label>
            <p className="mt-1 text-sm">{detail.appraisal.selfAchievements || '—'}</p>
          </div>
          <div>
            <Label className="text-muted-foreground">Challenges</Label>
            <p className="mt-1 text-sm">{detail.appraisal.selfChallenges || '—'}</p>
          </div>
          <div>
            <Label className="text-muted-foreground">Development Areas</Label>
            <p className="mt-1 text-sm">{detail.appraisal.selfDevelopmentAreas || '—'}</p>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-4">
        {detail.goals.map((goal) => (
          <ReviewGoalCard
            key={goal.id}
            goal={goal}
            state={goalReviews[goal.id]}
            readOnly={reviewReadOnly}
            onChange={handleGoalChange}
          />
        ))}
      </div>

      {!isCalibrationStage ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Manager Assessment</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {reviewReadOnly && (
              <p className="text-sm text-muted-foreground">
                This packet is currently in <strong>{detail.appraisal.status}</strong>. Review
                fields remain visible, but they can only be submitted while the packet is in the
                manager-review stage.
              </p>
            )}
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label>Competency Rating</Label>
                <Select
                  value={competencyRating}
                  onValueChange={setCompetencyRating}
                  disabled={reviewReadOnly}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select rating" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">1</SelectItem>
                    <SelectItem value="2">2</SelectItem>
                    <SelectItem value="3">3</SelectItem>
                    <SelectItem value="4">4</SelectItem>
                    <SelectItem value="5">5</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Employee Review Date</Label>
                <div className="pt-2">
                  <DateDisplay date={detail.appraisal.selfAppraisalDate ?? null} />
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Manager Summary</Label>
              <Textarea
                rows={4}
                value={managerSummary}
                onChange={(event) => setManagerSummary(event.target.value)}
                disabled={reviewReadOnly}
              />
            </div>
            <div className="space-y-2">
              <Label>Manager View of Achievements</Label>
              <Textarea
                rows={4}
                value={managerAchievements}
                onChange={(event) => setManagerAchievements(event.target.value)}
                disabled={reviewReadOnly}
              />
            </div>
            <div className="space-y-2">
              <Label>Improvement Areas</Label>
              <Textarea
                rows={4}
                value={managerImprovements}
                onChange={(event) => setManagerImprovements(event.target.value)}
                disabled={reviewReadOnly}
              />
            </div>
            <div className="space-y-2">
              <Label>Recommendations</Label>
              <Textarea
                rows={4}
                value={managerRecommendations}
                onChange={(event) => setManagerRecommendations(event.target.value)}
                disabled={reviewReadOnly}
              />
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Calibration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label>Calibrated Rating</Label>
                <Input
                  type="number"
                  min={1}
                  max={5}
                  step="0.01"
                  value={calibratedRating}
                  onChange={(event) => setCalibratedRating(event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Final Grade</Label>
                <Input value={finalGrade} onChange={(event) => setFinalGrade(event.target.value)} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Calibration Notes</Label>
              <Textarea
                rows={4}
                value={calibrationNotes}
                onChange={(event) => setCalibrationNotes(event.target.value)}
              />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
