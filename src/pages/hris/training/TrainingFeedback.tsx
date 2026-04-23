import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Star,
  StarHalf,
  Download,
  MessageSquare,
  Users,
  BarChart3,
  ThumbsUp,
  ThumbsDown,
  TrendingUp,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import { Progress } from '@/components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { formatDate } from '@/lib/utils';

interface FeedbackSummary {
  total_participants: number;
  feedback_received: number;
  response_rate: number;
  overall_rating: number;
  ratings: {
    category: string;
    rating: number;
    max_rating: number;
  }[];
  rating_distribution: {
    stars: number;
    count: number;
  }[];
  recommend_percentage: number;
}

interface IndividualFeedback {
  id: string;
  employee_name: string;
  employee_code: string;
  department: string;
  overall_rating: number;
  content_rating: number;
  trainer_rating: number;
  facilities_rating: number;
  relevance_rating: number;
  would_recommend: boolean;
  strengths: string;
  improvements: string;
  comments: string;
  submitted_on: string;
}

// Mock program details
const programDetails = {
  id: '1',
  program_code: 'TRN-2024-004',
  title: 'Customer Service Excellence',
  start_date: '2024-12-15',
  end_date: '2024-12-16',
  trainer_name: 'Rajesh Kumar',
};

// Mock feedback summary
const feedbackSummary: FeedbackSummary = {
  total_participants: 28,
  feedback_received: 24,
  response_rate: 85.7,
  overall_rating: 4.3,
  ratings: [
    { category: 'Content Quality', rating: 4.5, max_rating: 5 },
    { category: 'Trainer Effectiveness', rating: 4.6, max_rating: 5 },
    { category: 'Training Materials', rating: 4.2, max_rating: 5 },
    { category: 'Practical Relevance', rating: 4.1, max_rating: 5 },
    { category: 'Facilities & Logistics', rating: 4.0, max_rating: 5 },
  ],
  rating_distribution: [
    { stars: 5, count: 10 },
    { stars: 4, count: 9 },
    { stars: 3, count: 4 },
    { stars: 2, count: 1 },
    { stars: 1, count: 0 },
  ],
  recommend_percentage: 92,
};

// Mock individual feedback
const individualFeedbacks: IndividualFeedback[] = [
  {
    id: '1',
    employee_name: 'Rahul Sharma',
    employee_code: 'EMP001',
    department: 'Sales',
    overall_rating: 5,
    content_rating: 5,
    trainer_rating: 5,
    facilities_rating: 4,
    relevance_rating: 5,
    would_recommend: true,
    strengths: 'Excellent trainer, practical examples, interactive sessions',
    improvements: 'Could include more role-play exercises',
    comments: 'Very beneficial training. The trainer made complex concepts easy to understand.',
    submitted_on: '2024-12-16',
  },
  {
    id: '2',
    employee_name: 'Priya Patel',
    employee_code: 'EMP002',
    department: 'Support',
    overall_rating: 4,
    content_rating: 4,
    trainer_rating: 5,
    facilities_rating: 4,
    relevance_rating: 4,
    would_recommend: true,
    strengths: 'Real-world case studies, group activities',
    improvements: 'Duration could be extended for more practice',
    comments: 'Good training overall. Would like more focus on handling difficult customers.',
    submitted_on: '2024-12-16',
  },
  {
    id: '3',
    employee_name: 'Amit Kumar',
    employee_code: 'EMP003',
    department: 'Operations',
    overall_rating: 4,
    content_rating: 4,
    trainer_rating: 4,
    facilities_rating: 5,
    relevance_rating: 4,
    would_recommend: true,
    strengths: 'Well-organized content, good venue',
    improvements: 'More industry-specific examples needed',
    comments: 'Informative session with good takeaways.',
    submitted_on: '2024-12-17',
  },
  {
    id: '4',
    employee_name: 'Sneha Reddy',
    employee_code: 'EMP004',
    department: 'Sales',
    overall_rating: 3,
    content_rating: 3,
    trainer_rating: 4,
    facilities_rating: 3,
    relevance_rating: 3,
    would_recommend: false,
    strengths: 'Trainer was knowledgeable',
    improvements: 'Content was too basic for experienced staff',
    comments: 'Expected more advanced topics. Good for beginners.',
    submitted_on: '2024-12-17',
  },
];

const renderStars = (rating: number) => {
  const stars = [];
  const fullStars = Math.floor(rating);
  const hasHalfStar = rating % 1 >= 0.5;

  for (let i = 0; i < fullStars; i++) {
    stars.push(<Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />);
  }
  if (hasHalfStar) {
    stars.push(<StarHalf key="half" className="h-4 w-4 fill-yellow-400 text-yellow-400" />);
  }
  const remaining = 5 - Math.ceil(rating);
  for (let i = 0; i < remaining; i++) {
    stars.push(<Star key={`empty-${i}`} className="h-4 w-4 text-gray-300" />);
  }
  return stars;
};

export default function TrainingFeedback() {
  const navigate = useNavigate();
  const { id } = useParams();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Training Feedback"
        subtitle={programDetails.title}
        breadcrumbs={[
          { label: 'Training', to: '/admin/hris/training' },
          { label: 'Feedback' },
        ]}
        actions={
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
        }
      />

      {/* Program Summary */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div>
              <p className="text-xs text-muted-foreground">Program Code</p>
              <p className="font-medium">{programDetails.program_code}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Training Date</p>
              <p className="font-medium">
                {formatDate(programDetails.start_date)} - {formatDate(programDetails.end_date)}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Trainer</p>
              <p className="font-medium">{programDetails.trainer_name}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Participants</p>
              <p className="font-medium">{feedbackSummary.total_participants}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Response Rate</p>
              <p className="font-medium text-green-600">{feedbackSummary.response_rate}%</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-yellow-50 to-orange-50 border-yellow-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-yellow-700">Overall Rating</p>
                <p className="text-3xl font-bold text-yellow-800">
                  {feedbackSummary.overall_rating.toFixed(1)}
                </p>
                <div className="flex mt-1">{renderStars(feedbackSummary.overall_rating)}</div>
              </div>
              <Star className="h-10 w-10 text-yellow-500 fill-yellow-400" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Feedback Received</p>
                <p className="text-3xl font-bold">
                  {feedbackSummary.feedback_received}/{feedbackSummary.total_participants}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {feedbackSummary.response_rate}% response rate
                </p>
              </div>
              <MessageSquare className="h-10 w-10 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-700">Would Recommend</p>
                <p className="text-3xl font-bold text-green-800">
                  {feedbackSummary.recommend_percentage}%
                </p>
                <p className="text-xs text-green-600 mt-1">of participants</p>
              </div>
              <ThumbsUp className="h-10 w-10 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Trainer Rating</p>
                <p className="text-3xl font-bold">4.6</p>
                <div className="flex mt-1">{renderStars(4.6)}</div>
              </div>
              <TrendingUp className="h-10 w-10 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Feedback */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="ratings">Rating Breakdown</TabsTrigger>
          <TabsTrigger value="individual">Individual Responses</TabsTrigger>
          <TabsTrigger value="comments">Comments</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Rating Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Rating Distribution
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {feedbackSummary.rating_distribution.map((dist) => (
                  <div key={dist.stars} className="flex items-center gap-3">
                    <div className="flex items-center w-16">
                      {dist.stars} <Star className="h-4 w-4 ml-1 fill-yellow-400 text-yellow-400" />
                    </div>
                    <div className="flex-1">
                      <Progress
                        value={(dist.count / feedbackSummary.feedback_received) * 100}
                        className="h-3"
                      />
                    </div>
                    <div className="w-12 text-right text-sm text-muted-foreground">
                      {dist.count} ({Math.round((dist.count / feedbackSummary.feedback_received) * 100)}%)
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Category Ratings */}
            <Card>
              <CardHeader>
                <CardTitle>Category-wise Ratings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {feedbackSummary.ratings.map((cat) => (
                  <div key={cat.category} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span>{cat.category}</span>
                      <span className="font-medium">{cat.rating.toFixed(1)}/5</span>
                    </div>
                    <Progress value={(cat.rating / cat.max_rating) * 100} className="h-2" />
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="ratings">
          <Card>
            <CardHeader>
              <CardTitle>Detailed Rating Breakdown</CardTitle>
              <CardDescription>Individual ratings by category</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Employee</TableHead>
                    <TableHead className="text-center">Overall</TableHead>
                    <TableHead className="text-center">Content</TableHead>
                    <TableHead className="text-center">Trainer</TableHead>
                    <TableHead className="text-center">Facilities</TableHead>
                    <TableHead className="text-center">Relevance</TableHead>
                    <TableHead className="text-center">Recommend</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {individualFeedbacks.map((fb) => (
                    <TableRow key={fb.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{fb.employee_name}</div>
                          <div className="text-xs text-muted-foreground">{fb.department}</div>
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="flex justify-center">{renderStars(fb.overall_rating)}</div>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant="outline">{fb.content_rating}/5</Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant="outline">{fb.trainer_rating}/5</Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant="outline">{fb.facilities_rating}/5</Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant="outline">{fb.relevance_rating}/5</Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        {fb.would_recommend ? (
                          <ThumbsUp className="h-5 w-5 text-green-500 mx-auto" />
                        ) : (
                          <ThumbsDown className="h-5 w-5 text-red-500 mx-auto" />
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="individual">
          <div className="space-y-4">
            {individualFeedbacks.map((fb) => (
              <Card key={fb.id}>
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="font-semibold">{fb.employee_name}</h3>
                      <p className="text-sm text-muted-foreground">
                        {fb.employee_code} • {fb.department}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-1">
                        {renderStars(fb.overall_rating)}
                        <span className="ml-2 font-medium">{fb.overall_rating}/5</span>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Submitted on {formatDate(fb.submitted_on)}
                      </p>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-3 bg-green-50 rounded-lg">
                      <p className="text-xs font-medium text-green-700 mb-1">Strengths</p>
                      <p className="text-sm">{fb.strengths}</p>
                    </div>
                    <div className="p-3 bg-yellow-50 rounded-lg">
                      <p className="text-xs font-medium text-yellow-700 mb-1">Areas for Improvement</p>
                      <p className="text-sm">{fb.improvements}</p>
                    </div>
                    <div className="p-3 bg-blue-50 rounded-lg">
                      <p className="text-xs font-medium text-blue-700 mb-1">Additional Comments</p>
                      <p className="text-sm">{fb.comments}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="comments">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                All Comments
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {individualFeedbacks.map((fb) => (
                <div key={fb.id} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{fb.employee_name}</span>
                      <span className="text-sm text-muted-foreground">({fb.department})</span>
                    </div>
                    <div className="flex">{renderStars(fb.overall_rating)}</div>
                  </div>
                  <p className="text-sm text-muted-foreground">{fb.comments}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
