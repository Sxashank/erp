import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2,
  Edit,
  Eye,
  MoreHorizontal,
  Package,
  Plus,
  Search,
  Trash2,
  CheckCircle,
  XCircle,
  ArrowRightLeft,
  TrendingUp,
  TrendingDown,
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
import { fixedAssetsApi, organizationsApi } from '@/services/api';
import type { Organization, PaginatedResponse } from '@/types';

interface FixedAsset {
  id: string;
  organization_id: string;
  asset_code: string;
  asset_name: string;
  description?: string;
  category_id: string;
  category_code?: string;
  category_name?: string;
  location_id?: string;
  location_name?: string;
  department_id?: string;
  department_name?: string;
  acquisition_date: string;
  put_to_use_date?: string;
  acquisition_type: string;
  vendor_id?: string;
  vendor_name?: string;
  total_cost: number;
  residual_value: number;
  depreciable_value: number;
  depreciation_method: string;
  depreciation_rate?: number;
  accumulated_depreciation: number;
  wdv_value: number;
  status: string;
  is_fully_depreciated: boolean;
  is_active: boolean;
}

interface AssetCategory {
  id: string;
  category_code: string;
  category_name: string;
}

const ASSET_STATUSES = [
  { value: '', label: 'All Statuses' },
  { value: 'DRAFT', label: 'Draft' },
  { value: 'ACTIVE', label: 'Active' },
  { value: 'DISPOSED', label: 'Disposed' },
  { value: 'TRANSFERRED', label: 'Transferred' },
  { value: 'UNDER_MAINTENANCE', label: 'Under Maintenance' },
  { value: 'FULLY_DEPRECIATED', label: 'Fully Depreciated' },
];

export function AssetList() {
  const navigate = useNavigate();
  const [assets, setAssets] = useState<FixedAsset[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [categories, setCategories] = useState<AssetCategory[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [selectedCategoryId, setSelectedCategoryId] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const limit = 20;

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrgId) {
      fetchCategories();
      fetchAssets();
    }
  }, [selectedOrgId, selectedCategoryId, selectedStatus, skip]);

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

  const fetchCategories = async () => {
    try {
      const response = await fixedAssetsApi.listCategories({
        organization_id: selectedOrgId,
        limit: 500,
      });
      setCategories(response.data.items || []);
    } catch (error) {
      console.error('Failed to fetch categories:', error);
    }
  };

  const fetchAssets = async () => {
    if (!selectedOrgId) return;
    try {
      setLoading(true);
      const params: any = {
        organization_id: selectedOrgId,
        skip,
        limit,
      };
      if (selectedCategoryId) params.category_id = selectedCategoryId;
      if (selectedStatus) params.status = selectedStatus;
      if (searchQuery) params.search = searchQuery;

      const response = await fixedAssetsApi.listAssets(params);
      setAssets(response.data.items || []);
      setTotal(response.data.total || 0);
    } catch (error) {
      console.error('Failed to fetch assets:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setSkip(0);
    fetchAssets();
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this asset?')) return;
    try {
      await fixedAssetsApi.deleteAsset(id);
      fetchAssets();
    } catch (error) {
      console.error('Failed to delete asset:', error);
    }
  };

  const getStatusBadge = (status: string, isFullyDepreciated: boolean) => {
    if (isFullyDepreciated && status === 'ACTIVE') {
      return (
        <Badge className="bg-slate-100 text-slate-700 hover:bg-slate-100">
          Fully Depreciated
        </Badge>
      );
    }

    switch (status) {
      case 'DRAFT':
        return <Badge variant="outline">Draft</Badge>;
      case 'ACTIVE':
        return <Badge className="bg-emerald-50 text-emerald-700 hover:bg-emerald-50">Active</Badge>;
      case 'DISPOSED':
        return <Badge className="bg-red-50 text-red-700 hover:bg-red-50">Disposed</Badge>;
      case 'TRANSFERRED':
        return <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-50">Transferred</Badge>;
      case 'UNDER_MAINTENANCE':
        return <Badge className="bg-orange-50 text-orange-700 hover:bg-orange-50">Under Maintenance</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
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

  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(skip / limit) + 1;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Fixed Assets"
        subtitle="Manage organization fixed assets register"
        actions={
          <Button onClick={() => navigate('/admin/fixed-assets/assets/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Asset
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle>Asset Register</CardTitle>
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search assets..."
                  className="pl-8 w-[200px]"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                />
              </div>
              <Select value={selectedCategoryId} onValueChange={(value) => { setSelectedCategoryId(value); setSkip(0); }}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="All Categories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Categories</SelectItem>
                  {categories.map((cat) => (
                    <SelectItem key={cat.id} value={cat.id}>
                      {cat.category_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={selectedStatus} onValueChange={(value) => { setSelectedStatus(value); setSkip(0); }}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="All Statuses" />
                </SelectTrigger>
                <SelectContent>
                  {ASSET_STATUSES.map((status) => (
                    <SelectItem key={status.value} value={status.value}>
                      {status.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Select organization" />
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
          ) : assets.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <Package className="mb-4 h-12 w-12 text-slate-300" />
              <p className="text-sm text-slate-500">No assets found</p>
              <Button variant="link" onClick={() => navigate('/admin/fixed-assets/assets/new')}>
                Add your first asset
              </Button>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Asset Code</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead className="text-right">Total Cost</TableHead>
                    <TableHead className="text-right">Acc. Dep.</TableHead>
                    <TableHead className="text-right">WDV</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="w-[70px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {assets.map((asset) => (
                    <TableRow key={asset.id}>
                      <TableCell>
                        <span className="font-medium">{asset.asset_code}</span>
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="font-medium">{asset.asset_name}</p>
                          {asset.acquisition_date && (
                            <p className="text-xs text-slate-500">
                              Acquired: {formatDate(asset.acquisition_date)}
                            </p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{asset.category_name || '-'}</Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Building2 className="h-3 w-3 text-slate-400" />
                          <span className="text-sm">{asset.location_name || '-'}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(asset.total_cost)}
                      </TableCell>
                      <TableCell className="text-right text-slate-600">
                        {formatCurrency(asset.accumulated_depreciation)}
                      </TableCell>
                      <TableCell className="text-right font-medium text-emerald-600">
                        {formatCurrency(asset.wdv_value)}
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(asset.status, asset.is_fully_depreciated)}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => navigate(`/admin/fixed-assets/assets/${asset.id}`)}>
                              <Eye className="mr-2 h-4 w-4" />
                              View
                            </DropdownMenuItem>
                            {asset.status === 'DRAFT' && (
                              <DropdownMenuItem onClick={() => navigate(`/admin/fixed-assets/assets/${asset.id}/edit`)}>
                                <Edit className="mr-2 h-4 w-4" />
                                Edit
                              </DropdownMenuItem>
                            )}
                            {asset.status === 'DRAFT' && (
                              <>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem onClick={() => navigate(`/admin/fixed-assets/assets/${asset.id}/capitalize`)}>
                                  <CheckCircle className="mr-2 h-4 w-4" />
                                  Capitalize
                                </DropdownMenuItem>
                              </>
                            )}
                            {asset.status === 'ACTIVE' && (
                              <>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem onClick={() => navigate(`/admin/fixed-assets/assets/${asset.id}/transfer`)}>
                                  <ArrowRightLeft className="mr-2 h-4 w-4" />
                                  Transfer
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => navigate(`/admin/fixed-assets/assets/${asset.id}/revalue`)}>
                                  <TrendingUp className="mr-2 h-4 w-4" />
                                  Revalue
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => navigate(`/admin/fixed-assets/assets/${asset.id}/impair`)}>
                                  <TrendingDown className="mr-2 h-4 w-4" />
                                  Impair
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => navigate(`/admin/fixed-assets/assets/${asset.id}/dispose`)}>
                                  <XCircle className="mr-2 h-4 w-4" />
                                  Dispose
                                </DropdownMenuItem>
                              </>
                            )}
                            {asset.status === 'DRAFT' && (
                              <>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  onClick={() => handleDelete(asset.id)}
                                  className="text-red-600"
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  Delete
                                </DropdownMenuItem>
                              </>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <p className="text-sm text-slate-500">
                    Showing {skip + 1} to {Math.min(skip + limit, total)} of {total} assets
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSkip(Math.max(0, skip - limit))}
                      disabled={skip === 0}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSkip(skip + limit)}
                      disabled={currentPage >= totalPages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
