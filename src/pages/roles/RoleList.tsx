import { Edit, MoreHorizontal, Plus, Shield, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { rolesApi } from '@/services/api';
import type { RoleListItem } from '@/types';

import { logger } from "@/lib/logger";
export function RoleList() {
  const navigate = useNavigate();
  const [roles, setRoles] = useState<RoleListItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchRoles = async () => {
    try {
      setLoading(true);
      const response = await rolesApi.list();
      setRoles(response.data);
    } catch (error) {
      logger.error('Failed to fetch roles:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoles();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this role?')) return;
    try {
      await rolesApi.delete(id);
      fetchRoles();
    } catch (error) {
      logger.error('Failed to delete role:', error);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Roles"
        subtitle="Manage roles and their permissions"
        actions={
          <Button onClick={() => navigate('/admin/roles/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Role
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>All Roles</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-sm text-slate-500">Loading...</p>
            </div>
          ) : roles.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <p className="text-sm text-slate-500">No roles found</p>
              <Button variant="link" onClick={() => navigate('/admin/roles/new')}>
                Create your first role
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Code</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Permissions</TableHead>
                  <TableHead>Users</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead className="w-[70px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {roles.map((role) => (
                  <TableRow key={role.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        {role.is_system_role && (
                          <Shield className="h-4 w-4 text-blue-600" />
                        )}
                        {role.code}
                      </div>
                    </TableCell>
                    <TableCell>{role.name}</TableCell>
                    <TableCell className="max-w-[200px] truncate">
                      {role.description || '-'}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{role.permission_count} permissions</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{role.user_count} users</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        className={
                          role.is_system_role
                            ? 'bg-blue-50 text-blue-700 hover:bg-blue-50'
                            : 'bg-slate-100 text-slate-600 hover:bg-slate-100'
                        }
                      >
                        {role.is_system_role ? 'System' : 'Custom'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => navigate(`/admin/roles/${role.id}/edit`)}>
                            <Edit className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                          {!role.is_system_role && (
                            <DropdownMenuItem
                              onClick={() => handleDelete(role.id)}
                              className="text-red-600"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
