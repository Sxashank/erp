import {
  AlertTriangle,
  Calendar,
  CheckCircle,
  Download,
  FileText,
  Filter,
  MoreHorizontal,
  Plus,
  Search,
  Shield,
  Upload,
} from 'lucide-react';
import { useEffect, useState } from 'react';

import { DateDisplay } from '@/components/common/DateDisplay';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { organizationsApi } from '@/services/api';
import type { Organization, PaginatedResponse } from '@/types';

import { logger } from "@/lib/logger";
interface InsurancePolicy {
  id: string;
  policy_number: string;
  insurance_company: string;
  policy_type: string;
  coverage_type: string;
  sum_insured: number;
  premium_amount: number;
  premium_frequency: string;
  start_date: string;
  end_date: string;
  renewal_date: string;
  days_to_expiry: number;
  status: 'ACTIVE' | 'EXPIRED' | 'CANCELLED' | 'PENDING_RENEWAL';
  assets_covered: number;
  last_claim_date?: string;
  total_claims: number;
  claim_amount: number;
}

interface InsuranceClaim {
  id: string;
  claim_number: string;
  policy_number: string;
  asset_code: string;
  asset_name: string;
  incident_date: string;
  claim_date: string;
  claim_type: string;
  claim_amount: number;
  approved_amount?: number;
  status: 'DRAFT' | 'SUBMITTED' | 'UNDER_REVIEW' | 'APPROVED' | 'REJECTED' | 'SETTLED';
  settlement_date?: string;
}

export function InsuranceList() {
  const [activeTab, setActiveTab] = useState('policies');
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [policies, setPolicies] = useState<InsurancePolicy[]>([]);
  const [claims, setClaims] = useState<InsuranceClaim[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrgId) {
      fetchPolicies();
      fetchClaims();
    }
  }, [selectedOrgId]);

  const fetchOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      const data: PaginatedResponse<Organization> = response.data;
      setOrganizations(data.items);
      if (data.items.length > 0) {
        setSelectedOrgId(data.items[0].id);
      }
    } catch (error) {
      logger.error('Failed to fetch organizations:', error);
    }
  };

  const fetchPolicies = async () => {
    try {
      setLoading(true);
      // Mock data - replace with actual API call
      const mockPolicies: InsurancePolicy[] = [
        {
          id: '1',
          policy_number: 'POL-2024-001',
          insurance_company: 'ICICI Lombard',
          policy_type: 'FIRE_INSURANCE',
          coverage_type: 'Comprehensive',
          sum_insured: 50000000,
          premium_amount: 125000,
          premium_frequency: 'ANNUAL',
          start_date: '2024-04-01',
          end_date: '2025-03-31',
          renewal_date: '2025-03-01',
          days_to_expiry: 75,
          status: 'ACTIVE',
          assets_covered: 45,
          total_claims: 2,
          claim_amount: 350000,
        },
        {
          id: '2',
          policy_number: 'POL-2024-002',
          insurance_company: 'New India Assurance',
          policy_type: 'MACHINERY_BREAKDOWN',
          coverage_type: 'Standard',
          sum_insured: 25000000,
          premium_amount: 85000,
          premium_frequency: 'ANNUAL',
          start_date: '2024-01-01',
          end_date: '2024-12-31',
          renewal_date: '2024-12-01',
          days_to_expiry: 15,
          status: 'PENDING_RENEWAL',
          assets_covered: 28,
          total_claims: 1,
          claim_amount: 180000,
        },
        {
          id: '3',
          policy_number: 'POL-2023-015',
          insurance_company: 'Bajaj Allianz',
          policy_type: 'ALL_RISK',
          coverage_type: 'Premium',
          sum_insured: 75000000,
          premium_amount: 225000,
          premium_frequency: 'ANNUAL',
          start_date: '2023-06-01',
          end_date: '2024-05-31',
          renewal_date: '2024-05-01',
          days_to_expiry: -180,
          status: 'EXPIRED',
          assets_covered: 62,
          total_claims: 3,
          claim_amount: 520000,
        },
      ];
      setPolicies(mockPolicies);
    } catch (error) {
      logger.error('Failed to fetch policies:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchClaims = async () => {
    try {
      // Mock data - replace with actual API call
      const mockClaims: InsuranceClaim[] = [
        {
          id: '1',
          claim_number: 'CLM-2024-001',
          policy_number: 'POL-2024-001',
          asset_code: 'FA-VEH-001',
          asset_name: 'Toyota Innova Crysta',
          incident_date: '2024-09-15',
          claim_date: '2024-09-18',
          claim_type: 'ACCIDENT',
          claim_amount: 250000,
          approved_amount: 225000,
          status: 'SETTLED',
          settlement_date: '2024-10-25',
        },
        {
          id: '2',
          claim_number: 'CLM-2024-002',
          policy_number: 'POL-2024-002',
          asset_code: 'FA-MACH-005',
          asset_name: 'CNC Lathe Machine',
          incident_date: '2024-11-02',
          claim_date: '2024-11-05',
          claim_type: 'BREAKDOWN',
          claim_amount: 180000,
          status: 'UNDER_REVIEW',
        },
        {
          id: '3',
          claim_number: 'CLM-2024-003',
          policy_number: 'POL-2024-001',
          asset_code: 'FA-COMP-012',
          asset_name: 'Server Rack',
          incident_date: '2024-11-10',
          claim_date: '2024-11-12',
          claim_type: 'FIRE_DAMAGE',
          claim_amount: 100000,
          status: 'SUBMITTED',
        },
      ];
      setClaims(mockClaims);
    } catch (error) {
      logger.error('Failed to fetch claims:', error);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };


  const getPolicyStatusBadge = (status: string, daysToExpiry: number) => {
    if (status === 'EXPIRED') {
      return <Badge className="bg-red-50 text-red-700 hover:bg-red-50">Expired</Badge>;
    }
    if (status === 'CANCELLED') {
      return <Badge className="bg-slate-50 text-slate-700 hover:bg-slate-50">Cancelled</Badge>;
    }
    if (daysToExpiry <= 30) {
      return <Badge className="bg-yellow-50 text-yellow-700 hover:bg-yellow-50">Expiring Soon</Badge>;
    }
    return <Badge className="bg-emerald-50 text-emerald-700 hover:bg-emerald-50">Active</Badge>;
  };

  const getClaimStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      DRAFT: 'bg-slate-50 text-slate-700',
      SUBMITTED: 'bg-blue-50 text-blue-700',
      UNDER_REVIEW: 'bg-yellow-50 text-yellow-700',
      APPROVED: 'bg-emerald-50 text-emerald-700',
      REJECTED: 'bg-red-50 text-red-700',
      SETTLED: 'bg-purple-50 text-purple-700',
    };
    return <Badge className={`${styles[status]} hover:${styles[status]}`}>{status.replace('_', ' ')}</Badge>;
  };

  const activePolicies = policies.filter(p => p.status === 'ACTIVE').length;
  const expiringPolicies = policies.filter(p => p.days_to_expiry > 0 && p.days_to_expiry <= 30).length;
  const totalSumInsured = policies.filter(p => p.status === 'ACTIVE').reduce((sum, p) => sum + p.sum_insured, 0);
  const totalPremium = policies.filter(p => p.status === 'ACTIVE').reduce((sum, p) => sum + p.premium_amount, 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Asset Insurance"
        subtitle="Manage insurance policies and claims for fixed assets"
        actions={
          <div className="flex gap-2">
            <Button variant="outline">
              <Upload className="mr-2 h-4 w-4" />
              Import Policies
            </Button>
            <Button disabled>
              <Plus className="mr-2 h-4 w-4" />
              Policy Setup Deferred
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Policies</CardTitle>
            <Shield className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600">{activePolicies}</div>
            <p className="text-xs text-slate-500">Currently in force</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Expiring Soon</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{expiringPolicies}</div>
            <p className="text-xs text-slate-500">Within 30 days</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sum Insured</CardTitle>
            <FileText className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{formatCurrency(totalSumInsured)}</div>
            <p className="text-xs text-slate-500">Coverage value</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Annual Premium</CardTitle>
            <Calendar className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">{formatCurrency(totalPremium)}</div>
            <p className="text-xs text-slate-500">Total premium cost</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="policies">Insurance Policies</TabsTrigger>
          <TabsTrigger value="claims">Claims</TabsTrigger>
        </TabsList>

        <TabsContent value="policies">
          <Card>
            <CardHeader>
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <CardTitle>Policy Register</CardTitle>
                <div className="flex flex-wrap items-center gap-2">
                  <div className="relative">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                    <Input
                      placeholder="Search policies..."
                      className="pl-8 w-[200px]"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-[140px]">
                      <SelectValue placeholder="Status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Status</SelectItem>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="expiring">Expiring Soon</SelectItem>
                      <SelectItem value="expired">Expired</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Organization" />
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
              ) : policies.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <Shield className="mb-4 h-12 w-12 text-slate-300" />
                  <p className="text-sm text-slate-500">No insurance policies found</p>
                  <Button variant="link" disabled>
                    Policy setup deferred in this release
                  </Button>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Policy Number</TableHead>
                      <TableHead>Insurance Company</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead className="text-right">Sum Insured</TableHead>
                      <TableHead className="text-right">Premium</TableHead>
                      <TableHead>Validity</TableHead>
                      <TableHead>Assets</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="w-[70px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {policies.map((policy) => (
                      <TableRow key={policy.id}>
                        <TableCell className="font-medium">{policy.policy_number}</TableCell>
                        <TableCell>{policy.insurance_company}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{policy.policy_type.replace('_', ' ')}</Badge>
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {formatCurrency(policy.sum_insured)}
                        </TableCell>
                        <TableCell className="text-right">{formatCurrency(policy.premium_amount)}</TableCell>
                        <TableCell>
                          <div className="text-sm">
                            <p><DateDisplay date={policy.start_date} /></p>
                            <p className="text-slate-500">to <DateDisplay date={policy.end_date} /></p>
                          </div>
                        </TableCell>
                        <TableCell>{policy.assets_covered} assets</TableCell>
                        <TableCell>{getPolicyStatusBadge(policy.status, policy.days_to_expiry)}</TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem>View Details</DropdownMenuItem>
                              <DropdownMenuItem>Edit Policy</DropdownMenuItem>
                              <DropdownMenuItem>View Assets</DropdownMenuItem>
                              <DropdownMenuItem>File Claim</DropdownMenuItem>
                              <DropdownMenuItem>Renew Policy</DropdownMenuItem>
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
        </TabsContent>

        <TabsContent value="claims">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Insurance Claims</CardTitle>
                <Button disabled>
                  <Plus className="mr-2 h-4 w-4" />
                  Claim Workflow Deferred
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {claims.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <FileText className="mb-4 h-12 w-12 text-slate-300" />
                  <p className="text-sm text-slate-500">No claims filed</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Claim Number</TableHead>
                      <TableHead>Policy</TableHead>
                      <TableHead>Asset</TableHead>
                      <TableHead>Incident Date</TableHead>
                      <TableHead>Claim Type</TableHead>
                      <TableHead className="text-right">Claim Amount</TableHead>
                      <TableHead className="text-right">Approved</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="w-[70px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {claims.map((claim) => (
                      <TableRow key={claim.id}>
                        <TableCell className="font-medium">{claim.claim_number}</TableCell>
                        <TableCell>{claim.policy_number}</TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{claim.asset_code}</p>
                            <p className="text-sm text-slate-500">{claim.asset_name}</p>
                          </div>
                        </TableCell>
                        <TableCell><DateDisplay date={claim.incident_date} /></TableCell>
                        <TableCell>
                          <Badge variant="outline">{claim.claim_type.replace('_', ' ')}</Badge>
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {formatCurrency(claim.claim_amount)}
                        </TableCell>
                        <TableCell className="text-right">
                          {claim.approved_amount ? formatCurrency(claim.approved_amount) : '-'}
                        </TableCell>
                        <TableCell>{getClaimStatusBadge(claim.status)}</TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem>View Details</DropdownMenuItem>
                              <DropdownMenuItem>Upload Documents</DropdownMenuItem>
                              <DropdownMenuItem>Update Status</DropdownMenuItem>
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
        </TabsContent>
      </Tabs>
    </div>
  );
}
