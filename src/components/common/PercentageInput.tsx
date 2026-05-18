import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

export interface PercentageInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'value' | 'onChange'> {
  value: number | string | null | undefined;
  onChange: (value: number | undefined) => void;
}

export function PercentageInput({
  value,
  onChange,
  className,
  disabled,
  ...props
}: PercentageInputProps): JSX.Element {
  return (
    <div className="relative">
      <Input
        type="number"
        min="0"
        max="100"
        step="0.01"
        inputMode="decimal"
        value={value ?? ''}
        onChange={(event) => {
          const nextValue = event.target.value;
          onChange(nextValue === '' ? undefined : Number(nextValue));
        }}
        disabled={disabled}
        className={cn('pr-8 text-right font-mono', className)}
        {...props}
      />
      <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
        %
      </span>
    </div>
  );
}
