import { useEffect } from 'react';

import { ErrorState } from '@/components/common';
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
import { useLendingOptionRows } from '@/hooks/lending/useLendingMasters';
import { useLoanProduct } from '@/hooks/lending/useLoanProduct';

interface StepData {
  requestedAmount?: number;
  requestedTenureMonths?: number;
  purpose?: string;
  preferredInterestType?: string;
  proposedRate?: number;
  requestedMoratoriumMonths?: number;
  preferredRepaymentFrequency?: string;
  preferredRepaymentMode?: string;
}

export default function Step2LoanDetails() {
  const { data, updateStepData, setValidation } = useWizard();
  const stepData = (data['loan-details'] || {}) as StepData;
  const entityProduct = (data['entity-product'] || {}) as { productId?: string };
  const productQuery = useLoanProduct(entityProduct.productId);
  const rateTypesQuery = useLendingOptionRows('RATE_TYPE');
  const repaymentFrequenciesQuery = useLendingOptionRows('REPAYMENT_FREQUENCY');
  const repaymentModesQuery = useLendingOptionRows('REPAYMENT_MODE');
  const product = productQuery.data;

  const masterLabel = (
    rows: { data: Record<string, unknown> }[] | undefined,
    code: string | undefined,
  ) => String(rows?.find((row) => String(row.data.code) === code)?.data.label ?? code ?? '');
  const repaymentFrequencyOptions = (product?.allowedRepaymentFrequencies ?? []).map((code) => ({
    value: code,
    label: masterLabel(repaymentFrequenciesQuery.data?.items, code),
  }));
  const repaymentModeOptions = (product?.allowedRepaymentModes ?? []).map((code) => ({
    value: code,
    label: masterLabel(repaymentModesQuery.data?.items, code),
  }));

  useEffect(() => {
    const isValid = Boolean(
      stepData.requestedAmount &&
      stepData.requestedTenureMonths &&
      stepData.purpose &&
      stepData.preferredInterestType &&
      stepData.preferredRepaymentFrequency &&
      stepData.preferredRepaymentMode,
    );
    setValidation('loan-details', isValid);
  }, [stepData, setValidation]);

  useEffect(() => {
    if (!product) return;
    const patch: Partial<StepData> = {};
    if (!stepData.preferredInterestType) patch.preferredInterestType = product.interestType;
    if (!stepData.preferredRepaymentFrequency) {
      patch.preferredRepaymentFrequency = product.defaultRepaymentFrequency;
    }
    if (!stepData.preferredRepaymentMode) {
      patch.preferredRepaymentMode = product.defaultRepaymentMode;
    }
    if (!stepData.requestedTenureMonths && product.defaultTenureMonths) {
      patch.requestedTenureMonths = product.defaultTenureMonths;
    }
    if (Object.keys(patch).length > 0) {
      updateStepData('loan-details', { ...stepData, ...patch });
    }
  }, [product, stepData, updateStepData]);

  const handleChange = (field: string, value: string | number) => {
    updateStepData('loan-details', { ...stepData, [field]: value });
  };

  if (productQuery.isError) {
    return (
      <ErrorState
        title="Could not load selected product policy"
        error={productQuery.error}
        onRetry={() => productQuery.refetch()}
      />
    );
  }

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
            min={product?.minTenureMonths ?? 1}
            max={product?.maxTenureMonths ?? 600}
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
            disabled={Boolean(product?.interestType)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select interest type" />
            </SelectTrigger>
            <SelectContent>
              {(product?.interestType
                ? [
                    {
                      value: product.interestType,
                      label: masterLabel(rateTypesQuery.data?.items, product.interestType),
                    },
                  ]
                : (rateTypesQuery.data?.items ?? []).map((row) => ({
                    value: String(row.data.code),
                    label: String(row.data.label ?? row.data.code),
                  }))
              ).map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
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
            min={product?.minEffectiveRate ? Number(product.minEffectiveRate) : 0}
            max={product?.maxEffectiveRate ? Number(product.maxEffectiveRate) : 100}
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
              {repaymentFrequencyOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Repayment Mode */}
        <div className="space-y-2">
          <Label>Repayment Mode *</Label>
          <Select
            value={stepData.preferredRepaymentMode || ''}
            onValueChange={(value) => handleChange('preferredRepaymentMode', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select mode" />
            </SelectTrigger>
            <SelectContent>
              {repaymentModeOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
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
            max={product?.maxMoratoriumMonths ?? 0}
            disabled={!product?.allowsMoratorium}
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
