import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  TrendingDown,
  Calculator,
  Calendar,
  Download,
  RefreshCw,
  AlertTriangle,
  ArrowUp,
  ArrowDown,
  Info,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { formatCurrency, formatDate } from '@/lib/utils';

// Types
interface RateSensitivityBucket {
  bucket: string;
  bucket_label: string;
  rsa: number; // Rate Sensitive Assets
  rsl: number; // Rate Sensitive Liabilities
  gap: number;
  cumulative_gap: number;
}

interface NIIImpact {
  shock_bps: number;
  shock_label: string;
  nii_impact: number;
  nii_impact_percent: number;
  capital_impact_percent: number;
}

interface IRSAnalysis {
  analysis_date: string;
  rate_sensitive_assets: number;
  rate_sensitive_liabilities: number;
  rate_sensitivity_gap: number;
  gap_percent: number;
  current_nii: number;
  buckets: RateSensitivityBucket[];
  nii_impacts: NIIImpact[];
}

// Mock data
const irsAnalysis: IRSAnalysis = {
  analysis_date: '2024-12-31',
  rate_sensitive_assets: 3500000000,
  rate_sensitive_liabilities: 3200000000,
  rate_sensitivity_gap: 300000000,
  gap_percent: 9.38,
  current_nii: 450000000,
  buckets: [
    {
      bucket: 'DAYS_1_28',
      bucket_label: '1-28 Days',
      rsa: 400000000,
      rsl: 450000000,
      gap: -50000000,
      cumulative_gap: -50000000,
    },
    {
      bucket: 'DAYS_29_3M',
      bucket_label: '29 Days - 3 Months',
      rsa: 600000000,
      rsl: 700000000,
      gap: -100000000,
      cumulative_gap: -150000000,
    },
    {
      bucket: 'MONTHS_3_6',
      bucket_label: '3-6 Months',
      rsa: 800000000,
      rsl: 650000000,
      gap: 150000000,
      cumulative_gap: 0,
    },
    {
      bucket: 'MONTHS_6_12',
      bucket_label: '6-12 Months',
      rsa: 900000000,
      rsl: 700000000,
      gap: 200000000,
      cumulative_gap: 200000000,
    },
    {
      bucket: 'YEARS_1_3',
      bucket_label: '1-3 Years',
      rsa: 500000000,
      rsl: 450000000,
      gap: 50000000,
      cumulative_gap: 250000000,
    },
    {
      bucket: 'OVER_3_YEARS',
      bucket_label: 'Over 3 Years',
      rsa: 300000000,
      rsl: 250000000,
      gap: 50000000,
      cumulative_gap: 300000000,
    },
  ],
  nii_impacts: [
    {
      shock_bps: -100,
      shock_label: '-100 bps',
      nii_impact: -30000000,
      nii_impact_percent: -6.67,
      capital_impact_percent: -0.5,
    },
    {
      shock_bps: -50,
      shock_label: '-50 bps',
      nii_impact: -15000000,
      nii_impact_percent: -3.33,
      capital_impact_percent: -0.25,
    },
    {
      shock_bps: 50,
      shock_label: '+50 bps',
      nii_impact: 15000000,
      nii_impact_percent: 3.33,
      capital_impact_percent: 0.25,
    },
    {
      shock_bps: 100,
      shock_label: '+100 bps',
      nii_impact: 30000000,
      nii_impact_percent: 6.67,
      capital_impact_percent: 0.5,
    },
    {
      shock_bps: 200,
      shock_label: '+200 bps',
      nii_impact: 60000000,
      nii_impact_percent: 13.33,
      capital_impact_percent: 1.0,
    },
  ],
};

const portfolioBreakdown = {
  assets: {
    floating_rate: 2800000000,
    fixed_rate: 1500000000,
    mclr_linked: 1200000000,
    repo_linked: 600000000,
    eblr_linked: 400000000,
  },
  liabilities: {
    floating_rate: 2500000000,
    fixed_rate: 1200000000,
    cp_cd: 500000000,
  },
};

export default function InterestRateRisk() {
  const navigate = useNavigate();
  const [shockBps, setShockBps] = useState('100');
  const [analysisDate, setAnalysisDate] = useState('2024-12-31');

  const isAssetSensitive = irsAnalysis.rate_sensitivity_gap > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Interest Rate Risk Analysis</h1>
          <p className="text-muted-foreground">
            Rate sensitivity analysis and NII impact assessment
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Run Analysis
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Rate Sensitive Assets
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(irsAnalysis.rate_sensitive_assets)}
            </div>
            <p className="text-xs text-muted-foreground">Repricing within 1 year</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Rate Sensitive Liabilities
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(irsAnalysis.rate_sensitive_liabilities)}
            </div>
            <p className="text-xs text-muted-foreground">Repricing within 1 year</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Rate Sensitivity Gap
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className={`text-2xl font-bold ${
                isAssetSensitive ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {formatCurrency(irsAnalysis.rate_sensitivity_gap)}
            </div>
            <div className="flex items-center gap-1">
              {isAssetSensitive ? (
                <Badge variant="secondary" className="bg-green-100 text-green-800">
                  Asset Sensitive
                </Badge>
              ) : (
                <Badge variant="secondary" className="bg-red-100 text-red-800">
                  Liability Sensitive
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Current NII
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(irsAnalysis.current_nii)}</div>
            <p className="text-xs text-muted-foreground">Annualized</p>
          </CardContent>
        </Card>
      </div>

      {/* Position Interpretation */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>Interest Rate Position</AlertTitle>
        <AlertDescription>
          {isAssetSensitive ? (
            <>
              Your portfolio is <strong>asset sensitive</strong> (RSA &gt; RSL). This means:
              <ul className="list-disc ml-4 mt-2">
                <li>Rising rates will increase Net Interest Income (NII)</li>
                <li>Falling rates will decrease NII</li>
                <li>Gap represents {irsAnalysis.gap_percent.toFixed(2)}% of rate sensitive liabilities</li>
              </ul>
            </>
          ) : (
            <>
              Your portfolio is <strong>liability sensitive</strong> (RSL &gt; RSA). This means:
              <ul className="list-disc ml-4 mt-2">
                <li>Rising rates will decrease Net Interest Income (NII)</li>
                <li>Falling rates will increase NII</li>
                <li>Gap represents {Math.abs(irsAnalysis.gap_percent).toFixed(2)}% of rate sensitive liabilities</li>
              </ul>
            </>
          )}
        </AlertDescription>
      </Alert>

      <Tabs defaultValue="gap" className="space-y-4">
        <TabsList>
          <TabsTrigger value="gap">Gap Analysis</TabsTrigger>
          <TabsTrigger value="impact">NII Impact</TabsTrigger>
          <TabsTrigger value="portfolio">Portfolio Breakdown</TabsTrigger>
        </TabsList>

        <TabsContent value="gap" className="space-y-4">
          {/* Rate Sensitivity Gap by Bucket */}
          <Card>
            <CardHeader>
              <CardTitle>Rate Sensitivity Gap by Repricing Bucket</CardTitle>
              <CardDescription>
                Analysis Date: {formatDate(irsAnalysis.analysis_date)}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Repricing Bucket</TableHead>
                    <TableHead className="text-right">RSA</TableHead>
                    <TableHead className="text-right">RSL</TableHead>
                    <TableHead className="text-right">Gap</TableHead>
                    <TableHead className="text-right">Cumulative Gap</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {irsAnalysis.buckets.map((bucket) => (
                    <TableRow key={bucket.bucket}>
                      <TableCell className="font-medium">{bucket.bucket_label}</TableCell>
                      <TableCell className="text-right">{formatCurrency(bucket.rsa)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(bucket.rsl)}</TableCell>
                      <TableCell
                        className={`text-right font-medium ${
                          bucket.gap < 0 ? 'text-red-600' : 'text-green-600'
                        }`}
                      >
                        {bucket.gap < 0 ? '' : '+'}
                        {formatCurrency(bucket.gap)}
                      </TableCell>
                      <TableCell
                        className={`text-right font-medium ${
                          bucket.cumulative_gap < 0 ? 'text-red-600' : 'text-green-600'
                        }`}
                      >
                        {bucket.cumulative_gap < 0 ? '' : '+'}
                        {formatCurrency(bucket.cumulative_gap)}
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="font-bold bg-muted/50">
                    <TableCell>Total</TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(irsAnalysis.rate_sensitive_assets)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(irsAnalysis.rate_sensitive_liabilities)}
                    </TableCell>
                    <TableCell
                      className={`text-right ${
                        irsAnalysis.rate_sensitivity_gap < 0 ? 'text-red-600' : 'text-green-600'
                      }`}
                    >
                      {formatCurrency(irsAnalysis.rate_sensitivity_gap)}
                    </TableCell>
                    <TableCell></TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="impact" className="space-y-4">
          {/* NII Impact Analysis */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calculator className="h-5 w-5" />
                NII Impact under Rate Shocks
              </CardTitle>
              <CardDescription>
                Estimated impact on Net Interest Income for various rate scenarios
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Rate Shock</TableHead>
                    <TableHead className="text-right">NII Impact</TableHead>
                    <TableHead className="text-right">% of Current NII</TableHead>
                    <TableHead className="text-right">Capital Impact %</TableHead>
                    <TableHead>Direction</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {irsAnalysis.nii_impacts.map((impact) => (
                    <TableRow key={impact.shock_bps}>
                      <TableCell className="font-medium">{impact.shock_label}</TableCell>
                      <TableCell
                        className={`text-right font-medium ${
                          impact.nii_impact < 0 ? 'text-red-600' : 'text-green-600'
                        }`}
                      >
                        {impact.nii_impact < 0 ? '' : '+'}
                        {formatCurrency(impact.nii_impact)}
                      </TableCell>
                      <TableCell
                        className={`text-right ${
                          impact.nii_impact_percent < 0 ? 'text-red-600' : 'text-green-600'
                        }`}
                      >
                        {impact.nii_impact_percent > 0 ? '+' : ''}
                        {impact.nii_impact_percent.toFixed(2)}%
                      </TableCell>
                      <TableCell
                        className={`text-right ${
                          impact.capital_impact_percent < 0 ? 'text-red-600' : 'text-green-600'
                        }`}
                      >
                        {impact.capital_impact_percent > 0 ? '+' : ''}
                        {impact.capital_impact_percent.toFixed(2)}%
                      </TableCell>
                      <TableCell>
                        {impact.nii_impact < 0 ? (
                          <div className="flex items-center text-red-600">
                            <TrendingDown className="h-4 w-4 mr-1" />
                            Decrease
                          </div>
                        ) : (
                          <div className="flex items-center text-green-600">
                            <TrendingUp className="h-4 w-4 mr-1" />
                            Increase
                          </div>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Custom Shock Calculator */}
          <Card>
            <CardHeader>
              <CardTitle>Custom Rate Shock Calculator</CardTitle>
              <CardDescription>Calculate NII impact for custom rate change</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-end gap-4">
                <div className="flex-1 max-w-xs">
                  <Label htmlFor="shockBps">Rate Shock (basis points)</Label>
                  <Input
                    id="shockBps"
                    type="number"
                    value={shockBps}
                    onChange={(e) => setShockBps(e.target.value)}
                    placeholder="e.g., 100 or -50"
                  />
                </div>
                <Button>
                  <Calculator className="h-4 w-4 mr-2" />
                  Calculate Impact
                </Button>
              </div>

              {shockBps && (
                <div className="mt-6 grid grid-cols-3 gap-4">
                  <Card className="bg-muted/50">
                    <CardContent className="pt-4">
                      <div className="text-sm text-muted-foreground">Rate Change</div>
                      <div className="text-2xl font-bold">
                        {Number(shockBps) > 0 ? '+' : ''}
                        {shockBps} bps
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="bg-muted/50">
                    <CardContent className="pt-4">
                      <div className="text-sm text-muted-foreground">Estimated NII Impact</div>
                      <div
                        className={`text-2xl font-bold ${
                          Number(shockBps) * (isAssetSensitive ? 1 : -1) > 0
                            ? 'text-green-600'
                            : 'text-red-600'
                        }`}
                      >
                        {formatCurrency(
                          irsAnalysis.rate_sensitivity_gap * (Number(shockBps) / 10000)
                        )}
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="bg-muted/50">
                    <CardContent className="pt-4">
                      <div className="text-sm text-muted-foreground">% of Current NII</div>
                      <div
                        className={`text-2xl font-bold ${
                          Number(shockBps) * (isAssetSensitive ? 1 : -1) > 0
                            ? 'text-green-600'
                            : 'text-red-600'
                        }`}
                      >
                        {(
                          (irsAnalysis.rate_sensitivity_gap * (Number(shockBps) / 10000) /
                            irsAnalysis.current_nii) *
                          100
                        ).toFixed(2)}
                        %
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="portfolio" className="space-y-4">
          {/* Portfolio Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Asset Rate Profile</CardTitle>
                <CardDescription>Breakdown by rate type</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span>Floating Rate</span>
                    <span className="font-medium">
                      {formatCurrency(portfolioBreakdown.assets.floating_rate)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Fixed Rate</span>
                    <span className="font-medium">
                      {formatCurrency(portfolioBreakdown.assets.fixed_rate)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-muted-foreground text-sm">
                    <span className="ml-4">- MCLR Linked</span>
                    <span>{formatCurrency(portfolioBreakdown.assets.mclr_linked)}</span>
                  </div>
                  <div className="flex items-center justify-between text-muted-foreground text-sm">
                    <span className="ml-4">- Repo Linked</span>
                    <span>{formatCurrency(portfolioBreakdown.assets.repo_linked)}</span>
                  </div>
                  <div className="flex items-center justify-between text-muted-foreground text-sm">
                    <span className="ml-4">- EBLR Linked</span>
                    <span>{formatCurrency(portfolioBreakdown.assets.eblr_linked)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Liability Rate Profile</CardTitle>
                <CardDescription>Breakdown by rate type</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span>Floating Rate Borrowings</span>
                    <span className="font-medium">
                      {formatCurrency(portfolioBreakdown.liabilities.floating_rate)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Fixed Rate Borrowings</span>
                    <span className="font-medium">
                      {formatCurrency(portfolioBreakdown.liabilities.fixed_rate)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Commercial Paper / CD</span>
                    <span className="font-medium">
                      {formatCurrency(portfolioBreakdown.liabilities.cp_cd)}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
