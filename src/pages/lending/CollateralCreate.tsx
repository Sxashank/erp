import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowLeft, Building, Check, Upload } from 'lucide-react';
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
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { formatCurrency } from '@/lib/utils';

const collateralSchema = z.object({
  loan_account_id: z.string().min(1, 'Loan account is required'),
  category: z.enum(['PRIMARY', 'COLLATERAL', 'GUARANTEE']),
  security_type: z.string().min(1, 'Security type is required'),
  description: z.string().min(1, 'Description is required'),

  // Valuation
  market_value: z.string().min(1, 'Market value is required'),
  acceptable_value: z.string().min(1, 'Acceptable value is required'),
  margin_percentage: z.string().min(1, 'Margin is required'),
  valuation_date: z.string().min(1, 'Valuation date is required'),
  valuation_agency: z.string().optional(),
  valuation_report_number: z.string().optional(),
  next_valuation_date: z.string().optional(),

  // Property Details (for immovable property)
  property_address: z.string().optional(),
  property_area: z.string().optional(),
  property_unit: z.string().optional(),
  survey_number: z.string().optional(),

  // Document Details
  document_type: z.string().optional(),
  document_number: z.string().optional(),
  document_date: z.string().optional(),

  // Charge Details
  charge_type: z.string().optional(),
  charge_holder: z.string().optional(),

  // Guarantee Details (for guarantees)
  guarantor_name: z.string().optional(),
  guarantor_pan: z.string().optional(),
  guarantee_amount: z.string().optional(),
  guarantee_validity: z.string().optional(),

  remarks: z.string().optional(),
});

type CollateralFormData = z.infer<typeof collateralSchema>;

// Mock data
const loanAccounts = [
  { id: '1', number: 'SMFC/LA/2025/00145', entity: 'Sunrise Industries', sanctioned: 15000000 },
  { id: '2', number: 'SMFC/LA/2025/00146', entity: 'Metro Logistics', sanctioned: 25000000 },
  { id: '3', number: 'SMFC/LA/2025/00147', entity: 'Eastern Trading', sanctioned: 10000000 },
];

const securityTypes = {
  PRIMARY: [
    { value: 'IMMOVABLE_PROPERTY', label: 'Immovable Property' },
    { value: 'MOVABLE_PROPERTY', label: 'Movable Property' },
    { value: 'PLANT_MACHINERY', label: 'Plant & Machinery' },
    { value: 'STOCK_RECEIVABLES', label: 'Stock & Receivables' },
    { value: 'VEHICLES', label: 'Vehicles' },
  ],
  COLLATERAL: [
    { value: 'IMMOVABLE_PROPERTY', label: 'Immovable Property' },
    { value: 'FIXED_DEPOSIT', label: 'Fixed Deposit' },
    { value: 'SHARES_SECURITIES', label: 'Shares & Securities' },
    { value: 'GOLD', label: 'Gold' },
    { value: 'INSURANCE_POLICY', label: 'Insurance Policy' },
  ],
  GUARANTEE: [
    { value: 'PERSONAL_GUARANTEE', label: 'Personal Guarantee' },
    { value: 'CORPORATE_GUARANTEE', label: 'Corporate Guarantee' },
    { value: 'BANK_GUARANTEE', label: 'Bank Guarantee' },
    { value: 'GOVERNMENT_GUARANTEE', label: 'Government Guarantee' },
  ],
};

const chargeTypes = [
  { value: 'EXCLUSIVE_CHARGE', label: 'Exclusive Charge' },
  { value: 'PARI_PASSU', label: 'Pari Passu' },
  { value: 'SECOND_CHARGE', label: 'Second Charge' },
  { value: 'HYPOTHECATION', label: 'Hypothecation' },
  { value: 'PLEDGE', label: 'Pledge' },
  { value: 'MORTGAGE', label: 'Mortgage' },
];

export default function CollateralCreate() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [selectedLoan, setSelectedLoan] = useState<typeof loanAccounts[0] | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);
  const [calculatedNet, setCalculatedNet] = useState<number | null>(null);

  const form = useForm<CollateralFormData>({
    resolver: zodResolver(collateralSchema),
    defaultValues: {
      category: 'PRIMARY',
      margin_percentage: '25',
    },
  });

  const category = form.watch('category');
  const marketValue = form.watch('market_value');
  const marginPercentage = form.watch('margin_percentage');

  // Calculate net value when market value or margin changes
  const calculateNetValue = () => {
    const market = parseFloat(marketValue || '0');
    const margin = parseFloat(marginPercentage || '0');
    if (market > 0 && margin >= 0) {
      const net = market * (1 - margin / 100);
      setCalculatedNet(net);
      form.setValue('acceptable_value', net.toString());
    }
  };

  const onLoanSelect = (loanId: string) => {
    const loan = loanAccounts.find((l) => l.id === loanId);
    setSelectedLoan(loan || null);
    form.setValue('loan_account_id', loanId);
  };

  const onSubmit = async (data: CollateralFormData) => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setIsLoading(false);
    setShowSuccess(true);
  };

  if (showSuccess) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Check className="h-8 w-8 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold mb-2">Collateral Added Successfully</h2>
          <p className="text-muted-foreground mb-6">
            Security Code: <span className="font-mono">SEC/2025/00156</span>
          </p>
          <div className="flex gap-4 justify-center">
            <Button variant="outline" onClick={() => navigate('/lending/collaterals')}>
              View All Collaterals
            </Button>
            <Button variant="outline" onClick={() => setShowSuccess(false)}>
              Add Another
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Add Collateral"
        subtitle="Register a new security or collateral"
        breadcrumbs={[
          { label: 'Collaterals', to: '/lending/collaterals' },
          { label: 'New' },
        ]}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Collateral Details</CardTitle>
            <CardDescription>Enter security/collateral information</CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                {/* Basic Info */}
                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="loan_account_id"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Loan Account *</FormLabel>
                        <Select onValueChange={onLoanSelect} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select loan account" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {loanAccounts.map((acc) => (
                              <SelectItem key={acc.id} value={acc.id}>
                                {acc.number} - {acc.entity}
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
                        <FormLabel>Security Category *</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select category" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="PRIMARY">Primary Security</SelectItem>
                            <SelectItem value="COLLATERAL">Collateral Security</SelectItem>
                            <SelectItem value="GUARANTEE">Guarantee</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="security_type"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Security Type *</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select type" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {(securityTypes[category as keyof typeof securityTypes] || []).map((type) => (
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
                    name="charge_type"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Charge Type</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select charge type" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {chargeTypes.map((type) => (
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

                <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Description *</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="Detailed description of the security/collateral"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Valuation Section */}
                <div className="border-t pt-4">
                  <h3 className="font-medium mb-4">Valuation Details</h3>
                  <div className="grid grid-cols-3 gap-4">
                    <FormField
                      control={form.control}
                      name="market_value"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Market Value *</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              placeholder="Enter value"
                              {...field}
                              onBlur={() => calculateNetValue()}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="margin_percentage"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Margin % *</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              placeholder="25"
                              {...field}
                              onBlur={() => calculateNetValue()}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="acceptable_value"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Acceptable Value *</FormLabel>
                          <FormControl>
                            <Input type="number" placeholder="Net value" {...field} />
                          </FormControl>
                          <FormDescription>After margin deduction</FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <div className="grid grid-cols-3 gap-4 mt-4">
                    <FormField
                      control={form.control}
                      name="valuation_date"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Valuation Date *</FormLabel>
                          <FormControl>
                            <Input type="date" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="valuation_agency"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Valuation Agency</FormLabel>
                          <FormControl>
                            <Input placeholder="Agency name" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="next_valuation_date"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Next Valuation Date</FormLabel>
                          <FormControl>
                            <Input type="date" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </div>

                {/* Property Details - Show for immovable property */}
                {(form.watch('security_type') === 'IMMOVABLE_PROPERTY') && (
                  <div className="border-t pt-4">
                    <h3 className="font-medium mb-4">Property Details</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <FormField
                        control={form.control}
                        name="property_address"
                        render={({ field }) => (
                          <FormItem className="col-span-2">
                            <FormLabel>Property Address</FormLabel>
                            <FormControl>
                              <Textarea placeholder="Full address of property" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="property_area"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Area</FormLabel>
                            <FormControl>
                              <Input placeholder="e.g., 2500" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="property_unit"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Unit</FormLabel>
                            <Select onValueChange={field.onChange} value={field.value}>
                              <FormControl>
                                <SelectTrigger>
                                  <SelectValue placeholder="Select unit" />
                                </SelectTrigger>
                              </FormControl>
                              <SelectContent>
                                <SelectItem value="SQ_FT">Sq. Ft.</SelectItem>
                                <SelectItem value="SQ_MT">Sq. Mt.</SelectItem>
                                <SelectItem value="ACRES">Acres</SelectItem>
                                <SelectItem value="HECTARES">Hectares</SelectItem>
                              </SelectContent>
                            </Select>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="survey_number"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Survey Number</FormLabel>
                            <FormControl>
                              <Input placeholder="Survey/Plot number" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>
                  </div>
                )}

                {/* Guarantee Details - Show for guarantees */}
                {category === 'GUARANTEE' && (
                  <div className="border-t pt-4">
                    <h3 className="font-medium mb-4">Guarantor Details</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <FormField
                        control={form.control}
                        name="guarantor_name"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Guarantor Name</FormLabel>
                            <FormControl>
                              <Input placeholder="Full name" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="guarantor_pan"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>PAN Number</FormLabel>
                            <FormControl>
                              <Input placeholder="ABCDE1234F" maxLength={10} {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="guarantee_amount"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Guarantee Amount</FormLabel>
                            <FormControl>
                              <Input type="number" placeholder="Amount" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="guarantee_validity"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Validity Date</FormLabel>
                            <FormControl>
                              <Input type="date" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>
                  </div>
                )}

                {/* Document Details */}
                <div className="border-t pt-4">
                  <h3 className="font-medium mb-4">Document Details</h3>
                  <div className="grid grid-cols-3 gap-4">
                    <FormField
                      control={form.control}
                      name="document_type"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Document Type</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select type" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="SALE_DEED">Sale Deed</SelectItem>
                              <SelectItem value="TITLE_DEED">Title Deed</SelectItem>
                              <SelectItem value="MORTGAGE_DEED">Mortgage Deed</SelectItem>
                              <SelectItem value="LEASE_DEED">Lease Deed</SelectItem>
                              <SelectItem value="INVOICE">Invoice</SelectItem>
                              <SelectItem value="RC_BOOK">RC Book</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="document_number"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Document Number</FormLabel>
                          <FormControl>
                            <Input placeholder="Document number" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="document_date"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Document Date</FormLabel>
                          <FormControl>
                            <Input type="date" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </div>

                <FormField
                  control={form.control}
                  name="remarks"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Remarks</FormLabel>
                      <FormControl>
                        <Textarea placeholder="Any additional remarks" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="flex gap-4 justify-end">
                  <Button type="button" variant="outline" onClick={() => navigate(-1)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={isLoading}>
                    <Building className="h-4 w-4 mr-2" />
                    {isLoading ? 'Saving...' : 'Add Collateral'}
                  </Button>
                </div>
              </form>
            </Form>
          </CardContent>
        </Card>

        {/* Summary Panel */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Loan Summary</CardTitle>
            <CardDescription>
              {selectedLoan ? selectedLoan.number : 'Select a loan account'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {selectedLoan ? (
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground">Entity</p>
                  <p className="font-medium">{selectedLoan.entity}</p>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">Sanctioned Amount</p>
                  <p className="text-2xl font-bold">{formatCurrency(selectedLoan.sanctioned)}</p>
                </div>

                {calculatedNet && (
                  <div className="border-t pt-4">
                    <p className="text-sm text-muted-foreground">Net Realizable Value</p>
                    <p className="text-2xl font-bold text-green-600">
                      {formatCurrency(calculatedNet)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Coverage: {((calculatedNet / selectedLoan.sanctioned) * 100).toFixed(1)}%
                    </p>
                  </div>
                )}

                <div className="border-t pt-4">
                  <Button variant="outline" className="w-full">
                    <Upload className="h-4 w-4 mr-2" />
                    Upload Documents
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Building className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Select a loan account to view details</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
