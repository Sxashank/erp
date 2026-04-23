import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Search,
  Plus,
  CheckCircle,
  XCircle,
  Clock,
  Users,
  UserPlus,
  Calendar,
  GraduationCap,
  Send,
  Trash2,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { formatDate } from '@/lib/utils';

type NominationStatus = 'NOMINATED' | 'CONFIRMED' | 'ATTENDED' | 'NO_SHOW' | 'CANCELLED';

interface Nomination {
  id: string;
  employee_id: string;
  employee_code: string;
  employee_name: string;
  department: string;
  designation: string;
  nominated_by: string;
  nominated_on: string;
  status: NominationStatus;
  attendance_marked: boolean;
}

interface AvailableEmployee {
  id: string;
  employee_code: string;
  full_name: string;
  department: string;
  designation: string;
  email: string;
}

// Mock program data
const programDetails = {
  id: '1',
  program_code: 'TRN-2024-001',
  title: 'Leadership Excellence Program',
  start_date: '2025-01-15',
  end_date: '2025-01-17',
  duration_hours: 24,
  location: 'Training Center - Mumbai',
  max_participants: 25,
  trainer_name: 'Dr. Anand Verma',
};

// Mock nominations
const nominations: Nomination[] = [
  {
    id: '1',
    employee_id: 'emp-001',
    employee_code: 'EMP001',
    employee_name: 'Rahul Sharma',
    department: 'Engineering',
    designation: 'Team Lead',
    nominated_by: 'HR Admin',
    nominated_on: '2024-12-20',
    status: 'CONFIRMED',
    attendance_marked: false,
  },
  {
    id: '2',
    employee_id: 'emp-002',
    employee_code: 'EMP002',
    employee_name: 'Priya Patel',
    department: 'Finance',
    designation: 'Senior Accountant',
    nominated_by: 'Manager',
    nominated_on: '2024-12-21',
    status: 'NOMINATED',
    attendance_marked: false,
  },
  {
    id: '3',
    employee_id: 'emp-003',
    employee_code: 'EMP003',
    employee_name: 'Amit Kumar',
    department: 'Operations',
    designation: 'Assistant Manager',
    nominated_by: 'Self',
    nominated_on: '2024-12-22',
    status: 'CONFIRMED',
    attendance_marked: false,
  },
];

// Mock available employees
const availableEmployees: AvailableEmployee[] = [
  { id: 'emp-004', employee_code: 'EMP004', full_name: 'Sneha Reddy', department: 'HR', designation: 'Executive', email: 'sneha@company.com' },
  { id: 'emp-005', employee_code: 'EMP005', full_name: 'Vikram Singh', department: 'Sales', designation: 'Manager', email: 'vikram@company.com' },
  { id: 'emp-006', employee_code: 'EMP006', full_name: 'Anita Desai', department: 'Marketing', designation: 'Lead', email: 'anita@company.com' },
  { id: 'emp-007', employee_code: 'EMP007', full_name: 'Rajesh Gupta', department: 'IT', designation: 'Architect', email: 'rajesh@company.com' },
];

const getStatusBadge = (status: NominationStatus) => {
  const config: Record<NominationStatus, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; label: string }> = {
    NOMINATED: { variant: 'outline', label: 'Nominated' },
    CONFIRMED: { variant: 'secondary', label: 'Confirmed' },
    ATTENDED: { variant: 'default', label: 'Attended' },
    NO_SHOW: { variant: 'destructive', label: 'No Show' },
    CANCELLED: { variant: 'destructive', label: 'Cancelled' },
  };
  const cfg = config[status];
  return <Badge variant={cfg.variant}>{cfg.label}</Badge>;
};

export default function TrainingNomination() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [nominationList, setNominationList] = useState(nominations);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [selectedEmployees, setSelectedEmployees] = useState<string[]>([]);
  const [employeeSearch, setEmployeeSearch] = useState('');

  const filteredNominations = nominationList.filter((n) => {
    const matchesSearch =
      n.employee_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      n.employee_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      n.department.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || n.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const filteredEmployees = availableEmployees.filter(
    (e) =>
      e.full_name.toLowerCase().includes(employeeSearch.toLowerCase()) ||
      e.employee_code.toLowerCase().includes(employeeSearch.toLowerCase()) ||
      e.department.toLowerCase().includes(employeeSearch.toLowerCase())
  );

  const handleConfirmNomination = (nominationId: string) => {
    setNominationList(
      nominationList.map((n) =>
        n.id === nominationId ? { ...n, status: 'CONFIRMED' as NominationStatus } : n
      )
    );
  };

  const handleCancelNomination = (nominationId: string) => {
    setNominationList(
      nominationList.map((n) =>
        n.id === nominationId ? { ...n, status: 'CANCELLED' as NominationStatus } : n
      )
    );
  };

  const handleAddNominations = () => {
    const newNominations = selectedEmployees.map((empId) => {
      const emp = availableEmployees.find((e) => e.id === empId)!;
      return {
        id: `new-${empId}`,
        employee_id: emp.id,
        employee_code: emp.employee_code,
        employee_name: emp.full_name,
        department: emp.department,
        designation: emp.designation,
        nominated_by: 'HR Admin',
        nominated_on: new Date().toISOString().split('T')[0],
        status: 'NOMINATED' as NominationStatus,
        attendance_marked: false,
      };
    });
    setNominationList([...nominationList, ...newNominations]);
    setSelectedEmployees([]);
    setShowAddDialog(false);
  };

  const handleSendReminders = () => {
    // API call to send reminder emails
    alert('Reminders sent to all confirmed participants');
  };

  const enrolledCount = nominationList.filter(
    (n) => n.status === 'CONFIRMED' || n.status === 'NOMINATED'
  ).length;
  const availableSlots = programDetails.max_participants - enrolledCount;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Training Nominations"
        subtitle={programDetails.title}
        breadcrumbs={[
          { label: 'Training', to: '/admin/hris/training' },
          { label: 'Nominations' },
        ]}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleSendReminders}>
              <Send className="h-4 w-4 mr-2" />
              Send Reminders
            </Button>
            <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
            <DialogTrigger asChild>
              <Button disabled={availableSlots <= 0}>
                <UserPlus className="h-4 w-4 mr-2" />
                Add Nominations
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Add Nominations</DialogTitle>
                <DialogDescription>
                  Select employees to nominate for this training program
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search employees..."
                    className="pl-10"
                    value={employeeSearch}
                    onChange={(e) => setEmployeeSearch(e.target.value)}
                  />
                </div>
                <div className="border rounded-lg max-h-[300px] overflow-y-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-[50px]"></TableHead>
                        <TableHead>Employee</TableHead>
                        <TableHead>Department</TableHead>
                        <TableHead>Designation</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredEmployees.map((emp) => (
                        <TableRow key={emp.id}>
                          <TableCell>
                            <Checkbox
                              checked={selectedEmployees.includes(emp.id)}
                              onCheckedChange={(checked) => {
                                if (checked) {
                                  setSelectedEmployees([...selectedEmployees, emp.id]);
                                } else {
                                  setSelectedEmployees(
                                    selectedEmployees.filter((id) => id !== emp.id)
                                  );
                                }
                              }}
                              disabled={selectedEmployees.length >= availableSlots && !selectedEmployees.includes(emp.id)}
                            />
                          </TableCell>
                          <TableCell>
                            <div>
                              <div className="font-medium">{emp.full_name}</div>
                              <div className="text-xs text-muted-foreground">
                                {emp.employee_code}
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>{emp.department}</TableCell>
                          <TableCell>{emp.designation}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
                <p className="text-sm text-muted-foreground">
                  {selectedEmployees.length} selected | {availableSlots} slots available
                </p>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowAddDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={handleAddNominations} disabled={selectedEmployees.length === 0}>
                  Add {selectedEmployees.length} Nominations
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          </div>
        }
      />

      {/* Program Summary */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
            <div>
              <p className="text-xs text-muted-foreground">Program Code</p>
              <p className="font-medium">{programDetails.program_code}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Start Date</p>
              <p className="font-medium">{formatDate(programDetails.start_date)}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Duration</p>
              <p className="font-medium">{programDetails.duration_hours} hours</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Location</p>
              <p className="font-medium">{programDetails.location}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Trainer</p>
              <p className="font-medium">{programDetails.trainer_name}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Capacity</p>
              <p className="font-medium">
                {enrolledCount}/{programDetails.max_participants}
                <span className="text-green-600 ml-2">({availableSlots} available)</span>
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Alerts */}
      {availableSlots <= 5 && availableSlots > 0 && (
        <Alert>
          <Clock className="h-4 w-4" />
          <AlertTitle>Limited Slots Available</AlertTitle>
          <AlertDescription>
            Only {availableSlots} slots remaining. Please finalize nominations soon.
          </AlertDescription>
        </Alert>
      )}

      {availableSlots === 0 && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertTitle>Training Full</AlertTitle>
          <AlertDescription>
            Maximum capacity reached. No more nominations can be added.
          </AlertDescription>
        </Alert>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4 flex-wrap">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by name, code, or department..."
                className="pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="NOMINATED">Nominated</SelectItem>
                <SelectItem value="CONFIRMED">Confirmed</SelectItem>
                <SelectItem value="CANCELLED">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Nominations Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Nominations
          </CardTitle>
          <CardDescription>{filteredNominations.length} nominations</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Employee</TableHead>
                <TableHead>Department</TableHead>
                <TableHead>Designation</TableHead>
                <TableHead>Nominated By</TableHead>
                <TableHead>Nominated On</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredNominations.map((nom) => (
                <TableRow key={nom.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{nom.employee_name}</div>
                      <div className="text-xs text-muted-foreground">{nom.employee_code}</div>
                    </div>
                  </TableCell>
                  <TableCell>{nom.department}</TableCell>
                  <TableCell>{nom.designation}</TableCell>
                  <TableCell>{nom.nominated_by}</TableCell>
                  <TableCell>{formatDate(nom.nominated_on)}</TableCell>
                  <TableCell>{getStatusBadge(nom.status)}</TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      {nom.status === 'NOMINATED' && (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleConfirmNomination(nom.id)}
                          >
                            <CheckCircle className="h-4 w-4 mr-1" />
                            Confirm
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-red-600"
                            onClick={() => handleCancelNomination(nom.id)}
                          >
                            <XCircle className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                      {nom.status === 'CONFIRMED' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-600"
                          onClick={() => handleCancelNomination(nom.id)}
                        >
                          <Trash2 className="h-4 w-4 mr-1" />
                          Cancel
                        </Button>
                      )}
                    </div>
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
