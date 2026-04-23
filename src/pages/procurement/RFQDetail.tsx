import { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
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
  FileText,
  Building2,
  Calendar,
  Clock,
  CheckCircle,
  XCircle,
  Send,
  Download,
  BarChart3,
  Users,
  Package,
} from 'lucide-react';

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

// Mock RFQ detail data
const rfqData = {
  id: '1',
  rfqNumber: 'RFQ2025010001',
  title: 'Office Furniture - Q1 2025',
  category: 'Furniture',
  description: 'Procurement of office furniture including ergonomic chairs, standing desks, and storage cabinets for the new wing.',
  estimatedValue: 500000,
  startDate: '2025-01-10',
  endDate: '2025-01-20',
  deliveryDate: '2025-02-15',
  deliveryLocation: 'Head Office - Building B, Floor 3',
  paymentTerms: 'Net 30 Days',
  status: 'OPEN',
  createdBy: 'Admin',
  createdAt: '2025-01-08 10:30 AM',
  lineItems: [
    { id: 1, description: 'Ergonomic Office Chair', quantity: 50, uom: 'PCS', specifications: 'Lumbar support, adjustable height, mesh back' },
    { id: 2, description: 'Standing Desk - Electric', quantity: 25, uom: 'PCS', specifications: 'Height adjustable 70-120cm, memory presets' },
    { id: 3, description: 'Filing Cabinet - 4 Drawer', quantity: 30, uom: 'PCS', specifications: 'Steel construction, central locking' },
    { id: 4, description: 'Conference Table - 10 Seater', quantity: 5, uom: 'PCS', specifications: 'Modular design, cable management' },
  ],
  vendors: [
    { id: 'V001', name: 'ABC Suppliers Ltd', email: 'sales@abcsuppliers.com', phone: '+91 9876543210', status: 'INVITED', responseDate: null },
    { id: 'V005', name: 'Furniture Hub', email: 'info@furniturehub.com', phone: '+91 9988776655', status: 'QUOTED', responseDate: '2025-01-12' },
    { id: 'V007', name: 'Office Solutions', email: 'contact@officesol.com', phone: '+91 8899001122', status: 'QUOTED', responseDate: '2025-01-14' },
    { id: 'V008', name: 'Premium Furnishings', email: 'sales@premfurn.com', phone: '+91 7766554433', status: 'QUOTED', responseDate: '2025-01-15' },
    { id: 'V010', name: 'Metro Furniture', email: 'info@metrofurn.com', phone: '+91 6655443322', status: 'DECLINED', responseDate: '2025-01-11' },
  ],
  quotations: [
    {
      vendorId: 'V005',
      vendorName: 'Furniture Hub',
      totalAmount: 485000,
      deliveryDays: 20,
      warranty: '2 years',
      submittedAt: '2025-01-12 02:30 PM',
      items: [
        { itemId: 1, unitPrice: 4500, amount: 225000 },
        { itemId: 2, unitPrice: 6500, amount: 162500 },
        { itemId: 3, unitPrice: 2800, amount: 84000 },
        { itemId: 4, unitPrice: 2700, amount: 13500 },
      ],
    },
    {
      vendorId: 'V007',
      vendorName: 'Office Solutions',
      totalAmount: 520000,
      deliveryDays: 15,
      warranty: '3 years',
      submittedAt: '2025-01-14 11:45 AM',
      items: [
        { itemId: 1, unitPrice: 4800, amount: 240000 },
        { itemId: 2, unitPrice: 7000, amount: 175000 },
        { itemId: 3, unitPrice: 3000, amount: 90000 },
        { itemId: 4, unitPrice: 3000, amount: 15000 },
      ],
    },
    {
      vendorId: 'V008',
      vendorName: 'Premium Furnishings',
      totalAmount: 545000,
      deliveryDays: 25,
      warranty: '5 years',
      submittedAt: '2025-01-15 09:15 AM',
      items: [
        { itemId: 1, unitPrice: 5000, amount: 250000 },
        { itemId: 2, unitPrice: 7500, amount: 187500 },
        { itemId: 3, unitPrice: 3200, amount: 96000 },
        { itemId: 4, unitPrice: 2300, amount: 11500 },
      ],
    },
  ],
};

export default function RFQDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('details');

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'OPEN':
        return <Badge variant="default" className="bg-green-100 text-green-800"><Send className="h-3 w-3 mr-1" />Open</Badge>;
      case 'CLOSED':
        return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" />Closed</Badge>;
      case 'AWARDED':
        return <Badge variant="default" className="bg-blue-100 text-blue-800"><CheckCircle className="h-3 w-3 mr-1" />Awarded</Badge>;
      case 'CANCELLED':
        return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Cancelled</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getVendorStatusBadge = (status: string) => {
    switch (status) {
      case 'INVITED':
        return <Badge variant="outline">Invited</Badge>;
      case 'QUOTED':
        return <Badge variant="default" className="bg-green-100 text-green-800">Quoted</Badge>;
      case 'DECLINED':
        return <Badge variant="destructive">Declined</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const quotedCount = rfqData.vendors.filter(v => v.status === 'QUOTED').length;
  const invitedCount = rfqData.vendors.length;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title={rfqData.rfqNumber}
        subtitle={rfqData.title}
        breadcrumbs={[
          { label: 'RFQ', to: '/admin/procurement/rfq' },
          { label: rfqData.rfqNumber },
        ]}
        actions={
          <div className="flex gap-2">
            {getStatusBadge(rfqData.status)}
            {rfqData.status === 'OPEN' && (
              <>
                <Button variant="outline">
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </Button>
                <Link to={`/admin/procurement/rfq/${id}/compare`}>
                  <Button>
                    <BarChart3 className="h-4 w-4 mr-2" />
                    Compare Quotes
                  </Button>
                </Link>
              </>
            )}
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Estimated Value</div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(rfqData.estimatedValue)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Vendors Invited</div>
            <div className="text-2xl font-bold mt-1">{invitedCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Quotations Received</div>
            <div className="text-2xl font-bold mt-1 text-green-600">{quotedCount}/{invitedCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Due Date</div>
            <div className="text-2xl font-bold mt-1">{rfqData.endDate}</div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="items">Line Items ({rfqData.lineItems.length})</TabsTrigger>
          <TabsTrigger value="vendors">Vendors ({rfqData.vendors.length})</TabsTrigger>
          <TabsTrigger value="quotations">Quotations ({rfqData.quotations.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="details" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>RFQ Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-muted-foreground">Title</label>
                    <p className="font-medium">{rfqData.title}</p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Category</label>
                    <p><Badge variant="outline">{rfqData.category}</Badge></p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Description</label>
                    <p className="text-sm">{rfqData.description}</p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Payment Terms</label>
                    <p className="font-medium">{rfqData.paymentTerms}</p>
                  </div>
                </div>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-muted-foreground">RFQ Period</label>
                    <p className="font-medium flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      {rfqData.startDate} to {rfqData.endDate}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Expected Delivery</label>
                    <p className="font-medium">{rfqData.deliveryDate}</p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Delivery Location</label>
                    <p className="font-medium">{rfqData.deliveryLocation}</p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Created By</label>
                    <p className="font-medium">{rfqData.createdBy} on {rfqData.createdAt}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="items">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                Line Items
              </CardTitle>
              <CardDescription>Items included in this RFQ</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[60px]">#</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-center">Quantity</TableHead>
                    <TableHead className="text-center">UOM</TableHead>
                    <TableHead>Specifications</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rfqData.lineItems.map((item, index) => (
                    <TableRow key={item.id}>
                      <TableCell className="font-medium">{index + 1}</TableCell>
                      <TableCell className="font-medium">{item.description}</TableCell>
                      <TableCell className="text-center">{item.quantity}</TableCell>
                      <TableCell className="text-center">{item.uom}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{item.specifications}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="vendors">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Invited Vendors
              </CardTitle>
              <CardDescription>Vendors invited to quote for this RFQ</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Vendor Code</TableHead>
                    <TableHead>Vendor Name</TableHead>
                    <TableHead>Contact Email</TableHead>
                    <TableHead>Phone</TableHead>
                    <TableHead>Response Date</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rfqData.vendors.map((vendor) => (
                    <TableRow key={vendor.id}>
                      <TableCell className="font-mono">{vendor.id}</TableCell>
                      <TableCell className="font-medium">{vendor.name}</TableCell>
                      <TableCell>{vendor.email}</TableCell>
                      <TableCell>{vendor.phone}</TableCell>
                      <TableCell>{vendor.responseDate || '-'}</TableCell>
                      <TableCell>{getVendorStatusBadge(vendor.status)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="quotations">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Received Quotations
              </CardTitle>
              <CardDescription>Quotations submitted by vendors</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {rfqData.quotations.map((quotation) => (
                  <div key={quotation.vendorId} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h4 className="font-semibold">{quotation.vendorName}</h4>
                        <p className="text-sm text-muted-foreground">Submitted: {quotation.submittedAt}</p>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold">{formatCurrency(quotation.totalAmount)}</div>
                        <div className="text-sm text-muted-foreground">
                          Delivery: {quotation.deliveryDays} days | Warranty: {quotation.warranty}
                        </div>
                      </div>
                    </div>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Item</TableHead>
                          <TableHead className="text-right">Unit Price</TableHead>
                          <TableHead className="text-right">Amount</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {quotation.items.map((item) => {
                          const lineItem = rfqData.lineItems.find(li => li.id === item.itemId);
                          return (
                            <TableRow key={item.itemId}>
                              <TableCell>{lineItem?.description}</TableCell>
                              <TableCell className="text-right">{formatCurrency(item.unitPrice)}</TableCell>
                              <TableCell className="text-right font-medium">{formatCurrency(item.amount)}</TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
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
