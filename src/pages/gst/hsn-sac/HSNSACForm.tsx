import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, Pencil, Save } from 'lucide-react';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useLocation, useNavigate, useParams } from 'react-router-dom';

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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  useCreateHSNSAC,
  useGSTRates,
  useHSNSACItem,
  useUpdateHSNSAC,
  type HSNSACInput,
} from '@/hooks/tax/useTaxation';
import { hsnSacSchema, type HSNSACFormInput, type HSNSACFormValues } from '@/schemas/tax/taxSchemas';

const defaultValues: HSNSACFormValues = {
  code: '',
  description: '',
  hsnSacType: 'HSN',
  chapter: '',
  section: '',
  gstRateId: '',
  unitOfMeasurement: '',
  isActive: true,
};
const NO_GST_RATE_VALUE = '__no-gst-rate__';

export function HSNSACForm() {
  const navigate = useNavigate();
  const location = useLocation();
  const { id } = useParams();
  const isEdit = Boolean(id) && location.pathname.endsWith('/edit');
  const isDetail = Boolean(id) && !isEdit;
  const hsnSacQuery = useHSNSACItem(id);
  const gstRatesQuery = useGSTRates({ pageSize: 100, includeInactive: false });
  const createHsnSac = useCreateHSNSAC();
  const updateHsnSac = useUpdateHSNSAC(id ?? '');

  const form = useForm<HSNSACFormValues, unknown, HSNSACFormInput>({
    resolver: zodResolver(hsnSacSchema),
    defaultValues,
  });

  useEffect(() => {
    if (!hsnSacQuery.data) return;
    form.reset({
      code: hsnSacQuery.data.code,
      description: hsnSacQuery.data.description,
      hsnSacType: hsnSacQuery.data.hsnSacType as 'HSN' | 'SAC',
      chapter: hsnSacQuery.data.chapter ?? '',
      section: hsnSacQuery.data.section ?? '',
      gstRateId: hsnSacQuery.data.gstRateId ?? '',
      unitOfMeasurement: hsnSacQuery.data.unitOfMeasurement ?? '',
      isActive: hsnSacQuery.data.isActive,
    });
  }, [form, hsnSacQuery.data]);

  const mutation = isEdit ? updateHsnSac : createHsnSac;

  async function onSubmit(values: HSNSACFormInput) {
    const payload: HSNSACInput = {
      ...values,
      chapter: values.chapter || undefined,
      section: values.section || undefined,
      gstRateId: values.gstRateId || undefined,
      unitOfMeasurement: values.unitOfMeasurement || undefined,
    };
    await mutation.mutateAsync(payload);
    navigate('/admin/gst/hsn-sac');
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isDetail ? 'HSN / SAC Details' : isEdit ? 'Edit HSN / SAC' : 'Add HSN / SAC'}
        subtitle="Maintain GST classification codes and default rate mappings"
        breadcrumbs={[{ label: 'HSN / SAC', to: '/admin/gst/hsn-sac' }]}
        actions={isDetail ? <Button onClick={() => navigate(`/admin/gst/hsn-sac/${id}/edit`)}><Pencil className="mr-2 h-4 w-4" />Edit Code</Button> : undefined}
      />

      {mutation.error && <ErrorState error={mutation.error} />}
      {hsnSacQuery.error && <ErrorState error={hsnSacQuery.error} onRetry={() => hsnSacQuery.refetch()} />}

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <FormShell
            footer={
              isDetail ? (
                <Button type="button" variant="outline" onClick={() => navigate('/admin/gst/hsn-sac')}>Back</Button>
              ) : (
                <>
                  <Button type="button" variant="outline" onClick={() => navigate('/admin/gst/hsn-sac')}>Cancel</Button>
                  <Button type="submit" disabled={mutation.isPending}>
                    {mutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                    Save Code
                  </Button>
                </>
              )
            }
          >
            <FormSection title="Classification">
              <FormField control={form.control} name="code" render={({ field }) => (
                <FormItem>
                  <FormLabel>Code</FormLabel>
                  <FormControl><Input {...field} disabled={isDetail} placeholder="997113" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="hsnSacType" render={({ field }) => (
                <FormItem>
                  <FormLabel>Type</FormLabel>
                  <Select disabled={isDetail} value={field.value} onValueChange={field.onChange}>
                    <FormControl><SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger></FormControl>
                    <SelectContent>
                      <SelectItem value="HSN">HSN</SelectItem>
                      <SelectItem value="SAC">SAC</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="description" render={({ field }) => (
                <FormItem className="md:col-span-2">
                  <FormLabel>Description</FormLabel>
                  <FormControl><Input {...field} disabled={isDetail} placeholder="Tax classification description" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
            </FormSection>

            <FormSection title="Rate Mapping">
              <FormField control={form.control} name="chapter" render={({ field }) => (
                <FormItem>
                  <FormLabel>Chapter</FormLabel>
                  <FormControl><Input {...field} disabled={isDetail} placeholder="Optional" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="section" render={({ field }) => (
                <FormItem>
                  <FormLabel>Section</FormLabel>
                  <FormControl><Input {...field} disabled={isDetail} placeholder="Optional" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="gstRateId" render={({ field }) => (
                <FormItem>
                  <FormLabel>GST rate</FormLabel>
                  <Select
                    disabled={isDetail}
                    value={field.value || NO_GST_RATE_VALUE}
                    onValueChange={(value) => field.onChange(value === NO_GST_RATE_VALUE ? '' : value)}
                  >
                    <FormControl><SelectTrigger><SelectValue placeholder="Optional rate mapping" /></SelectTrigger></FormControl>
                    <SelectContent>
                      <SelectItem value={NO_GST_RATE_VALUE}>No default rate</SelectItem>
                      {(gstRatesQuery.data?.items ?? []).map((rate) => (
                        <SelectItem key={rate.id} value={rate.id}>{rate.code} · {rate.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="unitOfMeasurement" render={({ field }) => (
                <FormItem>
                  <FormLabel>Unit of measurement</FormLabel>
                  <FormControl><Input {...field} disabled={isDetail} placeholder="NOS / PCS / KGS" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="isActive" render={({ field }) => (
                <FormItem className="flex items-center gap-2 space-y-0">
                  <FormControl><Checkbox disabled={isDetail} checked={field.value} onCheckedChange={field.onChange} /></FormControl>
                  <FormLabel>Active</FormLabel>
                  <FormMessage />
                </FormItem>
              )} />
            </FormSection>
          </FormShell>
        </form>
      </Form>
    </div>
  );
}
