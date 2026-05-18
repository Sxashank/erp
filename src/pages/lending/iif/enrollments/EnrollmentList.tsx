/**
 * IIF Enrollments — list page with status tabs and an "Enroll Loan" modal.
 *
 * See CLAUDE.md §9.2, §9.3, §9.5.
 */

import { Check, CheckCircle2, Plus, ShieldOff, Sparkles, X, XCircle } from 'lucide-react';
import { useMemo, useState } from 'react';

import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { DataTable, type Column } from '@/components/common/DataTable';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
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
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import {
  useApproveEnrollment,
  useCreateEnrollment,
  useEligibilityCheck,
  useEnrollments,
  useReinstateEnrollment,
  useRejectEnrollment,
  useSubventionSchemes,
  useSuspendEnrollment,
} from '@/hooks/lending/useIif';
import { useLoanAccounts } from '@/hooks/lending/useLoanAccounts';
import { useToast } from '@/hooks/use-toast';
import type {
  EligibilityCheckResult,
  EnrollmentStatus,
  LoanSubventionEnrollment,
} from '@/services/lending/iifApi';

type TabValue = 'ALL' | EnrollmentStatus;

const TABS: { value: TabValue; label: string }[] = [
  { value: 'ALL', label: 'All' },
  { value: 'PENDING_APPROVAL', label: 'Pending' },
  { value: 'ENROLLED', label: 'Enrolled' },
  { value: 'REJECTED', label: 'Rejected' },
  { value: 'SUSPENDED', label: 'Suspended' },
];

function statusVariant(status: EnrollmentStatus): { className: string; label: string } {
  switch (status) {
    case 'ENROLLED':
      return { className: 'bg-green-100 text-green-800 border-green-300', label: 'Enrolled' };
    case 'PENDING_APPROVAL':
      return {
        className: 'bg-amber-100 text-amber-800 border-amber-300',
        label: 'Pending approval',
      };
    case 'REJECTED':
      return { className: 'bg-red-100 text-red-800 border-red-300', label: 'Rejected' };
    case 'SUSPENDED':
      return { className: 'bg-slate-100 text-slate-700 border-slate-300', label: 'Suspended' };
    case 'TERMINATED':
      return { className: 'bg-slate-200 text-slate-700 border-slate-400', label: 'Terminated' };
  }
}

interface RowAction {
  open: boolean;
  enrollment: LoanSubventionEnrollment | null;
  action: 'approve' | 'reject' | 'suspend' | 'reinstate' | null;
  reason: string;
}

const emptyRowAction: RowAction = {
  open: false,
  enrollment: null,
  action: null,
  reason: '',
};

export default function EnrollmentList(): JSX.Element {
  const { toast } = useToast();
  const [tab, setTab] = useState<TabValue>('ALL');
  const [enrollModalOpen, setEnrollModalOpen] = useState(false);
  const [rowAction, setRowAction] = useState<RowAction>(emptyRowAction);

  const params = useMemo(() => (tab === 'ALL' ? undefined : { status: tab }), [tab]);

  const { data, isLoading, error, refetch } = useEnrollments(params);
  const items = data?.items ?? [];

  const approveMut = useApproveEnrollment({
    onSuccess: () => {
      toast({ title: 'Enrollment approved' });
      setRowAction(emptyRowAction);
    },
  });
  const rejectMut = useRejectEnrollment({
    onSuccess: () => {
      toast({ title: 'Enrollment rejected' });
      setRowAction(emptyRowAction);
    },
  });
  const suspendMut = useSuspendEnrollment({
    onSuccess: () => {
      toast({ title: 'Enrollment suspended' });
      setRowAction(emptyRowAction);
    },
  });
  const reinstateMut = useReinstateEnrollment({
    onSuccess: () => {
      toast({ title: 'Enrollment reinstated' });
      setRowAction(emptyRowAction);
    },
  });

  const actionPending =
    approveMut.isPending || rejectMut.isPending || suspendMut.isPending || reinstateMut.isPending;

  const performRowAction = () => {
    if (!rowAction.enrollment || !rowAction.action) return;
    const enrollmentId = rowAction.enrollment.id;
    switch (rowAction.action) {
      case 'approve':
        approveMut.mutate({ id: enrollmentId, notes: rowAction.reason || undefined });
        break;
      case 'reject':
        rejectMut.mutate({ id: enrollmentId, reason: rowAction.reason });
        break;
      case 'suspend':
        suspendMut.mutate({ id: enrollmentId, reason: rowAction.reason });
        break;
      case 'reinstate':
        reinstateMut.mutate({
          id: enrollmentId,
          notes: rowAction.reason || undefined,
        });
        break;
    }
  };

  const columns: Column<LoanSubventionEnrollment>[] = [
    {
      key: 'loanAccountNumber',
      header: 'Loan Account #',
      sortable: true,
      render: (r) => <span className="font-mono text-sm">{r.loanAccountNumber}</span>,
    },
    { key: 'entityName', header: 'Borrower', sortable: true },
    {
      key: 'schemeCode',
      header: 'Scheme',
      render: (r) => <span className="font-mono text-sm">{r.schemeCode}</span>,
    },
    {
      key: 'enrolledDate',
      header: 'Enrolled',
      render: (r) => <DateDisplay date={r.enrolledDate} />,
    },
    {
      key: 'status',
      header: 'Status',
      render: (r) => {
        const v = statusVariant(r.status);
        return (
          <Badge variant="outline" className={v.className}>
            {v.label}
          </Badge>
        );
      },
    },
    {
      key: 'totalClaimedToDate',
      header: 'Claimed',
      align: 'right',
      render: (r) => <AmountDisplay amount={r.totalClaimedToDate} size="sm" />,
    },
    {
      key: 'totalPaidToDate',
      header: 'Paid',
      align: 'right',
      render: (r) => <AmountDisplay amount={r.totalPaidToDate} size="sm" />,
    },
    {
      key: 'actions',
      header: '',
      align: 'right',
      render: (r) => (
        <div className="flex justify-end gap-1">
          {r.status === 'PENDING_APPROVAL' && (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  setRowAction({ open: true, enrollment: r, action: 'approve', reason: '' });
                }}
                aria-label="Approve"
              >
                <Check className="h-4 w-4 text-green-600" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  setRowAction({ open: true, enrollment: r, action: 'reject', reason: '' });
                }}
                aria-label="Reject"
              >
                <X className="h-4 w-4 text-red-600" />
              </Button>
            </>
          )}
          {r.status === 'ENROLLED' && (
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                setRowAction({ open: true, enrollment: r, action: 'suspend', reason: '' });
              }}
              aria-label="Suspend"
            >
              <ShieldOff className="h-4 w-4 text-amber-600" />
            </Button>
          )}
          {r.status === 'SUSPENDED' && (
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                setRowAction({ open: true, enrollment: r, action: 'reinstate', reason: '' });
              }}
              aria-label="Reinstate"
            >
              <CheckCircle2 className="h-4 w-4 text-blue-600" />
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="IIF Enrollments"
        subtitle="Loan accounts enrolled into government interest-subvention schemes."
        breadcrumbs={[
          { label: 'Lending', to: '/admin/lending' },
          { label: 'Interest Subvention' },
          { label: 'Enrollments' },
        ]}
        actions={
          <Button onClick={() => setEnrollModalOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Enroll Loan
          </Button>
        }
      />

      <Tabs value={tab} onValueChange={(v) => setTab(v as TabValue)}>
        <TabsList>
          {TABS.map((t) => (
            <TabsTrigger key={t.value} value={t.value}>
              {t.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      <DataTable<LoanSubventionEnrollment>
        data={items}
        columns={columns}
        getRowId={(r) => r.id}
        isLoading={isLoading}
        error={error}
        onRetry={refetch}
        emptyTitle="No enrollments"
        emptySubtitle="Enroll a loan into a subvention scheme to start claiming."
        emptyAction={
          <Button onClick={() => setEnrollModalOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Enroll Loan
          </Button>
        }
      />

      <EnrollLoanModal open={enrollModalOpen} onOpenChange={setEnrollModalOpen} />

      <ConfirmDialog
        open={rowAction.open}
        onOpenChange={(open) => setRowAction((prev) => ({ ...prev, open }))}
        title={
          rowAction.action === 'approve'
            ? 'Approve enrollment?'
            : rowAction.action === 'reject'
              ? 'Reject enrollment?'
              : rowAction.action === 'suspend'
                ? 'Suspend enrollment?'
                : 'Reinstate enrollment?'
        }
        description={
          <div className="space-y-3">
            <p className="text-sm">
              Loan <span className="font-mono">{rowAction.enrollment?.loanAccountNumber}</span> (
              {rowAction.enrollment?.entityName}) — scheme{' '}
              <span className="font-mono">{rowAction.enrollment?.schemeCode}</span>.
            </p>
            <div>
              <Label className="text-sm">
                {rowAction.action === 'approve' || rowAction.action === 'reinstate'
                  ? 'Notes (optional)'
                  : 'Reason *'}
              </Label>
              <Textarea
                value={rowAction.reason}
                onChange={(e) => setRowAction((prev) => ({ ...prev, reason: e.target.value }))}
                rows={3}
              />
            </div>
          </div>
        }
        confirmLabel={
          rowAction.action === 'reject'
            ? 'Reject'
            : rowAction.action === 'suspend'
              ? 'Suspend'
              : rowAction.action === 'reinstate'
                ? 'Reinstate'
                : 'Approve'
        }
        variant={
          rowAction.action === 'reject' || rowAction.action === 'suspend'
            ? 'destructive'
            : 'default'
        }
        loading={actionPending}
        onConfirm={performRowAction}
      />
    </div>
  );
}

// ============================================================================
// Enroll Loan modal
// ============================================================================

interface EnrollLoanModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function EnrollLoanModal({ open, onOpenChange }: EnrollLoanModalProps): JSX.Element {
  const { toast } = useToast();
  const [loanAccountId, setLoanAccountId] = useState('');
  const [schemeId, setSchemeId] = useState('');
  const [notes, setNotes] = useState('');
  const [eligibility, setEligibility] = useState<EligibilityCheckResult | null>(null);

  const loansQuery = useLoanAccounts({ pageSize: 100 });
  const schemesQuery = useSubventionSchemes({ isActive: true });

  const checkMut = useEligibilityCheck({
    onSuccess: (result) => {
      setEligibility(result);
    },
  });

  const enrollMut = useCreateEnrollment({
    onSuccess: () => {
      toast({ title: 'Enrollment submitted' });
      reset();
      onOpenChange(false);
    },
  });

  const reset = () => {
    setLoanAccountId('');
    setSchemeId('');
    setNotes('');
    setEligibility(null);
  };

  const handleOpenChange = (next: boolean) => {
    if (!next) reset();
    onOpenChange(next);
  };

  const handleCheck = () => {
    if (!loanAccountId || !schemeId) return;
    setEligibility(null);
    checkMut.mutate({ loanAccountId, schemeId });
  };

  const handleEnroll = () => {
    if (!loanAccountId || !schemeId) return;
    enrollMut.mutate({
      loanAccountId,
      schemeId,
      notes: notes || null,
    });
  };

  const canEnroll = loanAccountId && schemeId;
  const eligiblePassed = eligibility?.eligible ?? false;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Enroll loan into subvention scheme</DialogTitle>
          <DialogDescription>
            Pick the loan account and scheme, run eligibility checks, then submit.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Loan Account *</Label>
            <Select value={loanAccountId} onValueChange={setLoanAccountId}>
              <SelectTrigger>
                <SelectValue placeholder="Select a loan account" />
              </SelectTrigger>
              <SelectContent>
                {(loansQuery.data?.items ?? []).map((l) => (
                  <SelectItem key={l.id} value={l.id}>
                    {l.loanAccountNumber} — {l.entityName ?? 'Unknown borrower'}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Scheme *</Label>
            <Select value={schemeId} onValueChange={setSchemeId}>
              <SelectTrigger>
                <SelectValue placeholder="Select a scheme" />
              </SelectTrigger>
              <SelectContent>
                {(schemesQuery.data?.items ?? []).map((s) => (
                  <SelectItem key={s.id} value={s.id}>
                    {s.schemeCode} — {s.schemeName}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex justify-end">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCheck}
              disabled={!canEnroll || checkMut.isPending}
            >
              <Sparkles className="mr-2 h-4 w-4" />
              Check eligibility
            </Button>
          </div>

          {eligibility && (
            <div className="rounded-md border p-3">
              <div className="mb-2 flex items-center gap-2 text-sm font-medium">
                {eligiblePassed ? (
                  <Badge className="border-green-300 bg-green-100 text-green-800" variant="outline">
                    Eligible
                  </Badge>
                ) : (
                  <Badge className="border-red-300 bg-red-100 text-red-800" variant="outline">
                    Not eligible
                  </Badge>
                )}
              </div>
              <ul className="space-y-1 text-sm">
                {Object.entries(eligibility.checks).map(([rule, passed]) => (
                  <li key={rule} className="flex items-start gap-2">
                    {passed ? (
                      <CheckCircle2 className="mt-0.5 h-4 w-4 text-green-600" />
                    ) : (
                      <XCircle className="mt-0.5 h-4 w-4 text-red-600" />
                    )}
                    <span className="flex-1 font-medium">{rule.replace(/_/g, ' ')}</span>
                  </li>
                ))}
              </ul>
              {eligibility.reasons.length > 0 && (
                <div className="mt-3 space-y-1 text-sm text-red-700">
                  {eligibility.reasons.map((r, i) => (
                    <div key={i}>· {r}</div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="space-y-2">
            <Label>Notes (optional)</Label>
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              placeholder="Reason for enrollment, special handling, etc."
            />
          </div>

          {checkMut.isError && (
            <ErrorState
              error={checkMut.error}
              onRetry={handleCheck}
              title="Eligibility check failed"
            />
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleEnroll}
            disabled={
              !canEnroll || enrollMut.isPending || (eligibility !== null && !eligiblePassed)
            }
          >
            <Plus className="mr-2 h-4 w-4" />
            Enroll
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
