import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { AmountDisplay, formatIndianCompactCurrency } from './AmountDisplay';

describe('AmountDisplay', () => {
  it('defaults to Indian compact: crore values render as Cr with full title', () => {
    render(<AmountDisplay amount={100000000} />);
    const amount = screen.getByText('₹10 Cr');
    expect(amount).toBeInTheDocument();
    expect(amount).toHaveAttribute('title', '₹10,00,00,000.00');
  });

  it('defaults to compact for lakh values too', () => {
    render(<AmountDisplay amount={125000} />);
    expect(screen.getByText('₹1.25 L')).toBeInTheDocument();
  });

  it('sub-lakh values fall back to full Indian grouping', () => {
    render(<AmountDisplay amount={4500} />);
    expect(screen.getByText('₹4,500')).toBeInTheDocument();
  });

  it('precise=true forces exact rupees+paise (no hover title)', () => {
    render(<AmountDisplay amount={100000000} precise />);
    const amount = screen.getByText('₹10,00,00,000.00');
    expect(amount).toBeInTheDocument();
    expect(amount).not.toHaveAttribute('title');
  });

  it('renders a dash placeholder for null / undefined / empty string', () => {
    const { rerender, container } = render(<AmountDisplay amount={null} />);
    expect(container.textContent).toBe('-');
    rerender(<AmountDisplay amount={undefined} />);
    expect(container.textContent).toBe('-');
    rerender(<AmountDisplay amount="" />);
    expect(container.textContent).toBe('-');
  });

  it('formatIndianCompactCurrency direct: lakh helper', () => {
    expect(formatIndianCompactCurrency(125000)).toBe('₹1.25 L');
  });

  it('formatIndianCompactCurrency direct: sub-lakh helper', () => {
    expect(formatIndianCompactCurrency(50000)).toBe('₹50,000');
  });

  it('formatIndianCompactCurrency direct: negative crore', () => {
    expect(formatIndianCompactCurrency(-25000000)).toBe('-₹2.50 Cr');
  });

  it('always uses tabular-nums so currency columns line up', () => {
    render(<AmountDisplay amount={1234} />);
    const span = screen.getByText('₹1,234');
    expect(span.className).toContain('tabular-nums');
  });
});
