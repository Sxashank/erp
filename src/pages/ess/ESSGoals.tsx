import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Target,
  Plus,
  Edit,
  CheckCircle,
  Clock,
  AlertCircle,
  TrendingUp,
  Calendar,
} from 'lucide-react';

// Mock data - Goals
const goals = [
  {
    id: '1',
    title: 'Complete AWS Certification',
    description: 'Achieve AWS Solutions Architect Associate certification',
    category: 'SKILL_DEVELOPMENT',
    priority: 'HIGH',
    startDate: '2025-01-01',
    dueDate: '2025-06-30',
    status: 'IN_PROGRESS',
    progress: 35,
    weight: 20,
    milestones: [
      { id: '1', title: 'Complete online course', completed: true, dueDate: '2025-02-28' },
      { id: '2', title: 'Practice exams', completed: false, dueDate: '2025-04-30' },
      { id: '3', title: 'Take certification exam', completed: false, dueDate: '2025-06-30' },
    ],
  },
  {
    id: '2',
    title: 'Deliver Project Alpha on time',
    description: 'Successfully deliver all milestones of Project Alpha within budget and timeline',
    category: 'PROJECT',
    priority: 'HIGH',
    startDate: '2024-10-01',
    dueDate: '2025-03-31',
    status: 'IN_PROGRESS',
    progress: 70,
    weight: 30,
    milestones: [
      { id: '1', title: 'Phase 1 - Requirements', completed: true, dueDate: '2024-11-15' },
      { id: '2', title: 'Phase 2 - Development', completed: true, dueDate: '2025-01-31' },
      { id: '3', title: 'Phase 3 - Testing', completed: false, dueDate: '2025-02-28' },
      { id: '4', title: 'Phase 4 - Deployment', completed: false, dueDate: '2025-03-31' },
    ],
  },
  {
    id: '3',
    title: 'Mentor 2 Junior Developers',
    description: 'Provide guidance and mentorship to junior team members',
    category: 'LEADERSHIP',
    priority: 'MEDIUM',
    startDate: '2025-01-01',
    dueDate: '2025-12-31',
    status: 'IN_PROGRESS',
    progress: 25,
    weight: 15,
    milestones: [
      { id: '1', title: 'Weekly 1:1 sessions established', completed: true, dueDate: '2025-01-31' },
      { id: '2', title: 'Code review sessions', completed: false, dueDate: '2025-06-30' },
      { id: '3', title: 'Knowledge transfer complete', completed: false, dueDate: '2025-12-31' },
    ],
  },
  {
    id: '4',
    title: 'Improve Code Quality',
    description: 'Achieve 90%+ code coverage and reduce bugs by 30%',
    category: 'QUALITY',
    priority: 'MEDIUM',
    startDate: '2025-01-01',
    dueDate: '2025-12-31',
    status: 'NOT_STARTED',
    progress: 0,
    weight: 20,
    milestones: [],
  },
  {
    id: '5',
    title: 'Client Satisfaction Score',
    description: 'Achieve average client satisfaction score of 4.5+',
    category: 'CUSTOMER',
    priority: 'HIGH',
    startDate: '2025-01-01',
    dueDate: '2025-12-31',
    status: 'IN_PROGRESS',
    progress: 50,
    weight: 15,
    milestones: [],
  },
];

const categories = [
  { value: 'PROJECT', label: 'Project Delivery' },
  { value: 'SKILL_DEVELOPMENT', label: 'Skill Development' },
  { value: 'LEADERSHIP', label: 'Leadership' },
  { value: 'QUALITY', label: 'Quality' },
  { value: 'CUSTOMER', label: 'Customer Focus' },
];

const priorities = [
  { value: 'HIGH', label: 'High' },
  { value: 'MEDIUM', label: 'Medium' },
  { value: 'LOW', label: 'Low' },
];

export default function ESSGoals() {
  const [selectedGoal, setSelectedGoal] = useState<typeof goals[0] | null>(null);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'NOT_STARTED':
        return <Badge variant="outline">Not Started</Badge>;
      case 'IN_PROGRESS':
        return <Badge variant="secondary" className="bg-blue-100 text-blue-800">In Progress</Badge>;
      case 'COMPLETED':
        return <Badge variant="default" className="bg-green-500">Completed</Badge>;
      case 'AT_RISK':
        return <Badge variant="destructive">At Risk</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'HIGH':
        return <Badge variant="destructive">High</Badge>;
      case 'MEDIUM':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Medium</Badge>;
      case 'LOW':
        return <Badge variant="outline">Low</Badge>;
      default:
        return <Badge variant="outline">{priority}</Badge>;
    }
  };

  const getCategoryLabel = (category: string) => {
    return categories.find(c => c.value === category)?.label || category;
  };

  const getProgressColor = (progress: number) => {
    if (progress >= 70) return 'bg-green-500';
    if (progress >= 40) return 'bg-blue-500';
    if (progress > 0) return 'bg-yellow-500';
    return 'bg-gray-300';
  };

  const overallProgress = Math.round(
    goals.reduce((sum, g) => sum + (g.progress * g.weight / 100), 0)
  );

  const goalsInProgress = goals.filter(g => g.status === 'IN_PROGRESS').length;
  const goalsCompleted = goals.filter(g => g.status === 'COMPLETED').length;

  const addGoalDialog = (
    <Dialog>
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Add Goal
        </Button>
      </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Add New Goal</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <label className="text-sm font-medium">Goal Title</label>
                <Input placeholder="Enter goal title" className="mt-1" />
              </div>
              <div>
                <label className="text-sm font-medium">Description</label>
                <Textarea placeholder="Describe your goal" className="mt-1" rows={3} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Category</label>
                  <Select>
                    <SelectTrigger className="mt-1">
                      <SelectValue placeholder="Select" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map(c => (
                        <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium">Priority</label>
                  <Select>
                    <SelectTrigger className="mt-1">
                      <SelectValue placeholder="Select" />
                    </SelectTrigger>
                    <SelectContent>
                      {priorities.map(p => (
                        <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Start Date</label>
                  <Input type="date" className="mt-1" />
                </div>
                <div>
                  <label className="text-sm font-medium">Due Date</label>
                  <Input type="date" className="mt-1" />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium">Weight (%)</label>
                <Input type="number" min="0" max="100" placeholder="20" className="mt-1" />
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline">Cancel</Button>
                <Button>Save Goal</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Goals"
        subtitle="Track your performance goals for the appraisal cycle"
        actions={addGoalDialog}
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Target className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{goals.length}</div>
                <div className="text-sm text-muted-foreground">Total Goals</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-yellow-100 rounded-lg">
                <Clock className="h-6 w-6 text-yellow-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{goalsInProgress}</div>
                <div className="text-sm text-muted-foreground">In Progress</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{goalsCompleted}</div>
                <div className="text-sm text-muted-foreground">Completed</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-100 rounded-lg">
                <TrendingUp className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{overallProgress}%</div>
                <div className="text-sm text-muted-foreground">Overall Progress</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Goals List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {goals.map((goal) => (
          <Card key={goal.id} className="cursor-pointer hover:shadow-md transition-shadow">
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold">{goal.title}</h3>
                    <p className="text-sm text-muted-foreground mt-1">{goal.description}</p>
                  </div>
                  <Button variant="ghost" size="icon">
                    <Edit className="h-4 w-4" />
                  </Button>
                </div>

                <div className="flex flex-wrap gap-2">
                  {getStatusBadge(goal.status)}
                  {getPriorityBadge(goal.priority)}
                  <Badge variant="outline">{getCategoryLabel(goal.category)}</Badge>
                  <Badge variant="outline">Weight: {goal.weight}%</Badge>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Progress</span>
                    <span className="font-medium">{goal.progress}%</span>
                  </div>
                  <Progress value={goal.progress} className={getProgressColor(goal.progress)} />
                </div>

                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    Due: {goal.dueDate}
                  </div>
                  {goal.milestones.length > 0 && (
                    <div className="flex items-center gap-1">
                      <CheckCircle className="h-4 w-4" />
                      {goal.milestones.filter(m => m.completed).length}/{goal.milestones.length} milestones
                    </div>
                  )}
                </div>

                {goal.milestones.length > 0 && (
                  <div className="border-t pt-3 mt-3">
                    <div className="text-sm font-medium mb-2">Milestones</div>
                    <div className="space-y-2">
                      {goal.milestones.slice(0, 3).map((milestone) => (
                        <div key={milestone.id} className="flex items-center gap-2 text-sm">
                          {milestone.completed ? (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          ) : (
                            <Clock className="h-4 w-4 text-muted-foreground" />
                          )}
                          <span className={milestone.completed ? 'line-through text-muted-foreground' : ''}>
                            {milestone.title}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
