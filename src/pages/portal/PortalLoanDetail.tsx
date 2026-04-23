/**
 * Customer Portal - Loan Detail Page
 * View loan details, schedule, and payment history
 */

import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  ArrowLeft,
  IndianRupee,
  Calendar,
  AlertTriangle,
  Loader2,
  Download,
  CreditCard,
  FileText,
  CheckCircle,
  Clock,
  XCircle,
} from 'lucide-react';
import { portalDashboardApi } from '@/services/portalApi';
import type { LoanDetail, RepaymentScheduleItem, PaymentHistory } from '@/types/portal';

export default function PortalLoanDetail() {
  const { loanId } = useParams<{ loanId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [loan, setLoan] = useState<LoanDetail | null>(null);
  const [schedule, setSchedule] = useState<RepaymentScheduleItem[]>([]);
  const [payments, setPayments] = useState<PaymentHistory[]>([]);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (loanId) {
      fetchLoanDetails();
    }
  }, [loanId]);

  const fetchLoanDetails = async () => {
    try {
      const [loanRes, scheduleRes, paymentsRes] = await Promise.all([
        portalDashboardApi.getLoan(loanId!),
        portalDashboardApi.getLoanSchedule(loanId!),
        portalDashboardApi.getLoanPayments(loanId!),
      ]);
      setLoan(loanRes.data);
      setSchedule(scheduleRes.data);
      setPayments(paymentsRes.data);
    } catch (error) {
      console.error('Failed to fetch loan details:', error);
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

  if (!loan) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Loan not found</p>
        <Button variant="link" onClick={() => navigate('/portal/loans')}>
          Back to Loans
        </Button>
      </div>
    );
  }

  const paidPercentage =
    loan.disbursed_amount > 0
      ? ((loan.disbursed_amount - loan.outstanding_principal) / loan.disbursed_amount) * 100
      : 0;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PAID':
        return <Badge className="bg-green-100 text-green-700">Paid</Badge>;
      case 'PARTIAL':
        return <Badge className="bg-yellow-100 text-yellow-700">Partial</Badge>;
      case 'DUE':
        return <Badge className="bg-blue-100 text-blue-700">Due</Badge>;
      case 'OVERDUE':
        return <Badge variant="destructive">Overdue</Badge>;
      case 'FUTURE':
        return <Badge variant="secondary">Future</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/portal/loans')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{loan.loan_account_number}</h1>
            <p className="text-gray-500">{loan.product_name}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Link to={`/portal/payments?loan=${loan.id}`}>
            <Button className="bg-emerald-600 hover:bg-emerald-700">
              <CreditCard className="h-4 w-4 mr-2" />
              Make Payment
            </Button>
          </Link>
        </div>
      </div>

      {/* Loan Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">Sanctioned Amount</p>
            <p className="text-xl font-bold">{formatCurrency(loan.sanctioned_amount)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">Disbursed Amount</p>
            <p className="text-xl font-bold">{formatCurrency(loan.disbursed_amount)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">Outstanding</p>
            <p className="text-xl font-bold">{formatCurrency(loan.total_outstanding)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">EMI Amount</p>
            <p className="text-xl font-bold">{formatCurrency(loan.emi_amount)}</p>
          </CardContent>
        </Card>
      </div>

      {/* Overdue Alert */}
      {loan.overdue_amount > 0 && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-6 w-6 text-red-600" />
                <div>
                  <p className="font-medium text-red-800">Payment Overdue</p>
                  <p className="text-sm text-red-600">
                    {formatCurrency(loan.overdue_amount)} is overdue by {loan.overdue_days} days
                  </p>
                </div>
              </div>
              <Link to={`/portal/payments?loan=${loan.id}`}>
                <Button variant="destructive">Pay Now</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="schedule">EMI Schedule</TabsTrigger>
          <TabsTrigger value="payments">Payment History</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Loan Details */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Loan Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Interest Rate</p>
                    <p className="font-medium">{loan.interest_rate}% p.a.</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Tenure</p>
                    <p className="font-medium">{loan.tenure_months} months</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Disbursement Date</p>
                    <p className="font-medium">
                      {new Date(loan.disbursement_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Maturity Date</p>
                    <p className="font-medium">
                      {new Date(loan.maturity_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">EMI Start Date</p>
                    <p className="font-medium">
                      {new Date(loan.emi_start_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Remaining Tenure</p>
                    <p className="font-medium">{loan.remaining_tenure} months</p>
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <p className="text-sm text-gray-500 mb-2">Borrower</p>
                  <p className="font-medium">{loan.borrower_name}</p>
                  {loan.co_borrowers && loan.co_borrowers.length > 0 && (
                    <p className="text-sm text-gray-500">
                      Co-Borrowers: {loan.co_borrowers.join(', ')}
                    </p>
                  )}
                </div>

                {loan.nach_mandate_status && (
                  <div className="pt-4 border-t">
                    <p className="text-sm text-gray-500 mb-1">NACH Mandate</p>
                    <Badge
                      className={
                        loan.nach_mandate_status === 'ACTIVE'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-yellow-100 text-yellow-700'
                      }
                    >
                      {loan.nach_mandate_status}
                    </Badge>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Payment Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Payment Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-500">Repayment Progress</span>
                    <span className="font-medium">{paidPercentage.toFixed(1)}%</span>
                  </div>
                  <Progress value={paidPercentage} className="h-3" />
                </div>

                <div className="grid grid-cols-2 gap-4 pt-4">
                  <div>
                    <p className="text-sm text-gray-500">Total Paid</p>
                    <p className="font-medium text-green-600">{formatCurrency(loan.total_paid)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Principal Paid</p>
                    <p className="font-medium">{formatCurrency(loan.total_principal_paid)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Interest Paid</p>
                    <p className="font-medium">{formatCurrency(loan.total_interest_paid)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Prepaid Amount</p>
                    <p className="font-medium">{formatCurrency(loan.prepaid_amount)}</p>
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Outstanding Principal</p>
                      <p className="font-medium">{formatCurrency(loan.outstanding_principal)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Outstanding Interest</p>
                      <p className="font-medium">{formatCurrency(loan.outstanding_interest)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Charges Due</p>
                      <p className="font-medium">{formatCurrency(loan.charges_due)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Total Outstanding</p>
                      <p className="font-bold text-lg">{formatCurrency(loan.total_outstanding)}</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="schedule">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base">EMI Repayment Schedule</CardTitle>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>EMI #</TableHead>
                      <TableHead>Due Date</TableHead>
                      <TableHead className="text-right">EMI Amount</TableHead>
                      <TableHead className="text-right">Principal</TableHead>
                      <TableHead className="text-right">Interest</TableHead>
                      <TableHead className="text-right">Balance</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {schedule.map((item) => (
                      <TableRow key={item.installment_number}>
                        <TableCell>{item.installment_number}</TableCell>
                        <TableCell>{new Date(item.due_date).toLocaleDateString()}</TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(item.emi_amount)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(item.principal)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(item.interest)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(item.closing_balance)}
                        </TableCell>
                        <TableCell>{getStatusBadge(item.status)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payments">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base">Payment History</CardTitle>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Download Statement
              </Button>
            </CardHeader>
            <CardContent>
              {payments.length > 0 ? (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Receipt #</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead className="text-right">Amount</TableHead>
                        <TableHead className="text-right">Principal</TableHead>
                        <TableHead className="text-right">Interest</TableHead>
                        <TableHead>Mode</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {payments.map((payment) => (
                        <TableRow key={payment.id}>
                          <TableCell className="font-medium">{payment.receipt_number}</TableCell>
                          <TableCell>
                            {new Date(payment.payment_date).toLocaleDateString()}
                          </TableCell>
                          <TableCell className="text-right">
                            {formatCurrency(payment.amount)}
                          </TableCell>
                          <TableCell className="text-right">
                            {formatCurrency(payment.principal_applied)}
                          </TableCell>
                          <TableCell className="text-right">
                            {formatCurrency(payment.interest_applied)}
                          </TableCell>
                          <TableCell>{payment.payment_mode}</TableCell>
                          <TableCell>
                            <Badge className="bg-green-100 text-green-700">{payment.status}</Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No payment history available</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
