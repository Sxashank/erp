import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { format } from 'date-fns';
import {
  ArrowDownCircle,
  ArrowLeft,
  ArrowUpCircle,
  Check,
  CheckCircle,
  FileText,
  Link2,
  Link2Off,
  RefreshCw,
  Search,
  Wand2,
} from 'lucide-react';

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
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import { bankReconciliationApi, accountsApi } from '@/services/api';

interface UnreconciledStatement {
  statement_id: string;
  transaction_date: string;
  reference_number: string | null;
  description: string | null;
  debit_amount: number;
  credit_amount: number;
  unreconciled_amount: number;
}

interface UnreconciledBookEntry {
  voucher_id: string;
  voucher_number: string;
  voucher_date: string;
  narration: string | null;
  debit_amount: number;
  credit_amount: number;
  entry_type: string;
}

interface BankAccount {
  id: string;
  code: string;
  name: string;
}

interface WorkspaceData {
  bank_account_id: string;
  bank_account_name: string;
  from_date: string;
  to_date: string;
  unreconciled_statements: UnreconciledStatement[];
  unreconciled_book_entries: UnreconciledBookEntry[];
  total_unreconciled_bank_credits: number;
  total_unreconciled_bank_debits: number;
  total_unreconciled_book_credits: number;
  total_unreconciled_book_debits: number;
}

export function BankReconciliation() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();

  const organizationId = localStorage.getItem('organization_id') || '';

  // State
  const [bankAccounts, setBankAccounts] = useState<BankAccount[]>([]);
  const [selectedBankAccount, setSelectedBankAccount] = useState(
    searchParams.get('bank_account_id') || ''
  );
  const [fromDate, setFromDate] = useState(
    searchParams.get('from_date') ||
      format(new Date(new Date().getFullYear(), new Date().getMonth(), 1), 'yyyy-MM-dd')
  );
  const [toDate, setToDate] = useState(
    searchParams.get('to_date') || format(new Date(), 'yyyy-MM-dd')
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
        console.error('Failed to fetch bank accounts:', error);
      }
    };
    fetchBankAccounts();
  }, [organizationId]);

  // Fetch workspace data
  const fetchWorkspace = async () => {
    if (!selectedBankAccount || !fromDate || !toDate) return;

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
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to fetch reconciliation data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedBankAccount) {
      fetchWorkspace();
    }
  }, [selectedBankAccount, fromDate, toDate]);

  // Handle statement selection
  const handleSelectStatement = (statement: UnreconciledStatement) => {
    setSelectedStatement(statement);
    setMatchAmount(statement.unreconciled_amount.toFixed(2));
    // Try to find matching book entry
    const amount = statement.credit_amount > 0 ? statement.credit_amount : statement.debit_amount;
    const matchingEntry = workspaceData?.unreconciled_book_entries.find((entry) => {
      const entryAmount =
        statement.credit_amount > 0 ? entry.debit_amount : entry.credit_amount;
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
      const amount = entry.debit_amount > 0 ? entry.debit_amount : entry.credit_amount;
      const matchingStatement = workspaceData?.unreconciled_statements.find((stmt) => {
        const stmtAmount =
          entry.debit_amount > 0 ? stmt.credit_amount : stmt.debit_amount;
        return Math.abs(stmtAmount - amount) < 0.01;
      });
      if (matchingStatement) {
        setSelectedStatement(matchingStatement);
        setMatchAmount(matchingStatement.unreconciled_amount.toFixed(2));
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
        statement_id: selectedStatement.statement_id,
        voucher_id: selectedBookEntry.voucher_id,
        matched_amount: amount,
        match_type: 'MANUAL',
      });
      toast({
        title: 'Success',
        description: 'Match created successfully',
      });
      fetchWorkspace();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to create match',
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
        description: `${response.data.matched_count} matches created`,
      });
      fetchWorkspace();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Auto-match failed',
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
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">Bank Reconciliation</h1>
          <p className="text-sm text-slate-500">
            Match bank statements with book entries
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() =>
            navigate(
              `/admin/ap-ar/bank-reconciliation/brs-report?bank_account_id=${selectedBankAccount}&from_date=${fromDate}&to_date=${toDate}`
            )
          }
        >
          <FileText className="mr-2 h-4 w-4" />
          BRS Report
        </Button>
      </div>

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
              <Input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
              />
            </div>
            <div>
              <Label>To Date</Label>
              <Input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
              />
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
                    {formatAmount(workspaceData.total_unreconciled_bank_credits)}
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
                    {formatAmount(workspaceData.total_unreconciled_bank_debits)}
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
                    {formatAmount(workspaceData.total_unreconciled_book_debits)}
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
                    {formatAmount(workspaceData.total_unreconciled_book_credits)}
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
                        <p className="font-medium">{selectedStatement.reference_number}</p>
                        <p className="text-sm text-slate-500">
                          {format(new Date(selectedStatement.transaction_date), 'dd/MM/yyyy')}
                        </p>
                        <p className="text-sm text-slate-500">{selectedStatement.description}</p>
                      </div>
                      <div className="text-right">
                        <p
                          className={`text-lg font-bold ${
                            selectedStatement.credit_amount > 0
                              ? 'text-green-600'
                              : 'text-red-600'
                          }`}
                        >
                          {formatAmount(selectedStatement.unreconciled_amount)}
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
                        <p className="font-medium">{selectedBookEntry.voucher_number}</p>
                        <p className="text-sm text-slate-500">
                          {format(new Date(selectedBookEntry.voucher_date), 'dd/MM/yyyy')}
                        </p>
                        <p className="text-sm text-slate-500">{selectedBookEntry.narration}</p>
                      </div>
                      <div className="text-right">
                        <p
                          className={`text-lg font-bold ${
                            selectedBookEntry.debit_amount > 0
                              ? 'text-blue-600'
                              : 'text-purple-600'
                          }`}
                        >
                          {formatAmount(
                            selectedBookEntry.debit_amount > 0
                              ? selectedBookEntry.debit_amount
                              : selectedBookEntry.credit_amount
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
              <CardTitle className="text-lg">
                Unreconciled Bank Statements
              </CardTitle>
              <CardDescription>
                {workspaceData.unreconciled_statements.length} items
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
                    {workspaceData.unreconciled_statements.map((statement) => (
                      <TableRow
                        key={statement.statement_id}
                        className={`cursor-pointer hover:bg-slate-50 ${
                          selectedStatement?.statement_id === statement.statement_id
                            ? 'bg-blue-50'
                            : ''
                        }`}
                        onClick={() => handleSelectStatement(statement)}
                      >
                        <TableCell>
                          {format(new Date(statement.transaction_date), 'dd/MM/yyyy')}
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">
                              {statement.reference_number || '-'}
                            </p>
                            <p className="max-w-[200px] truncate text-xs text-slate-500">
                              {statement.description}
                            </p>
                          </div>
                        </TableCell>
                        <TableCell
                          className={`text-right font-medium ${
                            statement.credit_amount > 0
                              ? 'text-green-600'
                              : 'text-red-600'
                          }`}
                        >
                          {statement.credit_amount > 0 ? '+' : '-'}
                          {formatAmount(statement.unreconciled_amount)}
                        </TableCell>
                      </TableRow>
                    ))}
                    {workspaceData.unreconciled_statements.length === 0 && (
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
                {workspaceData.unreconciled_book_entries.length} items
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
                    {workspaceData.unreconciled_book_entries.map((entry) => (
                      <TableRow
                        key={entry.voucher_id}
                        className={`cursor-pointer hover:bg-slate-50 ${
                          selectedBookEntry?.voucher_id === entry.voucher_id
                            ? 'bg-blue-50'
                            : ''
                        }`}
                        onClick={() => handleSelectBookEntry(entry)}
                      >
                        <TableCell>
                          {format(new Date(entry.voucher_date), 'dd/MM/yyyy')}
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{entry.voucher_number}</p>
                            <p className="max-w-[200px] truncate text-xs text-slate-500">
                              {entry.narration}
                            </p>
                          </div>
                        </TableCell>
                        <TableCell
                          className={`text-right font-medium ${
                            entry.debit_amount > 0
                              ? 'text-blue-600'
                              : 'text-purple-600'
                          }`}
                        >
                          {entry.debit_amount > 0 ? 'Dr ' : 'Cr '}
                          {formatAmount(
                            entry.debit_amount > 0
                              ? entry.debit_amount
                              : entry.credit_amount
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                    {workspaceData.unreconciled_book_entries.length === 0 && (
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
