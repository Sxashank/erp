/**
 * NACH Batch Detail Page
 * Displays batch details with individual transactions
 */

import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  FileText,
  Send,
  Upload,
  Download,
  Ban,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  RefreshCw,
  Search,
  Filter,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
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
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';

// Types
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

type TransactionStatus =
  | 'PENDING'
  | 'INCLUDED'
  | 'SUBMITTED'
  | 'SUCCESS'
  | 'BOUNCED'
  | 'REJECTED'
  | 'CANCELLED'
  | 'RETRY_SCHEDULED';

interface Transaction {
  id: string;
  transactionReference: string;
  loanAccountNumber: string;
  borrowerName: string;
  umrn: string;
  bankName: string;
  accountNumberMasked: string;
  debitAmount: number;
  debitDate: string;
  emiNumber: number;
  status: TransactionStatus;
  returnCode?: string;
  failureReason?: string;
  bankReference?: string;
  processedAt?: string;
  retryCount: number;
  maxRetries: number;
  nextRetryDate?: string;
}

interface NachBatch {
  id: string;
  batchReference: string;
  batchDate: string;
  debitDate: string;
  provider: string;
  totalTransactions: number;
  totalAmount: number;
  successCount: number;
  successAmount: number;
  failureCount: number;
  failureAmount: number;
  pendingCount: number;
  status: NachBatchStatus;
  fileGenerated: boolean;
  fileName?: string;
  fileChecksum?: string;
  submittedAt?: string;
  responseReceivedAt?: string;
  completedAt?: string;
  createdAt: string;
  createdBy: string;
  transactions: Transaction[];
}

// Mock data
const mockBatch: NachBatch = {
  id: '1',
  batchReference: 'NACH/2025/01/001',
  batchDate: '2025-01-10',
  debitDate: '2025-01-15',
  provider: 'RAZORPAY',
  totalTransactions: 10,
  totalAmount: 1250000,
  successCount: 7,
  successAmount: 875000,
  failureCount: 3,
  failureAmount: 375000,
  pendingCount: 0,
  status: 'COMPLETED',
  fileGenerated: true,
  fileName: 'NACH_DEBIT_20250115_001.txt',
  fileChecksum: 'a1b2c3d4e5f6...',
  submittedAt: '2025-01-14T10:30:00',
  responseReceivedAt: '2025-01-15T16:00:00',
  completedAt: '2025-01-15T18:00:00',
  createdAt: '2025-01-10T09:00:00',
  createdBy: 'Admin User',
  transactions: [
    {
      id: '1',
      transactionReference: 'NACH/TXN/001',
      loanAccountNumber: 'SMFC/TL/DEL/2024/L00001',
      borrowerName: 'ABC Industries Private Limited',
      umrn: 'RATN50000000001234',
      bankName: 'HDFC Bank',
      accountNumberMasked: 'XXXX1234',
      debitAmount: 125000,
      debitDate: '2025-01-15',
      emiNumber: 5,
      status: 'SUCCESS',
      bankReference: 'HDFC123456789',
      processedAt: '2025-01-15T14:30:00',
      retryCount: 0,
      maxRetries: 3,
    },
    {
      id: '2',
      transactionReference: 'NACH/TXN/002',
      loanAccountNumber: 'SMFC/WC/MUM/2024/L00089',
      borrowerName: 'XYZ Traders LLP',
      umrn: 'RATN50000000001235',
      bankName: 'ICICI Bank',
      accountNumberMasked: 'XXXX5678',
      debitAmount: 225000,
      debitDate: '2025-01-15',
      emiNumber: 8,
      status: 'SUCCESS',
      bankReference: 'ICICI987654321',
      processedAt: '2025-01-15T14:35:00',
      retryCount: 0,
      maxRetries: 3,
    },
    {
      id: '3',
      transactionReference: 'NACH/TXN/003',
      loanAccountNumber: 'SMFC/LAP/BLR/2024/L00045',
      borrowerName: 'Tech Solutions India Pvt Ltd',
      umrn: 'RATN50000000001236',
      bankName: 'Axis Bank',
      accountNumberMasked: 'XXXX9012',
      debitAmount: 150000,
      debitDate: '2025-01-15',
      emiNumber: 12,
      status: 'BOUNCED',
      returnCode: '01',
      failureReason: 'Insufficient funds in account',
      processedAt: '2025-01-15T14:40:00',
      retryCount: 0,
      maxRetries: 3,
      nextRetryDate: '2025-01-22',
    },
    {
      id: '4',
      transactionReference: 'NACH/TXN/004',
      loanAccountNumber: 'SMFC/TL/CHN/2023/L00034',
      borrowerName: 'Southern Motors Corp',
      umrn: 'RATN50000000001237',
      bankName: 'SBI',
      accountNumberMasked: 'XXXX3456',
      debitAmount: 100000,
      debitDate: '2025-01-15',
      emiNumber: 15,
      status: 'BOUNCED',
      returnCode: '02',
      failureReason: 'Account closed',
      processedAt: '2025-01-15T14:45:00',
      retryCount: 0,
      maxRetries: 3,
    },
    {
      id: '5',
      transactionReference: 'NACH/TXN/005',
      loanAccountNumber: 'SMFC/WC/KOL/2024/L00067',
      borrowerName: 'Eastern Exports Ltd',
      umrn: 'RATN50000000001238',
      bankName: 'Punjab National Bank',
      accountNumberMasked: 'XXXX7890',
      debitAmount: 175000,
      debitDate: '2025-01-15',
      emiNumber: 3,
      status: 'SUCCESS',
      bankReference: 'PNB567890123',
      processedAt: '2025-01-15T14:50:00',
      retryCount: 0,
      maxRetries: 3,
    },
    {
      id: '6',
      transactionReference: 'NACH/TXN/006',
      loanAccountNumber: 'SMFC/TL/HYD/2024/L00078',
      borrowerName: 'Deccan Enterprises',
      umrn: 'RATN50000000001239',
      bankName: 'Kotak Mahindra Bank',
      accountNumberMasked: 'XXXX2345',
      debitAmount: 95000,
      debitDate: '2025-01-15',
      emiNumber: 6,
      status: 'SUCCESS',
      bankReference: 'KOTAK234567890',
      processedAt: '2025-01-15T14:55:00',
      retryCount: 0,
      maxRetries: 3,
    },
    {
      id: '7',
      transactionReference: 'NACH/TXN/007',
      loanAccountNumber: 'SMFC/LAP/PUN/2024/L00090',
      borrowerName: 'Western Infra Projects',
      umrn: 'RATN50000000001240',
      bankName: 'Bank of Baroda',
      accountNumberMasked: 'XXXX6789',
      debitAmount: 125000,
      debitDate: '2025-01-15',
      emiNumber: 4,
      status: 'BOUNCED',
      returnCode: '03',
      failureReason: 'Mandate not registered/expired',
      processedAt: '2025-01-15T15:00:00',
      retryCount: 0,
      maxRetries: 3,
    },
    {
      id: '8',
      transactionReference: 'NACH/TXN/008',
      loanAccountNumber: 'SMFC/WC/AHM/2024/L00056',
      borrowerName: 'Gujarat Textiles Pvt Ltd',
      umrn: 'RATN50000000001241',
      bankName: 'Yes Bank',
      accountNumberMasked: 'XXXX0123',
      debitAmount: 80000,
      debitDate: '2025-01-15',
      emiNumber: 9,
      status: 'SUCCESS',
      bankReference: 'YES345678901',
      processedAt: '2025-01-15T15:05:00',
      retryCount: 0,
      maxRetries: 3,
    },
    {
      id: '9',
      transactionReference: 'NACH/TXN/009',
      loanAccountNumber: 'SMFC/TL/JAI/2024/L00023',
      borrowerName: 'Rajasthan Marble Works',
      umrn: 'RATN50000000001242',
      bankName: 'IDFC First Bank',
      accountNumberMasked: 'XXXX4567',
      debitAmount: 110000,
      debitDate: '2025-01-15',
      emiNumber: 7,
      status: 'SUCCESS',
      bankReference: 'IDFC456789012',
      processedAt: '2025-01-15T15:10:00',
      retryCount: 0,
      maxRetries: 3,
    },
    {
      id: '10',
      transactionReference: 'NACH/TXN/010',
      loanAccountNumber: 'SMFC/LAP/LKO/2024/L00012',
      borrowerName: 'UP Agri Commodities',
      umrn: 'RATN50000000001243',
      bankName: 'Union Bank of India',
      accountNumberMasked: 'XXXX8901',
      debitAmount: 65000,
      debitDate: '2025-01-15',
      emiNumber: 2,
      status: 'SUCCESS',
      bankReference: 'UNION567890123',
      processedAt: '2025-01-15T15:15:00',
      retryCount: 0,
      maxRetries: 3,
    },
  ],
};

const batchStatusConfig: Record<
  NachBatchStatus,
  { label: string; color: string; icon: React.ReactNode }
> = {
  CREATED: {
    label: 'Created',
    color: 'bg-slate-100 text-slate-700 border-slate-300',
    icon: <Clock className="h-4 w-4" />,
  },
  VALIDATED: {
    label: 'Validated',
    color: 'bg-blue-100 text-blue-700 border-blue-300',
    icon: <CheckCircle className="h-4 w-4" />,
  },
  FILE_GENERATED: {
    label: 'File Generated',
    color: 'bg-indigo-100 text-indigo-700 border-indigo-300',
    icon: <FileText className="h-4 w-4" />,
  },
  SUBMITTED: {
    label: 'Submitted',
    color: 'bg-purple-100 text-purple-700 border-purple-300',
    icon: <Send className="h-4 w-4" />,
  },
  PROCESSING: {
    label: 'Processing',
    color: 'bg-amber-100 text-amber-700 border-amber-300',
    icon: <RefreshCw className="h-4 w-4 animate-spin" />,
  },
  RESPONSE_RECEIVED: {
    label: 'Response Received',
    color: 'bg-cyan-100 text-cyan-700 border-cyan-300',
    icon: <Download className="h-4 w-4" />,
  },
  COMPLETED: {
    label: 'Completed',
    color: 'bg-green-100 text-green-700 border-green-300',
    icon: <CheckCircle className="h-4 w-4" />,
  },
  FAILED: {
    label: 'Failed',
    color: 'bg-red-100 text-red-700 border-red-300',
    icon: <XCircle className="h-4 w-4" />,
  },
  CANCELLED: {
    label: 'Cancelled',
    color: 'bg-gray-100 text-gray-600 border-gray-300',
    icon: <Ban className="h-4 w-4" />,
  },
};

const transactionStatusConfig: Record<
  TransactionStatus,
  { label: string; color: string; icon: React.ReactNode }
> = {
  PENDING: {
    label: 'Pending',
    color: 'bg-slate-100 text-slate-700 border-slate-300',
    icon: <Clock className="h-3 w-3" />,
  },
  INCLUDED: {
    label: 'Included',
    color: 'bg-blue-100 text-blue-700 border-blue-300',
    icon: <CheckCircle className="h-3 w-3" />,
  },
  SUBMITTED: {
    label: 'Submitted',
    color: 'bg-purple-100 text-purple-700 border-purple-300',
    icon: <Send className="h-3 w-3" />,
  },
  SUCCESS: {
    label: 'Success',
    color: 'bg-green-100 text-green-700 border-green-300',
    icon: <CheckCircle className="h-3 w-3" />,
  },
  BOUNCED: {
    label: 'Bounced',
    color: 'bg-red-100 text-red-700 border-red-300',
    icon: <XCircle className="h-3 w-3" />,
  },
  REJECTED: {
    label: 'Rejected',
    color: 'bg-red-200 text-red-800 border-red-400',
    icon: <Ban className="h-3 w-3" />,
  },
  CANCELLED: {
    label: 'Cancelled',
    color: 'bg-gray-100 text-gray-600 border-gray-300',
    icon: <Ban className="h-3 w-3" />,
  },
  RETRY_SCHEDULED: {
    label: 'Retry Scheduled',
    color: 'bg-amber-100 text-amber-700 border-amber-300',
    icon: <RefreshCw className="h-3 w-3" />,
  },
};

export default function NachBatchDetail() {
  const navigate = useNavigate();
  const { batchId } = useParams();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const batch = mockBatch;

  const filteredTransactions = batch.transactions.filter((txn) => {
    const matchesSearch =
      txn.transactionReference.toLowerCase().includes(searchQuery.toLowerCase()) ||
      txn.loanAccountNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
      txn.borrowerName.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || txn.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const successRate =
    batch.totalTransactions > 0
      ? ((batch.successCount / batch.totalTransactions) * 100).toFixed(1)
      : 0;

  const batchStatus = batchStatusConfig[batch.status];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate('/admin/lending/nach/batches')}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-semibold">{batch.batchReference}</h1>
              <Badge
                variant="outline"
                className={`${batchStatus.color} border font-medium`}
              >
                <span className="mr-1">{batchStatus.icon}</span>
                {batchStatus.label}
              </Badge>
            </div>
            <p className="text-muted-foreground">
              Debit Date: <DateDisplay date={batch.debitDate} /> | Provider:{' '}
              {batch.provider}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          {batch.status === 'CREATED' && (
            <Button variant="outline">
              <FileText className="mr-2 h-4 w-4" />
              Generate File
            </Button>
          )}
          {batch.status === 'FILE_GENERATED' && (
            <Button>
              <Send className="mr-2 h-4 w-4" />
              Submit to Provider
            </Button>
          )}
          {batch.status === 'SUBMITTED' && (
            <Button variant="outline">
              <Upload className="mr-2 h-4 w-4" />
              Upload Response
            </Button>
          )}
          {batch.fileGenerated && (
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Download File
            </Button>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Transactions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{batch.totalTransactions}</div>
            <AmountDisplay
              amount={batch.totalAmount}
              className="text-sm text-muted-foreground"
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Successful</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {batch.successCount}
            </div>
            <AmountDisplay
              amount={batch.successAmount}
              className="text-sm text-green-600"
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Bounced</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {batch.failureCount}
            </div>
            <AmountDisplay
              amount={batch.failureAmount}
              className="text-sm text-red-600"
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600">
              {batch.pendingCount}
            </div>
            <p className="text-sm text-muted-foreground">Awaiting response</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{successRate}%</div>
            <Progress
              value={Number(successRate)}
              className="mt-2 h-2"
            />
          </CardContent>
        </Card>
      </div>

      {/* Batch Details & File Info */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Batch Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Batch Date</span>
                <p className="font-medium">
                  <DateDisplay date={batch.batchDate} />
                </p>
              </div>
              <div>
                <span className="text-muted-foreground">Debit Date</span>
                <p className="font-medium">
                  <DateDisplay date={batch.debitDate} />
                </p>
              </div>
              <div>
                <span className="text-muted-foreground">Provider</span>
                <p className="font-medium">{batch.provider}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Created By</span>
                <p className="font-medium">{batch.createdBy}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Created At</span>
                <p className="font-medium">
                  <DateDisplay date={batch.createdAt} />
                </p>
              </div>
              {batch.submittedAt && (
                <div>
                  <span className="text-muted-foreground">Submitted At</span>
                  <p className="font-medium">
                    <DateDisplay date={batch.submittedAt} />
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>File Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {batch.fileGenerated ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2 p-3 bg-muted rounded-md">
                  <FileText className="h-5 w-5 text-muted-foreground" />
                  <div className="flex-1">
                    <p className="font-mono text-sm">{batch.fileName}</p>
                    <p className="text-xs text-muted-foreground">
                      Checksum: {batch.fileChecksum}
                    </p>
                  </div>
                  <Button variant="ghost" size="sm">
                    <Download className="h-4 w-4" />
                  </Button>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">File Format</span>
                    <p className="font-medium">ACH Debit</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Records</span>
                    <p className="font-medium">{batch.totalTransactions}</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-6 text-center">
                <FileText className="h-12 w-12 text-muted-foreground mb-3" />
                <p className="text-muted-foreground">
                  File not yet generated
                </p>
                <Button className="mt-3">
                  <FileText className="mr-2 h-4 w-4" />
                  Generate File
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Transactions */}
      <Card>
        <CardHeader>
          <CardTitle>Transactions</CardTitle>
          <CardDescription>
            Individual NACH debit transactions in this batch
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="all">
            <div className="flex items-center justify-between mb-4">
              <TabsList>
                <TabsTrigger value="all">
                  All ({batch.totalTransactions})
                </TabsTrigger>
                <TabsTrigger value="success">
                  Success ({batch.successCount})
                </TabsTrigger>
                <TabsTrigger value="bounced">
                  Bounced ({batch.failureCount})
                </TabsTrigger>
                {batch.pendingCount > 0 && (
                  <TabsTrigger value="pending">
                    Pending ({batch.pendingCount})
                  </TabsTrigger>
                )}
              </TabsList>
              <div className="flex gap-2">
                <div className="relative">
                  <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search transactions..."
                    className="pl-8 w-[250px]"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-[150px]">
                    <Filter className="mr-2 h-4 w-4" />
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">All Status</SelectItem>
                    <SelectItem value="SUCCESS">Success</SelectItem>
                    <SelectItem value="BOUNCED">Bounced</SelectItem>
                    <SelectItem value="PENDING">Pending</SelectItem>
                    <SelectItem value="RETRY_SCHEDULED">Retry Scheduled</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <TabsContent value="all" className="mt-0">
              <TransactionsTable transactions={filteredTransactions} />
            </TabsContent>
            <TabsContent value="success" className="mt-0">
              <TransactionsTable
                transactions={batch.transactions.filter(
                  (t) => t.status === 'SUCCESS'
                )}
              />
            </TabsContent>
            <TabsContent value="bounced" className="mt-0">
              <TransactionsTable
                transactions={batch.transactions.filter(
                  (t) => t.status === 'BOUNCED' || t.status === 'REJECTED'
                )}
              />
            </TabsContent>
            <TabsContent value="pending" className="mt-0">
              <TransactionsTable
                transactions={batch.transactions.filter(
                  (t) => t.status === 'PENDING' || t.status === 'SUBMITTED'
                )}
              />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}

function TransactionsTable({ transactions }: { transactions: Transaction[] }) {
  const navigate = useNavigate();

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Loan Account</TableHead>
          <TableHead>Borrower</TableHead>
          <TableHead>UMRN</TableHead>
          <TableHead>Bank</TableHead>
          <TableHead className="text-right">Amount</TableHead>
          <TableHead className="text-center">EMI #</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Reason</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {transactions.length === 0 ? (
          <TableRow>
            <TableCell
              colSpan={8}
              className="text-center py-8 text-muted-foreground"
            >
              No transactions found
            </TableCell>
          </TableRow>
        ) : (
          transactions.map((txn) => {
            const status = transactionStatusConfig[txn.status];
            return (
              <TableRow
                key={txn.id}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() =>
                  navigate(`/admin/lending/accounts/${txn.loanAccountNumber}`)
                }
              >
                <TableCell>
                  <div className="font-mono text-sm">{txn.loanAccountNumber}</div>
                  <div className="text-xs text-muted-foreground">
                    {txn.transactionReference}
                  </div>
                </TableCell>
                <TableCell className="max-w-[200px] truncate">
                  {txn.borrowerName}
                </TableCell>
                <TableCell className="font-mono text-xs">{txn.umrn}</TableCell>
                <TableCell>
                  <div>{txn.bankName}</div>
                  <div className="text-xs text-muted-foreground">
                    A/c: {txn.accountNumberMasked}
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <AmountDisplay amount={txn.debitAmount} />
                </TableCell>
                <TableCell className="text-center">{txn.emiNumber}</TableCell>
                <TableCell>
                  <Badge
                    variant="outline"
                    className={`${status.color} border font-medium`}
                  >
                    <span className="mr-1">{status.icon}</span>
                    {status.label}
                  </Badge>
                </TableCell>
                <TableCell className="max-w-[200px]">
                  {txn.failureReason ? (
                    <div className="flex items-start gap-1">
                      <AlertTriangle className="h-3 w-3 text-red-500 mt-0.5 flex-shrink-0" />
                      <span className="text-xs text-red-600 line-clamp-2">
                        {txn.returnCode}: {txn.failureReason}
                      </span>
                    </div>
                  ) : txn.bankReference ? (
                    <span className="text-xs text-muted-foreground font-mono">
                      Ref: {txn.bankReference}
                    </span>
                  ) : (
                    '-'
                  )}
                </TableCell>
              </TableRow>
            );
          })
        )}
      </TableBody>
    </Table>
  );
}
