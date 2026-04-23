import { useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useWizard } from '@/components/lending/wizard/WizardContext';
import { AmountInput } from '@/components/lending/common/AmountInput';

interface StepData {
  project_name?: string;
  project_cost?: number;
  promoter_contribution?: number;
  bank_finance?: number;
  project_start_date?: string;
  project_end_date?: string;
  project_description?: string;
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
          <Label htmlFor="project_name">Project Name</Label>
          <Input
            id="project_name"
            value={stepData.project_name || ''}
            onChange={(e) => handleChange('project_name', e.target.value)}
            placeholder="Enter project name"
          />
        </div>

        {/* Total Project Cost */}
        <div className="space-y-2">
          <Label htmlFor="project_cost">Total Project Cost</Label>
          <AmountInput
            value={stepData.project_cost || 0}
            onChange={(value) => handleChange('project_cost', value ?? 0)}
            placeholder="Enter total project cost"
          />
        </div>

        {/* Promoter Contribution */}
        <div className="space-y-2">
          <Label htmlFor="promoter_contribution">Promoter Contribution</Label>
          <AmountInput
            value={stepData.promoter_contribution || 0}
            onChange={(value) => handleChange('promoter_contribution', value ?? 0)}
            placeholder="Enter promoter contribution"
          />
        </div>

        {/* Bank Finance */}
        <div className="space-y-2">
          <Label htmlFor="bank_finance">Bank Finance Required</Label>
          <AmountInput
            value={stepData.bank_finance || 0}
            onChange={(value) => handleChange('bank_finance', value ?? 0)}
            placeholder="Enter bank finance required"
          />
        </div>

        {/* Calculated Debt-Equity */}
        <div className="space-y-2">
          <Label>Debt-Equity Ratio</Label>
          <div className="p-3 bg-muted rounded-md">
            <span className="font-mono">
              {stepData.project_cost && stepData.promoter_contribution
                ? `${(
                    (stepData.project_cost - stepData.promoter_contribution) /
                    stepData.promoter_contribution
                  ).toFixed(2)} : 1`
                : 'N/A'}
            </span>
          </div>
        </div>

        {/* Project Start Date */}
        <div className="space-y-2">
          <Label htmlFor="project_start_date">Expected Start Date</Label>
          <Input
            id="project_start_date"
            type="date"
            value={stepData.project_start_date || ''}
            onChange={(e) => handleChange('project_start_date', e.target.value)}
          />
        </div>

        {/* Project End Date */}
        <div className="space-y-2">
          <Label htmlFor="project_end_date">Expected Completion Date</Label>
          <Input
            id="project_end_date"
            type="date"
            value={stepData.project_end_date || ''}
            onChange={(e) => handleChange('project_end_date', e.target.value)}
          />
        </div>
      </div>

      {/* Project Description */}
      <div className="space-y-2">
        <Label htmlFor="project_description">Project Description</Label>
        <Textarea
          id="project_description"
          value={stepData.project_description || ''}
          onChange={(e) => handleChange('project_description', e.target.value)}
          placeholder="Describe the project details..."
          rows={4}
        />
      </div>
    </div>
  );
}
