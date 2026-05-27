import { Plus, Search, Filter, MoreHorizontal, Eye, Edit, Settings, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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
import {
  useLoanProducts,
  type LoanProductListItem,
  type ProductCategoryValue,
  type LoanProductFilters,
} from '@/hooks/lending/useLoanProducts';
import { useLendingOptionRows } from '@/hooks/lending/useLendingMasters';

export default function ProductList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const filters: LoanProductFilters = {
    pageSize: 100,
    ...(searchQuery && { search: searchQuery }),
    ...(categoryFilter !== 'ALL' && {
      category: categoryFilter as ProductCategoryValue,
    }),
    ...(statusFilter === 'INACTIVE' && { includeInactive: true }),
  };
  const { data, isLoading, isError, error, refetch } = useLoanProducts(filters);
  const productCategoriesQuery = useLendingOptionRows('PRODUCT_CATEGORY');
  const productCategoryOptions =
    productCategoriesQuery.data?.items.map((row) => ({
      value: String(row.data.code ?? ''),
      label: String(row.data.label ?? row.data.code ?? ''),
    })) ?? [];
  const categoryLabel = (value: string) =>
    productCategoryOptions.find((option) => option.value === value)?.label ??
    value.replace(/_/g, ' ');

  const all: LoanProductListItem[] = data?.items ?? [];
  // Status filter is client-side — BE returns active by default; we use
  // include_inactive=true to widen the result, then filter to the bucket here.
  const products = all.filter((p) => {
    if (statusFilter === 'ACTIVE') return p.isActive;
    if (statusFilter === 'INACTIVE') return !p.isActive;
    return true;
  });

  const activeCount = products.filter((p) => p.isActive).length;
  const categoryCount = new Set(products.map((p) => p.category)).size;
  // Wire rates are strings (Decimal precision); coerce once for display arithmetic.
  const avgRate = (() => {
    const withRate = products.filter((p) => p.baseRateValue != null || p.spreadBps != null);
    if (withRate.length === 0) return 0;
    return (
      withRate.reduce(
        (sum, p) => sum + (Number(p.baseRateValue ?? 0) + (p.spreadBps ?? 0) / 100),
        0,
      ) / withRate.length
    );
  })();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Loan Products"
        subtitle="Manage loan products, interest rates, and fee configurations"
        actions={
          <Button onClick={() => navigate('/admin/lending/products/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Product
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Products</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.total ?? products.length}</div>
            <p className="text-xs text-muted-foreground">Across all categories</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Products</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeCount}</div>
            <p className="text-xs text-muted-foreground">Available for booking</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Categories</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{categoryCount}</div>
            <p className="text-xs text-muted-foreground">Product categories</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {avgRate > 0 ? <PercentageDisplay value={avgRate} /> : '—'}
            </div>
            <p className="text-xs text-muted-foreground">Base + spread</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by product name or code..."
                className="pl-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="w-[200px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Categories</SelectItem>
                  {productCategoryOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Status</SelectItem>
                  <SelectItem value="ACTIVE">Active</SelectItem>
                  <SelectItem value="INACTIVE">Inactive</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product Code</TableHead>
                <TableHead>Product Name</TableHead>
                <TableHead>Category</TableHead>
                <TableHead className="text-right">Min Amount</TableHead>
                <TableHead className="text-right">Max Amount</TableHead>
                <TableHead>Tenure</TableHead>
                <TableHead>Interest Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading || productCategoriesQuery.isLoading ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8 text-center text-muted-foreground">
                    <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />
                    Loading products...
                  </TableCell>
                </TableRow>
              ) : isError || productCategoriesQuery.isError ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8">
                    <ErrorState
                      title="Could not load loan products"
                      error={error ?? productCategoriesQuery.error}
                      onRetry={() => {
                        refetch();
                        productCategoriesQuery.refetch();
                      }}
                    />
                  </TableCell>
                </TableRow>
              ) : products.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8 text-center text-muted-foreground">
                    No products found
                  </TableCell>
                </TableRow>
              ) : (
                products.map((product) => (
                  <TableRow
                    key={product.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => navigate(`/admin/lending/products/${product.id}`)}
                  >
                    <TableCell className="font-mono text-sm">{product.code}</TableCell>
                    <TableCell className="font-medium">{product.name}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="bg-blue-50 text-blue-700">
                        {categoryLabel(product.category)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={product.minAmount} abbreviated />
                    </TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={product.maxAmount} abbreviated />
                    </TableCell>
                    <TableCell>
                      {product.minTenureMonths}-{product.maxTenureMonths} months
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{product.interestType}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={
                          product.isActive
                            ? 'bg-green-50 text-green-700'
                            : 'bg-gray-50 text-gray-700'
                        }
                      >
                        {product.isActive ? 'ACTIVE' : 'INACTIVE'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/admin/lending/products/${product.id}`);
                            }}
                          >
                            <Eye className="mr-2 h-4 w-4" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/admin/lending/products/${product.id}/edit`);
                            }}
                          >
                            <Edit className="mr-2 h-4 w-4" />
                            Edit Product
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/admin/lending/products/${product.id}/checklist`);
                            }}
                          >
                            <Settings className="mr-2 h-4 w-4" />
                            Document Checklist
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
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
