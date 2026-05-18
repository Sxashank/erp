import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { AmountDisplay, formatIndianCompactCurrency } from './AmountDisplay';

describe('AmountDisplay', () => {
  it('renders the full Indian currency format by default', () => {
    render(<AmountDisplay amount={100000000} />);

    expect(screen.getByText('\u20B910,00,00,000.00')).toBeInTheDocument();
  });

  it('renders crore values in abbreviated mode with the full value in the title', () => {
    render(<AmountDisplay amount={100000000} abbreviated />);

    const amount = screen.getByText('\u20B910 Cr');
    expect(amount).toBeInTheDocument();
    expect(amount).toHaveAttribute('title', '\u20B910,00,00,000.00');
  });

  it('renders lakh values in abbreviated mode', () => {
    expect(formatIndianCompactCurrency(125000)).toBe('\u20B91.25 L');
  });

  it('keeps small values in full currency format when abbreviated', () => {
    expect(formatIndianCompactCurrency(50000)).toBe('\u20B950,000.00');
  });
});
