/**
 * Customer Portal - Payments Page
 * Make payments, prepayments, and foreclosure
 */

import {
  CreditCard,
  IndianRupee,
  Loader2,
  Wallet,
  Smartphone,
  Building,
  AlertCircle,
  CheckCircle,
  ArrowRight,
  Calculator,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

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
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { portalDashboardApi, portalPaymentApi } from '@/services/portalApi';
import type { LoanSummary, UpcomingDue, PrepaymentQuote, ForeclosureQuote } from '@/types/portal';

import { logger } from '@/lib/logger';
type PaymentType = 'emi' | 'prepayment' | 'foreclosure';
type PaymentMode = 'UPI' | 'NETBANKING' | 'CARD';

export default function PortalPayments() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const preselectedLoan = searchParams.get('loan');

  const [loading, setLoading] = useState(true);
  const [loans, setLoans] = useState<LoanSummary[]>([]);
  const [upcomingDues, setUpcomingDues] = useState<UpcomingDue[]>([]);
  const [selectedLoan, setSelectedLoan] = useState<string>('');
  const [paymentType, setPaymentType] = useState<PaymentType>('emi');
  const [paymentMode, setPaymentMode] = useState<PaymentMode>('UPI');
  const [amount, setAmount] = useState('');
  const [prepaymentQuote, setPrepaymentQuote] = useState<PrepaymentQuote | null>(null);
  const [foreclosureQuote, setForeclosureQuote] = useState<ForeclosureQuote | null>(null);
  const [quoteLoading, setQuoteLoading] = useState(false);
  const [paymentInitiated, setPaymentInitiated] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (preselectedLoan && loans.length > 0) {
      setSelectedLoan(preselectedLoan);
    }
  }, [preselectedLoan, loans]);

  const fetchData = async () => {
    try {
      const [loansRes, duesRes] = await Promise.all([
        portalDashboardApi.getLoans(),
        portalDashboardApi.getUpcomingDues(),
      ]);
      setLoans(loansRes.data.filter((l: LoanSummary) => l.status === 'ACTIVE'));
      setUpcomingDues(duesRes.data);
    } catch (error) {
      logger.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };
  const selectedLoanData = loans.find((l) => l.id === selectedLoan);
  const selectedDue = upcomingDues.find((d) => d.loan_account_id === selectedLoan);

  const calculatePrepaymentQuote = async () => {
    if (!selectedLoan || !amount) return;

    setQuoteLoading(true);
    try {
      const response = await portalPaymentApi.getPrepaymentQuote({
        loan_account_id: selectedLoan,
        prepayment_amount: parseFloat(amount),
        prepayment_date: new Date().toISOString().split('T')[0],
      });
      setPrepaymentQuote(response.data);
    } catch (error) {
      logger.error('Failed to get prepayment quote:', error);
    } finally {
      setQuoteLoading(false);
    }
  };

  const calculateForeclosureQuote = async () => {
    if (!selectedLoan) return;

    setQuoteLoading(true);
    try {
      const response = await portalPaymentApi.getForeclosureQuote({
        loan_account_id: selectedLoan,
        foreclosure_date: new Date().toISOString().split('T')[0],
      });
      setForeclosureQuote(response.data);
    } catch (error) {
      logger.error('Failed to get foreclosure quote:', error);
    } finally {
      setQuoteLoading(false);
    }
  };

  const getPaymentAmount = (): number => {
    if (paymentType === 'emi' && selectedDue) {
      return selectedDue.total_due;
    }
    if (paymentType === 'prepayment' && prepaymentQuote) {
      return prepaymentQuote.total_payable;
    }
    if (paymentType === 'foreclosure' && foreclosureQuote) {
      return foreclosureQuote.total_payable;
    }
    return parseFloat(amount) || 0;
  };

  const handleInitiatePayment = async () => {
    setShowConfirmDialog(false);
    setPaymentInitiated(true);

    try {
      const response = await portalPaymentApi.initiatePayment({
        loan_account_id: selectedLoan,
        amount: getPaymentAmount(),
        payment_type: paymentType.toUpperCase(),
        payment_mode: paymentMode,
      });

      // In real implementation, redirect to payment gateway
      if (response.data.gateway_url) {
        window.location.href = response.data.gateway_url;
      }
    } catch (error) {
      logger.error('Failed to initiate payment:', error);
      setPaymentInitiated(false);
    }
  };

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
        title="Make a Payment"
        subtitle="Pay your EMI, make prepayments, or foreclose your loan"
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Payment Form */}
        <div className="space-y-6 lg:col-span-2">
          {/* Select Loan */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Select Loan Account</CardTitle>
            </CardHeader>
            <CardContent>
              <Select value={selectedLoan} onValueChange={setSelectedLoan}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a loan account" />
                </SelectTrigger>
                <SelectContent>
                  {loans.map((loan) => (
                    <SelectItem key={loan.id} value={loan.id}>
                      <div className="flex w-full items-center justify-between">
                        <span>{loan.loan_account_number}</span>
                        <span className="ml-4 text-gray-500">
                          {formatIndianCompactCurrency(loan.total_outstanding)} outstanding
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {selectedLoanData && (
                <div className="mt-4 rounded-lg bg-gray-50 p-4">
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-gray-500">Product</p>
                      <p className="font-medium">{selectedLoanData.product_name}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">EMI Amount</p>
                      <p className="font-medium">
                        {formatIndianCompactCurrency(selectedLoanData.emi_amount)}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500">Outstanding</p>
                      <p className="font-medium">
                        {formatIndianCompactCurrency(selectedLoanData.total_outstanding)}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Payment Type */}
          {selectedLoan && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Payment Type</CardTitle>
              </CardHeader>
              <CardContent>
                <Tabs
                  value={paymentType}
                  onValueChange={(v) => {
                    setPaymentType(v as PaymentType);
                    setPrepaymentQuote(null);
                    setForeclosureQuote(null);
                  }}
                >
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="emi">EMI Payment</TabsTrigger>
                    <TabsTrigger value="prepayment">Part Prepayment</TabsTrigger>
                    <TabsTrigger value="foreclosure">Foreclosure</TabsTrigger>
                  </TabsList>

                  <TabsContent value="emi" className="mt-4">
                    {selectedDue ? (
                      <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-emerald-700">Amount Due</p>
                            <p className="text-2xl font-bold text-emerald-800">
                              {formatIndianCompactCurrency(selectedDue.total_due)}
                            </p>
                            <p className="text-sm text-emerald-600">
                              Due Date: <DateDisplay date={selectedDue.due_date} />
                            </p>
                          </div>
                          {selectedDue.is_overdue && <Badge variant="destructive">Overdue</Badge>}
                        </div>
                        {selectedDue.overdue_amount > 0 && (
                          <p className="mt-2 text-sm text-red-600">
                            Includes overdue:{' '}
                            {formatIndianCompactCurrency(selectedDue.overdue_amount)}
                          </p>
                        )}
                      </div>
                    ) : (
                      <div className="p-4 text-center text-gray-500">
                        <CheckCircle className="mx-auto mb-2 h-8 w-8 text-green-500" />
                        <p>No EMI due at the moment</p>
                      </div>
                    )}
                  </TabsContent>

                  <TabsContent value="prepayment" className="mt-4 space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="prepayment-amount">Prepayment Amount</Label>
                      <div className="flex gap-2">
                        <div className="relative flex-1">
                          <IndianRupee className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                          <Input
                            id="prepayment-amount"
                            type="number"
                            placeholder="Enter amount"
                            value={amount}
                            onChange={(e) => setAmount(e.target.value)}
                            className="pl-10"
                          />
                        </div>
                        <Button
                          onClick={calculatePrepaymentQuote}
                          disabled={!amount || quoteLoading}
                        >
                          {quoteLoading ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <>
                              <Calculator className="mr-2 h-4 w-4" />
                              Calculate
                            </>
                          )}
                        </Button>
                      </div>
                    </div>

                    {prepaymentQuote && (
                      <div className="space-y-3 rounded-lg border border-blue-200 bg-blue-50 p-4">
                        <h4 className="font-medium text-blue-800">Prepayment Quote</h4>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <p className="text-gray-600">Prepayment Amount</p>
                            <p className="font-medium">
                              {formatIndianCompactCurrency(prepaymentQuote.prepayment_amount)}
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-600">Accrued Interest</p>
                            <p className="font-medium">
                              {formatIndianCompactCurrency(prepaymentQuote.accrued_interest)}
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-600">Prepayment Charges</p>
                            <p className="font-medium">
                              {formatIndianCompactCurrency(prepaymentQuote.prepayment_charges)}
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-600">GST on Charges</p>
                            <p className="font-medium">
                              {formatIndianCompactCurrency(prepaymentQuote.gst_on_charges)}
                            </p>
                          </div>
                        </div>
                        <div className="border-t border-blue-200 pt-3">
                          <div className="flex justify-between">
                            <span className="font-medium text-blue-800">Total Payable</span>
                            <span className="text-xl font-bold text-blue-800">
                              {formatIndianCompactCurrency(prepaymentQuote.total_payable)}
                            </span>
                          </div>
                          <p className="mt-1 text-sm text-green-600">
                            Interest Savings:{' '}
                            {formatIndianCompactCurrency(prepaymentQuote.interest_savings)}
                          </p>
                        </div>
                      </div>
                    )}
                  </TabsContent>

                  <TabsContent value="foreclosure" className="mt-4 space-y-4">
                    <div className="flex justify-end">
                      <Button onClick={calculateForeclosureQuote} disabled={quoteLoading}>
                        {quoteLoading ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <>
                            <Calculator className="mr-2 h-4 w-4" />
                            Get Foreclosure Quote
                          </>
                        )}
                      </Button>
                    </div>

                    {foreclosureQuote && (
                      <div className="space-y-3 rounded-lg border border-purple-200 bg-purple-50 p-4">
                        <h4 className="font-medium text-purple-800">Foreclosure Quote</h4>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <p className="text-gray-600">Outstanding Principal</p>
                            <p className="font-medium">
                              {formatIndianCompactCurrency(foreclosureQuote.outstanding_principal)}
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-600">Accrued Interest</p>
                            <p className="font-medium">
                              {formatIndianCompactCurrency(foreclosureQuote.accrued_interest)}
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-600">Pending Charges</p>
                            <p className="font-medium">
                              {formatIndianCompactCurrency(foreclosureQuote.pending_charges)}
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-600">Foreclosure Charges</p>
                            <p className="font-medium">
                              {formatIndianCompactCurrency(foreclosureQuote.foreclosure_charges)}
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-600">GST on Charges</p>
                            <p className="font-medium">
                              {formatIndianCompactCurrency(foreclosureQuote.gst_on_charges)}
                            </p>
                          </div>
                        </div>
                        <div className="border-t border-purple-200 pt-3">
                          <div className="flex justify-between">
                            <span className="font-medium text-purple-800">Total Payable</span>
                            <span className="text-xl font-bold text-purple-800">
                              {formatIndianCompactCurrency(foreclosureQuote.total_payable)}
                            </span>
                          </div>
                          <p className="mt-1 text-sm text-green-600">
                            Interest Savings:{' '}
                            {formatIndianCompactCurrency(foreclosureQuote.interest_savings)}
                          </p>
                          <p className="mt-1 text-xs text-gray-500">
                            Valid until: <DateDisplay date={foreclosureQuote.valid_until} />
                          </p>
                        </div>
                      </div>
                    )}
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          )}

          {/* Payment Mode */}
          {selectedLoan && getPaymentAmount() > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Payment Method</CardTitle>
              </CardHeader>
              <CardContent>
                <RadioGroup
                  value={paymentMode}
                  onValueChange={(v) => setPaymentMode(v as PaymentMode)}
                  className="grid grid-cols-1 gap-4 md:grid-cols-3"
                >
                  <Label
                    htmlFor="upi"
                    className={`flex cursor-pointer items-center gap-3 rounded-lg border p-4 transition-colors ${
                      paymentMode === 'UPI'
                        ? 'border-emerald-500 bg-emerald-50'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    <RadioGroupItem value="UPI" id="upi" />
                    <Smartphone className="h-5 w-5 text-emerald-600" />
                    <div>
                      <p className="font-medium">UPI</p>
                      <p className="text-xs text-gray-500">Pay via UPI apps</p>
                    </div>
                  </Label>

                  <Label
                    htmlFor="netbanking"
                    className={`flex cursor-pointer items-center gap-3 rounded-lg border p-4 transition-colors ${
                      paymentMode === 'NETBANKING'
                        ? 'border-emerald-500 bg-emerald-50'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    <RadioGroupItem value="NETBANKING" id="netbanking" />
                    <Building className="h-5 w-5 text-blue-600" />
                    <div>
                      <p className="font-medium">Net Banking</p>
                      <p className="text-xs text-gray-500">All major banks</p>
                    </div>
                  </Label>

                  <Label
                    htmlFor="card"
                    className={`flex cursor-pointer items-center gap-3 rounded-lg border p-4 transition-colors ${
                      paymentMode === 'CARD'
                        ? 'border-emerald-500 bg-emerald-50'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    <RadioGroupItem value="CARD" id="card" />
                    <CreditCard className="h-5 w-5 text-purple-600" />
                    <div>
                      <p className="font-medium">Debit/Credit Card</p>
                      <p className="text-xs text-gray-500">Visa, Mastercard, RuPay</p>
                    </div>
                  </Label>
                </RadioGroup>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Payment Summary */}
        <div className="space-y-6">
          <Card className="sticky top-24">
            <CardHeader>
              <CardTitle className="text-base">Payment Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {selectedLoan ? (
                <>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Loan Account</span>
                      <span className="font-medium">{selectedLoanData?.loan_account_number}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Payment Type</span>
                      <span className="font-medium capitalize">{paymentType}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Payment Mode</span>
                      <span className="font-medium">{paymentMode}</span>
                    </div>
                  </div>

                  <div className="border-t pt-4">
                    <div className="flex justify-between">
                      <span className="font-medium">Amount to Pay</span>
                      <span className="text-2xl font-bold text-emerald-600">
                        {formatIndianCompactCurrency(getPaymentAmount())}
                      </span>
                    </div>
                  </div>

                  <Button
                    className="w-full bg-emerald-600 hover:bg-emerald-700"
                    size="lg"
                    disabled={getPaymentAmount() === 0 || paymentInitiated}
                    onClick={() => setShowConfirmDialog(true)}
                  >
                    {paymentInitiated ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        Pay {formatIndianCompactCurrency(getPaymentAmount())}
                        <ArrowRight className="ml-2 h-4 w-4" />
                      </>
                    )}
                  </Button>

                  <p className="text-center text-xs text-gray-500">
                    You will be redirected to secure payment gateway
                  </p>
                </>
              ) : (
                <div className="py-8 text-center text-gray-500">
                  <Wallet className="mx-auto mb-4 h-12 w-12 opacity-50" />
                  <p>Select a loan account to proceed</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Upcoming Dues */}
          {upcomingDues.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Upcoming Dues</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {upcomingDues.slice(0, 3).map((due) => (
                  <div
                    key={due.loan_account_id}
                    className={`rounded-lg p-3 transition-colors ${
                      selectedLoan === due.loan_account_id
                        ? 'border border-emerald-200 bg-emerald-50'
                        : 'bg-gray-50 hover:bg-gray-100'
                    }`}
                  >
                    <div
                      className="flex cursor-pointer items-start justify-between"
                      onClick={() => setSelectedLoan(due.loan_account_id)}
                    >
                      <div>
                        <p className="text-sm font-medium">{due.loan_account_number}</p>
                        <p className="text-xs text-gray-500">
                          Due: <DateDisplay date={due.due_date} />
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold">{formatIndianCompactCurrency(due.total_due)}</p>
                        {due.is_overdue && (
                          <Badge variant="destructive" className="text-xs">
                            Overdue
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="mt-2 flex justify-end">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate('/portal/pay/coming-soon');
                        }}
                      >
                        Pay
                      </Button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Confirmation Dialog */}
      <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Payment</DialogTitle>
            <DialogDescription>
              Please review the payment details before proceeding
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="flex justify-between">
              <span className="text-gray-500">Loan Account</span>
              <span className="font-medium">{selectedLoanData?.loan_account_number}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Payment Type</span>
              <span className="font-medium capitalize">{paymentType}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Payment Mode</span>
              <span className="font-medium">{paymentMode}</span>
            </div>
            <div className="flex justify-between border-t pt-4">
              <span className="font-medium">Total Amount</span>
              <span className="text-xl font-bold text-emerald-600">
                {formatIndianCompactCurrency(getPaymentAmount())}
              </span>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConfirmDialog(false)}>
              Cancel
            </Button>
            <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={handleInitiatePayment}>
              Confirm & Pay
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
