import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Progress } from '@/components/ui/progress';
import { formatCurrency, formatDate } from '@/lib/utils';

// Mock data
const collateralSummary = {
  total_count: 156,
  total_value: 25000000000,
  total_net_value: 18750000000,
  by_category: {
    PRIMARY: { count: 85, value: 15000000000 },
    COLLATERAL: { count: 55, value: 8000000000 },
    GUARANTEE: { count: 16, value: 2000000000 },
  },
  pending_valuation: 12,
};

const collaterals = [
  {
    id: '1',
    security_code: 'SEC/2024/00125',
    loan_account: 'SMFC/LA/2024/00089',
    entity: 'ABC Industries',
    category: 'PRIMARY',
    type: 'IMMOVABLE_PROPERTY',
    description: 'Commercial Building at MG Road, Bangalore',
    acceptable_value: 50000000,
    margin: 25,
    net_value: 37500000,
    market_value: 55000000,
    valuation_date: '2024-06-15',
    next_valuation: '2025-06-15',
    status: 'ACTIVE',
    charge_created: true,
  },
  {
    id: '2',
    security_code: 'SEC/2024/00126',
    loan_account: 'SMFC/LA/2024/00090',
    entity: 'XYZ Trading',
    category: 'COLLATERAL',
    type: 'PLANT_MACHINERY',
    description: 'CNC Machines - 5 Units',
    acceptable_value: 15000000,
    margin: 30,
    net_value: 10500000,
    market_value: 18000000,
    valuation_date: '2024-08-20',
    next_valuation: '2025-02-20',
    status: 'ACTIVE',
    charge_created: true,
  },
  {
    id: '3',
    security_code: 'SEC/2024/00127',
    loan_account: 'SMFC/LA/2024/00091',
    entity: 'Metro Logistics',
    category: 'PRIMARY',
    type: 'IMMOVABLE_PROPERTY',
    description: 'Warehouse at Electronic City',
    acceptable_value: 80000000,
    margin: 25,
    net_value: 60000000,
    market_value: 90000000,
    valuation_date: '2024-03-10',
    next_valuation: '2025-03-10',
    status: 'ACTIVE',
    charge_created: false,
  },
  {
    id: '4',
    security_code: 'SEC/2024/00128',
    loan_account: 'SMFC/LA/2024/00092',
    entity: 'Eastern Corp',
    category: 'GUARANTEE',
    type: 'PERSONAL_GUARANTEE',
    description: 'Personal Guarantee - Mr. John Doe',
    acceptable_value: 25000000,
    margin: 0,
    net_value: 25000000,
    market_value: null,
    valuation_date: null,
    next_valuation: null,
    status: 'ACTIVE',
    charge_created: true,
  },
];

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
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button onClick={() => navigate('/lending/collaterals/create')}>
              <Plus className="h-4 w-4 mr-2" />
              Add Collateral
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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
            <div className="text-3xl font-bold">
              {collateralSummary.by_category.PRIMARY.count}
            </div>
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
          <div className="flex gap-4 flex-wrap">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
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
                    <div className="font-medium">
                      {formatCurrency(collateral.acceptable_value)}
                    </div>
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
                          onClick={() => navigate(`/lending/collaterals/${collateral.id}`)}
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => navigate(`/lending/collaterals/${collateral.id}/valuation`)}
                        >
                          <RefreshCw className="h-4 w-4 mr-2" />
                          Update Valuation
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => navigate(`/lending/collaterals/${collateral.id}/release`)}
                        >
                          <Edit className="h-4 w-4 mr-2" />
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
