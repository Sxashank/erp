import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
import { formatCurrency, formatDate } from '@/lib/utils';

// Mock data
const receiptSummary = {
  total_receipts: 1245,
  total_amount: 125000000,
  today_receipts: 45,
  today_amount: 5600000,
  pending_allocation: 23,
  pending_amount: 2300000,
};

const receipts = [
  {
    id: '1',
    receipt_number: 'RCP/2025/00245',
    loan_account: 'SMFC/LA/2024/00125',
    entity: 'ABC Trading Co.',
    receipt_date: '2025-01-15',
    value_date: '2025-01-15',
    amount: 450000,
    receipt_type: 'REGULAR',
    receipt_mode: 'NEFT',
    instrument_number: 'UTR123456789',
    status: 'ALLOCATED',
    allocated_amount: 450000,
    unallocated_amount: 0,
  },
  {
    id: '2',
    receipt_number: 'RCP/2025/00244',
    loan_account: 'SMFC/LA/2024/00089',
    entity: 'XYZ Industries',
    receipt_date: '2025-01-15',
    value_date: '2025-01-15',
    amount: 750000,
    receipt_type: 'PREPAYMENT',
    receipt_mode: 'RTGS',
    instrument_number: 'UTR987654321',
    status: 'PARTIAL',
    allocated_amount: 500000,
    unallocated_amount: 250000,
  },
  {
    id: '3',
    receipt_number: 'RCP/2025/00243',
    loan_account: 'SMFC/LA/2024/00156',
    entity: 'Metro Logistics',
    receipt_date: '2025-01-14',
    value_date: '2025-01-14',
    amount: 320000,
    receipt_type: 'REGULAR',
    receipt_mode: 'CHEQUE',
    instrument_number: 'CHQ456789',
    status: 'PENDING',
    allocated_amount: 0,
    unallocated_amount: 320000,
  },
  {
    id: '4',
    receipt_number: 'RCP/2025/00242',
    loan_account: 'SMFC/LA/2024/00178',
    entity: 'Eastern Corp',
    receipt_date: '2025-01-14',
    value_date: '2025-01-14',
    amount: 150000,
    receipt_type: 'BOUNCE_RECOVERY',
    receipt_mode: 'CASH',
    instrument_number: null,
    status: 'ALLOCATED',
    allocated_amount: 150000,
    unallocated_amount: 0,
  },
  {
    id: '5',
    receipt_number: 'RCP/2025/00241',
    loan_account: 'SMFC/LA/2024/00125',
    entity: 'ABC Trading Co.',
    receipt_date: '2025-01-13',
    value_date: '2025-01-13',
    amount: 450000,
    receipt_type: 'REGULAR',
    receipt_mode: 'NACH',
    instrument_number: 'NACH001234',
    status: 'REVERSED',
    allocated_amount: 0,
    unallocated_amount: 0,
  },
];

const getStatusBadge = (status: string) => {
  const variants: Record<string, { variant: 'default' | 'secondary' | 'outline' | 'destructive'; icon: React.ReactNode }> = {
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
            <Button variant="outline" onClick={() => navigate('/lending/receipts/bulk-upload')}>
              <Upload className="h-4 w-4 mr-2" />
              Bulk Upload
            </Button>
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button onClick={() => navigate('/lending/receipts/create')}>
              <Plus className="h-4 w-4 mr-2" />
              New Receipt
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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
            <div className="text-3xl font-bold text-green-600">
              {receiptSummary.today_receipts}
            </div>
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
          <div className="flex gap-4 flex-wrap">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
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
                      <div className="text-xs text-muted-foreground font-mono">
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
                          onClick={() => navigate(`/lending/receipts/${receipt.id}`)}
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        {receipt.status === 'PENDING' || receipt.status === 'PARTIAL' ? (
                          <DropdownMenuItem
                            onClick={() => navigate(`/lending/receipts/${receipt.id}/allocate`)}
                          >
                            <Receipt className="h-4 w-4 mr-2" />
                            Allocate
                          </DropdownMenuItem>
                        ) : null}
                        {receipt.status !== 'REVERSED' && (
                          <DropdownMenuItem
                            onClick={() => navigate(`/lending/receipts/${receipt.id}/reverse`)}
                          >
                            <RotateCcw className="h-4 w-4 mr-2" />
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
