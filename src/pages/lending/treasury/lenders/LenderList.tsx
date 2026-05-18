import { Plus, Search, Filter, MoreHorizontal, Eye, Edit, Building2, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
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
import { useLenders, type LenderFilters } from '@/hooks/lending/useLenders';
import type { LenderListItem } from '@/types/lending';

const lenderTypeLabels: Record<string, { label: string; color: string }> = {
  BANK: { label: 'Bank', color: 'bg-blue-100 text-blue-700' },
  DFI: { label: 'DFI', color: 'bg-green-100 text-green-700' },
  MF: { label: 'Mutual Fund', color: 'bg-purple-100 text-purple-700' },
  NCD: { label: 'NCD', color: 'bg-orange-100 text-orange-700' },
  CP: { label: 'Commercial Paper', color: 'bg-pink-100 text-pink-700' },
  SECURITIZATION: { label: 'Securitization', color: 'bg-indigo-100 text-indigo-700' },
  SUBORDINATED_DEBT: { label: 'Sub Debt', color: 'bg-amber-100 text-amber-700' },
  OTHER: { label: 'Other', color: 'bg-gray-100 text-gray-700' },
};

export default function LenderList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');

  const filters: LenderFilters = {
    pageSize: 100,
    ...(typeFilter !== 'ALL' && { lenderType: typeFilter }),
  };
  const { data, isLoading: loading, isError, error, refetch } = useLenders(filters);

  // Client-side search-as-you-type — BE doesn't filter by name on this endpoint.
  const allLenders: LenderListItem[] = data?.items ?? [];
  const lenders = allLenders.filter((l) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return l.lenderName.toLowerCase().includes(q) || l.lenderCode.toLowerCase().includes(q);
  });

  // Wire amounts are strings (Decimal precision); coerce once for display-only sums.
  const totalSanctioned = lenders.reduce((sum, l) => sum + Number(l.totalSanctionLimit ?? 0), 0);
  const totalAvailable = lenders.reduce((sum, l) => sum + Number(l.availableLimit ?? 0), 0);
  const totalUtilized = totalSanctioned - totalAvailable;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Lenders"
        subtitle="Manage lender relationships and borrowing facilities"
        actions={
          <Button onClick={() => navigate('/admin/treasury/lenders/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Lender
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Lenders</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            ) : (
              <>
                <div className="text-2xl font-bold">{lenders.length}</div>
                <p className="text-xs text-muted-foreground">Active relationships</p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sanctioned</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalSanctioned} abbreviated className="text-2xl font-bold" />
            <p className="text-xs text-muted-foreground">Aggregate limits</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Utilized</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={totalUtilized}
              abbreviated
              className="text-2xl font-bold text-amber-600"
            />
            <p className="text-xs text-muted-foreground">
              <PercentageDisplay value={(totalUtilized / totalSanctioned) * 100} /> utilization
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Available Limit</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={totalAvailable}
              abbreviated
              className="text-2xl font-bold text-green-600"
            />
            <p className="text-xs text-muted-foreground">Undrawn facilities</p>
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
                placeholder="Search by lender name or code..."
                className="pl-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[180px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Lender Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Types</SelectItem>
                  <SelectItem value="BANK">Bank</SelectItem>
                  <SelectItem value="DFI">DFI</SelectItem>
                  <SelectItem value="MF">Mutual Fund</SelectItem>
                  <SelectItem value="NCD">NCD</SelectItem>
                  <SelectItem value="CP">Commercial Paper</SelectItem>
                  <SelectItem value="SECURITIZATION">Securitization</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lenders Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Lender Code</TableHead>
                <TableHead>Lender Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="text-right">Sanctioned</TableHead>
                <TableHead className="text-right">Utilized</TableHead>
                <TableHead className="text-right">Available</TableHead>
                <TableHead className="text-right">Avg Rate</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8 text-center text-muted-foreground">
                    <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />
                    Loading lenders...
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8">
                    <ErrorState
                      title="Could not load lenders"
                      error={error}
                      onRetry={() => refetch()}
                    />
                  </TableCell>
                </TableRow>
              ) : lenders.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8 text-center text-muted-foreground">
                    No lenders found
                  </TableCell>
                </TableRow>
              ) : (
                lenders.map((lender) => {
                  const typeConfig = lenderTypeLabels[lender.lenderType] ?? lenderTypeLabels.OTHER;
                  const sanctioned = Number(lender.totalSanctionLimit ?? 0);
                  const available = Number(lender.availableLimit ?? 0);
                  const utilized = sanctioned - available;
                  const utilizationPercent = sanctioned > 0 ? (utilized / sanctioned) * 100 : 0;
                  return (
                    <TableRow
                      key={lender.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => navigate(`/admin/treasury/lenders/${lender.id}`)}
                    >
                      <TableCell className="font-mono text-sm">{lender.lenderCode}</TableCell>
                      <TableCell>
                        <div className="font-medium">{lender.lenderName}</div>
                        {lender.externalRating && (
                          <div className="text-xs text-muted-foreground">
                            Rating: {lender.externalRating}
                            {lender.ratingAgency ? ` (${lender.ratingAgency})` : ''}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={typeConfig.color}>
                          {typeConfig.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={sanctioned} abbreviated />
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={utilized} abbreviated />
                        <div className="text-xs text-muted-foreground">
                          <PercentageDisplay value={utilizationPercent} />
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={available} abbreviated />
                      </TableCell>
                      <TableCell className="text-right text-muted-foreground">—</TableCell>
                      <TableCell>
                        <Badge
                          variant={lender.status === 'ACTIVE' ? 'default' : 'secondary'}
                          className={
                            lender.status === 'ACTIVE' ? 'bg-green-100 text-green-700' : ''
                          }
                        >
                          {lender.status}
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
                                navigate(`/admin/treasury/lenders/${lender.id}`);
                              }}
                            >
                              <Eye className="mr-2 h-4 w-4" />
                              View Details
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/admin/treasury/lenders/${lender.id}/edit`);
                              }}
                            >
                              <Edit className="mr-2 h-4 w-4" />
                              Edit Lender
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
