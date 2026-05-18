import { z } from 'zod';

export const sanctionSchema = z.object({
  applicationId: z.string().min(1, 'Application is required'),
  sanctionedAmount: z.number().positive('Sanctioned amount is required'),
  interestType: z.enum(['FIXED', 'FLOATING']),
  spreadBps: z.number().min(0),
  effectiveRate: z.number().min(0).max(100),
  tenureMonths: z.number().int().min(1, 'Tenure is required'),
  moratoriumMonths: z.number().int().min(0),
  repaymentFrequency: z.enum(['MONTHLY', 'QUARTERLY', 'HALF_YEARLY', 'YEARLY', 'BULLET']),
  repaymentMode: z.enum(['EMI', 'STRUCTURED', 'BULLET']),
  validityDays: z.number().int().min(1),
  conditions: z.array(
    z.object({
      conditionType: z.enum(['PRE_DISBURSEMENT', 'POST_DISBURSEMENT']),
      description: z.string().min(1, 'Condition is required'),
      isMandatory: z.boolean(),
    }),
  ),
  securities: z.array(
    z.object({
      securityCategory: z.enum(['PRIMARY', 'COLLATERAL']),
      securityType: z.string().min(1, 'Security type is required'),
      description: z.string().min(1, 'Description is required'),
      acceptableValue: z.number().min(0),
      marginPercentage: z.number().min(0).max(100),
    }),
  ),
  covenants: z.array(
    z.object({
      covenantType: z.enum(['FINANCIAL', 'REPORTING', 'OPERATIONAL', 'NEGATIVE']),
      description: z.string().min(1, 'Description is required'),
      frequency: z.enum(['MONTHLY', 'QUARTERLY', 'YEARLY', 'ONE_TIME']),
      threshold: z.string().optional(),
    }),
  ),
  remarks: z.string().optional(),
});

export type SanctionFormData = z.infer<typeof sanctionSchema>;
