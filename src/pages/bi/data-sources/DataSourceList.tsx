/**
 * Data Source List Page
 */

import { Plus, Edit, Trash2, Loader2, Database, Search, Eye } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useToast } from '@/hooks/use-toast';
import { hasPermission, Permissions } from '@/lib/permissions';
import { biDataSourceApi } from '@/services/biApi';
import type { DataSourceListItem, DataSourceType } from '@/types/bi';

import { logger } from "@/lib/logger";
const SOURCE_TYPES: DataSourceType[] = ['API_ENDPOINT', 'SQL_QUERY', 'STATIC'];

export function DataSourceList() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [dataSources, setDataSources] = useState<DataSourceListItem[]>([]);
  const [filteredDataSources, setFilteredDataSources] = useState<DataSourceListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Preview drawer state
  const [previewDrawerOpen, setPreviewDrawerOpen] = useState(false);
  const [previewId, setPreviewId] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<any>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');

  // Permissions
  const userPermissions = JSON.parse(localStorage.getItem('user_permissions') || '["SUPER_ADMIN"]');
  const canCreate = hasPermission(userPermissions, Permissions.BI_DATASOURCE_CREATE);
  const canEdit = hasPermission(userPermissions, Permissions.BI_DATASOURCE_UPDATE);
  const canDelete = hasPermission(userPermissions, Permissions.BI_DATASOURCE_DELETE);

  const fetchDataSources = async () => {
    try {
      setLoading(true);
      const response = await biDataSourceApi.list();
      setDataSources(response.data);
      setFilteredDataSources(response.data);
    } catch (error) {
      logger.error('Error fetching data sources:', error);
      toast({
        title: 'Error',
        description: 'Failed to load data sources',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDataSources();
  }, []);

  // Apply filters
  useEffect(() => {
    let result = dataSources;

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (ds) =>
          ds.name.toLowerCase().includes(query) ||
          ds.code.toLowerCase().includes(query)
      );
    }

    if (typeFilter !== 'all') {
      result = result.filter((ds) => ds.source_type === typeFilter);
    }

    setFilteredDataSources(result);
  }, [dataSources, searchQuery, typeFilter]);

  const handleDelete = async () => {
    if (!deleteId) return;

    try {
      setDeleting(true);
      await biDataSourceApi.delete(deleteId);
      toast({
        title: 'Success',
        description: 'Data source deleted successfully',
      });
      fetchDataSources();
    } catch (error) {
      logger.error('Error deleting data source:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete data source',
        variant: 'destructive',
      });
    } finally {
      setDeleting(false);
      setDeleteId(null);
    }
  };

  const handlePreview = async (id: string) => {
    setPreviewId(id);
    setPreviewDrawerOpen(true);
    setPreviewLoading(true);

    try {
      const response = await biDataSourceApi.preview(id);
      setPreviewData(response.data);
    } catch (error) {
      logger.error('Error fetching preview:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch data preview',
        variant: 'destructive',
      });
      setPreviewData(null);
    } finally {
      setPreviewLoading(false);
    }
  };

  const getSourceTypeColor = (type: DataSourceType) => {
    const colors: Record<DataSourceType, string> = {
      API_ENDPOINT: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
      SQL_QUERY: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
      STATIC: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Data Sources"
        subtitle="Configure data sources for BI widgets"
        actions={
          canCreate ? (
            <Button onClick={() => navigate('/admin/bi/data-sources/new')}>
              <Plus className="h-4 w-4 mr-2" />
              New Data Source
            </Button>
          ) : undefined
        }
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              All Data Sources ({filteredDataSources.length})
            </CardTitle>
            <div className="flex items-center gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search data sources..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 w-64"
                />
              </div>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  {SOURCE_TYPES.map((t) => (
                    <SelectItem key={t} value={t}>
                      {t.replace('_', ' ')}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : filteredDataSources.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              {dataSources.length === 0
                ? 'No data sources found. Create your first data source to get started.'
                : 'No data sources match your filters.'}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Code</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Cache TTL</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredDataSources.map((ds) => (
                  <TableRow key={ds.id}>
                    <TableCell className="font-mono text-sm">{ds.code}</TableCell>
                    <TableCell>{ds.name}</TableCell>
                    <TableCell>
                      <Badge className={getSourceTypeColor(ds.source_type)}>
                        {ds.source_type.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {ds.cache_ttl_seconds ? `${ds.cache_ttl_seconds}s` : 'No cache'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handlePreview(ds.id)}
                          title="Preview Data"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        {canEdit && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() =>
                              navigate(`/admin/bi/data-sources/${ds.id}/edit`)
                            }
                            title="Edit"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                        )}
                        {canDelete && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setDeleteId(ds.id)}
                            title="Delete"
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Preview Drawer */}
      <Sheet open={previewDrawerOpen} onOpenChange={setPreviewDrawerOpen}>
        <SheetContent className="sm:max-w-xl">
          <SheetHeader>
            <SheetTitle>Data Preview</SheetTitle>
            <SheetDescription>
              Preview data from this data source
            </SheetDescription>
          </SheetHeader>

          <div className="py-6">
            {previewLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : previewData ? (
              <div className="space-y-4">
                {previewData.data && Array.isArray(previewData.data) ? (
                  <div className="max-h-96 overflow-auto">
                    <pre className="text-xs bg-muted p-4 rounded-lg overflow-x-auto">
                      {JSON.stringify(previewData.data.slice(0, 10), null, 2)}
                    </pre>
                    {previewData.data.length > 10 && (
                      <p className="text-sm text-muted-foreground mt-2">
                        Showing first 10 of {previewData.data.length} records
                      </p>
                    )}
                  </div>
                ) : (
                  <pre className="text-xs bg-muted p-4 rounded-lg overflow-x-auto max-h-96">
                    {JSON.stringify(previewData, null, 2)}
                  </pre>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No data available or error fetching data
              </div>
            )}
          </div>
        </SheetContent>
      </Sheet>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Data Source</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this data source? This action cannot be undone.
              Charts and widgets using this data source will lose their data connection.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleting}
              className="bg-red-600 hover:bg-red-700"
            >
              {deleting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
