/**
 * Gauge/Progress Widget - displays a gauge or progress indicator
 */

import type { GaugeConfig } from '@/types/bi';

interface GaugeWidgetProps {
  config: GaugeConfig;
  data: Record<string, unknown>;
}

const DEFAULT_THRESHOLDS = [
  { value: 33, color: '#ef4444' }, // Red
  { value: 66, color: '#f59e0b' }, // Yellow
  { value: 100, color: '#22c55e' }, // Green
];

export function GaugeWidget({ config, data }: GaugeWidgetProps) {
  const value = Number(data[config.valueField] || 0);
  const minValue = config.minValue || 0;
  const maxValue = config.maxValue || 100;
  const thresholds = config.thresholds || DEFAULT_THRESHOLDS;

  // Calculate percentage
  const percentage = Math.min(
    100,
    Math.max(0, ((value - minValue) / (maxValue - minValue)) * 100)
  );

  // Determine color based on thresholds
  let color = thresholds[thresholds.length - 1]?.color || '#22c55e';
  for (const threshold of thresholds) {
    if (percentage <= threshold.value) {
      color = threshold.color;
      break;
    }
  }

  // SVG gauge parameters
  const size = 150;
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const arc = circumference * 0.75; // 270 degrees
  const offset = arc - (percentage / 100) * arc;

  return (
    <div className="h-full w-full flex flex-col items-center justify-center p-4">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className="transform -rotate-135"
        >
          {/* Background arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth={strokeWidth}
            strokeDasharray={`${arc} ${circumference}`}
            strokeLinecap="round"
          />
          {/* Value arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={`${arc} ${circumference}`}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-500"
          />
        </svg>
        {/* Center value */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold" style={{ color }}>
            {percentage.toFixed(0)}%
          </span>
          <span className="text-xs text-muted-foreground">
            {value.toLocaleString('en-IN')} / {maxValue.toLocaleString('en-IN')}
          </span>
        </div>
      </div>

      {/* Threshold legend */}
      <div className="flex gap-4 mt-4">
        {thresholds.map((t, i) => (
          <div key={i} className="flex items-center gap-1 text-xs">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: t.color }}
            />
            <span className="text-muted-foreground">
              {i === 0 ? '0' : thresholds[i - 1].value}-{t.value}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
