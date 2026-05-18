/**
 * useActiveEntity — selector wrapper over `portalActiveEntityStore`.
 *
 * Pages should read the active entity through this hook so future
 * refactors of the storage layer stay local to `src/stores/`.
 */

import {
  usePortalActiveEntityStore,
  usePortalActiveEntityId,
  usePortalEntities,
  type PortalEntityOption,
} from '@/stores/portalActiveEntityStore';

export interface UseActiveEntityResult {
  entities: PortalEntityOption[];
  activeEntityId: string | null;
  activeEntity: PortalEntityOption | undefined;
  setActiveEntityId: (id: string | null) => void;
  setEntities: (entities: PortalEntityOption[]) => void;
}

export function useActiveEntity(): UseActiveEntityResult {
  const entities = usePortalEntities();
  const activeEntityId = usePortalActiveEntityId();
  const setActiveEntityId = usePortalActiveEntityStore((s) => s.setActiveEntityId);
  const setEntities = usePortalActiveEntityStore((s) => s.setEntities);
  const activeEntity = entities.find((e) => e.id === activeEntityId);

  return {
    entities,
    activeEntityId,
    activeEntity,
    setActiveEntityId,
    setEntities,
  };
}

export type { PortalEntityOption };
