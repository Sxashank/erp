/**
 * Entity List Page
 * Displays list of entities/borrowers with filters and actions.
 *
 * Data source: GET /lending/entities (camelCase via Pydantic CamelSchema).
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
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { RatingBadge } from '@/components/lending/common/RatingBadge';
import { EntityStatusBadge, RiskCategoryBadge } from '@/components/lending/common/StatusBadge';
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
import {
  useEntities,
  type EntityFilters,
  type EntityStatusValue,
} from '@/hooks/lending/useEntities';
import { masterRowsToOptions, useLendingOptionRows } from '@/hooks/lending/useLendingMasters';
import { useToast } from '@/hooks/use-toast';
import { logger } from '@/lib/logger';
import { entityApi } from '@/services/lending';

const ENTITY_STATUSES: { value: EntityStatusValue; label: string }[] = [
  { value: 'PROSPECT', label: 'Prospect' },
  { value: 'ACTIVE', label: 'Active' },
  { value: 'INACTIVE', label: 'Inactive' },
  { value: 'BLACKLISTED', label: 'Blacklisted' },
];

const PAGE_SIZES = [10, 25, 50, 100];

export default function EntityList() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();

  const [searchInput, setSearchInput] = useState(searchParams.get('search') ?? '');
  const entityTypesQuery = useLendingOptionRows('ENTITY_TYPE_CORPORATE');
  const riskGradesQuery = useLendingOptionRows('RISK_GRADE');
  const entityTypes = masterRowsToOptions(entityTypesQuery.data?.items);
  const riskGrades = masterRowsToOptions(riskGradesQuery.data?.items);

  const filters: EntityFilters = useMemo(
    () => ({
      search: searchParams.get('search') || undefined,
      entityType: searchParams.get('entityType') || undefined,
      status: (searchParams.get('status') as EntityStatusValue) || undefined,
      riskCategory: searchParams.get('riskCategory') || undefined,
      page: parseInt(searchParams.get('page') ?? '1', 10),
      pageSize: parseInt(searchParams.get('pageSize') ?? '25', 10),
    }),
    [searchParams],
  );

  const { data, isLoading, isError, error, refetch, isFetching } = useEntities(filters);
  const entities = data?.items ?? [];
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

  const handleDelete = async (entityId: string) => {
    if (!confirm('Are you sure you want to delete this entity?')) return;
    try {
      await entityApi.deleteEntity(entityId);
      queryClient.invalidateQueries({ queryKey: ['lending', 'entities'] });
      toast({ title: 'Entity deleted' });
    } catch (err: unknown) {
      logger.error('Failed to delete entity:', err);
      toast({
        title: 'Delete failed',
        description:
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
          'Unable to delete the entity.',
        variant: 'destructive',
      });
    }
  };

  const hasActiveFilters =
    filters.search || filters.entityType || filters.status || filters.riskCategory;

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
                placeholder="Search by name, PAN, CIN, GSTIN..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select
              value={filters.entityType || 'all'}
              onValueChange={(v) => updateParam('entityType', v === 'all' ? undefined : v)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Entity Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {entityTypes.map((t) => (
                  <SelectItem key={t.value} value={t.value}>
                    {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={filters.status || 'all'}
              onValueChange={(v) => updateParam('status', v === 'all' ? undefined : v)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                {ENTITY_STATUSES.map((s) => (
                  <SelectItem key={s.value} value={s.value}>
                    {s.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={filters.riskCategory || 'all'}
              onValueChange={(v) => updateParam('riskCategory', v === 'all' ? undefined : v)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Risk Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Risk Levels</SelectItem>
                {riskGrades.map((r) => (
                  <SelectItem key={r.value} value={r.value}>
                    {r.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {hasActiveFilters && (
            <div className="mt-4 flex flex-wrap items-center gap-2">
              <span className="text-sm text-muted-foreground">Active filters:</span>
              {filters.search && <Badge variant="secondary">Search: {filters.search}</Badge>}
              {filters.entityType && (
                <Badge variant="secondary">
                  Type: {entityTypes.find((t) => t.value === filters.entityType)?.label}
                </Badge>
              )}
              {filters.status && (
                <Badge variant="secondary">
                  Status: {ENTITY_STATUSES.find((s) => s.value === filters.status)?.label}
                </Badge>
              )}
              {filters.riskCategory && (
                <Badge variant="secondary">
                  Risk: {riskGrades.find((r) => r.value === filters.riskCategory)?.label}
                </Badge>
              )}
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                Clear all
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardDescription>
              {isLoading ? 'Loading...' : `Showing ${entities.length} of ${totalCount} entities`}
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
                <TableHead className="w-[240px]">Entity Name</TableHead>
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
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                    <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />
                    Loading entities...
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8">
                    <ErrorState
                      title="Could not load entities"
                      error={error}
                      onRetry={() => refetch()}
                    />
                  </TableCell>
                </TableRow>
              ) : entities.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                    No entities found.
                    {hasActiveFilters && ' Try adjusting your filters.'}
                  </TableCell>
                </TableRow>
              ) : (
                entities.map((entity) => (
                  <TableRow
                    key={entity.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => navigate(`/admin/lending/entities/${entity.id}`)}
                  >
                    <TableCell>
                      <div className="font-medium">{entity.legalName}</div>
                      <div className="text-xs text-muted-foreground">
                        {entity.entityCode}
                        {entity.tradeName ? ` · ${entity.tradeName}` : ''}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {entityTypes.find((t) => t.value === entity.entityType)?.label ??
                          entity.entityType}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-sm">{entity.pan}</TableCell>
                    <TableCell>
                      {entity.internalRating ? (
                        <RatingBadge rating={entity.internalRating} />
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {entity.riskCategory ? (
                        <RiskCategoryBadge status={entity.riskCategory} />
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <EntityStatusBadge status={entity.status} />
                    </TableCell>
                    <TableCell>
                      <DateDisplay date={entity.createdAt} />
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
                            onClick={() => navigate(`/admin/lending/entities/${entity.id}`)}
                          >
                            <Eye className="mr-2 h-4 w-4" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => navigate(`/admin/lending/entities/${entity.id}/edit`)}
                          >
                            <Edit className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            className="text-red-600"
                            onClick={() => handleDelete(entity.id)}
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
