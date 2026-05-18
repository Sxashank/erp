import {
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  Eye,
  Phone,
  Mail,
  Calendar,
  CheckCircle,
  MessageSquare,
  FileWarning,
  Loader2,
} from 'lucide-react';
import { useState } from 'react';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
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
import {
  useFollowUps,
  type FollowUpListItem,
  type FollowUpStatusValue,
  type FollowUpTypeValue,
  type FollowUpFilters,
} from '@/hooks/lending/useFollowUps';

const followUpTypeConfig: Record<
  FollowUpTypeValue,
  { label: string; icon: React.ReactNode; color: string }
> = {
  CALL: { label: 'Call', icon: <Phone className="h-3 w-3" />, color: 'bg-blue-100 text-blue-700' },
  VISIT: {
    label: 'Visit',
    icon: <Calendar className="h-3 w-3" />,
    color: 'bg-purple-100 text-purple-700',
  },
  EMAIL: {
    label: 'Email',
    icon: <Mail className="h-3 w-3" />,
    color: 'bg-green-100 text-green-700',
  },
  SMS: {
    label: 'SMS',
    icon: <MessageSquare className="h-3 w-3" />,
    color: 'bg-teal-100 text-teal-700',
  },
  LETTER: {
    label: 'Letter',
    icon: <Mail className="h-3 w-3" />,
    color: 'bg-orange-100 text-orange-700',
  },
  LEGAL_NOTICE: {
    label: 'Legal Notice',
    icon: <FileWarning className="h-3 w-3" />,
    color: 'bg-red-100 text-red-700',
  },
  OTHER: { label: 'Other', icon: <Mail className="h-3 w-3" />, color: 'bg-gray-100 text-gray-700' },
};

const statusConfig: Record<FollowUpStatusValue, { label: string; color: string }> = {
  SCHEDULED: { label: 'Scheduled', color: 'bg-yellow-100 text-yellow-700' },
  COMPLETED: { label: 'Completed', color: 'bg-green-100 text-green-700' },
  CANCELLED: { label: 'Cancelled', color: 'bg-gray-200 text-gray-700' },
  RESCHEDULED: { label: 'Rescheduled', color: 'bg-blue-100 text-blue-700' },
  NO_RESPONSE: { label: 'No Response', color: 'bg-orange-100 text-orange-700' },
  PTP_RECEIVED: { label: 'Promise to Pay', color: 'bg-emerald-100 text-emerald-700' },
};

export default function FollowUpList() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');

  const filters: FollowUpFilters = {
    pageSize: 100,
    ...(statusFilter !== 'ALL' && { status: statusFilter as FollowUpStatusValue }),
  };
  const { data, isLoading, isError, error, refetch } = useFollowUps(filters);

  const all: FollowUpListItem[] = data?.items ?? [];
  const followUps = all.filter((f) => {
    if (typeFilter !== 'ALL' && f.followUpType !== typeFilter) return false;
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      (f.loanAccountNumber ?? '').toLowerCase().includes(q) ||
      (f.entityName ?? '').toLowerCase().includes(q) ||
      (f.contactPerson ?? '').toLowerCase().includes(q)
    );
  });

  const scheduledCount = followUps.filter((f) => f.status === 'SCHEDULED').length;
  const ptpCount = followUps.filter((f) => f.status === 'PTP_RECEIVED').length;
  const completedCount = followUps.filter((f) => f.status === 'COMPLETED').length;

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

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Follow-ups</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.total ?? followUps.length}</div>
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Scheduled</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600">{scheduledCount}</div>
            <p className="text-xs text-muted-foreground">Requires action</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Promises to Pay</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600">{ptpCount}</div>
            <p className="text-xs text-muted-foreground">Pending PTP follow-through</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{completedCount}</div>
            <p className="text-xs text-muted-foreground">Closed contacts</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by account number, entity, or contact..."
                className="pl-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[160px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Status</SelectItem>
                  <SelectItem value="SCHEDULED">Scheduled</SelectItem>
                  <SelectItem value="COMPLETED">Completed</SelectItem>
                  <SelectItem value="CANCELLED">Cancelled</SelectItem>
                  <SelectItem value="RESCHEDULED">Rescheduled</SelectItem>
                  <SelectItem value="NO_RESPONSE">No Response</SelectItem>
                  <SelectItem value="PTP_RECEIVED">Promise to Pay</SelectItem>
                </SelectContent>
              </Select>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Types</SelectItem>
                  <SelectItem value="CALL">Call</SelectItem>
                  <SelectItem value="VISIT">Visit</SelectItem>
                  <SelectItem value="EMAIL">Email</SelectItem>
                  <SelectItem value="SMS">SMS</SelectItem>
                  <SelectItem value="LETTER">Letter</SelectItem>
                  <SelectItem value="LEGAL_NOTICE">Legal Notice</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Account</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Stage</TableHead>
                <TableHead>Scheduled</TableHead>
                <TableHead>Assigned To</TableHead>
                <TableHead>PTP</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8 text-center text-muted-foreground">
                    <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />
                    Loading follow-ups...
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8">
                    <ErrorState
                      title="Could not load follow-ups"
                      error={error}
                      onRetry={() => refetch()}
                    />
                  </TableCell>
                </TableRow>
              ) : followUps.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8 text-center text-muted-foreground">
                    No follow-ups found
                  </TableCell>
                </TableRow>
              ) : (
                followUps.map((f) => {
                  const typeCfg = followUpTypeConfig[f.followUpType] ?? followUpTypeConfig.OTHER;
                  const statusCfg = statusConfig[f.status];
                  return (
                    <TableRow key={f.id} className="cursor-pointer hover:bg-muted/50">
                      <TableCell className="font-mono text-sm">
                        {f.loanAccountNumber ?? '—'}
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">{f.entityName ?? '—'}</div>
                        {f.contactPerson && (
                          <div className="text-xs text-muted-foreground">
                            {f.contactPerson}
                            {f.contactNumber ? ` · ${f.contactNumber}` : ''}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={typeCfg.color}>
                          {typeCfg.icon}
                          <span className="ml-1">{typeCfg.label}</span>
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{f.collectionStage}</Badge>
                      </TableCell>
                      <TableCell>
                        <DateDisplay date={f.scheduledDate} />
                        {f.scheduledTime && (
                          <div className="text-xs text-muted-foreground">{f.scheduledTime}</div>
                        )}
                      </TableCell>
                      <TableCell>{f.assignedToName ?? '—'}</TableCell>
                      <TableCell>
                        {f.ptpDate ? (
                          <div>
                            <DateDisplay date={f.ptpDate} />
                            {f.ptpBroken && <div className="text-xs text-red-600">Broken</div>}
                          </div>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={statusCfg.color}>
                          {statusCfg.label}
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
