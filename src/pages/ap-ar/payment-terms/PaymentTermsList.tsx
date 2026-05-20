import {
  Plus,
  Pencil,
  Trash2,
  Search,
  CreditCard,
  MoreHorizontal,
  Percent,
  Calendar,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

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
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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
import { paymentTermsApi, organizationsApi } from '@/services/api';

import { logger } from "@/lib/logger";
interface Organization {
  id: string;
  name: string;
}

interface PaymentTerms {
  id: string;
  code: string;
  name: string;
  description: string | null;
  days: number;
  discountDays: number;
  discountPercent: number;
  organizationId: string;
  isActive: boolean;
  createdAt: string;
}

export function PaymentTermsList() {
  const navigate = useNavigate();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [paymentTerms, setPaymentTerms] = useState<PaymentTerms[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const fetchOrganizations = useCallback(async () => {
    try {
      const response = await organizationsApi.list({ pageSize: 100 });
      setOrganizations(response.data.items);
      if (response.data.items.length > 0) {
        setSelectedOrgId(response.data.items[0].id);
      }
    } catch (error) {
      logger.error('Failed to fetch organizations:', error);
    }
  }, []);

  const fetchPaymentTerms = useCallback(async () => {
    try {
      setLoading(true);
      const response = await paymentTermsApi.list({
        page_size: 100,
        include_inactive: true,
      });
      setPaymentTerms(response.data.items);
    } catch (error) {
      logger.error('Failed to fetch payment terms:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedOrgId]);

  useEffect(() => {
    fetchOrganizations();
  }, [fetchOrganizations]);

  useEffect(() => {
    if (selectedOrgId) {
      fetchPaymentTerms();
    }
  }, [fetchPaymentTerms, selectedOrgId]);

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await paymentTermsApi.delete(deleteId);
      fetchPaymentTerms();
    } catch (error) {
      logger.error('Failed to delete payment terms:', error);
    } finally {
      setDeleteId(null);
    }
  };

  const filteredTerms = paymentTerms.filter(
    (term) =>
      term.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      term.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Payment Terms"
        subtitle="Manage payment terms for vendors and customers"
        actions={
          <Button onClick={() => navigate('/admin/ap-ar/payment-terms/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Payment Terms
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Payment Terms List
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
            <div>
              <Label>Organization</Label>
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
            <div className="md:col-span-2">
              <Label>Search</Label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  placeholder="Search by code or name..."
                  className="pl-9"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-sm text-slate-500">Loading...</div>
            </div>
          ) : filteredTerms.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <CreditCard className="mb-4 h-12 w-12 text-slate-300" />
              <p className="text-sm text-slate-500">No payment terms found</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Code</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead className="text-center">Due Days</TableHead>
                  <TableHead className="text-center">Discount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[80px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTerms.map((term) => (
                  <TableRow key={term.id}>
                    <TableCell className="font-mono font-medium">
                      {term.code}
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{term.name}</p>
                        {term.description && (
                          <p className="text-xs text-slate-500">
                            {term.description}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <div className="flex items-center justify-center gap-1">
                        <Calendar className="h-4 w-4 text-slate-400" />
                        <span>{term.days}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      {term.discountPercent > 0 ? (
                        <div className="flex flex-col items-center">
                          <Badge variant="secondary" className="text-xs">
                            <Percent className="mr-1 h-3 w-3" />
                            {term.discountPercent}%
                          </Badge>
                          <span className="text-xs text-slate-500">
                            within {term.discountDays} days
                          </span>
                        </div>
                      ) : (
                        <span className="text-slate-400">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={term.isActive ? 'default' : 'secondary'}
                        className={
                          term.isActive
                            ? 'bg-emerald-100 text-emerald-700'
                            : 'bg-slate-100 text-slate-600'
                        }
                      >
                        {term.isActive ? 'Active' : 'Inactive'}
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
                              navigate(`/admin/ap-ar/payment-terms/${term.id}/edit`)
                            }
                          >
                            <Pencil className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            className="text-red-600"
                            onClick={() => setDeleteId(term.id)}
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
          )}
        </CardContent>
      </Card>

      <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Payment Terms?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the
              payment terms.
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
