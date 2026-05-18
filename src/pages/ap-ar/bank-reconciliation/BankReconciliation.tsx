import { format } from 'date-fns';
import {
  ArrowDownCircle,
  ArrowUpCircle,
  Check,
  FileText,
  Link2,
  Link2Off,
  RefreshCw,
  Wand2,
} from 'lucide-react';
import { useCallback, useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
import { useToast } from '@/hooks/use-toast';
import { bankReconciliationApi, accountsApi } from '@/services/api';
import { useActiveOrganizationId } from '@/stores/organizationStore';

import { logger } from "@/lib/logger";
interface UnreconciledStatement {
  statementId: string;
  transactionDate: string;
  referenceNumber: string | null;
  description: string | null;
  debitAmount: number;
  creditAmount: number;
  unreconciledAmount: number;
}

interface UnreconciledBookEntry {
  voucherId: string;
  voucherNumber: string;
  voucherDate: string;
  narration: string | null;
  debitAmount: number;
  creditAmount: number;
  entryType: string;
}

interface BankAccount {
  id: string;
  code: string;
  name: string;
}

interface WorkspaceData {
  bankAccountId: string;
  bankAccountName: string;
  fromDate: string;
  toDate: string;
  unreconciledStatements: UnreconciledStatement[];
  unreconciledBookEntries: UnreconciledBookEntry[];
  totalUnreconciledBankCredits: number;
  totalUnreconciledBankDebits: number;
  totalUnreconciledBookCredits: number;
  totalUnreconciledBookDebits: number;
}

interface ApiError {
  response?: {
    data?: {
      detail?: string;
    };
  };
}

function getErrorMessage(error: unknown, fallback: string) {
  const apiError = error as ApiError;
  return apiError.response?.data?.detail || fallback;
}

export function BankReconciliation() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();

  const organizationId = useActiveOrganizationId() || '';

  // State
  const [bankAccounts, setBankAccounts] = useState<BankAccount[]>([]);
  const [selectedBankAccount, setSelectedBankAccount] = useState(
    searchParams.get('bank_account_id') || '',
  );
  const [fromDate, setFromDate] = useState(
    searchParams.get('from_date') ||
      format(new Date(new Date().getFullYear(), new Date().getMonth(), 1), 'yyyy-MM-dd'),
  );
  const [toDate, setToDate] = useState(
    searchParams.get('to_date') || format(new Date(), 'yyyy-MM-dd'),
  );
  const [loading, setLoading] = useState(false);
  const [workspaceData, setWorkspaceData] = useState<WorkspaceData | null>(null);
  const [selectedStatement, setSelectedStatement] = useState<UnreconciledStatement | null>(null);
  const [selectedBookEntry, setSelectedBookEntry] = useState<UnreconciledBookEntry | null>(null);
  const [matchAmount, setMatchAmount] = useState('');
  const [matching, setMatching] = useState(false);
  const [autoMatching, setAutoMatching] = useState(false);

  // Fetch bank accounts
  useEffect(() => {
    const fetchBankAccounts = async () => {
      if (!organizationId) return;
      try {
        const response = await accountsApi.list({
          organization_id: organizationId,
          account_type: 'BANK',
          page_size: 100,
        });
        setBankAccounts(response.data.items || []);
        if (!selectedBankAccount && response.data.items?.length > 0) {
          setSelectedBankAccount(response.data.items[0].id);
        }
      } catch (error) {
        logger.error('Failed to fetch bank accounts:', error);
      }
    };
    fetchBankAccounts();
  }, [organizationId, selectedBankAccount]);

  // Fetch workspace data
  const fetchWorkspace = useCallback(async () => {
    if (!organizationId || !selectedBankAccount || !fromDate || !toDate) return;

    setLoading(true);
    try {
      const response = await bankReconciliationApi.getWorkspace({
        bank_account_id: selectedBankAccount,
        from_date: fromDate,
        to_date: toDate,
      });
      setWorkspaceData(response.data);
      setSelectedStatement(null);
      setSelectedBookEntry(null);
      setMatchAmount('');
    } catch (error: unknown) {
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to fetch reconciliation data'),
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [fromDate, organizationId, selectedBankAccount, toDate, toast]);

  useEffect(() => {
    if (selectedBankAccount) {
      fetchWorkspace();
    }
  }, [fetchWorkspace, selectedBankAccount]);

  // Handle statement selection
  const handleSelectStatement = (statement: UnreconciledStatement) => {
    setSelectedStatement(statement);
    setMatchAmount(statement.unreconciledAmount.toFixed(2));
    // Try to find matching book entry
    const amount = statement.creditAmount > 0 ? statement.creditAmount : statement.debitAmount;
    const matchingEntry = workspaceData?.unreconciledBookEntries.find((entry) => {
      const entryAmount = statement.creditAmount > 0 ? entry.debitAmount : entry.creditAmount;
      return Math.abs(entryAmount - amount) < 0.01;
    });
    if (matchingEntry) {
      setSelectedBookEntry(matchingEntry);
    }
  };

  // Handle book entry selection
  const handleSelectBookEntry = (entry: UnreconciledBookEntry) => {
    setSelectedBookEntry(entry);
    if (!selectedStatement) {
      // Try to find matching statement
      const amount = entry.debitAmount > 0 ? entry.debitAmount : entry.creditAmount;
      const matchingStatement = workspaceData?.unreconciledStatements.find((stmt) => {
        const stmtAmount = entry.debitAmount > 0 ? stmt.creditAmount : stmt.debitAmount;
        return Math.abs(stmtAmount - amount) < 0.01;
      });
      if (matchingStatement) {
        setSelectedStatement(matchingStatement);
        setMatchAmount(matchingStatement.unreconciledAmount.toFixed(2));
      }
    }
  };

  // Handle manual match
  const handleMatch = async () => {
    if (!selectedStatement || !selectedBookEntry) {
      toast({
        title: 'Error',
        description: 'Please select both a bank statement and a book entry',
        variant: 'destructive',
      });
      return;
    }

    const amount = parseFloat(matchAmount);
    if (isNaN(amount) || amount <= 0) {
      toast({
        title: 'Error',
        description: 'Please enter a valid match amount',
        variant: 'destructive',
      });
      return;
    }

    setMatching(true);
    try {
      await bankReconciliationApi.matchStatement({
        statementId: selectedStatement.statementId,
        voucherId: selectedBookEntry.voucherId,
        matchedAmount: amount,
        matchType: 'MANUAL',
      });
      toast({
        title: 'Success',
        description: 'Match created successfully',
      });
      fetchWorkspace();
    } catch (error: unknown) {
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to create match'),
        variant: 'destructive',
      });
    } finally {
      setMatching(false);
    }
  };

  // Handle auto match
  const handleAutoMatch = async () => {
    if (!selectedBankAccount) return;

    setAutoMatching(true);
    try {
      const response = await bankReconciliationApi.autoMatch({
        bank_account_id: selectedBankAccount,
        from_date: fromDate,
        to_date: toDate,
      });
      toast({
        title: 'Auto-Match Complete',
        description: `${response.data.matchedCount} matches created`,
      });
      fetchWorkspace();
    } catch (error: unknown) {
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Auto-match failed'),
        variant: 'destructive',
      });
    } finally {
      setAutoMatching(false);
    }
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Bank Reconciliation"
        subtitle="Match bank statements with book entries"
        breadcrumbs={[{ label: 'AP / AR', to: '/admin/ap-ar' }, { label: 'Bank Reconciliation' }]}
        actions={
          <Button
            variant="outline"
            onClick={() =>
              navigate(
                `/admin/ap-ar/bank-reconciliation/brs-report?bank_account_id=${selectedBankAccount}&from_date=${fromDate}&to_date=${toDate}`,
              )
            }
          >
            <FileText className="mr-2 h-4 w-4" />
            BRS Report
          </Button>
        }
      />

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <Label>Bank Account</Label>
              <Select value={selectedBankAccount} onValueChange={setSelectedBankAccount}>
                <SelectTrigger>
                  <SelectValue placeholder="Select bank account" />
                </SelectTrigger>
                <SelectContent>
                  {bankAccounts.map((account) => (
                    <SelectItem key={account.id} value={account.id}>
                      {account.code} - {account.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>From Date</Label>
              <Input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
            </div>
            <div>
              <Label>To Date</Label>
              <Input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} />
            </div>
            <div className="flex items-end gap-2">
              <Button onClick={fetchWorkspace} disabled={loading}>
                {loading ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : null}
                Refresh
              </Button>
              <Button variant="outline" onClick={handleAutoMatch} disabled={autoMatching}>
                {autoMatching ? (
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Wand2 className="mr-2 h-4 w-4" />
                )}
                Auto-Match
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary */}
      {workspaceData && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Bank Credits</p>
                  <p className="text-xl font-bold text-green-600">
                    {formatAmount(workspaceData.totalUnreconciledBankCredits)}
                  </p>
                </div>
                <ArrowDownCircle className="h-8 w-8 text-green-200" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Bank Debits</p>
                  <p className="text-xl font-bold text-red-600">
                    {formatAmount(workspaceData.totalUnreconciledBankDebits)}
                  </p>
                </div>
                <ArrowUpCircle className="h-8 w-8 text-red-200" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Book Debits</p>
                  <p className="text-xl font-bold text-blue-600">
                    {formatAmount(workspaceData.totalUnreconciledBookDebits)}
                  </p>
                </div>
                <FileText className="h-8 w-8 text-blue-200" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Book Credits</p>
                  <p className="text-xl font-bold text-purple-600">
                    {formatAmount(workspaceData.totalUnreconciledBookCredits)}
                  </p>
                </div>
                <FileText className="h-8 w-8 text-purple-200" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Match Panel */}
      {(selectedStatement || selectedBookEntry) && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-8">
              {/* Selected Statement */}
              <div className="flex-1">
                <h4 className="mb-2 font-medium">Bank Statement</h4>
                {selectedStatement ? (
                  <div className="rounded-lg bg-white p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{selectedStatement.referenceNumber}</p>
                        <p className="text-sm text-slate-500">
                          {format(new Date(selectedStatement.transactionDate), 'dd/MM/yyyy')}
                        </p>
                        <p className="text-sm text-slate-500">{selectedStatement.description}</p>
                      </div>
                      <div className="text-right">
                        <p
                          className={`text-lg font-bold ${
                            selectedStatement.creditAmount > 0 ? 'text-green-600' : 'text-red-600'
                          }`}
                        >
                          {formatAmount(selectedStatement.unreconciledAmount)}
                        </p>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedStatement(null);
                            setMatchAmount('');
                          }}
                        >
                          <Link2Off className="mr-1 h-3 w-3" />
                          Clear
                        </Button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="rounded-lg border-2 border-dashed border-slate-300 p-4 text-center text-slate-500">
                    Select a bank statement
                  </div>
                )}
              </div>

              {/* Match Button */}
              <div className="flex flex-col items-center gap-2">
                <Link2 className="h-8 w-8 text-blue-500" />
                <div>
                  <Label className="text-xs">Amount</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={matchAmount}
                    onChange={(e) => setMatchAmount(e.target.value)}
                    className="w-32 text-center"
                  />
                </div>
                <Button
                  onClick={handleMatch}
                  disabled={matching || !selectedStatement || !selectedBookEntry}
                >
                  {matching ? (
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Check className="mr-2 h-4 w-4" />
                  )}
                  Match
                </Button>
              </div>

              {/* Selected Book Entry */}
              <div className="flex-1">
                <h4 className="mb-2 font-medium">Book Entry</h4>
                {selectedBookEntry ? (
                  <div className="rounded-lg bg-white p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{selectedBookEntry.voucherNumber}</p>
                        <p className="text-sm text-slate-500">
                          {format(new Date(selectedBookEntry.voucherDate), 'dd/MM/yyyy')}
                        </p>
                        <p className="text-sm text-slate-500">{selectedBookEntry.narration}</p>
                      </div>
                      <div className="text-right">
                        <p
                          className={`text-lg font-bold ${
                            selectedBookEntry.debitAmount > 0 ? 'text-blue-600' : 'text-purple-600'
                          }`}
                        >
                          {formatAmount(
                            selectedBookEntry.debitAmount > 0
                              ? selectedBookEntry.debitAmount
                              : selectedBookEntry.creditAmount,
                          )}
                        </p>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setSelectedBookEntry(null)}
                        >
                          <Link2Off className="mr-1 h-3 w-3" />
                          Clear
                        </Button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="rounded-lg border-2 border-dashed border-slate-300 p-4 text-center text-slate-500">
                    Select a book entry
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tables */}
      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <RefreshCw className="h-8 w-8 animate-spin text-slate-400" />
        </div>
      ) : workspaceData ? (
        <div className="grid gap-6 md:grid-cols-2">
          {/* Bank Statements */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Unreconciled Bank Statements</CardTitle>
              <CardDescription>
                {workspaceData.unreconciledStatements.length} items
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="max-h-[400px] overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Reference</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {workspaceData.unreconciledStatements.map((statement) => (
                      <TableRow
                        key={statement.statementId}
                        className={`cursor-pointer hover:bg-slate-50 ${
                          selectedStatement?.statementId === statement.statementId
                            ? 'bg-blue-50'
                            : ''
                        }`}
                        onClick={() => handleSelectStatement(statement)}
                      >
                        <TableCell>
                          {format(new Date(statement.transactionDate), 'dd/MM/yyyy')}
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{statement.referenceNumber || '-'}</p>
                            <p className="max-w-[200px] truncate text-xs text-slate-500">
                              {statement.description}
                            </p>
                          </div>
                        </TableCell>
                        <TableCell
                          className={`text-right font-medium ${
                            statement.creditAmount > 0 ? 'text-green-600' : 'text-red-600'
                          }`}
                        >
                          {statement.creditAmount > 0 ? '+' : '-'}
                          {formatAmount(statement.unreconciledAmount)}
                        </TableCell>
                      </TableRow>
                    ))}
                    {workspaceData.unreconciledStatements.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={3} className="text-center text-slate-500">
                          No unreconciled statements
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          {/* Book Entries */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Unreconciled Book Entries</CardTitle>
              <CardDescription>
                {workspaceData.unreconciledBookEntries.length} items
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="max-h-[400px] overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Voucher</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {workspaceData.unreconciledBookEntries.map((entry) => (
                      <TableRow
                        key={entry.voucherId}
                        className={`cursor-pointer hover:bg-slate-50 ${
                          selectedBookEntry?.voucherId === entry.voucherId ? 'bg-blue-50' : ''
                        }`}
                        onClick={() => handleSelectBookEntry(entry)}
                      >
                        <TableCell>{format(new Date(entry.voucherDate), 'dd/MM/yyyy')}</TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{entry.voucherNumber}</p>
                            <p className="max-w-[200px] truncate text-xs text-slate-500">
                              {entry.narration}
                            </p>
                          </div>
                        </TableCell>
                        <TableCell
                          className={`text-right font-medium ${
                            entry.debitAmount > 0 ? 'text-blue-600' : 'text-purple-600'
                          }`}
                        >
                          {entry.debitAmount > 0 ? 'Dr ' : 'Cr '}
                          {formatAmount(
                            entry.debitAmount > 0 ? entry.debitAmount : entry.creditAmount,
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                    {workspaceData.unreconciledBookEntries.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={3} className="text-center text-slate-500">
                          No unreconciled book entries
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : (
        <Card>
          <CardContent className="flex h-64 items-center justify-center">
            <p className="text-slate-500">Select a bank account to start reconciliation</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
