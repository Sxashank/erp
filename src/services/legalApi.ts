/**
 * Legal Module API Service
 * Handles all Legal Module API calls
 */

import api from './api';

// ==================== Law Firm APIs ====================

export const lawFirmApi = {
  getList: (params?: { search?: string; is_active?: boolean }) =>
    api.get('/legal/law-firms', { params }),

  getById: (id: string) =>
    api.get(`/legal/law-firms/${id}`),

  create: (data: {
    name: string;
    registration_number?: string;
    bar_council_id?: string;
    pan?: string;
    gstin?: string;
    address?: string;
    city?: string;
    state?: string;
    pincode?: string;
    phone?: string;
    email?: string;
    contact_person?: string;
    fee_structure?: string;
  }) =>
    api.post('/legal/law-firms', data),

  update: (id: string, data: any) =>
    api.patch(`/legal/law-firms/${id}`, data),

  delete: (id: string) =>
    api.delete(`/legal/law-firms/${id}`),
};

// ==================== Advocate APIs ====================

export const advocateApi = {
  getList: (params?: {
    search?: string;
    law_firm_id?: string;
    is_empanelled?: boolean;
    is_active?: boolean;
  }) =>
    api.get('/legal/advocates', { params }),

  getById: (id: string) =>
    api.get(`/legal/advocates/${id}`),

  create: (data: {
    law_firm_id?: string;
    name: string;
    enrollment_number: string;
    bar_council_state: string;
    specializations?: string[];
    experience_years?: number;
    mobile?: string;
    email?: string;
    fee_structure?: string;
    is_empanelled?: boolean;
  }) =>
    api.post('/legal/advocates', data),

  update: (id: string, data: any) =>
    api.patch(`/legal/advocates/${id}`, data),

  delete: (id: string) =>
    api.delete(`/legal/advocates/${id}`),

  assignToCase: (advocateId: string, data: {
    legal_case_id: string;
    role: 'LEAD' | 'ASSOCIATE';
    fee_amount?: number;
    fee_type?: 'FIXED' | 'PER_HEARING' | 'SUCCESS_FEE';
  }) =>
    api.post(`/legal/advocates/${advocateId}/assignments`, data),

  getAssignments: (advocateId: string) =>
    api.get(`/legal/advocates/${advocateId}/assignments`),

  getPerformance: (advocateId: string) =>
    api.get(`/legal/advocates/${advocateId}/performance`),
};

// ==================== Legal Notice APIs ====================

export const legalNoticeApi = {
  getList: (params?: {
    loan_account_id?: string;
    notice_type?: string;
    status?: string;
    from_date?: string;
    to_date?: string;
  }) =>
    api.get('/legal/notices', { params }),

  getById: (id: string) =>
    api.get(`/legal/notices/${id}`),

  generate: (data: {
    loan_account_id: string;
    notice_type: string;
    amount_demanded?: number;
    delivery_method: string;
    remarks?: string;
  }) =>
    api.post('/legal/notices', data),

  update: (id: string, data: any) =>
    api.patch(`/legal/notices/${id}`, data),

  downloadPdf: (id: string) =>
    api.get(`/legal/notices/${id}/pdf`, { responseType: 'blob' }),

  recordDispatch: (id: string, data: {
    dispatch_date: string;
    tracking_number: string;
    delivery_method: string;
  }) =>
    api.post(`/legal/notices/${id}/dispatch`, data),

  recordDelivery: (id: string, data: {
    delivery_date: string;
    pod_document_id?: string;
  }) =>
    api.post(`/legal/notices/${id}/delivery`, data),

  recordResponse: (id: string, data: {
    response_date: string;
    response_summary: string;
  }) =>
    api.post(`/legal/notices/${id}/response`, data),

  getOverdue: () =>
    api.get('/legal/notices/overdue'),

  getTemplates: (params?: { notice_type?: string }) =>
    api.get('/legal/notices/templates', { params }),
};

// ==================== Legal Case APIs ====================

export const legalCaseApi = {
  getList: (params?: {
    loan_account_id?: string;
    case_type?: string;
    forum_type?: string;
    status?: string;
    advocate_id?: string;
  }) =>
    api.get('/legal/cases', { params }),

  getById: (id: string) =>
    api.get(`/legal/cases/${id}`),

  create: (data: {
    loan_account_id: string;
    case_type: string;
    forum_type: string;
    court_name?: string;
    court_location?: string;
    claim_amount: number;
    advocate_id?: string;
    remarks?: string;
  }) =>
    api.post('/legal/cases', data),

  update: (id: string, data: any) =>
    api.patch(`/legal/cases/${id}`, data),

  getHearings: (caseId: string) =>
    api.get(`/legal/cases/${caseId}/hearings`),

  addHearing: (caseId: string, data: {
    hearing_date: string;
    hearing_time?: string;
    court_name: string;
    purpose: string;
    advocate_id?: string;
  }) =>
    api.post(`/legal/cases/${caseId}/hearings`, data),

  updateHearing: (caseId: string, hearingId: string, data: any) =>
    api.patch(`/legal/cases/${caseId}/hearings/${hearingId}`, data),

  getDocuments: (caseId: string) =>
    api.get(`/legal/cases/${caseId}/documents`),

  uploadDocument: (caseId: string, formData: FormData) =>
    api.post(`/legal/cases/${caseId}/documents`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
};

// ==================== SARFAESI APIs ====================

export const sarfaesiApi = {
  initiate: (data: {
    loan_account_id: string;
    notice_13_2_date?: string;
  }) =>
    api.post('/legal/sarfaesi/initiate', data),

  getTimeline: (caseId: string) =>
    api.get(`/legal/sarfaesi/${caseId}/timeline`),

  recordObjsection: (caseId: string, data: {
    objection_date: string;
    objection_summary: string;
    document_id?: string;
  }) =>
    api.post(`/legal/sarfaesi/${caseId}/objection`, data),

  takePossession: (caseId: string, data: {
    possession_date: string;
    possession_type: 'SYMBOLIC' | 'PHYSICAL';
    panchnama_document_id?: string;
  }) =>
    api.post(`/legal/sarfaesi/${caseId}/possession`, data),

  scheduleAuction: (caseId: string, data: {
    auction_date: string;
    auction_time?: string;
    reserve_price: number;
    earnest_money_deposit: number;
    auction_location: string;
    publication_details?: string;
  }) =>
    api.post(`/legal/sarfaesi/${caseId}/auction`, data),

  updateAuction: (caseId: string, auctionId: string, data: any) =>
    api.patch(`/legal/sarfaesi/${caseId}/auction/${auctionId}`, data),

  recordSale: (caseId: string, auctionId: string, data: {
    sale_amount: number;
    successful_bidder_name: string;
    sale_confirmation_date: string;
    sale_deed_date?: string;
  }) =>
    api.post(`/legal/sarfaesi/${caseId}/auction/${auctionId}/sale`, data),

  getUpcomingAuctions: () =>
    api.get('/legal/sarfaesi/upcoming-auctions'),
};

// ==================== Legal Expense APIs ====================

export const legalExpenseApi = {
  getList: (params?: {
    legal_case_id?: string;
    loan_account_id?: string;
    category?: string;
    status?: string;
    from_date?: string;
    to_date?: string;
  }) =>
    api.get('/legal/expenses', { params }),

  getById: (id: string) =>
    api.get(`/legal/expenses/${id}`),

  create: (data: {
    legal_case_id?: string;
    loan_account_id: string;
    category: string;
    description: string;
    amount: number;
    gst_amount?: number;
    expense_date: string;
    payee_name: string;
    payee_type: string;
    reference_number?: string;
    is_tds_applicable?: boolean;
  }) =>
    api.post('/legal/expenses', data),

  update: (id: string, data: any) =>
    api.patch(`/legal/expenses/${id}`, data),

  approve: (id: string, data?: { remarks?: string }) =>
    api.post(`/legal/expenses/${id}/approve`, data),

  reject: (id: string, data: { reason: string }) =>
    api.post(`/legal/expenses/${id}/reject`, data),

  recordRecovery: (id: string, data: {
    recovered_amount: number;
    recovery_date: string;
    recovery_source: 'BORROWER' | 'SALE_PROCEEDS' | 'WRITE_OFF';
  }) =>
    api.post(`/legal/expenses/${id}/recovery`, data),

  calculateCourtFee: (params: { forum_type: string; claim_amount: number }) =>
    api.get('/legal/court-fees/calculate', { params }),

  getSummary: (params?: { loan_account_id?: string; legal_case_id?: string }) =>
    api.get('/legal/expenses/summary', { params }),
};

// ==================== Statutory Period APIs ====================

export const statutoryPeriodApi = {
  getPeriods: () =>
    api.get('/legal/statutory-periods'),

  getActiveTracking: (params?: { loan_account_id?: string; status?: string }) =>
    api.get('/legal/statutory-periods/tracking', { params }),

  getUpcomingDeadlines: (days?: number) =>
    api.get('/legal/statutory-periods/deadlines', { params: { days } }),

  calculateTimeline: (data: {
    provision: string;
    start_date: string;
  }) =>
    api.post('/legal/statutory-periods/calculate', data),
};

// ==================== Legal Analytics APIs ====================

export const legalAnalyticsApi = {
  getDashboard: () =>
    api.get('/legal/analytics/dashboard'),

  getPortfolioStatus: (params?: {
    from_date?: string;
    to_date?: string;
  }) =>
    api.get('/legal/analytics/portfolio', { params }),

  getRecoveryEfficiency: (params?: {
    from_date?: string;
    to_date?: string;
    forum_type?: string;
  }) =>
    api.get('/legal/analytics/recovery', { params }),

  getForumAnalysis: () =>
    api.get('/legal/analytics/forum-wise'),

  getAgingAnalysis: () =>
    api.get('/legal/analytics/aging'),

  getMonthlyTrend: (params?: { months?: number }) =>
    api.get('/legal/analytics/monthly-trend', { params }),

  getUpcomingHearings: (days?: number) =>
    api.get('/legal/analytics/upcoming-hearings', { params: { days } }),
};

// ==================== Court APIs ====================

export const courtApi = {
  getList: (params?: { forum_type?: string; state?: string }) =>
    api.get('/legal/courts', { params }),

  getById: (id: string) =>
    api.get(`/legal/courts/${id}`),

  getFeeSlabs: (courtId: string) =>
    api.get(`/legal/courts/${courtId}/fee-slabs`),
};

export default {
  lawFirm: lawFirmApi,
  advocate: advocateApi,
  notice: legalNoticeApi,
  case: legalCaseApi,
  sarfaesi: sarfaesiApi,
  expense: legalExpenseApi,
  statutoryPeriod: statutoryPeriodApi,
  analytics: legalAnalyticsApi,
  court: courtApi,
};
