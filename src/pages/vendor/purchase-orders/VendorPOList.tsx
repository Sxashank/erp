/**
 * Vendor Purchase Order List
 */

import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  ShoppingCart,
  Search,
  Filter,
  Eye,
  CheckCircle,
  XCircle,
  FileText,
  Loader2,
  Clock,
  AlertCircle,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { vendorPOApi } from '@/services/vendorApi';
import type { PurchaseOrder } from '@/types/vendor';

export default function VendorPOList() {
  const { toast } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();

  const [loading, setLoading] = useState(true);
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrder[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState(searchParams.get('status') || 'all');
  const [page, setPage] = useState(1);
  const limit = 20;

  useEffect(() => {
    fetchPurchaseOrders();
  }, [status, page]);

  const fetchPurchaseOrders = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = {
        skip: (page - 1) * limit,
        limit,
      };
      if (status !== 'all') params.status = status;
      if (search) params.search = search;

      const response = await vendorPOApi.list(params);
      setPurchaseOrders(response.data.items);
      setTotal(response.data.total);
    } catch (error) {
      console.error('Failed to fetch POs:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to load purchase orders',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchPurchaseOrders();
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getStatusBadge = (po: PurchaseOrder) => {
    const ackStatus = po.acknowledgement_status;
    if (ackStatus === 'ACKNOWLEDGED') {
      return <Badge className="bg-green-100 text-green-800">Acknowledged</Badge>;
    }
    if (ackStatus === 'REJECTED') {
      return <Badge className="bg-red-100 text-red-800">Rejected</Badge>;
    }
    if (ackStatus === 'CHANGE_REQUESTED') {
      return <Badge className="bg-yellow-100 text-yellow-800">Change Requested</Badge>;
    }
    return <Badge className="bg-orange-100 text-orange-800">Pending</Badge>;
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Purchase Orders"
        subtitle="View and acknowledge purchase orders"
      />

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <form onSubmit={handleSearch} className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search by PO number..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-10"
                />
              </div>
            </form>
            <Select
              value={status}
              onValueChange={(value) => {
                setStatus(value);
                setSearchParams(value !== 'all' ? { status: value } : {});
              }}
            >
              <SelectTrigger className="w-[200px]">
                <Filter className="mr-2 h-4 w-4" />
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All POs</SelectItem>
                <SelectItem value="pending">Pending Acknowledgement</SelectItem>
                <SelectItem value="acknowledged">Acknowledged</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-orange-50 border-orange-200">
          <CardContent className="pt-4">
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-orange-600" />
              <span className="text-sm font-medium text-orange-800">Pending</span>
            </div>
            <p className="text-2xl font-bold text-orange-900 mt-2">
              {purchaseOrders.filter(po => !po.acknowledgement_status || po.acknowledgement_status === 'PENDING').length}
            </p>
          </CardContent>
        </Card>
        <Card className="bg-green-50 border-green-200">
          <CardContent className="pt-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <span className="text-sm font-medium text-green-800">Acknowledged</span>
            </div>
            <p className="text-2xl font-bold text-green-900 mt-2">
              {purchaseOrders.filter(po => po.acknowledgement_status === 'ACKNOWLEDGED').length}
            </p>
          </CardContent>
        </Card>
        <Card className="bg-yellow-50 border-yellow-200">
          <CardContent className="pt-4">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-yellow-600" />
              <span className="text-sm font-medium text-yellow-800">Change Requested</span>
            </div>
            <p className="text-2xl font-bold text-yellow-900 mt-2">
              {purchaseOrders.filter(po => po.acknowledgement_status === 'CHANGE_REQUESTED').length}
            </p>
          </CardContent>
        </Card>
        <Card className="bg-red-50 border-red-200">
          <CardContent className="pt-4">
            <div className="flex items-center space-x-2">
              <XCircle className="h-5 w-5 text-red-600" />
              <span className="text-sm font-medium text-red-800">Rejected</span>
            </div>
            <p className="text-2xl font-bold text-red-900 mt-2">
              {purchaseOrders.filter(po => po.acknowledgement_status === 'REJECTED').length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* PO Table */}
      <Card>
        <CardHeader>
          <CardTitle>Purchase Orders</CardTitle>
          <CardDescription>Total {total} purchase orders</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
            </div>
          ) : purchaseOrders.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-gray-500">
              <ShoppingCart className="h-12 w-12 text-gray-300 mb-2" />
              <p>No purchase orders found</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>PO Number</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Delivery Date</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {purchaseOrders.map((po) => (
                  <TableRow key={po.id}>
                    <TableCell className="font-medium">{po.po_number}</TableCell>
                    <TableCell>{new Date(po.po_date).toLocaleDateString()}</TableCell>
                    <TableCell>
                      {po.delivery_date ? new Date(po.delivery_date).toLocaleDateString() : '-'}
                    </TableCell>
                    <TableCell className="text-right">{formatCurrency(po.total_amount)}</TableCell>
                    <TableCell>{getStatusBadge(po)}</TableCell>
                    <TableCell className="text-right">
                      <Link to={`/vendor/purchase-orders/${po.id}`}>
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4 mr-1" />
                          View
                        </Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}

          {/* Pagination */}
          {total > limit && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-gray-500">
                Showing {(page - 1) * limit + 1} to {Math.min(page * limit, total)} of {total}
              </p>
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page + 1)}
                  disabled={page * limit >= total}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
