/**
 * NACH Retry List Page
 * Manage bounced transactions due for retry.
 *
 * Data source: GET /lending/nach/retry-due (camelCase via Pydantic CamelSchema).
 */

import { Search, Filter, RefreshCw, Calendar, Loader2, FileText } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
import { useCreateNachRetryBatch } from '@/hooks/lending/useNachBatches';
import { useNachRetryDue, type NachRetryDueItem } from '@/hooks/lending/useNachRetryDue';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';

const returnCodeLabels: Record<string, string> = {
  '00': 'Success',
  '01': 'Insufficient Funds',
  '02': 'Account Closed',
  '03': 'Mandate Expired',
  '04': 'Account Blocked',
  '05': 'Invalid Account',
  '06': 'Technical Error',
};

export default function NachRetryList() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState('');
  const [returnCodeFilter, setReturnCodeFilter] = useState<string>('ALL');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newDebitDate, setNewDebitDate] = useState('');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const { data, isLoading, isError, error, refetch } = useNachRetryDue();
  const createRetryBatch = useCreateNachRetryBatch();
  const items: NachRetryDueItem[] = data?.items ?? [];

  const filteredItems = useMemo(() => {
    return items.filter((txn) => {
      const q = searchQuery.toLowerCase();
      const matchesSearch =
        !searchQuery ||
        txn.loanAccountNumber.toLowerCase().includes(q) ||
        txn.borrowerName.toLowerCase().includes(q) ||
        txn.transactionReference.toLowerCase().includes(q);
      const matchesCode = returnCodeFilter === 'ALL' || txn.returnCode === returnCodeFilter;
      return matchesSearch && matchesCode;
    });
  }, [items, searchQuery, returnCodeFilter]);

  const selectedTransactions = items.filter((txn) => selectedIds.has(txn.id));
  // Wire amounts are strings (Decimal precision); coerce once for display-only sums.
  const totalSelectedAmount = selectedTransactions.reduce(
    (sum, txn) => sum + Number(txn.debitAmount),
    0,
  );

  const allFilteredSelected =
    filteredItems.length > 0 && filteredItems.every((t) => selectedIds.has(t.id));

  const handleSelectAll = (checked: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      filteredItems.forEach((t) => {
        if (checked) next.add(t.id);
        else next.delete(t.id);
      });
      return next;
    });
  };

  const handleSelectOne = (id: string, checked: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (checked) next.add(id);
      else next.delete(id);
      return next;
    });
  };

  const handleCreateRetryBatch = () => {
    if (selectedTransactions.length === 0 || !newDebitDate) return;
    createRetryBatch.mutate(
      {
        transactionIds: selectedTransactions.map((t) => t.id),
        newDebitDate,
      },
      {
        onSuccess: () => {
          toast({
            title: 'Retry batch created',
            description: `${selectedTransactions.length} transactions queued.`,
          });
          setShowCreateDialog(false);
          setSelectedIds(new Set());
          navigate('/admin/lending/nach/batches');
        },
        onError: (err) => showErrorToast(err, toast),
      },
    );
  };

  const isSubmitting = createRetryBatch.isPending;

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
                  Create a new NACH batch with {selectedTransactions.length} selected transactions
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
                <div className="space-y-2 rounded-md bg-muted p-4">
                  <div className="flex justify-between text-sm">
                    <span>Transactions</span>
                    <span className="font-medium">{selectedTransactions.length}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Total Amount</span>
                    <AmountDisplay amount={totalSelectedAmount} className="font-medium" />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreateRetryBatch} disabled={!newDebitDate || isSubmitting}>
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

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Retryable</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600">{data?.total ?? items.length}</div>
            <p className="text-xs text-muted-foreground">Eligible for retry</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Retry Amount</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={data?.totalAmount ?? 0}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-xs text-muted-foreground">Total retryable</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Selected</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={totalSelectedAmount}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-xs text-muted-foreground">{selectedTransactions.length} selected</p>
          </CardContent>
        </Card>
      </div>

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
              <SelectTrigger className="w-[220px]">
                <Filter className="mr-2 h-4 w-4" />
                <SelectValue placeholder="Return Code" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All Codes</SelectItem>
                {Object.entries(returnCodeLabels).map(([code, label]) => (
                  <SelectItem key={code} value={code}>
                    {code} - {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Retryable Transactions</CardTitle>
          <CardDescription>Transactions that can be re-presented via NACH</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[50px]">
                  <Checkbox
                    checked={allFilteredSelected}
                    onCheckedChange={(checked) => handleSelectAll(checked as boolean)}
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
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                    <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />
                    Loading retry queue...
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8">
                    <ErrorState
                      title="Could not load retry queue"
                      error={error}
                      onRetry={() => refetch()}
                    />
                  </TableCell>
                </TableRow>
              ) : filteredItems.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                    No retryable transactions found
                  </TableCell>
                </TableRow>
              ) : (
                filteredItems.map((txn) => (
                  <TableRow key={txn.id}>
                    <TableCell>
                      <Checkbox
                        checked={selectedIds.has(txn.id)}
                        onCheckedChange={(checked) => handleSelectOne(txn.id, checked as boolean)}
                        aria-label={`Select ${txn.transactionReference}`}
                      />
                    </TableCell>
                    <TableCell>
                      <div className="font-mono text-sm">{txn.transactionReference}</div>
                      <div className="text-xs text-muted-foreground">
                        Original: <DateDisplay date={txn.originalDebitDate} />
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-sm">{txn.loanAccountNumber}</TableCell>
                    <TableCell className="max-w-[180px] truncate">{txn.borrowerName}</TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={txn.debitAmount} />
                    </TableCell>
                    <TableCell>
                      {txn.returnCode ? (
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="bg-amber-100 text-amber-700">
                            {txn.returnCode}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {returnCodeLabels[txn.returnCode] ?? txn.lastFailureReason ?? '—'}
                          </span>
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground">
                          {txn.lastFailureReason ?? '—'}
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge variant="secondary">
                        {txn.retryCount}/{txn.maxRetries}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <DateDisplay date={txn.nextRetryDate} />
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
