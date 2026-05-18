/**
 * Counterparty Risk — top exposures, sector & rating concentration,
 * single-borrower / group limit breaches.
 *
 * Routed at /admin/treasury/counterparty-risk (see src/App.tsx).
 *
 * Per CLAUDE.md §4.9 / RBI SBR:
 *   single-borrower limit = 15% of Tier-1 (20% for infrastructure)
 *   group limit            = 25% of Tier-1
 *   status thresholds      = WITHIN_LIMIT (<80%) | NEAR_LIMIT (80–100%) | BREACHED (>100%)
 *
 * Wire format is camelCase. Money/percent are JSON strings (Pydantic Decimal —
 * CLAUDE.md §6.2). Coerce via `Number(...)` for display arithmetic only.
 */

import { AlertTriangle, ArrowLeft, Building2, TrendingUp, Users } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { AmountDisplay } from '@/components/common/AmountDisplay';
import { DataTable, type Column } from '@/components/common/DataTable';
import { PageHeader } from '@/components/common/PageHeader';
import { PercentageDisplay } from '@/components/common/PercentageDisplay';
import { LimitStatusPill } from '@/components/lending/common/LimitStatusPill';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  useCounterpartyExposures,
  useLimitBreaches,
  useRatingDistribution,
  useSectorConcentration,
} from '@/hooks/lending/useCounterpartyRisk';
import type {
  CounterpartyExposureItem,
  LimitBreachItem,
  RatingDistributionItem,
  SectorConcentrationItem,
} from '@/services/lending/counterpartyRiskApi';

// --------------------------------------------------------------------- utils

function toNumber(s: string | number | null | undefined): number {
  if (s === null || s === undefined) return 0;
  return typeof s === 'number' ? s : Number(s);
}

function counterpartyTypeLabel(type: CounterpartyExposureItem['counterpartyType']): string {
  switch (type) {
    case 'ENTITY':
      return 'Borrower';
    case 'ISSUER':
      return 'Issuer';
    case 'LENDER':
      return 'Lender';
  }
}

// --------------------------------------------------------------------- page

export default function CounterpartyRisk(): JSX.Element {
  const navigate = useNavigate();

  const exposuresQuery = useCounterpartyExposures(50);
  const sectorsQuery = useSectorConcentration();
  const ratingsQuery = useRatingDistribution();
  const breachesQuery = useLimitBreaches();

  const exposures = exposuresQuery.data;

  // Summary card values derived from the exposures payload (single source of
  // truth — the breaches endpoint is a filtered view of the same data).
  const totalCounterparties = exposures?.totalCounterparties ?? 0;
  const totalExposure = toNumber(exposures?.totalExposure);
  const nearLimitCount = exposures?.nearLimitCount ?? 0;
  const breachedCount = exposures?.breachedCount ?? 0;

  // ---------- column definitions ------------------------------------------

  const exposureColumns: Column<CounterpartyExposureItem>[] = [
    {
      key: 'counterpartyName',
      header: 'Counterparty',
      render: (row) => (
        <div className="min-w-0">
          <div className="truncate font-medium text-foreground">{row.counterpartyName}</div>
          <div className="text-xs text-muted-foreground">
            {counterpartyTypeLabel(row.counterpartyType)}
            {row.sector ? ` · ${row.sector.replace(/_/g, ' ')}` : ''}
            {row.isInfrastructure ? ' · Infra' : ''}
          </div>
        </div>
      ),
    },
    {
      key: 'rating',
      header: 'Rating',
      render: (row) => <span className="text-sm text-muted-foreground">{row.rating ?? '-'}</span>,
    },
    {
      key: 'loanExposure',
      header: 'Loans',
      align: 'right',
      render: (row) => <AmountDisplay amount={toNumber(row.loanExposure)} compact />,
    },
    {
      key: 'investmentExposure',
      header: 'Investments',
      align: 'right',
      render: (row) => <AmountDisplay amount={toNumber(row.investmentExposure)} compact />,
    },
    {
      key: 'borrowingExposure',
      header: 'Borrowings',
      align: 'right',
      render: (row) => <AmountDisplay amount={toNumber(row.borrowingExposure)} compact />,
    },
    {
      key: 'totalExposure',
      header: 'Total',
      align: 'right',
      sortable: true,
      sortValue: (row) => toNumber(row.totalExposure),
      render: (row) => <AmountDisplay amount={toNumber(row.totalExposure)} compact />,
    },
    {
      key: 'limitAmount',
      header: 'Limit',
      align: 'right',
      render: (row) => <AmountDisplay amount={toNumber(row.limitAmount)} compact />,
    },
    {
      key: 'utilizationPercent',
      header: 'Utilisation',
      align: 'right',
      sortable: true,
      sortValue: (row) => toNumber(row.utilizationPercent),
      render: (row) => <PercentageDisplay value={toNumber(row.utilizationPercent)} decimals={1} />,
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => <LimitStatusPill status={row.status} />,
    },
  ];

  const sectorColumns: Column<SectorConcentrationItem>[] = [
    {
      key: 'sector',
      header: 'Sector',
      render: (row) => <span className="font-medium">{row.sector.replace(/_/g, ' ')}</span>,
    },
    {
      key: 'count',
      header: 'Loans',
      align: 'right',
      sortable: true,
      sortValue: (row) => row.count,
    },
    {
      key: 'exposure',
      header: 'Exposure',
      align: 'right',
      sortable: true,
      sortValue: (row) => toNumber(row.exposure),
      render: (row) => <AmountDisplay amount={toNumber(row.exposure)} compact />,
    },
    {
      key: 'percentOfPortfolio',
      header: '% of portfolio',
      align: 'right',
      sortable: true,
      sortValue: (row) => toNumber(row.percentOfPortfolio),
      render: (row) => <PercentageDisplay value={toNumber(row.percentOfPortfolio)} decimals={2} />,
    },
  ];

  const ratingColumns: Column<RatingDistributionItem>[] = [
    {
      key: 'rating',
      header: 'Internal rating',
      render: (row) => <span className="font-medium tabular-nums">{row.rating}</span>,
    },
    {
      key: 'count',
      header: 'Loans',
      align: 'right',
      sortable: true,
      sortValue: (row) => row.count,
    },
    {
      key: 'exposure',
      header: 'Exposure',
      align: 'right',
      sortable: true,
      sortValue: (row) => toNumber(row.exposure),
      render: (row) => <AmountDisplay amount={toNumber(row.exposure)} compact />,
    },
    {
      key: 'percentOfPortfolio',
      header: '% of portfolio',
      align: 'right',
      sortable: true,
      sortValue: (row) => toNumber(row.percentOfPortfolio),
      render: (row) => <PercentageDisplay value={toNumber(row.percentOfPortfolio)} decimals={2} />,
    },
  ];

  const breachColumns: Column<LimitBreachItem>[] = [
    {
      key: 'counterpartyName',
      header: 'Counterparty',
      render: (row) => (
        <div className="min-w-0">
          <div className="truncate font-medium text-foreground">{row.counterpartyName}</div>
          <div className="text-xs text-muted-foreground">
            {counterpartyTypeLabel(row.counterpartyType)}
            {row.isInfrastructure ? ' · Infra (20% limit)' : ''}
          </div>
        </div>
      ),
    },
    {
      key: 'totalExposure',
      header: 'Exposure',
      align: 'right',
      sortable: true,
      sortValue: (row) => toNumber(row.totalExposure),
      render: (row) => <AmountDisplay amount={toNumber(row.totalExposure)} compact />,
    },
    {
      key: 'limitAmount',
      header: 'Limit',
      align: 'right',
      render: (row) => <AmountDisplay amount={toNumber(row.limitAmount)} compact />,
    },
    {
      key: 'utilizationPercent',
      header: 'Utilisation',
      align: 'right',
      sortable: true,
      sortValue: (row) => toNumber(row.utilizationPercent),
      render: (row) => <PercentageDisplay value={toNumber(row.utilizationPercent)} decimals={1} />,
    },
    {
      key: 'severity',
      header: 'Severity',
      render: (row) => (
        <span
          className={
            row.severity === 'CRITICAL'
              ? 'text-xs font-semibold text-red-700'
              : row.severity === 'BREACH'
                ? 'text-xs font-medium text-red-600'
                : 'text-xs font-medium text-amber-700'
          }
        >
          {row.severity}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => <LimitStatusPill status={row.status} />,
    },
  ];

  // ---------- render ------------------------------------------------------

  return (
    <div className="space-y-6">
      <PageHeader
        title="Counterparty Risk"
        subtitle="Top exposures, sector and rating distribution, single-borrower / group limit breaches"
        breadcrumbs={[{ label: 'Treasury', to: '/admin/treasury' }, { label: 'Counterparty Risk' }]}
        actions={
          <Button variant="ghost" onClick={() => navigate('/admin/treasury')}>
            <ArrowLeft className="mr-2 h-4 w-4" /> Back to Treasury
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          icon={<Users className="h-5 w-5 text-primary" />}
          label="Counterparties"
          value={totalCounterparties.toString()}
        />
        <SummaryCard
          icon={<TrendingUp className="h-5 w-5 text-primary" />}
          label="Total exposure"
          value={<AmountDisplay amount={totalExposure} compact />}
        />
        <SummaryCard
          icon={<Building2 className="h-5 w-5 text-amber-600" />}
          label="Near limit (≥80%)"
          value={nearLimitCount.toString()}
          tone={nearLimitCount > 0 ? 'warning' : 'default'}
        />
        <SummaryCard
          icon={<AlertTriangle className="h-5 w-5 text-red-600" />}
          label="Breached (>100%)"
          value={breachedCount.toString()}
          tone={breachedCount > 0 ? 'danger' : 'default'}
        />
      </div>

      <Tabs defaultValue="exposures">
        <TabsList>
          <TabsTrigger value="exposures">Top exposures</TabsTrigger>
          <TabsTrigger value="sectors">Sector concentration</TabsTrigger>
          <TabsTrigger value="ratings">Rating distribution</TabsTrigger>
          <TabsTrigger value="breaches">
            Limit breaches
            {(nearLimitCount > 0 || breachedCount > 0) && (
              <span className="ml-1.5 rounded-full bg-red-100 px-1.5 text-xs text-red-700">
                {nearLimitCount + breachedCount}
              </span>
            )}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="exposures" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Top counterparty exposures</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                data={exposures?.items ?? []}
                columns={exposureColumns}
                getRowId={(row) => row.counterpartyId}
                isLoading={exposuresQuery.isLoading}
                error={exposuresQuery.error}
                onRetry={() => void exposuresQuery.refetch()}
                emptyTitle="No counterparty exposures"
                emptySubtitle="No active loans, investments, or borrowings on the books."
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sectors" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Sector concentration</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                data={sectorsQuery.data?.items ?? []}
                columns={sectorColumns}
                getRowId={(row) => row.sector}
                isLoading={sectorsQuery.isLoading}
                error={sectorsQuery.error}
                onRetry={() => void sectorsQuery.refetch()}
                emptyTitle="No sector exposure"
                emptySubtitle="Sector concentration is calculated from active loan accounts."
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ratings" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Internal rating distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                data={ratingsQuery.data?.items ?? []}
                columns={ratingColumns}
                getRowId={(row) => row.rating}
                isLoading={ratingsQuery.isLoading}
                error={ratingsQuery.error}
                onRetry={() => void ratingsQuery.refetch()}
                emptyTitle="No rating distribution"
                emptySubtitle="Ratings come from entity.internal_rating on the borrower master."
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="breaches" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Single-borrower limit breaches</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                data={breachesQuery.data?.items ?? []}
                columns={breachColumns}
                getRowId={(row) => row.counterpartyId}
                isLoading={breachesQuery.isLoading}
                error={breachesQuery.error}
                onRetry={() => void breachesQuery.refetch()}
                emptyTitle="No limit breaches"
                emptySubtitle="All counterparties are within 80% of their RBI single-borrower limit."
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

// --------------------------------------------------------------------- card

interface SummaryCardProps {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
  tone?: 'default' | 'warning' | 'danger';
}

function SummaryCard({ icon, label, value, tone = 'default' }: SummaryCardProps): JSX.Element {
  const toneClass =
    tone === 'danger'
      ? 'border-red-200 bg-red-50'
      : tone === 'warning'
        ? 'border-amber-200 bg-amber-50'
        : '';
  return (
    <Card className={toneClass}>
      <CardContent className="flex items-center gap-3 py-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-background">
          {icon}
        </div>
        <div className="min-w-0">
          <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
          <div className="text-lg font-semibold">{value}</div>
        </div>
      </CardContent>
    </Card>
  );
}
