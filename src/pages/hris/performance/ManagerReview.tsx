import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
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
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { formatDate } from '@/lib/utils';

import { logger } from '@/lib/logger';
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

// Mock data
const cycleInfo = {
  id: 'cycle-001',
  name: 'Annual Performance Review 2024-25',
  manager_review_deadline: '2025-02-28',
};

const employeeInfo = {
  id: 'emp-001',
  name: 'Rahul Sharma',
  code: 'EMP001',
  department: 'Engineering',
  designation: 'Senior Developer',
  date_of_joining: '2020-03-15',
  reporting_manager: 'Priya Patel',
};

const selfAppraisalData = {
  overall_summary: 'This year has been highly productive. I successfully led the Project Alpha migration, achieved my AWS certification ahead of schedule, and contributed significantly to team development through mentoring initiatives.',
  key_achievements: '1. Successfully delivered Project Alpha with 99.9% uptime\n2. Achieved AWS Solutions Architect certification\n3. Improved code coverage from 60% to 78%\n4. Mentored 2 junior developers who are now independently handling modules',
  areas_of_improvement: 'I need to improve my documentation habits and work on time estimation accuracy. Also planning to enhance my system design skills.',
  training_needs: 'Advanced system design patterns, Leadership development program',
  career_aspirations: 'Aspiring to move into a Technical Lead role within the next 1-2 years.',
};

const goals: Goal[] = [
  {
    id: '1',
    title: 'Deliver Project Alpha on time',
    description: 'Lead and deliver the Project Alpha microservices migration',
    category: 'BUSINESS',
    weightage: 30,
    target_date: '2024-09-30',
    self_rating: 4,
    self_progress: 85,
    self_comments: 'Successfully delivered the project with minor delays due to scope changes. Achieved 99.9% uptime post-deployment. All P1 bugs were resolved within SLA.',
    self_achievements: 'Led a team of 5, managed 3 vendor integrations, zero critical bugs in production',
  },
  {
    id: '2',
    title: 'Improve code quality metrics',
    description: 'Improve overall code coverage and reduce technical debt',
    category: 'FUNCTIONAL',
    weightage: 25,
    target_date: '2025-03-31',
    self_rating: 4,
    self_progress: 70,
    self_comments: 'Increased code coverage from 60% to 78%. Reduced SonarQube issues by 45%. Documentation in progress.',
    self_achievements: 'Implemented automated testing framework, reduced technical debt by 40%',
  },
  {
    id: '3',
    title: 'Mentor junior developers',
    description: 'Mentor and upskill 2 junior developers in the team',
    category: 'BEHAVIORAL',
    weightage: 20,
    target_date: '2025-03-31',
    self_rating: 4,
    self_progress: 65,
    self_comments: 'Conducted weekly 1:1 sessions with both mentees. Both are now handling modules independently.',
    self_achievements: 'Mentees received positive feedback in their reviews, one got promoted',
  },
  {
    id: '4',
    title: 'AWS Certification',
    description: 'Obtain AWS Solutions Architect Associate certification',
    category: 'DEVELOPMENT',
    weightage: 15,
    target_date: '2024-12-31',
    self_rating: 5,
    self_progress: 100,
    self_comments: 'Completed certification in November 2024, ahead of the December deadline. Applied learnings to optimize cloud costs.',
    self_achievements: 'Achieved certification, implemented cost optimization saving ₹50k/month',
  },
  {
    id: '5',
    title: 'Process Improvement',
    description: 'Identify and implement at least 2 process improvements',
    category: 'FUNCTIONAL',
    weightage: 10,
    target_date: '2025-03-31',
    self_rating: 3,
    self_progress: 50,
    self_comments: 'Implemented automated deployment pipeline. Second improvement (code review process) is in planning stage.',
    self_achievements: 'CI/CD pipeline reduced deployment time by 60%',
  },
];

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
  const [goalReviews, setGoalReviews] = useState<Record<string, { rating: number; comments: string }>>(
    goals.reduce((acc, goal) => ({
      ...acc,
      [goal.id]: { rating: 0, comments: '' },
    }), {})
  );
  const [overallReview, setOverallReview] = useState({
    overall_rating: '',
    strengths: '',
    development_areas: '',
    recommendations: '',
    promotion_ready: '',
    overall_comments: '',
  });

  const handleSaveDraft = () => {
    logger.debug('Saving draft...', { goalReviews, overallReview });
    alert('Draft saved successfully');
  };

  const handleSubmit = () => {
    // Validate all goals have manager ratings
    const incompleteGoals = goals.filter((g) => !goalReviews[g.id]?.rating);
    if (incompleteGoals.length > 0) {
      alert('Please provide ratings for all goals');
      return;
    }
    if (!overallReview.overall_rating || !overallReview.strengths || !overallReview.development_areas) {
      alert('Please complete all required fields in the Overall Review section');
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/admin/hris/performance/cycles')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Manager Review</h1>
            <p className="text-muted-foreground">{cycleInfo.name}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleSaveDraft}>
            <Save className="h-4 w-4 mr-2" />
            Save Draft
          </Button>
          <Button onClick={handleSubmit}>
            <Send className="h-4 w-4 mr-2" />
            Submit Review
          </Button>
        </div>
      </div>

      {/* Employee Info */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
                <User className="h-8 w-8 text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">{employeeInfo.name}</h2>
                <p className="text-sm text-muted-foreground">
                  {employeeInfo.code} • {employeeInfo.department} • {employeeInfo.designation}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Joined: {formatDate(employeeInfo.date_of_joining)}
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-muted-foreground">Review Deadline</div>
              <div className="font-medium text-red-600">{formatDate(cycleInfo.manager_review_deadline)}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Rating Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-yellow-50">
          <CardContent className="pt-6">
            <div className="text-sm text-yellow-700">Self Rating</div>
            <div className="text-3xl font-bold text-yellow-800">{calculateSelfRating()}/5</div>
            <div className="flex mt-2">{renderStars(parseFloat(calculateSelfRating()))}</div>
          </CardContent>
        </Card>

        <Card className="bg-blue-50">
          <CardContent className="pt-6">
            <div className="text-sm text-blue-700">Manager Rating</div>
            <div className="text-3xl font-bold text-blue-800">{calculateManagerRating()}/5</div>
            <div className="flex mt-2">{renderStars(parseFloat(calculateManagerRating()) || 0)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Goals Reviewed</div>
            <div className="text-3xl font-bold">
              {Object.values(goalReviews).filter((r) => r.rating > 0).length}/{goals.length}
            </div>
            <Progress
              value={(Object.values(goalReviews).filter((r) => r.rating > 0).length / goals.length) * 100}
              className="h-2 mt-2"
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
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
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
                <div className="p-4 bg-yellow-50 rounded-lg mb-4">
                  <h4 className="font-medium text-yellow-800 mb-2">Self Assessment</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                <div className="p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-medium text-blue-800 mb-3">Manager Review</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
              <CardDescription>Review the employee's self-assessment before providing your feedback</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h4 className="font-medium flex items-center gap-2 mb-2">
                  <FileText className="h-4 w-4" />
                  Overall Summary
                </h4>
                <p className="text-sm p-3 bg-muted rounded-lg">{selfAppraisalData.overall_summary}</p>
              </div>

              <div>
                <h4 className="font-medium flex items-center gap-2 mb-2">
                  <Award className="h-4 w-4" />
                  Key Achievements
                </h4>
                <p className="text-sm p-3 bg-green-50 rounded-lg whitespace-pre-line">
                  {selfAppraisalData.key_achievements}
                </p>
              </div>

              <div>
                <h4 className="font-medium flex items-center gap-2 mb-2">
                  <TrendingUp className="h-4 w-4" />
                  Areas of Improvement (Self-Identified)
                </h4>
                <p className="text-sm p-3 bg-yellow-50 rounded-lg">{selfAppraisalData.areas_of_improvement}</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="font-medium mb-2">Training Needs</h4>
                  <p className="text-sm p-3 bg-muted rounded-lg">{selfAppraisalData.training_needs}</p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Career Aspirations</h4>
                  <p className="text-sm p-3 bg-muted rounded-lg">{selfAppraisalData.career_aspirations}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="overall">
          <Card>
            <CardHeader>
              <CardTitle>Overall Review & Recommendations</CardTitle>
              <CardDescription>Provide overall assessment and development recommendations</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                  onChange={(e) => setOverallReview({ ...overallReview, strengths: e.target.value })}
                />
              </div>

              <div>
                <label className="text-sm font-medium">Development Areas *</label>
                <Textarea
                  placeholder="Identify areas where the employee needs to improve..."
                  className="mt-1 min-h-[100px]"
                  value={overallReview.development_areas}
                  onChange={(e) => setOverallReview({ ...overallReview, development_areas: e.target.value })}
                />
              </div>

              <div>
                <label className="text-sm font-medium">Recommendations</label>
                <Textarea
                  placeholder="Provide specific recommendations for development, training, or career growth..."
                  className="mt-1 min-h-[100px]"
                  value={overallReview.recommendations}
                  onChange={(e) => setOverallReview({ ...overallReview, recommendations: e.target.value })}
                />
              </div>

              <div>
                <label className="text-sm font-medium">Overall Comments</label>
                <Textarea
                  placeholder="Any additional comments or feedback..."
                  className="mt-1"
                  value={overallReview.overall_comments}
                  onChange={(e) => setOverallReview({ ...overallReview, overall_comments: e.target.value })}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
