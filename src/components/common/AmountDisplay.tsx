import { cn } from '@/lib/utils';

interface AmountDisplayProps {
  amount: number | null | undefined;
  currency?: string;
  compact?: boolean;
  className?: string;
}

export function AmountDisplay({
  amount,
  currency = 'INR',
  compact = false,
  className,
}: AmountDisplayProps) {
  if (amount === null || amount === undefined) {
    return <span className={cn('text-gray-400', className)}>-</span>;
  }

  const formatter = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency,
    maximumFractionDigits: compact ? 0 : 2,
    minimumFractionDigits: compact ? 0 : 2,
  });

  return <span className={className}>{formatter.format(amount)}</span>;
}
