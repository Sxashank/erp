import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';

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
  useCycleEmployees,
  useEmployeePerformanceDetail,
  usePerformanceCycles,
  useSubmitSelfAppraisal,
} from '@/hooks/hris/usePerformance';
import { useToast } from '@/hooks/use-toast';
import type {
  AppraisalCycleListItem,
  PerformanceEmployeeSummary,
  PerformanceGoal,
  PerformanceSelfAppraisalPayload,
} from '@/services/hris/performanceApi';

interface GoalSelfState {
  goalId: string;
  selfRating: number;
  selfProgress: number;
  selfComments: string;
  achievementValue: string;
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

function GoalCard({
  goal,
  state,
  readOnly,
  onChange,
}: {
  goal: PerformanceGoal;
  state: GoalSelfState | undefined;
  readOnly: boolean;
  onChange: (goalId: string, patch: Partial<GoalSelfState>) => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{goal.title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 md:grid-cols-4">
          <div>
            <Label className="text-muted-foreground">Category</Label>
            <p className="mt-1 font-medium">{goal.category || 'General'}</p>
          </div>
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
            <Label className="text-muted-foreground">Current Status</Label>
            <div className="mt-1">
              <StatusPill type="application" status={goal.status} />
            </div>
          </div>
        </div>
        {goal.description && (
          <div>
            <Label className="text-muted-foreground">Description</Label>
            <p className="mt-1 text-sm">{goal.description}</p>
          </div>
        )}
        <div>
          <Label className="text-muted-foreground">Measurement Criteria</Label>
          <p className="mt-1 text-sm">{goal.measurementCriteria || '—'}</p>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <div className="space-y-2">
            <Label>Self Rating</Label>
            <Select
              value={String(state?.selfRating ?? goal.selfRating ?? 0)}
              onValueChange={(value) => onChange(goal.id, { selfRating: Number(value) })}
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
            <Label>Progress (%)</Label>
            <Input
              type="number"
              min={0}
              max={100}
              value={state?.selfProgress ?? goal.progressPercent ?? 0}
              onChange={(event) => onChange(goal.id, { selfProgress: Number(event.target.value) })}
              disabled={readOnly}
            />
          </div>
          <div className="space-y-2">
            <Label>Achievement Value</Label>
            <Input
              value={state?.achievementValue ?? goal.achievementValue ?? ''}
              onChange={(event) => onChange(goal.id, { achievementValue: event.target.value })}
              disabled={readOnly}
            />
          </div>
        </div>
        <div className="space-y-2">
          <Label>Self Comments</Label>
          <Textarea
            rows={4}
            value={state?.selfComments ?? goal.selfComments ?? ''}
            onChange={(event) => onChange(goal.id, { selfComments: event.target.value })}
            disabled={readOnly}
          />
        </div>
      </CardContent>
    </Card>
  );
}

export default function SelfAppraisal() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { cycleId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const employeeId = searchParams.get('employeeId') ?? '';

  const cyclesQuery = usePerformanceCycles({ skip: 0, limit: 100 });
  const employeesQuery = useCycleEmployees(cycleId);
  const detailQuery = useEmployeePerformanceDetail(cycleId, employeeId || undefined);
  const submitSelfAppraisalMutation = useSubmitSelfAppraisal(cycleId ?? '', employeeId || '');

  const [goalStates, setGoalStates] = useState<Record<string, GoalSelfState>>({});
  const [competencyRating, setCompetencyRating] = useState('3');
  const [selfSummary, setSelfSummary] = useState('');
  const [selfAchievements, setSelfAchievements] = useState('');
  const [selfChallenges, setSelfChallenges] = useState('');
  const [selfDevelopmentAreas, setSelfDevelopmentAreas] = useState('');
  const [employeeComments, setEmployeeComments] = useState('');

  useEffect(() => {
    if (employeeId || !employeesQuery.data?.length) {
      return;
    }
    setSearchParams({ employeeId: employeesQuery.data[0].employeeId });
  }, [employeeId, employeesQuery.data, setSearchParams]);

  useEffect(() => {
    const detail = detailQuery.data;
    if (!detail) {
      return;
    }
    setGoalStates(
      Object.fromEntries(
        detail.goals.map((goal) => [
          goal.id,
          {
            goalId: goal.id,
            selfRating: goal.selfRating ?? 0,
            selfProgress: goal.progressPercent ?? 0,
            selfComments: goal.selfComments ?? '',
            achievementValue: goal.achievementValue ?? '',
          },
        ]),
      ),
    );
    setCompetencyRating(String(detail.appraisal.competencyRating ?? 3));
    setSelfSummary(detail.appraisal.selfSummary ?? '');
    setSelfAchievements(detail.appraisal.selfAchievements ?? '');
    setSelfChallenges(detail.appraisal.selfChallenges ?? '');
    setSelfDevelopmentAreas(detail.appraisal.selfDevelopmentAreas ?? '');
    setEmployeeComments(detail.appraisal.employeeComments ?? '');
  }, [detailQuery.data]);

  const employeeOptions = useMemo(
    () => (employeesQuery.data ?? []) as PerformanceEmployeeSummary[],
    [employeesQuery.data],
  );
  const selectedCycle = useMemo(
    () => cyclesQuery.data?.items.find((item) => item.id === cycleId),
    [cycleId, cyclesQuery.data],
  );

  if (!cycleId) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Self Appraisal"
          subtitle="Select an active performance cycle to manage employee self-appraisals."
          breadcrumbs={[
            { label: 'Performance Cycles', to: '/admin/hris/performance/cycles' },
            { label: 'Self Appraisal' },
          ]}
        />
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <Label>Select cycle</Label>
              <Select
                value=""
                onValueChange={(value) =>
                  navigate(`/admin/hris/performance/self-appraisal/${value}`)
                }
              >
                <SelectTrigger className="w-[320px]">
                  <SelectValue placeholder="Choose an appraisal cycle" />
                </SelectTrigger>
                <SelectContent>
                  {(cyclesQuery.data?.items ?? []).map((cycle: AppraisalCycleListItem) => (
                    <SelectItem key={cycle.id} value={cycle.id}>
                      {cycle.name} ({cycle.code})
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

  const detail = detailQuery.data;
  const readOnly = detail?.appraisal.status !== 'SELF_APPRAISAL';

  const handleGoalChange = (goalId: string, patch: Partial<GoalSelfState>) => {
    setGoalStates((current) => ({
      ...current,
      [goalId]: {
        ...(current[goalId] ?? {
          goalId,
          selfRating: 0,
          selfProgress: 0,
          selfComments: '',
          achievementValue: '',
        }),
        ...patch,
      },
    }));
  };

  const handleSubmit = async () => {
    if (!detail) return;
    const payload: PerformanceSelfAppraisalPayload = {
      goals: detail.goals.map((goal) => ({
        goalId: goal.id,
        selfRating: goalStates[goal.id]?.selfRating ?? 0,
        selfProgress: goalStates[goal.id]?.selfProgress ?? 0,
        selfComments: goalStates[goal.id]?.selfComments ?? '',
        achievementValue: goalStates[goal.id]?.achievementValue || undefined,
      })),
      competencyRating: Number(competencyRating),
      selfSummary,
      selfAchievements,
      selfChallenges: selfChallenges || undefined,
      selfDevelopmentAreas,
      employeeComments: employeeComments || undefined,
    };
    await submitSelfAppraisalMutation.mutateAsync(payload);
    toast({ title: 'Self appraisal submitted' });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Self Appraisal"
        subtitle={selectedCycle?.name ?? detail?.cycle.name ?? 'Appraisal cycle'}
        breadcrumbs={[
          { label: 'Performance Cycles', to: '/admin/hris/performance/cycles' },
          { label: 'Self Appraisal' },
        ]}
        actions={
          <div className="flex gap-2">
            <Select
              value={cycleId}
              onValueChange={(value) => navigate(`/admin/hris/performance/self-appraisal/${value}`)}
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
              onValueChange={(value) => setSearchParams({ employeeId: value })}
            >
              <SelectTrigger className="w-[300px]">
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
            <Button
              onClick={() => void handleSubmit()}
              disabled={readOnly || submitSelfAppraisalMutation.isPending || !detail}
            >
              {submitSelfAppraisalMutation.isPending ? 'Submitting…' : 'Submit Self Appraisal'}
            </Button>
          </div>
        }
      />

      {!detail ? (
        <EmptyState
          title="No employee packet selected"
          subtitle="Choose an employee packet from the self-appraisal queue."
        />
      ) : (
        <>
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
              title="Self Appraisal Deadline"
              value={detail.cycle.selfAppraisalEnd ?? '—'}
              subtitle="Cycle self-appraisal deadline"
            />
            <SummaryCard
              title="Goals in Packet"
              value={detail.goals.length}
              subtitle={`${detail.employee.submittedGoals} already submitted`}
            />
          </div>

          {readOnly && (
            <Card className="border-amber-200 bg-amber-50">
              <CardContent className="pt-6 text-sm text-amber-900">
                This packet is currently in <strong>{detail.appraisal.status}</strong>. The page
                remains visible for review, but submission is only enabled while the packet is in
                the self-appraisal stage.
              </CardContent>
            </Card>
          )}

          <div className="space-y-4">
            {detail.goals.map((goal) => (
              <GoalCard
                key={goal.id}
                goal={goal}
                state={goalStates[goal.id]}
                readOnly={readOnly}
                onChange={handleGoalChange}
              />
            ))}
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Overall Self Assessment</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Competency Rating</Label>
                  <Select
                    value={competencyRating}
                    onValueChange={setCompetencyRating}
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
                  <Label>Cycle Status</Label>
                  <div className="pt-2">
                    <StatusPill type="application" status={detail.cycle.status} />
                  </div>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Overall Summary</Label>
                <Textarea
                  rows={4}
                  value={selfSummary}
                  onChange={(event) => setSelfSummary(event.target.value)}
                  disabled={readOnly}
                />
              </div>
              <div className="space-y-2">
                <Label>Key Achievements</Label>
                <Textarea
                  rows={4}
                  value={selfAchievements}
                  onChange={(event) => setSelfAchievements(event.target.value)}
                  disabled={readOnly}
                />
              </div>
              <div className="space-y-2">
                <Label>Challenges Faced</Label>
                <Textarea
                  rows={4}
                  value={selfChallenges}
                  onChange={(event) => setSelfChallenges(event.target.value)}
                  disabled={readOnly}
                />
              </div>
              <div className="space-y-2">
                <Label>Development Areas</Label>
                <Textarea
                  rows={4}
                  value={selfDevelopmentAreas}
                  onChange={(event) => setSelfDevelopmentAreas(event.target.value)}
                  disabled={readOnly}
                />
              </div>
              <div className="space-y-2">
                <Label>Employee Comments</Label>
                <Textarea
                  rows={3}
                  value={employeeComments}
                  onChange={(event) => setEmployeeComments(event.target.value)}
                  disabled={readOnly}
                />
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
