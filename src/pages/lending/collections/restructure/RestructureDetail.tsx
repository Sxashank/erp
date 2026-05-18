import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Edit, CheckCircle, Play } from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import api from '@/services/api';

interface RestructureDetailData {
  id: string;
  restructureReference: string;
  restructureType: string;
  status: string;
  proposalDate: string;
  loanAccountId: string;
  preOutstandingPrincipal: string | number;
  preInterestRate: string | number;
  preTenureMonths: number;
  preEmiAmount?: string | number | null;
  preMaturityDate: string;
  postOutstandingPrincipal: string | number;
  postInterestRate: string | number;
  postTenureMonths: number;
  postEmiAmount?: string | number | null;
  postMaturityDate: string;
  moratoriumMonths: number;
  interestWaived: string | number;
  penalWaived: string | number;
  isStandardRestructure: boolean;
  justification: string;
  approvalDate?: string | null;
  implementationDate?: string | null;
  remarks?: string | null;
}

export default function RestructureDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const { data, isLoading, isError, error, refetch } = useQuery<RestructureDetailData>({
    queryKey: ['lending', 'collections', 'restructure', id] as const,
    queryFn: async () => {
      const { data } = await api.get<RestructureDetailData>(
        `/lending/collections/restructures/${id}`,
      );
      return data;
    },
    enabled: !!id,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Restructure" subtitle="Loading..." />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="space-y-6">
        <PageHeader title="Restructure" />
        <ErrorState title="Could not load restructure" error={error} onRetry={() => refetch()} />
      </div>
    );
  }

  const r = data;

  return (
    <div className="space-y-6">
      <PageHeader
        title={r.restructureReference}
        subtitle={`${r.restructureType.replace('_', ' ')} · ${r.status}`}
        breadcrumbs={[
          { label: 'Lending', to: '/admin/lending' },
          { label: 'Collections', to: '/admin/lending/collections' },
          { label: 'Restructure', to: '/admin/lending/collections/restructure' },
          { label: r.restructureReference },
        ]}
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => navigate('/admin/lending/collections/restructure')}
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            {r.status === 'PENDING_APPROVAL' && (
              <Button
                onClick={() => navigate(`/admin/lending/collections/restructure/${id}/approve`)}
              >
                <CheckCircle className="mr-2 h-4 w-4" />
                Review & Approve
              </Button>
            )}
            {r.status === 'APPROVED' && !r.implementationDate && (
              <Button>
                <Play className="mr-2 h-4 w-4" />
                Implement
              </Button>
            )}
            {(r.status === 'DRAFT' || r.status === 'PROPOSED') && (
              <Button variant="outline">
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </Button>
            )}
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant="outline">{r.status.replace('_', ' ')}</Badge>
            <p className="mt-2 text-xs text-muted-foreground">
              {r.isStandardRestructure ? 'Standard' : 'Non-standard'} restructure
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Type</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant="outline">{r.restructureType.replace('_', ' ')}</Badge>
            <p className="mt-2 text-xs text-muted-foreground">
              Proposed <DateDisplay date={r.proposalDate} />
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Relief Given
            </CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={Number(r.interestWaived) + Number(r.penalWaived)}
              abbreviated
              className="text-2xl font-bold text-red-600"
            />
            <p className="mt-1 text-xs text-muted-foreground">Interest + Penal waived</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Terms Comparison</CardTitle>
          <CardDescription>Pre- vs post-restructure</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-3">
              <h3 className="font-semibold">Before</h3>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Outstanding Principal</dt>
                  <dd className="font-medium">
                    <AmountDisplay amount={r.preOutstandingPrincipal} />
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Interest Rate</dt>
                  <dd className="font-medium">{r.preInterestRate}% p.a.</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Tenure</dt>
                  <dd className="font-medium">{r.preTenureMonths} months</dd>
                </div>
                {r.preEmiAmount && (
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">EMI</dt>
                    <dd className="font-medium">
                      <AmountDisplay amount={r.preEmiAmount} />
                    </dd>
                  </div>
                )}
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Maturity</dt>
                  <dd className="font-medium">
                    <DateDisplay date={r.preMaturityDate} />
                  </dd>
                </div>
              </dl>
            </div>
            <div className="space-y-3">
              <h3 className="font-semibold">After</h3>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Outstanding Principal</dt>
                  <dd className="font-medium">
                    <AmountDisplay amount={r.postOutstandingPrincipal} />
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Interest Rate</dt>
                  <dd className="font-medium">{r.postInterestRate}% p.a.</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Tenure</dt>
                  <dd className="font-medium">{r.postTenureMonths} months</dd>
                </div>
                {r.postEmiAmount && (
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">EMI</dt>
                    <dd className="font-medium">
                      <AmountDisplay amount={r.postEmiAmount} />
                    </dd>
                  </div>
                )}
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Maturity</dt>
                  <dd className="font-medium">
                    <DateDisplay date={r.postMaturityDate} />
                  </dd>
                </div>
                {r.moratoriumMonths > 0 && (
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">Moratorium</dt>
                    <dd className="font-medium">{r.moratoriumMonths} months</dd>
                  </div>
                )}
              </dl>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Justification</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="whitespace-pre-line text-sm">{r.justification}</p>
          {r.remarks && (
            <div className="mt-4 border-t pt-4">
              <p className="text-sm text-muted-foreground">Remarks</p>
              <p className="mt-1 whitespace-pre-line text-sm">{r.remarks}</p>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Loan Account</CardTitle>
        </CardHeader>
        <CardContent>
          <Button
            variant="outline"
            onClick={() => navigate(`/admin/lending/accounts/${r.loanAccountId}`)}
          >
            View Loan Account
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
