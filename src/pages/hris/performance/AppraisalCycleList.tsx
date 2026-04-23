import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Plus,
  Eye,
  MoreHorizontal,
  Target,
  Calendar,
  Users,
  Clock,
  CheckCircle,
  PlayCircle,
  PauseCircle,
  BarChart3,
  Settings,
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
import { Progress } from '@/components/ui/progress';
import { formatDate } from '@/lib/utils';

type CycleStatus = 'DRAFT' | 'GOAL_SETTING' | 'IN_PROGRESS' | 'REVIEW' | 'CALIBRATION' | 'COMPLETED';

interface AppraisalCycle {
  id: string;
  cycle_name: string;
  cycle_code: string;
  financial_year: string;
  cycle_type: 'ANNUAL' | 'HALF_YEARLY' | 'QUARTERLY';
  start_date: string;
  end_date: string;
  goal_setting_deadline: string;
  self_appraisal_deadline: string;
  manager_review_deadline: string;
  status: CycleStatus;
  eligible_employees: number;
  completed_appraisals: number;
  pending_self_appraisal: number;
  pending_manager_review: number;
}

// Mock summary data
const cycleSummary = {
  total_cycles: 12,
  active: 2,
  completed: 9,
  draft: 1,
  employees_appraised: 450,
};

// Mock data
const appraisalCycles: AppraisalCycle[] = [
  {
    id: '1',
    cycle_name: 'Annual Performance Review 2024-25',
    cycle_code: 'APR-2024-25',
    financial_year: '2024-25',
    cycle_type: 'ANNUAL',
    start_date: '2024-04-01',
    end_date: '2025-03-31',
    goal_setting_deadline: '2024-04-30',
    self_appraisal_deadline: '2025-01-31',
    manager_review_deadline: '2025-02-28',
    status: 'IN_PROGRESS',
    eligible_employees: 150,
    completed_appraisals: 45,
    pending_self_appraisal: 80,
    pending_manager_review: 25,
  },
  {
    id: '2',
    cycle_name: 'Mid-Year Review H1 2024-25',
    cycle_code: 'MYR-H1-2024-25',
    financial_year: '2024-25',
    cycle_type: 'HALF_YEARLY',
    start_date: '2024-04-01',
    end_date: '2024-09-30',
    goal_setting_deadline: '2024-04-15',
    self_appraisal_deadline: '2024-09-25',
    manager_review_deadline: '2024-09-30',
    status: 'COMPLETED',
    eligible_employees: 145,
    completed_appraisals: 145,
    pending_self_appraisal: 0,
    pending_manager_review: 0,
  },
  {
    id: '3',
    cycle_name: 'Annual Performance Review 2023-24',
    cycle_code: 'APR-2023-24',
    financial_year: '2023-24',
    cycle_type: 'ANNUAL',
    start_date: '2023-04-01',
    end_date: '2024-03-31',
    goal_setting_deadline: '2023-04-30',
    self_appraisal_deadline: '2024-01-31',
    manager_review_deadline: '2024-02-28',
    status: 'COMPLETED',
    eligible_employees: 135,
    completed_appraisals: 135,
    pending_self_appraisal: 0,
    pending_manager_review: 0,
  },
  {
    id: '4',
    cycle_name: 'Q3 Review 2024-25',
    cycle_code: 'QR-Q3-2024-25',
    financial_year: '2024-25',
    cycle_type: 'QUARTERLY',
    start_date: '2024-10-01',
    end_date: '2024-12-31',
    goal_setting_deadline: '2024-10-10',
    self_appraisal_deadline: '2024-12-25',
    manager_review_deadline: '2024-12-31',
    status: 'REVIEW',
    eligible_employees: 148,
    completed_appraisals: 90,
    pending_self_appraisal: 20,
    pending_manager_review: 38,
  },
];

const getStatusBadge = (status: CycleStatus) => {
  const config: Record<CycleStatus, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ReactNode; label: string; color?: string }> = {
    DRAFT: { variant: 'outline', icon: <Clock className="h-3 w-3 mr-1" />, label: 'Draft' },
    GOAL_SETTING: { variant: 'secondary', icon: <Target className="h-3 w-3 mr-1" />, label: 'Goal Setting', color: 'bg-blue-100 text-blue-800' },
    IN_PROGRESS: { variant: 'default', icon: <PlayCircle className="h-3 w-3 mr-1" />, label: 'In Progress', color: 'bg-green-100 text-green-800' },
    REVIEW: { variant: 'secondary', icon: <BarChart3 className="h-3 w-3 mr-1" />, label: 'Under Review', color: 'bg-orange-100 text-orange-800' },
    CALIBRATION: { variant: 'secondary', icon: <Settings className="h-3 w-3 mr-1" />, label: 'Calibration', color: 'bg-purple-100 text-purple-800' },
    COMPLETED: { variant: 'default', icon: <CheckCircle className="h-3 w-3 mr-1" />, label: 'Completed' },
  };
  const cfg = config[status];
  return (
    <Badge variant={cfg.variant} className={`flex items-center w-fit ${cfg.color || ''}`}>
      {cfg.icon}
      {cfg.label}
    </Badge>
  );
};

const getCycleTypeBadge = (type: string) => {
  const colors: Record<string, string> = {
    ANNUAL: 'bg-purple-100 text-purple-800',
    HALF_YEARLY: 'bg-blue-100 text-blue-800',
    QUARTERLY: 'bg-green-100 text-green-800',
  };
  const labels: Record<string, string> = {
    ANNUAL: 'Annual',
    HALF_YEARLY: 'Half-Yearly',
    QUARTERLY: 'Quarterly',
  };
  return (
    <Badge variant="secondary" className={colors[type]}>
      {labels[type]}
    </Badge>
  );
};

export default function AppraisalCycleList() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');

  const filteredCycles = appraisalCycles.filter((c) => {
    const matchesSearch =
      c.cycle_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.cycle_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.financial_year.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || c.status === statusFilter;
    const matchesType = typeFilter === 'all' || c.cycle_type === typeFilter;
    return matchesSearch && matchesStatus && matchesType;
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Performance Appraisal"
        subtitle="Manage appraisal cycles and employee performance reviews"
        actions={
          <Button onClick={() => navigate('/admin/hris/performance/cycles/new')}>
            <Plus className="h-4 w-4 mr-2" />
            Create Cycle
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Cycles
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{cycleSummary.total_cycles}</div>
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Active Cycles
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{cycleSummary.active}</div>
            <p className="text-xs text-muted-foreground">Currently running</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Completed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">{cycleSummary.completed}</div>
            <p className="text-xs text-muted-foreground">Past cycles</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Draft
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-600">{cycleSummary.draft}</div>
            <p className="text-xs text-muted-foreground">Not started</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Employees Appraised
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-600">
              {cycleSummary.employees_appraised}
            </div>
            <p className="text-xs text-muted-foreground">This year</p>
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
                placeholder="Search by cycle name, code, or year..."
                className="pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Cycle Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="ANNUAL">Annual</SelectItem>
                <SelectItem value="HALF_YEARLY">Half-Yearly</SelectItem>
                <SelectItem value="QUARTERLY">Quarterly</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="DRAFT">Draft</SelectItem>
                <SelectItem value="GOAL_SETTING">Goal Setting</SelectItem>
                <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
                <SelectItem value="REVIEW">Under Review</SelectItem>
                <SelectItem value="CALIBRATION">Calibration</SelectItem>
                <SelectItem value="COMPLETED">Completed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Cycles Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Appraisal Cycles
          </CardTitle>
          <CardDescription>{filteredCycles.length} cycles found</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Cycle</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Period</TableHead>
                <TableHead>Deadlines</TableHead>
                <TableHead>Progress</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredCycles.map((cycle) => (
                <TableRow key={cycle.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{cycle.cycle_name}</div>
                      <div className="text-xs text-muted-foreground">{cycle.cycle_code}</div>
                    </div>
                  </TableCell>
                  <TableCell>{getCycleTypeBadge(cycle.cycle_type)}</TableCell>
                  <TableCell>
                    <div>
                      <div className="text-sm">{cycle.financial_year}</div>
                      <div className="text-xs text-muted-foreground">
                        {formatDate(cycle.start_date)} - {formatDate(cycle.end_date)}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-xs space-y-1">
                      <div>
                        <span className="text-muted-foreground">Self: </span>
                        {formatDate(cycle.self_appraisal_deadline)}
                      </div>
                      <div>
                        <span className="text-muted-foreground">Manager: </span>
                        {formatDate(cycle.manager_review_deadline)}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="w-32">
                      <div className="flex justify-between text-xs mb-1">
                        <span>{cycle.completed_appraisals}/{cycle.eligible_employees}</span>
                        <span>
                          {Math.round((cycle.completed_appraisals / cycle.eligible_employees) * 100)}%
                        </span>
                      </div>
                      <Progress
                        value={(cycle.completed_appraisals / cycle.eligible_employees) * 100}
                        className="h-2"
                      />
                      {cycle.pending_self_appraisal > 0 && (
                        <div className="text-xs text-orange-600 mt-1">
                          {cycle.pending_self_appraisal} pending self-appraisal
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>{getStatusBadge(cycle.status)}</TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => navigate(`/admin/hris/performance/cycles/${cycle.id}`)}
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => navigate(`/admin/hris/performance/cycles/${cycle.id}/goals`)}
                        >
                          <Target className="h-4 w-4 mr-2" />
                          Manage Goals
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => navigate(`/admin/hris/performance/cycles/${cycle.id}/appraisals`)}
                        >
                          <Users className="h-4 w-4 mr-2" />
                          View Appraisals
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => navigate(`/admin/hris/performance/cycles/${cycle.id}/reports`)}
                        >
                          <BarChart3 className="h-4 w-4 mr-2" />
                          Reports
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
