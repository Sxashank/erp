import { zodResolver } from '@hookform/resolvers/zod';
import { Save, Search } from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { z } from 'zod';

import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { AmountInput } from '@/components/lending/common/AmountInput';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { Badge } from '@/components/ui/badge';
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
import { Textarea } from '@/components/ui/textarea';
import { logger } from '@/lib/logger';
const receiptSchema = z.object({
  loanAccountId: z.string().min(1, 'Loan account is required'),
  amount: z.number().min(1, 'Amount is required'),
  receiptDate: z.string().min(1, 'Receipt date is required'),
  valueDate: z.string().min(1, 'Value date is required'),
  mode: z.enum(['CASH', 'CHEQUE', 'NEFT', 'RTGS', 'IMPS', 'UPI', 'DD']),
  instrumentNumber: z.string().optional(),
  instrumentDate: z.string().optional(),
  bankName: z.string().optional(),
  type: z.enum(['EMI', 'PART_PAYMENT', 'PREPAYMENT', 'PENAL', 'CHARGES', 'PROCESSING_FEE']),
  remarks: z.string().optional(),
});

type ReceiptFormData = z.infer<typeof receiptSchema>;

// Loan account context loads via useLoanAccount(accountId) once wired
// (passed via `?accountId=` query param). Until then, the form starts
// with no preselected account — user picks one explicitly.
const emptyLoanAccount = {
  id: '',
  loanAccountNumber: '',
  entityName: '',
  productName: '',
  totalOutstanding: 0,
  principalOutstanding: 0,
  interestOutstanding: 0,
  penalOutstanding: 0,
  otherCharges: 0,
  dpd: 0,
  overdues: [] as {
    type: string;
    dueDate: string;
    principal: number;
    interest: number;
    total: number;
  }[],
};

export default function ReceiptForm() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const accountId = searchParams.get('accountId');
  const [selectedAccount, setSelectedAccount] = useState(accountId ? emptyLoanAccount : null);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<ReceiptFormData>({
    resolver: zodResolver(receiptSchema),
    defaultValues: {
      loanAccountId: accountId || '',
      receiptDate: new Date().toISOString().split('T')[0],
      valueDate: new Date().toISOString().split('T')[0],
      mode: 'NEFT',
      type: 'EMI',
    },
  });

  const paymentMode = watch('mode');
  const receiptAmount = watch('amount') || 0;

  const onSubmit = async (data: ReceiptFormData) => {
    logger.debug('Receipt data:', data);
    navigate('/admin/lending/receipts');
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Record Receipt"
        subtitle="Record a new payment receipt against a loan account"
        breadcrumbs={[{ label: 'Receipts', to: '/admin/lending/receipts' }, { label: 'New' }]}
        actions={
          <Button onClick={handleSubmit(onSubmit)} disabled={isSubmitting}>
            <Save className="mr-2 h-4 w-4" />
            Save Receipt
          </Button>
        }
      />

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="grid gap-6 md:grid-cols-3">
          {/* Left Column - Main Form */}
          <div className="space-y-6 md:col-span-2">
            {/* Loan Account Selection */}
            <Card>
              <CardHeader>
                <CardTitle>Loan Account</CardTitle>
                <CardDescription>Select the loan account for this receipt</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {!selectedAccount ? (
                  <div className="space-y-2">
                    <Label>Search Loan Account</Label>
                    <div className="relative">
                      <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                      <Input
                        placeholder="Enter loan account number or entity name..."
                        className="pl-8"
                      />
                    </div>
                  </div>
                ) : (
                  <div className="rounded-lg border bg-muted/50 p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-mono font-medium">{selectedAccount.loanAccountNumber}</p>
                        <p className="text-sm">{selectedAccount.entityName}</p>
                        <p className="text-sm text-muted-foreground">
                          {selectedAccount.productName}
                        </p>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setSelectedAccount(null)}
                      >
                        Change
                      </Button>
                    </div>
                    <input
                      type="hidden"
                      {...register('loanAccountId')}
                      value={selectedAccount.id}
                    />
                  </div>
                )}
                {errors.loanAccountId && (
                  <p className="text-sm text-destructive">{errors.loanAccountId.message}</p>
                )}
              </CardContent>
            </Card>

            {/* Receipt Details */}
            <Card>
              <CardHeader>
                <CardTitle>Receipt Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Receipt Amount *</Label>
                    <AmountInput
                      value={watch('amount') || 0}
                      onChange={(v) => setValue('amount', v ?? 0)}
                      placeholder="Enter amount"
                    />
                    {errors.amount && (
                      <p className="text-sm text-destructive">{errors.amount.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label>Receipt Type *</Label>
                    <Select
                      value={watch('type')}
                      onValueChange={(v) => setValue('type', v as ReceiptFormData['type'])}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="EMI">EMI Payment</SelectItem>
                        <SelectItem value="PART_PAYMENT">Part Payment</SelectItem>
                        <SelectItem value="PREPAYMENT">Prepayment</SelectItem>
                        <SelectItem value="PENAL">Penal Interest</SelectItem>
                        <SelectItem value="CHARGES">Other Charges</SelectItem>
                        <SelectItem value="PROCESSING_FEE">Processing Fee</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="receiptDate">Receipt Date *</Label>
                    <Input id="receiptDate" type="date" {...register('receiptDate')} />
                    {errors.receiptDate && (
                      <p className="text-sm text-destructive">{errors.receiptDate.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="valueDate">Value Date *</Label>
                    <Input id="valueDate" type="date" {...register('valueDate')} />
                    {errors.valueDate && (
                      <p className="text-sm text-destructive">{errors.valueDate.message}</p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Payment Mode */}
            <Card>
              <CardHeader>
                <CardTitle>Payment Mode</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Payment Mode *</Label>
                  <Select
                    value={paymentMode}
                    onValueChange={(v) => setValue('mode', v as ReceiptFormData['mode'])}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select mode" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="CASH">Cash</SelectItem>
                      <SelectItem value="CHEQUE">Cheque</SelectItem>
                      <SelectItem value="DD">Demand Draft</SelectItem>
                      <SelectItem value="NEFT">NEFT</SelectItem>
                      <SelectItem value="RTGS">RTGS</SelectItem>
                      <SelectItem value="IMPS">IMPS</SelectItem>
                      <SelectItem value="UPI">UPI</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {['CHEQUE', 'DD'].includes(paymentMode) && (
                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="space-y-2">
                      <Label htmlFor="instrumentNumber">Cheque/DD Number</Label>
                      <Input
                        id="instrumentNumber"
                        placeholder="Enter number"
                        {...register('instrumentNumber')}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="instrumentDate">Cheque/DD Date</Label>
                      <Input id="instrumentDate" type="date" {...register('instrumentDate')} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="bankName">Bank Name</Label>
                      <Input id="bankName" placeholder="Drawn on bank" {...register('bankName')} />
                    </div>
                  </div>
                )}

                {['NEFT', 'RTGS', 'IMPS', 'UPI'].includes(paymentMode) && (
                  <div className="space-y-2">
                    <Label htmlFor="instrumentNumber">Transaction Reference</Label>
                    <Input
                      id="instrumentNumber"
                      placeholder="Enter UTR/Transaction ID"
                      {...register('instrumentNumber')}
                    />
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="remarks">Remarks</Label>
                  <Textarea
                    id="remarks"
                    placeholder="Any additional notes..."
                    rows={3}
                    {...register('remarks')}
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Account Summary */}
          <div className="space-y-6">
            {selectedAccount && (
              <>
                {/* Outstanding Summary */}
                <Card>
                  <CardHeader>
                    <CardTitle>Outstanding Summary</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableBody>
                        <TableRow>
                          <TableCell className="font-medium">Principal</TableCell>
                          <TableCell className="text-right">
                            <AmountDisplay amount={selectedAccount.principalOutstanding} />
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell className="font-medium">Interest</TableCell>
                          <TableCell className="text-right">
                            <AmountDisplay amount={selectedAccount.interestOutstanding} />
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell className="font-medium">Penal</TableCell>
                          <TableCell className="text-right">
                            <AmountDisplay amount={selectedAccount.penalOutstanding} />
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell className="font-medium">Other Charges</TableCell>
                          <TableCell className="text-right">
                            <AmountDisplay amount={selectedAccount.otherCharges} />
                          </TableCell>
                        </TableRow>
                        <TableRow className="bg-muted/50 font-bold">
                          <TableCell>Total Outstanding</TableCell>
                          <TableCell className="text-right">
                            <AmountDisplay amount={selectedAccount.totalOutstanding} />
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>

                {/* Overdue Details */}
                {selectedAccount.overdues.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Overdue EMIs</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Due Date</TableHead>
                            <TableHead className="text-right">Amount</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {selectedAccount.overdues.map((overdue, index) => (
                            <TableRow key={index}>
                              <TableCell>
                                <DateDisplay date={overdue.dueDate} />
                              </TableCell>
                              <TableCell className="text-right">
                                <AmountDisplay amount={overdue.total} />
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>
                )}

                {/* Receipt Preview */}
                {receiptAmount > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Receipt Preview</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="rounded-lg border bg-green-50 p-4">
                        <div className="text-center">
                          <p className="text-sm text-muted-foreground">Amount Being Received</p>
                          <p className="text-2xl font-bold text-green-600">
                            <AmountDisplay amount={receiptAmount} showFull />
                          </p>
                        </div>
                      </div>
                      <p className="mt-4 text-xs text-muted-foreground">
                        This amount will be allocated to the outstanding dues based on the
                        configured waterfall priority: Penal → Charges → Overdue Interest → Current
                        Interest → Overdue Principal → Current Principal
                      </p>
                    </CardContent>
                  </Card>
                )}
              </>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}
