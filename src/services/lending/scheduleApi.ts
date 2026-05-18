/**
 * Schedule API service — preview / generate / fetch repayment schedules.
 *
 * The /preview endpoint is pure computation (no DB writes, no permission
 * gate) and is what the LOS calculator screen consumes. Monetary fields
 * are JSON strings on the wire (Pydantic Decimal — CLAUDE.md §6.2); pass
 * them straight to <AmountDisplay> or coerce via Number() only at display
 * sites (e.g. recharts inputs).
 */

import api from '../api';

const BASE_URL = '/lending/schedules';

export type ScheduleCalculationMethod = 'reducing_balance' | 'flat' | 'emi' | 'rule_of_78';

export interface SchedulePreviewRequest {
  principal: string | number;
  interestRate: string | number;
  tenureMonths: number;
  disbursementDate: string; // ISO yyyy-MM-dd
  emiDay?: number;
  calculationMethod?: ScheduleCalculationMethod | string;
  moratoriumMonths?: number;
}

export interface SchedulePreviewLine {
  installmentNumber: number;
  dueDate: string;
  openingBalance: string;
  principalAmount: string;
  interestAmount: string;
  totalAmount: string;
  closingBalance: string;
  isMoratorium: boolean;
}

export interface SchedulePreviewSummary {
  totalInstallments: number;
  totalPrincipal: string;
  totalInterest: string;
  totalAmount: string;
  emiAmount: string;
  lastDueDate: string;
}

export interface SchedulePreviewResponse {
  entries: SchedulePreviewLine[];
  summary: SchedulePreviewSummary;
}

export async function previewSchedule(
  payload: SchedulePreviewRequest,
): Promise<SchedulePreviewResponse> {
  const response = await api.post<SchedulePreviewResponse>(`${BASE_URL}/preview`, payload);
  return response.data;
}

export const scheduleApi = {
  previewSchedule,
};

export default scheduleApi;
