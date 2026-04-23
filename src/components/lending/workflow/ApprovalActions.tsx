/**
 * ApprovalActions Component
 * Workflow approval action buttons with inline remarks
 */

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { InlineRemarks } from './InlineRemarks';

export interface ApprovalActionsProps {
  title?: string;
  currentStatus?: string;
  pendingWith?: string;
  slaHours?: number;
  slaExpiresAt?: string;
  onApprove?: (remarks: string) => void | Promise<void>;
  onReject?: (remarks: string) => void | Promise<void>;
  onReturn?: (remarks: string) => void | Promise<void>;
  onDelegate?: (remarks: string) => void | Promise<void>;
  onEscalate?: (remarks: string) => void | Promise<void>;
  requireRemarksForApprove?: boolean;
  requireRemarksForReject?: boolean;
  requireRemarksForReturn?: boolean;
  className?: string;
  disabled?: boolean;
}

export function ApprovalActions({
  title = 'Approval Decision',
  currentStatus,
  pendingWith,
  slaHours,
  slaExpiresAt,
  onApprove,
  onReject,
  onReturn,
  onDelegate,
  onEscalate,
  requireRemarksForApprove = false,
  requireRemarksForReject = true,
  requireRemarksForReturn = true,
  className,
  disabled = false,
}: ApprovalActionsProps) {
  const [remarks, setRemarks] = React.useState('');
  const [selectedAction, setSelectedAction] = React.useState<'approve' | 'reject' | 'return' | 'delegate' | 'escalate' | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string>();

  const requiresRemarks = (action: string): boolean => {
    switch (action) {
      case 'approve':
        return requireRemarksForApprove;
      case 'reject':
        return requireRemarksForReject;
      case 'return':
        return requireRemarksForReturn;
      default:
        return false;
    }
  };

  const handleSubmit = async () => {
    if (!selectedAction) return;

    if (requiresRemarks(selectedAction) && !remarks.trim()) {
      setError(`Remarks are required to ${selectedAction}`);
      return;
    }

    setError(undefined);
    setIsSubmitting(true);

    try {
      switch (selectedAction) {
        case 'approve':
          await onApprove?.(remarks);
          break;
        case 'reject':
          await onReject?.(remarks);
          break;
        case 'return':
          await onReturn?.(remarks);
          break;
        case 'delegate':
          await onDelegate?.(remarks);
          break;
        case 'escalate':
          await onEscalate?.(remarks);
          break;
      }
      setRemarks('');
      setSelectedAction(null);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getActionLabel = () => {
    switch (selectedAction) {
      case 'approve':
        return 'Approve';
      case 'reject':
        return 'Reject';
      case 'return':
        return 'Return';
      case 'delegate':
        return 'Delegate';
      case 'escalate':
        return 'Escalate';
      default:
        return 'Submit';
    }
  };

  return (
    <Card className={cn('border-2', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{title}</CardTitle>
          {currentStatus && (
            <Badge variant="outline">{currentStatus}</Badge>
          )}
        </div>
        {(pendingWith || slaHours) && (
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            {pendingWith && <span>Pending with: <strong>{pendingWith}</strong></span>}
            {slaHours && <span>SLA: {slaHours}h</span>}
          </div>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Action buttons */}
        <div className="flex flex-wrap gap-2">
          {onApprove && (
            <Button
              type="button"
              size="sm"
              onClick={() => setSelectedAction('approve')}
              disabled={disabled || isSubmitting}
              className={cn(
                'gap-1.5',
                selectedAction === 'approve'
                  ? 'bg-green-600 hover:bg-green-700'
                  : 'bg-green-100 text-green-700 hover:bg-green-200'
              )}
              variant={selectedAction === 'approve' ? 'default' : 'outline'}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Approve
            </Button>
          )}

          {onReturn && (
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => setSelectedAction('return')}
              disabled={disabled || isSubmitting}
              className={cn(
                'gap-1.5',
                selectedAction === 'return' && 'border-amber-500 bg-amber-50'
              )}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
              </svg>
              Return
            </Button>
          )}

          {onReject && (
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => setSelectedAction('reject')}
              disabled={disabled || isSubmitting}
              className={cn(
                'gap-1.5',
                selectedAction === 'reject' && 'border-red-500 bg-red-50 text-red-600'
              )}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              Reject
            </Button>
          )}

          {onDelegate && (
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => setSelectedAction('delegate')}
              disabled={disabled || isSubmitting}
              className="gap-1.5"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              Delegate
            </Button>
          )}

          {onEscalate && (
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => setSelectedAction('escalate')}
              disabled={disabled || isSubmitting}
              className="gap-1.5"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
              </svg>
              Escalate
            </Button>
          )}
        </div>

        {/* Remarks section (shown when action selected) */}
        {selectedAction && (
          <div className="space-y-4 animate-in fade-in-50 slide-in-from-top-2 duration-200">
            <InlineRemarks
              value={remarks}
              onChange={(v) => {
                setRemarks(v);
                if (error) setError(undefined);
              }}
              label={`Remarks for ${getActionLabel()}`}
              placeholder={`Enter your remarks for ${selectedAction}...`}
              required={requiresRemarks(selectedAction)}
              error={error}
              disabled={isSubmitting}
            />

            <div className="flex items-center gap-2">
              <Button
                type="button"
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="gap-1.5"
              >
                {isSubmitting ? (
                  <>
                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Submitting...
                  </>
                ) : (
                  <>Submit {getActionLabel()}</>
                )}
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  setSelectedAction(null);
                  setRemarks('');
                  setError(undefined);
                }}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Compact approval buttons (for toolbar)
 */
export function ApprovalButtonGroup({
  onApprove,
  onReject,
  onReturn,
  disabled,
  className,
}: {
  onApprove?: () => void;
  onReject?: () => void;
  onReturn?: () => void;
  disabled?: boolean;
  className?: string;
}) {
  return (
    <div className={cn('flex items-center gap-1', className)}>
      {onApprove && (
        <Button
          size="sm"
          onClick={onApprove}
          disabled={disabled}
          className="bg-green-600 hover:bg-green-700"
        >
          Approve
        </Button>
      )}
      {onReturn && (
        <Button
          size="sm"
          variant="outline"
          onClick={onReturn}
          disabled={disabled}
        >
          Return
        </Button>
      )}
      {onReject && (
        <Button
          size="sm"
          variant="outline"
          onClick={onReject}
          disabled={disabled}
          className="text-red-600 border-red-300 hover:bg-red-50"
        >
          Reject
        </Button>
      )}
    </div>
  );
}
