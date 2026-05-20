/**
 * Finance hooks — accounts, account groups, financial years, cost centers.
 * Every page that needs these data reads them through these hooks. No page
 * should call `accountsApi` directly. See CLAUDE.md §5.4.
 */

import { useQuery } from '@tanstack/react-query';

import { accountGroupsApi, accountsApi, financialYearsApi } from '@/services/api';
import { useActiveOrganizationId } from '@/stores/organizationStore';

export interface Account {
  id: string;
  code: string;
  name: string;
  accountType: string;
  nature?: string;
  is_active: boolean;
}

export interface FinancialYear {
  id: string;
  code: string;
  name: string;
  start_date: string;
  end_date: string;
  status: string;
  periods?: Period[];
}

export interface Period {
  id: string;
  code: string;
  name: string;
  start_date: string;
  end_date: string;
  status: 'OPEN' | 'SOFT_CLOSED' | 'HARD_CLOSED' | string;
}

export interface AccountGroup {
  id: string;
  code: string;
  name: string;
  nature: string;
}

export function useAccounts(params?: {
  accountType?: string;
  accountGroupId?: string;
  enabled?: boolean;
}) {
  const organizationId = useActiveOrganizationId();
  return useQuery({
    queryKey: ['accounts', organizationId, params?.accountType, params?.accountGroupId],
    enabled: !!organizationId && (params?.enabled ?? true),
    queryFn: async (): Promise<Account[]> => {
      const res = await accountsApi.list({
        accountType: params?.accountType,
        accountGroupId: params?.accountGroupId,
        pageSize: 100,
      });
      const data = res.data as Account[] | { items: Account[] };
      return Array.isArray(data) ? data : data.items;
    },
  });
}

export function useAccountGroups() {
  const organizationId = useActiveOrganizationId();
  return useQuery({
    queryKey: ['account-groups', organizationId],
    enabled: !!organizationId,
    queryFn: async (): Promise<AccountGroup[]> => {
      const res = await accountGroupsApi.list({
        pageSize: 100,
      });
      const data = res.data as AccountGroup[] | { items: AccountGroup[] };
      return Array.isArray(data) ? data : data.items;
    },
  });
}

export function useFinancialYears() {
  const organizationId = useActiveOrganizationId();
  return useQuery({
    queryKey: ['financial-years', organizationId],
    enabled: !!organizationId,
    queryFn: async (): Promise<FinancialYear[]> => {
      const res = await financialYearsApi.list({
        pageSize: 100,
      });
      const data = res.data as FinancialYear[] | { items: FinancialYear[] };
      return Array.isArray(data) ? data : data.items;
    },
  });
}

/**
 * Flattened Periods across all Financial Years the current org has. The
 * backend attaches `periods` on each FY; we flatten client-side.
 */
export function usePeriods() {
  const query = useFinancialYears();
  const periods: Period[] =
    query.data?.flatMap((fy) => fy.periods ?? []) ?? [];
  return { ...query, data: periods };
}
