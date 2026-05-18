/**
 * AUM Summary Report
 *
 * Surfaces live AUM via the lending dashboard aggregator endpoint.
 * Branch / industry / vintage breakdowns require dedicated aggregator
 * endpoints (not yet built) and show EmptyState placeholders.
 */

import { Download, RefreshCw, AlertTriangle } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useLendingDashboard } from '@/hooks/lending/useLendingDashboard';

export default function AUMSummary() {
  const { data, isLoading, isError, error, refetch, isFetching } = useLendingDashboard();
  const kpis = data?.portfolioKpis;
  const productSlices = data?.portfolioByProduct ?? [];
  const classification = data?.assetClassification ?? [];

  const pieData = productSlices.map((p) => ({
    name: p.name,
    value: Number(p.value),
    color: p.color,
  }));

  return (
    <div className="space-y-6">
      <PageHeader
        title="AUM Summary"
        subtitle="Assets under management — product split, classification, vintage"
        breadcrumbs={[
          { label: 'Reports', to: '/admin/lending/reports' },
          { label: 'Portfolio' },
          { label: 'AUM Summary' },
        ]}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => refetch()} disabled={isFetching}>
              <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
          </div>
        }
      />

      {isError && (
        <ErrorState title="Could not load AUM summary" error={error} onRetry={() => refetch()} />
      )}

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total AUM</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <AmountDisplay
                amount={kpis?.totalAum ?? 0}
                abbreviated
                className="text-2xl font-bold"
              />
            )}
            <p className="mt-1 text-xs text-muted-foreground">Outstanding</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Active Accounts
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold">{kpis?.activeAccounts ?? 0}</div>
            )}
            <p className="mt-1 text-xs text-muted-foreground">Live loan accounts</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Sanctioned Pipeline
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <AmountDisplay
                amount={kpis?.sanctionedPipeline ?? 0}
                abbreviated
                className="text-2xl font-bold text-amber-600"
              />
            )}
            <p className="mt-1 text-xs text-muted-foreground">Awaiting disbursement</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Gross NPA</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold">
                <PercentageDisplay value={kpis?.grossNpa ?? '0'} />
              </div>
            )}
            <p className="mt-1 text-xs text-muted-foreground">RBI definition</p>
          </CardContent>
        </Card>
      </div>

      {/* Product split */}
      <Card>
        <CardHeader>
          <CardTitle>AUM by Product</CardTitle>
          <CardDescription>Portfolio split (₹ Cr)</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-80 w-full" />
          ) : pieData.length === 0 ? (
            <EmptyState
              title="No active loans yet"
              subtitle="Product split will populate once loans are disbursed."
            />
          ) : (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData as unknown as Record<string, unknown>[]}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="value"
                    label={({ name, percent }) => `${name}: ${((percent ?? 0) * 100).toFixed(0)}%`}
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: number | undefined) => [`₹ ${v ?? 0} Cr`, 'AUM']} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Asset classification */}
      <Card>
        <CardHeader>
          <CardTitle>Asset Classification</CardTitle>
          <CardDescription>Portfolio quality breakdown</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6">
              <Skeleton className="h-40 w-full" />
            </div>
          ) : classification.length === 0 ? (
            <div className="p-6">
              <EmptyState
                title="No active loans yet"
                subtitle="Classification breakdown shows once accounts are live."
              />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Category</TableHead>
                  <TableHead className="text-right">Amount (₹ Cr)</TableHead>
                  <TableHead className="text-right">% of Portfolio</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {classification.map((row) => (
                  <TableRow key={row.category}>
                    <TableCell className="font-medium">{row.category}</TableCell>
                    <TableCell className="text-right">{row.amount}</TableCell>
                    <TableCell className="text-right">
                      <PercentageDisplay value={row.percentage} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Branch / industry / vintage placeholders */}
      <Card>
        <CardHeader>
          <CardTitle>Branch / Industry / Vintage Breakdowns</CardTitle>
          <CardDescription>Detailed slices of the portfolio</CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState
            title="Detailed breakdowns not yet wired"
            subtitle="Branch-wise, industry-wise and vintage breakdowns require a dedicated portfolio-analytics endpoint that joins loan accounts to entities, branches and FY of disbursement. Coming soon."
            icon={AlertTriangle}
          />
        </CardContent>
      </Card>
    </div>
  );
}
