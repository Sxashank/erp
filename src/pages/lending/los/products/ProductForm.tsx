import { zodResolver } from '@hookform/resolvers/zod';
import { FileCheck2, Save } from 'lucide-react';
import { useEffect, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { z } from 'zod';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountInput } from '@/components/lending/common/AmountInput';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { useLendingMasterRows, useLendingOptionRows } from '@/hooks/lending/useLendingMasters';
import { useLoanProduct } from '@/hooks/lending/useLoanProduct';
import { useCreateLoanProduct, useUpdateLoanProduct } from '@/hooks/lending/useLoanProducts';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import type { LoanProductMutationPayload } from '@/services/lending/productApi';

const today = new Date().toISOString().split('T')[0];
const optionalNonNegativeNumber = z.number().min(0).optional();
const optionalNumberRegister = {
  setValueAs: (value: string) => (value === '' ? undefined : Number(value)),
};

const productSchema = z.object({
  productCode: z.string().min(1, 'Product code is required'),
  productName: z.string().min(1, 'Product name is required'),
  description: z.string().optional(),
  category: z.string().min(1, 'Category is required'),
  subCategory: z.string().optional(),
  minAmount: z.number().min(0, 'Minimum amount must be positive'),
  maxAmount: z.number().min(0, 'Maximum amount must be positive'),
  minTenureMonths: z.number().min(1, 'Minimum tenure must be at least 1 month'),
  maxTenureMonths: z.number().min(1, 'Maximum tenure must be at least 1 month'),
  interestType: z.string().min(1, 'Interest type is required'),
  spreadBps: z.number().min(0).default(0),
  fixedRate: z.number().min(0).max(100).optional(),
  moratoriumAllowed: z.boolean().default(true),
  maxMoratoriumMonths: optionalNonNegativeNumber,
  repaymentFrequency: z.array(z.string()).min(1, 'Select at least one repayment frequency'),
  repaymentModes: z.array(z.string()).min(1, 'Select at least one repayment mode'),
  dayCountConvention: z.string().min(1, 'Day count convention is required'),
  prepaymentAllowed: z.boolean().default(true),
  prepaymentLockInMonths: optionalNonNegativeNumber,
  requiresCollateral: z.boolean().default(true),
  minCollateralCoverage: optionalNonNegativeNumber,
  effectiveFrom: z.string().min(1, 'Effective from date is required'),
  status: z.enum(['ACTIVE', 'INACTIVE']).default('ACTIVE'),
});

type ProductFormInput = z.input<typeof productSchema>;
type ProductFormData = z.output<typeof productSchema>;

const defaultValues: ProductFormInput = {
  productCode: '',
  productName: '',
  description: '',
  category: '',
  subCategory: '',
  minAmount: 1000000,
  maxAmount: 1000000000,
  minTenureMonths: 12,
  maxTenureMonths: 120,
  interestType: '',
  spreadBps: 200,
  fixedRate: undefined,
  moratoriumAllowed: true,
  maxMoratoriumMonths: 12,
  repaymentFrequency: [],
  repaymentModes: [],
  dayCountConvention: '',
  prepaymentAllowed: true,
  prepaymentLockInMonths: undefined,
  requiresCollateral: true,
  minCollateralCoverage: 100,
  effectiveFrom: today,
  status: 'ACTIVE',
};

function toOptions(
  rows: { data: Record<string, unknown> }[] | undefined,
  labelKey: 'label' | 'name' = 'label',
) {
  return (
    rows?.map((row) => ({
      value: String(row.data.code ?? ''),
      label: String(row.data[labelKey] ?? row.data.label ?? row.data.name ?? row.data.code ?? ''),
    })) ?? []
  );
}

function numberFromDecimal(value: string | number | null | undefined): number | undefined {
  if (value === null || value === undefined || value === '') return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function blankToNull(value: string | undefined): string | null {
  return value && value.trim() ? value.trim() : null;
}

function toPayload(data: ProductFormData): LoanProductMutationPayload {
  const fixedRate = data.interestType === 'FIXED' ? (data.fixedRate ?? null) : null;
  const defaultFrequency = data.repaymentFrequency[0];
  return {
    code: data.productCode,
    name: data.productName,
    description: blankToNull(data.description),
    category: data.category,
    subCategory: blankToNull(data.subCategory),
    minAmount: data.minAmount,
    maxAmount: data.maxAmount,
    minTenureMonths: data.minTenureMonths,
    maxTenureMonths: data.maxTenureMonths,
    allowsMoratorium: data.moratoriumAllowed,
    maxMoratoriumMonths: data.moratoriumAllowed ? (data.maxMoratoriumMonths ?? null) : 0,
    interestType: data.interestType,
    minSpreadBps: 0,
    maxSpreadBps: data.interestType === 'FLOATING' ? Math.max(data.spreadBps, 500) : 0,
    defaultSpreadBps: data.interestType === 'FLOATING' ? data.spreadBps : 0,
    minEffectiveRate: fixedRate,
    maxEffectiveRate: fixedRate,
    dayCountConvention: data.dayCountConvention,
    allowedRepaymentFrequencies: data.repaymentFrequency,
    defaultRepaymentFrequency: defaultFrequency,
    allowedRepaymentModes: data.repaymentModes,
    defaultRepaymentMode: data.repaymentModes[0],
    allowsPrepayment: data.prepaymentAllowed,
    prepaymentLockInMonths: data.prepaymentAllowed ? (data.prepaymentLockInMonths ?? null) : null,
    allowsForeclosure: data.prepaymentAllowed,
    requiresCollateral: data.requiresCollateral,
    minCollateralCoverage: data.requiresCollateral ? (data.minCollateralCoverage ?? null) : null,
    requiresGuarantee: false,
    effectiveFrom: data.effectiveFrom,
    isActive: data.status === 'ACTIVE',
  };
}

export default function ProductForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { toast } = useToast();
  const isEdit = Boolean(id);

  const productQuery = useLoanProduct(id);
  const createMutation = useCreateLoanProduct();
  const updateMutation = useUpdateLoanProduct();
  const productCategoriesQuery = useLendingOptionRows('PRODUCT_CATEGORY');
  const interestTypesQuery = useLendingOptionRows('RATE_TYPE');
  const repaymentFrequenciesQuery = useLendingOptionRows('REPAYMENT_FREQUENCY');
  const repaymentModesQuery = useLendingOptionRows('REPAYMENT_MODE');
  const dayCountConventionsQuery = useLendingMasterRows('day-count-conventions', {
    pageSize: 100,
  });

  const productCategoryOptions = useMemo(
    () => toOptions(productCategoriesQuery.data?.items),
    [productCategoriesQuery.data?.items],
  );
  const interestTypeOptions = useMemo(
    () => toOptions(interestTypesQuery.data?.items),
    [interestTypesQuery.data?.items],
  );
  const repaymentFrequencyOptions = useMemo(
    () => toOptions(repaymentFrequenciesQuery.data?.items),
    [repaymentFrequenciesQuery.data?.items],
  );
  const repaymentModeOptions = useMemo(
    () => toOptions(repaymentModesQuery.data?.items),
    [repaymentModesQuery.data?.items],
  );
  const dayCountConventionOptions = useMemo(
    () => toOptions(dayCountConventionsQuery.data?.items, 'name'),
    [dayCountConventionsQuery.data?.items],
  );

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    getValues,
    reset,
    formState: { errors },
  } = useForm<ProductFormInput, unknown, ProductFormData>({
    resolver: zodResolver(productSchema),
    defaultValues,
  });

  const interestType = watch('interestType');
  const saving = createMutation.isPending || updateMutation.isPending;
  const loadingMasters =
    productCategoriesQuery.isLoading ||
    interestTypesQuery.isLoading ||
    repaymentFrequenciesQuery.isLoading ||
    repaymentModesQuery.isLoading ||
    dayCountConventionsQuery.isLoading;
  const masterError =
    productCategoriesQuery.error ??
    interestTypesQuery.error ??
    repaymentFrequenciesQuery.error ??
    repaymentModesQuery.error ??
    dayCountConventionsQuery.error;

  useEffect(() => {
    if (isEdit) return;
    if (!getValues('category') && productCategoryOptions[0]) {
      setValue('category', productCategoryOptions[0].value);
    }
    if (!getValues('interestType') && interestTypeOptions[0]) {
      setValue('interestType', interestTypeOptions[0].value);
    }
    if (!getValues('dayCountConvention') && dayCountConventionOptions[0]) {
      setValue('dayCountConvention', dayCountConventionOptions[0].value);
    }
    if (!getValues('repaymentFrequency').length && repaymentFrequencyOptions[0]) {
      setValue('repaymentFrequency', [repaymentFrequencyOptions[0].value]);
    }
    if (!getValues('repaymentModes').length && repaymentModeOptions[0]) {
      setValue('repaymentModes', [repaymentModeOptions[0].value]);
    }
  }, [
    dayCountConventionOptions,
    getValues,
    interestTypeOptions,
    isEdit,
    productCategoryOptions,
    repaymentFrequencyOptions,
    repaymentModeOptions,
    setValue,
  ]);

  useEffect(() => {
    const product = productQuery.data;
    if (!product) return;
    reset({
      productCode: product.code,
      productName: product.name,
      description: product.description ?? '',
      category: product.category,
      subCategory: product.subCategory ?? '',
      minAmount: numberFromDecimal(product.minAmount) ?? 0,
      maxAmount: numberFromDecimal(product.maxAmount) ?? 0,
      minTenureMonths: product.minTenureMonths,
      maxTenureMonths: product.maxTenureMonths,
      interestType: product.interestType,
      spreadBps: product.defaultSpreadBps ?? 0,
      fixedRate: numberFromDecimal(product.minEffectiveRate),
      moratoriumAllowed: product.allowsMoratorium,
      maxMoratoriumMonths: product.maxMoratoriumMonths ?? undefined,
      repaymentFrequency: product.allowedRepaymentFrequencies?.length
        ? product.allowedRepaymentFrequencies
        : [product.defaultRepaymentFrequency],
      repaymentModes: product.allowedRepaymentModes?.length
        ? product.allowedRepaymentModes
        : [product.defaultRepaymentMode],
      dayCountConvention: product.dayCountConvention,
      prepaymentAllowed: product.allowsPrepayment,
      prepaymentLockInMonths: product.prepaymentLockInMonths ?? undefined,
      requiresCollateral: product.requiresCollateral,
      minCollateralCoverage: numberFromDecimal(product.minCollateralCoverage),
      effectiveFrom: product.effectiveFrom,
      status: product.isActive ? 'ACTIVE' : 'INACTIVE',
    });
  }, [productQuery.data, reset]);

  const onSubmit = async (data: ProductFormData) => {
    const payload = toPayload(data);
    try {
      if (isEdit && id) {
        await updateMutation.mutateAsync({ productId: id, payload });
        toast({ title: 'Product updated' });
        navigate(`/admin/lending/products/${id}`);
        return;
      }
      const created = await createMutation.mutateAsync(payload);
      toast({ title: 'Product created' });
      navigate(`/admin/lending/products/${created.id}`);
    } catch (error) {
      showErrorToast(error, toast);
    }
  };

  if ((isEdit && productQuery.isLoading) || loadingMasters) {
    return (
      <div className="space-y-6">
        <PageHeader
          title={isEdit ? 'Edit Loan Product' : 'Create Loan Product'}
          breadcrumbs={[
            { label: 'Loan Products', to: '/admin/lending/products' },
            { label: isEdit ? 'Edit' : 'New' },
          ]}
        />
        <Card>
          <CardContent className="p-8 text-sm text-muted-foreground">
            Loading product setup...
          </CardContent>
        </Card>
      </div>
    );
  }

  if ((isEdit && productQuery.isError) || masterError) {
    return (
      <ErrorState
        title="Could not load product setup"
        error={productQuery.error ?? masterError}
        onRetry={() => {
          productQuery.refetch();
          productCategoriesQuery.refetch();
          interestTypesQuery.refetch();
          repaymentFrequenciesQuery.refetch();
          repaymentModesQuery.refetch();
          dayCountConventionsQuery.refetch();
        }}
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEdit ? 'Edit Loan Product' : 'Create Loan Product'}
        subtitle={
          isEdit
            ? 'Update product configuration and terms'
            : 'Configure a new loan product with terms and conditions'
        }
        breadcrumbs={[
          { label: 'Loan Products', to: '/admin/lending/products' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
        actions={
          <div className="flex gap-2">
            {isEdit && id ? (
              <Button variant="outline" asChild>
                <Link to={`/admin/lending/products/${id}/checklist`}>
                  <FileCheck2 className="mr-2 h-4 w-4" />
                  Document requirements
                </Link>
              </Button>
            ) : null}
            <Button onClick={handleSubmit(onSubmit)} disabled={saving}>
              <Save className="mr-2 h-4 w-4" />
              {isEdit ? 'Update Product' : 'Create Product'}
            </Button>
          </div>
        }
      />

      <form onSubmit={handleSubmit(onSubmit)}>
        <Tabs defaultValue="basic">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="basic">Basic Info</TabsTrigger>
            <TabsTrigger value="interest">Interest</TabsTrigger>
            <TabsTrigger value="terms">Terms</TabsTrigger>
          </TabsList>

          <TabsContent value="basic" className="mt-6 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Product Details</CardTitle>
                <CardDescription>Basic product identification and categorisation</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="productCode">Product Code *</Label>
                    <Input
                      id="productCode"
                      placeholder="e.g., TL-CORP-001"
                      {...register('productCode')}
                    />
                    {errors.productCode ? (
                      <p className="text-sm text-destructive">{errors.productCode.message}</p>
                    ) : null}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="productName">Product Name *</Label>
                    <Input
                      id="productName"
                      placeholder="e.g., Corporate Term Loan"
                      {...register('productName')}
                    />
                    {errors.productName ? (
                      <p className="text-sm text-destructive">{errors.productName.message}</p>
                    ) : null}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea id="description" rows={3} {...register('description')} />
                </div>

                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label>Category *</Label>
                    <Select
                      value={watch('category')}
                      onValueChange={(value) => setValue('category', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent>
                        {productCategoryOptions.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="subCategory">Sub Category</Label>
                    <Input
                      id="subCategory"
                      placeholder="e.g., Corporate"
                      {...register('subCategory')}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Status</Label>
                    <Select
                      value={watch('status')}
                      onValueChange={(value) =>
                        setValue('status', value as ProductFormData['status'])
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="ACTIVE">Active</SelectItem>
                        <SelectItem value="INACTIVE">Inactive</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Minimum Loan Amount *</Label>
                    <AmountInput
                      value={watch('minAmount') || 0}
                      onChange={(value) => setValue('minAmount', value ?? 0)}
                    />
                    {errors.minAmount ? (
                      <p className="text-sm text-destructive">{errors.minAmount.message}</p>
                    ) : null}
                  </div>
                  <div className="space-y-2">
                    <Label>Maximum Loan Amount *</Label>
                    <AmountInput
                      value={watch('maxAmount') || 0}
                      onChange={(value) => setValue('maxAmount', value ?? 0)}
                    />
                    {errors.maxAmount ? (
                      <p className="text-sm text-destructive">{errors.maxAmount.message}</p>
                    ) : null}
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="minTenureMonths">Minimum Tenure (Months) *</Label>
                    <Input
                      id="minTenureMonths"
                      type="number"
                      min={1}
                      {...register('minTenureMonths', { valueAsNumber: true })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="maxTenureMonths">Maximum Tenure (Months) *</Label>
                    <Input
                      id="maxTenureMonths"
                      type="number"
                      min={1}
                      {...register('maxTenureMonths', { valueAsNumber: true })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="effectiveFrom">Effective From *</Label>
                    <Input id="effectiveFrom" type="date" {...register('effectiveFrom')} />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="interest" className="mt-6 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Interest Configuration</CardTitle>
                <CardDescription>Define rate type and calculation parameters</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Interest Type *</Label>
                    <Select
                      value={interestType}
                      onValueChange={(value) => setValue('interestType', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select interest type" />
                      </SelectTrigger>
                      <SelectContent>
                        {interestTypeOptions.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Day Count Convention *</Label>
                    <Select
                      value={watch('dayCountConvention')}
                      onValueChange={(value) => setValue('dayCountConvention', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select convention" />
                      </SelectTrigger>
                      <SelectContent>
                        {dayCountConventionOptions.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {interestType === 'FLOATING' ? (
                  <div className="space-y-2">
                    <Label htmlFor="spreadBps">Default Spread (Basis Points) *</Label>
                    <Input
                      id="spreadBps"
                      type="number"
                      min={0}
                      {...register('spreadBps', { valueAsNumber: true })}
                    />
                    <p className="text-xs text-muted-foreground">100 bps = 1%.</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Label htmlFor="fixedRate">Fixed Interest Rate (% p.a.) *</Label>
                    <Input
                      id="fixedRate"
                      type="number"
                      step="0.01"
                      min={0}
                      max={100}
                      {...register('fixedRate', optionalNumberRegister)}
                    />
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="terms" className="mt-6 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Repayment Terms</CardTitle>
                <CardDescription>
                  Configure repayment frequency and moratorium controls
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Repayment Frequency Options</Label>
                  <div className="flex flex-wrap gap-4">
                    {repaymentFrequencyOptions.map((option) => (
                      <label key={option.value} className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          value={option.value}
                          {...register('repaymentFrequency')}
                          className="h-4 w-4 rounded border-gray-300"
                        />
                        <span className="text-sm">{option.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Repayment Mode Options</Label>
                  <div className="flex flex-wrap gap-4">
                    {repaymentModeOptions.map((option) => (
                      <label key={option.value} className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          value={option.value}
                          {...register('repaymentModes')}
                          className="h-4 w-4 rounded border-gray-300"
                        />
                        <span className="text-sm">{option.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="flex items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <Label>Moratorium Allowed</Label>
                    <p className="text-sm text-muted-foreground">
                      Allow moratorium at the start of the loan
                    </p>
                  </div>
                  <Switch
                    checked={watch('moratoriumAllowed')}
                    onCheckedChange={(value) => setValue('moratoriumAllowed', value)}
                  />
                </div>

                {watch('moratoriumAllowed') ? (
                  <div className="space-y-2">
                    <Label htmlFor="maxMoratoriumMonths">Maximum Moratorium Period (Months)</Label>
                    <Input
                      id="maxMoratoriumMonths"
                      type="number"
                      min={0}
                      className="w-[200px]"
                      {...register('maxMoratoriumMonths', optionalNumberRegister)}
                    />
                  </div>
                ) : null}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Prepayment And Collateral</CardTitle>
                <CardDescription>
                  Configure product-level servicing and security controls
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <Label>Prepayment Allowed</Label>
                    <p className="text-sm text-muted-foreground">
                      Allow borrower to prepay the loan
                    </p>
                  </div>
                  <Switch
                    checked={watch('prepaymentAllowed')}
                    onCheckedChange={(value) => setValue('prepaymentAllowed', value)}
                  />
                </div>

                {watch('prepaymentAllowed') ? (
                  <div className="space-y-2">
                    <Label htmlFor="prepaymentLockInMonths">Lock-in Period (Months)</Label>
                    <Input
                      id="prepaymentLockInMonths"
                      type="number"
                      min={0}
                      className="w-[200px]"
                      {...register('prepaymentLockInMonths', optionalNumberRegister)}
                    />
                  </div>
                ) : null}

                <div className="flex items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <Label>Collateral Required</Label>
                    <p className="text-sm text-muted-foreground">
                      Require collateral/security for this product
                    </p>
                  </div>
                  <Switch
                    checked={watch('requiresCollateral')}
                    onCheckedChange={(value) => setValue('requiresCollateral', value)}
                  />
                </div>

                {watch('requiresCollateral') ? (
                  <div className="space-y-2">
                    <Label htmlFor="minCollateralCoverage">Minimum Collateral Coverage (%)</Label>
                    <Input
                      id="minCollateralCoverage"
                      type="number"
                      min={0}
                      step="0.01"
                      className="w-[220px]"
                      {...register('minCollateralCoverage', optionalNumberRegister)}
                    />
                  </div>
                ) : null}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </form>
    </div>
  );
}
