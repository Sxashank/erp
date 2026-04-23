/**
 * Integration test: finance hooks go through MSW (Stage 3e).
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import type { ReactNode } from 'react';

import { useAccounts, usePeriods } from './useAccounts';
import { server } from '@/test/msw/server';

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('useAccounts (integration)', () => {
  it('fetches accounts for the active org', async () => {
    const { result } = renderHook(() => useAccounts(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(4);
    expect(result.current.data?.[0]?.code).toBe('1001');
  });

  it('surfaces server errors', async () => {
    server.use(
      http.get('http://localhost:8001/api/v1/accounts', () =>
        HttpResponse.json(
          { error_code: 'DB_DOWN', message: 'Database temporarily unavailable' },
          { status: 503 },
        ),
      ),
    );
    const { result } = renderHook(() => useAccounts(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('usePeriods (integration)', () => {
  it('flattens periods from financial years', async () => {
    const { result } = renderHook(() => usePeriods(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(2);
    expect(result.current.data?.[0]?.status).toBe('OPEN');
  });
});
