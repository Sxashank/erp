/**
 * ErrorState — renders when a fetch fails. Provides a real retry. See CLAUDE.md §9.8.
 */

import { AlertTriangle, RefreshCw } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { getCorrelationId, getErrorCode, getErrorMessage } from '@/lib/errorMessage';
import { cn } from '@/lib/utils';

export interface ErrorStateProps {
  title?: string;
  error?: unknown;
  onRetry?: () => void;
  className?: string;
}

function describe(error: unknown): { message: string; code?: string; correlationId?: string } {
  return {
    message: getErrorMessage(error),
    code: getErrorCode(error),
    correlationId: getCorrelationId(error),
  };
}

export function ErrorState({
  title = 'Unable to load data',
  error,
  onRetry,
  className,
}: ErrorStateProps): JSX.Element {
  const { message, code, correlationId } = describe(error);
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-lg border border-destructive/30 bg-destructive/5 py-12 text-center',
        className,
      )}
      role="alert"
    >
      <AlertTriangle className="h-12 w-12 text-destructive/80" aria-hidden="true" />
      <h3 className="mt-4 text-base font-semibold">{title}</h3>
      <p className="mt-1 max-w-md text-sm text-muted-foreground">{message}</p>
      {(code || correlationId) && (
        <p className="mt-1 text-xs text-muted-foreground">
          {code && <span>code: {code}</span>}
          {code && correlationId && <span> · </span>}
          {correlationId && <span>id: {correlationId}</span>}
        </p>
      )}
      {onRetry && (
        <Button variant="outline" size="sm" className="mt-5" onClick={onRetry}>
          <RefreshCw className="mr-2 h-4 w-4" aria-hidden="true" />
          Retry
        </Button>
      )}
    </div>
  );
}
