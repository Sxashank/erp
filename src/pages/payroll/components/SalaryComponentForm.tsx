/**
 * Salary Component Form Page
 */

import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Save } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import payrollService, { SalaryComponent } from '@/services/payrollService';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';

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
    organization_id: organizationId,
    component_code: '',
    component_name: '',
    component_type: 'EARNING',
    category: 'ALLOWANCE',
    calculation_type: 'FIXED',
    percentage_of: '',
    percentage_value: '',
    formula: '',
    is_taxable: true,
    is_pro_rated: true,
    affects_pf: false,
    affects_esi: false,
    affects_pt: false,
    display_order: 0,
    is_active: true,
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
        organization_id: data.organization_id,
        component_code: data.component_code,
        component_name: data.component_name,
        component_type: data.component_type,
        category: data.category,
        calculation_type: data.calculation_type,
        percentage_of: data.percentage_of || '',
        percentage_value: data.percentage_value?.toString() || '',
        formula: data.formula || '',
        is_taxable: data.is_taxable,
        is_pro_rated: data.is_pro_rated,
        affects_pf: data.affects_pf,
        affects_esi: data.affects_esi,
        affects_pt: data.affects_pt,
        display_order: data.display_order,
        is_active: data.is_active,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load component',
        variant: 'destructive',
      });
      navigate('/payroll/components');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.component_code || !formData.component_name) {
      toast({
        title: 'Validation Error',
        description: 'Code and name are required',
        variant: 'destructive',
      });
      return;
    }

    try {
      setSaving(true);

      const payload: any = {
        ...formData,
        percentage_value: formData.percentage_value
          ? parseFloat(formData.percentage_value)
          : undefined,
        percentage_of: formData.percentage_of || undefined,
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

      navigate('/payroll/components');
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to save component',
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
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/payroll/components')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <div>
          <h1 className="text-2xl font-bold">
            {isEdit ? 'Edit' : 'New'} Salary Component
          </h1>
          <p className="text-muted-foreground">
            {isEdit ? 'Update component details' : 'Create a new salary component'}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="component_code">Component Code *</Label>
                  <Input
                    id="component_code"
                    value={formData.component_code}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        component_code: e.target.value.toUpperCase(),
                      })
                    }
                    placeholder="e.g., BASIC, HRA, PF"
                    disabled={isEdit}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="display_order">Display Order</Label>
                  <Input
                    id="display_order"
                    type="number"
                    value={formData.display_order}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        display_order: parseInt(e.target.value) || 0,
                      })
                    }
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="component_name">Component Name *</Label>
                <Input
                  id="component_name"
                  value={formData.component_name}
                  onChange={(e) =>
                    setFormData({ ...formData, component_name: e.target.value })
                  }
                  placeholder="e.g., Basic Salary, House Rent Allowance"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="component_type">Type *</Label>
                  <Select
                    value={formData.component_type}
                    onValueChange={(value) =>
                      setFormData({ ...formData, component_type: value })
                    }
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
                    onValueChange={(value) =>
                      setFormData({ ...formData, category: value })
                    }
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
                <Label htmlFor="calculation_type">Calculation Type *</Label>
                <Select
                  value={formData.calculation_type}
                  onValueChange={(value) =>
                    setFormData({ ...formData, calculation_type: value })
                  }
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

              {formData.calculation_type === 'PERCENTAGE' && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="percentage_of">Percentage Of</Label>
                    <Input
                      id="percentage_of"
                      value={formData.percentage_of}
                      onChange={(e) =>
                        setFormData({ ...formData, percentage_of: e.target.value })
                      }
                      placeholder="e.g., BASIC, GROSS"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="percentage_value">Percentage Value (%)</Label>
                    <Input
                      id="percentage_value"
                      type="number"
                      step="0.01"
                      value={formData.percentage_value}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          percentage_value: e.target.value,
                        })
                      }
                      placeholder="e.g., 50"
                    />
                  </div>
                </>
              )}

              {formData.calculation_type === 'FORMULA' && (
                <div className="space-y-2">
                  <Label htmlFor="formula">Formula</Label>
                  <Textarea
                    id="formula"
                    value={formData.formula}
                    onChange={(e) =>
                      setFormData({ ...formData, formula: e.target.value })
                    }
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
                  id="is_taxable"
                  checked={formData.is_taxable}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, is_taxable: checked as boolean })
                  }
                />
                <Label htmlFor="is_taxable">Taxable (included in TDS calculation)</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_pro_rated"
                  checked={formData.is_pro_rated}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, is_pro_rated: checked as boolean })
                  }
                />
                <Label htmlFor="is_pro_rated">Pro-rated (adjusted for LOP days)</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="affects_pf"
                  checked={formData.affects_pf}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, affects_pf: checked as boolean })
                  }
                />
                <Label htmlFor="affects_pf">Included in PF wage base</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="affects_esi"
                  checked={formData.affects_esi}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, affects_esi: checked as boolean })
                  }
                />
                <Label htmlFor="affects_esi">Included in ESI wage base</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="affects_pt"
                  checked={formData.affects_pt}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, affects_pt: checked as boolean })
                  }
                />
                <Label htmlFor="affects_pt">Included in Professional Tax base</Label>
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
                  id="is_active"
                  checked={formData.is_active}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, is_active: checked as boolean })
                  }
                />
                <Label htmlFor="is_active">Active</Label>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="flex justify-end gap-4 mt-6">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/payroll/components')}
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
