/**
 * useApplication — detail query for /lending/applications/{id}.
 *
 * Wire format is camelCase per Pydantic CamelSchema. Monetary fields are
 * JSON strings (Pydantic Decimal — CLAUDE.md §6.2).
 */

import { useQuery } from '@tanstack/react-query';

import api from '@/services/api';

export interface ApplicationView {
  id: string;
  applicationNumber: string;
  stage: string;
  status: string;
  priority: string;
  requestedAmount: string;
  requestedTenureMonths: number;
  purpose: string | null;
  projectName: string | null;
  projectCost: string | null;
  promoterContribution: string | null;
  entityId: string;
  entityName: string | null;
  entityLegalName: string | null;
  entityCode: string | null;
  entityPan: string | null;
  entityType: string | null;
  productId: string;
  productName: string | null;
  productCode: string | null;
  productCategory: string | null;
  relationshipManagerId: string | null;
  creditOfficerId: string | null;
  submittedAt: string | null;
  createdAt: string;
  updatedAt: string | null;
}

export function useApplication(id: string | undefined) {
  return useQuery<ApplicationView>({
    queryKey: ['lending', 'applications', id] as const,
    queryFn: async () => {
      const { data } = await api.get<ApplicationView>(`/lending/applications/${id}`);
      return data;
    },
    enabled: !!id,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
