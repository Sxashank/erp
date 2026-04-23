import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Building2,
  Calendar,
  Edit,
  FileText,
  IndianRupee,
  MapPin,
  Package,
  Settings,
  Tag,
  TrendingDown,
  User,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { fixedAssetsApi } from '@/services/api';

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
  custodian_id?: string;
  custodian_name?: string;
  acquisition_date: string;
  put_to_use_date?: string;
  acquisition_type: string;
  vendor_id?: string;
  vendor_name?: string;
  invoice_number?: string;
  invoice_date?: string;
  total_cost: number;
  residual_value: number;
  depreciable_value: number;
  depreciation_method: string;
  depreciation_rate?: number;
  useful_life_months?: number;
  accumulated_depreciation: number;
  wdv_value: number;
  status: string;
  is_fully_depreciated: boolean;
  is_active: boolean;
  serial_number?: string;
  model_number?: string;
  manufacturer?: string;
  warranty_expiry?: string;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

interface DepreciationEntry {
  id: string;
  period: string;
  depreciation_amount: number;
  accumulated_depreciation: number;
  wdv_after: number;
  created_at: string;
}

interface MaintenanceRecord {
  id: string;
  maintenance_date: string;
  maintenance_type: string;
  description: string;
  cost: number;
  vendor_name?: string;
  next_maintenance_date?: string;
}

export function AssetView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [asset, setAsset] = useState<FixedAsset | null>(null);
  const [depreciationHistory, setDepreciationHistory] = useState<DepreciationEntry[]>([]);
  const [maintenanceRecords, setMaintenanceRecords] = useState<MaintenanceRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      fetchAsset();
      fetchDepreciationHistory();
      fetchMaintenanceRecords();
    }
  }, [id]);

  const fetchAsset = async () => {
    try {
      setLoading(true);
      const response = await fixedAssetsApi.getAsset(id!);
      setAsset(response.data);
    } catch (error) {
      console.error('Failed to fetch asset:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDepreciationHistory = async () => {
    try {
      const response = await fixedAssetsApi.getAssetDepreciationHistory(id!);
      setDepreciationHistory(response.data || []);
    } catch (error) {
      console.error('Failed to fetch depreciation history:', error);
    }
  };

  const fetchMaintenanceRecords = async () => {
    try {
      const response = await (fixedAssetsApi as any).getAssetMaintenance(id!);
      setMaintenanceRecords(response.data || []);
    } catch (error) {
      console.error('Failed to fetch maintenance records:', error);
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

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
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

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <p className="text-sm text-slate-500">Loading...</p>
      </div>
    );
  }

  if (!asset) {
    return (
      <div className="flex flex-col items-center justify-center py-8">
        <Package className="mb-4 h-12 w-12 text-slate-300" />
        <p className="text-sm text-slate-500">Asset not found</p>
        <Button variant="link" onClick={() => navigate('/admin/fixed-assets/assets')}>
          Back to Assets
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/admin/fixed-assets/assets')}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-slate-900">{asset.asset_code}</h1>
              {getStatusBadge(asset.status, asset.is_fully_depreciated)}
            </div>
            <p className="text-sm text-slate-500">{asset.asset_name}</p>
          </div>
        </div>
        {asset.status === 'DRAFT' && (
          <Button onClick={() => navigate(`/admin/fixed-assets/assets/${id}/edit`)}>
            <Edit className="mr-2 h-4 w-4" />
            Edit Asset
          </Button>
        )}
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
            <IndianRupee className="h-4 w-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(asset.total_cost)}</div>
            <p className="text-xs text-slate-500">Acquisition value</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Accumulated Depreciation</CardTitle>
            <TrendingDown className="h-4 w-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {formatCurrency(asset.accumulated_depreciation)}
            </div>
            <p className="text-xs text-slate-500">Total depreciation</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Written Down Value</CardTitle>
            <IndianRupee className="h-4 w-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600">
              {formatCurrency(asset.wdv_value)}
            </div>
            <p className="text-xs text-slate-500">Current book value</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Depreciation Rate</CardTitle>
            <Settings className="h-4 w-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{asset.depreciation_rate || 0}%</div>
            <p className="text-xs text-slate-500">{asset.depreciation_method}</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="details" className="space-y-4">
        <TabsList>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="depreciation">Depreciation History</TabsTrigger>
          <TabsTrigger value="maintenance">Maintenance</TabsTrigger>
          <TabsTrigger value="documents">Documents</TabsTrigger>
        </TabsList>

        <TabsContent value="details" className="space-y-4">
          <div className="grid gap-6 md:grid-cols-2">
            {/* Basic Information */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Package className="h-4 w-4" />
                  Basic Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-slate-500">Asset Code</p>
                    <p className="font-medium">{asset.asset_code}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Asset Name</p>
                    <p className="font-medium">{asset.asset_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Category</p>
                    <p className="font-medium">{asset.category_name || '-'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Status</p>
                    {getStatusBadge(asset.status, asset.is_fully_depreciated)}
                  </div>
                </div>
                {asset.description && (
                  <div>
                    <p className="text-sm text-slate-500">Description</p>
                    <p className="font-medium">{asset.description}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Location & Custodian */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MapPin className="h-4 w-4" />
                  Location & Custodian
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-slate-500">Location</p>
                    <p className="font-medium">{asset.location_name || '-'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Department</p>
                    <p className="font-medium">{asset.department_name || '-'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Custodian</p>
                    <p className="font-medium">{asset.custodian_name || '-'}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Acquisition Details */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  Acquisition Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-slate-500">Acquisition Date</p>
                    <p className="font-medium">{formatDate(asset.acquisition_date)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Put to Use Date</p>
                    <p className="font-medium">{formatDate(asset.put_to_use_date)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Acquisition Type</p>
                    <p className="font-medium">{asset.acquisition_type}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Vendor</p>
                    <p className="font-medium">{asset.vendor_name || '-'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Invoice Number</p>
                    <p className="font-medium">{asset.invoice_number || '-'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Invoice Date</p>
                    <p className="font-medium">{formatDate(asset.invoice_date)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Technical Details */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Tag className="h-4 w-4" />
                  Technical Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-slate-500">Serial Number</p>
                    <p className="font-medium">{asset.serial_number || '-'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Model Number</p>
                    <p className="font-medium">{asset.model_number || '-'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Manufacturer</p>
                    <p className="font-medium">{asset.manufacturer || '-'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Warranty Expiry</p>
                    <p className="font-medium">{formatDate(asset.warranty_expiry)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Financial Details */}
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <IndianRupee className="h-4 w-4" />
                  Financial Details
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 md:grid-cols-6">
                  <div>
                    <p className="text-sm text-slate-500">Total Cost</p>
                    <p className="font-medium">{formatCurrency(asset.total_cost)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Residual Value</p>
                    <p className="font-medium">{formatCurrency(asset.residual_value)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Depreciable Value</p>
                    <p className="font-medium">{formatCurrency(asset.depreciable_value)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Depreciation Method</p>
                    <p className="font-medium">{asset.depreciation_method}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Depreciation Rate</p>
                    <p className="font-medium">{asset.depreciation_rate || 0}%</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Useful Life</p>
                    <p className="font-medium">{asset.useful_life_months ? `${asset.useful_life_months} months` : '-'}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="depreciation">
          <Card>
            <CardHeader>
              <CardTitle>Depreciation History</CardTitle>
              <CardDescription>Monthly depreciation entries for this asset</CardDescription>
            </CardHeader>
            <CardContent>
              {depreciationHistory.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <TrendingDown className="mb-4 h-12 w-12 text-slate-300" />
                  <p className="text-sm text-slate-500">No depreciation entries yet</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Period</TableHead>
                      <TableHead className="text-right">Depreciation Amount</TableHead>
                      <TableHead className="text-right">Accumulated Depreciation</TableHead>
                      <TableHead className="text-right">WDV After</TableHead>
                      <TableHead>Posted Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {depreciationHistory.map((entry) => (
                      <TableRow key={entry.id}>
                        <TableCell className="font-medium">{entry.period}</TableCell>
                        <TableCell className="text-right">{formatCurrency(entry.depreciation_amount)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(entry.accumulated_depreciation)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(entry.wdv_after)}</TableCell>
                        <TableCell>{formatDate(entry.created_at)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="maintenance">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Maintenance Records</CardTitle>
                <CardDescription>Service and maintenance history</CardDescription>
              </div>
              <Button onClick={() => navigate(`/admin/fixed-assets/maintenance/new?assetId=${id}`)}>
                Add Maintenance
              </Button>
            </CardHeader>
            <CardContent>
              {maintenanceRecords.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <Settings className="mb-4 h-12 w-12 text-slate-300" />
                  <p className="text-sm text-slate-500">No maintenance records yet</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Vendor</TableHead>
                      <TableHead className="text-right">Cost</TableHead>
                      <TableHead>Next Due</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {maintenanceRecords.map((record) => (
                      <TableRow key={record.id}>
                        <TableCell>{formatDate(record.maintenance_date)}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{record.maintenance_type}</Badge>
                        </TableCell>
                        <TableCell>{record.description}</TableCell>
                        <TableCell>{record.vendor_name || '-'}</TableCell>
                        <TableCell className="text-right">{formatCurrency(record.cost)}</TableCell>
                        <TableCell>{formatDate(record.next_maintenance_date)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="documents">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Documents</CardTitle>
                <CardDescription>Attached documents and files</CardDescription>
              </div>
              <Button variant="outline">
                <FileText className="mr-2 h-4 w-4" />
                Upload Document
              </Button>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col items-center justify-center py-8">
                <FileText className="mb-4 h-12 w-12 text-slate-300" />
                <p className="text-sm text-slate-500">No documents attached</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
