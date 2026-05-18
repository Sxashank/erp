import { zodResolver } from '@hookform/resolvers/zod';
import {
  ArrowRightLeft,
  PackageCheck,
  ReceiptIndianRupee,
  ShieldAlert,
  TrendingDown,
} from 'lucide-react';
import { useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';

import { AmountInput, DetailGrid, FormSection, FormShell, PageHeader } from '@/components/common';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
import { useFixedAsset } from '@/hooks/fixed-assets/useFixedAssets';
import {
  useCapitalizeFixedAsset,
  useImpairFixedAsset,
  useRevalueFixedAsset,
  useSubmitDisposal,
  useTransferFixedAsset,
} from '@/hooks/fixed-assets/useFixedAssets';
import {
  useFixedAssetDepartments,
  useFixedAssetUnits,
} from '@/hooks/fixed-assets/useMasters';
import { useToast } from '@/hooks/use-toast';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import { showErrorToast } from '@/lib/errorToast';
import {
  assetCapitalizeSchema,
  assetDisposeSchema,
  assetImpairSchema,
  assetRevalueSchema,
  assetTransferSchema,
  type AssetCapitalizeInput,
  type AssetDisposeInput,
  type AssetImpairInput,
  type AssetRevalueInput,
  type AssetTransferInput,
} from '@/schemas/fixed-assets/lifecycleSchema';

type AssetLifecycleAction = 'capitalize' | 'transfer' | 'revalue' | 'impair' | 'dispose';

const disposalTypeOptions = [
  { value: 'SALE', label: 'Sale' },
  { value: 'SCRAP', label: 'Scrap' },
  { value: 'WRITE_OFF', label: 'Write-off' },
  { value: 'DONATION', label: 'Donation' },
  { value: 'LOSS', label: 'Loss / damage' },
] as const;

function toDate(value: string | undefined): Date | null {
  return value ? new Date(value) : null;
}

function toIsoDate(value: Date | undefined): string {
  return value ? value.toISOString().slice(0, 10) : '';
}

export function AssetLifecycleActionPage({
  action,
}: {
  action: AssetLifecycleAction;
}): JSX.Element {
  const organizationId = useRequiredActiveOrganizationId();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const assetQuery = useFixedAsset(id);
  const unitsQuery = useFixedAssetUnits(organizationId);
  const departmentsQuery = useFixedAssetDepartments(organizationId);

  const capitalizeMutation = useCapitalizeFixedAsset(id ?? '', organizationId);
  const transferMutation = useTransferFixedAsset(id ?? '', organizationId);
  const revalueMutation = useRevalueFixedAsset(id ?? '', organizationId);
  const impairMutation = useImpairFixedAsset(id ?? '', organizationId);
  const disposeMutation = useSubmitDisposal(id ?? '', organizationId);

  const capitalizeForm = useForm<AssetCapitalizeInput>({
    resolver: zodResolver(assetCapitalizeSchema),
    defaultValues: {
      capitalizationDate: '',
      putToUseDate: '',
      depreciationStartDate: '',
      remarks: '',
    },
  });

  const transferForm = useForm<AssetTransferInput>({
    resolver: zodResolver(assetTransferSchema),
    defaultValues: {
      transferDate: '',
      toLocationId: '',
      toDepartmentId: '',
      toCustodianId: '',
      reason: '',
    },
  });

  const revalueForm = useForm<AssetRevalueInput>({
    resolver: zodResolver(assetRevalueSchema),
    defaultValues: {
      revaluationDate: '',
      newValue: 0,
      valuerName: '',
      valuationReportNumber: '',
      valuationReportDate: '',
      valuationMethod: '',
      reason: '',
    },
  });

  const impairForm = useForm<AssetImpairInput>({
    resolver: zodResolver(assetImpairSchema),
    defaultValues: {
      impairmentDate: '',
      impairmentAmount: 0,
      reason: '',
    },
  });

  const disposeForm = useForm<AssetDisposeInput>({
    resolver: zodResolver(assetDisposeSchema),
    defaultValues: {
      disposalDate: '',
      disposalType: 'SALE',
      disposalValue: 0,
      disposalRemarks: '',
      buyerName: '',
      buyerAddress: '',
    },
  });

  const config = useMemo(
    () => ({
      capitalize: {
        title: 'Capitalize Asset',
        subtitle: 'Move the draft asset into the active register and start depreciation.',
        icon: <PackageCheck className="h-4 w-4" />,
      },
      transfer: {
        title: 'Transfer Asset',
        subtitle: 'Record the operational transfer to a new location or department.',
        icon: <ArrowRightLeft className="h-4 w-4" />,
      },
      revalue: {
        title: 'Revalue Asset',
        subtitle: 'Record a revaluation adjustment and update the WDV basis.',
        icon: <ReceiptIndianRupee className="h-4 w-4" />,
      },
      impair: {
        title: 'Impair Asset',
        subtitle: 'Record a one-time impairment where the recoverable value has fallen.',
        icon: <TrendingDown className="h-4 w-4" />,
      },
      dispose: {
        title: 'Dispose Asset',
        subtitle: 'Submit a disposal or write-off. Approval will route automatically if configured.',
        icon: <ShieldAlert className="h-4 w-4" />,
      },
    }[action]),
    [action],
  );

  if (assetQuery.isLoading) {
    return <Skeleton className="h-[480px] w-full" />;
  }

  if (!assetQuery.data) {
    return (
      <CardMessage
        title="Asset not found"
        onBack={() => navigate('/admin/fixed-assets/assets')}
      />
    );
  }

  const asset = assetQuery.data;

  async function handleCapitalize(values: AssetCapitalizeInput) {
    try {
      await capitalizeMutation.mutateAsync(values);
      toast({ title: 'Asset capitalized' });
      navigate(`/admin/fixed-assets/assets/${asset.id}`);
    } catch (error) {
      showErrorToast(error, toast);
    }
  }

  async function handleTransfer(values: AssetTransferInput) {
    try {
      await transferMutation.mutateAsync(values);
      toast({ title: 'Asset transferred' });
      navigate(`/admin/fixed-assets/assets/${asset.id}`);
    } catch (error) {
      showErrorToast(error, toast);
    }
  }

  async function handleRevalue(values: AssetRevalueInput) {
    try {
      await revalueMutation.mutateAsync(values);
      toast({ title: 'Asset revalued' });
      navigate(`/admin/fixed-assets/assets/${asset.id}`);
    } catch (error) {
      showErrorToast(error, toast);
    }
  }

  async function handleImpair(values: AssetImpairInput) {
    try {
      await impairMutation.mutateAsync(values);
      toast({ title: 'Asset impairment recorded' });
      navigate(`/admin/fixed-assets/assets/${asset.id}`);
    } catch (error) {
      showErrorToast(error, toast);
    }
  }

  async function handleDispose(values: AssetDisposeInput) {
    try {
      const result = await disposeMutation.mutateAsync(values);
      toast({
        title:
          result.mode === 'disposed'
            ? 'Asset disposed'
            : `Disposal submitted for approval (${result.approvalRequestNumber})`,
      });
      navigate(`/admin/fixed-assets/assets/${asset.id}`);
    } catch (error) {
      showErrorToast(error, toast);
    }
  }

  const summaryCard = (
    <Card>
      <CardHeader>
        <CardTitle>Asset Summary</CardTitle>
      </CardHeader>
      <CardContent>
        <DetailGrid
          columns={2}
          fields={[
            { label: 'Asset', value: `${asset.assetCode} · ${asset.assetName}` },
            { label: 'Category', value: asset.categoryName ?? '—' },
            { label: 'Location', value: asset.locationName ?? '—' },
            { label: 'Department', value: asset.departmentName ?? '—' },
            { label: 'Status', value: asset.status.replace(/_/g, ' ') },
            { label: 'Total cost', value: asset.totalCost },
            { label: 'Accumulated depreciation', value: asset.accumulatedDepreciation },
            { label: 'WDV', value: asset.wdvValue },
          ]}
        />
      </CardContent>
    </Card>
  );

  function footer(isSubmitting: boolean): JSX.Element {
    return (
      <>
        <Button
          type="button"
          variant="outline"
          onClick={() => navigate(`/admin/fixed-assets/assets/${asset.id}`)}
        >
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {config.icon}
          <span className="ml-2">{isSubmitting ? 'Saving…' : config.title}</span>
        </Button>
      </>
    );
  }

  function renderActionForm(): JSX.Element {
    switch (action) {
      case 'capitalize':
        return (
          <Form {...capitalizeForm}>
            <form onSubmit={capitalizeForm.handleSubmit(handleCapitalize)}>
              <FormShell footer={footer(capitalizeForm.formState.isSubmitting)}>
                <FormSection
                  title="Capitalization Details"
                  description="Choose the capitalization and depreciation start dates."
                >
                  <FormField
                    control={capitalizeForm.control}
                    name="capitalizationDate"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Capitalization date</FormLabel>
                        <FormControl>
                          <DatePicker
                            date={toDate(field.value)}
                            onSelect={(value) => field.onChange(toIsoDate(value))}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={capitalizeForm.control}
                    name="putToUseDate"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Put-to-use date</FormLabel>
                        <FormControl>
                          <DatePicker
                            date={toDate(field.value)}
                            onSelect={(value) => field.onChange(toIsoDate(value))}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={capitalizeForm.control}
                    name="depreciationStartDate"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Depreciation start date</FormLabel>
                        <FormControl>
                          <DatePicker
                            date={toDate(field.value)}
                            onSelect={(value) => field.onChange(toIsoDate(value))}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={capitalizeForm.control}
                    name="remarks"
                    render={({ field }) => (
                      <FormItem className="md:col-span-2">
                        <FormLabel>Remarks</FormLabel>
                        <FormControl>
                          <Textarea {...field} rows={3} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </FormSection>
              </FormShell>
            </form>
          </Form>
        );

      case 'transfer':
        return (
          <Form {...transferForm}>
            <form onSubmit={transferForm.handleSubmit(handleTransfer)}>
              <FormShell footer={footer(transferForm.formState.isSubmitting)}>
                <FormSection
                  title="Transfer Details"
                  description="Capture where the asset is moving operationally."
                >
                  <FormField
                    control={transferForm.control}
                    name="transferDate"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Transfer date</FormLabel>
                        <FormControl>
                          <DatePicker
                            date={toDate(field.value)}
                            onSelect={(value) => field.onChange(toIsoDate(value))}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={transferForm.control}
                    name="toLocationId"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>To location</FormLabel>
                        <Select
                          value={field.value || 'NONE'}
                          onValueChange={(value) => field.onChange(value === 'NONE' ? '' : value)}
                        >
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="No location change" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="NONE">No location change</SelectItem>
                            {(unitsQuery.data ?? []).map((unit) => (
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
                    control={transferForm.control}
                    name="toDepartmentId"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>To department</FormLabel>
                        <Select
                          value={field.value || 'NONE'}
                          onValueChange={(value) => field.onChange(value === 'NONE' ? '' : value)}
                        >
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="No department change" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="NONE">No department change</SelectItem>
                            {(departmentsQuery.data ?? []).map((department) => (
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
                    control={transferForm.control}
                    name="reason"
                    render={({ field }) => (
                      <FormItem className="md:col-span-2">
                        <FormLabel>Reason</FormLabel>
                        <FormControl>
                          <Textarea {...field} rows={3} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </FormSection>
              </FormShell>
            </form>
          </Form>
        );

      case 'revalue':
        return (
          <Form {...revalueForm}>
            <form onSubmit={revalueForm.handleSubmit(handleRevalue)}>
              <FormShell footer={footer(revalueForm.formState.isSubmitting)}>
                <FormSection
                  title="Revaluation Details"
                  description="Enter the new recoverable value and valuation evidence."
                >
                  <FormField
                    control={revalueForm.control}
                    name="revaluationDate"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Revaluation date</FormLabel>
                        <FormControl>
                          <DatePicker
                            date={toDate(field.value)}
                            onSelect={(value) => field.onChange(toIsoDate(value))}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={revalueForm.control}
                    name="newValue"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>New value</FormLabel>
                        <FormControl>
                          <AmountInput value={field.value} onChange={field.onChange} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={revalueForm.control}
                    name="valuerName"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Valuer name</FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={revalueForm.control}
                    name="valuationReportNumber"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Report number</FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={revalueForm.control}
                    name="valuationReportDate"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Report date</FormLabel>
                        <FormControl>
                          <DatePicker
                            date={toDate(field.value)}
                            onSelect={(value) => field.onChange(toIsoDate(value))}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={revalueForm.control}
                    name="valuationMethod"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Valuation method</FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={revalueForm.control}
                    name="reason"
                    render={({ field }) => (
                      <FormItem className="md:col-span-2">
                        <FormLabel>Reason</FormLabel>
                        <FormControl>
                          <Textarea {...field} rows={3} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </FormSection>
              </FormShell>
            </form>
          </Form>
        );

      case 'impair':
        return (
          <Form {...impairForm}>
            <form onSubmit={impairForm.handleSubmit(handleImpair)}>
              <FormShell footer={footer(impairForm.formState.isSubmitting)}>
                <FormSection
                  title="Impairment Details"
                  description="Record the impairment amount and supporting reason."
                >
                  <FormField
                    control={impairForm.control}
                    name="impairmentDate"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Impairment date</FormLabel>
                        <FormControl>
                          <DatePicker
                            date={toDate(field.value)}
                            onSelect={(value) => field.onChange(toIsoDate(value))}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={impairForm.control}
                    name="impairmentAmount"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Impairment amount</FormLabel>
                        <FormControl>
                          <AmountInput value={field.value} onChange={field.onChange} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={impairForm.control}
                    name="reason"
                    render={({ field }) => (
                      <FormItem className="md:col-span-2">
                        <FormLabel>Reason</FormLabel>
                        <FormControl>
                          <Textarea {...field} rows={3} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </FormSection>
              </FormShell>
            </form>
          </Form>
        );

      case 'dispose':
        return (
          <Form {...disposeForm}>
            <form onSubmit={disposeForm.handleSubmit(handleDispose)}>
              <FormShell footer={footer(disposeForm.formState.isSubmitting)}>
                <FormSection
                  title="Disposal Details"
                  description="Capture the buyer, value, and remarks before routing approval if needed."
                >
                  <FormField
                    control={disposeForm.control}
                    name="disposalDate"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Disposal date</FormLabel>
                        <FormControl>
                          <DatePicker
                            date={toDate(field.value)}
                            onSelect={(value) => field.onChange(toIsoDate(value))}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={disposeForm.control}
                    name="disposalType"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Disposal type</FormLabel>
                        <Select value={field.value} onValueChange={field.onChange}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {disposalTypeOptions.map((option) => (
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
                    control={disposeForm.control}
                    name="disposalValue"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Disposal value</FormLabel>
                        <FormControl>
                          <AmountInput value={field.value} onChange={field.onChange} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={disposeForm.control}
                    name="buyerName"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Buyer / recipient</FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={disposeForm.control}
                    name="buyerAddress"
                    render={({ field }) => (
                      <FormItem className="md:col-span-2">
                        <FormLabel>Buyer address</FormLabel>
                        <FormControl>
                          <Textarea {...field} rows={3} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={disposeForm.control}
                    name="disposalRemarks"
                    render={({ field }) => (
                      <FormItem className="md:col-span-2">
                        <FormLabel>Remarks</FormLabel>
                        <FormControl>
                          <Textarea {...field} rows={3} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </FormSection>
              </FormShell>
            </form>
          </Form>
        );
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={config.title}
        subtitle={config.subtitle}
        breadcrumbs={[
          { label: 'Fixed Assets' },
          { label: 'Asset Register', to: '/admin/fixed-assets/assets' },
          { label: asset.assetCode, to: `/admin/fixed-assets/assets/${asset.id}` },
          { label: config.title },
        ]}
      />

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        {renderActionForm()}
        {summaryCard}
      </div>
    </div>
  );
}

function CardMessage({
  title,
  onBack,
}: {
  title: string;
  onBack: () => void;
}): JSX.Element {
  return (
    <div className="rounded-lg border bg-background p-8 text-center">
      <p className="text-sm text-muted-foreground">{title}</p>
      <Button type="button" variant="link" onClick={onBack}>
        Back to asset register
      </Button>
    </div>
  );
}
