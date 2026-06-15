/**
 * Admin — Borrower Portal Registrations queue.
 *
 * Pending queue list with a "Review" action that opens a modal showing the
 * registration detail + suggested entities (sorted by match strength).
 * Approve dialog renders a multi-select with EXACT_* suggestions pre-ticked;
 * Reject dialog requires a reason with at least 5 characters.
 *
 * CLAUDE.md §5.1 / §9.5 strict: PageHeader + DataTable + ConfirmDialog +
 * StatusPill — no inline tables or status badges.
 */

import { Eye, Loader2, ShieldCheck, ShieldX } from 'lucide-react';
import { useMemo, useState } from 'react';

import { DataTable, DateDisplay, PageHeader, StatusPill, type Column } from '@/components/common';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
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
  useApproveRegistration,
  usePendingRegistrations,
  usePortalRegistration,
  useRejectRegistration,
} from '@/hooks/admin/usePortalRegistrations';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import type {
  AdminRegistrationListItem,
  EntityMatchStrength,
  EntitySuggestion,
  PortalRegistrationStatus,
} from '@/services/admin/portalRegistrationsApi';

const STATUS_FILTERS: {
  value: PortalRegistrationStatus;
  label: string;
}[] = [
  { value: 'PENDING_APPROVAL', label: 'Pending approval' },
  { value: 'ACTIVE', label: 'Active' },
  { value: 'REJECTED', label: 'Rejected' },
];

const MATCH_STRENGTH_ORDER: Record<EntityMatchStrength, number> = {
  EXACT_LOAN_ACCOUNT: 0,
  EXACT_CIN: 1,
  EXACT_GSTIN: 2,
  EXACT_PAN: 3,
  EXACT_LLPIN: 4,
  FUZZY_NAME: 5,
};

const EXACT_STRENGTHS: EntityMatchStrength[] = [
  'EXACT_LOAN_ACCOUNT',
  'EXACT_CIN',
  'EXACT_GSTIN',
  'EXACT_PAN',
  'EXACT_LLPIN',
];

export default function AdminPortalRegistrations(): JSX.Element {
  const { toast } = useToast();
  const [statusFilter, setStatusFilter] = useState<PortalRegistrationStatus>('PENDING_APPROVAL');
  const [reviewingId, setReviewingId] = useState<string | null>(null);

  const query = usePendingRegistrations({ status: statusFilter });

  const columns: Column<AdminRegistrationListItem>[] = useMemo(
    () => [
      {
        key: 'registrationReference',
        header: 'Reference',
        render: (r) => <span className="font-mono text-xs">{r.registrationReference}</span>,
      },
      {
        key: 'authorizedSignatoryName',
        header: 'Signatory',
        render: (r) => (
          <div>
            <p className="font-medium">{r.authorizedSignatoryName}</p>
            <p className="text-xs text-muted-foreground">{r.email}</p>
          </div>
        ),
      },
      {
        key: 'identifier',
        header: 'Identifier',
        render: (r) => {
          const id = r.requestedLoanAccountNumber
            ? `${r.requestedLoanAccountNumber} / ${r.requestedSanctionedAmount ?? '—'}`
            : r.requestedCin ?? r.requestedGstin ?? r.requestedLlpin ?? r.requestedPan;
          const type = r.requestedLoanAccountNumber
            ? 'LOAN'
            : r.requestedCin
              ? 'CIN'
              : r.requestedGstin
                ? 'GSTIN'
                : r.requestedLlpin
                  ? 'LLPIN'
                  : 'PAN';
          return (
            <div>
              <Badge variant="secondary" className="mr-1">
                {type}
              </Badge>
              <span className="font-mono text-xs">{id ?? '—'}</span>
            </div>
          );
        },
      },
      {
        key: 'mobile',
        header: 'Mobile',
        render: (r) => <span className="font-mono text-xs">{r.mobile}</span>,
      },
      {
        key: 'registeredAt',
        header: 'Registered',
        render: (r) => <DateDisplay date={r.registeredAt} />,
        sortable: true,
        sortValue: (r) => r.registeredAt,
      },
      {
        key: 'registrationStatus',
        header: 'Status',
        render: (r) => <StatusPill type="application" status={r.registrationStatus} />,
      },
      {
        key: 'actions',
        header: '',
        align: 'right',
        render: (r) => (
          <Button size="sm" variant="outline" onClick={() => setReviewingId(r.portalUserId)}>
            <Eye className="mr-2 h-4 w-4" />
            Review
          </Button>
        ),
      },
    ],
    [],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Portal Registrations"
        subtitle="Borrower self-service registration requests awaiting your review."
        breadcrumbs={[{ label: 'Administration' }, { label: 'Portal Registrations' }]}
        actions={
          <div className="flex items-center gap-2">
            <Label htmlFor="status-filter" className="text-sm">
              Status
            </Label>
            <Select
              value={statusFilter}
              onValueChange={(v) => setStatusFilter(v as PortalRegistrationStatus)}
            >
              <SelectTrigger id="status-filter" className="w-[200px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {STATUS_FILTERS.map((s) => (
                  <SelectItem key={s.value} value={s.value}>
                    {s.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        }
      />

      <DataTable<AdminRegistrationListItem>
        data={query.data?.items ?? []}
        columns={columns}
        getRowId={(r) => r.portalUserId}
        isLoading={query.isLoading}
        error={query.isError ? query.error : undefined}
        onRetry={() => query.refetch()}
        emptyTitle={
          statusFilter === 'PENDING_APPROVAL'
            ? 'No pending registrations'
            : 'No matching registrations'
        }
        emptySubtitle={
          statusFilter === 'PENDING_APPROVAL'
            ? 'New borrower registrations will appear here when borrowers complete the OTP step.'
            : undefined
        }
      />

      {reviewingId && (
        <ReviewDialog
          id={reviewingId}
          onClose={() => setReviewingId(null)}
          onError={(err) => showErrorToast(err, toast)}
          onSuccess={(msg) => toast({ title: msg, description: 'Queue updated.' })}
        />
      )}
    </div>
  );
}

function ReviewDialog({
  id,
  onClose,
  onError,
  onSuccess,
}: {
  id: string;
  onClose: () => void;
  onError: (err: unknown) => void;
  onSuccess: (msg: string) => void;
}): JSX.Element {
  const detailQuery = usePortalRegistration(id);
  const approve = useApproveRegistration();
  const reject = useRejectRegistration();

  const [mode, setMode] = useState<'view' | 'approve' | 'reject'>('view');
  const [selectedEntityIds, setSelectedEntityIds] = useState<string[]>([]);
  const [initialized, setInitialized] = useState(false);
  const [rejectReason, setRejectReason] = useState('');

  // Pre-tick EXACT_* suggestions once data arrives.
  if (!initialized && detailQuery.data) {
    const exact = detailQuery.data.suggestedEntities
      .filter((s) => EXACT_STRENGTHS.includes(s.matchStrength))
      .map((s) => s.entityId);
    setSelectedEntityIds(exact);
    setInitialized(true);
  }

  const sortedSuggestions = (detailQuery.data?.suggestedEntities ?? [])
    .slice()
    .sort((a, b) => MATCH_STRENGTH_ORDER[a.matchStrength] - MATCH_STRENGTH_ORDER[b.matchStrength]);

  const toggleEntity = (entityId: string) => {
    setSelectedEntityIds((prev) =>
      prev.includes(entityId) ? prev.filter((x) => x !== entityId) : [...prev, entityId],
    );
  };

  const onApprove = async () => {
    try {
      await approve.mutateAsync({ id, entityIds: selectedEntityIds });
      onSuccess('Registration approved');
      onClose();
    } catch (err) {
      onError(err);
    }
  };

  const onReject = async () => {
    if (rejectReason.trim().length < 5) return;
    try {
      await reject.mutateAsync({ id, reason: rejectReason.trim() });
      onSuccess('Registration rejected');
      onClose();
    } catch (err) {
      onError(err);
    }
  };

  return (
    <Dialog open onOpenChange={(o) => (!o ? onClose() : undefined)}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Review portal registration</DialogTitle>
          <DialogDescription>
            Verify the requester and link them to one or more organisations before approving access.
          </DialogDescription>
        </DialogHeader>

        {detailQuery.isLoading && (
          <div className="flex items-center gap-2 py-6 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading registration…
          </div>
        )}

        {detailQuery.isError && (
          <p className="text-sm text-destructive">
            Could not load the registration. Close and retry from the queue.
          </p>
        )}

        {detailQuery.data && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-3 text-sm md:grid-cols-2">
              <div>
                <p className="text-muted-foreground">Reference</p>
                <p className="font-mono">{detailQuery.data.registrationReference}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Status</p>
                <p>
                  <StatusPill type="application" status={detailQuery.data.registrationStatus} />
                </p>
              </div>
              <div>
                <p className="text-muted-foreground">Signatory</p>
                <p>{detailQuery.data.authorizedSignatoryName}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Mobile / Email</p>
                <p className="font-mono text-xs">{detailQuery.data.mobile}</p>
                <p className="text-xs">{detailQuery.data.email}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Identifier</p>
                <p className="font-mono text-xs">
                  {detailQuery.data.requestedCin ??
                    detailQuery.data.requestedGstin ??
                    detailQuery.data.requestedLlpin ??
                    detailQuery.data.requestedPan ??
                    '—'}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground">Registered</p>
                <p>
                  <DateDisplay date={detailQuery.data.registeredAt} />
                </p>
              </div>
            </div>

            {mode === 'view' && (
              <div className="space-y-3">
                <p className="text-sm font-medium">Suggested entities</p>
                <p className="text-xs text-muted-foreground">
                  Sorted by match strength. Pick the entities the borrower should be granted access
                  to, then approve.
                </p>
                <div className="max-h-64 overflow-y-auto rounded-md border">
                  {sortedSuggestions.length === 0 ? (
                    <p className="p-4 text-sm text-muted-foreground">
                      No matching entities found. Approving will create no links; you may want to
                      reject instead.
                    </p>
                  ) : (
                    <ul className="divide-y">
                      {sortedSuggestions.map((s) => (
                        <li key={s.entityId} className="flex items-center gap-3 p-3">
                          <Checkbox
                            checked={selectedEntityIds.includes(s.entityId)}
                            onCheckedChange={() => toggleEntity(s.entityId)}
                            id={`ent-${s.entityId}`}
                          />
                          <label htmlFor={`ent-${s.entityId}`} className="flex-1 cursor-pointer">
                            <p className="text-sm font-medium">{s.legalName}</p>
                            <p className="text-xs text-muted-foreground">{idDescriptor(s)}</p>
                          </label>
                          <MatchStrengthBadge strength={s.matchStrength} />
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            )}

            {mode === 'reject' && (
              <div className="space-y-2">
                <Label htmlFor="reject-reason">Rejection reason</Label>
                <Textarea
                  id="reject-reason"
                  rows={4}
                  placeholder="Provide a clear reason — the borrower will see this."
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">Minimum 5 characters.</p>
              </div>
            )}
          </div>
        )}

        <DialogFooter className="flex flex-col-reverse gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            {mode !== 'view' && (
              <Button variant="ghost" onClick={() => setMode('view')}>
                Cancel
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
            {mode === 'view' && detailQuery.data?.registrationStatus === 'PENDING_APPROVAL' && (
              <>
                <Button
                  variant="outline"
                  onClick={() => setMode('reject')}
                  className="border-destructive/40 text-destructive hover:bg-destructive/10"
                >
                  <ShieldX className="mr-2 h-4 w-4" />
                  Reject…
                </Button>
                <Button
                  onClick={onApprove}
                  disabled={approve.isPending || selectedEntityIds.length === 0}
                  className="bg-emerald-600 hover:bg-emerald-700"
                >
                  {approve.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <ShieldCheck className="mr-2 h-4 w-4" />
                  )}
                  Approve ({selectedEntityIds.length})
                </Button>
              </>
            )}
            {mode === 'reject' && (
              <Button
                variant="destructive"
                onClick={onReject}
                disabled={reject.isPending || rejectReason.trim().length < 5}
              >
                {reject.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <ShieldX className="mr-2 h-4 w-4" />
                )}
                Confirm rejection
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function idDescriptor(s: EntitySuggestion): string {
  if (s.loanAccountNumber) {
    return `Loan ${s.loanAccountNumber} · Sanctioned ${s.sanctionedAmount ?? '—'}`;
  }
  if (s.cin) return `CIN ${s.cin}`;
  if (s.gstin) return `GSTIN ${s.gstin}`;
  if (s.pan) return `PAN ${s.pan}`;
  if (s.llpin) return `LLPIN ${s.llpin}`;
  return s.entityId;
}

function MatchStrengthBadge({ strength }: { strength: EntityMatchStrength }): JSX.Element {
  const label = strength.replace('_', ' ');
  const isExact = strength !== 'FUZZY_NAME';
  return <Badge variant={isExact ? 'default' : 'secondary'}>{label}</Badge>;
}
