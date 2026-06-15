import { CalendarDays, FileText, Plus, XCircle } from 'lucide-react';
import { useMemo, useState } from 'react';

import { DataTable, type Column } from '@/components/common/DataTable';
import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { StatusPill } from '@/components/common/StatusPill';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import {
  useCancelLeaveApplication,
  useCreateLeaveApplication,
  useEssLeaveSummary,
} from '@/hooks/ess/useEssOperations';
import { useToast } from '@/hooks/use-toast';
import type { ESSLeaveApplication } from '@/services/essApi';

function currentYear() {
  return new Date().getFullYear();
}

function days(value: number | string) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric.toFixed(numeric % 1 === 0 ? 0 : 1) : '0';
}

export default function ESSLeave() {
  const { toast } = useToast();
  const [year] = useState(currentYear());
  const [dialogOpen, setDialogOpen] = useState(false);
  const [leaveTypeId, setLeaveTypeId] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [isHalfDay, setIsHalfDay] = useState(false);
  const [halfDayType, setHalfDayType] = useState('FIRST_HALF');
  const [reason, setReason] = useState('');
  const [contactNumber, setContactNumber] = useState('');
  const [contactAddress, setContactAddress] = useState('');
  const [cancelTarget, setCancelTarget] = useState<ESSLeaveApplication | null>(null);
  const [cancelReason, setCancelReason] = useState('');

  const summaryQuery = useEssLeaveSummary(year);
  const createLeaveMutation = useCreateLeaveApplication();
  const cancelLeaveMutation = useCancelLeaveApplication();

  const leaveTypes = useMemo(() => summaryQuery.data?.leaveTypes ?? [], [summaryQuery.data]);
  const applications = summaryQuery.data?.applications ?? [];
  const balances = summaryQuery.data?.balances ?? [];

  const selectedLeaveType = useMemo(
    () => leaveTypes.find((item) => item.id === leaveTypeId),
    [leaveTypeId, leaveTypes],
  );

  const resetForm = () => {
    setLeaveTypeId('');
    setFromDate('');
    setToDate('');
    setIsHalfDay(false);
    setHalfDayType('FIRST_HALF');
    setReason('');
    setContactNumber('');
    setContactAddress('');
  };

  const handleCreate = async () => {
    try {
      await createLeaveMutation.mutateAsync({
        leaveTypeId,
        fromDate,
        toDate,
        isHalfDay,
        halfDayType: isHalfDay ? halfDayType : undefined,
        reason,
        contactNumber: contactNumber || undefined,
        contactAddress: contactAddress || undefined,
      });
      toast({ title: 'Leave application submitted' });
      setDialogOpen(false);
      resetForm();
    } catch (error) {
      toast({
        title: 'Unable to submit leave',
        description: error instanceof Error ? error.message : 'Please review the form and try again.',
        variant: 'destructive',
      });
    }
  };

  const handleCancel = async () => {
    if (!cancelTarget) return;
    try {
      await cancelLeaveMutation.mutateAsync({ application: cancelTarget, reason: cancelReason });
      toast({ title: 'Leave application cancelled' });
      setCancelTarget(null);
      setCancelReason('');
    } catch (error) {
      toast({
        title: 'Unable to cancel leave',
        description: error instanceof Error ? error.message : 'Please try again.',
        variant: 'destructive',
      });
    }
  };

  const columns: Column<ESSLeaveApplication>[] = [
    { key: 'applicationNumber', header: 'Application #' },
    { key: 'leaveTypeName', header: 'Leave Type' },
    {
      key: 'fromDate',
      header: 'From',
      render: (row) => <DateDisplay date={row.fromDate} />,
      sortable: true,
      sortValue: (row) => row.fromDate,
    },
    {
      key: 'toDate',
      header: 'To',
      render: (row) => <DateDisplay date={row.toDate} />,
      sortable: true,
      sortValue: (row) => row.toDate,
    },
    {
      key: 'workingDays',
      header: 'Days',
      align: 'right',
      render: (row) => days(row.workingDays),
      sortable: true,
      sortValue: (row) => Number(row.workingDays),
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => <StatusPill type="application" status={row.status} />,
    },
    {
      key: 'id',
      header: '',
      align: 'right',
      render: (row) =>
        ['PENDING', 'APPROVED'].includes(row.status) ? (
          <Button variant="ghost" size="sm" onClick={() => setCancelTarget(row)}>
            <XCircle className="mr-2 h-4 w-4" />
            Cancel
          </Button>
        ) : null,
    },
  ];

  const canSubmit =
    leaveTypeId && fromDate && toDate && reason.trim().length >= 10 && !createLeaveMutation.isPending;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Leave"
        subtitle="Review balances, apply for leave, and track approval status."
        actions={
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Apply Leave
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Apply for leave</DialogTitle>
                <DialogDescription>
                  Your manager or HR team will review this request in HRMS.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2 md:col-span-2">
                  <Label>Leave Type</Label>
                  <Select value={leaveTypeId} onValueChange={setLeaveTypeId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select leave type" />
                    </SelectTrigger>
                    <SelectContent>
                      {leaveTypes.map((type) => (
                        <SelectItem key={type.id} value={type.id}>
                          {type.name} ({days(type.availableBalance)} available)
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {selectedLeaveType?.documentRequired && (
                    <p className="text-xs text-muted-foreground">
                      Supporting document is required
                      {selectedLeaveType.documentRequiredAfterDays
                        ? ` after ${selectedLeaveType.documentRequiredAfterDays} days`
                        : ''}
                      .
                    </p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="leaveFromDate">From Date</Label>
                  <Input
                    id="leaveFromDate"
                    type="date"
                    value={fromDate}
                    onChange={(event) => setFromDate(event.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="leaveToDate">To Date</Label>
                  <Input
                    id="leaveToDate"
                    type="date"
                    value={toDate}
                    onChange={(event) => setToDate(event.target.value)}
                  />
                </div>
                <div className="flex items-center gap-3">
                  <Switch checked={isHalfDay} onCheckedChange={setIsHalfDay} />
                  <Label>Half day</Label>
                </div>
                {isHalfDay && (
                  <div className="space-y-2">
                    <Label>Half Day Type</Label>
                    <Select value={halfDayType} onValueChange={setHalfDayType}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="FIRST_HALF">First half</SelectItem>
                        <SelectItem value="SECOND_HALF">Second half</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                )}
                <div className="space-y-2">
                  <Label htmlFor="leaveContact">Contact Number</Label>
                  <Input
                    id="leaveContact"
                    value={contactNumber}
                    onChange={(event) => setContactNumber(event.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="leaveContactAddress">Contact Address</Label>
                  <Input
                    id="leaveContactAddress"
                    value={contactAddress}
                    onChange={(event) => setContactAddress(event.target.value)}
                  />
                </div>
                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="leaveReason">Reason</Label>
                  <Textarea
                    id="leaveReason"
                    value={reason}
                    onChange={(event) => setReason(event.target.value)}
                  />
                </div>
              </div>
              <div className="flex justify-end gap-3">
                <Button variant="outline" onClick={() => setDialogOpen(false)}>
                  Close
                </Button>
                <Button onClick={() => void handleCreate()} disabled={!canSubmit}>
                  {createLeaveMutation.isPending ? 'Submitting...' : 'Submit Leave'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Pending Requests</p>
            <p className="mt-2 text-3xl font-semibold">{summaryQuery.data?.pendingCount ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Approved This Year</p>
            <p className="mt-2 text-3xl font-semibold">
              {days(summaryQuery.data?.approvedThisYear ?? 0)}
            </p>
          </CardContent>
        </Card>
        <Card className="md:col-span-2">
          <CardContent className="flex items-center gap-3 pt-6">
            <CalendarDays className="h-8 w-8 text-primary" />
            <div>
              <p className="text-sm text-muted-foreground">Leave year</p>
              <p className="text-xl font-semibold">{year}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {balances.map((balance) => (
          <Card key={balance.leaveTypeId}>
            <CardContent className="pt-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-medium">{balance.name}</p>
                  <p className="text-xs text-muted-foreground">{balance.code}</p>
                </div>
                <FileText className="h-5 w-5 text-muted-foreground" />
              </div>
              <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-muted-foreground">Available</p>
                  <p className="text-lg font-semibold">{days(balance.availableBalance)}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Used</p>
                  <p className="text-lg font-semibold">{days(balance.used)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <DataTable
        data={applications}
        columns={columns}
        getRowId={(row) => row.id}
        isLoading={summaryQuery.isLoading}
        error={summaryQuery.error}
        onRetry={() => void summaryQuery.refetch()}
        emptyTitle="No leave applications"
        emptySubtitle="Apply for leave to track approval status here."
      />

      <Dialog open={Boolean(cancelTarget)} onOpenChange={(open) => !open && setCancelTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Cancel leave application</DialogTitle>
            <DialogDescription>
              This will send the cancellation through the HRMS leave workflow.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="cancelReason">Cancellation Reason</Label>
            <Textarea
              id="cancelReason"
              value={cancelReason}
              onChange={(event) => setCancelReason(event.target.value)}
            />
          </div>
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => setCancelTarget(null)}>
              Close
            </Button>
            <Button
              variant="destructive"
              onClick={() => void handleCancel()}
              disabled={cancelReason.trim().length < 10 || cancelLeaveMutation.isPending}
            >
              {cancelLeaveMutation.isPending ? 'Cancelling...' : 'Cancel Leave'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
