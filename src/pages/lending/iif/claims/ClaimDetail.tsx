/**
 * IIF Claim — detail page with state-machine actions.
 *
 * Maker/checker actions per CLAUDE.md §8.4 / §9.5. Destructive actions
 * (Cancel) require a typed confirmation. Permissions gate the verify button.
 */

import { CheckCircle2, Download, FileSpreadsheet, FileText, Send, X } from 'lucide-react';
import { useState } from 'react';
import { useParams } from 'react-router-dom';

import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { DetailGrid } from '@/components/common/DetailGrid';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import {
  useCancelClaim,
  useClaim,
  useInitiateClaimRelease,
  useMarkClaimReleased,
  useSubmitClaim,
  useVerifyClaim,
} from '@/hooks/lending/useIif';
import { useToast } from '@/hooks/use-toast';
import { usePermission } from '@/hooks/usePermission';
import { claimsApi, type ClaimStatus } from '@/services/lending/iifApi';

function statusVariant(status: ClaimStatus): {
  className: string;
  label: string;
} {
  switch (status) {
    case 'DRAFT':
      return { className: 'bg-slate-100 text-slate-700 border-slate-300', label: 'Draft' };
    case 'SUBMITTED':
      return { className: 'bg-blue-100 text-blue-800 border-blue-300', label: 'Submitted' };
    case 'VERIFIED':
      return { className: 'bg-purple-100 text-purple-800 border-purple-300', label: 'Verified' };
    case 'RELEASE_IN_PROGRESS':
      return {
        className: 'bg-amber-100 text-amber-800 border-amber-300',
        label: 'Release in Progress',
      };
    case 'RELEASED':
      return { className: 'bg-green-100 text-green-800 border-green-300', label: 'Released' };
    case 'REJECTED':
      return { className: 'bg-red-100 text-red-800 border-red-300', label: 'Rejected' };
    case 'CANCELLED':
      return { className: 'bg-slate-200 text-slate-700 border-slate-400', label: 'Cancelled' };
  }
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

export default function ClaimDetail(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  const { toast } = useToast();
  const canVerify = usePermission('subvention.verify');

  const { data: claim, isLoading, isError, error, refetch } = useClaim(id);

  const submitMut = useSubmitClaim({
    onSuccess: () => toast({ title: 'Claim submitted for verification' }),
  });
  const verifyMut = useVerifyClaim({
    onSuccess: () => toast({ title: 'Claim verified' }),
  });
  const initiateReleaseMut = useInitiateClaimRelease({
    onSuccess: () => toast({ title: 'Claim moved to release in progress' }),
  });
  const markReleasedMut = useMarkClaimReleased({
    onSuccess: () => toast({ title: 'Claim marked released' }),
  });
  const cancelMut = useCancelClaim({
    onSuccess: () => toast({ title: 'Claim cancelled' }),
  });

  const [initiateOpen, setInitiateOpen] = useState(false);
  const [instructionReference, setInstructionReference] = useState('');
  const [instructionNotes, setInstructionNotes] = useState('');
  const [releasedOpen, setReleasedOpen] = useState(false);
  const [releaseReference, setReleaseReference] = useState('');
  const [releasedDate, setReleasedDate] = useState('');
  const [cancelOpen, setCancelOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState('');
  const [downloading, setDownloading] = useState<'csv' | null>(null);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Claim"
          breadcrumbs={[
            { label: 'Lending', to: '/admin/lending' },
            { label: 'Interest Subvention' },
            { label: 'Claims', to: '/admin/lending/iif/claims' },
            { label: '…' },
          ]}
        />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (isError || !claim) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Claim"
          breadcrumbs={[
            { label: 'Lending', to: '/admin/lending' },
            { label: 'Interest Subvention' },
            { label: 'Claims', to: '/admin/lending/iif/claims' },
            { label: 'Not found' },
          ]}
        />
        <ErrorState error={error} onRetry={refetch} />
      </div>
    );
  }

  const v = statusVariant(claim.status);

  const handleSubmit = () => {
    if (!id) return;
    submitMut.mutate(id);
  };
  const handleVerify = () => {
    if (!id) return;
    verifyMut.mutate({ id, decision: 'APPROVE' });
  };
  const handleInitiateRelease = () => {
    if (!id) return;
    initiateReleaseMut.mutate(
      {
        id,
        payload: {
          releaseInstructionReference: instructionReference,
          releaseInitiatedDate: new Date().toISOString().slice(0, 10),
          releaseInstructionNotes: instructionNotes || undefined,
        },
      },
      {
        onSuccess: () => {
          setInitiateOpen(false);
          setInstructionReference('');
          setInstructionNotes('');
        },
      },
    );
  };
  const handleMarkReleased = () => {
    if (!id) return;
    markReleasedMut.mutate(
      { id, payload: { releaseReference, releasedDate } },
      {
        onSuccess: () => {
          setReleasedOpen(false);
          setReleaseReference('');
          setReleasedDate('');
        },
      },
    );
  };
  const handleCancel = () => {
    if (!id) return;
    cancelMut.mutate(
      { id, reason: cancelReason },
      {
        onSuccess: () => {
          setCancelOpen(false);
          setCancelReason('');
        },
      },
    );
  };

  const handleDownload = async (kind: 'csv') => {
    if (!id) return;
    setDownloading(kind);
    try {
      const blob = await claimsApi.downloadReportCsv(id);
      triggerDownload(blob, `${claim.claimReference}.${kind}`);
    } catch (e) {
      toast({
        title: 'Download failed',
        variant: 'destructive',
        description: (e as Error)?.message,
      });
    } finally {
      setDownloading(null);
    }
  };

  const isTerminal =
    claim.status === 'RELEASED' || claim.status === 'REJECTED' || claim.status === 'CANCELLED';

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Claim ${claim.claimReference}`}
        subtitle={`Loan ${claim.loanAccountNumber} · Scheme ${claim.schemeCode}`}
        breadcrumbs={[
          { label: 'Lending', to: '/admin/lending' },
          { label: 'Interest Subvention' },
          { label: 'Claims', to: '/admin/lending/iif/claims' },
          { label: claim.claimReference },
        ]}
        actions={
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline" className={v.className}>
              {v.label}
            </Badge>
            <Button
              variant="outline"
              onClick={() => handleDownload('csv')}
              disabled={downloading === 'csv'}
            >
              <Download className="mr-2 h-4 w-4" />
              Download CSV report
            </Button>
            {claim.status === 'DRAFT' && (
              <Button onClick={handleSubmit} disabled={submitMut.isPending}>
                <Send className="mr-2 h-4 w-4" />
                Submit for verification
              </Button>
            )}
            {claim.status === 'SUBMITTED' && canVerify && (
              <Button onClick={handleVerify} disabled={verifyMut.isPending}>
                <CheckCircle2 className="mr-2 h-4 w-4" />
                Mark verified
              </Button>
            )}
            {claim.status === 'VERIFIED' && (
              <Button onClick={() => setInitiateOpen(true)}>
                <FileSpreadsheet className="mr-2 h-4 w-4" />
                Initiate release
              </Button>
            )}
            {claim.status === 'RELEASE_IN_PROGRESS' && (
              <Button onClick={() => setReleasedOpen(true)}>
                <CheckCircle2 className="mr-2 h-4 w-4" />
                Mark released
              </Button>
            )}
            {!isTerminal && (
              <Button
                variant="outline"
                onClick={() => setCancelOpen(true)}
                disabled={cancelMut.isPending}
              >
                <X className="mr-2 h-4 w-4" />
                Cancel
              </Button>
            )}
          </div>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>Computation</CardTitle>
        </CardHeader>
        <CardContent>
          <DetailGrid
            fields={[
              {
                label: 'Period',
                value: (
                  <>
                    <DateDisplay date={claim.periodStart} /> —{' '}
                    <DateDisplay date={claim.periodEnd} />
                  </>
                ),
              },
              { label: 'Frequency', value: claim.claimFrequency },
              {
                label: 'Interest paid in period',
                value: <AmountDisplay amount={claim.interestPaidInPeriod} />,
              },
              {
                label: 'Applicable subvention',
                value: <AmountDisplay amount={claim.applicableSubventionAmount} size="lg" />,
              },
            ]}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Lifecycle</CardTitle>
        </CardHeader>
        <CardContent>
          <DetailGrid
            fields={[
              {
                label: 'Submitted',
                value: claim.submittedDate ? <DateDisplay date={claim.submittedDate} /> : '—',
              },
              {
                label: 'Verified',
                value: claim.verifiedDate ? <DateDisplay date={claim.verifiedDate} /> : '—',
              },
              {
                label: 'Release initiated',
                value: claim.releaseInitiatedDate ? (
                  <DateDisplay date={claim.releaseInitiatedDate} />
                ) : (
                  '—'
                ),
              },
              {
                label: 'Release instruction reference',
                value: claim.releaseInstructionReference ?? '—',
              },
              {
                label: 'Released',
                value: claim.releasedDate ? <DateDisplay date={claim.releasedDate} /> : '—',
              },
              { label: 'Release reference', value: claim.releaseReference ?? '—' },
              {
                label: 'Release notes',
                value: claim.releaseInstructionNotes ?? '—',
              },
              {
                label: 'Rejection reason',
                value: claim.rejectionReason ?? '—',
              },
              {
                label: 'Declaration signed by',
                value: claim.declarationSignedBy ?? '—',
              },
              {
                label: 'Declaration signed at',
                value: claim.declarationSignedAt ? (
                  <DateDisplay date={claim.declarationSignedAt} showTime />
                ) : (
                  '—'
                ),
              },
            ]}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Declaration</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-relaxed text-muted-foreground">
            I certify that the interest paid in the above period is correctly recorded, the loan
            account is in good standing as per scheme eligibility rules, and the applicable
            subvention amount has been computed by the system at the prevailing scheme rate. I
            authorize this organisation to submit this claim to the administering ministry /
            implementing agency on the NBFC&apos;s behalf.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Documents</CardTitle>
        </CardHeader>
        <CardContent>
          {claim.documents.length === 0 ? (
            <p className="text-sm text-muted-foreground">No documents attached.</p>
          ) : (
            <ul className="space-y-1 text-sm">
              {claim.documents.map((d) => (
                <li key={d.path} className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  <span>{d.name}</span>
                  <span className="text-xs text-muted-foreground">
                    (uploaded <DateDisplay date={d.uploadedAt} />)
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {/* Initiate release modal */}
      <Dialog open={initiateOpen} onOpenChange={setInitiateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Initiate release</DialogTitle>
            <DialogDescription>
              Capture the release instruction details before execution starts.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-2">
              <Label>Release instruction reference *</Label>
              <Input
                value={instructionReference}
                onChange={(e) => setInstructionReference(e.target.value)}
                placeholder="e.g. SMFCL/REL/2026/041"
              />
            </div>
            <div className="space-y-2">
              <Label>Instruction notes</Label>
              <Textarea
                value={instructionNotes}
                onChange={(e) => setInstructionNotes(e.target.value)}
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setInitiateOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleInitiateRelease}
              disabled={!instructionReference || initiateReleaseMut.isPending}
            >
              <FileSpreadsheet className="mr-2 h-4 w-4" />
              Start release
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Mark released modal */}
      <Dialog open={releasedOpen} onOpenChange={setReleasedOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Mark claim released</DialogTitle>
            <DialogDescription>
              Record the final release reference and date after disbursement completes.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-2">
              <Label>Release reference *</Label>
              <Input
                value={releaseReference}
                onChange={(e) => setReleaseReference(e.target.value)}
                placeholder="e.g. SBIN20260512XYZ"
              />
            </div>
            <div className="space-y-2">
              <Label>Released date *</Label>
              <Input
                type="date"
                value={releasedDate}
                onChange={(e) => setReleasedDate(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setReleasedOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleMarkReleased}
              disabled={!releaseReference || !releasedDate || markReleasedMut.isPending}
            >
              <CheckCircle2 className="mr-2 h-4 w-4" />
              Confirm released
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Cancel confirm */}
      <ConfirmDialog
        open={cancelOpen}
        onOpenChange={setCancelOpen}
        title="Cancel claim?"
        description={
          <div className="space-y-2">
            <p className="text-sm">
              This claim will be marked as cancelled and cannot be revived. The underlying
              enrollment is unaffected.
            </p>
            <div>
              <Label className="text-sm">Reason *</Label>
              <Textarea
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                rows={3}
              />
            </div>
          </div>
        }
        confirmLabel="Cancel claim"
        variant="destructive"
        requireConfirmation={claim.claimReference}
        loading={cancelMut.isPending}
        onConfirm={handleCancel}
      />
    </div>
  );
}
