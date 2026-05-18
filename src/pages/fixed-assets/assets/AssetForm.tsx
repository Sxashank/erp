import { zodResolver } from '@hookform/resolvers/zod';
import { Save } from 'lucide-react';
import { useEffect, useMemo } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';

import { AmountInput, FormSection, FormShell, PageHeader } from '@/components/common';
import { Button } from '@/components/ui/button';
import { DatePicker } from '@/components/ui/date-picker';
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
import { useAssetCategories } from '@/hooks/fixed-assets/useAssetCategories';
import { useCreateFixedAsset, useFixedAsset, useUpdateFixedAsset } from '@/hooks/fixed-assets/useFixedAssets';
import {
  useFixedAssetDepartments,
  useFixedAssetUnits,
  useFixedAssetVendors,
} from '@/hooks/fixed-assets/useMasters';
import { useToast } from '@/hooks/use-toast';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import { showErrorToast } from '@/lib/errorToast';
import {
  fixedAssetSchema,
  type FixedAssetInput,
} from '@/schemas/fixed-assets/assetSchema';

const acquisitionTypeOptions = [
  { value: 'PURCHASE', label: 'Purchase' },
  { value: 'LEASE', label: 'Lease' },
  { value: 'DONATION', label: 'Donation' },
  { value: 'TRANSFER_IN', label: 'Transfer in' },
  { value: 'CONSTRUCTED', label: 'Constructed' },
] as const;

const depreciationMethodOptions = [
  { value: 'SLM', label: 'Straight line method' },
  { value: 'WDV', label: 'Written down value' },
  { value: 'UNIT_OF_PRODUCTION', label: 'Unit of production' },
  { value: 'NO_DEPRECIATION', label: 'No depreciation' },
] as const;

const defaultValues: FixedAssetInput = {
  assetName: '',
  description: '',
  categoryId: '',
  locationId: '',
  departmentId: '',
  acquisitionDate: '',
  putToUseDate: '',
  acquisitionType: 'PURCHASE',
  vendorId: '',
  invoiceNumber: '',
  invoiceDate: '',
  poNumber: '',
  acquisitionCost: 0,
  installationCost: 0,
  otherCosts: 0,
  residualValue: 0,
  depreciationMethod: 'SLM',
  depreciationRate: 0,
  usefulLifeMonths: undefined,
  make: '',
  model: '',
  serialNumber: '',
  quantity: 1,
  warrantyStartDate: '',
  warrantyExpiryDate: '',
};

function toDate(value: string | undefined): Date | null {
  return value ? new Date(value) : null;
}

function toIsoDate(value: Date | undefined): string {
  return value ? value.toISOString().slice(0, 10) : '';
}

export function AssetForm(): JSX.Element {
  const organizationId = useRequiredActiveOrganizationId();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { toast } = useToast();
  const isEdit = Boolean(id);

  const assetQuery = useFixedAsset(id);
  const categoriesQuery = useAssetCategories(organizationId);
  const vendorsQuery = useFixedAssetVendors(organizationId);
  const unitsQuery = useFixedAssetUnits(organizationId);
  const departmentsQuery = useFixedAssetDepartments(organizationId);
  const createMutation = useCreateFixedAsset();
  const updateMutation = useUpdateFixedAsset(id ?? '');

  const form = useForm<FixedAssetInput>({
    resolver: zodResolver(fixedAssetSchema),
    defaultValues,
  });

  const selectedCategoryId = useWatch({ control: form.control, name: 'categoryId' });

  useEffect(() => {
    if (!assetQuery.data) return;
    form.reset({
      assetName: assetQuery.data.assetName,
      description: assetQuery.data.description ?? '',
      categoryId: assetQuery.data.categoryId,
      locationId: assetQuery.data.locationId ?? '',
      departmentId: assetQuery.data.departmentId ?? '',
      acquisitionDate: assetQuery.data.acquisitionDate,
      putToUseDate: assetQuery.data.putToUseDate ?? '',
      acquisitionType: assetQuery.data.acquisitionType,
      vendorId: assetQuery.data.vendorId ?? '',
      invoiceNumber: assetQuery.data.invoiceNumber ?? '',
      invoiceDate: assetQuery.data.invoiceDate ?? '',
      poNumber: assetQuery.data.poNumber ?? '',
      acquisitionCost: Number(assetQuery.data.acquisitionCost),
      installationCost: Number(assetQuery.data.installationCost),
      otherCosts: Number(assetQuery.data.otherCosts),
      residualValue: Number(assetQuery.data.residualValue),
      depreciationMethod: assetQuery.data.depreciationMethod,
      depreciationRate: Number(assetQuery.data.depreciationRate),
      usefulLifeMonths: assetQuery.data.usefulLifeMonths,
      make: assetQuery.data.make ?? '',
      model: assetQuery.data.model ?? '',
      serialNumber: assetQuery.data.serialNumber ?? '',
      quantity: assetQuery.data.quantity,
      warrantyStartDate: assetQuery.data.warrantyStartDate ?? '',
      warrantyExpiryDate: assetQuery.data.warrantyExpiryDate ?? '',
    });
  }, [assetQuery.data, form]);

  const categories = useMemo(
    () => categoriesQuery.data?.items ?? [],
    [categoriesQuery.data?.items],
  );

  useEffect(() => {
    if (!selectedCategoryId || isEdit) return;
    const category = categories.find((item) => item.id === selectedCategoryId);
    if (!category) return;
    form.setValue('depreciationMethod', category.depreciationMethod);
    form.setValue(
      'depreciationRate',
      Number(
        category.depreciationMethod === 'WDV'
          ? category.depreciationRateWdv
          : category.depreciationRateSlm,
      ),
    );
    form.setValue('usefulLifeMonths', category.usefulLifeYears * 12);
    form.setValue('residualValue', Number(category.capitalizationThreshold) === 0 ? 0 : form.getValues('residualValue'));
  }, [categories, form, isEdit, selectedCategoryId]);

  const relatedMasters = useMemo(
    () => ({
      categories,
      vendors: vendorsQuery.data ?? [],
      units: unitsQuery.data ?? [],
      departments: departmentsQuery.data ?? [],
    }),
    [categories, departmentsQuery.data, unitsQuery.data, vendorsQuery.data],
  );

  async function onSubmit(values: FixedAssetInput) {
    const payload = {
      organizationId,
      assetName: values.assetName,
      description: values.description || null,
      categoryId: values.categoryId,
      locationId: values.locationId || null,
      departmentId: values.departmentId || null,
      acquisitionDate: values.acquisitionDate,
      putToUseDate: values.putToUseDate || null,
      acquisitionType: values.acquisitionType,
      vendorId: values.vendorId || null,
      invoiceNumber: values.invoiceNumber || null,
      invoiceDate: values.invoiceDate || null,
      poNumber: values.poNumber || null,
      acquisitionCost: values.acquisitionCost,
      installationCost: values.installationCost ?? 0,
      otherCosts: values.otherCosts ?? 0,
      residualValue: values.residualValue ?? 0,
      usefulLifeMonths: values.usefulLifeMonths ?? null,
      depreciationMethod: values.depreciationMethod || null,
      depreciationRate: values.depreciationRate ?? null,
      make: values.make || null,
      model: values.model || null,
      serialNumber: values.serialNumber || null,
      quantity: values.quantity,
      warrantyStartDate: values.warrantyStartDate || null,
      warrantyExpiryDate: values.warrantyExpiryDate || null,
    };

    try {
      if (isEdit) {
        const asset = await updateMutation.mutateAsync(payload);
        toast({ title: 'Fixed asset updated' });
        navigate(`/admin/fixed-assets/assets/${asset.id}`);
        return;
      }

      const asset = await createMutation.mutateAsync(payload);
      toast({ title: 'Fixed asset created as draft' });
      navigate(`/admin/fixed-assets/assets/${asset.id}`);
    } catch (error) {
      showErrorToast(error, toast);
    }
  }

  if (assetQuery.isLoading && isEdit) {
    return <Skeleton className="h-[640px] w-full" />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEdit ? 'Edit Fixed Asset' : 'New Fixed Asset'}
        subtitle="Capture the draft asset record before capitalization."
        breadcrumbs={[
          { label: 'Fixed Assets' },
          { label: 'Asset Register', to: '/admin/fixed-assets/assets' },
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
                  onClick={() => navigate('/admin/fixed-assets/assets')}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={form.formState.isSubmitting}>
                  <Save className="mr-2 h-4 w-4" />
                  {form.formState.isSubmitting ? 'Saving…' : 'Save asset'}
                </Button>
              </>
            }
          >
            <FormSection
              title="Asset Identity"
              description="Core information used in the register and downstream depreciation runs."
            >
              <FormField
                control={form.control}
                name="assetName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Asset name</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="categoryId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Category</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select category" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {relatedMasters.categories.map((category) => (
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
              title="Placement & Ownership"
              description="Assign the asset to a location, department, and vendor reference."
            >
              <FormField
                control={form.control}
                name="locationId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Location</FormLabel>
                    <Select value={field.value || 'NONE'} onValueChange={(value) => field.onChange(value === 'NONE' ? '' : value)}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Not assigned" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="NONE">Not assigned</SelectItem>
                        {relatedMasters.units.map((unit) => (
                          <SelectItem key={unit.id} value={unit.id}>
                            {unit.code ? `${unit.code} · ` : ''}
                            {unit.name}
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
                name="departmentId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Department</FormLabel>
                    <Select value={field.value || 'NONE'} onValueChange={(value) => field.onChange(value === 'NONE' ? '' : value)}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Not assigned" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="NONE">Not assigned</SelectItem>
                        {relatedMasters.departments.map((department) => (
                          <SelectItem key={department.id} value={department.id}>
                            {department.code ? `${department.code} · ` : ''}
                            {department.name}
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
                name="vendorId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Vendor</FormLabel>
                    <Select value={field.value || 'NONE'} onValueChange={(value) => field.onChange(value === 'NONE' ? '' : value)}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Not linked" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="NONE">Not linked</SelectItem>
                        {relatedMasters.vendors.map((vendor) => (
                          <SelectItem key={vendor.id} value={vendor.id}>
                            {vendor.code ? `${vendor.code} · ` : ''}
                            {vendor.name}
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
                name="acquisitionType"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Acquisition type</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {acquisitionTypeOptions.map((option) => (
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

            <FormSection
              title="Acquisition & Depreciation"
              description="Capture values needed for capitalization, monthly depreciation, and the audit trail."
            >
              <FormField
                control={form.control}
                name="acquisitionDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Acquisition date</FormLabel>
                    <FormControl>
                      <DatePicker date={toDate(field.value)} onSelect={(value) => field.onChange(toIsoDate(value))} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="putToUseDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Put-to-use date</FormLabel>
                    <FormControl>
                      <DatePicker date={toDate(field.value)} onSelect={(value) => field.onChange(toIsoDate(value))} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="acquisitionCost"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Acquisition cost</FormLabel>
                    <FormControl>
                      <AmountInput value={field.value} onChange={field.onChange} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="installationCost"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Installation cost</FormLabel>
                    <FormControl>
                      <AmountInput value={field.value} onChange={field.onChange} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="otherCosts"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Other costs</FormLabel>
                    <FormControl>
                      <AmountInput value={field.value} onChange={field.onChange} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="residualValue"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Residual value</FormLabel>
                    <FormControl>
                      <AmountInput value={field.value} onChange={field.onChange} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="depreciationMethod"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Depreciation method</FormLabel>
                    <Select value={field.value || 'NONE'} onValueChange={(value) => field.onChange(value === 'NONE' ? '' : value)}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Use category default" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="NONE">Use category default</SelectItem>
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
                name="depreciationRate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Depreciation rate</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.01"
                        min={0}
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
                name="usefulLifeMonths"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Useful life (months)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={1}
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
            </FormSection>

            <FormSection
              title="Commercial References"
              description="Keep invoice, PO, and serial references with the draft asset."
            >
              <FormField
                control={form.control}
                name="invoiceNumber"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Invoice number</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="invoiceDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Invoice date</FormLabel>
                    <FormControl>
                      <DatePicker date={toDate(field.value)} onSelect={(value) => field.onChange(toIsoDate(value))} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="poNumber"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>PO number</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="quantity"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Quantity</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={1}
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
                name="make"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Make</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="model"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Model</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="serialNumber"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Serial number</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="warrantyStartDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Warranty start</FormLabel>
                    <FormControl>
                      <DatePicker date={toDate(field.value)} onSelect={(value) => field.onChange(toIsoDate(value))} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="warrantyExpiryDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Warranty expiry</FormLabel>
                    <FormControl>
                      <DatePicker date={toDate(field.value)} onSelect={(value) => field.onChange(toIsoDate(value))} />
                    </FormControl>
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
