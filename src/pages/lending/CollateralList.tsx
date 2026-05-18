import {
  Building,
  Plus,
  Search,
  Filter,
  Download,
  Eye,
  Edit,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Clock,
} from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
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
import { formatCurrency, formatDate } from '@/lib/utils';

// Collateral data loads from the BE collateral endpoint once wired
// (/lending/collaterals — TBD). Until then the list starts empty so the
// page doesn't surface fabricated security values.
const collateralSummary = {
  total_count: 0,
  total_value: 0,
  total_net_value: 0,
  by_category: {
    PRIMARY: { count: 0, value: 0 },
    COLLATERAL: { count: 0, value: 0 },
    GUARANTEE: { count: 0, value: 0 },
  } as Record<string, { count: number; value: number }>,
  pending_valuation: 0,
};

const collaterals: {
  id: string;
  security_code: string;
  loan_account: string;
  entity: string;
  category: string;
  type: string;
  description: string;
  acceptable_value: number;
  margin: number;
  net_value: number;
  market_value: number | null;
  valuation_date: string | null;
  next_valuation: string | null;
  status: string;
  charge_created: boolean;
}[] = [];

const getCategoryBadge = (category: string) => {
  const variants: Record<string, 'default' | 'secondary' | 'outline'> = {
    PRIMARY: 'default',
    COLLATERAL: 'secondary',
    GUARANTEE: 'outline',
  };
  return <Badge variant={variants[category] || 'default'}>{category}</Badge>;
};

const getStatusBadge = (status: string, chargeCreated: boolean) => {
  if (status === 'RELEASED') {
    return <Badge variant="secondary">Released</Badge>;
  }
  if (status === 'SUBSTITUTED') {
    return <Badge variant="outline">Substituted</Badge>;
  }
  if (!chargeCreated) {
    return (
      <Badge variant="destructive" className="flex items-center gap-1">
        <Clock className="h-3 w-3" />
        Pending Charge
      </Badge>
    );
  }
  return (
    <Badge variant="default" className="flex items-center gap-1 bg-green-600">
      <CheckCircle className="h-3 w-3" />
      Active
    </Badge>
  );
};

export default function CollateralList() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  const filteredCollaterals = collaterals.filter((c) => {
    const matchesSearch =
      c.security_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.entity.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || c.category === categoryFilter;
    const matchesStatus = statusFilter === 'all' || c.status === statusFilter;
    return matchesSearch && matchesCategory && matchesStatus;
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Collateral Management"
        subtitle="Manage securities and collaterals"
        actions={
          <div className="flex gap-2">
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
            <Button onClick={() => navigate('/admin/lending/collaterals/create')}>
              <Plus className="mr-2 h-4 w-4" />
              Add Collateral
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Securities
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{collateralSummary.total_count}</div>
            <p className="text-xs text-muted-foreground">
              Value: {formatCurrency(collateralSummary.total_value)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Net Realizable Value
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {formatCurrency(collateralSummary.total_net_value)}
            </div>
            <p className="text-xs text-muted-foreground">After margin deduction</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Primary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{collateralSummary.by_category.PRIMARY.count}</div>
            <p className="text-xs text-muted-foreground">
              {formatCurrency(collateralSummary.by_category.PRIMARY.value)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Pending Valuation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <span className="text-3xl font-bold text-orange-500">
                {collateralSummary.pending_valuation}
              </span>
              <AlertTriangle className="h-5 w-5 text-orange-500" />
            </div>
            <p className="text-xs text-muted-foreground">Due within 30 days</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4">
            <div className="relative min-w-[200px] flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search by code, entity, or description..."
                className="pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="PRIMARY">Primary</SelectItem>
                <SelectItem value="COLLATERAL">Collateral</SelectItem>
                <SelectItem value="GUARANTEE">Guarantee</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="ACTIVE">Active</SelectItem>
                <SelectItem value="RELEASED">Released</SelectItem>
                <SelectItem value="SUBSTITUTED">Substituted</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Collateral Table */}
      <Card>
        <CardHeader>
          <CardTitle>Securities List</CardTitle>
          <CardDescription>{filteredCollaterals.length} records found</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Security Code</TableHead>
                <TableHead>Entity / Loan</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Description</TableHead>
                <TableHead className="text-right">Value / Net</TableHead>
                <TableHead>Valuation</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredCollaterals.map((collateral) => (
                <TableRow key={collateral.id}>
                  <TableCell className="font-mono text-sm">{collateral.security_code}</TableCell>
                  <TableCell>
                    <div className="font-medium">{collateral.entity}</div>
                    <div className="text-xs text-muted-foreground">{collateral.loan_account}</div>
                  </TableCell>
                  <TableCell>{getCategoryBadge(collateral.category)}</TableCell>
                  <TableCell>
                    <div className="max-w-[200px] truncate" title={collateral.description}>
                      {collateral.description}
                    </div>
                    <div className="text-xs text-muted-foreground">{collateral.type}</div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="font-medium">{formatCurrency(collateral.acceptable_value)}</div>
                    <div className="text-xs text-muted-foreground">
                      Net: {formatCurrency(collateral.net_value)}
                    </div>
                  </TableCell>
                  <TableCell>
                    {collateral.valuation_date ? (
                      <div>
                        <div className="text-sm">{formatDate(collateral.valuation_date)}</div>
                        {collateral.next_valuation && (
                          <div className="text-xs text-muted-foreground">
                            Next: {formatDate(collateral.next_valuation)}
                          </div>
                        )}
                      </div>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {getStatusBadge(collateral.status, collateral.charge_created)}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          ...
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => navigate(`/admin/lending/collaterals/${collateral.id}`)}
                        >
                          <Eye className="mr-2 h-4 w-4" />
                          View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() =>
                            navigate(`/admin/lending/collaterals/${collateral.id}/valuation`)
                          }
                        >
                          <RefreshCw className="mr-2 h-4 w-4" />
                          Update Valuation
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() =>
                            navigate(`/admin/lending/collaterals/${collateral.id}/release`)
                          }
                        >
                          <Edit className="mr-2 h-4 w-4" />
                          Release
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
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
