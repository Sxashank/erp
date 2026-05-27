import {
  Calendar,
  CheckCircle,
  Clock,
  Eye,
  GraduationCap,
  MapPin,
  MoreHorizontal,
  PlayCircle,
  Plus,
  Search,
  Users,
  XCircle,
} from 'lucide-react';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { SkeletonTable } from '@/components/common/SkeletonTable';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
import { useTrainingPrograms } from '@/hooks/hris/useTraining';
import type { TrainingProgramMode, TrainingProgramStatus } from '@/services/hris/trainingApi';

const MODE_OPTIONS: { label: string; value: TrainingProgramMode }[] = [
  { label: 'Classroom', value: 'CLASSROOM' },
  { label: 'Virtual', value: 'VIRTUAL' },
  { label: 'E-Learning', value: 'E_LEARNING' },
  { label: 'Workshop', value: 'WORKSHOP' },
  { label: 'On-the-Job', value: 'ON_THE_JOB' },
];

function getStatusBadge(status: TrainingProgramStatus) {
  switch (status) {
    case 'DRAFT':
      return (
        <Badge variant="outline" className="flex w-fit items-center">
          <Clock className="mr-1 h-3 w-3" />
          Draft
        </Badge>
      );
    case 'SCHEDULED':
      return (
        <Badge variant="secondary" className="flex w-fit items-center">
          <Calendar className="mr-1 h-3 w-3" />
          Scheduled
        </Badge>
      );
    case 'IN_PROGRESS':
      return (
        <Badge variant="default" className="flex w-fit items-center">
          <PlayCircle className="mr-1 h-3 w-3" />
          In Progress
        </Badge>
      );
    case 'COMPLETED':
      return (
        <Badge variant="default" className="flex w-fit items-center bg-green-100 text-green-800">
          <CheckCircle className="mr-1 h-3 w-3" />
          Completed
        </Badge>
      );
    case 'CANCELLED':
      return (
        <Badge variant="destructive" className="flex w-fit items-center">
          <XCircle className="mr-1 h-3 w-3" />
          Cancelled
        </Badge>
      );
  }
}

function getModeBadge(mode: TrainingProgramMode) {
  const label =
    MODE_OPTIONS.find((option) => option.value === mode)?.label ?? mode.replace(/_/g, ' ');
  return (
    <Badge variant="outline" className="text-xs">
      {label}
    </Badge>
  );
}

export default function TrainingProgramList() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState<'all' | TrainingProgramStatus>('all');
  const [modeFilter, setModeFilter] = useState<'all' | TrainingProgramMode>('all');

  const query = useTrainingPrograms({
    search: searchTerm || undefined,
    category: categoryFilter !== 'all' ? categoryFilter : undefined,
    status: statusFilter !== 'all' ? statusFilter : undefined,
    mode: modeFilter !== 'all' ? modeFilter : undefined,
    skip: 0,
    limit: 100,
  });

  const programs = query.data?.items ?? [];
  const summary = query.data?.summary ?? {
    totalPrograms: 0,
    scheduled: 0,
    inProgress: 0,
    completed: 0,
    totalParticipants: 0,
  };
  const categories = useMemo(
    () => Array.from(new Set(programs.map((program) => program.category))).sort(),
    [programs],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Training Programs"
        subtitle="Manage employee training and development programs"
        actions={
          <Button onClick={() => navigate('/admin/hris/training/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Create Training Program
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Programs
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{summary.totalPrograms}</div>
            <p className="text-xs text-muted-foreground">Available in the active org</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Scheduled</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">{summary.scheduled}</div>
            <p className="text-xs text-muted-foreground">Upcoming sessions</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">In Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{summary.inProgress}</div>
            <p className="text-xs text-muted-foreground">Currently running</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Completed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-600">{summary.completed}</div>
            <p className="text-xs text-muted-foreground">Closed programs</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Participants
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-600">{summary.totalParticipants}</div>
            <p className="text-xs text-muted-foreground">Nominated or attended</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4">
            <div className="relative min-w-[220px] flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Search by title, code, or trainer..."
                className="pl-10"
              />
            </div>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-44">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {categories.map((category) => (
                  <SelectItem key={category} value={category}>
                    {category}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={modeFilter}
              onValueChange={(value) => setModeFilter(value as typeof modeFilter)}
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Mode" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Modes</SelectItem>
                {MODE_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={statusFilter}
              onValueChange={(value) => setStatusFilter(value as typeof statusFilter)}
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="DRAFT">Draft</SelectItem>
                <SelectItem value="SCHEDULED">Scheduled</SelectItem>
                <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
                <SelectItem value="COMPLETED">Completed</SelectItem>
                <SelectItem value="CANCELLED">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GraduationCap className="h-5 w-5" />
            Training Programs
          </CardTitle>
        </CardHeader>
        <CardContent>
          {query.isLoading ? (
            <SkeletonTable rows={6} columns={8} />
          ) : query.isError ? (
            <ErrorState error={query.error} onRetry={() => void query.refetch()} />
          ) : programs.length === 0 ? (
            <EmptyState
              title="No training programs found"
              subtitle="Create a training program to start scheduling nominations and feedback."
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Program</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Schedule</TableHead>
                  <TableHead>Mode</TableHead>
                  <TableHead>Trainer</TableHead>
                  <TableHead>Participants</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {programs.map((program) => (
                  <TableRow key={program.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{program.title}</div>
                        <div className="text-xs text-muted-foreground">{program.programCode}</div>
                      </div>
                    </TableCell>
                    <TableCell>{program.category}</TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <div>
                          <DateDisplay date={program.startDate} /> to{' '}
                          <DateDisplay date={program.endDate} />
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {program.durationHours} hours
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        {getModeBadge(program.mode)}
                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                          <MapPin className="h-3 w-3" />
                          {program.location}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">{program.trainerName}</div>
                        <div className="text-xs text-muted-foreground">{program.trainerType}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Users className="h-4 w-4 text-muted-foreground" />
                        <span>
                          {program.enrolledCount}/{program.maxParticipants}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>{getStatusBadge(program.status)}</TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={() => navigate(`/admin/hris/training/${program.id}`)}
                          >
                            <Eye className="mr-2 h-4 w-4" />
                            Edit Program
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() =>
                              navigate(`/admin/hris/training/${program.id}/nominations`)
                            }
                          >
                            <Users className="mr-2 h-4 w-4" />
                            Manage Nominations
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => navigate(`/admin/hris/training/${program.id}/feedback`)}
                          >
                            <CheckCircle className="mr-2 h-4 w-4" />
                            View Feedback
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
