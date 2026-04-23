import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft,
  Scale,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  Loader2,
  Download,
  Filter,
  FileSpreadsheet,
  XCircle,
  Check,
  Search,
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { gstnApi, gstRegistrationsApi } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import { useActiveOrganizationId } from '@/stores/organizationStore';
import { format, subMonths } from 'date-fns';

interface ITCMismatch {
  id: string;
  supplier_gstin: string;
  supplier_name: string;
  invoice_number: string;
  invoice_date: string;
  book_taxable_value: number;
  book_igst: number;
  book_cgst: number;
  book_sgst: number;
  gstr2b_taxable_value: number;
  gstr2b_igst: number;
  gstr2b_cgst: number;
  gstr2b_sgst: number;
  variance_amount: number;
  mismatch_type: string;
  resolution_status: string;
  resolution_notes?: string;
}

interface ReconciliationSummary {
  total_book_value: number;
  total_gstr2b_value: number;
  matched_count: number;
  matched_value: number;
  missing_in_2b_count: number;
  missing_in_2b_value: number;
  missing_in_books_count: number;
  missing_in_books_value: number;
  amount_mismatch_count: number;
  amount_mismatch_variance: number;
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

const getMismatchTypeBadge = (type: string) => {
  const config: Record<string, { className: string; label: string }> = {
    MATCHED: { className: 'bg-green-100 text-green-700', label: 'Matched' },
    MISSING_IN_2B: { className: 'bg-red-100 text-red-700', label: 'Missing in GSTR-2B' },
    MISSING_IN_BOOKS: { className: 'bg-amber-100 text-amber-700', label: 'Missing in Books' },
    AMOUNT_MISMATCH: { className: 'bg-purple-100 text-purple-700', label: 'Amount Mismatch' },
    GSTIN_MISMATCH: { className: 'bg-orange-100 text-orange-700', label: 'GSTIN Mismatch' },
  };
  const { className, label } = config[type] || config.AMOUNT_MISMATCH;
  return <Badge className={className}>{label}</Badge>;
};

const getResolutionBadge = (status: string) => {
  const config: Record<string, { className: string; label: string }> = {
    PENDING: { className: 'bg-slate-100 text-slate-700', label: 'Pending' },
    ACCEPTED: { className: 'bg-green-100 text-green-700', label: 'Accepted' },
    REJECTED: { className: 'bg-red-100 text-red-700', label: 'Rejected' },
    UNDER_REVIEW: { className: 'bg-blue-100 text-blue-700', label: 'Under Review' },
    FOLLOW_UP: { className: 'bg-amber-100 text-amber-700', label: 'Follow Up' },
  };
  const { className, label } = config[status] || config.PENDING;
  return <Badge className={className}>{label}</Badge>;
};

export function ItcReconciliation() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  const activeOrganizationId = useActiveOrganizationId();
  const [gstin, setGstin] = useState(searchParams.get('gstin') || '');
  const [returnPeriod, setReturnPeriod] = useState(format(subMonths(new Date(), 1), 'MMyyyy'));
  const [loading, setLoading] = useState(false);
  const [fetching2b, setFetching2b] = useState(false);
  const [reconciling, setReconciling] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [summary, setSummary] = useState<ReconciliationSummary | null>(null);
  const [mismatches, setMismatches] = useState<ITCMismatch[]>([]);
  const [filteredType, setFilteredType] = useState<string>('all');
  const [filteredStatus, setFilteredStatus] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [registrations, setRegistrations] = useState<any[]>([]);
  const [selectedMismatch, setSelectedMismatch] = useState<ITCMismatch | null>(null);
  const [showResolveDialog, setShowResolveDialog] = useState(false);
  const [resolutionStatus, setResolutionStatus] = useState('');
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [resolving, setResolving] = useState(false);
  const [activeTab, setActiveTab] = useState('summary');

  useEffect(() => {
    fetchRegistrations();
  }, []);

  useEffect(() => {
    if (gstin && returnPeriod) {
      fetchMismatches();
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

  const fetchMismatches = async () => {
    setLoading(true);
    setError('');
    try {
      const params: any = { gstin, return_period: returnPeriod };
      if (filteredType !== 'all') params.mismatch_type = filteredType;
      if (filteredStatus !== 'all') params.resolution_status = filteredStatus;

      const response = await gstnApi.getMismatches(params);
      setMismatches(response.data.items || []);
      calculateSummary(response.data.items || []);
    } catch (err: any) {
      if (err.response?.status !== 404) {
        setError('Failed to fetch mismatches');
      }
      setMismatches([]);
      setSummary(null);
    } finally {
      setLoading(false);
    }
  };

  const calculateSummary = (data: ITCMismatch[]) => {
    const summary: ReconciliationSummary = {
      total_book_value: 0,
      total_gstr2b_value: 0,
      matched_count: 0,
      matched_value: 0,
      missing_in_2b_count: 0,
      missing_in_2b_value: 0,
      missing_in_books_count: 0,
      missing_in_books_value: 0,
      amount_mismatch_count: 0,
      amount_mismatch_variance: 0,
    };

    data.forEach(item => {
      summary.total_book_value += item.book_taxable_value || 0;
      summary.total_gstr2b_value += item.gstr2b_taxable_value || 0;

      switch (item.mismatch_type) {
        case 'MATCHED':
          summary.matched_count++;
          summary.matched_value += item.book_taxable_value || 0;
          break;
        case 'MISSING_IN_2B':
          summary.missing_in_2b_count++;
          summary.missing_in_2b_value += item.book_taxable_value || 0;
          break;
        case 'MISSING_IN_BOOKS':
          summary.missing_in_books_count++;
          summary.missing_in_books_value += item.gstr2b_taxable_value || 0;
          break;
        case 'AMOUNT_MISMATCH':
          summary.amount_mismatch_count++;
          summary.amount_mismatch_variance += Math.abs(item.variance_amount || 0);
          break;
      }
    });

    setSummary(summary);
  };

  const handleFetch2B = async () => {
    setFetching2b(true);
    setError('');
    setSuccess('');
    try {
      await gstnApi.fetchGstr2b(gstin, returnPeriod);
      setSuccess('GSTR-2B data fetched successfully');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch GSTR-2B');
    } finally {
      setFetching2b(false);
    }
  };

  const handleReconcile = async () => {
    setReconciling(true);
    setError('');
    setSuccess('');
    try {
      await gstnApi.runReconciliation(gstin, returnPeriod);
      setSuccess('Reconciliation completed successfully');
      await fetchMismatches();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to run reconciliation');
    } finally {
      setReconciling(false);
    }
  };

  const handleResolve = async () => {
    if (!selectedMismatch || !resolutionStatus) return;

    setResolving(true);
    try {
      await gstnApi.resolveMismatch(selectedMismatch.id, {
        resolution_status: resolutionStatus,
        resolution_notes: resolutionNotes,
      });
      setSuccess('Mismatch resolved successfully');
      setShowResolveDialog(false);
      setSelectedMismatch(null);
      setResolutionStatus('');
      setResolutionNotes('');
      await fetchMismatches();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to resolve mismatch');
    } finally {
      setResolving(false);
    }
  };

  const openResolveDialog = (mismatch: ITCMismatch) => {
    setSelectedMismatch(mismatch);
    setResolutionStatus(mismatch.resolution_status);
    setResolutionNotes(mismatch.resolution_notes || '');
    setShowResolveDialog(true);
  };

  const filteredMismatches = mismatches.filter(m => {
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      if (!m.supplier_gstin.toLowerCase().includes(search) &&
          !m.supplier_name?.toLowerCase().includes(search) &&
          !m.invoice_number?.toLowerCase().includes(search)) {
        return false;
      }
    }
    return true;
  });

  const pendingCount = mismatches.filter(m => m.resolution_status === 'PENDING').length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="ITC Reconciliation"
        subtitle="Match purchase records with GSTR-2B"
        breadcrumbs={[
          { label: 'GSTN Portal', to: '/admin/gst/gstn' },
          { label: 'ITC Reconciliation' },
        ]}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleFetch2B} disabled={fetching2b}>
              {fetching2b ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Fetching...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" />
                  Fetch GSTR-2B
                </>
              )}
            </Button>
            <Button onClick={handleReconcile} disabled={reconciling}>
              {reconciling ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Reconciling...
                </>
              ) : (
                <>
                  <Scale className="mr-2 h-4 w-4" />
                  Run Reconciliation
                </>
              )}
            </Button>
          </div>
        }
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
            <Button variant="outline" onClick={fetchMismatches} disabled={loading}>
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

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="mismatches">
            Mismatches
            {pendingCount > 0 && (
              <Badge className="ml-2 bg-red-100 text-red-700">{pendingCount}</Badge>
            )}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="summary" className="space-y-4">
          {/* Summary Cards */}
          {summary ? (
            <>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      Matched
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-green-600">{summary.matched_count}</div>
                    <p className="text-sm text-muted-foreground">{formatAmount(summary.matched_value)}</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                      <XCircle className="h-4 w-4 text-red-500" />
                      Missing in GSTR-2B
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-red-600">{summary.missing_in_2b_count}</div>
                    <p className="text-sm text-muted-foreground">{formatAmount(summary.missing_in_2b_value)}</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-amber-500" />
                      Missing in Books
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-amber-600">{summary.missing_in_books_count}</div>
                    <p className="text-sm text-muted-foreground">{formatAmount(summary.missing_in_books_value)}</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                      <AlertCircle className="h-4 w-4 text-purple-500" />
                      Amount Mismatch
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-purple-600">{summary.amount_mismatch_count}</div>
                    <p className="text-sm text-muted-foreground">Variance: {formatAmount(summary.amount_mismatch_variance)}</p>
                  </CardContent>
                </Card>
              </div>

              {/* Summary Table */}
              <Card>
                <CardHeader>
                  <CardTitle>Reconciliation Summary for {formatPeriod(returnPeriod)}</CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableBody>
                      <TableRow>
                        <TableCell className="font-medium">Total ITC as per Books</TableCell>
                        <TableCell className="text-right font-semibold">{formatAmount(summary.total_book_value)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell className="font-medium">Total ITC as per GSTR-2B</TableCell>
                        <TableCell className="text-right font-semibold">{formatAmount(summary.total_gstr2b_value)}</TableCell>
                      </TableRow>
                      <TableRow className="bg-slate-50">
                        <TableCell className="font-medium">Difference</TableCell>
                        <TableCell className="text-right font-semibold">
                          {formatAmount(summary.total_book_value - summary.total_gstr2b_value)}
                        </TableCell>
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
                  <Scale className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                  <h3 className="text-lg font-medium mb-2">No Reconciliation Data</h3>
                  <p className="text-muted-foreground mb-4">
                    Fetch GSTR-2B and run reconciliation to compare with your books
                  </p>
                  <div className="flex gap-2 justify-center">
                    <Button variant="outline" onClick={handleFetch2B} disabled={fetching2b}>
                      <Download className="mr-2 h-4 w-4" />
                      Fetch GSTR-2B
                    </Button>
                    <Button onClick={handleReconcile} disabled={reconciling}>
                      <Scale className="mr-2 h-4 w-4" />
                      Run Reconciliation
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="mismatches" className="space-y-4">
          {/* Mismatch Filters */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      placeholder="Search by GSTIN, supplier name, or invoice..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                </div>
                <div className="w-48">
                  <Select value={filteredType} onValueChange={setFilteredType}>
                    <SelectTrigger>
                      <SelectValue placeholder="Mismatch Type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      <SelectItem value="MISSING_IN_2B">Missing in GSTR-2B</SelectItem>
                      <SelectItem value="MISSING_IN_BOOKS">Missing in Books</SelectItem>
                      <SelectItem value="AMOUNT_MISMATCH">Amount Mismatch</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="w-48">
                  <Select value={filteredStatus} onValueChange={setFilteredStatus}>
                    <SelectTrigger>
                      <SelectValue placeholder="Resolution Status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Status</SelectItem>
                      <SelectItem value="PENDING">Pending</SelectItem>
                      <SelectItem value="ACCEPTED">Accepted</SelectItem>
                      <SelectItem value="REJECTED">Rejected</SelectItem>
                      <SelectItem value="UNDER_REVIEW">Under Review</SelectItem>
                      <SelectItem value="FOLLOW_UP">Follow Up</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button variant="outline" onClick={fetchMismatches}>
                  <Filter className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Mismatch Table */}
          <Card>
            <CardHeader>
              <CardTitle>ITC Mismatches</CardTitle>
              <CardDescription>
                {filteredMismatches.length} records found for {formatPeriod(returnPeriod)}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                </div>
              ) : filteredMismatches.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-500" />
                  <p>No mismatches found. All records are reconciled!</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Supplier</TableHead>
                      <TableHead>Invoice</TableHead>
                      <TableHead className="text-right">Book Value</TableHead>
                      <TableHead className="text-right">GSTR-2B Value</TableHead>
                      <TableHead className="text-right">Variance</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="w-[70px]">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredMismatches.map((mismatch) => (
                      <TableRow key={mismatch.id}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{mismatch.supplier_name}</p>
                            <p className="text-sm text-muted-foreground font-mono">{mismatch.supplier_gstin}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{mismatch.invoice_number}</p>
                            <p className="text-sm text-muted-foreground">
                              {mismatch.invoice_date ? format(new Date(mismatch.invoice_date), 'dd MMM yyyy') : '-'}
                            </p>
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          {formatAmount(mismatch.book_taxable_value)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatAmount(mismatch.gstr2b_taxable_value)}
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          <span className={mismatch.variance_amount > 0 ? 'text-red-600' : mismatch.variance_amount < 0 ? 'text-amber-600' : ''}>
                            {formatAmount(mismatch.variance_amount)}
                          </span>
                        </TableCell>
                        <TableCell>{getMismatchTypeBadge(mismatch.mismatch_type)}</TableCell>
                        <TableCell>{getResolutionBadge(mismatch.resolution_status)}</TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openResolveDialog(mismatch)}
                          >
                            Resolve
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Resolve Dialog */}
      <Dialog open={showResolveDialog} onOpenChange={setShowResolveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Resolve Mismatch</DialogTitle>
            <DialogDescription>
              Update the resolution status for this ITC mismatch
            </DialogDescription>
          </DialogHeader>
          {selectedMismatch && (
            <div className="space-y-4 py-4">
              <div className="p-3 bg-slate-50 rounded-lg space-y-2">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Supplier</span>
                  <span className="font-medium">{selectedMismatch.supplier_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Invoice</span>
                  <span className="font-medium">{selectedMismatch.invoice_number}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Variance</span>
                  <span className="font-medium">{formatAmount(selectedMismatch.variance_amount)}</span>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Resolution Status</Label>
                <Select value={resolutionStatus} onValueChange={setResolutionStatus}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="PENDING">Pending</SelectItem>
                    <SelectItem value="ACCEPTED">Accepted (Claim ITC)</SelectItem>
                    <SelectItem value="REJECTED">Rejected (Do not claim)</SelectItem>
                    <SelectItem value="UNDER_REVIEW">Under Review</SelectItem>
                    <SelectItem value="FOLLOW_UP">Follow Up with Supplier</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  placeholder="Add notes about the resolution..."
                  rows={3}
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowResolveDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleResolve} disabled={resolving || !resolutionStatus}>
              {resolving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Check className="mr-2 h-4 w-4" />
                  Save Resolution
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default ItcReconciliation;
