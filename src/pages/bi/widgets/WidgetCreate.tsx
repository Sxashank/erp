/**
 * Widget Create Page - Add a new widget to a dashboard
 */

import { Loader2, Save, Eye } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useParams, useNavigate } from 'react-router-dom';

import { WidgetRenderer } from '@/components/bi';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { biWidgetApi, biChartApi, biDataSourceApi, biDashboardApi } from '@/services/biApi';
import { logger } from '@/lib/logger';
import type {
  Dashboard,
  ChartDefinitionListItem,
  DataSourceListItem,
  WidgetType,
  DashboardWidgetCreate,
} from '@/types/bi';
import { getErrorMessage } from '@/lib/errorMessage';

interface FormData {
  title: string;
  widget_type: WidgetType;
  chart_definition_id?: string;
  data_source_id?: string;
  grid_w: number;
  grid_h: number;
  config: WidgetConfig;
}

interface WidgetTableColumn {
  key: string;
  label: string;
}

interface WidgetConfig extends Record<string, unknown> {
  valueField?: string;
  subtitleField?: string;
  changeField?: string;
  valueFormat?: string;
  xAxisField?: string;
  series?: string[];
  showLegend?: boolean;
  showGrid?: boolean;
  stacked?: boolean;
  labelField?: string;
  columns?: WidgetTableColumn[];
  pageSize?: number;
  content?: string;
  minValue?: number;
  maxValue?: number;
}

const WIDGET_TYPES: { value: WidgetType; label: string; description: string }[] = [
  {
    value: 'KPI_CARD',
    label: 'KPI Card',
    description: 'Display a single metric with optional change indicator',
  },
  { value: 'LINE_CHART', label: 'Line Chart', description: 'Show trends over time' },
  { value: 'BAR_CHART', label: 'Bar Chart', description: 'Compare values across categories' },
  { value: 'PIE_CHART', label: 'Pie Chart', description: 'Show proportions of a whole' },
  { value: 'DONUT_CHART', label: 'Donut Chart', description: 'Pie chart with center hole' },
  { value: 'AREA_CHART', label: 'Area Chart', description: 'Line chart with filled area' },
  { value: 'DATA_TABLE', label: 'Data Table', description: 'Tabular data display' },
  { value: 'TEXT_MARKDOWN', label: 'Text/Markdown', description: 'Rich text or markdown content' },
  { value: 'GAUGE_PROGRESS', label: 'Gauge/Progress', description: 'Show progress toward a goal' },
];

export function WidgetCreate() {
  const { dashboardId } = useParams<{ dashboardId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [charts, setCharts] = useState<ChartDefinitionListItem[]>([]);
  const [dataSources, setDataSources] = useState<DataSourceListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [previewData, setPreviewData] = useState<Record<string, unknown>[]>([]);
  const [step, setStep] = useState<'type' | 'config'>('type');

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: {
      title: '',
      widget_type: 'KPI_CARD',
      grid_w: 4,
      grid_h: 3,
      config: {},
    },
  });

  const widgetType = watch('widget_type');
  const chartDefinitionId = watch('chart_definition_id');
  const dataSourceId = watch('data_source_id');
  const config = watch('config');
  const title = watch('title');

  const fetchData = async () => {
    if (!dashboardId) return;

    try {
      setLoading(true);
      const [dashboardRes, chartsRes, dataSourcesRes] = await Promise.all([
        biDashboardApi.get(dashboardId),
        biChartApi.list(),
        biDataSourceApi.list(),
      ]);

      setDashboard(dashboardRes.data);
      setCharts(chartsRes.data);
      setDataSources(dataSourcesRes.data);
    } catch (error) {
      logger.error('Error fetching data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [dashboardId]);

  // Fetch preview data when data source changes
  useEffect(() => {
    const fetchPreviewData = async () => {
      if (!dataSourceId) {
        setPreviewData([]);
        return;
      }

      try {
        const response = await biDataSourceApi.preview(dataSourceId);
        setPreviewData(Array.isArray(response.data.data) ? response.data.data : []);
      } catch (error) {
        logger.error('Error fetching preview:', error);
        setPreviewData([]);
      }
    };

    fetchPreviewData();
  }, [dataSourceId]);

  // When selecting a chart, auto-fill some fields
  useEffect(() => {
    if (chartDefinitionId) {
      const chart = charts.find((c) => c.id === chartDefinitionId);
      if (chart) {
        setValue('title', chart.name);
        // Map chart type to widget type
        const chartToWidgetMap: Record<string, WidgetType> = {
          LINE: 'LINE_CHART',
          BAR: 'BAR_CHART',
          PIE: 'PIE_CHART',
          DONUT: 'DONUT_CHART',
          AREA: 'AREA_CHART',
          GAUGE: 'GAUGE_PROGRESS',
          KPI: 'KPI_CARD',
          TABLE: 'DATA_TABLE',
        };
        const mappedType = chartToWidgetMap[chart.chart_type];
        if (mappedType) {
          setValue('widget_type', mappedType);
        }
      }
    }
  }, [chartDefinitionId, charts, setValue]);

  const onSubmit = async (data: FormData) => {
    if (!dashboardId) return;

    try {
      setSaving(true);

      // Calculate grid position (add to bottom)
      const existingWidgets = dashboard?.widgets || [];
      const maxY = existingWidgets.reduce((max, w) => Math.max(max, w.grid_y + w.grid_h), 0);

      const payload: DashboardWidgetCreate = {
        widget_key: `widget_${Date.now()}`,
        title: data.title,
        widget_type: data.widget_type,
        chart_definition_id: data.chart_definition_id || undefined,
        data_source_id: data.data_source_id || undefined,
        grid_x: 0,
        grid_y: maxY,
        grid_w: data.grid_w,
        grid_h: data.grid_h,
        config: data.config,
      };

      await biWidgetApi.create(dashboardId, payload);

      toast({
        title: 'Success',
        description: 'Widget added successfully',
      });

      navigate(`/admin/bi/dashboards/${dashboardId}/edit`);
    } catch (error: unknown) {
      logger.error('Error creating widget:', error);
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to create widget'),
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const updateConfig = (key: string, value: unknown) => {
    setValue('config', { ...config, [key]: value });
  };

  const renderConfigFields = () => {
    switch (widgetType) {
      case 'KPI_CARD':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Value Field</Label>
              <Input
                placeholder="value"
                value={config.valueField || ''}
                onChange={(e) => updateConfig('valueField', e.target.value)}
              />
              <p className="text-sm text-muted-foreground">
                The field in the data that contains the main value
              </p>
            </div>
            <div className="space-y-2">
              <Label>Subtitle Field</Label>
              <Input
                placeholder="subtitle"
                value={config.subtitleField || ''}
                onChange={(e) => updateConfig('subtitleField', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Change Field</Label>
              <Input
                placeholder="change"
                value={config.changeField || ''}
                onChange={(e) => updateConfig('changeField', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Value Format</Label>
              <Select
                value={config.valueFormat || 'number'}
                onValueChange={(value) => updateConfig('valueFormat', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="number">Number</SelectItem>
                  <SelectItem value="currency">Currency</SelectItem>
                  <SelectItem value="percentage">Percentage</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        );

      case 'LINE_CHART':
      case 'AREA_CHART':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>X-Axis Field</Label>
              <Input
                placeholder="date"
                value={config.xAxisField || ''}
                onChange={(e) => updateConfig('xAxisField', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Series (comma-separated)</Label>
              <Input
                placeholder="value1,value2"
                value={(config.series || []).join(',')}
                onChange={(e) =>
                  updateConfig(
                    'series',
                    e.target.value
                      .split(',')
                      .map((s) => s.trim())
                      .filter(Boolean),
                  )
                }
              />
              <p className="text-sm text-muted-foreground">
                The fields in the data to plot as lines
              </p>
            </div>
            <div className="flex items-center justify-between">
              <Label>Show Legend</Label>
              <Switch
                checked={config.showLegend ?? true}
                onCheckedChange={(checked) => updateConfig('showLegend', checked)}
              />
            </div>
            <div className="flex items-center justify-between">
              <Label>Show Grid</Label>
              <Switch
                checked={config.showGrid ?? true}
                onCheckedChange={(checked) => updateConfig('showGrid', checked)}
              />
            </div>
          </div>
        );

      case 'BAR_CHART':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>X-Axis Field</Label>
              <Input
                placeholder="category"
                value={config.xAxisField || ''}
                onChange={(e) => updateConfig('xAxisField', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Series (comma-separated)</Label>
              <Input
                placeholder="value1,value2"
                value={(config.series || []).join(',')}
                onChange={(e) =>
                  updateConfig(
                    'series',
                    e.target.value
                      .split(',')
                      .map((s) => s.trim())
                      .filter(Boolean),
                  )
                }
              />
            </div>
            <div className="flex items-center justify-between">
              <Label>Show Legend</Label>
              <Switch
                checked={config.showLegend ?? true}
                onCheckedChange={(checked) => updateConfig('showLegend', checked)}
              />
            </div>
            <div className="flex items-center justify-between">
              <Label>Stacked</Label>
              <Switch
                checked={config.stacked ?? false}
                onCheckedChange={(checked) => updateConfig('stacked', checked)}
              />
            </div>
          </div>
        );

      case 'PIE_CHART':
      case 'DONUT_CHART':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Value Field</Label>
              <Input
                placeholder="value"
                value={config.valueField || ''}
                onChange={(e) => updateConfig('valueField', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Label Field</Label>
              <Input
                placeholder="name"
                value={config.labelField || ''}
                onChange={(e) => updateConfig('labelField', e.target.value)}
              />
            </div>
            <div className="flex items-center justify-between">
              <Label>Show Legend</Label>
              <Switch
                checked={config.showLegend ?? true}
                onCheckedChange={(checked) => updateConfig('showLegend', checked)}
              />
            </div>
          </div>
        );

      case 'DATA_TABLE':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Columns (JSON array)</Label>
              <Textarea
                placeholder='[{"key": "name", "label": "Name"}, {"key": "value", "label": "Value"}]'
                rows={4}
                value={JSON.stringify(config.columns || [], null, 2)}
                onChange={(e) => {
                  try {
                    updateConfig('columns', JSON.parse(e.target.value));
                  } catch {}
                }}
              />
            </div>
            <div className="space-y-2">
              <Label>Page Size</Label>
              <Input
                type="number"
                min={5}
                max={100}
                value={config.pageSize || 10}
                onChange={(e) => updateConfig('pageSize', parseInt(e.target.value))}
              />
            </div>
          </div>
        );

      case 'TEXT_MARKDOWN':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Content (Markdown)</Label>
              <Textarea
                placeholder="# Heading\n\nSome **bold** text..."
                rows={10}
                value={config.content || ''}
                onChange={(e) => updateConfig('content', e.target.value)}
              />
            </div>
          </div>
        );

      case 'GAUGE_PROGRESS':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Value Field</Label>
              <Input
                placeholder="value"
                value={config.valueField || ''}
                onChange={(e) => updateConfig('valueField', e.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Min Value</Label>
                <Input
                  type="number"
                  value={config.minValue ?? 0}
                  onChange={(e) => updateConfig('minValue', parseFloat(e.target.value))}
                />
              </div>
              <div className="space-y-2">
                <Label>Max Value</Label>
                <Input
                  type="number"
                  value={config.maxValue ?? 100}
                  onChange={(e) => updateConfig('maxValue', parseFloat(e.target.value))}
                />
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Add Widget"
        subtitle={`Add a new widget to "${dashboard?.name}"`}
        breadcrumbs={[
          { label: 'Dashboards', to: '/admin/bi/dashboards' },
          { label: 'Edit Dashboard', to: `/admin/bi/dashboards/${dashboardId}/edit` },
          { label: 'Add Widget' },
        ]}
      />

      {step === 'type' ? (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Choose Widget Type</CardTitle>
              <CardDescription>
                Select the type of widget you want to add to your dashboard
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                {WIDGET_TYPES.map((type) => (
                  <Card
                    key={type.value}
                    className={`cursor-pointer transition-colors hover:border-primary ${
                      widgetType === type.value ? 'border-primary bg-primary/5' : ''
                    }`}
                    onClick={() => setValue('widget_type', type.value)}
                  >
                    <CardContent className="pt-6">
                      <h3 className="font-medium">{type.label}</h3>
                      <p className="mt-1 text-sm text-muted-foreground">{type.description}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Or Select from Pre-designed Charts</CardTitle>
              <CardDescription>
                Choose a pre-configured chart to quickly add a widget
              </CardDescription>
            </CardHeader>
            <CardContent>
              {charts.length === 0 ? (
                <p className="py-4 text-center text-muted-foreground">
                  No charts available. Create chart definitions first.
                </p>
              ) : (
                <div className="grid max-h-96 grid-cols-2 gap-4 overflow-y-auto">
                  {charts.map((chart) => (
                    <Card
                      key={chart.id}
                      className={`cursor-pointer transition-colors hover:border-primary ${
                        chartDefinitionId === chart.id ? 'border-primary bg-primary/5' : ''
                      }`}
                      onClick={() => setValue('chart_definition_id', chart.id)}
                    >
                      <CardContent className="pt-4">
                        <div className="flex items-center justify-between">
                          <h3 className="font-medium">{chart.name}</h3>
                          <Badge variant="outline">{chart.chart_type}</Badge>
                        </div>
                        <p className="mt-1 text-sm text-muted-foreground">{chart.module}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button onClick={() => setStep('config')}>Continue to Configuration</Button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="grid grid-cols-3 gap-6">
            {/* Configuration Panel */}
            <div className="col-span-2 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Widget Settings</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="title">Title *</Label>
                    <Input
                      id="title"
                      placeholder="Widget title"
                      {...register('title', { required: 'Title is required' })}
                    />
                    {errors.title && <p className="text-sm text-red-500">{errors.title.message}</p>}
                  </div>

                  <div className="space-y-2">
                    <Label>Data Source</Label>
                    <Select
                      value={dataSourceId ?? '__none__'}
                      onValueChange={(value) =>
                        setValue('data_source_id', value === '__none__' ? undefined : value)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select a data source" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__none__">
                          None (widget stays empty until a data source is assigned)
                        </SelectItem>
                        {dataSources.map((ds) => (
                          <SelectItem key={ds.id} value={ds.id}>
                            {ds.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Width (grid units)</Label>
                      <Input
                        type="number"
                        min={1}
                        max={12}
                        {...register('grid_w', { valueAsNumber: true })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Height (grid units)</Label>
                      <Input
                        type="number"
                        min={1}
                        max={12}
                        {...register('grid_h', { valueAsNumber: true })}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>
                    {WIDGET_TYPES.find((t) => t.value === widgetType)?.label} Configuration
                  </CardTitle>
                </CardHeader>
                <CardContent>{renderConfigFields()}</CardContent>
              </Card>

              <div className="flex justify-between">
                <Button type="button" variant="outline" onClick={() => setStep('type')}>
                  Back
                </Button>
                <div className="flex gap-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => navigate(`/admin/bi/dashboards/${dashboardId}/edit`)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={saving}>
                    {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    <Save className="mr-2 h-4 w-4" />
                    Add Widget
                  </Button>
                </div>
              </div>
            </div>

            {/* Preview Panel */}
            <div className="col-span-1">
              <Card className="sticky top-4">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Eye className="h-4 w-4" />
                    Preview
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="rounded-lg border bg-muted/50 p-4">
                    <WidgetRenderer
                      widget={{
                        id: 'preview',
                        dashboard_id: dashboardId || '',
                        widget_key: 'preview',
                        title: title || 'Preview Widget',
                        widget_type: widgetType,
                        grid_x: 0,
                        grid_y: 0,
                        grid_w: watch('grid_w'),
                        grid_h: watch('grid_h'),
                        config: config,
                        display_order: 0,
                        is_active: true,
                        created_at: new Date().toISOString(),
                        updated_at: new Date().toISOString(),
                      }}
                    />
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </form>
      )}
    </div>
  );
}
