/**
 * Entity List Page
 * Displays list of entities/borrowers with filters and actions
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Plus, Search, Filter, Download, MoreHorizontal, Eye, Edit, Trash2, RefreshCw } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
import { useToast } from '@/hooks/use-toast';
import { logger } from '@/lib/logger';
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

import { EntityStatusBadge, RiskCategoryBadge } from '@/components/lending/common/StatusBadge';
import { RatingBadge } from '@/components/lending/common/RatingBadge';
import { DateDisplay } from '@/components/lending/common/DateDisplay';

import { entityApi } from '@/services/lending';
import type { Entity, EntityFilters, PaginatedResponse } from '@/types/lending';

// Entity types for corporate/wholesale lending (Individual hidden per NBFC-IFC model)
const ENTITY_TYPES = [
  { value: 'CORPORATE', label: 'Corporate' },
  { value: 'LLP', label: 'LLP' },
  { value: 'PARTNERSHIP', label: 'Partnership Firm' },
  { value: 'TRUST', label: 'Trust' },
  { value: 'PROPRIETORSHIP', label: 'Proprietorship' },
  { value: 'SOCIETY', label: 'Society' },
];

const ENTITY_STATUSES = [
  { value: 'PROSPECT', label: 'Prospect' },
  { value: 'ACTIVE', label: 'Active' },
  { value: 'INACTIVE', label: 'Inactive' },
  { value: 'BLACKLISTED', label: 'Blacklisted' },
];

const RISK_CATEGORIES = [
  { value: 'LOW', label: 'Low Risk' },
  { value: 'MEDIUM', label: 'Medium Risk' },
  { value: 'HIGH', label: 'High Risk' },
];

const PAGE_SIZES = [10, 25, 50, 100];

export default function EntityList() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();

  // State
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  // Filters from URL params
  const [filters, setFilters] = useState<EntityFilters>({
    search: searchParams.get('search') || '',
    entity_type: searchParams.get('entity_type') as EntityFilters['entity_type'] || undefined,
    status: searchParams.get('status') as EntityFilters['status'] || undefined,
    risk_category: searchParams.get('risk_category') as EntityFilters['risk_category'] || undefined,
    page: parseInt(searchParams.get('page') || '1'),
    page_size: parseInt(searchParams.get('page_size') || '25'),
  });

  // Fetch entities
  const fetchEntities = useCallback(async () => {
    setLoading(true);
    try {
      const response: PaginatedResponse<Entity> = await entityApi.getEntities(filters);
      setEntities(response.items);
      setTotalCount(response.total);
      setTotalPages(response.total_pages);
    } catch (error) {
      logger.error('Failed to fetch entities:', error);
      toast({
        title: 'Failed to load entities',
        description:
          (error as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
          'Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [filters, toast]);

  useEffect(() => {
    fetchEntities();
  }, [fetchEntities]);

  // Update URL params when filters change
  useEffect(() => {
    const params = new URLSearchParams();
    if (filters.search) params.set('search', filters.search);
    if (filters.entity_type) params.set('entity_type', filters.entity_type);
    if (filters.status) params.set('status', filters.status);
    if (filters.risk_category) params.set('risk_category', filters.risk_category);
    if (filters.page && filters.page > 1) params.set('page', filters.page.toString());
    if (filters.page_size && filters.page_size !== 25) params.set('page_size', filters.page_size.toString());
    setSearchParams(params);
  }, [filters, setSearchParams]);

  // Handle filter changes
  const updateFilter = (key: keyof EntityFilters, value: string | number | undefined) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      page: key !== 'page' ? 1 : (value as number), // Reset page when other filters change
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

  // Delete entity
  const handleDelete = async (entityId: string) => {
    if (!confirm('Are you sure you want to delete this entity?')) return;
    try {
      await entityApi.deleteEntity(entityId);
      fetchEntities();
      toast({ title: 'Entity deleted', description: 'The entity has been removed.' });
    } catch (error) {
      logger.error('Failed to delete entity:', error);
      toast({
        title: 'Delete failed',
        description:
          (error as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
          'Unable to delete the entity.',
        variant: 'destructive',
      });
    }
  };

  // Pagination
  const handlePageChange = (page: number) => {
    updateFilter('page', page);
  };

  const hasActiveFilters = filters.search || filters.entity_type || filters.status || filters.risk_category;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Entities / Borrowers"
        subtitle="Manage borrower entities, their KYC documents, and credit ratings"
        actions={
          <Button onClick={() => navigate('/admin/lending/entities/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Entity
          </Button>
        }
      />

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
                placeholder="Search by name, PAN, CIN, GSTIN..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="pl-9"
              />
            </div>

            {/* Entity Type */}
            <Select
              value={filters.entity_type || 'all'}
              onValueChange={(value) => updateFilter('entity_type', value === 'all' ? undefined : value as EntityFilters['entity_type'])}
            >
              <SelectTrigger>
                <SelectValue placeholder="Entity Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {ENTITY_TYPES.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Status */}
            <Select
              value={filters.status || 'all'}
              onValueChange={(value) => updateFilter('status', value === 'all' ? undefined : value as EntityFilters['status'])}
            >
              <SelectTrigger>
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                {ENTITY_STATUSES.map((status) => (
                  <SelectItem key={status.value} value={status.value}>
                    {status.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Risk Category */}
            <Select
              value={filters.risk_category || 'all'}
              onValueChange={(value) => updateFilter('risk_category', value === 'all' ? undefined : value as EntityFilters['risk_category'])}
            >
              <SelectTrigger>
                <SelectValue placeholder="Risk Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Risk Levels</SelectItem>
                {RISK_CATEGORIES.map((risk) => (
                  <SelectItem key={risk.value} value={risk.value}>
                    {risk.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Active filters and clear button */}
          {hasActiveFilters && (
            <div className="mt-4 flex items-center gap-2">
              <span className="text-sm text-gray-500">Active filters:</span>
              {filters.search && (
                <Badge variant="secondary" className="gap-1">
                  Search: {filters.search}
                </Badge>
              )}
              {filters.entity_type && (
                <Badge variant="secondary">
                  Type: {ENTITY_TYPES.find(t => t.value === filters.entity_type)?.label}
                </Badge>
              )}
              {filters.status && (
                <Badge variant="secondary">
                  Status: {ENTITY_STATUSES.find(s => s.value === filters.status)?.label}
                </Badge>
              )}
              {filters.risk_category && (
                <Badge variant="secondary">
                  Risk: {RISK_CATEGORIES.find(r => r.value === filters.risk_category)?.label}
                </Badge>
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
              {loading ? (
                'Loading...'
              ) : (
                `Showing ${entities.length} of ${totalCount} entities`
              )}
            </CardDescription>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={fetchEntities}>
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
                <TableHead className="w-[200px]">Entity Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>PAN</TableHead>
                <TableHead>Rating</TableHead>
                <TableHead>Risk</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="w-[80px]">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                // Loading skeletons
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell><Skeleton className="h-4 w-40" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-12" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-16" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-16" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-8" /></TableCell>
                  </TableRow>
                ))
              ) : entities.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8 text-gray-500">
                    No entities found. {hasActiveFilters && 'Try adjusting your filters.'}
                  </TableCell>
                </TableRow>
              ) : (
                entities.map((entity) => (
                  <TableRow
                    key={entity.entity_id}
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => navigate(`/admin/lending/entities/${entity.entity_id}`)}
                  >
                    <TableCell className="font-medium">
                      <div>
                        <div className="font-medium text-gray-900">{entity.legal_name}</div>
                        <div className="text-xs text-gray-500">{entity.entity_code}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {ENTITY_TYPES.find(t => t.value === entity.entity_type)?.label || entity.entity_type}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-sm">{entity.pan}</TableCell>
                    <TableCell>
                      {entity.internal_rating ? (
                        <RatingBadge rating={entity.internal_rating} />
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {entity.risk_category ? (
                        <RiskCategoryBadge status={entity.risk_category} />
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <EntityStatusBadge status={entity.status} />
                    </TableCell>
                    <TableCell>
                      <DateDisplay date={entity.created_at} />
                    </TableCell>
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => navigate(`/admin/lending/entities/${entity.entity_id}`)}>
                            <Eye className="mr-2 h-4 w-4" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => navigate(`/admin/lending/entities/${entity.entity_id}/edit`)}>
                            <Edit className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            className="text-red-600"
                            onClick={() => handleDelete(entity.entity_id)}
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete
                          </DropdownMenuItem>
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
