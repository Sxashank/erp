import { Download, AlertTriangle, Clock } from 'lucide-react';
import { useState, useMemo } from 'react';

import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useMaturitySchedule } from '@/hooks/lending/useTreasuryInvestments';
import { formatCurrency, formatDate } from '@/lib/utils';

const PERIOD_OPTIONS = [
  { id: '3', label: 'Next 3 Months' },
  { id: '6', label: 'Next 6 Months' },
  { id: '12', label: 'Next 1 Year' },
  { id: '36', label: 'Next 3 Years' },
  { id: '120', label: 'All Periods' },
];

export default function InvestmentMaturity() {
  const [periodFilter, setPeriodFilter] = useState<string>('12');
  const months = Number(periodFilter);

  const query = useMaturitySchedule(months);
  const data = query.data;

  const totalsLabel = useMemo(() => {
    if (!data) return '';
    return `${data.buckets.length} bucket${data.buckets.length === 1 ? '' : 's'}`;
  }, [data]);

  // Compute "Maturing in 2025"-style year totals from buckets. Today's year
  // bucket totals from the response feed both this and the upcoming alert.
  const currentYearTotal = useMemo(() => {
    if (!data) return '0';
    const thisYear = new Date(data.asOfDate).getFullYear();
    let sum = 0;
    for (const b of data.buckets) {
      const y = new Date(b.periodStart).getFullYear();
      if (y === thisYear) sum += Number(b.totalFaceValue);
    }
    return String(sum);
  }, [data]);

  const daysToMaturity = (maturityDate: string) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const target = new Date(maturityDate);
    target.setHours(0, 0, 0, 0);
    const diffMs = target.getTime() - today.getTime();
    return Math.max(0, Math.round(diffMs / (1000 * 60 * 60 * 24)));
  };

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Maturity Schedule"
        subtitle="Investment maturity profile and upcoming redemptions"
        breadcrumbs={[
          { label: 'Investments', to: '/admin/treasury/investments' },
          { label: 'Maturity' },
        ]}
        actions={
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        }
      />

      {query.isLoading ? (
        <div className="space-y-6">
          <Skeleton className="h-32 w-full" />
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-20" />
            ))}
          </div>
          <Skeleton className="h-96 w-full" />
        </div>
      ) : query.isError ? (
        <ErrorState
          error={query.error}
          title="Unable to load maturity schedule"
          onRetry={() => query.refetch()}
        />
      ) : data ? (
        <>
          {/* Upcoming Maturities Alert */}
          {data.upcoming30D.length > 0 && (
            <Card className="border-yellow-200 bg-yellow-50">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-yellow-800">
                  <AlertTriangle className="h-5 w-5" />
                  Upcoming Maturities (Next 30 Days)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {data.upcoming30D.map((investment) => {
                    const days = daysToMaturity(investment.maturityDate);
                    const faceTotal = Number(investment.faceValue) * Number(investment.units);
                    return (
                      <div
                        key={investment.id}
                        className="flex items-center justify-between rounded-lg bg-white p-3"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-sm">{investment.investmentNumber}</span>
                            <Badge variant="outline">
                              <Clock className="mr-1 h-3 w-3" />
                              {days === 0 ? 'Today' : `${days} day${days === 1 ? '' : 's'}`}
                            </Badge>
                          </div>
                          <p className="font-medium">{investment.issuer}</p>
                          <p className="text-sm text-muted-foreground">{investment.description}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold tabular-nums">{formatCurrency(faceTotal)}</p>
                          <p className="text-sm text-muted-foreground">
                            Maturity: {formatDate(investment.maturityDate)}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Summary Statistics */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <Card>
              <CardContent className="pt-6">
                <div className="text-sm text-muted-foreground">Maturing in 30 Days</div>
                <div className="mt-1 text-2xl font-bold text-yellow-600">
                  {formatCurrency(data.totalMaturing30D)}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-sm text-muted-foreground">Maturing in 90 Days</div>
                <div className="mt-1 text-2xl font-bold">
                  {formatCurrency(data.totalMaturing90D)}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-sm text-muted-foreground">
                  Maturing in {new Date(data.asOfDate).getFullYear()}
                </div>
                <div className="mt-1 text-2xl font-bold">{formatCurrency(currentYearTotal)}</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-sm text-muted-foreground">Total in Selected Period</div>
                <div className="mt-1 text-2xl font-bold">
                  {formatCurrency(data.totalMaturingPeriod)}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Maturity Ladder */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Maturity Ladder</CardTitle>
                  <CardDescription>
                    Investment redemption schedule by time bucket — {totalsLabel}
                  </CardDescription>
                </div>
                <Select value={periodFilter} onValueChange={setPeriodFilter}>
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="Period" />
                  </SelectTrigger>
                  <SelectContent>
                    {PERIOD_OPTIONS.map((opt) => (
                      <SelectItem key={opt.id} value={opt.id}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              {data.buckets.length === 0 ? (
                <EmptyState
                  title="No maturities in selected period"
                  subtitle="Try widening the period filter or add an investment with a maturity date."
                />
              ) : (
                <div className="space-y-6">
                  {data.buckets.map((bucket) => (
                    <div key={bucket.label} className="rounded-lg border p-4">
                      <div className="mb-4 flex items-center justify-between">
                        <h3 className="text-lg font-bold">{bucket.label}</h3>
                        <Badge variant={Number(bucket.totalFaceValue) > 0 ? 'default' : 'outline'}>
                          {formatCurrency(bucket.totalFaceValue)}
                        </Badge>
                      </div>
                      {bucket.investments.length > 0 ? (
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Investment ID</TableHead>
                              <TableHead>Issuer</TableHead>
                              <TableHead>Description</TableHead>
                              <TableHead>Maturity Date</TableHead>
                              <TableHead className="text-right">Coupon</TableHead>
                              <TableHead className="text-right">Face Value</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {bucket.investments.map((investment) => {
                              const faceTotal =
                                Number(investment.faceValue) * Number(investment.units);
                              return (
                                <TableRow key={investment.id}>
                                  <TableCell className="font-mono text-sm">
                                    {investment.investmentNumber}
                                  </TableCell>
                                  <TableCell className="font-medium">{investment.issuer}</TableCell>
                                  <TableCell>{investment.description}</TableCell>
                                  <TableCell>{formatDate(investment.maturityDate)}</TableCell>
                                  <TableCell className="text-right tabular-nums">
                                    {Number(investment.couponRate) > 0
                                      ? `${Number(investment.couponRate).toFixed(2)}%`
                                      : '-'}
                                  </TableCell>
                                  <TableCell className="text-right font-medium tabular-nums">
                                    {formatCurrency(faceTotal)}
                                  </TableCell>
                                </TableRow>
                              );
                            })}
                          </TableBody>
                        </Table>
                      ) : (
                        <p className="py-4 text-center text-muted-foreground">
                          No maturities scheduled
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  );
}
