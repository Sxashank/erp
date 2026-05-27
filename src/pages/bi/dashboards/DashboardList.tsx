/**
 * Dashboard List Page
 */

import { Plus, Edit, Trash2, Eye, Settings, Star, StarOff, Loader2 } from 'lucide-react';
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
import { biDashboardApi } from '@/services/biApi';
import { useAuthStore } from '@/stores/authStore';
import type { DashboardListItem } from '@/types/bi';

import { logger } from '@/lib/logger';
export function DashboardList() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [dashboards, setDashboards] = useState<DashboardListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const userPermissions = Array.from(useAuthStore((state) => state.permissions));

  const canCreate = hasPermission(userPermissions, Permissions.BI_DASHBOARD_CREATE);
  const canEdit = hasPermission(userPermissions, Permissions.BI_DASHBOARD_UPDATE);
  const canDelete = hasPermission(userPermissions, Permissions.BI_DASHBOARD_DELETE);
  const canManageAccess = hasPermission(userPermissions, Permissions.BI_DASHBOARD_ACCESS_MANAGE);

  const fetchDashboards = async () => {
    try {
      setLoading(true);
      const response = await biDashboardApi.list();
      setDashboards(response.data);
    } catch (error) {
      logger.error('Error fetching dashboards:', error);
      toast({
        title: 'Error',
        description: 'Failed to load dashboards',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboards();
  }, []);

  const handleDelete = async () => {
    if (!deleteId) return;

    try {
      setDeleting(true);
      await biDashboardApi.delete(deleteId);
      toast({
        title: 'Success',
        description: 'Dashboard deleted successfully',
      });
      fetchDashboards();
    } catch (error) {
      logger.error('Error deleting dashboard:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete dashboard',
        variant: 'destructive',
      });
    } finally {
      setDeleting(false);
      setDeleteId(null);
    }
  };

  const handleSetDefault = async (id: string) => {
    try {
      await biDashboardApi.setDefault(id);
      toast({
        title: 'Success',
        description: 'Dashboard set as default',
      });
      fetchDashboards();
    } catch (error) {
      logger.error('Error setting default:', error);
      toast({
        title: 'Error',
        description: 'Failed to set default dashboard',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboards"
        subtitle="Manage custom BI dashboards"
        actions={
          canCreate ? (
            <Button onClick={() => navigate('/admin/bi/dashboards/new')}>
              <Plus className="mr-2 h-4 w-4" />
              New Dashboard
            </Button>
          ) : undefined
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>All Dashboards</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : dashboards.length === 0 ? (
            <div className="py-8 text-center text-muted-foreground">
              No dashboards found. Create your first dashboard to get started.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Code</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Widgets</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {dashboards.map((dashboard) => (
                  <TableRow key={dashboard.id}>
                    <TableCell className="font-mono text-sm">{dashboard.code}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {dashboard.name}
                        {dashboard.is_default && <Badge variant="secondary">Default</Badge>}
                      </div>
                    </TableCell>
                    <TableCell>{dashboard.widget_count}</TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        {dashboard.is_public && <Badge variant="outline">Public</Badge>}
                        <Badge variant={dashboard.is_active ? 'default' : 'secondary'}>
                          {dashboard.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => navigate(`/admin/bi/dashboards/${dashboard.id}`)}
                          title="View"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        {canEdit && (
                          <>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => navigate(`/admin/bi/dashboards/${dashboard.id}/edit`)}
                              title="Edit"
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleSetDefault(dashboard.id)}
                              title={dashboard.is_default ? 'Default Dashboard' : 'Set as Default'}
                              disabled={dashboard.is_default}
                            >
                              {dashboard.is_default ? (
                                <Star className="h-4 w-4 fill-yellow-500 text-yellow-500" />
                              ) : (
                                <StarOff className="h-4 w-4" />
                              )}
                            </Button>
                          </>
                        )}
                        {canManageAccess && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => navigate(`/admin/bi/dashboards/${dashboard.id}/access`)}
                            title="Manage Access"
                          >
                            <Settings className="h-4 w-4" />
                          </Button>
                        )}
                        {canDelete && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setDeleteId(dashboard.id)}
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
            <AlertDialogTitle>Delete Dashboard</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this dashboard? This action cannot be undone. All
              widgets in this dashboard will also be deleted.
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
