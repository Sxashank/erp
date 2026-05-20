import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, Pencil, Save } from 'lucide-react';
import { useEffect } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { useLocation, useNavigate, useParams } from 'react-router-dom';

import { AmountDisplay } from '@/components/common/AmountDisplay';
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
  useCreateTDSEntry,
  useFinancialYears,
  useTDSEntry,
  useTDSSections,
  useUpdateTDSEntry,
  useValidateTDSThreshold,
  type TDSEntryInput,
} from '@/hooks/tax/useTaxation';
import { tdsEntrySchema, type TDSEntryFormInput, type TDSEntryFormValues } from '@/schemas/tax/taxSchemas';
import { useActiveOrganizationId } from '@/stores/organizationStore';

const defaultValues: TDSEntryFormValues = {
  organizationId: '',
  tdsSectionId: '',
  financialYearId: '',
  voucherId: '',
  vendorId: '',
  deducteeName: '',
  deducteePan: '',
  deducteeType: 'COMPANY',
  deducteeAddress: '',
  deductionDate: new Date().toISOString().slice(0, 10),
  baseAmount: 0,
  tdsRate: 0,
  tdsAmount: 0,
  surcharge: 0,
  cess: 0,
  totalTds: 0,
  lowerDeductionCertNo: '',
  remarks: '',
  challanStatus: 'PENDING',
  challanNumber: '',
  challanDate: '',
  bankName: '',
  bsrCode: '',
  certificateNumber: '',
  certificateDate: '',
  returnQuarter: undefined,
  returnFiled: false,
  acknowledgmentNumber: '',
  isActive: true,
};

const deducteeTypes = ['INDIVIDUAL', 'COMPANY', 'FIRM', 'HUF', 'AOP', 'TRUST', 'GOVERNMENT', 'OTHER'];
const NO_FINANCIAL_YEAR_VALUE = '__no-financial-year__';
const NO_RETURN_QUARTER_VALUE = '__no-return-quarter__';

function getInputValue(value: unknown): string | number {
  return typeof value === 'string' || typeof value === 'number' ? value : '';
}

function toNumberValue(value: string): number {
  return value === '' ? 0 : Number(value);
}

export function TDSEntryForm() {
  const navigate = useNavigate();
  const location = useLocation();
  const { id } = useParams();
  const activeOrganizationId = useActiveOrganizationId();
  const isEdit = Boolean(id) && location.pathname.endsWith('/edit');
  const isDetail = Boolean(id) && !isEdit;

  const entryQuery = useTDSEntry(id);
  const sectionsQuery = useTDSSections({ pageSize: 100, includeInactive: false });
  const createEntry = useCreateTDSEntry();
  const updateEntry = useUpdateTDSEntry(id ?? '');
  const validateThreshold = useValidateTDSThreshold();

  const form = useForm<TDSEntryFormValues, unknown, TDSEntryFormInput>({
    resolver: zodResolver(tdsEntrySchema),
    defaultValues: {
      ...defaultValues ?? '',
    },
  });

  const organizationId = form.watch('organizationId');
  const financialYearsQuery = useFinancialYears();
  const selectedSectionId = form.watch('tdsSectionId');
  const [baseAmount, tdsRate, surcharge, cess] = useWatch({
    control: form.control,
    name: ['baseAmount', 'tdsRate', 'surcharge', 'cess'],
  });
  const selectedSection = sectionsQuery.data?.items.find((section) => section.id === selectedSectionId);
  const thresholdPreview = validateThreshold.data;

  useEffect(() => {
    if (activeOrganizationId && !id) {
      form.setValue('organizationId', activeOrganizationId);
    }
  }, [activeOrganizationId, form, id]);

  useEffect(() => {
    if (!entryQuery.data) return;
    form.reset({
      organizationId: entryQuery.data.organizationId,
      tdsSectionId: entryQuery.data.tdsSectionId,
      financialYearId: entryQuery.data.financialYearId ?? '',
      voucherId: entryQuery.data.voucherId ?? '',
      vendorId: entryQuery.data.vendorId ?? '',
      deducteeName: entryQuery.data.deducteeName,
      deducteePan: entryQuery.data.deducteePan ?? '',
      deducteeType: entryQuery.data.deducteeType as TDSEntryFormInput['deducteeType'],
      deducteeAddress: entryQuery.data.deducteeAddress ?? '',
      deductionDate: entryQuery.data.deductionDate,
      baseAmount: entryQuery.data.baseAmount,
      tdsRate: entryQuery.data.tdsRate,
      tdsAmount: entryQuery.data.tdsAmount,
      surcharge: entryQuery.data.surcharge,
      cess: entryQuery.data.cess,
      totalTds: entryQuery.data.totalTds,
      lowerDeductionCertNo: entryQuery.data.lowerDeductionCertNo ?? '',
      remarks: entryQuery.data.remarks ?? '',
      challanStatus: entryQuery.data.challanStatus as TDSEntryFormInput['challanStatus'],
      challanNumber: entryQuery.data.challanNumber ?? '',
      challanDate: entryQuery.data.challanDate ?? '',
      bankName: entryQuery.data.bankName ?? '',
      bsrCode: entryQuery.data.bsrCode ?? '',
      certificateNumber: entryQuery.data.certificateNumber ?? '',
      certificateDate: entryQuery.data.certificateDate ?? '',
      returnQuarter: entryQuery.data.returnQuarter as TDSEntryFormInput['returnQuarter'],
      returnFiled: entryQuery.data.returnFiled,
      acknowledgmentNumber: entryQuery.data.acknowledgmentNumber ?? '',
      isActive: entryQuery.data.isActive,
    });
  }, [entryQuery.data, form]);

  useEffect(() => {
    if (selectedSection && !id) {
      form.setValue('tdsRate', Number(selectedSection.rateCompany));
    }
  }, [form, id, selectedSection]);

  useEffect(() => {
    const computedBaseAmount = Number(baseAmount || 0);
    const computedTdsRate = Number(tdsRate || 0);
    const computedSurcharge = Number(surcharge || 0);
    const computedCess = Number(cess || 0);
    const tdsAmount = Number(((computedBaseAmount * computedTdsRate) / 100).toFixed(2));
    const totalTds = Number((tdsAmount + computedSurcharge + computedCess).toFixed(2));
    form.setValue('tdsAmount', tdsAmount);
    form.setValue('totalTds', totalTds);
  }, [baseAmount, cess, form, surcharge, tdsRate]);

  const mutation = isEdit ? updateEntry : createEntry;

  async function onPreviewThreshold() {
    const values = form.getValues();
    if (!values.organizationId || !values.tdsSectionId) return;
    await validateThreshold.mutateAsync({
      organizationId: values.organizationId,
      vendorId: values.vendorId || undefined,
      tdsSectionId: values.tdsSectionId,
      baseAmount: Number(values.baseAmount ?? 0),
      deductionDate: values.deductionDate,
      deducteeType: values.deducteeType,
      deducteePan: values.deducteePan || undefined,
    });
  }

  async function onSubmit(values: TDSEntryFormInput) {
    const payload: TDSEntryInput = {
      ...values,
      financialYearId: values.financialYearId || undefined,
      voucherId: values.voucherId || undefined,
      vendorId: values.vendorId || undefined,
      deducteePan: values.deducteePan || undefined,
      deducteeAddress: values.deducteeAddress || undefined,
      lowerDeductionCertNo: values.lowerDeductionCertNo || undefined,
      remarks: values.remarks || undefined,
      challanNumber: values.challanNumber || undefined,
      challanDate: values.challanDate || undefined,
      bankName: values.bankName || undefined,
      bsrCode: values.bsrCode || undefined,
      certificateNumber: values.certificateNumber || undefined,
      certificateDate: values.certificateDate || undefined,
      returnQuarter: values.returnQuarter || undefined,
      acknowledgmentNumber: values.acknowledgmentNumber || undefined,
    };
    await mutation.mutateAsync(payload);
    navigate('/admin/tds/entries');
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isDetail ? 'TDS Entry Details' : isEdit ? 'Edit TDS Entry' : 'Add TDS Entry'}
        subtitle="Capture deductee-level deduction details used in challans and quarterly returns"
        breadcrumbs={[{ label: 'TDS Entries', to: '/admin/tds/entries' }]}
        actions={isDetail ? <Button onClick={() => navigate(`/admin/tds/entries/${id}/edit`)}><Pencil className="mr-2 h-4 w-4" />Edit Entry</Button> : undefined}
      />

      {mutation.error && <ErrorState error={mutation.error} />}
      {entryQuery.error && <ErrorState error={entryQuery.error} onRetry={() => entryQuery.refetch()} />}

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <FormShell
            footer={
              isDetail ? (
                <Button type="button" variant="outline" onClick={() => navigate('/admin/tds/entries')}>Back</Button>
              ) : (
                <>
                  <Button type="button" variant="outline" onClick={onPreviewThreshold} disabled={validateThreshold.isPending}>
                    {validateThreshold.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                    Preview Threshold
                  </Button>
                  <Button type="button" variant="outline" onClick={() => navigate('/admin/tds/entries')}>Cancel</Button>
                  <Button type="submit" disabled={mutation.isPending}>
                    {mutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                    Save Entry
                  </Button>
                </>
              )
            }
          >
            <FormSection title="Deductee And Tax Setup">
              <FormField control={form.control} name="organizationId" render={({ field }) => (
                <FormItem>
                  <FormLabel>Organization</FormLabel>
                  <FormControl><Input {...field} disabled /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="financialYearId" render={({ field }) => (
                <FormItem>
                  <FormLabel>Financial year</FormLabel>
                  <Select
                    disabled={isDetail}
                    value={field.value || NO_FINANCIAL_YEAR_VALUE}
                    onValueChange={(value) => field.onChange(value === NO_FINANCIAL_YEAR_VALUE ? '' : value)}
                  >
                    <FormControl><SelectTrigger><SelectValue placeholder="Select financial year" /></SelectTrigger></FormControl>
                    <SelectContent>
                      <SelectItem value={NO_FINANCIAL_YEAR_VALUE}>No financial year</SelectItem>
                      {(financialYearsQuery.data?.items ?? []).map((year) => (
                        <SelectItem key={year.id} value={year.id}>{year.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="tdsSectionId" render={({ field }) => (
                <FormItem>
                  <FormLabel>TDS section</FormLabel>
                  <Select disabled={isDetail} value={field.value} onValueChange={field.onChange}>
                    <FormControl><SelectTrigger><SelectValue placeholder="Select section" /></SelectTrigger></FormControl>
                    <SelectContent>
                      {(sectionsQuery.data?.items ?? []).map((section) => (
                        <SelectItem key={section.id} value={section.id}>{section.sectionCode} · {section.sectionName}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="deducteeType" render={({ field }) => (
                <FormItem>
                  <FormLabel>Deductee type</FormLabel>
                  <Select disabled={isDetail} value={field.value} onValueChange={field.onChange}>
                    <FormControl><SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger></FormControl>
                    <SelectContent>
                      {deducteeTypes.map((type) => (
                        <SelectItem key={type} value={type}>{type}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="deducteeName" render={({ field }) => (
                <FormItem>
                  <FormLabel>Deductee name</FormLabel>
                  <FormControl><Input {...field} disabled={isDetail} placeholder="Deductee name" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="deducteePan" render={({ field }) => (
                <FormItem>
                  <FormLabel>Deductee PAN</FormLabel>
                  <FormControl><Input {...field} disabled={isDetail} placeholder="ABCDE1234F" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
            </FormSection>

            <FormSection title="Deduction Values">
              <FormField control={form.control} name="deductionDate" render={({ field }) => (
                <FormItem>
                  <FormLabel>Deduction date</FormLabel>
                  <FormControl><Input {...field} disabled={isDetail} type="date" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="baseAmount" render={({ field }) => (
                <FormItem>
                  <FormLabel>Base amount</FormLabel>
                  <FormControl><Input {...field} value={getInputValue(field.value)} onChange={(event) => field.onChange(toNumberValue(event.target.value))} disabled={isDetail} type="number" step="0.01" min="0" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="tdsRate" render={({ field }) => (
                <FormItem>
                  <FormLabel>TDS rate</FormLabel>
                  <FormControl><Input {...field} value={getInputValue(field.value)} onChange={(event) => field.onChange(toNumberValue(event.target.value))} disabled={isDetail} type="number" step="0.01" min="0" max="100" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="tdsAmount" render={({ field }) => (
                <FormItem>
                  <FormLabel>TDS amount</FormLabel>
                  <FormControl><Input {...field} value={getInputValue(field.value)} onChange={(event) => field.onChange(toNumberValue(event.target.value))} disabled type="number" step="0.01" min="0" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="surcharge" render={({ field }) => (
                <FormItem>
                  <FormLabel>Surcharge</FormLabel>
                  <FormControl><Input {...field} value={getInputValue(field.value)} onChange={(event) => field.onChange(toNumberValue(event.target.value))} disabled={isDetail} type="number" step="0.01" min="0" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="cess" render={({ field }) => (
                <FormItem>
                  <FormLabel>Cess</FormLabel>
                  <FormControl><Input {...field} value={getInputValue(field.value)} onChange={(event) => field.onChange(toNumberValue(event.target.value))} disabled={isDetail} type="number" step="0.01" min="0" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="totalTds" render={({ field }) => (
                <FormItem>
                  <FormLabel>Total TDS</FormLabel>
                  <FormControl><Input {...field} value={getInputValue(field.value)} onChange={(event) => field.onChange(toNumberValue(event.target.value))} disabled type="number" step="0.01" min="0" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="lowerDeductionCertNo" render={({ field }) => (
                <FormItem>
                  <FormLabel>Lower deduction certificate</FormLabel>
                  <FormControl><Input {...field} disabled={isDetail} placeholder="Optional" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
            </FormSection>

            <FormSection title="Operational Status">
              <FormField control={form.control} name="challanStatus" render={({ field }) => (
                <FormItem>
                  <FormLabel>Challan status</FormLabel>
                  <Select disabled={isDetail} value={field.value} onValueChange={field.onChange}>
                    <FormControl><SelectTrigger><SelectValue placeholder="Select status" /></SelectTrigger></FormControl>
                    <SelectContent>
                      <SelectItem value="PENDING">Pending</SelectItem>
                      <SelectItem value="PAID">Paid</SelectItem>
                      <SelectItem value="VERIFIED">Verified</SelectItem>
                      <SelectItem value="NOT_APPLICABLE">Not applicable</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="challanNumber" render={({ field }) => (
                <FormItem>
                  <FormLabel>Challan number</FormLabel>
                  <FormControl><Input {...field} disabled={isDetail} placeholder="Optional" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="challanDate" render={({ field }) => (
                <FormItem>
                  <FormLabel>Challan date</FormLabel>
                  <FormControl><Input {...field} disabled={isDetail} type="date" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="bankName" render={({ field }) => (
                <FormItem>
                  <FormLabel>Bank name</FormLabel>
                  <FormControl><Input {...field} disabled={isDetail} placeholder="Optional" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="bsrCode" render={({ field }) => (
                <FormItem>
                  <FormLabel>BSR code</FormLabel>
                  <FormControl><Input {...field} disabled={isDetail} placeholder="Optional" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="returnQuarter" render={({ field }) => (
                <FormItem>
                  <FormLabel>Return quarter</FormLabel>
                  <Select
                    disabled={isDetail}
                    value={field.value || NO_RETURN_QUARTER_VALUE}
                    onValueChange={(value) => field.onChange(value === NO_RETURN_QUARTER_VALUE ? undefined : value)}
                  >
                    <FormControl><SelectTrigger><SelectValue placeholder="Optional" /></SelectTrigger></FormControl>
                    <SelectContent>
                      <SelectItem value={NO_RETURN_QUARTER_VALUE}>Not assigned</SelectItem>
                      <SelectItem value="Q1">Q1</SelectItem>
                      <SelectItem value="Q2">Q2</SelectItem>
                      <SelectItem value="Q3">Q3</SelectItem>
                      <SelectItem value="Q4">Q4</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="returnFiled" render={({ field }) => (
                <FormItem className="flex items-center gap-2 space-y-0">
                  <FormControl><Checkbox disabled={isDetail} checked={field.value} onCheckedChange={field.onChange} /></FormControl>
                  <FormLabel>Included in filed return</FormLabel>
                  <FormMessage />
                </FormItem>
              )} />
            </FormSection>
          </FormShell>
        </form>
      </Form>

      {thresholdPreview && (
        <div className="rounded-lg border bg-muted/20 p-4 text-sm">
          <p className="font-medium">Threshold preview</p>
          <p>Applicable: {thresholdPreview.tdsApplicable ? 'Yes' : 'No'} · Reason: {thresholdPreview.reason}</p>
          <p>Current aggregate: <AmountDisplay amount={thresholdPreview.currentAggregate} /> · New aggregate: <AmountDisplay amount={thresholdPreview.newAggregate} /></p>
          <p>Estimated total TDS: <AmountDisplay amount={thresholdPreview.estimatedTotalTds} /></p>
        </div>
      )}
    </div>
  );
}
