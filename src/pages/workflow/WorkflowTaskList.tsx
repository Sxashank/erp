import {
  AlertCircle,
  CheckCircle,
  Clock,
  Eye,
  Loader2,
  MoreHorizontal,
  ThumbsDown,
  ThumbsUp,
  User,
} from 'lucide-react';
import { useMemo, useState } from 'react';

import { DateDisplay, EmptyState, ErrorState, PageHeader, SkeletonTable } from '@/components/common';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
import { useToast } from '@/hooks/use-toast';
import { useOrganization } from '@/hooks/useOrganization';
import {
  useApproveTask,
  useDelegateTask,
  usePendingTasks,
} from '@/hooks/workflow/useWorkflowTasks';
import { showErrorToast } from '@/lib/errorToast';
import type { TaskStatus, WorkflowTaskResponse } from '@/services/workflow/workflowApi';

const STATUS_FILTERS: { value: 'all' | TaskStatus; label: string }[] = [
  { value: 'all', label: 'All Statuses' },
  { value: 'PENDING', label: 'Pending' },
  { value: 'APPROVED', label: 'Approved' },
  { value: 'REJECTED', label: 'Rejected' },
  { value: 'ESCALATED', label: 'Escalated' },
  { value: 'SKIPPED', label: 'Skipped' },
];

function getStatusBadge(status: TaskStatus): JSX.Element {
  switch (status) {
    case 'PENDING':
      return <Badge className="bg-yellow-50 text-yellow-700 hover:bg-yellow-50">Pending</Badge>;
    case 'APPROVED':
      return <Badge className="bg-emerald-50 text-emerald-700 hover:bg-emerald-50">Approved</Badge>;
    case 'REJECTED':
      return <Badge className="bg-red-50 text-red-700 hover:bg-red-50">Rejected</Badge>;
    case 'ESCALATED':
      return <Badge className="bg-orange-50 text-orange-700 hover:bg-orange-50">Escalated</Badge>;
    case 'SKIPPED':
      return <Badge variant="outline">Skipped</Badge>;
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
}

interface ApprovalDialogState {
  task: WorkflowTaskResponse;
  action: 'APPROVE' | 'REJECT';
}

export function WorkflowTaskList(): JSX.Element {
  const { toast } = useToast();
  const { activeOrganizationId } = useOrganization();

  const [statusFilter, setStatusFilter] = useState<'all' | TaskStatus>('PENDING');
  const [activeTab, setActiveTab] = useState<'my-tasks' | 'completed'>('my-tasks');

  const [approvalDialog, setApprovalDialog] = useState<ApprovalDialogState | null>(null);
  const [approvalComments, setApprovalComments] = useState('');

  const [delegateDialog, setDelegateDialog] = useState<WorkflowTaskResponse | null>(null);
  const [delegateTo, setDelegateTo] = useState('');
  const [delegateReason, setDelegateReason] = useState('');

  const tasksQuery = usePendingTasks(
    activeOrganizationId ? {} : undefined,
  );
  const approveMutation = useApproveTask();
  const delegateMutation = useDelegateTask();

  const allTasks = useMemo(() => tasksQuery.data ?? [], [tasksQuery.data]);

  const filteredTasks = useMemo(() => {
    if (statusFilter === 'all') return allTasks;
    return allTasks.filter((t) => t.status === statusFilter);
  }, [allTasks, statusFilter]);

  const pendingTasks = allTasks.filter((t) => t.status === 'PENDING');
  const overdueTasks = pendingTasks.filter((t) => t.isOverdue);
  const escalatedTasks = allTasks.filter((t) => t.status === 'ESCALATED');
  const completedTasks = allTasks.filter((t) => t.status === 'APPROVED' || t.status === 'REJECTED');

  const handleApprovalSubmit = () => {
    if (!approvalDialog) return;
    approveMutation.mutate(
      {
        id: approvalDialog.task.id,
        body: {
          action: approvalDialog.action,
          comments: approvalComments.trim() || undefined,
        },
      },
      {
        onSuccess: () => {
          toast({
            title: approvalDialog.action === 'APPROVE' ? 'Task approved' : 'Task rejected',
            description: `${approvalDialog.task.stepName ?? 'Step'} updated.`,
          });
          setApprovalDialog(null);
          setApprovalComments('');
        },
        onError: (err) => showErrorToast(err, toast),
      },
    );
  };

  const handleDelegateSubmit = () => {
    if (!delegateDialog) return;
    const reason = delegateReason.trim();
    const userId = delegateTo.trim();
    if (!userId || !reason) {
      toast({
        title: 'Missing information',
        description: 'Please provide both a delegate user ID and a reason.',
        variant: 'destructive',
      });
      return;
    }
    delegateMutation.mutate(
      { id: delegateDialog.id, body: { delegateTo: userId, reason } },
      {
        onSuccess: () => {
          toast({
            title: 'Task delegated',
            description: 'The task has been re-assigned.',
          });
          setDelegateDialog(null);
          setDelegateTo('');
          setDelegateReason('');
        },
        onError: (err) => showErrorToast(err, toast),
      },
    );
  };

  return (
    <div className="space-y-6">
      <PageHeader title="Workflow Tasks" subtitle="Manage your pending approvals and tasks" />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Tasks</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{pendingTasks.length}</div>
            <p className="text-xs text-muted-foreground">Awaiting your action</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overdue</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{overdueTasks.length}</div>
            <p className="text-xs text-muted-foreground">Past due date</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Escalated</CardTitle>
            <AlertCircle className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{escalatedTasks.length}</div>
            <p className="text-xs text-muted-foreground">Need attention</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600">{completedTasks.length}</div>
            <p className="text-xs text-muted-foreground">Tasks completed</p>
          </CardContent>
        </Card>
      </div>

      <Tabs
        value={activeTab}
        onValueChange={(v) => setActiveTab(v as typeof activeTab)}
        className="space-y-4"
      >
        <TabsList>
          <TabsTrigger value="my-tasks">My Tasks</TabsTrigger>
          <TabsTrigger value="completed">Completed</TabsTrigger>
        </TabsList>

        <TabsContent value="my-tasks">
          <Card>
            <CardHeader>
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <CardTitle>Pending Approvals</CardTitle>
                <div className="flex flex-wrap items-center gap-2">
                  <Select
                    value={statusFilter}
                    onValueChange={(v) => setStatusFilter(v as 'all' | TaskStatus)}
                  >
                    <SelectTrigger className="w-[160px]">
                      <SelectValue placeholder="All Statuses" />
                    </SelectTrigger>
                    <SelectContent>
                      {STATUS_FILTERS.map((s) => (
                        <SelectItem key={s.value} value={s.value}>
                          {s.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {tasksQuery.isLoading ? (
                <SkeletonTable rows={6} columns={7} />
              ) : tasksQuery.isError ? (
                <ErrorState error={tasksQuery.error} onRetry={() => tasksQuery.refetch()} />
              ) : filteredTasks.length === 0 ? (
                <EmptyState
                  title="No pending tasks"
                  subtitle="You're all caught up. New approvals will appear here when assigned to you."
                  icon={CheckCircle}
                />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Step</TableHead>
                      <TableHead>Assigned</TableHead>
                      <TableHead>Due Date</TableHead>
                      <TableHead>Escalation</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="w-[140px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredTasks.map((task) => (
                      <TableRow key={task.id} className={task.isOverdue ? 'bg-red-50/50' : ''}>
                        <TableCell>
                          <div>
                            <p className="font-medium">
                              {task.stepName ?? 'Step'}{' '}
                              {task.stepNumber !== null && (
                                <span className="text-muted-foreground">(#{task.stepNumber})</span>
                              )}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              Task {task.id.slice(0, 8)}
                            </p>
                          </div>
                        </TableCell>
                        <TableCell className="text-sm tabular-nums">
                          <DateDisplay date={task.assignedAt} />
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            {task.isOverdue && <AlertCircle className="h-3 w-3 text-red-500" />}
                            <DateDisplay
                              date={task.dueAt}
                              className={
                                task.isOverdue
                                  ? 'font-medium tabular-nums text-red-600'
                                  : 'tabular-nums'
                              }
                            />
                          </div>
                        </TableCell>
                        <TableCell className="tabular-nums">
                          {task.escalationLevel > 0 ? (
                            <Badge className="bg-orange-50 text-orange-700 hover:bg-orange-50">
                              Level {task.escalationLevel}
                            </Badge>
                          ) : (
                            <span className="text-muted-foreground">—</span>
                          )}
                        </TableCell>
                        <TableCell>{getStatusBadge(task.status)}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-emerald-600 hover:bg-emerald-50 hover:text-emerald-700"
                              title="Approve"
                              disabled={task.status !== 'PENDING' || approveMutation.isPending}
                              onClick={() => {
                                setApprovalDialog({ task, action: 'APPROVE' });
                                setApprovalComments('');
                              }}
                            >
                              <ThumbsUp className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-red-600 hover:bg-red-50 hover:text-red-700"
                              title="Reject"
                              disabled={task.status !== 'PENDING' || approveMutation.isPending}
                              onClick={() => {
                                setApprovalDialog({ task, action: 'REJECT' });
                                setApprovalComments('');
                              }}
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
                                <DropdownMenuItem
                                  disabled={task.status !== 'PENDING'}
                                  onClick={() => {
                                    setDelegateDialog(task);
                                    setDelegateTo('');
                                    setDelegateReason('');
                                  }}
                                >
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

        <TabsContent value="completed">
          <Card>
            <CardHeader>
              <CardTitle>Completed Tasks</CardTitle>
            </CardHeader>
            <CardContent>
              {tasksQuery.isLoading ? (
                <SkeletonTable rows={4} columns={4} />
              ) : completedTasks.length === 0 ? (
                <EmptyState
                  title="No completed tasks yet"
                  subtitle="Tasks you've actioned will appear here."
                  icon={Clock}
                />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Step</TableHead>
                      <TableHead>Acted</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Comments</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {completedTasks.map((task) => (
                      <TableRow key={task.id}>
                        <TableCell>
                          <p className="font-medium">{task.stepName ?? 'Step'}</p>
                        </TableCell>
                        <TableCell className="text-sm tabular-nums">
                          <DateDisplay date={task.actedAt} />
                        </TableCell>
                        <TableCell>{getStatusBadge(task.status)}</TableCell>
                        <TableCell>{task.comments ?? '—'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Approve / Reject Dialog */}
      <Dialog
        open={approvalDialog !== null}
        onOpenChange={(open) => {
          if (!open) {
            setApprovalDialog(null);
            setApprovalComments('');
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {approvalDialog?.action === 'APPROVE' ? 'Approve task' : 'Reject task'}
            </DialogTitle>
            <DialogDescription>
              {approvalDialog?.task.stepName ?? 'Step'} — task{' '}
              {approvalDialog?.task.id.slice(0, 8)}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="approval-comments">Comments</Label>
            <Textarea
              id="approval-comments"
              placeholder={
                approvalDialog?.action === 'REJECT'
                  ? 'Reason for rejection (recommended)'
                  : 'Optional comments'
              }
              value={approvalComments}
              onChange={(e) => setApprovalComments(e.target.value)}
              rows={3}
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setApprovalDialog(null)}
              disabled={approveMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              variant={approvalDialog?.action === 'REJECT' ? 'destructive' : 'default'}
              disabled={approveMutation.isPending}
              onClick={handleApprovalSubmit}
            >
              {approveMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {approvalDialog?.action === 'APPROVE' ? 'Approve' : 'Reject'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delegate Dialog */}
      <Dialog
        open={delegateDialog !== null}
        onOpenChange={(open) => {
          if (!open) {
            setDelegateDialog(null);
            setDelegateTo('');
            setDelegateReason('');
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delegate task</DialogTitle>
            <DialogDescription>
              Reassign this task to another user. They will be responsible for the approval.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-2">
              <Label htmlFor="delegate-to">Delegate to (user ID)</Label>
              <Input
                id="delegate-to"
                placeholder="UUID of the target user"
                value={delegateTo}
                onChange={(e) => setDelegateTo(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="delegate-reason">Reason</Label>
              <Textarea
                id="delegate-reason"
                placeholder="Why is this being delegated?"
                value={delegateReason}
                onChange={(e) => setDelegateReason(e.target.value)}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDelegateDialog(null)}
              disabled={delegateMutation.isPending}
            >
              Cancel
            </Button>
            <Button disabled={delegateMutation.isPending} onClick={handleDelegateSubmit}>
              {delegateMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Delegate
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
