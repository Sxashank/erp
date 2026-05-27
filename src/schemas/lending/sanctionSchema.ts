import { z } from 'zod';

export const sanctionSchema = z.object({
  applicationId: z.string().min(1, 'Application is required'),
  sanctionedAmount: z.number().positive('Sanctioned amount is required'),
  interestType: z.string().min(1, 'Interest type is required'),
  spreadBps: z.number().min(0),
  effectiveRate: z.number().min(0).max(100),
  tenureMonths: z.number().int().min(1, 'Tenure is required'),
  moratoriumMonths: z.number().int().min(0),
  repaymentFrequency: z.string().min(1, 'Repayment frequency is required'),
  repaymentMode: z.string().min(1, 'Repayment mode is required'),
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
      securityCategory: z.string().min(1, 'Security nature is required'),
      securityType: z.string().min(1, 'Security type is required'),
      description: z.string().min(1, 'Description is required'),
      acceptableValue: z.number().min(0),
      marginPercentage: z.number().min(0).max(100),
    }),
  ),
  covenants: z.array(
    z.object({
      covenantType: z.string().min(1, 'Covenant type is required'),
      description: z.string().min(1, 'Description is required'),
      frequency: z.string().min(1, 'Frequency is required'),
      threshold: z.string().optional(),
    }),
  ),
  remarks: z.string().optional(),
});

export type SanctionFormData = z.infer<typeof sanctionSchema>;
