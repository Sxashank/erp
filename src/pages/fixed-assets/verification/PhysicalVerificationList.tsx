import { Eye, Plus } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import {
  AmountDisplay,
  DataTable,
  DateDisplay,
  FilterBar,
  PageHeader,
  type Column,
} from '@/components/common';
import { VerificationProgressCard } from '@/components/fixed-assets/VerificationProgressCard';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useVerificationSchedules, useVerificationSummary } from '@/hooks/fixed-assets/usePhysicalVerification';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import type { VerificationSchedule, VerificationScheduleStatus } from '@/types/fixed-assets';

const statusOptions: { value: VerificationScheduleStatus | 'ALL'; label: string }[] = [
  { value: 'ALL', label: 'All statuses' },
  { value: 'SCHEDULED', label: 'Scheduled' },
  { value: 'IN_PROGRESS', label: 'In progress' },
  { value: 'COMPLETED', label: 'Completed' },
  { value: 'CANCELLED', label: 'Cancelled' },
];

function defaultFinancialYear(): string {
  const now = new Date();
  const startYear = now.getMonth() >= 3 ? now.getFullYear() : now.getFullYear() - 1;
  return `${startYear}-${String((startYear + 1) % 100).padStart(2, '0')}`;
}

export function PhysicalVerificationList(): JSX.Element {
  const organizationId = useRequiredActiveOrganizationId();
  const navigate = useNavigate();
  const [status, setStatus] = useState<VerificationScheduleStatus | 'ALL'>('ALL');
  const [financialYear, setFinancialYear] = useState(defaultFinancialYear());
  const [search, setSearch] = useState('');

  const schedulesQuery = useVerificationSchedules(organizationId, {
    financialYear,
    status: status === 'ALL' ? undefined : status,
    limit: 100,
  });
  const summaryQuery = useVerificationSummary(organizationId, financialYear);

  const schedules = useMemo(() => {
    const items = schedulesQuery.data?.items ?? [];
    const query = search.trim().toLowerCase();
    if (!query) return items;
    return items.filter((schedule) =>
      [schedule.scheduleReference, schedule.scheduleName, schedule.locationName]
        .filter(Boolean)
        .some((value) => value!.toLowerCase().includes(query)),
    );
  }, [schedulesQuery.data?.items, search]);

  const columns: Column<VerificationSchedule>[] = useMemo(
    () => [
      {
        key: 'scheduleReference',
        header: 'Schedule',
        render: (row) => (
          <div>
            <div className="font-medium">{row.scheduleName}</div>
            <div className="text-xs text-muted-foreground">{row.scheduleReference}</div>
          </div>
        ),
      },
      {
        key: 'locationName',
        header: 'Location',
        render: (row) => row.locationName ?? 'All locations',
      },
      {
        key: 'scheduledStartDate',
        header: 'Window',
        render: (row) => (
          <div className="text-sm">
            <div><DateDisplay date={row.scheduledStartDate} /></div>
            <div className="text-muted-foreground"><DateDisplay date={row.scheduledEndDate} /></div>
          </div>
        ),
      },
      {
        key: 'verifiedCount',
        header: 'Progress',
        render: (row) => `${row.verifiedCount}/${row.totalAssets}`,
      },
      {
        key: 'totalValueVerified',
        header: 'Value verified',
        align: 'right',
        render: (row) => <AmountDisplay amount={row.totalValueVerified} compact />,
      },
      {
        key: 'status',
        header: 'Status',
        render: (row) => row.status.replace(/_/g, ' '),
      },
      {
        key: 'actions',
        header: '',
        align: 'right',
        render: (row) => (
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => navigate(`/admin/fixed-assets/verification/${row.id}`)}
          >
            <Eye className="mr-2 h-4 w-4" />
            Open
          </Button>
        ),
      },
    ],
    [navigate],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Physical Verification"
        subtitle="Plan, execute, and close annual or ad hoc verification schedules without mocked data."
        breadcrumbs={[{ label: 'Fixed Assets' }, { label: 'Physical Verification' }]}
        actions={
          <Button onClick={() => navigate('/admin/fixed-assets/verification/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New schedule
          </Button>
        }
      />

      {summaryQuery.data && (
        <VerificationProgressCard
          schedule={{
            id: 'summary',
            organizationId,
            scheduleReference: 'SUMMARY',
            scheduleName: `FY ${summaryQuery.data.financialYear}`,
            financialYear: summaryQuery.data.financialYear,
            locationId: null,
            locationName: null,
            categoryIds: null,
            scheduledStartDate: summaryQuery.data.financialYear,
            scheduledEndDate: summaryQuery.data.financialYear,
            actualStartDate: null,
            actualEndDate: null,
            assignedTo: null,
            assignedToName: null,
            teamMembers: null,
            totalAssets: summaryQuery.data.totalAssetsToVerify,
            verifiedCount: summaryQuery.data.totalAssetsVerified,
            foundCount: summaryQuery.data.totalFound,
            missingCount: summaryQuery.data.totalMissing,
            discrepancyCount: summaryQuery.data.totalDiscrepancies,
            totalValueVerified: summaryQuery.data.totalValueVerified,
            totalValueMissing: summaryQuery.data.totalValueMissing,
            status: 'COMPLETED',
            remarks: null,
            approvedBy: null,
            approvedAt: null,
            isActive: true,
            createdAt: null,
            updatedAt: null,
            createdBy: null,
            updatedBy: null,
          }}
        />
      )}

      <FilterBar
        search={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search by schedule reference, name, or location"
        onClear={() => {
          setSearch('');
          setStatus('ALL');
          setFinancialYear(defaultFinancialYear());
        }}
      >
        <InputMonth
          value={financialYear}
          onChange={setFinancialYear}
          className="w-[180px]"
        />
        <Select value={status} onValueChange={(value) => setStatus(value as VerificationScheduleStatus | 'ALL')}>
          <SelectTrigger className="w-[180px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {statusOptions.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </FilterBar>

      <DataTable
        data={schedules}
        columns={columns}
        getRowId={(row) => row.id}
        isLoading={schedulesQuery.isLoading}
        error={schedulesQuery.error}
        onRetry={() => schedulesQuery.refetch()}
        emptyTitle="No verification schedules found"
        emptySubtitle="Create a schedule to start physical verification for this financial year."
      />
    </div>
  );
}

function InputMonth({
  value,
  onChange,
  className,
}: {
  value: string;
  onChange: (value: string) => void;
  className?: string;
}): JSX.Element {
  return (
    <input
      type="text"
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className={`rounded-md border bg-background px-3 py-2 text-sm ${className ?? ''}`}
      placeholder="YYYY-YY"
    />
  );
}
