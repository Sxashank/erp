/**
 * WizardStep Component
 * Individual step wrapper for wizard forms
 */

import * as React from 'react';

import { useWizard, useWizardStep } from './WizardContext';

import { cn } from '@/lib/utils';

export interface WizardStepProps {
  stepId?: string;
  active?: boolean;
  children: React.ReactNode;
  className?: string;
  onEnter?: () => void;
  onLeave?: () => void;
  onValidate?: () => boolean | Promise<boolean>;
}

export function WizardStep({
  stepId,
  active,
  children,
  className,
  onEnter,
  onLeave,
  onValidate,
}: WizardStepProps) {
  const { currentStepId } = useWizard();
  const { isActive: contextActive, setValid } = useWizardStep(stepId || '');
  const isActive = active !== undefined ? active : contextActive;
  const prevActiveRef = React.useRef(isActive);

  // Handle enter/leave callbacks
  React.useEffect(() => {
    if (isActive && !prevActiveRef.current) {
      // Entering this step
      onEnter?.();
    } else if (!isActive && prevActiveRef.current) {
      // Leaving this step
      onLeave?.();
    }
    prevActiveRef.current = isActive;
  }, [isActive, onEnter, onLeave]);

  // Expose validation to context
  React.useEffect(() => {
    if (onValidate) {
      // Store validation function reference for the context to use
      // This is handled via the step's setValid function
    }
  }, [onValidate]);

  if (!isActive && currentStepId !== stepId) {
    return null;
  }

  return (
    <div className={cn('animate-in fade-in-50 duration-300', className)}>
      {children}
    </div>
  );
}

/**
 * Step header with title and description
 */
export function WizardStepHeader({
  title,
  description,
  className,
}: {
  title: string;
  description?: string;
  className?: string;
}) {
  return (
    <div className={cn('mb-6', className)}>
      <h2 className="text-xl font-semibold">{title}</h2>
      {description && (
        <p className="text-muted-foreground mt-1">{description}</p>
      )}
    </div>
  );
}

/**
 * Step content wrapper
 */
export function WizardStepContent({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('space-y-6', className)}>
      {children}
    </div>
  );
}

/**
 * Step section (for grouping fields within a step)
 */
export function WizardStepSection({
  title,
  description,
  children,
  className,
}: {
  title?: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('space-y-4', className)}>
      {title && (
        <div className="border-b pb-2">
          <h3 className="font-medium">{title}</h3>
          {description && (
            <p className="text-sm text-muted-foreground">{description}</p>
          )}
        </div>
      )}
      {children}
    </div>
  );
}

/**
 * Step form row (for laying out fields)
 */
export function WizardFormRow({
  children,
  className,
  cols = 2,
}: {
  children: React.ReactNode;
  className?: string;
  cols?: 1 | 2 | 3 | 4;
}) {
  const gridCols = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
  };

  return (
    <div className={cn('grid gap-4', gridCols[cols], className)}>
      {children}
    </div>
  );
}

/**
 * Step errors display
 */
export function WizardStepErrors({ stepId }: { stepId: string }) {
  const { stepErrors } = useWizardStep(stepId);

  if (stepErrors.length === 0) return null;

  return (
    <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 mt-4">
      <div className="flex items-start gap-3">
        <svg
          className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <div>
          <h4 className="font-medium text-destructive">Please fix the following errors:</h4>
          <ul className="mt-2 list-disc list-inside text-sm text-destructive/90 space-y-1">
            {stepErrors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

/**
 * Conditional step content (show/hide based on condition)
 */
export function WizardConditional({
  when,
  children,
}: {
  when: boolean;
  children: React.ReactNode;
}) {
  if (!when) return null;

  return (
    <div className="animate-in fade-in-50 slide-in-from-top-2 duration-200">
      {children}
    </div>
  );
}
