import { Building2, CreditCard, Loader2, MoreHorizontal, Plus, Star } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { organizationsApi } from '@/services/api';
import type { Organization, OrganizationBankAccount } from '@/types';

import { logger } from "@/lib/logger";
const ACCOUNT_TYPE_LABELS: Record<string, string> = {
  CURRENT: 'Current Account',
  SAVINGS: 'Savings Account',
  OD: 'Overdraft',
  CC: 'Cash Credit',
  FIXED_DEPOSIT: 'Fixed Deposit',
};

export function OrganizationBankAccountList() {
  const { orgId } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [bankAccounts, setBankAccounts] = useState<OrganizationBankAccount[]>([]);

  useEffect(() => {
    if (orgId) {
      fetchData();
    }
  }, [orgId]);

  const fetchData = async () => {
    if (!orgId) return;
    try {
      setLoading(true);
      const [orgRes, bankRes] = await Promise.all([
        organizationsApi.get(orgId),
        organizationsApi.listBankAccounts(orgId),
      ]);
      setOrganization(orgRes.data);
      setBankAccounts(bankRes.data);
    } catch (error) {
      logger.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSetPrimary = async (id: string) => {
    if (!orgId) return;
    try {
      await organizationsApi.setPrimaryBankAccount(orgId, id);
      fetchData();
    } catch (error) {
      logger.error('Failed to set primary:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (!orgId || !confirm('Are you sure you want to delete this bank account?')) return;
    try {
      await organizationsApi.deleteBankAccount(orgId, id);
      fetchData();
    } catch (error) {
      logger.error('Failed to delete:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Bank Accounts"
        subtitle={`Manage bank accounts for ${organization?.name}`}
        breadcrumbs={[
          { label: 'Organizations', to: '/admin/organizations' },
          { label: organization?.name ?? '...', to: `/admin/organizations/${orgId}` },
          { label: 'Bank Accounts' },
        ]}
        actions={
          <Button onClick={() => navigate(`/admin/organizations/${orgId}/bank-accounts/new`)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Bank Account
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            {organization?.name}
          </CardTitle>
          <CardDescription>
            {bankAccounts.length} bank account{bankAccounts.length !== 1 ? 's' : ''} configured
          </CardDescription>
        </CardHeader>
        <CardContent>
          {bankAccounts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <CreditCard className="h-12 w-12 text-slate-400" />
              <h3 className="mt-4 text-lg font-medium text-slate-900">No bank accounts</h3>
              <p className="mt-2 text-sm text-slate-500">
                Add bank accounts for payments and receipts.
              </p>
              <Button
                className="mt-4"
                onClick={() => navigate(`/admin/organizations/${orgId}/bank-accounts/new`)}
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Bank Account
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Account Name</TableHead>
                  <TableHead>Account Number</TableHead>
                  <TableHead>Bank</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {bankAccounts.map((account) => (
                  <TableRow key={account.id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{account.account_name}</span>
                        {account.is_primary && (
                          <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="font-mono">
                      {account.account_number.replace(/(.{4})/g, '$1 ').trim()}
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">{account.bank_name}</div>
                        {account.branch_name && (
                          <div className="text-sm text-slate-500">{account.branch_name}</div>
                        )}
                        <div className="text-xs text-slate-400">{account.ifsc_code}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {ACCOUNT_TYPE_LABELS[account.account_type] || account.account_type}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={account.status === 'ACTIVE' ? 'default' : 'secondary'}>
                        {account.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={() =>
                              navigate(
                                `/admin/organizations/${orgId}/bank-accounts/${account.id}/edit`,
                              )
                            }
                          >
                            Edit
                          </DropdownMenuItem>
                          {!account.is_primary && (
                            <DropdownMenuItem onClick={() => handleSetPrimary(account.id)}>
                              Set as Primary
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuItem
                            className="text-red-600"
                            onClick={() => handleDelete(account.id)}
                          >
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
