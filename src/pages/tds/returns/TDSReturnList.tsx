import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  Search,
  FileText,
  Download,
  CheckCircle,
  Clock,
  AlertTriangle,
  XCircle,
  Eye,
  Upload,
  RefreshCw,
  Calendar,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
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
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { formatCurrency, formatDate } from '@/lib/utils';

// Types
type ReturnStatus = 'DRAFT' | 'VALIDATED' | 'GENERATED' | 'UPLOADED' | 'FILED' | 'ACCEPTED' | 'REJECTED' | 'REVISED';
type ReturnType = 'FORM_26Q' | 'FORM_27Q' | 'FORM_27EQ';
type Quarter = 'Q1' | 'Q2' | 'Q3' | 'Q4';

interface TDSReturn {
  id: string;
  return_type: ReturnType;
  financial_year: string;
  quarter: Quarter;
  period_from: string;
  period_to: string;
  due_date: string;
  status: ReturnStatus;
  is_original: boolean;
  revision_number: number;
  deductor_tan: string;
  deductor_name: string;
  total_challans: number;
  total_deductees: number;
  total_amount_paid: number;
  total_tds_deducted: number;
  total_tds_deposited: number;
  is_late: boolean;
  days_late: number;
  acknowledgment_number?: string;
  filed_date?: string;
  file_name?: string;
}

// Mock data
const tdsReturnsSummary = {
  total_returns: 12,
  pending_filing: 3,
  filed_this_quarter: 4,
  overdue: 1,
};

const tdsReturns: TDSReturn[] = [
  {
    id: '1',
    return_type: 'FORM_26Q',
    financial_year: '2024-25',
    quarter: 'Q3',
    period_from: '2024-10-01',
    period_to: '2024-12-31',
    due_date: '2025-01-31',
    status: 'DRAFT',
    is_original: true,
    revision_number: 0,
    deductor_tan: 'DELH12345A',
    deductor_name: 'ABC Finance Ltd',
    total_challans: 5,
    total_deductees: 45,
    total_amount_paid: 15000000,
    total_tds_deducted: 1500000,
    total_tds_deposited: 1500000,
    is_late: false,
    days_late: 0,
  },
  {
    id: '2',
    return_type: 'FORM_27Q',
    financial_year: '2024-25',
    quarter: 'Q3',
    period_from: '2024-10-01',
    period_to: '2024-12-31',
    due_date: '2025-01-31',
    status: 'VALIDATED',
    is_original: true,
    revision_number: 0,
    deductor_tan: 'DELH12345A',
    deductor_name: 'ABC Finance Ltd',
    total_challans: 2,
    total_deductees: 8,
    total_amount_paid: 5000000,
    total_tds_deducted: 500000,
    total_tds_deposited: 500000,
    is_late: false,
    days_late: 0,
  },
  {
    id: '3',
    return_type: 'FORM_26Q',
    financial_year: '2024-25',
    quarter: 'Q2',
    period_from: '2024-07-01',
    period_to: '2024-09-30',
    due_date: '2024-10-31',
    status: 'FILED',
    is_original: true,
    revision_number: 0,
    deductor_tan: 'DELH12345A',
    deductor_name: 'ABC Finance Ltd',
    total_challans: 6,
    total_deductees: 52,
    total_amount_paid: 18000000,
    total_tds_deducted: 1800000,
    total_tds_deposited: 1800000,
    is_late: false,
    days_late: 0,
    acknowledgment_number: 'TDS123456789',
    filed_date: '2024-10-28',
  },
  {
    id: '4',
    return_type: 'FORM_26Q',
    financial_year: '2024-25',
    quarter: 'Q1',
    period_from: '2024-04-01',
    period_to: '2024-06-30',
    due_date: '2024-07-31',
    status: 'ACCEPTED',
    is_original: true,
    revision_number: 0,
    deductor_tan: 'DELH12345A',
    deductor_name: 'ABC Finance Ltd',
    total_challans: 4,
    total_deductees: 38,
    total_amount_paid: 12000000,
    total_tds_deducted: 1200000,
    total_tds_deposited: 1200000,
    is_late: false,
    days_late: 0,
    acknowledgment_number: 'TDS123456788',
    filed_date: '2024-07-25',
  },
  {
    id: '5',
    return_type: 'FORM_26Q',
    financial_year: '2024-25',
    quarter: 'Q1',
    period_from: '2024-04-01',
    period_to: '2024-06-30',
    due_date: '2024-07-31',
    status: 'FILED',
    is_original: false,
    revision_number: 1,
    deductor_tan: 'DELH12345A',
    deductor_name: 'ABC Finance Ltd',
    total_challans: 5,
    total_deductees: 40,
    total_amount_paid: 12500000,
    total_tds_deducted: 1250000,
    total_tds_deposited: 1250000,
    is_late: true,
    days_late: 15,
    acknowledgment_number: 'TDS123456790',
    filed_date: '2024-08-15',
  },
];

const getStatusBadge = (status: ReturnStatus) => {
  const statusConfig: Record<ReturnStatus, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ReactNode; label: string }> = {
    DRAFT: { variant: 'secondary', icon: <FileText className="h-3 w-3 mr-1" />, label: 'Draft' },
    VALIDATED: { variant: 'outline', icon: <CheckCircle className="h-3 w-3 mr-1" />, label: 'Validated' },
    GENERATED: { variant: 'outline', icon: <Download className="h-3 w-3 mr-1" />, label: 'Generated' },
    UPLOADED: { variant: 'outline', icon: <Upload className="h-3 w-3 mr-1" />, label: 'Uploaded' },
    FILED: { variant: 'default', icon: <CheckCircle className="h-3 w-3 mr-1" />, label: 'Filed' },
    ACCEPTED: { variant: 'default', icon: <CheckCircle className="h-3 w-3 mr-1" />, label: 'Accepted' },
    REJECTED: { variant: 'destructive', icon: <XCircle className="h-3 w-3 mr-1" />, label: 'Rejected' },
    REVISED: { variant: 'secondary', icon: <RefreshCw className="h-3 w-3 mr-1" />, label: 'Revised' },
  };

  const config = statusConfig[status];
  return (
    <Badge variant={config.variant} className="flex items-center w-fit">
      {config.icon}
      {config.label}
    </Badge>
  );
};

const getReturnTypeLabel = (type: ReturnType) => {
  const labels: Record<ReturnType, string> = {
    FORM_26Q: 'Form 26Q (Non-Salary)',
    FORM_27Q: 'Form 27Q (Non-Resident)',
    FORM_27EQ: 'Form 27EQ (TCS)',
  };
  return labels[type];
};

const getQuarterLabel = (quarter: Quarter) => {
  const labels: Record<Quarter, string> = {
    Q1: 'Q1 (Apr-Jun)',
    Q2: 'Q2 (Jul-Sep)',
    Q3: 'Q3 (Oct-Dec)',
    Q4: 'Q4 (Jan-Mar)',
  };
  return labels[quarter];
};

export default function TDSReturnList() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [quarterFilter, setQuarterFilter] = useState('all');

  const filteredReturns = tdsReturns.filter((r) => {
    const matchesSearch =
      r.financial_year.includes(searchTerm) ||
      r.deductor_tan.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.acknowledgment_number?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = typeFilter === 'all' || r.return_type === typeFilter;
    const matchesStatus = statusFilter === 'all' || r.status === statusFilter;
    const matchesQuarter = quarterFilter === 'all' || r.quarter === quarterFilter;
    return matchesSearch && matchesType && matchesStatus && matchesQuarter;
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="TDS Returns"
        subtitle="Manage TDS return filing and compliance"
        actions={
          <Button onClick={() => navigate('/tds/returns/create')}>
            <Plus className="h-4 w-4 mr-2" />
            Create Return
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Returns
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{tdsReturnsSummary.total_returns}</div>
            <p className="text-xs text-muted-foreground">This financial year</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Pending Filing
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-yellow-600">
              {tdsReturnsSummary.pending_filing}
            </div>
            <p className="text-xs text-muted-foreground">Awaiting submission</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Filed This Quarter
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {tdsReturnsSummary.filed_this_quarter}
            </div>
            <p className="text-xs text-muted-foreground">Successfully submitted</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Overdue</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-600">
              {tdsReturnsSummary.overdue}
            </div>
            <p className="text-xs text-muted-foreground">Past due date</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4 flex-wrap">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by year, TAN, acknowledgment..."
                className="pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Return Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="FORM_26Q">Form 26Q</SelectItem>
                <SelectItem value="FORM_27Q">Form 27Q</SelectItem>
                <SelectItem value="FORM_27EQ">Form 27EQ</SelectItem>
              </SelectContent>
            </Select>
            <Select value={quarterFilter} onValueChange={setQuarterFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Quarter" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Quarters</SelectItem>
                <SelectItem value="Q1">Q1 (Apr-Jun)</SelectItem>
                <SelectItem value="Q2">Q2 (Jul-Sep)</SelectItem>
                <SelectItem value="Q3">Q3 (Oct-Dec)</SelectItem>
                <SelectItem value="Q4">Q4 (Jan-Mar)</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="DRAFT">Draft</SelectItem>
                <SelectItem value="VALIDATED">Validated</SelectItem>
                <SelectItem value="GENERATED">Generated</SelectItem>
                <SelectItem value="FILED">Filed</SelectItem>
                <SelectItem value="ACCEPTED">Accepted</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Returns Table */}
      <Card>
        <CardHeader>
          <CardTitle>TDS Returns</CardTitle>
          <CardDescription>{filteredReturns.length} returns found</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Return Type</TableHead>
                <TableHead>Period</TableHead>
                <TableHead>Due Date</TableHead>
                <TableHead className="text-right">TDS Deducted</TableHead>
                <TableHead className="text-right">TDS Deposited</TableHead>
                <TableHead className="text-center">Deductees</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredReturns.map((ret) => (
                <TableRow key={ret.id}>
                  <TableCell>
                    <div className="font-medium">
                      {getReturnTypeLabel(ret.return_type)}
                      {!ret.is_original && (
                        <Badge variant="outline" className="ml-2">
                          Rev {ret.revision_number}
                        </Badge>
                      )}
                    </div>
                    <div className="text-sm text-muted-foreground">TAN: {ret.deductor_tan}</div>
                  </TableCell>
                  <TableCell>
                    <div className="font-medium">{ret.financial_year}</div>
                    <div className="text-sm text-muted-foreground">
                      {getQuarterLabel(ret.quarter)}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <div>{formatDate(ret.due_date)}</div>
                        {ret.is_late && (
                          <div className="text-xs text-red-600 flex items-center gap-1">
                            <AlertTriangle className="h-3 w-3" />
                            {ret.days_late} days late
                          </div>
                        )}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(ret.total_tds_deducted)}
                  </TableCell>
                  <TableCell className="text-right">
                    <div
                      className={
                        ret.total_tds_deposited < ret.total_tds_deducted
                          ? 'text-red-600 font-medium'
                          : 'text-green-600 font-medium'
                      }
                    >
                      {formatCurrency(ret.total_tds_deposited)}
                    </div>
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge variant="secondary">{ret.total_deductees}</Badge>
                  </TableCell>
                  <TableCell>{getStatusBadge(ret.status)}</TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          ...
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => navigate(`/tds/returns/${ret.id}`)}>
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        {ret.status === 'DRAFT' && (
                          <DropdownMenuItem onClick={() => navigate(`/tds/returns/${ret.id}/edit`)}>
                            <FileText className="h-4 w-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                        )}
                        {['DRAFT', 'VALIDATED'].includes(ret.status) && (
                          <DropdownMenuItem>
                            <CheckCircle className="h-4 w-4 mr-2" />
                            Validate
                          </DropdownMenuItem>
                        )}
                        {ret.status === 'VALIDATED' && (
                          <DropdownMenuItem>
                            <Download className="h-4 w-4 mr-2" />
                            Generate File
                          </DropdownMenuItem>
                        )}
                        {ret.file_name && (
                          <DropdownMenuItem>
                            <Download className="h-4 w-4 mr-2" />
                            Download File
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuSeparator />
                        {['FILED', 'ACCEPTED'].includes(ret.status) && ret.is_original && (
                          <DropdownMenuItem>
                            <RefreshCw className="h-4 w-4 mr-2" />
                            Create Revision
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
