import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Edit, FileText, MoreHorizontal, Plus, Trash2 } from 'lucide-react';

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
import { tdsSectionsApi } from '@/services/api';

interface TDSSection {
  id: string;
  section_code: string;
  section_name: string;
  description?: string;
  rate_individual: number;
  rate_company: number;
  rate_no_pan: number;
  rate_lower_deduction?: number;
  threshold_single: number;
  threshold_annual: number;
  is_tcs: boolean;
  surcharge_applicable: boolean;
  cess_rate: number;
  effective_from: string;
  effective_to?: string;
  return_form?: string;
  nature_of_payment_code?: string;
  is_active: boolean;
}

interface PaginatedResponse {
  items: TDSSection[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

const RETURN_FORMS = [
  { value: 'all', label: 'All Forms' },
  { value: '24Q', label: '24Q (Salary)' },
  { value: '26Q', label: '26Q (Non-Salary)' },
  { value: '27Q', label: '27Q (NRI)' },
  { value: '27EQ', label: '27EQ (TCS)' },
];

export default function TDSSectionList() {
  const navigate = useNavigate();
  const [sections, setSections] = useState<TDSSection[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedForm, setSelectedForm] = useState<string>('all');
  const [pagination, setPagination] = useState({ page: 1, total: 0, totalPages: 0 });

  useEffect(() => {
    fetchSections();
  }, [selectedForm]);

  const fetchSections = async (page = 1) => {
    try {
      setLoading(true);
      const params: any = { page, page_size: 20, include_inactive: true };
      if (selectedForm && selectedForm !== 'all') {
        params.return_form = selectedForm;
      }
      const response = await tdsSectionsApi.list(params);
      const data: PaginatedResponse = response.data;
      setSections(data.items);
      setPagination({ page: data.page, total: data.total, totalPages: data.total_pages });
    } catch (error) {
      console.error('Failed to fetch TDS sections:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this TDS section?')) return;
    try {
      await tdsSectionsApi.delete(id);
      fetchSections(pagination.page);
    } catch (error) {
      console.error('Failed to delete TDS section:', error);
    }
  };

  const formatPercent = (value: number) => `${value}%`;
  const formatAmount = (value: number) =>
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value);

  return (
    <div className="space-y-6">
      <PageHeader
        title="TDS/TCS Sections"
        subtitle="Manage TDS/TCS section configurations"
        actions={
          <Button onClick={() => navigate('/admin/tds/sections/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Section
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>All TDS/TCS Sections</CardTitle>
            <Select value={selectedForm} onValueChange={setSelectedForm}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Filter by Form" />
              </SelectTrigger>
              <SelectContent>
                {RETURN_FORMS.map((form) => (
                  <SelectItem key={form.value} value={form.value}>
                    {form.label}
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
          ) : sections.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <FileText className="mb-4 h-12 w-12 text-slate-300" />
              <p className="text-sm text-slate-500">No TDS sections found</p>
              <Button variant="link" onClick={() => navigate('/admin/tds/sections/new')}>
                Create your first TDS section
              </Button>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Section</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-right">Individual</TableHead>
                    <TableHead className="text-right">Company</TableHead>
                    <TableHead className="text-right">No PAN</TableHead>
                    <TableHead className="text-right">Threshold</TableHead>
                    <TableHead>Form</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="w-[70px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sections.map((section) => (
                    <TableRow key={section.id}>
                      <TableCell className="font-medium">{section.section_code}</TableCell>
                      <TableCell className="max-w-[200px] truncate" title={section.section_name}>
                        {section.section_name}
                      </TableCell>
                      <TableCell className="text-right">{formatPercent(section.rate_individual)}</TableCell>
                      <TableCell className="text-right">{formatPercent(section.rate_company)}</TableCell>
                      <TableCell className="text-right text-red-600">{formatPercent(section.rate_no_pan)}</TableCell>
                      <TableCell className="text-right">
                        {section.threshold_annual > 0 ? formatAmount(section.threshold_annual) : '-'}
                      </TableCell>
                      <TableCell>
                        <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-50">
                          {section.return_form || '-'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          className={
                            section.is_tcs
                              ? 'bg-purple-50 text-purple-700 hover:bg-purple-50'
                              : 'bg-amber-50 text-amber-700 hover:bg-amber-50'
                          }
                        >
                          {section.is_tcs ? 'TCS' : 'TDS'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          className={
                            section.is_active
                              ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-50'
                              : 'bg-slate-100 text-slate-600 hover:bg-slate-100'
                          }
                        >
                          {section.is_active ? 'Active' : 'Inactive'}
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
                              onClick={() => navigate(`/admin/tds/sections/${section.id}/edit`)}
                            >
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleDelete(section.id)}
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
                    Showing {sections.length} of {pagination.total} sections
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={pagination.page <= 1}
                      onClick={() => fetchSections(pagination.page - 1)}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={pagination.page >= pagination.totalPages}
                      onClick={() => fetchSections(pagination.page + 1)}
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
