/**
 * DetailGrid — read-only key/value display for detail pages. See CLAUDE.md §9.2.
 */

import { cn } from '@/lib/utils';

export interface DetailField {
  label: string;
  value: React.ReactNode;
  span?: 1 | 2 | 3;
  className?: string;
}

export interface DetailGridProps {
  fields: DetailField[];
  columns?: 2 | 3 | 4;
  className?: string;
}

export function DetailGrid({ fields, columns = 3, className }: DetailGridProps): JSX.Element {
  const gridClass =
    columns === 2
      ? 'sm:grid-cols-2'
      : columns === 3
        ? 'sm:grid-cols-2 lg:grid-cols-3'
        : 'sm:grid-cols-2 lg:grid-cols-4';

  return (
    <dl className={cn('grid grid-cols-1 gap-6', gridClass, className)}>
      {fields.map((f, i) => (
        <div
          key={`${f.label}-${i}`}
          className={cn(
            f.span === 2 && 'sm:col-span-2',
            f.span === 3 && 'lg:col-span-3',
            f.className,
          )}
        >
          <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {f.label}
          </dt>
          <dd className="mt-1 break-words text-sm font-medium">{f.value ?? '-'}</dd>
        </div>
      ))}
    </dl>
  );
}
