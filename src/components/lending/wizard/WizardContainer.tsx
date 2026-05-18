/**
 * WizardContainer Component
 * Main wizard wrapper with layout and keyboard navigation
 */

import * as React from 'react';

import { WizardProvider, type WizardStep } from './WizardContext';
import { WizardNavigation, type WizardNavigationProps } from './WizardNavigation';
import { WizardProgress, WizardProgressBar } from './WizardProgress';

import { Card, CardContent } from '@/components/ui/card';
import { logger } from '@/lib/logger';
import { cn } from '@/lib/utils';

export interface WizardContainerProps extends Omit<WizardNavigationProps, 'className'> {
  steps: WizardStep[];
  children: React.ReactNode;
  initialData?: Record<string, unknown>;
  title?: string;
  description?: string;
  className?: string;
  layout?: 'sidebar' | 'horizontal' | 'minimal';
  showProgress?: boolean;
  showKeyboardHint?: boolean;
  onStepChange?: (stepIndex: number, stepId: string) => void;
  onDataChange?: (data: Record<string, unknown>) => void;
}

export function WizardContainer({
  steps,
  children,
  initialData,
  title,
  description,
  className,
  layout = 'sidebar',
  showProgress = true,
  showKeyboardHint = true,
  onStepChange,
  onDataChange,
  ...navigationProps
}: WizardContainerProps) {
  return (
    <WizardProvider
      steps={steps}
      initialData={initialData}
      onStepChange={onStepChange}
      onDataChange={onDataChange}
    >
      <WizardLayout
        title={title}
        description={description}
        className={className}
        layout={layout}
        showProgress={showProgress}
        showKeyboardHint={showKeyboardHint}
        navigationProps={navigationProps}
      >
        {children}
      </WizardLayout>
    </WizardProvider>
  );
}

function WizardLayout({
  children,
  title,
  description,
  className,
  layout,
  showProgress,
  showKeyboardHint,
  navigationProps,
}: {
  children: React.ReactNode;
  title?: string;
  description?: string;
  className?: string;
  layout: 'sidebar' | 'horizontal' | 'minimal';
  showProgress: boolean;
  showKeyboardHint: boolean;
  navigationProps: Omit<WizardNavigationProps, 'className'>;
}) {
  // Keyboard navigation
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'Enter') {
        // Trigger next button click
        const nextButton = document.querySelector('[data-wizard-next]') as HTMLButtonElement;
        if (nextButton && !nextButton.disabled) {
          nextButton.click();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  if (layout === 'sidebar') {
    return (
      <div className={cn('flex gap-6', className)}>
        {/* Sidebar with steps */}
        <div className="w-64 flex-shrink-0">
          {title && (
            <div className="mb-6">
              <h1 className="text-xl font-semibold">{title}</h1>
              {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
            </div>
          )}
          {showProgress && <WizardProgress variant="sidebar" className="sticky top-6" />}
        </div>

        {/* Main content */}
        <Card className="flex-1">
          <CardContent className="p-6">
            {children}
            <WizardNavigation {...navigationProps} />
            {showKeyboardHint && (
              <p className="mt-4 text-center text-xs text-muted-foreground">
                Press <kbd className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">Ctrl</kbd> +{' '}
                <kbd className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">Enter</kbd> to
                proceed
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (layout === 'horizontal') {
    return (
      <div className={cn('space-y-6', className)}>
        {/* Header */}
        {title && (
          <div className="text-center">
            <h1 className="text-xl font-semibold">{title}</h1>
            {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
          </div>
        )}

        {/* Horizontal progress */}
        {showProgress && <WizardProgress variant="horizontal" />}

        {/* Content */}
        <Card>
          <CardContent className="p-6">
            {children}
            <WizardNavigation {...navigationProps} />
          </CardContent>
        </Card>
      </div>
    );
  }

  // Minimal layout
  return (
    <div className={cn('space-y-4', className)}>
      {/* Header with inline progress */}
      <div className="flex items-center justify-between">
        <div>
          {title && <h1 className="text-lg font-semibold">{title}</h1>}
          {description && <p className="text-sm text-muted-foreground">{description}</p>}
        </div>
        {showProgress && <WizardProgress variant="minimal" />}
      </div>

      {/* Progress bar */}
      {showProgress && <WizardProgressBar />}

      {/* Content */}
      <Card>
        <CardContent className="p-6">
          {children}
          <WizardNavigation {...navigationProps} />
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Wizard with draft persistence to localStorage
 */
export function WizardWithDraft({
  storageKey,
  ...props
}: WizardContainerProps & { storageKey: string }) {
  const [initialData, setInitialData] = React.useState<Record<string, unknown> | undefined>();
  const [isLoaded, setIsLoaded] = React.useState(false);

  // Load draft from localStorage
  React.useEffect(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        setInitialData(JSON.parse(saved));
      }
    } catch (error) {
      logger.error('Failed to load draft:', error);
    }
    setIsLoaded(true);
  }, [storageKey]);

  // Save draft handler
  const handleSaveDraft = React.useCallback(
    async (data: Record<string, unknown>) => {
      await props.onSaveDraft?.(data);
      alert('Draft saved successfully!');
    },
    [props.onSaveDraft],
  );

  // Save to localStorage on data change
  const handleDataChange = React.useCallback(
    (data: Record<string, unknown>) => {
      try {
        localStorage.setItem(storageKey, JSON.stringify(data));
      } catch (error) {
        logger.error('Failed to save draft:', error);
      }
      props.onDataChange?.(data);
    },
    [storageKey, props.onDataChange],
  );

  // Clear draft on successful submit
  const handleSubmit = React.useCallback(
    async (data: Record<string, unknown>) => {
      await props.onSubmit?.(data);
      localStorage.removeItem(storageKey);
    },
    [storageKey, props.onSubmit],
  );

  if (!isLoaded) {
    return (
      <div className="flex items-center justify-center p-12">
        <svg className="h-6 w-6 animate-spin text-muted-foreground" fill="none" viewBox="0 0 24 24">
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
      </div>
    );
  }

  return (
    <WizardContainer
      {...props}
      initialData={initialData || props.initialData}
      onDataChange={handleDataChange}
      onSaveDraft={handleSaveDraft}
      onSubmit={handleSubmit}
    />
  );
}
