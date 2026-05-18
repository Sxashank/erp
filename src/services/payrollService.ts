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
  calculation_type: 'FIXED' | 'PERCENTAGE' | 'FORMULA' | 'PERCENTAGE_OF_BASIC' | 'PERCENTAGE_OF_GROSS' | 'PERCENTAGE_OF_CTC';
  default_value?: number;
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
  effective_from: string;
  effective_to?: string;
  payment_mode?: string;
  pay_frequency?: string;
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
  calculation_type: 'FIXED' | 'PERCENTAGE' | 'FORMULA' | 'PERCENTAGE_OF_BASIC' | 'PERCENTAGE_OF_GROSS' | 'PERCENTAGE_OF_CTC';
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
  pf_employer_rate?: number;
  pf_employee_rate?: number;
  pf_admin_charge_rate?: number;
  pf_edli_rate?: number;
  pf_wage_ceiling?: number;
  eps_employer_rate?: number;
  eps_wage_ceiling?: number;
  esi_employer_rate?: number;
  esi_employee_rate?: number;
  esi_wage_ceiling?: number;
  pt_state?: string;
  pt_slabs?: Record<string, unknown>;
  lwf_employer_contribution?: number;
  lwf_employee_contribution?: number;
  lwf_frequency?: string;
  employer_contribution_pct?: number;
  employee_contribution_pct?: number;
  wage_ceiling?: number;
  admin_charges_pct?: number;
  is_applicable: boolean;
  effective_from: string;
  effective_to?: string;
  config_data?: Record<string, unknown>;
  created_at: string;
}

export interface PayrollBatch {
  id: string;
  organization_id: string;
  batch_reference: string;
  batch_number?: string;
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
  total_employer_statutory?: number;
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
  total_earnings?: number;
  status: 'DRAFT' | 'GENERATED' | 'PROCESSED' | 'APPROVED' | 'PAID' | 'CANCELLED';
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

export interface PayrollBankFile {
  file_name: string;
  file_content: string;
  record_count: number;
  total_amount: number;
  generated_at: string;
}

export interface PayrollGLPostRequest {
  salary_expense_account_id: string;
  net_salary_payable_account_id: string;
  pf_payable_account_id?: string;
  esi_payable_account_id?: string;
  pt_payable_account_id?: string;
  tds_payable_account_id?: string;
  other_deductions_payable_account_id?: string;
  employer_contribution_expense_account_id?: string;
  voucher_date?: string;
  cost_center_id?: string;
  narration?: string;
}

export interface PayrollGLPostResult {
  posted: boolean;
  source_reference: string;
  gl_entry_count: number;
  voucher_number?: string;
  total_debit: number;
  total_credit: number;
}

// Backend payroll payloads use slightly different field names across phases of
// the rollout; each normalizer accepts an unknown-value object and projects it
// to the shape the UI consumes.
type RawPayload = Record<string, unknown>;

function normalizeComponentCalculation(raw: RawPayload) {
  const calculationType = String(raw.calculation_type ?? 'FIXED');
  if (calculationType.startsWith('PERCENTAGE_OF_')) {
    return {
      calculation_type: 'PERCENTAGE' as const,
      percentage_of: calculationType.replace('PERCENTAGE_OF_', ''),
      percentage_value: Number(raw.default_value ?? raw.value ?? raw.percentage_value ?? 0),
    };
  }
  return {
    calculation_type: calculationType as SalaryComponent['calculation_type'],
    percentage_of: raw.percentage_of as string | undefined,
    percentage_value: raw.percentage_value as number | undefined,
  };
}

function toBackendCalculationType(input: {
  calculation_type?: string;
  percentage_of?: string;
}) {
  if (input.calculation_type === 'PERCENTAGE') {
    const base = String(input.percentage_of || 'BASIC').toUpperCase();
    return `PERCENTAGE_OF_${base}`;
  }
  return input.calculation_type;
}

function normalizeSalaryComponent(raw: RawPayload): SalaryComponent {
  return {
    ...(raw as unknown as SalaryComponent),
    ...normalizeComponentCalculation(raw),
    default_value: raw.default_value == null ? undefined : Number(raw.default_value),
  };
}

function salaryComponentToApi(data: Partial<SalaryComponent>) {
  return {
    ...data,
    calculation_type: toBackendCalculationType(data),
    default_value:
      data.calculation_type === 'PERCENTAGE'
        ? data.percentage_value
        : data.default_value ?? data.percentage_value,
    percentage_of: undefined,
    percentage_value: undefined,
  };
}

function normalizeSalaryStructureComponent(raw: RawPayload): SalaryStructureComponent {
  const calculation = normalizeComponentCalculation(raw);
  return {
    ...(raw as unknown as SalaryStructureComponent),
    ...calculation,
    default_value: (raw.default_value == null ? raw.value : raw.default_value) as number | undefined,
    component: raw.component
      ? normalizeSalaryComponent(raw.component as RawPayload)
      : (raw.component as SalaryComponent | undefined),
  };
}

function normalizeSalaryStructure(raw: RawPayload): SalaryStructure {
  const components = Array.isArray(raw.components) ? (raw.components as RawPayload[]) : [];
  return {
    ...(raw as unknown as SalaryStructure),
    components: components.map(normalizeSalaryStructureComponent),
  };
}

function salaryStructureComponentToApi(data: Partial<SalaryStructureComponent>) {
  const calculationType = toBackendCalculationType(data);
  return {
    component_id: data.component_id,
    calculation_type: calculationType,
    value:
      data.calculation_type === 'PERCENTAGE'
        ? data.percentage_value
        : data.default_value ?? data.percentage_value,
    formula: data.formula || undefined,
    is_mandatory: data.is_mandatory ?? true,
  };
}

type SalaryStructureInput = Omit<Partial<SalaryStructure>, 'components'> & {
  components?: Partial<SalaryStructureComponent>[];
};

function salaryStructureToApi(data: SalaryStructureInput) {
  return {
    organization_id: data.organization_id,
    structure_code: data.structure_code,
    structure_name: data.structure_name,
    description: data.description || undefined,
    effective_from: data.effective_from,
    effective_to: data.effective_to || undefined,
    payment_mode: data.payment_mode ?? 'BANK',
    pay_frequency: data.pay_frequency ?? 'MONTHLY',
    is_active: data.is_active ?? true,
    components: (data.components ?? []).map(salaryStructureComponentToApi),
  };
}

function normalizeEmployeeSalary(raw: RawPayload): EmployeeSalary {
  const employeeName = String(raw.employee_name ?? '').trim();
  const [firstName = employeeName, ...lastNameParts] = employeeName.split(' ');

  return {
    ...(raw as unknown as EmployeeSalary),
    gross_salary: Number(raw.gross_salary ?? raw.monthly_gross ?? 0),
    net_salary: Number(raw.net_salary ?? raw.monthly_net ?? 0),
    ctc: Number(raw.ctc ?? raw.monthly_ctc ?? raw.annual_ctc ?? 0),
    employee: (raw.employee as EmployeeSalary['employee']) ?? {
      id: String(raw.employee_id ?? ''),
      employee_code: String(raw.employee_code ?? ''),
      first_name: firstName,
      last_name: lastNameParts.join(' '),
    },
  };
}

function normalizePayrollBatch(raw: RawPayload): PayrollBatch {
  return {
    ...(raw as unknown as PayrollBatch),
    batch_reference: String(raw.batch_reference ?? raw.batch_number ?? ''),
    total_employer_contribution: Number(
      raw.total_employer_contribution ?? raw.total_employer_statutory ?? 0,
    ),
  };
}

function normalizePayslip(raw: RawPayload): Payslip {
  const employeeName = String(raw.employee_name ?? '').trim();
  const [firstName = employeeName, ...lastNameParts] = employeeName.split(' ');

  return {
    ...(raw as unknown as Payslip),
    gross_earnings: Number(raw.gross_earnings ?? raw.total_earnings ?? raw.gross_salary ?? 0),
    employee: (raw.employee as Payslip['employee']) ?? {
      id: String(raw.employee_id ?? ''),
      employee_code: String(raw.employee_code ?? ''),
      first_name: firstName,
      last_name: lastNameParts.join(' '),
    },
  };
}

function normalizeStatutorySetup(raw: RawPayload): StatutorySetup {
  const statutoryType = raw.statutory_type;
  const employerContribution =
    statutoryType === 'PF'
      ? raw.pf_employer_rate
      : statutoryType === 'ESI'
        ? raw.esi_employer_rate
        : statutoryType === 'LWF'
          ? raw.lwf_employer_contribution
          : undefined;
  const employeeContribution =
    statutoryType === 'PF'
      ? raw.pf_employee_rate
      : statutoryType === 'ESI'
        ? raw.esi_employee_rate
        : statutoryType === 'LWF'
          ? raw.lwf_employee_contribution
          : undefined;
  const wageCeiling =
    statutoryType === 'PF'
      ? raw.pf_wage_ceiling
      : statutoryType === 'ESI'
        ? raw.esi_wage_ceiling
        : undefined;

  return {
    ...(raw as unknown as StatutorySetup),
    employer_contribution_pct:
      employerContribution == null ? undefined : Number(employerContribution),
    employee_contribution_pct:
      employeeContribution == null ? undefined : Number(employeeContribution),
    wage_ceiling: wageCeiling == null ? undefined : Number(wageCeiling),
    admin_charges_pct:
      raw.pf_admin_charge_rate == null ? undefined : Number(raw.pf_admin_charge_rate),
    is_applicable: (raw.is_active as boolean | undefined) ?? true,
  };
}

function statutorySetupToApi(data: Partial<StatutorySetup>) {
  const payload: Record<string, unknown> = {
    organization_id: data.organization_id,
    statutory_type: data.statutory_type,
    effective_from: data.effective_from,
    effective_to: data.effective_to || undefined,
    is_active: data.is_applicable ?? true,
  };

  if (data.statutory_type === 'PF') {
    payload.pf_employer_rate = data.employer_contribution_pct;
    payload.pf_employee_rate = data.employee_contribution_pct;
    payload.pf_wage_ceiling = data.wage_ceiling;
    payload.pf_admin_charge_rate = data.admin_charges_pct;
    payload.pf_edli_rate = data.pf_edli_rate;
    payload.eps_employer_rate = data.eps_employer_rate;
    payload.eps_wage_ceiling = data.eps_wage_ceiling ?? data.wage_ceiling;
  }

  if (data.statutory_type === 'ESI') {
    payload.esi_employer_rate = data.employer_contribution_pct;
    payload.esi_employee_rate = data.employee_contribution_pct;
    payload.esi_wage_ceiling = data.wage_ceiling;
  }

  if (data.statutory_type === 'PT') {
    payload.pt_state = data.pt_state;
    payload.pt_slabs = data.pt_slabs;
  }

  if (data.statutory_type === 'LWF') {
    payload.lwf_employer_contribution = data.employer_contribution_pct;
    payload.lwf_employee_contribution = data.employee_contribution_pct;
    payload.lwf_frequency = data.lwf_frequency;
  }

  return payload;
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
    return {
      ...response.data,
      items: (response.data.items ?? []).map(normalizeSalaryComponent),
    };
  }

  async getComponent(id: string): Promise<SalaryComponent> {
    const response = await api.get(`/payroll/components/${id}`);
    return normalizeSalaryComponent(response.data);
  }

  async createComponent(data: Partial<SalaryComponent>): Promise<SalaryComponent> {
    const response = await api.post('/payroll/components', salaryComponentToApi(data));
    return normalizeSalaryComponent(response.data);
  }

  async updateComponent(id: string, data: Partial<SalaryComponent>): Promise<SalaryComponent> {
    const response = await api.put(`/payroll/components/${id}`, salaryComponentToApi(data));
    return normalizeSalaryComponent(response.data);
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
    return {
      ...response.data,
      items: (response.data.items ?? []).map(normalizeSalaryStructure),
    };
  }

  async getStructure(id: string): Promise<SalaryStructure> {
    const response = await api.get(`/payroll/structures/${id}`);
    return normalizeSalaryStructure(response.data);
  }

  async createStructure(data: SalaryStructureInput & { components: Partial<SalaryStructureComponent>[] }): Promise<SalaryStructure> {
    const response = await api.post('/payroll/structures', salaryStructureToApi(data));
    return normalizeSalaryStructure(response.data);
  }

  async updateStructure(id: string, data: SalaryStructureInput): Promise<SalaryStructure> {
    const response = await api.put(`/payroll/structures/${id}`, salaryStructureToApi(data));
    return normalizeSalaryStructure(response.data);
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
    return {
      ...response.data,
      items: (response.data.items ?? []).map(normalizeEmployeeSalary),
    };
  }

  async getEmployeeSalary(id: string): Promise<EmployeeSalary> {
    const response = await api.get(`/payroll/employee-salaries/${id}`);
    return normalizeEmployeeSalary(response.data);
  }

  async getCurrentEmployeeSalary(employeeId: string): Promise<EmployeeSalary> {
    const response = await api.get(`/payroll/employee-salaries/employee/${employeeId}/current`);
    return normalizeEmployeeSalary(response.data);
  }

  async createEmployeeSalary(data: Partial<EmployeeSalary> & {
    components: Partial<EmployeeSalaryComponent>[];
  }): Promise<EmployeeSalary> {
    const response = await api.post('/payroll/employee-salaries', data);
    return normalizeEmployeeSalary(response.data);
  }

  // ============== Statutory Setup ==============

  async listStatutorySetup(params: {
    organization_id: string;
    statutory_type?: string;
  }): Promise<StatutorySetup[]> {
    const response = await api.get('/payroll/statutory-setup', { params });
    return (response.data ?? []).map(normalizeStatutorySetup);
  }

  async getStatutorySetup(id: string): Promise<StatutorySetup> {
    const response = await api.get(`/payroll/statutory-setup/${id}`);
    return normalizeStatutorySetup(response.data);
  }

  async createStatutorySetup(data: Partial<StatutorySetup>): Promise<StatutorySetup> {
    const response = await api.post('/payroll/statutory-setup', statutorySetupToApi(data));
    return normalizeStatutorySetup(response.data);
  }

  async updateStatutorySetup(id: string, data: Partial<StatutorySetup>): Promise<StatutorySetup> {
    const response = await api.put(`/payroll/statutory-setup/${id}`, statutorySetupToApi(data));
    return normalizeStatutorySetup(response.data);
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
    return {
      ...response.data,
      items: (response.data.items ?? []).map(normalizePayrollBatch),
    };
  }

  async getBatch(id: string): Promise<PayrollBatch> {
    const response = await api.get(`/payroll/batches/${id}`);
    return normalizePayrollBatch(response.data);
  }

  async createBatch(data: Partial<PayrollBatch>): Promise<PayrollBatch> {
    const response = await api.post('/payroll/batches', data);
    return normalizePayrollBatch(response.data);
  }

  async updateBatch(id: string, data: Partial<PayrollBatch>): Promise<PayrollBatch> {
    const response = await api.put(`/payroll/batches/${id}`, data);
    return normalizePayrollBatch(response.data);
  }

  async processBatch(id: string, employeeIds?: string[]): Promise<PayrollBatch> {
    const response = await api.post(`/payroll/batches/${id}/process`, {
      employee_ids: employeeIds,
    });
    return normalizePayrollBatch(response.data);
  }

  async approveBatch(id: string, remarks?: string): Promise<PayrollBatch> {
    const response = await api.post(`/payroll/batches/${id}/approve`, { remarks });
    return normalizePayrollBatch(response.data);
  }

  async markBatchPaid(id: string, paymentReference?: string): Promise<PayrollBatch> {
    const response = await api.post(`/payroll/batches/${id}/mark-paid`, {
      payment_reference: paymentReference,
    });
    return normalizePayrollBatch(response.data);
  }

  async exportBankFile(id: string): Promise<PayrollBankFile> {
    const response = await api.get(`/payroll/batches/${id}/bank-file`);
    return response.data;
  }

  async postBatchToGL(id: string, data: PayrollGLPostRequest): Promise<PayrollGLPostResult> {
    const response = await api.post(`/payroll/batches/${id}/post-gl`, data);
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
    return {
      ...response.data,
      items: (response.data.items ?? []).map(normalizePayslip),
    };
  }

  async getPayslip(id: string): Promise<Payslip> {
    const response = await api.get(`/payroll/payslips/${id}`);
    return normalizePayslip(response.data);
  }

  async updatePayslip(id: string, data: Partial<Payslip>): Promise<Payslip> {
    const response = await api.put(`/payroll/payslips/${id}`, data);
    return normalizePayslip(response.data);
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
    return {
      ...response.data,
      items: (response.data.items ?? []).map(normalizePayslip),
    };
  }
}

export const payrollService = new PayrollService();
export default payrollService;
