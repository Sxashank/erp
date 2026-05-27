import { Wallet, ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface CashFlowProps {
  totalBankBalance: number;
  receiptsToday: number;
  paymentsToday: number;
  netToday: number;
  receiptsWeek: number;
  paymentsWeek: number;
  netWeek: number;
  receiptsMonth: number;
  paymentsMonth: number;
  netMonth: number;
  pendingChequeReceipts?: number;
  pendingChequePayments?: number;
}
const formatCompact = (amount: number | undefined | null) => {
  const num = Number(amount) || 0;
  const absAmount = Math.abs(num);
  if (absAmount >= 10000000) {
    return `${(num / 10000000).toFixed(2)} Cr`;
  }
  if (absAmount >= 100000) {
    return `${(num / 100000).toFixed(2)} L`;
  }
  if (absAmount >= 1000) {
    return `${(num / 1000).toFixed(1)} K`;
  }
  return num.toFixed(0);
};

export function CashFlowWidget({
  totalBankBalance,
  receiptsToday,
  paymentsToday,
  netToday,
  receiptsWeek,
  paymentsWeek,
  netWeek,
  receiptsMonth,
  paymentsMonth,
  netMonth,
  pendingChequeReceipts,
  pendingChequePayments,
}: CashFlowProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-lg font-semibold">
          <Wallet className="h-5 w-5 text-green-500" />
          Cash Flow
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Bank Balance */}
        <div className="rounded-lg bg-gradient-to-r from-green-500 to-emerald-600 p-4 text-white">
          <p className="text-sm opacity-90">Total Bank Balance</p>
          <p className="mt-1 text-3xl font-bold">{formatIndianCompactCurrency(totalBankBalance)}</p>
        </div>

        {/* Period Breakdown */}
        <div className="space-y-3">
          {/* Today */}
          <div className="rounded-lg border p-3">
            <p className="mb-2 text-sm font-medium text-muted-foreground">Today</p>
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div>
                <div className="flex items-center gap-1 text-green-600">
                  <ArrowUpRight className="h-3 w-3" />
                  <span>Receipts</span>
                </div>
                <p className="font-medium">{formatCompact(receiptsToday)}</p>
              </div>
              <div>
                <div className="flex items-center gap-1 text-red-600">
                  <ArrowDownRight className="h-3 w-3" />
                  <span>Payments</span>
                </div>
                <p className="font-medium">{formatCompact(paymentsToday)}</p>
              </div>
              <div>
                <div className="flex items-center gap-1 text-muted-foreground">
                  <Minus className="h-3 w-3" />
                  <span>Net</span>
                </div>
                <p className={cn('font-medium', netToday >= 0 ? 'text-green-600' : 'text-red-600')}>
                  {formatCompact(netToday)}
                </p>
              </div>
            </div>
          </div>

          {/* This Week */}
          <div className="rounded-lg border p-3">
            <p className="mb-2 text-sm font-medium text-muted-foreground">This Week</p>
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div>
                <div className="flex items-center gap-1 text-green-600">
                  <ArrowUpRight className="h-3 w-3" />
                  <span>Receipts</span>
                </div>
                <p className="font-medium">{formatCompact(receiptsWeek)}</p>
              </div>
              <div>
                <div className="flex items-center gap-1 text-red-600">
                  <ArrowDownRight className="h-3 w-3" />
                  <span>Payments</span>
                </div>
                <p className="font-medium">{formatCompact(paymentsWeek)}</p>
              </div>
              <div>
                <div className="flex items-center gap-1 text-muted-foreground">
                  <Minus className="h-3 w-3" />
                  <span>Net</span>
                </div>
                <p className={cn('font-medium', netWeek >= 0 ? 'text-green-600' : 'text-red-600')}>
                  {formatCompact(netWeek)}
                </p>
              </div>
            </div>
          </div>

          {/* This Month */}
          <div className="rounded-lg border p-3">
            <p className="mb-2 text-sm font-medium text-muted-foreground">This Month</p>
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div>
                <div className="flex items-center gap-1 text-green-600">
                  <ArrowUpRight className="h-3 w-3" />
                  <span>Receipts</span>
                </div>
                <p className="font-medium">{formatCompact(receiptsMonth)}</p>
              </div>
              <div>
                <div className="flex items-center gap-1 text-red-600">
                  <ArrowDownRight className="h-3 w-3" />
                  <span>Payments</span>
                </div>
                <p className="font-medium">{formatCompact(paymentsMonth)}</p>
              </div>
              <div>
                <div className="flex items-center gap-1 text-muted-foreground">
                  <Minus className="h-3 w-3" />
                  <span>Net</span>
                </div>
                <p className={cn('font-medium', netMonth >= 0 ? 'text-green-600' : 'text-red-600')}>
                  {formatCompact(netMonth)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Pending Cheques */}
        {(pendingChequeReceipts || pendingChequePayments) && (
          <div className="rounded-lg bg-yellow-50 p-3">
            <p className="mb-2 text-sm font-medium text-yellow-800">Pending Cheques</p>
            <div className="grid grid-cols-2 gap-4 text-sm">
              {pendingChequeReceipts !== undefined && pendingChequeReceipts > 0 && (
                <div>
                  <span className="text-yellow-700">Receipts: </span>
                  <span className="font-medium">{formatCompact(pendingChequeReceipts)}</span>
                </div>
              )}
              {pendingChequePayments !== undefined && pendingChequePayments > 0 && (
                <div>
                  <span className="text-yellow-700">Payments: </span>
                  <span className="font-medium">{formatCompact(pendingChequePayments)}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
