import {
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  Eye,
  CheckCircle,
  Clock,
  Loader2,
} from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
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
import { useDisbursements } from '@/hooks/lending/useDisbursements';
import type {
  DisbursementListItem,
  DisbursementStatusValue,
} from '@/services/lending/disbursementApi';
import type { DisbursementFilters } from '@/types/lending';

const statusConfig: Record<
  DisbursementStatusValue,
  { label: string; variant: 'default' | 'secondary' | 'destructive'; icon: React.ElementType }
> = {
  PENDING: { label: 'Pending', variant: 'secondary', icon: Clock },
  APPROVED: { label: 'Approved', variant: 'default', icon: CheckCircle },
  PROCESSED: { label: 'Processed', variant: 'default', icon: CheckCircle },
  REJECTED: { label: 'Rejected', variant: 'destructive', icon: Clock },
  CANCELLED: { label: 'Cancelled', variant: 'secondary', icon: Clock },
  FAILED: { label: 'Failed', variant: 'destructive', icon: Clock },
  REVERSED: { label: 'Reversed', variant: 'secondary', icon: Clock },
};

export default function DisbursementList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const filters: DisbursementFilters = {
    pageSize: 100,
    ...(searchQuery && { search: searchQuery }),
    ...(statusFilter !== 'ALL' && {
      status: statusFilter as DisbursementFilters['status'],
    }),
  };
  const { data, isLoading, isError, error, refetch } = useDisbursements(filters);

  const disbursements: DisbursementListItem[] = data?.items ?? [];

  // Wire amounts are strings (Decimal precision); coerce once for display-only sums.
  const totalDisbursed = disbursements
    .filter((d) => d.status === 'PROCESSED')
    .reduce((sum, d) => sum + Number(d.disbursedAmount ?? 0), 0);
  const pendingAmount = disbursements
    .filter((d) => d.status === 'PENDING' || d.status === 'APPROVED')
    .reduce((sum, d) => sum + Number(d.requestedAmount), 0);
  const pendingCount = disbursements.filter((d) => d.status === 'PENDING').length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Disbursements"
        subtitle="Manage disbursement requests and fund transfers"
        actions={
          <Button onClick={() => navigate('/admin/lending/disbursements/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Disbursement
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.total ?? disbursements.length}</div>
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Disbursed</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalDisbursed} abbreviated className="text-2xl font-bold" />
            <p className="text-xs text-muted-foreground">Completed disbursements</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Amount</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={pendingAmount} abbreviated className="text-2xl font-bold" />
            <p className="text-xs text-muted-foreground">In pipeline</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Approval</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingCount}</div>
            <p className="text-xs text-muted-foreground">Requests awaiting approval</p>
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
                placeholder="Search by disbursement number, entity, or loan account..."
                className="pl-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[180px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Status</SelectItem>
                  <SelectItem value="PENDING">Pending</SelectItem>
                  <SelectItem value="APPROVED">Approved</SelectItem>
                  <SelectItem value="PROCESSED">Processed</SelectItem>
                  <SelectItem value="REJECTED">Rejected</SelectItem>
                  <SelectItem value="CANCELLED">Cancelled</SelectItem>
                  <SelectItem value="FAILED">Failed</SelectItem>
                  <SelectItem value="REVERSED">Reversed</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Disbursements Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Disbursement #</TableHead>
                <TableHead>Loan Account</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Tranche</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead>Request Date</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                    <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />
                    Loading disbursements...
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8">
                    <ErrorState
                      title="Could not load disbursements"
                      error={error}
                      onRetry={() => refetch()}
                    />
                  </TableCell>
                </TableRow>
              ) : disbursements.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                    No disbursements found
                  </TableCell>
                </TableRow>
              ) : (
                disbursements.map((disb) => {
                  const status = statusConfig[disb.status];
                  const StatusIcon = status.icon;
                  return (
                    <TableRow
                      key={disb.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => navigate(`/admin/lending/disbursements/${disb.id}`)}
                    >
                      <TableCell className="font-mono text-sm">
                        {disb.disbursementReference}
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {disb.loanAccountNumber ?? '—'}
                      </TableCell>
                      <TableCell>{disb.entityName ?? '—'}</TableCell>
                      <TableCell>
                        <Badge variant="outline">Tranche {disb.disbursementNumber}</Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay
                          amount={
                            disb.disbursedAmount ?? disb.approvedAmount ?? disb.requestedAmount
                          }
                          abbreviated
                        />
                      </TableCell>
                      <TableCell>
                        <DateDisplay date={disb.requestDate} />
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={status.variant}
                          className={
                            status.variant === 'default' ? 'bg-green-100 text-green-700' : ''
                          }
                        >
                          <StatusIcon className="mr-1 h-3 w-3" />
                          {status.label}
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
                                navigate(`/admin/lending/disbursements/${disb.id}`);
                              }}
                            >
                              <Eye className="mr-2 h-4 w-4" />
                              View Details
                            </DropdownMenuItem>
                            {disb.status === 'PENDING' && (
                              <DropdownMenuItem
                                onClick={(e) => {
                                  e.stopPropagation();
                                  navigate(`/admin/lending/disbursements/${disb.id}/approve`);
                                }}
                              >
                                <CheckCircle className="mr-2 h-4 w-4" />
                                Approve
                              </DropdownMenuItem>
                            )}
                            {disb.status === 'APPROVED' && (
                              <DropdownMenuItem
                                onClick={(e) => {
                                  e.stopPropagation();
                                  navigate(`/admin/lending/disbursements/${disb.id}/process`);
                                }}
                              >
                                <CheckCircle className="mr-2 h-4 w-4" />
                                Process
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
