/**
 * RatingBadge Component
 * Credit rating display (AAA to D)
 */

import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import type { CreditRating } from '@/types/lending';

export interface RatingBadgeProps {
  rating: CreditRating | string | null | undefined;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showGrade?: boolean;
}

const ratingColors: Record<string, string> = {
  AAA: 'bg-emerald-100 text-emerald-800 border-emerald-400',
  AA: 'bg-green-100 text-green-800 border-green-400',
  A: 'bg-lime-100 text-lime-800 border-lime-400',
  BBB: 'bg-yellow-100 text-yellow-800 border-yellow-400',
  BB: 'bg-amber-100 text-amber-800 border-amber-400',
  B: 'bg-orange-100 text-orange-800 border-orange-400',
  C: 'bg-red-100 text-red-800 border-red-400',
  D: 'bg-red-200 text-red-900 border-red-500',
};

const ratingDescriptions: Record<string, string> = {
  AAA: 'Highest Safety',
  AA: 'High Safety',
  A: 'Adequate Safety',
  BBB: 'Moderate Safety',
  BB: 'Moderate Risk',
  B: 'High Risk',
  C: 'Very High Risk',
  D: 'Default',
};

const sizeClasses = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-0.5',
  lg: 'text-sm px-3 py-1 font-semibold',
};

export function RatingBadge({ rating, className, size = 'md', showGrade = false }: RatingBadgeProps) {
  if (!rating) {
    return <span className="text-muted-foreground text-sm">NR</span>;
  }

  const colorClass = ratingColors[rating] || 'bg-slate-100 text-slate-700 border-slate-300';
  const description = ratingDescriptions[rating];

  return (
    <Badge
      variant="outline"
      className={cn('font-bold border-2', colorClass, sizeClasses[size], className)}
      title={description}
    >
      {rating}
      {showGrade && description && <span className="ml-1 font-normal opacity-75">({description})</span>}
    </Badge>
  );
}

/**
 * Full rating display with description
 */
export function RatingDisplay({
  rating,
  className,
  variant = 'default',
}: {
  rating: CreditRating | string | null | undefined;
  className?: string;
  variant?: 'default' | 'compact' | 'detailed';
}) {
  if (!rating) {
    return (
      <div className={cn('text-muted-foreground', className)}>
        <span className="text-sm">Not Rated</span>
      </div>
    );
  }

  const colorClass = ratingColors[rating] || 'bg-slate-100 text-slate-700';
  const description = ratingDescriptions[rating];

  if (variant === 'compact') {
    return <RatingBadge rating={rating} className={className} size="sm" />;
  }

  if (variant === 'detailed') {
    return (
      <div className={cn('flex items-center gap-3', className)}>
        <RatingBadge rating={rating} size="lg" />
        <div className="flex flex-col">
          <span className="text-sm font-medium">{description}</span>
          <span className="text-xs text-muted-foreground">Internal Credit Rating</span>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <RatingBadge rating={rating} />
      {description && <span className="text-sm text-muted-foreground">{description}</span>}
    </div>
  );
}

/**
 * Rating scale visual
 */
export function RatingScale({ currentRating, className }: { currentRating?: CreditRating | string; className?: string }) {
  const ratings: CreditRating[] = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'C', 'D'];

  return (
    <div className={cn('flex items-center gap-1', className)}>
      {ratings.map((r) => (
        <div
          key={r}
          className={cn(
            'px-2 py-1 text-xs font-semibold rounded transition-all',
            currentRating === r
              ? cn(ratingColors[r], 'ring-2 ring-offset-1 ring-slate-400')
              : 'bg-slate-50 text-slate-400'
          )}
        >
          {r}
        </div>
      ))}
    </div>
  );
}
