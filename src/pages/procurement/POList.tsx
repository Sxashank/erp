import {
  ShoppingCart,
  Plus,
  Search,
  Filter,
  Eye,
  Download,
  CheckCircle,
  XCircle,
  Clock,
  Truck,
} from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
// Mock PO data
const purchaseOrders = [
  {
    id: '1',
    poNumber: 'PO2025010001',
    vendor: 'ABC Suppliers Ltd',
    vendorCode: 'V001',
    rfqNumber: 'RFQ2024120015',
    totalAmount: 145000,
    poDate: '2025-01-10',
    deliveryDate: '2025-01-25',
    status: 'APPROVED',
    grnStatus: 'PARTIAL',
    items: 5,
    createdBy: 'Procurement Team',
  },
  {
    id: '2',
    poNumber: 'PO2025010002',
    vendor: 'XYZ Tech Solutions',
    vendorCode: 'V002',
    rfqNumber: 'RFQ2025010002',
    totalAmount: 1150000,
    poDate: '2025-01-12',
    deliveryDate: '2025-01-30',
    status: 'PENDING_APPROVAL',
    grnStatus: 'PENDING',
    items: 10,
    createdBy: 'IT Admin',
  },
  {
    id: '3',
    poNumber: 'PO2025010003',
    vendor: 'Furniture Hub',
    vendorCode: 'V005',
    rfqNumber: 'RFQ2025010001',
    totalAmount: 485000,
    poDate: '2025-01-14',
    deliveryDate: '2025-02-10',
    status: 'APPROVED',
    grnStatus: 'PENDING',
    items: 8,
    createdBy: 'Admin',
  },
  {
    id: '4',
    poNumber: 'PO2024120025',
    vendor: 'Tech World',
    vendorCode: 'V004',
    rfqNumber: null,
    totalAmount: 250000,
    poDate: '2024-12-20',
    deliveryDate: '2025-01-10',
    status: 'COMPLETED',
    grnStatus: 'COMPLETE',
    items: 3,
    createdBy: 'IT Admin',
  },
  {
    id: '5',
    poNumber: 'PO2024120020',
    vendor: 'Services Plus',
    vendorCode: 'V006',
    rfqNumber: null,
    totalAmount: 75000,
    poDate: '2024-12-15',
    deliveryDate: '2024-12-30',
    status: 'CANCELLED',
    grnStatus: 'N/A',
    items: 1,
    createdBy: 'Facilities',
  },
];

export default function POList() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const filteredPOs = purchaseOrders.filter((po) => {
    const matchesSearch =
      po.poNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
      po.vendor.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || po.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'DRAFT':
        return <Badge variant="outline">Draft</Badge>;
      case 'PENDING_APPROVAL':
        return (
          <Badge variant="secondary">
            <Clock className="mr-1 h-3 w-3" />
            Pending Approval
          </Badge>
        );
      case 'APPROVED':
        return (
          <Badge variant="default" className="bg-green-100 text-green-800">
            <CheckCircle className="mr-1 h-3 w-3" />
            Approved
          </Badge>
        );
      case 'COMPLETED':
        return (
          <Badge variant="default" className="bg-blue-100 text-blue-800">
            <Truck className="mr-1 h-3 w-3" />
            Completed
          </Badge>
        );
      case 'CANCELLED':
        return (
          <Badge variant="destructive">
            <XCircle className="mr-1 h-3 w-3" />
            Cancelled
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getGRNBadge = (status: string) => {
    switch (status) {
      case 'PENDING':
        return <Badge variant="outline">Pending</Badge>;
      case 'PARTIAL':
        return <Badge variant="secondary">Partial</Badge>;
      case 'COMPLETE':
        return (
          <Badge variant="default" className="bg-green-100 text-green-800">
            Complete
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  // Statistics
  const stats = {
    total: purchaseOrders.length,
    pending: purchaseOrders.filter((p) => p.status === 'PENDING_APPROVAL').length,
    approved: purchaseOrders.filter((p) => p.status === 'APPROVED').length,
    totalValue: purchaseOrders
      .filter((p) => p.status !== 'CANCELLED')
      .reduce((sum, p) => sum + p.totalAmount, 0),
  };

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Purchase Orders"
        subtitle="Manage purchase orders"
        actions={
          <Link to="/admin/procurement/po/new">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create Purchase Order
            </Button>
          </Link>
        }
      />

      {/* Statistics */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total POs</div>
            <div className="mt-1 text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Pending Approval</div>
            <div className="mt-1 text-2xl font-bold text-yellow-600">{stats.pending}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Approved</div>
            <div className="mt-1 text-2xl font-bold text-green-600">{stats.approved}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Value</div>
            <div className="mt-1 text-2xl font-bold">
              {formatIndianCompactCurrency(stats.totalValue)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex min-w-[200px] flex-1 items-center gap-2">
              <Search className="h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by PO number or vendor..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="max-w-sm"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="DRAFT">Draft</SelectItem>
                  <SelectItem value="PENDING_APPROVAL">Pending Approval</SelectItem>
                  <SelectItem value="APPROVED">Approved</SelectItem>
                  <SelectItem value="COMPLETED">Completed</SelectItem>
                  <SelectItem value="CANCELLED">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* PO Table */}
      <Card>
        <CardHeader>
          <CardTitle>Purchase Order List</CardTitle>
          <CardDescription>
            Showing {filteredPOs.length} of {purchaseOrders.length} purchase orders
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>PO Number</TableHead>
                <TableHead>Vendor</TableHead>
                <TableHead>RFQ Ref</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead className="text-center">Items</TableHead>
                <TableHead>PO Date</TableHead>
                <TableHead>Delivery</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>GRN</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredPOs.map((po) => (
                <TableRow key={po.id}>
                  <TableCell className="font-mono">{po.poNumber}</TableCell>
                  <TableCell>
                    <div className="font-medium">{po.vendor}</div>
                    <div className="text-xs text-muted-foreground">{po.vendorCode}</div>
                  </TableCell>
                  <TableCell>
                    {po.rfqNumber ? (
                      <Link
                        to={`/admin/procurement/rfq/${po.rfqNumber}`}
                        className="text-primary hover:underline"
                      >
                        {po.rfqNumber}
                      </Link>
                    ) : (
                      <span className="text-muted-foreground">Direct PO</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatIndianCompactCurrency(po.totalAmount)}
                  </TableCell>
                  <TableCell className="text-center">{po.items}</TableCell>
                  <TableCell>{po.poDate}</TableCell>
                  <TableCell>{po.deliveryDate}</TableCell>
                  <TableCell>{getStatusBadge(po.status)}</TableCell>
                  <TableCell>{getGRNBadge(po.grnStatus)}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Link to={`/admin/procurement/po/${po.id}`}>
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                      </Link>
                      {po.status === 'APPROVED' && po.grnStatus !== 'COMPLETE' && (
                        <Link to={`/admin/procurement/grn/new?po=${po.id}`}>
                          <Button variant="ghost" size="sm">
                            GRN
                          </Button>
                        </Link>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
