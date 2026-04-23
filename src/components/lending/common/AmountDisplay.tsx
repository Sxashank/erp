/**
 * AmountDisplay Component
 * Displays amounts in Indian currency format (Lakhs/Crores)
 */

import { cn } from '@/lib/utils';

export interface AmountDisplayProps {
  amount: number | string | null | undefined;
  format?: 'abbreviated' | 'full' | 'words';
  abbreviated?: boolean;
  showFull?: boolean;
  showCurrency?: boolean;
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  colorize?: boolean; // Green for positive, red for negative
}

/**
 * Formats a number in Indian numbering system (Lakhs/Crores)
 */
export function formatIndianCurrency(
  amount: number,
  format: 'abbreviated' | 'full' | 'words' = 'abbreviated'
): string {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return '-';
  }

  const absAmount = Math.abs(amount);
  const sign = amount < 0 ? '-' : '';

  if (format === 'full') {
    // Full Indian format: 1,23,45,678.00
    return sign + formatFullIndian(absAmount);
  }

  if (format === 'words') {
    return sign + formatInWords(absAmount);
  }

  // Abbreviated format: 15.25 Cr, 50.00 L
  if (absAmount >= 10000000) {
    // Crores (1 Cr = 10,000,000)
    const crores = absAmount / 10000000;
    return `${sign}${crores.toFixed(2)} Cr`;
  } else if (absAmount >= 100000) {
    // Lakhs (1 L = 100,000)
    const lakhs = absAmount / 100000;
    return `${sign}${lakhs.toFixed(2)} L`;
  } else if (absAmount >= 1000) {
    // Thousands
    const thousands = absAmount / 1000;
    return `${sign}${thousands.toFixed(2)} K`;
  } else {
    return `${sign}${absAmount.toFixed(2)}`;
  }
}

/**
 * Formats number in full Indian format with commas: 1,23,45,678.00
 */
function formatFullIndian(amount: number): string {
  const [intPart, decPart] = amount.toFixed(2).split('.');

  // Indian format: first 3 digits from right, then groups of 2
  let result = '';
  const digits = intPart.split('').reverse();

  for (let i = 0; i < digits.length; i++) {
    if (i === 3) {
      result = ',' + result;
    } else if (i > 3 && (i - 3) % 2 === 0) {
      result = ',' + result;
    }
    result = digits[i] + result;
  }

  return result + '.' + decPart;
}

/**
 * Formats number in words: Fifteen Crore Twenty Five Lakh
 */
function formatInWords(amount: number): string {
  if (amount === 0) return 'Zero';

  const crores = Math.floor(amount / 10000000);
  const lakhs = Math.floor((amount % 10000000) / 100000);
  const thousands = Math.floor((amount % 100000) / 1000);
  const hundreds = Math.floor((amount % 1000) / 100);
  const remainder = Math.floor(amount % 100);

  const parts: string[] = [];

  if (crores > 0) parts.push(`${numberToWords(crores)} Crore`);
  if (lakhs > 0) parts.push(`${numberToWords(lakhs)} Lakh`);
  if (thousands > 0) parts.push(`${numberToWords(thousands)} Thousand`);
  if (hundreds > 0) parts.push(`${numberToWords(hundreds)} Hundred`);
  if (remainder > 0) parts.push(numberToWords(remainder));

  return parts.join(' ');
}

const ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten',
  'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen'];
const tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];

function numberToWords(n: number): string {
  if (n < 20) return ones[n];
  if (n < 100) return tens[Math.floor(n / 10)] + (n % 10 ? ' ' + ones[n % 10] : '');
  return n.toString();
}

const sizeClasses = {
  sm: 'text-sm',
  md: 'text-base',
  lg: 'text-lg font-medium',
  xl: 'text-xl font-semibold',
};

export function AmountDisplay({
  amount,
  format: formatProp,
  abbreviated = false,
  showFull = false,
  showCurrency = true,
  className,
  size = 'md',
  colorize = false,
}: AmountDisplayProps) {
  const format = formatProp ?? (showFull ? 'full' : abbreviated ? 'abbreviated' : 'abbreviated');

  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;

  if (numAmount === null || numAmount === undefined || isNaN(numAmount)) {
    return <span className={cn(sizeClasses[size], 'text-muted-foreground', className)}>-</span>;
  }

  const formatted = formatIndianCurrency(numAmount, format);
  const displayText = showCurrency ? `\u20B9 ${formatted}` : formatted;

  let colorClass = '';
  if (colorize) {
    colorClass = numAmount >= 0 ? 'text-green-600' : 'text-red-600';
  }

  return (
    <span
      className={cn(
        sizeClasses[size],
        'tabular-nums font-mono',
        colorClass,
        className
      )}
      title={showCurrency ? `\u20B9 ${formatFullIndian(Math.abs(numAmount))}` : formatFullIndian(Math.abs(numAmount))}
    >
      {displayText}
    </span>
  );
}

/**
 * Compact variant for tables
 */
export function AmountCell({ amount, className }: { amount: number | null | undefined; className?: string }) {
  return (
    <AmountDisplay
      amount={amount}
      format="abbreviated"
      showCurrency={true}
      size="sm"
      className={cn('whitespace-nowrap', className)}
    />
  );
}

/**
 * Large display for headers/summaries
 */
export function AmountHeading({ amount, label, className }: {
  amount: number | null | undefined;
  label?: string;
  className?: string;
}) {
  return (
    <div className={cn('space-y-1', className)}>
      {label && <p className="text-sm text-muted-foreground">{label}</p>}
      <AmountDisplay
        amount={amount}
        format="abbreviated"
        showCurrency={true}
        size="xl"
      />
    </div>
  );
}
