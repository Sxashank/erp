/**
 * Salary Component Form Page
 */

import { Save } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import payrollService, { SalaryComponent } from '@/services/payrollService';
import { getErrorMessage } from "@/lib/errorMessage";

const COMPONENT_TYPES = [
  { value: 'EARNING', label: 'Earning' },
  { value: 'DEDUCTION', label: 'Deduction' },
];

const CATEGORIES = [
  { value: 'BASIC', label: 'Basic' },
  { value: 'ALLOWANCE', label: 'Allowance' },
  { value: 'REIMBURSEMENT', label: 'Reimbursement' },
  { value: 'BONUS', label: 'Bonus' },
  { value: 'STATUTORY', label: 'Statutory' },
  { value: 'OTHER', label: 'Other' },
];

const CALCULATION_TYPES = [
  { value: 'FIXED', label: 'Fixed Amount' },
  { value: 'PERCENTAGE', label: 'Percentage' },
  { value: 'FORMULA', label: 'Formula' },
];

export default function SalaryComponentForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { toast } = useToast();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const organizationId = useRequiredActiveOrganizationId();

  const [formData, setFormData] = useState({
    componentCode: '',
    componentName: '',
    componentType: 'EARNING',
    category: 'ALLOWANCE',
    calculationType: 'FIXED',
    percentageOf: '',
    percentageValue: '',
    formula: '',
    isTaxable: true,
    isProRated: true,
    affectsPf: false,
    affectsEsi: false,
    affectsPt: false,
    displayOrder: 0,
    isActive: true,
  });

  useEffect(() => {
    if (isEdit && id) {
      loadComponent(id);
    }
  }, [id]);

  const loadComponent = async (componentId: string) => {
    try {
      setLoading(true);
      const data = await payrollService.getComponent(componentId);
      setFormData({
        componentCode: data.componentCode,
        componentName: data.componentName,
        componentType: data.componentType,
        category: data.category,
        calculationType: data.calculationType,
        percentageOf: data.percentageOf || '',
        percentageValue: data.percentageValue?.toString() || '',
        formula: data.formula || '',
        isTaxable: data.isTaxable,
        isProRated: data.isProRated,
        affectsPf: data.affectsPf,
        affectsEsi: data.affectsEsi,
        affectsPt: data.affectsPt,
        displayOrder: data.displayOrder,
        isActive: data.isActive,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load component',
        variant: 'destructive',
      });
      navigate('/admin/payroll/components');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.componentCode || !formData.componentName) {
      toast({
        title: 'Validation Error',
        description: 'Code and name are required',
        variant: 'destructive',
      });
      return;
    }

    try {
      setSaving(true);

      const payload: Record<string, unknown> = {
        ...formData,
        percentageValue: formData.percentageValue
          ? parseFloat(formData.percentageValue)
          : undefined,
        percentageOf: formData.percentageOf || undefined,
        formula: formData.formula || undefined,
      };

      if (isEdit && id) {
        await payrollService.updateComponent(id, payload);
        toast({
          title: 'Success',
          description: 'Component updated successfully',
        });
      } else {
        await payrollService.createComponent(payload);
        toast({
          title: 'Success',
          description: 'Component created successfully',
        });
      }

      navigate('/admin/payroll/components');
    } catch (error: unknown) {
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to save component'),
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
        title={`${isEdit ? 'Edit' : 'New'} Salary Component`}
        subtitle={isEdit ? 'Update component details' : 'Create a new salary component'}
        breadcrumbs={[
          { label: 'Salary Components', to: '/admin/payroll/components' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="componentCode">Component Code *</Label>
                  <Input
                    id="componentCode"
                    value={formData.componentCode}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        componentCode: e.target.value.toUpperCase(),
                      })
                    }
                    placeholder="e.g., BASIC, HRA, PF"
                    disabled={isEdit}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="displayOrder">Display Order</Label>
                  <Input
                    id="displayOrder"
                    type="number"
                    value={formData.displayOrder}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        displayOrder: parseInt(e.target.value) || 0,
                      })
                    }
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="componentName">Component Name *</Label>
                <Input
                  id="componentName"
                  value={formData.componentName}
                  onChange={(e) => setFormData({ ...formData, componentName: e.target.value })}
                  placeholder="e.g., Basic Salary, House Rent Allowance"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="componentType">Type *</Label>
                  <Select
                    value={formData.componentType}
                    onValueChange={(value) => setFormData({ ...formData, componentType: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {COMPONENT_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="category">Category *</Label>
                  <Select
                    value={formData.category}
                    onValueChange={(value) => setFormData({ ...formData, category: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {CATEGORIES.map((cat) => (
                        <SelectItem key={cat.value} value={cat.value}>
                          {cat.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Calculation Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="calculationType">Calculation Type *</Label>
                <Select
                  value={formData.calculationType}
                  onValueChange={(value) => setFormData({ ...formData, calculationType: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CALCULATION_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {formData.calculationType === 'PERCENTAGE' && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="percentageOf">Percentage Of</Label>
                    <Input
                      id="percentageOf"
                      value={formData.percentageOf}
                      onChange={(e) => setFormData({ ...formData, percentageOf: e.target.value })}
                      placeholder="e.g., BASIC, GROSS"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="percentageValue">Percentage Value (%)</Label>
                    <Input
                      id="percentageValue"
                      type="number"
                      step="0.01"
                      value={formData.percentageValue}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          percentageValue: e.target.value,
                        })
                      }
                      placeholder="e.g., 50"
                    />
                  </div>
                </>
              )}

              {formData.calculationType === 'FORMULA' && (
                <div className="space-y-2">
                  <Label htmlFor="formula">Formula</Label>
                  <Textarea
                    id="formula"
                    value={formData.formula}
                    onChange={(e) => setFormData({ ...formData, formula: e.target.value })}
                    placeholder="Enter calculation formula"
                    rows={3}
                  />
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Tax & Statutory</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="isTaxable"
                  checked={formData.isTaxable}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, isTaxable: checked as boolean })
                  }
                />
                <Label htmlFor="isTaxable">Taxable (included in TDS calculation)</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="isProRated"
                  checked={formData.isProRated}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, isProRated: checked as boolean })
                  }
                />
                <Label htmlFor="isProRated">Pro-rated (adjusted for LOP days)</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="affectsPf"
                  checked={formData.affectsPf}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, affectsPf: checked as boolean })
                  }
                />
                <Label htmlFor="affectsPf">Included in PF wage base</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="affectsEsi"
                  checked={formData.affectsEsi}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, affectsEsi: checked as boolean })
                  }
                />
                <Label htmlFor="affectsEsi">Included in ESI wage base</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="affectsPt"
                  checked={formData.affectsPt}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, affectsPt: checked as boolean })
                  }
                />
                <Label htmlFor="affectsPt">Included in Professional Tax base</Label>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="isActive"
                  checked={formData.isActive}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, isActive: checked as boolean })
                  }
                />
                <Label htmlFor="isActive">Active</Label>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="mt-6 flex justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/admin/payroll/components')}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={saving}>
            <Save className="mr-2 h-4 w-4" />
            {saving ? 'Saving...' : isEdit ? 'Update Component' : 'Create Component'}
          </Button>
        </div>
      </form>
    </div>
  );
}
