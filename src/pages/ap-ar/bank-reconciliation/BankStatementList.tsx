import { format } from 'date-fns';
import {
  ArrowDownCircle,
  ArrowUpCircle,
  FileSpreadsheet,
  RefreshCw,
  Search,
  Trash2,
  Upload,
  X,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

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
interface BankStatement {
  id: string;
  transactionDate: string;
  valueDate: string;
  referenceNumber: string | null;
  description: string | null;
  transactionType: 'CREDIT' | 'DEBIT';
  debitAmount: number;
  creditAmount: number;
  runningBalance: number | null;
  reconciliationStatus: 'UNRECONCILED' | 'MATCHED' | 'PARTIALLY_MATCHED' | 'RECONCILED';
  reconciledAmount: number;
  unreconciledAmount: number;
}

interface BankAccount {
  id: string;
  code: string;
  name: string;
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

const reconciliationStatusColors: Record<string, string> = {
  UNRECONCILED: 'bg-red-100 text-red-800',
  MATCHED: 'bg-blue-100 text-blue-800',
  PARTIALLY_MATCHED: 'bg-yellow-100 text-yellow-800',
  RECONCILED: 'bg-green-100 text-green-800',
};

const reconciliationStatusLabels: Record<string, string> = {
  UNRECONCILED: 'Unreconciled',
  MATCHED: 'Matched',
  PARTIALLY_MATCHED: 'Partial',
  RECONCILED: 'Reconciled',
};

export function BankStatementList() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { toast } = useToast();

  const organizationId = useActiveOrganizationId() || '';

  // State
  const [statements, setStatements] = useState<BankStatement[]>([]);
  const [bankAccounts, setBankAccounts] = useState<BankAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [selectedBankAccount, setSelectedBankAccount] = useState(searchParams.get('bank_account_id') || '');
  const [selectedStatus, setSelectedStatus] = useState(searchParams.get('status') || 'all');
  const [selectedType, setSelectedType] = useState(searchParams.get('type') || 'all');
  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '');
  const [fromDate, setFromDate] = useState(searchParams.get('from_date') || '');
  const [toDate, setToDate] = useState(searchParams.get('to_date') || '');
  const [page, setPage] = useState(parseInt(searchParams.get('page') || '1', 10));
  const pageSize = 20;

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
        // Auto-select first bank account if none selected
        if (!selectedBankAccount && response.data.items?.length > 0) {
          setSelectedBankAccount(response.data.items[0].id);
        }
      } catch (error) {
        logger.error('Failed to fetch bank accounts:', error);
      }
    };
    fetchBankAccounts();
  }, [organizationId, selectedBankAccount]);

  // Fetch statements
  useEffect(() => {
    const fetchStatements = async () => {
      if (!organizationId || !selectedBankAccount) {
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const params: Parameters<typeof bankReconciliationApi.listStatements>[0] = {
          bank_account_id: selectedBankAccount,
          organization_id: organizationId,
          skip: (page - 1) * pageSize,
          limit: pageSize,
        };

        if (selectedStatus !== 'all') {
          params.reconciliation_status = selectedStatus;
        }
        if (selectedType !== 'all') {
          params.transaction_type = selectedType;
        }
        if (searchQuery) {
          params.search = searchQuery;
        }
        if (fromDate) {
          params.from_date = fromDate;
        }
        if (toDate) {
          params.to_date = toDate;
        }

        const response = await bankReconciliationApi.listStatements(params);
        setStatements(response.data.items || []);
        setTotal(response.data.total || 0);
      } catch (error) {
        logger.error('Failed to fetch statements:', error);
        toast({
          title: 'Error',
          description: 'Failed to fetch bank statements',
          variant: 'destructive',
        });
      } finally {
        setLoading(false);
      }
    };
    fetchStatements();
  }, [
    selectedBankAccount,
    selectedStatus,
    selectedType,
    searchQuery,
    fromDate,
    toDate,
    page,
    organizationId,
    toast,
  ]);

  // Update URL params
  useEffect(() => {
    const params = new URLSearchParams();
    if (selectedBankAccount) params.set('bank_account_id', selectedBankAccount);
    if (selectedStatus !== 'all') params.set('status', selectedStatus);
    if (selectedType !== 'all') params.set('type', selectedType);
    if (searchQuery) params.set('search', searchQuery);
    if (fromDate) params.set('from_date', fromDate);
    if (toDate) params.set('to_date', toDate);
    if (page > 1) params.set('page', page.toString());
    setSearchParams(params);
  }, [
    selectedBankAccount,
    selectedStatus,
    selectedType,
    searchQuery,
    fromDate,
    toDate,
    page,
    setSearchParams,
  ]);

  const handleDeleteStatement = async (id: string) => {
    if (!confirm('Are you sure you want to delete this statement?')) return;

    try {
      await bankReconciliationApi.deleteStatement(id);
      toast({
        title: 'Success',
        description: 'Bank statement deleted successfully',
      });
      // Refresh list
      setStatements((prev) => prev.filter((s) => s.id !== id));
      setTotal((prev) => prev - 1);
    } catch (error: unknown) {
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to delete statement'),
        variant: 'destructive',
      });
    }
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Bank Statements"
        subtitle="Import and manage bank statements for reconciliation"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigate('/admin/ap-ar/bank-reconciliation/import')}>
              <Upload className="mr-2 h-4 w-4" />
              Import Statement
            </Button>
            <Button onClick={() => navigate(`/admin/ap-ar/bank-reconciliation/reconcile?bank_account_id=${selectedBankAccount}`)}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Reconcile
            </Button>
          </div>
        }
      />

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid gap-4 md:grid-cols-6">
            <div className="md:col-span-2">
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
            <div>
              <Label>Status</Label>
              <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="UNRECONCILED">Unreconciled</SelectItem>
                  <SelectItem value="MATCHED">Matched</SelectItem>
                  <SelectItem value="PARTIALLY_MATCHED">Partial</SelectItem>
                  <SelectItem value="RECONCILED">Reconciled</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Type</Label>
              <Select value={selectedType} onValueChange={setSelectedType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="CREDIT">Credits</SelectItem>
                  <SelectItem value="DEBIT">Debits</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="mt-4 flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input
                placeholder="Search by reference, description, cheque number..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button
              variant="ghost"
              onClick={() => {
                setSearchQuery('');
                setFromDate('');
                setToDate('');
                setSelectedStatus('all');
                setSelectedType('all');
                setPage(1);
              }}
            >
              <X className="mr-2 h-4 w-4" />
              Clear
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Statements Table */}
      <Card>
        <CardHeader>
          <CardTitle>Bank Statements</CardTitle>
          <CardDescription>
            {total} statement{total !== 1 ? 's' : ''} found
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex h-48 items-center justify-center">
              <RefreshCw className="h-8 w-8 animate-spin text-slate-400" />
            </div>
          ) : statements.length === 0 ? (
            <div className="flex h-48 flex-col items-center justify-center text-slate-500">
              <FileSpreadsheet className="mb-4 h-12 w-12" />
              <p>No bank statements found</p>
              <Button
                variant="link"
                onClick={() => navigate('/admin/ap-ar/bank-reconciliation/import')}
              >
                Import bank statement
              </Button>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Reference</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead className="text-right">Debit</TableHead>
                    <TableHead className="text-right">Credit</TableHead>
                    <TableHead className="text-right">Balance</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Reconciled</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {statements.map((statement) => (
                    <TableRow key={statement.id}>
                      <TableCell>
                        {format(new Date(statement.transactionDate), 'dd/MM/yyyy')}
                      </TableCell>
                      <TableCell className="font-medium">
                        {statement.referenceNumber || '-'}
                      </TableCell>
                      <TableCell className="max-w-xs truncate">
                        {statement.description || '-'}
                      </TableCell>
                      <TableCell>
                        {statement.transactionType === 'CREDIT' ? (
                          <Badge variant="outline" className="bg-green-50 text-green-700">
                            <ArrowDownCircle className="mr-1 h-3 w-3" />
                            Credit
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="bg-red-50 text-red-700">
                            <ArrowUpCircle className="mr-1 h-3 w-3" />
                            Debit
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right text-red-600">
                        {statement.debitAmount > 0 ? formatAmount(statement.debitAmount) : '-'}
                      </TableCell>
                      <TableCell className="text-right text-green-600">
                        {statement.creditAmount > 0 ? formatAmount(statement.creditAmount) : '-'}
                      </TableCell>
                      <TableCell className="text-right">
                        {statement.runningBalance !== null
                          ? formatAmount(statement.runningBalance)
                          : '-'}
                      </TableCell>
                      <TableCell>
                        <Badge
                          className={
                            reconciliationStatusColors[statement.reconciliationStatus]
                          }
                        >
                          {reconciliationStatusLabels[statement.reconciliationStatus]}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        {formatAmount(statement.reconciledAmount)}
                      </TableCell>
                      <TableCell>
                        {statement.reconciliationStatus !== 'RECONCILED' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteStatement(statement.id)}
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="mt-4 flex items-center justify-between">
                  <p className="text-sm text-slate-500">
                    Showing {(page - 1) * pageSize + 1} to{' '}
                    {Math.min(page * pageSize, total)} of {total}
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={page === 1}
                      onClick={() => setPage((p) => p - 1)}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={page >= totalPages}
                      onClick={() => setPage((p) => p + 1)}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
