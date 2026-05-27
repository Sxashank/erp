import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, ArrowRight, CheckCircle, Loader2, XCircle } from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';
import { z } from 'zod';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import { useAuth } from '@/hooks/useAuth';
import { masterRowsToOptions, useLendingOptionRows } from '@/hooks/lending/useLendingMasters';
import { collectionApi } from '@/services/lending/collectionApi';

const approvalSchema = z.object({
  decision: z.enum(['APPROVE', 'REJECT']),
  approvalAuthority: z.string().min(1, 'Approval authority is required'),
  remarks: z.string().optional(),
});

type ApprovalFormValues = z.infer<typeof approvalSchema>;

interface RestructureApprovalData {
  id: string;
  restructureReference: string;
  restructureType: string;
  status: string;
  proposalDate: string;
  loanAccountId: string;
  preOutstandingPrincipal: string | number;
  preOutstandingInterest: string | number;
  preInterestRate: string | number;
  preTenureMonths: number;
  preEmiAmount?: string | number | null;
  preMaturityDate: string;
  postOutstandingPrincipal: string | number;
  postInterestRate: string | number;
  postTenureMonths: number;
  postEmiAmount?: string | number | null;
  postMaturityDate: string;
  moratoriumMonths: number;
  moratoriumStartDate?: string | null;
  moratoriumEndDate?: string | null;
  moratoriumInterestTreatment?: string | null;
  interestWaived: string | number;
  penalWaived: string | number;
  principalConvertedToFitl: string | number;
  isStandardRestructure: boolean;
  downgradeRequired: boolean;
  preConditions?: string | null;
  postConditions?: string | null;
  justification: string;
  remarks?: string | null;
  createdAt: string;
}

export default function RestructureApproval() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const authorityRows = useLendingOptionRows('APPROVAL_AUTHORITY');
  const restructureTypeRows = useLendingOptionRows('RESTRUCTURE_TYPE');
  const moratoriumRows = useLendingOptionRows('MORATORIUM_INTEREST_TREATMENT');
  const authorityOptions = masterRowsToOptions(authorityRows.data?.items);
  const restructureTypeOptions = masterRowsToOptions(restructureTypeRows.data?.items);
  const moratoriumOptions = masterRowsToOptions(moratoriumRows.data?.items);

  const query = useQuery<RestructureApprovalData>({
    queryKey: ['lending', 'collections', 'restructure', id] as const,
    queryFn: () => collectionApi.getRestructure(id as string),
    enabled: Boolean(id),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });

  const form = useForm<ApprovalFormValues>({
    resolver: zodResolver(approvalSchema),
    defaultValues: {
      decision: undefined,
      approvalAuthority: '',
      remarks: '',
    },
  });

  const watchedDecision = form.watch('decision');
  const restructure = query.data;

  const labelFor = (options: { value: string; label: string }[], value?: string | null) =>
    options.find((option) => option.value === value)?.label ?? value ?? '—';

  const onSubmit = async (data: ApprovalFormValues) => {
    if (!id || !user) return;
    if (data.decision === 'REJECT' && !data.remarks?.trim()) {
      form.setError('remarks', { message: 'Rejection reason is required' });
      return;
    }

    setIsSubmitting(true);
    try {
      const displayName = user.fullName || user.username || user.email;
      if (data.decision === 'APPROVE') {
        await collectionApi.approveRestructure(id, {
          approvedById: user.id,
          approvedByName: displayName,
          approvalAuthority: data.approvalAuthority,
        });
      } else {
        await collectionApi.rejectRestructure(id, {
          rejectedById: user.id,
          rejectedByName: displayName,
          rejectionReason: data.remarks ?? '',
          approvalAuthority: data.approvalAuthority,
        });
      }
      navigate(`/admin/lending/collections/restructure/${id}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (query.isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-16 text-muted-foreground">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Loading restructure proposal...
        </CardContent>
      </Card>
    );
  }

  if (query.isError || !restructure) {
    return (
      <ErrorState
        title="Could not load restructure proposal"
        error={query.error}
        onRetry={() => query.refetch()}
      />
    );
  }

  const preRate = Number(restructure.preInterestRate);
  const postRate = Number(restructure.postInterestRate);
  const rateChange = postRate - preRate;
  const tenureChange = restructure.postTenureMonths - restructure.preTenureMonths;
  const preEmi = Number(restructure.preEmiAmount ?? 0);
  const postEmi = Number(restructure.postEmiAmount ?? 0);
  const emiReduction = preEmi - postEmi;
  const totalWaiver = Number(restructure.interestWaived) + Number(restructure.penalWaived);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Review Restructure Proposal"
        subtitle={`${restructure.restructureReference} - ${restructure.status}`}
        breadcrumbs={[
          { label: 'Restructures', to: '/admin/lending/collections/restructure' },
          {
            label: restructure.restructureReference,
            to: `/admin/lending/collections/restructure/${restructure.id}`,
          },
          { label: 'Approve' },
        ]}
      />

      <Alert variant="default" className="border-yellow-500 bg-yellow-50">
        <AlertTriangle className="h-4 w-4 text-yellow-600" />
        <AlertTitle className="text-yellow-800">Approval Required</AlertTitle>
        <AlertDescription className="text-yellow-700">
          Review the proposed change in economics, relief, classification impact, and conditions
          before approving or rejecting.
        </AlertDescription>
      </Alert>

      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs text-muted-foreground">Restructure Type</p>
            <Badge variant="secondary" className="mt-1">
              {labelFor(restructureTypeOptions, restructure.restructureType)}
            </Badge>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs text-muted-foreground">Rate Change</p>
            <p
              className={`text-xl font-bold ${rateChange < 0 ? 'text-green-600' : 'text-red-600'}`}
            >
              {rateChange > 0 ? '+' : ''}
              {rateChange.toFixed(2)}%
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs text-muted-foreground">Tenure Change</p>
            <p className="text-xl font-bold">
              {tenureChange > 0 ? '+' : ''}
              {tenureChange} mo
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs text-muted-foreground">Instalment Change</p>
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

      <Card>
        <CardHeader>
          <CardTitle>Loan Account Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <p className="text-xs text-muted-foreground">Loan Account ID</p>
              <p className="font-mono font-semibold">{restructure.loanAccountId}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Proposal Date</p>
              <DateDisplay date={restructure.proposalDate} />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Principal Outstanding</p>
              <AmountDisplay
                amount={restructure.preOutstandingPrincipal}
                className="font-semibold"
              />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Interest Outstanding</p>
              <AmountDisplay
                amount={restructure.preOutstandingInterest}
                className="font-semibold"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Terms Comparison</CardTitle>
          <CardDescription>Current terms versus proposed restructure terms</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="py-2 text-left font-medium">Parameter</th>
                  <th className="py-2 text-right font-medium">Current</th>
                  <th className="w-16 py-2 text-center font-medium"></th>
                  <th className="py-2 text-right font-medium">Proposed</th>
                  <th className="py-2 text-right font-medium">Change</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                <tr>
                  <td className="py-3">Interest Rate</td>
                  <td className="text-right">{preRate}%</td>
                  <td className="text-center">
                    <ArrowRight className="mx-auto h-4 w-4 text-muted-foreground" />
                  </td>
                  <td className="text-right">{postRate}%</td>
                  <td className="text-right font-semibold">
                    {rateChange > 0 ? '+' : ''}
                    {rateChange.toFixed(2)}%
                  </td>
                </tr>
                <tr>
                  <td className="py-3">Tenure</td>
                  <td className="text-right">{restructure.preTenureMonths} months</td>
                  <td className="text-center">
                    <ArrowRight className="mx-auto h-4 w-4 text-muted-foreground" />
                  </td>
                  <td className="text-right">{restructure.postTenureMonths} months</td>
                  <td className="text-right font-semibold">
                    {tenureChange > 0 ? '+' : ''}
                    {tenureChange} months
                  </td>
                </tr>
                <tr>
                  <td className="py-3">Instalment Amount</td>
                  <td className="text-right">
                    <AmountDisplay amount={preEmi} />
                  </td>
                  <td className="text-center">
                    <ArrowRight className="mx-auto h-4 w-4 text-muted-foreground" />
                  </td>
                  <td className="text-right">
                    <AmountDisplay amount={postEmi} />
                  </td>
                  <td className="text-right font-semibold">
                    <AmountDisplay amount={emiReduction} />
                  </td>
                </tr>
                <tr>
                  <td className="py-3">Maturity Date</td>
                  <td className="text-right">
                    <DateDisplay date={restructure.preMaturityDate} />
                  </td>
                  <td className="text-center">
                    <ArrowRight className="mx-auto h-4 w-4 text-muted-foreground" />
                  </td>
                  <td className="text-right">
                    <DateDisplay date={restructure.postMaturityDate} />
                  </td>
                  <td className="text-right font-semibold">Revised</td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Moratorium</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Duration</span>
              <span className="font-semibold">{restructure.moratoriumMonths} months</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Interest Treatment</span>
              <Badge variant="outline">
                {labelFor(moratoriumOptions, restructure.moratoriumInterestTreatment)}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Waivers & Relief</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Interest Waived</span>
              <AmountDisplay amount={restructure.interestWaived} className="font-semibold" />
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Penal Interest Waived</span>
              <AmountDisplay amount={restructure.penalWaived} className="font-semibold" />
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">FITL Conversion</span>
              <AmountDisplay
                amount={restructure.principalConvertedToFitl}
                className="font-semibold"
              />
            </div>
            <Separator />
            <div className="flex justify-between">
              <span className="font-medium">Total Waiver</span>
              <AmountDisplay amount={totalWaiver} className="font-bold text-red-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Classification & Conditions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-4">
            <Badge variant={restructure.isStandardRestructure ? 'default' : 'destructive'}>
              {restructure.isStandardRestructure ? 'Standard Restructure' : 'Non-standard'}
            </Badge>
            <Badge variant={restructure.downgradeRequired ? 'destructive' : 'outline'}>
              {restructure.downgradeRequired ? 'Downgrade Required' : 'No Downgrade'}
            </Badge>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="mb-2 text-sm font-medium">Pre-Conditions</p>
              <pre className="min-h-[80px] whitespace-pre-wrap rounded bg-muted p-3 text-sm">
                {restructure.preConditions || '—'}
              </pre>
            </div>
            <div>
              <p className="mb-2 text-sm font-medium">Post-Conditions</p>
              <pre className="min-h-[80px] whitespace-pre-wrap rounded bg-muted p-3 text-sm">
                {restructure.postConditions || '—'}
              </pre>
            </div>
          </div>
          <div>
            <p className="mb-2 text-sm font-medium">Justification</p>
            <p className="rounded bg-muted p-3 text-sm">{restructure.justification}</p>
          </div>
        </CardContent>
      </Card>

      <Card className="border-2 border-primary">
        <CardHeader>
          <CardTitle>Your Decision</CardTitle>
          <CardDescription>Approve or reject this restructure proposal</CardDescription>
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
                        className={
                          field.value === 'APPROVE' ? 'bg-green-600 hover:bg-green-700' : ''
                        }
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
                        {authorityOptions.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
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
                name="remarks"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Remarks {watchedDecision === 'REJECT' && '*'}</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder={
                          watchedDecision === 'REJECT'
                            ? 'Provide reasons for rejection...'
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
                <Button type="button" variant="outline" onClick={() => navigate(-1)}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isSubmitting || !watchedDecision || !user}
                  className={watchedDecision === 'APPROVE' ? 'bg-green-600 hover:bg-green-700' : ''}
                  variant={watchedDecision === 'REJECT' ? 'destructive' : 'default'}
                >
                  {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Confirm{' '}
                  {watchedDecision === 'APPROVE'
                    ? 'Approval'
                    : watchedDecision === 'REJECT'
                      ? 'Rejection'
                      : 'Decision'}
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}
