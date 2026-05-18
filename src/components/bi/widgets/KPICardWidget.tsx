/**
 * KPI Card Widget - displays a single metric with optional change indicator
 */

import { ArrowUpRight, ArrowDownRight, TrendingUp, DollarSign, Users, Percent, Activity } from 'lucide-react';

import type { KPICardConfig } from '@/types/bi';

interface KPICardWidgetProps {
  config: KPICardConfig;
  data: Record<string, unknown>;
}

const iconMap: Record<string, React.ElementType> = {
  dollar: DollarSign,
  users: Users,
  percent: Percent,
  trending: TrendingUp,
  activity: Activity,
};

const formatValue = (
  value: number | string | undefined,
  format?: 'currency' | 'number' | 'percentage',
  decimals = 0,
  prefix?: string,
  suffix?: string
): string => {
  if (value === undefined || value === null) return '-';

  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return '-';

  let formatted: string;

  switch (format) {
    case 'currency':
      // Format as Indian Rupees with lakhs/crores notation
      if (Math.abs(num) >= 10000000) {
        formatted = `${(num / 10000000).toFixed(decimals)} Cr`;
      } else if (Math.abs(num) >= 100000) {
        formatted = `${(num / 100000).toFixed(decimals)} L`;
      } else if (Math.abs(num) >= 1000) {
        formatted = `${(num / 1000).toFixed(decimals)} K`;
      } else {
        formatted = num.toFixed(decimals);
      }
      return `${prefix || '₹'}${formatted}${suffix || ''}`;

    case 'percentage':
      return `${prefix || ''}${num.toFixed(decimals)}${suffix || '%'}`;

    default:
      // Format as regular number with K/M notation
      if (Math.abs(num) >= 1000000) {
        formatted = `${(num / 1000000).toFixed(decimals)}M`;
      } else if (Math.abs(num) >= 1000) {
        formatted = `${(num / 1000).toFixed(decimals)}K`;
      } else {
        formatted = num.toFixed(decimals);
      }
      return `${prefix || ''}${formatted}${suffix || ''}`;
  }
};

export function KPICardWidget({ config, data }: KPICardWidgetProps) {
  const value = data[config.valueField];
  const subtitle = config.subtitleField ? data[config.subtitleField] : undefined;
  const change = config.changeField ? data[config.changeField] : undefined;

  const Icon = config.icon ? iconMap[config.icon] || Activity : Activity;
  const changeNum = change !== undefined ? (typeof change === 'string' ? parseFloat(change) : change as number) : undefined;
  const isPositive = changeNum !== undefined && changeNum >= 0;

  return (
    <div className="h-full flex flex-col justify-center p-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-muted-foreground font-medium uppercase tracking-wide">
            {String(subtitle || config.subtitleField || 'Value')}
          </p>
          <p className="text-3xl font-bold mt-1">
            {formatValue(
              value as number,
              config.valueFormat,
              config.decimals,
              config.prefix,
              config.suffix
            )}
          </p>
        </div>
        <div className="p-2 bg-primary/10 rounded-lg">
          <Icon className="h-6 w-6 text-primary" />
        </div>
      </div>

      {changeNum !== undefined && (
        <div className="flex items-center mt-3 gap-1">
          {isPositive ? (
            <ArrowUpRight className="h-4 w-4 text-green-500" />
          ) : (
            <ArrowDownRight className="h-4 w-4 text-red-500" />
          )}
          <span className={`text-sm font-medium ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
            {Math.abs(changeNum).toFixed(1)}%
          </span>
          <span className="text-sm text-muted-foreground">vs last period</span>
        </div>
      )}
    </div>
  );
}
