import {
  Copy,
  Edit,
  FileText,
  Heart,
  Loader2,
  MoreHorizontal,
  Plus,
  Search,
  Star,
  Trash2,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AmountDisplay } from '@/components/common/AmountDisplay';
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
import { organizationsApi, voucherTemplatesApi } from '@/services/api';

import { logger } from "@/lib/logger";
interface Organization {
  id: string;
  name: string;
}

interface VoucherTemplate {
  id: string;
  template_name: string;
  voucher_type_name: string;
  voucher_type_code: string;
  total_amount: number;
  category: string | null;
  is_active: boolean;
  is_favorite: boolean;
  usage_count: number;
  last_used_at: string | null;
}

interface TemplateStats {
  total_templates: number;
  active_templates: number;
  favorite_templates: number;
  categories: { category: string; count: number }[];
  most_used: VoucherTemplate[];
}

type VoucherTemplateListParams = Parameters<typeof voucherTemplatesApi.list>[0];

const CATEGORIES = [
  'PAYROLL',
  'RENT',
  'UTILITIES',
  'TAX',
  'DEPRECIATION',
  'INSURANCE',
  'INTEREST',
  'MISC',
];

export function VoucherTemplates() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');

  const [templates, setTemplates] = useState<VoucherTemplate[]>([]);
  const [stats, setStats] = useState<TemplateStats | null>(null);

  const [loading, setLoading] = useState(false);
  const [filterCategory, setFilterCategory] = useState<string>('');
  const [filterFavorite, setFilterFavorite] = useState<boolean | undefined>(undefined);
  const [searchQuery, setSearchQuery] = useState('');

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

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const params: VoucherTemplateListParams = { page_size: 50 };
      if (filterCategory && filterCategory !== 'ALL') params.category = filterCategory;
      if (filterFavorite !== undefined) params.is_favorite = filterFavorite;
      if (searchQuery) params.search = searchQuery;

      const [listRes, statsRes] = await Promise.all([
        voucherTemplatesApi.list(params),
        voucherTemplatesApi.getStats(),
      ]);

      setTemplates(listRes.data.items);
      setStats(statsRes.data);
    } catch (error) {
      logger.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  }, [filterCategory, filterFavorite, searchQuery, selectedOrgId]);

  useEffect(() => {
    fetchOrganizations();
  }, [fetchOrganizations]);

  useEffect(() => {
    if (selectedOrgId) {
      fetchData();
    }
  }, [fetchData, selectedOrgId]);

  const handleToggleFavorite = async (id: string) => {
    try {
      await voucherTemplatesApi.toggleFavorite(id);
      fetchData();
    } catch (error) {
      showErrorToast(error, toast);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this template?')) return;
    try {
      await voucherTemplatesApi.delete(id);
      toast({ title: 'Success', description: 'Template deleted' });
      fetchData();
    } catch (error) {
      showErrorToast(error, toast);
    }
  };

  const handleDuplicate = async (id: string) => {
    try {
      await voucherTemplatesApi.duplicate(id);
      toast({ title: 'Success', description: 'Template duplicated' });
      fetchData();
    } catch (error) {
      showErrorToast(error, toast);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Voucher Templates"
        subtitle="Reusable voucher entries for quick data entry"
        actions={
          <div className="flex gap-2">
            <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
              <SelectTrigger className="w-48">
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
            <Button onClick={() => navigate(`/admin/finance/voucher-templates/new?org=${selectedOrgId}`)}>
              <Plus className="mr-2 h-4 w-4" />
              New Template
            </Button>
          </div>
        }
      />

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-4">
              <div className="text-sm text-slate-500">Total Templates</div>
              <div className="text-2xl font-bold text-slate-800">{stats.total_templates}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-sm text-slate-500">Active</div>
              <div className="text-2xl font-bold text-emerald-600">{stats.active_templates}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-sm text-slate-500">Favorites</div>
              <div className="text-2xl font-bold text-amber-600">{stats.favorite_templates}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-sm text-slate-500">Categories</div>
              <div className="text-2xl font-bold text-blue-600">{stats.categories.length}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Most Used Templates */}
      {stats && stats.most_used.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Star className="h-5 w-5 text-amber-500" />
              Most Used Templates
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {stats.most_used.map((t) => (
                <button
                  type="button"
                  key={t.id}
                  className="flex items-center gap-3 bg-slate-50 rounded-lg px-4 py-2 hover:bg-slate-100 text-left"
                  onClick={() => navigate(`/admin/finance/voucher-templates/${t.id}/use`)}
                >
                  <div>
                    <p className="font-medium text-sm">{t.template_name}</p>
                    <p className="text-xs text-slate-500">Used {t.usage_count} times</p>
                  </div>
                  <Badge variant="outline">
                    <AmountDisplay amount={t.total_amount} />
                  </Badge>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search templates..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <Select value={filterCategory} onValueChange={setFilterCategory}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="All Categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All Categories</SelectItem>
            {CATEGORIES.map((c) => (
              <SelectItem key={c} value={c}>
                {c}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button
          variant={filterFavorite ? 'default' : 'outline'}
          onClick={() => setFilterFavorite(filterFavorite ? undefined : true)}
        >
          <Heart className={`h-4 w-4 mr-2 ${filterFavorite ? 'fill-current' : ''}`} />
          Favorites
        </Button>
      </div>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex justify-center items-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            </div>
          ) : templates.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <FileText className="h-12 w-12 mx-auto mb-3 text-slate-300" />
              <p>No templates found</p>
              <p className="text-sm">Create one to speed up voucher entry</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead></TableHead>
                  <TableHead>Template Name</TableHead>
                  <TableHead>Voucher Type</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead className="text-center">Used</TableHead>
                  <TableHead className="text-center">Status</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {templates.map((t) => (
                  <TableRow key={t.id} className="cursor-pointer hover:bg-slate-50">
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleToggleFavorite(t.id);
                        }}
                      >
                        <Star className={`h-4 w-4 ${t.is_favorite ? 'fill-amber-400 text-amber-400' : 'text-slate-300'}`} />
                      </Button>
                    </TableCell>
                    <TableCell
                      className="font-medium"
                      onClick={() => navigate(`/admin/finance/voucher-templates/${t.id}/use`)}
                    >
                      {t.template_name}
                    </TableCell>
                    <TableCell>{t.voucher_type_name}</TableCell>
                    <TableCell>
                      {t.category && <Badge variant="outline">{t.category}</Badge>}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      <AmountDisplay amount={t.total_amount} />
                    </TableCell>
                    <TableCell className="text-center">{t.usage_count}</TableCell>
                    <TableCell className="text-center">
                      <Badge className={t.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}>
                        {t.is_active ? 'Active' : 'Inactive'}
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
                          <DropdownMenuItem onClick={() => navigate(`/admin/finance/voucher-templates/${t.id}/use`)}>
                            <FileText className="mr-2 h-4 w-4" />
                            Use Template
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => navigate(`/admin/finance/voucher-templates/${t.id}/edit`)}>
                            <Edit className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleDuplicate(t.id)}>
                            <Copy className="mr-2 h-4 w-4" />
                            Duplicate
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem className="text-red-600" onClick={() => handleDelete(t.id)}>
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
    </div>
  );
}

export default VoucherTemplates;
