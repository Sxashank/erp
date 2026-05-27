/**
 * Legal Module Dashboard
 * Overview of legal cases, hearings, auctions, and expenses
 */

import {
  Briefcase,
  Scale,
  Gavel,
  Calendar,
  IndianRupee,
  AlertTriangle,
  Clock,
  ChevronRight,
  Loader2,
  TrendingUp,
  FileText,
  Users,
  Home,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { legalAnalyticsApi } from '@/services/legalApi';
import type {
  LegalDashboard as LegalDashboardType,
  LegalHearing,
  PropertyAuction,
  PeriodTracking,
} from '@/types/legal';

import { logger } from '@/lib/logger';
const forumColors: Record<string, string> = {
  DRT: 'bg-blue-100 text-blue-700',
  DRAT: 'bg-indigo-100 text-indigo-700',
  NCLT: 'bg-purple-100 text-purple-700',
  CIVIL_COURT: 'bg-green-100 text-green-700',
  HIGH_COURT: 'bg-orange-100 text-orange-700',
  ARBITRATION: 'bg-yellow-100 text-yellow-700',
  LOK_ADALAT: 'bg-teal-100 text-teal-700',
};

const stageColors: Record<string, string> = {
  DEMAND_13_2: 'bg-yellow-100 text-yellow-700',
  OBJECTION_RECEIVED: 'bg-orange-100 text-orange-700',
  POSSESSION_13_4: 'bg-blue-100 text-blue-700',
  AUCTION_NOTICE: 'bg-purple-100 text-purple-700',
  AUCTION_SCHEDULED: 'bg-indigo-100 text-indigo-700',
  AUCTION_COMPLETED: 'bg-green-100 text-green-700',
  SALE_CONFIRMED: 'bg-emerald-100 text-emerald-700',
  AMOUNT_RECOVERED: 'bg-teal-100 text-teal-700',
};

export default function LegalDashboard() {
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState<LegalDashboardType | null>(null);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const response = await legalAnalyticsApi.getDashboard();
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

  const recoveryRate = dashboard?.summary?.total_claim_amount
    ? ((dashboard.summary.total_recovered / dashboard.summary.total_claim_amount) * 100).toFixed(1)
    : '0';

  return (
    <div className="space-y-6">
      <PageHeader
        title="Legal Dashboard"
        subtitle="Overview of legal proceedings and recovery status"
        actions={
          <Link to="/admin/legal/cases/new">
            <Button>
              <Briefcase className="mr-2 h-4 w-4" />
              New Case
            </Button>
          </Link>
        }
      />

      {/* Quick Links */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
        <Link to="/admin/legal/cases">
          <Card className="cursor-pointer transition-shadow hover:shadow-md">
            <CardContent className="p-4 text-center">
              <div className="mb-2 inline-flex rounded-lg bg-blue-100 p-3">
                <Briefcase className="h-5 w-5 text-blue-600" />
              </div>
              <p className="text-sm font-medium">Legal Cases</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/admin/legal/notices">
          <Card className="cursor-pointer transition-shadow hover:shadow-md">
            <CardContent className="p-4 text-center">
              <div className="mb-2 inline-flex rounded-lg bg-yellow-100 p-3">
                <FileText className="h-5 w-5 text-yellow-600" />
              </div>
              <p className="text-sm font-medium">Notices</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/admin/legal/sarfaesi">
          <Card className="cursor-pointer transition-shadow hover:shadow-md">
            <CardContent className="p-4 text-center">
              <div className="mb-2 inline-flex rounded-lg bg-purple-100 p-3">
                <Home className="h-5 w-5 text-purple-600" />
              </div>
              <p className="text-sm font-medium">SARFAESI</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/admin/legal/advocates">
          <Card className="cursor-pointer transition-shadow hover:shadow-md">
            <CardContent className="p-4 text-center">
              <div className="mb-2 inline-flex rounded-lg bg-green-100 p-3">
                <Users className="h-5 w-5 text-green-600" />
              </div>
              <p className="text-sm font-medium">Advocates</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/admin/legal/expenses">
          <Card className="cursor-pointer transition-shadow hover:shadow-md">
            <CardContent className="p-4 text-center">
              <div className="mb-2 inline-flex rounded-lg bg-red-100 p-3">
                <IndianRupee className="h-5 w-5 text-red-600" />
              </div>
              <p className="text-sm font-medium">Expenses</p>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-blue-100 p-2">
                <Briefcase className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Active Cases</p>
                <p className="text-2xl font-bold">{dashboard?.summary?.active_cases || 0}</p>
                <p className="text-xs text-gray-500">
                  of {dashboard?.summary?.total_cases || 0} total
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-purple-100 p-2">
                <IndianRupee className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Claims</p>
                <p className="text-xl font-bold">
                  {formatIndianCompactCurrency(dashboard?.summary?.total_claim_amount || 0)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-green-100 p-2">
                <TrendingUp className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Recovered</p>
                <p className="text-xl font-bold text-green-600">
                  {formatIndianCompactCurrency(dashboard?.summary?.total_recovered || 0)}
                </p>
                <p className="text-xs text-gray-500">{recoveryRate}% recovery rate</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-red-100 p-2">
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Pending Expenses</p>
                <p className="text-xl font-bold text-red-600">
                  {formatIndianCompactCurrency(dashboard?.expense_summary?.pending_approval || 0)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Cases by Forum */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Scale className="h-4 w-4" />
              Cases by Forum
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {dashboard?.summary?.cases_by_forum &&
                Object.entries(dashboard.summary.cases_by_forum).map(([forum, count]) => (
                  <div key={forum} className="flex items-center justify-between">
                    <Badge className={forumColors[forum] || 'bg-gray-100 text-gray-700'}>
                      {forum.replace('_', ' ')}
                    </Badge>
                    <span className="font-medium">{count}</span>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>

        {/* SARFAESI by Stage */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Home className="h-4 w-4" />
              SARFAESI by Stage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {dashboard?.summary?.sarfaesi_by_stage &&
                Object.entries(dashboard.summary.sarfaesi_by_stage).map(([stage, count]) => (
                  <div key={stage} className="flex items-center justify-between">
                    <Badge className={stageColors[stage] || 'bg-gray-100 text-gray-700'}>
                      {stage.replace(/_/g, ' ')}
                    </Badge>
                    <span className="font-medium">{count}</span>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>

        {/* Expense Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <IndianRupee className="h-4 w-4" />
              Expense Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-gray-500">Total Expenses</span>
                <span className="font-medium">
                  {formatIndianCompactCurrency(dashboard?.expense_summary?.total_expenses || 0)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Pending Approval</span>
                <span className="font-medium text-yellow-600">
                  {formatIndianCompactCurrency(dashboard?.expense_summary?.pending_approval || 0)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Pending Recovery</span>
                <span className="font-medium text-orange-600">
                  {formatIndianCompactCurrency(dashboard?.expense_summary?.pending_recovery || 0)}
                </span>
              </div>
              <div className="flex justify-between border-t pt-2">
                <span className="text-gray-500">Recovered</span>
                <span className="font-medium text-green-600">
                  {formatIndianCompactCurrency(dashboard?.expense_summary?.recovered || 0)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Upcoming Hearings */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Gavel className="h-4 w-4" />
              Upcoming Hearings
            </CardTitle>
            <Link
              to="/admin/legal/hearings"
              className="flex items-center text-sm text-blue-600 hover:underline"
            >
              View All <ChevronRight className="h-4 w-4" />
            </Link>
          </CardHeader>
          <CardContent>
            {dashboard?.upcoming_hearings && dashboard.upcoming_hearings.length > 0 ? (
              <div className="space-y-3">
                {dashboard.upcoming_hearings.slice(0, 5).map((hearing) => (
                  <div
                    key={hearing.id}
                    className="flex items-center justify-between rounded-lg bg-gray-50 p-3"
                  >
                    <div>
                      <p className="font-medium">{hearing.case_number}</p>
                      <p className="text-sm text-gray-500">{hearing.purpose}</p>
                      <p className="text-xs text-gray-400">{hearing.court_name}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">
                        <DateDisplay date={hearing.hearing_date} />
                      </p>
                      {hearing.hearing_time && (
                        <p className="text-sm text-gray-500">{hearing.hearing_time}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="py-4 text-center text-gray-500">No upcoming hearings</p>
            )}
          </CardContent>
        </Card>

        {/* Upcoming Auctions */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Home className="h-4 w-4" />
              Upcoming Auctions
            </CardTitle>
            <Link
              to="/admin/legal/auctions"
              className="flex items-center text-sm text-blue-600 hover:underline"
            >
              View All <ChevronRight className="h-4 w-4" />
            </Link>
          </CardHeader>
          <CardContent>
            {dashboard?.upcoming_auctions && dashboard.upcoming_auctions.length > 0 ? (
              <div className="space-y-3">
                {dashboard.upcoming_auctions.slice(0, 5).map((auction) => (
                  <div
                    key={auction.id}
                    className="flex items-center justify-between rounded-lg bg-gray-50 p-3"
                  >
                    <div>
                      <p className="font-medium">{auction.case_number}</p>
                      <p className="max-w-[200px] truncate text-sm text-gray-500">
                        {auction.property_description}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">
                        <DateDisplay date={auction.auction_date} />
                      </p>
                      <p className="text-sm text-green-600">
                        {formatIndianCompactCurrency(auction.reserve_price)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="py-4 text-center text-gray-500">No upcoming auctions</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Expiring Statutory Periods */}
      {dashboard?.expiring_periods && dashboard.expiring_periods.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base text-yellow-800">
              <Clock className="h-4 w-4" />
              Expiring Statutory Periods
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Loan Account</TableHead>
                  <TableHead>Provision</TableHead>
                  <TableHead>End Date</TableHead>
                  <TableHead>Days Remaining</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {dashboard.expiring_periods.map((period) => (
                  <TableRow key={period.id}>
                    <TableCell className="font-medium">{period.loan_account_number}</TableCell>
                    <TableCell>{period.provision_name}</TableCell>
                    <TableCell>
                      <DateDisplay date={period.end_date} />
                    </TableCell>
                    <TableCell>
                      <span
                        className={
                          period.days_remaining <= 7 ? 'font-bold text-red-600' : 'text-yellow-600'
                        }
                      >
                        {period.days_remaining} days
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge
                        className={
                          period.status === 'EXPIRING_SOON'
                            ? 'bg-yellow-100 text-yellow-700'
                            : period.status === 'EXPIRED'
                              ? 'bg-red-100 text-red-700'
                              : 'bg-gray-100 text-gray-700'
                        }
                      >
                        {period.status.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Recent Cases */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">Recent Cases</CardTitle>
          <Link
            to="/admin/legal/cases"
            className="flex items-center text-sm text-blue-600 hover:underline"
          >
            View All <ChevronRight className="h-4 w-4" />
          </Link>
        </CardHeader>
        <CardContent>
          {dashboard?.recent_cases && dashboard.recent_cases.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Case Number</TableHead>
                  <TableHead>Borrower</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Forum</TableHead>
                  <TableHead className="text-right">Claim Amount</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {dashboard.recent_cases.map((legalCase) => (
                  <TableRow key={legalCase.id}>
                    <TableCell>
                      <Link
                        to={`/admin/legal/cases/${legalCase.id}`}
                        className="font-medium text-blue-600 hover:underline"
                      >
                        {legalCase.case_number}
                      </Link>
                    </TableCell>
                    <TableCell>{legalCase.borrower_name}</TableCell>
                    <TableCell>{legalCase.case_type.replace('_', ' ')}</TableCell>
                    <TableCell>
                      <Badge className={forumColors[legalCase.forum_type] || 'bg-gray-100'}>
                        {legalCase.forum_type}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {formatIndianCompactCurrency(legalCase.claim_amount)}
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{legalCase.current_status}</Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="py-4 text-center text-gray-500">No cases found</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
