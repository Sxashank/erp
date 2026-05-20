import { format, subMonths } from 'date-fns';
import {
  AlertCircle,
  Calculator,
  CheckCircle2,
  Loader2,
  RefreshCw,
  Send,
  ShieldCheck,
} from 'lucide-react';
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
  useFileGstr3b,
  useGenerateGstr3b,
  useGstr3b,
  useSubmitGstr3b,
  type Gstr3bBucket,
} from '@/hooks/tax/useGstn';
import { useGSTRegistrations } from '@/hooks/tax/useTaxation';
import { useActiveOrganizationId } from '@/stores/organizationStore';

interface Gstr3bRow {
  id: string;
  label: string;
  taxableValue?: number;
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

function toAmount(value?: number) {
  return value ?? 0;
}

function buildBucketRow(id: string, label: string, bucket?: Gstr3bBucket): Gstr3bRow {
  return {
    id,
    label,
    taxableValue: bucket?.taxableValue,
    igst: bucket?.igst ?? 0,
    cgst: bucket?.cgst ?? 0,
    sgst: bucket?.sgst ?? 0,
    cess: bucket?.cess ?? 0,
  };
}

export function Gstr3bFiling() {
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
    includeInactive: false,
    pageSize: 100,
  });
  const registrations = registrationsQuery.data?.items;

  useEffect(() => {
    if (!gstin && registrations && registrations.length > 0) {
      setGstin(registrations[0].gstin);
    }
  }, [gstin, registrations]);

  const gstr3bQuery = useGstr3b(gstin || undefined, returnPeriod);
  const generateGstr3b = useGenerateGstr3b(gstin || undefined, returnPeriod);
  const submitGstr3b = useSubmitGstr3b(gstin || undefined, returnPeriod);
  const fileGstr3b = useFileGstr3b(gstin || undefined, returnPeriod);

  const filingStatus = gstr3bQuery.data?.status ?? 'NOT_GENERATED';
  const selectedRegistration = registrations?.find((registration) => registration.gstin === gstin);
  const outwardSupplies = gstr3bQuery.data?.outwardTaxableSupplies;
  const eligibleItc = gstr3bQuery.data?.eligibleItc?.total;
  const taxPayable = gstr3bQuery.data?.taxPayable;

  const outwardRows = useMemo<Gstr3bRow[]>(
    () => [
      buildBucketRow(
        'outward-taxable',
        'Outward taxable supplies (other than zero rated, nil rated and exempted)',
        outwardSupplies,
      ),
      buildBucketRow(
        'outward-zero-rated',
        'Outward taxable supplies (zero rated)',
        gstr3bQuery.data?.outwardTaxableZeroRated,
      ),
      {
        id: 'other-outward',
        label: 'Other outward supplies (nil rated, exempted and non-GST)',
        taxableValue:
          toAmount(gstr3bQuery.data?.otherOutwardSupplies?.nilRated) +
          toAmount(gstr3bQuery.data?.otherOutwardSupplies?.exempt) +
          toAmount(gstr3bQuery.data?.otherOutwardSupplies?.nonGst),
        igst: 0,
        cgst: 0,
        sgst: 0,
        cess: 0,
      },
    ],
    [gstr3bQuery.data, outwardSupplies],
  );

  const itcRows = useMemo<Gstr3bRow[]>(
    () => [
      buildBucketRow('itc-import-goods', 'ITC available · import of goods', gstr3bQuery.data?.eligibleItc?.importOfGoods),
      buildBucketRow('itc-import-services', 'ITC available · import of services', gstr3bQuery.data?.eligibleItc?.importOfServices),
      buildBucketRow('itc-reverse-charge', 'ITC available · reverse charge', gstr3bQuery.data?.eligibleItc?.inwardReverseCharge),
      buildBucketRow('itc-all-other', 'ITC available · all other ITC', gstr3bQuery.data?.eligibleItc?.allOtherItc),
      buildBucketRow('itc-net', 'Net ITC available', gstr3bQuery.data?.netItc),
    ],
    [gstr3bQuery.data],
  );

  const paymentRows = useMemo<Gstr3bRow[]>(
    () => [buildBucketRow('tax-payable', 'Net tax payable after ITC adjustment', taxPayable)],
    [taxPayable],
  );

  const sectionColumns = useMemo<Column<Gstr3bRow>[]>(
    () => [
      { key: 'label', header: 'Particulars' },
      {
        key: 'taxableValue',
        header: 'Taxable Value',
        align: 'right',
        render: (row) => <AmountDisplay amount={row.taxableValue} />,
      },
      {
        key: 'igst',
        header: 'IGST',
        align: 'right',
        render: (row) => <AmountDisplay amount={row.igst} />,
      },
      {
        key: 'cgst',
        header: 'CGST',
        align: 'right',
        render: (row) => <AmountDisplay amount={row.cgst} />,
      },
      {
        key: 'sgst',
        header: 'SGST',
        align: 'right',
        render: (row) => <AmountDisplay amount={row.sgst} />,
      },
      {
        key: 'cess',
        header: 'Cess',
        align: 'right',
        render: (row) => <AmountDisplay amount={row.cess} />,
      },
    ],
    [],
  );

  async function handleGenerate() {
    setError('');
    setSuccess('');
    try {
      await generateGstr3b.mutateAsync({ regenerate: filingStatus !== 'NOT_GENERATED' });
      setSuccess('GSTR-3B prepared successfully.');
      await gstr3bQuery.refetch();
    } catch (mutationError) {
      setError(getApiErrorMessage(mutationError, 'Failed to prepare GSTR-3B.'));
    }
  }

  async function handleSubmit() {
    setError('');
    setSuccess('');
    try {
      await submitGstr3b.mutateAsync();
      setSuccess('GSTR-3B submitted successfully.');
      await gstr3bQuery.refetch();
    } catch (mutationError) {
      setError(getApiErrorMessage(mutationError, 'Failed to submit GSTR-3B.'));
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
      await fileGstr3b.mutateAsync({ pan, otp });
      setSuccess('GSTR-3B filed successfully.');
      setShowFilingDialog(false);
      await gstr3bQuery.refetch();
    } catch (mutationError) {
      setError(getApiErrorMessage(mutationError, 'Failed to file GSTR-3B.'));
    }
  }

  if (registrationsQuery.isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="GSTR-3B Filing"
          subtitle="Prepare monthly summary data for manual GSTN filing"
          breadcrumbs={[{ label: 'GSTN Portal', to: '/admin/gst/gstn' }, { label: 'GSTR-3B' }]}
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
          title="GSTR-3B Filing"
          subtitle="Prepare monthly summary data for manual GSTN filing"
          breadcrumbs={[{ label: 'GSTN Portal', to: '/admin/gst/gstn' }, { label: 'GSTR-3B' }]}
        />
        <EmptyState
          title="No GST registrations"
          subtitle="Add a GST registration before preparing GSTR-3B."
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
        title="GSTR-3B Filing"
        subtitle="Prepare monthly summary data for manual GSTN filing"
        breadcrumbs={[{ label: 'GSTN Portal', to: '/admin/gst/gstn' }, { label: 'GSTR-3B' }]}
        actions={<GstnFilingStatusBadge status={filingStatus} />}
      />

      <FilterBar
        onClear={() => {
          setError('');
          setSuccess('');
        }}
      >
        <div className="min-w-[320px]">
          <Label htmlFor="gstr3b-gstin">GSTIN</Label>
          <Select value={gstin} onValueChange={setGstin}>
            <SelectTrigger id="gstr3b-gstin" className="mt-1">
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
          <Label htmlFor="gstr3b-period">Return Period</Label>
          <Input
            id="gstr3b-period"
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
          onClick={() => gstr3bQuery.refetch()}
          disabled={!gstin || gstr3bQuery.isFetching}
          className="self-end"
        >
          {gstr3bQuery.isFetching ? (
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
            <CardTitle className="text-sm font-medium">Output Tax</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              <AmountDisplay
                amount={toAmount(outwardSupplies?.igst) + toAmount(outwardSupplies?.cgst) + toAmount(outwardSupplies?.sgst)}
              />
            </div>
            <p className="text-xs text-muted-foreground">Tax on outward supplies</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Input Tax Credit</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              <AmountDisplay
                amount={toAmount(eligibleItc?.igst) + toAmount(eligibleItc?.cgst) + toAmount(eligibleItc?.sgst)}
              />
            </div>
            <p className="text-xs text-muted-foreground">Eligible ITC to claim</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Net Tax Payable</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">
              <AmountDisplay
                amount={toAmount(taxPayable?.igst) + toAmount(taxPayable?.cgst) + toAmount(taxPayable?.sgst)}
              />
            </div>
            <p className="text-xs text-muted-foreground">After ITC adjustment</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Cess Payable</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600">
              <AmountDisplay amount={taxPayable?.cess} />
            </div>
            <p className="text-xs text-muted-foreground">Compensation cess</p>
          </CardContent>
        </Card>
      </div>

      {gstr3bQuery.data ? (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">3.1 Details of Outward Supplies</CardTitle>
              <CardDescription>
                {selectedRegistration
                  ? `${selectedRegistration.tradeName || selectedRegistration.legalName} · ${formatReturnPeriod(returnPeriod)}`
                  : formatReturnPeriod(returnPeriod)}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                data={outwardRows}
                columns={sectionColumns}
                getRowId={(row) => row.id}
                emptyTitle="No outward supply data"
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">4 Eligible ITC</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable data={itcRows} columns={sectionColumns} getRowId={(row) => row.id} emptyTitle="No ITC data" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">6.1 Payment of Tax</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                data={paymentRows}
                columns={sectionColumns}
                getRowId={(row) => row.id}
                emptyTitle="No payment data"
              />
            </CardContent>
          </Card>
        </>
      ) : (
        <EmptyState
          title="No prepared GSTR-3B data"
          subtitle="Generate the return to review outward supplies, ITC, and tax payable."
          action={
            <Button onClick={handleGenerate} disabled={generateGstr3b.isPending || !gstin}>
              <Calculator className="mr-2 h-4 w-4" />
              Generate GSTR-3B
            </Button>
          }
        />
      )}

      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium">Filing Actions</h3>
              <p className="text-sm text-muted-foreground">
                {filingStatus === 'NOT_GENERATED' && 'Prepare GSTR-3B to calculate tax liability.'}
                {['GENERATED', 'DRAFT'].includes(filingStatus) && 'Review the summary and submit the draft to GSTN.'}
                {filingStatus === 'SUBMITTED' && 'Capture PAN and OTP after confirming tax payment details.'}
                {filingStatus === 'FILED' && 'The manual filing record is complete for this period.'}
              </p>
            </div>
            <div className="flex gap-3">
              {['NOT_GENERATED', 'GENERATED', 'DRAFT'].includes(filingStatus) ? (
                <Button onClick={handleGenerate} disabled={generateGstr3b.isPending || !gstin} data-testid="gstr3b-generate">
                  {generateGstr3b.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Preparing...
                    </>
                  ) : (
                    <>
                      <Calculator className="mr-2 h-4 w-4" />
                      {filingStatus === 'NOT_GENERATED' ? 'Generate' : 'Regenerate'}
                    </>
                  )}
                </Button>
              ) : null}
              {['GENERATED', 'DRAFT'].includes(filingStatus) ? (
                <Button onClick={handleSubmit} disabled={submitGstr3b.isPending} variant="secondary" data-testid="gstr3b-submit">
                  {submitGstr3b.isPending ? (
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
                <Button onClick={() => setShowFilingDialog(true)} data-testid="gstr3b-open-file-dialog">
                  <ShieldCheck className="mr-2 h-4 w-4" />
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
            <DialogTitle>File GSTR-3B with EVC</DialogTitle>
            <DialogDescription>
              Enter the authorized signatory PAN and OTP to capture the filing action.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="gstr3b-pan">PAN of Authorized Signatory</Label>
              <Input
                id="gstr3b-pan"
                value={pan}
                onChange={(event) => setPan(event.target.value.toUpperCase())}
                placeholder="Enter PAN"
                maxLength={10}
                data-testid="gstr3b-pan-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="gstr3b-otp">OTP</Label>
              <Input
                id="gstr3b-otp"
                value={otp}
                onChange={(event) => setOtp(event.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="Enter 6-digit OTP"
                maxLength={6}
                data-testid="gstr3b-otp-input"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowFilingDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleFile} disabled={fileGstr3b.isPending || !pan || !otp} data-testid="gstr3b-file">
              {fileGstr3b.isPending ? (
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

export default Gstr3bFiling;
