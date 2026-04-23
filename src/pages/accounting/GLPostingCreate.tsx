import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { AlertTriangle, Calculator, Plus, Save, Send, Trash2 } from 'lucide-react';
import { useState } from 'react';
import { useFieldArray, useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';

import {
  EmptyState,
  ErrorState,
  FormSection,
  FormShell,
  PageHeader,
  SkeletonTable,
} from '@/components/common';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
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
import { useToast } from '@/hooks/use-toast';
import { useAccounts, usePeriods } from '@/hooks/finance/useAccounts';
import { formatCurrency } from '@/lib/utils';
import { vouchersApi } from '@/services/api';
import { useActiveOrganizationId } from '@/stores/organizationStore';

const entrySchema = z
  .object({
    accountId: z.string().min(1, 'Account is required'),
    description: z.string().optional(),
    debit: z.number().min(0),
    credit: z.number().min(0),
    costCenter: z.string().optional(),
  })
  .superRefine((v, ctx) => {
    if (v.debit > 0 && v.credit > 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Each line must be either debit or credit, not both',
        path: ['credit'],
      });
    }
    if (v.debit === 0 && v.credit === 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Enter a debit or credit amount',
        path: ['debit'],
      });
    }
  });

const postingSchema = z
  .object({
    description: z.string().min(1, 'Description is required'),
    postingDate: z.string().min(1, 'Posting date is required'),
    period: z.string().min(1, 'Period is required'),
    reference: z.string().optional(),
    narration: z.string().optional(),
    entries: z.array(entrySchema).min(2, 'At least 2 entries required'),
  })
  .superRefine((v, ctx) => {
    const totalDebit = v.entries.reduce((s, e) => s + (e.debit || 0), 0);
    const totalCredit = v.entries.reduce((s, e) => s + (e.credit || 0), 0);
    if (Math.abs(totalDebit - totalCredit) > 0.009) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: `Voucher is not balanced (debit ${totalDebit.toFixed(2)} ≠ credit ${totalCredit.toFixed(2)})`,
        path: ['entries'],
      });
    }
    if (totalDebit === 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Voucher must have a non-zero amount',
        path: ['entries'],
      });
    }
  });

type PostingFormData = z.infer<typeof postingSchema>;

export default function GLPostingCreate(): JSX.Element {
  const navigate = useNavigate();
  const { toast } = useToast();
  const organizationId = useActiveOrganizationId();

  const accountsQuery = useAccounts();
  const periodsQuery = usePeriods();

  const form = useForm<PostingFormData>({
    resolver: zodResolver(postingSchema),
    defaultValues: {
      description: '',
      postingDate: new Date().toISOString().split('T')[0] ?? '',
      period: '',
      reference: '',
      narration: '',
      entries: [
        { accountId: '', description: '', debit: 0, credit: 0, costCenter: '' },
        { accountId: '', description: '', debit: 0, credit: 0, costCenter: '' },
      ],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: 'entries',
  });

  const entries = form.watch('entries');
  const totalDebit = entries.reduce((sum, e) => sum + (Number(e.debit) || 0), 0);
  const totalCredit = entries.reduce((sum, e) => sum + (Number(e.credit) || 0), 0);
  const difference = totalDebit - totalCredit;
  const isBalanced = Math.abs(difference) < 0.009 && totalDebit > 0;

  const submitMutation = useMutation({
    mutationFn: async (payload: { data: PostingFormData; action: 'save' | 'submit' }) => {
      const { data, action } = payload;
      const body = {
        organization_id: organizationId,
        description: data.description,
        posting_date: data.postingDate,
        period_id: data.period,
        reference: data.reference,
        narration: data.narration,
        lines: data.entries.map((e) => ({
          account_id: e.accountId,
          description: e.description,
          debit_amount: e.debit,
          credit_amount: e.credit,
          cost_center_id: e.costCenter || null,
        })),
      };
      const headers: Record<string, string> = {
        'Idempotency-Key': crypto.randomUUID(),
      };
      const created = await vouchersApi.create(body);
      if (action === 'submit' && created.data?.id) {
        await vouchersApi.submit(created.data.id);
      }
      return created.data;
    },
    onSuccess: (_, { action }) => {
      toast({
        title: action === 'submit' ? 'Submitted for approval' : 'Saved as draft',
        description: 'Voucher recorded successfully.',
      });
      navigate('/admin/accounting/gl-postings');
    },
    onError: (err: unknown) => {
      const msg =
        (err as { response?: { data?: { message?: string; detail?: string } } }).response?.data
          ?.message ||
        (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
        'Failed to save voucher';
      toast({ title: 'Error', description: msg, variant: 'destructive' });
    },
  });

  const accounts = accountsQuery.data ?? [];
  const periods = periodsQuery.data ?? [];
  const addEntry = (): void => {
    append({ accountId: '', description: '', debit: 0, credit: 0, costCenter: '' });
  };

  if (!organizationId) {
    return (
      <div className="container mx-auto py-6">
        <PageHeader title="Create GL Posting" />
        <EmptyState
          title="No organization selected"
          subtitle="Select an organization from the header to create a GL posting."
        />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6">
      <PageHeader
        title="Create GL Posting"
        subtitle="Record a new general ledger posting. Every voucher must balance."
        breadcrumbs={[
          { label: 'Accounting', to: '/admin/accounting' },
          { label: 'GL Postings', to: '/admin/accounting/gl-postings' },
          { label: 'New' },
        ]}
      />

      <Form {...form}>
        <form
          className="space-y-6"
          onSubmit={(e) => {
            e.preventDefault();
            void form.handleSubmit((data) =>
              submitMutation.mutateAsync({ data, action: 'submit' }),
            )();
          }}
        >
          <FormShell>
            <FormSection title="Posting details">
              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem className="md:col-span-2">
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Input placeholder="Enter posting description" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="reference"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Reference</FormLabel>
                    <FormControl>
                      <Input placeholder="Reference number" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="postingDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Posting date</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="period"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Accounting period</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue
                            placeholder={
                              periodsQuery.isLoading ? 'Loading…' : 'Select period'
                            }
                          />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {periods.map((p) => {
                          const closed = p.status === 'HARD_CLOSED';
                          return (
                            <SelectItem key={p.id} value={p.id} disabled={closed}>
                              {p.name} {closed && '(closed)'}
                            </SelectItem>
                          );
                        })}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="narration"
                render={({ field }) => (
                  <FormItem className="md:col-span-2">
                    <FormLabel>Narration</FormLabel>
                    <FormControl>
                      <Textarea placeholder="Detailed narration…" rows={2} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormSection>

            <FormSection title="Journal entries">
              <div className="md:col-span-2">
                {accountsQuery.isLoading ? (
                  <SkeletonTable rows={3} columns={5} />
                ) : accountsQuery.error ? (
                  <ErrorState
                    error={accountsQuery.error}
                    onRetry={() => void accountsQuery.refetch()}
                  />
                ) : accounts.length === 0 ? (
                  <EmptyState
                    title="No accounts available"
                    subtitle="Create accounts in the chart of accounts before posting vouchers."
                  />
                ) : (
                  <>
                    <div className="mb-2 flex justify-end">
                      <Button type="button" variant="outline" size="sm" onClick={addEntry}>
                        <Plus className="mr-2 h-4 w-4" />
                        Add entry
                      </Button>
                    </div>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-[260px]">Account</TableHead>
                          <TableHead>Description</TableHead>
                          <TableHead className="w-[150px] text-right">Debit</TableHead>
                          <TableHead className="w-[150px] text-right">Credit</TableHead>
                          <TableHead className="w-[50px]" aria-label="Actions" />
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {fields.map((field, index) => (
                          <TableRow key={field.id}>
                            <TableCell>
                              <FormField
                                control={form.control}
                                name={`entries.${index}.accountId`}
                                render={({ field: f }) => (
                                  <Select onValueChange={f.onChange} value={f.value}>
                                    <SelectTrigger>
                                      <SelectValue placeholder="Select account" />
                                    </SelectTrigger>
                                    <SelectContent>
                                      {accounts.map((acc) => (
                                        <SelectItem key={acc.id} value={acc.id}>
                                          {acc.code} — {acc.name}
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
                                name={`entries.${index}.description`}
                                render={({ field: f }) => (
                                  <Input placeholder="Line description" {...f} />
                                )}
                              />
                            </TableCell>
                            <TableCell>
                              <FormField
                                control={form.control}
                                name={`entries.${index}.debit`}
                                render={({ field: f }) => (
                                  <Input
                                    type="number"
                                    step="0.01"
                                    className="text-right tabular-nums"
                                    {...f}
                                    onChange={(e) => {
                                      const v = Number(e.target.value);
                                      f.onChange(v);
                                      if (v > 0) form.setValue(`entries.${index}.credit`, 0);
                                    }}
                                  />
                                )}
                              />
                            </TableCell>
                            <TableCell>
                              <FormField
                                control={form.control}
                                name={`entries.${index}.credit`}
                                render={({ field: f }) => (
                                  <Input
                                    type="number"
                                    step="0.01"
                                    className="text-right tabular-nums"
                                    {...f}
                                    onChange={(e) => {
                                      const v = Number(e.target.value);
                                      f.onChange(v);
                                      if (v > 0) form.setValue(`entries.${index}.debit`, 0);
                                    }}
                                  />
                                )}
                              />
                            </TableCell>
                            <TableCell>
                              {fields.length > 2 && (
                                <Button
                                  type="button"
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => remove(index)}
                                  aria-label={`Remove line ${index + 1}`}
                                >
                                  <Trash2 className="h-4 w-4 text-destructive" />
                                </Button>
                              )}
                            </TableCell>
                          </TableRow>
                        ))}
                        <TableRow className="bg-muted/50 font-semibold">
                          <TableCell colSpan={2} className="text-right">
                            Total
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {formatCurrency(totalDebit)}
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {formatCurrency(totalCredit)}
                          </TableCell>
                          <TableCell />
                        </TableRow>
                      </TableBody>
                    </Table>

                    <div
                      className={`mt-4 flex items-center justify-between rounded-lg p-4 ${
                        isBalanced ? 'bg-emerald-50' : 'bg-destructive/10'
                      }`}
                      role="status"
                    >
                      <div className="flex items-center gap-2">
                        {isBalanced ? (
                          <Calculator className="h-5 w-5 text-emerald-700" />
                        ) : (
                          <AlertTriangle className="h-5 w-5 text-destructive" />
                        )}
                        <span
                          className={
                            isBalanced ? 'text-emerald-800' : 'text-destructive font-medium'
                          }
                        >
                          {isBalanced
                            ? 'Entries are balanced'
                            : `Out of balance by ${formatCurrency(Math.abs(difference))}`}
                        </span>
                      </div>
                      {!isBalanced && totalDebit + totalCredit > 0 && (
                        <span className="text-sm text-destructive">
                          {difference > 0 ? 'Debit exceeds credit' : 'Credit exceeds debit'}
                        </span>
                      )}
                    </div>
                  </>
                )}
              </div>
            </FormSection>
          </FormShell>

          <div className="flex items-center justify-end gap-2 pb-6">
            <Button
              type="button"
              variant="ghost"
              onClick={() => navigate(-1)}
              disabled={submitMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() =>
                void form.handleSubmit((data) =>
                  submitMutation.mutateAsync({ data, action: 'save' }),
                )()
              }
              disabled={submitMutation.isPending}
            >
              <Save className="mr-2 h-4 w-4" />
              Save as draft
            </Button>
            <Button type="submit" disabled={!isBalanced || submitMutation.isPending}>
              <Send className="mr-2 h-4 w-4" />
              {submitMutation.isPending ? 'Submitting…' : 'Submit for approval'}
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
}
