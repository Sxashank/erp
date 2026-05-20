/**
 * Borrower Portal Loan Application — zod schemas.
 *
 * Money amounts are Decimal-as-string per CLAUDE.md §6.2 — coerce only at
 * the math boundary.  Step-scoped schemas drive `form.trigger([...])` in
 * the wizard so each step validates its own slice.
 */

import { z } from 'zod';

const POSITIVE_DECIMAL = /^\d+(\.\d{1,2})?$/;

export const entityAndProductSchema = z.object({
  entityId: z.string().uuid('Pick an entity'),
  productId: z.string().uuid('Pick a loan product'),
});
export type EntityAndProductInput = z.infer<typeof entityAndProductSchema>;

export const loanDetailsSchema = z.object({
  requestedAmount: z
    .string()
    .regex(POSITIVE_DECIMAL, 'Enter a positive amount')
    .refine((v) => Number(v) > 0, 'Amount must be greater than zero'),
  tenureMonths: z
    .number()
    .int('Tenure must be a whole number of months')
    .min(1, 'Tenure must be at least 1 month')
    .max(360, 'Tenure cannot exceed 360 months'),
  purposeDescription: z
    .string()
    .trim()
    .min(10, 'Describe the purpose of the loan (at least 10 characters)')
    .max(2000, 'Purpose description is too long'),
  projectName: z.string().trim().max(200).optional().or(z.literal('')),
  projectLocation: z.string().trim().max(500).optional().or(z.literal('')),
  projectCost: z
    .string()
    .regex(POSITIVE_DECIMAL, 'Enter a positive amount')
    .optional()
    .or(z.literal('')),
  shipyardName: z.string().trim().max(200).optional().or(z.literal('')),
  maritimeSegment: z.string().trim().max(200).optional().or(z.literal('')),
  lenderName: z.string().trim().max(200).optional().or(z.literal('')),
  lenderBranch: z.string().trim().max(200).optional().or(z.literal('')),
  sanctionReference: z.string().trim().max(100).optional().or(z.literal('')),
  declarationAccepted: z.boolean().refine((v) => v, {
    message: 'Confirm the borrower declaration before submission',
  }),
});
export type LoanDetailsInput = z.infer<typeof loanDetailsSchema>;

export const fundingSourceLineSchema = z.object({
  sourceCode: z.string().trim().min(2).max(50),
  sourceLabel: z.string().trim().min(2).max(200),
  amount: z
    .string()
    .regex(POSITIVE_DECIMAL, 'Enter a valid amount')
    .refine((v) => Number(v) >= 0, 'Amount cannot be negative'),
  remarks: z.string().nullable().optional(),
});
export type FundingSourceLineInput = z.infer<typeof fundingSourceLineSchema>;

export const lenderLoanLineSchema = z.object({
  loanType: z.string().trim().min(2, 'Loan type is required').max(80),
  loanAmount: z
    .string()
    .regex(POSITIVE_DECIMAL, 'Enter a valid amount')
    .refine((v) => Number(v) > 0, 'Loan amount must be greater than zero'),
  lenderName: z.string().trim().min(2, 'Lender name is required').max(200),
  lenderCategory: z.string().trim().max(80).optional().or(z.literal('')),
  lenderContact: z.string().trim().max(50).optional().or(z.literal('')),
  lenderEmail: z.string().trim().email('Enter a valid email').optional().or(z.literal('')),
  lenderAddress: z.string().trim().max(500).optional().or(z.literal('')),
  lenderState: z.string().trim().max(100).optional().or(z.literal('')),
  lenderDistrict: z.string().trim().max(100).optional().or(z.literal('')),
  lenderPincode: z.string().trim().max(20).optional().or(z.literal('')),
  sanctionReference: z.string().trim().max(100).optional().or(z.literal('')),
  sanctionDate: z.string().date().optional().or(z.literal('')),
  interestRatePercent: z
    .string()
    .regex(POSITIVE_DECIMAL, 'Enter a valid rate')
    .refine((v) => Number(v) >= 0 && Number(v) <= 100, 'Rate must be between 0 and 100')
    .optional()
    .or(z.literal('')),
  emiPeriodicity: z.string().trim().max(30).optional().or(z.literal('')),
  interestDebitingPeriodicity: z.string().trim().max(30).optional().or(z.literal('')),
  loanAccountNumber: z.string().trim().max(80).optional().or(z.literal('')),
  ifscCode: z.string().trim().max(20).optional().or(z.literal('')),
  securityType: z.string().trim().max(100).optional().or(z.literal('')),
  disbursementCallType: z.string().trim().max(40).optional().or(z.literal('')),
  emiAmount: z
    .string()
    .regex(POSITIVE_DECIMAL, 'Enter a valid amount')
    .optional()
    .or(z.literal('')),
  emiDueDate: z.string().date().optional().or(z.literal('')),
});
export type LenderLoanLineInput = z.infer<typeof lenderLoanLineSchema>;

export const fundingAndLenderSchema = z.object({
  fundingSources: z.array(fundingSourceLineSchema),
  lenderLoans: z.array(lenderLoanLineSchema).min(1, 'Add at least one lender loan'),
});
export type FundingAndLenderInput = z.infer<typeof fundingAndLenderSchema>;

export const fundUtilizationLineSchema = z.object({
  categoryId: z.string().uuid(),
  categoryLabel: z.string().optional(),
  amount: z
    .string()
    .regex(POSITIVE_DECIMAL, 'Enter a positive amount')
    .refine((v) => Number(v) >= 0, 'Amount cannot be negative'),
  remarks: z.string().nullable().optional(),
});
export type FundUtilizationLineInput = z.infer<typeof fundUtilizationLineSchema>;

export const fundUtilizationSchema = z.object({
  lines: z.array(fundUtilizationLineSchema).min(1, 'Add at least one utilisation line'),
});
export type FundUtilizationInput = z.infer<typeof fundUtilizationSchema>;

export const submitApplicationSchema = entityAndProductSchema
  .merge(loanDetailsSchema)
  .merge(fundingAndLenderSchema)
  .merge(fundUtilizationSchema)
  .superRefine((data, ctx) => {
    const sum = data.lines.reduce((acc, l) => acc + Number(l.amount || 0), 0);
    const requested = Number(data.requestedAmount || 0);
    if (Math.abs(sum - requested) > 0.01) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['lines'],
        message: `Utilisation total (${sum.toFixed(2)}) must equal the requested amount (${requested.toFixed(2)})`,
      });
    }
    const lenderTotal = data.lenderLoans.reduce((acc, l) => acc + Number(l.loanAmount || 0), 0);
    if (Math.abs(lenderTotal - requested) > 0.01) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['lenderLoans'],
        message: `Lender loan total (${lenderTotal.toFixed(2)}) must equal the requested amount (${requested.toFixed(2)})`,
      });
    }
    const projectCost = Number(data.projectCost || 0);
    const fundingTotal = data.fundingSources.reduce((acc, l) => acc + Number(l.amount || 0), 0);
    if (projectCost > 0 && Math.abs(fundingTotal - projectCost) > 0.01) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['fundingSources'],
        message: `Funding-source total (${fundingTotal.toFixed(2)}) must equal the project cost (${projectCost.toFixed(2)})`,
      });
    }
  });
export type SubmitApplicationInput = z.infer<typeof submitApplicationSchema>;
