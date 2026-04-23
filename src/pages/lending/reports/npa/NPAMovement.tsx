import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, Filter, TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react';
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
import { Badge } from '@/components/ui/badge';
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
  PieChart,
  Pie,
  Cell,
} from 'recharts';

// Mock data
const npaMetrics = {
  grossNPA: 1600000000, // 160 Cr
  netNPA: 900000000, // 90 Cr
  grossNPAPercent: 3.2,
  netNPAPercent: 1.8,
  totalProvisions: 700000000, // 70 Cr
  provisionCoverageRatio: 43.75,
  npaAccounts: 28,
};

const npaMovement = {
  opening: 1450000000, // 145 Cr
  additions: 250000000, // 25 Cr
  upgrades: 50000000, // 5 Cr
  recoveries: 35000000, // 3.5 Cr
  writeOffs: 15000000, // 1.5 Cr
  closing: 1600000000, // 160 Cr
};

const monthlyNPATrend = [
  { month: 'Oct', grossNPA: 3.0, netNPA: 1.6 },
  { month: 'Nov', grossNPA: 3.1, netNPA: 1.7 },
  { month: 'Dec', grossNPA: 3.15, netNPA: 1.75 },
  { month: 'Jan', grossNPA: 3.2, netNPA: 1.8 },
];

const classificationBreakdown = [
  { category: 'Sub-Standard', amount: 850000000, accounts: 15, provision: 15, color: '#f97316' },
  { category: 'Doubtful 1', amount: 400000000, accounts: 7, provision: 25, color: '#ef4444' },
  { category: 'Doubtful 2', amount: 250000000, accounts: 4, provision: 40, color: '#dc2626' },
  { category: 'Doubtful 3', amount: 75000000, accounts: 1, provision: 100, color: '#b91c1c' },
  { category: 'Loss', amount: 25000000, accounts: 1, provision: 100, color: '#7f1d1d' },
];

const productWiseNPA = [
  { product: 'Term Loan', npaAmount: 800000000, totalAUM: 25000000000, npaPercent: 3.2 },
  { product: 'Working Capital', npaAmount: 400000000, totalAUM: 12000000000, npaPercent: 3.33 },
  { product: 'LAP', npaAmount: 280000000, totalAUM: 8000000000, npaPercent: 3.5 },
  { product: 'Project Finance', npaAmount: 120000000, totalAUM: 5000000000, npaPercent: 2.4 },
];

const smaAccounts = [
  { category: 'SMA-0 (1-30 DPD)', amount: 300000000, accounts: 12 },
  { category: 'SMA-1 (31-60 DPD)', amount: 200000000, accounts: 8 },
  { category: 'SMA-2 (61-90 DPD)', amount: 150000000, accounts: 5 },
];

const topNPAAccounts = [
  {
    id: '1',
    accountNumber: 'SMFC/TL/2020/L00045',
    entityName: 'Eastern Trading Co',
    outstanding: 450000000,
    dpd: 245,
    classification: 'DOUBTFUL_1',
    provision: 112500000,
  },
  {
    id: '2',
    accountNumber: 'SMFC/WC/2019/L00023',
    entityName: 'Western Industries',
    outstanding: 320000000,
    dpd: 180,
    classification: 'SUB_STANDARD',
    provision: 48000000,
  },
  {
    id: '3',
    accountNumber: 'SMFC/LAP/2021/L00089',
    entityName: 'Deccan Enterprises',
    outstanding: 280000000,
    dpd: 420,
    classification: 'DOUBTFUL_2',
    provision: 112000000,
  },
];

export default function NPAMovement() {
  const navigate = useNavigate();
  const [period, setPeriod] = useState<'MTD' | 'QTD' | 'YTD'>('QTD');
  const [productFilter, setProductFilter] = useState('ALL');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/admin/lending/reports')}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-semibold">NPA Movement Report</h1>
            <p className="text-muted-foreground">
              Non-performing assets analysis and provisioning
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
          <Select value={productFilter} onValueChange={setProductFilter}>
            <SelectTrigger className="w-[150px]">
              <Filter className="mr-2 h-4 w-4" />
              <SelectValue placeholder="Product" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All Products</SelectItem>
              <SelectItem value="TL">Term Loan</SelectItem>
              <SelectItem value="WC">Working Capital</SelectItem>
              <SelectItem value="LAP">LAP</SelectItem>
              <SelectItem value="PF">Project Finance</SelectItem>
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
              Gross NPA
            </CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={npaMetrics.grossNPA}
              abbreviated
              className="text-2xl font-bold text-red-600"
            />
            <p className="text-sm text-muted-foreground mt-1">
              <PercentageDisplay value={npaMetrics.grossNPAPercent} /> of AUM
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Net NPA
            </CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={npaMetrics.netNPA}
              abbreviated
              className="text-2xl font-bold text-amber-600"
            />
            <p className="text-sm text-muted-foreground mt-1">
              <PercentageDisplay value={npaMetrics.netNPAPercent} /> of AUM
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Provisions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={npaMetrics.totalProvisions}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-sm text-muted-foreground mt-1">
              Against NPA
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Provision Coverage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              <PercentageDisplay value={npaMetrics.provisionCoverageRatio} />
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              Coverage Ratio
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              NPA Accounts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{npaMetrics.npaAccounts}</div>
            <p className="text-sm text-muted-foreground mt-1">
              Total accounts
            </p>
          </CardContent>
        </Card>
      </div>

      {/* NPA Movement Statement */}
      <Card>
        <CardHeader>
          <CardTitle>NPA Movement Statement</CardTitle>
          <CardDescription>Quarter-wise NPA movement analysis</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-6">
            <Card className="bg-muted/50">
              <CardContent className="pt-6">
                <p className="text-sm text-muted-foreground">Opening NPA</p>
                <AmountDisplay
                  amount={npaMovement.opening}
                  abbreviated
                  className="text-xl font-bold mt-1"
                />
              </CardContent>
            </Card>
            <Card className="bg-red-50 border-red-200">
              <CardContent className="pt-6">
                <p className="text-sm text-red-600">+ Additions</p>
                <AmountDisplay
                  amount={npaMovement.additions}
                  abbreviated
                  className="text-xl font-bold mt-1 text-red-600"
                />
              </CardContent>
            </Card>
            <Card className="bg-green-50 border-green-200">
              <CardContent className="pt-6">
                <p className="text-sm text-green-600">- Upgrades</p>
                <AmountDisplay
                  amount={npaMovement.upgrades}
                  abbreviated
                  className="text-xl font-bold mt-1 text-green-600"
                />
              </CardContent>
            </Card>
            <Card className="bg-green-50 border-green-200">
              <CardContent className="pt-6">
                <p className="text-sm text-green-600">- Recoveries</p>
                <AmountDisplay
                  amount={npaMovement.recoveries}
                  abbreviated
                  className="text-xl font-bold mt-1 text-green-600"
                />
              </CardContent>
            </Card>
            <Card className="bg-purple-50 border-purple-200">
              <CardContent className="pt-6">
                <p className="text-sm text-purple-600">- Write-offs</p>
                <AmountDisplay
                  amount={npaMovement.writeOffs}
                  abbreviated
                  className="text-xl font-bold mt-1 text-purple-600"
                />
              </CardContent>
            </Card>
            <Card className="bg-muted/50">
              <CardContent className="pt-6">
                <p className="text-sm text-muted-foreground">Closing NPA</p>
                <AmountDisplay
                  amount={npaMovement.closing}
                  abbreviated
                  className="text-xl font-bold mt-1"
                />
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>

      {/* NPA Trend & Classification */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* NPA Trend */}
        <Card>
          <CardHeader>
            <CardTitle>NPA Trend</CardTitle>
            <CardDescription>Gross NPA vs Net NPA (%)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={monthlyNPATrend}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis domain={[0, 5]} />
                  <Tooltip formatter={(value: number | undefined) => [`${value ?? 0}%`, '']} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="grossNPA"
                    stroke="#ef4444"
                    strokeWidth={2}
                    name="Gross NPA %"
                  />
                  <Line
                    type="monotone"
                    dataKey="netNPA"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    name="Net NPA %"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Classification Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Classification Breakdown</CardTitle>
            <CardDescription>NPA by asset classification</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={classificationBreakdown}
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    dataKey="amount"
                    label={({ category, percent }: any) =>
                      `${category}: ${(percent * 100).toFixed(0)}%`
                    }
                  >
                    {classificationBreakdown.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number | undefined) => [
                      `₹ ${((value ?? 0) / 10000000).toFixed(2)} Cr`,
                      'Amount',
                    ]}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* SMA Pipeline */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-500" />
            SMA Pipeline (Early Warning)
          </CardTitle>
          <CardDescription>Accounts at risk of slipping into NPA</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            {smaAccounts.map((sma) => (
              <Card key={sma.category} className="bg-yellow-50 border-yellow-200">
                <CardContent className="pt-6">
                  <p className="text-sm font-medium">{sma.category}</p>
                  <AmountDisplay
                    amount={sma.amount}
                    abbreviated
                    className="text-2xl font-bold mt-2"
                  />
                  <p className="text-sm text-muted-foreground mt-1">
                    {sma.accounts} accounts
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Classification Details Table */}
      <Card>
        <CardHeader>
          <CardTitle>Classification-wise Details</CardTitle>
          <CardDescription>NPA breakdown with provisioning rates</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Classification</TableHead>
                <TableHead className="text-right">Outstanding</TableHead>
                <TableHead className="text-right">Accounts</TableHead>
                <TableHead className="text-right">Provision Rate</TableHead>
                <TableHead className="text-right">Provision Amount</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {classificationBreakdown.map((item) => (
                <TableRow key={item.category}>
                  <TableCell className="font-medium">{item.category}</TableCell>
                  <TableCell className="text-right">
                    <AmountDisplay amount={item.amount} abbreviated />
                  </TableCell>
                  <TableCell className="text-right">{item.accounts}</TableCell>
                  <TableCell className="text-right">{item.provision}%</TableCell>
                  <TableCell className="text-right">
                    <AmountDisplay
                      amount={(item.amount * item.provision) / 100}
                      abbreviated
                    />
                  </TableCell>
                </TableRow>
              ))}
              <TableRow className="font-bold bg-muted/50">
                <TableCell>Total</TableCell>
                <TableCell className="text-right">
                  <AmountDisplay amount={npaMetrics.grossNPA} abbreviated />
                </TableCell>
                <TableCell className="text-right">{npaMetrics.npaAccounts}</TableCell>
                <TableCell className="text-right">-</TableCell>
                <TableCell className="text-right">
                  <AmountDisplay amount={npaMetrics.totalProvisions} abbreviated />
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Product-wise NPA */}
      <Card>
        <CardHeader>
          <CardTitle>Product-wise NPA</CardTitle>
          <CardDescription>NPA distribution by loan product</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead>
                <TableHead className="text-right">Total AUM</TableHead>
                <TableHead className="text-right">NPA Amount</TableHead>
                <TableHead className="text-right">NPA %</TableHead>
                <TableHead>NPA Distribution</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {productWiseNPA.map((item) => (
                <TableRow key={item.product}>
                  <TableCell className="font-medium">{item.product}</TableCell>
                  <TableCell className="text-right">
                    <AmountDisplay amount={item.totalAUM} abbreviated />
                  </TableCell>
                  <TableCell className="text-right">
                    <AmountDisplay amount={item.npaAmount} abbreviated />
                  </TableCell>
                  <TableCell className="text-right">
                    <span
                      className={
                        item.npaPercent <= 3
                          ? 'text-green-600'
                          : item.npaPercent <= 5
                          ? 'text-yellow-600'
                          : 'text-red-600'
                      }
                    >
                      <PercentageDisplay value={item.npaPercent} />
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="w-full h-2 bg-muted rounded-full">
                      <div
                        className="h-full rounded-full bg-red-500"
                        style={{ width: `${item.npaPercent * 10}%` }}
                      />
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Top NPA Accounts */}
      <Card>
        <CardHeader>
          <CardTitle>Top NPA Accounts</CardTitle>
          <CardDescription>Largest NPA exposures</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Account Number</TableHead>
                <TableHead>Entity Name</TableHead>
                <TableHead className="text-right">Outstanding</TableHead>
                <TableHead className="text-right">DPD</TableHead>
                <TableHead>Classification</TableHead>
                <TableHead className="text-right">Provision</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {topNPAAccounts.map((account) => (
                <TableRow
                  key={account.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() =>
                    navigate(`/admin/lending/collections/npa/${account.id}`)
                  }
                >
                  <TableCell className="font-mono text-sm">
                    {account.accountNumber}
                  </TableCell>
                  <TableCell className="font-medium">{account.entityName}</TableCell>
                  <TableCell className="text-right">
                    <AmountDisplay amount={account.outstanding} abbreviated />
                  </TableCell>
                  <TableCell className="text-right">
                    <Badge variant="destructive">{account.dpd} days</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={
                        account.classification.includes('SUB')
                          ? 'bg-orange-100 text-orange-700'
                          : account.classification.includes('DOUBTFUL')
                          ? 'bg-red-100 text-red-700'
                          : 'bg-red-200 text-red-800'
                      }
                    >
                      {account.classification.replace('_', ' ')}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <AmountDisplay amount={account.provision} abbreviated />
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
