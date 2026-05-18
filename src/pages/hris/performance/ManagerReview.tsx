import {
  ArrowLeft,
  Target,
  Save,
  Send,
  CheckCircle,
  Star,
  MessageSquare,
  Award,
  TrendingUp,
  User,
  FileText,
  AlertCircle,
} from 'lucide-react';
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { logger } from '@/lib/logger';
import { formatDate } from '@/lib/utils';

interface Goal {
  id: string;
  title: string;
  description: string;
  category: string;
  weightage: number;
  target_date: string;
  self_rating: number;
  self_progress: number;
  self_comments: string;
  self_achievements: string;
  manager_rating?: number;
  manager_comments?: string;
}

interface CycleInfo {
  id: string;
  name: string;
  manager_review_deadline: string;
}

interface EmployeeInfo {
  id: string;
  name: string;
  code: string;
  department: string;
  designation: string;
  date_of_joining: string;
  reporting_manager: string;
}

interface SelfAppraisalData {
  overall_summary: string;
  key_achievements: string;
  areas_of_improvement: string;
  training_needs: string;
  career_aspirations: string;
}

const getCycleInfo = (): CycleInfo | null => null;
const getEmployeeInfo = (): EmployeeInfo | null => null;
const getSelfAppraisalData = (): SelfAppraisalData | null => null;
const goals: Goal[] = [];

const ratingLabels: Record<number, { label: string; color: string }> = {
  1: { label: 'Needs Significant Improvement', color: 'text-red-600' },
  2: { label: 'Needs Improvement', color: 'text-orange-600' },
  3: { label: 'Meets Expectations', color: 'text-yellow-600' },
  4: { label: 'Exceeds Expectations', color: 'text-green-600' },
  5: { label: 'Outstanding', color: 'text-blue-600' },
};

const getCategoryColor = (category: string) => {
  const colors: Record<string, string> = {
    BUSINESS: 'bg-purple-100 text-purple-800',
    FUNCTIONAL: 'bg-blue-100 text-blue-800',
    BEHAVIORAL: 'bg-green-100 text-green-800',
    DEVELOPMENT: 'bg-orange-100 text-orange-800',
  };
  return colors[category] || 'bg-gray-100 text-gray-800';
};

const renderStars = (rating: number) => {
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <Star
          key={star}
          className={`h-5 w-5 ${star <= rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`}
        />
      ))}
    </div>
  );
};

export default function ManagerReview() {
  const navigate = useNavigate();
  const { cycleId, employeeId } = useParams();
  const { toast } = useToast();
  const cycleInfo = getCycleInfo();
  const employeeInfo = getEmployeeInfo();
  const selfAppraisalData = getSelfAppraisalData();
  const [goalReviews, setGoalReviews] = useState<
    Record<string, { rating: number; comments: string }>
  >(
    goals.reduce(
      (acc, goal) => ({
        ...acc,
        [goal.id]: { rating: 0, comments: '' },
      }),
      {},
    ),
  );
  const [overallReview, setOverallReview] = useState({
    overall_rating: '',
    strengths: '',
    development_areas: '',
    recommendations: '',
    promotion_ready: '',
    overall_comments: '',
  });

  if (!cycleInfo || !employeeInfo || !selfAppraisalData) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Manager Review"
          subtitle={employeeId ? `Employee ${employeeId}` : 'Employee details unavailable'}
          breadcrumbs={[
            { label: 'Appraisal Cycles', to: '/admin/hris/performance/cycles' },
            { label: 'Manager Review' },
          ]}
        />
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            Manager review data is pending backend HRIS performance endpoints for cycle{' '}
            {cycleId ?? 'selected'}.
          </CardContent>
        </Card>
      </div>
    );
  }

  const handleSaveDraft = () => {
    logger.debug('Saving draft...', { goalReviews, overallReview });
    toast({ title: 'Draft saved successfully' });
  };

  const handleSubmit = () => {
    // Validate all goals have manager ratings
    const incompleteGoals = goals.filter((g) => !goalReviews[g.id]?.rating);
    if (incompleteGoals.length > 0) {
      toast({
        title: 'Ratings required',
        description: 'Please provide ratings for all goals.',
        variant: 'destructive',
      });
      return;
    }
    if (
      !overallReview.overall_rating ||
      !overallReview.strengths ||
      !overallReview.development_areas
    ) {
      toast({
        title: 'Overall review incomplete',
        description: 'Please complete all required fields in the Overall Review section.',
        variant: 'destructive',
      });
      return;
    }
    logger.debug('Submitting...', { goalReviews, overallReview });
    navigate('/admin/hris/performance/cycles');
  };

  const calculateSelfRating = () => {
    let weightedSum = 0;
    goals.forEach((goal) => {
      weightedSum += goal.self_rating * goal.weightage;
    });
    return (weightedSum / 100).toFixed(1);
  };

  const calculateManagerRating = () => {
    let weightedSum = 0;
    let totalWeight = 0;
    goals.forEach((goal) => {
      const rating = goalReviews[goal.id]?.rating || 0;
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
        title="Manager Review"
        subtitle={cycleInfo.name}
        breadcrumbs={[
          { label: 'Performance Cycles', to: '/admin/hris/performance/cycles' },
          { label: 'Manager Review' },
        ]}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleSaveDraft}>
              <Save className="mr-2 h-4 w-4" />
              Save Draft
            </Button>
            <Button onClick={handleSubmit}>
              <Send className="mr-2 h-4 w-4" />
              Submit Review
            </Button>
          </div>
        }
      />

      {/* Employee Info */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                <User className="h-8 w-8 text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">{employeeInfo.name}</h2>
                <p className="text-sm text-muted-foreground">
                  {employeeInfo.code} • {employeeInfo.department} • {employeeInfo.designation}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Joined: {formatDate(employeeInfo.date_of_joining)}
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-muted-foreground">Review Deadline</div>
              <div className="font-medium text-red-600">
                {formatDate(cycleInfo.manager_review_deadline)}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Rating Summary */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card className="bg-yellow-50">
          <CardContent className="pt-6">
            <div className="text-sm text-yellow-700">Self Rating</div>
            <div className="text-3xl font-bold text-yellow-800">{calculateSelfRating()}/5</div>
            <div className="mt-2 flex">{renderStars(parseFloat(calculateSelfRating()))}</div>
          </CardContent>
        </Card>

        <Card className="bg-blue-50">
          <CardContent className="pt-6">
            <div className="text-sm text-blue-700">Manager Rating</div>
            <div className="text-3xl font-bold text-blue-800">{calculateManagerRating()}/5</div>
            <div className="mt-2 flex">
              {renderStars(parseFloat(calculateManagerRating()) || 0)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Goals Reviewed</div>
            <div className="text-3xl font-bold">
              {Object.values(goalReviews).filter((r) => r.rating > 0).length}/{goals.length}
            </div>
            <Progress
              value={
                (Object.values(goalReviews).filter((r) => r.rating > 0).length / goals.length) * 100
              }
              className="mt-2 h-2"
            />
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="goals" className="space-y-4">
        <TabsList>
          <TabsTrigger value="goals">Goal-wise Review</TabsTrigger>
          <TabsTrigger value="self-summary">Self Appraisal Summary</TabsTrigger>
          <TabsTrigger value="overall">Overall Review</TabsTrigger>
        </TabsList>

        <TabsContent value="goals" className="space-y-4">
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

                {/* Self Assessment Section */}
                <div className="mb-4 rounded-lg bg-yellow-50 p-4">
                  <h4 className="mb-2 font-medium text-yellow-800">Self Assessment</h4>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                    <div>
                      <p className="text-xs text-yellow-700">Self Rating</p>
                      <div className="flex items-center gap-2">
                        {renderStars(goal.self_rating)}
                        <span className="text-sm font-medium">{goal.self_rating}/5</span>
                      </div>
                    </div>
                    <div>
                      <p className="text-xs text-yellow-700">Progress Claimed</p>
                      <div className="flex items-center gap-2">
                        <Progress value={goal.self_progress} className="h-2 flex-1" />
                        <span className="text-sm font-medium">{goal.self_progress}%</span>
                      </div>
                    </div>
                    <div>
                      <p className="text-xs text-yellow-700">Achievements</p>
                      <p className="text-sm">{goal.self_achievements}</p>
                    </div>
                  </div>
                  <div className="mt-3">
                    <p className="text-xs text-yellow-700">Self Comments</p>
                    <p className="text-sm text-yellow-900">{goal.self_comments}</p>
                  </div>
                </div>

                {/* Manager Review Section */}
                <div className="rounded-lg bg-blue-50 p-4">
                  <h4 className="mb-3 font-medium text-blue-800">Manager Review</h4>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div>
                      <label className="text-sm font-medium text-blue-700">Manager Rating *</label>
                      <Select
                        value={goalReviews[goal.id]?.rating?.toString() || ''}
                        onValueChange={(value) =>
                          setGoalReviews({
                            ...goalReviews,
                            [goal.id]: { ...goalReviews[goal.id], rating: parseInt(value) },
                          })
                        }
                      >
                        <SelectTrigger className="mt-1">
                          <SelectValue placeholder="Select rating" />
                        </SelectTrigger>
                        <SelectContent>
                          {[5, 4, 3, 2, 1].map((r) => (
                            <SelectItem key={r} value={r.toString()}>
                              <span className={ratingLabels[r].color}>
                                {r} - {ratingLabels[r].label}
                              </span>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-blue-700">Manager Comments</label>
                      <Textarea
                        placeholder="Provide feedback on the employee's performance..."
                        className="mt-1"
                        value={goalReviews[goal.id]?.comments || ''}
                        onChange={(e) =>
                          setGoalReviews({
                            ...goalReviews,
                            [goal.id]: { ...goalReviews[goal.id], comments: e.target.value },
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

        <TabsContent value="self-summary">
          <Card>
            <CardHeader>
              <CardTitle>Employee's Self Appraisal Summary</CardTitle>
              <CardDescription>
                Review the employee's self-assessment before providing your feedback
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h4 className="mb-2 flex items-center gap-2 font-medium">
                  <FileText className="h-4 w-4" />
                  Overall Summary
                </h4>
                <p className="rounded-lg bg-muted p-3 text-sm">
                  {selfAppraisalData.overall_summary}
                </p>
              </div>

              <div>
                <h4 className="mb-2 flex items-center gap-2 font-medium">
                  <Award className="h-4 w-4" />
                  Key Achievements
                </h4>
                <p className="whitespace-pre-line rounded-lg bg-green-50 p-3 text-sm">
                  {selfAppraisalData.key_achievements}
                </p>
              </div>

              <div>
                <h4 className="mb-2 flex items-center gap-2 font-medium">
                  <TrendingUp className="h-4 w-4" />
                  Areas of Improvement (Self-Identified)
                </h4>
                <p className="rounded-lg bg-yellow-50 p-3 text-sm">
                  {selfAppraisalData.areas_of_improvement}
                </p>
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <h4 className="mb-2 font-medium">Training Needs</h4>
                  <p className="rounded-lg bg-muted p-3 text-sm">
                    {selfAppraisalData.training_needs}
                  </p>
                </div>
                <div>
                  <h4 className="mb-2 font-medium">Career Aspirations</h4>
                  <p className="rounded-lg bg-muted p-3 text-sm">
                    {selfAppraisalData.career_aspirations}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="overall">
          <Card>
            <CardHeader>
              <CardTitle>Overall Review & Recommendations</CardTitle>
              <CardDescription>
                Provide overall assessment and development recommendations
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label className="text-sm font-medium">Overall Performance Rating *</label>
                  <Select
                    value={overallReview.overall_rating}
                    onValueChange={(value) =>
                      setOverallReview({ ...overallReview, overall_rating: value })
                    }
                  >
                    <SelectTrigger className="mt-1">
                      <SelectValue placeholder="Select overall rating" />
                    </SelectTrigger>
                    <SelectContent>
                      {[5, 4, 3, 2, 1].map((r) => (
                        <SelectItem key={r} value={r.toString()}>
                          <span className={ratingLabels[r].color}>
                            {r} - {ratingLabels[r].label}
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="text-sm font-medium">Promotion Readiness</label>
                  <Select
                    value={overallReview.promotion_ready}
                    onValueChange={(value) =>
                      setOverallReview({ ...overallReview, promotion_ready: value })
                    }
                  >
                    <SelectTrigger className="mt-1">
                      <SelectValue placeholder="Select readiness level" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="READY_NOW">Ready Now</SelectItem>
                      <SelectItem value="READY_IN_1_YEAR">Ready in 1 Year</SelectItem>
                      <SelectItem value="READY_IN_2_YEARS">Ready in 2+ Years</SelectItem>
                      <SelectItem value="NOT_READY">Not Ready</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <label className="text-sm font-medium">Key Strengths *</label>
                <Textarea
                  placeholder="Highlight the employee's key strengths and positive contributions..."
                  className="mt-1 min-h-[100px]"
                  value={overallReview.strengths}
                  onChange={(e) =>
                    setOverallReview({ ...overallReview, strengths: e.target.value })
                  }
                />
              </div>

              <div>
                <label className="text-sm font-medium">Development Areas *</label>
                <Textarea
                  placeholder="Identify areas where the employee needs to improve..."
                  className="mt-1 min-h-[100px]"
                  value={overallReview.development_areas}
                  onChange={(e) =>
                    setOverallReview({ ...overallReview, development_areas: e.target.value })
                  }
                />
              </div>

              <div>
                <label className="text-sm font-medium">Recommendations</label>
                <Textarea
                  placeholder="Provide specific recommendations for development, training, or career growth..."
                  className="mt-1 min-h-[100px]"
                  value={overallReview.recommendations}
                  onChange={(e) =>
                    setOverallReview({ ...overallReview, recommendations: e.target.value })
                  }
                />
              </div>

              <div>
                <label className="text-sm font-medium">Overall Comments</label>
                <Textarea
                  placeholder="Any additional comments or feedback..."
                  className="mt-1"
                  value={overallReview.overall_comments}
                  onChange={(e) =>
                    setOverallReview({ ...overallReview, overall_comments: e.target.value })
                  }
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
