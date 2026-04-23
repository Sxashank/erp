import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import {
  Shield,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  BarChart3,
  Activity,
  DollarSign,
  Users,
  Building,
  ChevronRight,
  RefreshCw,
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

// Risk metrics
const riskMetrics = {
  marketRisk: {
    var95: 15500000, // Value at Risk at 95% confidence
    var99: 22500000,
    limit: 25000000,
    utilizationPercent: 90,
  },
  creditRisk: {
    expectedLoss: 12500000,
    unexpectedLoss: 35000000,
    ecl: 45000000,
    limit: 50000000,
    utilizationPercent: 90,
  },
  liquidityRisk: {
    lcr: 125, // Liquidity Coverage Ratio
    nsfr: 112, // Net Stable Funding Ratio
    lcrLimit: 100,
    nsfrLimit: 100,
  },
  interestRateRisk: {
    nii: 85000000, // Net Interest Income
    niiAtRisk: 4250000, // NII at risk
    duration: 2.4,
    durationLimit: 3,
  },
  operationalRisk: {
    incidents: 5,
    lossAmount: 250000,
    openIssues: 12,
  },
};

// Risk alerts
const riskAlerts = [
  {
    id: 1,
    type: 'HIGH',
    category: 'Market Risk',
    message: 'VaR utilization at 90% - approaching limit',
    date: '2025-01-16',
  },
  {
    id: 2,
    type: 'MEDIUM',
    category: 'Credit Risk',
    message: 'Credit concentration in real estate sector exceeds 15%',
    date: '2025-01-15',
  },
  {
    id: 3,
    type: 'LOW',
    category: 'Liquidity',
    message: 'Short-term funding gap increased by 5%',
    date: '2025-01-14',
  },
];

// Top risk exposures
const topExposures = [
  { name: 'Real Estate Sector', exposure: 125000000, limit: 150000000, percent: 83 },
  { name: 'Single Counterparty', exposure: 85000000, limit: 100000000, percent: 85 },
  { name: 'Related Party', exposure: 45000000, limit: 60000000, percent: 75 },
  { name: 'Unsecured Lending', exposure: 280000000, limit: 350000000, percent: 80 },
];

export default function RiskDashboard() {
  const [lastUpdate] = useState(new Date().toLocaleString());

  const getAlertBadge = (type: string) => {
    switch (type) {
      case 'HIGH':
        return <Badge variant="destructive">High</Badge>;
      case 'MEDIUM':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Medium</Badge>;
      case 'LOW':
        return <Badge variant="outline">Low</Badge>;
      default:
        return <Badge variant="outline">{type}</Badge>;
    }
  };

  const getUtilizationColor = (percent: number) => {
    if (percent >= 90) return 'text-red-600';
    if (percent >= 75) return 'text-yellow-600';
    return 'text-green-600';
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Risk Dashboard"
        subtitle={`Enterprise risk management overview • Last updated: ${lastUpdate}`}
        actions={
          <Button variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        }
      />

      {/* Risk Alerts */}
      {riskAlerts.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-yellow-800">
              <AlertTriangle className="h-5 w-5" />
              Risk Alerts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {riskAlerts.map((alert) => (
                <div key={alert.id} className="flex items-center justify-between p-3 bg-white rounded-lg">
                  <div className="flex items-center gap-3">
                    {getAlertBadge(alert.type)}
                    <div>
                      <p className="font-medium text-sm">{alert.message}</p>
                      <p className="text-xs text-muted-foreground">{alert.category} • {alert.date}</p>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm">
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Key Risk Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <BarChart3 className="h-4 w-4" />
                Market VaR (95%)
              </div>
              <Badge variant="outline" className={getUtilizationColor(riskMetrics.marketRisk.utilizationPercent)}>
                {riskMetrics.marketRisk.utilizationPercent}%
              </Badge>
            </div>
            <div className="text-2xl font-bold mt-2">
              {formatCurrency(riskMetrics.marketRisk.var95)}
            </div>
            <Progress value={riskMetrics.marketRisk.utilizationPercent} className="mt-2 h-2" />
            <p className="text-xs text-muted-foreground mt-1">
              Limit: {formatCurrency(riskMetrics.marketRisk.limit)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <DollarSign className="h-4 w-4" />
                Expected Credit Loss
              </div>
              <Badge variant="outline" className={getUtilizationColor(riskMetrics.creditRisk.utilizationPercent)}>
                {riskMetrics.creditRisk.utilizationPercent}%
              </Badge>
            </div>
            <div className="text-2xl font-bold mt-2">
              {formatCurrency(riskMetrics.creditRisk.ecl)}
            </div>
            <Progress value={riskMetrics.creditRisk.utilizationPercent} className="mt-2 h-2" />
            <p className="text-xs text-muted-foreground mt-1">
              Limit: {formatCurrency(riskMetrics.creditRisk.limit)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Activity className="h-4 w-4" />
              Liquidity Coverage Ratio
            </div>
            <div className="text-2xl font-bold mt-2 flex items-center gap-2">
              {riskMetrics.liquidityRisk.lcr}%
              <TrendingUp className="h-4 w-4 text-green-500" />
            </div>
            <p className="text-sm text-green-600 mt-1">Above regulatory minimum</p>
            <p className="text-xs text-muted-foreground">
              Minimum required: {riskMetrics.liquidityRisk.lcrLimit}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <TrendingUp className="h-4 w-4" />
              NII at Risk
            </div>
            <div className="text-2xl font-bold mt-2">
              {formatCurrency(riskMetrics.interestRateRisk.niiAtRisk)}
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              {((riskMetrics.interestRateRisk.niiAtRisk / riskMetrics.interestRateRisk.nii) * 100).toFixed(1)}% of NII
            </p>
            <p className="text-xs text-muted-foreground">
              Duration: {riskMetrics.interestRateRisk.duration} years
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Risk Category Tabs */}
      <Tabs defaultValue="exposure" className="space-y-4">
        <TabsList>
          <TabsTrigger value="exposure">Concentration Risk</TabsTrigger>
          <TabsTrigger value="liquidity">Liquidity</TabsTrigger>
          <TabsTrigger value="interest">Interest Rate</TabsTrigger>
          <TabsTrigger value="operational">Operational</TabsTrigger>
        </TabsList>

        <TabsContent value="exposure">
          <Card>
            <CardHeader>
              <CardTitle>Top Risk Exposures</CardTitle>
              <CardDescription>Concentration limits and utilization</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {topExposures.map((item, index) => (
                  <div key={index} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{item.name}</span>
                      <span className={`font-bold ${getUtilizationColor(item.percent)}`}>
                        {item.percent}%
                      </span>
                    </div>
                    <Progress value={item.percent} className="h-2" />
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>Exposure: {formatCurrency(item.exposure)}</span>
                      <span>Limit: {formatCurrency(item.limit)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="liquidity">
          <Card>
            <CardHeader>
              <CardTitle>Liquidity Metrics</CardTitle>
              <CardDescription>Regulatory ratios and funding position</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="font-medium">Liquidity Coverage Ratio (LCR)</h4>
                  <div className="flex items-center gap-4">
                    <div className="h-24 w-24 rounded-full border-8 border-green-500 flex items-center justify-center">
                      <span className="text-2xl font-bold">{riskMetrics.liquidityRisk.lcr}%</span>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Minimum required: 100%</p>
                      <Badge variant="default" className="bg-green-100 text-green-800 mt-2">
                        Compliant
                      </Badge>
                    </div>
                  </div>
                </div>
                <div className="space-y-4">
                  <h4 className="font-medium">Net Stable Funding Ratio (NSFR)</h4>
                  <div className="flex items-center gap-4">
                    <div className="h-24 w-24 rounded-full border-8 border-green-500 flex items-center justify-center">
                      <span className="text-2xl font-bold">{riskMetrics.liquidityRisk.nsfr}%</span>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Minimum required: 100%</p>
                      <Badge variant="default" className="bg-green-100 text-green-800 mt-2">
                        Compliant
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="interest">
          <Card>
            <CardHeader>
              <CardTitle>Interest Rate Risk</CardTitle>
              <CardDescription>Banking book interest rate risk metrics</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-4 bg-muted rounded-lg text-center">
                  <p className="text-sm text-muted-foreground">Net Interest Income</p>
                  <p className="text-2xl font-bold mt-2">{formatCurrency(riskMetrics.interestRateRisk.nii)}</p>
                </div>
                <div className="p-4 bg-muted rounded-lg text-center">
                  <p className="text-sm text-muted-foreground">NII at Risk (100bps)</p>
                  <p className="text-2xl font-bold mt-2">{formatCurrency(riskMetrics.interestRateRisk.niiAtRisk)}</p>
                </div>
                <div className="p-4 bg-muted rounded-lg text-center">
                  <p className="text-sm text-muted-foreground">Modified Duration</p>
                  <p className="text-2xl font-bold mt-2">{riskMetrics.interestRateRisk.duration} years</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="operational">
          <Card>
            <CardHeader>
              <CardTitle>Operational Risk</CardTitle>
              <CardDescription>Incidents and control issues</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-4 bg-muted rounded-lg text-center">
                  <p className="text-sm text-muted-foreground">Open Incidents (MTD)</p>
                  <p className="text-2xl font-bold mt-2">{riskMetrics.operationalRisk.incidents}</p>
                </div>
                <div className="p-4 bg-muted rounded-lg text-center">
                  <p className="text-sm text-muted-foreground">Loss Amount (MTD)</p>
                  <p className="text-2xl font-bold mt-2">{formatCurrency(riskMetrics.operationalRisk.lossAmount)}</p>
                </div>
                <div className="p-4 bg-muted rounded-lg text-center">
                  <p className="text-sm text-muted-foreground">Open Control Issues</p>
                  <p className="text-2xl font-bold mt-2">{riskMetrics.operationalRisk.openIssues}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Quick Links */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Link to="/admin/treasury/var-report">
          <Card className="hover:bg-muted/50 cursor-pointer transition-colors">
            <CardContent className="pt-6">
              <BarChart3 className="h-8 w-8 text-primary mb-2" />
              <h3 className="font-medium">VaR Report</h3>
              <p className="text-sm text-muted-foreground">Detailed Value at Risk analysis</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/admin/treasury/liquidity-risk">
          <Card className="hover:bg-muted/50 cursor-pointer transition-colors">
            <CardContent className="pt-6">
              <Activity className="h-8 w-8 text-primary mb-2" />
              <h3 className="font-medium">Liquidity Risk</h3>
              <p className="text-sm text-muted-foreground">Cash flow projections</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/admin/treasury/counterparty-risk">
          <Card className="hover:bg-muted/50 cursor-pointer transition-colors">
            <CardContent className="pt-6">
              <Users className="h-8 w-8 text-primary mb-2" />
              <h3 className="font-medium">Counterparty Risk</h3>
              <p className="text-sm text-muted-foreground">Exposure monitoring</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/admin/treasury/stress-test">
          <Card className="hover:bg-muted/50 cursor-pointer transition-colors">
            <CardContent className="pt-6">
              <AlertTriangle className="h-8 w-8 text-primary mb-2" />
              <h3 className="font-medium">Stress Testing</h3>
              <p className="text-sm text-muted-foreground">Scenario analysis</p>
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}
