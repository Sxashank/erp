import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Upload,
  Download,
  FileSpreadsheet,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import { Progress } from '@/components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { formatCurrency } from '@/lib/utils';

interface UploadedReceipt {
  row: number;
  loan_account: string;
  entity: string;
  receipt_date: string;
  amount: number;
  mode: string;
  instrument_number?: string;
  status: 'valid' | 'invalid' | 'duplicate' | 'warning';
  errors: string[];
  warnings: string[];
}

export default function BulkReceiptUpload() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [parsedData, setParsedData] = useState<UploadedReceipt[]>([]);
  const [showResults, setShowResults] = useState(false);

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

    // Mock parsed data
    const mockData: UploadedReceipt[] = [
      {
        row: 2,
        loan_account: 'SMFC/LA/2024/00125',
        entity: 'ABC Trading Co.',
        receipt_date: '2025-01-15',
        amount: 450000,
        mode: 'NEFT',
        instrument_number: 'UTR123456789',
        status: 'valid',
        errors: [],
        warnings: [],
      },
      {
        row: 3,
        loan_account: 'SMFC/LA/2024/00089',
        entity: 'XYZ Industries',
        receipt_date: '2025-01-15',
        amount: 750000,
        mode: 'RTGS',
        instrument_number: 'UTR987654321',
        status: 'valid',
        errors: [],
        warnings: [],
      },
      {
        row: 4,
        loan_account: 'SMFC/LA/2024/00156',
        entity: 'Metro Logistics',
        receipt_date: '2025-01-14',
        amount: 320000,
        mode: 'CHEQUE',
        instrument_number: 'CHQ456789',
        status: 'warning',
        errors: [],
        warnings: ['Post-dated cheque'],
      },
      {
        row: 5,
        loan_account: 'INVALID/ACCOUNT',
        entity: 'Unknown Entity',
        receipt_date: '2025-01-14',
        amount: 150000,
        mode: 'CASH',
        status: 'invalid',
        errors: ['Loan account not found'],
        warnings: [],
      },
      {
        row: 6,
        loan_account: 'SMFC/LA/2024/00125',
        entity: 'ABC Trading Co.',
        receipt_date: '2025-01-15',
        amount: 450000,
        mode: 'NEFT',
        instrument_number: 'UTR123456789',
        status: 'duplicate',
        errors: ['Duplicate entry (same amount, date, and UTR)'],
        warnings: [],
      },
    ];

    setParsedData(mockData);
    setIsUploading(false);
  };

  const handleProcess = async () => {
    setIsProcessing(true);
    // Simulate processing
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsProcessing(false);
    setShowResults(true);
  };

  const handleDownloadTemplate = () => {
    // In a real implementation, this would download an actual template file
    alert('Template download started');
  };

  const validRecords = parsedData.filter((r) => r.status === 'valid');
  const warningRecords = parsedData.filter((r) => r.status === 'warning');
  const invalidRecords = parsedData.filter((r) => r.status === 'invalid' || r.status === 'duplicate');
  const totalAmount = parsedData
    .filter((r) => r.status === 'valid' || r.status === 'warning')
    .reduce((sum, r) => sum + r.amount, 0);

  if (showResults) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold mb-2">Bulk Upload Complete</h2>
          <p className="text-muted-foreground mb-6">
            {validRecords.length + warningRecords.length} receipts created successfully
          </p>
          <div className="grid grid-cols-3 gap-4 max-w-md mx-auto mb-6">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{validRecords.length}</div>
              <div className="text-xs text-muted-foreground">Created</div>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">{warningRecords.length}</div>
              <div className="text-xs text-muted-foreground">With Warnings</div>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">{invalidRecords.length}</div>
              <div className="text-xs text-muted-foreground">Skipped</div>
            </div>
          </div>
          <div className="flex gap-4 justify-center">
            <Button variant="outline" onClick={() => navigate('/lending/receipts')}>
              View Receipts
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setShowResults(false);
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
          { label: 'Receipts', to: '/lending/receipts' },
          { label: 'Bulk Upload' },
        ]}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Section */}
        <Card className={parsedData.length > 0 ? 'lg:col-span-2' : 'lg:col-span-3'}>
          <CardHeader>
            <CardTitle>Upload File</CardTitle>
            <CardDescription>Select an Excel or CSV file to upload</CardDescription>
          </CardHeader>
          <CardContent>
            {!uploadedFile ? (
              <div
                className="border-2 border-dashed rounded-lg p-12 text-center cursor-pointer hover:border-primary/50 transition-colors"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-medium mb-2">Drop your file here or click to browse</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Supported formats: .xlsx, .xls, .csv (max 5MB)
                </p>
                <Button variant="outline">
                  <FileSpreadsheet className="h-4 w-4 mr-2" />
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
              <div className="text-center py-12">
                <RefreshCw className="h-12 w-12 mx-auto mb-4 text-primary animate-spin" />
                <h3 className="text-lg font-medium mb-2">Parsing file...</h3>
                <Progress value={uploadProgress} className="w-64 mx-auto" />
                <p className="text-sm text-muted-foreground mt-2">{uploadProgress}% complete</p>
              </div>
            ) : (
              <div>
                <div className="flex items-center justify-between p-4 border rounded-lg mb-4">
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
                <div className="grid grid-cols-4 gap-4 mb-6">
                  <div className="text-center p-3 bg-muted rounded-lg">
                    <div className="text-2xl font-bold">{parsedData.length}</div>
                    <div className="text-xs text-muted-foreground">Total Records</div>
                  </div>
                  <div className="text-center p-3 bg-green-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">{validRecords.length}</div>
                    <div className="text-xs text-muted-foreground">Valid</div>
                  </div>
                  <div className="text-center p-3 bg-yellow-50 rounded-lg">
                    <div className="text-2xl font-bold text-yellow-600">{warningRecords.length}</div>
                    <div className="text-xs text-muted-foreground">Warnings</div>
                  </div>
                  <div className="text-center p-3 bg-red-50 rounded-lg">
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
                      <TableRow key={index} className={record.status === 'invalid' || record.status === 'duplicate' ? 'bg-red-50' : record.status === 'warning' ? 'bg-yellow-50' : ''}>
                        <TableCell>{record.row}</TableCell>
                        <TableCell className="font-mono text-sm">{record.loan_account}</TableCell>
                        <TableCell>{record.entity}</TableCell>
                        <TableCell>{record.receipt_date}</TableCell>
                        <TableCell className="text-right">{formatCurrency(record.amount)}</TableCell>
                        <TableCell>{record.mode}</TableCell>
                        <TableCell>
                          {record.status === 'valid' && (
                            <Badge variant="default" className="bg-green-600">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Valid
                            </Badge>
                          )}
                          {record.status === 'warning' && (
                            <div>
                              <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
                                <AlertTriangle className="h-3 w-3 mr-1" />
                                Warning
                              </Badge>
                              <p className="text-xs text-yellow-600 mt-1">{record.warnings[0]}</p>
                            </div>
                          )}
                          {(record.status === 'invalid' || record.status === 'duplicate') && (
                            <div>
                              <Badge variant="destructive">
                                <XCircle className="h-3 w-3 mr-1" />
                                {record.status === 'duplicate' ? 'Duplicate' : 'Invalid'}
                              </Badge>
                              <p className="text-xs text-red-600 mt-1">{record.errors[0]}</p>
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
                      {invalidRecords.length} record(s) will be skipped during processing. Please fix
                      the errors and re-upload, or proceed with valid records only.
                    </AlertDescription>
                  </Alert>
                )}

                <div className="flex justify-end gap-4 mt-6">
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
                    disabled={isProcessing || validRecords.length + warningRecords.length === 0}
                  >
                    {isProcessing ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <CheckCircle className="h-4 w-4 mr-2" />
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
                <h4 className="font-medium mb-2">Required Columns:</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>- Loan Account Number</li>
                  <li>- Receipt Date (DD/MM/YYYY)</li>
                  <li>- Amount</li>
                  <li>- Receipt Mode (NEFT/RTGS/CASH/CHEQUE)</li>
                </ul>
              </div>

              <div>
                <h4 className="font-medium mb-2">Optional Columns:</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>- Value Date</li>
                  <li>- Instrument Number</li>
                  <li>- Instrument Date</li>
                  <li>- Bank Name</li>
                  <li>- Remarks</li>
                </ul>
              </div>

              <Button variant="outline" className="w-full" onClick={handleDownloadTemplate}>
                <Download className="h-4 w-4 mr-2" />
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
                  <Download className="h-4 w-4 mr-2" />
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
