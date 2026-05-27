/**
 * Widget Renderer - dispatches to the correct widget component based on type
 */

import { Loader2, AlertCircle } from 'lucide-react';
import { useEffect, useState } from 'react';

import { AreaChartWidget } from './AreaChartWidget';
import { BarChartWidget } from './BarChartWidget';
import { DataTableWidget } from './DataTableWidget';
import { DonutChartWidget } from './DonutChartWidget';
import { GaugeWidget } from './GaugeWidget';
import { KPICardWidget } from './KPICardWidget';
import { LineChartWidget } from './LineChartWidget';
import { PieChartWidget } from './PieChartWidget';
import { TextMarkdownWidget } from './TextMarkdownWidget';

import { biDataSourceApi } from '@/services/biApi';
import type { DashboardWidget, WidgetConfig } from '@/types/bi';

import { logger } from '@/lib/logger';
interface WidgetRendererProps {
  widget: DashboardWidget;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export function WidgetRenderer({
  widget,
  autoRefresh = false,
  refreshInterval = 60000,
}: WidgetRendererProps) {
  const [data, setData] = useState<Record<string, unknown> | Record<string, unknown>[] | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    // Skip data fetch for markdown widgets
    if (widget.widget_type === 'TEXT_MARKDOWN') {
      setData({});
      setError(null);
      setLoading(false);
      return;
    }

    const dataSourceId = widget.data_source_id;

    if (!dataSourceId) {
      setData(null);
      setError('Assign a supported BI data source to render this widget.');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const response = await biDataSourceApi.fetch(dataSourceId);
      setData(response.data.data as Record<string, unknown>);
      setError(null);
    } catch (err) {
      logger.error('Error fetching widget data:', err);
      setError('Failed to load widget data from the configured source.');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();

    if (autoRefresh && refreshInterval > 0) {
      const interval = setInterval(fetchData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [widget.id, autoRefresh, refreshInterval]);

  if (loading) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center text-muted-foreground">
        <AlertCircle className="mb-2 h-6 w-6" />
        <p className="text-sm">{error}</p>
      </div>
    );
  }

  const config = (widget.config || {}) as WidgetConfig;

  switch (widget.widget_type) {
    // Each branch narrows the union by widget_type; we cast the still-widened
    // config to the specific shape the child widget needs.
    case 'KPI_CARD':
      return (
        <KPICardWidget
          config={config as Parameters<typeof KPICardWidget>[0]['config']}
          data={data as Record<string, unknown>}
        />
      );

    case 'LINE_CHART':
      return (
        <LineChartWidget
          config={config as Parameters<typeof LineChartWidget>[0]['config']}
          data={data as Record<string, unknown>[]}
        />
      );

    case 'BAR_CHART':
      return (
        <BarChartWidget
          config={config as Parameters<typeof BarChartWidget>[0]['config']}
          data={data as Record<string, unknown>[]}
        />
      );

    case 'PIE_CHART':
      return (
        <PieChartWidget
          config={config as Parameters<typeof PieChartWidget>[0]['config']}
          data={data as Record<string, unknown>[]}
        />
      );

    case 'DONUT_CHART':
      return (
        <DonutChartWidget
          config={config as Parameters<typeof DonutChartWidget>[0]['config']}
          data={data as Record<string, unknown>[]}
        />
      );

    case 'AREA_CHART':
      return (
        <AreaChartWidget
          config={config as Parameters<typeof AreaChartWidget>[0]['config']}
          data={data as Record<string, unknown>[]}
        />
      );

    case 'DATA_TABLE':
      return (
        <DataTableWidget
          config={config as Parameters<typeof DataTableWidget>[0]['config']}
          data={data as Record<string, unknown>[]}
        />
      );

    case 'TEXT_MARKDOWN':
      return (
        <TextMarkdownWidget config={config as Parameters<typeof TextMarkdownWidget>[0]['config']} />
      );

    case 'GAUGE_PROGRESS':
      return (
        <GaugeWidget
          config={config as Parameters<typeof GaugeWidget>[0]['config']}
          data={data as Record<string, unknown>}
        />
      );

    default:
      return (
        <div className="flex h-full w-full items-center justify-center text-muted-foreground">
          <p className="text-sm">Unknown widget type: {widget.widget_type}</p>
        </div>
      );
  }
}
