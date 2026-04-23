/**
 * Bar Chart Widget - displays a bar chart with multiple series
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { BarChartConfig } from '@/types/bi';

interface BarChartWidgetProps {
  config: BarChartConfig;
  data: Record<string, unknown>[];
}

const DEFAULT_COLORS = [
  '#8884d8',
  '#82ca9d',
  '#ffc658',
  '#ff7300',
  '#0088FE',
  '#00C49F',
  '#FFBB28',
  '#FF8042',
];

const formatCompact = (value: number | undefined | null) => {
  const num = Number(value) || 0;
  if (Math.abs(num) >= 10000000) {
    return `${(num / 10000000).toFixed(1)}Cr`;
  }
  if (Math.abs(num) >= 100000) {
    return `${(num / 100000).toFixed(1)}L`;
  }
  if (Math.abs(num) >= 1000) {
    return `${(num / 1000).toFixed(0)}K`;
  }
  return num.toFixed(0);
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white border rounded-lg shadow-lg p-3">
        <p className="font-medium mb-2">{label}</p>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center gap-2 text-sm">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-muted-foreground">{entry.name}:</span>
            <span className="font-medium">{formatCompact(entry.value)}</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export function BarChartWidget({ config, data }: BarChartWidgetProps) {
  const showLegend = config.showLegend !== false;
  const stacked = config.stacked === true;

  return (
    <div className="h-full w-full p-2">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis
            dataKey={config.xAxisField}
            tick={{ fontSize: 11 }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tick={{ fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={formatCompact}
          />
          <Tooltip content={<CustomTooltip />} />
          {showLegend && <Legend />}
          {config.series.map((series, index) => (
            <Bar
              key={series.dataKey}
              dataKey={series.dataKey}
              name={series.name}
              fill={series.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length]}
              radius={stacked ? 0 : [4, 4, 0, 0]}
              stackId={stacked ? 'stack' : undefined}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
