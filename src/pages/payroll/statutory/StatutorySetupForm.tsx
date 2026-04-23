/**
 * Statutory Setup Form Page
 */

import { useState, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Save } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import payrollService, { StatutorySetup } from '@/services/payrollService';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';

const STATUTORY_TYPES = [
  { value: 'PF', label: 'Provident Fund (PF)' },
  { value: 'ESI', label: 'Employee State Insurance (ESI)' },
  { value: 'PT', label: 'Professional Tax (PT)' },
  { value: 'LWF', label: 'Labour Welfare Fund (LWF)' },
  { value: 'GRATUITY', label: 'Gratuity' },
];

const DEFAULT_VALUES: Record<string, Partial<StatutorySetup>> = {
  PF: {
    employer_contribution_pct: 12,
    employee_contribution_pct: 12,
    wage_ceiling: 15000,
    admin_charges_pct: 0.5,
  },
  ESI: {
    employer_contribution_pct: 3.25,
    employee_contribution_pct: 0.75,
    wage_ceiling: 21000,
  },
  PT: {
    employer_contribution_pct: 0,
    employee_contribution_pct: 0,
    wage_ceiling: undefined,
  },
  LWF: {
    employer_contribution_pct: 0,
    employee_contribution_pct: 0,
    wage_ceiling: undefined,
  },
  GRATUITY: {
    employer_contribution_pct: 4.81,
    employee_contribution_pct: 0,
    wage_ceiling: undefined,
  },
};

export default function StatutorySetupForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const organizationId = useRequiredActiveOrganizationId();

  const presetType = searchParams.get('type');

  const [formData, setFormData] = useState({
    organization_id: organizationId,
    statutory_type: presetType || 'PF',
    employer_contribution_pct: '',
    employee_contribution_pct: '',
    wage_ceiling: '',
    admin_charges_pct: '',
    is_applicable: true,
    effective_from: new Date().toISOString().split('T')[0],
  });

  useEffect(() => {
    if (isEdit && id) {
      loadSetup(id);
    } else if (presetType) {
      applyDefaults(presetType);
    }
  }, [id, presetType]);

  const loadSetup = async (setupId: string) => {
    try {
      setLoading(true);
      const data = await payrollService.getStatutorySetup(setupId);
      setFormData({
        organization_id: data.organization_id,
        statutory_type: data.statutory_type,
        employer_contribution_pct: data.employer_contribution_pct?.toString() || '',
        employee_contribution_pct: data.employee_contribution_pct?.toString() || '',
        wage_ceiling: data.wage_ceiling?.toString() || '',
        admin_charges_pct: data.admin_charges_pct?.toString() || '',
        is_applicable: data.is_applicable,
        effective_from: data.effective_from,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load setup',
        variant: 'destructive',
      });
      navigate('/payroll/statutory');
    } finally {
      setLoading(false);
    }
  };

  const applyDefaults = (type: string) => {
    const defaults = DEFAULT_VALUES[type];
    if (defaults) {
      setFormData((prev) => ({
        ...prev,
        statutory_type: type,
        employer_contribution_pct: defaults.employer_contribution_pct?.toString() || '',
        employee_contribution_pct: defaults.employee_contribution_pct?.toString() || '',
        wage_ceiling: defaults.wage_ceiling?.toString() || '',
        admin_charges_pct: defaults.admin_charges_pct?.toString() || '',
      }));
    }
  };

  const handleTypeChange = (value: string) => {
    setFormData((prev) => ({ ...prev, statutory_type: value }));
    if (!isEdit) {
      applyDefaults(value);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.statutory_type || !formData.effective_from) {
      toast({
        title: 'Validation Error',
        description: 'Type and effective date are required',
        variant: 'destructive',
      });
      return;
    }

    try {
      setSaving(true);

      const payload: Partial<StatutorySetup> = {
        organization_id: formData.organization_id,
        statutory_type: formData.statutory_type as any,
        employer_contribution_pct: formData.employer_contribution_pct
          ? parseFloat(formData.employer_contribution_pct)
          : undefined,
        employee_contribution_pct: formData.employee_contribution_pct
          ? parseFloat(formData.employee_contribution_pct)
          : undefined,
        wage_ceiling: formData.wage_ceiling
          ? parseFloat(formData.wage_ceiling)
          : undefined,
        admin_charges_pct: formData.admin_charges_pct
          ? parseFloat(formData.admin_charges_pct)
          : undefined,
        is_applicable: formData.is_applicable,
        effective_from: formData.effective_from,
      };

      if (isEdit && id) {
        await payrollService.updateStatutorySetup(id, payload);
        toast({
          title: 'Success',
          description: 'Setup updated successfully',
        });
      } else {
        await payrollService.createStatutorySetup(payload);
        toast({
          title: 'Success',
          description: 'Setup created successfully',
        });
      }

      navigate('/payroll/statutory');
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to save setup',
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
    <div className="container mx-auto py-6 space-y-6 max-w-2xl">
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/payroll/statutory')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <div>
          <h1 className="text-2xl font-bold">
            {isEdit ? 'Edit' : 'Configure'} Statutory Setup
          </h1>
          <p className="text-muted-foreground">
            {isEdit ? 'Update configuration' : 'Set up statutory compliance'}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <CardTitle>Configuration Details</CardTitle>
            <CardDescription>
              Configure rates and thresholds for statutory compliance
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="statutory_type">Statutory Type *</Label>
              <Select
                value={formData.statutory_type}
                onValueChange={handleTypeChange}
                disabled={isEdit}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  {STATUTORY_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="employer_contribution_pct">
                  Employer Contribution (%)
                </Label>
                <Input
                  id="employer_contribution_pct"
                  type="number"
                  step="0.01"
                  value={formData.employer_contribution_pct}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      employer_contribution_pct: e.target.value,
                    })
                  }
                  placeholder="e.g., 12"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="employee_contribution_pct">
                  Employee Contribution (%)
                </Label>
                <Input
                  id="employee_contribution_pct"
                  type="number"
                  step="0.01"
                  value={formData.employee_contribution_pct}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      employee_contribution_pct: e.target.value,
                    })
                  }
                  placeholder="e.g., 12"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="wage_ceiling">Wage Ceiling (₹)</Label>
                <Input
                  id="wage_ceiling"
                  type="number"
                  value={formData.wage_ceiling}
                  onChange={(e) =>
                    setFormData({ ...formData, wage_ceiling: e.target.value })
                  }
                  placeholder="e.g., 15000"
                />
                <p className="text-xs text-muted-foreground">
                  Maximum wage for contribution calculation
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="admin_charges_pct">Admin Charges (%)</Label>
                <Input
                  id="admin_charges_pct"
                  type="number"
                  step="0.01"
                  value={formData.admin_charges_pct}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      admin_charges_pct: e.target.value,
                    })
                  }
                  placeholder="e.g., 0.5"
                />
                <p className="text-xs text-muted-foreground">
                  Additional administrative charges (if any)
                </p>
              </div>
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
              />
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_applicable"
                checked={formData.is_applicable}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, is_applicable: checked as boolean })
                }
              />
              <Label htmlFor="is_applicable">Applicable for payroll processing</Label>
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-4 mt-6">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/payroll/statutory')}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={saving}>
            <Save className="mr-2 h-4 w-4" />
            {saving ? 'Saving...' : isEdit ? 'Update Setup' : 'Save Setup'}
          </Button>
        </div>
      </form>
    </div>
  );
}
