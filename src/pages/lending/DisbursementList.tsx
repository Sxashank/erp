import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Banknote,
  Plus,
  Search,
  Download,
  Eye,
  CheckCircle,
  Clock,
  XCircle,
  AlertTriangle,
  ArrowUpRight,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { formatCurrency, formatDate } from '@/lib/utils';

// Mock data
const disbursementSummary = {
  total_disbursements: 856,
  total_amount: 2500000000,
  pending_approval: 12,
  pending_amount: 45000000,
  today_disbursements: 5,
  today_amount: 25000000,
};

const disbursements = [
  {
    id: '1',
    disbursement_number: 'SMFC/LA/2025/00145/D001',
    loan_account: 'SMFC/LA/2025/00145',
    entity: 'Sunrise Industries',
    requested_amount: 5000000,
    approved_amount: 5000000,
    disbursed_amount: 5000000,
    scheduled_date: '2025-01-15',
    disbursed_date: '2025-01-15',
    beneficiary_name: 'Sunrise Industries',
    beneficiary_account: '1234567890',
    disbursement_mode: 'RTGS',
    utr_number: 'HDFCH25015RTGS001',
    status: 'PROCESSED',
  },
  {
    id: '2',
    disbursement_number: 'SMFC/LA/2025/00146/D001',
    loan_account: 'SMFC/LA/2025/00146',
    entity: 'Metro Logistics',
    requested_amount: 10000000,
    approved_amount: 10000000,
    disbursed_amount: null,
    scheduled_date: '2025-01-16',
    disbursed_date: null,
    beneficiary_name: 'Metro Logistics',
    beneficiary_account: '5555666677',
    disbursement_mode: 'RTGS',
    utr_number: null,
    status: 'APPROVED',
  },
  {
    id: '3',
    disbursement_number: 'SMFC/LA/2025/00147/D001',
    loan_account: 'SMFC/LA/2025/00147',
    entity: 'Eastern Trading',
    requested_amount: 15000000,
    approved_amount: null,
    disbursed_amount: null,
    scheduled_date: '2025-01-17',
    disbursed_date: null,
    beneficiary_name: 'Eastern Trading Pvt Ltd',
    beneficiary_account: '9876543210',
    disbursement_mode: 'NEFT',
    utr_number: null,
    status: 'PENDING_APPROVAL',
  },
  {
    id: '4',
    disbursement_number: 'SMFC/LA/2025/00148/D001',
    loan_account: 'SMFC/LA/2025/00148',
    entity: 'Western Corp',
    requested_amount: 8000000,
    approved_amount: 6000000,
    disbursed_amount: null,
    scheduled_date: '2025-01-16',
    disbursed_date: null,
    beneficiary_name: 'Western Corp',
    beneficiary_account: '1122334455',
    disbursement_mode: 'RTGS',
    utr_number: null,
    status: 'VERIFIED',
  },
  {
    id: '5',
    disbursement_number: 'SMFC/LA/2025/00149/D001',
    loan_account: 'SMFC/LA/2025/00149',
    entity: 'Northern Industries',
    requested_amount: 20000000,
    approved_amount: null,
    disbursed_amount: null,
    scheduled_date: '2025-01-18',
    disbursed_date: null,
    beneficiary_name: 'Northern Industries',
    beneficiary_account: '6677889900',
    disbursement_mode: 'RTGS',
    utr_number: null,
    status: 'REJECTED',
    rejection_reason: 'Documentation incomplete',
  },
];

const getStatusBadge = (status: string) => {
  const variants: Record<string, { variant: 'default' | 'secondary' | 'outline' | 'destructive'; icon: React.ReactNode; label: string }> = {
    DRAFT: { variant: 'outline', icon: <Clock className="h-3 w-3" />, label: 'Draft' },
    PENDING_VERIFICATION: { variant: 'outline', icon: <Clock className="h-3 w-3" />, label: 'Pending Verification' },
    VERIFIED: { variant: 'secondary', icon: <CheckCircle className="h-3 w-3" />, label: 'Verified' },
    PENDING_APPROVAL: { variant: 'outline', icon: <AlertTriangle className="h-3 w-3" />, label: 'Pending Approval' },
    APPROVED: { variant: 'default', icon: <CheckCircle className="h-3 w-3" />, label: 'Approved' },
    PROCESSING: { variant: 'secondary', icon: <Clock className="h-3 w-3" />, label: 'Processing' },
    PROCESSED: { variant: 'default', icon: <CheckCircle className="h-3 w-3" />, label: 'Processed' },
    REJECTED: { variant: 'destructive', icon: <XCircle className="h-3 w-3" />, label: 'Rejected' },
    REVERSED: { variant: 'destructive', icon: <XCircle className="h-3 w-3" />, label: 'Reversed' },
  };
  const config = variants[status] || { variant: 'outline', icon: null, label: status };
  return (
    <Badge variant={config.variant} className="flex items-center gap-1">
      {config.icon}
      {config.label}
    </Badge>
  );
};

export default function DisbursementList() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [dateRange, setDateRange] = useState('month');

  const filteredDisbursements = disbursements.filter((d) => {
    const matchesSearch =
      d.disbursement_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.entity.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.loan_account.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || d.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const pendingApproval = disbursements.filter(
    (d) => d.status === 'PENDING_APPROVAL' || d.status === 'VERIFIED'
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Disbursements"
        subtitle="Manage loan disbursement requests"
        actions={
          <div className="flex gap-2">
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button onClick={() => navigate('/lending/disbursements/create')}>
              <Plus className="h-4 w-4 mr-2" />
              New Request
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Disbursements
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{disbursementSummary.total_disbursements}</div>
            <p className="text-xs text-muted-foreground">
              {formatCurrency(disbursementSummary.total_amount)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Today's Disbursements
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {disbursementSummary.today_disbursements}
            </div>
            <p className="text-xs text-muted-foreground">
              {formatCurrency(disbursementSummary.today_amount)}
            </p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:bg-muted/50" onClick={() => navigate('/lending/disbursements/approval')}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              Pending Approval
              <ArrowUpRight className="h-4 w-4" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-500">
              {disbursementSummary.pending_approval}
            </div>
            <p className="text-xs text-muted-foreground">
              {formatCurrency(disbursementSummary.pending_amount)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Avg. Disbursement
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {formatCurrency(disbursementSummary.total_amount / disbursementSummary.total_disbursements)}
            </div>
            <p className="text-xs text-muted-foreground">Per transaction</p>
          </CardContent>
        </Card>
      </div>

      {/* Pending Approval Alert */}
      {pendingApproval.length > 0 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="h-10 w-10 rounded-full bg-orange-100 flex items-center justify-center">
                  <AlertTriangle className="h-5 w-5 text-orange-600" />
                </div>
                <div>
                  <p className="font-medium">{pendingApproval.length} disbursements pending approval</p>
                  <p className="text-sm text-muted-foreground">
                    Total amount: {formatCurrency(pendingApproval.reduce((sum, d) => sum + d.requested_amount, 0))}
                  </p>
                </div>
              </div>
              <Button onClick={() => navigate('/lending/disbursements/approval')}>
                Review Now
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4 flex-wrap">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by disbursement number, entity, or loan account..."
                className="pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="DRAFT">Draft</SelectItem>
                <SelectItem value="PENDING_VERIFICATION">Pending Verification</SelectItem>
                <SelectItem value="VERIFIED">Verified</SelectItem>
                <SelectItem value="PENDING_APPROVAL">Pending Approval</SelectItem>
                <SelectItem value="APPROVED">Approved</SelectItem>
                <SelectItem value="PROCESSING">Processing</SelectItem>
                <SelectItem value="PROCESSED">Processed</SelectItem>
                <SelectItem value="REJECTED">Rejected</SelectItem>
              </SelectContent>
            </Select>
            <Select value={dateRange} onValueChange={setDateRange}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Date Range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="today">Today</SelectItem>
                <SelectItem value="week">This Week</SelectItem>
                <SelectItem value="month">This Month</SelectItem>
                <SelectItem value="quarter">This Quarter</SelectItem>
                <SelectItem value="all">All Time</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Disbursement Table */}
      <Card>
        <CardHeader>
          <CardTitle>Disbursement Requests</CardTitle>
          <CardDescription>{filteredDisbursements.length} records found</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Disbursement No.</TableHead>
                <TableHead>Entity / Loan</TableHead>
                <TableHead>Beneficiary</TableHead>
                <TableHead className="text-right">Requested</TableHead>
                <TableHead className="text-right">Approved</TableHead>
                <TableHead>Scheduled</TableHead>
                <TableHead>Mode</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredDisbursements.map((disbursement) => (
                <TableRow key={disbursement.id}>
                  <TableCell className="font-mono text-sm">{disbursement.disbursement_number}</TableCell>
                  <TableCell>
                    <div className="font-medium">{disbursement.entity}</div>
                    <div className="text-xs text-muted-foreground">{disbursement.loan_account}</div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">{disbursement.beneficiary_name}</div>
                    <div className="text-xs text-muted-foreground font-mono">
                      {disbursement.beneficiary_account}
                    </div>
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(disbursement.requested_amount)}
                  </TableCell>
                  <TableCell className="text-right">
                    {disbursement.approved_amount ? (
                      formatCurrency(disbursement.approved_amount)
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">{formatDate(disbursement.scheduled_date)}</div>
                    {disbursement.disbursed_date && (
                      <div className="text-xs text-green-600">
                        Paid: {formatDate(disbursement.disbursed_date)}
                      </div>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">{disbursement.disbursement_mode}</div>
                    {disbursement.utr_number && (
                      <div className="text-xs text-muted-foreground font-mono">
                        {disbursement.utr_number}
                      </div>
                    )}
                  </TableCell>
                  <TableCell>{getStatusBadge(disbursement.status)}</TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          ...
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => navigate(`/lending/disbursements/${disbursement.id}`)}
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        {(disbursement.status === 'PENDING_APPROVAL' || disbursement.status === 'VERIFIED') && (
                          <DropdownMenuItem
                            onClick={() => navigate(`/lending/disbursements/${disbursement.id}/approve`)}
                          >
                            <CheckCircle className="h-4 w-4 mr-2" />
                            Approve
                          </DropdownMenuItem>
                        )}
                        {disbursement.status === 'APPROVED' && (
                          <DropdownMenuItem
                            onClick={() => navigate(`/lending/disbursements/${disbursement.id}/process`)}
                          >
                            <Banknote className="h-4 w-4 mr-2" />
                            Process
                          </DropdownMenuItem>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
