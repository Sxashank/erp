import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowLeft, Banknote, Check, AlertCircle } from 'lucide-react';
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

const disbursementSchema = z.object({
  loan_account_id: z.string().min(1, 'Loan account is required'),
  requested_amount: z.string().min(1, 'Amount is required'),
  beneficiary_name: z.string().min(1, 'Beneficiary name is required'),
  beneficiary_account: z.string().min(1, 'Account number is required'),
  beneficiary_ifsc: z.string().min(11, 'Valid IFSC is required').max(11),
  beneficiary_bank: z.string().optional(),
  disbursement_mode: z.string().default('RTGS'),
  scheduled_date: z.string().optional(),
  purpose: z.string().optional(),
});

type DisbursementFormData = z.infer<typeof disbursementSchema>;

// Mock data
const loanAccounts = [
  {
    id: '1',
    number: 'SMFC/LA/2025/00145',
    entity: 'Sunrise Industries',
    sanctioned: 15000000,
    disbursed: 5000000,
    undisbursed: 10000000,
    bank_accounts: [
      { name: 'Primary Account', account: '1234567890', ifsc: 'HDFC0001234', bank: 'HDFC Bank' },
      { name: 'Secondary Account', account: '0987654321', ifsc: 'ICIC0005678', bank: 'ICICI Bank' },
    ],
  },
  {
    id: '2',
    number: 'SMFC/LA/2025/00146',
    entity: 'Metro Logistics',
    sanctioned: 25000000,
    disbursed: 0,
    undisbursed: 25000000,
    bank_accounts: [
      { name: 'Current Account', account: '5555666677', ifsc: 'SBIN0009999', bank: 'State Bank' },
    ],
  },
];

const disbursementModes = [
  { value: 'RTGS', label: 'RTGS' },
  { value: 'NEFT', label: 'NEFT' },
  { value: 'IMPS', label: 'IMPS' },
  { value: 'CHEQUE', label: 'Cheque' },
  { value: 'DD', label: 'Demand Draft' },
];

export default function DisbursementCreate() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [selectedLoan, setSelectedLoan] = useState<typeof loanAccounts[0] | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);

  const form = useForm<DisbursementFormData>({
    resolver: zodResolver(disbursementSchema) as any,
    defaultValues: {
      disbursement_mode: 'RTGS',
    },
  });

  const onLoanSelect = (loanId: string) => {
    const loan = loanAccounts.find((l) => l.id === loanId);
    setSelectedLoan(loan || null);
    form.setValue('loan_account_id', loanId);
    // Pre-fill beneficiary if first account available
    if (loan?.bank_accounts?.[0]) {
      const acc = loan.bank_accounts[0];
      form.setValue('beneficiary_name', loan.entity);
      form.setValue('beneficiary_account', acc.account);
      form.setValue('beneficiary_ifsc', acc.ifsc);
      form.setValue('beneficiary_bank', acc.bank);
    }
  };

  const onBankAccountSelect = (index: number) => {
    if (selectedLoan?.bank_accounts?.[index]) {
      const acc = selectedLoan.bank_accounts[index];
      form.setValue('beneficiary_account', acc.account);
      form.setValue('beneficiary_ifsc', acc.ifsc);
      form.setValue('beneficiary_bank', acc.bank);
    }
  };

  const onSubmit = async (data: DisbursementFormData) => {
    setIsLoading(true);
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
          <h2 className="text-2xl font-bold mb-2">Disbursement Request Created</h2>
          <p className="text-muted-foreground mb-6">
            Reference: <span className="font-mono">SMFC/LA/2025/00145/D001</span>
          </p>
          <Alert className="max-w-md mx-auto mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Pending Approval</AlertTitle>
            <AlertDescription>
              This disbursement request is pending verification and approval.
            </AlertDescription>
          </Alert>
          <div className="flex gap-4 justify-center">
            <Button variant="outline" onClick={() => navigate('/lending/disbursements')}>
              View All Disbursements
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
        title="Create Disbursement"
        subtitle="Request a new loan disbursement"
        breadcrumbs={[
          { label: 'Disbursements', to: '/lending/disbursements' },
          { label: 'New' },
        ]}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Disbursement Details</CardTitle>
            <CardDescription>Enter disbursement information</CardDescription>
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
                    name="requested_amount"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Disbursement Amount *</FormLabel>
                        <FormControl>
                          <Input type="number" placeholder="Enter amount" {...field} />
                        </FormControl>
                        {selectedLoan && (
                          <FormDescription>
                            Max: {formatCurrency(selectedLoan.undisbursed)}
                          </FormDescription>
                        )}
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="disbursement_mode"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Disbursement Mode</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select mode" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {disbursementModes.map((mode) => (
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
                </div>

                <div className="border-t pt-4">
                  <h3 className="font-medium mb-4">Beneficiary Details</h3>

                  {selectedLoan?.bank_accounts && selectedLoan.bank_accounts.length > 0 && (
                    <div className="mb-4">
                      <FormLabel>Quick Select Bank Account</FormLabel>
                      <div className="flex gap-2 mt-2">
                        {selectedLoan.bank_accounts.map((acc, idx) => (
                          <Button
                            key={idx}
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => onBankAccountSelect(idx)}
                          >
                            {acc.name}
                          </Button>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="beneficiary_name"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Beneficiary Name *</FormLabel>
                          <FormControl>
                            <Input placeholder="Account holder name" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="beneficiary_bank"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Bank Name</FormLabel>
                          <FormControl>
                            <Input placeholder="Bank name" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4 mt-4">
                    <FormField
                      control={form.control}
                      name="beneficiary_account"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Account Number *</FormLabel>
                          <FormControl>
                            <Input placeholder="Account number" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="beneficiary_ifsc"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>IFSC Code *</FormLabel>
                          <FormControl>
                            <Input placeholder="IFSC code" maxLength={11} {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="scheduled_date"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Scheduled Date</FormLabel>
                        <FormControl>
                          <Input type="date" {...field} />
                        </FormControl>
                        <FormDescription>Optional - for future disbursement</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <FormField
                  control={form.control}
                  name="purpose"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Purpose</FormLabel>
                      <FormControl>
                        <Textarea placeholder="Disbursement purpose" {...field} />
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
                    <Banknote className="h-4 w-4 mr-2" />
                    {isLoading ? 'Creating...' : 'Create Request'}
                  </Button>
                </div>
              </form>
            </Form>
          </CardContent>
        </Card>

        {/* Loan Summary Panel */}
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

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Sanctioned</p>
                    <p className="font-medium">{formatCurrency(selectedLoan.sanctioned)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Disbursed</p>
                    <p className="font-medium">{formatCurrency(selectedLoan.disbursed)}</p>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <p className="text-sm text-muted-foreground">Available for Disbursement</p>
                  <p className="text-2xl font-bold text-green-600">
                    {formatCurrency(selectedLoan.undisbursed)}
                  </p>
                </div>

                <div className="border-t pt-4 space-y-2">
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() =>
                      form.setValue('requested_amount', selectedLoan.undisbursed.toString())
                    }
                  >
                    Disburse Full Amount
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() =>
                      form.setValue(
                        'requested_amount',
                        Math.round(selectedLoan.undisbursed / 2).toString()
                      )
                    }
                  >
                    Disburse 50%
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Banknote className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Select a loan account to view details</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
