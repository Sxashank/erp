import { Loader2, Save } from 'lucide-react';
import { useEffect, useState } from 'react';
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
import { organizationsApi } from '@/services/api';
import { INDIAN_STATES, STATUS_OPTIONS } from '@/types';
import { logger } from "@/lib/logger";
import type {
  Organization,
  OrganizationAddress,
  OrganizationAddressCreate,
  OrganizationAddressUpdate,
} from '@/types';

const ADDRESS_TYPES = [
  { value: 'REGISTERED', label: 'Registered Office' },
  { value: 'CORPORATE', label: 'Corporate Office' },
  { value: 'BRANCH', label: 'Branch Office' },
  { value: 'FACTORY', label: 'Factory/Plant' },
  { value: 'WAREHOUSE', label: 'Warehouse' },
  { value: 'OTHER', label: 'Other' },
];

export function OrganizationAddressForm() {
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
  } = useForm<OrganizationAddressCreate | OrganizationAddressUpdate>();

  useEffect(() => {
    if (orgId) {
      fetchOrganization();
    }
  }, [orgId]);

  useEffect(() => {
    if (isEdit && orgId && id) {
      fetchAddress();
    }
  }, [isEdit, orgId, id]);

  const fetchOrganization = async () => {
    if (!orgId) return;
    try {
      const response = await organizationsApi.get(orgId);
      setOrganization(response.data);
    } catch (error) {
      logger.error('Failed to fetch organization:', error);
    }
  };

  const fetchAddress = async () => {
    if (!orgId || !id) return;
    try {
      setLoading(true);
      const response = await organizationsApi.getAddress(orgId, id);
      const address: OrganizationAddress = response.data;
      reset({
        address_type: address.address_type,
        address_line1: address.address_line1,
        address_line2: address.address_line2 || '',
        landmark: address.landmark || '',
        city: address.city,
        district: address.district || '',
        state_code: address.state_code,
        pincode: address.pincode,
        country: address.country || 'IN',
        latitude: address.latitude,
        longitude: address.longitude,
        is_primary: address.is_primary,
        status: address.status,
      });
    } catch (error) {
      logger.error('Failed to fetch address:', error);
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data: OrganizationAddressCreate | OrganizationAddressUpdate) => {
    if (!orgId) return;
    try {
      setSubmitting(true);
      if (isEdit && id) {
        await organizationsApi.updateAddress(orgId, id, data);
      } else {
        await organizationsApi.createAddress(orgId, data);
      }
      navigate(`/admin/organizations/${orgId}/addresses`);
    } catch (error) {
      logger.error('Failed to save address:', error);
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
        title={isEdit ? 'Edit Address' : 'New Address'}
        subtitle={`${organization?.name ?? ''} - ${isEdit ? 'Update address details' : 'Add a new address'}`}
        breadcrumbs={[
          { label: 'Organizations', to: '/admin/organizations' },
          { label: organization?.name ?? '...', to: `/admin/organizations/${orgId}` },
          { label: 'Addresses', to: `/admin/organizations/${orgId}/addresses` },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Address Type */}
        <Card>
          <CardHeader>
            <CardTitle>Address Type</CardTitle>
            <CardDescription>Select the type of address</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="address_type">Address Type *</Label>
                <Select
                  value={watch('address_type') || ''}
                  onValueChange={(value) => setValue('address_type', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select address type" />
                  </SelectTrigger>
                  <SelectContent>
                    {ADDRESS_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {isEdit && (
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
              )}
            </div>
          </CardContent>
        </Card>

        {/* Address Details */}
        <Card>
          <CardHeader>
            <CardTitle>Address Details</CardTitle>
            <CardDescription>Street address and location details</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="space-y-2">
              <Label htmlFor="address_line1">Address Line 1 *</Label>
              <Input
                id="address_line1"
                {...register('address_line1', { required: 'Address line 1 is required' })}
                placeholder="Building name, Street number"
              />
              {errors.address_line1 && (
                <p className="text-sm text-red-500">{errors.address_line1.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="address_line2">Address Line 2</Label>
              <Input
                id="address_line2"
                {...register('address_line2')}
                placeholder="Area, Locality"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="landmark">Landmark</Label>
              <Input id="landmark" {...register('landmark')} placeholder="Near..." />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="city">City *</Label>
                <Input
                  id="city"
                  {...register('city', { required: 'City is required' })}
                  placeholder="Mumbai"
                />
                {errors.city && <p className="text-sm text-red-500">{errors.city.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="district">District</Label>
                <Input id="district" {...register('district')} placeholder="Mumbai Suburban" />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="state_code">State *</Label>
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
                <Label htmlFor="pincode">Pincode *</Label>
                <Input
                  id="pincode"
                  {...register('pincode', { required: 'Pincode is required' })}
                  placeholder="400001"
                />
                {errors.pincode && <p className="text-sm text-red-500">{errors.pincode.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="country">Country</Label>
                <Input id="country" {...register('country')} placeholder="IN" defaultValue="IN" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* GPS Coordinates (Optional) */}
        <Card>
          <CardHeader>
            <CardTitle>GPS Coordinates</CardTitle>
            <CardDescription>Optional location coordinates for mapping</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="latitude">Latitude</Label>
                <Input
                  id="latitude"
                  type="number"
                  step="0.0000001"
                  {...register('latitude', { valueAsNumber: true })}
                  placeholder="19.0760"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="longitude">Longitude</Label>
                <Input
                  id="longitude"
                  type="number"
                  step="0.0000001"
                  {...register('longitude', { valueAsNumber: true })}
                  placeholder="72.8777"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Primary Setting */}
        <Card>
          <CardHeader>
            <CardTitle>Settings</CardTitle>
            <CardDescription>Additional configuration</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_primary"
                checked={watch('is_primary') || false}
                onCheckedChange={(checked) => setValue('is_primary', checked as boolean)}
              />
              <Label htmlFor="is_primary">Primary Address</Label>
              <span className="text-sm text-slate-500">(Default address for correspondence)</span>
            </div>
          </CardContent>
        </Card>

        {/* Form Actions */}
        <div className="flex items-center justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate(`/admin/organizations/${orgId}/addresses`)}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Save className="mr-2 h-4 w-4" />
            {isEdit ? 'Update Address' : 'Create Address'}
          </Button>
        </div>
      </form>
    </div>
  );
}
