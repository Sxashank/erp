import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

import { formatIndianCompactCurrency } from '@/lib/currency';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format a date to a readable string
 */
export function formatDate(
  date: string | Date | null | undefined,
  options?: Intl.DateTimeFormatOptions,
): string {
  if (!date) return '-';

  const dateObj = typeof date === 'string' ? new Date(date) : date;

  if (isNaN(dateObj.getTime())) return '-';

  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...options,
  };

  return dateObj.toLocaleDateString('en-IN', defaultOptions);
}

/**
 * Format a number as currency (INR).
 *
 * Per CLAUDE.md §5.8, the canonical render is `<AmountDisplay />`. This
 * helper exists for non-JSX call sites (PDF export, CSV download, logging)
 * and now delegates to the Indian-compact formatter so everything
 * normalises to "1 L", "1.02 Cr", etc. JSX call sites should be migrated
 * to <AmountDisplay /> over time.
 */
export function formatCurrency(
  amount: number | string | null | undefined,
  currency = 'INR',
): string {
  if (amount === null || amount === undefined || amount === '') return '-';
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (isNaN(num)) return '-';
  return formatIndianCompactCurrency(num, currency);
}

/**
 * Format a number with thousands separators
 */
export function formatNumber(num: number | string | null | undefined, decimals = 0): string {
  if (num === null || num === undefined || num === '') return '-';

  const number = typeof num === 'string' ? parseFloat(num) : num;

  if (isNaN(number)) return '-';

  return new Intl.NumberFormat('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(number);
}

/**
 * Format a percentage value
 */
export function formatPercentage(value: number | string | null | undefined, decimals = 2): string {
  if (value === null || value === undefined || value === '') return '-';

  const num = typeof value === 'string' ? parseFloat(value) : value;

  if (isNaN(num)) return '-';

  return `${num.toFixed(decimals)}%`;
}

/**
 * Format a date with time to a readable string
 */
export function formatDateTime(date: string | Date | null | undefined): string {
  if (!date) return '-';

  const dateObj = typeof date === 'string' ? new Date(date) : date;

  if (isNaN(dateObj.getTime())) return '-';

  return dateObj.toLocaleString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
