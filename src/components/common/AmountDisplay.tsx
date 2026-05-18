import { cn } from '@/lib/utils';

interface AmountDisplayProps {
  amount: number | string | null | undefined;
  currency?: string;
  compact?: boolean;
  abbreviated?: boolean;
  className?: string;
}

function normalizeAmount(amount: AmountDisplayProps['amount']): number | null {
  if (amount === null || amount === undefined || amount === '') {
    return null;
  }

  const value = typeof amount === 'string' ? Number(amount) : amount;
  return Number.isFinite(value) ? value : null;
}

function formatCurrency(amount: number, currency: string, compact: boolean) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency,
    maximumFractionDigits: compact ? 0 : 2,
    minimumFractionDigits: compact ? 0 : 2,
  }).format(amount);
}

function formatCompactValue(value: number) {
  return value.toLocaleString('en-IN', {
    maximumFractionDigits: 2,
    minimumFractionDigits: Number.isInteger(value) ? 0 : 2,
  });
}

function getCurrencySymbol(currency: string) {
  const symbol =
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
    })
      .formatToParts(0)
      .find((part) => part.type === 'currency')?.value ?? currency;

  return symbol === '\u20B9' ? symbol : `${symbol} `;
}

export function formatIndianCompactCurrency(amount: number, currency = 'INR') {
  const sign = amount < 0 ? '-' : '';
  const absoluteAmount = Math.abs(amount);
  const currencySymbol = getCurrencySymbol(currency);

  if (absoluteAmount >= 10000000) {
    return `${sign}${currencySymbol}${formatCompactValue(absoluteAmount / 10000000)} Cr`;
  }

  if (absoluteAmount >= 100000) {
    return `${sign}${currencySymbol}${formatCompactValue(absoluteAmount / 100000)} L`;
  }

  return formatCurrency(amount, currency, false);
}

export function AmountDisplay({
  amount,
  currency = 'INR',
  compact = false,
  abbreviated = false,
  className,
}: AmountDisplayProps) {
  const numericAmount = normalizeAmount(amount);

  if (numericAmount === null) {
    return <span className={cn('text-gray-400', className)}>-</span>;
  }

  const fullAmount = formatCurrency(numericAmount, currency, false);
  const displayAmount = abbreviated
    ? formatIndianCompactCurrency(numericAmount, currency)
    : formatCurrency(numericAmount, currency, compact);

  return (
    <span className={className} title={abbreviated ? fullAmount : undefined}>
      {displayAmount}
    </span>
  );
}
