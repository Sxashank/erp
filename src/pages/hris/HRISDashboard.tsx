import {
  AlertTriangle,
  ArrowRight,
  Award,
  Briefcase,
  Calendar,
  CalendarCheck,
  CheckCircle,
  Clock,
  DollarSign,
  FileText,
  GraduationCap,
  Heart,
  TrendingUp,
  UserCheck,
  UserMinus,
  Users,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { organizationsApi } from '@/services/api';
import type { Organization, PaginatedResponse } from '@/types';

import { logger } from "@/lib/logger";
interface DashboardStats {
  totalEmployees: number;
  activeEmployees: number;
  newJoineesThisMonth: number;
  separationsThisMonth: number;
  pendingLeaveApprovals: number;
  pendingRegularizations: number;
  todayPresent: number;
  todayAbsent: number;
  todayOnLeave: number;
  attendancePercentage: number;
  upcomingTrainings: number;
  activeCycles: number;
  pendingGoals: number;
  pendingAppraisals: number;
}

interface PendingAction {
  id: string;
  type: 'LEAVE' | 'REGULARIZATION' | 'SEPARATION' | 'APPRAISAL' | 'TRAINING';
  title: string;
  employee: string;
  requestDate: string;
  status: string;
}

interface UpcomingEvent {
  id: string;
  type: 'HOLIDAY' | 'BIRTHDAY' | 'ANNIVERSARY' | 'TRAINING' | 'APPRAISAL_DUE';
  title: string;
  date: string;
  count?: number;
}

export function HRISDashboard() {
  const navigate = useNavigate();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats>({
    totalEmployees: 0,
    activeEmployees: 0,
    newJoineesThisMonth: 0,
    separationsThisMonth: 0,
    pendingLeaveApprovals: 0,
    pendingRegularizations: 0,
    todayPresent: 0,
    todayAbsent: 0,
    todayOnLeave: 0,
    attendancePercentage: 0,
    upcomingTrainings: 0,
    activeCycles: 0,
    pendingGoals: 0,
    pendingAppraisals: 0,
  });
  const [pendingActions, setPendingActions] = useState<PendingAction[]>([]);
  const [upcomingEvents, setUpcomingEvents] = useState<UpcomingEvent[]>([]);

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrgId) {
      fetchDashboardData();
    }
  }, [selectedOrgId]);

  const fetchOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      const data: PaginatedResponse<Organization> = response.data;
      setOrganizations(data.items);
      if (data.items.length > 0) {
        setSelectedOrgId(data.items[0].id);
      }
    } catch (error) {
      logger.error('Failed to fetch organizations:', error);
    }
  };

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setStats({
        totalEmployees: 0,
        activeEmployees: 0,
        newJoineesThisMonth: 0,
        separationsThisMonth: 0,
        pendingLeaveApprovals: 0,
        pendingRegularizations: 0,
        todayPresent: 0,
        todayAbsent: 0,
        todayOnLeave: 0,
        attendancePercentage: 0,
        upcomingTrainings: 0,
        activeCycles: 0,
        pendingGoals: 0,
        pendingAppraisals: 0,
      });
      setPendingActions([]);
      setUpcomingEvents([]);
    } catch (error) {
      logger.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'HOLIDAY':
        return <Calendar className="h-4 w-4 text-emerald-500" />;
      case 'BIRTHDAY':
        return <Heart className="h-4 w-4 text-pink-500" />;
      case 'ANNIVERSARY':
        return <Award className="h-4 w-4 text-purple-500" />;
      case 'TRAINING':
        return <GraduationCap className="h-4 w-4 text-blue-500" />;
      case 'APPRAISAL_DUE':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      default:
        return <Calendar className="h-4 w-4 text-slate-500" />;
    }
  };

  const getActionIcon = (type: string) => {
    switch (type) {
      case 'LEAVE':
        return <CalendarCheck className="h-4 w-4 text-blue-500" />;
      case 'REGULARIZATION':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'SEPARATION':
        return <UserMinus className="h-4 w-4 text-red-500" />;
      case 'APPRAISAL':
        return <TrendingUp className="h-4 w-4 text-purple-500" />;
      case 'TRAINING':
        return <GraduationCap className="h-4 w-4 text-emerald-500" />;
      default:
        return <FileText className="h-4 w-4 text-slate-500" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-slate-500">Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="HRIS Dashboard"
        subtitle="Human Resource Information System Overview"
        actions={
          <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
            <SelectTrigger className="w-[200px]">
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
        }
      />

      {/* Employee Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Employees</CardTitle>
            <Users className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalEmployees}</div>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span className="text-emerald-600">+{stats.newJoineesThisMonth} new</span>
              <span>|</span>
              <span className="text-red-600">-{stats.separationsThisMonth} exit</span>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Today&apos;s Attendance</CardTitle>
            <UserCheck className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600">{stats.attendancePercentage}%</div>
            <div className="flex items-center gap-2 text-xs">
              <Badge variant="outline" className="bg-emerald-50 text-emerald-700">
                {stats.todayPresent} Present
              </Badge>
              <Badge variant="outline" className="bg-red-50 text-red-700">
                {stats.todayAbsent} Absent
              </Badge>
              <Badge variant="outline" className="bg-blue-50 text-blue-700">
                {stats.todayOnLeave} Leave
              </Badge>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Approvals</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {stats.pendingLeaveApprovals + stats.pendingRegularizations}
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span>{stats.pendingLeaveApprovals} leave</span>
              <span>|</span>
              <span>{stats.pendingRegularizations} regularization</span>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Performance</CardTitle>
            <TrendingUp className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">{stats.activeCycles}</div>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span>Active cycle</span>
              <span>|</span>
              <span>{stats.pendingAppraisals} pending</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Quick Actions */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Pending Actions</CardTitle>
            <CardDescription>Items requiring your attention</CardDescription>
          </CardHeader>
          <CardContent>
            {pendingActions.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <CheckCircle className="mx-auto h-12 w-12 text-emerald-300 mb-2" />
                <p>No pending actions</p>
              </div>
            ) : (
              <div className="space-y-3">
                {pendingActions.map((action) => (
                  <div
                    key={action.id}
                    className="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 cursor-pointer"
                  >
                    <div className="flex items-center gap-3">
                      {getActionIcon(action.type)}
                      <div>
                        <p className="font-medium">{action.title}</p>
                        <p className="text-sm text-slate-500">
                          {action.employee} • <DateDisplay date={action.requestDate} />
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        className={
                          action.status === 'PENDING'
                            ? 'bg-yellow-50 text-yellow-700'
                            : 'bg-blue-50 text-blue-700'
                        }
                      >
                        {action.status}
                      </Badge>
                      <ArrowRight className="h-4 w-4 text-slate-400" />
                    </div>
                  </div>
                ))}
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => navigate('/admin/hris/leave-applications')}
                >
                  View All Pending
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Upcoming Events */}
        <Card>
          <CardHeader>
            <CardTitle>Upcoming Events</CardTitle>
            <CardDescription>Next 7 days</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {upcomingEvents.map((event) => (
                <div key={event.id} className="flex items-center gap-3">
                  {getEventIcon(event.type)}
                  <div className="flex-1">
                    <p className="font-medium text-sm">{event.title}</p>
                    <p className="text-xs text-slate-500"><DateDisplay date={event.date} /></p>
                  </div>
                  {event.count && (
                    <Badge variant="outline">{event.count}</Badge>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Links */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card
          className="cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => navigate('/admin/hris/employees')}
        >
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-blue-50 p-3">
                <Users className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold">Employees</h3>
                <p className="text-sm text-slate-500">Manage employee data</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => navigate('/admin/hris/attendance')}
        >
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-emerald-50 p-3">
                <CalendarCheck className="h-6 w-6 text-emerald-600" />
              </div>
              <div>
                <h3 className="font-semibold">Attendance</h3>
                <p className="text-sm text-slate-500">Track attendance</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => navigate('/admin/hris/leave-applications')}
        >
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-purple-50 p-3">
                <Briefcase className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <h3 className="font-semibold">Leave</h3>
                <p className="text-sm text-slate-500">Leave management</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => navigate('/admin/payroll/batches')}
        >
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-amber-50 p-3">
                <DollarSign className="h-6 w-6 text-amber-600" />
              </div>
              <div>
                <h3 className="font-semibold">Payroll</h3>
                <p className="text-sm text-slate-500">Process salaries</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Department Attendance */}
      <Card>
        <CardHeader>
          <CardTitle>Department-wise Attendance</CardTitle>
          <CardDescription>Today&apos;s attendance by department</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { name: 'Engineering', present: 45, total: 50, percentage: 90 },
              { name: 'Sales', present: 28, total: 32, percentage: 87.5 },
              { name: 'Operations', present: 38, total: 42, percentage: 90.5 },
              { name: 'Finance', present: 18, total: 20, percentage: 90 },
              { name: 'HR', present: 12, total: 14, percentage: 85.7 },
            ].map((dept) => (
              <div key={dept.name} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">{dept.name}</span>
                  <span className="text-slate-500">
                    {dept.present}/{dept.total} ({dept.percentage.toFixed(1)}%)
                  </span>
                </div>
                <Progress value={dept.percentage} className="h-2" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
