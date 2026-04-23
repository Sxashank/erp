import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
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
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
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
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Slider } from '@/components/ui/slider';
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

type GoalStatus = 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'IN_PROGRESS' | 'COMPLETED' | 'NOT_ACHIEVED';

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

// Mock employee data
const employeeInfo = {
  id: 'emp-001',
  name: 'Rahul Sharma',
  code: 'EMP001',
  department: 'Engineering',
  designation: 'Senior Developer',
  manager: 'Priya Patel',
};

// Mock cycle data
const cycleInfo = {
  id: 'cycle-001',
  name: 'Annual Performance Review 2024-25',
  goal_setting_deadline: '2024-04-30',
  total_weightage: 100,
};

// Mock goals
const initialGoals: Goal[] = [
  {
    id: '1',
    title: 'Deliver Project Alpha on time',
    description: 'Lead and deliver the Project Alpha microservices migration with zero critical bugs in production',
    category: 'BUSINESS',
    weightage: 30,
    target_date: '2024-09-30',
    status: 'IN_PROGRESS',
    progress: 65,
    key_results: '1. Complete API migration by Q2\n2. Achieve 99.9% uptime\n3. Zero P1 bugs in production',
    measurement_criteria: 'Successful deployment and 3-month production stability',
    manager_comments: 'Good progress. Keep monitoring the deployment timeline.',
  },
  {
    id: '2',
    title: 'Improve code quality metrics',
    description: 'Improve overall code coverage and reduce technical debt in assigned modules',
    category: 'FUNCTIONAL',
    weightage: 25,
    target_date: '2025-03-31',
    status: 'IN_PROGRESS',
    progress: 40,
    key_results: '1. Achieve 80% code coverage\n2. Reduce SonarQube issues by 50%\n3. Document all critical modules',
    measurement_criteria: 'SonarQube and test coverage reports',
  },
  {
    id: '3',
    title: 'Mentor junior developers',
    description: 'Mentor and upskill 2 junior developers in the team',
    category: 'BEHAVIORAL',
    weightage: 20,
    target_date: '2025-03-31',
    status: 'APPROVED',
    progress: 20,
    key_results: '1. Conduct weekly 1:1 sessions\n2. Assign stretch projects\n3. Achieve 80% positive feedback from mentees',
    measurement_criteria: 'Mentee feedback and skill assessment',
  },
  {
    id: '4',
    title: 'AWS Certification',
    description: 'Obtain AWS Solutions Architect Associate certification',
    category: 'DEVELOPMENT',
    weightage: 15,
    target_date: '2024-12-31',
    status: 'COMPLETED',
    progress: 100,
    key_results: '1. Complete AWS training\n2. Pass certification exam\n3. Apply learnings to current project',
    measurement_criteria: 'Certification completion',
    manager_comments: 'Excellent! Completed ahead of schedule.',
  },
];

const getStatusBadge = (status: GoalStatus) => {
  const config: Record<GoalStatus, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; color?: string; label: string }> = {
    DRAFT: { variant: 'outline', label: 'Draft' },
    PENDING_APPROVAL: { variant: 'secondary', color: 'bg-yellow-100 text-yellow-800', label: 'Pending Approval' },
    APPROVED: { variant: 'secondary', color: 'bg-blue-100 text-blue-800', label: 'Approved' },
    IN_PROGRESS: { variant: 'default', color: 'bg-green-100 text-green-800', label: 'In Progress' },
    COMPLETED: { variant: 'default', label: 'Completed' },
    NOT_ACHIEVED: { variant: 'destructive', label: 'Not Achieved' },
  };
  const cfg = config[status];
  return <Badge variant={cfg.variant} className={cfg.color}>{cfg.label}</Badge>;
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
  const [goals, setGoals] = useState(initialGoals);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [editingGoal, setEditingGoal] = useState<Goal | null>(null);

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
    if (confirm('Are you sure you want to delete this goal?')) {
      setGoals(goals.filter((g) => g.id !== goalId));
    }
  };

  const handleSubmitForApproval = () => {
    if (totalWeightage !== 100) {
      alert('Total weightage must equal 100%');
      return;
    }
    setGoals(goals.map((g) => ({ ...g, status: 'PENDING_APPROVAL' as GoalStatus })));
    alert('Goals submitted for manager approval');
  };

  const handleUpdateProgress = (goalId: string, progress: number) => {
    setGoals(goals.map((g) => (g.id === goalId ? { ...g, progress } : g)));
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
            <h1 className="text-3xl font-bold">Goal Setting</h1>
            <p className="text-muted-foreground">{cycleInfo.name}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowAddDialog(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add Goal
          </Button>
          <Button onClick={handleSubmitForApproval} disabled={totalWeightage !== 100}>
            <Save className="h-4 w-4 mr-2" />
            Submit for Approval
          </Button>
        </div>
      </div>

      {/* Employee & Summary Info */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Employee</div>
            <div className="font-semibold">{employeeInfo.name}</div>
            <div className="text-xs text-muted-foreground">{employeeInfo.code} • {employeeInfo.department}</div>
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

        <Card className={totalWeightage === 100 ? 'bg-green-50' : totalWeightage > 100 ? 'bg-red-50' : 'bg-yellow-50'}>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Weightage</div>
            <div className={`text-2xl font-bold ${totalWeightage === 100 ? 'text-green-700' : totalWeightage > 100 ? 'text-red-700' : 'text-yellow-700'}`}>
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
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-lg">{goal.title}</h3>
                    <Badge variant="secondary" className={getCategoryColor(goal.category)}>
                      {goal.category}
                    </Badge>
                    {getStatusBadge(goal.status)}
                  </div>
                  <p className="text-sm text-muted-foreground">{goal.description}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-lg px-3 py-1">
                    <Percent className="h-4 w-4 mr-1" />
                    {goal.weightage}%
                  </Badge>
                  {goal.status === 'DRAFT' && (
                    <Button variant="ghost" size="icon" onClick={() => handleDeleteGoal(goal.id)}>
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-1">Key Results</p>
                  <p className="text-sm whitespace-pre-line">{goal.key_results}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-1">Measurement Criteria</p>
                  <p className="text-sm">{goal.measurement_criteria}</p>
                </div>
              </div>

              <div className="flex items-center justify-between pt-4 border-t">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2 text-sm">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span>Target: {formatDate(goal.target_date)}</span>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-40">
                    <div className="flex justify-between text-xs mb-1">
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
                      <span className="text-sm w-12">{goal.progress}%</span>
                    </div>
                  )}
                </div>
              </div>

              {goal.manager_comments && (
                <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                  <p className="text-xs font-medium text-blue-700 mb-1">Manager Comments</p>
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
                  <Target className="h-4 w-4 mr-2" />
                  Add Goal
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
