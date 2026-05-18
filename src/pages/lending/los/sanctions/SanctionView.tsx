import { Edit, FileText, Plus } from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';

import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { StatusBadge } from '@/components/lending/common/StatusBadge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useSanction } from '@/hooks/lending/useSanction';
import { SanctionApprovedUtilization } from '@/pages/lending/checklist/SanctionApprovedUtilization';

export default function SanctionView() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: sanction, isLoading, isError, error, refetch } = useSanction(id);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Sanction" subtitle="Loading..." />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (isError || !sanction) {
    return (
      <div className="space-y-6">
        <PageHeader title="Sanction" />
        <ErrorState title="Could not load sanction" error={error} onRetry={() => refetch()} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={sanction.sanctionNumber}
        subtitle={`Sanction date ${sanction.sanctionDate} · ${sanction.status}`}
        breadcrumbs={[
          { label: 'Lending', to: '/admin/lending' },
          { label: 'Sanctions', to: '/admin/lending/sanctions' },
          { label: sanction.sanctionNumber },
        ]}
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => navigate(`/admin/lending/sanctions/${id}/letter`)}
            >
              <FileText className="mr-2 h-4 w-4" />
              Sanction Letter
            </Button>
            {sanction.status === 'ACCEPTED' && (
              <Button onClick={() => navigate(`/admin/lending/disbursements/new?sanctionId=${id}`)}>
                <Plus className="mr-2 h-4 w-4" />
                Disburse
              </Button>
            )}
            {(sanction.status === 'DRAFT' || sanction.status === 'PENDING_APPROVAL') && (
              <Button
                variant="outline"
                onClick={() => navigate(`/admin/lending/sanctions/${id}/edit`)}
              >
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </Button>
            )}
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <StatusBadge status={sanction.status} type="sanction" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Sanctioned</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={sanction.sanctionedAmount}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="mt-1 text-xs text-muted-foreground">{sanction.tenureMonths} months</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              <PercentageDisplay value={sanction.effectiveRate} /> p.a.
            </div>
            <p className="mt-1 text-xs text-muted-foreground">Effective</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Validity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm font-medium">
              <DateDisplay date={sanction.validityDate} />
            </div>
            {sanction.approvedAt && (
              <p className="mt-1 text-xs text-muted-foreground">
                Approved <DateDisplay date={sanction.approvedAt} format="relative" />
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="terms">
        <TabsList>
          <TabsTrigger value="terms">Terms</TabsTrigger>
          <TabsTrigger value="conditions">Conditions</TabsTrigger>
          <TabsTrigger value="securities">Securities</TabsTrigger>
          {(sanction.status === 'PENDING_APPROVAL' || sanction.status === 'APPROVED') && (
            <TabsTrigger value="utilization">Approved Utilization</TabsTrigger>
          )}
        </TabsList>

        <TabsContent value="terms" className="space-y-4 pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Sanction Terms</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-2 gap-4 text-sm md:grid-cols-3">
                <div>
                  <dt className="text-muted-foreground">Sanctioned Amount</dt>
                  <dd className="font-medium">
                    <AmountDisplay amount={sanction.sanctionedAmount} />
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Tenure</dt>
                  <dd className="font-medium">{sanction.tenureMonths} months</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Moratorium</dt>
                  <dd className="font-medium">{sanction.moratoriumMonths} months</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Effective Rate</dt>
                  <dd className="font-medium">
                    <PercentageDisplay value={sanction.effectiveRate} /> p.a.
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Repayment Mode</dt>
                  <dd className="font-medium">{sanction.repaymentMode}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Repayment Frequency</dt>
                  <dd className="font-medium">{sanction.repaymentFrequency}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Sanction Date</dt>
                  <dd className="font-medium">
                    <DateDisplay date={sanction.sanctionDate} />
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Validity</dt>
                  <dd className="font-medium">
                    <DateDisplay date={sanction.validityDate} />
                  </dd>
                </div>
              </dl>
              {sanction.specialTerms && (
                <div className="mt-4 border-t pt-4">
                  <p className="text-sm text-muted-foreground">Special Terms</p>
                  <p className="mt-1 whitespace-pre-line text-sm">{sanction.specialTerms}</p>
                </div>
              )}
              {sanction.remarks && (
                <div className="mt-4">
                  <p className="text-sm text-muted-foreground">Remarks</p>
                  <p className="mt-1 text-sm">{sanction.remarks}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="conditions" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Sanction Conditions</CardTitle>
              <CardDescription>Pre-disbursement and post-disbursement</CardDescription>
            </CardHeader>
            <CardContent>
              <EmptyState
                title="Conditions list not embedded yet"
                subtitle="Use /lending/sanctions/{id}/conditions for the full list."
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="securities" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Securities & Collateral</CardTitle>
            </CardHeader>
            <CardContent>
              <EmptyState
                title="Securities list not embedded yet"
                subtitle="Use /lending/sanctions/{id}/securities for the full list."
              />
            </CardContent>
          </Card>
        </TabsContent>

        {(sanction.status === 'PENDING_APPROVAL' || sanction.status === 'APPROVED') && (
          <TabsContent value="utilization" className="pt-4">
            <SanctionApprovedUtilization
              applicationId={sanction.applicationId}
              sanctionedAmount={sanction.sanctionedAmount}
              editable={sanction.status === 'PENDING_APPROVAL'}
            />
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
}
