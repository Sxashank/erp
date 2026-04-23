import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Edit, MoreHorizontal, Percent, Plus, Trash2 } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/common/PageHeader';
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
import { gstRatesApi } from '@/services/api';

interface GSTRate {
  id: string;
  code: string;
  name: string;
  rate: number;
  cgst_rate: number;
  sgst_rate: number;
  igst_rate: number;
  cess_rate: number;
  description?: string;
  effective_from: string;
  effective_to?: string;
  is_active: boolean;
}

interface PaginatedResponse {
  items: GSTRate[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export function GSTRateList() {
  const navigate = useNavigate();
  const [rates, setRates] = useState<GSTRate[]>([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ page: 1, total: 0, totalPages: 0 });

  useEffect(() => {
    fetchRates();
  }, []);

  const fetchRates = async (page = 1) => {
    try {
      setLoading(true);
      const response = await gstRatesApi.list({ page, page_size: 20, include_inactive: true });
      const data: PaginatedResponse = response.data;
      setRates(data.items);
      setPagination({ page: data.page, total: data.total, totalPages: data.total_pages });
    } catch (error) {
      console.error('Failed to fetch GST rates:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this GST rate?')) return;
    try {
      await gstRatesApi.delete(id);
      fetchRates(pagination.page);
    } catch (error) {
      console.error('Failed to delete GST rate:', error);
    }
  };

  const formatPercent = (value: number) => `${value}%`;

  return (
    <div className="space-y-6">
      <PageHeader
        title="GST Rates"
        subtitle="Manage GST rate configurations"
        actions={
          <Button onClick={() => navigate('/admin/gst/rates/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add GST Rate
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>All GST Rates</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-sm text-slate-500">Loading...</p>
            </div>
          ) : rates.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <Percent className="mb-4 h-12 w-12 text-slate-300" />
              <p className="text-sm text-slate-500">No GST rates found</p>
              <Button variant="link" onClick={() => navigate('/admin/gst/rates/new')}>
                Create your first GST rate
              </Button>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Code</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead className="text-right">Total Rate</TableHead>
                    <TableHead className="text-right">CGST</TableHead>
                    <TableHead className="text-right">SGST</TableHead>
                    <TableHead className="text-right">IGST</TableHead>
                    <TableHead className="text-right">Cess</TableHead>
                    <TableHead>Effective From</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="w-[70px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rates.map((rate) => (
                    <TableRow key={rate.id}>
                      <TableCell className="font-medium">{rate.code}</TableCell>
                      <TableCell>{rate.name}</TableCell>
                      <TableCell className="text-right font-semibold text-blue-600">
                        {formatPercent(rate.rate)}
                      </TableCell>
                      <TableCell className="text-right">{formatPercent(rate.cgst_rate)}</TableCell>
                      <TableCell className="text-right">{formatPercent(rate.sgst_rate)}</TableCell>
                      <TableCell className="text-right">{formatPercent(rate.igst_rate)}</TableCell>
                      <TableCell className="text-right">
                        {rate.cess_rate > 0 ? formatPercent(rate.cess_rate) : '-'}
                      </TableCell>
                      <TableCell>
                        {new Date(rate.effective_from).toLocaleDateString('en-IN')}
                      </TableCell>
                      <TableCell>
                        <Badge
                          className={
                            rate.is_active
                              ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-50'
                              : 'bg-slate-100 text-slate-600 hover:bg-slate-100'
                          }
                        >
                          {rate.is_active ? 'Active' : 'Inactive'}
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
                              onClick={() => navigate(`/admin/gst/rates/${rate.id}/edit`)}
                            >
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleDelete(rate.id)}
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
                    Showing {rates.length} of {pagination.total} rates
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={pagination.page <= 1}
                      onClick={() => fetchRates(pagination.page - 1)}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={pagination.page >= pagination.totalPages}
                      onClick={() => fetchRates(pagination.page + 1)}
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
