import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Calculator, Calendar, Download, ArrowLeft, Eye } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/common/PageHeader';
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
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { formatCurrency, formatDate } from '@/lib/utils';

const scheduleSchema = z.object({
  loan_account_id: z.string().min(1, 'Loan account is required'),
  principal: z.string().min(1, 'Principal amount is required'),
  interest_rate: z.string().min(1, 'Interest rate is required'),
  tenure_months: z.string().min(1, 'Tenure is required'),
  disbursement_date: z.string().min(1, 'Start date is required'),
  emi_day: z.string().default('1'),
  calculation_method: z.string().default('reducing_balance'),
  moratorium_months: z.string().default('0'),
});

type ScheduleFormData = z.infer<typeof scheduleSchema>;

// Mock loan accounts
const loanAccounts = [
  { id: '1', number: 'SMFC/LA/2025/00145', entity: 'Sunrise Industries', sanctioned: 15000000 },
  { id: '2', number: 'SMFC/LA/2025/00146', entity: 'Metro Logistics', sanctioned: 25000000 },
  { id: '3', number: 'SMFC/LA/2025/00147', entity: 'Eastern Trading', sanctioned: 10000000 },
];

export default function ScheduleGenerate() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [schedule, setSchedule] = useState<any[] | null>(null);
  const [summary, setSummary] = useState<any | null>(null);

  const form = useForm<ScheduleFormData>({
    resolver: zodResolver(scheduleSchema) as any,
    defaultValues: {
      emi_day: '1',
      calculation_method: 'reducing_balance',
      moratorium_months: '0',
    },
  });

  const generateSchedule = async (data: ScheduleFormData) => {
    setIsLoading(true);

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));

    const principal = parseFloat(data.principal);
    const rate = parseFloat(data.interest_rate);
    const tenure = parseInt(data.tenure_months);
    const moratorium = parseInt(data.moratorium_months);
    const startDate = new Date(data.disbursement_date);
    const emiDay = parseInt(data.emi_day);

    // Calculate EMI for reducing balance
    const monthlyRate = rate / 12 / 100;
    const effectiveTenure = tenure - moratorium;
    const emi = effectiveTenure > 0
      ? (principal * monthlyRate * Math.pow(1 + monthlyRate, effectiveTenure)) /
        (Math.pow(1 + monthlyRate, effectiveTenure) - 1)
      : principal / Math.max(tenure, 1);

    // Generate schedule
    const entries = [];
    let balance = principal;
    let totalInterest = 0;
    let totalPrincipal = 0;

    for (let i = 0; i < tenure; i++) {
      const dueDate = new Date(startDate);
      dueDate.setMonth(dueDate.getMonth() + i + 1);
      dueDate.setDate(Math.min(emiDay, 28));

      const isMoratorium = i < moratorium;
      const interest = balance * monthlyRate;
      let principalPaid = 0;

      if (isMoratorium) {
        principalPaid = 0;
      } else if (i === tenure - 1) {
        principalPaid = balance;
      } else {
        principalPaid = emi - interest;
      }

      const opening = balance;
      balance = Math.max(0, balance - principalPaid);

      entries.push({
        installment_number: i + 1,
        due_date: dueDate.toISOString().split('T')[0],
        principal_amount: principalPaid,
        interest_amount: interest,
        total_amount: principalPaid + interest,
        opening_balance: opening,
        closing_balance: balance,
        is_moratorium: isMoratorium,
      });

      totalInterest += interest;
      totalPrincipal += principalPaid;
    }

    setSchedule(entries);
    setSummary({
      total_installments: tenure,
      total_principal: totalPrincipal,
      total_interest: totalInterest,
      total_amount: totalPrincipal + totalInterest,
      emi: emi,
    });

    setIsLoading(false);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Generate Repayment Schedule"
        subtitle="Create loan repayment schedule with different calculation methods"
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Schedule Parameters</CardTitle>
            <CardDescription>Enter loan details to generate schedule</CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(generateSchedule as any)} className="space-y-4">
                <FormField
                  control={form.control}
                  name="loan_account_id"
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
                  name="interest_rate"
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
                  name="tenure_months"
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
                  name="disbursement_date"
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
                  name="emi_day"
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
                  name="calculation_method"
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
                  name="moratorium_months"
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
                  <Calculator className="h-4 w-4 mr-2" />
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
                  <Eye className="h-4 w-4 mr-2" />
                  Preview
                </Button>
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </Button>
              </div>
            )}
          </CardHeader>
          <CardContent>
            {summary && (
              <div className="grid grid-cols-4 gap-4 mb-6 p-4 bg-muted rounded-lg">
                <div>
                  <p className="text-sm text-muted-foreground">Total Principal</p>
                  <p className="text-lg font-semibold">{formatCurrency(summary.total_principal)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Interest</p>
                  <p className="text-lg font-semibold">{formatCurrency(summary.total_interest)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Payment</p>
                  <p className="text-lg font-semibold">{formatCurrency(summary.total_amount)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Monthly EMI</p>
                  <p className="text-lg font-semibold">{formatCurrency(summary.emi)}</p>
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
                        key={entry.installment_number}
                        className={entry.is_moratorium ? 'bg-muted/50' : ''}
                      >
                        <TableCell className="font-medium">
                          {entry.installment_number}
                          {entry.is_moratorium && (
                            <span className="text-xs text-muted-foreground ml-1">(M)</span>
                          )}
                        </TableCell>
                        <TableCell>{formatDate(entry.due_date)}</TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(entry.opening_balance)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(entry.principal_amount)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(entry.interest_amount)}
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {formatCurrency(entry.total_amount)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(entry.closing_balance)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Calendar className="h-12 w-12 text-muted-foreground mb-4" />
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
