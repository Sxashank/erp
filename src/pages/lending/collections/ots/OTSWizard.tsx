import { zodResolver } from '@hookform/resolvers/zod';
import { Plus, Trash2 } from 'lucide-react';
import { useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { z } from 'zod';

import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { AmountInput } from '@/components/lending/common/AmountInput';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { DPDBadge } from '@/components/lending/common/DPDBadge';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { StatusBadge } from '@/components/lending/common/StatusBadge';
import { WizardContainer } from '@/components/lending/wizard/WizardContainer';
import { WizardStep } from '@/components/lending/wizard/WizardStep';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
const otsSchema = z.object({
  loanAccountId: z.string().min(1, 'Account is required'),
  settlementAmount: z.number().min(1, 'Settlement amount is required'),
  paymentMode: z.enum(['LUMPSUM', 'STRUCTURED']),
  validityDays: z.number().min(1),
  paymentSchedule: z
    .array(
      z.object({
        installment: z.number(),
        dueDate: z.string(),
        amount: z.number(),
      }),
    )
    .optional(),
  justification: z.string().min(10, 'Please provide detailed justification'),
  recoveryProspects: z.string().optional(),
  remarks: z.string().optional(),
});

type OTSFormData = z.infer<typeof otsSchema>;

// Loan account context is keyed off `?accountId=` in the URL. The wizard
// renders with zeroed defaults until the BE endpoint that prefills the
// NPA account snapshot (outstanding, classification, collection history)
// is wired. For now, the user enters figures manually.
const emptyNPAAccount = {
  id: '',
  loanAccountNumber: '',
  entityName: '',
  entityCode: '',
  productName: '',
  principalOutstanding: 0,
  interestOutstanding: 0,
  penalOutstanding: 0,
  totalOutstanding: 0,
  dpd: 0,
  classification: '',
  npaDate: '',
  collectionHistory: [] as { date: string; amount: number; remarks: string }[],
  securityValue: 0,
  securityType: '',
};
const mockNPAAccount = emptyNPAAccount;

const steps = [
  { id: 'account', title: 'Account Selection', description: 'Select NPA account' },
  { id: 'settlement', title: 'Settlement Terms', description: 'Define settlement amount' },
  { id: 'payment', title: 'Payment Schedule', description: 'Configure payment terms' },
  { id: 'justification', title: 'Justification', description: 'Provide rationale' },
  { id: 'review', title: 'Review & Submit', description: 'Review proposal' },
];

export default function OTSWizard() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const accountId = searchParams.get('accountId');
  // Wizard manages steps internally

  const form = useForm<OTSFormData>({
    resolver: zodResolver(otsSchema),
    defaultValues: {
      loanAccountId: accountId || mockNPAAccount.id,
      settlementAmount: Math.round(mockNPAAccount.totalOutstanding * 0.7), // Default 70% settlement
      paymentMode: 'LUMPSUM',
      validityDays: 90,
      paymentSchedule: [],
    },
  });

  const {
    watch,
    setValue,
    handleSubmit,
    register,
    formState: { errors },
  } = form;

  const {
    fields: scheduleFields,
    append: appendSchedule,
    remove: removeSchedule,
  } = useFieldArray({
    control: form.control,
    name: 'paymentSchedule',
  });

  const paymentMode = watch('paymentMode');
  const settlementAmount = watch('settlementAmount') || 0;
  const discountPercent =
    ((mockNPAAccount.totalOutstanding - settlementAmount) / mockNPAAccount.totalOutstanding) * 100;
  const haircut = mockNPAAccount.totalOutstanding - settlementAmount;

  const totalScheduled = scheduleFields.reduce(
    (sum, _, index) => sum + (watch(`paymentSchedule.${index}.amount`) || 0),
    0,
  );

  const onSubmit = async (data: OTSFormData) => {
    logger.debug('OTS data:', data);
    navigate('/admin/lending/collections/ots');
  };

  const canProceed = (step: number): boolean => {
    switch (step) {
      case 0:
        return Boolean(watch('loanAccountId'));
      case 1:
        return settlementAmount > 0 && settlementAmount <= mockNPAAccount.totalOutstanding;
      case 2:
        if (paymentMode === 'LUMPSUM') return true;
        return totalScheduled === settlementAmount && scheduleFields.length > 0;
      case 3:
        return (watch('justification')?.length || 0) >= 10;
      default:
        return true;
    }
  };

  return (
    <WizardContainer
      steps={steps}
      title="New OTS Proposal"
      description="Create one-time settlement proposal for NPA recovery"
      onSubmit={handleSubmit(onSubmit) as unknown as () => Promise<void>}
      onCancel={() => navigate('/admin/lending/collections/ots')}
      showCancel
    >
      {/* Step 1: Account Selection */}
      <WizardStep stepId="account">
        <Card>
          <CardHeader>
            <CardTitle>NPA Account Details</CardTitle>
            <CardDescription>Account selected for OTS proposal</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label className="text-muted-foreground">Account Number</Label>
                <p className="font-mono font-medium">{mockNPAAccount.loanAccountNumber}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Entity</Label>
                <p className="font-medium">{mockNPAAccount.entityName}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Product</Label>
                <p>{mockNPAAccount.productName}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">NPA Date</Label>
                <p>
                  <DateDisplay date={mockNPAAccount.npaDate} />
                </p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <Label className="text-muted-foreground">DPD</Label>
                <DPDBadge dpd={mockNPAAccount.dpd} size="lg" />
              </div>
              <div>
                <Label className="text-muted-foreground">Classification</Label>
                <StatusBadge status={mockNPAAccount.classification} type="classification" />
              </div>
              <div>
                <Label className="text-muted-foreground">Security Value</Label>
                <p>
                  <AmountDisplay amount={mockNPAAccount.securityValue} showFull />
                </p>
              </div>
            </div>

            <div className="border-t pt-4">
              <h4 className="mb-3 font-medium">Outstanding Breakdown</h4>
              <Table>
                <TableBody>
                  <TableRow>
                    <TableCell>Principal Outstanding</TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={mockNPAAccount.principalOutstanding} showFull />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Interest Outstanding</TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={mockNPAAccount.interestOutstanding} showFull />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Penal Interest</TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={mockNPAAccount.penalOutstanding} showFull />
                    </TableCell>
                  </TableRow>
                  <TableRow className="bg-muted/50 font-bold">
                    <TableCell>Total Outstanding</TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={mockNPAAccount.totalOutstanding} showFull />
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>

            <input type="hidden" {...register('loanAccountId')} value={mockNPAAccount.id} />
          </CardContent>
        </Card>
      </WizardStep>

      {/* Step 2: Settlement Terms */}
      <WizardStep stepId="settlement">
        <Card>
          <CardHeader>
            <CardTitle>Settlement Amount</CardTitle>
            <CardDescription>Define the proposed settlement amount</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label className="text-muted-foreground">Total Outstanding</Label>
                <p className="text-2xl font-bold">
                  <AmountDisplay amount={mockNPAAccount.totalOutstanding} showFull />
                </p>
              </div>
              <div className="space-y-2">
                <Label>Proposed Settlement Amount *</Label>
                <AmountInput
                  value={settlementAmount}
                  onChange={(v) => setValue('settlementAmount', v ?? 0)}
                  placeholder="Enter settlement amount"
                />
                {errors.settlementAmount && (
                  <p className="text-sm text-destructive">{errors.settlementAmount.message}</p>
                )}
              </div>
            </div>

            <div className="grid gap-4 rounded-lg bg-muted p-4 md:grid-cols-3">
              <div className="text-center">
                <Label className="text-muted-foreground">Settlement %</Label>
                <p className="text-2xl font-bold text-green-600">
                  <PercentageDisplay value={100 - discountPercent} />
                </p>
              </div>
              <div className="text-center">
                <Label className="text-muted-foreground">Discount %</Label>
                <p className="text-2xl font-bold text-amber-600">
                  <PercentageDisplay value={discountPercent} />
                </p>
              </div>
              <div className="text-center">
                <Label className="text-muted-foreground">Haircut Amount</Label>
                <p className="text-2xl font-bold text-red-600">
                  <AmountDisplay amount={haircut} abbreviated />
                </p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label>Payment Mode *</Label>
                <Select
                  value={paymentMode}
                  onValueChange={(v) => setValue('paymentMode', v as 'LUMPSUM' | 'STRUCTURED')}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="LUMPSUM">Lumpsum Payment</SelectItem>
                    <SelectItem value="STRUCTURED">Structured Payment</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="validityDays">Validity Period (Days)</Label>
                <Input
                  id="validityDays"
                  type="number"
                  min={30}
                  max={180}
                  {...register('validityDays', { valueAsNumber: true })}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </WizardStep>

      {/* Step 3: Payment Schedule */}
      <WizardStep stepId="payment">
        <Card>
          <CardHeader>
            <CardTitle>Payment Schedule</CardTitle>
            <CardDescription>
              {paymentMode === 'LUMPSUM'
                ? 'Lumpsum payment to be made within the validity period'
                : 'Define the structured payment schedule'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {paymentMode === 'LUMPSUM' ? (
              <div className="rounded-lg border border-green-200 bg-green-50 p-6 text-center">
                <p className="text-lg font-medium">Lumpsum Settlement</p>
                <p className="mt-2 text-3xl font-bold text-green-600">
                  <AmountDisplay amount={settlementAmount} showFull />
                </p>
                <p className="mt-2 text-sm text-muted-foreground">
                  To be paid within {watch('validityDays')} days of approval
                </p>
              </div>
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[80px]">#</TableHead>
                      <TableHead>Due Date</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {scheduleFields.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={4} className="py-8 text-center text-muted-foreground">
                          No payment schedule defined. Click "Add Installment" to create.
                        </TableCell>
                      </TableRow>
                    ) : (
                      scheduleFields.map((field, index) => (
                        <TableRow key={field.id}>
                          <TableCell>{index + 1}</TableCell>
                          <TableCell>
                            <Input type="date" {...register(`paymentSchedule.${index}.dueDate`)} />
                          </TableCell>
                          <TableCell className="text-right">
                            <Input
                              type="number"
                              {...register(`paymentSchedule.${index}.amount`, {
                                valueAsNumber: true,
                              })}
                              className="w-[150px] text-right"
                            />
                          </TableCell>
                          <TableCell>
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              onClick={() => removeSchedule(index)}
                            >
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                    {scheduleFields.length > 0 && (
                      <TableRow className="bg-muted/50 font-medium">
                        <TableCell colSpan={2}>Total Scheduled</TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={totalScheduled} />
                        </TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>

                <div className="flex items-center justify-between">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() =>
                      appendSchedule({
                        installment: scheduleFields.length + 1,
                        dueDate: '',
                        amount: 0,
                      })
                    }
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Add Installment
                  </Button>

                  {scheduleFields.length > 0 && (
                    <div
                      className={`text-sm font-medium ${
                        totalScheduled === settlementAmount ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {totalScheduled === settlementAmount
                        ? 'Schedule matches settlement amount ✓'
                        : `Difference: ${(settlementAmount - totalScheduled).toLocaleString('en-IN')}`}
                    </div>
                  )}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </WizardStep>

      {/* Step 4: Justification */}
      <WizardStep stepId="justification">
        <Card>
          <CardHeader>
            <CardTitle>Justification & Rationale</CardTitle>
            <CardDescription>Provide detailed justification for the OTS proposal</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="justification">Justification for Settlement *</Label>
              <Textarea
                id="justification"
                {...register('justification')}
                placeholder="Explain why this settlement is recommended..."
                rows={5}
              />
              {errors.justification && (
                <p className="text-sm text-destructive">{errors.justification.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="recoveryProspects">Recovery Prospects Analysis</Label>
              <Textarea
                id="recoveryProspects"
                {...register('recoveryProspects')}
                placeholder="Analyze the recovery prospects through legal action vs settlement..."
                rows={4}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="remarks">Additional Remarks</Label>
              <Textarea
                id="remarks"
                {...register('remarks')}
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
            <CardTitle>Review OTS Proposal</CardTitle>
            <CardDescription>Please review all details before submitting</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label className="text-muted-foreground">Account</Label>
                <p className="font-mono">{mockNPAAccount.loanAccountNumber}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Entity</Label>
                <p className="font-medium">{mockNPAAccount.entityName}</p>
              </div>
            </div>

            <div className="grid gap-4 rounded-lg bg-muted p-4 md:grid-cols-4">
              <div>
                <Label className="text-muted-foreground">Outstanding</Label>
                <p className="font-medium">
                  <AmountDisplay amount={mockNPAAccount.totalOutstanding} abbreviated />
                </p>
              </div>
              <div>
                <Label className="text-muted-foreground">Settlement</Label>
                <p className="font-medium text-green-600">
                  <AmountDisplay amount={settlementAmount} abbreviated />
                </p>
              </div>
              <div>
                <Label className="text-muted-foreground">Discount</Label>
                <p className="font-medium text-amber-600">
                  <PercentageDisplay value={discountPercent} />
                </p>
              </div>
              <div>
                <Label className="text-muted-foreground">Haircut</Label>
                <p className="font-medium text-red-600">
                  <AmountDisplay amount={haircut} abbreviated />
                </p>
              </div>
            </div>

            <div>
              <Label className="text-muted-foreground">Payment Mode</Label>
              <p className="font-medium">
                {paymentMode === 'LUMPSUM' ? 'Lumpsum Payment' : 'Structured Payment'}
                {paymentMode === 'STRUCTURED' && ` (${scheduleFields.length} installments)`}
              </p>
            </div>

            <div>
              <Label className="text-muted-foreground">Validity</Label>
              <p className="font-medium">{watch('validityDays')} days from approval</p>
            </div>

            <div>
              <Label className="text-muted-foreground">Justification</Label>
              <p className="text-sm">{watch('justification')}</p>
            </div>

            <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
              <p className="text-sm text-yellow-800">
                By submitting this proposal, you confirm that all details are accurate and the
                settlement is in the best interest of the company considering the recovery
                prospects.
              </p>
            </div>
          </CardContent>
        </Card>
      </WizardStep>
    </WizardContainer>
  );
}
