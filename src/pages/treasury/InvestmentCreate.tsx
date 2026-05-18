import { zodResolver } from '@hookform/resolvers/zod';
import { Save, Calculator, Loader2 } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';

import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
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
import { useCreateInvestment } from '@/hooks/lending/useTreasuryInvestments';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import { formatCurrency } from '@/lib/utils';
import type { InvestmentCreateRequest } from '@/services/lending/treasuryInvestmentApi';

const investmentSchema = z
  .object({
    type: z.string().min(1, 'Investment type is required'),
    category: z.string().min(1, 'Category is required'),
    issuer: z.string().min(1, 'Issuer is required'),
    description: z.string().min(1, 'Description is required'),
    isin: z.string().optional(),
    faceValue: z.number().positive('Face value must be greater than 0'),
    purchasePrice: z.number().positive('Purchase price must be greater than 0'),
    units: z.number().positive('Units must be greater than 0'),
    couponRate: z.number().min(0, 'Coupon rate must be >= 0'),
    ytm: z.number().min(0, 'YTM must be >= 0'),
    purchaseDate: z.string().min(1, 'Purchase date is required'),
    maturityDate: z.string().optional(),
    couponFrequency: z.string().min(1, 'Coupon frequency is required'),
    broker: z.string().optional(),
    remarks: z.string().optional(),
  })
  .superRefine((val, ctx) => {
    if (val.maturityDate && val.maturityDate < val.purchaseDate) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Maturity date cannot precede purchase date',
        path: ['maturityDate'],
      });
    }
  });

type InvestmentFormData = z.infer<typeof investmentSchema>;

const investmentTypes = [
  { id: 'GSEC', name: 'Government Securities' },
  { id: 'SDL', name: 'State Development Loans' },
  { id: 'TBILL', name: 'Treasury Bills' },
  { id: 'CORP_BOND', name: 'Corporate Bonds' },
  { id: 'NCD', name: 'Non-Convertible Debentures' },
  { id: 'CP', name: 'Commercial Paper' },
  { id: 'CD', name: 'Certificate of Deposit' },
  { id: 'MUTUAL_FUND', name: 'Mutual Fund' },
];

const categories = [
  { id: 'HTM', name: 'Held to Maturity (HTM)' },
  { id: 'AFS', name: 'Available for Sale (AFS)' },
  { id: 'HFT', name: 'Held for Trading (HFT)' },
];

const couponFrequencies = [
  { id: 'ANNUAL', name: 'Annual' },
  { id: 'SEMI_ANNUAL', name: 'Semi-Annual' },
  { id: 'QUARTERLY', name: 'Quarterly' },
  { id: 'MONTHLY', name: 'Monthly' },
  { id: 'ZERO', name: 'Zero Coupon' },
];

export default function InvestmentCreate() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const createMutation = useCreateInvestment();

  const form = useForm<InvestmentFormData>({
    resolver: zodResolver(investmentSchema),
    defaultValues: {
      type: '',
      category: 'HTM',
      issuer: '',
      description: '',
      isin: '',
      faceValue: 0,
      purchasePrice: 0,
      units: 1,
      couponRate: 0,
      ytm: 0,
      purchaseDate: new Date().toISOString().split('T')[0],
      maturityDate: '',
      couponFrequency: 'SEMI_ANNUAL',
      broker: '',
      remarks: '',
    },
  });

  const faceValue = form.watch('faceValue');
  const purchasePrice = form.watch('purchasePrice');
  const units = form.watch('units');
  const couponRate = form.watch('couponRate');

  const totalFaceValue = Number(faceValue) * Number(units);
  const totalPurchaseValue = Number(purchasePrice) * Number(units);
  const annualCouponIncome = (totalFaceValue * Number(couponRate)) / 100;

  const onSubmit = async (data: InvestmentFormData) => {
    // Money fields go over the wire as strings to preserve Decimal precision
    // (CLAUDE.md §6.2). The BE coerces them back to Python Decimal.
    const payload: InvestmentCreateRequest = {
      type: data.type as InvestmentCreateRequest['type'],
      category: data.category as InvestmentCreateRequest['category'],
      issuer: data.issuer,
      description: data.description,
      ...(data.isin ? { isin: data.isin } : {}),
      faceValue: String(data.faceValue),
      purchasePrice: String(data.purchasePrice),
      units: String(data.units),
      couponRate: String(data.couponRate),
      ytm: String(data.ytm),
      couponFrequency: data.couponFrequency as InvestmentCreateRequest['couponFrequency'],
      purchaseDate: data.purchaseDate,
      ...(data.maturityDate ? { maturityDate: data.maturityDate } : {}),
      ...(data.broker ? { broker: data.broker } : {}),
      ...(data.remarks ? { remarks: data.remarks } : {}),
    };

    try {
      const created = await createMutation.mutateAsync(payload);
      toast({
        title: 'Investment recorded',
        description: `Investment ${created.investmentNumber} created successfully.`,
      });
      navigate('/admin/treasury/investments');
    } catch (err) {
      showErrorToast(err, toast);
    }
  };

  const isSubmitting = createMutation.isPending;

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="New Investment"
        subtitle="Record a new treasury investment"
        breadcrumbs={[
          { label: 'Investments', to: '/admin/treasury/investments' },
          { label: 'New' },
        ]}
      />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            {/* Main Form */}
            <div className="space-y-6 lg:col-span-2">
              {/* Investment Details */}
              <Card>
                <CardHeader>
                  <CardTitle>Investment Details</CardTitle>
                  <CardDescription>Basic investment information</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <FormField
                      control={form.control}
                      name="type"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Investment Type</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select type" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              {investmentTypes.map((type) => (
                                <SelectItem key={type.id} value={type.id}>
                                  {type.name}
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
                      name="category"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Classification Category</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select category" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              {categories.map((cat) => (
                                <SelectItem key={cat.id} value={cat.id}>
                                  {cat.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <FormDescription>As per RBI investment classification</FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <FormField
                    control={form.control}
                    name="issuer"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Issuer</FormLabel>
                        <FormControl>
                          <Input placeholder="e.g., Government of India, HDFC Ltd" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="description"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Description</FormLabel>
                        <FormControl>
                          <Input placeholder="e.g., G-Sec 7.26% 2033" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="isin"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>ISIN (Optional)</FormLabel>
                        <FormControl>
                          <Input placeholder="INE..." {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>

              {/* Financial Details */}
              <Card>
                <CardHeader>
                  <CardTitle>Financial Details</CardTitle>
                  <CardDescription>Pricing and yield information</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                    <FormField
                      control={form.control}
                      name="faceValue"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Face Value (per unit)</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              placeholder="100"
                              {...field}
                              onChange={(e) => field.onChange(Number(e.target.value))}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="purchasePrice"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Purchase Price (per unit)</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              placeholder="99.50"
                              {...field}
                              onChange={(e) => field.onChange(Number(e.target.value))}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="units"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Units / Quantity</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              placeholder="100000"
                              {...field}
                              onChange={(e) => field.onChange(Number(e.target.value))}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                    <FormField
                      control={form.control}
                      name="couponRate"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Coupon Rate (%)</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              step="0.01"
                              placeholder="7.26"
                              {...field}
                              onChange={(e) => field.onChange(Number(e.target.value))}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="ytm"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Yield to Maturity (%)</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              step="0.01"
                              placeholder="7.10"
                              {...field}
                              onChange={(e) => field.onChange(Number(e.target.value))}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="couponFrequency"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Coupon Frequency</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select frequency" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              {couponFrequencies.map((freq) => (
                                <SelectItem key={freq.id} value={freq.id}>
                                  {freq.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <FormField
                      control={form.control}
                      name="purchaseDate"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Purchase Date</FormLabel>
                          <FormControl>
                            <Input type="date" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="maturityDate"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Maturity Date (Optional for MFs)</FormLabel>
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

              {/* Additional Info */}
              <Card>
                <CardHeader>
                  <CardTitle>Additional Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <FormField
                    control={form.control}
                    name="broker"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Broker / Dealer (Optional)</FormLabel>
                        <FormControl>
                          <Input placeholder="Broker name" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="remarks"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Remarks (Optional)</FormLabel>
                        <FormControl>
                          <Textarea placeholder="Additional notes..." rows={3} {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>
            </div>

            {/* Summary Sidebar */}
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Calculator className="h-5 w-5" />
                    Investment Summary
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Total Face Value</span>
                    <span className="font-bold tabular-nums">{formatCurrency(totalFaceValue)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Total Purchase Value</span>
                    <span className="font-bold tabular-nums">
                      {formatCurrency(totalPurchaseValue)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Premium / (Discount)</span>
                    <span
                      className={`font-bold tabular-nums ${
                        totalPurchaseValue - totalFaceValue > 0 ? 'text-red-600' : 'text-green-600'
                      }`}
                    >
                      {formatCurrency(totalPurchaseValue - totalFaceValue)}
                    </span>
                  </div>
                  <div className="border-t pt-4">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Annual Coupon Income</span>
                      <span className="font-bold tabular-nums text-green-600">
                        {formatCurrency(annualCouponIncome)}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="space-y-2">
                    <Button type="submit" className="w-full" disabled={isSubmitting}>
                      {isSubmitting ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <Save className="mr-2 h-4 w-4" />
                      )}
                      Record Investment
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      className="w-full"
                      onClick={() => navigate(-1)}
                      disabled={isSubmitting}
                    >
                      Cancel
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </form>
      </Form>
    </div>
  );
}
