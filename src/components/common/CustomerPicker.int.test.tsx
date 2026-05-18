/**
 * Integration test: CustomerPicker component + customer hook + MSW.
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import { describe, expect, it, vi } from 'vitest';

import { CustomerPicker } from './CustomerPicker';

function Host() {
  const [value, setValue] = useState<string | null>(null);
  return (
    <div>
      <span data-testid="selected">{value ?? 'none'}</span>
      <CustomerPicker value={value} onChange={setValue} />
    </div>
  );
}

function renderHost() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <Host />
    </QueryClientProvider>,
  );
}

describe('CustomerPicker (integration)', () => {
  it('opens, shows customers from API, and selects one', async () => {
    const user = userEvent.setup();
    renderHost();

    // Trigger opens the popover.
    await user.click(screen.getByRole('combobox'));

    // Wait for the list to load and pick one.
    const option = await screen.findByRole('option', { name: /Acme Industries/i });
    await user.click(option);

    expect(screen.getByTestId('selected')).toHaveTextContent('c1');
  });

  it('filters by search query', async () => {
    const user = userEvent.setup();
    renderHost();
    await user.click(screen.getByRole('combobox'));

    const search = screen.getByPlaceholderText(/search/i);
    await user.type(search, 'Beta');

    // Acme should be filtered out, Beta remains.
    expect(screen.queryByRole('option', { name: /Acme/i })).toBeNull();
    expect(screen.getByRole('option', { name: /Beta/i })).toBeInTheDocument();
  });
});
