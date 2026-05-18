import { Loader2, Edit, Send, CheckCircle, XCircle, Printer, FileCheck } from 'lucide-react';
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
import { salesInvoicesApi, customersApi } from '@/services/api';

import { logger } from "@/lib/logger";
interface InvoiceLine {
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

interface SalesInvoice {
  id: string;
  invoiceNumber: string;
  invoiceDate: string;
  dueDate: string;
  customerId: string;
  organizationId: string;
  unitId: string | null;
  subtotal: number;
  discountAmount: number;
  taxableAmount: number;
  cgstAmount: number;
  sgstAmount: number;
  igstAmount: number;
  cessAmount: number;
  tcsAmount: number;
  roundOff: number;
  totalAmount: number;
  balanceAmount: number;
  isReverseCharge: boolean;
  supplyType: string | null;
  customerGstin: string | null;
  placeOfSupply: string | null;
  eInvoiceRequired: boolean;
  irn: string | null;
  irnDate: string | null;
  ackNumber: string | null;
  ackDate: string | null;
  eInvoiceStatus: string | null;
  status: string;
  receiptStatus: string;
  isPosted: boolean;
  narration: string | null;
  referenceNumber: string | null;
  poNumber: string | null;
  poDate: string | null;
  shippingAddress: string | null;
  transporterName: string | null;
  vehicleNumber: string | null;
  ewayBillNumber: string | null;
  ewayBillDate: string | null;
  lines: InvoiceLine[];
  createdAt: string;
  updatedAt: string | null;
}

interface Customer {
  id: string;
  code: string;
  name: string;
  display_name: string | null;
  gstin: string | null;
  pan: string | null;
  billing_address_line1: string | null;
  billing_city: string | null;
  billing_state_code: string | null;
  billing_pincode: string | null;
}

const statusLabels: Record<string, string> = {
  DRAFT: 'Draft',
  SUBMITTED: 'Submitted',
  APPROVED: 'Approved',
  PARTIALLY_RECEIVED: 'Partially Received',
  RECEIVED: 'Received',
  CANCELLED: 'Cancelled',
};

const statusColors: Record<string, string> = {
  DRAFT: 'bg-slate-100 text-slate-800',
  SUBMITTED: 'bg-yellow-100 text-yellow-800',
  APPROVED: 'bg-blue-100 text-blue-800',
  PARTIALLY_RECEIVED: 'bg-orange-100 text-orange-800',
  RECEIVED: 'bg-green-100 text-green-800',
  CANCELLED: 'bg-red-100 text-red-800',
};

const receiptStatusLabels: Record<string, string> = {
  UNRECEIVED: 'Unreceived',
  PARTIALLY_RECEIVED: 'Partially Received',
  RECEIVED: 'Received',
};

const receiptStatusColors: Record<string, string> = {
  UNRECEIVED: 'bg-red-100 text-red-800',
  PARTIALLY_RECEIVED: 'bg-orange-100 text-orange-800',
  RECEIVED: 'bg-green-100 text-green-800',
};

const eInvoiceStatusLabels: Record<string, string> = {
  NOT_APPLICABLE: 'N/A',
  PENDING: 'Pending',
  GENERATED: 'Generated',
  CANCELLED: 'Cancelled',
};

const eInvoiceStatusColors: Record<string, string> = {
  NOT_APPLICABLE: 'bg-gray-100 text-gray-600',
  PENDING: 'bg-yellow-100 text-yellow-800',
  GENERATED: 'bg-green-100 text-green-800',
  CANCELLED: 'bg-red-100 text-red-800',
};

export function SalesInvoiceView() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [invoice, setInvoice] = useState<SalesInvoice | null>(null);
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState('');

  const loadInvoice = useCallback(async (invoiceId: string) => {
    try {
      setLoading(true);
      const response = await salesInvoicesApi.get(invoiceId);
      setInvoice(response.data);

      // Load customer details
      if (response.data.customerId) {
        const customerResponse = await customersApi.get(response.data.customerId);
        setCustomer(customerResponse.data);
      }
    } catch (error) {
      logger.error('Failed to load invoice:', error);
      toast({
        title: 'Error',
        description: 'Failed to load sales invoice',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    if (id) {
      loadInvoice(id);
    }
  }, [id, loadInvoice]);

  const handleSubmit = async () => {
    if (!invoice) return;
    try {
      await salesInvoicesApi.submit(invoice.id);
      toast({
        title: 'Success',
        description: 'Sales invoice submitted for approval',
      });
      loadInvoice(invoice.id);
    } catch (error) {
      showErrorToast(error, toast);
    }
  };

  const handleApprove = async () => {
    if (!invoice) return;
    try {
      await salesInvoicesApi.approve(invoice.id);
      toast({
        title: 'Success',
        description: 'Sales invoice approved successfully',
      });
      loadInvoice(invoice.id);
    } catch (error) {
      showErrorToast(error, toast);
    }
  };

  const handleCancel = async () => {
    if (!invoice || !cancelReason) return;
    try {
      await salesInvoicesApi.cancel(invoice.id, cancelReason);
      toast({
        title: 'Success',
        description: 'Sales invoice cancelled successfully',
      });
      loadInvoice(invoice.id);
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
    return invoice?.supplyType === 'INTRA_STATE';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  if (!invoice) {
    return (
      <div className="py-12 text-center">
        <p className="text-slate-500">Sales invoice not found</p>
        <Button
          variant="outline"
          onClick={() => navigate('/admin/ap-ar/sales-invoices')}
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
        title={invoice.invoiceNumber}
        subtitle={`Created on ${formatDate(invoice.createdAt)}`}
        breadcrumbs={[
          { label: 'Sales Invoices', to: '/admin/ap-ar/sales-invoices' },
          { label: invoice.invoiceNumber },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className={statusColors[invoice.status]}>
              {statusLabels[invoice.status]}
            </Badge>
            <Badge variant="secondary" className={receiptStatusColors[invoice.receiptStatus]}>
              {receiptStatusLabels[invoice.receiptStatus]}
            </Badge>
            {invoice.eInvoiceStatus && (
              <Badge variant="secondary" className={eInvoiceStatusColors[invoice.eInvoiceStatus]}>
                E-Inv: {eInvoiceStatusLabels[invoice.eInvoiceStatus]}
              </Badge>
            )}
            {invoice.status === 'DRAFT' && (
              <>
                <Button
                  variant="outline"
                  onClick={() => navigate(`/admin/ap-ar/sales-invoices/${invoice.id}/edit`)}
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
            {invoice.status === 'SUBMITTED' && (
              <Button onClick={handleApprove}>
                <CheckCircle className="mr-2 h-4 w-4" />
                Approve
              </Button>
            )}
            {invoice.eInvoiceRequired &&
              invoice.eInvoiceStatus === 'PENDING' &&
              invoice.status === 'APPROVED' && (
                <Button variant="outline">
                  <FileCheck className="mr-2 h-4 w-4" />
                  Generate E-Invoice
                </Button>
              )}
            {invoice.status !== 'CANCELLED' && invoice.receiptStatus === 'UNRECEIVED' && (
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
        {/* Customer Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Customer Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="font-medium">{customer?.name}</div>
            {customer?.display_name && customer.display_name !== customer.name && (
              <div className="text-slate-500">{customer.display_name}</div>
            )}
            {customer?.billing_address_line1 && (
              <div className="text-slate-600">
                {customer.billing_address_line1}
                {customer.billing_city && `, ${customer.billing_city}`}
                {customer.billing_state_code && ` - ${customer.billing_state_code}`}
                {customer.billing_pincode && `, ${customer.billing_pincode}`}
              </div>
            )}
            {customer?.gstin && (
              <div>
                <span className="text-slate-500">GSTIN: </span>
                <span className="font-mono">{customer.gstin}</span>
              </div>
            )}
            {customer?.pan && (
              <div>
                <span className="text-slate-500">PAN: </span>
                <span className="font-mono">{customer.pan}</span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Invoice Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Invoice Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-500">Invoice Number</span>
              <span className="font-medium">{invoice.invoiceNumber}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Invoice Date</span>
              <DateDisplay date={invoice.invoiceDate} />
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Due Date</span>
              <DateDisplay date={invoice.dueDate} />
            </div>
            {invoice.referenceNumber && (
              <div className="flex justify-between">
                <span className="text-slate-500">Reference</span>
                <span>{invoice.referenceNumber}</span>
              </div>
            )}
            {invoice.poNumber && (
              <div className="flex justify-between">
                <span className="text-slate-500">PO Number</span>
                <span>{invoice.poNumber}</span>
              </div>
            )}
            {invoice.poDate && (
              <div className="flex justify-between">
                <span className="text-slate-500">PO Date</span>
                <DateDisplay date={invoice.poDate} />
              </div>
            )}
          </CardContent>
        </Card>

        {/* GST & E-Invoice Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">GST & E-Invoice</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-500">Supply Type</span>
              <span>{invoice.supplyType === 'INTRA_STATE' ? 'Intra State' : 'Inter State'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Place of Supply</span>
              <span>{invoice.placeOfSupply || '-'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Customer GSTIN</span>
              <span className="font-mono">{invoice.customerGstin || '-'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Reverse Charge</span>
              <span>{invoice.isReverseCharge ? 'Yes' : 'No'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">E-Invoice Required</span>
              <span>{invoice.eInvoiceRequired ? 'Yes' : 'No'}</span>
            </div>
            {invoice.irn && (
              <div className="flex justify-between">
                <span className="text-slate-500">IRN</span>
                <span className="font-mono text-xs">{invoice.irn}</span>
              </div>
            )}
            {invoice.irnDate && (
              <div className="flex justify-between">
                <span className="text-slate-500">IRN Date</span>
                <DateDisplay date={invoice.irnDate} />
              </div>
            )}
            {invoice.ackNumber && (
              <div className="flex justify-between">
                <span className="text-slate-500">Ack Number</span>
                <span className="font-mono text-xs">{invoice.ackNumber}</span>
              </div>
            )}
            {invoice.ackDate && (
              <div className="flex justify-between">
                <span className="text-slate-500">Ack Date</span>
                <DateDisplay date={invoice.ackDate} />
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Shipping Details */}
      {(invoice.shippingAddress || invoice.transporterName || invoice.ewayBillNumber) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Shipping & Transport</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 text-sm md:grid-cols-2">
            {invoice.shippingAddress && (
              <div>
                <span className="mb-1 block text-slate-500">Shipping Address</span>
                <span className="whitespace-pre-wrap">{invoice.shippingAddress}</span>
              </div>
            )}
            <div className="space-y-2">
              {invoice.transporterName && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Transporter</span>
                  <span>{invoice.transporterName}</span>
                </div>
              )}
              {invoice.vehicleNumber && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Vehicle Number</span>
                  <span className="font-mono">{invoice.vehicleNumber}</span>
                </div>
              )}
              {invoice.ewayBillNumber && (
                <div className="flex justify-between">
                  <span className="text-slate-500">E-Way Bill</span>
                  <span className="font-mono">{invoice.ewayBillNumber}</span>
                </div>
              )}
              {invoice.ewayBillDate && (
                <div className="flex justify-between">
                  <span className="text-slate-500">E-Way Bill Date</span>
                  <DateDisplay date={invoice.ewayBillDate} />
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

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
              {invoice.lines.map((line) => (
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
        {invoice.narration && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Narration</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="whitespace-pre-wrap text-sm text-slate-600">{invoice.narration}</p>
            </CardContent>
          </Card>
        )}

        <Card className={invoice.narration ? '' : 'md:col-start-2'}>
          <CardHeader>
            <CardTitle className="text-base">Invoice Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-600">Subtotal</span>
              <AmountDisplay amount={invoice.subtotal} />
            </div>
            {invoice.discountAmount > 0 && (
              <div className="flex justify-between text-green-600">
                <span>Discount</span>
                <span>
                  - <AmountDisplay amount={invoice.discountAmount} />
                </span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-slate-600">Taxable Amount</span>
              <AmountDisplay amount={invoice.taxableAmount} />
            </div>
            {isIntraState() ? (
              <>
                <div className="flex justify-between">
                  <span className="text-slate-600">CGST</span>
                  <AmountDisplay amount={invoice.cgstAmount} />
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">SGST</span>
                  <AmountDisplay amount={invoice.sgstAmount} />
                </div>
              </>
            ) : (
              <div className="flex justify-between">
                <span className="text-slate-600">IGST</span>
                <AmountDisplay amount={invoice.igstAmount} />
              </div>
            )}
            {invoice.cessAmount > 0 && (
              <div className="flex justify-between">
                <span className="text-slate-600">Cess</span>
                <AmountDisplay amount={invoice.cessAmount} />
              </div>
            )}
            {invoice.tcsAmount > 0 && (
              <div className="flex justify-between text-blue-600">
                <span>TCS</span>
                <span>
                  + <AmountDisplay amount={invoice.tcsAmount} />
                </span>
              </div>
            )}
            {invoice.roundOff !== 0 && (
              <div className="flex justify-between">
                <span className="text-slate-600">Round Off</span>
                <AmountDisplay amount={invoice.roundOff} />
              </div>
            )}
            <div className="flex justify-between border-t pt-2 font-bold">
              <span>Total Amount</span>
              <AmountDisplay amount={invoice.totalAmount} />
            </div>
            <div className="flex justify-between text-blue-600">
              <span>Balance Receivable</span>
              <AmountDisplay amount={invoice.balanceAmount} className="font-bold" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Cancel Dialog */}
      <AlertDialog open={cancelDialogOpen} onOpenChange={setCancelDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancel Sales Invoice</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to cancel invoice &quot;{invoice.invoiceNumber}&quot;? Please provide a
              reason for cancellation.
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
              Cancel Invoice
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
