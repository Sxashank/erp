import { zodResolver } from '@hookform/resolvers/zod';
import { Receipt, Check, AlertCircle } from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';

import { PageHeader } from '@/components/common/PageHeader';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useLoanAccounts } from '@/hooks/lending/useLoanAccounts';
import { useCreateReceipt, type CreateReceiptResponse } from '@/hooks/lending/useReceipts';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import { formatCurrency } from '@/lib/utils';

const receiptSchema = z.object({
  loanAccountId: z.string().min(1, 'Loan account is required'),
  receiptAmount: z.string().min(1, 'Amount is required'),
  receiptDate: z.string().min(1, 'Receipt date is required'),
  valueDate: z.string().optional(),
  receiptType: z.string().default('REGULAR'),
  receiptMode: z.string().min(1, 'Receipt mode is required'),
  instrumentNumber: z.string().optional(),
  instrumentDate: z.string().optional(),
  instrumentBank: z.string().optional(),
  remarks: z.string().optional(),
});

type ReceiptFormInput = z.input<typeof receiptSchema>;
type ReceiptFormData = z.output<typeof receiptSchema>;

interface LoanAccountOption {
  id: string;
  number: string;
  entity: string;
  outstanding: number;
  overdue: number;
  nextDue: number;
  nextDueDate: string | null;
}

const receiptTypes = [
  { value: 'REGULAR', label: 'Regular Payment' },
  { value: 'PREPAYMENT', label: 'Prepayment' },
  { value: 'FORECLOSURE', label: 'Foreclosure' },
  { value: 'SUBVENTION', label: 'Subvention' },
  { value: 'INSURANCE_CLAIM', label: 'Insurance Claim' },
  { value: 'LEGAL_RECOVERY', label: 'Legal Recovery' },
  { value: 'OTS_SETTLEMENT', label: 'OTS Settlement' },
  { value: 'WRITE_BACK', label: 'Write Back' },
];

const receiptModes = [
  { value: 'CASH', label: 'Cash' },
  { value: 'CHEQUE', label: 'Cheque' },
  { value: 'DD', label: 'Demand Draft' },
  { value: 'NEFT', label: 'NEFT' },
  { value: 'RTGS', label: 'RTGS' },
  { value: 'IMPS', label: 'IMPS' },
  { value: 'UPI', label: 'UPI' },
  { value: 'NACH', label: 'NACH' },
];

export default function ReceiptCreate() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { data: loanAccountData, isLoading: isLoadingLoanAccounts } = useLoanAccounts({
    status: 'ACTIVE',
    pageSize: 100,
  });
  const loanAccounts: LoanAccountOption[] =
    loanAccountData?.items.map((loan) => {
      const outstanding = Number(loan.totalOutstanding);
      return {
        id: loan.id,
        number: loan.loanAccountNumber,
        entity: loan.entityName ?? 'Borrower entity',
        outstanding,
        overdue: loan.daysPastDue > 0 ? outstanding : 0,
        nextDue: outstanding > 0 ? outstanding : Number(loan.principalOutstanding),
        nextDueDate: loan.maturityDate,
      };
    }) ?? [];
  const [selectedLoan, setSelectedLoan] = useState<LoanAccountOption | null>(null);
  const [created, setCreated] = useState<CreateReceiptResponse | null>(null);
  const createReceipt = useCreateReceipt();

  const form = useForm<ReceiptFormInput, unknown, ReceiptFormData>({
    resolver: zodResolver(receiptSchema),
    defaultValues: {
      receiptType: 'REGULAR',
      receiptDate: new Date().toISOString().split('T')[0],
    },
  });

  const receiptMode = form.watch('receiptMode');

  const onLoanSelect = (loanId: string) => {
    const loan = loanAccounts.find((l) => l.id === loanId);
    setSelectedLoan(loan || null);
    form.setValue('loanAccountId', loanId);
  };

  const onSubmit = async (data: ReceiptFormData) => {
    const amountNum = Number(data.receiptAmount);
    if (!Number.isFinite(amountNum) || amountNum <= 0) {
      form.setError('receiptAmount', { message: 'Enter a positive amount' });
      return;
    }
    try {
      const response = await createReceipt.mutateAsync({
        loanAccountId: data.loanAccountId,
        receiptAmount: amountNum,
        receiptDate: data.receiptDate,
        valueDate: data.valueDate || undefined,
        receiptType: data.receiptType || 'REGULAR',
        receiptMode: data.receiptMode,
        instrumentNumber: data.instrumentNumber || undefined,
        instrumentDate: data.instrumentDate || undefined,
        instrumentBank: data.instrumentBank || undefined,
        remarks: data.remarks || undefined,
      });
      toast({
        title: 'Receipt created',
        description: `Receipt ${response.receiptNumber} recorded.`,
      });
      setCreated(response);
    } catch (err) {
      showErrorToast(err, toast);
    }
  };

  if (created) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
            <Check className="h-8 w-8 text-green-600" />
          </div>
          <h2 className="mb-2 text-2xl font-bold">Receipt Created Successfully</h2>
          <p className="mb-2 text-muted-foreground">
            Receipt number: <span className="font-mono">{created.receiptNumber}</span>
          </p>
          <p className="mb-6 text-muted-foreground">
            Status: {created.status} · Unallocated:{' '}
            {formatCurrency(Number(created.unallocatedAmount))}
          </p>
          <div className="flex justify-center gap-4">
            <Button variant="outline" onClick={() => navigate('/admin/lending/receipts')}>
              View All Receipts
            </Button>
            <Button onClick={() => navigate(`/admin/lending/receipts/${created.id}/allocate`)}>
              Allocate Receipt
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setCreated(null);
                form.reset({
                  receiptType: 'REGULAR',
                  receiptDate: new Date().toISOString().split('T')[0],
                });
              }}
            >
              Create Another
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Create Receipt"
        subtitle="Record a new payment receipt"
        breadcrumbs={[{ label: 'Receipts', to: '/admin/lending/receipts' }, { label: 'New' }]}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Form */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Receipt Details</CardTitle>
            <CardDescription>Enter payment information</CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                <FormField
                  control={form.control}
                  name="loanAccountId"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Loan Account *</FormLabel>
                      <Select onValueChange={onLoanSelect} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select loan account" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {isLoadingLoanAccounts && (
                            <SelectItem value="__loading" disabled>
                              Loading loan accounts...
                            </SelectItem>
                          )}
                          {loanAccounts.map((acc) => (
                            <SelectItem key={acc.id} value={acc.id}>
                              {acc.number} - {acc.entity}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="receiptAmount"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Receipt Amount *</FormLabel>
                        <FormControl>
                          <Input type="number" placeholder="Enter amount" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="receiptType"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Receipt Type</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select type" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {receiptTypes.map((type) => (
                              <SelectItem key={type.value} value={type.value}>
                                {type.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="receiptDate"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Receipt Date *</FormLabel>
                        <FormControl>
                          <Input type="date" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="valueDate"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Value Date</FormLabel>
                        <FormControl>
                          <Input type="date" {...field} />
                        </FormControl>
                        <FormDescription>Defaults to receipt date</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <FormField
                  control={form.control}
                  name="receiptMode"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Receipt Mode *</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select mode" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {receiptModes.map((mode) => (
                            <SelectItem key={mode.value} value={mode.value}>
                              {mode.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Instrument details for cheque/DD/NEFT/RTGS */}
                {['CHEQUE', 'DD', 'NEFT', 'RTGS', 'IMPS'].includes(receiptMode) && (
                  <div className="grid grid-cols-3 gap-4">
                    <FormField
                      control={form.control}
                      name="instrumentNumber"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>
                            {receiptMode === 'CHEQUE' || receiptMode === 'DD'
                              ? 'Cheque/DD Number'
                              : 'UTR Number'}
                          </FormLabel>
                          <FormControl>
                            <Input placeholder="Enter number" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="instrumentDate"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Instrument Date</FormLabel>
                          <FormControl>
                            <Input type="date" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="instrumentBank"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Bank</FormLabel>
                          <FormControl>
                            <Input placeholder="Bank name" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                )}

                <FormField
                  control={form.control}
                  name="remarks"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Remarks</FormLabel>
                      <FormControl>
                        <Textarea placeholder="Enter any remarks" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="flex justify-end gap-4">
                  <Button type="button" variant="outline" onClick={() => navigate(-1)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={createReceipt.isPending}>
                    <Receipt className="mr-2 h-4 w-4" />
                    {createReceipt.isPending ? 'Creating...' : 'Create Receipt'}
                  </Button>
                </div>
              </form>
            </Form>
          </CardContent>
        </Card>

        {/* Loan Details Panel */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Loan Summary</CardTitle>
            <CardDescription>
              {selectedLoan ? selectedLoan.number : 'Select a loan account'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {selectedLoan ? (
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground">Entity</p>
                  <p className="font-medium">{selectedLoan.entity}</p>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">Total Outstanding</p>
                  <p className="text-2xl font-bold">{formatCurrency(selectedLoan.outstanding)}</p>
                </div>

                {selectedLoan.overdue > 0 && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Overdue Amount</AlertTitle>
                    <AlertDescription>{formatCurrency(selectedLoan.overdue)}</AlertDescription>
                  </Alert>
                )}

                <div className="border-t pt-4">
                  <p className="text-sm text-muted-foreground">Next EMI Due</p>
                  <p className="font-medium">{formatCurrency(selectedLoan.nextDue)}</p>
                  <p className="text-sm text-muted-foreground">
                    Due on: {selectedLoan.nextDueDate ?? 'Not available'}
                  </p>
                </div>

                <div className="space-y-2 border-t pt-4">
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => form.setValue('receiptAmount', selectedLoan.nextDue.toString())}
                  >
                    Set EMI Amount
                  </Button>
                  {selectedLoan.overdue > 0 && (
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={() =>
                        form.setValue('receiptAmount', selectedLoan.overdue.toString())
                      }
                    >
                      Set Overdue Amount
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() =>
                      form.setValue(
                        'receiptAmount',
                        (selectedLoan.overdue + selectedLoan.nextDue).toString(),
                      )
                    }
                  >
                    Set Total Due
                  </Button>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-muted-foreground">
                <Receipt className="mx-auto mb-4 h-12 w-12 opacity-50" />
                <p>Select a loan account to view details</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
