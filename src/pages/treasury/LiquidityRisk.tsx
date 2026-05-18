/**
 * Liquidity Risk (LCR / NSFR / Cash-flow ladder / Funding concentration).
 *
 * Wires to /api/v1/lending/liquidity-risk/*. Numbers are computed on the
 * backend from the GL, the borrowing book, the loan portfolio and the
 * investment portfolio (CLAUDE.md §4.9). RBI factors are coded as constants
 * on the service today; a future PR will move them to mst_lcr_runoff_factor.
 *
 * Routed at /admin/treasury/liquidity-risk in src/App.tsx.
 */

import { ArrowLeft, Droplets, ShieldCheck, ShieldAlert, ShieldX } from 'lucide-react';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  ComposedChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { AmountDisplay } from '@/components/common/AmountDisplay';
import { DateDisplay } from '@/components/common/DateDisplay';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { InlineTabs } from '@/components/common/InlineTabs';
import { PageHeader } from '@/components/common/PageHeader';
import { PercentageDisplay } from '@/components/common/PercentageDisplay';
import { SkeletonTable } from '@/components/common/SkeletonTable';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  useCashflowLadder,
  useFundingConcentration,
  useLcr,
  useNsfr,
} from '@/hooks/lending/useLiquidityRisk';
import { cn } from '@/lib/utils';
import type {
  CashflowBucket,
  ConcentrationRiskFlag,
  FundingConcentrationItem,
  LCRComponent,
  LiquidityStatus,
  NSFRComponent,
} from '@/services/lending/liquidityRiskApi';

// =============================================================================
// helpers
// =============================================================================

const STATUS_LABEL: Record<LiquidityStatus, string> = {
  ADEQUATE: 'Adequate',
  WATCH: 'Watch',
  BREACH: 'Breach',
  NO_DATA: 'No data',
};

function statusToHero(status: LiquidityStatus): {
  text: string;
  bg: string;
  ring: string;
  icon: typeof ShieldCheck;
} {
  switch (status) {
    case 'ADEQUATE':
      return {
        text: 'text-emerald-700',
        bg: 'bg-emerald-50',
        ring: 'ring-emerald-200',
        icon: ShieldCheck,
      };
    case 'WATCH':
      return {
        text: 'text-amber-700',
        bg: 'bg-amber-50',
        ring: 'ring-amber-200',
        icon: ShieldAlert,
      };
    case 'BREACH':
      return {
        text: 'text-rose-700',
        bg: 'bg-rose-50',
        ring: 'ring-rose-200',
        icon: ShieldX,
      };
    case 'NO_DATA':
    default:
      return {
        text: 'text-slate-600',
        bg: 'bg-slate-50',
        ring: 'ring-slate-200',
        icon: ShieldAlert,
      };
  }
}

function StatusBadge({ status }: { status: LiquidityStatus }) {
  const colour =
    status === 'ADEQUATE'
      ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
      : status === 'WATCH'
        ? 'bg-amber-100 text-amber-800 border-amber-200'
        : status === 'BREACH'
          ? 'bg-rose-100 text-rose-800 border-rose-200'
          : 'bg-slate-100 text-slate-700 border-slate-200';
  return <Badge className={cn('border', colour)}>{STATUS_LABEL[status]}</Badge>;
}

function ConcentrationBadge({ flag }: { flag: ConcentrationRiskFlag }) {
  const colour =
    flag === 'HIGH'
      ? 'bg-rose-100 text-rose-800 border-rose-200'
      : flag === 'MEDIUM'
        ? 'bg-amber-100 text-amber-800 border-amber-200'
        : 'bg-emerald-100 text-emerald-800 border-emerald-200';
  return <Badge className={cn('border', colour)}>{flag}</Badge>;
}

function HeroCard({
  title,
  subtitle,
  ratio,
  minimum,
  status,
  asOfDate,
}: {
  title: string;
  subtitle: string;
  ratio: string;
  minimum: string;
  status: LiquidityStatus;
  asOfDate: string | undefined;
}) {
  const palette = statusToHero(status);
  const Icon = palette.icon;
  const ratioNum = Number(ratio);
  return (
    <Card className={cn('ring-1', palette.ring)}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">{title}</CardTitle>
            <CardDescription>{subtitle}</CardDescription>
          </div>
          <div className={cn('rounded-full p-2', palette.bg)}>
            <Icon className={cn('h-5 w-5', palette.text)} />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline gap-3">
          <div className={cn('text-3xl font-bold tabular-nums', palette.text)}>
            {Number.isFinite(ratioNum) ? `${ratioNum.toFixed(2)}%` : '—'}
          </div>
          <StatusBadge status={status} />
        </div>
        <div className="mt-2 text-xs text-muted-foreground">
          Minimum required {Number(minimum).toFixed(0)}% ·{' '}
          {asOfDate ? (
            <>
              as of <DateDisplay date={asOfDate} />
            </>
          ) : (
            'as of today'
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function ComponentTable({
  rows,
  title,
  totalLabel,
  totalAmount,
}: {
  rows: (LCRComponent | NSFRComponent)[];
  title: string;
  totalLabel: string;
  totalAmount: string;
}) {
  if (rows.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={Droplets}
            title="No entries"
            subtitle="No data in this bucket for the current organisation."
          />
        </CardContent>
      </Card>
    );
  }
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Category</TableHead>
              <TableHead className="text-right">Amount</TableHead>
              <TableHead className="text-right">Factor</TableHead>
              <TableHead className="text-right">Weighted</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.label}>
                <TableCell>{row.label}</TableCell>
                <TableCell className="text-right tabular-nums">
                  <AmountDisplay amount={Number(row.amount)} />
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  <PercentageDisplay value={Number(row.weight) * 100} />
                </TableCell>
                <TableCell className="text-right font-medium tabular-nums">
                  <AmountDisplay amount={Number(row.weightedAmount)} />
                </TableCell>
              </TableRow>
            ))}
            <TableRow className="bg-muted/40">
              <TableCell className="font-semibold">{totalLabel}</TableCell>
              <TableCell />
              <TableCell />
              <TableCell className="text-right font-semibold tabular-nums">
                <AmountDisplay amount={Number(totalAmount)} />
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

// =============================================================================
// Tabs
// =============================================================================

function LCRTab() {
  const { data, isLoading, isError, error, refetch } = useLcr();

  if (isLoading && !data) return <SkeletonTable rows={6} />;
  if (isError) return <ErrorState error={error} onRetry={() => refetch()} />;
  if (!data) {
    return (
      <EmptyState
        icon={Droplets}
        title="No LCR data"
        subtitle="The LCR computation returned no inputs for this organisation."
      />
    );
  }

  const allHqla: LCRComponent[] = [...data.hqlaLevel1, ...data.hqlaLevel2A, ...data.hqlaLevel2B];

  const chartData = [
    { name: 'HQLA', value: Number(data.totalHqla) / 1e7 },
    { name: 'Net outflows (30d)', value: Number(data.netCashOutflows) / 1e7 },
  ];

  return (
    <div className="space-y-4">
      {/* Summary numbers */}
      <div className="grid gap-3 md:grid-cols-4">
        <SummaryStat label="Total HQLA" amount={data.totalHqla} />
        <SummaryStat label="Weighted outflows" amount={data.totalWeightedOutflows} />
        <SummaryStat
          label={data.inflowCapApplied ? 'Inflows (capped at 75%)' : 'Weighted inflows'}
          amount={data.totalWeightedInflows}
        />
        <SummaryStat label="Net outflows" amount={data.netCashOutflows} />
      </div>

      {/* HQLA vs Net outflows */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">HQLA vs Net cash outflows (₹ crore)</CardTitle>
          <CardDescription>
            LCR = HQLA / Net cash outflows over 30 days. Minimum 100%.
          </CardDescription>
        </CardHeader>
        <CardContent className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value) => `₹${Number(value ?? 0).toFixed(2)} Cr`} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {chartData.map((entry, idx) => (
                  <Cell key={entry.name} fill={idx === 0 ? '#10b981' : '#f43f5e'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <ComponentTable
          rows={allHqla}
          title="High-Quality Liquid Assets (HQLA)"
          totalLabel="Total HQLA"
          totalAmount={data.totalHqla}
        />
        <ComponentTable
          rows={data.outflows}
          title="Cash outflows (next 30 days)"
          totalLabel="Total weighted outflows"
          totalAmount={data.totalWeightedOutflows}
        />
      </div>

      <ComponentTable
        rows={data.inflows}
        title={
          data.inflowCapApplied
            ? 'Cash inflows (next 30 days, capped at 75% of outflows)'
            : 'Cash inflows (next 30 days)'
        }
        totalLabel="Total weighted inflows"
        totalAmount={data.totalWeightedInflows}
      />
    </div>
  );
}

function NSFRTab() {
  const { data, isLoading, isError, error, refetch } = useNsfr();

  if (isLoading && !data) return <SkeletonTable rows={6} />;
  if (isError) return <ErrorState error={error} onRetry={() => refetch()} />;
  if (!data) {
    return (
      <EmptyState
        icon={Droplets}
        title="No NSFR data"
        subtitle="The NSFR computation returned no inputs for this organisation."
      />
    );
  }

  const chartData = [
    { name: 'ASF (available)', value: Number(data.totalAsf) / 1e7 },
    { name: 'RSF (required)', value: Number(data.totalRsf) / 1e7 },
  ];

  return (
    <div className="space-y-4">
      <div className="grid gap-3 md:grid-cols-2">
        <SummaryStat label="Total Available Stable Funding (ASF)" amount={data.totalAsf} />
        <SummaryStat label="Total Required Stable Funding (RSF)" amount={data.totalRsf} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">ASF vs RSF (₹ crore)</CardTitle>
          <CardDescription>NSFR = ASF / RSF. Minimum 100%.</CardDescription>
        </CardHeader>
        <CardContent className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value) => `₹${Number(value ?? 0).toFixed(2)} Cr`} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {chartData.map((entry, idx) => (
                  <Cell key={entry.name} fill={idx === 0 ? '#10b981' : '#f43f5e'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <ComponentTable
          rows={data.asfComponents}
          title="Available Stable Funding (ASF)"
          totalLabel="Total ASF"
          totalAmount={data.totalAsf}
        />
        <ComponentTable
          rows={data.rsfComponents}
          title="Required Stable Funding (RSF)"
          totalLabel="Total RSF"
          totalAmount={data.totalRsf}
        />
      </div>
    </div>
  );
}

function CashflowLadderTab() {
  const { data, isLoading, isError, error, refetch } = useCashflowLadder();

  if (isLoading && !data) return <SkeletonTable rows={11} />;
  if (isError) return <ErrorState error={error} onRetry={() => refetch()} />;
  if (!data || data.buckets.length === 0) {
    return (
      <EmptyState
        icon={Droplets}
        title="No cash flows scheduled"
        subtitle="There are no scheduled inflows or outflows to plot a cash-flow ladder."
      />
    );
  }

  const chartData = data.buckets.map((b: CashflowBucket) => ({
    name: b.bucketLabel,
    inflows: Number(b.inflows) / 1e7,
    outflows: -(Number(b.outflows) / 1e7),
    cumulativeGap: Number(b.cumulativeGap) / 1e7,
  }));

  return (
    <div className="space-y-4">
      <div className="grid gap-3 md:grid-cols-3">
        <SummaryStat label="Total inflows" amount={data.totalInflows} />
        <SummaryStat label="Total outflows" amount={data.totalOutflows} />
        <SummaryStat label="Net position" amount={data.netPosition} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Cash-flow ladder (₹ crore)</CardTitle>
          <CardDescription>
            Inflows (loan repayments) vs outflows (borrowing repayments) bucketed by RBI ALM bands.
            Cumulative gap is the running sum, oldest first.
          </CardDescription>
        </CardHeader>
        <CardContent className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-25} textAnchor="end" height={70} />
              <YAxis />
              <Tooltip formatter={(value) => `₹${Number(value ?? 0).toFixed(2)} Cr`} />
              <Legend />
              <Bar dataKey="inflows" name="Inflows" fill="#10b981" />
              <Bar dataKey="outflows" name="Outflows" fill="#f43f5e" />
              <Line
                type="monotone"
                dataKey="cumulativeGap"
                name="Cumulative gap"
                stroke="#2563eb"
                strokeWidth={2}
                dot={{ r: 3 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Ladder detail</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Bucket</TableHead>
                <TableHead className="text-right">Inflows</TableHead>
                <TableHead className="text-right">Outflows</TableHead>
                <TableHead className="text-right">Gap</TableHead>
                <TableHead className="text-right">Cumulative gap</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.buckets.map((b: CashflowBucket) => {
                const gap = Number(b.gap);
                const cum = Number(b.cumulativeGap);
                return (
                  <TableRow key={b.bucketLabel}>
                    <TableCell>{b.bucketLabel}</TableCell>
                    <TableCell className="text-right tabular-nums">
                      <AmountDisplay amount={Number(b.inflows)} />
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      <AmountDisplay amount={Number(b.outflows)} />
                    </TableCell>
                    <TableCell
                      className={cn(
                        'text-right tabular-nums',
                        gap < 0 ? 'text-rose-700' : gap > 0 ? 'text-emerald-700' : '',
                      )}
                    >
                      <AmountDisplay amount={gap} />
                    </TableCell>
                    <TableCell
                      className={cn(
                        'text-right font-medium tabular-nums',
                        cum < 0 ? 'text-rose-700' : cum > 0 ? 'text-emerald-700' : '',
                      )}
                    >
                      <AmountDisplay amount={cum} />
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

function FundingConcentrationTab() {
  const { data, isLoading, isError, error, refetch } = useFundingConcentration(10);

  if (isLoading && !data) return <SkeletonTable rows={6} />;
  if (isError) return <ErrorState error={error} onRetry={() => refetch()} />;
  if (!data || data.items.length === 0) {
    return (
      <EmptyState
        icon={Droplets}
        title="No active borrowings"
        subtitle="There are no active borrowing facilities to compute funding concentration."
      />
    );
  }

  const chartData = data.items.map((item: FundingConcentrationItem) => ({
    name: item.lenderName.length > 14 ? `${item.lenderName.slice(0, 12)}…` : item.lenderName,
    outstanding: Number(item.outstanding) / 1e7,
    percent: Number(item.percentOfTotal),
  }));

  return (
    <div className="space-y-4">
      <div className="grid gap-3 md:grid-cols-3">
        <SummaryStat label="Total outstanding" amount={data.totalOutstanding} />
        <SummaryStat label="Lenders contributing" amount={String(data.totalLenders)} isCount />
        <SummaryStat
          label="High-concentration lenders ( > 20%)"
          amount={String(data.highConcentrationCount)}
          isCount
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Top {data.items.length} lenders</CardTitle>
          <CardDescription>
            Outstanding borrowing in ₹ crore. A lender exceeding 20% of total funding is flagged
            HIGH.
          </CardDescription>
        </CardHeader>
        <CardContent className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis type="category" dataKey="name" width={120} />
              <Tooltip
                formatter={(value, key) => {
                  const n = Number(value ?? 0);
                  return key === 'outstanding' ? `₹${n.toFixed(2)} Cr` : `${n.toFixed(2)}%`;
                }}
              />
              <Bar dataKey="outstanding" fill="#2563eb" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Lender breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Lender</TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="text-right">Outstanding</TableHead>
                <TableHead className="text-right">% of total</TableHead>
                <TableHead>Risk</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((item: FundingConcentrationItem) => (
                <TableRow key={item.lenderId}>
                  <TableCell className="font-medium">{item.lenderName}</TableCell>
                  <TableCell className="text-muted-foreground">{item.lenderType ?? '—'}</TableCell>
                  <TableCell className="text-right tabular-nums">
                    <AmountDisplay amount={Number(item.outstanding)} />
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    <PercentageDisplay value={Number(item.percentOfTotal)} />
                  </TableCell>
                  <TableCell>
                    <ConcentrationBadge flag={item.riskFlag} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

function SummaryStat({
  label,
  amount,
  isCount = false,
}: {
  label: string;
  amount: string;
  isCount?: boolean;
}) {
  return (
    <Card>
      <CardContent className="pt-4">
        <div className="text-xs text-muted-foreground">{label}</div>
        <div className="mt-1 text-lg font-semibold tabular-nums">
          {isCount ? amount : <AmountDisplay amount={Number(amount)} />}
        </div>
      </CardContent>
    </Card>
  );
}

// =============================================================================
// Page
// =============================================================================

export default function LiquidityRisk() {
  const navigate = useNavigate();

  // The hero cards read the LCR + NSFR snapshots up front so the user sees
  // the colour-coded headline without switching tabs. Each tab still owns its
  // own hook call — react-query dedupes on the shared query key.
  const lcr = useLcr();
  const nsfr = useNsfr();

  const tabs = useMemo(
    () => [
      { value: 'lcr', label: 'LCR', content: <LCRTab /> },
      { value: 'nsfr', label: 'NSFR', content: <NSFRTab /> },
      { value: 'cashflow', label: 'Cash-flow Ladder', content: <CashflowLadderTab /> },
      {
        value: 'concentration',
        label: 'Funding Concentration',
        content: <FundingConcentrationTab />,
      },
    ],
    [],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Liquidity Risk"
        subtitle="LCR, NSFR, cash-flow ladder, and funding-concentration analytics"
        actions={
          <Button variant="ghost" onClick={() => navigate('/admin/treasury')}>
            <ArrowLeft className="mr-2 h-4 w-4" /> Back to Treasury
          </Button>
        }
      />

      {/* Hero cards. Skeleton while loading; quietly hide on error — the
          tabs below carry the full error surface. */}
      <div className="grid gap-4 md:grid-cols-2">
        {lcr.isLoading || !lcr.data ? (
          <Card>
            <CardContent className="py-6">
              <SkeletonTable rows={1} />
            </CardContent>
          </Card>
        ) : (
          <HeroCard
            title="Liquidity Coverage Ratio (LCR)"
            subtitle="HQLA / Net cash outflows over 30 days"
            ratio={lcr.data.lcrPercent}
            minimum={lcr.data.minimumRequiredPercent}
            status={lcr.data.status}
            asOfDate={lcr.data.asOfDate}
          />
        )}
        {nsfr.isLoading || !nsfr.data ? (
          <Card>
            <CardContent className="py-6">
              <SkeletonTable rows={1} />
            </CardContent>
          </Card>
        ) : (
          <HeroCard
            title="Net Stable Funding Ratio (NSFR)"
            subtitle="Available Stable Funding / Required Stable Funding"
            ratio={nsfr.data.nsfrPercent}
            minimum={nsfr.data.minimumRequiredPercent}
            status={nsfr.data.status}
            asOfDate={nsfr.data.asOfDate}
          />
        )}
      </div>

      <InlineTabs tabs={tabs} paramName="tab" />
    </div>
  );
}
