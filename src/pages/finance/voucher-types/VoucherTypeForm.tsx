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
import { voucherTypesApi, organizationsApi } from '@/services/api';
import type {
  VoucherType,
  VoucherTypeCreate,
  VoucherTypeUpdate,
  Organization,
  PaginatedResponse,
} from '@/types';
import { VOUCHER_CLASSES } from '@/types';

import { logger } from "@/lib/logger";
export function VoucherTypeForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [showApprovalLevels, setShowApprovalLevels] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<VoucherTypeCreate | VoucherTypeUpdate>();

  const requiresApproval = watch('requires_approval');

  useEffect(() => {
    setShowApprovalLevels(requiresApproval === true);
  }, [requiresApproval]);

  const fetchOrganizations = useCallback(async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      const data: PaginatedResponse<Organization> = response.data;
      setOrganizations(data.items);
    } catch (error) {
      logger.error('Failed to fetch organizations:', error);
    }
  }, []);

  const fetchVoucherType = useCallback(async (vtId: string) => {
    try {
      setLoading(true);
      const response = await voucherTypesApi.get(vtId);
      const vt: VoucherType = response.data;
      setShowApprovalLevels(vt.requires_approval);
      reset({
        code: vt.code,
        name: vt.name,
        voucher_class: vt.voucher_class,
        prefix: vt.prefix || '',
        auto_numbering: vt.auto_numbering,
        starting_number: vt.starting_number,
        number_format: vt.number_format || '',
        requires_approval: vt.requires_approval,
        approval_levels: vt.approval_levels,
        default_narration: vt.default_narration || '',
        description: vt.description || '',
        organization_id: vt.organization_id,
      });
    } catch (error) {
      logger.error('Failed to fetch voucher type:', error);
    } finally {
      setLoading(false);
    }
  }, [reset]);

  useEffect(() => {
    fetchOrganizations();
  }, [fetchOrganizations]);

  useEffect(() => {
    if (isEdit && id) {
      fetchVoucherType(id);
    }
  }, [fetchVoucherType, id, isEdit]);

  const onSubmit = async (data: VoucherTypeCreate | VoucherTypeUpdate) => {
    try {
      setSubmitting(true);
      // Set approval_levels to 0 if not required
      const submitData = {
        ...data,
        approval_levels: data.requires_approval ? data.approval_levels || 1 : 0,
      };
      if (isEdit && id) {
        await voucherTypesApi.update(id, submitData);
      } else {
        await voucherTypesApi.create(submitData);
      }
      navigate('/admin/finance/voucher-types');
    } catch (error) {
      logger.error('Failed to save voucher type:', error);
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
      <PageHeader
        title={isEdit ? 'Edit Voucher Type' : 'New Voucher Type'}
        subtitle={isEdit ? 'Update voucher type configuration' : 'Create a new voucher type'}
        breadcrumbs={[
          { label: 'Voucher Types', to: '/admin/finance/voucher-types' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
            <CardDescription>General voucher type details</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="organization_id">Organization *</Label>
                <Select
                  value={watch('organization_id') || ''}
                  onValueChange={(value) => setValue('organization_id', value)}
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
                <Label htmlFor="voucher_class">Voucher Class *</Label>
                <Select
                  value={watch('voucher_class') || ''}
                  onValueChange={(value) => setValue('voucher_class', value as VoucherTypeCreate['voucher_class'])}
                  disabled={isEdit}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select voucher class" />
                  </SelectTrigger>
                  <SelectContent>
                    {VOUCHER_CLASSES.map((vc) => (
                      <SelectItem key={vc.value} value={vc.value}>
                        {vc.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="code">Voucher Type Code *</Label>
                <Input
                  id="code"
                  {...register('code', { required: 'Code is required' })}
                  placeholder="JV"
                  disabled={isEdit}
                />
                {errors.code && <p className="text-sm text-red-500">{errors.code.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">Voucher Type Name *</Label>
                <Input
                  id="name"
                  {...register('name', { required: 'Name is required' })}
                  placeholder="Journal Voucher"
                />
                {errors.name && <p className="text-sm text-red-500">{errors.name.message}</p>}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                {...register('description')}
                placeholder="Brief description of the voucher type"
                rows={2}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Numbering Configuration</CardTitle>
            <CardDescription>Configure how voucher numbers are generated</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="auto_numbering"
                checked={watch('auto_numbering') || false}
                onCheckedChange={(checked) => setValue('auto_numbering', checked as boolean)}
              />
              <Label htmlFor="auto_numbering" className="cursor-pointer">
                Enable automatic numbering
              </Label>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="prefix">Prefix</Label>
                <Input id="prefix" {...register('prefix')} placeholder="JV-" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="starting_number">Starting Number</Label>
                <Input
                  id="starting_number"
                  type="number"
                  {...register('starting_number', { valueAsNumber: true })}
                  placeholder="1"
                  defaultValue={1}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="number_format">Number Format</Label>
                <Input
                  id="number_format"
                  {...register('number_format')}
                  placeholder="{PREFIX}{YYYY}-{MM}-{NNNN}"
                />
                <p className="text-xs text-slate-500">
                  Variables: {'{PREFIX}'}, {'{YYYY}'}, {'{YY}'}, {'{MM}'}, {'{NNNN}'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Approval Configuration</CardTitle>
            <CardDescription>Configure approval workflow for this voucher type</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="requires_approval"
                checked={watch('requires_approval') || false}
                onCheckedChange={(checked) => setValue('requires_approval', checked as boolean)}
              />
              <Label htmlFor="requires_approval" className="cursor-pointer">
                Requires approval before posting
              </Label>
            </div>

            {showApprovalLevels && (
              <div className="space-y-2">
                <Label htmlFor="approval_levels">Number of Approval Levels</Label>
                <Select
                  value={String(watch('approval_levels') || 1)}
                  onValueChange={(value) => setValue('approval_levels', parseInt(value))}
                >
                  <SelectTrigger className="w-[200px]">
                    <SelectValue placeholder="Select levels" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">1 Level</SelectItem>
                    <SelectItem value="2">2 Levels</SelectItem>
                    <SelectItem value="3">3 Levels</SelectItem>
                    <SelectItem value="4">4 Levels</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Default Settings</CardTitle>
            <CardDescription>Default values for new vouchers of this type</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="space-y-2">
              <Label htmlFor="default_narration">Default Narration</Label>
              <Textarea
                id="default_narration"
                {...register('default_narration')}
                placeholder="Enter default narration template..."
                rows={3}
              />
              <p className="text-xs text-slate-500">
                This will be pre-filled when creating new vouchers of this type.
              </p>
            </div>
          </CardContent>
        </Card>

        <div className="flex items-center justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/admin/finance/voucher-types')}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Save className="mr-2 h-4 w-4" />
            {isEdit ? 'Update Voucher Type' : 'Create Voucher Type'}
          </Button>
        </div>
      </form>
    </div>
  );
}
