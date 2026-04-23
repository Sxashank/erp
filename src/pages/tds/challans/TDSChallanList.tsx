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
  Eye,
  Calendar,
  IndianRupee,
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
} from '@/components/ui/dropdown-menu';
import { formatCurrency, formatDate } from '@/lib/utils';

// Types
type ChallanStatus = 'PENDING' | 'PAID' | 'VERIFIED' | 'INCLUDED_IN_RETURN' | 'CANCELLED';
type PaymentMode = 'ONLINE' | 'BANK' | 'NEFT' | 'RTGS';

interface TDSChallan {
  id: string;
  challan_number: string;
  bsr_code: string;
  payment_date: string;
  deposit_date: string;
  section_codes: string[];
  payment_mode: PaymentMode;
  bank_name: string;
  branch_name: string;
  total_tds_amount: number;
  total_surcharge: number;
  total_cess: number;
  interest_amount: number;
  late_fee: number;
  total_amount: number;
  deductee_count: number;
  status: ChallanStatus;
  quarter: string;
  financial_year: string;
  return_id?: string;
  cin?: string;
  verified_at?: string;
}

// Mock data
const challanSummary = {
  total_challans: 45,
  total_deposited: 8500000,
  pending_verification: 3,
  this_quarter: 12,
};

const challans: TDSChallan[] = [
  {
    id: '1',
    challan_number: '23456',
    bsr_code: '0001234',
    payment_date: '2024-12-07',
    deposit_date: '2024-12-07',
    section_codes: ['194A', '194C'],
    payment_mode: 'ONLINE',
    bank_name: 'State Bank of India',
    branch_name: 'Connaught Place',
    total_tds_amount: 250000,
    total_surcharge: 0,
    total_cess: 10000,
    interest_amount: 0,
    late_fee: 0,
    total_amount: 260000,
    deductee_count: 15,
    status: 'VERIFIED',
    quarter: 'Q3',
    financial_year: '2024-25',
    cin: 'CIN123456789012345',
    verified_at: '2024-12-08',
  },
  {
    id: '2',
    challan_number: '23457',
    bsr_code: '0001234',
    payment_date: '2024-12-15',
    deposit_date: '2024-12-15',
    section_codes: ['194J'],
    payment_mode: 'NEFT',
    bank_name: 'HDFC Bank',
    branch_name: 'Nehru Place',
    total_tds_amount: 180000,
    total_surcharge: 0,
    total_cess: 7200,
    interest_amount: 0,
    late_fee: 0,
    total_amount: 187200,
    deductee_count: 8,
    status: 'PAID',
    quarter: 'Q3',
    financial_year: '2024-25',
    cin: 'CIN123456789012346',
  },
  {
    id: '3',
    challan_number: '23458',
    bsr_code: '0001234',
    payment_date: '2024-11-07',
    deposit_date: '2024-11-08',
    section_codes: ['194A'],
    payment_mode: 'ONLINE',
    bank_name: 'State Bank of India',
    branch_name: 'Connaught Place',
    total_tds_amount: 320000,
    total_surcharge: 0,
    total_cess: 12800,
    interest_amount: 5000,
    late_fee: 200,
    total_amount: 338000,
    deductee_count: 22,
    status: 'INCLUDED_IN_RETURN',
    quarter: 'Q3',
    financial_year: '2024-25',
    return_id: '1',
    cin: 'CIN123456789012347',
    verified_at: '2024-11-09',
  },
  {
    id: '4',
    challan_number: '',
    bsr_code: '',
    payment_date: '2024-12-20',
    deposit_date: '',
    section_codes: ['194C', '194H'],
    payment_mode: 'ONLINE',
    bank_name: '',
    branch_name: '',
    total_tds_amount: 150000,
    total_surcharge: 0,
    total_cess: 6000,
    interest_amount: 0,
    late_fee: 0,
    total_amount: 156000,
    deductee_count: 12,
    status: 'PENDING',
    quarter: 'Q3',
    financial_year: '2024-25',
  },
];

const getStatusBadge = (status: ChallanStatus) => {
  const statusConfig: Record<ChallanStatus, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ReactNode; label: string }> = {
    PENDING: { variant: 'secondary', icon: <Clock className="h-3 w-3 mr-1" />, label: 'Pending' },
    PAID: { variant: 'outline', icon: <IndianRupee className="h-3 w-3 mr-1" />, label: 'Paid' },
    VERIFIED: { variant: 'default', icon: <CheckCircle className="h-3 w-3 mr-1" />, label: 'Verified' },
    INCLUDED_IN_RETURN: { variant: 'default', icon: <FileText className="h-3 w-3 mr-1" />, label: 'In Return' },
    CANCELLED: { variant: 'destructive', icon: <AlertTriangle className="h-3 w-3 mr-1" />, label: 'Cancelled' },
  };

  const config = statusConfig[status];
  return (
    <Badge variant={config.variant} className="flex items-center w-fit">
      {config.icon}
      {config.label}
    </Badge>
  );
};

export default function TDSChallanList() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [quarterFilter, setQuarterFilter] = useState('all');

  const filteredChallans = challans.filter((c) => {
    const matchesSearch =
      c.challan_number.includes(searchTerm) ||
      c.bsr_code.includes(searchTerm) ||
      c.cin?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.section_codes.some((s) => s.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesStatus = statusFilter === 'all' || c.status === statusFilter;
    const matchesQuarter = quarterFilter === 'all' || c.quarter === quarterFilter;
    return matchesSearch && matchesStatus && matchesQuarter;
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="TDS Challans"
        subtitle="Track TDS deposits and challan payments"
        actions={
          <Button onClick={() => navigate('/tds/challans/create')}>
            <Plus className="h-4 w-4 mr-2" />
            Record Challan
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Challans
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{challanSummary.total_challans}</div>
            <p className="text-xs text-muted-foreground">This financial year</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Deposited
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {formatCurrency(challanSummary.total_deposited)}
            </div>
            <p className="text-xs text-muted-foreground">Including cess & interest</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Pending Verification
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-yellow-600">
              {challanSummary.pending_verification}
            </div>
            <p className="text-xs text-muted-foreground">Awaiting OLTAS verification</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              This Quarter
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{challanSummary.this_quarter}</div>
            <p className="text-xs text-muted-foreground">Q3 2024-25</p>
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
                placeholder="Search by challan no, BSR code, CIN, section..."
                className="pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
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
                <SelectItem value="PENDING">Pending</SelectItem>
                <SelectItem value="PAID">Paid</SelectItem>
                <SelectItem value="VERIFIED">Verified</SelectItem>
                <SelectItem value="INCLUDED_IN_RETURN">In Return</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Challans Table */}
      <Card>
        <CardHeader>
          <CardTitle>TDS Challans</CardTitle>
          <CardDescription>{filteredChallans.length} challans found</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Challan Details</TableHead>
                <TableHead>Payment Date</TableHead>
                <TableHead>Sections</TableHead>
                <TableHead className="text-right">TDS Amount</TableHead>
                <TableHead className="text-right">Total Amount</TableHead>
                <TableHead className="text-center">Deductees</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredChallans.map((challan) => (
                <TableRow key={challan.id}>
                  <TableCell>
                    <div className="font-medium">
                      {challan.challan_number ? (
                        <>
                          Challan #{challan.challan_number}
                          <div className="text-xs text-muted-foreground">
                            BSR: {challan.bsr_code}
                          </div>
                        </>
                      ) : (
                        <span className="text-muted-foreground">Not yet deposited</span>
                      )}
                    </div>
                    {challan.cin && (
                      <div className="text-xs text-muted-foreground mt-1">CIN: {challan.cin}</div>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <div>{formatDate(challan.payment_date)}</div>
                        {challan.bank_name && (
                          <div className="text-xs text-muted-foreground">
                            {challan.bank_name}
                          </div>
                        )}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {challan.section_codes.map((code) => (
                        <Badge key={code} variant="outline" className="text-xs">
                          {code}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(challan.total_tds_amount)}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="font-medium">{formatCurrency(challan.total_amount)}</div>
                    {(challan.interest_amount > 0 || challan.late_fee > 0) && (
                      <div className="text-xs text-yellow-600">
                        +Int: {formatCurrency(challan.interest_amount)}
                      </div>
                    )}
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge variant="secondary">{challan.deductee_count}</Badge>
                  </TableCell>
                  <TableCell>{getStatusBadge(challan.status)}</TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          ...
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => navigate(`/tds/challans/${challan.id}`)}>
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        {challan.status === 'PENDING' && (
                          <DropdownMenuItem>
                            <FileText className="h-4 w-4 mr-2" />
                            Update Payment
                          </DropdownMenuItem>
                        )}
                        {challan.status === 'PAID' && (
                          <DropdownMenuItem>
                            <CheckCircle className="h-4 w-4 mr-2" />
                            Verify with OLTAS
                          </DropdownMenuItem>
                        )}
                        {challan.cin && (
                          <DropdownMenuItem>
                            <Download className="h-4 w-4 mr-2" />
                            Download Receipt
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
