/**
 * AmountDisplay — the only sanctioned way to render an INR amount in this app.
 *
 * Default: Indian-format compact ("₹1.02 Cr", "₹12.5 L", "₹4,500").
 * On hover, the user sees the exact rupees+paise in a native tooltip.
 *
 * Use ``precise`` ONLY for the small set of screens where every rupee+paise
 * matters: receipts/vouchers/payment lines/GST + TDS amounts/payslip
 * statutory columns/bank reconciliation. Everywhere else — dashboards,
 * cards, list tables, detail pages — leave the default on.
 *
 * See CLAUDE.md §5.8 — inline ``Intl.NumberFormat('INR', ...)``, hand-rolled
 * ``formatCurrency``, ``toFixed(2)``, or ``toLocaleString`` for money is a
 * defect. Everything goes through this component.
 */

import { cn } from '@/lib/utils';
import { formatIndianCompactCurrency, formatPreciseCurrency } from '@/lib/currency';

interface AmountDisplayProps {
  amount: number | string | null | undefined;
  currency?: string;
  /** Force exact ₹X,XX,XXX.YY. Use only where rupees+paise truly matter. */
  precise?: boolean;
  /**
   * Legacy aliases — kept for back-compat while we sweep the codebase.
   * - ``abbreviated`` (old) === default (do nothing).
   * - ``compact`` (old) was a no-decimals override; superseded by the new default.
   */
  abbreviated?: boolean;
  compact?: boolean;
  className?: string;
}

function normalizeAmount(amount: AmountDisplayProps['amount']): number | null {
  if (amount === null || amount === undefined || amount === '') {
    return null;
  }
  const value = typeof amount === 'string' ? Number(amount) : amount;
  return Number.isFinite(value) ? value : null;
}

export { formatIndianCompactCurrency } from '@/lib/currency';

export function AmountDisplay({
  amount,
  currency = 'INR',
  precise = false,
  abbreviated, // legacy — implicitly true under the new default
  compact, // legacy — implicitly true under the new default
  className,
}: AmountDisplayProps) {
  void abbreviated;
  void compact;

  const numericAmount = normalizeAmount(amount);
  if (numericAmount === null) {
    return <span className={cn('text-gray-400', className)}>-</span>;
  }

  const exact = formatPreciseCurrency(numericAmount, currency);
  const display = precise ? exact : formatIndianCompactCurrency(numericAmount, currency);

  return (
    <span className={cn('tabular-nums', className)} title={precise ? undefined : exact}>
      {display}
    </span>
  );
}
