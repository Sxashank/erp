import { Edit, FileText } from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';

import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import {
  ApplicationStageBadge,
  ApplicationStatusBadge,
} from '@/components/lending/common/StatusBadge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useApplication } from '@/hooks/lending/useApplication';
import { ApplicationChecklistTab } from '@/pages/lending/checklist/ApplicationChecklistTab';

export default function ApplicationView() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: app, isLoading, isError, error, refetch } = useApplication(id);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Application" subtitle="Loading..." />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (isError || !app) {
    return (
      <div className="space-y-6">
        <PageHeader title="Application" />
        <ErrorState title="Could not load application" error={error} onRetry={() => refetch()} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={app.applicationNumber}
        subtitle={`${app.entityName ?? app.entityLegalName ?? 'Entity'} · ${app.productName ?? 'Product'}`}
        breadcrumbs={[
          { label: 'Lending', to: '/admin/lending' },
          { label: 'Applications', to: '/admin/lending/applications' },
          { label: app.applicationNumber },
        ]}
        actions={
          app.status === 'DRAFT' ? (
            <Button onClick={() => navigate(`/admin/lending/applications/${id}/edit`)}>
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </Button>
          ) : null
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Stage</CardTitle>
          </CardHeader>
          <CardContent>
            <ApplicationStageBadge status={app.stage} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <ApplicationStatusBadge status={app.status} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Requested</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={app.requestedAmount}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="mt-1 text-xs text-muted-foreground">{app.requestedTenureMonths} months</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Created</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm">
              <DateDisplay date={app.createdAt} />
            </div>
            {app.submittedAt && (
              <p className="mt-1 text-xs text-muted-foreground">
                Submitted <DateDisplay date={app.submittedAt} format="relative" />
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="appraisal">Appraisal</TabsTrigger>
          <TabsTrigger value="documents">Documents</TabsTrigger>
          <TabsTrigger value="checklist">Approval Checklist</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4 pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Application Details</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-2 gap-4 text-sm md:grid-cols-3">
                <div>
                  <dt className="text-muted-foreground">Purpose</dt>
                  <dd className="font-medium">{app.purpose ?? '—'}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Project Name</dt>
                  <dd className="font-medium">{app.projectName ?? '—'}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Priority</dt>
                  <dd className="font-medium">{app.priority}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Project Cost</dt>
                  <dd className="font-medium">
                    {app.projectCost ? <AmountDisplay amount={app.projectCost} /> : '—'}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Promoter Contribution</dt>
                  <dd className="font-medium">
                    {app.promoterContribution ? (
                      <AmountDisplay amount={app.promoterContribution} />
                    ) : (
                      '—'
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Requested Amount</dt>
                  <dd className="font-medium">
                    <AmountDisplay amount={app.requestedAmount} />
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Borrower</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
                <div>
                  <dt className="text-muted-foreground">Legal Name</dt>
                  <dd className="font-medium">{app.entityLegalName ?? '—'}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Entity Code</dt>
                  <dd className="font-mono text-xs">{app.entityCode ?? '—'}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">PAN</dt>
                  <dd className="font-mono text-xs">{app.entityPan ?? '—'}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Entity Type</dt>
                  <dd className="font-medium">{app.entityType ?? '—'}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Product</dt>
                  <dd className="font-medium">
                    {app.productName ?? '—'}
                    {app.productCode && (
                      <span className="ml-1 text-xs text-muted-foreground">
                        ({app.productCode})
                      </span>
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Category</dt>
                  <dd className="font-medium">{app.productCategory ?? '—'}</dd>
                </div>
              </dl>
              <div className="mt-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/admin/lending/entities/${app.entityId}`)}
                >
                  <FileText className="mr-2 h-4 w-4" />
                  View Entity Profile
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="appraisal" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Technical & Financial Appraisal</CardTitle>
              <CardDescription>Credit appraisal artifacts</CardDescription>
            </CardHeader>
            <CardContent>
              <EmptyState
                title="Appraisal not embedded yet"
                subtitle="Use the appraisal module to record technical and financial assessment for this application."
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="documents" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Documents</CardTitle>
              <CardDescription>Application document checklist</CardDescription>
            </CardHeader>
            <CardContent>
              <EmptyState
                title="Document list not embedded yet"
                subtitle="Application documents are available via /lending/applications/{id}/documents; the embedded list will follow."
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="checklist" className="pt-4">
          {id ? (
            <ApplicationChecklistTab applicationId={id} />
          ) : (
            <EmptyState title="Application id missing" />
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
