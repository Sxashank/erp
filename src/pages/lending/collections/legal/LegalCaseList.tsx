import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Filter, MoreHorizontal, Eye, Calendar, FileText, Scale } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
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

import { logger } from '@/lib/logger';
interface LegalCase {
  id: string;
  caseNumber: string;
  loanAccountNumber: string;
  entityName: string;
  caseType: 'SARFAESI' | 'DRT' | 'NCLT' | 'CIVIL' | 'ARBITRATION';
  forum: string;
  filingDate: string;
  claimAmount: number;
  status: 'FILED' | 'NOTICE_ISSUED' | 'HEARING_SCHEDULED' | 'DECREE_OBTAINED' | 'EXECUTION' | 'CLOSED';
  nextHearingDate: string | null;
  advocate: string;
  stage: string;
}

// Mock data
const mockLegalCases: LegalCase[] = [
  {
    id: '1',
    caseNumber: 'SARFAESI/2024/00045',
    loanAccountNumber: 'SMFC/WC/KOL/2022/L00067',
    entityName: 'Eastern Trading Co',
    caseType: 'SARFAESI',
    forum: 'DRT Chennai',
    filingDate: '2024-06-15',
    claimAmount: 45000000,
    status: 'EXECUTION',
    nextHearingDate: '2025-02-15',
    advocate: 'M/s Legal Associates',
    stage: 'Possession Notice Issued',
  },
  {
    id: '2',
    caseNumber: 'DRT/CHN/2024/00123',
    loanAccountNumber: 'SMFC/LAP/HYD/2021/L00045',
    entityName: 'Deccan Enterprises',
    caseType: 'DRT',
    forum: 'DRT Hyderabad',
    filingDate: '2024-03-20',
    claimAmount: 28500000,
    status: 'HEARING_SCHEDULED',
    nextHearingDate: '2025-02-20',
    advocate: 'Adv. Kumar & Partners',
    stage: 'Arguments in Progress',
  },
  {
    id: '3',
    caseNumber: 'NCLT/DEL/2024/00089',
    loanAccountNumber: 'SMFC/TL/PUN/2020/L00023',
    entityName: 'Western Industries Ltd',
    caseType: 'NCLT',
    forum: 'NCLT Delhi',
    filingDate: '2024-08-10',
    claimAmount: 85000000,
    status: 'FILED',
    nextHearingDate: '2025-03-05',
    advocate: 'M/s Corporate Law Chambers',
    stage: 'Admission Pending',
  },
];

const caseTypeColors: Record<string, string> = {
  SARFAESI: 'bg-purple-100 text-purple-700',
  DRT: 'bg-blue-100 text-blue-700',
  NCLT: 'bg-indigo-100 text-indigo-700',
  CIVIL: 'bg-gray-100 text-gray-700',
  ARBITRATION: 'bg-orange-100 text-orange-700',
};

const statusConfig: Record<string, { label: string; color: string }> = {
  FILED: { label: 'Filed', color: 'bg-blue-100 text-blue-700' },
  NOTICE_ISSUED: { label: 'Notice Issued', color: 'bg-yellow-100 text-yellow-700' },
  HEARING_SCHEDULED: { label: 'Hearing Scheduled', color: 'bg-amber-100 text-amber-700' },
  DECREE_OBTAINED: { label: 'Decree Obtained', color: 'bg-green-100 text-green-700' },
  EXECUTION: { label: 'Execution', color: 'bg-green-200 text-green-800' },
  CLOSED: { label: 'Closed', color: 'bg-gray-200 text-gray-700' },
};

export default function LegalCaseList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [caseTypeFilter, setCaseTypeFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const filteredCases = mockLegalCases.filter((legalCase) => {
    const matchesSearch =
      legalCase.caseNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
      legalCase.entityName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      legalCase.loanAccountNumber.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCaseType = caseTypeFilter === 'ALL' || legalCase.caseType === caseTypeFilter;
    const matchesStatus = statusFilter === 'ALL' || legalCase.status === statusFilter;
    return matchesSearch && matchesCaseType && matchesStatus;
  });

  const totalClaimAmount = mockLegalCases.reduce((sum, c) => sum + c.claimAmount, 0);
  const upcomingHearings = mockLegalCases.filter((c) => c.nextHearingDate).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Legal Cases</h1>
          <p className="text-muted-foreground">
            Track legal proceedings for loan recovery
          </p>
        </div>
        <Button onClick={() => navigate('/admin/lending/collections/legal/new')}>
          <Plus className="mr-2 h-4 w-4" />
          New Legal Case
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Cases</CardTitle>
            <Scale className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockLegalCases.length}</div>
            <p className="text-xs text-muted-foreground">Across all forums</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Claims</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalClaimAmount} abbreviated className="text-2xl font-bold" />
            <p className="text-xs text-muted-foreground">Under litigation</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Upcoming Hearings</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{upcomingHearings}</div>
            <p className="text-xs text-muted-foreground">Next 30 days</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">SARFAESI Cases</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {mockLegalCases.filter((c) => c.caseType === 'SARFAESI').length}
            </div>
            <p className="text-xs text-muted-foreground">Recovery proceedings</p>
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
                placeholder="Search by case number, entity, or loan account..."
                className="pl-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Select value={caseTypeFilter} onValueChange={setCaseTypeFilter}>
                <SelectTrigger className="w-[150px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Case Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Types</SelectItem>
                  <SelectItem value="SARFAESI">SARFAESI</SelectItem>
                  <SelectItem value="DRT">DRT</SelectItem>
                  <SelectItem value="NCLT">NCLT</SelectItem>
                  <SelectItem value="CIVIL">Civil</SelectItem>
                  <SelectItem value="ARBITRATION">Arbitration</SelectItem>
                </SelectContent>
              </Select>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Status</SelectItem>
                  <SelectItem value="FILED">Filed</SelectItem>
                  <SelectItem value="NOTICE_ISSUED">Notice Issued</SelectItem>
                  <SelectItem value="HEARING_SCHEDULED">Hearing Scheduled</SelectItem>
                  <SelectItem value="DECREE_OBTAINED">Decree Obtained</SelectItem>
                  <SelectItem value="EXECUTION">Execution</SelectItem>
                  <SelectItem value="CLOSED">Closed</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Legal Cases Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Case Number</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Forum</TableHead>
                <TableHead className="text-right">Claim Amount</TableHead>
                <TableHead>Filed On</TableHead>
                <TableHead>Next Hearing</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredCases.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                    No legal cases found matching your criteria
                  </TableCell>
                </TableRow>
              ) : (
                filteredCases.map((legalCase) => {
                  const status = statusConfig[legalCase.status];
                  return (
                    <TableRow
                      key={legalCase.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => navigate(`/admin/lending/collections/legal/${legalCase.id}`)}
                    >
                      <TableCell>
                        <div className="font-mono text-sm">{legalCase.caseNumber}</div>
                        <div className="text-xs text-muted-foreground">
                          {legalCase.loanAccountNumber}
                        </div>
                      </TableCell>
                      <TableCell>{legalCase.entityName}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={caseTypeColors[legalCase.caseType]}>
                          {legalCase.caseType}
                        </Badge>
                      </TableCell>
                      <TableCell>{legalCase.forum}</TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={legalCase.claimAmount} abbreviated />
                      </TableCell>
                      <TableCell>
                        <DateDisplay date={legalCase.filingDate} />
                      </TableCell>
                      <TableCell>
                        {legalCase.nextHearingDate ? (
                          <DateDisplay date={legalCase.nextHearingDate} />
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={status.color}>
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
                                navigate(`/admin/lending/collections/legal/${legalCase.id}`);
                              }}
                            >
                              <Eye className="mr-2 h-4 w-4" />
                              View Details
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                logger.debug('Add hearing');
                              }}
                            >
                              <Calendar className="mr-2 h-4 w-4" />
                              Add Hearing
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                logger.debug('Upload document');
                              }}
                            >
                              <FileText className="mr-2 h-4 w-4" />
                              Upload Document
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
