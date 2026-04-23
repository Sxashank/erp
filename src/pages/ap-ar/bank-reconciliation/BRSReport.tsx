import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { format } from 'date-fns';
import {
  ArrowLeft,
  Download,
  ExternalLink,
  FileText,
  Printer,
  RefreshCw,
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
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { bankReconciliationApi, accountsApi } from '@/services/api';

interface BRSReportItem {
  id: string;
  date: string;
  reference: string;
  description: string | null;
  amount: number;
  item_type: string;
}

interface BRSReportData {
  bank_account_id: string;
  bank_account_name: string;
  reconciliation_date: string;
  from_date: string;
  to_date: string;
  statement_opening_balance: number;
  statement_closing_balance: number;
  book_opening_balance: number;
  book_closing_balance: number;
  deposits_in_transit: BRSReportItem[];
  outstanding_cheques: BRSReportItem[];
  credits_in_bank_not_books: BRSReportItem[];
  debits_in_bank_not_books: BRSReportItem[];
  total_deposits_in_transit: number;
  total_outstanding_cheques: number;
  total_credits_not_in_books: number;
  total_debits_not_in_books: number;
  reconciled_balance: number;
  difference: number;
}

interface BankAccount {
  id: string;
  code: string;
  name: string;
}

export function BRSReport() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();

  const organizationId = localStorage.getItem('organization_id') || '';

  // State
  const [bankAccounts, setBankAccounts] = useState<BankAccount[]>([]);
  const [selectedBankAccount, setSelectedBankAccount] = useState(
    searchParams.get('bank_account_id') || ''
  );
  const [reconciliationDate, setReconciliationDate] = useState(
    searchParams.get('reconciliation_date') || format(new Date(), 'yyyy-MM-dd')
  );
  const [fromDate, setFromDate] = useState(
    searchParams.get('from_date') ||
      format(new Date(new Date().getFullYear(), new Date().getMonth(), 1), 'yyyy-MM-dd')
  );
  const [toDate, setToDate] = useState(
    searchParams.get('to_date') || format(new Date(), 'yyyy-MM-dd')
  );
  const [statementOpeningBalance, setStatementOpeningBalance] = useState('0');
  const [statementClosingBalance, setStatementClosingBalance] = useState('0');
  const [bookOpeningBalance, setBookOpeningBalance] = useState('0');
  const [bookClosingBalance, setBookClosingBalance] = useState('0');
  const [loading, setLoading] = useState(false);
  const [reportData, setReportData] = useState<BRSReportData | null>(null);

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

  // Generate report
  const generateReport = async () => {
    if (!selectedBankAccount) {
      toast({
        title: 'Error',
        description: 'Please select a bank account',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);
    try {
      const response = await bankReconciliationApi.getBRSReport({
        bank_account_id: selectedBankAccount,
        reconciliation_date: reconciliationDate,
        from_date: fromDate,
        to_date: toDate,
        statement_opening_balance: parseFloat(statementOpeningBalance) || 0,
        statement_closing_balance: parseFloat(statementClosingBalance) || 0,
        book_opening_balance: parseFloat(bookOpeningBalance) || 0,
        book_closing_balance: parseFloat(bookClosingBalance) || 0,
      });
      setReportData(response.data);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to generate report',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const handlePrint = () => {
    window.print();
  };

  const handleDrillDown = (item: BRSReportItem) => {
    // For book entries (deposits in transit, outstanding cheques), navigate to voucher
    // For bank entries (credits/debits not in books), navigate to reconciliation
    if (item.item_type === 'DEPOSIT_IN_TRANSIT' || item.item_type === 'OUTSTANDING_CHEQUE') {
      navigate(`/admin/finance/vouchers/${item.id}`);
    } else {
      // Navigate to bank reconciliation with focus on the statement
      navigate(`/admin/ap-ar/bank-reconciliation?bank_account_id=${selectedBankAccount}&from_date=${fromDate}&to_date=${toDate}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4 print:hidden">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">Bank Reconciliation Statement</h1>
          <p className="text-sm text-slate-500">
            Generate BRS report for a bank account
          </p>
        </div>
        {reportData && (
          <Button variant="outline" onClick={handlePrint}>
            <Printer className="mr-2 h-4 w-4" />
            Print
          </Button>
        )}
      </div>

      {/* Parameters */}
      <Card className="print:hidden">
        <CardHeader>
          <CardTitle>Report Parameters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-5">
            <div>
              <Label>Bank Account</Label>
              <Select value={selectedBankAccount} onValueChange={setSelectedBankAccount}>
                <SelectTrigger>
                  <SelectValue placeholder="Select bank" />
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
              <Label>Reconciliation Date</Label>
              <Input
                type="date"
                value={reconciliationDate}
                onChange={(e) => setReconciliationDate(e.target.value)}
              />
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
            <div className="flex items-end">
              <Button onClick={generateReport} disabled={loading} className="w-full">
                {loading ? (
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <FileText className="mr-2 h-4 w-4" />
                )}
                Generate
              </Button>
            </div>
          </div>
          <Separator />
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <Label>Statement Opening Balance</Label>
              <Input
                type="number"
                step="0.01"
                value={statementOpeningBalance}
                onChange={(e) => setStatementOpeningBalance(e.target.value)}
              />
            </div>
            <div>
              <Label>Statement Closing Balance</Label>
              <Input
                type="number"
                step="0.01"
                value={statementClosingBalance}
                onChange={(e) => setStatementClosingBalance(e.target.value)}
              />
            </div>
            <div>
              <Label>Book Opening Balance</Label>
              <Input
                type="number"
                step="0.01"
                value={bookOpeningBalance}
                onChange={(e) => setBookOpeningBalance(e.target.value)}
              />
            </div>
            <div>
              <Label>Book Closing Balance</Label>
              <Input
                type="number"
                step="0.01"
                value={bookClosingBalance}
                onChange={(e) => setBookClosingBalance(e.target.value)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Report */}
      {reportData && (
        <Card className="print:border-0 print:shadow-none">
          <CardHeader className="text-center">
            <CardTitle className="text-xl">Bank Reconciliation Statement</CardTitle>
            <CardDescription>
              <p className="font-medium">{reportData.bank_account_name}</p>
              <p>
                Period: {format(new Date(reportData.from_date), 'dd/MM/yyyy')} to{' '}
                {format(new Date(reportData.to_date), 'dd/MM/yyyy')}
              </p>
              <p>
                As on: {format(new Date(reportData.reconciliation_date), 'dd/MM/yyyy')}
              </p>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Balance Summary */}
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-lg border p-4">
                <h3 className="mb-4 font-semibold">As Per Bank Statement</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Opening Balance:</span>
                    <span className="font-medium">
                      {formatAmount(reportData.statement_opening_balance)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Closing Balance:</span>
                    <span className="font-medium">
                      {formatAmount(reportData.statement_closing_balance)}
                    </span>
                  </div>
                </div>
              </div>
              <div className="rounded-lg border p-4">
                <h3 className="mb-4 font-semibold">As Per Books</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Opening Balance:</span>
                    <span className="font-medium">
                      {formatAmount(reportData.book_opening_balance)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Closing Balance:</span>
                    <span className="font-medium">
                      {formatAmount(reportData.book_closing_balance)}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Deposits in Transit */}
            {reportData.deposits_in_transit.length > 0 && (
              <div>
                <h3 className="mb-2 font-semibold">
                  Add: Deposits in Transit (In Books, Not in Bank)
                </h3>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Reference</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {reportData.deposits_in_transit.map((item) => (
                      <TableRow
                        key={item.id}
                        className="cursor-pointer hover:bg-green-100 transition-colors"
                        onClick={() => handleDrillDown(item)}
                      >
                        <TableCell>
                          {format(new Date(item.date), 'dd/MM/yyyy')}
                        </TableCell>
                        <TableCell className="text-blue-600 flex items-center gap-1">
                          {item.reference}
                          <ExternalLink className="h-3 w-3" />
                        </TableCell>
                        <TableCell>{item.description}</TableCell>
                        <TableCell className="text-right">
                          {formatAmount(item.amount)}
                        </TableCell>
                      </TableRow>
                    ))}
                    <TableRow className="bg-slate-50 font-medium">
                      <TableCell colSpan={3}>Total Deposits in Transit</TableCell>
                      <TableCell className="text-right">
                        {formatAmount(reportData.total_deposits_in_transit)}
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>
            )}

            {/* Outstanding Cheques */}
            {reportData.outstanding_cheques.length > 0 && (
              <div>
                <h3 className="mb-2 font-semibold">
                  Less: Outstanding Cheques (In Books, Not in Bank)
                </h3>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Reference</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {reportData.outstanding_cheques.map((item) => (
                      <TableRow
                        key={item.id}
                        className="cursor-pointer hover:bg-red-100 transition-colors"
                        onClick={() => handleDrillDown(item)}
                      >
                        <TableCell>
                          {format(new Date(item.date), 'dd/MM/yyyy')}
                        </TableCell>
                        <TableCell className="text-blue-600 flex items-center gap-1">
                          {item.reference}
                          <ExternalLink className="h-3 w-3" />
                        </TableCell>
                        <TableCell>{item.description}</TableCell>
                        <TableCell className="text-right">
                          {formatAmount(item.amount)}
                        </TableCell>
                      </TableRow>
                    ))}
                    <TableRow className="bg-slate-50 font-medium">
                      <TableCell colSpan={3}>Total Outstanding Cheques</TableCell>
                      <TableCell className="text-right">
                        {formatAmount(reportData.total_outstanding_cheques)}
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>
            )}

            {/* Credits in Bank Not in Books */}
            {reportData.credits_in_bank_not_books.length > 0 && (
              <div>
                <h3 className="mb-2 font-semibold">
                  Add: Credits in Bank, Not in Books
                </h3>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Reference</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {reportData.credits_in_bank_not_books.map((item) => (
                      <TableRow
                        key={item.id}
                        className="cursor-pointer hover:bg-blue-100 transition-colors"
                        onClick={() => handleDrillDown(item)}
                      >
                        <TableCell>
                          {format(new Date(item.date), 'dd/MM/yyyy')}
                        </TableCell>
                        <TableCell className="text-blue-600 flex items-center gap-1">
                          {item.reference}
                          <ExternalLink className="h-3 w-3" />
                        </TableCell>
                        <TableCell>{item.description}</TableCell>
                        <TableCell className="text-right">
                          {formatAmount(item.amount)}
                        </TableCell>
                      </TableRow>
                    ))}
                    <TableRow className="bg-slate-50 font-medium">
                      <TableCell colSpan={3}>Total Credits Not in Books</TableCell>
                      <TableCell className="text-right">
                        {formatAmount(reportData.total_credits_not_in_books)}
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>
            )}

            {/* Debits in Bank Not in Books */}
            {reportData.debits_in_bank_not_books.length > 0 && (
              <div>
                <h3 className="mb-2 font-semibold">
                  Less: Debits in Bank, Not in Books
                </h3>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Reference</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {reportData.debits_in_bank_not_books.map((item) => (
                      <TableRow
                        key={item.id}
                        className="cursor-pointer hover:bg-amber-100 transition-colors"
                        onClick={() => handleDrillDown(item)}
                      >
                        <TableCell>
                          {format(new Date(item.date), 'dd/MM/yyyy')}
                        </TableCell>
                        <TableCell className="text-blue-600 flex items-center gap-1">
                          {item.reference}
                          <ExternalLink className="h-3 w-3" />
                        </TableCell>
                        <TableCell>{item.description}</TableCell>
                        <TableCell className="text-right">
                          {formatAmount(item.amount)}
                        </TableCell>
                      </TableRow>
                    ))}
                    <TableRow className="bg-slate-50 font-medium">
                      <TableCell colSpan={3}>Total Debits Not in Books</TableCell>
                      <TableCell className="text-right">
                        {formatAmount(reportData.total_debits_not_in_books)}
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>
            )}

            {/* Summary */}
            <div className="rounded-lg border bg-slate-50 p-4">
              <h3 className="mb-4 text-lg font-semibold">Reconciliation Summary</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Balance as per Books:</span>
                  <span className="font-medium">
                    {formatAmount(reportData.book_closing_balance)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Add: Deposits in Transit:</span>
                  <span className="font-medium">
                    {formatAmount(reportData.total_deposits_in_transit)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Less: Outstanding Cheques:</span>
                  <span className="font-medium">
                    ({formatAmount(reportData.total_outstanding_cheques)})
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Add: Credits in Bank (Not in Books):</span>
                  <span className="font-medium">
                    {formatAmount(reportData.total_credits_not_in_books)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Less: Debits in Bank (Not in Books):</span>
                  <span className="font-medium">
                    ({formatAmount(reportData.total_debits_not_in_books)})
                  </span>
                </div>
                <Separator className="my-2" />
                <div className="flex justify-between text-lg font-semibold">
                  <span>Reconciled Balance:</span>
                  <span>{formatAmount(reportData.reconciled_balance)}</span>
                </div>
                <div className="flex justify-between text-lg font-semibold">
                  <span>Balance as per Bank Statement:</span>
                  <span>{formatAmount(reportData.statement_closing_balance)}</span>
                </div>
                <Separator className="my-2" />
                <div
                  className={`flex justify-between text-lg font-bold ${
                    Math.abs(reportData.difference) < 1
                      ? 'text-green-600'
                      : 'text-red-600'
                  }`}
                >
                  <span>Difference:</span>
                  <span>{formatAmount(reportData.difference)}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
