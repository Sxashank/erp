/**
 * Dashboard Access Configuration Page
 * Configure which roles can view/edit the dashboard
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, Plus, Save, Trash2, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetFooter,
} from '@/components/ui/sheet';
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
import { useToast } from '@/hooks/use-toast';
import { biDashboardApi, biDashboardAccessApi } from '@/services/biApi';
import { rolesApi } from '@/services/api';
import { Dashboard, DashboardRoleAccess, DashboardRoleAccessCreate } from '@/types/bi';

interface Role {
  id: string;
  name: string;
  code: string;
}

export function DashboardAccessConfig() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [accessList, setAccessList] = useState<DashboardRoleAccess[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Add access drawer state
  const [addDrawerOpen, setAddDrawerOpen] = useState(false);
  const [newAccess, setNewAccess] = useState<Partial<DashboardRoleAccessCreate>>({
    can_view: true,
    can_edit: false,
    show_on_landing: false,
    landing_order: 0,
  });

  // Delete confirmation state
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const fetchData = async () => {
    if (!id) return;

    try {
      setLoading(true);
      const [dashboardRes, accessRes] = await Promise.all([
        biDashboardApi.get(id),
        biDashboardAccessApi.list(id),
      ]);
      setDashboard(dashboardRes.data);
      setAccessList(accessRes.data);

      const rolesRes = await rolesApi.list();
      const roleList = Array.isArray(rolesRes.data) ? rolesRes.data : rolesRes.data.items ?? [];
      setRoles(
        roleList.map((r: { id: string; code: string; name: string }) => ({
          id: r.id,
          code: r.code,
          name: r.name,
        })),
      );
    } catch (error) {
      console.error('Error fetching data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load dashboard access configuration',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  const handleAddAccess = async () => {
    if (!id || !newAccess.role_id) {
      toast({
        title: 'Error',
        description: 'Please select a role',
        variant: 'destructive',
      });
      return;
    }

    // Check if role already has access
    if (accessList.some((a) => a.role_id === newAccess.role_id)) {
      toast({
        title: 'Error',
        description: 'This role already has access configured',
        variant: 'destructive',
      });
      return;
    }

    try {
      setSaving(true);
      await biDashboardAccessApi.create(id, newAccess as DashboardRoleAccessCreate);
      toast({
        title: 'Success',
        description: 'Role access added successfully',
      });
      setAddDrawerOpen(false);
      setNewAccess({
        can_view: true,
        can_edit: false,
        show_on_landing: false,
        landing_order: 0,
      });
      fetchData();
    } catch (error: any) {
      console.error('Error adding access:', error);
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to add role access',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateAccess = async (
    accessId: string,
    field: keyof DashboardRoleAccess,
    value: boolean | number
  ) => {
    if (!id) return;

    try {
      const access = accessList.find((a) => a.id === accessId);
      if (!access) return;

      await biDashboardAccessApi.update(id, accessId, {
        [field]: value,
      });

      setAccessList((prev) =>
        prev.map((a) => (a.id === accessId ? { ...a, [field]: value } : a))
      );

      toast({
        title: 'Success',
        description: 'Access updated successfully',
      });
    } catch (error) {
      console.error('Error updating access:', error);
      toast({
        title: 'Error',
        description: 'Failed to update access',
        variant: 'destructive',
      });
      fetchData(); // Refresh to get correct state
    }
  };

  const handleDeleteAccess = async () => {
    if (!id || !deleteId) return;

    try {
      setDeleting(true);
      await biDashboardAccessApi.delete(id, deleteId);
      toast({
        title: 'Success',
        description: 'Role access removed successfully',
      });
      fetchData();
    } catch (error) {
      console.error('Error deleting access:', error);
      toast({
        title: 'Error',
        description: 'Failed to remove role access',
        variant: 'destructive',
      });
    } finally {
      setDeleting(false);
      setDeleteId(null);
    }
  };

  const getRoleName = (roleId: string) => {
    const role = roles.find((r) => r.id === roleId);
    return role?.name || roleId;
  };

  const getAvailableRoles = () => {
    const assignedRoleIds = accessList.map((a) => a.role_id);
    return roles.filter((r) => !assignedRoleIds.includes(r.id));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Dashboard not found</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => navigate('/admin/bi/dashboards')}
        >
          Back to Dashboards
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate(`/admin/bi/dashboards/${id}/edit`)}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Access Configuration</h1>
            <p className="text-muted-foreground">
              Configure role access for "{dashboard.name}"
            </p>
          </div>
        </div>
        <Button onClick={() => setAddDrawerOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Role Access
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Role Access
          </CardTitle>
          <CardDescription>
            Define which roles can view or edit this dashboard, and whether it appears on their landing page.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {accessList.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No role access configured.</p>
              <p className="text-sm">
                {dashboard.is_public
                  ? 'This is a public dashboard - all users can view it.'
                  : 'Add roles to grant access to this dashboard.'}
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Role</TableHead>
                  <TableHead className="text-center">Can View</TableHead>
                  <TableHead className="text-center">Can Edit</TableHead>
                  <TableHead className="text-center">Show on Landing</TableHead>
                  <TableHead className="text-center">Landing Order</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {accessList.map((access) => (
                  <TableRow key={access.id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getRoleName(access.role_id)}
                        {access.can_edit && (
                          <Badge variant="secondary">Editor</Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <Switch
                        checked={access.can_view}
                        onCheckedChange={(checked) =>
                          handleUpdateAccess(access.id, 'can_view', checked)
                        }
                      />
                    </TableCell>
                    <TableCell className="text-center">
                      <Switch
                        checked={access.can_edit}
                        onCheckedChange={(checked) =>
                          handleUpdateAccess(access.id, 'can_edit', checked)
                        }
                      />
                    </TableCell>
                    <TableCell className="text-center">
                      <Switch
                        checked={access.show_on_landing}
                        onCheckedChange={(checked) =>
                          handleUpdateAccess(access.id, 'show_on_landing', checked)
                        }
                      />
                    </TableCell>
                    <TableCell className="text-center">
                      <Input
                        type="number"
                        min={0}
                        className="w-20 mx-auto text-center"
                        value={access.landing_order}
                        onChange={(e) =>
                          handleUpdateAccess(
                            access.id,
                            'landing_order',
                            parseInt(e.target.value) || 0
                          )
                        }
                        disabled={!access.show_on_landing}
                      />
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setDeleteId(access.id)}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {dashboard.is_public && (
        <Card className="border-blue-200 bg-blue-50 dark:bg-blue-950 dark:border-blue-800">
          <CardContent className="pt-6">
            <p className="text-sm text-blue-700 dark:text-blue-300">
              <strong>Note:</strong> This dashboard is marked as public, so all users can view it
              regardless of role access settings. Role access only controls edit permissions and
              landing page visibility for public dashboards.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Add Role Access Drawer */}
      <Sheet open={addDrawerOpen} onOpenChange={setAddDrawerOpen}>
        <SheetContent>
          <SheetHeader>
            <SheetTitle>Add Role Access</SheetTitle>
            <SheetDescription>
              Grant a role access to this dashboard
            </SheetDescription>
          </SheetHeader>

          <div className="space-y-6 py-6">
            <div className="space-y-2">
              <Label>Role *</Label>
              <Select
                value={newAccess.role_id || ''}
                onValueChange={(value) =>
                  setNewAccess((prev) => ({ ...prev, role_id: value }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a role" />
                </SelectTrigger>
                <SelectContent>
                  {getAvailableRoles().map((role) => (
                    <SelectItem key={role.id} value={role.id}>
                      {role.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {getAvailableRoles().length === 0 && (
                <p className="text-sm text-muted-foreground">
                  All roles have already been assigned access.
                </p>
              )}
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Can View</Label>
                <p className="text-sm text-muted-foreground">
                  Users with this role can view the dashboard
                </p>
              </div>
              <Switch
                checked={newAccess.can_view ?? true}
                onCheckedChange={(checked) =>
                  setNewAccess((prev) => ({ ...prev, can_view: checked }))
                }
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Can Edit</Label>
                <p className="text-sm text-muted-foreground">
                  Users with this role can edit the dashboard
                </p>
              </div>
              <Switch
                checked={newAccess.can_edit ?? false}
                onCheckedChange={(checked) =>
                  setNewAccess((prev) => ({ ...prev, can_edit: checked }))
                }
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Show on Landing Page</Label>
                <p className="text-sm text-muted-foreground">
                  Display this dashboard on the user's landing page
                </p>
              </div>
              <Switch
                checked={newAccess.show_on_landing ?? false}
                onCheckedChange={(checked) =>
                  setNewAccess((prev) => ({ ...prev, show_on_landing: checked }))
                }
              />
            </div>

            {newAccess.show_on_landing && (
              <div className="space-y-2">
                <Label>Landing Page Order</Label>
                <Input
                  type="number"
                  min={0}
                  value={newAccess.landing_order ?? 0}
                  onChange={(e) =>
                    setNewAccess((prev) => ({
                      ...prev,
                      landing_order: parseInt(e.target.value) || 0,
                    }))
                  }
                />
                <p className="text-sm text-muted-foreground">
                  Lower numbers appear first
                </p>
              </div>
            )}
          </div>

          <SheetFooter>
            <Button
              variant="outline"
              onClick={() => setAddDrawerOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleAddAccess}
              disabled={saving || !newAccess.role_id}
            >
              {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              <Save className="h-4 w-4 mr-2" />
              Add Access
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove Role Access</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to remove this role's access to the dashboard?
              Users with this role will no longer be able to view or edit the dashboard.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteAccess}
              disabled={deleting}
              className="bg-red-600 hover:bg-red-700"
            >
              {deleting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Remove Access
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
