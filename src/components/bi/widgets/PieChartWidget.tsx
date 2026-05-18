/**
 * Pie Chart Widget - displays a pie chart
 */

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

import type { PieChartConfig } from '@/types/bi';

interface PieChartWidgetProps {
  config: PieChartConfig;
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

interface RechartsTooltipEntry {
  color?: string;
  name?: string;
  value?: number | string;
  dataKey?: string;
  payload?: Record<string, unknown>;
}

interface RechartsTooltipProps {
  active?: boolean;
  payload?: RechartsTooltipEntry[];
  label?: string | number;
}

const CustomTooltip = ({ active, payload }: RechartsTooltipProps) => {
  if (active && payload && payload.length) {
    const entry = payload[0];
    return (
      <div className="bg-white border rounded-lg shadow-lg p-3">
        <div className="flex items-center gap-2 text-sm">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: (entry.payload?.fill as string | undefined) ?? '#000' }}
          />
          <span className="font-medium">{entry.name}:</span>
          <span>{formatCompact(Number(entry.value ?? 0))}</span>
        </div>
      </div>
    );
  }
  return null;
};

export function PieChartWidget({ config, data }: PieChartWidgetProps) {
  const showLegend = config.showLegend !== false;
  const colors = config.colors || DEFAULT_COLORS;

  // Transform data for pie chart
  const pieData = data.map((item, index) => ({
    name: item[config.labelField] as string,
    value: item[config.valueField] as number,
    fill: colors[index % colors.length],
  }));

  return (
    <div className="h-full w-full p-2">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={pieData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius="80%"
            label={({ name, percent }) => `${name} (${((percent ?? 0) * 100).toFixed(0)}%)`}
            labelLine={false}
          >
            {pieData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          {showLegend && <Legend />}
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
