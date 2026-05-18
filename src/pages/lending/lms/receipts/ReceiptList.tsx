import { Plus, Search, Filter, MoreHorizontal, Eye, RotateCcw, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
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
  useReceipts,
  type ReceiptListItem,
  type ReceiptStatusValue,
  type ReceiptFilters,
} from '@/hooks/lending/useReceipts';
import { logger } from '@/lib/logger';

const modeColors: Record<string, string> = {
  CASH: 'bg-green-100 text-green-700',
  CHEQUE: 'bg-blue-100 text-blue-700',
  NEFT: 'bg-purple-100 text-purple-700',
  RTGS: 'bg-indigo-100 text-indigo-700',
  IMPS: 'bg-pink-100 text-pink-700',
  UPI: 'bg-orange-100 text-orange-700',
  DD: 'bg-gray-100 text-gray-700',
  NACH: 'bg-teal-100 text-teal-700',
  AUTO_DEBIT: 'bg-cyan-100 text-cyan-700',
  ADJUSTMENT: 'bg-slate-100 text-slate-700',
};

const statusColors: Record<ReceiptStatusValue, string> = {
  PENDING: 'bg-gray-100 text-gray-700',
  ALLOCATED: 'bg-green-100 text-green-700',
  REVERSED: 'bg-red-100 text-red-700',
  BOUNCED: 'bg-orange-100 text-orange-700',
};

export default function ReceiptList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [modeFilter, setModeFilter] = useState<string>('ALL');

  const filters: ReceiptFilters = {
    pageSize: 100,
    ...(searchQuery && { search: searchQuery }),
    ...(statusFilter !== 'ALL' && {
      status: statusFilter as ReceiptStatusValue,
    }),
  };
  const { data, isLoading, isError, error, refetch } = useReceipts(filters);

  // Mode filter is client-side — the BE doesn't currently filter by mode.
  const allReceipts: ReceiptListItem[] = data?.items ?? [];
  const receipts =
    modeFilter === 'ALL' ? allReceipts : allReceipts.filter((r) => r.receiptMode === modeFilter);

  // Wire amounts are strings (Decimal precision); coerce once for display-only sums.
  const totalCollected = receipts.reduce((sum, r) => sum + Number(r.receiptAmount), 0);
  const totalAllocated = receipts.reduce((sum, r) => sum + Number(r.allocatedAmount), 0);
  const totalUnallocated = receipts.reduce((sum, r) => sum + Number(r.unallocatedAmount), 0);

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
            <div className="text-2xl font-bold">{data?.total ?? receipts.length}</div>
            <p className="text-xs text-muted-foreground">All time</p>
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
            <AmountDisplay
              amount={totalAllocated}
              abbreviated
              className="text-2xl font-bold text-green-600"
            />
            <p className="text-xs text-muted-foreground">Applied to dues</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Unallocated</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={totalUnallocated}
              abbreviated
              className="text-2xl font-bold text-yellow-600"
            />
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
                  <SelectItem value="PENDING">Pending</SelectItem>
                  <SelectItem value="ALLOCATED">Allocated</SelectItem>
                  <SelectItem value="REVERSED">Reversed</SelectItem>
                  <SelectItem value="BOUNCED">Bounced</SelectItem>
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
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8 text-center text-muted-foreground">
                    <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />
                    Loading receipts...
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8">
                    <ErrorState
                      title="Could not load receipts"
                      error={error}
                      onRetry={() => refetch()}
                    />
                  </TableCell>
                </TableRow>
              ) : receipts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8 text-center text-muted-foreground">
                    No receipts found
                  </TableCell>
                </TableRow>
              ) : (
                receipts.map((receipt) => (
                  <TableRow
                    key={receipt.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => navigate(`/admin/lending/receipts/${receipt.id}`)}
                  >
                    <TableCell className="font-mono text-sm">{receipt.receiptNumber}</TableCell>
                    <TableCell className="font-mono text-sm">
                      {receipt.loanAccountNumber ?? '—'}
                    </TableCell>
                    <TableCell>{receipt.entityName ?? '—'}</TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={receipt.receiptAmount} />
                      {Number(receipt.unallocatedAmount) > 0 && (
                        <div className="text-xs text-yellow-600">
                          Unalloc: <AmountDisplay amount={receipt.unallocatedAmount} />
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      <DateDisplay date={receipt.receiptDate} />
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={modeColors[receipt.receiptMode]}>
                        {receipt.receiptMode}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{receipt.receiptType.replace('_', ' ')}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={statusColors[receipt.status]}>
                        {receipt.status}
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
