import { Loader2, Plus, Save, Trash2 } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
import { Textarea } from '@/components/ui/textarea';
import { logger } from "@/lib/logger";
import {
  vouchersApi,
  voucherTypesApi,
  financialYearsApi,
  accountsApi,
  organizationsApi,
  unitsApi,
} from '@/services/api';
import type {
  Voucher,
  VoucherCreate,
  VoucherLineCreate,
  VoucherType,
  FinancialYear,
  Account,
  Organization,
  Unit,
  PaginatedResponse,
} from '@/types';

interface VoucherLineRow extends VoucherLineCreate {
  account_code?: string;
  account_name?: string;
}

export function VoucherForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [voucherTypes, setVoucherTypes] = useState<VoucherType[]>([]);
  const [financialYears, setFinancialYears] = useState<FinancialYear[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);

  const [selectedOrg, setSelectedOrg] = useState<string>('');
  const [voucherTypeId, setVoucherTypeId] = useState<string>('');
  const [financialYearId, setFinancialYearId] = useState<string>('');
  const [unitId, setUnitId] = useState<string>('all');
  const [voucherDate, setVoucherDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [referenceNumber, setReferenceNumber] = useState<string>('');
  const [referenceDate, setReferenceDate] = useState<string>('');
  const [narration, setNarration] = useState<string>('');

  const [lines, setLines] = useState<VoucherLineRow[]>([
    { account_id: '', debit_amount: 0, credit_amount: 0, narration: '' },
    { account_id: '', debit_amount: 0, credit_amount: 0, narration: '' },
  ]);

  const [totalDebit, setTotalDebit] = useState(0);
  const [totalCredit, setTotalCredit] = useState(0);
  const [isBalanced, setIsBalanced] = useState(true);

  useEffect(() => {
    const debit = lines.reduce((sum, line) => sum + (line.debit_amount || 0), 0);
    const credit = lines.reduce((sum, line) => sum + (line.credit_amount || 0), 0);
    setTotalDebit(debit);
    setTotalCredit(credit);
    setIsBalanced(Math.abs(debit - credit) < 0.01);
  }, [lines]);

  const fetchOrganizations = useCallback(async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      const data: PaginatedResponse<Organization> = response.data;
      setOrganizations(data.items);
      if (data.items.length > 0 && !isEdit) {
        setSelectedOrg(data.items[0].id);
      }
    } catch (error) {
      logger.error('Failed to fetch organizations:', error);
    }
  }, [isEdit]);

  const fetchUnits = useCallback(async () => {
    if (!selectedOrg) return;
    try {
      const response = await unitsApi.list({ organization_id: selectedOrg, page_size: 100 });
      const data: PaginatedResponse<Unit> = response.data;
      setUnits(data.items);
    } catch (error) {
      logger.error('Failed to fetch units:', error);
    }
  }, [selectedOrg]);

  const fetchVoucherTypes = useCallback(async () => {
    if (!selectedOrg) return;
    try {
      const response = await voucherTypesApi.list({ organization_id: selectedOrg, page_size: 100 });
      const data: PaginatedResponse<VoucherType> = response.data;
      setVoucherTypes(data.items);
    } catch (error) {
      logger.error('Failed to fetch voucher types:', error);
    }
  }, [selectedOrg]);

  const fetchFinancialYears = useCallback(async () => {
    if (!selectedOrg) return;
    try {
      const response = await financialYearsApi.list({
        organization_id: selectedOrg,
        page_size: 100,
      });
      const data: PaginatedResponse<FinancialYear> = response.data;
      setFinancialYears(data.items);
      // Set current financial year as default
      const currentFY = data.items.find((fy) => fy.is_current);
      if (currentFY && !isEdit) {
        setFinancialYearId(currentFY.id);
      }
    } catch (error) {
      logger.error('Failed to fetch financial years:', error);
    }
  }, [isEdit, selectedOrg]);

  const fetchAccounts = useCallback(async () => {
    if (!selectedOrg) return;
    try {
      // Fetch all accounts by paginating (backend limits to 100 per page)
      let allAccounts: Account[] = [];
      let page = 1;
      let hasMore = true;

      while (hasMore) {
        const response = await accountsApi.list({
          organization_id: selectedOrg,
          page,
          page_size: 100,
        });
        const data: PaginatedResponse<Account> = response.data;
        allAccounts = [...allAccounts, ...data.items];
        hasMore = page < data.total_pages;
        page++;
      }

      setAccounts(allAccounts);
    } catch (error) {
      logger.error('Failed to fetch accounts:', error);
    }
  }, [selectedOrg]);

  const fetchVoucher = useCallback(async (voucherId: string) => {
    try {
      setLoading(true);
      const response = await vouchersApi.get(voucherId);
      const voucher: Voucher = response.data;

      setSelectedOrg(voucher.organization_id);
      setVoucherTypeId(voucher.voucher_type_id);
      setFinancialYearId(voucher.financial_year_id);
      setUnitId(voucher.unit_id || '');
      setVoucherDate(voucher.voucher_date);
      setReferenceNumber(voucher.reference_number || '');
      setReferenceDate(voucher.reference_date || '');
      setNarration(voucher.narration || '');

      if (voucher.lines && voucher.lines.length > 0) {
        setLines(
          voucher.lines.map((line) => ({
            account_id: line.account_id,
            account_code: line.account_code,
            account_name: line.account_name,
            debit_amount: line.debit_amount,
            credit_amount: line.credit_amount,
            narration: line.narration || '',
            cost_center_id: line.cost_center_id,
            party_type: line.party_type,
            party_id: line.party_id,
            reference_type: line.reference_type,
            reference_id: line.reference_id,
            reference_number: line.reference_number,
            cheque_number: line.cheque_number,
            cheque_date: line.cheque_date,
          })),
        );
      }
    } catch (error) {
      logger.error('Failed to fetch voucher:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOrganizations();
  }, [fetchOrganizations]);

  useEffect(() => {
    if (isEdit && id) {
      fetchVoucher(id);
    }
  }, [fetchVoucher, id, isEdit]);

  useEffect(() => {
    if (selectedOrg) {
      fetchVoucherTypes();
      fetchFinancialYears();
      fetchAccounts();
      fetchUnits();
    }
  }, [fetchAccounts, fetchFinancialYears, fetchUnits, fetchVoucherTypes, selectedOrg]);

  const handleAddLine = () => {
    setLines([...lines, { account_id: '', debit_amount: 0, credit_amount: 0, narration: '' }]);
  };

  const handleRemoveLine = (index: number) => {
    if (lines.length <= 2) return;
    setLines(lines.filter((_, i) => i !== index));
  };

  const handleLineChange = (index: number, field: keyof VoucherLineRow, value: string | number) => {
    const newLines = [...lines];
    newLines[index] = { ...newLines[index], [field]: value };

    // Update account info when account is selected
    if (field === 'account_id') {
      const account = accounts.find((a) => a.id === value);
      if (account) {
        newLines[index].account_code = account.code;
        newLines[index].account_name = account.name;
      }
    }

    // Clear opposite amount when one is entered
    if (field === 'debit_amount' && Number(value) > 0) {
      newLines[index].credit_amount = 0;
    } else if (field === 'credit_amount' && Number(value) > 0) {
      newLines[index].debit_amount = 0;
    }

    setLines(newLines);
  };

  const onSubmit = async () => {
    if (!isBalanced) {
      alert('Voucher is not balanced. Total debit must equal total credit.');
      return;
    }

    if (
      lines.filter((l) => l.account_id && (l.debit_amount > 0 || l.credit_amount > 0)).length < 2
    ) {
      alert('Please enter at least two valid lines.');
      return;
    }

    try {
      setSubmitting(true);

      const voucherData: VoucherCreate = {
        voucher_type_id: voucherTypeId,
        voucher_date: voucherDate,
        financial_year_id: financialYearId,
        reference_number: referenceNumber || undefined,
        reference_date: referenceDate || undefined,
        narration: narration || undefined,
        organization_id: selectedOrg,
        unit_id: unitId && unitId !== 'all' ? unitId : undefined,
        lines: lines
          .filter((l) => l.account_id && (l.debit_amount > 0 || l.credit_amount > 0))
          .map((l) => ({
            account_id: l.account_id,
            debit_amount: l.debit_amount || 0,
            credit_amount: l.credit_amount || 0,
            narration: l.narration || undefined,
          })),
      };

      if (isEdit && id) {
        await vouchersApi.update(id, voucherData);
      } else {
        await vouchersApi.create(voucherData);
      }

      navigate('/admin/finance/vouchers');
    } catch (error) {
      logger.error('Failed to save voucher:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount);
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
        title={isEdit ? 'Edit Voucher' : 'New Voucher'}
        subtitle={isEdit ? 'Update voucher details' : 'Create a new accounting voucher'}
        breadcrumbs={[
          { label: 'Vouchers', to: '/admin/finance/vouchers' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Voucher Header</CardTitle>
            <CardDescription>Basic voucher information</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label>Organization *</Label>
                <Select value={selectedOrg} onValueChange={setSelectedOrg} disabled={isEdit}>
                  <SelectTrigger>
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
              <div className="space-y-2">
                <Label>Voucher Type *</Label>
                <Select
                  value={voucherTypeId}
                  onValueChange={setVoucherTypeId}
                  disabled={!selectedOrg || isEdit}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select voucher type" />
                  </SelectTrigger>
                  <SelectContent>
                    {voucherTypes.map((vt) => (
                      <SelectItem key={vt.id} value={vt.id}>
                        {vt.code} - {vt.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Financial Year *</Label>
                <Select
                  value={financialYearId}
                  onValueChange={setFinancialYearId}
                  disabled={!selectedOrg}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select financial year" />
                  </SelectTrigger>
                  <SelectContent>
                    {financialYears.map((fy) => (
                      <SelectItem key={fy.id} value={fy.id}>
                        {fy.code} {fy.is_current && '(Current)'}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-4">
              <div className="space-y-2">
                <Label>Voucher Date *</Label>
                <Input
                  type="date"
                  value={voucherDate}
                  onChange={(e) => setVoucherDate(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Unit</Label>
                <Select value={unitId} onValueChange={setUnitId} disabled={!selectedOrg}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select unit" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Units</SelectItem>
                    {units.map((unit) => (
                      <SelectItem key={unit.id} value={unit.id}>
                        {unit.code} - {unit.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Reference Number</Label>
                <Input
                  value={referenceNumber}
                  onChange={(e) => setReferenceNumber(e.target.value)}
                  placeholder="Optional"
                />
              </div>
              <div className="space-y-2">
                <Label>Reference Date</Label>
                <Input
                  type="date"
                  value={referenceDate}
                  onChange={(e) => setReferenceDate(e.target.value)}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Narration</Label>
              <Textarea
                value={narration}
                onChange={(e) => setNarration(e.target.value)}
                placeholder="Enter voucher narration..."
                rows={2}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Voucher Lines</CardTitle>
                <CardDescription>Enter debit and credit entries</CardDescription>
              </div>
              <Button type="button" variant="outline" size="sm" onClick={handleAddLine}>
                <Plus className="mr-2 h-4 w-4" />
                Add Line
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[300px]">Account</TableHead>
                  <TableHead className="w-[150px] text-right">Debit</TableHead>
                  <TableHead className="w-[150px] text-right">Credit</TableHead>
                  <TableHead>Narration</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {lines.map((line, index) => (
                  <TableRow key={index}>
                    <TableCell>
                      <Select
                        value={line.account_id || undefined}
                        onValueChange={(value) => handleLineChange(index, 'account_id', value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select account" />
                        </SelectTrigger>
                        <SelectContent>
                          {accounts.length === 0 ? (
                            <div className="px-2 py-4 text-center text-sm text-slate-500">
                              No accounts found
                            </div>
                          ) : (
                            accounts.map((account) => (
                              <SelectItem key={account.id} value={account.id}>
                                {account.code} - {account.name}
                              </SelectItem>
                            ))
                          )}
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        step="0.01"
                        min="0"
                        className="text-right"
                        value={line.debit_amount || ''}
                        onChange={(e) =>
                          handleLineChange(index, 'debit_amount', parseFloat(e.target.value) || 0)
                        }
                        placeholder="0.00"
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        step="0.01"
                        min="0"
                        className="text-right"
                        value={line.credit_amount || ''}
                        onChange={(e) =>
                          handleLineChange(index, 'credit_amount', parseFloat(e.target.value) || 0)
                        }
                        placeholder="0.00"
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        value={line.narration || ''}
                        onChange={(e) => handleLineChange(index, 'narration', e.target.value)}
                        placeholder="Line narration"
                      />
                    </TableCell>
                    <TableCell>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => handleRemoveLine(index)}
                        disabled={lines.length <= 2}
                      >
                        <Trash2 className="h-4 w-4 text-slate-400" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                <TableRow className="bg-slate-50 font-medium">
                  <TableCell className="text-right">Total</TableCell>
                  <TableCell className="text-right">{formatAmount(totalDebit)}</TableCell>
                  <TableCell className="text-right">{formatAmount(totalCredit)}</TableCell>
                  <TableCell colSpan={2}>
                    {isBalanced ? (
                      <Badge className="bg-emerald-50 text-emerald-700">Balanced</Badge>
                    ) : (
                      <Badge className="bg-red-50 text-red-700">
                        Difference: {formatAmount(Math.abs(totalDebit - totalCredit))}
                      </Badge>
                    )}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <div className="flex items-center justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/admin/finance/vouchers')}
          >
            Cancel
          </Button>
          <Button onClick={onSubmit} disabled={submitting || !isBalanced}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Save className="mr-2 h-4 w-4" />
            {isEdit ? 'Update Voucher' : 'Create Voucher'}
          </Button>
        </div>
      </div>
    </div>
  );
}
