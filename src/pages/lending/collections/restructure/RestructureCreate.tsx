import { zodResolver } from '@hookform/resolvers/zod';
import { Save, Calculator, AlertTriangle } from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import type { Resolver } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';

import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { Alert, AlertDescription } from '@/components/ui/alert';
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
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { logger } from '@/lib/logger';
import { masterRowsToOptions, useLendingOptionRows } from '@/hooks/lending/useLendingMasters';
import { useLoanAccounts } from '@/hooks/lending/useLoanAccounts';
import { collectionApi } from '@/services/lending/collectionApi';
import type { LoanAccountListItem } from '@/services/lending/loanAccountApi';

const restructureSchema = z.object({
  loanAccountId: z.string().min(1, 'Loan account is required'),
  restructureType: z.string().min(1, 'Restructure type is required'),
  proposalDate: z.string().min(1, 'Proposal date is required'),
  // Pre-restructure values (read from loan account)
  preOutstandingPrincipal: z.coerce.number().min(0),
  preOutstandingInterest: z.coerce.number().min(0),
  preInterestRate: z.coerce.number().min(0).max(100),
  preTenureMonths: z.coerce.number().int().min(1),
  preEmiAmount: z.coerce.number().optional(),
  preMaturityDate: z.string().min(1),
  // Post-restructure values
  postOutstandingPrincipal: z.coerce.number().min(0),
  postInterestRate: z.coerce.number().min(0).max(100),
  postTenureMonths: z.coerce.number().int().min(1),
  postEmiAmount: z.coerce.number().optional(),
  postMaturityDate: z.string().min(1),
  // Moratorium
  moratoriumMonths: z.coerce.number().int().min(0).default(0),
  moratoriumStartDate: z.string().optional(),
  moratoriumEndDate: z.string().optional(),
  moratoriumInterestTreatment: z.string().optional(),
  // Waivers
  interestWaived: z.coerce.number().min(0).default(0),
  penalWaived: z.coerce.number().min(0).default(0),
  principalConvertedToFitl: z.coerce.number().min(0).default(0),
  // Classification
  isStandardRestructure: z.boolean().default(true),
  downgradeRequired: z.boolean().default(false),
  // Conditions
  preConditions: z.string().optional(),
  postConditions: z.string().optional(),
  // Justification
  justification: z.string().min(10, 'Detailed justification is required'),
  remarks: z.string().optional(),
});

type RestructureFormValues = z.infer<typeof restructureSchema>;

export default function RestructureCreate() {
  const navigate = useNavigate();
  const [selectedLoan, setSelectedLoan] = useState<LoanAccountListItem | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const loanAccountsQuery = useLoanAccounts({ pageSize: 200, dpdFrom: 1 });
  const restructureTypeRows = useLendingOptionRows('RESTRUCTURE_TYPE');
  const moratoriumTreatmentRows = useLendingOptionRows('MORATORIUM_INTEREST_TREATMENT');
  const restructureTypeOptions = masterRowsToOptions(restructureTypeRows.data?.items);
  const moratoriumTreatmentOptions = masterRowsToOptions(moratoriumTreatmentRows.data?.items);

  const form = useForm<RestructureFormValues>({
    // RHF resolver type mismatch when schema has `.default(...)` fields and
    // schema field types are computed (e.g. `coerce.number`).
    resolver: zodResolver(restructureSchema) as Resolver<RestructureFormValues>,
    defaultValues: {
      proposalDate: new Date().toISOString().split('T')[0],
      moratoriumMonths: 0,
      interestWaived: 0,
      penalWaived: 0,
      principalConvertedToFitl: 0,
      isStandardRestructure: true,
      downgradeRequired: false,
    },
  });

  const handleLoanSelect = (loanId: string) => {
    const loan = (loanAccountsQuery.data?.items ?? []).find((l) => l.id === loanId);
    if (loan) {
      setSelectedLoan(loan);
      form.setValue('loanAccountId', loan.id);
      const principal = Number(loan.principalOutstanding);
      const total = Number(loan.totalOutstanding);
      const interest = Math.max(total - principal, 0);
      const rate = Number(loan.currentInterestRate);
      const maturityDate = loan.maturityDate ?? new Date().toISOString().split('T')[0];
      form.setValue('preOutstandingPrincipal', principal);
      form.setValue('preOutstandingInterest', interest);
      form.setValue('preInterestRate', rate);
      form.setValue('preTenureMonths', 1);
      form.setValue('preEmiAmount', undefined);
      form.setValue('preMaturityDate', maturityDate);
      form.setValue('postOutstandingPrincipal', principal);
      form.setValue('postInterestRate', rate);
      form.setValue('postTenureMonths', 1);
      form.setValue('postEmiAmount', undefined);
      form.setValue('postMaturityDate', maturityDate);
    }
  };

  const onSubmit = async (data: RestructureFormValues) => {
    setIsSubmitting(true);
    try {
      logger.debug('Restructure data:', data);
      await collectionApi.createRestructure(data);
      navigate('/admin/lending/collections/restructure');
    } catch {
    } finally {
      setIsSubmitting(false);
    }
  };

  const watchedValues = form.watch();
  const rateChange = (watchedValues.postInterestRate || 0) - (watchedValues.preInterestRate || 0);
  const tenureChange = (watchedValues.postTenureMonths || 0) - (watchedValues.preTenureMonths || 0);
  const totalWaiver = (watchedValues.interestWaived || 0) + (watchedValues.penalWaived || 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="New Restructure Proposal"
        subtitle="Create a loan restructuring proposal"
        breadcrumbs={[
          { label: 'Restructures', to: '/admin/lending/collections/restructure' },
          { label: 'New' },
        ]}
      />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          {/* Loan Selection */}
          <Card>
            <CardHeader>
              <CardTitle>Select Loan Account</CardTitle>
              <CardDescription>Choose the loan account for restructuring</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <FormField
                control={form.control}
                name="loanAccountId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Loan Account</FormLabel>
                    <Select
                      onValueChange={(value) => {
                        field.onChange(value);
                        handleLoanSelect(value);
                      }}
                      value={field.value}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue
                            placeholder={
                              loanAccountsQuery.isLoading
                                ? 'Loading loan accounts...'
                                : 'Select a loan account'
                            }
                          />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {(loanAccountsQuery.data?.items ?? []).map((loan) => (
                          <SelectItem key={loan.id} value={loan.id}>
                            {loan.loanAccountNumber} - {loan.entityName ?? 'Unnamed entity'}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {selectedLoan && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    <div className="mt-2 grid grid-cols-4 gap-4">
                      <div>
                        <span className="text-xs text-muted-foreground">Principal O/S</span>
                        <AmountDisplay
                          amount={selectedLoan.principalOutstanding}
                          className="font-semibold"
                        />
                      </div>
                      <div>
                        <span className="text-xs text-muted-foreground">Interest O/S</span>
                        <AmountDisplay
                          amount={
                            Number(selectedLoan.totalOutstanding) -
                            Number(selectedLoan.principalOutstanding)
                          }
                          className="font-semibold"
                        />
                      </div>
                      <div>
                        <span className="text-xs text-muted-foreground">DPD</span>
                        <p className="font-semibold text-red-600">
                          {selectedLoan.daysPastDue} days
                        </p>
                      </div>
                      <div>
                        <span className="text-xs text-muted-foreground">Classification</span>
                        <p className="font-semibold text-yellow-600">
                          {selectedLoan.assetClassification}
                        </p>
                      </div>
                    </div>
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Restructure Type & Date */}
          <Card>
            <CardHeader>
              <CardTitle>Restructure Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="restructureType"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Restructure Type</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select type" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {restructureTypeOptions.map((option) => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
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
                  name="proposalDate"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Proposal Date</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </CardContent>
          </Card>

          {/* Pre & Post Terms Comparison */}
          <div className="grid grid-cols-2 gap-6">
            {/* Pre-Restructure */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Pre-Restructure Terms</CardTitle>
                <CardDescription>
                  Current loan terms from account data; edit if needed
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <FormField
                  control={form.control}
                  name="preOutstandingPrincipal"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Principal Outstanding</FormLabel>
                      <FormControl>
                        <Input type="number" {...field} />
                      </FormControl>
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="preInterestRate"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Interest Rate (%)</FormLabel>
                      <FormControl>
                        <Input type="number" step="0.01" {...field} />
                      </FormControl>
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="preTenureMonths"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Tenure (Months)</FormLabel>
                      <FormControl>
                        <Input type="number" {...field} />
                      </FormControl>
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="preMaturityDate"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Maturity Date</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                    </FormItem>
                  )}
                />
              </CardContent>
            </Card>

            {/* Post-Restructure */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Post-Restructure Terms</CardTitle>
                <CardDescription>Proposed new terms</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <FormField
                  control={form.control}
                  name="postOutstandingPrincipal"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Principal Outstanding</FormLabel>
                      <FormControl>
                        <Input type="number" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="postInterestRate"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Interest Rate (%)</FormLabel>
                      <FormControl>
                        <Input type="number" step="0.01" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="postTenureMonths"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Tenure (Months)</FormLabel>
                      <FormControl>
                        <Input type="number" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="postMaturityDate"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>New Maturity Date</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </CardContent>
            </Card>
          </div>

          {/* Impact Summary */}
          {selectedLoan && (
            <Card className="bg-muted/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calculator className="h-5 w-5" />
                  Impact Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 gap-4">
                  <div className="rounded-lg bg-background p-4 text-center">
                    <p className="mb-1 text-xs text-muted-foreground">Rate Change</p>
                    <p
                      className={`text-xl font-bold ${rateChange < 0 ? 'text-green-600' : rateChange > 0 ? 'text-red-600' : ''}`}
                    >
                      {rateChange > 0 ? '+' : ''}
                      {rateChange.toFixed(2)}%
                    </p>
                  </div>
                  <div className="rounded-lg bg-background p-4 text-center">
                    <p className="mb-1 text-xs text-muted-foreground">Tenure Change</p>
                    <p className={`text-xl font-bold ${tenureChange > 0 ? 'text-yellow-600' : ''}`}>
                      {tenureChange > 0 ? '+' : ''}
                      {tenureChange} months
                    </p>
                  </div>
                  <div className="rounded-lg bg-background p-4 text-center">
                    <p className="mb-1 text-xs text-muted-foreground">Moratorium</p>
                    <p className="text-xl font-bold">
                      {watchedValues.moratoriumMonths || 0} months
                    </p>
                  </div>
                  <div className="rounded-lg bg-background p-4 text-center">
                    <p className="mb-1 text-xs text-muted-foreground">Total Waiver</p>
                    <AmountDisplay
                      amount={totalWaiver}
                      className="text-xl font-bold text-red-600"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Moratorium Details */}
          <Card>
            <CardHeader>
              <CardTitle>Moratorium Details</CardTitle>
              <CardDescription>Configure moratorium/payment holiday if applicable</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <FormField
                  control={form.control}
                  name="moratoriumMonths"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Moratorium Period (Months)</FormLabel>
                      <FormControl>
                        <Input type="number" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="moratoriumStartDate"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Moratorium Start</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="moratoriumInterestTreatment"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Interest Treatment</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select treatment" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {moratoriumTreatmentOptions.map((option) => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </CardContent>
          </Card>

          {/* Waivers */}
          <Card>
            <CardHeader>
              <CardTitle>Waivers & Relief</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <FormField
                  control={form.control}
                  name="interestWaived"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Interest Waived</FormLabel>
                      <FormControl>
                        <Input type="number" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="penalWaived"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Penal Interest Waived</FormLabel>
                      <FormControl>
                        <Input type="number" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="principalConvertedToFitl"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Principal to FITL</FormLabel>
                      <FormControl>
                        <Input type="number" {...field} />
                      </FormControl>
                      <FormDescription>Funded Interest Term Loan</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </CardContent>
          </Card>

          {/* Classification Impact */}
          <Card>
            <CardHeader>
              <CardTitle>Classification & Compliance</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <FormLabel>Standard Restructure (RBI Compliant)</FormLabel>
                  <FormDescription>
                    Restructure qualifies under standard asset category as per RBI norms
                  </FormDescription>
                </div>
                <FormField
                  control={form.control}
                  name="isStandardRestructure"
                  render={({ field }) => (
                    <FormItem>
                      <FormControl>
                        <Switch checked={field.value} onCheckedChange={field.onChange} />
                      </FormControl>
                    </FormItem>
                  )}
                />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <FormLabel>Downgrade Required</FormLabel>
                  <FormDescription>
                    Asset classification downgrade is required post-restructure
                  </FormDescription>
                </div>
                <FormField
                  control={form.control}
                  name="downgradeRequired"
                  render={({ field }) => (
                    <FormItem>
                      <FormControl>
                        <Switch checked={field.value} onCheckedChange={field.onChange} />
                      </FormControl>
                    </FormItem>
                  )}
                />
              </div>
            </CardContent>
          </Card>

          {/* Conditions & Justification */}
          <Card>
            <CardHeader>
              <CardTitle>Conditions & Justification</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <FormField
                control={form.control}
                name="preConditions"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Pre-Conditions</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Conditions to be fulfilled before restructure..."
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="postConditions"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Post-Conditions</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Conditions to be monitored after restructure..."
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="justification"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Justification *</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Detailed justification for restructure proposal..."
                        className="min-h-[120px]"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      Provide detailed reasons supporting this restructure proposal
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="remarks"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Additional Remarks</FormLabel>
                    <FormControl>
                      <Textarea placeholder="Any additional notes or remarks..." {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="flex justify-end gap-4">
            <Button type="button" variant="outline" onClick={() => navigate(-1)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              <Save className="mr-2 h-4 w-4" />
              {isSubmitting ? 'Saving...' : 'Create Proposal'}
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
}
