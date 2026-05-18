/**
 * WizardProgress Component
 * Step indicator sidebar for multi-step wizards
 */

import { useWizard, type WizardStep } from './WizardContext';

import { cn } from '@/lib/utils';

export interface WizardProgressProps {
  className?: string;
  variant?: 'sidebar' | 'horizontal' | 'minimal';
  showStepNumbers?: boolean;
  allowNavigation?: boolean;
}

export function WizardProgress({
  className,
  variant = 'sidebar',
  showStepNumbers = true,
  allowNavigation = true,
}: WizardProgressProps) {
  const { steps, currentStepIndex, goToStep, isSubmitting } = useWizard();

  if (variant === 'horizontal') {
    return (
      <HorizontalProgress
        steps={steps}
        currentStepIndex={currentStepIndex}
        onStepClick={allowNavigation && !isSubmitting ? goToStep : undefined}
        showStepNumbers={showStepNumbers}
        className={className}
      />
    );
  }

  if (variant === 'minimal') {
    return (
      <MinimalProgress
        steps={steps}
        currentStepIndex={currentStepIndex}
        className={className}
      />
    );
  }

  // Sidebar variant (default)
  return (
    <SidebarProgress
      steps={steps}
      currentStepIndex={currentStepIndex}
      onStepClick={allowNavigation && !isSubmitting ? goToStep : undefined}
      showStepNumbers={showStepNumbers}
      className={className}
    />
  );
}

// Sidebar variant
function SidebarProgress({
  steps,
  currentStepIndex,
  onStepClick,
  showStepNumbers,
  className,
}: {
  steps: WizardStep[];
  currentStepIndex: number;
  onStepClick?: (index: number) => void;
  showStepNumbers: boolean;
  className?: string;
}) {
  return (
    <nav className={cn('w-64 flex-shrink-0', className)} aria-label="Progress">
      <ol className="space-y-1">
        {steps.map((step, index) => {
          const isCompleted = step.isCompleted || index < currentStepIndex;
          const isCurrent = index === currentStepIndex;
          const canNavigate = onStepClick && (isCompleted || isCurrent);

          return (
            <li key={step.id}>
              <button
                type="button"
                onClick={() => canNavigate && onStepClick?.(index)}
                disabled={!canNavigate}
                className={cn(
                  'w-full flex items-start gap-3 p-3 rounded-lg text-left transition-colors',
                  isCurrent && 'bg-primary/10 border border-primary',
                  !isCurrent && isCompleted && 'hover:bg-muted',
                  !isCurrent && !isCompleted && 'opacity-60',
                  canNavigate && 'cursor-pointer',
                  !canNavigate && 'cursor-default'
                )}
              >
                {/* Step indicator */}
                <div
                  className={cn(
                    'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
                    isCurrent && 'bg-primary text-primary-foreground',
                    isCompleted && !isCurrent && 'bg-green-500 text-white',
                    !isCompleted && !isCurrent && 'bg-muted text-muted-foreground'
                  )}
                >
                  {isCompleted && !isCurrent ? (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : showStepNumbers ? (
                    index + 1
                  ) : (
                    <div className="w-2 h-2 rounded-full bg-current" />
                  )}
                </div>

                {/* Step content */}
                <div className="flex-1 min-w-0">
                  <p
                    className={cn(
                      'text-sm font-medium',
                      isCurrent && 'text-primary',
                      !isCurrent && 'text-foreground'
                    )}
                  >
                    {step.title}
                    {step.isOptional && (
                      <span className="ml-1 text-xs text-muted-foreground">(Optional)</span>
                    )}
                  </p>
                  {step.description && (
                    <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                      {step.description}
                    </p>
                  )}
                </div>
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

// Horizontal variant
function HorizontalProgress({
  steps,
  currentStepIndex,
  onStepClick,
  showStepNumbers,
  className,
}: {
  steps: WizardStep[];
  currentStepIndex: number;
  onStepClick?: (index: number) => void;
  showStepNumbers: boolean;
  className?: string;
}) {
  return (
    <nav className={cn('w-full', className)} aria-label="Progress">
      <ol className="flex items-center">
        {steps.map((step, index) => {
          const isCompleted = step.isCompleted || index < currentStepIndex;
          const isCurrent = index === currentStepIndex;
          const canNavigate = onStepClick && (isCompleted || isCurrent);
          const isLast = index === steps.length - 1;

          return (
            <li key={step.id} className={cn('flex items-center', !isLast && 'flex-1')}>
              <button
                type="button"
                onClick={() => canNavigate && onStepClick?.(index)}
                disabled={!canNavigate}
                className={cn(
                  'flex flex-col items-center',
                  canNavigate && 'cursor-pointer',
                  !canNavigate && 'cursor-default'
                )}
              >
                <div
                  className={cn(
                    'w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium border-2',
                    isCurrent && 'border-primary bg-primary text-primary-foreground',
                    isCompleted && !isCurrent && 'border-green-500 bg-green-500 text-white',
                    !isCompleted && !isCurrent && 'border-muted bg-background text-muted-foreground'
                  )}
                >
                  {isCompleted && !isCurrent ? (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : showStepNumbers ? (
                    index + 1
                  ) : null}
                </div>
                <span
                  className={cn(
                    'mt-2 text-xs font-medium text-center',
                    isCurrent && 'text-primary',
                    !isCurrent && 'text-muted-foreground'
                  )}
                >
                  {step.title}
                </span>
              </button>

              {/* Connector line */}
              {!isLast && (
                <div
                  className={cn(
                    'flex-1 h-0.5 mx-4',
                    isCompleted ? 'bg-green-500' : 'bg-muted'
                  )}
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

// Minimal variant (just dots)
function MinimalProgress({
  steps,
  currentStepIndex,
  className,
}: {
  steps: WizardStep[];
  currentStepIndex: number;
  className?: string;
}) {
  return (
    <div className={cn('flex items-center justify-center gap-2', className)}>
      {steps.map((step, index) => {
        const isCompleted = step.isCompleted || index < currentStepIndex;
        const isCurrent = index === currentStepIndex;

        return (
          <div
            key={step.id}
            className={cn(
              'w-2.5 h-2.5 rounded-full transition-colors',
              isCurrent && 'bg-primary scale-125',
              isCompleted && !isCurrent && 'bg-green-500',
              !isCompleted && !isCurrent && 'bg-muted'
            )}
            title={step.title}
          />
        );
      })}
    </div>
  );
}

/**
 * Progress bar variant
 */
export function WizardProgressBar({ className }: { className?: string }) {
  const { progress } = useWizard();

  return (
    <div className={cn('w-full', className)}>
      <div className="flex items-center justify-between text-sm mb-2">
        <span className="text-muted-foreground">Progress</span>
        <span className="font-medium">{progress}%</span>
      </div>
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div
          className="h-full bg-primary transition-all duration-300 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
