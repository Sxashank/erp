import {
  AlertCircle,
  CheckCircle2,
  Download,
  FilePenLine,
  FileSpreadsheet,
  Loader2,
  Plus,
  Trash2,
  Upload,
} from 'lucide-react';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { useEntities } from '@/hooks/lending/useEntities';
import {
  masterRowsToOptions,
  useLendingMasterRows,
  useLendingOptionRows,
} from '@/hooks/lending/useLendingMasters';
import { useLoanProducts } from '@/hooks/lending/useLoanProducts';
import { useToast } from '@/hooks/use-toast';
import {
  downloadHistoricalLoanTemplate,
  importHistoricalLoans,
  onboardHistoricalLoan,
  type HistoricalInstallmentPayload,
  type HistoricalLoanOnboardingBatchResponse,
  type HistoricalLoanOnboardingPayload,
} from '@/services/lending/loanAccountApi';

interface Option {
  value: string;
  label: string;
}

interface ManualLoanForm {
  entityId: string;
  productId: string;
  loanAccountNumber: string;
  legacyLoanNumber: string;
  loanReferenceNumber: string;
  applicationDate: string;
  sanctionDate: string;
  accountOpenDate: string;
  firstDisbursementDate: string;
  lastDisbursementDate: string;
  repaymentStartDate: string;
  maturityDate: string;
  cutoverDate: string;
  sanctionedAmount: string;
  totalDisbursedAmount: string;
  principalOutstanding: string;
  interestOutstanding: string;
  interestOverdue: string;
  principalOverdue: string;
  penalInterestOutstanding: string;
  chargesOutstanding: string;
  totalOutstanding: string;
  tenureMonths: string;
  moratoriumMonths: string;
  interestType: string;
  currentInterestRate: string;
  penalInterestRate: string;
  repaymentFrequency: string;
  repaymentMode: string;
  dayCountConvention: string;
  currentEmiAmount: string;
  daysPastDue: string;
  assetClassification: string;
  npaDate: string;
  purpose: string;
  projectName: string;
  remarks: string;
  createHistoricalReceipts: boolean;
}

interface ManualInstallmentForm {
  installmentNumber: string;
  dueDate: string;
  openingBalance: string;
  principalAmount: string;
  interestAmount: string;
  emiAmount: string;
  closingBalance: string;
  principalPaid: string;
  interestPaid: string;
  penalInterestDue: string;
  penalInterestPaid: string;
  status: string;
  paidDate: string;
  receiptReference: string;
  receiptMode: string;
  remarks: string;
}

const ASSET_CLASSIFICATION_OPTIONS: Option[] = [
  { value: 'STANDARD', label: 'Standard' },
  { value: 'SMA_0', label: 'SMA-0' },
  { value: 'SMA_1', label: 'SMA-1' },
  { value: 'SMA_2', label: 'SMA-2' },
  { value: 'NPA', label: 'NPA' },
  { value: 'SUBSTANDARD', label: 'Substandard' },
  { value: 'DOUBTFUL_1', label: 'Doubtful 1' },
  { value: 'DOUBTFUL_2', label: 'Doubtful 2' },
  { value: 'DOUBTFUL_3', label: 'Doubtful 3' },
  { value: 'LOSS', label: 'Loss' },
];

const INSTALLMENT_STATUS_OPTIONS: Option[] = [
  { value: 'NOT_DUE', label: 'Not due' },
  { value: 'DUE', label: 'Due' },
  { value: 'PARTIALLY_PAID', label: 'Partially paid' },
  { value: 'PAID', label: 'Paid' },
  { value: 'OVERDUE', label: 'Overdue' },
  { value: 'WAIVED', label: 'Waived' },
  { value: 'WRITTEN_OFF', label: 'Written off' },
];

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function emptyManualLoanForm(): ManualLoanForm {
  return {
    entityId: '',
    productId: '',
    loanAccountNumber: '',
    legacyLoanNumber: '',
    loanReferenceNumber: '',
    applicationDate: '',
    sanctionDate: '',
    accountOpenDate: '',
    firstDisbursementDate: '',
    lastDisbursementDate: '',
    repaymentStartDate: '',
    maturityDate: '',
    cutoverDate: '',
    sanctionedAmount: '',
    totalDisbursedAmount: '',
    principalOutstanding: '',
    interestOutstanding: '0',
    interestOverdue: '',
    principalOverdue: '',
    penalInterestOutstanding: '0',
    chargesOutstanding: '0',
    totalOutstanding: '',
    tenureMonths: '',
    moratoriumMonths: '0',
    interestType: '',
    currentInterestRate: '',
    penalInterestRate: '0',
    repaymentFrequency: '',
    repaymentMode: '',
    dayCountConvention: '',
    currentEmiAmount: '',
    daysPastDue: '',
    assetClassification: '',
    npaDate: '',
    purpose: 'Legacy loan onboarding',
    projectName: '',
    remarks: '',
    createHistoricalReceipts: true,
  };
}

function emptyInstallment(index: number): ManualInstallmentForm {
  return {
    installmentNumber: String(index + 1),
    dueDate: '',
    openingBalance: '',
    principalAmount: '0',
    interestAmount: '0',
    emiAmount: '',
    closingBalance: '',
    principalPaid: '0',
    interestPaid: '0',
    penalInterestDue: '0',
    penalInterestPaid: '0',
    status: '',
    paidDate: '',
    receiptReference: '',
    receiptMode: '',
    remarks: '',
  };
}

function hasInstallmentData(row: ManualInstallmentForm) {
  return [
    row.dueDate,
    row.openingBalance,
    row.principalAmount !== '0' ? row.principalAmount : '',
    row.interestAmount !== '0' ? row.interestAmount : '',
    row.emiAmount,
    row.closingBalance,
    row.principalPaid !== '0' ? row.principalPaid : '',
    row.interestPaid !== '0' ? row.interestPaid : '',
    row.penalInterestDue !== '0' ? row.penalInterestDue : '',
    row.penalInterestPaid !== '0' ? row.penalInterestPaid : '',
    row.status,
    row.paidDate,
    row.receiptReference,
    row.receiptMode,
  ].some((value) => value.trim().length > 0);
}

function maybe(value: string) {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

function requireText(value: string, label: string) {
  const trimmed = value.trim();
  if (!trimmed) {
    throw new Error(`${label} is required.`);
  }
  return trimmed;
}

function parsePositiveInt(value: string, label: string) {
  const parsed = Number.parseInt(requireText(value, label), 10);
  if (!Number.isFinite(parsed) || parsed < 1) {
    throw new Error(`${label} must be a positive number.`);
  }
  return parsed;
}

function parseNonNegativeInt(value: string, label: string) {
  const text = maybe(value);
  if (!text) return undefined;
  const parsed = Number.parseInt(text, 10);
  if (!Number.isFinite(parsed) || parsed < 0) {
    throw new Error(`${label} must be zero or more.`);
  }
  return parsed;
}

function buildInstallments(rows: ManualInstallmentForm[]): HistoricalInstallmentPayload[] {
  return rows.filter(hasInstallmentData).map((row) => ({
    installmentNumber: parsePositiveInt(row.installmentNumber, 'Installment number'),
    dueDate: requireText(row.dueDate, 'Due date'),
    openingBalance: requireText(row.openingBalance, 'Opening balance'),
    principalAmount: maybe(row.principalAmount),
    interestAmount: maybe(row.interestAmount),
    emiAmount: requireText(row.emiAmount, 'EMI amount'),
    closingBalance: requireText(row.closingBalance, 'Closing balance'),
    principalPaid: maybe(row.principalPaid),
    interestPaid: maybe(row.interestPaid),
    penalInterestDue: maybe(row.penalInterestDue),
    penalInterestPaid: maybe(row.penalInterestPaid),
    status: maybe(row.status),
    paidDate: maybe(row.paidDate),
    receiptReference: maybe(row.receiptReference),
    receiptMode: maybe(row.receiptMode),
    remarks: maybe(row.remarks),
  }));
}

function buildManualPayload(
  form: ManualLoanForm,
  rows: ManualInstallmentForm[],
): HistoricalLoanOnboardingPayload {
  if (!form.loanAccountNumber.trim() && !form.legacyLoanNumber.trim()) {
    throw new Error('Loan account number or legacy loan number is required.');
  }

  return {
    entityId: requireText(form.entityId, 'Borrower entity'),
    productId: requireText(form.productId, 'Loan product'),
    loanAccountNumber: maybe(form.loanAccountNumber),
    legacyLoanNumber: maybe(form.legacyLoanNumber),
    loanReferenceNumber: maybe(form.loanReferenceNumber),
    applicationDate: requireText(form.applicationDate, 'Application date'),
    sanctionDate: requireText(form.sanctionDate, 'Sanction date'),
    accountOpenDate: requireText(form.accountOpenDate, 'Account open date'),
    firstDisbursementDate: maybe(form.firstDisbursementDate),
    lastDisbursementDate: maybe(form.lastDisbursementDate),
    repaymentStartDate: maybe(form.repaymentStartDate),
    maturityDate: maybe(form.maturityDate),
    cutoverDate: requireText(form.cutoverDate, 'Cutover date'),
    sanctionedAmount: requireText(form.sanctionedAmount, 'Sanctioned amount'),
    totalDisbursedAmount: requireText(form.totalDisbursedAmount, 'Total disbursed amount'),
    principalOutstanding: requireText(form.principalOutstanding, 'Principal outstanding'),
    interestOutstanding: maybe(form.interestOutstanding),
    interestOverdue: maybe(form.interestOverdue),
    principalOverdue: maybe(form.principalOverdue),
    penalInterestOutstanding: maybe(form.penalInterestOutstanding),
    chargesOutstanding: maybe(form.chargesOutstanding),
    totalOutstanding: maybe(form.totalOutstanding),
    tenureMonths: parsePositiveInt(form.tenureMonths, 'Tenure months'),
    moratoriumMonths: parseNonNegativeInt(form.moratoriumMonths, 'Moratorium months'),
    interestType: requireText(form.interestType, 'Interest type'),
    currentInterestRate: requireText(form.currentInterestRate, 'Current interest rate'),
    penalInterestRate: maybe(form.penalInterestRate),
    repaymentFrequency: requireText(form.repaymentFrequency, 'Repayment frequency'),
    repaymentMode: requireText(form.repaymentMode, 'Repayment mode'),
    dayCountConvention: requireText(form.dayCountConvention, 'Day count convention'),
    currentEmiAmount: maybe(form.currentEmiAmount),
    daysPastDue: parseNonNegativeInt(form.daysPastDue, 'Days past due'),
    assetClassification: maybe(form.assetClassification),
    npaDate: maybe(form.npaDate),
    purpose: maybe(form.purpose),
    projectName: maybe(form.projectName),
    remarks: maybe(form.remarks),
    createHistoricalReceipts: form.createHistoricalReceipts,
    postHistoricalAccounting: false,
    installments: buildInstallments(rows),
  };
}

function toBatchResult(
  result: HistoricalLoanOnboardingBatchResponse['results'][number],
): HistoricalLoanOnboardingBatchResponse {
  return {
    dryRun: result.dryRun,
    totalLoans: 1,
    importedLoans: result.loanAccountId ? 1 : 0,
    totalInstallments: result.importedInstallments,
    importedReceipts: result.importedReceipts,
    results: [result],
  };
}

function TextField({
  label,
  value,
  onChange,
  type = 'text',
  required = false,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  required?: boolean;
  placeholder?: string;
}) {
  return (
    <div className="space-y-1.5">
      <Label>
        {label}
        {required ? ' *' : ''}
      </Label>
      <Input
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
  placeholder,
  required = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Option[];
  placeholder?: string;
  required?: boolean;
}) {
  return (
    <div className="space-y-1.5">
      <Label>
        {label}
        {required ? ' *' : ''}
      </Label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger>
          <SelectValue placeholder={placeholder ?? `Select ${label.toLowerCase()}`} />
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

export default function HistoricalLoanImport() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const fileLabelClassName = [
    'flex min-h-10 flex-1 cursor-pointer items-center rounded-md border',
    'border-input bg-background px-3 text-sm',
  ].join(' ');
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<HistoricalLoanOnboardingBatchResponse | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [isManualValidating, setIsManualValidating] = useState(false);
  const [isManualSaving, setIsManualSaving] = useState(false);
  const [manualForm, setManualForm] = useState<ManualLoanForm>(() => emptyManualLoanForm());
  const [manualInstallments, setManualInstallments] = useState<ManualInstallmentForm[]>(() => [
    emptyInstallment(0),
  ]);
  const hasErrors = result?.results.some((row) => row.errors.length > 0) ?? false;

  const entitiesQuery = useEntities({ status: 'ACTIVE', includeInactive: false, pageSize: 100 });
  const productsQuery = useLoanProducts({ includeInactive: false, pageSize: 100 });
  const interestTypesQuery = useLendingOptionRows('RATE_TYPE');
  const repaymentFrequenciesQuery = useLendingOptionRows('REPAYMENT_FREQUENCY');
  const repaymentModesQuery = useLendingOptionRows('REPAYMENT_MODE');
  const receiptModesQuery = useLendingOptionRows('RECEIPT_MODE');
  const dayCountQuery = useLendingMasterRows('day-count-conventions', { pageSize: 100 });

  const entityOptions = useMemo<Option[]>(
    () =>
      (entitiesQuery.data?.items ?? []).map((entity) => ({
        value: entity.id,
        label: `${entity.legalName} (${entity.entityCode})`,
      })),
    [entitiesQuery.data?.items],
  );
  const productOptions = useMemo<Option[]>(
    () =>
      (productsQuery.data?.items ?? []).map((product) => ({
        value: product.id,
        label: `${product.name} (${product.code})`,
      })),
    [productsQuery.data?.items],
  );
  const interestTypeOptions = masterRowsToOptions(interestTypesQuery.data?.items);
  const repaymentFrequencyOptions = masterRowsToOptions(repaymentFrequenciesQuery.data?.items);
  const repaymentModeOptions = masterRowsToOptions(repaymentModesQuery.data?.items);
  const receiptModeOptions = masterRowsToOptions(receiptModesQuery.data?.items);
  const dayCountOptions = masterRowsToOptions(dayCountQuery.data?.items, 'name');

  const updateManualForm = <K extends keyof ManualLoanForm>(key: K, value: ManualLoanForm[K]) => {
    setManualForm((current) => ({ ...current, [key]: value }));
  };

  const updateInstallment = <K extends keyof ManualInstallmentForm>(
    index: number,
    key: K,
    value: ManualInstallmentForm[K],
  ) => {
    setManualInstallments((current) =>
      current.map((row, rowIndex) => (rowIndex === index ? { ...row, [key]: value } : row)),
    );
  };

  const handleTemplateDownload = async () => {
    try {
      const blob = await downloadHistoricalLoanTemplate();
      downloadBlob(blob, 'historical-loan-onboarding-template.csv');
    } catch (error) {
      toast({
        title: 'Template download failed',
        description: error instanceof Error ? error.message : 'Could not download template',
        variant: 'destructive',
      });
    }
  };

  const runImport = async (dryRun: boolean) => {
    if (!file) {
      toast({
        title: 'Select a file',
        description: 'Upload the populated loan onboarding sheet first.',
        variant: 'destructive',
      });
      return;
    }

    if (dryRun) {
      setIsValidating(true);
    } else {
      setIsImporting(true);
    }

    try {
      const response = await importHistoricalLoans(file, dryRun);
      setResult(response);
      toast({
        title: dryRun ? 'Validation completed' : 'Historical loans imported',
        description: `${response.totalLoans} loan(s), ${response.totalInstallments} EMI row(s)`,
      });
    } catch (error) {
      toast({
        title: dryRun ? 'Validation failed' : 'Import failed',
        description: error instanceof Error ? error.message : 'Could not process file',
        variant: 'destructive',
      });
    } finally {
      setIsValidating(false);
      setIsImporting(false);
    }
  };

  const runManualOnboarding = async (dryRun: boolean) => {
    if (dryRun) {
      setIsManualValidating(true);
    } else {
      setIsManualSaving(true);
    }

    try {
      const payload = buildManualPayload(manualForm, manualInstallments);
      const response = await onboardHistoricalLoan(payload, dryRun);
      setResult(toBatchResult(response));
      toast({
        title: dryRun ? 'Manual entry validated' : 'Historical loan recorded',
        description: `${response.importedInstallments} EMI row(s), ${response.importedReceipts} receipt(s)`,
      });
      if (!dryRun && response.loanAccountId) {
        setManualForm(emptyManualLoanForm());
        setManualInstallments([emptyInstallment(0)]);
      }
    } catch (error) {
      toast({
        title: dryRun ? 'Validation failed' : 'Save failed',
        description: error instanceof Error ? error.message : 'Could not record historical loan',
        variant: 'destructive',
      });
    } finally {
      setIsManualValidating(false);
      setIsManualSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Historical Loan Onboarding"
        subtitle="Record existing corporate loan accounts, schedules, and EMI history"
        breadcrumbs={[
          { label: 'Lending', to: '/admin/lending' },
          { label: 'Loan Accounts', to: '/admin/lending/accounts' },
          { label: 'Historical Onboarding' },
        ]}
        actions={
          <Button variant="outline" onClick={() => navigate('/admin/lending/accounts')}>
            Back to Accounts
          </Button>
        }
      />

      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Cutover accounting</AlertTitle>
        <AlertDescription>
          Historical EMI rows are imported as loan operational history. Accounting starts from
          approved cutover outstanding balances unless a separate accounting migration is approved.
        </AlertDescription>
      </Alert>

      <Tabs defaultValue="file" className="space-y-4">
        <TabsList>
          <TabsTrigger value="file">
            <FileSpreadsheet className="mr-2 h-4 w-4" />
            Excel / CSV
          </TabsTrigger>
          <TabsTrigger value="manual">
            <FilePenLine className="mr-2 h-4 w-4" />
            Manual Entry
          </TabsTrigger>
        </TabsList>

        <TabsContent value="file">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <FileSpreadsheet className="h-5 w-5" />
                Import File
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-col gap-3 md:flex-row md:items-center">
                <Button variant="outline" onClick={handleTemplateDownload}>
                  <Download className="mr-2 h-4 w-4" />
                  Download Template
                </Button>
                <label className={fileLabelClassName}>
                  <input
                    type="file"
                    accept=".csv,.xlsx"
                    className="sr-only"
                    onChange={(event) => {
                      setFile(event.target.files?.[0] ?? null);
                      setResult(null);
                    }}
                  />
                  {file ? file.name : 'Select CSV or XLSX file'}
                </label>
                <Button
                  variant="outline"
                  disabled={!file || isValidating}
                  onClick={() => runImport(true)}
                >
                  {isValidating ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <CheckCircle2 className="mr-2 h-4 w-4" />
                  )}
                  Validate
                </Button>
                <Button
                  disabled={!file || isImporting || hasErrors}
                  onClick={() => runImport(false)}
                >
                  {isImporting ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Upload className="mr-2 h-4 w-4" />
                  )}
                  Import
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="manual">
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Loan Identity</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-4 md:grid-cols-3">
                <SelectField
                  label="Borrower Entity"
                  value={manualForm.entityId}
                  onChange={(value) => updateManualForm('entityId', value)}
                  options={entityOptions}
                  required
                />
                <SelectField
                  label="Loan Product"
                  value={manualForm.productId}
                  onChange={(value) => updateManualForm('productId', value)}
                  options={productOptions}
                  required
                />
                <TextField
                  label="Loan Account Number"
                  value={manualForm.loanAccountNumber}
                  onChange={(value) => updateManualForm('loanAccountNumber', value)}
                  placeholder="Existing SFC account number"
                />
                <TextField
                  label="Legacy Loan Number"
                  value={manualForm.legacyLoanNumber}
                  onChange={(value) => updateManualForm('legacyLoanNumber', value)}
                  placeholder="Client Excel/register reference"
                />
                <TextField
                  label="Loan Reference Number"
                  value={manualForm.loanReferenceNumber}
                  onChange={(value) => updateManualForm('loanReferenceNumber', value)}
                />
                <TextField
                  label="Project Name"
                  value={manualForm.projectName}
                  onChange={(value) => updateManualForm('projectName', value)}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Dates And Balances</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-4 md:grid-cols-4">
                <TextField
                  label="Application Date"
                  type="date"
                  value={manualForm.applicationDate}
                  onChange={(value) => updateManualForm('applicationDate', value)}
                  required
                />
                <TextField
                  label="Sanction Date"
                  type="date"
                  value={manualForm.sanctionDate}
                  onChange={(value) => updateManualForm('sanctionDate', value)}
                  required
                />
                <TextField
                  label="Account Open Date"
                  type="date"
                  value={manualForm.accountOpenDate}
                  onChange={(value) => updateManualForm('accountOpenDate', value)}
                  required
                />
                <TextField
                  label="Cutover Date"
                  type="date"
                  value={manualForm.cutoverDate}
                  onChange={(value) => updateManualForm('cutoverDate', value)}
                  required
                />
                <TextField
                  label="First Disbursement Date"
                  type="date"
                  value={manualForm.firstDisbursementDate}
                  onChange={(value) => updateManualForm('firstDisbursementDate', value)}
                />
                <TextField
                  label="Last Disbursement Date"
                  type="date"
                  value={manualForm.lastDisbursementDate}
                  onChange={(value) => updateManualForm('lastDisbursementDate', value)}
                />
                <TextField
                  label="Repayment Start Date"
                  type="date"
                  value={manualForm.repaymentStartDate}
                  onChange={(value) => updateManualForm('repaymentStartDate', value)}
                />
                <TextField
                  label="Maturity Date"
                  type="date"
                  value={manualForm.maturityDate}
                  onChange={(value) => updateManualForm('maturityDate', value)}
                />
                <TextField
                  label="Sanctioned Amount"
                  type="number"
                  value={manualForm.sanctionedAmount}
                  onChange={(value) => updateManualForm('sanctionedAmount', value)}
                  required
                />
                <TextField
                  label="Total Disbursed Amount"
                  type="number"
                  value={manualForm.totalDisbursedAmount}
                  onChange={(value) => updateManualForm('totalDisbursedAmount', value)}
                  required
                />
                <TextField
                  label="Principal Outstanding"
                  type="number"
                  value={manualForm.principalOutstanding}
                  onChange={(value) => updateManualForm('principalOutstanding', value)}
                  required
                />
                <TextField
                  label="Total Outstanding"
                  type="number"
                  value={manualForm.totalOutstanding}
                  onChange={(value) => updateManualForm('totalOutstanding', value)}
                />
                <TextField
                  label="Interest Outstanding"
                  type="number"
                  value={manualForm.interestOutstanding}
                  onChange={(value) => updateManualForm('interestOutstanding', value)}
                />
                <TextField
                  label="Principal Overdue"
                  type="number"
                  value={manualForm.principalOverdue}
                  onChange={(value) => updateManualForm('principalOverdue', value)}
                />
                <TextField
                  label="Interest Overdue"
                  type="number"
                  value={manualForm.interestOverdue}
                  onChange={(value) => updateManualForm('interestOverdue', value)}
                />
                <TextField
                  label="Penal / Charges Outstanding"
                  type="number"
                  value={manualForm.penalInterestOutstanding}
                  onChange={(value) => updateManualForm('penalInterestOutstanding', value)}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Terms And Classification</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-4 md:grid-cols-4">
                <TextField
                  label="Tenure Months"
                  type="number"
                  value={manualForm.tenureMonths}
                  onChange={(value) => updateManualForm('tenureMonths', value)}
                  required
                />
                <TextField
                  label="Moratorium Months"
                  type="number"
                  value={manualForm.moratoriumMonths}
                  onChange={(value) => updateManualForm('moratoriumMonths', value)}
                />
                <SelectField
                  label="Interest Type"
                  value={manualForm.interestType}
                  onChange={(value) => updateManualForm('interestType', value)}
                  options={interestTypeOptions}
                  required
                />
                <TextField
                  label="Current Interest Rate %"
                  type="number"
                  value={manualForm.currentInterestRate}
                  onChange={(value) => updateManualForm('currentInterestRate', value)}
                  required
                />
                <TextField
                  label="Penal Interest Rate %"
                  type="number"
                  value={manualForm.penalInterestRate}
                  onChange={(value) => updateManualForm('penalInterestRate', value)}
                />
                <SelectField
                  label="Repayment Frequency"
                  value={manualForm.repaymentFrequency}
                  onChange={(value) => updateManualForm('repaymentFrequency', value)}
                  options={repaymentFrequencyOptions}
                  required
                />
                <SelectField
                  label="Repayment Mode"
                  value={manualForm.repaymentMode}
                  onChange={(value) => updateManualForm('repaymentMode', value)}
                  options={repaymentModeOptions}
                  required
                />
                <SelectField
                  label="Day Count Convention"
                  value={manualForm.dayCountConvention}
                  onChange={(value) => updateManualForm('dayCountConvention', value)}
                  options={dayCountOptions}
                  required
                />
                <TextField
                  label="Current EMI / EPI Amount"
                  type="number"
                  value={manualForm.currentEmiAmount}
                  onChange={(value) => updateManualForm('currentEmiAmount', value)}
                />
                <TextField
                  label="Days Past Due"
                  type="number"
                  value={manualForm.daysPastDue}
                  onChange={(value) => updateManualForm('daysPastDue', value)}
                />
                <SelectField
                  label="Asset Classification"
                  value={manualForm.assetClassification}
                  onChange={(value) => updateManualForm('assetClassification', value)}
                  options={ASSET_CLASSIFICATION_OPTIONS}
                />
                <TextField
                  label="NPA Date"
                  type="date"
                  value={manualForm.npaDate}
                  onChange={(value) => updateManualForm('npaDate', value)}
                />
                <div className="space-y-1.5 md:col-span-2">
                  <Label>Purpose</Label>
                  <Textarea
                    value={manualForm.purpose}
                    onChange={(event) => updateManualForm('purpose', event.target.value)}
                    rows={3}
                  />
                </div>
                <div className="space-y-1.5 md:col-span-2">
                  <Label>Remarks</Label>
                  <Textarea
                    value={manualForm.remarks}
                    onChange={(event) => updateManualForm('remarks', event.target.value)}
                    rows={3}
                  />
                </div>
                <div className="flex items-center gap-2 md:col-span-4">
                  <Checkbox
                    id="createHistoricalReceipts"
                    checked={manualForm.createHistoricalReceipts}
                    onCheckedChange={(checked) =>
                      updateManualForm('createHistoricalReceipts', checked === true)
                    }
                  />
                  <Label htmlFor="createHistoricalReceipts" className="text-sm font-normal">
                    Create LMS receipt history for paid EMI rows
                  </Label>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0">
                <CardTitle className="text-base">Historical EMI / EPI Rows</CardTitle>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setManualInstallments((current) => [
                      ...current,
                      emptyInstallment(current.length),
                    ])
                  }
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Row
                </Button>
              </CardHeader>
              <CardContent className="space-y-4">
                {manualInstallments.map((row, index) => (
                  <div key={index} className="rounded-md border p-4">
                    <div className="mb-4 flex items-center justify-between">
                      <div className="font-medium">EMI Row {index + 1}</div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        disabled={manualInstallments.length === 1}
                        onClick={() =>
                          setManualInstallments((current) =>
                            current.filter((_, rowIndex) => rowIndex !== index),
                          )
                        }
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="grid gap-4 md:grid-cols-4">
                      <TextField
                        label="Installment No."
                        type="number"
                        value={row.installmentNumber}
                        onChange={(value) => updateInstallment(index, 'installmentNumber', value)}
                      />
                      <TextField
                        label="Due Date"
                        type="date"
                        value={row.dueDate}
                        onChange={(value) => updateInstallment(index, 'dueDate', value)}
                      />
                      <TextField
                        label="Opening Balance"
                        type="number"
                        value={row.openingBalance}
                        onChange={(value) => updateInstallment(index, 'openingBalance', value)}
                      />
                      <TextField
                        label="Closing Balance"
                        type="number"
                        value={row.closingBalance}
                        onChange={(value) => updateInstallment(index, 'closingBalance', value)}
                      />
                      <TextField
                        label="Principal Due"
                        type="number"
                        value={row.principalAmount}
                        onChange={(value) => updateInstallment(index, 'principalAmount', value)}
                      />
                      <TextField
                        label="Interest Due"
                        type="number"
                        value={row.interestAmount}
                        onChange={(value) => updateInstallment(index, 'interestAmount', value)}
                      />
                      <TextField
                        label="EMI / EPI Amount"
                        type="number"
                        value={row.emiAmount}
                        onChange={(value) => updateInstallment(index, 'emiAmount', value)}
                      />
                      <SelectField
                        label="Status"
                        value={row.status}
                        onChange={(value) => updateInstallment(index, 'status', value)}
                        options={INSTALLMENT_STATUS_OPTIONS}
                      />
                      <TextField
                        label="Principal Paid"
                        type="number"
                        value={row.principalPaid}
                        onChange={(value) => updateInstallment(index, 'principalPaid', value)}
                      />
                      <TextField
                        label="Interest Paid"
                        type="number"
                        value={row.interestPaid}
                        onChange={(value) => updateInstallment(index, 'interestPaid', value)}
                      />
                      <TextField
                        label="Penal Due"
                        type="number"
                        value={row.penalInterestDue}
                        onChange={(value) => updateInstallment(index, 'penalInterestDue', value)}
                      />
                      <TextField
                        label="Penal Paid"
                        type="number"
                        value={row.penalInterestPaid}
                        onChange={(value) => updateInstallment(index, 'penalInterestPaid', value)}
                      />
                      <TextField
                        label="Paid Date"
                        type="date"
                        value={row.paidDate}
                        onChange={(value) => updateInstallment(index, 'paidDate', value)}
                      />
                      <TextField
                        label="Receipt Reference"
                        value={row.receiptReference}
                        onChange={(value) => updateInstallment(index, 'receiptReference', value)}
                      />
                      <SelectField
                        label="Receipt Mode"
                        value={row.receiptMode}
                        onChange={(value) => updateInstallment(index, 'receiptMode', value)}
                        options={receiptModeOptions}
                      />
                      <TextField
                        label="Remarks"
                        value={row.remarks}
                        onChange={(value) => updateInstallment(index, 'remarks', value)}
                      />
                    </div>
                  </div>
                ))}

                <div className="flex justify-end gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    disabled={isManualValidating}
                    onClick={() => runManualOnboarding(true)}
                  >
                    {isManualValidating ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <CheckCircle2 className="mr-2 h-4 w-4" />
                    )}
                    Validate Manual Entry
                  </Button>
                  <Button
                    type="button"
                    disabled={isManualSaving}
                    onClick={() => runManualOnboarding(false)}
                  >
                    {isManualSaving ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Upload className="mr-2 h-4 w-4" />
                    )}
                    Record Historical Loan
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Onboarding Result</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-4">
              <div className="rounded-md border p-3">
                <div className="text-xs text-muted-foreground">Loans</div>
                <div className="text-xl font-semibold">{result.totalLoans}</div>
              </div>
              <div className="rounded-md border p-3">
                <div className="text-xs text-muted-foreground">Recorded</div>
                <div className="text-xl font-semibold">{result.importedLoans}</div>
              </div>
              <div className="rounded-md border p-3">
                <div className="text-xs text-muted-foreground">EMI Rows</div>
                <div className="text-xl font-semibold">{result.totalInstallments}</div>
              </div>
              <div className="rounded-md border p-3">
                <div className="text-xs text-muted-foreground">Receipts</div>
                <div className="text-xl font-semibold">{result.importedReceipts}</div>
              </div>
            </div>

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Loan Account</TableHead>
                  <TableHead className="text-right">EMI Rows</TableHead>
                  <TableHead className="text-right">Receipts</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {result.results.map((row, index) => (
                  <TableRow key={`${row.loanAccountNumber ?? 'loan'}-${index}`}>
                    <TableCell className="font-mono text-sm">
                      {row.loanAccountNumber ?? '—'}
                    </TableCell>
                    <TableCell className="text-right">{row.importedInstallments}</TableCell>
                    <TableCell className="text-right">{row.importedReceipts}</TableCell>
                    <TableCell>
                      {row.errors.length > 0 ? (
                        <span className="text-sm text-destructive">{row.errors.join('; ')}</span>
                      ) : row.loanAccountId ? (
                        <Button
                          variant="link"
                          className="h-auto p-0 text-sm"
                          onClick={() => navigate(`/admin/lending/accounts/${row.loanAccountId}`)}
                        >
                          View account
                        </Button>
                      ) : (
                        <span className="text-sm text-muted-foreground">Validated</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
