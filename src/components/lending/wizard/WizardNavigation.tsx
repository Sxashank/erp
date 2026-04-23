/**
 * WizardNavigation Component
 * Navigation buttons for wizard (Next, Previous, Save Draft, Submit)
 */

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { useWizard } from './WizardContext';

export interface WizardNavigationProps {
  className?: string;
  onSaveDraft?: () => void | Promise<void>;
  onSubmit?: () => void | Promise<void>;
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
      await onSaveDraft();
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
      await onSubmit();
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = () => {
    if (isDirty) {
      const confirmed = window.confirm('You have unsaved changes. Are you sure you want to cancel?');
      if (!confirmed) return;
    }
    onCancel?.();
  };

  return (
    <div className={cn('flex items-center justify-between pt-6 border-t', className)}>
      {/* Left side: Cancel and Save Draft */}
      <div className="flex items-center gap-2">
        {showCancel && onCancel && (
          <Button
            type="button"
            variant="ghost"
            onClick={handleCancel}
            disabled={isSubmitting}
          >
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
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
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
            <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            {previousLabel}
          </Button>
        )}

        {isLastStep ? (
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitting || !canGoNext}
          >
            {isSubmitting ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Submitting...
              </>
            ) : (
              <>
                {submitLabel}
                <svg className="w-4 h-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </>
            )}
          </Button>
        ) : (
          <Button
            type="button"
            onClick={handleNext}
            disabled={!canGoNext}
          >
            {nextLabel}
            <svg className="w-4 h-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
  onSubmit?: () => void | Promise<void>;
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
  } = useWizard();

  const handleNext = async () => {
    if (validateBeforeNext) {
      const isValid = await validateBeforeNext();
      if (!isValid) return;
    }

    if (isLastStep && onSubmit) {
      setSubmitting(true);
      try {
        await onSubmit();
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
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
    <p className={cn('text-xs text-muted-foreground text-center', className)}>
      Press <kbd className="px-1.5 py-0.5 bg-muted rounded text-xs font-mono">Ctrl</kbd> +{' '}
      <kbd className="px-1.5 py-0.5 bg-muted rounded text-xs font-mono">Enter</kbd> to proceed
    </p>
  );
}
