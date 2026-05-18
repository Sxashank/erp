import { zodResolver } from '@hookform/resolvers/zod';
import { Calculator, Calendar, Download, Eye } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';

import { PageHeader } from '@/components/common/PageHeader';
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { usePreviewSchedule } from '@/hooks/lending/usePreviewSchedule';
import { useToast } from '@/hooks/use-toast';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { SchedulePreviewLine, SchedulePreviewSummary } from '@/services/lending/scheduleApi';

const scheduleSchema = z.object({
  // Picker is forward-looking — preview endpoint is account-agnostic.
  loanAccountId: z.string().optional().default(''),
  principal: z.string().min(1, 'Principal amount is required'),
  interestRate: z.string().min(1, 'Interest rate is required'),
  tenureMonths: z.string().min(1, 'Tenure is required'),
  disbursementDate: z.string().min(1, 'Start date is required'),
  emiDay: z.string().default('1'),
  calculationMethod: z.string().default('reducing_balance'),
  moratoriumMonths: z.string().default('0'),
});

type ScheduleFormInput = z.input<typeof scheduleSchema>;
type ScheduleFormData = z.output<typeof scheduleSchema>;

// Loan accounts picker. Wires to GET /lending/loan-accounts via
// useLoanAccounts; render-empty until reused here.
interface LoanAccountOption {
  id: string;
  number: string;
  entity: string;
  sanctioned: number;
}

const loanAccounts: LoanAccountOption[] = [];

export default function ScheduleGenerate() {
  // navigate kept available via router context; back navigation handled by
  // the surrounding shell. Picker list is still empty (see note above).
  useNavigate();
  const { toast } = useToast();
  const previewMutation = usePreviewSchedule();

  const form = useForm<ScheduleFormInput, unknown, ScheduleFormData>({
    resolver: zodResolver(scheduleSchema),
    defaultValues: {
      loanAccountId: '',
      emiDay: '1',
      calculationMethod: 'reducing_balance',
      moratoriumMonths: '0',
    },
  });

  const schedule: SchedulePreviewLine[] | null = previewMutation.data?.entries ?? null;
  const summary: SchedulePreviewSummary | null = previewMutation.data?.summary ?? null;
  const isLoading = previewMutation.isPending;

  const generateSchedule = (data: ScheduleFormData) => {
    previewMutation.mutate(
      {
        // Decimal as string on the wire — backend parses to Decimal (§6.2).
        principal: data.principal,
        interestRate: data.interestRate,
        tenureMonths: parseInt(data.tenureMonths, 10),
        disbursementDate: data.disbursementDate,
        emiDay: parseInt(data.emiDay, 10),
        calculationMethod: data.calculationMethod,
        moratoriumMonths: parseInt(data.moratoriumMonths, 10),
      },
      {
        onSuccess: (result) => {
          toast({
            title: 'Schedule generated',
            description: `${result.summary.totalInstallments} installments computed.`,
          });
        },
        onError: (err) => {
          toast({
            title: 'Could not generate schedule',
            description: err.message,
            variant: 'destructive',
          });
        },
      },
    );
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Generate Repayment Schedule"
        subtitle="Create loan repayment schedule with different calculation methods"
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Form */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Schedule Parameters</CardTitle>
            <CardDescription>Enter loan details to generate schedule</CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(generateSchedule)} className="space-y-4">
                <FormField
                  control={form.control}
                  name="loanAccountId"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Loan Account</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
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

                <FormField
                  control={form.control}
                  name="principal"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Principal Amount</FormLabel>
                      <FormControl>
                        <Input type="number" placeholder="10000000" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="interestRate"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Annual Interest Rate (%)</FormLabel>
                      <FormControl>
                        <Input type="number" step="0.01" placeholder="12.5" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="tenureMonths"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Tenure (Months)</FormLabel>
                      <FormControl>
                        <Input type="number" placeholder="36" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="disbursementDate"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Start Date</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="emiDay"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>EMI Day</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select day" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {Array.from({ length: 28 }, (_, i) => i + 1).map((day) => (
                            <SelectItem key={day} value={day.toString()}>
                              {day}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="calculationMethod"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Calculation Method</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select method" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="reducing_balance">Reducing Balance</SelectItem>
                          <SelectItem value="flat">Flat Rate</SelectItem>
                          <SelectItem value="emi">EMI (Equated)</SelectItem>
                          <SelectItem value="rule_of_78">Rule of 78</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="moratoriumMonths"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Moratorium (Months)</FormLabel>
                      <FormControl>
                        <Input type="number" placeholder="0" {...field} />
                      </FormControl>
                      <FormDescription>Interest-only period</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <Button type="submit" className="w-full" disabled={isLoading}>
                  <Calculator className="mr-2 h-4 w-4" />
                  {isLoading ? 'Generating...' : 'Generate Schedule'}
                </Button>
              </form>
            </Form>
          </CardContent>
        </Card>

        {/* Schedule Display */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Repayment Schedule</CardTitle>
              <CardDescription>
                {schedule ? `${schedule.length} installments` : 'Schedule will appear here'}
              </CardDescription>
            </div>
            {schedule && (
              <div className="flex gap-2">
                <Button variant="outline" size="sm">
                  <Eye className="mr-2 h-4 w-4" />
                  Preview
                </Button>
                <Button variant="outline" size="sm">
                  <Download className="mr-2 h-4 w-4" />
                  Export
                </Button>
              </div>
            )}
          </CardHeader>
          <CardContent>
            {summary && (
              <div className="mb-6 grid grid-cols-4 gap-4 rounded-lg bg-muted p-4">
                <div>
                  <p className="text-sm text-muted-foreground">Total Principal</p>
                  <p className="text-lg font-semibold">{formatCurrency(summary.totalPrincipal)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Interest</p>
                  <p className="text-lg font-semibold">{formatCurrency(summary.totalInterest)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Payment</p>
                  <p className="text-lg font-semibold">{formatCurrency(summary.totalAmount)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Monthly EMI</p>
                  <p className="text-lg font-semibold">{formatCurrency(summary.emiAmount)}</p>
                </div>
              </div>
            )}

            {schedule ? (
              <div className="max-h-[500px] overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-12">#</TableHead>
                      <TableHead>Due Date</TableHead>
                      <TableHead className="text-right">Opening</TableHead>
                      <TableHead className="text-right">Principal</TableHead>
                      <TableHead className="text-right">Interest</TableHead>
                      <TableHead className="text-right">EMI</TableHead>
                      <TableHead className="text-right">Closing</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {schedule.map((entry) => (
                      <TableRow
                        key={entry.installmentNumber}
                        className={entry.isMoratorium ? 'bg-muted/50' : ''}
                      >
                        <TableCell className="font-medium">
                          {entry.installmentNumber}
                          {entry.isMoratorium && (
                            <span className="ml-1 text-xs text-muted-foreground">(M)</span>
                          )}
                        </TableCell>
                        <TableCell>{formatDate(entry.dueDate)}</TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(entry.openingBalance)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(entry.principalAmount)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(entry.interestAmount)}
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {formatCurrency(entry.totalAmount)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(entry.closingBalance)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Calendar className="mb-4 h-12 w-12 text-muted-foreground" />
                <h3 className="text-lg font-medium">No Schedule Generated</h3>
                <p className="text-muted-foreground">
                  Enter loan parameters and click Generate to create a schedule
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
