import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Edit, MoreHorizontal, Plus, Trash2 } from 'lucide-react';

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
import { designationsApi } from '@/services/api';
import type { Designation, PaginatedResponse } from '@/types';

export function DesignationList() {
  const navigate = useNavigate();
  const [designations, setDesignations] = useState<Designation[]>([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ page: 1, total: 0, totalPages: 0 });

  const fetchDesignations = async (page = 1) => {
    try {
      setLoading(true);
      const response = await designationsApi.list({ page, page_size: 10, include_inactive: true });
      const data: PaginatedResponse<Designation> = response.data;
      setDesignations(data.items);
      setPagination({ page: data.page, total: data.total, totalPages: data.total_pages });
    } catch (error) {
      console.error('Failed to fetch designations:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDesignations();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this designation?')) return;
    try {
      await designationsApi.delete(id);
      fetchDesignations(pagination.page);
    } catch (error) {
      console.error('Failed to delete designation:', error);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Designations"
        subtitle="Manage job titles and positions"
        actions={
          <Button onClick={() => navigate('/admin/designations/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Designation
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>All Designations</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-sm text-slate-500">Loading...</p>
            </div>
          ) : designations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <p className="text-sm text-slate-500">No designations found</p>
              <Button variant="link" onClick={() => navigate('/admin/designations/new')}>
                Create your first designation
              </Button>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Code</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Department</TableHead>
                    <TableHead>Level</TableHead>
                    <TableHead>Reports To</TableHead>
                    <TableHead>Min Exp (Years)</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="w-[70px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {designations.map((designation) => (
                    <TableRow key={designation.id}>
                      <TableCell className="font-medium">{designation.code}</TableCell>
                      <TableCell>{designation.name}</TableCell>
                      <TableCell>{designation.department_name || '-'}</TableCell>
                      <TableCell>{designation.level}</TableCell>
                      <TableCell>{designation.reporting_to_name || '-'}</TableCell>
                      <TableCell>{designation.min_experience_years}</TableCell>
                      <TableCell>
                        <Badge
                          className={
                            designation.status === 'ACTIVE'
                              ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-50'
                              : 'bg-slate-100 text-slate-600 hover:bg-slate-100'
                          }
                        >
                          {designation.status}
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
                            <DropdownMenuItem onClick={() => navigate(`/admin/designations/${designation.id}/edit`)}>
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleDelete(designation.id)}
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
                    Showing {designations.length} of {pagination.total} designations
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={pagination.page <= 1}
                      onClick={() => fetchDesignations(pagination.page - 1)}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={pagination.page >= pagination.totalPages}
                      onClick={() => fetchDesignations(pagination.page + 1)}
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
