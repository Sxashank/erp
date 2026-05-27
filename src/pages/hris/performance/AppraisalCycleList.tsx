import { zodResolver } from '@hookform/resolvers/zod';
import { useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { z } from 'zod';

import { DataTable, type Column } from '@/components/common/DataTable';
import { DateDisplay } from '@/components/common/DateDisplay';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { FilterBar } from '@/components/common/FilterBar';
import { FormSection, FormShell } from '@/components/common/FormShell';
import { PageHeader } from '@/components/common/PageHeader';
import { StatusPill } from '@/components/common/StatusPill';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
import { useEmployeeDirectory } from '@/hooks/hris/useEmployeeDirectory';
import {
  useCloseCycle,
  useCreateCycle,
  useCycleEmployees,
  usePerformanceCycle,
  usePerformanceCycles,
  useStartCycle,
} from '@/hooks/hris/usePerformance';
import { useToast } from '@/hooks/use-toast';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import { useFinancialYears } from '@/hooks/finance/useAccounts';
import type {
  AppraisalCycleListItem,
  AppraisalCyclePayload,
  AppraisalStatus,
  AppraisalCycleStatus,
  PerformanceEmployeeSummary,
} from '@/services/hris/performanceApi';

const cycleFormSchema = z
  .object({
    name: z.string().min(5, 'Cycle name must be at least 5 characters'),
    description: z.string().optional(),
    financialYearId: z.string().optional(),
    cycleType: z.enum(['ANNUAL', 'HALF_YEARLY', 'QUARTERLY']),
    startDate: z.string().min(1, 'Start date is required'),
    endDate: z.string().min(1, 'End date is required'),
    goalSettingStart: z.string().optional(),
    goalSettingEnd: z.string().optional(),
    selfAppraisalStart: z.string().optional(),
    selfAppraisalEnd: z.string().optional(),
    managerReviewStart: z.string().optional(),
    managerReviewEnd: z.string().optional(),
    calibrationStart: z.string().optional(),
    calibrationEnd: z.string().optional(),
    ratingScale: z.coerce.number().min(3).max(10),
    weightageGoals: z.coerce.number().min(0).max(100),
    weightageCompetencies: z.coerce.number().min(0).max(100),
    allowSelfRating: z.boolean(),
    allowPeerFeedback: z.boolean(),
    includeAllActiveEmployees: z.boolean(),
    employeeIds: z.array(z.string()),
  })
  .refine((values) => values.weightageGoals + values.weightageCompetencies === 100, {
    message: 'Goal and competency weightage must total 100%',
    path: ['weightageCompetencies'],
  })
  .refine((values) => values.includeAllActiveEmployees || values.employeeIds.length > 0, {
    message: 'Select at least one employee when not including all active employees',
    path: ['employeeIds'],
  });

type CycleFormValues = z.infer<typeof cycleFormSchema>;
type CycleFormInput = z.input<typeof cycleFormSchema>;

function MetricCard({
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

function CycleCreateForm() {
  useRequiredActiveOrganizationId();
  const navigate = useNavigate();
  const { toast } = useToast();
  const financialYearsQuery = useFinancialYears();
  const employeesQuery = useEmployeeDirectory({ employmentStatus: 'ACTIVE' });
  const createCycleMutation = useCreateCycle();

  const form = useForm<CycleFormInput, unknown, CycleFormValues>({
    resolver: zodResolver(cycleFormSchema),
    defaultValues: {
      name: '',
      description: '',
      financialYearId: undefined,
      cycleType: 'ANNUAL',
      startDate: '',
      endDate: '',
      goalSettingStart: '',
      goalSettingEnd: '',
      selfAppraisalStart: '',
      selfAppraisalEnd: '',
      managerReviewStart: '',
      managerReviewEnd: '',
      calibrationStart: '',
      calibrationEnd: '',
      ratingScale: 5,
      weightageGoals: 70,
      weightageCompetencies: 30,
      allowSelfRating: true,
      allowPeerFeedback: false,
      includeAllActiveEmployees: true,
      employeeIds: [],
    },
  });

  const includeAllActiveEmployees = form.watch('includeAllActiveEmployees');
  const selectedEmployees = form.watch('employeeIds');

  const handleToggleEmployee = (employeeId: string, checked: boolean) => {
    const current = form.getValues('employeeIds');
    form.setValue(
      'employeeIds',
      checked ? [...current, employeeId] : current.filter((id) => id !== employeeId),
      { shouldValidate: true },
    );
  };

  const onSubmit = async (values: CycleFormValues) => {
    const payload: AppraisalCyclePayload = {
      name: values.name,
      description: values.description || undefined,
      financialYearId: values.financialYearId || null,
      cycleType: values.cycleType,
      startDate: values.startDate,
      endDate: values.endDate,
      goalSettingStart: values.goalSettingStart || null,
      goalSettingEnd: values.goalSettingEnd || null,
      selfAppraisalStart: values.selfAppraisalStart || null,
      selfAppraisalEnd: values.selfAppraisalEnd || null,
      managerReviewStart: values.managerReviewStart || null,
      managerReviewEnd: values.managerReviewEnd || null,
      calibrationStart: values.calibrationStart || null,
      calibrationEnd: values.calibrationEnd || null,
      ratingScale: values.ratingScale,
      weightageGoals: values.weightageGoals,
      weightageCompetencies: values.weightageCompetencies,
      allowSelfRating: values.allowSelfRating,
      allowPeerFeedback: values.allowPeerFeedback,
      includeAllActiveEmployees: values.includeAllActiveEmployees,
      employeeIds: values.employeeIds,
    };
    const cycle = await createCycleMutation.mutateAsync(payload);
    toast({
      title: 'Appraisal cycle created',
      description: `${cycle.name} is ready for HR review and start.`,
    });
    navigate(`/admin/hris/performance/cycles/${cycle.id}`);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Create Appraisal Cycle"
        subtitle="Define the cycle dates, rating model, and participating employees."
        breadcrumbs={[
          { label: 'Performance Cycles', to: '/admin/hris/performance/cycles' },
          { label: 'Create Cycle' },
        ]}
      />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <FormShell
            footer={
              <>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate('/admin/hris/performance/cycles')}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={createCycleMutation.isPending}>
                  {createCycleMutation.isPending ? 'Creating…' : 'Create Cycle'}
                </Button>
              </>
            }
          >
            <FormSection
              title="Cycle Definition"
              description="Set the operating window and rating structure for the appraisal cycle."
            >
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Cycle Name</FormLabel>
                    <FormControl>
                      <Input placeholder="FY 2026 Annual Appraisal" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="cycleType"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Cycle Type</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a cycle type" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="ANNUAL">Annual</SelectItem>
                        <SelectItem value="HALF_YEARLY">Half-Yearly</SelectItem>
                        <SelectItem value="QUARTERLY">Quarterly</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="financialYearId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Financial Year</FormLabel>
                    <Select
                      value={field.value ?? '__none__'}
                      onValueChange={(value) =>
                        field.onChange(value === '__none__' ? undefined : value)
                      }
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a financial year" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="__none__">No financial year link</SelectItem>
                        {(financialYearsQuery.data ?? []).map((year) => (
                          <SelectItem key={year.id} value={year.id}>
                            {year.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
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
                      <Textarea
                        rows={3}
                        placeholder="Annual corporate appraisal cycle for employee goal-setting and performance review."
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormSection>

            <FormSection
              title="Cycle Dates"
              description="Configure the timeline for goals, self-appraisal, manager review, and calibration."
            >
              {[
                ['startDate', 'Cycle Start'],
                ['endDate', 'Cycle End'],
                ['goalSettingStart', 'Goal Setting Start'],
                ['goalSettingEnd', 'Goal Setting End'],
                ['selfAppraisalStart', 'Self Appraisal Start'],
                ['selfAppraisalEnd', 'Self Appraisal End'],
                ['managerReviewStart', 'Manager Review Start'],
                ['managerReviewEnd', 'Manager Review End'],
                ['calibrationStart', 'Calibration Start'],
                ['calibrationEnd', 'Calibration End'],
              ].map(([name, label]) => (
                <FormField
                  key={name}
                  control={form.control}
                  name={name as keyof CycleFormValues}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{label}</FormLabel>
                      <FormControl>
                        <Input
                          type="date"
                          value={(field.value as string | undefined) ?? ''}
                          onChange={field.onChange}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              ))}
            </FormSection>

            <FormSection
              title="Rating Policy"
              description="Define rating scale and the goal-vs-competency contribution."
            >
              <FormField
                control={form.control}
                name="ratingScale"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Rating Scale</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={3}
                        max={10}
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
                name="weightageGoals"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Goal Weightage (%)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={0}
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
                name="weightageCompetencies"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Competency Weightage (%)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={0}
                        max={100}
                        value={field.value == null ? '' : String(field.value)}
                        onChange={(event) => field.onChange(event.target.value)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="space-y-3 md:col-span-2">
                <FormField
                  control={form.control}
                  name="allowSelfRating"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center gap-3 space-y-0 rounded-lg border p-4">
                      <FormControl>
                        <Checkbox
                          checked={field.value}
                          onCheckedChange={(checked) => field.onChange(Boolean(checked))}
                        />
                      </FormControl>
                      <div className="space-y-1">
                        <FormLabel className="font-medium">Allow self rating</FormLabel>
                        <p className="text-sm text-muted-foreground">
                          Employees can rate their own goals during self-appraisal.
                        </p>
                      </div>
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="allowPeerFeedback"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center gap-3 space-y-0 rounded-lg border p-4">
                      <FormControl>
                        <Checkbox
                          checked={field.value}
                          onCheckedChange={(checked) => field.onChange(Boolean(checked))}
                        />
                      </FormControl>
                      <div className="space-y-1">
                        <FormLabel className="font-medium">Allow peer feedback</FormLabel>
                        <p className="text-sm text-muted-foreground">
                          Keep disabled unless the organization is ready for a peer-feedback
                          process.
                        </p>
                      </div>
                    </FormItem>
                  )}
                />
              </div>
            </FormSection>

            <FormSection
              title="Employee Inclusion"
              description="Choose whether the cycle applies to all active employees or a selected cohort."
            >
              <div className="space-y-4 md:col-span-2">
                <FormField
                  control={form.control}
                  name="includeAllActiveEmployees"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center gap-3 space-y-0 rounded-lg border p-4">
                      <FormControl>
                        <Checkbox
                          checked={field.value}
                          onCheckedChange={(checked) => field.onChange(Boolean(checked))}
                        />
                      </FormControl>
                      <div className="space-y-1">
                        <FormLabel className="font-medium">Include all active employees</FormLabel>
                        <p className="text-sm text-muted-foreground">
                          Turn this off to create a cycle for a hand-picked employee group.
                        </p>
                      </div>
                    </FormItem>
                  )}
                />
                {!includeAllActiveEmployees && (
                  <div className="space-y-3 rounded-lg border p-4">
                    <Label>Select employees</Label>
                    <div className="max-h-72 space-y-3 overflow-y-auto">
                      {(employeesQuery.data ?? []).map((employee) => (
                        <label
                          key={employee.id}
                          className="flex items-start gap-3 rounded-md border p-3"
                        >
                          <Checkbox
                            checked={selectedEmployees.includes(employee.id)}
                            onCheckedChange={(checked) =>
                              handleToggleEmployee(employee.id, Boolean(checked))
                            }
                          />
                          <div className="space-y-1">
                            <div className="font-medium">{employee.fullName}</div>
                            <div className="text-sm text-muted-foreground">
                              {employee.employeeCode}
                              {employee.departmentName ? ` · ${employee.departmentName}` : ''}
                              {employee.designationName ? ` · ${employee.designationName}` : ''}
                            </div>
                          </div>
                        </label>
                      ))}
                    </div>
                    {form.formState.errors.employeeIds && (
                      <p className="text-sm text-destructive">
                        {form.formState.errors.employeeIds.message}
                      </p>
                    )}
                  </div>
                )}
              </div>
            </FormSection>
          </FormShell>
        </form>
      </Form>
    </div>
  );
}

function CycleDetailPage({ cycleId }: { cycleId: string }) {
  const navigate = useNavigate();
  const location = useLocation();
  const cycleQuery = usePerformanceCycle(cycleId);
  const [employeeSearch, setEmployeeSearch] = useState('');
  const [employeeStatus, setEmployeeStatus] = useState<AppraisalStatus | 'ALL'>('ALL');
  const employeesQuery = useCycleEmployees(cycleId, {
    search: employeeSearch || undefined,
    status: employeeStatus === 'ALL' ? undefined : employeeStatus,
  });
  const startCycleMutation = useStartCycle();
  const closeCycleMutation = useCloseCycle();

  if (cycleQuery.isError) {
    return <ErrorState error={cycleQuery.error} onRetry={() => void cycleQuery.refetch()} />;
  }

  if (!cycleQuery.data && cycleQuery.isLoading) {
    return <DataTable data={[]} columns={[]} getRowId={() => ''} isLoading />;
  }

  const cycle = cycleQuery.data;
  if (!cycle) {
    return (
      <EmptyState
        title="Cycle not found"
        subtitle="The selected appraisal cycle could not be loaded."
        action={
          <Button onClick={() => navigate('/admin/hris/performance/cycles')}>Back to Cycles</Button>
        }
      />
    );
  }

  const employeeColumns: Column<PerformanceEmployeeSummary>[] = [
    {
      key: 'employeeName',
      header: 'Employee',
      render: (row) => (
        <div>
          <div className="font-medium">{row.employeeName}</div>
          <div className="text-xs text-muted-foreground">
            {row.employeeCode}
            {row.department ? ` · ${row.department}` : ''}
            {row.designation ? ` · ${row.designation}` : ''}
          </div>
        </div>
      ),
    },
    { key: 'reviewerName', header: 'Reviewer' },
    {
      key: 'status',
      header: 'Status',
      render: (row) => <StatusPill type="application" status={row.status} />,
    },
    {
      key: 'goalCount',
      header: 'Goals',
      align: 'right',
      render: (row) => `${row.submittedGoals}/${row.goalCount}`,
      sortable: true,
      sortValue: (row) => row.goalCount,
    },
    {
      key: 'overallRating',
      header: 'Overall Rating',
      align: 'right',
      render: (row) => row.overallRating?.toFixed(2) ?? '—',
      sortable: true,
      sortValue: (row) => row.overallRating ?? 0,
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row) => (
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() =>
              navigate(
                `/admin/hris/performance/cycles/${cycleId}/goals?employeeId=${row.employeeId}`,
              )
            }
          >
            Goals
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() =>
              navigate(
                `/admin/hris/performance/self-appraisal/${cycleId}?employeeId=${row.employeeId}`,
              )
            }
          >
            Self Appraisal
          </Button>
          <Button
            size="sm"
            onClick={() =>
              navigate(`/admin/hris/performance/manager-review/${cycleId}/${row.employeeId}`)
            }
          >
            Review
          </Button>
        </div>
      ),
    },
  ];

  const detailTitle = location.pathname.includes('/reports')
    ? 'Cycle Reporting'
    : location.pathname.includes('/appraisals')
      ? 'Employee Appraisals'
      : 'Cycle Workbench';

  return (
    <div className="space-y-6">
      <PageHeader
        title={cycle.name}
        subtitle={`${detailTitle} · ${cycle.code}`}
        breadcrumbs={[
          { label: 'Performance Cycles', to: '/admin/hris/performance/cycles' },
          { label: cycle.name },
        ]}
        actions={
          <div className="flex gap-2">
            {cycle.status === 'DRAFT' && (
              <Button
                onClick={() => void startCycleMutation.mutateAsync(cycle.id)}
                disabled={startCycleMutation.isPending}
              >
                {startCycleMutation.isPending ? 'Starting…' : 'Start Cycle'}
              </Button>
            )}
            {cycle.status !== 'COMPLETED' && (
              <Button
                variant="outline"
                onClick={() => void closeCycleMutation.mutateAsync(cycle.id)}
                disabled={closeCycleMutation.isPending}
              >
                {closeCycleMutation.isPending ? 'Closing…' : 'Close Cycle'}
              </Button>
            )}
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Cycle Status"
          value={cycle.status}
          subtitle={`${cycle.cycleType} cycle`}
        />
        <MetricCard
          title="Eligible Employees"
          value={cycle.eligibleEmployees}
          subtitle="Employees included in the cycle"
        />
        <MetricCard
          title="Completed Appraisals"
          value={cycle.completedAppraisals}
          subtitle={`${cycle.pendingManagerReview} pending manager review`}
        />
        <MetricCard
          title="Pending Self Appraisals"
          value={cycle.pendingSelfAppraisal}
          subtitle={`${cycle.pendingManagerReview} calibration/review pending`}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Cycle Timeline</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div>
            <p className="text-sm text-muted-foreground">Cycle Window</p>
            <p className="mt-1 font-medium">
              <DateDisplay date={cycle.startDate} /> to <DateDisplay date={cycle.endDate} />
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Goal Setting Deadline</p>
            <p className="mt-1 font-medium">
              <DateDisplay date={cycle.goalSettingEnd ?? null} />
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Self Appraisal Deadline</p>
            <p className="mt-1 font-medium">
              <DateDisplay date={cycle.selfAppraisalEnd ?? null} />
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Manager Review Deadline</p>
            <p className="mt-1 font-medium">
              <DateDisplay date={cycle.managerReviewEnd ?? null} />
            </p>
          </div>
        </CardContent>
      </Card>

      <FilterBar
        search={employeeSearch}
        onSearchChange={setEmployeeSearch}
        searchPlaceholder="Search employees in this cycle"
        onClear={() => {
          setEmployeeSearch('');
          setEmployeeStatus('ALL');
        }}
      >
        <Select
          value={employeeStatus}
          onValueChange={(value) => setEmployeeStatus(value as AppraisalStatus | 'ALL')}
        >
          <SelectTrigger className="w-[220px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All statuses</SelectItem>
            <SelectItem value="GOAL_SETTING">Goal Setting</SelectItem>
            <SelectItem value="SELF_APPRAISAL">Self Appraisal</SelectItem>
            <SelectItem value="MANAGER_REVIEW">Manager Review</SelectItem>
            <SelectItem value="CALIBRATION">Calibration</SelectItem>
            <SelectItem value="COMPLETED">Completed</SelectItem>
          </SelectContent>
        </Select>
      </FilterBar>

      <DataTable
        data={employeesQuery.data ?? []}
        columns={employeeColumns}
        getRowId={(row) => row.appraisalId}
        isLoading={employeesQuery.isLoading}
        error={employeesQuery.error}
        onRetry={() => void employeesQuery.refetch()}
        emptyTitle="No employee packets"
        emptySubtitle="Employees will appear here once the cycle is created with active participants."
      />
    </div>
  );
}

function CycleListPage() {
  useRequiredActiveOrganizationId();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<AppraisalCycleStatus | 'ALL'>('ALL');

  const cyclesQuery = usePerformanceCycles({
    search: search || undefined,
    status: statusFilter === 'ALL' ? undefined : statusFilter,
    skip: 0,
    limit: 50,
  });

  if (cyclesQuery.isError) {
    return <ErrorState error={cyclesQuery.error} onRetry={() => void cyclesQuery.refetch()} />;
  }

  const summary = cyclesQuery.data?.summary;

  const columns: Column<AppraisalCycleListItem>[] = [
    {
      key: 'name',
      header: 'Cycle',
      render: (row) => (
        <div>
          <div className="font-medium">{row.name}</div>
          <div className="text-xs text-muted-foreground">
            {row.code}
            {row.financialYear ? ` · ${row.financialYear}` : ''}
          </div>
        </div>
      ),
    },
    {
      key: 'cycleType',
      header: 'Type',
      render: (row) => <StatusPill type="application" status={row.cycleType} />,
    },
    {
      key: 'startDate',
      header: 'Window',
      render: (row) => (
        <div className="text-sm">
          <DateDisplay date={row.startDate} /> to <DateDisplay date={row.endDate} />
        </div>
      ),
      sortable: true,
      sortValue: (row) => row.startDate,
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => <StatusPill type="application" status={row.status} />,
      sortable: true,
      sortValue: (row) => row.status,
    },
    {
      key: 'eligibleEmployees',
      header: 'Employees',
      align: 'right',
      render: (row) => row.eligibleEmployees,
      sortable: true,
      sortValue: (row) => row.eligibleEmployees,
    },
    {
      key: 'completedAppraisals',
      header: 'Completed',
      align: 'right',
      render: (row) => row.completedAppraisals,
      sortable: true,
      sortValue: (row) => row.completedAppraisals,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Performance Cycles"
        subtitle="Create appraisal cycles, start the workflow, and monitor goal, self-appraisal, and review progress."
        actions={
          <Button onClick={() => navigate('/admin/hris/performance/cycles/new')}>
            Create Cycle
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-5">
        <MetricCard
          title="Total Cycles"
          value={summary?.totalCycles ?? 0}
          subtitle="All appraisal cycles"
        />
        <MetricCard
          title="Active"
          value={summary?.active ?? 0}
          subtitle="Goal-setting, review, and calibration"
        />
        <MetricCard title="Completed" value={summary?.completed ?? 0} subtitle="Closed cycles" />
        <MetricCard title="Draft" value={summary?.draft ?? 0} subtitle="Awaiting HR start" />
        <MetricCard
          title="Employees Appraised"
          value={summary?.employeesAppraised ?? 0}
          subtitle="Completed employee appraisals"
        />
      </div>

      <FilterBar
        search={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search cycles by name or code"
        onClear={() => {
          setSearch('');
          setStatusFilter('ALL');
        }}
      >
        <Select
          value={statusFilter}
          onValueChange={(value) => setStatusFilter(value as AppraisalCycleStatus | 'ALL')}
        >
          <SelectTrigger className="w-[220px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All statuses</SelectItem>
            <SelectItem value="DRAFT">Draft</SelectItem>
            <SelectItem value="GOAL_SETTING">Goal Setting</SelectItem>
            <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
            <SelectItem value="REVIEW">Review</SelectItem>
            <SelectItem value="CALIBRATION">Calibration</SelectItem>
            <SelectItem value="COMPLETED">Completed</SelectItem>
          </SelectContent>
        </Select>
      </FilterBar>

      <DataTable
        data={cyclesQuery.data?.items ?? []}
        columns={columns}
        getRowId={(row) => row.id}
        isLoading={cyclesQuery.isLoading}
        error={cyclesQuery.error}
        onRetry={() => void cyclesQuery.refetch()}
        onRowClick={(row) => navigate(`/admin/hris/performance/cycles/${row.id}`)}
        emptyTitle="No appraisal cycles"
        emptySubtitle="Create the first cycle to begin goal-setting and appraisal operations."
      />
    </div>
  );
}

export default function AppraisalCycleList() {
  const location = useLocation();
  const { cycleId } = useParams();

  if (location.pathname.endsWith('/new')) {
    return <CycleCreateForm />;
  }

  if (cycleId) {
    return <CycleDetailPage cycleId={cycleId} />;
  }

  return <CycleListPage />;
}
