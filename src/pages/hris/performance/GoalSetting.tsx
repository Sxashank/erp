import { zodResolver } from '@hookform/resolvers/zod';
import {
  ArrowLeft,
  Target,
  Plus,
  Edit,
  Trash2,
  CheckCircle,
  Clock,
  AlertCircle,
  Calendar,
  Percent,
  Save,
} from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';
import { z } from 'zod';

import { PageHeader } from '@/components/common/PageHeader';
import { HrisConfirmDialog } from '@/components/hris/HrisConfirmDialog';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { formatDate } from '@/lib/utils';

const goalSchema = z.object({
  title: z.string().min(5, 'Goal title must be at least 5 characters'),
  description: z.string().min(20, 'Description must be at least 20 characters'),
  category: z.enum(['BUSINESS', 'FUNCTIONAL', 'BEHAVIORAL', 'DEVELOPMENT']),
  weightage: z.number().min(5).max(50, 'Weightage must be between 5-50%'),
  target_date: z.string().min(1, 'Target date is required'),
  key_results: z.string().min(10, 'Key results are required'),
  measurement_criteria: z.string().min(10, 'Measurement criteria is required'),
});

type GoalFormData = z.infer<typeof goalSchema>;

type GoalStatus =
  | 'DRAFT'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'NOT_ACHIEVED';

interface Goal {
  id: string;
  title: string;
  description: string;
  category: string;
  weightage: number;
  target_date: string;
  status: GoalStatus;
  progress: number;
  key_results: string;
  measurement_criteria: string;
  manager_comments?: string;
}

interface EmployeeInfo {
  id: string;
  name: string;
  code: string;
  department: string;
  designation: string;
  manager: string;
}

interface CycleInfo {
  id: string;
  name: string;
  goal_setting_deadline: string;
  total_weightage: number;
}

const getEmployeeInfo = (): EmployeeInfo | null => null;
const getCycleInfo = (): CycleInfo | null => null;
const initialGoals: Goal[] = [];

const getStatusBadge = (status: GoalStatus) => {
  const config: Record<
    GoalStatus,
    { variant: 'default' | 'secondary' | 'destructive' | 'outline'; color?: string; label: string }
  > = {
    DRAFT: { variant: 'outline', label: 'Draft' },
    PENDING_APPROVAL: {
      variant: 'secondary',
      color: 'bg-yellow-100 text-yellow-800',
      label: 'Pending Approval',
    },
    APPROVED: { variant: 'secondary', color: 'bg-blue-100 text-blue-800', label: 'Approved' },
    IN_PROGRESS: { variant: 'default', color: 'bg-green-100 text-green-800', label: 'In Progress' },
    COMPLETED: { variant: 'default', label: 'Completed' },
    NOT_ACHIEVED: { variant: 'destructive', label: 'Not Achieved' },
  };
  const cfg = config[status];
  return (
    <Badge variant={cfg.variant} className={cfg.color}>
      {cfg.label}
    </Badge>
  );
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

export default function GoalSetting() {
  const navigate = useNavigate();
  const { cycleId, employeeId } = useParams();
  const { toast } = useToast();
  const employeeInfo = getEmployeeInfo();
  const cycleInfo = getCycleInfo();
  const [goals, setGoals] = useState(initialGoals);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [editingGoal, setEditingGoal] = useState<Goal | null>(null);
  const [deleteGoalId, setDeleteGoalId] = useState<string | null>(null);

  const form = useForm<GoalFormData>({
    resolver: zodResolver(goalSchema),
    defaultValues: {
      title: '',
      description: '',
      category: 'BUSINESS',
      weightage: 20,
      target_date: '',
      key_results: '',
      measurement_criteria: '',
    },
  });

  if (!employeeInfo || !cycleInfo) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Goal Setting"
          subtitle={employeeId ? `Employee ${employeeId}` : 'Employee details unavailable'}
          breadcrumbs={[
            { label: 'Performance Cycles', to: '/admin/hris/performance/cycles' },
            { label: 'Goal Setting' },
          ]}
        />
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            Goal setting data is pending backend HRIS performance endpoints for cycle{' '}
            {cycleId ?? 'selected'}.
          </CardContent>
        </Card>
      </div>
    );
  }

  const totalWeightage = goals.reduce((sum, g) => sum + g.weightage, 0);
  const remainingWeightage = cycleInfo.total_weightage - totalWeightage;

  const handleAddGoal = (data: GoalFormData) => {
    const newGoal: Goal = {
      id: `new-${Date.now()}`,
      ...data,
      status: 'DRAFT',
      progress: 0,
    };
    setGoals([...goals, newGoal]);
    form.reset();
    setShowAddDialog(false);
  };

  const handleDeleteGoal = (goalId: string) => {
    setDeleteGoalId(goalId);
  };

  const handleSubmitForApproval = () => {
    if (totalWeightage !== 100) {
      toast({
        title: 'Goal weightage must equal 100%',
        description: `Current total is ${totalWeightage}%. Adjust goals before submitting.`,
        variant: 'destructive',
      });
      return;
    }
    setGoals(goals.map((g) => ({ ...g, status: 'PENDING_APPROVAL' as GoalStatus })));
    toast({ title: 'Goals submitted for manager approval' });
  };

  const handleUpdateProgress = (goalId: string, progress: number) => {
    setGoals(goals.map((g) => (g.id === goalId ? { ...g, progress } : g)));
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Goal Setting"
        subtitle={cycleInfo.name}
        breadcrumbs={[
          { label: 'Performance Cycles', to: '/admin/hris/performance/cycles' },
          { label: 'Goal Setting' },
        ]}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setShowAddDialog(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Add Goal
            </Button>
            <Button onClick={handleSubmitForApproval} disabled={totalWeightage !== 100}>
              <Save className="mr-2 h-4 w-4" />
              Submit for Approval
            </Button>
          </div>
        }
      />

      {/* Employee & Summary Info */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Employee</div>
            <div className="font-semibold">{employeeInfo.name}</div>
            <div className="text-xs text-muted-foreground">
              {employeeInfo.code} • {employeeInfo.department}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Reporting Manager</div>
            <div className="font-semibold">{employeeInfo.manager}</div>
            <div className="text-xs text-muted-foreground">Approver</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Goal Setting Deadline</div>
            <div className="font-semibold">{formatDate(cycleInfo.goal_setting_deadline)}</div>
            <div className="text-xs text-muted-foreground">Submit by this date</div>
          </CardContent>
        </Card>

        <Card
          className={
            totalWeightage === 100
              ? 'bg-green-50'
              : totalWeightage > 100
                ? 'bg-red-50'
                : 'bg-yellow-50'
          }
        >
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Weightage</div>
            <div
              className={`text-2xl font-bold ${totalWeightage === 100 ? 'text-green-700' : totalWeightage > 100 ? 'text-red-700' : 'text-yellow-700'}`}
            >
              {totalWeightage}%
            </div>
            <div className="text-xs text-muted-foreground">
              {totalWeightage === 100 ? 'Weightage complete' : `${remainingWeightage}% remaining`}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Weightage Warning */}
      {totalWeightage !== 100 && (
        <Alert variant={totalWeightage > 100 ? 'destructive' : 'default'}>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Weightage {totalWeightage > 100 ? 'Exceeds' : 'Incomplete'}</AlertTitle>
          <AlertDescription>
            {totalWeightage > 100
              ? `Total weightage is ${totalWeightage}%. Please reduce by ${totalWeightage - 100}%.`
              : `Total weightage is ${totalWeightage}%. Add ${remainingWeightage}% more to reach 100%.`}
          </AlertDescription>
        </Alert>
      )}

      {/* Goals List */}
      <div className="space-y-4">
        {goals.map((goal) => (
          <Card key={goal.id}>
            <CardContent className="pt-6">
              <div className="mb-4 flex items-start justify-between">
                <div className="flex-1">
                  <div className="mb-1 flex items-center gap-2">
                    <h3 className="text-lg font-semibold">{goal.title}</h3>
                    <Badge variant="secondary" className={getCategoryColor(goal.category)}>
                      {goal.category}
                    </Badge>
                    {getStatusBadge(goal.status)}
                  </div>
                  <p className="text-sm text-muted-foreground">{goal.description}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="px-3 py-1 text-lg">
                    <Percent className="mr-1 h-4 w-4" />
                    {goal.weightage}%
                  </Badge>
                  {goal.status === 'DRAFT' && (
                    <Button variant="ghost" size="icon" onClick={() => handleDeleteGoal(goal.id)}>
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  )}
                </div>
              </div>

              <div className="mb-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <p className="mb-1 text-xs font-medium text-muted-foreground">Key Results</p>
                  <p className="whitespace-pre-line text-sm">{goal.key_results}</p>
                </div>
                <div>
                  <p className="mb-1 text-xs font-medium text-muted-foreground">
                    Measurement Criteria
                  </p>
                  <p className="text-sm">{goal.measurement_criteria}</p>
                </div>
              </div>

              <div className="flex items-center justify-between border-t pt-4">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2 text-sm">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span>Target: {formatDate(goal.target_date)}</span>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-40">
                    <div className="mb-1 flex justify-between text-xs">
                      <span>Progress</span>
                      <span>{goal.progress}%</span>
                    </div>
                    <Progress value={goal.progress} className="h-2" />
                  </div>
                  {(goal.status === 'IN_PROGRESS' || goal.status === 'APPROVED') && (
                    <div className="flex items-center gap-2">
                      <Slider
                        value={[goal.progress]}
                        max={100}
                        step={5}
                        className="w-24"
                        onValueChange={(value) => handleUpdateProgress(goal.id, value[0])}
                      />
                      <span className="w-12 text-sm">{goal.progress}%</span>
                    </div>
                  )}
                </div>
              </div>

              {goal.manager_comments && (
                <div className="mt-4 rounded-lg bg-blue-50 p-3">
                  <p className="mb-1 text-xs font-medium text-blue-700">Manager Comments</p>
                  <p className="text-sm text-blue-800">{goal.manager_comments}</p>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Add Goal Dialog */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Add New Goal</DialogTitle>
            <DialogDescription>
              Define a SMART goal with clear key results and measurement criteria
            </DialogDescription>
          </DialogHeader>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(handleAddGoal)} className="space-y-4">
              <FormField
                control={form.control}
                name="title"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Goal Title</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g., Deliver Project X on time" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Describe the goal in detail..."
                        className="min-h-[80px]"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="grid grid-cols-3 gap-4">
                <FormField
                  control={form.control}
                  name="category"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Category</FormLabel>
                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select category" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="BUSINESS">Business</SelectItem>
                          <SelectItem value="FUNCTIONAL">Functional</SelectItem>
                          <SelectItem value="BEHAVIORAL">Behavioral</SelectItem>
                          <SelectItem value="DEVELOPMENT">Development</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="weightage"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Weightage (%)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min={5}
                          max={50}
                          {...field}
                          onChange={(e) => field.onChange(parseInt(e.target.value))}
                        />
                      </FormControl>
                      <FormDescription>Max {remainingWeightage}% available</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="target_date"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Target Date</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="key_results"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Key Results</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="List specific, measurable key results (one per line)..."
                        className="min-h-[80px]"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>What specific outcomes define success?</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="measurement_criteria"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Measurement Criteria</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="How will progress and completion be measured?"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setShowAddDialog(false)}>
                  Cancel
                </Button>
                <Button type="submit">
                  <Target className="mr-2 h-4 w-4" />
                  Add Goal
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
      <HrisConfirmDialog
        open={Boolean(deleteGoalId)}
        title="Delete goal"
        description="This removes the goal from the current appraisal plan and recalculates total weightage."
        confirmLabel="Delete goal"
        destructive
        onOpenChange={(open) => {
          if (!open) setDeleteGoalId(null);
        }}
        onConfirm={() => {
          if (deleteGoalId) {
            setGoals(goals.filter((goal) => goal.id !== deleteGoalId));
            setDeleteGoalId(null);
          }
        }}
      />
    </div>
  );
}
