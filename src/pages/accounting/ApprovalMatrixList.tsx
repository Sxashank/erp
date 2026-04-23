import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  Search,
  Edit,
  Eye,
  Trash2,
  Settings,
  CheckCircle,
  XCircle,
  Users,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { formatCurrency } from '@/lib/utils';

// Mock data
const approvalMatrixSummary = {
  total_rules: 24,
  active_rules: 20,
  modules_covered: 8,
  pending_approvals: 45,
};

const approvalMatrices = [
  {
    id: '1',
    name: 'Loan Disbursement - Level 1',
    module: 'LENDING',
    transaction_type: 'DISBURSEMENT',
    min_amount: 0,
    max_amount: 5000000,
    approver_role: 'Branch Manager',
    approver_count: 1,
    sequence: 1,
    is_active: true,
    created_date: '2024-01-15',
  },
  {
    id: '2',
    name: 'Loan Disbursement - Level 2',
    module: 'LENDING',
    transaction_type: 'DISBURSEMENT',
    min_amount: 5000001,
    max_amount: 25000000,
    approver_role: 'Regional Manager',
    approver_count: 1,
    sequence: 2,
    is_active: true,
    created_date: '2024-01-15',
  },
  {
    id: '3',
    name: 'Loan Disbursement - Level 3',
    module: 'LENDING',
    transaction_type: 'DISBURSEMENT',
    min_amount: 25000001,
    max_amount: null,
    approver_role: 'Credit Committee',
    approver_count: 3,
    sequence: 3,
    is_active: true,
    created_date: '2024-01-15',
  },
  {
    id: '4',
    name: 'Purchase Order - Level 1',
    module: 'PROCUREMENT',
    transaction_type: 'PURCHASE_ORDER',
    min_amount: 0,
    max_amount: 100000,
    approver_role: 'Department Head',
    approver_count: 1,
    sequence: 1,
    is_active: true,
    created_date: '2024-02-10',
  },
  {
    id: '5',
    name: 'Vendor Payment - Standard',
    module: 'AP_AR',
    transaction_type: 'VENDOR_PAYMENT',
    min_amount: 0,
    max_amount: 500000,
    approver_role: 'Finance Manager',
    approver_count: 1,
    sequence: 1,
    is_active: true,
    created_date: '2024-02-20',
  },
  {
    id: '6',
    name: 'GL Posting - Journal Entry',
    module: 'ACCOUNTING',
    transaction_type: 'JOURNAL_VOUCHER',
    min_amount: 0,
    max_amount: null,
    approver_role: 'Chief Accountant',
    approver_count: 1,
    sequence: 1,
    is_active: true,
    created_date: '2024-03-01',
  },
  {
    id: '7',
    name: 'NPA Write-off',
    module: 'LENDING',
    transaction_type: 'NPA_WRITEOFF',
    min_amount: 0,
    max_amount: null,
    approver_role: 'Board Committee',
    approver_count: 5,
    sequence: 1,
    is_active: false,
    created_date: '2024-03-15',
  },
];

const modules = [
  { value: 'LENDING', label: 'Lending' },
  { value: 'ACCOUNTING', label: 'Accounting' },
  { value: 'PROCUREMENT', label: 'Procurement' },
  { value: 'AP_AR', label: 'AP/AR' },
  { value: 'HR', label: 'Human Resources' },
  { value: 'TREASURY', label: 'Treasury' },
];

export default function ApprovalMatrixList() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [moduleFilter, setModuleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  const filteredMatrices = approvalMatrices.filter((m) => {
    const matchesSearch =
      m.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.approver_role.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesModule = moduleFilter === 'all' || m.module === moduleFilter;
    const matchesStatus =
      statusFilter === 'all' ||
      (statusFilter === 'active' && m.is_active) ||
      (statusFilter === 'inactive' && !m.is_active);
    return matchesSearch && matchesModule && matchesStatus;
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Approval Matrix"
        subtitle="Configure approval workflows and hierarchies"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigate('/admin/accounting/pending-approvals')}>
              <Users className="h-4 w-4 mr-2" />
              Pending ({approvalMatrixSummary.pending_approvals})
            </Button>
            <Button onClick={() => navigate('/admin/accounting/approval-matrix/create')}>
              <Plus className="h-4 w-4 mr-2" />
              Add Rule
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Rules
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{approvalMatrixSummary.total_rules}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Active Rules</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {approvalMatrixSummary.active_rules}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Modules Covered
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{approvalMatrixSummary.modules_covered}</div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:bg-muted/50" onClick={() => navigate('/admin/accounting/pending-approvals')}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Pending Approvals
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-500">
              {approvalMatrixSummary.pending_approvals}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4 flex-wrap">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
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
              {filteredMatrices.map((matrix) => (
                <TableRow key={matrix.id}>
                  <TableCell className="font-medium">{matrix.name}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{matrix.module.replace(/_/g, '/')}</Badge>
                  </TableCell>
                  <TableCell>{matrix.transaction_type.replace(/_/g, ' ')}</TableCell>
                  <TableCell className="text-right">
                    <div className="text-sm">
                      {formatCurrency(matrix.min_amount)} -{' '}
                      {matrix.max_amount ? formatCurrency(matrix.max_amount) : 'Unlimited'}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="font-medium">{matrix.approver_role}</div>
                        {matrix.approver_count > 1 && (
                          <div className="text-xs text-muted-foreground">
                            {matrix.approver_count} approvers required
                          </div>
                        )}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge variant="secondary">{matrix.sequence}</Badge>
                  </TableCell>
                  <TableCell>
                    {matrix.is_active ? (
                      <Badge variant="default" className="bg-green-600">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Active
                      </Badge>
                    ) : (
                      <Badge variant="secondary">
                        <XCircle className="h-3 w-3 mr-1" />
                        Inactive
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          ...
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => navigate(`/admin/accounting/approval-matrix/${matrix.id}`)}
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() =>
                            navigate(`/admin/accounting/approval-matrix/${matrix.id}/edit`)
                          }
                        >
                          <Edit className="h-4 w-4 mr-2" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem className="text-red-600">
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
