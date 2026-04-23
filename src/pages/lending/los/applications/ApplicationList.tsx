/**
 * Application List Page
 * Pipeline view of loan applications with stage-based filtering
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Plus, Search, Filter, Download, MoreHorizontal, Eye, Edit, Trash2, RefreshCw } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';

import { ApplicationStageBadge, ApplicationStatusBadge } from '@/components/lending/common/StatusBadge';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';

import { applicationApi } from '@/services/lending';
import type { LoanApplication, ApplicationFilters, PaginatedResponse } from '@/types/lending';

const APPLICATION_STAGES = [
  { value: 'APPLICATION', label: 'Application', color: 'bg-blue-500' },
  { value: 'APPRAISAL', label: 'Appraisal', color: 'bg-amber-500' },
  { value: 'SANCTION', label: 'Sanction', color: 'bg-purple-500' },
  { value: 'POST_SANCTION', label: 'Post Sanction', color: 'bg-indigo-500' },
  { value: 'DISBURSED', label: 'Disbursed', color: 'bg-green-500' },
];

const APPLICATION_STATUSES = [
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
  const [searchParams, setSearchParams] = useSearchParams();

  // State
  const [applications, setApplications] = useState<LoanApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [stageCounts, setStageCounts] = useState<Record<string, number>>({});

  // Filters from URL params
  const [filters, setFilters] = useState<ApplicationFilters>({
    search: searchParams.get('search') || '',
    stage: searchParams.get('stage') as ApplicationFilters['stage'] || undefined,
    status: searchParams.get('status') as ApplicationFilters['status'] || undefined,
    date_from: searchParams.get('date_from') || undefined,
    date_to: searchParams.get('date_to') || undefined,
    page: parseInt(searchParams.get('page') || '1'),
    page_size: parseInt(searchParams.get('page_size') || '25'),
  });

  // Fetch applications
  const fetchApplications = useCallback(async () => {
    setLoading(true);
    try {
      const response: PaginatedResponse<LoanApplication> = await applicationApi.getApplications(filters);
      setApplications(response.items);
      setTotalCount(response.total);
      setTotalPages(response.total_pages);

      // Calculate stage counts (in production, this would be a separate API call)
      const counts: Record<string, number> = {};
      APPLICATION_STAGES.forEach(stage => {
        counts[stage.value] = response.items.filter(app => app.stage === stage.value).length;
      });
      setStageCounts(counts);
    } catch (error) {
      console.error('Failed to fetch applications:', error);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchApplications();
  }, [fetchApplications]);

  // Update URL params when filters change
  useEffect(() => {
    const params = new URLSearchParams();
    if (filters.search) params.set('search', filters.search);
    if (filters.stage) params.set('stage', filters.stage);
    if (filters.status) params.set('status', filters.status);
    if (filters.date_from) params.set('date_from', filters.date_from);
    if (filters.date_to) params.set('date_to', filters.date_to);
    if (filters.page && filters.page > 1) params.set('page', filters.page.toString());
    if (filters.page_size && filters.page_size !== 25) params.set('page_size', filters.page_size.toString());
    setSearchParams(params);
  }, [filters, setSearchParams]);

  // Handle filter changes
  const updateFilter = (key: keyof ApplicationFilters, value: string | number | undefined) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      page: key !== 'page' ? 1 : (value as number),
    }));
  };

  // Handle search with debounce
  const [searchInput, setSearchInput] = useState(filters.search || '');
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== filters.search) {
        updateFilter('search', searchInput || undefined);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  // Clear all filters
  const clearFilters = () => {
    setSearchInput('');
    setFilters({
      page: 1,
      page_size: 25,
    });
  };

  // Delete application
  const handleDelete = async (applicationId: string) => {
    if (!confirm('Are you sure you want to delete this application?')) return;
    try {
      await applicationApi.deleteApplication(applicationId);
      fetchApplications();
    } catch (error) {
      console.error('Failed to delete application:', error);
    }
  };

  // Pagination
  const handlePageChange = (page: number) => {
    updateFilter('page', page);
  };

  const hasActiveFilters = filters.search || filters.stage || filters.status || filters.date_from || filters.date_to;

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
            onValueChange={(value) => updateFilter('stage', value === 'all' ? undefined : value as ApplicationFilters['stage'])}
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
                  <span className={`w-2 h-2 rounded-full ${stage.color}`} />
                  {stage.label}
                  <Badge variant="secondary" className="ml-1">
                    {stageCounts[stage.value] || 0}
                  </Badge>
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        </CardContent>
      </Card>

      {/* Filters Card */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <Filter className="h-4 w-4" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Search */}
            <div className="relative lg:col-span-2">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search by application number, entity..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="pl-9"
              />
            </div>

            {/* Status */}
            <Select
              value={filters.status || 'all'}
              onValueChange={(value) => updateFilter('status', value === 'all' ? undefined : value as ApplicationFilters['status'])}
            >
              <SelectTrigger>
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                {APPLICATION_STATUSES.map((status) => (
                  <SelectItem key={status.value} value={status.value}>
                    {status.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Date From */}
            <Input
              type="date"
              placeholder="From Date"
              value={filters.date_from || ''}
              onChange={(e) => updateFilter('date_from', e.target.value || undefined)}
            />

            {/* Date To */}
            <Input
              type="date"
              placeholder="To Date"
              value={filters.date_to || ''}
              onChange={(e) => updateFilter('date_to', e.target.value || undefined)}
            />
          </div>

          {/* Active filters and clear button */}
          {hasActiveFilters && (
            <div className="mt-4 flex items-center gap-2">
              <span className="text-sm text-gray-500">Active filters:</span>
              {filters.search && (
                <Badge variant="secondary">Search: {filters.search}</Badge>
              )}
              {filters.stage && (
                <Badge variant="secondary">
                  Stage: {APPLICATION_STAGES.find(s => s.value === filters.stage)?.label}
                </Badge>
              )}
              {filters.status && (
                <Badge variant="secondary">
                  Status: {APPLICATION_STATUSES.find(s => s.value === filters.status)?.label}
                </Badge>
              )}
              {filters.date_from && (
                <Badge variant="secondary">From: {filters.date_from}</Badge>
              )}
              {filters.date_to && (
                <Badge variant="secondary">To: {filters.date_to}</Badge>
              )}
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                Clear all
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results Card */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardDescription>
              {loading ? 'Loading...' : `Showing ${applications.length} of ${totalCount} applications`}
            </CardDescription>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={fetchApplications}>
                <RefreshCw className="h-4 w-4" />
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
                <TableHead className="w-[180px]">Application #</TableHead>
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
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-40" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-28" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-8" /></TableCell>
                  </TableRow>
                ))
              ) : applications.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8 text-gray-500">
                    No applications found. {hasActiveFilters && 'Try adjusting your filters.'}
                  </TableCell>
                </TableRow>
              ) : (
                applications.map((application) => (
                  <TableRow
                    key={application.application_id}
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => navigate(`/admin/lending/applications/${application.application_id}`)}
                  >
                    <TableCell className="font-medium">
                      <div className="font-mono text-sm">{application.application_number}</div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">{application.entity_name || 'N/A'}</div>
                        <div className="text-xs text-gray-500">{(application as any).entity_code}</div>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={application.requested_amount} />
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{application.product_name || 'N/A'}</Badge>
                    </TableCell>
                    <TableCell>
                      <ApplicationStageBadge status={application.stage} />
                    </TableCell>
                    <TableCell>
                      <ApplicationStatusBadge status={application.status} />
                    </TableCell>
                    <TableCell>
                      <DateDisplay date={application.created_at} />
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
                            onClick={() => navigate(`/admin/lending/applications/${application.application_id}`)}
                          >
                            <Eye className="mr-2 h-4 w-4" />
                            View Details
                          </DropdownMenuItem>
                          {application.status === 'DRAFT' && (
                            <DropdownMenuItem
                              onClick={() => navigate(`/admin/lending/applications/${application.application_id}/edit`)}
                            >
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuSeparator />
                          {application.status === 'DRAFT' && (
                            <DropdownMenuItem
                              className="text-red-600"
                              onClick={() => handleDelete(application.application_id)}
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

          {/* Pagination */}
          {!loading && totalPages > 1 && (
            <div className="flex items-center justify-between px-6 py-4 border-t">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">Rows per page:</span>
                <Select
                  value={filters.page_size?.toString() || '25'}
                  onValueChange={(value) => updateFilter('page_size', parseInt(value))}
                >
                  <SelectTrigger className="w-[70px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {PAGE_SIZES.map((size) => (
                      <SelectItem key={size} value={size.toString()}>
                        {size}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">
                  Page {filters.page} of {totalPages}
                </span>
                <div className="flex gap-1">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(1)}
                    disabled={filters.page === 1}
                  >
                    First
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange((filters.page || 1) - 1)}
                    disabled={filters.page === 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange((filters.page || 1) + 1)}
                    disabled={filters.page === totalPages}
                  >
                    Next
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(totalPages)}
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
