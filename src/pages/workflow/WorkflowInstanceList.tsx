import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle,
  Clock,
  Eye,
  Filter,
  GitBranch,
  MoreHorizontal,
  RefreshCw,
  Search,
  XCircle,
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { organizationsApi } from '@/services/api';
import type { Organization, PaginatedResponse } from '@/types';

interface WorkflowInstance {
  id: string;
  instance_number: string;
  workflow_code: string;
  workflow_name: string;
  module: string;
  entity_type: string;
  entity_id: string;
  entity_reference: string;
  entity_title: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'REJECTED' | 'CANCELLED' | 'ESCALATED';
  current_step: number;
  total_steps: number;
  current_step_name: string;
  initiated_by: string;
  initiated_at: string;
  completed_at?: string;
  last_action_at?: string;
  last_action_by?: string;
  pending_with: string[];
  sla_status: 'ON_TRACK' | 'AT_RISK' | 'BREACHED';
  sla_hours_remaining?: number;
}

interface WorkflowHistory {
  id: string;
  step_number: number;
  step_name: string;
  action: 'APPROVED' | 'REJECTED' | 'RETURNED' | 'ESCALATED' | 'DELEGATED' | 'AUTO_APPROVED';
  action_by: string;
  action_at: string;
  remarks?: string;
}

const MODULES = [
  { value: 'all', label: 'All Modules' },
  { value: 'LENDING', label: 'Lending' },
  { value: 'FINANCE', label: 'Finance' },
  { value: 'HRIS', label: 'HRIS' },
  { value: 'PROCUREMENT', label: 'Procurement' },
  { value: 'AP_AR', label: 'AP/AR' },
  { value: 'FIXED_ASSETS', label: 'Fixed Assets' },
];

export function WorkflowInstanceList() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const definitionId = searchParams.get('definition_id');

  const [activeTab, setActiveTab] = useState('active');
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [instances, setInstances] = useState<WorkflowInstance[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [moduleFilter, setModuleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrgId) {
      fetchInstances();
    }
  }, [selectedOrgId, activeTab]);

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

  const fetchInstances = async () => {
    try {
      setLoading(true);
      // Mock data - replace with actual API call
      const mockInstances: WorkflowInstance[] = [
        {
          id: '1',
          instance_number: 'WI-2024-001234',
          workflow_code: 'WF-LOAN-APP',
          workflow_name: 'Loan Application Approval',
          module: 'LENDING',
          entity_type: 'loan_application',
          entity_id: 'LA-2024-001',
          entity_reference: 'LA-2024-001',
          entity_title: 'Term Loan - ₹50L - ABC Corp',
          status: 'IN_PROGRESS',
          current_step: 2,
          total_steps: 4,
          current_step_name: 'Credit Manager Approval',
          initiated_by: 'Sales Executive',
          initiated_at: '2024-11-15T10:30:00',
          last_action_at: '2024-11-16T14:20:00',
          last_action_by: 'Branch Manager',
          pending_with: ['Credit Manager', 'Risk Officer'],
          sla_status: 'ON_TRACK',
          sla_hours_remaining: 18,
        },
        {
          id: '2',
          instance_number: 'WI-2024-001235',
          workflow_code: 'WF-DISB-APP',
          workflow_name: 'Disbursement Approval',
          module: 'LENDING',
          entity_type: 'disbursement',
          entity_id: 'DISB-2024-045',
          entity_reference: 'DISB-2024-045',
          entity_title: 'Disbursement - ₹25L - XYZ Ltd',
          status: 'ESCALATED',
          current_step: 2,
          total_steps: 3,
          current_step_name: 'Finance Head Approval',
          initiated_by: 'Operations',
          initiated_at: '2024-11-14T09:00:00',
          last_action_at: '2024-11-15T16:00:00',
          last_action_by: 'System',
          pending_with: ['Finance Head'],
          sla_status: 'BREACHED',
          sla_hours_remaining: -8,
        },
        {
          id: '3',
          instance_number: 'WI-2024-001236',
          workflow_code: 'WF-LEAVE',
          workflow_name: 'Leave Application Approval',
          module: 'HRIS',
          entity_type: 'leave_application',
          entity_id: 'LV-2024-892',
          entity_reference: 'LV-2024-892',
          entity_title: 'Annual Leave - John Doe - 5 days',
          status: 'PENDING',
          current_step: 1,
          total_steps: 2,
          current_step_name: 'Manager Approval',
          initiated_by: 'John Doe',
          initiated_at: '2024-11-18T08:30:00',
          pending_with: ['Reporting Manager'],
          sla_status: 'AT_RISK',
          sla_hours_remaining: 4,
        },
        {
          id: '4',
          instance_number: 'WI-2024-001230',
          workflow_code: 'WF-VOUCHER',
          workflow_name: 'Journal Voucher Approval',
          module: 'FINANCE',
          entity_type: 'voucher',
          entity_id: 'JV-2024-1056',
          entity_reference: 'JV-2024-1056',
          entity_title: 'Salary Provision - Nov 2024',
          status: 'COMPLETED',
          current_step: 2,
          total_steps: 2,
          current_step_name: 'Completed',
          initiated_by: 'Accountant',
          initiated_at: '2024-11-10T11:00:00',
          completed_at: '2024-11-11T15:30:00',
          last_action_at: '2024-11-11T15:30:00',
          last_action_by: 'Finance Manager',
          pending_with: [],
          sla_status: 'ON_TRACK',
        },
        {
          id: '5',
          instance_number: 'WI-2024-001228',
          workflow_code: 'WF-PO-APP',
          workflow_name: 'Purchase Order Approval',
          module: 'PROCUREMENT',
          entity_type: 'purchase_order',
          entity_id: 'PO-2024-089',
          entity_reference: 'PO-2024-089',
          entity_title: 'Office Supplies - ₹85,000',
          status: 'REJECTED',
          current_step: 2,
          total_steps: 3,
          current_step_name: 'Rejected',
          initiated_by: 'Admin',
          initiated_at: '2024-11-08T14:00:00',
          completed_at: '2024-11-09T10:00:00',
          last_action_at: '2024-11-09T10:00:00',
          last_action_by: 'Finance Head',
          pending_with: [],
          sla_status: 'ON_TRACK',
        },
      ];
      setInstances(mockInstances);
    } catch (error) {
      console.error('Failed to fetch instances:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, { bg: string; icon: React.ReactNode }> = {
      PENDING: { bg: 'bg-slate-50 text-slate-700', icon: <Clock className="mr-1 h-3 w-3" /> },
      IN_PROGRESS: { bg: 'bg-blue-50 text-blue-700', icon: <Activity className="mr-1 h-3 w-3" /> },
      COMPLETED: { bg: 'bg-emerald-50 text-emerald-700', icon: <CheckCircle className="mr-1 h-3 w-3" /> },
      REJECTED: { bg: 'bg-red-50 text-red-700', icon: <XCircle className="mr-1 h-3 w-3" /> },
      CANCELLED: { bg: 'bg-slate-100 text-slate-500', icon: <XCircle className="mr-1 h-3 w-3" /> },
      ESCALATED: { bg: 'bg-orange-50 text-orange-700', icon: <AlertTriangle className="mr-1 h-3 w-3" /> },
    };
    const style = styles[status] || styles.PENDING;
    return (
      <Badge className={`${style.bg} hover:${style.bg} flex items-center`}>
        {style.icon}
        {status.replace('_', ' ')}
      </Badge>
    );
  };

  const getSLABadge = (status: string, hours?: number) => {
    if (status === 'BREACHED') {
      return (
        <Badge className="bg-red-50 text-red-700 hover:bg-red-50">
          SLA Breached ({Math.abs(hours || 0)}h overdue)
        </Badge>
      );
    }
    if (status === 'AT_RISK') {
      return (
        <Badge className="bg-yellow-50 text-yellow-700 hover:bg-yellow-50">
          At Risk ({hours}h left)
        </Badge>
      );
    }
    if (hours !== undefined) {
      return (
        <Badge className="bg-emerald-50 text-emerald-700 hover:bg-emerald-50">
          On Track ({hours}h left)
        </Badge>
      );
    }
    return null;
  };

  const getModuleBadge = (module: string) => {
    const colors: Record<string, string> = {
      LENDING: 'bg-blue-50 text-blue-700',
      FINANCE: 'bg-emerald-50 text-emerald-700',
      HRIS: 'bg-purple-50 text-purple-700',
      PROCUREMENT: 'bg-orange-50 text-orange-700',
      AP_AR: 'bg-cyan-50 text-cyan-700',
      FIXED_ASSETS: 'bg-amber-50 text-amber-700',
    };
    return (
      <Badge className={`${colors[module] || 'bg-slate-50 text-slate-700'} hover:${colors[module]}`}>
        {module.replace('_', '/')}
      </Badge>
    );
  };

  const filteredInstances = instances.filter((instance) => {
    if (activeTab === 'active' && ['COMPLETED', 'REJECTED', 'CANCELLED'].includes(instance.status)) {
      return false;
    }
    if (activeTab === 'completed' && !['COMPLETED', 'REJECTED', 'CANCELLED'].includes(instance.status)) {
      return false;
    }
    if (moduleFilter && moduleFilter !== 'all' && instance.module !== moduleFilter) return false;
    if (statusFilter && instance.status !== statusFilter) return false;
    if (definitionId && instance.workflow_code !== definitionId) return false;
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        instance.instance_number.toLowerCase().includes(query) ||
        instance.entity_reference.toLowerCase().includes(query) ||
        instance.entity_title.toLowerCase().includes(query)
      );
    }
    return true;
  });

  const activeCount = instances.filter(
    (i) => !['COMPLETED', 'REJECTED', 'CANCELLED'].includes(i.status)
  ).length;
  const escalatedCount = instances.filter((i) => i.status === 'ESCALATED').length;
  const breachedCount = instances.filter((i) => i.sla_status === 'BREACHED').length;
  const completedCount = instances.filter((i) => i.status === 'COMPLETED').length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Workflow Instances"
        subtitle="Track all running and completed workflow instances"
        actions={
          <Button variant="outline" onClick={() => fetchInstances()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Instances</CardTitle>
            <Activity className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{activeCount}</div>
            <p className="text-xs text-slate-500">Pending completion</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Escalated</CardTitle>
            <AlertTriangle className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{escalatedCount}</div>
            <p className="text-xs text-slate-500">Need attention</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">SLA Breached</CardTitle>
            <Clock className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{breachedCount}</div>
            <p className="text-xs text-slate-500">Overdue items</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600">{completedCount}</div>
            <p className="text-xs text-slate-500">This month</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="active">Active ({activeCount})</TabsTrigger>
          <TabsTrigger value="completed">Completed</TabsTrigger>
          <TabsTrigger value="all">All Instances</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab}>
          <Card>
            <CardHeader>
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <CardTitle>Workflow Instances</CardTitle>
                <div className="flex flex-wrap items-center gap-2">
                  <div className="relative">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                    <Input
                      placeholder="Search..."
                      className="pl-8 w-[200px]"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                  <Select value={moduleFilter} onValueChange={setModuleFilter}>
                    <SelectTrigger className="w-[140px]">
                      <SelectValue placeholder="Module" />
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
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Organization" />
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
              ) : filteredInstances.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <GitBranch className="mb-4 h-12 w-12 text-slate-300" />
                  <p className="text-sm text-slate-500">No workflow instances found</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Instance</TableHead>
                      <TableHead>Workflow</TableHead>
                      <TableHead>Entity</TableHead>
                      <TableHead>Progress</TableHead>
                      <TableHead>Pending With</TableHead>
                      <TableHead>SLA</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="w-[70px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredInstances.map((instance) => (
                      <TableRow key={instance.id}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{instance.instance_number}</p>
                            <p className="text-xs text-slate-500">{formatDate(instance.initiated_at)}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div>
                            <div className="flex items-center gap-2">
                              {getModuleBadge(instance.module)}
                            </div>
                            <p className="text-sm text-slate-600 mt-1">{instance.workflow_name}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{instance.entity_reference}</p>
                            <p className="text-sm text-slate-500 truncate max-w-[200px]">
                              {instance.entity_title}
                            </p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className="flex-1">
                              <div className="flex items-center justify-between text-sm mb-1">
                                <span>Step {instance.current_step}/{instance.total_steps}</span>
                              </div>
                              <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-blue-500 rounded-full"
                                  style={{
                                    width: `${(instance.current_step / instance.total_steps) * 100}%`,
                                  }}
                                />
                              </div>
                              <p className="text-xs text-slate-500 mt-1">{instance.current_step_name}</p>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          {instance.pending_with.length > 0 ? (
                            <div className="flex flex-wrap gap-1">
                              {instance.pending_with.slice(0, 2).map((approver, i) => (
                                <Badge key={i} variant="outline" className="text-xs">
                                  {approver}
                                </Badge>
                              ))}
                              {instance.pending_with.length > 2 && (
                                <Badge variant="outline" className="text-xs">
                                  +{instance.pending_with.length - 2}
                                </Badge>
                              )}
                            </div>
                          ) : (
                            <span className="text-slate-500">-</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {getSLABadge(instance.sla_status, instance.sla_hours_remaining)}
                        </TableCell>
                        <TableCell>{getStatusBadge(instance.status)}</TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem>
                                <Eye className="mr-2 h-4 w-4" />
                                View Details
                              </DropdownMenuItem>
                              <DropdownMenuItem>
                                <ArrowRight className="mr-2 h-4 w-4" />
                                View Entity
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem>View History</DropdownMenuItem>
                              {instance.status === 'IN_PROGRESS' && (
                                <>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem className="text-red-600">
                                    Cancel Instance
                                  </DropdownMenuItem>
                                </>
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
        </TabsContent>
      </Tabs>
    </div>
  );
}
