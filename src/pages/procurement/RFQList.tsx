import {
  FileText,
  Plus,
  Search,
  Filter,
  Eye,
  Edit,
  Clock,
  CheckCircle,
  XCircle,
  Send,
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
// Mock RFQ data
const rfqs = [
  {
    id: '1',
    rfqNumber: 'RFQ2025010001',
    title: 'Office Furniture - Q1 2025',
    category: 'Furniture',
    estimatedValue: 500000,
    vendors: 5,
    quotationsReceived: 3,
    startDate: '2025-01-10',
    endDate: '2025-01-20',
    status: 'OPEN',
    createdBy: 'Admin',
  },
  {
    id: '2',
    rfqNumber: 'RFQ2025010002',
    title: 'IT Equipment - Laptops',
    category: 'IT Hardware',
    estimatedValue: 1200000,
    vendors: 4,
    quotationsReceived: 4,
    startDate: '2025-01-08',
    endDate: '2025-01-15',
    status: 'CLOSED',
    createdBy: 'IT Admin',
  },
  {
    id: '3',
    rfqNumber: 'RFQ2025010003',
    title: 'Annual Maintenance Contract - HVAC',
    category: 'Services',
    estimatedValue: 350000,
    vendors: 3,
    quotationsReceived: 2,
    startDate: '2025-01-12',
    endDate: '2025-01-25',
    status: 'OPEN',
    createdBy: 'Facilities',
  },
  {
    id: '4',
    rfqNumber: 'RFQ2024120015',
    title: 'Stationery - Annual Contract',
    category: 'Office Supplies',
    estimatedValue: 150000,
    vendors: 6,
    quotationsReceived: 6,
    startDate: '2024-12-15',
    endDate: '2024-12-30',
    status: 'AWARDED',
    createdBy: 'Admin',
  },
  {
    id: '5',
    rfqNumber: 'RFQ2024120010',
    title: 'Server Maintenance',
    category: 'IT Services',
    estimatedValue: 800000,
    vendors: 3,
    quotationsReceived: 0,
    startDate: '2024-12-10',
    endDate: '2024-12-20',
    status: 'CANCELLED',
    createdBy: 'IT Admin',
  },
];

export default function RFQList() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const filteredRFQs = rfqs.filter((rfq) => {
    const matchesSearch =
      rfq.rfqNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rfq.title.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || rfq.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'OPEN':
        return (
          <Badge variant="default" className="bg-green-100 text-green-800">
            <Send className="mr-1 h-3 w-3" />
            Open
          </Badge>
        );
      case 'CLOSED':
        return (
          <Badge variant="secondary">
            <Clock className="mr-1 h-3 w-3" />
            Closed
          </Badge>
        );
      case 'AWARDED':
        return (
          <Badge variant="default" className="bg-blue-100 text-blue-800">
            <CheckCircle className="mr-1 h-3 w-3" />
            Awarded
          </Badge>
        );
      case 'CANCELLED':
        return (
          <Badge variant="destructive">
            <XCircle className="mr-1 h-3 w-3" />
            Cancelled
          </Badge>
        );
      case 'DRAFT':
        return (
          <Badge variant="outline">
            <Edit className="mr-1 h-3 w-3" />
            Draft
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  // Statistics
  const stats = {
    total: rfqs.length,
    open: rfqs.filter((r) => r.status === 'OPEN').length,
    closed: rfqs.filter((r) => r.status === 'CLOSED').length,
    awarded: rfqs.filter((r) => r.status === 'AWARDED').length,
  };

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Request for Quotation (RFQ)"
        subtitle="Manage vendor quotation requests"
        actions={
          <Link to="/admin/procurement/rfq/new">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create RFQ
            </Button>
          </Link>
        }
      />

      {/* Statistics */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total RFQs</div>
            <div className="mt-1 text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Open</div>
            <div className="mt-1 text-2xl font-bold text-green-600">{stats.open}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Awaiting Decision</div>
            <div className="mt-1 text-2xl font-bold text-yellow-600">{stats.closed}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Awarded</div>
            <div className="mt-1 text-2xl font-bold text-blue-600">{stats.awarded}</div>
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
                placeholder="Search by RFQ number or title..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="max-w-sm"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="DRAFT">Draft</SelectItem>
                  <SelectItem value="OPEN">Open</SelectItem>
                  <SelectItem value="CLOSED">Closed</SelectItem>
                  <SelectItem value="AWARDED">Awarded</SelectItem>
                  <SelectItem value="CANCELLED">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* RFQ Table */}
      <Card>
        <CardHeader>
          <CardTitle>RFQ List</CardTitle>
          <CardDescription>
            Showing {filteredRFQs.length} of {rfqs.length} RFQs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>RFQ Number</TableHead>
                <TableHead>Title</TableHead>
                <TableHead>Category</TableHead>
                <TableHead className="text-right">Est. Value</TableHead>
                <TableHead className="text-center">Vendors</TableHead>
                <TableHead className="text-center">Quotes</TableHead>
                <TableHead>Due Date</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredRFQs.map((rfq) => (
                <TableRow key={rfq.id}>
                  <TableCell className="font-mono">{rfq.rfqNumber}</TableCell>
                  <TableCell>
                    <div className="font-medium">{rfq.title}</div>
                    <div className="text-xs text-muted-foreground">by {rfq.createdBy}</div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{rfq.category}</Badge>
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatIndianCompactCurrency(rfq.estimatedValue)}
                  </TableCell>
                  <TableCell className="text-center">{rfq.vendors}</TableCell>
                  <TableCell className="text-center">
                    <span
                      className={rfq.quotationsReceived === rfq.vendors ? 'text-green-600' : ''}
                    >
                      {rfq.quotationsReceived}/{rfq.vendors}
                    </span>
                  </TableCell>
                  <TableCell>{rfq.endDate}</TableCell>
                  <TableCell>{getStatusBadge(rfq.status)}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Link to={`/admin/procurement/rfq/${rfq.id}`}>
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                      </Link>
                      {rfq.status === 'CLOSED' && (
                        <Link to={`/admin/procurement/rfq/${rfq.id}/compare`}>
                          <Button variant="ghost" size="sm">
                            Compare
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
