/**
 * Enhanced Lending API Service
 * NPA, Schedule, Receipt, Disbursement, Collateral
 */

import api from './api';

import type {
  NPAClassificationResult,
  ProvisionCalculation,
  NPASummary,
  NPAMovement,
  LoanSchedule,
  EMICalculation,
  ScheduleGenerateParams,
  RescheduleParams,
  ScheduleEntry,
  Receipt,
  ReceiptAllocation,
  ReceiptCreateParams,
  BulkReceiptItem,
  BulkReceiptResult,
  Disbursement,
  DisbursementCreateParams,
  DisbursementProcessParams,
  TrancheItem,
  DisbursementSummary,
  Collateral,
  CollateralCreateParams,
  SecurityCoverage,
  CollateralSummary,
  PropertyDetails,
  OwnerDetails,
  ValuationDetails,
} from '@/types/lending/enhanced';

const BASE_URL = '/api/v1/lending';

// ============== NPA API ==============

export const npaApi = {
  getDPD: async (loanAccountId: string): Promise<{ loan_account_id: string; dpd: number }> => {
    const response = await api.get(`${BASE_URL}/npa/dpd/${loanAccountId}`);
    return response.data;
  },

  classifyLoan: async (loanAccountId: string, asOfDate?: string): Promise<NPAClassificationResult> => {
    const response = await api.post(`${BASE_URL}/npa/classify`, {
      loan_account_id: loanAccountId,
      as_of_date: asOfDate,
    });
    return response.data;
  },

  calculateProvision: async (
    loanAccountId: string,
    securityValue?: number,
    asOfDate?: string
  ): Promise<ProvisionCalculation> => {
    const response = await api.post(`${BASE_URL}/npa/provision`, {
      loan_account_id: loanAccountId,
      security_value: securityValue,
      as_of_date: asOfDate,
    });
    return response.data;
  },

  batchClassify: async (
    asOfDate?: string,
    autoUpdate = true
  ): Promise<{ total_processed: number; classifications: Record<string, number>; errors: unknown[] }> => {
    const response = await api.post(`${BASE_URL}/npa/batch-classify`, {
      as_of_date: asOfDate,
      auto_update: autoUpdate,
    }, { params: {} });
    return response.data;
  },

  upgradeNPA: async (loanAccountId: string, reason: string, upgradeDate?: string): Promise<void> => {
    await api.post(`${BASE_URL}/npa/upgrade`, {
      loan_account_id: loanAccountId,
      upgrade_reason: reason,
      upgrade_date: upgradeDate,
    });
  },

  writeOffLoan: async (
    loanAccountId: string,
    reason: string,
    boardApprovalRef?: string,
    writeOffDate?: string
  ): Promise<void> => {
    await api.post(`${BASE_URL}/npa/write-off`, {
      loan_account_id: loanAccountId,
      write_off_reason: reason,
      board_approval_reference: boardApprovalRef,
      write_off_date: writeOffDate,
    });
  },

  getSummary: async (asOfDate?: string): Promise<NPASummary> => {
    const response = await api.get(`${BASE_URL}/npa/summary`, {
      params: { as_of_date: asOfDate },
    });
    return response.data;
  },

  getMovement: async (fromDate: string, toDate: string): Promise<NPAMovement> => {
    const response = await api.get(`${BASE_URL}/npa/movement`, {
      params: { from_date: fromDate, to_date: toDate },
    });
    return response.data;
  },
};

// ============== Schedule API ==============

export const scheduleApi = {
  generateSchedule: async (params: ScheduleGenerateParams): Promise<LoanSchedule> => {
    const response = await api.post(`${BASE_URL}/schedules/generate`, params);
    return response.data;
  },

  calculateEMI: async (principal: number, annualRate: number, tenureMonths: number): Promise<EMICalculation> => {
    const response = await api.post(`${BASE_URL}/schedules/calculate-emi`, {
      principal,
      annual_rate: annualRate,
      tenure_months: tenureMonths,
    });
    return response.data;
  },

  getSchedule: async (loanAccountId: string, includePaid = true): Promise<LoanSchedule> => {
    const response = await api.get(`${BASE_URL}/schedules/${loanAccountId}`, {
      params: { include_paid: includePaid },
    });
    return response.data;
  },

  getOverdueInstallments: async (
    loanAccountId: string,
    asOfDate?: string
  ): Promise<{ loan_account_id: string; overdue_count: number; installments: ScheduleEntry[] }> => {
    const response = await api.get(`${BASE_URL}/schedules/${loanAccountId}/overdue`, {
      params: { as_of_date: asOfDate },
    });
    return response.data;
  },

  rescheduleLoan: async (params: RescheduleParams): Promise<LoanSchedule> => {
    const response = await api.post(`${BASE_URL}/schedules/reschedule`, params);
    return response.data;
  },

  markInstallmentPaid: async (
    scheduleId: string,
    paymentDate: string,
    principalPaid: number,
    interestPaid: number,
    receiptId?: string
  ): Promise<ScheduleEntry> => {
    const response = await api.post(`${BASE_URL}/schedules/mark-paid`, {
      schedule_id: scheduleId,
      payment_date: paymentDate,
      principal_paid: principalPaid,
      interest_paid: interestPaid,
      receipt_id: receiptId,
    });
    return response.data;
  },
};

// ============== Receipt API ==============

export const receiptApi = {
  createReceipt: async (params: ReceiptCreateParams): Promise<Receipt> => {
    const response = await api.post(`${BASE_URL}/receipts`, params);
    return response.data;
  },

  allocateReceipt: async (
    receiptId: string,
    allocationMethod = 'fifo',
    specificAllocations?: Record<string, unknown>[]
  ): Promise<{ receipt_id: string; allocation_count: number; allocations: ReceiptAllocation[] }> => {
    const response = await api.post(`${BASE_URL}/receipts/allocate`, {
      receipt_id: receiptId,
      allocation_method: allocationMethod,
      specific_allocations: specificAllocations,
    });
    return response.data;
  },

  reverseReceipt: async (receiptId: string, reason: string, reversalDate?: string): Promise<Receipt> => {
    const response = await api.post(`${BASE_URL}/receipts/reverse`, {
      receipt_id: receiptId,
      reversal_reason: reason,
      reversal_date: reversalDate,
    });
    return response.data;
  },

  processBulkReceipts: async (
    receipts: BulkReceiptItem[],
    autoAllocate = true
  ): Promise<BulkReceiptResult> => {
    const response = await api.post(`${BASE_URL}/receipts/bulk`, {
      receipts,
      auto_allocate: autoAllocate,
    }, { params: {} });
    return response.data;
  },

  getReceiptsByLoan: async (
    loanAccountId: string,
    fromDate?: string,
    toDate?: string,
    status?: string
  ): Promise<{ loan_account_id: string; count: number; receipts: Receipt[] }> => {
    const response = await api.get(`${BASE_URL}/receipts/loan/${loanAccountId}`, {
      params: { from_date: fromDate, to_date: toDate, status },
    });
    return response.data;
  },

  getReceipt: async (receiptId: string): Promise<Receipt & { allocations: ReceiptAllocation[] }> => {
    const response = await api.get(`${BASE_URL}/receipts/${receiptId}`);
    return response.data;
  },

  getReceiptSummary: async (
    fromDate?: string,
    toDate?: string
  ): Promise<any> => {
    const response = await api.get(`${BASE_URL}/receipts/summary`, {
      params: { from_date: fromDate, to_date: toDate },
    });
    return response.data;
  },

  markBounced: async (
    receiptId: string,
    bounceReason: string,
    bounceDate?: string,
    bounceCharges?: number
  ): Promise<Receipt> => {
    const response = await api.post(`${BASE_URL}/receipts/${receiptId}/bounce`, null, {
      params: {
        bounce_reason: bounceReason,
        bounce_date: bounceDate,
        bounce_charges: bounceCharges,
      },
    });
    return response.data;
  },
};

// ============== Disbursement API ==============

export const disbursementApi = {
  createDisbursement: async (params: DisbursementCreateParams): Promise<Disbursement> => {
    const response = await api.post(`${BASE_URL}/disbursements`, params);
    return response.data;
  },

  verifyConditions: async (disbursementId: string, notes?: string): Promise<any> => {
    const response = await api.post(`${BASE_URL}/disbursements/verify-conditions`, {
      disbursement_id: disbursementId,
      verification_notes: notes,
    });
    return response.data;
  },

  approveDisbursement: async (
    disbursementId: string,
    approvedAmount?: number,
    remarks?: string
  ): Promise<any> => {
    const response = await api.post(`${BASE_URL}/disbursements/approve`, {
      disbursement_id: disbursementId,
      approved_amount: approvedAmount,
      remarks,
    });
    return response.data;
  },

  rejectDisbursement: async (disbursementId: string, reason: string): Promise<any> => {
    const response = await api.post(`${BASE_URL}/disbursements/reject`, {
      disbursement_id: disbursementId,
      rejection_reason: reason,
    });
    return response.data;
  },

  processDisbursement: async (params: DisbursementProcessParams): Promise<any> => {
    const response = await api.post(`${BASE_URL}/disbursements/process`, params);
    return response.data;
  },

  cancelDisbursement: async (disbursementId: string, reason: string): Promise<any> => {
    const response = await api.post(`${BASE_URL}/disbursements/cancel`, null, {
      params: { disbursement_id: disbursementId, cancellation_reason: reason },
    });
    return response.data;
  },

  reverseDisbursement: async (
    disbursementId: string,
    reason: string,
    reversalDate?: string
  ): Promise<any> => {
    const response = await api.post(`${BASE_URL}/disbursements/reverse`, {
      disbursement_id: disbursementId,
      reversal_reason: reason,
      reversal_date: reversalDate,
    });
    return response.data;
  },

  createTranches: async (loanAccountId: string, tranches: TrancheItem[]): Promise<any> => {
    const response = await api.post(`${BASE_URL}/disbursements/tranches`, {
      loan_account_id: loanAccountId,
      tranches,
    });
    return response.data;
  },

  getDisbursementsByLoan: async (
    loanAccountId: string,
    status?: string
  ): Promise<{ loan_account_id: string; count: number; disbursements: Disbursement[] }> => {
    const response = await api.get(`${BASE_URL}/disbursements/loan/${loanAccountId}`, {
      params: { status },
    });
    return response.data;
  },

  getPendingDisbursements: async (
    status?: string
  ): Promise<{ organizationId: string; count: number; disbursements: Record<string, unknown>[] }> => {
    const response = await api.get(`${BASE_URL}/disbursements/pending`, {
      params: { status },
    });
    return response.data;
  },

  getSummary: async (
    fromDate?: string,
    toDate?: string
  ): Promise<DisbursementSummary> => {
    const response = await api.get(`${BASE_URL}/disbursements/summary`, {
      params: { from_date: fromDate, to_date: toDate },
    });
    return response.data;
  },
};

// ============== Collateral API ==============

export const collateralApi = {
  createCollateral: async (params: CollateralCreateParams): Promise<Collateral> => {
    const response = await api.post(`${BASE_URL}/collaterals`, params);
    return response.data;
  },

  updateValuation: async (
    securityId: string,
    marketValue: number,
    forcedSaleValue?: number,
    acceptableValue?: number,
    valuationDate?: string,
    valuerName?: string,
    valuerFirm?: string,
    reportPath?: string,
    nextValuationDate?: string
  ): Promise<Collateral> => {
    const response = await api.put(`${BASE_URL}/collaterals/valuation`, {
      security_id: securityId,
      market_value: marketValue,
      forced_sale_value: forcedSaleValue,
      acceptable_value: acceptableValue,
      valuation_date: valuationDate,
      valuer_name: valuerName,
      valuer_firm: valuerFirm,
      report_path: reportPath,
      next_valuation_date: nextValuationDate,
    });
    return response.data;
  },

  releaseCollateral: async (
    securityId: string,
    releaseReason: string,
    releaseDate?: string,
    releaseTo?: string
  ): Promise<Collateral> => {
    const response = await api.post(`${BASE_URL}/collaterals/release`, {
      security_id: securityId,
      release_reason: releaseReason,
      release_date: releaseDate,
      release_to: releaseTo,
    });
    return response.data;
  },

  substituteCollateral: async (
    oldSecurityId: string,
    newSecurity: CollateralCreateParams,
    substitutionReason: string
  ): Promise<{ old_security_id: string; new_security_id: string }> => {
    const response = await api.post(`${BASE_URL}/collaterals/substitute`, {
      old_security_id: oldSecurityId,
      new_security: newSecurity,
      substitution_reason: substitutionReason,
    });
    return response.data;
  },

  getCoverage: async (sanctionId: string, includeReleased = false): Promise<SecurityCoverage> => {
    const response = await api.get(`${BASE_URL}/collaterals/coverage/${sanctionId}`, {
      params: { include_released: includeReleased },
    });
    return response.data;
  },

  getCollateralsByLoan: async (
    loanAccountId: string
  ): Promise<{ loan_account_id: string; count: number; securities: Collateral[] }> => {
    const response = await api.get(`${BASE_URL}/collaterals/loan/${loanAccountId}`);
    return response.data;
  },

  getDueForValuation: async (
    daysAhead = 30
  ): Promise<{ organizationId: string; count: number; securities: Record<string, unknown>[] }> => {
    const response = await api.get(`${BASE_URL}/collaterals/due-valuation`, {
      params: { days_ahead: daysAhead },
    });
    return response.data;
  },

  addEncumbrance: async (
    securityId: string,
    chargeHolder: string,
    chargeAmount: number,
    chargeDate?: string,
    chargeReference?: string
  ): Promise<Collateral> => {
    const response = await api.post(`${BASE_URL}/collaterals/encumbrance`, {
      security_id: securityId,
      charge_holder: chargeHolder,
      charge_amount: chargeAmount,
      charge_date: chargeDate,
      charge_reference: chargeReference,
    });
    return response.data;
  },

  recordChargeCreation: async (
    securityId: string,
    chargeCreationDate: string,
    chargeId?: string,
    rocFilingDate?: string,
    rocFilingSrn?: string,
    cersaiRegistrationDate?: string,
    cersaiTransactionId?: string
  ): Promise<Collateral> => {
    const response = await api.post(`${BASE_URL}/collaterals/charge`, {
      security_id: securityId,
      charge_creation_date: chargeCreationDate,
      charge_id: chargeId,
      roc_filing_date: rocFilingDate,
      roc_filing_srn: rocFilingSrn,
      cersai_registration_date: cersaiRegistrationDate,
      cersai_transaction_id: cersaiTransactionId,
    });
    return response.data;
  },

  getSummary: async (): Promise<CollateralSummary> => {
    const response = await api.get(`${BASE_URL}/collaterals/summary`, {
      params: {},
    });
    return response.data;
  },
};
