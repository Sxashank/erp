import { ArrowLeft, Check, Loader2, Save } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { rolesApi } from '@/services/api';
import type { RoleCreate, RoleUpdate, Role, Permission } from '@/types';

import { logger } from "@/lib/logger";
interface PermissionGroup {
  module: string;
  permissions: Permission[];
}

export function RoleForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [permissionGroups, setPermissionGroups] = useState<PermissionGroup[]>([]);
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);
  const [isSystemRole, setIsSystemRole] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<RoleCreate | RoleUpdate>();

  useEffect(() => {
    fetchPermissions();
  }, []);

  useEffect(() => {
    if (isEdit && id) {
      fetchRole(id);
    }
  }, [id, isEdit]);

  const fetchPermissions = async () => {
    try {
      const response = await rolesApi.getPermissionsGrouped();
      // Response is array of { module: string, permissions: Permission[] }
      const groups: PermissionGroup[] = response.data.map(
        (group: { module: string; permissions: Permission[] }) => ({
          module: group.module,
          permissions: group.permissions,
        })
      );
      setPermissionGroups(groups);
    } catch (error) {
      logger.error('Failed to fetch permissions:', error);
      // Fallback to flat list
      try {
        const response = await rolesApi.getPermissions();
        const allPerms: Permission[] = response.data;
        const grouped = allPerms.reduce((acc, perm) => {
          if (!acc[perm.module]) acc[perm.module] = [];
          acc[perm.module].push(perm);
          return acc;
        }, {} as Record<string, Permission[]>);
        const groups: PermissionGroup[] = Object.entries(grouped).map(
          ([module, permissions]) => ({ module, permissions })
        );
        setPermissionGroups(groups);
      } catch (e) {
        logger.error('Failed to fetch permissions (fallback):', e);
      }
    }
  };

  const fetchRole = async (roleId: string) => {
    try {
      setLoading(true);
      const response = await rolesApi.get(roleId);
      const role: Role = response.data;
      setIsSystemRole(role.is_system_role);
      reset({
        code: role.code,
        name: role.name,
        description: role.description || '',
        is_default: role.is_default,
      });
      setSelectedPermissions(role.permissions.map((p) => p.id));
    } catch (error) {
      logger.error('Failed to fetch role:', error);
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data: RoleCreate | RoleUpdate) => {
    try {
      setSubmitting(true);
      if (isEdit && id) {
        await rolesApi.update(id, data);
        // Update permissions separately
        await rolesApi.setPermissions(id, selectedPermissions);
      } else {
        const createData = {
          ...data,
          permission_ids: selectedPermissions,
        } as RoleCreate;
        await rolesApi.create(createData);
      }
      navigate('/admin/roles');
    } catch (error) {
      logger.error('Failed to save role:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const togglePermission = (permId: string) => {
    setSelectedPermissions((prev) =>
      prev.includes(permId) ? prev.filter((id) => id !== permId) : [...prev, permId]
    );
  };

  const toggleModule = (module: string) => {
    const group = permissionGroups.find((g) => g.module === module);
    if (!group) return;

    const allSelected = group.permissions.every((p) =>
      selectedPermissions.includes(p.id)
    );

    if (allSelected) {
      // Deselect all
      setSelectedPermissions((prev) =>
        prev.filter((id) => !group.permissions.some((p) => p.id === id))
      );
    } else {
      // Select all
      setSelectedPermissions((prev) => [
        ...prev,
        ...group.permissions.map((p) => p.id).filter((id) => !prev.includes(id)),
      ]);
    }
  };

  const isModuleSelected = (module: string) => {
    const group = permissionGroups.find((g) => g.module === module);
    if (!group) return false;
    return group.permissions.every((p) => selectedPermissions.includes(p.id));
  };

  const isModulePartiallySelected = (module: string) => {
    const group = permissionGroups.find((g) => g.module === module);
    if (!group) return false;
    const selectedCount = group.permissions.filter((p) =>
      selectedPermissions.includes(p.id)
    ).length;
    return selectedCount > 0 && selectedCount < group.permissions.length;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEdit ? 'Edit Role' : 'New Role'}
        subtitle={
          isEdit
            ? 'Update role details and permissions'
            : 'Create a new role with permissions'
        }
        breadcrumbs={[
          { label: 'Roles', to: '/admin/roles' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
            <CardDescription>Role identity and description</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="code">Role Code *</Label>
                <Input
                  id="code"
                  {...register('code', { required: 'Code is required' })}
                  placeholder="FINANCE_MANAGER"
                  disabled={isEdit}
                />
                {errors.code && (
                  <p className="text-sm text-red-500">{errors.code.message}</p>
                )}
                <p className="text-xs text-slate-500">Uppercase with underscores</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">Role Name *</Label>
                <Input
                  id="name"
                  {...register('name', { required: 'Name is required' })}
                  placeholder="Finance Manager"
                  disabled={isSystemRole}
                />
                {errors.name && (
                  <p className="text-sm text-red-500">{errors.name.message}</p>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                {...register('description')}
                placeholder="Describe the role and its responsibilities"
                rows={3}
                disabled={isSystemRole}
              />
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_default"
                checked={watch('is_default')}
                onCheckedChange={(checked) => setValue('is_default', checked as boolean)}
                disabled={isSystemRole}
              />
              <Label htmlFor="is_default">Default role for new users</Label>
            </div>

            {isSystemRole && (
              <p className="text-sm text-amber-600">
                This is a system role. Some fields cannot be modified.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Permissions */}
        <Card>
          <CardHeader>
            <CardTitle>Permissions</CardTitle>
            <CardDescription>
              Select permissions for this role ({selectedPermissions.length} selected)
            </CardDescription>
          </CardHeader>
          <CardContent>
            {permissionGroups.length === 0 ? (
              <p className="text-sm text-slate-500">Loading permissions...</p>
            ) : (
              <div className="space-y-6">
                {permissionGroups.map((group) => (
                  <div key={group.module} className="space-y-3">
                    <div
                      className="flex cursor-pointer items-center gap-2 rounded-lg bg-slate-100 px-3 py-2"
                      onClick={() => toggleModule(group.module)}
                    >
                      <Checkbox
                        checked={isModuleSelected(group.module)}
                        className={
                          isModulePartiallySelected(group.module) ? 'opacity-50' : ''
                        }
                        onCheckedChange={() => toggleModule(group.module)}
                      />
                      <span className="font-medium">{group.module}</span>
                      <span className="ml-auto text-sm text-slate-500">
                        {
                          group.permissions.filter((p) =>
                            selectedPermissions.includes(p.id)
                          ).length
                        }
                        /{group.permissions.length}
                      </span>
                    </div>
                    <div className="ml-4 grid gap-2 md:grid-cols-2 lg:grid-cols-3">
                      {group.permissions.map((perm) => (
                        <div
                          key={perm.id}
                          className={`flex cursor-pointer items-center gap-2 rounded-lg border p-3 transition-colors ${
                            selectedPermissions.includes(perm.id)
                              ? 'border-blue-500 bg-blue-50'
                              : 'border-slate-200 hover:border-slate-300'
                          }`}
                          onClick={() => togglePermission(perm.id)}
                        >
                          <Checkbox
                            checked={selectedPermissions.includes(perm.id)}
                            onCheckedChange={() => togglePermission(perm.id)}
                          />
                          <div className="flex-1 overflow-hidden">
                            <p className="truncate text-sm font-medium">{perm.name}</p>
                            <p className="truncate text-xs text-slate-500">{perm.code}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Form Actions */}
        <div className="flex items-center justify-end gap-4">
          <Button type="button" variant="outline" onClick={() => navigate('/admin/roles')}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Save className="mr-2 h-4 w-4" />
            {isEdit ? 'Update Role' : 'Create Role'}
          </Button>
        </div>
      </form>
    </div>
  );
}
