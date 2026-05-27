/**
 * Fixed Deposit Form Page
 */

import { ArrowLeft, Save, Calculator } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { CustomerPicker } from '@/components/common/CustomerPicker';
import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import type {
  FDProduct,
  FDCustomerCategory,
  FDInterestPayoutFrequency,
} from '@/services/fixedDepositService';
import fixedDepositService, { FDCompoundingFrequency } from '@/services/fixedDepositService';
import { getErrorMessage } from '@/lib/errorMessage';

const CUSTOMER_CATEGORIES: { value: FDCustomerCategory; label: string }[] = [
  { value: 'GENERAL', label: 'General' },
  { value: 'SENIOR_CITIZEN', label: 'Senior Citizen' },
  { value: 'STAFF', label: 'Staff' },
  { value: 'NRI', label: 'NRI' },
  { value: 'CORPORATE', label: 'Corporate' },
];

const INTEREST_PAYOUT_OPTIONS: { value: FDInterestPayoutFrequency; label: string }[] = [
  { value: 'MONTHLY', label: 'Monthly' },
  { value: 'QUARTERLY', label: 'Quarterly' },
  { value: 'HALF_YEARLY', label: 'Half-Yearly' },
  { value: 'ANNUALLY', label: 'Annually' },
  { value: 'ON_MATURITY', label: 'On Maturity' },
];

const PAYOUT_MODES = [
  { value: 'BANK_TRANSFER', label: 'Bank Transfer' },
  { value: 'CAPITALIZE', label: 'Capitalize' },
  { value: 'CHEQUE', label: 'Cheque' },
];

export default function FDForm() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [products, setProducts] = useState<FDProduct[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<FDProduct | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [calculatedRate, setCalculatedRate] = useState<number | null>(null);
  const [calculatedMaturity, setCalculatedMaturity] = useState<number | null>(null);

  const organizationId = useRequiredActiveOrganizationId();

  const [formData, setFormData] = useState({
    product_id: '',
    customer_id: '',
    customer_category: 'GENERAL' as FDCustomerCategory,
    deposit_amount: 0,
    deposit_date: new Date().toISOString().split('T')[0],
    value_date: new Date().toISOString().split('T')[0],
    tenure_days: 365,
    interest_payout_frequency: '' as FDInterestPayoutFrequency | '',
    interest_payout_mode: 'BANK_TRANSFER',
    auto_renew: false,
    renewal_tenure_days: null as number | null,
    remarks: '',
    nominees: [] as {
      nominee_name: string;
      relationship: string;
      share_percentage: number;
    }[],
  });

  useEffect(() => {
    loadProducts();
  }, [organizationId]);

  useEffect(() => {
    setFormData((current) => ({
      ...current,
    }));
  }, [organizationId]);

  const loadProducts = async () => {
    try {
      setLoading(true);
      const response = await fixedDepositService.listProducts({
        active_only: true,
      });
      setProducts(response.items);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load FD products',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleProductChange = (productId: string) => {
    const product = products.find((p) => p.id === productId);
    setSelectedProduct(product || null);
    setFormData({
      ...formData,
      product_id: productId,
      interest_payout_frequency: product?.interest_payout_frequency || '',
    });
    setCalculatedRate(null);
    setCalculatedMaturity(null);
  };

  const calculateRate = async () => {
    if (!formData.product_id || !formData.deposit_amount || !formData.tenure_days) {
      toast({
        title: 'Missing Information',
        description: 'Please select product, enter amount and tenure',
        variant: 'destructive',
      });
      return;
    }

    try {
      const result = await fixedDepositService.getApplicableRate({
        product_id: formData.product_id,
        tenure_days: formData.tenure_days,
        amount: formData.deposit_amount,
        customer_category: formData.customer_category,
      });
      setCalculatedRate(result.interest_rate);

      // Calculate maturity amount (simple calculation for display)
      const principal = formData.deposit_amount;
      const rate = result.interest_rate / 100;
      const years = formData.tenure_days / 365;
      const maturity = principal * Math.pow(1 + rate / 4, 4 * years); // Quarterly compounding
      setCalculatedMaturity(Math.round(maturity * 100) / 100);
    } catch (error: unknown) {
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'No applicable rate found for given parameters'),
        variant: 'destructive',
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.product_id) {
      toast({
        title: 'Validation Error',
        description: 'Please select an FD product',
        variant: 'destructive',
      });
      return;
    }

    if (!formData.deposit_amount || formData.deposit_amount <= 0) {
      toast({
        title: 'Validation Error',
        description: 'Please enter a valid deposit amount',
        variant: 'destructive',
      });
      return;
    }

    if (!formData.customer_id) {
      toast({
        title: 'Validation Error',
        description: 'Please select a customer',
        variant: 'destructive',
      });
      return;
    }

    const submitData = {
      ...formData,
      interest_payout_frequency: formData.interest_payout_frequency || undefined,
    };

    try {
      setSaving(true);
      const fd = await fixedDepositService.createDeposit(
        submitData as Parameters<typeof fixedDepositService.createDeposit>[0],
      );
      toast({
        title: 'Success',
        description: `Fixed deposit ${fd.fd_number} created successfully`,
      });
      navigate(`/admin/fixed-deposits/${fd.id}`);
    } catch (error: unknown) {
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to create fixed deposit'),
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };
  if (loading) {
    return (
      <div className="container mx-auto py-6">
        <div className="py-8 text-center">Loading...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="New Fixed Deposit"
        subtitle="Create a new fixed deposit account"
        breadcrumbs={[{ label: 'Fixed Deposits', to: '/admin/fixed-deposits' }, { label: 'New' }]}
      />

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Product Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Product Selection</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="product_id">FD Product *</Label>
              <Select value={formData.product_id} onValueChange={handleProductChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Select product" />
                </SelectTrigger>
                <SelectContent>
                  {products.map((product) => (
                    <SelectItem key={product.id} value={product.id}>
                      {product.product_code} - {product.product_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="customer_id">Customer *</Label>
              <CustomerPicker
                value={formData.customer_id || null}
                onChange={(id) => setFormData({ ...formData, customer_id: id ?? '' })}
                placeholder="Search and select customer"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="customer_category">Customer Category</Label>
              <Select
                value={formData.customer_category}
                onValueChange={(value: FDCustomerCategory) =>
                  setFormData({ ...formData, customer_category: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CUSTOMER_CATEGORIES.map((cat) => (
                    <SelectItem key={cat.value} value={cat.value}>
                      {cat.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Deposit Details */}
        <Card>
          <CardHeader>
            <CardTitle>Deposit Details</CardTitle>
            {selectedProduct && (
              <CardDescription>
                Amount: {selectedProduct.min_amount.toLocaleString()} -{' '}
                {selectedProduct.max_amount?.toLocaleString() || 'No limit'} | Tenure:{' '}
                {selectedProduct.min_tenure_days} - {selectedProduct.max_tenure_days} days
              </CardDescription>
            )}
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="deposit_amount">Deposit Amount *</Label>
              <Input
                id="deposit_amount"
                type="number"
                value={formData.deposit_amount || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    deposit_amount: parseFloat(e.target.value) || 0,
                  })
                }
                min={selectedProduct?.min_amount || 0}
                max={selectedProduct?.max_amount || undefined}
                step="0.01"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="tenure_days">Tenure (Days) *</Label>
              <Input
                id="tenure_days"
                type="number"
                value={formData.tenure_days}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    tenure_days: parseInt(e.target.value) || 0,
                  })
                }
                min={selectedProduct?.min_tenure_days || 7}
                max={selectedProduct?.max_tenure_days || 3650}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="deposit_date">Deposit Date</Label>
              <Input
                id="deposit_date"
                type="date"
                value={formData.deposit_date}
                onChange={(e) => setFormData({ ...formData, deposit_date: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="value_date">Value Date (Interest Start)</Label>
              <Input
                id="value_date"
                type="date"
                value={formData.value_date}
                onChange={(e) => setFormData({ ...formData, value_date: e.target.value })}
              />
            </div>
          </CardContent>
        </Card>

        {/* Interest Calculation */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Interest Calculation</CardTitle>
                <CardDescription>Calculate applicable rate and maturity amount</CardDescription>
              </div>
              <Button type="button" variant="outline" onClick={calculateRate}>
                <Calculator className="mr-2 h-4 w-4" />
                Calculate
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {calculatedRate !== null && (
              <div className="grid grid-cols-1 gap-4 rounded-lg bg-muted p-4 md:grid-cols-3">
                <div>
                  <p className="text-sm text-muted-foreground">Applicable Rate</p>
                  <p className="text-2xl font-bold text-green-600">{calculatedRate.toFixed(2)}%</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Estimated Maturity</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {formatIndianCompactCurrency(calculatedMaturity || 0)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Estimated Interest</p>
                  <p className="text-2xl font-bold">
                    {formatIndianCompactCurrency(
                      (calculatedMaturity || 0) - formData.deposit_amount,
                    )}
                  </p>
                </div>
              </div>
            )}
            {calculatedRate === null && (
              <p className="py-4 text-center text-muted-foreground">
                Click "Calculate" to see applicable rate and maturity amount
              </p>
            )}
          </CardContent>
        </Card>

        {/* Interest Payout */}
        <Card>
          <CardHeader>
            <CardTitle>Interest Payout</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="interest_payout_frequency">Payout Frequency</Label>
              <Select
                value={formData.interest_payout_frequency}
                onValueChange={(value: FDInterestPayoutFrequency) =>
                  setFormData({ ...formData, interest_payout_frequency: value })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Use product default" />
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
              <Label htmlFor="interest_payout_mode">Payout Mode</Label>
              <Select
                value={formData.interest_payout_mode}
                onValueChange={(value) => setFormData({ ...formData, interest_payout_mode: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PAYOUT_MODES.map((mode) => (
                    <SelectItem key={mode.value} value={mode.value}>
                      {mode.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
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
                <Label>Enable Auto Renewal</Label>
                <p className="text-sm text-muted-foreground">Automatically renew FD on maturity</p>
              </div>
              <Switch
                checked={formData.auto_renew}
                onCheckedChange={(checked) => setFormData({ ...formData, auto_renew: checked })}
              />
            </div>
            {formData.auto_renew && (
              <div className="space-y-2">
                <Label htmlFor="renewal_tenure_days">Renewal Tenure (Days)</Label>
                <Input
                  id="renewal_tenure_days"
                  type="number"
                  value={formData.renewal_tenure_days || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      renewal_tenure_days: e.target.value ? parseInt(e.target.value) : null,
                    })
                  }
                  placeholder="Same as original tenure"
                />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Remarks */}
        <Card>
          <CardHeader>
            <CardTitle>Additional Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Label htmlFor="remarks">Remarks</Label>
              <Textarea
                id="remarks"
                value={formData.remarks}
                onChange={(e) => setFormData({ ...formData, remarks: e.target.value })}
                placeholder="Any additional notes..."
                rows={3}
              />
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex justify-end gap-4">
          <Button type="button" variant="outline" onClick={() => navigate('/admin/fixed-deposits')}>
            Cancel
          </Button>
          <Button type="submit" disabled={saving}>
            <Save className="mr-2 h-4 w-4" />
            {saving ? 'Creating...' : 'Create Fixed Deposit'}
          </Button>
        </div>
      </form>
    </div>
  );
}
