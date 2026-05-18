import { useEffect } from 'react';

import { AmountInput } from '@/components/lending/common/AmountInput';
import { useWizard } from '@/components/lending/wizard/WizardContext';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';

interface StepData {
  projectName?: string;
  projectCost?: number;
  promoterContribution?: number;
  bankFinance?: number;
  projectStartDate?: string;
  projectCompletionDate?: string;
  projectDescription?: string;
}

export default function Step3ProjectDetails() {
  const { data, updateStepData, setValidation } = useWizard();
  const stepData = (data['project-details'] || {}) as StepData;

  useEffect(() => {
    // This step is optional for non-project finance loans
    setValidation('project-details', true);
  }, [setValidation]);

  const handleChange = (field: string, value: string | number) => {
    updateStepData('project-details', { ...stepData, [field]: value });
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Project Details</h3>
        <p className="text-sm text-muted-foreground">
          Enter project information for project finance or term loans (optional for other products)
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Project Name */}
        <div className="space-y-2 md:col-span-2">
          <Label htmlFor="projectName">Project Name</Label>
          <Input
            id="projectName"
            value={stepData.projectName || ''}
            onChange={(e) => handleChange('projectName', e.target.value)}
            placeholder="Enter project name"
          />
        </div>

        {/* Total Project Cost */}
        <div className="space-y-2">
          <Label htmlFor="projectCost">Total Project Cost</Label>
          <AmountInput
            value={stepData.projectCost || 0}
            onChange={(value) => handleChange('projectCost', value ?? 0)}
            placeholder="Enter total project cost"
          />
        </div>

        {/* Promoter Contribution */}
        <div className="space-y-2">
          <Label htmlFor="promoterContribution">Promoter Contribution</Label>
          <AmountInput
            value={stepData.promoterContribution || 0}
            onChange={(value) => handleChange('promoterContribution', value ?? 0)}
            placeholder="Enter promoter contribution"
          />
        </div>

        {/* Bank Finance */}
        <div className="space-y-2">
          <Label htmlFor="bankFinance">Bank Finance Required</Label>
          <AmountInput
            value={stepData.bankFinance || 0}
            onChange={(value) => handleChange('bankFinance', value ?? 0)}
            placeholder="Enter bank finance required"
          />
        </div>

        {/* Calculated Debt-Equity */}
        <div className="space-y-2">
          <Label>Debt-Equity Ratio</Label>
          <div className="rounded-md bg-muted p-3">
            <span className="font-mono">
              {stepData.projectCost && stepData.promoterContribution
                ? `${(
                    (stepData.projectCost - stepData.promoterContribution) /
                    stepData.promoterContribution
                  ).toFixed(2)} : 1`
                : 'N/A'}
            </span>
          </div>
        </div>

        {/* Project Start Date */}
        <div className="space-y-2">
          <Label htmlFor="projectStartDate">Expected Start Date</Label>
          <Input
            id="projectStartDate"
            type="date"
            value={stepData.projectStartDate || ''}
            onChange={(e) => handleChange('projectStartDate', e.target.value)}
          />
        </div>

        {/* Project End Date */}
        <div className="space-y-2">
          <Label htmlFor="projectCompletionDate">Expected Completion Date</Label>
          <Input
            id="projectCompletionDate"
            type="date"
            value={stepData.projectCompletionDate || ''}
            onChange={(e) => handleChange('projectCompletionDate', e.target.value)}
          />
        </div>
      </div>

      {/* Project Description */}
      <div className="space-y-2">
        <Label htmlFor="projectDescription">Project Description</Label>
        <Textarea
          id="projectDescription"
          value={stepData.projectDescription || ''}
          onChange={(e) => handleChange('projectDescription', e.target.value)}
          placeholder="Describe the project details..."
          rows={4}
        />
      </div>
    </div>
  );
}
