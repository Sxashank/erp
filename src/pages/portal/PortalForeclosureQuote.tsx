/**
 * PortalForeclosureQuote — borrower requests a foreclosure quote.
 *
 * Calls /lending/loan-accounts/{id}/foreclosure-quote and renders the
 * principal + accrued interest + foreclosure fee breakup.
 */

import { useMutation } from '@tanstack/react-query';
import { Calculator, FileText, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { useParams } from 'react-router-dom';

import { AmountDisplay, PageHeader } from '@/components/common';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import api from '@/services/api';

interface ForeclosureQuote {
  loanAccountId: string;
  asOfDate: string;
  principalOutstanding: number;
  interestAccrued: number;
  foreclosureFee: number;
  otherCharges: number;
  totalPayable: number;
  validTill: string;
}

async function fetchQuote(loanId: string, asOfDate: string): Promise<ForeclosureQuote> {
  const { data } = await api.post<ForeclosureQuote>(
    `/lending/loan-accounts/${loanId}/foreclosure-quote`,
    { asOfDate },
  );
  return data;
}

export default function PortalForeclosureQuote(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  const { toast } = useToast();
  const [asOfDate, setAsOfDate] = useState(new Date().toISOString().slice(0, 10));
  const [quote, setQuote] = useState<ForeclosureQuote | null>(null);

  const mutation = useMutation({
    mutationFn: () => fetchQuote(id as string, asOfDate),
    onSuccess: (data) => setQuote(data),
    onError: (err) =>
      toast({
        title: 'Could not fetch quote',
        description: err instanceof Error ? err.message : 'Unknown error',
        variant: 'destructive',
      }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Foreclosure quote"
        subtitle="Calculate the amount needed to close this loan in full"
        breadcrumbs={[{ label: 'My loans', to: '/portal/loans' }, { label: 'Foreclosure quote' }]}
      />

      <Card>
        <CardHeader>
          <CardTitle>Request a quote</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="asOfDate">As of date</Label>
            <Input
              id="asOfDate"
              type="date"
              value={asOfDate}
              onChange={(e) => setAsOfDate(e.target.value)}
              className="max-w-xs"
            />
          </div>
          <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
            {mutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Calculator className="mr-2 h-4 w-4" />
            )}
            Calculate
          </Button>
        </CardContent>
      </Card>

      {quote ? (
        <Card>
          <CardHeader>
            <CardTitle>Foreclosure breakup as on {quote.asOfDate}</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-x-6 gap-y-3 md:grid-cols-2">
              <div>
                <dt className="text-sm text-muted-foreground">Principal outstanding</dt>
                <dd className="font-semibold">
                  <AmountDisplay amount={quote.principalOutstanding} />
                </dd>
              </div>
              <div>
                <dt className="text-sm text-muted-foreground">Interest accrued</dt>
                <dd className="font-semibold">
                  <AmountDisplay amount={quote.interestAccrued} />
                </dd>
              </div>
              <div>
                <dt className="text-sm text-muted-foreground">Foreclosure fee</dt>
                <dd className="font-semibold">
                  <AmountDisplay amount={quote.foreclosureFee} />
                </dd>
              </div>
              <div>
                <dt className="text-sm text-muted-foreground">Other charges</dt>
                <dd className="font-semibold">
                  <AmountDisplay amount={quote.otherCharges} />
                </dd>
              </div>
              <div className="mt-4 border-t pt-4 md:col-span-2">
                <dt className="text-sm text-muted-foreground">TOTAL PAYABLE</dt>
                <dd className="text-2xl font-bold text-emerald-700">
                  <AmountDisplay amount={quote.totalPayable} />
                </dd>
              </div>
              <div className="text-sm text-muted-foreground md:col-span-2">
                Quote valid until <b>{quote.validTill}</b>.
              </div>
            </dl>
            <p className="mt-4 text-xs text-muted-foreground">
              Once you remit the total payable amount to our account, all charges on your security
              will be released. Original documents will be returned to you within 30 days per RBI
              directive.
            </p>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
