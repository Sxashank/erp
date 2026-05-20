/**
 * Salary Structure Form Page
 */

import { Save, Plus, Trash2 } from 'lucide-react';
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import type { SalaryComponent } from '@/services/payrollService';
import payrollService, {
  SalaryStructure,
  SalaryStructureComponent,
} from '@/services/payrollService';
import { getErrorMessage } from "@/lib/errorMessage";

interface ComponentLine {
  id?: string;
  componentId: string;
  component?: SalaryComponent;
  calculationType: 'FIXED' | 'PERCENTAGE' | 'FORMULA';
  defaultValue: string;
  percentageOf: string;
  percentageValue: string;
  formula: string;
  isMandatory: boolean;
}

export default function SalaryStructureForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { toast } = useToast();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [components, setComponents] = useState<SalaryComponent[]>([]);

  const organizationId = useRequiredActiveOrganizationId();

  const [formData, setFormData] = useState({
    structureCode: '',
    structureName: '',
    description: '',
    effectiveFrom: new Date().toISOString().split('T')[0],
    effectiveTo: '',
    paymentMode: 'BANK',
    payFrequency: 'MONTHLY',
    ctcFrom: '',
    ctcTo: '',
    isActive: true,
  });

  const [componentLines, setComponentLines] = useState<ComponentLine[]>([]);

  useEffect(() => {
    loadComponents();
    if (isEdit && id) {
      loadStructure(id);
    }
  }, [id]);

  const loadComponents = async () => {
    try {
      const response = await payrollService.listComponents({
        activeOnly: true,
        limit: 500,
      });
      setComponents(response.items);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load components',
        variant: 'destructive',
      });
    }
  };

  const loadStructure = async (structureId: string) => {
    try {
      setLoading(true);
      const data = await payrollService.getStructure(structureId);
      setFormData({
        structureCode: data.structureCode,
        structureName: data.structureName,
        description: data.description || '',
        effectiveFrom: data.effectiveFrom,
        effectiveTo: data.effectiveTo || '',
        paymentMode: data.paymentMode || 'BANK',
        payFrequency: data.payFrequency || 'MONTHLY',
        ctcFrom: data.ctcFrom?.toString() || '',
        ctcTo: data.ctcTo?.toString() || '',
        isActive: data.isActive,
      });

      if (data.components) {
        setComponentLines(
          data.components.map((c) => ({
            id: c.id,
            componentId: c.componentId,
            component: c.component,
            calculationType: c.calculationType === 'FIXED' || c.calculationType === 'FORMULA'
              ? c.calculationType
              : 'PERCENTAGE',
            defaultValue: c.defaultValue?.toString() || '',
            percentageOf: c.percentageOf || '',
            percentageValue: c.percentageValue?.toString() || '',
            formula: c.formula || '',
            isMandatory: c.isMandatory,
          })),
        );
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load structure',
        variant: 'destructive',
      });
      navigate('/admin/payroll/structures');
    } finally {
      setLoading(false);
    }
  };

  const addComponentLine = () => {
    setComponentLines([
      ...componentLines,
      {
        componentId: '',
        calculationType: 'FIXED',
        defaultValue: '',
        percentageOf: '',
        percentageValue: '',
        formula: '',
        isMandatory: false,
      },
    ]);
  };

  const removeComponentLine = (index: number) => {
    setComponentLines(componentLines.filter((_, i) => i !== index));
  };

  const updateComponentLine = (index: number, field: string, value: unknown) => {
    const updated = [...componentLines];
    updated[index] = { ...updated[index], [field]: value };

    // If component changed, update the component object too
    if (field === 'componentId') {
      updated[index].component = components.find((c) => c.id === value);
    }

    setComponentLines(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.structureCode || !formData.structureName) {
      toast({
        title: 'Validation Error',
        description: 'Code and name are required',
        variant: 'destructive',
      });
      return;
    }

    if (!formData.effectiveFrom) {
      toast({
        title: 'Validation Error',
        description: 'Effective from date is required',
        variant: 'destructive',
      });
      return;
    }

    if (componentLines.length === 0) {
      toast({
        title: 'Validation Error',
        description: 'At least one component is required',
        variant: 'destructive',
      });
      return;
    }

    // Validate all component lines have a component selected
    const invalidLines = componentLines.filter((line) => !line.componentId);
    if (invalidLines.length > 0) {
      toast({
        title: 'Validation Error',
        description: 'All component lines must have a component selected',
        variant: 'destructive',
      });
      return;
    }

    try {
      setSaving(true);

      const payload = {
        ...formData,
        effectiveTo: formData.effectiveTo || undefined,
        ctcFrom: formData.ctcFrom ? parseFloat(formData.ctcFrom) : undefined,
        ctcTo: formData.ctcTo ? parseFloat(formData.ctcTo) : undefined,
        components: componentLines.map((line) => ({
          componentId: line.componentId,
          calculationType: line.calculationType,
          defaultValue: line.defaultValue ? parseFloat(line.defaultValue) : undefined,
          percentageOf: line.percentageOf || undefined,
          percentageValue: line.percentageValue ? parseFloat(line.percentageValue) : undefined,
          formula: line.formula || undefined,
          isMandatory: line.isMandatory,
        })),
      };

      if (isEdit && id) {
        await payrollService.updateStructure(id, payload as Parameters<typeof payrollService.updateStructure>[1]);
        toast({
          title: 'Success',
          description: 'Structure updated successfully',
        });
      } else {
        await payrollService.createStructure(payload as Parameters<typeof payrollService.createStructure>[0]);
        toast({
          title: 'Success',
          description: 'Structure created successfully',
        });
      }

      navigate('/admin/payroll/structures');
    } catch (error: unknown) {
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to save structure'),
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
        title={`${isEdit ? 'Edit' : 'New'} Salary Structure`}
        subtitle={isEdit ? 'Update structure details' : 'Create a new salary structure'}
        breadcrumbs={[
          { label: 'Salary Structures', to: '/admin/payroll/structures' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit}>
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="structureCode">Structure Code *</Label>
                  <Input
                    id="structureCode"
                    value={formData.structureCode}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        structureCode: e.target.value.toUpperCase(),
                      })
                    }
                    placeholder="e.g., STD-01, MGR-01"
                    disabled={isEdit}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="structureName">Structure Name *</Label>
                  <Input
                    id="structureName"
                    value={formData.structureName}
                    onChange={(e) => setFormData({ ...formData, structureName: e.target.value })}
                    placeholder="e.g., Standard Structure, Manager Structure"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Optional description for this structure"
                  rows={2}
                />
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="ctcFrom">CTC Range From</Label>
                  <Input
                    id="ctcFrom"
                    type="number"
                    value={formData.ctcFrom}
                    onChange={(e) => setFormData({ ...formData, ctcFrom: e.target.value })}
                    placeholder="Minimum CTC"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ctcTo">CTC Range To</Label>
                  <Input
                    id="ctcTo"
                    type="number"
                    value={formData.ctcTo}
                    onChange={(e) => setFormData({ ...formData, ctcTo: e.target.value })}
                    placeholder="Maximum CTC"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="effectiveFrom">Effective From *</Label>
                  <Input
                    id="effectiveFrom"
                    type="date"
                    value={formData.effectiveFrom}
                    onChange={(e) => setFormData({ ...formData, effectiveFrom: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="effectiveTo">Effective To</Label>
                  <Input
                    id="effectiveTo"
                    type="date"
                    value={formData.effectiveTo}
                    onChange={(e) => setFormData({ ...formData, effectiveTo: e.target.value })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="paymentMode">Payment Mode</Label>
                  <Select
                    value={formData.paymentMode}
                    onValueChange={(value) => setFormData({ ...formData, paymentMode: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="BANK">Bank</SelectItem>
                      <SelectItem value="CASH">Cash</SelectItem>
                      <SelectItem value="CHEQUE">Cheque</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="payFrequency">Pay Frequency</Label>
                  <Select
                    value={formData.payFrequency}
                    onValueChange={(value) => setFormData({ ...formData, payFrequency: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="MONTHLY">Monthly</SelectItem>
                      <SelectItem value="WEEKLY">Weekly</SelectItem>
                      <SelectItem value="BIWEEKLY">Biweekly</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

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

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Components</CardTitle>
                <Button type="button" variant="outline" onClick={addComponentLine}>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Component
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[250px]">Component</TableHead>
                    <TableHead>Calculation Type</TableHead>
                    <TableHead>Default Value / %</TableHead>
                    <TableHead>Percentage Of</TableHead>
                    <TableHead className="w-[80px]">Mandatory</TableHead>
                    <TableHead className="w-[60px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {componentLines.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="py-8 text-center">
                        No components added. Click "Add Component" to start.
                      </TableCell>
                    </TableRow>
                  ) : (
                    componentLines.map((line, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Select
                            value={line.componentId}
                            onValueChange={(value) =>
                              updateComponentLine(index, 'componentId', value)
                            }
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select component" />
                            </SelectTrigger>
                            <SelectContent>
                              {components.map((comp) => (
                                <SelectItem key={comp.id} value={comp.id}>
                                  {comp.componentName} ({comp.componentType})
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </TableCell>
                        <TableCell>
                          <Select
                            value={line.calculationType}
                            onValueChange={(value) =>
                              updateComponentLine(index, 'calculationType', value)
                            }
                          >
                            <SelectTrigger className="w-[130px]">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="FIXED">Fixed</SelectItem>
                              <SelectItem value="PERCENTAGE">Percentage</SelectItem>
                              <SelectItem value="FORMULA">Formula</SelectItem>
                            </SelectContent>
                          </Select>
                        </TableCell>
                        <TableCell>
                          {line.calculationType === 'FIXED' && (
                            <Input
                              type="number"
                              value={line.defaultValue}
                              onChange={(e) =>
                                updateComponentLine(index, 'defaultValue', e.target.value)
                              }
                              placeholder="Amount"
                              className="w-[120px]"
                            />
                          )}
                          {line.calculationType === 'PERCENTAGE' && (
                            <Input
                              type="number"
                              step="0.01"
                              value={line.percentageValue}
                              onChange={(e) =>
                                updateComponentLine(index, 'percentageValue', e.target.value)
                              }
                              placeholder="%"
                              className="w-[100px]"
                            />
                          )}
                          {line.calculationType === 'FORMULA' && (
                            <Input
                              value={line.formula}
                              onChange={(e) =>
                                updateComponentLine(index, 'formula', e.target.value)
                              }
                              placeholder="Formula"
                              className="w-[150px]"
                            />
                          )}
                        </TableCell>
                        <TableCell>
                          {line.calculationType === 'PERCENTAGE' && (
                            <Input
                              value={line.percentageOf}
                              onChange={(e) =>
                                updateComponentLine(index, 'percentageOf', e.target.value)
                              }
                              placeholder="BASIC"
                              className="w-[100px]"
                            />
                          )}
                        </TableCell>
                        <TableCell>
                          <Checkbox
                            checked={line.isMandatory}
                            onCheckedChange={(checked) =>
                              updateComponentLine(index, 'isMandatory', checked)
                            }
                          />
                        </TableCell>
                        <TableCell>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            onClick={() => removeComponentLine(index)}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>

        <div className="mt-6 flex justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/admin/payroll/structures')}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={saving}>
            <Save className="mr-2 h-4 w-4" />
            {saving ? 'Saving...' : isEdit ? 'Update Structure' : 'Create Structure'}
          </Button>
        </div>
      </form>
    </div>
  );
}
