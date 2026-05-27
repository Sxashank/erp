/**
 * PortalApplicationQueries — borrower query inbox for one application.
 *
 * Shows SFC requests for clarification and lets the borrower respond with
 * text plus uploaded supporting documents.
 */

import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Clock,
  MessageSquare,
  Paperclip,
  Send,
} from 'lucide-react';
import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { DateDisplay, ErrorState, PageHeader, SkeletonTable } from '@/components/common';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  usePortalApplicationQueries,
  useRespondPortalApplicationQuery,
  useUploadApplicationDocument,
} from '@/hooks/portal/useApplications';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import type { PortalApplicationQuery } from '@/services/portalApi';

function statusBadge(status: PortalApplicationQuery['status']): JSX.Element {
  switch (status) {
    case 'RAISED':
      return (
        <Badge variant="outline" className="border-amber-500 text-amber-700">
          <AlertCircle className="mr-1 h-3 w-3" />
          Awaiting your response
        </Badge>
      );
    case 'RESPONDED':
    case 'RE_REVIEW':
      return (
        <Badge variant="secondary">
          <Clock className="mr-1 h-3 w-3" />
          Under SFC review
        </Badge>
      );
    case 'RESOLVED':
      return (
        <Badge variant="default" className="bg-green-100 text-green-800">
          <CheckCircle2 className="mr-1 h-3 w-3" />
          Resolved
        </Badge>
      );
    case 'LAPSED':
      return <Badge variant="destructive">Response overdue</Badge>;
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
}

function QueryCard({
  query,
  applicationId,
  onResponded,
}: {
  query: PortalApplicationQuery;
  applicationId: string;
  onResponded: () => void;
}): JSX.Element {
  const [draft, setDraft] = useState(query.responseText ?? '');
  const [files, setFiles] = useState<File[]>([]);
  const { toast } = useToast();
  const respond = useRespondPortalApplicationQuery(applicationId);
  const uploadDocument = useUploadApplicationDocument();

  const canRespond = query.status === 'RAISED' || query.status === 'RESPONDED';
  const requiredAttachments = query.requiredAttachments ?? [];
  const hasExistingAttachments = query.responseAttachments.length > 0;
  const needsUpload =
    requiredAttachments.length > 0 && files.length === 0 && !hasExistingAttachments;
  const isBusy = respond.isPending || uploadDocument.isPending;

  const submitResponse = async () => {
    if (!draft.trim()) return;
    try {
      const uploadedMetadata: Record<string, unknown>[] = [];
      for (let idx = 0; idx < files.length; idx += 1) {
        const file = files[idx]!;
        const documentCode =
          requiredAttachments[idx] ?? requiredAttachments[0] ?? 'BORROWER_QUERY_RESPONSE';
        const uploaded = await uploadDocument.mutateAsync({
          applicationId,
          file,
          documentType: documentCode,
          documentName: file.name,
        });
        uploadedMetadata.push({
          documentId: uploaded.id,
          documentCode: uploaded.documentCode ?? documentCode,
          documentName: uploaded.documentName ?? file.name,
          fileName: uploaded.fileName,
          uploadedAt: uploaded.uploadDate ?? uploaded.uploadedAt ?? null,
        });
      }

      await respond.mutateAsync({
        queryId: query.id,
        payload: {
          responseText: draft.trim(),
          responseAttachments: uploadedMetadata,
        },
      });
      setFiles([]);
      toast({ title: 'Response sent to SFC' });
      onResponded();
    } catch (err) {
      showErrorToast(err, toast);
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <CardTitle className="text-base">
            Q{query.queryNumber} · {query.raisedReasonCode.replace(/_/g, ' ')}
          </CardTitle>
          {statusBadge(query.status)}
        </div>
        <div className="text-xs text-muted-foreground">
          Raised <DateDisplay date={query.raisedAt} />
          {query.slaDueAt ? (
            <>
              {' '}
              · respond by <DateDisplay date={query.slaDueAt} />
            </>
          ) : null}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label className="text-xs uppercase tracking-wider text-muted-foreground">
            SFC query
          </Label>
          <p className="mt-1 whitespace-pre-line text-sm">{query.queryText}</p>
          {requiredAttachments.length > 0 ? (
            <div className="mt-2 text-xs text-muted-foreground">
              Required uploads: {requiredAttachments.join(', ')}
            </div>
          ) : null}
        </div>

        {query.responseText ? (
          <div className="rounded-lg border border-blue-100 bg-blue-50 p-3">
            <Label className="text-xs uppercase tracking-wider text-blue-700">Your response</Label>
            <p className="mt-1 whitespace-pre-line text-sm text-blue-900">{query.responseText}</p>
            {query.responseAttachments.length > 0 ? (
              <div className="mt-2 flex flex-wrap gap-2 text-xs text-blue-800">
                {query.responseAttachments.map((attachment, index) => (
                  <span key={index} className="inline-flex items-center rounded border px-2 py-1">
                    <Paperclip className="mr-1 h-3 w-3" />
                    {String(
                      attachment.fileName ?? attachment.documentName ?? `Attachment ${index + 1}`,
                    )}
                  </span>
                ))}
              </div>
            ) : null}
            {query.respondedAt ? (
              <div className="mt-1 text-xs text-blue-700">
                Sent <DateDisplay date={query.respondedAt} />
              </div>
            ) : null}
          </div>
        ) : null}

        {query.resolutionRemark ? (
          <div className="rounded-lg border border-emerald-100 bg-emerald-50 p-3">
            <Label className="text-xs uppercase tracking-wider text-emerald-700">
              SFC resolution
            </Label>
            <p className="mt-1 whitespace-pre-line text-sm text-emerald-900">
              {query.resolutionRemark}
            </p>
          </div>
        ) : null}

        {canRespond ? (
          <div className="space-y-3">
            <div className="space-y-2">
              <Label>Your response</Label>
              <Textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                rows={4}
                placeholder="Reply to SFC with the requested clarification."
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor={`query-files-${query.id}`}>Supporting documents</Label>
              <Input
                id={`query-files-${query.id}`}
                type="file"
                multiple
                onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
              />
              {files.length > 0 ? (
                <div className="text-xs text-muted-foreground">{files.length} file(s) selected</div>
              ) : null}
            </div>
            <Button
              onClick={() => void submitResponse()}
              disabled={!draft.trim() || needsUpload || isBusy}
            >
              <Send className="mr-2 h-4 w-4" />
              {isBusy ? 'Sending...' : 'Send response'}
            </Button>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

export default function PortalApplicationQueries(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  const query = usePortalApplicationQueries(id);

  if (query.isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Application queries"
          breadcrumbs={[
            { label: 'Applications', to: '/portal/applications' },
            { label: 'Queries' },
          ]}
        />
        <SkeletonTable rows={3} columns={1} />
      </div>
    );
  }

  if (query.isError || !query.data) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Application queries"
          breadcrumbs={[
            { label: 'Applications', to: '/portal/applications' },
            { label: 'Queries' },
          ]}
        />
        <ErrorState
          error={query.error ?? new Error('Could not load queries')}
          onRetry={() => query.refetch()}
        />
      </div>
    );
  }

  const openCount = query.data.items.filter((item) => item.status === 'RAISED').length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Application queries"
        subtitle={
          openCount > 0
            ? `${openCount} require your response`
            : `${query.data.total} total - all caught up`
        }
        breadcrumbs={[{ label: 'Applications', to: '/portal/applications' }, { label: 'Queries' }]}
        actions={
          <Button variant="outline" asChild>
            <Link to={`/portal/applications/${id}`}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to application
            </Link>
          </Button>
        }
      />

      {query.data.items.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-sm text-muted-foreground">
            <MessageSquare className="mx-auto mb-3 h-8 w-8 text-gray-300" />
            No queries have been raised on this application.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {query.data.items.map((item) => (
            <QueryCard
              key={item.id}
              query={item}
              applicationId={id as string}
              onResponded={() => void query.refetch()}
            />
          ))}
        </div>
      )}
    </div>
  );
}
