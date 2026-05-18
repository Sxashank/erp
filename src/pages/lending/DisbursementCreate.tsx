import { zodResolver } from '@hookform/resolvers/zod';
import { Banknote, Check, AlertCircle } from 'lucide-react';
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
import { useCreateDisbursement } from '@/hooks/lending/useDisbursements';
import { useLoanAccounts } from '@/hooks/lending/useLoanAccounts';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import { formatCurrency } from '@/lib/utils';
import type { DisbursementCreateResponse } from '@/services/lending/disbursementApi';

const disbursementSchema = z.object({
  loanAccountId: z.string().min(1, 'Loan account is required'),
  requestedAmount: z.string().min(1, 'Amount is required'),
  beneficiaryName: z.string().min(1, 'Beneficiary name is required'),
  beneficiaryAccountNumber: z.string().min(1, 'Account number is required'),
  beneficiaryIfsc: z.string().min(11, 'Valid IFSC is required').max(11),
  beneficiaryBank: z.string().optional(),
  disbursementMode: z.string().default('RTGS'),
  scheduledDate: z.string().optional(),
  purpose: z.string().optional(),
});

type DisbursementFormInput = z.input<typeof disbursementSchema>;
type DisbursementFormData = z.output<typeof disbursementSchema>;

type DisbursementLoanOption = {
  id: string;
  number: string;
  entity: string;
  sanctioned: number;
  disbursed: number;
  undisbursed: number;
};

const disbursementModes = [
  { value: 'RTGS', label: 'RTGS' },
  { value: 'NEFT', label: 'NEFT' },
  { value: 'IMPS', label: 'IMPS' },
  { value: 'CHEQUE', label: 'Cheque' },
  { value: 'DD', label: 'Demand Draft' },
];

export default function DisbursementCreate() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const createMutation = useCreateDisbursement();
  const { data: loanAccountData, isLoading: isLoadingLoanAccounts } = useLoanAccounts({
    status: 'ACTIVE',
    pageSize: 100,
  });
  const loanAccounts: DisbursementLoanOption[] =
    loanAccountData?.items.map((loan) => {
      const sanctioned = Number(loan.sanctionedAmount);
      const disbursed = Number(loan.totalDisbursedAmount);
      return {
        id: loan.id,
        number: loan.loanAccountNumber,
        entity: loan.entityName ?? 'Borrower entity',
        sanctioned,
        disbursed,
        undisbursed: Math.max(sanctioned - disbursed, 0),
      };
    }) ?? [];
  const [selectedLoan, setSelectedLoan] = useState<DisbursementLoanOption | null>(null);
  const [createdDisbursement, setCreatedDisbursement] = useState<DisbursementCreateResponse | null>(
    null,
  );
  const showSuccess = createdDisbursement !== null;

  const form = useForm<DisbursementFormInput, unknown, DisbursementFormData>({
    resolver: zodResolver(disbursementSchema),
    defaultValues: {
      disbursementMode: 'RTGS',
    },
  });

  const onLoanSelect = (loanId: string) => {
    const loan = loanAccounts.find((l) => l.id === loanId);
    setSelectedLoan(loan || null);
    form.setValue('loanAccountId', loanId);
    if (loan) {
      form.setValue('beneficiaryName', loan.entity);
    }
  };

  const onSubmit = async (data: DisbursementFormData) => {
    try {
      const created = await createMutation.mutateAsync({
        loanAccountId: data.loanAccountId,
        // Decimal on the wire — send as a string (CLAUDE.md §6.2).
        requestedAmount: data.requestedAmount,
        beneficiaryName: data.beneficiaryName,
        beneficiaryAccountNumber: data.beneficiaryAccountNumber,
        beneficiaryIfsc: data.beneficiaryIfsc,
        disbursementMode: data.disbursementMode,
        ...(data.scheduledDate ? { scheduledDate: data.scheduledDate } : {}),
        ...(data.purpose ? { purpose: data.purpose } : {}),
        ...(data.beneficiaryBank ? { beneficiaryBank: data.beneficiaryBank } : {}),
      });
      toast({
        title: 'Disbursement request created',
        description: `${created.disbursementReference} submitted successfully.`,
      });
      setCreatedDisbursement(created);
    } catch (err) {
      showErrorToast(err, toast);
    }
  };

  if (showSuccess && createdDisbursement) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
            <Check className="h-8 w-8 text-green-600" />
          </div>
          <h2 className="mb-2 text-2xl font-bold">Disbursement Request Created</h2>
          <p className="mb-2 text-muted-foreground">
            Reference:{' '}
            <span className="font-mono">{createdDisbursement.disbursementReference}</span>
          </p>
          <p className="mb-6 text-muted-foreground">
            The request has been submitted and is now {createdDisbursement.status.toLowerCase()}.
          </p>
          <Alert className="mx-auto mb-6 max-w-md">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Pending Approval</AlertTitle>
            <AlertDescription>
              This disbursement request is pending verification and approval.
            </AlertDescription>
          </Alert>
          <div className="flex justify-center gap-4">
            <Button variant="outline" onClick={() => navigate('/admin/lending/disbursements')}>
              View All Disbursements
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setCreatedDisbursement(null);
                form.reset({ disbursementMode: 'RTGS' });
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
        title="Create Disbursement"
        subtitle="Request a new loan disbursement"
        breadcrumbs={[
          { label: 'Disbursements', to: '/admin/lending/disbursements' },
          { label: 'New' },
        ]}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Form */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Disbursement Details</CardTitle>
            <CardDescription>Enter disbursement information</CardDescription>
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
                    name="requestedAmount"
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
                    name="disbursementMode"
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
                  <h3 className="mb-4 font-medium">Beneficiary Details</h3>

                  <div className="grid grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="beneficiaryName"
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
                      name="beneficiaryBank"
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

                  <div className="mt-4 grid grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="beneficiaryAccountNumber"
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
                      name="beneficiaryIfsc"
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
                    name="scheduledDate"
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

                <div className="flex justify-end gap-4">
                  <Button type="button" variant="outline" onClick={() => navigate(-1)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={createMutation.isPending}>
                    <Banknote className="mr-2 h-4 w-4" />
                    {createMutation.isPending ? 'Creating...' : 'Create Request'}
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

                <div className="space-y-2 border-t pt-4">
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() =>
                      form.setValue('requestedAmount', selectedLoan.undisbursed.toString())
                    }
                  >
                    Disburse Full Amount
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() =>
                      form.setValue(
                        'requestedAmount',
                        Math.round(selectedLoan.undisbursed / 2).toString(),
                      )
                    }
                  >
                    Disburse 50%
                  </Button>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-muted-foreground">
                <Banknote className="mx-auto mb-4 h-12 w-12 opacity-50" />
                <p>Select a loan account to view details</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
