/**
 * Design-token contract tests.
 *
 * Every common component commits to a small number of token-derived class
 * names so pages end up visually consistent. If a future refactor deletes
 * `text-2xl` from PageHeader, or drops `tabular-nums` from DataTable's
 * numeric column, these tests fail with a named error. See CLAUDE.md §9.
 */

import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { DataTable, type Column } from './DataTable';
import { EmptyState } from './EmptyState';
import { ErrorState } from './ErrorState';
import { FormSection, FormShell } from './FormShell';
import { PageHeader } from './PageHeader';

function renderWithRouter(ui: React.ReactNode) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

// ---------------------------------------------------------------------------
// PageHeader — title uses display typography, subtitle uses muted foreground.
// ---------------------------------------------------------------------------

describe('PageHeader design tokens', () => {
  it('title is h1 and uses the 2xl display size + semibold weight', () => {
    renderWithRouter(<PageHeader title="Loan Applications" />);
    const title = screen.getByRole('heading', { level: 1 });
    expect(title.className).toContain('text-2xl');
    expect(title.className).toContain('font-semibold');
    expect(title.className).toContain('tracking-tight');
  });

  it('subtitle uses muted-foreground token', () => {
    renderWithRouter(<PageHeader title="Loans" subtitle="All open applications" />);
    const subtitle = screen.getByText('All open applications');
    expect(subtitle.className).toContain('text-muted-foreground');
    expect(subtitle.className).toContain('text-sm');
  });

  it('breadcrumb uses text-sm + muted-foreground', () => {
    renderWithRouter(
      <PageHeader
        title="New"
        breadcrumbs={[
          { label: 'Lending', to: '/admin/lending' },
          { label: 'Applications' },
        ]}
      />,
    );
    const nav = screen.getByRole('navigation', { name: /breadcrumb/i });
    expect(nav.querySelector('ol')?.className).toContain('text-sm');
    expect(nav.querySelector('ol')?.className).toContain('text-muted-foreground');
  });
});

// ---------------------------------------------------------------------------
// FormSection — title + muted description.
// ---------------------------------------------------------------------------

describe('FormShell design tokens', () => {
  it('FormSection title uses text-base + semibold', () => {
    render(
      <FormSection title="Posting details">
        <div />
      </FormSection>,
    );
    const heading = screen.getByText('Posting details');
    expect(heading.className).toContain('text-base');
    expect(heading.className).toContain('font-semibold');
  });

  it('FormSection content uses grid with two columns on md+', () => {
    const { container } = render(
      <FormSection title="x">
        <div data-testid="field" />
      </FormSection>,
    );
    const gridParent = container.querySelector('.grid');
    expect(gridParent?.className).toContain('gap-4');
    expect(gridParent?.className).toContain('md:grid-cols-2');
  });

  it('FormShell renders a Card and a sticky footer when footer provided', () => {
    const { container } = render(
      <FormShell footer={<button>Save</button>}>
        <div />
      </FormShell>,
    );
    const sticky = container.querySelector('.sticky');
    expect(sticky?.className).toContain('bottom-0');
    expect(sticky?.className).toContain('border-t');
  });
});

// ---------------------------------------------------------------------------
// EmptyState / ErrorState — role + muted-foreground subtitle + destructive on error.
// ---------------------------------------------------------------------------

describe('EmptyState + ErrorState design tokens', () => {
  it('EmptyState has role="status" and dashed border', () => {
    render(<EmptyState title="No rows" subtitle="Try another filter" />);
    const state = screen.getByRole('status');
    expect(state.className).toContain('border-dashed');
    expect(state.className).toContain('bg-muted/10');
  });

  it('ErrorState uses destructive colour tokens', () => {
    render(<ErrorState error={new Error('boom')} />);
    const state = screen.getByRole('alert');
    expect(state.className).toContain('border-destructive');
    expect(state.className).toContain('bg-destructive/5');
  });
});

// ---------------------------------------------------------------------------
// DataTable — numeric columns get tabular-nums + text-right.
// ---------------------------------------------------------------------------

interface Row {
  id: string;
  name: string;
  amount: number;
}

const rows: Row[] = [{ id: 'r1', name: 'Alice', amount: 100 }];

const columns: Array<Column<Row>> = [
  { key: 'name', header: 'Name' },
  { key: 'amount', header: 'Amount', align: 'right' },
];

describe('DataTable design tokens', () => {
  it('right-aligned numeric cells include tabular-nums', () => {
    const { container } = render(
      <DataTable data={rows} columns={columns} getRowId={(r) => r.id} />,
    );
    // The second cell in the first data row is the Amount cell.
    const cells = container.querySelectorAll('tbody tr:first-child td');
    expect(cells.length).toBe(2);
    const amountCell = cells[1] as HTMLTableCellElement;
    expect(amountCell.className).toContain('text-right');
    expect(amountCell.className).toContain('tabular-nums');
  });

  it('right-aligned header also uses text-right', () => {
    const { container } = render(
      <DataTable data={rows} columns={columns} getRowId={(r) => r.id} />,
    );
    const headers = container.querySelectorAll('thead th');
    const amountHeader = headers[1] as HTMLTableCellElement;
    expect(amountHeader.className).toContain('text-right');
  });

  it('table is wrapped in a rounded bordered card', () => {
    const { container } = render(
      <DataTable data={rows} columns={columns} getRowId={(r) => r.id} />,
    );
    const outer = container.firstElementChild;
    expect(outer?.className).toContain('rounded-lg');
    expect(outer?.className).toContain('border');
    expect(outer?.className).toContain('bg-background');
  });
});
