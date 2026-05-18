import { ArrowLeft, Loader2, Save } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
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
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import { organizationsApi } from '@/services/api';
import { INDIAN_STATES, STATUS_OPTIONS } from '@/types';
import type { OrganizationCreate, OrganizationUpdate, Organization } from '@/types';

import { logger } from "@/lib/logger";
const CURRENCIES = [
  { value: 'INR', label: 'Indian Rupee (INR)' },
  { value: 'USD', label: 'US Dollar (USD)' },
  { value: 'EUR', label: 'Euro (EUR)' },
  { value: 'GBP', label: 'British Pound (GBP)' },
];

const MONTHS = [
  { value: 1, label: 'January' },
  { value: 2, label: 'February' },
  { value: 3, label: 'March' },
  { value: 4, label: 'April' },
  { value: 5, label: 'May' },
  { value: 6, label: 'June' },
  { value: 7, label: 'July' },
  { value: 8, label: 'August' },
  { value: 9, label: 'September' },
  { value: 10, label: 'October' },
  { value: 11, label: 'November' },
  { value: 12, label: 'December' },
];

export function OrganizationForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<OrganizationCreate | OrganizationUpdate>();

  useEffect(() => {
    if (isEdit && id) {
      fetchOrganization(id);
    }
  }, [id, isEdit]);

  const fetchOrganization = async (orgId: string) => {
    try {
      setLoading(true);
      const response = await organizationsApi.get(orgId);
      const org: Organization = response.data;
      reset({
        code: org.code,
        name: org.name,
        legal_name: org.legal_name,
        short_name: org.short_name || '',
        description: org.description || '',
        cin: org.cin || '',
        pan: org.pan,
        tan: org.tan || '',
        gstin: org.gstin || '',
        rbi_registration: org.rbi_registration || '',
        reg_address_line1: org.reg_address_line1 || '',
        reg_address_line2: org.reg_address_line2 || '',
        reg_city: org.reg_city || '',
        reg_district: org.reg_district || '',
        reg_state_code: org.reg_state_code || '',
        reg_pincode: org.reg_pincode || '',
        reg_country: org.reg_country || 'IN',
        phone: org.phone || '',
        email: org.email || '',
        website: org.website || '',
        base_currency: org.base_currency || 'INR',
        financial_year_start_month: org.financial_year_start_month || 4,
        logo_path: org.logo_path || '',
        primary_color: org.primary_color || '',
        status: org.status,
      });
    } catch (error) {
      logger.error('Failed to fetch organization:', error);
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data: OrganizationCreate | OrganizationUpdate) => {
    try {
      setSubmitting(true);
      if (isEdit && id) {
        await organizationsApi.update(id, data);
      } else {
        await organizationsApi.create(data);
      }
      navigate('/admin/organizations');
    } catch (error) {
      logger.error('Failed to save organization:', error);
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
        title={isEdit ? 'Edit Organization' : 'New Organization'}
        subtitle={isEdit ? 'Update organization details' : 'Create a new organization'}
        breadcrumbs={[
          { label: 'Organizations', to: '/admin/organizations' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
            <CardDescription>General organization details</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="code">Organization Code *</Label>
                <Input
                  id="code"
                  {...register('code', { required: 'Code is required' })}
                  placeholder="ORG001"
                  disabled={isEdit}
                />
                {errors.code && (
                  <p className="text-sm text-red-500">{errors.code.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">Organization Name *</Label>
                <Input
                  id="name"
                  {...register('name', { required: 'Name is required' })}
                  placeholder="SMFC Limited"
                />
                {errors.name && (
                  <p className="text-sm text-red-500">{errors.name.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="short_name">Short Name</Label>
                <Input id="short_name" {...register('short_name')} placeholder="SMFC" />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="legal_name">Legal Name *</Label>
                <Input
                  id="legal_name"
                  {...register('legal_name', { required: 'Legal name is required' })}
                  placeholder="SMFC Finance Private Limited"
                />
                {errors.legal_name && (
                  <p className="text-sm text-red-500">{errors.legal_name.message}</p>
                )}
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
                placeholder="Brief description of the organization"
                rows={3}
              />
            </div>
          </CardContent>
        </Card>

        {/* Statutory Information */}
        <Card>
          <CardHeader>
            <CardTitle>Statutory Information</CardTitle>
            <CardDescription>Registration and tax details</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="cin">CIN (Corporate Identity Number)</Label>
                <Input id="cin" {...register('cin')} placeholder="U65100MH2020PTC123456" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="pan">PAN *</Label>
                <Input
                  id="pan"
                  {...register('pan', { required: 'PAN is required' })}
                  placeholder="ABCDE1234F"
                />
                {errors.pan && (
                  <p className="text-sm text-red-500">{errors.pan.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="tan">TAN</Label>
                <Input id="tan" {...register('tan')} placeholder="MUMX12345E" />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="gstin">GSTIN</Label>
                <Input id="gstin" {...register('gstin')} placeholder="27ABCDE1234F1Z5" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="rbi_registration">RBI Registration Number</Label>
                <Input
                  id="rbi_registration"
                  {...register('rbi_registration')}
                  placeholder="N-13.00123"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Registered Address */}
        <Card>
          <CardHeader>
            <CardTitle>Registered Address</CardTitle>
            <CardDescription>Official registered address</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="reg_address_line1">Address Line 1</Label>
                <Input
                  id="reg_address_line1"
                  {...register('reg_address_line1')}
                  placeholder="Building name, Street"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="reg_address_line2">Address Line 2</Label>
                <Input
                  id="reg_address_line2"
                  {...register('reg_address_line2')}
                  placeholder="Area, Landmark"
                />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-4">
              <div className="space-y-2">
                <Label htmlFor="reg_city">City</Label>
                <Input id="reg_city" {...register('reg_city')} placeholder="Mumbai" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="reg_district">District</Label>
                <Input id="reg_district" {...register('reg_district')} placeholder="Mumbai Suburban" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="reg_state_code">State</Label>
                <Select
                  value={watch('reg_state_code') || ''}
                  onValueChange={(value) => setValue('reg_state_code', value)}
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
                <Label htmlFor="reg_pincode">Pincode</Label>
                <Input id="reg_pincode" {...register('reg_pincode')} placeholder="400001" />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="reg_country">Country</Label>
              <Input
                id="reg_country"
                {...register('reg_country')}
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
            <CardDescription>Organization contact details</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-3">
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
                  placeholder="info@smfc.com"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="website">Website</Label>
                <Input id="website" {...register('website')} placeholder="https://www.smfc.com" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Financial Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Financial Settings</CardTitle>
            <CardDescription>Currency and financial year configuration</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="base_currency">Base Currency</Label>
                <Select
                  value={watch('base_currency') || 'INR'}
                  onValueChange={(value) => setValue('base_currency', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select currency" />
                  </SelectTrigger>
                  <SelectContent>
                    {CURRENCIES.map((currency) => (
                      <SelectItem key={currency.value} value={currency.value}>
                        {currency.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="financial_year_start_month">Financial Year Start Month</Label>
                <Select
                  value={String(watch('financial_year_start_month') || 4)}
                  onValueChange={(value) => setValue('financial_year_start_month', parseInt(value))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select month" />
                  </SelectTrigger>
                  <SelectContent>
                    {MONTHS.map((month) => (
                      <SelectItem key={month.value} value={String(month.value)}>
                        {month.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Branding */}
        <Card>
          <CardHeader>
            <CardTitle>Branding</CardTitle>
            <CardDescription>Logo and color settings</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="logo_path">Logo URL</Label>
                <Input
                  id="logo_path"
                  {...register('logo_path')}
                  placeholder="https://cdn.smfc.com/logo.png"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="primary_color">Primary Color</Label>
                <div className="flex gap-2">
                  <Input
                    id="primary_color"
                    {...register('primary_color')}
                    placeholder="#2563eb"
                    className="flex-1"
                  />
                  <Input
                    type="color"
                    value={watch('primary_color') || '#2563eb'}
                    onChange={(e) => setValue('primary_color', e.target.value)}
                    className="h-10 w-14 cursor-pointer p-1"
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Form Actions */}
        <div className="flex items-center justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/admin/organizations')}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Save className="mr-2 h-4 w-4" />
            {isEdit ? 'Update Organization' : 'Create Organization'}
          </Button>
        </div>
      </form>
    </div>
  );
}
