import {
  ChevronDown,
  ChevronRight,
  Edit,
  FolderTree,
  MoreHorizontal,
  Plus,
  Trash2,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
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
import { accountGroupsApi, organizationsApi } from '@/services/api';
import type { AccountGroupTreeNode, Organization, PaginatedResponse } from '@/types';

import { logger } from "@/lib/logger";
interface TreeRowProps {
  node: AccountGroupTreeNode;
  level: number;
  expandedNodes: Set<string>;
  toggleNode: (id: string) => void;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
}

function TreeRow({ node, level, expandedNodes, toggleNode, onEdit, onDelete }: TreeRowProps) {
  const isExpanded = expandedNodes.has(node.id);
  const hasChildren = node.children && node.children.length > 0;

  const getNatureBadgeClass = (nature: string) => {
    switch (nature) {
      case 'ASSETS':
        return 'bg-blue-50 text-blue-700';
      case 'LIABILITIES':
        return 'bg-purple-50 text-purple-700';
      case 'INCOME':
        return 'bg-emerald-50 text-emerald-700';
      case 'EXPENSES':
        return 'bg-orange-50 text-orange-700';
      case 'EQUITY':
        return 'bg-slate-100 text-slate-700';
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
                className="mr-2 rounded p-1 hover:bg-slate-100"
              >
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </button>
            ) : (
              <span className="mr-2 w-6" />
            )}
            <span className="font-medium">{node.code}</span>
          </div>
        </TableCell>
        <TableCell>{node.name}</TableCell>
        <TableCell>
          <Badge
            className={`${getNatureBadgeClass(node.nature)} hover:${getNatureBadgeClass(node.nature)}`}
          >
            {node.nature}
          </Badge>
        </TableCell>
        <TableCell>{node.level}</TableCell>
        <TableCell>{node.sequence}</TableCell>
        <TableCell>
          {node.is_system ? (
            <Badge variant="outline">System</Badge>
          ) : (
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
                <DropdownMenuItem onClick={() => onDelete(node.id)} className="text-red-600">
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </TableCell>
      </TableRow>
      {isExpanded &&
        hasChildren &&
        node.children.map((child) => (
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

export function AccountGroupList() {
  const navigate = useNavigate();
  const [treeData, setTreeData] = useState<AccountGroupTreeNode[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());

  const fetchOrganizations = useCallback(async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      const data: PaginatedResponse<Organization> = response.data;
      setOrganizations(data.items);
      if (data.items.length > 0) {
        setSelectedOrgId(data.items[0].id);
      }
    } catch (error) {
      logger.error('Failed to fetch organizations:', error);
    }
  }, []);

  const fetchAccountGroups = useCallback(async () => {
    if (!selectedOrgId) return;
    try {
      setLoading(true);
      const response = await accountGroupsApi.getTree(selectedOrgId);
      setTreeData(response.data);
      // Expand root level by default
      const rootIds = new Set<string>(response.data.map((node: AccountGroupTreeNode) => node.id));
      setExpandedNodes(rootIds);
    } catch (error) {
      logger.error('Failed to fetch account groups:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedOrgId]);

  useEffect(() => {
    fetchOrganizations();
  }, [fetchOrganizations]);

  useEffect(() => {
    if (selectedOrgId) {
      fetchAccountGroups();
    }
  }, [fetchAccountGroups, selectedOrgId]);

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
    const collectIds = (nodes: AccountGroupTreeNode[]) => {
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
    if (!confirm('Are you sure you want to delete this account group?')) return;
    try {
      await accountGroupsApi.delete(id);
      fetchAccountGroups();
    } catch (error) {
      logger.error('Failed to delete account group:', error);
    }
  };

  const handleEdit = (id: string) => {
    navigate(`/admin/finance/account-groups/${id}/edit`);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Account Groups"
        subtitle="Manage chart of accounts hierarchy"
        breadcrumbs={[{ label: 'Finance', to: '/admin/finance' }, { label: 'Account Groups' }]}
        actions={
          <Button onClick={() => navigate('/admin/finance/account-groups/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Account Group
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Chart of Accounts</CardTitle>
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
              <p className="text-sm text-slate-500">No account groups found</p>
              <Button variant="link" onClick={() => navigate('/admin/finance/account-groups/new')}>
                Create your first account group
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Code</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Nature</TableHead>
                  <TableHead>Level</TableHead>
                  <TableHead>Sequence</TableHead>
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
