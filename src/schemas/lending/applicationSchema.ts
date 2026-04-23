/**
 * Loan Application Zod Validation Schemas
 */

import { z } from 'zod';

// Enums
export const interestTypeSchema = z.enum(['FIXED', 'FLOATING']);
export const repaymentFrequencySchema = z.enum(['MONTHLY', 'QUARTERLY', 'HALF_YEARLY', 'YEARLY', 'BULLET']);
export const repaymentModeSchema = z.enum(['EMI', 'STRUCTURED', 'BULLET', 'BALLOON', 'STEP_UP', 'STEP_DOWN']);

// ============== Application Step Schemas ==============

// Step 1: Entity & Product Selection
export const applicationStep1Schema = z.object({
  entity_id: z.string().uuid('Please select an entity'),
  product_id: z.string().uuid('Please select a product'),
});

// Step 2: Loan Details
export const applicationStep2Schema = z.object({
  requested_amount: z.number()
    .positive('Amount must be greater than 0')
    .max(100000000000, 'Amount exceeds maximum limit (1000 Cr)'),
  requested_tenure_months: z.number()
    .int('Tenure must be a whole number')
    .min(1, 'Minimum tenure is 1 month')
    .max(360, 'Maximum tenure is 360 months'),
  purpose: z.string()
    .min(10, 'Purpose must be at least 10 characters')
    .max(500, 'Purpose must not exceed 500 characters'),
  interest_type: interestTypeSchema.optional(),
  proposed_rate: z.number()
    .positive()
    .max(50, 'Rate cannot exceed 50%')
    .optional(),
  moratorium_months: z.number()
    .int()
    .nonnegative()
    .max(36, 'Maximum moratorium is 36 months')
    .optional()
    .default(0),
  repayment_frequency: repaymentFrequencySchema.optional(),
});

// Step 3: Project Details (for Project Finance)
export const applicationStep3Schema = z.object({
  project_name: z.string().min(2).max(200).optional(),
  project_cost: z.number().positive().optional(),
  promoter_contribution: z.number().nonnegative().optional(),
  bank_finance: z.number().nonnegative().optional(),
  project_start_date: z.string().optional(),
  project_end_date: z.string().optional(),
  milestones: z.array(
    z.object({
      milestone_name: z.string().min(2).max(100),
      description: z.string().max(500).optional(),
      expected_completion_date: z.string().optional(),
      disbursement_percent: z.number().min(0).max(100),
    })
  ).optional(),
}).superRefine((data, ctx) => {
  // Validate promoter contribution + bank finance = project cost
  if (data.project_cost && data.promoter_contribution && data.bank_finance) {
    const total = data.promoter_contribution + data.bank_finance;
    if (Math.abs(total - data.project_cost) > 1) { // Allow 1 rupee variance
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Promoter contribution + Bank finance must equal Project cost',
        path: ['bank_finance'],
      });
    }
  }

  // Validate milestones total = 100%
  if (data.milestones && data.milestones.length > 0) {
    const totalPercent = data.milestones.reduce((sum, m) => sum + m.disbursement_percent, 0);
    if (Math.abs(totalPercent - 100) > 0.01) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: `Milestone disbursement percentages must total 100% (current: ${totalPercent.toFixed(2)}%)`,
        path: ['milestones'],
      });
    }
  }
});

// Step 4: Security/Collateral
export const securityTypeSchema = z.enum(['PRIMARY', 'COLLATERAL']);
export const securityNatureSchema = z.enum([
  'PROPERTY',
  'FIXED_DEPOSIT',
  'RECEIVABLES',
  'INVENTORY',
  'EQUIPMENT',
  'SHARES',
  'GUARANTEE',
  'OTHER',
]);

export const loanSecuritySchema = z.object({
  security_type: securityTypeSchema,
  nature: securityNatureSchema,
  description: z.string().min(10).max(500),
  declared_value: z.number().positive().optional(),
  assessed_value: z.number().positive().optional(),
  margin_percent: z.number().min(0).max(100).optional(),

  // Property specific
  property_type: z.string().max(100).optional(),
  property_address: z.string().max(500).optional(),
  survey_number: z.string().max(100).optional(),
  area_sqft: z.number().positive().optional(),

  // Documentation
  document_type: z.string().max(100).optional(),
  document_number: z.string().max(100).optional(),
  document_date: z.string().optional(),

  charge_type: z.enum(['EXCLUSIVE', 'PARI_PASSU', 'SECOND']).optional(),
});

export const applicationStep4Schema = z.object({
  securities: z.array(loanSecuritySchema).min(1, 'At least one security is required'),
});

// Step 5: Documents
export const applicationDocumentSchema = z.object({
  checklist_id: z.string().uuid().optional(),
  document_name: z.string().min(2).max(200),
  file_path: z.string().optional(),
  file_name: z.string().optional(),
  remarks: z.string().max(500).optional(),
});

export const applicationStep5Schema = z.object({
  documents: z.array(applicationDocumentSchema),
});

// Step 6: Review (combines all steps)
export const applicationStep6Schema = z.object({
  terms_accepted: z.boolean().refine((val) => val === true, {
    message: 'You must accept the terms and conditions',
  }),
});

// ============== Full Application Schema ==============

export const createApplicationSchema = z.object({
  entity_id: z.string().uuid(),
  product_id: z.string().uuid(),
  requested_amount: z.number().positive(),
  requested_tenure_months: z.number().int().positive(),
  purpose: z.string().min(10).max(500),

  // Optional fields
  project_name: z.string().optional(),
  project_cost: z.number().positive().optional(),
  promoter_contribution: z.number().nonnegative().optional(),
  bank_finance: z.number().nonnegative().optional(),
  interest_type: interestTypeSchema.optional(),
  proposed_rate: z.number().positive().optional(),
  moratorium_months: z.number().int().nonnegative().optional(),
  repayment_frequency: repaymentFrequencySchema.optional(),
});

export const updateApplicationSchema = createApplicationSchema.partial();

// ============== Application Fee Schema ==============

export const applicationFeeSchema = z.object({
  fee_type: z.string(),
  fee_name: z.string(),
  calculated_amount: z.number().nonnegative(),
  gst_amount: z.number().nonnegative(),
  total_amount: z.number().nonnegative(),
  paid_amount: z.number().nonnegative().default(0),
});

// ============== Workflow Schema ==============

export const submitApplicationSchema = z.object({
  application_id: z.string().uuid(),
  remarks: z.string().max(500).optional(),
});

export const approveApplicationSchema = z.object({
  application_id: z.string().uuid(),
  remarks: z.string().min(1, 'Remarks are required').max(1000),
  action: z.enum(['APPROVE', 'REJECT', 'RETURN']),
});

// ============== Type Exports ==============

export type ApplicationStep1Input = z.infer<typeof applicationStep1Schema>;
export type ApplicationStep2Input = z.infer<typeof applicationStep2Schema>;
export type ApplicationStep3Input = z.infer<typeof applicationStep3Schema>;
export type ApplicationStep4Input = z.infer<typeof applicationStep4Schema>;
export type ApplicationStep5Input = z.infer<typeof applicationStep5Schema>;
export type ApplicationStep6Input = z.infer<typeof applicationStep6Schema>;
export type CreateApplicationInput = z.infer<typeof createApplicationSchema>;
export type UpdateApplicationInput = z.infer<typeof updateApplicationSchema>;
export type LoanSecurityInput = z.infer<typeof loanSecuritySchema>;
