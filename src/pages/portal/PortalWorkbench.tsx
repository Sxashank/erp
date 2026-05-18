/**
 * Scheme Portal — borrower workbench.
 */

import { ArrowRight, Building2, FileSignature, ShieldCheck } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

import {
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
import { usePortalWorkbench } from '@/hooks/portal/useWorkbench';
import type { PortalWorkbenchApplication } from '@/services/portalApi';

const ROLE_COPY: Record<
  string,
  {
    title: string;
    subtitle: string;
    badge: string;
    primaryHref?: string;
    primaryLabel?: string;
  }
> = {
  scheme_borrower: {
    title: 'Scheme Workbench',
    subtitle:
      'Track institutional applications, answer review queries, and monitor sanction progress.',
    badge: 'Borrower workbench',
    primaryHref: '/portal/applications/new',
    primaryLabel: 'New application',
  },
  scheme_lender: {
    title: 'Lender Workbench',
    subtitle: 'Validate submitted borrower applications and monitor lender-side review throughput.',
    badge: 'Lender review queue',
  },
  scheme_smfcl_reviewer: {
    title: 'SMFCL Review Workbench',
    subtitle: 'Process registrations, application review, and submitted subsidy claims.',
    badge: 'SMFCL reviewer',
  },
  scheme_smfcl_approver: {
    title: 'SMFCL Approval Workbench',
    subtitle: 'Approve appraised applications and release verified subsidy claims.',
    badge: 'SMFCL approver',
  },
  scheme_ministry_viewer: {
    title: 'Ministry Monitoring Workbench',
    subtitle: 'Monitor submissions, approvals, and claim releases across the scheme.',
    badge: 'Ministry view',
  },
  scheme_admin: {
    title: 'Scheme Administration Workbench',
    subtitle: 'Oversee registrations, reviews, approvals, and claim release activity.',
    badge: 'Scheme admin',
  },
};

const columns: Column<PortalWorkbenchApplication>[] = [
  {
    key: 'applicationNumber',
    header: 'Application #',
    render: (row) => <span className="font-medium">{row.applicationNumber}</span>,
  },
  {
    key: 'entityLegalName',
    header: 'Borrower entity',
    render: (row) => row.entityLegalName ?? '—',
  },
  {
    key: 'productName',
    header: 'Product',
    render: (row) => row.productName ?? '—',
  },
  {
    key: 'schemeStatus',
    header: 'Scheme status',
    render: (row) => <StatusPill type="application" status={row.schemeStatus} />,
  },
  {
    key: 'submittedAt',
    header: 'Submitted',
    render: (row) => <DateDisplay date={row.submittedAt} />,
  },
];

export default function PortalWorkbench(): JSX.Element {
  const navigate = useNavigate();
  const query = usePortalWorkbench();
  const roleCopy =
    ROLE_COPY[query.data?.actorRole ?? 'scheme_borrower'] ?? ROLE_COPY.scheme_borrower;

  return (
    <div className="space-y-6">
      <PageHeader
        title={roleCopy.title}
        subtitle={roleCopy.subtitle}
        breadcrumbs={[{ label: 'Scheme Portal' }, { label: 'Workbench' }]}
        actions={
          roleCopy.primaryHref && roleCopy.primaryLabel ? (
            <Button asChild className="bg-emerald-600 hover:bg-emerald-700">
              <Link to={roleCopy.primaryHref}>
                <FileSignature className="mr-2 h-4 w-4" />
                {roleCopy.primaryLabel}
              </Link>
            </Button>
          ) : undefined
        }
      />

      {query.isLoading && <SkeletonTable rows={5} columns={5} />}
      {query.isError && <ErrorState error={query.error} onRetry={() => query.refetch()} />}

      {query.data && (
        <>
          <Card>
            <CardContent className="flex flex-col gap-2 p-5 md:flex-row md:items-center md:justify-between">
              <div>
                <div className="text-sm text-muted-foreground">Signed in as</div>
                <div className="text-xl font-semibold">{query.data.displayName}</div>
                <div className="mt-1 text-sm text-muted-foreground">
                  {query.data.activeEntityCount} linked organisation
                  {query.data.activeEntityCount === 1 ? '' : 's'}
                </div>
              </div>
              <div className="flex items-center gap-2 rounded-lg bg-emerald-50 px-4 py-3 text-emerald-700">
                <ShieldCheck className="h-5 w-5" />
                <div>
                  <div className="text-sm font-medium">Scheme role</div>
                  <div className="text-sm">{roleCopy.badge}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            {query.data.stats.map((stat) => (
              <Card key={stat.key}>
                <CardContent className="p-5">
                  <div className="text-sm text-muted-foreground">{stat.label}</div>
                  <div className="mt-2 text-3xl font-semibold">{stat.value}</div>
                  {stat.hint ? (
                    <div className="mt-2 text-xs text-muted-foreground">{stat.hint}</div>
                  ) : null}
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="grid gap-6 xl:grid-cols-[1.4fr,1fr]">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Recent applications</CardTitle>
              </CardHeader>
              <CardContent>
                <DataTable<PortalWorkbenchApplication>
                  data={query.data.recentApplications}
                  columns={columns}
                  getRowId={(row) => row.id}
                  onRowClick={(row) => navigate(`/portal/applications/${row.id}`)}
                  emptyTitle="No applications yet"
                  emptySubtitle="Start your first institutional scheme application to begin lender review."
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Priority actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {query.data.priorityActions.length === 0 ? (
                  <EmptyState
                    icon={Building2}
                    title="No actions pending"
                    subtitle="Your borrower workbench is up to date."
                  />
                ) : (
                  query.data.priorityActions.map((action) => (
                    <Link
                      key={`${action.href}-${action.title}`}
                      to={action.href}
                      className="block rounded-lg border p-4 transition-colors hover:bg-muted/40"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="font-medium">{action.title}</div>
                          <div className="mt-1 text-sm text-muted-foreground">
                            {action.description}
                          </div>
                        </div>
                        <ArrowRight className="mt-0.5 h-4 w-4 text-muted-foreground" />
                      </div>
                    </Link>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
