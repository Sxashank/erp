import {
  Edit,
  Loader2,
  DollarSign,
  Clock,
  AlertTriangle,
  Plus,
  Receipt,
  RefreshCw,
  Download,
} from 'lucide-react';
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
  useBorrowing,
  useBorrowingPayments,
  useBorrowingSchedule,
  useBorrowingTranches,
  useRecordBorrowingPayment,
  useRecordDrawdown,
} from '@/hooks/lending/useBorrowings';
import { useToast } from '@/hooks/use-toast';

const statusColors: Record<string, string> = {
  ACTIVE: 'bg-green-100 text-green-700',
  CLOSED: 'bg-gray-100 text-gray-700',
  PREPAID: 'bg-blue-100 text-blue-700',
  MATURED: 'bg-purple-100 text-purple-700',
  PENDING: 'bg-yellow-100 text-yellow-700',
  APPROVED: 'bg-blue-100 text-blue-700',
  DISBURSED: 'bg-green-100 text-green-700',
  REJECTED: 'bg-red-100 text-red-700',
  PAID: 'bg-green-100 text-green-700',
  PARTIAL: 'bg-amber-100 text-amber-700',
  OVERDUE: 'bg-red-100 text-red-700',
};

export default function BorrowingView() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { toast } = useToast();
  const {
    data: borrowing,
    isLoading: isBorrowingLoading,
    isError: isBorrowingError,
    error: borrowingError,
    refetch: refetchBorrowing,
  } = useBorrowing(id);
  const { data: tranches = [], refetch: refetchTranches } = useBorrowingTranches(id);
  const { data: schedule = [], refetch: refetchSchedule } = useBorrowingSchedule(id);
  const { data: payments = [], refetch: refetchPayments } = useBorrowingPayments(id);
  const drawdownMutation = useRecordDrawdown();
  const paymentMutation = useRecordBorrowingPayment();
  const [showDrawdownDialog, setShowDrawdownDialog] = useState(false);
  const [showPaymentDialog, setShowPaymentDialog] = useState(false);
  const [drawdownAmount, setDrawdownAmount] = useState('');
  const [paymentAmount, setPaymentAmount] = useState('');

  const refetchAll = async () => {
    await Promise.all([
      refetchBorrowing(),
      refetchTranches(),
      refetchSchedule(),
      refetchPayments(),
    ]);
  };

  const handleDrawdown = async () => {
    if (!id || !drawdownAmount) return;
    try {
      await drawdownMutation.mutateAsync({
        borrowingId: id,
        amount: Number(drawdownAmount),
        drawdownDate: new Date().toISOString().split('T')[0],
        remarks: 'Drawdown request',
      });
      toast({
        title: 'Success',
        description: 'Drawdown request submitted',
      });
      setShowDrawdownDialog(false);
      setDrawdownAmount('');
      await refetchAll();
    } catch {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to submit drawdown request',
      });
    }
  };

  const handlePayment = async () => {
    if (!id || !paymentAmount) return;
    try {
      await paymentMutation.mutateAsync({
        borrowingId: id,
        paymentDate: new Date().toISOString().split('T')[0],
        principalAmount: Number(paymentAmount),
        interestAmount: 0,
        remarks: 'Manual payment',
      });
      toast({
        title: 'Success',
        description: 'Payment recorded successfully',
      });
      setShowPaymentDialog(false);
      setPaymentAmount('');
      await refetchAll();
    } catch {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to record payment',
      });
    }
  };

  if (isBorrowingLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (isBorrowingError) {
    return (
      <ErrorState
        title="Could not load borrowing details"
        error={borrowingError}
        onRetry={() => void refetchBorrowing()}
      />
    );
  }

  if (!borrowing) {
    return (
      <div className="flex h-64 flex-col items-center justify-center">
        <AlertTriangle className="mb-4 h-12 w-12 text-muted-foreground" />
        <p className="text-muted-foreground">Borrowing not found</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate(-1)}>
          Go Back
        </Button>
      </div>
    );
  }

  const sanctionedAmount = Number(borrowing.sanctionedAmount);
  const drawnAmount = Number(borrowing.drawnAmount);
  const outstandingPrincipal = Number(borrowing.principalOutstanding);
  const availableAmount = Number(borrowing.availableAmount);
  const utilizationPercent = sanctionedAmount > 0 ? (drawnAmount / sanctionedAmount) * 100 : 0;
  const nextScheduleItem = schedule.find((s) => s.status === 'DUE' || s.status === 'PENDING');
  const lenderName = borrowing.lenderName ?? borrowing.lenderCode ?? 'Funding source';
  const borrowingTypeLabel = borrowing.borrowingType.replace(/_/g, ' ');

  return (
    <div className="space-y-6">
      <PageHeader
        title={borrowing.borrowingNumber}
        subtitle={`${borrowingTypeLabel} from ${lenderName}`}
        breadcrumbs={[
          { label: 'Borrowings', to: '/admin/treasury/borrowings' },
          { label: borrowing.borrowingNumber },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Badge className={statusColors[borrowing.status] || ''}>{borrowing.status}</Badge>
            <Button variant="outline" onClick={() => void refetchAll()}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate(`/admin/treasury/borrowings/${id}/edit`)}
            >
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sanctioned Amount</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={borrowing.sanctionedAmount}
              abbreviated
              className="text-2xl font-bold"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Outstanding</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={outstandingPrincipal}
              abbreviated
              className="text-2xl font-bold text-amber-600"
            />
            <div className="mt-1 flex items-center gap-2">
              <Progress value={utilizationPercent} className="h-2" />
              <span className="text-xs text-muted-foreground">
                <PercentageDisplay value={utilizationPercent} />
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Effective Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              <PercentageDisplay value={borrowing.effectiveRate} /> p.a.
            </div>
            <p className="text-xs text-muted-foreground">
              {borrowing.rateType === 'FLOATING'
                ? `${borrowing.baseRateName} + ${borrowing.spreadBps} bps`
                : 'Fixed Rate'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Next Due</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {nextScheduleItem ? (
              <>
                <AmountDisplay
                  amount={nextScheduleItem.totalDue}
                  abbreviated
                  className="text-2xl font-bold text-red-600"
                />
                <p className="text-xs text-muted-foreground">
                  Due on <DateDisplay date={nextScheduleItem.dueDate} />
                </p>
              </>
            ) : (
              <p className="text-muted-foreground">No upcoming payments</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Detail Tabs */}
      <Tabs defaultValue="details" className="space-y-4">
        <TabsList>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="tranches">Tranches ({tranches.length})</TabsTrigger>
          <TabsTrigger value="schedule">Schedule ({schedule.length})</TabsTrigger>
          <TabsTrigger value="payments">Payments ({payments.length})</TabsTrigger>
        </TabsList>

        {/* Details Tab */}
        <TabsContent value="details" className="space-y-4">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Facility Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Lender</p>
                    <p className="font-medium">{lenderName}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Facility Type</p>
                    <p className="font-medium">{borrowingTypeLabel}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Sanction Date</p>
                    <p className="font-medium">
                      <DateDisplay date={borrowing.sanctionDate} />
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Maturity Date</p>
                    <p className="font-medium">
                      <DateDisplay date={borrowing.maturityDate} />
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Tenure</p>
                    <p className="font-medium">{borrowing.tenureMonths} months</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Repayment Frequency</p>
                    <p className="font-medium">
                      {borrowing.principalPaymentFrequency} principal /{' '}
                      {borrowing.interestPaymentFrequency} interest
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Interest Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Rate Type</p>
                    <p className="font-medium">{borrowing.rateType}</p>
                  </div>
                  {borrowing.rateType === 'FLOATING' && (
                    <>
                      <div>
                        <p className="text-muted-foreground">Base Rate</p>
                        <p className="font-medium">
                          {borrowing.baseRateName}:{' '}
                          <PercentageDisplay value={borrowing.baseRateValue} />
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Spread</p>
                        <p className="font-medium">{borrowing.spreadBps} bps</p>
                      </div>
                    </>
                  )}
                  <div>
                    <p className="text-muted-foreground">Effective Rate</p>
                    <p className="text-lg font-medium">
                      <PercentageDisplay value={borrowing.effectiveRate} /> p.a.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Amount Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Sanctioned</p>
                    <AmountDisplay
                      amount={borrowing.sanctionedAmount}
                      abbreviated
                      className="font-medium"
                    />
                  </div>
                  <div>
                    <p className="text-muted-foreground">Drawn</p>
                    <AmountDisplay
                      amount={borrowing.drawnAmount}
                      abbreviated
                      className="font-medium"
                    />
                  </div>
                  <div>
                    <p className="text-muted-foreground">Outstanding Principal</p>
                    <AmountDisplay
                      amount={borrowing.principalOutstanding}
                      abbreviated
                      className="font-medium"
                    />
                  </div>
                  <div>
                    <p className="text-muted-foreground">Available Limit</p>
                    <AmountDisplay
                      amount={borrowing.availableAmount}
                      abbreviated
                      className="font-medium text-green-600"
                    />
                  </div>
                  <div>
                    <p className="text-muted-foreground">Total Outstanding</p>
                    <AmountDisplay
                      amount={outstandingPrincipal}
                      abbreviated
                      className="text-lg font-medium text-amber-600"
                    />
                  </div>
                  <div>
                    <p className="text-muted-foreground">Undrawn Amount</p>
                    <AmountDisplay
                      amount={availableAmount}
                      abbreviated
                      className="font-medium text-green-600"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Security Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-sm">
                  <div className="mb-2">
                    <p className="text-muted-foreground">Security Type</p>
                    <p className="font-medium">{borrowing.securityType}</p>
                  </div>
                  {borrowing.securityDescription && (
                    <div>
                      <p className="text-muted-foreground">Description</p>
                      <p className="font-medium">{borrowing.securityDescription}</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tranches Tab */}
        <TabsContent value="tranches">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Drawdown Tranches</CardTitle>
                <CardDescription>Tranche-wise drawdown history</CardDescription>
              </div>
              <Dialog open={showDrawdownDialog} onOpenChange={setShowDrawdownDialog}>
                <DialogTrigger asChild>
                  <Button disabled={availableAmount <= 0}>
                    <Plus className="mr-2 h-4 w-4" />
                    Request Drawdown
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Request Drawdown</DialogTitle>
                    <DialogDescription>
                      Available limit: <AmountDisplay amount={availableAmount} abbreviated />
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label>Drawdown Amount</Label>
                      <Input
                        type="number"
                        placeholder="Enter amount"
                        value={drawdownAmount}
                        onChange={(e) => setDrawdownAmount(e.target.value)}
                        max={availableAmount}
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setShowDrawdownDialog(false)}>
                      Cancel
                    </Button>
                    <Button
                      onClick={handleDrawdown}
                      disabled={drawdownMutation.isPending || !drawdownAmount}
                    >
                      {drawdownMutation.isPending && (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      )}
                      Submit Request
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Tranche #</TableHead>
                    <TableHead className="text-right">Requested</TableHead>
                    <TableHead className="text-right">Approved</TableHead>
                    <TableHead className="text-right">Disbursed</TableHead>
                    <TableHead>Request Date</TableHead>
                    <TableHead>Disbursement Date</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tranches.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="py-8 text-center text-muted-foreground">
                        No tranches found
                      </TableCell>
                    </TableRow>
                  ) : (
                    tranches.map((tranche) => (
                      <TableRow key={tranche.trancheId}>
                        <TableCell className="font-medium">#{tranche.trancheNumber}</TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={tranche.requestedAmount} abbreviated />
                        </TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={tranche.approvedAmount} abbreviated />
                        </TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={tranche.disbursedAmount} abbreviated />
                        </TableCell>
                        <TableCell>
                          <DateDisplay date={tranche.requestDate} />
                        </TableCell>
                        <TableCell>
                          {tranche.disbursementDate ? (
                            <DateDisplay date={tranche.disbursementDate} />
                          ) : (
                            '-'
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge className={statusColors[tranche.status] || ''}>
                            {tranche.status}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Schedule Tab */}
        <TabsContent value="schedule">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Repayment Schedule</CardTitle>
                <CardDescription>Principal and interest payment schedule</CardDescription>
              </div>
              <Button variant="outline">
                <Download className="mr-2 h-4 w-4" />
                Export Schedule
              </Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>#</TableHead>
                    <TableHead>Due Date</TableHead>
                    <TableHead className="text-right">Principal</TableHead>
                    <TableHead className="text-right">Interest</TableHead>
                    <TableHead className="text-right">Total Due</TableHead>
                    <TableHead className="text-right">Paid</TableHead>
                    <TableHead className="text-right">Balance</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {schedule.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                        No schedule generated
                      </TableCell>
                    </TableRow>
                  ) : (
                    schedule.map((item) => (
                      <TableRow key={item.scheduleId}>
                        <TableCell className="font-medium">{item.installmentNumber}</TableCell>
                        <TableCell>
                          <DateDisplay date={item.dueDate} />
                        </TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={item.principalDue} abbreviated />
                        </TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={item.interestDue} abbreviated />
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          <AmountDisplay amount={item.totalDue} abbreviated />
                        </TableCell>
                        <TableCell className="text-right text-green-600">
                          <AmountDisplay amount={item.totalPaid} abbreviated />
                        </TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={item.closingBalance} abbreviated />
                        </TableCell>
                        <TableCell>
                          <Badge className={statusColors[item.status] || ''}>{item.status}</Badge>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Payments Tab */}
        <TabsContent value="payments">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Payment History</CardTitle>
                <CardDescription>All payments made against this facility</CardDescription>
              </div>
              <Dialog open={showPaymentDialog} onOpenChange={setShowPaymentDialog}>
                <DialogTrigger asChild>
                  <Button>
                    <Receipt className="mr-2 h-4 w-4" />
                    Record Payment
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Record Payment</DialogTitle>
                    <DialogDescription>
                      Record a manual payment for this borrowing
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label>Payment Amount</Label>
                      <Input
                        type="number"
                        placeholder="Enter amount"
                        value={paymentAmount}
                        onChange={(e) => setPaymentAmount(e.target.value)}
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setShowPaymentDialog(false)}>
                      Cancel
                    </Button>
                    <Button
                      onClick={handlePayment}
                      disabled={paymentMutation.isPending || !paymentAmount}
                    >
                      {paymentMutation.isPending && (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      )}
                      Record Payment
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead className="text-right">Principal</TableHead>
                    <TableHead className="text-right">Interest</TableHead>
                    <TableHead className="text-right">Total</TableHead>
                    <TableHead>Reference</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {payments.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="py-8 text-center text-muted-foreground">
                        No payments recorded
                      </TableCell>
                    </TableRow>
                  ) : (
                    payments.map((payment) => {
                      const paymentStatus = payment.status ?? 'RECORDED';
                      const paymentReference = payment.utrNumber ?? payment.bankReference ?? '-';
                      return (
                        <TableRow key={payment.paymentId}>
                          <TableCell>
                            <DateDisplay date={payment.paymentDate} />
                          </TableCell>
                          <TableCell>{payment.paymentType}</TableCell>
                          <TableCell className="text-right">
                            <AmountDisplay amount={payment.principalAmount} abbreviated />
                          </TableCell>
                          <TableCell className="text-right">
                            <AmountDisplay amount={payment.interestAmount} abbreviated />
                          </TableCell>
                          <TableCell className="text-right font-medium">
                            <AmountDisplay amount={payment.totalAmount} abbreviated />
                          </TableCell>
                          <TableCell className="font-mono text-sm">{paymentReference}</TableCell>
                          <TableCell>
                            <Badge className={statusColors[paymentStatus] || ''}>
                              {paymentStatus}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      );
                    })
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
