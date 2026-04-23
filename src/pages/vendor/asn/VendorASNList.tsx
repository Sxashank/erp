/**
 * Vendor ASN List
 */

import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Truck,
  Search,
  Filter,
  Eye,
  Plus,
  Loader2,
  CheckCircle,
  Package,
  MapPin,
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
import { vendorASNApi } from '@/services/vendorApi';
import type { AdvancedShippingNotice, ASNStatus } from '@/types/vendor';

export default function VendorASNList() {
  const { toast } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();

  const [loading, setLoading] = useState(true);
  const [asns, setASNs] = useState<AdvancedShippingNotice[]>([]);
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState(searchParams.get('status') || 'all');
  const [page, setPage] = useState(1);
  const limit = 20;

  useEffect(() => {
    fetchASNs();
  }, [status, page]);

  const fetchASNs = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = {
        skip: (page - 1) * limit,
        limit,
      };
      if (status !== 'all') params.status = status;

      const response = await vendorASNApi.list(params);
      setASNs(response.data.items);
      setTotal(response.data.total);
    } catch (error) {
      console.error('Failed to fetch ASNs:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to load shipments',
      });
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (asn: AdvancedShippingNotice) => {
    const statusColors: Record<ASNStatus, string> = {
      DRAFT: 'bg-gray-100 text-gray-800',
      DISPATCHED: 'bg-blue-100 text-blue-800',
      IN_TRANSIT: 'bg-yellow-100 text-yellow-800',
      DELIVERED: 'bg-green-100 text-green-800',
      PARTIALLY_RECEIVED: 'bg-orange-100 text-orange-800',
      CANCELLED: 'bg-red-100 text-red-800',
    };
    return (
      <Badge className={statusColors[asn.status] || 'bg-gray-100 text-gray-800'}>
        {asn.status.replace(/_/g, ' ')}
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Shipments (ASN)"
        subtitle="Create and track Advanced Shipping Notices"
        actions={
          <Link to="/vendor/asn/new">
            <Button className="bg-purple-600 hover:bg-purple-700">
              <Plus className="h-4 w-4 mr-2" />
              Create ASN
            </Button>
          </Link>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gray-50 border-gray-200">
          <CardContent className="pt-4">
            <div className="flex items-center space-x-2">
              <Package className="h-5 w-5 text-gray-600" />
              <span className="text-sm font-medium text-gray-800">Draft</span>
            </div>
            <p className="text-2xl font-bold text-gray-900 mt-2">
              {asns.filter(a => a.status === 'DRAFT').length}
            </p>
          </CardContent>
        </Card>
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-4">
            <div className="flex items-center space-x-2">
              <Truck className="h-5 w-5 text-blue-600" />
              <span className="text-sm font-medium text-blue-800">Dispatched</span>
            </div>
            <p className="text-2xl font-bold text-blue-900 mt-2">
              {asns.filter(a => a.status === 'DISPATCHED').length}
            </p>
          </CardContent>
        </Card>
        <Card className="bg-yellow-50 border-yellow-200">
          <CardContent className="pt-4">
            <div className="flex items-center space-x-2">
              <MapPin className="h-5 w-5 text-yellow-600" />
              <span className="text-sm font-medium text-yellow-800">In Transit</span>
            </div>
            <p className="text-2xl font-bold text-yellow-900 mt-2">
              {asns.filter(a => a.status === 'IN_TRANSIT').length}
            </p>
          </CardContent>
        </Card>
        <Card className="bg-green-50 border-green-200">
          <CardContent className="pt-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <span className="text-sm font-medium text-green-800">Delivered</span>
            </div>
            <p className="text-2xl font-bold text-green-900 mt-2">
              {asns.filter(a => a.status === 'DELIVERED').length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input placeholder="Search by ASN number..." className="pl-10" />
            </div>
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
                <SelectItem value="all">All Shipments</SelectItem>
                <SelectItem value="DRAFT">Draft</SelectItem>
                <SelectItem value="DISPATCHED">Dispatched</SelectItem>
                <SelectItem value="IN_TRANSIT">In Transit</SelectItem>
                <SelectItem value="DELIVERED">Delivered</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* ASN Table */}
      <Card>
        <CardHeader>
          <CardTitle>Shipments</CardTitle>
          <CardDescription>Total {total} shipments</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
            </div>
          ) : asns.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-gray-500">
              <Truck className="h-12 w-12 text-gray-300 mb-2" />
              <p>No shipments found</p>
              <Link to="/vendor/asn/new" className="mt-4">
                <Button variant="outline">Create your first ASN</Button>
              </Link>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ASN Number</TableHead>
                  <TableHead>Ship Date</TableHead>
                  <TableHead>Expected Delivery</TableHead>
                  <TableHead>Carrier</TableHead>
                  <TableHead>Tracking #</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {asns.map((asn) => (
                  <TableRow key={asn.id}>
                    <TableCell className="font-medium">{asn.asn_number}</TableCell>
                    <TableCell>
                      {asn.ship_date ? new Date(asn.ship_date).toLocaleDateString() : '-'}
                    </TableCell>
                    <TableCell>
                      {asn.expected_delivery_date
                        ? new Date(asn.expected_delivery_date).toLocaleDateString()
                        : '-'}
                    </TableCell>
                    <TableCell>{asn.carrier_name || '-'}</TableCell>
                    <TableCell>{asn.tracking_number || '-'}</TableCell>
                    <TableCell>{getStatusBadge(asn)}</TableCell>
                    <TableCell className="text-right">
                      <Link to={`/vendor/asn/${asn.id}`}>
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

          {total > limit && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-gray-500">
                Showing {(page - 1) * limit + 1} to {Math.min(page * limit, total)} of {total}
              </p>
              <div className="flex space-x-2">
                <Button variant="outline" size="sm" onClick={() => setPage(page - 1)} disabled={page === 1}>
                  Previous
                </Button>
                <Button variant="outline" size="sm" onClick={() => setPage(page + 1)} disabled={page * limit >= total}>
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
