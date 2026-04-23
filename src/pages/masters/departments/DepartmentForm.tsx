import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { ArrowLeft, Loader2, Save } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
import { departmentsApi, organizationsApi } from '@/services/api';
import { STATUS_OPTIONS } from '@/types';
import type { DepartmentCreate, DepartmentUpdate, Department, Organization } from '@/types';

export function DepartmentForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [parentDepartments, setParentDepartments] = useState<Department[]>([]);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<DepartmentCreate | DepartmentUpdate>();

  const selectedOrgId = watch('organization_id');

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrgId) {
      fetchParentDepartments(selectedOrgId);
    }
  }, [selectedOrgId]);

  useEffect(() => {
    if (isEdit && id) {
      fetchDepartment(id);
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

  const fetchParentDepartments = async (orgId: string) => {
    try {
      const response = await departmentsApi.list({ organization_id: orgId, page_size: 100 });
      setParentDepartments(response.data.items.filter((d: Department) => d.id !== id));
    } catch (error) {
      console.error('Failed to fetch parent departments:', error);
    }
  };

  const fetchDepartment = async (deptId: string) => {
    try {
      setLoading(true);
      const response = await departmentsApi.get(deptId);
      const dept: Department = response.data;
      reset({
        code: dept.code,
        name: dept.name,
        short_name: dept.short_name || '',
        description: dept.description || '',
        organization_id: dept.organization_id,
        parent_dept_id: dept.parent_dept_id || '',
        cost_center_code: dept.cost_center_code || '',
        head_name: dept.head_name || '',
        email: dept.email || '',
        phone: dept.phone || '',
        status: dept.status,
      });
    } catch (error) {
      console.error('Failed to fetch department:', error);
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data: DepartmentCreate | DepartmentUpdate) => {
    try {
      setSubmitting(true);
      const cleanData = {
        ...data,
        parent_dept_id: data.parent_dept_id || undefined,
      };
      if (isEdit && id) {
        await departmentsApi.update(id, cleanData);
      } else {
        await departmentsApi.create(cleanData);
      }
      navigate('/admin/departments');
    } catch (error) {
      console.error('Failed to save department:', error);
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
        title={isEdit ? 'Edit Department' : 'New Department'}
        subtitle={isEdit ? 'Update department details' : 'Create a new department'}
        breadcrumbs={[
          { label: 'Departments', to: '/admin/departments' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
            <CardDescription>General department details</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="code">Department Code *</Label>
                <Input
                  id="code"
                  {...register('code', { required: 'Code is required' })}
                  placeholder="DEPT001"
                  disabled={isEdit}
                />
                {errors.code && (
                  <p className="text-sm text-red-500">{errors.code.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">Department Name *</Label>
                <Input
                  id="name"
                  {...register('name', { required: 'Name is required' })}
                  placeholder="Finance"
                />
                {errors.name && (
                  <p className="text-sm text-red-500">{errors.name.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="short_name">Short Name</Label>
                <Input id="short_name" {...register('short_name')} placeholder="FIN" />
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
                <Label htmlFor="parent_dept_id">Parent Department</Label>
                <Select
                  value={watch('parent_dept_id') || '__none__'}
                  onValueChange={(value) => setValue('parent_dept_id', value === '__none__' ? '' : value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select parent department" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">None (Top Level)</SelectItem>
                    {parentDepartments.map((dept) => (
                      <SelectItem key={dept.id} value={dept.id}>
                        {dept.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
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
                placeholder="Brief description of the department"
                rows={3}
              />
            </div>
          </CardContent>
        </Card>

        {/* Additional Information */}
        <Card>
          <CardHeader>
            <CardTitle>Additional Information</CardTitle>
            <CardDescription>Cost center and management details</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="cost_center_code">Cost Center Code</Label>
                <Input
                  id="cost_center_code"
                  {...register('cost_center_code')}
                  placeholder="CC001"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="head_name">Department Head</Label>
                <Input
                  id="head_name"
                  {...register('head_name')}
                  placeholder="John Doe"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Contact Information */}
        <Card>
          <CardHeader>
            <CardTitle>Contact Information</CardTitle>
            <CardDescription>Department contact details</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  {...register('email')}
                  placeholder="finance@smfc.com"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Phone</Label>
                <Input id="phone" {...register('phone')} placeholder="+91 22 12345678" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Form Actions */}
        <div className="flex items-center justify-end gap-4">
          <Button type="button" variant="outline" onClick={() => navigate('/admin/departments')}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Save className="mr-2 h-4 w-4" />
            {isEdit ? 'Update Department' : 'Create Department'}
          </Button>
        </div>
      </form>
    </div>
  );
}
