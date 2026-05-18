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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  useCreateTDSSection,
  useTDSSection,
  useUpdateTDSSection,
  type TDSSectionInput,
} from '@/hooks/tax/useTaxation';
import {
  tdsSectionSchema,
  type TDSSectionFormInput,
  type TDSSectionFormValues,
} from '@/schemas/tax/taxSchemas';

const defaultValues: TDSSectionFormValues = {
  sectionCode: '',
  sectionName: '',
  description: '',
  rateIndividual: 0,
  rateCompany: 0,
  rateNoPan: 20,
  rateLowerDeduction: undefined,
  thresholdSingle: 0,
  thresholdAnnual: 0,
  isTcs: false,
  surchargeApplicable: false,
  cessRate: 0,
  effectiveFrom: new Date().toISOString().slice(0, 10),
  effectiveTo: '',
  returnForm: undefined,
  natureOfPaymentCode: '',
  isActive: true,
};

export function TDSSectionForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = Boolean(id);
  const sectionQuery = useTDSSection(id);
  const createSection = useCreateTDSSection();
  const updateSection = useUpdateTDSSection(id ?? '');

  const form = useForm<TDSSectionFormValues, unknown, TDSSectionFormInput>({
    resolver: zodResolver(tdsSectionSchema),
    defaultValues,
  });

  useEffect(() => {
    if (!sectionQuery.data) return;
    form.reset({
      sectionCode: sectionQuery.data.sectionCode,
      sectionName: sectionQuery.data.sectionName,
      description: sectionQuery.data.description ?? '',
      rateIndividual: sectionQuery.data.rateIndividual,
      rateCompany: sectionQuery.data.rateCompany,
      rateNoPan: sectionQuery.data.rateNoPan,
      rateLowerDeduction: sectionQuery.data.rateLowerDeduction,
      thresholdSingle: sectionQuery.data.thresholdSingle,
      thresholdAnnual: sectionQuery.data.thresholdAnnual,
      isTcs: sectionQuery.data.isTcs,
      surchargeApplicable: sectionQuery.data.surchargeApplicable,
      cessRate: sectionQuery.data.cessRate,
      effectiveFrom: sectionQuery.data.effectiveFrom,
      effectiveTo: sectionQuery.data.effectiveTo ?? '',
      returnForm: sectionQuery.data.returnForm as TDSSectionFormInput['returnForm'],
      natureOfPaymentCode: sectionQuery.data.natureOfPaymentCode ?? '',
      isActive: sectionQuery.data.isActive,
    });
  }, [form, sectionQuery.data]);

  const mutation = isEdit ? updateSection : createSection;

  async function onSubmit(values: TDSSectionFormInput) {
    const payload: TDSSectionInput = {
      ...values,
      effectiveTo: values.effectiveTo || undefined,
      natureOfPaymentCode: values.natureOfPaymentCode || undefined,
    };
    await mutation.mutateAsync(payload);
    navigate('/admin/tds/sections');
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEdit ? 'Edit TDS/TCS Section' : 'Add TDS/TCS Section'}
        subtitle="Maintain deduction and collection rates by effective date"
        breadcrumbs={[{ label: 'TDS/TCS Sections', to: '/admin/tds/sections' }]}
      />

      {mutation.error && <ErrorState error={mutation.error} />}

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <FormShell
            footer={
              <>
                <Button type="button" variant="outline" onClick={() => navigate('/admin/tds/sections')}>
                  Cancel
                </Button>
                <Button type="submit" disabled={mutation.isPending}>
                  {mutation.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="mr-2 h-4 w-4" />
                  )}
                  Save Section
                </Button>
              </>
            }
          >
            <FormSection title="Section Identity">
              <FormField
                control={form.control}
                name="sectionCode"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Section code</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="194A" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="sectionName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Section name</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="Interest other than securities" />
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
                      <Input {...field} placeholder="Optional note" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormSection>

            <FormSection title="Rates And Thresholds">
              {(['rateIndividual', 'rateCompany', 'rateNoPan', 'rateLowerDeduction', 'cessRate'] as const).map(
                (name) => (
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
                ),
              )}
              {(['thresholdSingle', 'thresholdAnnual'] as const).map((name) => (
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
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              ))}
            </FormSection>

            <FormSection title="Return Mapping">
              <FormField
                control={form.control}
                name="returnForm"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Return form</FormLabel>
                    <Select value={field.value ?? ''} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select return form" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="24Q">24Q Salary</SelectItem>
                        <SelectItem value="26Q">26Q Non-salary</SelectItem>
                        <SelectItem value="27Q">27Q NRI</SelectItem>
                        <SelectItem value="27EQ">27EQ TCS</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="natureOfPaymentCode"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Nature of payment code</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="Optional" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormSection>

            <FormSection title="Validity And Flags">
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
              {(['isTcs', 'surchargeApplicable', 'isActive'] as const).map((name) => (
                <FormField
                  key={name}
                  control={form.control}
                  name={name}
                  render={({ field }) => (
                    <FormItem className="flex items-center gap-2 space-y-0">
                      <FormControl>
                        <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                      </FormControl>
                      <FormLabel>{name.replace(/([A-Z])/g, ' $1')}</FormLabel>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              ))}
            </FormSection>
          </FormShell>
        </form>
      </Form>
    </div>
  );
}
