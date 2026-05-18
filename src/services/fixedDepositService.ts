/**
 * Fixed Deposit Service
 * API client for fixed deposit operations
 */

import api from './api';

// Enums
export type FDInterestPayoutFrequency =
  | 'MONTHLY'
  | 'QUARTERLY'
  | 'HALF_YEARLY'
  | 'ANNUALLY'
  | 'ON_MATURITY';

export type FDCompoundingFrequency =
  | 'MONTHLY'
  | 'QUARTERLY'
  | 'HALF_YEARLY'
  | 'ANNUALLY'
  | 'SIMPLE';

export type FDCustomerCategory =
  | 'GENERAL'
  | 'SENIOR_CITIZEN'
  | 'STAFF'
  | 'NRI'
  | 'CORPORATE';

export type FDStatus =
  | 'DRAFT'
  | 'PENDING_APPROVAL'
  | 'ACTIVE'
  | 'MATURED'
  | 'PREMATURE_CLOSED'
  | 'RENEWED'
  | 'CANCELLED';

export type FDTransactionType =
  | 'DEPOSIT'
  | 'INTEREST_PAYOUT'
  | 'INTEREST_CAPITALIZATION'
  | 'TDS_DEDUCTION'
  | 'MATURITY_PAYOUT'
  | 'PREMATURE_PAYOUT'
  | 'RENEWAL'
  | 'LOAN_DISBURSEMENT'
  | 'LOAN_REPAYMENT'
  | 'PENALTY';

// Types
export interface FDInterestSlab {
  id: string;
  product_id: string;
  customer_category: FDCustomerCategory;
  min_tenure_days: number;
  max_tenure_days: number;
  min_amount?: number;
  max_amount?: number;
  interest_rate: number;
  effective_from: string;
  effective_to?: string;
  is_active: boolean;
}

export interface FDProduct {
  id: string;
  organization_id: string;
  product_code: string;
  product_name: string;
  description?: string;
  min_tenure_days: number;
  max_tenure_days: number;
  min_amount: number;
  max_amount?: number;
  interest_payout_frequency: FDInterestPayoutFrequency;
  compounding_frequency: FDCompoundingFrequency;
  allow_premature_withdrawal: boolean;
  premature_penalty_rate?: number;
  allow_auto_renewal: boolean;
  auto_renewal_tenure_days?: number;
  allow_loan_against_fd: boolean;
  max_loan_percentage?: number;
  loan_interest_premium?: number;
  tds_applicable: boolean;
  tds_threshold: number;
  fd_liability_account_id?: string;
  interest_expense_account_id?: string;
  tds_payable_account_id?: string;
  effective_from: string;
  effective_to?: string;
  is_active: boolean;
  interest_slabs: FDInterestSlab[];
  created_at: string;
}

export interface FDNominee {
  id: string;
  fixed_deposit_id: string;
  nominee_name: string;
  relationship: string;
  date_of_birth?: string;
  share_percentage: number;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  pincode?: string;
  is_minor: boolean;
  guardian_name?: string;
  guardian_relationship?: string;
}

export interface FDTransaction {
  id: string;
  fixed_deposit_id: string;
  transaction_date: string;
  transaction_type: FDTransactionType;
  description: string;
  debit_amount: number;
  credit_amount: number;
  balance: number;
  payment_mode?: string;
  reference_number?: string;
  voucher_id?: string;
  remarks?: string;
  created_at: string;
}

export interface FDInterestAccrual {
  id: string;
  fixed_deposit_id: string;
  accrual_date: string;
  period_from: string;
  period_to: string;
  days: number;
  principal_amount: number;
  interest_rate: number;
  interest_amount: number;
  cumulative_interest: number;
  is_paid: boolean;
  paid_date?: string;
  payment_reference?: string;
  voucher_id?: string;
}

export interface FixedDeposit {
  id: string;
  organization_id: string;
  fd_number: string;
  certificate_number?: string;
  product_id: string;
  product_code?: string;
  product_name?: string;
  customer_id: string;
  customer_name?: string;
  customer_category: FDCustomerCategory;
  deposit_amount: number;
  deposit_date: string;
  value_date: string;
  tenure_days: number;
  maturity_date: string;
  interest_rate: number;
  interest_payout_frequency: FDInterestPayoutFrequency;
  compounding_frequency: FDCompoundingFrequency;
  maturity_amount: number;
  accrued_interest: number;
  paid_interest: number;
  tds_deducted: number;
  interest_payout_mode: string;
  payout_bank_account_id?: string;
  auto_renew: boolean;
  renewal_tenure_days?: number;
  renewal_count: number;
  parent_fd_id?: string;
  has_loan: boolean;
  loan_account_id?: string;
  status: FDStatus;
  last_interest_calc_date?: string;
  last_interest_payout_date?: string;
  closed_date?: string;
  closure_amount?: number;
  closure_remarks?: string;
  branch_id?: string;
  created_by_user_id?: string;
  approved_by_user_id?: string;
  approved_at?: string;
  remarks?: string;
  created_at: string;
  nominees: FDNominee[];
}

export interface FDSummary {
  total_fds: number;
  active_fds: number;
  total_deposit_amount: number;
  total_maturity_amount: number;
  maturing_this_month: number;
  maturing_next_month: number;
  by_status: Record<string, number>;
  by_customer_category: Record<string, number>;
}

export interface FDMaturityProjection {
  fd_id: string;
  fd_number: string;
  deposit_amount: number;
  interest_rate: number;
  tenure_days: number;
  maturity_date: string;
  projected_interest: number;
  projected_maturity_amount: number;
  tds_estimate: number;
  net_maturity_amount: number;
  schedule: {
    period_from: string;
    period_to: string;
    days: number;
    principal: number;
    interest: number;
  }[];
}

function toNumber(value: number | string | null | undefined): number {
  if (typeof value === 'number') {
    return value;
  }
  if (typeof value === 'string') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
  }
  return 0;
}

function toOptionalNumber(value: number | string | null | undefined): number | undefined {
  if (value === null || value === undefined || value === '') {
    return undefined;
  }
  return toNumber(value);
}

function normalizeInterestSlab(slab: FDInterestSlab): FDInterestSlab {
  return {
    ...slab,
    min_amount: toOptionalNumber(slab.min_amount),
    max_amount: toOptionalNumber(slab.max_amount),
    interest_rate: toNumber(slab.interest_rate),
  };
}

function normalizeProduct(product: FDProduct): FDProduct {
  return {
    ...product,
    min_amount: toNumber(product.min_amount),
    max_amount: toOptionalNumber(product.max_amount),
    premature_penalty_rate: toOptionalNumber(product.premature_penalty_rate),
    max_loan_percentage: toOptionalNumber(product.max_loan_percentage),
    loan_interest_premium: toOptionalNumber(product.loan_interest_premium),
    tds_threshold: toNumber(product.tds_threshold),
    interest_slabs: product.interest_slabs.map(normalizeInterestSlab),
  };
}

function normalizeNominee(nominee: FDNominee): FDNominee {
  return {
    ...nominee,
    share_percentage: toNumber(nominee.share_percentage),
  };
}

function normalizeTransaction(transaction: FDTransaction): FDTransaction {
  return {
    ...transaction,
    debit_amount: toNumber(transaction.debit_amount),
    credit_amount: toNumber(transaction.credit_amount),
    balance: toNumber(transaction.balance),
  };
}

function normalizeAccrual(accrual: FDInterestAccrual): FDInterestAccrual {
  return {
    ...accrual,
    principal_amount: toNumber(accrual.principal_amount),
    interest_rate: toNumber(accrual.interest_rate),
    interest_amount: toNumber(accrual.interest_amount),
    cumulative_interest: toNumber(accrual.cumulative_interest),
  };
}

function normalizeDeposit(deposit: FixedDeposit): FixedDeposit {
  return {
    ...deposit,
    deposit_amount: toNumber(deposit.deposit_amount),
    interest_rate: toNumber(deposit.interest_rate),
    maturity_amount: toNumber(deposit.maturity_amount),
    accrued_interest: toNumber(deposit.accrued_interest),
    paid_interest: toNumber(deposit.paid_interest),
    tds_deducted: toNumber(deposit.tds_deducted),
    closure_amount: toOptionalNumber(deposit.closure_amount),
    nominees: deposit.nominees.map(normalizeNominee),
  };
}

function normalizeSummary(summary: FDSummary): FDSummary {
  return {
    ...summary,
    total_deposit_amount: toNumber(summary.total_deposit_amount),
    total_maturity_amount: toNumber(summary.total_maturity_amount),
  };
}

function normalizeProjection(projection: FDMaturityProjection): FDMaturityProjection {
  return {
    ...projection,
    deposit_amount: toNumber(projection.deposit_amount),
    interest_rate: toNumber(projection.interest_rate),
    projected_interest: toNumber(projection.projected_interest),
    projected_maturity_amount: toNumber(projection.projected_maturity_amount),
    tds_estimate: toNumber(projection.tds_estimate),
    net_maturity_amount: toNumber(projection.net_maturity_amount),
    schedule: projection.schedule.map((item) => ({
      ...item,
      principal: toNumber(item.principal),
      interest: toNumber(item.interest),
    })),
  };
}

// Service class
class FixedDepositService {
  // ============== FD Products ==============

  async listProducts(params: {
    organization_id: string;
    active_only?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<{ items: FDProduct[]; total: number }> {
    const response = await api.get('/fixed-deposits/products', { params });
    return {
      ...response.data,
      items: response.data.items.map(normalizeProduct),
    };
  }

  async getProduct(id: string): Promise<FDProduct> {
    const response = await api.get(`/fixed-deposits/products/${id}`);
    return normalizeProduct(response.data);
  }

  async createProduct(data: Partial<FDProduct>): Promise<FDProduct> {
    const response = await api.post('/fixed-deposits/products', data);
    return normalizeProduct(response.data);
  }

  async updateProduct(id: string, data: Partial<FDProduct>): Promise<FDProduct> {
    const response = await api.put(`/fixed-deposits/products/${id}`, data);
    return normalizeProduct(response.data);
  }

  async deleteProduct(id: string): Promise<void> {
    await api.delete(`/fixed-deposits/products/${id}`);
  }

  // Interest Slabs
  async addInterestSlab(
    productId: string,
    data: Partial<FDInterestSlab>
  ): Promise<FDInterestSlab> {
    const response = await api.post(
      `/fixed-deposits/products/${productId}/slabs`,
      data
    );
    return normalizeInterestSlab(response.data);
  }

  async updateInterestSlab(
    slabId: string,
    data: Partial<FDInterestSlab>
  ): Promise<FDInterestSlab> {
    const response = await api.put(`/fixed-deposits/products/slabs/${slabId}`, data);
    return normalizeInterestSlab(response.data);
  }

  async deleteInterestSlab(slabId: string): Promise<void> {
    await api.delete(`/fixed-deposits/products/slabs/${slabId}`);
  }

  async getApplicableRate(params: {
    product_id: string;
    tenure_days: number;
    amount: number;
    customer_category: FDCustomerCategory;
    as_of_date?: string;
  }): Promise<{ interest_rate: number }> {
    const response = await api.get(
      `/fixed-deposits/products/${params.product_id}/rate`,
      {
        params: {
          tenure_days: params.tenure_days,
          amount: params.amount,
          customer_category: params.customer_category,
          as_of_date: params.as_of_date,
        },
      }
    );
    return {
      ...response.data,
      interest_rate: toNumber(response.data.interest_rate),
    };
  }

  // ============== Fixed Deposits ==============

  async listDeposits(params: {
    organization_id: string;
    customer_id?: string;
    product_id?: string;
    status?: FDStatus;
    maturing_before?: string;
    maturing_after?: string;
    skip?: number;
    limit?: number;
  }): Promise<{ items: FixedDeposit[]; total: number }> {
    const response = await api.get('/fixed-deposits/deposits', { params });
    return {
      ...response.data,
      items: response.data.items.map(normalizeDeposit),
    };
  }

  async getDeposit(id: string): Promise<FixedDeposit> {
    const response = await api.get(`/fixed-deposits/deposits/${id}`);
    return normalizeDeposit(response.data);
  }

  async createDeposit(data: Partial<FixedDeposit>): Promise<FixedDeposit> {
    const response = await api.post('/fixed-deposits/deposits', data);
    return normalizeDeposit(response.data);
  }

  async updateDeposit(
    id: string,
    data: Partial<FixedDeposit>
  ): Promise<FixedDeposit> {
    const response = await api.put(`/fixed-deposits/deposits/${id}`, data);
    return normalizeDeposit(response.data);
  }

  async approveDeposit(id: string, userId: string): Promise<FixedDeposit> {
    const response = await api.post(`/fixed-deposits/deposits/${id}/approve`, null, {
      params: { user_id: userId },
    });
    return normalizeDeposit(response.data);
  }

  async closeDeposit(
    id: string,
    data: {
      closure_date: string;
      closure_reason: 'MATURITY' | 'PREMATURE' | 'CUSTOMER_REQUEST';
      payout_mode: 'BANK_TRANSFER' | 'CHEQUE' | 'CASH';
      bank_account_id?: string;
      remarks?: string;
    }
  ): Promise<FixedDeposit> {
    const response = await api.post(`/fixed-deposits/deposits/${id}/close`, data);
    return normalizeDeposit(response.data);
  }

  async renewDeposit(
    id: string,
    data: {
      new_tenure_days?: number;
      new_product_id?: string;
      include_interest?: boolean;
      partial_withdrawal?: number;
      remarks?: string;
    }
  ): Promise<FixedDeposit> {
    const response = await api.post(`/fixed-deposits/deposits/${id}/renew`, data);
    return normalizeDeposit(response.data);
  }

  // Summary
  async getSummary(organizationId: string): Promise<FDSummary> {
    const response = await api.get('/fixed-deposits/deposits/summary', {
      params: { organization_id: organizationId },
    });
    return normalizeSummary(response.data);
  }

  // Projection
  async getProjection(fdId: string): Promise<FDMaturityProjection> {
    const response = await api.get(`/fixed-deposits/deposits/${fdId}/projection`);
    return normalizeProjection(response.data);
  }

  // Nominees
  async addNominee(fdId: string, data: Partial<FDNominee>): Promise<FDNominee> {
    const response = await api.post(
      `/fixed-deposits/deposits/${fdId}/nominees`,
      data
    );
    return normalizeNominee(response.data);
  }

  async removeNominee(nomineeId: string): Promise<void> {
    await api.delete(`/fixed-deposits/deposits/nominees/${nomineeId}`);
  }

  // Transactions
  async getTransactions(fdId: string): Promise<FDTransaction[]> {
    const response = await api.get(`/fixed-deposits/deposits/${fdId}/transactions`);
    return response.data.map(normalizeTransaction);
  }

  // Accruals
  async getAccruals(fdId: string): Promise<FDInterestAccrual[]> {
    const response = await api.get(`/fixed-deposits/deposits/${fdId}/accruals`);
    return response.data.map(normalizeAccrual);
  }

  // Interest Operations
  async runInterestAccrual(
    organizationId: string,
    accrualDate: string
  ): Promise<{ processed: number; total_interest: number }> {
    const response = await api.post('/fixed-deposits/deposits/interest/accrue', null, {
      params: { organization_id: organizationId, accrual_date: accrualDate },
    });
    return {
      ...response.data,
      total_interest: toNumber(response.data.total_interest),
    };
  }

  async processInterestPayout(
    organizationId: string,
    payoutDate: string
  ): Promise<{ processed: number; total_payout: number }> {
    const response = await api.post('/fixed-deposits/deposits/interest/payout', null, {
      params: { organization_id: organizationId, payout_date: payoutDate },
    });
    return {
      ...response.data,
      total_payout: toNumber(response.data.total_payout),
    };
  }
}

export const fixedDepositService = new FixedDepositService();
export default fixedDepositService;
