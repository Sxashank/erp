import { formatIndianCompactCurrency } from '@/lib/currency';

declare global {
  interface Window {
    formatIndianCompactCurrency?: typeof formatIndianCompactCurrency;
  }
}

(
  globalThis as typeof globalThis & {
    formatIndianCompactCurrency: typeof formatIndianCompactCurrency;
  }
).formatIndianCompactCurrency = formatIndianCompactCurrency;
