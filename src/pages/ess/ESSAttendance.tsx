import { useMemo, useState } from 'react';

import { DataTable, type Column } from '@/components/common/DataTable';
import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { StatusPill } from '@/components/common/StatusPill';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
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
import { Textarea } from '@/components/ui/textarea';
import {
  useAttendanceRecords,
  useAttendanceSummary,
  useCreateRegularization,
  useRegularizationTypes,
  useRegularizations,
} from '@/hooks/ess/useEssOperations';
import type { AttendanceRecordRow, AttendanceRegularizationRow } from '@/services/essApi';

function currentMonthString() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
}

function monthBounds(month: string) {
  const [year, monthIndex] = month.split('-').map(Number);
  const start = new Date(year, monthIndex - 1, 1);
  const end = new Date(year, monthIndex, 0);
  return {
    fromDate: start.toISOString().slice(0, 10),
    toDate: end.toISOString().slice(0, 10),
  };
}

function AttendanceMetric({
  title,
  value,
  subtitle,
}: {
  title: string;
  value: string | number;
  subtitle: string;
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <p className="text-sm text-muted-foreground">{title}</p>
        <p className="mt-2 text-3xl font-semibold">{value}</p>
        <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>
      </CardContent>
    </Card>
  );
}

export default function ESSAttendance() {
  const [month, setMonth] = useState(currentMonthString());
  const [showRegularizationDialog, setShowRegularizationDialog] = useState(false);
  const [attendanceDate, setAttendanceDate] = useState('');
  const [requestType, setRequestType] = useState('');
  const [requestedInTime, setRequestedInTime] = useState('');
  const [requestedOutTime, setRequestedOutTime] = useState('');
  const [reason, setReason] = useState('');

  const bounds = useMemo(() => monthBounds(month), [month]);
  const summaryQuery = useAttendanceSummary(month);
  const recordsQuery = useAttendanceRecords(bounds.fromDate, bounds.toDate);
  const regularizationTypesQuery = useRegularizationTypes();
  const regularizationsQuery = useRegularizations({
    fromDate: bounds.fromDate,
    toDate: bounds.toDate,
    limit: 20,
    offset: 0,
  });
  const createRegularizationMutation = useCreateRegularization();
  const attendanceRecords = recordsQuery.data?.items ?? [];

  const attendanceColumns: Column<AttendanceRecordRow>[] = [
    {
      key: 'date',
      header: 'Date',
      render: (row) => <DateDisplay date={row.date} />,
      sortable: true,
      sortValue: (row) => row.date,
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => <StatusPill type="application" status={row.status} />,
    },
    { key: 'inTime', header: 'First In' },
    { key: 'outTime', header: 'Last Out' },
    {
      key: 'workingHours',
      header: 'Hours',
      align: 'right',
      render: (row) => row.workingHours.toFixed(2),
      sortable: true,
      sortValue: (row) => row.workingHours,
    },
  ];

  const regularizationColumns: Column<AttendanceRegularizationRow>[] = [
    { key: 'id', header: 'Request #', render: (row) => row.id.slice(0, 8).toUpperCase() },
    {
      key: 'attendanceDate',
      header: 'Attendance Date',
      render: (row) => <DateDisplay date={row.attendanceDate} />,
      sortable: true,
      sortValue: (row) => row.attendanceDate,
    },
    {
      key: 'requestType',
      header: 'Type',
      render: (row) =>
        regularizationTypesQuery.data?.find((item) => item.code === row.requestType)?.label ??
        row.requestType,
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => <StatusPill type="application" status={row.status} />,
    },
    { key: 'reason', header: 'Reason' },
  ];

  const handleCreateRegularization = async () => {
    await createRegularizationMutation.mutateAsync({
      attendanceDate,
      requestType,
      requestedFirstIn: requestedInTime || undefined,
      requestedLastOut: requestedOutTime || undefined,
      reason,
    });
    setShowRegularizationDialog(false);
    setAttendanceDate('');
    setRequestedInTime('');
    setRequestedOutTime('');
    setReason('');
    void regularizationsQuery.refetch();
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Attendance"
        subtitle="Review attendance records for the selected month and raise regularization requests."
        actions={
          <div className="flex items-center gap-2">
            <Input
              type="month"
              value={month}
              onChange={(event) => setMonth(event.target.value)}
              className="w-[180px]"
            />
            <Dialog open={showRegularizationDialog} onOpenChange={setShowRegularizationDialog}>
              <DialogTrigger asChild>
                <Button>Raise Regularization</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Attendance Regularization</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="attendanceDate">Attendance Date</Label>
                    <Input
                      id="attendanceDate"
                      type="date"
                      value={attendanceDate}
                      onChange={(event) => setAttendanceDate(event.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="regularizationType">Regularization Type</Label>
                    <Select value={requestType} onValueChange={setRequestType}>
                      <SelectTrigger id="regularizationType">
                        <SelectValue placeholder="Select request type" />
                      </SelectTrigger>
                      <SelectContent>
                        {(regularizationTypesQuery.data ?? []).map((item) => (
                          <SelectItem key={item.code} value={item.code}>
                            {item.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="requestedInTime">Requested In Time</Label>
                      <Input
                        id="requestedInTime"
                        type="time"
                        value={requestedInTime}
                        onChange={(event) => setRequestedInTime(event.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="requestedOutTime">Requested Out Time</Label>
                      <Input
                        id="requestedOutTime"
                        type="time"
                        value={requestedOutTime}
                        onChange={(event) => setRequestedOutTime(event.target.value)}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="regularizationReason">Reason</Label>
                    <Textarea
                      id="regularizationReason"
                      value={reason}
                      onChange={(event) => setReason(event.target.value)}
                    />
                  </div>
                  <div className="flex justify-end">
                    <Button
                      onClick={() => void handleCreateRegularization()}
                      disabled={
                        !attendanceDate ||
                        !requestType ||
                        reason.trim().length === 0 ||
                        createRegularizationMutation.isPending
                      }
                    >
                      {createRegularizationMutation.isPending ? 'Submitting…' : 'Submit Request'}
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <AttendanceMetric
          title="Working Days"
          value={summaryQuery.data?.workingDays ?? 0}
          subtitle={`Month ${month}`}
        />
        <AttendanceMetric
          title="Present"
          value={summaryQuery.data?.present ?? 0}
          subtitle={`${summaryQuery.data?.workFromHome ?? 0} WFH days`}
        />
        <AttendanceMetric
          title="Absent"
          value={summaryQuery.data?.absent ?? 0}
          subtitle={`${summaryQuery.data?.halfDay ?? 0} half-days`}
        />
        <AttendanceMetric
          title="Leave & Holidays"
          value={(summaryQuery.data?.leave ?? 0) + (summaryQuery.data?.holiday ?? 0)}
          subtitle={`${summaryQuery.data?.leave ?? 0} leave · ${summaryQuery.data?.holiday ?? 0} holidays`}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Attendance Records</CardTitle>
          </CardHeader>
          <CardContent>
          <DataTable
              data={attendanceRecords}
              columns={attendanceColumns}
              getRowId={(row) => `${row.date}-${row.status}`}
              isLoading={recordsQuery.isLoading}
              error={recordsQuery.error}
              onRetry={() => void recordsQuery.refetch()}
              emptyTitle="No attendance records"
              emptySubtitle="Attendance for the selected month will appear here."
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Regularization Requests</CardTitle>
          </CardHeader>
          <CardContent>
            <DataTable
              data={regularizationsQuery.data ?? []}
              columns={regularizationColumns}
              getRowId={(row) => row.id}
              isLoading={regularizationsQuery.isLoading}
              error={regularizationsQuery.error}
              onRetry={() => void regularizationsQuery.refetch()}
              emptyTitle="No regularization requests"
              emptySubtitle="Requests raised for the selected month will appear here."
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
