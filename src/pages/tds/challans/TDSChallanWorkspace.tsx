import { zodResolver } from '@hookform/resolvers/zod';
import { CheckCircle2, Loader2, Pencil, Save, ShieldCheck, Wallet } from 'lucide-react';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useLocation, useNavigate, useParams } from 'react-router-dom';

import { AmountDisplay } from '@/components/common/AmountDisplay';
import { ErrorState } from '@/components/common/ErrorState';
import { FormSection, FormShell } from '@/components/common/FormShell';
import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
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
  useCreateTDSChallan,
  useFinalizeTDSChallan,
  useFinancialYears,
  useRecordTDSChallanPayment,
  useTDSChallan,
  useTDSEntries,
  useTDSSections,
  useUpdateTDSChallan,
  useVerifyTDSChallanOLTAS,
  type TDSChallanInput,
} from '@/hooks/tax/useTaxation';
import {
  tdsChallanOltasSchema,
  tdsChallanPaymentSchema,
  tdsChallanSchema,
  type TDSChallanFormInput,
  type TDSChallanFormValues,
  type TDSChallanOltasFormInput,
  type TDSChallanOltasFormValues,
  type TDSChallanPaymentFormInput,
  type TDSChallanPaymentFormValues,
} from '@/schemas/tax/taxSchemas';
import { useActiveOrganizationId } from '@/stores/organizationStore';

const defaultValues: TDSChallanFormValues = {
  organizationId: '',
  tdsSectionId: '',
  financialYearId: '',
  assessmentYear: '',
  periodFrom: new Date().toISOString().slice(0, 10),
  periodTo: new Date().toISOString().slice(0, 10),
  challanType: '281',
  minorHead: '',
  deductorTan: '',
  deductorName: '',
  deductorAddress: '',
  returnQuarter: undefined,
  entryIds: [],
  interestAmount: 0,
  penaltyAmount: 0,
  otherAmount: 0,
  remarks: '',
};

const paymentDefaults: TDSChallanPaymentFormValues = {
  challanNumber: '',
  bsrCode: '',
  serialNumber: '',
  paymentDate: new Date().toISOString().slice(0, 10),
  paymentMode: 'ONLINE',
  bankName: '',
  bankBranch: '',
  bankAccountNumber: '',
  chequeDdNumber: '',
  chequeDdDate: '',
};

const oltasDefaults: TDSChallanOltasFormValues = {
  oltasAcknowledgment: '',
  oltasStatus: '',
  oltasVerifiedAt: new Date().toISOString().slice(0, 10),
};
const NO_RETURN_QUARTER_VALUE = '__no-return-quarter__';

function getInputValue(value: unknown): string | number {
  return typeof value === 'string' || typeof value === 'number' ? value : '';
}

function toNumberValue(value: string): number {
  return value === '' ? 0 : Number(value);
}

export default function TDSChallanWorkspace() {
  const navigate = useNavigate();
  const location = useLocation();
  const { id } = useParams();
  const activeOrganizationId = useActiveOrganizationId();
  const isEdit = Boolean(id) && location.pathname.endsWith('/edit');
  const isDetail = Boolean(id) && !isEdit;

  const challanQuery = useTDSChallan(id);
  const createChallan = useCreateTDSChallan();
  const updateChallan = useUpdateTDSChallan(id ?? '');
  const finalizeChallan = useFinalizeTDSChallan(id ?? '');
  const recordPayment = useRecordTDSChallanPayment(id ?? '');
  const verifyOltas = useVerifyTDSChallanOLTAS(id ?? '');

  const form = useForm<TDSChallanFormValues, unknown, TDSChallanFormInput>({
    resolver: zodResolver(tdsChallanSchema),
    defaultValues: { ...defaultValues, organizationId: activeOrganizationId ?? '' },
  });
  const paymentForm = useForm<TDSChallanPaymentFormValues, unknown, TDSChallanPaymentFormInput>({
    resolver: zodResolver(tdsChallanPaymentSchema),
    defaultValues: paymentDefaults,
  });
  const oltasForm = useForm<TDSChallanOltasFormValues, unknown, TDSChallanOltasFormInput>({
    resolver: zodResolver(tdsChallanOltasSchema),
    defaultValues: oltasDefaults,
  });

  const organizationId = form.watch('organizationId');
  const sectionsQuery = useTDSSections({ pageSize: 100, includeInactive: false });
  const financialYearsQuery = useFinancialYears(organizationId || activeOrganizationId || undefined);
  const entriesQuery = useTDSEntries({ organizationId: organizationId || activeOrganizationId || undefined, challanStatus: 'PENDING', pageSize: 100 });
  const selectedEntryIds = form.watch('entryIds') || [];

  useEffect(() => {
    if (activeOrganizationId && !id) {
      form.setValue('organizationId', activeOrganizationId);
    }
  }, [activeOrganizationId, form, id]);

  useEffect(() => {
    if (!challanQuery.data) return;
    form.reset({
      organizationId: challanQuery.data.organizationId,
      tdsSectionId: challanQuery.data.tdsSectionId,
      financialYearId: challanQuery.data.financialYearId,
      assessmentYear: challanQuery.data.assessmentYear,
      periodFrom: challanQuery.data.periodFrom,
      periodTo: challanQuery.data.periodTo,
      challanType: challanQuery.data.challanType as '281',
      minorHead: challanQuery.data.minorHead ?? '',
      deductorTan: challanQuery.data.deductorTan,
      deductorName: challanQuery.data.deductorName,
      deductorAddress: challanQuery.data.deductorAddress ?? '',
      returnQuarter: challanQuery.data.returnQuarter as TDSChallanFormInput['returnQuarter'],
      entryIds: challanQuery.data.entries?.map((entry) => entry.id) ?? [],
      interestAmount: challanQuery.data.interestAmount,
      penaltyAmount: challanQuery.data.penaltyAmount,
      otherAmount: challanQuery.data.otherAmount,
      remarks: challanQuery.data.remarks ?? '',
    });
    paymentForm.reset({
      challanNumber: challanQuery.data.challanNumber ?? '',
      bsrCode: challanQuery.data.bsrCode ?? '',
      serialNumber: challanQuery.data.serialNumber ?? '',
      paymentDate: challanQuery.data.paymentDate ?? paymentDefaults.paymentDate,
      paymentMode: (challanQuery.data.paymentMode as TDSChallanPaymentFormInput['paymentMode']) || 'ONLINE',
      bankName: challanQuery.data.bankName ?? '',
      bankBranch: challanQuery.data.bankBranch ?? '',
      bankAccountNumber: challanQuery.data.bankAccountNumber ?? '',
      chequeDdNumber: challanQuery.data.chequeDdNumber ?? '',
      chequeDdDate: challanQuery.data.chequeDdDate ?? '',
    });
    oltasForm.reset({
      oltasAcknowledgment: challanQuery.data.oltasAcknowledgment ?? '',
      oltasStatus: challanQuery.data.oltasStatus ?? '',
      oltasVerifiedAt: challanQuery.data.oltasVerifiedAt ?? oltasDefaults.oltasVerifiedAt,
    });
  }, [challanQuery.data, form, oltasForm, paymentForm]);

  const mutation = isEdit ? updateChallan : createChallan;

  async function onSubmit(values: TDSChallanFormInput) {
    const payload: TDSChallanInput = {
      ...values,
      minorHead: values.minorHead || undefined,
      deductorAddress: values.deductorAddress || undefined,
      returnQuarter: values.returnQuarter || undefined,
      remarks: values.remarks || undefined,
    };
    const savedChallan = await mutation.mutateAsync(payload);
    navigate(`/admin/tds/challans/${savedChallan.id}`);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isDetail ? 'TDS Challan Workspace' : isEdit ? 'Edit TDS Challan' : 'Create TDS Challan'}
        subtitle="Aggregate deductions, finalize challan, capture payment and OLTAS verification"
        breadcrumbs={[{ label: 'TDS Challans', to: '/admin/tds/challans' }]}
        actions={isDetail ? <Button onClick={() => navigate(`/admin/tds/challans/${id}/edit`)}><Pencil className="mr-2 h-4 w-4" />Edit Challan</Button> : undefined}
      />

      {mutation.error && <ErrorState error={mutation.error} />}
      {challanQuery.error && <ErrorState error={challanQuery.error} onRetry={() => challanQuery.refetch()} />}

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <FormShell
            footer={
              isDetail ? (
                <div className="flex flex-wrap gap-2">
                  <Button type="button" variant="outline" onClick={() => finalizeChallan.mutateAsync()} disabled={finalizeChallan.isPending}>
                    {finalizeChallan.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <ShieldCheck className="mr-2 h-4 w-4" />}
                    Finalize Challan
                  </Button>
                </div>
              ) : (
                <>
                  <Button type="button" variant="outline" onClick={() => navigate('/admin/tds/challans')}>Cancel</Button>
                  <Button type="submit" disabled={mutation.isPending}>
                    {mutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                    Save Challan
                  </Button>
                </>
              )
            }
          >
            <FormSection title="Challan Setup">
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
                  <Select disabled={Boolean(id)} value={field.value} onValueChange={field.onChange}>
                    <FormControl><SelectTrigger><SelectValue placeholder="Select financial year" /></SelectTrigger></FormControl>
                    <SelectContent>
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
                  <Select disabled={Boolean(id)} value={field.value} onValueChange={field.onChange}>
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
              <FormField control={form.control} name="assessmentYear" render={({ field }) => (
                <FormItem>
                  <FormLabel>Assessment year</FormLabel>
                  <FormControl><Input {...field} disabled={isDetail} placeholder="2026-27" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="periodFrom" render={({ field }) => (
                <FormItem>
                  <FormLabel>Period from</FormLabel>
                  <FormControl><Input {...field} disabled={isDetail} type="date" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="periodTo" render={({ field }) => (
                <FormItem>
                  <FormLabel>Period to</FormLabel>
                  <FormControl><Input {...field} disabled={isDetail} type="date" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="minorHead" render={({ field }) => (
                <FormItem>
                  <FormLabel>Minor head</FormLabel>
                  <FormControl><Input {...field} disabled={isDetail} placeholder="200 / 400" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
            </FormSection>

            <FormSection title="Deductor And Amounts">
              <FormField control={form.control} name="deductorTan" render={({ field }) => (
                <FormItem>
                  <FormLabel>Deductor tan</FormLabel>
                  <FormControl><Input {...field} value={field.value || ''} disabled={isDetail} /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="deductorName" render={({ field }) => (
                <FormItem>
                  <FormLabel>Deductor name</FormLabel>
                  <FormControl><Input {...field} value={field.value || ''} disabled={isDetail} /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="deductorAddress" render={({ field }) => (
                <FormItem>
                  <FormLabel>Deductor address</FormLabel>
                  <FormControl><Input {...field} value={field.value || ''} disabled={isDetail} /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="interestAmount" render={({ field }) => (
                <FormItem>
                  <FormLabel>Interest amount</FormLabel>
                  <FormControl><Input {...field} value={getInputValue(field.value)} onChange={(event) => field.onChange(toNumberValue(event.target.value))} disabled={isDetail} type="number" step="0.01" min="0" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="penaltyAmount" render={({ field }) => (
                <FormItem>
                  <FormLabel>Penalty amount</FormLabel>
                  <FormControl><Input {...field} value={getInputValue(field.value)} onChange={(event) => field.onChange(toNumberValue(event.target.value))} disabled={isDetail} type="number" step="0.01" min="0" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="otherAmount" render={({ field }) => (
                <FormItem>
                  <FormLabel>Other amount</FormLabel>
                  <FormControl><Input {...field} value={getInputValue(field.value)} onChange={(event) => field.onChange(toNumberValue(event.target.value))} disabled={isDetail} type="number" step="0.01" min="0" /></FormControl>
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
            </FormSection>

            <FormSection title="Pending Entries">
              <div className="md:col-span-2 rounded-lg border p-4">
                <div className="mb-2 text-sm font-medium">Available entries for aggregation</div>
                <div className="max-h-56 space-y-2 overflow-y-auto">
                  {(entriesQuery.data?.items ?? []).map((entry) => {
                    const selected = selectedEntryIds.includes(entry.id);
                    return (
                      <label key={entry.id} className="flex items-center justify-between gap-3 rounded border px-3 py-2 text-sm">
                        <span>{entry.deducteeName} · {entry.tdsSectionCode} · <AmountDisplay amount={entry.totalTds} /></span>
                        <input
                          type="checkbox"
                          disabled={isDetail}
                          checked={selected}
                          onChange={(event) => {
                            const current = form.getValues('entryIds') || [];
                            form.setValue(
                              'entryIds',
                              event.target.checked ? [...current, entry.id] : current.filter((item) => item !== entry.id),
                            );
                          }}
                        />
                      </label>
                    );
                  })}
                </div>
              </div>
            </FormSection>
          </FormShell>
        </form>
      </Form>

      {id ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-lg border p-4">
            <div className="mb-3 flex items-center gap-2 font-medium"><Wallet className="h-4 w-4" />Payment Details</div>
            <Form {...paymentForm}>
              <form onSubmit={paymentForm.handleSubmit((values) => recordPayment.mutateAsync(values))} className="space-y-4">
                {['challanNumber', 'bsrCode', 'serialNumber', 'paymentDate', 'paymentMode', 'bankName', 'bankBranch', 'bankAccountNumber', 'chequeDdNumber', 'chequeDdDate'].map((name) => (
                  <FormField key={name} control={paymentForm.control} name={name as keyof TDSChallanPaymentFormInput} render={({ field }) => (
                    <FormItem>
                      <FormLabel>{name.replace(/([A-Z])/g, ' $1')}</FormLabel>
                      <FormControl><Input {...field} type={name.toLowerCase().includes('date') ? 'date' : 'text'} /></FormControl>
                      <FormMessage />
                    </FormItem>
                  )} />
                ))}
                <Button type="submit" disabled={recordPayment.isPending} data-testid="tds-challan-save-payment">
                  {recordPayment.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                  Save Payment
                </Button>
              </form>
            </Form>
          </div>
          <div className="rounded-lg border p-4">
            <div className="mb-3 flex items-center gap-2 font-medium"><CheckCircle2 className="h-4 w-4" />OLTAS Verification</div>
            <Form {...oltasForm}>
              <form onSubmit={oltasForm.handleSubmit((values) => verifyOltas.mutateAsync(values))} className="space-y-4">
                {['oltasAcknowledgment', 'oltasStatus', 'oltasVerifiedAt'].map((name) => (
                  <FormField key={name} control={oltasForm.control} name={name as keyof TDSChallanOltasFormInput} render={({ field }) => (
                    <FormItem>
                      <FormLabel>{name.replace(/([A-Z])/g, ' $1')}</FormLabel>
                      <FormControl><Input {...field} type={name === 'oltasVerifiedAt' ? 'date' : 'text'} /></FormControl>
                      <FormMessage />
                    </FormItem>
                  )} />
                ))}
                <Button type="submit" disabled={verifyOltas.isPending} data-testid="tds-challan-save-oltas">
                  {verifyOltas.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <ShieldCheck className="mr-2 h-4 w-4" />}
                  Save OLTAS Status
                </Button>
              </form>
            </Form>
          </div>
        </div>
      ) : null}
    </div>
  );
}
