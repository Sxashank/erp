import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, Save } from 'lucide-react';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { FormSection, FormShell } from '@/components/common/FormShell';
import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import {
  useCreateGSTRate,
  useGSTRate,
  useUpdateGSTRate,
  type GSTRateInput,
} from '@/hooks/tax/useTaxation';
import {
  gstRateSchema,
  type GSTRateFormInput,
  type GSTRateFormValues,
} from '@/schemas/tax/taxSchemas';

const defaultValues: GSTRateFormValues = {
  code: '',
  name: '',
  rate: 0,
  cgstRate: 0,
  sgstRate: 0,
  igstRate: 0,
  cessRate: 0,
  description: '',
  effectiveFrom: new Date().toISOString().slice(0, 10),
  effectiveTo: '',
  isActive: true,
};

export function GSTRateForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = Boolean(id);
  const rateQuery = useGSTRate(id);
  const createRate = useCreateGSTRate();
  const updateRate = useUpdateGSTRate(id ?? '');

  const form = useForm<GSTRateFormValues, unknown, GSTRateFormInput>({
    resolver: zodResolver(gstRateSchema),
    defaultValues,
  });

  useEffect(() => {
    if (!rateQuery.data) return;
    form.reset({
      code: rateQuery.data.code,
      name: rateQuery.data.name,
      rate: rateQuery.data.rate,
      cgstRate: rateQuery.data.cgstRate,
      sgstRate: rateQuery.data.sgstRate,
      igstRate: rateQuery.data.igstRate,
      cessRate: rateQuery.data.cessRate,
      description: rateQuery.data.description ?? '',
      effectiveFrom: rateQuery.data.effectiveFrom,
      effectiveTo: rateQuery.data.effectiveTo ?? '',
      isActive: rateQuery.data.isActive,
    });
  }, [form, rateQuery.data]);

  const mutation = isEdit ? updateRate : createRate;

  async function onSubmit(values: GSTRateFormInput) {
    const payload: GSTRateInput = { ...values, effectiveTo: values.effectiveTo || undefined };
    await mutation.mutateAsync(payload);
    navigate('/admin/gst/rates');
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEdit ? 'Edit GST Rate' : 'Add GST Rate'}
        subtitle="Define statutory GST rate splits with effective dates"
        breadcrumbs={[{ label: 'GST Rates', to: '/admin/gst/rates' }]}
      />

      {mutation.error && <ErrorState error={mutation.error} />}

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <FormShell
            footer={
              <>
                <Button type="button" variant="outline" onClick={() => navigate('/admin/gst/rates')}>
                  Cancel
                </Button>
                <Button type="submit" disabled={mutation.isPending}>
                  {mutation.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="mr-2 h-4 w-4" />
                  )}
                  Save Rate
                </Button>
              </>
            }
          >
            <FormSection title="Rate Identity">
              <FormField
                control={form.control}
                name="code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Code</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="GST18" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Name</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="GST 18%" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem className="md:col-span-2">
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="Optional statutory note" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormSection>

            <FormSection title="Rate Split">
              {(['rate', 'cgstRate', 'sgstRate', 'igstRate', 'cessRate'] as const).map((name) => (
                <FormField
                  key={name}
                  control={form.control}
                  name={name}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{name.replace(/([A-Z])/g, ' $1')}</FormLabel>
                      <FormControl>
                        <Input
                          {...field}
                          value={(field.value as string | number | undefined) ?? ''}
                          type="number"
                          step="0.01"
                          min="0"
                          max="100"
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              ))}
            </FormSection>

            <FormSection title="Validity">
              <FormField
                control={form.control}
                name="effectiveFrom"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Effective from</FormLabel>
                    <FormControl>
                      <Input {...field} type="date" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="effectiveTo"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Effective to</FormLabel>
                    <FormControl>
                      <Input {...field} type="date" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="isActive"
                render={({ field }) => (
                  <FormItem className="flex items-center gap-2 space-y-0">
                    <FormControl>
                      <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
                    <FormLabel>Active</FormLabel>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormSection>
          </FormShell>
        </form>
      </Form>
    </div>
  );
}
