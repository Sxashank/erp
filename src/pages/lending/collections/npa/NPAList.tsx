import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, MoreHorizontal, Eye, FileText, AlertTriangle, TrendingDown, TrendingUp } from 'lucide-react';
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

import { logger } from '@/lib/logger';
interface NPAAccount {
  id: string;
  loanAccountNumber: string;
  entityName: string;
  entityCode: string;
  productName: string;
  totalOutstanding: number;
  principalOutstanding: number;
  dpd: number;
  classification: string;
  npaDate: string;
  provisionRate: number;
  provisionAmount: number;
  recoveryAction: string;
  collectionOfficer: string;
}

// Mock data
const mockNPAAccounts: NPAAccount[] = [
  {
    id: '1',
    loanAccountNumber: 'SMFC/TL/CHN/2023/L00034',
    entityName: 'Southern Motors Corp',
    entityCode: 'ENT/2023/00089',
    productName: 'Corporate Term Loan',
    totalOutstanding: 130250000,
    principalOutstanding: 125000000,
    dpd: 95,
    classification: 'SUB_STANDARD',
    npaDate: '2024-11-15',
    provisionRate: 15,
    provisionAmount: 18750000,
    recoveryAction: 'OTS_PROPOSED',
    collectionOfficer: 'Amit Kumar',
  },
  {
    id: '2',
    loanAccountNumber: 'SMFC/WC/KOL/2022/L00067',
    entityName: 'Eastern Trading Co',
    entityCode: 'ENT/2022/00067',
    productName: 'Working Capital',
    totalOutstanding: 45000000,
    principalOutstanding: 42000000,
    dpd: 420,
    classification: 'DOUBTFUL_1',
    npaDate: '2023-12-01',
    provisionRate: 25,
    provisionAmount: 10500000,
    recoveryAction: 'LEGAL_SARFAESI',
    collectionOfficer: 'Priya Singh',
  },
  {
    id: '3',
    loanAccountNumber: 'SMFC/LAP/HYD/2021/L00045',
    entityName: 'Deccan Enterprises',
    entityCode: 'ENT/2021/00045',
    productName: 'Loan Against Property',
    totalOutstanding: 28500000,
    principalOutstanding: 25000000,
    dpd: 850,
    classification: 'DOUBTFUL_2',
    npaDate: '2022-08-15',
    provisionRate: 40,
    provisionAmount: 10000000,
    recoveryAction: 'LEGAL_DRT',
    collectionOfficer: 'Rahul Verma',
  },
  {
    id: '4',
    loanAccountNumber: 'SMFC/TL/PUN/2020/L00023',
    entityName: 'Western Industries Ltd',
    entityCode: 'ENT/2020/00023',
    productName: 'Term Loan',
    totalOutstanding: 85000000,
    principalOutstanding: 80000000,
    dpd: 1200,
    classification: 'DOUBTFUL_3',
    npaDate: '2021-05-20',
    provisionRate: 100,
    provisionAmount: 80000000,
    recoveryAction: 'WRITE_OFF_PROPOSED',
    collectionOfficer: 'Suresh Menon',
  },
];

const classificationColors: Record<string, string> = {
  SUB_STANDARD: 'bg-red-100 text-red-700',
  DOUBTFUL_1: 'bg-red-200 text-red-800',
  DOUBTFUL_2: 'bg-red-300 text-red-900',
  DOUBTFUL_3: 'bg-red-400 text-red-950',
  LOSS: 'bg-red-500 text-white',
};

const recoveryActionLabels: Record<string, string> = {
  FOLLOW_UP: 'Follow-up',
  OTS_PROPOSED: 'OTS Proposed',
  OTS_APPROVED: 'OTS Approved',
  RESTRUCTURE: 'Restructuring',
  LEGAL_SARFAESI: 'SARFAESI',
  LEGAL_DRT: 'DRT',
  LEGAL_NCLT: 'NCLT',
  WRITE_OFF_PROPOSED: 'Write-off Proposed',
  WRITTEN_OFF: 'Written Off',
};

export default function NPAList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [classificationFilter, setClassificationFilter] = useState<string>('ALL');

  const filteredAccounts = mockNPAAccounts.filter((account) => {
    const matchesSearch =
      account.loanAccountNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
      account.entityName.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesClassification =
      classificationFilter === 'ALL' || account.classification === classificationFilter;
    return matchesSearch && matchesClassification;
  });

  const totalNPA = mockNPAAccounts.reduce((sum, a) => sum + a.totalOutstanding, 0);
  const totalProvision = mockNPAAccounts.reduce((sum, a) => sum + a.provisionAmount, 0);
  const provisionCoverage = (totalProvision / totalNPA) * 100;

  return (
    <div className="space-y-6">
      <PageHeader
        title="NPA Accounts"
        subtitle="Manage non-performing assets, provisioning, and recovery actions"
        actions={
          <Button variant="outline" onClick={() => logger.debug('Run NPA identification')}>
            <AlertTriangle className="mr-2 h-4 w-4" />
            Run NPA Identification
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total NPA</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockNPAAccounts.length}</div>
            <p className="text-xs text-muted-foreground">Non-performing accounts</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Gross NPA</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalNPA} abbreviated className="text-2xl font-bold text-red-600" />
            <p className="text-xs text-muted-foreground">Total outstanding</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Provision</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalProvision} abbreviated className="text-2xl font-bold" />
            <p className="text-xs text-muted-foreground">As per IRAC norms</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Provision Coverage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              <PercentageDisplay value={provisionCoverage} />
            </div>
            <p className="text-xs text-muted-foreground">Coverage ratio</p>
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
                placeholder="Search by loan account or entity name..."
                className="pl-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Select value={classificationFilter} onValueChange={setClassificationFilter}>
                <SelectTrigger className="w-[180px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Classification" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Classifications</SelectItem>
                  <SelectItem value="SUB_STANDARD">Sub-Standard</SelectItem>
                  <SelectItem value="DOUBTFUL_1">Doubtful-1</SelectItem>
                  <SelectItem value="DOUBTFUL_2">Doubtful-2</SelectItem>
                  <SelectItem value="DOUBTFUL_3">Doubtful-3</SelectItem>
                  <SelectItem value="LOSS">Loss</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* NPA Accounts Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Loan Account</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead className="text-right">Outstanding</TableHead>
                <TableHead>DPD</TableHead>
                <TableHead>Classification</TableHead>
                <TableHead>NPA Date</TableHead>
                <TableHead className="text-right">Provision</TableHead>
                <TableHead>Recovery Action</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAccounts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                    No NPA accounts found matching your criteria
                  </TableCell>
                </TableRow>
              ) : (
                filteredAccounts.map((account) => (
                  <TableRow
                    key={account.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => navigate(`/admin/lending/collections/npa/${account.id}`)}
                  >
                    <TableCell>
                      <div className="font-mono text-sm">{account.loanAccountNumber}</div>
                      <div className="text-xs text-muted-foreground">{account.productName}</div>
                    </TableCell>
                    <TableCell>
                      <div className="font-medium">{account.entityName}</div>
                      <div className="text-xs text-muted-foreground">{account.entityCode}</div>
                    </TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={account.totalOutstanding} abbreviated />
                    </TableCell>
                    <TableCell>
                      <DPDBadge dpd={account.dpd} />
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={account.classification} type="classification" />
                    </TableCell>
                    <TableCell>
                      <DateDisplay date={account.npaDate} />
                    </TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={account.provisionAmount} abbreviated />
                      <div className="text-xs text-muted-foreground">
                        @ <PercentageDisplay value={account.provisionRate} />
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="inline-flex items-center rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700">
                        {recoveryActionLabels[account.recoveryAction]}
                      </span>
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
                              navigate(`/admin/lending/collections/npa/${account.id}`);
                            }}
                          >
                            <Eye className="mr-2 h-4 w-4" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(
                                `/admin/lending/collections/ots/new?accountId=${account.id}`
                              );
                            }}
                          >
                            <TrendingDown className="mr-2 h-4 w-4" />
                            Create OTS Proposal
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(
                                `/admin/lending/collections/legal/new?accountId=${account.id}`
                              );
                            }}
                          >
                            <FileText className="mr-2 h-4 w-4" />
                            Initiate Legal Action
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              logger.debug('Request upgrade:', account.id);
                            }}
                          >
                            <TrendingUp className="mr-2 h-4 w-4" />
                            Request Upgrade
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
