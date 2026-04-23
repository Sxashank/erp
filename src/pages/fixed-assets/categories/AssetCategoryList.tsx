import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronDown, ChevronRight, Edit, FolderTree, MoreHorizontal, Plus, Trash2 } from 'lucide-react';

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
import { fixedAssetsApi, organizationsApi } from '@/services/api';
import type { Organization, PaginatedResponse } from '@/types';

interface AssetCategoryTreeNode {
  id: string;
  organization_id: string;
  category_code: string;
  category_name: string;
  description?: string;
  parent_category_id?: string;
  asset_type: string;
  depreciation_method: string;
  useful_life_years?: number;
  depreciation_rate_slm?: number;
  depreciation_rate_wdv?: number;
  is_active: boolean;
  children?: AssetCategoryTreeNode[];
}

interface TreeRowProps {
  node: AssetCategoryTreeNode;
  level: number;
  expandedNodes: Set<string>;
  toggleNode: (id: string) => void;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
}

function TreeRow({ node, level, expandedNodes, toggleNode, onEdit, onDelete }: TreeRowProps) {
  const isExpanded = expandedNodes.has(node.id);
  const hasChildren = node.children && node.children.length > 0;

  const getAssetTypeBadgeClass = (type: string) => {
    switch (type) {
      case 'TANGIBLE':
        return 'bg-blue-50 text-blue-700';
      case 'INTANGIBLE':
        return 'bg-purple-50 text-purple-700';
      case 'RIGHT_OF_USE':
        return 'bg-emerald-50 text-emerald-700';
      default:
        return 'bg-slate-100 text-slate-600';
    }
  };

  const getDepMethodBadgeClass = (method: string) => {
    switch (method) {
      case 'SLM':
        return 'bg-orange-50 text-orange-700';
      case 'WDV':
        return 'bg-cyan-50 text-cyan-700';
      case 'UNIT_OF_PRODUCTION':
        return 'bg-violet-50 text-violet-700';
      case 'NO_DEPRECIATION':
        return 'bg-slate-100 text-slate-600';
      default:
        return 'bg-slate-100 text-slate-600';
    }
  };

  return (
    <>
      <TableRow>
        <TableCell>
          <div className="flex items-center" style={{ paddingLeft: `${level * 20}px` }}>
            {hasChildren ? (
              <button
                onClick={() => toggleNode(node.id)}
                className="mr-2 p-1 hover:bg-slate-100 rounded"
              >
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </button>
            ) : (
              <span className="w-6 mr-2" />
            )}
            <span className="font-medium">{node.category_code}</span>
          </div>
        </TableCell>
        <TableCell>{node.category_name}</TableCell>
        <TableCell>
          <Badge className={`${getAssetTypeBadgeClass(node.asset_type)} hover:${getAssetTypeBadgeClass(node.asset_type)}`}>
            {node.asset_type.replace(/_/g, ' ')}
          </Badge>
        </TableCell>
        <TableCell>
          <Badge className={`${getDepMethodBadgeClass(node.depreciation_method)} hover:${getDepMethodBadgeClass(node.depreciation_method)}`}>
            {node.depreciation_method.replace(/_/g, ' ')}
          </Badge>
        </TableCell>
        <TableCell className="text-right">
          {node.useful_life_years ? `${node.useful_life_years} years` : '-'}
        </TableCell>
        <TableCell className="text-right">
          {node.depreciation_rate_slm ? `${node.depreciation_rate_slm}%` : '-'}
        </TableCell>
        <TableCell className="text-right">
          {node.depreciation_rate_wdv ? `${node.depreciation_rate_wdv}%` : '-'}
        </TableCell>
        <TableCell>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onEdit(node.id)}>
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => onDelete(node.id)}
                className="text-red-600"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </TableCell>
      </TableRow>
      {isExpanded &&
        hasChildren &&
        node.children!.map((child) => (
          <TreeRow
            key={child.id}
            node={child}
            level={level + 1}
            expandedNodes={expandedNodes}
            toggleNode={toggleNode}
            onEdit={onEdit}
            onDelete={onDelete}
          />
        ))}
    </>
  );
}

export function AssetCategoryList() {
  const navigate = useNavigate();
  const [treeData, setTreeData] = useState<AssetCategoryTreeNode[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrgId) {
      fetchCategories();
    }
  }, [selectedOrgId]);

  const fetchOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      const data: PaginatedResponse<Organization> = response.data;
      setOrganizations(data.items);
      if (data.items.length > 0) {
        setSelectedOrgId(data.items[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
    }
  };

  const fetchCategories = async () => {
    if (!selectedOrgId) return;
    try {
      setLoading(true);
      const response = await fixedAssetsApi.getCategoryTree(selectedOrgId);
      setTreeData(response.data);
      // Expand root level by default
      const rootIds = new Set<string>(response.data.map((node: AssetCategoryTreeNode) => node.id));
      setExpandedNodes(rootIds);
    } catch (error) {
      console.error('Failed to fetch asset categories:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleNode = (id: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const expandAll = () => {
    const allIds = new Set<string>();
    const collectIds = (nodes: AssetCategoryTreeNode[]) => {
      nodes.forEach((node) => {
        allIds.add(node.id);
        if (node.children) {
          collectIds(node.children);
        }
      });
    };
    collectIds(treeData);
    setExpandedNodes(allIds);
  };

  const collapseAll = () => {
    setExpandedNodes(new Set());
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this asset category?')) return;
    try {
      await fixedAssetsApi.deleteCategory(id);
      fetchCategories();
    } catch (error) {
      console.error('Failed to delete asset category:', error);
    }
  };

  const handleEdit = (id: string) => {
    navigate(`/admin/fixed-assets/categories/${id}/edit`);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Asset Categories"
        subtitle="Manage fixed asset category hierarchy and depreciation settings"
        actions={
          <Button onClick={() => navigate('/admin/fixed-assets/categories/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Category
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Asset Category Hierarchy</CardTitle>
            <div className="flex items-center gap-4">
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={expandAll}>
                  Expand All
                </Button>
                <Button variant="outline" size="sm" onClick={collapseAll}>
                  Collapse All
                </Button>
              </div>
              <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
                <SelectTrigger className="w-[250px]">
                  <SelectValue placeholder="Select organization" />
                </SelectTrigger>
                <SelectContent>
                  {organizations.map((org) => (
                    <SelectItem key={org.id} value={org.id}>
                      {org.name}
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
              <p className="text-sm text-slate-500">Loading...</p>
            </div>
          ) : treeData.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <FolderTree className="mb-4 h-12 w-12 text-slate-300" />
              <p className="text-sm text-slate-500">No asset categories found</p>
              <Button variant="link" onClick={() => navigate('/admin/fixed-assets/categories/new')}>
                Create your first asset category
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Code</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Asset Type</TableHead>
                  <TableHead>Dep. Method</TableHead>
                  <TableHead className="text-right">Useful Life</TableHead>
                  <TableHead className="text-right">SLM Rate</TableHead>
                  <TableHead className="text-right">WDV Rate</TableHead>
                  <TableHead className="w-[70px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {treeData.map((node) => (
                  <TreeRow
                    key={node.id}
                    node={node}
                    level={0}
                    expandedNodes={expandedNodes}
                    toggleNode={toggleNode}
                    onEdit={handleEdit}
                    onDelete={handleDelete}
                  />
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
