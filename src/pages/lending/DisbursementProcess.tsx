import { zodResolver } from '@hookform/resolvers/zod';
import { Banknote, CheckCircle } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';
import { z } from 'zod';

import { PageHeader } from '@/components/common/PageHeader';
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
import { Textarea } from '@/components/ui/textarea';
import { useProcessDisbursement } from '@/hooks/lending/useDisbursements';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';

const processDisbursementSchema = z.object({
  disbursedAmount: z.string().min(1, 'Disbursed amount is required'),
  disbursementDate: z.string().optional(),
  valueDate: z.string().optional(),
  utrNumber: z.string().optional(),
  chequeNumber: z.string().optional(),
  disbursementCharges: z.string().optional(),
  remarks: z.string().optional(),
});

type ProcessDisbursementFormInput = z.input<typeof processDisbursementSchema>;
type ProcessDisbursementFormData = z.output<typeof processDisbursementSchema>;

export default function DisbursementProcess() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const processMutation = useProcessDisbursement();
  const form = useForm<ProcessDisbursementFormInput, unknown, ProcessDisbursementFormData>({
    resolver: zodResolver(processDisbursementSchema),
    defaultValues: {
      disbursementDate: new Date().toISOString().split('T')[0],
      valueDate: new Date().toISOString().split('T')[0],
      disbursementCharges: '0',
    },
  });

  const onSubmit = async (data: ProcessDisbursementFormData) => {
    if (!id) return;
    try {
      await processMutation.mutateAsync({
        disbursementId: id,
        disbursedAmount: data.disbursedAmount,
        disbursementDate: data.disbursementDate || undefined,
        valueDate: data.valueDate || undefined,
        utrNumber: data.utrNumber || undefined,
        chequeNumber: data.chequeNumber || undefined,
        disbursementCharges: data.disbursementCharges || '0',
      });
      toast({
        title: 'Disbursement processed',
        description: 'The disbursement has been recorded and posted to accounting.',
      });
      navigate('/admin/lending/disbursements');
    } catch (err) {
      showErrorToast(err, toast);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Process Disbursement"
        subtitle="Record manual fund release after approval"
        breadcrumbs={[
          { label: 'Disbursements', to: '/admin/lending/disbursements' },
          { label: 'Process' },
        ]}
      />

      <Card className="max-w-3xl">
        <CardHeader>
          <CardTitle>Fund Release Details</CardTitle>
          <CardDescription>
            Uses the organisation primary bank ledger by default unless a source ledger is supplied
            by backend configuration.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="disbursedAmount"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Disbursed Amount *</FormLabel>
                    <FormControl>
                      <Input type="number" placeholder="Enter amount released" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="grid gap-4 md:grid-cols-2">
                <FormField
                  control={form.control}
                  name="disbursementDate"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Disbursement Date</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="valueDate"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Value Date</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormDescription>Defaults to the disbursement date</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <FormField
                  control={form.control}
                  name="utrNumber"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>UTR Number</FormLabel>
                      <FormControl>
                        <Input placeholder="Enter NEFT/RTGS/IMPS reference" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="chequeNumber"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Cheque Number</FormLabel>
                      <FormControl>
                        <Input placeholder="Enter cheque reference if applicable" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="disbursementCharges"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Disbursement Charges</FormLabel>
                    <FormControl>
                      <Input type="number" placeholder="0" {...field} />
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
                    <FormLabel>Remarks</FormLabel>
                    <FormControl>
                      <Textarea placeholder="Internal notes" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="flex justify-end gap-4">
                <Button type="button" variant="outline" onClick={() => navigate(-1)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={processMutation.isPending || !id}>
                  {processMutation.isPending ? (
                    <Banknote className="mr-2 h-4 w-4 animate-pulse" />
                  ) : (
                    <CheckCircle className="mr-2 h-4 w-4" />
                  )}
                  {processMutation.isPending ? 'Processing...' : 'Process Disbursement'}
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}
