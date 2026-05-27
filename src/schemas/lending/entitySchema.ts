/**
 * Entity/Borrower Zod Validation Schemas
 */

import { z } from 'zod';

// Policy option sets are loaded from lending masters in the UI; validation
// only enforces that a configured code is submitted.
export const entityTypeSchema = z.string().min(1, 'Entity type is required');
export const entityStatusSchema = z.enum(['PROSPECT', 'ACTIVE', 'INACTIVE', 'BLACKLISTED']);
export const riskCategorySchema = z.string().min(1, 'Risk category is required');

// PAN validation (Indian PAN format)
const panRegex = /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/;
export const panSchema = z.string().regex(panRegex, 'Invalid PAN format (e.g., ABCDE1234F)');

// CIN validation (Company Identification Number)
const cinRegex = /^[UL][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}$/;
export const cinSchema = z
  .string()
  .regex(cinRegex, 'Invalid CIN format')
  .optional()
  .or(z.literal(''));

// GSTIN validation
const gstinRegex = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/;
export const gstinSchema = z
  .string()
  .regex(gstinRegex, 'Invalid GSTIN format')
  .optional()
  .or(z.literal(''));

// Phone validation (Indian format)
const phoneRegex = /^[6-9]\d{9}$/;
export const phoneSchema = z
  .string()
  .regex(phoneRegex, 'Invalid mobile number')
  .optional()
  .or(z.literal(''));

// Email validation
export const emailSchema = z.string().email('Invalid email address').optional().or(z.literal(''));

// Pincode validation (Indian)
const pincodeRegex = /^[1-9][0-9]{5}$/;
export const pincodeSchema = z.string().regex(pincodeRegex, 'Invalid pincode');

// IFSC validation
const ifscRegex = /^[A-Z]{4}0[A-Z0-9]{6}$/;
export const ifscSchema = z.string().regex(ifscRegex, 'Invalid IFSC code');

// ============== Entity Schemas ==============

// Base schema without refinements (for partial/extend operations)
const entityBaseSchema = z.object({
  entityType: entityTypeSchema,
  legalName: z.string().min(2, 'Legal name must be at least 2 characters').max(200),
  tradeName: z.string().max(200).optional(),
  cin: z
    .string()
    .optional()
    .refine((val) => !val || cinRegex.test(val), 'Invalid CIN format'),
  pan: panSchema,
  gstin: z
    .string()
    .optional()
    .refine((val) => !val || gstinRegex.test(val), 'Invalid GSTIN format'),
  tan: z.string().max(20).optional(),
  constitutionDate: z.string().optional(),
  riskCategory: riskCategorySchema,
  relationshipManagerId: z.string().uuid().optional(),
  remarks: z.string().max(500).optional(),
  status: z.string().optional(),
  dateOfIncorporation: z.string().optional(),
});

// Create schema with refinements for validation
export const createEntitySchema = entityBaseSchema.superRefine((data, ctx) => {
  // CIN required for CORPORATE
  if (data.entityType === 'CORPORATE' && !data.cin) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: 'CIN is required for Corporate entities',
      path: ['cin'],
    });
  }
});

// Update schema uses base (without refinement) to allow partial
export const updateEntitySchema = entityBaseSchema.partial().extend({
  status: entityStatusSchema.optional(),
});

// ============== Contact Schemas ==============

export const contactTypeSchema = z.string().min(1, 'Contact type is required');

export const entityContactSchema = z.object({
  contactType: contactTypeSchema,
  name: z.string().min(2, 'Name must be at least 2 characters').max(100),
  designation: z.string().max(100).optional(),
  din: z.string().max(20).optional(),
  pan: z
    .string()
    .optional()
    .refine((val) => !val || panRegex.test(val), 'Invalid PAN format'),
  phone: z.string().optional(),
  mobile: z
    .string()
    .optional()
    .refine((val) => !val || phoneRegex.test(val), 'Invalid mobile number'),
  email: emailSchema,
  isPrimary: z.boolean().default(false),
});

// ============== Address Schemas ==============

export const addressTypeSchema = z.string().min(1, 'Address type is required');

export const entityAddressSchema = z.object({
  addressType: addressTypeSchema,
  addressLine1: z.string().min(5, 'Address must be at least 5 characters').max(200),
  addressLine2: z.string().max(200).optional(),
  city: z.string().min(2).max(100),
  state: z.string().min(2).max(100),
  pincode: pincodeSchema,
  country: z.string().default('India'),
  isPrimary: z.boolean().default(false),
});

// ============== Bank Account Schemas ==============

export const accountTypeSchema = z.string().min(1, 'Account type is required');

export const entityBankAccountSchema = z.object({
  bankName: z.string().min(2).max(100),
  branchName: z.string().min(2).max(100),
  accountNumber: z.string().min(8).max(20),
  ifscCode: ifscSchema,
  accountType: accountTypeSchema,
  isPrimary: z.boolean().default(false),
  isVerified: z.boolean().default(false),
});

// ============== Financial Schemas ==============

export const entityFinancialSchema = z.object({
  financialYear: z.string().regex(/^\d{4}-\d{2}$/, 'Format: YYYY-YY (e.g., 2024-25)'),
  audited: z.boolean().default(false),

  // Balance Sheet
  totalAssets: z.number().positive().optional(),
  fixedAssets: z.number().nonnegative().optional(),
  currentAssets: z.number().nonnegative().optional(),
  totalLiabilities: z.number().nonnegative().optional(),
  netWorth: z.number().optional(),
  longTermDebt: z.number().nonnegative().optional(),
  shortTermDebt: z.number().nonnegative().optional(),

  // P&L
  revenue: z.number().nonnegative().optional(),
  operatingProfit: z.number().optional(),
  profitBeforeTax: z.number().optional(),
  profitAfterTax: z.number().optional(),
  depreciation: z.number().nonnegative().optional(),
  interestExpense: z.number().nonnegative().optional(),

  // Ratios (calculated or input)
  currentRatio: z.number().nonnegative().optional(),
  debtEquityRatio: z.number().nonnegative().optional(),
  dscr: z.number().optional(),
  interestCoverage: z.number().optional(),
});

// ============== KYC Document Schemas ==============

export const kycVerificationStatusSchema = z.enum(['PENDING', 'VERIFIED', 'REJECTED']);

export const entityKYCDocumentSchema = z.object({
  documentType: z.string().min(2).max(50),
  documentNumber: z.string().max(50).optional(),
  issueDate: z.string().optional(),
  expiryDate: z.string().optional(),
  filePath: z.string().optional(),
  fileName: z.string().optional(),
  verificationStatus: kycVerificationStatusSchema.default('PENDING'),
  remarks: z.string().max(500).optional(),
});

// ============== Type Exports ==============

export type CreateEntityInput = z.infer<typeof createEntitySchema>;
export type UpdateEntityInput = z.infer<typeof updateEntitySchema>;
export type EntityContactInput = z.infer<typeof entityContactSchema>;
export type EntityAddressInput = z.infer<typeof entityAddressSchema>;
export type EntityBankAccountInput = z.infer<typeof entityBankAccountSchema>;
export type EntityFinancialInput = z.infer<typeof entityFinancialSchema>;
export type EntityKYCDocumentInput = z.infer<typeof entityKYCDocumentSchema>;
