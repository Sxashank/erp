import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Plus,
  Eye,
  MoreHorizontal,
  GraduationCap,
  Calendar,
  Users,
  Clock,
  MapPin,
  CheckCircle,
  XCircle,
  PlayCircle,
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

type TrainingStatus = 'DRAFT' | 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
type TrainingMode = 'CLASSROOM' | 'VIRTUAL' | 'E_LEARNING' | 'WORKSHOP' | 'ON_THE_JOB';

interface TrainingProgram {
  id: string;
  program_code: string;
  title: string;
  description: string;
  category: string;
  mode: TrainingMode;
  trainer_name: string;
  trainer_type: 'INTERNAL' | 'EXTERNAL';
  start_date: string;
  end_date: string;
  duration_hours: number;
  location: string;
  max_participants: number;
  enrolled_count: number;
  status: TrainingStatus;
  cost_per_participant: number;
}

// Mock data
const trainingSummary = {
  total_programs: 45,
  scheduled: 12,
  in_progress: 5,
  completed: 25,
  total_participants: 320,
};

const trainingPrograms: TrainingProgram[] = [
  {
    id: '1',
    program_code: 'TRN-2024-001',
    title: 'Leadership Excellence Program',
    description: 'Develop leadership skills for mid-level managers',
    category: 'Leadership',
    mode: 'CLASSROOM',
    trainer_name: 'Dr. Anand Verma',
    trainer_type: 'EXTERNAL',
    start_date: '2025-01-15',
    end_date: '2025-01-17',
    duration_hours: 24,
    location: 'Training Center - Mumbai',
    max_participants: 25,
    enrolled_count: 22,
    status: 'SCHEDULED',
    cost_per_participant: 15000,
  },
  {
    id: '2',
    program_code: 'TRN-2024-002',
    title: 'Advanced Excel & Data Analysis',
    description: 'Master advanced Excel features and data analytics',
    category: 'Technical',
    mode: 'VIRTUAL',
    trainer_name: 'Priya Sharma',
    trainer_type: 'INTERNAL',
    start_date: '2025-01-10',
    end_date: '2025-01-12',
    duration_hours: 16,
    location: 'Online - Microsoft Teams',
    max_participants: 50,
    enrolled_count: 45,
    status: 'IN_PROGRESS',
    cost_per_participant: 0,
  },
  {
    id: '3',
    program_code: 'TRN-2024-003',
    title: 'Compliance & Regulatory Training',
    description: 'Annual mandatory compliance training for all employees',
    category: 'Compliance',
    mode: 'E_LEARNING',
    trainer_name: 'System Generated',
    trainer_type: 'INTERNAL',
    start_date: '2025-01-01',
    end_date: '2025-01-31',
    duration_hours: 4,
    location: 'E-Learning Portal',
    max_participants: 500,
    enrolled_count: 380,
    status: 'IN_PROGRESS',
    cost_per_participant: 0,
  },
  {
    id: '4',
    program_code: 'TRN-2024-004',
    title: 'Customer Service Excellence',
    description: 'Enhance customer handling and service delivery skills',
    category: 'Soft Skills',
    mode: 'WORKSHOP',
    trainer_name: 'Rajesh Kumar',
    trainer_type: 'EXTERNAL',
    start_date: '2024-12-15',
    end_date: '2024-12-16',
    duration_hours: 12,
    location: 'Training Center - Delhi',
    max_participants: 30,
    enrolled_count: 28,
    status: 'COMPLETED',
    cost_per_participant: 8000,
  },
  {
    id: '5',
    program_code: 'TRN-2024-005',
    title: 'Project Management Fundamentals',
    description: 'Introduction to project management methodologies',
    category: 'Management',
    mode: 'CLASSROOM',
    trainer_name: 'Amit Patel',
    trainer_type: 'INTERNAL',
    start_date: '2025-02-01',
    end_date: '2025-02-03',
    duration_hours: 20,
    location: 'Training Center - Mumbai',
    max_participants: 20,
    enrolled_count: 8,
    status: 'SCHEDULED',
    cost_per_participant: 5000,
  },
];

const getStatusBadge = (status: TrainingStatus) => {
  const config: Record<TrainingStatus, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ReactNode; label: string }> = {
    DRAFT: { variant: 'outline', icon: <Clock className="h-3 w-3 mr-1" />, label: 'Draft' },
    SCHEDULED: { variant: 'secondary', icon: <Calendar className="h-3 w-3 mr-1" />, label: 'Scheduled' },
    IN_PROGRESS: { variant: 'default', icon: <PlayCircle className="h-3 w-3 mr-1" />, label: 'In Progress' },
    COMPLETED: { variant: 'default', icon: <CheckCircle className="h-3 w-3 mr-1" />, label: 'Completed' },
    CANCELLED: { variant: 'destructive', icon: <XCircle className="h-3 w-3 mr-1" />, label: 'Cancelled' },
  };
  const cfg = config[status];
  return (
    <Badge variant={cfg.variant} className="flex items-center w-fit">
      {cfg.icon}
      {cfg.label}
    </Badge>
  );
};

const getModeBadge = (mode: TrainingMode) => {
  const modeLabels: Record<TrainingMode, string> = {
    CLASSROOM: 'Classroom',
    VIRTUAL: 'Virtual',
    E_LEARNING: 'E-Learning',
    WORKSHOP: 'Workshop',
    ON_THE_JOB: 'On-the-Job',
  };
  return (
    <Badge variant="outline" className="text-xs">
      {modeLabels[mode]}
    </Badge>
  );
};

export default function TrainingProgramList() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [modeFilter, setModeFilter] = useState('all');

  const filteredPrograms = trainingPrograms.filter((p) => {
    const matchesSearch =
      p.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.program_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.trainer_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || p.category === categoryFilter;
    const matchesStatus = statusFilter === 'all' || p.status === statusFilter;
    const matchesMode = modeFilter === 'all' || p.mode === modeFilter;
    return matchesSearch && matchesCategory && matchesStatus && matchesMode;
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Training Programs"
        subtitle="Manage employee training and development programs"
        actions={
          <Button onClick={() => navigate('/admin/hris/training/new')}>
            <Plus className="h-4 w-4 mr-2" />
            Create Program
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Programs
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{trainingSummary.total_programs}</div>
            <p className="text-xs text-muted-foreground">This year</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Scheduled
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">
              {trainingSummary.scheduled}
            </div>
            <p className="text-xs text-muted-foreground">Upcoming</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              In Progress
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {trainingSummary.in_progress}
            </div>
            <p className="text-xs text-muted-foreground">Ongoing</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Completed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-600">
              {trainingSummary.completed}
            </div>
            <p className="text-xs text-muted-foreground">This year</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Participants
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-600">
              {trainingSummary.total_participants}
            </div>
            <p className="text-xs text-muted-foreground">Trained</p>
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
                placeholder="Search by title, code, or trainer..."
                className="pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="Leadership">Leadership</SelectItem>
                <SelectItem value="Technical">Technical</SelectItem>
                <SelectItem value="Compliance">Compliance</SelectItem>
                <SelectItem value="Soft Skills">Soft Skills</SelectItem>
                <SelectItem value="Management">Management</SelectItem>
              </SelectContent>
            </Select>
            <Select value={modeFilter} onValueChange={setModeFilter}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Mode" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Modes</SelectItem>
                <SelectItem value="CLASSROOM">Classroom</SelectItem>
                <SelectItem value="VIRTUAL">Virtual</SelectItem>
                <SelectItem value="E_LEARNING">E-Learning</SelectItem>
                <SelectItem value="WORKSHOP">Workshop</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="SCHEDULED">Scheduled</SelectItem>
                <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
                <SelectItem value="COMPLETED">Completed</SelectItem>
                <SelectItem value="CANCELLED">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Programs Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GraduationCap className="h-5 w-5" />
            Training Programs
          </CardTitle>
          <CardDescription>{filteredPrograms.length} programs found</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Program</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Mode</TableHead>
                <TableHead>Schedule</TableHead>
                <TableHead>Trainer</TableHead>
                <TableHead>Enrollment</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredPrograms.map((program) => (
                <TableRow key={program.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{program.title}</div>
                      <div className="text-xs text-muted-foreground">{program.program_code}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{program.category}</Badge>
                  </TableCell>
                  <TableCell>{getModeBadge(program.mode)}</TableCell>
                  <TableCell>
                    <div>
                      <div className="text-sm flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {formatDate(program.start_date)}
                      </div>
                      <div className="text-xs text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {program.duration_hours} hours
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div>
                      <div className="text-sm">{program.trainer_name}</div>
                      <div className="text-xs text-muted-foreground">
                        {program.trainer_type === 'INTERNAL' ? 'Internal' : 'External'}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4 text-muted-foreground" />
                      <span>
                        {program.enrolled_count}/{program.max_participants}
                      </span>
                    </div>
                    <div className="w-24 bg-gray-200 rounded-full h-1.5 mt-1">
                      <div
                        className="bg-blue-600 h-1.5 rounded-full"
                        style={{
                          width: `${(program.enrolled_count / program.max_participants) * 100}%`,
                        }}
                      />
                    </div>
                  </TableCell>
                  <TableCell>{getStatusBadge(program.status)}</TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => navigate(`/admin/hris/training/${program.id}`)}
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        {program.status === 'SCHEDULED' && (
                          <DropdownMenuItem
                            onClick={() => navigate(`/admin/hris/training/${program.id}/nominations`)}
                          >
                            <Users className="h-4 w-4 mr-2" />
                            Manage Nominations
                          </DropdownMenuItem>
                        )}
                        {program.status === 'COMPLETED' && (
                          <DropdownMenuItem
                            onClick={() => navigate(`/admin/hris/training/${program.id}/feedback`)}
                          >
                            <CheckCircle className="h-4 w-4 mr-2" />
                            View Feedback
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
