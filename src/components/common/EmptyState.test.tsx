import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { EmptyState } from './EmptyState';

describe('EmptyState', () => {
  it('renders title and subtitle', () => {
    render(<EmptyState title="No results" subtitle="Try a different filter" />);
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText('No results')).toBeInTheDocument();
    expect(screen.getByText('Try a different filter')).toBeInTheDocument();
  });

  it('renders optional action slot', () => {
    render(<EmptyState title="No entities" action={<button>Create</button>} />);
    expect(screen.getByRole('button', { name: 'Create' })).toBeInTheDocument();
  });
});
