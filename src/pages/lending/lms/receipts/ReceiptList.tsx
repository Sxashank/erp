import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Filter, MoreHorizontal, Eye, RotateCcw } from 'lucide-react';
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
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';

import { logger } from '@/lib/logger';
interface Receipt {
  id: string;
  receiptNumber: string;
  loanAccountNumber: string;
  entityName: string;
  amount: number;
  receiptDate: string;
  valueDate: string;
  mode: 'CASH' | 'CHEQUE' | 'NEFT' | 'RTGS' | 'IMPS' | 'UPI' | 'DD';
  instrumentNumber: string | null;
  type: 'EMI' | 'PART_PAYMENT' | 'PREPAYMENT' | 'PENAL' | 'CHARGES' | 'PROCESSING_FEE';
  status: 'ALLOCATED' | 'PARTIALLY_ALLOCATED' | 'UNALLOCATED' | 'REVERSED';
  allocatedAmount: number;
  unallocatedAmount: number;
  remarks: string | null;
}

// Mock data
const mockReceipts: Receipt[] = [
  {
    id: '1',
    receiptNumber: 'RCP/2025/00001',
    loanAccountNumber: 'SMFC/TL/DEL/2025/L00001',
    entityName: 'ABC Industries Private Limited',
    amount: 2500000,
    receiptDate: '2025-01-12',
    valueDate: '2025-01-12',
    mode: 'NEFT',
    instrumentNumber: 'NEFT123456789',
    type: 'PROCESSING_FEE',
    status: 'ALLOCATED',
    allocatedAmount: 2500000,
    unallocatedAmount: 0,
    remarks: 'Processing fee for sanction',
  },
  {
    id: '2',
    receiptNumber: 'RCP/2025/00002',
    loanAccountNumber: 'SMFC/WC/MUM/2024/L00089',
    entityName: 'XYZ Traders LLP',
    amount: 2250000,
    receiptDate: '2025-01-20',
    valueDate: '2025-01-20',
    mode: 'RTGS',
    instrumentNumber: 'RTGS987654321',
    type: 'EMI',
    status: 'ALLOCATED',
    allocatedAmount: 2250000,
    unallocatedAmount: 0,
    remarks: null,
  },
  {
    id: '3',
    receiptNumber: 'RCP/2025/00003',
    loanAccountNumber: 'SMFC/LAP/BLR/2024/L00045',
    entityName: 'Tech Solutions India Pvt Ltd',
    amount: 5000000,
    receiptDate: '2025-01-22',
    valueDate: '2025-01-22',
    mode: 'NEFT',
    instrumentNumber: 'NEFT567891234',
    type: 'PART_PAYMENT',
    status: 'PARTIALLY_ALLOCATED',
    allocatedAmount: 3500000,
    unallocatedAmount: 1500000,
    remarks: 'Partial payment towards outstanding',
  },
  {
    id: '4',
    receiptNumber: 'RCP/2025/00004',
    loanAccountNumber: 'SMFC/TL/CHN/2023/L00034',
    entityName: 'Southern Motors Corp',
    amount: 1000000,
    receiptDate: '2025-01-25',
    valueDate: '2025-01-25',
    mode: 'CHEQUE',
    instrumentNumber: 'CHQ456789',
    type: 'EMI',
    status: 'UNALLOCATED',
    allocatedAmount: 0,
    unallocatedAmount: 1000000,
    remarks: 'On account payment',
  },
];

const modeColors: Record<string, string> = {
  CASH: 'bg-green-100 text-green-700',
  CHEQUE: 'bg-blue-100 text-blue-700',
  NEFT: 'bg-purple-100 text-purple-700',
  RTGS: 'bg-indigo-100 text-indigo-700',
  IMPS: 'bg-pink-100 text-pink-700',
  UPI: 'bg-orange-100 text-orange-700',
  DD: 'bg-gray-100 text-gray-700',
};

const statusColors: Record<string, string> = {
  ALLOCATED: 'bg-green-100 text-green-700',
  PARTIALLY_ALLOCATED: 'bg-yellow-100 text-yellow-700',
  UNALLOCATED: 'bg-gray-100 text-gray-700',
  REVERSED: 'bg-red-100 text-red-700',
};

export default function ReceiptList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [modeFilter, setModeFilter] = useState<string>('ALL');

  const filteredReceipts = mockReceipts.filter((receipt) => {
    const matchesSearch =
      receipt.receiptNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
      receipt.entityName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      receipt.loanAccountNumber.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || receipt.status === statusFilter;
    const matchesMode = modeFilter === 'ALL' || receipt.mode === modeFilter;
    return matchesSearch && matchesStatus && matchesMode;
  });

  const totalCollected = mockReceipts.reduce((sum, r) => sum + r.amount, 0);
  const totalAllocated = mockReceipts.reduce((sum, r) => sum + r.allocatedAmount, 0);
  const totalUnallocated = mockReceipts.reduce((sum, r) => sum + r.unallocatedAmount, 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Receipts"
        subtitle="Record and manage loan payment receipts"
        actions={
          <Button onClick={() => navigate('/admin/lending/receipts/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Record Receipt
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Receipts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockReceipts.length}</div>
            <p className="text-xs text-muted-foreground">This month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Collected</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalCollected} abbreviated className="text-2xl font-bold" />
            <p className="text-xs text-muted-foreground">Gross collection</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Allocated</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalAllocated} abbreviated className="text-2xl font-bold text-green-600" />
            <p className="text-xs text-muted-foreground">Applied to dues</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Unallocated</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalUnallocated} abbreviated className="text-2xl font-bold text-yellow-600" />
            <p className="text-xs text-muted-foreground">On account</p>
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
                placeholder="Search by receipt number, entity, or loan account..."
                className="pl-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[180px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Status</SelectItem>
                  <SelectItem value="ALLOCATED">Allocated</SelectItem>
                  <SelectItem value="PARTIALLY_ALLOCATED">Partially Allocated</SelectItem>
                  <SelectItem value="UNALLOCATED">Unallocated</SelectItem>
                  <SelectItem value="REVERSED">Reversed</SelectItem>
                </SelectContent>
              </Select>
              <Select value={modeFilter} onValueChange={setModeFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Mode" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Modes</SelectItem>
                  <SelectItem value="CASH">Cash</SelectItem>
                  <SelectItem value="CHEQUE">Cheque</SelectItem>
                  <SelectItem value="NEFT">NEFT</SelectItem>
                  <SelectItem value="RTGS">RTGS</SelectItem>
                  <SelectItem value="IMPS">IMPS</SelectItem>
                  <SelectItem value="UPI">UPI</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Receipts Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Receipt #</TableHead>
                <TableHead>Loan Account</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Mode</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredReceipts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                    No receipts found matching your criteria
                  </TableCell>
                </TableRow>
              ) : (
                filteredReceipts.map((receipt) => (
                  <TableRow
                    key={receipt.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => navigate(`/admin/lending/receipts/${receipt.id}`)}
                  >
                    <TableCell className="font-mono text-sm">{receipt.receiptNumber}</TableCell>
                    <TableCell className="font-mono text-sm">
                      {receipt.loanAccountNumber}
                    </TableCell>
                    <TableCell>{receipt.entityName}</TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={receipt.amount} />
                      {receipt.unallocatedAmount > 0 && (
                        <div className="text-xs text-yellow-600">
                          Unalloc: <AmountDisplay amount={receipt.unallocatedAmount} />
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      <DateDisplay date={receipt.receiptDate} />
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={modeColors[receipt.mode]}>
                        {receipt.mode}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{receipt.type.replace('_', ' ')}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={statusColors[receipt.status]}>
                        {receipt.status.replace('_', ' ')}
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
                              navigate(`/admin/lending/receipts/${receipt.id}`);
                            }}
                          >
                            <Eye className="mr-2 h-4 w-4" />
                            View Details
                          </DropdownMenuItem>
                          {receipt.status !== 'REVERSED' && (
                            <>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                onClick={(e) => {
                                  e.stopPropagation();
                                  logger.debug('Reverse receipt:', receipt.id);
                                }}
                                className="text-destructive"
                              >
                                <RotateCcw className="mr-2 h-4 w-4" />
                                Reverse Receipt
                              </DropdownMenuItem>
                            </>
                          )}
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
