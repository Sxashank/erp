import { Briefcase, Plus, Search, Filter, Eye, Download, TrendingUp, Calendar } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { AmountDisplay } from '@/components/common/AmountDisplay';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { SkeletonTable } from '@/components/common/SkeletonTable';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
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
import { useInvestments, usePortfolioSummary } from '@/hooks/lending/useTreasuryInvestments';
import { formatDate } from '@/lib/utils';
import type {
  InvestmentCategory,
  InvestmentResponse,
} from '@/services/lending/treasuryInvestmentApi';

const TYPE_LABELS: Record<string, string> = {
  GSEC: 'Government Securities',
  SDL: 'State Development Loans',
  TBILL: 'Treasury Bills',
  CORP_BOND: 'Corporate Bonds',
  NCD: 'Non-Convertible Debentures',
  CP: 'Commercial Paper',
  CD: 'Certificate of Deposit',
  MUTUAL_FUND: 'Mutual Fund',
};

function getStatusBadge(status: string) {
  switch (status) {
    case 'ACTIVE':
      return (
        <Badge variant="default" className="bg-green-100 text-green-800">
          Active
        </Badge>
      );
    case 'MATURED':
      return <Badge variant="secondary">Matured</Badge>;
    case 'SOLD':
      return <Badge variant="outline">Sold</Badge>;
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
}

function getCategoryBadge(category: string) {
  switch (category) {
    case 'HTM':
      return <Badge variant="outline">HTM</Badge>;
    case 'AFS':
      return <Badge variant="secondary">AFS</Badge>;
    case 'HFT':
      return <Badge variant="default">HFT</Badge>;
    default:
      return <Badge variant="outline">{category}</Badge>;
  }
}

export default function InvestmentList() {
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');

  // Server-side filter only by category (BE supports it). Type and free-text
  // filter on the client over the current page — BE side text-search is a
  // follow-up.
  const investmentsQuery = useInvestments({
    category: categoryFilter === 'all' ? undefined : (categoryFilter as InvestmentCategory),
    page_size: 200,
  });
  const summaryQuery = usePortfolioSummary();

  const investments = investmentsQuery.data?.items ?? [];
  const filteredInvestments: InvestmentResponse[] = useMemo(() => {
    return investments.filter((inv) => {
      const haystack = `${inv.investmentNumber} ${inv.issuer} ${inv.description}`.toLowerCase();
      const matchesSearch = searchTerm.trim() === '' || haystack.includes(searchTerm.toLowerCase());
      const matchesType = typeFilter === 'all' || inv.type === typeFilter;
      return matchesSearch && matchesType;
    });
  }, [investments, searchTerm, typeFilter]);

  const summary = summaryQuery.data;
  const summaryError = summaryQuery.isError;

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Investment Portfolio"
        subtitle="Manage treasury investments and securities"
        actions={
          <Link to="/admin/treasury/investments/new">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              New Investment
            </Button>
          </Link>
        }
      />

      {/* Portfolio Summary */}
      {summaryQuery.isLoading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <div className="mb-2 h-4 w-24 animate-pulse rounded bg-muted" />
                <div className="h-7 w-32 animate-pulse rounded bg-muted" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : summaryError ? (
        <ErrorState
          error={summaryQuery.error}
          title="Unable to load portfolio summary"
          onRetry={() => summaryQuery.refetch()}
        />
      ) : summary ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-6">
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-muted-foreground">Face Value</div>
              <AmountDisplay
                amount={summary.totalFaceValue}
                abbreviated
                className="mt-1 block whitespace-nowrap text-2xl font-bold"
              />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-muted-foreground">Purchase Value</div>
              <AmountDisplay
                amount={summary.totalPurchaseValue}
                abbreviated
                className="mt-1 block whitespace-nowrap text-2xl font-bold"
              />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-muted-foreground">Current Value</div>
              <AmountDisplay
                amount={summary.totalCurrentValue}
                abbreviated
                className="mt-1 block whitespace-nowrap text-2xl font-bold"
              />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-muted-foreground">Unrealised Gain / (Loss)</div>
              <AmountDisplay
                amount={summary.unrealizedGainLoss}
                abbreviated
                className={`mt-1 block whitespace-nowrap text-2xl font-bold ${
                  Number(summary.unrealizedGainLoss) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-muted-foreground">Weighted Avg. YTM</div>
              <div className="mt-1 text-2xl font-bold">
                {summary.weightedAvgYtm ? `${Number(summary.weightedAvgYtm).toFixed(2)}%` : '-'}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-muted-foreground">Active Holdings</div>
              <div className="mt-1 text-2xl font-bold">{summary.activeCount}</div>
            </CardContent>
          </Card>
        </div>
      ) : null}

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex min-w-[200px] flex-1 items-center gap-2">
              <Search className="h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by ID, issuer, or description..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="max-w-sm"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  {Object.entries(TYPE_LABELS).map(([id, label]) => (
                    <SelectItem key={id} value={id}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="HTM">HTM</SelectItem>
                <SelectItem value="AFS">AFS</SelectItem>
                <SelectItem value="HFT">HFT</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Investments Table */}
      <Card>
        <CardHeader>
          <CardTitle>Investment Holdings</CardTitle>
          <CardDescription>
            {investmentsQuery.isLoading
              ? 'Loading…'
              : `Showing ${filteredInvestments.length} of ${investments.length} investments`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {investmentsQuery.isLoading ? (
            <SkeletonTable rows={6} columns={9} />
          ) : investmentsQuery.isError ? (
            <ErrorState
              error={investmentsQuery.error}
              title="Unable to load investments"
              onRetry={() => investmentsQuery.refetch()}
            />
          ) : filteredInvestments.length === 0 ? (
            <EmptyState
              title="No investments yet"
              subtitle={
                investments.length === 0
                  ? 'Record your first treasury investment to start tracking the portfolio.'
                  : 'No investments match the current filters.'
              }
              action={
                investments.length === 0 ? (
                  <Link to="/admin/treasury/investments/new">
                    <Button>
                      <Plus className="mr-2 h-4 w-4" />
                      Add Investment
                    </Button>
                  </Link>
                ) : undefined
              }
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Investment</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead className="text-right">Face Value</TableHead>
                  <TableHead className="text-right">Current Value</TableHead>
                  <TableHead className="text-right">Coupon</TableHead>
                  <TableHead className="text-right">YTM</TableHead>
                  <TableHead>Maturity</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredInvestments.map((investment) => {
                  const faceTotal = Number(investment.faceValue) * Number(investment.units);
                  const purchaseTotal = Number(investment.purchasePrice) * Number(investment.units);
                  const currentTotal =
                    investment.currentValue !== null
                      ? Number(investment.currentValue)
                      : purchaseTotal;
                  const delta = currentTotal - purchaseTotal;
                  return (
                    <TableRow key={investment.id}>
                      <TableCell>
                        <div>
                          <div className="font-mono text-sm">{investment.investmentNumber}</div>
                          <div className="font-medium">{investment.issuer}</div>
                          <div className="text-xs text-muted-foreground">
                            {investment.description}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{TYPE_LABELS[investment.type] ?? investment.type}</TableCell>
                      <TableCell>{getCategoryBadge(investment.category)}</TableCell>
                      <TableCell className="text-right font-medium tabular-nums">
                        <AmountDisplay amount={faceTotal} abbreviated />
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        <div>
                          <AmountDisplay amount={currentTotal} abbreviated />
                        </div>
                        {delta > 0 && (
                          <div className="text-xs text-green-600">
                            +<AmountDisplay amount={delta} abbreviated />
                          </div>
                        )}
                        {delta < 0 && (
                          <div className="text-xs text-red-600">
                            <AmountDisplay amount={delta} abbreviated />
                          </div>
                        )}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {Number(investment.couponRate) > 0
                          ? `${Number(investment.couponRate).toFixed(2)}%`
                          : '-'}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {Number(investment.ytm) > 0 ? `${Number(investment.ytm).toFixed(2)}%` : '-'}
                      </TableCell>
                      <TableCell>{formatDate(investment.maturityDate)}</TableCell>
                      <TableCell>{getStatusBadge(investment.status)}</TableCell>
                      <TableCell className="text-right">
                        <Link to={`/admin/treasury/investments/${investment.id}`}>
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Quick Links */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Link to="/admin/treasury/investments/maturity">
          <Card className="cursor-pointer transition-colors hover:bg-muted/50">
            <CardContent className="pt-6">
              <Calendar className="mb-2 h-8 w-8 text-primary" />
              <h3 className="font-medium">Maturity Schedule</h3>
              <p className="text-sm text-muted-foreground">View upcoming maturities</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/admin/treasury/investments/valuation">
          <Card className="cursor-pointer transition-colors hover:bg-muted/50">
            <CardContent className="pt-6">
              <TrendingUp className="mb-2 h-8 w-8 text-primary" />
              <h3 className="font-medium">Portfolio Valuation</h3>
              <p className="text-sm text-muted-foreground">Mark-to-market analysis</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/admin/treasury/risk-dashboard">
          <Card className="cursor-pointer transition-colors hover:bg-muted/50">
            <CardContent className="pt-6">
              <Briefcase className="mb-2 h-8 w-8 text-primary" />
              <h3 className="font-medium">Risk Analysis</h3>
              <p className="text-sm text-muted-foreground">Investment risk metrics</p>
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}
