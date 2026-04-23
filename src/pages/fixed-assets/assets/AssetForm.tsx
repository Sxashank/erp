import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Save } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { fixedAssetsApi, organizationsApi, vendorsApi, unitsApi, departmentsApi } from '@/services/api';
import type { Organization, PaginatedResponse } from '@/types';

interface AssetCategory {
  id: string;
  category_code: string;
  category_name: string;
  depreciation_method: string;
  depreciation_rate_slm?: number;
  depreciation_rate_wdv?: number;
  useful_life_years?: number;
  residual_value_pct?: number;
}

interface Vendor {
  id: string;
  code: string;
  name: string;
}

interface Unit {
  id: string;
  code: string;
  name: string;
}

interface Department {
  id: string;
  code: string;
  name: string;
}

const ACQUISITION_TYPES = [
  { value: 'PURCHASE', label: 'Purchase' },
  { value: 'LEASE', label: 'Lease' },
  { value: 'DONATION', label: 'Donation' },
  { value: 'TRANSFER_IN', label: 'Transfer In' },
  { value: 'CONSTRUCTED', label: 'Constructed' },
];

const DEPRECIATION_METHODS = [
  { value: 'SLM', label: 'Straight Line Method (SLM)' },
  { value: 'WDV', label: 'Written Down Value (WDV)' },
  { value: 'UNIT_OF_PRODUCTION', label: 'Unit of Production' },
  { value: 'NO_DEPRECIATION', label: 'No Depreciation' },
];

export function AssetForm() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id;

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [categories, setCategories] = useState<AssetCategory[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);

  const [formData, setFormData] = useState({
    organization_id: '',
    asset_name: '',
    description: '',
    category_id: '',
    location_id: '',
    department_id: '',
    acquisition_date: '',
    acquisition_type: 'PURCHASE',
    vendor_id: '',
    invoice_number: '',
    invoice_date: '',
    po_number: '',
    acquisition_cost: '',
    installation_cost: '',
    other_costs: '',
    residual_value: '',
    useful_life_months: '',
    depreciation_method: '',
    depreciation_rate: '',
    make: '',
    model: '',
    serial_number: '',
    quantity: '1',
    warranty_start_date: '',
    warranty_expiry_date: '',
    insurance_policy_number: '',
    insurance_provider: '',
    insurance_expiry_date: '',
    insured_value: '',
    amc_vendor_id: '',
    amc_start_date: '',
    amc_expiry_date: '',
    amc_value: '',
    tags: '',
  });

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (formData.organization_id) {
      fetchCategories();
      fetchVendors();
      fetchUnits();
      fetchDepartments();
    }
  }, [formData.organization_id]);

  useEffect(() => {
    if (isEdit && id) {
      fetchAsset();
    }
  }, [id]);

  const fetchOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      const data: PaginatedResponse<Organization> = response.data;
      setOrganizations(data.items);
      if (!isEdit && data.items.length > 0) {
        setFormData((prev) => ({ ...prev, organization_id: data.items[0].id }));
      }
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await fixedAssetsApi.listCategories({
        organization_id: formData.organization_id,
        limit: 500,
      });
      setCategories(response.data.items || []);
    } catch (error) {
      console.error('Failed to fetch categories:', error);
    }
  };

  const fetchVendors = async () => {
    try {
      const response = await vendorsApi.list({
        organization_id: formData.organization_id,
        page_size: 500,
      });
      setVendors(response.data.items || []);
    } catch (error) {
      console.error('Failed to fetch vendors:', error);
    }
  };

  const fetchUnits = async () => {
    try {
      const response = await unitsApi.list({
        organization_id: formData.organization_id,
        page_size: 500,
      });
      setUnits(response.data.items || []);
    } catch (error) {
      console.error('Failed to fetch units:', error);
    }
  };

  const fetchDepartments = async () => {
    try {
      const response = await departmentsApi.list({
        organization_id: formData.organization_id,
        page_size: 500,
      });
      setDepartments(response.data.items || []);
    } catch (error) {
      console.error('Failed to fetch departments:', error);
    }
  };

  const fetchAsset = async () => {
    try {
      setLoading(true);
      const response = await fixedAssetsApi.getAsset(id!);
      const asset = response.data;
      setFormData({
        organization_id: asset.organization_id,
        asset_name: asset.asset_name,
        description: asset.description || '',
        category_id: asset.category_id,
        location_id: asset.location_id || '',
        department_id: asset.department_id || '',
        acquisition_date: asset.acquisition_date?.split('T')[0] || '',
        acquisition_type: asset.acquisition_type,
        vendor_id: asset.vendor_id || '',
        invoice_number: asset.invoice_number || '',
        invoice_date: asset.invoice_date?.split('T')[0] || '',
        po_number: asset.po_number || '',
        acquisition_cost: asset.acquisition_cost?.toString() || '',
        installation_cost: asset.installation_cost?.toString() || '',
        other_costs: asset.other_costs?.toString() || '',
        residual_value: asset.residual_value?.toString() || '',
        useful_life_months: asset.useful_life_months?.toString() || '',
        depreciation_method: asset.depreciation_method,
        depreciation_rate: asset.depreciation_rate?.toString() || '',
        make: asset.make || '',
        model: asset.model || '',
        serial_number: asset.serial_number || '',
        quantity: asset.quantity?.toString() || '1',
        warranty_start_date: asset.warranty_start_date?.split('T')[0] || '',
        warranty_expiry_date: asset.warranty_expiry_date?.split('T')[0] || '',
        insurance_policy_number: asset.insurance_policy_number || '',
        insurance_provider: asset.insurance_provider || '',
        insurance_expiry_date: asset.insurance_expiry_date?.split('T')[0] || '',
        insured_value: asset.insured_value?.toString() || '',
        amc_vendor_id: asset.amc_vendor_id || '',
        amc_start_date: asset.amc_start_date?.split('T')[0] || '',
        amc_expiry_date: asset.amc_expiry_date?.split('T')[0] || '',
        amc_value: asset.amc_value?.toString() || '',
        tags: asset.tags ? JSON.stringify(asset.tags) : '',
      });
    } catch (error) {
      console.error('Failed to fetch asset:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryChange = (categoryId: string) => {
    const category = categories.find((c) => c.id === categoryId);
    if (category) {
      setFormData((prev) => ({
        ...prev,
        category_id: categoryId,
        depreciation_method: category.depreciation_method,
        depreciation_rate:
          category.depreciation_method === 'SLM'
            ? category.depreciation_rate_slm?.toString() || ''
            : category.depreciation_rate_wdv?.toString() || '',
        useful_life_months: category.useful_life_years
          ? (category.useful_life_years * 12).toString()
          : '',
      }));
    } else {
      setFormData((prev) => ({ ...prev, category_id: categoryId }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      const payload = {
        organization_id: formData.organization_id,
        asset_name: formData.asset_name,
        description: formData.description || null,
        category_id: formData.category_id,
        location_id: formData.location_id || null,
        department_id: formData.department_id || null,
        acquisition_date: formData.acquisition_date,
        acquisition_type: formData.acquisition_type,
        vendor_id: formData.vendor_id || null,
        invoice_number: formData.invoice_number || null,
        invoice_date: formData.invoice_date || null,
        po_number: formData.po_number || null,
        acquisition_cost: formData.acquisition_cost ? parseFloat(formData.acquisition_cost) : 0,
        installation_cost: formData.installation_cost ? parseFloat(formData.installation_cost) : 0,
        other_costs: formData.other_costs ? parseFloat(formData.other_costs) : 0,
        residual_value: formData.residual_value ? parseFloat(formData.residual_value) : null,
        useful_life_months: formData.useful_life_months ? parseInt(formData.useful_life_months) : null,
        depreciation_method: formData.depreciation_method,
        depreciation_rate: formData.depreciation_rate ? parseFloat(formData.depreciation_rate) : null,
        make: formData.make || null,
        model: formData.model || null,
        serial_number: formData.serial_number || null,
        quantity: formData.quantity ? parseInt(formData.quantity) : 1,
        warranty_start_date: formData.warranty_start_date || null,
        warranty_expiry_date: formData.warranty_expiry_date || null,
        insurance_policy_number: formData.insurance_policy_number || null,
        insurance_provider: formData.insurance_provider || null,
        insurance_expiry_date: formData.insurance_expiry_date || null,
        insured_value: formData.insured_value ? parseFloat(formData.insured_value) : null,
        amc_vendor_id: formData.amc_vendor_id || null,
        amc_start_date: formData.amc_start_date || null,
        amc_expiry_date: formData.amc_expiry_date || null,
        amc_value: formData.amc_value ? parseFloat(formData.amc_value) : null,
        tags: formData.tags ? JSON.parse(formData.tags) : null,
      };

      if (isEdit) {
        await fixedAssetsApi.updateAsset(id!, payload);
      } else {
        await fixedAssetsApi.createAsset(payload);
      }
      navigate('/admin/fixed-assets/assets');
    } catch (error) {
      console.error('Failed to save asset:', error);
    } finally {
      setSaving(false);
    }
  };

  const calculateTotalCost = () => {
    const acquisition = parseFloat(formData.acquisition_cost) || 0;
    const installation = parseFloat(formData.installation_cost) || 0;
    const other = parseFloat(formData.other_costs) || 0;
    return acquisition + installation + other;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <p className="text-sm text-slate-500">Loading...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEdit ? 'Edit Asset' : 'New Asset'}
        subtitle={isEdit ? 'Update asset details' : 'Create a new fixed asset'}
        breadcrumbs={[
          { label: 'Fixed Assets', to: '/admin/fixed-assets/assets' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit}>
        <Tabs defaultValue="basic" className="space-y-6">
          <TabsList>
            <TabsTrigger value="basic">Basic Info</TabsTrigger>
            <TabsTrigger value="acquisition">Acquisition</TabsTrigger>
            <TabsTrigger value="depreciation">Depreciation</TabsTrigger>
            <TabsTrigger value="physical">Physical Details</TabsTrigger>
            <TabsTrigger value="warranty">Warranty & AMC</TabsTrigger>
            <TabsTrigger value="insurance">Insurance</TabsTrigger>
          </TabsList>

          {/* Basic Information Tab */}
          <TabsContent value="basic">
            <Card>
              <CardHeader>
                <CardTitle>Basic Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="organization_id">Organization</Label>
                    <Select
                      value={formData.organization_id}
                      onValueChange={(value) => setFormData((prev) => ({ ...prev, organization_id: value }))}
                      disabled={isEdit}
                    >
                      <SelectTrigger>
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
                  <div className="space-y-2">
                    <Label htmlFor="category_id">Category</Label>
                    <Select
                      value={formData.category_id}
                      onValueChange={handleCategoryChange}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent>
                        {categories.map((cat) => (
                          <SelectItem key={cat.id} value={cat.id}>
                            {cat.category_code} - {cat.category_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="asset_name">Asset Name</Label>
                  <Input
                    id="asset_name"
                    value={formData.asset_name}
                    onChange={(e) => setFormData((prev) => ({ ...prev, asset_name: e.target.value }))}
                    placeholder="e.g., Dell Laptop - Latitude 5520"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
                    placeholder="Optional description"
                    rows={2}
                  />
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="location_id">Location</Label>
                    <Select
                      value={formData.location_id}
                      onValueChange={(value) => setFormData((prev) => ({ ...prev, location_id: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select location" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">None</SelectItem>
                        {units.map((unit) => (
                          <SelectItem key={unit.id} value={unit.id}>
                            {unit.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="department_id">Department</Label>
                    <Select
                      value={formData.department_id}
                      onValueChange={(value) => setFormData((prev) => ({ ...prev, department_id: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select department" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">None</SelectItem>
                        {departments.map((dept) => (
                          <SelectItem key={dept.id} value={dept.id}>
                            {dept.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Acquisition Tab */}
          <TabsContent value="acquisition">
            <Card>
              <CardHeader>
                <CardTitle>Acquisition Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="acquisition_date">Acquisition Date</Label>
                    <Input
                      id="acquisition_date"
                      type="date"
                      value={formData.acquisition_date}
                      onChange={(e) => setFormData((prev) => ({ ...prev, acquisition_date: e.target.value }))}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="acquisition_type">Acquisition Type</Label>
                    <Select
                      value={formData.acquisition_type}
                      onValueChange={(value) => setFormData((prev) => ({ ...prev, acquisition_type: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {ACQUISITION_TYPES.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="vendor_id">Vendor</Label>
                    <Select
                      value={formData.vendor_id}
                      onValueChange={(value) => setFormData((prev) => ({ ...prev, vendor_id: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select vendor" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">None</SelectItem>
                        {vendors.map((vendor) => (
                          <SelectItem key={vendor.id} value={vendor.id}>
                            {vendor.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="invoice_number">Invoice Number</Label>
                    <Input
                      id="invoice_number"
                      value={formData.invoice_number}
                      onChange={(e) => setFormData((prev) => ({ ...prev, invoice_number: e.target.value }))}
                      placeholder="Invoice #"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="invoice_date">Invoice Date</Label>
                    <Input
                      id="invoice_date"
                      type="date"
                      value={formData.invoice_date}
                      onChange={(e) => setFormData((prev) => ({ ...prev, invoice_date: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="po_number">PO Number</Label>
                    <Input
                      id="po_number"
                      value={formData.po_number}
                      onChange={(e) => setFormData((prev) => ({ ...prev, po_number: e.target.value }))}
                      placeholder="PO #"
                    />
                  </div>
                </div>

                <Separator />

                <p className="text-sm font-medium text-slate-700">Cost Breakdown</p>

                <div className="grid gap-4 sm:grid-cols-4">
                  <div className="space-y-2">
                    <Label htmlFor="acquisition_cost">Acquisition Cost</Label>
                    <Input
                      id="acquisition_cost"
                      type="number"
                      step="0.01"
                      value={formData.acquisition_cost}
                      onChange={(e) => setFormData((prev) => ({ ...prev, acquisition_cost: e.target.value }))}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="installation_cost">Installation Cost</Label>
                    <Input
                      id="installation_cost"
                      type="number"
                      step="0.01"
                      value={formData.installation_cost}
                      onChange={(e) => setFormData((prev) => ({ ...prev, installation_cost: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="other_costs">Other Costs</Label>
                    <Input
                      id="other_costs"
                      type="number"
                      step="0.01"
                      value={formData.other_costs}
                      onChange={(e) => setFormData((prev) => ({ ...prev, other_costs: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Total Cost</Label>
                    <Input
                      value={calculateTotalCost().toFixed(2)}
                      disabled
                      className="bg-slate-50 font-medium"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Depreciation Tab */}
          <TabsContent value="depreciation">
            <Card>
              <CardHeader>
                <CardTitle>Depreciation Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="depreciation_method">Depreciation Method</Label>
                    <Select
                      value={formData.depreciation_method}
                      onValueChange={(value) => setFormData((prev) => ({ ...prev, depreciation_method: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select method" />
                      </SelectTrigger>
                      <SelectContent>
                        {DEPRECIATION_METHODS.map((method) => (
                          <SelectItem key={method.value} value={method.value}>
                            {method.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="depreciation_rate">Depreciation Rate (%)</Label>
                    <Input
                      id="depreciation_rate"
                      type="number"
                      step="0.01"
                      value={formData.depreciation_rate}
                      onChange={(e) => setFormData((prev) => ({ ...prev, depreciation_rate: e.target.value }))}
                    />
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="useful_life_months">Useful Life (Months)</Label>
                    <Input
                      id="useful_life_months"
                      type="number"
                      value={formData.useful_life_months}
                      onChange={(e) => setFormData((prev) => ({ ...prev, useful_life_months: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="residual_value">Residual Value</Label>
                    <Input
                      id="residual_value"
                      type="number"
                      step="0.01"
                      value={formData.residual_value}
                      onChange={(e) => setFormData((prev) => ({ ...prev, residual_value: e.target.value }))}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Physical Details Tab */}
          <TabsContent value="physical">
            <Card>
              <CardHeader>
                <CardTitle>Physical Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="make">Make</Label>
                    <Input
                      id="make"
                      value={formData.make}
                      onChange={(e) => setFormData((prev) => ({ ...prev, make: e.target.value }))}
                      placeholder="e.g., Dell"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="model">Model</Label>
                    <Input
                      id="model"
                      value={formData.model}
                      onChange={(e) => setFormData((prev) => ({ ...prev, model: e.target.value }))}
                      placeholder="e.g., Latitude 5520"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="serial_number">Serial Number</Label>
                    <Input
                      id="serial_number"
                      value={formData.serial_number}
                      onChange={(e) => setFormData((prev) => ({ ...prev, serial_number: e.target.value }))}
                    />
                  </div>
                </div>

                <div className="space-y-2 max-w-[200px]">
                  <Label htmlFor="quantity">Quantity</Label>
                  <Input
                    id="quantity"
                    type="number"
                    value={formData.quantity}
                    onChange={(e) => setFormData((prev) => ({ ...prev, quantity: e.target.value }))}
                    min="1"
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Warranty & AMC Tab */}
          <TabsContent value="warranty">
            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Warranty</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="warranty_start_date">Start Date</Label>
                      <Input
                        id="warranty_start_date"
                        type="date"
                        value={formData.warranty_start_date}
                        onChange={(e) => setFormData((prev) => ({ ...prev, warranty_start_date: e.target.value }))}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="warranty_expiry_date">Expiry Date</Label>
                      <Input
                        id="warranty_expiry_date"
                        type="date"
                        value={formData.warranty_expiry_date}
                        onChange={(e) => setFormData((prev) => ({ ...prev, warranty_expiry_date: e.target.value }))}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Annual Maintenance Contract (AMC)</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="amc_vendor_id">AMC Vendor</Label>
                    <Select
                      value={formData.amc_vendor_id}
                      onValueChange={(value) => setFormData((prev) => ({ ...prev, amc_vendor_id: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select vendor" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">None</SelectItem>
                        {vendors.map((vendor) => (
                          <SelectItem key={vendor.id} value={vendor.id}>
                            {vendor.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="amc_start_date">Start Date</Label>
                      <Input
                        id="amc_start_date"
                        type="date"
                        value={formData.amc_start_date}
                        onChange={(e) => setFormData((prev) => ({ ...prev, amc_start_date: e.target.value }))}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="amc_expiry_date">Expiry Date</Label>
                      <Input
                        id="amc_expiry_date"
                        type="date"
                        value={formData.amc_expiry_date}
                        onChange={(e) => setFormData((prev) => ({ ...prev, amc_expiry_date: e.target.value }))}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="amc_value">AMC Value</Label>
                    <Input
                      id="amc_value"
                      type="number"
                      step="0.01"
                      value={formData.amc_value}
                      onChange={(e) => setFormData((prev) => ({ ...prev, amc_value: e.target.value }))}
                    />
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Insurance Tab */}
          <TabsContent value="insurance">
            <Card>
              <CardHeader>
                <CardTitle>Insurance Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="insurance_policy_number">Policy Number</Label>
                    <Input
                      id="insurance_policy_number"
                      value={formData.insurance_policy_number}
                      onChange={(e) => setFormData((prev) => ({ ...prev, insurance_policy_number: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="insurance_provider">Insurance Provider</Label>
                    <Input
                      id="insurance_provider"
                      value={formData.insurance_provider}
                      onChange={(e) => setFormData((prev) => ({ ...prev, insurance_provider: e.target.value }))}
                    />
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="insurance_expiry_date">Expiry Date</Label>
                    <Input
                      id="insurance_expiry_date"
                      type="date"
                      value={formData.insurance_expiry_date}
                      onChange={(e) => setFormData((prev) => ({ ...prev, insurance_expiry_date: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="insured_value">Insured Value</Label>
                    <Input
                      id="insured_value"
                      type="number"
                      step="0.01"
                      value={formData.insured_value}
                      onChange={(e) => setFormData((prev) => ({ ...prev, insured_value: e.target.value }))}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <div className="flex justify-end gap-4 mt-6">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/admin/fixed-assets/assets')}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={saving}>
            <Save className="mr-2 h-4 w-4" />
            {saving ? 'Saving...' : isEdit ? 'Update Asset' : 'Create Asset'}
          </Button>
        </div>
      </form>
    </div>
  );
}
