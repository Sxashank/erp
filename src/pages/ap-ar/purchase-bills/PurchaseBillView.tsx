import { Loader2, Edit, Send, CheckCircle, XCircle, Printer } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { AmountDisplay } from '@/components/common/AmountDisplay';
import { DateDisplay } from '@/components/common/DateDisplay';
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
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import { purchaseBillsApi, vendorsApi } from '@/services/api';

import { logger } from "@/lib/logger";
interface BillLine {
  id: string;
  lineNumber: number;
  description: string;
  hsnSacCode: string | null;
  quantity: number;
  unitPrice: number;
  discountPercent: number;
  discountAmount: number;
  taxableAmount: number;
  cgstRate: number;
  cgstAmount: number;
  sgstRate: number;
  sgstAmount: number;
  igstRate: number;
  igstAmount: number;
  cessRate: number;
  cessAmount: number;
  totalAmount: number;
}

interface PurchaseBill {
  id: string;
  billNumber: string;
  vendorInvoiceNumber: string | null;
  vendorInvoiceDate: string | null;
  billDate: string;
  dueDate: string;
  vendorId: string;
  organizationId: string;
  unitId: string | null;
  subtotal: number;
  discountAmount: number;
  taxableAmount: number;
  cgstAmount: number;
  sgstAmount: number;
  igstAmount: number;
  cessAmount: number;
  tdsAmount: number;
  roundOff: number;
  totalAmount: number;
  balanceAmount: number;
  isReverseCharge: boolean;
  supplyType: string | null;
  vendorGstin: string | null;
  placeOfSupply: string | null;
  status: string;
  paymentStatus: string;
  isPosted: boolean;
  narration: string | null;
  referenceNumber: string | null;
  lines: BillLine[];
  createdAt: string;
  updatedAt: string | null;
}

interface Vendor {
  id: string;
  code: string;
  name: string;
  displayName: string | null;
  gstin: string | null;
  pan: string | null;
  addressLine1: string | null;
  city: string | null;
  stateCode: string | null;
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

  const loadBill = useCallback(async (billId: string) => {
    try {
      setLoading(true);
      const response = await purchaseBillsApi.get(billId);
      setBill(response.data);

      // Load vendor details
      if (response.data.vendorId) {
        const vendorResponse = await vendorsApi.get(response.data.vendorId);
        setVendor(vendorResponse.data);
      }
    } catch (error) {
      logger.error('Failed to load bill:', error);
      toast({
        title: 'Error',
        description: 'Failed to load purchase bill',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    if (id) {
      loadBill(id);
    }
  }, [id, loadBill]);

  const handleSubmit = async () => {
    if (!bill) return;
    try {
      await purchaseBillsApi.submit(bill.id);
      toast({
        title: 'Success',
        description: 'Purchase bill submitted for approval',
      });
      loadBill(bill.id);
    } catch (error) {
      showErrorToast(error, toast);
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
    } catch (error) {
      showErrorToast(error, toast);
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
    } catch (error) {
      showErrorToast(error, toast);
    } finally {
      setCancelDialogOpen(false);
      setCancelReason('');
    }
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
    return bill?.supplyType === 'INTRA_STATE';
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
      <div className="py-12 text-center">
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
      <PageHeader
        title={bill.billNumber}
        subtitle={`Created on ${formatDate(bill.createdAt)}`}
        breadcrumbs={[
          { label: 'Purchase Bills', to: '/admin/ap-ar/purchase-bills' },
          { label: bill.billNumber },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className={statusColors[bill.status]}>
              {statusLabels[bill.status]}
            </Badge>
            <Badge variant="secondary" className={paymentStatusColors[bill.paymentStatus]}>
              {paymentStatusLabels[bill.paymentStatus]}
            </Badge>
            {bill.status === 'DRAFT' && (
              <>
                <Button
                  variant="outline"
                  onClick={() => navigate(`/admin/ap-ar/purchase-bills/${bill.id}/edit`)}
                >
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
            {bill.status !== 'CANCELLED' && bill.paymentStatus === 'UNPAID' && (
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
        }
      />

      <div className="grid gap-6 md:grid-cols-3">
        {/* Vendor Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Vendor Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="font-medium">{vendor?.name}</div>
            {vendor?.displayName && vendor.displayName !== vendor.name && (
              <div className="text-slate-500">{vendor.displayName}</div>
            )}
            {vendor?.addressLine1 && (
              <div className="text-slate-600">
                {vendor.addressLine1}
                {vendor.city && `, ${vendor.city}`}
                {vendor.stateCode && ` - ${vendor.stateCode}`}
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
              <span className="font-medium">{bill.billNumber}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Vendor Invoice</span>
              <span className="font-mono">{bill.vendorInvoiceNumber || '-'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Vendor Invoice Date</span>
              <DateDisplay date={bill.vendorInvoiceDate} />
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Bill Date</span>
              <DateDisplay date={bill.billDate} />
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Due Date</span>
              <DateDisplay date={bill.dueDate} />
            </div>
            {bill.referenceNumber && (
              <div className="flex justify-between">
                <span className="text-slate-500">Reference</span>
                <span>{bill.referenceNumber}</span>
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
              <span>{bill.supplyType === 'INTRA_STATE' ? 'Intra State' : 'Inter State'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Place of Supply</span>
              <span>{bill.placeOfSupply || '-'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Vendor GSTIN</span>
              <span className="font-mono">{bill.vendorGstin || '-'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Reverse Charge</span>
              <span>{bill.isReverseCharge ? 'Yes' : 'No'}</span>
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
                  <TableCell>{line.lineNumber}</TableCell>
                  <TableCell>{line.description}</TableCell>
                  <TableCell className="font-mono text-sm">{line.hsnSacCode || '-'}</TableCell>
                  <TableCell className="text-right">{line.quantity}</TableCell>
                  <TableCell className="text-right">
                    <AmountDisplay amount={line.unitPrice} />
                  </TableCell>
                  <TableCell className="text-right">
                    {line.discountAmount > 0 ? <AmountDisplay amount={line.discountAmount} /> : '-'}
                  </TableCell>
                  <TableCell className="text-right">
                    <AmountDisplay amount={line.taxableAmount} />
                  </TableCell>
                  {isIntraState() ? (
                    <>
                      <TableCell className="text-right text-sm">
                        <AmountDisplay amount={line.cgstAmount} />
                        <span className="block text-slate-400">@{line.cgstRate}%</span>
                      </TableCell>
                      <TableCell className="text-right text-sm">
                        <AmountDisplay amount={line.sgstAmount} />
                        <span className="block text-slate-400">@{line.sgstRate}%</span>
                      </TableCell>
                    </>
                  ) : (
                    <TableCell className="text-right text-sm">
                      <AmountDisplay amount={line.igstAmount} />
                      <span className="block text-slate-400">@{line.igstRate}%</span>
                    </TableCell>
                  )}
                  <TableCell className="text-right font-medium">
                    <AmountDisplay amount={line.totalAmount} />
                  </TableCell>
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
              <p className="whitespace-pre-wrap text-sm text-slate-600">{bill.narration}</p>
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
              <AmountDisplay amount={bill.subtotal} />
            </div>
            {bill.discountAmount > 0 && (
              <div className="flex justify-between text-green-600">
                <span>Discount</span>
                <span>
                  - <AmountDisplay amount={bill.discountAmount} />
                </span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-slate-600">Taxable Amount</span>
              <AmountDisplay amount={bill.taxableAmount} />
            </div>
            {isIntraState() ? (
              <>
                <div className="flex justify-between">
                  <span className="text-slate-600">CGST</span>
                  <AmountDisplay amount={bill.cgstAmount} />
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">SGST</span>
                  <AmountDisplay amount={bill.sgstAmount} />
                </div>
              </>
            ) : (
              <div className="flex justify-between">
                <span className="text-slate-600">IGST</span>
                <AmountDisplay amount={bill.igstAmount} />
              </div>
            )}
            {bill.cessAmount > 0 && (
              <div className="flex justify-between">
                <span className="text-slate-600">Cess</span>
                <AmountDisplay amount={bill.cessAmount} />
              </div>
            )}
            {bill.tdsAmount > 0 && (
              <div className="flex justify-between text-orange-600">
                <span>TDS Deducted</span>
                <span>
                  - <AmountDisplay amount={bill.tdsAmount} />
                </span>
              </div>
            )}
            {bill.roundOff !== 0 && (
              <div className="flex justify-between">
                <span className="text-slate-600">Round Off</span>
                <AmountDisplay amount={bill.roundOff} />
              </div>
            )}
            <div className="flex justify-between border-t pt-2 font-bold">
              <span>Total Amount</span>
              <AmountDisplay amount={bill.totalAmount} />
            </div>
            <div className="flex justify-between text-blue-600">
              <span>Balance Due</span>
              <AmountDisplay amount={bill.balanceAmount} className="font-bold" />
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
              Are you sure you want to cancel bill &quot;{bill.billNumber}&quot;? Please provide a reason for
              cancellation.
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
