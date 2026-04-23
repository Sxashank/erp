import { useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { PageHeader } from '@/components/common/PageHeader';
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
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from '@/components/ui/form';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  ArrowLeft,
  Shield,
  Plus,
  Trash2,
  Save,
  ArrowUp,
  ArrowDown,
} from 'lucide-react';

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
  levels: z.array(levelSchema).min(1, 'At least one level is required'),
});

type MatrixFormData = z.infer<typeof matrixSchema>;

// Mock roles
const roles = [
  { id: 'ROLE001', name: 'Branch Manager' },
  { id: 'ROLE002', name: 'Regional Manager' },
  { id: 'ROLE003', name: 'Finance Manager' },
  { id: 'ROLE004', name: 'CFO' },
  { id: 'ROLE005', name: 'CEO' },
  { id: 'ROLE006', name: 'Board' },
];

// Mock transaction types
const transactionTypes = [
  { id: 'GL_POSTING', name: 'GL Posting' },
  { id: 'JOURNAL_VOUCHER', name: 'Journal Voucher' },
  { id: 'PAYMENT', name: 'Payment/Receipt' },
  { id: 'LOAN_DISBURSEMENT', name: 'Loan Disbursement' },
  { id: 'LOAN_SANCTION', name: 'Loan Sanction' },
  { id: 'EXPENSE', name: 'Expense Approval' },
  { id: 'VENDOR_PAYMENT', name: 'Vendor Payment' },
  { id: 'SALARY', name: 'Salary Processing' },
];

// Mock existing matrix for edit mode
const existingMatrix = {
  id: '1',
  name: 'GL Posting Approval',
  description: 'Approval workflow for GL postings based on amount',
  transactionType: 'GL_POSTING',
  isActive: true,
  levels: [
    { level: 1, roleId: 'ROLE001', minAmount: 0, maxAmount: 100000, isOptional: false },
    { level: 2, roleId: 'ROLE003', minAmount: 100000, maxAmount: 500000, isOptional: false },
    { level: 3, roleId: 'ROLE004', minAmount: 500000, maxAmount: 5000000, isOptional: false },
    { level: 4, roleId: 'ROLE005', minAmount: 5000000, maxAmount: 999999999, isOptional: false },
  ],
};

export default function ApprovalMatrixCreate() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const isEditMode = !!id;

  const form = useForm<MatrixFormData>({
    resolver: zodResolver(matrixSchema),
    defaultValues: isEditMode
      ? existingMatrix
      : {
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

  const onSubmit = async (data: MatrixFormData) => {
    setIsSubmitting(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    setIsSubmitting(false);
    navigate('/admin/accounting/approval-matrix');
  };

  const addLevel = () => {
    const currentLevels = form.getValues('levels');
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
                      <Select onValueChange={field.onChange} value={field.value}>
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
