/**
 * DPDBadge Component
 * Days Past Due indicator with visual severity levels
 */

import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

export interface DPDBadgeProps {
  dpd: number | null | undefined;
  className?: string;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

/**
 * Get color based on DPD severity
 * Based on RBI IRAC norms:
 * - 0-30: Standard (Green)
 * - 1-30: SMA-0 (Light Yellow)
 * - 31-60: SMA-1 (Yellow)
 * - 61-90: SMA-2 (Orange)
 * - 91+: NPA (Red)
 */
function getDPDColor(dpd: number): string {
  if (dpd <= 0) return 'bg-green-100 text-green-700 border-green-300';
  if (dpd <= 30) return 'bg-yellow-100 text-yellow-700 border-yellow-300';
  if (dpd <= 60) return 'bg-amber-100 text-amber-700 border-amber-300';
  if (dpd <= 90) return 'bg-orange-100 text-orange-700 border-orange-300';
  return 'bg-red-100 text-red-700 border-red-300';
}

/**
 * Get category label based on DPD
 */
function getDPDCategory(dpd: number): string {
  if (dpd <= 0) return 'Current';
  if (dpd <= 30) return 'SMA-0';
  if (dpd <= 60) return 'SMA-1';
  if (dpd <= 90) return 'SMA-2';
  if (dpd <= 365) return 'Sub-Standard';
  if (dpd <= 730) return 'Doubtful-1';
  if (dpd <= 1095) return 'Doubtful-2';
  if (dpd <= 1460) return 'Doubtful-3';
  return 'Loss';
}

const sizeClasses = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-0.5',
  lg: 'text-sm px-3 py-1',
};

export function DPDBadge({ dpd, className, showLabel = false, size = 'md' }: DPDBadgeProps) {
  if (dpd === null || dpd === undefined) {
    return <span className="text-muted-foreground">-</span>;
  }

  const colorClass = getDPDColor(dpd);
  const category = getDPDCategory(dpd);

  return (
    <Badge variant="outline" className={cn('font-mono font-medium border', colorClass, sizeClasses[size], className)}>
      {dpd} {showLabel ? `(${category})` : 'days'}
    </Badge>
  );
}

/**
 * Visual DPD indicator with filled circles
 */
export function DPDIndicator({ dpd, className }: { dpd: number | null | undefined; className?: string }) {
  if (dpd === null || dpd === undefined) {
    return null;
  }

  // 5 circles, filled based on severity
  const filledCount = dpd <= 0 ? 5 : dpd <= 30 ? 4 : dpd <= 60 ? 3 : dpd <= 90 ? 2 : 1;

  const getCircleColor = (index: number) => {
    if (index >= filledCount) return 'text-slate-200';
    if (dpd <= 0) return 'text-green-500';
    if (dpd <= 30) return 'text-yellow-500';
    if (dpd <= 60) return 'text-amber-500';
    if (dpd <= 90) return 'text-orange-500';
    return 'text-red-500';
  };

  return (
    <div className={cn('flex items-center gap-0.5', className)} title={`${dpd} days past due`}>
      {[0, 1, 2, 3, 4].map((i) => (
        <svg
          key={i}
          className={cn('w-2.5 h-2.5', getCircleColor(4 - i))}
          fill="currentColor"
          viewBox="0 0 8 8"
        >
          <circle cx="4" cy="4" r="4" />
        </svg>
      ))}
    </div>
  );
}

/**
 * Compact DPD display for tables
 */
export function DPDCell({ dpd, className }: { dpd: number | null | undefined; className?: string }) {
  if (dpd === null || dpd === undefined) {
    return <span className="text-muted-foreground text-sm">-</span>;
  }

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <span className={cn('text-sm font-mono', dpd > 90 ? 'text-red-600 font-semibold' : dpd > 0 ? 'text-amber-600' : 'text-green-600')}>
        {dpd}
      </span>
      <DPDIndicator dpd={dpd} />
    </div>
  );
}
