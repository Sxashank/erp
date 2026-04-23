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
  BarChart3,
  TrendingUp,
  TrendingDown,
  Calendar,
  Download,
  Info,
  AlertTriangle,
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

// VaR data by portfolio
const varByPortfolio = [
  { portfolio: 'Loan Portfolio', var95: 8500000, var99: 12500000, limit: 15000000, change: 2.5 },
  { portfolio: 'Treasury Investments', var95: 3200000, var99: 4800000, limit: 6000000, change: -1.2 },
  { portfolio: 'Fixed Deposits', var95: 1800000, var99: 2700000, limit: 4000000, change: 0.5 },
  { portfolio: 'Interbank Lending', var95: 2000000, var99: 2500000, limit: 3000000, change: 1.8 },
];

// Historical VaR trend
const varTrend = [
  { date: '2025-01-10', var95: 14800000, actual: 2500000 },
  { date: '2025-01-11', var95: 15000000, actual: 3200000 },
  { date: '2025-01-12', var95: 15200000, actual: 1800000 },
  { date: '2025-01-13', var95: 15100000, actual: 4500000 },
  { date: '2025-01-14', var95: 15300000, actual: 2100000 },
  { date: '2025-01-15', var95: 15500000, actual: 2800000 },
];

// VaR by risk factor
const varByRiskFactor = [
  { factor: 'Interest Rate Risk', var: 6500000, contribution: 42 },
  { factor: 'Credit Spread Risk', var: 4200000, contribution: 27 },
  { factor: 'Foreign Exchange Risk', var: 1800000, contribution: 12 },
  { factor: 'Equity Risk', var: 1500000, contribution: 10 },
  { factor: 'Commodity Risk', var: 500000, contribution: 3 },
  { factor: 'Diversification Benefit', var: -950000, contribution: -6 },
];

// Backtesting results
const backtestResults = {
  period: '12 months',
  tradingDays: 252,
  exceedances: 8,
  expectedExceedances: 13,
  status: 'GREEN',
  binomialTest: 'Pass',
  kupiecTest: 'Pass',
};

export default function VaRReport() {
  const [confidenceLevel, setConfidenceLevel] = useState('95');
  const [holdingPeriod, setHoldingPeriod] = useState('1');

  const totalVar95 = varByPortfolio.reduce((sum, p) => sum + p.var95, 0);
  const totalVar99 = varByPortfolio.reduce((sum, p) => sum + p.var99, 0);
  const totalLimit = varByPortfolio.reduce((sum, p) => sum + p.limit, 0);

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Value at Risk Report"
        subtitle="VaR analysis as of January 16, 2025"
        breadcrumbs={[
          { label: 'Risk Dashboard', to: '/admin/treasury/risk-dashboard' },
          { label: 'VaR Report' },
        ]}
        actions={
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        }
      />

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Confidence Level:</span>
              <Select value={confidenceLevel} onValueChange={setConfidenceLevel}>
                <SelectTrigger className="w-24">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="95">95%</SelectItem>
                  <SelectItem value="99">99%</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Holding Period:</span>
              <Select value={holdingPeriod} onValueChange={setHoldingPeriod}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1 Day</SelectItem>
                  <SelectItem value="10">10 Days</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total VaR (95%)</div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(totalVar95)}</div>
            <Progress value={(totalVar95 / totalLimit) * 100} className="mt-2 h-2" />
            <p className="text-xs text-muted-foreground mt-1">
              {((totalVar95 / totalLimit) * 100).toFixed(0)}% of limit
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total VaR (99%)</div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(totalVar99)}</div>
            <Progress value={(totalVar99 / totalLimit) * 100} className="mt-2 h-2" />
            <p className="text-xs text-muted-foreground mt-1">
              {((totalVar99 / totalLimit) * 100).toFixed(0)}% of limit
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Aggregate Limit</div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(totalLimit)}</div>
            <p className="text-xs text-muted-foreground mt-1">Approved by Board</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Backtest Status</div>
            <Badge variant="default" className="bg-green-100 text-green-800 mt-2">
              Green Zone
            </Badge>
            <p className="text-xs text-muted-foreground mt-2">
              {backtestResults.exceedances} exceedances in {backtestResults.period}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analysis Tabs */}
      <Tabs defaultValue="portfolio" className="space-y-4">
        <TabsList>
          <TabsTrigger value="portfolio">By Portfolio</TabsTrigger>
          <TabsTrigger value="riskfactor">By Risk Factor</TabsTrigger>
          <TabsTrigger value="backtest">Backtesting</TabsTrigger>
          <TabsTrigger value="trend">Historical Trend</TabsTrigger>
        </TabsList>

        <TabsContent value="portfolio">
          <Card>
            <CardHeader>
              <CardTitle>VaR by Portfolio</CardTitle>
              <CardDescription>Value at Risk breakdown by portfolio type</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Portfolio</TableHead>
                    <TableHead className="text-right">VaR (95%)</TableHead>
                    <TableHead className="text-right">VaR (99%)</TableHead>
                    <TableHead className="text-right">Limit</TableHead>
                    <TableHead className="text-right">Utilization</TableHead>
                    <TableHead className="text-right">Change</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {varByPortfolio.map((item) => (
                    <TableRow key={item.portfolio}>
                      <TableCell className="font-medium">{item.portfolio}</TableCell>
                      <TableCell className="text-right">{formatCurrency(item.var95)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(item.var99)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(item.limit)}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Progress value={(item.var95 / item.limit) * 100} className="w-20 h-2" />
                          <span className="text-sm">{((item.var95 / item.limit) * 100).toFixed(0)}%</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className={`flex items-center justify-end gap-1 ${item.change >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                          {item.change >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                          {Math.abs(item.change)}%
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="bg-muted/50 font-bold">
                    <TableCell>Total</TableCell>
                    <TableCell className="text-right">{formatCurrency(totalVar95)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(totalVar99)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(totalLimit)}</TableCell>
                    <TableCell className="text-right">{((totalVar95 / totalLimit) * 100).toFixed(0)}%</TableCell>
                    <TableCell></TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="riskfactor">
          <Card>
            <CardHeader>
              <CardTitle>VaR by Risk Factor</CardTitle>
              <CardDescription>Marginal contribution to portfolio VaR</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Risk Factor</TableHead>
                    <TableHead className="text-right">VaR Contribution</TableHead>
                    <TableHead className="text-right">% Contribution</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {varByRiskFactor.map((item) => (
                    <TableRow key={item.factor}>
                      <TableCell className="font-medium">{item.factor}</TableCell>
                      <TableCell className={`text-right ${item.var < 0 ? 'text-green-600' : ''}`}>
                        {item.var < 0 ? '-' : ''}{formatCurrency(Math.abs(item.var))}
                      </TableCell>
                      <TableCell className={`text-right ${item.contribution < 0 ? 'text-green-600' : ''}`}>
                        {item.contribution}%
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="bg-muted/50 font-bold">
                    <TableCell>Net Portfolio VaR</TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(varByRiskFactor.reduce((sum, f) => sum + f.var, 0))}
                    </TableCell>
                    <TableCell className="text-right">100%</TableCell>
                  </TableRow>
                </TableBody>
              </Table>

              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <div className="flex items-start gap-2">
                  <Info className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-blue-900">Diversification Benefit</p>
                    <p className="text-sm text-blue-700 mt-1">
                      The portfolio benefits from {formatCurrency(Math.abs(varByRiskFactor.find(f => f.factor === 'Diversification Benefit')?.var || 0))}
                      diversification benefit due to imperfect correlation between risk factors.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="backtest">
          <Card>
            <CardHeader>
              <CardTitle>Backtesting Results</CardTitle>
              <CardDescription>Model validation over the last {backtestResults.period}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-4">Summary Statistics</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between p-3 bg-muted rounded-lg">
                      <span className="text-muted-foreground">Trading Days</span>
                      <span className="font-medium">{backtestResults.tradingDays}</span>
                    </div>
                    <div className="flex justify-between p-3 bg-muted rounded-lg">
                      <span className="text-muted-foreground">Actual Exceedances</span>
                      <span className="font-medium">{backtestResults.exceedances}</span>
                    </div>
                    <div className="flex justify-between p-3 bg-muted rounded-lg">
                      <span className="text-muted-foreground">Expected Exceedances (95%)</span>
                      <span className="font-medium">{backtestResults.expectedExceedances}</span>
                    </div>
                    <div className="flex justify-between p-3 bg-muted rounded-lg">
                      <span className="text-muted-foreground">Zone Status</span>
                      <Badge variant="default" className="bg-green-100 text-green-800">
                        {backtestResults.status}
                      </Badge>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-4">Statistical Tests</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between p-3 bg-muted rounded-lg">
                      <span className="text-muted-foreground">Binomial Test</span>
                      <Badge variant="default" className="bg-green-100 text-green-800">
                        {backtestResults.binomialTest}
                      </Badge>
                    </div>
                    <div className="flex justify-between p-3 bg-muted rounded-lg">
                      <span className="text-muted-foreground">Kupiec Test</span>
                      <Badge variant="default" className="bg-green-100 text-green-800">
                        {backtestResults.kupiecTest}
                      </Badge>
                    </div>
                  </div>

                  <div className="mt-6 p-4 bg-green-50 rounded-lg">
                    <p className="text-sm text-green-800">
                      The VaR model is performing within acceptable parameters.
                      No capital add-on required per Basel III guidelines.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trend">
          <Card>
            <CardHeader>
              <CardTitle>Historical VaR Trend</CardTitle>
              <CardDescription>VaR and actual P&L over time</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">VaR (95%)</TableHead>
                    <TableHead className="text-right">Actual P&L</TableHead>
                    <TableHead className="text-right">Breach</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {varTrend.map((item) => {
                    const isBreach = item.actual > item.var95;
                    return (
                      <TableRow key={item.date}>
                        <TableCell className="font-medium">{item.date}</TableCell>
                        <TableCell className="text-right">{formatCurrency(item.var95)}</TableCell>
                        <TableCell className={`text-right ${item.actual > item.var95 ? 'text-red-600' : ''}`}>
                          {formatCurrency(item.actual)}
                        </TableCell>
                        <TableCell className="text-right">
                          {isBreach ? (
                            <Badge variant="destructive" className="gap-1">
                              <AlertTriangle className="h-3 w-3" />
                              Yes
                            </Badge>
                          ) : (
                            <Badge variant="outline">No</Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
