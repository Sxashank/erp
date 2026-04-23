import { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
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
  ShoppingCart,
  Building2,
  Calendar,
  Clock,
  CheckCircle,
  XCircle,
  Truck,
  Download,
  Printer,
  Package,
  FileText,
  History,
} from 'lucide-react';

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

// Mock PO detail data
const poData = {
  id: '1',
  poNumber: 'PO2025010001',
  vendor: {
    code: 'V001',
    name: 'ABC Suppliers Ltd',
    gst: '27AABCU9603R1ZM',
    address: '123, Industrial Area, Mumbai - 400001',
    contactPerson: 'Rajesh Kumar',
    phone: '+91 9876543210',
    email: 'rajesh@abcsuppliers.com',
  },
  rfqNumber: 'RFQ2024120015',
  poDate: '2025-01-10',
  deliveryDate: '2025-01-25',
  deliveryLocation: 'Head Office - Building A, Ground Floor',
  paymentTerms: 'Net 30 Days',
  status: 'APPROVED',
  grnStatus: 'PARTIAL',
  createdBy: 'Procurement Team',
  createdAt: '2025-01-10 10:30 AM',
  approvedBy: 'Finance Head',
  approvedAt: '2025-01-11 04:30 PM',
  remarks: 'Urgent requirement for new office setup.',
  lineItems: [
    { id: 1, description: 'Ergonomic Office Chair', quantity: 50, uom: 'PCS', unitPrice: 1500, taxPercent: 18, total: 88500, receivedQty: 30 },
    { id: 2, description: 'Standing Desk - Electric', quantity: 25, uom: 'PCS', unitPrice: 3000, taxPercent: 18, total: 88500, receivedQty: 20 },
    { id: 3, description: 'Filing Cabinet - 4 Drawer', quantity: 30, uom: 'PCS', unitPrice: 2500, taxPercent: 18, total: 88500, receivedQty: 30 },
    { id: 4, description: 'Conference Table', quantity: 5, uom: 'PCS', unitPrice: 15000, taxPercent: 18, total: 88500, receivedQty: 0 },
    { id: 5, description: 'Visitor Chairs', quantity: 20, uom: 'PCS', unitPrice: 800, taxPercent: 18, total: 18880, receivedQty: 20 },
  ],
  grnHistory: [
    { grnNumber: 'GRN2025010001', date: '2025-01-15', items: 3, value: 85000, status: 'APPROVED' },
    { grnNumber: 'GRN2025010003', date: '2025-01-18', items: 2, value: 60000, status: 'APPROVED' },
  ],
  activityLog: [
    { action: 'PO Created', by: 'Procurement Team', at: '2025-01-10 10:30 AM', details: 'Purchase order created from RFQ2024120015' },
    { action: 'Submitted for Approval', by: 'Procurement Team', at: '2025-01-10 10:35 AM', details: 'Submitted to Finance Head' },
    { action: 'Approved', by: 'Finance Head', at: '2025-01-11 04:30 PM', details: 'Approved as per budget allocation.' },
    { action: 'GRN Created', by: 'Warehouse Team', at: '2025-01-15 02:00 PM', details: 'GRN2025010001 - Partial receipt' },
    { action: 'GRN Created', by: 'Warehouse Team', at: '2025-01-18 11:30 AM', details: 'GRN2025010003 - Partial receipt' },
  ],
};

export default function PODetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('details');

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'DRAFT':
        return <Badge variant="outline">Draft</Badge>;
      case 'PENDING_APPROVAL':
        return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" />Pending Approval</Badge>;
      case 'APPROVED':
        return <Badge variant="default" className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Approved</Badge>;
      case 'COMPLETED':
        return <Badge variant="default" className="bg-blue-100 text-blue-800"><Truck className="h-3 w-3 mr-1" />Completed</Badge>;
      case 'CANCELLED':
        return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Cancelled</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getGRNStatusBadge = (status: string) => {
    switch (status) {
      case 'PENDING':
        return <Badge variant="outline">Pending</Badge>;
      case 'PARTIAL':
        return <Badge variant="secondary">Partial</Badge>;
      case 'COMPLETE':
        return <Badge variant="default" className="bg-green-100 text-green-800">Complete</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  // Calculate totals
  const subtotal = poData.lineItems.reduce((sum, item) => sum + (item.quantity * item.unitPrice), 0);
  const totalTax = poData.lineItems.reduce((sum, item) => {
    const itemTotal = item.quantity * item.unitPrice;
    return sum + (itemTotal * item.taxPercent / 100);
  }, 0);
  const grandTotal = subtotal + totalTax;

  // Calculate receipt progress
  const totalOrderedQty = poData.lineItems.reduce((sum, item) => sum + item.quantity, 0);
  const totalReceivedQty = poData.lineItems.reduce((sum, item) => sum + item.receivedQty, 0);
  const receiptProgress = (totalReceivedQty / totalOrderedQty) * 100;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title={poData.poNumber}
        subtitle="Purchase Order Details"
        breadcrumbs={[
          { label: 'Purchase Orders', to: '/admin/procurement/po' },
          { label: poData.poNumber },
        ]}
        actions={
          <div className="flex gap-2">
            {getStatusBadge(poData.status)}
            {getGRNStatusBadge(poData.grnStatus)}
            <Button variant="outline">
              <Printer className="h-4 w-4 mr-2" />
              Print
            </Button>
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Download PDF
            </Button>
            {poData.status === 'APPROVED' && poData.grnStatus !== 'COMPLETE' && (
              <Link to={`/admin/procurement/grn/new?po=${poData.id}`}>
                <Button>
                  <Package className="h-4 w-4 mr-2" />
                  Create GRN
                </Button>
              </Link>
            )}
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">PO Value</div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(grandTotal)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Line Items</div>
            <div className="text-2xl font-bold mt-1">{poData.lineItems.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Receipt Progress</div>
            <div className="text-2xl font-bold mt-1">{receiptProgress.toFixed(0)}%</div>
            <Progress value={receiptProgress} className="mt-2" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Delivery Date</div>
            <div className="text-2xl font-bold mt-1">{poData.deliveryDate}</div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="items">Items ({poData.lineItems.length})</TabsTrigger>
          <TabsTrigger value="grn">GRN History ({poData.grnHistory.length})</TabsTrigger>
          <TabsTrigger value="activity">Activity Log</TabsTrigger>
        </TabsList>

        <TabsContent value="details" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Vendor Information */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Building2 className="h-5 w-5" />
                  Vendor Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-muted-foreground">Vendor Code</label>
                    <p className="font-medium">{poData.vendor.code}</p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Vendor Name</label>
                    <p className="font-medium">{poData.vendor.name}</p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">GSTIN</label>
                    <p className="font-mono">{poData.vendor.gst}</p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Contact Person</label>
                    <p className="font-medium">{poData.vendor.contactPerson}</p>
                  </div>
                </div>
                <div>
                  <label className="text-sm text-muted-foreground">Address</label>
                  <p>{poData.vendor.address}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-muted-foreground">Phone</label>
                    <p>{poData.vendor.phone}</p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Email</label>
                    <p>{poData.vendor.email}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* PO Information */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  PO Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-muted-foreground">PO Date</label>
                    <p className="font-medium">{poData.poDate}</p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">RFQ Reference</label>
                    <p>
                      {poData.rfqNumber ? (
                        <Link to={`/admin/procurement/rfq/${poData.rfqNumber}`} className="text-primary hover:underline">
                          {poData.rfqNumber}
                        </Link>
                      ) : (
                        'Direct PO'
                      )}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Delivery Date</label>
                    <p className="font-medium">{poData.deliveryDate}</p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Payment Terms</label>
                    <p className="font-medium">{poData.paymentTerms}</p>
                  </div>
                </div>
                <div>
                  <label className="text-sm text-muted-foreground">Delivery Location</label>
                  <p>{poData.deliveryLocation}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-muted-foreground">Created By</label>
                    <p>{poData.createdBy} on {poData.createdAt}</p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Approved By</label>
                    <p>{poData.approvedBy} on {poData.approvedAt}</p>
                  </div>
                </div>
                {poData.remarks && (
                  <div>
                    <label className="text-sm text-muted-foreground">Remarks</label>
                    <p>{poData.remarks}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="items">
          <Card>
            <CardHeader>
              <CardTitle>Line Items</CardTitle>
              <CardDescription>Items ordered in this purchase order</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[60px]">#</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-center">Qty</TableHead>
                    <TableHead className="text-center">UOM</TableHead>
                    <TableHead className="text-right">Unit Price</TableHead>
                    <TableHead className="text-center">Tax %</TableHead>
                    <TableHead className="text-center">Received</TableHead>
                    <TableHead className="text-right">Total</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {poData.lineItems.map((item, index) => {
                    const itemSubtotal = item.quantity * item.unitPrice;
                    const itemTax = itemSubtotal * (item.taxPercent / 100);
                    const itemTotal = itemSubtotal + itemTax;
                    const receiptPercent = (item.receivedQty / item.quantity) * 100;
                    return (
                      <TableRow key={item.id}>
                        <TableCell className="font-medium">{index + 1}</TableCell>
                        <TableCell className="font-medium">{item.description}</TableCell>
                        <TableCell className="text-center">{item.quantity}</TableCell>
                        <TableCell className="text-center">{item.uom}</TableCell>
                        <TableCell className="text-right">{formatCurrency(item.unitPrice)}</TableCell>
                        <TableCell className="text-center">{item.taxPercent}%</TableCell>
                        <TableCell className="text-center">
                          <span className={receiptPercent === 100 ? 'text-green-600' : receiptPercent > 0 ? 'text-yellow-600' : ''}>
                            {item.receivedQty}/{item.quantity}
                          </span>
                        </TableCell>
                        <TableCell className="text-right font-medium">{formatCurrency(itemTotal)}</TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>

              {/* Totals */}
              <div className="mt-6 flex justify-end">
                <div className="w-72 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Subtotal:</span>
                    <span>{formatCurrency(subtotal)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Total Tax:</span>
                    <span>{formatCurrency(totalTax)}</span>
                  </div>
                  <div className="flex justify-between text-lg font-bold border-t pt-2">
                    <span>Grand Total:</span>
                    <span>{formatCurrency(grandTotal)}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="grn">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                GRN History
              </CardTitle>
              <CardDescription>Goods receipts recorded against this PO</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>GRN Number</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-center">Items Received</TableHead>
                    <TableHead className="text-right">Value</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {poData.grnHistory.map((grn) => (
                    <TableRow key={grn.grnNumber}>
                      <TableCell className="font-mono">{grn.grnNumber}</TableCell>
                      <TableCell>{grn.date}</TableCell>
                      <TableCell className="text-center">{grn.items}</TableCell>
                      <TableCell className="text-right">{formatCurrency(grn.value)}</TableCell>
                      <TableCell>
                        <Badge variant="default" className="bg-green-100 text-green-800">
                          {grn.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Link to={`/admin/procurement/grn/${grn.grnNumber}`}>
                          <Button variant="ghost" size="sm">View</Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {poData.grnHistory.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  No goods receipts recorded yet.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="activity">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5" />
                Activity Log
              </CardTitle>
              <CardDescription>Complete history of actions on this PO</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {poData.activityLog.map((activity, index) => (
                  <div key={index} className="flex gap-4 pb-4 border-b last:border-0">
                    <div className="w-2 h-2 mt-2 rounded-full bg-primary"></div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <p className="font-medium">{activity.action}</p>
                        <span className="text-sm text-muted-foreground">{activity.at}</span>
                      </div>
                      <p className="text-sm text-muted-foreground">by {activity.by}</p>
                      {activity.details && (
                        <p className="text-sm mt-1">{activity.details}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
