import {
  Search,
  Filter,
  MoreHorizontal,
  Eye,
  FileText,
  AlertTriangle,
  TrendingDown,
  TrendingUp,
  Loader2,
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
import {
  useNPAAccounts,
  type NPAAccountListItem,
  type NPAClassificationValue,
  type NPAFilters,
} from '@/hooks/lending/useNPAAccounts';
import { logger } from '@/lib/logger';

export default function NPAList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [classificationFilter, setClassificationFilter] = useState<string>('ALL');

  const filters: NPAFilters = {
    pageSize: 100,
    ...(classificationFilter !== 'ALL' && {
      classification: classificationFilter as NPAClassificationValue,
    }),
  };
  const { data, isLoading, isError, error, refetch } = useNPAAccounts(filters);

  // Client-side search-as-you-type — BE doesn't filter by name on this list.
  const allAccounts: NPAAccountListItem[] = data?.items ?? [];
  const accounts = allAccounts.filter((a) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      a.loanAccountNumber.toLowerCase().includes(q) ||
      (a.entityName ?? '').toLowerCase().includes(q)
    );
  });

  // Wire amounts are strings (Decimal precision); coerce once for display-only sums.
  const totalNPA = accounts.reduce((sum, a) => sum + Number(a.totalOutstanding), 0);
  const totalProvision = accounts.reduce((sum, a) => sum + Number(a.provisionAmount ?? 0), 0);
  const provisionCoverage = totalNPA > 0 ? (totalProvision / totalNPA) * 100 : 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="NPA Accounts"
        subtitle="Manage non-performing assets, provisioning, and recovery actions"
        actions={
          <Button variant="outline" onClick={() => logger.debug('Run NPA identification')}>
            <AlertTriangle className="mr-2 h-4 w-4" />
            Run NPA Identification
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total NPA Accounts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.total ?? accounts.length}</div>
            <p className="text-xs text-muted-foreground">Non-performing accounts</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Gross NPA</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={totalNPA}
              abbreviated
              className="text-2xl font-bold text-red-600"
            />
            <p className="text-xs text-muted-foreground">Total outstanding</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Provision</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalProvision} abbreviated className="text-2xl font-bold" />
            <p className="text-xs text-muted-foreground">As per IRAC norms</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Provision Coverage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              <PercentageDisplay value={provisionCoverage} />
            </div>
            <p className="text-xs text-muted-foreground">Coverage ratio</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by loan account or entity name..."
                className="pl-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Select value={classificationFilter} onValueChange={setClassificationFilter}>
                <SelectTrigger className="w-[180px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Classification" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Classifications</SelectItem>
                  <SelectItem value="SUBSTANDARD">Sub-Standard</SelectItem>
                  <SelectItem value="DOUBTFUL_1">Doubtful-1</SelectItem>
                  <SelectItem value="DOUBTFUL_2">Doubtful-2</SelectItem>
                  <SelectItem value="DOUBTFUL_3">Doubtful-3</SelectItem>
                  <SelectItem value="LOSS">Loss</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Loan Account</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead className="text-right">Outstanding</TableHead>
                <TableHead>DPD</TableHead>
                <TableHead>Classification</TableHead>
                <TableHead>NPA Date</TableHead>
                <TableHead className="text-right">Provision</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                    <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />
                    Loading NPA accounts...
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8">
                    <ErrorState
                      title="Could not load NPA accounts"
                      error={error}
                      onRetry={() => refetch()}
                    />
                  </TableCell>
                </TableRow>
              ) : accounts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                    No NPA accounts found
                  </TableCell>
                </TableRow>
              ) : (
                accounts.map((account) => (
                  <TableRow
                    key={account.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => navigate(`/admin/lending/accounts/${account.loanAccountId}`)}
                  >
                    <TableCell>
                      <div className="font-mono text-sm">{account.loanAccountNumber}</div>
                      {account.productName && (
                        <div className="text-xs text-muted-foreground">{account.productName}</div>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="font-medium">{account.entityName ?? '—'}</div>
                    </TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={account.totalOutstanding} abbreviated />
                      <div className="text-xs text-muted-foreground">
                        Principal:{' '}
                        <AmountDisplay amount={account.principalOutstanding} abbreviated />
                      </div>
                    </TableCell>
                    <TableCell>
                      <DPDBadge dpd={account.daysPastDue} />
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={account.classification} type="classification" />
                    </TableCell>
                    <TableCell>
                      {account.npaDate ? (
                        <DateDisplay date={account.npaDate} />
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      {account.provisionAmount != null ? (
                        <>
                          <AmountDisplay amount={account.provisionAmount} abbreviated />
                          {account.provisionRate != null && (
                            <div className="text-xs text-muted-foreground">
                              @ <PercentageDisplay value={account.provisionRate} />
                            </div>
                          )}
                        </>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
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
                              navigate(`/admin/lending/accounts/${account.loanAccountId}`);
                            }}
                          >
                            <Eye className="mr-2 h-4 w-4" />
                            View Loan Account
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(
                                `/admin/lending/collections/ots/new?accountId=${account.loanAccountId}`,
                              );
                            }}
                          >
                            <TrendingDown className="mr-2 h-4 w-4" />
                            Create OTS Proposal
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(
                                `/admin/lending/collections/legal/new?accountId=${account.loanAccountId}`,
                              );
                            }}
                          >
                            <FileText className="mr-2 h-4 w-4" />
                            Initiate Legal Action
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              logger.debug('Request upgrade:', account.loanAccountId);
                            }}
                          >
                            <TrendingUp className="mr-2 h-4 w-4" />
                            Request Upgrade
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
