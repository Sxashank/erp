import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowLeft, CheckCircle, XCircle, AlertTriangle, ArrowRight, Calendar, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';

import { logger } from '@/lib/logger';
const approvalSchema = z.object({
  decision: z.enum(['APPROVE', 'REJECT']),
  approvalAuthority: z.string().min(1, 'Approval authority is required'),
  remarks: z.string().optional(),
});

type ApprovalFormValues = z.infer<typeof approvalSchema>;

// Mock restructure data
const mockRestructure = {
  id: '1',
  restructureReference: 'RESTR/2025/00001',
  loanAccountNumber: 'SMFC/TL/CHN/2023/L00034',
  entityName: 'Southern Motors Corp',
  restructureType: 'COMPREHENSIVE',
  status: 'PENDING_APPROVAL',
  proposalDate: '2025-01-15',
  preOutstandingPrincipal: 130250000,
  preOutstandingInterest: 5250000,
  preInterestRate: 12.5,
  preTenureMonths: 60,
  preEmiAmount: 2950000,
  preMaturityDate: '2028-06-15',
  postOutstandingPrincipal: 130250000,
  postInterestRate: 11.0,
  postTenureMonths: 84,
  postEmiAmount: 2100000,
  postMaturityDate: '2032-01-15',
  moratoriumMonths: 6,
  moratoriumStartDate: '2025-02-01',
  moratoriumEndDate: '2025-07-31',
  moratoriumInterestTreatment: 'CAPITALIZE',
  interestWaived: 2500000,
  penalWaived: 750000,
  principalConvertedToFitl: 0,
  isStandardRestructure: true,
  downgradeRequired: false,
  preConditions: '1. Submission of all pending financials\n2. Personal guarantee from promoters\n3. Additional collateral coverage of 1.5x',
  postConditions: '1. Quarterly stock audit\n2. No dividend distribution for 2 years\n3. Monthly cash flow statements',
  justification: 'Borrower facing temporary cash flow issues due to delayed receivables from major customers. The company has secured new orders worth Rs. 50 Cr which will be executed over the next 18 months.',
  createdBy: 'Rajesh Kumar',
  createdAt: '2025-01-15T10:30:00Z',
};

const restructureTypeLabels: Record<string, string> = {
  TENURE_EXTENSION: 'Tenure Extension',
  EMI_REDUCTION: 'EMI Reduction',
  MORATORIUM: 'Moratorium',
  RATE_REDUCTION: 'Rate Reduction',
  PRINCIPAL_HAIRCUT: 'Principal Haircut',
  INTEREST_WAIVER: 'Interest Waiver',
  COMPREHENSIVE: 'Comprehensive',
  COVID_RESTRUCTURE: 'COVID Restructure',
};

export default function RestructureApproval() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const restructure = mockRestructure;

  const form = useForm<ApprovalFormValues>({
    resolver: zodResolver(approvalSchema),
    defaultValues: {
      decision: undefined,
      approvalAuthority: '',
      remarks: '',
    },
  });

  const watchedDecision = form.watch('decision');

  const onSubmit = async (data: ApprovalFormValues) => {
    setIsSubmitting(true);
    try {
      logger.debug('Approval data:', data);
      // API call would go here
      navigate(`/admin/lending/collections/restructure/${id}`);
    } catch (error) {
      console.error('Error processing approval:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const rateChange = restructure.postInterestRate - restructure.preInterestRate;
  const tenureChange = restructure.postTenureMonths - restructure.preTenureMonths;
  const totalWaiver = restructure.interestWaived + restructure.penalWaived;
  const emiReduction = restructure.preEmiAmount - restructure.postEmiAmount;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-semibold">Review Restructure Proposal</h1>
          <p className="text-muted-foreground">
            {restructure.restructureReference} - {restructure.entityName}
          </p>
        </div>
      </div>

      {/* Warning Alert */}
      <Alert variant="default" className="border-yellow-500 bg-yellow-50">
        <AlertTriangle className="h-4 w-4 text-yellow-600" />
        <AlertTitle className="text-yellow-800">Approval Required</AlertTitle>
        <AlertDescription className="text-yellow-700">
          This restructure proposal requires your review and approval. Please carefully review all terms before making a decision.
        </AlertDescription>
      </Alert>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs text-muted-foreground">Restructure Type</p>
            <Badge variant="secondary" className="mt-1">
              {restructureTypeLabels[restructure.restructureType]}
            </Badge>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs text-muted-foreground">Rate Change</p>
            <p className={`text-xl font-bold ${rateChange < 0 ? 'text-green-600' : 'text-red-600'}`}>
              {rateChange > 0 ? '+' : ''}{rateChange.toFixed(2)}%
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs text-muted-foreground">Tenure Extension</p>
            <p className="text-xl font-bold">{tenureChange > 0 ? '+' : ''}{tenureChange} mo</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs text-muted-foreground">EMI Reduction</p>
            <AmountDisplay amount={emiReduction} className="text-xl font-bold text-green-600" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs text-muted-foreground">Total Waiver</p>
            <AmountDisplay amount={totalWaiver} className="text-xl font-bold text-red-600" />
          </CardContent>
        </Card>
      </div>

      {/* Loan & Entity Info */}
      <Card>
        <CardHeader>
          <CardTitle>Loan Account Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-muted-foreground">Account Number</p>
              <p className="font-mono font-semibold">{restructure.loanAccountNumber}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Entity Name</p>
              <p className="font-semibold">{restructure.entityName}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Principal Outstanding</p>
              <AmountDisplay amount={restructure.preOutstandingPrincipal} className="font-semibold" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Interest Outstanding</p>
              <AmountDisplay amount={restructure.preOutstandingInterest} className="font-semibold" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Terms Comparison */}
      <Card>
        <CardHeader>
          <CardTitle>Terms Comparison</CardTitle>
          <CardDescription>Review the changes in loan terms</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 font-medium">Parameter</th>
                  <th className="text-right py-2 font-medium">Current</th>
                  <th className="text-center py-2 font-medium w-16"></th>
                  <th className="text-right py-2 font-medium">Proposed</th>
                  <th className="text-right py-2 font-medium">Change</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                <tr>
                  <td className="py-3">Interest Rate</td>
                  <td className="text-right">{restructure.preInterestRate}%</td>
                  <td className="text-center"><ArrowRight className="h-4 w-4 mx-auto text-muted-foreground" /></td>
                  <td className="text-right">{restructure.postInterestRate}%</td>
                  <td className={`text-right font-semibold ${rateChange < 0 ? 'text-green-600' : rateChange > 0 ? 'text-red-600' : ''}`}>
                    {rateChange > 0 ? '+' : ''}{rateChange.toFixed(2)}%
                  </td>
                </tr>
                <tr>
                  <td className="py-3">Tenure</td>
                  <td className="text-right">{restructure.preTenureMonths} months</td>
                  <td className="text-center"><ArrowRight className="h-4 w-4 mx-auto text-muted-foreground" /></td>
                  <td className="text-right">{restructure.postTenureMonths} months</td>
                  <td className="text-right font-semibold">
                    {tenureChange > 0 ? '+' : ''}{tenureChange} months
                  </td>
                </tr>
                <tr>
                  <td className="py-3">EMI Amount</td>
                  <td className="text-right"><AmountDisplay amount={restructure.preEmiAmount} /></td>
                  <td className="text-center"><ArrowRight className="h-4 w-4 mx-auto text-muted-foreground" /></td>
                  <td className="text-right"><AmountDisplay amount={restructure.postEmiAmount} /></td>
                  <td className="text-right font-semibold text-green-600">
                    -<AmountDisplay amount={emiReduction} />
                  </td>
                </tr>
                <tr>
                  <td className="py-3">Maturity Date</td>
                  <td className="text-right"><DateDisplay date={restructure.preMaturityDate} /></td>
                  <td className="text-center"><ArrowRight className="h-4 w-4 mx-auto text-muted-foreground" /></td>
                  <td className="text-right"><DateDisplay date={restructure.postMaturityDate} /></td>
                  <td className="text-right font-semibold">Extended</td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Moratorium & Waivers */}
      <div className="grid grid-cols-2 gap-6">
        {restructure.moratoriumMonths > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Moratorium
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Duration</span>
                <span className="font-semibold">{restructure.moratoriumMonths} months</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Period</span>
                <span className="font-semibold">
                  <DateDisplay date={restructure.moratoriumStartDate!} /> - <DateDisplay date={restructure.moratoriumEndDate!} />
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Interest Treatment</span>
                <Badge variant="outline">{restructure.moratoriumInterestTreatment}</Badge>
              </div>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Waivers & Relief</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Interest Waived</span>
              <AmountDisplay amount={restructure.interestWaived} className="font-semibold text-red-600" />
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Penal Interest Waived</span>
              <AmountDisplay amount={restructure.penalWaived} className="font-semibold text-red-600" />
            </div>
            <Separator />
            <div className="flex justify-between">
              <span className="font-medium">Total Waiver</span>
              <AmountDisplay amount={totalWaiver} className="font-bold text-red-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Classification & Compliance */}
      <Card>
        <CardHeader>
          <CardTitle>Classification & Compliance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-6">
            <div className="flex items-center gap-2">
              {restructure.isStandardRestructure ? (
                <CheckCircle className="h-5 w-5 text-green-600" />
              ) : (
                <XCircle className="h-5 w-5 text-red-600" />
              )}
              <span>Standard Restructure (RBI Compliant)</span>
            </div>
            <Separator orientation="vertical" className="h-6" />
            <div className="flex items-center gap-2">
              {restructure.downgradeRequired ? (
                <>
                  <AlertTriangle className="h-5 w-5 text-yellow-600" />
                  <span className="text-yellow-700">Downgrade Required</span>
                </>
              ) : (
                <>
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span>No Downgrade Required</span>
                </>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Conditions */}
      <div className="grid grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Pre-Conditions</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-sm whitespace-pre-wrap bg-muted p-3 rounded">
              {restructure.preConditions}
            </pre>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Post-Conditions</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-sm whitespace-pre-wrap bg-muted p-3 rounded">
              {restructure.postConditions}
            </pre>
          </CardContent>
        </Card>
      </div>

      {/* Justification */}
      <Card>
        <CardHeader>
          <CardTitle>Justification</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm">{restructure.justification}</p>
          <Separator className="my-4" />
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <User className="h-4 w-4" />
            <span>Proposed by {restructure.createdBy} on {new Date(restructure.createdAt).toLocaleDateString()}</span>
          </div>
        </CardContent>
      </Card>

      {/* Approval Form */}
      <Card className="border-2 border-primary">
        <CardHeader>
          <CardTitle>Your Decision</CardTitle>
          <CardDescription>
            Please review all details above and provide your decision
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="decision"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Decision *</FormLabel>
                    <div className="flex gap-4">
                      <Button
                        type="button"
                        variant={field.value === 'APPROVE' ? 'default' : 'outline'}
                        className={field.value === 'APPROVE' ? 'bg-green-600 hover:bg-green-700' : ''}
                        onClick={() => field.onChange('APPROVE')}
                      >
                        <CheckCircle className="mr-2 h-4 w-4" />
                        Approve
                      </Button>
                      <Button
                        type="button"
                        variant={field.value === 'REJECT' ? 'destructive' : 'outline'}
                        onClick={() => field.onChange('REJECT')}
                      >
                        <XCircle className="mr-2 h-4 w-4" />
                        Reject
                      </Button>
                    </div>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="approvalAuthority"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Approval Authority *</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select authority level" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="GM_CREDIT">GM Credit</SelectItem>
                        <SelectItem value="DGM_CREDIT">DGM Credit</SelectItem>
                        <SelectItem value="AGM_CREDIT">AGM Credit</SelectItem>
                        <SelectItem value="CREDIT_COMMITTEE">Credit Committee</SelectItem>
                        <SelectItem value="BOARD">Board</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="remarks"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Remarks {watchedDecision === 'REJECT' && '*'}
                    </FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder={
                          watchedDecision === 'REJECT'
                            ? 'Please provide reasons for rejection...'
                            : 'Any additional comments or conditions...'
                        }
                        className="min-h-[100px]"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="flex justify-end gap-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate(-1)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isSubmitting || !watchedDecision}
                  className={watchedDecision === 'APPROVE' ? 'bg-green-600 hover:bg-green-700' : ''}
                  variant={watchedDecision === 'REJECT' ? 'destructive' : 'default'}
                >
                  {isSubmitting ? 'Processing...' : `Confirm ${watchedDecision === 'APPROVE' ? 'Approval' : watchedDecision === 'REJECT' ? 'Rejection' : 'Decision'}`}
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}
