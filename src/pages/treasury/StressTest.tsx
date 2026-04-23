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
import {
  ArrowLeft,
  AlertTriangle,
  TrendingDown,
  BarChart3,
  Play,
  Download,
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

// Predefined stress scenarios
const stressScenarios = [
  {
    id: 'mild',
    name: 'Mild Stress',
    description: 'Economic slowdown with 10% credit deterioration',
    assumptions: {
      interestRateShock: 50, // bps
      creditLoss: 10, // %
      liquidityStress: 15, // %
      marketDecline: 5, // %
    },
  },
  {
    id: 'moderate',
    name: 'Moderate Stress',
    description: 'Recession scenario with significant asset quality deterioration',
    assumptions: {
      interestRateShock: 100,
      creditLoss: 25,
      liquidityStress: 30,
      marketDecline: 15,
    },
  },
  {
    id: 'severe',
    name: 'Severe Stress',
    description: 'Global financial crisis type scenario',
    assumptions: {
      interestRateShock: 200,
      creditLoss: 50,
      liquidityStress: 50,
      marketDecline: 30,
    },
  },
];

// Stress test results
const stressResults = {
  mild: {
    capitalRatio: { base: 18.5, stressed: 16.2, change: -2.3, minimum: 11.5, compliant: true },
    nii: { base: 85000000, stressed: 78500000, change: -7.6 },
    npa: { base: 2.5, stressed: 4.2, change: 1.7 },
    lcr: { base: 125, stressed: 110, change: -15, minimum: 100, compliant: true },
    profit: { base: 45000000, stressed: 32000000, change: -28.9 },
  },
  moderate: {
    capitalRatio: { base: 18.5, stressed: 13.8, change: -4.7, minimum: 11.5, compliant: true },
    nii: { base: 85000000, stressed: 68000000, change: -20 },
    npa: { base: 2.5, stressed: 8.5, change: 6.0 },
    lcr: { base: 125, stressed: 95, change: -30, minimum: 100, compliant: false },
    profit: { base: 45000000, stressed: 12000000, change: -73.3 },
  },
  severe: {
    capitalRatio: { base: 18.5, stressed: 10.2, change: -8.3, minimum: 11.5, compliant: false },
    nii: { base: 85000000, stressed: 51000000, change: -40 },
    npa: { base: 2.5, stressed: 15.0, change: 12.5 },
    lcr: { base: 125, stressed: 72, change: -53, minimum: 100, compliant: false },
    profit: { base: 45000000, stressed: -25000000, change: -155.6 },
  },
};

// Historical stress test runs
const stressHistory = [
  { date: '2025-01-15', scenario: 'Moderate Stress', capital: 13.8, lcr: 95, status: 'Completed' },
  { date: '2025-01-01', scenario: 'Severe Stress', capital: 10.5, lcr: 75, status: 'Completed' },
  { date: '2024-12-15', scenario: 'Mild Stress', capital: 16.5, lcr: 112, status: 'Completed' },
  { date: '2024-12-01', scenario: 'Moderate Stress', capital: 14.2, lcr: 98, status: 'Completed' },
];

export default function StressTest() {
  const [selectedScenario, setSelectedScenario] = useState('moderate');
  const [isRunning, setIsRunning] = useState(false);

  const currentScenario = stressScenarios.find(s => s.id === selectedScenario);
  const results = stressResults[selectedScenario as keyof typeof stressResults];

  const runStressTest = () => {
    setIsRunning(true);
    setTimeout(() => setIsRunning(false), 2000);
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Stress Testing"
        subtitle="Scenario-based stress testing and capital adequacy analysis"
        breadcrumbs={[
          { label: 'Risk Dashboard', to: '/admin/treasury/risk-dashboard' },
          { label: 'Stress Testing' },
        ]}
        actions={
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
        }
      />

      {/* Scenario Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Select Stress Scenario</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-4">
            <Select value={selectedScenario} onValueChange={setSelectedScenario}>
              <SelectTrigger className="w-64">
                <SelectValue placeholder="Select scenario" />
              </SelectTrigger>
              <SelectContent>
                {stressScenarios.map((scenario) => (
                  <SelectItem key={scenario.id} value={scenario.id}>
                    {scenario.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button onClick={runStressTest} disabled={isRunning}>
              {isRunning ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Run Stress Test
                </>
              )}
            </Button>
          </div>

          {currentScenario && (
            <div className="mt-4 p-4 bg-muted rounded-lg">
              <p className="font-medium">{currentScenario.name}</p>
              <p className="text-sm text-muted-foreground mt-1">{currentScenario.description}</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                <div>
                  <p className="text-xs text-muted-foreground">Interest Rate Shock</p>
                  <p className="font-medium">+{currentScenario.assumptions.interestRateShock} bps</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Credit Loss Increase</p>
                  <p className="font-medium">+{currentScenario.assumptions.creditLoss}%</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Liquidity Stress</p>
                  <p className="font-medium">-{currentScenario.assumptions.liquidityStress}%</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Market Decline</p>
                  <p className="font-medium">-{currentScenario.assumptions.marketDecline}%</p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results Summary */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Capital Ratio</div>
            <div className={`text-2xl font-bold mt-1 ${results.capitalRatio.compliant ? 'text-green-600' : 'text-red-600'}`}>
              {results.capitalRatio.stressed}%
            </div>
            <div className="flex items-center gap-1 text-sm text-red-500">
              <TrendingDown className="h-3 w-3" />
              {results.capitalRatio.change}%
            </div>
            <Badge variant={results.capitalRatio.compliant ? 'default' : 'destructive'} className="mt-2">
              {results.capitalRatio.compliant ? 'Compliant' : 'Breach'}
            </Badge>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">LCR</div>
            <div className={`text-2xl font-bold mt-1 ${results.lcr.compliant ? 'text-green-600' : 'text-red-600'}`}>
              {results.lcr.stressed}%
            </div>
            <div className="flex items-center gap-1 text-sm text-red-500">
              <TrendingDown className="h-3 w-3" />
              {results.lcr.change}%
            </div>
            <Badge variant={results.lcr.compliant ? 'default' : 'destructive'} className="mt-2">
              {results.lcr.compliant ? 'Compliant' : 'Breach'}
            </Badge>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Stressed NPA</div>
            <div className="text-2xl font-bold mt-1 text-red-600">{results.npa.stressed}%</div>
            <div className="flex items-center gap-1 text-sm text-red-500">
              +{results.npa.change}%
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Stressed NII</div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(results.nii.stressed)}</div>
            <div className="flex items-center gap-1 text-sm text-red-500">
              <TrendingDown className="h-3 w-3" />
              {results.nii.change}%
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Stressed Profit</div>
            <div className={`text-2xl font-bold mt-1 ${results.profit.stressed >= 0 ? '' : 'text-red-600'}`}>
              {formatCurrency(results.profit.stressed)}
            </div>
            <div className="flex items-center gap-1 text-sm text-red-500">
              <TrendingDown className="h-3 w-3" />
              {Math.abs(results.profit.change)}%
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Results */}
      <Tabs defaultValue="comparison" className="space-y-4">
        <TabsList>
          <TabsTrigger value="comparison">Base vs Stressed</TabsTrigger>
          <TabsTrigger value="sensitivity">Sensitivity Analysis</TabsTrigger>
          <TabsTrigger value="history">Historical Runs</TabsTrigger>
        </TabsList>

        <TabsContent value="comparison">
          <Card>
            <CardHeader>
              <CardTitle>Base Case vs Stressed Comparison</CardTitle>
              <CardDescription>Impact analysis for {currentScenario?.name}</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Metric</TableHead>
                    <TableHead className="text-right">Base Case</TableHead>
                    <TableHead className="text-right">Stressed</TableHead>
                    <TableHead className="text-right">Change</TableHead>
                    <TableHead className="text-right">Minimum</TableHead>
                    <TableHead className="text-center">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell className="font-medium">Capital Adequacy Ratio</TableCell>
                    <TableCell className="text-right">{results.capitalRatio.base}%</TableCell>
                    <TableCell className="text-right font-bold">{results.capitalRatio.stressed}%</TableCell>
                    <TableCell className="text-right text-red-500">{results.capitalRatio.change}%</TableCell>
                    <TableCell className="text-right">{results.capitalRatio.minimum}%</TableCell>
                    <TableCell className="text-center">
                      <Badge variant={results.capitalRatio.compliant ? 'default' : 'destructive'}>
                        {results.capitalRatio.compliant ? 'Pass' : 'Fail'}
                      </Badge>
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">Liquidity Coverage Ratio</TableCell>
                    <TableCell className="text-right">{results.lcr.base}%</TableCell>
                    <TableCell className="text-right font-bold">{results.lcr.stressed}%</TableCell>
                    <TableCell className="text-right text-red-500">{results.lcr.change}%</TableCell>
                    <TableCell className="text-right">{results.lcr.minimum}%</TableCell>
                    <TableCell className="text-center">
                      <Badge variant={results.lcr.compliant ? 'default' : 'destructive'}>
                        {results.lcr.compliant ? 'Pass' : 'Fail'}
                      </Badge>
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">Net Interest Income</TableCell>
                    <TableCell className="text-right">{formatCurrency(results.nii.base)}</TableCell>
                    <TableCell className="text-right font-bold">{formatCurrency(results.nii.stressed)}</TableCell>
                    <TableCell className="text-right text-red-500">{results.nii.change}%</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-center">-</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">Gross NPA Ratio</TableCell>
                    <TableCell className="text-right">{results.npa.base}%</TableCell>
                    <TableCell className="text-right font-bold">{results.npa.stressed}%</TableCell>
                    <TableCell className="text-right text-red-500">+{results.npa.change}%</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-center">-</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">Net Profit</TableCell>
                    <TableCell className="text-right">{formatCurrency(results.profit.base)}</TableCell>
                    <TableCell className={`text-right font-bold ${results.profit.stressed < 0 ? 'text-red-600' : ''}`}>
                      {formatCurrency(results.profit.stressed)}
                    </TableCell>
                    <TableCell className="text-right text-red-500">{results.profit.change}%</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-center">-</TableCell>
                  </TableRow>
                </TableBody>
              </Table>

              {!results.capitalRatio.compliant || !results.lcr.compliant ? (
                <div className="mt-6 p-4 bg-red-50 rounded-lg">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-red-800">Regulatory Breach Warning</p>
                      <p className="text-sm text-red-700 mt-1">
                        Under the {currentScenario?.name.toLowerCase()} scenario, regulatory minimums would be breached.
                        Management action and contingency plans should be reviewed.
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="mt-6 p-4 bg-green-50 rounded-lg">
                  <p className="text-sm text-green-800">
                    All regulatory ratios remain compliant under the {currentScenario?.name.toLowerCase()} scenario.
                    Capital buffers are sufficient to absorb stressed losses.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sensitivity">
          <Card>
            <CardHeader>
              <CardTitle>Sensitivity Analysis</CardTitle>
              <CardDescription>Impact of key risk factors on capital ratio</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Risk Factor</TableHead>
                    <TableHead className="text-right">+50 bps</TableHead>
                    <TableHead className="text-right">+100 bps</TableHead>
                    <TableHead className="text-right">+150 bps</TableHead>
                    <TableHead className="text-right">+200 bps</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell className="font-medium">Interest Rate Shock</TableCell>
                    <TableCell className="text-right">17.8%</TableCell>
                    <TableCell className="text-right">17.2%</TableCell>
                    <TableCell className="text-right">16.5%</TableCell>
                    <TableCell className="text-right">15.8%</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">Credit Loss (+% of NPA)</TableCell>
                    <TableCell className="text-right">18.0%</TableCell>
                    <TableCell className="text-right">17.5%</TableCell>
                    <TableCell className="text-right">17.0%</TableCell>
                    <TableCell className="text-right">16.5%</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">Market Value Decline</TableCell>
                    <TableCell className="text-right">18.2%</TableCell>
                    <TableCell className="text-right">17.9%</TableCell>
                    <TableCell className="text-right">17.6%</TableCell>
                    <TableCell className="text-right">17.3%</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">Operational Loss</TableCell>
                    <TableCell className="text-right">18.4%</TableCell>
                    <TableCell className="text-right">18.3%</TableCell>
                    <TableCell className="text-right">18.2%</TableCell>
                    <TableCell className="text-right">18.1%</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>Historical Stress Test Runs</CardTitle>
              <CardDescription>Previous stress test executions and results</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Run Date</TableHead>
                    <TableHead>Scenario</TableHead>
                    <TableHead className="text-right">Capital Ratio</TableHead>
                    <TableHead className="text-right">LCR</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {stressHistory.map((run, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium">{run.date}</TableCell>
                      <TableCell>{run.scenario}</TableCell>
                      <TableCell className={`text-right ${run.capital < 11.5 ? 'text-red-600' : ''}`}>
                        {run.capital}%
                      </TableCell>
                      <TableCell className={`text-right ${run.lcr < 100 ? 'text-red-600' : ''}`}>
                        {run.lcr}%
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{run.status}</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
