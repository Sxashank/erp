import { useEffect } from 'react';

import { AmountInput } from '@/components/lending/common/AmountInput';
import { useWizard } from '@/components/lending/wizard/WizardContext';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';

interface StepData {
  requestedAmount?: number;
  requestedTenureMonths?: number;
  purpose?: string;
  preferredInterestType?: string;
  proposedRate?: number;
  requestedMoratoriumMonths?: number;
  preferredRepaymentFrequency?: string;
}

export default function Step2LoanDetails() {
  const { data, updateStepData, setValidation } = useWizard();
  const stepData = (data['loan-details'] || {}) as StepData;

  useEffect(() => {
    const isValid = Boolean(
      stepData.requestedAmount &&
      stepData.requestedTenureMonths &&
      stepData.purpose &&
      stepData.preferredInterestType &&
      stepData.preferredRepaymentFrequency,
    );
    setValidation('loan-details', isValid);
  }, [stepData, setValidation]);

  const handleChange = (field: string, value: string | number) => {
    updateStepData('loan-details', { ...stepData, [field]: value });
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Loan Details</h3>
        <p className="text-sm text-muted-foreground">
          Enter the loan amount, tenure, and repayment terms
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Requested Amount */}
        <div className="space-y-2">
          <Label htmlFor="requestedAmount">Requested Amount *</Label>
          <AmountInput
            value={stepData.requestedAmount || 0}
            onChange={(value) => handleChange('requestedAmount', value ?? 0)}
            placeholder="Enter loan amount"
          />
        </div>

        {/* Tenure */}
        <div className="space-y-2">
          <Label htmlFor="requestedTenureMonths">Tenure (Months) *</Label>
          <Input
            id="requestedTenureMonths"
            type="number"
            min={1}
            max={360}
            value={stepData.requestedTenureMonths || ''}
            onChange={(e) => handleChange('requestedTenureMonths', parseInt(e.target.value))}
            placeholder="Enter tenure in months"
          />
        </div>

        {/* Interest Type */}
        <div className="space-y-2">
          <Label>Interest Type *</Label>
          <Select
            value={stepData.preferredInterestType || ''}
            onValueChange={(value) => handleChange('preferredInterestType', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select interest type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="FIXED">Fixed Rate</SelectItem>
              <SelectItem value="FLOATING">Floating Rate</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Proposed Rate */}
        <div className="space-y-2">
          <Label htmlFor="proposedRate">Proposed Interest Rate (% p.a.)</Label>
          <Input
            id="proposedRate"
            type="number"
            step="0.01"
            min={0}
            max={50}
            value={stepData.proposedRate || ''}
            onChange={(e) => handleChange('proposedRate', parseFloat(e.target.value))}
            placeholder="e.g., 12.50"
          />
        </div>

        {/* Repayment Frequency */}
        <div className="space-y-2">
          <Label>Repayment Frequency *</Label>
          <Select
            value={stepData.preferredRepaymentFrequency || ''}
            onValueChange={(value) => handleChange('preferredRepaymentFrequency', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select frequency" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="MONTHLY">Monthly</SelectItem>
              <SelectItem value="QUARTERLY">Quarterly</SelectItem>
              <SelectItem value="HALF_YEARLY">Half-Yearly</SelectItem>
              <SelectItem value="YEARLY">Yearly</SelectItem>
              <SelectItem value="BULLET">Bullet (At Maturity)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Moratorium Period */}
        <div className="space-y-2">
          <Label htmlFor="requestedMoratoriumMonths">Moratorium Period (Months)</Label>
          <Input
            id="requestedMoratoriumMonths"
            type="number"
            min={0}
            max={36}
            value={stepData.requestedMoratoriumMonths || ''}
            onChange={(e) => handleChange('requestedMoratoriumMonths', parseInt(e.target.value))}
            placeholder="Enter moratorium period"
          />
        </div>
      </div>

      {/* Purpose */}
      <div className="space-y-2">
        <Label htmlFor="purpose">Purpose of Loan *</Label>
        <Textarea
          id="purpose"
          value={stepData.purpose || ''}
          onChange={(e) => handleChange('purpose', e.target.value)}
          placeholder="Describe the purpose of this loan..."
          rows={4}
        />
      </div>
    </div>
  );
}
