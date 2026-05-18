import { ArrowLeft, Calendar, Save } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { hrisApi, organizationsApi } from '@/services/api';

import { logger } from "@/lib/logger";
interface LeaveTypeFormData {
  organization_id: string;
  leave_code: string;
  leave_name: string;
  category: string;
  description?: string;
  annual_quota: number;
  max_accumulation?: number;
  accrual_type: string;
  accrual_on_joining: boolean;
  prorate_on_joining: boolean;
  carry_forward_allowed: boolean;
  max_carry_forward?: number;
  carry_forward_expiry_months?: number;
  encashment_allowed: boolean;
  max_encashment_days?: number;
  encashment_on_separation: boolean;
  min_days_per_application: number;
  max_days_per_application?: number;
  max_consecutive_days?: number;
  min_advance_days: number;
  max_advance_days?: number;
  can_club_with_holidays: boolean;
  can_club_with_weekoff: boolean;
  excluded_holidays_counted: boolean;
  negative_balance_allowed: boolean;
  max_negative_balance?: number;
  document_required: boolean;
  document_required_after_days?: number;
  gender_specific?: string;
  applicable_employment_types?: string[];
  applicable_in_probation: boolean;
  probation_quota?: number;
  applicable_in_notice: boolean;
  comp_off_validity_days?: number;
  half_day_allowed: boolean;
  is_paid: boolean;
  is_active: boolean;
  display_order: number;
}

interface Organization {
  id: string;
  name: string;
}

const LEAVE_CATEGORIES = [
  { value: 'CASUAL', label: 'Casual Leave' },
  { value: 'SICK', label: 'Sick Leave' },
  { value: 'EARNED', label: 'Earned/Privilege Leave' },
  { value: 'MATERNITY', label: 'Maternity Leave' },
  { value: 'PATERNITY', label: 'Paternity Leave' },
  { value: 'COMP_OFF', label: 'Compensatory Off' },
  { value: 'LOP', label: 'Loss of Pay' },
  { value: 'BEREAVEMENT', label: 'Bereavement Leave' },
  { value: 'MARRIAGE', label: 'Marriage Leave' },
  { value: 'STUDY', label: 'Study Leave' },
  { value: 'SPECIAL', label: 'Special Leave' },
];

const ACCRUAL_TYPES = [
  { value: 'YEARLY', label: 'Yearly (Credit at start)' },
  { value: 'MONTHLY', label: 'Monthly Accrual' },
  { value: 'PRORATE', label: 'Prorated based on joining' },
];

const GENDER_OPTIONS = [
  { value: '', label: 'All Genders' },
  { value: 'MALE', label: 'Male Only' },
  { value: 'FEMALE', label: 'Female Only' },
];

const EMPLOYMENT_TYPES = [
  { value: 'PERMANENT', label: 'Permanent' },
  { value: 'CONTRACT', label: 'Contract' },
  { value: 'PROBATION', label: 'Probation' },
  { value: 'INTERN', label: 'Intern' },
  { value: 'TRAINEE', label: 'Trainee' },
  { value: 'CONSULTANT', label: 'Consultant' },
];

export function LeaveTypeForm() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<LeaveTypeFormData>({
    defaultValues: {
      category: 'CASUAL',
      annual_quota: 12,
      accrual_type: 'YEARLY',
      accrual_on_joining: true,
      prorate_on_joining: true,
      carry_forward_allowed: false,
      encashment_allowed: false,
      encashment_on_separation: false,
      min_days_per_application: 0.5,
      min_advance_days: 0,
      can_club_with_holidays: true,
      can_club_with_weekoff: true,
      excluded_holidays_counted: false,
      negative_balance_allowed: false,
      document_required: false,
      applicable_in_probation: true,
      applicable_in_notice: false,
      half_day_allowed: true,
      is_paid: true,
      is_active: true,
      display_order: 0,
    },
  });

  const watchOrganizationId = watch('organization_id');
  const watchCategory = watch('category');
  const watchCarryForward = watch('carry_forward_allowed');
  const watchEncashment = watch('encashment_allowed');
  const watchNegativeBalance = watch('negative_balance_allowed');
  const watchDocumentRequired = watch('document_required');
  const watchApplicableInProbation = watch('applicable_in_probation');
  const watchApplicableEmploymentTypes = watch('applicable_employment_types') || [];

  useEffect(() => {
    const fetchOrganizations = async () => {
      try {
        const response = await organizationsApi.list({ page_size: 100 });
        const orgs = response.data.items || response.data;
        setOrganizations(Array.isArray(orgs) ? orgs : []);
        if (orgs.length > 0 && !watchOrganizationId) {
          setValue('organization_id', orgs[0].id);
        }
      } catch (error) {
        logger.error('Failed to fetch organizations:', error);
      }
    };
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (isEdit && id) {
      const fetchLeaveType = async () => {
        try {
          setLoading(true);
          const response = await hrisApi.getLeaveType(id);
          const leaveType = response.data;

          Object.keys(leaveType).forEach((key) => {
            if (key in leaveType) {
              setValue(key as keyof LeaveTypeFormData, leaveType[key]);
            }
          });
        } catch (error) {
          logger.error('Failed to fetch leave type:', error);
        } finally {
          setLoading(false);
        }
      };
      fetchLeaveType();
    }
  }, [id, isEdit, setValue]);

  const onSubmit = async (data: LeaveTypeFormData) => {
    try {
      setSaving(true);
      if (isEdit && id) {
        await hrisApi.updateLeaveType(id, data);
      } else {
        await hrisApi.createLeaveType(data);
      }
      navigate('/admin/hris/leave-types');
    } catch (error) {
      logger.error('Failed to save leave type:', error);
    } finally {
      setSaving(false);
    }
  };

  const toggleEmploymentType = (type: string) => {
    const current = watchApplicableEmploymentTypes || [];
    if (current.includes(type)) {
      setValue('applicable_employment_types', current.filter((t) => t !== type));
    } else {
      setValue('applicable_employment_types', [...current, type]);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-sm text-slate-500">Loading...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEdit ? 'Edit Leave Type' : 'New Leave Type'}
        subtitle={
          isEdit ? 'Update leave type configuration' : 'Create a new leave type'
        }
        breadcrumbs={[
          { label: 'Leave Types', to: '/admin/hris/leave-types' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit(onSubmit)}>
        <Tabs defaultValue="basic" className="space-y-4">
          <TabsList>
            <TabsTrigger value="basic">Basic Details</TabsTrigger>
            <TabsTrigger value="accrual">Accrual & Quota</TabsTrigger>
            <TabsTrigger value="rules">Application Rules</TabsTrigger>
            <TabsTrigger value="eligibility">Eligibility</TabsTrigger>
          </TabsList>

          {/* Basic Details Tab */}
          <TabsContent value="basic">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  Basic Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="organization_id">Organization *</Label>
                    <Select
                      value={watchOrganizationId}
                      onValueChange={(v) => setValue('organization_id', v)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select Organization" />
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
                    <Label htmlFor="leave_code">Leave Code *</Label>
                    <Input
                      id="leave_code"
                      {...register('leave_code', { required: 'Leave code is required' })}
                      placeholder="e.g., CL, SL, EL"
                    />
                    {errors.leave_code && (
                      <p className="text-xs text-red-500">{errors.leave_code.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="leave_name">Leave Name *</Label>
                    <Input
                      id="leave_name"
                      {...register('leave_name', { required: 'Leave name is required' })}
                      placeholder="e.g., Casual Leave"
                    />
                    {errors.leave_name && (
                      <p className="text-xs text-red-500">{errors.leave_name.message}</p>
                    )}
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="category">Category *</Label>
                    <Select
                      value={watchCategory}
                      onValueChange={(v) => setValue('category', v)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select Category" />
                      </SelectTrigger>
                      <SelectContent>
                        {LEAVE_CATEGORIES.map((cat) => (
                          <SelectItem key={cat.value} value={cat.value}>
                            {cat.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="display_order">Display Order</Label>
                    <Input
                      id="display_order"
                      type="number"
                      {...register('display_order', { valueAsNumber: true })}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    {...register('description')}
                    placeholder="Leave type description and usage notes"
                    rows={3}
                  />
                </div>

                <div className="flex flex-wrap gap-6">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="is_paid"
                      checked={watch('is_paid')}
                      onCheckedChange={(checked) => setValue('is_paid', checked as boolean)}
                    />
                    <Label htmlFor="is_paid">Paid Leave</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="half_day_allowed"
                      checked={watch('half_day_allowed')}
                      onCheckedChange={(checked) => setValue('half_day_allowed', checked as boolean)}
                    />
                    <Label htmlFor="half_day_allowed">Half Day Allowed</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="is_active"
                      checked={watch('is_active')}
                      onCheckedChange={(checked) => setValue('is_active', checked as boolean)}
                    />
                    <Label htmlFor="is_active">Active</Label>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Accrual & Quota Tab */}
          <TabsContent value="accrual">
            <Card>
              <CardHeader>
                <CardTitle>Accrual & Quota Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="annual_quota">Annual Quota (days) *</Label>
                    <Input
                      id="annual_quota"
                      type="number"
                      step="0.5"
                      {...register('annual_quota', {
                        required: 'Annual quota is required',
                        valueAsNumber: true,
                      })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="max_accumulation">Max Accumulation</Label>
                    <Input
                      id="max_accumulation"
                      type="number"
                      step="0.5"
                      {...register('max_accumulation', { valueAsNumber: true })}
                      placeholder="Max balance allowed"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="accrual_type">Accrual Type</Label>
                    <Select
                      value={watch('accrual_type')}
                      onValueChange={(v) => setValue('accrual_type', v)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {ACCRUAL_TYPES.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="flex flex-wrap gap-6">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="accrual_on_joining"
                      checked={watch('accrual_on_joining')}
                      onCheckedChange={(checked) => setValue('accrual_on_joining', checked as boolean)}
                    />
                    <Label htmlFor="accrual_on_joining">Accrue from Joining Date</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="prorate_on_joining"
                      checked={watch('prorate_on_joining')}
                      onCheckedChange={(checked) => setValue('prorate_on_joining', checked as boolean)}
                    />
                    <Label htmlFor="prorate_on_joining">Prorate for Partial Year</Label>
                  </div>
                </div>

                <hr />

                <h4 className="font-medium">Carry Forward Settings</h4>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="carry_forward_allowed"
                    checked={watchCarryForward}
                    onCheckedChange={(checked) => setValue('carry_forward_allowed', checked as boolean)}
                  />
                  <Label htmlFor="carry_forward_allowed">Allow Carry Forward</Label>
                </div>

                {watchCarryForward && (
                  <div className="grid gap-4 md:grid-cols-2 pl-6">
                    <div className="space-y-2">
                      <Label htmlFor="max_carry_forward">Max Carry Forward Days</Label>
                      <Input
                        id="max_carry_forward"
                        type="number"
                        step="0.5"
                        {...register('max_carry_forward', { valueAsNumber: true })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="carry_forward_expiry_months">Expiry (Months)</Label>
                      <Input
                        id="carry_forward_expiry_months"
                        type="number"
                        {...register('carry_forward_expiry_months', { valueAsNumber: true })}
                        placeholder="e.g., 3 months"
                      />
                    </div>
                  </div>
                )}

                <hr />

                <h4 className="font-medium">Encashment Settings</h4>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="encashment_allowed"
                    checked={watchEncashment}
                    onCheckedChange={(checked) => setValue('encashment_allowed', checked as boolean)}
                  />
                  <Label htmlFor="encashment_allowed">Allow Encashment</Label>
                </div>

                {watchEncashment && (
                  <div className="grid gap-4 md:grid-cols-2 pl-6">
                    <div className="space-y-2">
                      <Label htmlFor="max_encashment_days">Max Encashable Days</Label>
                      <Input
                        id="max_encashment_days"
                        type="number"
                        step="0.5"
                        {...register('max_encashment_days', { valueAsNumber: true })}
                      />
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="encashment_on_separation"
                        checked={watch('encashment_on_separation')}
                        onCheckedChange={(checked) => setValue('encashment_on_separation', checked as boolean)}
                      />
                      <Label htmlFor="encashment_on_separation">Encash on Separation</Label>
                    </div>
                  </div>
                )}

                {watchCategory === 'COMP_OFF' && (
                  <>
                    <hr />
                    <h4 className="font-medium">Compensatory Off Settings</h4>
                    <div className="space-y-2">
                      <Label htmlFor="comp_off_validity_days">Validity (Days)</Label>
                      <Input
                        id="comp_off_validity_days"
                        type="number"
                        {...register('comp_off_validity_days', { valueAsNumber: true })}
                        placeholder="e.g., 30 days"
                        className="max-w-xs"
                      />
                      <p className="text-xs text-slate-500">Days within which comp-off must be availed</p>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Application Rules Tab */}
          <TabsContent value="rules">
            <Card>
              <CardHeader>
                <CardTitle>Application Rules</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="min_days_per_application">Min Days Per Application</Label>
                    <Input
                      id="min_days_per_application"
                      type="number"
                      step="0.5"
                      {...register('min_days_per_application', { valueAsNumber: true })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="max_days_per_application">Max Days Per Application</Label>
                    <Input
                      id="max_days_per_application"
                      type="number"
                      step="0.5"
                      {...register('max_days_per_application', { valueAsNumber: true })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="max_consecutive_days">Max Consecutive Days</Label>
                    <Input
                      id="max_consecutive_days"
                      type="number"
                      {...register('max_consecutive_days', { valueAsNumber: true })}
                    />
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="min_advance_days">Min Advance Notice (Days)</Label>
                    <Input
                      id="min_advance_days"
                      type="number"
                      {...register('min_advance_days', { valueAsNumber: true })}
                    />
                    <p className="text-xs text-slate-500">Days in advance required for application</p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="max_advance_days">Max Advance Notice (Days)</Label>
                    <Input
                      id="max_advance_days"
                      type="number"
                      {...register('max_advance_days', { valueAsNumber: true })}
                    />
                  </div>
                </div>

                <hr />

                <h4 className="font-medium">Clubbing Rules</h4>
                <div className="flex flex-wrap gap-6">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="can_club_with_holidays"
                      checked={watch('can_club_with_holidays')}
                      onCheckedChange={(checked) => setValue('can_club_with_holidays', checked as boolean)}
                    />
                    <Label htmlFor="can_club_with_holidays">Can Club with Holidays</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="can_club_with_weekoff"
                      checked={watch('can_club_with_weekoff')}
                      onCheckedChange={(checked) => setValue('can_club_with_weekoff', checked as boolean)}
                    />
                    <Label htmlFor="can_club_with_weekoff">Can Club with Week-offs</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="excluded_holidays_counted"
                      checked={watch('excluded_holidays_counted')}
                      onCheckedChange={(checked) => setValue('excluded_holidays_counted', checked as boolean)}
                    />
                    <Label htmlFor="excluded_holidays_counted">Count Holidays in Between</Label>
                  </div>
                </div>

                <hr />

                <h4 className="font-medium">Negative Balance</h4>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="negative_balance_allowed"
                    checked={watchNegativeBalance}
                    onCheckedChange={(checked) => setValue('negative_balance_allowed', checked as boolean)}
                  />
                  <Label htmlFor="negative_balance_allowed">Allow Negative Balance</Label>
                </div>

                {watchNegativeBalance && (
                  <div className="pl-6">
                    <div className="space-y-2 max-w-xs">
                      <Label htmlFor="max_negative_balance">Max Negative Balance</Label>
                      <Input
                        id="max_negative_balance"
                        type="number"
                        step="0.5"
                        {...register('max_negative_balance', { valueAsNumber: true })}
                      />
                    </div>
                  </div>
                )}

                <hr />

                <h4 className="font-medium">Document Requirements</h4>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="document_required"
                    checked={watchDocumentRequired}
                    onCheckedChange={(checked) => setValue('document_required', checked as boolean)}
                  />
                  <Label htmlFor="document_required">Document Required</Label>
                </div>

                {watchDocumentRequired && (
                  <div className="pl-6">
                    <div className="space-y-2 max-w-xs">
                      <Label htmlFor="document_required_after_days">Required After Days</Label>
                      <Input
                        id="document_required_after_days"
                        type="number"
                        {...register('document_required_after_days', { valueAsNumber: true })}
                        placeholder="e.g., 2 days"
                      />
                      <p className="text-xs text-slate-500">Document required for leaves exceeding this duration</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Eligibility Tab */}
          <TabsContent value="eligibility">
            <Card>
              <CardHeader>
                <CardTitle>Eligibility Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="gender_specific">Gender Specific</Label>
                  <Select
                    value={watch('gender_specific') || ''}
                    onValueChange={(v) => setValue('gender_specific', v || undefined)}
                  >
                    <SelectTrigger className="max-w-xs">
                      <SelectValue placeholder="Select Gender" />
                    </SelectTrigger>
                    <SelectContent>
                      {GENDER_OPTIONS.map((opt) => (
                        <SelectItem key={opt.value || 'all'} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <hr />

                <div className="space-y-4">
                  <Label>Applicable Employment Types</Label>
                  <p className="text-xs text-slate-500">Leave blank for all employment types</p>
                  <div className="flex flex-wrap gap-4">
                    {EMPLOYMENT_TYPES.map((type) => (
                      <div key={type.value} className="flex items-center space-x-2">
                        <Checkbox
                          id={`emptype_${type.value}`}
                          checked={watchApplicableEmploymentTypes.includes(type.value)}
                          onCheckedChange={() => toggleEmploymentType(type.value)}
                        />
                        <Label htmlFor={`emptype_${type.value}`} className="font-normal">
                          {type.label}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>

                <hr />

                <h4 className="font-medium">Probation Period</h4>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="applicable_in_probation"
                    checked={watchApplicableInProbation}
                    onCheckedChange={(checked) => setValue('applicable_in_probation', checked as boolean)}
                  />
                  <Label htmlFor="applicable_in_probation">Applicable During Probation</Label>
                </div>

                {watchApplicableInProbation && (
                  <div className="pl-6">
                    <div className="space-y-2 max-w-xs">
                      <Label htmlFor="probation_quota">Probation Quota</Label>
                      <Input
                        id="probation_quota"
                        type="number"
                        step="0.5"
                        {...register('probation_quota', { valueAsNumber: true })}
                        placeholder="Leave blank for full quota"
                      />
                      <p className="text-xs text-slate-500">Different quota during probation (if any)</p>
                    </div>
                  </div>
                )}

                <hr />

                <h4 className="font-medium">Notice Period</h4>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="applicable_in_notice"
                    checked={watch('applicable_in_notice')}
                    onCheckedChange={(checked) => setValue('applicable_in_notice', checked as boolean)}
                  />
                  <Label htmlFor="applicable_in_notice">Applicable During Notice Period</Label>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Actions */}
        <div className="flex justify-end gap-2 mt-6">
          <Button type="button" variant="outline" onClick={() => navigate('/admin/hris/leave-types')}>
            Cancel
          </Button>
          <Button type="submit" disabled={saving}>
            <Save className="mr-2 h-4 w-4" />
            {saving ? 'Saving...' : isEdit ? 'Update Leave Type' : 'Create Leave Type'}
          </Button>
        </div>
      </form>
    </div>
  );
}
