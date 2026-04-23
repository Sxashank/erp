/**
 * Entity Financials Tab
 * Inline management of entity financial statements (NO MODALS)
 */

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Plus, Edit, Trash2, X, Check, Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from '@/components/ui/form';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

import { AmountInput } from '@/components/lending/common/AmountInput';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';

import { entityApi } from '@/services/lending';
import type { EntityFinancial } from '@/types/lending';

const financialSchema = z.object({
  financial_year: z.string().regex(/^\d{4}-\d{2}$/, 'Format: YYYY-YY (e.g., 2024-25)'),
  revenue: z.number().nonnegative().optional(),
  ebitda: z.number().optional(),
  depreciation: z.number().nonnegative().optional(),
  interest_expense: z.number().nonnegative().optional(),
  pbt: z.number().optional(),
  tax: z.number().nonnegative().optional(),
  net_profit: z.number().optional(),
  net_worth: z.number().optional(),
  total_debt: z.number().nonnegative().optional(),
  current_assets: z.number().nonnegative().optional(),
  current_liabilities: z.number().nonnegative().optional(),
  audited: z.boolean().default(false),
});

type FinancialFormData = z.infer<typeof financialSchema>;

interface EntityFinancialsTabProps {
  entityId: string;
}

export default function EntityFinancialsTab({ entityId }: EntityFinancialsTabProps) {
  const [financials, setFinancials] = useState<EntityFinancial[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [saving, setSaving] = useState(false);

  const form = useForm<FinancialFormData>({
    resolver: zodResolver(financialSchema) as any,
    defaultValues: {
      financial_year: '',
      revenue: undefined,
      ebitda: undefined,
      depreciation: undefined,
      interest_expense: undefined,
      pbt: undefined,
      tax: undefined,
      net_profit: undefined,
      net_worth: undefined,
      total_debt: undefined,
      current_assets: undefined,
      current_liabilities: undefined,
      audited: false,
    },
  });

  useEffect(() => {
    loadFinancials();
  }, [entityId]);

  const loadFinancials = async () => {
    setLoading(true);
    try {
      const data = await entityApi.getEntityFinancials(entityId);
      setFinancials(data);
    } catch (error) {
      console.error('Failed to load financials:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddNew = () => {
    // Suggest next financial year
    const currentYear = new Date().getFullYear();
    const currentMonth = new Date().getMonth();
    const fyYear = currentMonth >= 3 ? currentYear : currentYear - 1;
    const suggestedFY = `${fyYear}-${(fyYear + 1).toString().slice(-2)}`;

    form.reset({
      financial_year: suggestedFY,
      revenue: undefined,
      ebitda: undefined,
      depreciation: undefined,
      interest_expense: undefined,
      pbt: undefined,
      tax: undefined,
      net_profit: undefined,
      net_worth: undefined,
      total_debt: undefined,
      current_assets: undefined,
      current_liabilities: undefined,
      audited: false,
    });
    setIsAdding(true);
    setEditingId(null);
  };

  const handleEdit = (financial: EntityFinancial) => {
    form.reset({
      financial_year: financial.financial_year,
      revenue: financial.revenue || undefined,
      ebitda: financial.ebitda || undefined,
      depreciation: financial.depreciation || undefined,
      interest_expense: financial.interest_expense || undefined,
      pbt: financial.pbt || undefined,
      tax: financial.tax || undefined,
      net_profit: financial.net_profit || undefined,
      net_worth: financial.net_worth || undefined,
      total_debt: financial.total_debt || undefined,
      current_assets: financial.current_assets || undefined,
      current_liabilities: financial.current_liabilities || undefined,
      audited: financial.audited,
    });
    setEditingId(financial.financial_id);
    setIsAdding(false);
  };

  const handleCancel = () => {
    form.reset();
    setEditingId(null);
    setIsAdding(false);
  };

  const handleSave = async (data: FinancialFormData) => {
    setSaving(true);
    try {
      if (editingId) {
        await entityApi.updateEntityFinancial(entityId, editingId, data);
      } else {
        await entityApi.addEntityFinancial(entityId, data);
      }
      await loadFinancials();
      handleCancel();
    } catch (error) {
      console.error('Failed to save financial:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (financialId: string) => {
    if (!confirm('Are you sure you want to delete this financial year data?')) return;
    try {
      await entityApi.deleteEntityFinancial(entityId, financialId);
      await loadFinancials();
    } catch (error) {
      console.error('Failed to delete financial:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Financial Statements</CardTitle>
          <CardDescription>
            Annual financial data for credit analysis (amounts in INR)
          </CardDescription>
        </div>
        {!isAdding && !editingId && (
          <Button onClick={handleAddNew}>
            <Plus className="mr-2 h-4 w-4" />
            Add Financial Year
          </Button>
        )}
      </CardHeader>
      <CardContent>
        {/* Add/Edit Form */}
        {(isAdding || editingId) && (
          <div className="mb-6 p-4 border rounded-lg bg-gray-50">
            <h4 className="font-medium mb-4">
              {editingId ? 'Edit Financial Data' : 'Add Financial Year Data'}
            </h4>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(handleSave as any)} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <FormField
                    control={form.control}
                    name="financial_year"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Financial Year *</FormLabel>
                        <FormControl>
                          <Input placeholder="YYYY-YY" maxLength={7} {...field} />
                        </FormControl>
                        <FormDescription>e.g., 2024-25</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="audited"
                    render={({ field }) => (
                      <FormItem className="flex items-end space-x-2 space-y-0 pb-2">
                        <FormControl>
                          <Checkbox
                            checked={field.value}
                            onCheckedChange={field.onChange}
                          />
                        </FormControl>
                        <FormLabel className="font-normal">Audited</FormLabel>
                      </FormItem>
                    )}
                  />
                </div>

                <div className="border-t pt-4">
                  <h5 className="text-sm font-medium text-gray-500 mb-4">Profit & Loss</h5>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <FormField
                      control={form.control}
                      name="revenue"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Revenue</FormLabel>
                          <FormControl>
                            <AmountInput
                              value={field.value}
                              onChange={field.onChange}
                              placeholder="Total revenue"
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="ebitda"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>EBITDA</FormLabel>
                          <FormControl>
                            <AmountInput
                              value={field.value}
                              onChange={field.onChange}
                              placeholder="EBITDA"
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="depreciation"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Depreciation</FormLabel>
                          <FormControl>
                            <AmountInput
                              value={field.value}
                              onChange={field.onChange}
                              placeholder="Depreciation"
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="interest_expense"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Interest Expense</FormLabel>
                          <FormControl>
                            <AmountInput
                              value={field.value}
                              onChange={field.onChange}
                              placeholder="Interest"
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="pbt"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>PBT</FormLabel>
                          <FormControl>
                            <AmountInput
                              value={field.value}
                              onChange={field.onChange}
                              placeholder="Profit Before Tax"
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="tax"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Tax</FormLabel>
                          <FormControl>
                            <AmountInput
                              value={field.value}
                              onChange={field.onChange}
                              placeholder="Tax expense"
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="net_profit"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Net Profit</FormLabel>
                          <FormControl>
                            <AmountInput
                              value={field.value}
                              onChange={field.onChange}
                              placeholder="PAT"
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </div>

                <div className="border-t pt-4">
                  <h5 className="text-sm font-medium text-gray-500 mb-4">Balance Sheet</h5>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <FormField
                      control={form.control}
                      name="net_worth"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Net Worth</FormLabel>
                          <FormControl>
                            <AmountInput
                              value={field.value}
                              onChange={field.onChange}
                              placeholder="Net worth"
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="total_debt"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Total Debt</FormLabel>
                          <FormControl>
                            <AmountInput
                              value={field.value}
                              onChange={field.onChange}
                              placeholder="Total borrowings"
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="current_assets"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Current Assets</FormLabel>
                          <FormControl>
                            <AmountInput
                              value={field.value}
                              onChange={field.onChange}
                              placeholder="Current assets"
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="current_liabilities"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Current Liabilities</FormLabel>
                          <FormControl>
                            <AmountInput
                              value={field.value}
                              onChange={field.onChange}
                              placeholder="Current liabilities"
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button type="submit" disabled={saving}>
                    {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    <Check className="mr-2 h-4 w-4" />
                    Save
                  </Button>
                  <Button type="button" variant="outline" onClick={handleCancel}>
                    <X className="mr-2 h-4 w-4" />
                    Cancel
                  </Button>
                </div>
              </form>
            </Form>
          </div>
        )}

        {/* Financials Table */}
        {financials.length === 0 && !isAdding ? (
          <p className="text-center py-8 text-gray-500">
            No financial data added yet. Click "Add Financial Year" to add one.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">FY</th>
                  <th className="text-right p-2">Revenue</th>
                  <th className="text-right p-2">EBITDA</th>
                  <th className="text-right p-2">Net Profit</th>
                  <th className="text-right p-2">Net Worth</th>
                  <th className="text-right p-2">Total Debt</th>
                  <th className="text-center p-2">Status</th>
                  <th className="text-right p-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {financials.map((fin) => (
                  <tr
                    key={fin.financial_id}
                    className={`border-b ${editingId === fin.financial_id ? 'hidden' : ''}`}
                  >
                    <td className="p-2 font-medium">{fin.financial_year}</td>
                    <td className="p-2 text-right">
                      <AmountDisplay amount={fin.revenue || 0} />
                    </td>
                    <td className="p-2 text-right">
                      <AmountDisplay amount={fin.ebitda || 0} />
                    </td>
                    <td className="p-2 text-right">
                      <AmountDisplay amount={fin.net_profit || 0} />
                    </td>
                    <td className="p-2 text-right">
                      <AmountDisplay amount={fin.net_worth || 0} />
                    </td>
                    <td className="p-2 text-right">
                      <AmountDisplay amount={fin.total_debt || 0} />
                    </td>
                    <td className="p-2 text-center">
                      <Badge variant={fin.audited ? 'default' : 'secondary'}>
                        {fin.audited ? 'Audited' : 'Provisional'}
                      </Badge>
                    </td>
                    <td className="p-2 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(fin)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(fin.financial_id)}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
