/**
 * Application Wizard Page
 * 6-step wizard for creating/editing loan applications (NO MODALS)
 */

import { useState, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';

import { WizardContainer } from '@/components/lending/wizard/WizardContainer';
import { WizardStep } from '@/components/lending/wizard/WizardStep';

import { applicationApi } from '@/services/lending';
import type { LoanApplication } from '@/types/lending';

// Import step components
import Step1EntityProduct from './steps/Step1EntityProduct';
import Step2LoanDetails from './steps/Step2LoanDetails';
import Step3ProjectDetails from './steps/Step3ProjectDetails';
import Step4Security from './steps/Step4Security';
import Step5Documents from './steps/Step5Documents';
import Step6Review from './steps/Step6Review';

const WIZARD_STEPS = [
  {
    id: 'entity-product',
    title: 'Entity & Product',
    description: 'Select borrower and loan product',
  },
  {
    id: 'loan-details',
    title: 'Loan Details',
    description: 'Enter loan amount, tenure, and terms',
  },
  {
    id: 'project-details',
    title: 'Project Details',
    description: 'Project information and milestones',
  },
  {
    id: 'security',
    title: 'Security',
    description: 'Add collateral and security details',
  },
  {
    id: 'documents',
    title: 'Documents',
    description: 'Upload required documents',
  },
  {
    id: 'review',
    title: 'Review & Submit',
    description: 'Review and submit application',
  },
];

export default function ApplicationWizard() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const isEditMode = Boolean(id);

  const [loading, setLoading] = useState(isEditMode);
  const [application, setApplication] = useState<LoanApplication | null>(null);
  const [initialData, setInitialData] = useState<Record<string, unknown>>({});

  // Get pre-selected entity from URL params (when coming from entity page)
  const preSelectedEntityId = searchParams.get('entity_id');

  // Load application data for edit mode
  useEffect(() => {
    if (isEditMode && id) {
      loadApplication(id);
    } else if (preSelectedEntityId) {
      setInitialData({
        'entity-product': { entity_id: preSelectedEntityId },
      });
    }
  }, [id, isEditMode, preSelectedEntityId]);

  const loadApplication = async (applicationId: string) => {
    setLoading(true);
    try {
      const data = await applicationApi.getApplication(applicationId);
      setApplication(data);

      // Convert application data to wizard step data format
      setInitialData({
        'entity-product': {
          entity_id: data.entity_id,
          product_id: data.product_id,
        },
        'loan-details': {
          requested_amount: data.requested_amount,
          requested_tenure_months: data.requested_tenure_months,
          purpose: data.purpose,
          interest_type: data.interest_type,
          proposed_rate: data.proposed_rate,
          moratorium_months: data.moratorium_months,
          repayment_frequency: data.repayment_frequency,
        },
        'project-details': {
          project_name: data.project_name,
          project_cost: data.project_cost,
          promoter_contribution: data.promoter_contribution,
          bank_finance: data.bank_finance,
          project_start_date: data.project_start_date,
          project_end_date: data.project_end_date,
        },
      });
    } catch (error) {
      console.error('Failed to load application:', error);
      navigate('/admin/lending/applications');
    } finally {
      setLoading(false);
    }
  };

  // Handle wizard completion
  const handleComplete = async (data: Record<string, unknown>) => {
    try {
      // Flatten wizard data into single application object
      const applicationData = {
        ...(data['entity-product'] as Record<string, unknown> || {}),
        ...(data['loan-details'] as Record<string, unknown> || {}),
        ...(data['project-details'] as Record<string, unknown> || {}),
      } as Record<string, unknown>;

      if (isEditMode && id) {
        await applicationApi.updateApplication(id, applicationData);
        navigate(`/admin/lending/applications/${id}`);
      } else {
        const newApp = await applicationApi.createApplication(applicationData as any);
        // Submit the application after creation
        await applicationApi.submitApplication(newApp.application_id);
        navigate(`/admin/lending/applications/${newApp.application_id}`);
      }
    } catch (error) {
      console.error('Failed to save application:', error);
    }
  };

  // Handle draft save
  const handleSaveDraft = async (data: Record<string, unknown>) => {
    try {
      const applicationData = {
        ...(data['entity-product'] as Record<string, unknown> || {}),
        ...(data['loan-details'] as Record<string, unknown> || {}),
        ...(data['project-details'] as Record<string, unknown> || {}),
      } as Record<string, unknown>;

      const result = await applicationApi.saveDraft(
        isEditMode && id ? id : null,
        applicationData as any
      );

      if (!isEditMode) {
        // Redirect to edit mode for the new draft
        navigate(`/admin/lending/applications/${result.application_id}/edit`, { replace: true });
      }
    } catch (error) {
      console.error('Failed to save draft:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">
            {isEditMode ? 'Edit Application' : 'New Loan Application'}
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            {isEditMode
              ? `Editing application ${application?.application_number}`
              : 'Create a new loan application in 6 easy steps'}
          </p>
        </div>
      </div>

      {/* Wizard */}
      <WizardContainer
        steps={WIZARD_STEPS}
        initialData={initialData}
        onSubmit={handleComplete as unknown as () => Promise<void>}
        onSaveDraft={handleSaveDraft as unknown as () => Promise<void>}
        layout="sidebar"
      >
        <WizardStep stepId="entity-product">
          <Step1EntityProduct />
        </WizardStep>

        <WizardStep stepId="loan-details">
          <Step2LoanDetails />
        </WizardStep>

        <WizardStep stepId="project-details">
          <Step3ProjectDetails />
        </WizardStep>

        <WizardStep stepId="security">
          <Step4Security applicationId={application?.application_id} />
        </WizardStep>

        <WizardStep stepId="documents">
          <Step5Documents applicationId={application?.application_id} />
        </WizardStep>

        <WizardStep stepId="review">
          <Step6Review applicationId={application?.application_id} />
        </WizardStep>
      </WizardContainer>
    </div>
  );
}
