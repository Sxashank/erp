import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import {
  AlertCircle,
  ArrowLeft,
  Check,
  CheckCircle,
  FileSpreadsheet,
  RefreshCw,
  Upload,
  X,
  XCircle,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Checkbox } from '@/components/ui/checkbox';
import { useToast } from '@/hooks/use-toast';
import { bankReconciliationApi, accountsApi } from '@/services/api';

interface ParsedRow {
  transaction_date: string;
  value_date: string | null;
  reference_number: string | null;
  description: string | null;
  debit_amount: number;
  credit_amount: number;
  running_balance: number | null;
  cheque_number: string | null;
  utr_number: string | null;
  selected?: boolean;
}

interface BankAccount {
  id: string;
  code: string;
  name: string;
}

export function BankStatementImport() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const organizationId = localStorage.getItem('organization_id') || '';

  // State
  const [step, setStep] = useState(1);
  const [bankAccounts, setBankAccounts] = useState<BankAccount[]>([]);
  const [selectedBankAccount, setSelectedBankAccount] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [parsedRows, setParsedRows] = useState<ParsedRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<{
    success_count: number;
    error_count: number;
    messages: string[];
  } | null>(null);

  // Column mapping
  const [dateColumn, setDateColumn] = useState('Date');
  const [debitColumn, setDebitColumn] = useState('Withdrawal');
  const [creditColumn, setCreditColumn] = useState('Deposit');
  const [referenceColumn, setReferenceColumn] = useState('Reference');
  const [descriptionColumn, setDescriptionColumn] = useState('Description');
  const [balanceColumn, setBalanceColumn] = useState('Balance');
  const [chequeColumn, setChequeColumn] = useState('Cheque No');
  const [utrColumn, setUtrColumn] = useState('UTR');

  // Fetch bank accounts
  useEffect(() => {
    const fetchBankAccounts = async () => {
      try {
        const response = await accountsApi.list({
          organization_id: organizationId,
          account_type: 'BANK',
          page_size: 100,
        });
        setBankAccounts(response.data.items || []);
      } catch (error) {
        console.error('Failed to fetch bank accounts:', error);
      }
    };
    fetchBankAccounts();
  }, [organizationId]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setParsedRows([]);
      setImportResult(null);
    }
  };

  const handleParse = async () => {
    if (!file || !selectedBankAccount) {
      toast({
        title: 'Error',
        description: 'Please select a bank account and upload a file',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('date_column', dateColumn);
      formData.append('debit_column', debitColumn);
      formData.append('credit_column', creditColumn);
      formData.append('reference_column', referenceColumn);
      formData.append('description_column', descriptionColumn);
      formData.append('balance_column', balanceColumn);
      formData.append('cheque_column', chequeColumn);
      formData.append('utr_column', utrColumn);

      const response = await bankReconciliationApi.parseCsvStatement(formData);
      const rows = response.data.map((row: ParsedRow) => ({ ...row, selected: true }));
      setParsedRows(rows);
      setStep(2);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to parse file',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    const selectedRows = parsedRows.filter((row) => row.selected);
    if (selectedRows.length === 0) {
      toast({
        title: 'Error',
        description: 'Please select at least one row to import',
        variant: 'destructive',
      });
      return;
    }

    setImporting(true);
    try {
      const response = await bankReconciliationApi.importStatements({
        bank_account_id: selectedBankAccount,
        organization_id: organizationId,
        rows: selectedRows.map((row) => ({
          transaction_date: row.transaction_date,
          value_date: row.value_date,
          reference_number: row.reference_number,
          description: row.description,
          debit_amount: row.debit_amount,
          credit_amount: row.credit_amount,
          running_balance: row.running_balance,
          cheque_number: row.cheque_number,
          utr_number: row.utr_number,
        })),
      });

      setImportResult(response.data);
      setStep(3);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to import statements',
        variant: 'destructive',
      });
    } finally {
      setImporting(false);
    }
  };

  const toggleRowSelection = (index: number) => {
    setParsedRows((prev) =>
      prev.map((row, i) =>
        i === index ? { ...row, selected: !row.selected } : row
      )
    );
  };

  const toggleAllRows = (selected: boolean) => {
    setParsedRows((prev) => prev.map((row) => ({ ...row, selected })));
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const selectedCount = parsedRows.filter((r) => r.selected).length;
  const allSelected = parsedRows.length > 0 && selectedCount === parsedRows.length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Import Bank Statement</h1>
          <p className="text-sm text-slate-500">
            Upload and import bank statement from CSV file
          </p>
        </div>
      </div>

      {/* Steps */}
      <div className="flex items-center justify-center gap-4">
        <div className={`flex items-center gap-2 ${step >= 1 ? 'text-blue-600' : 'text-slate-400'}`}>
          <div className={`flex h-8 w-8 items-center justify-center rounded-full ${step >= 1 ? 'bg-blue-600 text-white' : 'bg-slate-200'}`}>
            1
          </div>
          <span className="font-medium">Upload</span>
        </div>
        <div className={`h-px w-16 ${step >= 2 ? 'bg-blue-600' : 'bg-slate-200'}`} />
        <div className={`flex items-center gap-2 ${step >= 2 ? 'text-blue-600' : 'text-slate-400'}`}>
          <div className={`flex h-8 w-8 items-center justify-center rounded-full ${step >= 2 ? 'bg-blue-600 text-white' : 'bg-slate-200'}`}>
            2
          </div>
          <span className="font-medium">Preview</span>
        </div>
        <div className={`h-px w-16 ${step >= 3 ? 'bg-blue-600' : 'bg-slate-200'}`} />
        <div className={`flex items-center gap-2 ${step >= 3 ? 'text-blue-600' : 'text-slate-400'}`}>
          <div className={`flex h-8 w-8 items-center justify-center rounded-full ${step >= 3 ? 'bg-blue-600 text-white' : 'bg-slate-200'}`}>
            3
          </div>
          <span className="font-medium">Complete</span>
        </div>
      </div>

      {/* Step 1: Upload */}
      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Upload Bank Statement</CardTitle>
            <CardDescription>
              Select a bank account and upload a CSV file
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label>Bank Account *</Label>
                <Select value={selectedBankAccount} onValueChange={setSelectedBankAccount}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select bank account" />
                  </SelectTrigger>
                  <SelectContent>
                    {bankAccounts.map((account) => (
                      <SelectItem key={account.id} value={account.id}>
                        {account.code} - {account.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Statement File (CSV) *</Label>
                <Input
                  type="file"
                  accept=".csv"
                  onChange={handleFileChange}
                  className="cursor-pointer"
                />
              </div>
            </div>

            <div>
              <h3 className="mb-4 font-medium">Column Mapping</h3>
              <p className="mb-4 text-sm text-slate-500">
                Map the columns in your CSV file to the corresponding fields
              </p>
              <div className="grid gap-4 md:grid-cols-4">
                <div>
                  <Label>Transaction Date Column</Label>
                  <Input
                    value={dateColumn}
                    onChange={(e) => setDateColumn(e.target.value)}
                    placeholder="Date"
                  />
                </div>
                <div>
                  <Label>Debit/Withdrawal Column</Label>
                  <Input
                    value={debitColumn}
                    onChange={(e) => setDebitColumn(e.target.value)}
                    placeholder="Withdrawal"
                  />
                </div>
                <div>
                  <Label>Credit/Deposit Column</Label>
                  <Input
                    value={creditColumn}
                    onChange={(e) => setCreditColumn(e.target.value)}
                    placeholder="Deposit"
                  />
                </div>
                <div>
                  <Label>Reference Column</Label>
                  <Input
                    value={referenceColumn}
                    onChange={(e) => setReferenceColumn(e.target.value)}
                    placeholder="Reference"
                  />
                </div>
                <div>
                  <Label>Description Column</Label>
                  <Input
                    value={descriptionColumn}
                    onChange={(e) => setDescriptionColumn(e.target.value)}
                    placeholder="Description"
                  />
                </div>
                <div>
                  <Label>Balance Column</Label>
                  <Input
                    value={balanceColumn}
                    onChange={(e) => setBalanceColumn(e.target.value)}
                    placeholder="Balance"
                  />
                </div>
                <div>
                  <Label>Cheque Number Column</Label>
                  <Input
                    value={chequeColumn}
                    onChange={(e) => setChequeColumn(e.target.value)}
                    placeholder="Cheque No"
                  />
                </div>
                <div>
                  <Label>UTR Column</Label>
                  <Input
                    value={utrColumn}
                    onChange={(e) => setUtrColumn(e.target.value)}
                    placeholder="UTR"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-4">
              <Button variant="outline" onClick={() => navigate(-1)}>
                Cancel
              </Button>
              <Button onClick={handleParse} disabled={loading || !file || !selectedBankAccount}>
                {loading ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Parsing...
                  </>
                ) : (
                  <>
                    <FileSpreadsheet className="mr-2 h-4 w-4" />
                    Parse File
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Preview */}
      {step === 2 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Preview Parsed Data</CardTitle>
                <CardDescription>
                  Review and select rows to import ({selectedCount} of {parsedRows.length} selected)
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => toggleAllRows(true)}>
                  Select All
                </Button>
                <Button variant="outline" size="sm" onClick={() => toggleAllRows(false)}>
                  Deselect All
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="max-h-[500px] overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox
                        checked={allSelected}
                        onCheckedChange={(checked) => toggleAllRows(!!checked)}
                      />
                    </TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Reference</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-right">Debit</TableHead>
                    <TableHead className="text-right">Credit</TableHead>
                    <TableHead className="text-right">Balance</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {parsedRows.map((row, index) => (
                    <TableRow key={index} className={!row.selected ? 'opacity-50' : ''}>
                      <TableCell>
                        <Checkbox
                          checked={row.selected}
                          onCheckedChange={() => toggleRowSelection(index)}
                        />
                      </TableCell>
                      <TableCell>
                        {row.transaction_date
                          ? format(new Date(row.transaction_date), 'dd/MM/yyyy')
                          : '-'}
                      </TableCell>
                      <TableCell>{row.reference_number || '-'}</TableCell>
                      <TableCell className="max-w-xs truncate">
                        {row.description || '-'}
                      </TableCell>
                      <TableCell className="text-right text-red-600">
                        {row.debit_amount > 0 ? formatAmount(row.debit_amount) : '-'}
                      </TableCell>
                      <TableCell className="text-right text-green-600">
                        {row.credit_amount > 0 ? formatAmount(row.credit_amount) : '-'}
                      </TableCell>
                      <TableCell className="text-right">
                        {row.running_balance !== null
                          ? formatAmount(row.running_balance)
                          : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            <div className="mt-6 flex justify-between">
              <Button variant="outline" onClick={() => setStep(1)}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back
              </Button>
              <Button onClick={handleImport} disabled={importing || selectedCount === 0}>
                {importing ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Importing...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Import {selectedCount} Row{selectedCount !== 1 ? 's' : ''}
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Complete */}
      {step === 3 && importResult && (
        <Card>
          <CardHeader>
            <CardTitle>Import Complete</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
                  <CheckCircle className="h-8 w-8 text-green-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-green-600">
                    {importResult.success_count}
                  </p>
                  <p className="text-sm text-slate-500">Imported successfully</p>
                </div>
              </div>
              {importResult.error_count > 0 && (
                <div className="flex items-center gap-4">
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
                    <XCircle className="h-8 w-8 text-red-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-red-600">
                      {importResult.error_count}
                    </p>
                    <p className="text-sm text-slate-500">Errors</p>
                  </div>
                </div>
              )}
            </div>

            {importResult.messages.length > 0 && (
              <Alert variant={importResult.error_count > 0 ? 'destructive' : 'default'}>
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Import Messages</AlertTitle>
                <AlertDescription>
                  <ul className="mt-2 list-inside list-disc">
                    {importResult.messages.map((msg, i) => (
                      <li key={i}>{msg}</li>
                    ))}
                  </ul>
                </AlertDescription>
              </Alert>
            )}

            <div className="flex justify-end gap-4">
              <Button variant="outline" onClick={() => {
                setStep(1);
                setFile(null);
                setParsedRows([]);
                setImportResult(null);
              }}>
                Import More
              </Button>
              <Button onClick={() => navigate('/admin/ap-ar/bank-reconciliation')}>
                View Statements
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
