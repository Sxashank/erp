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
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
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
import { formatDate } from '@/lib/utils';
import { hrisApi } from '@/services/api';

type SeparationType = 'RESIGNATION' | 'TERMINATION' | 'RETIREMENT' | 'ABSCONDING' | 'DEATH' | 'VRS' | 'CONTRACT_END';
type SeparationStatus =
  | 'INITIATED'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'NOTICE_PERIOD'
  | 'CLEARANCE'
  | 'FNF_PENDING'
  | 'FNF_CALCULATED'
  | 'FNF_APPROVED'
  | 'FNF_PAID'
  | 'COMPLETED'
  | 'WITHDRAWN'
  | 'REJECTED';

interface Separation {
  id: string;
  employee_id: string;
  employee_code?: string;
  employee_name?: string;
  separation_type: SeparationType;
  status: SeparationStatus;
  initiation_date: string;
  requested_last_working_date?: string;
  approved_last_working_date?: string;
  actual_last_working_date?: string;
  notice_period_days: number;
  notice_period_served: number;
  notice_period_shortfall: number;
  is_notice_buyout: boolean;
  reason_category?: string;
  remarks?: string;
}

const getTypeBadge = (type: SeparationType) => {
  const config: Record<SeparationType, { color: string; label: string }> = {
    RESIGNATION: { color: 'bg-blue-100 text-blue-800', label: 'Resignation' },
    TERMINATION: { color: 'bg-red-100 text-red-800', label: 'Termination' },
    RETIREMENT: { color: 'bg-purple-100 text-purple-800', label: 'Retirement' },
    ABSCONDING: { color: 'bg-orange-100 text-orange-800', label: 'Absconding' },
    DEATH: { color: 'bg-gray-100 text-gray-800', label: 'Death' },
    VRS: { color: 'bg-indigo-100 text-indigo-800', label: 'VRS' },
    CONTRACT_END: { color: 'bg-slate-100 text-slate-700', label: 'Contract End' },
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
    PENDING_APPROVAL: { variant: 'secondary', icon: <Clock className="h-3 w-3 mr-1" />, label: 'Pending Approval' },
    NOTICE_PERIOD: { variant: 'secondary', icon: <Clock className="h-3 w-3 mr-1" />, label: 'Notice Period' },
    CLEARANCE: { variant: 'secondary', icon: <AlertTriangle className="h-3 w-3 mr-1" />, label: 'Clearance' },
    FNF_PENDING: { variant: 'secondary', icon: <Calculator className="h-3 w-3 mr-1" />, label: 'F&F Pending' },
    FNF_CALCULATED: { variant: 'secondary', icon: <Calculator className="h-3 w-3 mr-1" />, label: 'F&F Calculated' },
    FNF_APPROVED: { variant: 'default', icon: <CheckCircle className="h-3 w-3 mr-1" />, label: 'F&F Approved' },
    FNF_PAID: { variant: 'default', icon: <CheckCircle className="h-3 w-3 mr-1" />, label: 'F&F Paid' },
    APPROVED: { variant: 'default', icon: <CheckCircle className="h-3 w-3 mr-1" />, label: 'Approved' },
    COMPLETED: { variant: 'default', icon: <CheckCircle className="h-3 w-3 mr-1" />, label: 'Completed' },
    WITHDRAWN: { variant: 'destructive', icon: <XCircle className="h-3 w-3 mr-1" />, label: 'Withdrawn' },
    REJECTED: { variant: 'destructive', icon: <XCircle className="h-3 w-3 mr-1" />, label: 'Rejected' },
  };
  const cfg = config[status];
  return (
    <Badge variant={cfg.variant} className="flex items-center w-fit">
      {cfg.icon}
      {cfg.label}
    </Badge>
  );
};

const getClearanceProgress = (status: SeparationStatus) => {
  if (['COMPLETED', 'FNF_PAID'].includes(status)) return 100;
  if (['FNF_APPROVED', 'FNF_CALCULATED', 'FNF_PENDING'].includes(status)) return 85;
  if (status === 'CLEARANCE') return 50;
  if (['APPROVED', 'NOTICE_PERIOD'].includes(status)) return 30;
  if (status === 'INITIATED' || status === 'PENDING_APPROVAL') return 10;
  return 0;
};

export default function SeparationList() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [separations, setSeparations] = useState<Separation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    let mounted = true;
    const loadSeparations = async () => {
      setIsLoading(true);
      try {
        const response = await hrisApi.listSeparations({ limit: 100 });
        if (!mounted) return;
        setSeparations(response.data.items || []);
      } catch (error) {
        if (!mounted) return;
        toast({
          title: 'Unable to load separations',
          description: 'Check your HRIS separation permissions and retry.',
          variant: 'destructive',
        });
      } finally {
        if (mounted) setIsLoading(false);
      }
    };
    loadSeparations();
    return () => {
      mounted = false;
    };
  }, [toast]);

  const filteredSeparations = useMemo(() => separations.filter((s) => {
    const matchesSearch =
      (s.employee_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (s.employee_code || '').toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = typeFilter === 'all' || s.separation_type === typeFilter;
    const matchesStatus = statusFilter === 'all' || s.status === statusFilter;
    return matchesSearch && matchesType && matchesStatus;
  }), [searchTerm, separations, statusFilter, typeFilter]);

  const separationSummary = useMemo(() => ({
    total: separations.length,
    in_progress: separations.filter((s) => !['COMPLETED', 'WITHDRAWN', 'REJECTED'].includes(s.status)).length,
    clearance_pending: separations.filter((s) => s.status === 'CLEARANCE').length,
    fnf_pending: separations.filter((s) => ['FNF_PENDING', 'FNF_CALCULATED'].includes(s.status)).length,
    completed: separations.filter((s) => ['COMPLETED', 'FNF_PAID'].includes(s.status)).length,
  }), [separations]);

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
                <SelectItem value="DEATH">Death</SelectItem>
                <SelectItem value="VRS">VRS</SelectItem>
                <SelectItem value="CONTRACT_END">Contract End</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="INITIATED">Initiated</SelectItem>
                <SelectItem value="PENDING_APPROVAL">Pending Approval</SelectItem>
                <SelectItem value="NOTICE_PERIOD">Notice Period</SelectItem>
                <SelectItem value="CLEARANCE">Clearance</SelectItem>
                <SelectItem value="FNF_PENDING">F&F Pending</SelectItem>
                <SelectItem value="FNF_CALCULATED">F&F Calculated</SelectItem>
                <SelectItem value="APPROVED">Approved</SelectItem>
                <SelectItem value="COMPLETED">Completed</SelectItem>
                <SelectItem value="WITHDRAWN">Withdrawn</SelectItem>
                <SelectItem value="REJECTED">Rejected</SelectItem>
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
                <TableHead>Reason</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Notice Date</TableHead>
                <TableHead>Last Working Day</TableHead>
                <TableHead>Clearance</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center text-sm text-muted-foreground">
                    Loading separation records...
                  </TableCell>
                </TableRow>
              ) : filteredSeparations.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center text-sm text-muted-foreground">
                    No separation records found.
                  </TableCell>
                </TableRow>
              ) : filteredSeparations.map((sep) => {
                const clearanceProgress = getClearanceProgress(sep.status);
                const lastWorkingDate =
                  sep.approved_last_working_date || sep.requested_last_working_date;
                return (
                <TableRow key={sep.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{sep.employee_name || 'Employee'}</div>
                      <div className="text-xs text-muted-foreground">{sep.employee_code || sep.employee_id}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div>
                      <div className="text-sm">{sep.reason_category?.replace(/_/g, ' ') || '—'}</div>
                      <div className="text-xs text-muted-foreground">
                        {sep.is_notice_buyout ? 'Notice buyout' : `${sep.notice_period_days} day notice`}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>{getTypeBadge(sep.separation_type)}</TableCell>
                  <TableCell>{formatDate(sep.initiation_date)}</TableCell>
                  <TableCell>
                    <div>
                      <div className="text-sm">{lastWorkingDate ? formatDate(lastWorkingDate) : '—'}</div>
                      {sep.actual_last_working_date && (
                        <div className="text-xs text-green-600">
                          Relieved: {formatDate(sep.actual_last_working_date)}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="w-24">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span>Progress</span>
                        <span>{clearanceProgress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${clearanceProgress}%` }}
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
                        {(['FNF_PENDING', 'FNF_CALCULATED', 'FNF_APPROVED', 'FNF_PAID', 'CLEARANCE'] as SeparationStatus[]).includes(sep.status) && (
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
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
