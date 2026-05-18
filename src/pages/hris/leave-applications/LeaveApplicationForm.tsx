import { ArrowLeft, Calendar, Save } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
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
import { Textarea } from '@/components/ui/textarea';
import { hrisApi, organizationsApi } from '@/services/api';

import { logger } from "@/lib/logger";
interface LeaveApplicationFormData {
  employee_id: string;
  leave_type_id: string;
  from_date: string;
  to_date: string;
  is_half_day: boolean;
  half_day_type?: string;
  reason: string;
  contact_number?: string;
  contact_address?: string;
}

interface Organization {
  id: string;
  name: string;
}

interface Employee {
  id: string;
  employee_code: string;
  full_name: string;
}

interface LeaveType {
  id: string;
  leave_code: string;
  leave_name: string;
  half_day_allowed: boolean;
}

interface LeaveBalance {
  leave_type_id: string;
  leave_type_name?: string;
  available_balance: number;
}

const HALF_DAY_OPTIONS = [
  { value: 'FIRST_HALF', label: 'First Half' },
  { value: 'SECOND_HALF', label: 'Second Half' },
];

export function LeaveApplicationForm() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);
  const [leaveBalances, setLeaveBalances] = useState<LeaveBalance[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<LeaveApplicationFormData>({
    defaultValues: {
      is_half_day: false,
    },
  });

  const watchEmployeeId = watch('employee_id');
  const watchLeaveTypeId = watch('leave_type_id');
  const watchIsHalfDay = watch('is_half_day');
  const watchFromDate = watch('from_date');
  const watchToDate = watch('to_date');

  const selectedLeaveType = leaveTypes.find((lt) => lt.id === watchLeaveTypeId);
  const selectedBalance = leaveBalances.find((lb) => lb.leave_type_id === watchLeaveTypeId);

  // Calculate days between dates
  const calculateDays = () => {
    if (!watchFromDate || !watchToDate) return 0;
    const from = new Date(watchFromDate);
    const to = new Date(watchToDate);
    const diffTime = Math.abs(to.getTime() - from.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
    return watchIsHalfDay ? 0.5 : diffDays;
  };

  useEffect(() => {
    const fetchOrganizations = async () => {
      try {
        const response = await organizationsApi.list({ page_size: 100 });
        const orgs = response.data.items || response.data;
        setOrganizations(Array.isArray(orgs) ? orgs : []);
        if (orgs.length > 0 && !selectedOrgId) {
          setSelectedOrgId(orgs[0].id);
        }
      } catch (error) {
        logger.error('Failed to fetch organizations:', error);
      }
    };
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (!selectedOrgId) return;

    const fetchEmployeesAndLeaveTypes = async () => {
      try {
        const [empRes, ltRes] = await Promise.all([
          hrisApi.listEmployees({ organization_id: selectedOrgId, limit: 500 }),
          hrisApi.listLeaveTypes({ organization_id: selectedOrgId }),
        ]);
        setEmployees(empRes.data.items || []);
        setLeaveTypes(ltRes.data.items || ltRes.data || []);
      } catch (error) {
        logger.error('Failed to fetch data:', error);
      }
    };
    fetchEmployeesAndLeaveTypes();
  }, [selectedOrgId]);

  // Fetch leave balances when employee changes
  useEffect(() => {
    if (!watchEmployeeId) {
      setLeaveBalances([]);
      return;
    }

    const fetchLeaveBalances = async () => {
      try {
        const response = await hrisApi.getLeaveBalances(watchEmployeeId, new Date().getFullYear());
        setLeaveBalances(response.data.items || response.data || []);
      } catch (error) {
        logger.error('Failed to fetch leave balances:', error);
      }
    };
    fetchLeaveBalances();
  }, [watchEmployeeId]);

  useEffect(() => {
    if (isEdit && id) {
      const fetchApplication = async () => {
        try {
          setLoading(true);
          const response = await hrisApi.getLeaveApplication(id);
          const application = response.data;

          Object.keys(application).forEach((key) => {
            if (key in application) {
              setValue(key as keyof LeaveApplicationFormData, application[key]);
            }
          });
        } catch (error) {
          logger.error('Failed to fetch leave application:', error);
        } finally {
          setLoading(false);
        }
      };
      fetchApplication();
    }
  }, [id, isEdit, setValue]);

  const onSubmit = async (data: LeaveApplicationFormData) => {
    try {
      setSaving(true);
      if (isEdit && id) {
        await hrisApi.updateLeaveApplication(id, data);
      } else {
        await hrisApi.createLeaveApplication(data);
      }
      navigate('/admin/hris/leave-applications');
    } catch (error) {
      logger.error('Failed to save leave application:', error);
    } finally {
      setSaving(false);
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
        title={isEdit ? 'Edit Leave Application' : 'Apply for Leave'}
        subtitle={isEdit ? 'Update leave application' : 'Submit a new leave request'}
        breadcrumbs={[
          { label: 'Leave Applications', to: '/admin/hris/leave-applications' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Main Form */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  Leave Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Organization & Employee */}
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Organization *</Label>
                    <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
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
                    <Label htmlFor="employee_id">Employee *</Label>
                    <Select
                      value={watchEmployeeId}
                      onValueChange={(v) => setValue('employee_id', v)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select Employee" />
                      </SelectTrigger>
                      <SelectContent>
                        {employees.map((emp) => (
                          <SelectItem key={emp.id} value={emp.id}>
                            {emp.employee_code} - {emp.full_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {errors.employee_id && (
                      <p className="text-xs text-red-500">{errors.employee_id.message}</p>
                    )}
                  </div>
                </div>

                {/* Leave Type */}
                <div className="space-y-2">
                  <Label htmlFor="leave_type_id">Leave Type *</Label>
                  <Select
                    value={watchLeaveTypeId}
                    onValueChange={(v) => setValue('leave_type_id', v)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select Leave Type" />
                    </SelectTrigger>
                    <SelectContent>
                      {leaveTypes.map((lt) => (
                        <SelectItem key={lt.id} value={lt.id}>
                          {lt.leave_code} - {lt.leave_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.leave_type_id && (
                    <p className="text-xs text-red-500">{errors.leave_type_id.message}</p>
                  )}
                </div>

                {/* Dates */}
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="from_date">From Date *</Label>
                    <Input
                      id="from_date"
                      type="date"
                      {...register('from_date', { required: 'From date is required' })}
                    />
                    {errors.from_date && (
                      <p className="text-xs text-red-500">{errors.from_date.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="to_date">To Date *</Label>
                    <Input
                      id="to_date"
                      type="date"
                      {...register('to_date', { required: 'To date is required' })}
                    />
                    {errors.to_date && (
                      <p className="text-xs text-red-500">{errors.to_date.message}</p>
                    )}
                  </div>
                </div>

                {/* Half Day */}
                {selectedLeaveType?.half_day_allowed && (
                  <div className="space-y-4">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="is_half_day"
                        checked={watchIsHalfDay}
                        onCheckedChange={(checked) => setValue('is_half_day', checked as boolean)}
                      />
                      <Label htmlFor="is_half_day">Half Day Leave</Label>
                    </div>

                    {watchIsHalfDay && (
                      <div className="space-y-2 pl-6">
                        <Label htmlFor="half_day_type">Half Day Type *</Label>
                        <Select
                          value={watch('half_day_type') || ''}
                          onValueChange={(v) => setValue('half_day_type', v)}
                        >
                          <SelectTrigger className="max-w-xs">
                            <SelectValue placeholder="Select Half" />
                          </SelectTrigger>
                          <SelectContent>
                            {HALF_DAY_OPTIONS.map((opt) => (
                              <SelectItem key={opt.value} value={opt.value}>
                                {opt.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    )}
                  </div>
                )}

                {/* Reason */}
                <div className="space-y-2">
                  <Label htmlFor="reason">Reason *</Label>
                  <Textarea
                    id="reason"
                    {...register('reason', { required: 'Reason is required' })}
                    placeholder="Please provide the reason for leave"
                    rows={4}
                  />
                  {errors.reason && (
                    <p className="text-xs text-red-500">{errors.reason.message}</p>
                  )}
                </div>

                {/* Contact During Leave */}
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="contact_number">Contact Number During Leave</Label>
                    <Input
                      id="contact_number"
                      {...register('contact_number')}
                      placeholder="Phone number"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="contact_address">Contact Address</Label>
                    <Input
                      id="contact_address"
                      {...register('contact_address')}
                      placeholder="Address during leave"
                    />
                  </div>
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => navigate('/admin/hris/leave-applications')}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={saving}>
                    <Save className="mr-2 h-4 w-4" />
                    {saving ? 'Submitting...' : isEdit ? 'Update Application' : 'Submit Application'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Summary Card */}
          <div>
            <Card>
              <CardHeader>
                <CardTitle>Leave Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-sm text-slate-500">Leave Type</span>
                  <span className="font-medium">
                    {selectedLeaveType?.leave_name || '-'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-slate-500">Duration</span>
                  <span className="font-medium">{calculateDays()} day(s)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-slate-500">Available Balance</span>
                  <Badge variant={selectedBalance && selectedBalance.available_balance > 0 ? 'default' : 'secondary'}>
                    {selectedBalance?.available_balance ?? '-'} days
                  </Badge>
                </div>

                {watchEmployeeId && leaveBalances.length > 0 && (
                  <>
                    <hr />
                    <h4 className="font-medium text-sm">All Leave Balances</h4>
                    <div className="space-y-2">
                      {leaveBalances.map((balance) => (
                        <div key={balance.leave_type_id} className="flex justify-between text-sm">
                          <span className="text-slate-500">{balance.leave_type_name}</span>
                          <span className="font-medium">{balance.available_balance}</span>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </form>
    </div>
  );
}
