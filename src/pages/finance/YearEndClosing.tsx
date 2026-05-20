import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Calendar,
  Check,
  CheckCircle2,
  FileText,
  Loader2,
  Lock,
  RefreshCw,
  XCircle,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
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
import { organizationsApi, financialYearsApi, yearEndApi } from '@/services/api';

import { logger } from "@/lib/logger";
interface Organization {
  id: string;
  name: string;
}

interface FinancialYear {
  id: string;
  code: string;
  name: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  is_closed: boolean;
}

interface PreviewAccount {
  account_id: string;
  account_code: string;
  account_name: string;
  closing_balance: number;
  balance_type: string;
}

interface YearEndPreview {
  can_close: boolean;
  net_profit_loss: number;
  profit_loss_type: string;
  retained_earnings_account_id: string | null;
  retained_earnings_account_name: string | null;
  accounts_to_carry_forward: PreviewAccount[];
  total_accounts: number;
  unclosed_periods: string[];
  unposted_vouchers: number;
  errors: string[];
  warnings: string[];
}

interface YearEndResult {
  success: boolean;
  message: string;
  net_profit_loss: number;
  profit_loss_type: string;
  closing_voucher_id: string | null;
  closing_voucher_number: string | null;
  accounts_carried_forward: number;
  new_year_id: string | null;
  errors: string[];
  warnings: string[];
}

type Step = 'select' | 'preview' | 'confirm' | 'result';

export function YearEndClosing() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>('select');
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [financialYears, setFinancialYears] = useState<FinancialYear[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [sourceYearId, setSourceYearId] = useState<string>('');
  const [targetYearId, setTargetYearId] = useState<string>('');
  const [skipValidations, setSkipValidations] = useState(false);
  const [preview, setPreview] = useState<YearEndPreview | null>(null);
  const [result, setResult] = useState<YearEndResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);

  const fetchOrganizations = useCallback(async () => {
    try {
      const response = await organizationsApi.list({ pageSize: 100 });
      setOrganizations(response.data.items);
      if (response.data.items.length > 0) {
        setSelectedOrgId(response.data.items[0].id);
      }
    } catch (error) {
      logger.error('Failed to fetch organizations:', error);
    }
  }, []);

  const fetchFinancialYears = useCallback(async () => {
    try {
      const response = await financialYearsApi.list({ pageSize: 100 });
      setFinancialYears(response.data.items);
    } catch (error) {
      logger.error('Failed to fetch financial years:', error);
    }
  }, [selectedOrgId]);

  useEffect(() => {
    fetchOrganizations();
  }, [fetchOrganizations]);

  useEffect(() => {
    if (selectedOrgId) {
      fetchFinancialYears();
    }
  }, [fetchFinancialYears, selectedOrgId]);

  const handleGeneratePreview = async () => {
    if (!sourceYearId) return;
    try {
      setPreviewLoading(true);
      const response = await yearEndApi.getPreview(sourceYearId);
      setPreview(response.data);
      setStep('preview');
    } catch (error) {
      logger.error('Failed to generate preview:', error);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleExecuteClosing = async () => {
    if (!sourceYearId || !targetYearId) return;
    try {
      setLoading(true);
      const response = await yearEndApi.execute({
        source_financial_year_id: sourceYearId,
        target_financial_year_id: targetYearId,
        skip_validations: skipValidations,
      });
      setResult(response.data);
      setStep('result');
    } catch (error) {
      setResult({
        success: false,
        message: 'Failed to execute year-end closing',
        net_profit_loss: 0,
        profit_loss_type: 'PROFIT',
        closing_voucher_id: null,
        closing_voucher_number: null,
        accounts_carried_forward: 0,
        new_year_id: null,
        errors: [error instanceof Error ? error.message : 'An unexpected error occurred'],
        warnings: [],
      });
      setStep('result');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount);

  const sourceYear = financialYears.find(fy => fy.id === sourceYearId);
  const targetYear = financialYears.find(fy => fy.id === targetYearId);
  const openYears = financialYears.filter(fy => !fy.is_closed);
  const availableTargetYears = financialYears.filter(
    fy => !fy.is_closed && fy.id !== sourceYearId && (sourceYear ? new Date(fy.start_date) > new Date(sourceYear.end_date) : true)
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Year-End Closing"
        subtitle="Close a financial year and carry forward balances"
      />

      {/* Progress Steps */}
      <div className="flex items-center justify-center space-x-4 py-4">
        <StepIndicator step={1} label="Select Years" active={step === 'select'} completed={step !== 'select'} />
        <div className="h-px w-8 bg-slate-300" />
        <StepIndicator step={2} label="Preview" active={step === 'preview'} completed={step === 'confirm' || step === 'result'} />
        <div className="h-px w-8 bg-slate-300" />
        <StepIndicator step={3} label="Confirm" active={step === 'confirm'} completed={step === 'result'} />
        <div className="h-px w-8 bg-slate-300" />
        <StepIndicator step={4} label="Complete" active={step === 'result'} completed={false} />
      </div>

      {/* Step 1: Select Years */}
      {step === 'select' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Select Financial Years
            </CardTitle>
            <CardDescription>
              Choose the financial year to close and the year to carry forward opening balances
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label>Organization</Label>
                <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select organization" />
                  </SelectTrigger>
                  <SelectContent>
                    {organizations.map((org) => (
                      <SelectItem key={org.id} value={org.id}>
                        {org.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Financial Year to Close</Label>
                <Select value={sourceYearId} onValueChange={setSourceYearId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select year to close" />
                  </SelectTrigger>
                  <SelectContent>
                    {openYears.map((fy) => (
                      <SelectItem key={fy.id} value={fy.id}>
                        {fy.name} {fy.is_current && '(Current)'}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Carry Forward to Year</Label>
                <Select value={targetYearId} onValueChange={setTargetYearId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select target year" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableTargetYears.length === 0 ? (
                      <div className="py-2 px-3 text-sm text-slate-500">
                        No available target year. Please create a new financial year first.
                      </div>
                    ) : (
                      availableTargetYears.map((fy) => (
                        <SelectItem key={fy.id} value={fy.id}>
                          {fy.name}
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {sourceYear && (
              <div className="bg-slate-50 rounded-lg p-4">
                <h4 className="font-medium text-slate-700 mb-2">Selected Year Details</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-slate-500">Code:</span>
                    <p className="font-medium">{sourceYear.code}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">Period:</span>
                    <p className="font-medium">
                      <DateDisplay date={sourceYear.start_date} /> - <DateDisplay date={sourceYear.end_date} />
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-500">Status:</span>
                    <p>
                      <Badge className={sourceYear.is_closed ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'}>
                        {sourceYear.is_closed ? 'Closed' : 'Open'}
                      </Badge>
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-500">Current:</span>
                    <p>
                      <Badge className={sourceYear.is_current ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-600'}>
                        {sourceYear.is_current ? 'Yes' : 'No'}
                      </Badge>
                    </p>
                  </div>
                </div>
              </div>
            )}

            <div className="flex justify-end">
              <Button
                onClick={handleGeneratePreview}
                disabled={!sourceYearId || !targetYearId || previewLoading}
              >
                {previewLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating Preview...
                  </>
                ) : (
                  <>
                    Generate Preview
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Preview */}
      {step === 'preview' && preview && (
        <div className="space-y-6">
          {/* Errors and Warnings */}
          {preview.errors.length > 0 && (
            <Alert variant="destructive">
              <XCircle className="h-4 w-4" />
              <AlertTitle>Cannot Proceed</AlertTitle>
              <AlertDescription>
                <ul className="list-disc list-inside mt-2">
                  {preview.errors.map((error, idx) => (
                    <li key={idx}>{error}</li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          )}

          {preview.warnings.length > 0 && (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Warnings</AlertTitle>
              <AlertDescription>
                <ul className="list-disc list-inside mt-2">
                  {preview.warnings.map((warning, idx) => (
                    <li key={idx}>{warning}</li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          )}

          {/* P&L Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Profit & Loss Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className={`rounded-lg p-6 text-center ${preview.profit_loss_type === 'PROFIT' ? 'bg-emerald-50' : 'bg-red-50'}`}>
                  <p className="text-sm text-slate-600">Net {preview.profit_loss_type}</p>
                  <p className={`text-3xl font-bold ${preview.profit_loss_type === 'PROFIT' ? 'text-emerald-600' : 'text-red-600'}`}>
                    {formatCurrency(preview.net_profit_loss)}
                  </p>
                </div>
                <div className="bg-purple-50 rounded-lg p-6 text-center">
                  <p className="text-sm text-slate-600">Transfer To</p>
                  <p className="text-lg font-semibold text-purple-700">
                    {preview.retained_earnings_account_name || 'Not Found'}
                  </p>
                </div>
                <div className="bg-blue-50 rounded-lg p-6 text-center">
                  <p className="text-sm text-slate-600">Accounts to Carry Forward</p>
                  <p className="text-3xl font-bold text-blue-700">{preview.total_accounts}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Accounts Preview */}
          <Card>
            <CardHeader>
              <CardTitle>Balance Sheet Accounts to Carry Forward</CardTitle>
              <CardDescription>
                These account balances will be carried forward as opening balances in the new year
              </CardDescription>
            </CardHeader>
            <CardContent>
              {preview.accounts_to_carry_forward.length === 0 ? (
                <p className="text-center text-slate-500 py-8">No accounts with balances to carry forward</p>
              ) : (
                <div className="max-h-96 overflow-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-slate-50">
                        <TableHead>Code</TableHead>
                        <TableHead>Account Name</TableHead>
                        <TableHead className="text-right">Closing Balance</TableHead>
                        <TableHead className="text-center">Type</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {preview.accounts_to_carry_forward.map((account) => (
                        <TableRow key={account.account_id}>
                          <TableCell className="font-mono text-sm">{account.account_code}</TableCell>
                          <TableCell>{account.account_name}</TableCell>
                          <TableCell className="text-right font-mono">
                            {formatCurrency(account.closing_balance)}
                          </TableCell>
                          <TableCell className="text-center">
                            <Badge className={account.balance_type === 'DR' ? 'bg-blue-100 text-blue-700' : 'bg-red-100 text-red-700'}>
                              {account.balance_type}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="flex justify-between">
            <Button variant="outline" onClick={() => setStep('select')}>
              Back
            </Button>
            <Button
              onClick={() => setStep('confirm')}
              disabled={!preview.can_close}
            >
              Proceed to Confirmation
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Step 3: Confirm */}
      {step === 'confirm' && preview && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-amber-500" />
              Confirm Year-End Closing
            </CardTitle>
            <CardDescription>
              Please review and confirm the following actions
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>This action cannot be easily undone</AlertTitle>
              <AlertDescription>
                Year-end closing will permanently close the selected financial year and update account opening balances.
              </AlertDescription>
            </Alert>

            <div className="bg-slate-50 rounded-lg p-6 space-y-4">
              <h4 className="font-semibold text-lg">Summary of Actions</h4>
              <ul className="space-y-3">
                <li className="flex items-start gap-3">
                  <FileText className="h-5 w-5 text-blue-500 mt-0.5" />
                  <div>
                    <p className="font-medium">Create Closing Voucher</p>
                    <p className="text-sm text-slate-600">
                      Transfer Net {preview.profit_loss_type} of {formatCurrency(preview.net_profit_loss)} to Retained Earnings
                    </p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <RefreshCw className="h-5 w-5 text-emerald-500 mt-0.5" />
                  <div>
                    <p className="font-medium">Carry Forward Balances</p>
                    <p className="text-sm text-slate-600">
                      Update opening balances for {preview.total_accounts} accounts in {targetYear?.name}
                    </p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <Lock className="h-5 w-5 text-red-500 mt-0.5" />
                  <div>
                    <p className="font-medium">Close Financial Year</p>
                    <p className="text-sm text-slate-600">
                      Mark {sourceYear?.name} as closed (no further entries allowed)
                    </p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="h-5 w-5 text-purple-500 mt-0.5" />
                  <div>
                    <p className="font-medium">Set New Current Year</p>
                    <p className="text-sm text-slate-600">
                      Set {targetYear?.name} as the current financial year
                    </p>
                  </div>
                </li>
              </ul>
            </div>

            {preview.unclosed_periods.length > 0 && (
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="skip-validations"
                  checked={skipValidations}
                  onCheckedChange={(checked) => setSkipValidations(checked === true)}
                />
                <Label htmlFor="skip-validations" className="text-sm cursor-pointer">
                  Skip period closure validation (not recommended)
                </Label>
              </div>
            )}

            <div className="flex justify-between pt-4">
              <Button variant="outline" onClick={() => setStep('preview')}>
                Back to Preview
              </Button>
              <Button
                variant="destructive"
                onClick={handleExecuteClosing}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Lock className="mr-2 h-4 w-4" />
                    Execute Year-End Closing
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 4: Result */}
      {step === 'result' && result && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {result.success ? (
                <>
                  <CheckCircle2 className="h-6 w-6 text-emerald-500" />
                  Year-End Closing Completed
                </>
              ) : (
                <>
                  <XCircle className="h-6 w-6 text-red-500" />
                  Year-End Closing Failed
                </>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {result.success ? (
              <>
                <Alert className="bg-emerald-50 border-emerald-200">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  <AlertTitle className="text-emerald-800">Success</AlertTitle>
                  <AlertDescription className="text-emerald-700">
                    {result.message}
                  </AlertDescription>
                </Alert>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-slate-50 rounded-lg p-4 text-center">
                    <p className="text-sm text-slate-500">Net {result.profit_loss_type}</p>
                    <p className="text-2xl font-bold text-slate-800">
                      {formatCurrency(result.net_profit_loss)}
                    </p>
                  </div>
                  <div className="bg-slate-50 rounded-lg p-4 text-center">
                    <p className="text-sm text-slate-500">Accounts Carried Forward</p>
                    <p className="text-2xl font-bold text-slate-800">
                      {result.accounts_carried_forward}
                    </p>
                  </div>
                  <div className="bg-slate-50 rounded-lg p-4 text-center">
                    <p className="text-sm text-slate-500">Closing Voucher</p>
                    <p className="text-lg font-bold text-blue-600">
                      {result.closing_voucher_number || 'N/A'}
                    </p>
                  </div>
                </div>
              </>
            ) : (
              <Alert variant="destructive">
                <XCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>
                  <ul className="list-disc list-inside mt-2">
                    {result.errors.map((error, idx) => (
                      <li key={idx}>{error}</li>
                    ))}
                  </ul>
                </AlertDescription>
              </Alert>
            )}

            <div className="flex justify-center gap-4 pt-4">
              {result.success ? (
                <>
                  {result.closing_voucher_id && (
                    <Button
                      variant="outline"
                      onClick={() => navigate(`/admin/finance/vouchers/${result.closing_voucher_id}`)}
                    >
                      <FileText className="mr-2 h-4 w-4" />
                      View Closing Voucher
                    </Button>
                  )}
                  <Button onClick={() => navigate('/admin/finance/financial-years')}>
                    <Calendar className="mr-2 h-4 w-4" />
                    Go to Financial Years
                  </Button>
                </>
              ) : (
                <Button onClick={() => setStep('select')}>
                  Try Again
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function StepIndicator({
  step,
  label,
  active,
  completed,
}: {
  step: number;
  label: string;
  active: boolean;
  completed: boolean;
}) {
  return (
    <div className="flex flex-col items-center">
      <div
        className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
          completed
            ? 'bg-emerald-500 text-white'
            : active
            ? 'bg-blue-500 text-white'
            : 'bg-slate-200 text-slate-500'
        }`}
      >
        {completed ? <Check className="h-5 w-5" /> : step}
      </div>
      <span className={`text-xs mt-1 ${active ? 'text-blue-600 font-medium' : 'text-slate-500'}`}>
        {label}
      </span>
    </div>
  );
}
