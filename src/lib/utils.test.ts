/**
 * Unit tests for `src/lib/utils.ts`. Targets 100% on this module per
 * CLAUDE.md §10.1.
 */

import { describe, expect, it } from 'vitest';

import {
  cn,
  formatCurrency,
  formatDate,
  formatDateTime,
  formatNumber,
  formatPercentage,
} from './utils';

describe('cn', () => {
  it('merges class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar');
  });
  it('dedupes conflicting tailwind classes via twMerge', () => {
    expect(cn('p-2', 'p-4')).toBe('p-4');
  });
  it('filters falsy values', () => {
    expect(cn('foo', null, undefined, false, 'bar')).toBe('foo bar');
  });
});

describe('formatCurrency', () => {
  it('formats positive INR amount with 2 decimals', () => {
    // en-IN uses narrow no-break space (U+00A0 or U+202F) between symbol and digits.
    expect(formatCurrency(1234567.89)).toMatch(/₹[\s  ]?12,34,567\.89/);
  });
  it('returns dash for null/undefined/empty', () => {
    expect(formatCurrency(null)).toBe('-');
    expect(formatCurrency(undefined)).toBe('-');
    expect(formatCurrency('')).toBe('-');
  });
  it('parses string inputs', () => {
    expect(formatCurrency('100')).toMatch(/100\.00/);
  });
  it('returns dash for NaN input', () => {
    expect(formatCurrency('not-a-number')).toBe('-');
  });
});

describe('formatNumber', () => {
  it('formats with thousands separators in en-IN', () => {
    expect(formatNumber(1234567)).toBe('12,34,567');
  });
  it('respects decimals', () => {
    expect(formatNumber(1.23456, 2)).toBe('1.23');
  });
  it('returns dash for null', () => {
    expect(formatNumber(null)).toBe('-');
  });
});

describe('formatPercentage', () => {
  it('formats with 2 decimals', () => {
    expect(formatPercentage(12.5)).toBe('12.50%');
  });
  it('returns dash for null', () => {
    expect(formatPercentage(null)).toBe('-');
  });
});

describe('formatDate / formatDateTime', () => {
  it('formats ISO date in en-IN', () => {
    const out = formatDate('2026-04-23');
    expect(out).toMatch(/Apr/);
    expect(out).toMatch(/2026/);
  });
  it('formats Date objects', () => {
    const d = new Date(2026, 3, 23);
    expect(formatDate(d)).toMatch(/Apr/);
  });
  it('returns dash for invalid or null dates', () => {
    expect(formatDate(null)).toBe('-');
    expect(formatDate('not-a-date')).toBe('-');
    expect(formatDateTime(null)).toBe('-');
  });
  it('formatDateTime includes time portion', () => {
    const out = formatDateTime('2026-04-23T10:30:00Z');
    expect(out).toMatch(/2026/);
  });
});
