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
  return symbol === '₹' ? symbol : `${symbol} `;
}

export function formatPreciseCurrency(amount: number, currency = 'INR') {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  }).format(amount);
}

/** Indian compact: ≥ 1 Cr → "X.YY Cr", ≥ 1 L → "X.YY L", else "X,XXX". */
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
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency,
    maximumFractionDigits: Number.isInteger(amount) ? 0 : 2,
    minimumFractionDigits: 0,
  }).format(amount);
}
