/**
 * Entity Bank Accounts Tab
 * Inline management of entity bank accounts (NO MODALS)
 */

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Plus, Edit, Trash2, X, Check, Loader2, ShieldCheck } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

import { entityApi } from '@/services/lending';
import type { EntityBankAccount } from '@/types/lending';

const ACCOUNT_TYPES = [
  { value: 'SAVINGS', label: 'Savings Account' },
  { value: 'CURRENT', label: 'Current Account' },
  { value: 'OVERDRAFT', label: 'Overdraft Account' },
  { value: 'CASH_CREDIT', label: 'Cash Credit Account' },
];

const bankAccountSchema = z.object({
  bank_name: z.string().min(2, 'Bank name is required'),
  branch_name: z.string().min(2, 'Branch name is required'),
  account_number: z.string().min(9, 'Account number must be at least 9 digits').max(18),
  ifsc_code: z.string().regex(/^[A-Z]{4}0[A-Z0-9]{6}$/, 'Invalid IFSC code format'),
  account_type: z.enum(['SAVINGS', 'CURRENT', 'OVERDRAFT', 'CASH_CREDIT']),
  account_holder_name: z.string().optional(),
  is_primary: z.boolean().default(false),
});

type BankAccountFormData = z.infer<typeof bankAccountSchema>;

interface EntityBankAccountsTabProps {
  entityId: string;
}

export default function EntityBankAccountsTab({ entityId }: EntityBankAccountsTabProps) {
  const [accounts, setAccounts] = useState<EntityBankAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [saving, setSaving] = useState(false);

  const form = useForm<BankAccountFormData>({
    resolver: zodResolver(bankAccountSchema) as any,
    defaultValues: {
      bank_name: '',
      branch_name: '',
      account_number: '',
      ifsc_code: '',
      account_type: 'CURRENT',
      account_holder_name: '',
      is_primary: false,
    },
  });

  useEffect(() => {
    loadAccounts();
  }, [entityId]);

  const loadAccounts = async () => {
    setLoading(true);
    try {
      const data = await entityApi.getEntityBankAccounts(entityId);
      setAccounts(data);
    } catch (error) {
      console.error('Failed to load bank accounts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddNew = () => {
    form.reset({
      bank_name: '',
      branch_name: '',
      account_number: '',
      ifsc_code: '',
      account_type: 'CURRENT',
      account_holder_name: '',
      is_primary: false,
    });
    setIsAdding(true);
    setEditingId(null);
  };

  const handleEdit = (account: EntityBankAccount) => {
    form.reset({
      bank_name: account.bank_name,
      branch_name: account.branch_name,
      account_number: account.account_number,
      ifsc_code: account.ifsc_code,
      account_type: account.account_type as BankAccountFormData['account_type'],
      account_holder_name: account.account_holder_name || '',
      is_primary: account.is_primary,
    });
    setEditingId(account.bank_account_id);
    setIsAdding(false);
  };

  const handleCancel = () => {
    form.reset();
    setEditingId(null);
    setIsAdding(false);
  };

  const handleSave = async (data: BankAccountFormData) => {
    setSaving(true);
    try {
      if (editingId) {
        await entityApi.updateEntityBankAccount(entityId, editingId, data as any);
      } else {
        await entityApi.addEntityBankAccount(entityId, data as any);
      }
      await loadAccounts();
      handleCancel();
    } catch (error) {
      console.error('Failed to save bank account:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (accountId: string) => {
    if (!confirm('Are you sure you want to delete this bank account?')) return;
    try {
      await entityApi.deleteEntityBankAccount(entityId, accountId);
      await loadAccounts();
    } catch (error) {
      console.error('Failed to delete bank account:', error);
    }
  };

  // Auto-populate bank name from IFSC (simplified)
  const handleIFSCChange = (value: string) => {
    form.setValue('ifsc_code', value.toUpperCase());
    // In production, this would call an API to get bank details
    const bankCodes: Record<string, string> = {
      'HDFC': 'HDFC Bank',
      'ICIC': 'ICICI Bank',
      'SBIN': 'State Bank of India',
      'AXIS': 'Axis Bank',
      'KKBK': 'Kotak Mahindra Bank',
      'UTIB': 'Axis Bank',
      'YESB': 'Yes Bank',
      'PUNB': 'Punjab National Bank',
      'BARB': 'Bank of Baroda',
      'CNRB': 'Canara Bank',
    };
    const bankCode = value.substring(0, 4).toUpperCase();
    if (bankCodes[bankCode]) {
      form.setValue('bank_name', bankCodes[bankCode]);
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
          <CardTitle>Bank Accounts</CardTitle>
          <CardDescription>
            Bank accounts for disbursement and collection
          </CardDescription>
        </div>
        {!isAdding && !editingId && (
          <Button onClick={handleAddNew}>
            <Plus className="mr-2 h-4 w-4" />
            Add Bank Account
          </Button>
        )}
      </CardHeader>
      <CardContent>
        {/* Add/Edit Form */}
        {(isAdding || editingId) && (
          <div className="mb-6 p-4 border rounded-lg bg-gray-50">
            <h4 className="font-medium mb-4">
              {editingId ? 'Edit Bank Account' : 'Add New Bank Account'}
            </h4>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(handleSave as any)} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <FormField
                    control={form.control}
                    name="ifsc_code"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>IFSC Code *</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="e.g., HDFC0001234"
                            maxLength={11}
                            {...field}
                            onChange={(e) => handleIFSCChange(e.target.value)}
                          />
                        </FormControl>
                        <FormDescription>Bank/branch will auto-fill</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="bank_name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Bank Name *</FormLabel>
                        <FormControl>
                          <Input placeholder="Bank name" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="branch_name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Branch Name *</FormLabel>
                        <FormControl>
                          <Input placeholder="Branch name" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="account_number"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Account Number *</FormLabel>
                        <FormControl>
                          <Input placeholder="Account number" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="account_type"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Account Type *</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {ACCOUNT_TYPES.map((type) => (
                              <SelectItem key={type.value} value={type.value}>
                                {type.label}
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
                    name="account_holder_name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Account Holder Name</FormLabel>
                        <FormControl>
                          <Input placeholder="Name as in bank" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <FormField
                  control={form.control}
                  name="is_primary"
                  render={({ field }) => (
                    <FormItem className="flex items-center space-x-2 space-y-0">
                      <FormControl>
                        <Checkbox
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </FormControl>
                      <FormLabel className="font-normal">
                        Primary Account (for disbursement)
                      </FormLabel>
                    </FormItem>
                  )}
                />

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

        {/* Accounts List */}
        {accounts.length === 0 && !isAdding ? (
          <p className="text-center py-8 text-gray-500">
            No bank accounts added yet. Click "Add Bank Account" to add one.
          </p>
        ) : (
          <div className="space-y-3">
            {accounts.map((account) => (
              <div
                key={account.bank_account_id}
                className={`flex items-start justify-between p-4 border rounded-lg ${
                  editingId === account.bank_account_id ? 'hidden' : ''
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-medium">{account.bank_name}</p>
                    <Badge variant="outline">
                      {ACCOUNT_TYPES.find(t => t.value === account.account_type)?.label || account.account_type}
                    </Badge>
                    {account.is_primary && <Badge>Primary</Badge>}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    A/C: {account.account_number}
                  </p>
                  <p className="text-sm text-gray-600">
                    IFSC: {account.ifsc_code} | Branch: {account.branch_name}
                  </p>
                  {account.account_holder_name && (
                    <p className="text-sm text-gray-500">
                      Holder: {account.account_holder_name}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={account.is_verified ? 'default' : 'secondary'}>
                    {account.is_verified ? (
                      <>
                        <ShieldCheck className="h-3 w-3 mr-1" />
                        Verified
                      </>
                    ) : (
                      'Pending'
                    )}
                  </Badge>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleEdit(account)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(account.bank_account_id)}
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
