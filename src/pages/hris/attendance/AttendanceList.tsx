import {
  Calendar,
  Clock,
  Search,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
import { hrisApi, organizationsApi, departmentsApi } from '@/services/api';

import { logger } from "@/lib/logger";
interface Attendance {
  id: string;
  employeeId: string;
  employeeName?: string;
  employeeCode?: string;
  attendanceDate: string;
  shiftName?: string;
  scheduledIn?: string;
  scheduledOut?: string;
  firstIn?: string;
  lastOut?: string;
  status: string;
  totalWorkMinutes: number;
  lateMinutes: number;
  earlyLeaveMinutes: number;
  overtimeMinutes: number;
  isHoliday: boolean;
  isWeekOff: boolean;
  isRegularized: boolean;
}

interface Organization {
  id: string;
  name: string;
}

interface Department {
  id: string;
  name: string;
}

const STATUS_OPTIONS = [
  { value: '__all__', label: 'All Statuses' },
  { value: 'PRESENT', label: 'Present' },
  { value: 'ABSENT', label: 'Absent' },
  { value: 'HALF_DAY', label: 'Half Day' },
  { value: 'ON_LEAVE', label: 'On Leave' },
  { value: 'HOLIDAY', label: 'Holiday' },
  { value: 'WEEK_OFF', label: 'Week Off' },
];

const getStatusBadgeColor = (status: string) => {
  switch (status) {
    case 'PRESENT':
      return 'bg-green-50 text-green-700';
    case 'ABSENT':
      return 'bg-red-50 text-red-700';
    case 'HALF_DAY':
      return 'bg-amber-50 text-amber-700';
    case 'ON_LEAVE':
      return 'bg-blue-50 text-blue-700';
    case 'HOLIDAY':
      return 'bg-purple-50 text-purple-700';
    case 'WEEK_OFF':
      return 'bg-slate-100 text-slate-600';
    default:
      return 'bg-slate-100 text-slate-600';
  }
};

const formatTime = (time: string | null | undefined) => {
  if (!time) return '-';
  const [hours, minutes] = time.split(':');
  const h = parseInt(hours, 10);
  const ampm = h >= 12 ? 'PM' : 'AM';
  const displayHour = h % 12 || 12;
  return `${displayHour}:${minutes} ${ampm}`;
};

const formatMinutes = (minutes: number) => {
  if (!minutes) return '-';
  const hrs = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hrs > 0) {
    return `${hrs}h ${mins}m`;
  }
  return `${mins}m`;
};

export function AttendanceList() {
  const navigate = useNavigate();
  const [attendance, setAttendance] = useState<Attendance[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ skip: 0, limit: 20, total: 0 });

  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [selectedDeptId, setSelectedDeptId] = useState<string>('__all__');
  const [selectedStatus, setSelectedStatus] = useState<string>('__all__');
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [searchQuery, setSearchQuery] = useState<string>('');

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

  const fetchAttendance = async (skip = 0) => {
    if (!selectedOrgId) return;
    try {
      setLoading(true);
      const params: Record<string, unknown> = {
        date: selectedDate,
        skip,
        limit: pagination.limit,
      };
      if (selectedDeptId !== '__all__') params.department_id = selectedDeptId;
      if (selectedStatus !== '__all__') params.status = selectedStatus;
      if (searchQuery) params.search = searchQuery;

      const response = await hrisApi.listAttendance(params);
      setAttendance(response.data.items || []);
      setPagination((prev) => ({ ...prev, skip, total: response.data.total || 0 }));
    } catch (error) {
      logger.error('Failed to fetch attendance:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAttendance(0);
  }, [selectedOrgId, selectedDeptId, selectedStatus, selectedDate]);

  const handleSearch = () => {
    fetchAttendance(0);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Attendance"
        subtitle="Daily attendance records"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigate('/admin/hris/attendance/regularization')}>
              Regularization Requests
            </Button>
            <Button onClick={() => navigate('/admin/hris/attendance/process')}>
              Process Attendance
            </Button>
          </div>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Attendance Records
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

            <Select value={selectedDeptId} onValueChange={setSelectedDeptId}>
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

            <Select value={selectedStatus} onValueChange={setSelectedStatus}>
              <SelectTrigger>
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                {STATUS_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
            />

            <div className="flex gap-2 md:col-span-2">
              <Input
                placeholder="Search by name or code..."
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
          ) : attendance.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <Calendar className="h-12 w-12 text-slate-300 mb-4" />
              <p className="text-sm text-slate-500">No attendance records found</p>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Employee</TableHead>
                    <TableHead>Shift</TableHead>
                    <TableHead>In Time</TableHead>
                    <TableHead>Out Time</TableHead>
                    <TableHead>Work Hours</TableHead>
                    <TableHead>Late</TableHead>
                    <TableHead>Early Leave</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Regularized</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {attendance.map((record) => (
                    <TableRow key={record.id}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{record.employeeName}</p>
                          <p className="text-xs text-slate-500">{record.employeeCode}</p>
                        </div>
                      </TableCell>
                      <TableCell>{record.shiftName || '-'}</TableCell>
                      <TableCell>
                        <div>
                          <p className="font-medium">{formatTime(record.firstIn)}</p>
                          <p className="text-xs text-slate-500">Scheduled: {formatTime(record.scheduledIn)}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="font-medium">{formatTime(record.lastOut)}</p>
                          <p className="text-xs text-slate-500">Scheduled: {formatTime(record.scheduledOut)}</p>
                        </div>
                      </TableCell>
                      <TableCell>{formatMinutes(record.totalWorkMinutes)}</TableCell>
                      <TableCell>
                        {record.lateMinutes > 0 ? (
                          <span className="text-amber-600">{formatMinutes(record.lateMinutes)}</span>
                        ) : (
                          '-'
                        )}
                      </TableCell>
                      <TableCell>
                        {record.earlyLeaveMinutes > 0 ? (
                          <span className="text-orange-600">{formatMinutes(record.earlyLeaveMinutes)}</span>
                        ) : (
                          '-'
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge className={getStatusBadgeColor(record.status)}>
                          {record.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {record.isRegularized && (
                          <Badge variant="outline" className="text-blue-600">
                            Regularized
                          </Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              <div className="mt-4 flex items-center justify-between">
                <p className="text-sm text-slate-500">
                  Showing {attendance.length} of {pagination.total} records
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={pagination.skip === 0}
                    onClick={() => fetchAttendance(pagination.skip - pagination.limit)}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={pagination.skip + pagination.limit >= pagination.total}
                    onClick={() => fetchAttendance(pagination.skip + pagination.limit)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
