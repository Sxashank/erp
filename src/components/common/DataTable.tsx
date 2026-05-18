/**
 * DataTable — the canonical list component. See CLAUDE.md §5.1, §9.2, §9.3.
 *
 * Handles loading (SkeletonTable), empty (EmptyState), error (ErrorState) in one place.
 * Rows are right-aligned for numeric columns (pass `align: 'right'`).
 *
 * Usage:
 *   <DataTable
 *     data={loans ?? []}
 *     isLoading={isLoading}
 *     error={error}
 *     onRetry={refetch}
 *     getRowId={(r) => r.id}
 *     columns={[
 *       { key: 'applicationNumber', header: 'Application #' },
 *       { key: 'amount', header: 'Amount', align: 'right', render: (r) => <AmountDisplay amount={r.amount} /> },
 *     ]}
 *   />
 */

import { ArrowDown, ArrowUp, ArrowUpDown } from 'lucide-react';
import { useMemo, useState } from 'react';

import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { SkeletonTable } from '@/components/common/SkeletonTable';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { cn } from '@/lib/utils';

export interface Column<T> {
  key: string;
  header: string;
  render?: (row: T, index: number) => React.ReactNode;
  align?: 'left' | 'right' | 'center';
  sortable?: boolean;
  sortValue?: (row: T) => string | number | null | undefined;
  width?: string;
  className?: string;
}

export interface DataTableProps<T> {
  data: readonly T[];
  columns: Column<T>[];
  getRowId: (row: T, index: number) => string;
  isLoading?: boolean;
  error?: unknown;
  onRetry?: () => void;

  emptyTitle?: string;
  emptySubtitle?: string;
  emptyAction?: React.ReactNode;

  onRowClick?: (row: T) => void;
  rowClassName?: (row: T) => string | undefined;

  dense?: boolean;
  stickyHeader?: boolean;
  className?: string;
}

type SortDir = 'asc' | 'desc';

export function DataTable<T>({
  data,
  columns,
  getRowId,
  isLoading,
  error,
  onRetry,
  emptyTitle = 'No results',
  emptySubtitle,
  emptyAction,
  onRowClick,
  rowClassName,
  dense,
  stickyHeader,
  className,
}: DataTableProps<T>): JSX.Element {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  const sorted = useMemo(() => {
    if (!sortKey) return data;
    const column = columns.find((c) => c.key === sortKey);
    if (!column || !column.sortable) return data;
    const sortFn =
      column.sortValue ?? ((r: T) => (r as unknown as Record<string, unknown>)[column.key]);
    const arr = [...data];
    arr.sort((a, b) => {
      const av = sortFn(a);
      const bv = sortFn(b);
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      if (av < bv) return sortDir === 'asc' ? -1 : 1;
      if (av > bv) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
    return arr;
  }, [data, columns, sortKey, sortDir]);

  function handleHeaderClick(col: Column<T>): void {
    if (!col.sortable) return;
    if (sortKey === col.key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(col.key);
      setSortDir('asc');
    }
  }

  if (error) {
    return <ErrorState error={error} onRetry={onRetry} />;
  }
  if (isLoading) {
    return <SkeletonTable rows={8} columns={columns.length} />;
  }
  if (data.length === 0) {
    return <EmptyState title={emptyTitle} subtitle={emptySubtitle} action={emptyAction} />;
  }

  return (
    <div className={cn('overflow-hidden rounded-lg border bg-background', className)}>
      <div className="max-w-full overflow-x-auto">
        <Table>
          <TableHeader className={cn(stickyHeader && 'sticky top-0 z-10 bg-background')}>
            <TableRow>
              {columns.map((col) => {
                const active = sortKey === col.key;
                return (
                  <TableHead
                    key={col.key}
                    scope="col"
                    style={col.width ? { width: col.width } : undefined}
                    className={cn(
                      col.align === 'right' && 'text-right',
                      col.align === 'center' && 'text-center',
                      col.sortable && 'cursor-pointer select-none',
                      col.className,
                    )}
                    onClick={() => handleHeaderClick(col)}
                    aria-sort={
                      active ? (sortDir === 'asc' ? 'ascending' : 'descending') : undefined
                    }
                  >
                    <span className="inline-flex items-center gap-1">
                      {col.header}
                      {col.sortable &&
                        (active ? (
                          sortDir === 'asc' ? (
                            <ArrowUp className="h-3.5 w-3.5" aria-hidden="true" />
                          ) : (
                            <ArrowDown className="h-3.5 w-3.5" aria-hidden="true" />
                          )
                        ) : (
                          <ArrowUpDown
                            className="h-3.5 w-3.5 opacity-50"
                            aria-hidden="true"
                          />
                        ))}
                    </span>
                  </TableHead>
                );
              })}
            </TableRow>
          </TableHeader>
          <TableBody>
            {sorted.map((row, i) => (
              <TableRow
                key={getRowId(row, i)}
                className={cn(
                  dense && 'h-10',
                  onRowClick && 'cursor-pointer hover:bg-muted/50',
                  rowClassName?.(row),
                )}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
              >
                {columns.map((col) => (
                  <TableCell
                    key={col.key}
                    className={cn(
                      col.align === 'right' && 'text-right tabular-nums',
                      col.align === 'center' && 'text-center',
                      col.className,
                    )}
                  >
                    {col.render
                      ? col.render(row, i)
                      : String(
                          (row as unknown as Record<string, unknown>)[col.key] ?? '',
                        )}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
