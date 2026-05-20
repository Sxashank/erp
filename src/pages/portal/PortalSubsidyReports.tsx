/**
 * Scheme Portal — claim center / verification / release queue.
 */

import {
  Award,
  Download,
  FileSignature,
  Loader2,
  Paperclip,
  Pencil,
  Send,
  Upload,
} from 'lucide-react';
import { useMemo, useState } from 'react';

import {
  AmountDisplay,
  DataTable,
  DateDisplay,
  EmptyState,
  ErrorState,
  PageHeader,
  SkeletonTable,
  StatusPill,
  type Column,
} from '@/components/common';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { usePortalSession } from '@/hooks/portal/usePortalSession';
import {
  useCreatePortalClaim,
  usePortalClaim,
  useDownloadPortalClaimCsv,
  useDownloadPortalClaimReport,
  useInitiatePortalClaimRelease,
  useMarkPortalClaimReleased,
  usePortalClaimEnrollments,
  usePortalClaims,
  usePortalClaimsWorkbench,
  useSubmitPortalClaim,
  useUploadPortalClaimDocument,
  useVerifyPortalClaim,
} from '@/hooks/portal/useSubsidyReports';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import type {
  PortalClaim,
  PortalClaimEnrollment,
  PortalEligibleClaimPeriod,
} from '@/services/portalApi';

const ALL_ENROLLMENTS = '__ALL_ENROLLMENTS__';
const ALL_STATUSES = '__ALL_STATUSES__';
const CLAIM_DOCUMENT_TYPES = [
  { value: 'INTEREST_CALCULATION_SHEET', label: 'Interest calculation sheet' },
  { value: 'REPAYMENT_RECORD', label: 'Borrower repayment record' },
  { value: 'REGULAR_ACCOUNT_CERTIFICATE', label: 'Regular account certificate' },
  { value: 'NON_DUPLICATION_UNDERTAKING', label: 'Non-duplication undertaking' },
  { value: 'AUDITED_INTEREST_CERTIFICATE', label: 'Audited interest certificate' },
  { value: 'CLAIM_SUMMARY', label: 'Claim summary' },
];

export default function PortalSubsidyReports(): JSX.Element {
  const { toast } = useToast();
  const { actorRole } = usePortalSession();
  const isBorrower = actorRole === 'scheme_borrower';
  const canCreateClaim =
    actorRole === 'scheme_borrower' || actorRole === 'scheme_lender' || actorRole === 'scheme_admin';
  const canVerify = actorRole === 'scheme_smfcl_reviewer' || actorRole === 'scheme_admin';
  const canRelease = actorRole === 'scheme_smfcl_approver' || actorRole === 'scheme_admin';

  const [selectedEnrollmentId, setSelectedEnrollmentId] = useState<string>(ALL_ENROLLMENTS);
  const [statusFilter, setStatusFilter] = useState<string>(ALL_STATUSES);
  const [createOpen, setCreateOpen] = useState(false);
  const [documentsClaimId, setDocumentsClaimId] = useState<string | null>(null);

  const workbenchQuery = usePortalClaimsWorkbench();
  const enrollmentsQuery = usePortalClaimEnrollments();
  const claimsQuery = usePortalClaims({
    pageSize: 100,
    status: statusFilter === ALL_STATUSES ? undefined : statusFilter,
  });

  const enrollments = enrollmentsQuery.data ?? [];

  const filteredClaims = useMemo(() => {
    const claims = claimsQuery.data?.items ?? [];
    if (!isBorrower || selectedEnrollmentId === ALL_ENROLLMENTS) {
      return claims;
    }
    return claims.filter((claim) => claim.enrollmentId === selectedEnrollmentId);
  }, [claimsQuery.data?.items, isBorrower, selectedEnrollmentId]);

  const eligibleEnrollmentCount = enrollments.filter(
    (enrollment) =>
      enrollment.eligiblePeriods.filter((period) => !period.alreadyClaimed).length > 0,
  ).length;
  const firstDraftClaim = filteredClaims.find((claim) => claim.status === 'DRAFT');

  const title = isBorrower
    ? 'Claims'
    : canCreateClaim
      ? 'Lender Claim Submission'
    : canRelease
      ? 'Claim Release Queue'
      : canVerify
        ? 'Claim Verification Queue'
        : 'Claims Monitoring';
  const subtitle = isBorrower
    ? 'Create borrower subsidy claims, submit draft periods, and track release status across enrolled loans.'
    : canCreateClaim
      ? 'Submit IIF claim proposals with required lender certificates and repayment records.'
    : canRelease
      ? 'Mark verified subsidy claims as released and capture audited payment references.'
      : canVerify
        ? 'Review submitted subsidy claims and decide whether they should proceed to release.'
        : 'Monitor scheme claims across submission, verification, and release stages.';

  const columns: Column<PortalClaim>[] = [
    {
      key: 'claimReference',
      header: 'Claim #',
      render: (row) => <span className="font-medium">{row.claimReference}</span>,
    },
    {
      key: 'loanAccountNumber',
      header: 'Loan account',
      render: (row) => row.loanAccountNumber ?? '—',
    },
    {
      key: 'schemeCode',
      header: 'Scheme',
      render: (row) => row.schemeCode ?? '—',
    },
    {
      key: 'period',
      header: 'Period',
      render: (row) => (
        <span>
          <DateDisplay date={row.periodStart} /> – <DateDisplay date={row.periodEnd} />
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => <StatusPill type="application" status={row.status} />,
    },
    {
      key: 'amount',
      header: 'Subvention amount',
      align: 'right',
      render: (row) => <AmountDisplay amount={Number(row.applicableSubventionAmount)} />,
    },
    {
      key: 'releasedDate',
      header: 'Released',
      render: (row) => <DateDisplay date={row.releasedDate ?? null} />,
    },
    {
      key: 'actions',
      header: '',
      align: 'right',
      render: (row) => (
        <div className="flex justify-end gap-2">
          {isBorrower && row.status === 'DRAFT' ? (
            <>
              <Button variant="outline" size="sm" onClick={() => setDocumentsClaimId(row.id)}>
                <Pencil className="mr-2 h-4 w-4" />
                Edit draft
              </Button>
              <SubmitClaimButton
                claimId={row.id}
                hasDocuments={row.documents.length > 0}
                onError={(err) => showErrorToast(err, toast)}
              />
            </>
          ) : null}
          {canVerify && row.status === 'SUBMITTED' ? (
            <VerifyClaimButtons claimId={row.id} onError={(err) => showErrorToast(err, toast)} />
          ) : null}
          {canRelease && row.status === 'VERIFIED' ? (
            <InitiateReleaseButton claimId={row.id} onError={(err) => showErrorToast(err, toast)} />
          ) : null}
          {canRelease && row.status === 'RELEASE_IN_PROGRESS' ? (
            <MarkReleasedButton claimId={row.id} onError={(err) => showErrorToast(err, toast)} />
          ) : null}
          {isBorrower && row.status !== 'DRAFT' && row.documents.length > 0 ? (
            <Button variant="outline" size="sm" onClick={() => setDocumentsClaimId(row.id)}>
              <Paperclip className="mr-2 h-4 w-4" />
              Documents
            </Button>
          ) : null}
          <DownloadClaimButton
            claimId={row.id}
            claimReference={row.claimReference}
            onError={(err) => showErrorToast(err, toast)}
          />
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title={title}
        subtitle={subtitle}
        breadcrumbs={[{ label: 'Scheme Portal', to: '/portal/workbench' }, { label: 'Claims' }]}
        actions={
          canCreateClaim ? (
            <div className="flex flex-wrap justify-end gap-2">
              {firstDraftClaim ? (
                <Button variant="outline" onClick={() => setDocumentsClaimId(firstDraftClaim.id)}>
                  <Pencil className="mr-2 h-4 w-4" />
                  Edit draft
                </Button>
              ) : null}
              <Button
                className="bg-emerald-600 hover:bg-emerald-700"
                onClick={() => setCreateOpen(true)}
                disabled={eligibleEnrollmentCount === 0}
                title={
                  eligibleEnrollmentCount === 0
                    ? 'No unclaimed eligible claim periods are available.'
                    : undefined
                }
              >
                <FileSignature className="mr-2 h-4 w-4" />
                New claim
              </Button>
            </div>
          ) : undefined
        }
      />

      {workbenchQuery.isLoading ? (
        <SkeletonTable rows={1} columns={5} />
      ) : workbenchQuery.isError ? (
        <ErrorState error={workbenchQuery.error} onRetry={() => workbenchQuery.refetch()} />
      ) : workbenchQuery.data ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
          <StatsCard label="Draft claims" value={workbenchQuery.data.stats.draft} />
          <StatsCard label="Submitted" value={workbenchQuery.data.stats.submitted} />
          <StatsCard label="Verified" value={workbenchQuery.data.stats.verified} />
          <StatsCard
            label="Release in progress"
            value={workbenchQuery.data.stats.releaseInProgress}
          />
          <StatsCard label="Released" value={workbenchQuery.data.stats.released} />
          <StatsCard label="Eligible periods" value={workbenchQuery.data.stats.eligiblePeriods} />
        </div>
      ) : null}

      {isBorrower ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Enrollment filter</CardTitle>
          </CardHeader>
          <CardContent>
            {enrollmentsQuery.isLoading ? (
              <SkeletonTable rows={1} columns={2} />
            ) : enrollmentsQuery.isError ? (
              <ErrorState
                error={enrollmentsQuery.error}
                onRetry={() => enrollmentsQuery.refetch()}
              />
            ) : enrollments.length === 0 ? (
              <EmptyState
                icon={Award}
                title="No enrolled loans"
                subtitle="Borrower claims become available once a disbursed loan is enrolled in an active subvention scheme."
              />
            ) : (
              <Select value={selectedEnrollmentId} onValueChange={setSelectedEnrollmentId}>
                <SelectTrigger className="w-full md:w-[420px]">
                  <SelectValue placeholder="Choose an enrollment" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL_ENROLLMENTS}>All enrolled loans</SelectItem>
                  {enrollments.map((enrollment) => (
                    <SelectItem key={enrollment.enrollmentId} value={enrollment.enrollmentId}>
                      {enrollment.loanAccountNumber ?? 'Loan'} — {enrollment.schemeCode ?? 'Scheme'}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Claim status filter</CardTitle>
          </CardHeader>
          <CardContent>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full md:w-[320px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_STATUSES}>All statuses</SelectItem>
                <SelectItem value="SUBMITTED">Submitted</SelectItem>
                <SelectItem value="VERIFIED">Verified</SelectItem>
                <SelectItem value="RELEASE_IN_PROGRESS">Release in progress</SelectItem>
                <SelectItem value="RELEASED">Released</SelectItem>
                <SelectItem value="REJECTED">Rejected</SelectItem>
                <SelectItem value="CANCELLED">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </CardContent>
        </Card>
      )}

      {claimsQuery.isLoading ? (
        <SkeletonTable rows={5} columns={7} />
      ) : claimsQuery.isError ? (
        <ErrorState error={claimsQuery.error} onRetry={() => claimsQuery.refetch()} />
      ) : (
        <DataTable<PortalClaim>
          data={filteredClaims}
          columns={columns}
          getRowId={(row) => row.id}
          emptyTitle="No claims yet"
          emptySubtitle={
            isBorrower
              ? 'Create your first borrower claim once an eligible period is available.'
              : 'No claims match the current review filters.'
          }
        />
      )}

      {isBorrower ? (
        <CreateClaimDialog
          open={createOpen}
          onOpenChange={setCreateOpen}
          enrollments={enrollments}
          onError={(err) => showErrorToast(err, toast)}
        />
      ) : null}

      {documentsClaimId ? (
        <ClaimDocumentsDialog
          claimId={documentsClaimId}
          open={Boolean(documentsClaimId)}
          onOpenChange={(next) => {
            if (!next) {
              setDocumentsClaimId(null);
            }
          }}
          onError={(err) => showErrorToast(err, toast)}
        />
      ) : null}
    </div>
  );
}

function StatsCard({ label, value }: { label: string; value: number }): JSX.Element {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="text-sm text-muted-foreground">{label}</div>
        <div className="mt-2 text-3xl font-semibold">{value}</div>
      </CardContent>
    </Card>
  );
}

function CreateClaimDialog({
  open,
  onOpenChange,
  enrollments,
  onError,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  enrollments: PortalClaimEnrollment[];
  onError: (err: unknown) => void;
}): JSX.Element {
  const createClaim = useCreatePortalClaim();
  const [selectedEnrollmentId, setSelectedEnrollmentId] = useState<string>('');
  const [selectedPeriodKey, setSelectedPeriodKey] = useState<string>('');

  const eligibleEnrollments = useMemo(
    () =>
      enrollments.filter(
        (enrollment) =>
          enrollment.eligiblePeriods.filter((period) => !period.alreadyClaimed).length > 0,
      ),
    [enrollments],
  );

  const selectedEnrollment = eligibleEnrollments.find(
    (enrollment) => enrollment.enrollmentId === selectedEnrollmentId,
  );
  const eligiblePeriods = (selectedEnrollment?.eligiblePeriods ?? []).filter(
    (period) => !period.alreadyClaimed,
  );
  const selectedPeriod = eligiblePeriods.find((period) => periodKey(period) === selectedPeriodKey);

  const reset = () => {
    setSelectedEnrollmentId('');
    setSelectedPeriodKey('');
  };

  const handleCreate = async () => {
    if (!selectedEnrollment || !selectedPeriod) {
      return;
    }
    try {
      await createClaim.mutateAsync({
        enrollmentId: selectedEnrollment.enrollmentId,
        periodStart: selectedPeriod.periodStart,
        periodEnd: selectedPeriod.periodEnd,
        documents: [],
      });
      reset();
      onOpenChange(false);
    } catch (err) {
      onError(err);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) {
          reset();
        }
        onOpenChange(next);
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create borrower claim</DialogTitle>
          <DialogDescription>
            Select an enrolled loan and an eligible closed period to create a draft IIF claim.
          </DialogDescription>
        </DialogHeader>

        {eligibleEnrollments.length === 0 ? (
          <EmptyState
            icon={Award}
            title="No eligible periods available"
            subtitle="Claims can only be created when an enrolled loan completes a claimable period."
          />
        ) : (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="portal-claim-enrollment">Enrollment</Label>
              <Select
                value={selectedEnrollmentId}
                onValueChange={(value) => {
                  setSelectedEnrollmentId(value);
                  setSelectedPeriodKey('');
                }}
              >
                <SelectTrigger id="portal-claim-enrollment">
                  <SelectValue placeholder="Choose an enrolled loan" />
                </SelectTrigger>
                <SelectContent>
                  {eligibleEnrollments.map((enrollment) => (
                    <SelectItem key={enrollment.enrollmentId} value={enrollment.enrollmentId}>
                      {enrollment.loanAccountNumber ?? 'Loan'} — {enrollment.schemeCode ?? 'Scheme'}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="portal-claim-period">Eligible period</Label>
              <Select
                value={selectedPeriodKey}
                onValueChange={setSelectedPeriodKey}
                disabled={!selectedEnrollment}
              >
                <SelectTrigger id="portal-claim-period">
                  <SelectValue placeholder="Choose a claim period" />
                </SelectTrigger>
                <SelectContent>
                  {eligiblePeriods.map((period) => (
                    <SelectItem key={periodKey(period)} value={periodKey(period)}>
                      {period.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {selectedEnrollment ? (
              <div className="rounded-lg border bg-muted/30 p-4 text-sm">
                <div className="font-medium">
                  {selectedEnrollment.loanAccountNumber ?? 'Loan account'} —{' '}
                  {selectedEnrollment.schemeName ?? selectedEnrollment.schemeCode ?? 'Scheme'}
                </div>
                <div className="mt-1 text-muted-foreground">
                  Claimed to date:{' '}
                  <AmountDisplay amount={Number(selectedEnrollment.totalClaimedToDate)} />
                </div>
                <div className="mt-1 text-muted-foreground">
                  Released to date:{' '}
                  <AmountDisplay amount={Number(selectedEnrollment.totalPaidToDate)} />
                </div>
              </div>
            ) : null}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleCreate}
            disabled={createClaim.isPending || !selectedEnrollment || !selectedPeriod}
            className="bg-emerald-600 hover:bg-emerald-700"
          >
            {createClaim.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <FileSignature className="mr-2 h-4 w-4" />
            )}
            Save draft
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function SubmitClaimButton({
  claimId,
  hasDocuments,
  onError,
}: {
  claimId: string;
  hasDocuments: boolean;
  onError: (err: unknown) => void;
}): JSX.Element {
  const submitClaim = useSubmitPortalClaim();
  return (
    <Button
      variant="outline"
      size="sm"
      onClick={async () => {
        try {
          await submitClaim.mutateAsync({
            id: claimId,
            declarationSignedAt: new Date().toISOString(),
          });
        } catch (err) {
          onError(err);
        }
      }}
      disabled={submitClaim.isPending || !hasDocuments}
    >
      {submitClaim.isPending ? (
        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
      ) : (
        <Send className="mr-2 h-4 w-4" />
      )}
      Submit
    </Button>
  );
}

function ClaimDocumentsDialog({
  claimId,
  open,
  onOpenChange,
  onError,
}: {
  claimId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onError: (err: unknown) => void;
}): JSX.Element {
  const claimQuery = usePortalClaim(claimId);
  const uploadDocument = useUploadPortalClaimDocument();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentName, setDocumentName] = useState('');
  const [documentCategory, setDocumentCategory] = useState(CLAIM_DOCUMENT_TYPES[0].value);

  const claim = claimQuery.data;
  const canUpload = claim?.status === 'DRAFT';

  const resetUploadState = () => {
    setSelectedFile(null);
    setDocumentName('');
    setDocumentCategory(CLAIM_DOCUMENT_TYPES[0].value);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      return;
    }
    try {
      await uploadDocument.mutateAsync({
        id: claimId,
        file: selectedFile,
        documentName: documentName.trim() || selectedFile.name,
        documentCategory,
      });
      resetUploadState();
      await claimQuery.refetch();
    } catch (err) {
      onError(err);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) {
          resetUploadState();
        }
        onOpenChange(next);
      }}
    >
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {claim?.status === 'DRAFT' ? 'Edit draft claim' : 'Claim documents'}
          </DialogTitle>
          <DialogDescription>
            Supporting documents are stored in the shared DMS with audit history and controlled
            downloads.
          </DialogDescription>
        </DialogHeader>

        {claimQuery.isLoading ? (
          <SkeletonTable rows={2} columns={3} />
        ) : claimQuery.isError ? (
          <ErrorState error={claimQuery.error} onRetry={() => claimQuery.refetch()} />
        ) : claim ? (
          <div className="space-y-4">
            <div className="rounded-lg border bg-muted/30 p-4 text-sm">
              <div className="font-medium">{claim.claimReference}</div>
              <div className="mt-1 text-muted-foreground">Status: {claim.status}</div>
            </div>

            {canUpload ? (
              <div className="grid gap-4 md:grid-cols-[1fr_1fr_auto]">
                <div className="space-y-2">
                  <Label htmlFor="claim-document-category">Document type</Label>
                  <Select value={documentCategory} onValueChange={setDocumentCategory}>
                    <SelectTrigger id="claim-document-category">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {CLAIM_DOCUMENT_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="claim-document-name">Document name</Label>
                  <Input
                    id="claim-document-name"
                    value={documentName}
                    onChange={(event) => setDocumentName(event.target.value)}
                    placeholder="Sanction letter, account statement, lender certificate"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="claim-document-file">File</Label>
                  <Input
                    id="claim-document-file"
                    type="file"
                    onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
                  />
                </div>
              </div>
            ) : null}

            {claim.documents.length === 0 ? (
              <EmptyState
                icon={Paperclip}
                title="No claim documents uploaded"
                subtitle={
                  canUpload
                    ? 'Upload supporting documents before submitting the draft claim.'
                    : 'No supporting documents were attached to this claim.'
                }
              />
            ) : (
              <div className="space-y-3">
                {claim.documents.map((document, index) => (
                  <div
                    key={document.documentId ?? `${document.name}-${index}`}
                    className="flex items-center justify-between rounded-lg border p-3"
                  >
                    <div>
                      <div className="font-medium">{document.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {document.fileName ?? document.name}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        <DateDisplay date={document.uploadedAt ?? null} />
                      </div>
                    </div>
                    {document.downloadUrl ? (
                      <Button asChild variant="outline" size="sm">
                        <a href={document.downloadUrl} target="_blank" rel="noreferrer">
                          <Download className="mr-2 h-4 w-4" />
                          Download
                        </a>
                      </Button>
                    ) : (
                      <span className="text-sm text-muted-foreground">Unavailable</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : null}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          {canUpload ? (
            <Button
              onClick={handleUpload}
              disabled={uploadDocument.isPending || !selectedFile}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              {uploadDocument.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Upload className="mr-2 h-4 w-4" />
              )}
              Upload document
            </Button>
          ) : null}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function VerifyClaimButtons({
  claimId,
  onError,
}: {
  claimId: string;
  onError: (err: unknown) => void;
}): JSX.Element {
  const verifyClaim = useVerifyPortalClaim();
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState('');

  async function approve() {
    try {
      await verifyClaim.mutateAsync({ id: claimId, decision: 'APPROVE' });
    } catch (err) {
      onError(err);
    }
  }

  async function reject() {
    try {
      await verifyClaim.mutateAsync({
        id: claimId,
        decision: 'REJECT',
        reason,
      });
      setOpen(false);
      setReason('');
    } catch (err) {
      onError(err);
    }
  }

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => void approve()}
        disabled={verifyClaim.isPending}
      >
        Verify
      </Button>
      <Button variant="destructive" size="sm" onClick={() => setOpen(true)}>
        Reject
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject claim</DialogTitle>
            <DialogDescription>
              Provide the rejection reason that should be visible in the claim history.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="claim-reject-reason">Reason</Label>
            <Textarea
              id="claim-reject-reason"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              rows={4}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              disabled={reason.trim().length < 5}
              onClick={() => void reject()}
            >
              Reject claim
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

function InitiateReleaseButton({
  claimId,
  onError,
}: {
  claimId: string;
  onError: (err: unknown) => void;
}): JSX.Element {
  const initiateRelease = useInitiatePortalClaimRelease();
  const [open, setOpen] = useState(false);
  const [instructionReference, setInstructionReference] = useState('');
  const [instructionNotes, setInstructionNotes] = useState('');

  async function submit() {
    try {
      await initiateRelease.mutateAsync({
        id: claimId,
        releaseInstructionReference: instructionReference.trim(),
        releaseInitiatedDate: new Date().toISOString().slice(0, 10),
        releaseInstructionNotes: instructionNotes.trim() || undefined,
      });
      setOpen(false);
      setInstructionReference('');
      setInstructionNotes('');
    } catch (err) {
      onError(err);
    }
  }

  return (
    <>
      <Button variant="outline" size="sm" onClick={() => setOpen(true)}>
        Initiate release
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Initiate claim release</DialogTitle>
            <DialogDescription>
              Capture the release instruction that sends this verified claim into the execution
              queue.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="claim-release-instruction-reference">
              Release instruction reference
            </Label>
            <Input
              id="claim-release-instruction-reference"
              value={instructionReference}
              onChange={(event) => setInstructionReference(event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="claim-release-instruction-notes">Instruction notes</Label>
            <Textarea
              id="claim-release-instruction-notes"
              value={instructionNotes}
              onChange={(event) => setInstructionNotes(event.target.value)}
              rows={4}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              disabled={initiateRelease.isPending || instructionReference.trim().length === 0}
              onClick={() => void submit()}
            >
              Start release
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

function MarkReleasedButton({
  claimId,
  onError,
}: {
  claimId: string;
  onError: (err: unknown) => void;
}): JSX.Element {
  const markReleased = useMarkPortalClaimReleased();
  const [open, setOpen] = useState(false);
  const [releaseReference, setReleaseReference] = useState('');

  async function submit() {
    try {
      await markReleased.mutateAsync({
        id: claimId,
        releaseReference: releaseReference.trim(),
        releasedDate: new Date().toISOString().slice(0, 10),
      });
      setOpen(false);
      setReleaseReference('');
    } catch (err) {
      onError(err);
    }
  }

  return (
    <>
      <Button variant="outline" size="sm" onClick={() => setOpen(true)}>
        Mark released
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Mark claim released</DialogTitle>
            <DialogDescription>
              Record the final bank / release reference after the subsidy transfer is completed.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="claim-release-reference">Release reference</Label>
            <Input
              id="claim-release-reference"
              value={releaseReference}
              onChange={(event) => setReleaseReference(event.target.value)}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              disabled={markReleased.isPending || releaseReference.trim().length === 0}
              onClick={() => void submit()}
            >
              Confirm released
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

function DownloadClaimButton({
  claimId,
  claimReference,
  onError,
}: {
  claimId: string;
  claimReference: string;
  onError: (err: unknown) => void;
}): JSX.Element {
  const csv = useDownloadPortalClaimCsv(claimId);
  const xlsx = useDownloadPortalClaimReport(claimId, 'xlsx');
  const pdf = useDownloadPortalClaimReport(claimId, 'pdf');
  const isDownloading = csv.isDownloading || xlsx.isDownloading || pdf.isDownloading;
  const downloadAs = async (format: 'csv' | 'xlsx' | 'pdf') => {
    const downloader = format === 'xlsx' ? xlsx : format === 'pdf' ? pdf : csv;
    await downloader.download(`${claimReference}.${format}`);
  };
  return (
    <>
      {(['csv', 'xlsx', 'pdf'] as const).map((format) => (
        <Button
          key={format}
          variant="outline"
          size="sm"
          onClick={async () => {
            try {
              await downloadAs(format);
            } catch (err) {
              onError(err);
            }
          }}
          disabled={isDownloading}
        >
          {isDownloading ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Download className="mr-2 h-4 w-4" />
          )}
          {format.toUpperCase()}
        </Button>
      ))}
    </>
  );
}

function periodKey(period: PortalEligibleClaimPeriod): string {
  return `${period.periodStart}:${period.periodEnd}`;
}
