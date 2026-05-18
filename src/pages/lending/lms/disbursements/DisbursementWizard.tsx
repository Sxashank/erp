import { zodResolver } from '@hookform/resolvers/zod';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { z } from 'zod';

import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { AmountInput } from '@/components/lending/common/AmountInput';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { WizardContainer } from '@/components/lending/wizard/WizardContainer';
import { WizardStep } from '@/components/lending/wizard/WizardStep';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';
import { logger } from '@/lib/logger';
const disbursementSchema = z.object({
  sanctionId: z.string().min(1, 'Sanction is required'),
  loanAccountId: z.string().optional(),
  tranche: z.number().min(1),
  amount: z.number().min(1, 'Amount is required'),
  milestoneId: z.string().optional(),
  paymentMode: z.enum(['RTGS', 'NEFT', 'IMPS', 'CHEQUE']),
  bankAccountId: z.string().min(1, 'Bank account is required'),
  remarks: z.string().optional(),
  conditionsVerified: z.array(z.string()).min(1, 'At least one condition must be verified'),
});

type DisbursementFormData = z.infer<typeof disbursementSchema>;

// Sanction context is keyed off `?sanctionId=` in the URL. The wizard
// loads with empty defaults until the BE endpoint that prefills the
// sanction snapshot (remaining amount, conditions, milestones, beneficiary
// bank accounts) is wired. For now, the user enters everything manually.
const mockSanction = {
  id: '',
  sanctionNumber: '',
  entityName: '',
  sanctionedAmount: 0,
  disbursedAmount: 0,
  remainingAmount: 0,
  conditions: [] as { id: string; condition: string; status: string }[],
  milestones: [] as { id: string; milestone: string; amount: number; status: string }[],
  bankAccounts: [] as {
    id: string;
    bankName: string;
    accountNumber: string;
    ifsc: string;
    isPrimary: boolean;
  }[],
};

const steps = [
  { id: 'sanction', title: 'Select Sanction', description: 'Choose sanction for disbursement' },
  {
    id: 'conditions',
    title: 'Verify Conditions',
    description: 'Verify pre-disbursement conditions',
  },
  { id: 'amount', title: 'Disbursement Amount', description: 'Enter amount and milestone' },
  { id: 'payment', title: 'Payment Details', description: 'Select payment mode and account' },
  { id: 'review', title: 'Review & Submit', description: 'Review and submit request' },
];

export default function DisbursementWizard() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const sanctionId = searchParams.get('sanctionId');
  // Wizard manages steps internally

  const form = useForm<DisbursementFormData>({
    resolver: zodResolver(disbursementSchema),
    defaultValues: {
      sanctionId: sanctionId || '',
      tranche: 2,
      amount: 0,
      paymentMode: 'RTGS',
      bankAccountId: mockSanction.bankAccounts.find((b) => b.isPrimary)?.id || '',
      conditionsVerified: [],
    },
  });

  const {
    watch,
    setValue,
    handleSubmit,
    formState: { errors },
  } = form;

  const selectedMilestone = mockSanction.milestones.find((m) => m.id === watch('milestoneId'));

  const onSubmit = async (data: DisbursementFormData) => {
    logger.debug('Disbursement data:', data);
    navigate('/admin/lending/disbursements');
  };

  const canProceed = (step: number): boolean => {
    switch (step) {
      case 0:
        return Boolean(watch('sanctionId'));
      case 1:
        return watch('conditionsVerified')?.length > 0;
      case 2:
        return watch('amount') > 0;
      case 3:
        return Boolean(watch('bankAccountId'));
      default:
        return true;
    }
  };

  return (
    <WizardContainer
      steps={steps}
      title="New Disbursement Request"
      description="Request disbursement against sanctioned facility"
      onSubmit={handleSubmit(onSubmit) as unknown as () => Promise<void>}
      onCancel={() => navigate('/admin/lending/disbursements')}
      showCancel
    >
      {/* Step 1: Select Sanction */}
      <WizardStep stepId="sanction">
        <Card>
          <CardHeader>
            <CardTitle>Sanction Details</CardTitle>
            <CardDescription>
              Disbursement for sanction {mockSanction.sanctionNumber}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label className="text-muted-foreground">Entity</Label>
                <p className="font-medium">{mockSanction.entityName}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Sanction Number</Label>
                <p className="font-mono">{mockSanction.sanctionNumber}</p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <Label className="text-muted-foreground">Sanctioned Amount</Label>
                <p className="text-lg font-semibold">
                  <AmountDisplay amount={mockSanction.sanctionedAmount} showFull />
                </p>
              </div>
              <div>
                <Label className="text-muted-foreground">Already Disbursed</Label>
                <p className="text-lg font-semibold">
                  <AmountDisplay amount={mockSanction.disbursedAmount} showFull />
                </p>
              </div>
              <div>
                <Label className="text-muted-foreground">Available for Disbursement</Label>
                <p className="text-lg font-semibold text-green-600">
                  <AmountDisplay amount={mockSanction.remainingAmount} showFull />
                </p>
              </div>
            </div>

            <div>
              <Label className="text-muted-foreground">Utilization</Label>
              <div className="mt-2 h-3 overflow-hidden rounded-full bg-gray-200">
                <div
                  className="h-full rounded-full bg-blue-500"
                  style={{
                    width: `${(mockSanction.disbursedAmount / mockSanction.sanctionedAmount) * 100}%`,
                  }}
                />
              </div>
              <p className="mt-1 text-sm text-muted-foreground">
                <PercentageDisplay
                  value={(mockSanction.disbursedAmount / mockSanction.sanctionedAmount) * 100}
                />{' '}
                utilized
              </p>
            </div>

            <input type="hidden" {...form.register('sanctionId')} value={mockSanction.id} />
          </CardContent>
        </Card>
      </WizardStep>

      {/* Step 2: Verify Conditions */}
      <WizardStep stepId="conditions">
        <Card>
          <CardHeader>
            <CardTitle>Pre-Disbursement Conditions</CardTitle>
            <CardDescription>
              Verify that the following conditions have been satisfied
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[50px]">Verify</TableHead>
                  <TableHead>Condition</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {mockSanction.conditions.map((cond) => (
                  <TableRow key={cond.id}>
                    <TableCell>
                      <Checkbox
                        checked={watch('conditionsVerified')?.includes(cond.id)}
                        disabled={cond.status !== 'COMPLETED'}
                        onCheckedChange={(checked) => {
                          const current = watch('conditionsVerified') || [];
                          if (checked) {
                            setValue('conditionsVerified', [...current, cond.id]);
                          } else {
                            setValue(
                              'conditionsVerified',
                              current.filter((id) => id !== cond.id),
                            );
                          }
                        }}
                      />
                    </TableCell>
                    <TableCell>{cond.condition}</TableCell>
                    <TableCell>
                      <Badge
                        variant={cond.status === 'COMPLETED' ? 'default' : 'secondary'}
                        className={cond.status === 'COMPLETED' ? 'bg-green-100 text-green-700' : ''}
                      >
                        {cond.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {errors.conditionsVerified && (
              <p className="mt-2 text-sm text-destructive">{errors.conditionsVerified.message}</p>
            )}
          </CardContent>
        </Card>
      </WizardStep>

      {/* Step 3: Amount & Milestone */}
      <WizardStep stepId="amount">
        <Card>
          <CardHeader>
            <CardTitle>Disbursement Amount</CardTitle>
            <CardDescription>Select milestone and enter disbursement amount</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label>Select Milestone (Optional)</Label>
              <Select
                value={watch('milestoneId') || ''}
                onValueChange={(v) => {
                  setValue('milestoneId', v);
                  const milestone = mockSanction.milestones.find((m) => m.id === v);
                  if (milestone) {
                    setValue('amount', milestone.amount);
                  }
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a milestone" />
                </SelectTrigger>
                <SelectContent>
                  {mockSanction.milestones
                    .filter((m) => m.status === 'PENDING')
                    .map((milestone) => (
                      <SelectItem key={milestone.id} value={milestone.id}>
                        {milestone.milestone} -{' '}
                        <AmountDisplay amount={milestone.amount} abbreviated />
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Disbursement Amount *</Label>
              <AmountInput
                value={watch('amount') || 0}
                onChange={(v) => setValue('amount', v ?? 0)}
                placeholder="Enter amount"
              />
              <p className="text-sm text-muted-foreground">
                Maximum available:{' '}
                <AmountDisplay amount={mockSanction.remainingAmount} abbreviated />
              </p>
              {errors.amount && <p className="text-sm text-destructive">{errors.amount.message}</p>}
            </div>

            {selectedMilestone && (
              <div className="rounded-lg bg-muted p-4">
                <h4 className="font-medium">Selected Milestone</h4>
                <p className="mt-1 text-sm text-muted-foreground">{selectedMilestone.milestone}</p>
                <p className="mt-1 text-sm">
                  Budgeted Amount: <AmountDisplay amount={selectedMilestone.amount} showFull />
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </WizardStep>

      {/* Step 4: Payment Details */}
      <WizardStep stepId="payment">
        <Card>
          <CardHeader>
            <CardTitle>Payment Details</CardTitle>
            <CardDescription>Select payment mode and beneficiary account</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label>Payment Mode *</Label>
              <Select
                value={watch('paymentMode')}
                onValueChange={(v) =>
                  setValue('paymentMode', v as DisbursementFormData['paymentMode'])
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select payment mode" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="RTGS">RTGS</SelectItem>
                  <SelectItem value="NEFT">NEFT</SelectItem>
                  <SelectItem value="IMPS">IMPS</SelectItem>
                  <SelectItem value="CHEQUE">Cheque</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Beneficiary Bank Account *</Label>
              <div className="space-y-2">
                {mockSanction.bankAccounts.map((account) => (
                  <div
                    key={account.id}
                    className={`cursor-pointer rounded-lg border p-4 transition-colors ${
                      watch('bankAccountId') === account.id
                        ? 'border-primary bg-primary/5'
                        : 'hover:border-primary/50'
                    }`}
                    onClick={() => setValue('bankAccountId', account.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{account.bankName}</p>
                        <p className="text-sm text-muted-foreground">
                          A/c: {account.accountNumber} | IFSC: {account.ifsc}
                        </p>
                      </div>
                      {account.isPrimary && <Badge variant="outline">Primary</Badge>}
                    </div>
                  </div>
                ))}
              </div>
              {errors.bankAccountId && (
                <p className="text-sm text-destructive">{errors.bankAccountId.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label>Remarks</Label>
              <Textarea
                {...form.register('remarks')}
                placeholder="Any additional remarks..."
                rows={3}
              />
            </div>
          </CardContent>
        </Card>
      </WizardStep>

      {/* Step 5: Review */}
      <WizardStep stepId="review">
        <Card>
          <CardHeader>
            <CardTitle>Review Disbursement Request</CardTitle>
            <CardDescription>Please review all details before submitting</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label className="text-muted-foreground">Entity</Label>
                <p className="font-medium">{mockSanction.entityName}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Sanction Number</Label>
                <p className="font-mono">{mockSanction.sanctionNumber}</p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <Label className="text-muted-foreground">Disbursement Amount</Label>
                <p className="text-xl font-bold text-green-600">
                  <AmountDisplay amount={watch('amount')} showFull />
                </p>
              </div>
              <div>
                <Label className="text-muted-foreground">Payment Mode</Label>
                <p className="font-medium">{watch('paymentMode')}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Tranche</Label>
                <p className="font-medium">{watch('tranche')}</p>
              </div>
            </div>

            {selectedMilestone && (
              <div>
                <Label className="text-muted-foreground">Milestone</Label>
                <p className="font-medium">{selectedMilestone.milestone}</p>
              </div>
            )}

            <div>
              <Label className="text-muted-foreground">Beneficiary Account</Label>
              {(() => {
                const account = mockSanction.bankAccounts.find(
                  (a) => a.id === watch('bankAccountId'),
                );
                return account ? (
                  <p className="font-medium">
                    {account.bankName} - {account.accountNumber}
                  </p>
                ) : null;
              })()}
            </div>

            <div>
              <Label className="text-muted-foreground">Conditions Verified</Label>
              <p className="font-medium">
                {watch('conditionsVerified')?.length || 0} of {mockSanction.conditions.length}{' '}
                conditions
              </p>
            </div>

            {watch('remarks') && (
              <div>
                <Label className="text-muted-foreground">Remarks</Label>
                <p>{watch('remarks')}</p>
              </div>
            )}

            <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
              <p className="text-sm text-yellow-800">
                By submitting this request, you confirm that all pre-disbursement conditions have
                been verified and the disbursement is in accordance with the sanction terms.
              </p>
            </div>
          </CardContent>
        </Card>
      </WizardStep>
    </WizardContainer>
  );
}
