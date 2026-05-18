import { Download, Loader2 } from 'lucide-react';
import { useState } from 'react';

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
import { useDownloadPortalReportCsv, usePortalReports } from '@/hooks/portal/useReports';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import type {
  PortalReportBorrowerBreakdownItem,
  PortalReportLenderBreakdownItem,
  PortalReportRecentReleaseItem,
  PortalReportStatusBreakdownItem,
} from '@/services/portalApi';

const ROLE_COPY: Record<string, { title: string; subtitle: string }> = {
  scheme_borrower: {
    title: 'Scheme Reports',
    subtitle:
      'Review application, claim, and release metrics for your linked institutional entities.',
  },
  scheme_lender: {
    title: 'Lender Monitoring',
    subtitle:
      'Track lender validation throughput, approval conversion, and claim-release activity.',
  },
  scheme_smfcl_reviewer: {
    title: 'SMFCL Review Reports',
    subtitle: 'Monitor review backlogs, borrower concentration, and claim verification progress.',
  },
  scheme_smfcl_approver: {
    title: 'SMFCL Approval Reports',
    subtitle: 'Track sanction approvals and claim release execution across the scheme.',
  },
  scheme_ministry_viewer: {
    title: 'Ministry Monitoring Reports',
    subtitle:
      'Review scheme-wide application funnel, borrower coverage, lender participation, and releases.',
  },
  scheme_admin: {
    title: 'Scheme Administration Reports',
    subtitle:
      'Oversee the end-to-end scheme pipeline across applications, claims, and borrower concentration.',
  },
};

function formatStatus(status: string): string {
  return status.replace(/_/g, ' ');
}

const applicationStatusColumns: Column<PortalReportStatusBreakdownItem>[] = [
  {
    key: 'status',
    header: 'Scheme status',
    render: (row) => <StatusPill type="application" status={row.status} />,
  },
  {
    key: 'count',
    header: 'Applications',
    align: 'right',
    render: (row) => <span className="font-medium">{row.count}</span>,
    sortable: true,
    sortValue: (row) => row.count,
  },
];

const claimStatusColumns: Column<PortalReportStatusBreakdownItem>[] = [
  {
    key: 'status',
    header: 'Claim status',
    render: (row) => <span className="font-medium">{formatStatus(row.status)}</span>,
  },
  {
    key: 'count',
    header: 'Claims',
    align: 'right',
    render: (row) => <span className="font-medium">{row.count}</span>,
    sortable: true,
    sortValue: (row) => row.count,
  },
];

const borrowerColumns: Column<PortalReportBorrowerBreakdownItem>[] = [
  {
    key: 'entityLegalName',
    header: 'Borrower entity',
    render: (row) => <span className="font-medium">{row.entityLegalName}</span>,
  },
  {
    key: 'applicationCount',
    header: 'Applications',
    align: 'right',
    render: (row) => row.applicationCount,
    sortable: true,
    sortValue: (row) => row.applicationCount,
  },
  {
    key: 'approvedCount',
    header: 'Approved',
    align: 'right',
    render: (row) => row.approvedCount,
    sortable: true,
    sortValue: (row) => row.approvedCount,
  },
  {
    key: 'requestedAmount',
    header: 'Requested amount',
    align: 'right',
    render: (row) => <AmountDisplay amount={Number(row.requestedAmount)} />,
    sortable: true,
    sortValue: (row) => Number(row.requestedAmount),
  },
];

const lenderColumns: Column<PortalReportLenderBreakdownItem>[] = [
  {
    key: 'lenderName',
    header: 'Lender',
    render: (row) => <span className="font-medium">{row.lenderName}</span>,
  },
  {
    key: 'applicationCount',
    header: 'Applications',
    align: 'right',
    render: (row) => row.applicationCount,
    sortable: true,
    sortValue: (row) => row.applicationCount,
  },
  {
    key: 'pendingLenderReview',
    header: 'Pending lender review',
    align: 'right',
    render: (row) => row.pendingLenderReview,
    sortable: true,
    sortValue: (row) => row.pendingLenderReview,
  },
  {
    key: 'requestedAmount',
    header: 'Requested amount',
    align: 'right',
    render: (row) => <AmountDisplay amount={Number(row.requestedAmount)} />,
    sortable: true,
    sortValue: (row) => Number(row.requestedAmount),
  },
];

const releaseColumns: Column<PortalReportRecentReleaseItem>[] = [
  {
    key: 'claimReference',
    header: 'Claim reference',
    render: (row) => <span className="font-medium">{row.claimReference}</span>,
  },
  {
    key: 'entityLegalName',
    header: 'Borrower entity',
    render: (row) => row.entityLegalName ?? '—',
  },
  {
    key: 'schemeName',
    header: 'Scheme',
    render: (row) => row.schemeName ?? '—',
  },
  {
    key: 'applicableSubventionAmount',
    header: 'Released amount',
    align: 'right',
    render: (row) => <AmountDisplay amount={Number(row.applicableSubventionAmount)} />,
    sortable: true,
    sortValue: (row) => Number(row.applicableSubventionAmount),
  },
  {
    key: 'releasedDate',
    header: 'Released on',
    render: (row) => <DateDisplay date={row.releasedDate} />,
    sortable: true,
    sortValue: (row) => row.releasedDate ?? '',
  },
];

export default function PortalReports(): JSX.Element {
  const query = usePortalReports();
  const downloadCsv = useDownloadPortalReportCsv();
  const { toast } = useToast();
  const [isDownloading, setIsDownloading] = useState(false);
  const roleCopy =
    ROLE_COPY[query.data?.actorRole ?? 'scheme_borrower'] ?? ROLE_COPY.scheme_borrower;

  async function handleDownloadCsv() {
    try {
      setIsDownloading(true);
      await downloadCsv('scheme-portal-report.csv');
    } catch (err) {
      showErrorToast(err, toast);
    } finally {
      setIsDownloading(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={roleCopy.title}
        subtitle={roleCopy.subtitle}
        breadcrumbs={[{ label: 'Scheme Portal' }, { label: 'Reports' }]}
        actions={
          <Button
            variant="outline"
            onClick={() => void handleDownloadCsv()}
            disabled={isDownloading}
          >
            {isDownloading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Download className="mr-2 h-4 w-4" />
            )}
            Download CSV
          </Button>
        }
      />

      {query.isLoading ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <Card key={index}>
                <CardContent className="space-y-3 p-5">
                  <div className="h-4 w-1/2 rounded bg-muted" />
                  <div className="h-8 w-1/3 rounded bg-muted" />
                </CardContent>
              </Card>
            ))}
          </div>
          <SkeletonTable rows={6} columns={4} />
        </>
      ) : null}

      {query.isError ? <ErrorState error={query.error} onRetry={() => query.refetch()} /> : null}

      {query.data ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <MetricCard label="Applications total" value={query.data.applicationSummary.total} />
            <MetricCard
              label="Applications submitted"
              value={query.data.applicationSummary.submitted}
            />
            <MetricCard
              label="Applications under review"
              value={query.data.applicationSummary.underReview}
            />
            <MetricCard
              label="Applications approved"
              value={query.data.applicationSummary.approved}
            />
            <MetricCard label="Claims submitted" value={query.data.claimSummary.submitted} />
            <MetricCard
              label="Released amount"
              value={<AmountDisplay amount={Number(query.data.claimSummary.releasedAmount)} />}
            />
          </div>

          <div className="grid gap-6 xl:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Application funnel</CardTitle>
              </CardHeader>
              <CardContent>
                <DataTable<PortalReportStatusBreakdownItem>
                  data={query.data.applicationStatusBreakdown}
                  columns={applicationStatusColumns}
                  getRowId={(row) => row.status}
                  emptyTitle="No applications in scope"
                  emptySubtitle="Applications will appear here once the selected actor has accessible scheme records."
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Claim funnel</CardTitle>
              </CardHeader>
              <CardContent>
                <DataTable<PortalReportStatusBreakdownItem>
                  data={query.data.claimStatusBreakdown}
                  columns={claimStatusColumns}
                  getRowId={(row) => row.status}
                  emptyTitle="No claims in scope"
                  emptySubtitle="Submitted and released claims will populate this section once claim activity starts."
                />
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-6 xl:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Borrower concentration</CardTitle>
              </CardHeader>
              <CardContent>
                <DataTable<PortalReportBorrowerBreakdownItem>
                  data={query.data.borrowerBreakdown}
                  columns={borrowerColumns}
                  getRowId={(row) => row.entityId ?? row.entityLegalName}
                  emptyTitle="No borrower concentration yet"
                  emptySubtitle="Borrower activity will appear here once applications or releases are in scope."
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Lender participation</CardTitle>
              </CardHeader>
              <CardContent>
                <DataTable<PortalReportLenderBreakdownItem>
                  data={query.data.lenderBreakdown}
                  columns={lenderColumns}
                  getRowId={(row) => row.lenderName}
                  emptyTitle="No lender mapping yet"
                  emptySubtitle="This table fills once applications carry lender details."
                />
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Recent claim releases</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable<PortalReportRecentReleaseItem>
                data={query.data.recentReleases}
                columns={releaseColumns}
                getRowId={(row) => row.claimId}
                emptyTitle="No released claims yet"
                emptySubtitle="Released subvention claims will appear here with the borrower, scheme, amount, and release date."
              />
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: React.ReactNode }): JSX.Element {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="text-sm text-muted-foreground">{label}</div>
        <div className="mt-2 text-3xl font-semibold">{value}</div>
      </CardContent>
    </Card>
  );
}
