import { useState } from 'react';
import { Download, RefreshCw, Calendar, TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/common/PageHeader';
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
import { Badge } from '@/components/ui/badge';
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
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts';

// ALM Bucket Data (RBI Guidelines)
const almBuckets = [
  { bucket: 'Day 1', daysFrom: 1, daysTo: 1, assets: 2500000000, liabilities: 1800000000, gap: 700000000, cumulativeGap: 700000000 },
  { bucket: '2-7 Days', daysFrom: 2, daysTo: 7, assets: 1500000000, liabilities: 2000000000, gap: -500000000, cumulativeGap: 200000000 },
  { bucket: '8-14 Days', daysFrom: 8, daysTo: 14, assets: 1200000000, liabilities: 1000000000, gap: 200000000, cumulativeGap: 400000000 },
  { bucket: '15-28 Days', daysFrom: 15, daysTo: 28, assets: 2000000000, liabilities: 1500000000, gap: 500000000, cumulativeGap: 900000000 },
  { bucket: '29D-3M', daysFrom: 29, daysTo: 90, assets: 5000000000, liabilities: 4500000000, gap: 500000000, cumulativeGap: 1400000000 },
  { bucket: '3-6M', daysFrom: 91, daysTo: 180, assets: 8000000000, liabilities: 7000000000, gap: 1000000000, cumulativeGap: 2400000000 },
  { bucket: '6-12M', daysFrom: 181, daysTo: 365, assets: 15000000000, liabilities: 12000000000, gap: 3000000000, cumulativeGap: 5400000000 },
  { bucket: '1-3Y', daysFrom: 366, daysTo: 1095, assets: 25000000000, liabilities: 20000000000, gap: 5000000000, cumulativeGap: 10400000000 },
  { bucket: '3-5Y', daysFrom: 1096, daysTo: 1825, assets: 15000000000, liabilities: 10000000000, gap: 5000000000, cumulativeGap: 15400000000 },
  { bucket: '>5Y', daysFrom: 1826, daysTo: null, assets: 10000000000, liabilities: 5000000000, gap: 5000000000, cumulativeGap: 20400000000 },
];

// Interest Rate Sensitivity Data
const irsSensitivity = [
  { bucket: 'Up to 1M', rsaAssets: 4000000000, rslLiabilities: 3500000000, gap: 500000000 },
  { bucket: '1-3M', rsaAssets: 5000000000, rslLiabilities: 4500000000, gap: 500000000 },
  { bucket: '3-6M', rsaAssets: 8000000000, rslLiabilities: 7000000000, gap: 1000000000 },
  { bucket: '6-12M', rsaAssets: 15000000000, rslLiabilities: 12000000000, gap: 3000000000 },
  { bucket: 'Over 1Y', rsaAssets: 50000000000, rslLiabilities: 35000000000, gap: 15000000000 },
];

// Chart data for visualization
const gapChartData = almBuckets.map((bucket) => ({
  name: bucket.bucket,
  assets: bucket.assets / 10000000, // Convert to Cr
  liabilities: bucket.liabilities / 10000000,
  gap: bucket.gap / 10000000,
}));

const cumulativeGapData = almBuckets.map((bucket) => ({
  name: bucket.bucket,
  cumulativeGap: bucket.cumulativeGap / 10000000,
}));

export default function ALMDashboard() {
  const [reportDate, setReportDate] = useState('2025-01-31');

  const totalAssets = almBuckets.reduce((sum, b) => sum + b.assets, 0);
  const totalLiabilities = almBuckets.reduce((sum, b) => sum + b.liabilities, 0);
  const shortTermGap = almBuckets.slice(0, 4).reduce((sum, b) => sum + b.gap, 0);
  const netGap = almBuckets.reduce((sum, b) => sum + b.gap, 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="ALM Dashboard"
        subtitle="Asset Liability Management - Structural Liquidity & Interest Rate Sensitivity"
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
                <SelectItem value="2024-11-30">30-Nov-2024</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline">
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export ALM-1
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Assets</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalAssets} abbreviated className="text-2xl font-bold" />
            <p className="text-xs text-muted-foreground">Loans & advances</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Liabilities</CardTitle>
            <TrendingDown className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalLiabilities} abbreviated className="text-2xl font-bold" />
            <p className="text-xs text-muted-foreground">Borrowings & NCDs</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Short-term Gap</CardTitle>
            {shortTermGap >= 0 ? (
              <Badge variant="default" className="bg-green-100 text-green-700">Surplus</Badge>
            ) : (
              <Badge variant="destructive">Deficit</Badge>
            )}
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={Math.abs(shortTermGap)}
              abbreviated
              className={`text-2xl font-bold ${shortTermGap >= 0 ? 'text-green-600' : 'text-red-600'}`}
            />
            <p className="text-xs text-muted-foreground">Up to 28 days</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Net Gap</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={netGap}
              abbreviated
              className="text-2xl font-bold text-green-600"
            />
            <p className="text-xs text-muted-foreground">Assets - Liabilities</p>
          </CardContent>
        </Card>
      </div>

      {/* Structural Liquidity (ALM-1) */}
      <Card>
        <CardHeader>
          <CardTitle>Structural Liquidity Statement (ALM-1)</CardTitle>
          <CardDescription>
            As on <DateDisplay date={reportDate} /> - RBI bucket-wise analysis
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Time Bucket</TableHead>
                <TableHead className="text-right">Inflows (Assets)</TableHead>
                <TableHead className="text-right">Outflows (Liabilities)</TableHead>
                <TableHead className="text-right">Gap</TableHead>
                <TableHead className="text-right">Cumulative Gap</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {almBuckets.map((bucket, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">{bucket.bucket}</TableCell>
                  <TableCell className="text-right">
                    <AmountDisplay amount={bucket.assets} abbreviated />
                  </TableCell>
                  <TableCell className="text-right">
                    <AmountDisplay amount={bucket.liabilities} abbreviated />
                  </TableCell>
                  <TableCell className={`text-right font-medium ${bucket.gap >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {bucket.gap >= 0 ? '+' : ''}
                    <AmountDisplay amount={bucket.gap} abbreviated />
                  </TableCell>
                  <TableCell className={`text-right font-medium ${bucket.cumulativeGap >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {bucket.cumulativeGap >= 0 ? '+' : ''}
                    <AmountDisplay amount={bucket.cumulativeGap} abbreviated />
                  </TableCell>
                  <TableCell>
                    {bucket.gap >= 0 ? (
                      <Badge variant="outline" className="bg-green-100 text-green-700">
                        Surplus
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="bg-red-100 text-red-700">
                        <AlertTriangle className="h-3 w-3 mr-1" />
                        Deficit
                      </Badge>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              <TableRow className="font-bold bg-muted/50">
                <TableCell>Total</TableCell>
                <TableCell className="text-right">
                  <AmountDisplay amount={totalAssets} abbreviated />
                </TableCell>
                <TableCell className="text-right">
                  <AmountDisplay amount={totalLiabilities} abbreviated />
                </TableCell>
                <TableCell className="text-right text-green-600">
                  +<AmountDisplay amount={netGap} abbreviated />
                </TableCell>
                <TableCell></TableCell>
                <TableCell></TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Charts */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Asset-Liability Gap Analysis</CardTitle>
            <CardDescription>Bucket-wise inflows vs outflows</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={gapChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip
                    formatter={(value: number | undefined) => [`₹ ${(value ?? 0).toFixed(0)} Cr`, '']}
                  />
                  <Legend />
                  <Bar dataKey="assets" name="Assets" fill="#22c55e" />
                  <Bar dataKey="liabilities" name="Liabilities" fill="#f59e0b" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Cumulative Gap Trend</CardTitle>
            <CardDescription>Running liquidity position</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={cumulativeGapData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip
                    formatter={(value: number | undefined) => [`₹ ${(value ?? 0).toFixed(0)} Cr`, 'Cumulative Gap']}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="cumulativeGap"
                    name="Cumulative Gap"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ fill: '#3b82f6' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Interest Rate Sensitivity */}
      <Card>
        <CardHeader>
          <CardTitle>Interest Rate Sensitivity (ALM-2)</CardTitle>
          <CardDescription>
            Impact of 100 bps rate change on NIM - Rate Sensitive Assets vs Liabilities
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Time Bucket</TableHead>
                <TableHead className="text-right">RSA (Rate Sensitive Assets)</TableHead>
                <TableHead className="text-right">RSL (Rate Sensitive Liabilities)</TableHead>
                <TableHead className="text-right">Gap</TableHead>
                <TableHead className="text-right">Impact (+100 bps)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {irsSensitivity.map((row, index) => {
                const impact = (row.gap * 0.01); // 1% of gap
                return (
                  <TableRow key={index}>
                    <TableCell className="font-medium">{row.bucket}</TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={row.rsaAssets} abbreviated />
                    </TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={row.rslLiabilities} abbreviated />
                    </TableCell>
                    <TableCell className={`text-right font-medium ${row.gap >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {row.gap >= 0 ? '+' : ''}
                      <AmountDisplay amount={row.gap} abbreviated />
                    </TableCell>
                    <TableCell className={`text-right font-medium ${impact >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {impact >= 0 ? '+' : ''}
                      <AmountDisplay amount={impact} abbreviated />
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>Note:</strong> A positive gap indicates that assets reprice faster than
              liabilities. In a rising rate environment, this results in higher NIM. The bank
              maintains an asset-sensitive position with positive gaps across most buckets.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Compliance Indicators */}
      <Card>
        <CardHeader>
          <CardTitle>Regulatory Compliance Indicators</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="p-4 border rounded-lg">
              <p className="text-sm text-muted-foreground">LCR (Liquidity Coverage Ratio)</p>
              <p className="text-2xl font-bold text-green-600">125%</p>
              <p className="text-xs text-muted-foreground">Min required: 100%</p>
            </div>
            <div className="p-4 border rounded-lg">
              <p className="text-sm text-muted-foreground">NSFR (Net Stable Funding Ratio)</p>
              <p className="text-2xl font-bold text-green-600">115%</p>
              <p className="text-xs text-muted-foreground">Min required: 100%</p>
            </div>
            <div className="p-4 border rounded-lg">
              <p className="text-sm text-muted-foreground">Short-term Gap / Assets</p>
              <p className="text-2xl font-bold text-green-600">8.5%</p>
              <p className="text-xs text-muted-foreground">Within tolerance</p>
            </div>
            <div className="p-4 border rounded-lg">
              <p className="text-sm text-muted-foreground">CRAR (Capital Adequacy)</p>
              <p className="text-2xl font-bold text-green-600">18.5%</p>
              <p className="text-xs text-muted-foreground">Min required: 15%</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
