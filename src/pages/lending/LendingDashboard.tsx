import {
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  FileText,
  Users,
  Landmark,
  ArrowRight,
  Calendar,
  Banknote,
  WalletCards,
  Scale,
} from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';

import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useLendingDashboard } from '@/hooks/lending/useLendingDashboard';
import type {
  PortfolioKPIs,
  TreasuryFundingSummary,
  SourceOfFundsSummary,
  MarginSummary,
  CollectionSummary,
  CashflowBucket,
  PendingApprovalItem,
  UpcomingMaturityItem,
} from '@/services/lending/dashboardApi';

const EMPTY_KPIS: PortfolioKPIs = {
  totalAum: '0',
  aumGrowthMom: '0',
  activeAccounts: 0,
  sanctionedPipeline: '0',
  pendingDisbursements: '0',
  collectionEfficiency: '0',
  overdueAmount: '0',
  grossNpa: '0',
  netNpa: '0',
  provisionCoverage: '0',
};

const EMPTY_TREASURY_FUNDING: TreasuryFundingSummary = {
  activeBorrowings: 0,
  sanctionedBorrowings: '0',
  drawnBorrowings: '0',
  availableBorrowings: '0',
  borrowingOutstanding: '0',
  weightedCostOfFunds: '0',
};

const EMPTY_SOURCE_OF_FUNDS: SourceOfFundsSummary = {
  mappedDeployments: 0,
  deployedAmount: '0',
  activeDrawnBorrowings: '0',
  unmappedDrawnBorrowings: '0',
  weightedCostRate: '0',
  weightedLendingRate: '0',
  weightedSpreadBps: '0',
};

const EMPTY_MARGIN_SUMMARY: MarginSummary = {
  lendingYield: '0',
  costOfFunds: '0',
  grossSpreadBps: '0',
  interestReceivable: '0',
  interestPayable: '0',
  netInterestPosition: '0',
};

const EMPTY_COLLECTION_SUMMARY: CollectionSummary = {
  dueThisMonth: '0',
  collectedThisMonth: '0',
  collectionEfficiency: '0',
  overdueAmount: '0',
  unallocatedReceipts: '0',
  unmatchedBankCreditCount: 0,
  unmatchedBankCreditAmount: '0',
  autoMatchCandidateCount: 0,
  matchReviewRequiredCount: 0,
};

export default function LendingDashboard() {
  const navigate = useNavigate();
  const [period, setPeriod] = useState<'MTD' | 'QTD' | 'YTD'>('MTD');
  const { data, isError, refetch } = useLendingDashboard();

  const portfolioKPIs = data?.portfolioKpis ?? EMPTY_KPIS;
  const lifecyclePipeline = data?.lifecyclePipeline ?? [];
  const treasuryFunding = data?.treasuryFunding ?? EMPTY_TREASURY_FUNDING;
  const sourceOfFunds = data?.sourceOfFunds ?? EMPTY_SOURCE_OF_FUNDS;
  const marginSummary = data?.marginSummary ?? EMPTY_MARGIN_SUMMARY;
  const collectionSummary = data?.collectionSummary ?? EMPTY_COLLECTION_SUMMARY;
  const cashflowBuckets: CashflowBucket[] = data?.cashflowBuckets ?? [];
  const monthlyDisbursements = data?.monthlyDisbursements ?? [];
  const portfolioByProduct = data?.portfolioByProduct ?? [];
  const assetClassification = data?.assetClassification ?? [];
  const pendingApprovals: PendingApprovalItem[] = data?.pendingApprovals ?? [];
  const upcomingMaturities: UpcomingMaturityItem[] = data?.upcomingMaturities ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Lending Dashboard"
        subtitle="Portfolio overview and key metrics"
        actions={
          <Tabs value={period} onValueChange={(v) => setPeriod(v as 'MTD' | 'QTD' | 'YTD')}>
            <TabsList>
              <TabsTrigger value="MTD">MTD</TabsTrigger>
              <TabsTrigger value="QTD">QTD</TabsTrigger>
              <TabsTrigger value="YTD">YTD</TabsTrigger>
            </TabsList>
          </Tabs>
        }
      />

      {isError && <ErrorState title="Could not load dashboard" onRetry={() => refetch()} />}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total AUM</CardTitle>
            <Landmark className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={portfolioKPIs.totalAum}
              abbreviated
              className="text-2xl font-bold"
            />
            {Number(portfolioKPIs.aumGrowthMom) === 0 ? (
              <p className="text-xs text-muted-foreground">No history yet</p>
            ) : (
              <div className="flex items-center text-xs text-muted-foreground">
                <TrendingUp className="mr-1 h-3 w-3 text-green-500" />
                <span className="text-green-500">+{portfolioKPIs.aumGrowthMom}%</span>
                <span className="ml-1">vs last month</span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Collection Efficiency</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div
              className={
                Number(portfolioKPIs.collectionEfficiency) === 0
                  ? 'text-2xl font-bold text-muted-foreground'
                  : 'text-2xl font-bold text-green-600'
              }
            >
              <PercentageDisplay value={portfolioKPIs.collectionEfficiency} />
            </div>
            <p className="text-xs text-muted-foreground">
              Target: 98% | Overdue:{' '}
              <AmountDisplay amount={portfolioKPIs.overdueAmount} abbreviated />
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Gross NPA</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div
              className={
                Number(portfolioKPIs.grossNpa) === 0
                  ? 'text-2xl font-bold text-muted-foreground'
                  : 'text-2xl font-bold text-amber-600'
              }
            >
              <PercentageDisplay value={portfolioKPIs.grossNpa} />
            </div>
            <p className="text-xs text-muted-foreground">
              Net NPA: <PercentageDisplay value={portfolioKPIs.netNpa} /> | PCR:{' '}
              <PercentageDisplay value={portfolioKPIs.provisionCoverage} />
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Accounts</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{portfolioKPIs.activeAccounts}</div>
            <p className="text-xs text-muted-foreground">
              Pipeline: <AmountDisplay amount={portfolioKPIs.sanctionedPipeline} abbreviated />
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Borrowing Outstanding</CardTitle>
            <Banknote className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={treasuryFunding.borrowingOutstanding}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-xs text-muted-foreground">
              Cost of funds: <PercentageDisplay value={treasuryFunding.weightedCostOfFunds} />
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Funding Deployment</CardTitle>
            <WalletCards className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={sourceOfFunds.deployedAmount}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-xs text-muted-foreground">
              Mapped deployments: {sourceOfFunds.mappedDeployments}
            </p>
            <p className="text-xs text-muted-foreground">
              Unmapped drawn:{' '}
              <AmountDisplay amount={sourceOfFunds.unmappedDrawnBorrowings} abbreviated />
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Gross Spread</CardTitle>
            <Scale className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{marginSummary.grossSpreadBps} bps</div>
            <p className="text-xs text-muted-foreground">
              Yield <PercentageDisplay value={marginSummary.lendingYield} /> | Cost{' '}
              <PercentageDisplay value={marginSummary.costOfFunds} />
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">MTD Collections</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={collectionSummary.collectedThisMonth}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-xs text-muted-foreground">
              Due: <AmountDisplay amount={collectionSummary.dueThisMonth} abbreviated />
            </p>
            <p className="text-xs text-muted-foreground">
              Unallocated receipts:{' '}
              <AmountDisplay amount={collectionSummary.unallocatedReceipts} abbreviated />
            </p>
            <Button
              variant="link"
              className="mt-1 h-auto p-0 text-xs"
              onClick={() => navigate('/admin/lending/collection-cockpit')}
            >
              Open collection cockpit
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Corporate Loan Lifecycle</CardTitle>
            <CardDescription>Pipeline, sanctioned, live and overdue exposure</CardDescription>
          </CardHeader>
          <CardContent>
            {lifecyclePipeline.length === 0 ? (
              <EmptyState
                title="No lifecycle exposure"
                subtitle="Pipeline and exposure stages appear when lending activity starts."
              />
            ) : (
              <div className="space-y-4">
                {lifecyclePipeline.map((stage) => (
                  <div
                    key={stage.stage}
                    className="flex items-center justify-between rounded-lg border p-3"
                  >
                    <div>
                      <p className="font-medium">{stage.stage}</p>
                      <p className="text-sm text-muted-foreground">{stage.count} records</p>
                    </div>
                    <AmountDisplay amount={stage.amount} abbreviated className="font-medium" />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Borrower Inflows vs Lender Outflows</CardTitle>
            <CardDescription>Expected cashflow buckets for liquidity monitoring</CardDescription>
          </CardHeader>
          <CardContent>
            {cashflowBuckets.length === 0 ? (
              <EmptyState
                title="No scheduled cashflows"
                subtitle="Future borrower inflows and borrowing repayments show here once schedules exist."
              />
            ) : (
              <div className="space-y-3">
                {cashflowBuckets.map((bucket) => (
                  <div
                    key={bucket.bucket}
                    className="grid grid-cols-4 items-center gap-3 rounded-lg border p-3 text-sm"
                  >
                    <div className="font-medium">{bucket.bucket}</div>
                    <div>
                      <p className="text-xs text-muted-foreground">Inflows</p>
                      <AmountDisplay amount={bucket.borrowerInflows} abbreviated size="sm" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Outflows</p>
                      <AmountDisplay amount={bucket.lenderOutflows} abbreviated size="sm" />
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-muted-foreground">Gap</p>
                      <AmountDisplay amount={bucket.netGap} abbreviated colorize size="sm" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Disbursement Trend</CardTitle>
            <CardDescription>Monthly disbursements (in Cr)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              {monthlyDisbursements.length === 0 ? (
                <EmptyState
                  title="No disbursements yet"
                  subtitle="Trend will appear after the first disbursement is recorded."
                />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={monthlyDisbursements.map((m) => ({
                      month: m.month,
                      amount: Number(m.amount),
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip
                      formatter={(value: number | undefined) => [`₹ ${value ?? 0} Cr`, 'Disbursed']}
                    />
                    <Bar dataKey="amount" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Portfolio by Product</CardTitle>
            <CardDescription>AUM distribution (in Cr)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              {portfolioByProduct.length === 0 ? (
                <EmptyState
                  title="No active loans"
                  subtitle="Distribution will appear once loan accounts are live."
                />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={portfolioByProduct.map((p) => ({
                        name: p.name,
                        value: Number(p.value),
                        color: p.color,
                      }))}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={2}
                      dataKey="value"
                      label={({ name, percent }) =>
                        `${name}: ${((percent ?? 0) * 100).toFixed(0)}%`
                      }
                    >
                      {portfolioByProduct.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value: number | undefined) => [`₹ ${value ?? 0} Cr`, 'AUM']}
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Asset Classification</CardTitle>
            <CardDescription>Portfolio quality breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            {assetClassification.length === 0 ? (
              <EmptyState
                title="No active loans"
                subtitle="Asset classification appears once loans are disbursed."
              />
            ) : (
              <div className="space-y-4">
                {assetClassification.map((item) => (
                  <div key={item.category} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>{item.category}</span>
                      <span className="font-medium">
                        ₹ {item.amount} Cr ({item.percentage}%)
                      </span>
                    </div>
                    <div className="h-2 rounded-full bg-muted">
                      <div
                        className={`h-full rounded-full ${item.color}`}
                        style={{ width: `${item.percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
            <div className="mt-4 border-t pt-4">
              <Button
                variant="outline"
                className="w-full"
                onClick={() => navigate('/admin/lending/reports/npa')}
              >
                View NPA Report
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Pending Approvals</CardTitle>
            <CardDescription>Items requiring your attention</CardDescription>
          </CardHeader>
          <CardContent>
            {pendingApprovals.length === 0 ? (
              <EmptyState
                title="Nothing pending approval"
                subtitle="New applications, disbursements and OTS proposals show here when they need a reviewer."
              />
            ) : (
              <div className="space-y-4">
                {pendingApprovals.map((item) => (
                  <div
                    key={item.id}
                    className="flex cursor-pointer items-center justify-between rounded-lg border p-3 hover:bg-muted/50"
                    onClick={() => {
                      if (item.type === 'Application') {
                        navigate(`/admin/lending/applications/${item.id}`);
                      } else if (item.type === 'Disbursement') {
                        navigate(`/admin/lending/disbursements/${item.id}`);
                      } else {
                        navigate(`/admin/lending/collections/ots/${item.id}`);
                      }
                    }}
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs">
                          {item.type}
                        </Badge>
                        <span className="font-mono text-sm">{item.reference}</span>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">{item.entity}</p>
                    </div>
                    <div className="text-right">
                      <AmountDisplay amount={item.amount} abbreviated className="font-medium" />
                      <div className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        Due: {item.dueDate}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <div className="mt-4 border-t pt-4">
              <Button
                variant="outline"
                className="w-full"
                onClick={() => navigate('/admin/lending/applications')}
              >
                View All Pending
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Upcoming Maturities</CardTitle>
            <CardDescription>Loans maturing in next 30 days</CardDescription>
          </CardHeader>
          <CardContent>
            {upcomingMaturities.length === 0 ? (
              <EmptyState
                title="No upcoming maturities"
                subtitle="Loan accounts maturing in the next 30 days show here."
              />
            ) : (
              <div className="space-y-4">
                {upcomingMaturities.map((item) => (
                  <div
                    key={item.id}
                    className="flex cursor-pointer items-center justify-between rounded-lg border p-3 hover:bg-muted/50"
                    onClick={() => navigate(`/admin/lending/accounts/${item.id}`)}
                  >
                    <div>
                      <p className="font-mono text-sm">{item.accountNumber}</p>
                      <p className="text-sm text-muted-foreground">{item.entity}</p>
                    </div>
                    <div className="text-right">
                      <AmountDisplay
                        amount={item.outstanding}
                        abbreviated
                        className="font-medium"
                      />
                      <div className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                        <Calendar className="h-3 w-3" />
                        <DateDisplay date={item.maturityDate} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common tasks and shortcuts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <Button
                variant="outline"
                className="flex h-auto flex-col items-center gap-2 py-4"
                onClick={() => navigate('/admin/lending/entities/new')}
              >
                <Users className="h-5 w-5" />
                <span>New Entity</span>
              </Button>
              <Button
                variant="outline"
                className="flex h-auto flex-col items-center gap-2 py-4"
                onClick={() => navigate('/admin/lending/applications/new')}
              >
                <FileText className="h-5 w-5" />
                <span>New Application</span>
              </Button>
              <Button
                variant="outline"
                className="flex h-auto flex-col items-center gap-2 py-4"
                onClick={() => navigate('/admin/lending/disbursements/new')}
              >
                <Landmark className="h-5 w-5" />
                <span>New Disbursement</span>
              </Button>
              <Button
                variant="outline"
                className="flex h-auto flex-col items-center gap-2 py-4"
                onClick={() => navigate('/admin/lending/receipts/new')}
              >
                <CheckCircle className="h-5 w-5" />
                <span>Record Receipt</span>
              </Button>
            </div>
            <div className="mt-4 space-y-2 border-t pt-4">
              <Button
                variant="default"
                className="w-full"
                onClick={() => navigate('/admin/lending/reports')}
              >
                <TrendingUp className="mr-2 h-4 w-4" />
                View Reports & Analytics
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
