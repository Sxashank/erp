import { z } from 'zod';

export const fundDeploymentSchema = z.object({
  borrowingId: z.string().uuid('Select a borrowing facility'),
  loanAccountId: z.string().uuid('Select a loan account'),
  allocatedAmount: z.number().positive('Allocated amount must be greater than zero'),
  allocationDate: z.string().date('Select an allocation date'),
  remarks: z.string().trim().max(500, 'Remarks must be 500 characters or fewer').optional(),
});

export type FundDeploymentInput = z.infer<typeof fundDeploymentSchema>;
export type FundDeploymentFormInput = z.input<typeof fundDeploymentSchema>;
