/**
 * PercentageDisplay Component
 * Rate/percentage formatting with optional basis points
 */

import { cn } from '@/lib/utils';

export interface PercentageDisplayProps {
  value: number | string | null | undefined;
  decimals?: number;
  className?: string;
  showSymbol?: boolean;
  colorize?: boolean;
  asBasisPoints?: boolean;
}

export function PercentageDisplay({
  value,
  decimals = 2,
  className,
  showSymbol = true,
  colorize = false,
  asBasisPoints = false,
}: PercentageDisplayProps) {
  const numValue = typeof value === 'string' ? parseFloat(value) : value;

  if (numValue === null || numValue === undefined || isNaN(numValue)) {
    return <span className={cn('text-muted-foreground', className)}>-</span>;
  }

  const displayValue = asBasisPoints ? numValue / 100 : numValue;
  const formatted = displayValue.toFixed(decimals);
  const symbol = showSymbol ? '%' : '';

  let colorClass = '';
  if (colorize) {
    colorClass = numValue > 0 ? 'text-green-600' : numValue < 0 ? 'text-red-600' : '';
  }

  return (
    <span className={cn('tabular-nums font-mono', colorClass, className)}>
      {formatted}{symbol}
    </span>
  );
}

/**
 * Interest rate display with spread information
 */
export function InterestRateDisplay({
  baseRate,
  spread,
  effectiveRate,
  className,
}: {
  baseRate?: number | null;
  spread?: number | null; // in basis points
  effectiveRate?: number | null;
  className?: string;
}) {
  const effective = effectiveRate ?? (baseRate && spread ? baseRate + spread / 100 : null);

  return (
    <div className={cn('space-y-1', className)}>
      <div className="font-semibold tabular-nums">
        {effective !== null && effective !== undefined ? `${(Number(effective) || 0).toFixed(2)}% p.a.` : '-'}
      </div>
      {baseRate !== undefined && spread !== undefined && (
        <div className="text-xs text-muted-foreground">
          {baseRate?.toFixed(2)}% + {spread} bps
        </div>
      )}
    </div>
  );
}

/**
 * Compact rate for tables
 */
export function RateCell({
  rate,
  className,
}: {
  rate: number | string | null | undefined;
  className?: string;
}) {
  return (
    <PercentageDisplay
      value={rate}
      decimals={2}
      className={cn('text-sm', className)}
    />
  );
}

/**
 * Percentage change with arrow indicator
 */
export function PercentageChange({
  value,
  className,
}: {
  value: number | null | undefined;
  className?: string;
}) {
  if (value === null || value === undefined) {
    return <span className={cn('text-muted-foreground', className)}>-</span>;
  }

  const isPositive = value > 0;
  const isNegative = value < 0;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-0.5 tabular-nums text-sm font-medium',
        isPositive && 'text-green-600',
        isNegative && 'text-red-600',
        className
      )}
    >
      {isPositive && (
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
        </svg>
      )}
      {isNegative && (
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      )}
      {Math.abs(value).toFixed(2)}%
    </span>
  );
}
