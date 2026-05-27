import { AlertTriangle, CheckCircle, Clock, Search, UserPlus, Users, XCircle } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
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
import {
  useAddTrainingNominations,
  useTrainingAvailableEmployees,
  useTrainingNominations,
  useTrainingProgram,
  useUpdateTrainingNomination,
} from '@/hooks/hris/useTraining';
import { useToast } from '@/hooks/use-toast';
import { getErrorMessage } from '@/lib/errorMessage';
import { formatDate } from '@/lib/utils';
import type { TrainingNominationStatus } from '@/services/hris/trainingApi';

function getStatusBadge(status: TrainingNominationStatus) {
  switch (status) {
    case 'NOMINATED':
      return <Badge variant="outline">Nominated</Badge>;
    case 'CONFIRMED':
      return <Badge variant="secondary">Confirmed</Badge>;
    case 'ATTENDED':
      return <Badge variant="default">Attended</Badge>;
    case 'NO_SHOW':
      return <Badge variant="destructive">No Show</Badge>;
    case 'CANCELLED':
      return <Badge variant="destructive">Cancelled</Badge>;
  }
}

export default function TrainingNomination() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { toast } = useToast();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | TrainingNominationStatus>('all');
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [selectedEmployees, setSelectedEmployees] = useState<string[]>([]);
  const [employeeSearch, setEmployeeSearch] = useState('');

  const programQuery = useTrainingProgram(id);
  const nominationsQuery = useTrainingNominations(id);
  const availableEmployeesQuery = useTrainingAvailableEmployees(id, employeeSearch || undefined);
  const addNominations = useAddTrainingNominations(id ?? '');
  const updateNomination = useUpdateTrainingNomination(id ?? '');

  const nominations = nominationsQuery.data ?? [];
  const filteredNominations = useMemo(
    () =>
      nominations.filter((nomination) => {
        const matchesSearch =
          nomination.employeeName.toLowerCase().includes(searchTerm.toLowerCase()) ||
          nomination.employeeCode.toLowerCase().includes(searchTerm.toLowerCase()) ||
          nomination.department.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesStatus = statusFilter === 'all' || nomination.status === statusFilter;
        return matchesSearch && matchesStatus;
      }),
    [nominations, searchTerm, statusFilter],
  );
  const availableEmployees = availableEmployeesQuery.data ?? [];
  const program = programQuery.data;

  const enrolledCount = nominations.filter((nomination) =>
    ['NOMINATED', 'CONFIRMED', 'ATTENDED'].includes(nomination.status),
  ).length;
  const availableSlots = Math.max(0, (program?.maxParticipants ?? 0) - enrolledCount);

  const handleAddNominations = async () => {
    try {
      await addNominations.mutateAsync(selectedEmployees);
      setSelectedEmployees([]);
      setShowAddDialog(false);
      toast({ title: 'Nominations added' });
    } catch (error: unknown) {
      toast({
        title: 'Unable to add nominations',
        description: getErrorMessage(error, 'Please try again.'),
        variant: 'destructive',
      });
    }
  };

  const handleStatusChange = async (
    nominationId: string,
    status: TrainingNominationStatus,
    attendanceMarked?: boolean,
  ) => {
    try {
      await updateNomination.mutateAsync({
        nominationId,
        payload: { status, attendanceMarked },
      });
      toast({ title: 'Nomination updated' });
    } catch (error: unknown) {
      toast({
        title: 'Unable to update nomination',
        description: getErrorMessage(error, 'Please try again.'),
        variant: 'destructive',
      });
    }
  };

  if (programQuery.isLoading || nominationsQuery.isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Training Nominations"
          subtitle="Loading training program"
          breadcrumbs={[
            { label: 'Training', to: '/admin/hris/training' },
            { label: 'Nominations' },
          ]}
        />
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            Loading nominations...
          </CardContent>
        </Card>
      </div>
    );
  }

  if (programQuery.isError || nominationsQuery.isError) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Training Nominations"
          subtitle="Unable to load nomination details"
          breadcrumbs={[
            { label: 'Training', to: '/admin/hris/training' },
            { label: 'Nominations' },
          ]}
        />
        <ErrorState
          error={programQuery.error ?? nominationsQuery.error}
          onRetry={() => {
            void programQuery.refetch();
            void nominationsQuery.refetch();
          }}
        />
      </div>
    );
  }

  if (!program) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Training Nominations"
          subtitle="Program details unavailable"
          breadcrumbs={[
            { label: 'Training', to: '/admin/hris/training' },
            { label: 'Nominations' },
          ]}
        />
        <EmptyState
          title="Training program not found"
          subtitle="The selected training program is not available."
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Training Nominations"
        subtitle={program.title}
        breadcrumbs={[{ label: 'Training', to: '/admin/hris/training' }, { label: 'Nominations' }]}
        actions={
          <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
            <DialogTrigger asChild>
              <Button disabled={availableSlots <= 0}>
                <UserPlus className="mr-2 h-4 w-4" />
                Add Nominations
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Add Nominations</DialogTitle>
                <DialogDescription>
                  Select active employees to nominate for this training program.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    value={employeeSearch}
                    onChange={(event) => setEmployeeSearch(event.target.value)}
                    placeholder="Search employees..."
                    className="pl-10"
                  />
                </div>
                {availableEmployeesQuery.isError ? (
                  <ErrorState
                    error={availableEmployeesQuery.error}
                    onRetry={() => void availableEmployeesQuery.refetch()}
                  />
                ) : (
                  <div className="max-h-[320px] overflow-y-auto rounded-lg border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-[50px]" />
                          <TableHead>Employee</TableHead>
                          <TableHead>Department</TableHead>
                          <TableHead>Designation</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {availableEmployees.map((employee) => (
                          <TableRow key={employee.id}>
                            <TableCell>
                              <Checkbox
                                checked={selectedEmployees.includes(employee.id)}
                                onCheckedChange={(checked) => {
                                  if (checked) {
                                    setSelectedEmployees((current) => [...current, employee.id]);
                                  } else {
                                    setSelectedEmployees((current) =>
                                      current.filter((value) => value !== employee.id),
                                    );
                                  }
                                }}
                                disabled={
                                  selectedEmployees.length >= availableSlots &&
                                  !selectedEmployees.includes(employee.id)
                                }
                              />
                            </TableCell>
                            <TableCell>
                              <div>
                                <div className="font-medium">{employee.fullName}</div>
                                <div className="text-xs text-muted-foreground">
                                  {employee.employeeCode}
                                </div>
                              </div>
                            </TableCell>
                            <TableCell>{employee.department}</TableCell>
                            <TableCell>{employee.designation}</TableCell>
                          </TableRow>
                        ))}
                        {!availableEmployeesQuery.isLoading && availableEmployees.length === 0 ? (
                          <TableRow>
                            <TableCell
                              colSpan={4}
                              className="py-8 text-center text-muted-foreground"
                            >
                              No more employees are available for nomination.
                            </TableCell>
                          </TableRow>
                        ) : null}
                      </TableBody>
                    </Table>
                  </div>
                )}
                <p className="text-sm text-muted-foreground">
                  {selectedEmployees.length} selected • {availableSlots} slots available
                </p>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowAddDialog(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={() => void handleAddNominations()}
                  disabled={selectedEmployees.length === 0 || addNominations.isPending}
                >
                  {addNominations.isPending
                    ? 'Adding...'
                    : `Add ${selectedEmployees.length} Nominations`}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        }
      />

      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-6">
            <div>
              <p className="text-xs text-muted-foreground">Program Code</p>
              <p className="font-medium">{program.programCode}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Start Date</p>
              <p className="font-medium">{formatDate(program.startDate)}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Duration</p>
              <p className="font-medium">{program.durationHours} hours</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Location</p>
              <p className="font-medium">{program.location}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Trainer</p>
              <p className="font-medium">{program.trainerName}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Capacity</p>
              <p className="font-medium">
                {enrolledCount}/{program.maxParticipants}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {availableSlots <= 3 && (
        <Alert variant={availableSlots === 0 ? 'destructive' : 'default'}>
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>{availableSlots === 0 ? 'Training Full' : 'Limited Slots Left'}</AlertTitle>
          <AlertDescription>
            {availableSlots === 0
              ? 'Maximum capacity reached. No more nominations can be added.'
              : `Only ${availableSlots} slots remain for this program.`}
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Nominations
          </CardTitle>
          <CardDescription>{filteredNominations.length} nominations</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-4">
            <div className="relative min-w-[220px] flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Search nominations..."
                className="pl-10"
              />
            </div>
            <Select
              value={statusFilter}
              onValueChange={(value) => setStatusFilter(value as typeof statusFilter)}
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="NOMINATED">Nominated</SelectItem>
                <SelectItem value="CONFIRMED">Confirmed</SelectItem>
                <SelectItem value="ATTENDED">Attended</SelectItem>
                <SelectItem value="NO_SHOW">No Show</SelectItem>
                <SelectItem value="CANCELLED">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {filteredNominations.length === 0 ? (
            <EmptyState
              title="No nominations found"
              subtitle="Nominate employees to track attendance and collect feedback."
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead>Nominated By</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredNominations.map((nomination) => (
                  <TableRow key={nomination.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{nomination.employeeName}</div>
                        <div className="text-xs text-muted-foreground">
                          {nomination.employeeCode} • {nomination.designation}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>{nomination.department}</TableCell>
                    <TableCell>{nomination.nominatedBy ?? '-'}</TableCell>
                    <TableCell>{formatDate(nomination.nominatedOn)}</TableCell>
                    <TableCell>{getStatusBadge(nomination.status)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        {nomination.status === 'NOMINATED' ? (
                          <>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => void handleStatusChange(nomination.id, 'CONFIRMED')}
                            >
                              <CheckCircle className="mr-1 h-4 w-4" />
                              Confirm
                            </Button>
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => void handleStatusChange(nomination.id, 'CANCELLED')}
                            >
                              <XCircle className="mr-1 h-4 w-4" />
                              Cancel
                            </Button>
                          </>
                        ) : null}
                        {nomination.status === 'CONFIRMED' ? (
                          <>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() =>
                                void handleStatusChange(nomination.id, 'ATTENDED', true)
                              }
                            >
                              Mark Attended
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() =>
                                void handleStatusChange(nomination.id, 'NO_SHOW', false)
                              }
                            >
                              No Show
                            </Button>
                          </>
                        ) : null}
                        {nomination.status === 'ATTENDED' ? (
                          <Badge variant="default">Attendance marked</Badge>
                        ) : null}
                        {nomination.status === 'NO_SHOW' ? (
                          <Badge variant="destructive">Absent</Badge>
                        ) : null}
                        {nomination.status === 'CANCELLED' ? (
                          <Badge variant="outline">Closed</Badge>
                        ) : null}
                      </div>
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
