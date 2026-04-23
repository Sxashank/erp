import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Edit,
  Loader2,
  Calendar,
  DollarSign,
  Clock,
  Building2,
  AlertTriangle,
  Plus,
  Receipt,
  FileText,
  RefreshCw,
  Download,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
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
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { treasuryApi } from '@/services/lending/treasuryApi';
import { useToast } from '@/hooks/use-toast';

interface BorrowingDetail {
  borrowing_id: string;
  borrowing_number: string;
  lender_id: string;
  lender_name: string;
  lender_type: string;
  facility_type: string;
  facility_name: string;
  sanctioned_amount: number;
  drawn_amount: number;
  outstanding_principal: number;
  outstanding_interest: number;
  total_outstanding: number;
  available_limit: number;
  interest_type: string;
  base_rate_type: string;
  base_rate_value: number;
  spread_bps: number;
  effective_rate: number;
  sanction_date: string;
  first_drawdown_date: string;
  maturity_date: string;
  tenure_months: number;
  repayment_frequency: string;
  status: string;
  security_type: string;
  security_description: string;
  remarks: string;
  created_at: string;
  updated_at: string;
}

interface Tranche {
  tranche_id: string;
  tranche_number: number;
  request_date: string;
  requested_amount: number;
  approved_amount: number;
  disbursed_amount: number;
  drawdown_date: string;
  approval_date: string;
  disbursement_date: string;
  status: string;
  remarks: string;
}

interface ScheduleItem {
  schedule_id: string;
  installment_number: number;
  due_date: string;
  principal_due: number;
  interest_due: number;
  total_due: number;
  principal_paid: number;
  interest_paid: number;
  total_paid: number;
  opening_balance: number;
  closing_balance: number;
  status: string;
}

interface Payment {
  payment_id: string;
  payment_date: string;
  value_date: string;
  payment_type: string;
  principal_amount: number;
  interest_amount: number;
  total_amount: number;
  reference: string;
  status: string;
  remarks: string;
}

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
  const [loading, setLoading] = useState(true);
  const [borrowing, setBorrowing] = useState<BorrowingDetail | null>(null);
  const [tranches, setTranches] = useState<Tranche[]>([]);
  const [schedule, setSchedule] = useState<ScheduleItem[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [showDrawdownDialog, setShowDrawdownDialog] = useState(false);
  const [showPaymentDialog, setShowPaymentDialog] = useState(false);
  const [drawdownAmount, setDrawdownAmount] = useState('');
  const [paymentAmount, setPaymentAmount] = useState('');
  const [savingDrawdown, setSavingDrawdown] = useState(false);
  const [savingPayment, setSavingPayment] = useState(false);

  const fetchBorrowing = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await treasuryApi.getBorrowing(id);
      setBorrowing(data as unknown as BorrowingDetail);

      // Fetch tranches
      try {
        const tranchesData = await treasuryApi.getTranches(id);
        setTranches((tranchesData as any) || []);
      } catch {
        setTranches([]);
      }

      // Fetch schedule
      try {
        const scheduleData = await treasuryApi.getBorrowingSchedule(id);
        setSchedule((scheduleData as any) || []);
      } catch {
        setSchedule([]);
      }

      // Fetch payments
      try {
        const paymentsData = await treasuryApi.getRepaymentHistory(id);
        setPayments((paymentsData as any) || []);
      } catch {
        setPayments([]);
      }
    } catch (error) {
      console.error('Failed to fetch borrowing:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to load borrowing details',
      });
      // Use mock data for demonstration
      setBorrowing({
        borrowing_id: id,
        borrowing_number: 'BOR/HDFC/2024/001',
        lender_id: '1',
        lender_name: 'HDFC Bank Ltd',
        lender_type: 'BANK',
        facility_type: 'TERM_LOAN',
        facility_name: 'Term Loan Facility',
        sanctioned_amount: 1000000000,
        drawn_amount: 850000000,
        outstanding_principal: 850000000,
        outstanding_interest: 6562500,
        total_outstanding: 856562500,
        available_limit: 150000000,
        interest_type: 'FLOATING',
        base_rate_type: 'MCLR',
        base_rate_value: 8.50,
        spread_bps: 75,
        effective_rate: 9.25,
        sanction_date: '2024-01-15',
        first_drawdown_date: '2024-02-01',
        maturity_date: '2029-01-15',
        tenure_months: 60,
        repayment_frequency: 'QUARTERLY',
        status: 'ACTIVE',
        security_type: 'SECURED',
        security_description: 'First charge on receivables, personal guarantee of promoters',
        remarks: 'Facility for working capital requirements',
        created_at: '2024-01-15',
        updated_at: '2025-01-15',
      });

      setTranches([
        { tranche_id: '1', tranche_number: 1, request_date: '2024-01-28', requested_amount: 500000000, approved_amount: 500000000, disbursed_amount: 500000000, drawdown_date: '2024-02-01', approval_date: '2024-02-02', disbursement_date: '2024-02-05', status: 'DISBURSED', remarks: 'Initial drawdown' },
        { tranche_id: '2', tranche_number: 2, request_date: '2024-06-10', requested_amount: 350000000, approved_amount: 350000000, disbursed_amount: 350000000, drawdown_date: '2024-06-15', approval_date: '2024-06-16', disbursement_date: '2024-06-20', status: 'DISBURSED', remarks: 'Second tranche' },
      ]);

      setSchedule([
        { schedule_id: '1', installment_number: 1, due_date: '2024-05-15', principal_due: 50000000, interest_due: 7812500, total_due: 57812500, principal_paid: 50000000, interest_paid: 7812500, total_paid: 57812500, opening_balance: 500000000, closing_balance: 450000000, status: 'PAID' },
        { schedule_id: '2', installment_number: 2, due_date: '2024-08-15', principal_due: 50000000, interest_due: 7031250, total_due: 57031250, principal_paid: 50000000, interest_paid: 7031250, total_paid: 57031250, opening_balance: 800000000, closing_balance: 750000000, status: 'PAID' },
        { schedule_id: '3', installment_number: 3, due_date: '2024-11-15', principal_due: 50000000, interest_due: 6718750, total_due: 56718750, principal_paid: 50000000, interest_paid: 6718750, total_paid: 56718750, opening_balance: 750000000, closing_balance: 700000000, status: 'PAID' },
        { schedule_id: '4', installment_number: 4, due_date: '2025-02-15', principal_due: 50000000, interest_due: 6562500, total_due: 56562500, principal_paid: 0, interest_paid: 0, total_paid: 0, opening_balance: 700000000, closing_balance: 650000000, status: 'PENDING' },
        { schedule_id: '5', installment_number: 5, due_date: '2025-05-15', principal_due: 50000000, interest_due: 5812500, total_due: 55812500, principal_paid: 0, interest_paid: 0, total_paid: 0, opening_balance: 650000000, closing_balance: 600000000, status: 'PENDING' },
      ]);

      setPayments([
        { payment_id: '1', payment_date: '2024-05-15', value_date: '2024-05-15', payment_type: 'SCHEDULED', principal_amount: 50000000, interest_amount: 7812500, total_amount: 57812500, reference: 'NEFT/2024/001', status: 'COMPLETED', remarks: '' },
        { payment_id: '2', payment_date: '2024-08-15', value_date: '2024-08-15', payment_type: 'SCHEDULED', principal_amount: 50000000, interest_amount: 7031250, total_amount: 57031250, reference: 'NEFT/2024/002', status: 'COMPLETED', remarks: '' },
        { payment_id: '3', payment_date: '2024-11-15', value_date: '2024-11-15', payment_type: 'SCHEDULED', principal_amount: 50000000, interest_amount: 6718750, total_amount: 56718750, reference: 'NEFT/2024/003', status: 'COMPLETED', remarks: '' },
      ]);
    } finally {
      setLoading(false);
    }
  }, [id, toast]);

  useEffect(() => {
    fetchBorrowing();
  }, [fetchBorrowing]);

  const handleDrawdown = async () => {
    if (!id || !drawdownAmount) return;
    setSavingDrawdown(true);
    try {
      await treasuryApi.recordDrawdown(id, {
        amount: Number(drawdownAmount),
        drawdown_date: new Date().toISOString().split('T')[0],
        remarks: 'Drawdown request',
      });
      toast({
        title: 'Success',
        description: 'Drawdown request submitted',
      });
      setShowDrawdownDialog(false);
      setDrawdownAmount('');
      fetchBorrowing();
    } catch (error) {
      console.error('Failed to create drawdown:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to submit drawdown request',
      });
    } finally {
      setSavingDrawdown(false);
    }
  };

  const handlePayment = async () => {
    if (!id || !paymentAmount) return;
    setSavingPayment(true);
    try {
      await treasuryApi.recordRepayment(id, {
        payment_date: new Date().toISOString().split('T')[0],
        principal_amount: Number(paymentAmount),
        interest_amount: 0,
        remarks: 'Manual payment',
      });
      toast({
        title: 'Success',
        description: 'Payment recorded successfully',
      });
      setShowPaymentDialog(false);
      setPaymentAmount('');
      fetchBorrowing();
    } catch (error) {
      console.error('Failed to record payment:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to record payment',
      });
    } finally {
      setSavingPayment(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!borrowing) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <AlertTriangle className="h-12 w-12 text-muted-foreground mb-4" />
        <p className="text-muted-foreground">Borrowing not found</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate(-1)}>
          Go Back
        </Button>
      </div>
    );
  }

  const utilizationPercent = (borrowing.drawn_amount / borrowing.sanctioned_amount) * 100;
  const nextScheduleItem = schedule.find((s) => s.status === 'PENDING');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-semibold">{borrowing.borrowing_number}</h1>
              <Badge className={statusColors[borrowing.status] || ''}>
                {borrowing.status}
              </Badge>
            </div>
            <p className="text-muted-foreground">
              {borrowing.facility_type.replace('_', ' ')} from {borrowing.lender_name}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchBorrowing}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button
            variant="outline"
            onClick={() => navigate(`/admin/lending/treasury/borrowings/${id}/edit`)}
          >
            <Edit className="mr-2 h-4 w-4" />
            Edit
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sanctioned Amount</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={borrowing.sanctioned_amount} abbreviated className="text-2xl font-bold" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Outstanding</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={borrowing.total_outstanding}
              abbreviated
              className="text-2xl font-bold text-amber-600"
            />
            <div className="flex items-center gap-2 mt-1">
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
              <PercentageDisplay value={borrowing.effective_rate} /> p.a.
            </div>
            <p className="text-xs text-muted-foreground">
              {borrowing.interest_type === 'FLOATING'
                ? `${borrowing.base_rate_type} + ${borrowing.spread_bps} bps`
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
                  amount={nextScheduleItem.total_due}
                  abbreviated
                  className="text-2xl font-bold text-red-600"
                />
                <p className="text-xs text-muted-foreground">
                  Due on <DateDisplay date={nextScheduleItem.due_date} />
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
                    <p className="font-medium">{borrowing.lender_name}</p>
                    <p className="text-xs text-muted-foreground">{borrowing.lender_type}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Facility Type</p>
                    <p className="font-medium">{borrowing.facility_type.replace('_', ' ')}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Sanction Date</p>
                    <p className="font-medium">
                      <DateDisplay date={borrowing.sanction_date} />
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Maturity Date</p>
                    <p className="font-medium">
                      <DateDisplay date={borrowing.maturity_date} />
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Tenure</p>
                    <p className="font-medium">{borrowing.tenure_months} months</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Repayment Frequency</p>
                    <p className="font-medium">{borrowing.repayment_frequency}</p>
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
                    <p className="font-medium">{borrowing.interest_type}</p>
                  </div>
                  {borrowing.interest_type === 'FLOATING' && (
                    <>
                      <div>
                        <p className="text-muted-foreground">Base Rate</p>
                        <p className="font-medium">
                          {borrowing.base_rate_type}: <PercentageDisplay value={borrowing.base_rate_value} />
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Spread</p>
                        <p className="font-medium">{borrowing.spread_bps} bps</p>
                      </div>
                    </>
                  )}
                  <div>
                    <p className="text-muted-foreground">Effective Rate</p>
                    <p className="font-medium text-lg">
                      <PercentageDisplay value={borrowing.effective_rate} /> p.a.
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
                    <AmountDisplay amount={borrowing.sanctioned_amount} abbreviated className="font-medium" />
                  </div>
                  <div>
                    <p className="text-muted-foreground">Drawn</p>
                    <AmountDisplay amount={borrowing.drawn_amount} abbreviated className="font-medium" />
                  </div>
                  <div>
                    <p className="text-muted-foreground">Outstanding Principal</p>
                    <AmountDisplay amount={borrowing.outstanding_principal} abbreviated className="font-medium" />
                  </div>
                  <div>
                    <p className="text-muted-foreground">Outstanding Interest</p>
                    <AmountDisplay amount={borrowing.outstanding_interest} abbreviated className="font-medium" />
                  </div>
                  <div>
                    <p className="text-muted-foreground">Total Outstanding</p>
                    <AmountDisplay amount={borrowing.total_outstanding} abbreviated className="font-medium text-lg text-amber-600" />
                  </div>
                  <div>
                    <p className="text-muted-foreground">Available Limit</p>
                    <AmountDisplay amount={borrowing.available_limit} abbreviated className="font-medium text-green-600" />
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
                    <p className="font-medium">{borrowing.security_type}</p>
                  </div>
                  {borrowing.security_description && (
                    <div>
                      <p className="text-muted-foreground">Description</p>
                      <p className="font-medium">{borrowing.security_description}</p>
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
                  <Button disabled={borrowing.available_limit <= 0}>
                    <Plus className="mr-2 h-4 w-4" />
                    Request Drawdown
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Request Drawdown</DialogTitle>
                    <DialogDescription>
                      Available limit:{' '}
                      <AmountDisplay amount={borrowing.available_limit} abbreviated />
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
                        max={borrowing.available_limit}
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setShowDrawdownDialog(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleDrawdown} disabled={savingDrawdown || !drawdownAmount}>
                      {savingDrawdown && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
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
                      <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                        No tranches found
                      </TableCell>
                    </TableRow>
                  ) : (
                    tranches.map((tranche) => (
                      <TableRow key={tranche.tranche_id}>
                        <TableCell className="font-medium">#{tranche.tranche_number}</TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={tranche.requested_amount} abbreviated />
                        </TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={tranche.approved_amount} abbreviated />
                        </TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={tranche.disbursed_amount} abbreviated />
                        </TableCell>
                        <TableCell>
                          <DateDisplay date={tranche.request_date} />
                        </TableCell>
                        <TableCell>
                          {tranche.disbursement_date ? (
                            <DateDisplay date={tranche.disbursement_date} />
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
                      <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                        No schedule generated
                      </TableCell>
                    </TableRow>
                  ) : (
                    schedule.map((item) => (
                      <TableRow key={item.schedule_id}>
                        <TableCell className="font-medium">{item.installment_number}</TableCell>
                        <TableCell>
                          <DateDisplay date={item.due_date} />
                        </TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={item.principal_due} abbreviated />
                        </TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={item.interest_due} abbreviated />
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          <AmountDisplay amount={item.total_due} abbreviated />
                        </TableCell>
                        <TableCell className="text-right text-green-600">
                          <AmountDisplay amount={item.total_paid} abbreviated />
                        </TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={item.closing_balance} abbreviated />
                        </TableCell>
                        <TableCell>
                          <Badge className={statusColors[item.status] || ''}>
                            {item.status}
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
                    <Button onClick={handlePayment} disabled={savingPayment || !paymentAmount}>
                      {savingPayment && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
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
                      <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                        No payments recorded
                      </TableCell>
                    </TableRow>
                  ) : (
                    payments.map((payment) => (
                      <TableRow key={payment.payment_id}>
                        <TableCell>
                          <DateDisplay date={payment.payment_date} />
                        </TableCell>
                        <TableCell>{payment.payment_type}</TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={payment.principal_amount} abbreviated />
                        </TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={payment.interest_amount} abbreviated />
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          <AmountDisplay amount={payment.total_amount} abbreviated />
                        </TableCell>
                        <TableCell className="font-mono text-sm">{payment.reference}</TableCell>
                        <TableCell>
                          <Badge className={statusColors[payment.status] || ''}>
                            {payment.status}
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
      </Tabs>
    </div>
  );
}
