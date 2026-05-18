import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { ErrorState } from './ErrorState';

describe('ErrorState', () => {
  it('shows a default title and retry button', async () => {
    const onRetry = vi.fn();
    render(<ErrorState onRetry={onRetry} />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText(/unable to load data/i)).toBeInTheDocument();
    const btn = screen.getByRole('button', { name: /retry/i });
    await userEvent.click(btn);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('extracts message + code from an axios-style error', () => {
    const err = {
      isAxiosError: true,
      message: 'Request failed',
      response: {
        status: 409,
        data: {
          error_code: 'CONCURRENCY_CONFLICT',
          message: 'Row modified by another user',
          correlation_id: 'abc-123',
        },
      },
    };
    render(<ErrorState error={err} />);
    expect(screen.getByText(/Row modified by another user/)).toBeInTheDocument();
    expect(screen.getByText(/CONCURRENCY_CONFLICT/)).toBeInTheDocument();
    expect(screen.getByText(/abc-123/)).toBeInTheDocument();
  });

  it('handles plain Error objects', () => {
    render(<ErrorState error={new Error('boom')} />);
    expect(screen.getByText('boom')).toBeInTheDocument();
  });

  it('renders FastAPI validation errors as text', () => {
    const err = {
      isAxiosError: true,
      message: 'Request failed',
      response: {
        status: 422,
        data: {
          detail: [
            {
              loc: ['path', 'id'],
              msg: 'Input should be a valid UUID',
            },
          ],
        },
      },
    };

    render(<ErrorState error={err} />);
    expect(screen.getByText(/path.id: Input should be a valid UUID/)).toBeInTheDocument();
  });
});
