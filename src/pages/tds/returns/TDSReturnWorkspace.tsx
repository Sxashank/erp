import { zodResolver } from '@hookform/resolvers/zod';
import { CheckCircle2, Download, FileWarning, Loader2, Pencil, Save, ShieldCheck, Wand2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useLocation, useNavigate, useParams } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { FormSection, FormShell } from '@/components/common/FormShell';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
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
  useCreateTDSReturn,
  useFinancialYears,
  useGenerateTDSReturnFile,
  useTDSReturn,
  useUpdateTDSReturn,
  useUpdateTDSReturnFilingDetails,
  useValidateTDSReturn,
  type TDSReturnInput,
} from '@/hooks/tax/useTaxation';
import {
  tdsReturnFilingSchema,
  tdsReturnSchema,
  type TDSReturnFilingFormInput,
  type TDSReturnFilingFormValues,
  type TDSReturnFormInput,
  type TDSReturnFormValues,
} from '@/schemas/tax/taxSchemas';
import { useActiveOrganizationId } from '@/stores/organizationStore';
import { getFinancialYearValue } from '@/utils/financialYears';

const defaultValues: TDSReturnFormValues = {
  organizationId: '',
  returnType: '26Q',
  financialYearId: '',
  financialYear: '',
  quarter: 'Q1',
  deductorTan: '',
  deductorName: '',
  deductorPan: '',
  deductorType: '',
  deductorCategory: '',
  deductorAddress: '',
  deductorCity: '',
  deductorState: '',
  deductorPincode: '',
  deductorEmail: '',
  deductorPhone: '',
  responsiblePersonName: '',
  responsiblePersonDesignation: '',
  responsiblePersonAddress: '',
  responsiblePersonPan: '',
  remarks: '',
};

const filingDefaults: TDSReturnFilingFormValues = {
  provisionalReceiptNumber: '',
  tokenNumber: '',
  acknowledgmentNumber: '',
  filedDate: '',
};

export default function TDSReturnWorkspace() {
  const navigate = useNavigate();
  const location = useLocation();
  const { id } = useParams();
  const activeOrganizationId = useActiveOrganizationId();
  const isEdit = Boolean(id) && location.pathname.endsWith('/edit');
  const isDetail = Boolean(id) && !isEdit;

  const returnQuery = useTDSReturn(id);
  const createReturn = useCreateTDSReturn();
  const updateReturn = useUpdateTDSReturn(id ?? '');
  const validateReturn = useValidateTDSReturn(id ?? '');
  const generateFile = useGenerateTDSReturnFile(id ?? '');
  const updateFilingDetails = useUpdateTDSReturnFilingDetails(id ?? '');

  const form = useForm<TDSReturnFormValues, unknown, TDSReturnFormInput>({
    resolver: zodResolver(tdsReturnSchema),
    defaultValues: { ...defaultValues ?? '' },
  });
  const filingForm = useForm<TDSReturnFilingFormValues, unknown, TDSReturnFilingFormInput>({
    resolver: zodResolver(tdsReturnFilingSchema),
    defaultValues: filingDefaults,
  });
  const organizationId = form.watch('organizationId');
  const financialYearsQuery = useFinancialYears();
  const [generatedFileContent, setGeneratedFileContent] = useState<string>('');
  const [generatedFileName, setGeneratedFileName] = useState<string>('');
  const [generatedFileNote, setGeneratedFileNote] = useState<string>('');

  useEffect(() => {
    if (activeOrganizationId && !id) {
      form.setValue('organizationId', activeOrganizationId);
    }
  }, [activeOrganizationId, form, id]);

  useEffect(() => {
    if (!returnQuery.data) return;
    form.reset({
      organizationId: returnQuery.data.organizationId,
      returnType: returnQuery.data.returnType as TDSReturnFormInput['returnType'],
      financialYearId: returnQuery.data.financialYearId,
      financialYear: returnQuery.data.financialYear,
      quarter: returnQuery.data.quarter as TDSReturnFormInput['quarter'],
      deductorTan: returnQuery.data.deductorTan,
      deductorName: returnQuery.data.deductorName,
      deductorPan: returnQuery.data.deductorPan ?? '',
      deductorType: returnQuery.data.deductorType ?? '',
      deductorCategory: returnQuery.data.deductorCategory ?? '',
      deductorAddress: returnQuery.data.deductorAddress ?? '',
      deductorCity: returnQuery.data.deductorCity ?? '',
      deductorState: returnQuery.data.deductorState ?? '',
      deductorPincode: returnQuery.data.deductorPincode ?? '',
      deductorEmail: returnQuery.data.deductorEmail ?? '',
      deductorPhone: returnQuery.data.deductorPhone ?? '',
      responsiblePersonName: returnQuery.data.responsiblePersonName ?? '',
      responsiblePersonDesignation: returnQuery.data.responsiblePersonDesignation ?? '',
      responsiblePersonAddress: returnQuery.data.responsiblePersonAddress ?? '',
      responsiblePersonPan: returnQuery.data.responsiblePersonPan ?? '',
      remarks: returnQuery.data.remarks ?? '',
    });
    filingForm.reset({
      provisionalReceiptNumber: returnQuery.data.provisionalReceiptNumber ?? '',
      tokenNumber: returnQuery.data.tokenNumber ?? '',
      acknowledgmentNumber: returnQuery.data.acknowledgmentNumber ?? '',
      filedDate: returnQuery.data.filedDate ?? '',
    });
  }, [filingForm, form, returnQuery.data]);

  const mutation = isEdit ? updateReturn : createReturn;
  const validationSummary = useMemo(() => returnQuery.data?.validationErrors ?? [], [returnQuery.data?.validationErrors]);

  async function onSubmit(values: TDSReturnFormInput) {
    const payload: TDSReturnInput = {
      ...values,
      deductorPan: values.deductorPan || undefined,
      deductorType: values.deductorType || undefined,
      deductorCategory: values.deductorCategory || undefined,
      deductorAddress: values.deductorAddress || undefined,
      deductorCity: values.deductorCity || undefined,
      deductorState: values.deductorState || undefined,
      deductorPincode: values.deductorPincode || undefined,
      deductorEmail: values.deductorEmail || undefined,
      deductorPhone: values.deductorPhone || undefined,
      responsiblePersonName: values.responsiblePersonName || undefined,
      responsiblePersonDesignation: values.responsiblePersonDesignation || undefined,
      responsiblePersonAddress: values.responsiblePersonAddress || undefined,
      responsiblePersonPan: values.responsiblePersonPan || undefined,
      remarks: values.remarks || undefined,
    };
    const savedReturn = await mutation.mutateAsync(payload);
    navigate(`/admin/tds/returns/${savedReturn.id}`);
  }

  async function handleValidate() {
    await validateReturn.mutateAsync();
    await returnQuery.refetch();
  }

  async function handleGenerateFile() {
    const result = await generateFile.mutateAsync();
    setGeneratedFileContent(result.fileContent);
    setGeneratedFileName(result.fileName);
    setGeneratedFileNote(result.complianceNote);
  }

  async function handleSaveFiling(values: TDSReturnFilingFormInput) {
    await updateFilingDetails.mutateAsync({
      provisionalReceiptNumber: values.provisionalReceiptNumber || undefined,
      tokenNumber: values.tokenNumber || undefined,
      acknowledgmentNumber: values.acknowledgmentNumber || undefined,
      filedDate: values.filedDate || undefined,
    });
    await returnQuery.refetch();
  }

  function handleDownloadFile() {
    if (!generatedFileContent || !generatedFileName) return;
    const blob = new Blob([generatedFileContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = generatedFileName;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isDetail ? 'TDS Return Workspace' : isEdit ? 'Edit TDS Return' : 'Create TDS Return'}
        subtitle="Prepare quarterly return data, validate totals, and capture filing evidence"
        breadcrumbs={[{ label: 'TDS Returns', to: '/admin/tds/returns' }]}
        actions={
          isDetail ? (
            <div className="flex items-center gap-2">
              <Badge variant="outline">{returnQuery.data?.status ?? 'DRAFT'}</Badge>
              <Button onClick={() => navigate(`/admin/tds/returns/${id}/edit`)}>
                <Pencil className="mr-2 h-4 w-4" />
                Edit Return
              </Button>
            </div>
          ) : undefined
        }
      />

      {mutation.error && <ErrorState error={mutation.error} />}
      {returnQuery.error && <ErrorState error={returnQuery.error} onRetry={() => returnQuery.refetch()} />}

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <FormShell
            footer={
              isDetail ? (
                <div className="flex flex-wrap gap-2">
                  <Button type="button" variant="outline" onClick={handleValidate} disabled={validateReturn.isPending} data-testid="tds-return-validate">
                    {validateReturn.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <ShieldCheck className="mr-2 h-4 w-4" />}
                    Validate Return
                  </Button>
                  <Button type="button" variant="outline" onClick={handleGenerateFile} disabled={generateFile.isPending} data-testid="tds-return-generate-file">
                    {generateFile.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Wand2 className="mr-2 h-4 w-4" />}
                    Generate File
                  </Button>
                  {generatedFileContent ? (
                    <Button type="button" onClick={handleDownloadFile} data-testid="tds-return-download-file">
                      <Download className="mr-2 h-4 w-4" />
                      Download {generatedFileName}
                    </Button>
                  ) : null}
                </div>
              ) : (
                <>
                  <Button type="button" variant="outline" onClick={() => navigate('/admin/tds/returns')}>Cancel</Button>
                  <Button type="submit" disabled={mutation.isPending}>
                    {mutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                    Save Return
                  </Button>
                </>
              )
            }
          >
            <FormSection title="Return Setup">
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
                  <Select disabled={Boolean(id)} value={field.value} onValueChange={(value) => {
                    field.onChange(value);
                    const year = financialYearsQuery.data?.items.find((item) => item.id === value);
                    form.setValue('financialYear', year ? getFinancialYearValue(year) : '');
                  }}>
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
              <FormField control={form.control} name="returnType" render={({ field }) => (
                <FormItem>
                  <FormLabel>Return type</FormLabel>
                  <Select disabled={Boolean(id)} value={field.value} onValueChange={field.onChange}>
                    <FormControl><SelectTrigger><SelectValue placeholder="Select return type" /></SelectTrigger></FormControl>
                    <SelectContent>
                      <SelectItem value="24Q">24Q Salary</SelectItem>
                      <SelectItem value="26Q">26Q Non-salary</SelectItem>
                      <SelectItem value="27Q">27Q NRI</SelectItem>
                      <SelectItem value="27EQ">27EQ TCS</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="quarter" render={({ field }) => (
                <FormItem>
                  <FormLabel>Quarter</FormLabel>
                  <Select disabled={Boolean(id)} value={field.value} onValueChange={field.onChange}>
                    <FormControl><SelectTrigger><SelectValue placeholder="Select quarter" /></SelectTrigger></FormControl>
                    <SelectContent>
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

            <FormSection title="Deductor Details">
              {['deductorTan', 'deductorName', 'deductorPan', 'deductorType', 'deductorCategory', 'deductorCity', 'deductorState', 'deductorPincode', 'deductorEmail', 'deductorPhone']
                .map((name) => (
                  <FormField
                    key={name}
                    control={form.control}
                    name={name as keyof TDSReturnFormInput}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>{name.replace(/([A-Z])/g, ' $1')}</FormLabel>
                        <FormControl><Input {...field} disabled={isDetail} /></FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                ))}
              <FormField control={form.control} name="deductorAddress" render={({ field }) => (
                <FormItem className="md:col-span-2">
                  <FormLabel>Deductor address</FormLabel>
                  <FormControl><Input {...field} disabled={isDetail} /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
            </FormSection>

            <FormSection title="Responsible Person">
              {['responsiblePersonName', 'responsiblePersonDesignation', 'responsiblePersonPan']
                .map((name) => (
                  <FormField
                    key={name}
                    control={form.control}
                    name={name as keyof TDSReturnFormInput}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>{name.replace(/([A-Z])/g, ' $1')}</FormLabel>
                        <FormControl><Input {...field} disabled={isDetail} /></FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                ))}
              <FormField control={form.control} name="responsiblePersonAddress" render={({ field }) => (
                <FormItem className="md:col-span-2">
                  <FormLabel>Responsible person address</FormLabel>
                  <FormControl><Input {...field} disabled={isDetail} /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={form.control} name="remarks" render={({ field }) => (
                <FormItem className="md:col-span-2">
                  <FormLabel>Remarks</FormLabel>
                  <FormControl><Input {...field} disabled={isDetail} /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
            </FormSection>
          </FormShell>
        </form>
      </Form>

      {id && returnQuery.data ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-lg border p-4">
            <div className="mb-3 flex items-center gap-2 font-medium">
              <CheckCircle2 className="h-4 w-4" />
              Validation Summary
            </div>
            <p className="text-sm text-muted-foreground">Status: {returnQuery.data.status}</p>
            <p className="text-sm text-muted-foreground">Total challans: {returnQuery.data.totalChallans}</p>
            <p className="text-sm text-muted-foreground">Total deductees: {returnQuery.data.totalDeductees}</p>
            {validationSummary.length === 0 ? (
              <p className="mt-3 text-sm">No blocking validation errors captured.</p>
            ) : (
              <ul className="mt-3 space-y-2 text-sm">
                {validationSummary.map((error) => (
                  <li key={`${error.code}-${error.message}`} className="flex gap-2">
                    <FileWarning className="mt-0.5 h-4 w-4 text-amber-600" />
                    <span>{error.message}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="rounded-lg border p-4">
            <div className="mb-3 flex items-center gap-2 font-medium">
              <Download className="h-4 w-4" />
              Filing Evidence
            </div>
            {generatedFileNote ? (
              <p className="mb-4 text-sm text-muted-foreground">{generatedFileNote}</p>
            ) : null}
            <Form {...filingForm}>
              <form onSubmit={filingForm.handleSubmit(handleSaveFiling)} className="space-y-4">
                {['provisionalReceiptNumber', 'tokenNumber', 'acknowledgmentNumber', 'filedDate'].map((name) => (
                  <FormField
                    key={name}
                    control={filingForm.control}
                    name={name as keyof TDSReturnFilingFormInput}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>{name.replace(/([A-Z])/g, ' $1')}</FormLabel>
                        <FormControl><Input {...field} type={name === 'filedDate' ? 'date' : 'text'} /></FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                ))}
                <Button type="submit" disabled={updateFilingDetails.isPending} data-testid="tds-return-save-filing">
                  {updateFilingDetails.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                  Save Filing Details
                </Button>
              </form>
            </Form>
          </div>
        </div>
      ) : null}
    </div>
  );
}
