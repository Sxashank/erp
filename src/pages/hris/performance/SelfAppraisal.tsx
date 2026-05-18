import { zodResolver } from '@hookform/resolvers/zod';
import {
  Target,
  Save,
  Send,
  CheckCircle,
  Star,
  FileText,
  MessageSquare,
  Award,
  TrendingUp,
  AlertCircle,
} from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';
import { z } from 'zod';

import { PageHeader } from '@/components/common/PageHeader';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Progress } from '@/components/ui/progress';
import { Slider } from '@/components/ui/slider';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { logger } from '@/lib/logger';
import { formatDate } from '@/lib/utils';

const selfAppraisalSchema = z.object({
  goals: z.array(
    z.object({
      goal_id: z.string(),
      self_rating: z.number().min(1).max(5),
      self_progress: z.number().min(0).max(100),
      self_comments: z.string().min(20, 'Please provide detailed comments'),
      achievements: z.string().optional(),
      challenges: z.string().optional(),
    }),
  ),
  overall_summary: z.string().min(50, 'Summary must be at least 50 characters'),
  key_achievements: z.string().min(30, 'Please list your key achievements'),
  areas_of_improvement: z.string().min(20, 'Please identify areas for improvement'),
  training_needs: z.string().optional(),
  career_aspirations: z.string().optional(),
});

type SelfAppraisalFormData = z.infer<typeof selfAppraisalSchema>;

interface Goal {
  id: string;
  title: string;
  description: string;
  category: string;
  weightage: number;
  target_date: string;
  progress: number;
  key_results: string;
}

interface CycleInfo {
  id: string;
  name: string;
  self_appraisal_deadline: string;
}

interface EmployeeInfo {
  id: string;
  name: string;
  code: string;
  department: string;
  designation: string;
}

const getCycleInfo = (): CycleInfo | null => null;
const getEmployeeInfo = (): EmployeeInfo | null => null;
const goals: Goal[] = [];

const getCategoryColor = (category: string) => {
  const colors: Record<string, string> = {
    BUSINESS: 'bg-purple-100 text-purple-800',
    FUNCTIONAL: 'bg-blue-100 text-blue-800',
    BEHAVIORAL: 'bg-green-100 text-green-800',
    DEVELOPMENT: 'bg-orange-100 text-orange-800',
  };
  return colors[category] || 'bg-gray-100 text-gray-800';
};

const renderStars = (rating: number, onChange?: (value: number) => void) => {
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <Star
          key={star}
          className={`h-6 w-6 cursor-pointer transition-colors ${
            star <= rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'
          }`}
          onClick={() => onChange?.(star)}
        />
      ))}
    </div>
  );
};

export default function SelfAppraisal() {
  const navigate = useNavigate();
  const { cycleId } = useParams();
  const { toast } = useToast();
  const cycleInfo = getCycleInfo();
  const employeeInfo = getEmployeeInfo();
  const [goalAppraisals, setGoalAppraisals] = useState<
    Record<
      string,
      {
        rating: number;
        progress: number;
        comments: string;
        achievements: string;
        challenges: string;
      }
    >
  >(
    goals.reduce(
      (acc, goal) => ({
        ...acc,
        [goal.id]: {
          rating: 0,
          progress: goal.progress,
          comments: '',
          achievements: '',
          challenges: '',
        },
      }),
      {},
    ),
  );
  const [overallData, setOverallData] = useState({
    summary: '',
    achievements: '',
    improvements: '',
    training: '',
    aspirations: '',
  });

  if (!cycleInfo || !employeeInfo) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Self Appraisal"
          subtitle={cycleId ? `Cycle ${cycleId}` : 'Cycle details unavailable'}
          breadcrumbs={[
            { label: 'Appraisal Cycles', to: '/admin/hris/performance/cycles' },
            { label: 'Self Appraisal' },
          ]}
        />
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            Self appraisal data is pending backend HRIS performance endpoints.
          </CardContent>
        </Card>
      </div>
    );
  }

  const handleSaveDraft = () => {
    logger.debug('Saving draft...', { goalAppraisals, overallData });
    toast({ title: 'Draft saved successfully' });
  };

  const handleSubmit = () => {
    // Validate all goals have ratings and comments
    const incompleteGoals = goals.filter(
      (g) => !goalAppraisals[g.id]?.rating || !goalAppraisals[g.id]?.comments,
    );
    if (incompleteGoals.length > 0) {
      toast({
        title: 'Goal appraisal incomplete',
        description: 'Please complete ratings and comments for all goals.',
        variant: 'destructive',
      });
      return;
    }
    if (!overallData.summary || !overallData.achievements || !overallData.improvements) {
      toast({
        title: 'Overall assessment incomplete',
        description: 'Please complete all required fields in the Overall Assessment section.',
        variant: 'destructive',
      });
      return;
    }
    logger.debug('Submitting...', { goalAppraisals, overallData });
    navigate('/admin/hris/performance/cycles');
  };

  const calculateOverallRating = () => {
    let weightedSum = 0;
    let totalWeight = 0;
    goals.forEach((goal) => {
      const rating = goalAppraisals[goal.id]?.rating || 0;
      if (rating > 0) {
        weightedSum += rating * goal.weightage;
        totalWeight += goal.weightage;
      }
    });
    return totalWeight > 0 ? (weightedSum / totalWeight).toFixed(1) : '-';
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Self Appraisal"
        subtitle={cycleInfo.name}
        breadcrumbs={[
          { label: 'Appraisal Cycles', to: '/admin/hris/performance/cycles' },
          { label: 'Self Appraisal' },
        ]}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleSaveDraft}>
              <Save className="mr-2 h-4 w-4" />
              Save Draft
            </Button>
            <Button onClick={handleSubmit}>
              <Send className="mr-2 h-4 w-4" />
              Submit Appraisal
            </Button>
          </div>
        }
      />

      {/* Summary Info */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Employee</div>
            <div className="font-semibold">{employeeInfo.name}</div>
            <div className="text-xs text-muted-foreground">{employeeInfo.department}</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Deadline</div>
            <div className="font-semibold">{formatDate(cycleInfo.self_appraisal_deadline)}</div>
            <div className="text-xs text-red-500">Submit by this date</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Goals to Assess</div>
            <div className="font-semibold">{goals.length}</div>
            <div className="text-xs text-muted-foreground">
              {Object.values(goalAppraisals).filter((g) => g.rating > 0).length} completed
            </div>
          </CardContent>
        </Card>

        <Card className="bg-yellow-50">
          <CardContent className="pt-6">
            <div className="text-sm text-yellow-700">Self Rating</div>
            <div className="text-2xl font-bold text-yellow-800">{calculateOverallRating()}/5</div>
            <div className="text-xs text-yellow-600">Weighted average</div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="goals" className="space-y-4">
        <TabsList>
          <TabsTrigger value="goals">Goal-wise Assessment</TabsTrigger>
          <TabsTrigger value="overall">Overall Assessment</TabsTrigger>
        </TabsList>

        <TabsContent value="goals" className="space-y-4">
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Self Assessment Guidelines</AlertTitle>
            <AlertDescription>
              Rate your performance against each goal objectively. Provide specific examples and
              evidence to support your ratings.
            </AlertDescription>
          </Alert>

          {goals.map((goal) => (
            <Card key={goal.id}>
              <CardContent className="pt-6">
                <div className="mb-4 flex items-start justify-between">
                  <div className="flex-1">
                    <div className="mb-1 flex items-center gap-2">
                      <h3 className="font-semibold">{goal.title}</h3>
                      <Badge variant="secondary" className={getCategoryColor(goal.category)}>
                        {goal.category}
                      </Badge>
                      <Badge variant="outline">{goal.weightage}%</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{goal.description}</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                  {/* Left: Progress & Rating */}
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium">Self Rating</label>
                      <div className="mt-2 flex items-center gap-4">
                        {renderStars(goalAppraisals[goal.id]?.rating || 0, (value) =>
                          setGoalAppraisals({
                            ...goalAppraisals,
                            [goal.id]: { ...goalAppraisals[goal.id], rating: value },
                          }),
                        )}
                        <span className="text-sm text-muted-foreground">
                          {goalAppraisals[goal.id]?.rating || 0}/5
                        </span>
                      </div>
                    </div>

                    <div>
                      <label className="text-sm font-medium">Progress Update</label>
                      <div className="mt-2 flex items-center gap-4">
                        <Slider
                          value={[goalAppraisals[goal.id]?.progress || goal.progress]}
                          max={100}
                          step={5}
                          className="flex-1"
                          onValueChange={(value) =>
                            setGoalAppraisals({
                              ...goalAppraisals,
                              [goal.id]: { ...goalAppraisals[goal.id], progress: value[0] },
                            })
                          }
                        />
                        <span className="w-12 text-sm font-medium">
                          {goalAppraisals[goal.id]?.progress || goal.progress}%
                        </span>
                      </div>
                      <Progress
                        value={goalAppraisals[goal.id]?.progress || goal.progress}
                        className="mt-2 h-2"
                      />
                    </div>

                    <div className="rounded-lg bg-muted p-3">
                      <p className="mb-1 text-xs font-medium text-muted-foreground">Key Results</p>
                      <p className="whitespace-pre-line text-sm">{goal.key_results}</p>
                    </div>
                  </div>

                  {/* Right: Comments */}
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium">Self Assessment Comments *</label>
                      <Textarea
                        placeholder="Describe your achievements against this goal with specific examples..."
                        className="mt-2 min-h-[80px]"
                        value={goalAppraisals[goal.id]?.comments || ''}
                        onChange={(e) =>
                          setGoalAppraisals({
                            ...goalAppraisals,
                            [goal.id]: { ...goalAppraisals[goal.id], comments: e.target.value },
                          })
                        }
                      />
                    </div>

                    <div>
                      <label className="text-sm font-medium">Key Achievements</label>
                      <Textarea
                        placeholder="List specific achievements..."
                        className="mt-2"
                        value={goalAppraisals[goal.id]?.achievements || ''}
                        onChange={(e) =>
                          setGoalAppraisals({
                            ...goalAppraisals,
                            [goal.id]: { ...goalAppraisals[goal.id], achievements: e.target.value },
                          })
                        }
                      />
                    </div>

                    <div>
                      <label className="text-sm font-medium">Challenges Faced</label>
                      <Textarea
                        placeholder="Describe any challenges or roadblocks..."
                        className="mt-2"
                        value={goalAppraisals[goal.id]?.challenges || ''}
                        onChange={(e) =>
                          setGoalAppraisals({
                            ...goalAppraisals,
                            [goal.id]: { ...goalAppraisals[goal.id], challenges: e.target.value },
                          })
                        }
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="overall" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Overall Performance Summary
              </CardTitle>
              <CardDescription>
                Provide a comprehensive summary of your performance this review period
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <label className="text-sm font-medium">Performance Summary *</label>
                <Textarea
                  placeholder="Provide an overall summary of your performance, highlighting key contributions and impact..."
                  className="mt-2 min-h-[120px]"
                  value={overallData.summary}
                  onChange={(e) => setOverallData({ ...overallData, summary: e.target.value })}
                />
              </div>

              <div>
                <label className="flex items-center gap-2 text-sm font-medium">
                  <Award className="h-4 w-4" />
                  Key Achievements *
                </label>
                <Textarea
                  placeholder="List your top 3-5 achievements with measurable impact..."
                  className="mt-2 min-h-[100px]"
                  value={overallData.achievements}
                  onChange={(e) => setOverallData({ ...overallData, achievements: e.target.value })}
                />
              </div>

              <div>
                <label className="flex items-center gap-2 text-sm font-medium">
                  <TrendingUp className="h-4 w-4" />
                  Areas for Improvement *
                </label>
                <Textarea
                  placeholder="Identify areas where you can improve and how you plan to address them..."
                  className="mt-2 min-h-[100px]"
                  value={overallData.improvements}
                  onChange={(e) => setOverallData({ ...overallData, improvements: e.target.value })}
                />
              </div>

              <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                <div>
                  <label className="text-sm font-medium">Training & Development Needs</label>
                  <Textarea
                    placeholder="What training or development would help you perform better?"
                    className="mt-2"
                    value={overallData.training}
                    onChange={(e) => setOverallData({ ...overallData, training: e.target.value })}
                  />
                </div>

                <div>
                  <label className="text-sm font-medium">Career Aspirations</label>
                  <Textarea
                    placeholder="Share your career goals and aspirations..."
                    className="mt-2"
                    value={overallData.aspirations}
                    onChange={(e) =>
                      setOverallData({ ...overallData, aspirations: e.target.value })
                    }
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
