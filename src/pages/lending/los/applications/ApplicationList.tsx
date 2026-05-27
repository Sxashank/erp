/**
 * Application List Page
 * Pipeline view of loan applications with stage-based filtering.
 *
 * Data source: GET /lending/applications (camelCase via Pydantic CamelSchema).
 */

import { useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  Search,
  Filter,
  Download,
  MoreHorizontal,
  Eye,
  Edit,
  Trash2,
  RefreshCw,
  Loader2,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import {
  ApplicationStageBadge,
  ApplicationStatusBadge,
} from '@/components/lending/common/StatusBadge';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
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
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  useApplications,
  type ApplicationFilters,
  type ApplicationStageValue,
  type ApplicationStatusValue,
} from '@/hooks/lending/useApplications';
import { useToast } from '@/hooks/use-toast';
import { applicationApi } from '@/services/lending';

const APPLICATION_STAGES: { value: ApplicationStageValue; label: string; color: string }[] = [
  { value: 'APPLICATION', label: 'Application', color: 'bg-blue-500' },
  { value: 'APPRAISAL', label: 'Appraisal', color: 'bg-amber-500' },
  { value: 'SANCTION', label: 'Sanction', color: 'bg-purple-500' },
  { value: 'POST_SANCTION', label: 'Post Sanction', color: 'bg-indigo-500' },
  { value: 'DISBURSED', label: 'Disbursed', color: 'bg-green-500' },
];

const APPLICATION_STATUSES: { value: ApplicationStatusValue; label: string }[] = [
  { value: 'DRAFT', label: 'Draft' },
  { value: 'SUBMITTED', label: 'Submitted' },
  { value: 'UNDER_REVIEW', label: 'Under Review' },
  { value: 'SANCTIONED', label: 'Sanctioned' },
  { value: 'REJECTED', label: 'Rejected' },
  { value: 'WITHDRAWN', label: 'Withdrawn' },
];

const PAGE_SIZES = [10, 25, 50, 100];

export default function ApplicationList() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();

  const [searchInput, setSearchInput] = useState(searchParams.get('search') ?? '');

  const filters: ApplicationFilters = useMemo(
    () => ({
      search: searchParams.get('search') || undefined,
      stage: (searchParams.get('stage') as ApplicationStageValue) || undefined,
      status: (searchParams.get('status') as ApplicationStatusValue) || undefined,
      fromDate: searchParams.get('fromDate') || undefined,
      toDate: searchParams.get('toDate') || undefined,
      page: parseInt(searchParams.get('page') ?? '1', 10),
      pageSize: parseInt(searchParams.get('pageSize') ?? '25', 10),
    }),
    [searchParams],
  );

  const { data, isLoading, isError, error, refetch, isFetching } = useApplications(filters);
  const applications = data?.items ?? [];
  const totalCount = data?.total ?? 0;
  const totalPages = data?.total_pages ?? 0;

  // Debounce search → URL
  useEffect(() => {
    const t = setTimeout(() => {
      if (searchInput === (searchParams.get('search') ?? '')) return;
      const next = new URLSearchParams(searchParams);
      if (searchInput) next.set('search', searchInput);
      else next.delete('search');
      next.set('page', '1');
      setSearchParams(next);
    }, 300);
    return () => clearTimeout(t);
  }, [searchInput, searchParams, setSearchParams]);

  const updateParam = (key: string, value: string | undefined) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    if (key !== 'page') next.set('page', '1');
    setSearchParams(next);
  };

  const clearFilters = () => {
    setSearchInput('');
    setSearchParams(new URLSearchParams());
  };

  const handleDelete = async (applicationId: string) => {
    if (!confirm('Are you sure you want to delete this application?')) return;
    try {
      await applicationApi.deleteApplication(applicationId);
      toast({ title: 'Application deleted' });
      queryClient.invalidateQueries({ queryKey: ['lending', 'applications'] });
    } catch (err: unknown) {
      toast({
        title: 'Failed to delete application',
        description: err instanceof Error ? err.message : 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  const hasActiveFilters =
    filters.search || filters.stage || filters.status || filters.fromDate || filters.toDate;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Loan Applications"
        subtitle="Manage loan applications through the origination pipeline"
        actions={
          <Button onClick={() => navigate('/admin/lending/applications/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Application
          </Button>
        }
      />

      {/* Stage Pipeline Tabs */}
      <Card>
        <CardContent className="pt-6">
          <Tabs
            value={filters.stage || 'all'}
            onValueChange={(v) => updateParam('stage', v === 'all' ? undefined : v)}
          >
            <TabsList className="grid w-full grid-cols-6">
              <TabsTrigger value="all" className="gap-2">
                All
                <Badge variant="secondary" className="ml-1">
                  {totalCount}
                </Badge>
              </TabsTrigger>
              {APPLICATION_STAGES.map((stage) => (
                <TabsTrigger key={stage.value} value={stage.value} className="gap-2">
                  <span className={`h-2 w-2 rounded-full ${stage.color}`} />
                  {stage.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        </CardContent>
      </Card>

      {/* Filters */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base font-medium">
            <Filter className="h-4 w-4" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
            <div className="relative lg:col-span-2">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search by application number..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select
              value={filters.status || 'all'}
              onValueChange={(v) => updateParam('status', v === 'all' ? undefined : v)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                {APPLICATION_STATUSES.map((s) => (
                  <SelectItem key={s.value} value={s.value}>
                    {s.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Input
              type="date"
              value={filters.fromDate || ''}
              onChange={(e) => updateParam('fromDate', e.target.value || undefined)}
            />
            <Input
              type="date"
              value={filters.toDate || ''}
              onChange={(e) => updateParam('toDate', e.target.value || undefined)}
            />
          </div>
          {hasActiveFilters && (
            <div className="mt-4 flex flex-wrap items-center gap-2">
              <span className="text-sm text-muted-foreground">Active filters:</span>
              {filters.search && <Badge variant="secondary">Search: {filters.search}</Badge>}
              {filters.stage && (
                <Badge variant="secondary">
                  Stage: {APPLICATION_STAGES.find((s) => s.value === filters.stage)?.label}
                </Badge>
              )}
              {filters.status && (
                <Badge variant="secondary">
                  Status: {APPLICATION_STATUSES.find((s) => s.value === filters.status)?.label}
                </Badge>
              )}
              {filters.fromDate && <Badge variant="secondary">From: {filters.fromDate}</Badge>}
              {filters.toDate && <Badge variant="secondary">To: {filters.toDate}</Badge>}
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                Clear all
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardDescription>
              {isLoading
                ? 'Loading...'
                : `Showing ${applications.length} of ${totalCount} applications`}
            </CardDescription>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
                <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
              </Button>
              <Button variant="outline" size="sm">
                <Download className="mr-2 h-4 w-4" />
                Export
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[200px]">Application #</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead>Product</TableHead>
                <TableHead>Stage</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="w-[80px]">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                    <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />
                    Loading applications...
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8">
                    <ErrorState
                      title="Could not load applications"
                      error={error}
                      onRetry={() => refetch()}
                    />
                  </TableCell>
                </TableRow>
              ) : applications.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                    No applications found.
                    {hasActiveFilters && ' Try adjusting your filters.'}
                  </TableCell>
                </TableRow>
              ) : (
                applications.map((app) => (
                  <TableRow
                    key={app.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => navigate(`/admin/lending/applications/${app.id}`)}
                  >
                    <TableCell>
                      <div className="font-mono text-sm">{app.applicationNumber}</div>
                    </TableCell>
                    <TableCell>
                      <div className="font-medium">{app.entityName ?? '—'}</div>
                    </TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={app.requestedAmount} />
                      <div className="text-xs text-muted-foreground">
                        {app.requestedTenureMonths} months
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{app.productName ?? '—'}</Badge>
                    </TableCell>
                    <TableCell>
                      <ApplicationStageBadge status={app.stage} />
                    </TableCell>
                    <TableCell>
                      <ApplicationStatusBadge status={app.status} />
                    </TableCell>
                    <TableCell>
                      <DateDisplay date={app.createdAt} />
                    </TableCell>
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={() => navigate(`/admin/lending/applications/${app.id}`)}
                          >
                            <Eye className="mr-2 h-4 w-4" />
                            View Details
                          </DropdownMenuItem>
                          {app.status === 'DRAFT' && (
                            <DropdownMenuItem
                              onClick={() => navigate(`/admin/lending/applications/${app.id}/edit`)}
                            >
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuSeparator />
                          {app.status === 'DRAFT' && (
                            <DropdownMenuItem
                              className="text-red-600"
                              onClick={() => handleDelete(app.id)}
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete
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

          {!isLoading && totalPages > 1 && (
            <div className="flex items-center justify-between border-t px-6 py-4">
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Rows per page:</span>
                <Select
                  value={String(filters.pageSize ?? 25)}
                  onValueChange={(v) => updateParam('pageSize', v)}
                >
                  <SelectTrigger className="w-[70px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {PAGE_SIZES.map((size) => (
                      <SelectItem key={size} value={String(size)}>
                        {size}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">
                  Page {filters.page} of {totalPages}
                </span>
                <div className="flex gap-1">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => updateParam('page', '1')}
                    disabled={filters.page === 1}
                  >
                    First
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => updateParam('page', String((filters.page ?? 1) - 1))}
                    disabled={filters.page === 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => updateParam('page', String((filters.page ?? 1) + 1))}
                    disabled={filters.page === totalPages}
                  >
                    Next
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => updateParam('page', String(totalPages))}
                    disabled={filters.page === totalPages}
                  >
                    Last
                  </Button>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
