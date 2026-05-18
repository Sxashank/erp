import { useQuery } from '@tanstack/react-query';

import {
  getCollectionCockpit,
  type CollectionCockpitFilters,
  type CollectionCockpitResponse,
} from '@/services/lending/collectionCockpitApi';

export const collectionCockpitQueryKeys = {
  all: ['lending', 'collection-cockpit'] as const,
  detail: (filters: CollectionCockpitFilters) =>
    [...collectionCockpitQueryKeys.all, filters] as const,
};

export function useCollectionCockpit(filters: CollectionCockpitFilters = {}) {
  return useQuery<CollectionCockpitResponse>({
    queryKey: collectionCockpitQueryKeys.detail(filters),
    queryFn: () => getCollectionCockpit(filters),
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });
}
