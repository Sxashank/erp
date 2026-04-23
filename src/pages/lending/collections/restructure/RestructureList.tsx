import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Filter, MoreHorizontal, Eye, CheckCircle, Clock, FileText, RefreshCw } from 'lucide-react';
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
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';

interface LoanRestructure {
  id: string;
  restructureReference: string;
  loanAccountNumber: string;
  entityName: string;
  restructureType: 'TENURE_EXTENSION' | 'EMI_REDUCTION' | 'MORATORIUM' | 'RATE_REDUCTION' | 'PRINCIPAL_HAIRCUT' | 'INTEREST_WAIVER' | 'COMPREHENSIVE' | 'COVID_RESTRUCTURE';
  preOutstandingPrincipal: number;
  postOutstandingPrincipal: number;
  preInterestRate: number;
  postInterestRate: number;
  preTenureMonths: number;
  postTenureMonths: number;
  moratoriumMonths: number;
  interestWaived: number;
  penalWaived: number;
  proposalDate: string;
  postMaturityDate: string;
  status: 'DRAFT' | 'PROPOSED' | 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'IMPLEMENTED' | 'CANCELLED';
  approvalAuthority: string | null;
  justification: string;
}

// Mock data
const mockRestructures: LoanRestructure[] = [
  {
    id: '1',
    restructureReference: 'RESTR/2025/00001',
    loanAccountNumber: 'SMFC/TL/CHN/2023/L00034',
    entityName: 'Southern Motors Corp',
    restructureType: 'COMPREHENSIVE',
    preOutstandingPrincipal: 130250000,
    postOutstandingPrincipal: 130250000,
    preInterestRate: 12.5,
    postInterestRate: 11.0,
    preTenureMonths: 60,
    postTenureMonths: 84,
    moratoriumMonths: 6,
    interestWaived: 2500000,
    penalWaived: 750000,
    proposalDate: '2025-01-15',
    postMaturityDate: '2032-01-15',
    status: 'PENDING_APPROVAL',
    approvalAuthority: 'Credit Committee',
    justification: 'Borrower facing temporary cash flow issues due to delayed receivables',
  },
  {
    id: '2',
    restructureReference: 'RESTR/2024/00089',
    loanAccountNumber: 'SMFC/WC/KOL/2022/L00067',
    entityName: 'Eastern Trading Co',
    restructureType: 'TENURE_EXTENSION',
    preOutstandingPrincipal: 45000000,
    postOutstandingPrincipal: 45000000,
    preInterestRate: 13.0,
    postInterestRate: 13.0,
    preTenureMonths: 48,
    postTenureMonths: 60,
    moratoriumMonths: 0,
    interestWaived: 0,
    penalWaived: 500000,
    proposalDate: '2024-12-10',
    postMaturityDate: '2029-12-10',
    status: 'IMPLEMENTED',
    approvalAuthority: 'GM Credit',
    justification: 'Tenure extension to reduce EMI burden',
  },
  {
    id: '3',
    restructureReference: 'RESTR/2024/00078',
    loanAccountNumber: 'SMFC/LAP/HYD/2021/L00045',
    entityName: 'Deccan Enterprises',
    restructureType: 'MORATORIUM',
    preOutstandingPrincipal: 28500000,
    postOutstandingPrincipal: 28500000,
    preInterestRate: 11.5,
    postInterestRate: 11.5,
    preTenureMonths: 72,
    postTenureMonths: 78,
    moratoriumMonths: 6,
    interestWaived: 0,
    penalWaived: 0,
    proposalDate: '2024-11-01',
    postMaturityDate: '2030-05-01',
    status: 'APPROVED',
    approvalAuthority: 'Credit Committee',
    justification: 'COVID-19 impact - 6 month moratorium requested',
  },
  {
    id: '4',
    restructureReference: 'RESTR/2024/00065',
    loanAccountNumber: 'SMFC/TL/MUM/2022/L00023',
    entityName: 'Western Industries Ltd',
    restructureType: 'RATE_REDUCTION',
    preOutstandingPrincipal: 75000000,
    postOutstandingPrincipal: 75000000,
    preInterestRate: 14.0,
    postInterestRate: 12.0,
    preTenureMonths: 60,
    postTenureMonths: 60,
    moratoriumMonths: 0,
    interestWaived: 0,
    penalWaived: 0,
    proposalDate: '2024-10-15',
    postMaturityDate: '2029-10-15',
    status: 'REJECTED',
    approvalAuthority: null,
    justification: 'Rate reduction requested due to competitive market rates',
  },
];

const statusConfig: Record<string, { label: string; color: string; icon: React.ElementType }> = {
  DRAFT: { label: 'Draft', color: 'bg-gray-100 text-gray-700', icon: FileText },
  PROPOSED: { label: 'Proposed', color: 'bg-blue-100 text-blue-700', icon: FileText },
  PENDING_APPROVAL: { label: 'Pending Approval', color: 'bg-yellow-100 text-yellow-700', icon: Clock },
  APPROVED: { label: 'Approved', color: 'bg-green-100 text-green-700', icon: CheckCircle },
  REJECTED: { label: 'Rejected', color: 'bg-red-100 text-red-700', icon: Clock },
  IMPLEMENTED: { label: 'Implemented', color: 'bg-green-200 text-green-800', icon: CheckCircle },
  CANCELLED: { label: 'Cancelled', color: 'bg-gray-200 text-gray-700', icon: Clock },
};

const restructureTypeLabels: Record<string, string> = {
  TENURE_EXTENSION: 'Tenure Extension',
  EMI_REDUCTION: 'EMI Reduction',
  MORATORIUM: 'Moratorium',
  RATE_REDUCTION: 'Rate Reduction',
  PRINCIPAL_HAIRCUT: 'Principal Haircut',
  INTEREST_WAIVER: 'Interest Waiver',
  COMPREHENSIVE: 'Comprehensive',
  COVID_RESTRUCTURE: 'COVID Restructure',
};

export default function RestructureList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');

  const filteredRestructures = mockRestructures.filter((restructure) => {
    const matchesSearch =
      restructure.restructureReference.toLowerCase().includes(searchQuery.toLowerCase()) ||
      restructure.entityName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      restructure.loanAccountNumber.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || restructure.status === statusFilter;
    const matchesType = typeFilter === 'ALL' || restructure.restructureType === typeFilter;
    return matchesSearch && matchesStatus && matchesType;
  });

  const totalWaived = mockRestructures
    .filter((r) => ['APPROVED', 'IMPLEMENTED'].includes(r.status))
    .reduce((sum, r) => sum + r.interestWaived + r.penalWaived, 0);
  const pendingApproval = mockRestructures.filter((r) => r.status === 'PENDING_APPROVAL').length;
  const implementedCount = mockRestructures.filter((r) => r.status === 'IMPLEMENTED').length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Loan Restructuring"
        subtitle="Manage loan restructure proposals and implementations"
        actions={
          <Button onClick={() => navigate('/admin/lending/collections/restructure/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Restructure
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Proposals</CardTitle>
            <RefreshCw className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockRestructures.length}</div>
            <p className="text-xs text-muted-foreground">All restructure proposals</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Approval</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{pendingApproval}</div>
            <p className="text-xs text-muted-foreground">Awaiting decision</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Implemented</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{implementedCount}</div>
            <p className="text-xs text-muted-foreground">Successfully restructured</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Waived</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalWaived} format="abbreviated" className="text-2xl font-bold text-red-600" />
            <p className="text-xs text-muted-foreground">Interest + Penal waived</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by reference, entity, or loan account..."
                className="pl-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[180px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Status</SelectItem>
                  <SelectItem value="DRAFT">Draft</SelectItem>
                  <SelectItem value="PROPOSED">Proposed</SelectItem>
                  <SelectItem value="PENDING_APPROVAL">Pending Approval</SelectItem>
                  <SelectItem value="APPROVED">Approved</SelectItem>
                  <SelectItem value="REJECTED">Rejected</SelectItem>
                  <SelectItem value="IMPLEMENTED">Implemented</SelectItem>
                  <SelectItem value="CANCELLED">Cancelled</SelectItem>
                </SelectContent>
              </Select>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Types</SelectItem>
                  <SelectItem value="TENURE_EXTENSION">Tenure Extension</SelectItem>
                  <SelectItem value="EMI_REDUCTION">EMI Reduction</SelectItem>
                  <SelectItem value="MORATORIUM">Moratorium</SelectItem>
                  <SelectItem value="RATE_REDUCTION">Rate Reduction</SelectItem>
                  <SelectItem value="PRINCIPAL_HAIRCUT">Principal Haircut</SelectItem>
                  <SelectItem value="INTEREST_WAIVER">Interest Waiver</SelectItem>
                  <SelectItem value="COMPREHENSIVE">Comprehensive</SelectItem>
                  <SelectItem value="COVID_RESTRUCTURE">COVID Restructure</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Restructure Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Reference</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="text-right">Rate Change</TableHead>
                <TableHead className="text-right">Tenure Change</TableHead>
                <TableHead className="text-right">Moratorium</TableHead>
                <TableHead>Maturity</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredRestructures.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                    No restructure proposals found matching your criteria
                  </TableCell>
                </TableRow>
              ) : (
                filteredRestructures.map((restructure) => {
                  const status = statusConfig[restructure.status];
                  const StatusIcon = status.icon;
                  const rateChange = restructure.postInterestRate - restructure.preInterestRate;
                  const tenureChange = restructure.postTenureMonths - restructure.preTenureMonths;
                  return (
                    <TableRow
                      key={restructure.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => navigate(`/admin/lending/collections/restructure/${restructure.id}`)}
                    >
                      <TableCell>
                        <div className="font-mono text-sm">{restructure.restructureReference}</div>
                        <div className="text-xs text-muted-foreground">
                          {restructure.loanAccountNumber}
                        </div>
                      </TableCell>
                      <TableCell>{restructure.entityName}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {restructureTypeLabels[restructure.restructureType]}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex flex-col items-end">
                          <span className={rateChange < 0 ? 'text-green-600' : rateChange > 0 ? 'text-red-600' : ''}>
                            {restructure.preInterestRate}% → {restructure.postInterestRate}%
                          </span>
                          {rateChange !== 0 && (
                            <span className={`text-xs ${rateChange < 0 ? 'text-green-600' : 'text-red-600'}`}>
                              ({rateChange > 0 ? '+' : ''}{rateChange.toFixed(2)}%)
                            </span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex flex-col items-end">
                          <span>{restructure.preTenureMonths} → {restructure.postTenureMonths} mo</span>
                          {tenureChange !== 0 && (
                            <span className="text-xs text-muted-foreground">
                              ({tenureChange > 0 ? '+' : ''}{tenureChange} months)
                            </span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        {restructure.moratoriumMonths > 0 ? (
                          <Badge variant="secondary">{restructure.moratoriumMonths} months</Badge>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <DateDisplay date={restructure.postMaturityDate} />
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={status.color}>
                          <StatusIcon className="h-3 w-3 mr-1" />
                          {status.label}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/admin/lending/collections/restructure/${restructure.id}`);
                              }}
                            >
                              <Eye className="mr-2 h-4 w-4" />
                              View Details
                            </DropdownMenuItem>
                            {restructure.status === 'PENDING_APPROVAL' && (
                              <DropdownMenuItem
                                onClick={(e) => {
                                  e.stopPropagation();
                                  navigate(`/admin/lending/collections/restructure/${restructure.id}/approve`);
                                }}
                              >
                                <CheckCircle className="mr-2 h-4 w-4" />
                                Review & Approve
                              </DropdownMenuItem>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
