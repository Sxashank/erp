/**
 * AuditTimeline Component
 * Displays audit trail / activity history
 */

import { format, parseISO } from 'date-fns';

import { cn } from '@/lib/utils';

export interface AuditEntry {
  id: string;
  action: string;
  description?: string;
  user_name?: string;
  user_id?: string;
  timestamp: string;
  old_value?: string;
  new_value?: string;
  metadata?: Record<string, unknown>;
}

export interface AuditTimelineProps {
  entries: AuditEntry[];
  className?: string;
  maxHeight?: string;
  showValues?: boolean;
}

const actionColors: Record<string, string> = {
  CREATE: 'bg-green-500',
  UPDATE: 'bg-blue-500',
  DELETE: 'bg-red-500',
  APPROVE: 'bg-emerald-500',
  REJECT: 'bg-red-500',
  SUBMIT: 'bg-purple-500',
  RETURN: 'bg-amber-500',
  STATUS_CHANGE: 'bg-indigo-500',
  COMMENT: 'bg-slate-500',
  DEFAULT: 'bg-slate-400',
};

function getActionColor(action: string): string {
  const upperAction = action.toUpperCase();
  for (const [key, color] of Object.entries(actionColors)) {
    if (upperAction.includes(key)) return color;
  }
  return actionColors.DEFAULT;
}

export function AuditTimeline({
  entries,
  className,
  maxHeight = '400px',
  showValues = false,
}: AuditTimelineProps) {
  if (!entries || entries.length === 0) {
    return (
      <div className={cn('text-center py-8 text-muted-foreground', className)}>
        No activity recorded
      </div>
    );
  }

  return (
    <div
      className={cn('overflow-y-auto', className)}
      style={{ maxHeight }}
    >
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-3 top-2 bottom-2 w-0.5 bg-border" />

        <div className="space-y-4">
          {entries.map((entry, index) => (
            <div key={entry.id} className="relative flex gap-4 pb-4">
              {/* Timeline dot */}
              <div
                className={cn(
                  'relative z-10 w-6 h-6 rounded-full flex items-center justify-center',
                  getActionColor(entry.action)
                )}
              >
                {getActionIcon(entry.action)}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0 pt-0.5">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-medium text-sm">
                      {formatAction(entry.action)}
                    </p>
                    {entry.description && (
                      <p className="text-sm text-muted-foreground mt-0.5">
                        {entry.description}
                      </p>
                    )}
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-xs text-muted-foreground">
                      {formatTimestamp(entry.timestamp)}
                    </p>
                    {entry.user_name && (
                      <p className="text-xs text-muted-foreground mt-0.5">
                        by {entry.user_name}
                      </p>
                    )}
                  </div>
                </div>

                {/* Value changes */}
                {showValues && (entry.old_value || entry.new_value) && (
                  <div className="mt-2 p-2 bg-muted rounded-md text-xs font-mono">
                    {entry.old_value && (
                      <div className="text-red-600">
                        - {entry.old_value}
                      </div>
                    )}
                    {entry.new_value && (
                      <div className="text-green-600">
                        + {entry.new_value}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * Compact audit log for inline display
 */
export function AuditLogCompact({
  entries,
  limit = 3,
  className,
}: {
  entries: AuditEntry[];
  limit?: number;
  className?: string;
}) {
  const displayEntries = entries.slice(0, limit);
  const remaining = entries.length - limit;

  return (
    <div className={cn('space-y-2', className)}>
      {displayEntries.map((entry) => (
        <div key={entry.id} className="flex items-center gap-2 text-sm">
          <div className={cn('w-2 h-2 rounded-full', getActionColor(entry.action))} />
          <span className="flex-1 truncate">{entry.description || formatAction(entry.action)}</span>
          <span className="text-xs text-muted-foreground">{formatTimestamp(entry.timestamp, true)}</span>
        </div>
      ))}
      {remaining > 0 && (
        <p className="text-xs text-muted-foreground">+{remaining} more</p>
      )}
    </div>
  );
}

/**
 * Single audit entry display
 */
export function AuditEntry({
  entry,
  className,
}: {
  entry: AuditEntry;
  className?: string;
}) {
  return (
    <div className={cn('flex items-start gap-3 p-3 bg-muted/50 rounded-lg', className)}>
      <div className={cn('w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0', getActionColor(entry.action))}>
        {getActionIcon(entry.action)}
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium">{formatAction(entry.action)}</p>
        {entry.description && (
          <p className="text-sm text-muted-foreground">{entry.description}</p>
        )}
        <p className="text-xs text-muted-foreground mt-1">
          {entry.user_name && `${entry.user_name} · `}
          {formatTimestamp(entry.timestamp)}
        </p>
      </div>
    </div>
  );
}

// Helper functions
function formatAction(action: string): string {
  return action
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatTimestamp(timestamp: string, short = false): string {
  try {
    const date = parseISO(timestamp);
    return short
      ? format(date, 'dd MMM HH:mm')
      : format(date, 'dd MMM yyyy, HH:mm');
  } catch {
    return timestamp;
  }
}

function getActionIcon(action: string) {
  const upperAction = action.toUpperCase();

  // Return simple colored SVG icons
  if (upperAction.includes('CREATE')) {
    return (
      <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
      </svg>
    );
  }
  if (upperAction.includes('APPROVE')) {
    return (
      <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    );
  }
  if (upperAction.includes('REJECT') || upperAction.includes('DELETE')) {
    return (
      <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    );
  }

  // Default dot
  return <div className="w-2 h-2 bg-white rounded-full" />;
}
