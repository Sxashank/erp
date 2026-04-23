/**
 * Account Aggregator Fetched Data Page
 *
 * Full page view for browsing fetched bank accounts and transactions.
 * Supports filtering by entity, FI type, and date range.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { format } from 'date-fns';
import {
  ArrowLeft,
  Search,
  Filter,
  Building2,
  CreditCard,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Calendar,
  Download,
  ChevronRight,
  RefreshCw,
  Wallet,
  PiggyBank,
  BarChart3,
  ArrowUpRight,
  ArrowDownLeft,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';

// Types
interface BankAccount {
  id: string;
  fetch_session_id: string;
  consent_id: string;
  entity_id: string | null;
  entity_name: string | null;
  fi_type: string;
  fip_id: string;
  fip_name: string;
  link_ref_number: string;
  masked_account_number: string;
  account_type: string;
  ifsc_code: string;
  bank_name: string;
  branch: string | null;
  holder_name: string;
  nominee: string | null;
  current_balance: number;
  available_balance: number | null;
  currency: string;
  balance_as_on: string;
  transactions_count: number;
  fetched_at: string;
}

interface Transaction {
  id: string;
  txn_id: string;
  txn_type: string;
  mode: string;
  amount: number;
  current_balance: number | null;
  txn_date: string;
  value_date: string | null;
  narration: string;
  reference: string | null;
  category: string | null;
}

interface PaginationInfo {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

// Format currency
const formatCurrency = (amount: number, currency: string = 'INR') => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: currency,
    maximumFractionDigits: 2,
  }).format(amount);
};

// Account type icons
const getAccountTypeIcon = (type: string) => {
  switch (type?.toUpperCase()) {
    case 'SAVINGS':
      return <PiggyBank className="h-4 w-4" />;
    case 'CURRENT':
      return <Wallet className="h-4 w-4" />;
    case 'FIXED_DEPOSIT':
    case 'TERM_DEPOSIT':
      return <Building2 className="h-4 w-4" />;
    default:
      return <CreditCard className="h-4 w-4" />;
  }
};

// FI Type badge
const getFiTypeBadge = (fiType: string) => {
  const styles: Record<string, string> = {
    DEPOSIT: 'bg-blue-100 text-blue-800',
    TERM_DEPOSIT: 'bg-purple-100 text-purple-800',
    RECURRING_DEPOSIT: 'bg-indigo-100 text-indigo-800',
    MUTUAL_FUNDS: 'bg-green-100 text-green-800',
    EQUITIES: 'bg-orange-100 text-orange-800',
    INSURANCE_POLICIES: 'bg-cyan-100 text-cyan-800',
  };

  return (
    <Badge className={styles[fiType] || 'bg-gray-100 text-gray-800'} variant="outline">
      {fiType.replace(/_/g, ' ')}
    </Badge>
  );
};

export default function FetchedDataPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { toast } = useToast();

  // State
  const [loading, setLoading] = useState(true);
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [pagination, setPagination] = useState<PaginationInfo>({
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0,
  });

  // Selected account for transactions view
  const [selectedAccount, setSelectedAccount] = useState<BankAccount | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loadingTransactions, setLoadingTransactions] = useState(false);
  const [txnPagination, setTxnPagination] = useState<PaginationInfo>({
    page: 1,
    page_size: 50,
    total: 0,
    total_pages: 0,
  });

  // Filters
  const [filters, setFilters] = useState({
    search: searchParams.get('search') || '',
    fi_type: searchParams.get('fi_type') || '',
    entity_id: searchParams.get('entity_id') || '',
    organization_id: searchParams.get('organization_id') || '',
  });

  // Summary stats
  const [stats, setStats] = useState({
    total_accounts: 0,
    total_balance: 0,
    unique_banks: 0,
    total_transactions: 0,
  });

  // Fetch bank accounts
  const fetchAccounts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('page', pagination.page.toString());
      params.set('page_size', pagination.page_size.toString());
      if (filters.organization_id) params.set('organization_id', filters.organization_id);
      if (filters.entity_id) params.set('entity_id', filters.entity_id);
      if (filters.fi_type) params.set('fi_type', filters.fi_type);

      const response = await fetch(`/api/v1/lending/aa/bank-accounts?${params}`);
      if (!response.ok) throw new Error('Failed to fetch accounts');

      const data = await response.json();
      setAccounts(data.items || []);
      setPagination(prev => ({
        ...prev,
        total: data.total || 0,
        total_pages: data.total_pages || 0,
      }));

      // Calculate stats
      const uniqueBanks = new Set(data.items?.map((a: BankAccount) => a.bank_name) || []);
      setStats({
        total_accounts: data.total || 0,
        total_balance: data.items?.reduce((sum: number, a: BankAccount) => sum + (a.current_balance || 0), 0) || 0,
        unique_banks: uniqueBanks.size,
        total_transactions: data.items?.reduce((sum: number, a: BankAccount) => sum + (a.transactions_count || 0), 0) || 0,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load bank accounts.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  // Fetch transactions for selected account
  const fetchTransactions = async (accountId: string, page: number = 1) => {
    setLoadingTransactions(true);
    try {
      const params = new URLSearchParams();
      params.set('page', page.toString());
      params.set('page_size', '50');

      const response = await fetch(`/api/v1/lending/aa/bank-accounts/${accountId}/transactions?${params}`);
      if (!response.ok) throw new Error('Failed to fetch transactions');

      const data = await response.json();
      setTransactions(data.items || []);
      setTxnPagination({
        page,
        page_size: 50,
        total: data.total || 0,
        total_pages: data.total_pages || 0,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load transactions.',
        variant: 'destructive',
      });
    } finally {
      setLoadingTransactions(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, [pagination.page, filters.fi_type, filters.entity_id, filters.organization_id]);

  // Handle account selection
  const handleAccountSelect = (account: BankAccount) => {
    setSelectedAccount(account);
    fetchTransactions(account.id);
  };

  // Handle filter changes
  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, page: 1 }));

    // Update URL params
    const params = new URLSearchParams(searchParams);
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    setSearchParams(params);
  };

  if (loading && accounts.length === 0) {
    return (
      <div className="container mx-auto py-6 space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate('/lending/aa/consents')}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Fetched Financial Data</h1>
            <p className="text-sm text-muted-foreground">
              Bank accounts and transactions from Account Aggregator
            </p>
          </div>
        </div>
        <Button variant="outline" onClick={fetchAccounts}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Accounts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <CreditCard className="h-5 w-5 text-muted-foreground" />
              <span className="text-2xl font-bold">{stats.total_accounts}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Balance</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-muted-foreground" />
              <span className="text-2xl font-bold">{formatCurrency(stats.total_balance)}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Unique Banks</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Building2 className="h-5 w-5 text-muted-foreground" />
              <span className="text-2xl font-bold">{stats.unique_banks}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Transactions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-muted-foreground" />
              <span className="text-2xl font-bold">{stats.total_transactions}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex-1 min-w-[200px]">
              <Label htmlFor="search" className="sr-only">Search</Label>
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="search"
                  placeholder="Search accounts..."
                  value={filters.search}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>

            <div className="w-[180px]">
              <Label htmlFor="fi_type" className="sr-only">FI Type</Label>
              <Select
                value={filters.fi_type}
                onValueChange={(value) => handleFilterChange('fi_type', value)}
              >
                <SelectTrigger id="fi_type">
                  <SelectValue placeholder="All FI Types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All FI Types</SelectItem>
                  <SelectItem value="DEPOSIT">Deposit</SelectItem>
                  <SelectItem value="TERM_DEPOSIT">Term Deposit</SelectItem>
                  <SelectItem value="RECURRING_DEPOSIT">Recurring Deposit</SelectItem>
                  <SelectItem value="MUTUAL_FUNDS">Mutual Funds</SelectItem>
                  <SelectItem value="EQUITIES">Equities</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button variant="outline" size="icon">
              <Download className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Accounts List */}
        <div className="lg:col-span-1 space-y-4">
          <h2 className="text-lg font-semibold">Bank Accounts</h2>
          {accounts.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <CreditCard className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No accounts found</p>
                <Button
                  variant="outline"
                  className="mt-4"
                  onClick={() => navigate('/lending/aa/consents')}
                >
                  View Consents
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {accounts.map((account) => (
                <Card
                  key={account.id}
                  className={`cursor-pointer transition-colors hover:bg-muted/50 ${
                    selectedAccount?.id === account.id ? 'ring-2 ring-primary' : ''
                  }`}
                  onClick={() => handleAccountSelect(account)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <div className="p-2 rounded-full bg-muted">
                          {getAccountTypeIcon(account.account_type)}
                        </div>
                        <div>
                          <p className="font-medium text-sm">{account.bank_name}</p>
                          <p className="text-xs text-muted-foreground font-mono">
                            {account.masked_account_number}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {account.holder_name}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-sm">
                          {formatCurrency(account.current_balance, account.currency)}
                        </p>
                        {getFiTypeBadge(account.fi_type)}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Pagination */}
          {pagination.total_pages > 1 && (
            <div className="flex items-center justify-between pt-4">
              <Button
                variant="outline"
                size="sm"
                disabled={pagination.page <= 1}
                onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {pagination.page} of {pagination.total_pages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={pagination.page >= pagination.total_pages}
                onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
              >
                Next
              </Button>
            </div>
          )}
        </div>

        {/* Account Details & Transactions */}
        <div className="lg:col-span-2">
          {selectedAccount ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      {getAccountTypeIcon(selectedAccount.account_type)}
                      {selectedAccount.bank_name}
                    </CardTitle>
                    <CardDescription>
                      {selectedAccount.masked_account_number} • {selectedAccount.ifsc_code}
                    </CardDescription>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold">
                      {formatCurrency(selectedAccount.current_balance, selectedAccount.currency)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      as on {format(new Date(selectedAccount.balance_as_on), 'dd MMM yyyy')}
                    </p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="transactions">
                  <TabsList>
                    <TabsTrigger value="transactions">
                      Transactions ({selectedAccount.transactions_count})
                    </TabsTrigger>
                    <TabsTrigger value="details">Account Details</TabsTrigger>
                  </TabsList>

                  <TabsContent value="transactions" className="mt-4">
                    {loadingTransactions ? (
                      <div className="space-y-2">
                        <Skeleton className="h-12" />
                        <Skeleton className="h-12" />
                        <Skeleton className="h-12" />
                      </div>
                    ) : transactions.length === 0 ? (
                      <div className="text-center py-8">
                        <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                        <p className="text-muted-foreground">No transactions found</p>
                      </div>
                    ) : (
                      <>
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Date</TableHead>
                              <TableHead>Description</TableHead>
                              <TableHead>Mode</TableHead>
                              <TableHead className="text-right">Amount</TableHead>
                              <TableHead className="text-right">Balance</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {transactions.map((txn) => (
                              <TableRow key={txn.id}>
                                <TableCell className="text-xs">
                                  {format(new Date(txn.txn_date), 'dd MMM yyyy')}
                                </TableCell>
                                <TableCell>
                                  <p className="text-sm truncate max-w-[200px]" title={txn.narration}>
                                    {txn.narration}
                                  </p>
                                  {txn.reference && (
                                    <p className="text-xs text-muted-foreground font-mono">
                                      {txn.reference}
                                    </p>
                                  )}
                                </TableCell>
                                <TableCell>
                                  <Badge variant="outline" className="text-xs">
                                    {txn.mode}
                                  </Badge>
                                </TableCell>
                                <TableCell className="text-right">
                                  <span className={`flex items-center justify-end gap-1 font-medium ${
                                    txn.txn_type === 'CREDIT' ? 'text-green-600' : 'text-red-600'
                                  }`}>
                                    {txn.txn_type === 'CREDIT' ? (
                                      <ArrowDownLeft className="h-3 w-3" />
                                    ) : (
                                      <ArrowUpRight className="h-3 w-3" />
                                    )}
                                    {formatCurrency(txn.amount)}
                                  </span>
                                </TableCell>
                                <TableCell className="text-right text-sm">
                                  {txn.current_balance != null
                                    ? formatCurrency(txn.current_balance)
                                    : '-'}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>

                        {/* Transaction Pagination */}
                        {txnPagination.total_pages > 1 && (
                          <div className="flex items-center justify-between mt-4">
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={txnPagination.page <= 1}
                              onClick={() => fetchTransactions(selectedAccount.id, txnPagination.page - 1)}
                            >
                              Previous
                            </Button>
                            <span className="text-sm text-muted-foreground">
                              Page {txnPagination.page} of {txnPagination.total_pages}
                            </span>
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={txnPagination.page >= txnPagination.total_pages}
                              onClick={() => fetchTransactions(selectedAccount.id, txnPagination.page + 1)}
                            >
                              Next
                            </Button>
                          </div>
                        )}
                      </>
                    )}
                  </TabsContent>

                  <TabsContent value="details" className="mt-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Account Type</p>
                        <p className="font-medium">{selectedAccount.account_type}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">FI Type</p>
                        <p className="font-medium">{selectedAccount.fi_type}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">FIP Name</p>
                        <p className="font-medium">{selectedAccount.fip_name || selectedAccount.fip_id}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Branch</p>
                        <p className="font-medium">{selectedAccount.branch || '-'}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Account Holder</p>
                        <p className="font-medium">{selectedAccount.holder_name}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Nominee</p>
                        <p className="font-medium">{selectedAccount.nominee || '-'}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Available Balance</p>
                        <p className="font-medium">
                          {selectedAccount.available_balance != null
                            ? formatCurrency(selectedAccount.available_balance, selectedAccount.currency)
                            : '-'}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Fetched At</p>
                        <p className="font-medium">
                          {format(new Date(selectedAccount.fetched_at), 'dd MMM yyyy HH:mm')}
                        </p>
                      </div>
                      {selectedAccount.entity_name && (
                        <div className="col-span-2">
                          <p className="text-sm text-muted-foreground">Linked Entity</p>
                          <p className="font-medium">{selectedAccount.entity_name}</p>
                        </div>
                      )}
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-24">
                <CreditCard className="h-16 w-16 text-muted-foreground mb-4" />
                <p className="text-lg font-medium">Select an account</p>
                <p className="text-sm text-muted-foreground">
                  Choose a bank account from the list to view details and transactions
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
