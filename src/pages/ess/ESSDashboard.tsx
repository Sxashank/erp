/**
 * ESS Portal Dashboard
 * Employee home page with summary widgets
 */

import {
  User,
  Calendar,
  FileText,
  Receipt,
  HelpCircle,
  Calculator,
  Clock,
  Download,
  ChevronRight,
  Bell,
  TrendingUp,
  Loader2,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { essProfileApi } from '@/services/essApi';
import { useEssAuthStore } from '@/stores/essAuthStore';
import type { ESSDashboard, ESSUser } from '@/types/ess';

import { logger } from '@/lib/logger';
export default function ESSDashboardPage() {
  const navigate = useNavigate();
  const accessToken = useEssAuthStore((state) => state.accessToken);
  const sessionUser = useEssAuthStore((state) => state.user);
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState<ESSDashboard | null>(null);
  const [user, setUser] = useState<ESSUser | null>(null);

  useEffect(() => {
    if (!accessToken) {
      navigate('/ess/login');
      return;
    }

    setUser(sessionUser as ESSUser | null);

    fetchDashboard();
  }, [accessToken, navigate, sessionUser]);

  const fetchDashboard = async () => {
    try {
      const response = await essProfileApi.getDashboard();
      setDashboard(response.data);
    } catch (error) {
      logger.error('Failed to fetch dashboard:', error);
    } finally {
      setLoading(false);
    }
  };
  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const quickLinks = [
    { label: 'My Profile', icon: User, href: '/ess/profile', color: 'bg-blue-100 text-blue-600' },
    {
      label: 'Payslips',
      icon: FileText,
      href: '/ess/payslips',
      color: 'bg-green-100 text-green-600',
    },
    {
      label: 'Reimbursements',
      icon: Receipt,
      href: '/ess/reimbursements',
      color: 'bg-orange-100 text-orange-600',
    },
    {
      label: 'Helpdesk',
      icon: HelpCircle,
      href: '/ess/helpdesk',
      color: 'bg-purple-100 text-purple-600',
    },
    {
      label: 'IT Declaration',
      icon: Calculator,
      href: '/ess/it-declaration',
      color: 'bg-pink-100 text-pink-600',
    },
    {
      label: 'Attendance',
      icon: Clock,
      href: '/ess/attendance',
      color: 'bg-cyan-100 text-cyan-600',
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Welcome, ${dashboard?.employee?.name || user?.employee_name || 'Employee'}!`}
        subtitle={`${dashboard?.employee?.designation ?? ''} • ${dashboard?.employee?.department ?? ''} • Employee ID: ${dashboard?.employee?.employee_code || user?.employee_code || ''}`}
        actions={
          <Button variant="outline" size="sm">
            <Bell className="mr-2 h-4 w-4" />
            Notifications
          </Button>
        }
      />

      {/* Quick Links */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
        {quickLinks.map((link) => (
          <Link key={link.href} to={link.href}>
            <Card className="cursor-pointer transition-shadow hover:shadow-md">
              <CardContent className="p-4 text-center">
                <div className={`inline-flex rounded-xl p-3 ${link.color} mb-2`}>
                  <link.icon className="h-5 w-5" />
                </div>
                <p className="text-sm font-medium">{link.label}</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left Column - Attendance & Leave */}
        <div className="space-y-6">
          {/* Attendance Summary */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <Calendar className="h-4 w-4" />
                Attendance - {dashboard?.attendance?.current_month || 'This Month'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-lg bg-green-50 p-3 text-center">
                  <p className="text-2xl font-bold text-green-600">
                    {dashboard?.attendance?.present_days || 0}
                  </p>
                  <p className="text-xs text-gray-500">Present</p>
                </div>
                <div className="rounded-lg bg-red-50 p-3 text-center">
                  <p className="text-2xl font-bold text-red-600">
                    {dashboard?.attendance?.absent_days || 0}
                  </p>
                  <p className="text-xs text-gray-500">Absent</p>
                </div>
                <div className="rounded-lg bg-blue-50 p-3 text-center">
                  <p className="text-2xl font-bold text-blue-600">
                    {dashboard?.attendance?.leave_days || 0}
                  </p>
                  <p className="text-xs text-gray-500">Leave</p>
                </div>
                <div className="rounded-lg bg-purple-50 p-3 text-center">
                  <p className="text-2xl font-bold text-purple-600">
                    {dashboard?.attendance?.wfh_days || 0}
                  </p>
                  <p className="text-xs text-gray-500">WFH</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Leave Balance */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Leave Balance</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="mb-1 flex justify-between text-sm">
                  <span>Casual Leave</span>
                  <span className="font-medium">
                    {dashboard?.leave_balance?.casual_leave || 0} days
                  </span>
                </div>
                <Progress
                  value={((dashboard?.leave_balance?.casual_leave || 0) / 12) * 100}
                  className="h-2"
                />
              </div>
              <div>
                <div className="mb-1 flex justify-between text-sm">
                  <span>Sick Leave</span>
                  <span className="font-medium">
                    {dashboard?.leave_balance?.sick_leave || 0} days
                  </span>
                </div>
                <Progress
                  value={((dashboard?.leave_balance?.sick_leave || 0) / 12) * 100}
                  className="h-2"
                />
              </div>
              <div>
                <div className="mb-1 flex justify-between text-sm">
                  <span>Earned Leave</span>
                  <span className="font-medium">
                    {dashboard?.leave_balance?.earned_leave || 0} days
                  </span>
                </div>
                <Progress
                  value={((dashboard?.leave_balance?.earned_leave || 0) / 30) * 100}
                  className="h-2"
                />
              </div>
              <div className="border-t pt-2">
                <div className="flex justify-between">
                  <span className="font-medium">Total Available</span>
                  <span className="font-bold text-blue-600">
                    {dashboard?.leave_balance?.total_available || 0} days
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Middle Column - Pending Actions & Recent Payslip */}
        <div className="space-y-6">
          {/* Pending Actions */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Pending Actions</CardTitle>
              <CardDescription>Items requiring your attention</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {(dashboard?.pending_actions?.pending_claims ?? 0) > 0 && (
                <Link
                  to="/ess/reimbursements"
                  className="flex items-center justify-between rounded-lg bg-orange-50 p-3 hover:bg-orange-100"
                >
                  <div className="flex items-center gap-3">
                    <Receipt className="h-5 w-5 text-orange-600" />
                    <span className="text-sm">Pending Reimbursement Claims</span>
                  </div>
                  <Badge variant="secondary">
                    {dashboard?.pending_actions?.pending_claims ?? 0}
                  </Badge>
                </Link>
              )}
              {(dashboard?.pending_actions?.pending_tickets ?? 0) > 0 && (
                <Link
                  to="/ess/helpdesk"
                  className="flex items-center justify-between rounded-lg bg-purple-50 p-3 hover:bg-purple-100"
                >
                  <div className="flex items-center gap-3">
                    <HelpCircle className="h-5 w-5 text-purple-600" />
                    <span className="text-sm">Open Helpdesk Tickets</span>
                  </div>
                  <Badge variant="secondary">
                    {dashboard?.pending_actions?.pending_tickets ?? 0}
                  </Badge>
                </Link>
              )}
              {(dashboard?.pending_actions?.pending_regularizations ?? 0) > 0 && (
                <Link
                  to="/ess/attendance"
                  className="flex items-center justify-between rounded-lg bg-cyan-50 p-3 hover:bg-cyan-100"
                >
                  <div className="flex items-center gap-3">
                    <Clock className="h-5 w-5 text-cyan-600" />
                    <span className="text-sm">Pending Regularizations</span>
                  </div>
                  <Badge variant="secondary">
                    {dashboard?.pending_actions?.pending_regularizations ?? 0}
                  </Badge>
                </Link>
              )}
              {(dashboard?.pending_actions?.pending_declarations ?? 0) > 0 && (
                <Link
                  to="/ess/it-declaration"
                  className="flex items-center justify-between rounded-lg bg-pink-50 p-3 hover:bg-pink-100"
                >
                  <div className="flex items-center gap-3">
                    <Calculator className="h-5 w-5 text-pink-600" />
                    <span className="text-sm">Complete IT Declaration</span>
                  </div>
                  <Badge variant="secondary">
                    {dashboard?.pending_actions?.pending_declarations ?? 0}
                  </Badge>
                </Link>
              )}
              {Object.values(dashboard?.pending_actions || {}).every((v) => v === 0) && (
                <div className="py-4 text-center text-gray-500">
                  <TrendingUp className="mx-auto mb-2 h-8 w-8 text-green-500" />
                  <p className="text-sm">All caught up! No pending actions.</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recent Payslip */}
          {dashboard?.recent_payslip && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <FileText className="h-4 w-4" />
                  Latest Payslip
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between rounded-lg bg-green-50 p-4">
                  <div>
                    <p className="text-sm text-gray-500">{dashboard.recent_payslip.month}</p>
                    <p className="text-2xl font-bold text-green-700">
                      {formatIndianCompactCurrency(dashboard.recent_payslip.net_salary)}
                    </p>
                    <p className="text-xs text-gray-500">Net Salary</p>
                  </div>
                  <Button variant="outline" size="sm">
                    <Download className="mr-2 h-4 w-4" />
                    Download
                  </Button>
                </div>
                <Link
                  to="/ess/payslips"
                  className="mt-4 flex items-center justify-center gap-1 text-sm text-blue-600 hover:underline"
                >
                  View all payslips
                  <ChevronRight className="h-4 w-4" />
                </Link>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Column - Announcements */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <Bell className="h-4 w-4" />
                Announcements
              </CardTitle>
            </CardHeader>
            <CardContent>
              {dashboard?.announcements && dashboard.announcements.length > 0 ? (
                <div className="space-y-4">
                  {dashboard.announcements.map((announcement) => (
                    <div key={announcement.id} className="rounded-lg border p-3">
                      <h4 className="text-sm font-medium">{announcement.title}</h4>
                      <p className="mt-1 text-xs text-gray-500">{announcement.message}</p>
                      <p className="mt-2 text-xs text-gray-400">
                        <DateDisplay date={announcement.created_at} />
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-8 text-center text-gray-500">
                  <Bell className="mx-auto mb-2 h-8 w-8 opacity-50" />
                  <p className="text-sm">No announcements</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Stats */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Quick Stats</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between rounded-lg bg-gray-50 p-3">
                  <span className="text-sm text-gray-600">Total Claims (YTD)</span>
                  <span className="font-medium">12</span>
                </div>
                <div className="flex items-center justify-between rounded-lg bg-gray-50 p-3">
                  <span className="text-sm text-gray-600">Total Reimbursed</span>
                  <span className="font-medium">{formatIndianCompactCurrency(45000)}</span>
                </div>
                <div className="flex items-center justify-between rounded-lg bg-gray-50 p-3">
                  <span className="text-sm text-gray-600">Tickets Raised</span>
                  <span className="font-medium">5</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
