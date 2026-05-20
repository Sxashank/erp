import { Calendar, Edit, Lock, MoreHorizontal, Plus, Star, Trash2 } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
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
import { financialYearsApi, organizationsApi } from '@/services/api';
import type { FinancialYear, Organization, PaginatedResponse } from '@/types';

import { logger } from "@/lib/logger";
export function FinancialYearList() {
  const navigate = useNavigate();
  const [financialYears, setFinancialYears] = useState<FinancialYear[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
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

  const fetchFinancialYears = useCallback(async (page = 1) => {
    if (!selectedOrgId) return;
    try {
      setLoading(true);
      const response = await financialYearsApi.list({
        page,
        pageSize: 10,
        includeInactive: true,
      });
      const data: PaginatedResponse<FinancialYear> = response.data;
      setFinancialYears(data.items);
      setPagination({ page: data.page, total: data.total, totalPages: data.total_pages });
    } catch (error) {
      logger.error('Failed to fetch financial years:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedOrgId]);

  useEffect(() => {
    fetchOrganizations();
  }, [fetchOrganizations]);

  useEffect(() => {
    if (selectedOrgId) {
      fetchFinancialYears();
    }
  }, [fetchFinancialYears, selectedOrgId]);

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this financial year?')) return;
    try {
      await financialYearsApi.delete(id);
      fetchFinancialYears(pagination.page);
    } catch (error) {
      logger.error('Failed to delete financial year:', error);
    }
  };

  const handleSetCurrent = async (id: string) => {
    try {
      await financialYearsApi.setCurrent(id);
      fetchFinancialYears(pagination.page);
    } catch (error) {
      logger.error('Failed to set current financial year:', error);
    }
  };

  const handleCloseYear = async (id: string) => {
    if (!confirm('Are you sure you want to close this financial year? This action cannot be undone.')) return;
    try {
      await financialYearsApi.closeYear(id);
      fetchFinancialYears(pagination.page);
    } catch (error) {
      logger.error('Failed to close financial year:', error);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Financial Years"
        subtitle="Manage financial years and periods"
        actions={
          <Button onClick={() => navigate('/admin/finance/financial-years/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Financial Year
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>All Financial Years</CardTitle>
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
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-sm text-slate-500">Loading...</p>
            </div>
          ) : financialYears.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <Calendar className="mb-4 h-12 w-12 text-slate-300" />
              <p className="text-sm text-slate-500">No financial years found</p>
              <Button variant="link" onClick={() => navigate('/admin/finance/financial-years/new')}>
                Create your first financial year
              </Button>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Code</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Start Date</TableHead>
                    <TableHead>End Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Current</TableHead>
                    <TableHead className="w-[70px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {financialYears.map((fy) => (
                    <TableRow key={fy.id}>
                      <TableCell className="font-medium">{fy.code}</TableCell>
                      <TableCell>{fy.name}</TableCell>
                      <TableCell><DateDisplay date={fy.start_date} /></TableCell>
                      <TableCell><DateDisplay date={fy.end_date} /></TableCell>
                      <TableCell>
                        <Badge
                          className={
                            fy.is_closed
                              ? 'bg-slate-100 text-slate-600 hover:bg-slate-100'
                              : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-50'
                          }
                        >
                          {fy.is_closed ? 'Closed' : 'Open'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {fy.is_current && (
                          <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-50">
                            <Star className="mr-1 h-3 w-3" />
                            Current
                          </Badge>
                        )}
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
                              onClick={() => navigate(`/admin/finance/financial-years/${fy.id}/edit`)}
                            >
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            {!fy.is_current && !fy.is_closed && (
                              <DropdownMenuItem onClick={() => handleSetCurrent(fy.id)}>
                                <Star className="mr-2 h-4 w-4" />
                                Set as Current
                              </DropdownMenuItem>
                            )}
                            {!fy.is_closed && (
                              <DropdownMenuItem onClick={() => handleCloseYear(fy.id)}>
                                <Lock className="mr-2 h-4 w-4" />
                                Close Year
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => handleDelete(fy.id)}
                              className="text-red-600"
                              disabled={fy.is_closed}
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
                    Showing {financialYears.length} of {pagination.total} financial years
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={pagination.page <= 1}
                      onClick={() => fetchFinancialYears(pagination.page - 1)}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={pagination.page >= pagination.totalPages}
                      onClick={() => fetchFinancialYears(pagination.page + 1)}
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
