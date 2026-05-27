/**
 * Borrower Portal - Application detail and borrower actions.
 */

import { Download, Upload } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import {
  AmountDisplay,
  DataTable,
  DateDisplay,
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
  usePortalApplication,
  usePortalApplicationDocuments,
  useResubmitPortalApplication,
  useSubmitPortalApplication,
  useUploadApplicationDocument,
  useWithdrawPortalApplication,
} from '@/hooks/portal/useApplications';
import { usePortalSession } from '@/hooks/portal/usePortalSession';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import type { PortalApplicationDocument } from '@/services/portalApi';

interface UtilizationRow {
  categoryId: string;
  categoryLabel: string;
  amount: string;
  approvedAmount?: string | null;
  remarks?: string | null;
}

type ReasonAction = 'withdraw';

export default function PortalApplicationDetail(): JSX.Element {
  const { toast } = useToast();
  const { actorRole } = usePortalSession();
  const { id } = useParams<{ id: string }>();
  const appQuery = usePortalApplication(id);
  const docsQuery = usePortalApplicationDocuments(id);
  const submitApplication = useSubmitPortalApplication();
  const resubmitApplication = useResubmitPortalApplication();
  const withdrawApplication = useWithdrawPortalApplication();
  const uploadDocument = useUploadApplicationDocument();

  const [reasonAction, setReasonAction] = useState<ReasonAction | null>(null);
  const [reason, setReason] = useState('');
  const [selectedDocumentCode, setSelectedDocumentCode] = useState('BORROWER_UPLOAD');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const application = appQuery.data;
  const schemeStatus = application?.schemeStatus ?? '';
  const documentRequirements = useMemo(
    () => application?.documentRequirements ?? [],
    [application?.documentRequirements],
  );
  const hasMissingMandatoryDocuments = documentRequirements.some(
    (requirement) => requirement.isMandatory && requirement.missing,
  );
  const isBorrower = actorRole === 'scheme_borrower';

  useEffect(() => {
    if (documentRequirements.length === 0) {
      return;
    }
    setSelectedDocumentCode((current) => {
      if (
        current !== 'BORROWER_UPLOAD' &&
        documentRequirements.some((requirement) => requirement.code === current)
      ) {
        return current;
      }
      const nextRequirement =
        documentRequirements.find((requirement) => requirement.missing) ?? documentRequirements[0];
      return nextRequirement?.code ?? 'BORROWER_UPLOAD';
    });
  }, [documentRequirements]);

  const utilizationRows: UtilizationRow[] = (application?.fundUtilization ?? []).map((l) => ({
    categoryId: l.categoryId,
    categoryLabel: l.categoryLabel ?? l.categoryId,
    amount: l.amount,
    approvedAmount: l.approvedAmount,
    remarks: l.remarks,
  }));

  const utilizationColumns: Column<UtilizationRow>[] = [
    {
      key: 'categoryLabel',
      header: 'Category',
      render: (r) => r.categoryLabel,
    },
    {
      key: 'amount',
      header: 'Requested',
      align: 'right',
      render: (r) => <AmountDisplay amount={Number(r.amount)} />,
    },
    {
      key: 'approvedAmount',
      header: 'Approved',
      align: 'right',
      render: (r) =>
        r.approvedAmount == null ? (
          <span className="text-muted-foreground">—</span>
        ) : (
          <AmountDisplay amount={Number(r.approvedAmount)} />
        ),
    },
    {
      key: 'remarks',
      header: 'Remarks',
      render: (r) => r.remarks ?? '',
    },
  ];

  const docColumns: Column<PortalApplicationDocument>[] = [
    {
      key: 'fileName',
      header: 'Document',
      render: (d) => <span className="font-medium">{d.documentName ?? d.fileName}</span>,
    },
    {
      key: 'documentType',
      header: 'Type',
      render: (d) => d.documentCode ?? d.documentType ?? '—',
    },
    {
      key: 'uploadedAt',
      header: 'Uploaded',
      render: (d) => <DateDisplay date={d.uploadDate ?? d.uploadedAt} />,
    },
    {
      key: 'actions',
      header: '',
      align: 'right',
      render: (d) =>
        d.downloadUrl ? (
          <Button asChild variant="outline" size="sm">
            <a href={d.downloadUrl} target="_blank" rel="noreferrer">
              <Download className="mr-2 h-4 w-4" />
              Download
            </a>
          </Button>
        ) : (
          <span className="text-sm text-muted-foreground">Pending</span>
        ),
    },
  ];

  const requirementColumns: Column<(typeof documentRequirements)[number]>[] = [
    {
      key: 'name',
      header: 'Requirement',
      render: (requirement) => (
        <div>
          <div className="font-medium">{requirement.name}</div>
          <div className="text-sm text-muted-foreground">{requirement.category}</div>
        </div>
      ),
    },
    {
      key: 'requiredAtStage',
      header: 'Stage',
      render: (requirement) => requirement.requiredAtStage,
    },
    {
      key: 'uploadedCount',
      header: 'Uploaded',
      align: 'right',
      render: (requirement) => `${requirement.uploadedCount} / ${requirement.minFileCount}`,
    },
    {
      key: 'status',
      header: 'Status',
      render: (requirement) =>
        requirement.missing ? (
          <span className="font-medium text-amber-700">Missing</span>
        ) : requirement.isUploaded ? (
          <span className="font-medium text-emerald-700">Ready</span>
        ) : (
          <span className="text-muted-foreground">Optional</span>
        ),
    },
  ];

  async function runAction(action: 'submit' | 'resubmit') {
    if (!application) return;
    try {
      if (action === 'submit') {
        await submitApplication.mutateAsync(application.id);
      } else {
        await resubmitApplication.mutateAsync(application.id);
      }
      await appQuery.refetch();
      toast({
        title: 'Application updated',
        description: 'The SFC application status was updated successfully.',
      });
    } catch (err) {
      showErrorToast(err, toast);
    }
  }

  async function submitReasonAction() {
    if (!application || reason.trim().length < 5) {
      return;
    }
    try {
      if (reasonAction === 'withdraw') {
        await withdrawApplication.mutateAsync({ id: application.id, reason: reason.trim() });
      }
      setReason('');
      setReasonAction(null);
      await appQuery.refetch();
      toast({
        title: 'Application updated',
        description: 'The SFC application status was updated successfully.',
      });
    } catch (err) {
      showErrorToast(err, toast);
    }
  }

  async function uploadSelectedDocument() {
    if (!application || !selectedFile) {
      return;
    }
    const selectedRequirement = documentRequirements.find(
      (requirement) => requirement.code === selectedDocumentCode,
    );
    try {
      await uploadDocument.mutateAsync({
        applicationId: application.id,
        file: selectedFile,
        documentType: selectedDocumentCode,
        documentName: selectedRequirement?.name ?? selectedFile.name,
      });
      setSelectedFile(null);
      await Promise.all([docsQuery.refetch(), appQuery.refetch()]);
      toast({
        title: 'Document uploaded',
        description: 'The application document was uploaded successfully.',
      });
    } catch (err) {
      showErrorToast(err, toast);
    }
  }

  const headerActions = application ? (
    <div className="flex flex-wrap items-center gap-2">
      <StatusPill type="application" status={application.schemeStatus} />
      <Link to={`/portal/applications/${application.id}/queries`}>
        <Button variant="outline" size="sm">
          Queries
        </Button>
      </Link>
      <Link to={`/portal/applications/${application.id}/kfs`}>
        <Button variant="outline" size="sm">
          KFS
        </Button>
      </Link>
      {isBorrower && schemeStatus === 'DRAFT' ? (
        <Button
          className="bg-emerald-600 hover:bg-emerald-700"
          onClick={() => void runAction('submit')}
          disabled={submitApplication.isPending || hasMissingMandatoryDocuments}
        >
          Submit
        </Button>
      ) : null}
      {isBorrower && schemeStatus === 'QUERY_PENDING' ? (
        <Button
          className="bg-emerald-600 hover:bg-emerald-700"
          onClick={() => void runAction('resubmit')}
          disabled={resubmitApplication.isPending || hasMissingMandatoryDocuments}
        >
          Resubmit
        </Button>
      ) : null}
      {isBorrower &&
      !['APPROVED', 'REJECTED', 'CLOSED', 'SANCTION_ISSUED', 'CLAIM_OPEN', 'RELEASED'].includes(
        schemeStatus,
      ) ? (
        <Button variant="outline" onClick={() => setReasonAction('withdraw')}>
          Withdraw
        </Button>
      ) : null}
    </div>
  ) : undefined;

  return (
    <div className="space-y-6">
      <PageHeader
        title={application?.applicationNumber ?? 'Application'}
        subtitle={application?.productName ?? 'Loading…'}
        breadcrumbs={[
          { label: 'Borrower Portal', to: '/portal/workbench' },
          { label: 'Applications', to: '/portal/applications' },
          { label: application?.applicationNumber ?? 'Detail' },
        ]}
        actions={headerActions}
      />

      {appQuery.isLoading ? <SkeletonTable rows={4} columns={2} /> : null}
      {appQuery.isError ? (
        <ErrorState error={appQuery.error} onRetry={() => appQuery.refetch()} />
      ) : null}

      {application ? (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Application summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
                <div>
                  <p className="text-muted-foreground">Entity</p>
                  <p className="font-medium">{application.entityLegalName}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Requested amount</p>
                  <p className="font-medium">
                    <AmountDisplay amount={Number(application.requestedAmount)} />
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Tenure</p>
                  <p className="font-medium">{application.tenureMonths} months</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Status</p>
                  <div className="font-medium">
                    <StatusPill type="application" status={application.schemeStatus} />
                  </div>
                </div>
                <div>
                  <p className="text-muted-foreground">Submitted</p>
                  <p className="font-medium">
                    <DateDisplay date={application.submittedAt} />
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Decision</p>
                  <p className="font-medium">
                    <DateDisplay date={application.decisionAt} />
                  </p>
                </div>
              </div>
              <div className="mt-4 border-t pt-4">
                <p className="text-sm text-muted-foreground">Purpose</p>
                <p className="mt-1 whitespace-pre-line text-sm">{application.purposeDescription}</p>
              </div>
              <div className="mt-4 grid grid-cols-1 gap-4 border-t pt-4 md:grid-cols-2">
                <div>
                  <p className="text-sm text-muted-foreground">Project</p>
                  <p className="mt-1 text-sm font-medium">{application.projectName ?? '—'}</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {application.projectLocation ?? 'Location not provided'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {application.reviewRemarks || application.rejectionReason ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Review notes</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                {application.reviewRemarks ? (
                  <div>
                    <p className="text-muted-foreground">Latest review remarks</p>
                    <p className="mt-1 whitespace-pre-line">{application.reviewRemarks}</p>
                  </div>
                ) : null}
                {application.rejectionReason ? (
                  <div>
                    <p className="text-muted-foreground">Rejection reason</p>
                    <p className="mt-1 whitespace-pre-line">{application.rejectionReason}</p>
                  </div>
                ) : null}
              </CardContent>
            </Card>
          ) : null}

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Fund utilisation</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable<UtilizationRow>
                data={utilizationRows}
                columns={utilizationColumns}
                getRowId={(r) => r.categoryId}
                emptyTitle="No fund-utilisation lines"
                emptySubtitle="The borrower has not yet provided a utilisation breakdown."
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Application-stage document requirements</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable<(typeof documentRequirements)[number]>
                data={documentRequirements}
                columns={requirementColumns}
                getRowId={(requirement) => requirement.code}
                emptyTitle="No document checklist configured"
                emptySubtitle="This SFC product does not yet have an application-stage checklist."
              />
              {hasMissingMandatoryDocuments ? (
                <p className="mt-4 text-sm text-amber-700">
                  Submit and resubmit stay locked until every mandatory requirement is uploaded.
                </p>
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Documents</CardTitle>
            </CardHeader>
            <CardContent>
              {isBorrower ? (
                <div className="mb-4 grid gap-4 rounded-lg border bg-muted/20 p-4 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]">
                  <div className="space-y-2">
                    <Label htmlFor="application-document-type">Requirement</Label>
                    <Select value={selectedDocumentCode} onValueChange={setSelectedDocumentCode}>
                      <SelectTrigger id="application-document-type">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {documentRequirements.map((requirement) => (
                          <SelectItem key={requirement.code} value={requirement.code}>
                            {requirement.name}
                          </SelectItem>
                        ))}
                        <SelectItem value="BORROWER_UPLOAD">
                          Additional supporting document
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="application-document-file">File</Label>
                    <Input
                      id="application-document-file"
                      type="file"
                      onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
                    />
                  </div>
                  <div className="flex items-end">
                    <Button
                      className="w-full bg-emerald-600 hover:bg-emerald-700 md:w-auto"
                      onClick={() => void uploadSelectedDocument()}
                      disabled={uploadDocument.isPending || !selectedFile}
                    >
                      <Upload className="mr-2 h-4 w-4" />
                      Upload
                    </Button>
                  </div>
                </div>
              ) : null}
              <DataTable<PortalApplicationDocument>
                data={docsQuery.data ?? []}
                columns={docColumns}
                getRowId={(d) => d.id}
                isLoading={docsQuery.isLoading}
                error={docsQuery.isError ? docsQuery.error : undefined}
                onRetry={() => docsQuery.refetch()}
                emptyTitle="No documents uploaded"
                emptySubtitle="Documents linked to this application will appear here."
              />
            </CardContent>
          </Card>
        </>
      ) : null}

      <Dialog
        open={reasonAction !== null}
        onOpenChange={(open) => {
          if (!open) {
            setReasonAction(null);
            setReason('');
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Withdraw application</DialogTitle>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="application-reason">Reason</Label>
            <Textarea
              id="application-reason"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              rows={5}
              placeholder="Provide the reason and the expected next action."
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setReasonAction(null);
                setReason('');
              }}
            >
              Cancel
            </Button>
            <Button
              variant="default"
              onClick={() => void submitReasonAction()}
              disabled={reason.trim().length < 5}
            >
              Confirm
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
