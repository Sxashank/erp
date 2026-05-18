import { zodResolver } from '@hookform/resolvers/zod';
import { CheckCircle2, FileSearch, PlayCircle } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';

import {
  AmountDisplay,
  DataTable,
  DateDisplay,
  DetailGrid,
  EmptyState,
  ErrorState,
  PageHeader,
  type Column,
} from '@/components/common';
import { VerificationProgressCard } from '@/components/fixed-assets/VerificationProgressCard';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DatePicker } from '@/components/ui/date-picker';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import {
  useApproveVerificationSchedule,
  useCompleteVerificationSchedule,
  useStartVerificationSchedule,
  useUpdateVerificationDiscrepancy,
  useVerificationDiscrepancies,
  useVerificationEntries,
  useVerificationSchedule,
  useVerifyVerificationEntry,
} from '@/hooks/fixed-assets/usePhysicalVerification';
import { useToast } from '@/hooks/use-toast';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import { showErrorToast } from '@/lib/errorToast';
import {
  discrepancyResolutionSchema,
  verifyEntrySchema,
  type DiscrepancyResolutionInput,
  type VerifyEntryInput,
} from '@/schemas/fixed-assets/verificationSchema';
import type { Discrepancy, VerificationEntry } from '@/types/fixed-assets';

function toDate(value: string | undefined | null): Date | null {
  return value ? new Date(value) : null;
}

function toIsoDate(value: Date | undefined): string {
  return value ? value.toISOString().slice(0, 10) : '';
}

export function PhysicalVerificationDetail(): JSX.Element {
  const organizationId = useRequiredActiveOrganizationId();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const scheduleQuery = useVerificationSchedule(id);
  const entriesQuery = useVerificationEntries(id);
  const discrepanciesQuery = useVerificationDiscrepancies(organizationId, { limit: 200 });

  const startMutation = useStartVerificationSchedule(organizationId, id ?? '');
  const completeMutation = useCompleteVerificationSchedule(organizationId, id ?? '');
  const approveMutation = useApproveVerificationSchedule(organizationId, id ?? '');
  const verifyMutation = useVerifyVerificationEntry(organizationId, id ?? '');
  const discrepancyMutation = useUpdateVerificationDiscrepancy(organizationId, id);

  const [entryDialog, setEntryDialog] = useState<VerificationEntry | null>(null);
  const [discrepancyDialog, setDiscrepancyDialog] = useState<Discrepancy | null>(null);

  const verifyForm = useForm<VerifyEntryInput>({
    resolver: zodResolver(verifyEntrySchema),
    defaultValues: {
      verificationDate: '',
      verificationResult: 'FOUND',
      assetCondition: 'GOOD',
      actualLocationId: '',
      actualDepartmentId: '',
      barcodeScan: '',
      conditionNotes: '',
      remarks: '',
    },
  });
  const discrepancyForm = useForm<DiscrepancyResolutionInput>({
    resolver: zodResolver(discrepancyResolutionSchema),
    defaultValues: {
      status: 'INVESTIGATING',
      investigationNotes: '',
      resolution: '',
      remarks: '',
    },
  });

  const schedule = scheduleQuery.data;
  const discrepancies = useMemo(
    () =>
      (discrepanciesQuery.data?.items ?? []).filter(
        (discrepancy) => discrepancy.entryId && entriesQuery.data?.items.some((entry) => entry.id === discrepancy.entryId),
      ),
    [discrepanciesQuery.data?.items, entriesQuery.data?.items],
  );

  const entryColumns: Column<VerificationEntry>[] = useMemo(
    () => [
      {
        key: 'assetCode',
        header: 'Asset',
        render: (row) => (
          <div>
            <div className="font-medium">{row.assetName ?? row.assetCode}</div>
            <div className="text-xs text-muted-foreground">{row.assetCode}</div>
          </div>
        ),
      },
      {
        key: 'categoryName',
        header: 'Category',
        render: (row) => row.categoryName ?? '—',
      },
      {
        key: 'bookValue',
        header: 'Book value',
        align: 'right',
        render: (row) => <AmountDisplay amount={row.bookValue} compact />,
      },
      {
        key: 'verificationResult',
        header: 'Result',
        render: (row) => row.verificationResult ?? 'Pending',
      },
      {
        key: 'verificationDate',
        header: 'Verified on',
        render: (row) => <DateDisplay date={row.verificationDate} />,
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
            onClick={() => {
              setEntryDialog(row);
              verifyForm.reset({
                verificationDate: row.verificationDate ?? new Date().toISOString().slice(0, 10),
                verificationResult: row.verificationResult ?? 'FOUND',
                assetCondition: row.assetCondition ?? 'GOOD',
                actualLocationId: '',
                actualDepartmentId: '',
                barcodeScan: row.barcodeScan ?? '',
                conditionNotes: row.conditionNotes ?? '',
                remarks: row.remarks ?? '',
              });
            }}
          >
            Verify
          </Button>
        ),
      },
    ],
    [verifyForm],
  );

  const discrepancyColumns: Column<Discrepancy>[] = useMemo(
    () => [
      {
        key: 'assetCode',
        header: 'Asset',
        render: (row) => (
          <div>
            <div className="font-medium">{row.assetName ?? row.assetCode}</div>
            <div className="text-xs text-muted-foreground">{row.assetCode}</div>
          </div>
        ),
      },
      { key: 'discrepancyType', header: 'Type' },
      {
        key: 'valueImpact',
        header: 'Value impact',
        align: 'right',
        render: (row) => <AmountDisplay amount={row.valueImpact} compact />,
      },
      { key: 'status', header: 'Status' },
      {
        key: 'actions',
        header: '',
        align: 'right',
        render: (row) => (
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => {
              setDiscrepancyDialog(row);
              discrepancyForm.reset({
                status: row.status,
                investigationNotes: row.investigationNotes ?? '',
                resolution: row.resolution ?? '',
                remarks: row.remarks ?? '',
              });
            }}
          >
            Resolve
          </Button>
        ),
      },
    ],
    [discrepancyForm],
  );

  if (scheduleQuery.isLoading) {
    return <div className="rounded-lg border bg-background p-8 text-sm text-muted-foreground">Loading verification schedule…</div>;
  }

  if (scheduleQuery.error) {
    return <ErrorState error={scheduleQuery.error} onRetry={() => scheduleQuery.refetch()} />;
  }

  if (!schedule) {
    return (
      <EmptyState
        title="Verification schedule not found"
        subtitle="The requested schedule does not exist in the current organization."
        action={
          <Button type="button" onClick={() => navigate('/admin/fixed-assets/verification')}>
            Back to verification
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={schedule.scheduleName}
        subtitle={schedule.scheduleReference}
        breadcrumbs={[
          { label: 'Fixed Assets' },
          { label: 'Physical Verification', to: '/admin/fixed-assets/verification' },
          { label: schedule.scheduleReference },
        ]}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            {schedule.status === 'SCHEDULED' && (
              <Button
                onClick={async () => {
                  try {
                    await startMutation.mutateAsync();
                    toast({ title: 'Verification started' });
                  } catch (error) {
                    showErrorToast(error, toast);
                  }
                }}
              >
                <PlayCircle className="mr-2 h-4 w-4" />
                Start
              </Button>
            )}
            {schedule.status === 'IN_PROGRESS' && (
              <Button
                onClick={async () => {
                  try {
                    await completeMutation.mutateAsync();
                    toast({ title: 'Verification completed' });
                  } catch (error) {
                    showErrorToast(error, toast);
                  }
                }}
              >
                <CheckCircle2 className="mr-2 h-4 w-4" />
                Complete
              </Button>
            )}
            {schedule.status === 'COMPLETED' && !schedule.approvedAt && (
              <Button
                onClick={async () => {
                  try {
                    await approveMutation.mutateAsync();
                    toast({ title: 'Verification approved' });
                  } catch (error) {
                    showErrorToast(error, toast);
                  }
                }}
              >
                <FileSearch className="mr-2 h-4 w-4" />
                Approve
              </Button>
            )}
          </div>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardHeader>
            <CardTitle>Schedule Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <DetailGrid
              columns={2}
              fields={[
                { label: 'Financial year', value: schedule.financialYear },
                { label: 'Status', value: schedule.status.replace(/_/g, ' ') },
                { label: 'Location', value: schedule.locationName ?? 'All locations' },
                { label: 'Scheduled start', value: <DateDisplay date={schedule.scheduledStartDate} /> },
                { label: 'Scheduled end', value: <DateDisplay date={schedule.scheduledEndDate} /> },
                { label: 'Actual start', value: <DateDisplay date={schedule.actualStartDate} /> },
                { label: 'Actual end', value: <DateDisplay date={schedule.actualEndDate} /> },
                { label: 'Approved at', value: <DateDisplay date={schedule.approvedAt} /> },
              ]}
            />
          </CardContent>
        </Card>
        <VerificationProgressCard schedule={schedule} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Verification Entries</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            data={entriesQuery.data?.items ?? []}
            columns={entryColumns}
            getRowId={(row) => row.id}
            isLoading={entriesQuery.isLoading}
            error={entriesQuery.error}
            onRetry={() => entriesQuery.refetch()}
            emptyTitle="No verification entries available"
            emptySubtitle="Assets will populate here once the schedule scope is built."
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Discrepancies</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            data={discrepancies}
            columns={discrepancyColumns}
            getRowId={(row) => row.id}
            isLoading={discrepanciesQuery.isLoading}
            error={discrepanciesQuery.error}
            onRetry={() => discrepanciesQuery.refetch()}
            emptyTitle="No discrepancies raised"
            emptySubtitle="Missing, misplaced, or damaged assets will open discrepancies here."
          />
        </CardContent>
      </Card>

      <Dialog open={Boolean(entryDialog)} onOpenChange={(open) => !open && setEntryDialog(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Verify Asset</DialogTitle>
          </DialogHeader>
          <Form {...verifyForm}>
            <form
              className="space-y-4"
              onSubmit={verifyForm.handleSubmit(async (values) => {
                if (!entryDialog) return;
                try {
                  await verifyMutation.mutateAsync({
                    entryId: entryDialog.id,
                    payload: {
                      assetId: entryDialog.assetId,
                      verificationDate: values.verificationDate,
                      verificationResult: values.verificationResult,
                      assetCondition: values.assetCondition,
                      barcodeScan: values.barcodeScan || null,
                      conditionNotes: values.conditionNotes || null,
                      remarks: values.remarks || null,
                    },
                  });
                  toast({ title: 'Verification saved' });
                  setEntryDialog(null);
                } catch (error) {
                  showErrorToast(error, toast);
                }
              })}
            >
              <FormField
                control={verifyForm.control}
                name="verificationDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Verification date</FormLabel>
                    <FormControl>
                      <DatePicker date={toDate(field.value)} onSelect={(value) => field.onChange(toIsoDate(value))} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={verifyForm.control}
                name="verificationResult"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Result</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="FOUND">Found</SelectItem>
                        <SelectItem value="MISSING">Missing</SelectItem>
                        <SelectItem value="MISPLACED">Misplaced</SelectItem>
                        <SelectItem value="EXCESS">Excess</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={verifyForm.control}
                name="assetCondition"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Condition</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="GOOD">Good</SelectItem>
                        <SelectItem value="FAIR">Fair</SelectItem>
                        <SelectItem value="POOR">Poor</SelectItem>
                        <SelectItem value="DAMAGED">Damaged</SelectItem>
                        <SelectItem value="NOT_WORKING">Not working</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={verifyForm.control}
                name="conditionNotes"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Condition notes</FormLabel>
                    <FormControl>
                      <Textarea {...field} rows={3} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setEntryDialog(null)}>
                  Cancel
                </Button>
                <Button type="submit">Save verification</Button>
              </div>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      <Dialog open={Boolean(discrepancyDialog)} onOpenChange={(open) => !open && setDiscrepancyDialog(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Resolve Discrepancy</DialogTitle>
          </DialogHeader>
          <Form {...discrepancyForm}>
            <form
              className="space-y-4"
              onSubmit={discrepancyForm.handleSubmit(async (values) => {
                if (!discrepancyDialog) return;
                try {
                  await discrepancyMutation.mutateAsync({
                    discrepancyId: discrepancyDialog.id,
                    payload: {
                      status: values.status,
                      investigationNotes: values.investigationNotes || null,
                      resolution: values.resolution || null,
                      remarks: values.remarks || null,
                    },
                  });
                  toast({ title: 'Discrepancy updated' });
                  setDiscrepancyDialog(null);
                } catch (error) {
                  showErrorToast(error, toast);
                }
              })}
            >
              <FormField
                control={discrepancyForm.control}
                name="status"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Status</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="OPEN">Open</SelectItem>
                        <SelectItem value="INVESTIGATING">Investigating</SelectItem>
                        <SelectItem value="RESOLVED">Resolved</SelectItem>
                        <SelectItem value="WRITTEN_OFF">Written off</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={discrepancyForm.control}
                name="investigationNotes"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Investigation notes</FormLabel>
                    <FormControl>
                      <Textarea {...field} rows={3} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={discrepancyForm.control}
                name="resolution"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Resolution</FormLabel>
                    <FormControl>
                      <Textarea {...field} rows={3} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setDiscrepancyDialog(null)}>
                  Cancel
                </Button>
                <Button type="submit">Save resolution</Button>
              </div>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
