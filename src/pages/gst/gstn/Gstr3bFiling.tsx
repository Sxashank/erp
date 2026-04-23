import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft,
  FileText,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Clock,
  Loader2,
  Send,
  Calculator,
  CreditCard,
  Building2,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { gstnApi, gstRegistrationsApi } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import { useActiveOrganizationId } from '@/stores/organizationStore';
import { format, subMonths } from 'date-fns';

interface GSTR3BData {
  outward_taxable_supplies?: {
    total_taxable_value: number;
    igst: number;
    cgst: number;
    sgst: number;
    cess: number;
  };
  outward_taxable_zero_rated?: {
    total_taxable_value: number;
  };
  other_outward_supplies?: {
    nil_rated: number;
    exempt: number;
    non_gst: number;
  };
  eligible_itc?: {
    import_of_goods: { igst: number; cgst: number; sgst: number; cess: number };
    import_of_services: { igst: number; cgst: number; sgst: number; cess: number };
    inward_reverse_charge: { igst: number; cgst: number; sgst: number; cess: number };
    inward_isd: { igst: number; cgst: number; sgst: number; cess: number };
    all_other_itc: { igst: number; cgst: number; sgst: number; cess: number };
    total: { igst: number; cgst: number; sgst: number; cess: number };
  };
  ineligible_itc?: {
    blocked: { igst: number; cgst: number; sgst: number; cess: number };
    reversal_others: { igst: number; cgst: number; sgst: number; cess: number };
    total: { igst: number; cgst: number; sgst: number; cess: number };
  };
  net_itc?: { igst: number; cgst: number; sgst: number; cess: number };
  inward_reverse_charge?: {
    total_taxable_value: number;
    igst: number;
    cgst: number;
    sgst: number;
    cess: number;
  };
  tax_payable?: { igst: number; cgst: number; sgst: number; cess: number };
  tax_paid?: { igst: number; cgst: number; sgst: number; cess: number };
}

const formatAmount = (amount: number | undefined) => {
  if (amount === undefined || amount === null) return '₹ 0.00';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
  }).format(amount);
};

const formatPeriod = (period: string) => {
  if (!period || period.length !== 6) return period;
  const month = period.substring(0, 2);
  const year = period.substring(2, 6);
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${monthNames[parseInt(month) - 1]} ${year}`;
};

export function Gstr3bFiling() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  const activeOrganizationId = useActiveOrganizationId();
  const [gstin, setGstin] = useState(searchParams.get('gstin') || '');
  const [returnPeriod, setReturnPeriod] = useState(format(subMonths(new Date(), 1), 'MMyyyy'));
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [filing, setFiling] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [gstr3bData, setGstr3bData] = useState<GSTR3BData | null>(null);
  const [status, setStatus] = useState<string>('NOT_GENERATED');
  const [showFilingDialog, setShowFilingDialog] = useState(false);
  const [pan, setPan] = useState('');
  const [otp, setOtp] = useState('');
  const [registrations, setRegistrations] = useState<any[]>([]);

  useEffect(() => {
    fetchRegistrations();
  }, []);

  useEffect(() => {
    if (gstin && returnPeriod) {
      fetchGstr3bData();
    }
  }, [gstin, returnPeriod]);

  const fetchRegistrations = async () => {
    try {
      const response = await gstRegistrationsApi.list({
        organization_id: activeOrganizationId ?? undefined,
        include_inactive: false,
      });
      const data = response.data.items || response.data;
      setRegistrations(data);
      if (!gstin && data.length > 0) {
        setGstin(data[0].gstin);
      }
    } catch (error) {
      console.error('Failed to fetch registrations:', error);
    }
  };

  const fetchGstr3bData = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await gstnApi.getGstr3b(gstin, returnPeriod);
      if (response.data) {
        setGstr3bData(response.data);
        setStatus(response.data.status || 'GENERATED');
      } else {
        setGstr3bData(null);
        setStatus('NOT_GENERATED');
      }
    } catch (err: any) {
      if (err.response?.status === 404) {
        setGstr3bData(null);
        setStatus('NOT_GENERATED');
      } else {
        setError('Failed to fetch GSTR-3B data');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setError('');
    setSuccess('');
    try {
      await gstnApi.generateGstr3b(gstin, returnPeriod, { regenerate: status !== 'NOT_GENERATED' });
      setSuccess('GSTR-3B generated successfully');
      await fetchGstr3bData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate GSTR-3B');
    } finally {
      setGenerating(false);
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError('');
    setSuccess('');
    try {
      await gstnApi.submitGstr3b(gstin, returnPeriod);
      setSuccess('GSTR-3B submitted successfully');
      await fetchGstr3bData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit GSTR-3B');
    } finally {
      setSubmitting(false);
    }
  };

  const handleFile = async () => {
    if (!pan || !otp) {
      setError('Please enter PAN and OTP');
      return;
    }

    setFiling(true);
    setError('');
    try {
      await gstnApi.fileGstr3b(gstin, returnPeriod, { pan, otp });
      setSuccess('GSTR-3B filed successfully!');
      setShowFilingDialog(false);
      await fetchGstr3bData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to file GSTR-3B');
    } finally {
      setFiling(false);
    }
  };

  const getStatusBadge = () => {
    const statusConfig: Record<string, { className: string; label: string; icon: any }> = {
      NOT_GENERATED: { className: 'bg-slate-100 text-slate-700', label: 'Not Generated', icon: Clock },
      DRAFT: { className: 'bg-slate-100 text-slate-700', label: 'Draft', icon: FileText },
      GENERATED: { className: 'bg-blue-100 text-blue-700', label: 'Generated', icon: Calculator },
      VALIDATED: { className: 'bg-amber-100 text-amber-700', label: 'Validated', icon: CheckCircle },
      SUBMITTED: { className: 'bg-purple-100 text-purple-700', label: 'Submitted', icon: Send },
      FILED: { className: 'bg-green-100 text-green-700', label: 'Filed', icon: CheckCircle },
      ERROR: { className: 'bg-red-100 text-red-700', label: 'Error', icon: AlertCircle },
    };
    const config = statusConfig[status] || statusConfig.NOT_GENERATED;
    const Icon = config.icon;
    return (
      <Badge className={config.className}>
        <Icon className="h-3 w-3 mr-1" />
        {config.label}
      </Badge>
    );
  };

  const outwardSupplies = gstr3bData?.outward_taxable_supplies;
  const eligibleItc = gstr3bData?.eligible_itc?.total;
  const taxPayable = gstr3bData?.tax_payable;

  return (
    <div className="space-y-6">
      <PageHeader
        title="GSTR-3B Filing"
        subtitle="Monthly summary return"
        breadcrumbs={[
          { label: 'GSTN Portal', to: '/admin/gst/gstn' },
          { label: 'GSTR-3B' },
        ]}
        actions={getStatusBadge()}
      />

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-end gap-4">
            <div className="flex-1">
              <Label>GSTIN</Label>
              <select
                value={gstin}
                onChange={(e) => setGstin(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm mt-1"
              >
                {registrations.map((reg) => (
                  <option key={reg.id} value={reg.gstin}>
                    {reg.gstin} - {reg.trade_name || reg.legal_name}
                  </option>
                ))}
              </select>
            </div>
            <div className="w-48">
              <Label>Return Period</Label>
              <Input
                type="month"
                value={`${returnPeriod.substring(2, 6)}-${returnPeriod.substring(0, 2)}`}
                onChange={(e) => {
                  const [year, month] = e.target.value.split('-');
                  setReturnPeriod(`${month}${year}`);
                }}
                className="mt-1"
              />
            </div>
            <Button variant="outline" onClick={fetchGstr3bData} disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            </Button>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="bg-green-50 border-green-200">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{success}</AlertDescription>
        </Alert>
      )}

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Output Tax</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {formatAmount((outwardSupplies?.igst || 0) + (outwardSupplies?.cgst || 0) + (outwardSupplies?.sgst || 0))}
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
              {formatAmount((eligibleItc?.igst || 0) + (eligibleItc?.cgst || 0) + (eligibleItc?.sgst || 0))}
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
              {formatAmount((taxPayable?.igst || 0) + (taxPayable?.cgst || 0) + (taxPayable?.sgst || 0))}
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
              {formatAmount(taxPayable?.cess || 0)}
            </div>
            <p className="text-xs text-muted-foreground">Compensation cess</p>
          </CardContent>
        </Card>
      </div>

      {/* GSTR-3B Sections */}
      {loading ? (
        <Card>
          <CardContent className="py-12">
            <div className="flex items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            </div>
          </CardContent>
        </Card>
      ) : gstr3bData ? (
        <>
          {/* 3.1 - Outward Supplies */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">3.1 - Details of Outward Supplies</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nature of Supplies</TableHead>
                    <TableHead className="text-right">Taxable Value</TableHead>
                    <TableHead className="text-right">IGST</TableHead>
                    <TableHead className="text-right">CGST</TableHead>
                    <TableHead className="text-right">SGST</TableHead>
                    <TableHead className="text-right">Cess</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell>(a) Outward taxable supplies (other than zero rated, nil rated and exempted)</TableCell>
                    <TableCell className="text-right">{formatAmount(outwardSupplies?.total_taxable_value)}</TableCell>
                    <TableCell className="text-right">{formatAmount(outwardSupplies?.igst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(outwardSupplies?.cgst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(outwardSupplies?.sgst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(outwardSupplies?.cess)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>(b) Outward taxable supplies (zero rated)</TableCell>
                    <TableCell className="text-right">{formatAmount(gstr3bData?.outward_taxable_zero_rated?.total_taxable_value)}</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">-</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>(c) Other outward supplies (Nil rated, exempted)</TableCell>
                    <TableCell className="text-right">
                      {formatAmount((gstr3bData?.other_outward_supplies?.nil_rated || 0) + (gstr3bData?.other_outward_supplies?.exempt || 0))}
                    </TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">-</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* 4 - Eligible ITC */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">4 - Eligible ITC</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Details</TableHead>
                    <TableHead className="text-right">IGST</TableHead>
                    <TableHead className="text-right">CGST</TableHead>
                    <TableHead className="text-right">SGST</TableHead>
                    <TableHead className="text-right">Cess</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell>(A) ITC Available - Import of goods</TableCell>
                    <TableCell className="text-right">{formatAmount(gstr3bData?.eligible_itc?.import_of_goods?.igst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(gstr3bData?.eligible_itc?.import_of_goods?.cgst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(gstr3bData?.eligible_itc?.import_of_goods?.sgst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(gstr3bData?.eligible_itc?.import_of_goods?.cess)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>(B) ITC Available - Import of services</TableCell>
                    <TableCell className="text-right">{formatAmount(gstr3bData?.eligible_itc?.import_of_services?.igst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(gstr3bData?.eligible_itc?.import_of_services?.cgst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(gstr3bData?.eligible_itc?.import_of_services?.sgst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(gstr3bData?.eligible_itc?.import_of_services?.cess)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>(C) ITC Available - Inward supplies liable to reverse charge</TableCell>
                    <TableCell className="text-right">{formatAmount(gstr3bData?.eligible_itc?.inward_reverse_charge?.igst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(gstr3bData?.eligible_itc?.inward_reverse_charge?.cgst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(gstr3bData?.eligible_itc?.inward_reverse_charge?.sgst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(gstr3bData?.eligible_itc?.inward_reverse_charge?.cess)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>(D) ITC Available - All other ITC</TableCell>
                    <TableCell className="text-right">{formatAmount(gstr3bData?.eligible_itc?.all_other_itc?.igst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(gstr3bData?.eligible_itc?.all_other_itc?.cgst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(gstr3bData?.eligible_itc?.all_other_itc?.sgst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(gstr3bData?.eligible_itc?.all_other_itc?.cess)}</TableCell>
                  </TableRow>
                  <TableRow className="font-semibold bg-slate-50">
                    <TableCell>Total ITC Available</TableCell>
                    <TableCell className="text-right">{formatAmount(eligibleItc?.igst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(eligibleItc?.cgst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(eligibleItc?.sgst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(eligibleItc?.cess)}</TableCell>
                  </TableRow>
                  <TableRow className="font-semibold bg-green-50">
                    <TableCell>Net ITC Available</TableCell>
                    <TableCell className="text-right">{formatAmount(gstr3bData?.net_itc?.igst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(gstr3bData?.net_itc?.cgst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(gstr3bData?.net_itc?.sgst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(gstr3bData?.net_itc?.cess)}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* 6.1 - Payment of Tax */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">6.1 - Payment of Tax</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-right">IGST</TableHead>
                    <TableHead className="text-right">CGST</TableHead>
                    <TableHead className="text-right">SGST</TableHead>
                    <TableHead className="text-right">Cess</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow className="font-semibold bg-red-50">
                    <TableCell>Tax Payable</TableCell>
                    <TableCell className="text-right">{formatAmount(taxPayable?.igst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(taxPayable?.cgst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(taxPayable?.sgst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(taxPayable?.cess)}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      ) : (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <Calculator className="h-12 w-12 mx-auto mb-4 text-slate-300" />
              <h3 className="text-lg font-medium mb-2">GSTR-3B Not Generated</h3>
              <p className="text-muted-foreground mb-4">
                Generate GSTR-3B from your vouchers to see the summary
              </p>
              <Button onClick={handleGenerate} disabled={generating}>
                {generating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Calculator className="mr-2 h-4 w-4" />
                    Generate GSTR-3B
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Actions */}
      {gstr3bData && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium">Filing Actions</h3>
                <p className="text-sm text-muted-foreground">
                  {status === 'GENERATED' && 'Review the data and submit to GSTN'}
                  {status === 'SUBMITTED' && 'File with EVC to complete the return'}
                  {status === 'FILED' && 'GSTR-3B has been successfully filed'}
                </p>
              </div>
              <div className="flex gap-3">
                {(status === 'NOT_GENERATED' || status === 'GENERATED' || status === 'DRAFT') && (
                  <Button onClick={handleGenerate} disabled={generating} variant="outline">
                    {generating ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Regenerate
                      </>
                    )}
                  </Button>
                )}
                {status === 'GENERATED' && (
                  <Button onClick={handleSubmit} disabled={submitting}>
                    {submitting ? (
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
                )}
                {status === 'SUBMITTED' && (
                  <Button onClick={() => setShowFilingDialog(true)}>
                    <CheckCircle className="mr-2 h-4 w-4" />
                    File with EVC
                  </Button>
                )}
                {status === 'FILED' && (
                  <Badge className="bg-green-100 text-green-700 px-4 py-2">
                    <CheckCircle className="mr-2 h-4 w-4" />
                    Filed Successfully
                  </Badge>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filing Dialog */}
      <Dialog open={showFilingDialog} onOpenChange={setShowFilingDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>File GSTR-3B with EVC</DialogTitle>
            <DialogDescription>
              Enter the authorized signatory's PAN and OTP to file the return.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="pan">PAN of Authorized Signatory</Label>
              <Input
                id="pan"
                value={pan}
                onChange={(e) => setPan(e.target.value.toUpperCase())}
                placeholder="Enter PAN"
                maxLength={10}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="filingOtp">OTP</Label>
              <Input
                id="filingOtp"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                placeholder="Enter OTP received"
                maxLength={6}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowFilingDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleFile} disabled={filing || !pan || !otp}>
              {filing ? (
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
