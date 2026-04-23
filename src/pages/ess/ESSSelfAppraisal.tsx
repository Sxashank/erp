import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { Slider } from '@/components/ui/slider';
import { Separator } from '@/components/ui/separator';
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

// Mock data - Appraisal Cycle
const appraisalCycle = {
  id: '1',
  name: 'Annual Appraisal 2024-25',
  period: 'April 2024 - March 2025',
  selfAppraisalDeadline: '2025-03-15',
  status: 'SELF_APPRAISAL',
  daysRemaining: 58,
};

// Mock data - Goals for appraisal
const goalsForAppraisal = [
  {
    id: '1',
    title: 'Deliver Project Alpha on time',
    weight: 30,
    targetDescription: 'Successfully deliver all milestones of Project Alpha within budget and timeline',
    achievement: 70,
    selfRating: 4,
    selfComments: '',
    evidence: 'Phase 1 & 2 completed on time. Phase 3 in progress.',
  },
  {
    id: '2',
    title: 'Complete AWS Certification',
    weight: 20,
    targetDescription: 'Achieve AWS Solutions Architect Associate certification',
    achievement: 35,
    selfRating: 3,
    selfComments: '',
    evidence: 'Online course 70% complete. Exam scheduled for Q2.',
  },
  {
    id: '3',
    title: 'Mentor 2 Junior Developers',
    weight: 15,
    targetDescription: 'Provide guidance and mentorship to junior team members',
    achievement: 40,
    selfRating: 4,
    selfComments: '',
    evidence: 'Weekly 1:1 sessions established. Code review sessions ongoing.',
  },
  {
    id: '4',
    title: 'Improve Code Quality',
    weight: 20,
    targetDescription: 'Achieve 90%+ code coverage and reduce bugs by 30%',
    achievement: 60,
    selfRating: 3,
    selfComments: '',
    evidence: 'Code coverage improved from 65% to 82%. Bug count reduced by 20%.',
  },
  {
    id: '5',
    title: 'Client Satisfaction Score',
    weight: 15,
    targetDescription: 'Achieve average client satisfaction score of 4.5+',
    achievement: 85,
    selfRating: 5,
    selfComments: '',
    evidence: 'Current average score: 4.6. Received positive feedback from 3 clients.',
  },
];

// Mock data - Competencies
const competencies = [
  { id: '1', name: 'Technical Skills', description: 'Proficiency in required technical skills', selfRating: 4, selfComments: '' },
  { id: '2', name: 'Problem Solving', description: 'Ability to analyze and solve complex problems', selfRating: 4, selfComments: '' },
  { id: '3', name: 'Communication', description: 'Effective verbal and written communication', selfRating: 3, selfComments: '' },
  { id: '4', name: 'Teamwork', description: 'Collaboration and contribution to team success', selfRating: 5, selfComments: '' },
  { id: '5', name: 'Initiative', description: 'Proactively identifying and acting on opportunities', selfRating: 4, selfComments: '' },
  { id: '6', name: 'Time Management', description: 'Effectively managing time and meeting deadlines', selfRating: 4, selfComments: '' },
];

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
