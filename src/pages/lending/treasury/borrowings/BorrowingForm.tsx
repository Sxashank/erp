import { zodResolver } from '@hookform/resolvers/zod';
import { Save, Loader2 } from 'lucide-react';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/use-toast';
import {
  useBorrowing,
  useCreateBorrowing,
  useUpdateBorrowing,
} from '@/hooks/lending/useBorrowings';
import { useLenders } from '@/hooks/lending/useLenders';
import { useLendingMasterRows, useLendingOptionRows } from '@/hooks/lending/useLendingMasters';
import {
  borrowingDetailToFormValues,
  borrowingFormSchema,
  borrowingFormToRequest,
  defaultBorrowingFormValues,
  type BorrowingFormData,
  type BorrowingFormInput,
} from '@/schemas/lending/treasuryBorrowingSchema';

function toOptions(
  rows: { data: Record<string, unknown> }[] | undefined,
  labelKey: 'label' | 'name' = 'label',
) {
  return (
    rows?.map((row) => ({
      value: String(row.data.code ?? ''),
      label: String(row.data[labelKey] ?? row.data.label ?? row.data.name ?? row.data.code ?? ''),
    })) ?? []
  );
}

export default function BorrowingForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { toast } = useToast();
  const isEditMode = Boolean(id);
  const {
    data: borrowing,
    isLoading: isBorrowingLoading,
    isError: isBorrowingError,
    error: borrowingError,
    refetch: refetchBorrowing,
  } = useBorrowing(id);
  const {
    data: lendersResponse,
    isLoading: isLendersLoading,
    isError: isLendersError,
    error: lendersError,
    refetch: refetchLenders,
  } = useLenders({ pageSize: 200 });
  const borrowingTypesQuery = useLendingOptionRows('BORROWING_TYPE');
  const rateTypesQuery = useLendingOptionRows('RATE_TYPE');
  const repaymentFrequenciesQuery = useLendingOptionRows('REPAYMENT_FREQUENCY');
  const securityTypesQuery = useLendingOptionRows('SECURITY_TYPE');
  const dayCountConventionsQuery = useLendingMasterRows('day-count-conventions', {
    pageSize: 100,
  });
  const rateBenchmarksQuery = useLendingMasterRows('rate-reset-benchmarks', {
    pageSize: 100,
  });
  const createBorrowingMutation = useCreateBorrowing();
  const updateBorrowingMutation = useUpdateBorrowing();
  const saving = createBorrowingMutation.isPending || updateBorrowingMutation.isPending;
  const lenders = lendersResponse?.items ?? [];
  const borrowingTypeOptions = toOptions(borrowingTypesQuery.data?.items);
  const rateTypeOptions = toOptions(rateTypesQuery.data?.items);
  const repaymentFrequencyOptions = toOptions(repaymentFrequenciesQuery.data?.items);
  const rateResetFrequencyOptions = repaymentFrequencyOptions.filter(
    (option) => option.value !== 'BULLET',
  );
  const securityTypeOptions = toOptions(securityTypesQuery.data?.items);
  const dayCountConventionOptions = toOptions(dayCountConventionsQuery.data?.items, 'name');
  const rateBenchmarkOptions = toOptions(rateBenchmarksQuery.data?.items, 'name');

  const form = useForm<BorrowingFormInput, unknown, BorrowingFormData>({
    resolver: zodResolver(borrowingFormSchema),
    defaultValues: defaultBorrowingFormValues(),
  });

  const rateType = form.watch('rateType');
  const baseRateValue = form.watch('baseRateValue');
  const spreadBps = form.watch('spreadBps');

  // Auto-calculate effective rate for floating
  useEffect(() => {
    if (rateType === 'FLOATING' && baseRateValue !== undefined && spreadBps !== undefined) {
      const effectiveRate = baseRateValue + spreadBps / 100;
      form.setValue('effectiveRate', Number(effectiveRate.toFixed(4)));
    }
  }, [rateType, baseRateValue, spreadBps, form]);

  useEffect(() => {
    if (borrowing) {
      form.reset(borrowingDetailToFormValues(borrowing));
      return;
    }
    if (!isEditMode) {
      form.reset(defaultBorrowingFormValues());
    }
  }, [borrowing, form, isEditMode]);

  const onSubmit = async (data: BorrowingFormData) => {
    try {
      const selectedLender = lenders.find((lender) => lender.id === data.lenderId);
      if (!selectedLender) {
        throw new Error('Selected lender is not available in the lender list');
      }

      const payload = borrowingFormToRequest(data);

      if (isEditMode && id) {
        await updateBorrowingMutation.mutateAsync({ borrowingId: id, payload });
        toast({
          title: 'Success',
          description: 'Borrowing updated successfully',
        });
      } else {
        const newBorrowing = await createBorrowingMutation.mutateAsync(payload);
        toast({
          title: 'Success',
          description: 'Borrowing created successfully',
        });
        navigate(`/admin/treasury/borrowings/${newBorrowing.borrowingId}`);
        return;
      }
      navigate('/admin/treasury/borrowings');
    } catch {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: `Failed to ${isEditMode ? 'update' : 'create'} borrowing`,
      });
    }
  };

  const isMasterLoading =
    borrowingTypesQuery.isLoading ||
    rateTypesQuery.isLoading ||
    repaymentFrequenciesQuery.isLoading ||
    securityTypesQuery.isLoading ||
    dayCountConventionsQuery.isLoading ||
    rateBenchmarksQuery.isLoading;

  if (isLendersLoading || isMasterLoading || (isEditMode && isBorrowingLoading)) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (isLendersError) {
    return (
      <ErrorState
        title="Could not load treasury lenders"
        error={lendersError}
        onRetry={() => void refetchLenders()}
      />
    );
  }

  const firstMasterError =
    borrowingTypesQuery.error ??
    rateTypesQuery.error ??
    repaymentFrequenciesQuery.error ??
    securityTypesQuery.error ??
    dayCountConventionsQuery.error ??
    rateBenchmarksQuery.error;

  if (firstMasterError) {
    return (
      <ErrorState
        title="Could not load borrowing master data"
        error={firstMasterError}
        onRetry={() => {
          borrowingTypesQuery.refetch();
          rateTypesQuery.refetch();
          repaymentFrequenciesQuery.refetch();
          securityTypesQuery.refetch();
          dayCountConventionsQuery.refetch();
          rateBenchmarksQuery.refetch();
        }}
      />
    );
  }

  if (isEditMode && isBorrowingError) {
    return (
      <ErrorState
        title="Could not load borrowing details"
        error={borrowingError}
        onRetry={() => void refetchBorrowing()}
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEditMode ? 'Edit Borrowing' : 'New Borrowing Facility'}
        subtitle={
          isEditMode ? 'Update borrowing facility details' : 'Create a new borrowing facility'
        }
        breadcrumbs={[
          { label: 'Borrowings', to: '/admin/treasury/borrowings' },
          { label: isEditMode ? 'Edit' : 'New' },
        ]}
      />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle>Facility Details</CardTitle>
              <CardDescription>Basic borrowing facility information</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <FormField
                  control={form.control}
                  name="lenderId"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Lender *</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select lender" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {lenders.map((lender) => (
                            <SelectItem key={lender.id} value={lender.id}>
                              {lender.lenderName} ({lender.lenderType})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="borrowingType"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Facility Type *</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select facility type" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {borrowingTypeOptions.map((type) => (
                            <SelectItem key={type.value} value={type.value}>
                              {type.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                <FormField
                  control={form.control}
                  name="sanctionDate"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Sanction Date *</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} value={field.value ?? ''} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="sanctionReference"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Sanction Reference</FormLabel>
                      <FormControl>
                        <Input placeholder="Sanction letter reference" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="sanctionedAmount"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Sanctioned Amount *</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          placeholder="Sanctioned amount"
                          {...field}
                          value={field.value ?? ''}
                          onChange={(e) =>
                            field.onChange(e.target.value ? Number(e.target.value) : undefined)
                          }
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </CardContent>
          </Card>

          {/* Interest Terms */}
          <Card>
            <CardHeader>
              <CardTitle>Interest Terms</CardTitle>
              <CardDescription>Interest rate and calculation terms</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <FormField
                  control={form.control}
                  name="rateType"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Rate Type *</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select rate type" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {rateTypeOptions.map((type) => (
                            <SelectItem key={type.value} value={type.value}>
                              {type.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="dayCountConvention"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Day Count Convention</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select convention" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {dayCountConventionOptions.map((conv) => (
                            <SelectItem key={conv.value} value={conv.value}>
                              {conv.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              {rateType === 'FLOATING' && (
                <div className="grid gap-4 md:grid-cols-3">
                  <FormField
                    control={form.control}
                    name="baseRateName"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Base Rate Type</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select base rate" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {rateBenchmarkOptions.map((type) => (
                              <SelectItem key={type.value} value={type.value}>
                                {type.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="baseRateValue"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Base Rate (%)</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            step="0.01"
                            placeholder="e.g., 8.50"
                            {...field}
                            value={field.value ?? ''}
                            onChange={(e) =>
                              field.onChange(e.target.value ? Number(e.target.value) : undefined)
                            }
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="spreadBps"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Spread (bps)</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            placeholder="e.g., 75"
                            {...field}
                            value={field.value ?? ''}
                            onChange={(e) =>
                              field.onChange(e.target.value ? Number(e.target.value) : 0)
                            }
                          />
                        </FormControl>
                        <FormDescription>Basis points over base rate</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              )}

              <div className="grid gap-4 md:grid-cols-3">
                <FormField
                  control={form.control}
                  name="effectiveRate"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Effective Rate (% p.a.) *</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          step="0.01"
                          placeholder="e.g., 9.25"
                          {...field}
                          value={field.value ?? ''}
                          onChange={(e) =>
                            field.onChange(e.target.value ? Number(e.target.value) : undefined)
                          }
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="interestPaymentFrequency"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Interest Payment Frequency</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {repaymentFrequencyOptions.map((freq) => (
                            <SelectItem key={freq.value} value={freq.value}>
                              {freq.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                {rateType === 'FLOATING' && (
                  <FormField
                    control={form.control}
                    name="rateResetFrequency"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Rate Reset Frequency</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select frequency" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {rateResetFrequencyOptions.map((freq) => (
                              <SelectItem key={freq.value} value={freq.value}>
                                {freq.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                )}
              </div>
            </CardContent>
          </Card>

          {/* Tenure & Repayment */}
          <Card>
            <CardHeader>
              <CardTitle>Tenure & Repayment</CardTitle>
              <CardDescription>Loan tenure and repayment schedule terms</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-4">
                <FormField
                  control={form.control}
                  name="tenureMonths"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Tenure (Months) *</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          placeholder="e.g., 60"
                          {...field}
                          value={field.value ?? ''}
                          onChange={(e) =>
                            field.onChange(e.target.value ? Number(e.target.value) : undefined)
                          }
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="moratoriumMonths"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Moratorium (Months)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          placeholder="e.g., 6"
                          {...field}
                          value={field.value ?? ''}
                          onChange={(e) =>
                            field.onChange(e.target.value ? Number(e.target.value) : 0)
                          }
                        />
                      </FormControl>
                      <FormDescription>Principal moratorium period</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="maturityDate"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Maturity Date *</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} value={field.value ?? ''} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="principalPaymentFrequency"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Principal Repayment</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {repaymentFrequencyOptions.map((freq) => (
                            <SelectItem key={freq.value} value={freq.value}>
                              {freq.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <FormField
                  control={form.control}
                  name="firstInterestDate"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>First Interest Date</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} value={field.value ?? ''} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="firstPrincipalDate"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>First Principal Date</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} value={field.value ?? ''} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </CardContent>
          </Card>

          {/* Security */}
          <Card>
            <CardHeader>
              <CardTitle>Security Details</CardTitle>
              <CardDescription>Collateral and security information</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <FormField
                  control={form.control}
                  name="securityType"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Security Type</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {securityTypeOptions.map((type) => (
                            <SelectItem key={type.value} value={type.value}>
                              {type.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="securityCoverRequired"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Security Cover Required</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          step="0.01"
                          placeholder="e.g., 1.25 for 125%"
                          {...field}
                          value={field.value ?? ''}
                          onChange={(e) =>
                            field.onChange(e.target.value ? Number(e.target.value) : undefined)
                          }
                        />
                      </FormControl>
                      <FormDescription>e.g., 1.25 = 125% cover</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              <FormField
                control={form.control}
                name="securityDescription"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Security Description</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Describe the security/collateral pledged..."
                        {...field}
                        rows={3}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          {/* Fees */}
          <Card>
            <CardHeader>
              <CardTitle>Fees & Charges</CardTitle>
              <CardDescription>Applicable fees and charges</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <FormField
                  control={form.control}
                  name="processingFeePercent"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Processing Fee (%)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          step="0.01"
                          placeholder="e.g., 0.50"
                          {...field}
                          value={field.value ?? ''}
                          onChange={(e) =>
                            field.onChange(e.target.value ? Number(e.target.value) : undefined)
                          }
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="commitmentFeePercent"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Commitment Fee (%)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          step="0.01"
                          placeholder="e.g., 0.25"
                          {...field}
                          value={field.value ?? ''}
                          onChange={(e) =>
                            field.onChange(e.target.value ? Number(e.target.value) : undefined)
                          }
                        />
                      </FormControl>
                      <FormDescription>On undrawn amount</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="prepaymentPenaltyPercent"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Prepayment Penalty (%)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          step="0.01"
                          placeholder="e.g., 2.00"
                          {...field}
                          value={field.value ?? ''}
                          onChange={(e) =>
                            field.onChange(e.target.value ? Number(e.target.value) : undefined)
                          }
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </CardContent>
          </Card>

          {/* Remarks */}
          <Card>
            <CardHeader>
              <CardTitle>Additional Information</CardTitle>
            </CardHeader>
            <CardContent>
              <FormField
                control={form.control}
                name="remarks"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Remarks</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Any additional notes or remarks..."
                        {...field}
                        rows={3}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="flex justify-end gap-4">
            <Button type="button" variant="outline" onClick={() => navigate(-1)} disabled={saving}>
              Cancel
            </Button>
            <Button type="submit" disabled={saving}>
              {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              <Save className="mr-2 h-4 w-4" />
              {isEditMode ? 'Update Borrowing' : 'Create Borrowing'}
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
}
