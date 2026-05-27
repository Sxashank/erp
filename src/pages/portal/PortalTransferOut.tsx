/**
 * PortalTransferOut — borrower initiates a balance-transfer to another lender.
 *
 * Creates a transfer-out record (status: NOC_REQUESTED) which the lender
 * then progresses through OUTSTANDING_ISSUED → PAYMENT_RECEIVED → CLOSED.
 */

import { useMutation } from '@tanstack/react-query';
import { ArrowRight, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { PageHeader } from '@/components/common';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import api from '@/services/api';

export default function PortalTransferOut(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [targetLender, setTargetLender] = useState('');
  const [reason, setReason] = useState('');

  const mutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/lending/loan-accounts/${id}/transfer-out`, {
        targetLenderName: targetLender,
      });
      return data;
    },
    onSuccess: () => {
      toast({
        title: 'Transfer-out request initiated',
        description:
          'Your NoC request has been recorded. We will issue the outstanding letter shortly.',
      });
      navigate(`/portal/loans/${id}/timeline`);
    },
    onError: (err) =>
      toast({
        title: 'Could not initiate transfer',
        description: err instanceof Error ? err.message : 'Unknown error',
        variant: 'destructive',
      }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Transfer this loan to another lender"
        subtitle="Request a No-Objection Certificate so you can move this loan."
        breadcrumbs={[{ label: 'My loans', to: '/portal/loans' }, { label: 'Transfer out' }]}
      />

      <Card>
        <CardHeader>
          <CardTitle>Balance transfer request</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Once we receive your request, we will issue an outstanding letter listing the amount
            required to close this loan. Your new lender pays that amount to our account. Once
            received, the security is discharged and original documents are released to you within
            30 days.
          </p>
          <div>
            <Label htmlFor="targetLender">Target lender</Label>
            <Input
              id="targetLender"
              value={targetLender}
              onChange={(e) => setTargetLender(e.target.value)}
              placeholder="Name of the bank / NBFC taking over"
            />
          </div>
          <div>
            <Label htmlFor="reason">Reason (optional)</Label>
            <Textarea
              id="reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Help us understand why you are switching"
              rows={3}
            />
          </div>
          <Button
            onClick={() => mutation.mutate()}
            disabled={!targetLender.trim() || mutation.isPending}
          >
            {mutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <ArrowRight className="mr-2 h-4 w-4" />
            )}
            Initiate transfer
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
