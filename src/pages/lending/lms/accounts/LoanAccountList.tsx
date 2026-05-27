import {
  Search,
  Filter,
  MoreHorizontal,
  Eye,
  FileText,
  Receipt,
  AlertTriangle,
  Loader2,
  Upload,
} from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { DPDBadge } from '@/components/lending/common/DPDBadge';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { StatusBadge } from '@/components/lending/common/StatusBadge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
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
import { useLoanAccounts } from '@/hooks/lending/useLoanAccounts';
import type { LoanAccountListItem } from '@/services/lending/loanAccountApi';
import type { LoanAccountFilters } from '@/types/lending';

export default function LoanAccountList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [classificationFilter, setClassificationFilter] = useState<string>('ALL');

  // Fetch from /api/v1/lending/accounts. Filters are sent as query params
  // so the backend does the WHERE — pagination and KPI math stay accurate.
  const filters: LoanAccountFilters = {
    pageSize: 100,
    ...(searchQuery && { search: searchQuery }),
    ...(statusFilter !== 'ALL' && {
      status: statusFilter as LoanAccountFilters['status'],
    }),
    ...(classificationFilter !== 'ALL' && {
      assetClassification: classificationFilter as LoanAccountFilters['assetClassification'],
    }),
  };
  const { data, isLoading, isError, error, refetch } = useLoanAccounts(filters);

  // Wire format is camelCase numbers/strings (Pydantic CamelSchema on the BE).
  // No mapping needed — consume the API DTO directly.
  const accounts: LoanAccountListItem[] = data?.items ?? [];

  // Wire amounts are strings (Decimal precision); coerce once for display-only sums.
  const totalAUM = accounts.reduce((sum, a) => sum + Number(a.totalOutstanding), 0);
  const totalDisbursed = accounts.reduce((sum, a) => sum + Number(a.totalDisbursedAmount), 0);
  const npaAccounts = accounts.filter((a) =>
    [
      'NPA',
      'SUBSTANDARD',
      'SUB_STANDARD',
      'DOUBTFUL',
      'DOUBTFUL_1',
      'DOUBTFUL_2',
      'DOUBTFUL_3',
      'LOSS',
    ].includes(a.assetClassification),
  ).length;
  const smaAccounts = accounts.filter((a) =>
    ['SMA_0', 'SMA_1', 'SMA_2'].includes(a.assetClassification),
  ).length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Loan Accounts"
        subtitle="Manage active loan accounts, schedules, and statements"
        actions={
          <Button onClick={() => navigate('/admin/lending/accounts/historical-import')}>
            <Upload className="mr-2 h-4 w-4" />
            Historical Import
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total AUM</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalAUM} abbreviated className="text-2xl font-bold" />
            <p className="text-xs text-muted-foreground">{accounts.length} active accounts</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Disbursed</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalDisbursed} abbreviated className="text-2xl font-bold" />
            <p className="text-xs text-muted-foreground">Cumulative disbursement</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">SMA Accounts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{smaAccounts}</div>
            <p className="text-xs text-muted-foreground">Requires attention</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">NPA Accounts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{npaAccounts}</div>
            <p className="text-xs text-muted-foreground">Non-performing assets</p>
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
                placeholder="Search by loan account number or entity name..."
                className="pl-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[150px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Status</SelectItem>
                  <SelectItem value="CREATED">Created</SelectItem>
                  <SelectItem value="ACTIVE">Active</SelectItem>
                  <SelectItem value="DORMANT">Dormant</SelectItem>
                  <SelectItem value="FROZEN">Frozen</SelectItem>
                  <SelectItem value="CLOSED">Closed</SelectItem>
                  <SelectItem value="RECALLED">Recalled</SelectItem>
                  <SelectItem value="WRITTEN_OFF">Written Off</SelectItem>
                </SelectContent>
              </Select>
              <Select value={classificationFilter} onValueChange={setClassificationFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Classification" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Classifications</SelectItem>
                  <SelectItem value="STANDARD">Standard</SelectItem>
                  <SelectItem value="SMA_0">SMA-0 (1-30 DPD)</SelectItem>
                  <SelectItem value="SMA_1">SMA-1 (31-60 DPD)</SelectItem>
                  <SelectItem value="SMA_2">SMA-2 (61-90 DPD)</SelectItem>
                  <SelectItem value="SUB_STANDARD">Sub-Standard</SelectItem>
                  <SelectItem value="DOUBTFUL">Doubtful</SelectItem>
                  <SelectItem value="LOSS">Loss</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Loan Accounts Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Loan Account</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Product</TableHead>
                <TableHead className="text-right">Outstanding</TableHead>
                <TableHead className="text-right">Rate</TableHead>
                <TableHead>DPD</TableHead>
                <TableHead>Classification</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                    <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />
                    Loading loan accounts...
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8">
                    <ErrorState
                      title="Could not load loan accounts"
                      error={error}
                      onRetry={() => refetch()}
                    />
                  </TableCell>
                </TableRow>
              ) : accounts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                    No loan accounts yet
                  </TableCell>
                </TableRow>
              ) : (
                accounts.map((account) => (
                  <TableRow
                    key={account.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => navigate(`/admin/lending/accounts/${account.id}`)}
                  >
                    <TableCell>
                      <div className="font-mono text-sm">{account.loanAccountNumber}</div>
                      {account.maturityDate && (
                        <div className="text-xs text-muted-foreground">
                          Maturity: <DateDisplay date={account.maturityDate} />
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="font-medium">{account.entityName ?? '—'}</div>
                    </TableCell>
                    <TableCell>
                      <div>{account.productName ?? '—'}</div>
                    </TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={account.totalOutstanding} abbreviated />
                      <div className="text-xs text-muted-foreground">
                        of <AmountDisplay amount={account.sanctionedAmount} abbreviated />
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <PercentageDisplay value={account.currentInterestRate} /> p.a.
                    </TableCell>
                    <TableCell>
                      <DPDBadge dpd={account.daysPastDue} />
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={account.assetClassification} type="classification" />
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/admin/lending/accounts/${account.id}`);
                            }}
                          >
                            <Eye className="mr-2 h-4 w-4" />
                            View Account
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/admin/lending/accounts/${account.id}/statement`);
                            }}
                          >
                            <FileText className="mr-2 h-4 w-4" />
                            Statement of Account
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/admin/lending/receipts/new?accountId=${account.id}`);
                            }}
                          >
                            <Receipt className="mr-2 h-4 w-4" />
                            Record Receipt
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
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
