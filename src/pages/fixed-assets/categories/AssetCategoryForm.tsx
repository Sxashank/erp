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
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import { fixedAssetsApi, organizationsApi, accountsApi } from '@/services/api';
import type { Organization, PaginatedResponse } from '@/types';

interface AssetCategory {
  id: string;
  organization_id: string;
  category_code: string;
  category_name: string;
  description?: string;
  parent_category_id?: string;
  asset_type: string;
  depreciation_method: string;
  useful_life_years?: number;
  residual_value_pct?: number;
  depreciation_rate_slm?: number;
  depreciation_rate_wdv?: number;
  it_act_rate?: number;
  it_act_block?: string;
  capitalization_threshold?: number;
  gl_asset_account_id?: string;
  gl_accum_dep_account_id?: string;
  gl_dep_expense_account_id?: string;
  gl_disposal_gain_account_id?: string;
  gl_disposal_loss_account_id?: string;
  gl_revaluation_reserve_account_id?: string;
  gl_impairment_account_id?: string;
  requires_insurance: boolean;
  requires_amc: boolean;
  is_active: boolean;
}

interface Account {
  id: string;
  code: string;
  name: string;
}

const ASSET_TYPES = [
  { value: 'TANGIBLE', label: 'Tangible' },
  { value: 'INTANGIBLE', label: 'Intangible' },
  { value: 'RIGHT_OF_USE', label: 'Right of Use' },
];

const DEPRECIATION_METHODS = [
  { value: 'SLM', label: 'Straight Line Method (SLM)' },
  { value: 'WDV', label: 'Written Down Value (WDV)' },
  { value: 'UNIT_OF_PRODUCTION', label: 'Unit of Production' },
  { value: 'NO_DEPRECIATION', label: 'No Depreciation' },
];

export function AssetCategoryForm() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id;

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [parentCategories, setParentCategories] = useState<AssetCategory[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);

  const [formData, setFormData] = useState({
    organization_id: '',
    category_code: '',
    category_name: '',
    description: '',
    parent_category_id: '',
    asset_type: 'TANGIBLE',
    depreciation_method: 'SLM',
    useful_life_years: '',
    residual_value_pct: '',
    depreciation_rate_slm: '',
    depreciation_rate_wdv: '',
    it_act_rate: '',
    it_act_block: '',
    capitalization_threshold: '',
    gl_asset_account_id: '',
    gl_accum_dep_account_id: '',
    gl_dep_expense_account_id: '',
    gl_disposal_gain_account_id: '',
    gl_disposal_loss_account_id: '',
    gl_revaluation_reserve_account_id: '',
    gl_impairment_account_id: '',
    requires_insurance: false,
    requires_amc: false,
  });

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (formData.organization_id) {
      fetchParentCategories();
      fetchAccounts();
    }
  }, [formData.organization_id]);

  useEffect(() => {
    if (isEdit && id) {
      fetchCategory();
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

  const fetchParentCategories = async () => {
    try {
      const response = await fixedAssetsApi.listCategories({
        organization_id: formData.organization_id,
        limit: 500,
      });
      setParentCategories(response.data.items || []);
    } catch (error) {
      console.error('Failed to fetch parent categories:', error);
    }
  };

  const fetchAccounts = async () => {
    try {
      const response = await accountsApi.list({
        organization_id: formData.organization_id,
        page_size: 500,
      });
      setAccounts(response.data.items || []);
    } catch (error) {
      console.error('Failed to fetch accounts:', error);
    }
  };

  const fetchCategory = async () => {
    try {
      setLoading(true);
      const response = await fixedAssetsApi.getCategory(id!);
      const category = response.data;
      setFormData({
        organization_id: category.organization_id,
        category_code: category.category_code,
        category_name: category.category_name,
        description: category.description || '',
        parent_category_id: category.parent_category_id || '',
        asset_type: category.asset_type,
        depreciation_method: category.depreciation_method,
        useful_life_years: category.useful_life_years?.toString() || '',
        residual_value_pct: category.residual_value_pct?.toString() || '',
        depreciation_rate_slm: category.depreciation_rate_slm?.toString() || '',
        depreciation_rate_wdv: category.depreciation_rate_wdv?.toString() || '',
        it_act_rate: category.it_act_rate?.toString() || '',
        it_act_block: category.it_act_block || '',
        capitalization_threshold: category.capitalization_threshold?.toString() || '',
        gl_asset_account_id: category.gl_asset_account_id || '',
        gl_accum_dep_account_id: category.gl_accum_dep_account_id || '',
        gl_dep_expense_account_id: category.gl_dep_expense_account_id || '',
        gl_disposal_gain_account_id: category.gl_disposal_gain_account_id || '',
        gl_disposal_loss_account_id: category.gl_disposal_loss_account_id || '',
        gl_revaluation_reserve_account_id: category.gl_revaluation_reserve_account_id || '',
        gl_impairment_account_id: category.gl_impairment_account_id || '',
        requires_insurance: category.requires_insurance,
        requires_amc: category.requires_amc,
      });
    } catch (error) {
      console.error('Failed to fetch category:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      const payload = {
        ...formData,
        parent_category_id: formData.parent_category_id || null,
        useful_life_years: formData.useful_life_years ? parseInt(formData.useful_life_years) : null,
        residual_value_pct: formData.residual_value_pct ? parseFloat(formData.residual_value_pct) : null,
        depreciation_rate_slm: formData.depreciation_rate_slm ? parseFloat(formData.depreciation_rate_slm) : null,
        depreciation_rate_wdv: formData.depreciation_rate_wdv ? parseFloat(formData.depreciation_rate_wdv) : null,
        it_act_rate: formData.it_act_rate ? parseFloat(formData.it_act_rate) : null,
        it_act_block: formData.it_act_block || null,
        capitalization_threshold: formData.capitalization_threshold ? parseFloat(formData.capitalization_threshold) : null,
        gl_asset_account_id: formData.gl_asset_account_id || null,
        gl_accum_dep_account_id: formData.gl_accum_dep_account_id || null,
        gl_dep_expense_account_id: formData.gl_dep_expense_account_id || null,
        gl_disposal_gain_account_id: formData.gl_disposal_gain_account_id || null,
        gl_disposal_loss_account_id: formData.gl_disposal_loss_account_id || null,
        gl_revaluation_reserve_account_id: formData.gl_revaluation_reserve_account_id || null,
        gl_impairment_account_id: formData.gl_impairment_account_id || null,
      };

      if (isEdit) {
        await fixedAssetsApi.updateCategory(id!, payload);
      } else {
        await fixedAssetsApi.createCategory(payload);
      }
      navigate('/admin/fixed-assets/categories');
    } catch (error) {
      console.error('Failed to save category:', error);
    } finally {
      setSaving(false);
    }
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
        title={isEdit ? 'Edit Asset Category' : 'New Asset Category'}
        subtitle={
          isEdit ? 'Update asset category details' : 'Create a new asset category'
        }
        breadcrumbs={[
          { label: 'Asset Categories', to: '/admin/fixed-assets/categories' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit}>
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
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

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="category_code">Category Code</Label>
                  <Input
                    id="category_code"
                    value={formData.category_code}
                    onChange={(e) => setFormData((prev) => ({ ...prev, category_code: e.target.value }))}
                    placeholder="e.g., FA-COMP"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="category_name">Category Name</Label>
                  <Input
                    id="category_name"
                    value={formData.category_name}
                    onChange={(e) => setFormData((prev) => ({ ...prev, category_name: e.target.value }))}
                    placeholder="e.g., Computer Equipment"
                    required
                  />
                </div>
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

              <div className="space-y-2">
                <Label htmlFor="parent_category_id">Parent Category</Label>
                <Select
                  value={formData.parent_category_id}
                  onValueChange={(value) => setFormData((prev) => ({ ...prev, parent_category_id: value }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select parent (optional)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">No Parent</SelectItem>
                    {parentCategories
                      .filter((cat) => cat.id !== id)
                      .map((cat) => (
                        <SelectItem key={cat.id} value={cat.id}>
                          {cat.category_code} - {cat.category_name}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="asset_type">Asset Type</Label>
                  <Select
                    value={formData.asset_type}
                    onValueChange={(value) => setFormData((prev) => ({ ...prev, asset_type: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ASSET_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="capitalization_threshold">Capitalization Threshold</Label>
                  <Input
                    id="capitalization_threshold"
                    type="number"
                    step="0.01"
                    value={formData.capitalization_threshold}
                    onChange={(e) => setFormData((prev) => ({ ...prev, capitalization_threshold: e.target.value }))}
                    placeholder="Minimum value"
                  />
                </div>
              </div>

              <div className="flex items-center gap-6">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="requires_insurance"
                    checked={formData.requires_insurance}
                    onCheckedChange={(checked) =>
                      setFormData((prev) => ({ ...prev, requires_insurance: checked as boolean }))
                    }
                  />
                  <Label htmlFor="requires_insurance" className="text-sm font-normal">
                    Requires Insurance
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="requires_amc"
                    checked={formData.requires_amc}
                    onCheckedChange={(checked) =>
                      setFormData((prev) => ({ ...prev, requires_amc: checked as boolean }))
                    }
                  />
                  <Label htmlFor="requires_amc" className="text-sm font-normal">
                    Requires AMC
                  </Label>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Depreciation Settings */}
          <Card>
            <CardHeader>
              <CardTitle>Depreciation Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="depreciation_method">Depreciation Method</Label>
                <Select
                  value={formData.depreciation_method}
                  onValueChange={(value) => setFormData((prev) => ({ ...prev, depreciation_method: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
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

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="useful_life_years">Useful Life (Years)</Label>
                  <Input
                    id="useful_life_years"
                    type="number"
                    value={formData.useful_life_years}
                    onChange={(e) => setFormData((prev) => ({ ...prev, useful_life_years: e.target.value }))}
                    placeholder="e.g., 5"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="residual_value_pct">Residual Value (%)</Label>
                  <Input
                    id="residual_value_pct"
                    type="number"
                    step="0.01"
                    value={formData.residual_value_pct}
                    onChange={(e) => setFormData((prev) => ({ ...prev, residual_value_pct: e.target.value }))}
                    placeholder="e.g., 5"
                  />
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="depreciation_rate_slm">SLM Rate (%)</Label>
                  <Input
                    id="depreciation_rate_slm"
                    type="number"
                    step="0.01"
                    value={formData.depreciation_rate_slm}
                    onChange={(e) => setFormData((prev) => ({ ...prev, depreciation_rate_slm: e.target.value }))}
                    placeholder="e.g., 20"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="depreciation_rate_wdv">WDV Rate (%)</Label>
                  <Input
                    id="depreciation_rate_wdv"
                    type="number"
                    step="0.01"
                    value={formData.depreciation_rate_wdv}
                    onChange={(e) => setFormData((prev) => ({ ...prev, depreciation_rate_wdv: e.target.value }))}
                    placeholder="e.g., 40"
                  />
                </div>
              </div>

              <Separator />

              <p className="text-sm font-medium text-slate-700">Income Tax Act Settings</p>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="it_act_rate">IT Act Rate (%)</Label>
                  <Input
                    id="it_act_rate"
                    type="number"
                    step="0.01"
                    value={formData.it_act_rate}
                    onChange={(e) => setFormData((prev) => ({ ...prev, it_act_rate: e.target.value }))}
                    placeholder="e.g., 15"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="it_act_block">IT Act Block</Label>
                  <Input
                    id="it_act_block"
                    value={formData.it_act_block}
                    onChange={(e) => setFormData((prev) => ({ ...prev, it_act_block: e.target.value }))}
                    placeholder="e.g., Block III"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* GL Account Mapping */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>GL Account Mapping</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <div className="space-y-2">
                  <Label htmlFor="gl_asset_account_id">Asset Account</Label>
                  <Select
                    value={formData.gl_asset_account_id}
                    onValueChange={(value) => setFormData((prev) => ({ ...prev, gl_asset_account_id: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select account" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">None</SelectItem>
                      {accounts.map((acc) => (
                        <SelectItem key={acc.id} value={acc.id}>
                          {acc.code} - {acc.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="gl_accum_dep_account_id">Accumulated Depreciation</Label>
                  <Select
                    value={formData.gl_accum_dep_account_id}
                    onValueChange={(value) => setFormData((prev) => ({ ...prev, gl_accum_dep_account_id: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select account" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">None</SelectItem>
                      {accounts.map((acc) => (
                        <SelectItem key={acc.id} value={acc.id}>
                          {acc.code} - {acc.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="gl_dep_expense_account_id">Depreciation Expense</Label>
                  <Select
                    value={formData.gl_dep_expense_account_id}
                    onValueChange={(value) => setFormData((prev) => ({ ...prev, gl_dep_expense_account_id: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select account" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">None</SelectItem>
                      {accounts.map((acc) => (
                        <SelectItem key={acc.id} value={acc.id}>
                          {acc.code} - {acc.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="gl_disposal_gain_account_id">Disposal Gain</Label>
                  <Select
                    value={formData.gl_disposal_gain_account_id}
                    onValueChange={(value) => setFormData((prev) => ({ ...prev, gl_disposal_gain_account_id: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select account" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">None</SelectItem>
                      {accounts.map((acc) => (
                        <SelectItem key={acc.id} value={acc.id}>
                          {acc.code} - {acc.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="gl_disposal_loss_account_id">Disposal Loss</Label>
                  <Select
                    value={formData.gl_disposal_loss_account_id}
                    onValueChange={(value) => setFormData((prev) => ({ ...prev, gl_disposal_loss_account_id: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select account" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">None</SelectItem>
                      {accounts.map((acc) => (
                        <SelectItem key={acc.id} value={acc.id}>
                          {acc.code} - {acc.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="gl_revaluation_reserve_account_id">Revaluation Reserve</Label>
                  <Select
                    value={formData.gl_revaluation_reserve_account_id}
                    onValueChange={(value) => setFormData((prev) => ({ ...prev, gl_revaluation_reserve_account_id: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select account" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">None</SelectItem>
                      {accounts.map((acc) => (
                        <SelectItem key={acc.id} value={acc.id}>
                          {acc.code} - {acc.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="gl_impairment_account_id">Impairment Loss</Label>
                  <Select
                    value={formData.gl_impairment_account_id}
                    onValueChange={(value) => setFormData((prev) => ({ ...prev, gl_impairment_account_id: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select account" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">None</SelectItem>
                      {accounts.map((acc) => (
                        <SelectItem key={acc.id} value={acc.id}>
                          {acc.code} - {acc.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="flex justify-end gap-4 mt-6">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/admin/fixed-assets/categories')}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={saving}>
            <Save className="mr-2 h-4 w-4" />
            {saving ? 'Saving...' : isEdit ? 'Update Category' : 'Create Category'}
          </Button>
        </div>
      </form>
    </div>
  );
}
