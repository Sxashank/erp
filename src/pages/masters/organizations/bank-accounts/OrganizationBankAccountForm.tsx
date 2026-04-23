import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { ArrowLeft, Loader2, Save } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
import { organizationsApi } from '@/services/api';
import { STATUS_OPTIONS } from '@/types';
import type {
  Organization,
  OrganizationBankAccount,
  OrganizationBankAccountCreate,
  OrganizationBankAccountUpdate,
} from '@/types';

const ACCOUNT_TYPES = [
  { value: 'CURRENT', label: 'Current Account' },
  { value: 'SAVINGS', label: 'Savings Account' },
  { value: 'OD', label: 'Overdraft' },
  { value: 'CC', label: 'Cash Credit' },
  { value: 'FIXED_DEPOSIT', label: 'Fixed Deposit' },
];

export function OrganizationBankAccountForm() {
  const { orgId, id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [organization, setOrganization] = useState<Organization | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<OrganizationBankAccountCreate | OrganizationBankAccountUpdate>();

  useEffect(() => {
    if (orgId) {
      fetchOrganization();
    }
  }, [orgId]);

  useEffect(() => {
    if (isEdit && orgId && id) {
      fetchBankAccount();
    }
  }, [isEdit, orgId, id]);

  const fetchOrganization = async () => {
    if (!orgId) return;
    try {
      const response = await organizationsApi.get(orgId);
      setOrganization(response.data);
    } catch (error) {
      console.error('Failed to fetch organization:', error);
    }
  };

  const fetchBankAccount = async () => {
    if (!orgId || !id) return;
    try {
      setLoading(true);
      const response = await organizationsApi.getBankAccount(orgId, id);
      const account: OrganizationBankAccount = response.data;
      reset({
        account_name: account.account_name,
        account_number: account.account_number,
        ifsc_code: account.ifsc_code,
        bank_name: account.bank_name,
        branch_name: account.branch_name || '',
        account_type: account.account_type,
        sanctioned_limit: account.sanctioned_limit,
        drawing_power: account.drawing_power,
        is_primary: account.is_primary,
        allow_payments: account.allow_payments,
        allow_receipts: account.allow_receipts,
        status: account.status,
      });
    } catch (error) {
      console.error('Failed to fetch bank account:', error);
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data: OrganizationBankAccountCreate | OrganizationBankAccountUpdate) => {
    if (!orgId) return;
    try {
      setSubmitting(true);
      if (isEdit && id) {
        await organizationsApi.updateBankAccount(orgId, id, data);
      } else {
        await organizationsApi.createBankAccount(orgId, data);
      }
      navigate(`/admin/organizations/${orgId}/bank-accounts`);
    } catch (error) {
      console.error('Failed to save bank account:', error);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate(`/admin/organizations/${orgId}/bank-accounts`)}
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            {isEdit ? 'Edit Bank Account' : 'New Bank Account'}
          </h1>
          <p className="text-sm text-slate-500">
            {organization?.name} - {isEdit ? 'Update bank account details' : 'Add a new bank account'}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Account Details */}
        <Card>
          <CardHeader>
            <CardTitle>Account Details</CardTitle>
            <CardDescription>Basic bank account information</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="account_name">Account Name *</Label>
                <Input
                  id="account_name"
                  {...register('account_name', { required: 'Account name is required' })}
                  placeholder="Main Current Account"
                />
                {errors.account_name && (
                  <p className="text-sm text-red-500">{errors.account_name.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="account_type">Account Type *</Label>
                <Select
                  value={watch('account_type') || ''}
                  onValueChange={(value) => setValue('account_type', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select account type" />
                  </SelectTrigger>
                  <SelectContent>
                    {ACCOUNT_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="account_number">Account Number *</Label>
                <Input
                  id="account_number"
                  {...register('account_number', { required: 'Account number is required' })}
                  placeholder="1234567890123456"
                  disabled={isEdit}
                />
                {errors.account_number && (
                  <p className="text-sm text-red-500">{errors.account_number.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="ifsc_code">IFSC Code *</Label>
                <Input
                  id="ifsc_code"
                  {...register('ifsc_code', { required: 'IFSC code is required' })}
                  placeholder="HDFC0001234"
                  className="uppercase"
                  disabled={isEdit}
                />
                {errors.ifsc_code && (
                  <p className="text-sm text-red-500">{errors.ifsc_code.message}</p>
                )}
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="bank_name">Bank Name *</Label>
                <Input
                  id="bank_name"
                  {...register('bank_name', { required: 'Bank name is required' })}
                  placeholder="HDFC Bank"
                  disabled={isEdit}
                />
                {errors.bank_name && (
                  <p className="text-sm text-red-500">{errors.bank_name.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="branch_name">Branch Name</Label>
                <Input
                  id="branch_name"
                  {...register('branch_name')}
                  placeholder="Mumbai Main Branch"
                />
              </div>
            </div>

            {isEdit && (
              <div className="space-y-2">
                <Label htmlFor="status">Status</Label>
                <Select
                  value={watch('status') || 'ACTIVE'}
                  onValueChange={(value) => setValue('status', value)}
                >
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="Select status" />
                  </SelectTrigger>
                  <SelectContent>
                    {STATUS_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Credit Limits (for OD/CC accounts) */}
        {(watch('account_type') === 'OD' || watch('account_type') === 'CC') && (
          <Card>
            <CardHeader>
              <CardTitle>Credit Limits</CardTitle>
              <CardDescription>Overdraft/Cash Credit limits</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="sanctioned_limit">Sanctioned Limit</Label>
                  <Input
                    id="sanctioned_limit"
                    type="number"
                    step="0.01"
                    {...register('sanctioned_limit', { valueAsNumber: true })}
                    placeholder="1000000.00"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="drawing_power">Drawing Power</Label>
                  <Input
                    id="drawing_power"
                    type="number"
                    step="0.01"
                    {...register('drawing_power', { valueAsNumber: true })}
                    placeholder="800000.00"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Usage Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Usage Settings</CardTitle>
            <CardDescription>Configure how this account can be used</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_primary"
                checked={watch('is_primary') || false}
                onCheckedChange={(checked) => setValue('is_primary', checked as boolean)}
              />
              <Label htmlFor="is_primary">Primary Account</Label>
              <span className="text-sm text-slate-500">
                (Default account for payments and receipts)
              </span>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="allow_payments"
                checked={watch('allow_payments') !== false}
                onCheckedChange={(checked) => setValue('allow_payments', checked as boolean)}
              />
              <Label htmlFor="allow_payments">Allow Payments</Label>
              <span className="text-sm text-slate-500">(Use this account for outgoing payments)</span>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="allow_receipts"
                checked={watch('allow_receipts') !== false}
                onCheckedChange={(checked) => setValue('allow_receipts', checked as boolean)}
              />
              <Label htmlFor="allow_receipts">Allow Receipts</Label>
              <span className="text-sm text-slate-500">(Use this account for incoming receipts)</span>
            </div>
          </CardContent>
        </Card>

        {/* Form Actions */}
        <div className="flex items-center justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate(`/admin/organizations/${orgId}/bank-accounts`)}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Save className="mr-2 h-4 w-4" />
            {isEdit ? 'Update Bank Account' : 'Create Bank Account'}
          </Button>
        </div>
      </form>
    </div>
  );
}
