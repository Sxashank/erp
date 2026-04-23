/**
 * Chart Definition Create Page
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { ArrowLeft, Loader2, Save } from 'lucide-react';
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
import { useToast } from '@/hooks/use-toast';
import { biChartApi, biDataSourceApi } from '@/services/biApi';
import { ChartDefinitionCreate as ChartDefinitionCreateType, BIModule, ChartType, DataSourceListItem } from '@/types/bi';

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

const CHART_TYPES: { value: ChartType; label: string; description: string }[] = [
  { value: 'KPI', label: 'KPI Card', description: 'Single value metric display' },
  { value: 'LINE', label: 'Line Chart', description: 'Trend over time' },
  { value: 'BAR', label: 'Bar Chart', description: 'Compare categories' },
  { value: 'PIE', label: 'Pie Chart', description: 'Part of whole' },
  { value: 'DONUT', label: 'Donut Chart', description: 'Pie with center' },
  { value: 'AREA', label: 'Area Chart', description: 'Filled line chart' },
  { value: 'GAUGE', label: 'Gauge', description: 'Progress indicator' },
  { value: 'TABLE', label: 'Data Table', description: 'Tabular data' },
];

export function ChartDefinitionCreate() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [dataSources, setDataSources] = useState<DataSourceListItem[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  const organizationId = localStorage.getItem('organization_id') || '';

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

  useEffect(() => {
    const fetchDataSources = async () => {
      try {
        setLoading(true);
        const response = await biDataSourceApi.list();
        setDataSources(response.data);
      } catch (error) {
        console.error('Error fetching data sources:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchDataSources();
  }, []);

  const onSubmit = async (data: FormData) => {
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

      const payload: ChartDefinitionCreateType = {
        code: data.code,
        name: data.name,
        description: data.description || undefined,
        organization_id: organizationId || undefined,
        module: data.module,
        chart_type: data.chart_type,
        default_data_source_id: data.default_data_source_id || undefined,
        config,
        data_mapping: dataMapping,
        is_system: false,
      };

      await biChartApi.create(payload);

      toast({
        title: 'Success',
        description: 'Chart definition created successfully',
      });

      navigate('/admin/bi/chart-definitions');
    } catch (error: any) {
      console.error('Error creating chart:', error);
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to create chart definition',
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const chartType = watch('chart_type');

  const getConfigTemplate = (type: ChartType): string => {
    const templates: Record<ChartType, object> = {
      KPI: {
        valueField: 'value',
        subtitleField: 'subtitle',
        changeField: 'change',
        valueFormat: 'number',
        icon: 'DollarSign',
      },
      LINE: {
        xAxisField: 'date',
        series: ['value'],
        showLegend: true,
        showGrid: true,
      },
      BAR: {
        xAxisField: 'category',
        series: ['value'],
        showLegend: true,
        stacked: false,
      },
      PIE: {
        valueField: 'value',
        labelField: 'name',
        showLegend: true,
      },
      DONUT: {
        valueField: 'value',
        labelField: 'name',
        showLegend: true,
        innerRadius: 60,
        outerRadius: 80,
      },
      AREA: {
        xAxisField: 'date',
        series: ['value'],
        showLegend: true,
        stacked: false,
      },
      GAUGE: {
        valueField: 'value',
        minValue: 0,
        maxValue: 100,
        thresholds: [
          { value: 30, color: '#ef4444' },
          { value: 70, color: '#eab308' },
          { value: 100, color: '#22c55e' },
        ],
      },
      TABLE: {
        columns: [
          { key: 'name', label: 'Name' },
          { key: 'value', label: 'Value', format: 'number' },
        ],
        pageSize: 10,
        sortable: true,
      },
    };
    return JSON.stringify(templates[type], null, 2);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate('/admin/bi/chart-definitions')}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Create Chart Definition</h1>
          <p className="text-muted-foreground">
            Define a reusable chart that can be added to dashboards
          </p>
        </div>
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
                    placeholder="FIN_REV_MTD"
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
                    placeholder="Revenue MTD"
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
                  placeholder="Month-to-date revenue from all sources"
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
                    value={chartType}
                    onValueChange={(value) => {
                      setValue('chart_type', value as ChartType);
                      setValue('config', getConfigTemplate(value as ChartType));
                    }}
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
                <p className="text-sm text-muted-foreground">
                  The default data source for this chart
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Chart Configuration</CardTitle>
              <CardDescription>
                JSON configuration for the {CHART_TYPES.find((t) => t.value === chartType)?.label}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Config (JSON)</Label>
                <Textarea
                  rows={10}
                  className="font-mono text-sm"
                  placeholder="{}"
                  {...register('config')}
                />
                <p className="text-sm text-muted-foreground">
                  Chart-specific configuration options
                </p>
              </div>

              <div className="space-y-2">
                <Label>Data Mapping (JSON)</Label>
                <Textarea
                  rows={6}
                  className="font-mono text-sm"
                  placeholder="{}"
                  {...register('data_mapping')}
                />
                <p className="text-sm text-muted-foreground">
                  Map data source fields to chart fields
                </p>
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
            Create Chart
          </Button>
        </div>
      </form>
    </div>
  );
}
