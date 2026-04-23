import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Plus,
  Eye,
  MoreHorizontal,
  UserMinus,
  CheckCircle,
  Clock,
  XCircle,
  AlertTriangle,
  FileText,
  Calculator,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
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
import { formatDate } from '@/lib/utils';

type SeparationType = 'RESIGNATION' | 'TERMINATION' | 'RETIREMENT' | 'ABSCONDING' | 'DEATH';
type SeparationStatus = 'INITIATED' | 'CLEARANCE_PENDING' | 'FNF_PENDING' | 'APPROVED' | 'COMPLETED' | 'WITHDRAWN';

interface Separation {
  id: string;
  employee_id: string;
  employee_code: string;
  employee_name: string;
  department: string;
  designation: string;
  separation_type: SeparationType;
  status: SeparationStatus;
  notice_date: string;
  last_working_date: string;
  actual_relieving_date?: string;
  reason: string;
  initiated_by: string;
  clearance_progress: number;
}

// Mock data
const separationSummary = {
  total: 24,
  in_progress: 8,
  clearance_pending: 5,
  fnf_pending: 3,
  completed: 8,
};

const separations: Separation[] = [
  {
    id: '1',
    employee_id: 'emp-001',
    employee_code: 'EMP001',
    employee_name: 'Rahul Sharma',
    department: 'Engineering',
    designation: 'Senior Developer',
    separation_type: 'RESIGNATION',
    status: 'CLEARANCE_PENDING',
    notice_date: '2024-12-01',
    last_working_date: '2024-12-31',
    reason: 'Better opportunity',
    initiated_by: 'Self',
    clearance_progress: 60,
  },
  {
    id: '2',
    employee_id: 'emp-002',
    employee_code: 'EMP002',
    employee_name: 'Priya Patel',
    department: 'Finance',
    designation: 'Accountant',
    separation_type: 'RESIGNATION',
    status: 'FNF_PENDING',
    notice_date: '2024-11-15',
    last_working_date: '2024-12-15',
    actual_relieving_date: '2024-12-15',
    reason: 'Personal reasons',
    initiated_by: 'Self',
    clearance_progress: 100,
  },
  {
    id: '3',
    employee_id: 'emp-003',
    employee_code: 'EMP003',
    employee_name: 'Amit Kumar',
    department: 'Operations',
    designation: 'Manager',
    separation_type: 'RETIREMENT',
    status: 'INITIATED',
    notice_date: '2024-10-01',
    last_working_date: '2025-01-31',
    reason: 'Superannuation',
    initiated_by: 'HR',
    clearance_progress: 0,
  },
  {
    id: '4',
    employee_id: 'emp-004',
    employee_code: 'EMP004',
    employee_name: 'Sneha Reddy',
    department: 'HR',
    designation: 'Executive',
    separation_type: 'TERMINATION',
    status: 'COMPLETED',
    notice_date: '2024-11-01',
    last_working_date: '2024-11-01',
    actual_relieving_date: '2024-11-01',
    reason: 'Policy violation',
    initiated_by: 'Management',
    clearance_progress: 100,
  },
  {
    id: '5',
    employee_id: 'emp-005',
    employee_code: 'EMP005',
    employee_name: 'Vikram Singh',
    department: 'Sales',
    designation: 'Associate',
    separation_type: 'ABSCONDING',
    status: 'INITIATED',
    notice_date: '2024-12-10',
    last_working_date: '2024-12-10',
    reason: 'Absent without notice for 10+ days',
    initiated_by: 'HR',
    clearance_progress: 20,
  },
];

const getTypeBadge = (type: SeparationType) => {
  const config: Record<SeparationType, { color: string; label: string }> = {
    RESIGNATION: { color: 'bg-blue-100 text-blue-800', label: 'Resignation' },
    TERMINATION: { color: 'bg-red-100 text-red-800', label: 'Termination' },
    RETIREMENT: { color: 'bg-purple-100 text-purple-800', label: 'Retirement' },
    ABSCONDING: { color: 'bg-orange-100 text-orange-800', label: 'Absconding' },
    DEATH: { color: 'bg-gray-100 text-gray-800', label: 'Death' },
  };
  return (
    <Badge variant="secondary" className={config[type].color}>
      {config[type].label}
    </Badge>
  );
};

const getStatusBadge = (status: SeparationStatus) => {
  const config: Record<SeparationStatus, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ReactNode; label: string }> = {
    INITIATED: { variant: 'outline', icon: <Clock className="h-3 w-3 mr-1" />, label: 'Initiated' },
    CLEARANCE_PENDING: { variant: 'secondary', icon: <AlertTriangle className="h-3 w-3 mr-1" />, label: 'Clearance Pending' },
    FNF_PENDING: { variant: 'secondary', icon: <Calculator className="h-3 w-3 mr-1" />, label: 'F&F Pending' },
    APPROVED: { variant: 'default', icon: <CheckCircle className="h-3 w-3 mr-1" />, label: 'Approved' },
    COMPLETED: { variant: 'default', icon: <CheckCircle className="h-3 w-3 mr-1" />, label: 'Completed' },
    WITHDRAWN: { variant: 'destructive', icon: <XCircle className="h-3 w-3 mr-1" />, label: 'Withdrawn' },
  };
  const cfg = config[status];
  return (
    <Badge variant={cfg.variant} className="flex items-center w-fit">
      {cfg.icon}
      {cfg.label}
    </Badge>
  );
};

export default function SeparationList() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  const filteredSeparations = separations.filter((s) => {
    const matchesSearch =
      s.employee_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.employee_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.department.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = typeFilter === 'all' || s.separation_type === typeFilter;
    const matchesStatus = statusFilter === 'all' || s.status === statusFilter;
    return matchesSearch && matchesType && matchesStatus;
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Employee Separation"
        subtitle="Manage employee resignations, terminations, and exit process"
        actions={
          <Button onClick={() => navigate('/admin/hris/separation/new')}>
            <Plus className="h-4 w-4 mr-2" />
            Initiate Separation
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Separations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{separationSummary.total}</div>
            <p className="text-xs text-muted-foreground">This year</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              In Progress
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">
              {separationSummary.in_progress}
            </div>
            <p className="text-xs text-muted-foreground">Active cases</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Clearance Pending
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-600">
              {separationSummary.clearance_pending}
            </div>
            <p className="text-xs text-muted-foreground">Awaiting clearance</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              F&F Pending
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-yellow-600">
              {separationSummary.fnf_pending}
            </div>
            <p className="text-xs text-muted-foreground">Settlement due</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Completed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {separationSummary.completed}
            </div>
            <p className="text-xs text-muted-foreground">Fully processed</p>
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
                placeholder="Search by employee name, code, or department..."
                className="pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="RESIGNATION">Resignation</SelectItem>
                <SelectItem value="TERMINATION">Termination</SelectItem>
                <SelectItem value="RETIREMENT">Retirement</SelectItem>
                <SelectItem value="ABSCONDING">Absconding</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="INITIATED">Initiated</SelectItem>
                <SelectItem value="CLEARANCE_PENDING">Clearance Pending</SelectItem>
                <SelectItem value="FNF_PENDING">F&F Pending</SelectItem>
                <SelectItem value="APPROVED">Approved</SelectItem>
                <SelectItem value="COMPLETED">Completed</SelectItem>
                <SelectItem value="WITHDRAWN">Withdrawn</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Separations Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UserMinus className="h-5 w-5" />
            Separation Requests
          </CardTitle>
          <CardDescription>{filteredSeparations.length} records found</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Employee</TableHead>
                <TableHead>Department</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Notice Date</TableHead>
                <TableHead>Last Working Day</TableHead>
                <TableHead>Clearance</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredSeparations.map((sep) => (
                <TableRow key={sep.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{sep.employee_name}</div>
                      <div className="text-xs text-muted-foreground">{sep.employee_code}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div>
                      <div className="text-sm">{sep.department}</div>
                      <div className="text-xs text-muted-foreground">{sep.designation}</div>
                    </div>
                  </TableCell>
                  <TableCell>{getTypeBadge(sep.separation_type)}</TableCell>
                  <TableCell>{formatDate(sep.notice_date)}</TableCell>
                  <TableCell>
                    <div>
                      <div className="text-sm">{formatDate(sep.last_working_date)}</div>
                      {sep.actual_relieving_date && (
                        <div className="text-xs text-green-600">
                          Relieved: {formatDate(sep.actual_relieving_date)}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="w-24">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span>Progress</span>
                        <span>{sep.clearance_progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${sep.clearance_progress}%` }}
                        />
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>{getStatusBadge(sep.status)}</TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => navigate(`/admin/hris/separation/${sep.id}`)}
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => navigate(`/admin/hris/separation/${sep.id}/checklist`)}
                        >
                          <FileText className="h-4 w-4 mr-2" />
                          Clearance Checklist
                        </DropdownMenuItem>
                        {(sep.status === 'FNF_PENDING' || sep.status === 'CLEARANCE_PENDING') && (
                          <DropdownMenuItem
                            onClick={() => navigate(`/admin/hris/separation/${sep.id}/fnf`)}
                          >
                            <Calculator className="h-4 w-4 mr-2" />
                            F&F Calculation
                          </DropdownMenuItem>
                        )}
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
