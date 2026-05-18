import {
  CheckCircle,
  Edit,
  Eye,
  Plus,
  Search,
  Settings,
  Users,
  XCircle,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { EmptyState } from '@/components/common/EmptyState';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
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
import { formatCurrency } from '@/lib/utils';
import { approvalsApi, type ApprovalWorkflowResponse } from '@/services/api';
import { useActiveOrganizationId } from '@/stores/organizationStore';

import { logger } from "@/lib/logger";
const modules = [
  { value: 'LENDING', label: 'Lending' },
  { value: 'ACCOUNTING', label: 'Accounting' },
  { value: 'PROCUREMENT', label: 'Procurement' },
  { value: 'AP_AR', label: 'AP/AR' },
  { value: 'HR', label: 'Human Resources' },
  { value: 'TREASURY', label: 'Treasury' },
  { value: 'FIXED_ASSETS', label: 'Fixed Assets' },
  { value: 'PAYROLL', label: 'Payroll' },
];

const getWorkflowModule = (workflowType: string) => {
  if (workflowType.startsWith('FIN_')) return 'ACCOUNTING';
  if (workflowType === 'PAYMENT_RELEASE') return 'AP_AR';
  if (workflowType.startsWith('LOAN_')) return 'LENDING';
  if (workflowType.startsWith('FA_')) return 'FIXED_ASSETS';
  if (workflowType === 'PAYROLL_POSTING') return 'PAYROLL';
  return 'ACCOUNTING';
};

export default function ApprovalMatrixList() {
  const navigate = useNavigate();
  const organizationId = useActiveOrganizationId();
  const [searchTerm, setSearchTerm] = useState('');
  const [moduleFilter, setModuleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [approvalMatrices, setApprovalMatrices] = useState<ApprovalWorkflowResponse[]>([]);

  useEffect(() => {
    const loadRules = async () => {
      if (!organizationId) return;
      try {
        const response = await approvalsApi.listWorkflows({
          organization_id: organizationId,
          limit: 100,
        });
        setApprovalMatrices(response.data.items || []);
      } catch (error) {
        logger.error('Failed to load approval matrix rules:', error);
        setApprovalMatrices([]);
      }
    };
    loadRules();
  }, [organizationId]);

  const filteredMatrices = useMemo(
    () =>
      approvalMatrices.filter((matrix) => {
        const search = searchTerm.toLowerCase();
        const matchesSearch =
          matrix.workflowName.toLowerCase().includes(search) ||
          matrix.workflowType.toLowerCase().includes(search);
        const matchesModule =
          moduleFilter === 'all' || getWorkflowModule(matrix.workflowType) === moduleFilter;
        const matchesStatus =
          statusFilter === 'all' ||
          (statusFilter === 'active' && matrix.isActive) ||
          (statusFilter === 'inactive' && !matrix.isActive);
        return matchesSearch && matchesModule && matchesStatus;
      }),
    [approvalMatrices, moduleFilter, searchTerm, statusFilter],
  );

  const activeRules = approvalMatrices.filter((matrix) => matrix.isActive).length;
  const modulesCovered = new Set(approvalMatrices.map((matrix) => getWorkflowModule(matrix.workflowType))).size;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Approval Matrix"
        subtitle="Configure approval workflows and hierarchies"
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => navigate('/admin/accounting/pending-approvals')}
            >
              <Users className="mr-2 h-4 w-4" />
              Pending Approvals
            </Button>
            <Button onClick={() => navigate('/admin/accounting/approval-matrix/new')}>
              <Plus className="mr-2 h-4 w-4" />
              Add Rule
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Rules</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{approvalMatrices.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Active Rules
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{activeRules}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Modules Covered
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{modulesCovered}</div>
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:bg-muted/50"
          onClick={() => navigate('/admin/accounting/pending-approvals')}
        >
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Pending Approvals
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-500">View</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4">
            <div className="relative min-w-[200px] flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search by name or role..."
                className="pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Select value={moduleFilter} onValueChange={setModuleFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Module" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Modules</SelectItem>
                {modules.map((mod) => (
                  <SelectItem key={mod.value} value={mod.value}>
                    {mod.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Approval Matrix Table */}
      <Card>
        <CardHeader>
          <CardTitle>Approval Rules</CardTitle>
          <CardDescription>{filteredMatrices.length} rules configured</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Rule Name</TableHead>
                <TableHead>Module</TableHead>
                <TableHead>Transaction Type</TableHead>
                <TableHead className="text-right">Amount Range</TableHead>
                <TableHead>Approver</TableHead>
                <TableHead className="text-center">Level</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredMatrices.map((matrix) => {
                const firstLevel = matrix.levels[0];
                return (
                  <TableRow key={matrix.id}>
                    <TableCell className="font-medium">{matrix.workflowName}</TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {getWorkflowModule(matrix.workflowType).replace(/_/g, '/')}
                      </Badge>
                    </TableCell>
                    <TableCell>{matrix.workflowType.replace(/_/g, ' ')}</TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(Number(matrix.thresholdAmount))} and above
                    </TableCell>
                    <TableCell>{firstLevel?.levelName || '-'}</TableCell>
                    <TableCell className="text-center">
                      <Badge variant="secondary">{matrix.approvalLevels}</Badge>
                    </TableCell>
                    <TableCell>
                      {matrix.isActive ? (
                        <Badge variant="default" className="bg-green-600">
                          <CheckCircle className="mr-1 h-3 w-3" />
                          Active
                        </Badge>
                      ) : (
                        <Badge variant="secondary">
                          <XCircle className="mr-1 h-3 w-3" />
                          Inactive
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate(`/admin/accounting/approval-matrix/${matrix.id}`)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            navigate(`/admin/accounting/approval-matrix/${matrix.id}/edit`)
                          }
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
          {filteredMatrices.length === 0 && (
            <EmptyState
              className="mt-4"
              icon={Settings}
              title="No approval matrix rules configured"
              subtitle="Configure voucher, payment, and other finance approvals using Add Rule."
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
