/**
 * LoanSummaryCard Component
 * Loan account quick view card
 */

import { AmountDisplay } from './AmountDisplay';
import { DateDisplay } from './DateDisplay';
import { DPDIndicator } from './DPDBadge';
import { PercentageDisplay } from './PercentageDisplay';
import { AssetClassificationBadge, LoanAccountStatusBadge } from './StatusBadge';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import type { LoanAccount } from '@/types/lending';

export interface LoanSummaryCardProps {
  loan: LoanAccount;
  className?: string;
  variant?: 'default' | 'compact' | 'detailed';
  onClick?: () => void;
}

export function LoanSummaryCard({
  loan,
  className,
  variant = 'default',
  onClick,
}: LoanSummaryCardProps) {
  if (variant === 'compact') {
    return (
      <Card
        className={cn('cursor-pointer hover:shadow-md transition-shadow', className)}
        onClick={onClick}
      >
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">{loan.loan_account_number}</p>
              <p className="text-sm text-muted-foreground">{loan.entity_name}</p>
            </div>
            <div className="text-right">
              <AmountDisplay amount={loan.total_outstanding} size="md" />
              <div className="flex items-center gap-2 mt-1 justify-end">
                <AssetClassificationBadge status={loan.asset_classification} size="sm" />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (variant === 'detailed') {
    return (
      <Card className={cn(onClick && 'cursor-pointer hover:shadow-md transition-shadow', className)} onClick={onClick}>
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-lg">{loan.loan_account_number}</CardTitle>
              <p className="text-sm text-muted-foreground">{loan.entity_name}</p>
              <p className="text-xs text-muted-foreground">{loan.product_name}</p>
            </div>
            <div className="flex flex-col items-end gap-1">
              <LoanAccountStatusBadge status={loan.status} />
              <AssetClassificationBadge status={loan.asset_classification} size="sm" />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-muted-foreground">Sanctioned</p>
              <AmountDisplay amount={loan.sanctioned_amount} size="sm" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Disbursed</p>
              <AmountDisplay amount={loan.disbursed_amount} size="sm" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Outstanding</p>
              <AmountDisplay amount={loan.total_outstanding} size="sm" className="font-semibold" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">DPD</p>
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm">{loan.dpd}</span>
                <DPDIndicator dpd={loan.dpd} />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t">
            <div>
              <p className="text-xs text-muted-foreground">Interest Rate</p>
              <PercentageDisplay value={loan.effective_rate} className="text-sm font-medium" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Tenure</p>
              <p className="text-sm font-medium">{loan.tenure_months} months</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Maturity</p>
              <DateDisplay date={loan.maturity_date} className="text-sm" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Provision</p>
              <AmountDisplay amount={loan.provision_amount} size="sm" />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Default variant
  return (
    <Card
      className={cn(onClick && 'cursor-pointer hover:shadow-md transition-shadow', className)}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h3 className="font-medium">{loan.loan_account_number}</h3>
            <p className="text-sm text-muted-foreground">{loan.entity_name}</p>
          </div>
          <LoanAccountStatusBadge status={loan.status} size="sm" />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <p className="text-xs text-muted-foreground">Outstanding</p>
            <AmountDisplay amount={loan.total_outstanding} />
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Classification</p>
            <div className="flex items-center gap-2">
              <AssetClassificationBadge status={loan.asset_classification} size="sm" />
              <span className="text-sm text-muted-foreground">{loan.dpd}d</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Loan outstanding breakdown
 */
export function LoanOutstandingBreakdown({
  loan,
  className,
}: {
  loan: Pick<LoanAccount, 'principal_outstanding' | 'interest_outstanding' | 'penal_outstanding' | 'charges_outstanding' | 'total_outstanding'>;
  className?: string;
}) {
  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex justify-between items-center">
        <span className="text-sm text-muted-foreground">Principal</span>
        <AmountDisplay amount={loan.principal_outstanding} size="sm" />
      </div>
      <div className="flex justify-between items-center">
        <span className="text-sm text-muted-foreground">Interest</span>
        <AmountDisplay amount={loan.interest_outstanding} size="sm" />
      </div>
      {loan.penal_outstanding > 0 && (
        <div className="flex justify-between items-center">
          <span className="text-sm text-muted-foreground">Penal Interest</span>
          <AmountDisplay amount={loan.penal_outstanding} size="sm" className="text-red-600" />
        </div>
      )}
      {loan.charges_outstanding > 0 && (
        <div className="flex justify-between items-center">
          <span className="text-sm text-muted-foreground">Charges</span>
          <AmountDisplay amount={loan.charges_outstanding} size="sm" />
        </div>
      )}
      <div className="flex justify-between items-center pt-2 border-t font-semibold">
        <span>Total Outstanding</span>
        <AmountDisplay amount={loan.total_outstanding} size="md" className="font-semibold" />
      </div>
    </div>
  );
}

/**
 * Mini loan reference for inline display
 */
export function LoanReference({
  loan,
  className,
}: {
  loan: Pick<LoanAccount, 'loan_account_number' | 'entity_name'>;
  className?: string;
}) {
  return (
    <div className={cn('inline-flex items-center gap-1', className)}>
      <span className="font-mono font-medium">{loan.loan_account_number}</span>
      <span className="text-muted-foreground">({loan.entity_name})</span>
    </div>
  );
}
