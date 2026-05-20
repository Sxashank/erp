/**
 * CRAR Dashboard — Capital adequacy + large-exposure surface.
 *
 * Wired against:
 *   GET /api/v1/reports/regulatory/crar                       (useCrar)
 *   GET /api/v1/reports/regulatory/crar/composition           (useCrarComposition)
 *   GET /api/v1/reports/regulatory/crar/trend                 (useCrarTrend)
 *   GET /api/v1/reports/regulatory/crar/infrastructure-ratio  (useInfrastructureRatio)
 *   GET /api/v1/reports/regulatory/large-exposure             (useLargeExposure)
 *
 * Section NOT wired: regulatory-returns calendar — that surface is
 * owned by the compliance module (`/compliance`, see CLAUDE.md §4.18).
 * A small EmptyState links there rather than duplicating logic.
 *
 * See CLAUDE.md §5.7 (loading / empty / error states) and §9.7.
 */

import {
  AlertTriangle,
  Building2,
  CheckCircle,
  Download,
  Info,
  Shield,
  TrendingUp,
  Calendar,
  TrendingDown,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { SkeletonTable } from '@/components/common/SkeletonTable';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import {
  useCrar,
  useCrarComposition,
  useCrarTrend,
  useInfrastructureRatio,
  useLargeExposure,
} from '@/hooks/reports/useRegulatoryReports';
import type { CapitalCompositionLine, NumericValue } from '@/services/reports/regulatoryApi';

/** Backend currently emits `float`, but the contract may flip to decimal
 *  strings later (CLAUDE.md §6.2). Coerce at the display boundary only. */
function toNumber(value: NumericValue | null | undefined): number {
  if (value === null || value === undefined) return 0;
  if (typeof value === 'number') return value;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

type ComplianceStatus = 'COMPLIANT' | 'WARNING' | 'BREACH';

function deriveStatus(actual: number, minimum: number): ComplianceStatus {
  if (actual < minimum) return 'BREACH';
  if (actual < minimum + 1) return 'WARNING';
  return 'COMPLIANT';
}

function statusBadgeClass(status: string): string {
  switch (status) {
    case 'COMPLIANT':
    case 'WITHIN_LIMIT':
      return 'bg-green-100 text-green-700';
    case 'WARNING':
    case 'NEAR_LIMIT':
      return 'bg-amber-100 text-amber-700';
    case 'BREACH':
    case 'BREACHED':
      return 'bg-red-100 text-red-700';
    default:
      return 'bg-gray-100 text-gray-700';
  }
}

export default function CRARDashboard() {
  const crarQuery = useCrar();
  const largeExposureQuery = useLargeExposure();
  const compositionQuery = useCrarComposition();
  const trendQuery = useCrarTrend({ months: 12 });
  const infraRatioQuery = useInfrastructureRatio();

  const crarData = crarQuery.data;
  const tier1Capital = toNumber(crarData?.capital.tier1_capital);
  const tier2Capital = toNumber(crarData?.capital.tier2_capital);
  const totalCapital = toNumber(crarData?.capital.total_capital);
  const totalRwa = toNumber(crarData?.risk_weighted_assets.total_rwa);
  const creditRiskRwa = toNumber(crarData?.risk_weighted_assets.credit_risk_rwa);
  const marketRiskRwa = toNumber(crarData?.risk_weighted_assets.market_risk_rwa);
  const operationalRiskRwa = toNumber(crarData?.risk_weighted_assets.operational_risk_rwa);
  const crarRatio = toNumber(crarData?.ratios.crar);
  const tier1Ratio = toNumber(crarData?.ratios.tier1_ratio);
  const minimumCrar = toNumber(crarData?.ratios.minimum_crar_required) || 15;
  // RBI: Tier-1 minimum is 10% (separate from total CRAR of 15%).
  const tier1Minimum = 10;
  const surplusDeficit = toNumber(crarData?.ratios.surplus_deficit);

  const tier1Status = deriveStatus(tier1Ratio, tier1Minimum);
  const totalStatus = deriveStatus(crarRatio, minimumCrar);

  const rwaBreakdown: { category: string; rwa: number }[] = [
    { category: 'Credit Risk', rwa: creditRiskRwa },
    { category: 'Market Risk', rwa: marketRiskRwa },
    { category: 'Operational Risk', rwa: operationalRiskRwa },
  ];

  const crarReturnsZero = crarQuery.isSuccess && totalRwa === 0 && totalCapital === 0;

  const largeExposures = largeExposureQuery.data?.exposures ?? [];
  const largeExposureTier1 = toNumber(largeExposureQuery.data?.tier1_capital);

  // Single-borrower limit per CLAUDE.md §4.9: 15% of Tier-1 capital
  // (infra carve-out 20%). Group limit 25% of Tier-1.
  const SINGLE_BORROWER_LIMIT_PCT = 15;
  const GROUP_BORROWER_LIMIT_PCT = 25;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Regulatory Dashboard"
        subtitle="CRAR, Exposure Limits & Regulatory Compliance"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" disabled>
              <Calendar className="mr-2 h-4 w-4" />
              {crarData?.as_of_date ?? 'Today'}
            </Button>
            <Button variant="outline" disabled>
              <Download className="mr-2 h-4 w-4" />
              Export Report
            </Button>
          </div>
        }
      />

      {/* CRAR Summary Cards */}
      {crarQuery.isLoading ? (
        <div className="grid gap-4 md:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-32" />
                <Skeleton className="mt-2 h-2 w-full" />
                <Skeleton className="mt-2 h-3 w-40" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : crarQuery.isError ? (
        <ErrorState
          title="Unable to load CRAR report"
          error={crarQuery.error}
          onRetry={() => void crarQuery.refetch()}
        />
      ) : crarReturnsZero ? (
        <EmptyState
          title="No CRAR data yet"
          subtitle="The capital adequacy aggregator returned zero values. Once vouchers + risk-weight rules are seeded the dashboard will populate automatically."
        />
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Tier-I CRAR</CardTitle>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger>
                      <Info className="h-4 w-4 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Minimum required: {tier1Minimum}%</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <span className="text-2xl font-bold">
                    <PercentageDisplay value={tier1Ratio} />
                  </span>
                  <Badge className={statusBadgeClass(tier1Status)}>
                    {tier1Status === 'COMPLIANT' ? (
                      <CheckCircle className="mr-1 h-3 w-3" />
                    ) : (
                      <AlertTriangle className="mr-1 h-3 w-3" />
                    )}
                    {tier1Status}
                  </Badge>
                </div>
                <Progress value={Math.min((tier1Ratio / 25) * 100, 100)} className="mt-2 h-2" />
                <p className="mt-1 text-xs text-muted-foreground">
                  Min: {tier1Minimum}% | Buffer:{' '}
                  <PercentageDisplay value={tier1Ratio - tier1Minimum} />
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total CRAR</CardTitle>
                <Shield className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <span className="text-2xl font-bold text-green-600">
                    <PercentageDisplay value={crarRatio} />
                  </span>
                  <Badge className={statusBadgeClass(totalStatus)}>{totalStatus}</Badge>
                </div>
                <Progress value={Math.min((crarRatio / 25) * 100, 100)} className="mt-2 h-2" />
                <p className="mt-1 text-xs text-muted-foreground">
                  Min: {minimumCrar}% | Surplus: <PercentageDisplay value={surplusDeficit} />
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Capital</CardTitle>
                <Building2 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <AmountDisplay amount={totalCapital} abbreviated className="text-2xl font-bold" />
                <p className="mt-1 text-xs text-muted-foreground">
                  Tier-I: <AmountDisplay amount={tier1Capital} abbreviated /> | Tier-II:{' '}
                  <AmountDisplay amount={tier2Capital} abbreviated />
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Risk-Weighted Assets</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <AmountDisplay amount={totalRwa} abbreviated className="text-2xl font-bold" />
                <p className="mt-1 text-xs text-muted-foreground">Capital / RWA determines CRAR</p>
              </CardContent>
            </Card>
          </div>

          {/* RWA Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>Risk-Weighted Assets Breakdown</CardTitle>
              <CardDescription>
                Components of total risk-weighted assets as of {crarData?.as_of_date}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Category</TableHead>
                    <TableHead className="text-right">RWA</TableHead>
                    <TableHead className="text-right">% of Total</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rwaBreakdown.map((rwa) => (
                    <TableRow key={rwa.category}>
                      <TableCell className="font-medium">{rwa.category}</TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={rwa.rwa} abbreviated />
                      </TableCell>
                      <TableCell className="text-right text-muted-foreground">
                        <PercentageDisplay value={totalRwa > 0 ? (rwa.rwa / totalRwa) * 100 : 0} />
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="bg-muted/50 font-bold">
                    <TableCell>Total RWA</TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={totalRwa} abbreviated />
                    </TableCell>
                    <TableCell className="text-right">100%</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}

      {/* Large Exposure Table */}
      <Card>
        <CardHeader>
          <CardTitle>Large Exposure Report</CardTitle>
          <CardDescription>
            Single borrower limit: {SINGLE_BORROWER_LIMIT_PCT}% of Tier-I capital | Group borrower
            limit: {GROUP_BORROWER_LIMIT_PCT}% of Tier-I capital
          </CardDescription>
        </CardHeader>
        <CardContent>
          {largeExposureQuery.isLoading ? (
            <SkeletonTable rows={4} columns={4} />
          ) : largeExposureQuery.isError ? (
            <ErrorState
              title="Unable to load large exposures"
              error={largeExposureQuery.error}
              onRetry={() => void largeExposureQuery.refetch()}
            />
          ) : largeExposures.length === 0 ? (
            <EmptyState
              title="No large exposures"
              subtitle={`No borrower exposure exceeds ${toNumber(
                largeExposureQuery.data?.threshold_percentage,
              )}% of Tier-I capital.`}
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Entity Name</TableHead>
                  <TableHead className="text-right">Exposure</TableHead>
                  <TableHead className="text-right">% of Tier-I</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {largeExposures.map((exp, index) => {
                  const exposure = toNumber(exp.exposure_amount);
                  const exposurePct =
                    largeExposureTier1 > 0 ? (exposure / largeExposureTier1) * 100 : 0;
                  const limitStatus: string =
                    exposurePct >= SINGLE_BORROWER_LIMIT_PCT
                      ? 'BREACHED'
                      : exposurePct >= SINGLE_BORROWER_LIMIT_PCT - 5
                        ? 'NEAR_LIMIT'
                        : 'WITHIN_LIMIT';
                  return (
                    <TableRow key={`${exp.borrower_name}-${index}`}>
                      <TableCell className="font-medium">{exp.borrower_name}</TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={exposure} abbreviated />
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        <PercentageDisplay value={exposurePct} />
                      </TableCell>
                      <TableCell>
                        <Badge className={statusBadgeClass(limitStatus)}>
                          {limitStatus === 'WITHIN_LIMIT' && (
                            <CheckCircle className="mr-1 h-3 w-3" />
                          )}
                          {limitStatus === 'NEAR_LIMIT' && (
                            <AlertTriangle className="mr-1 h-3 w-3" />
                          )}
                          {limitStatus.replace('_', ' ')}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Capital Composition (Tier-1 / Tier-2 line items) */}
      <Card>
        <CardHeader>
          <CardTitle>Capital Composition</CardTitle>
          <CardDescription>
            Tier-I / Tier-II breakdown ladders up to total regulatory capital. Mapping is heuristic
            against COA group names, tracked in `regulatory_report_service.py`.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {compositionQuery.isLoading ? (
            <SkeletonTable rows={6} columns={2} />
          ) : compositionQuery.isError ? (
            <ErrorState
              title="Unable to load capital composition"
              error={compositionQuery.error}
              onRetry={() => void compositionQuery.refetch()}
            />
          ) : !compositionQuery.data ||
            (compositionQuery.data.tier1Lines.length === 0 &&
              compositionQuery.data.tier2Lines.length === 0) ? (
            <EmptyState
              title="No capital composition data"
              subtitle="Once the COA is seeded with equity / reserves / sub-debt account groups the composition will populate automatically."
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Component</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {compositionQuery.data.tier1Lines.map(
                  (line: CapitalCompositionLine, idx: number) => (
                    <TableRow key={`t1-${idx}-${line.label}`}>
                      <TableCell className={line.isSubtotal ? 'border-t font-semibold' : ''}>
                        {line.label}
                      </TableCell>
                      <TableCell
                        className={`text-right tabular-nums ${
                          line.isSubtotal ? 'border-t font-semibold' : ''
                        }`}
                      >
                        <AmountDisplay amount={toNumber(line.amount)} abbreviated />
                      </TableCell>
                    </TableRow>
                  ),
                )}
                <TableRow className="border-t bg-muted/30 font-semibold">
                  <TableCell>Tier-I Sub-total</TableCell>
                  <TableCell className="text-right tabular-nums">
                    <AmountDisplay
                      amount={toNumber(compositionQuery.data.tier1Total)}
                      abbreviated
                    />
                  </TableCell>
                </TableRow>
                {compositionQuery.data.tier2Lines.map(
                  (line: CapitalCompositionLine, idx: number) => (
                    <TableRow key={`t2-${idx}-${line.label}`}>
                      <TableCell className={line.isSubtotal ? 'border-t font-semibold' : ''}>
                        {line.label}
                      </TableCell>
                      <TableCell
                        className={`text-right tabular-nums ${
                          line.isSubtotal ? 'border-t font-semibold' : ''
                        }`}
                      >
                        <AmountDisplay amount={toNumber(line.amount)} abbreviated />
                      </TableCell>
                    </TableRow>
                  ),
                )}
                <TableRow className="border-t bg-muted/30 font-semibold">
                  <TableCell>Tier-II Sub-total</TableCell>
                  <TableCell className="text-right tabular-nums">
                    <AmountDisplay
                      amount={toNumber(compositionQuery.data.tier2Total)}
                      abbreviated
                    />
                  </TableCell>
                </TableRow>
                <TableRow className="border-t-2 bg-muted/50 font-bold">
                  <TableCell>Total Capital</TableCell>
                  <TableCell className="text-right tabular-nums">
                    <AmountDisplay
                      amount={toNumber(compositionQuery.data.totalCapital)}
                      abbreviated
                    />
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* CRAR Trend (historical series) */}
      <Card>
        <CardHeader>
          <CardTitle>CRAR Trend</CardTitle>
          <CardDescription>
            12-month rolling CRAR + Tier-I ratio from `fin_capital_snapshot`. Snapshots accrue as
            the daily roll-up job runs.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {trendQuery.isLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : trendQuery.isError ? (
            <ErrorState
              title="Unable to load CRAR trend"
              error={trendQuery.error}
              onRetry={() => void trendQuery.refetch()}
            />
          ) : !trendQuery.data || trendQuery.data.snapshots.length === 0 ? (
            <EmptyState
              title="No historical snapshots yet"
              subtitle="Snapshots accrue over time as the daily snapshot job runs. Once a few weeks of history exist the chart will render automatically."
            />
          ) : (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={trendQuery.data.snapshots.map((s) => ({
                    snapshotDate: s.snapshotDate,
                    crar: toNumber(s.crar),
                    tier1Ratio: toNumber(s.tier1Ratio),
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="snapshotDate" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <RechartsTooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="crar"
                    name="CRAR %"
                    stroke="#059669"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="tier1Ratio"
                    name="Tier-I %"
                    stroke="#2563eb"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      {/* NBFC-IFC Infrastructure Ratio */}
      <Card>
        <CardHeader>
          <CardTitle>NBFC-IFC Infrastructure Ratio</CardTitle>
          <CardDescription>
            Infrastructure book ÷ total active loan book. RBI requires ≥ 75% for NBFC-IFC
            eligibility.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {infraRatioQuery.isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-40" />
              <Skeleton className="h-2 w-full" />
              <Skeleton className="h-4 w-64" />
            </div>
          ) : infraRatioQuery.isError ? (
            <ErrorState
              title="Unable to load infrastructure ratio"
              error={infraRatioQuery.error}
              onRetry={() => void infraRatioQuery.refetch()}
            />
          ) : !infraRatioQuery.data || toNumber(infraRatioQuery.data.totalLoansAmount) === 0 ? (
            <EmptyState
              title="No active loan book"
              subtitle="Once active loans exist the infrastructure ratio will be computed automatically."
            />
          ) : (
            (() => {
              const infraRatio = toNumber(infraRatioQuery.data.infrastructureRatioPercent);
              const minRequired = toNumber(infraRatioQuery.data.minimumRequiredPercent);
              const infraAmount = toNumber(infraRatioQuery.data.infrastructureLoansAmount);
              const totalAmount = toNumber(infraRatioQuery.data.totalLoansAmount);
              const status = infraRatioQuery.data.status;
              const statusClass = statusBadgeClass(
                status === 'QUALIFIED' ? 'COMPLIANT' : status === 'AT_RISK' ? 'WARNING' : 'BREACH',
              );
              return (
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl font-bold">
                      <PercentageDisplay value={infraRatio} />
                    </span>
                    <Badge className={statusClass}>
                      {status === 'QUALIFIED' ? (
                        <CheckCircle className="mr-1 h-3 w-3" />
                      ) : status === 'AT_RISK' ? (
                        <AlertTriangle className="mr-1 h-3 w-3" />
                      ) : (
                        <TrendingDown className="mr-1 h-3 w-3" />
                      )}
                      {status.replace('_', ' ')}
                    </Badge>
                  </div>
                  <Progress value={Math.min((infraRatio / 100) * 100, 100)} className="h-2" />
                  <div className="grid gap-3 text-sm text-muted-foreground md:grid-cols-3">
                    <div>
                      <p className="text-xs uppercase tracking-wide">Infrastructure book</p>
                      <p className="font-medium text-foreground">
                        <AmountDisplay amount={infraAmount} abbreviated />
                      </p>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-wide">Total active book</p>
                      <p className="font-medium text-foreground">
                        <AmountDisplay amount={totalAmount} abbreviated />
                      </p>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-wide">Minimum required</p>
                      <p className="font-medium text-foreground">
                        <PercentageDisplay value={minRequired} />
                      </p>
                    </div>
                  </div>
                </div>
              );
            })()
          )}
        </CardContent>
      </Card>

      {/* Regulatory Returns Calendar — owned by the compliance module
          (CLAUDE.md §4.18). We surface a pointer rather than duplicating
          the logic here. */}
      <Card>
        <CardHeader>
          <CardTitle>Regulatory Returns Calendar</CardTitle>
          <CardDescription>
            NBS-1 / NBS-2 / NBS-9, ALM-1 / 2, CRILC filings and reminders.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState
            title="Tracked under Compliance"
            subtitle="Regulatory-returns calendar is part of the compliance module — open the compliance dashboard for filing schedules, D-7 / D+3 reminders, and audit trail."
            action={
              <Button variant="outline" asChild>
                <Link to="/compliance">Open Compliance</Link>
              </Button>
            }
          />
        </CardContent>
      </Card>

      {/* Compliance Notes */}
      <Card className="border-blue-200 bg-blue-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-blue-900">
            <Info className="h-5 w-5" />
            Regulatory Compliance Notes
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-blue-800">
          <p>
            <strong>CRAR Requirement:</strong> NBFCs must maintain a minimum CRAR of {minimumCrar}%
            (Tier-I ≥ {tier1Minimum}%) per RBI Master Direction.
          </p>
          <p>
            <strong>Single Borrower Limit:</strong> Exposure to a single borrower should not exceed{' '}
            {SINGLE_BORROWER_LIMIT_PCT}% of Tier-I capital (infrastructure carve-out 20%).
          </p>
          <p>
            <strong>Group Borrower Limit:</strong> Exposure to a single group of borrowers should
            not exceed {GROUP_BORROWER_LIMIT_PCT}% of Tier-I capital.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
