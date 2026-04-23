/**
 * Credit Bureau Pull List Page
 * Displays all credit bureau pulls with filtering and analysis options
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
  TrendingDown,
  Minus,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { DateDisplay } from '@/components/lending/common/DateDisplay';

// Credit Pull Status
type CreditPullStatus = 'PENDING' | 'IN_PROGRESS' | 'SUCCESS' | 'FAILED' | 'NO_HIT' | 'EXPIRED';

// Credit Bureau
type CreditBureau = 'CIBIL' | 'EXPERIAN' | 'EQUIFAX' | 'CRIF';

// Pull Type
type PullType = 'SOFT' | 'HARD';

// Score Band
type ScoreBand = 'EXCELLENT' | 'GOOD' | 'FAIR' | 'POOR' | 'VERY_POOR' | 'NA';

interface CreditPull {
  id: string;
  bureau: CreditBureau;
  pullType: PullType;
  status: CreditPullStatus;
  customerName: string;
  panNumber?: string;
  entityName?: string;
  loanApplicationNumber?: string;
  creditScore?: number;
  scoreBand?: ScoreBand;
  totalAccounts?: number;
  activeAccounts?: number;
  totalOutstanding?: number;
  maxDpd12m?: number;
  enquiriesLast30d?: number;
  requestReference?: string;
  bureauReference?: string;
  pulledAt?: string;
  expiresAt?: string;
  isValid: boolean;
  createdAt: string;
  errorMessage?: string;
}

// Status badge colors
const statusColors: Record<CreditPullStatus, string> = {
  PENDING: 'bg-amber-100 text-amber-700 border-amber-300',
  IN_PROGRESS: 'bg-blue-100 text-blue-700 border-blue-300',
  SUCCESS: 'bg-green-100 text-green-700 border-green-300',
  FAILED: 'bg-red-100 text-red-700 border-red-300',
  NO_HIT: 'bg-slate-100 text-slate-700 border-slate-300',
  EXPIRED: 'bg-gray-100 text-gray-600 border-gray-300',
};

// Score band colors
const scoreBandColors: Record<ScoreBand, string> = {
  EXCELLENT: 'bg-green-100 text-green-700 border-green-300',
  GOOD: 'bg-emerald-100 text-emerald-700 border-emerald-300',
  FAIR: 'bg-amber-100 text-amber-700 border-amber-300',
  POOR: 'bg-orange-100 text-orange-700 border-orange-300',
  VERY_POOR: 'bg-red-100 text-red-700 border-red-300',
  NA: 'bg-gray-100 text-gray-600 border-gray-300',
};

const StatusIcon = ({ status }: { status: CreditPullStatus }) => {
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

// Credit Score Gauge (inline mini version)
const CreditScoreIndicator = ({ score, band }: { score?: number; band?: ScoreBand }) => {
  if (!score) return <span className="text-muted-foreground">-</span>;

  // Calculate position (300-900 range)
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
      <div className="w-24 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full ${colorClass} rounded-full transition-all`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

// Mock data
const mockCreditPulls: CreditPull[] = [
  {
    id: '1',
    bureau: 'CIBIL',
    pullType: 'SOFT',
    status: 'SUCCESS',
    customerName: 'Rahul Sharma',
    panNumber: 'ABCDE1234F',
    entityName: 'ABC Industries Pvt Ltd',
    loanApplicationNumber: 'APP-2025-0001',
    creditScore: 782,
    scoreBand: 'EXCELLENT',
    totalAccounts: 8,
    activeAccounts: 5,
    totalOutstanding: 2500000,
    maxDpd12m: 0,
    enquiriesLast30d: 1,
    requestReference: 'REQ-2025-001',
    bureauReference: 'CIB-RPT-001',
    pulledAt: '2025-01-10T14:30:00',
    expiresAt: '2025-02-10T14:30:00',
    isValid: true,
    createdAt: '2025-01-10T14:25:00',
  },
  {
    id: '2',
    bureau: 'EXPERIAN',
    pullType: 'HARD',
    status: 'SUCCESS',
    customerName: 'Priya Patel',
    panNumber: 'XYZAB5678G',
    entityName: 'XYZ Trading Co',
    loanApplicationNumber: 'APP-2025-0015',
    creditScore: 695,
    scoreBand: 'FAIR',
    totalAccounts: 5,
    activeAccounts: 3,
    totalOutstanding: 1200000,
    maxDpd12m: 30,
    enquiriesLast30d: 3,
    requestReference: 'REQ-2025-002',
    bureauReference: 'EXP-RPT-002',
    pulledAt: '2025-01-12T10:15:00',
    expiresAt: '2025-02-12T10:15:00',
    isValid: true,
    createdAt: '2025-01-12T10:10:00',
  },
  {
    id: '3',
    bureau: 'CIBIL',
    pullType: 'SOFT',
    status: 'NO_HIT',
    customerName: 'Amit Kumar',
    panNumber: 'PQRST9012H',
    entityName: 'Kumar Enterprises',
    requestReference: 'REQ-2025-003',
    isValid: false,
    createdAt: '2025-01-13T09:00:00',
    errorMessage: 'No credit record found for the given PAN',
  },
  {
    id: '4',
    bureau: 'EQUIFAX',
    pullType: 'SOFT',
    status: 'SUCCESS',
    customerName: 'Sneha Reddy',
    panNumber: 'LMNOP3456J',
    entityName: 'Reddy & Sons',
    loanApplicationNumber: 'APP-2024-0089',
    creditScore: 545,
    scoreBand: 'VERY_POOR',
    totalAccounts: 12,
    activeAccounts: 4,
    totalOutstanding: 4500000,
    maxDpd12m: 90,
    enquiriesLast30d: 5,
    requestReference: 'REQ-2024-089',
    bureauReference: 'EQF-RPT-089',
    pulledAt: '2024-12-15T11:30:00',
    expiresAt: '2025-01-15T11:30:00',
    isValid: false,
    createdAt: '2024-12-15T11:25:00',
  },
  {
    id: '5',
    bureau: 'CIBIL',
    pullType: 'SOFT',
    status: 'PENDING',
    customerName: 'Vikram Singh',
    panNumber: 'UVWXY7890K',
    entityName: 'Singh Industries',
    loanApplicationNumber: 'APP-2025-0022',
    requestReference: 'REQ-2025-022',
    isValid: false,
    createdAt: '2025-01-14T08:00:00',
  },
  {
    id: '6',
    bureau: 'EXPERIAN',
    pullType: 'SOFT',
    status: 'FAILED',
    customerName: 'Meera Joshi',
    panNumber: 'ABCXY1234L',
    entityName: 'Joshi Traders',
    requestReference: 'REQ-2025-023',
    isValid: false,
    createdAt: '2025-01-14T09:30:00',
    errorMessage: 'Bureau API timeout',
  },
];

export default function CreditPullList() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [bureauFilter, setBureauFilter] = useState<string>('all');

  // Filter pulls
  const filteredPulls = mockCreditPulls.filter((pull) => {
    const matchesSearch =
      searchTerm === '' ||
      pull.customerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      pull.panNumber?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      pull.entityName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      pull.requestReference?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === 'all' || pull.status === statusFilter;
    const matchesBureau = bureauFilter === 'all' || pull.bureau === bureauFilter;

    return matchesSearch && matchesStatus && matchesBureau;
  });

  // Calculate statistics
  const stats = {
    total: mockCreditPulls.length,
    successful: mockCreditPulls.filter((p) => p.status === 'SUCCESS').length,
    pending: mockCreditPulls.filter((p) => p.status === 'PENDING' || p.status === 'IN_PROGRESS').length,
    failed: mockCreditPulls.filter((p) => p.status === 'FAILED' || p.status === 'NO_HIT').length,
    avgScore:
      Math.round(
        mockCreditPulls
          .filter((p) => p.creditScore)
          .reduce((sum, p) => sum + (p.creditScore || 0), 0) /
          mockCreditPulls.filter((p) => p.creditScore).length
      ) || 0,
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Credit Bureau Pulls"
        subtitle="View and manage credit report pulls from CIBIL, Experian, Equifax, and CRIF"
        actions={
          <Button onClick={() => navigate('/lending/credit/request')}>
            <Plus className="mr-2 h-4 w-4" />
            Pull Credit Report
          </Button>
        }
      />

      {/* Statistics Cards */}
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
            <div className="text-2xl font-bold text-blue-600">{stats.avgScore}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by name, PAN, or reference..."
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

      {/* Credit Pulls Table */}
      <Card>
        <CardContent className="pt-6">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Reference</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>Bureau</TableHead>
                <TableHead>Credit Score</TableHead>
                <TableHead>Accounts</TableHead>
                <TableHead>DPD</TableHead>
                <TableHead>Enquiries</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredPulls.map((pull) => (
                <TableRow key={pull.id}>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="font-medium font-mono text-sm">
                        {pull.requestReference || '-'}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        <DateDisplay date={pull.createdAt} format="short" />
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{pull.customerName}</span>
                      </div>
                      {pull.panNumber && (
                        <div className="text-xs text-muted-foreground font-mono">
                          PAN: {pull.panNumber}
                        </div>
                      )}
                      {pull.entityName && (
                        <div className="text-xs text-muted-foreground">{pull.entityName}</div>
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
                    {pull.status === 'SUCCESS' ? (
                      <div className="text-sm">
                        <div>
                          <span className="font-medium">{pull.activeAccounts}</span>
                          <span className="text-muted-foreground"> / {pull.totalAccounts}</span>
                        </div>
                        <div className="text-xs text-muted-foreground">Active / Total</div>
                      </div>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {pull.status === 'SUCCESS' ? (
                      <div className="flex items-center gap-1">
                        {pull.maxDpd12m === 0 ? (
                          <Badge variant="outline" className="bg-green-50 text-green-700">
                            0 Days
                          </Badge>
                        ) : pull.maxDpd12m && pull.maxDpd12m <= 30 ? (
                          <Badge variant="outline" className="bg-amber-50 text-amber-700">
                            {pull.maxDpd12m} Days
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="bg-red-50 text-red-700">
                            {pull.maxDpd12m}+ Days
                          </Badge>
                        )}
                      </div>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {pull.status === 'SUCCESS' ? (
                      <div className="flex items-center gap-1">
                        {pull.enquiriesLast30d === 0 || !pull.enquiriesLast30d ? (
                          <span className="text-green-600">0</span>
                        ) : pull.enquiriesLast30d <= 2 ? (
                          <span className="text-amber-600">{pull.enquiriesLast30d}</span>
                        ) : (
                          <span className="text-red-600 font-medium">{pull.enquiriesLast30d}</span>
                        )}
                        <span className="text-xs text-muted-foreground">(30d)</span>
                      </div>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <Badge
                        variant="outline"
                        className={`font-medium border ${statusColors[pull.status]}`}
                      >
                        <StatusIcon status={pull.status} />
                        <span className="ml-1">{pull.status.replace('_', ' ')}</span>
                      </Badge>
                      {pull.isValid && (
                        <div className="text-xs text-green-600">Valid</div>
                      )}
                      {pull.status === 'SUCCESS' && !pull.isValid && (
                        <div className="text-xs text-red-600">Expired</div>
                      )}
                    </div>
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
                          onClick={() => navigate(`/lending/credit/pulls/${pull.id}`)}
                        >
                          <Eye className="mr-2 h-4 w-4" />
                          View Report
                        </DropdownMenuItem>
                        {pull.status === 'SUCCESS' && (
                          <>
                            <DropdownMenuItem
                              onClick={() => navigate(`/lending/credit/pulls/${pull.id}/analyze`)}
                            >
                              <BarChart3 className="mr-2 h-4 w-4" />
                              Analyze Report
                            </DropdownMenuItem>
                          </>
                        )}
                        {(pull.status === 'PENDING' || pull.status === 'IN_PROGRESS') && (
                          <DropdownMenuItem>
                            <RefreshCw className="mr-2 h-4 w-4" />
                            Refresh Status
                          </DropdownMenuItem>
                        )}
                        {pull.status === 'FAILED' && (
                          <DropdownMenuItem>
                            <RefreshCw className="mr-2 h-4 w-4" />
                            Retry Pull
                          </DropdownMenuItem>
                        )}
                        {!pull.isValid && pull.status !== 'PENDING' && (
                          <>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() =>
                                navigate(`/lending/credit/request?pan=${pull.panNumber}`)
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
              ))}
            </TableBody>
          </Table>

          {filteredPulls.length === 0 && (
            <div className="text-center py-12">
              <CreditCard className="mx-auto h-12 w-12 text-muted-foreground" />
              <h3 className="mt-4 text-lg font-medium">No credit pulls found</h3>
              <p className="text-muted-foreground">
                Try adjusting your search or filter criteria
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
