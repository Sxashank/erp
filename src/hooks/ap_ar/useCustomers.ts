/**
 * Customers hook. See CLAUDE.md §5.4.
 */

import { useQuery } from '@tanstack/react-query';

import { customersApi } from '@/services/api';
import { useActiveOrganizationId } from '@/stores/organizationStore';

export interface Customer {
  id: string;
  customer_code: string;
  customer_name: string;
  customer_type?: string;
  email?: string;
  phone?: string;
  gstin?: string;
  pan?: string;
  is_active: boolean;
}

export function useCustomers(params?: { search?: string; enabled?: boolean }) {
  const organizationId = useActiveOrganizationId();
  return useQuery({
    queryKey: ['customers', organizationId, params?.search],
    enabled: !!organizationId && (params?.enabled ?? true),
    queryFn: async (): Promise<Customer[]> => {
      const res = await customersApi.list({
        organization_id: organizationId!,
        search: params?.search?.trim() || undefined,
        page_size: 100,
      });
      const data = res.data as Customer[] | { items: Customer[] };
      return Array.isArray(data) ? data : data.items;
    },
  });
}

export function useCustomer(id: string | null | undefined) {
  return useQuery({
    queryKey: ['customer', id],
    enabled: !!id,
    queryFn: async (): Promise<Customer> => {
      const res = await customersApi.get(id!);
      return res.data as Customer;
    },
  });
}
