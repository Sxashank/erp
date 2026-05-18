import { zodResolver } from '@hookform/resolvers/zod';
import { Building, Check, Upload, Calendar } from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';
import { useUpdateValuation } from '@/hooks/lending/useCollateral';
import { useToast } from '@/hooks/use-toast';
import { logger } from '@/lib/logger';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { UpdateValuationRequest } from '@/services/lending/collateralApi';

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

interface ValuationHistoryEntry {
  id: string;
  valuation_date: string;
  market_value: number;
  acceptable_value: number;
  margin: number;
  net_value: number;
  agency: string;
  report_number: string;
  valuer: string;
  created_by: string;
}

// Until the BE exposes a security-detail + valuation-history endpoint
// (tracked separately), these stay empty so the page renders without
// fabricated data. The valuation submission below is fully wired.
const collateralDetails = {
  id: '',
  security_code: '',
  loan_account: '',
  entity: '',
  category: '',
  type: '',
  description: '',
  current_value: 0,
  current_margin: 0,
  current_net_value: 0,
  last_valuation_date: '',
  property_address: '',
  property_area: '',
};
const valuationHistory: ValuationHistoryEntry[] = [];

export default function CollateralValuation() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { id } = useParams();
  const [showSuccess, setShowSuccess] = useState(false);
  const [calculatedNet, setCalculatedNet] = useState<number | null>(null);

  const updateMutation = useUpdateValuation();

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
    if (!id) {
      toast({
        title: 'Missing security id',
        description: 'No collateral id was provided in the URL.',
        variant: 'destructive',
      });
      return;
    }

    const payload: UpdateValuationRequest = {
      securityId: id,
      marketValue: data.market_value,
      acceptableValue: data.acceptable_value || undefined,
      valuationDate: data.valuation_date,
      valuerName: data.valuer_name || undefined,
      valuerFirm: data.valuation_agency || undefined,
      reportPath: data.valuation_report_number || undefined,
      nextValuationDate: data.next_valuation_date || undefined,
    };

    try {
      await updateMutation.mutateAsync(payload);
      toast({
        title: 'Valuation updated',
        description: 'New valuation recorded successfully.',
      });
      setShowSuccess(true);
    } catch (error) {
      logger.error('Failed to update valuation', error);
      const message =
        (error as { response?: { data?: { message?: string; detail?: string } } }).response?.data
          ?.message ||
        (error as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
        'Failed to update valuation. Please try again.';
      toast({ title: 'Save failed', description: message, variant: 'destructive' });
    }
  };

  const isSubmitting = updateMutation.isPending;

  if (showSuccess) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
            <Check className="h-8 w-8 text-green-600" />
          </div>
          <h2 className="mb-2 text-2xl font-bold">Valuation Updated Successfully</h2>
          <p className="mb-6 text-muted-foreground">
            New valuation recorded for {collateralDetails.security_code || 'this collateral'}
          </p>
          <div className="flex justify-center gap-4">
            <Button variant="outline" onClick={() => navigate('/admin/lending/collaterals')}>
              View All Collaterals
            </Button>
            <Button variant="outline" onClick={() => navigate(`/admin/lending/collaterals/${id}`)}>
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
          { label: 'Collaterals', to: '/admin/lending/collaterals' },
          { label: collateralDetails.security_code || 'Collateral' },
          { label: 'Revalue' },
        ]}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
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
                  <h3 className="mb-4 font-medium">Valuation Agency Details</h3>
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
                  <Button type="button" variant="outline" className="mb-4" disabled>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload Valuation Report
                  </Button>
                </div>

                <div className="flex justify-end gap-4">
                  <Button type="button" variant="outline" onClick={() => navigate(-1)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={isSubmitting}>
                    <Building className="mr-2 h-4 w-4" />
                    {isSubmitting ? 'Saving...' : 'Update Valuation'}
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
                <p className="text-sm text-muted-foreground">Security ID</p>
                <p className="font-mono text-xs">{id ?? '—'}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Last Valuation</p>
                <p className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  {collateralDetails.last_valuation_date
                    ? formatDate(collateralDetails.last_valuation_date)
                    : '—'}
                </p>
              </div>
            </CardContent>
          </Card>

          {calculatedNet !== null && (
            <Card className="border-green-200 bg-green-50">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">New Net Value</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold text-green-600">{formatCurrency(calculatedNet)}</p>
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
          {valuationHistory.length === 0 ? (
            <p className="py-4 text-sm text-muted-foreground">
              No previous valuations recorded for this collateral.
            </p>
          ) : (
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
          )}
        </CardContent>
      </Card>
    </div>
  );
}
