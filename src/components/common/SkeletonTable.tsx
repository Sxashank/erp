/**
 * SkeletonTable — renders while a table query is loading. See CLAUDE.md §9.8.
 */

import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

export interface SkeletonTableProps {
  rows?: number;
  columns?: number;
  className?: string;
}

export function SkeletonTable({
  rows = 8,
  columns = 5,
  className,
}: SkeletonTableProps): JSX.Element {
  return (
    <div
      className={cn('w-full space-y-3', className)}
      role="status"
      aria-label="Loading"
    >
      <div className="flex gap-3 border-b pb-3">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} className="h-4 flex-1" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex gap-3">
          {Array.from({ length: columns }).map((_, c) => (
            <Skeleton key={c} className="h-8 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}
