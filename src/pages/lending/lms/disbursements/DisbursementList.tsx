import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Filter, MoreHorizontal, Eye, CheckCircle, Clock } from 'lucide-react';
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
import { DateDisplay } from '@/components/lending/common/DateDisplay';

interface Disbursement {
  id: string;
  disbursementNumber: string;
  loanAccountNumber: string;
  entityName: string;
  tranche: number;
  amount: number;
  requestDate: string;
  disbursementDate: string | null;
  milestone: string;
  status: 'PENDING_APPROVAL' | 'APPROVED' | 'PROCESSING' | 'COMPLETED' | 'REJECTED';
  paymentMode: string;
  bankAccount: string;
}

// Mock data
const mockDisbursements: Disbursement[] = [
  {
    id: '1',
    disbursementNumber: 'DISB/2025/00001',
    loanAccountNumber: 'SMFC/TL/DEL/2025/L00001',
    entityName: 'ABC Industries Private Limited',
    tranche: 1,
    amount: 50000000,
    requestDate: '2025-01-18',
    disbursementDate: '2025-01-20',
    milestone: 'Land acquisition',
    status: 'COMPLETED',
    paymentMode: 'RTGS',
    bankAccount: 'HDFC Bank - xxxx1234',
  },
  {
    id: '2',
    disbursementNumber: 'DISB/2025/00002',
    loanAccountNumber: 'SMFC/TL/DEL/2025/L00001',
    entityName: 'ABC Industries Private Limited',
    tranche: 2,
    amount: 75000000,
    requestDate: '2025-01-25',
    disbursementDate: null,
    milestone: 'Civil construction - Phase 1',
    status: 'PENDING_APPROVAL',
    paymentMode: 'RTGS',
    bankAccount: 'HDFC Bank - xxxx1234',
  },
  {
    id: '3',
    disbursementNumber: 'DISB/2025/00003',
    loanAccountNumber: 'SMFC/LAP/BLR/2024/L00045',
    entityName: 'Tech Solutions India Pvt Ltd',
    tranche: 1,
    amount: 75000000,
    requestDate: '2024-03-08',
    disbursementDate: '2024-03-10',
    milestone: 'Full disbursement',
    status: 'COMPLETED',
    paymentMode: 'RTGS',
    bankAccount: 'ICICI Bank - xxxx5678',
  },
];

const statusConfig: Record<string, { label: string; variant: 'default' | 'secondary' | 'destructive'; icon: React.ElementType }> = {
  PENDING_APPROVAL: { label: 'Pending Approval', variant: 'secondary', icon: Clock },
  APPROVED: { label: 'Approved', variant: 'default', icon: CheckCircle },
  PROCESSING: { label: 'Processing', variant: 'secondary', icon: Clock },
  COMPLETED: { label: 'Completed', variant: 'default', icon: CheckCircle },
  REJECTED: { label: 'Rejected', variant: 'destructive', icon: Clock },
};

export default function DisbursementList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const filteredDisbursements = mockDisbursements.filter((disb) => {
    const matchesSearch =
      disb.disbursementNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
      disb.entityName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      disb.loanAccountNumber.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || disb.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const totalDisbursed = mockDisbursements
    .filter((d) => d.status === 'COMPLETED')
    .reduce((sum, d) => sum + d.amount, 0);
  const pendingAmount = mockDisbursements
    .filter((d) => ['PENDING_APPROVAL', 'APPROVED', 'PROCESSING'].includes(d.status))
    .reduce((sum, d) => sum + d.amount, 0);
  const pendingCount = mockDisbursements.filter((d) => d.status === 'PENDING_APPROVAL').length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Disbursements"
        subtitle="Manage disbursement requests and fund transfers"
        actions={
          <Button onClick={() => navigate('/admin/lending/disbursements/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Disbursement
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockDisbursements.length}</div>
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Disbursed</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalDisbursed} abbreviated className="text-2xl font-bold" />
            <p className="text-xs text-muted-foreground">Completed disbursements</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Amount</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={pendingAmount} abbreviated className="text-2xl font-bold" />
            <p className="text-xs text-muted-foreground">In pipeline</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Approval</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingCount}</div>
            <p className="text-xs text-muted-foreground">Requests awaiting approval</p>
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
                placeholder="Search by disbursement number, entity, or loan account..."
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
                  <SelectItem value="PENDING_APPROVAL">Pending Approval</SelectItem>
                  <SelectItem value="APPROVED">Approved</SelectItem>
                  <SelectItem value="PROCESSING">Processing</SelectItem>
                  <SelectItem value="COMPLETED">Completed</SelectItem>
                  <SelectItem value="REJECTED">Rejected</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Disbursements Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Disbursement #</TableHead>
                <TableHead>Loan Account</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Tranche</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead>Milestone</TableHead>
                <TableHead>Request Date</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredDisbursements.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                    No disbursements found matching your criteria
                  </TableCell>
                </TableRow>
              ) : (
                filteredDisbursements.map((disb) => {
                  const status = statusConfig[disb.status];
                  const StatusIcon = status.icon;
                  return (
                    <TableRow
                      key={disb.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => navigate(`/admin/lending/disbursements/${disb.id}`)}
                    >
                      <TableCell className="font-mono text-sm">{disb.disbursementNumber}</TableCell>
                      <TableCell className="font-mono text-sm">{disb.loanAccountNumber}</TableCell>
                      <TableCell>{disb.entityName}</TableCell>
                      <TableCell>
                        <Badge variant="outline">Tranche {disb.tranche}</Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={disb.amount} abbreviated />
                      </TableCell>
                      <TableCell>{disb.milestone}</TableCell>
                      <TableCell>
                        <DateDisplay date={disb.requestDate} />
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={status.variant}
                          className={
                            status.variant === 'default' ? 'bg-green-100 text-green-700' : ''
                          }
                        >
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
                                navigate(`/admin/lending/disbursements/${disb.id}`);
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
