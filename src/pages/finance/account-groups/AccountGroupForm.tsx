import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { ArrowLeft, Loader2, Save } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
import { accountGroupsApi, organizationsApi } from '@/services/api';
import type { AccountGroup, AccountGroupCreate, AccountGroupUpdate, Organization, PaginatedResponse } from '@/types';
import { ACCOUNT_NATURES, AccountNature } from '@/types';

export function AccountGroupForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [parentGroups, setParentGroups] = useState<AccountGroup[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<string>('');
  const [selectedNature, setSelectedNature] = useState<AccountNature | ''>('');

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<AccountGroupCreate | AccountGroupUpdate>();

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (isEdit && id) {
      fetchAccountGroup(id);
    }
  }, [id, isEdit]);

  useEffect(() => {
    if (selectedOrg && selectedNature) {
      fetchParentGroups();
    }
  }, [selectedOrg, selectedNature]);

  const fetchOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      const data: PaginatedResponse<Organization> = response.data;
      setOrganizations(data.items);
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
    }
  };

  const fetchParentGroups = async () => {
    if (!selectedOrg || !selectedNature) return;
    try {
      const response = await accountGroupsApi.list({
        organization_id: selectedOrg,
        nature: selectedNature,
        page_size: 100,
      });
      const data: PaginatedResponse<AccountGroup> = response.data;
      // Filter out current group if editing
      const filtered = isEdit ? data.items.filter((g) => g.id !== id) : data.items;
      setParentGroups(filtered);
    } catch (error) {
      console.error('Failed to fetch parent groups:', error);
    }
  };

  const fetchAccountGroup = async (groupId: string) => {
    try {
      setLoading(true);
      const response = await accountGroupsApi.get(groupId);
      const group: AccountGroup = response.data;
      setSelectedOrg(group.organization_id);
      setSelectedNature(group.nature);
      reset({
        code: group.code,
        name: group.name,
        nature: group.nature,
        parent_group_id: group.parent_group_id || '',
        sequence: group.sequence,
        description: group.description || '',
        organization_id: group.organization_id,
      });
    } catch (error) {
      console.error('Failed to fetch account group:', error);
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data: AccountGroupCreate | AccountGroupUpdate) => {
    try {
      setSubmitting(true);
      // Clean up empty parent_group_id
      const submitData = {
        ...data,
        parent_group_id: data.parent_group_id || null,
      };
      if (isEdit && id) {
        await accountGroupsApi.update(id, submitData);
      } else {
        await accountGroupsApi.create(submitData);
      }
      navigate('/admin/finance/account-groups');
    } catch (error) {
      console.error('Failed to save account group:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleOrgChange = (orgId: string) => {
    setSelectedOrg(orgId);
    setValue('organization_id', orgId);
    setValue('parent_group_id', '');
    setParentGroups([]);
  };

  const handleNatureChange = (nature: AccountNature) => {
    setSelectedNature(nature);
    setValue('nature', nature);
    setValue('parent_group_id', '');
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
        <Button variant="ghost" size="icon" onClick={() => navigate('/admin/finance/account-groups')}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            {isEdit ? 'Edit Account Group' : 'New Account Group'}
          </h1>
          <p className="text-sm text-slate-500">
            {isEdit ? 'Update account group details' : 'Create a new account group'}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Account Group Details</CardTitle>
            <CardDescription>Basic information about the account group</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="organization_id">Organization *</Label>
                <Select
                  value={selectedOrg}
                  onValueChange={handleOrgChange}
                  disabled={isEdit}
                >
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
                <Label htmlFor="nature">Account Nature *</Label>
                <Select
                  value={selectedNature}
                  onValueChange={handleNatureChange}
                  disabled={isEdit}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select nature" />
                  </SelectTrigger>
                  <SelectContent>
                    {ACCOUNT_NATURES.map((nature) => (
                      <SelectItem key={nature.value} value={nature.value}>
                        {nature.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="code">Group Code *</Label>
                <Input
                  id="code"
                  {...register('code', { required: 'Code is required' })}
                  placeholder="CURR_ASSETS"
                  disabled={isEdit}
                />
                {errors.code && (
                  <p className="text-sm text-red-500">{errors.code.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">Group Name *</Label>
                <Input
                  id="name"
                  {...register('name', { required: 'Name is required' })}
                  placeholder="Current Assets"
                />
                {errors.name && (
                  <p className="text-sm text-red-500">{errors.name.message}</p>
                )}
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="parent_group_id">Parent Group</Label>
                <Select
                  value={watch('parent_group_id') || 'none'}
                  onValueChange={(value) => setValue('parent_group_id', value === 'none' ? '' : value)}
                  disabled={!selectedOrg || !selectedNature}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select parent group (optional)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">No parent (Root level)</SelectItem>
                    {parentGroups.map((group) => (
                      <SelectItem key={group.id} value={group.id}>
                        {group.code} - {group.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="sequence">Sequence</Label>
                <Input
                  id="sequence"
                  type="number"
                  {...register('sequence', { valueAsNumber: true })}
                  placeholder="1"
                  defaultValue={1}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                {...register('description')}
                placeholder="Brief description of the account group"
                rows={3}
              />
            </div>
          </CardContent>
        </Card>

        <div className="flex items-center justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/admin/finance/account-groups')}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Save className="mr-2 h-4 w-4" />
            {isEdit ? 'Update Account Group' : 'Create Account Group'}
          </Button>
        </div>
      </form>
    </div>
  );
}
