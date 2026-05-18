/**
 * InlineRemarks Component
 * Inline remarks input for approval actions (NO MODAL)
 */

import * as React from 'react';

import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';

export interface InlineRemarksProps {
  value: string;
  onChange: (value: string) => void;
  label?: string;
  placeholder?: string;
  required?: boolean;
  error?: string;
  maxLength?: number;
  rows?: number;
  className?: string;
  disabled?: boolean;
}

export function InlineRemarks({
  value,
  onChange,
  label = 'Remarks',
  placeholder = 'Enter your remarks...',
  required = false,
  error,
  maxLength = 1000,
  rows = 3,
  className,
  disabled = false,
}: InlineRemarksProps) {
  const charCount = value.length;
  const isOverLimit = maxLength && charCount > maxLength;

  return (
    <div className={cn('space-y-2', className)}>
      {label && (
        <Label className="text-sm font-medium">
          {label}
          {required && <span className="text-destructive ml-1">*</span>}
        </Label>
      )}
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        disabled={disabled}
        className={cn(
          'resize-none',
          error && 'border-destructive focus-visible:ring-destructive',
          isOverLimit && 'border-destructive'
        )}
      />
      <div className="flex items-center justify-between text-xs">
        {error ? (
          <span className="text-destructive">{error}</span>
        ) : (
          <span className="text-muted-foreground">{required && 'Required'}</span>
        )}
        {maxLength && (
          <span className={cn('text-muted-foreground', isOverLimit && 'text-destructive font-medium')}>
            {charCount}/{maxLength}
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * Inline remarks with action buttons
 */
export interface RemarksWithActionsProps {
  value: string;
  onChange: (value: string) => void;
  onApprove?: () => void;
  onReject?: () => void;
  onReturn?: () => void;
  isSubmitting?: boolean;
  requireRemarksForReject?: boolean;
  requireRemarksForReturn?: boolean;
  className?: string;
}

export function RemarksWithActions({
  value,
  onChange,
  onApprove,
  onReject,
  onReturn,
  isSubmitting = false,
  requireRemarksForReject = true,
  requireRemarksForReturn = true,
  className,
}: RemarksWithActionsProps) {
  const [error, setError] = React.useState<string>();

  const validateAndExecute = (action: 'approve' | 'reject' | 'return', handler?: () => void) => {
    if (!handler) return;

    const requiresRemarks =
      (action === 'reject' && requireRemarksForReject) ||
      (action === 'return' && requireRemarksForReturn);

    if (requiresRemarks && !value.trim()) {
      setError(`Remarks are required to ${action}`);
      return;
    }

    setError(undefined);
    handler();
  };

  return (
    <div className={cn('space-y-4', className)}>
      <InlineRemarks
        value={value}
        onChange={(v) => {
          onChange(v);
          if (error) setError(undefined);
        }}
        label="Decision Remarks"
        placeholder="Enter your remarks for this decision..."
        error={error}
        disabled={isSubmitting}
      />

      <div className="flex flex-wrap items-center gap-2">
        {onApprove && (
          <Button
            type="button"
            onClick={() => validateAndExecute('approve', onApprove)}
            disabled={isSubmitting}
            className="bg-green-600 hover:bg-green-700"
          >
            <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Approve
          </Button>
        )}

        {onReturn && (
          <Button
            type="button"
            variant="outline"
            onClick={() => validateAndExecute('return', onReturn)}
            disabled={isSubmitting}
            className="border-amber-500 text-amber-600 hover:bg-amber-50"
          >
            <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
            </svg>
            Return for Query
          </Button>
        )}

        {onReject && (
          <Button
            type="button"
            variant="outline"
            onClick={() => validateAndExecute('reject', onReject)}
            disabled={isSubmitting}
            className="border-red-500 text-red-600 hover:bg-red-50"
          >
            <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            Reject
          </Button>
        )}
      </div>
    </div>
  );
}

/**
 * Compact remarks for inline editing
 */
export function CompactRemarks({
  value,
  onChange,
  placeholder = 'Add a note...',
  className,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}) {
  const [isExpanded, setIsExpanded] = React.useState(false);

  if (!isExpanded && !value) {
    return (
      <button
        type="button"
        onClick={() => setIsExpanded(true)}
        className={cn(
          'text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1',
          className
        )}
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
        Add remarks
      </button>
    );
  }

  return (
    <div className={cn('space-y-2', className)}>
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={2}
        className="resize-none text-sm"
        autoFocus={isExpanded && !value}
        onBlur={() => {
          if (!value) setIsExpanded(false);
        }}
      />
    </div>
  );
}
