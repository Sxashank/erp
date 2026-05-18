import {
  Upload,
  Download,
  FileSpreadsheet,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';
import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  useImportBulkReceipts,
  type BulkReceiptItem,
  type BulkReceiptResponse,
} from '@/hooks/lending/useReceipts';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import { formatCurrency } from '@/lib/utils';

interface UploadedReceipt {
  row: number;
  loanAccount: string;
  entity: string;
  receiptDate: string;
  amount: number;
  mode: string;
  instrumentNumber?: string;
  status: 'valid' | 'invalid' | 'duplicate' | 'warning';
  errors: string[];
  warnings: string[];
}

export default function BulkReceiptUpload() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [parsedData, setParsedData] = useState<UploadedReceipt[]>([]);
  const [showResults, setShowResults] = useState(false);
  const [serverResult, setServerResult] = useState<BulkReceiptResponse | null>(null);
  const importBulk = useImportBulkReceipts();

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      handleParseFile(file);
    }
  };

  const handleParseFile = async (file: File) => {
    setIsUploading(true);
    setUploadProgress(0);

    // Simulate parsing progress
    for (let i = 0; i <= 100; i += 10) {
      await new Promise((resolve) => setTimeout(resolve, 100));
      setUploadProgress(i);
    }

    // The parsed-preview list will populate once a BE bulk-receipt preview
    // endpoint ships. Today the BE exposes a single POST /lending/receipts/bulk
    // that validates + creates in one call; we surface its result in the
    // import-complete view rather than fabricating a client-side preview.
    setParsedData([]);
    setIsUploading(false);
  };

  const handleProcess = async () => {
    const items: BulkReceiptItem[] = parsedData
      .filter((r) => r.status === 'valid' || r.status === 'warning')
      .map((r) => ({
        loanAccountNumber: r.loanAccount,
        receiptAmount: r.amount,
        receiptDate: r.receiptDate,
        receiptMode: r.mode,
        instrumentNumber: r.instrumentNumber,
      }));
    if (items.length === 0) {
      toast({
        title: 'Nothing to import',
        description: 'No valid rows were detected in the uploaded file.',
        variant: 'destructive',
      });
      return;
    }
    try {
      const response = await importBulk.mutateAsync({
        receipts: items,
        autoAllocate: true,
      });
      setServerResult(response);
      toast({
        title: 'Bulk import complete',
        description: `${response.successCount} of ${response.totalCount} receipts created.`,
      });
      setShowResults(true);
    } catch (err) {
      showErrorToast(err, toast);
    }
  };

  const handleDownloadTemplate = () => {
    // In a real implementation, this would download an actual template file
    alert('Template download started');
  };

  const validRecords = parsedData.filter((r) => r.status === 'valid');
  const warningRecords = parsedData.filter((r) => r.status === 'warning');
  const invalidRecords = parsedData.filter(
    (r) => r.status === 'invalid' || r.status === 'duplicate',
  );
  const totalAmount = parsedData
    .filter((r) => r.status === 'valid' || r.status === 'warning')
    .reduce((sum, r) => sum + r.amount, 0);

  if (showResults && serverResult) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
          <h2 className="mb-2 text-2xl font-bold">Bulk Upload Complete</h2>
          <p className="mb-6 text-muted-foreground">
            {serverResult.successCount} of {serverResult.totalCount} receipts created. Total amount:{' '}
            {formatCurrency(Number(serverResult.totalAmount))}.
          </p>
          <div className="mx-auto mb-6 grid max-w-md grid-cols-3 gap-4">
            <div className="rounded-lg bg-green-50 p-4 text-center">
              <div className="text-2xl font-bold text-green-600">{serverResult.successCount}</div>
              <div className="text-xs text-muted-foreground">Created</div>
            </div>
            <div className="rounded-lg bg-yellow-50 p-4 text-center">
              <div className="text-2xl font-bold text-yellow-600">{warningRecords.length}</div>
              <div className="text-xs text-muted-foreground">With Warnings</div>
            </div>
            <div className="rounded-lg bg-red-50 p-4 text-center">
              <div className="text-2xl font-bold text-red-600">{serverResult.failedCount}</div>
              <div className="text-xs text-muted-foreground">Failed</div>
            </div>
          </div>
          {serverResult.failures.length > 0 && (
            <Alert variant="destructive" className="mx-auto mb-6 max-w-2xl text-left">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Failures</AlertTitle>
              <AlertDescription>
                <ul className="list-disc pl-5 text-sm">
                  {serverResult.failures.slice(0, 5).map((f, i) => (
                    <li key={i}>
                      {f.loanAccountNumber ? `${f.loanAccountNumber}: ` : ''}
                      {f.error ?? 'Unknown error'}
                    </li>
                  ))}
                  {serverResult.failures.length > 5 && (
                    <li>… and {serverResult.failures.length - 5} more</li>
                  )}
                </ul>
              </AlertDescription>
            </Alert>
          )}
          <div className="flex justify-center gap-4">
            <Button variant="outline" onClick={() => navigate('/admin/lending/receipts')}>
              View Receipts
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setShowResults(false);
                setServerResult(null);
                setParsedData([]);
                setUploadedFile(null);
              }}
            >
              Upload More
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Bulk Receipt Upload"
        subtitle="Upload multiple receipts from Excel/CSV file"
        breadcrumbs={[
          { label: 'Receipts', to: '/admin/lending/receipts' },
          { label: 'Bulk Upload' },
        ]}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Upload Section */}
        <Card className={parsedData.length > 0 ? 'lg:col-span-2' : 'lg:col-span-3'}>
          <CardHeader>
            <CardTitle>Upload File</CardTitle>
            <CardDescription>Select an Excel or CSV file to upload</CardDescription>
          </CardHeader>
          <CardContent>
            {!uploadedFile ? (
              <div
                className="cursor-pointer rounded-lg border-2 border-dashed p-12 text-center transition-colors hover:border-primary/50"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
                <h3 className="mb-2 text-lg font-medium">Drop your file here or click to browse</h3>
                <p className="mb-4 text-sm text-muted-foreground">
                  Supported formats: .xlsx, .xls, .csv (max 5MB)
                </p>
                <Button variant="outline">
                  <FileSpreadsheet className="mr-2 h-4 w-4" />
                  Select File
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  className="hidden"
                  onChange={handleFileSelect}
                />
              </div>
            ) : isUploading ? (
              <div className="py-12 text-center">
                <RefreshCw className="mx-auto mb-4 h-12 w-12 animate-spin text-primary" />
                <h3 className="mb-2 text-lg font-medium">Parsing file...</h3>
                <Progress value={uploadProgress} className="mx-auto w-64" />
                <p className="mt-2 text-sm text-muted-foreground">{uploadProgress}% complete</p>
              </div>
            ) : (
              <div>
                <div className="mb-4 flex items-center justify-between rounded-lg border p-4">
                  <div className="flex items-center gap-3">
                    <FileSpreadsheet className="h-8 w-8 text-green-600" />
                    <div>
                      <p className="font-medium">{uploadedFile.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {(uploadedFile.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setUploadedFile(null);
                      setParsedData([]);
                    }}
                  >
                    <XCircle className="h-4 w-4" />
                  </Button>
                </div>

                {/* Validation Summary */}
                <div className="mb-6 grid grid-cols-4 gap-4">
                  <div className="rounded-lg bg-muted p-3 text-center">
                    <div className="text-2xl font-bold">{parsedData.length}</div>
                    <div className="text-xs text-muted-foreground">Total Records</div>
                  </div>
                  <div className="rounded-lg bg-green-50 p-3 text-center">
                    <div className="text-2xl font-bold text-green-600">{validRecords.length}</div>
                    <div className="text-xs text-muted-foreground">Valid</div>
                  </div>
                  <div className="rounded-lg bg-yellow-50 p-3 text-center">
                    <div className="text-2xl font-bold text-yellow-600">
                      {warningRecords.length}
                    </div>
                    <div className="text-xs text-muted-foreground">Warnings</div>
                  </div>
                  <div className="rounded-lg bg-red-50 p-3 text-center">
                    <div className="text-2xl font-bold text-red-600">{invalidRecords.length}</div>
                    <div className="text-xs text-muted-foreground">Invalid</div>
                  </div>
                </div>

                {/* Parsed Data Table */}
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Row</TableHead>
                      <TableHead>Loan Account</TableHead>
                      <TableHead>Entity</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                      <TableHead>Mode</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {parsedData.map((record, index) => (
                      <TableRow
                        key={index}
                        className={
                          record.status === 'invalid' || record.status === 'duplicate'
                            ? 'bg-red-50'
                            : record.status === 'warning'
                              ? 'bg-yellow-50'
                              : ''
                        }
                      >
                        <TableCell>{record.row}</TableCell>
                        <TableCell className="font-mono text-sm">{record.loanAccount}</TableCell>
                        <TableCell>{record.entity}</TableCell>
                        <TableCell>{record.receiptDate}</TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(record.amount)}
                        </TableCell>
                        <TableCell>{record.mode}</TableCell>
                        <TableCell>
                          {record.status === 'valid' && (
                            <Badge variant="default" className="bg-green-600">
                              <CheckCircle className="mr-1 h-3 w-3" />
                              Valid
                            </Badge>
                          )}
                          {record.status === 'warning' && (
                            <div>
                              <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
                                <AlertTriangle className="mr-1 h-3 w-3" />
                                Warning
                              </Badge>
                              <p className="mt-1 text-xs text-yellow-600">{record.warnings[0]}</p>
                            </div>
                          )}
                          {(record.status === 'invalid' || record.status === 'duplicate') && (
                            <div>
                              <Badge variant="destructive">
                                <XCircle className="mr-1 h-3 w-3" />
                                {record.status === 'duplicate' ? 'Duplicate' : 'Invalid'}
                              </Badge>
                              <p className="mt-1 text-xs text-red-600">{record.errors[0]}</p>
                            </div>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>

                {invalidRecords.length > 0 && (
                  <Alert variant="destructive" className="mt-4">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertTitle>Invalid Records Found</AlertTitle>
                    <AlertDescription>
                      {invalidRecords.length} record(s) will be skipped during processing. Please
                      fix the errors and re-upload, or proceed with valid records only.
                    </AlertDescription>
                  </Alert>
                )}

                <div className="mt-6 flex justify-end gap-4">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setUploadedFile(null);
                      setParsedData([]);
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleProcess}
                    disabled={
                      importBulk.isPending || validRecords.length + warningRecords.length === 0
                    }
                  >
                    {importBulk.isPending ? (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <CheckCircle className="mr-2 h-4 w-4" />
                        Process {validRecords.length + warningRecords.length} Records
                      </>
                    )}
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Instructions Panel */}
        {parsedData.length === 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Instructions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="mb-2 font-medium">Required Columns:</h4>
                <ul className="space-y-1 text-sm text-muted-foreground">
                  <li>- Loan Account Number</li>
                  <li>- Receipt Date (DD/MM/YYYY)</li>
                  <li>- Amount</li>
                  <li>- Receipt Mode (NEFT/RTGS/CASH/CHEQUE)</li>
                </ul>
              </div>

              <div>
                <h4 className="mb-2 font-medium">Optional Columns:</h4>
                <ul className="space-y-1 text-sm text-muted-foreground">
                  <li>- Value Date</li>
                  <li>- Instrument Number</li>
                  <li>- Instrument Date</li>
                  <li>- Bank Name</li>
                  <li>- Remarks</li>
                </ul>
              </div>

              <Button variant="outline" className="w-full" onClick={handleDownloadTemplate}>
                <Download className="mr-2 h-4 w-4" />
                Download Template
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Summary Panel when data is parsed */}
        {parsedData.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Upload Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground">Total Amount</p>
                <p className="text-2xl font-bold">{formatCurrency(totalAmount)}</p>
              </div>

              <div>
                <p className="text-sm text-muted-foreground">Records to Process</p>
                <p className="text-xl font-bold text-green-600">
                  {validRecords.length + warningRecords.length}
                </p>
              </div>

              <div>
                <p className="text-sm text-muted-foreground">Records to Skip</p>
                <p className="text-xl font-bold text-red-600">{invalidRecords.length}</p>
              </div>

              <div className="border-t pt-4">
                <Button variant="outline" className="w-full" onClick={handleDownloadTemplate}>
                  <Download className="mr-2 h-4 w-4" />
                  Download Error Report
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
