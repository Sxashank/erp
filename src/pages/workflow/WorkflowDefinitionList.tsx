import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
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

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/common/PageHeader';
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
import { organizationsApi } from '@/services/api';
import type { Organization, PaginatedResponse } from '@/types';

interface WorkflowDefinition {
  id: string;
  code: string;
  name: string;
  description?: string;
  module: string;
  entity_type: string;
  version: number;
  is_active: boolean;
  is_published: boolean;
  steps_count: number;
  approvers_count: number;
  active_instances: number;
  created_at: string;
  updated_at: string;
}

const MODULES = [
  { value: 'all', label: 'All Modules' },
  { value: 'LENDING', label: 'Lending' },
  { value: 'FINANCE', label: 'Finance' },
  { value: 'HRIS', label: 'HRIS' },
  { value: 'PROCUREMENT', label: 'Procurement' },
  { value: 'AP_AR', label: 'AP/AR' },
];

export function WorkflowDefinitionList() {
  const navigate = useNavigate();
  const [workflows, setWorkflows] = useState<WorkflowDefinition[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [selectedModule, setSelectedModule] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrgId) {
      fetchWorkflows();
    }
  }, [selectedOrgId, selectedModule]);

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

  const fetchWorkflows = async () => {
    try {
      setLoading(true);
      // Mock data - replace with actual API call
      const mockWorkflows: WorkflowDefinition[] = [
        {
          id: '1',
          code: 'WF-LOAN-APP',
          name: 'Loan Application Approval',
          description: 'Multi-level approval workflow for loan applications',
          module: 'LENDING',
          entity_type: 'loan_application',
          version: 3,
          is_active: true,
          is_published: true,
          steps_count: 4,
          approvers_count: 6,
          active_instances: 12,
          created_at: '2024-01-15',
          updated_at: '2024-11-20',
        },
        {
          id: '2',
          code: 'WF-DISB-APP',
          name: 'Disbursement Approval',
          description: 'Approval workflow for loan disbursements',
          module: 'LENDING',
          entity_type: 'disbursement',
          version: 2,
          is_active: true,
          is_published: true,
          steps_count: 3,
          approvers_count: 4,
          active_instances: 5,
          created_at: '2024-02-10',
          updated_at: '2024-10-15',
        },
        {
          id: '3',
          code: 'WF-VOUCHER',
          name: 'Journal Voucher Approval',
          description: 'Approval workflow for accounting vouchers',
          module: 'FINANCE',
          entity_type: 'voucher',
          version: 1,
          is_active: true,
          is_published: true,
          steps_count: 2,
          approvers_count: 3,
          active_instances: 8,
          created_at: '2024-03-01',
          updated_at: '2024-09-20',
        },
        {
          id: '4',
          code: 'WF-LEAVE',
          name: 'Leave Application Approval',
          description: 'Approval workflow for employee leave requests',
          module: 'HRIS',
          entity_type: 'leave_application',
          version: 2,
          is_active: true,
          is_published: true,
          steps_count: 2,
          approvers_count: 2,
          active_instances: 15,
          created_at: '2024-01-20',
          updated_at: '2024-08-10',
        },
        {
          id: '5',
          code: 'WF-PO-APP',
          name: 'Purchase Order Approval',
          description: 'Multi-level approval for purchase orders',
          module: 'PROCUREMENT',
          entity_type: 'purchase_order',
          version: 1,
          is_active: false,
          is_published: false,
          steps_count: 3,
          approvers_count: 0,
          active_instances: 0,
          created_at: '2024-11-01',
          updated_at: '2024-11-01',
        },
      ];
      setWorkflows(mockWorkflows);
    } catch (error) {
      console.error('Failed to fetch workflows:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  };

  const getModuleBadge = (module: string) => {
    const colors: Record<string, string> = {
      LENDING: 'bg-blue-50 text-blue-700',
      FINANCE: 'bg-emerald-50 text-emerald-700',
      HRIS: 'bg-purple-50 text-purple-700',
      PROCUREMENT: 'bg-orange-50 text-orange-700',
      AP_AR: 'bg-cyan-50 text-cyan-700',
    };
    return (
      <Badge className={`${colors[module] || 'bg-slate-50 text-slate-700'} hover:${colors[module]}`}>
        {module.replace('_', '/')}
      </Badge>
    );
  };

  const activeWorkflows = workflows.filter(w => w.is_active && w.is_published).length;
  const draftWorkflows = workflows.filter(w => !w.is_published).length;
  const totalInstances = workflows.reduce((sum, w) => sum + w.active_instances, 0);

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
            <p className="text-xs text-slate-500">Published and active</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Draft Workflows</CardTitle>
            <Settings className="h-4 w-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{draftWorkflows}</div>
            <p className="text-xs text-slate-500">In configuration</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Instances</CardTitle>
            <Activity className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{totalInstances}</div>
            <p className="text-xs text-slate-500">Pending approvals</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Workflows</CardTitle>
            <GitBranch className="h-4 w-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{workflows.length}</div>
            <p className="text-xs text-slate-500">All configurations</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle>Workflow Configurations</CardTitle>
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search workflows..."
                  className="pl-8 w-[200px]"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <Select value={selectedModule} onValueChange={setSelectedModule}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="All Modules" />
                </SelectTrigger>
                <SelectContent>
                  {MODULES.map((module) => (
                    <SelectItem key={module.value} value={module.value}>
                      {module.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
                <SelectTrigger className="w-[200px]">
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
          ) : workflows.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <GitBranch className="mb-4 h-12 w-12 text-slate-300" />
              <p className="text-sm text-slate-500">No workflows found</p>
              <Button
                variant="link"
                onClick={() => navigate('/admin/workflow/definitions/new')}
              >
                Create your first workflow
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Workflow</TableHead>
                  <TableHead>Module</TableHead>
                  <TableHead>Steps</TableHead>
                  <TableHead>Approvers</TableHead>
                  <TableHead>Active Instances</TableHead>
                  <TableHead>Version</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[70px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {workflows.map((workflow) => (
                  <TableRow key={workflow.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{workflow.code}</p>
                        <p className="text-sm text-slate-500">{workflow.name}</p>
                      </div>
                    </TableCell>
                    <TableCell>{getModuleBadge(workflow.module)}</TableCell>
                    <TableCell>{workflow.steps_count} steps</TableCell>
                    <TableCell>{workflow.approvers_count} users</TableCell>
                    <TableCell>
                      {workflow.active_instances > 0 ? (
                        <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-50">
                          {workflow.active_instances}
                        </Badge>
                      ) : (
                        <span className="text-slate-500">0</span>
                      )}
                    </TableCell>
                    <TableCell>v{workflow.version}</TableCell>
                    <TableCell>
                      {workflow.is_published ? (
                        workflow.is_active ? (
                          <Badge className="bg-emerald-50 text-emerald-700 hover:bg-emerald-50">
                            Active
                          </Badge>
                        ) : (
                          <Badge className="bg-yellow-50 text-yellow-700 hover:bg-yellow-50">
                            Inactive
                          </Badge>
                        )
                      ) : (
                        <Badge variant="outline">Draft</Badge>
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
                            onClick={() => navigate(`/admin/workflow/definitions/${workflow.id}/edit`)}
                          >
                            <Edit className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                          {workflow.active_instances > 0 && (
                            <DropdownMenuItem
                              onClick={() => navigate(`/admin/workflow/instances?definition_id=${workflow.id}`)}
                            >
                              <Activity className="mr-2 h-4 w-4" />
                              View Instances
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuSeparator />
                          {!workflow.is_published && (
                            <DropdownMenuItem className="text-red-600">
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
