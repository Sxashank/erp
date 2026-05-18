/**
 * Account Aggregator Fetched Data Page
 *
 * Full page view for browsing fetched bank accounts and transactions.
 * Supports filtering by entity, FI type, and date range.
 */

import { format } from 'date-fns';
import {
  Search,
  Building2,
  CreditCard,
  DollarSign,
  Download,
  RefreshCw,
  Wallet,
  PiggyBank,
  BarChart3,
  ArrowUpRight,
  ArrowDownLeft,
} from 'lucide-react';
import React, { useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
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
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  useAAAccountTransactions,
  useAABankAccounts,
} from '@/hooks/lending/useAABankAccounts';
import type { BankAccount } from '@/services/lending/aaApi';

// Format currency
const formatCurrency = (amount: number, currency = 'INR') => {
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

  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Selected account for transactions view
  const [selectedAccount, setSelectedAccount] = useState<BankAccount | null>(null);
  const [txnPage, setTxnPage] = useState(1);
  const txnPageSize = 50;

  // Filters
  const [filters, setFilters] = useState({
    search: searchParams.get('search') || '',
    fiType: searchParams.get('fi_type') || '',
    entityId: searchParams.get('entity_id') || '',
    organizationId: searchParams.get('organization_id') || '',
  });

  const accountsQuery = useAABankAccounts({
    organizationId: filters.organizationId || undefined,
    entityId: filters.entityId || undefined,
    fiType: filters.fiType || undefined,
    page,
    pageSize,
  });
  const transactionsQuery = useAAAccountTransactions(
    selectedAccount?.id,
    { page: txnPage, pageSize: txnPageSize },
  );

  const accounts = accountsQuery.data?.items ?? [];
  const transactions = transactionsQuery.data?.items ?? [];

  const totalAccounts = accountsQuery.data?.total ?? 0;
  const totalPages = accountsQuery.data
    ? Math.max(1, Math.ceil(accountsQuery.data.total / pageSize))
    : 0;
  const txnTotalPages = transactionsQuery.data
    ? Math.max(1, Math.ceil(transactionsQuery.data.total / txnPageSize))
    : 0;

  // Summary stats — derived from the current page of accounts (matches the
  // pre-rewrite behaviour, where stats reflected the most recent fetch).
  const stats = useMemo(() => {
    const uniqueBanks = new Set(accounts.map((a) => a.bankName));
    return {
      totalAccounts,
      totalBalance: accounts.reduce((sum, a) => sum + (a.currentBalance || 0), 0),
      uniqueBanks: uniqueBanks.size,
      totalTransactions: accounts.reduce((sum, a) => sum + (a.transactionsCount || 0), 0),
    };
  }, [accounts, totalAccounts]);

  const handleAccountSelect = (account: BankAccount) => {
    setSelectedAccount(account);
    setTxnPage(1);
  };

  // Handle filter changes
  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(1);

    // Update URL params
    const params = new URLSearchParams(searchParams);
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    setSearchParams(params);
  };

  const loadingTransactions = transactionsQuery.isLoading || transactionsQuery.isFetching;

  if (accountsQuery.isLoading && accounts.length === 0) {
    return (
      <div className="container mx-auto space-y-6 py-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (accountsQuery.isError && accounts.length === 0) {
    return (
      <div className="container mx-auto space-y-6 py-6">
        <ErrorState
          title="Could not load bank accounts"
          error={accountsQuery.error}
          onRetry={() => accountsQuery.refetch()}
        />
      </div>
    );
  }

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Fetched Financial Data"
        subtitle="Bank accounts and transactions from Account Aggregator"
        breadcrumbs={[
          { label: 'AA Consents', to: '/admin/lending/aa/consents' },
          { label: 'Fetched Data' },
        ]}
        actions={
          <Button
            variant="outline"
            onClick={() => accountsQuery.refetch()}
            disabled={accountsQuery.isFetching}
          >
            <RefreshCw
              className={`mr-2 h-4 w-4 ${accountsQuery.isFetching ? 'animate-spin' : ''}`}
            />
            Refresh
          </Button>
        }
      />

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Accounts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <CreditCard className="h-5 w-5 text-muted-foreground" />
              <span className="text-2xl font-bold">{stats.totalAccounts}</span>
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
              <span className="text-2xl font-bold">{formatCurrency(stats.totalBalance)}</span>
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
              <span className="text-2xl font-bold">{stats.uniqueBanks}</span>
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
              <span className="text-2xl font-bold">{stats.totalTransactions}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-end gap-4">
            <div className="min-w-[200px] flex-1">
              <Label htmlFor="search" className="sr-only">
                Search
              </Label>
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
              <Label htmlFor="fi_type" className="sr-only">
                FI Type
              </Label>
              <Select
                value={filters.fiType || '__all__'}
                onValueChange={(value) =>
                  handleFilterChange('fiType', value === '__all__' ? '' : value)
                }
              >
                <SelectTrigger id="fi_type">
                  <SelectValue placeholder="All FI Types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__all__">All FI Types</SelectItem>
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
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Accounts List */}
        <div className="space-y-4 lg:col-span-1">
          <h2 className="text-lg font-semibold">Bank Accounts</h2>
          {accounts.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <CreditCard className="mb-4 h-12 w-12 text-muted-foreground" />
                <p className="text-muted-foreground">No accounts found</p>
                <Button
                  variant="outline"
                  className="mt-4"
                  onClick={() => navigate('/admin/lending/aa/consents')}
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
                        <div className="rounded-full bg-muted p-2">
                          {getAccountTypeIcon(account.accountType)}
                        </div>
                        <div>
                          <p className="text-sm font-medium">{account.bankName}</p>
                          <p className="font-mono text-xs text-muted-foreground">
                            {account.maskedAccountNumber}
                          </p>
                          <p className="text-xs text-muted-foreground">{account.holderName}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold">
                          {formatCurrency(account.currentBalance, account.currency)}
                        </p>
                        {getFiTypeBadge(account.fiType)}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
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
                      {getAccountTypeIcon(selectedAccount.accountType)}
                      {selectedAccount.bankName}
                    </CardTitle>
                    <CardDescription>
                      {selectedAccount.maskedAccountNumber} • {selectedAccount.ifscCode}
                    </CardDescription>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold">
                      {formatCurrency(selectedAccount.currentBalance, selectedAccount.currency)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      as on {format(new Date(selectedAccount.balanceAsOn), 'dd MMM yyyy')}
                    </p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="transactions">
                  <TabsList>
                    <TabsTrigger value="transactions">
                      Transactions ({selectedAccount.transactionsCount})
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
                      <div className="py-8 text-center">
                        <BarChart3 className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
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
                                  {format(new Date(txn.txnDate), 'dd MMM yyyy')}
                                </TableCell>
                                <TableCell>
                                  <p
                                    className="max-w-[200px] truncate text-sm"
                                    title={txn.narration}
                                  >
                                    {txn.narration}
                                  </p>
                                  {txn.reference && (
                                    <p className="font-mono text-xs text-muted-foreground">
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
                                  <span
                                    className={`flex items-center justify-end gap-1 font-medium ${
                                      txn.txnType === 'CREDIT' ? 'text-green-600' : 'text-red-600'
                                    }`}
                                  >
                                    {txn.txnType === 'CREDIT' ? (
                                      <ArrowDownLeft className="h-3 w-3" />
                                    ) : (
                                      <ArrowUpRight className="h-3 w-3" />
                                    )}
                                    {formatCurrency(txn.amount)}
                                  </span>
                                </TableCell>
                                <TableCell className="text-right text-sm">
                                  {txn.currentBalance != null
                                    ? formatCurrency(txn.currentBalance)
                                    : '-'}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>

                        {/* Transaction Pagination */}
                        {txnTotalPages > 1 && (
                          <div className="mt-4 flex items-center justify-between">
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={txnPage <= 1}
                              onClick={() => setTxnPage((p) => Math.max(1, p - 1))}
                            >
                              Previous
                            </Button>
                            <span className="text-sm text-muted-foreground">
                              Page {txnPage} of {txnTotalPages}
                            </span>
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={txnPage >= txnTotalPages}
                              onClick={() => setTxnPage((p) => p + 1)}
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
                        <p className="font-medium">{selectedAccount.accountType}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">FI Type</p>
                        <p className="font-medium">{selectedAccount.fiType}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">FIP Name</p>
                        <p className="font-medium">
                          {selectedAccount.fipName || selectedAccount.fipId}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Branch</p>
                        <p className="font-medium">{selectedAccount.branch || '-'}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Account Holder</p>
                        <p className="font-medium">{selectedAccount.holderName}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Nominee</p>
                        <p className="font-medium">{selectedAccount.nominee || '-'}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Available Balance</p>
                        <p className="font-medium">
                          {selectedAccount.availableBalance != null
                            ? formatCurrency(
                                selectedAccount.availableBalance,
                                selectedAccount.currency,
                              )
                            : '-'}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Fetched At</p>
                        <p className="font-medium">
                          {format(new Date(selectedAccount.fetchedAt), 'dd MMM yyyy HH:mm')}
                        </p>
                      </div>
                      {selectedAccount.entityName && (
                        <div className="col-span-2">
                          <p className="text-sm text-muted-foreground">Linked Entity</p>
                          <p className="font-medium">{selectedAccount.entityName}</p>
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
                <CreditCard className="mb-4 h-16 w-16 text-muted-foreground" />
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
