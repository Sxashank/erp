import { useEffect, useMemo, useState } from 'react';

import { EmptyState } from '@/components/common/EmptyState';
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
import { useEssSelfAppraisalPacket, useSubmitEssSelfAppraisal } from '@/hooks/ess/useEssOperations';
import type { ESSPerformanceGoal, ESSPerformanceSelfAppraisalPayload } from '@/services/essApi';

interface GoalFormState {
  selfRating: string;
  selfProgress: string;
  selfComments: string;
  achievementValue: string;
}

export default function ESSSelfAppraisal() {
  const packetQuery = useEssSelfAppraisalPacket();
  const submitMutation = useSubmitEssSelfAppraisal();
  const appraisal = packetQuery.data?.appraisal ?? null;
  const goals = appraisal?.goals ?? [];

  const [goalState, setGoalState] = useState<Record<string, GoalFormState>>({});
  const [competencyRating, setCompetencyRating] = useState('3');
  const [selfSummary, setSelfSummary] = useState('');
  const [selfAchievements, setSelfAchievements] = useState('');
  const [selfChallenges, setSelfChallenges] = useState('');
  const [selfDevelopmentAreas, setSelfDevelopmentAreas] = useState('');
  const [employeeComments, setEmployeeComments] = useState('');

  useEffect(() => {
    if (!appraisal) return;
    const nextGoalState: Record<string, GoalFormState> = {};
    for (const goal of appraisal.goals) {
      nextGoalState[goal.id] = {
        selfRating: String(goal.selfRating ?? 3),
        selfProgress: String(goal.progressPercent ?? 0),
        selfComments: goal.selfComments ?? '',
        achievementValue: goal.achievementValue ?? '',
      };
    }
    setGoalState(nextGoalState);
    setCompetencyRating(String(appraisal.appraisal.competencyRating ?? 3));
    setSelfSummary(appraisal.appraisal.selfSummary ?? '');
    setSelfAchievements(appraisal.appraisal.selfAchievements ?? '');
    setSelfChallenges(appraisal.appraisal.selfChallenges ?? '');
    setSelfDevelopmentAreas(appraisal.appraisal.selfDevelopmentAreas ?? '');
    setEmployeeComments(appraisal.appraisal.employeeComments ?? '');
  }, [appraisal]);

  const weightedGoalRating = useMemo(() => {
    if (goals.length === 0) return 0;
    return goals.reduce((sum, goal) => {
      const rating = Number(goalState[goal.id]?.selfRating ?? goal.selfRating ?? 0);
      return sum + (rating * goal.weightage) / 100;
    }, 0);
  }, [goals, goalState]);

  const canSubmit =
    appraisal?.appraisal.status === 'SELF_APPRAISAL' &&
    goals.length > 0 &&
    goals.every((goal) => {
      const current = goalState[goal.id];
      return (
        current &&
        current.selfComments.trim().length >= 10 &&
        Number(current.selfRating) >= 1 &&
        Number(current.selfProgress) >= 0
      );
    }) &&
    selfSummary.trim().length >= 20 &&
    selfAchievements.trim().length >= 20 &&
    selfDevelopmentAreas.trim().length >= 10;

  const updateGoal = (goalId: string, patch: Partial<GoalFormState>) => {
    setGoalState((prev) => ({
      ...prev,
      [goalId]: {
        ...prev[goalId],
        ...patch,
      },
    }));
  };

  const handleSubmit = async () => {
    if (!canSubmit) return;
    const payload: ESSPerformanceSelfAppraisalPayload = {
      goals: goals.map((goal) => ({
        goalId: goal.id,
        selfRating: Number(goalState[goal.id].selfRating),
        selfProgress: Number(goalState[goal.id].selfProgress),
        selfComments: goalState[goal.id].selfComments,
        achievementValue: goalState[goal.id].achievementValue || undefined,
      })),
      competencyRating: Number(competencyRating),
      selfSummary,
      selfAchievements,
      selfChallenges: selfChallenges || undefined,
      selfDevelopmentAreas,
      employeeComments: employeeComments || undefined,
    };
    await submitMutation.mutateAsync(payload);
    void packetQuery.refetch();
  };

  const renderGoalCard = (goal: ESSPerformanceGoal) => {
    const current = goalState[goal.id];
    return (
      <Card key={goal.id}>
        <CardHeader>
          <CardTitle className="flex items-center justify-between gap-4 text-base">
            <span>{goal.title}</span>
            <div className="flex items-center gap-2">
              <StatusPill type="application" status={goal.status} />
              <span className="text-sm text-muted-foreground">{goal.weightage}%</span>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div className="space-y-3">
            <div>
              <p className="text-sm text-muted-foreground">Description</p>
              <p className="text-sm">{goal.description || '—'}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Target Value</p>
              <p className="text-sm">{goal.targetValue || '—'}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Measurement Criteria</p>
              <p className="text-sm">{goal.measurementCriteria || '—'}</p>
            </div>
          </div>
          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label>Self Rating</Label>
                <Select
                  value={current?.selfRating ?? '3'}
                  onValueChange={(value) => updateGoal(goal.id, { selfRating: value })}
                  disabled={appraisal?.appraisal.status !== 'SELF_APPRAISAL'}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select rating" />
                  </SelectTrigger>
                  <SelectContent>
                    {[1, 2, 3, 4, 5].map((rating) => (
                      <SelectItem key={rating} value={String(rating)}>
                        {rating}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Progress (%)</Label>
                <Input
                  type="number"
                  min={0}
                  max={100}
                  value={current?.selfProgress ?? '0'}
                  onChange={(event) => updateGoal(goal.id, { selfProgress: event.target.value })}
                  disabled={appraisal?.appraisal.status !== 'SELF_APPRAISAL'}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Achievement Value</Label>
              <Input
                value={current?.achievementValue ?? ''}
                onChange={(event) => updateGoal(goal.id, { achievementValue: event.target.value })}
                disabled={appraisal?.appraisal.status !== 'SELF_APPRAISAL'}
              />
            </div>
            <div className="space-y-2">
              <Label>Comments</Label>
              <Textarea
                value={current?.selfComments ?? ''}
                onChange={(event) => updateGoal(goal.id, { selfComments: event.target.value })}
                disabled={appraisal?.appraisal.status !== 'SELF_APPRAISAL'}
                rows={4}
              />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Self Appraisal"
        subtitle="Complete your self-appraisal using the live goal packet from the active appraisal cycle."
      />

      {!appraisal && !packetQuery.isLoading ? (
        <EmptyState
          title="No active self-appraisal"
          subtitle="HR has not yet opened a self-appraisal stage for your current cycle."
        />
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-muted-foreground">Cycle</p>
                <p className="mt-2 text-xl font-semibold">{appraisal?.cycle.name ?? '—'}</p>
                <p className="mt-1 text-xs text-muted-foreground">{appraisal?.cycle.cycleType}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-muted-foreground">Stage</p>
                <div className="mt-2">
                  {appraisal ? (
                    <StatusPill type="application" status={appraisal.appraisal.status} />
                  ) : null}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Current employee appraisal status
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-muted-foreground">Goals</p>
                <p className="mt-2 text-3xl font-semibold">{goals.length}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {appraisal?.employee.completedGoals ?? 0} completed
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-muted-foreground">Weighted Goal Rating</p>
                <p className="mt-2 text-3xl font-semibold">{weightedGoalRating.toFixed(2)}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Computed from current self ratings
                </p>
              </CardContent>
            </Card>
          </div>

          {goals.map(renderGoalCard)}

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Overall Self Appraisal</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label>Competency Rating</Label>
                <Select
                  value={competencyRating}
                  onValueChange={setCompetencyRating}
                  disabled={appraisal?.appraisal.status !== 'SELF_APPRAISAL'}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select rating" />
                  </SelectTrigger>
                  <SelectContent>
                    {[1, 2, 3, 4, 5].map((rating) => (
                      <SelectItem key={rating} value={String(rating)}>
                        {rating}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Employee Comments</Label>
                <Textarea
                  value={employeeComments}
                  onChange={(event) => setEmployeeComments(event.target.value)}
                  disabled={appraisal?.appraisal.status !== 'SELF_APPRAISAL'}
                  rows={2}
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label>Performance Summary</Label>
                <Textarea
                  value={selfSummary}
                  onChange={(event) => setSelfSummary(event.target.value)}
                  disabled={appraisal?.appraisal.status !== 'SELF_APPRAISAL'}
                  rows={4}
                />
              </div>
              <div className="space-y-2">
                <Label>Key Achievements</Label>
                <Textarea
                  value={selfAchievements}
                  onChange={(event) => setSelfAchievements(event.target.value)}
                  disabled={appraisal?.appraisal.status !== 'SELF_APPRAISAL'}
                  rows={4}
                />
              </div>
              <div className="space-y-2">
                <Label>Challenges</Label>
                <Textarea
                  value={selfChallenges}
                  onChange={(event) => setSelfChallenges(event.target.value)}
                  disabled={appraisal?.appraisal.status !== 'SELF_APPRAISAL'}
                  rows={4}
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label>Development Areas</Label>
                <Textarea
                  value={selfDevelopmentAreas}
                  onChange={(event) => setSelfDevelopmentAreas(event.target.value)}
                  disabled={appraisal?.appraisal.status !== 'SELF_APPRAISAL'}
                  rows={4}
                />
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button
              onClick={() => void handleSubmit()}
              disabled={!canSubmit || submitMutation.isPending}
            >
              {submitMutation.isPending ? 'Submitting…' : 'Submit Self Appraisal'}
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
