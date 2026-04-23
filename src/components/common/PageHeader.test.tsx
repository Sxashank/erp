import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MemoryRouter } from 'react-router-dom';

import { PageHeader } from './PageHeader';

function renderWithRouter(ui: React.ReactNode) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe('PageHeader', () => {
  it('renders title and subtitle', () => {
    renderWithRouter(<PageHeader title="Loan Applications" subtitle="All active" />);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Loan Applications');
    expect(screen.getByText('All active')).toBeInTheDocument();
  });

  it('renders breadcrumbs, linking all but the last', () => {
    renderWithRouter(
      <PageHeader
        title="Create Application"
        breadcrumbs={[
          { label: 'Lending', to: '/admin/lending' },
          { label: 'Applications', to: '/admin/lending/applications' },
          { label: 'New' },
        ]}
      />,
    );
    expect(screen.getByRole('link', { name: 'Lending' })).toHaveAttribute(
      'href',
      '/admin/lending',
    );
    expect(screen.getByRole('link', { name: 'Applications' })).toBeInTheDocument();
    // The last crumb must NOT be a link.
    expect(screen.queryByRole('link', { name: 'New' })).toBeNull();
    const last = screen.getByText('New');
    expect(last).toHaveAttribute('aria-current', 'page');
  });

  it('renders action slot', () => {
    renderWithRouter(
      <PageHeader title="Vouchers" actions={<button>New Voucher</button>} />,
    );
    expect(screen.getByRole('button', { name: 'New Voucher' })).toBeInTheDocument();
  });
});
