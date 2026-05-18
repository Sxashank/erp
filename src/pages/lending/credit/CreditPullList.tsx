/**
 * Credit Bureau Pull List Page
 * Displays all credit bureau pulls with filtering and analysis options.
 *
 * Data source: GET /lending/credit/pulls (camelCase via Pydantic CamelSchema).
 */

import {
  Plus,
  Search,
  MoreHorizontal,
  Eye,
  BarChart3,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  User,
  CreditCard,
  TrendingUp,
  Loader2,
} from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
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
import {
  useCreditPulls,
  type CreditPullListItem,
  type CreditPullStatusValue,
  type CreditBureauValue,
  type ScoreBandValue,
  type CreditPullFilters,
} from '@/hooks/lending/useCreditPulls';

const statusColors: Record<CreditPullStatusValue, string> = {
  PENDING: 'bg-amber-100 text-amber-700 border-amber-300',
  IN_PROGRESS: 'bg-blue-100 text-blue-700 border-blue-300',
  SUCCESS: 'bg-green-100 text-green-700 border-green-300',
  FAILED: 'bg-red-100 text-red-700 border-red-300',
  NO_HIT: 'bg-slate-100 text-slate-700 border-slate-300',
  EXPIRED: 'bg-gray-100 text-gray-600 border-gray-300',
};

const scoreBandColors: Record<ScoreBandValue, string> = {
  EXCELLENT: 'bg-green-100 text-green-700 border-green-300',
  GOOD: 'bg-emerald-100 text-emerald-700 border-emerald-300',
  FAIR: 'bg-amber-100 text-amber-700 border-amber-300',
  POOR: 'bg-orange-100 text-orange-700 border-orange-300',
  VERY_POOR: 'bg-red-100 text-red-700 border-red-300',
  NA: 'bg-gray-100 text-gray-600 border-gray-300',
};

const StatusIcon = ({ status }: { status: CreditPullStatusValue }) => {
  switch (status) {
    case 'SUCCESS':
      return <CheckCircle className="h-4 w-4 text-green-600" />;
    case 'PENDING':
    case 'IN_PROGRESS':
      return <Clock className="h-4 w-4 text-amber-600" />;
    case 'FAILED':
      return <XCircle className="h-4 w-4 text-red-600" />;
    case 'NO_HIT':
    case 'EXPIRED':
      return <AlertTriangle className="h-4 w-4 text-slate-500" />;
    default:
      return null;
  }
};

const CreditScoreIndicator = ({
  score,
  band,
}: {
  score: number | null;
  band: ScoreBandValue | null;
}) => {
  if (score == null) return <span className="text-muted-foreground">—</span>;

  const percentage = Math.min(Math.max(((score - 300) / 600) * 100, 0), 100);

  let colorClass = 'bg-gray-400';
  if (score >= 750) colorClass = 'bg-green-500';
  else if (score >= 700) colorClass = 'bg-emerald-500';
  else if (score >= 650) colorClass = 'bg-amber-500';
  else if (score >= 550) colorClass = 'bg-orange-500';
  else colorClass = 'bg-red-500';

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <span className="text-lg font-bold">{score}</span>
        {band && (
          <Badge variant="outline" className={`text-xs ${scoreBandColors[band]}`}>
            {band}
          </Badge>
        )}
      </div>
      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-gray-200">
        <div
          className={`h-full ${colorClass} rounded-full transition-all`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

export default function CreditPullList() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [bureauFilter, setBureauFilter] = useState<string>('all');

  const filters: CreditPullFilters = {
    pageSize: 100,
    ...(statusFilter !== 'all' && {
      pullStatus: statusFilter as CreditPullStatusValue,
    }),
    ...(bureauFilter !== 'all' && { bureau: bureauFilter as CreditBureauValue }),
  };
  const { data, isLoading, isError, error, refetch } = useCreditPulls(filters);

  const all: CreditPullListItem[] = data?.items ?? [];
  const pulls = all.filter((p) => {
    if (!searchTerm) return true;
    const q = searchTerm.toLowerCase();
    return (
      p.customerName.toLowerCase().includes(q) || (p.panNumber ?? '').toLowerCase().includes(q)
    );
  });

  const stats = {
    total: data?.total ?? pulls.length,
    successful: pulls.filter((p) => p.status === 'SUCCESS').length,
    pending: pulls.filter((p) => p.status === 'PENDING' || p.status === 'IN_PROGRESS').length,
    failed: pulls.filter((p) => p.status === 'FAILED' || p.status === 'NO_HIT').length,
    avgScore: (() => {
      const scored = pulls.filter((p) => p.creditScore != null);
      if (scored.length === 0) return 0;
      return Math.round(scored.reduce((sum, p) => sum + (p.creditScore ?? 0), 0) / scored.length);
    })(),
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Credit Bureau Pulls"
        subtitle="View and manage credit report pulls from CIBIL, Experian, Equifax, and CRIF"
        actions={
          <Button onClick={() => navigate('/admin/lending/credit/request')}>
            <Plus className="mr-2 h-4 w-4" />
            Pull Credit Report
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Pulls</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Successful</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.successful}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Clock className="h-4 w-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600">{stats.pending}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed/No-Hit</CardTitle>
            <XCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.failed}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Score</CardTitle>
            <TrendingUp className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats.avgScore || '—'}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4">
            <div className="min-w-[200px] flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search by customer name or PAN..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="SUCCESS">Success</SelectItem>
                <SelectItem value="PENDING">Pending</SelectItem>
                <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
                <SelectItem value="FAILED">Failed</SelectItem>
                <SelectItem value="NO_HIT">No Hit</SelectItem>
                <SelectItem value="EXPIRED">Expired</SelectItem>
              </SelectContent>
            </Select>
            <Select value={bureauFilter} onValueChange={setBureauFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Bureau" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Bureaus</SelectItem>
                <SelectItem value="CIBIL">CIBIL</SelectItem>
                <SelectItem value="EXPERIAN">Experian</SelectItem>
                <SelectItem value="EQUIFAX">Equifax</SelectItem>
                <SelectItem value="CRIF">CRIF</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Pulled</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>Bureau</TableHead>
                <TableHead>Credit Score</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Validity</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-8 text-center text-muted-foreground">
                    <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />
                    Loading credit pulls...
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-8">
                    <ErrorState
                      title="Could not load credit pulls"
                      error={error}
                      onRetry={() => refetch()}
                    />
                  </TableCell>
                </TableRow>
              ) : pulls.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-12">
                    <div className="text-center">
                      <CreditCard className="mx-auto h-12 w-12 text-muted-foreground" />
                      <h3 className="mt-4 text-lg font-medium">No credit pulls found</h3>
                      <p className="text-muted-foreground">
                        Try adjusting your search or pull a new credit report
                      </p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                pulls.map((pull) => (
                  <TableRow key={pull.id}>
                    <TableCell>
                      <div className="text-sm">
                        {pull.pulledAt ? (
                          <DateDisplay date={pull.pulledAt} format="short" />
                        ) : (
                          <DateDisplay date={pull.createdAt} format="short" />
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">{pull.customerName}</span>
                        </div>
                        {pull.panNumber && (
                          <div className="font-mono text-xs text-muted-foreground">
                            PAN: {pull.panNumber}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <Badge variant="outline" className="font-medium">
                          {pull.bureau}
                        </Badge>
                        <div className="text-xs text-muted-foreground">
                          {pull.pullType === 'SOFT' ? 'Soft Pull' : 'Hard Pull'}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <CreditScoreIndicator score={pull.creditScore} band={pull.scoreBand} />
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={`border font-medium ${statusColors[pull.status]}`}
                      >
                        <StatusIcon status={pull.status} />
                        <span className="ml-1">{pull.status.replace('_', ' ')}</span>
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {pull.isValid ? (
                        <Badge variant="outline" className="bg-green-50 text-green-700">
                          Valid
                        </Badge>
                      ) : pull.status === 'SUCCESS' ? (
                        <Badge variant="outline" className="bg-red-50 text-red-700">
                          Expired
                        </Badge>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                      {pull.expiresAt && (
                        <div className="mt-1 text-xs text-muted-foreground">
                          <DateDisplay date={pull.expiresAt} format="short" />
                        </div>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={() => navigate(`/admin/lending/credit/pulls/${pull.id}`)}
                          >
                            <Eye className="mr-2 h-4 w-4" />
                            View Report
                          </DropdownMenuItem>
                          {pull.status === 'SUCCESS' && (
                            <DropdownMenuItem
                              onClick={() =>
                                navigate(`/admin/lending/credit/pulls/${pull.id}/analyze`)
                              }
                            >
                              <BarChart3 className="mr-2 h-4 w-4" />
                              Analyze Report
                            </DropdownMenuItem>
                          )}
                          {(pull.status === 'PENDING' || pull.status === 'IN_PROGRESS') && (
                            <DropdownMenuItem onClick={() => refetch()}>
                              <RefreshCw className="mr-2 h-4 w-4" />
                              Refresh Status
                            </DropdownMenuItem>
                          )}
                          {!pull.isValid && pull.status !== 'PENDING' && pull.panNumber && (
                            <>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                onClick={() =>
                                  navigate(`/admin/lending/credit/request?pan=${pull.panNumber}`)
                                }
                              >
                                <Plus className="mr-2 h-4 w-4" />
                                New Pull
                              </DropdownMenuItem>
                            </>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
