/**
 * Lending API Services
 * Export all lending-related API services
 */

// LOS (Loan Origination System)
export { entityApi, default as entityApiDefault } from './entityApi';
export { applicationApi, default as applicationApiDefault } from './applicationApi';
export { sanctionApi, default as sanctionApiDefault } from './sanctionApi';

// LMS (Loan Management System)
export { loanAccountApi, default as loanAccountApiDefault } from './loanAccountApi';
export { disbursementApi, default as disbursementApiDefault } from './disbursementApi';
export { receiptApi, default as receiptApiDefault } from './receiptApi';

// Collections
export { collectionApi, default as collectionApiDefault } from './collectionApi';

// Treasury
export { treasuryApi, default as treasuryApiDefault } from './treasuryApi';

// Re-export all functions for convenience
export * from './entityApi';
export * from './applicationApi';
export * from './sanctionApi';
export * from './loanAccountApi';
export * from './receiptApi';
export * from './collectionApi';

// Re-export disbursementApi (excluding getTranches to avoid conflict with treasuryApi)
export {
  getDisbursements,
  getDisbursement,
  createDisbursementRequest,
  updateDisbursementRequest,
  deleteDisbursementRequest,
  getPendingConditions,
  verifyCondition,
  submitDisbursement,
  approveDisbursement,
  initiateFundTransfer,
  getTransferStatus,
  confirmDisbursement,
  getTranches as getDisbursementTranches,
  getDisbursementsByAccount,
  uploadUtilizationCertificate,
  getUtilizationCertificates,
} from './disbursementApi';
export type { CreateDisbursementRequest } from './disbursementApi';

export * from './treasuryApi';
