/**
 * Entity Bank Accounts Tab
 * Inline management of entity bank accounts (NO MODALS)
 */

import { zodResolver } from '@hookform/resolvers/zod';
import { Plus, Edit, Trash2, X, Check, Loader2, ShieldCheck } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { entityApi } from '@/services/lending';
import type { EntityBankAccount } from '@/types/lending';

const ACCOUNT_TYPES = [
  { value: 'SAVINGS', label: 'Savings Account' },
  { value: 'CURRENT', label: 'Current Account' },
  { value: 'OD', label: 'Overdraft Account' },
  { value: 'CC', label: 'Cash Credit Account' },
];

const bankAccountSchema = z.object({
  bankName: z.string().min(2, 'Bank name is required'),
  branchName: z.string().min(2, 'Branch name is required'),
  accountNumber: z.string().min(9, 'Account number must be at least 9 digits').max(30),
  ifscCode: z.string().regex(/^[A-Z]{4}0[A-Z0-9]{6}$/, 'Invalid IFSC code format'),
  accountType: z.enum(['SAVINGS', 'CURRENT', 'OD', 'CC']),
  accountHolderName: z.string().min(2, 'Account holder name is required'),
  isPrimary: z.boolean(),
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
    resolver: zodResolver(bankAccountSchema),
    defaultValues: {
      bankName: '',
      branchName: '',
      accountNumber: '',
      ifscCode: '',
      accountType: 'CURRENT',
      accountHolderName: '',
      isPrimary: false,
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
    } catch {
    } finally {
      setLoading(false);
    }
  };

  const handleAddNew = () => {
    form.reset({
      bankName: '',
      branchName: '',
      accountNumber: '',
      ifscCode: '',
      accountType: 'CURRENT',
      accountHolderName: '',
      isPrimary: false,
    });
    setIsAdding(true);
    setEditingId(null);
  };

  const handleEdit = (account: EntityBankAccount) => {
    form.reset({
      bankName: account.bankName,
      branchName: account.branchName || '',
      accountNumber: account.accountNumber,
      ifscCode: account.ifscCode,
      accountType: account.accountType as BankAccountFormData['accountType'],
      accountHolderName: account.accountHolderName || '',
      isPrimary: account.isPrimary,
    });
    setEditingId(account.id);
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
        await entityApi.updateEntityBankAccount(entityId, editingId, data);
      } else {
        await entityApi.addEntityBankAccount(entityId, data);
      }
      await loadAccounts();
      handleCancel();
    } catch {
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (accountId: string) => {
    if (!confirm('Are you sure you want to delete this bank account?')) return;
    try {
      await entityApi.deleteEntityBankAccount(entityId, accountId);
      await loadAccounts();
    } catch {}
  };

  // Auto-populate bank name from IFSC (simplified)
  const handleIFSCChange = (value: string) => {
    form.setValue('ifscCode', value.toUpperCase());
    // In production, this would call an API to get bank details
    const bankCodes: Record<string, string> = {
      HDFC: 'HDFC Bank',
      ICIC: 'ICICI Bank',
      SBIN: 'State Bank of India',
      AXIS: 'Axis Bank',
      KKBK: 'Kotak Mahindra Bank',
      UTIB: 'Axis Bank',
      YESB: 'Yes Bank',
      PUNB: 'Punjab National Bank',
      BARB: 'Bank of Baroda',
      CNRB: 'Canara Bank',
    };
    const bankCode = value.substring(0, 4).toUpperCase();
    if (bankCodes[bankCode]) {
      form.setValue('bankName', bankCodes[bankCode]);
    }
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
          <CardTitle>Bank Accounts</CardTitle>
          <CardDescription>Bank accounts for disbursement and collection</CardDescription>
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
          <div className="mb-6 rounded-lg border bg-gray-50 p-4">
            <h4 className="mb-4 font-medium">
              {editingId ? 'Edit Bank Account' : 'Add New Bank Account'}
            </h4>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(handleSave)} className="space-y-4">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                  <FormField
                    control={form.control}
                    name="ifscCode"
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
                    name="bankName"
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
                    name="branchName"
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
                    name="accountNumber"
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
                    name="accountType"
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
                    name="accountHolderName"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Account Holder Name *</FormLabel>
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
                  name="isPrimary"
                  render={({ field }) => (
                    <FormItem className="flex items-center space-x-2 space-y-0">
                      <FormControl>
                        <Checkbox checked={field.value} onCheckedChange={field.onChange} />
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
          <p className="py-8 text-center text-gray-500">
            No bank accounts added yet. Click "Add Bank Account" to add one.
          </p>
        ) : (
          <div className="space-y-3">
            {accounts.map((account) => (
              <div
                key={account.id}
                className={`flex items-start justify-between rounded-lg border p-4 ${
                  editingId === account.id ? 'hidden' : ''
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-medium">{account.bankName}</p>
                    <Badge variant="outline">
                      {ACCOUNT_TYPES.find((t) => t.value === account.accountType)?.label ||
                        account.accountType}
                    </Badge>
                    {account.isPrimary && <Badge>Primary</Badge>}
                  </div>
                  <p className="mt-1 text-sm text-gray-600">A/C: {account.accountNumber}</p>
                  <p className="text-sm text-gray-600">
                    IFSC: {account.ifscCode} | Branch: {account.branchName}
                  </p>
                  {account.accountHolderName && (
                    <p className="text-sm text-gray-500">Holder: {account.accountHolderName}</p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={account.isVerified ? 'default' : 'secondary'}>
                    {account.isVerified ? (
                      <>
                        <ShieldCheck className="mr-1 h-3 w-3" />
                        Verified
                      </>
                    ) : (
                      'Pending'
                    )}
                  </Badge>
                  <Button variant="ghost" size="sm" onClick={() => handleEdit(account)}>
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => handleDelete(account.id)}>
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
