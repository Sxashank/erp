import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Edit, FileText, MoreHorizontal, Plus, Trash2 } from 'lucide-react';

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
import { voucherTypesApi, organizationsApi } from '@/services/api';
import type { VoucherType, Organization, PaginatedResponse } from '@/types';
import { VOUCHER_CLASSES } from '@/types';

export function VoucherTypeList() {
  const navigate = useNavigate();
  const [voucherTypes, setVoucherTypes] = useState<VoucherType[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [selectedClass, setSelectedClass] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ page: 1, total: 0, totalPages: 0 });

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrgId) {
      fetchVoucherTypes();
    }
  }, [selectedOrgId, selectedClass]);

  const fetchOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      const data: PaginatedResponse<Organization> = response.data;
      setOrganizations(data.items);
      if (data.items.length > 0) {
        setSelectedOrgId(data.items[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
    }
  };

  const fetchVoucherTypes = async (page = 1) => {
    if (!selectedOrgId) return;
    try {
      setLoading(true);
      const params: any = {
        organization_id: selectedOrgId,
        page,
        page_size: 20,
        include_inactive: true,
      };
      if (selectedClass && selectedClass !== 'all') {
        params.voucher_class = selectedClass;
      }
      const response = await voucherTypesApi.list(params);
      const data: PaginatedResponse<VoucherType> = response.data;
      setVoucherTypes(data.items);
      setPagination({ page: data.page, total: data.total, totalPages: data.total_pages });
    } catch (error) {
      console.error('Failed to fetch voucher types:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this voucher type?')) return;
    try {
      await voucherTypesApi.delete(id);
      fetchVoucherTypes(pagination.page);
    } catch (error) {
      console.error('Failed to delete voucher type:', error);
    }
  };

  const getClassBadgeClass = (voucherClass: string) => {
    switch (voucherClass) {
      case 'JOURNAL':
        return 'bg-slate-100 text-slate-700';
      case 'PAYMENT':
        return 'bg-red-50 text-red-700';
      case 'RECEIPT':
        return 'bg-emerald-50 text-emerald-700';
      case 'CONTRA':
        return 'bg-blue-50 text-blue-700';
      case 'SALES':
        return 'bg-green-50 text-green-700';
      case 'PURCHASE':
        return 'bg-orange-50 text-orange-700';
      case 'DEBIT_NOTE':
        return 'bg-amber-50 text-amber-700';
      case 'CREDIT_NOTE':
        return 'bg-purple-50 text-purple-700';
      default:
        return 'bg-slate-100 text-slate-600';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Voucher Types</h1>
          <p className="text-sm text-slate-500">Manage voucher type configurations</p>
        </div>
        <Button onClick={() => navigate('/admin/finance/voucher-types/new')}>
          <Plus className="mr-2 h-4 w-4" />
          Add Voucher Type
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>All Voucher Types</CardTitle>
            <div className="flex items-center gap-4">
              <Select value={selectedClass} onValueChange={setSelectedClass}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="All Classes" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Classes</SelectItem>
                  {VOUCHER_CLASSES.map((vc) => (
                    <SelectItem key={vc.value} value={vc.value}>
                      {vc.label}
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
          ) : voucherTypes.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <FileText className="mb-4 h-12 w-12 text-slate-300" />
              <p className="text-sm text-slate-500">No voucher types found</p>
              <Button variant="link" onClick={() => navigate('/admin/finance/voucher-types/new')}>
                Create your first voucher type
              </Button>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Code</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Class</TableHead>
                    <TableHead>Prefix</TableHead>
                    <TableHead>Auto Number</TableHead>
                    <TableHead>Approval</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="w-[70px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {voucherTypes.map((vt) => (
                    <TableRow key={vt.id}>
                      <TableCell className="font-medium">{vt.code}</TableCell>
                      <TableCell>{vt.name}</TableCell>
                      <TableCell>
                        <Badge className={`${getClassBadgeClass(vt.voucher_class)} hover:${getClassBadgeClass(vt.voucher_class)}`}>
                          {vt.voucher_class.replace('_', ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell>{vt.prefix || '-'}</TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={vt.auto_numbering ? 'border-green-200 text-green-700' : ''}
                        >
                          {vt.auto_numbering ? 'Yes' : 'No'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {vt.requires_approval ? (
                          <Badge className="bg-amber-50 text-amber-700 hover:bg-amber-50">
                            {vt.approval_levels} Level{vt.approval_levels > 1 ? 's' : ''}
                          </Badge>
                        ) : (
                          <Badge variant="outline">Not Required</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge
                          className={
                            vt.is_active
                              ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-50'
                              : 'bg-slate-100 text-slate-600 hover:bg-slate-100'
                          }
                        >
                          {vt.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {vt.is_system ? (
                          <Badge variant="outline">System</Badge>
                        ) : (
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem
                                onClick={() => navigate(`/admin/finance/voucher-types/${vt.id}/edit`)}
                              >
                                <Edit className="mr-2 h-4 w-4" />
                                Edit
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() => handleDelete(vt.id)}
                                className="text-red-600"
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {pagination.totalPages > 1 && (
                <div className="mt-4 flex items-center justify-between">
                  <p className="text-sm text-slate-500">
                    Showing {voucherTypes.length} of {pagination.total} voucher types
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={pagination.page <= 1}
                      onClick={() => fetchVoucherTypes(pagination.page - 1)}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={pagination.page >= pagination.totalPages}
                      onClick={() => fetchVoucherTypes(pagination.page + 1)}
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
