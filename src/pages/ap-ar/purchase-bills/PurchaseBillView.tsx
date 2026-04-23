import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Loader2, Edit, Send, CheckCircle, XCircle, Printer } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
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
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import { purchaseBillsApi, vendorsApi } from '@/services/api';

interface BillLine {
  id: string;
  line_number: number;
  description: string;
  hsn_sac_code: string | null;
  quantity: number;
  unit_price: number;
  discount_percent: number;
  discount_amount: number;
  taxable_amount: number;
  cgst_rate: number;
  cgst_amount: number;
  sgst_rate: number;
  sgst_amount: number;
  igst_rate: number;
  igst_amount: number;
  cess_rate: number;
  cess_amount: number;
  total_amount: number;
}

interface PurchaseBill {
  id: string;
  bill_number: string;
  vendor_invoice_number: string | null;
  vendor_invoice_date: string | null;
  bill_date: string;
  due_date: string;
  vendor_id: string;
  organization_id: string;
  unit_id: string | null;
  subtotal: number;
  discount_amount: number;
  taxable_amount: number;
  cgst_amount: number;
  sgst_amount: number;
  igst_amount: number;
  cess_amount: number;
  tds_amount: number;
  round_off: number;
  total_amount: number;
  balance_amount: number;
  is_reverse_charge: boolean;
  supply_type: string | null;
  vendor_gstin: string | null;
  place_of_supply: string | null;
  status: string;
  payment_status: string;
  is_posted: boolean;
  narration: string | null;
  reference_number: string | null;
  lines: BillLine[];
  created_at: string;
  updated_at: string | null;
}

interface Vendor {
  id: string;
  code: string;
  name: string;
  display_name: string | null;
  gstin: string | null;
  pan: string | null;
  address_line1: string | null;
  city: string | null;
  state_code: string | null;
  pincode: string | null;
}

const statusLabels: Record<string, string> = {
  DRAFT: 'Draft',
  SUBMITTED: 'Submitted',
  APPROVED: 'Approved',
  PARTIALLY_PAID: 'Partially Paid',
  PAID: 'Paid',
  CANCELLED: 'Cancelled',
};

const statusColors: Record<string, string> = {
  DRAFT: 'bg-slate-100 text-slate-800',
  SUBMITTED: 'bg-yellow-100 text-yellow-800',
  APPROVED: 'bg-blue-100 text-blue-800',
  PARTIALLY_PAID: 'bg-orange-100 text-orange-800',
  PAID: 'bg-green-100 text-green-800',
  CANCELLED: 'bg-red-100 text-red-800',
};

const paymentStatusLabels: Record<string, string> = {
  UNPAID: 'Unpaid',
  PARTIALLY_PAID: 'Partially Paid',
  PAID: 'Paid',
};

const paymentStatusColors: Record<string, string> = {
  UNPAID: 'bg-red-100 text-red-800',
  PARTIALLY_PAID: 'bg-orange-100 text-orange-800',
  PAID: 'bg-green-100 text-green-800',
};

export function PurchaseBillView() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [bill, setBill] = useState<PurchaseBill | null>(null);
  const [vendor, setVendor] = useState<Vendor | null>(null);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState('');

  useEffect(() => {
    if (id) {
      loadBill(id);
    }
  }, [id]);

  const loadBill = async (billId: string) => {
    try {
      setLoading(true);
      const response = await purchaseBillsApi.get(billId);
      setBill(response.data);

      // Load vendor details
      if (response.data.vendor_id) {
        const vendorResponse = await vendorsApi.get(response.data.vendor_id);
        setVendor(vendorResponse.data);
      }
    } catch (error) {
      console.error('Failed to load bill:', error);
      toast({
        title: 'Error',
        description: 'Failed to load purchase bill',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!bill) return;
    try {
      await purchaseBillsApi.submit(bill.id);
      toast({
        title: 'Success',
        description: 'Purchase bill submitted for approval',
      });
      loadBill(bill.id);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to submit purchase bill',
        variant: 'destructive',
      });
    }
  };

  const handleApprove = async () => {
    if (!bill) return;
    try {
      await purchaseBillsApi.approve(bill.id);
      toast({
        title: 'Success',
        description: 'Purchase bill approved successfully',
      });
      loadBill(bill.id);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to approve purchase bill',
        variant: 'destructive',
      });
    }
  };

  const handleCancel = async () => {
    if (!bill || !cancelReason) return;
    try {
      await purchaseBillsApi.cancel(bill.id, cancelReason);
      toast({
        title: 'Success',
        description: 'Purchase bill cancelled successfully',
      });
      loadBill(bill.id);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to cancel purchase bill',
        variant: 'destructive',
      });
    } finally {
      setCancelDialogOpen(false);
      setCancelReason('');
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  };

  const isIntraState = () => {
    return bill?.supply_type === 'INTRA_STATE';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  if (!bill) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-500">Purchase bill not found</p>
        <Button
          variant="outline"
          onClick={() => navigate('/admin/ap-ar/purchase-bills')}
          className="mt-4"
        >
          Back to List
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/admin/ap-ar/purchase-bills')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-900">{bill.bill_number}</h1>
              <Badge variant="secondary" className={statusColors[bill.status]}>
                {statusLabels[bill.status]}
              </Badge>
              <Badge variant="secondary" className={paymentStatusColors[bill.payment_status]}>
                {paymentStatusLabels[bill.payment_status]}
              </Badge>
            </div>
            <p className="text-sm text-slate-500">
              Created on {formatDate(bill.created_at)}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {bill.status === 'DRAFT' && (
            <>
              <Button variant="outline" onClick={() => navigate(`/admin/ap-ar/purchase-bills/${bill.id}/edit`)}>
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </Button>
              <Button onClick={handleSubmit}>
                <Send className="mr-2 h-4 w-4" />
                Submit
              </Button>
            </>
          )}
          {bill.status === 'SUBMITTED' && (
            <Button onClick={handleApprove}>
              <CheckCircle className="mr-2 h-4 w-4" />
              Approve
            </Button>
          )}
          {bill.status !== 'CANCELLED' && bill.payment_status === 'UNPAID' && (
            <Button variant="outline" onClick={() => setCancelDialogOpen(true)}>
              <XCircle className="mr-2 h-4 w-4" />
              Cancel
            </Button>
          )}
          <Button variant="outline">
            <Printer className="mr-2 h-4 w-4" />
            Print
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Vendor Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Vendor Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="font-medium">{vendor?.name}</div>
            {vendor?.display_name && vendor.display_name !== vendor.name && (
              <div className="text-slate-500">{vendor.display_name}</div>
            )}
            {vendor?.address_line1 && (
              <div className="text-slate-600">
                {vendor.address_line1}
                {vendor.city && `, ${vendor.city}`}
                {vendor.state_code && ` - ${vendor.state_code}`}
                {vendor.pincode && `, ${vendor.pincode}`}
              </div>
            )}
            {vendor?.gstin && (
              <div>
                <span className="text-slate-500">GSTIN: </span>
                <span className="font-mono">{vendor.gstin}</span>
              </div>
            )}
            {vendor?.pan && (
              <div>
                <span className="text-slate-500">PAN: </span>
                <span className="font-mono">{vendor.pan}</span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Bill Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Bill Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-500">Bill Number</span>
              <span className="font-medium">{bill.bill_number}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Vendor Invoice</span>
              <span className="font-mono">{bill.vendor_invoice_number || '-'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Vendor Invoice Date</span>
              <span>{formatDate(bill.vendor_invoice_date)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Bill Date</span>
              <span>{formatDate(bill.bill_date)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Due Date</span>
              <span>{formatDate(bill.due_date)}</span>
            </div>
            {bill.reference_number && (
              <div className="flex justify-between">
                <span className="text-slate-500">Reference</span>
                <span>{bill.reference_number}</span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* GST Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">GST Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-500">Supply Type</span>
              <span>{bill.supply_type === 'INTRA_STATE' ? 'Intra State' : 'Inter State'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Place of Supply</span>
              <span>{bill.place_of_supply || '-'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Vendor GSTIN</span>
              <span className="font-mono">{bill.vendor_gstin || '-'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Reverse Charge</span>
              <span>{bill.is_reverse_charge ? 'Yes' : 'No'}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Line Items */}
      <Card>
        <CardHeader>
          <CardTitle>Line Items</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[40px]">#</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>HSN/SAC</TableHead>
                <TableHead className="text-right">Qty</TableHead>
                <TableHead className="text-right">Unit Price</TableHead>
                <TableHead className="text-right">Discount</TableHead>
                <TableHead className="text-right">Taxable</TableHead>
                {isIntraState() ? (
                  <>
                    <TableHead className="text-right">CGST</TableHead>
                    <TableHead className="text-right">SGST</TableHead>
                  </>
                ) : (
                  <TableHead className="text-right">IGST</TableHead>
                )}
                <TableHead className="text-right">Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {bill.lines.map((line) => (
                <TableRow key={line.id}>
                  <TableCell>{line.line_number}</TableCell>
                  <TableCell>{line.description}</TableCell>
                  <TableCell className="font-mono text-sm">{line.hsn_sac_code || '-'}</TableCell>
                  <TableCell className="text-right">{line.quantity}</TableCell>
                  <TableCell className="text-right">{formatCurrency(line.unit_price)}</TableCell>
                  <TableCell className="text-right">
                    {line.discount_amount > 0 ? formatCurrency(line.discount_amount) : '-'}
                  </TableCell>
                  <TableCell className="text-right">{formatCurrency(line.taxable_amount)}</TableCell>
                  {isIntraState() ? (
                    <>
                      <TableCell className="text-right text-sm">
                        {formatCurrency(line.cgst_amount)}
                        <span className="text-slate-400 block">@{line.cgst_rate}%</span>
                      </TableCell>
                      <TableCell className="text-right text-sm">
                        {formatCurrency(line.sgst_amount)}
                        <span className="text-slate-400 block">@{line.sgst_rate}%</span>
                      </TableCell>
                    </>
                  ) : (
                    <TableCell className="text-right text-sm">
                      {formatCurrency(line.igst_amount)}
                      <span className="text-slate-400 block">@{line.igst_rate}%</span>
                    </TableCell>
                  )}
                  <TableCell className="text-right font-medium">{formatCurrency(line.total_amount)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Summary */}
      <div className="grid gap-6 md:grid-cols-2">
        {bill.narration && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Narration</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-600 whitespace-pre-wrap">{bill.narration}</p>
            </CardContent>
          </Card>
        )}

        <Card className={bill.narration ? '' : 'md:col-start-2'}>
          <CardHeader>
            <CardTitle className="text-base">Bill Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-600">Subtotal</span>
              <span>{formatCurrency(bill.subtotal)}</span>
            </div>
            {bill.discount_amount > 0 && (
              <div className="flex justify-between text-green-600">
                <span>Discount</span>
                <span>- {formatCurrency(bill.discount_amount)}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-slate-600">Taxable Amount</span>
              <span>{formatCurrency(bill.taxable_amount)}</span>
            </div>
            {isIntraState() ? (
              <>
                <div className="flex justify-between">
                  <span className="text-slate-600">CGST</span>
                  <span>{formatCurrency(bill.cgst_amount)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">SGST</span>
                  <span>{formatCurrency(bill.sgst_amount)}</span>
                </div>
              </>
            ) : (
              <div className="flex justify-between">
                <span className="text-slate-600">IGST</span>
                <span>{formatCurrency(bill.igst_amount)}</span>
              </div>
            )}
            {bill.cess_amount > 0 && (
              <div className="flex justify-between">
                <span className="text-slate-600">Cess</span>
                <span>{formatCurrency(bill.cess_amount)}</span>
              </div>
            )}
            {bill.tds_amount > 0 && (
              <div className="flex justify-between text-orange-600">
                <span>TDS Deducted</span>
                <span>- {formatCurrency(bill.tds_amount)}</span>
              </div>
            )}
            {bill.round_off !== 0 && (
              <div className="flex justify-between">
                <span className="text-slate-600">Round Off</span>
                <span>{formatCurrency(bill.round_off)}</span>
              </div>
            )}
            <div className="border-t pt-2 flex justify-between font-bold">
              <span>Total Amount</span>
              <span>{formatCurrency(bill.total_amount)}</span>
            </div>
            <div className="flex justify-between text-blue-600">
              <span>Balance Due</span>
              <span className="font-bold">{formatCurrency(bill.balance_amount)}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Cancel Dialog */}
      <AlertDialog open={cancelDialogOpen} onOpenChange={setCancelDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancel Purchase Bill</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to cancel bill "{bill.bill_number}"?
              Please provide a reason for cancellation.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="py-4">
            <Input
              placeholder="Cancellation reason"
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
            />
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleCancel}
              disabled={!cancelReason}
              className="bg-orange-600 hover:bg-orange-700"
            >
              Cancel Bill
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
