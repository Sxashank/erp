/**
 * Document Search Page
 * Advanced search for documents with filters
 */

import {
  Search,
  Filter,
  File,
  FileText,
  FileImage,
  FileSpreadsheet,
  Calendar,
  Tag,
  Folder,
  ChevronDown,
  X,
  SlidersHorizontal,
  RefreshCw,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { documentApi, tagApi, folderApi } from '@/services/dmsApi';
import type { DMSDocument, DMSTag, DMSFolder, DocumentSearchParams, FolderTreeNode } from '@/types/dms';
import { formatFileSize, DOCUMENT_TYPES } from '@/types/dms';

import { logger } from "@/lib/logger";
export default function DocumentSearch() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // Search state
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [results, setResults] = useState<DMSDocument[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  // Pagination
  const [page, setPage] = useState(1);
  const limit = 20;

  // Filters
  const [showFilters, setShowFilters] = useState(true);
  const [filters, setFilters] = useState<DocumentSearchParams>({
    document_type: searchParams.get('type') || undefined,
    folder_id: searchParams.get('folder') || undefined,
    tags: searchParams.get('tags') || undefined,
    date_from: searchParams.get('from') || undefined,
    date_to: searchParams.get('to') || undefined,
    include_archived: searchParams.get('archived') === 'true',
  });

  // Filter options
  const [tags, setTags] = useState<DMSTag[]>([]);
  const [folders, setFolders] = useState<DMSFolder[]>([]);

  useEffect(() => {
    // Load filter options
    const loadOptions = async () => {
      try {
        const [tagsData, foldersData] = await Promise.all([
          tagApi.list({ limit: 100 }),
          folderApi.getTree({ max_depth: 3 }),
        ]);
        setTags(tagsData.items);

        // Flatten folder tree
        const flattenTree = (nodes: FolderTreeNode[], level = 0): DMSFolder[] => {
          let result: DMSFolder[] = [];
          for (const node of nodes) {
            result.push({ ...node, level } as unknown as DMSFolder);
            if (node.children?.length) {
              result = result.concat(flattenTree(node.children, level + 1));
            }
          }
          return result;
        };
        setFolders(flattenTree(foldersData));
      } catch (error) {
        logger.error('Failed to load filter options:', error);
      }
    };
    loadOptions();
  }, []);

  const performSearch = async () => {
    setLoading(true);
    try {
      const response = await documentApi.search({
        query: query || undefined,
        ...filters,
        skip: (page - 1) * limit,
        limit,
      });
      setResults(response.items);
      setTotal(response.total);
    } catch (error) {
      logger.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    performSearch();
  }, [page, filters]);

  const handleSearch = () => {
    setPage(1);
    performSearch();

    // Update URL params
    const params = new URLSearchParams();
    if (query) params.set('q', query);
    if (filters.document_type) params.set('type', filters.document_type);
    if (filters.folder_id) params.set('folder', filters.folder_id);
    if (filters.tags) params.set('tags', filters.tags);
    if (filters.date_from) params.set('from', filters.date_from);
    if (filters.date_to) params.set('to', filters.date_to);
    if (filters.include_archived) params.set('archived', 'true');
    setSearchParams(params);
  };

  const clearFilters = () => {
    setFilters({
      include_archived: false,
    });
    setQuery('');
    setPage(1);
    setSearchParams({});
  };

  const getDocIcon = (doc: DMSDocument) => {
    const ext = doc.file_extension?.toLowerCase() || '';
    if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(ext)) {
      return <FileImage className="h-10 w-10 text-green-500" />;
    }
    if (['xlsx', 'xls', 'csv'].includes(ext)) {
      return <FileSpreadsheet className="h-10 w-10 text-emerald-500" />;
    }
    if (ext === 'pdf') {
      return <FileText className="h-10 w-10 text-red-500" />;
    }
    return <File className="h-10 w-10 text-gray-500" />;
  };

  const hasActiveFilters = () => {
    return (
      filters.document_type ||
      filters.folder_id ||
      filters.tags ||
      filters.date_from ||
      filters.date_to ||
      filters.include_archived
    );
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="Search Documents"
        subtitle="Find documents using search and filters"
        breadcrumbs={[
          { label: 'DMS', to: '/admin/dms' },
          { label: 'Search' },
        ]}
      />

      {/* Search Bar */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search documents by name, content, or keywords..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="pl-10"
              />
            </div>
            <Button onClick={handleSearch}>
              <Search className="h-4 w-4 mr-2" />
              Search
            </Button>
            <Button
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
            >
              <SlidersHorizontal className="h-4 w-4 mr-2" />
              Filters
              {hasActiveFilters() && (
                <Badge variant="secondary" className="ml-2">
                  Active
                </Badge>
              )}
            </Button>
          </div>

          {/* Filters Panel */}
          <Collapsible open={showFilters}>
            <CollapsibleContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Document Type */}
                <div>
                  <Label>Document Type</Label>
                  <Select
                    value={filters.document_type || 'all'}
                    onValueChange={(value) =>
                      setFilters({
                        ...filters,
                        document_type: value === 'all' ? undefined : value,
                      })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All types" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All types</SelectItem>
                      {DOCUMENT_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Folder */}
                <div>
                  <Label>Folder</Label>
                  <Select
                    value={filters.folder_id || 'all'}
                    onValueChange={(value) =>
                      setFilters({
                        ...filters,
                        folder_id: value === 'all' ? undefined : value,
                      })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All folders" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All folders</SelectItem>
                      {folders.map((folder) => (
                        <SelectItem key={folder.id} value={folder.id}>
                          <span style={{ paddingLeft: (folder.level || 0) * 12 }}>
                            {folder.name}
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Date From */}
                <div>
                  <Label>From Date</Label>
                  <Input
                    type="date"
                    value={filters.date_from || ''}
                    onChange={(e) =>
                      setFilters({ ...filters, date_from: e.target.value || undefined })
                    }
                  />
                </div>

                {/* Date To */}
                <div>
                  <Label>To Date</Label>
                  <Input
                    type="date"
                    value={filters.date_to || ''}
                    onChange={(e) =>
                      setFilters({ ...filters, date_to: e.target.value || undefined })
                    }
                  />
                </div>

                {/* Tags */}
                <div>
                  <Label>Tags</Label>
                  <Select
                    value={filters.tags || 'all'}
                    onValueChange={(value) =>
                      setFilters({
                        ...filters,
                        tags: value === 'all' ? undefined : value,
                      })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All tags" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All tags</SelectItem>
                      {tags.map((tag) => (
                        <SelectItem key={tag.id} value={tag.name}>
                          <div className="flex items-center gap-2">
                            {tag.color && (
                              <div
                                className="h-3 w-3 rounded-full"
                                style={{ backgroundColor: tag.color }}
                              />
                            )}
                            {tag.name}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Include Archived */}
                <div className="flex items-center space-x-2 pt-6">
                  <Checkbox
                    id="archived"
                    checked={filters.include_archived}
                    onCheckedChange={(checked) =>
                      setFilters({ ...filters, include_archived: !!checked })
                    }
                  />
                  <label
                    htmlFor="archived"
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    Include archived
                  </label>
                </div>

                {/* Clear Filters */}
                <div className="pt-6">
                  <Button
                    variant="outline"
                    onClick={clearFilters}
                    disabled={!hasActiveFilters() && !query}
                  >
                    <X className="h-4 w-4 mr-2" />
                    Clear Filters
                  </Button>
                </div>
              </div>
            </CollapsibleContent>
          </Collapsible>
        </CardContent>
      </Card>

      {/* Results */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            {loading ? (
              'Searching...'
            ) : (
              <>
                Found <strong>{total}</strong> document{total !== 1 ? 's' : ''}
              </>
            )}
          </p>
          <Button variant="ghost" size="sm" onClick={performSearch}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>

        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-24" />
            ))}
          </div>
        ) : results.length === 0 ? (
          <Card className="p-12">
            <div className="text-center">
              <Search className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No documents found</h3>
              <p className="text-muted-foreground">
                Try adjusting your search terms or filters
              </p>
            </div>
          </Card>
        ) : (
          <div className="space-y-3">
            {results.map((doc) => (
              <Card
                key={doc.id}
                className="cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => navigate(`/admin/dms/documents/${doc.id}`)}
              >
                <CardContent className="flex items-center gap-4 p-4">
                  {getDocIcon(doc)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium truncate">{doc.name}</h3>
                      <Badge variant="outline" className="shrink-0">
                        v{doc.current_version}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground truncate">
                      {doc.file_name}
                    </p>
                    <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                      <span>{formatFileSize(doc.file_size)}</span>
                      <span>{doc.file_extension?.toUpperCase()}</span>
                      {doc.document_type && (
                        <Badge variant="secondary" className="text-xs">
                          {doc.document_type}
                        </Badge>
                      )}
                      <DateDisplay date={doc.created_at} />
                    </div>
                    {doc.description && (
                      <p className="text-sm text-muted-foreground mt-2 line-clamp-1">
                        {doc.description}
                      </p>
                    )}
                  </div>
                  <div className="text-right shrink-0">
                    <Badge
                      variant={doc.status === 'active' ? 'default' : 'secondary'}
                    >
                      {doc.status}
                    </Badge>
                    <p className="text-xs text-muted-foreground mt-1">
                      {doc.access_level}
                    </p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <Pagination>
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious
                  onClick={() => setPage(Math.max(1, page - 1))}
                  className={page === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                />
              </PaginationItem>
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (page <= 3) {
                  pageNum = i + 1;
                } else if (page >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = page - 2 + i;
                }
                return (
                  <PaginationItem key={pageNum}>
                    <PaginationLink
                      onClick={() => setPage(pageNum)}
                      isActive={page === pageNum}
                      className="cursor-pointer"
                    >
                      {pageNum}
                    </PaginationLink>
                  </PaginationItem>
                );
              })}
              <PaginationItem>
                <PaginationNext
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  className={
                    page === totalPages ? 'pointer-events-none opacity-50' : 'cursor-pointer'
                  }
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        )}
      </div>
    </div>
  );
}
