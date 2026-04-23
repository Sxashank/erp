/**
 * Customer Portal Dashboard
 * Overview of loans, payments, and dues
 */

import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import { Progress } from '@/components/ui/progress';
import {
  Wallet,
  CreditCard,
  FileText,
  HelpCircle,
  Clock,
  IndianRupee,
  AlertTriangle,
  ChevronRight,
  Download,
  Loader2,
  TrendingDown,
  Calendar,
} from 'lucide-react';
import { portalDashboardApi } from '@/services/portalApi';
import type { PortalDashboard, LoanSummary, UpcomingDue } from '@/types/portal';

export default function PortalDashboardPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState<PortalDashboard | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('portal_access_token');
    if (!token) {
      navigate('/portal/login');
      return;
    }
    fetchDashboard();
  }, [navigate]);

  const fetchDashboard = async () => {
    try {
      const response = await portalDashboardApi.getDashboard();
      setDashboard(response.data);
    } catch (error) {
      console.error('Failed to fetch dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
      </div>
    );
  }

  const quickLinks = [
    { label: 'My Loans', icon: Wallet, href: '/portal/loans', color: 'bg-emerald-100 text-emerald-600' },
    { label: 'Make Payment', icon: CreditCard, href: '/portal/payments', color: 'bg-blue-100 text-blue-600' },
    { label: 'Documents', icon: FileText, href: '/portal/documents', color: 'bg-purple-100 text-purple-600' },
    { label: 'Support', icon: HelpCircle, href: '/portal/support', color: 'bg-orange-100 text-orange-600' },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Welcome, ${dashboard?.customer?.name || 'Customer'}!`}
        subtitle={`Customer ID: ${dashboard?.customer?.customer_id ?? ''}`}
      />

      {/* Quick Links */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {quickLinks.map((link) => (
          <Link key={link.href} to={link.href}>
            <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
              <CardContent className="p-4 text-center">
                <div className={`inline-flex p-3 rounded-xl ${link.color} mb-2`}>
                  <link.icon className="h-5 w-5" />
                </div>
                <p className="text-sm font-medium">{link.label}</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-emerald-100 rounded-lg">
                <Wallet className="h-5 w-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Active Loans</p>
                <p className="text-xl font-bold">{dashboard?.loans_summary?.active_loans || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <IndianRupee className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Outstanding</p>
                <p className="text-xl font-bold">{formatCurrency(dashboard?.loans_summary?.total_outstanding || 0)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Overdue</p>
                <p className="text-xl font-bold text-red-600">{formatCurrency(dashboard?.loans_summary?.total_overdue || 0)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Calendar className="h-5 w-5 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Next Due</p>
                <p className="text-sm font-bold">{dashboard?.loans_summary?.next_due_date || '-'}</p>
                <p className="text-lg font-bold">{formatCurrency(dashboard?.loans_summary?.next_due_amount || 0)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Loans Overview */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">My Loans</CardTitle>
                <Link to="/portal/loans" className="text-sm text-emerald-600 hover:underline flex items-center">
                  View All <ChevronRight className="h-4 w-4" />
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              {dashboard?.loans && dashboard.loans.length > 0 ? (
                <div className="space-y-4">
                  {dashboard.loans.slice(0, 3).map((loan) => (
                    <LoanCard key={loan.id} loan={loan} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Wallet className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No active loans</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recent Payments */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Recent Payments</CardTitle>
            </CardHeader>
            <CardContent>
              {dashboard?.recent_payments && dashboard.recent_payments.length > 0 ? (
                <div className="space-y-3">
                  {dashboard.recent_payments.slice(0, 5).map((payment) => (
                    <div key={payment.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium">{formatCurrency(payment.amount)}</p>
                        <p className="text-sm text-gray-500">{payment.receipt_number}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm">{new Date(payment.payment_date).toLocaleDateString()}</p>
                        <Badge variant="secondary" className="bg-green-100 text-green-700">
                          {payment.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center py-4 text-gray-500">No recent payments</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Upcoming Dues & Announcements */}
        <div className="space-y-6">
          {/* Upcoming Dues */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Upcoming Dues
              </CardTitle>
            </CardHeader>
            <CardContent>
              {dashboard?.upcoming_dues && dashboard.upcoming_dues.length > 0 ? (
                <div className="space-y-4">
                  {dashboard.upcoming_dues.map((due) => (
                    <div
                      key={due.loan_account_id}
                      className={`p-4 rounded-lg ${due.is_overdue ? 'bg-red-50 border border-red-200' : 'bg-gray-50'}`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium">{due.loan_account_number}</span>
                        {due.is_overdue && (
                          <Badge variant="destructive">Overdue</Badge>
                        )}
                      </div>
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-lg font-bold">{formatCurrency(due.total_due)}</p>
                          <p className="text-xs text-gray-500">
                            Due: {new Date(due.due_date).toLocaleDateString()}
                          </p>
                        </div>
                        <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700">
                          Pay Now
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-4 text-gray-500">
                  <TrendingDown className="h-8 w-8 mx-auto mb-2 text-green-500" />
                  <p className="text-sm">No upcoming dues</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Announcements */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Announcements</CardTitle>
            </CardHeader>
            <CardContent>
              {dashboard?.announcements && dashboard.announcements.length > 0 ? (
                <div className="space-y-3">
                  {dashboard.announcements.map((announcement) => (
                    <div key={announcement.id} className="p-3 border rounded-lg">
                      <h4 className="font-medium text-sm">{announcement.title}</h4>
                      <p className="text-xs text-gray-500 mt-1">{announcement.message}</p>
                      <p className="text-xs text-gray-400 mt-2">
                        {new Date(announcement.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center py-4 text-gray-500 text-sm">No announcements</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

// Loan Card Component
function LoanCard({ loan }: { loan: LoanSummary }) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const paidPercentage = loan.disbursed_amount > 0
    ? ((loan.disbursed_amount - loan.outstanding_principal) / loan.disbursed_amount) * 100
    : 0;

  return (
    <Link to={`/portal/loans/${loan.id}`}>
      <div className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="font-medium">{loan.loan_account_number}</p>
            <p className="text-sm text-gray-500">{loan.product_name}</p>
          </div>
          <Badge
            variant="secondary"
            className={loan.overdue_days > 0 ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}
          >
            {loan.status}
          </Badge>
        </div>
        <div className="grid grid-cols-3 gap-4 mb-3 text-sm">
          <div>
            <p className="text-gray-500">Outstanding</p>
            <p className="font-medium">{formatCurrency(loan.total_outstanding)}</p>
          </div>
          <div>
            <p className="text-gray-500">EMI</p>
            <p className="font-medium">{formatCurrency(loan.emi_amount)}</p>
          </div>
          <div>
            <p className="text-gray-500">Next Due</p>
            <p className="font-medium">{loan.next_emi_date ? new Date(loan.next_emi_date).toLocaleDateString() : '-'}</p>
          </div>
        </div>
        <div>
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Repayment Progress</span>
            <span>{paidPercentage.toFixed(0)}%</span>
          </div>
          <Progress value={paidPercentage} className="h-2" />
        </div>
        {loan.overdue_amount > 0 && (
          <div className="mt-3 p-2 bg-red-50 rounded text-sm text-red-700">
            <AlertTriangle className="h-4 w-4 inline mr-1" />
            Overdue: {formatCurrency(loan.overdue_amount)} ({loan.overdue_days} days)
          </div>
        )}
      </div>
    </Link>
  );
}
