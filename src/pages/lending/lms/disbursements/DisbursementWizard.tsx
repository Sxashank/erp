import { ArrowLeft, CheckCircle, Loader2, Send } from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { useDisbursement } from '@/hooks/lending/useDisbursements';

const statusVariant: Record<string, 'default' | 'secondary' | 'destructive'> = {
  PENDING: 'secondary',
  APPROVED: 'default',
  PROCESSED: 'default',
  REJECTED: 'destructive',
  CANCELLED: 'secondary',
  FAILED: 'destructive',
  REVERSED: 'secondary',
};

export default function DisbursementWizard() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { data: disbursement, isLoading, isError, error, refetch } = useDisbursement(id);

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (isError || !disbursement) {
    return (
      <ErrorState title="Could not load disbursement" error={error} onRetry={() => refetch()} />
    );
  }

  const amount =
    disbursement.disbursedAmount ?? disbursement.approvedAmount ?? disbursement.requestedAmount;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Disbursement Details"
        subtitle={disbursement.disbursementReference}
        breadcrumbs={[
          { label: 'Disbursements', to: '/admin/lending/disbursements' },
          { label: disbursement.disbursementReference },
        ]}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigate('/admin/lending/disbursements')}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            {disbursement.status === 'PENDING' && (
              <Button
                variant="outline"
                onClick={() => navigate(`/admin/lending/disbursements/${disbursement.id}/approve`)}
              >
                <CheckCircle className="mr-2 h-4 w-4" />
                Approve
              </Button>
            )}
            {disbursement.status === 'APPROVED' && (
              <Button
                onClick={() => navigate(`/admin/lending/disbursements/${disbursement.id}/process`)}
              >
                <Send className="mr-2 h-4 w-4" />
                Process
              </Button>
            )}
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Amount</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={amount} abbreviated className="text-2xl font-bold" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={statusVariant[disbursement.status] ?? 'secondary'}>
              {disbursement.status}
            </Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Tranche</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{disbursement.disbursementNumber}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Request Information</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-6 md:grid-cols-2">
          <div>
            <Label className="text-muted-foreground">Loan Account</Label>
            <p className="font-mono">{disbursement.loanAccountNumber ?? 'Not available'}</p>
          </div>
          <div>
            <Label className="text-muted-foreground">Borrower Entity</Label>
            <p className="font-medium">{disbursement.entityName ?? 'Not available'}</p>
          </div>
          <div>
            <Label className="text-muted-foreground">Requested Amount</Label>
            <p className="font-semibold">
              <AmountDisplay amount={disbursement.requestedAmount} showFull />
            </p>
          </div>
          <div>
            <Label className="text-muted-foreground">Approved Amount</Label>
            <p className="font-semibold">
              {disbursement.approvedAmount ? (
                <AmountDisplay amount={disbursement.approvedAmount} showFull />
              ) : (
                'Pending approval'
              )}
            </p>
          </div>
          <div>
            <Label className="text-muted-foreground">Request Date</Label>
            <p>
              <DateDisplay date={disbursement.requestDate} />
            </p>
          </div>
          <div>
            <Label className="text-muted-foreground">Disbursement Date</Label>
            <p>
              {disbursement.disbursementDate ? (
                <DateDisplay date={disbursement.disbursementDate} />
              ) : (
                'Not processed'
              )}
            </p>
          </div>
          <div>
            <Label className="text-muted-foreground">Beneficiary</Label>
            <p className="font-medium">{disbursement.beneficiaryName}</p>
          </div>
          <div>
            <Label className="text-muted-foreground">UTR / Reference</Label>
            <p className="font-mono">{disbursement.utrNumber ?? 'Not recorded'}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
