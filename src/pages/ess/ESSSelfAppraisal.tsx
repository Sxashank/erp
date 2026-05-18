import {
  ClipboardCheck,
  Save,
  Send,
  Target,
  Star,
  CheckCircle,
  AlertCircle,
  TrendingUp,
} from 'lucide-react';
import { useState } from 'react';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Slider } from '@/components/ui/slider';
import { Textarea } from '@/components/ui/textarea';

interface AppraisalCycle {
  id: string;
  name: string;
  period: string;
  selfAppraisalDeadline: string;
  status: string;
  daysRemaining: number;
}

interface AppraisalGoal {
  id: string;
  title: string;
  weight: number;
  targetDescription: string;
  achievement: number;
  selfRating: number;
  selfComments: string;
  evidence?: string;
}

interface CompetencyRating {
  id: string;
  name: string;
  description: string;
  selfRating: number;
  selfComments: string;
}

const appraisalCycle: AppraisalCycle | null = null;
const goalsForAppraisal: AppraisalGoal[] = [];
const competencies: CompetencyRating[] = [];

const ratingLabels = {
  1: 'Needs Significant Improvement',
  2: 'Needs Improvement',
  3: 'Meets Expectations',
  4: 'Exceeds Expectations',
  5: 'Outstanding',
};

export default function ESSSelfAppraisal() {
  const [goals, setGoals] = useState(goalsForAppraisal);
  const [competencyRatings, setCompetencyRatings] = useState(competencies);
  const [overallComments, setOverallComments] = useState('');
  const [achievements, setAchievements] = useState('');
  const [challenges, setChallenges] = useState('');
  const [developmentAreas, setDevelopmentAreas] = useState('');
  const [careerAspirations, setCareerAspirations] = useState('');

  const updateGoalRating = (goalId: string, rating: number) => {
    setGoals(goals.map(g => g.id === goalId ? { ...g, selfRating: rating } : g));
  };

  const updateGoalComments = (goalId: string, comments: string) => {
    setGoals(goals.map(g => g.id === goalId ? { ...g, selfComments: comments } : g));
  };

  const updateCompetencyRating = (compId: string, rating: number) => {
    setCompetencyRatings(competencyRatings.map(c => c.id === compId ? { ...c, selfRating: rating } : c));
  };

  const updateCompetencyComments = (compId: string, comments: string) => {
    setCompetencyRatings(competencyRatings.map(c => c.id === compId ? { ...c, selfComments: comments } : c));
  };

  const calculateWeightedScore = () => {
    return goals.reduce((sum, g) => sum + (g.selfRating * g.weight / 100), 0);
  };

  const calculateCompetencyAverage = () => {
    const sum = competencyRatings.reduce((s, c) => s + c.selfRating, 0);
    return (sum / competencyRatings.length).toFixed(1);
  };

  const getRatingColor = (rating: number) => {
    if (rating >= 4) return 'text-green-600';
    if (rating >= 3) return 'text-blue-600';
    return 'text-orange-600';
  };

  if (!appraisalCycle) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Self Appraisal"
          subtitle="Complete your self assessment"
        />
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            Self-appraisal data is pending ESS performance endpoints. Appraisal cycles, goals, and competency ratings will appear after HRIS performance APIs are exposed to ESS.
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Self Appraisal"
        subtitle={`${appraisalCycle.name} | ${appraisalCycle.period}`}
        actions={
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-sm text-muted-foreground">Deadline</div>
              <div className="font-medium flex items-center gap-1">
                <AlertCircle className="h-4 w-4 text-orange-500" />
                {appraisalCycle.daysRemaining} days remaining
              </div>
            </div>
            <Badge variant="secondary" className="bg-blue-100 text-blue-800">
              Self Appraisal Phase
            </Badge>
          </div>
        }
      />

      {/* Summary Card */}
      <Card className="bg-gradient-to-r from-blue-50 to-purple-50">
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
            <div>
              <div className="text-3xl font-bold text-blue-600">{calculateWeightedScore().toFixed(1)}</div>
              <div className="text-sm text-muted-foreground">Weighted Goal Score</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-purple-600">{calculateCompetencyAverage()}</div>
              <div className="text-sm text-muted-foreground">Avg Competency Rating</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-green-600">
                {Math.round((calculateWeightedScore() + parseFloat(calculateCompetencyAverage())) / 2 * 20)}%
              </div>
              <div className="text-sm text-muted-foreground">Overall Score</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Goals Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Goal Achievement
          </CardTitle>
          <CardDescription>Rate your achievement against each goal</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {goals.map((goal, index) => (
            <div key={goal.id} className="space-y-4">
              {index > 0 && <Separator />}
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium">{goal.title}</h4>
                    <Badge variant="outline">Weight: {goal.weight}%</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">{goal.targetDescription}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-sm text-muted-foreground">Achievement:</span>
                    <Progress value={goal.achievement} className="w-32" />
                    <span className="text-sm font-medium">{goal.achievement}%</span>
                  </div>
                  {goal.evidence && (
                    <p className="text-sm text-muted-foreground mt-1">
                      <strong>Evidence:</strong> {goal.evidence}
                    </p>
                  )}
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pl-4 border-l-2 border-muted">
                <div>
                  <label className="text-sm font-medium">Self Rating</label>
                  <div className="flex items-center gap-4 mt-2">
                    {[1, 2, 3, 4, 5].map((rating) => (
                      <button
                        key={rating}
                        type="button"
                        onClick={() => updateGoalRating(goal.id, rating)}
                        className={`p-2 rounded-full transition-colors ${
                          goal.selfRating >= rating
                            ? 'bg-yellow-400 text-yellow-900'
                            : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
                        }`}
                      >
                        <Star className="h-5 w-5" fill={goal.selfRating >= rating ? 'currentColor' : 'none'} />
                      </button>
                    ))}
                    <span className={`text-sm font-medium ${getRatingColor(goal.selfRating)}`}>
                      {ratingLabels[goal.selfRating as keyof typeof ratingLabels]}
                    </span>
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium">Comments</label>
                  <Textarea
                    value={goal.selfComments}
                    onChange={(e) => updateGoalComments(goal.id, e.target.value)}
                    placeholder="Add your comments..."
                    className="mt-2"
                    rows={2}
                  />
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Competencies Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Competency Assessment
          </CardTitle>
          <CardDescription>Rate yourself on core competencies</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {competencyRatings.map((comp, index) => (
            <div key={comp.id} className="space-y-3">
              {index > 0 && <Separator />}
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-medium">{comp.name}</h4>
                  <p className="text-sm text-muted-foreground">{comp.description}</p>
                </div>
                <div className="flex items-center gap-2">
                  {[1, 2, 3, 4, 5].map((rating) => (
                    <button
                      key={rating}
                      type="button"
                      onClick={() => updateCompetencyRating(comp.id, rating)}
                      className={`p-1.5 rounded-full transition-colors ${
                        comp.selfRating >= rating
                          ? 'bg-yellow-400 text-yellow-900'
                          : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
                      }`}
                    >
                      <Star className="h-4 w-4" fill={comp.selfRating >= rating ? 'currentColor' : 'none'} />
                    </button>
                  ))}
                </div>
              </div>
              <Textarea
                value={comp.selfComments}
                onChange={(e) => updateCompetencyComments(comp.id, e.target.value)}
                placeholder="Provide examples or comments..."
                rows={2}
              />
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Overall Comments Section */}
      <Card>
        <CardHeader>
          <CardTitle>Additional Comments</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">Key Achievements</label>
            <Textarea
              value={achievements}
              onChange={(e) => setAchievements(e.target.value)}
              placeholder="List your key achievements during this period..."
              className="mt-2"
              rows={3}
            />
          </div>
          <div>
            <label className="text-sm font-medium">Challenges Faced</label>
            <Textarea
              value={challenges}
              onChange={(e) => setChallenges(e.target.value)}
              placeholder="Describe any challenges you faced and how you overcame them..."
              className="mt-2"
              rows={3}
            />
          </div>
          <div>
            <label className="text-sm font-medium">Development Areas</label>
            <Textarea
              value={developmentAreas}
              onChange={(e) => setDevelopmentAreas(e.target.value)}
              placeholder="Areas where you would like to improve..."
              className="mt-2"
              rows={3}
            />
          </div>
          <div>
            <label className="text-sm font-medium">Career Aspirations</label>
            <Textarea
              value={careerAspirations}
              onChange={(e) => setCareerAspirations(e.target.value)}
              placeholder="Your career goals and aspirations..."
              className="mt-2"
              rows={3}
            />
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex justify-end gap-4">
        <Button variant="outline">
          <Save className="h-4 w-4 mr-2" />
          Save Draft
        </Button>
        <Button>
          <Send className="h-4 w-4 mr-2" />
          Submit Self Appraisal
        </Button>
      </div>
    </div>
  );
}
