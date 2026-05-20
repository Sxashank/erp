import {
  ChevronDown,
  ChevronUp,
  GripVertical,
  Loader2,
  Plus,
  Save,
  Settings,
  Trash2,
  Users,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { useFieldArray, useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';

import { EmptyState, ErrorState, PageHeader, SkeletonTable } from '@/components/common';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { useOrganization } from '@/hooks/useOrganization';
import {
  useCreateWorkflowDefinition,
  useUpdateWorkflowDefinition,
  useWorkflowDefinition,
} from '@/hooks/workflow/useWorkflowDefinitions';
import { showErrorToast } from '@/lib/errorToast';
import type {
  ApprovalMode,
  ApproverType,
  WorkflowDefinitionCreate,
  WorkflowEntityType,
  WorkflowStepCreate,
  WorkflowStepType,
} from '@/services/workflow/workflowApi';

interface ApproverFormValue {
  approverType: ApproverType;
  userId?: string;
  roleId?: string;
  designation?: string;
  isMandatory: boolean;
  canSelfApprove: boolean;
}

interface StepFormValue {
  stepNumber: number;
  name: string;
  description?: string;
  stepType: WorkflowStepType;
  approvalMode: ApprovalMode;
  slaHours?: number | null;
  reminderHours?: number | null;
  allowDelegation: boolean;
  approvers: ApproverFormValue[];
}

interface WorkflowFormData {
  code: string;
  name: string;
  description: string;
  entityType: WorkflowEntityType | '';
  isDefault: boolean;
  priority: number;
  allowParallelBranches: boolean;
  requireCommentsOnReject: boolean;
  notifyInitiatorOnComplete: boolean;
  allowWithdrawal: boolean;
  steps: StepFormValue[];
}

const ENTITY_TYPES: { value: WorkflowEntityType; label: string }[] = [
  { value: 'VOUCHER', label: 'Voucher' },
  { value: 'PURCHASE_BILL', label: 'Purchase Bill' },
  { value: 'SALES_INVOICE', label: 'Sales Invoice' },
  { value: 'PAYMENT', label: 'Payment' },
  { value: 'JOURNAL_ENTRY', label: 'Journal Entry' },
  { value: 'LOAN_APPLICATION', label: 'Loan Application' },
  { value: 'LOAN_SANCTION', label: 'Loan Sanction' },
  { value: 'LOAN_RATING', label: 'Loan Rating' },
];

const STEP_TYPES: {
  value: WorkflowStepType;
  label: string;
  description: string;
}[] = [
  { value: 'APPROVAL', label: 'Approval', description: 'Requires explicit approval action' },
  {
    value: 'NOTIFICATION',
    label: 'Notification',
    description: 'Send notification and auto-proceed',
  },
  {
    value: 'CONDITIONAL',
    label: 'Conditional',
    description: 'Conditional branching based on rules',
  },
  { value: 'PARALLEL_GATE', label: 'Parallel Gate', description: 'Multiple parallel branches' },
];

const APPROVAL_MODES: { value: ApprovalMode; label: string; description: string }[] = [
  { value: 'SEQUENTIAL', label: 'Sequential', description: 'One approver at a time' },
  { value: 'PARALLEL_ANY', label: 'Parallel — Any', description: 'Any one approver can approve' },
  { value: 'PARALLEL_ALL', label: 'Parallel — All', description: 'All approvers must approve' },
];

const APPROVER_TYPES: { value: ApproverType; label: string }[] = [
  { value: 'USER', label: 'Specific User' },
  { value: 'ROLE', label: 'Role-based' },
  { value: 'DESIGNATION', label: 'Designation' },
  { value: 'DEPARTMENT_HEAD', label: 'Department Head' },
  { value: 'REPORTING_MANAGER', label: 'Reporting Manager' },
  { value: 'DYNAMIC', label: 'Dynamic (Rule-based)' },
];

const DEFAULT_STEP: StepFormValue = {
  stepNumber: 1,
  name: 'Step 1',
  stepType: 'APPROVAL',
  approvalMode: 'SEQUENTIAL',
  allowDelegation: false,
  approvers: [],
};

export function WorkflowDefinitionForm(): JSX.Element {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { activeOrganizationId } = useOrganization();
  const isEdit = Boolean(id);

  const [expandedSteps, setExpandedSteps] = useState<number[]>([0]);

  const definitionQuery = useWorkflowDefinition(isEdit ? id : undefined);
  const createMutation = useCreateWorkflowDefinition();
  const updateMutation = useUpdateWorkflowDefinition();

  const {
    register,
    control,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<WorkflowFormData>({
    defaultValues: {
      code: '',
      name: '',
      description: '',
      entityType: '',
      isDefault: false,
      priority: 0,
      allowParallelBranches: false,
      requireCommentsOnReject: true,
      notifyInitiatorOnComplete: true,
      allowWithdrawal: true,
      steps: [DEFAULT_STEP],
    },
  });

  const {
    fields: steps,
    append: addStep,
    remove: removeStep,
    move: moveStep,
  } = useFieldArray({ control, name: 'steps' });

  // Hydrate the form when editing an existing definition.
  useEffect(() => {
    if (!isEdit || !definitionQuery.data) return;
    const d = definitionQuery.data;
    reset({
      code: d.code,
      name: d.name,
      description: d.description ?? '',
      entityType: d.entityType,
      isDefault: d.isDefault,
      priority: d.priority,
      allowParallelBranches: d.allowParallelBranches,
      requireCommentsOnReject: d.requireCommentsOnReject,
      notifyInitiatorOnComplete: d.notifyInitiatorOnComplete,
      allowWithdrawal: d.allowWithdrawal,
      steps: d.steps.map((s) => ({
        stepNumber: s.stepNumber,
        name: s.name,
        description: s.description ?? '',
        stepType: s.stepType,
        approvalMode: s.approvalMode,
        slaHours: s.slaHours,
        reminderHours: s.reminderHours,
        allowDelegation: s.allowDelegation,
        approvers: s.approvalRules.map((r) => ({
          approverType: r.approverType,
          userId: r.userId ?? undefined,
          roleId: r.roleId ?? undefined,
          designation: r.designation ?? undefined,
          isMandatory: r.isMandatory,
          canSelfApprove: r.canSelfApprove,
        })),
      })),
    });
  }, [isEdit, definitionQuery.data, reset]);

  const toggleStepExpanded = (index: number) => {
    setExpandedSteps((prev) =>
      prev.includes(index) ? prev.filter((i) => i !== index) : [...prev, index],
    );
  };

  const handleAddStep = () => {
    const next = steps.length + 1;
    addStep({
      ...DEFAULT_STEP,
      stepNumber: next,
      name: `Step ${next}`,
    });
    setExpandedSteps((prev) => [...prev, steps.length]);
  };

  const handleMoveStep = (index: number, direction: 'up' | 'down') => {
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    if (newIndex < 0 || newIndex >= steps.length) return;
    moveStep(index, newIndex);
    steps.forEach((_, i) => {
      setValue(`steps.${i}.stepNumber`, i + 1);
    });
  };

  const handleAddApprover = (stepIndex: number) => {
    const path = `steps.${stepIndex}.approvers` as const;
    const current = watch(path) ?? [];
    setValue(path, [
      ...current,
      {
        approverType: 'ROLE',
        isMandatory: true,
        canSelfApprove: false,
      },
    ]);
  };

  const handleRemoveApprover = (stepIndex: number, approverIndex: number) => {
    const path = `steps.${stepIndex}.approvers` as const;
    const current = watch(path) ?? [];
    setValue(
      path,
      current.filter((_, i) => i !== approverIndex),
    );
  };

  const onSubmit = (data: WorkflowFormData) => {
    if (!activeOrganizationId) {
      toast({
        title: 'No organization selected',
        description: 'Switch to an organization before saving a workflow.',
        variant: 'destructive',
      });
      return;
    }
    if (!data.entityType) {
      toast({
        title: 'Entity type required',
        description: 'Pick the entity type this workflow applies to.',
        variant: 'destructive',
      });
      return;
    }

    if (isEdit && id) {
      updateMutation.mutate(
        {
          id,
          body: {
            name: data.name,
            description: data.description || null,
            isDefault: data.isDefault,
            priority: data.priority,
            allowParallelBranches: data.allowParallelBranches,
            requireCommentsOnReject: data.requireCommentsOnReject,
            notifyInitiatorOnComplete: data.notifyInitiatorOnComplete,
            allowWithdrawal: data.allowWithdrawal,
          },
        },
        {
          onSuccess: () => {
            toast({
              title: 'Workflow updated',
              description: `${data.code} has been saved.`,
            });
            navigate('/admin/workflow/definitions');
          },
          onError: (err) => showErrorToast(err, toast),
        },
      );
      return;
    }

    const payload: WorkflowDefinitionCreate = {
      name: data.name,
      code: data.code,
      description: data.description || null,
      entityType: data.entityType,
      isDefault: data.isDefault,
      priority: data.priority,
      allowParallelBranches: data.allowParallelBranches,
      requireCommentsOnReject: data.requireCommentsOnReject,
      notifyInitiatorOnComplete: data.notifyInitiatorOnComplete,
      allowWithdrawal: data.allowWithdrawal,
      steps: data.steps.map<WorkflowStepCreate>((s, idx) => ({
        stepNumber: idx + 1,
        name: s.name,
        description: s.description || null,
        stepType: s.stepType,
        approvalMode: s.approvalMode,
        slaHours: s.slaHours ?? null,
        reminderHours: s.reminderHours ?? null,
        allowDelegation: s.allowDelegation,
        approvalRules: s.approvers.map((a, ai) => ({
          sequence: ai + 1,
          approverType: a.approverType,
          userId: a.userId || null,
          roleId: a.roleId || null,
          designation: a.designation || null,
          isMandatory: a.isMandatory,
          canSelfApprove: a.canSelfApprove,
        })),
      })),
    };

    createMutation.mutate(payload, {
      onSuccess: () => {
        toast({
          title: 'Workflow created',
          description: `${data.code} is now available.`,
        });
        navigate('/admin/workflow/definitions');
      },
      onError: (err) => showErrorToast(err, toast),
    });
  };

  // Loading state for edit hydration.
  if (isEdit && definitionQuery.isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Edit Workflow"
          subtitle="Loading workflow configuration"
          breadcrumbs={[
            { label: 'Workflow Definitions', to: '/admin/workflow/definitions' },
            { label: 'Edit' },
          ]}
        />
        <SkeletonTable rows={6} columns={3} />
      </div>
    );
  }

  if (isEdit && definitionQuery.isError) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Edit Workflow"
          subtitle="Unable to load this workflow"
          breadcrumbs={[
            { label: 'Workflow Definitions', to: '/admin/workflow/definitions' },
            { label: 'Edit' },
          ]}
        />
        <ErrorState error={definitionQuery.error} onRetry={() => definitionQuery.refetch()} />
      </div>
    );
  }

  if (!activeOrganizationId) {
    return (
      <div className="space-y-6">
        <PageHeader
          title={isEdit ? 'Edit Workflow' : 'Create Workflow'}
          subtitle="Select an organization to continue"
          breadcrumbs={[
            { label: 'Workflow Definitions', to: '/admin/workflow/definitions' },
            { label: isEdit ? 'Edit' : 'New' },
          ]}
        />
        <EmptyState
          title="No active organization"
          subtitle="Switch to an organization to create or edit workflow definitions."
        />
      </div>
    );
  }

  const saving = isSubmitting || createMutation.isPending || updateMutation.isPending;

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEdit ? 'Edit Workflow' : 'Create Workflow'}
        subtitle={isEdit ? 'Modify workflow configuration' : 'Define a new approval workflow'}
        breadcrumbs={[
          { label: 'Workflow Definitions', to: '/admin/workflow/definitions' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Main Form */}
          <div className="space-y-6 lg:col-span-2">
            {/* Basic Information */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  Basic Information
                </CardTitle>
                <CardDescription>Define the workflow identification and scope</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="code">Workflow Code *</Label>
                    <Input
                      id="code"
                      placeholder="e.g., WF-LOAN-APP"
                      disabled={isEdit}
                      {...register('code', { required: 'Code is required' })}
                    />
                    {errors.code && (
                      <p className="text-sm text-destructive">{errors.code.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="name">Workflow Name *</Label>
                    <Input
                      id="name"
                      placeholder="e.g., Loan Application Approval"
                      {...register('name', { required: 'Name is required' })}
                    />
                    {errors.name && (
                      <p className="text-sm text-destructive">{errors.name.message}</p>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    placeholder="Describe the purpose of this workflow..."
                    {...register('description')}
                  />
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="entityType">Entity Type *</Label>
                    <Select
                      value={watch('entityType')}
                      onValueChange={(v) => setValue('entityType', v as WorkflowEntityType)}
                      disabled={isEdit}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select entity type" />
                      </SelectTrigger>
                      <SelectContent>
                        {ENTITY_TYPES.map((t) => (
                          <SelectItem key={t.value} value={t.value}>
                            {t.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="priority">Priority</Label>
                    <Input
                      id="priority"
                      type="number"
                      min={0}
                      {...register('priority', { valueAsNumber: true, min: 0 })}
                    />
                  </div>
                </div>

                <Separator />

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="isDefault"
                      checked={watch('isDefault')}
                      onCheckedChange={(checked) => setValue('isDefault', checked)}
                    />
                    <Label htmlFor="isDefault">Default workflow for this entity type</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="allowParallelBranches"
                      checked={watch('allowParallelBranches')}
                      onCheckedChange={(checked) => setValue('allowParallelBranches', checked)}
                    />
                    <Label htmlFor="allowParallelBranches">Allow parallel branches</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="requireCommentsOnReject"
                      checked={watch('requireCommentsOnReject')}
                      onCheckedChange={(checked) => setValue('requireCommentsOnReject', checked)}
                    />
                    <Label htmlFor="requireCommentsOnReject">Require comments on reject</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="notifyInitiatorOnComplete"
                      checked={watch('notifyInitiatorOnComplete')}
                      onCheckedChange={(checked) =>
                        setValue('notifyInitiatorOnComplete', checked)
                      }
                    />
                    <Label htmlFor="notifyInitiatorOnComplete">
                      Notify initiator on completion
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="allowWithdrawal"
                      checked={watch('allowWithdrawal')}
                      onCheckedChange={(checked) => setValue('allowWithdrawal', checked)}
                    />
                    <Label htmlFor="allowWithdrawal">Allow initiator withdrawal</Label>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Workflow Steps */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Users className="h-5 w-5" />
                      Workflow Steps
                    </CardTitle>
                    <CardDescription>
                      Configure approval steps and assignees. Step edits only apply on create — to
                      change steps on an existing workflow, create a new version.
                    </CardDescription>
                  </div>
                  <Button type="button" variant="outline" onClick={handleAddStep} disabled={isEdit}>
                    <Plus className="mr-2 h-4 w-4" />
                    Add Step
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {steps.length === 0 ? (
                  <EmptyState
                    title="No steps defined"
                    subtitle="Add at least one step to define the approval path."
                    icon={Users}
                    action={
                      <Button type="button" onClick={handleAddStep} disabled={isEdit}>
                        <Plus className="mr-2 h-4 w-4" />
                        Add Step
                      </Button>
                    }
                  />
                ) : (
                  steps.map((step, index) => {
                    const approvers = watch(`steps.${index}.approvers`) ?? [];
                    return (
                      <div key={step.id} className="rounded-lg border bg-muted/30">
                        <div
                          role="button"
                          tabIndex={0}
                          className="flex cursor-pointer items-center gap-2 p-4"
                          onClick={() => toggleStepExpanded(index)}
                          onKeyDown={(event) => {
                            if (event.key === 'Enter' || event.key === ' ') {
                              event.preventDefault();
                              toggleStepExpanded(index);
                            }
                          }}
                        >
                          <GripVertical className="h-4 w-4 text-muted-foreground" />
                          <Badge variant="outline" className="mr-2">
                            Step {index + 1}
                          </Badge>
                          <span className="flex-1 font-medium">
                            {watch(`steps.${index}.name`) || `Step ${index + 1}`}
                          </span>
                          <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-50">
                            {watch(`steps.${index}.stepType`) || 'APPROVAL'}
                          </Badge>
                          <div className="flex items-center gap-1">
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              disabled={index === 0 || isEdit}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleMoveStep(index, 'up');
                              }}
                            >
                              <ChevronUp className="h-4 w-4" />
                            </Button>
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              disabled={index === steps.length - 1 || isEdit}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleMoveStep(index, 'down');
                              }}
                            >
                              <ChevronDown className="h-4 w-4" />
                            </Button>
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-destructive hover:text-destructive"
                              disabled={isEdit}
                              onClick={(e) => {
                                e.stopPropagation();
                                removeStep(index);
                              }}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                            {expandedSteps.includes(index) ? (
                              <ChevronUp className="h-4 w-4" />
                            ) : (
                              <ChevronDown className="h-4 w-4" />
                            )}
                          </div>
                        </div>

                        {expandedSteps.includes(index) && (
                          <div className="space-y-4 border-t bg-background px-4 pb-4">
                            <div className="grid gap-4 pt-4 sm:grid-cols-2">
                              <div className="space-y-2">
                                <Label>Step Name *</Label>
                                <Input
                                  placeholder="e.g., Manager Approval"
                                  disabled={isEdit}
                                  {...register(`steps.${index}.name`, { required: true })}
                                />
                              </div>
                              <div className="space-y-2">
                                <Label>Step Type *</Label>
                                <Select
                                  value={watch(`steps.${index}.stepType`)}
                                  onValueChange={(v) =>
                                    setValue(`steps.${index}.stepType`, v as WorkflowStepType)
                                  }
                                  disabled={isEdit}
                                >
                                  <SelectTrigger>
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    {STEP_TYPES.map((type) => (
                                      <SelectItem key={type.value} value={type.value}>
                                        <div>
                                          <p>{type.label}</p>
                                          <p className="text-xs text-muted-foreground">
                                            {type.description}
                                          </p>
                                        </div>
                                      </SelectItem>
                                    ))}
                                  </SelectContent>
                                </Select>
                              </div>
                            </div>

                            <div className="space-y-2">
                              <Label>Description</Label>
                              <Input
                                placeholder="Step description..."
                                disabled={isEdit}
                                {...register(`steps.${index}.description`)}
                              />
                            </div>

                            <div className="grid gap-4 sm:grid-cols-3">
                              <div className="space-y-2">
                                <Label>Approval Mode</Label>
                                <Select
                                  value={watch(`steps.${index}.approvalMode`)}
                                  onValueChange={(v) =>
                                    setValue(`steps.${index}.approvalMode`, v as ApprovalMode)
                                  }
                                  disabled={isEdit}
                                >
                                  <SelectTrigger>
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    {APPROVAL_MODES.map((m) => (
                                      <SelectItem key={m.value} value={m.value}>
                                        {m.label}
                                      </SelectItem>
                                    ))}
                                  </SelectContent>
                                </Select>
                              </div>
                              <div className="space-y-2">
                                <Label>SLA (hours)</Label>
                                <Input
                                  type="number"
                                  min={1}
                                  placeholder="24"
                                  disabled={isEdit}
                                  {...register(`steps.${index}.slaHours`, {
                                    valueAsNumber: true,
                                  })}
                                />
                              </div>
                              <div className="space-y-2">
                                <Label>Reminder (hours)</Label>
                                <Input
                                  type="number"
                                  min={1}
                                  placeholder="12"
                                  disabled={isEdit}
                                  {...register(`steps.${index}.reminderHours`, {
                                    valueAsNumber: true,
                                  })}
                                />
                              </div>
                            </div>

                            <div className="flex items-center space-x-2">
                              <Switch
                                id={`allowDelegation_${index}`}
                                checked={watch(`steps.${index}.allowDelegation`)}
                                onCheckedChange={(checked) =>
                                  setValue(`steps.${index}.allowDelegation`, checked)
                                }
                                disabled={isEdit}
                              />
                              <Label htmlFor={`allowDelegation_${index}`}>Allow delegation</Label>
                            </div>

                            <Separator />

                            <div className="space-y-3">
                              <div className="flex items-center justify-between">
                                <Label>Approvers ({approvers.length})</Label>
                                <Button
                                  type="button"
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleAddApprover(index)}
                                  disabled={isEdit}
                                >
                                  <Plus className="mr-2 h-3 w-3" />
                                  Add Approver
                                </Button>
                              </div>
                              {approvers.length === 0 ? (
                                <p className="text-sm text-muted-foreground">
                                  No approvers configured. Add at least one to route this step.
                                </p>
                              ) : (
                                <div className="space-y-2">
                                  {approvers.map((_, approverIndex) => (
                                    <div
                                      key={approverIndex}
                                      className="grid items-end gap-2 rounded-md border bg-muted/20 p-3 sm:grid-cols-[1fr_1fr_auto]"
                                    >
                                      <div className="space-y-1">
                                        <Label className="text-xs">Approver Type</Label>
                                        <Select
                                          value={watch(
                                            `steps.${index}.approvers.${approverIndex}.approverType`,
                                          )}
                                          onValueChange={(v) =>
                                            setValue(
                                              `steps.${index}.approvers.${approverIndex}.approverType`,
                                              v as ApproverType,
                                            )
                                          }
                                          disabled={isEdit}
                                        >
                                          <SelectTrigger>
                                            <SelectValue />
                                          </SelectTrigger>
                                          <SelectContent>
                                            {APPROVER_TYPES.map((t) => (
                                              <SelectItem key={t.value} value={t.value}>
                                                {t.label}
                                              </SelectItem>
                                            ))}
                                          </SelectContent>
                                        </Select>
                                      </div>
                                      <div className="space-y-1">
                                        <Label className="text-xs">
                                          User / Role / Designation ID
                                        </Label>
                                        <Input
                                          placeholder="UUID or designation key"
                                          disabled={isEdit}
                                          {...register(
                                            `steps.${index}.approvers.${approverIndex}.roleId`,
                                          )}
                                        />
                                      </div>
                                      <Button
                                        type="button"
                                        variant="ghost"
                                        size="icon"
                                        className="text-destructive"
                                        onClick={() => handleRemoveApprover(index, approverIndex)}
                                        disabled={isEdit}
                                      >
                                        <Trash2 className="h-4 w-4" />
                                      </Button>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button type="submit" className="w-full" disabled={saving}>
                  {saving ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="mr-2 h-4 w-4" />
                  )}
                  {isEdit ? 'Update Workflow' : 'Create Workflow'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="w-full"
                  disabled={saving}
                  onClick={() => navigate('/admin/workflow/definitions')}
                >
                  Cancel
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Help</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-muted-foreground">
                <p>
                  <strong>Step Types:</strong>
                </p>
                <ul className="list-inside list-disc space-y-1">
                  <li>
                    <strong>Approval:</strong> Requires explicit action
                  </li>
                  <li>
                    <strong>Notification:</strong> Sends notice and auto-proceeds
                  </li>
                  <li>
                    <strong>Conditional:</strong> Branching logic
                  </li>
                  <li>
                    <strong>Parallel Gate:</strong> Multiple parallel branches
                  </li>
                </ul>
                <p className="pt-2">
                  Steps are immutable after the workflow is saved. Create a new version to change
                  the routing path.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </form>
    </div>
  );
}
