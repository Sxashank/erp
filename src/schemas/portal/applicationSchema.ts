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
  declarationAccepted: z.boolean().refine((v) => v, {
    message: 'Confirm the borrower declaration before submission',
  }),
});
export type LoanDetailsInput = z.infer<typeof loanDetailsSchema>;

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
  });
export type SubmitApplicationInput = z.infer<typeof submitApplicationSchema>;
