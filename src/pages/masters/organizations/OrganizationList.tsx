import { Building2, CreditCard, Edit, MapPin, MoreHorizontal, Plus, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { organizationsApi } from '@/services/api';
import type { Organization, PaginatedResponse } from '@/types';

import { logger } from "@/lib/logger";
export function OrganizationList() {
  const navigate = useNavigate();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ page: 1, total: 0, totalPages: 0 });

  const fetchOrganizations = async (page = 1) => {
    try {
      setLoading(true);
      const response = await organizationsApi.list({ page, pageSize: 10, includeInactive: true });
      const data: PaginatedResponse<Organization> = response.data;
      setOrganizations(data.items);
      setPagination({ page: data.page, total: data.total, totalPages: data.total_pages });
    } catch (error) {
      logger.error('Failed to fetch organizations:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrganizations();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this organization?')) return;
    try {
      await organizationsApi.delete(id);
      fetchOrganizations(pagination.page);
    } catch (error) {
      logger.error('Failed to delete organization:', error);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Organizations"
        subtitle="Manage your organization settings and details"
        actions={
          <Button onClick={() => navigate('/admin/organizations/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Organization
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>All Organizations</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-sm text-slate-500">Loading...</p>
            </div>
          ) : organizations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <p className="text-sm text-slate-500">No organizations found</p>
              <Button variant="link" onClick={() => navigate('/admin/organizations/new')}>
                Create your first organization
              </Button>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Code</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Legal Name</TableHead>
                    <TableHead>PAN</TableHead>
                    <TableHead>GSTIN</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="w-[70px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {organizations.map((org) => (
                    <TableRow key={org.id}>
                      <TableCell className="font-medium">{org.code}</TableCell>
                      <TableCell>{org.name}</TableCell>
                      <TableCell>{org.legal_name}</TableCell>
                      <TableCell>{org.pan}</TableCell>
                      <TableCell>{org.gstin || '-'}</TableCell>
                      <TableCell>
                        <Badge
                          className={
                            org.status === 'ACTIVE'
                              ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-50'
                              : 'bg-slate-100 text-slate-600 hover:bg-slate-100'
                          }
                        >
                          {org.status}
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
                            <DropdownMenuItem onClick={() => navigate(`/admin/organizations/${org.id}/edit`)}>
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => navigate(`/admin/organizations/${org.id}/bank-accounts`)}>
                              <CreditCard className="mr-2 h-4 w-4" />
                              Bank Accounts
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => navigate(`/admin/organizations/${org.id}/addresses`)}>
                              <MapPin className="mr-2 h-4 w-4" />
                              Addresses
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleDelete(org.id)}
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
                    Showing {organizations.length} of {pagination.total} organizations
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={pagination.page <= 1}
                      onClick={() => fetchOrganizations(pagination.page - 1)}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={pagination.page >= pagination.totalPages}
                      onClick={() => fetchOrganizations(pagination.page + 1)}
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
