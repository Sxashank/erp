import {
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  Eye,
  Receipt,
  RefreshCw,
  Loader2,
} from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { Badge } from '@/components/ui/badge';
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
  useBorrowings,
  type BorrowingListItem,
  type BorrowingFilters,
} from '@/hooks/lending/useBorrowings';
import { logger } from '@/lib/logger';

const typeColors: Record<string, string> = {
  TERM_LOAN: 'bg-blue-100 text-blue-700',
  CC: 'bg-green-100 text-green-700',
  NCD: 'bg-orange-100 text-orange-700',
  CP: 'bg-pink-100 text-pink-700',
  WCDL: 'bg-purple-100 text-purple-700',
  REFINANCE: 'bg-indigo-100 text-indigo-700',
  WORKING_CAPITAL: 'bg-teal-100 text-teal-700',
  SUBORDINATED_DEBT: 'bg-amber-100 text-amber-700',
  OTHER: 'bg-gray-100 text-gray-700',
};

export default function BorrowingList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const filters: BorrowingFilters = {
    pageSize: 100,
    ...(statusFilter !== 'ALL' && { status: statusFilter }),
  };
  const { data, isLoading: loading, isError, error, refetch } = useBorrowings(filters);

  const all: BorrowingListItem[] = data?.items ?? [];
  const borrowings = all.filter((b) => {
    if (typeFilter !== 'ALL' && b.borrowingType !== typeFilter) return false;
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      b.borrowingNumber.toLowerCase().includes(q) || (b.lenderName ?? '').toLowerCase().includes(q)
    );
  });

  // Wire amounts/rates are strings (Decimal precision); coerce once for display-only sums.
  const totalSanctioned = borrowings.reduce((sum, b) => sum + Number(b.sanctionedAmount), 0);
  const totalOutstanding = borrowings.reduce((sum, b) => sum + Number(b.principalOutstanding), 0);
  const weightedAvgRate =
    totalOutstanding > 0
      ? borrowings.reduce(
          (sum, b) => sum + Number(b.effectiveRate) * Number(b.principalOutstanding),
          0,
        ) / totalOutstanding
      : 0;
  const totalDrawn = borrowings.reduce((sum, b) => sum + Number(b.drawnAmount), 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Borrowings"
        subtitle="Manage borrowing facilities and repayment schedules"
        actions={
          <Button onClick={() => navigate('/admin/treasury/borrowings/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Borrowing
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sanctioned</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            ) : (
              <>
                <AmountDisplay
                  amount={totalSanctioned}
                  abbreviated
                  className="text-2xl font-bold"
                />
                <p className="text-xs text-muted-foreground">Across all facilities</p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Outstanding</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            ) : (
              <>
                <AmountDisplay
                  amount={totalOutstanding}
                  abbreviated
                  className="text-2xl font-bold text-amber-600"
                />
                <p className="text-xs text-muted-foreground">
                  <PercentageDisplay
                    value={totalSanctioned > 0 ? (totalOutstanding / totalSanctioned) * 100 : 0}
                  />{' '}
                  utilized
                </p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Weighted Avg Rate</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            ) : (
              <>
                <div className="text-2xl font-bold">
                  <PercentageDisplay value={weightedAvgRate} /> p.a.
                </div>
                <p className="text-xs text-muted-foreground">Cost of borrowing</p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Drawn</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            ) : (
              <>
                <AmountDisplay amount={totalDrawn} abbreviated className="text-2xl font-bold" />
                <p className="text-xs text-muted-foreground">Cumulative drawdowns</p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by borrowing number or lender..."
                className="pl-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[160px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Borrowing Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Types</SelectItem>
                  <SelectItem value="TERM_LOAN">Term Loan</SelectItem>
                  <SelectItem value="CC">Cash Credit</SelectItem>
                  <SelectItem value="NCD">NCD</SelectItem>
                  <SelectItem value="CP">Commercial Paper</SelectItem>
                  <SelectItem value="WCDL">WCDL</SelectItem>
                  <SelectItem value="REFINANCE">Refinance</SelectItem>
                  <SelectItem value="WORKING_CAPITAL">Working Capital</SelectItem>
                  <SelectItem value="SUBORDINATED_DEBT">Sub Debt</SelectItem>
                </SelectContent>
              </Select>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Status</SelectItem>
                  <SelectItem value="SANCTIONED">Sanctioned</SelectItem>
                  <SelectItem value="ACTIVE">Active</SelectItem>
                  <SelectItem value="FULLY_DRAWN">Fully Drawn</SelectItem>
                  <SelectItem value="REPAYING">Repaying</SelectItem>
                  <SelectItem value="MATURED">Matured</SelectItem>
                  <SelectItem value="PREPAID">Prepaid</SelectItem>
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
                <TableHead>Borrowing #</TableHead>
                <TableHead>Lender</TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="text-right">Outstanding</TableHead>
                <TableHead className="text-right">Rate</TableHead>
                <TableHead>Maturity</TableHead>
                <TableHead>Security</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8 text-center text-muted-foreground">
                    <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />
                    Loading borrowings...
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8">
                    <ErrorState
                      title="Could not load borrowings"
                      error={error}
                      onRetry={() => refetch()}
                    />
                  </TableCell>
                </TableRow>
              ) : borrowings.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8 text-center text-muted-foreground">
                    No borrowings found
                  </TableCell>
                </TableRow>
              ) : (
                borrowings.map((borrowing) => {
                  const typeColor = typeColors[borrowing.borrowingType] ?? typeColors.OTHER;
                  return (
                    <TableRow
                      key={borrowing.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => navigate(`/admin/treasury/borrowings/${borrowing.id}`)}
                    >
                      <TableCell className="font-mono text-sm">
                        {borrowing.borrowingNumber}
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">{borrowing.lenderName ?? '—'}</div>
                        {borrowing.lenderCode && (
                          <div className="text-xs text-muted-foreground">
                            {borrowing.lenderCode}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={typeColor}>
                          {borrowing.borrowingType}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={borrowing.principalOutstanding} abbreviated />
                        <div className="text-xs text-muted-foreground">
                          of <AmountDisplay amount={borrowing.sanctionedAmount} abbreviated />
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <PercentageDisplay value={borrowing.effectiveRate} /> p.a.
                        <div className="text-xs text-muted-foreground">{borrowing.rateType}</div>
                      </TableCell>
                      <TableCell>
                        <DateDisplay date={borrowing.maturityDate} />
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{borrowing.securityType}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={borrowing.status === 'ACTIVE' ? 'default' : 'secondary'}
                          className={
                            borrowing.status === 'ACTIVE' ? 'bg-green-100 text-green-700' : ''
                          }
                        >
                          {borrowing.status}
                        </Badge>
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
                                navigate(`/admin/treasury/borrowings/${borrowing.id}`);
                              }}
                            >
                              <Eye className="mr-2 h-4 w-4" />
                              View Details
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                logger.debug('Record payment');
                              }}
                            >
                              <Receipt className="mr-2 h-4 w-4" />
                              Record Payment
                            </DropdownMenuItem>
                            {borrowing.rateType === 'FLOATING' && (
                              <DropdownMenuItem
                                onClick={(e) => {
                                  e.stopPropagation();
                                  logger.debug('Rate reset');
                                }}
                              >
                                <RefreshCw className="mr-2 h-4 w-4" />
                                Rate Reset
                              </DropdownMenuItem>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
