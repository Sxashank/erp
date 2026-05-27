/**
 * PortalKFSAcknowledge — borrower acknowledges the Key Facts Statement.
 *
 * Per RBI Oct-2024 mandate, this acknowledgement is required before the
 * borrower can accept the sanction. Until clicked, the sanction acceptance
 * endpoint returns 422 KFS_ACK_REQUIRED.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CheckCircle2, FileText, Loader2 } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';

import { DateDisplay, ErrorState, PageHeader, SkeletonTable } from '@/components/common';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import api from '@/services/api';

interface CertificateRow {
  id: string;
  certificateType: string;
  certificateNumber: string;
  issuedAt: string;
  requiresAcknowledgement: boolean;
  isAcknowledged: boolean;
  acknowledgedAt?: string | null;
}

interface CertList {
  items: CertificateRow[];
  total: number;
}

async function fetchApplicationCertificates(applicationId: string): Promise<CertList> {
  const { data } = await api.get<CertList>(`/portal/applications/${applicationId}/certificates`);
  return data;
}

async function acknowledge(certId: string): Promise<CertificateRow> {
  const { data } = await api.post<CertificateRow>(`/portal/certificates/${certId}/acknowledge`);
  return data;
}

export default function PortalKFSAcknowledge(): JSX.Element {
  const { id: applicationId } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const { toast } = useToast();

  const query = useQuery<CertList>({
    queryKey: ['portal', 'application', applicationId, 'certificates'],
    queryFn: () => fetchApplicationCertificates(applicationId as string),
    enabled: Boolean(applicationId),
    staleTime: 30_000,
  });

  const mutation = useMutation({
    mutationFn: acknowledge,
    onSuccess: () => {
      toast({ title: 'KFS acknowledged', description: 'You may now accept the sanction.' });
      qc.invalidateQueries({ queryKey: ['portal', 'application', applicationId, 'certificates'] });
      qc.invalidateQueries({ queryKey: ['portal', 'application', applicationId, 'lifecycle'] });
    },
    onError: (err) =>
      toast({
        title: 'Could not acknowledge KFS',
        description: err instanceof Error ? err.message : 'Unknown error',
        variant: 'destructive',
      }),
  });

  if (query.isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Key Facts Statement"
          breadcrumbs={[{ label: 'Applications', to: '/portal/applications' }, { label: 'KFS' }]}
        />
        <SkeletonTable rows={3} columns={1} />
      </div>
    );
  }
  if (query.isError || !query.data) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Key Facts Statement"
          breadcrumbs={[{ label: 'Applications', to: '/portal/applications' }, { label: 'KFS' }]}
        />
        <ErrorState
          error={query.error ?? new Error('Could not load certificates')}
          onRetry={() => query.refetch()}
        />
      </div>
    );
  }

  const kfsList = query.data.items.filter((c) => c.certificateType === 'KFS');

  return (
    <div className="space-y-6">
      <PageHeader
        title="Key Facts Statement"
        subtitle="Please read the Key Facts Statement and acknowledge before accepting the sanction."
        breadcrumbs={[{ label: 'Applications', to: '/portal/applications' }, { label: 'KFS' }]}
      />

      {kfsList.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-sm text-muted-foreground">
            <FileText className="mx-auto mb-3 h-8 w-8 text-gray-300" />
            The Key Facts Statement has not been issued yet. Please wait until SFC issues the
            sanction.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {kfsList.map((cert) => (
            <Card key={cert.id} className="border-amber-100 bg-amber-50">
              <CardHeader>
                <div className="flex items-center justify-between gap-2">
                  <CardTitle className="text-base">KFS {cert.certificateNumber}</CardTitle>
                  {cert.isAcknowledged ? (
                    <Badge variant="default" className="bg-green-100 text-green-800">
                      <CheckCircle2 className="mr-1 h-3 w-3" />
                      Acknowledged
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="border-amber-500 text-amber-700">
                      Action required
                    </Badge>
                  )}
                </div>
                <div className="text-xs text-muted-foreground">
                  Issued <DateDisplay date={cert.issuedAt} />
                  {cert.acknowledgedAt ? (
                    <>
                      {' '}
                      · Acknowledged <DateDisplay date={cert.acknowledgedAt} />
                    </>
                  ) : null}
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm">
                  The Key Facts Statement contains the loan amount, interest rate, EMI, fees, total
                  cost of credit, and cooling-off period. RBI mandates explicit acknowledgement
                  before the loan agreement is signed.
                </p>
                <div className="flex flex-wrap gap-2">
                  <Button asChild variant="outline">
                    <a
                      href={`/api/v1/portal/certificates/${cert.id}/download`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <FileText className="mr-2 h-4 w-4" />
                      Download KFS
                    </a>
                  </Button>
                  {!cert.isAcknowledged ? (
                    <Button onClick={() => mutation.mutate(cert.id)} disabled={mutation.isPending}>
                      {mutation.isPending ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <CheckCircle2 className="mr-2 h-4 w-4" />
                      )}
                      I have read and accept the Key Facts Statement
                    </Button>
                  ) : (
                    <Button asChild variant="default">
                      <Link to={`/portal/applications/${applicationId}`}>
                        Continue to acceptance
                      </Link>
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
