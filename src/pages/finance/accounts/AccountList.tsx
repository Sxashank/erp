import { BookOpen, Edit, FileText, MoreHorizontal, Plus, Trash2 } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { accountsApi, organizationsApi } from '@/services/api';
import type { Account, Organization, PaginatedResponse } from '@/types';
import { ACCOUNT_TYPES } from '@/types';

import { logger } from '@/lib/logger';
export function AccountList() {
  const navigate = useNavigate();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ page: 1, total: 0, totalPages: 0 });

  const fetchOrganizations = useCallback(async () => {
    try {
      const response = await organizationsApi.list({ pageSize: 100 });
      const data: PaginatedResponse<Organization> = response.data;
      setOrganizations(data.items);
      if (data.items.length > 0) {
        setSelectedOrgId(data.items[0].id);
      }
    } catch (error) {
      logger.error('Failed to fetch organizations:', error);
    }
  }, []);

  const fetchAccounts = useCallback(
    async (page = 1) => {
      if (!selectedOrgId) return;
      try {
        setLoading(true);
        const params: Parameters<typeof accountsApi.list>[0] = {
          page,
          pageSize: 20,
          includeInactive: true,
        };
        if (selectedType && selectedType !== 'all') {
          params.accountType = selectedType;
        }
        const response = await accountsApi.list(params);
        const data: PaginatedResponse<Account> = response.data;
        setAccounts(data.items);
        setPagination({ page: data.page, total: data.total, totalPages: data.total_pages });
      } catch (error) {
        logger.error('Failed to fetch accounts:', error);
      } finally {
        setLoading(false);
      }
    },
    [selectedOrgId, selectedType],
  );

  useEffect(() => {
    fetchOrganizations();
  }, [fetchOrganizations]);

  useEffect(() => {
    if (selectedOrgId) {
      fetchAccounts();
    }
  }, [fetchAccounts, selectedOrgId, selectedType]);

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this account?')) return;
    try {
      await accountsApi.delete(id);
      fetchAccounts(pagination.page);
    } catch (error) {
      logger.error('Failed to delete account:', error);
    }
  };

  const getTypeBadgeClass = (type: string) => {
    switch (type) {
      case 'LEDGER':
        return 'bg-slate-100 text-slate-700';
      case 'CONTROL':
        return 'bg-purple-50 text-purple-700';
      case 'BANK':
        return 'bg-blue-50 text-blue-700';
      case 'CASH':
        return 'bg-emerald-50 text-emerald-700';
      default:
        return 'bg-slate-100 text-slate-600';
    }
  };

  const formatAmount = (amount: number, type: string) => {
    const formatted = formatIndianCompactCurrency(Math.abs(amount));
    return `${formatted} ${type}`;
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Accounts"
        subtitle="Manage ledger accounts"
        actions={
          <Button onClick={() => navigate('/admin/finance/accounts/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Account
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>All Accounts</CardTitle>
            <div className="flex items-center gap-4">
              <Select value={selectedType} onValueChange={setSelectedType}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="All Types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  {ACCOUNT_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
                <SelectTrigger className="w-[250px]">
                  <SelectValue placeholder="Select organization" />
                </SelectTrigger>
                <SelectContent>
                  {organizations.map((org) => (
                    <SelectItem key={org.id} value={org.id}>
                      {org.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-sm text-slate-500">Loading...</p>
            </div>
          ) : accounts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <BookOpen className="mb-4 h-12 w-12 text-slate-300" />
              <p className="text-sm text-slate-500">No accounts found</p>
              <Button variant="link" onClick={() => navigate('/admin/finance/accounts/new')}>
                Create your first account
              </Button>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Code</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Group</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Opening Balance</TableHead>
                    <TableHead>Current Balance</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="w-[70px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {accounts.map((account) => (
                    <TableRow key={account.id}>
                      <TableCell className="font-medium">{account.code}</TableCell>
                      <TableCell>{account.name}</TableCell>
                      <TableCell>{account.account_group_name || '-'}</TableCell>
                      <TableCell>
                        <Badge
                          className={`${getTypeBadgeClass(account.account_type)} hover:${getTypeBadgeClass(account.account_type)}`}
                        >
                          {account.account_type}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {formatAmount(account.opening_balance, account.opening_balance_type)}
                      </TableCell>
                      <TableCell>
                        {formatAmount(account.current_balance, account.current_balance_type)}
                      </TableCell>
                      <TableCell>
                        <Badge
                          className={
                            account.is_active
                              ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-50'
                              : 'bg-slate-100 text-slate-600 hover:bg-slate-100'
                          }
                        >
                          {account.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              onClick={() =>
                                navigate(`/admin/reports/account-ledger?accountId=${account.id}`)
                              }
                            >
                              <FileText className="mr-2 h-4 w-4" />
                              View Ledger
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => navigate(`/admin/finance/accounts/${account.id}/edit`)}
                            >
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleDelete(account.id)}
                              className="text-red-600"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {pagination.totalPages > 1 && (
                <div className="mt-4 flex items-center justify-between">
                  <p className="text-sm text-slate-500">
                    Showing {accounts.length} of {pagination.total} accounts
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={pagination.page <= 1}
                      onClick={() => fetchAccounts(pagination.page - 1)}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={pagination.page >= pagination.totalPages}
                      onClick={() => fetchAccounts(pagination.page + 1)}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
