import { useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useWizard } from '@/components/lending/wizard/WizardContext';
import { AmountInput } from '@/components/lending/common/AmountInput';

interface StepData {
  requested_amount?: number;
  requested_tenure_months?: number;
  purpose?: string;
  interest_type?: string;
  proposed_rate?: number;
  moratorium_months?: number;
  repayment_frequency?: string;
}

export default function Step2LoanDetails() {
  const { data, updateStepData, setValidation } = useWizard();
  const stepData = (data['loan-details'] || {}) as StepData;

  useEffect(() => {
    const isValid = Boolean(
      stepData.requested_amount &&
      stepData.requested_tenure_months &&
      stepData.purpose &&
      stepData.interest_type &&
      stepData.repayment_frequency
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
          <Label htmlFor="requested_amount">Requested Amount *</Label>
          <AmountInput
            value={stepData.requested_amount || 0}
            onChange={(value) => handleChange('requested_amount', value ?? 0)}
            placeholder="Enter loan amount"
          />
        </div>

        {/* Tenure */}
        <div className="space-y-2">
          <Label htmlFor="requested_tenure_months">Tenure (Months) *</Label>
          <Input
            id="requested_tenure_months"
            type="number"
            min={1}
            max={360}
            value={stepData.requested_tenure_months || ''}
            onChange={(e) => handleChange('requested_tenure_months', parseInt(e.target.value))}
            placeholder="Enter tenure in months"
          />
        </div>

        {/* Interest Type */}
        <div className="space-y-2">
          <Label>Interest Type *</Label>
          <Select
            value={stepData.interest_type || ''}
            onValueChange={(value) => handleChange('interest_type', value)}
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
          <Label htmlFor="proposed_rate">Proposed Interest Rate (% p.a.)</Label>
          <Input
            id="proposed_rate"
            type="number"
            step="0.01"
            min={0}
            max={50}
            value={stepData.proposed_rate || ''}
            onChange={(e) => handleChange('proposed_rate', parseFloat(e.target.value))}
            placeholder="e.g., 12.50"
          />
        </div>

        {/* Repayment Frequency */}
        <div className="space-y-2">
          <Label>Repayment Frequency *</Label>
          <Select
            value={stepData.repayment_frequency || ''}
            onValueChange={(value) => handleChange('repayment_frequency', value)}
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
          <Label htmlFor="moratorium_months">Moratorium Period (Months)</Label>
          <Input
            id="moratorium_months"
            type="number"
            min={0}
            max={36}
            value={stepData.moratorium_months || ''}
            onChange={(e) => handleChange('moratorium_months', parseInt(e.target.value))}
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
