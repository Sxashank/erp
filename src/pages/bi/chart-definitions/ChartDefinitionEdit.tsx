/**
 * Chart Definition Edit Page
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { ArrowLeft, Loader2, Save, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
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
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetFooter,
} from '@/components/ui/sheet';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { biChartApi, biDataSourceApi } from '@/services/biApi';
import { rolesApi } from '@/services/api';
import {
  ChartDefinition,
  BIModule,
  ChartType,
  DataSourceListItem,
} from '@/types/bi';

interface FormData {
  code: string;
  name: string;
  description: string;
  module: BIModule;
  chart_type: ChartType;
  default_data_source_id?: string;
  config: string;
  data_mapping: string;
}

interface Role {
  id: string;
  name: string;
  code: string;
}

const MODULES: { value: BIModule; label: string }[] = [
  { value: 'FINANCE', label: 'Finance' },
  { value: 'LENDING', label: 'Lending' },
  { value: 'HR', label: 'Human Resources' },
  { value: 'TREASURY', label: 'Treasury' },
  { value: 'PROCUREMENT', label: 'Procurement' },
  { value: 'INVENTORY', label: 'Inventory' },
  { value: 'TAX', label: 'Tax' },
  { value: 'COLLECTIONS', label: 'Collections' },
  { value: 'LEGAL', label: 'Legal' },
  { value: 'PORTAL', label: 'Customer Portal' },
];

const CHART_TYPES: { value: ChartType; label: string }[] = [
  { value: 'KPI', label: 'KPI Card' },
  { value: 'LINE', label: 'Line Chart' },
  { value: 'BAR', label: 'Bar Chart' },
  { value: 'PIE', label: 'Pie Chart' },
  { value: 'DONUT', label: 'Donut Chart' },
  { value: 'AREA', label: 'Area Chart' },
  { value: 'GAUGE', label: 'Gauge' },
  { value: 'TABLE', label: 'Data Table' },
];

export function ChartDefinitionEdit() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [chart, setChart] = useState<ChartDefinition | null>(null);
  const [dataSources, setDataSources] = useState<DataSourceListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // Role access drawer state
  const [roleDrawerOpen, setRoleDrawerOpen] = useState(false);
  const [roles, setRoles] = useState<Role[]>([]);
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);
  const [savingRoles, setSavingRoles] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: {
      code: '',
      name: '',
      description: '',
      module: 'FINANCE',
      chart_type: 'KPI',
      config: '{}',
      data_mapping: '{}',
    },
  });

  const fetchData = async () => {
    if (!id) return;

    try {
      setLoading(true);
      const [chartRes, dataSourcesRes] = await Promise.all([
        biChartApi.get(id),
        biDataSourceApi.list(),
      ]);

      setChart(chartRes.data);
      setDataSources(dataSourcesRes.data);

      // Set form values
      const c = chartRes.data;
      setValue('code', c.code);
      setValue('name', c.name);
      setValue('description', c.description || '');
      setValue('module', c.module);
      setValue('chart_type', c.chart_type);
      setValue('default_data_source_id', c.default_data_source_id || '');
      setValue('config', JSON.stringify(c.config || {}, null, 2));
      setValue('data_mapping', JSON.stringify(c.data_mapping || {}, null, 2));

      // Set role access
      if (c.role_access) {
        setSelectedRoleIds(c.role_access.map((ra) => ra.role_id));
      }

      const rolesRes = await rolesApi.list();
      const roleList = Array.isArray(rolesRes.data) ? rolesRes.data : rolesRes.data.items ?? [];
      setRoles(
        roleList.map((r: { id: string; code: string; name: string }) => ({
          id: r.id,
          code: r.code,
          name: r.name,
        })),
      );
    } catch (error) {
      console.error('Error fetching data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load chart definition',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  const onSubmit = async (data: FormData) => {
    if (!id) return;

    try {
      setSubmitting(true);

      let config = {};
      let dataMapping = {};

      try {
        config = JSON.parse(data.config);
      } catch {
        toast({
          title: 'Error',
          description: 'Invalid JSON in config field',
          variant: 'destructive',
        });
        return;
      }

      try {
        dataMapping = JSON.parse(data.data_mapping);
      } catch {
        toast({
          title: 'Error',
          description: 'Invalid JSON in data mapping field',
          variant: 'destructive',
        });
        return;
      }

      await biChartApi.update(id, {
        code: data.code,
        name: data.name,
        description: data.description || undefined,
        module: data.module,
        chart_type: data.chart_type,
        default_data_source_id: data.default_data_source_id || undefined,
        config,
        data_mapping: dataMapping,
      });

      toast({
        title: 'Success',
        description: 'Chart definition updated successfully',
      });

      navigate('/admin/bi/chart-definitions');
    } catch (error: any) {
      console.error('Error updating chart:', error);
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update chart definition',
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleSaveRoles = async () => {
    if (!id) return;

    try {
      setSavingRoles(true);
      await biChartApi.setRoleAccess(id, { role_ids: selectedRoleIds });
      toast({
        title: 'Success',
        description: 'Role access updated successfully',
      });
      setRoleDrawerOpen(false);
    } catch (error) {
      console.error('Error saving role access:', error);
      toast({
        title: 'Error',
        description: 'Failed to update role access',
        variant: 'destructive',
      });
    } finally {
      setSavingRoles(false);
    }
  };

  const toggleRole = (roleId: string) => {
    setSelectedRoleIds((prev) =>
      prev.includes(roleId) ? prev.filter((id) => id !== roleId) : [...prev, roleId]
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!chart) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Chart definition not found</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => navigate('/admin/bi/chart-definitions')}
        >
          Back to Charts
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate('/admin/bi/chart-definitions')}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Edit Chart Definition</h1>
            <p className="text-muted-foreground">{chart.code}</p>
          </div>
        </div>
        <Button variant="outline" onClick={() => setRoleDrawerOpen(true)}>
          <Users className="h-4 w-4 mr-2" />
          Role Access ({selectedRoleIds.length})
        </Button>
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="grid grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="code">Code *</Label>
                  <Input
                    id="code"
                    {...register('code', {
                      required: 'Code is required',
                      pattern: {
                        value: /^[A-Z0-9_]+$/,
                        message: 'Code must be uppercase letters, numbers, and underscores',
                      },
                    })}
                  />
                  {errors.code && (
                    <p className="text-sm text-red-500">{errors.code.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="name">Name *</Label>
                  <Input
                    id="name"
                    {...register('name', { required: 'Name is required' })}
                  />
                  {errors.name && (
                    <p className="text-sm text-red-500">{errors.name.message}</p>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  rows={2}
                  {...register('description')}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Module *</Label>
                  <Select
                    value={watch('module')}
                    onValueChange={(value) => setValue('module', value as BIModule)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {MODULES.map((m) => (
                        <SelectItem key={m.value} value={m.value}>
                          {m.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Chart Type *</Label>
                  <Select
                    value={watch('chart_type')}
                    onValueChange={(value) => setValue('chart_type', value as ChartType)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {CHART_TYPES.map((t) => (
                        <SelectItem key={t.value} value={t.value}>
                          {t.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Default Data Source</Label>
                <Select
                  value={watch('default_data_source_id') || ''}
                  onValueChange={(value) => setValue('default_data_source_id', value || undefined)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a data source" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">None</SelectItem>
                    {dataSources.map((ds) => (
                      <SelectItem key={ds.id} value={ds.id}>
                        {ds.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Chart Configuration</CardTitle>
              <CardDescription>
                JSON configuration for the chart
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Config (JSON)</Label>
                <Textarea
                  rows={10}
                  className="font-mono text-sm"
                  {...register('config')}
                />
              </div>

              <div className="space-y-2">
                <Label>Data Mapping (JSON)</Label>
                <Textarea
                  rows={6}
                  className="font-mono text-sm"
                  {...register('data_mapping')}
                />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="flex justify-end gap-4 mt-6">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/admin/bi/chart-definitions')}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            <Save className="h-4 w-4 mr-2" />
            Save Changes
          </Button>
        </div>
      </form>

      {/* Role Access Drawer */}
      <Sheet open={roleDrawerOpen} onOpenChange={setRoleDrawerOpen}>
        <SheetContent>
          <SheetHeader>
            <SheetTitle>Role Access</SheetTitle>
            <SheetDescription>
              Select which roles can use this chart in their dashboards
            </SheetDescription>
          </SheetHeader>

          <div className="py-6 space-y-4">
            {roles.map((role) => (
              <div
                key={role.id}
                className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-muted/50 cursor-pointer"
                onClick={() => toggleRole(role.id)}
              >
                <Checkbox
                  checked={selectedRoleIds.includes(role.id)}
                  onCheckedChange={() => toggleRole(role.id)}
                />
                <div className="flex-1">
                  <p className="font-medium">{role.name}</p>
                  <p className="text-sm text-muted-foreground">{role.code}</p>
                </div>
              </div>
            ))}
          </div>

          <SheetFooter>
            <Button variant="outline" onClick={() => setRoleDrawerOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveRoles} disabled={savingRoles}>
              {savingRoles && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              <Save className="h-4 w-4 mr-2" />
              Save Access
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>
    </div>
  );
}
