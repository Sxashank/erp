import { ArrowLeft, Loader2, Save } from 'lucide-react';
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
import { usersApi, organizationsApi, unitsApi, rolesApi } from '@/services/api';
import type { UserCreate, UserUpdate, User, Organization, Unit, RoleListItem } from '@/types';

import { logger } from "@/lib/logger";
const USER_STATUS_OPTIONS = [
  { value: 'ACTIVE', label: 'Active' },
  { value: 'INACTIVE', label: 'Inactive' },
  { value: 'LOCKED', label: 'Locked' },
  { value: 'PASSWORD_EXPIRED', label: 'Password Expired' },
];

const TIMEZONES = [
  { value: 'Asia/Kolkata', label: 'India (IST)' },
  { value: 'UTC', label: 'UTC' },
  { value: 'America/New_York', label: 'Eastern Time (ET)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
  { value: 'Europe/London', label: 'London (GMT)' },
  { value: 'Asia/Singapore', label: 'Singapore (SGT)' },
];

export function UserForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [roles, setRoles] = useState<RoleListItem[]>([]);
  const [selectedRoles, setSelectedRoles] = useState<string[]>([]);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<UserCreate | UserUpdate>();

  const selectedOrgId = watch('organization_id');
  const mfaEnabled = watch('mfa_enabled');

  useEffect(() => {
    fetchOrganizations();
    fetchRoles();
  }, []);

  useEffect(() => {
    if (selectedOrgId) {
      fetchUnits(selectedOrgId);
    }
  }, [selectedOrgId]);

  useEffect(() => {
    if (isEdit && id) {
      fetchUser(id);
    }
  }, [id, isEdit]);

  const fetchOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      setOrganizations(response.data.items);
    } catch (error) {
      logger.error('Failed to fetch organizations:', error);
    }
  };

  const fetchUnits = async (orgId: string) => {
    try {
      const response = await unitsApi.list({ organization_id: orgId, page_size: 100 });
      setUnits(response.data.items);
    } catch (error) {
      logger.error('Failed to fetch units:', error);
    }
  };

  const fetchRoles = async () => {
    try {
      const response = await rolesApi.list();
      setRoles(response.data);
    } catch (error) {
      logger.error('Failed to fetch roles:', error);
    }
  };

  const fetchUser = async (userId: string) => {
    try {
      setLoading(true);
      const response = await usersApi.get(userId);
      const user: User = response.data;
      reset({
        username: user.username,
        email: user.email,
        full_name: user.full_name,
        employee_code: user.employee_code || '',
        phone: user.phone || '',
        timezone: user.timezone || 'Asia/Kolkata',
        organization_id: user.organization_id || '',
        default_unit_id: user.default_unit_id || '',
        mfa_enabled: user.mfa_enabled,
        status: user.status,
      });
      setSelectedRoles(user.roles.map((r) => r.id));
    } catch (error) {
      logger.error('Failed to fetch user:', error);
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data: UserCreate | UserUpdate) => {
    try {
      setSubmitting(true);
      const cleanData = {
        ...data,
        organization_id: data.organization_id || undefined,
        default_unit_id: data.default_unit_id || undefined,
        role_ids: selectedRoles.length > 0 ? selectedRoles : undefined,
      };
      if (isEdit && id) {
        await usersApi.update(id, cleanData);
      } else {
        await usersApi.create(cleanData as UserCreate);
      }
      navigate('/admin/users');
    } catch (error) {
      logger.error('Failed to save user:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const toggleRole = (roleId: string) => {
    setSelectedRoles((prev) =>
      prev.includes(roleId) ? prev.filter((id) => id !== roleId) : [...prev, roleId]
    );
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
        title={isEdit ? 'Edit User' : 'New User'}
        subtitle={isEdit ? 'Update user details' : 'Create a new user account'}
        breadcrumbs={[
          { label: 'Users', to: '/admin/users' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Account Information */}
        <Card>
          <CardHeader>
            <CardTitle>Account Information</CardTitle>
            <CardDescription>Login credentials and identity</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="username">Username *</Label>
                <Input
                  id="username"
                  {...register('username', { required: 'Username is required' })}
                  placeholder="john.doe"
                  disabled={isEdit}
                />
                {errors.username && (
                  <p className="text-sm text-red-500">{errors.username.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email *</Label>
                <Input
                  id="email"
                  type="email"
                  {...register('email', { required: 'Email is required' })}
                  placeholder="john.doe@smfc.com"
                />
                {errors.email && (
                  <p className="text-sm text-red-500">{errors.email.message}</p>
                )}
              </div>
            </div>

            {!isEdit && (
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="password">Password *</Label>
                  <Input
                    id="password"
                    type="password"
                    {...register('password', {
                      required: !isEdit ? 'Password is required' : false,
                      minLength: { value: 8, message: 'Password must be at least 8 characters' },
                    })}
                    placeholder="Enter password"
                  />
                  {errors.password && (
                    <p className="text-sm text-red-500">{errors.password.message}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirm_password">Confirm Password *</Label>
                  <Input
                    id="confirm_password"
                    type="password"
                    {...register('confirm_password', {
                      required: !isEdit ? 'Confirm password is required' : false,
                    })}
                    placeholder="Confirm password"
                  />
                  {errors.confirm_password && (
                    <p className="text-sm text-red-500">{errors.confirm_password.message}</p>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Personal Information */}
        <Card>
          <CardHeader>
            <CardTitle>Personal Information</CardTitle>
            <CardDescription>User profile details</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="full_name">Full Name *</Label>
                <Input
                  id="full_name"
                  {...register('full_name', { required: 'Full name is required' })}
                  placeholder="John Doe"
                />
                {errors.full_name && (
                  <p className="text-sm text-red-500">{errors.full_name.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="employee_code">Employee Code</Label>
                <Input
                  id="employee_code"
                  {...register('employee_code')}
                  placeholder="EMP001"
                />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="phone">Phone</Label>
                <Input
                  id="phone"
                  {...register('phone')}
                  placeholder="+91 98765 43210"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="timezone">Timezone</Label>
                <Select
                  value={watch('timezone') || 'Asia/Kolkata'}
                  onValueChange={(value) => setValue('timezone', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select timezone" />
                  </SelectTrigger>
                  <SelectContent>
                    {TIMEZONES.map((tz) => (
                      <SelectItem key={tz.value} value={tz.value}>
                        {tz.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Organization & Access */}
        <Card>
          <CardHeader>
            <CardTitle>Organization & Access</CardTitle>
            <CardDescription>Assign organization and default unit</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="organization_id">Organization</Label>
                <Select
                  value={watch('organization_id') || '__none__'}
                  onValueChange={(value) => setValue('organization_id', value === '__none__' ? '' : value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select organization" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">None</SelectItem>
                    {organizations.map((org) => (
                      <SelectItem key={org.id} value={org.id}>
                        {org.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="default_unit_id">Default Unit</Label>
                <Select
                  value={watch('default_unit_id') || '__none__'}
                  onValueChange={(value) => setValue('default_unit_id', value === '__none__' ? '' : value)}
                  disabled={!selectedOrgId}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select unit" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">None</SelectItem>
                    {units.map((unit) => (
                      <SelectItem key={unit.id} value={unit.id}>
                        {unit.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {isEdit && (
              <div className="space-y-2">
                <Label htmlFor="status">Status</Label>
                <Select
                  value={watch('status') || 'ACTIVE'}
                  onValueChange={(value) => setValue('status', value)}
                >
                  <SelectTrigger className="w-[200px]">
                    <SelectValue placeholder="Select status" />
                  </SelectTrigger>
                  <SelectContent>
                    {USER_STATUS_OPTIONS.map((option) => (
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

        {/* Security */}
        <Card>
          <CardHeader>
            <CardTitle>Security</CardTitle>
            <CardDescription>Authentication settings</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="mfa_enabled"
                checked={mfaEnabled}
                onCheckedChange={(checked) => setValue('mfa_enabled', checked as boolean)}
              />
              <Label htmlFor="mfa_enabled">Enable Multi-Factor Authentication (MFA)</Label>
            </div>
          </CardContent>
        </Card>

        {/* Roles */}
        <Card>
          <CardHeader>
            <CardTitle>Roles</CardTitle>
            <CardDescription>Assign roles to this user</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {roles.map((role) => (
                <div
                  key={role.id}
                  className={`flex cursor-pointer items-center space-x-3 rounded-lg border p-3 transition-colors ${
                    selectedRoles.includes(role.id)
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                  onClick={() => toggleRole(role.id)}
                >
                  <Checkbox
                    checked={selectedRoles.includes(role.id)}
                    onCheckedChange={() => toggleRole(role.id)}
                  />
                  <div>
                    <p className="text-sm font-medium">{role.name}</p>
                    <p className="text-xs text-slate-500">{role.code}</p>
                  </div>
                </div>
              ))}
            </div>
            {roles.length === 0 && (
              <p className="text-sm text-slate-500">No roles available</p>
            )}
          </CardContent>
        </Card>

        {/* Form Actions */}
        <div className="flex items-center justify-end gap-4">
          <Button type="button" variant="outline" onClick={() => navigate('/admin/users')}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Save className="mr-2 h-4 w-4" />
            {isEdit ? 'Update User' : 'Create User'}
          </Button>
        </div>
      </form>
    </div>
  );
}
