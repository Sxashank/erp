/**
 * IIF Claims — list with status / scheme / period filters and a "New Claim"
 * modal that runs the compute preview before persisting a draft.
 *
 * See CLAUDE.md §9.2, §9.3, §9.5.
 */

import { Calculator, Eye, FileText, Plus } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { DataTable, type Column } from '@/components/common/DataTable';
import { ErrorState } from '@/components/common/ErrorState';
import { FilterBar } from '@/components/common/FilterBar';
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
import { Textarea } from '@/components/ui/textarea';
import {
  useClaims,
  useComputeClaim,
  useCreateClaim,
  useEligibleLoans,
  useSubventionSchemes,
} from '@/hooks/lending/useIif';
import { useToast } from '@/hooks/use-toast';
import type { ClaimComputePreview, ClaimStatus, SubventionClaim } from '@/services/lending/iifApi';

const ALL = '__ALL__';

function statusVariant(status: ClaimStatus): {
  className: string;
  label: string;
} {
  switch (status) {
    case 'DRAFT':
      return {
        className: 'bg-slate-100 text-slate-700 border-slate-300',
        label: 'Draft',
      };
    case 'SUBMITTED':
      return {
        className: 'bg-blue-100 text-blue-800 border-blue-300',
        label: 'Submitted',
      };
    case 'VERIFIED':
      return {
        className: 'bg-purple-100 text-purple-800 border-purple-300',
        label: 'Verified',
      };
    case 'RELEASE_IN_PROGRESS':
      return {
        className: 'bg-amber-100 text-amber-800 border-amber-300',
        label: 'Release in Progress',
      };
    case 'RELEASED':
      return {
        className: 'bg-green-100 text-green-800 border-green-300',
        label: 'Released',
      };
    case 'REJECTED':
      return {
        className: 'bg-red-100 text-red-800 border-red-300',
        label: 'Rejected',
      };
    case 'CANCELLED':
      return {
        className: 'bg-slate-200 text-slate-700 border-slate-400',
        label: 'Cancelled',
      };
  }
}

export default function ClaimList(): JSX.Element {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [modalOpen, setModalOpen] = useState(false);

  const status = (searchParams.get('status') as ClaimStatus | null) ?? null;
  const schemeId = searchParams.get('schemeId') ?? null;
  const periodStartFrom = searchParams.get('periodStartFrom') ?? '';
  const periodEndTo = searchParams.get('periodEndTo') ?? '';

  const params = useMemo(
    () => ({
      status: status ?? undefined,
      schemeId: schemeId ?? undefined,
      periodStartFrom: periodStartFrom || undefined,
      periodEndTo: periodEndTo || undefined,
    }),
    [status, schemeId, periodStartFrom, periodEndTo],
  );

  const { data, isLoading, error, refetch } = useClaims(params);
  const items = data?.items ?? [];
  const { data: schemesData } = useSubventionSchemes();
  const schemes = schemesData?.items ?? [];

  const setFilter = (key: string, value: string | null) => {
    const next = new URLSearchParams(searchParams);
    if (value === null || value === '' || value === ALL) {
      next.delete(key);
    } else {
      next.set(key, value);
    }
    setSearchParams(next);
  };

  const columns: Column<SubventionClaim>[] = [
    {
      key: 'claimReference',
      header: 'Reference',
      sortable: true,
      render: (r) => <span className="font-mono text-sm">{r.claimReference}</span>,
    },
    {
      key: 'loanAccountNumber',
      header: 'Loan Account',
      render: (r) => <span className="font-mono text-sm">{r.loanAccountNumber}</span>,
    },
    {
      key: 'schemeCode',
      header: 'Scheme',
      render: (r) => <span className="font-mono text-sm">{r.schemeCode}</span>,
    },
    {
      key: 'periodStart',
      header: 'Period',
      render: (r) => (
        <span className="text-sm">
          <DateDisplay date={r.periodStart} /> — <DateDisplay date={r.periodEnd} />
        </span>
      ),
    },
    {
      key: 'interestPaidInPeriod',
      header: 'Interest Paid',
      align: 'right',
      render: (r) => <AmountDisplay amount={r.interestPaidInPeriod} size="sm" />,
    },
    {
      key: 'applicableSubventionAmount',
      header: 'Subvention',
      align: 'right',
      render: (r) => <AmountDisplay amount={r.applicableSubventionAmount} size="sm" />,
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
      key: 'releasedDate',
      header: 'Released On',
      render: (r) => (r.releasedDate ? <DateDisplay date={r.releasedDate} /> : '—'),
    },
    {
      key: 'actions',
      header: '',
      align: 'right',
      render: (r) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/admin/lending/iif/claims/${r.id}`);
          }}
          aria-label="View claim"
        >
          <Eye className="h-4 w-4" />
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Subvention Claims"
        subtitle="Quarterly claims under government interest-subvention schemes (e.g. IIF)."
        breadcrumbs={[
          { label: 'Lending', to: '/admin/lending' },
          { label: 'Interest Subvention' },
          { label: 'Claims' },
        ]}
        actions={
          <Button onClick={() => setModalOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New Claim
          </Button>
        }
      />

      <FilterBar>
        <div className="flex flex-wrap gap-3">
          <div className="w-48">
            <Label className="text-xs text-muted-foreground">Status</Label>
            <Select
              value={status ?? ALL}
              onValueChange={(v) => setFilter('status', v === ALL ? null : v)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>All statuses</SelectItem>
                <SelectItem value="DRAFT">Draft</SelectItem>
                <SelectItem value="SUBMITTED">Submitted</SelectItem>
                <SelectItem value="VERIFIED">Verified</SelectItem>
                <SelectItem value="RELEASE_IN_PROGRESS">Release in Progress</SelectItem>
                <SelectItem value="RELEASED">Released</SelectItem>
                <SelectItem value="REJECTED">Rejected</SelectItem>
                <SelectItem value="CANCELLED">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="w-56">
            <Label className="text-xs text-muted-foreground">Scheme</Label>
            <Select
              value={schemeId ?? ALL}
              onValueChange={(v) => setFilter('schemeId', v === ALL ? null : v)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>All schemes</SelectItem>
                {schemes.map((s) => (
                  <SelectItem key={s.id} value={s.id}>
                    {s.schemeCode}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="w-40">
            <Label className="text-xs text-muted-foreground">Period from</Label>
            <Input
              type="date"
              value={periodStartFrom}
              onChange={(e) => setFilter('periodStartFrom', e.target.value || null)}
            />
          </div>
          <div className="w-40">
            <Label className="text-xs text-muted-foreground">Period to</Label>
            <Input
              type="date"
              value={periodEndTo}
              onChange={(e) => setFilter('periodEndTo', e.target.value || null)}
            />
          </div>
        </div>
      </FilterBar>

      <DataTable<SubventionClaim>
        data={items}
        columns={columns}
        getRowId={(r) => r.id}
        isLoading={isLoading}
        error={error}
        onRetry={refetch}
        emptyTitle="No claims"
        emptySubtitle="Create a claim against an enrolled loan to start the cycle."
        emptyAction={
          <Button onClick={() => setModalOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New Claim
          </Button>
        }
      />

      <NewClaimModal open={modalOpen} onOpenChange={setModalOpen} />
    </div>
  );
}

// ============================================================================
// New Claim modal
// ============================================================================

interface NewClaimModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function NewClaimModal({ open, onOpenChange }: NewClaimModalProps): JSX.Element {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [enrollmentId, setEnrollmentId] = useState('');
  const [periodStart, setPeriodStart] = useState('');
  const [periodEnd, setPeriodEnd] = useState('');
  const [notes, setNotes] = useState('');
  const [preview, setPreview] = useState<ClaimComputePreview | null>(null);

  const { data: loans } = useEligibleLoans();

  const computeMut = useComputeClaim({
    onSuccess: (result) => setPreview(result),
  });
  const createMut = useCreateClaim({
    onSuccess: (claim) => {
      toast({ title: 'Draft claim created', description: claim.claimReference });
      reset();
      onOpenChange(false);
      navigate(`/admin/lending/iif/claims/${claim.id}`);
    },
  });

  const reset = () => {
    setEnrollmentId('');
    setPeriodStart('');
    setPeriodEnd('');
    setNotes('');
    setPreview(null);
  };

  const handleOpenChange = (next: boolean) => {
    if (!next) reset();
    onOpenChange(next);
  };

  const selectLoan = (id: string) => {
    const loan = loans?.find((l) => l.enrollmentId === id);
    setEnrollmentId(id);
    if (loan?.periodStart) setPeriodStart(loan.periodStart);
    if (loan?.periodEnd) setPeriodEnd(loan.periodEnd);
    setPreview(null);
  };

  const handleCompute = () => {
    if (!enrollmentId || !periodStart || !periodEnd) return;
    setPreview(null);
    computeMut.mutate({ enrollmentId, periodStart, periodEnd });
  };

  const handleCreate = () => {
    if (!enrollmentId || !periodStart || !periodEnd) return;
    createMut.mutate({
      enrollmentId,
      periodStart,
      periodEnd,
      notes: notes || null,
    });
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>New subvention claim</DialogTitle>
          <DialogDescription>
            Pick an enrolled loan and a period, run the compute preview, then save as draft.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Enrolled loan *</Label>
            <Select value={enrollmentId} onValueChange={selectLoan}>
              <SelectTrigger>
                <SelectValue placeholder="Select an enrolled loan" />
              </SelectTrigger>
              <SelectContent>
                {(loans ?? []).map((l) => (
                  <SelectItem key={l.enrollmentId} value={l.enrollmentId}>
                    {l.loanAccountNumber ?? l.loanAccountId.slice(0, 8)} · {l.schemeCode} ·{' '}
                    {l.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>Period start *</Label>
              <Input
                type="date"
                value={periodStart}
                onChange={(e) => {
                  setPeriodStart(e.target.value);
                  setPreview(null);
                }}
              />
            </div>
            <div className="space-y-2">
              <Label>Period end *</Label>
              <Input
                type="date"
                value={periodEnd}
                onChange={(e) => {
                  setPeriodEnd(e.target.value);
                  setPreview(null);
                }}
              />
            </div>
          </div>

          <div className="flex justify-end">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCompute}
              disabled={!enrollmentId || !periodStart || !periodEnd || computeMut.isPending}
            >
              <Calculator className="mr-2 h-4 w-4" />
              Compute
            </Button>
          </div>

          {preview && (
            <div className="rounded-md border bg-muted/30 p-4">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <div className="text-xs text-muted-foreground">Period</div>
                  <DateDisplay date={preview.periodStart} /> —{' '}
                  <DateDisplay date={preview.periodEnd} />
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">Rate</div>
                  <span className="tabular-nums">{preview.subventionRatePercent}%</span>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">Interest paid</div>
                  <AmountDisplay amount={preview.interestPaidInPeriod} />
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">Applicable subvention</div>
                  <AmountDisplay amount={preview.applicableSubventionAmount} size="lg" />
                </div>
              </div>
            </div>
          )}

          <div className="space-y-2">
            <Label>Notes (optional)</Label>
            <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} />
          </div>

          {computeMut.isError && (
            <ErrorState error={computeMut.error} onRetry={handleCompute} title="Compute failed" />
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleCreate} disabled={!preview || createMut.isPending}>
            <FileText className="mr-2 h-4 w-4" />
            Create draft claim
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
