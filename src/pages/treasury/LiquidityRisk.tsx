import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
import { Progress } from '@/components/ui/progress';
import {
  ArrowLeft,
  Activity,
  TrendingUp,
  TrendingDown,
  Download,
  AlertTriangle,
  CheckCircle,
  DollarSign,
  Calendar,
} from 'lucide-react';

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

// LCR Components
const lcrComponents = {
  hqla: {
    level1: 250000000,
    level2a: 80000000,
    level2b: 45000000,
    total: 375000000,
  },
  outflows: {
    retailDeposits: 45000000,
    wholesaleDeposits: 120000000,
    creditFacilities: 35000000,
    other: 25000000,
    total: 225000000,
  },
  inflows: {
    retailInflows: 15000000,
    wholesaleInflows: 60000000,
    other: 10000000,
    total: 85000000,
    capped: 75000000,
  },
  lcr: 125,
};

// Cash Flow Ladder
const cashFlowLadder = [
  { bucket: 'Overnight', inflows: 25000000, outflows: 35000000, net: -10000000, cumulative: -10000000 },
  { bucket: '2-7 Days', inflows: 45000000, outflows: 55000000, net: -10000000, cumulative: -20000000 },
  { bucket: '8-14 Days', inflows: 60000000, outflows: 50000000, net: 10000000, cumulative: -10000000 },
  { bucket: '15-30 Days', inflows: 85000000, outflows: 65000000, net: 20000000, cumulative: 10000000 },
  { bucket: '1-3 Months', inflows: 150000000, outflows: 120000000, net: 30000000, cumulative: 40000000 },
  { bucket: '3-6 Months', inflows: 200000000, outflows: 180000000, net: 20000000, cumulative: 60000000 },
  { bucket: '6-12 Months', inflows: 280000000, outflows: 250000000, net: 30000000, cumulative: 90000000 },
  { bucket: '>12 Months', inflows: 350000000, outflows: 300000000, net: 50000000, cumulative: 140000000 },
];

// NSFR Components
const nsfrComponents = {
  asf: {
    capital: 180000000,
    longTermFunding: 450000000,
    stableDeposits: 320000000,
    lessStableDeposits: 250000000,
    other: 80000000,
    total: 1280000000,
  },
  rsf: {
    cash: 0,
    unencumberedAssets: 150000000,
    loans: 850000000,
    otherAssets: 145000000,
    total: 1145000000,
  },
  nsfr: 112,
};

// Funding Concentration
const fundingConcentration = [
  { source: 'Public Deposits', amount: 450000000, percent: 35, trend: 'up' },
  { source: 'Bank Borrowings', amount: 320000000, percent: 25, trend: 'stable' },
  { source: 'NCD/Bonds', amount: 250000000, percent: 20, trend: 'up' },
  { source: 'Commercial Paper', amount: 130000000, percent: 10, trend: 'down' },
  { source: 'Subordinated Debt', amount: 80000000, percent: 6, trend: 'stable' },
  { source: 'Other', amount: 50000000, percent: 4, trend: 'stable' },
];

export default function LiquidityRisk() {
  const [selectedScenario, setSelectedScenario] = useState('base');

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Liquidity Risk Management"
        subtitle="Liquidity metrics and cash flow analysis"
        breadcrumbs={[
          { label: 'Risk Dashboard', to: '/admin/treasury/risk-dashboard' },
          { label: 'Liquidity Risk' },
        ]}
        actions={
          <div className="flex gap-2">
            <Select value={selectedScenario} onValueChange={setSelectedScenario}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Scenario" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="base">Base Case</SelectItem>
                <SelectItem value="stress">Stress Case</SelectItem>
                <SelectItem value="severe">Severe Stress</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        }
      />

      {/* Key Ratios */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">LCR</span>
              <Badge variant="default" className="bg-green-100 text-green-800">
                <CheckCircle className="h-3 w-3 mr-1" />
                Compliant
              </Badge>
            </div>
            <div className="text-3xl font-bold mt-2">{lcrComponents.lcr}%</div>
            <Progress value={lcrComponents.lcr > 100 ? 100 : lcrComponents.lcr} className="mt-2 h-2" />
            <p className="text-xs text-muted-foreground mt-1">Minimum: 100%</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">NSFR</span>
              <Badge variant="default" className="bg-green-100 text-green-800">
                <CheckCircle className="h-3 w-3 mr-1" />
                Compliant
              </Badge>
            </div>
            <div className="text-3xl font-bold mt-2">{nsfrComponents.nsfr}%</div>
            <Progress value={nsfrComponents.nsfr > 100 ? 100 : nsfrComponents.nsfr} className="mt-2 h-2" />
            <p className="text-xs text-muted-foreground mt-1">Minimum: 100%</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">HQLA</div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(lcrComponents.hqla.total)}</div>
            <p className="text-xs text-muted-foreground mt-1">High Quality Liquid Assets</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">30-Day Gap</div>
            <div className={`text-2xl font-bold mt-1 ${cashFlowLadder[3].cumulative >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(cashFlowLadder[3].cumulative)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Cumulative net cash flow</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="lcr" className="space-y-4">
        <TabsList>
          <TabsTrigger value="lcr">LCR Analysis</TabsTrigger>
          <TabsTrigger value="nsfr">NSFR Analysis</TabsTrigger>
          <TabsTrigger value="cashflow">Cash Flow Ladder</TabsTrigger>
          <TabsTrigger value="funding">Funding Concentration</TabsTrigger>
        </TabsList>

        <TabsContent value="lcr">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>High Quality Liquid Assets</CardTitle>
                <CardDescription>Numerator of LCR calculation</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Category</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow>
                      <TableCell>Level 1 Assets (Cash, Govt Securities)</TableCell>
                      <TableCell className="text-right font-medium">{formatCurrency(lcrComponents.hqla.level1)}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Level 2A Assets (PSU Bonds)</TableCell>
                      <TableCell className="text-right font-medium">{formatCurrency(lcrComponents.hqla.level2a)}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Level 2B Assets (Corporate Bonds)</TableCell>
                      <TableCell className="text-right font-medium">{formatCurrency(lcrComponents.hqla.level2b)}</TableCell>
                    </TableRow>
                    <TableRow className="bg-muted/50 font-bold">
                      <TableCell>Total HQLA</TableCell>
                      <TableCell className="text-right">{formatCurrency(lcrComponents.hqla.total)}</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Net Cash Outflows</CardTitle>
                <CardDescription>Denominator of LCR calculation</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Category</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow>
                      <TableCell>Retail Deposit Outflows</TableCell>
                      <TableCell className="text-right font-medium">{formatCurrency(lcrComponents.outflows.retailDeposits)}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Wholesale Deposit Outflows</TableCell>
                      <TableCell className="text-right font-medium">{formatCurrency(lcrComponents.outflows.wholesaleDeposits)}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Credit Facility Drawdowns</TableCell>
                      <TableCell className="text-right font-medium">{formatCurrency(lcrComponents.outflows.creditFacilities)}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Other Outflows</TableCell>
                      <TableCell className="text-right font-medium">{formatCurrency(lcrComponents.outflows.other)}</TableCell>
                    </TableRow>
                    <TableRow className="bg-muted/50">
                      <TableCell>Total Outflows</TableCell>
                      <TableCell className="text-right font-bold">{formatCurrency(lcrComponents.outflows.total)}</TableCell>
                    </TableRow>
                    <TableRow className="text-green-600">
                      <TableCell>Less: Inflows (Capped)</TableCell>
                      <TableCell className="text-right font-medium">-{formatCurrency(lcrComponents.inflows.capped)}</TableCell>
                    </TableRow>
                    <TableRow className="bg-muted/50 font-bold">
                      <TableCell>Net Cash Outflows</TableCell>
                      <TableCell className="text-right">{formatCurrency(lcrComponents.outflows.total - lcrComponents.inflows.capped)}</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="nsfr">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Available Stable Funding (ASF)</CardTitle>
                <CardDescription>Numerator of NSFR calculation</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableBody>
                    <TableRow>
                      <TableCell>Regulatory Capital</TableCell>
                      <TableCell className="text-right font-medium">{formatCurrency(nsfrComponents.asf.capital)}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Long-term Funding ({'>'}1 year)</TableCell>
                      <TableCell className="text-right font-medium">{formatCurrency(nsfrComponents.asf.longTermFunding)}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Stable Deposits</TableCell>
                      <TableCell className="text-right font-medium">{formatCurrency(nsfrComponents.asf.stableDeposits)}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Less Stable Deposits</TableCell>
                      <TableCell className="text-right font-medium">{formatCurrency(nsfrComponents.asf.lessStableDeposits)}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Other Liabilities</TableCell>
                      <TableCell className="text-right font-medium">{formatCurrency(nsfrComponents.asf.other)}</TableCell>
                    </TableRow>
                    <TableRow className="bg-muted/50 font-bold">
                      <TableCell>Total ASF</TableCell>
                      <TableCell className="text-right">{formatCurrency(nsfrComponents.asf.total)}</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Required Stable Funding (RSF)</CardTitle>
                <CardDescription>Denominator of NSFR calculation</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableBody>
                    <TableRow>
                      <TableCell>Cash & Central Bank Reserves</TableCell>
                      <TableCell className="text-right font-medium">{formatCurrency(nsfrComponents.rsf.cash)}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Unencumbered Securities</TableCell>
                      <TableCell className="text-right font-medium">{formatCurrency(nsfrComponents.rsf.unencumberedAssets)}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Performing Loans</TableCell>
                      <TableCell className="text-right font-medium">{formatCurrency(nsfrComponents.rsf.loans)}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Other Assets</TableCell>
                      <TableCell className="text-right font-medium">{formatCurrency(nsfrComponents.rsf.otherAssets)}</TableCell>
                    </TableRow>
                    <TableRow className="bg-muted/50 font-bold">
                      <TableCell>Total RSF</TableCell>
                      <TableCell className="text-right">{formatCurrency(nsfrComponents.rsf.total)}</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="cashflow">
          <Card>
            <CardHeader>
              <CardTitle>Cash Flow Ladder</CardTitle>
              <CardDescription>Projected cash flows by time bucket</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Time Bucket</TableHead>
                    <TableHead className="text-right">Inflows</TableHead>
                    <TableHead className="text-right">Outflows</TableHead>
                    <TableHead className="text-right">Net</TableHead>
                    <TableHead className="text-right">Cumulative</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {cashFlowLadder.map((row) => (
                    <TableRow key={row.bucket}>
                      <TableCell className="font-medium">{row.bucket}</TableCell>
                      <TableCell className="text-right text-green-600">{formatCurrency(row.inflows)}</TableCell>
                      <TableCell className="text-right text-red-600">{formatCurrency(row.outflows)}</TableCell>
                      <TableCell className={`text-right font-medium ${row.net >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {row.net >= 0 ? '+' : ''}{formatCurrency(row.net)}
                      </TableCell>
                      <TableCell className={`text-right font-bold ${row.cumulative >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {row.cumulative >= 0 ? '+' : ''}{formatCurrency(row.cumulative)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="funding">
          <Card>
            <CardHeader>
              <CardTitle>Funding Concentration</CardTitle>
              <CardDescription>Source-wise funding breakdown</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {fundingConcentration.map((item) => (
                  <div key={item.source} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{item.source}</span>
                        {item.trend === 'up' && <TrendingUp className="h-4 w-4 text-green-500" />}
                        {item.trend === 'down' && <TrendingDown className="h-4 w-4 text-red-500" />}
                      </div>
                      <div className="text-right">
                        <span className="font-bold">{item.percent}%</span>
                        <span className="text-sm text-muted-foreground ml-2">({formatCurrency(item.amount)})</span>
                      </div>
                    </div>
                    <Progress value={item.percent} className="h-2" />
                  </div>
                ))}
              </div>

              <div className="mt-6 p-4 bg-yellow-50 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-yellow-800">Concentration Alert</p>
                    <p className="text-sm text-yellow-700 mt-1">
                      Public deposits constitute 35% of total funding. Diversification recommended
                      to reduce reliance on any single funding source.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
