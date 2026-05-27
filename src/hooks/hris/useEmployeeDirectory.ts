import { useQuery } from '@tanstack/react-query';

import { hrisApi } from '@/services/api';
import { useActiveOrganizationId } from '@/stores/organizationStore';

export interface EmployeeDirectoryItem {
  id: string;
  employeeCode: string;
  fullName: string;
  departmentName?: string | null;
  designationName?: string | null;
  employmentStatus: string;
}

export function useEmployeeDirectory(params?: {
  search?: string;
  employmentStatus?: string;
  enabled?: boolean;
}) {
  const organizationId = useActiveOrganizationId();

  return useQuery({
    queryKey: ['hris', 'employee-directory', organizationId, params] as const,
    enabled: Boolean(organizationId) && (params?.enabled ?? true),
    queryFn: async (): Promise<EmployeeDirectoryItem[]> => {
      const response = await hrisApi.listEmployees({
        search: params?.search,
        employment_status: params?.employmentStatus,
        skip: 0,
        limit: 200,
      });
      const payload = response.data as
        | { items?: EmployeeDirectoryItem[] }
        | EmployeeDirectoryItem[];
      return Array.isArray(payload) ? payload : (payload.items ?? []);
    },
  });
}
