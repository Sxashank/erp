import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertCircle,
  CheckCircle,
  Clock,
  Eye,
  Filter,
  MoreHorizontal,
  ThumbsDown,
  ThumbsUp,
  User,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/common/PageHeader';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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

interface WorkflowTask {
  id: string;
  workflow_name: string;
  workflow_code: string;
  step_name: string;
  entity_type: string;
  entity_id: string;
  entity_reference: string;
  entity_description: string;
  assigned_to_id: string;
  assigned_to_name: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'ESCALATED';
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  due_date?: string;
  created_at: string;
  completed_at?: string;
  remarks?: string;
  is_overdue: boolean;
}

const STATUSES = [
  { value: 'all', label: 'All Statuses' },
  { value: 'PENDING', label: 'Pending' },
  { value: 'APPROVED', label: 'Approved' },
  { value: 'REJECTED', label: 'Rejected' },
  { value: 'ESCALATED', label: 'Escalated' },
];

const PRIORITIES = [
  { value: 'all', label: 'All Priorities' },
  { value: 'LOW', label: 'Low' },
  { value: 'MEDIUM', label: 'Medium' },
  { value: 'HIGH', label: 'High' },
  { value: 'CRITICAL', label: 'Critical' },
];

export function WorkflowTaskList() {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<WorkflowTask[]>([]);
  const [selectedStatus, setSelectedStatus] = useState<string>('PENDING');
  const [selectedPriority, setSelectedPriority] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<string>('my-tasks');

  useEffect(() => {
    fetchTasks();
  }, [selectedStatus, selectedPriority, activeTab]);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      // Mock data - replace with actual API call
      const mockTasks: WorkflowTask[] = [
        {
          id: '1',
          workflow_name: 'Loan Application Approval',
          workflow_code: 'WF-LOAN-APP',
          step_name: 'Credit Manager Approval',
          entity_type: 'loan_application',
          entity_id: 'app1',
          entity_reference: 'LOAN-2024-001234',
          entity_description: 'Personal Loan - John Doe - ₹5,00,000',
          assigned_to_id: 'user1',
          assigned_to_name: 'Current User',
          status: 'PENDING',
          priority: 'HIGH',
          due_date: '2024-12-15',
          created_at: '2024-12-10',
          is_overdue: false,
        },
        {
          id: '2',
          workflow_name: 'Disbursement Approval',
          workflow_code: 'WF-DISB-APP',
          step_name: 'Finance Head Approval',
          entity_type: 'disbursement',
          entity_id: 'disb1',
          entity_reference: 'DISB-2024-000456',
          entity_description: 'Business Loan Disbursement - ABC Corp - ₹25,00,000',
          assigned_to_id: 'user1',
          assigned_to_name: 'Current User',
          status: 'PENDING',
          priority: 'CRITICAL',
          due_date: '2024-12-12',
          created_at: '2024-12-08',
          is_overdue: true,
        },
        {
          id: '3',
          workflow_name: 'Journal Voucher Approval',
          workflow_code: 'WF-VOUCHER',
          step_name: 'Accountant Review',
          entity_type: 'voucher',
          entity_id: 'voucher1',
          entity_reference: 'JV-2024-001234',
          entity_description: 'Salary Provision Entry - Dec 2024',
          assigned_to_id: 'user1',
          assigned_to_name: 'Current User',
          status: 'PENDING',
          priority: 'MEDIUM',
          due_date: '2024-12-20',
          created_at: '2024-12-12',
          is_overdue: false,
        },
        {
          id: '4',
          workflow_name: 'Leave Application Approval',
          workflow_code: 'WF-LEAVE',
          step_name: 'Manager Approval',
          entity_type: 'leave_application',
          entity_id: 'leave1',
          entity_reference: 'LV-2024-000789',
          entity_description: 'Annual Leave - Jane Smith - 5 days',
          assigned_to_id: 'user1',
          assigned_to_name: 'Current User',
          status: 'APPROVED',
          priority: 'LOW',
          created_at: '2024-12-05',
          completed_at: '2024-12-06',
          is_overdue: false,
          remarks: 'Approved as requested',
        },
      ];
      setTasks(mockTasks);
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PENDING':
        return <Badge className="bg-yellow-50 text-yellow-700 hover:bg-yellow-50">Pending</Badge>;
      case 'APPROVED':
        return <Badge className="bg-emerald-50 text-emerald-700 hover:bg-emerald-50">Approved</Badge>;
      case 'REJECTED':
        return <Badge className="bg-red-50 text-red-700 hover:bg-red-50">Rejected</Badge>;
      case 'ESCALATED':
        return <Badge className="bg-orange-50 text-orange-700 hover:bg-orange-50">Escalated</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'LOW':
        return <Badge variant="outline">Low</Badge>;
      case 'MEDIUM':
        return <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-50">Medium</Badge>;
      case 'HIGH':
        return <Badge className="bg-orange-50 text-orange-700 hover:bg-orange-50">High</Badge>;
      case 'CRITICAL':
        return <Badge className="bg-red-50 text-red-700 hover:bg-red-50">Critical</Badge>;
      default:
        return <Badge variant="outline">{priority}</Badge>;
    }
  };

  const pendingTasks = tasks.filter(t => t.status === 'PENDING');
  const overdueTasks = pendingTasks.filter(t => t.is_overdue);
  const completedTasks = tasks.filter(t => t.status === 'APPROVED' || t.status === 'REJECTED');

  return (
    <div className="space-y-6">
      <PageHeader
        title="Workflow Tasks"
        subtitle="Manage your pending approvals and tasks"
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Tasks</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{pendingTasks.length}</div>
            <p className="text-xs text-slate-500">Awaiting your action</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overdue</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{overdueTasks.length}</div>
            <p className="text-xs text-slate-500">Past due date</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed Today</CardTitle>
            <CheckCircle className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600">{completedTasks.length}</div>
            <p className="text-xs text-slate-500">Tasks completed</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Critical Priority</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {pendingTasks.filter(t => t.priority === 'CRITICAL').length}
            </div>
            <p className="text-xs text-slate-500">Need immediate attention</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="my-tasks">My Tasks</TabsTrigger>
          <TabsTrigger value="all-tasks">All Tasks</TabsTrigger>
          <TabsTrigger value="completed">Completed</TabsTrigger>
        </TabsList>

        <TabsContent value="my-tasks">
          <Card>
            <CardHeader>
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <CardTitle>Pending Approvals</CardTitle>
                <div className="flex flex-wrap items-center gap-2">
                  <Select value={selectedPriority} onValueChange={setSelectedPriority}>
                    <SelectTrigger className="w-[140px]">
                      <SelectValue placeholder="All Priorities" />
                    </SelectTrigger>
                    <SelectContent>
                      {PRIORITIES.map((priority) => (
                        <SelectItem key={priority.value} value={priority.value}>
                          {priority.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <p className="text-sm text-slate-500">Loading...</p>
                </div>
              ) : pendingTasks.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <CheckCircle className="mb-4 h-12 w-12 text-emerald-300" />
                  <p className="text-sm text-slate-500">No pending tasks. You're all caught up!</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Reference</TableHead>
                      <TableHead>Workflow</TableHead>
                      <TableHead>Step</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead>Due Date</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="w-[100px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pendingTasks.map((task) => (
                      <TableRow key={task.id} className={task.is_overdue ? 'bg-red-50/50' : ''}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{task.entity_reference}</p>
                            <p className="text-sm text-slate-500">{task.entity_description}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{task.workflow_code}</p>
                            <p className="text-sm text-slate-500">{task.workflow_name}</p>
                          </div>
                        </TableCell>
                        <TableCell>{task.step_name}</TableCell>
                        <TableCell>{getPriorityBadge(task.priority)}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            {task.is_overdue && <AlertCircle className="h-3 w-3 text-red-500" />}
                            <span className={task.is_overdue ? 'text-red-600 font-medium' : ''}>
                              {formatDate(task.due_date)}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>{getStatusBadge(task.status)}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
                              title="Approve"
                            >
                              <ThumbsUp className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-red-600 hover:text-red-700 hover:bg-red-50"
                              title="Reject"
                            >
                              <ThumbsDown className="h-4 w-4" />
                            </Button>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8">
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem>
                                  <Eye className="mr-2 h-4 w-4" />
                                  View Details
                                </DropdownMenuItem>
                                <DropdownMenuItem>
                                  <User className="mr-2 h-4 w-4" />
                                  Delegate
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="all-tasks">
          <Card>
            <CardHeader>
              <CardTitle>All Tasks</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-500">View all tasks across the organization</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="completed">
          <Card>
            <CardHeader>
              <CardTitle>Completed Tasks</CardTitle>
            </CardHeader>
            <CardContent>
              {completedTasks.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <Clock className="mb-4 h-12 w-12 text-slate-300" />
                  <p className="text-sm text-slate-500">No completed tasks yet</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Reference</TableHead>
                      <TableHead>Workflow</TableHead>
                      <TableHead>Completed</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Remarks</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {completedTasks.map((task) => (
                      <TableRow key={task.id}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{task.entity_reference}</p>
                            <p className="text-sm text-slate-500">{task.entity_description}</p>
                          </div>
                        </TableCell>
                        <TableCell>{task.workflow_name}</TableCell>
                        <TableCell>{formatDate(task.completed_at)}</TableCell>
                        <TableCell>{getStatusBadge(task.status)}</TableCell>
                        <TableCell>{task.remarks || '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
