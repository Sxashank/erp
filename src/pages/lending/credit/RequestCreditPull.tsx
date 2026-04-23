/**
 * Request Credit Pull Page
 * Form to initiate a credit bureau pull for a customer
 */

import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  ArrowLeft,
  CreditCard,
  User,
  AlertTriangle,
  Info,
  CheckCircle,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
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
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { DatePicker } from '@/components/ui/date-picker';

import { logger } from '@/lib/logger';
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

type CreditPullFormData = z.infer<typeof creditPullFormSchema>;

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
  const [isSubmitting, setIsSubmitting] = useState(false);
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

  const form = useForm<CreditPullFormData>({
    resolver: zodResolver(creditPullFormSchema) as any,
    defaultValues,
  });

  const selectedBureau = form.watch('bureau');
  const pullType = form.watch('pullType');
  const panNumber = form.watch('panNumber');

  // Check for existing score when PAN changes
  const checkExistingScore = async (pan: string) => {
    // Mock check - in reality this would call the API
    if (pan === 'ABCDE1234F') {
      setExistingScore({
        score: 782,
        bureau: 'CIBIL',
        pulledAt: '2025-01-10',
        isValid: true,
      });
    } else {
      setExistingScore(null);
    }
  };

  const onSubmit = async (data: CreditPullFormData) => {
    setIsSubmitting(true);
    try {
      // API call would go here
      logger.debug('Submitting credit pull request:', data);
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Navigate to the pull result
      navigate('/lending/credit/pulls/new-pull-id');
    } catch (error) {
      console.error('Error submitting credit pull:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/lending/credit')}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Request Credit Report</h1>
          <p className="text-muted-foreground">
            Pull credit report from CIBIL, Experian, Equifax, or CRIF
          </p>
        </div>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit as any)} className="space-y-6">
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
                                className={`flex items-start space-x-3 rounded-lg border p-4 cursor-pointer transition-colors ${
                                  field.value === key
                                    ? 'border-primary bg-primary/5'
                                    : 'border-muted hover:border-primary/50'
                                }`}
                                onClick={() => field.onChange(key)}
                              >
                                <RadioGroupItem value={key} id={key} className="mt-1" />
                                <div className="space-y-1">
                                  <label
                                    htmlFor={key}
                                    className="font-medium cursor-pointer"
                                  >
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
                              className={`flex items-start space-x-3 rounded-lg border p-4 cursor-pointer transition-colors ${
                                field.value === 'SOFT'
                                  ? 'border-green-500 bg-green-50'
                                  : 'border-muted hover:border-green-300'
                              }`}
                              onClick={() => field.onChange('SOFT')}
                            >
                              <RadioGroupItem value="SOFT" id="soft" className="mt-1" />
                              <div className="space-y-1">
                                <label htmlFor="soft" className="font-medium cursor-pointer">
                                  Soft Pull
                                </label>
                                <p className="text-xs text-muted-foreground">
                                  Does not affect customer's credit score. Use for
                                  pre-qualification and account reviews.
                                </p>
                                <Badge variant="outline" className="bg-green-50 text-green-700">
                                  Recommended
                                </Badge>
                              </div>
                            </div>
                            <div
                              className={`flex items-start space-x-3 rounded-lg border p-4 cursor-pointer transition-colors ${
                                field.value === 'HARD'
                                  ? 'border-amber-500 bg-amber-50'
                                  : 'border-muted hover:border-amber-300'
                              }`}
                              onClick={() => field.onChange('HARD')}
                            >
                              <RadioGroupItem value="HARD" id="hard" className="mt-1" />
                              <div className="space-y-1">
                                <label htmlFor="hard" className="font-medium cursor-pointer">
                                  Hard Pull
                                </label>
                                <p className="text-xs text-muted-foreground">
                                  May temporarily affect credit score. Use only for final
                                  loan approval decisions.
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
            <div className="lg:col-span-2 space-y-6">
              {/* Customer Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="h-5 w-5" />
                    Customer Information
                  </CardTitle>
                  <CardDescription>
                    Enter customer details for credit bureau lookup
                  </CardDescription>
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
                              className="uppercase font-mono"
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
                      <AlertTitle className="text-green-700">
                        Valid Report Found
                      </AlertTitle>
                      <AlertDescription className="text-green-600">
                        A valid {existingScore.bureau} report exists for this PAN with score{' '}
                        <strong>{existingScore.score}</strong> (pulled on{' '}
                        {existingScore.pulledAt}). You may use the existing report instead
                        of pulling a new one.
                        <div className="mt-2">
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => navigate('/lending/credit/pulls/existing-id')}
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
                          <FormDescription>
                            Helps in accurate matching
                          </FormDescription>
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
                          <Input
                            type="email"
                            placeholder="customer@example.com"
                            {...field}
                          />
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
                              <Select
                                onValueChange={field.onChange}
                                value={field.value}
                              >
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
                          <Checkbox
                            checked={field.value}
                            onCheckedChange={field.onChange}
                          />
                        </FormControl>
                        <div className="space-y-1 leading-none">
                          <FormLabel>Customer Consent Confirmation *</FormLabel>
                          <FormDescription>
                            I confirm that the customer has provided explicit consent to
                            pull their credit report from the selected bureau. The
                            customer understands that this inquiry will be recorded in
                            their credit history.
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
                  onClick={() => navigate('/lending/credit')}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {isSubmitting ? 'Pulling Report...' : 'Pull Credit Report'}
                </Button>
              </div>
            </div>
          </div>
        </form>
      </Form>
    </div>
  );
}
