import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { ArrowLeft, Loader2, Save } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { PageHeader } from '@/components/common/PageHeader';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { unitsApi, organizationsApi } from '@/services/api';
import { INDIAN_STATES, STATUS_OPTIONS, UNIT_TYPES } from '@/types';
import type { UnitCreate, UnitUpdate, Unit, Organization } from '@/types';

export function UnitForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [parentUnits, setParentUnits] = useState<Unit[]>([]);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<UnitCreate | UnitUpdate>();

  const selectedOrgId = watch('organization_id');
  const isSeparateAccounting = watch('is_separate_accounting');
  const isHeadOffice = watch('is_head_office');

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrgId) {
      fetchParentUnits(selectedOrgId);
    }
  }, [selectedOrgId]);

  useEffect(() => {
    if (isEdit && id) {
      fetchUnit(id);
    }
  }, [id, isEdit]);

  const fetchOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      setOrganizations(response.data.items);
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
    }
  };

  const fetchParentUnits = async (orgId: string) => {
    try {
      const response = await unitsApi.list({ organization_id: orgId, page_size: 100 });
      setParentUnits(response.data.items.filter((u: Unit) => u.id !== id));
    } catch (error) {
      console.error('Failed to fetch parent units:', error);
    }
  };

  const fetchUnit = async (unitId: string) => {
    try {
      setLoading(true);
      const response = await unitsApi.get(unitId);
      const unit: Unit = response.data;
      reset({
        code: unit.code,
        name: unit.name,
        short_name: unit.short_name || '',
        description: unit.description || '',
        unit_type: unit.unit_type,
        organization_id: unit.organization_id,
        parent_unit_id: unit.parent_unit_id || '',
        is_separate_accounting: unit.is_separate_accounting,
        gstin: unit.gstin || '',
        gst_state_code: unit.gst_state_code || '',
        address_line1: unit.address_line1 || '',
        address_line2: unit.address_line2 || '',
        city: unit.city || '',
        district: unit.district || '',
        state_code: unit.state_code || '',
        pincode: unit.pincode || '',
        country: unit.country || 'IN',
        phone: unit.phone || '',
        email: unit.email || '',
        manager_name: unit.manager_name || '',
        is_head_office: unit.is_head_office,
        status: unit.status,
      });
    } catch (error) {
      console.error('Failed to fetch unit:', error);
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data: UnitCreate | UnitUpdate) => {
    try {
      setSubmitting(true);
      // Clean up empty strings
      const cleanData = {
        ...data,
        parent_unit_id: data.parent_unit_id || undefined,
      };
      if (isEdit && id) {
        await unitsApi.update(id, cleanData);
      } else {
        await unitsApi.create(cleanData);
      }
      navigate('/admin/units');
    } catch (error) {
      console.error('Failed to save unit:', error);
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
        title={isEdit ? 'Edit Unit' : 'New Unit'}
        subtitle={isEdit ? 'Update unit details' : 'Create a new unit or branch'}
        breadcrumbs={[
          { label: 'Units', to: '/admin/units' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
            <CardDescription>General unit details</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="code">Unit Code *</Label>
                <Input
                  id="code"
                  {...register('code', { required: 'Code is required' })}
                  placeholder="UNIT001"
                  disabled={isEdit}
                />
                {errors.code && (
                  <p className="text-sm text-red-500">{errors.code.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">Unit Name *</Label>
                <Input
                  id="name"
                  {...register('name', { required: 'Name is required' })}
                  placeholder="Head Office"
                />
                {errors.name && (
                  <p className="text-sm text-red-500">{errors.name.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="short_name">Short Name</Label>
                <Input id="short_name" {...register('short_name')} placeholder="HO" />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
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
                <Label htmlFor="unit_type">Unit Type</Label>
                <Select
                  value={watch('unit_type') || 'BRANCH'}
                  onValueChange={(value) => setValue('unit_type', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    {UNIT_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="parent_unit_id">Parent Unit</Label>
                <Select
                  value={watch('parent_unit_id') || '__none__'}
                  onValueChange={(value) => setValue('parent_unit_id', value === '__none__' ? '' : value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select parent unit" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">None (Top Level)</SelectItem>
                    {parentUnits.map((unit) => (
                      <SelectItem key={unit.id} value={unit.id}>
                        {unit.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="manager_name">Manager Name</Label>
                <Input
                  id="manager_name"
                  {...register('manager_name')}
                  placeholder="John Doe"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="status">Status</Label>
                <Select
                  value={watch('status') || 'ACTIVE'}
                  onValueChange={(value) => setValue('status', value)}
                >
                  <SelectTrigger>
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
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                {...register('description')}
                placeholder="Brief description of the unit"
                rows={3}
              />
            </div>

            <div className="flex flex-wrap gap-6">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_head_office"
                  checked={isHeadOffice}
                  onCheckedChange={(checked) => setValue('is_head_office', checked as boolean)}
                />
                <Label htmlFor="is_head_office">Head Office</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_separate_accounting"
                  checked={isSeparateAccounting}
                  onCheckedChange={(checked) => setValue('is_separate_accounting', checked as boolean)}
                />
                <Label htmlFor="is_separate_accounting">Separate Accounting Unit</Label>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* GST Information */}
        <Card>
          <CardHeader>
            <CardTitle>GST Information</CardTitle>
            <CardDescription>Unit GST registration details</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="gstin">GSTIN</Label>
                <Input id="gstin" {...register('gstin')} placeholder="27ABCDE1234F1Z5" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="gst_state_code">GST State Code</Label>
                <Select
                  value={watch('gst_state_code') || ''}
                  onValueChange={(value) => setValue('gst_state_code', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select state" />
                  </SelectTrigger>
                  <SelectContent>
                    {INDIAN_STATES.map((state) => (
                      <SelectItem key={state.code} value={state.code}>
                        {state.code} - {state.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Address */}
        <Card>
          <CardHeader>
            <CardTitle>Address</CardTitle>
            <CardDescription>Unit location details</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="address_line1">Address Line 1</Label>
                <Input
                  id="address_line1"
                  {...register('address_line1')}
                  placeholder="Building name, Street"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="address_line2">Address Line 2</Label>
                <Input
                  id="address_line2"
                  {...register('address_line2')}
                  placeholder="Area, Landmark"
                />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-4">
              <div className="space-y-2">
                <Label htmlFor="city">City</Label>
                <Input id="city" {...register('city')} placeholder="Mumbai" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="district">District</Label>
                <Input id="district" {...register('district')} placeholder="Mumbai Suburban" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="state_code">State</Label>
                <Select
                  value={watch('state_code') || ''}
                  onValueChange={(value) => setValue('state_code', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select state" />
                  </SelectTrigger>
                  <SelectContent>
                    {INDIAN_STATES.map((state) => (
                      <SelectItem key={state.code} value={state.code}>
                        {state.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="pincode">Pincode</Label>
                <Input id="pincode" {...register('pincode')} placeholder="400001" />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="country">Country</Label>
              <Input
                id="country"
                {...register('country')}
                placeholder="IN"
                defaultValue="IN"
              />
            </div>
          </CardContent>
        </Card>

        {/* Contact Information */}
        <Card>
          <CardHeader>
            <CardTitle>Contact Information</CardTitle>
            <CardDescription>Unit contact details</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="phone">Phone</Label>
                <Input id="phone" {...register('phone')} placeholder="+91 22 12345678" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  {...register('email')}
                  placeholder="branch@smfc.com"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Form Actions */}
        <div className="flex items-center justify-end gap-4">
          <Button type="button" variant="outline" onClick={() => navigate('/admin/units')}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Save className="mr-2 h-4 w-4" />
            {isEdit ? 'Update Unit' : 'Create Unit'}
          </Button>
        </div>
      </form>
    </div>
  );
}
