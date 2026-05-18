import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import { describe, expect, it, vi } from 'vitest';

import { PercentageInput } from './PercentageInput';

describe('PercentageInput', () => {
  it('renders the current value and suffix', () => {
    render(<PercentageInput value={12.5} onChange={() => undefined} aria-label="Rate" />);
    expect(screen.getByRole('spinbutton', { name: 'Rate' })).toHaveValue(12.5);
    expect(screen.getByText('%')).toBeInTheDocument();
  });

  it('parses numeric changes', async () => {
    const onChange = vi.fn();
    function Harness(): JSX.Element {
      const [value, setValue] = useState<number | undefined>(undefined);

      return (
        <PercentageInput
          value={value}
          onChange={(nextValue) => {
            setValue(nextValue);
            onChange(nextValue);
          }}
          aria-label="Rate"
        />
      );
    }

    render(<Harness />);
    await userEvent.type(screen.getByRole('spinbutton', { name: 'Rate' }), '7.25');
    expect(onChange).toHaveBeenLastCalledWith(7.25);
  });
});
