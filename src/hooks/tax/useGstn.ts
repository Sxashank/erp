import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { isAxiosError } from 'axios';

import { gstnApi } from '@/services/api';

type ApiRecord = Record<string, unknown>;

function asRecord(value: unknown): ApiRecord {
  return value && typeof value === 'object' ? (value as ApiRecord) : {};
}

function readString(record: ApiRecord, ...keys: string[]): string | undefined {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === 'string' && value.trim().length > 0) {
      return value;
    }
  }
  return undefined;
}

function readNumber(record: ApiRecord, ...keys: string[]): number {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === 'number' && Number.isFinite(value)) {
      return value;
    }
    if (typeof value === 'string' && value.trim().length > 0) {
      const parsed = Number(value);
      if (!Number.isNaN(parsed)) {
        return parsed;
      }
    }
  }
  return 0;
}

function readBoolean(record: ApiRecord, ...keys: string[]): boolean {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === 'boolean') {
      return value;
    }
  }
  return false;
}

function readArray(record: ApiRecord, ...keys: string[]): unknown[] {
  for (const key of keys) {
    const value = record[key];
    if (Array.isArray(value)) {
      return value;
    }
  }
  return [];
}

function isNotFoundError(error: unknown): boolean {
  return isAxiosError(error) && error.response?.status === 404;
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (!isAxiosError(error)) {
    return fallback;
  }

  const detail = asRecord(error.response?.data).detail;
  return typeof detail === 'string' && detail.trim().length > 0 ? detail : fallback;
}

export interface GstnSessionStatus {
  isAuthenticated: boolean;
  gstin: string;
  expiresAt?: string;
}

export interface GstnStats {
  gstin: string;
  returnPeriod?: string;
  pendingFilings: number;
  submittedFilings: number;
  filedFilings: number;
  itcMismatches: number;
}

export interface GstnTaxSummary {
  taxableValue: number;
  igstAmount: number;
  cgstAmount: number;
  sgstAmount: number;
  cessAmount: number;
}

export interface Gstr1Data {
  status: string;
  filingId?: string;
  b2bInvoices: unknown[];
  b2bSummary: GstnTaxSummary;
  b2clInvoices: unknown[];
  b2clSummary: GstnTaxSummary;
  b2csInvoices: unknown[];
  b2csCount: number;
  b2csSummary: GstnTaxSummary;
  cdnrInvoices: unknown[];
  cdnrCount: number;
  cdnrSummary: GstnTaxSummary;
  expInvoices: unknown[];
  exportsCount: number;
  expSummary: GstnTaxSummary;
  hsnSummary: unknown[];
}

export interface Gstr3bBucket {
  taxableValue?: number;
  igst: number;
  cgst: number;
  sgst: number;
  cess: number;
}

export interface Gstr3bData {
  status: string;
  filingId?: string;
  outwardTaxableSupplies?: Gstr3bBucket;
  outwardTaxableZeroRated?: Gstr3bBucket;
  otherOutwardSupplies?: {
    nilRated: number;
    exempt: number;
    nonGst: number;
  };
  inwardReverseCharge?: Gstr3bBucket;
  eligibleItc?: {
    total: Gstr3bBucket;
    importOfGoods: Gstr3bBucket;
    importOfServices: Gstr3bBucket;
    inwardReverseCharge: Gstr3bBucket;
    allOtherItc: Gstr3bBucket;
  };
  ineligibleItc?: Gstr3bBucket;
  netItc?: Gstr3bBucket;
  taxPayable?: Gstr3bBucket;
  interestLateFee?: {
    igst: number;
    cgst: number;
    sgst: number;
    cess: number;
    interest: number;
    lateFee: number;
  };
}

export interface Gstr2bFetchResult {
  gstin: string;
  returnPeriod: string;
  status: string;
  total: number;
}

export interface ItcMismatch {
  id: string;
  supplierGstin: string;
  supplierName: string;
  invoiceNumber: string;
  invoiceDate?: string;
  bookTaxableValue: number;
  bookIgst: number;
  bookCgst: number;
  bookSgst: number;
  gstr2bTaxableValue: number;
  gstr2bIgst: number;
  gstr2bCgst: number;
  gstr2bSgst: number;
  varianceAmount: number;
  mismatchType: string;
  resolutionStatus: string;
  resolutionNotes?: string;
}

export interface ItcMismatchList {
  items: ItcMismatch[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface ManualReconciliationResult {
  gstin: string;
  returnPeriod: string;
  status: string;
  totalBookValue: number;
  totalGstr2bValue: number;
  matchedCount: number;
  mismatchCount: number;
}

export interface ResolveItcMismatchInput {
  resolutionStatus: string;
  resolutionNotes?: string;
}

function normalizeTaxSummary(value: unknown): GstnTaxSummary {
  const record = asRecord(value);
  return {
    taxableValue: readNumber(record, 'taxableValue', 'taxable_value', 'total_taxable_value'),
    igstAmount: readNumber(record, 'igstAmount', 'igst_amount', 'igst'),
    cgstAmount: readNumber(record, 'cgstAmount', 'cgst_amount', 'cgst'),
    sgstAmount: readNumber(record, 'sgstAmount', 'sgst_amount', 'sgst'),
    cessAmount: readNumber(record, 'cessAmount', 'cess_amount', 'cess'),
  };
}

function normalizeBucket(value: unknown): Gstr3bBucket {
  const record = asRecord(value);
  return {
    taxableValue: readNumber(record, 'taxableValue', 'taxable_value', 'total_taxable_value', 'txval'),
    igst: readNumber(record, 'igst'),
    cgst: readNumber(record, 'cgst'),
    sgst: readNumber(record, 'sgst'),
    cess: readNumber(record, 'cess'),
  };
}

function normalizeSessionStatus(value: unknown, gstin: string): GstnSessionStatus {
  const record = asRecord(value);
  return {
    isAuthenticated: readBoolean(record, 'isAuthenticated', 'is_authenticated'),
    gstin: readString(record, 'gstin') ?? gstin,
    expiresAt: readString(record, 'expiresAt', 'expires_at'),
  };
}

function normalizeStats(value: unknown): GstnStats {
  const record = asRecord(value);
  return {
    gstin: readString(record, 'gstin') ?? '',
    returnPeriod: readString(record, 'returnPeriod', 'return_period'),
    pendingFilings: readNumber(record, 'pendingFilings', 'pending_filings'),
    submittedFilings: readNumber(record, 'submittedFilings', 'submitted_filings'),
    filedFilings: readNumber(record, 'filedFilings', 'filed_filings'),
    itcMismatches: readNumber(record, 'itcMismatches', 'itc_mismatches'),
  };
}

function normalizeGstr1(value: unknown): Gstr1Data {
  const record = asRecord(value);
  return {
    status: readString(record, 'status') ?? 'NOT_GENERATED',
    filingId: readString(record, 'filingId', 'filing_id'),
    b2bInvoices: readArray(record, 'b2bInvoices', 'b2b_invoices'),
    b2bSummary: normalizeTaxSummary(record.b2bSummary ?? record.b2b_summary),
    b2clInvoices: readArray(record, 'b2clInvoices', 'b2cl_invoices'),
    b2clSummary: normalizeTaxSummary(record.b2clSummary ?? record.b2cl_summary),
    b2csInvoices: readArray(record, 'b2csInvoices', 'b2cs_invoices'),
    b2csCount: readNumber(record, 'b2csCount', 'b2cs_count'),
    b2csSummary: normalizeTaxSummary(record.b2csSummary ?? record.b2cs_summary),
    cdnrInvoices: readArray(record, 'cdnrInvoices', 'cdnr_invoices'),
    cdnrCount: readNumber(record, 'cdnrCount', 'cdnr_count'),
    cdnrSummary: normalizeTaxSummary(record.cdnrSummary ?? record.cdnr_summary),
    expInvoices: readArray(record, 'expInvoices', 'exp_invoices'),
    exportsCount: readNumber(record, 'exportsCount', 'exports_count'),
    expSummary: normalizeTaxSummary(record.expSummary ?? record.exp_summary ?? record.exports_summary),
    hsnSummary: readArray(record, 'hsnSummary', 'hsn_summary'),
  };
}

function normalizeGstr3b(value: unknown): Gstr3bData {
  const record = asRecord(value);
  const otherOutward = asRecord(record.otherOutwardSupplies ?? record.other_outward_supplies);
  const interestLateFee = asRecord(record.interestLateFee ?? record.interest_late_fee);

  return {
    status: readString(record, 'status') ?? 'NOT_GENERATED',
    filingId: readString(record, 'filingId', 'filing_id'),
    outwardTaxableSupplies: normalizeBucket(record.outwardTaxableSupplies ?? record.outward_taxable_supplies),
    outwardTaxableZeroRated: normalizeBucket(record.outwardTaxableZeroRated ?? record.outward_taxable_zero_rated),
    otherOutwardSupplies: {
      nilRated: readNumber(otherOutward, 'nilRated', 'nil_rated'),
      exempt: readNumber(otherOutward, 'exempt'),
      nonGst: readNumber(otherOutward, 'nonGst', 'non_gst'),
    },
    inwardReverseCharge: normalizeBucket(record.inwardReverseCharge ?? record.inward_reverse_charge),
    eligibleItc: {
      total: normalizeBucket(asRecord(record.eligibleItc ?? record.eligible_itc).total),
      importOfGoods: normalizeBucket(asRecord(record.eligibleItc ?? record.eligible_itc).importOfGoods ?? asRecord(record.eligibleItc ?? record.eligible_itc).import_of_goods),
      importOfServices: normalizeBucket(asRecord(record.eligibleItc ?? record.eligible_itc).importOfServices ?? asRecord(record.eligibleItc ?? record.eligible_itc).import_of_services),
      inwardReverseCharge: normalizeBucket(asRecord(record.eligibleItc ?? record.eligible_itc).inwardReverseCharge ?? asRecord(record.eligibleItc ?? record.eligible_itc).inward_reverse_charge),
      allOtherItc: normalizeBucket(asRecord(record.eligibleItc ?? record.eligible_itc).allOtherItc ?? asRecord(record.eligibleItc ?? record.eligible_itc).all_other_itc),
    },
    ineligibleItc: normalizeBucket(record.ineligibleItc ?? record.ineligible_itc),
    netItc: normalizeBucket(record.netItc ?? record.net_itc),
    taxPayable: normalizeBucket(record.taxPayable ?? record.tax_payable),
    interestLateFee: {
      igst: readNumber(interestLateFee, 'igst'),
      cgst: readNumber(interestLateFee, 'cgst'),
      sgst: readNumber(interestLateFee, 'sgst'),
      cess: readNumber(interestLateFee, 'cess'),
      interest: readNumber(interestLateFee, 'interest'),
      lateFee: readNumber(interestLateFee, 'lateFee', 'late_fee'),
    },
  };
}

function normalizeGstr2bFetch(value: unknown): Gstr2bFetchResult {
  const record = asRecord(value);
  return {
    gstin: readString(record, 'gstin') ?? '',
    returnPeriod: readString(record, 'returnPeriod', 'return_period') ?? '',
    status: readString(record, 'status') ?? 'FETCHED',
    total: readNumber(record, 'total'),
  };
}

function normalizeMismatch(value: unknown): ItcMismatch {
  const record = asRecord(value);
  return {
    id: readString(record, 'id') ?? '',
    supplierGstin: readString(record, 'supplierGstin', 'supplier_gstin') ?? '',
    supplierName: readString(record, 'supplierName', 'supplier_name') ?? '',
    invoiceNumber: readString(record, 'invoiceNumber', 'invoice_number') ?? '',
    invoiceDate: readString(record, 'invoiceDate', 'invoice_date'),
    bookTaxableValue: readNumber(record, 'bookTaxableValue', 'book_taxable_value'),
    bookIgst: readNumber(record, 'bookIgst', 'book_igst'),
    bookCgst: readNumber(record, 'bookCgst', 'book_cgst'),
    bookSgst: readNumber(record, 'bookSgst', 'book_sgst'),
    gstr2bTaxableValue: readNumber(record, 'gstr2bTaxableValue', 'gstr2b_taxable_value'),
    gstr2bIgst: readNumber(record, 'gstr2bIgst', 'gstr2b_igst'),
    gstr2bCgst: readNumber(record, 'gstr2bCgst', 'gstr2b_cgst'),
    gstr2bSgst: readNumber(record, 'gstr2bSgst', 'gstr2b_sgst'),
    varianceAmount: readNumber(record, 'varianceAmount', 'variance_amount', 'variance_total'),
    mismatchType: readString(record, 'mismatchType', 'mismatch_type') ?? 'PENDING',
    resolutionStatus: readString(record, 'resolutionStatus', 'resolution_status') ?? 'PENDING',
    resolutionNotes: readString(record, 'resolutionNotes', 'resolution_notes'),
  };
}

function normalizeMismatchList(value: unknown): ItcMismatchList {
  const record = asRecord(value);
  const items = readArray(record, 'items').map(normalizeMismatch);
  return {
    items,
    total: readNumber(record, 'total'),
    page: readNumber(record, 'page') || 1,
    pageSize: readNumber(record, 'pageSize', 'page_size') || items.length,
    totalPages: readNumber(record, 'totalPages', 'total_pages'),
  };
}

function normalizeManualReconciliation(value: unknown): ManualReconciliationResult {
  const record = asRecord(value);
  return {
    gstin: readString(record, 'gstin') ?? '',
    returnPeriod: readString(record, 'returnPeriod', 'return_period') ?? '',
    status: readString(record, 'status') ?? 'COMPLETED',
    totalBookValue: readNumber(record, 'totalBookValue', 'total_book_value'),
    totalGstr2bValue: readNumber(record, 'totalGstr2bValue', 'total_gstr2b_value'),
    matchedCount: readNumber(record, 'matchedCount', 'matched_count'),
    mismatchCount: readNumber(record, 'mismatchCount', 'mismatch_count'),
  };
}

export function useGstnSession(gstin?: string) {
  return useQuery({
    queryKey: ['gstn-session', gstin],
    enabled: Boolean(gstin),
    retry: false,
    queryFn: async () => {
      if (!gstin) {
        return null;
      }

      try {
        const response = await gstnApi.getSession(gstin);
        return normalizeSessionStatus(response.data, gstin);
      } catch (error) {
        if (isNotFoundError(error)) {
          return normalizeSessionStatus({}, gstin);
        }
        throw error;
      }
    },
  });
}

export function useGstnStats(gstin?: string, returnPeriod?: string) {
  return useQuery({
    queryKey: ['gstn-stats', gstin, returnPeriod],
    enabled: Boolean(gstin),
    retry: false,
    queryFn: async () => {
      if (!gstin) {
        return null;
      }

      const response = await gstnApi.getStats({
        gstin,
        return_period: returnPeriod,
      });
      return normalizeStats(response.data);
    },
  });
}

export function useRequestGstnOtp() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (gstin: string) => {
      const response = await gstnApi.requestOtp({ gstin });
      return asRecord(response.data);
    },
    onSuccess: (_, gstin) => {
      queryClient.invalidateQueries({ queryKey: ['gstn-session', gstin] });
    },
  });
}

export function useVerifyGstnOtp() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ gstin, otp }: { gstin: string; otp: string }) => {
      const response = await gstnApi.verifyOtp({ gstin, otp });
      return asRecord(response.data);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['gstn-session', variables.gstin] });
    },
  });
}

export function useGstr1(gstin?: string, returnPeriod?: string) {
  return useQuery({
    queryKey: ['gstn-gstr1', gstin, returnPeriod],
    enabled: Boolean(gstin && returnPeriod),
    retry: false,
    queryFn: async () => {
      if (!gstin || !returnPeriod) {
        return null;
      }

      try {
        const response = await gstnApi.getGstr1(gstin, returnPeriod);
        return normalizeGstr1(response.data);
      } catch (error) {
        if (isNotFoundError(error)) {
          return null;
        }
        throw error;
      }
    },
  });
}

export function useGenerateGstr1(gstin?: string, returnPeriod?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ regenerate = false }: { regenerate?: boolean }) => {
      if (!gstin || !returnPeriod) {
        throw new Error('GSTIN and return period are required');
      }
      const response = await gstnApi.generateGstr1(gstin, returnPeriod, { regenerate });
      return normalizeGstr1(response.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gstn-gstr1', gstin, returnPeriod] });
      queryClient.invalidateQueries({ queryKey: ['gstn-stats', gstin] });
    },
  });
}

export function useSubmitGstr1(gstin?: string, returnPeriod?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      if (!gstin || !returnPeriod) {
        throw new Error('GSTIN and return period are required');
      }
      const response = await gstnApi.submitGstr1(gstin, returnPeriod);
      return normalizeGstr1(response.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gstn-gstr1', gstin, returnPeriod] });
      queryClient.invalidateQueries({ queryKey: ['gstn-stats', gstin] });
    },
  });
}

export function useFileGstr1(gstin?: string, returnPeriod?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: { pan: string; otp: string }) => {
      if (!gstin || !returnPeriod) {
        throw new Error('GSTIN and return period are required');
      }
      const response = await gstnApi.fileGstr1(gstin, returnPeriod, input);
      return normalizeGstr1(response.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gstn-gstr1', gstin, returnPeriod] });
      queryClient.invalidateQueries({ queryKey: ['gstn-stats', gstin] });
    },
  });
}

export function useGstr3b(gstin?: string, returnPeriod?: string) {
  return useQuery({
    queryKey: ['gstn-gstr3b', gstin, returnPeriod],
    enabled: Boolean(gstin && returnPeriod),
    retry: false,
    queryFn: async () => {
      if (!gstin || !returnPeriod) {
        return null;
      }

      try {
        const response = await gstnApi.getGstr3b(gstin, returnPeriod);
        return normalizeGstr3b(response.data);
      } catch (error) {
        if (isNotFoundError(error)) {
          return null;
        }
        throw error;
      }
    },
  });
}

export function useGenerateGstr3b(gstin?: string, returnPeriod?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ regenerate = false }: { regenerate?: boolean }) => {
      if (!gstin || !returnPeriod) {
        throw new Error('GSTIN and return period are required');
      }
      const response = await gstnApi.generateGstr3b(gstin, returnPeriod, { regenerate });
      return normalizeGstr3b(response.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gstn-gstr3b', gstin, returnPeriod] });
      queryClient.invalidateQueries({ queryKey: ['gstn-stats', gstin] });
    },
  });
}

export function useSubmitGstr3b(gstin?: string, returnPeriod?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      if (!gstin || !returnPeriod) {
        throw new Error('GSTIN and return period are required');
      }
      const response = await gstnApi.submitGstr3b(gstin, returnPeriod);
      return normalizeGstr3b(response.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gstn-gstr3b', gstin, returnPeriod] });
      queryClient.invalidateQueries({ queryKey: ['gstn-stats', gstin] });
    },
  });
}

export function useFileGstr3b(gstin?: string, returnPeriod?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: { pan: string; otp: string }) => {
      if (!gstin || !returnPeriod) {
        throw new Error('GSTIN and return period are required');
      }
      const response = await gstnApi.fileGstr3b(gstin, returnPeriod, input);
      return normalizeGstr3b(response.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gstn-gstr3b', gstin, returnPeriod] });
      queryClient.invalidateQueries({ queryKey: ['gstn-stats', gstin] });
    },
  });
}

export function useFetchGstr2b(gstin?: string, returnPeriod?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      if (!gstin || !returnPeriod) {
        throw new Error('GSTIN and return period are required');
      }
      const response = await gstnApi.fetchGstr2b(gstin, returnPeriod);
      return normalizeGstr2bFetch(response.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gstn-itc-mismatches', gstin, returnPeriod] });
      queryClient.invalidateQueries({ queryKey: ['gstn-stats', gstin] });
    },
  });
}

export function useItcMismatches(params: {
  gstin?: string;
  returnPeriod?: string;
  mismatchType?: string;
  resolutionStatus?: string;
  page?: number;
  pageSize?: number;
}) {
  const { gstin, returnPeriod, mismatchType, resolutionStatus, page = 1, pageSize = 20 } = params;
  return useQuery({
    queryKey: ['gstn-itc-mismatches', gstin, returnPeriod, mismatchType, resolutionStatus, page, pageSize],
    enabled: Boolean(gstin && returnPeriod),
    retry: false,
    queryFn: async () => {
      if (!gstin || !returnPeriod) {
        return { items: [], total: 0, page, pageSize, totalPages: 0 };
      }

      try {
        const response = await gstnApi.getMismatches({
          gstin,
          return_period: returnPeriod,
          mismatch_type: mismatchType,
          resolution_status: resolutionStatus,
          page,
          page_size: pageSize,
        });
        return normalizeMismatchList(response.data);
      } catch (error) {
        if (isNotFoundError(error)) {
          return { items: [], total: 0, page, pageSize, totalPages: 0 };
        }
        throw error;
      }
    },
  });
}

export function useRunItcReconciliation(gstin?: string, returnPeriod?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      if (!gstin || !returnPeriod) {
        throw new Error('GSTIN and return period are required');
      }
      const response = await gstnApi.runReconciliation(gstin, returnPeriod);
      return normalizeManualReconciliation(response.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gstn-itc-mismatches', gstin, returnPeriod] });
      queryClient.invalidateQueries({ queryKey: ['gstn-stats', gstin] });
    },
  });
}

export function useResolveItcMismatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      mismatchId,
      input,
    }: {
      mismatchId: string;
      input: ResolveItcMismatchInput;
    }) => {
      const response = await gstnApi.resolveMismatch(mismatchId, {
        resolution_status: input.resolutionStatus,
        resolution_notes: input.resolutionNotes,
      });
      return normalizeMismatch(response.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gstn-itc-mismatches'] });
      queryClient.invalidateQueries({ queryKey: ['gstn-stats'] });
    },
  });
}
