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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { hrisApi, organizationsApi, departmentsApi, designationsApi, unitsApi } from '@/services/api';

import { logger } from "@/lib/logger";
const GENDER_OPTIONS = [
  { value: 'MALE', label: 'Male' },
  { value: 'FEMALE', label: 'Female' },
  { value: 'OTHER', label: 'Other' },
];

const SALUTATION_OPTIONS = [
  { value: 'MR', label: 'Mr.' },
  { value: 'MS', label: 'Ms.' },
  { value: 'MRS', label: 'Mrs.' },
  { value: 'DR', label: 'Dr.' },
  { value: 'PROF', label: 'Prof.' },
];

const MARITAL_STATUS_OPTIONS = [
  { value: 'SINGLE', label: 'Single' },
  { value: 'MARRIED', label: 'Married' },
  { value: 'DIVORCED', label: 'Divorced' },
  { value: 'WIDOWED', label: 'Widowed' },
];

const EMPLOYMENT_TYPE_OPTIONS = [
  { value: 'PERMANENT', label: 'Permanent' },
  { value: 'CONTRACT', label: 'Contract' },
  { value: 'PROBATION', label: 'Probation' },
  { value: 'INTERN', label: 'Intern' },
  { value: 'TRAINEE', label: 'Trainee' },
  { value: 'CONSULTANT', label: 'Consultant' },
  { value: 'TEMPORARY', label: 'Temporary' },
];

const EMPLOYMENT_STATUS_OPTIONS = [
  { value: 'ACTIVE', label: 'Active' },
  { value: 'PROBATION', label: 'Probation' },
  { value: 'NOTICE_PERIOD', label: 'Notice Period' },
  { value: 'RELIEVED', label: 'Relieved' },
  { value: 'SUSPENDED', label: 'Suspended' },
];

const BLOOD_GROUP_OPTIONS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

interface FormData {
  organization_id: string;
  employee_code?: string;
  salutation?: string;
  first_name: string;
  middle_name?: string;
  last_name: string;
  gender: string;
  date_of_birth: string;
  blood_group?: string;
  marital_status?: string;
  nationality?: string;
  personal_email?: string;
  personal_mobile: string;
  official_email?: string;
  official_mobile?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  emergency_contact_relation?: string;
  current_address?: {
    line1?: string;
    line2?: string;
    city?: string;
    state?: string;
    pincode?: string;
    country?: string;
  };
  permanent_address?: {
    line1?: string;
    line2?: string;
    city?: string;
    state?: string;
    pincode?: string;
    country?: string;
  };
  is_address_same?: boolean;
  department_id?: string;
  designation_id?: string;
  reporting_manager_id?: string;
  unit_id?: string;
  date_of_joining: string;
  confirmation_date?: string;
  probation_end_date?: string;
  employment_type: string;
  employment_status: string;
  notice_period_days?: number;
  shift_id?: string;
  pan_number?: string;
  aadhaar_number?: string;
  uan_number?: string;
  esic_number?: string;
}

export function EmployeeForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [organizations, setOrganizations] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [designations, setDesignations] = useState<any[]>([]);
  const [units, setUnits] = useState<any[]>([]);
  const [shifts, setShifts] = useState<any[]>([]);
  const [managers, setManagers] = useState<any[]>([]);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: {
      employment_type: 'PERMANENT',
      employment_status: 'ACTIVE',
      nationality: 'Indian',
      notice_period_days: 30,
    },
  });

  const selectedOrgId = watch('organization_id');
  const selectedDeptId = watch('department_id');
  const isAddressSame = watch('is_address_same');

  // Fetch organizations
  useEffect(() => {
    const fetchOrgs = async () => {
      try {
        const response = await organizationsApi.list({ page_size: 100 });
        setOrganizations(response.data.items || []);
      } catch (error) {
        logger.error('Failed to fetch organizations:', error);
      }
    };
    fetchOrgs();
  }, []);

  // Fetch departments when org changes
  useEffect(() => {
    const fetchDepts = async () => {
      if (!selectedOrgId) return;
      try {
        const response = await departmentsApi.list({ organization_id: selectedOrgId, page_size: 100 });
        setDepartments(response.data.items || []);
      } catch (error) {
        logger.error('Failed to fetch departments:', error);
      }
    };
    fetchDepts();
  }, [selectedOrgId]);

  // Fetch designations when dept changes
  useEffect(() => {
    const fetchDesigs = async () => {
      if (!selectedDeptId) return;
      try {
        const response = await designationsApi.list({ department_id: selectedDeptId, page_size: 100 });
        setDesignations(response.data.items || []);
      } catch (error) {
        logger.error('Failed to fetch designations:', error);
      }
    };
    fetchDesigs();
  }, [selectedDeptId]);

  // Fetch units when org changes
  useEffect(() => {
    const fetchUnits = async () => {
      if (!selectedOrgId) return;
      try {
        const response = await unitsApi.list({ organization_id: selectedOrgId, page_size: 100 });
        setUnits(response.data.items || []);
      } catch (error) {
        logger.error('Failed to fetch units:', error);
      }
    };
    fetchUnits();
  }, [selectedOrgId]);

  // Fetch shifts when org changes
  useEffect(() => {
    const fetchShifts = async () => {
      if (!selectedOrgId) return;
      try {
        const response = await hrisApi.listShifts({ organization_id: selectedOrgId, active_only: true });
        setShifts(response.data || []);
      } catch (error) {
        logger.error('Failed to fetch shifts:', error);
      }
    };
    fetchShifts();
  }, [selectedOrgId]);

  // Fetch managers when org changes
  useEffect(() => {
    const fetchManagers = async () => {
      if (!selectedOrgId) return;
      try {
        const response = await hrisApi.listEmployees({
          organization_id: selectedOrgId,
          employment_status: 'ACTIVE',
          limit: 100,
        });
        setManagers(response.data.items?.filter((e: { id: string }) => e.id !== id) || []);
      } catch (error) {
        logger.error('Failed to fetch managers:', error);
      }
    };
    fetchManagers();
  }, [selectedOrgId, id]);

  // Fetch employee for edit
  useEffect(() => {
    const fetchEmployee = async () => {
      if (!isEdit || !id) return;
      try {
        setLoading(true);
        const response = await hrisApi.getEmployee(id);
        const emp = response.data;
        reset({
          organization_id: emp.organization_id,
          employee_code: emp.employee_code,
          salutation: emp.salutation,
          first_name: emp.first_name,
          middle_name: emp.middle_name,
          last_name: emp.last_name,
          gender: emp.gender,
          date_of_birth: emp.date_of_birth,
          blood_group: emp.blood_group,
          marital_status: emp.marital_status,
          nationality: emp.nationality,
          personal_email: emp.personal_email,
          personal_mobile: emp.personal_mobile,
          official_email: emp.official_email,
          official_mobile: emp.official_mobile,
          emergency_contact_name: emp.emergency_contact_name,
          emergency_contact_phone: emp.emergency_contact_phone,
          emergency_contact_relation: emp.emergency_contact_relation,
          current_address: emp.current_address,
          permanent_address: emp.permanent_address,
          is_address_same: emp.is_address_same,
          department_id: emp.department_id,
          designation_id: emp.designation_id,
          reporting_manager_id: emp.reporting_manager_id,
          unit_id: emp.unit_id,
          date_of_joining: emp.date_of_joining,
          confirmation_date: emp.confirmation_date,
          probation_end_date: emp.probation_end_date,
          employment_type: emp.employment_type,
          employment_status: emp.employment_status,
          notice_period_days: emp.notice_period_days,
          shift_id: emp.shift_id,
          pan_number: emp.pan_number,
          aadhaar_number: emp.aadhaar_number,
          uan_number: emp.uan_number,
          esic_number: emp.esic_number,
        });
      } catch (error) {
        logger.error('Failed to fetch employee:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchEmployee();
  }, [id, isEdit, reset]);

  const onSubmit = async (data: FormData) => {
    try {
      setSubmitting(true);
      const cleanData = {
        ...data,
        department_id: data.department_id || undefined,
        designation_id: data.designation_id || undefined,
        reporting_manager_id: data.reporting_manager_id || undefined,
        unit_id: data.unit_id || undefined,
        shift_id: data.shift_id || undefined,
      };

      if (isEdit && id) {
        await hrisApi.updateEmployee(id, cleanData);
      } else {
        await hrisApi.createEmployee(cleanData);
      }
      navigate('/admin/hris/employees');
    } catch (error) {
      logger.error('Failed to save employee:', error);
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
        title={isEdit ? 'Edit Employee' : 'New Employee'}
        subtitle={
          isEdit ? 'Update employee details' : 'Add a new employee to the system'
        }
        breadcrumbs={[
          { label: 'Employees', to: '/admin/hris/employees' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <Tabs defaultValue="personal" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="personal">Personal Info</TabsTrigger>
            <TabsTrigger value="employment">Employment</TabsTrigger>
            <TabsTrigger value="contact">Contact & Address</TabsTrigger>
            <TabsTrigger value="statutory">Statutory</TabsTrigger>
          </TabsList>

          {/* Personal Information Tab */}
          <TabsContent value="personal" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Personal Information</CardTitle>
                <CardDescription>Basic personal details of the employee</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-6">
                <div className="grid gap-4 md:grid-cols-4">
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
                    <Label htmlFor="employee_code">Employee Code</Label>
                    <Input
                      id="employee_code"
                      {...register('employee_code')}
                      placeholder="Auto-generated if empty"
                      disabled={isEdit}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="salutation">Salutation</Label>
                    <Select
                      value={watch('salutation') || ''}
                      onValueChange={(value) => setValue('salutation', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select" />
                      </SelectTrigger>
                      <SelectContent>
                        {SALUTATION_OPTIONS.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="gender">Gender *</Label>
                    <Select
                      value={watch('gender') || ''}
                      onValueChange={(value) => setValue('gender', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select gender" />
                      </SelectTrigger>
                      <SelectContent>
                        {GENDER_OPTIONS.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="first_name">First Name *</Label>
                    <Input
                      id="first_name"
                      {...register('first_name', { required: 'First name is required' })}
                      placeholder="John"
                    />
                    {errors.first_name && (
                      <p className="text-sm text-red-500">{errors.first_name.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="middle_name">Middle Name</Label>
                    <Input id="middle_name" {...register('middle_name')} placeholder="William" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="last_name">Last Name *</Label>
                    <Input
                      id="last_name"
                      {...register('last_name', { required: 'Last name is required' })}
                      placeholder="Doe"
                    />
                    {errors.last_name && (
                      <p className="text-sm text-red-500">{errors.last_name.message}</p>
                    )}
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-4">
                  <div className="space-y-2">
                    <Label htmlFor="date_of_birth">Date of Birth *</Label>
                    <Input
                      id="date_of_birth"
                      type="date"
                      {...register('date_of_birth', { required: 'Date of birth is required' })}
                    />
                    {errors.date_of_birth && (
                      <p className="text-sm text-red-500">{errors.date_of_birth.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="blood_group">Blood Group</Label>
                    <Select
                      value={watch('blood_group') || ''}
                      onValueChange={(value) => setValue('blood_group', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select" />
                      </SelectTrigger>
                      <SelectContent>
                        {BLOOD_GROUP_OPTIONS.map((bg) => (
                          <SelectItem key={bg} value={bg}>
                            {bg}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="marital_status">Marital Status</Label>
                    <Select
                      value={watch('marital_status') || ''}
                      onValueChange={(value) => setValue('marital_status', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select" />
                      </SelectTrigger>
                      <SelectContent>
                        {MARITAL_STATUS_OPTIONS.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="nationality">Nationality</Label>
                    <Input id="nationality" {...register('nationality')} placeholder="Indian" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Employment Tab */}
          <TabsContent value="employment" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Employment Details</CardTitle>
                <CardDescription>Job role and organizational structure</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-6">
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
                    <Label htmlFor="designation_id">Designation</Label>
                    <Select
                      value={watch('designation_id') || '__none__'}
                      onValueChange={(value) => setValue('designation_id', value === '__none__' ? '' : value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select designation" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__none__">None</SelectItem>
                        {designations.map((desig) => (
                          <SelectItem key={desig.id} value={desig.id}>
                            {desig.title}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="unit_id">Unit / Location</Label>
                    <Select
                      value={watch('unit_id') || '__none__'}
                      onValueChange={(value) => setValue('unit_id', value === '__none__' ? '' : value)}
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

                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="reporting_manager_id">Reporting Manager</Label>
                    <Select
                      value={watch('reporting_manager_id') || '__none__'}
                      onValueChange={(value) => setValue('reporting_manager_id', value === '__none__' ? '' : value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select manager" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__none__">None</SelectItem>
                        {managers.map((mgr) => (
                          <SelectItem key={mgr.id} value={mgr.id}>
                            {mgr.full_name} ({mgr.employee_code})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="shift_id">Shift</Label>
                    <Select
                      value={watch('shift_id') || '__none__'}
                      onValueChange={(value) => setValue('shift_id', value === '__none__' ? '' : value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select shift" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__none__">None</SelectItem>
                        {shifts.map((shift) => (
                          <SelectItem key={shift.id} value={shift.id}>
                            {shift.shift_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="notice_period_days">Notice Period (Days)</Label>
                    <Input
                      id="notice_period_days"
                      type="number"
                      {...register('notice_period_days', { valueAsNumber: true })}
                    />
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-4">
                  <div className="space-y-2">
                    <Label htmlFor="date_of_joining">Date of Joining *</Label>
                    <Input
                      id="date_of_joining"
                      type="date"
                      {...register('date_of_joining', { required: 'Joining date is required' })}
                    />
                    {errors.date_of_joining && (
                      <p className="text-sm text-red-500">{errors.date_of_joining.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="probation_end_date">Probation End Date</Label>
                    <Input id="probation_end_date" type="date" {...register('probation_end_date')} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="confirmation_date">Confirmation Date</Label>
                    <Input id="confirmation_date" type="date" {...register('confirmation_date')} />
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="employment_type">Employment Type *</Label>
                    <Select
                      value={watch('employment_type') || 'PERMANENT'}
                      onValueChange={(value) => setValue('employment_type', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        {EMPLOYMENT_TYPE_OPTIONS.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="employment_status">Employment Status *</Label>
                    <Select
                      value={watch('employment_status') || 'ACTIVE'}
                      onValueChange={(value) => setValue('employment_status', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select status" />
                      </SelectTrigger>
                      <SelectContent>
                        {EMPLOYMENT_STATUS_OPTIONS.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Contact & Address Tab */}
          <TabsContent value="contact" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Contact Information</CardTitle>
                <CardDescription>Phone numbers and email addresses</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-6">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="personal_mobile">Personal Mobile *</Label>
                    <Input
                      id="personal_mobile"
                      {...register('personal_mobile', { required: 'Personal mobile is required' })}
                      placeholder="+91 9876543210"
                    />
                    {errors.personal_mobile && (
                      <p className="text-sm text-red-500">{errors.personal_mobile.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="personal_email">Personal Email</Label>
                    <Input
                      id="personal_email"
                      type="email"
                      {...register('personal_email')}
                      placeholder="john.doe@gmail.com"
                    />
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="official_mobile">Official Mobile</Label>
                    <Input
                      id="official_mobile"
                      {...register('official_mobile')}
                      placeholder="+91 9876543210"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="official_email">Official Email</Label>
                    <Input
                      id="official_email"
                      type="email"
                      {...register('official_email')}
                      placeholder="john.doe@company.com"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Emergency Contact</CardTitle>
                <CardDescription>Person to contact in case of emergency</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-6">
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="emergency_contact_name">Contact Name</Label>
                    <Input
                      id="emergency_contact_name"
                      {...register('emergency_contact_name')}
                      placeholder="Jane Doe"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="emergency_contact_phone">Contact Phone</Label>
                    <Input
                      id="emergency_contact_phone"
                      {...register('emergency_contact_phone')}
                      placeholder="+91 9876543210"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="emergency_contact_relation">Relationship</Label>
                    <Input
                      id="emergency_contact_relation"
                      {...register('emergency_contact_relation')}
                      placeholder="Spouse / Parent"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Current Address</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-6">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Address Line 1</Label>
                    <Input {...register('current_address.line1')} placeholder="123 Main Street" />
                  </div>
                  <div className="space-y-2">
                    <Label>Address Line 2</Label>
                    <Input {...register('current_address.line2')} placeholder="Apt 4B" />
                  </div>
                </div>
                <div className="grid gap-4 md:grid-cols-4">
                  <div className="space-y-2">
                    <Label>City</Label>
                    <Input {...register('current_address.city')} placeholder="Mumbai" />
                  </div>
                  <div className="space-y-2">
                    <Label>State</Label>
                    <Input {...register('current_address.state')} placeholder="Maharashtra" />
                  </div>
                  <div className="space-y-2">
                    <Label>PIN Code</Label>
                    <Input {...register('current_address.pincode')} placeholder="400001" />
                  </div>
                  <div className="space-y-2">
                    <Label>Country</Label>
                    <Input {...register('current_address.country')} placeholder="India" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Permanent Address</CardTitle>
                <CardDescription>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      {...register('is_address_same')}
                      className="h-4 w-4"
                    />
                    Same as current address
                  </label>
                </CardDescription>
              </CardHeader>
              {!isAddressSame && (
                <CardContent className="grid gap-6">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label>Address Line 1</Label>
                      <Input {...register('permanent_address.line1')} placeholder="123 Main Street" />
                    </div>
                    <div className="space-y-2">
                      <Label>Address Line 2</Label>
                      <Input {...register('permanent_address.line2')} placeholder="Apt 4B" />
                    </div>
                  </div>
                  <div className="grid gap-4 md:grid-cols-4">
                    <div className="space-y-2">
                      <Label>City</Label>
                      <Input {...register('permanent_address.city')} placeholder="Mumbai" />
                    </div>
                    <div className="space-y-2">
                      <Label>State</Label>
                      <Input {...register('permanent_address.state')} placeholder="Maharashtra" />
                    </div>
                    <div className="space-y-2">
                      <Label>PIN Code</Label>
                      <Input {...register('permanent_address.pincode')} placeholder="400001" />
                    </div>
                    <div className="space-y-2">
                      <Label>Country</Label>
                      <Input {...register('permanent_address.country')} placeholder="India" />
                    </div>
                  </div>
                </CardContent>
              )}
            </Card>
          </TabsContent>

          {/* Statutory Tab */}
          <TabsContent value="statutory" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Identity Documents</CardTitle>
                <CardDescription>Government issued IDs and statutory numbers</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-6">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="pan_number">PAN Number</Label>
                    <Input
                      id="pan_number"
                      {...register('pan_number')}
                      placeholder="ABCDE1234F"
                      maxLength={10}
                      style={{ textTransform: 'uppercase' }}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="aadhaar_number">Aadhaar Number</Label>
                    <Input
                      id="aadhaar_number"
                      {...register('aadhaar_number')}
                      placeholder="1234 5678 9012"
                      maxLength={12}
                    />
                  </div>
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="uan_number">UAN (PF Account)</Label>
                    <Input
                      id="uan_number"
                      {...register('uan_number')}
                      placeholder="100XXXXXXXXX"
                      maxLength={12}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="esic_number">ESIC Number</Label>
                    <Input
                      id="esic_number"
                      {...register('esic_number')}
                      placeholder="ESIC Number"
                      maxLength={17}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Form Actions */}
        <div className="flex items-center justify-end gap-4">
          <Button type="button" variant="outline" onClick={() => navigate('/admin/hris/employees')}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Save className="mr-2 h-4 w-4" />
            {isEdit ? 'Update Employee' : 'Create Employee'}
          </Button>
        </div>
      </form>
    </div>
  );
}
