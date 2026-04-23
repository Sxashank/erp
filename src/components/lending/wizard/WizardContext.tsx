/**
 * WizardContext
 * State management for multi-step wizard forms
 */

import * as React from 'react';

export interface WizardStep {
  id: string;
  title: string;
  description?: string;
  isOptional?: boolean;
  isCompleted?: boolean;
  isValid?: boolean;
}

export interface WizardState {
  steps: WizardStep[];
  currentStepIndex: number;
  currentStepId: string;
  data: Record<string, unknown>;
  isDirty: boolean;
  isSubmitting: boolean;
  errors: Record<string, string[]>;
  validation: Record<string, boolean>;
}

export interface WizardContextValue extends WizardState {
  // Navigation
  goToStep: (stepIndex: number) => void;
  goToStepById: (stepId: string) => void;
  nextStep: () => void;
  previousStep: () => void;

  // Data management
  setStepData: (stepId: string, data: Record<string, unknown>) => void;
  updateData: (data: Record<string, unknown>) => void;
  getData: <T = unknown>(key: string) => T | undefined;

  // Validation
  setStepValid: (stepId: string, isValid: boolean) => void;
  setStepCompleted: (stepId: string, isCompleted: boolean) => void;
  setErrors: (stepId: string, errors: string[]) => void;
  clearErrors: (stepId?: string) => void;

  setValidation: (stepId: string, isValid: boolean) => void;
  updateStepData: (stepId: string, data: Record<string, unknown>) => void;

  // Status
  setSubmitting: (isSubmitting: boolean) => void;
  markDirty: () => void;
  resetWizard: () => void;

  // Helpers
  isFirstStep: boolean;
  isLastStep: boolean;
  canGoNext: boolean;
  canGoPrevious: boolean;
  progress: number;
  completedSteps: number;
}

const WizardContext = React.createContext<WizardContextValue | null>(null);

export interface WizardProviderProps {
  children: React.ReactNode;
  steps: WizardStep[];
  initialData?: Record<string, unknown>;
  onStepChange?: (stepIndex: number, stepId: string) => void;
  onDataChange?: (data: Record<string, unknown>) => void;
}

export function WizardProvider({
  children,
  steps,
  initialData = {},
  onStepChange,
  onDataChange,
}: WizardProviderProps) {
  const [state, setState] = React.useState<WizardState>({
    steps,
    currentStepIndex: 0,
    currentStepId: steps[0]?.id || '',
    data: initialData,
    isDirty: false,
    isSubmitting: false,
    errors: {},
    validation: {},
  });

  // Navigation functions
  const goToStep = React.useCallback((stepIndex: number) => {
    if (stepIndex < 0 || stepIndex >= state.steps.length) return;

    setState((prev) => ({
      ...prev,
      currentStepIndex: stepIndex,
      currentStepId: prev.steps[stepIndex].id,
    }));

    onStepChange?.(stepIndex, state.steps[stepIndex].id);
  }, [state.steps, onStepChange]);

  const goToStepById = React.useCallback((stepId: string) => {
    const index = state.steps.findIndex((s) => s.id === stepId);
    if (index !== -1) {
      goToStep(index);
    }
  }, [state.steps, goToStep]);

  const nextStep = React.useCallback(() => {
    if (state.currentStepIndex < state.steps.length - 1) {
      goToStep(state.currentStepIndex + 1);
    }
  }, [state.currentStepIndex, state.steps.length, goToStep]);

  const previousStep = React.useCallback(() => {
    if (state.currentStepIndex > 0) {
      goToStep(state.currentStepIndex - 1);
    }
  }, [state.currentStepIndex, goToStep]);

  // Data management
  const setStepData = React.useCallback((stepId: string, data: Record<string, unknown>) => {
    setState((prev) => {
      const newData = { ...prev.data, [stepId]: data };
      onDataChange?.(newData);
      return {
        ...prev,
        data: newData,
        isDirty: true,
      };
    });
  }, [onDataChange]);

  const updateData = React.useCallback((data: Record<string, unknown>) => {
    setState((prev) => {
      const newData = { ...prev.data, ...data };
      onDataChange?.(newData);
      return {
        ...prev,
        data: newData,
        isDirty: true,
      };
    });
  }, [onDataChange]);

  const getData = React.useCallback(<T = unknown>(key: string): T | undefined => {
    return state.data[key] as T | undefined;
  }, [state.data]);

  // Validation
  const setStepValid = React.useCallback((stepId: string, isValid: boolean) => {
    setState((prev) => ({
      ...prev,
      steps: prev.steps.map((s) =>
        s.id === stepId ? { ...s, isValid } : s
      ),
    }));
  }, []);

  const setStepCompleted = React.useCallback((stepId: string, isCompleted: boolean) => {
    setState((prev) => ({
      ...prev,
      steps: prev.steps.map((s) =>
        s.id === stepId ? { ...s, isCompleted } : s
      ),
    }));
  }, []);

  const setErrors = React.useCallback((stepId: string, errors: string[]) => {
    setState((prev) => ({
      ...prev,
      errors: { ...prev.errors, [stepId]: errors },
    }));
  }, []);

  const clearErrors = React.useCallback((stepId?: string) => {
    setState((prev) => {
      if (stepId) {
        const { [stepId]: _, ...rest } = prev.errors;
        return { ...prev, errors: rest };
      }
      return { ...prev, errors: {} };
    });
  }, []);

  const setValidation = React.useCallback((stepId: string, isValid: boolean) => {
    setState((prev) => ({
      ...prev,
      validation: { ...prev.validation, [stepId]: isValid },
    }));
    setStepValid(stepId, isValid);
  }, [setStepValid]);

  const updateStepData = React.useCallback((stepId: string, data: Record<string, unknown>) => {
    setStepData(stepId, data);
  }, [setStepData]);

  // Status
  const setSubmitting = React.useCallback((isSubmitting: boolean) => {
    setState((prev) => ({ ...prev, isSubmitting }));
  }, []);

  const markDirty = React.useCallback(() => {
    setState((prev) => ({ ...prev, isDirty: true }));
  }, []);

  const resetWizard = React.useCallback(() => {
    setState({
      steps,
      currentStepIndex: 0,
      currentStepId: steps[0]?.id || '',
      data: initialData,
      isDirty: false,
      isSubmitting: false,
      errors: {},
      validation: {},
    });
  }, [steps, initialData]);

  // Computed values
  const isFirstStep = state.currentStepIndex === 0;
  const isLastStep = state.currentStepIndex === state.steps.length - 1;
  const currentStep = state.steps[state.currentStepIndex];
  const canGoNext = currentStep?.isValid !== false && !state.isSubmitting;
  const canGoPrevious = !isFirstStep && !state.isSubmitting;
  const completedSteps = state.steps.filter((s) => s.isCompleted).length;
  const progress = state.steps.length > 0
    ? Math.round((completedSteps / state.steps.length) * 100)
    : 0;

  const value: WizardContextValue = {
    ...state,
    goToStep,
    goToStepById,
    nextStep,
    previousStep,
    setStepData,
    updateData,
    getData,
    setStepValid,
    setStepCompleted,
    setValidation,
    updateStepData,
    setErrors,
    clearErrors,
    setSubmitting,
    markDirty,
    resetWizard,
    isFirstStep,
    isLastStep,
    canGoNext,
    canGoPrevious,
    progress,
    completedSteps,
  };

  return (
    <WizardContext.Provider value={value}>
      {children}
    </WizardContext.Provider>
  );
}

export function useWizard() {
  const context = React.useContext(WizardContext);
  if (!context) {
    throw new Error('useWizard must be used within a WizardProvider');
  }
  return context;
}

export function useWizardStep(stepId: string) {
  const wizard = useWizard();
  const step = wizard.steps.find((s) => s.id === stepId);
  const isActive = wizard.currentStepId === stepId;
  const stepData = wizard.getData<Record<string, unknown>>(stepId) || {};
  const stepErrors = wizard.errors[stepId] || [];

  return {
    step,
    isActive,
    stepData,
    stepErrors,
    setData: (data: Record<string, unknown>) => wizard.setStepData(stepId, data),
    setValid: (isValid: boolean) => wizard.setStepValid(stepId, isValid),
    setCompleted: (isCompleted: boolean) => wizard.setStepCompleted(stepId, isCompleted),
    setErrors: (errors: string[]) => wizard.setErrors(stepId, errors),
    clearErrors: () => wizard.clearErrors(stepId),
  };
}
