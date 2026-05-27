import { zodResolver } from '@hookform/resolvers/zod';
import { Save, Plus, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';

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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { useLendingOptionRows } from '@/hooks/lending/useLendingMasters';
import { useSanction } from '@/hooks/lending/useSanction';
import { useCreateSanction, useUpdateSanction } from '@/hooks/lending/useSanctionMutations';
import { sanctionSchema, type SanctionFormData } from '@/schemas/lending/sanctionSchema';

// Default values for form fields. Conditions, securities and covenants start
// empty; the user adds rows as needed.
const defaultValues: Partial<SanctionFormData> = {
  interestType: 'FLOATING',
  spreadBps: 0,
  effectiveRate: 0,
  repaymentFrequency: 'MONTHLY',
  repaymentMode: 'EMI',
  validityDays: 90,
  moratoriumMonths: 0,
  conditions: [],
  securities: [],
  covenants: [],
};

const addDays = (date: Date, days: number) => {
  const nextDate = new Date(date);
  nextDate.setDate(nextDate.getDate() + days);
  return nextDate.toISOString().slice(0, 10);
};

function toOptionRows(rows: { data: Record<string, unknown> }[] | undefined) {
  return (
    rows?.map((row) => ({
      value: String(row.data.code ?? ''),
      label: String(row.data.label ?? row.data.name ?? row.data.code ?? ''),
    })) ?? []
  );
}

export default function SanctionForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const applicationId = searchParams.get('applicationId');
  const isEdit = Boolean(id);
  const [activeTab, setActiveTab] = useState('terms');
  const { data: existingSanction } = useSanction(isEdit ? id : undefined);
  const createMutation = useCreateSanction();
  const updateMutation = useUpdateSanction(id);
  const interestTypesQuery = useLendingOptionRows('RATE_TYPE');
  const repaymentFrequenciesQuery = useLendingOptionRows('REPAYMENT_FREQUENCY');
  const repaymentModesQuery = useLendingOptionRows('REPAYMENT_MODE');
  const securityNaturesQuery = useLendingOptionRows('SECURITY_NATURE');
  const securityCategoriesQuery = useLendingOptionRows('SECURITY_CATEGORY');
  const covenantTypesQuery = useLendingOptionRows('COVENANT_TYPE');
  const covenantFrequenciesQuery = useLendingOptionRows('COVENANT_FREQUENCY');

  const interestTypeOptions = toOptionRows(interestTypesQuery.data?.items);
  const repaymentFrequencyOptions = toOptionRows(repaymentFrequenciesQuery.data?.items);
  const repaymentModeOptions = toOptionRows(repaymentModesQuery.data?.items);
  const securityNatureOptions = toOptionRows(securityNaturesQuery.data?.items);
  const securityCategoryOptions = toOptionRows(securityCategoriesQuery.data?.items);
  const covenantTypeOptions = toOptionRows(covenantTypesQuery.data?.items);
  const covenantFrequencyOptions = toOptionRows(covenantFrequenciesQuery.data?.items);

  const {
    register,
    control,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<SanctionFormData>({
    resolver: zodResolver(sanctionSchema),
    defaultValues: {
      ...defaultValues,
      applicationId: applicationId || '',
      sanctionedAmount: 0,
      tenureMonths: 0,
    },
  });

  const {
    fields: conditionFields,
    append: appendCondition,
    remove: removeCondition,
  } = useFieldArray({
    control,
    name: 'conditions',
  });

  const {
    fields: securityFields,
    append: appendSecurity,
    remove: removeSecurity,
  } = useFieldArray({
    control,
    name: 'securities',
  });

  const {
    fields: covenantFields,
    append: appendCovenant,
    remove: removeCovenant,
  } = useFieldArray({
    control,
    name: 'covenants',
  });

  const interestType = watch('interestType');

  useEffect(() => {
    if (!existingSanction) return;

    const sanctionDate = new Date(existingSanction.sanctionDate);
    const validityDate = new Date(existingSanction.validityDate);
    const validityDays = Math.max(
      1,
      Math.ceil((validityDate.getTime() - sanctionDate.getTime()) / 86_400_000),
    );

    reset({
      applicationId: existingSanction.applicationId,
      sanctionedAmount: Number(existingSanction.sanctionedAmount),
      interestType: existingSanction.interestType,
      spreadBps: existingSanction.spreadBps,
      effectiveRate: Number(existingSanction.effectiveRate),
      tenureMonths: existingSanction.tenureMonths,
      moratoriumMonths: existingSanction.moratoriumMonths,
      repaymentFrequency: existingSanction.repaymentFrequency,
      repaymentMode: existingSanction.repaymentMode,
      validityDays,
      conditions: [],
      securities: [],
      covenants: [],
      remarks: existingSanction.remarks ?? '',
    });
  }, [existingSanction, reset]);

  const onSubmit = async (data: SanctionFormData) => {
    const sanctionDate = new Date().toISOString().slice(0, 10);
    const basePayload = {
      sanctionedAmount: data.sanctionedAmount,
      tenureMonths: data.tenureMonths,
      moratoriumMonths: data.moratoriumMonths,
      interestType: data.interestType,
      spreadBps: data.spreadBps,
      effectiveRate: data.effectiveRate,
      repaymentMode: data.repaymentMode,
      repaymentFrequency: data.repaymentFrequency,
      dayCountConvention: 'ACT_365',
      disbursementType: 'SINGLE',
      maxTranches: 1,
      sanctionDate,
      validityDate: addDays(new Date(sanctionDate), data.validityDays),
      specialTerms: data.covenants.length
        ? data.covenants
            .map((covenant) => `${covenant.covenantType}: ${covenant.description}`)
            .join('\n')
        : undefined,
      remarks: data.remarks,
    };

    if (isEdit) {
      const sanction = await updateMutation.mutateAsync(basePayload);
      navigate(`/admin/lending/sanctions/${sanction.id}`);
      return;
    }

    const sanction = await createMutation.mutateAsync({
      applicationId: data.applicationId,
      ...basePayload,
      conditions: [
        ...data.conditions.map((condition, index) => ({
          conditionType: condition.conditionType,
          category: 'OPERATIONAL' as const,
          description: condition.description,
          isMandatory: condition.isMandatory,
          blocksDisbursement: condition.conditionType === 'PRE_DISBURSEMENT',
          displayOrder: index + 1,
        })),
        ...data.covenants.map((covenant, index) => ({
          conditionType: 'ONGOING' as const,
          category:
            covenant.covenantType === 'FINANCIAL'
              ? ('FINANCIAL' as const)
              : ('OPERATIONAL' as const),
          description: covenant.threshold
            ? `${covenant.description} (Threshold: ${covenant.threshold})`
            : covenant.description,
          isMandatory: true,
          blocksDisbursement: false,
          frequency: covenant.frequency,
          displayOrder: data.conditions.length + index + 1,
        })),
      ],
      securities: data.securities.map((security) => ({
        securityCategory: security.securityCategory,
        securityType: security.securityType,
        chargeType: 'FIRST',
        description: security.description,
        marketValue: security.acceptableValue,
        acceptableValue: security.acceptableValue,
        marginPercentage: security.marginPercentage,
      })),
    });

    navigate(`/admin/lending/sanctions/${sanction.id}`);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEdit ? 'Edit Sanction' : 'Create Sanction'}
        subtitle="Define sanction terms, conditions, and covenants for the loan"
        breadcrumbs={[
          { label: 'Sanctions', to: '/admin/lending/sanctions' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
        actions={
          <Button onClick={handleSubmit(onSubmit)} disabled={isSubmitting}>
            <Save className="mr-2 h-4 w-4" />
            {isEdit ? 'Update Sanction' : 'Create Sanction'}
          </Button>
        }
      />

      {/* Application context — pulled from the application referenced in the URL.
          Detailed entity / product / requested-amount summary will be wired
          once the per-application sanction-prefill endpoint lands. */}
      {applicationId && (
        <Card>
          <CardHeader>
            <CardTitle>Application Context</CardTitle>
            <CardDescription>Application ID: {applicationId}</CardDescription>
          </CardHeader>
        </Card>
      )}

      <form onSubmit={handleSubmit(onSubmit)}>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="terms">Sanction Terms</TabsTrigger>
            <TabsTrigger value="conditions">Conditions</TabsTrigger>
            <TabsTrigger value="security">Security</TabsTrigger>
            <TabsTrigger value="covenants">Covenants</TabsTrigger>
          </TabsList>

          {/* Sanction Terms Tab */}
          <TabsContent value="terms" className="mt-6 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Loan Amount & Tenure</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label>Sanctioned Amount *</Label>
                    <AmountInput
                      value={watch('sanctionedAmount') || 0}
                      onChange={(v) => setValue('sanctionedAmount', v ?? 0)}
                      placeholder="Enter sanctioned amount"
                    />
                    {errors.sanctionedAmount && (
                      <p className="text-sm text-destructive">{errors.sanctionedAmount.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="tenureMonths">Tenure (Months) *</Label>
                    <Input
                      id="tenureMonths"
                      type="number"
                      min={1}
                      {...register('tenureMonths', { valueAsNumber: true })}
                    />
                    {errors.tenureMonths && (
                      <p className="text-sm text-destructive">{errors.tenureMonths.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="moratoriumMonths">Moratorium (Months)</Label>
                    <Input
                      id="moratoriumMonths"
                      type="number"
                      min={0}
                      {...register('moratoriumMonths', { valueAsNumber: true })}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Interest Configuration</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Interest Type *</Label>
                    <Select
                      value={interestType}
                      onValueChange={(v) =>
                        setValue('interestType', v as SanctionFormData['interestType'])
                      }
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
                </div>

                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="spreadBps">Spread (Basis Points)</Label>
                    <Input
                      id="spreadBps"
                      type="number"
                      min={0}
                      placeholder="e.g., 200 for 2%"
                      {...register('spreadBps', { valueAsNumber: true })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="effectiveRate">Effective Rate (% p.a.) *</Label>
                    <Input
                      id="effectiveRate"
                      type="number"
                      step="0.01"
                      min={0}
                      max={100}
                      {...register('effectiveRate', { valueAsNumber: true })}
                    />
                    {errors.effectiveRate && (
                      <p className="text-sm text-destructive">{errors.effectiveRate.message}</p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Repayment Terms</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Repayment Frequency *</Label>
                    <Select
                      value={watch('repaymentFrequency')}
                      onValueChange={(v) =>
                        setValue('repaymentFrequency', v as SanctionFormData['repaymentFrequency'])
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select frequency" />
                      </SelectTrigger>
                      <SelectContent>
                        {repaymentFrequencyOptions.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Repayment Mode *</Label>
                    <Select
                      value={watch('repaymentMode')}
                      onValueChange={(v) =>
                        setValue('repaymentMode', v as SanctionFormData['repaymentMode'])
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select mode" />
                      </SelectTrigger>
                      <SelectContent>
                        {repaymentModeOptions.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Fees & Validity</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="validityDays">Sanction Validity (Days)</Label>
                    <Input
                      id="validityDays"
                      type="number"
                      min={1}
                      className="w-[200px]"
                      {...register('validityDays', { valueAsNumber: true })}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Conditions Tab */}
          <TabsContent value="conditions" className="mt-6 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Pre-Disbursement Conditions</CardTitle>
                <CardDescription>
                  Conditions that must be satisfied before any disbursement
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[50px]">#</TableHead>
                      <TableHead>Condition</TableHead>
                      <TableHead className="w-[120px]">Mandatory</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {conditionFields
                      .filter(
                        (_, i) => watch(`conditions.${i}.conditionType`) === 'PRE_DISBURSEMENT',
                      )
                      .map((field, displayIndex) => {
                        const actualIndex = conditionFields.findIndex((f) => f.id === field.id);
                        return (
                          <TableRow key={field.id}>
                            <TableCell>{displayIndex + 1}</TableCell>
                            <TableCell>
                              <Textarea
                                {...register(`conditions.${actualIndex}.description`)}
                                rows={2}
                                placeholder="Enter condition..."
                              />
                            </TableCell>
                            <TableCell>
                              <Switch
                                checked={watch(`conditions.${actualIndex}.isMandatory`)}
                                onCheckedChange={(v) =>
                                  setValue(`conditions.${actualIndex}.isMandatory`, v)
                                }
                              />
                            </TableCell>
                            <TableCell>
                              <Button
                                type="button"
                                variant="ghost"
                                size="icon"
                                onClick={() => removeCondition(actualIndex)}
                              >
                                <Trash2 className="h-4 w-4 text-destructive" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                  </TableBody>
                </Table>
                <Button
                  type="button"
                  variant="outline"
                  className="mt-4"
                  onClick={() =>
                    appendCondition({
                      conditionType: 'PRE_DISBURSEMENT',
                      description: '',
                      isMandatory: true,
                    })
                  }
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Pre-Disbursement Condition
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Post-Disbursement Conditions</CardTitle>
                <CardDescription>Conditions to be complied with after disbursement</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[50px]">#</TableHead>
                      <TableHead>Condition</TableHead>
                      <TableHead className="w-[120px]">Mandatory</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {conditionFields
                      .filter(
                        (_, i) => watch(`conditions.${i}.conditionType`) === 'POST_DISBURSEMENT',
                      )
                      .map((field, displayIndex) => {
                        const actualIndex = conditionFields.findIndex((f) => f.id === field.id);
                        return (
                          <TableRow key={field.id}>
                            <TableCell>{displayIndex + 1}</TableCell>
                            <TableCell>
                              <Textarea
                                {...register(`conditions.${actualIndex}.description`)}
                                rows={2}
                                placeholder="Enter condition..."
                              />
                            </TableCell>
                            <TableCell>
                              <Switch
                                checked={watch(`conditions.${actualIndex}.isMandatory`)}
                                onCheckedChange={(v) =>
                                  setValue(`conditions.${actualIndex}.isMandatory`, v)
                                }
                              />
                            </TableCell>
                            <TableCell>
                              <Button
                                type="button"
                                variant="ghost"
                                size="icon"
                                onClick={() => removeCondition(actualIndex)}
                              >
                                <Trash2 className="h-4 w-4 text-destructive" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                  </TableBody>
                </Table>
                <Button
                  type="button"
                  variant="outline"
                  className="mt-4"
                  onClick={() =>
                    appendCondition({
                      conditionType: 'POST_DISBURSEMENT',
                      description: '',
                      isMandatory: true,
                    })
                  }
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Post-Disbursement Condition
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Security Tab */}
          <TabsContent value="security" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Security/Collateral Details</CardTitle>
                <CardDescription>
                  Define primary security and collateral for the loan
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Type</TableHead>
                      <TableHead>Nature</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-right">Value</TableHead>
                      <TableHead className="text-right">Margin %</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {securityFields.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} className="py-8 text-center text-muted-foreground">
                          No security added. Click "Add Security" to add collateral.
                        </TableCell>
                      </TableRow>
                    ) : (
                      securityFields.map((field, index) => (
                        <TableRow key={field.id}>
                          <TableCell>
                            <Select
                              value={watch(`securities.${index}.securityCategory`)}
                              onValueChange={(v) =>
                                setValue(`securities.${index}.securityCategory`, v)
                              }
                            >
                              <SelectTrigger className="w-[130px]">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {securityNatureOptions.map((option) => (
                                  <SelectItem key={option.value} value={option.value}>
                                    {option.label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell>
                            <Select
                              value={watch(`securities.${index}.securityType`)}
                              onValueChange={(v) => setValue(`securities.${index}.securityType`, v)}
                            >
                              <SelectTrigger className="w-[150px]">
                                <SelectValue placeholder="Select nature" />
                              </SelectTrigger>
                              <SelectContent>
                                {securityCategoryOptions.map((option) => (
                                  <SelectItem key={option.value} value={option.value}>
                                    {option.label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell>
                            <Input
                              {...register(`securities.${index}.description`)}
                              placeholder="Description"
                            />
                          </TableCell>
                          <TableCell className="text-right">
                            <Input
                              type="number"
                              {...register(`securities.${index}.acceptableValue`, {
                                valueAsNumber: true,
                              })}
                              placeholder="Value"
                              className="w-[150px]"
                            />
                          </TableCell>
                          <TableCell className="text-right">
                            <Input
                              type="number"
                              {...register(`securities.${index}.marginPercentage`, {
                                valueAsNumber: true,
                              })}
                              placeholder="%"
                              className="w-[80px]"
                            />
                          </TableCell>
                          <TableCell>
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              onClick={() => removeSecurity(index)}
                            >
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
                <Button
                  type="button"
                  variant="outline"
                  className="mt-4"
                  onClick={() =>
                    appendSecurity({
                      securityCategory: securityNatureOptions[0]?.value ?? '',
                      securityType: securityCategoryOptions[0]?.value ?? '',
                      description: '',
                      acceptableValue: 0,
                      marginPercentage: 0,
                    })
                  }
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Security
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Covenants Tab */}
          <TabsContent value="covenants" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Financial & Other Covenants</CardTitle>
                <CardDescription>
                  Define covenants that the borrower must comply with
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Covenant Type</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Frequency</TableHead>
                      <TableHead>Threshold</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {covenantFields.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} className="py-8 text-center text-muted-foreground">
                          No covenants added. Click "Add Covenant" to define covenants.
                        </TableCell>
                      </TableRow>
                    ) : (
                      covenantFields.map((field, index) => (
                        <TableRow key={field.id}>
                          <TableCell>
                            <Select
                              value={watch(`covenants.${index}.covenantType`)}
                              onValueChange={(v) => setValue(`covenants.${index}.covenantType`, v)}
                            >
                              <SelectTrigger className="w-[130px]">
                                <SelectValue placeholder="Type" />
                              </SelectTrigger>
                              <SelectContent>
                                {covenantTypeOptions.map((option) => (
                                  <SelectItem key={option.value} value={option.value}>
                                    {option.label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell>
                            <Input
                              {...register(`covenants.${index}.description`)}
                              placeholder="Covenant description"
                            />
                          </TableCell>
                          <TableCell>
                            <Select
                              value={watch(`covenants.${index}.frequency`)}
                              onValueChange={(v) => setValue(`covenants.${index}.frequency`, v)}
                            >
                              <SelectTrigger className="w-[120px]">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {covenantFrequencyOptions.map((option) => (
                                  <SelectItem key={option.value} value={option.value}>
                                    {option.label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell>
                            <Input
                              {...register(`covenants.${index}.threshold`)}
                              placeholder="e.g., 1.5x, 2:1"
                              className="w-[100px]"
                            />
                          </TableCell>
                          <TableCell>
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              onClick={() => removeCovenant(index)}
                            >
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
                <Button
                  type="button"
                  variant="outline"
                  className="mt-4"
                  onClick={() =>
                    appendCovenant({
                      covenantType: covenantTypeOptions[0]?.value ?? '',
                      description: '',
                      frequency: covenantFrequencyOptions[0]?.value ?? '',
                      threshold: '',
                    })
                  }
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Covenant
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Additional Remarks</CardTitle>
              </CardHeader>
              <CardContent>
                <Textarea
                  {...register('remarks')}
                  placeholder="Any additional remarks or special conditions..."
                  rows={4}
                />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </form>
    </div>
  );
}
