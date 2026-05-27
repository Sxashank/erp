import { Download, MessageSquare, Plus, Star, StarHalf, ThumbsUp, TrendingUp } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';

import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import {
  useRecordTrainingFeedback,
  useTrainingFeedback,
  useTrainingNominations,
} from '@/hooks/hris/useTraining';
import { useToast } from '@/hooks/use-toast';
import { getErrorMessage } from '@/lib/errorMessage';
import { formatDate } from '@/lib/utils';

function renderStars(rating: number) {
  const stars: JSX.Element[] = [];
  const fullStars = Math.floor(rating);
  const hasHalfStar = rating % 1 >= 0.5;

  for (let index = 0; index < fullStars; index += 1) {
    stars.push(<Star key={`full-${index}`} className="h-4 w-4 fill-yellow-400 text-yellow-400" />);
  }
  if (hasHalfStar) {
    stars.push(<StarHalf key="half" className="h-4 w-4 fill-yellow-400 text-yellow-400" />);
  }
  const remaining = 5 - Math.ceil(rating);
  for (let index = 0; index < remaining; index += 1) {
    stars.push(<Star key={`empty-${index}`} className="h-4 w-4 text-gray-300" />);
  }
  return stars;
}

function downloadCsv(filename: string, rows: string[][]) {
  const csv = rows
    .map((row) => row.map((value) => `"${String(value ?? '').replace(/"/g, '""')}"`).join(','))
    .join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  window.URL.revokeObjectURL(url);
}

export default function TrainingFeedback() {
  const { id } = useParams();
  const { toast } = useToast();
  const feedbackQuery = useTrainingFeedback(id);
  const nominationsQuery = useTrainingNominations(id);
  const recordFeedback = useRecordTrainingFeedback(id ?? '');
  const [showDialog, setShowDialog] = useState(false);
  const [employeeId, setEmployeeId] = useState('');
  const [submittedOn, setSubmittedOn] = useState(new Date().toISOString().split('T')[0] ?? '');
  const [overallRating, setOverallRating] = useState('5');
  const [contentRating, setContentRating] = useState('5');
  const [trainerRating, setTrainerRating] = useState('5');
  const [facilitiesRating, setFacilitiesRating] = useState('5');
  const [relevanceRating, setRelevanceRating] = useState('5');
  const [wouldRecommend, setWouldRecommend] = useState<'YES' | 'NO'>('YES');
  const [strengths, setStrengths] = useState('');
  const [improvements, setImprovements] = useState('');
  const [comments, setComments] = useState('');

  const feedbackBundle = feedbackQuery.data;
  const nominations = nominationsQuery.data ?? [];
  const feedbackEmployees = useMemo(
    () => new Set(feedbackBundle?.individualFeedbacks.map((item) => item.employeeId) ?? []),
    [feedbackBundle?.individualFeedbacks],
  );
  const eligibleEmployees = nominations.filter(
    (nomination) =>
      nomination.status !== 'CANCELLED' && !feedbackEmployees.has(nomination.employeeId),
  );

  const resetFeedbackForm = () => {
    setEmployeeId('');
    setSubmittedOn(new Date().toISOString().split('T')[0] ?? '');
    setOverallRating('5');
    setContentRating('5');
    setTrainerRating('5');
    setFacilitiesRating('5');
    setRelevanceRating('5');
    setWouldRecommend('YES');
    setStrengths('');
    setImprovements('');
    setComments('');
  };

  const handleRecordFeedback = async () => {
    try {
      await recordFeedback.mutateAsync({
        employeeId,
        submittedOn,
        overallRating: Number(overallRating),
        contentRating: Number(contentRating),
        trainerRating: Number(trainerRating),
        facilitiesRating: Number(facilitiesRating),
        relevanceRating: Number(relevanceRating),
        wouldRecommend: wouldRecommend === 'YES',
        strengths,
        improvements,
        comments,
      });
      toast({ title: 'Feedback recorded' });
      resetFeedbackForm();
      setShowDialog(false);
    } catch (error: unknown) {
      toast({
        title: 'Unable to record feedback',
        description: getErrorMessage(error, 'Please try again.'),
        variant: 'destructive',
      });
    }
  };

  if (feedbackQuery.isLoading || nominationsQuery.isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Training Feedback"
          subtitle="Loading feedback summary"
          breadcrumbs={[{ label: 'Training', to: '/admin/hris/training' }, { label: 'Feedback' }]}
        />
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            Loading feedback...
          </CardContent>
        </Card>
      </div>
    );
  }

  if (feedbackQuery.isError) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Training Feedback"
          subtitle="Unable to load feedback details"
          breadcrumbs={[{ label: 'Training', to: '/admin/hris/training' }, { label: 'Feedback' }]}
        />
        <ErrorState error={feedbackQuery.error} onRetry={() => void feedbackQuery.refetch()} />
      </div>
    );
  }

  if (!feedbackBundle) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Training Feedback"
          subtitle="Program details unavailable"
          breadcrumbs={[{ label: 'Training', to: '/admin/hris/training' }, { label: 'Feedback' }]}
        />
        <EmptyState
          title="Training program not found"
          subtitle="The selected training program is not available."
        />
      </div>
    );
  }

  const trainerSummary =
    feedbackBundle.summary.ratings.find((rating) => rating.category === 'Trainer')?.rating ?? 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Training Feedback"
        subtitle={feedbackBundle.program.title}
        breadcrumbs={[{ label: 'Training', to: '/admin/hris/training' }, { label: 'Feedback' }]}
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() =>
                downloadCsv(`${feedbackBundle.program.programCode}-feedback.csv`, [
                  [
                    'Employee Code',
                    'Employee Name',
                    'Department',
                    'Overall Rating',
                    'Content Rating',
                    'Trainer Rating',
                    'Facilities Rating',
                    'Relevance Rating',
                    'Would Recommend',
                    'Submitted On',
                    'Strengths',
                    'Improvements',
                    'Comments',
                  ],
                  ...feedbackBundle.individualFeedbacks.map((row) => [
                    row.employeeCode,
                    row.employeeName,
                    row.department,
                    String(row.overallRating),
                    String(row.contentRating),
                    String(row.trainerRating),
                    String(row.facilitiesRating),
                    String(row.relevanceRating),
                    row.wouldRecommend ? 'Yes' : 'No',
                    row.submittedOn,
                    row.strengths ?? '',
                    row.improvements ?? '',
                    row.comments ?? '',
                  ]),
                ])
              }
            >
              <Download className="mr-2 h-4 w-4" />
              Export Report
            </Button>
            <Button onClick={() => setShowDialog(true)} disabled={eligibleEmployees.length === 0}>
              <Plus className="mr-2 h-4 w-4" />
              Record Feedback
            </Button>
          </div>
        }
      />

      <Dialog
        open={showDialog}
        onOpenChange={(open) => {
          setShowDialog(open);
          if (!open) {
            resetFeedbackForm();
          }
        }}
      >
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Record Manual Feedback</DialogTitle>
            <DialogDescription>
              Capture training feedback manually for a nominated participant.
            </DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="employeeId">Participant</Label>
              <Select value={employeeId} onValueChange={setEmployeeId}>
                <SelectTrigger id="employeeId">
                  <SelectValue placeholder="Select nominated employee" />
                </SelectTrigger>
                <SelectContent>
                  {eligibleEmployees.map((nomination) => (
                    <SelectItem key={nomination.employeeId} value={nomination.employeeId}>
                      {nomination.employeeName} ({nomination.employeeCode})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="submittedOn">Submitted On</Label>
              <Input
                id="submittedOn"
                type="date"
                value={submittedOn}
                onChange={(event) => setSubmittedOn(event.target.value)}
              />
            </div>
            {(
              [
                ['overallRating', 'Overall Rating', overallRating, setOverallRating],
                ['contentRating', 'Content Rating', contentRating, setContentRating],
                ['trainerRating', 'Trainer Rating', trainerRating, setTrainerRating],
                ['facilitiesRating', 'Facilities Rating', facilitiesRating, setFacilitiesRating],
                ['relevanceRating', 'Relevance Rating', relevanceRating, setRelevanceRating],
              ] as const
            ).map(([fieldId, label, value, setter]) => (
              <div key={fieldId} className="space-y-2">
                <Label htmlFor={fieldId}>{label}</Label>
                <Input
                  id={fieldId}
                  type="number"
                  min="1"
                  max="5"
                  step="0.1"
                  value={value}
                  onChange={(event) => setter(event.target.value)}
                />
              </div>
            ))}
            <div className="space-y-2">
              <Label htmlFor="wouldRecommend">Would Recommend</Label>
              <Select
                value={wouldRecommend}
                onValueChange={(value) => setWouldRecommend(value as 'YES' | 'NO')}
              >
                <SelectTrigger id="wouldRecommend">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="YES">Yes</SelectItem>
                  <SelectItem value="NO">No</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="strengths">Strengths</Label>
              <Textarea
                id="strengths"
                value={strengths}
                onChange={(event) => setStrengths(event.target.value)}
              />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="improvements">Improvements</Label>
              <Textarea
                id="improvements"
                value={improvements}
                onChange={(event) => setImprovements(event.target.value)}
              />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="comments">Comments</Label>
              <Textarea
                id="comments"
                value={comments}
                onChange={(event) => setComments(event.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => void handleRecordFeedback()}
              disabled={!employeeId || recordFeedback.isPending}
            >
              {recordFeedback.isPending ? 'Saving...' : 'Save Feedback'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
            <div>
              <p className="text-xs text-muted-foreground">Program Code</p>
              <p className="font-medium">{feedbackBundle.program.programCode}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Training Date</p>
              <p className="font-medium">
                {formatDate(feedbackBundle.program.startDate)} -{' '}
                {formatDate(feedbackBundle.program.endDate)}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Trainer</p>
              <p className="font-medium">{feedbackBundle.program.trainerName}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Participants</p>
              <p className="font-medium">{feedbackBundle.summary.totalParticipants}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Response Rate</p>
              <p className="font-medium text-green-600">{feedbackBundle.summary.responseRate}%</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card className="border-yellow-200 bg-gradient-to-br from-yellow-50 to-orange-50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-yellow-700">Overall Rating</p>
                <p className="text-3xl font-bold text-yellow-800">
                  {feedbackBundle.summary.overallRating.toFixed(1)}
                </p>
                <div className="mt-1 flex">{renderStars(feedbackBundle.summary.overallRating)}</div>
              </div>
              <Star className="h-10 w-10 fill-yellow-400 text-yellow-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Feedback Received</p>
                <p className="text-3xl font-bold">
                  {feedbackBundle.summary.feedbackReceived}/
                  {feedbackBundle.summary.totalParticipants}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {feedbackBundle.summary.responseRate}% response rate
                </p>
              </div>
              <MessageSquare className="h-10 w-10 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-green-200 bg-gradient-to-br from-green-50 to-emerald-50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-700">Would Recommend</p>
                <p className="text-3xl font-bold text-green-800">
                  {feedbackBundle.summary.recommendPercentage}%
                </p>
                <p className="mt-1 text-xs text-green-600">of participants</p>
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
                <p className="text-3xl font-bold">{trainerSummary.toFixed(1)}</p>
                <div className="mt-1 flex">{renderStars(trainerSummary)}</div>
              </div>
              <TrendingUp className="h-10 w-10 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="ratings">Rating Breakdown</TabsTrigger>
          <TabsTrigger value="individual">Individual Responses</TabsTrigger>
          <TabsTrigger value="comments">Comments</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Rating Distribution</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {feedbackBundle.summary.ratingDistribution.map((distribution) => (
                  <div key={distribution.stars} className="flex items-center gap-3">
                    <div className="flex w-16 items-center">
                      {distribution.stars}
                      <Star className="ml-1 h-4 w-4 fill-yellow-400 text-yellow-400" />
                    </div>
                    <div className="flex-1">
                      <Progress
                        value={
                          feedbackBundle.summary.feedbackReceived > 0
                            ? (distribution.count / feedbackBundle.summary.feedbackReceived) * 100
                            : 0
                        }
                        className="h-3"
                      />
                    </div>
                    <div className="w-16 text-right text-sm text-muted-foreground">
                      {distribution.count}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Category Ratings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {feedbackBundle.summary.ratings.map((rating) => (
                  <div key={rating.category} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span>{rating.category}</span>
                      <span className="font-medium">
                        {rating.rating.toFixed(1)}/{rating.maxRating}
                      </span>
                    </div>
                    <Progress value={(rating.rating / rating.maxRating) * 100} className="h-2" />
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="ratings">
          {feedbackBundle.individualFeedbacks.length === 0 ? (
            <EmptyState
              title="No feedback recorded"
              subtitle="Use Record Feedback to capture participant responses manually."
            />
          ) : (
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
                    {feedbackBundle.individualFeedbacks.map((feedback) => (
                      <TableRow key={feedback.id}>
                        <TableCell>
                          <div>
                            <div className="font-medium">{feedback.employeeName}</div>
                            <div className="text-xs text-muted-foreground">
                              {feedback.department}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell className="text-center">{feedback.overallRating}</TableCell>
                        <TableCell className="text-center">{feedback.contentRating}</TableCell>
                        <TableCell className="text-center">{feedback.trainerRating}</TableCell>
                        <TableCell className="text-center">{feedback.facilitiesRating}</TableCell>
                        <TableCell className="text-center">{feedback.relevanceRating}</TableCell>
                        <TableCell className="text-center">
                          {feedback.wouldRecommend ? (
                            <Badge variant="default">Yes</Badge>
                          ) : (
                            <Badge variant="secondary">No</Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="individual">
          {feedbackBundle.individualFeedbacks.length === 0 ? (
            <EmptyState
              title="No individual responses"
              subtitle="Manual or ESS feedback responses will appear here."
            />
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Individual Responses</CardTitle>
                <CardDescription>
                  Submitted participant feedback with dates and recommendation signals
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Employee</TableHead>
                      <TableHead>Submitted On</TableHead>
                      <TableHead>Overall Rating</TableHead>
                      <TableHead>Recommendation</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {feedbackBundle.individualFeedbacks.map((feedback) => (
                      <TableRow key={feedback.id}>
                        <TableCell>
                          <div>
                            <div className="font-medium">{feedback.employeeName}</div>
                            <div className="text-xs text-muted-foreground">
                              {feedback.employeeCode}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>{formatDate(feedback.submittedOn)}</TableCell>
                        <TableCell>{feedback.overallRating.toFixed(1)}</TableCell>
                        <TableCell>
                          {feedback.wouldRecommend ? (
                            <Badge variant="default">Would recommend</Badge>
                          ) : (
                            <Badge variant="secondary">Would not recommend</Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="comments">
          {feedbackBundle.individualFeedbacks.length === 0 ? (
            <EmptyState
              title="No feedback comments"
              subtitle="Comments and improvement suggestions will appear after feedback is recorded."
            />
          ) : (
            <div className="space-y-4">
              {feedbackBundle.individualFeedbacks.map((feedback) => (
                <Card key={feedback.id}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle>{feedback.employeeName}</CardTitle>
                        <CardDescription>
                          {feedback.department} • {formatDate(feedback.submittedOn)}
                        </CardDescription>
                      </div>
                      <Badge variant={feedback.wouldRecommend ? 'default' : 'secondary'}>
                        {feedback.wouldRecommend ? 'Recommend' : 'Do not recommend'}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <p className="text-sm font-medium">Strengths</p>
                      <p className="text-sm text-muted-foreground">
                        {feedback.strengths || 'No strengths captured.'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium">Improvements</p>
                      <p className="text-sm text-muted-foreground">
                        {feedback.improvements || 'No improvements captured.'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium">Comments</p>
                      <p className="text-sm text-muted-foreground">
                        {feedback.comments || 'No additional comments provided.'}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
