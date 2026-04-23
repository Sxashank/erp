import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Filter, MoreHorizontal, Eye, Phone, Mail, Calendar, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { DPDBadge } from '@/components/lending/common/DPDBadge';

interface FollowUp {
  id: string;
  loanAccountNumber: string;
  entityName: string;
  overdueAmount: number;
  dpd: number;
  lastContactDate: string | null;
  nextFollowUpDate: string;
  followUpType: 'CALL' | 'VISIT' | 'EMAIL' | 'NOTICE';
  assignedTo: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'ESCALATED';
  remarks: string | null;
}

// Mock data
const mockFollowUps: FollowUp[] = [
  {
    id: '1',
    loanAccountNumber: 'SMFC/TL/DEL/2023/L00045',
    entityName: 'Metro Industries Pvt Ltd',
    overdueAmount: 45000000,
    dpd: 45,
    lastContactDate: '2025-01-08',
    nextFollowUpDate: '2025-01-14',
    followUpType: 'CALL',
    assignedTo: 'Rajesh Kumar',
    status: 'IN_PROGRESS',
    remarks: 'Promised to pay by 15th Jan',
  },
  {
    id: '2',
    loanAccountNumber: 'SMFC/WC/MUM/2022/L00089',
    entityName: 'Eastern Trading Co',
    overdueAmount: 28500000,
    dpd: 62,
    lastContactDate: '2025-01-05',
    nextFollowUpDate: '2025-01-13',
    followUpType: 'VISIT',
    assignedTo: 'Priya Sharma',
    status: 'PENDING',
    remarks: 'Site visit scheduled',
  },
  {
    id: '3',
    loanAccountNumber: 'SMFC/LAP/CHN/2023/L00123',
    entityName: 'Sunrise Enterprises',
    overdueAmount: 15000000,
    dpd: 28,
    lastContactDate: '2025-01-10',
    nextFollowUpDate: '2025-01-15',
    followUpType: 'EMAIL',
    assignedTo: 'Amit Patel',
    status: 'COMPLETED',
    remarks: 'Payment received partially',
  },
  {
    id: '4',
    loanAccountNumber: 'SMFC/TL/KOL/2021/L00067',
    entityName: 'Western Logistics',
    overdueAmount: 85000000,
    dpd: 85,
    lastContactDate: '2025-01-02',
    nextFollowUpDate: '2025-01-12',
    followUpType: 'NOTICE',
    assignedTo: 'Suresh Verma',
    status: 'ESCALATED',
    remarks: 'Demand notice sent, no response',
  },
];

const followUpTypeConfig: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  CALL: { label: 'Call', icon: <Phone className="h-3 w-3" />, color: 'bg-blue-100 text-blue-700' },
  VISIT: { label: 'Visit', icon: <Calendar className="h-3 w-3" />, color: 'bg-purple-100 text-purple-700' },
  EMAIL: { label: 'Email', icon: <Mail className="h-3 w-3" />, color: 'bg-green-100 text-green-700' },
  NOTICE: { label: 'Notice', icon: <Mail className="h-3 w-3" />, color: 'bg-orange-100 text-orange-700' },
};

const statusConfig: Record<string, { label: string; color: string }> = {
  PENDING: { label: 'Pending', color: 'bg-yellow-100 text-yellow-700' },
  IN_PROGRESS: { label: 'In Progress', color: 'bg-blue-100 text-blue-700' },
  COMPLETED: { label: 'Completed', color: 'bg-green-100 text-green-700' },
  ESCALATED: { label: 'Escalated', color: 'bg-red-100 text-red-700' },
};

export default function FollowUpList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');

  const filteredFollowUps = mockFollowUps.filter((followUp) => {
    const matchesSearch =
      followUp.loanAccountNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
      followUp.entityName.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || followUp.status === statusFilter;
    const matchesType = typeFilter === 'ALL' || followUp.followUpType === typeFilter;
    return matchesSearch && matchesStatus && matchesType;
  });

  const totalOverdue = mockFollowUps.reduce((sum, f) => sum + f.overdueAmount, 0);
  const pendingFollowUps = mockFollowUps.filter((f) => f.status === 'PENDING').length;
  const escalatedCount = mockFollowUps.filter((f) => f.status === 'ESCALATED').length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Collection Follow-ups"
        subtitle="Track and manage overdue collection activities"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Schedule Follow-up
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Overdue</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalOverdue} abbreviated className="text-2xl font-bold text-red-600" />
            <p className="text-xs text-muted-foreground">{mockFollowUps.length} accounts</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Follow-ups</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600">{pendingFollowUps}</div>
            <p className="text-xs text-muted-foreground">Requires action today</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Escalated Cases</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{escalatedCount}</div>
            <p className="text-xs text-muted-foreground">Needs supervisor attention</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Collection Today</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={15000000} abbreviated className="text-2xl font-bold text-green-600" />
            <p className="text-xs text-muted-foreground">From 3 accounts</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by account number or entity..."
                className="pl-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[150px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Status</SelectItem>
                  <SelectItem value="PENDING">Pending</SelectItem>
                  <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
                  <SelectItem value="COMPLETED">Completed</SelectItem>
                  <SelectItem value="ESCALATED">Escalated</SelectItem>
                </SelectContent>
              </Select>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Follow-up Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Types</SelectItem>
                  <SelectItem value="CALL">Call</SelectItem>
                  <SelectItem value="VISIT">Visit</SelectItem>
                  <SelectItem value="EMAIL">Email</SelectItem>
                  <SelectItem value="NOTICE">Notice</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Follow-ups Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Account</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead className="text-right">Overdue</TableHead>
                <TableHead className="text-right">DPD</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Next Follow-up</TableHead>
                <TableHead>Assigned To</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredFollowUps.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                    No follow-ups found matching your criteria
                  </TableCell>
                </TableRow>
              ) : (
                filteredFollowUps.map((followUp) => {
                  const typeConfig = followUpTypeConfig[followUp.followUpType];
                  const status = statusConfig[followUp.status];
                  return (
                    <TableRow
                      key={followUp.id}
                      className="cursor-pointer hover:bg-muted/50"
                    >
                      <TableCell className="font-mono text-sm">
                        {followUp.loanAccountNumber}
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">{followUp.entityName}</div>
                        {followUp.remarks && (
                          <div className="text-xs text-muted-foreground truncate max-w-[200px]">
                            {followUp.remarks}
                          </div>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={followUp.overdueAmount} abbreviated className="text-red-600" />
                      </TableCell>
                      <TableCell className="text-right">
                        <DPDBadge dpd={followUp.dpd} />
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={typeConfig.color}>
                          {typeConfig.icon}
                          <span className="ml-1">{typeConfig.label}</span>
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <DateDisplay date={followUp.nextFollowUpDate} />
                      </TableCell>
                      <TableCell>{followUp.assignedTo}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={status.color}>
                          {status.label}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>
                              <Eye className="mr-2 h-4 w-4" />
                              View Account
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Phone className="mr-2 h-4 w-4" />
                              Log Call
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem>
                              <CheckCircle className="mr-2 h-4 w-4" />
                              Mark Completed
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Calendar className="mr-2 h-4 w-4" />
                              Reschedule
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
