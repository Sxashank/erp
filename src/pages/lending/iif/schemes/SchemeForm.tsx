/**
 * IIF Subvention Scheme create/edit form.
 *
 * react-hook-form + zod via shadcn <Form>/<FormField>. See CLAUDE.md §5.3.
 */

import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, Save } from 'lucide-react';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';
import { z } from 'zod';

import { ErrorState } from '@/components/common/ErrorState';
import { FormSection, FormShell } from '@/components/common/FormShell';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
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
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import {
  useCreateSubventionScheme,
  useSubventionScheme,
  useUpdateSubventionScheme,
  useUtilizationCategories,
} from '@/hooks/lending/useIif';
import { useLendingOptionRows } from '@/hooks/lending/useLendingMasters';
import { useToast } from '@/hooks/use-toast';

const schemeSchema = z.object({
  schemeCode: z.string().trim().min(1, 'Code is required').max(64),
  schemeName: z.string().trim().min(1, 'Name is required').max(256),
  administeringMinistry: z.string().trim().optional(),
  implementingAgency: z.string().trim().optional(),
  subventionRatePercent: z.coerce.number().min(0).max(100),
  maxSubventionPerBeneficiary: z.union([z.coerce.number().nonnegative(), z.literal('')]).optional(),
  schemeCorpus: z.union([z.coerce.number().nonnegative(), z.literal('')]).optional(),
  eligibleLoanTypes: z.array(z.string().min(1)).min(1, 'Select at least one eligible loan type'),
  maxTenureTermLoanMonths: z.union([z.coerce.number().int().positive(), z.literal('')]).optional(),
  maxTenureWorkingCapitalMonths: z
    .union([z.coerce.number().int().positive(), z.literal('')])
    .optional(),
  schemeStartDate: z.string().min(1, 'Start date is required'),
  schemeEndDate: z.string().min(1, 'End date is required'),
  eligibilityWindowMonths: z.union([z.coerce.number().int().positive(), z.literal('')]).optional(),
  claimFrequency: z.string().min(1, 'Claim frequency is required'),
  npaDisqualificationDpdDays: z.coerce.number().int().nonnegative(),
  description: z.string().trim().optional(),
  isActive: z.boolean(),
});

type SchemeFormInput = z.input<typeof schemeSchema>;
type SchemeFormValues = z.output<typeof schemeSchema>;

function toOptionalNumberString(value: number | '' | undefined): string | null {
  if (value === undefined || value === '') return null;
  return String(value);
}

/**
 * `z.coerce.number()` widens `field.value` to `unknown`. The underlying
 * `<Input>` only accepts `string | number | readonly string[] | undefined`,
 * so funnel through this helper to widen back without losing RHF wiring.
 */
function fieldInputValue(value: unknown): string | number {
  if (value === null || value === undefined) return '';
  if (typeof value === 'number' || typeof value === 'string') return value;
  return String(value);
}

function toOptionRows(rows: { data: Record<string, unknown> }[] | undefined) {
  return (
    rows?.map((row) => ({
      value: String(row.data.code ?? ''),
      label: String(row.data.label ?? row.data.name ?? row.data.code ?? ''),
    })) ?? []
  );
}

export default function SchemeForm(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const isEdit = Boolean(id);

  const schemeQuery = useSubventionScheme(id);
  const { data: categoriesData } = useUtilizationCategories(
    isEdit && id ? { schemeId: id } : undefined,
  );
  const eligibleLoanTypesQuery = useLendingOptionRows('IIF_ELIGIBLE_LOAN_TYPE');
  const claimFrequenciesQuery = useLendingOptionRows('IIF_CLAIM_FREQUENCY');
  const eligibleLoanTypeOptions = toOptionRows(eligibleLoanTypesQuery.data?.items);
  const claimFrequencyOptions = toOptionRows(claimFrequenciesQuery.data?.items);
  const linkedCategories = categoriesData?.items ?? [];

  const form = useForm<SchemeFormInput, unknown, SchemeFormValues>({
    resolver: zodResolver(schemeSchema),
    defaultValues: {
      schemeCode: '',
      schemeName: '',
      administeringMinistry: '',
      implementingAgency: '',
      subventionRatePercent: 3,
      maxSubventionPerBeneficiary: 10000000000,
      schemeCorpus: 50000000000,
      eligibleLoanTypes: [],
      maxTenureTermLoanMonths: 180,
      maxTenureWorkingCapitalMonths: 60,
      schemeStartDate: '2025-09-24',
      schemeEndDate: '2036-03-31',
      eligibilityWindowMonths: 36,
      claimFrequency: '',
      npaDisqualificationDpdDays: 30,
      description: '',
      isActive: true,
    },
  });

  // Hydrate on load (edit mode)
  useEffect(() => {
    if (!schemeQuery.data) return;
    const s = schemeQuery.data;
    form.reset({
      schemeCode: s.schemeCode,
      schemeName: s.schemeName,
      administeringMinistry: s.administeringMinistry ?? '',
      implementingAgency: s.implementingAgency ?? '',
      subventionRatePercent: Number(s.subventionRatePercent),
      maxSubventionPerBeneficiary:
        s.maxSubventionPerBeneficiary !== null ? Number(s.maxSubventionPerBeneficiary) : '',
      schemeCorpus: s.schemeCorpus !== null ? Number(s.schemeCorpus) : '',
      eligibleLoanTypes: s.eligibleLoanTypes,
      maxTenureTermLoanMonths: s.maxTenureTermLoanMonths ?? '',
      maxTenureWorkingCapitalMonths: s.maxTenureWorkingCapitalMonths ?? '',
      schemeStartDate: s.schemeStartDate,
      schemeEndDate: s.schemeEndDate,
      eligibilityWindowMonths: s.eligibilityWindowMonths ?? '',
      claimFrequency: s.claimFrequency,
      npaDisqualificationDpdDays: s.npaDisqualificationDpdDays,
      description: s.description ?? '',
      isActive: s.isActive,
    });
  }, [schemeQuery.data, form]);

  useEffect(() => {
    if (isEdit) return;
    const currentTypes = form.getValues('eligibleLoanTypes') ?? [];
    if (currentTypes.length === 0 && eligibleLoanTypeOptions.length > 0) {
      form.setValue(
        'eligibleLoanTypes',
        eligibleLoanTypeOptions.slice(0, 2).map((option) => option.value),
        { shouldValidate: true },
      );
    }
    if (!form.getValues('claimFrequency') && claimFrequencyOptions[0]) {
      form.setValue('claimFrequency', claimFrequencyOptions[0].value, {
        shouldValidate: true,
      });
    }
  }, [claimFrequencyOptions, eligibleLoanTypeOptions, form, isEdit]);

  const createMut = useCreateSubventionScheme({
    onSuccess: () => {
      toast({ title: 'Scheme created' });
      navigate('/admin/lending/iif/schemes');
    },
  });
  const updateMut = useUpdateSubventionScheme({
    onSuccess: () => {
      toast({ title: 'Scheme updated' });
      navigate('/admin/lending/iif/schemes');
    },
  });

  const submitting = createMut.isPending || updateMut.isPending;

  function onSubmit(values: SchemeFormValues) {
    const payload = {
      schemeCode: values.schemeCode,
      schemeName: values.schemeName,
      administeringMinistry: values.administeringMinistry || null,
      implementingAgency: values.implementingAgency || null,
      subventionRatePercent: String(values.subventionRatePercent),
      maxSubventionPerBeneficiary: toOptionalNumberString(values.maxSubventionPerBeneficiary),
      schemeCorpus: toOptionalNumberString(values.schemeCorpus),
      eligibleLoanTypes: values.eligibleLoanTypes,
      maxTenureTermLoanMonths:
        values.maxTenureTermLoanMonths === '' || values.maxTenureTermLoanMonths === undefined
          ? null
          : Number(values.maxTenureTermLoanMonths),
      maxTenureWorkingCapitalMonths:
        values.maxTenureWorkingCapitalMonths === '' ||
        values.maxTenureWorkingCapitalMonths === undefined
          ? null
          : Number(values.maxTenureWorkingCapitalMonths),
      schemeStartDate: values.schemeStartDate,
      schemeEndDate: values.schemeEndDate,
      eligibilityWindowMonths:
        values.eligibilityWindowMonths === '' || values.eligibilityWindowMonths === undefined
          ? null
          : Number(values.eligibilityWindowMonths),
      claimFrequency: values.claimFrequency,
      npaDisqualificationDpdDays: values.npaDisqualificationDpdDays,
      description: values.description || null,
      isActive: values.isActive,
    };

    if (isEdit && id) {
      updateMut.mutate({ id, payload });
    } else {
      createMut.mutate(payload);
    }
  }

  if (isEdit && schemeQuery.isError) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Edit Scheme"
          breadcrumbs={[
            { label: 'Lending', to: '/admin/lending' },
            { label: 'Interest Subvention' },
            { label: 'Schemes', to: '/admin/lending/iif/schemes' },
            { label: 'Edit' },
          ]}
        />
        <ErrorState error={schemeQuery.error} onRetry={schemeQuery.refetch} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEdit ? 'Edit Scheme' : 'New Subvention Scheme'}
        subtitle={
          isEdit
            ? `Editing ${schemeQuery.data?.schemeCode ?? ''}`
            : 'Configure a new government interest-subvention programme.'
        }
        breadcrumbs={[
          { label: 'Lending', to: '/admin/lending' },
          { label: 'Interest Subvention' },
          { label: 'Schemes', to: '/admin/lending/iif/schemes' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <FormShell
            footer={
              <>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate('/admin/lending/iif/schemes')}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting}>
                  {submitting ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="mr-2 h-4 w-4" />
                  )}
                  {isEdit ? 'Update Scheme' : 'Create Scheme'}
                </Button>
              </>
            }
          >
            <FormSection title="Basics" description="Scheme code and naming.">
              <FormField
                control={form.control}
                name="schemeCode"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Scheme Code *</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g. IIF" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="schemeName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Scheme Name *</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g. Interest Incentivization Fund" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="administeringMinistry"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Administering Ministry</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="e.g. Ministry of Ports, Shipping and Waterways"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="implementingAgency"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Implementing Agency</FormLabel>
                    <FormControl>
                      <Input placeholder="Optional" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormSection>

            <FormSection title="Rate & Limits">
              <FormField
                control={form.control}
                name="subventionRatePercent"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Subvention Rate (% p.a.) *</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={0}
                        max={100}
                        step="0.01"
                        name={field.name}
                        ref={field.ref}
                        onBlur={field.onBlur}
                        onChange={field.onChange}
                        value={fieldInputValue(field.value)}
                      />
                    </FormControl>
                    <FormDescription>e.g. 3.00 for IIF.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="maxSubventionPerBeneficiary"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Max Subvention / Beneficiary (₹)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={0}
                        step="1"
                        name={field.name}
                        ref={field.ref}
                        onBlur={field.onBlur}
                        onChange={field.onChange}
                        value={fieldInputValue(field.value)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="schemeCorpus"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Scheme Corpus (₹)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={0}
                        step="1"
                        name={field.name}
                        ref={field.ref}
                        onBlur={field.onBlur}
                        onChange={field.onChange}
                        value={fieldInputValue(field.value)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="npaDisqualificationDpdDays"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>NPA Disqualification DPD (days) *</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={0}
                        name={field.name}
                        ref={field.ref}
                        onBlur={field.onBlur}
                        onChange={field.onChange}
                        value={fieldInputValue(field.value)}
                      />
                    </FormControl>
                    <FormDescription>
                      Loans crossing this DPD become ineligible for claims.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormSection>

            <FormSection title="Eligibility">
              <FormField
                control={form.control}
                name="eligibleLoanTypes"
                render={() => (
                  <FormItem className="md:col-span-2">
                    <FormLabel>Eligible Loan Types *</FormLabel>
                    <div className="flex flex-wrap gap-4">
                      {eligibleLoanTypeOptions.map((option) => (
                        <FormField
                          key={option.value}
                          control={form.control}
                          name="eligibleLoanTypes"
                          render={({ field }) => (
                            <FormItem className="flex items-center gap-2 space-y-0">
                              <FormControl>
                                <Checkbox
                                  checked={field.value?.includes(option.value)}
                                  onCheckedChange={(checked) => {
                                    if (checked) {
                                      field.onChange([...(field.value ?? []), option.value]);
                                    } else {
                                      field.onChange(
                                        (field.value ?? []).filter((v) => v !== option.value),
                                      );
                                    }
                                  }}
                                />
                              </FormControl>
                              <FormLabel className="font-normal">{option.label}</FormLabel>
                            </FormItem>
                          )}
                        />
                      ))}
                    </div>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="maxTenureTermLoanMonths"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Max Tenure — Term Loan (months)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={1}
                        name={field.name}
                        ref={field.ref}
                        onBlur={field.onBlur}
                        onChange={field.onChange}
                        value={fieldInputValue(field.value)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="maxTenureWorkingCapitalMonths"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Max Tenure — Working Capital (months)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={1}
                        name={field.name}
                        ref={field.ref}
                        onBlur={field.onBlur}
                        onChange={field.onChange}
                        value={fieldInputValue(field.value)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="eligibilityWindowMonths"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Eligibility Window (months)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={1}
                        name={field.name}
                        ref={field.ref}
                        onBlur={field.onBlur}
                        onChange={field.onChange}
                        value={fieldInputValue(field.value)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormSection>

            <FormSection title="Dates & Claim Cycle">
              <FormField
                control={form.control}
                name="schemeStartDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Scheme Start Date *</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="schemeEndDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Scheme End Date *</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="claimFrequency"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Claim Frequency *</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {claimFrequencyOptions.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormSection>

            <FormSection title="Description & Status">
              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem className="md:col-span-2">
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Textarea rows={3} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="isActive"
                render={({ field }) => (
                  <FormItem className="flex items-center justify-between rounded-md border p-3 md:col-span-2">
                    <div>
                      <FormLabel>Active</FormLabel>
                      <FormDescription>
                        Inactive schemes cannot accept new enrollments.
                      </FormDescription>
                    </div>
                    <FormControl>
                      <Switch checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
                  </FormItem>
                )}
              />
            </FormSection>

            {isEdit && linkedCategories.length > 0 && (
              <FormSection
                title="Linked Fund Utilization Categories"
                description="Categories that loan applicants must split the requested loan amount across."
              >
                <div className="flex flex-wrap gap-2 md:col-span-2">
                  {linkedCategories.map((c) => (
                    <Badge key={c.id} variant="secondary">
                      {c.label}
                    </Badge>
                  ))}
                </div>
              </FormSection>
            )}
          </FormShell>
        </form>
      </Form>
    </div>
  );
}
