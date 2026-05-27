/**
 * Application Wizard Page
 * 6-step wizard for creating/editing loan applications (NO MODALS)
 */

import { Loader2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';

// Import step components
import Step1EntityProduct from './steps/Step1EntityProduct';
import Step2LoanDetails from './steps/Step2LoanDetails';
import Step3ProjectDetails from './steps/Step3ProjectDetails';
import Step4Security from './steps/Step4Security';
import Step5Documents from './steps/Step5Documents';
import Step6Review from './steps/Step6Review';
import StepFundUtilization, { type UtilizationLineDraft } from './steps/StepFundUtilization';

import { PageHeader } from '@/components/common/PageHeader';
import { WizardContainer } from '@/components/lending/wizard/WizardContainer';
import { WizardStep } from '@/components/lending/wizard/WizardStep';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import { applicationApi } from '@/services/lending';
import { applicationUtilizationApi } from '@/services/lending/iifApi';
import type { CreateApplicationRequest, LoanApplication } from '@/types/lending';

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
    id: 'fund-utilization',
    title: 'Fund Utilization',
    description: 'Split the requested amount across IIF utilization categories',
  },
  {
    id: 'review',
    title: 'Review & Submit',
    description: 'Review and submit application',
  },
];

type EntityProductStepData = Pick<CreateApplicationRequest, 'entityId' | 'productId'>;
type LoanDetailsStepData = Pick<
  CreateApplicationRequest,
  | 'requestedAmount'
  | 'requestedTenureMonths'
  | 'purpose'
  | 'preferredInterestType'
  | 'proposedRate'
  | 'requestedMoratoriumMonths'
  | 'preferredRepaymentFrequency'
  | 'preferredRepaymentMode'
>;
type ProjectDetailsStepData = Pick<
  CreateApplicationRequest,
  | 'isProjectFinance'
  | 'projectName'
  | 'projectCost'
  | 'promoterContribution'
  | 'bankFinance'
  | 'projectStartDate'
  | 'projectCompletionDate'
>;

function buildApplicationPayload(data: Record<string, unknown>): CreateApplicationRequest {
  return {
    ...((data['entity-product'] as Partial<EntityProductStepData>) || {}),
    ...((data['loan-details'] as Partial<LoanDetailsStepData>) || {}),
    ...((data['project-details'] as Partial<ProjectDetailsStepData>) || {}),
  } as CreateApplicationRequest;
}

export default function ApplicationWizard() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const isEditMode = Boolean(id);

  const [loading, setLoading] = useState(isEditMode);
  const [application, setApplication] = useState<LoanApplication | null>(null);
  const [initialData, setInitialData] = useState<Record<string, unknown>>({});

  // Get pre-selected entity from URL params (when coming from entity page)
  const preSelectedEntityId = searchParams.get('entityId');

  // Load application data for edit mode
  useEffect(() => {
    if (isEditMode && id) {
      loadApplication(id);
    } else if (preSelectedEntityId) {
      setInitialData({
        'entity-product': { entityId: preSelectedEntityId },
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
          entityId: data.entityId,
          productId: data.productId,
        },
        'loan-details': {
          requestedAmount: Number(data.requestedAmount),
          requestedTenureMonths: data.requestedTenureMonths,
          purpose: data.purpose,
          preferredInterestType: data.preferredInterestType,
          proposedRate: data.proposedRate ? Number(data.proposedRate) : undefined,
          requestedMoratoriumMonths: data.requestedMoratoriumMonths,
          preferredRepaymentFrequency: data.preferredRepaymentFrequency,
          preferredRepaymentMode: data.preferredRepaymentMode,
        },
        'project-details': {
          isProjectFinance: data.isProjectFinance,
          projectName: data.projectName,
          projectCost: data.projectCost ? Number(data.projectCost) : undefined,
          promoterContribution: data.promoterContribution
            ? Number(data.promoterContribution)
            : undefined,
          bankFinance: data.bankFinance ? Number(data.bankFinance) : undefined,
          projectStartDate: data.projectStartDate,
          projectCompletionDate: data.projectCompletionDate,
        },
      });
    } catch (err) {
      showErrorToast(err, toast);
      navigate('/admin/lending/applications');
    } finally {
      setLoading(false);
    }
  };

  // Handle wizard completion
  const handleComplete = async (data: Record<string, unknown>) => {
    try {
      const applicationData = buildApplicationPayload(data);

      let savedApplicationId: string;
      if (isEditMode && id) {
        await applicationApi.updateApplication(id, applicationData);
        savedApplicationId = id;
      } else {
        const newApp = await applicationApi.createApplication(applicationData);
        savedApplicationId = newApp.id;
      }

      // Persist IIF fund-utilization lines (if any). The step writes its lines
      // under `fund-utilization`. CLAUDE.md §6.2: amount stays as string on
      // the wire.
      const utilizationStep = data['fund-utilization'] as
        | { lines?: UtilizationLineDraft[]; override?: boolean }
        | undefined;
      const utilizationLines = utilizationStep?.lines ?? [];
      const utilizationOverride = Boolean(utilizationStep?.override);
      if (utilizationLines.length > 0) {
        const overrideNote = utilizationOverride
          ? 'OVERRIDE: total does not match requested amount.'
          : null;
        const payloadLines = utilizationLines.map((l) => ({
          categoryId: l.categoryId,
          amount: l.amount === '' ? '0' : l.amount,
          remarks:
            overrideNote && !l.remarks
              ? overrideNote
              : overrideNote && l.remarks
                ? `${l.remarks} — ${overrideNote}`
                : l.remarks,
        }));
        await applicationUtilizationApi.bulkReplace(savedApplicationId, payloadLines);
      }

      if (!isEditMode) {
        // Submit the application after creation + utilization persistence.
        await applicationApi.submitApplication(savedApplicationId);
      }
      navigate(`/admin/lending/applications/${savedApplicationId}`);
    } catch (err) {
      showErrorToast(err, toast);
    }
  };

  // Handle draft save
  const handleSaveDraft = async (data: Record<string, unknown>) => {
    try {
      const applicationData = buildApplicationPayload(data);

      const result = await applicationApi.saveDraft(isEditMode && id ? id : null, applicationData);

      if (!isEditMode) {
        // Redirect to edit mode for the new draft
        navigate(`/admin/lending/applications/${result.id}/edit`, { replace: true });
      }
    } catch (err) {
      showErrorToast(err, toast);
    }
  };

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEditMode ? 'Edit Application' : 'New Loan Application'}
        subtitle={
          isEditMode
            ? `Editing application ${application?.applicationNumber}`
            : 'Create a new loan application in 6 easy steps'
        }
        breadcrumbs={[
          { label: 'Applications', to: '/admin/lending/applications' },
          { label: isEditMode ? 'Edit' : 'New' },
        ]}
      />

      {/* Wizard */}
      <WizardContainer
        steps={WIZARD_STEPS}
        initialData={initialData}
        onSubmit={handleComplete}
        onSaveDraft={handleSaveDraft}
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
          <Step4Security applicationId={application?.id} />
        </WizardStep>

        <WizardStep stepId="documents">
          <Step5Documents applicationId={application?.id} />
        </WizardStep>

        <WizardStep stepId="fund-utilization">
          <StepFundUtilization applicationId={application?.id} />
        </WizardStep>

        <WizardStep stepId="review">
          <Step6Review applicationId={application?.id} />
        </WizardStep>
      </WizardContainer>
    </div>
  );
}
