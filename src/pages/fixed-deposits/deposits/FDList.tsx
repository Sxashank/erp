/**
 * Fixed Deposit List Page
 */

import { Plus, Eye, Search, Filter } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
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
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import type {
  FixedDeposit,
  FDStatus,
  FDProduct,
} from '@/services/fixedDepositService';
import fixedDepositService from '@/services/fixedDepositService';

import { logger } from "@/lib/logger";
const ALL_FILTER_VALUE = '__all__';

const STATUS_OPTIONS: { value: FDStatus | typeof ALL_FILTER_VALUE; label: string }[] = [
  { value: ALL_FILTER_VALUE, label: 'All Status' },
  { value: 'DRAFT', label: 'Draft' },
  { value: 'PENDING_APPROVAL', label: 'Pending Approval' },
  { value: 'ACTIVE', label: 'Active' },
  { value: 'MATURED', label: 'Matured' },
  { value: 'PREMATURE_CLOSED', label: 'Premature Closed' },
  { value: 'RENEWED', label: 'Renewed' },
  { value: 'CANCELLED', label: 'Cancelled' },
];

const STATUS_COLORS: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  DRAFT: 'outline',
  PENDING_APPROVAL: 'secondary',
  ACTIVE: 'default',
  MATURED: 'default',
  PREMATURE_CLOSED: 'secondary',
  RENEWED: 'default',
  CANCELLED: 'destructive',
};

export default function FDList() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [fds, setFDs] = useState<FixedDeposit[]>([]);
  const [products, setProducts] = useState<FDProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<FDStatus | typeof ALL_FILTER_VALUE>(
    ALL_FILTER_VALUE,
  );
  const [productFilter, setProductFilter] = useState(ALL_FILTER_VALUE);
  const [total, setTotal] = useState(0);

  const organizationId = useRequiredActiveOrganizationId();

  useEffect(() => {
    loadProducts();
  }, [organizationId]);

  useEffect(() => {
    loadFDs();
  }, [organizationId, statusFilter, productFilter]);

  const loadProducts = async () => {
    try {
      const response = await fixedDepositService.listProducts({
        active_only: false,
      });
      setProducts(response.items);
    } catch (error) {
      logger.error('Failed to load products', error);
    }
  };

  const loadFDs = async () => {
    try {
      setLoading(true);
      const response = await fixedDepositService.listDeposits({
        status: statusFilter === ALL_FILTER_VALUE ? undefined : statusFilter,
        product_id: productFilter === ALL_FILTER_VALUE ? undefined : productFilter,
      });
      setFDs(response.items);
      setTotal(response.total);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load fixed deposits',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const filteredFDs = fds.filter(
    (fd) =>
      fd.fd_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      fd.customer_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Fixed Deposits"
        subtitle={`Manage customer fixed deposits (${total} total)`}
        actions={
          <Button onClick={() => navigate('/admin/fixed-deposits/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Fixed Deposit
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex flex-col md:flex-row gap-4 justify-between">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                placeholder="Search by FD number or customer..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              <Select
                value={statusFilter}
                onValueChange={(v) => setStatusFilter(v as FDStatus | typeof ALL_FILTER_VALUE)}
              >
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="All Status" />
                </SelectTrigger>
                <SelectContent>
                  {STATUS_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={productFilter} onValueChange={setProductFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="All Products" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL_FILTER_VALUE}>All Products</SelectItem>
                  {products.map((product) => (
                    <SelectItem key={product.id} value={product.id}>
                      {product.product_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>FD Number</TableHead>
                <TableHead>Product</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead className="text-right">Deposit</TableHead>
                <TableHead>Rate</TableHead>
                <TableHead>Tenure</TableHead>
                <TableHead>Maturity Date</TableHead>
                <TableHead className="text-right">Maturity Amount</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={10} className="text-center py-8">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : filteredFDs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={10} className="text-center py-8">
                    No fixed deposits found
                  </TableCell>
                </TableRow>
              ) : (
                filteredFDs.map((fd) => (
                  <TableRow key={fd.id}>
                    <TableCell className="font-mono">{fd.fd_number}</TableCell>
                    <TableCell>{fd.product_name || fd.product_code}</TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{fd.customer_name || '-'}</p>
                        <p className="text-xs text-muted-foreground">
                          {fd.customer_category}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(fd.deposit_amount)}
                    </TableCell>
                    <TableCell>{fd.interest_rate.toFixed(2)}%</TableCell>
                    <TableCell>{fd.tenure_days} days</TableCell>
                    <TableCell>
                      <DateDisplay date={fd.maturity_date} />
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      {formatCurrency(fd.maturity_amount)}
                    </TableCell>
                    <TableCell>
                      <Badge variant={STATUS_COLORS[fd.status]}>
                        {fd.status.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => navigate(`/admin/fixed-deposits/${fd.id}`)}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
