import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Loader2, Edit, Send, CheckCircle, XCircle, Printer, FileCheck } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
import { salesInvoicesApi, customersApi } from '@/services/api';

interface InvoiceLine {
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

interface SalesInvoice {
  id: string;
  invoice_number: string;
  invoice_date: string;
  due_date: string;
  customer_id: string;
  organization_id: string;
  unit_id: string | null;
  subtotal: number;
  discount_amount: number;
  taxable_amount: number;
  cgst_amount: number;
  sgst_amount: number;
  igst_amount: number;
  cess_amount: number;
  tcs_amount: number;
  round_off: number;
  total_amount: number;
  balance_amount: number;
  is_reverse_charge: boolean;
  supply_type: string | null;
  customer_gstin: string | null;
  place_of_supply: string | null;
  e_invoice_required: boolean;
  irn: string | null;
  e_invoice_status: string | null;
  status: string;
  receipt_status: string;
  is_posted: boolean;
  narration: string | null;
  reference_number: string | null;
  po_number: string | null;
  po_date: string | null;
  shipping_address: string | null;
  transporter_name: string | null;
  vehicle_number: string | null;
  eway_bill_number: string | null;
  eway_bill_date: string | null;
  lines: InvoiceLine[];
  created_at: string;
  updated_at: string | null;
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

  useEffect(() => {
    if (id) {
      loadInvoice(id);
    }
  }, [id]);

  const loadInvoice = async (invoiceId: string) => {
    try {
      setLoading(true);
      const response = await salesInvoicesApi.get(invoiceId);
      setInvoice(response.data);

      // Load customer details
      if (response.data.customer_id) {
        const customerResponse = await customersApi.get(response.data.customer_id);
        setCustomer(customerResponse.data);
      }
    } catch (error) {
      console.error('Failed to load invoice:', error);
      toast({
        title: 'Error',
        description: 'Failed to load sales invoice',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!invoice) return;
    try {
      await salesInvoicesApi.submit(invoice.id);
      toast({
        title: 'Success',
        description: 'Sales invoice submitted for approval',
      });
      loadInvoice(invoice.id);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to submit sales invoice',
        variant: 'destructive',
      });
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
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to approve sales invoice',
        variant: 'destructive',
      });
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
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to cancel sales invoice',
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
    return invoice?.supply_type === 'INTRA_STATE';
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
      <div className="text-center py-12">
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/admin/ap-ar/sales-invoices')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-900">{invoice.invoice_number}</h1>
              <Badge variant="secondary" className={statusColors[invoice.status]}>
                {statusLabels[invoice.status]}
              </Badge>
              <Badge variant="secondary" className={receiptStatusColors[invoice.receipt_status]}>
                {receiptStatusLabels[invoice.receipt_status]}
              </Badge>
              {invoice.e_invoice_status && (
                <Badge variant="secondary" className={eInvoiceStatusColors[invoice.e_invoice_status]}>
                  E-Inv: {eInvoiceStatusLabels[invoice.e_invoice_status]}
                </Badge>
              )}
            </div>
            <p className="text-sm text-slate-500">
              Created on {formatDate(invoice.created_at)}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {invoice.status === 'DRAFT' && (
            <>
              <Button variant="outline" onClick={() => navigate(`/admin/ap-ar/sales-invoices/${invoice.id}/edit`)}>
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
          {invoice.e_invoice_required && invoice.e_invoice_status === 'PENDING' && invoice.status === 'APPROVED' && (
            <Button variant="outline">
              <FileCheck className="mr-2 h-4 w-4" />
              Generate E-Invoice
            </Button>
          )}
          {invoice.status !== 'CANCELLED' && invoice.receipt_status === 'UNRECEIVED' && (
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
              <span className="font-medium">{invoice.invoice_number}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Invoice Date</span>
              <span>{formatDate(invoice.invoice_date)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Due Date</span>
              <span>{formatDate(invoice.due_date)}</span>
            </div>
            {invoice.reference_number && (
              <div className="flex justify-between">
                <span className="text-slate-500">Reference</span>
                <span>{invoice.reference_number}</span>
              </div>
            )}
            {invoice.po_number && (
              <div className="flex justify-between">
                <span className="text-slate-500">PO Number</span>
                <span>{invoice.po_number}</span>
              </div>
            )}
            {invoice.po_date && (
              <div className="flex justify-between">
                <span className="text-slate-500">PO Date</span>
                <span>{formatDate(invoice.po_date)}</span>
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
              <span>{invoice.supply_type === 'INTRA_STATE' ? 'Intra State' : 'Inter State'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Place of Supply</span>
              <span>{invoice.place_of_supply || '-'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Customer GSTIN</span>
              <span className="font-mono">{invoice.customer_gstin || '-'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Reverse Charge</span>
              <span>{invoice.is_reverse_charge ? 'Yes' : 'No'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">E-Invoice Required</span>
              <span>{invoice.e_invoice_required ? 'Yes' : 'No'}</span>
            </div>
            {invoice.irn && (
              <div className="flex justify-between">
                <span className="text-slate-500">IRN</span>
                <span className="font-mono text-xs">{invoice.irn}</span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Shipping Details */}
      {(invoice.shipping_address || invoice.transporter_name || invoice.eway_bill_number) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Shipping & Transport</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2 text-sm">
            {invoice.shipping_address && (
              <div>
                <span className="text-slate-500 block mb-1">Shipping Address</span>
                <span className="whitespace-pre-wrap">{invoice.shipping_address}</span>
              </div>
            )}
            <div className="space-y-2">
              {invoice.transporter_name && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Transporter</span>
                  <span>{invoice.transporter_name}</span>
                </div>
              )}
              {invoice.vehicle_number && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Vehicle Number</span>
                  <span className="font-mono">{invoice.vehicle_number}</span>
                </div>
              )}
              {invoice.eway_bill_number && (
                <div className="flex justify-between">
                  <span className="text-slate-500">E-Way Bill</span>
                  <span className="font-mono">{invoice.eway_bill_number}</span>
                </div>
              )}
              {invoice.eway_bill_date && (
                <div className="flex justify-between">
                  <span className="text-slate-500">E-Way Bill Date</span>
                  <span>{formatDate(invoice.eway_bill_date)}</span>
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
        {invoice.narration && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Narration</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-600 whitespace-pre-wrap">{invoice.narration}</p>
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
              <span>{formatCurrency(invoice.subtotal)}</span>
            </div>
            {invoice.discount_amount > 0 && (
              <div className="flex justify-between text-green-600">
                <span>Discount</span>
                <span>- {formatCurrency(invoice.discount_amount)}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-slate-600">Taxable Amount</span>
              <span>{formatCurrency(invoice.taxable_amount)}</span>
            </div>
            {isIntraState() ? (
              <>
                <div className="flex justify-between">
                  <span className="text-slate-600">CGST</span>
                  <span>{formatCurrency(invoice.cgst_amount)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">SGST</span>
                  <span>{formatCurrency(invoice.sgst_amount)}</span>
                </div>
              </>
            ) : (
              <div className="flex justify-between">
                <span className="text-slate-600">IGST</span>
                <span>{formatCurrency(invoice.igst_amount)}</span>
              </div>
            )}
            {invoice.cess_amount > 0 && (
              <div className="flex justify-between">
                <span className="text-slate-600">Cess</span>
                <span>{formatCurrency(invoice.cess_amount)}</span>
              </div>
            )}
            {invoice.tcs_amount > 0 && (
              <div className="flex justify-between text-blue-600">
                <span>TCS</span>
                <span>+ {formatCurrency(invoice.tcs_amount)}</span>
              </div>
            )}
            {invoice.round_off !== 0 && (
              <div className="flex justify-between">
                <span className="text-slate-600">Round Off</span>
                <span>{formatCurrency(invoice.round_off)}</span>
              </div>
            )}
            <div className="border-t pt-2 flex justify-between font-bold">
              <span>Total Amount</span>
              <span>{formatCurrency(invoice.total_amount)}</span>
            </div>
            <div className="flex justify-between text-blue-600">
              <span>Balance Receivable</span>
              <span className="font-bold">{formatCurrency(invoice.balance_amount)}</span>
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
              Are you sure you want to cancel invoice "{invoice.invoice_number}"?
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
              Cancel Invoice
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
