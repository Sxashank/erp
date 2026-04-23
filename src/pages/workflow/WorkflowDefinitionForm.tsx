import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm, useFieldArray } from 'react-hook-form';
import {
  ArrowLeft,
  ChevronDown,
  ChevronUp,
  GripVertical,
  Plus,
  Save,
  Settings,
  Trash2,
  Users,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/common/PageHeader';
import { Checkbox } from '@/components/ui/checkbox';
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
import { organizationsApi } from '@/services/api';
import type { Organization, PaginatedResponse } from '@/types';

import { logger } from '@/lib/logger';
interface WorkflowStep {
  id?: string;
  step_number: number;
  name: string;
  description?: string;
  step_type: 'APPROVAL' | 'REVIEW' | 'NOTIFICATION' | 'CONDITION' | 'PARALLEL';
  approval_type: 'ANY' | 'ALL' | 'SEQUENTIAL' | 'PERCENTAGE';
  approval_percentage?: number;
  timeout_hours?: number;
  auto_approve_on_timeout: boolean;
  escalation_enabled: boolean;
  escalation_hours?: number;
  approvers: WorkflowApprover[];
}

interface WorkflowApprover {
  id?: string;
  approver_type: 'USER' | 'ROLE' | 'DEPARTMENT_HEAD' | 'REPORTING_MANAGER' | 'DYNAMIC';
  user_id?: string;
  role_id?: string;
  can_delegate: boolean;
  can_reassign: boolean;
  is_mandatory: boolean;
}

interface WorkflowFormData {
  code: string;
  name: string;
  description: string;
  module: string;
  entity_type: string;
  is_active: boolean;
  auto_trigger: boolean;
  trigger_conditions?: string;
  steps: WorkflowStep[];
}

const MODULES = [
  { value: 'LENDING', label: 'Lending' },
  { value: 'FINANCE', label: 'Finance' },
  { value: 'HRIS', label: 'HRIS' },
  { value: 'PROCUREMENT', label: 'Procurement' },
  { value: 'AP_AR', label: 'AP/AR' },
  { value: 'FIXED_ASSETS', label: 'Fixed Assets' },
  { value: 'INVENTORY', label: 'Inventory' },
];

const ENTITY_TYPES: Record<string, { value: string; label: string }[]> = {
  LENDING: [
    { value: 'loan_application', label: 'Loan Application' },
    { value: 'disbursement', label: 'Disbursement' },
    { value: 'sanction', label: 'Sanction Letter' },
    { value: 'collateral', label: 'Collateral Release' },
  ],
  FINANCE: [
    { value: 'voucher', label: 'Journal Voucher' },
    { value: 'period_close', label: 'Period Close' },
  ],
  HRIS: [
    { value: 'leave_application', label: 'Leave Application' },
    { value: 'reimbursement', label: 'Reimbursement' },
    { value: 'attendance_regularization', label: 'Attendance Regularization' },
    { value: 'separation', label: 'Separation/Exit' },
  ],
  PROCUREMENT: [
    { value: 'purchase_requisition', label: 'Purchase Requisition' },
    { value: 'purchase_order', label: 'Purchase Order' },
    { value: 'rfq', label: 'RFQ' },
  ],
  AP_AR: [
    { value: 'purchase_bill', label: 'Purchase Bill' },
    { value: 'payment', label: 'Payment' },
  ],
  FIXED_ASSETS: [
    { value: 'asset_acquisition', label: 'Asset Acquisition' },
    { value: 'asset_disposal', label: 'Asset Disposal' },
    { value: 'asset_transfer', label: 'Asset Transfer' },
  ],
  INVENTORY: [
    { value: 'stock_adjustment', label: 'Stock Adjustment' },
    { value: 'stock_transfer', label: 'Stock Transfer' },
  ],
};

const STEP_TYPES = [
  { value: 'APPROVAL', label: 'Approval', description: 'Requires explicit approval action' },
  { value: 'REVIEW', label: 'Review', description: 'Review only, no approval needed' },
  { value: 'NOTIFICATION', label: 'Notification', description: 'Send notification and auto-proceed' },
  { value: 'CONDITION', label: 'Condition', description: 'Conditional branching based on rules' },
  { value: 'PARALLEL', label: 'Parallel', description: 'Multiple approvals in parallel' },
];

const APPROVAL_TYPES = [
  { value: 'ANY', label: 'Any One', description: 'Any one approver can approve' },
  { value: 'ALL', label: 'All', description: 'All approvers must approve' },
  { value: 'SEQUENTIAL', label: 'Sequential', description: 'Approvers in sequence' },
  { value: 'PERCENTAGE', label: 'Percentage', description: 'Percentage of approvers' },
];

const APPROVER_TYPES = [
  { value: 'USER', label: 'Specific User' },
  { value: 'ROLE', label: 'Role-based' },
  { value: 'DEPARTMENT_HEAD', label: 'Department Head' },
  { value: 'REPORTING_MANAGER', label: 'Reporting Manager' },
  { value: 'DYNAMIC', label: 'Dynamic (Rule-based)' },
];

export function WorkflowDefinitionForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [expandedSteps, setExpandedSteps] = useState<number[]>([0]);

  const {
    register,
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<WorkflowFormData>({
    defaultValues: {
      code: '',
      name: '',
      description: '',
      module: '',
      entity_type: '',
      is_active: true,
      auto_trigger: true,
      steps: [
        {
          step_number: 1,
          name: 'Step 1',
          step_type: 'APPROVAL',
          approval_type: 'ANY',
          auto_approve_on_timeout: false,
          escalation_enabled: false,
          approvers: [],
        },
      ],
    },
  });

  const { fields: steps, append: addStep, remove: removeStep, move: moveStep } = useFieldArray({
    control,
    name: 'steps',
  });

  const selectedModule = watch('module');

  useEffect(() => {
    fetchOrganizations();
    if (isEdit) {
      fetchWorkflow();
    }
  }, [id]);

  const fetchOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      const data: PaginatedResponse<Organization> = response.data;
      setOrganizations(data.items);
      if (data.items.length > 0) {
        setSelectedOrgId(data.items[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
    }
  };

  const fetchWorkflow = async () => {
    try {
      setLoading(true);
      // Mock fetch - replace with actual API call
      // const response = await workflowApi.get(id);
      // Reset form with fetched data
    } catch (error) {
      console.error('Failed to fetch workflow:', error);
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data: WorkflowFormData) => {
    try {
      setSaving(true);
      // API call to save workflow
      logger.debug('Saving workflow:', data);
      // await workflowApi.create(data) or workflowApi.update(id, data)
      navigate('/admin/workflow/definitions');
    } catch (error) {
      console.error('Failed to save workflow:', error);
    } finally {
      setSaving(false);
    }
  };

  const toggleStepExpanded = (index: number) => {
    setExpandedSteps((prev) =>
      prev.includes(index) ? prev.filter((i) => i !== index) : [...prev, index]
    );
  };

  const handleAddStep = () => {
    addStep({
      step_number: steps.length + 1,
      name: `Step ${steps.length + 1}`,
      step_type: 'APPROVAL',
      approval_type: 'ANY',
      auto_approve_on_timeout: false,
      escalation_enabled: false,
      approvers: [],
    });
    setExpandedSteps((prev) => [...prev, steps.length]);
  };

  const handleMoveStep = (index: number, direction: 'up' | 'down') => {
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    if (newIndex >= 0 && newIndex < steps.length) {
      moveStep(index, newIndex);
      // Update step numbers
      steps.forEach((_, i) => {
        setValue(`steps.${i}.step_number`, i + 1);
      });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-slate-500">Loading workflow...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEdit ? 'Edit Workflow' : 'Create Workflow'}
        subtitle={
          isEdit ? 'Modify workflow configuration' : 'Define a new approval workflow'
        }
        breadcrumbs={[
          { label: 'Workflow Definitions', to: '/admin/workflow/definitions' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-6">
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
                      {...register('code', { required: 'Code is required' })}
                    />
                    {errors.code && (
                      <p className="text-sm text-red-500">{errors.code.message}</p>
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
                      <p className="text-sm text-red-500">{errors.name.message}</p>
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
                    <Label htmlFor="module">Module *</Label>
                    <Select
                      value={watch('module')}
                      onValueChange={(value) => {
                        setValue('module', value);
                        setValue('entity_type', '');
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select module" />
                      </SelectTrigger>
                      <SelectContent>
                        {MODULES.map((module) => (
                          <SelectItem key={module.value} value={module.value}>
                            {module.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="entity_type">Entity Type *</Label>
                    <Select
                      value={watch('entity_type')}
                      onValueChange={(value) => setValue('entity_type', value)}
                      disabled={!selectedModule}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select entity type" />
                      </SelectTrigger>
                      <SelectContent>
                        {selectedModule &&
                          ENTITY_TYPES[selectedModule]?.map((entity) => (
                            <SelectItem key={entity.value} value={entity.value}>
                              {entity.label}
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <Separator />

                <div className="flex flex-wrap gap-6">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="is_active"
                      checked={watch('is_active')}
                      onCheckedChange={(checked) => setValue('is_active', checked)}
                    />
                    <Label htmlFor="is_active">Active</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="auto_trigger"
                      checked={watch('auto_trigger')}
                      onCheckedChange={(checked) => setValue('auto_trigger', checked)}
                    />
                    <Label htmlFor="auto_trigger">Auto-trigger on creation</Label>
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
                    <CardDescription>Configure approval steps and assignees</CardDescription>
                  </div>
                  <Button type="button" variant="outline" onClick={handleAddStep}>
                    <Plus className="mr-2 h-4 w-4" />
                    Add Step
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {steps.length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <p>No steps defined. Click &quot;Add Step&quot; to begin.</p>
                  </div>
                ) : (
                  steps.map((step, index) => (
                    <div
                      key={step.id}
                      className="border rounded-lg bg-slate-50"
                    >
                      <div
                        className="flex items-center gap-2 p-4 cursor-pointer"
                        onClick={() => toggleStepExpanded(index)}
                      >
                        <GripVertical className="h-4 w-4 text-slate-400" />
                        <Badge variant="outline" className="mr-2">
                          Step {index + 1}
                        </Badge>
                        <span className="font-medium flex-1">
                          {watch(`steps.${index}.name`) || `Step ${index + 1}`}
                        </span>
                        <Badge className="bg-blue-50 text-blue-700">
                          {watch(`steps.${index}.step_type`) || 'APPROVAL'}
                        </Badge>
                        <div className="flex items-center gap-1">
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            disabled={index === 0}
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
                            disabled={index === steps.length - 1}
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
                            className="h-8 w-8 text-red-500 hover:text-red-600"
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
                        <div className="px-4 pb-4 space-y-4 border-t bg-white">
                          <div className="grid gap-4 sm:grid-cols-2 pt-4">
                            <div className="space-y-2">
                              <Label>Step Name *</Label>
                              <Input
                                placeholder="e.g., Manager Approval"
                                {...register(`steps.${index}.name`, { required: true })}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label>Step Type *</Label>
                              <Select
                                value={watch(`steps.${index}.step_type`)}
                                onValueChange={(value) =>
                                  setValue(`steps.${index}.step_type`, value as WorkflowStep['step_type'])
                                }
                              >
                                <SelectTrigger>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {STEP_TYPES.map((type) => (
                                    <SelectItem key={type.value} value={type.value}>
                                      <div>
                                        <p>{type.label}</p>
                                        <p className="text-xs text-slate-500">{type.description}</p>
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
                              {...register(`steps.${index}.description`)}
                            />
                          </div>

                          <div className="grid gap-4 sm:grid-cols-3">
                            <div className="space-y-2">
                              <Label>Approval Type</Label>
                              <Select
                                value={watch(`steps.${index}.approval_type`)}
                                onValueChange={(value) =>
                                  setValue(`steps.${index}.approval_type`, value as WorkflowStep['approval_type'])
                                }
                              >
                                <SelectTrigger>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {APPROVAL_TYPES.map((type) => (
                                    <SelectItem key={type.value} value={type.value}>
                                      {type.label}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </div>
                            <div className="space-y-2">
                              <Label>Timeout (hours)</Label>
                              <Input
                                type="number"
                                placeholder="24"
                                {...register(`steps.${index}.timeout_hours`, { valueAsNumber: true })}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label>Escalation (hours)</Label>
                              <Input
                                type="number"
                                placeholder="48"
                                {...register(`steps.${index}.escalation_hours`, { valueAsNumber: true })}
                              />
                            </div>
                          </div>

                          <div className="flex flex-wrap gap-6">
                            <div className="flex items-center space-x-2">
                              <Checkbox
                                id={`auto_approve_${index}`}
                                checked={watch(`steps.${index}.auto_approve_on_timeout`)}
                                onCheckedChange={(checked) =>
                                  setValue(`steps.${index}.auto_approve_on_timeout`, checked as boolean)
                                }
                              />
                              <Label htmlFor={`auto_approve_${index}`}>Auto-approve on timeout</Label>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Checkbox
                                id={`escalation_${index}`}
                                checked={watch(`steps.${index}.escalation_enabled`)}
                                onCheckedChange={(checked) =>
                                  setValue(`steps.${index}.escalation_enabled`, checked as boolean)
                                }
                              />
                              <Label htmlFor={`escalation_${index}`}>Enable escalation</Label>
                            </div>
                          </div>

                          <Separator />

                          <div className="space-y-2">
                            <Label>Approvers</Label>
                            <div className="text-sm text-slate-500">
                              Configure approvers for this step. You can add specific users, roles, or dynamic assignees.
                            </div>
                            <Button type="button" variant="outline" size="sm">
                              <Plus className="mr-2 h-3 w-3" />
                              Add Approver
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Organization</CardTitle>
              </CardHeader>
              <CardContent>
                <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select organization" />
                  </SelectTrigger>
                  <SelectContent>
                    {organizations.map((org) => (
                      <SelectItem key={org.id} value={org.id}>
                        {org.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button type="submit" className="w-full" disabled={saving}>
                  <Save className="mr-2 h-4 w-4" />
                  {saving ? 'Saving...' : isEdit ? 'Update Workflow' : 'Create Workflow'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="w-full"
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
              <CardContent className="text-sm text-slate-500 space-y-2">
                <p>
                  <strong>Step Types:</strong>
                </p>
                <ul className="list-disc list-inside space-y-1">
                  <li><strong>Approval:</strong> Requires action</li>
                  <li><strong>Review:</strong> FYI, no action needed</li>
                  <li><strong>Notification:</strong> Auto-proceeds</li>
                  <li><strong>Condition:</strong> Branching logic</li>
                  <li><strong>Parallel:</strong> Multiple parallel approvals</li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </form>
    </div>
  );
}
