import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
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
import {
  BarChart3,
  Download,
  FileText,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Wallet,
  Users,
  Building,
  AlertTriangle,
  ArrowLeft,
  Calendar,
  Filter,
  PieChart,
} from 'lucide-react';
import { Link } from 'react-router-dom';

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    notation: 'compact',
    maximumFractionDigits: 2,
  }).format(value);
};

const formatPercent = (value: number) => `${value.toFixed(2)}%`;

// Portfolio Summary Report
function PortfolioSummaryReport() {
  const [reportDate, setReportDate] = useState(new Date().toISOString().split('T')[0]);

  const portfolioSummary = {
    asOfDate: reportDate,
    totalAUM: 2235000000,
    totalAccounts: 12458,
    avgTicketSize: 179375,
    productBreakdown: [
      { product: 'Business Loan', count: 4520, amount: 890000000, share: 39.8, avgYield: 18.5 },
      { product: 'Vehicle Loan', count: 3890, amount: 620000000, share: 27.7, avgYield: 16.2 },
      { product: 'Gold Loan', count: 2150, amount: 425000000, share: 19.0, avgYield: 14.5 },
      { product: 'Personal Loan', count: 1898, amount: 300000000, share: 13.4, avgYield: 22.0 },
    ],
    tenureBreakdown: [
      { tenure: '0-12 months', count: 3200, amount: 480000000, share: 21.5 },
      { tenure: '12-24 months', count: 4100, amount: 720000000, share: 32.2 },
      { tenure: '24-36 months', count: 3500, amount: 650000000, share: 29.1 },
      { tenure: '36+ months', count: 1658, amount: 385000000, share: 17.2 },
    ],
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Label>As of Date</Label>
          <Input
            type="date"
            value={reportDate}
            onChange={(e) => setReportDate(e.target.value)}
            className="w-40"
          />
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Generate
          </Button>
        </div>
        <Button variant="outline" size="sm">
          <Download className="h-4 w-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-muted-foreground text-sm">
              <Wallet className="h-4 w-4" />
              Total AUM
            </div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(portfolioSummary.totalAUM)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-muted-foreground text-sm">
              <Users className="h-4 w-4" />
              Total Accounts
            </div>
            <div className="text-2xl font-bold mt-1">{portfolioSummary.totalAccounts.toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-muted-foreground text-sm">
              <BarChart3 className="h-4 w-4" />
              Avg Ticket Size
            </div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(portfolioSummary.avgTicketSize)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-muted-foreground text-sm">
              <PieChart className="h-4 w-4" />
              Products
            </div>
            <div className="text-2xl font-bold mt-1">{portfolioSummary.productBreakdown.length}</div>
          </CardContent>
        </Card>
      </div>

      {/* Product-wise Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Product-wise Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead>
                <TableHead className="text-right">Accounts</TableHead>
                <TableHead className="text-right">Outstanding</TableHead>
                <TableHead className="text-right">Share %</TableHead>
                <TableHead className="text-right">Avg Yield %</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {portfolioSummary.productBreakdown.map((item, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">{item.product}</TableCell>
                  <TableCell className="text-right">{item.count.toLocaleString()}</TableCell>
                  <TableCell className="text-right">{formatCurrency(item.amount)}</TableCell>
                  <TableCell className="text-right">{formatPercent(item.share)}</TableCell>
                  <TableCell className="text-right">{formatPercent(item.avgYield)}</TableCell>
                </TableRow>
              ))}
              <TableRow className="font-bold bg-muted/50">
                <TableCell>Total</TableCell>
                <TableCell className="text-right">{portfolioSummary.totalAccounts.toLocaleString()}</TableCell>
                <TableCell className="text-right">{formatCurrency(portfolioSummary.totalAUM)}</TableCell>
                <TableCell className="text-right">100.00%</TableCell>
                <TableCell className="text-right">-</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Tenure-wise Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Tenure-wise Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Tenure Bucket</TableHead>
                <TableHead className="text-right">Accounts</TableHead>
                <TableHead className="text-right">Outstanding</TableHead>
                <TableHead className="text-right">Share %</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {portfolioSummary.tenureBreakdown.map((item, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">{item.tenure}</TableCell>
                  <TableCell className="text-right">{item.count.toLocaleString()}</TableCell>
                  <TableCell className="text-right">{formatCurrency(item.amount)}</TableCell>
                  <TableCell className="text-right">{formatPercent(item.share)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

// Disbursement Report
function DisbursementReport() {
  const [fromDate, setFromDate] = useState(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]);
  const [toDate, setToDate] = useState(new Date().toISOString().split('T')[0]);
  const [groupBy, setGroupBy] = useState('PRODUCT');

  const disbursementData = {
    totalDisbursed: 185000000,
    totalAccounts: 892,
    avgTicketSize: 207399,
    growth: 12.5,
    breakdown: [
      { name: 'Business Loan', count: 320, amount: 72000000, avgAmount: 225000, share: 38.9 },
      { name: 'Vehicle Loan', count: 285, amount: 52000000, avgAmount: 182456, share: 28.1 },
      { name: 'Gold Loan', count: 187, amount: 38000000, avgAmount: 203208, share: 20.5 },
      { name: 'Personal Loan', count: 100, amount: 23000000, avgAmount: 230000, share: 12.4 },
    ],
    trend: [
      { period: 'Week 1', amount: 42000000 },
      { period: 'Week 2', amount: 48000000 },
      { period: 'Week 3', amount: 45000000 },
      { period: 'Week 4', amount: 50000000 },
    ],
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Label>From</Label>
            <Input
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="w-40"
            />
          </div>
          <div className="flex items-center gap-2">
            <Label>To</Label>
            <Input
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="w-40"
            />
          </div>
          <Select value={groupBy} onValueChange={setGroupBy}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="PRODUCT">By Product</SelectItem>
              <SelectItem value="BRANCH">By Branch</SelectItem>
              <SelectItem value="CHANNEL">By Channel</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Generate
          </Button>
        </div>
        <Button variant="outline" size="sm">
          <Download className="h-4 w-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Disbursed</div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(disbursementData.totalDisbursed)}</div>
            <div className="flex items-center text-sm text-green-600 mt-1">
              <TrendingUp className="h-4 w-4 mr-1" />
              +{disbursementData.growth}% vs last period
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Accounts Disbursed</div>
            <div className="text-2xl font-bold mt-1">{disbursementData.totalAccounts}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Avg Ticket Size</div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(disbursementData.avgTicketSize)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Daily Average</div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(disbursementData.totalDisbursed / 30)}</div>
          </CardContent>
        </Card>
      </div>

      {/* Breakdown Table */}
      <Card>
        <CardHeader>
          <CardTitle>Disbursement Breakdown by {groupBy === 'PRODUCT' ? 'Product' : groupBy === 'BRANCH' ? 'Branch' : 'Channel'}</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{groupBy === 'PRODUCT' ? 'Product' : groupBy === 'BRANCH' ? 'Branch' : 'Channel'}</TableHead>
                <TableHead className="text-right">No. of Loans</TableHead>
                <TableHead className="text-right">Amount Disbursed</TableHead>
                <TableHead className="text-right">Avg Ticket Size</TableHead>
                <TableHead className="text-right">Share %</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {disbursementData.breakdown.map((item, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">{item.name}</TableCell>
                  <TableCell className="text-right">{item.count}</TableCell>
                  <TableCell className="text-right">{formatCurrency(item.amount)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(item.avgAmount)}</TableCell>
                  <TableCell className="text-right">{formatPercent(item.share)}</TableCell>
                </TableRow>
              ))}
              <TableRow className="font-bold bg-muted/50">
                <TableCell>Total</TableCell>
                <TableCell className="text-right">{disbursementData.totalAccounts}</TableCell>
                <TableCell className="text-right">{formatCurrency(disbursementData.totalDisbursed)}</TableCell>
                <TableCell className="text-right">{formatCurrency(disbursementData.avgTicketSize)}</TableCell>
                <TableCell className="text-right">100.00%</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

// Collection Report
function CollectionReport() {
  const [fromDate, setFromDate] = useState(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]);
  const [toDate, setToDate] = useState(new Date().toISOString().split('T')[0]);

  const collectionData = {
    totalDemand: 125000000,
    totalCollection: 110500000,
    collectionEfficiency: 88.4,
    principalCollected: 72000000,
    interestCollected: 38500000,
    channelBreakdown: [
      { channel: 'NACH/ECS', amount: 65000000, share: 58.8, efficiency: 92.5 },
      { channel: 'Cash', amount: 22000000, share: 19.9, efficiency: 85.0 },
      { channel: 'UPI/Online', amount: 15500000, share: 14.0, efficiency: 88.2 },
      { channel: 'Cheque', amount: 8000000, share: 7.2, efficiency: 78.5 },
    ],
    bucketWise: [
      { bucket: 'Current', demand: 95000000, collected: 92000000, efficiency: 96.8 },
      { bucket: '1-30 DPD', demand: 18000000, collected: 12500000, efficiency: 69.4 },
      { bucket: '31-60 DPD', demand: 8000000, collected: 4500000, efficiency: 56.3 },
      { bucket: '61-90 DPD', demand: 4000000, collected: 1500000, efficiency: 37.5 },
    ],
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Label>From</Label>
            <Input
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="w-40"
            />
          </div>
          <div className="flex items-center gap-2">
            <Label>To</Label>
            <Input
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="w-40"
            />
          </div>
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Generate
          </Button>
        </div>
        <Button variant="outline" size="sm">
          <Download className="h-4 w-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Demand</div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(collectionData.totalDemand)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Collection</div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(collectionData.totalCollection)}</div>
          </CardContent>
        </Card>
        <Card className="bg-green-50">
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Collection Efficiency</div>
            <div className="text-2xl font-bold mt-1 text-green-600">{formatPercent(collectionData.collectionEfficiency)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Shortfall</div>
            <div className="text-2xl font-bold mt-1 text-red-600">
              {formatCurrency(collectionData.totalDemand - collectionData.totalCollection)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Collection by Channel */}
      <Card>
        <CardHeader>
          <CardTitle>Collection by Channel</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Collection Channel</TableHead>
                <TableHead className="text-right">Amount Collected</TableHead>
                <TableHead className="text-right">Share %</TableHead>
                <TableHead className="text-right">Efficiency %</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {collectionData.channelBreakdown.map((item, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">{item.channel}</TableCell>
                  <TableCell className="text-right">{formatCurrency(item.amount)}</TableCell>
                  <TableCell className="text-right">{formatPercent(item.share)}</TableCell>
                  <TableCell className="text-right">
                    <Badge variant={item.efficiency >= 90 ? 'default' : item.efficiency >= 80 ? 'secondary' : 'destructive'}>
                      {formatPercent(item.efficiency)}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Collection by DPD Bucket */}
      <Card>
        <CardHeader>
          <CardTitle>Collection by DPD Bucket</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>DPD Bucket</TableHead>
                <TableHead className="text-right">Demand</TableHead>
                <TableHead className="text-right">Collected</TableHead>
                <TableHead className="text-right">Shortfall</TableHead>
                <TableHead className="text-right">Efficiency %</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {collectionData.bucketWise.map((item, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">{item.bucket}</TableCell>
                  <TableCell className="text-right">{formatCurrency(item.demand)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(item.collected)}</TableCell>
                  <TableCell className="text-right text-red-600">
                    {formatCurrency(item.demand - item.collected)}
                  </TableCell>
                  <TableCell className="text-right">
                    <Badge variant={item.efficiency >= 90 ? 'default' : item.efficiency >= 70 ? 'secondary' : 'destructive'}>
                      {formatPercent(item.efficiency)}
                    </Badge>
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

// Delinquency Report
function DelinquencyReport() {
  const [reportDate, setReportDate] = useState(new Date().toISOString().split('T')[0]);

  const delinquencyData = {
    totalPortfolio: 2235000000,
    totalOverdue: 198000000,
    delinquencyRate: 8.86,
    bucketWise: [
      { bucket: 'Current', accounts: 10200, amount: 2037000000, share: 91.1 },
      { bucket: '1-30 DPD', accounts: 1250, amount: 98000000, share: 4.4 },
      { bucket: '31-60 DPD', accounts: 520, amount: 52000000, share: 2.3 },
      { bucket: '61-90 DPD', accounts: 288, amount: 28000000, share: 1.3 },
      { bucket: '90+ DPD (NPA)', accounts: 200, amount: 20000000, share: 0.9 },
    ],
    movement: [
      { from: 'Current', to: '1-30 DPD', accounts: 180, amount: 15000000 },
      { from: '1-30 DPD', to: '31-60 DPD', accounts: 85, amount: 8500000 },
      { from: '31-60 DPD', to: '61-90 DPD', accounts: 42, amount: 4200000 },
      { from: '61-90 DPD', to: 'NPA', accounts: 25, amount: 2500000 },
    ],
    topDelinquent: [
      { id: 'LN2024001234', customer: 'ABC Enterprises', amount: 5200000, dpd: 75, product: 'Business Loan' },
      { id: 'LN2024001567', customer: 'XYZ Traders', amount: 3800000, dpd: 62, product: 'Business Loan' },
      { id: 'LN2024002890', customer: 'PQR Industries', amount: 2900000, dpd: 48, product: 'Vehicle Loan' },
      { id: 'LN2024003456', customer: 'LMN Services', amount: 2500000, dpd: 35, product: 'Gold Loan' },
    ],
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Label>As of Date</Label>
          <Input
            type="date"
            value={reportDate}
            onChange={(e) => setReportDate(e.target.value)}
            className="w-40"
          />
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Generate
          </Button>
        </div>
        <Button variant="outline" size="sm">
          <Download className="h-4 w-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Portfolio</div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(delinquencyData.totalPortfolio)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Overdue</div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(delinquencyData.totalOverdue)}</div>
          </CardContent>
        </Card>
        <Card className="bg-orange-50">
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Delinquency Rate</div>
            <div className="text-2xl font-bold mt-1 text-orange-600">{formatPercent(delinquencyData.delinquencyRate)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Overdue Accounts</div>
            <div className="text-2xl font-bold mt-1">
              {delinquencyData.bucketWise.filter(b => b.bucket !== 'Current').reduce((sum, b) => sum + b.accounts, 0).toLocaleString()}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Bucket-wise Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>DPD Bucket Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>DPD Bucket</TableHead>
                <TableHead className="text-right">Accounts</TableHead>
                <TableHead className="text-right">Outstanding</TableHead>
                <TableHead className="text-right">Share %</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {delinquencyData.bucketWise.map((item, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">{item.bucket}</TableCell>
                  <TableCell className="text-right">{item.accounts.toLocaleString()}</TableCell>
                  <TableCell className="text-right">{formatCurrency(item.amount)}</TableCell>
                  <TableCell className="text-right">{formatPercent(item.share)}</TableCell>
                  <TableCell>
                    <Badge variant={
                      item.bucket === 'Current' ? 'default' :
                      item.bucket === '1-30 DPD' ? 'secondary' :
                      item.bucket.includes('NPA') ? 'destructive' : 'outline'
                    }>
                      {item.bucket === 'Current' ? 'Standard' : item.bucket.includes('NPA') ? 'NPA' : 'SMA'}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Top Delinquent Accounts */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-500" />
            Top Delinquent Accounts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Loan ID</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>Product</TableHead>
                <TableHead className="text-right">Outstanding</TableHead>
                <TableHead className="text-right">DPD</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {delinquencyData.topDelinquent.map((item, index) => (
                <TableRow key={index}>
                  <TableCell className="font-mono text-sm">{item.id}</TableCell>
                  <TableCell>{item.customer}</TableCell>
                  <TableCell>{item.product}</TableCell>
                  <TableCell className="text-right">{formatCurrency(item.amount)}</TableCell>
                  <TableCell className="text-right">
                    <Badge variant={item.dpd > 60 ? 'destructive' : 'secondary'}>
                      {item.dpd} days
                    </Badge>
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

// Profitability Report
function ProfitabilityReport() {
  const [fromDate, setFromDate] = useState(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]);
  const [toDate, setToDate] = useState(new Date().toISOString().split('T')[0]);

  const profitabilityData = {
    totalIncome: 42500000,
    interestIncome: 38000000,
    feeIncome: 4500000,
    totalExpense: 28000000,
    interestExpense: 18000000,
    operatingExpense: 8500000,
    provisionExpense: 1500000,
    netProfit: 14500000,
    nim: 4.2,
    roa: 2.8,
    roe: 15.5,
    costToIncome: 45.2,
    productWise: [
      { product: 'Business Loan', income: 18000000, expense: 11500000, profit: 6500000, margin: 36.1 },
      { product: 'Vehicle Loan', income: 12500000, expense: 8200000, profit: 4300000, margin: 34.4 },
      { product: 'Gold Loan', income: 7500000, expense: 5000000, profit: 2500000, margin: 33.3 },
      { product: 'Personal Loan', income: 4500000, expense: 3300000, profit: 1200000, margin: 26.7 },
    ],
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Label>From</Label>
            <Input
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="w-40"
            />
          </div>
          <div className="flex items-center gap-2">
            <Label>To</Label>
            <Input
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="w-40"
            />
          </div>
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Generate
          </Button>
        </div>
        <Button variant="outline" size="sm">
          <Download className="h-4 w-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Key Ratios */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-green-50">
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Net Profit</div>
            <div className="text-2xl font-bold mt-1 text-green-600">{formatCurrency(profitabilityData.netProfit)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">NIM</div>
            <div className="text-2xl font-bold mt-1">{formatPercent(profitabilityData.nim)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">ROA</div>
            <div className="text-2xl font-bold mt-1">{formatPercent(profitabilityData.roa)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">ROE</div>
            <div className="text-2xl font-bold mt-1">{formatPercent(profitabilityData.roe)}</div>
          </CardContent>
        </Card>
      </div>

      {/* Income Statement Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Income Statement Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between items-center py-2 border-b">
              <span className="font-medium">Interest Income</span>
              <span className="text-green-600">{formatCurrency(profitabilityData.interestIncome)}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span className="font-medium">Fee & Other Income</span>
              <span className="text-green-600">{formatCurrency(profitabilityData.feeIncome)}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b bg-green-50 px-2 rounded">
              <span className="font-bold">Total Income</span>
              <span className="font-bold text-green-600">{formatCurrency(profitabilityData.totalIncome)}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span className="font-medium">Interest Expense</span>
              <span className="text-red-600">({formatCurrency(profitabilityData.interestExpense)})</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span className="font-medium">Operating Expense</span>
              <span className="text-red-600">({formatCurrency(profitabilityData.operatingExpense)})</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span className="font-medium">Provision Expense</span>
              <span className="text-red-600">({formatCurrency(profitabilityData.provisionExpense)})</span>
            </div>
            <div className="flex justify-between items-center py-2 bg-blue-50 px-2 rounded">
              <span className="font-bold">Net Profit</span>
              <span className="font-bold text-blue-600">{formatCurrency(profitabilityData.netProfit)}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Product-wise Profitability */}
      <Card>
        <CardHeader>
          <CardTitle>Product-wise Profitability</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead>
                <TableHead className="text-right">Income</TableHead>
                <TableHead className="text-right">Expense</TableHead>
                <TableHead className="text-right">Profit</TableHead>
                <TableHead className="text-right">Margin %</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {profitabilityData.productWise.map((item, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">{item.product}</TableCell>
                  <TableCell className="text-right text-green-600">{formatCurrency(item.income)}</TableCell>
                  <TableCell className="text-right text-red-600">{formatCurrency(item.expense)}</TableCell>
                  <TableCell className="text-right font-medium">{formatCurrency(item.profit)}</TableCell>
                  <TableCell className="text-right">
                    <Badge variant={item.margin >= 35 ? 'default' : 'secondary'}>
                      {formatPercent(item.margin)}
                    </Badge>
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

// Branch Performance Report
function BranchPerformanceReport() {
  const [fromDate, setFromDate] = useState(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]);
  const [toDate, setToDate] = useState(new Date().toISOString().split('T')[0]);

  const branchData = {
    branches: [
      {
        name: 'Mumbai Central',
        aum: 520000000,
        disbursement: 45000000,
        collection: 38000000,
        efficiency: 92.5,
        npa: 2.8,
        staff: 25,
        productivity: 20800000,
      },
      {
        name: 'Delhi NCR',
        aum: 480000000,
        disbursement: 42000000,
        collection: 35000000,
        efficiency: 89.2,
        npa: 3.5,
        staff: 22,
        productivity: 21818181,
      },
      {
        name: 'Bangalore',
        aum: 410000000,
        disbursement: 38000000,
        collection: 32000000,
        efficiency: 90.8,
        npa: 3.2,
        staff: 18,
        productivity: 22777777,
      },
      {
        name: 'Chennai',
        aum: 380000000,
        disbursement: 32000000,
        collection: 28000000,
        efficiency: 88.5,
        npa: 4.1,
        staff: 16,
        productivity: 23750000,
      },
      {
        name: 'Pune',
        aum: 320000000,
        disbursement: 28000000,
        collection: 24000000,
        efficiency: 87.2,
        npa: 4.5,
        staff: 14,
        productivity: 22857142,
      },
    ],
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Label>From</Label>
            <Input
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="w-40"
            />
          </div>
          <div className="flex items-center gap-2">
            <Label>To</Label>
            <Input
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="w-40"
            />
          </div>
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Generate
          </Button>
        </div>
        <Button variant="outline" size="sm">
          <Download className="h-4 w-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Branch Performance Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building className="h-5 w-5" />
            Branch Performance Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Branch</TableHead>
                <TableHead className="text-right">AUM</TableHead>
                <TableHead className="text-right">Disbursement</TableHead>
                <TableHead className="text-right">Collection</TableHead>
                <TableHead className="text-right">Efficiency</TableHead>
                <TableHead className="text-right">NPA %</TableHead>
                <TableHead className="text-right">Staff</TableHead>
                <TableHead className="text-right">Per Capita AUM</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {branchData.branches.map((branch, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">{branch.name}</TableCell>
                  <TableCell className="text-right">{formatCurrency(branch.aum)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(branch.disbursement)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(branch.collection)}</TableCell>
                  <TableCell className="text-right">
                    <Badge variant={branch.efficiency >= 90 ? 'default' : branch.efficiency >= 85 ? 'secondary' : 'destructive'}>
                      {formatPercent(branch.efficiency)}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <span className={branch.npa <= 3 ? 'text-green-600' : branch.npa <= 4 ? 'text-orange-600' : 'text-red-600'}>
                      {formatPercent(branch.npa)}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">{branch.staff}</TableCell>
                  <TableCell className="text-right">{formatCurrency(branch.productivity)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

export default function MISReports() {
  const [activeTab, setActiveTab] = useState('portfolio');

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/admin/reports">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <BarChart3 className="h-6 w-6" />
            MIS Reports
          </h1>
          <p className="text-muted-foreground">Management information and analytics reports</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-6 w-full max-w-4xl">
          <TabsTrigger value="portfolio">Portfolio</TabsTrigger>
          <TabsTrigger value="disbursement">Disbursement</TabsTrigger>
          <TabsTrigger value="collection">Collection</TabsTrigger>
          <TabsTrigger value="delinquency">Delinquency</TabsTrigger>
          <TabsTrigger value="profitability">Profitability</TabsTrigger>
          <TabsTrigger value="branch">Branch</TabsTrigger>
        </TabsList>

        <TabsContent value="portfolio" className="mt-6">
          <PortfolioSummaryReport />
        </TabsContent>

        <TabsContent value="disbursement" className="mt-6">
          <DisbursementReport />
        </TabsContent>

        <TabsContent value="collection" className="mt-6">
          <CollectionReport />
        </TabsContent>

        <TabsContent value="delinquency" className="mt-6">
          <DelinquencyReport />
        </TabsContent>

        <TabsContent value="profitability" className="mt-6">
          <ProfitabilityReport />
        </TabsContent>

        <TabsContent value="branch" className="mt-6">
          <BranchPerformanceReport />
        </TabsContent>
      </Tabs>
    </div>
  );
}
