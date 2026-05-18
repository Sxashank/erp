/**
 * AmountInput Component
 * Currency input with Indian formatting and Cr/L suffix options
 */

import * as React from 'react';

import { formatIndianCurrency } from './AmountDisplay';

import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

export interface AmountInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'value' | 'onChange'> {
  value: number | string | undefined;
  onChange: (value: number | undefined) => void;
  showCurrency?: boolean;
  showAbbreviated?: boolean;
  min?: number;
  max?: number;
}

export function AmountInput({
  value,
  onChange,
  showCurrency = true,
  showAbbreviated = true,
  min,
  max,
  className,
  disabled,
  ...props
}: AmountInputProps) {
  const [displayValue, setDisplayValue] = React.useState('');
  const [isFocused, setIsFocused] = React.useState(false);

  // Update display value when external value changes
  React.useEffect(() => {
    if (!isFocused) {
      const numValue = typeof value === 'string' ? parseFloat(value) : value;
      if (numValue !== undefined && !isNaN(numValue)) {
        setDisplayValue(formatForDisplay(numValue));
      } else {
        setDisplayValue('');
      }
    }
  }, [value, isFocused]);

  // Format number with commas for display (Indian format)
  function formatForDisplay(num: number): string {
    return num.toLocaleString('en-IN', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });
  }

  // Parse input value, removing commas and non-numeric chars
  function parseInputValue(input: string): number | undefined {
    // Remove all non-numeric chars except decimal point
    const cleaned = input.replace(/[^\d.]/g, '');
    if (cleaned === '' || cleaned === '.') return undefined;

    const num = parseFloat(cleaned);
    if (isNaN(num)) return undefined;

    return num;
  }

  const handleFocus = () => {
    setIsFocused(true);
    // Show raw number on focus
    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    if (numValue !== undefined && !isNaN(numValue)) {
      setDisplayValue(numValue.toString());
    }
  };

  const handleBlur = () => {
    setIsFocused(false);
    // Format on blur
    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    if (numValue !== undefined && !isNaN(numValue)) {
      // Validate min/max
      let validValue = numValue;
      if (min !== undefined && numValue < min) validValue = min;
      if (max !== undefined && numValue > max) validValue = max;

      if (validValue !== numValue) {
        onChange(validValue);
      }
      setDisplayValue(formatForDisplay(validValue));
    } else {
      setDisplayValue('');
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const input = e.target.value;
    setDisplayValue(input);

    const parsed = parseInputValue(input);
    onChange(parsed);
  };

  // Calculate abbreviated display
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  const abbreviatedValue = numValue !== undefined && !isNaN(numValue) && showAbbreviated
    ? formatIndianCurrency(numValue, 'abbreviated')
    : null;

  return (
    <div className="relative">
      <div className={cn('relative', className)}>
        {showCurrency && (
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">
            ₹
          </span>
        )}
        <Input
          type="text"
          inputMode="decimal"
          value={displayValue}
          onChange={handleChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          disabled={disabled}
          className={cn(
            'text-right font-mono',
            showCurrency && 'pl-7',
            abbreviatedValue && !isFocused && 'pr-20'
          )}
          {...props}
        />
        {abbreviatedValue && !isFocused && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">
            ({abbreviatedValue})
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * AmountInput with form field wrapper
 */
export interface AmountFieldProps extends AmountInputProps {
  label?: string;
  error?: string;
  hint?: string;
  required?: boolean;
}

export function AmountField({
  label,
  error,
  hint,
  required,
  className,
  ...props
}: AmountFieldProps) {
  return (
    <div className={cn('space-y-2', className)}>
      {label && (
        <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
          {label}
          {required && <span className="text-destructive ml-1">*</span>}
        </label>
      )}
      <AmountInput {...props} />
      {hint && !error && (
        <p className="text-sm text-muted-foreground">{hint}</p>
      )}
      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}
    </div>
  );
}
