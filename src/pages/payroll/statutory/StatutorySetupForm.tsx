/**
 * Statutory Setup Form Page
 */

import { Save } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
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
import { useToast } from '@/hooks/use-toast';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import type { StatutorySetup } from '@/services/payrollService';
import payrollService from '@/services/payrollService';
import { getErrorMessage } from "@/lib/errorMessage";

const STATUTORY_TYPES = [
  { value: 'PF', label: 'Provident Fund (PF)' },
  { value: 'ESI', label: 'Employee State Insurance (ESI)' },
  { value: 'PT', label: 'Professional Tax (PT)' },
  { value: 'LWF', label: 'Labour Welfare Fund (LWF)' },
  { value: 'GRATUITY', label: 'Gratuity' },
];

const DEFAULT_VALUES: Record<string, Partial<StatutorySetup>> = {
  PF: {
    employerContributionPct: 12,
    employeeContributionPct: 12,
    wageCeiling: 15000,
    adminChargesPct: 0.5,
  },
  ESI: {
    employerContributionPct: 3.25,
    employeeContributionPct: 0.75,
    wageCeiling: 21000,
  },
  PT: {
    employerContributionPct: 0,
    employeeContributionPct: 0,
    wageCeiling: undefined,
  },
  LWF: {
    employerContributionPct: 0,
    employeeContributionPct: 0,
    wageCeiling: undefined,
  },
  GRATUITY: {
    employerContributionPct: 4.81,
    employeeContributionPct: 0,
    wageCeiling: undefined,
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
    statutoryType: presetType || 'PF',
    employerContributionPct: '',
    employeeContributionPct: '',
    wageCeiling: '',
    adminChargesPct: '',
    isApplicable: true,
    effectiveFrom: new Date().toISOString().split('T')[0],
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
        statutoryType: data.statutoryType,
        employerContributionPct: data.employerContributionPct?.toString() || '',
        employeeContributionPct: data.employeeContributionPct?.toString() || '',
        wageCeiling: data.wageCeiling?.toString() || '',
        adminChargesPct: data.adminChargesPct?.toString() || '',
        isApplicable: data.isApplicable,
        effectiveFrom: data.effectiveFrom,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load setup',
        variant: 'destructive',
      });
      navigate('/admin/payroll/statutory');
    } finally {
      setLoading(false);
    }
  };

  const applyDefaults = (type: string) => {
    const defaults = DEFAULT_VALUES[type];
    if (defaults) {
      setFormData((prev) => ({
        ...prev,
        statutoryType: type,
        employerContributionPct: defaults.employerContributionPct?.toString() || '',
        employeeContributionPct: defaults.employeeContributionPct?.toString() || '',
        wageCeiling: defaults.wageCeiling?.toString() || '',
        adminChargesPct: defaults.adminChargesPct?.toString() || '',
      }));
    }
  };

  const handleTypeChange = (value: string) => {
    setFormData((prev) => ({ ...prev, statutoryType: value }));
    if (!isEdit) {
      applyDefaults(value);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.statutoryType || !formData.effectiveFrom) {
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
        statutoryType: formData.statutoryType as StatutorySetup['statutoryType'],
        employerContributionPct: formData.employerContributionPct
          ? parseFloat(formData.employerContributionPct)
          : undefined,
        employeeContributionPct: formData.employeeContributionPct
          ? parseFloat(formData.employeeContributionPct)
          : undefined,
        wageCeiling: formData.wageCeiling ? parseFloat(formData.wageCeiling) : undefined,
        adminChargesPct: formData.adminChargesPct
          ? parseFloat(formData.adminChargesPct)
          : undefined,
        isApplicable: formData.isApplicable,
        effectiveFrom: formData.effectiveFrom,
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

      navigate('/admin/payroll/statutory');
    } catch (error: unknown) {
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to save setup'),
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
    <div className="container mx-auto max-w-2xl space-y-6 py-6">
      <PageHeader
        title={`${isEdit ? 'Edit' : 'Configure'} Statutory Setup`}
        subtitle={isEdit ? 'Update configuration' : 'Set up statutory compliance'}
        breadcrumbs={[
          { label: 'Statutory Setup', to: '/admin/payroll/statutory' },
          { label: isEdit ? 'Edit' : 'Configure' },
        ]}
      />

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
              <Label htmlFor="statutoryType">Statutory Type *</Label>
              <Select
                value={formData.statutoryType}
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
                <Label htmlFor="employerContributionPct">Employer Contribution (%)</Label>
                <Input
                  id="employerContributionPct"
                  type="number"
                  step="0.01"
                  value={formData.employerContributionPct}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      employerContributionPct: e.target.value,
                    })
                  }
                  placeholder="e.g., 12"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="employeeContributionPct">Employee Contribution (%)</Label>
                <Input
                  id="employeeContributionPct"
                  type="number"
                  step="0.01"
                  value={formData.employeeContributionPct}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      employeeContributionPct: e.target.value,
                    })
                  }
                  placeholder="e.g., 12"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="wageCeiling">Wage Ceiling (₹)</Label>
                <Input
                  id="wageCeiling"
                  type="number"
                  value={formData.wageCeiling}
                  onChange={(e) => setFormData({ ...formData, wageCeiling: e.target.value })}
                  placeholder="e.g., 15000"
                />
                <p className="text-xs text-muted-foreground">
                  Maximum wage for contribution calculation
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="adminChargesPct">Admin Charges (%)</Label>
                <Input
                  id="adminChargesPct"
                  type="number"
                  step="0.01"
                  value={formData.adminChargesPct}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      adminChargesPct: e.target.value,
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
              <Label htmlFor="effectiveFrom">Effective From *</Label>
              <Input
                id="effectiveFrom"
                type="date"
                value={formData.effectiveFrom}
                onChange={(e) => setFormData({ ...formData, effectiveFrom: e.target.value })}
              />
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="isApplicable"
                checked={formData.isApplicable}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, isApplicable: checked as boolean })
                }
              />
              <Label htmlFor="isApplicable">Applicable for payroll processing</Label>
            </div>
          </CardContent>
        </Card>

        <div className="mt-6 flex justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/admin/payroll/statutory')}
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
