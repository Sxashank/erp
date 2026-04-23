import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Filter, MoreHorizontal, Eye, Edit, Building2, Loader2 } from 'lucide-react';
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

interface LenderDisplay {
  id: string;
  lenderCode: string;
  lenderName: string;
  lenderType: 'BANK' | 'DFI' | 'MF' | 'NCD' | 'CP' | 'SECURITIZATION' | 'SUBORDINATED_DEBT' | 'OTHER';
  sanctionedLimit: number;
  utilizedAmount: number;
  availableLimit: number;
  avgRate: number;
  status: 'ACTIVE' | 'INACTIVE' | 'EXPIRED';
  activeFacilities: number;
  contactPerson: string;
}

// Mock data (fallback when API unavailable)
const mockLenders: LenderDisplay[] = [
  {
    id: '1',
    lenderCode: 'HDFC-BNK',
    lenderName: 'HDFC Bank Ltd',
    lenderType: 'BANK',
    sanctionedLimit: 2000000000,
    utilizedAmount: 1500000000,
    availableLimit: 500000000,
    avgRate: 9.25,
    status: 'ACTIVE',
    activeFacilities: 3,
    contactPerson: 'Mr. Rajesh Sharma',
  },
  {
    id: '2',
    lenderCode: 'SIDBI',
    lenderName: 'SIDBI',
    lenderType: 'DFI',
    sanctionedLimit: 500000000,
    utilizedAmount: 350000000,
    availableLimit: 150000000,
    avgRate: 8.75,
    status: 'ACTIVE',
    activeFacilities: 2,
    contactPerson: 'Ms. Priya Agarwal',
  },
  {
    id: '3',
    lenderCode: 'ICICI-BNK',
    lenderName: 'ICICI Bank Ltd',
    lenderType: 'BANK',
    sanctionedLimit: 1000000000,
    utilizedAmount: 800000000,
    availableLimit: 200000000,
    avgRate: 9.50,
    status: 'ACTIVE',
    activeFacilities: 2,
    contactPerson: 'Mr. Amit Patel',
  },
  {
    id: '4',
    lenderCode: 'NCD-2024',
    lenderName: 'NCD Series 2024',
    lenderType: 'NCD',
    sanctionedLimit: 300000000,
    utilizedAmount: 300000000,
    availableLimit: 0,
    avgRate: 10.50,
    status: 'ACTIVE',
    activeFacilities: 1,
    contactPerson: 'M/s Trustee Services',
  },
];

const lenderTypeLabels: Record<string, { label: string; color: string }> = {
  BANK: { label: 'Bank', color: 'bg-blue-100 text-blue-700' },
  DFI: { label: 'DFI', color: 'bg-green-100 text-green-700' },
  MF: { label: 'Mutual Fund', color: 'bg-purple-100 text-purple-700' },
  NCD: { label: 'NCD', color: 'bg-orange-100 text-orange-700' },
  CP: { label: 'Commercial Paper', color: 'bg-pink-100 text-pink-700' },
  SECURITIZATION: { label: 'Securitization', color: 'bg-indigo-100 text-indigo-700' },
  SUBORDINATED_DEBT: { label: 'Sub Debt', color: 'bg-amber-100 text-amber-700' },
  OTHER: { label: 'Other', color: 'bg-gray-100 text-gray-700' },
};

export default function LenderList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);
  const [lenders, setLenders] = useState<LenderDisplay[]>([]);

  // Fetch lenders from API
  useEffect(() => {
    async function fetchLenders() {
      setLoading(true);
      try {
        const response = await treasuryApi.getLenders({
          search: searchQuery || undefined,
          lender_type: typeFilter !== 'ALL' ? typeFilter : undefined,
        });

        // Map API response to display format
        const mappedLenders: LenderDisplay[] = response.items.map((lender: any) => ({
          id: lender.lender_id,
          lenderCode: lender.lender_code || lender.lender_id.slice(0, 8).toUpperCase(),
          lenderName: lender.lender_name,
          lenderType: lender.lender_type,
          sanctionedLimit: lender.total_sanctioned || 0,
          utilizedAmount: lender.total_outstanding || 0,
          availableLimit: (lender.total_sanctioned || 0) - (lender.total_outstanding || 0),
          avgRate: lender.weighted_avg_rate || 0,
          status: lender.status || 'ACTIVE',
          activeFacilities: lender.active_facilities || 0,
          contactPerson: lender.contact_person || '',
        }));

        setLenders(mappedLenders);
      } catch (error) {
        console.error('Failed to fetch lenders, using mock data:', error);
        // Fallback to mock data
        setLenders(mockLenders);
      } finally {
        setLoading(false);
      }
    }

    fetchLenders();
  }, [searchQuery, typeFilter]);

  const filteredLenders = lenders.filter((lender) => {
    const matchesSearch =
      lender.lenderName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      lender.lenderCode.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = typeFilter === 'ALL' || lender.lenderType === typeFilter;
    return matchesSearch && matchesType;
  });

  const totalSanctioned = lenders.reduce((sum, l) => sum + l.sanctionedLimit, 0);
  const totalUtilized = lenders.reduce((sum, l) => sum + l.utilizedAmount, 0);
  const totalAvailable = lenders.reduce((sum, l) => sum + l.availableLimit, 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Lenders"
        subtitle="Manage lender relationships and borrowing facilities"
        actions={
          <Button onClick={() => navigate('/admin/treasury/lenders/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Lender
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Lenders</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            ) : (
              <>
                <div className="text-2xl font-bold">{lenders.length}</div>
                <p className="text-xs text-muted-foreground">Active relationships</p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sanctioned</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalSanctioned} abbreviated className="text-2xl font-bold" />
            <p className="text-xs text-muted-foreground">Aggregate limits</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Utilized</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalUtilized} abbreviated className="text-2xl font-bold text-amber-600" />
            <p className="text-xs text-muted-foreground">
              <PercentageDisplay value={(totalUtilized / totalSanctioned) * 100} /> utilization
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Available Limit</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalAvailable} abbreviated className="text-2xl font-bold text-green-600" />
            <p className="text-xs text-muted-foreground">Undrawn facilities</p>
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
                placeholder="Search by lender name or code..."
                className="pl-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[180px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Lender Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Types</SelectItem>
                  <SelectItem value="BANK">Bank</SelectItem>
                  <SelectItem value="DFI">DFI</SelectItem>
                  <SelectItem value="MF">Mutual Fund</SelectItem>
                  <SelectItem value="NCD">NCD</SelectItem>
                  <SelectItem value="CP">Commercial Paper</SelectItem>
                  <SelectItem value="SECURITIZATION">Securitization</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lenders Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Lender Code</TableHead>
                <TableHead>Lender Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="text-right">Sanctioned</TableHead>
                <TableHead className="text-right">Utilized</TableHead>
                <TableHead className="text-right">Available</TableHead>
                <TableHead className="text-right">Avg Rate</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredLenders.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                    No lenders found matching your criteria
                  </TableCell>
                </TableRow>
              ) : (
                filteredLenders.map((lender) => {
                  const typeConfig = lenderTypeLabels[lender.lenderType];
                  const utilizationPercent = (lender.utilizedAmount / lender.sanctionedLimit) * 100;
                  return (
                    <TableRow
                      key={lender.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => navigate(`/admin/treasury/lenders/${lender.id}`)}
                    >
                      <TableCell className="font-mono text-sm">{lender.lenderCode}</TableCell>
                      <TableCell>
                        <div className="font-medium">{lender.lenderName}</div>
                        <div className="text-xs text-muted-foreground">
                          {lender.activeFacilities} active facilities
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={typeConfig.color}>
                          {typeConfig.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={lender.sanctionedLimit} abbreviated />
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={lender.utilizedAmount} abbreviated />
                        <div className="text-xs text-muted-foreground">
                          <PercentageDisplay value={utilizationPercent} />
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={lender.availableLimit} abbreviated />
                      </TableCell>
                      <TableCell className="text-right">
                        <PercentageDisplay value={lender.avgRate} /> p.a.
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={lender.status === 'ACTIVE' ? 'default' : 'secondary'}
                          className={
                            lender.status === 'ACTIVE' ? 'bg-green-100 text-green-700' : ''
                          }
                        >
                          {lender.status}
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
                                navigate(`/admin/treasury/lenders/${lender.id}`);
                              }}
                            >
                              <Eye className="mr-2 h-4 w-4" />
                              View Details
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/admin/treasury/lenders/${lender.id}/edit`);
                              }}
                            >
                              <Edit className="mr-2 h-4 w-4" />
                              Edit Lender
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
