import { useEffect } from 'react';
import { CheckCircle, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { useWizard } from '@/components/lending/wizard/WizardContext';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';

interface Step6Props {
  applicationId?: string;
}

export default function Step6Review({ applicationId }: Step6Props) {
  const { data, validation, setValidation } = useWizard();

  const entityProductData = data['entity-product'] as Record<string, any> || {};
  const loanDetailsData = data['loan-details'] as Record<string, any> || {};
  const projectDetailsData = data['project-details'] as Record<string, any> || {};

  // All previous steps must be valid
  const allStepsValid =
    validation['entity-product'] &&
    validation['loan-details'] &&
    validation['project-details'] &&
    validation['security'] &&
    validation['documents'];

  useEffect(() => {
    // Review step is valid if all previous steps are valid
    setValidation('review', allStepsValid);
  }, [allStepsValid, setValidation]);

  const StepStatus = ({ stepId, label }: { stepId: string; label: string }) => (
    <div className="flex items-center justify-between py-2">
      <span>{label}</span>
      {validation[stepId] ? (
        <CheckCircle className="h-5 w-5 text-green-500" />
      ) : (
        <AlertCircle className="h-5 w-5 text-amber-500" />
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Review & Submit</h3>
        <p className="text-sm text-muted-foreground">
          Review your application details before submission
        </p>
      </div>

      {/* Step Completion Status */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Application Checklist</CardTitle>
        </CardHeader>
        <CardContent>
          <StepStatus stepId="entity-product" label="Entity & Product Selection" />
          <Separator />
          <StepStatus stepId="loan-details" label="Loan Details" />
          <Separator />
          <StepStatus stepId="project-details" label="Project Details" />
          <Separator />
          <StepStatus stepId="security" label="Security & Collateral" />
          <Separator />
          <StepStatus stepId="documents" label="Document Upload" />
        </CardContent>
      </Card>

      {/* Application Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Application Summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Entity & Product */}
          <div>
            <h4 className="text-sm font-medium text-muted-foreground mb-2">
              Entity & Product
            </h4>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <p className="text-sm text-muted-foreground">Entity</p>
                <p className="font-medium">
                  {entityProductData.entity_id ? 'Selected' : 'Not Selected'}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Loan Product</p>
                <p className="font-medium">
                  {entityProductData.product_id ? 'Selected' : 'Not Selected'}
                </p>
              </div>
            </div>
          </div>

          <Separator />

          {/* Loan Details */}
          <div>
            <h4 className="text-sm font-medium text-muted-foreground mb-2">
              Loan Details
            </h4>
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <p className="text-sm text-muted-foreground">Requested Amount</p>
                <AmountDisplay
                  amount={loanDetailsData.requested_amount || 0}
                  abbreviated
                  className="font-medium"
                />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Tenure</p>
                <p className="font-medium">
                  {loanDetailsData.requested_tenure_months || '-'} Months
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Interest Type</p>
                <p className="font-medium">
                  {loanDetailsData.interest_type?.replace('_', ' ') || '-'}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Proposed Rate</p>
                <p className="font-medium">
                  {loanDetailsData.proposed_rate
                    ? `${loanDetailsData.proposed_rate}% p.a.`
                    : '-'}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Repayment Frequency</p>
                <p className="font-medium">
                  {loanDetailsData.repayment_frequency?.replace('_', ' ') || '-'}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Moratorium</p>
                <p className="font-medium">
                  {loanDetailsData.moratorium_months || 0} Months
                </p>
              </div>
            </div>
            {loanDetailsData.purpose && (
              <div className="mt-4">
                <p className="text-sm text-muted-foreground">Purpose</p>
                <p className="font-medium">{loanDetailsData.purpose}</p>
              </div>
            )}
          </div>

          {projectDetailsData.project_name && (
            <>
              <Separator />
              {/* Project Details */}
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">
                  Project Details
                </h4>
                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <p className="text-sm text-muted-foreground">Project Name</p>
                    <p className="font-medium">{projectDetailsData.project_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Cost</p>
                    <AmountDisplay
                      amount={projectDetailsData.project_cost || 0}
                      abbreviated
                      className="font-medium"
                    />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Promoter Contribution</p>
                    <AmountDisplay
                      amount={projectDetailsData.promoter_contribution || 0}
                      abbreviated
                      className="font-medium"
                    />
                  </div>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Terms & Conditions */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <Checkbox id="terms1" />
              <Label htmlFor="terms1" className="text-sm leading-relaxed">
                I confirm that all information provided in this application is true and
                accurate to the best of my knowledge.
              </Label>
            </div>
            <div className="flex items-start space-x-3">
              <Checkbox id="terms2" />
              <Label htmlFor="terms2" className="text-sm leading-relaxed">
                I authorize SMFC to verify the information provided and conduct necessary
                due diligence including credit bureau checks.
              </Label>
            </div>
            <div className="flex items-start space-x-3">
              <Checkbox id="terms3" />
              <Label htmlFor="terms3" className="text-sm leading-relaxed">
                I understand that this application is subject to approval and does not
                constitute a commitment to lend.
              </Label>
            </div>
          </div>
        </CardContent>
      </Card>

      {!allStepsValid && (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-amber-700">
              <AlertCircle className="h-5 w-5" />
              <p className="font-medium">Please complete all required steps before submitting.</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
