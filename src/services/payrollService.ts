/**
 * Payroll Service
 * API client for payroll operations
 */

import api from './api';

// Types
export interface SalaryComponent {
  id: string;
  organization_id: string;
  component_code: string;
  component_name: string;
  component_type: 'EARNING' | 'DEDUCTION';
  category: 'BASIC' | 'ALLOWANCE' | 'REIMBURSEMENT' | 'BONUS' | 'STATUTORY' | 'OTHER';
  calculation_type: 'FIXED' | 'PERCENTAGE' | 'FORMULA';
  percentage_of?: string;
  percentage_value?: number;
  formula?: string;
  is_taxable: boolean;
  is_pro_rated: boolean;
  affects_pf: boolean;
  affects_esi: boolean;
  affects_pt: boolean;
  display_order: number;
  is_active: boolean;
  created_at: string;
}

export interface SalaryStructure {
  id: string;
  organization_id: string;
  structure_code: string;
  structure_name: string;
  description?: string;
  ctc_from?: number;
  ctc_to?: number;
  is_active: boolean;
  components?: SalaryStructureComponent[];
  created_at: string;
}

export interface SalaryStructureComponent {
  id: string;
  structure_id: string;
  component_id: string;
  component?: SalaryComponent;
  calculation_type: 'FIXED' | 'PERCENTAGE' | 'FORMULA';
  default_value?: number;
  percentage_of?: string;
  percentage_value?: number;
  formula?: string;
  is_mandatory: boolean;
}

export interface EmployeeSalary {
  id: string;
  employee_id: string;
  employee?: {
    id: string;
    employee_code: string;
    first_name: string;
    last_name: string;
  };
  structure_id?: string;
  structure?: SalaryStructure;
  effective_from: string;
  effective_to?: string;
  gross_salary: number;
  net_salary: number;
  ctc: number;
  status: 'ACTIVE' | 'SUPERSEDED' | 'DRAFT';
  revision_number: number;
  components?: EmployeeSalaryComponent[];
  created_at: string;
}

export interface EmployeeSalaryComponent {
  id: string;
  employee_salary_id: string;
  component_id: string;
  component?: SalaryComponent;
  amount: number;
  calculation_type: 'FIXED' | 'PERCENTAGE' | 'FORMULA';
  percentage_value?: number;
}

export interface StatutorySetup {
  id: string;
  organization_id: string;
  statutory_type: 'PF' | 'ESI' | 'PT' | 'LWF' | 'GRATUITY';
  employer_contribution_pct?: number;
  employee_contribution_pct?: number;
  wage_ceiling?: number;
  admin_charges_pct?: number;
  is_applicable: boolean;
  effective_from: string;
  config_data?: Record<string, any>;
  created_at: string;
}

export interface PayrollBatch {
  id: string;
  organization_id: string;
  batch_reference: string;
  payroll_month: number;
  payroll_year: number;
  pay_period_from: string;
  pay_period_to: string;
  status: 'DRAFT' | 'PROCESSING' | 'PROCESSED' | 'APPROVED' | 'PAID' | 'CANCELLED';
  total_employees: number;
  total_gross: number;
  total_deductions: number;
  total_net: number;
  total_employer_contribution: number;
  processed_at?: string;
  processed_by?: string;
  approved_at?: string;
  approved_by?: string;
  paid_at?: string;
  paid_by?: string;
  remarks?: string;
  created_at: string;
}

export interface Payslip {
  id: string;
  batch_id: string;
  batch?: PayrollBatch;
  employee_id: string;
  employee?: {
    id: string;
    employee_code: string;
    first_name: string;
    last_name: string;
    department?: { department_name: string };
  };
  employee_salary_id: string;
  payroll_month: number;
  payroll_year: number;
  working_days: number;
  paid_days: number;
  lop_days: number;
  basic_salary: number;
  gross_earnings: number;
  total_deductions: number;
  net_salary: number;
  employer_pf?: number;
  employer_esi?: number;
  status: 'DRAFT' | 'PROCESSED' | 'APPROVED' | 'PAID' | 'CANCELLED';
  components?: PayslipComponent[];
  statutory?: PayrollStatutory[];
  created_at: string;
}

export interface PayslipComponent {
  id: string;
  payslip_id: string;
  component_id: string;
  component?: SalaryComponent;
  component_name: string;
  component_type: 'EARNING' | 'DEDUCTION';
  amount: number;
  is_arrear: boolean;
}

export interface PayrollStatutory {
  id: string;
  payslip_id: string;
  statutory_type: 'PF' | 'ESI' | 'PT' | 'TDS' | 'LWF';
  employee_amount: number;
  employer_amount: number;
  wage_base: number;
  remarks?: string;
}

// Service class
class PayrollService {
  // ============== Salary Components ==============

  async listComponents(params: {
    organization_id: string;
    component_type?: string;
    category?: string;
    active_only?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<{ items: SalaryComponent[]; total: number }> {
    const response = await api.get('/payroll/components', { params });
    return response.data;
  }

  async getComponent(id: string): Promise<SalaryComponent> {
    const response = await api.get(`/payroll/components/${id}`);
    return response.data;
  }

  async createComponent(data: Partial<SalaryComponent>): Promise<SalaryComponent> {
    const response = await api.post('/payroll/components', data);
    return response.data;
  }

  async updateComponent(id: string, data: Partial<SalaryComponent>): Promise<SalaryComponent> {
    const response = await api.put(`/payroll/components/${id}`, data);
    return response.data;
  }

  async deleteComponent(id: string): Promise<void> {
    await api.delete(`/payroll/components/${id}`);
  }

  // ============== Salary Structures ==============

  async listStructures(params: {
    organization_id: string;
    active_only?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<{ items: SalaryStructure[]; total: number }> {
    const response = await api.get('/payroll/structures', { params });
    return response.data;
  }

  async getStructure(id: string): Promise<SalaryStructure> {
    const response = await api.get(`/payroll/structures/${id}`);
    return response.data;
  }

  async createStructure(data: Partial<SalaryStructure> & {
    components: Partial<SalaryStructureComponent>[];
  }): Promise<SalaryStructure> {
    const response = await api.post('/payroll/structures', data);
    return response.data;
  }

  async updateStructure(id: string, data: Partial<SalaryStructure> & {
    components?: Partial<SalaryStructureComponent>[];
  }): Promise<SalaryStructure> {
    const response = await api.put(`/payroll/structures/${id}`, data);
    return response.data;
  }

  async deleteStructure(id: string): Promise<void> {
    await api.delete(`/payroll/structures/${id}`);
  }

  // ============== Employee Salaries ==============

  async listEmployeeSalaries(params: {
    employee_id?: string;
    active_only?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<{ items: EmployeeSalary[]; total: number }> {
    const response = await api.get('/payroll/employee-salaries', { params });
    return response.data;
  }

  async getEmployeeSalary(id: string): Promise<EmployeeSalary> {
    const response = await api.get(`/payroll/employee-salaries/${id}`);
    return response.data;
  }

  async getCurrentEmployeeSalary(employeeId: string): Promise<EmployeeSalary> {
    const response = await api.get(`/payroll/employee-salaries/employee/${employeeId}/current`);
    return response.data;
  }

  async createEmployeeSalary(data: Partial<EmployeeSalary> & {
    components: Partial<EmployeeSalaryComponent>[];
  }): Promise<EmployeeSalary> {
    const response = await api.post('/payroll/employee-salaries', data);
    return response.data;
  }

  // ============== Statutory Setup ==============

  async listStatutorySetup(params: {
    organization_id: string;
    statutory_type?: string;
  }): Promise<StatutorySetup[]> {
    const response = await api.get('/payroll/statutory-setup', { params });
    return response.data;
  }

  async getStatutorySetup(id: string): Promise<StatutorySetup> {
    const response = await api.get(`/payroll/statutory-setup/${id}`);
    return response.data;
  }

  async createStatutorySetup(data: Partial<StatutorySetup>): Promise<StatutorySetup> {
    const response = await api.post('/payroll/statutory-setup', data);
    return response.data;
  }

  async updateStatutorySetup(id: string, data: Partial<StatutorySetup>): Promise<StatutorySetup> {
    const response = await api.put(`/payroll/statutory-setup/${id}`, data);
    return response.data;
  }

  // ============== Payroll Batches ==============

  async listBatches(params: {
    organization_id: string;
    year?: number;
    status?: string;
    skip?: number;
    limit?: number;
  }): Promise<{ items: PayrollBatch[]; total: number }> {
    const response = await api.get('/payroll/batches', { params });
    return response.data;
  }

  async getBatch(id: string): Promise<PayrollBatch> {
    const response = await api.get(`/payroll/batches/${id}`);
    return response.data;
  }

  async createBatch(data: Partial<PayrollBatch>): Promise<PayrollBatch> {
    const response = await api.post('/payroll/batches', data);
    return response.data;
  }

  async updateBatch(id: string, data: Partial<PayrollBatch>): Promise<PayrollBatch> {
    const response = await api.put(`/payroll/batches/${id}`, data);
    return response.data;
  }

  async processBatch(id: string, employeeIds?: string[]): Promise<PayrollBatch> {
    const response = await api.post(`/payroll/batches/${id}/process`, {
      employee_ids: employeeIds,
    });
    return response.data;
  }

  async approveBatch(id: string, remarks?: string): Promise<PayrollBatch> {
    const response = await api.post(`/payroll/batches/${id}/approve`, { remarks });
    return response.data;
  }

  async markBatchPaid(id: string): Promise<PayrollBatch> {
    const response = await api.post(`/payroll/batches/${id}/mark-paid`);
    return response.data;
  }

  // ============== Payslips ==============

  async listPayslips(params: {
    batch_id?: string;
    employee_id?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }): Promise<{ items: Payslip[]; total: number }> {
    const response = await api.get('/payroll/payslips', { params });
    return response.data;
  }

  async getPayslip(id: string): Promise<Payslip> {
    const response = await api.get(`/payroll/payslips/${id}`);
    return response.data;
  }

  async updatePayslip(id: string, data: Partial<Payslip>): Promise<Payslip> {
    const response = await api.put(`/payroll/payslips/${id}`, data);
    return response.data;
  }

  async getEmployeePayslips(params: {
    employee_id: string;
    year?: number;
    skip?: number;
    limit?: number;
  }): Promise<{ items: Payslip[]; total: number }> {
    const response = await api.get(`/payroll/payslips/employee/${params.employee_id}`, {
      params: {
        year: params.year,
        skip: params.skip,
        limit: params.limit,
      },
    });
    return response.data;
  }
}

export const payrollService = new PayrollService();
export default payrollService;
