import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  productApi,
  type ProductDocumentRequirement,
  type ProductDocumentRequirementCreate,
  type ProductDocumentRequirementUpdate,
} from '@/services/lending/productApi';

const baseKey = ['lending', 'products', 'document-requirements'] as const;
const keyFor = (productId: string | undefined) => [...baseKey, productId ?? ''] as const;

export function useProductDocumentRequirements(productId: string | undefined) {
  return useQuery<ProductDocumentRequirement[]>({
    queryKey: keyFor(productId),
    queryFn: () => productApi.listDocumentRequirements(productId as string),
    enabled: Boolean(productId),
    staleTime: 60_000,
  });
}

export function useAddProductDocumentRequirement(productId: string) {
  const queryClient = useQueryClient();
  return useMutation<ProductDocumentRequirement, unknown, ProductDocumentRequirementCreate>({
    mutationFn: (payload) => productApi.addDocumentRequirement(productId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: keyFor(productId) });
    },
  });
}

export function useUpdateProductDocumentRequirement(productId: string) {
  const queryClient = useQueryClient();
  return useMutation<
    ProductDocumentRequirement,
    unknown,
    { requirementId: string; payload: ProductDocumentRequirementUpdate }
  >({
    mutationFn: ({ requirementId, payload }) =>
      productApi.updateDocumentRequirement(requirementId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: keyFor(productId) });
    },
  });
}

export function useDeleteProductDocumentRequirement(productId: string) {
  const queryClient = useQueryClient();
  return useMutation<void, unknown, string>({
    mutationFn: (requirementId) => productApi.deleteDocumentRequirement(requirementId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: keyFor(productId) });
    },
  });
}
