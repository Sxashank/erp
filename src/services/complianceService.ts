/**
 * Compliance Service
 * API client for compliance operations
 */

import api from './api';

// Types
export interface ComplianceItem {
  id: string;
  organization_id: string;
  item_code: string;
  item_name: string;
  description?: string;
  regulatory_body: 'RBI' | 'SEBI' | 'MCA' | 'GST' | 'INCOME_TAX' | 'EPFO' | 'ESIC' | 'STATE' | 'OTHER';
  regulation_reference?: string;
  section_reference?: string;
  frequency: 'DAILY' | 'WEEKLY' | 'MONTHLY' | 'QUARTERLY' | 'HALF_YEARLY' | 'ANNUALLY' | 'AS_REQUIRED' | 'ONE_TIME';
  due_day?: number;
  due_month?: number;
  grace_days: number;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  penalty_type?: string;
  penalty_amount?: number;
  penalty_rate_per_day?: number;
  responsible_designation?: string;
  department?: string;
  required_documents?: string[];
  form_name?: string;
  filing_portal?: string;
  effective_from?: string;
  effective_to?: string;
  is_active: boolean;
  created_at: string;
}

export interface ComplianceInstance {
  id: string;
  compliance_item_id: string;
  compliance_item?: ComplianceItem;
  item_code?: string;
  item_name?: string;
  regulatory_body?: string;
  period_year: number;
  period_month?: number;
  period_quarter?: number;
  period_from?: string;
  period_to?: string;
  original_due_date: string;
  extended_due_date?: string;
  actual_due_date: string;
  status: 'NOT_DUE' | 'PENDING' | 'IN_PROGRESS' | 'PREPARED' | 'UNDER_REVIEW' | 'FILED' | 'ACKNOWLEDGED' | 'DELAYED' | 'NOT_APPLICABLE';
  filed_date?: string;
  acknowledgment_number?: string;
  acknowledgment_date?: string;
  reference_number?: string;
  is_delayed: boolean;
  delay_days?: number;
  penalty_paid?: number;
  penalty_reference?: string;
  assigned_to?: string;
  reviewer?: string;
  remarks?: string;
  internal_notes?: string;
  reminder_days?: number;
  created_at: string;
}

export interface ComplianceSummary {
  total: number;
  pending: number;
  in_progress: number;
  prepared: number;
  filed: number;
  delayed: number;
  not_applicable: number;
}

export interface ComplianceCalendarItem {
  id: string;
  item_code: string;
  item_name: string;
  regulatory_body: string;
  due_date: string;
  status: string;
  is_delayed: boolean;
}

export interface UpcomingCompliance {
  due_this_week: ComplianceCalendarItem[];
  due_this_month: ComplianceCalendarItem[];
  overdue: ComplianceCalendarItem[];
}

// Service class
class ComplianceService {
  // ============== Compliance Items ==============

  async listItems(params: {
    organization_id: string;
    regulatory_body?: string;
    frequency?: string;
    active_only?: boolean;
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
    organization_id: string;
    compliance_item_id?: string;
    regulatory_body?: string;
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
      params: { acknowledgment_number: acknowledgmentNumber },
    });
    return response.data;
  }

  // ============== Dashboard ==============

  async getSummary(params: { organization_id: string; year?: number }): Promise<ComplianceSummary> {
    const response = await api.get('/compliance/summary', { params });
    return response.data;
  }

  async getUpcoming(organization_id: string): Promise<UpcomingCompliance> {
    const response = await api.get('/compliance/upcoming', {
      params: { organization_id },
    });
    return response.data;
  }

  async generateInstances(params: {
    organization_id: string;
    year: number;
    month?: number;
  }): Promise<{ message: string; count: number }> {
    const response = await api.post('/compliance/generate-instances', null, { params });
    return response.data;
  }
}

export const complianceService = new ComplianceService();
export default complianceService;
