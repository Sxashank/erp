import {
  Activity,
  CheckCircle,
  Edit,
  Eye,
  GitBranch,
  MoreHorizontal,
  Plus,
  Search,
  Settings,
  Trash2,
} from 'lucide-react';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { EmptyState, ErrorState, PageHeader, SkeletonTable } from '@/components/common';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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
import { useOrganization } from '@/hooks/useOrganization';
import {
  useDeleteWorkflowDefinition,
  useWorkflowDefinitions,
} from '@/hooks/workflow/useWorkflowDefinitions';
import { showErrorToast } from '@/lib/errorToast';
import type {
  WorkflowDefinitionResponse,
  WorkflowEntityType,
} from '@/services/workflow/workflowApi';

const ENTITY_TYPES: { value: WorkflowEntityType | 'all'; label: string }[] = [
  { value: 'all', label: 'All Entity Types' },
  { value: 'VOUCHER', label: 'Voucher' },
  { value: 'PURCHASE_BILL', label: 'Purchase Bill' },
  { value: 'SALES_INVOICE', label: 'Sales Invoice' },
  { value: 'PAYMENT', label: 'Payment' },
  { value: 'JOURNAL_ENTRY', label: 'Journal Entry' },
  { value: 'LOAN_APPLICATION', label: 'Loan Application' },
  { value: 'LOAN_SANCTION', label: 'Loan Sanction' },
  { value: 'LOAN_RATING', label: 'Loan Rating' },
];

function getEntityBadge(entityType: WorkflowEntityType): JSX.Element {
  const colors: Record<string, string> = {
    LOAN_APPLICATION: 'bg-blue-50 text-blue-700',
    LOAN_SANCTION: 'bg-indigo-50 text-indigo-700',
    LOAN_RATING: 'bg-violet-50 text-violet-700',
    VOUCHER: 'bg-emerald-50 text-emerald-700',
    PURCHASE_BILL: 'bg-orange-50 text-orange-700',
    SALES_INVOICE: 'bg-cyan-50 text-cyan-700',
    PAYMENT: 'bg-amber-50 text-amber-700',
    JOURNAL_ENTRY: 'bg-purple-50 text-purple-700',
  };
  const cls = colors[entityType] ?? 'bg-slate-50 text-slate-700';
  return <Badge className={`${cls} hover:${cls}`}>{entityType.replace(/_/g, ' ')}</Badge>;
}

export function WorkflowDefinitionList(): JSX.Element {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { activeOrganizationId } = useOrganization();

  const [selectedEntityType, setSelectedEntityType] = useState<WorkflowEntityType | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const filters = activeOrganizationId
    ? {
        organization_id: activeOrganizationId,
        ...(selectedEntityType !== 'all' && { entity_type: selectedEntityType }),
        page: 1,
        page_size: 100,
      }
    : undefined;

  const definitionsQuery = useWorkflowDefinitions(filters);
  const deleteMutation = useDeleteWorkflowDefinition();

  const items = definitionsQuery.data?.items ?? [];
  const filteredItems = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return items;
    return items.filter(
      (d) =>
        d.code.toLowerCase().includes(q) ||
        d.name.toLowerCase().includes(q) ||
        (d.description ?? '').toLowerCase().includes(q),
    );
  }, [items, searchQuery]);

  const activeWorkflows = items.filter((w) => w.is_active).length;
  const defaultWorkflows = items.filter((w) => w.is_default).length;
  const totalWorkflows = items.length;

  const handleDelete = (def: WorkflowDefinitionResponse) => {
    deleteMutation.mutate(def.id, {
      onSuccess: () => {
        toast({
          title: 'Workflow deleted',
          description: `${def.code} has been removed.`,
        });
      },
      onError: (err) => showErrorToast(err, toast),
    });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Workflow Definitions"
        subtitle="Configure approval workflows for different processes"
        actions={
          <Button onClick={() => navigate('/admin/workflow/definitions/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Create Workflow
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Workflows</CardTitle>
            <CheckCircle className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600">{activeWorkflows}</div>
            <p className="text-xs text-muted-foreground">Available for use</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Default Workflows</CardTitle>
            <Settings className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{defaultWorkflows}</div>
            <p className="text-xs text-muted-foreground">Auto-triggered defaults</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Workflows</CardTitle>
            <GitBranch className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalWorkflows}</div>
            <p className="text-xs text-muted-foreground">All configurations</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Filtered</CardTitle>
            <Activity className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{filteredItems.length}</div>
            <p className="text-xs text-muted-foreground">Matching criteria</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle>Workflow Configurations</CardTitle>
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search workflows..."
                  className="w-[200px] pl-8"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <Select
                value={selectedEntityType}
                onValueChange={(value) =>
                  setSelectedEntityType(value as WorkflowEntityType | 'all')
                }
              >
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="All Entity Types" />
                </SelectTrigger>
                <SelectContent>
                  {ENTITY_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {!activeOrganizationId ? (
            <EmptyState
              title="Select an organization"
              subtitle="Switch to an organization to view its workflow definitions."
            />
          ) : definitionsQuery.isLoading ? (
            <SkeletonTable rows={6} columns={6} />
          ) : definitionsQuery.isError ? (
            <ErrorState error={definitionsQuery.error} onRetry={() => definitionsQuery.refetch()} />
          ) : filteredItems.length === 0 ? (
            <EmptyState
              title="No workflows found"
              subtitle="Create a workflow definition to begin routing approvals."
              icon={GitBranch}
              action={
                <Button onClick={() => navigate('/admin/workflow/definitions/new')}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create your first workflow
                </Button>
              }
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Workflow</TableHead>
                  <TableHead>Entity Type</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Default</TableHead>
                  <TableHead>Version</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[70px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredItems.map((workflow) => (
                  <TableRow key={workflow.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{workflow.code}</p>
                        <p className="text-sm text-muted-foreground">{workflow.name}</p>
                      </div>
                    </TableCell>
                    <TableCell>{getEntityBadge(workflow.entity_type)}</TableCell>
                    <TableCell className="tabular-nums">{workflow.priority}</TableCell>
                    <TableCell>
                      {workflow.is_default ? (
                        <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-50">Default</Badge>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>v{workflow.version}</TableCell>
                    <TableCell>
                      {workflow.is_active ? (
                        <Badge className="bg-emerald-50 text-emerald-700 hover:bg-emerald-50">
                          Active
                        </Badge>
                      ) : (
                        <Badge variant="outline">Inactive</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={() => navigate(`/admin/workflow/definitions/${workflow.id}`)}
                          >
                            <Eye className="mr-2 h-4 w-4" />
                            View
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() =>
                              navigate(`/admin/workflow/definitions/${workflow.id}/edit`)
                            }
                          >
                            <Edit className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() =>
                              navigate(`/admin/workflow/instances?definition_id=${workflow.id}`)
                            }
                          >
                            <Activity className="mr-2 h-4 w-4" />
                            View Instances
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            className="text-red-600"
                            disabled={deleteMutation.isPending}
                            onClick={() => handleDelete(workflow)}
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
          )}
        </CardContent>
      </Card>
    </div>
  );
}
