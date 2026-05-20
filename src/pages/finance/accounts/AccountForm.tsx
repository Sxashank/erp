import { Loader2, Save } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
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
import { Textarea } from '@/components/ui/textarea';
import { accountsApi, accountGroupsApi, organizationsApi } from '@/services/api';
import type {
  Account,
  AccountCreate,
  AccountUpdate,
  AccountGroup,
  Organization,
  PaginatedResponse,
} from '@/types';
import { ACCOUNT_TYPES, BALANCE_TYPES } from '@/types';

import { logger } from "@/lib/logger";
export function AccountForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [accountGroups, setAccountGroups] = useState<AccountGroup[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<string>('');
  const [showBankFields, setShowBankFields] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<AccountCreate | AccountUpdate>();

  const accountType = watch('account_type');

  useEffect(() => {
    setShowBankFields(accountType === 'BANK');
  }, [accountType]);

  const fetchOrganizations = useCallback(async () => {
    try {
      const response = await organizationsApi.list({ pageSize: 100 });
      const data: PaginatedResponse<Organization> = response.data;
      setOrganizations(data.items);
    } catch (error) {
      logger.error('Failed to fetch organizations:', error);
    }
  }, []);

  const fetchAccountGroups = useCallback(async () => {
    if (!selectedOrg) return;
    try {
      const response = await accountGroupsApi.list({
        pageSize: 100,
      });
      const data: PaginatedResponse<AccountGroup> = response.data;
      setAccountGroups(data.items);
    } catch (error) {
      logger.error('Failed to fetch account groups:', error);
    }
  }, [selectedOrg]);

  const fetchAccount = useCallback(async (accountId: string) => {
    try {
      setLoading(true);
      const response = await accountsApi.get(accountId);
      const account: Account = response.data;
      setSelectedOrg(account.organization_id);
      setShowBankFields(account.account_type === 'BANK');
      reset({
        code: account.code,
        name: account.name,
        account_group_id: account.account_group_id,
        account_type: account.account_type,
        description: account.description || '',
        is_control_account: account.is_control_account,
        control_type: account.control_type || '',
        currency_code: account.currency_code || 'INR',
        opening_balance: account.opening_balance,
        opening_balance_type: account.opening_balance_type,
        bank_name: account.bank_name || '',
        bank_branch: account.bank_branch || '',
        bank_account_number: account.bank_account_number || '',
        bank_ifsc: account.bank_ifsc || '',
        tds_applicable: account.tds_applicable,
        tds_section_code: account.tds_section_code || '',
        gst_applicable: account.gst_applicable,
        hsn_sac_code: account.hsn_sac_code || '',
        organization_id: account.organization_id,
      });
    } catch (error) {
      logger.error('Failed to fetch account:', error);
    } finally {
      setLoading(false);
    }
  }, [reset]);

  useEffect(() => {
    fetchOrganizations();
  }, [fetchOrganizations]);

  useEffect(() => {
    if (isEdit && id) {
      fetchAccount(id);
    }
  }, [fetchAccount, id, isEdit]);

  useEffect(() => {
    if (selectedOrg) {
      fetchAccountGroups();
    }
  }, [fetchAccountGroups, selectedOrg]);

  const onSubmit = async (data: AccountCreate | AccountUpdate) => {
    try {
      setSubmitting(true);
      if (isEdit && id) {
        await accountsApi.update(id, data);
      } else {
        await accountsApi.create(data);
      }
      navigate('/admin/finance/accounts');
    } catch (error) {
      logger.error('Failed to save account:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleOrgChange = (orgId: string) => {
    setSelectedOrg(orgId);
    setValue('organization_id', orgId);
    setValue('account_group_id', '');
    setAccountGroups([]);
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
      <PageHeader
        title={isEdit ? 'Edit Account' : 'New Account'}
        subtitle={isEdit ? 'Update account details' : 'Create a new ledger account'}
        breadcrumbs={[
          { label: 'Accounts', to: '/admin/finance/accounts' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Account Details</CardTitle>
            <CardDescription>Basic information about the account</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="organization_id">Organization *</Label>
                <Select value={selectedOrg} onValueChange={handleOrgChange} disabled={isEdit}>
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
              </div>
              <div className="space-y-2">
                <Label htmlFor="account_group_id">Account Group *</Label>
                <Select
                  value={watch('account_group_id') || ''}
                  onValueChange={(value) => setValue('account_group_id', value)}
                  disabled={!selectedOrg}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select account group" />
                  </SelectTrigger>
                  <SelectContent>
                    {accountGroups.map((group) => (
                      <SelectItem key={group.id} value={group.id}>
                        {group.code} - {group.name} ({group.nature})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="code">Account Code *</Label>
                <Input
                  id="code"
                  {...register('code', { required: 'Code is required' })}
                  placeholder="1001"
                  disabled={isEdit}
                />
                {errors.code && <p className="text-sm text-red-500">{errors.code.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">Account Name *</Label>
                <Input
                  id="name"
                  {...register('name', { required: 'Name is required' })}
                  placeholder="Cash in Hand"
                />
                {errors.name && <p className="text-sm text-red-500">{errors.name.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="account_type">Account Type *</Label>
                <Select
                  value={watch('account_type') || 'LEDGER'}
                  onValueChange={(value) => setValue('account_type', value as AccountCreate['account_type'])}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
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

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                {...register('description')}
                placeholder="Brief description of the account"
                rows={2}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Opening Balance</CardTitle>
            <CardDescription>Initial balance for this account</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="currency_code">Currency</Label>
                <Select
                  value={watch('currency_code') || 'INR'}
                  onValueChange={(value) => setValue('currency_code', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select currency" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="INR">INR - Indian Rupee</SelectItem>
                    <SelectItem value="USD">USD - US Dollar</SelectItem>
                    <SelectItem value="EUR">EUR - Euro</SelectItem>
                    <SelectItem value="GBP">GBP - British Pound</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="opening_balance">Opening Balance</Label>
                <Input
                  id="opening_balance"
                  type="number"
                  step="0.01"
                  {...register('opening_balance', { valueAsNumber: true })}
                  placeholder="0.00"
                  defaultValue={0}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="opening_balance_type">Balance Type</Label>
                <Select
                  value={watch('opening_balance_type') || 'DR'}
                  onValueChange={(value) =>
                    setValue('opening_balance_type', value as AccountCreate['opening_balance_type'])
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    {BALANCE_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {showBankFields && (
          <Card>
            <CardHeader>
              <CardTitle>Bank Details</CardTitle>
              <CardDescription>Bank account information</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="bank_name">Bank Name</Label>
                  <Input
                    id="bank_name"
                    {...register('bank_name')}
                    placeholder="State Bank of India"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="bank_branch">Branch</Label>
                  <Input id="bank_branch" {...register('bank_branch')} placeholder="Main Branch" />
                </div>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="bank_account_number">Account Number</Label>
                  <Input
                    id="bank_account_number"
                    {...register('bank_account_number')}
                    placeholder="1234567890"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="bank_ifsc">IFSC Code</Label>
                  <Input id="bank_ifsc" {...register('bank_ifsc')} placeholder="SBIN0001234" />
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Tax Settings</CardTitle>
            <CardDescription>TDS and GST configuration</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="tds_applicable"
                    checked={watch('tds_applicable') || false}
                    onCheckedChange={(checked) => setValue('tds_applicable', checked as boolean)}
                  />
                  <Label htmlFor="tds_applicable" className="cursor-pointer">
                    TDS Applicable
                  </Label>
                </div>
                {watch('tds_applicable') && (
                  <div className="space-y-2">
                    <Label htmlFor="tds_section_code">TDS Section</Label>
                    <Input
                      id="tds_section_code"
                      {...register('tds_section_code')}
                      placeholder="194C"
                    />
                  </div>
                )}
              </div>
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="gst_applicable"
                    checked={watch('gst_applicable') || false}
                    onCheckedChange={(checked) => setValue('gst_applicable', checked as boolean)}
                  />
                  <Label htmlFor="gst_applicable" className="cursor-pointer">
                    GST Applicable
                  </Label>
                </div>
                {watch('gst_applicable') && (
                  <div className="space-y-2">
                    <Label htmlFor="hsn_sac_code">HSN/SAC Code</Label>
                    <Input id="hsn_sac_code" {...register('hsn_sac_code')} placeholder="998314" />
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="flex items-center justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/admin/finance/accounts')}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Save className="mr-2 h-4 w-4" />
            {isEdit ? 'Update Account' : 'Create Account'}
          </Button>
        </div>
      </form>
    </div>
  );
}
