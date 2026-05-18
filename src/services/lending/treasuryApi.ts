/**
 * Treasury API Service
 * API calls for Treasury, Borrowings, and ALM management
 */

import api from '../api';

import type { LenderListItem, ALMPosition, PaginatedResponse } from '@/types/lending';

const BASE_URL = '/lending/treasury';

// ============== Lenders ==============

export interface LenderFilters {
  search?: string;
  lenderType?: string;
  status?: string;
  page?: number;
  pageSize?: number;
}

export interface LenderDetail {
  lenderId: string;
  organizationId: string;
  lenderCode: string;
  lenderName: string;
  lenderType: string;
  pan: string | null;
  cin: string | null;
  gstin: string | null;
  rbiRegistration: string | null;
  registeredAddress: string | null;
  contactPerson: string | null;
  contactEmail: string | null;
  contactPhone: string | null;
  bankName: string | null;
  bankBranch: string | null;
  bankAccountNumber: string | null;
  bankIfsc: string | null;
  externalRating: string | null;
  ratingAgency: string | null;
  ratingDate: string | null;
  totalSanctionLimit: string | null;
  availableLimit: string | null;
  status: string;
  remarks: string | null;
  createdAt: string;
  updatedAt: string;
}

export async function getLenders(
  filters?: LenderFilters,
): Promise<PaginatedResponse<LenderListItem>> {
  const params = new URLSearchParams();

  if (filters?.search) params.append('search', filters.search);
  if (filters?.lenderType) params.append('lender_type', filters.lenderType);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.page) params.append('page', filters.page.toString());
  if (filters?.pageSize) params.append('page_size', filters.pageSize.toString());

  const response = await api.get<PaginatedResponse<LenderListItem>>(
    `${BASE_URL}/lenders?${params.toString()}`,
  );
  return response.data;
}

export async function getLender(lenderId: string): Promise<LenderDetail> {
  const response = await api.get<LenderDetail>(`${BASE_URL}/lenders/${lenderId}`);
  return response.data;
}

export interface CreateLenderRequest {
  lenderName: string;
  lenderType: string;
  pan?: string;
  cin?: string;
  gstin?: string;
  rbiRegistration?: string;
  registeredAddress?: string;
  contactPerson?: string;
  contactEmail?: string;
  contactPhone?: string;
  bankName?: string;
  bankBranch?: string;
  bankAccountNumber?: string;
  bankIfsc?: string;
  externalRating?: string;
  ratingAgency?: string;
  ratingDate?: string;
  totalSanctionLimit?: number;
  remarks?: string;
}

export async function createLender(data: CreateLenderRequest): Promise<LenderDetail> {
  const response = await api.post<LenderDetail>(`${BASE_URL}/lenders`, data);
  return response.data;
}

export async function updateLender(
  lenderId: string,
  data: Partial<CreateLenderRequest>,
): Promise<LenderDetail> {
  const response = await api.put<LenderDetail>(`${BASE_URL}/lenders/${lenderId}`, data);
  return response.data;
}

export async function deleteLender(lenderId: string): Promise<void> {
  await api.delete(`${BASE_URL}/lenders/${lenderId}`);
}

// ============== Borrowings ==============

export interface BorrowingFilters {
  search?: string;
  lenderId?: string;
  borrowingType?: string;
  status?: string;
  dateFrom?: string;
  dateTo?: string;
  page?: number;
  pageSize?: number;
}

export interface BorrowingListItem {
  id: string;
  borrowingNumber: string;
  borrowingType: string;
  lenderId: string;
  lenderName: string | null;
  lenderCode: string | null;
  sanctionDate: string;
  sanctionedAmount: string;
  drawnAmount: string;
  availableAmount: string;
  principalOutstanding: string;
  effectiveRate: string;
  rateType: string;
  tenureMonths: number;
  maturityDate: string;
  securityType: string;
  currency: string;
  status: string;
}

export async function getBorrowings(
  filters?: BorrowingFilters,
): Promise<PaginatedResponse<BorrowingListItem>> {
  const params = new URLSearchParams();

  if (filters?.search) params.append('search', filters.search);
  if (filters?.lenderId) params.append('lender_id', filters.lenderId);
  if (filters?.borrowingType) params.append('borrowing_type', filters.borrowingType);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.dateFrom) params.append('date_from', filters.dateFrom);
  if (filters?.dateTo) params.append('date_to', filters.dateTo);
  if (filters?.page) params.append('page', filters.page.toString());
  if (filters?.pageSize) params.append('page_size', filters.pageSize.toString());

  const response = await api.get<PaginatedResponse<BorrowingListItem>>(
    `${BASE_URL}/borrowings?${params.toString()}`,
  );
  return response.data;
}

export interface BorrowingDetail {
  borrowingId: string;
  organizationId: string;
  borrowingNumber: string;
  lenderId: string;
  lenderName: string | null;
  lenderCode: string | null;
  borrowingType: string;
  sanctionDate: string;
  sanctionReference: string | null;
  sanctionedAmount: string;
  currency: string;
  rateType: string;
  baseRateName: string | null;
  baseRateValue: string | null;
  spreadBps: number;
  effectiveRate: string;
  rateResetFrequency: string | null;
  dayCountConvention: string;
  interestPaymentFrequency: string;
  principalPaymentFrequency: string;
  tenureMonths: number;
  moratoriumMonths: number;
  firstInterestDate: string | null;
  firstPrincipalDate: string | null;
  maturityDate: string;
  securityType: string;
  securityDescription: string | null;
  securityCoverRequired: string | null;
  processingFeePercent: string | null;
  commitmentFeePercent: string | null;
  prepaymentPenaltyPercent: string | null;
  financialCovenants?: Record<string, unknown> | null;
  reportingRequirements?: Record<string, unknown> | null;
  remarks: string | null;
  drawnAmount: string;
  availableAmount: string;
  principalOutstanding: string;
  nextRateResetDate: string | null;
  sanctionLetterPath: string | null;
  agreementDate: string | null;
  agreementPath: string | null;
  status: string;
  createdAt: string;
  updatedAt: string;
  tranches: BorrowingTranche[];
  schedule: BorrowingScheduleEntry[];
}

export async function getBorrowing(borrowingId: string): Promise<BorrowingDetail> {
  const response = await api.get<BorrowingDetail>(`${BASE_URL}/borrowings/${borrowingId}`);
  return response.data;
}

export interface CreateBorrowingRequest {
  lenderId: string;
  borrowingType:
    | 'TERM_LOAN'
    | 'WORKING_CAPITAL'
    | 'CASH_CREDIT'
    | 'NCD'
    | 'CP'
    | 'SUBORDINATED_DEBT'
    | 'ECB'
    | 'REFINANCE'
    | 'ICD';
  sanctionDate: string;
  sanctionReference?: string;
  sanctionedAmount: number;
  currency: string;
  rateType: 'FIXED' | 'FLOATING';
  baseRateName?: string;
  baseRateValue?: number;
  spreadBps?: number;
  effectiveRate: number;
  rateResetFrequency?: string;
  dayCountConvention: string;
  interestPaymentFrequency: string;
  principalPaymentFrequency: 'MONTHLY' | 'QUARTERLY' | 'HALF_YEARLY' | 'YEARLY' | 'BULLET';
  tenureMonths: number;
  moratoriumMonths: number;
  firstInterestDate?: string;
  firstPrincipalDate?: string;
  maturityDate: string;
  securityType: string;
  securityDescription?: string;
  securityCoverRequired?: number;
  processingFeePercent?: number;
  commitmentFeePercent?: number;
  prepaymentPenaltyPercent?: number;
  remarks?: string;
}

export async function createBorrowing(data: CreateBorrowingRequest): Promise<BorrowingDetail> {
  const response = await api.post<BorrowingDetail>(`${BASE_URL}/borrowings`, data);
  return response.data;
}

export async function updateBorrowing(
  borrowingId: string,
  data: Partial<CreateBorrowingRequest>,
): Promise<BorrowingDetail> {
  const response = await api.put<BorrowingDetail>(`${BASE_URL}/borrowings/${borrowingId}`, data);
  return response.data;
}

// ============== Borrowing Tranches/Drawdowns ==============

export interface BorrowingTranche {
  trancheId: string;
  borrowingId: string;
  trancheNumber: number;
  requestDate: string;
  requestedAmount: number | string;
  approvedAmount?: number | string | null;
  disbursementDate?: string | null;
  disbursedAmount?: number | string | null;
  principalOutstanding: number | string;
  effectiveRate?: number | string | null;
  status: string;
  remarks?: string | null;
}

export async function recordDrawdown(
  borrowingId: string,
  data: { amount: number; drawdownDate: string; interestRate?: number; remarks?: string },
): Promise<BorrowingTranche> {
  const response = await api.post<BorrowingTranche>(`${BASE_URL}/tranches`, {
    borrowingId,
    requestDate: data.drawdownDate,
    requestedAmount: data.amount,
    purpose: data.remarks,
  });
  return response.data;
}

export async function getTranches(borrowingId: string): Promise<BorrowingTranche[]> {
  const response = await api.get<PaginatedResponse<BorrowingTranche>>(
    `${BASE_URL}/borrowings/${borrowingId}/tranches`,
  );
  return response.data.items;
}

// ============== Borrowing Repayments ==============

export interface BorrowingRepayment {
  paymentId: string;
  borrowingId: string;
  trancheId?: string;
  paymentDate: string;
  paymentType: string;
  principalAmount: number | string;
  interestAmount: number | string;
  totalAmount: number | string;
  utrNumber?: string | null;
  bankReference?: string | null;
  status?: string;
  remarks?: string;
}

export async function recordRepayment(
  borrowingId: string,
  data: {
    trancheId?: string;
    paymentDate: string;
    principalAmount: number;
    interestAmount: number;
    referenceNumber?: string;
    remarks?: string;
  },
): Promise<BorrowingRepayment> {
  const response = await api.post<BorrowingRepayment>(`${BASE_URL}/payments`, {
    borrowingId,
    paymentType: 'MANUAL',
    scheduleId: data.trancheId,
    paymentDate: data.paymentDate,
    valueDate: data.paymentDate,
    principalAmount: data.principalAmount,
    interestAmount: data.interestAmount,
    paymentMode: 'BANK_TRANSFER',
    utrNumber: data.referenceNumber,
    remarks: data.remarks,
  });
  return response.data;
}

export async function getRepaymentHistory(borrowingId: string): Promise<BorrowingRepayment[]> {
  const response = await api.get<PaginatedResponse<BorrowingRepayment>>(
    `${BASE_URL}/borrowings/${borrowingId}/payments`,
  );
  return response.data.items;
}

// ============== Borrowing Schedule ==============

export interface BorrowingScheduleEntry {
  scheduleId: string;
  borrowingId: string;
  trancheId?: string;
  installmentNumber: number;
  dueDate: string;
  principalDue: number | string;
  interestDue: number | string;
  totalDue: number | string;
  principalPaid: number | string;
  interestPaid: number | string;
  totalPaid: number | string;
  openingBalance: number | string;
  closingBalance: number | string;
  status: string;
}

export async function getBorrowingSchedule(borrowingId: string): Promise<BorrowingScheduleEntry[]> {
  const response = await api.get<PaginatedResponse<BorrowingScheduleEntry>>(
    `${BASE_URL}/borrowings/${borrowingId}/schedule`,
  );
  return response.data.items;
}

export async function regenerateBorrowingSchedule(
  borrowingId: string,
): Promise<BorrowingScheduleEntry[]> {
  const response = await api.post<BorrowingScheduleEntry[]>(
    `${BASE_URL}/borrowings/${borrowingId}/schedule/regenerate`,
  );
  return response.data;
}

// ============== ALM (Asset Liability Management) ==============

export async function generateALMPosition(asOfDate?: string): Promise<ALMPosition> {
  const params = asOfDate ? `?as_of_date=${asOfDate}` : '';
  const response = await api.post<ALMPosition>(`${BASE_URL}/alm/generate${params}`);
  return response.data;
}

export async function getALMPosition(positionId: string): Promise<ALMPosition> {
  const response = await api.get<ALMPosition>(`${BASE_URL}/alm/positions/${positionId}`);
  return response.data;
}

export async function getLatestALMPosition(): Promise<ALMPosition> {
  const response = await api.get<ALMPosition>(`${BASE_URL}/alm/positions/latest`);
  return response.data;
}

export async function getALMHistory(limit = 12): Promise<
  {
    positionId: string;
    asOfDate: string;
    totalAssets: number;
    totalLiabilities: number;
    netPosition: number;
    createdAt: string;
  }[]
> {
  const response = await api.get(`${BASE_URL}/alm/history?limit=${limit}`);
  return response.data;
}

export interface ALMBucketData {
  bucketName: string;
  daysFrom: number;
  daysTo: number;
  assets: number;
  liabilities: number;
  gap: number;
  cumulativeGap: number;
}

export async function getGapAnalysis(positionId?: string): Promise<{
  asOfDate: string;
  buckets: ALMBucketData[];
  totalAssets: number;
  totalLiabilities: number;
  netGap: number;
}> {
  const params = positionId ? `?position_id=${positionId}` : '';
  const response = await api.get(`${BASE_URL}/alm/gap-analysis${params}`);
  return response.data;
}

export interface IRSData {
  rateShockBps: number;
  impactOnNii: number;
  impactOnEquity: number;
}

// =============== IRS Preview (non-persisting) ===============
// Wire format: Pydantic CamelSchema; Decimal fields are JSON strings per
// CLAUDE.md §6.2 — coerce with `Number(...)` only at the chart input boundary.

export interface IRSShockBucketWire {
  shockBps: number;
  rsa: string;
  rsl: string;
  gap: string;
  niiImpact: string;
  niiImpactPercent: string;
}

export interface IRSPreviewSummaryWire {
  rsa: string;
  rsl: string;
  gap: string;
  totalAssets: string;
  gapToTotalAssetsPercent: string;
}

export interface IRSPreviewResponseWire {
  asOfDate: string;
  summary: IRSPreviewSummaryWire;
  shocks: IRSShockBucketWire[];
}

export async function getIrsPreview(asOfDate?: string): Promise<IRSPreviewResponseWire> {
  const params = new URLSearchParams();
  if (asOfDate) params.append('as_of_date', asOfDate);
  const qs = params.toString();
  const url = qs ? `${BASE_URL}/irs/preview?${qs}` : `${BASE_URL}/irs/preview`;
  const response = await api.get<IRSPreviewResponseWire>(url);
  return response.data;
}

export async function getIRSAnalysis(positionId?: string): Promise<{
  asOfDate: string;
  scenarios: {
    scenario: string;
    rateShockBps: number;
    impactOnNii: number;
    impactOnEquity: number;
    niiPercentChange: number;
  }[];
  riskSensitiveAssets: number;
  riskSensitiveLiabilities: number;
  gap: number;
}> {
  const params = positionId ? `?position_id=${positionId}` : '';
  const response = await api.get(`${BASE_URL}/alm/irs-analysis${params}`);
  return response.data;
}

// ============== Exposure & Limits ==============

export async function getExposureSummary(): Promise<{
  totalBorrowings: number;
  byLenderType: {
    lenderType: string;
    amount: number;
    count: number;
    percent: number;
  }[];
  byLender: {
    lenderId: string;
    lenderName: string;
    sanctioned: number;
    outstanding: number;
    utilizationPercent: number;
  }[];
  concentrationRisk: {
    lenderName: string;
    exposurePercent: number;
    limitPercent: number;
    status: 'WITHIN_LIMIT' | 'NEAR_LIMIT' | 'BREACHED';
  }[];
}> {
  const response = await api.get(`${BASE_URL}/exposure/summary`);
  return response.data;
}

export async function getMaturityProfile(): Promise<{
  assets: { bucket: string; amount: number }[];
  liabilities: { bucket: string; amount: number }[];
  totalAssets: number;
  totalLiabilities: number;
}> {
  const response = await api.get(`${BASE_URL}/maturity-profile`);
  return response.data;
}

// ============== Reports ==============

export async function getBorrowingPosition(): Promise<{
  asOfDate: string;
  totalSanctioned: number;
  totalDrawn: number;
  totalOutstanding: number;
  availableLimit: number;
  weightedAvgRate: number;
  byFacilityType: {
    facilityType: string;
    sanctioned: number;
    outstanding: number;
    rate: number;
  }[];
}> {
  const response = await api.get(`${BASE_URL}/reports/borrowing-position`);
  return response.data;
}

export async function getUpcomingRepayments(days = 30): Promise<
  {
    borrowingId: string;
    lenderName: string;
    facilityName: string;
    dueDate: string;
    principalDue: number;
    interestDue: number;
    totalDue: number;
  }[]
> {
  const response = await api.get(`${BASE_URL}/reports/upcoming-repayments?days=${days}`);
  return response.data;
}

// ============== Export all functions ==============

export const treasuryApi = {
  // Lenders
  getLenders,
  getLender,
  createLender,
  updateLender,
  deleteLender,

  // Borrowings
  getBorrowings,
  getBorrowing,
  createBorrowing,
  updateBorrowing,

  // Tranches
  recordDrawdown,
  getTranches,

  // Repayments
  recordRepayment,
  getRepaymentHistory,

  // Schedule
  getBorrowingSchedule,
  regenerateBorrowingSchedule,

  // ALM
  generateALMPosition,
  getALMPosition,
  getLatestALMPosition,
  getALMHistory,
  getGapAnalysis,
  getIRSAnalysis,
  getIrsPreview,

  // Exposure
  getExposureSummary,
  getMaturityProfile,

  // Reports
  getBorrowingPosition,
  getUpcomingRepayments,
};

export default treasuryApi;
