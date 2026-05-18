import { zodResolver } from '@hookform/resolvers/zod';
import { CheckCircle2, Download, Loader2, Save } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';

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
  useFinancialYears,
  useGenerateBulkTDSCertificates,
  useGenerateTDSCertificate,
  useTDSCertificate,
  useTDSCertificateCandidates,
} from '@/hooks/tax/useTaxation';
import {
  tdsCertificateSchema,
  type TDSCertificateFormInput,
  type TDSCertificateFormValues,
} from '@/schemas/tax/taxSchemas';
import { useActiveOrganizationId } from '@/stores/organizationStore';
import { getFinancialYearValue } from '@/utils/financialYears';

const defaultValues: TDSCertificateFormValues = {
  organizationId: '',
  financialYear: '',
  quarter: 'Q1',
  deducteePan: '',
  tdsSectionId: '',
};

function getCandidateValue(deducteePan: string, tdsSectionId: string) {
  return `${deducteePan}::${tdsSectionId}`;
}

export default function TDSCertificateWorkspace() {
  const navigate = useNavigate();
  const { id } = useParams();
  const activeOrganizationId = useActiveOrganizationId();
  const financialYearsQuery = useFinancialYears(activeOrganizationId ?? undefined);
  const certificateQuery = useTDSCertificate(id, activeOrganizationId ?? undefined);
  const generateCertificate = useGenerateTDSCertificate();
  const generateBulk = useGenerateBulkTDSCertificates();
  const [downloadMarkup, setDownloadMarkup] = useState('');

  const form = useForm<TDSCertificateFormValues, unknown, TDSCertificateFormInput>({
    resolver: zodResolver(tdsCertificateSchema),
    defaultValues: { ...defaultValues, organizationId: activeOrganizationId ?? '' },
  });
  const organizationId = form.watch('organizationId');
  const financialYear = form.watch('financialYear');
  const quarter = form.watch('quarter');
  const deducteePan = form.watch('deducteePan');
  const tdsSectionId = form.watch('tdsSectionId');
  const candidatesQuery = useTDSCertificateCandidates(organizationId || activeOrganizationId || undefined, financialYear || undefined, quarter);

  useEffect(() => {
    if (activeOrganizationId) {
      form.setValue('organizationId', activeOrganizationId);
    }
  }, [activeOrganizationId, form]);

  const selectedCandidate = useMemo(
    () =>
      candidatesQuery.data?.find(
        (candidate) =>
          candidate.deducteePan === deducteePan &&
          (!tdsSectionId || candidate.tdsSectionId === tdsSectionId),
      ),
    [candidatesQuery.data, deducteePan, tdsSectionId],
  );
  const selectedCandidateValue =
    deducteePan && tdsSectionId ? getCandidateValue(deducteePan, tdsSectionId) : '';

  async function onSubmit(values: TDSCertificateFormInput) {
    const result = await generateCertificate.mutateAsync(values);
    setDownloadMarkup(JSON.stringify(result, null, 2));
  }

  function handleDownloadSummary() {
    if (!downloadMarkup) return;
    const blob = new Blob([downloadMarkup], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `tds-certificate-summary-${Date.now()}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={id ? 'TDS Certificate Details' : 'Generate TDS Certificates'}
        subtitle="Generate deductee working summaries and track certificate metadata"
        breadcrumbs={[{ label: 'TDS Certificates', to: '/admin/tds/certificates' }]}
      />

      {generateCertificate.error && <ErrorState error={generateCertificate.error} />}
      {certificateQuery.error && <ErrorState error={certificateQuery.error} onRetry={() => certificateQuery.refetch()} />}

      {id ? (
        <div className="rounded-lg border p-4 text-sm">
          <div className="mb-3 flex items-center gap-2 font-medium"><CheckCircle2 className="h-4 w-4" />Certificate Summary</div>
          <pre className="overflow-x-auto whitespace-pre-wrap">{JSON.stringify(certificateQuery.data, null, 2)}</pre>
        </div>
      ) : (
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <FormShell
              footer={
                <>
                  <Button type="button" variant="outline" onClick={() => navigate('/admin/tds/certificates')}>Back</Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => generateBulk.mutateAsync({ organizationId: organizationId || activeOrganizationId || '', financialYear, quarter })}
                    disabled={generateBulk.isPending || !financialYear}
                    data-testid="tds-certificate-generate-bulk"
                  >
                    {generateBulk.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                    Generate Bulk
                  </Button>
                  <Button type="submit" disabled={generateCertificate.isPending} data-testid="tds-certificate-generate-single">
                    {generateCertificate.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                    Generate Certificate
                  </Button>
                </>
              }
            >
              <FormSection title="Certificate Scope">
                <FormField control={form.control} name="organizationId" render={({ field }) => (
                  <FormItem>
                    <FormLabel>Organization</FormLabel>
                    <FormControl><Input {...field} disabled /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField control={form.control} name="financialYear" render={({ field }) => (
                  <FormItem>
                    <FormLabel>Financial year</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl><SelectTrigger><SelectValue placeholder="Select financial year" /></SelectTrigger></FormControl>
                      <SelectContent>
                        {(financialYearsQuery.data?.items ?? []).map((year) => (
                          <SelectItem key={year.id} value={getFinancialYearValue(year)}>
                            {year.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField control={form.control} name="quarter" render={({ field }) => (
                  <FormItem>
                    <FormLabel>Quarter</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
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
                <FormField control={form.control} name="deducteePan" render={({ field }) => (
                  <FormItem>
                    <FormLabel>Deductee</FormLabel>
                    <Select
                      value={selectedCandidateValue}
                      onValueChange={(value) => {
                        const [nextDeducteePan = '', nextTdsSectionId = ''] = value.split('::');
                        field.onChange(nextDeducteePan);
                        form.setValue('tdsSectionId', nextTdsSectionId);
                      }}
                    >
                      <FormControl><SelectTrigger><SelectValue placeholder="Select deductee" /></SelectTrigger></FormControl>
                      <SelectContent>
                        {(candidatesQuery.data ?? []).filter((candidate) => candidate.deducteePan).map((candidate) => (
                          <SelectItem
                            key={`${candidate.deducteePan}-${candidate.tdsSectionId}`}
                            value={getCandidateValue(candidate.deducteePan!, candidate.tdsSectionId)}
                          >
                            {candidate.deducteeName} · {candidate.deducteePan}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField control={form.control} name="tdsSectionId" render={({ field }) => (
                  <FormItem>
                    <FormLabel>TDS section</FormLabel>
                    <FormControl><Input {...field} value={selectedCandidate?.tdsSectionCode ? `${selectedCandidate.tdsSectionCode} · ${selectedCandidate.tdsSectionName}` : field.value} readOnly /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
              </FormSection>
            </FormShell>
          </form>
        </Form>
      )}

      {downloadMarkup ? (
        <div className="rounded-lg border p-4">
          <div className="mb-3 flex items-center justify-between">
            <div className="font-medium">Generated certificate summary</div>
            <Button type="button" onClick={handleDownloadSummary} data-testid="tds-certificate-download-summary"><Download className="mr-2 h-4 w-4" />Download Summary</Button>
          </div>
          <pre className="overflow-x-auto whitespace-pre-wrap text-sm">{downloadMarkup}</pre>
        </div>
      ) : null}
    </div>
  );
}
