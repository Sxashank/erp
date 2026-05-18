import {
  Receipt,
  Plus,
  Search,
  Download,
  Eye,
  RotateCcw,
  CheckCircle,
  Clock,
  XCircle,
  Upload,
  Filter,
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

// Legacy root-level receipt list. Canonical wired view lives at
// /pages/lending/lms/ReceiptList.tsx and consumes /lending/receipts via
// useReceipts. This page renders empty until migrated to the same hook.
const receiptSummary = {
  total_receipts: 0,
  total_amount: 0,
  today_receipts: 0,
  today_amount: 0,
  pending_allocation: 0,
  pending_amount: 0,
};

interface ReceiptRow {
  id: string;
  receipt_number: string;
  loan_account: string;
  entity: string;
  receipt_date: string;
  value_date: string;
  amount: number;
  receipt_type: string;
  receipt_mode: string;
  instrument_number: string | null;
  status: string;
  allocated_amount: number;
  unallocated_amount: number;
}

const receipts: ReceiptRow[] = [];

const getStatusBadge = (status: string) => {
  const variants: Record<
    string,
    { variant: 'default' | 'secondary' | 'outline' | 'destructive'; icon: React.ReactNode }
  > = {
    ALLOCATED: { variant: 'default', icon: <CheckCircle className="h-3 w-3" /> },
    PARTIAL: { variant: 'secondary', icon: <Clock className="h-3 w-3" /> },
    PENDING: { variant: 'outline', icon: <Clock className="h-3 w-3" /> },
    REVERSED: { variant: 'destructive', icon: <XCircle className="h-3 w-3" /> },
  };
  const config = variants[status] || { variant: 'outline', icon: null };
  return (
    <Badge variant={config.variant} className="flex items-center gap-1">
      {config.icon}
      {status}
    </Badge>
  );
};

const getTypeBadge = (type: string) => {
  const labels: Record<string, string> = {
    REGULAR: 'Regular',
    PREPAYMENT: 'Prepayment',
    PARTIAL_PREPAYMENT: 'Partial Prepay',
    FORECLOSURE: 'Foreclosure',
    BOUNCE_RECOVERY: 'Bounce Recovery',
  };
  return <Badge variant="outline">{labels[type] || type}</Badge>;
};

export default function ReceiptList() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [dateRange, setDateRange] = useState('today');

  const filteredReceipts = receipts.filter((r) => {
    const matchesSearch =
      r.receipt_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.entity.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.loan_account.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || r.status === statusFilter;
    const matchesType = typeFilter === 'all' || r.receipt_type === typeFilter;
    return matchesSearch && matchesStatus && matchesType;
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Receipts"
        subtitle="Manage loan payment receipts"
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => navigate('/admin/lending/receipts/bulk-upload')}
            >
              <Upload className="mr-2 h-4 w-4" />
              Bulk Upload
            </Button>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
            <Button onClick={() => navigate('/admin/lending/receipts/create')}>
              <Plus className="mr-2 h-4 w-4" />
              New Receipt
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Receipts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{receiptSummary.total_receipts}</div>
            <p className="text-xs text-muted-foreground">
              {formatCurrency(receiptSummary.total_amount)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Today's Collection
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{receiptSummary.today_receipts}</div>
            <p className="text-xs text-muted-foreground">
              {formatCurrency(receiptSummary.today_amount)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Pending Allocation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-500">
              {receiptSummary.pending_allocation}
            </div>
            <p className="text-xs text-muted-foreground">
              {formatCurrency(receiptSummary.pending_amount)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Avg. Receipt Value
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {formatCurrency(receiptSummary.total_amount / receiptSummary.total_receipts)}
            </div>
            <p className="text-xs text-muted-foreground">Per transaction</p>
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
                placeholder="Search by receipt number, entity, or loan account..."
                className="pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="ALLOCATED">Allocated</SelectItem>
                <SelectItem value="PARTIAL">Partial</SelectItem>
                <SelectItem value="PENDING">Pending</SelectItem>
                <SelectItem value="REVERSED">Reversed</SelectItem>
              </SelectContent>
            </Select>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="REGULAR">Regular</SelectItem>
                <SelectItem value="PREPAYMENT">Prepayment</SelectItem>
                <SelectItem value="FORECLOSURE">Foreclosure</SelectItem>
                <SelectItem value="BOUNCE_RECOVERY">Bounce Recovery</SelectItem>
              </SelectContent>
            </Select>
            <Select value={dateRange} onValueChange={setDateRange}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Date Range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="today">Today</SelectItem>
                <SelectItem value="week">This Week</SelectItem>
                <SelectItem value="month">This Month</SelectItem>
                <SelectItem value="quarter">This Quarter</SelectItem>
                <SelectItem value="all">All Time</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Receipt Table */}
      <Card>
        <CardHeader>
          <CardTitle>Receipt List</CardTitle>
          <CardDescription>{filteredReceipts.length} records found</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Receipt No.</TableHead>
                <TableHead>Entity / Loan</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Mode</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead className="text-right">Allocated</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredReceipts.map((receipt) => (
                <TableRow key={receipt.id}>
                  <TableCell className="font-mono text-sm">{receipt.receipt_number}</TableCell>
                  <TableCell>
                    <div className="font-medium">{receipt.entity}</div>
                    <div className="text-xs text-muted-foreground">{receipt.loan_account}</div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">{formatDate(receipt.receipt_date)}</div>
                    {receipt.value_date !== receipt.receipt_date && (
                      <div className="text-xs text-muted-foreground">
                        Value: {formatDate(receipt.value_date)}
                      </div>
                    )}
                  </TableCell>
                  <TableCell>{getTypeBadge(receipt.receipt_type)}</TableCell>
                  <TableCell>
                    <div className="text-sm">{receipt.receipt_mode}</div>
                    {receipt.instrument_number && (
                      <div className="font-mono text-xs text-muted-foreground">
                        {receipt.instrument_number}
                      </div>
                    )}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(receipt.amount)}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="font-medium">{formatCurrency(receipt.allocated_amount)}</div>
                    {receipt.unallocated_amount > 0 && (
                      <div className="text-xs text-orange-500">
                        Unalloc: {formatCurrency(receipt.unallocated_amount)}
                      </div>
                    )}
                  </TableCell>
                  <TableCell>{getStatusBadge(receipt.status)}</TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          ...
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => navigate(`/admin/lending/receipts/${receipt.id}`)}
                        >
                          <Eye className="mr-2 h-4 w-4" />
                          View Details
                        </DropdownMenuItem>
                        {receipt.status === 'PENDING' || receipt.status === 'PARTIAL' ? (
                          <DropdownMenuItem
                            onClick={() =>
                              navigate(`/admin/lending/receipts/${receipt.id}/allocate`)
                            }
                          >
                            <Receipt className="mr-2 h-4 w-4" />
                            Allocate
                          </DropdownMenuItem>
                        ) : null}
                        {receipt.status !== 'REVERSED' && (
                          <DropdownMenuItem
                            onClick={() =>
                              navigate(`/admin/lending/receipts/${receipt.id}/reverse`)
                            }
                          >
                            <RotateCcw className="mr-2 h-4 w-4" />
                            Reverse
                          </DropdownMenuItem>
                        )}
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
