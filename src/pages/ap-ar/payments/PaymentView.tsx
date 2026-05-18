import { format } from 'date-fns';
import {
  Edit,
  Send,
  Check,
  X,
  Printer,
  CreditCard,
  Building2,
  User,
  Calendar,
  Banknote,
  FileText,
  AlertCircle,
} from 'lucide-react';
import { useCallback, useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import { paymentsApi } from '@/services/api';

import { logger } from "@/lib/logger";
interface PaymentDetail {
  id: string;
  payment_number: string;
  payment_date: string;
  payment_type: string;
  party_type: string;
  vendor_id: string | null;
  customer_id: string | null;
  organization_id: string;
  unit_id: string | null;
  payment_mode: string;
  bank_account_id: string | null;
  cash_account_id: string | null;
  amount: number;
  tds_amount: number;
  tds_section_id: string | null;
  tds_rate: number;
  discount_amount: number;
  write_off_amount: number;
  net_amount: number;
  currency_code: string;
  cheque_number: string | null;
  cheque_date: string | null;
  cheque_bank_name: string | null;
  cheque_branch: string | null;
  cheque_status: string | null;
  cheque_cleared_date: string | null;
  cheque_bounced_date: string | null;
  cheque_bounced_reason: string | null;
  reference_number: string | null;
  narration: string | null;
  status: string;
  submitted_at: string | null;
  approved_at: string | null;
  cancelled_at: string | null;
  cancellation_reason: string | null;
  voucher_id: string | null;
  is_posted: boolean;
  posted_at: string | null;
  allocated_amount: number;
  unallocated_amount: number;
  vendor_name: string | null;
  customer_name: string | null;
  bank_account_name: string | null;
  cash_account_name: string | null;
  tds_section_code: string | null;
  created_at: string;
  allocations: {
    id: string;
    document_type: string;
    document_id: string;
    document_number: string;
    document_date: string;
    document_amount: number;
    outstanding_before: number;
    allocated_amount: number;
    allocation_date: string;
  }[];
}

const PAYMENT_TYPES: Record<string, string> = {
  VENDOR_PAYMENT: 'Vendor Payment',
  CUSTOMER_RECEIPT: 'Customer Receipt',
  ADVANCE_PAYMENT: 'Advance to Vendor',
  ADVANCE_RECEIPT: 'Advance from Customer',
  REFUND_PAYMENT: 'Refund to Customer',
  REFUND_RECEIPT: 'Refund from Vendor',
};

const PAYMENT_MODES: Record<string, string> = {
  CASH: 'Cash',
  CHEQUE: 'Cheque',
  NEFT: 'NEFT',
  RTGS: 'RTGS',
  IMPS: 'IMPS',
  UPI: 'UPI',
  BANK_TRANSFER: 'Bank Transfer',
  DEMAND_DRAFT: 'Demand Draft',
};

const CHEQUE_STATUS_COLORS: Record<string, string> = {
  ISSUED: 'bg-blue-100 text-blue-800',
  DEPOSITED: 'bg-yellow-100 text-yellow-800',
  CLEARED: 'bg-green-100 text-green-800',
  BOUNCED: 'bg-red-100 text-red-800',
  CANCELLED: 'bg-gray-100 text-gray-800',
  RETURNED: 'bg-orange-100 text-orange-800',
};

export function PaymentView() {
  const { id } = useParams();
  const { toast } = useToast();

  const [payment, setPayment] = useState<PaymentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [cancellationReason, setCancellationReason] = useState('');

  const loadPayment = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const response = await paymentsApi.get(id);
      setPayment(response.data);
    } catch (error) {
      logger.error('Failed to load payment:', error);
      toast({
        title: 'Error',
        description: 'Failed to load payment details',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [id, toast]);

  useEffect(() => {
    loadPayment();
  }, [loadPayment]);

  const handleSubmit = async () => {
    if (!payment) return;
    try {
      await paymentsApi.submit(payment.id);
      toast({ title: 'Success', description: 'Payment submitted for approval' });
      loadPayment();
    } catch (error) {
      showErrorToast(error, toast);
    }
  };

  const handleApprove = async () => {
    if (!payment) return;
    try {
      await paymentsApi.approve(payment.id);
      toast({ title: 'Success', description: 'Payment approved and posted' });
      loadPayment();
    } catch (error) {
      showErrorToast(error, toast);
    }
  };

  const handleCancel = async () => {
    if (!payment || !cancellationReason.trim()) return;
    try {
      await paymentsApi.cancel(payment.id, cancellationReason);
      toast({ title: 'Success', description: 'Payment cancelled' });
      setCancelDialogOpen(false);
      setCancellationReason('');
      loadPayment();
    } catch (error) {
      showErrorToast(error, toast);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      DRAFT: 'bg-gray-100 text-gray-800',
      SUBMITTED: 'bg-blue-100 text-blue-800',
      APPROVED: 'bg-green-100 text-green-800',
      POSTED: 'bg-green-100 text-green-800',
      CANCELLED: 'bg-red-100 text-red-800',
    };
    return <Badge className={styles[status] || 'bg-gray-100'}>{status}</Badge>;
  };

  if (loading) {
    return <div className="p-8 text-center">Loading...</div>;
  }

  if (!payment) {
    return <div className="p-8 text-center">Payment not found</div>;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={payment.payment_number}
        subtitle={PAYMENT_TYPES[payment.payment_type] || payment.payment_type}
        breadcrumbs={[
          { label: 'Payments', to: '/admin/ap-ar/payments' },
          { label: payment.payment_number },
        ]}
        actions={
          <div className="flex items-center gap-2">
            {getStatusBadge(payment.status)}
            {payment.is_posted && (
              <Badge variant="outline" className="bg-green-50">
                Posted
              </Badge>
            )}
            {payment.status === 'DRAFT' && (
              <>
                <Button variant="outline" asChild>
                  <Link to={`/admin/ap-ar/payments/${payment.id}/edit`}>
                    <Edit className="mr-2 h-4 w-4" />
                    Edit
                  </Link>
                </Button>
                <Button onClick={handleSubmit}>
                  <Send className="mr-2 h-4 w-4" />
                  Submit
                </Button>
              </>
            )}
            {payment.status === 'SUBMITTED' && (
              <>
                <Button variant="outline" onClick={() => setCancelDialogOpen(true)}>
                  <X className="mr-2 h-4 w-4" />
                  Reject
                </Button>
                <Button onClick={handleApprove}>
                  <Check className="mr-2 h-4 w-4" />
                  Approve
                </Button>
              </>
            )}
            {payment.status === 'POSTED' && (
              <Button variant="outline" onClick={() => setCancelDialogOpen(true)}>
                <X className="mr-2 h-4 w-4" />
                Cancel
              </Button>
            )}
            <Button variant="outline">
              <Printer className="mr-2 h-4 w-4" />
              Print
            </Button>
          </div>
        }
      />

      {payment.status === 'CANCELLED' && payment.cancellation_reason && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="mt-0.5 h-5 w-5 text-red-600" />
              <div>
                <p className="font-medium text-red-800">Payment Cancelled</p>
                <p className="text-sm text-red-700">{payment.cancellation_reason}</p>
                {payment.cancelled_at && (
                  <p className="mt-1 text-xs text-red-600">
                    Cancelled on {format(new Date(payment.cancelled_at), 'dd MMM yyyy HH:mm')}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          {/* Party Details */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {payment.party_type === 'VENDOR' ? (
                  <Building2 className="h-5 w-5" />
                ) : (
                  <User className="h-5 w-5" />
                )}
                {payment.party_type === 'VENDOR' ? 'Vendor' : 'Customer'} Details
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <p className="text-sm text-muted-foreground">
                    {payment.party_type === 'VENDOR' ? 'Vendor' : 'Customer'} Name
                  </p>
                  <p className="font-medium">
                    {payment.vendor_name || payment.customer_name || '-'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Party Type</p>
                  <p className="font-medium">{payment.party_type}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Payment Details */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5" />
                Payment Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <div>
                  <p className="text-sm text-muted-foreground">Payment Date</p>
                  <p className="font-medium">
                    {format(new Date(payment.payment_date), 'dd MMM yyyy')}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Payment Mode</p>
                  <p className="font-medium">
                    {PAYMENT_MODES[payment.payment_mode] || payment.payment_mode}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">
                    {payment.payment_mode === 'CASH' ? 'Cash Account' : 'Bank Account'}
                  </p>
                  <p className="font-medium">
                    {payment.bank_account_name || payment.cash_account_name || '-'}
                  </p>
                </div>
                {payment.reference_number && (
                  <div>
                    <p className="text-sm text-muted-foreground">Reference/UTR</p>
                    <p className="font-medium">{payment.reference_number}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Cheque Details */}
          {payment.payment_mode === 'CHEQUE' && payment.cheque_number && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Cheque Details
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <p className="text-sm text-muted-foreground">Cheque Number</p>
                    <p className="font-medium">{payment.cheque_number}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Cheque Date</p>
                    <p className="font-medium">
                      {payment.cheque_date
                        ? format(new Date(payment.cheque_date), 'dd MMM yyyy')
                        : '-'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Cheque Status</p>
                    {payment.cheque_status && (
                      <Badge className={CHEQUE_STATUS_COLORS[payment.cheque_status]}>
                        {payment.cheque_status}
                      </Badge>
                    )}
                  </div>
                  {payment.cheque_bank_name && (
                    <div>
                      <p className="text-sm text-muted-foreground">Bank Name</p>
                      <p className="font-medium">{payment.cheque_bank_name}</p>
                    </div>
                  )}
                  {payment.cheque_branch && (
                    <div>
                      <p className="text-sm text-muted-foreground">Branch</p>
                      <p className="font-medium">{payment.cheque_branch}</p>
                    </div>
                  )}
                  {payment.cheque_cleared_date && (
                    <div>
                      <p className="text-sm text-muted-foreground">Cleared Date</p>
                      <p className="font-medium">
                        {format(new Date(payment.cheque_cleared_date), 'dd MMM yyyy')}
                      </p>
                    </div>
                  )}
                  {payment.cheque_bounced_date && (
                    <div className="md:col-span-3">
                      <p className="text-sm text-muted-foreground">Bounced</p>
                      <p className="font-medium text-red-600">
                        {format(new Date(payment.cheque_bounced_date), 'dd MMM yyyy')} -{' '}
                        {payment.cheque_bounced_reason}
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Allocations */}
          {payment.allocations && payment.allocations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Payment Allocations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Document</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Document Date</TableHead>
                        <TableHead className="text-right">Document Amount</TableHead>
                        <TableHead className="text-right">Outstanding Before</TableHead>
                        <TableHead className="text-right">Allocated</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {payment.allocations.map((alloc) => (
                        <TableRow key={alloc.id}>
                          <TableCell className="font-medium">{alloc.document_number}</TableCell>
                          <TableCell>{alloc.document_type.replace('_', ' ')}</TableCell>
                          <TableCell>
                            {format(new Date(alloc.document_date), 'dd MMM yyyy')}
                          </TableCell>
                          <TableCell className="text-right">
                            {formatCurrency(alloc.document_amount)}
                          </TableCell>
                          <TableCell className="text-right">
                            {formatCurrency(alloc.outstanding_before)}
                          </TableCell>
                          <TableCell className="text-right font-medium">
                            {formatCurrency(alloc.allocated_amount)}
                          </TableCell>
                        </TableRow>
                      ))}
                      <TableRow className="bg-muted/50">
                        <TableCell colSpan={5} className="font-medium">
                          Total Allocated
                        </TableCell>
                        <TableCell className="text-right font-semibold">
                          {formatCurrency(payment.allocated_amount)}
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Narration */}
          {payment.narration && (
            <Card>
              <CardHeader>
                <CardTitle>Narration</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">{payment.narration}</p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Summary Sidebar */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Payment Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Gross Amount</span>
                <span className="font-medium">{formatCurrency(payment.amount)}</span>
              </div>
              {payment.tds_amount > 0 && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">
                    TDS ({payment.tds_section_code} @ {payment.tds_rate}%)
                  </span>
                  <span className="font-medium text-red-600">
                    -{formatCurrency(payment.tds_amount)}
                  </span>
                </div>
              )}
              {payment.discount_amount > 0 && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Discount</span>
                  <span className="font-medium text-red-600">
                    -{formatCurrency(payment.discount_amount)}
                  </span>
                </div>
              )}
              {payment.write_off_amount > 0 && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Write Off</span>
                  <span className="font-medium text-red-600">
                    -{formatCurrency(payment.write_off_amount)}
                  </span>
                </div>
              )}
              <Separator />
              <div className="flex justify-between text-lg font-semibold">
                <span>Net {payment.party_type === 'VENDOR' ? 'Payment' : 'Receipt'}</span>
                <span>{formatCurrency(payment.net_amount)}</span>
              </div>

              {payment.allocations && payment.allocations.length > 0 && (
                <>
                  <Separator />
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Allocated</span>
                    <span className="font-medium">{formatCurrency(payment.allocated_amount)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Unallocated</span>
                    <span className="font-medium">
                      {formatCurrency(payment.unallocated_amount)}
                    </span>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Timeline</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-3 text-sm">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="font-medium">Created</p>
                  <p className="text-muted-foreground">
                    {format(new Date(payment.created_at), 'dd MMM yyyy HH:mm')}
                  </p>
                </div>
              </div>
              {payment.submitted_at && (
                <div className="flex items-center gap-3 text-sm">
                  <Send className="h-4 w-4 text-blue-600" />
                  <div>
                    <p className="font-medium">Submitted</p>
                    <p className="text-muted-foreground">
                      {format(new Date(payment.submitted_at), 'dd MMM yyyy HH:mm')}
                    </p>
                  </div>
                </div>
              )}
              {payment.approved_at && (
                <div className="flex items-center gap-3 text-sm">
                  <Check className="h-4 w-4 text-green-600" />
                  <div>
                    <p className="font-medium">Approved</p>
                    <p className="text-muted-foreground">
                      {format(new Date(payment.approved_at), 'dd MMM yyyy HH:mm')}
                    </p>
                  </div>
                </div>
              )}
              {payment.posted_at && (
                <div className="flex items-center gap-3 text-sm">
                  <Banknote className="h-4 w-4 text-green-600" />
                  <div>
                    <p className="font-medium">Posted</p>
                    <p className="text-muted-foreground">
                      {format(new Date(payment.posted_at), 'dd MMM yyyy HH:mm')}
                    </p>
                  </div>
                </div>
              )}
              {payment.cancelled_at && (
                <div className="flex items-center gap-3 text-sm">
                  <X className="h-4 w-4 text-red-600" />
                  <div>
                    <p className="font-medium">Cancelled</p>
                    <p className="text-muted-foreground">
                      {format(new Date(payment.cancelled_at), 'dd MMM yyyy HH:mm')}
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Cancel Dialog */}
      <AlertDialog open={cancelDialogOpen} onOpenChange={setCancelDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancel Payment</AlertDialogTitle>
            <AlertDialogDescription>
              Please provide a reason for cancelling this payment. This action will reverse any
              document allocations.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="py-4">
            <Label htmlFor="reason">Cancellation Reason</Label>
            <Textarea
              id="reason"
              value={cancellationReason}
              onChange={(e) => setCancellationReason(e.target.value)}
              placeholder="Enter reason for cancellation..."
              className="mt-2"
            />
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setCancellationReason('')}>Back</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleCancel}
              disabled={!cancellationReason.trim()}
              className="bg-red-600"
            >
              Cancel Payment
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
