/**
 * LimitStatusPill — pill for RBI single-borrower / group exposure limit
 * utilisation status. CLAUDE.md §5.1 forbids inline `<Badge>` for status in
 * pages; this component is the canonical home for the limit-status pattern.
 */

import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

export type LimitStatus = 'WITHIN_LIMIT' | 'NEAR_LIMIT' | 'BREACHED';

const colors: Record<LimitStatus, string> = {
  WITHIN_LIMIT: 'bg-green-100 text-green-700 border-green-300',
  NEAR_LIMIT: 'bg-amber-100 text-amber-700 border-amber-300',
  BREACHED: 'bg-red-100 text-red-700 border-red-300',
};

const labels: Record<LimitStatus, string> = {
  WITHIN_LIMIT: 'Within limit',
  NEAR_LIMIT: 'Near limit',
  BREACHED: 'Breached',
};

export interface LimitStatusPillProps {
  status: LimitStatus;
  className?: string;
}

export function LimitStatusPill({ status, className }: LimitStatusPillProps): JSX.Element {
  return (
    <Badge variant="outline" className={cn('text-xs font-medium', colors[status], className)}>
      {labels[status]}
    </Badge>
  );
}
