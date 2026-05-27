import {
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  Eye,
  CheckCircle,
  Clock,
  FileText,
  RefreshCw,
  Loader2,
} from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
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
import {
  useRestructures,
  type RestructureListItem,
  type RestructureStatusValue,
  type RestructureFilters,
} from '@/hooks/lending/useRestructures';
import { masterRowsToOptions, useLendingOptionRows } from '@/hooks/lending/useLendingMasters';

const statusConfig: Record<
  RestructureStatusValue,
  { label: string; color: string; icon: React.ElementType }
> = {
  DRAFT: { label: 'Draft', color: 'bg-gray-100 text-gray-700', icon: FileText },
  PROPOSED: { label: 'Proposed', color: 'bg-blue-100 text-blue-700', icon: FileText },
  PENDING_APPROVAL: {
    label: 'Pending Approval',
    color: 'bg-yellow-100 text-yellow-700',
    icon: Clock,
  },
  APPROVED: { label: 'Approved', color: 'bg-green-100 text-green-700', icon: CheckCircle },
  REJECTED: { label: 'Rejected', color: 'bg-red-100 text-red-700', icon: Clock },
  IMPLEMENTED: { label: 'Implemented', color: 'bg-green-200 text-green-800', icon: CheckCircle },
  CANCELLED: { label: 'Cancelled', color: 'bg-gray-200 text-gray-700', icon: Clock },
};

export default function RestructureList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');

  const filters: RestructureFilters = {
    pageSize: 100,
    ...(statusFilter !== 'ALL' && { status: statusFilter as RestructureStatusValue }),
  };
  const { data, isLoading, isError, error, refetch } = useRestructures(filters);
  const restructureTypeRows = useLendingOptionRows('RESTRUCTURE_TYPE');
  const restructureTypeOptions = masterRowsToOptions(restructureTypeRows.data?.items);
  const restructureTypeLabel = (value: string) =>
    restructureTypeOptions.find((option) => option.value === value)?.label ?? value;

  const all: RestructureListItem[] = data?.items ?? [];
  const restructures = all.filter((r) => {
    if (typeFilter !== 'ALL' && r.restructureType !== typeFilter) return false;
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      r.restructureReference.toLowerCase().includes(q) ||
      (r.entityName ?? '').toLowerCase().includes(q) ||
      (r.loanAccountNumber ?? '').toLowerCase().includes(q)
    );
  });

  const pendingApproval = restructures.filter((r) => r.status === 'PENDING_APPROVAL').length;
  const implementedCount = restructures.filter((r) => r.status === 'IMPLEMENTED').length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Loan Restructuring"
        subtitle="Manage loan restructure proposals and implementations"
        actions={
          <Button onClick={() => navigate('/admin/lending/collections/restructure/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Restructure
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Proposals</CardTitle>
            <RefreshCw className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.total ?? restructures.length}</div>
            <p className="text-xs text-muted-foreground">All restructure proposals</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Approval</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{pendingApproval}</div>
            <p className="text-xs text-muted-foreground">Awaiting decision</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Implemented</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{implementedCount}</div>
            <p className="text-xs text-muted-foreground">Successfully restructured</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Tenure Extension</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {restructures.length === 0
                ? '—'
                : `${Math.round(
                    restructures.reduce((s, r) => s + (r.postTenureMonths - r.preTenureMonths), 0) /
                      restructures.length,
                  )} mo`}
            </div>
            <p className="text-xs text-muted-foreground">Across visible rows</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by reference, entity, or loan account..."
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
                  <SelectItem value="DRAFT">Draft</SelectItem>
                  <SelectItem value="PROPOSED">Proposed</SelectItem>
                  <SelectItem value="PENDING_APPROVAL">Pending Approval</SelectItem>
                  <SelectItem value="APPROVED">Approved</SelectItem>
                  <SelectItem value="REJECTED">Rejected</SelectItem>
                  <SelectItem value="IMPLEMENTED">Implemented</SelectItem>
                  <SelectItem value="CANCELLED">Cancelled</SelectItem>
                </SelectContent>
              </Select>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Types</SelectItem>
                  {restructureTypeOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
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
                <TableHead>Reference</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="text-right">Rate Change</TableHead>
                <TableHead className="text-right">Tenure Change</TableHead>
                <TableHead className="text-right">Moratorium</TableHead>
                <TableHead className="text-right">Principal</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8 text-center text-muted-foreground">
                    <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />
                    Loading restructures...
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8">
                    <ErrorState
                      title="Could not load restructures"
                      error={error}
                      onRetry={() => refetch()}
                    />
                  </TableCell>
                </TableRow>
              ) : restructures.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8 text-center text-muted-foreground">
                    No restructure proposals found
                  </TableCell>
                </TableRow>
              ) : (
                restructures.map((restructure) => {
                  const status = statusConfig[restructure.status];
                  const StatusIcon = status.icon;
                  // Wire rates are strings (Decimal precision); coerce for display math.
                  const preRate = Number(restructure.preInterestRate);
                  const postRate = Number(restructure.postInterestRate);
                  const rateChange = postRate - preRate;
                  const tenureChange = restructure.postTenureMonths - restructure.preTenureMonths;
                  return (
                    <TableRow
                      key={restructure.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() =>
                        navigate(`/admin/lending/collections/restructure/${restructure.id}`)
                      }
                    >
                      <TableCell>
                        <div className="font-mono text-sm">{restructure.restructureReference}</div>
                        <div className="text-xs text-muted-foreground">
                          {restructure.loanAccountNumber ?? '—'}
                        </div>
                      </TableCell>
                      <TableCell>{restructure.entityName ?? '—'}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {restructureTypeLabel(restructure.restructureType)}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex flex-col items-end">
                          <span
                            className={
                              rateChange < 0
                                ? 'text-green-600'
                                : rateChange > 0
                                  ? 'text-red-600'
                                  : ''
                            }
                          >
                            {preRate}% → {postRate}%
                          </span>
                          {rateChange !== 0 && (
                            <span
                              className={`text-xs ${
                                rateChange < 0 ? 'text-green-600' : 'text-red-600'
                              }`}
                            >
                              ({rateChange > 0 ? '+' : ''}
                              {rateChange.toFixed(2)}%)
                            </span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex flex-col items-end">
                          <span>
                            {restructure.preTenureMonths} → {restructure.postTenureMonths} mo
                          </span>
                          {tenureChange !== 0 && (
                            <span className="text-xs text-muted-foreground">
                              ({tenureChange > 0 ? '+' : ''}
                              {tenureChange} months)
                            </span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        {restructure.moratoriumMonths > 0 ? (
                          <Badge variant="secondary">{restructure.moratoriumMonths} months</Badge>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={restructure.postOutstandingPrincipal} abbreviated />
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={status.color}>
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
                                navigate(
                                  `/admin/lending/collections/restructure/${restructure.id}`,
                                );
                              }}
                            >
                              <Eye className="mr-2 h-4 w-4" />
                              View Details
                            </DropdownMenuItem>
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
