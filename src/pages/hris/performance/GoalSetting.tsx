import { zodResolver } from '@hookform/resolvers/zod';
import { useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { z } from 'zod';

import { DataTable, type Column } from '@/components/common/DataTable';
import { DateDisplay } from '@/components/common/DateDisplay';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { StatusPill } from '@/components/common/StatusPill';
import { HrisConfirmDialog } from '@/components/hris/HrisConfirmDialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import {
  useCycleEmployees,
  useCreateGoal,
  useDeleteGoal,
  useEmployeePerformanceDetail,
  usePerformanceCycle,
  useSubmitGoals,
  useUpdateGoal,
} from '@/hooks/hris/usePerformance';
import { useToast } from '@/hooks/use-toast';
import type {
  PerformanceEmployeeSummary,
  PerformanceGoal,
  PerformanceGoalPayload,
} from '@/services/hris/performanceApi';

const goalSchema = z.object({
  title: z.string().min(5, 'Goal title must be at least 5 characters'),
  description: z.string().optional(),
  category: z.string().optional(),
  weightage: z.coerce.number().min(1).max(100),
  targetValue: z.string().optional(),
  measurementCriteria: z.string().min(5, 'Measurement criteria is required'),
  startDate: z.string().optional(),
  dueDate: z.string().optional(),
});

type GoalFormValues = z.infer<typeof goalSchema>;
type GoalFormInput = z.input<typeof goalSchema>;

function SummaryCard({
  title,
  value,
  subtitle,
}: {
  title: string;
  value: string | number;
  subtitle: string;
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <p className="text-sm text-muted-foreground">{title}</p>
        <p className="mt-2 text-3xl font-semibold">{value}</p>
        <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>
      </CardContent>
    </Card>
  );
}

function GoalDialog({
  open,
  initialGoal,
  pending,
  onOpenChange,
  onSubmit,
}: {
  open: boolean;
  initialGoal?: PerformanceGoal | null;
  pending: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (payload: GoalFormValues) => Promise<void>;
}) {
  const form = useForm<GoalFormInput, unknown, GoalFormValues>({
    resolver: zodResolver(goalSchema),
    values: initialGoal
      ? {
          title: initialGoal.title,
          description: initialGoal.description ?? '',
          category: initialGoal.category ?? '',
          weightage: initialGoal.weightage,
          targetValue: initialGoal.targetValue ?? '',
          measurementCriteria: initialGoal.measurementCriteria ?? '',
          startDate: initialGoal.startDate ?? '',
          dueDate: initialGoal.dueDate ?? '',
        }
      : {
          title: '',
          description: '',
          category: '',
          weightage: 20,
          targetValue: '',
          measurementCriteria: '',
          startDate: '',
          dueDate: '',
        },
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{initialGoal ? 'Edit Goal' : 'Add Goal'}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form
            className="space-y-4"
            onSubmit={form.handleSubmit(async (values) => {
              await onSubmit(values);
              form.reset();
            })}
          >
            <div className="grid gap-4 md:grid-cols-2">
              <FormField
                control={form.control}
                name="title"
                render={({ field }) => (
                  <FormItem className="md:col-span-2">
                    <FormLabel>Goal Title</FormLabel>
                    <FormControl>
                      <Input placeholder="Improve monthly collection efficiency" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="category"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Category</FormLabel>
                    <FormControl>
                      <Input placeholder="BUSINESS / FUNCTIONAL / DEVELOPMENT" {...field} />
                    </FormControl>
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
                        min={1}
                        max={100}
                        value={field.value == null ? '' : String(field.value)}
                        onChange={(event) => field.onChange(event.target.value)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="startDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Start Date</FormLabel>
                    <FormControl>
                      <Input type="date" value={field.value ?? ''} onChange={field.onChange} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="dueDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Due Date</FormLabel>
                    <FormControl>
                      <Input type="date" value={field.value ?? ''} onChange={field.onChange} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="targetValue"
                render={({ field }) => (
                  <FormItem className="md:col-span-2">
                    <FormLabel>Target Value</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="98% efficiency / 50 accounts / 0 overdue exceptions"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="measurementCriteria"
                render={({ field }) => (
                  <FormItem className="md:col-span-2">
                    <FormLabel>Measurement Criteria</FormLabel>
                    <FormControl>
                      <Textarea
                        rows={3}
                        placeholder="Define how the goal will be measured and reviewed."
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem className="md:col-span-2">
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Textarea rows={3} placeholder="Goal context and scope" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={pending}>
                {pending ? 'Saving…' : initialGoal ? 'Update Goal' : 'Add Goal'}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

export default function GoalSetting() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { cycleId, employeeId: employeeIdParam } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedEmployeeId = searchParams.get('employeeId') ?? employeeIdParam ?? '';
  const [goalDialogOpen, setGoalDialogOpen] = useState(false);
  const [editingGoal, setEditingGoal] = useState<PerformanceGoal | null>(null);
  const [goalToDelete, setGoalToDelete] = useState<PerformanceGoal | null>(null);

  const cycleQuery = usePerformanceCycle(cycleId);
  const employeesQuery = useCycleEmployees(cycleId);
  const detailQuery = useEmployeePerformanceDetail(cycleId, selectedEmployeeId || undefined);
  const createGoalMutation = useCreateGoal(cycleId ?? '', selectedEmployeeId || '');
  const updateGoalMutation = useUpdateGoal();
  const deleteGoalMutation = useDeleteGoal();
  const submitGoalsMutation = useSubmitGoals(cycleId ?? '', selectedEmployeeId || '');

  const employeeOptions = employeesQuery.data ?? [];
  const currentEmployee = employeeOptions.find(
    (employee) => employee.employeeId === selectedEmployeeId,
  );
  const goals = detailQuery.data?.goals ?? [];
  const totalWeightage = useMemo(
    () => goals.reduce((sum, goal) => sum + Number(goal.weightage), 0),
    [goals],
  );
  const canEditGoals = detailQuery.data?.appraisal.status === 'GOAL_SETTING';

  if (!cycleId) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Goal Setting"
          subtitle="Select a cycle from the appraisal workbench to manage an employee goal packet."
          breadcrumbs={[
            { label: 'Performance Cycles', to: '/admin/hris/performance/cycles' },
            { label: 'Goal Setting' },
          ]}
        />
        <EmptyState
          title="No cycle selected"
          subtitle="Goal packets are managed inside a specific appraisal cycle."
          action={
            <Button onClick={() => navigate('/admin/hris/performance/cycles')}>
              Back to Cycles
            </Button>
          }
        />
      </div>
    );
  }

  if (cycleQuery.isError) {
    return <ErrorState error={cycleQuery.error} onRetry={() => void cycleQuery.refetch()} />;
  }

  if (!selectedEmployeeId) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Goal Setting"
          subtitle={cycleQuery.data?.name ?? 'Appraisal Cycle'}
          breadcrumbs={[
            { label: 'Performance Cycles', to: '/admin/hris/performance/cycles' },
            {
              label: cycleQuery.data?.name ?? 'Cycle',
              to: `/admin/hris/performance/cycles/${cycleId}`,
            },
            { label: 'Goal Setting' },
          ]}
        />
        <DataTable
          data={employeeOptions}
          columns={[
            {
              key: 'employeeName',
              header: 'Employee',
              render: (row: PerformanceEmployeeSummary) => (
                <div>
                  <div className="font-medium">{row.employeeName}</div>
                  <div className="text-xs text-muted-foreground">
                    {row.employeeCode}
                    {row.department ? ` · ${row.department}` : ''}
                  </div>
                </div>
              ),
            },
            {
              key: 'status',
              header: 'Status',
              render: (row: PerformanceEmployeeSummary) => (
                <StatusPill type="application" status={row.status} />
              ),
            },
            {
              key: 'goalCount',
              header: 'Goals',
              align: 'right',
              render: (row: PerformanceEmployeeSummary) => `${row.submittedGoals}/${row.goalCount}`,
            },
          ]}
          getRowId={(row) => row.appraisalId}
          isLoading={employeesQuery.isLoading}
          error={employeesQuery.error}
          onRetry={() => void employeesQuery.refetch()}
          onRowClick={(row) => setSearchParams({ employeeId: row.employeeId })}
          emptyTitle="No employee packets"
          emptySubtitle="Create a cycle with employees before assigning goals."
        />
      </div>
    );
  }

  const handleSaveGoal = async (values: GoalFormValues) => {
    const payload: PerformanceGoalPayload = {
      title: values.title,
      description: values.description || undefined,
      category: values.category || undefined,
      weightage: values.weightage,
      targetValue: values.targetValue || undefined,
      measurementCriteria: values.measurementCriteria || undefined,
      startDate: values.startDate || null,
      dueDate: values.dueDate || null,
    };
    if (editingGoal) {
      await updateGoalMutation.mutateAsync({ goalId: editingGoal.id, payload });
      toast({ title: 'Goal updated' });
    } else {
      await createGoalMutation.mutateAsync(payload);
      toast({ title: 'Goal added' });
    }
    setEditingGoal(null);
    setGoalDialogOpen(false);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Goal Setting"
        subtitle={cycleQuery.data?.name ?? 'Appraisal Cycle'}
        breadcrumbs={[
          { label: 'Performance Cycles', to: '/admin/hris/performance/cycles' },
          {
            label: cycleQuery.data?.name ?? 'Cycle',
            to: `/admin/hris/performance/cycles/${cycleId}`,
          },
          { label: 'Goal Setting' },
        ]}
        actions={
          <div className="flex gap-2">
            <Select
              value={selectedEmployeeId}
              onValueChange={(value) => setSearchParams({ employeeId: value })}
            >
              <SelectTrigger className="w-[280px]">
                <SelectValue placeholder="Select employee" />
              </SelectTrigger>
              <SelectContent>
                {employeeOptions.map((employee) => (
                  <SelectItem key={employee.employeeId} value={employee.employeeId}>
                    {employee.employeeName} ({employee.employeeCode})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              onClick={() => {
                setEditingGoal(null);
                setGoalDialogOpen(true);
              }}
              disabled={!canEditGoals}
            >
              Add Goal
            </Button>
            <Button
              onClick={() => void submitGoalsMutation.mutateAsync()}
              disabled={
                !canEditGoals ||
                goals.length === 0 ||
                totalWeightage !== 100 ||
                submitGoalsMutation.isPending
              }
            >
              {submitGoalsMutation.isPending ? 'Submitting…' : 'Submit Goals'}
            </Button>
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <SummaryCard
          title="Employee"
          value={currentEmployee?.employeeName ?? '—'}
          subtitle={currentEmployee?.employeeCode ?? 'Select an employee'}
        />
        <SummaryCard
          title="Packet Status"
          value={detailQuery.data?.appraisal.status ?? '—'}
          subtitle={currentEmployee?.reviewerName ?? 'Reviewer not assigned'}
        />
        <SummaryCard
          title="Goal Weightage"
          value={`${totalWeightage}%`}
          subtitle="Must total 100% before submission"
        />
        <SummaryCard
          title="Self Appraisal Deadline"
          value={detailQuery.data?.cycle.selfAppraisalEnd ?? '—'}
          subtitle={
            detailQuery.data?.cycle.selfAppraisalEnd
              ? 'Cycle self-appraisal deadline'
              : 'No deadline configured'
          }
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Employee Packet</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div>
            <Label className="text-muted-foreground">Employee</Label>
            <p className="mt-1 font-medium">{currentEmployee?.employeeName ?? '—'}</p>
          </div>
          <div>
            <Label className="text-muted-foreground">Department</Label>
            <p className="mt-1 font-medium">{currentEmployee?.department ?? '—'}</p>
          </div>
          <div>
            <Label className="text-muted-foreground">Designation</Label>
            <p className="mt-1 font-medium">{currentEmployee?.designation ?? '—'}</p>
          </div>
          <div>
            <Label className="text-muted-foreground">Reviewer</Label>
            <p className="mt-1 font-medium">{currentEmployee?.reviewerName ?? '—'}</p>
          </div>
        </CardContent>
      </Card>

      <DataTable
        data={goals}
        columns={[
          {
            key: 'title',
            header: 'Goal',
            render: (row: PerformanceGoal) => (
              <div>
                <div className="font-medium">{row.title}</div>
                <div className="text-xs text-muted-foreground">{row.category || 'General'}</div>
              </div>
            ),
          },
          {
            key: 'dueDate',
            header: 'Due Date',
            render: (row: PerformanceGoal) => <DateDisplay date={row.dueDate ?? null} />,
          },
          {
            key: 'weightage',
            header: 'Weight',
            align: 'right',
            render: (row: PerformanceGoal) => `${Number(row.weightage).toFixed(2)}%`,
            sortable: true,
            sortValue: (row: PerformanceGoal) => Number(row.weightage),
          },
          {
            key: 'progressPercent',
            header: 'Progress',
            align: 'right',
            render: (row: PerformanceGoal) => `${Number(row.progressPercent).toFixed(2)}%`,
          },
          {
            key: 'status',
            header: 'Status',
            render: (row: PerformanceGoal) => <StatusPill type="application" status={row.status} />,
          },
          {
            key: 'actions',
            header: 'Actions',
            render: (row: PerformanceGoal) => (
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setEditingGoal(row);
                    setGoalDialogOpen(true);
                  }}
                  disabled={!canEditGoals}
                >
                  Edit
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setGoalToDelete(row)}
                  disabled={!canEditGoals}
                >
                  Delete
                </Button>
              </div>
            ),
          },
        ]}
        getRowId={(row) => row.id}
        isLoading={detailQuery.isLoading}
        error={detailQuery.error}
        onRetry={() => void detailQuery.refetch()}
        emptyTitle="No goals created"
        emptySubtitle="Add goals for this employee before submitting the goal packet."
      />

      <GoalDialog
        open={goalDialogOpen}
        initialGoal={editingGoal}
        pending={createGoalMutation.isPending || updateGoalMutation.isPending}
        onOpenChange={(open) => {
          setGoalDialogOpen(open);
          if (!open) {
            setEditingGoal(null);
          }
        }}
        onSubmit={handleSaveGoal}
      />

      <HrisConfirmDialog
        open={Boolean(goalToDelete)}
        title="Delete goal"
        description={`Remove "${goalToDelete?.title ?? 'this goal'}" from the employee packet?`}
        confirmLabel="Delete Goal"
        destructive
        busy={deleteGoalMutation.isPending}
        onOpenChange={(open) => {
          if (!open) {
            setGoalToDelete(null);
          }
        }}
        onConfirm={() => {
          if (!goalToDelete) return;
          void deleteGoalMutation.mutateAsync(goalToDelete.id).then(() => {
            toast({ title: 'Goal deleted' });
            setGoalToDelete(null);
          });
        }}
      />
    </div>
  );
}
