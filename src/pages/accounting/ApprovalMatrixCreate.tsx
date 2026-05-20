import { zodResolver } from '@hookform/resolvers/zod';
import {
  Plus,
  Trash2,
  Save,
  ArrowUp,
  ArrowDown,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';
import { z } from 'zod';

import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  approvalsApi,
  rolesApi,
  type ApprovalWorkflowPayload,
  type ApprovalWorkflowType,
} from '@/services/api';
import { useActiveOrganizationId } from '@/stores/organizationStore';


import { logger } from "@/lib/logger";
const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

const levelSchema = z.object({
  level: z.number(),
  roleId: z.string().min(1, 'Role is required'),
  minAmount: z.number().min(0, 'Min amount must be >= 0'),
  maxAmount: z.number().min(0, 'Max amount must be >= 0'),
  isOptional: z.boolean(),
});

const matrixSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional(),
  transactionType: z.string().min(1, 'Transaction type is required'),
  isActive: z.boolean(),
  levels: z.array(levelSchema).min(1, 'At least one level is required').max(3, 'Maximum three levels are supported'),
});

type MatrixFormData = z.infer<typeof matrixSchema>;

interface ApprovalRole {
  id: string;
  name: string;
}

interface RoleApiResponse {
  id: string;
  name?: string;
  code?: string;
}

const transactionTypes: { id: ApprovalWorkflowType; name: string }[] = [
  { id: 'FIN_VOUCHER', name: 'Finance Voucher' },
  { id: 'FIN_JOURNAL', name: 'Journal Voucher' },
  { id: 'PAYMENT_RELEASE', name: 'Payment Release' },
  { id: 'PAYROLL_POSTING', name: 'Payroll Posting' },
  { id: 'LOAN_DISBURSEMENT', name: 'Loan Disbursement' },
  { id: 'LOAN_SANCTION', name: 'Loan Sanction' },
];

export default function ApprovalMatrixCreate() {
  const { id } = useParams();
  const navigate = useNavigate();
  const organizationId = useActiveOrganizationId();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [roles, setRoles] = useState<ApprovalRole[]>([]);
  const [rolesError, setRolesError] = useState<string | null>(null);
  const isEditMode = !!id;

  const form = useForm<MatrixFormData>({
    resolver: zodResolver(matrixSchema),
    defaultValues: {
      name: '',
      description: '',
      transactionType: '',
      isActive: true,
      levels: [
        { level: 1, roleId: '', minAmount: 0, maxAmount: 100000, isOptional: false },
      ],
    },
  });

  const { fields, append, remove, move } = useFieldArray({
    control: form.control,
    name: 'levels',
  });

  useEffect(() => {
    let isMounted = true;
    rolesApi
      .list()
      .then((response) => {
        if (!isMounted) return;
        const data: RoleApiResponse[] = Array.isArray(response.data)
          ? response.data
          : response.data?.items || [];
        setRoles(
          data.map((role) => ({
            id: role.id,
            name: role.name || role.code || role.id,
          })),
        );
      })
      .catch(() => {
        if (isMounted) {
          setRolesError('Unable to load approver roles.');
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (!isEditMode || !id) return;
    approvalsApi
      .getWorkflow(id)
      .then((response) => {
        const workflow = response.data;
        const sortedLevels = [...workflow.levels].sort(
          (a, b) => a.levelNumber - b.levelNumber,
        );
        form.reset({
          name: workflow.workflowName,
          description: workflow.description || '',
          transactionType: workflow.workflowType,
          isActive: workflow.isActive,
          levels: sortedLevels.map((level, index) => {
            const nextLevel = sortedLevels[index + 1];
            const minAmount = Number(level.thresholdAmount || 0);
            return {
              level: level.levelNumber,
              roleId: level.approverRoles?.[0] || '',
              minAmount,
              maxAmount: nextLevel ? Number(nextLevel.thresholdAmount || 0) - 1 : 999999999,
              isOptional: false,
            };
          }),
        });
      })
      .catch(() => {
        form.setError('root', {
          type: 'manual',
          message: 'Unable to load approval matrix rule.',
        });
      });
  }, [form, id, isEditMode]);

  const onSubmit = async (data: MatrixFormData) => {
    if (!organizationId) {
      form.setError('root', {
        type: 'manual',
        message: 'Select an organization before saving approval rules.',
      });
      return;
    }
    setIsSubmitting(true);
    try {
      const payload: ApprovalWorkflowPayload = {
        workflowType: data.transactionType as ApprovalWorkflowType,
        workflowName: data.name,
        description: data.description || null,
        thresholdAmount: Math.min(...data.levels.map((level) => level.minAmount)),
        thresholdCurrency: 'INR',
        approvalLevels: data.levels.length,
        isSequential: true,
        autoApproveOnTimeout: false,
        allowSelfApproval: false,
        notifyOnSubmit: true,
        notifyOnApproval: true,
        notifyOnRejection: true,
        levels: data.levels.map((level, index) => {
          const role = roles.find((item) => item.id === level.roleId);
          return {
            levelNumber: index + 1,
            levelName: role?.name || `Level ${index + 1}`,
            approverRoles: [level.roleId],
            approverUsers: null,
            minApprovers: 1,
            thresholdAmount: level.minAmount,
            escalationHours: null,
            escalationUserId: null,
          };
        }),
      };
      if (isEditMode && id) {
        const { workflowType: _workflowType, ...updatePayload } = payload;
        await approvalsApi.updateWorkflow(id, {
          ...updatePayload,
          isActive: data.isActive,
        });
      } else {
        await approvalsApi.createWorkflow(payload);
      }
      navigate('/admin/accounting/approval-matrix');
    } catch (error) {
      logger.error('Failed to save approval matrix:', error);
      form.setError('root', {
        type: 'manual',
        message: 'Unable to save approval matrix. Check for duplicate transaction type or permission issues.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const addLevel = () => {
    const currentLevels = form.getValues('levels');
    if (currentLevels.length >= 3) return;
    const lastLevel = currentLevels[currentLevels.length - 1];
    append({
      level: currentLevels.length + 1,
      roleId: '',
      minAmount: lastLevel?.maxAmount || 0,
      maxAmount: (lastLevel?.maxAmount || 0) + 500000,
      isOptional: false,
    });
  };

  const moveLevel = (index: number, direction: 'up' | 'down') => {
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    if (newIndex >= 0 && newIndex < fields.length) {
      move(index, newIndex);
      // Update level numbers
      const levels = form.getValues('levels');
      levels.forEach((level, i) => {
        form.setValue(`levels.${i}.level`, i + 1);
      });
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title={isEditMode ? 'Edit Approval Matrix' : 'Create Approval Matrix'}
        subtitle={
          isEditMode
            ? 'Modify the approval workflow configuration'
            : 'Define a new approval workflow'
        }
        breadcrumbs={[
          { label: 'Approval Matrix', to: '/admin/accounting/approval-matrix' },
          { label: isEditMode ? 'Edit' : 'Create' },
        ]}
      />

      <Card className="border-emerald-200 bg-emerald-50">
        <CardContent className="pt-6 text-sm text-emerald-900">
          Approval matrix rules are persisted in the core maker-checker workflow engine and apply
          server-side for configured transaction types.
        </CardContent>
      </Card>
      {rolesError && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6 text-sm text-red-900">{rolesError}</CardContent>
        </Card>
      )}
      {form.formState.errors.root?.message && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6 text-sm text-red-900">
            {form.formState.errors.root.message}
          </CardContent>
        </Card>
      )}

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
              <CardDescription>Configure the approval matrix details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Matrix Name</FormLabel>
                      <FormControl>
                        <Input placeholder="e.g., GL Posting Approval" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="transactionType"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Transaction Type</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        value={field.value}
                        disabled={isEditMode}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select transaction type" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {transactionTypes.map(type => (
                            <SelectItem key={type.id} value={type.id}>
                              {type.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Input placeholder="Description of this approval workflow" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="isActive"
                render={({ field }) => (
                  <FormItem className="flex items-center justify-between rounded-lg border p-4">
                    <div>
                      <FormLabel>Active</FormLabel>
                      <FormDescription>
                        Enable this approval matrix for the selected transaction type
                      </FormDescription>
                    </div>
                    <FormControl>
                      <Switch checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          {/* Approval Levels */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Approval Levels</span>
                <Button type="button" variant="outline" size="sm" onClick={addLevel}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Level
                </Button>
              </CardTitle>
              <CardDescription>
                Define the approval hierarchy with amount-based routing
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[80px]">Level</TableHead>
                    <TableHead>Approving Role</TableHead>
                    <TableHead className="w-[180px]">Min Amount</TableHead>
                    <TableHead className="w-[180px]">Max Amount</TableHead>
                    <TableHead className="w-[100px] text-center">Optional</TableHead>
                    <TableHead className="w-[120px] text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {fields.map((field, index) => (
                    <TableRow key={field.id}>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0"
                            onClick={() => moveLevel(index, 'up')}
                            disabled={index === 0}
                          >
                            <ArrowUp className="h-3 w-3" />
                          </Button>
                          <span className="font-bold w-6 text-center">{index + 1}</span>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0"
                            onClick={() => moveLevel(index, 'down')}
                            disabled={index === fields.length - 1}
                          >
                            <ArrowDown className="h-3 w-3" />
                          </Button>
                        </div>
                      </TableCell>
                      <TableCell>
                        <FormField
                          control={form.control}
                          name={`levels.${index}.roleId`}
                          render={({ field }) => (
                            <Select onValueChange={field.onChange} value={field.value}>
                              <SelectTrigger>
                                <SelectValue placeholder="Select role" />
                              </SelectTrigger>
                              <SelectContent>
                                {roles.map(role => (
                                  <SelectItem key={role.id} value={role.id}>
                                    {role.name}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          )}
                        />
                      </TableCell>
                      <TableCell>
                        <FormField
                          control={form.control}
                          name={`levels.${index}.minAmount`}
                          render={({ field }) => (
                            <Input
                              type="number"
                              placeholder="0"
                              {...field}
                              onChange={(e) => field.onChange(Number(e.target.value))}
                            />
                          )}
                        />
                      </TableCell>
                      <TableCell>
                        <FormField
                          control={form.control}
                          name={`levels.${index}.maxAmount`}
                          render={({ field }) => (
                            <Input
                              type="number"
                              placeholder="100000"
                              {...field}
                              onChange={(e) => field.onChange(Number(e.target.value))}
                            />
                          )}
                        />
                      </TableCell>
                      <TableCell className="text-center">
                        <FormField
                          control={form.control}
                          name={`levels.${index}.isOptional`}
                          render={({ field }) => (
                            <Switch checked={field.value} onCheckedChange={field.onChange} />
                          )}
                        />
                      </TableCell>
                      <TableCell className="text-right">
                        {fields.length > 1 && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => remove(index)}
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Preview */}
              <div className="mt-6 p-4 bg-muted rounded-lg">
                <h4 className="font-medium mb-3">Approval Flow Preview</h4>
                <div className="flex items-center flex-wrap gap-2">
                  {fields.map((field, index) => {
                    const roleId = form.watch(`levels.${index}.roleId`);
                    const role = roles.find(r => r.id === roleId);
                    const minAmount = form.watch(`levels.${index}.minAmount`);
                    const maxAmount = form.watch(`levels.${index}.maxAmount`);
                    return (
                      <div key={field.id} className="flex items-center gap-2">
                        <div className="bg-background border rounded-lg p-3 text-center">
                          <div className="text-xs text-muted-foreground">Level {index + 1}</div>
                          <div className="font-medium">{role?.name || 'Not set'}</div>
                          <div className="text-xs text-muted-foreground">
                            {formatCurrency(minAmount)} - {formatCurrency(maxAmount)}
                          </div>
                        </div>
                        {index < fields.length - 1 && (
                          <div className="text-muted-foreground">→</div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="flex gap-2">
            <Button type="submit" disabled={isSubmitting}>
              <Save className="h-4 w-4 mr-2" />
              {isSubmitting ? 'Saving...' : isEditMode ? 'Update Matrix' : 'Create Matrix'}
            </Button>
            <Button type="button" variant="ghost" onClick={() => navigate(-1)}>
              Cancel
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
}
