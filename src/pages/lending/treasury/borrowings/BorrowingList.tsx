import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Filter, MoreHorizontal, Eye, Receipt, RefreshCw, Loader2 } from 'lucide-react';
import { treasuryApi } from '@/services/lending/treasuryApi';
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
import { Badge } from '@/components/ui/badge';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';

import { logger } from '@/lib/logger';
interface BorrowingDisplay {
  id: string;
  facilityNumber: string;
  lenderName: string;
  lenderType: string;
  facilityType: 'TERM_LOAN' | 'CC' | 'NCD' | 'CP' | 'WCDL' | 'REFINANCE' | 'WORKING_CAPITAL' | 'SUBORDINATED_DEBT';
  sanctionedAmount: number;
  outstandingAmount: number;
  interestRate: number;
  rateType: 'FIXED' | 'FLOATING';
  sanctionDate: string;
  maturityDate: string;
  nextRepaymentDate: string;
  nextRepaymentAmount: number;
  status: 'ACTIVE' | 'MATURED' | 'PREPAID' | 'EXPIRED';
}

// Mock data (fallback when API unavailable)
const mockBorrowings: BorrowingDisplay[] = [
  {
    id: '1',
    facilityNumber: 'BOR/HDFC/2024/001',
    lenderName: 'HDFC Bank Ltd',
    lenderType: 'BANK',
    facilityType: 'TERM_LOAN',
    sanctionedAmount: 1000000000,
    outstandingAmount: 850000000,
    interestRate: 9.25,
    rateType: 'FLOATING',
    sanctionDate: '2024-01-15',
    maturityDate: '2029-01-15',
    nextRepaymentDate: '2025-02-15',
    nextRepaymentAmount: 50000000,
    status: 'ACTIVE',
  },
  {
    id: '2',
    facilityNumber: 'BOR/SIDBI/2024/001',
    lenderName: 'SIDBI',
    lenderType: 'DFI',
    facilityType: 'REFINANCE',
    sanctionedAmount: 350000000,
    outstandingAmount: 280000000,
    interestRate: 8.75,
    rateType: 'FLOATING',
    sanctionDate: '2024-03-01',
    maturityDate: '2027-03-01',
    nextRepaymentDate: '2025-03-01',
    nextRepaymentAmount: 35000000,
    status: 'ACTIVE',
  },
  {
    id: '3',
    facilityNumber: 'NCD/2024/001',
    lenderName: 'NCD Series 2024',
    lenderType: 'NCD',
    facilityType: 'NCD',
    sanctionedAmount: 300000000,
    outstandingAmount: 300000000,
    interestRate: 10.50,
    rateType: 'FIXED',
    sanctionDate: '2024-06-01',
    maturityDate: '2027-06-01',
    nextRepaymentDate: '2025-06-01',
    nextRepaymentAmount: 15750000,
    status: 'ACTIVE',
  },
  {
    id: '4',
    facilityNumber: 'BOR/ICICI/2024/001',
    lenderName: 'ICICI Bank Ltd',
    lenderType: 'BANK',
    facilityType: 'CC',
    sanctionedAmount: 500000000,
    outstandingAmount: 420000000,
    interestRate: 9.50,
    rateType: 'FLOATING',
    sanctionDate: '2024-04-15',
    maturityDate: '2025-04-15',
    nextRepaymentDate: '2025-02-28',
    nextRepaymentAmount: 3937500,
    status: 'ACTIVE',
  },
];

const facilityTypeLabels: Record<string, { label: string; color: string }> = {
  TERM_LOAN: { label: 'Term Loan', color: 'bg-blue-100 text-blue-700' },
  CC: { label: 'Cash Credit', color: 'bg-green-100 text-green-700' },
  NCD: { label: 'NCD', color: 'bg-orange-100 text-orange-700' },
  CP: { label: 'Commercial Paper', color: 'bg-pink-100 text-pink-700' },
  WCDL: { label: 'WCDL', color: 'bg-purple-100 text-purple-700' },
  REFINANCE: { label: 'Refinance', color: 'bg-indigo-100 text-indigo-700' },
  WORKING_CAPITAL: { label: 'Working Capital', color: 'bg-teal-100 text-teal-700' },
  SUBORDINATED_DEBT: { label: 'Sub Debt', color: 'bg-amber-100 text-amber-700' },
};

export default function BorrowingList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);
  const [borrowings, setBorrowings] = useState<BorrowingDisplay[]>([]);

  // Fetch borrowings from API
  useEffect(() => {
    async function fetchBorrowings() {
      setLoading(true);
      try {
        const response = await treasuryApi.getBorrowings({
          search: searchQuery || undefined,
          facility_type: typeFilter !== 'ALL' ? typeFilter : undefined,
          status: statusFilter !== 'ALL' ? statusFilter : undefined,
        });

        // Map API response to display format
        const mappedBorrowings: BorrowingDisplay[] = response.items.map((borrowing: any) => ({
          id: borrowing.borrowing_id,
          facilityNumber: borrowing.facility_number || borrowing.borrowing_id.slice(0, 12).toUpperCase(),
          lenderName: borrowing.lender_name || 'Unknown Lender',
          lenderType: borrowing.lender_type || 'BANK',
          facilityType: borrowing.facility_type || 'TERM_LOAN',
          sanctionedAmount: borrowing.sanctioned_amount || 0,
          outstandingAmount: borrowing.outstanding_amount || 0,
          interestRate: borrowing.interest_rate || borrowing.effective_rate || 0,
          rateType: borrowing.interest_type || 'FIXED',
          sanctionDate: borrowing.sanction_date || '',
          maturityDate: borrowing.maturity_date || '',
          nextRepaymentDate: borrowing.next_repayment_date || '',
          nextRepaymentAmount: borrowing.next_repayment_amount || 0,
          status: borrowing.status || 'ACTIVE',
        }));

        setBorrowings(mappedBorrowings);
      } catch (error) {
        console.error('Failed to fetch borrowings, using mock data:', error);
        // Fallback to mock data
        setBorrowings(mockBorrowings);
      } finally {
        setLoading(false);
      }
    }

    fetchBorrowings();
  }, [searchQuery, typeFilter, statusFilter]);

  const filteredBorrowings = borrowings.filter((borrowing) => {
    const matchesSearch =
      borrowing.facilityNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
      borrowing.lenderName.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = typeFilter === 'ALL' || borrowing.facilityType === typeFilter;
    const matchesStatus = statusFilter === 'ALL' || borrowing.status === statusFilter;
    return matchesSearch && matchesType && matchesStatus;
  });

  const totalSanctioned = borrowings.reduce((sum, b) => sum + b.sanctionedAmount, 0);
  const totalOutstanding = borrowings.reduce((sum, b) => sum + b.outstandingAmount, 0);
  const upcomingRepayments = borrowings.reduce((sum, b) => sum + b.nextRepaymentAmount, 0);
  const weightedAvgRate = totalOutstanding > 0
    ? borrowings.reduce((sum, b) => sum + b.interestRate * b.outstandingAmount, 0) / totalOutstanding
    : 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Borrowings"
        subtitle="Manage borrowing facilities and repayment schedules"
        actions={
          <Button onClick={() => navigate('/admin/treasury/borrowings/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Borrowing
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sanctioned</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            ) : (
              <>
                <AmountDisplay amount={totalSanctioned} abbreviated className="text-2xl font-bold" />
                <p className="text-xs text-muted-foreground">Across all facilities</p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Outstanding</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            ) : (
              <>
                <AmountDisplay amount={totalOutstanding} abbreviated className="text-2xl font-bold text-amber-600" />
                <p className="text-xs text-muted-foreground">
                  <PercentageDisplay value={totalSanctioned > 0 ? (totalOutstanding / totalSanctioned) * 100 : 0} /> utilized
                </p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Weighted Avg Rate</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            ) : (
              <>
                <div className="text-2xl font-bold">
                  <PercentageDisplay value={weightedAvgRate} /> p.a.
                </div>
                <p className="text-xs text-muted-foreground">Cost of borrowing</p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Next 30 Days</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            ) : (
              <>
                <AmountDisplay amount={upcomingRepayments} abbreviated className="text-2xl font-bold text-red-600" />
                <p className="text-xs text-muted-foreground">Upcoming repayments</p>
              </>
            )}
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
                placeholder="Search by facility number or lender..."
                className="pl-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[160px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Facility Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Types</SelectItem>
                  <SelectItem value="TERM_LOAN">Term Loan</SelectItem>
                  <SelectItem value="CC">Cash Credit</SelectItem>
                  <SelectItem value="NCD">NCD</SelectItem>
                  <SelectItem value="CP">Commercial Paper</SelectItem>
                  <SelectItem value="WCDL">WCDL</SelectItem>
                  <SelectItem value="REFINANCE">Refinance</SelectItem>
                </SelectContent>
              </Select>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Status</SelectItem>
                  <SelectItem value="ACTIVE">Active</SelectItem>
                  <SelectItem value="MATURED">Matured</SelectItem>
                  <SelectItem value="PREPAID">Prepaid</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Borrowings Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Facility Number</TableHead>
                <TableHead>Lender</TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="text-right">Outstanding</TableHead>
                <TableHead className="text-right">Rate</TableHead>
                <TableHead>Maturity</TableHead>
                <TableHead>Next Repayment</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredBorrowings.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                    No borrowings found matching your criteria
                  </TableCell>
                </TableRow>
              ) : (
                filteredBorrowings.map((borrowing) => {
                  const typeConfig = facilityTypeLabels[borrowing.facilityType];
                  return (
                    <TableRow
                      key={borrowing.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() =>
                        navigate(`/admin/treasury/borrowings/${borrowing.id}`)
                      }
                    >
                      <TableCell className="font-mono text-sm">
                        {borrowing.facilityNumber}
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">{borrowing.lenderName}</div>
                        <div className="text-xs text-muted-foreground">
                          {borrowing.lenderType}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={typeConfig.color}>
                          {typeConfig.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={borrowing.outstandingAmount} abbreviated />
                        <div className="text-xs text-muted-foreground">
                          of <AmountDisplay amount={borrowing.sanctionedAmount} abbreviated />
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <PercentageDisplay value={borrowing.interestRate} /> p.a.
                        <div className="text-xs text-muted-foreground">
                          {borrowing.rateType}
                        </div>
                      </TableCell>
                      <TableCell>
                        <DateDisplay date={borrowing.maturityDate} />
                      </TableCell>
                      <TableCell>
                        <DateDisplay date={borrowing.nextRepaymentDate} />
                        <div className="text-xs text-muted-foreground">
                          <AmountDisplay amount={borrowing.nextRepaymentAmount} abbreviated />
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={borrowing.status === 'ACTIVE' ? 'default' : 'secondary'}
                          className={
                            borrowing.status === 'ACTIVE' ? 'bg-green-100 text-green-700' : ''
                          }
                        >
                          {borrowing.status}
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
                                navigate(`/admin/treasury/borrowings/${borrowing.id}`);
                              }}
                            >
                              <Eye className="mr-2 h-4 w-4" />
                              View Details
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                logger.debug('Record payment');
                              }}
                            >
                              <Receipt className="mr-2 h-4 w-4" />
                              Record Payment
                            </DropdownMenuItem>
                            {borrowing.rateType === 'FLOATING' && (
                              <DropdownMenuItem
                                onClick={(e) => {
                                  e.stopPropagation();
                                  logger.debug('Rate reset');
                                }}
                              >
                                <RefreshCw className="mr-2 h-4 w-4" />
                                Rate Reset
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
