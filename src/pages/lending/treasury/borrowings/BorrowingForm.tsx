import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Save, Loader2 } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { treasuryApi, CreateBorrowingRequest } from '@/services/lending/treasuryApi';
import { useToast } from '@/components/ui/use-toast';

const BORROWING_TYPES = [
  { value: 'TERM_LOAN', label: 'Term Loan' },
  { value: 'WORKING_CAPITAL', label: 'Working Capital Loan' },
  { value: 'CASH_CREDIT', label: 'Cash Credit / Overdraft' },
  { value: 'NCD', label: 'Non-Convertible Debentures' },
  { value: 'CP', label: 'Commercial Paper' },
  { value: 'SUBORDINATED_DEBT', label: 'Subordinated Debt / Tier-II' },
  { value: 'ECB', label: 'External Commercial Borrowing' },
  { value: 'REFINANCE', label: 'Refinance Facility' },
  { value: 'ICD', label: 'Inter-Corporate Deposit' },
];

const RATE_TYPES = [
  { value: 'FIXED', label: 'Fixed Rate' },
  { value: 'FLOATING', label: 'Floating Rate' },
];

const BASE_RATE_TYPES = [
  { value: 'MCLR', label: 'MCLR' },
  { value: 'REPO', label: 'Repo Rate' },
  { value: 'T_BILL', label: 'T-Bill Rate' },
  { value: 'LIBOR', label: 'LIBOR' },
  { value: 'SOFR', label: 'SOFR' },
  { value: 'OTHER', label: 'Other' },
];

const REPAYMENT_FREQUENCIES = [
  { value: 'MONTHLY', label: 'Monthly' },
  { value: 'QUARTERLY', label: 'Quarterly' },
  { value: 'HALF_YEARLY', label: 'Half-Yearly' },
  { value: 'YEARLY', label: 'Yearly' },
  { value: 'BULLET', label: 'Bullet' },
];

const DAY_COUNT_CONVENTIONS = [
  { value: 'ACT_365', label: 'Actual/365' },
  { value: 'ACT_360', label: 'Actual/360' },
  { value: 'THIRTY_360', label: '30/360' },
];

const SECURITY_TYPES = [
  { value: 'SECURED', label: 'Secured' },
  { value: 'UNSECURED', label: 'Unsecured' },
];

interface Lender {
  lender_id: string;
  lender_code: string;
  lender_name: string;
  lender_type: string;
}

const borrowingFormSchema = z.object({
  lender_id: z.string().min(1, 'Lender is required'),
  borrowing_type: z.string().min(1, 'Borrowing type is required'),
  sanction_date: z.string().min(1, 'Sanction date is required'),
  sanction_reference: z.string().max(100).optional(),
  sanctioned_amount: z.coerce.number().positive('Amount must be positive'),
  currency: z.string().default('INR'),

  // Interest terms
  rate_type: z.string().min(1, 'Rate type is required'),
  base_rate_name: z.string().optional(),
  base_rate_value: z.coerce.number().nonnegative().optional(),
  spread_bps: z.coerce.number().int().nonnegative().default(0),
  effective_rate: z.coerce.number().positive('Effective rate is required'),
  rate_reset_frequency: z.string().optional(),

  // Day count and frequency
  day_count_convention: z.string().default('ACT_365'),
  interest_payment_frequency: z.string().default('MONTHLY'),
  principal_payment_frequency: z.string().default('QUARTERLY'),

  // Tenure
  tenure_months: z.coerce.number().int().positive('Tenure is required'),
  moratorium_months: z.coerce.number().int().nonnegative().default(0),
  first_interest_date: z.string().optional(),
  first_principal_date: z.string().optional(),
  maturity_date: z.string().min(1, 'Maturity date is required'),

  // Security
  security_type: z.string().default('UNSECURED'),
  security_description: z.string().optional(),
  security_cover_required: z.coerce.number().optional(),

  // Fees
  processing_fee_percent: z.coerce.number().optional(),
  commitment_fee_percent: z.coerce.number().optional(),
  prepayment_penalty_percent: z.coerce.number().optional(),

  remarks: z.string().optional(),
});

type BorrowingFormData = z.infer<typeof borrowingFormSchema>;

export default function BorrowingForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [lenders, setLenders] = useState<Lender[]>([]);
  const isEditMode = Boolean(id);

  const form = useForm<BorrowingFormData>({
    resolver: zodResolver(borrowingFormSchema) as any,
    defaultValues: {
      lender_id: '',
      borrowing_type: '',
      sanction_date: new Date().toISOString().split('T')[0],
      sanction_reference: '',
      sanctioned_amount: undefined,
      currency: 'INR',
      rate_type: 'FLOATING',
      base_rate_name: '',
      base_rate_value: undefined,
      spread_bps: 0,
      effective_rate: undefined,
      rate_reset_frequency: 'QUARTERLY',
      day_count_convention: 'ACT_365',
      interest_payment_frequency: 'MONTHLY',
      principal_payment_frequency: 'QUARTERLY',
      tenure_months: undefined,
      moratorium_months: 0,
      first_interest_date: '',
      first_principal_date: '',
      maturity_date: '',
      security_type: 'UNSECURED',
      security_description: '',
      security_cover_required: undefined,
      processing_fee_percent: undefined,
      commitment_fee_percent: undefined,
      prepayment_penalty_percent: undefined,
      remarks: '',
    },
  });

  const rateType = form.watch('rate_type');
  const baseRateValue = form.watch('base_rate_value');
  const spreadBps = form.watch('spread_bps');

  // Auto-calculate effective rate for floating
  useEffect(() => {
    if (rateType === 'FLOATING' && baseRateValue !== undefined && spreadBps !== undefined) {
      const effectiveRate = baseRateValue + spreadBps / 100;
      form.setValue('effective_rate', Number(effectiveRate.toFixed(4)));
    }
  }, [rateType, baseRateValue, spreadBps, form]);

  const fetchLenders = useCallback(async () => {
    try {
      const response = await treasuryApi.getLenders();
      setLenders(response.items || []);
    } catch (error) {
      console.error('Failed to fetch lenders:', error);
      // Use mock data if API fails
      setLenders([
        { lender_id: '1', lender_code: 'HDFC-BNK', lender_name: 'HDFC Bank Ltd', lender_type: 'BANK' },
        { lender_id: '2', lender_code: 'SIDBI', lender_name: 'SIDBI', lender_type: 'DFI' },
        { lender_id: '3', lender_code: 'ICICI-BNK', lender_name: 'ICICI Bank Ltd', lender_type: 'BANK' },
      ]);
    }
  }, []);

  useEffect(() => {
    fetchLenders();
    if (isEditMode && id) {
      loadBorrowing(id);
    }
  }, [id, isEditMode, fetchLenders]);

  const loadBorrowing = async (borrowingId: string) => {
    setLoading(true);
    try {
      const borrowing = await treasuryApi.getBorrowing(borrowingId);
      form.reset({
        lender_id: borrowing.lender_id || '',
        borrowing_type: borrowing.facility_type || '',
        sanction_date: borrowing.sanction_date || '',
        sanction_reference: borrowing.sanction_reference || '',
        sanctioned_amount: borrowing.sanctioned_amount || undefined,
        currency: borrowing.currency || 'INR',
        rate_type: borrowing.interest_type || 'FLOATING',
        base_rate_name: borrowing.base_rate_type || '',
        base_rate_value: borrowing.base_rate_value || undefined,
        spread_bps: borrowing.spread_bps || 0,
        effective_rate: borrowing.effective_rate || undefined,
        rate_reset_frequency: borrowing.rate_reset_frequency || 'QUARTERLY',
        day_count_convention: borrowing.day_count_convention || 'ACT_365',
        interest_payment_frequency: borrowing.interest_payment_frequency || 'MONTHLY',
        principal_payment_frequency: borrowing.principal_payment_frequency || 'QUARTERLY',
        tenure_months: borrowing.tenure_months || undefined,
        moratorium_months: borrowing.moratorium_months || 0,
        first_interest_date: borrowing.first_interest_date || '',
        first_principal_date: borrowing.first_principal_date || '',
        maturity_date: borrowing.maturity_date || '',
        security_type: borrowing.security_type || 'UNSECURED',
        security_description: borrowing.security_description || '',
        security_cover_required: borrowing.security_cover_required || undefined,
        processing_fee_percent: borrowing.processing_fee_percent || undefined,
        commitment_fee_percent: borrowing.commitment_fee_percent || undefined,
        prepayment_penalty_percent: borrowing.prepayment_penalty_percent || undefined,
        remarks: borrowing.remarks || '',
      });
    } catch (error) {
      console.error('Failed to load borrowing:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to load borrowing details',
      });
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data: BorrowingFormData) => {
    setSaving(true);
    try {
      const payload: CreateBorrowingRequest = {
        lender_id: data.lender_id,
        facility_type: data.borrowing_type as CreateBorrowingRequest['facility_type'],
        facility_name: `${data.borrowing_type} - ${lenders.find(l => l.lender_id === data.lender_id)?.lender_name || ''}`,
        sanctioned_amount: data.sanctioned_amount,
        interest_type: data.rate_type as 'FIXED' | 'FLOATING',
        interest_rate: data.effective_rate,
        spread_bps: data.spread_bps,
        tenure_months: data.tenure_months,
        sanction_date: data.sanction_date,
        maturity_date: data.maturity_date,
        repayment_frequency: data.principal_payment_frequency as CreateBorrowingRequest['repayment_frequency'],
        security_details: data.security_description,
        remarks: data.remarks,
      };

      if (isEditMode && id) {
        await treasuryApi.updateBorrowing(id, payload);
        toast({
          title: 'Success',
          description: 'Borrowing updated successfully',
        });
      } else {
        const newBorrowing = await treasuryApi.createBorrowing(payload);
        toast({
          title: 'Success',
          description: 'Borrowing created successfully',
        });
        navigate(`/admin/lending/treasury/borrowings/${newBorrowing.borrowing_id}`);
        return;
      }
      navigate('/admin/lending/treasury/borrowings');
    } catch (error) {
      console.error('Failed to save borrowing:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: `Failed to ${isEditMode ? 'update' : 'create'} borrowing`,
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-semibold">
            {isEditMode ? 'Edit Borrowing' : 'New Borrowing Facility'}
          </h1>
          <p className="text-muted-foreground">
            {isEditMode
              ? 'Update borrowing facility details'
              : 'Create a new borrowing facility'}
          </p>
        </div>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit as any)} className="space-y-6">
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
                  name="lender_id"
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
                            <SelectItem key={lender.lender_id} value={lender.lender_id}>
                              {lender.lender_name} ({lender.lender_type})
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
                  name="borrowing_type"
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
                          {BORROWING_TYPES.map((type) => (
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
                  name="sanction_date"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Sanction Date *</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="sanction_reference"
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
                  name="sanctioned_amount"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Sanctioned Amount *</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          placeholder="Sanctioned amount"
                          {...field}
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
                  name="rate_type"
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
                          {RATE_TYPES.map((type) => (
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
                  name="day_count_convention"
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
                          {DAY_COUNT_CONVENTIONS.map((conv) => (
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
                    name="base_rate_name"
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
                            {BASE_RATE_TYPES.map((type) => (
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
                    name="base_rate_value"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Base Rate (%)</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            step="0.01"
                            placeholder="e.g., 8.50"
                            {...field}
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
                    name="spread_bps"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Spread (bps)</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            placeholder="e.g., 75"
                            {...field}
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
                  name="effective_rate"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Effective Rate (% p.a.) *</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          step="0.01"
                          placeholder="e.g., 9.25"
                          {...field}
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
                  name="interest_payment_frequency"
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
                          {REPAYMENT_FREQUENCIES.map((freq) => (
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
                    name="rate_reset_frequency"
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
                            {REPAYMENT_FREQUENCIES.slice(0, -1).map((freq) => (
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
                  name="tenure_months"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Tenure (Months) *</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          placeholder="e.g., 60"
                          {...field}
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
                  name="moratorium_months"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Moratorium (Months)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          placeholder="e.g., 6"
                          {...field}
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
                  name="maturity_date"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Maturity Date *</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="principal_payment_frequency"
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
                          {REPAYMENT_FREQUENCIES.map((freq) => (
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
                  name="first_interest_date"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>First Interest Date</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="first_principal_date"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>First Principal Date</FormLabel>
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
                  name="security_type"
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
                          {SECURITY_TYPES.map((type) => (
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
                  name="security_cover_required"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Security Cover Required</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          step="0.01"
                          placeholder="e.g., 1.25 for 125%"
                          {...field}
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
                name="security_description"
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
                  name="processing_fee_percent"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Processing Fee (%)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          step="0.01"
                          placeholder="e.g., 0.50"
                          {...field}
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
                  name="commitment_fee_percent"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Commitment Fee (%)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          step="0.01"
                          placeholder="e.g., 0.25"
                          {...field}
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
                  name="prepayment_penalty_percent"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Prepayment Penalty (%)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          step="0.01"
                          placeholder="e.g., 2.00"
                          {...field}
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
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate(-1)}
              disabled={saving}
            >
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
