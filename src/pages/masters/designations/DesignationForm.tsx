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
import { Textarea } from '@/components/ui/textarea';
import { designationsApi, departmentsApi } from '@/services/api';
import { STATUS_OPTIONS } from '@/types';
import type { DesignationCreate, DesignationUpdate, Designation, Department } from '@/types';

import { logger } from "@/lib/logger";
export function DesignationForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [reportingDesignations, setReportingDesignations] = useState<Designation[]>([]);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<DesignationCreate | DesignationUpdate>();

  const selectedDeptId = watch('department_id');

  useEffect(() => {
    fetchDepartments();
    fetchReportingDesignations();
  }, []);

  useEffect(() => {
    if (isEdit && id) {
      fetchDesignation(id);
    }
  }, [id, isEdit]);

  const fetchDepartments = async () => {
    try {
      const response = await departmentsApi.list({ page_size: 100 });
      setDepartments(response.data.items);
    } catch (error) {
      logger.error('Failed to fetch departments:', error);
    }
  };

  const fetchReportingDesignations = async () => {
    try {
      const response = await designationsApi.list({ page_size: 100 });
      setReportingDesignations(response.data.items.filter((d: Designation) => d.id !== id));
    } catch (error) {
      logger.error('Failed to fetch reporting designations:', error);
    }
  };

  const fetchDesignation = async (desigId: string) => {
    try {
      setLoading(true);
      const response = await designationsApi.get(desigId);
      const designation: Designation = response.data;
      reset({
        code: designation.code,
        name: designation.name,
        short_name: designation.short_name || '',
        description: designation.description || '',
        department_id: designation.department_id || '',
        level: designation.level,
        reporting_to_id: designation.reporting_to_id || '',
        min_experience_years: designation.min_experience_years,
        min_qualification: designation.min_qualification || '',
        job_description: designation.job_description || '',
        responsibilities: designation.responsibilities || '',
        status: designation.status,
      });
    } catch (error) {
      logger.error('Failed to fetch designation:', error);
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data: DesignationCreate | DesignationUpdate) => {
    try {
      setSubmitting(true);
      const cleanData = {
        ...data,
        department_id: data.department_id || undefined,
        reporting_to_id: data.reporting_to_id || undefined,
        level: data.level ? Number(data.level) : 1,
        min_experience_years: data.min_experience_years ? Number(data.min_experience_years) : 0,
      };
      if (isEdit && id) {
        await designationsApi.update(id, cleanData);
      } else {
        await designationsApi.create(cleanData);
      }
      navigate('/admin/designations');
    } catch (error) {
      logger.error('Failed to save designation:', error);
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
        title={isEdit ? 'Edit Designation' : 'New Designation'}
        subtitle={isEdit ? 'Update designation details' : 'Create a new designation'}
        breadcrumbs={[
          { label: 'Designations', to: '/admin/designations' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
            <CardDescription>General designation details</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="code">Designation Code *</Label>
                <Input
                  id="code"
                  {...register('code', { required: 'Code is required' })}
                  placeholder="MGR001"
                  disabled={isEdit}
                />
                {errors.code && (
                  <p className="text-sm text-red-500">{errors.code.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">Designation Name *</Label>
                <Input
                  id="name"
                  {...register('name', { required: 'Name is required' })}
                  placeholder="Senior Manager"
                />
                {errors.name && (
                  <p className="text-sm text-red-500">{errors.name.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="short_name">Short Name</Label>
                <Input id="short_name" {...register('short_name')} placeholder="Sr Mgr" />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="department_id">Department</Label>
                <Select
                  value={watch('department_id') || '__none__'}
                  onValueChange={(value) => setValue('department_id', value === '__none__' ? '' : value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select department" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">None</SelectItem>
                    {departments.map((dept) => (
                      <SelectItem key={dept.id} value={dept.id}>
                        {dept.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="reporting_to_id">Reports To</Label>
                <Select
                  value={watch('reporting_to_id') || '__none__'}
                  onValueChange={(value) => setValue('reporting_to_id', value === '__none__' ? '' : value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select reporting designation" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">None</SelectItem>
                    {reportingDesignations.map((desig) => (
                      <SelectItem key={desig.id} value={desig.id}>
                        {desig.name}
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
                placeholder="Brief description of the designation"
                rows={3}
              />
            </div>
          </CardContent>
        </Card>

        {/* Position Details */}
        <Card>
          <CardHeader>
            <CardTitle>Position Details</CardTitle>
            <CardDescription>Level and requirements</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="level">Level</Label>
                <Input
                  id="level"
                  type="number"
                  {...register('level')}
                  placeholder="1"
                  min={1}
                  max={20}
                />
                <p className="text-xs text-slate-500">Higher level = more senior position</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="min_experience_years">Minimum Experience (Years)</Label>
                <Input
                  id="min_experience_years"
                  type="number"
                  {...register('min_experience_years')}
                  placeholder="0"
                  min={0}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="min_qualification">Minimum Qualification</Label>
                <Input
                  id="min_qualification"
                  {...register('min_qualification')}
                  placeholder="Bachelor's Degree"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Job Details */}
        <Card>
          <CardHeader>
            <CardTitle>Job Details</CardTitle>
            <CardDescription>Description and responsibilities</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="space-y-2">
              <Label htmlFor="job_description">Job Description</Label>
              <Textarea
                id="job_description"
                {...register('job_description')}
                placeholder="Detailed job description..."
                rows={4}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="responsibilities">Key Responsibilities</Label>
              <Textarea
                id="responsibilities"
                {...register('responsibilities')}
                placeholder="Key responsibilities and duties..."
                rows={4}
              />
            </div>
          </CardContent>
        </Card>

        {/* Form Actions */}
        <div className="flex items-center justify-end gap-4">
          <Button type="button" variant="outline" onClick={() => navigate('/admin/designations')}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Save className="mr-2 h-4 w-4" />
            {isEdit ? 'Update Designation' : 'Create Designation'}
          </Button>
        </div>
      </form>
    </div>
  );
}
