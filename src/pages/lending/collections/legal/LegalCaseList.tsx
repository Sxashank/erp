import {
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  Eye,
  Calendar,
  FileText,
  Scale,
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
import {
  useLegalCases,
  type LegalCaseListItem,
  type LegalCaseStatusValue,
  type LegalCaseTypeValue,
  type LegalCaseFilters,
} from '@/hooks/lending/useLegalCases';
import { logger } from '@/lib/logger';

const caseTypeColors: Record<LegalCaseTypeValue, string> = {
  SARFAESI: 'bg-purple-100 text-purple-700',
  DRT_APPLICATION: 'bg-blue-100 text-blue-700',
  RECOVERY_SUIT: 'bg-cyan-100 text-cyan-700',
  WINDING_UP: 'bg-orange-100 text-orange-700',
  IBC: 'bg-indigo-100 text-indigo-700',
  ARBITRATION: 'bg-amber-100 text-amber-700',
  EXECUTION: 'bg-green-100 text-green-700',
  APPEAL: 'bg-rose-100 text-rose-700',
};

const statusConfig: Record<LegalCaseStatusValue, { label: string; color: string }> = {
  DRAFT: { label: 'Draft', color: 'bg-gray-100 text-gray-700' },
  NOTICE_ISSUED: { label: 'Notice Issued', color: 'bg-yellow-100 text-yellow-700' },
  FILED: { label: 'Filed', color: 'bg-blue-100 text-blue-700' },
  PENDING: { label: 'Pending', color: 'bg-amber-100 text-amber-700' },
  INTERIM_ORDER: { label: 'Interim Order', color: 'bg-cyan-100 text-cyan-700' },
  DECREE_OBTAINED: { label: 'Decree Obtained', color: 'bg-green-100 text-green-700' },
  EXECUTION: { label: 'Execution', color: 'bg-green-200 text-green-800' },
  SETTLED: { label: 'Settled', color: 'bg-emerald-100 text-emerald-700' },
  DISMISSED: { label: 'Dismissed', color: 'bg-red-100 text-red-700' },
};

export default function LegalCaseList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [caseTypeFilter, setCaseTypeFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const filters: LegalCaseFilters = {
    pageSize: 100,
    ...(statusFilter !== 'ALL' && { status: statusFilter as LegalCaseStatusValue }),
    ...(caseTypeFilter !== 'ALL' && { caseType: caseTypeFilter as LegalCaseTypeValue }),
  };
  const { data, isLoading, isError, error, refetch } = useLegalCases(filters);

  const all: LegalCaseListItem[] = data?.items ?? [];
  const cases = all.filter((c) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      c.caseReference.toLowerCase().includes(q) ||
      (c.caseNumber ?? '').toLowerCase().includes(q) ||
      (c.entityName ?? '').toLowerCase().includes(q) ||
      (c.loanAccountNumber ?? '').toLowerCase().includes(q)
    );
  });

  // Wire amounts are strings (Decimal precision); coerce once for display-only sums.
  const totalClaimAmount = cases.reduce((sum, c) => sum + Number(c.totalClaim), 0);
  const upcomingHearings = cases.filter((c) => c.nextHearingDate).length;
  const sarfaesiCount = cases.filter((c) => c.caseType === 'SARFAESI').length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Legal Cases"
        subtitle="Track legal proceedings for loan recovery"
        breadcrumbs={[
          { label: 'Collections', to: '/admin/lending/collections' },
          { label: 'Legal Cases' },
        ]}
        actions={
          <Button onClick={() => navigate('/admin/lending/collections/legal/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Legal Case
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Cases</CardTitle>
            <Scale className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.total ?? cases.length}</div>
            <p className="text-xs text-muted-foreground">Across all forums</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Claims</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalClaimAmount} abbreviated className="text-2xl font-bold" />
            <p className="text-xs text-muted-foreground">Under litigation</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Upcoming Hearings</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{upcomingHearings}</div>
            <p className="text-xs text-muted-foreground">With scheduled date</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">SARFAESI Cases</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{sarfaesiCount}</div>
            <p className="text-xs text-muted-foreground">Recovery proceedings</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by case reference, court case #, entity, or loan account..."
                className="pl-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Select value={caseTypeFilter} onValueChange={setCaseTypeFilter}>
                <SelectTrigger className="w-[180px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Case Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Types</SelectItem>
                  <SelectItem value="SARFAESI">SARFAESI</SelectItem>
                  <SelectItem value="DRT_APPLICATION">DRT Application</SelectItem>
                  <SelectItem value="RECOVERY_SUIT">Recovery Suit</SelectItem>
                  <SelectItem value="WINDING_UP">Winding Up</SelectItem>
                  <SelectItem value="IBC">IBC</SelectItem>
                  <SelectItem value="ARBITRATION">Arbitration</SelectItem>
                  <SelectItem value="EXECUTION">Execution</SelectItem>
                  <SelectItem value="APPEAL">Appeal</SelectItem>
                </SelectContent>
              </Select>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Status</SelectItem>
                  <SelectItem value="DRAFT">Draft</SelectItem>
                  <SelectItem value="NOTICE_ISSUED">Notice Issued</SelectItem>
                  <SelectItem value="FILED">Filed</SelectItem>
                  <SelectItem value="PENDING">Pending</SelectItem>
                  <SelectItem value="INTERIM_ORDER">Interim Order</SelectItem>
                  <SelectItem value="DECREE_OBTAINED">Decree Obtained</SelectItem>
                  <SelectItem value="EXECUTION">Execution</SelectItem>
                  <SelectItem value="SETTLED">Settled</SelectItem>
                  <SelectItem value="DISMISSED">Dismissed</SelectItem>
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
                <TableHead>Case Reference</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Forum</TableHead>
                <TableHead className="text-right">Claim</TableHead>
                <TableHead>Filed</TableHead>
                <TableHead>Next Hearing</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8 text-center text-muted-foreground">
                    <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />
                    Loading legal cases...
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8">
                    <ErrorState
                      title="Could not load legal cases"
                      error={error}
                      onRetry={() => refetch()}
                    />
                  </TableCell>
                </TableRow>
              ) : cases.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8 text-center text-muted-foreground">
                    No legal cases found
                  </TableCell>
                </TableRow>
              ) : (
                cases.map((legalCase) => {
                  const status = statusConfig[legalCase.status];
                  return (
                    <TableRow
                      key={legalCase.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => navigate(`/admin/lending/collections/legal/${legalCase.id}`)}
                    >
                      <TableCell>
                        <div className="font-mono text-sm">{legalCase.caseReference}</div>
                        {legalCase.caseNumber && (
                          <div className="text-xs text-muted-foreground">
                            Court #: {legalCase.caseNumber}
                          </div>
                        )}
                        {legalCase.loanAccountNumber && (
                          <div className="text-xs text-muted-foreground">
                            {legalCase.loanAccountNumber}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>{legalCase.entityName ?? '—'}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={caseTypeColors[legalCase.caseType]}>
                          {legalCase.caseType.replace('_', ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div>{legalCase.forumType.replace('_', ' ')}</div>
                        <div className="text-xs text-muted-foreground">{legalCase.courtName}</div>
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={legalCase.totalClaim} abbreviated />
                        {Number(legalCase.recoveryThroughCase) > 0 && (
                          <div className="text-xs text-green-600">
                            Recovered:{' '}
                            <AmountDisplay amount={legalCase.recoveryThroughCase} abbreviated />
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        {legalCase.filingDate ? (
                          <DateDisplay date={legalCase.filingDate} />
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {legalCase.nextHearingDate ? (
                          <DateDisplay date={legalCase.nextHearingDate} />
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={status.color}>
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
                                navigate(`/admin/lending/collections/legal/${legalCase.id}`);
                              }}
                            >
                              <Eye className="mr-2 h-4 w-4" />
                              View Details
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                logger.debug('Add hearing:', legalCase.id);
                              }}
                            >
                              <Calendar className="mr-2 h-4 w-4" />
                              Add Hearing
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                logger.debug('Upload document:', legalCase.id);
                              }}
                            >
                              <FileText className="mr-2 h-4 w-4" />
                              Upload Document
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
