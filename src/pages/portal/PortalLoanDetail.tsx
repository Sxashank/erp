/**
 * Customer Portal - Loan Detail Page
 * View loan details, schedule, and payment history
 */

import { AlertTriangle, Loader2, Download, CreditCard, FileText } from 'lucide-react';
import { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';

import {
  AmountDisplay,
  DataTable,
  DateDisplay,
  EmptyState,
  ErrorState,
  SkeletonTable,
  type Column,
} from '@/components/common';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  useDownloadScheduleCsv,
  useFailedSchedule,
  useMissedSchedule,
} from '@/hooks/portal/useFailedEmis';
import {
  usePortalLoan,
  usePortalLoanPayments,
  usePortalLoanSchedule,
} from '@/hooks/portal/useLoanDetail';
import type { FailedScheduleItem } from '@/services/portalApi';

export default function PortalLoanDetail() {
  const { loanId } = useParams<{ loanId: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');

  const loanQuery = usePortalLoan(loanId);
  const scheduleQuery = usePortalLoanSchedule(loanId);
  const paymentsQuery = usePortalLoanPayments(loanId);

  const failedQuery = useFailedSchedule(loanId);
  const missedQuery = useMissedSchedule(loanId);
  const scheduleCsv = useDownloadScheduleCsv(loanId);

  const loan = loanQuery.data;
  const schedule = scheduleQuery.data ?? [];
  const payments = paymentsQuery.data ?? [];

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  if (loanQuery.isLoading && !loan) {
    return (
      <div className="space-y-6">
        <SkeletonTable rows={6} />
      </div>
    );
  }

  if (loanQuery.isError) {
    return (
      <div className="space-y-6">
        <ErrorState error={loanQuery.error} onRetry={() => loanQuery.refetch()} />
      </div>
    );
  }

  if (!loan) {
    return (
      <EmptyState
        title="Loan not found"
        subtitle="We could not find the loan you were looking for."
        action={
          <Button variant="link" onClick={() => navigate('/portal/loans')}>
            Back to Loans
          </Button>
        }
      />
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
      <PageHeader
        title={loan.loan_account_number}
        subtitle={loan.product_name}
        breadcrumbs={[{ label: 'Loans', to: '/portal/loans' }, { label: loan.loan_account_number }]}
        actions={
          <Link to={`/portal/payments?loan=${loan.id}`}>
            <Button className="bg-emerald-600 hover:bg-emerald-700">
              <CreditCard className="mr-2 h-4 w-4" />
              Make Payment
            </Button>
          </Link>
        }
      />

      {/* Loan Summary Cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
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
          <TabsTrigger value="failed">Failed EMIs</TabsTrigger>
          <TabsTrigger value="missed">Missed Payments</TabsTrigger>
          <TabsTrigger value="payments">Payment History</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
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
                    <DateDisplay date={loan.disbursement_date} className="font-medium" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Maturity Date</p>
                    <DateDisplay date={loan.maturity_date} className="font-medium" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">EMI Start Date</p>
                    <DateDisplay date={loan.emi_start_date} className="font-medium" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Remaining Tenure</p>
                    <p className="font-medium">{loan.remaining_tenure} months</p>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <p className="mb-2 text-sm text-gray-500">Borrower</p>
                  <p className="font-medium">{loan.borrower_name}</p>
                  {loan.co_borrowers && loan.co_borrowers.length > 0 && (
                    <p className="text-sm text-gray-500">
                      Co-Borrowers: {loan.co_borrowers.join(', ')}
                    </p>
                  )}
                </div>

                {loan.nach_mandate_status && (
                  <div className="border-t pt-4">
                    <p className="mb-1 text-sm text-gray-500">NACH Mandate</p>
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
                  <div className="mb-1 flex justify-between text-sm">
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

                <div className="border-t pt-4">
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
                      <p className="text-lg font-bold">{formatCurrency(loan.total_outstanding)}</p>
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
              <Button
                variant="outline"
                size="sm"
                onClick={() => scheduleCsv.download()}
                disabled={scheduleCsv.isDownloading}
              >
                {scheduleCsv.isDownloading ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Download className="mr-2 h-4 w-4" />
                )}
                Download Schedule (CSV)
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
                        <TableCell><DateDisplay date={item.due_date} /></TableCell>
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

        <TabsContent value="failed">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Failed EMIs</CardTitle>
            </CardHeader>
            <CardContent>
              <FailedMissedTable
                rows={failedQuery.data ?? []}
                isLoading={failedQuery.isLoading}
                error={failedQuery.isError ? failedQuery.error : undefined}
                onRetry={() => failedQuery.refetch()}
                emptyTitle="No failed EMIs"
                emptySubtitle="Auto-debit attempts that failed will appear here once the next NACH presentation cycle runs."
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="missed">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Missed Payments</CardTitle>
            </CardHeader>
            <CardContent>
              <FailedMissedTable
                rows={missedQuery.data ?? []}
                isLoading={missedQuery.isLoading}
                error={missedQuery.isError ? missedQuery.error : undefined}
                onRetry={() => missedQuery.refetch()}
                emptyTitle="No missed payments"
                emptySubtitle="Instalments overdue beyond your grace period will be listed here."
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payments">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base">Payment History</CardTitle>
              <Button variant="outline" size="sm">
                <Download className="mr-2 h-4 w-4" />
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
                            <DateDisplay date={payment.payment_date} />
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
                <div className="py-8 text-center text-gray-500">
                  <FileText className="mx-auto mb-4 h-12 w-12 opacity-50" />
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

interface FailedMissedTableProps {
  rows: FailedScheduleItem[];
  isLoading: boolean;
  error: unknown;
  onRetry: () => void;
  emptyTitle: string;
  emptySubtitle: string;
}

function FailedMissedTable({
  rows,
  isLoading,
  error,
  onRetry,
  emptyTitle,
  emptySubtitle,
}: FailedMissedTableProps) {
  const columns: Column<FailedScheduleItem>[] = [
    {
      key: 'installmentNumber',
      header: 'EMI #',
      render: (r) => r.installmentNumber,
      align: 'left',
      sortable: true,
      sortValue: (r) => r.installmentNumber,
    },
    {
      key: 'dueDate',
      header: 'Due Date',
      render: (r) => <DateDisplay date={r.dueDate} />,
      sortable: true,
      sortValue: (r) => r.dueDate,
    },
    {
      key: 'principalDue',
      header: 'Principal Due',
      align: 'right',
      render: (r) => <AmountDisplay amount={Number(r.principalDue)} />,
    },
    {
      key: 'interestDue',
      header: 'Interest Due',
      align: 'right',
      render: (r) => <AmountDisplay amount={Number(r.interestDue)} />,
    },
    {
      key: 'dpdDays',
      header: 'DPD',
      align: 'right',
      render: (r) => `${r.dpdDays}d`,
      sortable: true,
      sortValue: (r) => r.dpdDays,
    },
    {
      key: 'failReason',
      header: 'Reason',
      render: (r) => r.failReason ?? '—',
    },
    {
      key: 'lastAttemptDate',
      header: 'Last Attempt',
      render: (r) => <DateDisplay date={r.lastAttemptDate} />,
    },
  ];

  return (
    <DataTable<FailedScheduleItem>
      data={rows}
      columns={columns}
      getRowId={(r) => String(r.installmentNumber)}
      isLoading={isLoading}
      error={error}
      onRetry={onRetry}
      emptyTitle={emptyTitle}
      emptySubtitle={emptySubtitle}
    />
  );
}
