import { BookOpen, ExternalLink, FileSpreadsheet, FileText, Filter, Printer, Search } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
import { reportsApi, organizationsApi, accountsApi, financialYearsApi } from '@/services/api';
import type { Account, Organization, FinancialYear } from '@/types';
import { exportAccountLedgerToExcel, exportAccountLedgerToPDF } from '@/utils/exportUtils';

import { logger } from "@/lib/logger";
interface LedgerEntry {
  voucher_id: string;
  voucher_number: string;
  voucher_date: string;
  voucher_type: string;
  narration: string;
  reference_number?: string;
  debit_amount: number;
  credit_amount: number;
  running_balance: number;
  balance_type: string;
}

interface AccountLedgerResponse {
  account_id: string;
  account_code: string;
  account_name: string;
  account_group_name: string;
  from_date: string;
  to_date: string;
  opening_balance: number;
  opening_balance_type: string;
  closing_balance: number;
  closing_balance_type: string;
  total_debit: number;
  total_credit: number;
  entries: LedgerEntry[];
  generated_at: string;
}

export function AccountLedger() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  // Support both accountId and account_id for flexibility
  const accountIdFromUrl = searchParams.get('account_id') || searchParams.get('accountId');
  const fromDateFromUrl = searchParams.get('from_date');
  const toDateFromUrl = searchParams.get('to_date');
  const orgIdFromUrl = searchParams.get('organization_id');

  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [financialYears, setFinancialYears] = useState<FinancialYear[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [selectedFYId, setSelectedFYId] = useState<string>('');
  const [selectedAccountId, setSelectedAccountId] = useState<string>('');
  const [fromDate, setFromDate] = useState<string>('');
  const [toDate, setToDate] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [reportData, setReportData] = useState<AccountLedgerResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [accountsLoading, setAccountsLoading] = useState(false);

  useEffect(() => {
    if (selectedFYId) {
      const fy = financialYears.find(f => f.id === selectedFYId);
      if (fy) {
        setFromDate(fy.start_date);
        setToDate(fy.end_date);
      }
    }
  }, [selectedFYId, financialYears]);

  useEffect(() => {
    // If account ID is passed via URL, set it after accounts are loaded
    if (accountIdFromUrl && accounts.length > 0) {
      const account = accounts.find(a => a.id === accountIdFromUrl);
      if (account) {
        setSelectedAccountId(accountIdFromUrl);
        // Use dates from URL if provided
        if (fromDateFromUrl) setFromDate(fromDateFromUrl);
        if (toDateFromUrl) setToDate(toDateFromUrl);
      }
    }
  }, [accountIdFromUrl, accounts, fromDateFromUrl, toDateFromUrl]);

  const handleVoucherDrillDown = (voucherId: string) => {
    navigate(`/admin/finance/vouchers/${voucherId}`);
  };

  const fetchOrganizations = useCallback(async () => {
    try {
      const response = await organizationsApi.list({ pageSize: 100 });
      setOrganizations(response.data.items);
      if (response.data.items.length > 0) {
        // Use org ID from URL if provided, otherwise use first org
        if (orgIdFromUrl && response.data.items.find((o: Organization) => o.id === orgIdFromUrl)) {
          setSelectedOrgId(orgIdFromUrl);
        } else {
          setSelectedOrgId(response.data.items[0].id);
        }
      }
    } catch (error) {
      logger.error('Failed to fetch organizations:', error);
    }
  }, [orgIdFromUrl]);

  const fetchFinancialYears = useCallback(async () => {
    try {
      const response = await financialYearsApi.list({ pageSize: 100 });
      setFinancialYears(response.data.items);
      const currentFY = response.data.items.find((fy: FinancialYear) => fy.is_current);
      if (currentFY) {
        setSelectedFYId(currentFY.id);
      } else if (response.data.items.length > 0) {
        setSelectedFYId(response.data.items[0].id);
      }
    } catch (error) {
      logger.error('Failed to fetch financial years:', error);
    }
  }, [selectedOrgId]);

  const fetchAccounts = useCallback(async () => {
    try {
      setAccountsLoading(true);
      const response = await accountsApi.list({
        pageSize: 100,
        includeInactive: false,
      });
      setAccounts(response.data.items);
    } catch (error) {
      logger.error('Failed to fetch accounts:', error);
    } finally {
      setAccountsLoading(false);
    }
  }, [selectedOrgId]);

  const generateReport = useCallback(async () => {
    if (!selectedAccountId || !fromDate || !toDate) return;
    try {
      setLoading(true);
      const response = await reportsApi.getAccountLedger(selectedAccountId, {
        from_date: fromDate,
        to_date: toDate,
      });
      setReportData(response.data);
    } catch (error) {
      logger.error('Failed to generate report:', error);
    } finally {
      setLoading(false);
    }
  }, [fromDate, selectedAccountId, toDate]);

  useEffect(() => {
    fetchOrganizations();
  }, [fetchOrganizations]);

  useEffect(() => {
    if (selectedOrgId) {
      fetchFinancialYears();
      fetchAccounts();
    }
  }, [fetchAccounts, fetchFinancialYears, selectedOrgId]);

  // Auto-generate report when coming from drill-down with all parameters
  useEffect(() => {
    if (accountIdFromUrl && selectedAccountId && fromDate && toDate && !reportData) {
      generateReport();
    }
  }, [accountIdFromUrl, fromDate, generateReport, reportData, selectedAccountId, toDate]);

  const formatCurrency = (amount: number) =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(Math.abs(amount));

  const handlePrint = () => {
    window.print();
  };

  const filteredAccounts = searchQuery
    ? accounts.filter(
        a =>
          a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          a.code.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : accounts;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Account Ledger"
        subtitle="View all transactions for an account"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={handlePrint} disabled={!reportData}>
              <Printer className="mr-2 h-4 w-4" />
              Print
            </Button>
            <Button
              variant="outline"
              onClick={() => reportData && exportAccountLedgerToExcel(reportData)}
              disabled={!reportData}
            >
              <FileSpreadsheet className="mr-2 h-4 w-4" />
              Excel
            </Button>
            <Button
              variant="outline"
              onClick={() => reportData && exportAccountLedgerToPDF(reportData)}
              disabled={!reportData}
            >
              <FileText className="mr-2 h-4 w-4" />
              PDF
            </Button>
          </div>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Report Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3 lg:grid-cols-6">
            <div>
              <Label>Organization</Label>
              <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select organization" />
                </SelectTrigger>
                <SelectContent>
                  {organizations.map((org) => (
                    <SelectItem key={org.id} value={org.id}>
                      {org.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Financial Year</Label>
              <Select value={selectedFYId} onValueChange={setSelectedFYId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select FY" />
                </SelectTrigger>
                <SelectContent>
                  {financialYears.map((fy) => (
                    <SelectItem key={fy.id} value={fy.id}>
                      {fy.name} {fy.is_current && '(Current)'}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="lg:col-span-2">
              <Label>Account</Label>
              <div className="relative">
                <Select
                  value={selectedAccountId}
                  onValueChange={setSelectedAccountId}
                  disabled={accountsLoading}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={accountsLoading ? 'Loading...' : 'Select account'} />
                  </SelectTrigger>
                  <SelectContent>
                    <div className="px-2 pb-2">
                      <div className="relative">
                        <Search className="absolute left-2 top-2.5 h-4 w-4 text-slate-400" />
                        <Input
                          placeholder="Search accounts..."
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          className="pl-8"
                        />
                      </div>
                    </div>
                    {filteredAccounts.slice(0, 100).map((account) => (
                      <SelectItem key={account.id} value={account.id}>
                        {account.code} - {account.name}
                      </SelectItem>
                    ))}
                    {filteredAccounts.length === 0 && (
                      <div className="py-2 px-4 text-sm text-slate-500">No accounts found</div>
                    )}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <Label>From Date</Label>
              <Input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
            </div>
            <div>
              <Label>To Date</Label>
              <Input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} />
            </div>
          </div>
          <div className="mt-4 flex justify-end">
            <Button
              onClick={generateReport}
              disabled={loading || !selectedAccountId || !fromDate || !toDate}
            >
              {loading ? 'Generating...' : 'Generate Ledger'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {reportData && (
        <Card className="print:shadow-none">
          <CardHeader className="print:pb-2">
            <div className="text-center">
              <h2 className="text-xl font-bold">{reportData.account_name}</h2>
              <p className="text-sm text-slate-600">
                {reportData.account_code} | {reportData.account_group_name}
              </p>
              <p className="text-sm text-slate-500">
                Ledger for the period <DateDisplay date={reportData.from_date} /> to <DateDisplay date={reportData.to_date} />
              </p>
            </div>
          </CardHeader>
          <CardContent>
            {/* Opening Balance */}
            <div className="mb-4 flex justify-between rounded-lg bg-slate-50 p-4">
              <div>
                <span className="text-sm font-medium text-slate-600">Opening Balance</span>
                <p className="text-lg font-semibold">
                  {formatCurrency(reportData.opening_balance)}{' '}
                  <span className={reportData.opening_balance_type === 'DR' ? 'text-blue-600' : 'text-red-600'}>
                    {reportData.opening_balance_type}
                  </span>
                </p>
              </div>
              <div className="text-right">
                <span className="text-sm font-medium text-slate-600">Closing Balance</span>
                <p className="text-lg font-semibold">
                  {formatCurrency(reportData.closing_balance)}{' '}
                  <span className={reportData.closing_balance_type === 'DR' ? 'text-blue-600' : 'text-red-600'}>
                    {reportData.closing_balance_type}
                  </span>
                </p>
              </div>
            </div>

            {reportData.entries.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8">
                <BookOpen className="mb-4 h-12 w-12 text-slate-300" />
                <p className="text-sm text-slate-500">No transactions found for the selected period</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-50">
                    <TableHead className="w-[100px]">Date</TableHead>
                    <TableHead className="w-[120px]">Voucher No.</TableHead>
                    <TableHead className="w-[100px]">Type</TableHead>
                    <TableHead>Narration</TableHead>
                    <TableHead className="text-right w-[130px]">Debit</TableHead>
                    <TableHead className="text-right w-[130px]">Credit</TableHead>
                    <TableHead className="text-right w-[150px]">Balance</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {/* Opening Balance Row */}
                  <TableRow className="bg-slate-50 font-medium">
                    <TableCell><DateDisplay date={reportData.from_date} /></TableCell>
                    <TableCell>-</TableCell>
                    <TableCell>-</TableCell>
                    <TableCell>Opening Balance</TableCell>
                    <TableCell className="text-right font-mono">-</TableCell>
                    <TableCell className="text-right font-mono">-</TableCell>
                    <TableCell className="text-right font-mono">
                      {formatCurrency(reportData.opening_balance)}{' '}
                      <span className={reportData.opening_balance_type === 'DR' ? 'text-blue-600' : 'text-red-600'}>
                        {reportData.opening_balance_type}
                      </span>
                    </TableCell>
                  </TableRow>
                  {reportData.entries.map((entry, index) => (
                    <TableRow key={entry.voucher_id + '-' + index} className="hover:bg-slate-50">
                      <TableCell className="font-mono text-sm">
                        <DateDisplay date={entry.voucher_date} />
                      </TableCell>
                      <TableCell
                        className="font-medium text-blue-600 cursor-pointer hover:underline"
                        onClick={() => handleVoucherDrillDown(entry.voucher_id)}
                      >
                        <span className="flex items-center gap-1">
                          {entry.voucher_number}
                          <ExternalLink className="h-3 w-3 opacity-50" />
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="inline-flex items-center rounded px-2 py-0.5 text-xs font-medium bg-slate-100 text-slate-700">
                          {entry.voucher_type}
                        </span>
                      </TableCell>
                      <TableCell className="max-w-[300px] truncate" title={entry.narration}>
                        {entry.narration || '-'}
                        {entry.reference_number && (
                          <span className="ml-1 text-slate-400 text-xs">
                            (Ref: {entry.reference_number})
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {entry.debit_amount > 0 ? formatCurrency(entry.debit_amount) : '-'}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {entry.credit_amount > 0 ? formatCurrency(entry.credit_amount) : '-'}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {formatCurrency(entry.running_balance)}{' '}
                        <span className={entry.balance_type === 'DR' ? 'text-blue-600' : 'text-red-600'}>
                          {entry.balance_type}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                  {/* Closing Balance / Totals Row */}
                  <TableRow className="bg-slate-100 font-bold">
                    <TableCell colSpan={4}>TOTAL / Closing Balance</TableCell>
                    <TableCell className="text-right font-mono text-blue-600">
                      {formatCurrency(reportData.total_debit)}
                    </TableCell>
                    <TableCell className="text-right font-mono text-red-600">
                      {formatCurrency(reportData.total_credit)}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {formatCurrency(reportData.closing_balance)}{' '}
                      <span className={reportData.closing_balance_type === 'DR' ? 'text-blue-600' : 'text-red-600'}>
                        {reportData.closing_balance_type}
                      </span>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            )}

            <div className="mt-4 flex justify-between text-xs text-slate-500 print:mt-8">
              <span>
                Transactions: {reportData.entries.length} | Total Debit: {formatCurrency(reportData.total_debit)} | Total Credit: {formatCurrency(reportData.total_credit)}
              </span>
              <span>Generated on: {new Date(reportData.generated_at).toLocaleString('en-IN')}</span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
