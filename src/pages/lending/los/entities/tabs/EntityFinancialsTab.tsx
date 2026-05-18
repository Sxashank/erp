/**
 * Entity Financials Tab
 * Inline management of entity financial statements (NO MODALS)
 */

import { zodResolver } from '@hookform/resolvers/zod';
import { Plus, Edit, Trash2, X, Check, Loader2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { AmountInput } from '@/components/lending/common/AmountInput';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
import { Input } from '@/components/ui/input';
import { entityApi } from '@/services/lending';
import type { EntityFinancial } from '@/types/lending';

const financialSchema = z.object({
  financialYear: z.string().regex(/^\d{4}-\d{2}$/, 'Format: YYYY-YY (e.g., 2024-25)'),
  revenue: z.number().nonnegative().optional(),
  ebitda: z.number().optional(),
  depreciation: z.number().nonnegative().optional(),
  interestExpense: z.number().nonnegative().optional(),
  profitBeforeTax: z.number().optional(),
  taxExpense: z.number().nonnegative().optional(),
  netProfit: z.number().optional(),
  netWorth: z.number().optional(),
  totalDebt: z.number().nonnegative().optional(),
  currentAssets: z.number().nonnegative().optional(),
  currentLiabilities: z.number().nonnegative().optional(),
  isAudited: z.boolean(),
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
    resolver: zodResolver(financialSchema),
    defaultValues: {
      financialYear: '',
      revenue: undefined,
      ebitda: undefined,
      depreciation: undefined,
      interestExpense: undefined,
      profitBeforeTax: undefined,
      taxExpense: undefined,
      netProfit: undefined,
      netWorth: undefined,
      totalDebt: undefined,
      currentAssets: undefined,
      currentLiabilities: undefined,
      isAudited: false,
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
    } catch {
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
      financialYear: suggestedFY,
      revenue: undefined,
      ebitda: undefined,
      depreciation: undefined,
      interestExpense: undefined,
      profitBeforeTax: undefined,
      taxExpense: undefined,
      netProfit: undefined,
      netWorth: undefined,
      totalDebt: undefined,
      currentAssets: undefined,
      currentLiabilities: undefined,
      isAudited: false,
    });
    setIsAdding(true);
    setEditingId(null);
  };

  const handleEdit = (financial: EntityFinancial) => {
    form.reset({
      financialYear: financial.financialYear,
      revenue: financial.revenue || undefined,
      ebitda: financial.ebitda || undefined,
      depreciation: financial.depreciation || undefined,
      interestExpense: financial.interestExpense || undefined,
      profitBeforeTax: financial.profitBeforeTax || undefined,
      taxExpense: financial.taxExpense || undefined,
      netProfit: financial.netProfit || undefined,
      netWorth: financial.netWorth || undefined,
      totalDebt: financial.totalDebt || undefined,
      currentAssets: financial.currentAssets || undefined,
      currentLiabilities: financial.currentLiabilities || undefined,
      isAudited: financial.isAudited,
    });
    setEditingId(financial.id);
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
    } catch {
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (financialId: string) => {
    if (!confirm('Are you sure you want to delete this financial year data?')) return;
    try {
      await entityApi.deleteEntityFinancial(entityId, financialId);
      await loadFinancials();
    } catch {}
  };

  if (loading) {
    return (
      <div className="flex h-48 items-center justify-center">
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
          <div className="mb-6 rounded-lg border bg-gray-50 p-4">
            <h4 className="mb-4 font-medium">
              {editingId ? 'Edit Financial Data' : 'Add Financial Year Data'}
            </h4>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(handleSave)} className="space-y-6">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
                  <FormField
                    control={form.control}
                    name="financialYear"
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
                    name="isAudited"
                    render={({ field }) => (
                      <FormItem className="flex items-end space-x-2 space-y-0 pb-2">
                        <FormControl>
                          <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                        </FormControl>
                        <FormLabel className="font-normal">Audited</FormLabel>
                      </FormItem>
                    )}
                  />
                </div>

                <div className="border-t pt-4">
                  <h5 className="mb-4 text-sm font-medium text-gray-500">Profit & Loss</h5>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
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
                      name="interestExpense"
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
                      name="profitBeforeTax"
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
                      name="taxExpense"
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
                      name="netProfit"
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
                  <h5 className="mb-4 text-sm font-medium text-gray-500">Balance Sheet</h5>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
                    <FormField
                      control={form.control}
                      name="netWorth"
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
                      name="totalDebt"
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
                      name="currentAssets"
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
                      name="currentLiabilities"
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
          <p className="py-8 text-center text-gray-500">
            No financial data added yet. Click "Add Financial Year" to add one.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="p-2 text-left">FY</th>
                  <th className="p-2 text-right">Revenue</th>
                  <th className="p-2 text-right">EBITDA</th>
                  <th className="p-2 text-right">Net Profit</th>
                  <th className="p-2 text-right">Net Worth</th>
                  <th className="p-2 text-right">Total Debt</th>
                  <th className="p-2 text-center">Status</th>
                  <th className="p-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {financials.map((fin) => (
                  <tr key={fin.id} className={`border-b ${editingId === fin.id ? 'hidden' : ''}`}>
                    <td className="p-2 font-medium">{fin.financialYear}</td>
                    <td className="p-2 text-right">
                      <AmountDisplay amount={fin.revenue || 0} />
                    </td>
                    <td className="p-2 text-right">
                      <AmountDisplay amount={fin.ebitda || 0} />
                    </td>
                    <td className="p-2 text-right">
                      <AmountDisplay amount={fin.netProfit || 0} />
                    </td>
                    <td className="p-2 text-right">
                      <AmountDisplay amount={fin.netWorth || 0} />
                    </td>
                    <td className="p-2 text-right">
                      <AmountDisplay amount={fin.totalDebt || 0} />
                    </td>
                    <td className="p-2 text-center">
                      <Badge variant={fin.isAudited ? 'default' : 'secondary'}>
                        {fin.isAudited ? 'Audited' : 'Provisional'}
                      </Badge>
                    </td>
                    <td className="p-2 text-right">
                      <Button variant="ghost" size="sm" onClick={() => handleEdit(fin)}>
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => handleDelete(fin.id)}>
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
