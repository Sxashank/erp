/**
 * Treasury API Service
 * API calls for Treasury, Borrowings, and ALM management
 */

import api from '../api';
import type {
  Lender,
  Borrowing,
  ALMPosition,
  LenderFilters,
  BorrowingFilters,
  PaginatedResponse,
} from '@/types/lending';

const BASE_URL = '/lending/treasury';

// ============== Lenders ==============

export async function getLenders(filters?: LenderFilters): Promise<PaginatedResponse<Lender>> {
  const params = new URLSearchParams();

  if (filters?.search) params.append('search', filters.search);
  if (filters?.lender_type) params.append('lender_type', filters.lender_type);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.page) params.append('page', filters.page.toString());
  if (filters?.page_size) params.append('page_size', filters.page_size.toString());

  const response = await api.get<PaginatedResponse<Lender>>(`${BASE_URL}/lenders?${params.toString()}`);
  return response.data;
}

export async function getLender(lenderId: string): Promise<Lender> {
  const response = await api.get<Lender>(`${BASE_URL}/lenders/${lenderId}`);
  return response.data;
}

export interface CreateLenderRequest {
  lender_name: string;
  lender_type: 'BANK' | 'DFI' | 'NCD' | 'CP' | 'SUBORDINATED_DEBT' | 'OTHER';
  contact_person?: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  remarks?: string;
}

export async function createLender(data: CreateLenderRequest): Promise<Lender> {
  const response = await api.post<Lender>(`${BASE_URL}/lenders`, data);
  return response.data;
}

export async function updateLender(lenderId: string, data: Partial<CreateLenderRequest>): Promise<Lender> {
  const response = await api.put<Lender>(`${BASE_URL}/lenders/${lenderId}`, data);
  return response.data;
}

export async function deleteLender(lenderId: string): Promise<void> {
  await api.delete(`${BASE_URL}/lenders/${lenderId}`);
}

// ============== Borrowings ==============

export async function getBorrowings(filters?: BorrowingFilters): Promise<PaginatedResponse<Borrowing>> {
  const params = new URLSearchParams();

  if (filters?.search) params.append('search', filters.search);
  if (filters?.lender_id) params.append('lender_id', filters.lender_id);
  if (filters?.facility_type) params.append('facility_type', filters.facility_type);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.date_from) params.append('date_from', filters.date_from);
  if (filters?.date_to) params.append('date_to', filters.date_to);
  if (filters?.page) params.append('page', filters.page.toString());
  if (filters?.page_size) params.append('page_size', filters.page_size.toString());

  const response = await api.get<PaginatedResponse<Borrowing>>(`${BASE_URL}/borrowings?${params.toString()}`);
  return response.data;
}

export async function getBorrowing(borrowingId: string): Promise<Borrowing> {
  const response = await api.get<Borrowing>(`${BASE_URL}/borrowings/${borrowingId}`);
  return response.data;
}

export interface CreateBorrowingRequest {
  lender_id: string;
  facility_type: 'TERM_LOAN' | 'WORKING_CAPITAL' | 'NCD' | 'CP' | 'SUBORDINATED_DEBT';
  facility_name: string;
  sanctioned_amount: number;
  interest_type: 'FIXED' | 'FLOATING';
  interest_rate: number;
  base_rate_id?: string;
  spread_bps?: number;
  tenure_months: number;
  sanction_date: string;
  maturity_date: string;
  repayment_frequency: 'MONTHLY' | 'QUARTERLY' | 'HALF_YEARLY' | 'YEARLY' | 'BULLET';
  security_details?: string;
  covenants?: string;
  remarks?: string;
}

export async function createBorrowing(data: CreateBorrowingRequest): Promise<Borrowing> {
  const response = await api.post<Borrowing>(`${BASE_URL}/borrowings`, data);
  return response.data;
}

export async function updateBorrowing(borrowingId: string, data: Partial<CreateBorrowingRequest>): Promise<Borrowing> {
  const response = await api.put<Borrowing>(`${BASE_URL}/borrowings/${borrowingId}`, data);
  return response.data;
}

// ============== Borrowing Tranches/Drawdowns ==============

export interface BorrowingTranche {
  tranche_id: string;
  borrowing_id: string;
  tranche_number: number;
  drawdown_date: string;
  amount: number;
  maturity_date: string;
  interest_rate: number;
  status: 'ACTIVE' | 'CLOSED';
  outstanding_amount: number;
}

export async function recordDrawdown(
  borrowingId: string,
  data: { amount: number; drawdown_date: string; interest_rate?: number; remarks?: string }
): Promise<BorrowingTranche> {
  const response = await api.post<BorrowingTranche>(`${BASE_URL}/borrowings/${borrowingId}/drawdown`, data);
  return response.data;
}

export async function getTranches(borrowingId: string): Promise<BorrowingTranche[]> {
  const response = await api.get<BorrowingTranche[]>(`${BASE_URL}/borrowings/${borrowingId}/tranches`);
  return response.data;
}

// ============== Borrowing Repayments ==============

export interface BorrowingRepayment {
  repayment_id: string;
  borrowing_id: string;
  tranche_id?: string;
  payment_date: string;
  principal_amount: number;
  interest_amount: number;
  total_amount: number;
  reference_number?: string;
  remarks?: string;
}

export async function recordRepayment(
  borrowingId: string,
  data: {
    tranche_id?: string;
    payment_date: string;
    principal_amount: number;
    interest_amount: number;
    reference_number?: string;
    remarks?: string;
  }
): Promise<BorrowingRepayment> {
  const response = await api.post<BorrowingRepayment>(`${BASE_URL}/borrowings/${borrowingId}/repayment`, data);
  return response.data;
}

export async function getRepaymentHistory(borrowingId: string): Promise<BorrowingRepayment[]> {
  const response = await api.get<BorrowingRepayment[]>(`${BASE_URL}/borrowings/${borrowingId}/repayments`);
  return response.data;
}

// ============== Borrowing Schedule ==============

export interface BorrowingScheduleEntry {
  schedule_id: string;
  borrowing_id: string;
  tranche_id?: string;
  due_date: string;
  principal_due: number;
  interest_due: number;
  total_due: number;
  principal_paid: number;
  interest_paid: number;
  status: 'PENDING' | 'PAID' | 'OVERDUE';
}

export async function getBorrowingSchedule(borrowingId: string): Promise<BorrowingScheduleEntry[]> {
  const response = await api.get<BorrowingScheduleEntry[]>(`${BASE_URL}/borrowings/${borrowingId}/schedule`);
  return response.data;
}

export async function regenerateBorrowingSchedule(borrowingId: string): Promise<BorrowingScheduleEntry[]> {
  const response = await api.post<BorrowingScheduleEntry[]>(`${BASE_URL}/borrowings/${borrowingId}/schedule/regenerate`);
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

export async function getALMHistory(limit: number = 12): Promise<Array<{
  position_id: string;
  as_of_date: string;
  total_assets: number;
  total_liabilities: number;
  net_position: number;
  created_at: string;
}>> {
  const response = await api.get(`${BASE_URL}/alm/history?limit=${limit}`);
  return response.data;
}

export interface ALMBucketData {
  bucket_name: string;
  days_from: number;
  days_to: number;
  assets: number;
  liabilities: number;
  gap: number;
  cumulative_gap: number;
}

export async function getGapAnalysis(positionId?: string): Promise<{
  as_of_date: string;
  buckets: ALMBucketData[];
  total_assets: number;
  total_liabilities: number;
  net_gap: number;
}> {
  const params = positionId ? `?position_id=${positionId}` : '';
  const response = await api.get(`${BASE_URL}/alm/gap-analysis${params}`);
  return response.data;
}

export interface IRSData {
  rate_shock_bps: number;
  impact_on_nii: number;
  impact_on_equity: number;
}

export async function getIRSAnalysis(positionId?: string): Promise<{
  as_of_date: string;
  scenarios: Array<{
    scenario: string;
    rate_shock_bps: number;
    impact_on_nii: number;
    impact_on_equity: number;
    nii_percent_change: number;
  }>;
  risk_sensitive_assets: number;
  risk_sensitive_liabilities: number;
  gap: number;
}> {
  const params = positionId ? `?position_id=${positionId}` : '';
  const response = await api.get(`${BASE_URL}/alm/irs-analysis${params}`);
  return response.data;
}

// ============== Exposure & Limits ==============

export async function getExposureSummary(): Promise<{
  total_borrowings: number;
  by_lender_type: Array<{
    lender_type: string;
    amount: number;
    count: number;
    percent: number;
  }>;
  by_lender: Array<{
    lender_id: string;
    lender_name: string;
    sanctioned: number;
    outstanding: number;
    utilization_percent: number;
  }>;
  concentration_risk: Array<{
    lender_name: string;
    exposure_percent: number;
    limit_percent: number;
    status: 'WITHIN_LIMIT' | 'NEAR_LIMIT' | 'BREACHED';
  }>;
}> {
  const response = await api.get(`${BASE_URL}/exposure/summary`);
  return response.data;
}

export async function getMaturityProfile(): Promise<{
  assets: Array<{ bucket: string; amount: number }>;
  liabilities: Array<{ bucket: string; amount: number }>;
  total_assets: number;
  total_liabilities: number;
}> {
  const response = await api.get(`${BASE_URL}/maturity-profile`);
  return response.data;
}

// ============== Reports ==============

export async function getBorrowingPosition(): Promise<{
  as_of_date: string;
  total_sanctioned: number;
  total_drawn: number;
  total_outstanding: number;
  available_limit: number;
  weighted_avg_rate: number;
  by_facility_type: Array<{
    facility_type: string;
    sanctioned: number;
    outstanding: number;
    rate: number;
  }>;
}> {
  const response = await api.get(`${BASE_URL}/reports/borrowing-position`);
  return response.data;
}

export async function getUpcomingRepayments(days: number = 30): Promise<Array<{
  borrowing_id: string;
  lender_name: string;
  facility_name: string;
  due_date: string;
  principal_due: number;
  interest_due: number;
  total_due: number;
}>> {
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

  // Exposure
  getExposureSummary,
  getMaturityProfile,

  // Reports
  getBorrowingPosition,
  getUpcomingRepayments,
};

export default treasuryApi;
