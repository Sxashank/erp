/**
 * Request Credit Pull Page
 * Form to initiate a credit bureau pull for a customer
 */

import { zodResolver } from '@hookform/resolvers/zod';
import { CreditCard, User, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { z } from 'zod';

import { PageHeader } from '@/components/common/PageHeader';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { DatePicker } from '@/components/ui/date-picker';
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
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { useCreateCreditPull } from '@/hooks/lending/useCreditPulls';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import { logger } from '@/lib/logger';
import type { CreateCreditPullRequest } from '@/services/lending/creditApi';
// Form validation schema
const creditPullFormSchema = z.object({
  bureau: z.enum(['CIBIL', 'EXPERIAN', 'EQUIFAX', 'CRIF'], {
    message: 'Please select a credit bureau',
  }),
  pullType: z.enum(['SOFT', 'HARD'], {
    message: 'Please select pull type',
  }),
  customerName: z.string().min(2, 'Name must be at least 2 characters').max(200),
  panNumber: z
    .string()
    .regex(/^[A-Z]{5}[0-9]{4}[A-Z]{1}$/, 'Invalid PAN format')
    .optional()
    .or(z.literal('')),
  dateOfBirth: z.date().optional(),
  mobileNumber: z
    .string()
    .regex(/^[6-9]\d{9}$/, 'Invalid mobile number')
    .optional()
    .or(z.literal('')),
  email: z.string().email('Invalid email').optional().or(z.literal('')),
  addressLine1: z.string().max(255).optional(),
  addressLine2: z.string().max(255).optional(),
  city: z.string().max(100).optional(),
  state: z.string().max(100).optional(),
  pincode: z
    .string()
    .regex(/^\d{6}$/, 'Invalid pincode')
    .optional()
    .or(z.literal('')),
  entityId: z.string().optional(),
  loanApplicationId: z.string().optional(),
  purpose: z.string().optional(),
  consent: z.boolean().refine((val) => val === true, {
    message: 'You must confirm customer consent',
  }),
});

type CreditPullFormInput = z.input<typeof creditPullFormSchema>;
type CreditPullFormData = z.output<typeof creditPullFormSchema>;

// Bureau info
const bureauInfo = {
  CIBIL: {
    name: 'CIBIL (TransUnion)',
    description: 'Most widely used bureau in India. Provides TransUnion CIBIL Score.',
    scoreRange: '300-900',
  },
  EXPERIAN: {
    name: 'Experian India',
    description: 'Global credit bureau with comprehensive consumer and commercial data.',
    scoreRange: '300-900',
  },
  EQUIFAX: {
    name: 'Equifax India',
    description: 'One of the major global credit bureaus with Indian presence.',
    scoreRange: '300-900',
  },
  CRIF: {
    name: 'CRIF High Mark',
    description: 'Specialized in microfinance and small business credit data.',
    scoreRange: '300-900',
  },
};

export default function RequestCreditPull() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  const createPullMutation = useCreateCreditPull();
  const [existingScore, setExistingScore] = useState<{
    score: number;
    bureau: string;
    pulledAt: string;
    isValid: boolean;
  } | null>(null);

  // Pre-fill from URL params
  const defaultValues: Partial<CreditPullFormData> = {
    bureau: 'CIBIL',
    pullType: 'SOFT',
    panNumber: searchParams.get('pan') || '',
    customerName: searchParams.get('name') || '',
    consent: false,
  };

  const form = useForm<CreditPullFormInput, unknown, CreditPullFormData>({
    resolver: zodResolver(creditPullFormSchema),
    defaultValues,
  });

  const selectedBureau = form.watch('bureau');
  const pullType = form.watch('pullType');
  const panNumber = form.watch('panNumber');

  // Check for existing valid score. Wires to
  // GET /lending/credit/pulls?pan=:pan&status=COMPLETED once that filter is
  // exposed; until then we just clear any prior score.
  const checkExistingScore = async (_pan: string) => {
    setExistingScore(null);
  };

  const onSubmit = async (data: CreditPullFormData) => {
    // Build the camelCase request body the backend contract exposes. Only send
    // populated optional fields so the BE doesn't reject empty strings.
    const payload: CreateCreditPullRequest = {
      bureau: data.bureau,
      pullType: data.pullType,
      customerName: data.customerName,
    };
    if (data.panNumber) payload.panNumber = data.panNumber;
    if (data.mobileNumber) payload.mobileNumber = data.mobileNumber;
    if (data.email) payload.email = data.email;
    if (data.dateOfBirth) {
      // Wire format is ISO date `yyyy-MM-dd` (CLAUDE.md §5.8).
      payload.dateOfBirth = data.dateOfBirth.toISOString().slice(0, 10);
    }
    if (data.addressLine1) payload.addressLine1 = data.addressLine1;
    if (data.addressLine2) payload.addressLine2 = data.addressLine2;
    if (data.city) payload.city = data.city;
    if (data.state) payload.state = data.state;
    if (data.pincode) payload.pincode = data.pincode;
    if (data.entityId) payload.entityId = data.entityId;
    if (data.loanApplicationId) payload.loanApplicationId = data.loanApplicationId;
    if (data.purpose) payload.purpose = data.purpose;

    // Note: PAN is collected but never logged (CLAUDE.md §8.7). The mutation
    // hook injects an Idempotency-Key per call (CLAUDE.md §6.3).
    logger.debug('Submitting credit pull request', {
      bureau: payload.bureau,
      pullType: payload.pullType,
    });

    try {
      const result = await createPullMutation.mutateAsync(payload);
      toast({
        title: 'Credit pull initiated',
        description: `${result.bureau} ${result.pullType.toLowerCase()} pull queued. Reference: ${
          result.requestReference ?? result.id.slice(0, 8)
        }`,
      });
      navigate(`/admin/lending/credit/pulls/${result.id}`);
    } catch (err) {
      showErrorToast(err, toast);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Request Credit Report"
        subtitle="Pull credit report from CIBIL, Experian, Equifax, or CRIF"
        breadcrumbs={[{ label: 'Credit Pulls', to: '/admin/lending/credit' }, { label: 'Request' }]}
      />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Left Column - Bureau & Pull Type */}
            <div className="space-y-6">
              {/* Bureau Selection */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CreditCard className="h-5 w-5" />
                    Credit Bureau
                  </CardTitle>
                  <CardDescription>Select the bureau to pull from</CardDescription>
                </CardHeader>
                <CardContent>
                  <FormField
                    control={form.control}
                    name="bureau"
                    render={({ field }) => (
                      <FormItem>
                        <FormControl>
                          <RadioGroup
                            onValueChange={field.onChange}
                            defaultValue={field.value}
                            className="space-y-3"
                          >
                            {Object.entries(bureauInfo).map(([key, info]) => (
                              <div
                                key={key}
                                className={`flex cursor-pointer items-start space-x-3 rounded-lg border p-4 transition-colors ${
                                  field.value === key
                                    ? 'border-primary bg-primary/5'
                                    : 'border-muted hover:border-primary/50'
                                }`}
                                onClick={() => field.onChange(key)}
                              >
                                <RadioGroupItem value={key} id={key} className="mt-1" />
                                <div className="space-y-1">
                                  <label htmlFor={key} className="cursor-pointer font-medium">
                                    {info.name}
                                  </label>
                                  <p className="text-xs text-muted-foreground">
                                    {info.description}
                                  </p>
                                  <Badge variant="secondary" className="text-xs">
                                    Score: {info.scoreRange}
                                  </Badge>
                                </div>
                              </div>
                            ))}
                          </RadioGroup>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>

              {/* Pull Type */}
              <Card>
                <CardHeader>
                  <CardTitle>Pull Type</CardTitle>
                  <CardDescription>Select the type of credit inquiry</CardDescription>
                </CardHeader>
                <CardContent>
                  <FormField
                    control={form.control}
                    name="pullType"
                    render={({ field }) => (
                      <FormItem>
                        <FormControl>
                          <RadioGroup
                            onValueChange={field.onChange}
                            defaultValue={field.value}
                            className="space-y-3"
                          >
                            <div
                              className={`flex cursor-pointer items-start space-x-3 rounded-lg border p-4 transition-colors ${
                                field.value === 'SOFT'
                                  ? 'border-green-500 bg-green-50'
                                  : 'border-muted hover:border-green-300'
                              }`}
                              onClick={() => field.onChange('SOFT')}
                            >
                              <RadioGroupItem value="SOFT" id="soft" className="mt-1" />
                              <div className="space-y-1">
                                <label htmlFor="soft" className="cursor-pointer font-medium">
                                  Soft Pull
                                </label>
                                <p className="text-xs text-muted-foreground">
                                  Does not affect customer's credit score. Use for pre-qualification
                                  and account reviews.
                                </p>
                                <Badge variant="outline" className="bg-green-50 text-green-700">
                                  Recommended
                                </Badge>
                              </div>
                            </div>
                            <div
                              className={`flex cursor-pointer items-start space-x-3 rounded-lg border p-4 transition-colors ${
                                field.value === 'HARD'
                                  ? 'border-amber-500 bg-amber-50'
                                  : 'border-muted hover:border-amber-300'
                              }`}
                              onClick={() => field.onChange('HARD')}
                            >
                              <RadioGroupItem value="HARD" id="hard" className="mt-1" />
                              <div className="space-y-1">
                                <label htmlFor="hard" className="cursor-pointer font-medium">
                                  Hard Pull
                                </label>
                                <p className="text-xs text-muted-foreground">
                                  May temporarily affect credit score. Use only for final loan
                                  approval decisions.
                                </p>
                                <Badge variant="outline" className="bg-amber-50 text-amber-700">
                                  Use with caution
                                </Badge>
                              </div>
                            </div>
                          </RadioGroup>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>

              {/* Hard Pull Warning */}
              {pullType === 'HARD' && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>Hard Pull Warning</AlertTitle>
                  <AlertDescription>
                    Hard pulls are recorded on the customer's credit report and may temporarily
                    lower their credit score. Only use for final loan decisions.
                  </AlertDescription>
                </Alert>
              )}
            </div>

            {/* Right Column - Customer Details */}
            <div className="space-y-6 lg:col-span-2">
              {/* Customer Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="h-5 w-5" />
                    Customer Information
                  </CardTitle>
                  <CardDescription>Enter customer details for credit bureau lookup</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <FormField
                      control={form.control}
                      name="customerName"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Full Name *</FormLabel>
                          <FormControl>
                            <Input placeholder="As per PAN card" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="panNumber"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>PAN Number *</FormLabel>
                          <FormControl>
                            <Input
                              placeholder="ABCDE1234F"
                              {...field}
                              onChange={(e) => {
                                field.onChange(e.target.value.toUpperCase());
                                if (e.target.value.length === 10) {
                                  checkExistingScore(e.target.value.toUpperCase());
                                }
                              }}
                              className="font-mono uppercase"
                            />
                          </FormControl>
                          <FormDescription>
                            Primary identifier for credit bureau lookup
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  {/* Existing Score Alert */}
                  {existingScore && (
                    <Alert className="border-green-200 bg-green-50">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <AlertTitle className="text-green-700">Valid Report Found</AlertTitle>
                      <AlertDescription className="text-green-600">
                        A valid {existingScore.bureau} report exists for this PAN with score{' '}
                        <strong>{existingScore.score}</strong> (pulled on {existingScore.pulledAt}).
                        You may use the existing report instead of pulling a new one.
                        <div className="mt-2">
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => navigate('/admin/lending/credit/pulls/existing-id')}
                          >
                            View Existing Report
                          </Button>
                        </div>
                      </AlertDescription>
                    </Alert>
                  )}

                  <div className="grid gap-4 md:grid-cols-2">
                    <FormField
                      control={form.control}
                      name="dateOfBirth"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Date of Birth</FormLabel>
                          <FormControl>
                            <DatePicker
                              date={field.value}
                              onSelect={field.onChange}
                              placeholder="Select date"
                            />
                          </FormControl>
                          <FormDescription>Helps in accurate matching</FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="mobileNumber"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Mobile Number</FormLabel>
                          <FormControl>
                            <Input placeholder="9876543210" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <FormField
                    control={form.control}
                    name="email"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Email</FormLabel>
                        <FormControl>
                          <Input type="email" placeholder="customer@example.com" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <Separator />

                  <div className="space-y-4">
                    <h4 className="font-medium">Address (Optional)</h4>
                    <FormField
                      control={form.control}
                      name="addressLine1"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Address Line 1</FormLabel>
                          <FormControl>
                            <Input placeholder="House/Building, Street" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="addressLine2"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Address Line 2</FormLabel>
                          <FormControl>
                            <Input placeholder="Locality, Area" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <div className="grid gap-4 md:grid-cols-3">
                      <FormField
                        control={form.control}
                        name="city"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>City</FormLabel>
                            <FormControl>
                              <Input placeholder="City" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={form.control}
                        name="state"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>State</FormLabel>
                            <FormControl>
                              <Select onValueChange={field.onChange} value={field.value}>
                                <SelectTrigger>
                                  <SelectValue placeholder="Select state" />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="MH">Maharashtra</SelectItem>
                                  <SelectItem value="DL">Delhi</SelectItem>
                                  <SelectItem value="KA">Karnataka</SelectItem>
                                  <SelectItem value="TN">Tamil Nadu</SelectItem>
                                  <SelectItem value="GJ">Gujarat</SelectItem>
                                  <SelectItem value="RJ">Rajasthan</SelectItem>
                                  <SelectItem value="UP">Uttar Pradesh</SelectItem>
                                  <SelectItem value="WB">West Bengal</SelectItem>
                                  <SelectItem value="AP">Andhra Pradesh</SelectItem>
                                  <SelectItem value="TS">Telangana</SelectItem>
                                </SelectContent>
                              </Select>
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={form.control}
                        name="pincode"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Pincode</FormLabel>
                            <FormControl>
                              <Input placeholder="400001" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Linking */}
              <Card>
                <CardHeader>
                  <CardTitle>Link to Entity/Application</CardTitle>
                  <CardDescription>
                    Optionally link this pull to an existing entity or loan application
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <FormField
                      control={form.control}
                      name="entityId"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Entity</FormLabel>
                          <FormControl>
                            <Select onValueChange={field.onChange} value={field.value}>
                              <SelectTrigger>
                                <SelectValue placeholder="Select entity" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="ent-1">ABC Industries Pvt Ltd</SelectItem>
                                <SelectItem value="ent-2">XYZ Trading Co</SelectItem>
                                <SelectItem value="ent-3">Kumar Enterprises</SelectItem>
                              </SelectContent>
                            </Select>
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="loanApplicationId"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Loan Application</FormLabel>
                          <FormControl>
                            <Select onValueChange={field.onChange} value={field.value}>
                              <SelectTrigger>
                                <SelectValue placeholder="Select application" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="app-1">APP-2025-0001</SelectItem>
                                <SelectItem value="app-2">APP-2025-0015</SelectItem>
                                <SelectItem value="app-3">APP-2025-0022</SelectItem>
                              </SelectContent>
                            </Select>
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                  <FormField
                    control={form.control}
                    name="purpose"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Purpose</FormLabel>
                        <FormControl>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <SelectTrigger>
                              <SelectValue placeholder="Select purpose" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="UNDERWRITING">Loan Underwriting</SelectItem>
                              <SelectItem value="ACCOUNT_REVIEW">Account Review</SelectItem>
                              <SelectItem value="CREDIT_LIMIT">Credit Limit Review</SelectItem>
                              <SelectItem value="COLLECTION">Collection</SelectItem>
                              <SelectItem value="OTHER">Other</SelectItem>
                            </SelectContent>
                          </Select>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>

              {/* Consent */}
              <Card>
                <CardContent className="pt-6">
                  <FormField
                    control={form.control}
                    name="consent"
                    render={({ field }) => (
                      <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                        <FormControl>
                          <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                        </FormControl>
                        <div className="space-y-1 leading-none">
                          <FormLabel>Customer Consent Confirmation *</FormLabel>
                          <FormDescription>
                            I confirm that the customer has provided explicit consent to pull their
                            credit report from the selected bureau. The customer understands that
                            this inquiry will be recorded in their credit history.
                          </FormDescription>
                          <FormMessage />
                        </div>
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
                  onClick={() => navigate('/admin/lending/credit')}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={createPullMutation.isPending}>
                  {createPullMutation.isPending && (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  )}
                  {createPullMutation.isPending ? 'Pulling Report...' : 'Pull Credit Report'}
                </Button>
              </div>
            </div>
          </div>
        </form>
      </Form>
    </div>
  );
}
