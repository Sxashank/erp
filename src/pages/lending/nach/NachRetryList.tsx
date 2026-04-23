/**
 * NACH Retry List Page
 * Manage bounced transactions due for retry
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Filter,
  RefreshCw,
  AlertTriangle,
  Calendar,
  Loader2,
  FileText,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';

interface BouncedTransaction {
  id: string;
  transactionReference: string;
  originalBatchReference: string;
  loanAccountNumber: string;
  borrowerName: string;
  umrn: string;
  mandateStatus: 'ACTIVE' | 'PENDING' | 'EXPIRED';
  bankName: string;
  accountNumberMasked: string;
  debitAmount: number;
  originalDebitDate: string;
  returnCode: string;
  failureReason: string;
  retryCount: number;
  maxRetries: number;
  nextRetryDate?: string;
  selected: boolean;
}

// Mock data
const mockBouncedTransactions: BouncedTransaction[] = [
  {
    id: '1',
    transactionReference: 'NACH/TXN/003',
    originalBatchReference: 'NACH/2025/01/001',
    loanAccountNumber: 'SMFC/LAP/BLR/2024/L00045',
    borrowerName: 'Tech Solutions India Pvt Ltd',
    umrn: 'RATN50000000001236',
    mandateStatus: 'ACTIVE',
    bankName: 'Axis Bank',
    accountNumberMasked: 'XXXX9012',
    debitAmount: 150000,
    originalDebitDate: '2025-01-15',
    returnCode: '01',
    failureReason: 'Insufficient funds in account',
    retryCount: 0,
    maxRetries: 3,
    nextRetryDate: '2025-01-22',
    selected: true,
  },
  {
    id: '2',
    transactionReference: 'NACH/TXN/004',
    originalBatchReference: 'NACH/2025/01/001',
    loanAccountNumber: 'SMFC/TL/CHN/2023/L00034',
    borrowerName: 'Southern Motors Corp',
    umrn: 'RATN50000000001237',
    mandateStatus: 'EXPIRED',
    bankName: 'SBI',
    accountNumberMasked: 'XXXX3456',
    debitAmount: 100000,
    originalDebitDate: '2025-01-15',
    returnCode: '02',
    failureReason: 'Account closed',
    retryCount: 0,
    maxRetries: 3,
    selected: false,
  },
  {
    id: '3',
    transactionReference: 'NACH/TXN/007',
    originalBatchReference: 'NACH/2025/01/001',
    loanAccountNumber: 'SMFC/LAP/PUN/2024/L00090',
    borrowerName: 'Western Infra Projects',
    umrn: 'RATN50000000001240',
    mandateStatus: 'EXPIRED',
    bankName: 'Bank of Baroda',
    accountNumberMasked: 'XXXX6789',
    debitAmount: 125000,
    originalDebitDate: '2025-01-15',
    returnCode: '03',
    failureReason: 'Mandate not registered/expired',
    retryCount: 0,
    maxRetries: 3,
    selected: false,
  },
  {
    id: '4',
    transactionReference: 'NACH/TXN/015',
    originalBatchReference: 'NACH/2025/01/002',
    loanAccountNumber: 'SMFC/WC/DEL/2024/L00112',
    borrowerName: 'Delhi Trading Company',
    umrn: 'RATN50000000001250',
    mandateStatus: 'ACTIVE',
    bankName: 'HDFC Bank',
    accountNumberMasked: 'XXXX4567',
    debitAmount: 85000,
    originalDebitDate: '2025-01-20',
    returnCode: '01',
    failureReason: 'Insufficient funds in account',
    retryCount: 1,
    maxRetries: 3,
    nextRetryDate: '2025-01-27',
    selected: true,
  },
];

const returnCodeLabels: Record<string, { label: string; retryable: boolean }> = {
  '00': { label: 'Success', retryable: false },
  '01': { label: 'Insufficient Funds', retryable: true },
  '02': { label: 'Account Closed', retryable: false },
  '03': { label: 'Mandate Expired', retryable: false },
  '04': { label: 'Account Blocked', retryable: false },
  '05': { label: 'Invalid Account', retryable: false },
  '06': { label: 'Technical Error', retryable: true },
};

export default function NachRetryList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [returnCodeFilter, setReturnCodeFilter] = useState<string>('ALL');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newDebitDate, setNewDebitDate] = useState('');
  const [transactions, setTransactions] = useState(mockBouncedTransactions);

  // Filter only retryable transactions
  const retryableTransactions = transactions.filter((txn) => {
    const codeInfo = returnCodeLabels[txn.returnCode];
    return (
      codeInfo?.retryable &&
      txn.mandateStatus === 'ACTIVE' &&
      txn.retryCount < txn.maxRetries
    );
  });

  const nonRetryableTransactions = transactions.filter((txn) => {
    const codeInfo = returnCodeLabels[txn.returnCode];
    return (
      !codeInfo?.retryable ||
      txn.mandateStatus !== 'ACTIVE' ||
      txn.retryCount >= txn.maxRetries
    );
  });

  const filteredTransactions = retryableTransactions.filter((txn) => {
    const matchesSearch =
      txn.loanAccountNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
      txn.borrowerName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      txn.transactionReference.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCode =
      returnCodeFilter === 'ALL' || txn.returnCode === returnCodeFilter;
    return matchesSearch && matchesCode;
  });

  const selectedTransactions = transactions.filter(
    (txn) => txn.selected && retryableTransactions.includes(txn)
  );
  const totalAmount = selectedTransactions.reduce(
    (sum, txn) => sum + txn.debitAmount,
    0
  );

  const handleSelectAll = (checked: boolean) => {
    setTransactions(
      transactions.map((txn) => ({
        ...txn,
        selected: retryableTransactions.includes(txn) ? checked : txn.selected,
      }))
    );
  };

  const handleSelectTransaction = (id: string, checked: boolean) => {
    setTransactions(
      transactions.map((txn) =>
        txn.id === id ? { ...txn, selected: checked } : txn
      )
    );
  };

  const handleCreateRetryBatch = async () => {
    if (selectedTransactions.length === 0 || !newDebitDate) {
      return;
    }

    setIsSubmitting(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsSubmitting(false);
    setShowCreateDialog(false);

    navigate('/admin/lending/nach/batches');
  };

  const allSelected =
    retryableTransactions.length > 0 &&
    retryableTransactions.every((txn) => txn.selected);

  return (
    <div className="space-y-6">
      <PageHeader
        title="NACH Retry Queue"
        subtitle="Manage bounced transactions due for retry"
        actions={
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button disabled={selectedTransactions.length === 0}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Create Retry Batch ({selectedTransactions.length})
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Retry Batch</DialogTitle>
              <DialogDescription>
                Create a new NACH batch with {selectedTransactions.length} selected
                transactions
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="retryDebitDate">New Debit Date</Label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="retryDebitDate"
                    type="date"
                    value={newDebitDate}
                    onChange={(e) => setNewDebitDate(e.target.value)}
                    className="pl-10"
                    min={new Date().toISOString().split('T')[0]}
                  />
                </div>
              </div>
              <div className="bg-muted p-4 rounded-md space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Transactions</span>
                  <span className="font-medium">{selectedTransactions.length}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Total Amount</span>
                  <AmountDisplay amount={totalAmount} className="font-medium" />
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowCreateDialog(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={handleCreateRetryBatch}
                disabled={!newDebitDate || isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <FileText className="mr-2 h-4 w-4" />
                    Create Batch
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Bounced</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {transactions.length}
            </div>
            <p className="text-xs text-muted-foreground">
              Pending resolution
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Retryable</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600">
              {retryableTransactions.length}
            </div>
            <p className="text-xs text-muted-foreground">
              Eligible for retry
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Non-Retryable</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-600">
              {nonRetryableTransactions.length}
            </div>
            <p className="text-xs text-muted-foreground">
              Requires manual action
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Selected Amount</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={totalAmount}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-xs text-muted-foreground">
              {selectedTransactions.length} selected
            </p>
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
                placeholder="Search by reference, account or borrower..."
                className="pl-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <Select value={returnCodeFilter} onValueChange={setReturnCodeFilter}>
              <SelectTrigger className="w-[200px]">
                <Filter className="mr-2 h-4 w-4" />
                <SelectValue placeholder="Return Code" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All Codes</SelectItem>
                <SelectItem value="01">01 - Insufficient Funds</SelectItem>
                <SelectItem value="06">06 - Technical Error</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Retryable Transactions */}
      <Card>
        <CardHeader>
          <CardTitle>Retryable Transactions</CardTitle>
          <CardDescription>
            Transactions that can be re-presented via NACH
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[50px]">
                  <Checkbox
                    checked={allSelected}
                    onCheckedChange={(checked) =>
                      handleSelectAll(checked as boolean)
                    }
                    aria-label="Select all"
                  />
                </TableHead>
                <TableHead>Reference</TableHead>
                <TableHead>Loan Account</TableHead>
                <TableHead>Borrower</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead>Return Code</TableHead>
                <TableHead className="text-center">Retry #</TableHead>
                <TableHead>Next Retry</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredTransactions.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={8}
                    className="text-center py-8 text-muted-foreground"
                  >
                    No retryable transactions found
                  </TableCell>
                </TableRow>
              ) : (
                filteredTransactions.map((txn) => (
                  <TableRow key={txn.id}>
                    <TableCell>
                      <Checkbox
                        checked={txn.selected}
                        onCheckedChange={(checked) =>
                          handleSelectTransaction(txn.id, checked as boolean)
                        }
                        aria-label={`Select ${txn.transactionReference}`}
                      />
                    </TableCell>
                    <TableCell>
                      <div className="font-mono text-sm">
                        {txn.transactionReference}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {txn.originalBatchReference}
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {txn.loanAccountNumber}
                    </TableCell>
                    <TableCell className="max-w-[180px] truncate">
                      {txn.borrowerName}
                    </TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={txn.debitAmount} />
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Badge
                          variant="outline"
                          className="bg-amber-100 text-amber-700"
                        >
                          {txn.returnCode}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {returnCodeLabels[txn.returnCode]?.label}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge variant="secondary">
                        {txn.retryCount}/{txn.maxRetries}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {txn.nextRetryDate ? (
                        <DateDisplay date={txn.nextRetryDate} />
                      ) : (
                        '-'
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Non-Retryable Transactions */}
      {nonRetryableTransactions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-gray-600">
              <AlertTriangle className="h-5 w-5" />
              Non-Retryable Transactions ({nonRetryableTransactions.length})
            </CardTitle>
            <CardDescription>
              These transactions cannot be retried via NACH. Manual collection or
              mandate re-registration required.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Reference</TableHead>
                  <TableHead>Loan Account</TableHead>
                  <TableHead>Borrower</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Return Code</TableHead>
                  <TableHead>Reason</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {nonRetryableTransactions.map((txn) => (
                  <TableRow key={txn.id} className="bg-muted/30">
                    <TableCell>
                      <div className="font-mono text-sm">
                        {txn.transactionReference}
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {txn.loanAccountNumber}
                    </TableCell>
                    <TableCell className="max-w-[180px] truncate">
                      {txn.borrowerName}
                    </TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={txn.debitAmount} />
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className="bg-red-100 text-red-700"
                      >
                        {txn.returnCode} - {returnCodeLabels[txn.returnCode]?.label}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {txn.mandateStatus !== 'ACTIVE'
                        ? 'Mandate not active'
                        : txn.retryCount >= txn.maxRetries
                        ? 'Max retries exceeded'
                        : 'Non-retryable error'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
