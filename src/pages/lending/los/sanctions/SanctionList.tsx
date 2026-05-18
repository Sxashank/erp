import {
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  Eye,
  Edit,
  FileText,
  Printer,
  Loader2,
} from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
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
import { useSanctions } from '@/hooks/lending/useSanctions';
import type { SanctionListItem } from '@/services/lending/sanctionApi';
import type { SanctionFilters } from '@/types/lending';

export default function SanctionList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const filters: SanctionFilters = {
    pageSize: 100,
    ...(searchQuery && { search: searchQuery }),
    ...(statusFilter !== 'ALL' && {
      status: statusFilter as SanctionFilters['status'],
    }),
  };
  const { data, isLoading, isError, error, refetch } = useSanctions(filters);

  const sanctions: SanctionListItem[] = data?.items ?? [];

  // Wire amounts are strings (Decimal precision); coerce once for display-only sums.
  const totalSanctioned = sanctions.reduce((sum, s) => sum + Number(s.sanctionedAmount), 0);
  const pendingApproval = sanctions.filter((s) => s.status === 'PENDING_APPROVAL').length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Loan Sanctions"
        subtitle="View and manage sanctioned loans, generate sanction letters"
        actions={
          <Button onClick={() => navigate('/admin/lending/sanctions/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Sanction
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sanctions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.total ?? sanctions.length}</div>
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sanctioned</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalSanctioned} abbreviated className="text-2xl font-bold" />
            <p className="text-xs text-muted-foreground">Across visible sanctions</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Approval</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingApproval}</div>
            <p className="text-xs text-muted-foreground">Awaiting approval workflow</p>
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
                placeholder="Search by sanction number, entity name, or application..."
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
                  <SelectItem value="PENDING_APPROVAL">Pending Approval</SelectItem>
                  <SelectItem value="APPROVED">Approved</SelectItem>
                  <SelectItem value="ACCEPTED">Accepted</SelectItem>
                  <SelectItem value="ACTIVE">Active</SelectItem>
                  <SelectItem value="EXPIRED">Expired</SelectItem>
                  <SelectItem value="CANCELLED">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Sanctions Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Sanction Number</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Product</TableHead>
                <TableHead className="text-right">Sanctioned</TableHead>
                <TableHead className="text-right">Rate</TableHead>
                <TableHead>Tenure</TableHead>
                <TableHead>Sanction Date</TableHead>
                <TableHead>Valid Until</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={10} className="py-8 text-center text-muted-foreground">
                    <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />
                    Loading sanctions...
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={10} className="py-8">
                    <ErrorState
                      title="Could not load sanctions"
                      error={error}
                      onRetry={() => refetch()}
                    />
                  </TableCell>
                </TableRow>
              ) : sanctions.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={10} className="py-8 text-center text-muted-foreground">
                    No sanctions found
                  </TableCell>
                </TableRow>
              ) : (
                sanctions.map((sanction) => (
                  <TableRow
                    key={sanction.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => navigate(`/admin/lending/sanctions/${sanction.id}`)}
                  >
                    <TableCell className="font-mono text-sm">{sanction.sanctionNumber}</TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">{sanction.entityName ?? '—'}</div>
                        {sanction.applicationNumber && (
                          <div className="text-xs text-muted-foreground">
                            {sanction.applicationNumber}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>{sanction.productName ?? '—'}</TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={sanction.sanctionedAmount} abbreviated />
                    </TableCell>
                    <TableCell className="text-right">
                      <PercentageDisplay value={sanction.effectiveRate} /> p.a.
                    </TableCell>
                    <TableCell>{sanction.tenureMonths} months</TableCell>
                    <TableCell>
                      <DateDisplay date={sanction.sanctionDate} />
                    </TableCell>
                    <TableCell>
                      <DateDisplay date={sanction.validityDate} />
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={sanction.status} type="sanction" />
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
                              navigate(`/admin/lending/sanctions/${sanction.id}`);
                            }}
                          >
                            <Eye className="mr-2 h-4 w-4" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/admin/lending/sanctions/${sanction.id}/letter`);
                            }}
                          >
                            <FileText className="mr-2 h-4 w-4" />
                            Sanction Letter
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              window.print();
                            }}
                          >
                            <Printer className="mr-2 h-4 w-4" />
                            Print
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          {(sanction.status === 'DRAFT' ||
                            sanction.status === 'PENDING_APPROVAL') && (
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/admin/lending/sanctions/${sanction.id}/edit`);
                              }}
                            >
                              <Edit className="mr-2 h-4 w-4" />
                              Edit Sanction
                            </DropdownMenuItem>
                          )}
                          {sanction.status === 'ACCEPTED' && (
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(
                                  `/admin/lending/disbursements/new?sanctionId=${sanction.id}`,
                                );
                              }}
                            >
                              <Plus className="mr-2 h-4 w-4" />
                              Create Disbursement
                            </DropdownMenuItem>
                          )}
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
