/**
 * FD Product Form Page
 */

import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Save } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { PageHeader } from '@/components/common/PageHeader';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import fixedDepositService, {
  FDProduct,
  FDInterestPayoutFrequency,
  FDCompoundingFrequency,
} from '@/services/fixedDepositService';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';

const INTEREST_PAYOUT_OPTIONS: { value: FDInterestPayoutFrequency; label: string }[] = [
  { value: 'MONTHLY', label: 'Monthly' },
  { value: 'QUARTERLY', label: 'Quarterly' },
  { value: 'HALF_YEARLY', label: 'Half-Yearly' },
  { value: 'ANNUALLY', label: 'Annually' },
  { value: 'ON_MATURITY', label: 'On Maturity' },
];

const COMPOUNDING_OPTIONS: { value: FDCompoundingFrequency; label: string }[] = [
  { value: 'MONTHLY', label: 'Monthly' },
  { value: 'QUARTERLY', label: 'Quarterly' },
  { value: 'HALF_YEARLY', label: 'Half-Yearly' },
  { value: 'ANNUALLY', label: 'Annually' },
  { value: 'SIMPLE', label: 'Simple Interest' },
];

export default function FDProductForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { toast } = useToast();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const organizationId = useRequiredActiveOrganizationId();

  const [formData, setFormData] = useState<Partial<FDProduct>>({
    organization_id: organizationId,
    product_code: '',
    product_name: '',
    description: '',
    min_tenure_days: 7,
    max_tenure_days: 3650,
    min_amount: 1000,
    max_amount: undefined,
    interest_payout_frequency: 'QUARTERLY',
    compounding_frequency: 'QUARTERLY',
    allow_premature_withdrawal: true,
    premature_penalty_rate: 1.0,
    allow_auto_renewal: true,
    auto_renewal_tenure_days: undefined,
    allow_loan_against_fd: true,
    max_loan_percentage: 90,
    loan_interest_premium: 2,
    tds_applicable: true,
    tds_threshold: 40000,
    effective_from: new Date().toISOString().split('T')[0],
    effective_to: undefined,
    is_active: true,
  });

  useEffect(() => {
    if (isEdit && id) {
      loadProduct(id);
    }
  }, [id]);

  const loadProduct = async (productId: string) => {
    try {
      setLoading(true);
      const product = await fixedDepositService.getProduct(productId);
      setFormData(product);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load product',
        variant: 'destructive',
      });
      navigate('/admin/fixed-deposits/products');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.product_code || !formData.product_name) {
      toast({
        title: 'Validation Error',
        description: 'Product code and name are required',
        variant: 'destructive',
      });
      return;
    }

    try {
      setSaving(true);
      if (isEdit && id) {
        await fixedDepositService.updateProduct(id, formData);
        toast({
          title: 'Success',
          description: 'Product updated successfully',
        });
      } else {
        await fixedDepositService.createProduct(formData);
        toast({
          title: 'Success',
          description: 'Product created successfully',
        });
      }
      navigate('/admin/fixed-deposits/products');
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to save product',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center py-8">Loading...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title={isEdit ? 'Edit FD Product' : 'New FD Product'}
        subtitle="Configure fixed deposit product settings"
        breadcrumbs={[
          { label: 'FD Products', to: '/admin/fixed-deposits/products' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Details */}
        <Card>
          <CardHeader>
            <CardTitle>Basic Details</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="product_code">Product Code *</Label>
              <Input
                id="product_code"
                value={formData.product_code}
                onChange={(e) =>
                  setFormData({ ...formData, product_code: e.target.value })
                }
                placeholder="e.g., FD-STD"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="product_name">Product Name *</Label>
              <Input
                id="product_name"
                value={formData.product_name}
                onChange={(e) =>
                  setFormData({ ...formData, product_name: e.target.value })
                }
                placeholder="e.g., Standard Fixed Deposit"
                required
              />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description || ''}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                placeholder="Product description..."
                rows={3}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="effective_from">Effective From *</Label>
              <Input
                id="effective_from"
                type="date"
                value={formData.effective_from}
                onChange={(e) =>
                  setFormData({ ...formData, effective_from: e.target.value })
                }
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="effective_to">Effective To</Label>
              <Input
                id="effective_to"
                type="date"
                value={formData.effective_to || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    effective_to: e.target.value || undefined,
                  })
                }
              />
            </div>
          </CardContent>
        </Card>

        {/* Tenure & Amount */}
        <Card>
          <CardHeader>
            <CardTitle>Tenure & Amount Limits</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="min_tenure_days">Minimum Tenure (Days)</Label>
              <Input
                id="min_tenure_days"
                type="number"
                value={formData.min_tenure_days}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    min_tenure_days: parseInt(e.target.value),
                  })
                }
                min={1}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="max_tenure_days">Maximum Tenure (Days)</Label>
              <Input
                id="max_tenure_days"
                type="number"
                value={formData.max_tenure_days}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    max_tenure_days: parseInt(e.target.value),
                  })
                }
                min={1}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="min_amount">Minimum Amount</Label>
              <Input
                id="min_amount"
                type="number"
                value={formData.min_amount}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    min_amount: parseFloat(e.target.value),
                  })
                }
                min={0}
                step="0.01"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="max_amount">Maximum Amount</Label>
              <Input
                id="max_amount"
                type="number"
                value={formData.max_amount || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    max_amount: e.target.value
                      ? parseFloat(e.target.value)
                      : undefined,
                  })
                }
                min={0}
                step="0.01"
                placeholder="No limit"
              />
            </div>
          </CardContent>
        </Card>

        {/* Interest Configuration */}
        <Card>
          <CardHeader>
            <CardTitle>Interest Configuration</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="interest_payout_frequency">Interest Payout Frequency</Label>
              <Select
                value={formData.interest_payout_frequency}
                onValueChange={(value: FDInterestPayoutFrequency) =>
                  setFormData({ ...formData, interest_payout_frequency: value })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select frequency" />
                </SelectTrigger>
                <SelectContent>
                  {INTEREST_PAYOUT_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="compounding_frequency">Compounding Frequency</Label>
              <Select
                value={formData.compounding_frequency}
                onValueChange={(value: FDCompoundingFrequency) =>
                  setFormData({ ...formData, compounding_frequency: value })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select frequency" />
                </SelectTrigger>
                <SelectContent>
                  {COMPOUNDING_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Premature Withdrawal */}
        <Card>
          <CardHeader>
            <CardTitle>Premature Withdrawal</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>Allow Premature Withdrawal</Label>
                <p className="text-sm text-muted-foreground">
                  Allow customers to close FD before maturity
                </p>
              </div>
              <Switch
                checked={formData.allow_premature_withdrawal}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, allow_premature_withdrawal: checked })
                }
              />
            </div>
            {formData.allow_premature_withdrawal && (
              <div className="space-y-2">
                <Label htmlFor="premature_penalty_rate">
                  Penalty Rate (% reduction in interest)
                </Label>
                <Input
                  id="premature_penalty_rate"
                  type="number"
                  value={formData.premature_penalty_rate || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      premature_penalty_rate: parseFloat(e.target.value),
                    })
                  }
                  min={0}
                  max={10}
                  step="0.01"
                />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Auto Renewal */}
        <Card>
          <CardHeader>
            <CardTitle>Auto Renewal</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>Allow Auto Renewal</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically renew FD on maturity
                </p>
              </div>
              <Switch
                checked={formData.allow_auto_renewal}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, allow_auto_renewal: checked })
                }
              />
            </div>
            {formData.allow_auto_renewal && (
              <div className="space-y-2">
                <Label htmlFor="auto_renewal_tenure_days">
                  Auto Renewal Tenure (Days)
                </Label>
                <Input
                  id="auto_renewal_tenure_days"
                  type="number"
                  value={formData.auto_renewal_tenure_days || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      auto_renewal_tenure_days: e.target.value
                        ? parseInt(e.target.value)
                        : undefined,
                    })
                  }
                  placeholder="Same as original tenure"
                />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Loan Against FD */}
        <Card>
          <CardHeader>
            <CardTitle>Loan Against FD</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>Allow Loan Against FD</Label>
                <p className="text-sm text-muted-foreground">
                  Allow customers to take loan against this FD
                </p>
              </div>
              <Switch
                checked={formData.allow_loan_against_fd}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, allow_loan_against_fd: checked })
                }
              />
            </div>
            {formData.allow_loan_against_fd && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="max_loan_percentage">Max Loan %</Label>
                  <Input
                    id="max_loan_percentage"
                    type="number"
                    value={formData.max_loan_percentage || ''}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        max_loan_percentage: parseFloat(e.target.value),
                      })
                    }
                    min={0}
                    max={100}
                    step="0.01"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="loan_interest_premium">
                    Loan Interest Premium (%)
                  </Label>
                  <Input
                    id="loan_interest_premium"
                    type="number"
                    value={formData.loan_interest_premium || ''}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        loan_interest_premium: parseFloat(e.target.value),
                      })
                    }
                    min={0}
                    max={10}
                    step="0.01"
                  />
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* TDS Configuration */}
        <Card>
          <CardHeader>
            <CardTitle>TDS Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>TDS Applicable</Label>
                <p className="text-sm text-muted-foreground">
                  Deduct TDS on interest earned
                </p>
              </div>
              <Switch
                checked={formData.tds_applicable}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, tds_applicable: checked })
                }
              />
            </div>
            {formData.tds_applicable && (
              <div className="space-y-2">
                <Label htmlFor="tds_threshold">TDS Threshold (Annual Interest)</Label>
                <Input
                  id="tds_threshold"
                  type="number"
                  value={formData.tds_threshold || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      tds_threshold: parseFloat(e.target.value),
                    })
                  }
                  min={0}
                  step="0.01"
                />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Status */}
        <Card>
          <CardHeader>
            <CardTitle>Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <Label>Active</Label>
                <p className="text-sm text-muted-foreground">
                  Product is available for new FDs
                </p>
              </div>
              <Switch
                checked={formData.is_active}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, is_active: checked })
                }
              />
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/admin/fixed-deposits/products')}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={saving}>
            <Save className="mr-2 h-4 w-4" />
            {saving ? 'Saving...' : isEdit ? 'Update Product' : 'Create Product'}
          </Button>
        </div>
      </form>
    </div>
  );
}
