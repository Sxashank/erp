import { z } from 'zod';

const optionalDate = z.string().date().optional().or(z.literal(''));
const optionalTrimmed = z.string().trim().optional();

export const gstRateSchema = z
  .object({
    code: z.string().trim().min(1, 'Required').max(20),
    name: z.string().trim().min(1, 'Required').max(100),
    rate: z.coerce.number().min(0).max(100),
    cgstRate: z.coerce.number().min(0).max(100),
    sgstRate: z.coerce.number().min(0).max(100),
    igstRate: z.coerce.number().min(0).max(100),
    cessRate: z.coerce.number().min(0).max(100).default(0),
    description: optionalTrimmed,
    effectiveFrom: z.string().date(),
    effectiveTo: optionalDate,
    isActive: z.boolean().default(true),
  })
  .superRefine((value, ctx) => {
    if (value.cgstRate + value.sgstRate !== value.rate) {
      ctx.addIssue({
        code: 'custom',
        path: ['rate'],
        message: 'Total rate must equal CGST + SGST for intra-state supplies',
      });
    }
    if (value.igstRate !== value.rate) {
      ctx.addIssue({
        code: 'custom',
        path: ['igstRate'],
        message: 'IGST rate must equal total rate for inter-state supplies',
      });
    }
  });

export type GSTRateFormValues = z.input<typeof gstRateSchema>;
export type GSTRateFormInput = z.output<typeof gstRateSchema>;

export const gstRegistrationSchema = z.object({
  organizationId: z.string().uuid('Select organization'),
  gstin: z.string().trim().length(15, 'GSTIN must be 15 characters'),
  legalName: z.string().trim().min(1, 'Required').max(200),
  tradeName: optionalTrimmed,
  registrationType: z.string().trim().min(1, 'Required'),
  stateCode: z.string().trim().length(2, 'State code must be 2 digits'),
  stateName: z.string().trim().min(1, 'Required').max(50),
  address: optionalTrimmed,
  pincode: z.string().trim().length(6, 'PIN code must be 6 digits').optional().or(z.literal('')),
  isEInvoiceEnabled: z.boolean().default(false),
  eInvoiceUsername: optionalTrimmed,
  eInvoicePassword: optionalTrimmed,
  isEWayBillEnabled: z.boolean().default(false),
  unitId: z.string().uuid().optional().or(z.literal('')),
  isActive: z.boolean().default(true),
});

export type GSTRegistrationFormValues = z.input<typeof gstRegistrationSchema>;
export type GSTRegistrationFormInput = z.output<typeof gstRegistrationSchema>;

export const hsnSacSchema = z.object({
  code: z.string().trim().min(1, 'Required').max(20),
  description: z.string().trim().min(1, 'Required'),
  hsnSacType: z.enum(['HSN', 'SAC']),
  chapter: optionalTrimmed,
  section: optionalTrimmed,
  gstRateId: z.string().uuid().optional().or(z.literal('')),
  unitOfMeasurement: optionalTrimmed,
  isActive: z.boolean().default(true),
});

export type HSNSACFormValues = z.input<typeof hsnSacSchema>;
export type HSNSACFormInput = z.output<typeof hsnSacSchema>;

export const tdsSectionSchema = z.object({
  sectionCode: z.string().trim().min(1, 'Required').max(20),
  sectionName: z.string().trim().min(1, 'Required').max(200),
  description: optionalTrimmed,
  rateIndividual: z.coerce.number().min(0).max(100),
  rateCompany: z.coerce.number().min(0).max(100),
  rateNoPan: z.coerce.number().min(20).max(100),
  rateLowerDeduction: z.coerce.number().min(0).max(100).optional(),
  thresholdSingle: z.coerce.number().nonnegative(),
  thresholdAnnual: z.coerce.number().nonnegative(),
  isTcs: z.boolean().default(false),
  surchargeApplicable: z.boolean().default(false),
  cessRate: z.coerce.number().min(0).max(100),
  effectiveFrom: z.string().date(),
  effectiveTo: optionalDate,
  returnForm: z.enum(['24Q', '26Q', '27Q', '27EQ']).optional(),
  natureOfPaymentCode: optionalTrimmed,
  isActive: z.boolean().default(true),
});

export type TDSSectionFormValues = z.input<typeof tdsSectionSchema>;
export type TDSSectionFormInput = z.output<typeof tdsSectionSchema>;

export const tdsEntrySchema = z.object({
  organizationId: z.string().uuid('Select organization'),
  tdsSectionId: z.string().uuid('Select section'),
  financialYearId: z.string().uuid().optional().or(z.literal('')),
  voucherId: z.string().uuid().optional().or(z.literal('')),
  vendorId: z.string().uuid().optional().or(z.literal('')),
  deducteeName: z.string().trim().min(1, 'Required').max(200),
  deducteePan: z.string().trim().max(10).optional().or(z.literal('')),
  deducteeType: z.enum(['INDIVIDUAL', 'COMPANY', 'FIRM', 'HUF', 'AOP', 'TRUST', 'GOVERNMENT', 'OTHER']),
  deducteeAddress: optionalTrimmed,
  deductionDate: z.string().date(),
  baseAmount: z.number().nonnegative(),
  tdsRate: z.number().min(0).max(100),
  tdsAmount: z.number().nonnegative(),
  surcharge: z.number().nonnegative(),
  cess: z.number().nonnegative(),
  totalTds: z.number().nonnegative(),
  lowerDeductionCertNo: optionalTrimmed,
  remarks: optionalTrimmed,
  challanStatus: z.enum(['PENDING', 'PAID', 'VERIFIED', 'NOT_APPLICABLE']).optional(),
  challanNumber: optionalTrimmed,
  challanDate: optionalDate,
  bankName: optionalTrimmed,
  bsrCode: optionalTrimmed,
  certificateNumber: optionalTrimmed,
  certificateDate: optionalDate,
  returnQuarter: z.enum(['Q1', 'Q2', 'Q3', 'Q4']).optional(),
  returnFiled: z.boolean(),
  acknowledgmentNumber: optionalTrimmed,
  isActive: z.boolean(),
});

export type TDSEntryFormValues = z.input<typeof tdsEntrySchema>;
export type TDSEntryFormInput = z.output<typeof tdsEntrySchema>;

export const tdsReturnSchema = z.object({
  organizationId: z.string().uuid('Select organization'),
  returnType: z.enum(['24Q', '26Q', '27Q', '27EQ']),
  financialYearId: z.string().uuid('Select financial year'),
  financialYear: z.string().trim().min(1, 'Required'),
  quarter: z.enum(['Q1', 'Q2', 'Q3', 'Q4']),
  deductorTan: z.string().trim().length(10, 'TAN must be 10 characters'),
  deductorName: z.string().trim().min(1, 'Required').max(200),
  deductorPan: z.string().trim().max(10).optional().or(z.literal('')),
  deductorType: optionalTrimmed,
  deductorCategory: optionalTrimmed,
  deductorAddress: optionalTrimmed,
  deductorCity: optionalTrimmed,
  deductorState: optionalTrimmed,
  deductorPincode: optionalTrimmed,
  deductorEmail: z.string().email('Enter a valid email').optional().or(z.literal('')),
  deductorPhone: optionalTrimmed,
  responsiblePersonName: optionalTrimmed,
  responsiblePersonDesignation: optionalTrimmed,
  responsiblePersonAddress: optionalTrimmed,
  responsiblePersonPan: z.string().trim().max(10).optional().or(z.literal('')),
  remarks: optionalTrimmed,
});

export type TDSReturnFormValues = z.input<typeof tdsReturnSchema>;
export type TDSReturnFormInput = z.output<typeof tdsReturnSchema>;

export const tdsReturnFilingSchema = z.object({
  provisionalReceiptNumber: optionalTrimmed,
  tokenNumber: optionalTrimmed,
  acknowledgmentNumber: optionalTrimmed,
  filedDate: optionalDate,
});

export type TDSReturnFilingFormValues = z.input<typeof tdsReturnFilingSchema>;
export type TDSReturnFilingFormInput = z.output<typeof tdsReturnFilingSchema>;

export const tdsChallanSchema = z.object({
  organizationId: z.string().uuid('Select organization'),
  tdsSectionId: z.string().uuid('Select section'),
  financialYearId: z.string().uuid('Select financial year'),
  assessmentYear: z.string().trim().min(1, 'Required').max(10),
  periodFrom: z.string().date(),
  periodTo: z.string().date(),
  challanType: z.enum(['281']),
  minorHead: optionalTrimmed,
  deductorTan: z.string().trim().length(10, 'TAN must be 10 characters'),
  deductorName: z.string().trim().min(1, 'Required').max(200),
  deductorAddress: optionalTrimmed,
  returnQuarter: z.enum(['Q1', 'Q2', 'Q3', 'Q4']).optional(),
  entryIds: z.array(z.string().uuid()),
  interestAmount: z.number().nonnegative(),
  penaltyAmount: z.number().nonnegative(),
  otherAmount: z.number().nonnegative(),
  remarks: optionalTrimmed,
});

export type TDSChallanFormValues = z.input<typeof tdsChallanSchema>;
export type TDSChallanFormInput = z.output<typeof tdsChallanSchema>;

export const tdsChallanPaymentSchema = z.object({
  challanNumber: z.string().trim().min(1, 'Required').max(50),
  bsrCode: z.string().trim().min(1, 'Required').max(10),
  serialNumber: optionalTrimmed,
  paymentDate: z.string().date(),
  paymentMode: z.enum(['ONLINE', 'CHEQUE', 'DD']),
  bankName: z.string().trim().min(1, 'Required').max(100),
  bankBranch: optionalTrimmed,
  bankAccountNumber: optionalTrimmed,
  chequeDdNumber: optionalTrimmed,
  chequeDdDate: optionalDate,
});

export type TDSChallanPaymentFormValues = z.input<typeof tdsChallanPaymentSchema>;
export type TDSChallanPaymentFormInput = z.output<typeof tdsChallanPaymentSchema>;

export const tdsChallanOltasSchema = z.object({
  oltasAcknowledgment: z.string().trim().min(1, 'Required').max(50),
  oltasStatus: z.string().trim().min(1, 'Required').max(20),
  oltasVerifiedAt: z.string().date(),
});

export type TDSChallanOltasFormValues = z.input<typeof tdsChallanOltasSchema>;
export type TDSChallanOltasFormInput = z.output<typeof tdsChallanOltasSchema>;

export const tdsCertificateSchema = z.object({
  financialYear: z.string().trim().min(1, 'Required'),
  quarter: z.enum(['Q1', 'Q2', 'Q3', 'Q4']),
  deducteePan: z.string().trim().min(1, 'Select deductee').max(10),
  tdsSectionId: z.string().uuid('Select section'),
});

export type TDSCertificateFormValues = z.input<typeof tdsCertificateSchema>;
export type TDSCertificateFormInput = z.output<typeof tdsCertificateSchema>;
