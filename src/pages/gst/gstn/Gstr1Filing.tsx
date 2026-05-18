import { format, subMonths } from 'date-fns';
import { AlertCircle, CheckCircle2, Loader2, RefreshCw, Send } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { AmountDisplay } from '@/components/common/AmountDisplay';
import { DataTable, type Column } from '@/components/common/DataTable';
import { EmptyState } from '@/components/common/EmptyState';
import { FilterBar } from '@/components/common/FilterBar';
import { PageHeader } from '@/components/common/PageHeader';
import { GstnFilingStatusBadge } from '@/components/gst/GstnStatusBadge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  getApiErrorMessage,
  useFileGstr1,
  useGenerateGstr1,
  useGstr1,
  useSubmitGstr1,
} from '@/hooks/tax/useGstn';
import { useGSTRegistrations } from '@/hooks/tax/useTaxation';
import { useActiveOrganizationId } from '@/stores/organizationStore';

interface Gstr1Section {
  section: string;
  description: string;
  invoiceCount: number;
  taxableValue: number;
  igst: number;
  cgst: number;
  sgst: number;
  cess: number;
}

function formatReturnPeriod(period: string) {
  if (!period || period.length !== 6) {
    return period;
  }

  const month = Number.parseInt(period.substring(0, 2), 10);
  const year = period.substring(2, 6);
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${monthNames[month - 1]} ${year}`;
}

function getInitialReturnPeriod() {
  return format(subMonths(new Date(), 1), 'MMyyyy');
}

export function Gstr1Filing() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const activeOrganizationId = useActiveOrganizationId();
  const [gstin, setGstin] = useState(searchParams.get('gstin') || '');
  const [returnPeriod, setReturnPeriod] = useState(getInitialReturnPeriod());
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showFilingDialog, setShowFilingDialog] = useState(false);
  const [pan, setPan] = useState('');
  const [otp, setOtp] = useState('');

  const registrationsQuery = useGSTRegistrations({
    organizationId: activeOrganizationId ?? undefined,
    includeInactive: false,
    pageSize: 100,
  });
  const registrations = registrationsQuery.data?.items;

  useEffect(() => {
    if (!gstin && registrations && registrations.length > 0) {
      setGstin(registrations[0].gstin);
    }
  }, [gstin, registrations]);

  const gstr1Query = useGstr1(gstin || undefined, returnPeriod);
  const generateGstr1 = useGenerateGstr1(gstin || undefined, returnPeriod);
  const submitGstr1 = useSubmitGstr1(gstin || undefined, returnPeriod);
  const fileGstr1 = useFileGstr1(gstin || undefined, returnPeriod);

  const filingStatus = gstr1Query.data?.status ?? 'NOT_GENERATED';
  const selectedRegistration = registrations?.find((registration) => registration.gstin === gstin);

  const sections = useMemo<Gstr1Section[]>(() => {
    if (!gstr1Query.data) {
      return [];
    }

    return [
      {
        section: 'B2B',
        description: 'B2B invoices (taxable)',
        invoiceCount: gstr1Query.data.b2bInvoices.length,
        taxableValue: gstr1Query.data.b2bSummary.taxableValue,
        igst: gstr1Query.data.b2bSummary.igstAmount,
        cgst: gstr1Query.data.b2bSummary.cgstAmount,
        sgst: gstr1Query.data.b2bSummary.sgstAmount,
        cess: gstr1Query.data.b2bSummary.cessAmount,
      },
      {
        section: 'B2CL',
        description: 'B2C large invoices (> ₹2.5 lakh)',
        invoiceCount: gstr1Query.data.b2clInvoices.length,
        taxableValue: gstr1Query.data.b2clSummary.taxableValue,
        igst: gstr1Query.data.b2clSummary.igstAmount,
        cgst: gstr1Query.data.b2clSummary.cgstAmount,
        sgst: gstr1Query.data.b2clSummary.sgstAmount,
        cess: gstr1Query.data.b2clSummary.cessAmount,
      },
      {
        section: 'B2CS',
        description: 'B2C small invoices',
        invoiceCount: gstr1Query.data.b2csCount,
        taxableValue: gstr1Query.data.b2csSummary.taxableValue,
        igst: gstr1Query.data.b2csSummary.igstAmount,
        cgst: gstr1Query.data.b2csSummary.cgstAmount,
        sgst: gstr1Query.data.b2csSummary.sgstAmount,
        cess: gstr1Query.data.b2csSummary.cessAmount,
      },
      {
        section: 'CDNR',
        description: 'Credit and debit notes',
        invoiceCount: gstr1Query.data.cdnrCount,
        taxableValue: gstr1Query.data.cdnrSummary.taxableValue,
        igst: gstr1Query.data.cdnrSummary.igstAmount,
        cgst: gstr1Query.data.cdnrSummary.cgstAmount,
        sgst: gstr1Query.data.cdnrSummary.sgstAmount,
        cess: gstr1Query.data.cdnrSummary.cessAmount,
      },
      {
        section: 'EXP',
        description: 'Export invoices',
        invoiceCount: gstr1Query.data.exportsCount,
        taxableValue: gstr1Query.data.expSummary.taxableValue,
        igst: gstr1Query.data.expSummary.igstAmount,
        cgst: gstr1Query.data.expSummary.cgstAmount,
        sgst: gstr1Query.data.expSummary.sgstAmount,
        cess: gstr1Query.data.expSummary.cessAmount,
      },
    ];
  }, [gstr1Query.data]);

  const totals = useMemo(
    () =>
      sections.reduce(
        (accumulator, section) => ({
          taxableValue: accumulator.taxableValue + section.taxableValue,
          igst: accumulator.igst + section.igst,
          cgst: accumulator.cgst + section.cgst,
          sgst: accumulator.sgst + section.sgst,
          cess: accumulator.cess + section.cess,
        }),
        { taxableValue: 0, igst: 0, cgst: 0, sgst: 0, cess: 0 },
      ),
    [sections],
  );

  const sectionColumns = useMemo<Column<Gstr1Section>[]>(
    () => [
      { key: 'section', header: 'Section', sortable: true },
      { key: 'description', header: 'Description' },
      { key: 'invoiceCount', header: 'Invoices', align: 'right', sortable: true },
      {
        key: 'taxableValue',
        header: 'Taxable Value',
        align: 'right',
        sortable: true,
        render: (section) => <AmountDisplay amount={section.taxableValue} />,
      },
      {
        key: 'igst',
        header: 'IGST',
        align: 'right',
        render: (section) => <AmountDisplay amount={section.igst} />,
      },
      {
        key: 'cgst',
        header: 'CGST',
        align: 'right',
        render: (section) => <AmountDisplay amount={section.cgst} />,
      },
      {
        key: 'sgst',
        header: 'SGST',
        align: 'right',
        render: (section) => <AmountDisplay amount={section.sgst} />,
      },
      {
        key: 'cess',
        header: 'Cess',
        align: 'right',
        render: (section) => <AmountDisplay amount={section.cess} />,
      },
    ],
    [],
  );

  async function handleGenerate() {
    setError('');
    setSuccess('');
    try {
      await generateGstr1.mutateAsync({ regenerate: filingStatus !== 'NOT_GENERATED' });
      setSuccess('GSTR-1 prepared successfully.');
      await gstr1Query.refetch();
    } catch (mutationError) {
      setError(getApiErrorMessage(mutationError, 'Failed to prepare GSTR-1.'));
    }
  }

  async function handleSubmit() {
    setError('');
    setSuccess('');
    try {
      await submitGstr1.mutateAsync();
      setSuccess('GSTR-1 submitted successfully.');
      await gstr1Query.refetch();
    } catch (mutationError) {
      setError(getApiErrorMessage(mutationError, 'Failed to submit GSTR-1.'));
    }
  }

  async function handleFile() {
    if (!pan || !otp) {
      setError('Enter PAN and OTP to file the return.');
      return;
    }

    setError('');
    setSuccess('');
    try {
      await fileGstr1.mutateAsync({ pan, otp });
      setSuccess('GSTR-1 filed successfully.');
      setShowFilingDialog(false);
      await gstr1Query.refetch();
    } catch (mutationError) {
      setError(getApiErrorMessage(mutationError, 'Failed to file GSTR-1.'));
    }
  }

  const totalTax = totals.igst + totals.cgst + totals.sgst + totals.cess;

  if (registrationsQuery.isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="GSTR-1 Filing"
          subtitle="Prepare outward supply data for manual GSTN filing"
          breadcrumbs={[{ label: 'GSTN Portal', to: '/admin/gst/gstn' }, { label: 'GSTR-1' }]}
        />
        <div className="flex h-40 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (!registrations || registrations.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="GSTR-1 Filing"
          subtitle="Prepare outward supply data for manual GSTN filing"
          breadcrumbs={[{ label: 'GSTN Portal', to: '/admin/gst/gstn' }, { label: 'GSTR-1' }]}
        />
        <EmptyState
          title="No GST registrations"
          subtitle="Add a GST registration before preparing GSTR-1."
          action={
            <Button onClick={() => navigate('/admin/gst/registrations')}>
              Manage GST Registrations
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="GSTR-1 Filing"
        subtitle="Prepare outward supply data for manual GSTN filing"
        breadcrumbs={[{ label: 'GSTN Portal', to: '/admin/gst/gstn' }, { label: 'GSTR-1' }]}
        actions={<GstnFilingStatusBadge status={filingStatus} />}
      />

      <FilterBar
        onClear={() => {
          setError('');
          setSuccess('');
        }}
      >
        <div className="min-w-[320px]">
          <Label htmlFor="gstr1-gstin">GSTIN</Label>
          <Select value={gstin} onValueChange={setGstin}>
            <SelectTrigger id="gstr1-gstin" className="mt-1">
              <SelectValue placeholder="Select GSTIN" />
            </SelectTrigger>
            <SelectContent>
              {registrations.map((registration) => (
                <SelectItem key={registration.id} value={registration.gstin}>
                  {registration.gstin} · {registration.tradeName || registration.legalName}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="w-48">
          <Label htmlFor="gstr1-period">Return Period</Label>
          <Input
            id="gstr1-period"
            type="month"
            value={`${returnPeriod.substring(2, 6)}-${returnPeriod.substring(0, 2)}`}
            onChange={(event) => {
              const [year, month] = event.target.value.split('-');
              if (year && month) {
                setReturnPeriod(`${month}${year}`);
              }
            }}
            className="mt-1"
          />
        </div>
        <Button
          variant="outline"
          onClick={() => gstr1Query.refetch()}
          disabled={!gstin || gstr1Query.isFetching}
          className="self-end"
        >
          {gstr1Query.isFetching ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
        </Button>
      </FilterBar>

      {error ? (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {success ? (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle2 className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{success}</AlertDescription>
        </Alert>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Taxable Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              <AmountDisplay amount={totals.taxableValue} />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">IGST</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              <AmountDisplay amount={totals.igst} />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">CGST + SGST</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              <AmountDisplay amount={totals.cgst + totals.sgst} />
            </div>
            <p className="text-xs text-muted-foreground">
              CGST <AmountDisplay amount={totals.cgst} compact /> · SGST{' '}
              <AmountDisplay amount={totals.sgst} compact />
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Tax</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">
              <AmountDisplay amount={totalTax} />
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>GSTR-1 Sections for {formatReturnPeriod(returnPeriod)}</CardTitle>
          <CardDescription>
            {selectedRegistration
              ? `${selectedRegistration.tradeName || selectedRegistration.legalName} · ${gstin}`
              : 'Summary of outward supplies by section'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {gstr1Query.data ? (
            <DataTable
              data={sections}
              columns={sectionColumns}
              getRowId={(section) => section.section}
              isLoading={gstr1Query.isLoading}
              error={gstr1Query.error}
              onRetry={() => gstr1Query.refetch()}
              emptyTitle="No section data"
              emptySubtitle="Generate GSTR-1 to load outward supply sections for the selected period."
            />
          ) : (
            <EmptyState
              title="No prepared GSTR-1 data"
              subtitle="Generate the return to review section-wise outward supply totals."
            />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium">Filing Actions</h3>
              <p className="text-sm text-muted-foreground">
                {filingStatus === 'NOT_GENERATED' && 'Prepare GSTR-1 from approved outward supply data.'}
                {['GENERATED', 'DRAFT'].includes(filingStatus) && 'Review the totals and submit the draft to GSTN.'}
                {filingStatus === 'SUBMITTED' && 'Capture PAN and OTP to complete manual filing.'}
                {filingStatus === 'FILED' && 'The manual filing record is complete for this period.'}
              </p>
            </div>
            <div className="flex gap-3">
              {['NOT_GENERATED', 'GENERATED', 'DRAFT'].includes(filingStatus) ? (
                <Button onClick={handleGenerate} disabled={generateGstr1.isPending || !gstin} data-testid="gstr1-generate">
                  {generateGstr1.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Preparing...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4" />
                      {filingStatus === 'NOT_GENERATED' ? 'Generate' : 'Regenerate'}
                    </>
                  )}
                </Button>
              ) : null}
              {['GENERATED', 'DRAFT'].includes(filingStatus) ? (
                <Button onClick={handleSubmit} disabled={submitGstr1.isPending} variant="secondary" data-testid="gstr1-submit">
                  {submitGstr1.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    <>
                      <Send className="mr-2 h-4 w-4" />
                      Submit to GSTN
                    </>
                  )}
                </Button>
              ) : null}
              {filingStatus === 'SUBMITTED' ? (
                <Button onClick={() => setShowFilingDialog(true)} data-testid="gstr1-open-file-dialog">
                  <CheckCircle2 className="mr-2 h-4 w-4" />
                  File with EVC
                </Button>
              ) : null}
              {filingStatus === 'FILED' ? (
                <GstnFilingStatusBadge status="FILED" className="px-4 py-2" />
              ) : null}
            </div>
          </div>
        </CardContent>
      </Card>

      <Dialog open={showFilingDialog} onOpenChange={setShowFilingDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>File GSTR-1 with EVC</DialogTitle>
            <DialogDescription>
              Enter the authorized signatory PAN and OTP to capture the filing action.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="gstr1-pan">PAN of Authorized Signatory</Label>
              <Input
                id="gstr1-pan"
                value={pan}
                onChange={(event) => setPan(event.target.value.toUpperCase())}
                placeholder="Enter PAN"
                maxLength={10}
                data-testid="gstr1-pan-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="gstr1-otp">OTP</Label>
              <Input
                id="gstr1-otp"
                value={otp}
                onChange={(event) => setOtp(event.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="Enter 6-digit OTP"
                maxLength={6}
                data-testid="gstr1-otp-input"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowFilingDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleFile} disabled={fileGstr1.isPending || !pan || !otp} data-testid="gstr1-file">
              {fileGstr1.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Filing...
                </>
              ) : (
                'File Return'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default Gstr1Filing;
