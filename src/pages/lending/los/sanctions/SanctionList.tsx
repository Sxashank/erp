import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Filter, MoreHorizontal, Eye, Edit, FileText, Printer } from 'lucide-react';
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
import { StatusBadge } from '@/components/lending/common/StatusBadge';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';

interface Sanction {
  id: string;
  sanctionNumber: string;
  applicationNumber: string;
  entityName: string;
  entityCode: string;
  productName: string;
  sanctionedAmount: number;
  interestRate: number;
  tenureMonths: number;
  sanctionDate: string;
  validUntil: string;
  status: 'PENDING_ACCEPTANCE' | 'ACCEPTED' | 'EXPIRED' | 'DISBURSED' | 'CANCELLED';
  disbursedAmount: number;
  approvedBy: string;
}

// Mock data
const mockSanctions: Sanction[] = [
  {
    id: '1',
    sanctionNumber: 'SMFC/SAN/2025/00001',
    applicationNumber: 'SMFC/TL/DEL/2025/A00001',
    entityName: 'ABC Industries Private Limited',
    entityCode: 'ENT/2025/00001',
    productName: 'Corporate Term Loan',
    sanctionedAmount: 250000000,
    interestRate: 12.5,
    tenureMonths: 60,
    sanctionDate: '2025-01-10',
    validUntil: '2025-04-10',
    status: 'ACCEPTED',
    disbursedAmount: 50000000,
    approvedBy: 'Credit Committee',
  },
  {
    id: '2',
    sanctionNumber: 'SMFC/SAN/2025/00002',
    applicationNumber: 'SMFC/WC/MUM/2025/A00015',
    entityName: 'XYZ Traders LLP',
    entityCode: 'ENT/2025/00012',
    productName: 'SME Working Capital',
    sanctionedAmount: 50000000,
    interestRate: 13.5,
    tenureMonths: 24,
    sanctionDate: '2025-01-08',
    validUntil: '2025-04-08',
    status: 'PENDING_ACCEPTANCE',
    disbursedAmount: 0,
    approvedBy: 'GM Credit',
  },
  {
    id: '3',
    sanctionNumber: 'SMFC/SAN/2025/00003',
    applicationNumber: 'SMFC/LAP/BLR/2025/A00023',
    entityName: 'Tech Solutions India Pvt Ltd',
    entityCode: 'ENT/2025/00025',
    productName: 'Loan Against Property',
    sanctionedAmount: 75000000,
    interestRate: 14.0,
    tenureMonths: 120,
    sanctionDate: '2025-01-05',
    validUntil: '2025-04-05',
    status: 'DISBURSED',
    disbursedAmount: 75000000,
    approvedBy: 'AGM Credit',
  },
  {
    id: '4',
    sanctionNumber: 'SMFC/SAN/2024/00089',
    applicationNumber: 'SMFC/TL/CHN/2024/A00156',
    entityName: 'Southern Motors Corp',
    entityCode: 'ENT/2024/00089',
    productName: 'Corporate Term Loan',
    sanctionedAmount: 150000000,
    interestRate: 12.75,
    tenureMonths: 84,
    sanctionDate: '2024-10-15',
    validUntil: '2025-01-15',
    status: 'EXPIRED',
    disbursedAmount: 0,
    approvedBy: 'Credit Committee',
  },
];

export default function SanctionList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const filteredSanctions = mockSanctions.filter((sanction) => {
    const matchesSearch =
      sanction.sanctionNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sanction.entityName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sanction.applicationNumber.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || sanction.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const totalSanctioned = mockSanctions.reduce((sum, s) => sum + s.sanctionedAmount, 0);
  const totalDisbursed = mockSanctions.reduce((sum, s) => sum + s.disbursedAmount, 0);
  const pendingAcceptance = mockSanctions.filter((s) => s.status === 'PENDING_ACCEPTANCE').length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Loan Sanctions"
        subtitle="View and manage sanctioned loans, generate sanction letters"
        actions={
          <Button onClick={() => navigate('/admin/lending/sanctions/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Sanction
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sanctions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockSanctions.length}</div>
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sanctioned</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalSanctioned} abbreviated className="text-2xl font-bold" />
            <p className="text-xs text-muted-foreground">Across all sanctions</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Disbursed</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalDisbursed} abbreviated className="text-2xl font-bold" />
            <p className="text-xs text-muted-foreground">
              <PercentageDisplay value={(totalDisbursed / totalSanctioned) * 100} /> utilization
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Acceptance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingAcceptance}</div>
            <p className="text-xs text-muted-foreground">Awaiting borrower acceptance</p>
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
                placeholder="Search by sanction number, entity name, or application..."
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
                  <SelectItem value="PENDING_ACCEPTANCE">Pending Acceptance</SelectItem>
                  <SelectItem value="ACCEPTED">Accepted</SelectItem>
                  <SelectItem value="DISBURSED">Disbursed</SelectItem>
                  <SelectItem value="EXPIRED">Expired</SelectItem>
                  <SelectItem value="CANCELLED">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Sanctions Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Sanction Number</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Product</TableHead>
                <TableHead className="text-right">Sanctioned</TableHead>
                <TableHead className="text-right">Rate</TableHead>
                <TableHead>Tenure</TableHead>
                <TableHead>Sanction Date</TableHead>
                <TableHead>Valid Until</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredSanctions.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={10} className="text-center py-8 text-muted-foreground">
                    No sanctions found matching your criteria
                  </TableCell>
                </TableRow>
              ) : (
                filteredSanctions.map((sanction) => (
                  <TableRow
                    key={sanction.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => navigate(`/admin/lending/sanctions/${sanction.id}`)}
                  >
                    <TableCell className="font-mono text-sm">
                      {sanction.sanctionNumber}
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">{sanction.entityName}</div>
                        <div className="text-xs text-muted-foreground">{sanction.entityCode}</div>
                      </div>
                    </TableCell>
                    <TableCell>{sanction.productName}</TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={sanction.sanctionedAmount} abbreviated />
                      {sanction.disbursedAmount > 0 && (
                        <div className="text-xs text-muted-foreground">
                          Disbursed: <AmountDisplay amount={sanction.disbursedAmount} abbreviated />
                        </div>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <PercentageDisplay value={sanction.interestRate} /> p.a.
                    </TableCell>
                    <TableCell>{sanction.tenureMonths} months</TableCell>
                    <TableCell>
                      <DateDisplay date={sanction.sanctionDate} />
                    </TableCell>
                    <TableCell>
                      <DateDisplay date={sanction.validUntil} />
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={sanction.status} type="sanction" />
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
                              navigate(`/admin/lending/sanctions/${sanction.id}`);
                            }}
                          >
                            <Eye className="mr-2 h-4 w-4" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/admin/lending/sanctions/${sanction.id}/letter`);
                            }}
                          >
                            <FileText className="mr-2 h-4 w-4" />
                            Sanction Letter
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              window.print();
                            }}
                          >
                            <Printer className="mr-2 h-4 w-4" />
                            Print
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          {sanction.status === 'PENDING_ACCEPTANCE' && (
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/admin/lending/sanctions/${sanction.id}/edit`);
                              }}
                            >
                              <Edit className="mr-2 h-4 w-4" />
                              Edit Sanction
                            </DropdownMenuItem>
                          )}
                          {sanction.status === 'ACCEPTED' && (
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/admin/lending/disbursements/new?sanctionId=${sanction.id}`);
                              }}
                            >
                              <Plus className="mr-2 h-4 w-4" />
                              Create Disbursement
                            </DropdownMenuItem>
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
