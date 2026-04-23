import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowLeft, Receipt, Check, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/common/PageHeader';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { formatCurrency } from '@/lib/utils';

const receiptSchema = z.object({
  loan_account_id: z.string().min(1, 'Loan account is required'),
  receipt_amount: z.string().min(1, 'Amount is required'),
  receipt_date: z.string().min(1, 'Receipt date is required'),
  value_date: z.string().optional(),
  receipt_type: z.string().default('REGULAR'),
  receipt_mode: z.string().min(1, 'Receipt mode is required'),
  instrument_number: z.string().optional(),
  instrument_date: z.string().optional(),
  instrument_bank: z.string().optional(),
  remarks: z.string().optional(),
});

type ReceiptFormData = z.infer<typeof receiptSchema>;

// Mock data
const loanAccounts = [
  {
    id: '1',
    number: 'SMFC/LA/2024/00125',
    entity: 'ABC Trading Co.',
    outstanding: 15000000,
    overdue: 500000,
    next_emi: 450000,
    next_due_date: '2025-01-15',
  },
  {
    id: '2',
    number: 'SMFC/LA/2024/00089',
    entity: 'XYZ Industries',
    outstanding: 25000000,
    overdue: 0,
    next_emi: 750000,
    next_due_date: '2025-01-20',
  },
];

const receiptTypes = [
  { value: 'REGULAR', label: 'Regular Payment' },
  { value: 'PREPAYMENT', label: 'Prepayment' },
  { value: 'PARTIAL_PREPAYMENT', label: 'Partial Prepayment' },
  { value: 'FORECLOSURE', label: 'Foreclosure' },
  { value: 'BOUNCE_RECOVERY', label: 'Bounce Recovery' },
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
  const [isLoading, setIsLoading] = useState(false);
  const [selectedLoan, setSelectedLoan] = useState<typeof loanAccounts[0] | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);

  const form = useForm<ReceiptFormData>({
    resolver: zodResolver(receiptSchema) as any,
    defaultValues: {
      receipt_type: 'REGULAR',
      receipt_date: new Date().toISOString().split('T')[0],
    },
  });

  const receiptMode = form.watch('receipt_mode');

  const onLoanSelect = (loanId: string) => {
    const loan = loanAccounts.find((l) => l.id === loanId);
    setSelectedLoan(loan || null);
    form.setValue('loan_account_id', loanId);
  };

  const onSubmit = async (data: ReceiptFormData) => {
    setIsLoading(true);
    // API call would go here
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setIsLoading(false);
    setShowSuccess(true);
  };

  if (showSuccess) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Check className="h-8 w-8 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold mb-2">Receipt Created Successfully</h2>
          <p className="text-muted-foreground mb-6">
            Receipt number: <span className="font-mono">RCP/2025/00245</span>
          </p>
          <div className="flex gap-4 justify-center">
            <Button variant="outline" onClick={() => navigate('/lending/receipts')}>
              View All Receipts
            </Button>
            <Button onClick={() => navigate('/lending/receipts/allocate')}>
              Allocate Receipt
            </Button>
            <Button variant="outline" onClick={() => setShowSuccess(false)}>
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
        breadcrumbs={[
          { label: 'Receipts', to: '/lending/receipts' },
          { label: 'New' },
        ]}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Receipt Details</CardTitle>
            <CardDescription>Enter payment information</CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit as any)} className="space-y-6">
                <FormField
                  control={form.control}
                  name="loan_account_id"
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
                    name="receipt_amount"
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
                    name="receipt_type"
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
                    name="receipt_date"
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
                    name="value_date"
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
                  name="receipt_mode"
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
                      name="instrument_number"
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
                      name="instrument_date"
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
                      name="instrument_bank"
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

                <div className="flex gap-4 justify-end">
                  <Button type="button" variant="outline" onClick={() => navigate(-1)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={isLoading}>
                    <Receipt className="h-4 w-4 mr-2" />
                    {isLoading ? 'Creating...' : 'Create Receipt'}
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
                  <p className="text-2xl font-bold">
                    {formatCurrency(selectedLoan.outstanding)}
                  </p>
                </div>

                {selectedLoan.overdue > 0 && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Overdue Amount</AlertTitle>
                    <AlertDescription>
                      {formatCurrency(selectedLoan.overdue)}
                    </AlertDescription>
                  </Alert>
                )}

                <div className="border-t pt-4">
                  <p className="text-sm text-muted-foreground">Next EMI Due</p>
                  <p className="font-medium">{formatCurrency(selectedLoan.next_emi)}</p>
                  <p className="text-sm text-muted-foreground">
                    Due on: {selectedLoan.next_due_date}
                  </p>
                </div>

                <div className="border-t pt-4 space-y-2">
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() =>
                      form.setValue('receipt_amount', selectedLoan.next_emi.toString())
                    }
                  >
                    Set EMI Amount
                  </Button>
                  {selectedLoan.overdue > 0 && (
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={() =>
                        form.setValue('receipt_amount', selectedLoan.overdue.toString())
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
                        'receipt_amount',
                        (selectedLoan.overdue + selectedLoan.next_emi).toString()
                      )
                    }
                  >
                    Set Total Due
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Receipt className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Select a loan account to view details</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
