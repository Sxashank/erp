import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, MoreHorizontal, Eye, FileText, Receipt, AlertTriangle } from 'lucide-react';
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
import { DPDBadge } from '@/components/lending/common/DPDBadge';

interface LoanAccount {
  id: string;
  loanAccountNumber: string;
  entityName: string;
  entityCode: string;
  productName: string;
  productCategory: string;
  sanctionedAmount: number;
  disbursedAmount: number;
  principalOutstanding: number;
  interestOutstanding: number;
  totalOutstanding: number;
  effectiveRate: number;
  nextDueDate: string;
  nextDueAmount: number;
  dpd: number;
  assetClassification: string;
  status: 'ACTIVE' | 'CLOSED' | 'NPA' | 'WRITTEN_OFF';
  disbursementDate: string;
  maturityDate: string;
}

// Mock data
const mockLoanAccounts: LoanAccount[] = [
  {
    id: '1',
    loanAccountNumber: 'SMFC/TL/DEL/2025/L00001',
    entityName: 'ABC Industries Private Limited',
    entityCode: 'ENT/2025/00001',
    productName: 'Corporate Term Loan',
    productCategory: 'TERM_LOAN',
    sanctionedAmount: 250000000,
    disbursedAmount: 50000000,
    principalOutstanding: 48500000,
    interestOutstanding: 520000,
    totalOutstanding: 49020000,
    effectiveRate: 12.5,
    nextDueDate: '2025-02-15',
    nextDueAmount: 1250000,
    dpd: 0,
    assetClassification: 'STANDARD',
    status: 'ACTIVE',
    disbursementDate: '2025-01-20',
    maturityDate: '2030-01-20',
  },
  {
    id: '2',
    loanAccountNumber: 'SMFC/WC/MUM/2024/L00089',
    entityName: 'XYZ Traders LLP',
    entityCode: 'ENT/2024/00056',
    productName: 'SME Working Capital',
    productCategory: 'WORKING_CAPITAL',
    sanctionedAmount: 50000000,
    disbursedAmount: 50000000,
    principalOutstanding: 42000000,
    interestOutstanding: 0,
    totalOutstanding: 42000000,
    effectiveRate: 13.5,
    nextDueDate: '2025-02-01',
    nextDueAmount: 2250000,
    dpd: 15,
    assetClassification: 'SMA_0',
    status: 'ACTIVE',
    disbursementDate: '2024-06-15',
    maturityDate: '2026-06-15',
  },
  {
    id: '3',
    loanAccountNumber: 'SMFC/LAP/BLR/2024/L00045',
    entityName: 'Tech Solutions India Pvt Ltd',
    entityCode: 'ENT/2024/00025',
    productName: 'Loan Against Property',
    productCategory: 'LAP',
    sanctionedAmount: 75000000,
    disbursedAmount: 75000000,
    principalOutstanding: 68500000,
    interestOutstanding: 850000,
    totalOutstanding: 69350000,
    effectiveRate: 14.0,
    nextDueDate: '2025-01-25',
    nextDueAmount: 980000,
    dpd: 45,
    assetClassification: 'SMA_1',
    status: 'ACTIVE',
    disbursementDate: '2024-03-10',
    maturityDate: '2034-03-10',
  },
  {
    id: '4',
    loanAccountNumber: 'SMFC/TL/CHN/2023/L00034',
    entityName: 'Southern Motors Corp',
    entityCode: 'ENT/2023/00089',
    productName: 'Corporate Term Loan',
    productCategory: 'TERM_LOAN',
    sanctionedAmount: 150000000,
    disbursedAmount: 150000000,
    principalOutstanding: 125000000,
    interestOutstanding: 5250000,
    totalOutstanding: 130250000,
    effectiveRate: 12.75,
    nextDueDate: '2024-11-15',
    nextDueAmount: 2850000,
    dpd: 95,
    assetClassification: 'SUB_STANDARD',
    status: 'NPA',
    disbursementDate: '2023-05-20',
    maturityDate: '2030-05-20',
  },
];

export default function LoanAccountList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [classificationFilter, setClassificationFilter] = useState<string>('ALL');

  const filteredAccounts = mockLoanAccounts.filter((account) => {
    const matchesSearch =
      account.loanAccountNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
      account.entityName.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || account.status === statusFilter;
    const matchesClassification =
      classificationFilter === 'ALL' || account.assetClassification === classificationFilter;
    return matchesSearch && matchesStatus && matchesClassification;
  });

  const totalAUM = mockLoanAccounts.reduce((sum, a) => sum + a.totalOutstanding, 0);
  const totalDisbursed = mockLoanAccounts.reduce((sum, a) => sum + a.disbursedAmount, 0);
  const npaAccounts = mockLoanAccounts.filter((a) => a.status === 'NPA').length;
  const smaAccounts = mockLoanAccounts.filter((a) =>
    ['SMA_0', 'SMA_1', 'SMA_2'].includes(a.assetClassification)
  ).length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Loan Accounts"
        subtitle="Manage active loan accounts, schedules, and statements"
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total AUM</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalAUM} abbreviated className="text-2xl font-bold" />
            <p className="text-xs text-muted-foreground">
              {mockLoanAccounts.length} active accounts
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Disbursed</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalDisbursed} abbreviated className="text-2xl font-bold" />
            <p className="text-xs text-muted-foreground">Cumulative disbursement</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">SMA Accounts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{smaAccounts}</div>
            <p className="text-xs text-muted-foreground">Requires attention</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">NPA Accounts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{npaAccounts}</div>
            <p className="text-xs text-muted-foreground">Non-performing assets</p>
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
                placeholder="Search by loan account number or entity name..."
                className="pl-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[150px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Status</SelectItem>
                  <SelectItem value="ACTIVE">Active</SelectItem>
                  <SelectItem value="NPA">NPA</SelectItem>
                  <SelectItem value="CLOSED">Closed</SelectItem>
                  <SelectItem value="WRITTEN_OFF">Written Off</SelectItem>
                </SelectContent>
              </Select>
              <Select value={classificationFilter} onValueChange={setClassificationFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Classification" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Classifications</SelectItem>
                  <SelectItem value="STANDARD">Standard</SelectItem>
                  <SelectItem value="SMA_0">SMA-0 (1-30 DPD)</SelectItem>
                  <SelectItem value="SMA_1">SMA-1 (31-60 DPD)</SelectItem>
                  <SelectItem value="SMA_2">SMA-2 (61-90 DPD)</SelectItem>
                  <SelectItem value="SUB_STANDARD">Sub-Standard</SelectItem>
                  <SelectItem value="DOUBTFUL">Doubtful</SelectItem>
                  <SelectItem value="LOSS">Loss</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Loan Accounts Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Loan Account</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Product</TableHead>
                <TableHead className="text-right">Outstanding</TableHead>
                <TableHead className="text-right">Rate</TableHead>
                <TableHead>Next Due</TableHead>
                <TableHead>DPD</TableHead>
                <TableHead>Classification</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAccounts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                    No loan accounts found matching your criteria
                  </TableCell>
                </TableRow>
              ) : (
                filteredAccounts.map((account) => (
                  <TableRow
                    key={account.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => navigate(`/admin/lending/accounts/${account.id}`)}
                  >
                    <TableCell>
                      <div className="font-mono text-sm">{account.loanAccountNumber}</div>
                      <div className="text-xs text-muted-foreground">
                        Maturity: <DateDisplay date={account.maturityDate} />
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="font-medium">{account.entityName}</div>
                      <div className="text-xs text-muted-foreground">{account.entityCode}</div>
                    </TableCell>
                    <TableCell>
                      <div>{account.productName}</div>
                    </TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={account.totalOutstanding} abbreviated />
                      <div className="text-xs text-muted-foreground">
                        of <AmountDisplay amount={account.sanctionedAmount} abbreviated />
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <PercentageDisplay value={account.effectiveRate} /> p.a.
                    </TableCell>
                    <TableCell>
                      <DateDisplay date={account.nextDueDate} />
                      <div className="text-xs text-muted-foreground">
                        <AmountDisplay amount={account.nextDueAmount} abbreviated />
                      </div>
                    </TableCell>
                    <TableCell>
                      <DPDBadge dpd={account.dpd} />
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={account.assetClassification} type="classification" />
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
                              navigate(`/admin/lending/accounts/${account.id}`);
                            }}
                          >
                            <Eye className="mr-2 h-4 w-4" />
                            View Account
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/admin/lending/accounts/${account.id}/statement`);
                            }}
                          >
                            <FileText className="mr-2 h-4 w-4" />
                            Statement of Account
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/admin/lending/receipts/new?accountId=${account.id}`);
                            }}
                          >
                            <Receipt className="mr-2 h-4 w-4" />
                            Record Receipt
                          </DropdownMenuItem>
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
