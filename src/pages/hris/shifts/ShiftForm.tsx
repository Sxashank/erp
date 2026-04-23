import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { ArrowLeft, Clock, Save } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { PageHeader } from '@/components/common/PageHeader';
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
import { hrisApi, organizationsApi } from '@/services/api';

interface ShiftFormData {
  organization_id: string;
  shift_code: string;
  shift_name: string;
  shift_type: string;
  start_time: string;
  end_time: string;
  break_duration_minutes: number;
  working_hours: number;
  grace_period_minutes: number;
  half_day_hours: number;
  min_half_day_hours: number;
  late_mark_threshold_minutes: number;
  early_leave_threshold_minutes: number;
  is_night_shift: boolean;
  is_flexible: boolean;
  flexible_start_time?: string;
  flexible_end_time?: string;
  week_offs: string[];
  is_active: boolean;
  remarks?: string;
}

interface Organization {
  id: string;
  name: string;
}

const SHIFT_TYPES = [
  { value: 'GENERAL', label: 'General' },
  { value: 'MORNING', label: 'Morning' },
  { value: 'AFTERNOON', label: 'Afternoon' },
  { value: 'NIGHT', label: 'Night' },
  { value: 'ROTATIONAL', label: 'Rotational' },
  { value: 'FLEXIBLE', label: 'Flexible' },
];

const WEEK_DAYS = [
  { value: 'MONDAY', label: 'Monday' },
  { value: 'TUESDAY', label: 'Tuesday' },
  { value: 'WEDNESDAY', label: 'Wednesday' },
  { value: 'THURSDAY', label: 'Thursday' },
  { value: 'FRIDAY', label: 'Friday' },
  { value: 'SATURDAY', label: 'Saturday' },
  { value: 'SUNDAY', label: 'Sunday' },
];

export function ShiftForm() {
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
  } = useForm<ShiftFormData>({
    defaultValues: {
      shift_type: 'GENERAL',
      break_duration_minutes: 60,
      working_hours: 8,
      grace_period_minutes: 15,
      half_day_hours: 4,
      min_half_day_hours: 2,
      late_mark_threshold_minutes: 15,
      early_leave_threshold_minutes: 15,
      is_night_shift: false,
      is_flexible: false,
      week_offs: ['SATURDAY', 'SUNDAY'],
      is_active: true,
    },
  });

  const watchOrganizationId = watch('organization_id');
  const watchIsFlexible = watch('is_flexible');
  const watchWeekOffs = watch('week_offs') || [];

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
        console.error('Failed to fetch organizations:', error);
      }
    };
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (isEdit && id) {
      const fetchShift = async () => {
        try {
          setLoading(true);
          const response = await hrisApi.getShift(id);
          const shift = response.data;

          Object.keys(shift).forEach((key) => {
            if (key in shift) {
              setValue(key as keyof ShiftFormData, shift[key]);
            }
          });
        } catch (error) {
          console.error('Failed to fetch shift:', error);
        } finally {
          setLoading(false);
        }
      };
      fetchShift();
    }
  }, [id, isEdit, setValue]);

  const onSubmit = async (data: ShiftFormData) => {
    try {
      setSaving(true);
      if (isEdit && id) {
        await hrisApi.updateShift(id, data);
      } else {
        await hrisApi.createShift(data);
      }
      navigate('/admin/hris/shifts');
    } catch (error) {
      console.error('Failed to save shift:', error);
    } finally {
      setSaving(false);
    }
  };

  const toggleWeekOff = (day: string) => {
    const current = watchWeekOffs || [];
    if (current.includes(day)) {
      setValue('week_offs', current.filter((d) => d !== day));
    } else {
      setValue('week_offs', [...current, day]);
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
        title={isEdit ? 'Edit Shift' : 'New Shift'}
        subtitle={isEdit ? 'Update shift details' : 'Create a new work shift'}
        breadcrumbs={[
          { label: 'Shifts', to: '/admin/hris/shifts' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit(onSubmit)}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Shift Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Basic Info */}
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
                <Label htmlFor="shift_code">Shift Code *</Label>
                <Input
                  id="shift_code"
                  {...register('shift_code', { required: 'Shift code is required' })}
                  placeholder="e.g., GEN, MOR, AFT"
                />
                {errors.shift_code && (
                  <p className="text-xs text-red-500">{errors.shift_code.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="shift_name">Shift Name *</Label>
                <Input
                  id="shift_name"
                  {...register('shift_name', { required: 'Shift name is required' })}
                  placeholder="e.g., General Shift"
                />
                {errors.shift_name && (
                  <p className="text-xs text-red-500">{errors.shift_name.message}</p>
                )}
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="shift_type">Shift Type *</Label>
                <Select
                  value={watch('shift_type')}
                  onValueChange={(v) => setValue('shift_type', v)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select Type" />
                  </SelectTrigger>
                  <SelectContent>
                    {SHIFT_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="start_time">Start Time *</Label>
                <Input
                  id="start_time"
                  type="time"
                  {...register('start_time', { required: 'Start time is required' })}
                />
                {errors.start_time && (
                  <p className="text-xs text-red-500">{errors.start_time.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="end_time">End Time *</Label>
                <Input
                  id="end_time"
                  type="time"
                  {...register('end_time', { required: 'End time is required' })}
                />
                {errors.end_time && (
                  <p className="text-xs text-red-500">{errors.end_time.message}</p>
                )}
              </div>
            </div>

            {/* Duration Settings */}
            <div className="grid gap-4 md:grid-cols-4">
              <div className="space-y-2">
                <Label htmlFor="working_hours">Working Hours *</Label>
                <Input
                  id="working_hours"
                  type="number"
                  step="0.5"
                  {...register('working_hours', {
                    required: 'Working hours is required',
                    valueAsNumber: true,
                  })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="break_duration_minutes">Break Duration (mins)</Label>
                <Input
                  id="break_duration_minutes"
                  type="number"
                  {...register('break_duration_minutes', { valueAsNumber: true })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="half_day_hours">Half Day Hours</Label>
                <Input
                  id="half_day_hours"
                  type="number"
                  step="0.5"
                  {...register('half_day_hours', { valueAsNumber: true })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="min_half_day_hours">Min Half Day Hours</Label>
                <Input
                  id="min_half_day_hours"
                  type="number"
                  step="0.5"
                  {...register('min_half_day_hours', { valueAsNumber: true })}
                />
              </div>
            </div>

            {/* Grace & Threshold Settings */}
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="grace_period_minutes">Grace Period (mins)</Label>
                <Input
                  id="grace_period_minutes"
                  type="number"
                  {...register('grace_period_minutes', { valueAsNumber: true })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="late_mark_threshold_minutes">Late Mark Threshold (mins)</Label>
                <Input
                  id="late_mark_threshold_minutes"
                  type="number"
                  {...register('late_mark_threshold_minutes', { valueAsNumber: true })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="early_leave_threshold_minutes">Early Leave Threshold (mins)</Label>
                <Input
                  id="early_leave_threshold_minutes"
                  type="number"
                  {...register('early_leave_threshold_minutes', { valueAsNumber: true })}
                />
              </div>
            </div>

            {/* Flexible Shift Settings */}
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_flexible"
                  checked={watchIsFlexible}
                  onCheckedChange={(checked) => setValue('is_flexible', checked as boolean)}
                />
                <Label htmlFor="is_flexible">Flexible Shift</Label>
              </div>

              {watchIsFlexible && (
                <div className="grid gap-4 md:grid-cols-2 pl-6">
                  <div className="space-y-2">
                    <Label htmlFor="flexible_start_time">Flexible Start Window</Label>
                    <Input
                      id="flexible_start_time"
                      type="time"
                      {...register('flexible_start_time')}
                    />
                    <p className="text-xs text-slate-500">Earliest allowed check-in time</p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="flexible_end_time">Flexible End Window</Label>
                    <Input
                      id="flexible_end_time"
                      type="time"
                      {...register('flexible_end_time')}
                    />
                    <p className="text-xs text-slate-500">Latest allowed check-out time</p>
                  </div>
                </div>
              )}
            </div>

            {/* Week Offs */}
            <div className="space-y-4">
              <Label>Week Offs</Label>
              <div className="flex flex-wrap gap-4">
                {WEEK_DAYS.map((day) => (
                  <div key={day.value} className="flex items-center space-x-2">
                    <Checkbox
                      id={`weekoff_${day.value}`}
                      checked={watchWeekOffs.includes(day.value)}
                      onCheckedChange={() => toggleWeekOff(day.value)}
                    />
                    <Label htmlFor={`weekoff_${day.value}`} className="font-normal">
                      {day.label}
                    </Label>
                  </div>
                ))}
              </div>
            </div>

            {/* Flags */}
            <div className="flex flex-wrap gap-6">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_night_shift"
                  checked={watch('is_night_shift')}
                  onCheckedChange={(checked) => setValue('is_night_shift', checked as boolean)}
                />
                <Label htmlFor="is_night_shift">Night Shift</Label>
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

            {/* Remarks */}
            <div className="space-y-2">
              <Label htmlFor="remarks">Remarks</Label>
              <Textarea
                id="remarks"
                {...register('remarks')}
                placeholder="Additional notes about this shift"
                rows={3}
              />
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => navigate('/admin/hris/shifts')}>
                Cancel
              </Button>
              <Button type="submit" disabled={saving}>
                <Save className="mr-2 h-4 w-4" />
                {saving ? 'Saving...' : isEdit ? 'Update Shift' : 'Create Shift'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  );
}
