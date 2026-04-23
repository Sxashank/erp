/**
 * EmptyState — renders when a list has zero items. See CLAUDE.md §9.8.
 */

import { Inbox, type LucideIcon } from 'lucide-react';

import { cn } from '@/lib/utils';

export interface EmptyStateProps {
  title: string;
  subtitle?: string;
  icon?: LucideIcon;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  title,
  subtitle,
  icon: Icon = Inbox,
  action,
  className,
}: EmptyStateProps): JSX.Element {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-lg border border-dashed border-muted-foreground/30 bg-muted/10 py-12 text-center',
        className,
      )}
      role="status"
    >
      <Icon className="h-12 w-12 text-muted-foreground/60" aria-hidden="true" />
      <h3 className="mt-4 text-base font-semibold">{title}</h3>
      {subtitle && (
        <p className="mt-1 max-w-md text-sm text-muted-foreground">{subtitle}</p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
