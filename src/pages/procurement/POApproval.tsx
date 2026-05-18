import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Clock,
  Eye,
  FileText,
  Building2,
  Calendar,
  DollarSign,
} from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

// Mock pending POs for approval
const pendingApprovals = [
  {
    id: '1',
    poNumber: 'PO2025010002',
    vendor: 'XYZ Tech Solutions',
    vendorCode: 'V002',
    rfqNumber: 'RFQ2025010002',
    totalAmount: 1150000,
    poDate: '2025-01-12',
    deliveryDate: '2025-01-30',
    items: 10,
    createdBy: 'IT Admin',
    submittedAt: '2025-01-12 11:30 AM',
    category: 'IT Hardware',
    urgency: 'HIGH',
    lineItems: [
      { description: 'Laptop - Dell Latitude 5540', quantity: 10, unitPrice: 85000, total: 850000 },
      { description: 'Docking Station', quantity: 10, unitPrice: 15000, total: 150000 },
      { description: 'Wireless Mouse & Keyboard', quantity: 10, unitPrice: 3000, total: 30000 },
      { description: 'Laptop Bag', quantity: 10, unitPrice: 2000, total: 20000 },
      { description: 'Extended Warranty - 3 Years', quantity: 10, unitPrice: 10000, total: 100000 },
    ],
  },
  {
    id: '2',
    poNumber: 'PO2025010005',
    vendor: 'Office Pro',
    vendorCode: 'V003',
    rfqNumber: null,
    totalAmount: 45000,
    poDate: '2025-01-14',
    deliveryDate: '2025-01-20',
    items: 6,
    createdBy: 'Admin',
    submittedAt: '2025-01-14 03:45 PM',
    category: 'Office Supplies',
    urgency: 'NORMAL',
    lineItems: [
      { description: 'A4 Paper (500 sheets) x 50 reams', quantity: 50, unitPrice: 350, total: 17500 },
      { description: 'Printer Cartridges - HP 78A', quantity: 10, unitPrice: 1500, total: 15000 },
      { description: 'Stapler Set', quantity: 25, unitPrice: 250, total: 6250 },
      { description: 'Pen Boxes (50 pens)', quantity: 10, unitPrice: 350, total: 3500 },
      { description: 'Notepads', quantity: 50, unitPrice: 50, total: 2500 },
      { description: 'File Folders', quantity: 25, unitPrice: 10, total: 250 },
    ],
  },
  {
    id: '3',
    poNumber: 'PO2025010006',
    vendor: 'Furniture Hub',
    vendorCode: 'V005',
    rfqNumber: 'RFQ2025010001',
    totalAmount: 485000,
    poDate: '2025-01-15',
    deliveryDate: '2025-02-10',
    items: 4,
    createdBy: 'Admin',
    submittedAt: '2025-01-15 10:15 AM',
    category: 'Furniture',
    urgency: 'NORMAL',
    lineItems: [
      { description: 'Ergonomic Office Chair', quantity: 50, unitPrice: 4500, total: 225000 },
      { description: 'Standing Desk - Electric', quantity: 25, unitPrice: 6500, total: 162500 },
      { description: 'Filing Cabinet - 4 Drawer', quantity: 30, unitPrice: 2800, total: 84000 },
      { description: 'Conference Table', quantity: 5, unitPrice: 2700, total: 13500 },
    ],
  },
];

const approvalHistory = [
  {
    poNumber: 'PO2025010001',
    vendor: 'ABC Suppliers Ltd',
    amount: 145000,
    action: 'APPROVED',
    actionBy: 'Finance Head',
    actionAt: '2025-01-11 04:30 PM',
    remarks: 'Approved as per budget allocation.',
  },
  {
    poNumber: 'PO2024120020',
    vendor: 'Services Plus',
    amount: 75000,
    action: 'REJECTED',
    actionBy: 'Finance Head',
    actionAt: '2025-01-10 02:15 PM',
    remarks: 'Budget exceeded for Q4. Please resubmit in Q1.',
  },
];

export default function POApproval() {
  const navigate = useNavigate();
  const [selectedPO, setSelectedPO] = useState<typeof pendingApprovals[0] | null>(null);
  const [showApproveDialog, setShowApproveDialog] = useState(false);
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [remarks, setRemarks] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const handleApprove = async () => {
    setIsProcessing(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsProcessing(false);
    setShowApproveDialog(false);
    setSelectedPO(null);
    setRemarks('');
  };

  const handleReject = async () => {
    setIsProcessing(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsProcessing(false);
    setShowRejectDialog(false);
    setSelectedPO(null);
    setRemarks('');
  };

  const getUrgencyBadge = (urgency: string) => {
    switch (urgency) {
      case 'HIGH':
        return <Badge variant="destructive">High Priority</Badge>;
      case 'NORMAL':
        return <Badge variant="secondary">Normal</Badge>;
      case 'LOW':
        return <Badge variant="outline">Low</Badge>;
      default:
        return <Badge variant="outline">{urgency}</Badge>;
    }
  };

  // Statistics
  const stats = {
    pending: pendingApprovals.length,
    totalValue: pendingApprovals.reduce((sum, po) => sum + po.totalAmount, 0),
    highPriority: pendingApprovals.filter(p => p.urgency === 'HIGH').length,
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="PO Approval"
        subtitle="Review and approve purchase orders"
        breadcrumbs={[
          { label: 'Purchase Orders', to: '/admin/procurement/po' },
          { label: 'Approval' },
        ]}
      />

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Pending Approval</div>
            <div className="text-2xl font-bold mt-1 text-yellow-600">{stats.pending}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Value Pending</div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(stats.totalValue)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">High Priority</div>
            <div className="text-2xl font-bold mt-1 text-red-600">{stats.highPriority}</div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="pending">
        <TabsList>
          <TabsTrigger value="pending">Pending ({pendingApprovals.length})</TabsTrigger>
          <TabsTrigger value="history">History ({approvalHistory.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="pending" className="space-y-4">
          {pendingApprovals.map((po) => (
            <Card key={po.id} className={po.urgency === 'HIGH' ? 'border-red-200' : ''}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="h-5 w-5" />
                      {po.poNumber}
                      {getUrgencyBadge(po.urgency)}
                    </CardTitle>
                    <CardDescription>
                      Submitted by {po.createdBy} on {po.submittedAt}
                    </CardDescription>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold">{formatCurrency(po.totalAmount)}</div>
                    <Badge variant="outline">{po.category}</Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div className="flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Vendor</p>
                      <p className="font-medium">{po.vendor}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">PO Date</p>
                      <p className="font-medium">{po.poDate}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Delivery Date</p>
                      <p className="font-medium">{po.deliveryDate}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">RFQ Reference</p>
                      <p className="font-medium">{po.rfqNumber || 'Direct PO'}</p>
                    </div>
                  </div>
                </div>

                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Item Description</TableHead>
                      <TableHead className="text-center">Qty</TableHead>
                      <TableHead className="text-right">Unit Price</TableHead>
                      <TableHead className="text-right">Total</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {po.lineItems.map((item, index) => (
                      <TableRow key={index}>
                        <TableCell>{item.description}</TableCell>
                        <TableCell className="text-center">{item.quantity}</TableCell>
                        <TableCell className="text-right">{formatCurrency(item.unitPrice)}</TableCell>
                        <TableCell className="text-right font-medium">{formatCurrency(item.total)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>

                <div className="flex justify-end gap-2 mt-4">
                  <Link to={`/admin/procurement/po/${po.id}`}>
                    <Button variant="outline" size="sm">
                      <Eye className="h-4 w-4 mr-2" />
                      View Details
                    </Button>
                  </Link>
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-red-600 hover:text-red-700"
                    onClick={() => {
                      setSelectedPO(po);
                      setShowRejectDialog(true);
                    }}
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    Reject
                  </Button>
                  <Button
                    size="sm"
                    className="bg-green-600 hover:bg-green-700"
                    onClick={() => {
                      setSelectedPO(po);
                      setShowApproveDialog(true);
                    }}
                  >
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    Approve
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>Approval History</CardTitle>
              <CardDescription>Recent approval actions</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>PO Number</TableHead>
                    <TableHead>Vendor</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Action By</TableHead>
                    <TableHead>Date/Time</TableHead>
                    <TableHead>Remarks</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {approvalHistory.map((item, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-mono">{item.poNumber}</TableCell>
                      <TableCell>{item.vendor}</TableCell>
                      <TableCell className="text-right">{formatCurrency(item.amount)}</TableCell>
                      <TableCell>
                        {item.action === 'APPROVED' ? (
                          <Badge className="bg-green-100 text-green-800">
                            <CheckCircle2 className="h-3 w-3 mr-1" />
                            Approved
                          </Badge>
                        ) : (
                          <Badge variant="destructive">
                            <XCircle className="h-3 w-3 mr-1" />
                            Rejected
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>{item.actionBy}</TableCell>
                      <TableCell>{item.actionAt}</TableCell>
                      <TableCell className="max-w-xs truncate">{item.remarks}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Approve Dialog */}
      <Dialog open={showApproveDialog} onOpenChange={setShowApproveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Approve Purchase Order</DialogTitle>
            <DialogDescription>
              Are you sure you want to approve {selectedPO?.poNumber}?
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="p-4 bg-muted rounded-lg">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-muted-foreground">PO Number:</span>
                  <p className="font-medium">{selectedPO?.poNumber}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Vendor:</span>
                  <p className="font-medium">{selectedPO?.vendor}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Amount:</span>
                  <p className="font-medium">{selectedPO && formatCurrency(selectedPO.totalAmount)}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Items:</span>
                  <p className="font-medium">{selectedPO?.items}</p>
                </div>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium">Remarks (Optional)</label>
              <Textarea
                placeholder="Enter approval remarks..."
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                rows={3}
                className="mt-2"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowApproveDialog(false)}>
              Cancel
            </Button>
            <Button
              className="bg-green-600 hover:bg-green-700"
              onClick={handleApprove}
              disabled={isProcessing}
            >
              <CheckCircle2 className="h-4 w-4 mr-2" />
              Confirm Approval
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reject Dialog */}
      <Dialog open={showRejectDialog} onOpenChange={setShowRejectDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject Purchase Order</DialogTitle>
            <DialogDescription>
              Are you sure you want to reject {selectedPO?.poNumber}?
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="p-4 bg-muted rounded-lg">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-muted-foreground">PO Number:</span>
                  <p className="font-medium">{selectedPO?.poNumber}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Vendor:</span>
                  <p className="font-medium">{selectedPO?.vendor}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Amount:</span>
                  <p className="font-medium">{selectedPO && formatCurrency(selectedPO.totalAmount)}</p>
                </div>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium">Reason for Rejection *</label>
              <Textarea
                placeholder="Enter rejection reason..."
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                rows={3}
                className="mt-2"
                required
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRejectDialog(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleReject}
              disabled={isProcessing || !remarks.trim()}
            >
              <XCircle className="h-4 w-4 mr-2" />
              Confirm Rejection
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
