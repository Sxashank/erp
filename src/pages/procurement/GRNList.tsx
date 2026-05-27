import {
  Package,
  Plus,
  Search,
  Filter,
  Eye,
  Download,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
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
// Mock GRN data
const grnList = [
  {
    id: '1',
    grnNumber: 'GRN2025010001',
    poNumber: 'PO2025010001',
    vendor: 'ABC Suppliers Ltd',
    vendorCode: 'V001',
    receivedDate: '2025-01-15',
    totalItems: 5,
    receivedItems: 3,
    totalValue: 85000,
    status: 'PARTIAL',
    qualityStatus: 'APPROVED',
    receivedBy: 'Warehouse Team',
    invoiceNumber: 'INV-ABC-2025-001',
  },
  {
    id: '2',
    grnNumber: 'GRN2025010002',
    poNumber: 'PO2024120025',
    vendor: 'Tech World',
    vendorCode: 'V004',
    receivedDate: '2025-01-10',
    totalItems: 3,
    receivedItems: 3,
    totalValue: 250000,
    status: 'COMPLETE',
    qualityStatus: 'APPROVED',
    receivedBy: 'IT Team',
    invoiceNumber: 'INV-TW-2025-0012',
  },
  {
    id: '3',
    grnNumber: 'GRN2025010003',
    poNumber: 'PO2025010001',
    vendor: 'ABC Suppliers Ltd',
    vendorCode: 'V001',
    receivedDate: '2025-01-18',
    totalItems: 5,
    receivedItems: 2,
    totalValue: 60000,
    status: 'COMPLETE',
    qualityStatus: 'APPROVED',
    receivedBy: 'Warehouse Team',
    invoiceNumber: 'INV-ABC-2025-002',
  },
  {
    id: '4',
    grnNumber: 'GRN2025010004',
    poNumber: 'PO2025010003',
    vendor: 'Furniture Hub',
    vendorCode: 'V005',
    receivedDate: '2025-01-20',
    totalItems: 8,
    receivedItems: 8,
    totalValue: 485000,
    status: 'PENDING_QC',
    qualityStatus: 'PENDING',
    receivedBy: 'Admin',
    invoiceNumber: 'INV-FH-2025-008',
  },
  {
    id: '5',
    grnNumber: 'GRN2025010005',
    poNumber: 'PO2025010002',
    vendor: 'XYZ Tech Solutions',
    vendorCode: 'V002',
    receivedDate: '2025-01-22',
    totalItems: 10,
    receivedItems: 10,
    totalValue: 1150000,
    status: 'REJECTED',
    qualityStatus: 'REJECTED',
    receivedBy: 'IT Team',
    invoiceNumber: 'INV-XYZ-2025-015',
  },
];

export default function GRNList() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const filteredGRNs = grnList.filter((grn) => {
    const matchesSearch =
      grn.grnNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
      grn.poNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
      grn.vendor.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || grn.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PENDING_QC':
        return (
          <Badge variant="secondary">
            <Clock className="mr-1 h-3 w-3" />
            Pending QC
          </Badge>
        );
      case 'PARTIAL':
        return (
          <Badge variant="outline" className="border-yellow-500 text-yellow-700">
            <AlertTriangle className="mr-1 h-3 w-3" />
            Partial
          </Badge>
        );
      case 'COMPLETE':
        return (
          <Badge variant="default" className="bg-green-100 text-green-800">
            <CheckCircle className="mr-1 h-3 w-3" />
            Complete
          </Badge>
        );
      case 'REJECTED':
        return (
          <Badge variant="destructive">
            <XCircle className="mr-1 h-3 w-3" />
            Rejected
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getQualityBadge = (status: string) => {
    switch (status) {
      case 'PENDING':
        return <Badge variant="outline">Pending</Badge>;
      case 'APPROVED':
        return (
          <Badge variant="default" className="bg-green-100 text-green-800">
            Approved
          </Badge>
        );
      case 'REJECTED':
        return <Badge variant="destructive">Rejected</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  // Statistics
  const stats = {
    total: grnList.length,
    pendingQC: grnList.filter((g) => g.status === 'PENDING_QC').length,
    complete: grnList.filter((g) => g.status === 'COMPLETE').length,
    totalValue: grnList
      .filter((g) => g.status !== 'REJECTED')
      .reduce((sum, g) => sum + g.totalValue, 0),
  };

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Goods Receipt Notes (GRN)"
        subtitle="Manage goods receipts against purchase orders"
        actions={
          <Link to="/admin/procurement/grn/new">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create GRN
            </Button>
          </Link>
        }
      />

      {/* Statistics */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total GRNs</div>
            <div className="mt-1 text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Pending QC</div>
            <div className="mt-1 text-2xl font-bold text-yellow-600">{stats.pendingQC}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Completed</div>
            <div className="mt-1 text-2xl font-bold text-green-600">{stats.complete}</div>
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
                placeholder="Search by GRN, PO number or vendor..."
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
                  <SelectItem value="PENDING_QC">Pending QC</SelectItem>
                  <SelectItem value="PARTIAL">Partial</SelectItem>
                  <SelectItem value="COMPLETE">Complete</SelectItem>
                  <SelectItem value="REJECTED">Rejected</SelectItem>
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

      {/* GRN Table */}
      <Card>
        <CardHeader>
          <CardTitle>GRN List</CardTitle>
          <CardDescription>
            Showing {filteredGRNs.length} of {grnList.length} goods receipt notes
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>GRN Number</TableHead>
                <TableHead>PO Number</TableHead>
                <TableHead>Vendor</TableHead>
                <TableHead>Received Date</TableHead>
                <TableHead className="text-center">Items</TableHead>
                <TableHead className="text-right">Value</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>QC Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredGRNs.map((grn) => (
                <TableRow key={grn.id}>
                  <TableCell className="font-mono">{grn.grnNumber}</TableCell>
                  <TableCell>
                    <Link
                      to={`/admin/procurement/po/${grn.poNumber}`}
                      className="text-primary hover:underline"
                    >
                      {grn.poNumber}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <div className="font-medium">{grn.vendor}</div>
                    <div className="text-xs text-muted-foreground">{grn.vendorCode}</div>
                  </TableCell>
                  <TableCell>{grn.receivedDate}</TableCell>
                  <TableCell className="text-center">
                    <span
                      className={
                        grn.receivedItems === grn.totalItems ? 'text-green-600' : 'text-yellow-600'
                      }
                    >
                      {grn.receivedItems}/{grn.totalItems}
                    </span>
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatIndianCompactCurrency(grn.totalValue)}
                  </TableCell>
                  <TableCell>{getStatusBadge(grn.status)}</TableCell>
                  <TableCell>{getQualityBadge(grn.qualityStatus)}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Link to={`/admin/procurement/grn/${grn.id}`}>
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                      </Link>
                      {grn.qualityStatus === 'PENDING' && (
                        <Link to={`/admin/procurement/grn/${grn.id}/qc`}>
                          <Button variant="ghost" size="sm">
                            QC
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
