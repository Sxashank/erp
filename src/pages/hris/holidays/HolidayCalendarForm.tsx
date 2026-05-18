import { ArrowLeft, CalendarDays, Edit, Plus, Save, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { HrisConfirmDialog } from '@/components/hris/HrisConfirmDialog';
import { Badge } from '@/components/ui/badge';
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';
import { hrisApi, organizationsApi } from '@/services/api';

import { logger } from "@/lib/logger";
interface HolidayCalendarFormData {
  organization_id: string;
  calendar_name: string;
  year: number;
  is_default: boolean;
  is_active: boolean;
  remarks?: string;
}

interface Holiday {
  id?: string;
  holiday_date: string;
  holiday_name: string;
  holiday_type: string;
  is_restricted: boolean;
  is_optional: boolean;
  applicable_for?: string;
  description?: string;
}

interface Organization {
  id: string;
  name: string;
}

const HOLIDAY_TYPES = [
  { value: 'NATIONAL', label: 'National Holiday' },
  { value: 'REGIONAL', label: 'Regional Holiday' },
  { value: 'RELIGIOUS', label: 'Religious Holiday' },
  { value: 'COMPANY', label: 'Company Holiday' },
  { value: 'OPTIONAL', label: 'Optional Holiday' },
];

const getHolidayTypeBadgeColor = (type: string) => {
  switch (type) {
    case 'NATIONAL':
      return 'bg-red-50 text-red-700';
    case 'REGIONAL':
      return 'bg-blue-50 text-blue-700';
    case 'RELIGIOUS':
      return 'bg-purple-50 text-purple-700';
    case 'COMPANY':
      return 'bg-green-50 text-green-700';
    case 'OPTIONAL':
      return 'bg-amber-50 text-amber-700';
    default:
      return 'bg-slate-100 text-slate-600';
  }
};

export function HolidayCalendarForm() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [holidays, setHolidays] = useState<Holiday[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showHolidayForm, setShowHolidayForm] = useState(false);
  const [editingHoliday, setEditingHoliday] = useState<Holiday | null>(null);
  const [deleteHolidayId, setDeleteHolidayId] = useState<string | null>(null);
  const [deleteBusy, setDeleteBusy] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<HolidayCalendarFormData>({
    defaultValues: {
      year: new Date().getFullYear(),
      is_default: false,
      is_active: true,
    },
  });

  const {
    register: registerHoliday,
    handleSubmit: handleSubmitHoliday,
    setValue: setHolidayValue,
    watch: watchHoliday,
    reset: resetHolidayForm,
    formState: { errors: holidayErrors },
  } = useForm<Holiday>({
    defaultValues: {
      holiday_type: 'NATIONAL',
      is_restricted: false,
      is_optional: false,
    },
  });

  const watchOrganizationId = watch('organization_id');
  const calendarId = id;

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
      const fetchCalendar = async () => {
        try {
          setLoading(true);
          const calendarRes = await hrisApi.getHolidayCalendar(id);

          const calendar = calendarRes.data;
          Object.keys(calendar).forEach((key) => {
            if (key in calendar) {
              setValue(key as keyof HolidayCalendarFormData, calendar[key]);
            }
          });

          // Holidays are included in the calendar response
          setHolidays(calendar.holidays || []);
        } catch (error) {
          logger.error('Failed to fetch calendar:', error);
        } finally {
          setLoading(false);
        }
      };
      fetchCalendar();
    }
  }, [id, isEdit, setValue]);

  const onSubmit = async (data: HolidayCalendarFormData) => {
    try {
      setSaving(true);
      if (isEdit && id) {
        await hrisApi.updateHolidayCalendar(id, data);
      } else {
        const response = await hrisApi.createHolidayCalendar(data);
        navigate(`/admin/hris/holidays/${response.data.id}/edit`);
        return;
      }
      navigate('/admin/hris/holidays');
    } catch (error) {
      logger.error('Failed to save calendar:', error);
    } finally {
      setSaving(false);
    }
  };

  const onHolidaySubmit = async (data: Holiday) => {
    if (!calendarId) return;

    try {
      if (editingHoliday?.id) {
        await hrisApi.updateHoliday(calendarId, editingHoliday.id, data);
        setHolidays(holidays.map((h) => (h.id === editingHoliday.id ? { ...data, id: editingHoliday.id } : h)));
      } else {
        const response = await hrisApi.createHoliday(calendarId, data);
        setHolidays([...holidays, response.data]);
      }
      resetHolidayForm();
      setShowHolidayForm(false);
      setEditingHoliday(null);
    } catch (error) {
      logger.error('Failed to save holiday:', error);
    }
  };

  const handleEditHoliday = (holiday: Holiday) => {
    setEditingHoliday(holiday);
    Object.keys(holiday).forEach((key) => {
      // Holiday[key] is a polymorphic field set; RHF setValue's value parameter
      // varies per key. Cast through unknown to avoid the per-key narrowing dance.
      setHolidayValue(key as keyof Holiday, holiday[key as keyof Holiday] as unknown as Holiday[keyof Holiday]);
    });
    setShowHolidayForm(true);
  };

  const executeDeleteHoliday = async () => {
    if (!calendarId || !deleteHolidayId) return;
    try {
      setDeleteBusy(true);
      await hrisApi.deleteHoliday(calendarId, deleteHolidayId);
      setHolidays(holidays.filter((h) => h.id !== deleteHolidayId));
      setDeleteHolidayId(null);
    } catch (error) {
      logger.error('Failed to delete holiday:', error);
    } finally {
      setDeleteBusy(false);
    }
  };

  const handleAddNewHoliday = () => {
    setEditingHoliday(null);
    resetHolidayForm({
      holiday_type: 'NATIONAL',
      is_restricted: false,
      is_optional: false,
    });
    setShowHolidayForm(true);
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
        title={isEdit ? 'Edit Holiday Calendar' : 'New Holiday Calendar'}
        subtitle={
          isEdit
            ? 'Update calendar and manage holidays'
            : 'Create a new holiday calendar'
        }
        breadcrumbs={[
          { label: 'Holiday Calendars', to: '/admin/hris/holidays' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit(onSubmit)}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CalendarDays className="h-5 w-5" />
              Calendar Details
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
                <Label htmlFor="calendar_name">Calendar Name *</Label>
                <Input
                  id="calendar_name"
                  {...register('calendar_name', { required: 'Calendar name is required' })}
                  placeholder="e.g., India Holidays 2026"
                />
                {errors.calendar_name && (
                  <p className="text-xs text-red-500">{errors.calendar_name.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="year">Year *</Label>
                <Input
                  id="year"
                  type="number"
                  {...register('year', {
                    required: 'Year is required',
                    valueAsNumber: true,
                    min: { value: 2020, message: 'Year must be 2020 or later' },
                    max: { value: 2100, message: 'Year must be before 2100' },
                  })}
                />
                {errors.year && (
                  <p className="text-xs text-red-500">{errors.year.message}</p>
                )}
              </div>
            </div>

            <div className="flex flex-wrap gap-6">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_default"
                  checked={watch('is_default')}
                  onCheckedChange={(checked) => setValue('is_default', checked as boolean)}
                />
                <Label htmlFor="is_default">Default Calendar</Label>
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

            <div className="space-y-2">
              <Label htmlFor="remarks">Remarks</Label>
              <Textarea
                id="remarks"
                {...register('remarks')}
                placeholder="Additional notes"
                rows={2}
              />
            </div>

            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => navigate('/admin/hris/holidays')}>
                Cancel
              </Button>
              <Button type="submit" disabled={saving}>
                <Save className="mr-2 h-4 w-4" />
                {saving ? 'Saving...' : isEdit ? 'Update Calendar' : 'Create Calendar'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </form>

      {/* Holidays Section - Only show for edit mode */}
      {isEdit && calendarId && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <CalendarDays className="h-5 w-5" />
                Holidays ({holidays.length})
              </CardTitle>
              <Button onClick={handleAddNewHoliday}>
                <Plus className="mr-2 h-4 w-4" />
                Add Holiday
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {showHolidayForm && (
              <form onSubmit={handleSubmitHoliday(onHolidaySubmit)} className="mb-6 p-4 border rounded-lg bg-slate-50">
                <h4 className="font-medium mb-4">{editingHoliday ? 'Edit Holiday' : 'Add New Holiday'}</h4>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="holiday_date">Date *</Label>
                    <Input
                      id="holiday_date"
                      type="date"
                      {...registerHoliday('holiday_date', { required: 'Date is required' })}
                    />
                    {holidayErrors.holiday_date && (
                      <p className="text-xs text-red-500">{holidayErrors.holiday_date.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="holiday_name">Holiday Name *</Label>
                    <Input
                      id="holiday_name"
                      {...registerHoliday('holiday_name', { required: 'Name is required' })}
                      placeholder="e.g., Republic Day"
                    />
                    {holidayErrors.holiday_name && (
                      <p className="text-xs text-red-500">{holidayErrors.holiday_name.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="holiday_type">Type *</Label>
                    <Select
                      value={watchHoliday('holiday_type')}
                      onValueChange={(v) => setHolidayValue('holiday_type', v)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select Type" />
                      </SelectTrigger>
                      <SelectContent>
                        {HOLIDAY_TYPES.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="description">Description</Label>
                    <Input
                      id="description"
                      {...registerHoliday('description')}
                      placeholder="Optional description"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="applicable_for">Applicable For</Label>
                    <Input
                      id="applicable_for"
                      {...registerHoliday('applicable_for')}
                      placeholder="e.g., All employees, specific region"
                    />
                  </div>
                </div>
                <div className="mt-4 flex flex-wrap gap-6">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="is_restricted"
                      checked={watchHoliday('is_restricted')}
                      onCheckedChange={(checked) => setHolidayValue('is_restricted', checked as boolean)}
                    />
                    <Label htmlFor="is_restricted">Restricted Holiday</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="is_optional"
                      checked={watchHoliday('is_optional')}
                      onCheckedChange={(checked) => setHolidayValue('is_optional', checked as boolean)}
                    />
                    <Label htmlFor="is_optional">Optional Holiday</Label>
                  </div>
                </div>
                <div className="mt-4 flex justify-end gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setShowHolidayForm(false);
                      setEditingHoliday(null);
                      resetHolidayForm();
                    }}
                  >
                    Cancel
                  </Button>
                  <Button type="submit">
                    {editingHoliday ? 'Update Holiday' : 'Add Holiday'}
                  </Button>
                </div>
              </form>
            )}

            {holidays.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8">
                <CalendarDays className="h-12 w-12 text-slate-300 mb-4" />
                <p className="text-sm text-slate-500">No holidays added yet</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Holiday Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Restricted</TableHead>
                    <TableHead>Optional</TableHead>
                    <TableHead className="w-[100px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {holidays
                    .sort((a, b) => new Date(a.holiday_date).getTime() - new Date(b.holiday_date).getTime())
                    .map((holiday) => (
                      <TableRow key={holiday.id}>
                        <TableCell>
                          <DateDisplay date={holiday.holiday_date} formatStr="EEE, MMM dd" />
                        </TableCell>
                        <TableCell className="font-medium">{holiday.holiday_name}</TableCell>
                        <TableCell>
                          <Badge className={getHolidayTypeBadgeColor(holiday.holiday_type)}>
                            {holiday.holiday_type}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={holiday.is_restricted ? 'default' : 'secondary'}>
                            {holiday.is_restricted ? 'Yes' : 'No'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={holiday.is_optional ? 'default' : 'secondary'}>
                            {holiday.is_optional ? 'Yes' : 'No'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleEditHoliday(holiday)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => holiday.id && setDeleteHolidayId(holiday.id)}
                              className="text-red-600 hover:text-red-700"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}
      <HrisConfirmDialog
        open={Boolean(deleteHolidayId)}
        title="Delete holiday"
        description="This removes the holiday from the calendar and may affect future attendance processing."
        confirmLabel="Delete holiday"
        destructive
        busy={deleteBusy}
        onOpenChange={(open) => {
          if (!open && !deleteBusy) setDeleteHolidayId(null);
        }}
        onConfirm={executeDeleteHoliday}
      />
    </div>
  );
}
