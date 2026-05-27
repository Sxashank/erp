/**
 * Chart Definition List Page
 */

import { Plus, Edit, Trash2, Loader2, BarChart3, Search } from 'lucide-react';
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useToast } from '@/hooks/use-toast';
import { hasPermission, Permissions } from '@/lib/permissions';
import { biChartApi } from '@/services/biApi';
import { useAuthStore } from '@/stores/authStore';
import type { ChartDefinitionListItem, BIModule, ChartType } from '@/types/bi';

import { logger } from '@/lib/logger';
const MODULES: BIModule[] = [
  'FINANCE',
  'LENDING',
  'HR',
  'TREASURY',
  'PROCUREMENT',
  'INVENTORY',
  'TAX',
  'COLLECTIONS',
  'LEGAL',
  'PORTAL',
];

const CHART_TYPES: ChartType[] = ['LINE', 'BAR', 'PIE', 'DONUT', 'AREA', 'GAUGE', 'KPI', 'TABLE'];

export function ChartDefinitionList() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [charts, setCharts] = useState<ChartDefinitionListItem[]>([]);
  const [filteredCharts, setFilteredCharts] = useState<ChartDefinitionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [moduleFilter, setModuleFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');

  // Permissions
  const userPermissions = Array.from(useAuthStore((state) => state.permissions));
  const canCreate = hasPermission(userPermissions, Permissions.BI_CHART_CREATE);
  const canEdit = hasPermission(userPermissions, Permissions.BI_CHART_UPDATE);
  const canDelete = hasPermission(userPermissions, Permissions.BI_CHART_DELETE);

  const fetchCharts = async () => {
    try {
      setLoading(true);
      const response = await biChartApi.list();
      setCharts(response.data);
      setFilteredCharts(response.data);
    } catch (error) {
      logger.error('Error fetching charts:', error);
      toast({
        title: 'Error',
        description: 'Failed to load chart definitions',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCharts();
  }, []);

  // Apply filters
  useEffect(() => {
    let result = charts;

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (c) => c.name.toLowerCase().includes(query) || c.code.toLowerCase().includes(query),
      );
    }

    if (moduleFilter !== 'all') {
      result = result.filter((c) => c.module === moduleFilter);
    }

    if (typeFilter !== 'all') {
      result = result.filter((c) => c.chart_type === typeFilter);
    }

    setFilteredCharts(result);
  }, [charts, searchQuery, moduleFilter, typeFilter]);

  const handleDelete = async () => {
    if (!deleteId) return;

    try {
      setDeleting(true);
      await biChartApi.delete(deleteId);
      toast({
        title: 'Success',
        description: 'Chart definition deleted successfully',
      });
      fetchCharts();
    } catch (error) {
      logger.error('Error deleting chart:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete chart definition',
        variant: 'destructive',
      });
    } finally {
      setDeleting(false);
      setDeleteId(null);
    }
  };

  const getChartTypeColor = (type: ChartType) => {
    const colors: Record<ChartType, string> = {
      LINE: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
      BAR: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
      PIE: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
      DONUT: 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-300',
      AREA: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-300',
      GAUGE: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
      KPI: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
      TABLE: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Chart Definitions"
        subtitle="Pre-designed charts that can be added to dashboards"
        actions={
          canCreate ? (
            <Button onClick={() => navigate('/admin/bi/chart-definitions/new')}>
              <Plus className="mr-2 h-4 w-4" />
              New Chart
            </Button>
          ) : undefined
        }
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              All Charts ({filteredCharts.length})
            </CardTitle>
            <div className="flex items-center gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search charts..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-64 pl-10"
                />
              </div>
              <Select value={moduleFilter} onValueChange={setModuleFilter}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Module" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Modules</SelectItem>
                  {MODULES.map((m) => (
                    <SelectItem key={m} value={m}>
                      {m}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  {CHART_TYPES.map((t) => (
                    <SelectItem key={t} value={t}>
                      {t}
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
          ) : filteredCharts.length === 0 ? (
            <div className="py-8 text-center text-muted-foreground">
              {charts.length === 0
                ? 'No chart definitions found. Create your first chart to get started.'
                : 'No charts match your filters.'}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Code</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Module</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredCharts.map((chart) => (
                  <TableRow key={chart.id}>
                    <TableCell className="font-mono text-sm">{chart.code}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {chart.name}
                        {chart.is_system && <Badge variant="secondary">System</Badge>}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{chart.module}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={getChartTypeColor(chart.chart_type)}>
                        {chart.chart_type}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {chart.has_data_source ? 'Connected' : 'None'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        {canEdit && !chart.is_system && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => navigate(`/admin/bi/chart-definitions/${chart.id}/edit`)}
                            title="Edit"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                        )}
                        {canDelete && !chart.is_system && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setDeleteId(chart.id)}
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

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Chart Definition</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this chart definition? This action cannot be undone.
              Widgets using this chart will lose their chart reference.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleting}
              className="bg-red-600 hover:bg-red-700"
            >
              {deleting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
