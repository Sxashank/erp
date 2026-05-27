import { zodResolver } from '@hookform/resolvers/zod';
import { Save, Send, Plus, Trash2, Upload } from 'lucide-react';
import { useForm, useFieldArray } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';
import { z } from 'zod';

import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
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
import { Textarea } from '@/components/ui/textarea';
import { logger } from '@/lib/logger';
const expenseLineSchema = z.object({
  date: z.string().min(1, 'Date is required'),
  category: z.string().min(1, 'Category is required'),
  description: z.string().min(1, 'Description is required'),
  amount: z.number().min(0.01, 'Amount must be greater than 0'),
  receipt: z.string().optional(),
});

const expenseSchema = z.object({
  projectId: z.string().optional(),
  purpose: z.string().min(1, 'Purpose is required'),
  remarks: z.string().optional(),
  lines: z.array(expenseLineSchema).min(1, 'At least one expense line is required'),
});

type ExpenseFormData = z.infer<typeof expenseSchema>;

const categories = [
  { value: 'Travel', label: 'Travel & Conveyance' },
  { value: 'Food & Entertainment', label: 'Food & Entertainment' },
  { value: 'Office Supplies', label: 'Office Supplies' },
  { value: 'Communication', label: 'Communication' },
  { value: 'Accommodation', label: 'Accommodation' },
  { value: 'Training', label: 'Training & Education' },
  { value: 'Other', label: 'Other' },
];

const projects = [
  { id: '1', name: 'Project Alpha' },
  { id: '2', name: 'Project Beta' },
  { id: '3', name: 'Internal Operations' },
];
export default function ESSExpenseForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = Boolean(id);

  const form = useForm<ExpenseFormData>({
    resolver: zodResolver(expenseSchema),
    defaultValues: {
      projectId: '',
      purpose: '',
      remarks: '',
      lines: [
        {
          date: new Date().toISOString().split('T')[0],
          category: '',
          description: '',
          amount: 0,
          receipt: '',
        },
      ],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: 'lines',
  });

  const onSubmit = (data: ExpenseFormData, submitForApproval = false) => {
    logger.debug('Expense submitted:', { ...data, submitForApproval });
    navigate('/ess/expenses');
  };

  const totalAmount = fields.reduce((sum, _, index) => {
    return sum + (form.watch(`lines.${index}.amount`) || 0);
  }, 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEdit ? 'Edit Expense Claim' : 'New Expense Claim'}
        subtitle={
          isEdit ? 'Update expense details' : 'Submit a new expense claim for reimbursement'
        }
        breadcrumbs={[
          { label: 'Expenses', to: '/ess/expenses' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <Form {...form}>
        <form className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Expense Details</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <FormField
                control={form.control}
                name="purpose"
                render={({ field }) => (
                  <FormItem className="md:col-span-2">
                    <FormLabel>Purpose of Expense *</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g., Client visit to Mumbai" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="projectId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Project / Cost Center</FormLabel>
                    <Select
                      onValueChange={(v) => field.onChange(v === '__none__' ? '' : v)}
                      value={field.value || '__none__'}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select project (optional)" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="__none__">None</SelectItem>
                        {projects.map((proj) => (
                          <SelectItem key={proj.id} value={proj.id}>
                            {proj.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormDescription>Associate with a project for cost tracking</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="remarks"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Additional Remarks</FormLabel>
                    <FormControl>
                      <Textarea placeholder="Any additional notes" rows={2} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Expense Items</CardTitle>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() =>
                  append({
                    date: new Date().toISOString().split('T')[0],
                    category: '',
                    description: '',
                    amount: 0,
                    receipt: '',
                  })
                }
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Item
              </Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-32">Date</TableHead>
                    <TableHead className="w-40">Category</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="w-32">Amount</TableHead>
                    <TableHead className="w-32">Receipt</TableHead>
                    <TableHead className="w-16"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {fields.map((field, index) => (
                    <TableRow key={field.id}>
                      <TableCell>
                        <FormField
                          control={form.control}
                          name={`lines.${index}.date`}
                          render={({ field }) => <Input type="date" className="w-32" {...field} />}
                        />
                      </TableCell>
                      <TableCell>
                        <FormField
                          control={form.control}
                          name={`lines.${index}.category`}
                          render={({ field }) => (
                            <Select onValueChange={field.onChange} value={field.value}>
                              <SelectTrigger className="w-40">
                                <SelectValue placeholder="Select" />
                              </SelectTrigger>
                              <SelectContent>
                                {categories.map((cat) => (
                                  <SelectItem key={cat.value} value={cat.value}>
                                    {cat.label}
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
                          name={`lines.${index}.description`}
                          render={({ field }) => <Input placeholder="Description" {...field} />}
                        />
                      </TableCell>
                      <TableCell>
                        <FormField
                          control={form.control}
                          name={`lines.${index}.amount`}
                          render={({ field }) => (
                            <Input
                              type="number"
                              min="0"
                              step="0.01"
                              className="w-32"
                              {...field}
                              onChange={(e) => field.onChange(parseFloat(e.target.value) || 0)}
                            />
                          )}
                        />
                      </TableCell>
                      <TableCell>
                        <Button type="button" variant="outline" size="sm">
                          <Upload className="h-4 w-4" />
                        </Button>
                      </TableCell>
                      <TableCell>
                        {fields.length > 1 && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            onClick={() => remove(index)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              <div className="mt-4 flex justify-end">
                <div className="rounded-lg bg-muted p-4">
                  <div className="text-sm text-muted-foreground">Total Amount</div>
                  <div className="text-2xl font-bold">
                    {formatIndianCompactCurrency(totalAmount)}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-end gap-4">
            <Button type="button" variant="outline" onClick={() => navigate(-1)}>
              Cancel
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={form.handleSubmit((data) => onSubmit(data, false))}
            >
              <Save className="mr-2 h-4 w-4" />
              Save as Draft
            </Button>
            <Button type="button" onClick={form.handleSubmit((data) => onSubmit(data, true))}>
              <Send className="mr-2 h-4 w-4" />
              Submit for Approval
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
}
