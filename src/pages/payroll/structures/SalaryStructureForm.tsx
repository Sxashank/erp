/**
 * Salary Structure Form Page
 */

import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Save, Plus, Trash2 } from 'lucide-react';

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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useToast } from '@/hooks/use-toast';
import payrollService, {
  SalaryStructure,
  SalaryComponent,
  SalaryStructureComponent,
} from '@/services/payrollService';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';

interface ComponentLine {
  id?: string;
  component_id: string;
  component?: SalaryComponent;
  calculation_type: 'FIXED' | 'PERCENTAGE' | 'FORMULA';
  default_value: string;
  percentage_of: string;
  percentage_value: string;
  formula: string;
  is_mandatory: boolean;
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
    organization_id: organizationId,
    structure_code: '',
    structure_name: '',
    description: '',
    ctc_from: '',
    ctc_to: '',
    is_active: true,
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
        organization_id: organizationId,
        active_only: true,
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
        organization_id: data.organization_id,
        structure_code: data.structure_code,
        structure_name: data.structure_name,
        description: data.description || '',
        ctc_from: data.ctc_from?.toString() || '',
        ctc_to: data.ctc_to?.toString() || '',
        is_active: data.is_active,
      });

      if (data.components) {
        setComponentLines(
          data.components.map((c) => ({
            id: c.id,
            component_id: c.component_id,
            component: c.component,
            calculation_type: c.calculation_type,
            default_value: c.default_value?.toString() || '',
            percentage_of: c.percentage_of || '',
            percentage_value: c.percentage_value?.toString() || '',
            formula: c.formula || '',
            is_mandatory: c.is_mandatory,
          }))
        );
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load structure',
        variant: 'destructive',
      });
      navigate('/payroll/structures');
    } finally {
      setLoading(false);
    }
  };

  const addComponentLine = () => {
    setComponentLines([
      ...componentLines,
      {
        component_id: '',
        calculation_type: 'FIXED',
        default_value: '',
        percentage_of: '',
        percentage_value: '',
        formula: '',
        is_mandatory: false,
      },
    ]);
  };

  const removeComponentLine = (index: number) => {
    setComponentLines(componentLines.filter((_, i) => i !== index));
  };

  const updateComponentLine = (index: number, field: string, value: any) => {
    const updated = [...componentLines];
    updated[index] = { ...updated[index], [field]: value };

    // If component changed, update the component object too
    if (field === 'component_id') {
      updated[index].component = components.find((c) => c.id === value);
    }

    setComponentLines(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.structure_code || !formData.structure_name) {
      toast({
        title: 'Validation Error',
        description: 'Code and name are required',
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
    const invalidLines = componentLines.filter((line) => !line.component_id);
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
        ctc_from: formData.ctc_from ? parseFloat(formData.ctc_from) : undefined,
        ctc_to: formData.ctc_to ? parseFloat(formData.ctc_to) : undefined,
        components: componentLines.map((line) => ({
          component_id: line.component_id,
          calculation_type: line.calculation_type,
          default_value: line.default_value
            ? parseFloat(line.default_value)
            : undefined,
          percentage_of: line.percentage_of || undefined,
          percentage_value: line.percentage_value
            ? parseFloat(line.percentage_value)
            : undefined,
          formula: line.formula || undefined,
          is_mandatory: line.is_mandatory,
        })),
      };

      if (isEdit && id) {
        await payrollService.updateStructure(id, payload as any);
        toast({
          title: 'Success',
          description: 'Structure updated successfully',
        });
      } else {
        await payrollService.createStructure(payload as any);
        toast({
          title: 'Success',
          description: 'Structure created successfully',
        });
      }

      navigate('/payroll/structures');
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to save structure',
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
        <Button variant="ghost" onClick={() => navigate('/payroll/structures')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <div>
          <h1 className="text-2xl font-bold">
            {isEdit ? 'Edit' : 'New'} Salary Structure
          </h1>
          <p className="text-muted-foreground">
            {isEdit ? 'Update structure details' : 'Create a new salary structure'}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="structure_code">Structure Code *</Label>
                  <Input
                    id="structure_code"
                    value={formData.structure_code}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        structure_code: e.target.value.toUpperCase(),
                      })
                    }
                    placeholder="e.g., STD-01, MGR-01"
                    disabled={isEdit}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="structure_name">Structure Name *</Label>
                  <Input
                    id="structure_name"
                    value={formData.structure_name}
                    onChange={(e) =>
                      setFormData({ ...formData, structure_name: e.target.value })
                    }
                    placeholder="e.g., Standard Structure, Manager Structure"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  placeholder="Optional description for this structure"
                  rows={2}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="ctc_from">CTC Range From</Label>
                  <Input
                    id="ctc_from"
                    type="number"
                    value={formData.ctc_from}
                    onChange={(e) =>
                      setFormData({ ...formData, ctc_from: e.target.value })
                    }
                    placeholder="Minimum CTC"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ctc_to">CTC Range To</Label>
                  <Input
                    id="ctc_to"
                    type="number"
                    value={formData.ctc_to}
                    onChange={(e) =>
                      setFormData({ ...formData, ctc_to: e.target.value })
                    }
                    placeholder="Maximum CTC"
                  />
                </div>
              </div>

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

          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
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
                      <TableCell colSpan={6} className="text-center py-8">
                        No components added. Click "Add Component" to start.
                      </TableCell>
                    </TableRow>
                  ) : (
                    componentLines.map((line, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Select
                            value={line.component_id}
                            onValueChange={(value) =>
                              updateComponentLine(index, 'component_id', value)
                            }
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select component" />
                            </SelectTrigger>
                            <SelectContent>
                              {components.map((comp) => (
                                <SelectItem key={comp.id} value={comp.id}>
                                  {comp.component_name} ({comp.component_type})
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </TableCell>
                        <TableCell>
                          <Select
                            value={line.calculation_type}
                            onValueChange={(value) =>
                              updateComponentLine(index, 'calculation_type', value)
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
                          {line.calculation_type === 'FIXED' && (
                            <Input
                              type="number"
                              value={line.default_value}
                              onChange={(e) =>
                                updateComponentLine(
                                  index,
                                  'default_value',
                                  e.target.value
                                )
                              }
                              placeholder="Amount"
                              className="w-[120px]"
                            />
                          )}
                          {line.calculation_type === 'PERCENTAGE' && (
                            <Input
                              type="number"
                              step="0.01"
                              value={line.percentage_value}
                              onChange={(e) =>
                                updateComponentLine(
                                  index,
                                  'percentage_value',
                                  e.target.value
                                )
                              }
                              placeholder="%"
                              className="w-[100px]"
                            />
                          )}
                          {line.calculation_type === 'FORMULA' && (
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
                          {line.calculation_type === 'PERCENTAGE' && (
                            <Input
                              value={line.percentage_of}
                              onChange={(e) =>
                                updateComponentLine(
                                  index,
                                  'percentage_of',
                                  e.target.value
                                )
                              }
                              placeholder="BASIC"
                              className="w-[100px]"
                            />
                          )}
                        </TableCell>
                        <TableCell>
                          <Checkbox
                            checked={line.is_mandatory}
                            onCheckedChange={(checked) =>
                              updateComponentLine(index, 'is_mandatory', checked)
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

        <div className="flex justify-end gap-4 mt-6">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/payroll/structures')}
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
