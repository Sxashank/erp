/**
 * Entity/Borrower Zod Validation Schemas
 */

import { z } from 'zod';

// Enums
export const entityTypeSchema = z.enum(['CORPORATE', 'INDIVIDUAL', 'LLP', 'PARTNERSHIP', 'TRUST', 'HUF']);
export const entityStatusSchema = z.enum(['PROSPECT', 'ACTIVE', 'INACTIVE', 'BLACKLISTED']);
export const riskCategorySchema = z.enum(['LOW', 'MEDIUM', 'HIGH']);

// PAN validation (Indian PAN format)
const panRegex = /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/;
export const panSchema = z.string().regex(panRegex, 'Invalid PAN format (e.g., ABCDE1234F)');

// CIN validation (Company Identification Number)
const cinRegex = /^[UL][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}$/;
export const cinSchema = z.string().regex(cinRegex, 'Invalid CIN format').optional().or(z.literal(''));

// GSTIN validation
const gstinRegex = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/;
export const gstinSchema = z.string().regex(gstinRegex, 'Invalid GSTIN format').optional().or(z.literal(''));

// Phone validation (Indian format)
const phoneRegex = /^[6-9]\d{9}$/;
export const phoneSchema = z.string().regex(phoneRegex, 'Invalid mobile number').optional().or(z.literal(''));

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
  entity_type: entityTypeSchema,
  legal_name: z.string().min(2, 'Legal name must be at least 2 characters').max(200),
  trade_name: z.string().max(200).optional(),
  cin: z.string().optional().refine(
    (val) => !val || cinRegex.test(val),
    'Invalid CIN format'
  ),
  pan: panSchema,
  gstin: z.string().optional().refine(
    (val) => !val || gstinRegex.test(val),
    'Invalid GSTIN format'
  ),
  tan: z.string().max(20).optional(),
  constitution_date: z.string().optional(),
  risk_category: riskCategorySchema.optional().default('MEDIUM'),
  relationship_manager_id: z.string().uuid().optional(),
  remarks: z.string().max(500).optional(),
  status: z.string().optional(),
  date_of_incorporation: z.string().optional(),
});

// Create schema with refinements for validation
export const createEntitySchema = entityBaseSchema.superRefine((data, ctx) => {
  // CIN required for CORPORATE
  if (data.entity_type === 'CORPORATE' && !data.cin) {
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

export const contactTypeSchema = z.enum(['DIRECTOR', 'PROMOTER', 'AUTHORIZED_SIGNATORY', 'KEY_PERSON', 'GUARANTOR']);

export const entityContactSchema = z.object({
  contact_type: contactTypeSchema,
  name: z.string().min(2, 'Name must be at least 2 characters').max(100),
  designation: z.string().max(100).optional(),
  din: z.string().max(20).optional(),
  pan: z.string().optional().refine(
    (val) => !val || panRegex.test(val),
    'Invalid PAN format'
  ),
  phone: z.string().optional(),
  mobile: z.string().optional().refine(
    (val) => !val || phoneRegex.test(val),
    'Invalid mobile number'
  ),
  email: emailSchema,
  is_primary: z.boolean().default(false),
});

// ============== Address Schemas ==============

export const addressTypeSchema = z.enum(['REGISTERED', 'CORRESPONDENCE', 'PLANT', 'WAREHOUSE', 'BRANCH']);

export const entityAddressSchema = z.object({
  address_type: addressTypeSchema,
  address_line1: z.string().min(5, 'Address must be at least 5 characters').max(200),
  address_line2: z.string().max(200).optional(),
  city: z.string().min(2).max(100),
  state: z.string().min(2).max(100),
  pincode: pincodeSchema,
  country: z.string().default('India'),
  is_primary: z.boolean().default(false),
});

// ============== Bank Account Schemas ==============

export const accountTypeSchema = z.enum(['CURRENT', 'SAVINGS', 'CC', 'OD']);

export const entityBankAccountSchema = z.object({
  bank_name: z.string().min(2).max(100),
  branch_name: z.string().min(2).max(100),
  account_number: z.string().min(8).max(20),
  ifsc_code: ifscSchema,
  account_type: accountTypeSchema,
  is_primary: z.boolean().default(false),
  is_verified: z.boolean().default(false),
});

// ============== Financial Schemas ==============

export const entityFinancialSchema = z.object({
  financial_year: z.string().regex(/^\d{4}-\d{2}$/, 'Format: YYYY-YY (e.g., 2024-25)'),
  audited: z.boolean().default(false),

  // Balance Sheet
  total_assets: z.number().positive().optional(),
  fixed_assets: z.number().nonnegative().optional(),
  current_assets: z.number().nonnegative().optional(),
  total_liabilities: z.number().nonnegative().optional(),
  net_worth: z.number().optional(),
  long_term_debt: z.number().nonnegative().optional(),
  short_term_debt: z.number().nonnegative().optional(),

  // P&L
  revenue: z.number().nonnegative().optional(),
  operating_profit: z.number().optional(),
  profit_before_tax: z.number().optional(),
  profit_after_tax: z.number().optional(),
  depreciation: z.number().nonnegative().optional(),
  interest_expense: z.number().nonnegative().optional(),

  // Ratios (calculated or input)
  current_ratio: z.number().nonnegative().optional(),
  debt_equity_ratio: z.number().nonnegative().optional(),
  dscr: z.number().optional(),
  interest_coverage: z.number().optional(),
});

// ============== KYC Document Schemas ==============

export const kycVerificationStatusSchema = z.enum(['PENDING', 'VERIFIED', 'REJECTED']);

export const entityKYCDocumentSchema = z.object({
  document_type: z.string().min(2).max(50),
  document_number: z.string().max(50).optional(),
  issue_date: z.string().optional(),
  expiry_date: z.string().optional(),
  file_path: z.string().optional(),
  file_name: z.string().optional(),
  verification_status: kycVerificationStatusSchema.default('PENDING'),
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
