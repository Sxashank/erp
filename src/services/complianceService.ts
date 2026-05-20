/**
 * Compliance Service
 * API client for compliance operations
 */

import api from './api';

// Types
export interface ComplianceItem {
  id: string;
  itemCode: string;
  itemName: string;
  description?: string;
  regulatoryBody: 'RBI' | 'SEBI' | 'MCA' | 'GST' | 'INCOME_TAX' | 'EPFO' | 'ESIC' | 'STATE' | 'OTHER';
  regulationReference?: string;
  sectionReference?: string;
  frequency: 'DAILY' | 'WEEKLY' | 'MONTHLY' | 'QUARTERLY' | 'HALF_YEARLY' | 'ANNUALLY' | 'AS_REQUIRED' | 'ONE_TIME';
  dueDay?: number;
  dueMonth?: number;
  graceDays: number;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  penaltyType?: string;
  penaltyAmount?: number;
  penaltyRatePerDay?: number;
  responsibleDesignation?: string;
  department?: string;
  requiredDocuments?: string[];
  formName?: string;
  filingPortal?: string;
  effectiveFrom?: string;
  effectiveTo?: string;
  isActive: boolean;
  createdAt: string;
}

export interface ComplianceInstance {
  id: string;
  complianceItemId: string;
  complianceItem?: ComplianceItem;
  itemCode?: string;
  itemName?: string;
  regulatoryBody?: string;
  periodYear: number;
  periodMonth?: number;
  periodQuarter?: number;
  periodFrom?: string;
  periodTo?: string;
  originalDueDate: string;
  extendedDueDate?: string;
  actualDueDate: string;
  status: 'NOT_DUE' | 'PENDING' | 'IN_PROGRESS' | 'PREPARED' | 'UNDER_REVIEW' | 'FILED' | 'ACKNOWLEDGED' | 'DELAYED' | 'NOT_APPLICABLE';
  filedDate?: string;
  acknowledgmentNumber?: string;
  acknowledgmentDate?: string;
  referenceNumber?: string;
  isDelayed: boolean;
  delayDays?: number;
  penaltyPaid?: number;
  penaltyReference?: string;
  assignedTo?: string;
  reviewer?: string;
  remarks?: string;
  internalNotes?: string;
  reminderDays?: number;
  createdAt: string;
}

export interface ComplianceSummary {
  total: number;
  pending: number;
  inProgress: number;
  prepared: number;
  filed: number;
  delayed: number;
  notApplicable: number;
}

export interface ComplianceCalendarItem {
  id: string;
  itemCode: string;
  itemName: string;
  regulatoryBody: string;
  dueDate: string;
  status: string;
  isDelayed: boolean;
}

export interface UpcomingCompliance {
  dueThisWeek: ComplianceCalendarItem[];
  dueThisMonth: ComplianceCalendarItem[];
  overdue: ComplianceCalendarItem[];
}

// Service class
class ComplianceService {
  // ============== Compliance Items ==============

  async listItems(params: {
    regulatoryBody?: string;
    frequency?: string;
    activeOnly?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<{ items: ComplianceItem[]; total: number }> {
    const response = await api.get('/compliance/items', { params });
    return response.data;
  }

  async getItem(id: string): Promise<ComplianceItem> {
    const response = await api.get(`/compliance/items/${id}`);
    return response.data;
  }

  async createItem(data: Partial<ComplianceItem>): Promise<ComplianceItem> {
    const response = await api.post('/compliance/items', data);
    return response.data;
  }

  async updateItem(id: string, data: Partial<ComplianceItem>): Promise<ComplianceItem> {
    const response = await api.put(`/compliance/items/${id}`, data);
    return response.data;
  }

  async deleteItem(id: string): Promise<void> {
    await api.delete(`/compliance/items/${id}`);
  }

  // ============== Compliance Instances ==============

  async listInstances(params: {
    complianceItemId?: string;
    regulatoryBody?: string;
    status?: string;
    year?: number;
    month?: number;
    skip?: number;
    limit?: number;
  }): Promise<{ items: ComplianceInstance[]; total: number }> {
    const response = await api.get('/compliance/instances', { params });
    return response.data;
  }

  async getInstance(id: string): Promise<ComplianceInstance> {
    const response = await api.get(`/compliance/instances/${id}`);
    return response.data;
  }

  async createInstance(data: Partial<ComplianceInstance>): Promise<ComplianceInstance> {
    const response = await api.post('/compliance/instances', data);
    return response.data;
  }

  async updateInstance(id: string, data: Partial<ComplianceInstance>): Promise<ComplianceInstance> {
    const response = await api.put(`/compliance/instances/${id}`, data);
    return response.data;
  }

  async markInstanceFiled(id: string, acknowledgmentNumber?: string): Promise<ComplianceInstance> {
    const response = await api.post(`/compliance/instances/${id}/file`, null, {
      params: { acknowledgmentNumber: acknowledgmentNumber },
    });
    return response.data;
  }

  // ============== Dashboard ==============

  async getSummary(params: { year?: number }): Promise<ComplianceSummary> {
    const response = await api.get('/compliance/summary', { params });
    return response.data;
  }

  async getUpcoming(): Promise<UpcomingCompliance> {
    const response = await api.get('/compliance/upcoming');
    return response.data;
  }

  async generateInstances(params: {
    year: number;
    month?: number;
  }): Promise<{ message: string; count: number }> {
    const response = await api.post('/compliance/generate-instances', null, { params });
    return response.data;
  }
}

export const complianceService = new ComplianceService();
export default complianceService;
