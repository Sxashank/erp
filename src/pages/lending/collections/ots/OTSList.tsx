import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Filter, MoreHorizontal, Eye, CheckCircle, Clock, FileText } from 'lucide-react';
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

interface OTSProposal {
  id: string;
  otsNumber: string;
  loanAccountNumber: string;
  entityName: string;
  totalOutstanding: number;
  settlementAmount: number;
  discountPercent: number;
  haircut: number;
  paymentMode: 'LUMPSUM' | 'STRUCTURED';
  proposedDate: string;
  validUntil: string;
  status: 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'ACCEPTED' | 'COMPLETED' | 'REJECTED' | 'EXPIRED';
  approvalAuthority: string;
  remarks: string | null;
}

// Mock data
const mockOTSProposals: OTSProposal[] = [
  {
    id: '1',
    otsNumber: 'OTS/2025/00001',
    loanAccountNumber: 'SMFC/TL/CHN/2023/L00034',
    entityName: 'Southern Motors Corp',
    totalOutstanding: 130250000,
    settlementAmount: 91175000,
    discountPercent: 30,
    haircut: 39075000,
    paymentMode: 'STRUCTURED',
    proposedDate: '2025-01-20',
    validUntil: '2025-04-20',
    status: 'PENDING_APPROVAL',
    approvalAuthority: 'Credit Committee',
    remarks: 'Borrower facing financial stress due to market conditions',
  },
  {
    id: '2',
    otsNumber: 'OTS/2024/00089',
    loanAccountNumber: 'SMFC/WC/KOL/2022/L00067',
    entityName: 'Eastern Trading Co',
    totalOutstanding: 45000000,
    settlementAmount: 36000000,
    discountPercent: 20,
    haircut: 9000000,
    paymentMode: 'LUMPSUM',
    proposedDate: '2024-12-15',
    validUntil: '2025-03-15',
    status: 'APPROVED',
    approvalAuthority: 'GM Credit',
    remarks: 'Strong recovery prospects through settlement',
  },
  {
    id: '3',
    otsNumber: 'OTS/2024/00078',
    loanAccountNumber: 'SMFC/LAP/HYD/2021/L00045',
    entityName: 'Deccan Enterprises',
    totalOutstanding: 28500000,
    settlementAmount: 19950000,
    discountPercent: 30,
    haircut: 8550000,
    paymentMode: 'STRUCTURED',
    proposedDate: '2024-11-01',
    validUntil: '2025-02-01',
    status: 'COMPLETED',
    approvalAuthority: 'Credit Committee',
    remarks: 'Settlement completed with 70% recovery',
  },
];

const statusConfig: Record<string, { label: string; color: string; icon: React.ElementType }> = {
  DRAFT: { label: 'Draft', color: 'bg-gray-100 text-gray-700', icon: FileText },
  PENDING_APPROVAL: { label: 'Pending Approval', color: 'bg-yellow-100 text-yellow-700', icon: Clock },
  APPROVED: { label: 'Approved', color: 'bg-blue-100 text-blue-700', icon: CheckCircle },
  ACCEPTED: { label: 'Accepted', color: 'bg-green-100 text-green-700', icon: CheckCircle },
  COMPLETED: { label: 'Completed', color: 'bg-green-200 text-green-800', icon: CheckCircle },
  REJECTED: { label: 'Rejected', color: 'bg-red-100 text-red-700', icon: Clock },
  EXPIRED: { label: 'Expired', color: 'bg-gray-200 text-gray-700', icon: Clock },
};

export default function OTSList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const filteredProposals = mockOTSProposals.filter((proposal) => {
    const matchesSearch =
      proposal.otsNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
      proposal.entityName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      proposal.loanAccountNumber.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || proposal.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const totalSettlement = mockOTSProposals
    .filter((p) => ['APPROVED', 'ACCEPTED', 'COMPLETED'].includes(p.status))
    .reduce((sum, p) => sum + p.settlementAmount, 0);
  const totalHaircut = mockOTSProposals
    .filter((p) => ['APPROVED', 'ACCEPTED', 'COMPLETED'].includes(p.status))
    .reduce((sum, p) => sum + p.haircut, 0);
  const pendingApproval = mockOTSProposals.filter((p) => p.status === 'PENDING_APPROVAL').length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="OTS Proposals"
        subtitle="Manage one-time settlement proposals for NPA recovery"
        actions={
          <Button onClick={() => navigate('/admin/lending/collections/ots/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New OTS Proposal
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Proposals</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockOTSProposals.length}</div>
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Settlement Value</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalSettlement} abbreviated className="text-2xl font-bold text-green-600" />
            <p className="text-xs text-muted-foreground">Approved/Completed</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Haircut</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalHaircut} abbreviated className="text-2xl font-bold text-red-600" />
            <p className="text-xs text-muted-foreground">Write-off amount</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Approval</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingApproval}</div>
            <p className="text-xs text-muted-foreground">Awaiting decision</p>
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
                placeholder="Search by OTS number, entity, or loan account..."
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
                  <SelectItem value="PENDING_APPROVAL">Pending Approval</SelectItem>
                  <SelectItem value="APPROVED">Approved</SelectItem>
                  <SelectItem value="ACCEPTED">Accepted</SelectItem>
                  <SelectItem value="COMPLETED">Completed</SelectItem>
                  <SelectItem value="REJECTED">Rejected</SelectItem>
                  <SelectItem value="EXPIRED">Expired</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* OTS Proposals Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>OTS Number</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead className="text-right">Outstanding</TableHead>
                <TableHead className="text-right">Settlement</TableHead>
                <TableHead className="text-right">Discount</TableHead>
                <TableHead>Payment</TableHead>
                <TableHead>Valid Until</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredProposals.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                    No OTS proposals found matching your criteria
                  </TableCell>
                </TableRow>
              ) : (
                filteredProposals.map((proposal) => {
                  const status = statusConfig[proposal.status];
                  const StatusIcon = status.icon;
                  return (
                    <TableRow
                      key={proposal.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => navigate(`/admin/lending/collections/ots/${proposal.id}`)}
                    >
                      <TableCell>
                        <div className="font-mono text-sm">{proposal.otsNumber}</div>
                        <div className="text-xs text-muted-foreground">
                          {proposal.loanAccountNumber}
                        </div>
                      </TableCell>
                      <TableCell>{proposal.entityName}</TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={proposal.totalOutstanding} abbreviated />
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={proposal.settlementAmount} abbreviated />
                      </TableCell>
                      <TableCell className="text-right">
                        <PercentageDisplay value={proposal.discountPercent} />
                        <div className="text-xs text-red-600">
                          Haircut: <AmountDisplay amount={proposal.haircut} abbreviated />
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {proposal.paymentMode === 'LUMPSUM' ? 'Lumpsum' : 'Structured'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <DateDisplay date={proposal.validUntil} />
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
                                navigate(`/admin/lending/collections/ots/${proposal.id}`);
                              }}
                            >
                              <Eye className="mr-2 h-4 w-4" />
                              View Details
                            </DropdownMenuItem>
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
