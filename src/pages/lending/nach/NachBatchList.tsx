/**
 * NACH Batch List Page
 * Displays all NACH batches with filtering and management options
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  Eye,
  FileText,
  Upload,
  Ban,
  Send,
  RefreshCw,
  Download,
  CheckCircle,
  XCircle,
  Clock,
} from 'lucide-react';
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
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';

import { logger } from '@/lib/logger';
// NACH Batch Status
type NachBatchStatus =
  | 'CREATED'
  | 'VALIDATED'
  | 'FILE_GENERATED'
  | 'SUBMITTED'
  | 'PROCESSING'
  | 'RESPONSE_RECEIVED'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED';

interface NachBatch {
  id: string;
  batchReference: string;
  batchDate: string;
  debitDate: string;
  provider: 'RAZORPAY' | 'CASHFREE' | 'NPCI_DIRECT';
  totalTransactions: number;
  totalAmount: number;
  successCount: number;
  failureCount: number;
  pendingCount: number;
  status: NachBatchStatus;
  fileGenerated: boolean;
  fileName?: string;
  submittedAt?: string;
  completedAt?: string;
  createdAt: string;
}

// Mock data
const mockBatches: NachBatch[] = [
  {
    id: '1',
    batchReference: 'NACH/2025/01/001',
    batchDate: '2025-01-10',
    debitDate: '2025-01-15',
    provider: 'RAZORPAY',
    totalTransactions: 245,
    totalAmount: 12500000,
    successCount: 230,
    failureCount: 15,
    pendingCount: 0,
    status: 'COMPLETED',
    fileGenerated: true,
    fileName: 'NACH_DEBIT_20250115_001.txt',
    submittedAt: '2025-01-14T10:30:00',
    completedAt: '2025-01-15T18:00:00',
    createdAt: '2025-01-10T09:00:00',
  },
  {
    id: '2',
    batchReference: 'NACH/2025/01/002',
    batchDate: '2025-01-12',
    debitDate: '2025-01-20',
    provider: 'RAZORPAY',
    totalTransactions: 312,
    totalAmount: 15750000,
    successCount: 0,
    failureCount: 0,
    pendingCount: 312,
    status: 'SUBMITTED',
    fileGenerated: true,
    fileName: 'NACH_DEBIT_20250120_001.txt',
    submittedAt: '2025-01-18T14:00:00',
    createdAt: '2025-01-12T11:30:00',
  },
  {
    id: '3',
    batchReference: 'NACH/2025/01/003',
    batchDate: '2025-01-13',
    debitDate: '2025-01-25',
    provider: 'CASHFREE',
    totalTransactions: 178,
    totalAmount: 8900000,
    successCount: 0,
    failureCount: 0,
    pendingCount: 178,
    status: 'FILE_GENERATED',
    fileGenerated: true,
    fileName: 'NACH_DEBIT_20250125_001.txt',
    createdAt: '2025-01-13T08:45:00',
  },
  {
    id: '4',
    batchReference: 'NACH/2025/01/004',
    batchDate: '2025-01-14',
    debitDate: '2025-01-28',
    provider: 'RAZORPAY',
    totalTransactions: 425,
    totalAmount: 21250000,
    successCount: 0,
    failureCount: 0,
    pendingCount: 425,
    status: 'CREATED',
    fileGenerated: false,
    createdAt: '2025-01-14T16:20:00',
  },
];

const statusConfig: Record<
  NachBatchStatus,
  { label: string; color: string; icon: React.ReactNode }
> = {
  CREATED: {
    label: 'Created',
    color: 'bg-slate-100 text-slate-700 border-slate-300',
    icon: <Clock className="h-3 w-3" />,
  },
  VALIDATED: {
    label: 'Validated',
    color: 'bg-blue-100 text-blue-700 border-blue-300',
    icon: <CheckCircle className="h-3 w-3" />,
  },
  FILE_GENERATED: {
    label: 'File Generated',
    color: 'bg-indigo-100 text-indigo-700 border-indigo-300',
    icon: <FileText className="h-3 w-3" />,
  },
  SUBMITTED: {
    label: 'Submitted',
    color: 'bg-purple-100 text-purple-700 border-purple-300',
    icon: <Send className="h-3 w-3" />,
  },
  PROCESSING: {
    label: 'Processing',
    color: 'bg-amber-100 text-amber-700 border-amber-300',
    icon: <RefreshCw className="h-3 w-3 animate-spin" />,
  },
  RESPONSE_RECEIVED: {
    label: 'Response Received',
    color: 'bg-cyan-100 text-cyan-700 border-cyan-300',
    icon: <Download className="h-3 w-3" />,
  },
  COMPLETED: {
    label: 'Completed',
    color: 'bg-green-100 text-green-700 border-green-300',
    icon: <CheckCircle className="h-3 w-3" />,
  },
  FAILED: {
    label: 'Failed',
    color: 'bg-red-100 text-red-700 border-red-300',
    icon: <XCircle className="h-3 w-3" />,
  },
  CANCELLED: {
    label: 'Cancelled',
    color: 'bg-gray-100 text-gray-600 border-gray-300',
    icon: <Ban className="h-3 w-3" />,
  },
};

const providerLabels: Record<string, { label: string; color: string }> = {
  RAZORPAY: { label: 'Razorpay', color: 'bg-blue-100 text-blue-700' },
  CASHFREE: { label: 'Cashfree', color: 'bg-green-100 text-green-700' },
  NPCI_DIRECT: { label: 'NPCI Direct', color: 'bg-purple-100 text-purple-700' },
};

export default function NachBatchList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [providerFilter, setProviderFilter] = useState<string>('ALL');

  const filteredBatches = mockBatches.filter((batch) => {
    const matchesSearch = batch.batchReference
      .toLowerCase()
      .includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || batch.status === statusFilter;
    const matchesProvider =
      providerFilter === 'ALL' || batch.provider === providerFilter;
    return matchesSearch && matchesStatus && matchesProvider;
  });

  // Calculate summary stats
  const totalBatches = mockBatches.length;
  const totalAmount = mockBatches.reduce((sum, b) => sum + b.totalAmount, 0);
  const totalSuccess = mockBatches.reduce((sum, b) => sum + b.successCount, 0);
  const totalFailed = mockBatches.reduce((sum, b) => sum + b.failureCount, 0);
  const totalTransactions = mockBatches.reduce(
    (sum, b) => sum + b.totalTransactions,
    0
  );
  const successRate =
    totalTransactions > 0
      ? ((totalSuccess / (totalSuccess + totalFailed)) * 100).toFixed(1)
      : 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="NACH Batches"
        subtitle="Manage NACH/Auto-debit batches for EMI collection"
        actions={
          <Button onClick={() => navigate('/admin/lending/nach/batches/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Generate Batch
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Batches</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalBatches}</div>
            <p className="text-xs text-muted-foreground">This month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Presented</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalAmount} abbreviated className="text-2xl font-bold" />
            <p className="text-xs text-muted-foreground">
              {totalTransactions} transactions
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Successful</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{totalSuccess}</div>
            <p className="text-xs text-muted-foreground">Debits completed</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Bounced</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{totalFailed}</div>
            <p className="text-xs text-muted-foreground">Failed debits</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{successRate}%</div>
            <p className="text-xs text-muted-foreground">Overall</p>
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
                placeholder="Search by batch reference..."
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
                  <SelectItem value="CREATED">Created</SelectItem>
                  <SelectItem value="VALIDATED">Validated</SelectItem>
                  <SelectItem value="FILE_GENERATED">File Generated</SelectItem>
                  <SelectItem value="SUBMITTED">Submitted</SelectItem>
                  <SelectItem value="PROCESSING">Processing</SelectItem>
                  <SelectItem value="RESPONSE_RECEIVED">Response Received</SelectItem>
                  <SelectItem value="COMPLETED">Completed</SelectItem>
                  <SelectItem value="FAILED">Failed</SelectItem>
                  <SelectItem value="CANCELLED">Cancelled</SelectItem>
                </SelectContent>
              </Select>
              <Select value={providerFilter} onValueChange={setProviderFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Provider" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Providers</SelectItem>
                  <SelectItem value="RAZORPAY">Razorpay</SelectItem>
                  <SelectItem value="CASHFREE">Cashfree</SelectItem>
                  <SelectItem value="NPCI_DIRECT">NPCI Direct</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Batches Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Batch Reference</TableHead>
                <TableHead>Debit Date</TableHead>
                <TableHead>Provider</TableHead>
                <TableHead className="text-right">Transactions</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead className="text-center">Success/Fail</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredBatches.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={8}
                    className="text-center py-8 text-muted-foreground"
                  >
                    No batches found matching your criteria
                  </TableCell>
                </TableRow>
              ) : (
                filteredBatches.map((batch) => {
                  const status = statusConfig[batch.status];
                  const provider = providerLabels[batch.provider];
                  return (
                    <TableRow
                      key={batch.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() =>
                        navigate(`/admin/lending/nach/batches/${batch.id}`)
                      }
                    >
                      <TableCell>
                        <div className="font-mono text-sm font-medium">
                          {batch.batchReference}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Created: <DateDisplay date={batch.createdAt} />
                        </div>
                      </TableCell>
                      <TableCell>
                        <DateDisplay date={batch.debitDate} />
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={provider.color}>
                          {provider.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {batch.totalTransactions}
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={batch.totalAmount} />
                      </TableCell>
                      <TableCell className="text-center">
                        {batch.status === 'COMPLETED' ||
                        batch.status === 'RESPONSE_RECEIVED' ? (
                          <div className="flex items-center justify-center gap-2">
                            <span className="text-green-600 font-medium">
                              {batch.successCount}
                            </span>
                            <span className="text-muted-foreground">/</span>
                            <span className="text-red-600 font-medium">
                              {batch.failureCount}
                            </span>
                          </div>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={`${status.color} border font-medium`}
                        >
                          <span className="mr-1">{status.icon}</span>
                          {status.label}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger
                            asChild
                            onClick={(e) => e.stopPropagation()}
                          >
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(
                                  `/admin/lending/nach/batches/${batch.id}`
                                );
                              }}
                            >
                              <Eye className="mr-2 h-4 w-4" />
                              View Details
                            </DropdownMenuItem>

                            {batch.status === 'CREATED' && (
                              <>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    logger.debug('Generate file:', batch.id);
                                  }}
                                >
                                  <FileText className="mr-2 h-4 w-4" />
                                  Generate File
                                </DropdownMenuItem>
                              </>
                            )}

                            {batch.status === 'FILE_GENERATED' && (
                              <>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    logger.debug('Submit batch:', batch.id);
                                  }}
                                >
                                  <Send className="mr-2 h-4 w-4" />
                                  Submit to Provider
                                </DropdownMenuItem>
                              </>
                            )}

                            {batch.status === 'SUBMITTED' && (
                              <>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    logger.debug('Upload response:', batch.id);
                                  }}
                                >
                                  <Upload className="mr-2 h-4 w-4" />
                                  Upload Response
                                </DropdownMenuItem>
                              </>
                            )}

                            {batch.fileGenerated && (
                              <>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    logger.debug('Download file:', batch.id);
                                  }}
                                >
                                  <Download className="mr-2 h-4 w-4" />
                                  Download File
                                </DropdownMenuItem>
                              </>
                            )}

                            {['CREATED', 'VALIDATED', 'FILE_GENERATED'].includes(
                              batch.status
                            ) && (
                              <>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    logger.debug('Cancel batch:', batch.id);
                                  }}
                                  className="text-destructive"
                                >
                                  <Ban className="mr-2 h-4 w-4" />
                                  Cancel Batch
                                </DropdownMenuItem>
                              </>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
