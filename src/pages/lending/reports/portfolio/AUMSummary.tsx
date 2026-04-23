import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, TrendingUp, TrendingDown, Filter } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
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

// Mock data
const summaryData = {
  totalAUM: 50000000000, // 500 Cr
  lastMonthAUM: 47500000000, // 475 Cr
  ytdGrowth: 18.5,
  activeAccounts: 245,
  avgTicketSize: 204081632,
};

const monthlyTrend = [
  { month: 'Apr', aum: 420 },
  { month: 'May', aum: 435 },
  { month: 'Jun', aum: 448 },
  { month: 'Jul', aum: 455 },
  { month: 'Aug', aum: 462 },
  { month: 'Sep', aum: 470 },
  { month: 'Oct', aum: 478 },
  { month: 'Nov', aum: 485 },
  { month: 'Dec', aum: 492 },
  { month: 'Jan', aum: 500 },
];

const productWiseBreakdown = [
  { product: 'Term Loan - Corporate', aum: 15000000000, accounts: 45, share: 30, color: '#3b82f6' },
  { product: 'Term Loan - Project', aum: 10000000000, accounts: 25, share: 20, color: '#60a5fa' },
  { product: 'Working Capital', aum: 12000000000, accounts: 80, share: 24, color: '#10b981' },
  { product: 'LAP', aum: 8000000000, accounts: 60, share: 16, color: '#f59e0b' },
  { product: 'Project Finance', aum: 5000000000, accounts: 35, share: 10, color: '#8b5cf6' },
];

const branchWiseData = [
  { branch: 'Mumbai', aum: 20000000000, share: 40 },
  { branch: 'Delhi', aum: 12500000000, share: 25 },
  { branch: 'Chennai', aum: 7500000000, share: 15 },
  { branch: 'Kolkata', aum: 5000000000, share: 10 },
  { branch: 'Hyderabad', aum: 5000000000, share: 10 },
];

const classificationBreakdown = [
  { classification: 'Standard', aum: 48500000000, share: 97.0, color: '#22c55e' },
  { classification: 'SMA-0', aum: 300000000, share: 0.6, color: '#eab308' },
  { classification: 'SMA-1', aum: 200000000, share: 0.4, color: '#f59e0b' },
  { classification: 'SMA-2', aum: 150000000, share: 0.3, color: '#f97316' },
  { classification: 'NPA', aum: 850000000, share: 1.7, color: '#ef4444' },
];

export default function AUMSummary() {
  const navigate = useNavigate();
  const [period, setPeriod] = useState<'MTD' | 'QTD' | 'YTD'>('YTD');
  const [branchFilter, setBranchFilter] = useState('ALL');

  const aumChange = summaryData.totalAUM - summaryData.lastMonthAUM;
  const aumChangePercent = (aumChange / summaryData.lastMonthAUM) * 100;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/admin/lending/reports')}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-semibold">AUM Summary Report</h1>
            <p className="text-muted-foreground">
              Assets Under Management analysis and trends
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Tabs value={period} onValueChange={(v) => setPeriod(v as 'MTD' | 'QTD' | 'YTD')}>
            <TabsList>
              <TabsTrigger value="MTD">MTD</TabsTrigger>
              <TabsTrigger value="QTD">QTD</TabsTrigger>
              <TabsTrigger value="YTD">YTD</TabsTrigger>
            </TabsList>
          </Tabs>
          <Select value={branchFilter} onValueChange={setBranchFilter}>
            <SelectTrigger className="w-[150px]">
              <Filter className="mr-2 h-4 w-4" />
              <SelectValue placeholder="Branch" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All Branches</SelectItem>
              <SelectItem value="MUMBAI">Mumbai</SelectItem>
              <SelectItem value="DELHI">Delhi</SelectItem>
              <SelectItem value="CHENNAI">Chennai</SelectItem>
              <SelectItem value="KOLKATA">Kolkata</SelectItem>
              <SelectItem value="HYDERABAD">Hyderabad</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total AUM
            </CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={summaryData.totalAUM} abbreviated className="text-2xl font-bold" />
            <div className="flex items-center gap-1 text-sm mt-1">
              {aumChange >= 0 ? (
                <TrendingUp className="h-4 w-4 text-green-500" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500" />
              )}
              <span className={aumChange >= 0 ? 'text-green-600' : 'text-red-600'}>
                {aumChange >= 0 ? '+' : ''}
                <AmountDisplay amount={aumChange} abbreviated />
              </span>
              <span className="text-muted-foreground">vs last month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              YTD Growth
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              +<PercentageDisplay value={summaryData.ytdGrowth} />
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              Since April 2024
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Active Accounts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summaryData.activeAccounts}</div>
            <p className="text-sm text-muted-foreground mt-1">
              +12 new this month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Avg Ticket Size
            </CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={summaryData.avgTicketSize} abbreviated className="text-2xl font-bold" />
            <p className="text-sm text-muted-foreground mt-1">
              Per account
            </p>
          </CardContent>
        </Card>
      </div>

      {/* AUM Trend Chart */}
      <Card>
        <CardHeader>
          <CardTitle>AUM Trend</CardTitle>
          <CardDescription>Monthly AUM movement (in Cr)</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={monthlyTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(value: number | undefined) => [`₹ ${value ?? 0} Cr`, 'AUM']} />
                <Line
                  type="monotone"
                  dataKey="aum"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Product & Branch Distribution */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Product-wise Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Product-wise Breakdown</CardTitle>
            <CardDescription>AUM distribution by loan product</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={productWiseBreakdown}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="aum"
                    label={({ product, share }: any) => `${share}%`}
                  >
                    {productWiseBreakdown.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number | undefined) => [
                      `₹ ${((value ?? 0) / 10000000).toFixed(0)} Cr`,
                      'AUM',
                    ]}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Branch-wise Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Branch-wise Distribution</CardTitle>
            <CardDescription>AUM by branch location</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={branchWiseData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="branch" type="category" width={80} />
                  <Tooltip
                    formatter={(value: number | undefined) => [
                      `₹ ${((value ?? 0) / 10000000).toFixed(0)} Cr`,
                      'AUM',
                    ]}
                  />
                  <Bar dataKey="aum" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Asset Classification */}
      <Card>
        <CardHeader>
          <CardTitle>Asset Classification</CardTitle>
          <CardDescription>Portfolio quality breakdown</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Classification</TableHead>
                <TableHead className="text-right">AUM</TableHead>
                <TableHead className="text-right">Share (%)</TableHead>
                <TableHead className="text-right">Accounts</TableHead>
                <TableHead>Distribution</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {classificationBreakdown.map((item) => (
                <TableRow key={item.classification}>
                  <TableCell className="font-medium">{item.classification}</TableCell>
                  <TableCell className="text-right">
                    <AmountDisplay amount={item.aum} abbreviated />
                  </TableCell>
                  <TableCell className="text-right">
                    <PercentageDisplay value={item.share} />
                  </TableCell>
                  <TableCell className="text-right">
                    {Math.round(245 * (item.share / 100))}
                  </TableCell>
                  <TableCell>
                    <div className="w-full h-2 bg-muted rounded-full">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${item.share}%`,
                          backgroundColor: item.color,
                        }}
                      />
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Detailed Product Table */}
      <Card>
        <CardHeader>
          <CardTitle>Product-wise Details</CardTitle>
          <CardDescription>Detailed breakdown by loan product</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead>
                <TableHead className="text-right">AUM (Cr)</TableHead>
                <TableHead className="text-right">Accounts</TableHead>
                <TableHead className="text-right">Share (%)</TableHead>
                <TableHead className="text-right">Avg Ticket (Cr)</TableHead>
                <TableHead className="text-right">MoM Change</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {productWiseBreakdown.map((item) => (
                <TableRow key={item.product}>
                  <TableCell className="font-medium">{item.product}</TableCell>
                  <TableCell className="text-right">
                    <AmountDisplay amount={item.aum} abbreviated />
                  </TableCell>
                  <TableCell className="text-right">{item.accounts}</TableCell>
                  <TableCell className="text-right">
                    <PercentageDisplay value={item.share} />
                  </TableCell>
                  <TableCell className="text-right">
                    <AmountDisplay amount={item.aum / item.accounts} abbreviated />
                  </TableCell>
                  <TableCell className="text-right">
                    <span className="text-green-600">+2.5%</span>
                  </TableCell>
                </TableRow>
              ))}
              <TableRow className="font-bold bg-muted/50">
                <TableCell>Total</TableCell>
                <TableCell className="text-right">
                  <AmountDisplay amount={summaryData.totalAUM} abbreviated />
                </TableCell>
                <TableCell className="text-right">{summaryData.activeAccounts}</TableCell>
                <TableCell className="text-right">100%</TableCell>
                <TableCell className="text-right">
                  <AmountDisplay amount={summaryData.avgTicketSize} abbreviated />
                </TableCell>
                <TableCell className="text-right">
                  <span className="text-green-600">
                    +<PercentageDisplay value={aumChangePercent} />
                  </span>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
