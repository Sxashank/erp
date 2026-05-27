import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, Plus, Trash2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useFieldArray, useForm } from 'react-hook-form';
import type { Resolver } from 'react-hook-form';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { z } from 'zod';

import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
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
import { masterRowsToOptions, useLendingOptionRows } from '@/hooks/lending/useLendingMasters';
import { useNPAAccounts } from '@/hooks/lending/useNPAAccounts';
import { collectionApi } from '@/services/lending/collectionApi';

const otsSchema = z.object({
  loanAccountId: z.string().min(1, 'Account is required'),
  principalOutstanding: z.coerce.number().min(0),
  interestOutstanding: z.coerce.number().min(0),
  penalOutstanding: z.coerce.number().min(0),
  otherCharges: z.coerce.number().min(0),
  settlementAmount: z.coerce.number().min(1, 'Settlement amount is required'),
  paymentMode: z.string().min(1, 'Payment mode is required'),
  validityDays: z.coerce.number().int().min(1),
  paymentSchedule: z
    .array(
      z.object({
        installment: z.number(),
        dueDate: z.string(),
        amount: z.coerce.number(),
      }),
    )
    .optional(),
  justification: z.string().min(10, 'Please provide detailed justification'),
  recoveryProspects: z.string().optional(),
  remarks: z.string().optional(),
});

type OTSFormData = z.infer<typeof otsSchema>;

const steps = [
  { id: 'account', title: 'Account Selection', description: 'Select NPA account' },
  { id: 'settlement', title: 'Settlement Terms', description: 'Define settlement amount' },
  { id: 'payment', title: 'Payment Schedule', description: 'Configure payment terms' },
  { id: 'justification', title: 'Justification', description: 'Provide rationale' },
  { id: 'review', title: 'Review & Submit', description: 'Review proposal' },
];

function addDays(date: Date, days: number): string {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result.toISOString().split('T')[0];
}

function allocateHaircut(
  haircut: number,
  principal: number,
  interest: number,
  penal: number,
  charges: number,
) {
  const interestWaiver = Math.min(interest, haircut);
  let remaining = haircut - interestWaiver;
  const penalWaiver = Math.min(penal, remaining);
  remaining -= penalWaiver;
  const chargesWaiver = Math.min(charges, remaining);
  remaining -= chargesWaiver;
  const principalWaiver = Math.min(principal, Math.max(remaining, 0));
  return { principalWaiver, interestWaiver, penalWaiver, chargesWaiver };
}

export default function OTSWizard() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const accountId = searchParams.get('accountId');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const npaQuery = useNPAAccounts({ pageSize: 200 });
  const paymentModeRows = useLendingOptionRows('OTS_PAYMENT_MODE');
  const paymentModes = masterRowsToOptions(paymentModeRows.data?.items);

  const form = useForm<OTSFormData>({
    resolver: zodResolver(otsSchema) as Resolver<OTSFormData>,
    defaultValues: {
      loanAccountId: accountId || '',
      principalOutstanding: 0,
      interestOutstanding: 0,
      penalOutstanding: 0,
      otherCharges: 0,
      settlementAmount: 0,
      paymentMode: '',
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

  const selectedLoanAccountId = watch('loanAccountId');
  const selectedAccount = useMemo(() => {
    const selectedId = selectedLoanAccountId;
    return (npaQuery.data?.items ?? []).find(
      (account) => account.loanAccountId === selectedId || account.id === selectedId,
    );
  }, [npaQuery.data?.items, selectedLoanAccountId]);

  useEffect(() => {
    if (!accountId || !npaQuery.data?.items?.length) return;
    const account = npaQuery.data.items.find(
      (item) => item.id === accountId || item.loanAccountId === accountId,
    );
    if (account) {
      handleAccountSelect(account.loanAccountId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accountId, npaQuery.data?.items]);

  useEffect(() => {
    if (!watch('paymentMode') && paymentModes[0]?.value) {
      setValue('paymentMode', paymentModes[0].value);
    }
  }, [paymentModes, setValue, watch]);

  const principalOutstanding = watch('principalOutstanding') || 0;
  const interestOutstanding = watch('interestOutstanding') || 0;
  const penalOutstanding = watch('penalOutstanding') || 0;
  const otherCharges = watch('otherCharges') || 0;
  const totalOutstanding =
    principalOutstanding + interestOutstanding + penalOutstanding + otherCharges;
  const paymentMode = watch('paymentMode');
  const settlementAmount = watch('settlementAmount') || 0;
  const discountPercent =
    totalOutstanding > 0 ? ((totalOutstanding - settlementAmount) / totalOutstanding) * 100 : 0;
  const haircut = Math.max(totalOutstanding - settlementAmount, 0);

  const totalScheduled = scheduleFields.reduce(
    (sum, _, index) => sum + (watch(`paymentSchedule.${index}.amount`) || 0),
    0,
  );

  function handleAccountSelect(loanAccountId: string) {
    const account = (npaQuery.data?.items ?? []).find(
      (item) => item.loanAccountId === loanAccountId || item.id === loanAccountId,
    );
    setValue('loanAccountId', loanAccountId);
    if (!account) return;

    const principal = Number(account.principalOutstanding);
    const total = Number(account.totalOutstanding);
    const interest = Math.max(total - principal, 0);
    setValue('principalOutstanding', principal);
    setValue('interestOutstanding', interest);
    setValue('penalOutstanding', 0);
    setValue('otherCharges', 0);
    setValue('settlementAmount', Math.round(total * 0.7));
  }

  const onSubmit = async (data: OTSFormData) => {
    setIsSubmitting(true);
    try {
      const total =
        data.principalOutstanding +
        data.interestOutstanding +
        data.penalOutstanding +
        data.otherCharges;
      const waiver = allocateHaircut(
        Math.max(total - data.settlementAmount, 0),
        data.principalOutstanding,
        data.interestOutstanding,
        data.penalOutstanding,
        data.otherCharges,
      );
      const schedule =
        data.paymentMode === 'INSTALLMENTS' || data.paymentMode === 'HYBRID'
          ? (data.paymentSchedule ?? []).map((item, index) => ({
              installmentNumber: item.installment || index + 1,
              dueDate: item.dueDate,
              dueAmount: item.amount,
            }))
          : undefined;

      await collectionApi.createOTSProposal(
        {
          loanAccountId: data.loanAccountId,
          proposalDate: new Date().toISOString().split('T')[0],
          principalOutstanding: data.principalOutstanding,
          interestOutstanding: data.interestOutstanding,
          penalOutstanding: data.penalOutstanding,
          otherCharges: data.otherCharges,
          totalOutstanding: total,
          otsAmount: data.settlementAmount,
          ...waiver,
          paymentMode: data.paymentMode,
          upfrontAmount: data.paymentMode === 'LUMP_SUM' ? data.settlementAmount : 0,
          upfrontDueDate:
            data.paymentMode === 'LUMP_SUM' ? addDays(new Date(), data.validityDays) : null,
          numberOfInstallments: schedule?.length || 1,
          validTill: addDays(new Date(), data.validityDays),
          termsAndConditions: data.recoveryProspects,
          remarks: data.remarks || data.justification,
        },
        schedule,
      );
      navigate('/admin/lending/collections/ots');
    } finally {
      setIsSubmitting(false);
    }
  };

  const canProceed = (step: number): boolean => {
    switch (step) {
      case 0:
        return Boolean(watch('loanAccountId')) && totalOutstanding > 0;
      case 1:
        return settlementAmount > 0 && settlementAmount <= totalOutstanding && Boolean(paymentMode);
      case 2:
        if (paymentMode === 'LUMP_SUM') return true;
        return totalScheduled === settlementAmount && scheduleFields.length > 0;
      case 3:
        return (watch('justification')?.length || 0) >= 10;
      default:
        return true;
    }
  };

  if (npaQuery.isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-16 text-muted-foreground">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Loading NPA accounts...
        </CardContent>
      </Card>
    );
  }

  if (npaQuery.isError) {
    return (
      <ErrorState
        title="Could not load NPA accounts"
        error={npaQuery.error}
        onRetry={() => npaQuery.refetch()}
      />
    );
  }

  if ((npaQuery.data?.items ?? []).length === 0) {
    return (
      <EmptyState
        title="No NPA accounts available"
        subtitle="Create an OTS proposal only after a real loan account is classified as NPA."
        action={
          <Button variant="outline" onClick={() => navigate('/admin/lending/collections/ots')}>
            Back to OTS
          </Button>
        }
      />
    );
  }

  return (
    <WizardContainer
      steps={steps}
      title="New OTS Proposal"
      description="Create one-time settlement proposal for NPA recovery"
      onSubmit={handleSubmit(onSubmit) as unknown as () => Promise<void>}
      onCancel={() => navigate('/admin/lending/collections/ots')}
      showCancel
    >
      <WizardStep stepId="account">
        <Card>
          <CardHeader>
            <CardTitle>NPA Account Details</CardTitle>
            <CardDescription>
              Select a real NPA account and confirm outstanding values
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label>Loan Account *</Label>
              <Select value={watch('loanAccountId')} onValueChange={handleAccountSelect}>
                <SelectTrigger>
                  <SelectValue placeholder="Select NPA loan account" />
                </SelectTrigger>
                <SelectContent>
                  {(npaQuery.data?.items ?? []).map((account) => (
                    <SelectItem key={account.loanAccountId} value={account.loanAccountId}>
                      {account.loanAccountNumber} - {account.entityName ?? 'Unnamed entity'}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.loanAccountId && (
                <p className="text-sm text-destructive">{errors.loanAccountId.message}</p>
              )}
            </div>

            {selectedAccount && (
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label className="text-muted-foreground">Account Number</Label>
                  <p className="font-mono font-medium">{selectedAccount.loanAccountNumber}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Entity</Label>
                  <p className="font-medium">{selectedAccount.entityName ?? '—'}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Product</Label>
                  <p>{selectedAccount.productName ?? '—'}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">NPA Date</Label>
                  <p>
                    {selectedAccount.npaDate ? <DateDisplay date={selectedAccount.npaDate} /> : '—'}
                  </p>
                </div>
                <div>
                  <Label className="text-muted-foreground">DPD</Label>
                  <DPDBadge dpd={selectedAccount.daysPastDue} size="lg" />
                </div>
                <div>
                  <Label className="text-muted-foreground">Classification</Label>
                  <StatusBadge status={selectedAccount.classification} type="classification" />
                </div>
              </div>
            )}

            <div className="grid gap-4 md:grid-cols-4">
              <div className="space-y-2">
                <Label>Principal Outstanding</Label>
                <Input
                  type="number"
                  {...register('principalOutstanding', { valueAsNumber: true })}
                />
              </div>
              <div className="space-y-2">
                <Label>Interest Outstanding</Label>
                <Input
                  type="number"
                  {...register('interestOutstanding', { valueAsNumber: true })}
                />
              </div>
              <div className="space-y-2">
                <Label>Penal Outstanding</Label>
                <Input type="number" {...register('penalOutstanding', { valueAsNumber: true })} />
              </div>
              <div className="space-y-2">
                <Label>Other Charges</Label>
                <Input type="number" {...register('otherCharges', { valueAsNumber: true })} />
              </div>
            </div>

            <div className="rounded-lg bg-muted p-4">
              <Label className="text-muted-foreground">Total Outstanding</Label>
              <p className="text-2xl font-bold">
                <AmountDisplay amount={totalOutstanding} showFull />
              </p>
            </div>
          </CardContent>
        </Card>
      </WizardStep>

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
                  <AmountDisplay amount={totalOutstanding} showFull />
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
                  <PercentageDisplay value={Math.max(100 - discountPercent, 0)} />
                </p>
              </div>
              <div className="text-center">
                <Label className="text-muted-foreground">Discount %</Label>
                <p className="text-2xl font-bold text-amber-600">
                  <PercentageDisplay value={Math.max(discountPercent, 0)} />
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
                <Select value={paymentMode} onValueChange={(v) => setValue('paymentMode', v)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select payment mode" />
                  </SelectTrigger>
                  <SelectContent>
                    {paymentModes.map((mode) => (
                      <SelectItem key={mode.value} value={mode.value}>
                        {mode.label}
                      </SelectItem>
                    ))}
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

      <WizardStep stepId="payment">
        <Card>
          <CardHeader>
            <CardTitle>Payment Schedule</CardTitle>
            <CardDescription>
              {paymentMode === 'LUMP_SUM'
                ? 'Lump sum payment to be made within the validity period'
                : 'Define the structured payment schedule'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {paymentMode === 'LUMP_SUM' ? (
              <div className="rounded-lg border border-green-200 bg-green-50 p-6 text-center">
                <p className="text-lg font-medium">Lump Sum Settlement</p>
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
                          No payment schedule defined. Add installments to continue.
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
                        ? 'Schedule matches settlement amount'
                        : `Difference: ${(settlementAmount - totalScheduled).toLocaleString('en-IN')}`}
                    </div>
                  )}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </WizardStep>

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
              <Textarea id="remarks" {...register('remarks')} rows={3} />
            </div>
          </CardContent>
        </Card>
      </WizardStep>

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
                <p className="font-mono">
                  {selectedAccount?.loanAccountNumber ?? watch('loanAccountId')}
                </p>
              </div>
              <div>
                <Label className="text-muted-foreground">Entity</Label>
                <p className="font-medium">{selectedAccount?.entityName ?? '—'}</p>
              </div>
            </div>

            <div className="grid gap-4 rounded-lg bg-muted p-4 md:grid-cols-4">
              <div>
                <Label className="text-muted-foreground">Outstanding</Label>
                <p className="font-medium">
                  <AmountDisplay amount={totalOutstanding} abbreviated />
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
                  <PercentageDisplay value={Math.max(discountPercent, 0)} />
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
                {paymentModes.find((mode) => mode.value === paymentMode)?.label ?? paymentMode}
                {paymentMode !== 'LUMP_SUM' && ` (${scheduleFields.length} installments)`}
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
                settlement is in the best interest of the company considering recovery prospects.
              </p>
            </div>

            {isSubmitting && (
              <div className="flex items-center text-sm text-muted-foreground">
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Submitting OTS proposal...
              </div>
            )}
          </CardContent>
        </Card>
      </WizardStep>
    </WizardContainer>
  );
}
