/**
 * Customer Portal — "Online payments coming soon" placeholder.
 *
 * Routed from the "Pay" button on every upcoming EMI.  Until the payment
 * gateway integration ships, this page explains the interim NACH/RTGS/NEFT
 * flow and accepts a "Notify me" intent (currently just a toast — no BE
 * wiring required per the prompt).
 */

import { ArrowLeft, BellRing, CreditCard } from 'lucide-react';
import { Link } from 'react-router-dom';

import { PageHeader } from '@/components/common';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';

export default function PortalPaymentComingSoon(): JSX.Element {
  const { toast } = useToast();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Online payments coming soon"
        subtitle="A self-service payment experience is on the way."
        breadcrumbs={[
          { label: 'Portal', to: '/portal/dashboard' },
          { label: 'Payments', to: '/portal/payments' },
          { label: 'Coming soon' },
        ]}
      />

      <Card>
        <CardContent className="p-8">
          <div className="mx-auto flex max-w-xl flex-col items-center gap-4 text-center">
            <div className="rounded-2xl bg-emerald-100 p-4 text-emerald-700">
              <CreditCard className="h-10 w-10" />
            </div>
            <h2 className="text-xl font-semibold">Online payments are on the way</h2>
            <p className="text-sm text-muted-foreground">
              We are wiring up secure online payments inside the portal. For now, please continue
              your existing NACH / RTGS / NEFT payment flow. If you need help, reach out to your
              relationship manager or our support team.
            </p>
            <div className="flex flex-col gap-3 pt-2 sm:flex-row">
              <Button
                onClick={() =>
                  toast({
                    title: "We'll notify you",
                    description: 'Thanks — we will email you when online payments launch.',
                  })
                }
                className="bg-emerald-600 hover:bg-emerald-700"
              >
                <BellRing className="mr-2 h-4 w-4" />
                Notify me when this launches
              </Button>
              <Button asChild variant="outline">
                <Link to="/portal/payments">
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back to payments
                </Link>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
