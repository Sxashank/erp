import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, Filter, TrendingUp, TrendingDown } from 'lucide-react';
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
  Legend,
} from 'recharts';

// Mock data
const summaryMetrics = {
  totalDemand: 2500000000, // 250 Cr
  totalCollection: 2462500000, // 246.25 Cr
  efficiency: 98.5,
  lastMonthEfficiency: 97.8,
  overdueAmount: 850000000, // 85 Cr
  advanceReceived: 125000000, // 12.5 Cr
};

const monthlyTrend = [
  { month: 'Oct', demand: 240, collection: 235, efficiency: 97.9 },
  { month: 'Nov', demand: 242, collection: 238, efficiency: 98.3 },
  { month: 'Dec', demand: 245, collection: 240, efficiency: 98.0 },
  { month: 'Jan', demand: 250, collection: 246.25, efficiency: 98.5 },
];

const branchWiseCollection = [
  { branch: 'Mumbai', demand: 100, collection: 99, efficiency: 99.0 },
  { branch: 'Delhi', demand: 62.5, collection: 61, efficiency: 97.6 },
  { branch: 'Chennai', demand: 37.5, collection: 37, efficiency: 98.7 },
  { branch: 'Kolkata', demand: 25, collection: 24.5, efficiency: 98.0 },
  { branch: 'Hyderabad', demand: 25, collection: 24.75, efficiency: 99.0 },
];

const productWiseCollection = [
  { product: 'Term Loan', demand: 125, collection: 123.5, efficiency: 98.8 },
  { product: 'Working Capital', demand: 60, collection: 59, efficiency: 98.3 },
  { product: 'LAP', demand: 40, collection: 39.5, efficiency: 98.75 },
  { product: 'Project Finance', demand: 25, collection: 24.25, efficiency: 97.0 },
];

const ageingBuckets = [
  { bucket: 'Current', amount: 2462500000, percentage: 98.5, color: 'bg-green-500' },
  { bucket: '1-30 Days', amount: 15000000, percentage: 0.6, color: 'bg-yellow-500' },
  { bucket: '31-60 Days', amount: 10000000, percentage: 0.4, color: 'bg-orange-500' },
  { bucket: '61-90 Days', amount: 7500000, percentage: 0.3, color: 'bg-red-400' },
  { bucket: '>90 Days', amount: 5000000, percentage: 0.2, color: 'bg-red-600' },
];

const dailyCollection = [
  { date: '01 Jan', amount: 8.2 },
  { date: '02 Jan', amount: 12.5 },
  { date: '03 Jan', amount: 9.8 },
  { date: '04 Jan', amount: 15.3 },
  { date: '05 Jan', amount: 11.2 },
  { date: '06 Jan', amount: 7.5 },
  { date: '07 Jan', amount: 6.8 },
  { date: '08 Jan', amount: 10.2 },
  { date: '09 Jan', amount: 14.5 },
  { date: '10 Jan', amount: 12.8 },
];

export default function CollectionEfficiency() {
  const navigate = useNavigate();
  const [period, setPeriod] = useState<'MTD' | 'QTD' | 'YTD'>('MTD');
  const [branchFilter, setBranchFilter] = useState('ALL');

  const efficiencyChange = summaryMetrics.efficiency - summaryMetrics.lastMonthEfficiency;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/admin/lending/reports')}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-semibold">Collection Efficiency Report</h1>
            <p className="text-muted-foreground">
              Demand vs collection analysis and recovery metrics
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
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Demand
            </CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={summaryMetrics.totalDemand}
              abbreviated
              className="text-2xl font-bold"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Collection
            </CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={summaryMetrics.totalCollection}
              abbreviated
              className="text-2xl font-bold text-green-600"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Collection Efficiency
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              <PercentageDisplay value={summaryMetrics.efficiency} />
            </div>
            <div className="flex items-center gap-1 text-sm mt-1">
              {efficiencyChange >= 0 ? (
                <TrendingUp className="h-4 w-4 text-green-500" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500" />
              )}
              <span className={efficiencyChange >= 0 ? 'text-green-600' : 'text-red-600'}>
                {efficiencyChange >= 0 ? '+' : ''}
                <PercentageDisplay value={efficiencyChange} />
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Overdue Amount
            </CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={summaryMetrics.overdueAmount}
              abbreviated
              className="text-2xl font-bold text-red-600"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Advance Received
            </CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={summaryMetrics.advanceReceived}
              abbreviated
              className="text-2xl font-bold text-blue-600"
            />
          </CardContent>
        </Card>
      </div>

      {/* Monthly Trend */}
      <Card>
        <CardHeader>
          <CardTitle>Demand vs Collection Trend</CardTitle>
          <CardDescription>Monthly comparison (in Cr)</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" domain={[90, 100]} />
                <Tooltip />
                <Legend />
                <Bar yAxisId="left" dataKey="demand" fill="#94a3b8" name="Demand (Cr)" />
                <Bar yAxisId="left" dataKey="collection" fill="#22c55e" name="Collection (Cr)" />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="efficiency"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="Efficiency %"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Daily Collection Trend */}
      <Card>
        <CardHeader>
          <CardTitle>Daily Collection (Current Month)</CardTitle>
          <CardDescription>Day-wise collection pattern (in Cr)</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dailyCollection}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value: number | undefined) => [`₹ ${value ?? 0} Cr`, 'Collection']} />
                <Bar dataKey="amount" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Branch-wise & Product-wise */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Branch-wise Collection */}
        <Card>
          <CardHeader>
            <CardTitle>Branch-wise Collection</CardTitle>
            <CardDescription>Performance by branch</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Branch</TableHead>
                  <TableHead className="text-right">Demand</TableHead>
                  <TableHead className="text-right">Collection</TableHead>
                  <TableHead className="text-right">Efficiency</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {branchWiseCollection.map((item) => (
                  <TableRow key={item.branch}>
                    <TableCell className="font-medium">{item.branch}</TableCell>
                    <TableCell className="text-right">₹ {item.demand} Cr</TableCell>
                    <TableCell className="text-right">₹ {item.collection} Cr</TableCell>
                    <TableCell className="text-right">
                      <span
                        className={
                          item.efficiency >= 98
                            ? 'text-green-600'
                            : item.efficiency >= 95
                            ? 'text-yellow-600'
                            : 'text-red-600'
                        }
                      >
                        <PercentageDisplay value={item.efficiency} />
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Product-wise Collection */}
        <Card>
          <CardHeader>
            <CardTitle>Product-wise Collection</CardTitle>
            <CardDescription>Performance by loan product</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Product</TableHead>
                  <TableHead className="text-right">Demand</TableHead>
                  <TableHead className="text-right">Collection</TableHead>
                  <TableHead className="text-right">Efficiency</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {productWiseCollection.map((item) => (
                  <TableRow key={item.product}>
                    <TableCell className="font-medium">{item.product}</TableCell>
                    <TableCell className="text-right">₹ {item.demand} Cr</TableCell>
                    <TableCell className="text-right">₹ {item.collection} Cr</TableCell>
                    <TableCell className="text-right">
                      <span
                        className={
                          item.efficiency >= 98
                            ? 'text-green-600'
                            : item.efficiency >= 95
                            ? 'text-yellow-600'
                            : 'text-red-600'
                        }
                      >
                        <PercentageDisplay value={item.efficiency} />
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {/* Overdue Ageing */}
      <Card>
        <CardHeader>
          <CardTitle>Overdue Ageing Analysis</CardTitle>
          <CardDescription>Distribution by ageing bucket</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {ageingBuckets.map((bucket) => (
              <div key={bucket.bucket} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">{bucket.bucket}</span>
                  <span>
                    <AmountDisplay amount={bucket.amount} abbreviated /> (
                    <PercentageDisplay value={bucket.percentage} />)
                  </span>
                </div>
                <div className="h-3 rounded-full bg-muted">
                  <div
                    className={`h-full rounded-full ${bucket.color}`}
                    style={{ width: `${Math.max(bucket.percentage * 1, 2)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
