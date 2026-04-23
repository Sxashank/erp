/**
 * DateDisplay Component
 * Indian date format display (DD-MMM-YYYY)
 */

import { format, parseISO, isValid, formatDistanceToNow, differenceInDays } from 'date-fns';
import { cn } from '@/lib/utils';

export interface DateDisplayProps {
  date: string | Date | null | undefined;
  format?: 'short' | 'long' | 'relative' | string;
  formatStr?: string;
  className?: string;
  showRelative?: boolean;
  showTime?: boolean;
}

/**
 * Parse date from various formats
 */
function parseDate(date: string | Date | null | undefined): Date | null {
  if (!date) return null;

  if (date instanceof Date) {
    return isValid(date) ? date : null;
  }

  try {
    const parsed = parseISO(date);
    return isValid(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

/**
 * Main date display component
 */
export function DateDisplay({
  date,
  format: formatAlias,
  formatStr: formatStrProp,
  className,
  showRelative = false,
  showTime = false,
}: DateDisplayProps) {
  // Resolve formatStr from format alias
  const formatStr = formatStrProp ?? (
    formatAlias === 'short' ? 'dd-MMM-yyyy' :
    formatAlias === 'long' ? 'dd MMMM yyyy' :
    formatAlias === 'relative' ? 'dd-MMM-yyyy' :
    formatAlias ?? 'dd-MMM-yyyy'
  );
  const isRelativeFormat = formatAlias === 'relative' || showRelative;

  const parsedDate = parseDate(date);

  if (!parsedDate) {
    return <span className={cn('text-muted-foreground', className)}>-</span>;
  }

  if (formatAlias === 'relative' && parsedDate) {
    return (
      <span className={cn('whitespace-nowrap', className)} title={format(parsedDate, 'PPpp')}>
        {formatDistanceToNow(parsedDate, { addSuffix: true })}
      </span>
    );
  }

  const displayFormat = showTime ? `${formatStr} HH:mm` : formatStr;
  const formatted = format(parsedDate, displayFormat);
  const relative = isRelativeFormat ? formatDistanceToNow(parsedDate, { addSuffix: true }) : null;

  return (
    <span className={cn('whitespace-nowrap', className)} title={format(parsedDate, 'PPpp')}>
      {formatted}
      {relative && <span className="ml-1 text-muted-foreground text-sm">({relative})</span>}
    </span>
  );
}

/**
 * Date range display
 */
export function DateRangeDisplay({
  startDate,
  endDate,
  className,
}: {
  startDate: string | Date | null | undefined;
  endDate: string | Date | null | undefined;
  className?: string;
}) {
  const start = parseDate(startDate);
  const end = parseDate(endDate);

  if (!start && !end) {
    return <span className={cn('text-muted-foreground', className)}>-</span>;
  }

  return (
    <span className={cn('whitespace-nowrap', className)}>
      {start ? format(start, 'dd-MMM-yyyy') : '-'}
      <span className="mx-2 text-muted-foreground">to</span>
      {end ? format(end, 'dd-MMM-yyyy') : '-'}
    </span>
  );
}

/**
 * Due date with overdue highlighting
 */
export function DueDateDisplay({
  date,
  className,
}: {
  date: string | Date | null | undefined;
  className?: string;
}) {
  const parsedDate = parseDate(date);

  if (!parsedDate) {
    return <span className={cn('text-muted-foreground', className)}>-</span>;
  }

  const today = new Date();
  const daysUntil = differenceInDays(parsedDate, today);
  const isOverdue = daysUntil < 0;
  const isDueSoon = daysUntil >= 0 && daysUntil <= 7;

  const colorClass = isOverdue
    ? 'text-red-600 font-medium'
    : isDueSoon
      ? 'text-amber-600'
      : '';

  const formatted = format(parsedDate, 'dd-MMM-yyyy');

  return (
    <span className={cn('whitespace-nowrap', colorClass, className)} title={`Due ${formatted}`}>
      {formatted}
      {isOverdue && (
        <span className="ml-1 text-xs">({Math.abs(daysUntil)} days overdue)</span>
      )}
      {isDueSoon && !isOverdue && daysUntil > 0 && (
        <span className="ml-1 text-xs text-muted-foreground">({daysUntil} days)</span>
      )}
      {daysUntil === 0 && (
        <span className="ml-1 text-xs font-semibold">(Today)</span>
      )}
    </span>
  );
}

/**
 * Compact date for tables
 */
export function DateCell({
  date,
  className,
}: {
  date: string | Date | null | undefined;
  className?: string;
}) {
  return <DateDisplay date={date} className={cn('text-sm', className)} />;
}

/**
 * DateTime display for audit logs
 */
export function DateTimeDisplay({
  date,
  className,
}: {
  date: string | Date | null | undefined;
  className?: string;
}) {
  return (
    <DateDisplay
      date={date}
      formatStr="dd-MMM-yyyy HH:mm"
      showTime={false}
      className={cn('text-sm', className)}
    />
  );
}

/**
 * Relative time display (e.g., "2 hours ago")
 */
export function RelativeTime({
  date,
  className,
}: {
  date: string | Date | null | undefined;
  className?: string;
}) {
  const parsedDate = parseDate(date);

  if (!parsedDate) {
    return <span className={cn('text-muted-foreground', className)}>-</span>;
  }

  return (
    <span
      className={cn('text-muted-foreground', className)}
      title={format(parsedDate, 'PPpp')}
    >
      {formatDistanceToNow(parsedDate, { addSuffix: true })}
    </span>
  );
}
