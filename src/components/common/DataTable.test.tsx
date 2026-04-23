import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { DataTable, type Column } from './DataTable';

interface Row {
  id: string;
  name: string;
  amount: number;
}

const rows: Row[] = [
  { id: 'r1', name: 'Bob', amount: 300 },
  { id: 'r2', name: 'Alice', amount: 100 },
  { id: 'r3', name: 'Carol', amount: 200 },
];

const columns: Array<Column<Row>> = [
  { key: 'name', header: 'Name', sortable: true },
  { key: 'amount', header: 'Amount', align: 'right', sortable: true },
];

describe('DataTable', () => {
  it('renders rows when data is provided', () => {
    render(<DataTable data={rows} columns={columns} getRowId={(r) => r.id} />);
    expect(screen.getAllByRole('row')).toHaveLength(rows.length + 1); // + header
    expect(screen.getByText('Alice')).toBeInTheDocument();
  });

  it('renders SkeletonTable while loading', () => {
    render(<DataTable data={[]} columns={columns} getRowId={(r) => r.id} isLoading />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders EmptyState when data is empty', () => {
    render(<DataTable data={[]} columns={columns} getRowId={(r) => r.id} />);
    expect(screen.getByText(/no results/i)).toBeInTheDocument();
  });

  it('renders ErrorState on error and allows retry', async () => {
    const onRetry = vi.fn();
    render(
      <DataTable
        data={[]}
        columns={columns}
        getRowId={(r) => r.id}
        error={new Error('boom')}
        onRetry={onRetry}
      />,
    );
    const retry = screen.getByRole('button', { name: /retry/i });
    await userEvent.click(retry);
    expect(onRetry).toHaveBeenCalled();
  });

  it('sorts ascending and toggles to descending on second click', async () => {
    render(<DataTable data={rows} columns={columns} getRowId={(r) => r.id} />);
    const nameHeader = screen.getByRole('columnheader', { name: /name/i });
    await userEvent.click(nameHeader);

    let nameCells = screen.getAllByRole('row').slice(1).map((r) => r.children[0]?.textContent);
    expect(nameCells).toEqual(['Alice', 'Bob', 'Carol']);

    await userEvent.click(nameHeader);
    nameCells = screen.getAllByRole('row').slice(1).map((r) => r.children[0]?.textContent);
    expect(nameCells).toEqual(['Carol', 'Bob', 'Alice']);
  });

  it('invokes onRowClick with the clicked row', async () => {
    const onRowClick = vi.fn();
    render(
      <DataTable data={rows} columns={columns} getRowId={(r) => r.id} onRowClick={onRowClick} />,
    );
    await userEvent.click(screen.getByText('Alice'));
    expect(onRowClick).toHaveBeenCalledWith(rows[1]);
  });
});
