import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2,
  ChevronDown,
  ChevronRight,
  Edit,
  GitBranch,
  List,
  MoreHorizontal,
  Plus,
  Trash2,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/common/PageHeader';
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
import { unitsApi, organizationsApi } from '@/services/api';
import type { Unit, UnitTreeNode, Organization, PaginatedResponse } from '@/types';

// Tree node component
function TreeNode({
  node,
  level = 0,
  onEdit,
  onDelete,
}: {
  node: UnitTreeNode;
  level?: number;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(true);
  const hasChildren = node.children && node.children.length > 0;

  const getUnitTypeColor = (type: string) => {
    switch (type) {
      case 'HEAD_OFFICE':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'REGIONAL_OFFICE':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'BRANCH':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'PROJECT_OFFICE':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

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
        <div className={`p-2 rounded-lg ${getUnitTypeColor(node.unit_type)}`}>
          <Building2 className="h-4 w-4" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-slate-900">{node.name}</span>
            <span className="text-xs text-slate-500">({node.code})</span>
            {node.is_head_office && (
              <Badge className="bg-blue-100 text-blue-700 text-xs">HQ</Badge>
            )}
          </div>
          <div className="flex items-center gap-2 mt-1">
            <Badge variant="outline" className="text-xs">
              {node.unit_type.replace(/_/g, ' ')}
            </Badge>
            <span className="text-xs text-slate-400">Level {node.level}</span>
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

export function UnitList() {
  const navigate = useNavigate();
  const [units, setUnits] = useState<Unit[]>([]);
  const [treeData, setTreeData] = useState<UnitTreeNode[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'table' | 'tree'>('table');
  const [pagination, setPagination] = useState({ page: 1, total: 0, totalPages: 0 });

  // Fetch organizations
  useEffect(() => {
    const fetchOrganizations = async () => {
      try {
        const response = await organizationsApi.list({ page_size: 100 });
        const orgs = response.data.items || response.data;
        setOrganizations(Array.isArray(orgs) ? orgs : []);
        if (orgs.length > 0 && !selectedOrgId) {
          setSelectedOrgId(orgs[0].id);
        }
      } catch (error) {
        console.error('Failed to fetch organizations:', error);
      }
    };
    fetchOrganizations();
  }, []);

  // Fetch units (table view)
  const fetchUnits = async (page = 1) => {
    try {
      setLoading(true);
      const params: any = { page, page_size: 10, include_inactive: true };
      if (selectedOrgId) {
        params.organization_id = selectedOrgId;
      }
      const response = await unitsApi.list(params);
      const data: PaginatedResponse<Unit> = response.data;
      setUnits(data.items);
      setPagination({ page: data.page, total: data.total, totalPages: data.total_pages });
    } catch (error) {
      console.error('Failed to fetch units:', error);
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
      const response = await unitsApi.getTree(selectedOrgId);
      setTreeData(response.data);
    } catch (error) {
      console.error('Failed to fetch unit tree:', error);
      setTreeData([]);
    } finally {
      setLoading(false);
    }
  };

  // Effect to fetch data when view or org changes
  useEffect(() => {
    if (viewMode === 'table') {
      fetchUnits();
    } else {
      fetchTree();
    }
  }, [viewMode, selectedOrgId]);

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this unit?')) return;
    try {
      await unitsApi.delete(id);
      if (viewMode === 'table') {
        fetchUnits(pagination.page);
      } else {
        fetchTree();
      }
    } catch (error) {
      console.error('Failed to delete unit:', error);
    }
  };

  const handleEdit = (id: string) => {
    navigate(`/admin/units/${id}/edit`);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Units"
        subtitle="Manage organizational units and branches"
        actions={
          <Button onClick={() => navigate('/admin/units/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Unit
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>All Units</CardTitle>
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
                <p className="text-sm text-slate-500">No units found for this organization</p>
                <Button variant="link" onClick={() => navigate('/admin/units/new')}>
                  Create your first unit
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
            units.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8">
                <p className="text-sm text-slate-500">No units found</p>
                <Button variant="link" onClick={() => navigate('/admin/units/new')}>
                  Create your first unit
                </Button>
              </div>
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Code</TableHead>
                      <TableHead>Name</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Organization</TableHead>
                      <TableHead>Parent Unit</TableHead>
                      <TableHead>City</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="w-[70px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {units.map((unit) => (
                      <TableRow key={unit.id}>
                        <TableCell className="font-medium">{unit.code}</TableCell>
                        <TableCell>{unit.name}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{unit.unit_type.replace(/_/g, ' ')}</Badge>
                        </TableCell>
                        <TableCell>{unit.organization_name || '-'}</TableCell>
                        <TableCell>{unit.parent_unit_name || '-'}</TableCell>
                        <TableCell>{unit.city || '-'}</TableCell>
                        <TableCell>
                          <Badge
                            className={
                              unit.status === 'ACTIVE'
                                ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-50'
                                : 'bg-slate-100 text-slate-600 hover:bg-slate-100'
                            }
                          >
                            {unit.status}
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
                              <DropdownMenuItem onClick={() => navigate(`/admin/units/${unit.id}/edit`)}>
                                <Edit className="mr-2 h-4 w-4" />
                                Edit
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() => handleDelete(unit.id)}
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
                      Showing {units.length} of {pagination.total} units
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={pagination.page <= 1}
                        onClick={() => fetchUnits(pagination.page - 1)}
                      >
                        Previous
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={pagination.page >= pagination.totalPages}
                        onClick={() => fetchUnits(pagination.page + 1)}
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
