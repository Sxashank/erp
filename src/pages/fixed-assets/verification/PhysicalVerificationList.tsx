import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Calendar,
  CheckCircle,
  ClipboardCheck,
  Eye,
  MoreHorizontal,
  Plus,
  Search,
  XCircle,
} from 'lucide-react';

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
import { organizationsApi } from '@/services/api';
import type { Organization, PaginatedResponse } from '@/types';

interface VerificationCampaign {
  id: string;
  campaign_code: string;
  campaign_name: string;
  organization_id: string;
  location_id?: string;
  location_name?: string;
  department_id?: string;
  department_name?: string;
  start_date: string;
  end_date: string;
  status: 'DRAFT' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  total_assets: number;
  verified_count: number;
  missing_count: number;
  extra_count: number;
  variance_count: number;
  created_by_name?: string;
  created_at: string;
}

const STATUSES = [
  { value: '', label: 'All Statuses' },
  { value: 'DRAFT', label: 'Draft' },
  { value: 'IN_PROGRESS', label: 'In Progress' },
  { value: 'COMPLETED', label: 'Completed' },
  { value: 'CANCELLED', label: 'Cancelled' },
];

export function PhysicalVerificationList() {
  const navigate = useNavigate();
  const [campaigns, setCampaigns] = useState<VerificationCampaign[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const limit = 20;

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrgId) {
      fetchCampaigns();
    }
  }, [selectedOrgId, selectedStatus, skip]);

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

  const fetchCampaigns = async () => {
    try {
      setLoading(true);
      // Mock data - replace with actual API call
      const mockCampaigns: VerificationCampaign[] = [
        {
          id: '1',
          campaign_code: 'PV-2024-001',
          campaign_name: 'Q4 2024 Physical Verification',
          organization_id: selectedOrgId,
          location_name: 'Head Office',
          start_date: '2024-12-01',
          end_date: '2024-12-31',
          status: 'IN_PROGRESS',
          total_assets: 150,
          verified_count: 120,
          missing_count: 3,
          extra_count: 2,
          variance_count: 5,
          created_by_name: 'Admin User',
          created_at: '2024-11-25',
        },
        {
          id: '2',
          campaign_code: 'PV-2024-002',
          campaign_name: 'IT Assets Verification',
          organization_id: selectedOrgId,
          department_name: 'IT Department',
          start_date: '2024-11-15',
          end_date: '2024-11-30',
          status: 'COMPLETED',
          total_assets: 75,
          verified_count: 73,
          missing_count: 2,
          extra_count: 0,
          variance_count: 2,
          created_by_name: 'Admin User',
          created_at: '2024-11-10',
        },
      ];
      setCampaigns(mockCampaigns);
      setTotal(mockCampaigns.length);
    } catch (error) {
      console.error('Failed to fetch campaigns:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'DRAFT':
        return <Badge variant="outline">Draft</Badge>;
      case 'IN_PROGRESS':
        return <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-50">In Progress</Badge>;
      case 'COMPLETED':
        return <Badge className="bg-emerald-50 text-emerald-700 hover:bg-emerald-50">Completed</Badge>;
      case 'CANCELLED':
        return <Badge className="bg-red-50 text-red-700 hover:bg-red-50">Cancelled</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getProgressColor = (verified: number, total: number) => {
    const percentage = total > 0 ? (verified / total) * 100 : 0;
    if (percentage >= 90) return 'bg-emerald-500';
    if (percentage >= 70) return 'bg-blue-500';
    if (percentage >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Physical Verification"
        subtitle="Manage asset verification campaigns"
        actions={
          <Button onClick={() => navigate('/admin/fixed-assets/verification/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Campaign
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Campaigns</CardTitle>
            <ClipboardCheck className="h-4 w-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {campaigns.filter(c => c.status === 'IN_PROGRESS').length}
            </div>
            <p className="text-xs text-slate-500">Currently running</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Verified Assets</CardTitle>
            <CheckCircle className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600">
              {campaigns.reduce((sum, c) => sum + c.verified_count, 0)}
            </div>
            <p className="text-xs text-slate-500">This month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Missing Assets</CardTitle>
            <XCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {campaigns.reduce((sum, c) => sum + c.missing_count, 0)}
            </div>
            <p className="text-xs text-slate-500">Requires attention</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Variances</CardTitle>
            <Calendar className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {campaigns.reduce((sum, c) => sum + c.variance_count, 0)}
            </div>
            <p className="text-xs text-slate-500">To be resolved</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle>Verification Campaigns</CardTitle>
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search campaigns..."
                  className="pl-8 w-[200px]"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="All Statuses" />
                </SelectTrigger>
                <SelectContent>
                  {STATUSES.map((status) => (
                    <SelectItem key={status.value} value={status.value}>
                      {status.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
                <SelectTrigger className="w-[200px]">
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
          ) : campaigns.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <ClipboardCheck className="mb-4 h-12 w-12 text-slate-300" />
              <p className="text-sm text-slate-500">No verification campaigns found</p>
              <Button
                variant="link"
                onClick={() => navigate('/admin/fixed-assets/verification/new')}
              >
                Create your first campaign
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Campaign</TableHead>
                  <TableHead>Location/Department</TableHead>
                  <TableHead>Period</TableHead>
                  <TableHead>Progress</TableHead>
                  <TableHead>Missing</TableHead>
                  <TableHead>Variances</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[70px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {campaigns.map((campaign) => (
                  <TableRow key={campaign.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{campaign.campaign_code}</p>
                        <p className="text-sm text-slate-500">{campaign.campaign_name}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      {campaign.location_name || campaign.department_name || '-'}
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <p>{formatDate(campaign.start_date)}</p>
                        <p className="text-slate-500">to {formatDate(campaign.end_date)}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <span>{campaign.verified_count} / {campaign.total_assets}</span>
                          <span className="text-slate-500">
                            {Math.round((campaign.verified_count / campaign.total_assets) * 100)}%
                          </span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-slate-100">
                          <div
                            className={`h-2 rounded-full ${getProgressColor(campaign.verified_count, campaign.total_assets)}`}
                            style={{
                              width: `${(campaign.verified_count / campaign.total_assets) * 100}%`,
                            }}
                          />
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      {campaign.missing_count > 0 ? (
                        <Badge className="bg-red-50 text-red-700 hover:bg-red-50">
                          {campaign.missing_count}
                        </Badge>
                      ) : (
                        <span className="text-slate-500">0</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {campaign.variance_count > 0 ? (
                        <Badge className="bg-orange-50 text-orange-700 hover:bg-orange-50">
                          {campaign.variance_count}
                        </Badge>
                      ) : (
                        <span className="text-slate-500">0</span>
                      )}
                    </TableCell>
                    <TableCell>{getStatusBadge(campaign.status)}</TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={() => navigate(`/admin/fixed-assets/verification/${campaign.id}`)}
                          >
                            <Eye className="mr-2 h-4 w-4" />
                            View Details
                          </DropdownMenuItem>
                          {campaign.status === 'IN_PROGRESS' && (
                            <DropdownMenuItem
                              onClick={() => navigate(`/admin/fixed-assets/verification/${campaign.id}/verify`)}
                            >
                              <ClipboardCheck className="mr-2 h-4 w-4" />
                              Continue Verification
                            </DropdownMenuItem>
                          )}
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
