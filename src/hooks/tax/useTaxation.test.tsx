import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  useCreateGSTRate,
  useGenerateTDSReturnFile,
  useGSTRegistrations,
  useGSTRates,
  useTDSCertificates,
  useTDSEntries,
  useTDSSections,
} from './useTaxation';

import {
  gstRatesApi,
  gstRegistrationsApi,
  tdsEntriesApi,
  tdsForm16AApi,
  tdsReturnsApi,
  tdsSectionsApi,
} from '@/services/api';

vi.mock('@/services/api', () => ({
  organizationsApi: { list: vi.fn() },
  unitsApi: { list: vi.fn() },
  financialYearsApi: { list: vi.fn() },
  gstRatesApi: { list: vi.fn(), get: vi.fn(), create: vi.fn(), update: vi.fn(), delete: vi.fn() },
  gstRegistrationsApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
  hsnSacApi: { list: vi.fn(), get: vi.fn(), create: vi.fn(), update: vi.fn(), delete: vi.fn() },
  tdsSectionsApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
  tdsEntriesApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    validateThreshold: vi.fn(),
    getPendingChallans: vi.fn(),
    getByQuarter: vi.fn(),
    updateChallan: vi.fn(),
  },
  tdsReturnsApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    validate: vi.fn(),
    generateFile: vi.fn(),
    updateFilingDetails: vi.fn(),
    revise: vi.fn(),
    getPending: vi.fn(),
    getDue: vi.fn(),
  },
  tdsChallansApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    generate: vi.fn(),
    addEntries: vi.fn(),
    removeEntries: vi.fn(),
    finalize: vi.fn(),
    recordPayment: vi.fn(),
    verifyOltas: vi.fn(),
    cancel: vi.fn(),
    getSummary: vi.fn(),
    getDue: vi.fn(),
  },
  tdsForm16AApi: {
    listCertificates: vi.fn(),
    getDeductees: vi.fn(),
    generate: vi.fn(),
    generateBulk: vi.fn(),
    get: vi.fn(),
    download: vi.fn(),
  },
}));

function wrapper({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

describe('tax hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('normalizes GST rate API data into camelCase frontend fields', async () => {
    vi.mocked(gstRatesApi.list).mockResolvedValueOnce({
      data: {
        items: [
          {
            id: 'rate-1',
            code: 'GST18',
            name: 'GST 18%',
            rate: 18,
            cgstRate: 9,
            sgstRate: 9,
            igstRate: 18,
            cessRate: 0,
            effectiveFrom: '2026-04-01',
            isActive: true,
          },
        ],
        total: 1,
        page: 1,
        pageSize: 50,
        totalPages: 1,
      },
    } as any);

    const { result } = renderHook(() => useGSTRates({ pageSize: 50 }), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.items[0]).toMatchObject({
      code: 'GST18',
      cgstRate: 9,
      effectiveFrom: '2026-04-01',
      isActive: true,
    });
  });

  it('sends GST rate mutations using the backend tax contract', async () => {
    vi.mocked(gstRatesApi.create).mockResolvedValueOnce({ data: {} } as any);
    const { result } = renderHook(() => useCreateGSTRate(), { wrapper });

    await result.current.mutateAsync({
      code: 'GST5',
      name: 'GST 5%',
      rate: 5,
      cgstRate: 2.5,
      sgstRate: 2.5,
      igstRate: 5,
      cessRate: 0,
      effectiveFrom: '2026-04-01',
      isActive: true,
    });

    expect(gstRatesApi.create).toHaveBeenCalledWith(
      expect.objectContaining({
        cgstRate: 2.5,
        sgstRate: 2.5,
        effectiveFrom: '2026-04-01',
        isActive: true,
      }),
    );
  });

  it('normalizes GST registrations from camelCase responses', async () => {
    vi.mocked(gstRegistrationsApi.list).mockResolvedValueOnce({
      data: {
        items: [
          {
            id: 'gst-reg-1',
            gstin: '27ABCDE1234F1Z5',
            legalName: 'Acme Finance Limited',
            stateCode: '27',
            stateName: 'Maharashtra',
            registrationType: 'REGULAR',
            isActive: true,
            isEInvoiceEnabled: true,
            isEWayBillEnabled: false,
          },
        ],
      },
    } as any);

    const { result } = renderHook(() => useGSTRegistrations(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.items[0]).toMatchObject({
      legalName: 'Acme Finance Limited',
      stateCode: '27',
      isEInvoiceEnabled: true,
    });
  });

  it('normalizes TDS/TCS sections and passes return form filters', async () => {
    vi.mocked(tdsSectionsApi.list).mockResolvedValueOnce({
      data: {
        items: [
          {
            id: 'sec-1',
            sectionCode: '194A',
            sectionName: 'Interest',
            rateIndividual: 10,
            rateCompany: 10,
            rateNoPan: 20,
            thresholdSingle: 5000,
            thresholdAnnual: 40000,
            isTcs: false,
            surchargeApplicable: false,
            cessRate: 0,
            effectiveFrom: '2026-04-01',
            returnForm: '26Q',
            isActive: true,
          },
        ],
      },
    } as any);

    const { result } = renderHook(() => useTDSSections({ returnForm: '26Q' }), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(tdsSectionsApi.list).toHaveBeenCalledWith(
      expect.objectContaining({ returnForm: '26Q' }),
    );
    expect(result.current.data?.items[0]).toMatchObject({
      sectionCode: '194A',
      thresholdAnnual: 40000,
      returnForm: '26Q',
    });
  });

  it('normalizes TDS entries for workflow screens', async () => {
    vi.mocked(tdsEntriesApi.list).mockResolvedValueOnce({
      data: {
        items: [
          {
            id: 'entry-1',
            tdsSectionId: 'sec-1',
            deducteeName: 'Vendor One',
            deducteePan: 'ABCDE1234F',
            deducteeType: 'COMPANY',
            deductionDate: '2026-04-10',
            baseAmount: 100000,
            tdsRate: 10,
            tdsAmount: 10000,
            surcharge: 0,
            cess: 0,
            totalTds: 10000,
            isThresholdCrossed: true,
            aggregateAmountYtd: 100000,
            challanStatus: 'PENDING',
            returnFiled: false,
            isActive: true,
          },
        ],
      },
    } as any);

    const { result } = renderHook(() => useTDSEntries({}), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.items[0]).toMatchObject({
      deducteeName: 'Vendor One',
      totalTds: 10000,
      challanStatus: 'PENDING',
    });
  });

  it('maps TDS return file generation metadata from camelCase responses', async () => {
    vi.mocked(tdsReturnsApi.generateFile).mockResolvedValueOnce({
      data: {
        fileName: '26Q_202526_Q1.txt',
        fileContent: '^FH^26Q^2025-26^Q1^',
        fileSize: 19,
        fileHash: 'abc123',
        generatedAt: '2026-05-17T10:00:00Z',
        artifactStatus: 'WORKING_DRAFT',
        statutoryStatus: 'NOT_FILED',
        complianceNote: 'Working draft only',
      },
    } as any);

    const { result } = renderHook(() => useGenerateTDSReturnFile('return-1'), { wrapper });

    const file = await result.current.mutateAsync();

    expect(file).toMatchObject({
      fileName: '26Q_2025-26_Q1.txt',
      artifactStatus: 'WORKING_DRAFT',
      statutoryStatus: 'NOT_FILED',
      complianceNote: 'Working draft only',
    });
  });

  it('maps certificate legal-status metadata for UI tracking', async () => {
    vi.mocked(tdsForm16AApi.listCertificates).mockResolvedValueOnce({
      data: [
        {
          certificate_number: '16A-202526-Q1-ABC123',
          deductee_name: 'Vendor One',
          deductee_pan: 'ABCDE1234F',
          tds_section_code: '194A',
          total_amount_paid: 100000,
          total_tds_deducted: 10000,
          entry_count: 2,
          artifact_status: 'GENERATED_SUMMARY',
          legal_status: 'NOT_TRACES_ISSUED',
          source: 'SYSTEM_GENERATED_SUMMARY',
          compliance_note: 'Use TRACES-issued Form 16A as the legal certificate.',
        },
      ],
    } as any);

    const { result } = renderHook(() => useTDSCertificates('2025-26', 'Q1'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.[0]).toMatchObject({
      certificateNumber: '16A-202526-Q1-ABC123',
      artifactStatus: 'GENERATED_SUMMARY',
      legalStatus: 'NOT_TRACES_ISSUED',
      source: 'SYSTEM_GENERATED_SUMMARY',
    });
  });
});
