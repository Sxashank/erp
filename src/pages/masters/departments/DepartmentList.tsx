import {
  ChevronDown,
  ChevronRight,
  Edit,
  FolderTree,
  GitBranch,
  List,
  MoreHorizontal,
  Plus,
  Trash2,
} from 'lucide-react';
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
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { departmentsApi, organizationsApi } from '@/services/api';
import type { Department, DepartmentTreeNode, Organization, PaginatedResponse } from '@/types';

import { logger } from "@/lib/logger";
// Tree node component
function TreeNode({
  node,
  level = 0,
  onEdit,
  onDelete,
}: {
  node: DepartmentTreeNode;
  level?: number;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(true);
  const hasChildren = node.children && node.children.length > 0;

  return (
    <div className="select-none">
      <div
        className={`flex items-center gap-2 rounded-lg border p-3 mb-2 ${
          node.status === 'ACTIVE' ? 'bg-white' : 'bg-slate-50 opacity-60'
        }`}
        style={{ marginLeft: `${level * 24}px` }}
      >
        {/* Expand/Collapse button */}
        <button
          onClick={() => setExpanded(!expanded)}
          className={`p-1 rounded hover:bg-slate-100 ${!hasChildren ? 'invisible' : ''}`}
        >
          {expanded ? (
            <ChevronDown className="h-4 w-4 text-slate-500" />
          ) : (
            <ChevronRight className="h-4 w-4 text-slate-500" />
          )}
        </button>

        {/* Icon */}
        <div className="p-2 rounded-lg bg-indigo-50 text-indigo-700">
          <FolderTree className="h-4 w-4" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-slate-900">{node.name}</span>
            <span className="text-xs text-slate-500">({node.code})</span>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-slate-400">Level {node.level}</span>
            {node.cost_center_code && (
              <Badge variant="outline" className="text-xs">
                CC: {node.cost_center_code}
              </Badge>
            )}
          </div>
        </div>

        {/* Status */}
        <Badge
          className={
            node.status === 'ACTIVE'
              ? 'bg-emerald-50 text-emerald-700'
              : 'bg-slate-100 text-slate-600'
          }
        >
          {node.status}
        </Badge>

        {/* Actions */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onEdit(node.id)}>
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onDelete(node.id)} className="text-red-600">
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Children */}
      {expanded && hasChildren && (
        <div>
          {node.children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function DepartmentList() {
  const navigate = useNavigate();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [treeData, setTreeData] = useState<DepartmentTreeNode[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'table' | 'tree'>('table');
  const [pagination, setPagination] = useState({ page: 1, total: 0, totalPages: 0 });

  // Fetch organizations
  useEffect(() => {
    const fetchOrganizations = async () => {
      try {
        const response = await organizationsApi.list({ pageSize: 100 });
        const orgs = response.data.items || response.data;
        setOrganizations(Array.isArray(orgs) ? orgs : []);
        if (orgs.length > 0 && !selectedOrgId) {
          setSelectedOrgId(orgs[0].id);
        }
      } catch (error) {
        logger.error('Failed to fetch organizations:', error);
      }
    };
    fetchOrganizations();
  }, []);

  // Fetch departments (table view)
  const fetchDepartments = async (page = 1) => {
    try {
      setLoading(true);
      const params: Record<string, unknown> = { page, page_size: 10, include_inactive: true };
      if (selectedOrgId) {
        params.organization_id = selectedOrgId;
      }
      const response = await departmentsApi.list(params);
      const data: PaginatedResponse<Department> = response.data;
      setDepartments(data.items);
      setPagination({ page: data.page, total: data.total, totalPages: data.total_pages });
    } catch (error) {
      logger.error('Failed to fetch departments:', error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch tree data
  const fetchTree = async () => {
    if (!selectedOrgId) {
      setTreeData([]);
      return;
    }
    try {
      setLoading(true);
      const response = await departmentsApi.getTree();
      setTreeData(response.data);
    } catch (error) {
      logger.error('Failed to fetch department tree:', error);
      setTreeData([]);
    } finally {
      setLoading(false);
    }
  };

  // Effect to fetch data when view or org changes
  useEffect(() => {
    if (viewMode === 'table') {
      fetchDepartments();
    } else {
      fetchTree();
    }
  }, [viewMode, selectedOrgId]);

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this department?')) return;
    try {
      await departmentsApi.delete(id);
      if (viewMode === 'table') {
        fetchDepartments(pagination.page);
      } else {
        fetchTree();
      }
    } catch (error) {
      logger.error('Failed to delete department:', error);
    }
  };

  const handleEdit = (id: string) => {
    navigate(`/admin/departments/${id}/edit`);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Departments"
        subtitle="Manage organizational departments"
        actions={
          <Button onClick={() => navigate('/admin/departments/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Department
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>All Departments</CardTitle>
            <div className="flex items-center gap-4">
              {/* Organization filter */}
              <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Select Organization" />
                </SelectTrigger>
                <SelectContent>
                  {organizations.map((org) => (
                    <SelectItem key={org.id} value={org.id}>
                      {org.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* View mode toggle */}
              <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as 'table' | 'tree')}>
                <TabsList>
                  <TabsTrigger value="table" className="gap-2">
                    <List className="h-4 w-4" />
                    Table
                  </TabsTrigger>
                  <TabsTrigger value="tree" className="gap-2">
                    <GitBranch className="h-4 w-4" />
                    Tree
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-sm text-slate-500">Loading...</p>
            </div>
          ) : viewMode === 'tree' ? (
            // Tree View
            !selectedOrgId ? (
              <div className="flex flex-col items-center justify-center py-8">
                <p className="text-sm text-slate-500">Please select an organization to view the hierarchy</p>
              </div>
            ) : treeData.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8">
                <p className="text-sm text-slate-500">No departments found for this organization</p>
                <Button variant="link" onClick={() => navigate('/admin/departments/new')}>
                  Create your first department
                </Button>
              </div>
            ) : (
              <div className="space-y-2">
                {treeData.map((node) => (
                  <TreeNode
                    key={node.id}
                    node={node}
                    onEdit={handleEdit}
                    onDelete={handleDelete}
                  />
                ))}
              </div>
            )
          ) : (
            // Table View
            departments.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8">
                <p className="text-sm text-slate-500">No departments found</p>
                <Button variant="link" onClick={() => navigate('/admin/departments/new')}>
                  Create your first department
                </Button>
              </div>
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Code</TableHead>
                      <TableHead>Name</TableHead>
                      <TableHead>Organization</TableHead>
                      <TableHead>Parent Department</TableHead>
                      <TableHead>Head</TableHead>
                      <TableHead>Cost Center</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="w-[70px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {departments.map((dept) => (
                      <TableRow key={dept.id}>
                        <TableCell className="font-medium">{dept.code}</TableCell>
                        <TableCell>{dept.name}</TableCell>
                        <TableCell>{dept.organization_name || '-'}</TableCell>
                        <TableCell>{dept.parent_dept_name || '-'}</TableCell>
                        <TableCell>{dept.head_name || '-'}</TableCell>
                        <TableCell>{dept.cost_center_code || '-'}</TableCell>
                        <TableCell>
                          <Badge
                            className={
                              dept.status === 'ACTIVE'
                                ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-50'
                                : 'bg-slate-100 text-slate-600 hover:bg-slate-100'
                            }
                          >
                            {dept.status}
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
                              <DropdownMenuItem onClick={() => navigate(`/admin/departments/${dept.id}/edit`)}>
                                <Edit className="mr-2 h-4 w-4" />
                                Edit
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() => handleDelete(dept.id)}
                                className="text-red-600"
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>

                {pagination.totalPages > 1 && (
                  <div className="mt-4 flex items-center justify-between">
                    <p className="text-sm text-slate-500">
                      Showing {departments.length} of {pagination.total} departments
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={pagination.page <= 1}
                        onClick={() => fetchDepartments(pagination.page - 1)}
                      >
                        Previous
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={pagination.page >= pagination.totalPages}
                        onClick={() => fetchDepartments(pagination.page + 1)}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )
          )}
        </CardContent>
      </Card>
    </div>
  );
}
