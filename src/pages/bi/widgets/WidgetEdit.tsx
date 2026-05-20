/**
 * Widget Edit Page - Full page editor for widget configuration
 */

import { Loader2, Save, Eye } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useParams, useNavigate } from 'react-router-dom';

import { WidgetRenderer } from '@/components/bi';
import { PageHeader } from '@/components/common/PageHeader';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { biWidgetApi, biChartApi, biDataSourceApi } from '@/services/biApi';
import { logger } from "@/lib/logger";
import type {
  DashboardWidget,
  ChartDefinitionListItem,
  DataSourceListItem,
  WidgetType,
} from '@/types/bi';
import { getErrorMessage } from "@/lib/errorMessage";

interface FormData {
  title: string;
  widget_type: WidgetType;
  chart_definition_id?: string;
  data_source_id?: string;
  grid_w: number;
  grid_h: number;
  config: Record<string, any>;
}

const WIDGET_TYPES: { value: WidgetType; label: string }[] = [
  { value: 'KPI_CARD', label: 'KPI Card' },
  { value: 'LINE_CHART', label: 'Line Chart' },
  { value: 'BAR_CHART', label: 'Bar Chart' },
  { value: 'PIE_CHART', label: 'Pie Chart' },
  { value: 'DONUT_CHART', label: 'Donut Chart' },
  { value: 'AREA_CHART', label: 'Area Chart' },
  { value: 'DATA_TABLE', label: 'Data Table' },
  { value: 'TEXT_MARKDOWN', label: 'Text/Markdown' },
  { value: 'GAUGE_PROGRESS', label: 'Gauge/Progress' },
];

export function WidgetEdit() {
  const { dashboardId, widgetId } = useParams<{ dashboardId: string; widgetId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [widget, setWidget] = useState<DashboardWidget | null>(null);
  const [charts, setCharts] = useState<ChartDefinitionListItem[]>([]);
  const [dataSources, setDataSources] = useState<DataSourceListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [previewData, setPreviewData] = useState<any[]>([]);

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

  const fetchData = async () => {
    if (!dashboardId || !widgetId) return;

    try {
      setLoading(true);
      const [widgetRes, chartsRes, dataSourcesRes] = await Promise.all([
        biWidgetApi.get(dashboardId, widgetId),
        biChartApi.list(),
        biDataSourceApi.list(),
      ]);

      setWidget(widgetRes.data);
      setCharts(chartsRes.data);
      setDataSources(dataSourcesRes.data);

      // Set form values
      const w = widgetRes.data;
      setValue('title', w.title);
      setValue('widget_type', w.widget_type);
      setValue('chart_definition_id', w.chart_definition_id || '');
      setValue('data_source_id', w.data_source_id || '');
      setValue('grid_w', w.grid_w);
      setValue('grid_h', w.grid_h);
      setValue('config', w.config || {});
    } catch (error) {
      logger.error('Error fetching data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load widget',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [dashboardId, widgetId]);

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

  const onSubmit = async (data: FormData) => {
    if (!dashboardId || !widgetId) return;

    try {
      setSaving(true);
      await biWidgetApi.update(dashboardId, widgetId, {
        title: data.title,
        chart_definition_id: data.chart_definition_id || undefined,
        data_source_id: data.data_source_id || undefined,
        grid_w: data.grid_w,
        grid_h: data.grid_h,
        config: data.config,
      });

      toast({
        title: 'Success',
        description: 'Widget updated successfully',
      });

      navigate(`/admin/bi/dashboards/${dashboardId}/edit`);
    } catch (error: unknown) {
      logger.error('Error updating widget:', error);
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to update widget'),
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
            <div className="space-y-2">
              <Label>Icon</Label>
              <Input
                placeholder="DollarSign"
                value={config.icon || ''}
                onChange={(e) => updateConfig('icon', e.target.value)}
              />
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
            {widgetType === 'AREA_CHART' && (
              <div className="flex items-center justify-between">
                <Label>Stacked</Label>
                <Switch
                  checked={config.stacked ?? false}
                  onCheckedChange={(checked) => updateConfig('stacked', checked)}
                />
              </div>
            )}
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
            {widgetType === 'DONUT_CHART' && (
              <>
                <div className="space-y-2">
                  <Label>Inner Radius</Label>
                  <Input
                    type="number"
                    placeholder="60"
                    value={config.innerRadius || 60}
                    onChange={(e) => updateConfig('innerRadius', parseInt(e.target.value))}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Outer Radius</Label>
                  <Input
                    type="number"
                    placeholder="80"
                    value={config.outerRadius || 80}
                    onChange={(e) => updateConfig('outerRadius', parseInt(e.target.value))}
                  />
                </div>
              </>
            )}
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
            <div className="flex items-center justify-between">
              <Label>Sortable</Label>
              <Switch
                checked={config.sortable ?? true}
                onCheckedChange={(checked) => updateConfig('sortable', checked)}
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
            <div className="space-y-2">
              <Label>Thresholds (JSON array)</Label>
              <Textarea
                placeholder='[{"value": 30, "color": "red"}, {"value": 70, "color": "yellow"}, {"value": 100, "color": "green"}]'
                rows={3}
                value={JSON.stringify(config.thresholds || [], null, 2)}
                onChange={(e) => {
                  try {
                    updateConfig('thresholds', JSON.parse(e.target.value));
                  } catch {}
                }}
              />
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

  if (!widget) {
    return (
      <div className="py-12 text-center">
        <p className="text-muted-foreground">Widget not found</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => navigate(`/admin/bi/dashboards/${dashboardId}/edit`)}
        >
          Back to Dashboard
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Edit Widget"
        subtitle="Configure widget settings and appearance"
        breadcrumbs={[
          { label: 'Dashboards', to: '/admin/bi/dashboards' },
          { label: 'Edit Dashboard', to: `/admin/bi/dashboards/${dashboardId}/edit` },
          { label: 'Edit Widget' },
        ]}
      />

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="grid grid-cols-3 gap-6">
          {/* Configuration Panel */}
          <div className="col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Basic Settings</CardTitle>
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
                  <Label>Widget Type *</Label>
                  <Select
                    value={widgetType}
                    onValueChange={(value) => setValue('widget_type', value as WidgetType)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {WIDGET_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Chart Definition</Label>
                    <Select
                      value={chartDefinitionId || ''}
                      onValueChange={(value) => setValue('chart_definition_id', value || undefined)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select a chart" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__none__">None</SelectItem>
                        {charts.map((chart) => (
                          <SelectItem key={chart.id} value={chart.id}>
                            {chart.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Data Source</Label>
                    <Select
                      value={dataSourceId || ''}
                      onValueChange={(value) => setValue('data_source_id', value || undefined)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select a data source" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__none__">None</SelectItem>
                        {dataSources.map((ds) => (
                          <SelectItem key={ds.id} value={ds.id}>
                            {ds.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
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
                <CardTitle>Widget Configuration</CardTitle>
                <CardDescription>
                  Configure the specific settings for this{' '}
                  {WIDGET_TYPES.find((t) => t.value === widgetType)?.label || 'widget'}
                </CardDescription>
              </CardHeader>
              <CardContent>{renderConfigFields()}</CardContent>
            </Card>

            <div className="flex justify-end gap-4">
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
                Save Widget
              </Button>
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
                      ...widget,
                      title: watch('title'),
                      widget_type: widgetType,
                      config: config,
                    }}
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </form>
    </div>
  );
}
