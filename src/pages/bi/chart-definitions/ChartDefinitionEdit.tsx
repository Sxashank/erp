/**
 * Chart Definition Edit Page
 */

import { Loader2, Save, Users } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useParams, useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
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
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetFooter,
} from '@/components/ui/sheet';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { rolesApi } from '@/services/api';
import { biChartApi, biDataSourceApi } from '@/services/biApi';
import type { ChartDefinition, BIModule, ChartType, DataSourceListItem } from '@/types/bi';

import { logger } from "@/lib/logger";
import { getErrorMessage } from "@/lib/errorMessage";
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
      const roleList = Array.isArray(rolesRes.data) ? rolesRes.data : (rolesRes.data.items ?? []);
      setRoles(
        roleList.map((r: { id: string; code: string; name: string }) => ({
          id: r.id,
          code: r.code,
          name: r.name,
        })),
      );
    } catch (error) {
      logger.error('Error fetching data:', error);
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
    } catch (error: unknown) {
      logger.error('Error updating chart:', error);
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to update chart definition'),
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
      logger.error('Error saving role access:', error);
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
      prev.includes(roleId) ? prev.filter((id) => id !== roleId) : [...prev, roleId],
    );
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!chart) {
    return (
      <div className="py-12 text-center">
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
      <PageHeader
        title="Edit Chart Definition"
        subtitle={chart.code}
        breadcrumbs={[
          { label: 'Chart Definitions', to: '/admin/bi/chart-definitions' },
          { label: chart.code },
        ]}
        actions={
          <Button variant="outline" onClick={() => setRoleDrawerOpen(true)}>
            <Users className="mr-2 h-4 w-4" />
            Role Access ({selectedRoleIds.length})
          </Button>
        }
      />

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
                  {errors.code && <p className="text-sm text-red-500">{errors.code.message}</p>}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="name">Name *</Label>
                  <Input id="name" {...register('name', { required: 'Name is required' })} />
                  {errors.name && <p className="text-sm text-red-500">{errors.name.message}</p>}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea id="description" rows={2} {...register('description')} />
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
              <CardDescription>JSON configuration for the chart</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Config (JSON)</Label>
                <Textarea rows={10} className="font-mono text-sm" {...register('config')} />
              </div>

              <div className="space-y-2">
                <Label>Data Mapping (JSON)</Label>
                <Textarea rows={6} className="font-mono text-sm" {...register('data_mapping')} />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="mt-6 flex justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/admin/bi/chart-definitions')}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Save className="mr-2 h-4 w-4" />
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

          <div className="space-y-4 py-6">
            {roles.map((role) => (
              <div
                key={role.id}
                className="flex cursor-pointer items-center space-x-3 rounded-lg border p-3 hover:bg-muted/50"
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
              {savingRoles && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              <Save className="mr-2 h-4 w-4" />
              Save Access
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>
    </div>
  );
}
