import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/common/PageHeader';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from '@/components/ui/form';
import {
  ArrowLeft,
  Briefcase,
  Save,
  Calculator,
} from 'lucide-react';

const investmentSchema = z.object({
  type: z.string().min(1, 'Investment type is required'),
  category: z.string().min(1, 'Category is required'),
  issuer: z.string().min(1, 'Issuer is required'),
  description: z.string().min(1, 'Description is required'),
  isin: z.string().optional(),
  faceValue: z.number().min(1, 'Face value is required'),
  purchasePrice: z.number().min(1, 'Purchase price is required'),
  units: z.number().min(1, 'Units must be at least 1'),
  couponRate: z.number().min(0, 'Coupon rate must be >= 0'),
  ytm: z.number().min(0, 'YTM must be >= 0'),
  purchaseDate: z.string().min(1, 'Purchase date is required'),
  maturityDate: z.string().min(1, 'Maturity date is required'),
  couponFrequency: z.string().min(1, 'Coupon frequency is required'),
  broker: z.string().optional(),
  remarks: z.string().optional(),
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

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

export default function InvestmentCreate() {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);

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

  const totalFaceValue = faceValue * units;
  const totalPurchaseValue = purchasePrice * units;
  const annualCouponIncome = (totalFaceValue * couponRate) / 100;

  const onSubmit = async (data: InvestmentFormData) => {
    setIsSubmitting(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    setIsSubmitting(false);
    navigate('/admin/treasury/investments');
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
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
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Form */}
            <div className="lg:col-span-2 space-y-6">
              {/* Investment Details */}
              <Card>
                <CardHeader>
                  <CardTitle>Investment Details</CardTitle>
                  <CardDescription>Basic investment information</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                              {investmentTypes.map(type => (
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
                              {categories.map(cat => (
                                <SelectItem key={cat.id} value={cat.id}>
                                  {cat.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <FormDescription>
                            As per RBI investment classification
                          </FormDescription>
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
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                              {couponFrequencies.map(freq => (
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

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                          <FormLabel>Maturity Date</FormLabel>
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
                    <span className="font-bold">{formatCurrency(totalFaceValue)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Total Purchase Value</span>
                    <span className="font-bold">{formatCurrency(totalPurchaseValue)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Premium / (Discount)</span>
                    <span className={`font-bold ${totalPurchaseValue - totalFaceValue > 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {formatCurrency(totalPurchaseValue - totalFaceValue)}
                    </span>
                  </div>
                  <div className="border-t pt-4">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Annual Coupon Income</span>
                      <span className="font-bold text-green-600">
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
                      <Save className="h-4 w-4 mr-2" />
                      {isSubmitting ? 'Saving...' : 'Record Investment'}
                    </Button>
                    <Button type="button" variant="outline" className="w-full" onClick={() => navigate(-1)}>
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
