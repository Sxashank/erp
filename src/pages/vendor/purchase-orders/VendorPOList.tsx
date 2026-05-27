/**
 * Vendor Purchase Order List
 */

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
import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
import { useToast } from '@/hooks/use-toast';
import { vendorPOApi } from '@/services/vendorApi';
import type { PurchaseOrder } from '@/types/vendor';

import { logger } from '@/lib/logger';
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
      logger.error('Failed to fetch POs:', error);
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
      <PageHeader title="Purchase Orders" subtitle="View and acknowledge purchase orders" />

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 sm:flex-row">
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
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="pt-4">
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-orange-600" />
              <span className="text-sm font-medium text-orange-800">Pending</span>
            </div>
            <p className="mt-2 text-2xl font-bold text-orange-900">
              {
                purchaseOrders.filter(
                  (po) => !po.acknowledgement_status || po.acknowledgement_status === 'PENDING',
                ).length
              }
            </p>
          </CardContent>
        </Card>
        <Card className="border-green-200 bg-green-50">
          <CardContent className="pt-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <span className="text-sm font-medium text-green-800">Acknowledged</span>
            </div>
            <p className="mt-2 text-2xl font-bold text-green-900">
              {purchaseOrders.filter((po) => po.acknowledgement_status === 'ACKNOWLEDGED').length}
            </p>
          </CardContent>
        </Card>
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="pt-4">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-yellow-600" />
              <span className="text-sm font-medium text-yellow-800">Change Requested</span>
            </div>
            <p className="mt-2 text-2xl font-bold text-yellow-900">
              {
                purchaseOrders.filter((po) => po.acknowledgement_status === 'CHANGE_REQUESTED')
                  .length
              }
            </p>
          </CardContent>
        </Card>
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-4">
            <div className="flex items-center space-x-2">
              <XCircle className="h-5 w-5 text-red-600" />
              <span className="text-sm font-medium text-red-800">Rejected</span>
            </div>
            <p className="mt-2 text-2xl font-bold text-red-900">
              {purchaseOrders.filter((po) => po.acknowledgement_status === 'REJECTED').length}
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
            <div className="flex h-64 items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
            </div>
          ) : purchaseOrders.length === 0 ? (
            <div className="flex h-64 flex-col items-center justify-center text-gray-500">
              <ShoppingCart className="mb-2 h-12 w-12 text-gray-300" />
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
                    <TableCell>
                      <DateDisplay date={po.po_date} />
                    </TableCell>
                    <TableCell>
                      <DateDisplay date={po.delivery_date} />
                    </TableCell>
                    <TableCell className="text-right">
                      {formatIndianCompactCurrency(po.total_amount)}
                    </TableCell>
                    <TableCell>{getStatusBadge(po)}</TableCell>
                    <TableCell className="text-right">
                      <Link to={`/vendor/purchase-orders/${po.id}`}>
                        <Button variant="ghost" size="sm">
                          <Eye className="mr-1 h-4 w-4" />
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
            <div className="mt-4 flex items-center justify-between">
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
