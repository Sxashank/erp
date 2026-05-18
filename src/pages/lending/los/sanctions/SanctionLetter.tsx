/**
 * Sanction Letter (printable view).
 *
 * Fetches sanction by ID and renders a print-ready letter. Borrower
 * address / signatory details are not yet on the slim sanction detail
 * endpoint — those sections show "—" placeholders until the BE response
 * is extended to include them via the EntityDetailResponse join.
 */

import { Download, ArrowLeft } from 'lucide-react';
import { useParams, useNavigate } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { PrintButton } from '@/components/lending/common/PrintButton';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useSanction } from '@/hooks/lending/useSanction';

export default function SanctionLetter() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: sanction, isLoading, isError, error, refetch } = useSanction(id);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Sanction Letter" subtitle="Loading..." />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (isError || !sanction) {
    return (
      <div className="space-y-6">
        <PageHeader title="Sanction Letter" />
        <ErrorState title="Could not load sanction" error={error} onRetry={() => refetch()} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Sanction Letter · ${sanction.sanctionNumber}`}
        breadcrumbs={[
          { label: 'Sanctions', to: '/admin/lending/sanctions' },
          { label: sanction.sanctionNumber, to: `/admin/lending/sanctions/${id}` },
          { label: 'Letter' },
        ]}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigate(`/admin/lending/sanctions/${id}`)}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            <PrintButton />
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Download PDF
            </Button>
          </div>
        }
      />

      <Card className="mx-auto max-w-4xl print:border-none print:shadow-none">
        <CardContent className="space-y-6 p-10">
          <div className="border-b pb-4 text-center">
            <h1 className="text-2xl font-bold">SANCTION LETTER</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Reference: {sanction.sanctionNumber}
            </p>
            <p className="text-sm text-muted-foreground">
              Date: <DateDisplay date={sanction.sanctionDate} />
            </p>
          </div>

          <section>
            <h2 className="mb-2 font-semibold">1. Sanctioned Amount & Terms</h2>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-muted-foreground">Sanctioned Amount</dt>
                <dd className="font-medium">
                  <AmountDisplay amount={sanction.sanctionedAmount} />
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Tenure</dt>
                <dd className="font-medium">{sanction.tenureMonths} months</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Moratorium</dt>
                <dd className="font-medium">{sanction.moratoriumMonths} months</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Effective Rate</dt>
                <dd className="font-medium">
                  <PercentageDisplay value={sanction.effectiveRate} /> p.a.
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Repayment Mode</dt>
                <dd className="font-medium">{sanction.repaymentMode}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Repayment Frequency</dt>
                <dd className="font-medium">{sanction.repaymentFrequency}</dd>
              </div>
            </dl>
          </section>

          {sanction.specialTerms && (
            <section>
              <h2 className="mb-2 font-semibold">2. Special Terms</h2>
              <p className="whitespace-pre-line text-sm">{sanction.specialTerms}</p>
            </section>
          )}

          <section>
            <h2 className="mb-2 font-semibold">Validity</h2>
            <p className="text-sm">
              This sanction is valid until{' '}
              <strong>
                <DateDisplay date={sanction.validityDate} />
              </strong>
              .
            </p>
          </section>

          {sanction.remarks && (
            <section>
              <h2 className="mb-2 font-semibold">Remarks</h2>
              <p className="whitespace-pre-line text-sm">{sanction.remarks}</p>
            </section>
          )}

          <div className="grid grid-cols-2 gap-12 pt-12 text-sm">
            <div className="border-t pt-2 text-center">
              <p className="text-muted-foreground">For the Lender</p>
              <p className="mt-12 border-t pt-2">Authorised Signatory</p>
            </div>
            <div className="border-t pt-2 text-center">
              <p className="text-muted-foreground">For the Borrower</p>
              <p className="mt-12 border-t pt-2">Authorised Signatory</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
