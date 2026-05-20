/**
 * Payroll Service
 * API client for payroll operations
 */

import api from './api';

// Types — wire shape is camelCase per Wave 3 of the Convention Sweep
// (`response_model_by_alias=True` everywhere). Listing types match the wire.
export interface SalaryComponent {
  id: string;
  componentCode: string;
  componentName: string;
  componentType: 'EARNING' | 'DEDUCTION';
  category: 'BASIC' | 'ALLOWANCE' | 'REIMBURSEMENT' | 'BONUS' | 'STATUTORY' | 'OTHER';
  calculationType: 'FIXED' | 'PERCENTAGE' | 'FORMULA' | 'PERCENTAGE_OF_BASIC' | 'PERCENTAGE_OF_GROSS' | 'PERCENTAGE_OF_CTC';
  defaultValue?: number;
  percentageOf?: string;
  percentageValue?: number;
  formula?: string;
  isTaxable: boolean;
  isProRated: boolean;
  affectsPf: boolean;
  affectsEsi: boolean;
  affectsPt: boolean;
  displayOrder: number;
  isActive: boolean;
  createdAt: string;
}

export interface SalaryStructure {
  id: string;
  structureCode: string;
  structureName: string;
  description?: string;
  effectiveFrom: string;
  effectiveTo?: string;
  paymentMode?: string;
  payFrequency?: string;
  ctcFrom?: number;
  ctcTo?: number;
  isActive: boolean;
  components?: SalaryStructureComponent[];
  createdAt: string;
}

export interface SalaryStructureComponent {
  id: string;
  structureId: string;
  componentId: string;
  component?: SalaryComponent;
  calculationType: 'FIXED' | 'PERCENTAGE' | 'FORMULA' | 'PERCENTAGE_OF_BASIC' | 'PERCENTAGE_OF_GROSS' | 'PERCENTAGE_OF_CTC';
  defaultValue?: number;
  percentageOf?: string;
  percentageValue?: number;
  formula?: string;
  isMandatory: boolean;
}

export interface EmployeeSalary {
  id: string;
  employeeId: string;
  employee?: {
    id: string;
    employeeCode: string;
    firstName: string;
    lastName: string;
  };
  structureId?: string;
  structure?: SalaryStructure;
  effectiveFrom: string;
  effectiveTo?: string;
  grossSalary: number;
  netSalary: number;
  ctc: number;
  status: 'ACTIVE' | 'SUPERSEDED' | 'DRAFT';
  revisionNumber: number;
  components?: EmployeeSalaryComponent[];
  createdAt: string;
}

export interface EmployeeSalaryComponent {
  id: string;
  employeeSalaryId: string;
  componentId: string;
  component?: SalaryComponent;
  amount: number;
  calculationType: 'FIXED' | 'PERCENTAGE' | 'FORMULA';
  percentageValue?: number;
}

export interface StatutorySetup {
  id: string;
  statutoryType: 'PF' | 'ESI' | 'PT' | 'LWF' | 'GRATUITY';
  pfEmployerRate?: number;
  pfEmployeeRate?: number;
  pfAdminChargeRate?: number;
  pfEdliRate?: number;
  pfWageCeiling?: number;
  epsEmployerRate?: number;
  epsWageCeiling?: number;
  esiEmployerRate?: number;
  esiEmployeeRate?: number;
  esiWageCeiling?: number;
  ptState?: string;
  ptSlabs?: Record<string, unknown>;
  lwfEmployerContribution?: number;
  lwfEmployeeContribution?: number;
  lwfFrequency?: string;
  employerContributionPct?: number;
  employeeContributionPct?: number;
  wageCeiling?: number;
  adminChargesPct?: number;
  isApplicable: boolean;
  effectiveFrom: string;
  effectiveTo?: string;
  configData?: Record<string, unknown>;
  createdAt: string;
}

export interface PayrollBatch {
  id: string;
  batchReference: string;
  batchNumber?: string;
  payrollMonth: number;
  payrollYear: number;
  payPeriodFrom: string;
  payPeriodTo: string;
  status: 'DRAFT' | 'PROCESSING' | 'PROCESSED' | 'APPROVED' | 'PAID' | 'CANCELLED';
  totalEmployees: number;
  totalGross: number;
  totalDeductions: number;
  totalNet: number;
  totalEmployerContribution: number;
  totalEmployerStatutory?: number;
  processedAt?: string;
  processedBy?: string;
  approvedAt?: string;
  approvedBy?: string;
  paidAt?: string;
  paidBy?: string;
  remarks?: string;
  createdAt: string;
}

export interface Payslip {
  id: string;
  batchId: string;
  batch?: PayrollBatch;
  employeeId: string;
  employee?: {
    id: string;
    employeeCode: string;
    firstName: string;
    lastName: string;
    department?: { departmentName: string };
  };
  employeeSalaryId: string;
  payrollMonth: number;
  payrollYear: number;
  workingDays: number;
  paidDays: number;
  lopDays: number;
  basicSalary: number;
  grossEarnings: number;
  totalDeductions: number;
  netSalary: number;
  employerPf?: number;
  employerEsi?: number;
  totalEarnings?: number;
  status: 'DRAFT' | 'GENERATED' | 'PROCESSED' | 'APPROVED' | 'PAID' | 'CANCELLED';
  components?: PayslipComponent[];
  statutory?: PayrollStatutory[];
  createdAt: string;
}

export interface PayslipComponent {
  id: string;
  payslipId: string;
  componentId: string;
  component?: SalaryComponent;
  componentName: string;
  componentType: 'EARNING' | 'DEDUCTION';
  amount: number;
  isArrear: boolean;
}

export interface PayrollStatutory {
  id: string;
  payslipId: string;
  statutoryType: 'PF' | 'ESI' | 'PT' | 'TDS' | 'LWF';
  employeeAmount: number;
  employerAmount: number;
  wageBase: number;
  remarks?: string;
}

export interface PayrollBankFile {
  fileName: string;
  fileContent: string;
  recordCount: number;
  totalAmount: number;
  generatedAt: string;
}

export interface PayrollGLPostRequest {
  salaryExpenseAccountId: string;
  netSalaryPayableAccountId: string;
  pfPayableAccountId?: string;
  esiPayableAccountId?: string;
  ptPayableAccountId?: string;
  tdsPayableAccountId?: string;
  otherDeductionsPayableAccountId?: string;
  employerContributionExpenseAccountId?: string;
  voucherDate?: string;
  costCenterId?: string;
  narration?: string;
}

export interface PayrollGLPostResult {
  posted: boolean;
  sourceReference: string;
  glEntryCount: number;
  voucherNumber?: string;
  totalDebit: number;
  totalCredit: number;
}

// Backend payroll payloads use slightly different field names across phases of
// the rollout; each normalizer accepts an unknown-value object and projects it
// to the shape the UI consumes.
type RawPayload = Record<string, unknown>;

function normalizeComponentCalculation(raw: RawPayload) {
  const calculationType = String(raw.calculationType ?? 'FIXED');
  if (calculationType.startsWith('PERCENTAGE_OF_')) {
    return {
      calculationType: 'PERCENTAGE' as const,
      percentageOf: calculationType.replace('PERCENTAGE_OF_', ''),
      percentageValue: Number(raw.defaultValue ?? raw.value ?? raw.percentageValue ?? 0),
    };
  }
  return {
    calculationType: calculationType as SalaryComponent['calculationType'],
    percentageOf: raw.percentageOf as string | undefined,
    percentageValue: raw.percentageValue as number | undefined,
  };
}

function toBackendCalculationType(input: {
  calculationType?: string;
  percentageOf?: string;
}) {
  if (input.calculationType === 'PERCENTAGE') {
    const base = String(input.percentageOf || 'BASIC').toUpperCase();
    return `PERCENTAGE_OF_${base}`;
  }
  return input.calculationType;
}

function normalizeSalaryComponent(raw: RawPayload): SalaryComponent {
  return {
    ...(raw as unknown as SalaryComponent),
    ...normalizeComponentCalculation(raw),
    defaultValue: raw.defaultValue == null ? undefined : Number(raw.defaultValue),
  };
}

function salaryComponentToApi(data: Partial<SalaryComponent>) {
  return {
    ...data,
    calculationType: toBackendCalculationType(data),
    defaultValue:
      data.calculationType === 'PERCENTAGE'
        ? data.percentageValue
        : data.defaultValue ?? data.percentageValue,
    percentageOf: undefined,
    percentageValue: undefined,
  };
}

function normalizeSalaryStructureComponent(raw: RawPayload): SalaryStructureComponent {
  const calculation = normalizeComponentCalculation(raw);
  return {
    ...(raw as unknown as SalaryStructureComponent),
    ...calculation,
    defaultValue: (raw.defaultValue == null ? raw.value : raw.defaultValue) as number | undefined,
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
    componentId: data.componentId,
    calculationType: calculationType,
    value:
      data.calculationType === 'PERCENTAGE'
        ? data.percentageValue
        : data.defaultValue ?? data.percentageValue,
    formula: data.formula || undefined,
    isMandatory: data.isMandatory ?? true,
  };
}

type SalaryStructureInput = Omit<Partial<SalaryStructure>, 'components'> & {
  components?: Partial<SalaryStructureComponent>[];
};

function salaryStructureToApi(data: SalaryStructureInput) {
  return {
    structureCode: data.structureCode,
    structureName: data.structureName,
    description: data.description || undefined,
    effectiveFrom: data.effectiveFrom,
    effectiveTo: data.effectiveTo || undefined,
    paymentMode: data.paymentMode ?? 'BANK',
    payFrequency: data.payFrequency ?? 'MONTHLY',
    isActive: data.isActive ?? true,
    components: (data.components ?? []).map(salaryStructureComponentToApi),
  };
}

function normalizeEmployeeSalary(raw: RawPayload): EmployeeSalary {
  const employeeName = String(raw.employee_name ?? '').trim();
  const [firstName = employeeName, ...lastNameParts] = employeeName.split(' ');

  return {
    ...(raw as unknown as EmployeeSalary),
    grossSalary: Number(raw.grossSalary ?? raw.monthly_gross ?? 0),
    netSalary: Number(raw.netSalary ?? raw.monthly_net ?? 0),
    ctc: Number(raw.ctc ?? raw.monthly_ctc ?? raw.annual_ctc ?? 0),
    employee: (raw.employee as EmployeeSalary['employee']) ?? {
      id: String(raw.employeeId ?? ''),
      employeeCode: String(raw.employeeCode ?? ''),
      firstName: firstName,
      lastName: lastNameParts.join(' '),
    },
  };
}

function normalizePayrollBatch(raw: RawPayload): PayrollBatch {
  return {
    ...(raw as unknown as PayrollBatch),
    batchReference: String(raw.batchReference ?? raw.batchNumber ?? ''),
    totalEmployerContribution: Number(
      raw.totalEmployerContribution ?? raw.totalEmployerStatutory ?? 0,
    ),
  };
}

function normalizePayslip(raw: RawPayload): Payslip {
  const employeeName = String(raw.employee_name ?? '').trim();
  const [firstName = employeeName, ...lastNameParts] = employeeName.split(' ');

  return {
    ...(raw as unknown as Payslip),
    grossEarnings: Number(raw.grossEarnings ?? raw.totalEarnings ?? raw.grossSalary ?? 0),
    employee: (raw.employee as Payslip['employee']) ?? {
      id: String(raw.employeeId ?? ''),
      employeeCode: String(raw.employeeCode ?? ''),
      firstName: firstName,
      lastName: lastNameParts.join(' '),
    },
  };
}

function normalizeStatutorySetup(raw: RawPayload): StatutorySetup {
  const statutoryType = raw.statutoryType;
  const employerContribution =
    statutoryType === 'PF'
      ? raw.pfEmployerRate
      : statutoryType === 'ESI'
        ? raw.esiEmployerRate
        : statutoryType === 'LWF'
          ? raw.lwfEmployerContribution
          : undefined;
  const employeeContribution =
    statutoryType === 'PF'
      ? raw.pfEmployeeRate
      : statutoryType === 'ESI'
        ? raw.esiEmployeeRate
        : statutoryType === 'LWF'
          ? raw.lwfEmployeeContribution
          : undefined;
  const wageCeiling =
    statutoryType === 'PF'
      ? raw.pfWageCeiling
      : statutoryType === 'ESI'
        ? raw.esiWageCeiling
        : undefined;

  return {
    ...(raw as unknown as StatutorySetup),
    employerContributionPct:
      employerContribution == null ? undefined : Number(employerContribution),
    employeeContributionPct:
      employeeContribution == null ? undefined : Number(employeeContribution),
    wageCeiling: wageCeiling == null ? undefined : Number(wageCeiling),
    adminChargesPct:
      raw.pfAdminChargeRate == null ? undefined : Number(raw.pfAdminChargeRate),
    isApplicable: (raw.isActive as boolean | undefined) ?? true,
  };
}

function statutorySetupToApi(data: Partial<StatutorySetup>) {
  const payload: Record<string, unknown> = {
    statutoryType: data.statutoryType,
    effectiveFrom: data.effectiveFrom,
    effectiveTo: data.effectiveTo || undefined,
    isActive: data.isApplicable ?? true,
  };

  if (data.statutoryType === 'PF') {
    payload.pfEmployerRate = data.employerContributionPct;
    payload.pfEmployeeRate = data.employeeContributionPct;
    payload.pfWageCeiling = data.wageCeiling;
    payload.pfAdminChargeRate = data.adminChargesPct;
    payload.pfEdliRate = data.pfEdliRate;
    payload.epsEmployerRate = data.epsEmployerRate;
    payload.epsWageCeiling = data.epsWageCeiling ?? data.wageCeiling;
  }

  if (data.statutoryType === 'ESI') {
    payload.esiEmployerRate = data.employerContributionPct;
    payload.esiEmployeeRate = data.employeeContributionPct;
    payload.esiWageCeiling = data.wageCeiling;
  }

  if (data.statutoryType === 'PT') {
    payload.ptState = data.ptState;
    payload.ptSlabs = data.ptSlabs;
  }

  if (data.statutoryType === 'LWF') {
    payload.lwfEmployerContribution = data.employerContributionPct;
    payload.lwfEmployeeContribution = data.employeeContributionPct;
    payload.lwfFrequency = data.lwfFrequency;
  }

  return payload;
}

// Service class
class PayrollService {
  // ============== Salary Components ==============

  async listComponents(params: {
    componentType?: string;
    category?: string;
    activeOnly?: boolean;
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
    activeOnly?: boolean;
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
    employeeId?: string;
    activeOnly?: boolean;
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
    statutoryType?: string;
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
    batchId?: string;
    employeeId?: string;
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
    employeeId: string;
    year?: number;
    skip?: number;
    limit?: number;
  }): Promise<{ items: Payslip[]; total: number }> {
    const response = await api.get(`/payroll/payslips/employee/${params.employeeId}`, {
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
