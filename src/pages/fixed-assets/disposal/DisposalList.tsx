import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  Archive,
  ArrowUpDown,
  Banknote,
  CheckCircle,
  Clock,
  Download,
  FileText,
  Filter,
  MoreHorizontal,
  Plus,
  Search,
  Trash2,
  TrendingDown,
  XCircle,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/common/PageHeader';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { organizationsApi } from '@/services/api';
import type { Organization, PaginatedResponse } from '@/types';

interface AssetDisposal {
  id: string;
  disposal_number: string;
  asset_code: string;
  asset_name: string;
  category: string;
  disposal_type: 'SALE' | 'SCRAP' | 'WRITE_OFF' | 'DONATION' | 'EXCHANGE' | 'THEFT_LOSS';
  disposal_method: string;
  request_date: string;
  disposal_date?: string;
  original_cost: number;
  accumulated_depreciation: number;
  wdv: number;
  sale_value?: number;
  profit_loss: number;
  status: 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'COMPLETED' | 'CANCELLED';
  reason: string;
  buyer_name?: string;
  requested_by: string;
  approved_by?: string;
}

export function DisposalList() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('pending');
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [disposals, setDisposals] = useState<AssetDisposal[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrgId) {
      fetchDisposals();
    }
  }, [selectedOrgId]);

  const fetchOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      const data: PaginatedResponse<Organization> = response.data;
      setOrganizations(data.items);
      if (data.items.length > 0) {
        setSelectedOrgId(data.items[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
    }
  };

  const fetchDisposals = async () => {
    try {
      setLoading(true);
      // Mock data - replace with actual API call
      const mockDisposals: AssetDisposal[] = [
        {
          id: '1',
          disposal_number: 'DISP-2024-001',
          asset_code: 'FA-COMP-005',
          asset_name: 'Dell Laptop Latitude 5520',
          category: 'Computer Equipment',
          disposal_type: 'SALE',
          disposal_method: 'Auction',
          request_date: '2024-11-01',
          disposal_date: '2024-11-15',
          original_cost: 85000,
          accumulated_depreciation: 68000,
          wdv: 17000,
          sale_value: 22000,
          profit_loss: 5000,
          status: 'COMPLETED',
          reason: 'Obsolete - upgraded to newer model',
          buyer_name: 'Tech Solutions Pvt Ltd',
          requested_by: 'John Doe',
          approved_by: 'Jane Smith',
        },
        {
          id: '2',
          disposal_number: 'DISP-2024-002',
          asset_code: 'FA-FURN-012',
          asset_name: 'Executive Desk - Mahogany',
          category: 'Furniture & Fixtures',
          disposal_type: 'SCRAP',
          disposal_method: 'Scrap Dealer',
          request_date: '2024-11-10',
          original_cost: 45000,
          accumulated_depreciation: 40500,
          wdv: 4500,
          sale_value: 2500,
          profit_loss: -2000,
          status: 'PENDING_APPROVAL',
          reason: 'Damaged beyond repair',
          requested_by: 'Mike Wilson',
        },
        {
          id: '3',
          disposal_number: 'DISP-2024-003',
          asset_code: 'FA-VEH-003',
          asset_name: 'Maruti Swift Dzire',
          category: 'Vehicles',
          disposal_type: 'SALE',
          disposal_method: 'Direct Sale',
          request_date: '2024-11-12',
          original_cost: 750000,
          accumulated_depreciation: 450000,
          wdv: 300000,
          sale_value: 320000,
          profit_loss: 20000,
          status: 'APPROVED',
          reason: 'Fleet optimization - downsizing',
          buyer_name: 'Individual Buyer',
          requested_by: 'Sarah Johnson',
          approved_by: 'Admin Manager',
        },
        {
          id: '4',
          disposal_number: 'DISP-2024-004',
          asset_code: 'FA-MACH-008',
          asset_name: 'Industrial Printer - HP',
          category: 'Plant & Machinery',
          disposal_type: 'WRITE_OFF',
          disposal_method: 'Write-off',
          request_date: '2024-11-05',
          disposal_date: '2024-11-08',
          original_cost: 120000,
          accumulated_depreciation: 96000,
          wdv: 24000,
          profit_loss: -24000,
          status: 'COMPLETED',
          reason: 'Fire damage - insurance claim filed',
          requested_by: 'Tom Harris',
          approved_by: 'Finance Head',
        },
        {
          id: '5',
          disposal_number: 'DISP-2024-005',
          asset_code: 'FA-COMP-022',
          asset_name: 'Server - Dell PowerEdge',
          category: 'Computer Equipment',
          disposal_type: 'EXCHANGE',
          disposal_method: 'Trade-in',
          request_date: '2024-11-14',
          original_cost: 350000,
          accumulated_depreciation: 175000,
          wdv: 175000,
          sale_value: 150000,
          profit_loss: -25000,
          status: 'DRAFT',
          reason: 'Upgrading to newer server model',
          requested_by: 'IT Manager',
        },
      ];
      setDisposals(mockDisposals);
    } catch (error) {
      console.error('Failed to fetch disposals:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, { bg: string; icon: React.ReactNode }> = {
      DRAFT: { bg: 'bg-slate-50 text-slate-700', icon: <FileText className="mr-1 h-3 w-3" /> },
      PENDING_APPROVAL: { bg: 'bg-yellow-50 text-yellow-700', icon: <Clock className="mr-1 h-3 w-3" /> },
      APPROVED: { bg: 'bg-blue-50 text-blue-700', icon: <CheckCircle className="mr-1 h-3 w-3" /> },
      REJECTED: { bg: 'bg-red-50 text-red-700', icon: <XCircle className="mr-1 h-3 w-3" /> },
      COMPLETED: { bg: 'bg-emerald-50 text-emerald-700', icon: <CheckCircle className="mr-1 h-3 w-3" /> },
      CANCELLED: { bg: 'bg-slate-50 text-slate-500', icon: <XCircle className="mr-1 h-3 w-3" /> },
    };
    const style = styles[status] || styles.DRAFT;
    return (
      <Badge className={`${style.bg} hover:${style.bg} flex items-center`}>
        {style.icon}
        {status.replace('_', ' ')}
      </Badge>
    );
  };

  const getDisposalTypeBadge = (type: string) => {
    const colors: Record<string, string> = {
      SALE: 'bg-emerald-50 text-emerald-700',
      SCRAP: 'bg-orange-50 text-orange-700',
      WRITE_OFF: 'bg-red-50 text-red-700',
      DONATION: 'bg-purple-50 text-purple-700',
      EXCHANGE: 'bg-blue-50 text-blue-700',
      THEFT_LOSS: 'bg-red-100 text-red-800',
    };
    return (
      <Badge className={`${colors[type] || 'bg-slate-50 text-slate-700'} hover:${colors[type]}`}>
        {type.replace('_', ' ')}
      </Badge>
    );
  };

  const filteredDisposals = disposals.filter((d) => {
    if (activeTab === 'pending' && !['DRAFT', 'PENDING_APPROVAL', 'APPROVED'].includes(d.status)) return false;
    if (activeTab === 'completed' && d.status !== 'COMPLETED') return false;
    if (typeFilter !== 'all' && d.disposal_type !== typeFilter) return false;
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        d.disposal_number.toLowerCase().includes(query) ||
        d.asset_code.toLowerCase().includes(query) ||
        d.asset_name.toLowerCase().includes(query)
      );
    }
    return true;
  });

  const pendingCount = disposals.filter(d => ['DRAFT', 'PENDING_APPROVAL', 'APPROVED'].includes(d.status)).length;
  const completedCount = disposals.filter(d => d.status === 'COMPLETED').length;
  const totalSaleValue = disposals
    .filter(d => d.status === 'COMPLETED' && d.sale_value)
    .reduce((sum, d) => sum + (d.sale_value || 0), 0);
  const totalProfitLoss = disposals
    .filter(d => d.status === 'COMPLETED')
    .reduce((sum, d) => sum + d.profit_loss, 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Asset Disposal"
        subtitle="Manage asset disposals, sales, scrapping, and write-offs"
        actions={
          <div className="flex gap-2">
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
            <Button onClick={() => navigate('/admin/fixed-assets/disposal/new')}>
              <Plus className="mr-2 h-4 w-4" />
              New Disposal
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Disposals</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{pendingCount}</div>
            <p className="text-xs text-slate-500">Awaiting action</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600">{completedCount}</div>
            <p className="text-xs text-slate-500">This financial year</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sale Value</CardTitle>
            <Banknote className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{formatCurrency(totalSaleValue)}</div>
            <p className="text-xs text-slate-500">Realized from disposals</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Net Profit/Loss</CardTitle>
            {totalProfitLoss >= 0 ? (
              <TrendingDown className="h-4 w-4 text-emerald-500 rotate-180" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-500" />
            )}
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${totalProfitLoss >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
              {formatCurrency(Math.abs(totalProfitLoss))}
              <span className="text-sm font-normal ml-1">{totalProfitLoss >= 0 ? 'Profit' : 'Loss'}</span>
            </div>
            <p className="text-xs text-slate-500">On completed disposals</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="pending">Pending ({pendingCount})</TabsTrigger>
          <TabsTrigger value="completed">Completed ({completedCount})</TabsTrigger>
          <TabsTrigger value="all">All Disposals</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab}>
          <Card>
            <CardHeader>
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <CardTitle>Disposal Requests</CardTitle>
                <div className="flex flex-wrap items-center gap-2">
                  <div className="relative">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                    <Input
                      placeholder="Search..."
                      className="pl-8 w-[200px]"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                  <Select value={typeFilter} onValueChange={setTypeFilter}>
                    <SelectTrigger className="w-[140px]">
                      <SelectValue placeholder="Type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      <SelectItem value="SALE">Sale</SelectItem>
                      <SelectItem value="SCRAP">Scrap</SelectItem>
                      <SelectItem value="WRITE_OFF">Write-off</SelectItem>
                      <SelectItem value="DONATION">Donation</SelectItem>
                      <SelectItem value="EXCHANGE">Exchange</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Organization" />
                    </SelectTrigger>
                    <SelectContent>
                      {organizations.map((org) => (
                        <SelectItem key={org.id} value={org.id}>
                          {org.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <p className="text-sm text-slate-500">Loading...</p>
                </div>
              ) : filteredDisposals.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <Archive className="mb-4 h-12 w-12 text-slate-300" />
                  <p className="text-sm text-slate-500">No disposal requests found</p>
                  <Button variant="link" onClick={() => navigate('/admin/fixed-assets/disposal/new')}>
                    Create a disposal request
                  </Button>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Disposal #</TableHead>
                      <TableHead>Asset</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead className="text-right">Original Cost</TableHead>
                      <TableHead className="text-right">WDV</TableHead>
                      <TableHead className="text-right">Sale Value</TableHead>
                      <TableHead className="text-right">Profit/Loss</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="w-[70px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredDisposals.map((disposal) => (
                      <TableRow key={disposal.id}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{disposal.disposal_number}</p>
                            <p className="text-xs text-slate-500">{formatDate(disposal.request_date)}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{disposal.asset_code}</p>
                            <p className="text-sm text-slate-500">{disposal.asset_name}</p>
                          </div>
                        </TableCell>
                        <TableCell>{getDisposalTypeBadge(disposal.disposal_type)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(disposal.original_cost)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(disposal.wdv)}</TableCell>
                        <TableCell className="text-right">
                          {disposal.sale_value ? formatCurrency(disposal.sale_value) : '-'}
                        </TableCell>
                        <TableCell className="text-right">
                          <span className={disposal.profit_loss >= 0 ? 'text-emerald-600' : 'text-red-600'}>
                            {disposal.profit_loss >= 0 ? '+' : ''}
                            {formatCurrency(disposal.profit_loss)}
                          </span>
                        </TableCell>
                        <TableCell>{getStatusBadge(disposal.status)}</TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem>View Details</DropdownMenuItem>
                              {disposal.status === 'DRAFT' && (
                                <>
                                  <DropdownMenuItem>Edit</DropdownMenuItem>
                                  <DropdownMenuItem>Submit for Approval</DropdownMenuItem>
                                </>
                              )}
                              {disposal.status === 'PENDING_APPROVAL' && (
                                <>
                                  <DropdownMenuItem className="text-emerald-600">Approve</DropdownMenuItem>
                                  <DropdownMenuItem className="text-red-600">Reject</DropdownMenuItem>
                                </>
                              )}
                              {disposal.status === 'APPROVED' && (
                                <DropdownMenuItem>Complete Disposal</DropdownMenuItem>
                              )}
                              <DropdownMenuSeparator />
                              <DropdownMenuItem>View Asset</DropdownMenuItem>
                              <DropdownMenuItem>Print</DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
