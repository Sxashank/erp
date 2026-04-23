import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Clock,
  FileText,
  Users,
  Landmark,
  ArrowRight,
  Calendar,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';

// Mock data for dashboard
const portfolioKPIs = {
  totalAUM: 50000000000, // 500 Cr
  aumGrowthMoM: 5.2,
  activeAccounts: 245,
  sanctionedPipeline: 8500000000, // 85 Cr
  pendingDisbursements: 3200000000, // 32 Cr
  collectionEfficiency: 98.5,
  overdueAmount: 850000000, // 8.5 Cr
  grossNPA: 3.2,
  netNPA: 1.8,
  provisionCoverage: 72,
};

const monthlyDisbursements = [
  { month: 'Oct', amount: 350 },
  { month: 'Nov', amount: 420 },
  { month: 'Dec', amount: 380 },
  { month: 'Jan', amount: 450 },
  { month: 'Feb', amount: 520 },
  { month: 'Mar', amount: 480 },
];

const portfolioByProduct = [
  { name: 'Term Loan', value: 25000, color: '#3b82f6' },
  { name: 'Working Capital', value: 12000, color: '#10b981' },
  { name: 'LAP', value: 8000, color: '#f59e0b' },
  { name: 'Project Finance', value: 5000, color: '#8b5cf6' },
];

const assetClassification = [
  { category: 'Standard', amount: 48500, percentage: 97.0, color: 'bg-green-500' },
  { category: 'SMA-0', amount: 300, percentage: 0.6, color: 'bg-yellow-400' },
  { category: 'SMA-1', amount: 200, percentage: 0.4, color: 'bg-yellow-500' },
  { category: 'SMA-2', amount: 150, percentage: 0.3, color: 'bg-orange-500' },
  { category: 'NPA', amount: 850, percentage: 1.7, color: 'bg-red-500' },
];

const pendingApprovals = [
  {
    id: '1',
    type: 'Application',
    reference: 'APP/2025/00145',
    entity: 'Sunrise Industries',
    amount: 150000000,
    stage: 'Credit Review',
    dueDate: '2025-01-14',
  },
  {
    id: '2',
    type: 'Disbursement',
    reference: 'DISB/2025/00078',
    entity: 'Metro Logistics',
    amount: 50000000,
    stage: 'Operations',
    dueDate: '2025-01-13',
  },
  {
    id: '3',
    type: 'OTS',
    reference: 'OTS/2025/00012',
    entity: 'Eastern Trading',
    amount: 35000000,
    stage: 'Management',
    dueDate: '2025-01-15',
  },
];

const upcomingMaturities = [
  {
    id: '1',
    accountNumber: 'SMFC/TL/2020/L00045',
    entity: 'Global Exports Ltd',
    maturityDate: '2025-01-20',
    outstanding: 125000000,
  },
  {
    id: '2',
    accountNumber: 'SMFC/WC/2021/L00089',
    entity: 'Prime Distributors',
    maturityDate: '2025-01-25',
    outstanding: 75000000,
  },
  {
    id: '3',
    accountNumber: 'SMFC/LAP/2022/L00123',
    entity: 'Tech Solutions',
    maturityDate: '2025-02-01',
    outstanding: 45000000,
  },
];

export default function LendingDashboard() {
  const navigate = useNavigate();
  const [period, setPeriod] = useState<'MTD' | 'QTD' | 'YTD'>('MTD');

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

      {/* Key Metrics Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total AUM</CardTitle>
            <Landmark className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={portfolioKPIs.totalAUM}
              abbreviated
              className="text-2xl font-bold"
            />
            <div className="flex items-center text-xs text-muted-foreground">
              <TrendingUp className="mr-1 h-3 w-3 text-green-500" />
              <span className="text-green-500">+{portfolioKPIs.aumGrowthMoM}%</span>
              <span className="ml-1">vs last month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Collection Efficiency</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
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
            <div className="text-2xl font-bold text-amber-600">
              <PercentageDisplay value={portfolioKPIs.grossNPA} />
            </div>
            <p className="text-xs text-muted-foreground">
              Net NPA: <PercentageDisplay value={portfolioKPIs.netNPA} /> | PCR:{' '}
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
              Pipeline:{' '}
              <AmountDisplay amount={portfolioKPIs.sanctionedPipeline} abbreviated />
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Disbursement Trend */}
        <Card>
          <CardHeader>
            <CardTitle>Disbursement Trend</CardTitle>
            <CardDescription>Monthly disbursements (in Cr)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={monthlyDisbursements}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip
                    formatter={(value: number | undefined) => [`₹ ${value ?? 0} Cr`, 'Disbursed']}
                  />
                  <Bar dataKey="amount" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Portfolio by Product */}
        <Card>
          <CardHeader>
            <CardTitle>Portfolio by Product</CardTitle>
            <CardDescription>AUM distribution (in Cr)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={portfolioByProduct}
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
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Asset Classification & Pending Approvals */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Asset Classification */}
        <Card>
          <CardHeader>
            <CardTitle>Asset Classification</CardTitle>
            <CardDescription>Portfolio quality breakdown</CardDescription>
          </CardHeader>
          <CardContent>
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
            <div className="mt-4 pt-4 border-t">
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

        {/* Pending Approvals */}
        <Card>
          <CardHeader>
            <CardTitle>Pending Approvals</CardTitle>
            <CardDescription>Items requiring your attention</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {pendingApprovals.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 cursor-pointer"
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
                    <p className="text-sm text-muted-foreground mt-1">
                      {item.entity}
                    </p>
                  </div>
                  <div className="text-right">
                    <AmountDisplay
                      amount={item.amount}
                      abbreviated
                      className="font-medium"
                    />
                    <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                      <Clock className="h-3 w-3" />
                      Due: {item.dueDate}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 pt-4 border-t">
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

      {/* Upcoming Maturities & Quick Actions */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Upcoming Maturities */}
        <Card>
          <CardHeader>
            <CardTitle>Upcoming Maturities</CardTitle>
            <CardDescription>Loans maturing in next 30 days</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {upcomingMaturities.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 cursor-pointer"
                  onClick={() =>
                    navigate(`/admin/lending/accounts/${item.id}`)
                  }
                >
                  <div>
                    <p className="font-mono text-sm">{item.accountNumber}</p>
                    <p className="text-sm text-muted-foreground">
                      {item.entity}
                    </p>
                  </div>
                  <div className="text-right">
                    <AmountDisplay
                      amount={item.outstanding}
                      abbreviated
                      className="font-medium"
                    />
                    <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                      <Calendar className="h-3 w-3" />
                      <DateDisplay date={item.maturityDate} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common tasks and shortcuts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <Button
                variant="outline"
                className="h-auto py-4 flex flex-col items-center gap-2"
                onClick={() => navigate('/admin/lending/entities/new')}
              >
                <Users className="h-5 w-5" />
                <span>New Entity</span>
              </Button>
              <Button
                variant="outline"
                className="h-auto py-4 flex flex-col items-center gap-2"
                onClick={() => navigate('/admin/lending/applications/new')}
              >
                <FileText className="h-5 w-5" />
                <span>New Application</span>
              </Button>
              <Button
                variant="outline"
                className="h-auto py-4 flex flex-col items-center gap-2"
                onClick={() => navigate('/admin/lending/disbursements/new')}
              >
                <Landmark className="h-5 w-5" />
                <span>New Disbursement</span>
              </Button>
              <Button
                variant="outline"
                className="h-auto py-4 flex flex-col items-center gap-2"
                onClick={() => navigate('/admin/lending/receipts/new')}
              >
                <CheckCircle className="h-5 w-5" />
                <span>Record Receipt</span>
              </Button>
            </div>
            <div className="mt-4 pt-4 border-t space-y-2">
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
