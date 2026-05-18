import { useMutation, useQueryClient } from '@tanstack/react-query';

import {
  createSanction,
  updateSanction,
  type SanctionCreatePayload,
  type SanctionUpdatePayload,
} from '@/services/lending/sanctionApi';

export function useCreateSanction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: SanctionCreatePayload) => {
      const { applicationId, ...data } = payload;
      return createSanction(applicationId, data);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['lending', 'sanctions'] });
    },
  });
}

export function useUpdateSanction(sanctionId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: SanctionUpdatePayload) => {
      if (!sanctionId) {
        throw new Error('Sanction ID is required');
      }
      return updateSanction(sanctionId, payload);
    },
    onSuccess: (sanction) => {
      void queryClient.invalidateQueries({ queryKey: ['lending', 'sanctions'] });
      void queryClient.invalidateQueries({ queryKey: ['lending', 'sanctions', sanction.id] });
    },
  });
}
