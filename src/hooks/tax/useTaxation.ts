import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  financialYearsApi,
  gstRatesApi,
  gstRegistrationsApi,
  hsnSacApi,
  organizationsApi,
  tdsChallansApi,
  tdsEntriesApi,
  tdsForm16AApi,
  tdsReturnsApi,
  tdsSectionsApi,
  unitsApi,
} from '@/services/api';
import { useActiveOrganizationId } from '@/stores/organizationStore';

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface LookupOption {
  id: string;
  code?: string;
  name: string;
}

export interface FinancialYearOption extends LookupOption {
  startDate?: string;
  endDate?: string;
  isCurrent?: boolean;
}

export interface GSTRate {
  id: string;
  code: string;
  name: string;
  rate: number;
  cgstRate: number;
  sgstRate: number;
  igstRate: number;
  cessRate: number;
  description?: string;
  effectiveFrom: string;
  effectiveTo?: string;
  isActive: boolean;
}

export interface GSTRateInput {
  code: string;
  name: string;
  rate: number;
  cgstRate: number;
  sgstRate: number;
  igstRate: number;
  cessRate: number;
  description?: string;
  effectiveFrom: string;
  effectiveTo?: string;
  isActive: boolean;
}

export interface GSTRegistration {
  id: string;
  gstin: string;
  legalName: string;
  tradeName?: string;
  registrationType: string;
  stateCode: string;
  stateName: string;
  address?: string;
  pincode?: string;
  isEInvoiceEnabled: boolean;
  eInvoiceUsername?: string;
  isEWayBillEnabled: boolean;
  organizationId: string;
  organizationName?: string;
  unitId?: string;
  unitName?: string;
  createdAt?: string;
  updatedAt?: string;
  isActive: boolean;
}

export interface GSTRegistrationInput {
  organizationId: string;
  gstin: string;
  legalName: string;
  tradeName?: string;
  registrationType: string;
  stateCode: string;
  stateName: string;
  address?: string;
  pincode?: string;
  isEInvoiceEnabled: boolean;
  eInvoiceUsername?: string;
  eInvoicePassword?: string;
  isEWayBillEnabled: boolean;
  unitId?: string;
  isActive?: boolean;
}

export interface HSNSAC {
  id: string;
  code: string;
  description: string;
  hsnSacType: string;
  chapter?: string;
  section?: string;
  gstRateId?: string;
  gstRateCode?: string;
  gstRateName?: string;
  gstRateValue?: number;
  unitOfMeasurement?: string;
  createdAt?: string;
  updatedAt?: string;
  isActive: boolean;
}

export interface HSNSACInput {
  code: string;
  description: string;
  hsnSacType: string;
  chapter?: string;
  section?: string;
  gstRateId?: string;
  unitOfMeasurement?: string;
  isActive?: boolean;
}

export interface TDSSection {
  id: string;
  sectionCode: string;
  sectionName: string;
  description?: string;
  rateIndividual: number;
  rateCompany: number;
  rateNoPan: number;
  rateLowerDeduction?: number;
  thresholdSingle: number;
  thresholdAnnual: number;
  isTcs: boolean;
  surchargeApplicable: boolean;
  cessRate: number;
  effectiveFrom: string;
  effectiveTo?: string;
  returnForm?: string;
  natureOfPaymentCode?: string;
  isActive: boolean;
}

export interface TDSSectionInput {
  sectionCode: string;
  sectionName: string;
  description?: string;
  rateIndividual: number;
  rateCompany: number;
  rateNoPan: number;
  rateLowerDeduction?: number;
  thresholdSingle: number;
  thresholdAnnual: number;
  isTcs: boolean;
  surchargeApplicable: boolean;
  cessRate: number;
  effectiveFrom: string;
  effectiveTo?: string;
  returnForm?: string;
  natureOfPaymentCode?: string;
  isActive: boolean;
}

export interface TDSEntry {
  id: string;
  tdsSectionId: string;
  tdsSectionCode?: string;
  tdsSectionName?: string;
  voucherId?: string;
  voucherNumber?: string;
  organizationId: string;
  vendorId?: string;
  financialYearId?: string;
  deducteeName: string;
  deducteePan?: string;
  deducteeType: string;
  deducteeAddress?: string;
  deductionDate: string;
  baseAmount: number;
  tdsRate: number;
  tdsAmount: number;
  surcharge: number;
  cess: number;
  totalTds: number;
  lowerDeductionCertNo?: string;
  isThresholdCrossed: boolean;
  aggregateAmountYtd: number;
  thresholdReason?: string;
  challanStatus: string;
  challanNumber?: string;
  challanDate?: string;
  bankName?: string;
  bsrCode?: string;
  certificateNumber?: string;
  certificateDate?: string;
  returnQuarter?: string;
  returnFiled: boolean;
  acknowledgmentNumber?: string;
  remarks?: string;
  createdAt?: string;
  updatedAt?: string;
  isActive: boolean;
}

export interface TDSEntryInput {
  organizationId: string;
  tdsSectionId: string;
  financialYearId?: string;
  voucherId?: string;
  vendorId?: string;
  deducteeName: string;
  deducteePan?: string;
  deducteeType: string;
  deducteeAddress?: string;
  deductionDate: string;
  baseAmount: number;
  tdsRate: number;
  tdsAmount: number;
  surcharge: number;
  cess: number;
  totalTds: number;
  lowerDeductionCertNo?: string;
  remarks?: string;
  challanStatus?: string;
  challanNumber?: string;
  challanDate?: string;
  bankName?: string;
  bsrCode?: string;
  certificateNumber?: string;
  certificateDate?: string;
  returnQuarter?: string;
  returnFiled?: boolean;
  acknowledgmentNumber?: string;
  isActive?: boolean;
}

export interface ThresholdValidationResult {
  tdsApplicable: boolean;
  reason: string;
  singleThreshold: number;
  annualThreshold: number;
  currentAggregate: number;
  newAggregate: number;
  tdsRate: number;
  estimatedTds: number;
  estimatedSurcharge: number;
  estimatedCess: number;
  estimatedTotalTds: number;
}

export interface TDSReturn {
  id: string;
  organizationId: string;
  returnType: string;
  financialYearId: string;
  financialYear: string;
  assessmentYear: string;
  quarter: string;
  periodFrom: string;
  periodTo: string;
  status: string;
  isOriginal: boolean;
  revisionNumber: number;
  originalReturnId?: string;
  deductorTan: string;
  deductorName: string;
  deductorPan?: string;
  deductorType?: string;
  deductorCategory?: string;
  deductorAddress?: string;
  deductorCity?: string;
  deductorState?: string;
  deductorPincode?: string;
  deductorEmail?: string;
  deductorPhone?: string;
  responsiblePersonName?: string;
  responsiblePersonDesignation?: string;
  responsiblePersonAddress?: string;
  responsiblePersonPan?: string;
  totalChallans: number;
  totalDeductees: number;
  totalAmountPaid: number;
  totalTdsDeducted: number;
  totalTdsDeposited: number;
  totalInterest: number;
  totalLateFee: number;
  fileGeneratedAt?: string;
  fileName?: string;
  provisionalReceiptNumber?: string;
  tokenNumber?: string;
  acknowledgmentNumber?: string;
  filedDate?: string;
  acceptedAt?: string;
  dueDate: string;
  isLate: boolean;
  daysLate: number;
  validationErrors?: { code: string; message: string; field?: string; row?: number }[];
  validationWarnings?: { code: string; message: string; field?: string; row?: number }[];
  lastValidatedAt?: string;
  remarks?: string;
  createdAt?: string;
  updatedAt?: string;
  isActive: boolean;
}

export interface TDSReturnInput {
  organizationId: string;
  returnType: string;
  financialYearId: string;
  financialYear: string;
  quarter: string;
  deductorTan: string;
  deductorName: string;
  deductorPan?: string;
  deductorType?: string;
  deductorCategory?: string;
  deductorAddress?: string;
  deductorCity?: string;
  deductorState?: string;
  deductorPincode?: string;
  deductorEmail?: string;
  deductorPhone?: string;
  responsiblePersonName?: string;
  responsiblePersonDesignation?: string;
  responsiblePersonAddress?: string;
  responsiblePersonPan?: string;
  remarks?: string;
}

export interface TDSReturnValidationResult {
  isValid: boolean;
  errors: { code: string; message: string; field?: string; row?: number }[];
  warnings: { code: string; message: string; field?: string; row?: number }[];
  totalChallans: number;
  totalDeductees: number;
  totalTdsDeducted: number;
  totalTdsDeposited: number;
}

export interface GeneratedReturnFile {
  fileName: string;
  fileContent: string;
  fileSize: number;
  fileHash: string;
  generatedAt: string;
  artifactStatus: string;
  statutoryStatus: string;
  complianceNote: string;
}

export interface FilingDetailsInput {
  provisionalReceiptNumber?: string;
  tokenNumber?: string;
  acknowledgmentNumber?: string;
  filedDate?: string;
}

export interface TDSChallan {
  id: string;
  challanNumber?: string;
  bsrCode?: string;
  serialNumber?: string;
  organizationId: string;
  tdsSectionId: string;
  tdsSectionCode?: string;
  tdsSectionName?: string;
  financialYearId: string;
  assessmentYear: string;
  periodFrom: string;
  periodTo: string;
  totalBaseAmount: number;
  totalTdsAmount: number;
  totalSurcharge: number;
  totalCess: number;
  interestAmount: number;
  penaltyAmount: number;
  otherAmount: number;
  totalAmount: number;
  entryCount: number;
  status: string;
  paymentDate?: string;
  paymentMode?: string;
  bankName?: string;
  bankBranch?: string;
  bankAccountNumber?: string;
  chequeDdNumber?: string;
  chequeDdDate?: string;
  oltasAcknowledgment?: string;
  oltasStatus?: string;
  oltasVerifiedAt?: string;
  challanType: string;
  minorHead?: string;
  deductorTan: string;
  deductorName: string;
  deductorAddress?: string;
  returnQuarter?: string;
  isIncludedInReturn: boolean;
  returnId?: string;
  isLate: boolean;
  remarks?: string;
  createdAt?: string;
  updatedAt?: string;
  isActive: boolean;
  entries?: TDSEntry[];
}

export interface TDSChallanInput {
  organizationId: string;
  tdsSectionId: string;
  financialYearId: string;
  assessmentYear: string;
  periodFrom: string;
  periodTo: string;
  challanType?: string;
  minorHead?: string;
  deductorTan: string;
  deductorName: string;
  deductorAddress?: string;
  returnQuarter?: string;
  entryIds?: string[];
  interestAmount?: number;
  penaltyAmount?: number;
  otherAmount?: number;
  remarks?: string;
}

export interface TDSChallanPaymentInput {
  challanNumber: string;
  bsrCode: string;
  serialNumber?: string;
  paymentDate: string;
  paymentMode: string;
  bankName: string;
  bankBranch?: string;
  bankAccountNumber?: string;
  chequeDdNumber?: string;
  chequeDdDate?: string;
}

export interface TDSChallanOLTASInput {
  oltasAcknowledgment: string;
  oltasStatus: string;
  oltasVerifiedAt: string;
}

export interface TDSCertificateCandidate {
  deducteePan?: string;
  deducteeName: string;
  tdsSectionId: string;
  tdsSectionCode?: string;
  tdsSectionName?: string;
  totalAmountPaid: number;
  totalTdsDeducted: number;
  transactionCount: number;
}

export interface TDSCertificateInfo {
  certificateNumber: string;
  certificateDate?: string;
  deducteePan?: string;
  deducteeName: string;
  tdsSectionCode?: string;
  tdsSectionName?: string;
  totalAmountPaid: number;
  totalTdsDeducted: number;
  entryCount: number;
  artifactStatus: string;
  legalStatus: string;
  source: string;
  complianceNote?: string;
}

export interface TDSCertificateDetail {
  certificateNumber: string;
  deductorTan: string;
  deductorName: string;
  deducteePan: string;
  deducteeName: string;
  financialYear: string;
  assessmentYear: string;
  periodFrom: string;
  periodTo: string;
  tdsSectionCode: string;
  tdsSectionName: string;
  totalAmountPaid: number;
  totalTdsDeducted: number;
  totalTdsDeposited: number;
  transactionCount: number;
  challanCount: number;
  generatedDate: string;
  artifactStatus: string;
  legalStatus: string;
  source: string;
  complianceNote?: string;
}

export interface TDSCertificateGenerateInput {
  deducteePan: string;
  tdsSectionId: string;
  financialYear: string;
  quarter: string;
}

type ApiRecord = Record<string, unknown>;

function asRecord(value: unknown): ApiRecord {
  return value && typeof value === 'object' ? (value as ApiRecord) : {};
}

function readValue(record: ApiRecord, ...keys: string[]) {
  return keys.map((key) => record[key]).find((candidate) => candidate != null);
}

function readString(record: ApiRecord, ...keys: string[]): string {
  const value = readValue(record, ...keys);
  return value == null ? '' : String(value);
}

function readOptionalString(record: ApiRecord, ...keys: string[]): string | undefined {
  const value = readValue(record, ...keys);
  return value == null || value === '' ? undefined : String(value);
}

function readNumber(record: ApiRecord, ...keys: string[]): number {
  const numericValue = Number(readValue(record, ...keys) ?? 0);
  return Number.isFinite(numericValue) ? numericValue : 0;
}

function readBoolean(record: ApiRecord, ...keys: string[]): boolean {
  return Boolean(readValue(record, ...keys));
}

function normalizePage<T>(data: unknown, mapper: (item: unknown) => T): PaginatedResponse<T> {
  const page = asRecord(data);
  const items = Array.isArray(data) ? data : Array.isArray(page.items) ? page.items : [];
  return {
    items: items.map(mapper),
    total: readNumber(page, 'total') || items.length,
    page: readNumber(page, 'page') || 1,
    pageSize: readNumber(page, 'pageSize', 'page_size') || items.length,
    totalPages: readNumber(page, 'totalPages', 'total_pages') || 1,
  };
}

function mapLookup(value: unknown): LookupOption {
  const item = asRecord(value);
  return {
    id: readString(item, 'id'),
    code: readOptionalString(item, 'code'),
    name: readString(item, 'name'),
  };
}

function mapFinancialYear(value: unknown): FinancialYearOption {
  const item = asRecord(value);
  return {
    id: readString(item, 'id'),
    code: readString(item, 'code'),
    name: readString(item, 'name'),
    startDate: readOptionalString(item, 'startDate'),
    endDate: readOptionalString(item, 'endDate'),
    isCurrent: readBoolean(item, 'isCurrent'),
  };
}

function mapGstRate(value: unknown): GSTRate {
  const item = asRecord(value);
  return {
    id: readString(item, 'id'),
    code: readString(item, 'code'),
    name: readString(item, 'name'),
    rate: readNumber(item, 'rate'),
    cgstRate: readNumber(item, 'cgstRate'),
    sgstRate: readNumber(item, 'sgstRate'),
    igstRate: readNumber(item, 'igstRate'),
    cessRate: readNumber(item, 'cessRate'),
    description: readOptionalString(item, 'description'),
    effectiveFrom: readString(item, 'effectiveFrom'),
    effectiveTo: readOptionalString(item, 'effectiveTo'),
    isActive: readBoolean(item, 'isActive'),
  };
}

function gstRateToApi(input: GSTRateInput) {
  return {
    code: input.code,
    name: input.name,
    rate: input.rate,
    cgstRate: input.cgstRate,
    sgstRate: input.sgstRate,
    igstRate: input.igstRate,
    cessRate: input.cessRate,
    description: input.description,
    effectiveFrom: input.effectiveFrom,
    effectiveTo: input.effectiveTo || undefined,
    isActive: input.isActive,
  };
}

function mapGSTRegistration(value: unknown): GSTRegistration {
  const item = asRecord(value);
  return {
    id: readString(item, 'id'),
    gstin: readString(item, 'gstin'),
    legalName: readString(item, 'legalName'),
    tradeName: readOptionalString(item, 'tradeName'),
    registrationType: readString(item, 'registrationType'),
    stateCode: readString(item, 'stateCode'),
    stateName: readString(item, 'stateName'),
    address: readOptionalString(item, 'address'),
    pincode: readOptionalString(item, 'pincode'),
    isEInvoiceEnabled: readBoolean(item, 'isEInvoiceEnabled'),
    eInvoiceUsername: readOptionalString(item, 'eInvoiceUsername'),
    isEWayBillEnabled: readBoolean(item, 'isEWayBillEnabled'),
    organizationId: readString(item, 'organizationId'),
    organizationName: readOptionalString(item, 'organizationName'),
    unitId: readOptionalString(item, 'unitId'),
    unitName: readOptionalString(item, 'unitName'),
    createdAt: readOptionalString(item, 'createdAt'),
    updatedAt: readOptionalString(item, 'updatedAt'),
    isActive: readBoolean(item, 'isActive'),
  };
}

function gstRegistrationToApi(input: GSTRegistrationInput) {
  return {
    organizationId: input.organizationId,
    gstin: input.gstin,
    legalName: input.legalName,
    tradeName: input.tradeName || undefined,
    registrationType: input.registrationType,
    stateCode: input.stateCode,
    stateName: input.stateName,
    address: input.address || undefined,
    pincode: input.pincode || undefined,
    isEInvoiceEnabled: input.isEInvoiceEnabled,
    eInvoiceUsername: input.eInvoiceUsername || undefined,
    eInvoicePassword: input.eInvoicePassword || undefined,
    isEWayBillEnabled: input.isEWayBillEnabled,
    unitId: input.unitId || undefined,
    ...(input.isActive != null ? { isActive: input.isActive } : {}),
  };
}

function mapHsnSac(value: unknown): HSNSAC {
  const item = asRecord(value);
  return {
    id: readString(item, 'id'),
    code: readString(item, 'code'),
    description: readString(item, 'description'),
    hsnSacType: readString(item, 'hsnSacType'),
    chapter: readOptionalString(item, 'chapter'),
    section: readOptionalString(item, 'section'),
    gstRateId: readOptionalString(item, 'gstRateId'),
    gstRateCode: readOptionalString(item, 'gstRateCode'),
    gstRateName: readOptionalString(item, 'gstRateName'),
    gstRateValue: readNumber(item, 'gstRateValue') || undefined,
    unitOfMeasurement: readOptionalString(item, 'unitOfMeasurement'),
    createdAt: readOptionalString(item, 'createdAt'),
    updatedAt: readOptionalString(item, 'updatedAt'),
    isActive: readBoolean(item, 'isActive'),
  };
}

function hsnSacToApi(input: HSNSACInput) {
  return {
    code: input.code,
    description: input.description,
    hsnSacType: input.hsnSacType,
    chapter: input.chapter || undefined,
    section: input.section || undefined,
    gstRateId: input.gstRateId || undefined,
    unitOfMeasurement: input.unitOfMeasurement || undefined,
    ...(input.isActive != null ? { isActive: input.isActive } : {}),
  };
}

function mapTdsSection(value: unknown): TDSSection {
  const item = asRecord(value);
  return {
    id: readString(item, 'id'),
    sectionCode: readString(item, 'sectionCode'),
    sectionName: readString(item, 'sectionName'),
    description: readOptionalString(item, 'description'),
    rateIndividual: readNumber(item, 'rateIndividual'),
    rateCompany: readNumber(item, 'rateCompany'),
    rateNoPan: readNumber(item, 'rateNoPan') || 20,
    rateLowerDeduction: readNumber(item, 'rateLowerDeduction') || undefined,
    thresholdSingle: readNumber(item, 'thresholdSingle'),
    thresholdAnnual: readNumber(item, 'thresholdAnnual'),
    isTcs: readBoolean(item, 'isTcs'),
    surchargeApplicable: readBoolean(item, 'surchargeApplicable'),
    cessRate: readNumber(item, 'cessRate'),
    effectiveFrom: readString(item, 'effectiveFrom'),
    effectiveTo: readOptionalString(item, 'effectiveTo'),
    returnForm: readOptionalString(item, 'returnForm'),
    natureOfPaymentCode: readOptionalString(item, 'natureOfPaymentCode'),
    isActive: readBoolean(item, 'isActive'),
  };
}

function tdsSectionToApi(input: TDSSectionInput) {
  return {
    sectionCode: input.sectionCode,
    sectionName: input.sectionName,
    description: input.description,
    rateIndividual: input.rateIndividual,
    rateCompany: input.rateCompany,
    rateNoPan: input.rateNoPan,
    rateLowerDeduction: input.rateLowerDeduction,
    thresholdSingle: input.thresholdSingle,
    thresholdAnnual: input.thresholdAnnual,
    isTcs: input.isTcs,
    surchargeApplicable: input.surchargeApplicable,
    cessRate: input.cessRate,
    effectiveFrom: input.effectiveFrom,
    effectiveTo: input.effectiveTo || undefined,
    returnForm: input.returnForm || undefined,
    natureOfPaymentCode: input.natureOfPaymentCode || undefined,
    isActive: input.isActive,
  };
}

function mapTdsEntry(value: unknown): TDSEntry {
  const item = asRecord(value);
  return {
    id: readString(item, 'id'),
    tdsSectionId: readString(item, 'tdsSectionId'),
    tdsSectionCode: readOptionalString(item, 'tdsSectionCode'),
    tdsSectionName: readOptionalString(item, 'tdsSectionName'),
    voucherId: readOptionalString(item, 'voucherId'),
    voucherNumber: readOptionalString(item, 'voucherNumber'),
    organizationId: readString(item, 'organizationId'),
    vendorId: readOptionalString(item, 'vendorId'),
    financialYearId: readOptionalString(item, 'financialYearId'),
    deducteeName: readString(item, 'deducteeName'),
    deducteePan: readOptionalString(item, 'deducteePan'),
    deducteeType: readString(item, 'deducteeType'),
    deducteeAddress: readOptionalString(item, 'deducteeAddress'),
    deductionDate: readString(item, 'deductionDate'),
    baseAmount: readNumber(item, 'baseAmount'),
    tdsRate: readNumber(item, 'tdsRate'),
    tdsAmount: readNumber(item, 'tdsAmount'),
    surcharge: readNumber(item, 'surcharge'),
    cess: readNumber(item, 'cess'),
    totalTds: readNumber(item, 'totalTds'),
    lowerDeductionCertNo: readOptionalString(item, 'lowerDeductionCertNo'),
    isThresholdCrossed: readBoolean(item, 'isThresholdCrossed'),
    aggregateAmountYtd: readNumber(item, 'aggregateAmountYtd'),
    thresholdReason: readOptionalString(item, 'thresholdReason'),
    challanStatus: readString(item, 'challanStatus'),
    challanNumber: readOptionalString(item, 'challanNumber'),
    challanDate: readOptionalString(item, 'challanDate'),
    bankName: readOptionalString(item, 'bankName'),
    bsrCode: readOptionalString(item, 'bsrCode'),
    certificateNumber: readOptionalString(item, 'certificateNumber'),
    certificateDate: readOptionalString(item, 'certificateDate'),
    returnQuarter: readOptionalString(item, 'returnQuarter'),
    returnFiled: readBoolean(item, 'returnFiled'),
    acknowledgmentNumber: readOptionalString(item, 'acknowledgmentNumber'),
    remarks: readOptionalString(item, 'remarks'),
    createdAt: readOptionalString(item, 'createdAt'),
    updatedAt: readOptionalString(item, 'updatedAt'),
    isActive: readBoolean(item, 'isActive'),
  };
}

function tdsEntryToApi(input: TDSEntryInput) {
  return {
    organizationId: input.organizationId,
    tdsSectionId: input.tdsSectionId,
    financialYearId: input.financialYearId || undefined,
    voucherId: input.voucherId || undefined,
    vendorId: input.vendorId || undefined,
    deducteeName: input.deducteeName,
    deducteePan: input.deducteePan || undefined,
    deducteeType: input.deducteeType,
    deducteeAddress: input.deducteeAddress || undefined,
    deductionDate: input.deductionDate,
    baseAmount: input.baseAmount,
    tdsRate: input.tdsRate,
    tdsAmount: input.tdsAmount,
    surcharge: input.surcharge,
    cess: input.cess,
    totalTds: input.totalTds,
    lowerDeductionCertNo: input.lowerDeductionCertNo || undefined,
    remarks: input.remarks || undefined,
    challanStatus: input.challanStatus || undefined,
    challanNumber: input.challanNumber || undefined,
    challanDate: input.challanDate || undefined,
    bankName: input.bankName || undefined,
    bsrCode: input.bsrCode || undefined,
    certificateNumber: input.certificateNumber || undefined,
    certificateDate: input.certificateDate || undefined,
    returnQuarter: input.returnQuarter || undefined,
    returnFiled: input.returnFiled,
    acknowledgmentNumber: input.acknowledgmentNumber || undefined,
    ...(input.isActive != null ? { isActive: input.isActive } : {}),
  };
}

function mapThresholdValidation(value: unknown): ThresholdValidationResult {
  const item = asRecord(value);
  return {
    tdsApplicable: readBoolean(item, 'tdsApplicable'),
    reason: readString(item, 'reason'),
    singleThreshold: readNumber(item, 'singleThreshold'),
    annualThreshold: readNumber(item, 'annualThreshold'),
    currentAggregate: readNumber(item, 'currentAggregate'),
    newAggregate: readNumber(item, 'newAggregate'),
    tdsRate: readNumber(item, 'tdsRate'),
    estimatedTds: readNumber(item, 'estimatedTds'),
    estimatedSurcharge: readNumber(item, 'estimatedSurcharge'),
    estimatedCess: readNumber(item, 'estimatedCess'),
    estimatedTotalTds: readNumber(item, 'estimatedTotalTds'),
  };
}

function mapTdsReturn(value: unknown): TDSReturn {
  const item = asRecord(value);
  return {
    id: readString(item, 'id'),
    organizationId: readString(item, 'organizationId'),
    returnType: readString(item, 'returnType'),
    financialYearId: readString(item, 'financialYearId'),
    financialYear: readString(item, 'financialYear'),
    assessmentYear: readString(item, 'assessmentYear'),
    quarter: readString(item, 'quarter'),
    periodFrom: readString(item, 'periodFrom'),
    periodTo: readString(item, 'periodTo'),
    status: readString(item, 'status'),
    isOriginal: readBoolean(item, 'isOriginal'),
    revisionNumber: readNumber(item, 'revisionNumber'),
    originalReturnId: readOptionalString(item, 'originalReturnId'),
    deductorTan: readString(item, 'deductorTan'),
    deductorName: readString(item, 'deductorName'),
    deductorPan: readOptionalString(item, 'deductorPan'),
    deductorType: readOptionalString(item, 'deductorType'),
    deductorCategory: readOptionalString(item, 'deductorCategory'),
    deductorAddress: readOptionalString(item, 'deductorAddress'),
    deductorCity: readOptionalString(item, 'deductorCity'),
    deductorState: readOptionalString(item, 'deductorState'),
    deductorPincode: readOptionalString(item, 'deductorPincode'),
    deductorEmail: readOptionalString(item, 'deductorEmail'),
    deductorPhone: readOptionalString(item, 'deductorPhone'),
    responsiblePersonName: readOptionalString(item, 'responsiblePersonName'),
    responsiblePersonDesignation: readOptionalString(item, 'responsiblePersonDesignation'),
    responsiblePersonAddress: readOptionalString(item, 'responsiblePersonAddress'),
    responsiblePersonPan: readOptionalString(item, 'responsiblePersonPan'),
    totalChallans: readNumber(item, 'totalChallans'),
    totalDeductees: readNumber(item, 'totalDeductees'),
    totalAmountPaid: readNumber(item, 'totalAmountPaid'),
    totalTdsDeducted: readNumber(item, 'totalTdsDeducted'),
    totalTdsDeposited: readNumber(item, 'totalTdsDeposited'),
    totalInterest: readNumber(item, 'totalInterest'),
    totalLateFee: readNumber(item, 'totalLateFee'),
    fileGeneratedAt: readOptionalString(item, 'fileGeneratedAt'),
    fileName: readOptionalString(item, 'fileName'),
    provisionalReceiptNumber: readOptionalString(item, 'provisionalReceiptNumber'),
    tokenNumber: readOptionalString(item, 'tokenNumber'),
    acknowledgmentNumber: readOptionalString(item, 'acknowledgmentNumber'),
    filedDate: readOptionalString(item, 'filedDate'),
    acceptedAt: readOptionalString(item, 'acceptedAt'),
    dueDate: readString(item, 'dueDate'),
    isLate: readBoolean(item, 'isLate'),
    daysLate: readNumber(item, 'daysLate'),
    validationErrors: (item.validationErrors as TDSReturn['validationErrors']) ?? [],
    validationWarnings: (item.validationWarnings as TDSReturn['validationWarnings']) ?? [],
    lastValidatedAt: readOptionalString(item, 'lastValidatedAt'),
    remarks: readOptionalString(item, 'remarks'),
    createdAt: readOptionalString(item, 'createdAt'),
    updatedAt: readOptionalString(item, 'updatedAt'),
    isActive: readBoolean(item, 'isActive'),
  };
}

function tdsReturnToApi(input: TDSReturnInput) {
  return {
    organizationId: input.organizationId,
    returnType: input.returnType,
    financialYearId: input.financialYearId,
    financialYear: input.financialYear,
    quarter: input.quarter,
    deductorTan: input.deductorTan,
    deductorName: input.deductorName,
    deductorPan: input.deductorPan || undefined,
    deductorType: input.deductorType || undefined,
    deductorCategory: input.deductorCategory || undefined,
    deductorAddress: input.deductorAddress || undefined,
    deductorCity: input.deductorCity || undefined,
    deductorState: input.deductorState || undefined,
    deductorPincode: input.deductorPincode || undefined,
    deductorEmail: input.deductorEmail || undefined,
    deductorPhone: input.deductorPhone || undefined,
    responsiblePersonName: input.responsiblePersonName || undefined,
    responsiblePersonDesignation: input.responsiblePersonDesignation || undefined,
    responsiblePersonAddress: input.responsiblePersonAddress || undefined,
    responsiblePersonPan: input.responsiblePersonPan || undefined,
    remarks: input.remarks || undefined,
  };
}

function mapTdsReturnValidation(value: unknown): TDSReturnValidationResult {
  const item = asRecord(value);
  return {
    isValid: readBoolean(item, 'isValid'),
    errors: (item.errors as TDSReturnValidationResult['errors']) ?? [],
    warnings: (item.warnings as TDSReturnValidationResult['warnings']) ?? [],
    totalChallans: readNumber(item, 'totalChallans'),
    totalDeductees: readNumber(item, 'totalDeductees'),
    totalTdsDeducted: readNumber(item, 'totalTdsDeducted'),
    totalTdsDeposited: readNumber(item, 'totalTdsDeposited'),
  };
}

function filingDetailsToApi(input: FilingDetailsInput) {
  return {
    provisionalReceiptNumber: input.provisionalReceiptNumber || undefined,
    tokenNumber: input.tokenNumber || undefined,
    acknowledgmentNumber: input.acknowledgmentNumber || undefined,
    filedDate: input.filedDate || undefined,
  };
}

function mapTdsChallan(value: unknown): TDSChallan {
  const item = asRecord(value);
  const entries = Array.isArray(item.entries) ? item.entries.map(mapTdsEntry) : undefined;
  return {
    id: readString(item, 'id'),
    challanNumber: readOptionalString(item, 'challanNumber', 'challan_number'),
    bsrCode: readOptionalString(item, 'bsrCode', 'bsr_code'),
    serialNumber: readOptionalString(item, 'serialNumber', 'serial_number'),
    organizationId: readString(item, 'organizationId', 'organization_id'),
    tdsSectionId: readString(item, 'tdsSectionId', 'tds_section_id'),
    tdsSectionCode: readOptionalString(item, 'tdsSectionCode', 'tds_section_code'),
    tdsSectionName: readOptionalString(item, 'tdsSectionName', 'tds_section_name'),
    financialYearId: readString(item, 'financialYearId', 'financial_year_id'),
    assessmentYear: readString(item, 'assessmentYear', 'assessment_year'),
    periodFrom: readString(item, 'periodFrom', 'period_from'),
    periodTo: readString(item, 'periodTo', 'period_to'),
    totalBaseAmount: readNumber(item, 'totalBaseAmount', 'total_base_amount'),
    totalTdsAmount: readNumber(item, 'totalTdsAmount', 'total_tds_amount'),
    totalSurcharge: readNumber(item, 'totalSurcharge', 'total_surcharge'),
    totalCess: readNumber(item, 'totalCess', 'total_cess'),
    interestAmount: readNumber(item, 'interestAmount', 'interest_amount'),
    penaltyAmount: readNumber(item, 'penaltyAmount', 'penalty_amount'),
    otherAmount: readNumber(item, 'otherAmount', 'other_amount'),
    totalAmount: readNumber(item, 'totalAmount', 'total_amount'),
    entryCount: readNumber(item, 'entryCount', 'entry_count'),
    status: readString(item, 'status'),
    paymentDate: readOptionalString(item, 'paymentDate', 'payment_date'),
    paymentMode: readOptionalString(item, 'paymentMode', 'payment_mode'),
    bankName: readOptionalString(item, 'bankName', 'bank_name'),
    bankBranch: readOptionalString(item, 'bankBranch', 'bank_branch'),
    bankAccountNumber: readOptionalString(item, 'bankAccountNumber', 'bank_account_number'),
    chequeDdNumber: readOptionalString(item, 'chequeDdNumber', 'cheque_dd_number'),
    chequeDdDate: readOptionalString(item, 'chequeDdDate', 'cheque_dd_date'),
    oltasAcknowledgment: readOptionalString(item, 'oltasAcknowledgment', 'oltas_acknowledgment'),
    oltasStatus: readOptionalString(item, 'oltasStatus', 'oltas_status'),
    oltasVerifiedAt: readOptionalString(item, 'oltasVerifiedAt', 'oltas_verified_at'),
    challanType: readString(item, 'challanType', 'challan_type'),
    minorHead: readOptionalString(item, 'minorHead', 'minor_head'),
    deductorTan: readString(item, 'deductorTan', 'deductor_tan'),
    deductorName: readString(item, 'deductorName', 'deductor_name'),
    deductorAddress: readOptionalString(item, 'deductorAddress', 'deductor_address'),
    returnQuarter: readOptionalString(item, 'returnQuarter', 'return_quarter'),
    isIncludedInReturn: readBoolean(item, 'isIncludedInReturn', 'is_included_in_return'),
    returnId: readOptionalString(item, 'returnId', 'return_id'),
    isLate: readBoolean(item, 'isLate', 'is_late'),
    remarks: readOptionalString(item, 'remarks'),
    createdAt: readOptionalString(item, 'createdAt', 'created_at'),
    updatedAt: readOptionalString(item, 'updatedAt', 'updated_at'),
    isActive: readBoolean(item, 'isActive', 'is_active'),
    entries,
  };
}

function tdsChallanToApi(input: TDSChallanInput) {
  return {
    organization_id: input.organizationId,
    tds_section_id: input.tdsSectionId,
    financial_year_id: input.financialYearId,
    assessment_year: input.assessmentYear,
    period_from: input.periodFrom,
    period_to: input.periodTo,
    challan_type: input.challanType || '281',
    minor_head: input.minorHead || undefined,
    deductor_tan: input.deductorTan,
    deductor_name: input.deductorName,
    deductor_address: input.deductorAddress || undefined,
    return_quarter: input.returnQuarter || undefined,
    entry_ids: input.entryIds ?? [],
    interest_amount: input.interestAmount ?? 0,
    penalty_amount: input.penaltyAmount ?? 0,
    other_amount: input.otherAmount ?? 0,
    remarks: input.remarks || undefined,
  };
}

function challanPaymentToApi(input: TDSChallanPaymentInput) {
  return {
    challan_number: input.challanNumber,
    bsr_code: input.bsrCode,
    serial_number: input.serialNumber || undefined,
    payment_date: input.paymentDate,
    payment_mode: input.paymentMode,
    bank_name: input.bankName,
    bank_branch: input.bankBranch || undefined,
    bank_account_number: input.bankAccountNumber || undefined,
    cheque_dd_number: input.chequeDdNumber || undefined,
    cheque_dd_date: input.chequeDdDate || undefined,
  };
}

function challanOltasToApi(input: TDSChallanOLTASInput) {
  return {
    oltas_acknowledgment: input.oltasAcknowledgment,
    oltas_status: input.oltasStatus,
    oltas_verified_at: input.oltasVerifiedAt,
  };
}

function mapCertificateCandidate(value: unknown): TDSCertificateCandidate {
  const item = asRecord(value);
  return {
    deducteePan: readOptionalString(item, 'deducteePan', 'deductee_pan'),
    deducteeName: readString(item, 'deducteeName', 'deductee_name'),
    tdsSectionId: readString(item, 'tdsSectionId', 'tds_section_id'),
    tdsSectionCode: readOptionalString(item, 'tdsSectionCode', 'tds_section_code'),
    tdsSectionName: readOptionalString(item, 'tdsSectionName', 'tds_section_name'),
    totalAmountPaid: readNumber(item, 'totalAmountPaid', 'total_amount_paid'),
    totalTdsDeducted: readNumber(item, 'totalTdsDeducted', 'total_tds_deducted'),
    transactionCount: readNumber(item, 'transactionCount', 'transaction_count'),
  };
}

function mapCertificateInfo(value: unknown): TDSCertificateInfo {
  const item = asRecord(value);
  return {
    certificateNumber: readString(item, 'certificateNumber', 'certificate_number'),
    certificateDate: readOptionalString(item, 'certificateDate', 'certificate_date'),
    deducteePan: readOptionalString(item, 'deducteePan', 'deductee_pan'),
    deducteeName: readString(item, 'deducteeName', 'deductee_name'),
    tdsSectionCode: readOptionalString(item, 'tdsSectionCode', 'tds_section_code'),
    tdsSectionName: readOptionalString(item, 'tdsSectionName', 'tds_section_name'),
    totalAmountPaid: readNumber(item, 'totalAmountPaid', 'total_amount_paid'),
    totalTdsDeducted: readNumber(item, 'totalTdsDeducted', 'total_tds_deducted'),
    entryCount: readNumber(item, 'entryCount', 'entry_count'),
    artifactStatus: readString(item, 'artifactStatus', 'artifact_status'),
    legalStatus: readString(item, 'legalStatus', 'legal_status'),
    source: readString(item, 'source'),
    complianceNote: readOptionalString(item, 'complianceNote', 'compliance_note'),
  };
}

function mapCertificateDetail(value: unknown): TDSCertificateDetail {
  const item = asRecord(value);
  return {
    certificateNumber: readString(item, 'certificateNumber', 'certificate_number'),
    deductorTan: readString(item, 'deductorTan', 'deductor_tan'),
    deductorName: readString(item, 'deductorName', 'deductor_name'),
    deducteePan: readString(item, 'deducteePan', 'deductee_pan'),
    deducteeName: readString(item, 'deducteeName', 'deductee_name'),
    financialYear: readString(item, 'financialYear', 'financial_year'),
    assessmentYear: readString(item, 'assessmentYear', 'assessment_year'),
    periodFrom: readString(item, 'periodFrom', 'period_from'),
    periodTo: readString(item, 'periodTo', 'period_to'),
    tdsSectionCode: readString(item, 'tdsSectionCode', 'tds_section_code'),
    tdsSectionName: readString(item, 'tdsSectionName', 'tds_section_name'),
    totalAmountPaid: readNumber(item, 'totalAmountPaid', 'total_amount_paid'),
    totalTdsDeducted: readNumber(item, 'totalTdsDeducted', 'total_tds_deducted'),
    totalTdsDeposited: readNumber(item, 'totalTdsDeposited', 'total_tds_deposited'),
    transactionCount: readNumber(item, 'transactionCount', 'transaction_count'),
    challanCount: readNumber(item, 'challanCount', 'challan_count'),
    generatedDate: readString(item, 'generatedDate', 'generated_date'),
    artifactStatus: readString(item, 'artifactStatus', 'artifact_status'),
    legalStatus: readString(item, 'legalStatus', 'legal_status'),
    source: readString(item, 'source'),
    complianceNote: readOptionalString(item, 'complianceNote', 'compliance_note'),
  };
}

function certificateGenerateToApi(input: TDSCertificateGenerateInput) {
  return {
    deductee_pan: input.deducteePan,
    tds_section_id: input.tdsSectionId,
    financial_year: input.financialYear,
    quarter: input.quarter,
  };
}

function certificateBulkToApi(financialYear: string, quarter: string) {
  return {
    financial_year: financialYear,
    quarter,
  };
}

function normalizeTdsReturnFileName(fileName: string): string {
  return fileName.replace(/^(24Q|26Q|27Q|27EQ)_(\d{4})(\d{2})_/, '$1_$2-$3_');
}

export function useOrganizations() {
  return useQuery({
    queryKey: ['tax-organizations'],
    queryFn: async () =>
      normalizePage(
        (await organizationsApi.list({ pageSize: 100, includeInactive: false })).data,
        mapLookup,
      ),
  });
}

export function useUnits(organizationId?: string) {
  return useQuery({
    queryKey: ['tax-units', organizationId],
    enabled: !!organizationId,
    queryFn: async () =>
      normalizePage(
        (await unitsApi.list({ organizationId, pageSize: 100, includeInactive: false })).data,
        mapLookup,
      ),
  });
}

export function useFinancialYears() {
  const organizationId = useActiveOrganizationId();
  return useQuery({
    queryKey: ['tax-financial-years', organizationId],
    enabled: !!organizationId,
    queryFn: async () =>
      normalizePage(
        (await financialYearsApi.list({ pageSize: 100, includeInactive: false })).data,
        mapFinancialYear,
      ),
  });
}

export function useGSTRates(params?: {
  page?: number;
  pageSize?: number;
  includeInactive?: boolean;
}) {
  return useQuery({
    queryKey: ['gst-rates', params],
    queryFn: async () => {
      const response = await gstRatesApi.list({
        page: params?.page ?? 1,
        pageSize: params?.pageSize ?? 50,
        includeInactive: params?.includeInactive ?? true,
      });
      return normalizePage(response.data, mapGstRate);
    },
  });
}

export function useGSTRate(id?: string) {
  return useQuery({
    queryKey: ['gst-rate', id],
    enabled: !!id,
    queryFn: async () => mapGstRate((await gstRatesApi.get(id!)).data),
  });
}

export function useCreateGSTRate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: GSTRateInput) => gstRatesApi.create(gstRateToApi(input)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['gst-rates'] }),
  });
}

export function useUpdateGSTRate(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: GSTRateInput) => gstRatesApi.update(id, gstRateToApi(input)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gst-rates'] });
      queryClient.invalidateQueries({ queryKey: ['gst-rate', id] });
    },
  });
}

export function useDeleteGSTRate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => gstRatesApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['gst-rates'] }),
  });
}

export function useGSTRegistrations(params: { pageSize?: number; includeInactive?: boolean } = {}) {
  return useQuery({
    queryKey: ['gst-registrations', params],
    queryFn: async () =>
      normalizePage(
        (
          await gstRegistrationsApi.list({
            pageSize: params.pageSize ?? 100,
            includeInactive: params.includeInactive ?? true,
          })
        ).data,
        mapGSTRegistration,
      ),
  });
}

export function useGSTRegistration(id?: string) {
  return useQuery({
    queryKey: ['gst-registration', id],
    enabled: !!id,
    queryFn: async () => mapGSTRegistration((await gstRegistrationsApi.get(id!)).data),
  });
}

export function useCreateGSTRegistration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: GSTRegistrationInput) =>
      gstRegistrationsApi.create(gstRegistrationToApi(input)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['gst-registrations'] }),
  });
}

export function useUpdateGSTRegistration(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: GSTRegistrationInput) =>
      gstRegistrationsApi.update(id, gstRegistrationToApi(input)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gst-registrations'] });
      queryClient.invalidateQueries({ queryKey: ['gst-registration', id] });
    },
  });
}

export function useDeleteGSTRegistration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => gstRegistrationsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['gst-registrations'] }),
  });
}

export function useHSNSAC(params?: { search?: string; hsnSacType?: string; pageSize?: number }) {
  return useQuery({
    queryKey: ['hsn-sac', params],
    queryFn: async () =>
      normalizePage(
        (
          await hsnSacApi.list({
            search: params?.search ?? '',
            hsnSacType: params?.hsnSacType,
            pageSize: params?.pageSize ?? 100,
          })
        ).data,
        mapHsnSac,
      ),
  });
}

export function useHSNSACItem(id?: string) {
  return useQuery({
    queryKey: ['hsn-sac-item', id],
    enabled: !!id,
    queryFn: async () => mapHsnSac((await hsnSacApi.get(id!)).data),
  });
}

export function useCreateHSNSAC() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: HSNSACInput) => hsnSacApi.create(hsnSacToApi(input)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hsn-sac'] }),
  });
}

export function useUpdateHSNSAC(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: HSNSACInput) => hsnSacApi.update(id, hsnSacToApi(input)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hsn-sac'] });
      queryClient.invalidateQueries({ queryKey: ['hsn-sac-item', id] });
    },
  });
}

export function useDeleteHSNSAC() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => hsnSacApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hsn-sac'] }),
  });
}

export function useTDSSections(params?: {
  page?: number;
  pageSize?: number;
  includeInactive?: boolean;
  returnForm?: string;
}) {
  return useQuery({
    queryKey: ['tds-sections', params],
    queryFn: async () => {
      const response = await tdsSectionsApi.list({
        page: params?.page ?? 1,
        pageSize: params?.pageSize ?? 50,
        includeInactive: params?.includeInactive ?? true,
        ...(params?.returnForm && params.returnForm !== 'all'
          ? { returnForm: params.returnForm }
          : {}),
      });
      return normalizePage(response.data, mapTdsSection);
    },
  });
}

export function useTDSSection(id?: string) {
  return useQuery({
    queryKey: ['tds-section', id],
    enabled: !!id,
    queryFn: async () => mapTdsSection((await tdsSectionsApi.get(id!)).data),
  });
}

export function useCreateTDSSection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: TDSSectionInput) => tdsSectionsApi.create(tdsSectionToApi(input)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tds-sections'] }),
  });
}

export function useUpdateTDSSection(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: TDSSectionInput) => tdsSectionsApi.update(id, tdsSectionToApi(input)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tds-sections'] });
      queryClient.invalidateQueries({ queryKey: ['tds-section', id] });
    },
  });
}

export function useDeleteTDSSection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => tdsSectionsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tds-sections'] }),
  });
}

export function useTDSEntries(params: {
  fromDate?: string;
  toDate?: string;
  challanStatus?: string;
  pageSize?: number;
}) {
  return useQuery({
    queryKey: ['tds-entries', params],
    queryFn: async () =>
      normalizePage(
        (
          await tdsEntriesApi.list({
            from_date: params.fromDate,
            to_date: params.toDate,
            challan_status: params.challanStatus,
            pageSize: params.pageSize ?? 100,
          })
        ).data,
        mapTdsEntry,
      ),
  });
}

export function useTDSEntry(id?: string) {
  return useQuery({
    queryKey: ['tds-entry', id],
    enabled: !!id,
    queryFn: async () => mapTdsEntry((await tdsEntriesApi.get(id!)).data),
  });
}

export function useValidateTDSThreshold() {
  return useMutation<
    ThresholdValidationResult,
    Error,
    {
      organizationId: string;
      vendorId?: string;
      tdsSectionId: string;
      baseAmount: number;
      deductionDate: string;
      deducteeType: string;
      deducteePan?: string;
    }
  >({
    mutationFn: (data: {
      organizationId: string;
      vendorId?: string;
      tdsSectionId: string;
      baseAmount: number;
      deductionDate: string;
      deducteeType: string;
      deducteePan?: string;
    }) =>
      tdsEntriesApi
        .validateThreshold({
          vendorId: data.vendorId || undefined,
          tdsSectionId: data.tdsSectionId,
          baseAmount: data.baseAmount,
          deductionDate: data.deductionDate,
          deducteeType: data.deducteeType,
          deducteePan: data.deducteePan || undefined,
        })
        .then((response) => mapThresholdValidation(response.data)),
    onSuccess: () => undefined,
  });
}

export function useCreateTDSEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: TDSEntryInput) => tdsEntriesApi.create(tdsEntryToApi(input)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tds-entries'] }),
  });
}

export function useUpdateTDSEntry(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: TDSEntryInput) => tdsEntriesApi.update(id, tdsEntryToApi(input)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tds-entries'] });
      queryClient.invalidateQueries({ queryKey: ['tds-entry', id] });
    },
  });
}

export function useDeleteTDSEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => tdsEntriesApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tds-entries'] }),
  });
}

export function useTDSReturns(params: {
  returnType?: string;
  financialYearId?: string;
  quarter?: string;
  status?: string;
  pageSize?: number;
}) {
  return useQuery({
    queryKey: ['tds-returns', params],
    queryFn: async () =>
      normalizePage(
        (
          await tdsReturnsApi.list({
            return_type: params.returnType,
            financial_year_id: params.financialYearId,
            quarter: params.quarter,
            status: params.status,
            pageSize: params.pageSize ?? 100,
          })
        ).data,
        mapTdsReturn,
      ),
  });
}

export function useTDSReturn(id?: string) {
  return useQuery({
    queryKey: ['tds-return', id],
    enabled: !!id,
    queryFn: async () => mapTdsReturn((await tdsReturnsApi.get(id!)).data),
  });
}

export function useCreateTDSReturn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: TDSReturnInput) =>
      mapTdsReturn((await tdsReturnsApi.create(tdsReturnToApi(input))).data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tds-returns'] }),
  });
}

export function useUpdateTDSReturn(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: TDSReturnInput) =>
      mapTdsReturn((await tdsReturnsApi.update(id, tdsReturnToApi(input))).data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tds-returns'] });
      queryClient.invalidateQueries({ queryKey: ['tds-return', id] });
    },
  });
}

export function useValidateTDSReturn(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => mapTdsReturnValidation((await tdsReturnsApi.validate(id)).data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tds-return', id] });
    },
  });
}

export function useGenerateTDSReturnFile(id: string) {
  const queryClient = useQueryClient();
  return useMutation<GeneratedReturnFile, Error, void>({
    mutationFn: async (): Promise<GeneratedReturnFile> => {
      const response = await tdsReturnsApi.generateFile(id, { includeNilReturn: false });
      return {
        fileName: normalizeTdsReturnFileName(
          String(response.data?.fileName ?? `tds-return-${id}.txt`),
        ),
        fileContent: String(response.data?.fileContent ?? ''),
        fileSize: Number(response.data?.fileSize ?? 0),
        fileHash: String(response.data?.fileHash ?? ''),
        generatedAt: String(response.data?.generatedAt ?? ''),
        artifactStatus: String(response.data?.artifactStatus ?? 'WORKING_DRAFT'),
        statutoryStatus: String(response.data?.statutoryStatus ?? 'NOT_FILED'),
        complianceNote: String(response.data?.complianceNote ?? ''),
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tds-return', id] });
    },
  });
}

export function useUpdateTDSReturnFilingDetails(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: FilingDetailsInput) =>
      mapTdsReturn((await tdsReturnsApi.updateFilingDetails(id, filingDetailsToApi(input))).data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tds-return', id] });
      queryClient.invalidateQueries({ queryKey: ['tds-returns'] });
    },
  });
}

export function useReviseTDSReturn(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (reason: string) =>
      mapTdsReturn((await tdsReturnsApi.revise(id, { reason })).data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tds-returns'] }),
  });
}

export function useTDSChallans(params: {
  fromDate?: string;
  toDate?: string;
  status?: string;
  tdsSectionId?: string;
  financialYearId?: string;
  pageSize?: number;
}) {
  return useQuery({
    queryKey: ['tds-challans', params],
    queryFn: async () =>
      normalizePage(
        (
          await tdsChallansApi.list({
            from_date: params.fromDate,
            to_date: params.toDate,
            status: params.status,
            tds_section_id: params.tdsSectionId,
            financial_year_id: params.financialYearId,
            pageSize: params.pageSize ?? 100,
          })
        ).data,
        mapTdsChallan,
      ),
  });
}

export function useTDSChallan(id?: string, includeEntries = true) {
  return useQuery({
    queryKey: ['tds-challan', id, includeEntries],
    enabled: !!id,
    queryFn: async () => mapTdsChallan((await tdsChallansApi.get(id!, includeEntries)).data),
  });
}

export function useCreateTDSChallan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: TDSChallanInput) =>
      mapTdsChallan((await tdsChallansApi.create(tdsChallanToApi(input))).data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tds-challans'] }),
  });
}

export function useUpdateTDSChallan(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: TDSChallanInput) =>
      mapTdsChallan((await tdsChallansApi.update(id, tdsChallanToApi(input))).data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tds-challans'] });
      queryClient.invalidateQueries({ queryKey: ['tds-challan', id] });
    },
  });
}

export function useFinalizeTDSChallan(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => mapTdsChallan((await tdsChallansApi.finalize(id)).data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tds-challans'] });
      queryClient.invalidateQueries({ queryKey: ['tds-challan', id] });
    },
  });
}

export function useRecordTDSChallanPayment(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: TDSChallanPaymentInput) =>
      mapTdsChallan((await tdsChallansApi.recordPayment(id, challanPaymentToApi(input))).data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tds-challans'] });
      queryClient.invalidateQueries({ queryKey: ['tds-challan', id] });
    },
  });
}

export function useVerifyTDSChallanOLTAS(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: TDSChallanOLTASInput) =>
      mapTdsChallan((await tdsChallansApi.verifyOltas(id, challanOltasToApi(input))).data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tds-challans'] });
      queryClient.invalidateQueries({ queryKey: ['tds-challan', id] });
    },
  });
}

export function useAddEntriesToTDSChallan(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (entryIds: string[]) =>
      mapTdsChallan((await tdsChallansApi.addEntries(id, { entry_ids: entryIds })).data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tds-challans'] });
      queryClient.invalidateQueries({ queryKey: ['tds-challan', id] });
      queryClient.invalidateQueries({ queryKey: ['tds-entries'] });
    },
  });
}

export function useRemoveEntriesFromTDSChallan(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (entryIds: string[]) =>
      mapTdsChallan((await tdsChallansApi.removeEntries(id, { entry_ids: entryIds })).data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tds-challans'] });
      queryClient.invalidateQueries({ queryKey: ['tds-challan', id] });
      queryClient.invalidateQueries({ queryKey: ['tds-entries'] });
    },
  });
}

export function useTDSCertificateCandidates(financialYear?: string, quarter?: string) {
  return useQuery({
    queryKey: ['tds-certificate-candidates', financialYear, quarter],
    enabled: !!financialYear && !!quarter,
    queryFn: async () => {
      const response = await tdsForm16AApi.getDeductees({
        financial_year: financialYear!,
        quarter: quarter!,
      });
      return (Array.isArray(response.data) ? response.data : []).map(mapCertificateCandidate);
    },
  });
}

export function useTDSCertificates(financialYear?: string, quarter?: string) {
  return useQuery({
    queryKey: ['tds-certificates', financialYear, quarter],
    enabled: !!financialYear,
    queryFn: async () => {
      const response = await tdsForm16AApi.listCertificates({
        financial_year: financialYear!,
        quarter,
      });
      return (Array.isArray(response.data) ? response.data : []).map(mapCertificateInfo);
    },
  });
}

export function useTDSCertificate(certificateNumber?: string) {
  return useQuery({
    queryKey: ['tds-certificate', certificateNumber],
    enabled: !!certificateNumber,
    queryFn: async () => mapCertificateInfo((await tdsForm16AApi.get(certificateNumber!)).data),
  });
}

export function useGenerateTDSCertificate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: TDSCertificateGenerateInput) =>
      mapCertificateDetail((await tdsForm16AApi.generate(certificateGenerateToApi(input))).data),
    onSuccess: (_, input) => {
      queryClient.invalidateQueries({ queryKey: ['tds-certificates', input.financialYear] });
      queryClient.invalidateQueries({
        queryKey: ['tds-certificate-candidates', input.financialYear, input.quarter],
      });
    },
  });
}

export function useGenerateBulkTDSCertificates() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: { financialYear: string; quarter: string }) => {
      const response = await tdsForm16AApi.generateBulk(
        certificateBulkToApi(input.financialYear, input.quarter),
      );
      return (Array.isArray(response.data) ? response.data : []).map(mapCertificateDetail);
    },
    onSuccess: (_, input) => {
      queryClient.invalidateQueries({ queryKey: ['tds-certificates', input.financialYear] });
      queryClient.invalidateQueries({
        queryKey: ['tds-certificate-candidates', input.financialYear, input.quarter],
      });
    },
  });
}
