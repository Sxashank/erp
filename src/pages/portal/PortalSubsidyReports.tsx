/**
 * Borrower Portal - claim center.
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
import { useEffect, useMemo, useState } from 'react';

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
import { usePortalSession } from '@/hooks/portal/usePortalSession';
import {
  useCreatePortalClaim,
  usePortalClaim,
  usePortalClaimDocumentTypes,
  useDownloadPortalClaimCsv,
  useDownloadPortalClaimCertificate,
  useDownloadPortalClaimReport,
  usePortalClaimEnrollments,
  usePortalClaims,
  usePortalClaimsWorkbench,
  useSubmitPortalClaim,
  useUploadPortalClaimDocument,
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

export default function PortalSubsidyReports(): JSX.Element {
  const { toast } = useToast();
  const { actorRole } = usePortalSession();
  const isBorrower = actorRole === 'scheme_borrower';
  const canCreateClaim = isBorrower;

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

  const title = isBorrower ? 'Claims' : 'Claims Monitoring';
  const subtitle = isBorrower
    ? 'Create borrower subsidy claims, submit draft periods, and track release status across enrolled loans.'
    : 'Monitor SFC claim status across submission, verification, and release stages.';

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
        <div className="flex flex-wrap justify-end gap-2">
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
        breadcrumbs={[{ label: 'Borrower Portal', to: '/portal/workbench' }, { label: 'Claims' }]}
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
  const documentTypesQuery = usePortalClaimDocumentTypes();
  const uploadDocument = useUploadPortalClaimDocument();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentName, setDocumentName] = useState('');
  const [documentCategory, setDocumentCategory] = useState('');

  const claim = claimQuery.data;
  const canUpload = claim?.status === 'DRAFT';
  const documentTypes = useMemo(() => documentTypesQuery.data ?? [], [documentTypesQuery.data]);

  useEffect(() => {
    if (!documentCategory && documentTypes[0]?.code) {
      setDocumentCategory(documentTypes[0].code);
    }
  }, [documentCategory, documentTypes]);

  const resetUploadState = () => {
    setSelectedFile(null);
    setDocumentName('');
    setDocumentCategory(documentTypes[0]?.code ?? '');
  };

  const handleUpload = async () => {
    if (!selectedFile || !documentCategory) {
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
                      <SelectValue placeholder="Select document type" />
                    </SelectTrigger>
                    <SelectContent>
                      {documentTypes.map((type) => (
                        <SelectItem key={type.code} value={type.code}>
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
                    placeholder="Sanction letter, account statement, SFC certificate"
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
              disabled={uploadDocument.isPending || !selectedFile || !documentCategory}
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
  const certificate = useDownloadPortalClaimCertificate(claimId);
  const isDownloading =
    csv.isDownloading || xlsx.isDownloading || pdf.isDownloading || certificate.isDownloading;
  const safeClaimReference = claimReference.replace(/[\\/:*?"<>|]+/g, '_');
  const downloadAs = async (format: 'csv' | 'xlsx' | 'pdf') => {
    const downloader = format === 'xlsx' ? xlsx : format === 'pdf' ? pdf : csv;
    await downloader.download(`${safeClaimReference}.${format}`);
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
      <Button
        variant="outline"
        size="sm"
        onClick={async () => {
          try {
            await certificate.download(`${safeClaimReference}-certificate.pdf`);
          } catch (err) {
            onError(err);
          }
        }}
        disabled={isDownloading}
      >
        {certificate.isDownloading ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <Download className="mr-2 h-4 w-4" />
        )}
        Certificate
      </Button>
    </>
  );
}

function periodKey(period: PortalEligibleClaimPeriod): string {
  return `${period.periodStart}:${period.periodEnd}`;
}
