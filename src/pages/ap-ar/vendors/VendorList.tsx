import {
  Plus,
  Search,
  MoreHorizontal,
  Edit,
  Trash2,
  ChevronLeft,
  ChevronRight,
  MapPin,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AmountDisplay } from '@/components/common/AmountDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
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
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import { vendorsApi, organizationsApi } from '@/services/api';

import { logger } from "@/lib/logger";
interface Organization {
  id: string;
  code: string;
  name: string;
}

interface Vendor {
  id: string;
  code: string;
  name: string;
  display_name: string | null;
  vendor_type: string;
  gstin: string | null;
  pan: string | null;
  city: string | null;
  state_code: string | null;
  current_balance: number;
  current_balance_type: string | null;
  is_active: boolean;
}

type VendorListParams = Parameters<typeof vendorsApi.list>[0];

const vendorTypeLabels: Record<string, string> = {
  SUPPLIER: 'Supplier',
  CONTRACTOR: 'Contractor',
  SERVICE_PROVIDER: 'Service Provider',
  OTHERS: 'Others',
};

const vendorTypeColors: Record<string, string> = {
  SUPPLIER: 'bg-blue-100 text-blue-800',
  CONTRACTOR: 'bg-purple-100 text-purple-800',
  SERVICE_PROVIDER: 'bg-green-100 text-green-800',
  OTHERS: 'bg-gray-100 text-gray-800',
};

export function VendorList() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [vendorTypeFilter, setVendorTypeFilter] = useState<string>('all');
  const [includeInactive, setIncludeInactive] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [vendorToDelete, setVendorToDelete] = useState<Vendor | null>(null);
  const pageSize = 20;

  const loadOrganizations = useCallback(async () => {
    try {
      const response = await organizationsApi.list({ page: 1, page_size: 100 });
      const orgs = response.data.items || [];
      setOrganizations(orgs);
      if (orgs.length > 0) {
        setSelectedOrgId(orgs[0].id);
      }
    } catch (error) {
      logger.error('Failed to load organizations:', error);
      toast({
        title: 'Error',
        description: 'Failed to load organizations',
        variant: 'destructive',
      });
    }
  }, [toast]);

  const loadVendors = useCallback(async () => {
    if (!selectedOrgId) return;
    setLoading(true);
    try {
      const params: VendorListParams = {
        organization_id: selectedOrgId,
        page,
        page_size: pageSize,
        include_inactive: includeInactive,
      };
      if (searchQuery) {
        params.search = searchQuery;
      }
      if (vendorTypeFilter && vendorTypeFilter !== 'all') {
        params.vendor_type = vendorTypeFilter;
      }
      const response = await vendorsApi.list(params);
      setVendors(response.data.items || []);
      setTotal(response.data.total || 0);
      setTotalPages(response.data.pages || 1);
    } catch (error) {
      logger.error('Failed to load vendors:', error);
      toast({
        title: 'Error',
        description: 'Failed to load vendors',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [includeInactive, page, searchQuery, selectedOrgId, toast, vendorTypeFilter]);

  useEffect(() => {
    loadOrganizations();
  }, [loadOrganizations]);

  useEffect(() => {
    if (selectedOrgId) {
      loadVendors();
    }
  }, [loadVendors, selectedOrgId]);

  const handleDelete = async () => {
    if (!vendorToDelete) return;
    try {
      await vendorsApi.delete(vendorToDelete.id);
      toast({
        title: 'Success',
        description: 'Vendor deleted successfully',
      });
      loadVendors();
    } catch (error) {
      showErrorToast(error, toast);
    } finally {
      setDeleteDialogOpen(false);
      setVendorToDelete(null);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Vendors"
        subtitle="Manage vendor/supplier master records"
        actions={
          <Button onClick={() => navigate('/admin/ap-ar/vendors/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Vendor
          </Button>
        }
      />

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4 rounded-lg border border-slate-200 bg-white p-4">
        <div className="flex-1 min-w-[200px]">
          <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
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
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input
              placeholder="Search by code, name, GSTIN, PAN..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(1);
              }}
              className="pl-9"
            />
          </div>
        </div>
        <div className="w-[180px]">
          <Select
            value={vendorTypeFilter}
            onValueChange={(value) => {
              setVendorTypeFilter(value);
              setPage(1);
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="All Types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="SUPPLIER">Supplier</SelectItem>
              <SelectItem value="CONTRACTOR">Contractor</SelectItem>
              <SelectItem value="SERVICE_PROVIDER">Service Provider</SelectItem>
              <SelectItem value="OTHERS">Others</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center gap-2">
          <Checkbox
            id="includeInactive"
            checked={includeInactive}
            onCheckedChange={(checked) => {
              setIncludeInactive(checked === true);
              setPage(1);
            }}
          />
          <label htmlFor="includeInactive" className="text-sm text-slate-600">
            Include inactive
          </label>
        </div>
      </div>

      {/* Table */}
      <div className="rounded-lg border border-slate-200 bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[100px]">Code</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>GSTIN</TableHead>
              <TableHead>PAN</TableHead>
              <TableHead>Location</TableHead>
              <TableHead className="text-right">Balance</TableHead>
              <TableHead className="w-[80px]">Status</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={9} className="text-center py-8">
                  Loading...
                </TableCell>
              </TableRow>
            ) : vendors.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} className="text-center py-8">
                  No vendors found
                </TableCell>
              </TableRow>
            ) : (
              vendors.map((vendor) => (
                <TableRow key={vendor.id}>
                  <TableCell className="font-medium">{vendor.code}</TableCell>
                  <TableCell>
                    <div>
                      <div className="font-medium">{vendor.name}</div>
                      {vendor.display_name && vendor.display_name !== vendor.name && (
                        <div className="text-sm text-slate-500">{vendor.display_name}</div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={vendorTypeColors[vendor.vendor_type] || 'bg-gray-100'}
                    >
                      {vendorTypeLabels[vendor.vendor_type] || vendor.vendor_type}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono text-sm">{vendor.gstin || '-'}</TableCell>
                  <TableCell className="font-mono text-sm">{vendor.pan || '-'}</TableCell>
                  <TableCell>
                    {vendor.city || vendor.state_code ? (
                      <div className="flex items-center gap-1 text-sm text-slate-600">
                        <MapPin className="h-3 w-3" />
                        {[vendor.city, vendor.state_code].filter(Boolean).join(', ')}
                      </div>
                    ) : (
                      '-'
                    )}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    <AmountDisplay amount={Math.abs(vendor.current_balance)} />
                    {vendor.current_balance !== 0 && vendor.current_balance_type ? (
                      <span className="ml-1">{vendor.current_balance_type}</span>
                    ) : null}
                  </TableCell>
                  <TableCell>
                    <Badge variant={vendor.is_active ? 'default' : 'secondary'}>
                      {vendor.is_active ? 'Active' : 'Inactive'}
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
                          onClick={() => navigate(`/admin/ap-ar/vendors/${vendor.id}/edit`)}
                        >
                          <Edit className="mr-2 h-4 w-4" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => {
                            setVendorToDelete(vendor);
                            setDeleteDialogOpen(true);
                          }}
                          className="text-red-600"
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-slate-200 px-4 py-3">
            <div className="text-sm text-slate-500">
              Showing {(page - 1) * pageSize + 1} to{' '}
              {Math.min(page * pageSize, total)} of {total} vendors
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm text-slate-600">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Vendor</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete vendor &quot;{vendorToDelete?.name}&quot;? This action
              cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
