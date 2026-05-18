/**
 * useSanction — detail query for /lending/sanctions/{id}.
 *
 * The detail endpoint emits camelCase via Pydantic CamelSchema on the BE.
 */

import { useQuery } from '@tanstack/react-query';

import api from '@/services/api';
import type { LoanSanction } from '@/types/lending';

export function useSanction(id: string | undefined) {
  return useQuery<LoanSanction>({
    queryKey: ['lending', 'sanctions', id] as const,
    queryFn: async () => {
      const { data } = await api.get<LoanSanction>(`/lending/sanctions/${id}`);
      return data;
    },
    enabled: !!id,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
