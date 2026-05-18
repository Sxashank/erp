/**
 * Customer Portal - Documents Page
 * View and download loan documents, statements, certificates
 */

import type { File } from 'lucide-react';
import {
  FileText,
  Download,
  Loader2,
  FileCheck,
  Calendar,
  Search,
  Filter,
  Eye,
  IndianRupee,
  Upload,
} from 'lucide-react';
import { useState, useEffect } from 'react';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import { portalDocumentApi, portalDashboardApi } from '@/services/portalApi';
import type { PortalDocument, LoanSummary } from '@/types/portal';

import { logger } from "@/lib/logger";
const documentTypeLabels: Record<string, string> = {
  SANCTION_LETTER: 'Sanction Letter',
  LOAN_AGREEMENT: 'Loan Agreement',
  WELCOME_KIT: 'Welcome Kit',
  REPAYMENT_SCHEDULE: 'Repayment Schedule',
  NOC: 'No Objection Certificate',
  FORECLOSURE_LETTER: 'Foreclosure Letter',
  STATEMENT: 'Account Statement',
  INTEREST_CERTIFICATE: 'Interest Certificate',
  TDS_CERTIFICATE: 'TDS Certificate (Form 16A)',
};

const documentTypeIcons: Record<string, string> = {
  SANCTION_LETTER: 'bg-emerald-100 text-emerald-600',
  LOAN_AGREEMENT: 'bg-blue-100 text-blue-600',
  WELCOME_KIT: 'bg-purple-100 text-purple-600',
  REPAYMENT_SCHEDULE: 'bg-orange-100 text-orange-600',
  NOC: 'bg-green-100 text-green-600',
  FORECLOSURE_LETTER: 'bg-red-100 text-red-600',
  STATEMENT: 'bg-gray-100 text-gray-600',
  INTEREST_CERTIFICATE: 'bg-yellow-100 text-yellow-600',
  TDS_CERTIFICATE: 'bg-indigo-100 text-indigo-600',
};

export default function PortalDocuments() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [documents, setDocuments] = useState<PortalDocument[]>([]);
  const [loans, setLoans] = useState<LoanSummary[]>([]);
  const [selectedLoan, setSelectedLoan] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [downloading, setDownloading] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('documents');

  // Per-loan upload state — see CLAUDE.md §6.3: every mutation carries an
  // Idempotency-Key. The portalDocumentApi.uploadForLoan helper below
  // builds one for us. The BE accepts multipart/form-data.
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadLoanId, setUploadLoanId] = useState<string>('');
  const [uploadType, setUploadType] = useState<string>('SUPPORTING_DOCUMENT');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  // Statement generation
  const [statementLoan, setStatementLoan] = useState('');
  const [statementFromDate, setStatementFromDate] = useState('');
  const [statementToDate, setStatementToDate] = useState('');
  const [generatingStatement, setGeneratingStatement] = useState(false);

  // Interest certificate
  const [certLoan, setCertLoan] = useState('');
  const [certYear, setCertYear] = useState('');
  const [generatingCert, setGeneratingCert] = useState(false);

  // TDS certificate
  const [tdsYear, setTdsYear] = useState('');
  const [generatingTds, setGeneratingTds] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [docsRes, loansRes] = await Promise.all([
        portalDocumentApi.getDocuments(),
        portalDashboardApi.getLoans(),
      ]);
      setDocuments(docsRes.data);
      setLoans(loansRes.data);
    } catch (error) {
      logger.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (document: PortalDocument) => {
    if (!document.is_downloadable) return;

    setDownloading(document.id);
    try {
      const response = await portalDocumentApi.downloadDocument(document.id);
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const a = window.document.createElement('a');
      a.href = url;
      a.download = document.document_name;
      window.document.body.appendChild(a);
      a.click();
      window.document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      logger.error('Failed to download document:', error);
    } finally {
      setDownloading(null);
    }
  };

  const handleGenerateStatement = async () => {
    if (!statementLoan || !statementFromDate || !statementToDate) return;

    setGeneratingStatement(true);
    try {
      const response = await portalDocumentApi.getStatement({
        loan_account_id: statementLoan,
        from_date: statementFromDate,
        to_date: statementToDate,
      });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = window.document.createElement('a');
      a.href = url;
      a.download = `statement_${statementLoan}_${statementFromDate}_${statementToDate}.pdf`;
      window.document.body.appendChild(a);
      a.click();
      window.document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      logger.error('Failed to generate statement:', error);
    } finally {
      setGeneratingStatement(false);
    }
  };

  const handleGenerateInterestCert = async () => {
    if (!certLoan || !certYear) return;

    setGeneratingCert(true);
    try {
      const response = await portalDocumentApi.getInterestCertificate({
        loan_account_id: certLoan,
        financial_year: certYear,
      });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = window.document.createElement('a');
      a.href = url;
      a.download = `interest_certificate_${certYear}.pdf`;
      window.document.body.appendChild(a);
      a.click();
      window.document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      logger.error('Failed to generate interest certificate:', error);
    } finally {
      setGeneratingCert(false);
    }
  };

  const handleGenerateTdsCert = async () => {
    if (!tdsYear) return;

    setGeneratingTds(true);
    try {
      const response = await portalDocumentApi.getTdsCertificate({
        financial_year: tdsYear,
      });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = window.document.createElement('a');
      a.href = url;
      a.download = `tds_certificate_${tdsYear}.pdf`;
      window.document.body.appendChild(a);
      a.click();
      window.document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      logger.error('Failed to generate TDS certificate:', error);
    } finally {
      setGeneratingTds(false);
    }
  };

  const handleUpload = async () => {
    if (!uploadFile || !uploadLoanId) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('document_type', uploadType);
      formData.append('loan_account_id', uploadLoanId);
      // The portal documents endpoint accepts multipart uploads keyed by
      // loan_account_id. Idempotency-Key is set per CLAUDE.md §6.3.
      const idempotencyKey = crypto.randomUUID();
      await (
        await import('@/services/api')
      ).default.post('/portal/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Idempotency-Key': idempotencyKey,
        },
      });
      toast({
        title: 'Document uploaded',
        description: 'Your document is now available for the operations team.',
      });
      setUploadOpen(false);
      setUploadFile(null);
      // Refresh the docs list.
      const docsRes = await portalDocumentApi.getDocuments();
      setDocuments(docsRes.data);
    } catch (err) {
      showErrorToast(err, toast);
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const filteredDocuments = documents.filter((doc) => {
    const matchesLoan = selectedLoan === 'all' || doc.loan_account_id === selectedLoan;
    const matchesSearch =
      !searchQuery ||
      doc.document_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      documentTypeLabels[doc.document_type]?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesLoan && matchesSearch;
  });

  const getCurrentFY = () => {
    const now = new Date();
    const year = now.getMonth() >= 3 ? now.getFullYear() : now.getFullYear() - 1;
    return `${year}-${(year + 1).toString().slice(-2)}`;
  };

  const financialYears = Array.from({ length: 5 }, (_, i) => {
    const year = new Date().getFullYear() - i;
    return `${year - 1}-${year.toString().slice(-2)}`;
  });

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Documents"
        subtitle="Download your loan documents, statements, and certificates"
        actions={
          <Button
            onClick={() => {
              setUploadLoanId(loans[0]?.id ?? '');
              setUploadFile(null);
              setUploadOpen(true);
            }}
            className="bg-emerald-600 hover:bg-emerald-700"
            disabled={loans.length === 0}
          >
            <Upload className="mr-2 h-4 w-4" />
            Upload document
          </Button>
        }
      />

      <Dialog open={uploadOpen} onOpenChange={setUploadOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Upload document</DialogTitle>
            <DialogDescription>
              Attach a document to a specific loan account. Our operations team will pick it up
              automatically.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label>Loan account</Label>
              <Select value={uploadLoanId} onValueChange={setUploadLoanId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a loan" />
                </SelectTrigger>
                <SelectContent>
                  {loans.map((l) => (
                    <SelectItem key={l.id} value={l.id}>
                      {l.loan_account_number}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Document type</Label>
              <Select value={uploadType} onValueChange={setUploadType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="BOARD_RESOLUTION">Board resolution</SelectItem>
                  <SelectItem value="FINANCIAL_STATEMENT">Financial statement</SelectItem>
                  <SelectItem value="PROJECT_PROPOSAL">Project proposal</SelectItem>
                  <SelectItem value="SUPPORTING_DOCUMENT">Supporting document</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>File</Label>
              <Input type="file" onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setUploadOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleUpload}
              disabled={uploading || !uploadFile || !uploadLoanId}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              {uploading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Upload className="mr-2 h-4 w-4" />
              )}
              Upload
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="documents">My Documents</TabsTrigger>
          <TabsTrigger value="generate">Generate Documents</TabsTrigger>
        </TabsList>

        <TabsContent value="documents" className="space-y-4">
          {/* Filters */}
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-col gap-4 md:flex-row">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                  <Input
                    placeholder="Search documents..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <Select value={selectedLoan} onValueChange={setSelectedLoan}>
                  <SelectTrigger className="w-full md:w-[250px]">
                    <SelectValue placeholder="Filter by loan" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Loans</SelectItem>
                    {loans.map((loan) => (
                      <SelectItem key={loan.id} value={loan.id}>
                        {loan.loan_account_number}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Documents List */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Available Documents</CardTitle>
              <CardDescription>{filteredDocuments.length} document(s) found</CardDescription>
            </CardHeader>
            <CardContent>
              {filteredDocuments.length > 0 ? (
                <div className="divide-y">
                  {filteredDocuments.map((doc) => (
                    <div
                      key={doc.id}
                      className="flex items-center justify-between py-4 first:pt-0 last:pb-0"
                    >
                      <div className="flex items-center gap-4">
                        <div
                          className={`rounded-lg p-3 ${
                            documentTypeIcons[doc.document_type] || 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          <FileText className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="font-medium">{doc.document_name}</p>
                          <div className="flex items-center gap-2 text-sm text-gray-500">
                            <span>
                              {documentTypeLabels[doc.document_type] || doc.document_type}
                            </span>
                            {doc.loan_account_number && (
                              <>
                                <span>•</span>
                                <span>{doc.loan_account_number}</span>
                              </>
                            )}
                            <span>•</span>
                            <span>{formatFileSize(doc.file_size)}</span>
                          </div>
                          <p className="text-xs text-gray-400">
                            Uploaded: <DateDisplay date={doc.uploaded_at} />
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {doc.is_downloadable ? (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDownload(doc)}
                            disabled={downloading === doc.id}
                          >
                            {downloading === doc.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Download className="h-4 w-4" />
                            )}
                          </Button>
                        ) : (
                          <Badge variant="secondary">Not Available</Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-12 text-center text-gray-500">
                  <FileText className="mx-auto mb-4 h-12 w-12 opacity-50" />
                  <p>No documents found</p>
                  {searchQuery && (
                    <Button variant="link" onClick={() => setSearchQuery('')}>
                      Clear search
                    </Button>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="generate" className="space-y-6">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {/* Account Statement */}
            <Card>
              <CardHeader>
                <div className="w-fit rounded-lg bg-gray-100 p-3">
                  <FileText className="h-5 w-5 text-gray-600" />
                </div>
                <CardTitle className="text-base">Account Statement</CardTitle>
                <CardDescription>
                  Generate detailed account statement for a specific period
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Loan Account</Label>
                  <Select value={statementLoan} onValueChange={setStatementLoan}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select loan" />
                    </SelectTrigger>
                    <SelectContent>
                      {loans.map((loan) => (
                        <SelectItem key={loan.id} value={loan.id}>
                          {loan.loan_account_number}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>From Date</Label>
                    <Input
                      type="date"
                      value={statementFromDate}
                      onChange={(e) => setStatementFromDate(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>To Date</Label>
                    <Input
                      type="date"
                      value={statementToDate}
                      onChange={(e) => setStatementToDate(e.target.value)}
                    />
                  </div>
                </div>
                <Button
                  className="w-full"
                  onClick={handleGenerateStatement}
                  disabled={
                    !statementLoan || !statementFromDate || !statementToDate || generatingStatement
                  }
                >
                  {generatingStatement ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Download className="mr-2 h-4 w-4" />
                      Download Statement
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Interest Certificate */}
            <Card>
              <CardHeader>
                <div className="w-fit rounded-lg bg-yellow-100 p-3">
                  <IndianRupee className="h-5 w-5 text-yellow-600" />
                </div>
                <CardTitle className="text-base">Interest Certificate</CardTitle>
                <CardDescription>
                  Certificate for claiming tax deduction on home loan interest
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Loan Account</Label>
                  <Select value={certLoan} onValueChange={setCertLoan}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select loan" />
                    </SelectTrigger>
                    <SelectContent>
                      {loans.map((loan) => (
                        <SelectItem key={loan.id} value={loan.id}>
                          {loan.loan_account_number}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Financial Year</Label>
                  <Select value={certYear} onValueChange={setCertYear}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select FY" />
                    </SelectTrigger>
                    <SelectContent>
                      {financialYears.map((fy) => (
                        <SelectItem key={fy} value={fy}>
                          FY {fy}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button
                  className="w-full"
                  onClick={handleGenerateInterestCert}
                  disabled={!certLoan || !certYear || generatingCert}
                >
                  {generatingCert ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Download className="mr-2 h-4 w-4" />
                      Download Certificate
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* TDS Certificate */}
            <Card>
              <CardHeader>
                <div className="w-fit rounded-lg bg-indigo-100 p-3">
                  <FileCheck className="h-5 w-5 text-indigo-600" />
                </div>
                <CardTitle className="text-base">TDS Certificate (Form 16A)</CardTitle>
                <CardDescription>
                  Certificate of TDS deducted on interest paid to you
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Financial Year</Label>
                  <Select value={tdsYear} onValueChange={setTdsYear}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select FY" />
                    </SelectTrigger>
                    <SelectContent>
                      {financialYears.map((fy) => (
                        <SelectItem key={fy} value={fy}>
                          FY {fy}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button
                  className="w-full"
                  onClick={handleGenerateTdsCert}
                  disabled={!tdsYear || generatingTds}
                >
                  {generatingTds ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Download className="mr-2 h-4 w-4" />
                      Download Certificate
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
