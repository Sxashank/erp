import { z } from 'zod';

export const depreciationRunSchema = z.object({
  depreciationPeriod: z
    .string()
    .regex(/^\d{4}-\d{2}$/, 'Period must be in YYYY-MM format'),
  depreciationBook: z.enum(['COMPANIES_ACT', 'IT_ACT']),
  remarks: z.string().trim().max(500).optional().or(z.literal('')),
});

export type DepreciationRunInput = z.infer<typeof depreciationRunSchema>;
