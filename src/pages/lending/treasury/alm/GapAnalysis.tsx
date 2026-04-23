import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowUpDown,
  Calendar,
  Download,
  RefreshCw,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  BarChart3,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
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
import { Progress } from '@/components/ui/progress';
import { formatCurrency, formatDate } from '@/lib/utils';

// Types
interface GapBucket {
  bucket: string;
  bucket_label: string;
  days_from: number;
  days_to: number;
  assets: number;
  liabilities: number;
  gap: number;
  cumulative_gap: number;
  gap_percent: number;
  cumulative_gap_percent: number;
}

interface ALMPosition {
  position_date: string;
  total_assets: number;
  total_liabilities: number;
  net_position: number;
  cumulative_gap_1_year: number;
  cumulative_gap_percent: number;
  buckets: GapBucket[];
}

// Mock data
const almPosition: ALMPosition = {
  position_date: '2024-12-31',
  total_assets: 5000000000,
  total_liabilities: 4200000000,
  net_position: 800000000,
  cumulative_gap_1_year: -150000000,
  cumulative_gap_percent: -3.57,
  buckets: [
    {
      bucket: 'DAY_1',
      bucket_label: '1 Day',
      days_from: 1,
      days_to: 1,
      assets: 150000000,
      liabilities: 100000000,
      gap: 50000000,
      cumulative_gap: 50000000,
      gap_percent: 1.19,
      cumulative_gap_percent: 1.19,
    },
    {
      bucket: 'DAYS_2_7',
      bucket_label: '2-7 Days',
      days_from: 2,
      days_to: 7,
      assets: 200000000,
      liabilities: 180000000,
      gap: 20000000,
      cumulative_gap: 70000000,
      gap_percent: 0.48,
      cumulative_gap_percent: 1.67,
    },
    {
      bucket: 'DAYS_8_14',
      bucket_label: '8-14 Days',
      days_from: 8,
      days_to: 14,
      assets: 180000000,
      liabilities: 250000000,
      gap: -70000000,
      cumulative_gap: 0,
      gap_percent: -1.67,
      cumulative_gap_percent: 0,
    },
    {
      bucket: 'DAYS_15_28',
      bucket_label: '15-28 Days',
      days_from: 15,
      days_to: 28,
      assets: 220000000,
      liabilities: 280000000,
      gap: -60000000,
      cumulative_gap: -60000000,
      gap_percent: -1.43,
      cumulative_gap_percent: -1.43,
    },
    {
      bucket: 'DAYS_29_3M',
      bucket_label: '29 Days - 3 Months',
      days_from: 29,
      days_to: 90,
      assets: 450000000,
      liabilities: 520000000,
      gap: -70000000,
      cumulative_gap: -130000000,
      gap_percent: -1.67,
      cumulative_gap_percent: -3.10,
    },
    {
      bucket: 'MONTHS_3_6',
      bucket_label: '3-6 Months',
      days_from: 91,
      days_to: 180,
      assets: 600000000,
      liabilities: 620000000,
      gap: -20000000,
      cumulative_gap: -150000000,
      gap_percent: -0.48,
      cumulative_gap_percent: -3.57,
    },
    {
      bucket: 'MONTHS_6_12',
      bucket_label: '6-12 Months',
      days_from: 181,
      days_to: 365,
      assets: 800000000,
      liabilities: 700000000,
      gap: 100000000,
      cumulative_gap: -50000000,
      gap_percent: 2.38,
      cumulative_gap_percent: -1.19,
    },
    {
      bucket: 'YEARS_1_3',
      bucket_label: '1-3 Years',
      days_from: 366,
      days_to: 1095,
      assets: 1200000000,
      liabilities: 900000000,
      gap: 300000000,
      cumulative_gap: 250000000,
      gap_percent: 7.14,
      cumulative_gap_percent: 5.95,
    },
    {
      bucket: 'YEARS_3_5',
      bucket_label: '3-5 Years',
      days_from: 1096,
      days_to: 1825,
      assets: 700000000,
      liabilities: 400000000,
      gap: 300000000,
      cumulative_gap: 550000000,
      gap_percent: 7.14,
      cumulative_gap_percent: 13.10,
    },
    {
      bucket: 'OVER_5_YEARS',
      bucket_label: 'Over 5 Years',
      days_from: 1826,
      days_to: 99999,
      assets: 500000000,
      liabilities: 250000000,
      gap: 250000000,
      cumulative_gap: 800000000,
      gap_percent: 5.95,
      cumulative_gap_percent: 19.05,
    },
  ],
};

const regulatoryLimits = {
  cumulative_gap_1_to_14_days: { limit: 20, current: -1.67, status: 'COMPLIANT' },
  cumulative_gap_15_to_28_days: { limit: 20, current: -1.43, status: 'COMPLIANT' },
  negative_gap_single_bucket: { limit: 5, current: -1.67, status: 'COMPLIANT' },
};

export default function GapAnalysis() {
  const navigate = useNavigate();
  const [positionDate, setPositionDate] = useState('2024-12-31');

  const negativeGapBuckets = almPosition.buckets.filter((b) => b.gap < 0);
  const hasNegativeGap1Year = almPosition.cumulative_gap_1_year < 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Liquidity Gap Analysis</h1>
          <p className="text-muted-foreground">
            Asset-Liability mismatch analysis as per RBI ALM guidelines
          </p>
        </div>
        <div className="flex gap-2">
          <Select value={positionDate} onValueChange={setPositionDate}>
            <SelectTrigger className="w-40">
              <Calendar className="h-4 w-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="2024-12-31">31 Dec 2024</SelectItem>
              <SelectItem value="2024-11-30">30 Nov 2024</SelectItem>
              <SelectItem value="2024-10-31">31 Oct 2024</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Regenerate
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Regulatory Compliance Alert */}
      {hasNegativeGap1Year && (
        <Alert className="border-yellow-200 bg-yellow-50">
          <AlertTriangle className="h-4 w-4 text-yellow-600" />
          <AlertTitle className="text-yellow-800">Negative Cumulative Gap</AlertTitle>
          <AlertDescription className="text-yellow-700">
            Cumulative gap up to 1 year is negative ({formatCurrency(almPosition.cumulative_gap_1_year)}).
            This indicates a structural liquidity mismatch. Review funding sources.
          </AlertDescription>
        </Alert>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Assets
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(almPosition.total_assets)}</div>
            <p className="text-xs text-muted-foreground">Rate sensitive + Non-sensitive</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Liabilities
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(almPosition.total_liabilities)}
            </div>
            <p className="text-xs text-muted-foreground">Rate sensitive + Non-sensitive</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Net Position
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(almPosition.net_position)}
            </div>
            <p className="text-xs text-muted-foreground">Assets - Liabilities</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Cumulative Gap (1Y)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className={`text-2xl font-bold ${
                almPosition.cumulative_gap_1_year < 0 ? 'text-red-600' : 'text-green-600'
              }`}
            >
              {formatCurrency(almPosition.cumulative_gap_1_year)}
            </div>
            <div className="flex items-center gap-1 mt-1">
              {almPosition.cumulative_gap_1_year < 0 ? (
                <TrendingDown className="h-4 w-4 text-red-600" />
              ) : (
                <TrendingUp className="h-4 w-4 text-green-600" />
              )}
              <span
                className={`text-sm ${
                  almPosition.cumulative_gap_1_year < 0 ? 'text-red-600' : 'text-green-600'
                }`}
              >
                {almPosition.cumulative_gap_percent.toFixed(2)}% of liabilities
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Regulatory Limits */}
      <Card>
        <CardHeader>
          <CardTitle>Regulatory Limit Compliance</CardTitle>
          <CardDescription>RBI prescribed limits for structural liquidity</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Cumulative Gap (1-14 Days)</span>
                <Badge
                  variant={
                    regulatoryLimits.cumulative_gap_1_to_14_days.status === 'COMPLIANT'
                      ? 'default'
                      : 'destructive'
                  }
                >
                  {regulatoryLimits.cumulative_gap_1_to_14_days.status}
                </Badge>
              </div>
              <div className="text-2xl font-bold">
                {regulatoryLimits.cumulative_gap_1_to_14_days.current.toFixed(2)}%
              </div>
              <Progress
                value={Math.abs(regulatoryLimits.cumulative_gap_1_to_14_days.current) /
                       regulatoryLimits.cumulative_gap_1_to_14_days.limit * 100}
                className="mt-2"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Limit: {regulatoryLimits.cumulative_gap_1_to_14_days.limit}% of outflows
              </p>
            </div>

            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Cumulative Gap (15-28 Days)</span>
                <Badge
                  variant={
                    regulatoryLimits.cumulative_gap_15_to_28_days.status === 'COMPLIANT'
                      ? 'default'
                      : 'destructive'
                  }
                >
                  {regulatoryLimits.cumulative_gap_15_to_28_days.status}
                </Badge>
              </div>
              <div className="text-2xl font-bold">
                {regulatoryLimits.cumulative_gap_15_to_28_days.current.toFixed(2)}%
              </div>
              <Progress
                value={Math.abs(regulatoryLimits.cumulative_gap_15_to_28_days.current) /
                       regulatoryLimits.cumulative_gap_15_to_28_days.limit * 100}
                className="mt-2"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Limit: {regulatoryLimits.cumulative_gap_15_to_28_days.limit}% of outflows
              </p>
            </div>

            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Max Negative Gap (Single Bucket)</span>
                <Badge
                  variant={
                    regulatoryLimits.negative_gap_single_bucket.status === 'COMPLIANT'
                      ? 'default'
                      : 'destructive'
                  }
                >
                  {regulatoryLimits.negative_gap_single_bucket.status}
                </Badge>
              </div>
              <div className="text-2xl font-bold">
                {regulatoryLimits.negative_gap_single_bucket.current.toFixed(2)}%
              </div>
              <Progress
                value={Math.abs(regulatoryLimits.negative_gap_single_bucket.current) /
                       regulatoryLimits.negative_gap_single_bucket.limit * 100}
                className="mt-2"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Limit: {regulatoryLimits.negative_gap_single_bucket.limit}% of outflows
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Gap Analysis Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Maturity Bucket Analysis
          </CardTitle>
          <CardDescription>
            Position Date: {formatDate(almPosition.position_date)}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Time Bucket</TableHead>
                <TableHead className="text-right">Assets (Inflows)</TableHead>
                <TableHead className="text-right">Liabilities (Outflows)</TableHead>
                <TableHead className="text-right">Gap</TableHead>
                <TableHead className="text-right">Cumulative Gap</TableHead>
                <TableHead className="text-right">Gap %</TableHead>
                <TableHead className="text-right">Cum. Gap %</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {almPosition.buckets.map((bucket) => (
                <TableRow key={bucket.bucket}>
                  <TableCell className="font-medium">{bucket.bucket_label}</TableCell>
                  <TableCell className="text-right">{formatCurrency(bucket.assets)}</TableCell>
                  <TableCell className="text-right">
                    {formatCurrency(bucket.liabilities)}
                  </TableCell>
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
                  <TableCell
                    className={`text-right ${bucket.gap_percent < 0 ? 'text-red-600' : 'text-green-600'}`}
                  >
                    {bucket.gap_percent.toFixed(2)}%
                  </TableCell>
                  <TableCell
                    className={`text-right ${
                      bucket.cumulative_gap_percent < 0 ? 'text-red-600' : 'text-green-600'
                    }`}
                  >
                    {bucket.cumulative_gap_percent.toFixed(2)}%
                  </TableCell>
                </TableRow>
              ))}
              {/* Total Row */}
              <TableRow className="font-bold bg-muted/50">
                <TableCell>Total</TableCell>
                <TableCell className="text-right">
                  {formatCurrency(almPosition.total_assets)}
                </TableCell>
                <TableCell className="text-right">
                  {formatCurrency(almPosition.total_liabilities)}
                </TableCell>
                <TableCell
                  className={`text-right ${
                    almPosition.net_position < 0 ? 'text-red-600' : 'text-green-600'
                  }`}
                >
                  {formatCurrency(almPosition.net_position)}
                </TableCell>
                <TableCell colSpan={3}></TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Negative Gap Buckets Alert */}
      {negativeGapBuckets.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardHeader>
            <CardTitle className="text-yellow-800">Buckets with Negative Gaps</CardTitle>
            <CardDescription className="text-yellow-700">
              These buckets have liabilities exceeding assets
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {negativeGapBuckets.map((bucket) => (
                <div key={bucket.bucket} className="border rounded-lg p-3 bg-white">
                  <div className="font-medium">{bucket.bucket_label}</div>
                  <div className="text-lg font-bold text-red-600">
                    {formatCurrency(bucket.gap)}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {bucket.gap_percent.toFixed(2)}% of outflows
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
