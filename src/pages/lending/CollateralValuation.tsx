import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowLeft, Building, Check, Upload, FileText, Calendar } from 'lucide-react';
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
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { formatCurrency, formatDate } from '@/lib/utils';

const valuationSchema = z.object({
  valuation_date: z.string().min(1, 'Valuation date is required'),
  market_value: z.string().min(1, 'Market value is required'),
  acceptable_value: z.string().min(1, 'Acceptable value is required'),
  margin_percentage: z.string().min(1, 'Margin is required'),
  valuation_agency: z.string().optional(),
  valuation_report_number: z.string().optional(),
  valuer_name: z.string().optional(),
  next_valuation_date: z.string().optional(),
  valuation_method: z.string().optional(),
  remarks: z.string().optional(),
});

type ValuationFormData = z.infer<typeof valuationSchema>;

// Mock data
const collateralDetails = {
  id: '1',
  security_code: 'SEC/2024/00125',
  loan_account: 'SMFC/LA/2024/00089',
  entity: 'ABC Industries',
  category: 'PRIMARY',
  type: 'IMMOVABLE_PROPERTY',
  description: 'Commercial Building at MG Road, Bangalore',
  current_value: 50000000,
  current_margin: 25,
  current_net_value: 37500000,
  last_valuation_date: '2024-06-15',
  property_address: 'Plot No. 123, MG Road, Bangalore - 560001',
  property_area: '5000 sq.ft.',
};

const valuationHistory = [
  {
    id: '1',
    valuation_date: '2024-06-15',
    market_value: 50000000,
    acceptable_value: 50000000,
    margin: 25,
    net_value: 37500000,
    agency: 'ABC Valuers Pvt Ltd',
    report_number: 'VAL/2024/00456',
    valuer: 'Mr. Ramesh Kumar',
    created_by: 'John Smith',
  },
  {
    id: '2',
    valuation_date: '2023-06-20',
    market_value: 45000000,
    acceptable_value: 45000000,
    margin: 25,
    net_value: 33750000,
    agency: 'ABC Valuers Pvt Ltd',
    report_number: 'VAL/2023/00234',
    valuer: 'Mr. Suresh Patil',
    created_by: 'John Smith',
  },
  {
    id: '3',
    valuation_date: '2022-06-25',
    market_value: 40000000,
    acceptable_value: 40000000,
    margin: 25,
    net_value: 30000000,
    agency: 'XYZ Valuations',
    report_number: 'VAL/2022/00789',
    valuer: 'Mr. Anil Sharma',
    created_by: 'Sarah Wilson',
  },
];

export default function CollateralValuation() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [isLoading, setIsLoading] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [calculatedNet, setCalculatedNet] = useState<number | null>(null);

  const form = useForm<ValuationFormData>({
    resolver: zodResolver(valuationSchema),
    defaultValues: {
      valuation_date: new Date().toISOString().split('T')[0],
      margin_percentage: collateralDetails.current_margin.toString(),
    },
  });

  const marketValue = form.watch('market_value');
  const marginPercentage = form.watch('margin_percentage');

  const calculateNetValue = () => {
    const market = parseFloat(marketValue || '0');
    const margin = parseFloat(marginPercentage || '0');
    if (market > 0 && margin >= 0) {
      const net = market * (1 - margin / 100);
      setCalculatedNet(net);
      form.setValue('acceptable_value', net.toString());
    }
  };

  const onSubmit = async (data: ValuationFormData) => {
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
          <h2 className="text-2xl font-bold mb-2">Valuation Updated Successfully</h2>
          <p className="text-muted-foreground mb-6">
            New valuation recorded for {collateralDetails.security_code}
          </p>
          <div className="flex gap-4 justify-center">
            <Button variant="outline" onClick={() => navigate('/lending/collaterals')}>
              View All Collaterals
            </Button>
            <Button variant="outline" onClick={() => navigate(`/lending/collaterals/${id}`)}>
              View Collateral Details
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Update Valuation"
        subtitle={`${collateralDetails.security_code} - ${collateralDetails.entity}`}
        breadcrumbs={[
          { label: 'Collaterals', to: '/lending/collaterals' },
          { label: collateralDetails.security_code },
          { label: 'Revalue' },
        ]}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Valuation Form */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>New Valuation Details</CardTitle>
            <CardDescription>Enter the latest valuation information</CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
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
                    name="valuation_method"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Valuation Method</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select method" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="MARKET_APPROACH">Market Approach</SelectItem>
                            <SelectItem value="INCOME_APPROACH">Income Approach</SelectItem>
                            <SelectItem value="COST_APPROACH">Cost Approach</SelectItem>
                            <SelectItem value="COMBINATION">Combination</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

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

                <div className="border-t pt-4">
                  <h3 className="font-medium mb-4">Valuation Agency Details</h3>
                  <div className="grid grid-cols-2 gap-4">
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
                      name="valuer_name"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Valuer Name</FormLabel>
                          <FormControl>
                            <Input placeholder="Name of valuer" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="valuation_report_number"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Report Number</FormLabel>
                          <FormControl>
                            <Input placeholder="Report/Reference number" {...field} />
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
                          <FormLabel>Next Valuation Due</FormLabel>
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
                        <Textarea
                          placeholder="Any observations or remarks about the valuation"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="border-t pt-4">
                  <Button type="button" variant="outline" className="mb-4">
                    <Upload className="h-4 w-4 mr-2" />
                    Upload Valuation Report
                  </Button>
                </div>

                <div className="flex gap-4 justify-end">
                  <Button type="button" variant="outline" onClick={() => navigate(-1)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={isLoading}>
                    <Building className="h-4 w-4 mr-2" />
                    {isLoading ? 'Saving...' : 'Update Valuation'}
                  </Button>
                </div>
              </form>
            </Form>
          </CardContent>
        </Card>

        {/* Collateral Summary */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Current Collateral</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground">Security Code</p>
                <p className="font-mono">{collateralDetails.security_code}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Type</p>
                <Badge variant="outline">{collateralDetails.type.replace(/_/g, ' ')}</Badge>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Description</p>
                <p className="text-sm">{collateralDetails.description}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Property Address</p>
                <p className="text-sm">{collateralDetails.property_address}</p>
              </div>
              <div className="border-t pt-4">
                <p className="text-sm text-muted-foreground">Current Value</p>
                <p className="text-xl font-bold">{formatCurrency(collateralDetails.current_value)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Current Net Value</p>
                <p className="text-xl font-bold text-green-600">
                  {formatCurrency(collateralDetails.current_net_value)}
                </p>
                <p className="text-xs text-muted-foreground">
                  After {collateralDetails.current_margin}% margin
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Last Valuation</p>
                <p className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  {formatDate(collateralDetails.last_valuation_date)}
                </p>
              </div>
            </CardContent>
          </Card>

          {calculatedNet && (
            <Card className="border-green-200 bg-green-50">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">New Net Value</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold text-green-600">{formatCurrency(calculatedNet)}</p>
                <p className="text-xs text-muted-foreground">
                  Change:{' '}
                  {calculatedNet > collateralDetails.current_net_value ? '+' : ''}
                  {formatCurrency(calculatedNet - collateralDetails.current_net_value)} (
                  {(
                    ((calculatedNet - collateralDetails.current_net_value) /
                      collateralDetails.current_net_value) *
                    100
                  ).toFixed(1)}
                  %)
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Valuation History */}
      <Card>
        <CardHeader>
          <CardTitle>Valuation History</CardTitle>
          <CardDescription>Previous valuations for this collateral</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead className="text-right">Market Value</TableHead>
                <TableHead className="text-right">Margin</TableHead>
                <TableHead className="text-right">Net Value</TableHead>
                <TableHead>Agency</TableHead>
                <TableHead>Report No.</TableHead>
                <TableHead>Valuer</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {valuationHistory.map((v) => (
                <TableRow key={v.id}>
                  <TableCell>{formatDate(v.valuation_date)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(v.market_value)}</TableCell>
                  <TableCell className="text-right">{v.margin}%</TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(v.net_value)}
                  </TableCell>
                  <TableCell>{v.agency}</TableCell>
                  <TableCell className="font-mono text-sm">{v.report_number}</TableCell>
                  <TableCell>{v.valuer}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
