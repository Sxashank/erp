import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2,
  Wallet,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Calendar,
  PieChart,
  BarChart3,
  RefreshCw,
  ArrowRight,
  Clock,
  CreditCard,
  Receipt,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
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
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { treasuryApi } from '@/services/lending/treasuryApi';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
} from 'recharts';

interface TreasurySummaryData {
  borrowing_summary: {
    total_sanctioned: number;
    total_drawn: number;
    total_available: number;
    total_outstanding: number;
    active_borrowings: number;
    lender_count: number;
    weighted_avg_rate: number | null;
    upcoming_repayments_30d: number;
    upcoming_maturities_90d: number;
  };
  alm_summary: {
    position_date: string;
    total_assets: number;
    total_liabilities: number;
    net_position: number;
    cumulative_gap_1_year: number;
    cumulative_gap_percent: number;
    gap_analysis: Array<{
      bucket: string;
      assets: number;
      liabilities: number;
      gap: number;
      cumulative_gap: number;
      gap_percent: number;
    }>;
  } | null;
  exposure_summary: {
    total_limits: number;
    within_limit: number;
    near_limit: number;
    breach_count: number;
    total_exposure: number;
    top_exposures: Array<{
      lender_name: string;
      exposure_percent: number;
      limit_percent: number;
      status: string;
    }>;
  };
}

interface UpcomingRepayment {
  borrowing_id: string;
  lender_name: string;
  facility_name: string;
  due_date: string;
  principal_due: number;
  interest_due: number;
  total_due: number;
}

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

const formatCurrency = (value: number) => {
  if (value >= 10000000) {
    return `₹${(value / 10000000).toFixed(2)} Cr`;
  }
  if (value >= 100000) {
    return `₹${(value / 100000).toFixed(2)} L`;
  }
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

export default function TreasuryDashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<TreasurySummaryData | null>(null);
  const [upcomingRepayments, setUpcomingRepayments] = useState<UpcomingRepayment[]>([]);
  const [borrowingPosition, setBorrowingPosition] = useState<{
    by_facility_type: Array<{
      facility_type: string;
      sanctioned: number;
      outstanding: number;
      rate: number;
    }>;
  } | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [summaryData, repaymentsData, positionData] = await Promise.all([
        treasuryApi.getBorrowingPosition().catch(() => null),
        treasuryApi.getUpcomingRepayments(30).catch(() => []),
        treasuryApi.getExposureSummary().catch(() => null),
      ]);

      // Construct summary from available data
      if (summaryData || positionData) {
        setSummary({
          borrowing_summary: {
            total_sanctioned: summaryData?.total_sanctioned || 0,
            total_drawn: summaryData?.total_drawn || 0,
            total_available: summaryData?.available_limit || 0,
            total_outstanding: summaryData?.total_outstanding || 0,
            active_borrowings: summaryData?.by_facility_type?.length || 0,
            lender_count: positionData?.by_lender?.length || 0,
            weighted_avg_rate: summaryData?.weighted_avg_rate || null,
            upcoming_repayments_30d: (repaymentsData as any[]).reduce((sum: number, r: any) => sum + (r.total_due || 0), 0),
            upcoming_maturities_90d: 0,
          },
          alm_summary: null,
          exposure_summary: {
            total_limits: positionData?.concentration_risk?.length || 0,
            within_limit: positionData?.concentration_risk?.filter((c: { status: string }) => c.status === 'WITHIN_LIMIT').length || 0,
            near_limit: positionData?.concentration_risk?.filter((c: { status: string }) => c.status === 'NEAR_LIMIT').length || 0,
            breach_count: positionData?.concentration_risk?.filter((c: { status: string }) => c.status === 'BREACHED').length || 0,
            total_exposure: positionData?.total_borrowings || 0,
            top_exposures: positionData?.concentration_risk || [],
          },
        });

        if (summaryData) {
          setBorrowingPosition({
            by_facility_type: summaryData.by_facility_type || [],
          });
        }
      }

      setUpcomingRepayments(repaymentsData || []);
    } catch (error) {
      console.error('Failed to fetch treasury data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Mock data for demonstration when API returns empty
  const mockSummary: TreasurySummaryData = {
    borrowing_summary: {
      total_sanctioned: 3800000000,
      total_drawn: 1850000000,
      total_available: 1950000000,
      total_outstanding: 1850000000,
      active_borrowings: 4,
      lender_count: 4,
      weighted_avg_rate: 9.25,
      upcoming_repayments_30d: 104687500,
      upcoming_maturities_90d: 1,
    },
    alm_summary: {
      position_date: new Date().toISOString().split('T')[0],
      total_assets: 85200000000,
      total_liabilities: 64800000000,
      net_position: 20400000000,
      cumulative_gap_1_year: 5400000000,
      cumulative_gap_percent: 6.34,
      gap_analysis: [
        { bucket: 'Day 1', assets: 2500000000, liabilities: 1800000000, gap: 700000000, cumulative_gap: 700000000, gap_percent: 2.8 },
        { bucket: '2-7 Days', assets: 1500000000, liabilities: 2000000000, gap: -500000000, cumulative_gap: 200000000, gap_percent: -3.3 },
        { bucket: '8-14 Days', assets: 1200000000, liabilities: 1000000000, gap: 200000000, cumulative_gap: 400000000, gap_percent: 1.7 },
        { bucket: '15-28 Days', assets: 2000000000, liabilities: 1500000000, gap: 500000000, cumulative_gap: 900000000, gap_percent: 2.5 },
      ],
    },
    exposure_summary: {
      total_limits: 6,
      within_limit: 4,
      near_limit: 1,
      breach_count: 1,
      total_exposure: 1850000000,
      top_exposures: [
        { lender_name: 'HDFC Bank Ltd', exposure_percent: 45.9, limit_percent: 50, status: 'NEAR_LIMIT' },
        { lender_name: 'SIDBI', exposure_percent: 18.9, limit_percent: 30, status: 'WITHIN_LIMIT' },
        { lender_name: 'NCD Series 2024', exposure_percent: 16.2, limit_percent: 25, status: 'WITHIN_LIMIT' },
        { lender_name: 'ICICI Bank Ltd', exposure_percent: 22.7, limit_percent: 20, status: 'BREACHED' },
      ],
    },
  };

  const mockBorrowingPosition = {
    by_facility_type: [
      { facility_type: 'TERM_LOAN', sanctioned: 1350000000, outstanding: 1130000000, rate: 9.0 },
      { facility_type: 'NCD', sanctioned: 300000000, outstanding: 300000000, rate: 10.5 },
      { facility_type: 'CASH_CREDIT', sanctioned: 500000000, outstanding: 420000000, rate: 9.5 },
      { facility_type: 'REFINANCE', sanctioned: 350000000, outstanding: 280000000, rate: 8.75 },
    ],
  };

  const mockUpcomingRepayments: UpcomingRepayment[] = [
    { borrowing_id: '1', lender_name: 'HDFC Bank Ltd', facility_name: 'Term Loan', due_date: '2025-02-15', principal_due: 50000000, interest_due: 6562500, total_due: 56562500 },
    { borrowing_id: '2', lender_name: 'SIDBI', facility_name: 'Refinance', due_date: '2025-03-01', principal_due: 35000000, interest_due: 2041667, total_due: 37041667 },
    { borrowing_id: '4', lender_name: 'ICICI Bank Ltd', facility_name: 'Cash Credit', due_date: '2025-02-28', principal_due: 0, interest_due: 3312500, total_due: 3312500 },
  ];

  // Use actual data if available, otherwise use mock
  const displaySummary = summary || mockSummary;
  const displayPosition = borrowingPosition || mockBorrowingPosition;
  const displayRepayments = upcomingRepayments.length > 0 ? upcomingRepayments : mockUpcomingRepayments;

  const facilityPieData = displayPosition.by_facility_type.map((f) => ({
    name: f.facility_type.replace('_', ' '),
    value: f.outstanding,
  }));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Treasury Dashboard"
        subtitle="Borrowings, ALM & Liquidity Management"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={fetchData} disabled={loading}>
              <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button onClick={() => navigate('/admin/lending/treasury/borrowings/new')}>
              <Wallet className="mr-2 h-4 w-4" />
              New Borrowing
            </Button>
          </div>
        }
      />

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sanctioned</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <>
                <AmountDisplay
                  amount={displaySummary.borrowing_summary.total_sanctioned}
                  abbreviated
                  className="text-2xl font-bold"
                />
                <p className="text-xs text-muted-foreground">
                  {displaySummary.borrowing_summary.active_borrowings} active facilities
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Outstanding</CardTitle>
            <TrendingDown className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <>
                <AmountDisplay
                  amount={displaySummary.borrowing_summary.total_outstanding}
                  abbreviated
                  className="text-2xl font-bold text-amber-600"
                />
                <div className="flex items-center gap-2 mt-1">
                  <Progress
                    value={
                      (displaySummary.borrowing_summary.total_outstanding /
                        displaySummary.borrowing_summary.total_sanctioned) *
                      100
                    }
                    className="h-2"
                  />
                  <span className="text-xs text-muted-foreground">
                    <PercentageDisplay
                      value={
                        (displaySummary.borrowing_summary.total_outstanding /
                          displaySummary.borrowing_summary.total_sanctioned) *
                        100
                      }
                    />
                  </span>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Weighted Avg Rate</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <>
                <div className="text-2xl font-bold">
                  <PercentageDisplay
                    value={displaySummary.borrowing_summary.weighted_avg_rate || 0}
                  />{' '}
                  p.a.
                </div>
                <p className="text-xs text-muted-foreground">Cost of borrowing</p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Available Limit</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <>
                <AmountDisplay
                  amount={displaySummary.borrowing_summary.total_available}
                  abbreviated
                  className="text-2xl font-bold text-green-600"
                />
                <p className="text-xs text-muted-foreground">Undrawn facilities</p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Borrowing by Facility Type */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Borrowing Mix</CardTitle>
              <CardDescription>Outstanding by facility type</CardDescription>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/admin/lending/treasury/borrowings')}
            >
              View All <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <RechartsPieChart>
                  <Pie
                    data={facilityPieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="value"
                    label={({ name, percent }) =>
                      `${name} ${((percent ?? 0) * 100).toFixed(0)}%`
                    }
                    labelLine={false}
                  >
                    {facilityPieData.map((_, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number | undefined) => formatCurrency(value ?? 0)}
                  />
                </RechartsPieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-2">
              {displayPosition.by_facility_type.map((f, index) => (
                <div
                  key={f.facility_type}
                  className="flex items-center gap-2 text-sm"
                >
                  <div
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  />
                  <span className="truncate">{f.facility_type.replace('_', ' ')}</span>
                  <span className="ml-auto font-medium">
                    <PercentageDisplay value={f.rate} />
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Upcoming Repayments */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Upcoming Repayments</CardTitle>
              <CardDescription>Next 30 days</CardDescription>
            </div>
            <Badge variant="outline" className="bg-red-50 text-red-700">
              <Clock className="mr-1 h-3 w-3" />
              <AmountDisplay
                amount={displayRepayments.reduce((sum, r) => sum + r.total_due, 0)}
                abbreviated
              />
            </Badge>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Lender</TableHead>
                  <TableHead>Due Date</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {displayRepayments.slice(0, 5).map((repayment) => (
                  <TableRow
                    key={repayment.borrowing_id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() =>
                      navigate(
                        `/admin/lending/treasury/borrowings/${repayment.borrowing_id}`
                      )
                    }
                  >
                    <TableCell>
                      <div className="font-medium">{repayment.lender_name}</div>
                      <div className="text-xs text-muted-foreground">
                        {repayment.facility_name}
                      </div>
                    </TableCell>
                    <TableCell>
                      <DateDisplay date={repayment.due_date} />
                    </TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={repayment.total_due} abbreviated />
                      <div className="text-xs text-muted-foreground">
                        P: <AmountDisplay amount={repayment.principal_due} abbreviated /> |
                        I: <AmountDisplay amount={repayment.interest_due} abbreviated />
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
                {displayRepayments.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={3} className="text-center py-4 text-muted-foreground">
                      No upcoming repayments
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {/* ALM & Exposure Summary */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* ALM Summary */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>ALM Position</CardTitle>
              <CardDescription>
                As of{' '}
                {displaySummary.alm_summary ? (
                  <DateDisplay date={displaySummary.alm_summary.position_date} />
                ) : (
                  'N/A'
                )}
              </CardDescription>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/admin/lending/treasury/alm')}
            >
              View Details <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent>
            {displaySummary.alm_summary ? (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div className="p-3 border rounded-lg">
                    <p className="text-xs text-muted-foreground">Total Assets</p>
                    <AmountDisplay
                      amount={displaySummary.alm_summary.total_assets}
                      abbreviated
                      className="text-lg font-bold"
                    />
                  </div>
                  <div className="p-3 border rounded-lg">
                    <p className="text-xs text-muted-foreground">Total Liabilities</p>
                    <AmountDisplay
                      amount={displaySummary.alm_summary.total_liabilities}
                      abbreviated
                      className="text-lg font-bold"
                    />
                  </div>
                  <div className="p-3 border rounded-lg">
                    <p className="text-xs text-muted-foreground">Net Position</p>
                    <AmountDisplay
                      amount={displaySummary.alm_summary.net_position}
                      abbreviated
                      className={`text-lg font-bold ${
                        displaySummary.alm_summary.net_position >= 0
                          ? 'text-green-600'
                          : 'text-red-600'
                      }`}
                    />
                  </div>
                </div>
                <div className="h-[200px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={displaySummary.alm_summary.gap_analysis.slice(0, 4)}
                      layout="vertical"
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" tick={{ fontSize: 10 }} />
                      <YAxis dataKey="bucket" type="category" tick={{ fontSize: 10 }} width={80} />
                      <Tooltip formatter={(value: number | undefined) => formatCurrency(value ?? 0)} />
                      <Bar dataKey="gap" name="Gap" fill="#3b82f6" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-[300px] text-muted-foreground">
                <PieChart className="h-12 w-12 mb-2 opacity-50" />
                <p>No ALM position generated</p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-2"
                  onClick={() => navigate('/admin/lending/treasury/alm')}
                >
                  Generate Now
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Exposure Summary */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Exposure Concentration</CardTitle>
              <CardDescription>Top lender exposures</CardDescription>
            </div>
            {displaySummary.exposure_summary.breach_count > 0 && (
              <Badge variant="destructive">
                <AlertTriangle className="mr-1 h-3 w-3" />
                {displaySummary.exposure_summary.breach_count} Breach
              </Badge>
            )}
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {displaySummary.exposure_summary.top_exposures.slice(0, 4).map((exp, index) => (
                <div key={index} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium truncate max-w-[200px]">
                      {exp.lender_name}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground">
                        <PercentageDisplay value={exp.exposure_percent} /> / {exp.limit_percent}%
                      </span>
                      <Badge
                        variant="outline"
                        className={
                          exp.status === 'WITHIN_LIMIT'
                            ? 'bg-green-50 text-green-700'
                            : exp.status === 'NEAR_LIMIT'
                            ? 'bg-amber-50 text-amber-700'
                            : 'bg-red-50 text-red-700'
                        }
                      >
                        {exp.status.replace('_', ' ')}
                      </Badge>
                    </div>
                  </div>
                  <Progress
                    value={(exp.exposure_percent / exp.limit_percent) * 100}
                    className={`h-2 ${
                      exp.status === 'BREACHED' ? '[&>div]:bg-red-500' : ''
                    }`}
                  />
                </div>
              ))}
              {displaySummary.exposure_summary.top_exposures.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  No exposure limits configured
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <Button
              variant="outline"
              className="h-auto py-4 flex-col"
              onClick={() => navigate('/admin/lending/treasury/lenders')}
            >
              <Building2 className="h-6 w-6 mb-2" />
              <span>Manage Lenders</span>
              <span className="text-xs text-muted-foreground">
                {displaySummary.borrowing_summary.lender_count} active
              </span>
            </Button>
            <Button
              variant="outline"
              className="h-auto py-4 flex-col"
              onClick={() => navigate('/admin/lending/treasury/borrowings')}
            >
              <Wallet className="h-6 w-6 mb-2" />
              <span>All Borrowings</span>
              <span className="text-xs text-muted-foreground">
                {displaySummary.borrowing_summary.active_borrowings} facilities
              </span>
            </Button>
            <Button
              variant="outline"
              className="h-auto py-4 flex-col"
              onClick={() => navigate('/admin/lending/treasury/alm')}
            >
              <BarChart3 className="h-6 w-6 mb-2" />
              <span>ALM Reports</span>
              <span className="text-xs text-muted-foreground">Gap Analysis</span>
            </Button>
            <Button
              variant="outline"
              className="h-auto py-4 flex-col"
              onClick={() => navigate('/admin/regulatory/crar')}
            >
              <Receipt className="h-6 w-6 mb-2" />
              <span>Regulatory</span>
              <span className="text-xs text-muted-foreground">CRAR & Returns</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
