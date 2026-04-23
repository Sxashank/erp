import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft,
  FileSpreadsheet,
  RefreshCw,
  Download,
  Upload,
  CheckCircle,
  AlertCircle,
  Clock,
  Building2,
  Users,
  Loader2,
  FileText,
  Send,
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { gstnApi, gstRegistrationsApi } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import { useActiveOrganizationId } from '@/stores/organizationStore';
import { format, subMonths } from 'date-fns';

interface GSTR1Section {
  section: string;
  description: string;
  invoiceCount: number;
  taxableValue: number;
  igst: number;
  cgst: number;
  sgst: number;
  cess: number;
}

const formatAmount = (amount: number) => {
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

export function Gstr1Filing() {
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
  const [gstr1Data, setGstr1Data] = useState<any>(null);
  const [sections, setSections] = useState<GSTR1Section[]>([]);
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
      fetchGstr1Data();
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

  const fetchGstr1Data = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await gstnApi.getGstr1(gstin, returnPeriod);
      if (response.data) {
        setGstr1Data(response.data);
        setStatus(response.data.status || 'GENERATED');
        processGstr1Sections(response.data);
      } else {
        setGstr1Data(null);
        setStatus('NOT_GENERATED');
        setSections([]);
      }
    } catch (err: any) {
      if (err.response?.status === 404) {
        setGstr1Data(null);
        setStatus('NOT_GENERATED');
        setSections([]);
      } else {
        setError('Failed to fetch GSTR-1 data');
      }
    } finally {
      setLoading(false);
    }
  };

  const processGstr1Sections = (data: any) => {
    const sectionData: GSTR1Section[] = [
      {
        section: 'B2B',
        description: 'B2B Invoices (Taxable)',
        invoiceCount: data.b2b_invoices?.length || 0,
        taxableValue: data.b2b_summary?.taxable_value || 0,
        igst: data.b2b_summary?.igst_amount || 0,
        cgst: data.b2b_summary?.cgst_amount || 0,
        sgst: data.b2b_summary?.sgst_amount || 0,
        cess: data.b2b_summary?.cess_amount || 0,
      },
      {
        section: 'B2CL',
        description: 'B2C Large Invoices (>2.5L)',
        invoiceCount: data.b2cl_invoices?.length || 0,
        taxableValue: data.b2cl_summary?.taxable_value || 0,
        igst: data.b2cl_summary?.igst_amount || 0,
        cgst: 0,
        sgst: 0,
        cess: data.b2cl_summary?.cess_amount || 0,
      },
      {
        section: 'B2CS',
        description: 'B2C Small Invoices',
        invoiceCount: data.b2cs_count || 0,
        taxableValue: data.b2cs_summary?.taxable_value || 0,
        igst: data.b2cs_summary?.igst_amount || 0,
        cgst: data.b2cs_summary?.cgst_amount || 0,
        sgst: data.b2cs_summary?.sgst_amount || 0,
        cess: data.b2cs_summary?.cess_amount || 0,
      },
      {
        section: 'CDNR',
        description: 'Credit/Debit Notes (Registered)',
        invoiceCount: data.cdnr_count || 0,
        taxableValue: data.cdnr_summary?.taxable_value || 0,
        igst: data.cdnr_summary?.igst_amount || 0,
        cgst: data.cdnr_summary?.cgst_amount || 0,
        sgst: data.cdnr_summary?.sgst_amount || 0,
        cess: data.cdnr_summary?.cess_amount || 0,
      },
      {
        section: 'EXP',
        description: 'Export Invoices',
        invoiceCount: data.exp_invoices?.length || 0,
        taxableValue: data.exp_summary?.taxable_value || 0,
        igst: data.exp_summary?.igst_amount || 0,
        cgst: 0,
        sgst: 0,
        cess: 0,
      },
    ];
    setSections(sectionData);
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setError('');
    setSuccess('');
    try {
      await gstnApi.generateGstr1(gstin, returnPeriod, { regenerate: status !== 'NOT_GENERATED' });
      setSuccess('GSTR-1 generated successfully');
      await fetchGstr1Data();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate GSTR-1');
    } finally {
      setGenerating(false);
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError('');
    setSuccess('');
    try {
      await gstnApi.submitGstr1(gstin, returnPeriod);
      setSuccess('GSTR-1 submitted successfully');
      await fetchGstr1Data();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit GSTR-1');
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
      await gstnApi.fileGstr1(gstin, returnPeriod, { pan, otp });
      setSuccess('GSTR-1 filed successfully!');
      setShowFilingDialog(false);
      await fetchGstr1Data();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to file GSTR-1');
    } finally {
      setFiling(false);
    }
  };

  const getStatusBadge = () => {
    const statusConfig: Record<string, { className: string; label: string; icon: any }> = {
      NOT_GENERATED: { className: 'bg-slate-100 text-slate-700', label: 'Not Generated', icon: Clock },
      DRAFT: { className: 'bg-slate-100 text-slate-700', label: 'Draft', icon: FileText },
      GENERATED: { className: 'bg-blue-100 text-blue-700', label: 'Generated', icon: FileSpreadsheet },
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

  const totalTaxableValue = sections.reduce((sum, s) => sum + s.taxableValue, 0);
  const totalIGST = sections.reduce((sum, s) => sum + s.igst, 0);
  const totalCGST = sections.reduce((sum, s) => sum + s.cgst, 0);
  const totalSGST = sections.reduce((sum, s) => sum + s.sgst, 0);
  const totalCess = sections.reduce((sum, s) => sum + s.cess, 0);
  const totalTax = totalIGST + totalCGST + totalSGST + totalCess;

  return (
    <div className="space-y-6">
      <PageHeader
        title="GSTR-1 Filing"
        subtitle="Outward supplies return"
        breadcrumbs={[
          { label: 'GSTN Portal', to: '/admin/gst/gstn' },
          { label: 'GSTR-1' },
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
            <Button variant="outline" onClick={fetchGstr1Data} disabled={loading}>
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
            <CardTitle className="text-sm font-medium">Taxable Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatAmount(totalTaxableValue)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">IGST</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{formatAmount(totalIGST)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">CGST + SGST</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{formatAmount(totalCGST + totalSGST)}</div>
            <p className="text-xs text-muted-foreground">
              CGST: {formatAmount(totalCGST)} | SGST: {formatAmount(totalSGST)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Tax</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">{formatAmount(totalTax)}</div>
          </CardContent>
        </Card>
      </div>

      {/* Sections Table */}
      <Card>
        <CardHeader>
          <CardTitle>GSTR-1 Sections for {formatPeriod(returnPeriod)}</CardTitle>
          <CardDescription>Summary of outward supplies by section</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Section</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Invoices</TableHead>
                  <TableHead className="text-right">Taxable Value</TableHead>
                  <TableHead className="text-right">IGST</TableHead>
                  <TableHead className="text-right">CGST</TableHead>
                  <TableHead className="text-right">SGST</TableHead>
                  <TableHead className="text-right">Cess</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sections.map((section) => (
                  <TableRow key={section.section}>
                    <TableCell className="font-medium">{section.section}</TableCell>
                    <TableCell>{section.description}</TableCell>
                    <TableCell className="text-right">{section.invoiceCount}</TableCell>
                    <TableCell className="text-right">{formatAmount(section.taxableValue)}</TableCell>
                    <TableCell className="text-right">{formatAmount(section.igst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(section.cgst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(section.sgst)}</TableCell>
                    <TableCell className="text-right">{formatAmount(section.cess)}</TableCell>
                  </TableRow>
                ))}
                <TableRow className="font-semibold bg-slate-50">
                  <TableCell colSpan={3}>Total</TableCell>
                  <TableCell className="text-right">{formatAmount(totalTaxableValue)}</TableCell>
                  <TableCell className="text-right">{formatAmount(totalIGST)}</TableCell>
                  <TableCell className="text-right">{formatAmount(totalCGST)}</TableCell>
                  <TableCell className="text-right">{formatAmount(totalSGST)}</TableCell>
                  <TableCell className="text-right">{formatAmount(totalCess)}</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Actions */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium">Filing Actions</h3>
              <p className="text-sm text-muted-foreground">
                {status === 'NOT_GENERATED' && 'Generate GSTR-1 from your sales invoices'}
                {status === 'GENERATED' && 'Review the data and submit to GSTN'}
                {status === 'SUBMITTED' && 'File with EVC to complete the return'}
                {status === 'FILED' && 'GSTR-1 has been successfully filed'}
              </p>
            </div>
            <div className="flex gap-3">
              {(status === 'NOT_GENERATED' || status === 'GENERATED' || status === 'DRAFT') && (
                <Button onClick={handleGenerate} disabled={generating}>
                  {generating ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4" />
                      {status === 'NOT_GENERATED' ? 'Generate' : 'Regenerate'}
                    </>
                  )}
                </Button>
              )}
              {status === 'GENERATED' && (
                <Button onClick={handleSubmit} disabled={submitting} variant="secondary">
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

      {/* Filing Dialog */}
      <Dialog open={showFilingDialog} onOpenChange={setShowFilingDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>File GSTR-1 with EVC</DialogTitle>
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
              <p className="text-xs text-muted-foreground">
                OTP will be sent to the registered mobile number
              </p>
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

export default Gstr1Filing;
