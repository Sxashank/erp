/**
 * FilterBar — row of filters above a DataTable. See CLAUDE.md §9.2.
 */

import { Search, X } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

export interface FilterBarProps {
  search?: string;
  onSearchChange?: (v: string) => void;
  searchPlaceholder?: string;
  onClear?: () => void;
  children?: React.ReactNode;
  className?: string;
}

export function FilterBar({
  search,
  onSearchChange,
  searchPlaceholder = 'Search…',
  onClear,
  children,
  className,
}: FilterBarProps): JSX.Element {
  const hasFilters = !!search || !!children;
  return (
    <div
      className={cn(
        'mb-4 flex flex-wrap items-center gap-2 rounded-lg border bg-background p-3',
        className,
      )}
      role="search"
    >
      {onSearchChange && (
        <div className="relative min-w-[240px] flex-1">
          <Search
            className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground"
            aria-hidden="true"
          />
          <Input
            type="search"
            value={search ?? ''}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder={searchPlaceholder}
            className="pl-8"
            aria-label={searchPlaceholder}
          />
        </div>
      )}
      {children}
      {onClear && hasFilters && (
        <Button variant="ghost" size="sm" onClick={onClear}>
          <X className="mr-1 h-4 w-4" aria-hidden="true" />
          Clear
        </Button>
      )}
    </div>
  );
}
