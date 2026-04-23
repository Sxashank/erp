/**
 * Donut Chart Widget - displays a donut chart
 */

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { DonutChartConfig } from '@/types/bi';

interface DonutChartWidgetProps {
  config: DonutChartConfig;
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
  '#a855f7',
  '#ec4899',
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

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const entry = payload[0];
    return (
      <div className="bg-white border rounded-lg shadow-lg p-3">
        <div className="flex items-center gap-2 text-sm">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: entry.payload.fill }}
          />
          <span className="font-medium">{entry.name}:</span>
          <span>{formatCompact(entry.value)}</span>
        </div>
      </div>
    );
  }
  return null;
};

export function DonutChartWidget({ config, data }: DonutChartWidgetProps) {
  const showLegend = config.showLegend !== false;
  const colors = config.colors || DEFAULT_COLORS;
  const innerRadius = config.innerRadius || 60;
  const outerRadius = config.outerRadius || 80;

  // Transform data for donut chart
  const donutData = data.map((item, index) => ({
    name: item[config.labelField] as string,
    value: item[config.valueField] as number,
    fill: colors[index % colors.length],
  }));

  // Calculate total for center display
  const total = donutData.reduce((sum, item) => sum + (item.value || 0), 0);

  return (
    <div className="h-full w-full p-2 relative">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={donutData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={`${innerRadius}%`}
            outerRadius={`${outerRadius}%`}
          >
            {donutData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          {showLegend && <Legend />}
        </PieChart>
      </ResponsiveContainer>
      {/* Center total display */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="text-center">
          <p className="text-2xl font-bold">{formatCompact(total)}</p>
          <p className="text-xs text-muted-foreground">Total</p>
        </div>
      </div>
    </div>
  );
}
