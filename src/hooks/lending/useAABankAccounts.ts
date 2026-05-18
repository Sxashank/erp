/**
 * useAABankAccounts / useAAAccountTransactions — read-only queries for
 * /lending/aa/bank-accounts/* endpoints. See CLAUDE.md §3.3, §5.4.
 */

import { useQuery } from '@tanstack/react-query';

import {
  listAccountTransactions,
  listBankAccounts,
  type AccountTransactionFilters,
  type BankAccount,
  type BankAccountFilters,
  type BankTransaction,
} from '@/services/lending/aaApi';
import type { PaginatedResponse } from '@/types/lending';

export const aaBankAccountsQueryKey = (filters?: BankAccountFilters) =>
  ['lending', 'aa', 'bank-accounts', filters ?? {}] as const;

export function useAABankAccounts(filters?: BankAccountFilters) {
  return useQuery<PaginatedResponse<BankAccount>>({
    queryKey: aaBankAccountsQueryKey(filters),
    queryFn: () => listBankAccounts(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export const aaAccountTransactionsQueryKey = (
  accountId: string | undefined,
  filters?: AccountTransactionFilters,
) => ['lending', 'aa', 'bank-accounts', accountId ?? null, 'transactions', filters ?? {}] as const;

export function useAAAccountTransactions(
  accountId: string | undefined,
  filters?: AccountTransactionFilters,
) {
  return useQuery<PaginatedResponse<BankTransaction>>({
    queryKey: aaAccountTransactionsQueryKey(accountId, filters),
    queryFn: () => listAccountTransactions(accountId as string, filters),
    enabled: Boolean(accountId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
