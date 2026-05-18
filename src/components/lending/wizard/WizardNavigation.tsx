/**
 * WizardNavigation Component
 * Navigation buttons for wizard (Next, Previous, Save Draft, Submit)
 */

import * as React from 'react';

import { useWizard } from './WizardContext';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export type WizardSubmitHandler = (data: Record<string, unknown>) => void | Promise<void>;

export interface WizardNavigationProps {
  className?: string;
  onSaveDraft?: WizardSubmitHandler;
  onSubmit?: WizardSubmitHandler;
  onCancel?: () => void;
  showSaveDraft?: boolean;
  showCancel?: boolean;
  nextLabel?: string;
  previousLabel?: string;
  submitLabel?: string;
  saveDraftLabel?: string;
  cancelLabel?: string;
  validateBeforeNext?: () => boolean | Promise<boolean>;
}

export function WizardNavigation({
  className,
  onSaveDraft,
  onSubmit,
  onCancel,
  showSaveDraft = true,
  showCancel = false,
  nextLabel = 'Next',
  previousLabel = 'Previous',
  submitLabel = 'Submit',
  saveDraftLabel = 'Save Draft',
  cancelLabel = 'Cancel',
  validateBeforeNext,
}: WizardNavigationProps) {
  const {
    nextStep,
    previousStep,
    isFirstStep,
    isLastStep,
    canGoNext,
    canGoPrevious,
    isSubmitting,
    isDirty,
    setSubmitting,
    data,
  } = useWizard();

  const [isSaving, setIsSaving] = React.useState(false);

  const handleNext = async () => {
    if (validateBeforeNext) {
      const isValid = await validateBeforeNext();
      if (!isValid) return;
    }
    nextStep();
  };

  const handlePrevious = () => {
    previousStep();
  };

  const handleSaveDraft = async () => {
    if (!onSaveDraft) return;

    setIsSaving(true);
    try {
      await onSaveDraft(data);
    } finally {
      setIsSaving(false);
    }
  };

  const handleSubmit = async () => {
    if (!onSubmit) return;

    if (validateBeforeNext) {
      const isValid = await validateBeforeNext();
      if (!isValid) return;
    }

    setSubmitting(true);
    try {
      await onSubmit(data);
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = () => {
    if (isDirty) {
      const confirmed = window.confirm(
        'You have unsaved changes. Are you sure you want to cancel?',
      );
      if (!confirmed) return;
    }
    onCancel?.();
  };

  return (
    <div className={cn('flex items-center justify-between border-t pt-6', className)}>
      {/* Left side: Cancel and Save Draft */}
      <div className="flex items-center gap-2">
        {showCancel && onCancel && (
          <Button type="button" variant="ghost" onClick={handleCancel} disabled={isSubmitting}>
            {cancelLabel}
          </Button>
        )}
        {showSaveDraft && onSaveDraft && (
          <Button
            type="button"
            variant="outline"
            onClick={handleSaveDraft}
            disabled={isSaving || isSubmitting || !isDirty}
          >
            {isSaving ? (
              <>
                <svg className="-ml-1 mr-2 h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Saving...
              </>
            ) : (
              saveDraftLabel
            )}
          </Button>
        )}
      </div>

      {/* Right side: Navigation */}
      <div className="flex items-center gap-2">
        {!isFirstStep && (
          <Button
            type="button"
            variant="outline"
            onClick={handlePrevious}
            disabled={!canGoPrevious}
          >
            <svg className="mr-1 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
            {previousLabel}
          </Button>
        )}

        {isLastStep ? (
          <Button type="button" onClick={handleSubmit} disabled={isSubmitting || !canGoNext}>
            {isSubmitting ? (
              <>
                <svg className="-ml-1 mr-2 h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Submitting...
              </>
            ) : (
              <>
                {submitLabel}
                <svg className="ml-1 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </>
            )}
          </Button>
        ) : (
          <Button type="button" onClick={handleNext} disabled={!canGoNext}>
            {nextLabel}
            <svg className="ml-1 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Button>
        )}
      </div>
    </div>
  );
}

/**
 * Compact navigation for narrow layouts
 */
export function WizardNavigationCompact({
  className,
  onSubmit,
  validateBeforeNext,
}: {
  className?: string;
  onSubmit?: WizardSubmitHandler;
  validateBeforeNext?: () => boolean | Promise<boolean>;
}) {
  const {
    nextStep,
    previousStep,
    isFirstStep,
    isLastStep,
    canGoNext,
    canGoPrevious,
    isSubmitting,
    setSubmitting,
    currentStepIndex,
    steps,
    data,
  } = useWizard();

  const handleNext = async () => {
    if (validateBeforeNext) {
      const isValid = await validateBeforeNext();
      if (!isValid) return;
    }

    if (isLastStep && onSubmit) {
      setSubmitting(true);
      try {
        await onSubmit(data);
      } finally {
        setSubmitting(false);
      }
    } else {
      nextStep();
    }
  };

  return (
    <div className={cn('flex items-center justify-between', className)}>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={previousStep}
        disabled={!canGoPrevious}
        className="gap-1"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back
      </Button>

      <span className="text-sm text-muted-foreground">
        Step {currentStepIndex + 1} of {steps.length}
      </span>

      <Button
        type="button"
        size="sm"
        onClick={handleNext}
        disabled={!canGoNext || isSubmitting}
        className="gap-1"
      >
        {isLastStep ? 'Submit' : 'Next'}
        {!isLastStep && (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        )}
      </Button>
    </div>
  );
}

/**
 * Keyboard shortcut hint
 */
export function WizardKeyboardHint({ className }: { className?: string }) {
  return (
    <p className={cn('text-center text-xs text-muted-foreground', className)}>
      Press <kbd className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">Ctrl</kbd> +{' '}
      <kbd className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">Enter</kbd> to proceed
    </p>
  );
}
