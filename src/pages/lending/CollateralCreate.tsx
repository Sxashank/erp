import { zodResolver } from '@hookform/resolvers/zod';
import { Building, Check, Upload } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';

import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
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
import { useCreateCollateral } from '@/hooks/lending/useCollateral';
import { useLoanAccount } from '@/hooks/lending/useLoanAccount';
import { useLoanAccounts } from '@/hooks/lending/useLoanAccounts';
import { useToast } from '@/hooks/use-toast';
import { logger } from '@/lib/logger';
import { formatCurrency } from '@/lib/utils';
import type {
  CreateCollateralRequest,
  SecurityCategory,
  ChargeType,
} from '@/services/lending/collateralApi';

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

const chargeTypes: { value: ChargeType; label: string }[] = [
  { value: 'FIRST', label: 'First Charge / Exclusive' },
  { value: 'PARI_PASSU', label: 'Pari Passu' },
  { value: 'SECOND', label: 'Second Charge' },
  { value: 'SUBSERVIENT', label: 'Subservient' },
];

export default function CollateralCreate() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [selectedLoanId, setSelectedLoanId] = useState<string | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);
  const [calculatedNet, setCalculatedNet] = useState<number | null>(null);
  const [createdSecurityNumber, setCreatedSecurityNumber] = useState<number | null>(null);

  const loanAccountsQuery = useLoanAccounts({ page: 1, pageSize: 100 });
  const selectedLoanDetail = useLoanAccount(selectedLoanId ?? undefined);
  const createMutation = useCreateCollateral();

  const loanAccounts = loanAccountsQuery.data?.items ?? [];
  const selectedLoan = useMemo(() => {
    if (!selectedLoanId) return null;
    return loanAccounts.find((acc) => acc.id === selectedLoanId) ?? null;
  }, [loanAccounts, selectedLoanId]);

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
    setSelectedLoanId(loanId);
    form.setValue('loan_account_id', loanId);
  };

  const onSubmit = async (data: CollateralFormData) => {
    // Resolve the sanction id from the selected loan account (the BE
    // collateral endpoint is sanction-scoped, not loan-account-scoped).
    const sanctionId = selectedLoanDetail.data?.sanctionId;
    if (!sanctionId) {
      toast({
        title: 'Cannot save collateral',
        description: 'Could not resolve the sanction for the selected loan account.',
        variant: 'destructive',
      });
      return;
    }

    const propertyDetails =
      data.security_type === 'IMMOVABLE_PROPERTY'
        ? {
            address: data.property_address,
            areaSqft: data.property_area,
            surveyNumber: data.survey_number,
            type: data.property_unit,
          }
        : undefined;

    const ownerDetails =
      data.category === 'GUARANTEE' && data.guarantor_name
        ? {
            name: data.guarantor_name,
            isThirdParty: true,
          }
        : undefined;

    const valuationDetails = {
      declaredValue: data.market_value,
      marketValue: data.market_value,
      valuationDate: data.valuation_date,
      valuerFirm: data.valuation_agency,
      reportPath: data.valuation_report_number,
    };

    // BE chargeType expects FIRST/SECOND/PARI_PASSU/SUBSERVIENT. The
    // form historically exposed a richer vocabulary; map down to the BE
    // enum and default to FIRST when unknown.
    const chargeTypeMap: Record<string, ChargeType> = {
      EXCLUSIVE_CHARGE: 'FIRST',
      FIRST: 'FIRST',
      PARI_PASSU: 'PARI_PASSU',
      SECOND_CHARGE: 'SECOND',
      SECOND: 'SECOND',
      SUBSERVIENT: 'SUBSERVIENT',
      HYPOTHECATION: 'FIRST',
      PLEDGE: 'FIRST',
      MORTGAGE: 'FIRST',
    };

    const payload: CreateCollateralRequest = {
      sanctionId,
      securityCategory: data.category as SecurityCategory,
      securityType: data.security_type,
      description: data.description,
      acceptableValue: data.acceptable_value,
      marginPercentage: data.margin_percentage,
      chargeType: data.charge_type ? (chargeTypeMap[data.charge_type] ?? 'FIRST') : 'FIRST',
      propertyDetails,
      ownerDetails,
      valuationDetails,
    };

    try {
      const created = await createMutation.mutateAsync(payload);
      setCreatedSecurityNumber(created.securityNumber);
      toast({
        title: 'Collateral added',
        description: `Security #${created.securityNumber} recorded successfully.`,
      });
      setShowSuccess(true);
    } catch (error) {
      logger.error('Failed to create collateral', error);
      const message =
        (error as { response?: { data?: { message?: string; detail?: string } } }).response?.data
          ?.message ||
        (error as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
        'Failed to save collateral. Please try again.';
      toast({ title: 'Save failed', description: message, variant: 'destructive' });
    }
  };

  const isSubmitting = createMutation.isPending;

  if (showSuccess) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
            <Check className="h-8 w-8 text-green-600" />
          </div>
          <h2 className="mb-2 text-2xl font-bold">Collateral Added Successfully</h2>
          {createdSecurityNumber !== null && (
            <p className="mb-6 text-muted-foreground">
              Security #: <span className="font-mono">{createdSecurityNumber}</span>
            </p>
          )}
          <div className="flex justify-center gap-4">
            <Button variant="outline" onClick={() => navigate('/admin/lending/collaterals')}>
              View All Collaterals
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setShowSuccess(false);
                setCreatedSecurityNumber(null);
                form.reset({ category: 'PRIMARY', margin_percentage: '25' });
                setCalculatedNet(null);
                setSelectedLoanId(null);
              }}
            >
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
        breadcrumbs={[{ label: 'Collaterals', to: '/admin/lending/collaterals' }, { label: 'New' }]}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
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
                              <SelectValue
                                placeholder={
                                  loanAccountsQuery.isLoading
                                    ? 'Loading loan accounts...'
                                    : 'Select loan account'
                                }
                              />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {loanAccounts.map((acc) => (
                              <SelectItem key={acc.id} value={acc.id}>
                                {acc.loanAccountNumber} - {acc.entityName ?? 'Unknown entity'}
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
                            {(securityTypes[category as keyof typeof securityTypes] || []).map(
                              (type) => (
                                <SelectItem key={type.value} value={type.value}>
                                  {type.label}
                                </SelectItem>
                              ),
                            )}
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
                  <h3 className="mb-4 font-medium">Valuation Details</h3>
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

                  <div className="mt-4 grid grid-cols-3 gap-4">
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
                {form.watch('security_type') === 'IMMOVABLE_PROPERTY' && (
                  <div className="border-t pt-4">
                    <h3 className="mb-4 font-medium">Property Details</h3>
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
                    <h3 className="mb-4 font-medium">Guarantor Details</h3>
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
                  <h3 className="mb-4 font-medium">Document Details</h3>
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

                <div className="flex justify-end gap-4">
                  <Button type="button" variant="outline" onClick={() => navigate(-1)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={isSubmitting}>
                    <Building className="mr-2 h-4 w-4" />
                    {isSubmitting ? 'Saving...' : 'Add Collateral'}
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
              {selectedLoan ? selectedLoan.loanAccountNumber : 'Select a loan account'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {selectedLoan ? (
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground">Entity</p>
                  <p className="font-medium">{selectedLoan.entityName ?? '—'}</p>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">Sanctioned Amount</p>
                  <p className="text-2xl font-bold">
                    {formatCurrency(Number(selectedLoan.sanctionedAmount))}
                  </p>
                </div>

                {calculatedNet !== null && (
                  <div className="border-t pt-4">
                    <p className="text-sm text-muted-foreground">Net Realizable Value</p>
                    <p className="text-2xl font-bold text-green-600">
                      {formatCurrency(calculatedNet)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Coverage:{' '}
                      {((calculatedNet / Number(selectedLoan.sanctionedAmount)) * 100).toFixed(1)}%
                    </p>
                  </div>
                )}

                <div className="border-t pt-4">
                  <Button variant="outline" className="w-full" type="button" disabled>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload Documents
                  </Button>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-muted-foreground">
                <Building className="mx-auto mb-4 h-12 w-12 opacity-50" />
                <p>Select a loan account to view details</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
