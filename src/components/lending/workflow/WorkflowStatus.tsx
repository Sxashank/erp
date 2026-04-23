/**
 * WorkflowStatus Component
 * Current workflow state and history display
 */

import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { format, parseISO } from 'date-fns';

export interface WorkflowStep {
  step_id: string;
  step_number: number;
  step_name: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'SKIPPED' | 'REJECTED';
  assigned_to?: string;
  assigned_to_name?: string;
  completed_by?: string;
  completed_by_name?: string;
  completed_at?: string;
  remarks?: string;
  action?: 'APPROVE' | 'REJECT' | 'RETURN' | 'FORWARD';
  sla_hours?: number;
  is_overdue?: boolean;
}

export interface WorkflowInstance {
  instance_id: string;
  workflow_name: string;
  entity_type: string;
  entity_id: string;
  status: 'IN_PROGRESS' | 'COMPLETED' | 'REJECTED' | 'CANCELLED';
  current_step?: number;
  initiated_by?: string;
  initiated_at: string;
  completed_at?: string;
  steps: WorkflowStep[];
}

export interface WorkflowStatusProps {
  workflow: WorkflowInstance;
  className?: string;
  variant?: 'default' | 'compact' | 'detailed';
}

const statusColors = {
  IN_PROGRESS: 'bg-blue-100 text-blue-700 border-blue-300',
  COMPLETED: 'bg-green-100 text-green-700 border-green-300',
  REJECTED: 'bg-red-100 text-red-700 border-red-300',
  CANCELLED: 'bg-slate-100 text-slate-600 border-slate-300',
};

const stepStatusColors = {
  PENDING: 'bg-slate-100 text-slate-600',
  IN_PROGRESS: 'bg-blue-100 text-blue-700',
  COMPLETED: 'bg-green-100 text-green-700',
  SKIPPED: 'bg-slate-100 text-slate-500',
  REJECTED: 'bg-red-100 text-red-700',
};

export function WorkflowStatus({
  workflow,
  className,
  variant = 'default',
}: WorkflowStatusProps) {
  if (variant === 'compact') {
    return (
      <CompactWorkflowStatus workflow={workflow} className={className} />
    );
  }

  if (variant === 'detailed') {
    return (
      <DetailedWorkflowStatus workflow={workflow} className={className} />
    );
  }

  return (
    <DefaultWorkflowStatus workflow={workflow} className={className} />
  );
}

function DefaultWorkflowStatus({
  workflow,
  className,
}: {
  workflow: WorkflowInstance;
  className?: string;
}) {
  const currentStep = workflow.steps.find(
    (s) => s.status === 'IN_PROGRESS' || s.status === 'PENDING'
  );

  return (
    <Card className={cn('', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Workflow Status</CardTitle>
          <Badge variant="outline" className={cn('font-medium', statusColors[workflow.status])}>
            {workflow.status.replace('_', ' ')}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current step info */}
        {currentStep && (
          <div className="p-3 bg-primary/5 rounded-lg border border-primary/20">
            <p className="text-sm text-muted-foreground">Currently at</p>
            <p className="font-medium">{currentStep.step_name}</p>
            {currentStep.assigned_to_name && (
              <p className="text-sm text-muted-foreground mt-1">
                Pending with: <span className="text-foreground">{currentStep.assigned_to_name}</span>
              </p>
            )}
            {currentStep.is_overdue && (
              <Badge variant="outline" className="mt-2 bg-red-100 text-red-700 border-red-300">
                Overdue
              </Badge>
            )}
          </div>
        )}

        {/* Steps progress */}
        <div className="space-y-2">
          {workflow.steps.map((step, index) => (
            <div
              key={step.step_id}
              className={cn(
                'flex items-center gap-3 p-2 rounded',
                step.status === 'IN_PROGRESS' && 'bg-blue-50'
              )}
            >
              <div
                className={cn(
                  'w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium',
                  stepStatusColors[step.status]
                )}
              >
                {step.status === 'COMPLETED' ? (
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : step.status === 'REJECTED' ? (
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                ) : (
                  step.step_number
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{step.step_name}</p>
                {step.completed_by_name && (
                  <p className="text-xs text-muted-foreground">
                    {step.action === 'APPROVE' ? 'Approved' : step.action === 'REJECT' ? 'Rejected' : 'Processed'} by {step.completed_by_name}
                  </p>
                )}
              </div>
              <Badge variant="outline" size="sm" className={cn('text-xs', stepStatusColors[step.status])}>
                {step.status.replace('_', ' ')}
              </Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function CompactWorkflowStatus({
  workflow,
  className,
}: {
  workflow: WorkflowInstance;
  className?: string;
}) {
  const currentStep = workflow.steps.find(
    (s) => s.status === 'IN_PROGRESS' || s.status === 'PENDING'
  );
  const completedSteps = workflow.steps.filter((s) => s.status === 'COMPLETED').length;
  const totalSteps = workflow.steps.length;

  return (
    <div className={cn('flex items-center gap-4', className)}>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-medium">
            Step {completedSteps + 1} of {totalSteps}
          </span>
          <Badge variant="outline" className={cn('text-xs', statusColors[workflow.status])}>
            {workflow.status.replace('_', ' ')}
          </Badge>
        </div>
        {currentStep && (
          <p className="text-sm text-muted-foreground">
            {currentStep.step_name}
            {currentStep.assigned_to_name && ` - ${currentStep.assigned_to_name}`}
          </p>
        )}
      </div>

      {/* Mini progress */}
      <div className="flex items-center gap-1">
        {workflow.steps.map((step) => (
          <div
            key={step.step_id}
            className={cn(
              'w-2.5 h-2.5 rounded-full',
              step.status === 'COMPLETED' && 'bg-green-500',
              step.status === 'IN_PROGRESS' && 'bg-blue-500',
              step.status === 'PENDING' && 'bg-slate-200',
              step.status === 'REJECTED' && 'bg-red-500',
              step.status === 'SKIPPED' && 'bg-slate-300'
            )}
            title={`${step.step_name}: ${step.status}`}
          />
        ))}
      </div>
    </div>
  );
}

function DetailedWorkflowStatus({
  workflow,
  className,
}: {
  workflow: WorkflowInstance;
  className?: string;
}) {
  return (
    <Card className={cn('', className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>{workflow.workflow_name}</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Started {formatDate(workflow.initiated_at)}
              {workflow.completed_at && ` · Completed ${formatDate(workflow.completed_at)}`}
            </p>
          </div>
          <Badge variant="outline" className={cn('font-medium', statusColors[workflow.status])}>
            {workflow.status.replace('_', ' ')}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {/* Timeline view */}
        <div className="relative">
          <div className="absolute left-3 top-2 bottom-2 w-0.5 bg-border" />

          <div className="space-y-4">
            {workflow.steps.map((step) => (
              <div key={step.step_id} className="relative flex gap-4">
                <div
                  className={cn(
                    'relative z-10 w-6 h-6 rounded-full flex items-center justify-center',
                    step.status === 'COMPLETED' && 'bg-green-500 text-white',
                    step.status === 'IN_PROGRESS' && 'bg-blue-500 text-white',
                    step.status === 'PENDING' && 'bg-white border-2 border-slate-300',
                    step.status === 'REJECTED' && 'bg-red-500 text-white',
                    step.status === 'SKIPPED' && 'bg-slate-300 text-white'
                  )}
                >
                  {step.status === 'COMPLETED' ? (
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : step.status === 'REJECTED' ? (
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  ) : step.status === 'IN_PROGRESS' ? (
                    <div className="w-2 h-2 bg-white rounded-full" />
                  ) : (
                    <span className="text-xs">{step.step_number}</span>
                  )}
                </div>

                <div className="flex-1 pb-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium">{step.step_name}</p>
                      {step.status === 'IN_PROGRESS' && step.assigned_to_name && (
                        <p className="text-sm text-muted-foreground">
                          Pending with {step.assigned_to_name}
                          {step.is_overdue && (
                            <Badge variant="outline" className="ml-2 text-xs bg-red-100 text-red-700">
                              Overdue
                            </Badge>
                          )}
                        </p>
                      )}
                      {step.status === 'COMPLETED' && step.completed_by_name && (
                        <p className="text-sm text-muted-foreground">
                          {step.action === 'APPROVE' ? 'Approved' : 'Processed'} by {step.completed_by_name}
                        </p>
                      )}
                      {step.remarks && (
                        <p className="text-sm text-muted-foreground mt-1 italic">
                          "{step.remarks}"
                        </p>
                      )}
                    </div>
                    {step.completed_at && (
                      <span className="text-xs text-muted-foreground">
                        {formatDate(step.completed_at)}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Workflow history list
 */
export function WorkflowHistory({
  steps,
  className,
}: {
  steps: WorkflowStep[];
  className?: string;
}) {
  const completedSteps = steps.filter(
    (s) => s.status === 'COMPLETED' || s.status === 'REJECTED'
  );

  if (completedSteps.length === 0) {
    return (
      <div className={cn('text-center py-4 text-muted-foreground text-sm', className)}>
        No approval history yet
      </div>
    );
  }

  return (
    <div className={cn('space-y-3', className)}>
      {completedSteps.map((step) => (
        <div key={step.step_id} className="flex items-start gap-3 p-3 bg-muted/50 rounded-lg">
          <div
            className={cn(
              'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
              step.action === 'APPROVE' && 'bg-green-100 text-green-700',
              step.action === 'REJECT' && 'bg-red-100 text-red-700',
              step.action === 'RETURN' && 'bg-amber-100 text-amber-700',
              !step.action && 'bg-blue-100 text-blue-700'
            )}
          >
            {step.action === 'APPROVE' ? (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : step.action === 'REJECT' ? (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium">{step.step_name}</p>
            <p className="text-sm text-muted-foreground">
              {step.action} by {step.completed_by_name}
            </p>
            {step.remarks && (
              <p className="text-sm mt-1 italic text-muted-foreground">
                "{step.remarks}"
              </p>
            )}
            {step.completed_at && (
              <p className="text-xs text-muted-foreground mt-1">
                {formatDate(step.completed_at)}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function formatDate(dateStr: string): string {
  try {
    return format(parseISO(dateStr), 'dd MMM yyyy, HH:mm');
  } catch {
    return dateStr;
  }
}
