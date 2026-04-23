import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Filter, MoreHorizontal, Eye, Edit, Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { StatusBadge } from '@/components/lending/common/StatusBadge';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
// Local product type matching UI mock data (camelCase)
interface ProductListItem {
  id: string;
  productCode: string;
  productName: string;
  category: string;
  subCategory: string;
  minAmount: number;
  maxAmount: number;
  minTenureMonths: number;
  maxTenureMonths: number;
  interestType: string;
  baseRate: string;
  spreadBps: number;
  effectiveRate: number;
  processingFeePercent: number;
  status: string;
  createdAt: string;
  updatedAt: string;
}

type ProductCategory = string;
type ProductStatus = string;

// Mock data for demonstration
const mockProducts: ProductListItem[] = [
  {
    id: '1',
    productCode: 'TL-CORP-001',
    productName: 'Corporate Term Loan',
    category: 'TERM_LOAN',
    subCategory: 'CORPORATE',
    minAmount: 10000000,
    maxAmount: 5000000000,
    minTenureMonths: 12,
    maxTenureMonths: 120,
    interestType: 'FLOATING',
    baseRate: 'SMFC_BR',
    spreadBps: 200,
    effectiveRate: 12.5,
    processingFeePercent: 1.0,
    status: 'ACTIVE',
    createdAt: '2025-01-01',
    updatedAt: '2025-01-01',
  },
  {
    id: '2',
    productCode: 'WC-SME-001',
    productName: 'SME Working Capital',
    category: 'WORKING_CAPITAL',
    subCategory: 'SME',
    minAmount: 5000000,
    maxAmount: 500000000,
    minTenureMonths: 6,
    maxTenureMonths: 36,
    interestType: 'FLOATING',
    baseRate: 'SMFC_BR',
    spreadBps: 300,
    effectiveRate: 13.5,
    processingFeePercent: 1.5,
    status: 'ACTIVE',
    createdAt: '2025-01-02',
    updatedAt: '2025-01-02',
  },
  {
    id: '3',
    productCode: 'LAP-RES-001',
    productName: 'Loan Against Property - Residential',
    category: 'LAP',
    subCategory: 'RESIDENTIAL',
    minAmount: 2500000,
    maxAmount: 100000000,
    minTenureMonths: 24,
    maxTenureMonths: 180,
    interestType: 'FIXED',
    baseRate: 'FIXED',
    spreadBps: 0,
    effectiveRate: 14.0,
    processingFeePercent: 1.0,
    status: 'ACTIVE',
    createdAt: '2025-01-03',
    updatedAt: '2025-01-03',
  },
  {
    id: '4',
    productCode: 'PF-INFRA-001',
    productName: 'Infrastructure Project Finance',
    category: 'PROJECT_FINANCE',
    subCategory: 'INFRASTRUCTURE',
    minAmount: 500000000,
    maxAmount: 50000000000,
    minTenureMonths: 60,
    maxTenureMonths: 240,
    interestType: 'FLOATING',
    baseRate: 'SMFC_BR',
    spreadBps: 175,
    effectiveRate: 12.25,
    processingFeePercent: 0.5,
    status: 'ACTIVE',
    createdAt: '2025-01-04',
    updatedAt: '2025-01-04',
  },
];

const categoryLabels: Record<ProductCategory, string> = {
  TERM_LOAN: 'Term Loan',
  WORKING_CAPITAL: 'Working Capital',
  PROJECT_FINANCE: 'Project Finance',
  LAP: 'Loan Against Property',
  EQUIPMENT_FINANCE: 'Equipment Finance',
  BILL_DISCOUNTING: 'Bill Discounting',
};

export default function ProductList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const filteredProducts = mockProducts.filter((product) => {
    const matchesSearch =
      product.productName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      product.productCode.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = categoryFilter === 'ALL' || product.category === categoryFilter;
    const matchesStatus = statusFilter === 'ALL' || product.status === statusFilter;
    return matchesSearch && matchesCategory && matchesStatus;
  });

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

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Products</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockProducts.length}</div>
            <p className="text-xs text-muted-foreground">Across all categories</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Products</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {mockProducts.filter((p) => p.status === 'ACTIVE').length}
            </div>
            <p className="text-xs text-muted-foreground">Available for booking</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Categories</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {new Set(mockProducts.map((p) => p.category)).size}
            </div>
            <p className="text-xs text-muted-foreground">Product categories</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(
                mockProducts.reduce((sum, p) => sum + p.effectiveRate, 0) / mockProducts.length
              ).toFixed(2)}
              %
            </div>
            <p className="text-xs text-muted-foreground">Average effective rate</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
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
                <SelectTrigger className="w-[180px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Categories</SelectItem>
                  <SelectItem value="TERM_LOAN">Term Loan</SelectItem>
                  <SelectItem value="WORKING_CAPITAL">Working Capital</SelectItem>
                  <SelectItem value="PROJECT_FINANCE">Project Finance</SelectItem>
                  <SelectItem value="LAP">Loan Against Property</SelectItem>
                  <SelectItem value="EQUIPMENT_FINANCE">Equipment Finance</SelectItem>
                  <SelectItem value="BILL_DISCOUNTING">Bill Discounting</SelectItem>
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
                  <SelectItem value="DISCONTINUED">Discontinued</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Products Table */}
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
                <TableHead className="text-right">Effective Rate</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredProducts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                    No products found matching your criteria
                  </TableCell>
                </TableRow>
              ) : (
                filteredProducts.map((product) => (
                  <TableRow
                    key={product.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => navigate(`/admin/lending/products/${product.id}`)}
                  >
                    <TableCell className="font-mono text-sm">{product.productCode}</TableCell>
                    <TableCell className="font-medium">{product.productName}</TableCell>
                    <TableCell>
                      <span className="inline-flex items-center rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700">
                        {categoryLabels[product.category]}
                      </span>
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
                    <TableCell className="text-right">
                      <PercentageDisplay value={product.effectiveRate} />
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={product.status} type={"application" as any} />
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
