import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useFetchGstr2b, useGstr1, useGstnSession, useItcMismatches } from './useGstn';

import { gstnApi } from '@/services/api';

vi.mock('@/services/api', () => ({
  gstnApi: {
    requestOtp: vi.fn(),
    verifyOtp: vi.fn(),
    getSession: vi.fn(),
    getStats: vi.fn(),
    getGstr1: vi.fn(),
    generateGstr1: vi.fn(),
    submitGstr1: vi.fn(),
    fileGstr1: vi.fn(),
    getGstr3b: vi.fn(),
    generateGstr3b: vi.fn(),
    submitGstr3b: vi.fn(),
    fileGstr3b: vi.fn(),
    fetchGstr2b: vi.fn(),
    getMismatches: vi.fn(),
    runReconciliation: vi.fn(),
    resolveMismatch: vi.fn(),
  },
}));

function wrapper({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

describe('useGstn', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns a disconnected session state for 404 responses', async () => {
    vi.mocked(gstnApi.getSession).mockRejectedValueOnce({
      isAxiosError: true,
      response: { status: 404, data: {} },
    });

    const { result } = renderHook(() => useGstnSession('27ABCDE1234F1Z5'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual({
      isAuthenticated: false,
      gstin: '27ABCDE1234F1Z5',
      expiresAt: undefined,
    });
  });

  it('normalizes GSTR-1 payloads into camelCase frontend fields', async () => {
    vi.mocked(gstnApi.getGstr1).mockResolvedValueOnce({
      data: {
        status: 'GENERATED',
        b2b_invoices: [{ id: '1' }],
        b2b_summary: { taxable_value: 1000, igst_amount: 180, cgst_amount: 0, sgst_amount: 0, cess_amount: 0 },
        b2cl_invoices: [],
        b2cl_summary: { taxable_value: 0, igst_amount: 0, cgst_amount: 0, sgst_amount: 0, cess_amount: 0 },
        b2cs_count: 2,
        b2cs_summary: { taxable_value: 500, igst_amount: 0, cgst_amount: 45, sgst_amount: 45, cess_amount: 0 },
        cdnr_count: 1,
        cdnr_summary: { taxable_value: 100, igst_amount: 18, cgst_amount: 0, sgst_amount: 0, cess_amount: 0 },
        exp_invoices: [],
        exp_summary: { taxable_value: 0, igst_amount: 0, cgst_amount: 0, sgst_amount: 0, cess_amount: 0 },
      },
    } as never);

    const { result } = renderHook(() => useGstr1('27ABCDE1234F1Z5', '042026'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toMatchObject({
      status: 'GENERATED',
      b2bInvoices: [{ id: '1' }],
      b2csCount: 2,
      b2csSummary: { cgstAmount: 45, sgstAmount: 45 },
      cdnrCount: 1,
    });
  });

  it('normalizes mismatch lists and sends ITC filter params', async () => {
    vi.mocked(gstnApi.getMismatches).mockResolvedValueOnce({
      data: {
        items: [
          {
            id: 'mm-1',
            supplier_gstin: '27ABCDE1234F1Z5',
            supplier_name: 'Vendor One',
            invoice_number: 'INV-001',
            invoice_date: '2026-04-10',
            book_taxable_value: 1000,
            gstr2b_taxable_value: 900,
            variance_amount: 100,
            mismatch_type: 'AMOUNT_MISMATCH',
            resolution_status: 'PENDING',
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      },
    } as never);

    const { result } = renderHook(
      () =>
        useItcMismatches({
          gstin: '27ABCDE1234F1Z5',
          returnPeriod: '042026',
          mismatchType: 'AMOUNT_MISMATCH',
          resolutionStatus: 'PENDING',
        }),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(gstnApi.getMismatches).toHaveBeenCalledWith(
      expect.objectContaining({
        gstin: '27ABCDE1234F1Z5',
        return_period: '042026',
        mismatch_type: 'AMOUNT_MISMATCH',
        resolution_status: 'PENDING',
      }),
    );
    expect(result.current.data?.items[0]).toMatchObject({
      supplierGstin: '27ABCDE1234F1Z5',
      invoiceNumber: 'INV-001',
      varianceAmount: 100,
      mismatchType: 'AMOUNT_MISMATCH',
    });
  });

  it('fetches GSTR-2B with the selected GSTIN and period', async () => {
    vi.mocked(gstnApi.fetchGstr2b).mockResolvedValueOnce({
      data: {
        gstin: '27ABCDE1234F1Z5',
        return_period: '042026',
        status: 'FETCHED',
        total: 42,
      },
    } as never);

    const { result } = renderHook(() => useFetchGstr2b('27ABCDE1234F1Z5', '042026'), { wrapper });

    await result.current.mutateAsync();

    expect(gstnApi.fetchGstr2b).toHaveBeenCalledWith('27ABCDE1234F1Z5', '042026');
  });
});
