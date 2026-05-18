/**
 * Customer Portal - My Loans Page
 * View all loans and their details
 */

import {
  Wallet,
  IndianRupee,
  Calendar,
  AlertTriangle,
  ChevronRight,
  Loader2,
  TrendingUp,
  Clock,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { portalDashboardApi } from '@/services/portalApi';
import type { LoanSummary } from '@/types/portal';

import { logger } from "@/lib/logger";
export default function PortalLoans() {
  const [loading, setLoading] = useState(true);
  const [loans, setLoans] = useState<LoanSummary[]>([]);
  const [activeTab, setActiveTab] = useState('all');

  useEffect(() => {
    fetchLoans();
  }, []);

  const fetchLoans = async () => {
    try {
      const response = await portalDashboardApi.getLoans();
      setLoans(response.data);
    } catch (error) {
      logger.error('Failed to fetch loans:', error);
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

  const filteredLoans = loans.filter((loan) => {
    if (activeTab === 'all') return true;
    if (activeTab === 'active') return loan.status === 'ACTIVE';
    if (activeTab === 'overdue') return loan.overdue_days > 0;
    if (activeTab === 'closed') return loan.status === 'CLOSED';
    return true;
  });

  const summaryStats = {
    totalLoans: loans.length,
    activeLoans: loans.filter((l) => l.status === 'ACTIVE').length,
    totalOutstanding: loans.reduce((sum, l) => sum + l.total_outstanding, 0),
    totalOverdue: loans.filter((l) => l.overdue_days > 0).length,
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Loans"
        subtitle="View and manage your loan accounts"
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Wallet className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Loans</p>
                <p className="text-xl font-bold">{summaryStats.totalLoans}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-emerald-100 rounded-lg">
                <TrendingUp className="h-5 w-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Active Loans</p>
                <p className="text-xl font-bold">{summaryStats.activeLoans}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <IndianRupee className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Outstanding</p>
                <p className="text-lg font-bold">{formatCurrency(summaryStats.totalOutstanding)}</p>
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
                <p className="text-sm text-gray-500">Overdue</p>
                <p className="text-xl font-bold text-red-600">{summaryStats.totalOverdue}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Loans List */}
      <Card>
        <CardHeader>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger value="all">All Loans</TabsTrigger>
              <TabsTrigger value="active">Active</TabsTrigger>
              <TabsTrigger value="overdue">Overdue</TabsTrigger>
              <TabsTrigger value="closed">Closed</TabsTrigger>
            </TabsList>
          </Tabs>
        </CardHeader>
        <CardContent>
          {filteredLoans.length > 0 ? (
            <div className="space-y-4">
              {filteredLoans.map((loan) => (
                <LoanCard key={loan.id} loan={loan} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <Wallet className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg">No loans found</p>
              <p className="text-sm">
                {activeTab === 'all'
                  ? "You don't have any loan accounts yet"
                  : `No ${activeTab} loans`}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function LoanCard({ loan }: { loan: LoanSummary }) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const paidPercentage =
    loan.disbursed_amount > 0
      ? ((loan.disbursed_amount - loan.outstanding_principal) / loan.disbursed_amount) * 100
      : 0;

  const getStatusBadge = () => {
    if (loan.overdue_days > 0) {
      return <Badge variant="destructive">Overdue</Badge>;
    }
    switch (loan.status) {
      case 'ACTIVE':
        return <Badge className="bg-green-100 text-green-700">Active</Badge>;
      case 'CLOSED':
        return <Badge className="bg-gray-100 text-gray-700">Closed</Badge>;
      default:
        return <Badge variant="secondary">{loan.status}</Badge>;
    }
  };

  return (
    <Link to={`/portal/loans/${loan.id}`}>
      <div className="p-4 border rounded-lg hover:bg-gray-50 transition-colors cursor-pointer">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-lg">{loan.loan_account_number}</h3>
              {getStatusBadge()}
            </div>
            <p className="text-sm text-gray-500">{loan.product_name}</p>
          </div>
          <ChevronRight className="h-5 w-5 text-gray-400" />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div>
            <p className="text-xs text-gray-500">Sanctioned</p>
            <p className="font-medium">{formatCurrency(loan.sanctioned_amount)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Outstanding</p>
            <p className="font-medium">{formatCurrency(loan.total_outstanding)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">EMI Amount</p>
            <p className="font-medium">{formatCurrency(loan.emi_amount)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Next EMI Date</p>
            <DateDisplay date={loan.next_emi_date} className="font-medium" />
          </div>
        </div>

        <div className="mb-3">
          <div className="flex justify-between text-sm text-gray-500 mb-1">
            <span>Repayment Progress</span>
            <span>{paidPercentage.toFixed(0)}%</span>
          </div>
          <Progress value={paidPercentage} className="h-2" />
        </div>

        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-4 text-gray-500">
            <span className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              {loan.remaining_tenure} months left
            </span>
            <span>@ {loan.interest_rate}% p.a.</span>
          </div>

          {loan.overdue_amount > 0 && (
            <div className="flex items-center gap-1 text-red-600">
              <AlertTriangle className="h-4 w-4" />
              <span>
                {formatCurrency(loan.overdue_amount)} overdue ({loan.overdue_days} days)
              </span>
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}
