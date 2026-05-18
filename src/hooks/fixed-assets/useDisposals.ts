import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  getDisposal,
  listDisposals,
  takeApprovalAction,
  type ApprovalActionPayload,
  type ApprovalRequestResponse,
} from '@/services/fixed-assets';
import type { DisposalRegisterItem, OffsetPaginatedResponse } from '@/types/fixed-assets';

export const disposalsQueryKey = (
  organizationId: string,
  params?: { status?: string; disposalType?: string; search?: string; skip?: number; limit?: number },
) => ['fixed-assets', 'disposals', organizationId, params ?? {}] as const;

export const disposalDetailQueryKey = (assetId: string) =>
  ['fixed-assets', 'disposal', assetId] as const;

export function useDisposals(
  organizationId: string,
  params?: { status?: string; disposalType?: string; search?: string; skip?: number; limit?: number },
) {
  return useQuery<OffsetPaginatedResponse<DisposalRegisterItem>>({
    queryKey: disposalsQueryKey(organizationId, params),
    queryFn: () => listDisposals(organizationId, params),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useDisposal(assetId: string | undefined) {
  return useQuery<DisposalRegisterItem>({
    queryKey: disposalDetailQueryKey(assetId ?? 'missing'),
    queryFn: () => getDisposal(assetId!),
    enabled: Boolean(assetId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useTakeDisposalApprovalAction(organizationId: string, assetId?: string) {
  const queryClient = useQueryClient();
  return useMutation<ApprovalRequestResponse, unknown, { requestId: string; payload: ApprovalActionPayload }>({
    mutationFn: ({ requestId, payload }) => takeApprovalAction(requestId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fixed-assets', 'disposals', organizationId] });
      if (assetId) {
        queryClient.invalidateQueries({ queryKey: disposalDetailQueryKey(assetId) });
      }
    },
  });
}
