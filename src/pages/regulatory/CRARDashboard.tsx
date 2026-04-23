import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Shield,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Download,
  Info,
  Building2,
  Landmark,
  PieChart,
  FileText,
  Calendar,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import { Progress } from '@/components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
} from 'recharts';

interface CRARData {
  computation_date: string;
  tier1_capital: number;
  tier2_capital: number;
  total_capital: number;
  risk_weighted_assets: number;
  tier1_ratio: number;
  total_crar: number;
  tier1_minimum: number;
  total_minimum: number;
  tier1_status: 'COMPLIANT' | 'WARNING' | 'BREACH';
  total_status: 'COMPLIANT' | 'WARNING' | 'BREACH';
}

interface ExposureData {
  entity_name: string;
  entity_type: string;
  exposure_amount: number;
  tier1_capital: number;
  exposure_percent: number;
  single_borrower_limit: number;
  group_borrower_limit: number;
  status: 'WITHIN_LIMIT' | 'NEAR_LIMIT' | 'BREACHED';
}

interface InfrastructureData {
  total_loans: number;
  infrastructure_loans: number;
  infrastructure_ratio: number;
  required_ratio: number;
  status: 'COMPLIANT' | 'WARNING' | 'BREACH';
  sector_breakdown: Array<{
    sector: string;
    amount: number;
    percent: number;
  }>;
}

interface RegulatoryReturn {
  return_type: string;
  return_name: string;
  period: string;
  due_date: string;
  status: 'PENDING' | 'DRAFT' | 'SUBMITTED' | 'ACCEPTED' | 'OVERDUE';
  submission_date?: string;
}

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export default function CRARDashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [reportDate, setReportDate] = useState(new Date().toISOString().split('T')[0]);

  // Mock CRAR data
  const crarData: CRARData = {
    computation_date: reportDate,
    tier1_capital: 4500000000, // 450 Cr
    tier2_capital: 500000000, // 50 Cr
    total_capital: 5000000000, // 500 Cr
    risk_weighted_assets: 27000000000, // 2700 Cr
    tier1_ratio: 16.67,
    total_crar: 18.52,
    tier1_minimum: 10,
    total_minimum: 15,
    tier1_status: 'COMPLIANT',
    total_status: 'COMPLIANT',
  };

  // Capital components breakdown
  const capitalComponents = [
    { name: 'Paid-up Capital', amount: 1000000000, category: 'Tier-I' },
    { name: 'Reserves & Surplus', amount: 3200000000, category: 'Tier-I' },
    { name: 'Less: Intangible Assets', amount: -200000000, category: 'Tier-I' },
    { name: 'Other Tier-I Capital', amount: 500000000, category: 'Tier-I' },
    { name: 'Subordinated Debt', amount: 400000000, category: 'Tier-II' },
    { name: 'General Provisions', amount: 100000000, category: 'Tier-II' },
  ];

  // Risk Weighted Assets breakdown
  const rwaBreakdown = [
    { category: 'On-Balance Sheet', rwa: 22000000000, risk_weight: 'Various' },
    { category: 'Off-Balance Sheet', rwa: 3000000000, risk_weight: '100%' },
    { category: 'Market Risk', rwa: 1500000000, risk_weight: 'VaR' },
    { category: 'Operational Risk', rwa: 500000000, risk_weight: '15% of GI' },
  ];

  // Large Exposure data
  const largeExposures: ExposureData[] = [
    { entity_name: 'ABC Infrastructure Ltd', entity_type: 'Single Borrower', exposure_amount: 800000000, tier1_capital: 4500000000, exposure_percent: 17.78, single_borrower_limit: 25, group_borrower_limit: 0, status: 'WITHIN_LIMIT' },
    { entity_name: 'XYZ Group', entity_type: 'Group', exposure_amount: 1200000000, tier1_capital: 4500000000, exposure_percent: 26.67, single_borrower_limit: 0, group_borrower_limit: 40, status: 'WITHIN_LIMIT' },
    { entity_name: 'PQR Power Projects', entity_type: 'Single Borrower', exposure_amount: 1000000000, tier1_capital: 4500000000, exposure_percent: 22.22, single_borrower_limit: 25, group_borrower_limit: 0, status: 'NEAR_LIMIT' },
    { entity_name: 'LMN Holdings', entity_type: 'Group', exposure_amount: 1500000000, tier1_capital: 4500000000, exposure_percent: 33.33, single_borrower_limit: 0, group_borrower_limit: 40, status: 'WITHIN_LIMIT' },
  ];

  // Infrastructure lending data (for NBFC-IFC)
  const infrastructureData: InfrastructureData = {
    total_loans: 25000000000,
    infrastructure_loans: 19500000000,
    infrastructure_ratio: 78,
    required_ratio: 75,
    status: 'COMPLIANT',
    sector_breakdown: [
      { sector: 'Power Generation', amount: 6500000000, percent: 33.33 },
      { sector: 'Roads & Highways', amount: 5000000000, percent: 25.64 },
      { sector: 'Ports & Shipping', amount: 4000000000, percent: 20.51 },
      { sector: 'Industrial Infrastructure', amount: 2500000000, percent: 12.82 },
      { sector: 'Other Infrastructure', amount: 1500000000, percent: 7.69 },
    ],
  };

  // Regulatory returns calendar
  const regulatoryReturns: RegulatoryReturn[] = [
    { return_type: 'NBS-1', return_name: 'Prudential Norms Return', period: 'Q3 FY25', due_date: '2025-01-21', status: 'PENDING' },
    { return_type: 'NBS-2', return_name: 'Asset Classification Return', period: 'Q3 FY25', due_date: '2025-01-21', status: 'PENDING' },
    { return_type: 'ALM-1', return_name: 'Structural Liquidity', period: 'Dec 2024', due_date: '2025-01-15', status: 'SUBMITTED', submission_date: '2025-01-10' },
    { return_type: 'ALM-2', return_name: 'Interest Rate Sensitivity', period: 'Dec 2024', due_date: '2025-01-15', status: 'SUBMITTED', submission_date: '2025-01-10' },
    { return_type: 'CRILC', return_name: 'Large Credit Exposure', period: 'Dec 2024', due_date: '2025-01-07', status: 'ACCEPTED', submission_date: '2025-01-05' },
    { return_type: 'NBS-9', return_name: 'Branch Information', period: 'H1 FY25', due_date: '2024-10-31', status: 'ACCEPTED', submission_date: '2024-10-28' },
  ];

  // Historical CRAR trend
  const crarTrend = [
    { period: 'Mar-24', tier1: 15.5, total: 17.2, minimum: 15 },
    { period: 'Jun-24', tier1: 16.0, total: 17.8, minimum: 15 },
    { period: 'Sep-24', tier1: 16.3, total: 18.1, minimum: 15 },
    { period: 'Dec-24', tier1: 16.67, total: 18.52, minimum: 15 },
  ];

  const infraPieData = infrastructureData.sector_breakdown.map((s) => ({
    name: s.sector,
    value: s.amount,
  }));

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      COMPLIANT: 'bg-green-100 text-green-700',
      WARNING: 'bg-amber-100 text-amber-700',
      BREACH: 'bg-red-100 text-red-700',
      WITHIN_LIMIT: 'bg-green-100 text-green-700',
      NEAR_LIMIT: 'bg-amber-100 text-amber-700',
      BREACHED: 'bg-red-100 text-red-700',
      PENDING: 'bg-yellow-100 text-yellow-700',
      DRAFT: 'bg-gray-100 text-gray-700',
      SUBMITTED: 'bg-blue-100 text-blue-700',
      ACCEPTED: 'bg-green-100 text-green-700',
      OVERDUE: 'bg-red-100 text-red-700',
    };
    return colors[status] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Regulatory Dashboard"
        subtitle="CRAR, Exposure Limits & Regulatory Compliance"
        actions={
          <div className="flex gap-2">
            <Select value={reportDate} onValueChange={setReportDate}>
              <SelectTrigger className="w-[180px]">
                <Calendar className="mr-2 h-4 w-4" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="2025-01-31">31-Jan-2025</SelectItem>
                <SelectItem value="2024-12-31">31-Dec-2024</SelectItem>
                <SelectItem value="2024-09-30">30-Sep-2024</SelectItem>
                <SelectItem value="2024-06-30">30-Jun-2024</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export Report
            </Button>
          </div>
        }
      />

      {/* CRAR Summary Cards */}
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
                  <p>Minimum required: {crarData.tier1_minimum}%</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">
                <PercentageDisplay value={crarData.tier1_ratio} />
              </span>
              <Badge className={getStatusBadge(crarData.tier1_status)}>
                {crarData.tier1_status === 'COMPLIANT' ? (
                  <CheckCircle className="mr-1 h-3 w-3" />
                ) : (
                  <AlertTriangle className="mr-1 h-3 w-3" />
                )}
                {crarData.tier1_status}
              </Badge>
            </div>
            <Progress
              value={(crarData.tier1_ratio / 25) * 100}
              className="mt-2 h-2"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              Min: {crarData.tier1_minimum}% | Buffer: +{(crarData.tier1_ratio - crarData.tier1_minimum).toFixed(2)}%
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
                <PercentageDisplay value={crarData.total_crar} />
              </span>
              <Badge className={getStatusBadge(crarData.total_status)}>
                {crarData.total_status}
              </Badge>
            </div>
            <Progress
              value={(crarData.total_crar / 25) * 100}
              className="mt-2 h-2"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              Min: {crarData.total_minimum}% | Buffer: +{(crarData.total_crar - crarData.total_minimum).toFixed(2)}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Capital</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={crarData.total_capital}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Tier-I: <AmountDisplay amount={crarData.tier1_capital} abbreviated /> |
              Tier-II: <AmountDisplay amount={crarData.tier2_capital} abbreviated />
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Risk-Weighted Assets</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={crarData.risk_weighted_assets}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Capital / RWA determines CRAR
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Infrastructure Ratio (for NBFC-IFC) */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Infrastructure Lending Ratio</CardTitle>
            <CardDescription>
              NBFC-IFC requirement: Minimum 75% of total assets in infrastructure lending
            </CardDescription>
          </div>
          <Badge className={getStatusBadge(infrastructureData.status)}>
            {infrastructureData.status === 'COMPLIANT' ? (
              <CheckCircle className="mr-1 h-3 w-3" />
            ) : (
              <AlertTriangle className="mr-1 h-3 w-3" />
            )}
            {infrastructureData.status}
          </Badge>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Infrastructure Lending</span>
                <span className="text-2xl font-bold text-green-600">
                  <PercentageDisplay value={infrastructureData.infrastructure_ratio} />
                </span>
              </div>
              <Progress value={infrastructureData.infrastructure_ratio} className="h-3" />
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">
                  Min Required: {infrastructureData.required_ratio}%
                </span>
                <span className="text-muted-foreground">
                  Excess: +{(infrastructureData.infrastructure_ratio - infrastructureData.required_ratio).toFixed(1)}%
                </span>
              </div>
              <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                <div>
                  <p className="text-sm text-muted-foreground">Total Loans</p>
                  <AmountDisplay
                    amount={infrastructureData.total_loans}
                    abbreviated
                    className="text-lg font-bold"
                  />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Infrastructure Loans</p>
                  <AmountDisplay
                    amount={infrastructureData.infrastructure_loans}
                    abbreviated
                    className="text-lg font-bold text-green-600"
                  />
                </div>
              </div>
            </div>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <RechartsPieChart>
                  <Pie
                    data={infraPieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
                    label={({ name, percent }) =>
                      `${(name ?? '').split(' ')[0]} ${((percent ?? 0) * 100).toFixed(0)}%`
                    }
                    labelLine={false}
                  >
                    {infraPieData.map((_, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </RechartsPieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* CRAR Trend */}
        <Card>
          <CardHeader>
            <CardTitle>CRAR Trend</CardTitle>
            <CardDescription>Quarterly capital adequacy trend</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={crarTrend}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" />
                  <YAxis domain={[10, 25]} />
                  <RechartsTooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="tier1"
                    name="Tier-I CRAR"
                    stroke="#22c55e"
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="total"
                    name="Total CRAR"
                    stroke="#3b82f6"
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="minimum"
                    name="Minimum"
                    stroke="#ef4444"
                    strokeDasharray="5 5"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Capital Components */}
        <Card>
          <CardHeader>
            <CardTitle>Capital Composition</CardTitle>
            <CardDescription>Tier-I and Tier-II capital breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Component</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {capitalComponents.map((comp, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-medium">{comp.name}</TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={
                          comp.category === 'Tier-I'
                            ? 'bg-green-50 text-green-700'
                            : 'bg-blue-50 text-blue-700'
                        }
                      >
                        {comp.category}
                      </Badge>
                    </TableCell>
                    <TableCell
                      className={`text-right font-medium ${
                        comp.amount < 0 ? 'text-red-600' : ''
                      }`}
                    >
                      {comp.amount < 0 ? '(' : ''}
                      <AmountDisplay amount={Math.abs(comp.amount)} abbreviated />
                      {comp.amount < 0 ? ')' : ''}
                    </TableCell>
                  </TableRow>
                ))}
                <TableRow className="font-bold bg-muted/50">
                  <TableCell>Total Capital</TableCell>
                  <TableCell></TableCell>
                  <TableCell className="text-right">
                    <AmountDisplay amount={crarData.total_capital} abbreviated />
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {/* Large Exposure Table */}
      <Card>
        <CardHeader>
          <CardTitle>Large Exposure Report</CardTitle>
          <CardDescription>
            Single borrower limit: 25% of Tier-I capital | Group borrower limit: 40% of Tier-I capital
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Entity Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="text-right">Exposure</TableHead>
                <TableHead className="text-right">% of Tier-I</TableHead>
                <TableHead className="text-right">Limit (%)</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {largeExposures.map((exp, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">{exp.entity_name}</TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {exp.entity_type}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <AmountDisplay amount={exp.exposure_amount} abbreviated />
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    <PercentageDisplay value={exp.exposure_percent} />
                  </TableCell>
                  <TableCell className="text-right text-muted-foreground">
                    {exp.entity_type === 'Single Borrower'
                      ? `${exp.single_borrower_limit}%`
                      : `${exp.group_borrower_limit}%`}
                  </TableCell>
                  <TableCell>
                    <Badge className={getStatusBadge(exp.status)}>
                      {exp.status === 'WITHIN_LIMIT' && <CheckCircle className="mr-1 h-3 w-3" />}
                      {exp.status === 'NEAR_LIMIT' && <AlertTriangle className="mr-1 h-3 w-3" />}
                      {exp.status.replace('_', ' ')}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Regulatory Returns Calendar */}
      <Card>
        <CardHeader>
          <CardTitle>Regulatory Returns Calendar</CardTitle>
          <CardDescription>Status of RBI regulatory filings</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Return</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Period</TableHead>
                <TableHead>Due Date</TableHead>
                <TableHead>Submitted</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {regulatoryReturns.map((ret, index) => (
                <TableRow key={index}>
                  <TableCell className="font-mono font-medium">{ret.return_type}</TableCell>
                  <TableCell>{ret.return_name}</TableCell>
                  <TableCell>{ret.period}</TableCell>
                  <TableCell>
                    <DateDisplay date={ret.due_date} />
                  </TableCell>
                  <TableCell>
                    {ret.submission_date ? (
                      <DateDisplay date={ret.submission_date} />
                    ) : (
                      '-'
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge className={getStatusBadge(ret.status)}>
                      {ret.status === 'ACCEPTED' && <CheckCircle className="mr-1 h-3 w-3" />}
                      {ret.status === 'OVERDUE' && <AlertTriangle className="mr-1 h-3 w-3" />}
                      {ret.status}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* RWA Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Risk-Weighted Assets Breakdown</CardTitle>
          <CardDescription>Components of total risk-weighted assets</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-2">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Category</TableHead>
                  <TableHead className="text-right">RWA</TableHead>
                  <TableHead className="text-right">% of Total</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rwaBreakdown.map((rwa, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-medium">{rwa.category}</TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={rwa.rwa} abbreviated />
                    </TableCell>
                    <TableCell className="text-right text-muted-foreground">
                      <PercentageDisplay
                        value={(rwa.rwa / crarData.risk_weighted_assets) * 100}
                      />
                    </TableCell>
                  </TableRow>
                ))}
                <TableRow className="font-bold bg-muted/50">
                  <TableCell>Total RWA</TableCell>
                  <TableCell className="text-right">
                    <AmountDisplay amount={crarData.risk_weighted_assets} abbreviated />
                  </TableCell>
                  <TableCell className="text-right">100%</TableCell>
                </TableRow>
              </TableBody>
            </Table>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={rwaBreakdown}
                  layout="vertical"
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" tickFormatter={(v) => `${(v / 10000000).toFixed(0)} Cr`} />
                  <YAxis dataKey="category" type="category" width={120} />
                  <RechartsTooltip
                    formatter={(value: number | undefined) =>
                      new Intl.NumberFormat('en-IN', {
                        style: 'currency',
                        currency: 'INR',
                        notation: 'compact',
                      }).format(value ?? 0)
                    }
                  />
                  <Bar dataKey="rwa" name="RWA" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Compliance Notes */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-900 flex items-center gap-2">
            <Info className="h-5 w-5" />
            Regulatory Compliance Notes
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-blue-800 space-y-2">
          <p>
            <strong>CRAR Requirement:</strong> As per RBI Master Direction, NBFCs must maintain
            minimum CRAR of 15% (Tier-I ≥ 10%) by March 2027.
          </p>
          <p>
            <strong>Infrastructure Lending:</strong> NBFC-IFC must deploy at least 75% of total
            assets in infrastructure loans to maintain IFC classification.
          </p>
          <p>
            <strong>Single Borrower Limit:</strong> Exposure to single borrower should not exceed
            25% of Tier-I capital.
          </p>
          <p>
            <strong>Group Borrower Limit:</strong> Exposure to single group of borrowers should
            not exceed 40% of Tier-I capital.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
