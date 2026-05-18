/**
 * Credit Bureau API Service
 *
 * Thin axios wrapper for /lending/credit/* endpoints.
 *
 * Wire format is camelCase via backend CamelSchema. Query-string names are
 * translated at the hook boundary where FastAPI query parameters require it.
 *
 * See CLAUDE.md §5.4 (services are thin), §6.3 (Idempotency-Key required on
 * financial mutations — a bureau pull triggers a paid API call).
 */
import api from '../api';

export type CreditBureau = 'CIBIL' | 'EXPERIAN' | 'EQUIFAX' | 'CRIF';
export type CreditPullType = 'SOFT' | 'HARD';

/**
 * Request body for POST /lending/credit/pull.
 *
 * Field names match the backend `CreditPullRequest` schema (camelCase).
 * Optional fields should be omitted (not sent as empty strings) when blank.
 */
export interface CreateCreditPullRequest {
  bureau: CreditBureau;
  pullType: CreditPullType;
  customerName: string;
  panNumber?: string;
  aadhaarLast4?: string;
  mobileNumber?: string;
  email?: string;
  /** ISO date string `yyyy-MM-dd` */
  dateOfBirth?: string;
  addressLine1?: string;
  addressLine2?: string;
  city?: string;
  state?: string;
  pincode?: string;
  entityId?: string;
  loanApplicationId?: string;
  purpose?: string;
}

/**
 * Response shape from POST /lending/credit/pull.
 */
export interface CreditPullDetail {
  id: string;
  organizationId: string;
  entityId: string | null;
  loanApplicationId: string | null;
  bureau: CreditBureau;
  pullType: CreditPullType;
  status: string;
  customerName: string;
  panNumber: string | null;
  requestReference: string | null;
  bureauReference: string | null;
  creditScore: number | null;
  scoreVersion: string | null;
  scoreDate: string | null;
  scoreBand: string | null;
  totalAccounts: number | null;
  activeAccounts: number | null;
  // Decimal fields arrive as JSON strings (CLAUDE.md §6.2).
  totalSanctioned: string | null;
  totalOutstanding: string | null;
  totalOverdue: string | null;
  maxDpdLast12m: number | null;
  maxDpdLast24m: number | null;
  enquiriesLast30d: number | null;
  enquiriesLast12m: number | null;
  errorCode: string | null;
  errorMessage: string | null;
  pulledAt: string | null;
  expiresAt: string | null;
  createdAt: string;
  accounts: unknown[];
  enquiries: unknown[];
  isValid: boolean;
}

const BASE_URL = '/lending/credit';

/**
 * Initiate a credit-bureau pull.
 *
 * Generates a fresh `Idempotency-Key` per call — a bureau pull is a paid
 * financial mutation (CLAUDE.md §6.3). If the network call retries, the
 * same key reaches the server and dedupe kicks in.
 */
export async function createCreditPull(data: CreateCreditPullRequest): Promise<CreditPullDetail> {
  const response = await api.post<CreditPullDetail>(`${BASE_URL}/pull`, data, {
    headers: {
      'Idempotency-Key': crypto.randomUUID(),
    },
  });
  return response.data;
}

export const creditApi = {
  createCreditPull,
};

export default creditApi;
