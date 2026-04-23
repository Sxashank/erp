/**
 * Widget Renderer - dispatches to the correct widget component based on type
 */

import { useEffect, useState } from 'react';
import { Loader2, AlertCircle } from 'lucide-react';
import { DashboardWidget, WidgetType, WidgetConfig } from '@/types/bi';
import { biDataSourceApi } from '@/services/biApi';

import { KPICardWidget } from './KPICardWidget';
import { LineChartWidget } from './LineChartWidget';
import { BarChartWidget } from './BarChartWidget';
import { PieChartWidget } from './PieChartWidget';
import { DonutChartWidget } from './DonutChartWidget';
import { AreaChartWidget } from './AreaChartWidget';
import { DataTableWidget } from './DataTableWidget';
import { TextMarkdownWidget } from './TextMarkdownWidget';
import { GaugeWidget } from './GaugeWidget';

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
  const [data, setData] = useState<Record<string, unknown> | Record<string, unknown>[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    // Skip data fetch for markdown widgets
    if (widget.widget_type === 'TEXT_MARKDOWN') {
      setData({});
      setLoading(false);
      return;
    }

    // Determine data source
    const dataSourceId = widget.data_source_id || widget.chart_definition?.id;

    if (!dataSourceId && !widget.config) {
      // Use mock data for demo
      setData(getMockData(widget.widget_type));
      setLoading(false);
      return;
    }

    if (dataSourceId) {
      try {
        setLoading(true);
        const response = await biDataSourceApi.fetch(dataSourceId);
        setData(response.data.data as Record<string, unknown>);
        setError(null);
      } catch (err) {
        console.error('Error fetching widget data:', err);
        setError('Failed to load data');
        // Fall back to mock data
        setData(getMockData(widget.widget_type));
      } finally {
        setLoading(false);
      }
    } else {
      // Use mock data if no data source
      setData(getMockData(widget.widget_type));
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
      <div className="h-full w-full flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="h-full w-full flex flex-col items-center justify-center text-muted-foreground">
        <AlertCircle className="h-6 w-6 mb-2" />
        <p className="text-sm">{error}</p>
      </div>
    );
  }

  const config = (widget.config || {}) as WidgetConfig;

  switch (widget.widget_type) {
    case 'KPI_CARD':
      return <KPICardWidget config={config as any} data={data as Record<string, unknown>} />;

    case 'LINE_CHART':
      return <LineChartWidget config={config as any} data={data as Record<string, unknown>[]} />;

    case 'BAR_CHART':
      return <BarChartWidget config={config as any} data={data as Record<string, unknown>[]} />;

    case 'PIE_CHART':
      return <PieChartWidget config={config as any} data={data as Record<string, unknown>[]} />;

    case 'DONUT_CHART':
      return <DonutChartWidget config={config as any} data={data as Record<string, unknown>[]} />;

    case 'AREA_CHART':
      return <AreaChartWidget config={config as any} data={data as Record<string, unknown>[]} />;

    case 'DATA_TABLE':
      return <DataTableWidget config={config as any} data={data as Record<string, unknown>[]} />;

    case 'TEXT_MARKDOWN':
      return <TextMarkdownWidget config={config as any} />;

    case 'GAUGE_PROGRESS':
      return <GaugeWidget config={config as any} data={data as Record<string, unknown>} />;

    default:
      return (
        <div className="h-full w-full flex items-center justify-center text-muted-foreground">
          <p className="text-sm">Unknown widget type: {widget.widget_type}</p>
        </div>
      );
  }
}

// Mock data for demo purposes
function getMockData(widgetType: WidgetType): Record<string, unknown> | Record<string, unknown>[] {
  switch (widgetType) {
    case 'KPI_CARD':
      return {
        value: 15750000,
        subtitle: 'Revenue MTD',
        change: 12.5,
      };

    case 'LINE_CHART':
    case 'AREA_CHART':
      return [
        { month: 'Jan', revenue: 4000000, expenses: 2400000 },
        { month: 'Feb', revenue: 3000000, expenses: 1398000 },
        { month: 'Mar', revenue: 2000000, expenses: 9800000 },
        { month: 'Apr', revenue: 2780000, expenses: 3908000 },
        { month: 'May', revenue: 1890000, expenses: 4800000 },
        { month: 'Jun', revenue: 2390000, expenses: 3800000 },
      ];

    case 'BAR_CHART':
      return [
        { name: 'Branch A', value: 4000 },
        { name: 'Branch B', value: 3000 },
        { name: 'Branch C', value: 2000 },
        { name: 'Branch D', value: 2780 },
        { name: 'Branch E', value: 1890 },
      ];

    case 'PIE_CHART':
    case 'DONUT_CHART':
      return [
        { name: 'Product A', value: 400 },
        { name: 'Product B', value: 300 },
        { name: 'Product C', value: 200 },
        { name: 'Product D', value: 100 },
      ];

    case 'DATA_TABLE':
      return [
        { id: '001', name: 'John Doe', amount: 50000, date: '2024-01-15' },
        { id: '002', name: 'Jane Smith', amount: 75000, date: '2024-01-16' },
        { id: '003', name: 'Bob Johnson', amount: 32000, date: '2024-01-17' },
        { id: '004', name: 'Alice Brown', amount: 98000, date: '2024-01-18' },
        { id: '005', name: 'Charlie Wilson', amount: 45000, date: '2024-01-19' },
      ];

    case 'GAUGE_PROGRESS':
      return {
        value: 72,
      };

    default:
      return {};
  }
}
