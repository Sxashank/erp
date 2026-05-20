import {
  Edit,
  Eye,
  MoreHorizontal,
  Plus,
  Search,
  Trash2,
  Users,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { HrisConfirmDialog } from '@/components/hris/HrisConfirmDialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
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
import { hrisApi, organizationsApi, departmentsApi, designationsApi } from '@/services/api';

import { logger } from "@/lib/logger";
interface Employee {
  id: string;
  employeeCode: string;
  firstName: string;
  middleName?: string;
  lastName: string;
  fullName: string;
  personalMobile: string;
  officialEmail?: string;
  departmentName?: string;
  designationName?: string;
  employmentType: string;
  employmentStatus: string;
  dateOfJoining: string;
}

interface Organization {
  id: string;
  name: string;
}

interface Department {
  id: string;
  name: string;
}

interface Designation {
  id: string;
  title: string;
}

const EMPLOYMENT_STATUS_OPTIONS = [
  { value: '__all__', label: 'All Statuses' },
  { value: 'ACTIVE', label: 'Active' },
  { value: 'PROBATION', label: 'Probation' },
  { value: 'NOTICE_PERIOD', label: 'Notice Period' },
  { value: 'RELIEVED', label: 'Relieved' },
  { value: 'SUSPENDED', label: 'Suspended' },
];

const EMPLOYMENT_TYPE_OPTIONS = [
  { value: '__all__', label: 'All Types' },
  { value: 'PERMANENT', label: 'Permanent' },
  { value: 'CONTRACT', label: 'Contract' },
  { value: 'PROBATION', label: 'Probation' },
  { value: 'INTERN', label: 'Intern' },
  { value: 'TRAINEE', label: 'Trainee' },
  { value: 'CONSULTANT', label: 'Consultant' },
];

const getStatusBadgeColor = (status: string) => {
  switch (status) {
    case 'ACTIVE':
      return 'bg-emerald-50 text-emerald-700';
    case 'PROBATION':
      return 'bg-amber-50 text-amber-700';
    case 'NOTICE_PERIOD':
      return 'bg-orange-50 text-orange-700';
    case 'RELIEVED':
      return 'bg-slate-100 text-slate-600';
    case 'SUSPENDED':
      return 'bg-red-50 text-red-700';
    default:
      return 'bg-slate-100 text-slate-600';
  }
};

export function EmployeeList() {
  const navigate = useNavigate();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [designations, setDesignations] = useState<Designation[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleteEmployeeId, setDeleteEmployeeId] = useState<string | null>(null);
  const [deleteBusy, setDeleteBusy] = useState(false);
  const [pagination, setPagination] = useState({ skip: 0, limit: 20, total: 0 });

  // Filters
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [selectedDeptId, setSelectedDeptId] = useState<string>('__all__');
  const [selectedDesigId, setSelectedDesigId] = useState<string>('__all__');
  const [selectedStatus, setSelectedStatus] = useState<string>('__all__');
  const [selectedType, setSelectedType] = useState<string>('__all__');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Fetch organizations on mount
  useEffect(() => {
    const fetchOrganizations = async () => {
      try {
        const response = await organizationsApi.list({ pageSize: 100 });
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

  // Fetch departments when org changes
  useEffect(() => {
    const fetchDepartments = async () => {
      if (!selectedOrgId) {
        setDepartments([]);
        return;
      }
      try {
        const response = await departmentsApi.list({ pageSize: 100 });
        setDepartments(response.data.items || []);
      } catch (error) {
        logger.error('Failed to fetch departments:', error);
      }
    };
    fetchDepartments();
  }, [selectedOrgId]);

  // Fetch designations when dept changes
  useEffect(() => {
    const fetchDesignations = async () => {
      if (selectedDeptId === '__all__') {
        setDesignations([]);
        return;
      }
      try {
        const response = await designationsApi.list({ departmentId: selectedDeptId, pageSize: 100 });
        setDesignations(response.data.items || []);
      } catch (error) {
        logger.error('Failed to fetch designations:', error);
      }
    };
    fetchDesignations();
  }, [selectedDeptId]);

  // Fetch employees
  const fetchEmployees = async (skip = 0) => {
    if (!selectedOrgId) return;
    try {
      setLoading(true);
      const params: Record<string, unknown> = {
        skip,
        limit: pagination.limit,
      };
      if (selectedDeptId !== '__all__') params.department_id = selectedDeptId;
      if (selectedDesigId !== '__all__') params.designation_id = selectedDesigId;
      if (selectedStatus !== '__all__') params.employment_status = selectedStatus;
      if (selectedType !== '__all__') params.employment_type = selectedType;
      if (searchQuery) params.search = searchQuery;

      const response = await hrisApi.listEmployees(params);
      setEmployees(response.data.items || []);
      setPagination((prev) => ({ ...prev, skip, total: response.data.total || 0 }));
    } catch (error) {
      logger.error('Failed to fetch employees:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployees(0);
  }, [selectedOrgId, selectedDeptId, selectedDesigId, selectedStatus, selectedType]);

  const handleSearch = () => {
    fetchEmployees(0);
  };

  const executeDelete = async () => {
    if (!deleteEmployeeId) return;
    try {
      setDeleteBusy(true);
      await hrisApi.deleteEmployee(deleteEmployeeId);
      setDeleteEmployeeId(null);
      fetchEmployees(pagination.skip);
    } catch (error) {
      logger.error('Failed to delete employee:', error);
    } finally {
      setDeleteBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Employees"
        subtitle="Manage employee records"
        actions={
          <Button onClick={() => navigate('/admin/hris/employees/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Employee
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Employee Directory
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {/* Filters */}
          <div className="grid gap-4 md:grid-cols-6 mb-6">
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

            <Select value={selectedDeptId} onValueChange={(v) => { setSelectedDeptId(v); setSelectedDesigId('__all__'); }}>
              <SelectTrigger>
                <SelectValue placeholder="Department" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">All Departments</SelectItem>
                {departments.map((dept) => (
                  <SelectItem key={dept.id} value={dept.id}>
                    {dept.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={selectedDesigId} onValueChange={setSelectedDesigId}>
              <SelectTrigger>
                <SelectValue placeholder="Designation" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">All Designations</SelectItem>
                {designations.map((desig) => (
                  <SelectItem key={desig.id} value={desig.id}>
                    {desig.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={selectedStatus} onValueChange={setSelectedStatus}>
              <SelectTrigger>
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                {EMPLOYMENT_STATUS_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={selectedType} onValueChange={setSelectedType}>
              <SelectTrigger>
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                {EMPLOYMENT_TYPE_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <div className="flex gap-2">
              <Input
                placeholder="Search..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              />
              <Button variant="outline" size="icon" onClick={handleSearch}>
                <Search className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Table */}
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-sm text-slate-500">Loading...</p>
            </div>
          ) : employees.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <Users className="h-12 w-12 text-slate-300 mb-4" />
              <p className="text-sm text-slate-500">No employees found</p>
              <Button variant="link" onClick={() => navigate('/admin/hris/employees/new')}>
                Add your first employee
              </Button>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Employee Code</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Department</TableHead>
                    <TableHead>Designation</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Joining Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="w-[70px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {employees.map((emp) => (
                    <TableRow key={emp.id}>
                      <TableCell className="font-medium">{emp.employeeCode}</TableCell>
                      <TableCell>
                        <div>
                          <p className="font-medium">{emp.fullName}</p>
                          <p className="text-xs text-slate-500">{emp.officialEmail || emp.personalMobile}</p>
                        </div>
                      </TableCell>
                      <TableCell>{emp.departmentName || '-'}</TableCell>
                      <TableCell>{emp.designationName || '-'}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{emp.employmentType}</Badge>
                      </TableCell>
                      <TableCell><DateDisplay date={emp.dateOfJoining} /></TableCell>
                      <TableCell>
                        <Badge className={getStatusBadgeColor(emp.employmentStatus)}>
                          {emp.employmentStatus}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => navigate(`/admin/hris/employees/${emp.id}`)}>
                              <Eye className="mr-2 h-4 w-4" />
                              View
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => navigate(`/admin/hris/employees/${emp.id}/edit`)}>
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => setDeleteEmployeeId(emp.id)}
                              className="text-red-600"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              <div className="mt-4 flex items-center justify-between">
                <p className="text-sm text-slate-500">
                  Showing {employees.length} of {pagination.total} employees
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={pagination.skip === 0}
                    onClick={() => fetchEmployees(pagination.skip - pagination.limit)}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={pagination.skip + pagination.limit >= pagination.total}
                    onClick={() => fetchEmployees(pagination.skip + pagination.limit)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
      <HrisConfirmDialog
        open={Boolean(deleteEmployeeId)}
        title="Delete employee"
        description="This removes the employee record from active HRIS workflows. Continue only if this is not part of an audited lifecycle action."
        confirmLabel="Delete employee"
        destructive
        busy={deleteBusy}
        onOpenChange={(open) => {
          if (!open && !deleteBusy) setDeleteEmployeeId(null);
        }}
        onConfirm={executeDelete}
      />
    </div>
  );
}
