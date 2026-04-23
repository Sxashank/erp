import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Save } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { paymentTermsApi, organizationsApi } from '@/services/api';

interface Organization {
  id: string;
  name: string;
}

interface FormData {
  code: string;
  name: string;
  description: string;
  days: number;
  discount_days: number;
  discount_percent: number;
  organization_id: string;
  is_active: boolean;
}

export function PaymentTermsForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = !!id;

  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<FormData>({
    code: '',
    name: '',
    description: '',
    days: 0,
    discount_days: 0,
    discount_percent: 0,
    organization_id: '',
    is_active: true,
  });

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (isEdit && id) {
      fetchPaymentTerms(id);
    }
  }, [id, isEdit]);

  const fetchOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      setOrganizations(response.data.items);
      if (!isEdit && response.data.items.length > 0) {
        setFormData((prev) => ({
          ...prev,
          organization_id: response.data.items[0].id,
        }));
      }
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
    }
  };

  const fetchPaymentTerms = async (termsId: string) => {
    try {
      setLoading(true);
      const response = await paymentTermsApi.get(termsId);
      const data = response.data;
      setFormData({
        code: data.code,
        name: data.name,
        description: data.description || '',
        days: data.days,
        discount_days: data.discount_days,
        discount_percent: data.discount_percent,
        organization_id: data.organization_id,
        is_active: data.is_active,
      });
    } catch (error) {
      console.error('Failed to fetch payment terms:', error);
      setError('Failed to load payment terms');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!formData.code || !formData.name || !formData.organization_id) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      setSaving(true);
      if (isEdit && id) {
        await paymentTermsApi.update(id, {
          name: formData.name,
          description: formData.description || null,
          days: formData.days,
          discount_days: formData.discount_days,
          discount_percent: formData.discount_percent,
          is_active: formData.is_active,
        });
      } else {
        await paymentTermsApi.create({
          code: formData.code,
          name: formData.name,
          description: formData.description || null,
          days: formData.days,
          discount_days: formData.discount_days,
          discount_percent: formData.discount_percent,
          organization_id: formData.organization_id,
        });
      }
      navigate('/admin/ap-ar/payment-terms');
    } catch (error: any) {
      console.error('Failed to save payment terms:', error);
      setError(
        error.response?.data?.detail || 'Failed to save payment terms'
      );
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-sm text-slate-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEdit ? 'Edit Payment Terms' : 'New Payment Terms'}
        subtitle={
          isEdit
            ? 'Update payment terms details'
            : 'Create new payment terms for your organization'
        }
        breadcrumbs={[
          { label: 'Payment Terms', to: '/admin/ap-ar/payment-terms' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <CardTitle>Payment Terms Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {error && (
              <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
                {error}
              </div>
            )}

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="organization_id">
                  Organization <span className="text-red-500">*</span>
                </Label>
                <Select
                  value={formData.organization_id}
                  onValueChange={(value) =>
                    setFormData((prev) => ({ ...prev, organization_id: value }))
                  }
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

              <div>
                <Label htmlFor="code">
                  Code <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="code"
                  value={formData.code}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      code: e.target.value.toUpperCase(),
                    }))
                  }
                  placeholder="e.g., NET30, COD"
                  disabled={isEdit}
                  className="uppercase"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="name">
                Name <span className="text-red-500">*</span>
              </Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, name: e.target.value }))
                }
                placeholder="e.g., Net 30 Days"
              />
            </div>

            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    description: e.target.value,
                  }))
                }
                placeholder="Description of payment terms"
                rows={3}
              />
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div>
                <Label htmlFor="days">
                  Due Days <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="days"
                  type="number"
                  min="0"
                  max="365"
                  value={formData.days}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      days: parseInt(e.target.value) || 0,
                    }))
                  }
                />
                <p className="mt-1 text-xs text-slate-500">
                  Days from invoice date for payment
                </p>
              </div>

              <div>
                <Label htmlFor="discount_days">Discount Days</Label>
                <Input
                  id="discount_days"
                  type="number"
                  min="0"
                  max="365"
                  value={formData.discount_days}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      discount_days: parseInt(e.target.value) || 0,
                    }))
                  }
                />
                <p className="mt-1 text-xs text-slate-500">
                  Days for early payment discount
                </p>
              </div>

              <div>
                <Label htmlFor="discount_percent">Discount Percent (%)</Label>
                <Input
                  id="discount_percent"
                  type="number"
                  min="0"
                  max="100"
                  step="0.01"
                  value={formData.discount_percent}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      discount_percent: parseFloat(e.target.value) || 0,
                    }))
                  }
                />
                <p className="mt-1 text-xs text-slate-500">
                  Early payment discount percentage
                </p>
              </div>
            </div>

            {isEdit && (
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_active"
                  checked={formData.is_active}
                  onCheckedChange={(checked) =>
                    setFormData((prev) => ({
                      ...prev,
                      is_active: checked === true,
                    }))
                  }
                />
                <Label htmlFor="is_active" className="cursor-pointer">
                  Active
                </Label>
              </div>
            )}

            <div className="flex justify-end gap-4 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/admin/ap-ar/payment-terms')}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={saving}>
                <Save className="mr-2 h-4 w-4" />
                {saving ? 'Saving...' : isEdit ? 'Update' : 'Create'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  );
}
