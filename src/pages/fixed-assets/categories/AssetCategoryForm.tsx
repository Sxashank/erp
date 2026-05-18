import { zodResolver } from '@hookform/resolvers/zod';
import { Save } from 'lucide-react';
import { useEffect, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';

import {
  AmountInput,
  FormSection,
  FormShell,
  PageHeader,
  PercentageInput,
} from '@/components/common';
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
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import { useAssetCategories, useAssetCategory, useCreateAssetCategory, useUpdateAssetCategory } from '@/hooks/fixed-assets/useAssetCategories';
import { useFixedAssetAccounts } from '@/hooks/fixed-assets/useMasters';
import { useToast } from '@/hooks/use-toast';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import { showErrorToast } from '@/lib/errorToast';
import {
  assetCategorySchema,
  type AssetCategoryInput,
} from '@/schemas/fixed-assets/assetCategorySchema';

const assetTypeOptions = [
  { value: 'TANGIBLE', label: 'Tangible' },
  { value: 'INTANGIBLE', label: 'Intangible' },
  { value: 'RIGHT_OF_USE', label: 'Right of use' },
] as const;

const depreciationMethodOptions = [
  { value: 'SLM', label: 'Straight line method' },
  { value: 'WDV', label: 'Written down value' },
  { value: 'UNIT_OF_PRODUCTION', label: 'Unit of production' },
  { value: 'NO_DEPRECIATION', label: 'No depreciation' },
] as const;

const defaultValues: AssetCategoryInput = {
  categoryCode: '',
  categoryName: '',
  description: '',
  parentCategoryId: '',
  assetType: 'TANGIBLE',
  depreciationMethod: 'SLM',
  usefulLifeYears: 5,
  residualValuePct: 5,
  depreciationRateSlm: 0,
  depreciationRateWdv: 0,
  itActBlock: '',
  capitalizationThreshold: 5000,
  glAssetAccountId: '',
  glAccumDepAccountId: '',
  glDepExpenseAccountId: '',
  glDisposalGainAccountId: '',
  glDisposalLossAccountId: '',
  glRevaluationReserveAccountId: '',
  glImpairmentAccountId: '',
  requiresInsurance: false,
  requiresAmc: false,
};

export function AssetCategoryForm(): JSX.Element {
  const organizationId = useRequiredActiveOrganizationId();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { toast } = useToast();
  const isEdit = Boolean(id);

  const categoryQuery = useAssetCategory(id);
  const categoriesQuery = useAssetCategories(organizationId);
  const accountsQuery = useFixedAssetAccounts(organizationId);
  const createMutation = useCreateAssetCategory();
  const updateMutation = useUpdateAssetCategory(id ?? '');

  const form = useForm<AssetCategoryInput>({
    resolver: zodResolver(assetCategorySchema),
    defaultValues,
  });

  useEffect(() => {
    if (!categoryQuery.data) return;
    form.reset({
      categoryCode: categoryQuery.data.categoryCode,
      categoryName: categoryQuery.data.categoryName,
      description: categoryQuery.data.description ?? '',
      parentCategoryId: categoryQuery.data.parentCategoryId ?? '',
      assetType: categoryQuery.data.assetType,
      depreciationMethod: categoryQuery.data.depreciationMethod,
      usefulLifeYears: categoryQuery.data.usefulLifeYears,
      residualValuePct: Number(categoryQuery.data.residualValuePct),
      depreciationRateSlm: Number(categoryQuery.data.depreciationRateSlm),
      depreciationRateWdv: Number(categoryQuery.data.depreciationRateWdv),
      itActRate: categoryQuery.data.itActRate ? Number(categoryQuery.data.itActRate) : undefined,
      itActBlock: categoryQuery.data.itActBlock ?? '',
      capitalizationThreshold: Number(categoryQuery.data.capitalizationThreshold),
      glAssetAccountId: categoryQuery.data.glAssetAccountId ?? '',
      glAccumDepAccountId: categoryQuery.data.glAccumDepAccountId ?? '',
      glDepExpenseAccountId: categoryQuery.data.glDepExpenseAccountId ?? '',
      glDisposalGainAccountId: categoryQuery.data.glDisposalGainAccountId ?? '',
      glDisposalLossAccountId: categoryQuery.data.glDisposalLossAccountId ?? '',
      glRevaluationReserveAccountId: categoryQuery.data.glRevaluationReserveAccountId ?? '',
      glImpairmentAccountId: categoryQuery.data.glImpairmentAccountId ?? '',
      requiresInsurance: categoryQuery.data.requiresInsurance,
      requiresAmc: categoryQuery.data.requiresAmc,
    });
  }, [categoryQuery.data, form]);

  const parentCategoryOptions = useMemo(
    () =>
      (categoriesQuery.data?.items ?? []).filter((category) => category.id !== id),
    [categoriesQuery.data?.items, id],
  );

  async function onSubmit(values: AssetCategoryInput) {
    const payload = {
      organizationId,
      categoryCode: values.categoryCode,
      categoryName: values.categoryName,
      description: values.description || null,
      parentCategoryId: values.parentCategoryId || null,
      assetType: values.assetType,
      depreciationMethod: values.depreciationMethod,
      usefulLifeYears: values.usefulLifeYears,
      residualValuePct: values.residualValuePct,
      depreciationRateSlm: values.depreciationRateSlm,
      depreciationRateWdv: values.depreciationRateWdv,
      itActRate: values.itActRate ?? null,
      itActBlock: values.itActBlock || null,
      capitalizationThreshold: values.capitalizationThreshold,
      glAssetAccountId: values.glAssetAccountId || null,
      glAccumDepAccountId: values.glAccumDepAccountId || null,
      glDepExpenseAccountId: values.glDepExpenseAccountId || null,
      glDisposalGainAccountId: values.glDisposalGainAccountId || null,
      glDisposalLossAccountId: values.glDisposalLossAccountId || null,
      glRevaluationReserveAccountId: values.glRevaluationReserveAccountId || null,
      glImpairmentAccountId: values.glImpairmentAccountId || null,
      requiresInsurance: values.requiresInsurance,
      requiresAmc: values.requiresAmc,
    };

    try {
      if (isEdit) {
        await updateMutation.mutateAsync(payload);
        toast({ title: 'Asset category updated' });
      } else {
        await createMutation.mutateAsync(payload);
        toast({ title: 'Asset category created' });
      }
      navigate('/admin/fixed-assets/categories');
    } catch (error) {
      showErrorToast(error, toast);
    }
  }

  const isLoading = categoryQuery.isLoading || categoriesQuery.isLoading || accountsQuery.isLoading;

  if (isLoading && isEdit) {
    return <Skeleton className="h-[520px] w-full" />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEdit ? 'Edit Asset Category' : 'New Asset Category'}
        subtitle="Set depreciation defaults, capitalization threshold, and GL mapping for this category."
        breadcrumbs={[
          { label: 'Fixed Assets' },
          { label: 'Asset Categories', to: '/admin/fixed-assets/categories' },
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
                  onClick={() => navigate('/admin/fixed-assets/categories')}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={form.formState.isSubmitting}
                >
                  <Save className="mr-2 h-4 w-4" />
                  {form.formState.isSubmitting ? 'Saving…' : 'Save category'}
                </Button>
              </>
            }
          >
            <FormSection
              title="Basic Information"
              description="Define how this asset category appears in the register."
            >
              <FormField
                control={form.control}
                name="categoryCode"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Category code</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="categoryName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Category name</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="parentCategoryId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Parent category</FormLabel>
                    <Select value={field.value || 'ROOT'} onValueChange={(value) => field.onChange(value === 'ROOT' ? '' : value)}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Root category" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="ROOT">Root category</SelectItem>
                        {parentCategoryOptions.map((category) => (
                          <SelectItem key={category.id} value={category.id}>
                            {category.categoryCode} · {category.categoryName}
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
                name="assetType"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Asset type</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {assetTypeOptions.map((option) => (
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
              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem className="md:col-span-2">
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Textarea {...field} rows={3} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormSection>

            <FormSection
              title="Depreciation Policy"
              description="These defaults apply when assets are created in this category."
            >
              <FormField
                control={form.control}
                name="depreciationMethod"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Method</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {depreciationMethodOptions.map((option) => (
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
              <FormField
                control={form.control}
                name="usefulLifeYears"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Useful life (years)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={1}
                        max={100}
                        value={field.value ?? ''}
                        onChange={(event) => {
                          const nextValue = event.target.value;
                          field.onChange(nextValue === '' ? undefined : Number(nextValue));
                        }}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="residualValuePct"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Residual value</FormLabel>
                    <FormControl>
                      <PercentageInput value={field.value} onChange={field.onChange} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="depreciationRateSlm"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>SLM rate</FormLabel>
                    <FormControl>
                      <PercentageInput value={field.value} onChange={field.onChange} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="depreciationRateWdv"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>WDV rate</FormLabel>
                    <FormControl>
                      <PercentageInput value={field.value} onChange={field.onChange} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="capitalizationThreshold"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Capitalization threshold</FormLabel>
                    <FormControl>
                      <AmountInput value={field.value} onChange={field.onChange} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormSection>

            <FormSection
              title="GL Mapping"
              description="Pick the ledger accounts that receive capitalization, depreciation, disposal, and impairment postings."
            >
              {[
                ['glAssetAccountId', 'Asset account'],
                ['glAccumDepAccountId', 'Accumulated depreciation'],
                ['glDepExpenseAccountId', 'Depreciation expense'],
                ['glDisposalGainAccountId', 'Disposal gain'],
                ['glDisposalLossAccountId', 'Disposal loss'],
                ['glRevaluationReserveAccountId', 'Revaluation reserve'],
                ['glImpairmentAccountId', 'Impairment expense'],
              ].map(([name, label]) => (
                <FormField
                  key={name}
                  control={form.control}
                  name={name as keyof AssetCategoryInput}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{label}</FormLabel>
                      <Select
                        value={(field.value as string) || 'NONE'}
                        onValueChange={(value) => field.onChange(value === 'NONE' ? '' : value)}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Not mapped" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="NONE">Not mapped</SelectItem>
                          {(accountsQuery.data ?? []).map((account) => (
                            <SelectItem key={account.id} value={account.id}>
                              {account.code ? `${account.code} · ` : ''}
                              {account.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              ))}
            </FormSection>

            <FormSection
              title="Operational Flags"
              description="Enable mandatory supporting cover if this category requires insurance or AMC."
            >
              <FormField
                control={form.control}
                name="requiresInsurance"
                render={({ field }) => (
                  <FormItem className="flex items-center gap-3 space-y-0 rounded-lg border p-4">
                    <FormControl>
                      <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
                    <div>
                      <FormLabel>Requires insurance</FormLabel>
                    </div>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="requiresAmc"
                render={({ field }) => (
                  <FormItem className="flex items-center gap-3 space-y-0 rounded-lg border p-4">
                    <FormControl>
                      <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
                    <div>
                      <FormLabel>Requires AMC</FormLabel>
                    </div>
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
